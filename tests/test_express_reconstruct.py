"""Task 5 (M3): LIR straight-run -> Stmt/Expr tree reconstruction.

Brief defect note (see task-5-report.md for the full writeup): the brief's
Step-1 test_move_and_arith_reconstruct used the source
`local a = 1 local b = 2 local c = a + b return c` and asserted a LocalDecl
binding a '+' BinExpr. Checked against the real classify_registers output
for that exact snippet (via the sz4 luac build): registers a, b, AND c are
ALL classified temp (each has exactly one def and one adjacent single use --
c's only use is the immediately-following RETURN), so the whole expression
correctly inlines straight into ReturnStmt with zero LocalDecls at all --
the literal brief test can never pass without breaking the single-use
inlining invariant the whole module exists to preserve. Fixed by adding a
second read of c (`print(c)`) so its register genuinely has two uses,
forcing it local -- this preserves the test's evident intent (verify ADD
reconstructs to a BinExpr and lands in a LocalDecl) using a source shape
that classify_registers actually agrees is a local.
"""
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _proto_and_fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    p = load_file(o)
    return p, lift_proto(p)


def test_move_and_arith_reconstruct(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight
    from pyluadec.express.expr import BinExpr
    # print(c) forces c's register to have two uses (print, return), so it
    # is classified local -- see module docstring for why the brief's
    # original single-use `return c` source can never produce a LocalDecl.
    p, fn = _proto_and_fn(
        "local a = 1 local b = 2 local c = a + b print(c) return c", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    # somewhere a LocalDecl binds an ADD expression
    from pyluadec.express.reconstruct import LocalDecl
    adds = [s for s in stmts if isinstance(s, LocalDecl) and any(isinstance(e, BinExpr) and e.op == "+" for e in s.exprs)]
    assert adds


def test_call_arg_staging_inlines(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, ExprStmt
    from pyluadec.express.expr import CallExpr, ConstExpr
    p, fn = _proto_and_fn("print('a', 'b', 'c')", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    calls = [s for s in stmts if isinstance(s, ExprStmt)]
    assert calls and isinstance(calls[0].call, CallExpr)
    assert len(calls[0].call.args) == 3      # three literals inlined as args, no intermediate locals
    assert all(isinstance(a, ConstExpr) for a in calls[0].call.args)


def test_table_constructor_reconstructs(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl
    from pyluadec.express.expr import TableExpr
    p, fn = _proto_and_fn("local t = {10, 20, 30} return t", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    decls = [s for s in stmts if isinstance(s, LocalDecl) and any(isinstance(e, TableExpr) for e in s.exprs)]
    assert decls and len(decls[0].exprs[0].array) == 3


def test_reassignment_emits_assign_not_second_decl(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl, Assign
    p, fn = _proto_and_fn("local a = 1 a = a + 1 return a", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    assert sum(isinstance(s, LocalDecl) for s in stmts) == 1
    assert sum(isinstance(s, Assign) for s in stmts) == 1


# ---- additional coverage beyond the brief's four starter tests ------------

def test_table_constructor_array_values_are_correct_constants(tmp_path):
    """Pins the actual VALUES folded into the TableExpr, not just the count
    (test_table_constructor_reconstructs already pins len==3; this pins that
    the three ConstExpr payloads are 10, 20, 30 in that order -- catches a
    reversed or off-by-one fold)."""
    import struct
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl
    from pyluadec.express.expr import ConstExpr, TableExpr
    p, fn = _proto_and_fn("local t = {10, 20, 30} return t", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    decls = [s for s in stmts if isinstance(s, LocalDecl) and any(isinstance(e, TableExpr) for e in s.exprs)]
    table = decls[0].exprs[0]
    values = [struct.unpack("<d", e.value.payload)[0] for e in table.array]
    assert values == [10.0, 20.0, 30.0]


def test_sub_does_not_swap_operands(tmp_path):
    """SUB is non-commutative: 'local a = 5 local b = 2 local c = a - b
    print(c) return c' must reconstruct BinExpr('-', <5-side>, <2-side>),
    never the reverse -- a swap would silently invert every subtraction in
    the corpus."""
    import struct
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl
    from pyluadec.express.expr import BinExpr, ConstExpr
    p, fn = _proto_and_fn(
        "local a = 5 local b = 2 local c = a - b print(c) return c", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    subs = [e for s in stmts if isinstance(s, LocalDecl)
            for e in s.exprs if isinstance(e, BinExpr) and e.op == "-"]
    assert len(subs) == 1
    lhs = struct.unpack("<d", subs[0].lhs.value.payload)[0]
    rhs = struct.unpack("<d", subs[0].rhs.value.payload)[0]
    assert (lhs, rhs) == (5.0, 2.0)


def test_concat_does_not_swap_operands(tmp_path):
    """CONCAT ('..') is non-commutative too: 'local a = "x" local b = "y"
    local c = a .. b print(c) return c' must produce BinExpr('..', "x", "y")
    in that order.

    Note: luac stages a's and b's *values* into a fresh contiguous register
    pair for CONCAT (MOVE r2,r0; MOVE r3,r1) and then overwrites r2 in place
    with the CONCAT result -- r2 ends up local (two defs: the staging MOVE,
    then CONCAT) and its second write is therefore an Assign, not a second
    LocalDecl. So the BinExpr can land in either statement kind depending on
    register reuse; check both rather than assuming LocalDecl specifically
    (an earlier version of this test assumed LocalDecl only and would have
    silently found zero matches on this exact source -- a Task-5 test
    honesty bug on the model of the brief's own Step-1 defect, see the
    module docstring).
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl, Assign
    from pyluadec.express.expr import BinExpr, ConstExpr, LocalExpr
    p, fn = _proto_and_fn(
        'local a = "x" local b = "y" local c = a .. b print(c) return c', tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    cats = [e for s in stmts if isinstance(s, (LocalDecl, Assign))
            for e in s.exprs if isinstance(e, BinExpr) and e.op == ".."]
    assert len(cats) == 1
    lhs, rhs = cats[0].lhs, cats[0].rhs
    # By the time CONCAT runs, a's and b's values have already been staged
    # into fresh (local) registers by luac -- resolve those registers' own
    # first-declared value to check the underlying literals, in order.
    decl_value = {r: e for s in stmts if isinstance(s, LocalDecl)
                  for r, e in zip(s.regs, s.exprs)}
    assert isinstance(lhs, LocalExpr) and isinstance(rhs, LocalExpr)
    assert lhs.reg != rhs.reg
    assert decl_value[lhs.reg].value == b"x"
    assert decl_value[rhs.reg].value == b"y"


def test_rk_constant_operand_is_not_read_as_register(tmp_path):
    """'local a = 1 a = a + 1 return a' compiles ADD's RK(C) operand to a
    K-bit-set constant index (reusing the interned constant 1), never a
    plain register. rk() must honor the K bit: the BinExpr's rhs must be the
    ConstExpr for 1, not some register's LocalExpr/garbage read."""
    import struct
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, Assign
    from pyluadec.express.expr import BinExpr, ConstExpr
    p, fn = _proto_and_fn("local a = 1 a = a + 1 return a", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    assigns = [s for s in stmts if isinstance(s, Assign)]
    assert len(assigns) == 1
    add = assigns[0].exprs[0]
    assert isinstance(add, BinExpr) and add.op == "+"
    assert isinstance(add.rhs, ConstExpr)
    assert struct.unpack("<d", add.rhs.value.payload)[0] == 1.0


def test_temp_read_pops_environment_single_use(tmp_path):
    """Direct proof of the pop-on-read invariant fault-injection targets:
    after reconstructing, a Reconstructor built manually and driven through
    stmts_for must have removed every temp register it inlined from its
    env -- nothing is left over to be accidentally reused by a later
    take_expr/cond_operand call."""
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import Reconstructor
    p, fn = _proto_and_fn(
        "local a = 1 local b = 2 local c = a + b print(c) return c", tmp_path)
    rc = classify_registers(fn)
    r = Reconstructor(fn, rc, depth=0)
    r.stmts_for(tuple(fn.instrs[i] for i in sorted(fn.instrs)))
    # a and b were single-use temps consumed by the ADD; they must not
    # remain in the environment afterward.
    assert 0 not in r.env or fn.proto.numparams > 0
    assert not (rc.temps & set(r.env))


def test_self_method_call_does_not_duplicate_receiver(tmp_path):
    """'local t = {} function t.f(self) end t:f()' (approximated with a
    plain global self-call) exercises SELF -> CALL fusion. The receiver
    expression must be embedded exactly once in the resulting CallExpr
    (is_method=True) -- not once via a materialized register AND again via
    a raw IndexExpr, which would duplicate evaluation of the receiver if it
    were itself an effectful expression."""
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, ExprStmt
    from pyluadec.express.expr import CallExpr
    p, fn = _proto_and_fn("local t = {} t:f()", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    calls = [s.call for s in stmts if isinstance(s, ExprStmt)]
    assert calls and calls[0].is_method and calls[0].method == b"f"


def test_loop_var_never_gets_a_localdecl(tmp_path):
    """FORPREP/FORLOOP's loop variable register (rc.loop_vars) must never be
    the target of a LocalDecl emitted by reconstruct_straight -- it is
    declared by the `for` statement itself (Task 6/7), not by this layer.

    'for i = 1, 3 do i = i + 10 print(i) end' is deliberately chosen so the
    loop body *writes back* to the loop variable (legal Lua: reassigning i
    inside the body doesn't affect iteration) -- this is the one shape that
    actually calls write_reg on a loop_vars register and would surface a
    missing "pre-seed declared" guard. A body that only *reads* i (e.g.
    plain 'print(i)') never calls write_reg for register 3 at all, so it
    would pass even with that guard entirely missing -- see the comment in
    Reconstructor.__init__ (`self.declared = set(rc.loop_vars)`) for why the
    guard is needed and this file's mutation (a) below for the fault
    injection that confirms it's load-bearing.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl, Assign
    from pyluadec.lift import Op
    p, fn = _proto_and_fn("for i = 1, 3 do i = i + 10 print(i) end", tmp_path)
    rc = classify_registers(fn)
    assert rc.loop_vars
    body_pcs = [pc for pc in sorted(fn.instrs)
                if fn.instrs[pc].ri.op not in (Op.FORPREP, Op.FORLOOP)]
    stmts = reconstruct_straight(fn, tuple(fn.instrs[pc] for pc in body_pcs), rc, depth=0)
    declared_regs = {r for s in stmts if isinstance(s, LocalDecl) for r in s.regs}
    assert not (declared_regs & rc.loop_vars)
    # and the write really did happen, as an Assign (not silently dropped)
    assigned_regs = {t.reg for s in stmts if isinstance(s, Assign)
                     for t in s.targets if hasattr(t, "reg")}
    assert rc.loop_vars & assigned_regs

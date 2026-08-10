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

import pytest

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


def test_self_dynamic_key_falls_back_to_index_expr_without_duplicating_receiver():
    """SELF's method-key operand (C) as a plain register (not an RK
    constant) -- real luac output never produces this (Lua's `:` syntax
    always compiles the method name to a literal constant), but SELF's own
    bytecode format permits it, and `_self`'s dynamic-key branch (the `else`
    of the `isk(c) and isinstance(..., bytes)` check) had no dedicated
    regression test -- the existing SELF test
    (test_self_method_call_does_not_duplicate_receiver) only exercises the
    constant-key, is_method=True fusion path. Verifies: (1) it falls back to
    a plain IndexExpr (a dynamic key can't use `:` sugar), and (2) the
    receiver is referenced via the materialized register (LocalExpr), never
    re-embedding the raw (potentially effectful) object expression a second
    time -- the same duplication hazard the constant-key test pins,
    reproduced with a hand-built SELF/Reconstructor (real luac never emits
    this exact shape, so it can't be driven from compiled source).
    """
    from pyluadec.express.names import RegClass
    from pyluadec.express.reconstruct import Reconstructor, LocalDecl
    from pyluadec.express.expr import CallExpr, GlobalExpr, IndexExpr, LocalExpr
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    self_ri = mk_instr(Op.SELF, a=6, b=5, c=9, pc=1)   # c: plain register, K bit NOT set
    self_fx = InstrEffects(reads=frozenset({5, 9}), writes=frozenset({6, 7}),
                            reads_open=False, writes_open=False,
                            effect=Effect.ARBITRARY, may_error=True)
    instrs = {1: LirInstr(ri=self_ri, effects=self_fx, successors=(), consumed=())}
    proto = mk_proto((0,), numparams=0, maxstacksize=10)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=1,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = RegClass(locals=frozenset({9}), temps=frozenset({5, 6, 7}), loop_vars=frozenset())
    rec = Reconstructor(fn, rc, depth=0)
    receiver_call = CallExpr(GlobalExpr(b"getObj"), ())
    rec.env[5] = receiver_call            # reg 5 already holds a staged (effectful) call

    stmts = rec.stmts_for((instrs[1],))

    # the receiver was materialized exactly once, as reg 7 (a+1)
    decls = [s for s in stmts if isinstance(s, LocalDecl)]
    assert len(decls) == 1
    assert decls[0].regs == (7,) and decls[0].exprs == (receiver_call,)

    def count(node, target) -> int:
        n = 1 if node == target else 0
        if hasattr(node, "__dataclass_fields__"):
            for f in node.__dataclass_fields__:
                n += count(getattr(node, f), target)
        elif isinstance(node, (tuple, list)):
            for item in node:
                n += count(item, target)
        return n

    assert sum(count(s, receiver_call) for s in stmts) == 1

    # reg 6 (the method-lookup result, temp, still pending) references the
    # materialized reg 7 -- not the raw receiver_call -- and reg 9's key
    # via plain register read (not treated as a constant).
    assert rec.env.get(6) == IndexExpr(LocalExpr(7), LocalExpr(9))


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


# ---- M3 task-5 round-1 review fixes ---------------------------------------
#
# Findings 1-4 from the coordinator's first fix round (see
# task-5-report.md's "Round 1" section for the full corpus investigation):
#   1. Nested/interrupted table constructors crashed rather than degrading
#      (an unconditional NEWTABLE-triggered close plus a pop-once write for
#      a register that gets re-read later). Fixed via a table-context STACK
#      (only a genuine register conflict forces a close) plus a
#      write-count/read-count census (_reliable_temps) that stops trusting
#      rc.temps for a register with more than one static write or read
#      anywhere in the function -- rc.temps can be true for reasons
#      (FORPREP/FORLOOP/TFORLOOP's per-register-number `controls` override)
#      that have nothing to do with any *specific* def/use pair being
#      single-use. (Round 2 moved this census into
#      express.names.classify_registers itself -- see that module and
#      test_express_names.py -- so RegClass.temps is correct at the
#      source and reconstruct.py trusts it directly again;
#      _reliable_temps no longer exists here.)
#   2. SELF/method-call fusion re-embedded the raw (possibly effectful)
#      receiver expression twice instead of referencing the one
#      materialized local -- fixed by referencing LocalExpr(a+1)/LocalExpr(
#      a1), never the raw `obj` tree, after force_materialize.
#   3. SETLIST's batch index (C) was silently ignored; a second/later batch
#      (>50 array elements) would silently write to the wrong indices.
#      Fixed with an explicit refusal for C != 1.
#   4. LOADBOOL's C!=0 skip-next form wasn't explicitly refused (only
#      accidentally unreachable via an upstream SIR invariant). Fixed with
#      an explicit refusal.

def test_nested_table_constructor_reconstructs_without_crashing(tmp_path):
    """Finding 1 regression pin: 'local t = {a=1, b={}, c=2} return t' --
    a table literal with another table literal as one of its own values,
    interrupting the outer NEWTABLE's SETLIST/SETTABLE fold with a nested
    NEWTABLE -- must not raise, and the nested `{}` should fold straight
    into the outer TableExpr's hash value (not degrade to a separately
    declared local), since it is genuinely single-write/single-read.

    This exact shape (empirically confirmed against the real corpus,
    snr_common.lua's main chunk) used to raise
    "temp register 0 read before it was staged" before the round-1 fix:
    _close_table_ctx used to unconditionally close on any NEWTABLE and
    write_reg (pop-once) the partial table into a temp register that then
    got read a second time by the very next SETTABLE.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl
    from pyluadec.express.expr import TableExpr
    p, fn = _proto_and_fn("local t = {a=1, b={}, c=2} return t", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    decls = [s for s in stmts if isinstance(s, LocalDecl)
             and any(isinstance(e, TableExpr) for e in s.exprs)]
    assert decls
    outer = decls[0].exprs[0]
    assert isinstance(outer, TableExpr)
    nested_values = [v for _, v in outer.hash if isinstance(v, TableExpr)]
    assert nested_values == [TableExpr(array=(), hash=())]
    # and nothing else in the whole reconstruction separately declares a
    # second local for the (fully-inlined) nested table
    assert len(decls) == 1


def test_self_receiver_not_duplicated_across_stmts_for_boundary():
    """Finding 2 regression pin, reproduced exactly as the reviewer
    described: drive a Reconstructor across TWO separate stmts_for() calls
    with a SELF and its matching CALL split across that boundary -- the
    shared-environment-across-regions usage documented on the Reconstructor
    class. Register 5 (the receiver) is hand-staged as a *pending, unpopped*
    effectful expression (a call to getObj()) rather than derived from real
    luac output, because real luac output never actually produces this
    exact split (SELF is always immediately followed by its own CALL in the
    same straight run) -- this is the "IR luac never would produce, but the
    code must still not silently mishandle" category test_express_names.py
    already uses this pattern for (see e.g.
    test_open_region_write_between_def_and_use_forces_local).

    Before the round-1 fix, _self's dynamic-key branch and
    _finalize_pending's unconsumed-SELF flush both re-embedded the raw
    `obj` expression a second time (as the table of an IndexExpr) instead
    of referencing the one force_materialize'd local -- so getObj() would
    appear twice in the reconstructed tree, meaning Task 6's printer would
    silently emit code that calls getObj() twice instead of once.
    """
    from pyluadec.express.names import RegClass
    from pyluadec.express.reconstruct import Reconstructor
    from pyluadec.express.expr import CallExpr, GlobalExpr
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    self_ri = mk_instr(Op.SELF, a=6, b=5, c=0 | 256, pc=1)   # c: K bit set, const index 0 ("f")
    self_fx = InstrEffects(reads=frozenset({5}), writes=frozenset({6, 7}),
                            reads_open=False, writes_open=False,
                            effect=Effect.ARBITRARY, may_error=True)
    call_ri = mk_instr(Op.CALL, a=6, b=1, c=1, pc=2)         # obj:f() -- no extra args, no results
    call_fx = InstrEffects(reads=frozenset({6}), writes=frozenset(),
                            reads_open=False, writes_open=False,
                            effect=Effect.ARBITRARY, may_error=True)
    instrs = {
        1: LirInstr(ri=self_ri, effects=self_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=call_ri, effects=call_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0, 0), constants=(b"f",), numparams=0, maxstacksize=8)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=2,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = RegClass(locals=frozenset(), temps=frozenset({5, 6, 7}), loop_vars=frozenset())
    rec = Reconstructor(fn, rc, depth=0)
    receiver_call = CallExpr(GlobalExpr(b"getObj"), ())
    rec.env[5] = receiver_call                              # reg 5 already holds a staged call

    chunk1 = rec.stmts_for((instrs[1],))                     # SELF only
    chunk2 = rec.stmts_for((instrs[2],))                     # its CALL, a separate stmts_for() call

    def count(node, target) -> int:
        n = 1 if node == target else 0
        if hasattr(node, "__dataclass_fields__"):
            for f in node.__dataclass_fields__:
                n += count(getattr(node, f), target)
        elif isinstance(node, (tuple, list)):
            for item in node:
                n += count(item, target)
        return n

    total = sum(count(s, receiver_call) for s in chunk1 + chunk2)
    assert total == 1, f"getObj() receiver embedded {total} times, expected exactly 1"


def test_setlist_second_batch_refuses(tmp_path):
    """Finding 3: SETLIST's C (batch index) selects which 50-element
    LFIELDS_PER_FLUSH chunk the array elements land in; this reconstructor
    only computes plain 1..b positions (batch 1). A synthetic C=2 SETLIST
    (unreachable on the current corpus -- all 92 real SETLIST instructions
    have C==1 -- but exactly what a >50-element array literal would compile
    to) must raise rather than silently writing to the wrong indices.
    """
    from pyluadec.express.reconstruct import Reconstructor, ReconstructError
    from pyluadec.express.names import RegClass
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    newtable_ri = mk_instr(Op.NEWTABLE, a=0, b=0, c=0, pc=1)
    newtable_fx = InstrEffects(reads=frozenset(), writes=frozenset({0}),
                                reads_open=False, writes_open=False,
                                effect=Effect.PURE, may_error=False)
    loadk_ri = mk_instr(Op.LOADK, a=1, bx=0, pc=2)
    loadk_fx = InstrEffects(reads=frozenset(), writes=frozenset({1}),
                             reads_open=False, writes_open=False,
                             effect=Effect.PURE, may_error=False)
    setlist_ri = mk_instr(Op.SETLIST, a=0, b=1, c=2, pc=3)   # C=2: second batch
    setlist_fx = InstrEffects(reads=frozenset({0, 1}), writes=frozenset(),
                               reads_open=False, writes_open=False,
                               effect=Effect.ARBITRARY, may_error=True)
    instrs = {
        1: LirInstr(ri=newtable_ri, effects=newtable_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=loadk_ri, effects=loadk_fx, successors=(3,), consumed=()),
        3: LirInstr(ri=setlist_ri, effects=setlist_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0, 0, 0), constants=(None,), numparams=0, maxstacksize=8)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=3,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = RegClass(locals=frozenset(), temps=frozenset({1}), loop_vars=frozenset())
    rec = Reconstructor(fn, rc, depth=0)
    with pytest.raises(ReconstructError, match="batch"):
        rec.stmts_for(tuple(instrs[i] for i in (1, 2, 3)))


def test_loadbool_skip_next_form_refuses():
    """Finding 4: LOADBOOL with C!=0 means "skip the next instruction"
    (lvm.c's dojump) -- a control-flow effect reconstruct_straight cannot
    represent. Real luac output never feeds this to reconstruct_straight
    (a non-fallthrough LOADBOOL always forces the whole function to the SIR
    fallback), but that must not be the only thing standing between this
    module and silently dropping the skip -- refuse explicitly.
    """
    from pyluadec.express.reconstruct import Reconstructor, ReconstructError
    from pyluadec.express.names import RegClass
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    ri = mk_instr(Op.LOADBOOL, a=0, b=1, c=1, pc=1)          # C=1: skip-next form
    fx = InstrEffects(reads=frozenset(), writes=frozenset({0}),
                       reads_open=False, writes_open=False,
                       effect=Effect.PURE, may_error=False)
    instrs = {1: LirInstr(ri=ri, effects=fx, successors=(3,), consumed=())}
    proto = mk_proto((0,), numparams=0, maxstacksize=4)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=1,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = RegClass(locals=frozenset({0}), temps=frozenset(), loop_vars=frozenset())
    rec = Reconstructor(fn, rc, depth=0)
    with pytest.raises(ReconstructError, match="LOADBOOL"):
        rec.stmts_for((instrs[1],))

# Round-1's test_reliable_temps_census_rescues_a_multiply_written_forced_temp
# (a direct unit pin for reconstruct.py's own defensive write/read census)
# was removed in round 2: that census (_reliable_temps) moved into
# express.names.classify_registers itself, so RegClass.temps is correct by
# the time it reaches this module and reconstruct.py trusts rc.temps
# directly again. The equivalent scenario -- a register that is a loop's
# control slot in one range and a multiply-written/read ordinary local
# elsewhere in the same function -- is now pinned in test_express_names.py
# (test_controls_register_reused_as_ordinary_local_classifies_local), closer
# to where the fix actually lives.


def _all_stmts(fn):
    """Drive a single Reconstructor over the whole SIR region tree in program
    order -- the way Task 6's printer will -- and return every statement it
    produced. for-headers consume their control slots via take_expr, exactly
    as the printer must, so a control slot that was wrongly classified temp
    still gets popped here rather than quietly surviving in the environment.
    """
    from pyluadec import sir as S
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import Reconstructor
    from pyluadec.sir import build_sir

    rc = classify_registers(fn)
    rec = Reconstructor(fn, rc, depth=0)
    out = []

    def walk(r):
        t = type(r)
        if t is S.Straight:
            out.extend(rec.stmts_for(r.instrs))
        elif t is S.Return:
            out.extend(rec.stmts_for((r.instr,)))
        elif t is S.Seq:
            for child in r.body:
                walk(child)
        elif t is S.If:
            walk(r.then_body)
            if r.else_body is not None:
                walk(r.else_body)
        elif t is S.NumericFor:
            for i in range(3):
                rec.take_expr(r.prep.ri.a + i)
            walk(r.body)
        elif t is S.GenericFor:
            for i in range(3):
                rec.take_expr(r.call.ri.a + i)
            walk(r.body)

    walk(build_sir(fn))
    return rc, tuple(out)


def test_local_before_a_for_loop_reusing_its_register_is_not_deleted(tmp_path):
    """Round-4 review, case A, at the level where the damage actually shows.

    `do local x = 5 end for i = 1, 3 do print(i) end`: when register 0 is
    misclassified temp (round 3 did), `local x = 5` is popped into the
    for-header's init operand and the statement is simply gone -- no
    exception, no warning, one fewer statement in the output. Assert the
    constant 5 still reaches a statement.
    """
    from pyluadec.express.reconstruct import Assign, LocalDecl
    from pyluadec.express.expr import ConstExpr
    p, fn = _proto_and_fn("do local x = 5 end for i = 1, 3 do print(i) end", tmp_path)
    rc, stmts = _all_stmts(fn)
    fives = [s for s in stmts
             if isinstance(s, (LocalDecl, Assign))
             and any(isinstance(e, ConstExpr) and e.value.value == 5.0 for e in s.exprs)]
    assert len(fives) == 1, f"`local x = 5` lost; statements were {stmts}"
    assert 0 in rc.locals            # the classification that makes it so


def test_mutated_local_before_two_loops_is_not_deleted(tmp_path):
    """Round-4 review, case C. `do local z = 1 z = z + 1 z = z + 1 end`
    followed by two register-0 loops: all three of z's statements must
    appear. Round 3 emitted two statements total for the whole function.
    """
    from pyluadec.express.reconstruct import Assign, LocalDecl
    from pyluadec.express.expr import BinExpr
    p, fn = _proto_and_fn(
        "do local z = 1  z = z + 1  z = z + 1 end "
        "for i = 1, 3 do end for j = 1, 5 do print(j) end", tmp_path)
    rc, stmts = _all_stmts(fn)
    increments = [s for s in stmts
                  if isinstance(s, (LocalDecl, Assign))
                  and any(isinstance(e, BinExpr) and e.op == "+" for e in s.exprs)]
    assert len(increments) == 2, f"`z = z + 1` lost; statements were {stmts}"
    # z's initialiser too: four register-0 statements in all (z = 1, the two
    # increments, and loop 2's own init write -- loop 1's init is the first
    # write of register 0 in the function and so is z's own LocalDecl).
    assert sum(isinstance(s, (LocalDecl, Assign)) for s in stmts) == 5
    assert 0 in rc.locals            # the classification that makes it so


def test_genuine_for_control_slots_still_inline_into_the_header(tmp_path):
    """The counterweight: a for loop with no register reuse must still emit
    NO statement for its control slots -- a fix that demoted them would
    produce `local` declarations for init/limit/step and change register
    allocation. `for i = 1, 3 do print(i) end` reconstructs to exactly the
    body call plus the trailing return.
    """
    from pyluadec.express.reconstruct import Assign, ExprStmt, LocalDecl, ReturnStmt
    p, fn = _proto_and_fn("for i = 1, 3 do print(i) end", tmp_path)
    rc, stmts = _all_stmts(fn)
    assert {0, 1, 2} <= rc.temps
    assert not any(isinstance(s, (LocalDecl, Assign)) for s in stmts)
    assert [type(s) for s in stmts] == [ExprStmt, ReturnStmt]


def test_partially_demoted_generic_for_triple_reconstructs(tmp_path):
    """M3 task-5 round-5 review: `_emit_multi` used to refuse a multi-result
    write whose targets mix already-declared and fresh registers.

    `local t = {} do local x = 5 end for k, v in pairs(t) do end`: `x` goes
    out of scope, so luac reuses its register as the generic-for's iterator
    base. classify_registers correctly calls that base a local (it is `x`
    too) while the state/control slots stay temp -- and the staging
    `CALL a 2 4` writes all three at once, so one Lua statement has to
    assign to one existing local and two new ones.

    Round 3 "handled" this shape by classifying the base temp, which
    silently deleted `local x = 5`; round 4 classified it correctly and then
    raised here, refusing the whole function. Neither is acceptable: the
    mixed case is expressible as `local <fresh>` followed by a multi-assign
    over all three, which is what this now emits. `local a, b, c = ...`
    would NOT do -- a second `local` of an existing name shadows it rather
    than assigning to it.
    """
    from pyluadec.express.reconstruct import Assign, LocalDecl, LocalTarget
    from pyluadec.express.expr import ConstExpr
    p, fn = _proto_and_fn(
        "local t = {} do local x = 5 end for k, v in pairs(t) do end", tmp_path)
    rc, stmts = _all_stmts(fn)
    # the base is local, the other two control slots are still temp
    assert 1 in rc.locals and {2, 3} <= rc.temps
    # `local x = 5` survived
    assert [s for s in stmts
            if isinstance(s, LocalDecl)
            and any(isinstance(e, ConstExpr) and e.value.value == 5.0
                    for e in s.exprs)]
    # ... and the mixed multi-result write became `local r2, r3` + one
    # three-target assignment, not a refusal and not a shadowing redeclaration
    assert LocalDecl((2, 3), ()) in stmts
    multi = [s for s in stmts if isinstance(s, Assign) and len(s.targets) == 3]
    assert len(multi) == 1
    assert multi[0].targets == (LocalTarget(1), LocalTarget(2), LocalTarget(3))
    assert not any(isinstance(s, LocalDecl) and 1 in s.regs and s.exprs
                   and s.regs != (1,) for s in stmts)

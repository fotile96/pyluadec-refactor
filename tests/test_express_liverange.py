"""M4 task 13: register classification is per (register, definition), not per
register number.

The property under test, stated once:

    a register is materialized as a named `local` **iff** luac's parser would
    have had an active local variable in that slot at that pc.

`lparser.c` resets `fs->freereg = fs->nactvar` at the end of every statement
(`:1334`) and asserts `freereg >= nactvar` throughout (`:1333`), so one slot is
routinely a declared local in one statement and expression-stack scratch in the
next. A whole-function verdict per register *number* cannot express that, and
the conservative answer -- `local` -- materializes luac's expression stack as
named locals and emits the `MOVE`s that copy into it.

Both directions break certification, so both are fixtured here:

  * `TEMP_CASES` -- staging registers that must NOT become locals. Before this
    task each of these recompiled with extra `MOVE`s and certified `L1`.
  * `LOCAL_CASES` -- genuine locals that must NOT be inlined away. Each one has
    a reason the pc-linear freereg simulation would otherwise call it a
    temporary: a second read, a read through a back edge, or an operand
    position where `lcode.c` would have used a constant rather than a register.

Every case is oracle-compiled with the real `luac_sz4` and adjudicated by
`certify_proto`, which recompiles the printed source and compares the resulting
proto field-by-field under the normalization ladder. Nothing here relaxes the
gate. `LOCAL_CASES` additionally run both the original bytecode and the printed
source under `lua_sz4` and diff stdout, because the failure mode in that
direction is not merely a fidelity loss: an over-inlined local disappears from
the output and its later reads resolve as *globals*.

All fixture sources are pure ASCII by construction, so assertions that inspect
printed text may decode; bytecode-derived strings elsewhere stay `bytes`.
"""
import pytest

from pyluadec.emit.lua import print_chunk
from pyluadec.express.names import classify_registers
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.structure.structured import certify_proto

# --- direction 1: staging registers must stay temporaries -----------------
# Every one of these has at least one register that is a declared local in one
# statement and call-staging scratch in another. `snr_crd_10.lua:main_2`, the
# corpus exemplar this task was scoped from, is the third shape: registers
# 0/1/2 stage a two-argument call, then the same three slots become the loop's
# counters.
TEMP_CASES = [
    # The brief's first required shape: a bare two-argument global call whose
    # arguments are locals. luac emits `GETGLOBAL; MOVE; MOVE; CALL` with the
    # two MOVEs staging *from* the locals; materializing the staging slots as
    # locals of their own adds three more MOVEs.
    b"local a, b = 1, 2 f(a, b) print(a, b)",
    # ... and with the same slots reused as a local afterwards, which is what
    # forced the whole-function verdict to `local` before this task.
    b"f(1, 2) local a = 3 local b = 4 print(a, b)",
    # The corpus exemplar's shape, reduced: stage a two-argument call, then
    # declare locals into the very same registers and loop on them.
    b"f(g, h) local i = 0 local n = 0 while i < 3 do i = i + 1 n = n + i end print(n)",
    # The brief's second required shape: a call whose arguments are themselves
    # calls.
    b"print(f(1), g(2))",
    b"print(string.format('%d', 42))",
    # The brief's third required shape: a call in a loop body reusing the same
    # registers on every iteration.
    b"for i = 1, 3 do f(i, i + 1) g(i) end",
    b"local i = 0 while i < 3 do f(i, i) i = i + 1 end",
    # A `for` header whose control base is also the enclosing `while`'s
    # condition slot -- one register number, two unrelated jobs.
    b"while a do for i = 1, 10 do f(i) end end",
    # Method calls: SELF stages the receiver into a slot that a later
    # statement declares a local into.
    b"local t = {} t:m(1) local x = 5 print(x)",
]

# --- direction 2: genuine locals must stay locals --------------------------
# Each entry is (source, expected stdout words). The expectation is measured
# from the ORIGINAL bytecode inside the test, not hard-coded here -- the words
# are recorded only so a fixture that silently stops exercising anything is
# visible.
LOCAL_CASES = [
    # The brief's required opposite-direction guard: `x` is read twice, so
    # inlining it into the first use loses it for the second.
    (b"local x = f() g(x) h(x)", None),
    # Read twice with the second read after a statement boundary that the
    # freereg simulation sees; the plain single-read version of this is a
    # temporary and must stay one (covered by TEMP_CASES above).
    (b"local x = 1 print(x) print(x)", [b"1", b"1"]),
    # Defined OUTSIDE a loop, read INSIDE it: the pc-linear walk sees exactly
    # one read and would call it a temporary, which moves `local i = 0` into
    # the loop body and never terminates. Pinned by `_same_loops`.
    (b"local i = 0 repeat i = i + 1 until i > 5 print(i)", [b"6"]),
    (b"local i = 0 while i < 4 do i = i + 1 end print(i)", [b"4"]),
    # Defined INSIDE a loop, read AFTER it: the mirror image. Inlining hoists
    # the work out of the loop.
    (b"local x = 0 for i = 1, 3 do x = i end print(x)", [b"3"]),
    # Read once, but in an RK operand slot. `luaK_exp2RK` encodes a literal
    # straight into B/C, so the original's use of a *register* there proves
    # the slot held a local; inlining prints `1 + 1`, which luac folds back
    # into a single LOADK.
    (b"local a = 1 a = a + 1 print(a)", [b"2"]),
    (b"local a = 1 if a == 2 then print('eq') else print('ne') end", [b"ne"]),
    (b"local a = 2 print(a * 3)", [b"6"]),
    # The unary-fold half of the same rule: `luaK_prefix` folds `-1`/`not 1`
    # at parse time, so an `UNM`/`NOT` reading a register proves that register
    # was not a literal.
    (b"local a = 1 a = -a print(a)", [b"-1"]),
    (b"local a = 1 a = not a print(a)", [b"false"]),
    # A string literal in an RK slot (EQ's C), same rule, non-numeric.
    (b"local s = 'v' if s == 'x' then print(1) else print(2) end", [b"2"]),
    # Defined in one basic block, read in another: exactly one read, so the
    # pc-linear walk would call it a temporary, but the read is inside a
    # conditional/loop body. `open_scope`/`close_scope` roll the pop back at
    # the block's `end`, so the block's whole statement disappears from the
    # output. Pinned by `_same_block`.
    (b"function f() return 7 end function g(v) print(v) end "
     b"local x = f() if x then g(x) end", [b"7"]),
    (b"function f() return 7 end function g(v) print(v) end "
     b"local x = f() for i = 1, 2 do g(x) end", [b"7", b"7"]),
    # `MOVE d, s` with `s < d`: `luaK_exp2nextreg` copies a VLOCAL upward and
    # never copies a temporary (a temporary is already at `freereg - 1`), so
    # the copy itself proves the source slot held a named local. Without that
    # rule the whole reassignment chain collapses into one nested expression
    # and every `MOVE` disappears from the recompile.
    (b"function h(p) local n = p n = string.gsub(n, 'a', 'b') return n end "
     b"print(h('aaa'))", [b"bbb"]),
    (b"local function h(p) local n = p n = tostring(n) return n end print(h(5))",
     [b"5"]),
]

# Same direction, but the ORIGINAL program does not terminate, so only the
# certification half applies (running it would hang the suite).
LOCAL_CASES_CERT_ONLY = [
    # The one shape on this project's fixtures where `_same_block` is the ONLY
    # rule that keeps a definition local (measured by neutering each rule in
    # turn, M4 task 13): the `or` chain's result register is redefined inside
    # the `while` body, and the pre-loop definition's single read is the
    # loop's own condition, in a different block. Also asserted by
    # tests/test_express_testset.py::test_fixtures_certify_l3.
    b"local b, c = 1, 2 local a = b or c while a do a = b or c end print(a)",
]


def _certifies(src: bytes):
    p = load_bytes(compile_source(src, strip=True))
    return p, certify_proto(p, is_chunk_root=True)


@pytest.mark.parametrize("src", TEMP_CASES, ids=range(len(TEMP_CASES)))
def test_staging_registers_are_not_materialized_as_locals(src):
    p, cert = _certifies(src)
    assert cert.level == "L3", (src, cert.mismatches)


@pytest.mark.parametrize("src,words", LOCAL_CASES,
                         ids=range(len(LOCAL_CASES)))
def test_genuine_locals_are_not_inlined_away(src, words):
    p, cert = _certifies(src)
    assert cert.level == "L3", (src, cert.mismatches)
    printed = print_chunk(p)
    assert printed is not None
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode), printed
    if words is not None:
        assert a.stdout.split() == words


@pytest.mark.parametrize("src", LOCAL_CASES_CERT_ONLY,
                         ids=range(len(LOCAL_CASES_CERT_ONLY)))
def test_genuine_locals_are_not_inlined_away_cert_only(src):
    _, cert = _certifies(src)
    assert cert.level == "L3", (src, cert.mismatches)


def test_one_register_is_both_a_temp_and_a_local_in_the_same_function():
    """The property, read directly off `RegClass` rather than through the
    gate: register 0 below is call-staging scratch at pc 0 and a declared
    local later, so it is in `locals` (the whole-register verdict, which must
    stay conservative) while its *staging* definition is in `temp_defs`.

    This is the invariant `temps` alone cannot express, and the reason
    `reconstruct.write_reg` keys on `(pc, reg)`.
    """
    src = b"f(1, 2) local a = 3 local b = 4 print(a, b)"
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    rc = classify_registers(fn)
    staging_pc = min(pc for pc in fn.instrs if 0 in fn.instrs[pc].effects.writes)
    later = [pc for pc in fn.instrs if 0 in fn.instrs[pc].effects.writes
             and pc > staging_pc]
    assert later, "fixture no longer reuses register 0"
    assert 0 in rc.locals and 0 not in rc.temps       # whole-register verdict
    assert (staging_pc, 0) in rc.temp_defs            # ... but this def is a temp
    assert any((pc, 0) not in rc.temp_defs for pc in later)


def test_temp_defs_refines_temps_rather_than_contradicting_it():
    """`RegClass`' documented invariant, checked on every fixture in this
    file: for every `r in temps`, every tracked definition `(pc, r)` is in
    `temp_defs`. `reconstruct.write_reg` reads the two as a disjunction and
    would silently diverge from `classify_registers` if this ever broke.
    """
    for src in TEMP_CASES + [s for s, _ in LOCAL_CASES] + LOCAL_CASES_CERT_ONLY:
        fn = lift_proto(load_bytes(compile_source(src, strip=True)))
        rc = classify_registers(fn)
        for pc, li in fn.instrs.items():
            for r in li.effects.writes:
                if r in rc.temps:
                    assert (pc, r) in rc.temp_defs, (src, pc, r)


def test_reassigning_a_register_a_staged_expression_names_is_refused():
    """`Reconstructor._refuse_stale_reference`, pinned by injection.

    `_read_reg` returns `LocalExpr(reg)` -- a name -- for a materialized
    register, and a staged expression is not printed until its consumer is.
    Reassigning `reg` in between makes the staged tree print the NEW value.
    Reached for real before this task's `VKNUM`/`MAXINDEXRK` correction
    (`snr_crd_15.lua:main_1` printed `gameSave[l1_1][l1_1][l1_1] = l1_2`) and
    reached by 0 of 1478 corpus protos after it, so it is driven here by
    hand: register 3 holds a staged `IndexExpr` naming register 1, and the
    `GETGLOBAL` then materializes register 1.

    Neuter check (M4 task 13): deleting the `_refuse_stale_reference(reg)`
    call at the top of `force_materialize` makes this test fail with
    `DID NOT RAISE`.
    """
    from pyluadec.express.expr import IndexExpr, LocalExpr, ConstExpr
    from pyluadec.express.names import RegClass
    from pyluadec.express.reconstruct import ReconstructError, Reconstructor
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    ri = mk_instr(Op.GETGLOBAL, a=1, bx=0, pc=1)
    fx = InstrEffects(reads=frozenset(), writes=frozenset({1}),
                      reads_open=False, writes_open=False,
                      effect=Effect.READ_HEAP, may_error=True)
    instrs = {1: LirInstr(ri=ri, effects=fx, successors=(), consumed=())}
    proto = mk_proto((0,), constants=(b"g",), numparams=0, maxstacksize=8)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=1,
                     captured_regs=frozenset(), closure_pseudo={})
    # Register 1 is a declared local; register 3 holds a staged expression
    # that refers to it by name. GETGLOBAL then reassigns register 1.
    rc = RegClass(locals=frozenset({1}), temps=frozenset({3}),
                  loop_vars=frozenset())
    rec = Reconstructor(fn, rc, depth=0)
    rec.force_materialize(1, ConstExpr(None))
    rec.stage(3, IndexExpr(LocalExpr(1), ConstExpr(b"k")))
    with pytest.raises(ReconstructError, match="still refers to it by name"):
        rec.stmts_for((instrs[1],))


def test_reading_a_consumed_staging_register_again_is_refused():
    """`Reconstructor._read_reg`'s `_consumed` refusal, pinned by injection.

    A definition graded a temporary is staged, not emitted; the first read
    pops and inlines it. A SECOND read has nothing to name -- `LocalExpr(reg)`
    would print an identifier this function never declares, which Lua resolves
    as a *global*. `_stack_discipline` only grades a definition a temporary
    when its value is read exactly once before the statement ends, so this is
    unreachable whenever that accounting is right; it is the refusal that
    converts a mistake in the accounting from silent wrongness into a
    fallback. Driven by hand with a `RegClass` that claims a definition is a
    temporary while the instruction stream reads it twice -- 0 of 1478 corpus
    protos reach it.

    Neuter check (M4 task 13): replacing the `if reg in self._consumed:`
    refusal with `if False and ...` makes this test fail with `DID NOT RAISE`,
    and the second read then prints as a bare global reference.
    """
    from pyluadec.express.names import RegClass
    from pyluadec.express.reconstruct import ReconstructError, Reconstructor
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    heap = dict(reads_open=False, writes_open=False, effect=Effect.READ_HEAP,
                may_error=True)
    instrs = {
        # reg 1 <- _ENV.g          (the staged temp)
        1: LirInstr(ri=mk_instr(Op.GETGLOBAL, a=1, bx=0, pc=1),
                    effects=InstrEffects(reads=frozenset(),
                                         writes=frozenset({1}), **heap),
                    successors=(2,), consumed=()),
        # reg 2 <- reg 1[k]        (first read: pops and inlines it)
        2: LirInstr(ri=mk_instr(Op.GETTABLE, a=2, b=1, c=256, pc=2),
                    effects=InstrEffects(reads=frozenset({1}),
                                         writes=frozenset({2}), **heap),
                    successors=(3,), consumed=()),
        # reg 3 <- reg 1[k]        (second read: nothing left to name)
        3: LirInstr(ri=mk_instr(Op.GETTABLE, a=3, b=1, c=256, pc=3),
                    effects=InstrEffects(reads=frozenset({1}),
                                         writes=frozenset({3}), **heap),
                    successors=(), consumed=()),
    }
    proto = mk_proto((0, 0, 0), constants=(b"g",), maxstacksize=8)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=3,
                     captured_regs=frozenset(), closure_pseudo={})
    rc = RegClass(locals=frozenset(), temps=frozenset(),
                  loop_vars=frozenset(),
                  temp_defs=frozenset({(1, 1), (2, 2), (3, 3)}))
    rec = Reconstructor(fn, rc, depth=0)
    with pytest.raises(ReconstructError, match="read again after its staged"):
        rec.stmts_for(tuple(instrs[pc] for pc in sorted(instrs)))


# --- residual: shapes this task does NOT fix ------------------------------
# Both were `L1` before M4 task 13 as well (measured on `dec379e`), so neither
# is a regression; they are recorded here, adjacent to the fixtures they were
# drafted alongside, so the next census (Task 6) inherits the diagnosis rather
# than re-deriving it.
KNOWN_RESIDUAL = [
    # `_emit_multi`: a `CALL` with several fixed results is one `Expr` and
    # cannot be split into independently-inlinable per-register pieces, so
    # every target is materialized. A generic `for` over `pairs(t)` therefore
    # prints `local l0_1, l0_2, l0_3 = pairs(l0_0)` where luac left the triple
    # in the control slots, and the recompile grows three MOVEs. Nothing to do
    # with register classification: all three slots are already in `rc.temps`.
    b"local t = {} for k, v in pairs(t) do f(k, v) g(k) end",
    # NEWTABLE's size hints. The constructor fold turns a following
    # `t.k = s` statement into `{["k"] = s}`, so the recompiled NEWTABLE
    # carries a hash-size hint of 1 where the original had 0.
    b"local s = 'v' local t = {} t.k = s print(t.k)",
]


@pytest.mark.parametrize("src", KNOWN_RESIDUAL, ids=range(len(KNOWN_RESIDUAL)))
def test_known_residual_shapes_still_do_not_certify(src):
    """Recorded, not asserted away: if one of these starts certifying, this
    test fails and the shape should move up into TEMP_CASES/LOCAL_CASES with
    its cause struck from the list above.
    """
    _, cert = _certifies(src)
    assert cert.level == "L1", (src, "now certifies -- promote it")

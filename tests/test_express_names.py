import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return lift_proto(load_file(o))


def test_reassigned_register_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    # 'a' is written twice (a=1; a=a+1) → its register is a local, not a temp
    fn = _fn("local a = 1 a = a + 1 print(a)", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps


def test_call_arg_staging_is_temp(tmp_path):
    """'local x = string.format(\"%d\", 42)': the two LOADK-staged CALL
    arguments (the format string, the number) are each single-def with a
    single adjacent use (the CALL itself) and nothing in between writes their
    inputs -> both inline as temps.

    Deliberately not `print(string.format(...))`: there, string.format's own
    CALL has C==0 (its results feed print's open argument list), so its
    result write clobbers the very registers that staged its arguments --
    correctly making them NOT single-def, hence local. See
    test_open_region_write_between_def_and_use_forces_local for that
    mechanism in isolation.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("local x = string.format('%d', 42)", tmp_path)
    rc = classify_registers(fn)
    assert {1, 2} <= rc.temps             # the '%d' register and the 42 register


def test_parameter_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    fn = _fn("local function f(x, y) return x + y end return f", tmp_path)
    inner = fn.proto.subprotos[0]
    from pyluadec.lift import lift_proto
    rc = classify_registers(lift_proto(inner))
    assert 0 in rc.locals and 1 in rc.locals     # both params are locals


def test_captured_register_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import lift_proto
    root = _fn("local n = 0 local f = function() return n end return f()", tmp_path)
    rc = classify_registers(root)
    # n's register is captured by the closure → local
    assert root.captured_regs
    assert root.captured_regs <= rc.locals


def test_name_for_is_valid_identifier():
    from pyluadec.express.names import name_for
    from pyluadec.lift import LUA_KEYWORDS
    n = name_for(3, depth=1)
    assert n.isidentifier() and n not in LUA_KEYWORDS and not n.startswith("__pld_")
    assert name_for(3, 1) != name_for(3, 2)      # depth disambiguates across protos


def test_multiply_written_dead_write_is_still_local(tmp_path):
    """Isolates the def-count rule from the use-count rule.

    'local a = 1 a = 2 local b = a': the first write to a's register is dead
    (overwritten before any read), so there is exactly one *use* (the final
    read feeding b) with nothing writing that use's inputs in between -- the
    def/use pair alone would look "adjacent pure" and inline as a temp. Only
    the def-count check (2 writes) forces it local. This is a case
    test_reassigned_register_is_local does not actually isolate: that test's
    register also fails the use-count check (its 'a' is read twice: once by
    the ADD that recomputes it, once by print), so it would still classify as
    local even if the def-count check were deleted.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("local a = 1 a = 2 local b = a", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps


def test_numeric_for_control_slots_are_temp_and_loop_var_is_local(tmp_path):
    """'for i=1,3 do print(i) end': FORPREP/FORLOOP control slots R(A..A+2)
    must be temps (they're consumed by the for-header, not real locals) and
    the visible loop variable R(A+3) must be local and recorded in loop_vars.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("for i=1,3 do print(i) end", tmp_path)
    rc = classify_registers(fn)
    assert {0, 1, 2} <= rc.temps
    assert 3 in rc.locals and 3 in rc.loop_vars
    assert not ({0, 1, 2} & rc.locals)


def test_generic_for_control_slots_are_temp_and_loop_vars_are_local(tmp_path):
    """'for k,v in pairs(t) do end': TFORLOOP control slots R(A..A+2) must be
    temps and the visible loop variables R(A+3..A+2+C) must be local and
    recorded in loop_vars.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("local t = {} for k, v in pairs(t) do print(k, v) end", tmp_path)
    rc = classify_registers(fn)
    assert {1, 2, 3} <= rc.temps
    assert {4, 5} <= rc.locals
    assert {4, 5} <= rc.loop_vars
    assert not ({1, 2, 3} & rc.locals)


def test_value_not_consumed_before_a_loop_header_is_local():
    """A value that is still live when a `for` header runs is a local.

    Historically this test isolated `_adjacent_pure`'s may_error term
    (FORPREP/FORLOOP being the only opcodes that are PURE at every EffectMode
    yet may_error=True). `_adjacent_pure` is gone as of M3 task 8 and the
    freereg simulation that replaced it reaches the same verdict for a
    stronger reason: FORPREP is a statement boundary, so anything still
    pending when it executes is promoted to local by definition. Register 5
    is written at pc 1 and only read at pc 3, on the far side of the header,
    so it survives a statement boundary -> local. (Real luac never stages a
    temp across a for header; this is a tests/synth.py shape.)
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    def_ri = mk_instr(Op.LOADK, a=5, bx=0, pc=1)
    def_fx = InstrEffects(reads=frozenset(), writes=frozenset({5}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    forprep_ri = mk_instr(Op.FORPREP, a=10, sbx=1, pc=2)
    forprep_fx = InstrEffects(reads=frozenset({10, 11, 12}), writes=frozenset({10, 11, 12}),
                               reads_open=False, writes_open=False,
                               effect=Effect.PURE, may_error=True)
    use_ri = mk_instr(Op.MOVE, a=6, b=5, pc=3)
    use_fx = InstrEffects(reads=frozenset({5}), writes=frozenset({6}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    instrs = {
        1: LirInstr(ri=def_ri, effects=def_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=forprep_ri, effects=forprep_fx, successors=(3,), consumed=()),
        3: LirInstr(ri=use_ri, effects=use_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0, 0, 0), numparams=0, maxstacksize=16)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=3,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(fn)
    assert 5 in rc.locals and 5 not in rc.temps


def test_open_region_write_between_def_and_use_forces_local():
    """A VARARG B==0 (open write, R[A..top) unbounded) between a def and its
    use must force local, never temp. Under the freereg simulation that
    replaced `_adjacent_pure` in M3 task 8 this still holds, by a different
    route: the open producer pushes at register 0, which pops everything at
    or above it -- register 7 among them -- and register 7 had not been read
    at that point, so it is disqualified.

    Open regions are not statically bounded, so they never appear in a real
    instruction's .writes/.reads -- an instruction with writes_open=True can
    silently clobber any register it might reach. Real luac never places one
    between a temp candidate's def and use (see
    test_corpus_no_open_region_in_pre_fix_temp_window for the empirical
    corpus check), so this is a hand-built shape via tests/synth.py, exactly
    the kind of "IR luac never would produce" this module must still not
    silently mishandle. Register 7 has one def, one use, and nothing writes
    its (empty) input set in between -- only the open-region guard keeps it
    out of temps.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    def_ri = mk_instr(Op.LOADK, a=7, bx=0, pc=1)
    def_fx = InstrEffects(reads=frozenset(), writes=frozenset({7}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    vararg_ri = mk_instr(Op.VARARG, a=0, b=0, pc=2)
    vararg_fx = InstrEffects(reads=frozenset(), writes=frozenset(),
                              reads_open=False, writes_open=True,
                              effect=Effect.PURE, may_error=False)
    use_ri = mk_instr(Op.MOVE, a=8, b=7, pc=3)
    use_fx = InstrEffects(reads=frozenset({7}), writes=frozenset({8}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    instrs = {
        1: LirInstr(ri=def_ri, effects=def_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=vararg_ri, effects=vararg_fx, successors=(3,), consumed=()),
        3: LirInstr(ri=use_ri, effects=use_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0, 0, 0), numparams=0, maxstacksize=10)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=3,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(fn)
    assert 7 in rc.locals and 7 not in rc.temps


def test_open_region_check_ignores_which_registers_it_touches():
    """A value pushed below an open region and never consumed inside its own
    statement is a local.

    This test used to pin `_adjacent_pure`'s open-region check as
    unconditional (blocking on ANY reads_open/writes_open in the window
    regardless of which registers it touched). That barrier is gone as of M3
    task 8. The freereg simulation reaches the same verdict here for a reason
    that does not depend on the open region at all: register 2 is written at
    pc 1, read at pc 3 by a MOVE that pushes at register 9, and the function
    then ends -- so register 2 is still pending at the end and is promoted to
    local. Kept as a standing shape-robustness pin (tests/synth.py builds an
    instruction order luac would not emit; the classifier must still give a
    printable answer rather than crash or silently inline).
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    def_ri = mk_instr(Op.LOADK, a=2, bx=0, pc=1)
    def_fx = InstrEffects(reads=frozenset(), writes=frozenset({2}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    vararg_ri = mk_instr(Op.VARARG, a=5, b=0, pc=2)          # base 5, doesn't touch reg 2
    vararg_fx = InstrEffects(reads=frozenset(), writes=frozenset(),
                              reads_open=False, writes_open=True,
                              effect=Effect.PURE, may_error=False)
    use_ri = mk_instr(Op.MOVE, a=9, b=2, pc=3)
    use_fx = InstrEffects(reads=frozenset({2}), writes=frozenset({9}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    instrs = {
        1: LirInstr(ri=def_ri, effects=def_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=vararg_ri, effects=vararg_fx, successors=(3,), consumed=()),
        3: LirInstr(ri=use_ri, effects=use_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0, 0, 0), numparams=0, maxstacksize=10)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=3,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(fn)
    assert 2 in rc.locals and 2 not in rc.temps


def test_open_call_argument_staging_stays_temp(tmp_path):
    """Registers staged as the fixed arguments of a call whose results feed an
    OPEN argument list are temps, and the whole chunk certifies L3.

    Supersedes `test_open_write_at_use_pc_forces_local` (M3 task 8), which
    asserted the opposite -- that registers 2 and 3 here are LOCALS. That
    assertion pinned a limitation of the old `_adjacent_pure` def/use barrier,
    not a fact about the bytecode: `print(string.format("%d", 42))` stages
    "%d" and 42 into registers 2 and 3, string.format's own `CALL ... C==0`
    consumes them and leaves its results open at register 1, and print's
    `CALL ... B==0` consumes that. Every one of those values lives and dies
    inside one statement, so all four registers are luac temporaries; calling
    two of them `local` forced the printer to emit `local` declarations luac
    never compiled, costing stack slots and a certification.

    The `assert certify_proto(...).level == "L3"` below is what makes this a
    fact rather than a preference: `luac` itself confirms that the printed
    source recompiles to this exact proto.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.structure.structured import certify_proto
    fn = _fn("print(string.format('%d', 42))", tmp_path)
    rc = classify_registers(fn)
    assert {0, 1, 2, 3} <= rc.temps
    assert not rc.locals
    assert certify_proto(fn.proto, is_chunk_root=True).level == "L3"


def test_open_region_in_an_earlier_statement_does_not_poison_a_later_one(tmp_path):
    """An open-region instruction in one statement must not disqualify the
    temps of a *later* statement.

    Round-2 of this module fixed a version of classify_registers that poisoned
    its bookkeeping globally for every open-region instruction in the
    function, flipping 154 of 342 registers temp->local corpus-wide for no
    soundness gain. That regression is still worth a standing pin, but the
    old test built the shape by hand out of `tests/synth.py` instructions in
    an order luac never emits (a value pushed at register 9 and then a fresh
    value pushed at register 2 while 9 was still live -- freereg only ever
    moves down by *consuming* the values above it). The freereg simulation
    that replaced the def/use barrier in M3 task 8 reads that as "register 9
    was silently dropped" and classifies it local, which is the correct
    reading of that instruction sequence.

    So the property is re-pinned on real luac output instead: statement one
    is an open call (`print(string.format(...))`, whose inner CALL has C==0),
    statement two stages two ordinary constant arguments. The second
    statement's staging registers must still be temps, and the chunk must
    certify.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.structure.structured import certify_proto
    fn = _fn("print(string.format('%d', 42)) print('a', 'b')", tmp_path)
    rc = classify_registers(fn)
    assert {0, 1, 2, 3} <= rc.temps
    assert not rc.locals
    assert certify_proto(fn.proto, is_chunk_root=True).level == "L3"


def test_local_released_by_scope_exit_is_not_inlined_as_a_temp(tmp_path):
    """Pins the CALL/TAILCALL statement boundary's `promote_all()`.

    `do local a = f() g(a) end h()` declares a genuine local that is read
    exactly once, and whose slot is then handed to the *next* statement --
    not by a redefinition of `a`, but by SCOPE EXIT: `end` drops `a` from
    `nactvar`, so `GETGLOBAL h` reuses register 0. luac emits no `CLOSE`
    for that release (it emits `CLOSE` only when the block captured an
    upvalue), and no other boundary in the simulation sees it either.

    So the only thing that stops register 0 from looking like a pop-once
    temp is the `promote_all()` at the CALL-statement boundary (`g(a)`,
    C==1), which empties the expression stack before the reuse. Neuter that
    one line and register 0 flips local -> temp, which would inline it as
    `g(f())` and hoist `GETGLOBAL g` in front of the call to `f` -- an
    observable reordering under STRICT metamethod semantics.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("do local a = f() g(a) end h()", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals, "scope-exit-released local inlined as a temp"
    assert 0 not in rc.temps


def test_corpus_no_open_region_in_pre_fix_temp_window(lifted_corpus):
    """Empirical invariant, not a correctness proof: across the full 229-file
    corpus, no register that the *pre-open-region-fix* classify_registers
    would have called temp (single explicit def, single explicit use,
    def-pc < use-pc, nothing writes the def's inputs in between, and nothing
    in between is WRITE_HEAP-effect or may_error) additionally has an
    open-region instruction (reads_open/writes_open) strictly between its
    def and use.

    Deliberately reimplements the *old* (pre-fix) _adjacent_pure barrier
    locally rather than importing it from names.py -- names.py no longer has
    that exact function post-fix, and the point of this test is to check
    what the *previous* code's temp set looks like against open regions, not
    to exercise the current implementation (that's
    test_open_region_write_between_def_and_use_forces_local's job). A looser
    version of this check -- flagging every single-def/single-use window
    regardless of whether it would have passed the other barriers -- finds
    thousands of hits, almost all from `return f(...)`-shaped open RETURNs
    sitting between two pcs that are otherwise unrelated to each other in
    linear instruction order (RETURN is PURE/may_error=False at every mode,
    so it does not itself trip the old WRITE_HEAP/may_error barrier); that is
    not the claim being pinned here.

    If this ever fails, it means a real corpus function's *old-style*
    temp-eligible register now depends on the open-region guard for
    correctness, which is worth knowing on its own.

    Round-1 fold-in (2026-08-12): shares `conftest.py`'s session-scoped
    `lifted_corpus` fixture instead of its own `load_file`+`lift_proto`
    walk. The `try/except Exception` around the old walk's own `lift_proto`
    call is dropped along with it: `lifted_corpus` calls `lift_proto`
    unconditionally and is consumed by several other corpus tests
    (`test_corpus_every_temp_write_has_exactly_one_consumer` below among
    them) with no failure ever observed across all 1944 proto occurrences,
    so the `except` was defensive dead code, not a load-bearing skip.
    """
    from pyluadec.lift import Effect

    def old_adjacent_pure(fn, dp, up, ordered) -> bool:
        dli = fn.instrs[dp]
        inputs = set(dli.effects.reads)
        for pc in ordered:
            if not (dp < pc < up):
                continue
            li = fn.instrs[pc]
            if li.effects.writes & inputs:
                return False
            if li.effects.effect >= Effect.WRITE_HEAP or li.effects.may_error:
                return False
        return True

    hits = []

    for _fname, _path, proto, fn in lifted_corpus:
        defs: dict[int, list[int]] = {}
        uses: dict[int, list[int]] = {}
        ordered = sorted(fn.instrs)
        for pc in ordered:
            li = fn.instrs[pc]
            for r in li.effects.writes:
                defs.setdefault(r, []).append(pc)
            for r in li.effects.reads:
                uses.setdefault(r, []).append(pc)
        for r in sorted(set(defs) & set(uses)):
            d, u = defs[r], uses[r]
            if len(d) != 1 or len(u) != 1:
                continue
            dp, up = d[0], u[0]
            if dp >= up or not old_adjacent_pure(fn, dp, up, ordered):
                continue
            for pc in ordered:
                if dp < pc < up:
                    oe = fn.instrs[pc].effects
                    if oe.reads_open or oe.writes_open:
                        hits.append((proto.source, r, dp, up, pc))

    assert hits == [], f"open-region instruction inside a pre-fix temp window: {hits[:5]}"


def test_classification_does_not_consult_the_effect_table(tmp_path):
    """A value produced by an effectful, may_error instruction is still a temp
    when it is consumed inside its own statement.

    Supersedes `test_adjacent_pure_window_excludes_the_def_pc_itself` (M3 task
    8), which pinned the bottom edge of `_adjacent_pure`'s `(dp, up]` scan
    window -- a function that no longer exists. Its underlying claim was that
    the *risk* of an instruction (can it raise, can it touch the heap) has
    nothing to do with whether its result is inlinable, and that claim is now
    structural: `_stack_discipline` never looks at `InstrEffects.effect` or
    `.may_error` at all, only at which registers are read and written.

    `print(t.field)` is the smallest real shape that would have been blocked
    by the old barrier for effect reasons alone: under EffectMode.STRICT both
    the `GETGLOBAL t` and the `GETTABLE` are ARBITRARY, and GETTABLE is
    may_error as well. Both results are consumed before the statement ends,
    so both are temps -- confirmed by luac via certification.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.structure.structured import certify_proto
    fn = _fn("print(t.field)", tmp_path)
    rc = classify_registers(fn)
    assert {0, 1} <= rc.temps
    assert not rc.locals
    assert certify_proto(fn.proto, is_chunk_root=True).level == "L3"


def test_controls_register_reused_as_ordinary_local_classifies_local(tmp_path):
    """M3 task-5 round-2 review pin: a register that is a for-loop's control
    slot in one range of the function, and an ordinary, multiply-written/
    read local everywhere else, must classify LOCAL -- not temp.

    `controls` (accumulated over every FORPREP/FORLOOP/TFORLOOP in the
    function, purely by register number) used to force such a register temp
    unconditionally, with no check for reuse outside its role as a control
    slot. Measured on the 229-file corpus: 188 (proto, register) pairs were
    ever forced temp this way; 105 of them (register 0 in snr_common.lua's
    main chunk among them -- the coordinator's cited example) had real,
    unrelated reuse elsewhere in the function that the naive override
    ignored entirely.

    'for i = 1, 3 do end local x = 1 x = x + 1 x = x + 1' reproduces this
    directly with real luac output: register 0 is the for-loop's init/'a'
    control slot (FORPREP/FORLOOP both write and read it), and after the
    loop ends luac reuses register 0 for the entirely unrelated local `x`,
    written three more times and read twice more. Fails against the pre-fix
    `controls`-only override (register 0 would be forced temp, and
    reconstruct.py would then try to pop-once-inline a value that's actually
    reassigned and read multiple times).

    Deliberately call-free (round-4 review: the fixture used to be
    'for i = 1, 3 do print(i) end local x = 1 ... print(x)'). A CALL with no
    results has empty `writes`, which under the round-3 backward scan acted
    as an accidental terminator for the staging window -- so a fixture with
    an incidentally-placed call can pass without the property under test
    actually holding. Every fixture in this family is now call-free so it
    proves its claim on its own shape.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("for i = 1, 3 do end local x = 1 x = x + 1 x = x + 1", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps
    # the loop's own control machinery is otherwise unaffected by register
    # 0's demotion: the limit/step slots stay temp and the loop variable is
    # still local and recorded as such.
    assert {1, 2} <= rc.temps
    assert 3 in rc.locals and 3 in rc.loop_vars


def test_register_reused_between_two_loops_sharing_it_as_control_base_classifies_local(tmp_path):
    """M3 task-5 round-3 review pin: `_staging_window_ok` (round 2) checked
    *membership* -- does this pc fall in some gap before some loop that
    claims r -- but not *chain coherence*: do ALL of r's defs/uses belong to
    exactly one loop's own control lifetime. When the same register is the
    control base for TWO loops, ordinary code living in the gap BETWEEN
    them (not staging for either) gets swept into "the gap before the
    second loop" and misclassified temp.

    'for i=1,3 do end do local x=1 x=x+1 x=x+1 end for j=1,5 do end':
    register 0 is loop 1's control base, then `x` once that scope frees it,
    then loop 2's control base again. Removing the second `for` loop makes
    register 0 correctly classify local under round 2's code too -- it is
    specifically the *later* claim that used to provide cover for x's
    activity to hide in the gap.

    Round-4 review: this fixture used to carry a trailing `print(x)` inside
    the `do ... end` block and `print` calls in both loop bodies, and it
    passed against round 3's own backward scan *because of them* -- a
    zero-result CALL has empty `writes`, which terminated that scan's run of
    "instructions writing into the control triple" and so happened to keep
    x's writes out of the window. Strip the calls and round 3 classifies
    register 0 temp, silently deleting all three of x's statements from the
    reconstructed output. The fixture is now call-free so nothing incidental
    stands in for the property.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn(
        "for i=1,3 do end "
        "do local x = 1  x = x + 1  x = x + 1 end "
        "for j=1,5 do end",
        tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps


def test_two_loops_legitimately_sharing_a_control_base_both_stay_temp(tmp_path):
    """The other direction of the round-3 fix, pinned separately so the
    chain-coherence check can't be satisfied by simply always demoting a
    register claimed by more than one loop: 'for i=1,3 do end for j=1,5 do
    end' -- two numeric-for loops immediately adjacent, genuinely sharing
    registers 0/1/2 as their control base with NO unrelated activity in the
    gap between them -- must still classify all three temp.

    Call-free for the same reason as its sibling above (round-4 review): the
    fixture must not lean on a `print` in either loop body.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("for i=1,3 do end for j=1,5 do end", tmp_path)
    rc = classify_registers(fn)
    assert {0, 1, 2} <= rc.temps
    assert not ({0, 1, 2} & rc.locals)


def test_local_dropped_before_a_for_loop_reusing_its_register_is_local(tmp_path):
    """M3 task-5 round-4 review pin (case A), the commonest shape of all:

        do local x = 5 end
        for i = 1, 3 do print(i) end

    `x` goes out of scope, so luac hands register 0 straight to the loop's
    init slot. Register 0 therefore has two writes -- x's `LOADK 5` and the
    loop's own `LOADK 1` -- and only the second one is staging for the loop.

    Round 3 classified register 0 temp here: it walked backward from FORPREP
    over every *consecutive* instruction whose writes intersect {0,1,2},
    which runs straight through the loop's three staging LOADKs and into
    x's, because that one also writes register 0. Register 0 being temp
    means `local x = 5` is inlined into the for-header and its statement
    vanishes from the output with no error raised.

    The producer-chain slice asks which instruction produced the value the
    header reads instead, so it stops at the loop's own `LOADK 1` and never
    reaches x's write.

    What makes this fixture prove that rather than an accident: nothing at
    all stands between x's write and the loop's staging, and the only call
    in the function (`print(i)`) is inside the loop body, textually *after*
    FORPREP -- downstream of where any backward run from the header starts,
    so it cannot terminate one. The round-3 scan only ever stopped at an
    instruction whose `writes` missed the triple, in practice a zero-result
    CALL; there is none available here. Verified directly: deleting
    `print(i)` leaves both this test's verdict and round 3's unchanged.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("do local x = 5 end for i = 1, 3 do print(i) end", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps
    # the loop's limit/step slots have no such double duty and stay temp --
    # the fix must not demote the whole triple indiscriminately.
    assert {1, 2} <= rc.temps
    assert 3 in rc.locals and 3 in rc.loop_vars


def test_mutated_local_before_two_loops_reusing_its_register_is_local(tmp_path):
    """M3 task-5 round-4 review pin (case C):

        do local z = 1  z = z + 1  z = z + 1 end
        for i = 1, 3 do end
        for j = 1, 5 do print(j) end

    Register 0 is `z` (three writes, two reads), then the control base of
    two consecutive loops. Round 3 classified it temp: its backward run from
    either FORPREP passes over both loops' staging, the first loop's own
    FORPREP/FORLOOP and all three of z's writes without ever meeting an
    instruction whose `writes` miss {0,1,2}, so it ran to pc 0 and swallowed
    every one of z's statements, which then disappeared from the
    reconstructed output.

    There is no call anywhere *before* the loops -- the only one,
    `print(j)`, is inside the second loop's body, after both FORPREPs, so it
    is downstream of where either backward run starts and cannot terminate
    one. Verified directly: deleting it leaves both this test's verdict and
    round 3's unchanged.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("do local z = 1  z = z + 1  z = z + 1 end "
             "for i = 1, 3 do end "
             "for j = 1, 5 do print(j) end", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps
    assert {1, 2} <= rc.temps


def test_multi_instruction_generic_for_iterator_staging_stays_temp(tmp_path):
    """The other direction for a multi-instruction staging chain, which a
    fix that only accepted single-instruction staging would break.

    'local t = {} for k, v in string.gmatch(t, t) do end' stages the
    iterator triple with GETGLOBAL -> GETTABLE -> MOVE -> MOVE -> CALL, five
    instructions, three of which write register 1 (the iterator slot) in
    succession. All of {1, 2, 3} must stay temp: every write and read of
    them belongs to the chain that produces what TFORLOOP reads.

    Corpus relationship, stated precisely (round-5 review corrected an
    earlier overclaim here): the corpus has 7 TFORLOOPs, whose stagings are
    GETGLOBAL/GETUPVAL/GETTABLE/CALL (4), GETGLOBAL/GETGLOBAL/GETTABLE/CALL
    (1), GETGLOBAL/GETGLOBAL/CALL (1) and GETGLOBAL/MOVE/CALL (1). So five
    of them do contain a GETTABLE, but in every one it rewrites the *state*
    slot (a+1), not the base -- no corpus GETTABLE writes the iterator base.
    This fixture is the harder shape on purpose (the GETTABLE rewrites the
    base, so the chain has to follow a producer's own read of a register it
    also writes); it is not a transcription of a corpus instance.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("local t = {} for k, v in string.gmatch(t, t) do end", tmp_path)
    rc = classify_registers(fn)
    assert {1, 2, 3} <= rc.temps
    assert not ({1, 2, 3} & rc.locals)
    assert {4, 5} <= rc.loop_vars


def test_numeric_for_limit_computed_by_a_call_stays_temp(tmp_path):
    """Numeric-for staging is not always three LOADKs: 'for i = 1,
    tonumber(x) do end' stages the limit with GETGLOBAL/MOVE/CALL, and the
    CALL reads the step slot (as its own argument register) before the step
    LOADK writes it. The chain has to follow that read back rather than
    treat the slot as already resolved, or the triple gets demoted.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("local x = 1 for i = 1, tonumber(x) do end", tmp_path)
    rc = classify_registers(fn)
    assert {1, 2, 3} <= rc.temps
    assert 0 in rc.locals            # x itself, read by the staging MOVE
    assert 4 in rc.loop_vars


def test_control_lifetime_proof_does_not_scan_the_whole_preceding_function(tmp_path):
    """The staging proof must be bounded by the length of the staging chain,
    not by how much code precedes the loop.

    A 400-statement call-free prefix that repeatedly rewrites register 0,
    followed by two loops using register 0 as their control base: round 3
    walked back through every one of those writes for every loop occurrence
    (its run only ever stopped at an instruction whose writes missed the
    triple, and there is none here), which is both wrong -- register 0 is
    plainly double duty -- and quadratic. Asserting the verdict rather than
    a wall-clock number; the 60s pytest timeout is the backstop for the
    cost.
    """
    from pyluadec.express.names import classify_registers
    prefix = " ".join("z = z + 1" for _ in range(400))
    fn = _fn(f"do local z = 0 {prefix} end for i = 1, 3 do end for j = 1, 5 do end",
             tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps
    assert {1, 2} <= rc.temps


def test_regclass_does_not_classify_registers_with_no_tracked_def_or_use():
    """RegClass only covers registers classify_registers actually saw a def
    or use for. A register that's neither written nor read (dead stack
    space, e.g. maxstacksize padding) appears in none of locals/temps/
    loop_vars -- it is untracked, not implicitly "temp" or "local".
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    ri = mk_instr(Op.LOADK, a=0, bx=0, pc=1)
    fx = InstrEffects(reads=frozenset(), writes=frozenset({0}),
                       reads_open=False, writes_open=False,
                       effect=Effect.PURE, may_error=False)
    instrs = {1: LirInstr(ri=ri, effects=fx, successors=(), consumed=())}
    proto = mk_proto((0,), numparams=0, maxstacksize=5)   # regs 0..4 exist; only 0 is touched
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=1,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(fn)
    for r in (1, 2, 3, 4):
        assert r not in rc.locals and r not in rc.temps and r not in rc.loop_vars


def _temp_write_violations(fn, rc):
    """Per-*write* soundness oracle for RegClass.temps. Classification only:
    no SIR walk, no Reconstructor, so it is an invariant of
    classify_registers itself, not of any consumer.

    A temp register is reconstructed by staging its defining expression and
    splicing it into its single consumer, popping it on the way. That is
    sound for one value of one register exactly when the value has EXACTLY
    ONE reader before it is overwritten:

      - zero readers  -> nothing ever splices it in, so the statement that
                         produced it vanishes from the output entirely, with
                         no error raised. This is the failure mode that
                         rounds 1-3 shipped three times.
      - two or more   -> the first read pops it and the second finds nothing
                         staged (a ReconstructError at best, a wrong tree at
                         worst).

    So: for every r in rc.temps, every write of r that is not the loop
    header's own FORPREP/FORLOOP/TFORLOOP must have exactly one read of r in
    `(write_pc, next_write_pc]`.

    The window is open at the bottom and CLOSED AT THE TOP on purpose. An
    instruction that reads a register and also writes it -- `ADD r, r, k`,
    or FORPREP/FORLOOP reading their control triple before rewriting it --
    consumes the old value, so its read belongs to the previous write's
    window. Excluding it reports false violations on every genuine for-loop
    control slot in existence (the same half-open-window subtlety as
    _adjacent_pure's `(dp, up]`).

    Returns a list of (register, write_pc, reader_count) for each violation.
    """
    from pyluadec.lift.opcodes import Op

    control = (Op.FORPREP, Op.FORLOOP, Op.TFORLOOP)
    writes: dict[int, list[int]] = {}
    reads: dict[int, list[int]] = {}
    # `R[base..top)` regions do not appear in .reads/.writes at all -- their
    # top is a dynamic stack depth. Counting only explicit reads/writes makes
    # this oracle report a false verdict for every register staged into an
    # open call: `f(a, b, c, g(h))` stages a/b/c into registers that ONLY the
    # open `CALL f ... B==0` reads (false "zero readers"), and the inner
    # `CALL g ... C==0` then re-defines those same slots with its results
    # (which, unmodelled, made the outer read look like a second reader of
    # the *staging* write -- false "two readers"). Both directions occur in
    # the corpus (M3 task 8: 464 and 874 protos respectively).
    open_reads: list[tuple[int, int]] = []       # (pc, lowest register read)
    open_writes: list[tuple[int, int]] = []      # (pc, lowest register written)
    for pc in sorted(fn.instrs):
        li = fn.instrs[pc]
        for r in li.effects.writes:
            writes.setdefault(r, []).append(pc)
        for r in li.effects.reads:
            reads.setdefault(r, []).append(pc)
        if li.effects.reads_open:
            open_reads.append((pc, li.ri.a if li.ri.op is Op.RETURN else li.ri.a + 1))
        if li.effects.writes_open:
            # `or li.ri.op is Op.TAILCALL` used to be spelled out here: when
            # its callee is not a Lua function, OP_TAILCALL leaves the results
            # at R[a..top) and the RETURN luac always emits directly after it
            # returns exactly that open range -- so `return f(a, b, c, "k")`
            # has TAILCALL read a..a+4 explicitly and then RETURN read the
            # same slots open, which without the extra term looks like a
            # second consumer of the *staging* writes. It was modelled in this
            # oracle rather than in the effect table because the table is the
            # axiom layer and changing it needs an lvm.c citation plus a full
            # differential run (CLAUDE.md).
            #
            # M4 task 8 did exactly that (lvm.c:630-632; the differential over
            # all 1944 protos moved nothing -- see tests/test_effects_tailcall.py),
            # so `analyze()` now returns writes_open=True for EVERY TAILCALL
            # operand form, unconditionally. The special case is therefore
            # exactly redundant, not merely usually redundant:
            # test_effects_tailcall.py::
            # test_tailcall_declares_an_open_write_region_for_every_operand_form
            # is the standing proof of the equivalence.
            open_writes.append((pc, li.ri.a))

    bad = []
    for r in sorted(rc.temps):
        ws = sorted(set(writes.get(r, []))
                    | {pc for pc, base in open_writes if r >= base})
        rs = sorted(set(reads.get(r, []))
                    | {pc for pc, base in open_reads if r >= base})
        for i, pc in enumerate(ws):
            if fn.instrs[pc].ri.op in control:
                continue
            nxt = ws[i + 1] if i + 1 < len(ws) else None
            n = sum(1 for u in rs if u > pc and (nxt is None or u <= nxt))
            if n != 1:
                bad.append((r, pc, n))
    return bad


def test_corpus_every_temp_write_has_exactly_one_consumer(lifted_corpus):
    """Standing corpus gate for RegClass.temps (M3 task-5 round-5 review).

    Runs _temp_write_violations over every proto of all 229 corpus files.
    This is the instrument that would have caught rounds 1, 2 and 3
    immediately -- each of them classified registers temp whose writes had
    zero readers, which deletes statements silently. Costs well under a
    second corpus-wide.

    Note what this gate does and does not prove. It is sound in the
    direction that matters (a temp that fails it WILL lose or duplicate
    something), but the corpus itself is nearly inert for the control-slot
    rule: this corpus is dense with calls, which is exactly what let round
    3's backward scan terminate in the right place by accident, so round 3
    also scores zero here. The teeth are demonstrated by the injection test
    below and by the case-A/case-C tests above; this gate is the standing
    guard against the next regression, not the evidence for the last one.

    Round-1 fold-in (2026-08-12): shares `conftest.py`'s session-scoped
    `lifted_corpus` fixture instead of its own `load_file`+`lift_proto`
    walk (this file used to pay for that walk twice -- see the sibling
    test above).
    """
    from pyluadec.express.names import classify_registers

    hits = []
    n = 0

    for fname, path, _proto, fn in lifted_corpus:
        n += 1
        bad = _temp_write_violations(fn, classify_registers(fn))
        if bad:
            hits.append(((fname,) + path, bad))

    assert n > 1900, f"corpus looks truncated: only {n} protos"
    assert hits == [], f"temp register whose write has != 1 consumer: {hits[:5]}"


def test_temp_write_oracle_fires_on_an_injected_misclassification(tmp_path):
    """The gate above has teeth: inject the exact mistake rounds 1-3 made
    and confirm it is reported.

    `do local x = 5 end for i = 1, 3 do print(i) end` -- register 0 is `x`
    and then the loop's init slot. classify_registers correctly calls it
    local; forcing it into `temps` (which is literally what round 3's
    `controls` override did) gives its first write, `LOADK 5`, zero readers
    before the loop's own `LOADK 1` overwrites it, so the oracle reports
    (register 0, that pc, 0 readers).

    Also asserts the un-injected classification is clean, so the test cannot
    pass by the oracle simply flagging everything.
    """
    from pyluadec.express.names import RegClass, classify_registers

    fn = _fn("do local x = 5 end for i = 1, 3 do print(i) end", tmp_path)
    rc = classify_registers(fn)
    assert _temp_write_violations(fn, rc) == []

    injected = RegClass(locals=rc.locals - {0}, temps=rc.temps | {0},
                        loop_vars=rc.loop_vars)
    bad = _temp_write_violations(fn, injected)
    assert [(r, n) for r, _pc, n in bad] == [(0, 0)], bad


def test_parameters_and_captured_registers_win_over_the_controls_override():
    """The `controls` branch runs after -- not before -- the parameter and
    captured-register guards (M3 task-5 round-5 review).

    Both guards exist to be unconditional: a parameter and an
    upvalue-captured register are named, live locals whose slot the loop
    header must never be allowed to claim as an inlinable staging temp.
    Ordered the other way, `controls` reached them first and a for-loop
    based at register 0 of a 3-parameter function classified all three
    declared parameters temp.

    luac never emits this (a live parameter's slot is not reused as a loop
    header's base), so it is hand-built -- but the module refuses cleanly on
    every other malformed shape it can see, and an unconditional temp
    override sitting in front of two unconditional guards is exactly the
    kind of ordering the rest of this file has already been bitten by.
    Corpus-neutral: 0 of 1944 protos change classification.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    pure = dict(reads_open=False, writes_open=False, effect=Effect.PURE,
                may_error=True)
    prep = mk_instr(Op.FORPREP, a=0, sbx=0, pc=1)
    loop = mk_instr(Op.FORLOOP, a=0, sbx=-1, pc=2)
    triple = frozenset({0, 1, 2})
    instrs = {
        1: LirInstr(ri=prep, effects=InstrEffects(reads=triple, writes=triple, **pure),
                    successors=(2,), consumed=()),
        2: LirInstr(ri=loop, effects=InstrEffects(reads=triple,
                                                  writes=frozenset({0, 3}), **pure),
                    successors=(2, 3), consumed=()),
    }
    proto = mk_proto((0, 0), numparams=3, maxstacksize=8)

    params = LirFunction(proto=proto, instrs=instrs, n_pcs=2,
                         captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(params)
    assert {0, 1, 2} <= rc.locals, "declared parameters classified temp"
    assert not ({0, 1, 2} & rc.temps)

    # Same shape with no parameters, but register 1 captured by a closure.
    proto0 = mk_proto((0, 0), numparams=0, maxstacksize=8)
    captured = LirFunction(proto=proto0, instrs=instrs, n_pcs=2,
                           captured_regs=frozenset({1}), closure_pseudo={})
    rc = classify_registers(captured)
    assert 1 in rc.locals and 1 not in rc.temps
    # the un-captured, non-parameter slots of the same triple are unaffected
    assert {0, 2} <= rc.temps

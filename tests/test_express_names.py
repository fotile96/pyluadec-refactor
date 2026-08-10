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


def test_adjacent_pure_blocks_inlining_across_may_error_pure_instruction():
    """_adjacent_pure's may_error term, isolated from its effect-level term.

    FORPREP/FORLOOP are the only opcodes that are PURE at every EffectMode
    yet may_error=True (see lift/effects.py's FORLOOP comment) -- so they are
    the only way to build a def/use pair whose intervening instruction is
    blocked *solely* by the may_error check, never by the effect>=WRITE_HEAP
    check. This hand-built shape (real luac never stages a temp's def and use
    across a for-loop header) isolates exactly that: register 5 has one def,
    one use, and nothing writes its (empty) input set in between -- only
    may_error keeps it out of temps.
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
    use must force local, never temp.

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
    """_adjacent_pure's open-region check is unconditional: it blocks on ANY
    reads_open/writes_open instruction in (dp, up], regardless of whether
    that instruction's own base register happens to overlap the candidate.

    Register 2's def/use window (pc 1..3) contains a VARARG B==0 at pc 2 with
    base register 5 -- register 2 is nowhere near that range. This pins the
    deliberate design choice of NOT trying to compute the open region's
    actual affected range (base is known, but "top" is a dynamic stack depth
    this module does not simulate, so no such range could be proven safe to
    exclude) -- see the M3 task-4 round-2 review, which flagged and removed
    an earlier version that tried to track per-register open ranges globally
    (unwindowed, which was itself the round-2 defect) rather than treating
    "is there any open region in my own window at all" as the question.
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


def test_open_write_at_use_pc_forces_local(tmp_path):
    """_adjacent_pure's open-region check scans (dp, up] -- inclusive of the
    use pc itself -- using a real (non-synthetic) luac-compiled shape.

    'print(string.format("%d", 42))': string.format's own CALL has C==0
    (its results feed print's open argument list), so it both *reads*
    registers 2 and 3 as explicit arguments AND (via writes_open) implicitly
    re-defines them with its own return values -- at the very same pc as the
    read (up). A strictly-between scan (dp, up) would never reach pc == up
    at all, so this specifically exercises the half-open-at-the-top window,
    not just "some open region exists somewhere in this function" (which
    test_windowing_ignores_open_regions_outside_the_def_use_window pins the
    negative of). See test_call_arg_staging_is_temp for the contrasting case
    -- same shape of Lua source, without the open call -- where the
    equivalent registers correctly inline as temps.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("print(string.format('%d', 42))", tmp_path)
    rc = classify_registers(fn)
    assert {2, 3} <= rc.locals


def test_windowing_ignores_open_regions_outside_the_def_use_window():
    """Round-2 regression pin: an open-region instruction elsewhere in the
    function -- outside a candidate's own (dp, up] window -- must NOT
    disqualify that candidate. An earlier version of classify_registers
    poisoned its defs/uses dicts globally for every open-region instruction
    in the function, regardless of position; on the 229-file corpus that
    flipped 154 of 342 temp->local reclassifications for zero soundness
    gain (registers whose own def/use window had no open region in it at
    all). This is a synthetic function (tests/synth.py) with two disjoint
    regions: an open VARARG at pc 2, unrelated to register 9's own def (pc
    4) and use (pc 6) later in the same function -- register 9's window
    contains no open-region instruction, so it must still inline as a temp
    despite the function having one elsewhere.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    unrelated_def_ri = mk_instr(Op.LOADK, a=0, bx=0, pc=1)
    unrelated_def_fx = InstrEffects(reads=frozenset(), writes=frozenset({0}),
                                     reads_open=False, writes_open=False,
                                     effect=Effect.PURE, may_error=False)
    vararg_ri = mk_instr(Op.VARARG, a=0, b=0, pc=2)          # open, but far from reg 9's window
    vararg_fx = InstrEffects(reads=frozenset(), writes=frozenset(),
                              reads_open=False, writes_open=True,
                              effect=Effect.PURE, may_error=False)
    unrelated_use_ri = mk_instr(Op.MOVE, a=1, b=0, pc=3)
    unrelated_use_fx = InstrEffects(reads=frozenset({0}), writes=frozenset({1}),
                                     reads_open=False, writes_open=False,
                                     effect=Effect.PURE, may_error=False)
    def_ri = mk_instr(Op.LOADK, a=9, bx=0, pc=4)
    def_fx = InstrEffects(reads=frozenset(), writes=frozenset({9}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    filler_ri = mk_instr(Op.MOVE, a=2, b=1, pc=5)
    filler_fx = InstrEffects(reads=frozenset({1}), writes=frozenset({2}),
                              reads_open=False, writes_open=False,
                              effect=Effect.PURE, may_error=False)
    use_ri = mk_instr(Op.MOVE, a=3, b=9, pc=6)
    use_fx = InstrEffects(reads=frozenset({9}), writes=frozenset({3}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    instrs = {
        1: LirInstr(ri=unrelated_def_ri, effects=unrelated_def_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=vararg_ri, effects=vararg_fx, successors=(3,), consumed=()),
        3: LirInstr(ri=unrelated_use_ri, effects=unrelated_use_fx, successors=(4,), consumed=()),
        4: LirInstr(ri=def_ri, effects=def_fx, successors=(5,), consumed=()),
        5: LirInstr(ri=filler_ri, effects=filler_fx, successors=(6,), consumed=()),
        6: LirInstr(ri=use_ri, effects=use_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0,) * 6, numparams=0, maxstacksize=10)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=6,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(fn)
    assert 9 in rc.temps and 9 not in rc.locals


def test_corpus_no_open_region_in_pre_fix_temp_window(corpus_dir):
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
    """
    from pyluadec.ingest import load_file
    from pyluadec.lift import Effect, lift_proto

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

    def walk(proto):
        try:
            fn = lift_proto(proto)
        except Exception:
            fn = None
        if fn is not None:
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
        for sp in proto.subprotos:
            walk(sp)

    for f in sorted(corpus_dir.glob("*.lua")):
        walk(load_file(f))

    assert hits == [], f"open-region instruction inside a pre-fix temp window: {hits[:5]}"


def test_adjacent_pure_window_excludes_the_def_pc_itself():
    """Pins _adjacent_pure's window at the BOTTOM: (dp, up] is exclusive at
    dp, inclusive at up. The top boundary (inclusive at up) is already
    covered by test_open_write_at_use_pc_forces_local; nothing in this
    module's existing tests pins the bottom.

    Mutating the scan from `dp < pc <= up` to `dp <= pc <= up` (i.e.
    including the def instruction's own pc in the barrier scan) makes a
    register's *own* def-time effect/may_error block its *own* eligibility
    -- nonsensical, since _adjacent_pure's barriers are about what happens
    *between* computing a value and consuming it, not about the computation
    itself. On the 229-file corpus this exact mutation flips 49 registers
    temp->local for no soundness reason (a computed-once value that was
    never touched by anything else is still safe to inline at its single
    use site, regardless of whether computing it could itself raise/mutate
    the heap -- that risk exists identically whether the value is inlined
    or stored to a local first).

    Register 5's def (pc 1) is deliberately given effect=ARBITRARY,
    may_error=True -- exactly what a realistic risky def instruction (e.g.
    GETGLOBAL or ADD under EffectMode.STRICT) looks like -- with its single
    use immediately adjacent (pc 2, nothing between). Under the correct
    exclusive-at-dp window, dp itself is never scanned, so this passes
    unaffected -> temp. Under the `[dp, up]` mutation, dp enters the scan
    and its own effect/may_error immediately fails the barrier -> local.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    def_ri = mk_instr(Op.ADD, a=5, b=0, c=1, pc=1)
    def_fx = InstrEffects(reads=frozenset(), writes=frozenset({5}),
                           reads_open=False, writes_open=False,
                           effect=Effect.ARBITRARY, may_error=True)
    use_ri = mk_instr(Op.MOVE, a=6, b=5, pc=2)
    use_fx = InstrEffects(reads=frozenset({5}), writes=frozenset({6}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    instrs = {
        1: LirInstr(ri=def_ri, effects=def_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=use_ri, effects=use_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0, 0), numparams=0, maxstacksize=8)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=2,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(fn)
    assert 5 in rc.temps and 5 not in rc.locals


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

    'for i = 1, 3 do print(i) end local x = 1 x = x + 1 x = x + 1 print(x)'
    reproduces this directly with real luac output: register 0 is the
    for-loop's init/'a' control slot (FORPREP/FORLOOP both write and read
    it), and after the loop ends luac reuses register 0 for the entirely
    unrelated local `x`, written three more times and read twice more.
    Fails against the pre-fix `controls`-only override (register 0 would be
    forced temp, and reconstruct.py would then try to pop-once-inline a
    value that's actually reassigned and read multiple times).
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("for i = 1, 3 do print(i) end local x = 1 x = x + 1 x = x + 1 print(x)",
             tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps
    # the loop's own control machinery is otherwise unaffected by register
    # 0's demotion: the loop variable is still local and recorded as such
    # (registers 1/2, the limit/step slots, happen to *also* get reused for
    # this exact source's trailing `print(x)` call -- correctly demoted for
    # the same reason, not asserted here since that's incidental to this
    # source rather than the property under test).
    assert 3 in rc.locals and 3 in rc.loop_vars


def test_register_reused_between_two_loops_sharing_it_as_control_base_classifies_local(tmp_path):
    """M3 task-5 round-3 review pin: `_staging_window_ok` (round 2) checked
    *membership* -- does this pc fall in some gap before some loop that
    claims r -- but not *chain coherence*: do ALL of r's defs/uses belong to
    exactly one loop's own control lifetime. When the same register is the
    control base for TWO loops, ordinary code living in the gap BETWEEN
    them (not staging for either) gets swept into "the gap before the
    second loop" and misclassified temp.

    'for i=1,3 do print(i) end do local x=1 x=x+1 x=x+1 print(x) end for
    j=1,5 do print(j) end': register 0 is loop 1's control base, then `x`
    once that scope frees it, then loop 2's control base again. Removing
    the second `for` loop makes register 0 correctly classify local under
    round 2's code too -- it is specifically the *later* claim that used to
    provide cover for x's activity to hide in the gap.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn(
        "for i=1,3 do print(i) end "
        "do local x = 1  x = x + 1  x = x + 1  print(x) end "
        "for j=1,5 do print(j) end",
        tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps


def test_two_loops_legitimately_sharing_a_control_base_both_stay_temp(tmp_path):
    """The other direction of the round-3 fix, pinned separately so the
    chain-coherence check can't be satisfied by simply always demoting a
    register claimed by more than one loop: 'for i=1,3 do print(i) end for
    j=1,5 do print(j) end' -- two numeric-for loops immediately adjacent,
    genuinely sharing registers 0/1/2 as their control base with NO
    unrelated activity in the gap between them -- must still classify all
    three temp.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("for i=1,3 do print(i) end for j=1,5 do print(j) end", tmp_path)
    rc = classify_registers(fn)
    assert {0, 1, 2} <= rc.temps
    assert not ({0, 1, 2} & rc.locals)


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

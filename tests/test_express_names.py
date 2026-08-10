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
    silently clobber any register from its base up to maxstacksize. Real
    luac never places one between a temp candidate's def and use (see
    test_corpus_no_open_region_in_single_def_use_window for the empirical
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


def test_open_region_outside_its_affected_range_still_blocks_via_barrier():
    """Isolates _adjacent_pure's unconditional open-region barrier from the
    defs/uses open-region augmentation in classify_registers.

    Register 2's def/use window (pc 1..3) contains a VARARG B==0 at pc 2 with
    base register 5 -- its conservatively-touched range [5, maxstacksize) does
    NOT include register 2, so the defs/uses augmentation adds no entry for
    register 2 at all; only the unconditional "any open-region instruction in
    the window blocks, regardless of which registers it touches" barrier in
    _adjacent_pure can catch this. (Confirmed by hand: removing just that
    barrier while keeping the augmentation flips register 2 to temp.)
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


def test_open_write_at_use_pc_forces_local_via_defs_augmentation(tmp_path):
    """Isolates the defs/uses open-region augmentation from _adjacent_pure's
    barrier, using a real (non-synthetic) luac-compiled shape.

    'print(string.format("%d", 42))': string.format's own CALL has C==0
    (its results feed print's open argument list), so it both *reads*
    registers 2 and 3 as explicit arguments AND (via writes_open) implicitly
    *re-defines* them with its own return values -- at the very same pc as
    the read. _adjacent_pure's window scan is strictly `dp < pc < up`, so an
    open-region instruction sitting exactly *at* up (never strictly between
    dp and up) never reaches that barrier at all. Only the augmentation
    (which is not windowed -- it runs once per instruction, unconditionally)
    adds the second def entry that makes len(defs[reg]) != 1. (Confirmed by
    hand: removing just the augmentation while keeping the barrier flips
    registers 2 and 3 to temp; see test_call_arg_staging_is_temp for the
    contrasting case, same shape of Lua source, without the open call.)
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("print(string.format('%d', 42))", tmp_path)
    rc = classify_registers(fn)
    assert {2, 3} <= rc.locals


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

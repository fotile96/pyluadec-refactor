"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

import bisect
from dataclasses import dataclass

from pyluadec.cfg import build_cfg
from pyluadec.express.freereg import stack_discipline
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import Op

from pyluadec.lift import LUA_KEYWORDS

# Hard cap on the length of one loop's staging chain (see _staging_slice).
# Real luac staging is three instructions for a numeric for and up to a
# handful for a generic for whose iterator is an indexed call; the cap only
# exists so that a pathological or hand-built chain cannot make
# classify_registers' cost depend on how many defs a register has. Hitting
# it abandons the proof, which classifies the register local -- the safe way
# to be wrong.
_MAX_STAGING_STEPS = 64


@dataclass(frozen=True)
class RegClass:
    """Local/temp/loop-var partition of a function's registers, plus the
    per-*definition* refinement of it (`temp_defs`).

    Only covers registers with at least one *tracked* (explicit, present in
    an instruction's .writes/.reads) def or use. A register classify_registers
    never sees at all -- dead stack space that is never written or read, or a
    register touched only implicitly by an open-region read/write outside any
    candidate's own def/use window -- appears in none of locals/temps/
    loop_vars. Callers must not assume every register in
    range(fn.proto.maxstacksize) is classified; a register missing from all
    three sets is untracked, not "temp by default."

    ## `locals`/`temps`/`loop_vars` are per register *number*

    These three fields are a whole-function partition, and luac freely reuses
    one register number for a declared local in one statement and an
    expression-stack temporary in the next (`lparser.c` resets
    `fs->freereg = fs->nactvar` at the end of every statement, so every slot
    at or above `nactvar` is scratch that is reallocated statement by
    statement). A register used both ways therefore cannot have a single
    honest verdict here, and `temps` keeps its strict meaning: **every**
    tracked definition of the register is a temporary. A register with even
    one surviving definition lands in `locals`.

    ## `temp_defs` is the (register, definition-pc) refinement

    `temp_defs` holds one entry per *definition site* -- `(pc, reg)` is
    present iff the value written into `reg` at `pc` is consumed before the
    end of the statement that produced it, i.e. iff luac's parser had no
    active local variable in that slot at that pc. This is the field a
    reconstructor should consult when it is deciding what to do with one
    particular write; `temps` answers only the much weaker whole-function
    question. The two agree by construction: for every `r in temps`, every
    tracked def `(pc, r)` is in `temp_defs`, so a consumer that switches from
    one to the other can only ever *gain* staging decisions, never lose one.

    Registers whose verdict does not come from the freereg simulation at all
    (parameters, closure-captured slots, `for` loop variables, and loop
    control slots) are handled exactly as before and contribute all-or-nothing
    to `temp_defs`: a control triple that passes `_control_lifetime_ok`
    contributes every one of its defs, everything else in that group
    contributes none.
    """
    locals: frozenset[int]
    temps: frozenset[int]
    loop_vars: frozenset[int]    # declared by the for statement itself, never by LocalDecl
    # (pc, reg) for every definition that is a luac expression-stack
    # temporary. Defaults to empty so the many hand-built RegClass fixtures
    # that predate this field keep constructing; a caller that wants the
    # per-def refinement must go through classify_registers.
    temp_defs: frozenset[tuple[int, int]] = frozenset()


def name_for(reg: int, depth: int) -> str:
    n = f"l{depth}_{reg}"
    assert n.isidentifier() and n not in LUA_KEYWORDS and not n.startswith("__pld_")
    return n


def classify_registers(fn: LirFunction) -> RegClass:
    defs: dict[int, list[int]] = {}
    uses: dict[int, list[int]] = {}
    ordered = sorted(fn.instrs)
    for pc in ordered:
        li = fn.instrs[pc]
        for r in li.effects.writes:
            defs.setdefault(r, []).append(pc)
        for r in li.effects.reads:
            uses.setdefault(r, []).append(pc)
    controls: set[int] = set()
    loop_vars: set[int] = set()
    # One entry per loop *occurrence* (not per register): its control triple
    # {a,a+1,a+2}, the pcs of its own FORPREP/FORLOOP/TFORLOOP, and its
    # "loop_start" -- the pc the backward staging slice starts from.
    # For numeric-for that's FORPREP's own pc (staging is directly adjacent
    # to it). For generic-for it's the *leading* JMP that skips straight to
    # the TFORLOOP test on entry, not TFORLOOP's own pc -- TFORLOOP is
    # separated from its staging by the entire loop body in program order
    # (luac's layout is: [stage iterator triple] -> [leading JMP to test] ->
    # [body] -> TFORLOOP -> [JMP back]). Starting the slice at TFORLOOP
    # would put the whole loop body, and the basic-block boundary at the
    # body's head, between the header and the staging it consumes
    # (round-3 review finding).
    occurrences: list[dict] = []
    jmp_targets: dict[int, int] = {}          # successor pc -> a JMP pc that targets it
    for pc in ordered:
        ri = fn.instrs[pc].ri
        if ri.op is Op.JMP:
            jmp_targets.setdefault(fn.instrs[pc].successors[0], pc)
    seen_forloop_pcs: set[int] = set()
    for pc in ordered:
        ri = fn.instrs[pc].ri
        if ri.op is Op.FORPREP:
            triple = {ri.a, ri.a + 1, ri.a + 2}
            occ_pcs = {pc}
            forloop_pc = fn.instrs[pc].successors[0]
            if forloop_pc in fn.instrs and fn.instrs[forloop_pc].ri.op is Op.FORLOOP:
                occ_pcs.add(forloop_pc)
                seen_forloop_pcs.add(forloop_pc)
            controls |= triple
            loop_vars.add(ri.a + 3)
            occurrences.append({"triple": triple, "control_pcs": occ_pcs,
                                "loop_start": pc, "vars": {ri.a + 3}})
        elif ri.op is Op.FORLOOP and pc not in seen_forloop_pcs:
            # A FORLOOP whose paired FORPREP wasn't found above (malformed/
            # unexpected bytecode) -- still claim it defensively rather than
            # silently drop it, treating it as its own (maximally
            # conservative: loop_start == its own pc) occurrence.
            triple = {ri.a, ri.a + 1, ri.a + 2}
            controls |= triple
            loop_vars.add(ri.a + 3)
            occurrences.append({"triple": triple, "control_pcs": {pc},
                                "loop_start": pc, "vars": {ri.a + 3}})
        elif ri.op is Op.TFORLOOP:
            triple = {ri.a, ri.a + 1, ri.a + 2}
            controls |= triple
            occ_vars = set(range(ri.a + 3, ri.a + 3 + ri.c))
            loop_vars |= occ_vars
            loop_start = jmp_targets.get(pc, pc)
            occurrences.append({"triple": triple, "control_pcs": {pc},
                                "loop_start": loop_start, "vars": occ_vars})
    claims: dict[int, list[int]] = {}         # register -> indices into `occurrences`
    own_control_pcs: dict[int, set[int]] = {}  # register -> control pcs of ITS OWN claimers
    for i, occ in enumerate(occurrences):
        for r in occ["triple"]:
            claims.setdefault(r, []).append(i)
            own_control_pcs.setdefault(r, set()).update(occ["control_pcs"])

    # pcs whose write region is unbounded (`R[a..top)`): they can clobber a
    # register without appearing in `defs`, so a staging chain may not be
    # proved *across* one (see _staging_slice).
    open_write_pcs = [pc for pc in ordered if fn.instrs[pc].effects.writes_open]

    block_floor_cache: dict[int, int] = {}
    leader_pcs: list[int] = []

    def _block_floor(pc: int) -> int:
        """First pc of the basic block containing `pc`.

        Staging for a loop header is always emitted by luac into the header's
        own basic block -- it is straight-line code with no branch between the
        expressions and the header that consumes them. Refusing to look for a
        producer past the block entry is therefore complete for real luac
        output, and it keeps the search from wandering into an unrelated
        predecessor block whose writes have nothing to do with this loop.
        """
        if not leader_pcs:
            leader_pcs.extend(sorted(build_cfg(fn).blocks))
        if pc not in block_floor_cache:
            block_floor_cache[pc] = leader_pcs[bisect.bisect_right(leader_pcs, pc) - 1]
        return block_floor_cache[pc]

    slice_cache: dict[int, dict[int, set[int]]] = {}

    def _staging_slice(occ_index: int) -> dict[int, set[int]]:
        """`pc -> registers of this occurrence's control triple that pc is a
        proved part of the control lifetime for`.

        This is a backward slice over the loop header's OWN operand registers,
        not a syntactic scan of neighbouring instructions. Starting from the
        occurrence's `loop_start` with the whole control triple "needed", it
        repeatedly jumps to the nearest *tracked def* of any still-needed
        register (via `defs`, by bisection -- never by scanning the
        instructions in between) and records that instruction as the producer
        of the registers it writes. A producer that also reads a triple
        register (generic-for's `CALL` reads its own callee slot and
        overwrites it with the first result; a `GETGLOBAL`/`GETTABLE` chain
        rewrites the same slot repeatedly) puts those registers back into the
        needed set, so a multi-instruction iterator-staging chain is followed
        to its true root. The walk ends as soon as every triple register has
        a producer.

        Two things bound the work, neither of them the size of the function:
          - the walk never looks below the header's own basic block entry
            (`_block_floor`), and
          - it takes at most `_MAX_STAGING_STEPS` jumps; each jump moves
            strictly backwards and is found by bisection, so the cost is
            proportional to the length of the staging chain (three
            instructions for a numeric for, a handful for a generic for),
            not to how much code precedes the loop.
        Giving up early (either bound, or an unbounded-write instruction
        standing between a producer and its consumer) simply leaves registers
        unattributed, which forces them local -- the safe direction.
        """
        if occ_index in slice_cache:
            return slice_cache[occ_index]
        occ = occurrences[occ_index]
        slice_cache[occ_index] = _walk_staging(
            occ, _block_floor(occ["loop_start"]))
        return slice_cache[occ_index]

    def _walk_staging(occ: dict, floor: int) -> dict[int, set[int]]:
        """`_staging_slice`'s walk, with the floor supplied by the caller.

        Split out for `_window_floor` below, which needs the same backward
        slice but must not force a CFG. Everything the walk does is
        floor-independent; the floor only truncates it earlier."""
        triple: set[int] = occ["triple"]
        attributed: dict[int, set[int]] = {}
        need = set(triple)
        pos = occ["loop_start"]
        for _ in range(_MAX_STAGING_STEPS):
            if not need:
                break
            best = -1
            for r in need:
                dl = defs.get(r)
                if not dl:
                    continue
                j = bisect.bisect_left(dl, pos) - 1
                if j >= 0 and floor <= dl[j] and dl[j] > best:
                    best = dl[j]
            if best < 0:
                break
            k = bisect.bisect_right(open_write_pcs, best)
            if k < len(open_write_pcs) and open_write_pcs[k] < pos:
                break                      # an `R[a..top)` write may clobber; unprovable
            eff = fn.instrs[best].effects
            attributed.setdefault(best, set()).update(
                (eff.writes & need) | (eff.reads & triple))
            need = (need - eff.writes) | (eff.reads & triple)
            pos = best
        return attributed

    window_floor_cache: dict[int, int] = {}

    def _window_floor(occ_index: int) -> int:
        """The lowest pc this occurrence's ownership window reaches: the first
        instruction of the staging chain that feeds its header.

        Deliberately computed with **no basic-block floor**, i.e. NOT via
        `_staging_slice`. `_block_floor` builds the CFG, and this value is
        needed for every control register of every loop, on every call --
        including for hand-built `LirFunction`s whose successors point past
        their own last instruction, which `build_cfg` cannot survive (see
        `freereg.stack_discipline`'s `block_floor` parameter for why that
        laziness is load-bearing). Dropping the floor can only make the window
        WIDER, which pulls more pre-loop defs inside it, which can only make
        `_control_lifetime_ok` refuse more often -- the pre-M5-task-5
        behaviour, and the safe direction.
        """
        if occ_index not in window_floor_cache:
            occ = occurrences[occ_index]
            pcs = set(_walk_staging(occ, ordered[0] if ordered else 0))
            window_floor_cache[occ_index] = min(
                pcs | occ["control_pcs"] | {occ["loop_start"]})
        return window_floor_cache[occ_index]

    # ---- loop WINDOWS: where a `for` header's slots are actually its own ----
    #
    # A `for` header owns registers `a..a+2` (the control triple) and `a+3...`
    # (the visible variables) -- but it owns them only for the pcs its own
    # statement spans, exactly as `lparser.c`'s `fornum`/`forlist` open a
    # `BlockCnt` around them and `leaveblock` releases them at the loop's
    # `end`. Before M5 task 5 that ownership was a whole-FUNCTION property
    # here, which is what `lparser.c` never says: `leaveblock` restores
    # `fs->freereg = fs->nactvar` and hands `a..a+3` straight back to the next
    # statement's expression stack, and luac reuses them immediately
    # (`for i = 0, 20 do f(i) end  g(0, "", 60)` puts `g`'s callee in `a` and
    # its third argument in `a+3`).
    #
    # The window is `[_window_floor(i), max(control_pcs)]`: from the first
    # instruction of the staging chain that feeds the header, through the
    # header, the body and the closing FORLOOP/TFORLOOP -- and nothing else.
    # A register is looked up per pc against the windows of the occurrences
    # that claim it; outside all of them the slot is ordinary scratch and the
    # freereg simulation is its only judge.
    ctl_win: dict[int, list[int]] = {}       # register -> occurrence indices
    var_win: dict[int, list[int]] = {}
    for i, occ in enumerate(occurrences):
        for r in occ["triple"]:
            ctl_win.setdefault(r, []).append(i)
        for r in occ["vars"]:
            var_win.setdefault(r, []).append(i)

    def _in(idxs, pc: int) -> bool:
        return any(_window_floor(i) <= pc <= max(occurrences[i]["control_pcs"])
                   for i in idxs)

    def _control_lifetime_ok(r: int) -> bool:
        """True iff every tracked def and use of r *inside one of r's control
        windows* belongs to a claiming loop occurrence's control lifetime:
        that loop's own FORPREP/FORLOOP/TFORLOOP, or an instruction the
        backward slice above proved to be part of the chain producing r for
        that loop's header.

        Defs and uses OUTSIDE every window are not asked about at all (M5
        task 5). They are not the loop's business: the slot has been handed
        back to the expression stack by then (`leaveblock` restores
        `fs->freereg = fs->nactvar`), and the ordinary per-definition rules in
        `freereg.stack_discipline` are the right judge of them. Asking about
        them is what made `for i = 0, 20 do layerLoad(i, "") end
        switchScreen(0, "", 60)` (`snr_novel.lua:main_6`) grade `switchScreen`
        and its first two arguments named locals: the third argument reuses
        the loop variable's slot, which counted as an assignment to a named
        local and so ended the statement early.

        `controls` is accumulated over EVERY FORPREP/FORLOOP/TFORLOOP in the
        function, purely by register number -- it says nothing about whether
        THIS register is genuinely dedicated to being some loop's control
        slot, or whether luac later reused the same number for a completely
        unrelated, ordinary local (round-2 review: measured 188/188
        controls-forced registers on the corpus that the ordinary def/use
        rules below would have classified local -- register 0 in one file
        alone had hundreds of ordinary defs/uses spread across the whole
        function, entirely unrelated to any loop).

        Two weaker proxies for this question have already failed here, both
        of them syntactic rather than data-flow:
          - *membership in some gap between two control pcs* (round 2): with
            the same register serving as the control base of two loops, any
            unrelated code sitting textually between them falls in "the gap
            before the second loop" and is swallowed.
          - *a backward run of instructions whose writes intersect the
            triple* (round 3): `do local x = 5 end for i=1,3 do print(i) end`
            walks straight through the loop's own three staging writes into
            `x`'s initialisation, because that write also targets a register
            number in the triple. It only appeared to work when a zero-result
            CALL happened to sit in between and terminate the run.
        The slice above asks the actual question instead -- *which
        instruction produced the value this loop header reads* -- so an
        earlier, already-overwritten write to the same register number is
        never reached, however adjacent it is.

        Only the claiming occurrences' own control pcs are exempted. A def of
        r at some *other* loop's FORLOOP/TFORLOOP (r being that loop's
        variable, say) is real double duty and stays in the census.
        """
        exempt = own_control_pcs.get(r, ())
        extra = {pc for pc in defs.get(r, []) if pc not in exempt}
        extra |= {pc for pc in uses.get(r, []) if pc not in exempt}
        if not extra:
            # Answered without consulting a window at all -- deliberately, so
            # a function whose only loop is its whole body never forces
            # `_window_floor` (and through it the staging walk) to run.
            return True
        extra = {pc for pc in extra if _in(ctl_win.get(r, ()), pc)}
        if not extra:
            return True
        idxs = claims.get(r, ())
        return all(
            any(r in _staging_slice(i).get(pc, ()) for i in idxs)
            for pc in extra)

    regs = set(defs) | set(uses) | controls | loop_vars
    # Control slots whose ENTIRE def/use census belongs to the loop headers
    # that claim them -- i.e. the ones that really are dedicated loop control
    # registers rather than a number some `for` header happens to share with
    # an unrelated ordinary local.
    dedicated_controls = {r for r in sorted(controls) if _control_lifetime_ok(r)}
    # Registers already known to be real, named locals before the freereg
    # simulation runs: parameters, closure-captured slots, and every slot a
    # `for` header genuinely owns (a dedicated control triple and the visible
    # loop variables). Seeding them keeps the simulation from ever pushing
    # them as temps and from treating a read of one as a read of a consumed
    # temp.
    #
    # A control slot that FAILED `_control_lifetime_ok` is deliberately not
    # seeded: it is, by that verdict, an ordinary register that a loop header
    # merely reuses, and seeding it would leave the simulation with no opinion
    # at all about its non-control definitions. The whole-register verdict for
    # it is `local` either way (the `controls` branch below), but its
    # individual definitions still deserve the per-def answer -- without this,
    # every register number a `for` header touches loses `temp_defs` entirely,
    # and a `for k, v in pairs(x)` at the end of a function retroactively
    # materializes every temporary that ever used slots a/a+1/a+2 anywhere
    # before it (measured: this alone is the difference between `local l0_1 =
    # g  l0_1 = l0_1()` and `local l0_1 = g()` in
    # `if x then local y = g() print(y) end for k, v in pairs(x) do ... end`).
    #
    # Since M5 task 5 all three of the sets below are asked *per pc*, not per
    # register: a `for` header owns its slots only inside its own extent (see
    # the extent block above). Outside it the same register number is ordinary
    # scratch and the simulation must be free to grade it, which is exactly
    # what `for i = 0, 20 do f(i) end g(0, "", 60)` needs -- with whole-
    # function seeding, `g`'s third argument (which lands in the loop
    # variable's slot) counted as a write to a named local, ended the
    # statement, and promoted `g` and its first two arguments to locals.
    frame_locals = set(range(fn.proto.numparams)) | set(fn.captured_regs)

    def _known_local(r: int, pc: int) -> bool:
        return (r in frame_locals
                or (r in dedicated_controls and _in(ctl_win.get(r, ()), pc))
                or _in(var_win.get(r, ()), pc))

    def _loop_control(r: int, pc: int) -> bool:
        return r in controls and _in(ctl_win.get(r, ()), pc)

    def _named_local(r: int, pc: int) -> bool:
        return r in frame_locals or _in(var_win.get(r, ()), pc)

    stack_temps, stack_temp_defs = stack_discipline(
        fn, ordered, _known_local, _loop_control, _named_local, _block_floor)
    locals_: set[int] = set()
    temps: set[int] = set()
    # (pc, reg) definitions the reconstructor may stage instead of
    # materializing. Assembled alongside the per-register verdict below so the
    # two can never disagree about a register the whole-function rules decide:
    # each branch either contributes every one of the register's defs or none
    # of them, and only the `stack_temps` branch -- the freereg simulation,
    # the one rule that is genuinely per definition -- contributes a subset.
    temp_defs: set[tuple[int, int]] = set()
    sim_by_reg: dict[int, set[tuple[int, int]]] = {}
    for key in stack_temp_defs:
        sim_by_reg.setdefault(key[1], set()).add(key)

    def all_defs_of(r: int) -> set[tuple[int, int]]:
        return {(pc, r) for pc in defs.get(r, ())}

    def _outside(r: int, spans) -> set[tuple[int, int]]:
        """The simulation's temp verdicts for `r`'s definitions OUTSIDE the
        `for` extents that own it. Inside them the header's own rules decide
        (a proved control triple's staging is a temp, a loop variable's
        `for`-statement binding is a local); outside, the slot is ordinary
        scratch and the freereg simulation is the judge."""
        return {k for k in sim_by_reg.get(r, ()) if not _in(spans, k[0])}

    for r in sorted(regs):
        # Parameters and closure-captured registers are named, live locals by
        # construction -- checked FIRST so that the `controls` branch cannot
        # override them. luac never hands a live parameter's or an upvalue's
        # slot to a loop header, so this is unreachable from real bytecode;
        # it is ordered this way because leaving an unconditional temp
        # override in front of two guards that exist to be unconditional is
        # the kind of inconsistency this module has already been bitten by
        # (M3 task-5 round-5 review).
        if r < fn.proto.numparams or r in fn.captured_regs:
            locals_.add(r); continue
        if r in controls:
            spans = ctl_win.get(r, ())
            if r in dedicated_controls:
                # Inside its own extent every def of a proved control slot is
                # header staging, hence a temp; outside, the simulation
                # decides. The whole-register verdict follows from the two
                # (`temps` still means "every tracked def of r is a temp",
                # which is what `RegClass` documents and what `_read_reg`
                # falls back on).
                mine = {(pc, r) for pc in defs.get(r, ()) if _in(spans, pc)}
                mine |= _outside(r, spans)
                temp_defs |= mine
                if defs.get(r) and mine == all_defs_of(r):
                    temps.add(r)
                else:
                    locals_.add(r)
            else:
                locals_.add(r)
                temp_defs |= sim_by_reg.get(r, frozenset())
            continue
        if r in loop_vars:
            spans = var_win.get(r, ())
            # A loop variable is a named local for the `for` statement's own
            # extent and ordinary scratch after it (`lparser.c`'s `forbody`
            # opens a block around it; `leaveblock` at the loop's `end` gives
            # the slot straight back).
            mine = _outside(r, spans)
            temp_defs |= mine
            if defs.get(r) and mine == all_defs_of(r):
                temps.add(r)
            else:
                locals_.add(r)
            continue
        temp_defs |= sim_by_reg.get(r, frozenset())
        if r in stack_temps:
            temps.add(r)
        else:
            locals_.add(r)
    return RegClass(locals=frozenset(locals_), temps=frozenset(temps),
                    loop_vars=frozenset(loop_vars),
                    temp_defs=frozenset(temp_defs))

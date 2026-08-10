"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

import bisect
from dataclasses import dataclass

from pyluadec.lift.effects import Effect
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import Op

from pyluadec.lift import LUA_KEYWORDS


@dataclass(frozen=True)
class RegClass:
    """Local/temp/loop-var partition of a function's registers.

    Only covers registers with at least one *tracked* (explicit, present in
    an instruction's .writes/.reads) def or use. A register classify_registers
    never sees at all -- dead stack space that is never written or read, or a
    register touched only implicitly by an open-region read/write outside any
    candidate's own def/use window -- appears in none of locals/temps/
    loop_vars. Callers must not assume every register in
    range(fn.proto.maxstacksize) is classified; a register missing from all
    three sets is untracked, not "temp by default."

    Modeling limitation: this is a whole-function, per-register-*number*
    classification, but luac freely reuses a register number for different,
    lexically disjoint local variables across a single function (once one
    variable's scope ends, the compiler is free to hand that slot to the
    next). classify_registers has no live-range/scope model, so any verdict
    it gives is necessarily an approximation for a register reused this way
    -- the `controls` handling below is the one place this project has
    already had to correct for it (a register can be a control slot for one
    loop's range and an ordinary, multiply-written/read local everywhere
    else in the same function; see that code's comment). A future
    consumer that needs more precision than "one verdict per register
    number for the whole function" will need actual live-range analysis,
    which this module does not attempt (M3 task-5 round-2 review).
    """
    locals: frozenset[int]
    temps: frozenset[int]
    loop_vars: frozenset[int]    # declared by the for statement itself, never by LocalDecl


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
    control_pcs: set[int] = set()             # pcs of FORPREP/FORLOOP/TFORLOOP themselves
    # One entry per loop *occurrence* (not per register): its control triple
    # {a,a+1,a+2}, the control_pcs belonging to it, and its "loop_start" --
    # the pc where this specific occurrence's own textual footprint begins.
    # For numeric-for that's FORPREP's own pc (staging is directly adjacent
    # to it). For generic-for it's the *leading* JMP that skips straight to
    # the TFORLOOP test on entry, not TFORLOOP's own pc -- TFORLOOP is
    # separated from its staging by the entire loop body in program order
    # (luac's layout is: [stage iterator triple] -> [leading JMP to test] ->
    # [body] -> TFORLOOP -> [JMP back]), so anchoring on TFORLOOP itself
    # would make the loop body's own instructions look like they sit between
    # staging and "loop start", breaking the adjacency check below for every
    # generic-for (round-3 review finding).
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
            control_pcs |= occ_pcs
            controls |= triple
            loop_vars.add(ri.a + 3)
            occurrences.append({"triple": triple, "control_pcs": occ_pcs, "loop_start": pc})
        elif ri.op is Op.FORLOOP and pc not in seen_forloop_pcs:
            # A FORLOOP whose paired FORPREP wasn't found above (malformed/
            # unexpected bytecode) -- still claim it defensively rather than
            # silently drop it, treating it as its own (maximally
            # conservative: loop_start == its own pc) occurrence.
            triple = {ri.a, ri.a + 1, ri.a + 2}
            control_pcs.add(pc)
            controls |= triple
            loop_vars.add(ri.a + 3)
            occurrences.append({"triple": triple, "control_pcs": {pc}, "loop_start": pc})
        elif ri.op is Op.TFORLOOP:
            triple = {ri.a, ri.a + 1, ri.a + 2}
            control_pcs.add(pc)
            controls |= triple
            loop_vars |= set(range(ri.a + 3, ri.a + 3 + ri.c))
            loop_start = jmp_targets.get(pc, pc)
            occurrences.append({"triple": triple, "control_pcs": {pc}, "loop_start": loop_start})
    claims: dict[int, list[dict]] = {}        # register -> occurrences claiming it
    for occ in occurrences:
        for r in occ["triple"]:
            claims.setdefault(r, []).append(occ)

    def _occurrence_window(occ: dict) -> tuple[int, int]:
        """(boundary, loop_start): the open interval a def/use pc must fall
        in to count as this occurrence's own staging. Found by walking
        backward from loop_start through `ordered`, extending the window
        past any instruction that writes into this occurrence's OWN control
        triple (the loop's staging block, however many instructions -- one
        LOADK each for numeric-for's init/limit/step; a GETGLOBAL-then-
        CALL-with-self-overwrite pair for generic-for's iterator function
        slot) and stopping at the first instruction that does not (an
        unrelated instruction, or another loop's own control instruction
        that happens not to share this triple).
        """
        triple = occ["triple"]
        i = bisect.bisect_left(ordered, occ["loop_start"]) - 1
        while i >= 0 and fn.instrs[ordered[i]].effects.writes & triple:
            i -= 1
        boundary = ordered[i] if i >= 0 else 0
        return boundary, occ["loop_start"]

    def _staging_window_ok(r: int) -> bool:
        """True iff every def/use of r *outside* the FORPREP/FORLOOP/TFORLOOP
        instructions that claim it falls within some claiming occurrence's
        own staging window (see _occurrence_window).

        `controls` is accumulated over EVERY FORPREP/FORLOOP/TFORLOOP in the
        function, purely by register number -- it says nothing about whether
        THIS register is genuinely dedicated to being some loop's control
        slot, or whether luac later reused the same number for a completely
        unrelated, ordinary local (round-2 review: measured 188/188
        controls-forced registers on the corpus that the ordinary def/use
        rules below would have classified local -- register 0 in one file
        alone had hundreds of ordinary defs/uses spread across the whole
        function, entirely unrelated to any loop).

        Membership in *some* gap between two control instructions is not
        enough on its own (round-2's first attempt): when the same register
        is later reused as a second loop's control base, everything living
        in the gap between the first loop's end and the second loop's start
        -- including genuinely unrelated code with its own local variables
        -- looks like it's "before some control_pc that claims r" (round-3
        review: `for i=1,3 do end; do local x=1 x=x+1 x=x+1 end; for j=1,5
        do end` reusing register 0 as x lets x's writes hide in the gap
        between the two loops). What actually distinguishes genuine staging
        is *chain coherence*: every def/use of r must belong to exactly one
        loop occurrence's own control lifetime -- its own control
        instructions plus the staging block immediately, contiguously
        adjacent to that occurrence's start (_occurrence_window), not merely
        somewhere in the wide gap since the previous loop ended.
        """
        extra = sorted(
            {pc for pc in defs.get(r, []) if pc not in control_pcs}
            | {pc for pc in uses.get(r, []) if pc not in control_pcs})
        if not extra:
            return True
        windows = [_occurrence_window(occ) for occ in claims.get(r, ())]
        return all(any(lo < pc < hi for lo, hi in windows) for pc in extra)

    regs = set(defs) | set(uses) | controls | loop_vars
    locals_: set[int] = set()
    temps: set[int] = set()
    for r in sorted(regs):
        if r in controls:
            if _staging_window_ok(r):
                temps.add(r)
            else:
                locals_.add(r)
            continue
        if r in loop_vars:
            locals_.add(r); continue
        if r < fn.proto.numparams or r in fn.captured_regs:
            locals_.add(r); continue
        d, u = defs.get(r, []), uses.get(r, [])
        if len(d) != 1 or len(u) != 1:
            locals_.add(r); continue
        dp, up = d[0], u[0]
        if dp >= up or not _adjacent_pure(fn, r, dp, up, ordered):
            locals_.add(r); continue
        temps.add(r)
    return RegClass(locals=frozenset(locals_), temps=frozenset(temps),
                    loop_vars=frozenset(loop_vars))


def _adjacent_pure(fn: LirFunction, reg: int, dp: int, up: int, ordered) -> bool:
    """No open region through the use (inclusive), no write to reg's inputs,
    and no WRITE_HEAP/may_error strictly between the def and its use.

    Two different windows, deliberately:
      - The open-region check (reads_open/writes_open) scans (dp, up] --
        including the use instruction itself. An open WRITE at the very use
        pc (e.g. a CALL C==0 whose own execution both reads reg as an
        explicit argument and, via its open result-write, overwrites reg's
        slot with a return value right after) is a same-pc hazard a
        strictly-between scan cannot see -- this is the
        print(string.format(...)) corpus case (M3 task-4 round-2 review).
        Checked without regard to which specific registers the open region
        touches: its affected range has a known base but an unbounded top,
        so this function cannot prove reg falls outside it. This check is
        NOT scoped to any wider range than a single candidate's own (dp, up]
        window -- unlike an earlier version of this function, it must never
        disqualify a register for an open-region instruction that has
        nothing to do with that register's own def/use pair (see round-2
        review: over-broad global open-region bookkeeping had flipped 154 of
        342 registers to local for zero soundness gain, verified on the
        229-file corpus).
      - The other barriers (a write to one of the def's own inputs, or an
        intervening WRITE_HEAP-effect/may_error instruction) are checked
        over the strictly-between window (dp, up), as before: they are
        about what happens *before* reg is consumed, not about the
        consuming instruction's own other effects.
    """
    dli = fn.instrs[dp]
    inputs = set(dli.effects.reads)
    for pc in ordered:
        if not (dp < pc <= up):
            continue
        li = fn.instrs[pc]
        if li.effects.reads_open or li.effects.writes_open:
            return False
        if pc == up:
            continue
        if li.effects.writes & inputs:
            return False
        if li.effects.effect >= Effect.WRITE_HEAP or li.effects.may_error:
            return False
    return True

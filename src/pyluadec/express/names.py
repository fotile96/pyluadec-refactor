"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

import bisect
from dataclasses import dataclass

from pyluadec.cfg import build_cfg
from pyluadec.lift.effects import Effect
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
            occurrences.append({"triple": triple, "control_pcs": occ_pcs, "loop_start": pc})
        elif ri.op is Op.FORLOOP and pc not in seen_forloop_pcs:
            # A FORLOOP whose paired FORPREP wasn't found above (malformed/
            # unexpected bytecode) -- still claim it defensively rather than
            # silently drop it, treating it as its own (maximally
            # conservative: loop_start == its own pc) occurrence.
            triple = {ri.a, ri.a + 1, ri.a + 2}
            controls |= triple
            loop_vars.add(ri.a + 3)
            occurrences.append({"triple": triple, "control_pcs": {pc}, "loop_start": pc})
        elif ri.op is Op.TFORLOOP:
            triple = {ri.a, ri.a + 1, ri.a + 2}
            controls |= triple
            loop_vars |= set(range(ri.a + 3, ri.a + 3 + ri.c))
            loop_start = jmp_targets.get(pc, pc)
            occurrences.append({"triple": triple, "control_pcs": {pc}, "loop_start": loop_start})
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
        triple: set[int] = occ["triple"]
        floor = _block_floor(occ["loop_start"])
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
        slice_cache[occ_index] = attributed
        return attributed

    def _control_lifetime_ok(r: int) -> bool:
        """True iff every tracked def and use of r belongs to one claiming
        loop occurrence's control lifetime: that loop's own FORPREP/FORLOOP/
        TFORLOOP, or an instruction the backward slice above proved to be
        part of the chain producing r for that loop's header.

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
            return True
        idxs = claims.get(r, ())
        return all(
            any(r in _staging_slice(i).get(pc, ()) for i in idxs)
            for pc in extra)

    regs = set(defs) | set(uses) | controls | loop_vars
    locals_: set[int] = set()
    temps: set[int] = set()
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
            if _control_lifetime_ok(r):
                temps.add(r)
            else:
                locals_.add(r)
            continue
        if r in loop_vars:
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

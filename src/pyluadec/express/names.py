"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

import bisect
from dataclasses import dataclass

from pyluadec.cfg import build_cfg
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
    # Registers already known to be real, named locals before the freereg
    # simulation runs: parameters, closure-captured slots, and every slot a
    # `for` header owns (its control triple and its visible loop variables).
    # Seeding them keeps the simulation from ever pushing them as temps and
    # from treating a read of one as a read of a consumed temp.
    stack_temps = _stack_discipline(
        fn, ordered,
        controls | loop_vars | set(range(fn.proto.numparams)) | set(fn.captured_regs))
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
        if r in stack_temps:
            temps.add(r)
        else:
            locals_.add(r)
    return RegClass(locals=frozenset(locals_), temps=frozenset(temps),
                    loop_vars=frozenset(loop_vars))


def _stack_discipline(fn: LirFunction, ordered: list[int],
                      known_locals: set[int]) -> set[int]:
    """Registers whose EVERY definition in this function is a luac *temporary*
    -- a value pushed onto the expression stack and consumed again before the
    statement that produced it ends.

    ## Why this replaced the old def/use "adjacent pure" barrier (M3 task 8)

    The previous rule was: a register is a temp iff it has exactly one
    tracked def and one tracked use, in that order, with no WRITE_HEAP/
    may_error/open-region instruction in between. That is a *per-register-
    number, whole-function* question, and luac does not allocate registers
    that way. It reuses the same slot for a fresh temporary in every
    statement, so on real corpus code a register like `1` typically has a
    dozen defs and a dozen uses and the single-def rule rejected it outright.
    Everything it rejected then materialized as a real `local`, which needs
    more stack slots than luac used -- `maxstacksize` was the single largest
    mismatch cluster on the corpus (1292/1944 protos, measured before this
    change; the two shapes below were 1220 of them).

    It was also wrong in the other direction, for a reason worth recording
    because it explains why simply loosening the barrier's effect mode
    achieved nothing (measured: 339/1944 both before and after). The barrier
    was accidentally acting as a crude *statement-boundary detector*: in
    `local x = 1 print(x)` the `GETGLOBAL print` sitting between x's def and
    its use is what kept x local (GETGLOBAL is ARBITRARY under STRICT).
    Re-grading GETGLOBAL to READ_HEAP made genuine temps inlinable and
    genuine locals inlinable at the same rate, so the net was exactly zero.
    The effect model was never answering the question being asked.

    ## The rule this implements instead

    `lparser.c`'s `statement()` ends with `fs->freereg = fs->nactvar` -- at
    every statement boundary the expression stack is empty and only declared
    locals occupy registers. Registers below `nactvar` are named locals;
    everything at or above it is scratch that lives and dies inside one
    statement. So:

        a definition is a temp iff its value is consumed before the end of
        the statement that produced it, and a local iff it survives one.

    That is directly simulable from the bytecode without knowing `nactvar`,
    because `freereg` after any value-producing instruction is simply its
    target register plus one (luaK frees an operator's operands and then
    `exp2nextreg`s the result into the lowest slot it just freed). The
    simulation keeps a `pending` stack of pushed-but-unconsumed values:

      * a value producer targeting `a` pops every pending entry at or above
        `a` (those are exactly the operands it just consumed) and pushes its
        own results;
      * a statement-ending instruction (`CALL` with C==1, `TAILCALL`,
        `RETURN`, `SETGLOBAL`, `SETUPVAL`, `FORPREP`, `CLOSE`, or a write
        whose target is already a known local) pops its own operands and then
        **promotes everything still pending to local** -- surviving a
        statement boundary is the definition of being one;
      * `SETTABLE`/`SETLIST` pop only above the table's own register, leaving
        the table itself pending: `local t = {} t.x = 1` and `local t = {x=1}`
        differ only in NEWTABLE's size hints, so the table's fate is left to
        be decided by whether it survives a *later* boundary;
      * conditions (`TEST`/`EQ`/`LT`/`LE`) and `JMP` only read. Nothing is
        popped there, so `if f() then` correctly keeps f()'s result a temp
        (the next instruction to target that slot pops it) while
        `local x = f() if x then` correctly promotes x at the boundary that
        follows.

    A pending value must be read exactly once before it is popped, or the
    register is disqualified: zero reads would make the reconstructor's
    environment leak a staged expression that is never emitted (a silently
    dropped statement), and more than one read would make it inline the same
    expression tree -- and re-evaluate it -- in two places. Reading a
    register that is neither pending nor a known local (i.e. re-reading a
    value already consumed) disqualifies it for the same reason.

    ## Soundness

    This is a *heuristic for reconstructing luac's input*, exactly as the old
    barrier was, and it is not what makes the output safe: nothing this feeds
    ever ships unless L3 certification recompiles the printed source back to
    the original proto under the normalization ladder, which is strictly
    stronger than any register model. Being wrong here costs certifications,
    never correctness. The verdict is aggregated per register number and any
    single disqualified definition makes the whole register local, so the
    approximation is one-directional: a register the simulation is unsure
    about becomes a named local, which is always printable.

    Known approximation (unchanged in kind from the previous rule): the walk
    is pc-linear and has no control-flow model, so a `pending` value that is
    live across a branch is simulated as if the branch fell through. Because
    every statement boundary clears `pending` entirely, and luac places
    branches at statement boundaries, this is exact for real luac output; on
    anything else it drifts toward "promote to local", the safe direction.
    """
    pending: list[list[int]] = []           # [reg, def_pc, n_reads], reg-ascending
    verdict: dict[int, bool] = {}

    def mark(reg: int, ok: bool) -> None:
        verdict[reg] = verdict.get(reg, True) and ok

    def do_read(r: int) -> None:
        for ent in pending:
            if ent[0] == r:
                ent[2] += 1
                return
        if r not in known_locals:
            # Not pending and not a known local: either a slot this function
            # never defines, or a second read of an already-consumed temp.
            # Either way it cannot be a pop-once inlinable binding.
            mark(r, False)

    def read_open(base: int) -> None:
        """An `R[base..top)` read (CALL/TAILCALL B==0, RETURN B==0, SETLIST
        B==0) consumes every pending value from `base` upwards. Counting
        those reads is what lets `print(string.format(...))` keep its two
        staged argument registers as temps."""
        for ent in pending:
            if ent[0] >= base:
                ent[2] += 1

    def pop_ge(base: int) -> None:
        while pending and pending[-1][0] >= base:
            reg, _dpc, n = pending.pop()
            mark(reg, n == 1)

    def promote_all() -> None:
        while pending:
            reg, _dpc, _n = pending.pop()
            mark(reg, False)

    # NOTE on the intermediate `promote_all()` calls below (fault-injection
    # result, M3 task 8): disabling the one after a `CALL` statement, or the
    # one after a write to an already-known local, changes NOTHING -- not the
    # corpus ledger (byte-identical), not any test, and not any shape
    # constructed by hand to try to separate them. That is not an accident:
    # the terminal `promote_all()` after the loop disqualifies every register
    # still pending at the end, and a register that survives an intermediate
    # boundary survives to that one too unless a later `pop_ge` reaches it --
    # which only happens when the register is redefined, and a redefinition
    # gives it a second def that must independently prove itself clean. They
    # are kept because they state the model (a statement boundary empties the
    # expression stack) at the point it applies rather than leaving it
    # implicit, but they are documented here as defensive rather than
    # load-bearing, so nobody reads their presence as evidence they were
    # needed.
    for pc in ordered:
        li = fn.instrs[pc]
        ri = li.ri
        op, a, b, c = ri.op, ri.a, ri.b, ri.c

        def push(regs) -> None:
            for r in regs:
                if r not in known_locals:
                    pending.append([r, pc, 0])

        for r in sorted(li.effects.reads):
            do_read(r)
        if li.effects.reads_open:
            read_open(a if op is Op.RETURN else a + 1)

        if op in (Op.CALL, Op.TAILCALL):
            pop_ge(a)
            if op is Op.TAILCALL or c == 1:
                promote_all()                      # call statement / tail return
            elif c == 0:
                push((a,))                         # open producer
            else:
                push(range(a, a + c - 1))
        elif op is Op.RETURN:
            if b != 1:
                pop_ge(a)
            promote_all()
        elif op in (Op.SETGLOBAL, Op.SETUPVAL, Op.FORPREP):
            pop_ge(a)
            promote_all()
        elif op in (Op.CLOSE, Op.FORLOOP, Op.TFORLOOP):
            promote_all()
        elif op in (Op.SETTABLE, Op.SETLIST):
            pop_ge(a + 1)                          # table itself stays pending
        elif op in (Op.JMP, Op.TEST, Op.EQ, Op.LT, Op.LE):
            pass                                   # reads only
        elif op is Op.VARARG:
            if b == 0:
                pop_ge(a); push((a,))
            elif b >= 2:
                pop_ge(a); push(range(a, a + b - 1))
        else:
            writes = sorted(li.effects.writes)
            if writes:
                pop_ge(writes[0])
                if writes[0] in known_locals:
                    promote_all()                  # assignment to a named local
                else:
                    push(writes)
    promote_all()
    return {r for r, ok in verdict.items() if ok}

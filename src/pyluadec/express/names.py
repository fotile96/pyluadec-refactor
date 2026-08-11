"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

import bisect
from collections.abc import Callable
from dataclasses import dataclass

from pyluadec.cfg import build_cfg
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import OP_SPECS, ArgMode, Fmt, Op, isk

from pyluadec.lift import LUA_KEYWORDS

# Hard cap on the length of one loop's staging chain (see _staging_slice).
# Real luac staging is three instructions for a numeric for and up to a
# handful for a generic for whose iterator is an indexed call; the cap only
# exists so that a pathological or hand-built chain cannot make
# classify_registers' cost depend on how many defs a register has. Hitting
# it abandons the proof, which classifies the register local -- the safe way
# to be wrong.
_MAX_STAGING_STEPS = 64

# lopcodes.h's `MAXINDEXRK` (`BITRK - 1`, BITRK = 1 << (SIZE_B - 1) = 256):
# the largest constant-table index that fits in an RK operand. Past it
# `luaK_exp2RK` gives up and loads the constant into a register instead.
_MAXINDEXRK = 255


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
    stack_temps, stack_temp_defs = _stack_discipline(
        fn, ordered,
        dedicated_controls | loop_vars | set(range(fn.proto.numparams))
        | set(fn.captured_regs),
        frozenset(controls),
        frozenset(loop_vars) | frozenset(range(fn.proto.numparams))
        | frozenset(fn.captured_regs),
        _block_floor)
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
            if r in dedicated_controls:
                temps.add(r)
                temp_defs |= all_defs_of(r)
            else:
                locals_.add(r)
                temp_defs |= sim_by_reg.get(r, frozenset())
            continue
        if r in loop_vars:
            locals_.add(r); continue
        temp_defs |= sim_by_reg.get(r, frozenset())
        if r in stack_temps:
            temps.add(r)
        else:
            locals_.add(r)
    return RegClass(locals=frozenset(locals_), temps=frozenset(temps),
                    loop_vars=frozenset(loop_vars),
                    temp_defs=frozenset(temp_defs))


def _stack_discipline(fn: LirFunction, ordered: list[int],
                      known_locals: set[int],
                      loop_control_regs: frozenset[int],
                      named_locals: frozenset[int],
                      block_floor: Callable[[int], int],
                      ) -> tuple[set[int], set[tuple[int, int]]]:
    """`(registers whose EVERY definition is a luac temporary, the set of
    individual `(def_pc, reg)` definitions that are temporaries)`.

    A luac *temporary* is a value pushed onto the expression stack and
    consumed again before the statement that produced it ends.

    The second element is the primary result and the first is a projection of
    it (`{r : r has defs and all of them are in the second}` plus the
    read-poisoning below); they are returned together because both are cheap
    once the walk has run and `RegClass` publishes both. The per-definition
    answer is the one that matches luac: `nactvar` changes from statement to
    statement, so "is slot r a local?" is only ever well posed at a given pc.

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
        whose target is already a NAMED local -- `named_locals`: a parameter,
        a closure-captured slot, or a `for` variable, but deliberately NOT a
        `for` header's control triple, whose staging writes happen mid
        -statement) pops its own operands and then
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
    never correctness.

    The approximation is still one-directional -- every way of being unsure
    (a definition read zero times or twice, a definition still pending at a
    statement boundary, a read of a slot with nothing pending, a jump the
    pc-linear walk models as fall-through) drives the answer toward "local",
    which is always printable. What changed in M4 task 13 is only the
    *granularity* of that answer: an unsure definition no longer drags every
    other definition of the same register number down with it.

    ## Why the per-definition answer cannot clobber a live local

    `lparser.c:1333` asserts `fs->freereg >= fs->nactvar` at every statement
    boundary, and `luaK_reserveregs`/`freereg` maintain it in between: an
    expression-stack temporary is always allocated at or above every active
    local. So a slot can only be handed to a temporary once the local that
    held it has left scope, and a definition graded a temporary here is never
    a write over a still-live named local. (The walk has no control-flow
    model, so this is a statement about real luac output, which is what the
    reconstruction is for; anything else drifts local, per the paragraph
    above.)

    Known approximation (unchanged in kind from the previous rule): the walk
    is pc-linear and has no control-flow model, so a `pending` value that is
    live across a branch is simulated as if the branch fell through. Because
    every statement boundary clears `pending` entirely, and luac places
    branches at statement boundaries, this is exact for real luac output; on
    anything else it drifts toward "promote to local", the safe direction.
    """
    # Back-edge spans `[target, source]`. luac's loops are natural and its
    def _same_block(d: int, r: int) -> bool:
        """True iff pcs `d` and `r` are in the same CFG basic block.

        THE control-flow requirement on per-definition staging. A staged
        definition is not a statement: it lives only in the reconstructor's
        register environment until a read pops and inlines it. Two things
        follow, and both are violated as soon as a definition and its read
        sit in different blocks.

        1. **Execution counts must match.** `local i = 0 repeat i = i + 1
           until i > 5` defines register 0 once, before the loop, and reads it
           once per iteration; the pc-linear walk below sees exactly one read
           and would call the definition a temporary, which moves `local i =
           0` inside the body and the program never terminates. The mirror
           image -- defined in a loop body, read after the loop -- hoists work
           out of the loop.

        2. **Block scoping must match.** `emit.lua` wraps every `if` arm and
           loop body in `Reconstructor.open_scope`/`close_scope`, which
           snapshot and restore the staging environment because a `local`
           declared in one Lua block is out of scope in the next. A value
           staged *before* a block and popped *inside* it has its pop rolled
           back at `close_scope`, so whatever the block computed from it
           disappears from the output entirely; a value staged *inside* a
           block and read *after* it is discarded by the same rollback.
           Measured on `snr_common.lua:main_77_20`, whose `if` arm's whole
           `CONCAT` statement vanished from the printed function (M4 task 13;
           the certification gate refused the result so it never shipped, but
           the proto dropped from `L3` to `L1`, which is what caught it).

        A basic block cannot span a branch or a jump target, so "same block"
        gives both properties at once. It is stronger than either strictly
        needs -- `f(a or b)` stages the callee in one block and calls it in
        another -- and the cost of that strictness was measured rather than
        assumed (see the task report). Erring here materializes a named local,
        which is always printable; the alternative is silently dropped code.
        """
        return block_floor(d) == block_floor(r)
    def _pending_def(r: int):
        for ent in pending:
            if ent[0] == r:
                return ent
        return None

    def _renders_as_literal(ent) -> bool:
        """True iff this pending definition would be printed as a Lua *literal*
        (`1`, `"s"`, `nil`, `true`) rather than as a name or a compound
        expression -- i.e. iff `lparser.c` would read it back as VKNUM/VK/
        VNIL/VTRUE/VFALSE.
        """
        d = fn.instrs[ent[1]].ri
        if d.op is Op.LOADK:
            k = fn.proto.constants[d.bx]
            if isinstance(k, bytes):
                # A string literal is already `VK` when `luaK_exp2RK` sees it
                # (`codestring` interns it through `luaK_stringK` at parse
                # time), so lcode.c's test is on its INDEX: `e->u.s.info <=
                # MAXINDEXRK`. Past that luac loads it into a register
                # instead, which is exactly the shape being examined, so the
                # barrier must not fire. The original proto's index is a proxy
                # for the recompiled one -- being wrong costs a certification,
                # never correctness.
                return d.bx <= _MAXINDEXRK
            # A NUMBER literal is `VKNUM` -- it is not in the constant table
            # yet, and `luaK_exp2RK` tests `fs->nk <= MAXINDEXRK`, the table's
            # SIZE, before interning it. So in a proto with more than 256
            # constants luac loads even `1` into a register, however low the
            # index it would eventually get. Using the index here instead
            # (which this did in its first draft) declared that `LOADK` a
            # local and cost `snr_crd_15.lua:main_1` and
            # `snr_crd_20.lua:main_1` their certification -- both have >400
            # constants, and both compare against a small integer near the
            # end of the function.
            return len(fn.proto.constants) <= _MAXINDEXRK
        if d.op is Op.LOADNIL or (d.op is Op.LOADBOOL and d.c == 0):
            # VNIL/VTRUE/VFALSE, same as VKNUM: interned at exp2RK time, so
            # the test is on the table's size.
            return len(fn.proto.constants) <= _MAXINDEXRK
        return False

    def _bar_literal_operands(li) -> None:
        """Disqualify pending definitions that this instruction reads in a
        position where luac would never have used a register at all.

        Two ways that happens, both of them in `lcode.c`:

        * an **RK operand** (`OP_SPECS`' `ArgMode.K` slots, transcribed from
          `lopcodes.c`): `luaK_exp2RK` encodes a literal straight into B/C
          with the K bit set. So `EQ 0 R0 K"x"` proves R0 held something that
          was *not* a literal at that point -- a local. Inlining a staged
          `LOADK` there prints `if 1 == 2 then`, which recompiles to
          `EQ 0 K1 K2` with no `LOADK` and a different constant table.
        * a **unary fold**: `luaK_prefix` runs `codearith(OP_UNM)`/`codenot`,
          and both fold a literal operand at parse time (`constfolding`,
          `codenot`). `-1` and `not 1` never emit `UNM`/`NOT`, so an `UNM`/
          `NOT` reading a register proves that register was not a literal.

        Binary arithmetic needs no separate fold rule: its operands are RK
        slots, so the first bullet already covers `LOADK 0 K1; ADD 0 0 K1`
        (which is `local a = 1  a = a + 1`, the shape that made this barrier
        necessary -- without it the two statements collapse into
        `local a = 1 + 1`, which luac folds back to a single `LOADK`).
        """
        ri = li.ri
        if ri.op is Op.MOVE and ri.b < ri.a:
            # `MOVE d, s` with `s < d` proves `s` held a NAMED LOCAL, not a
            # temporary. `luaK_exp2nextreg` runs `freeexp` first, and
            # `freeexp` only releases a VNONRELOC expression sitting at
            # `freereg - 1` (it asserts exactly that), so discharging a
            # temporary into the next free register finds `reg ==
            # e->u.s.info` and emits nothing at all. A copy from a lower slot
            # upward is `discharge2reg`'s VLOCAL case: the source is below
            # `nactvar` and must be preserved, so luac makes a copy.
            #
            # Without this, `local n = p  n = string.gsub(n, ...)` inlines the
            # parameter into the call and collapses the whole chain of
            # reassignments into one nested expression -- semantically fine,
            # but it deletes a local the original declared and the recompile
            # loses every `MOVE`. Measured on `snr_common.lua:main_77_1`.
            ent = _pending_def(ri.b)
            if ent is not None:
                ent[3] = 1
        spec = OP_SPECS[ri.op]
        slots: list[int] = []
        if spec.fmt is Fmt.iABC:
            if spec.bmode is ArgMode.K and not isk(ri.b):
                slots.append(ri.b)
            if spec.cmode is ArgMode.K and not isk(ri.c):
                slots.append(ri.c)
        if ri.op in (Op.UNM, Op.NOT):
            slots.append(ri.b)
        for r in slots:
            ent = _pending_def(r)
            if ent is not None and _renders_as_literal(ent):
                ent[3] = 1

    # [reg, def_pc, n_reads, disqualified], reg-ascending. `disqualified` is
    # set by a read this definition cannot legally be inlined into even though
    # the read count is right (see _same_block and the constant-folding
    # barrier below); it is carried on the entry rather than applied
    # immediately so that a single pop site stays the one place a verdict is
    # recorded.
    # `block_floor` is `classify_registers._block_floor`: the first pc of the
    # basic block containing a pc. It is required, not defaulted -- a default
    # would have to be either "everything is one block" (silently unsound: it
    # turns _same_block into a tautology) or an eager `build_cfg` (which a
    # hand-built LirFunction whose successors point past its own last
    # instruction cannot survive). Passing the caller's lazy one gets both:
    # sound, and no CFG is built for a function whose staging never crosses a
    # block boundary.
    pending: list[list[int]] = []
    verdict: dict[int, bool] = {}
    def_verdict: dict[tuple[int, int], bool] = {}
    last_def: dict[int, int] = {}           # reg -> pc of its most recent push

    def mark(reg: int, ok: bool) -> None:
        verdict[reg] = verdict.get(reg, True) and ok

    def mark_def(pc: int, reg: int, ok: bool) -> None:
        key = (pc, reg)
        def_verdict[key] = def_verdict.get(key, True) and ok

    def do_read(r: int, at: int) -> None:
        for ent in pending:
            if ent[0] == r:
                ent[2] += 1
                if not _same_block(ent[1], at):
                    ent[3] = 1
                return
        if r not in known_locals and r not in loop_control_regs:
            # Not pending and not a known local: either a slot this function
            # never defines, or a second read of an already-consumed temp.
            # Either way it cannot be a pop-once inlinable binding.
            #
            # `loop_control_regs` is exempted from the poisoning but NOT from
            # being pushed (that is `known_locals`' job). A `for` header's own
            # FORLOOP/TFORLOOP re-reads its control slots on every iteration,
            # long after FORPREP consumed the staged values; those reads are
            # the loop's own bookkeeping, not a decompiler-visible second use,
            # and blaming the staging definition for them would materialize
            # `for i = 1, 10` as `local l0_0 = 1  for i = l0_0, 10, 1`.
            mark(r, False)
            # Per-definition, blame the definition that produced the value
            # being re-read -- the most recent push into this slot, which the
            # walk has already popped. Grading THAT def local is what makes
            # the reconstructor materialize it as a named local, so the
            # second read has a name to refer to instead of an expression
            # that was already inlined somewhere else. A slot with no
            # preceding def in this function (an uninitialised read) has
            # nothing to blame and simply contributes no `temp_defs` entry,
            # which is the local direction anyway.
            if r in last_def:
                mark_def(last_def[r], r, False)

    def read_open(base: int, at: int) -> None:
        """An `R[base..top)` read (CALL/TAILCALL B==0, RETURN B==0, SETLIST
        B==0) consumes every pending value from `base` upwards. Counting
        those reads is what lets `print(string.format(...))` keep its two
        staged argument registers as temps."""
        for ent in pending:
            if ent[0] >= base:
                ent[2] += 1
                if not _same_block(ent[1], at):
                    ent[3] = 1

    def pop_ge(base: int) -> None:
        while pending and pending[-1][0] >= base:
            reg, dpc, n, bad = pending.pop()
            mark(reg, n == 1 and not bad)
            mark_def(dpc, reg, n == 1 and not bad)

    def promote_all() -> None:
        while pending:
            reg, dpc, _n, _bad = pending.pop()
            mark(reg, False)
            mark_def(dpc, reg, False)

    # NOTE on the two intermediate `promote_all()` calls below. They are NOT
    # interchangeable and were separately fault-injected (M3 task 8, corrected
    # in round 1 after the original note lumped them together and got the
    # first one wrong).
    #
    # 1. The one after a `CALL`/`TAILCALL` statement is LOAD-BEARING. It is
    #    what protects a local whose slot is released by SCOPE EXIT rather
    #    than by a redefinition. In `do local a = f() g(a) end h()`, `end`
    #    drops `a` from `nactvar` and `GETGLOBAL h` reuses register 0, but
    #    nothing in the instruction stream marks the release: luac emits
    #    `CLOSE` only when the block captured an upvalue, so the `CLOSE`
    #    boundary does not cover this, and no other boundary sees it either.
    #    Without this line the pending entry for `a` (one def, one read)
    #    survives to the `pop_ge` of that reuse and is graded a pop-once temp,
    #    which would inline it as `g(f())` -- hoisting `GETGLOBAL g` in front
    #    of the call to `f`, an observable reordering under STRICT. Measured:
    #    neutering it changes classification on 14 of 1944 corpus protos; the
    #    committed ledger stays byte-identical only because all 14 are already
    #    `L1` for unrelated reasons, which is luck, not structure. Pinned by
    #    tests/test_express_names.py::
    #    test_local_released_by_scope_exit_is_not_inlined_as_a_temp.
    #
    # 2. The one after a write to an already-known local is redundant on this
    #    corpus -- measured separately: 0 of 1944 protos change classification
    #    when it alone is neutered. Different reason, and a structural one:
    #    that branch runs `pop_ge(writes[0])` first, and a *live* named local
    #    sits below every pending temp (pending entries are only pushed at or
    #    above freereg, which is at or above `nactvar`), so the `pop_ge` has
    #    already drained the stack and `promote_all()` finds it empty. The
    #    residual gap is the same one as in (1): `known_locals` is a
    #    whole-function set, so a slot that was a named local in an exited
    #    scope is still treated as one here. Should that ever leave a lower
    #    pending entry behind, this `promote_all()` fires in the SAFE
    #    direction (promote to local), which is why it is kept rather than
    #    deleted as dead.
    #
    # Both are kept because they state the model (a statement boundary empties
    # the expression stack) at the point it applies rather than leaving it
    # implicit. Only (2) is currently documentation; (1) is behaviour.
    for pc in ordered:
        li = fn.instrs[pc]
        ri = li.ri
        op, a, b, c = ri.op, ri.a, ri.b, ri.c

        def push(regs) -> None:
            for r in regs:
                if r not in known_locals:
                    pending.append([r, pc, 0, 0])
                    last_def[r] = pc

        _bar_literal_operands(li)
        for r in sorted(li.effects.reads):
            do_read(r, pc)
        if li.effects.reads_open:
            read_open(a if op is Op.RETURN else a + 1, pc)

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
                if writes[0] in named_locals:
                    promote_all()                  # assignment to a named local
                else:
                    push(writes)
    promote_all()
    return ({r for r, ok in verdict.items() if ok},
            {key for key, ok in def_verdict.items() if ok})

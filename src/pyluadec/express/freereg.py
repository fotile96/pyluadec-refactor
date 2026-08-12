"""luac's `freereg = nactvar` allocation discipline, simulated.

`express/names.py::classify_registers` asks one question per definition site:
did `lparser.c` have an active local variable in that slot at that pc?
`stack_discipline` answers it by simulating the expression stack `lparser.c`
maintains, and nothing else -- it knows nothing about `for` headers, loop
ownership windows or `RegClass`. The four callbacks in its signature are the
entire interface to the caller's half of the analysis.

Split out of `names.py` in M5 task 11. The split is exactly where the
callback interface already was: `_stack_discipline` never closed over
`classify_registers`' state, so the move is textual.
"""
from __future__ import annotations

from collections.abc import Callable

from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import OP_SPECS, ArgMode, Fmt, Op, isk

# lopcodes.h's `MAXINDEXRK` (`BITRK - 1`, BITRK = 1 << (SIZE_B - 1) = 256):
# the largest constant-table index that fits in an RK operand. Past it
# `luaK_exp2RK` gives up and loads the constant into a register instead.
_MAXINDEXRK = 255


def stack_discipline(fn: LirFunction, ordered: list[int],
                     known_local: Callable[[int, int], bool],
                     loop_control: Callable[[int, int], bool],
                     named_local: Callable[[int, int], bool],
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

        1. **Execution counts must match.** A definition read once per loop
           iteration but written only once before the loop must not be popped
           on its first textual read -- that would move the definition inside
           the loop body and change how often it runs.
           `local i = 0 repeat i = i + 1 until i > 5` is NOT a working example
           of this on its own (fix round 1, F5(a), re-measured 2026-08-11):
           neutering `_same_block` alone still certifies this shape `L3`,
           because `i`'s definition is *already* disqualified by the ordinary
           pop-once accounting before `_same_block` gets a say -- it is read
           once by the `until` test AND once by the body's `i = i + 1`, two
           textual reads of the same pending entry, which fails the "read
           exactly once" rule regardless of blocks (see
           `tests/test_express_liverange.py::LOCAL_CASES[2]`'s docstring for
           the traced-through account, including what DOES require both
           `_same_block` and the RK/literal barrier to fail this fixture).
           The concrete shape that DOES need `_same_block` for execution-count
           correctness, reproduced this session:
           `local b, c = 1, 2  local a = b or c  while a do a = b or c end
           print(a)` -- neutering `_same_block` prints
           `while l0_0 or l0_1 do local l0_2 = l0_0 or l0_1 end
           print(l0_0 or l0_1)`, silently turning the reassignment to `a`
           into a fresh, unrelated local `l0_2` inside the loop rather than a
           write to the outer `a`. Certification refuses this (a `code`/
           `maxstacksize` mismatch), so it never ships, but it is a genuinely
           different program, not merely an unfaithful one -- pinned as
           `tests/test_express_liverange.py::LOCAL_CASES_CERT_ONLY[0]`.

        2. **Block scoping must match.** `emit.lua` wraps every `if` arm and
           loop body in `Reconstructor.open_scope`/`close_scope`, which
           snapshot and restore the staging environment because a `local`
           declared in one Lua block is out of scope in the next. A value
           staged *before* a block and popped *inside* it has its pop rolled
           back at `close_scope`, so whatever the block computed from it
           disappears from the output entirely; a value staged *inside* a
           block and read *after* it is discarded by the same rollback.
           `snr_common.lua:main_77_20` was the shape that motivated this rule
           during M4 task 13's development (its `if` arm's whole `CONCAT`
           statement vanished with `_same_block` neutered at that point in the
           change). It does NOT reproduce against the code at HEAD (fix round
           1, F5(b), re-measured 2026-08-11: printing `main_77_20` with and
           without the guard gives byte-identical bodies) -- some other
           change in the same task's fix history (plausibly the RK/literal
           barrier, added afterward) came to cover this specific shape too.
           Historical, not a live pin; kept as the motivating example for
           *why* the block-scoping property must hold, not as a claim this
           exact proto currently demonstrates the failure.

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
            # upward is what luac emits instead: `luaK_dischargevars` turns
            # `VLOCAL` into `VNONRELOC` carrying the local's own slot
            # (`lcode.c:306-309`), and `discharge2reg`'s `VNONRELOC` arm then
            # sees `reg != e->u.s.info` and codes the `MOVE`
            # (`lcode.c:367-371`). `discharge2reg` itself has no `VLOCAL`
            # case; the local's slot is below `nactvar` and must be
            # preserved, so the copy is the only option.
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
        if not known_local(r, at) and not loop_control(r, at):
            # Not pending and not a known local: either a slot this function
            # never defines, or a second read of an already-consumed temp.
            # Either way it cannot be a pop-once inlinable binding.
            #
            # `loop_control` is exempted from the poisoning but NOT from
            # being pushed (that is `known_local`'s job). A `for` header's own
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
    #    residual gap is the same one as in (1): a slot released by an
    #    ordinary `do ... end` block's exit (as opposed to a `for`'s, which
    #    M5 task 5 made pc-scoped) is still treated as a named local here. Should that ever leave a lower
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
                if not known_local(r, pc):
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
                if named_local(writes[0], pc):
                    promote_all()                  # assignment to a named local
                else:
                    push(writes)
    promote_all()
    return ({r for r, ok in verdict.items() if ok},
            {key for key, ok in def_verdict.items() if ok})

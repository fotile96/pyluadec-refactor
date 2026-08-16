"""luac's `freereg = nactvar` allocation discipline, simulated.

`express/names.py::classify_registers` asks one question per definition site:
did `lparser.c` have an active local variable in that slot at that pc?
`stack_discipline` answers it by simulating the expression stack `lparser.c`
maintains, and nothing else -- it knows nothing about `for` headers, loop
ownership windows or `RegClass`. The four callbacks in its signature are the
entire interface to the caller's half of the analysis.

Split out of `names.py` in M5 task 11, at exactly the seam the callback
interface already drew: `_stack_discipline` never closed over
`classify_registers`' state, which is what let the first of that task's two
code commits move the body across byte for byte. The second one then did
change things here -- the three state-independent barriers became the
module-level functions below, `pending` entries became `_Pending` instead of
4-element lists read by index, and `push` stopped being rebuilt once per
instruction inside the walk's own loop. Every step was checked by
regenerating `corpus/ledger.jsonl` and requiring it byte-identical, which
proves those 1944 protos classify the same and proves nothing about shapes
the corpus lacks (it reaches 33 of 38 opcodes).
"""
from __future__ import annotations

import bisect
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from pyluadec.lift.lift import LirFunction, LirInstr
from pyluadec.lift.opcodes import OP_SPECS, ArgMode, Fmt, Op, isk

# lopcodes.h's `MAXINDEXRK` (`BITRK - 1`, BITRK = 1 << (SIZE_B - 1) = 256):
# the largest constant-table index that fits in an RK operand. Past it
# `luaK_exp2RK` gives up and loads the constant into a register instead.
_MAXINDEXRK = 255


def _merge_veto_skipped_kill(reg: int, def_pc: int, kill_li: LirInstr,
                             jmp_list: list[tuple[int, int]],
                             reads_at: dict[int, list[int]],
                             writes_at: dict[int, list[int]],
                             open_reads: list[tuple[int, int]]) -> bool:
    """Skipped-kill veto (M7 task 7): True iff `kill_li` (a write popping the
    pending entry for `reg` defined at `def_pc`) does not read `reg` itself
    -- so the pop is a kill, not an operand consumption -- AND a `JMP`
    between the definition and the kill jumps past the kill to a point where
    `reg`'s next tracked mention is a *read*.

    On that taken path the entry's value survives what the pc-linear walk
    modelled as its death: the single read the walk counted (the condition)
    did not consume it on every path, so the entry crossed a statement
    boundary and is a named local, not a temp. This is the half of the
    clamp/conditional-reassignment family rule B cannot see: the OLD
    definition (`SUB`/`MOVE`/`GETGLOBAL` staging the initial value) is killed
    by the then-arm's reassignment, and the walk happily pops it as consumed
    because the condition read it once.

    Narrow by construction: only writes that do not read the killed register
    (explicitly, or via an `R[a..top)` open range) can be kills this rule
    speaks about, and `stack_discipline` only asks it at its generic-write
    site -- operand-consumption pops (`ADD`'s operands, call arguments,
    `SETLIST` items) are exempt because the instruction reads what it pops.
    The `and`/`or` *condition* chains (`if a and b then`) do not fire either:
    their short-circuit jump lands where the branch decision was already
    taken, so the next mention of the slot is a fresh staging *write*, not a
    read. Being wrong here costs certifications, never correctness (the
    certification gate recompiles everything this grades).

    ## Why there is no symmetric "merge-read" rule (measured, then deleted)

    A second veto was built for the OTHER half of the family -- the arm's own
    redefinition (`LOADK`/`MOVE`), whose join read is reachable from before
    it -- and deleted the same day: promote-the-old-definition (this rule)
    plus `write_reg`'s "`declared` still wins" gate absorbs the whole family
    end to end. Once the old definition is a named local, the reconstructor
    has declared the slot, and every later write to it materializes as an
    assignment regardless of its temp grade, so the join read always has a
    name. Measured both ways (M7 task 7): with the merge-read veto neutered,
    all 1944 corpus occurrences certify identically (1909 `L3` both ways) and
    every synthetic carrier of the family certifies. The shapes it alone
    could catch -- a pending temp read at a pc reachable from before its own
    def, with the slot never declared -- real luac cannot produce, because an
    expression-stack temp never crosses a branch in the first place.
    """
    ri = kill_li.ri
    if reg in kill_li.effects.reads:
        return False
    if kill_li.effects.reads_open and reg >= (
            ri.a if ri.op is Op.RETURN else ri.a + 1):
        return False
    kill_pc = ri.pc
    # `jmp_list` is sorted and strictly increasing on pc (one instruction per
    # pc), so tuple bisection bounds "JMPs strictly between def and kill".
    lo = bisect.bisect_right(jmp_list, (def_pc, 1 << 30))
    hi = bisect.bisect_left(jmp_list, (kill_pc, 0))
    for k in range(lo, hi):
        j_pc, succ = jmp_list[k]
        if succ > kill_pc and _next_mention_is_read(
                reg, succ, reads_at, writes_at, open_reads):
            return True
    return False


def _next_mention_is_read(reg: int, from_pc: int,
                          reads_at: dict[int, list[int]],
                          writes_at: dict[int, list[int]],
                          open_reads: list[tuple[int, int]]) -> bool:
    """True iff `reg`'s first tracked mention at or after `from_pc` is a read
    (explicit, or an `R[a..top)` open read covering it) rather than a write.

    A write first means the taken path overwrites the slot before anyone sees
    the old value, so the kill the walk modelled was harmless on that path
    too and no veto is owed. Mentions are the per-register sorted lists built
    by `stack_discipline` in one pass; the lookups are bisections.

    A read at the SAME pc as the limiting write counts as a read: every
    opcode that both reads and writes a register reads the old value first
    (`ADD A=B=C` with A==B, `FORPREP`'s `R[A] -= R[A+2]`, a CALL overwriting
    its callee slot with the result) -- there is no write-then-read operand
    order in the 5.1 instruction set, so the tie resolves to "read".
    """
    wl = writes_at.get(reg, [])
    i = bisect.bisect_left(wl, from_pc)
    limit = wl[i] if i < len(wl) else None
    rl = reads_at.get(reg, [])
    j = bisect.bisect_left(rl, from_pc)
    if j < len(rl) and (limit is None or rl[j] <= limit):
        return True
    lo = bisect.bisect_left(open_reads, (from_pc, -1))
    hi = bisect.bisect_left(open_reads, (limit, -1)) if limit is not None \
        else len(open_reads)
    return any(base <= reg for _, base in open_reads[lo:hi])


@dataclass(slots=True)
class _Pending:
    """One pushed-but-unconsumed value on the simulated expression stack.

    `stack_discipline` keeps these in a list, reg-ascending. `bad` is set by a
    read this definition cannot legally be inlined into even though the read
    count is right (the barriers below); it is carried on the entry rather
    than applied immediately so that a single pop site stays the one place a
    verdict is recorded.
    """
    reg: int
    def_pc: int
    n_reads: int = 0
    bad: bool = False


# Hard cap on how far a staged value may reach across basic blocks (see
# `_staging_span_ok`). Real luac keeps one statement's expression window to a
# handful of instructions; a span past this bound is not a statement window
# but unrelated code the pc-linear walk is misreading, and the answer is the
# budget refusal -- materialize, the safe direction -- never an unbounded
# scan and never a silent sample.
_MAX_STAGING_SPAN = 256


@dataclass(frozen=True)
class _SpanView:
    """Jump-structure summary `_staging_span_ok` needs, built once per
    function by `build_span_view` (shared with `express/reconstruct.py`).

    `branches` is every instruction whose successors are not exactly the
    fall-through `(pc + 1,)` -- TEST/EQ/LT/LE, JMP, FORPREP, FORLOOP, TFORLOOP
    -- sorted by pc, with its successor tuple. `target_srcs` maps each branch
    target pc to the (min, max) pc of the branches targeting it.
    `up_moves` maps each upward `MOVE a, b` (a > b) pc to its source `b` --
    `luaK_exp2nextreg` copies a VLOCAL upward and never a temporary (a
    temporary already sits at freereg - 1), so such a MOVE is bytecode-level
    proof its source slot held a named local.
    """
    branches: list[tuple[int, tuple[int, ...]]]
    target_srcs: dict[int, tuple[int, int]]
    up_moves: dict[int, int]


def build_span_view(fn: LirFunction) -> _SpanView:
    branches: list[tuple[int, tuple[int, ...]]] = []
    target_srcs: dict[int, list[int]] = {}
    up_moves: dict[int, int] = {}
    for pc in sorted(fn.instrs):
        li = fn.instrs[pc]
        succs = li.successors
        if succs == (pc + 1,):
            if li.ri.op is Op.MOVE and li.ri.a > li.ri.b:
                up_moves[pc] = li.ri.b
            continue
        branches.append((pc, succs))
        for s in succs:
            target_srcs.setdefault(s, []).append(pc)
    return _SpanView(
        branches=branches,
        target_srcs={t: (min(srcs), max(srcs))
                     for t, srcs in target_srcs.items()},
        up_moves=up_moves)


def _staging_span_ok(view: _SpanView, d: int, r: int, *,
                     entry_at_r_ok: bool, read_reg: int | None = None) -> bool:
    """True iff a value defined at `d` may stay STAGED (inlined as an
    expression) at its read at `r` even though `d` and `r` sit in different
    basic blocks (M7 task 8, mechanism C).

    What the block boundary actually protects -- the two properties
    `_same_block`'s docstring proves -- is (1) execution counts: a read that
    runs a different number of times than its definition (loop bodies, loop
    exits) must not inline the definition's expression; and (2) scope
    isolation: a pop inside an `open_scope`/`close_scope` region is rolled
    back, dropping the block's statement. Both are properties of the JUMP
    STRUCTURE between `d` and `r`, and the four clauses below read them off
    it:

      * interior branches go FORWARD and land at or before `r` -- an `if`
        arm's exit jump, a loop header's skip-out and a FORPREP into a loop
        body all jump PAST a read inside those constructs, which is exactly
        the arm/loop shape the barrier must keep refusing;
      * no branch from OUTSIDE `[d, r)` targets strictly inside `(d, r]` --
        control that reaches the middle without passing `d` makes `r`'s read
        a phi of values this entry does not carry;
      * no branch with source at/after `r` targets at/before `d` -- that is
        a back edge enclosing the interval, i.e. `[d, r]` sits inside a loop
        (`repeat` bodies have no header skip-out, so the enclosure clause is
        what catches them);
      * the span fits `_MAX_STAGING_SPAN` -- the budget refusal.

    Purity is deliberately NOT asked. The original sketch for this rule
    demanded an effect-free interior under STRICT, but the corpus rows it
    exists for (`snr_graphic:main_2` et al.) stage a GETUPVAL callee across
    an LT/CONCAT chain -- impure under STRICT -- so that condition would
    unlock nothing; and the opposite direction (an unsound staging shipping
    wrong source) is certification's to catch, not this walk's: the printed
    text is recompiled and compared field by field, so a staging that
    misjudges costs an `L1`, never correctness. What the clauses above
    protect is the L3s that exist today via materialization -- a shape the
    exemption wrongly un-grades stops certifying and the ratchet sees it.

    A fifth clause refuses the one consumer shape that is bytecode-level
    PROOF the slot held a named local: `read_reg` is the register the
    consumer reads, and when the instruction at `r` is an upward `MOVE a, b`
    with `b == read_reg`, `luaK_exp2nextreg` was copying a VLOCAL into the
    expression stack -- a temporary is already at `freereg - 1` and never
    needs the copy (the same fact `_bar_literal_operands`'s MOVE rule keys
    on, read from the consumer side). Staging such a slot drops its `local`
    declaration and shifts every later register (`local a = b or c
    print(a)` recompiles with `a`'s slot never allocated). Both the walk
    (`_same_block`) and the region path (`cond_value`) pass `read_reg`; the
    clause is what keeps the exemption from overriding a local verdict the
    bytecode itself carries.

    `entry_at_r_ok` is the region-computed-merge variant (the only caller:
    `express/reconstruct.py::cond_value`, for a `CondValue` chain's result).
    There the "definition" is the whole short-circuit expression, which
    already merges every path through the chain, so a branch landing exactly
    ON `r` is not an outside entry but the join the expression subsumes;
    clause two then excludes only targets strictly inside `(d, r)`. `d` for
    that caller is the chain's CONVERGENCE pc (see `_cond_value_stages`), and
    `r == d` is allowed: the empty interior is trivially free of hazards --
    it is the `g(a and 1 or 2)` shape, where the consuming call sits exactly
    on the join.
    """
    if r < d or r - d > _MAX_STAGING_SPAN:
        return False
    if read_reg is not None and view.up_moves.get(r) == read_reg:
        return False
    branches = view.branches
    lo = bisect.bisect_right(branches, (d, (1 << 30,)))
    hi = bisect.bisect_left(branches, (r, ()))
    for k in range(lo, hi):
        pc, succs = branches[k]
        if not all(pc < s <= r for s in succs):
            return False
    tgt_hi = r if entry_at_r_ok else r + 1
    for t, (mn, mx) in view.target_srcs.items():
        if d < t < tgt_hi and (mn < d or mx > r):
            return False
    for pc, succs in branches:
        if pc >= r and any(s <= d for s in succs):
            return False
    return True


def _pending_def(pending: list[_Pending], r: int) -> _Pending | None:
    """The entry `pending` holds for register `r`, or None."""
    for ent in pending:
        if ent.reg == r:
            return ent
    return None


# --------------------------------------------------------------------------
# The four barriers on top of the pop-once rule
# --------------------------------------------------------------------------
# `docs/runbooks/structured-pipeline.md` documents these four as one group
# under this heading, so they live under it here too. Three of them are
# state-independent questions about what `lcode.c` would have emitted and are
# free functions below: barrier 1 is `_same_block`; barriers 2 (RK/literal)
# and 3 (`MOVE d, s` with `s < d`) share `_bar_literal_operands`, because both
# are "this operand position proves the slot did not hold a temporary" and
# both need the same lookup into the pending stack.
#
# Barrier 4 -- read-poisoning blames the last definition -- is NOT here, and
# that is a judgement rather than an impossibility. It is two lines inside
# `stack_discipline`'s `do_read` that read the walk's `last_def` and write its
# `def_verdict`; a `_bar_read_poison(last_def, mark_def, r)` up here would
# work. Two lines behind a call, with two pieces of walk state threaded
# through the signature to get there, is indirection with no second reader, so
# it stays in place and is marked there instead. Its neuter proof does not
# live with the other three either; see that comment.
#
# `_constructor_field_target` below is NOT a fifth barrier: the four above all
# *disqualify* a definition that the pop-once count would have accepted, and
# it does the opposite -- it declines to count a read that was never a
# consumption in `lparser.c` to begin with, so it can only ever let more
# definitions through. It lives in this section because it is the same kind of
# object (a state-independent question about what `lparser.c` emits, answered
# by looking at one instruction and the pending stack) and because a reader
# auditing the read-counting rules needs to find all of them in one place.


def _same_block(block_floor: Callable[[int], int], d: int, r: int,
                span: _SpanView | None = None,
                read_reg: int | None = None) -> bool:
    """True iff pcs `d` and `r` are in the same CFG basic block.

    Barrier 1 of the four (see the section header), and THE control-flow
    requirement on per-definition staging. A staged definition is not a
    statement: it lives only in the reconstructor's register environment until
    a read pops and inlines it. Two things follow, and both are violated as
    soon as a definition and its read sit in different blocks.

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

    ## The staging-span exemption (M7 task 8, mechanism C)

    `span` (built by `build_span_view`, passed by `stack_discipline`) lets a
    definition in one block stage for a read in another when the jump
    structure between them carries neither hazard: all interior branches
    forward and at-or-before the read, no outside branch into the interval,
    no back edge enclosing it, span within the budget -- `_staging_span_ok`
    carries the clause-by-clause argument. That is the shape of luac's
    `and`/`or` VALUE idiom in operand position (`g(a and 1 or 2)`: callee
    staged at the head, chain's joins and the consuming call in later
    blocks), which the strict form forced to materialize `local` -- the
    extra `MOVE`s of copying a materialized callee back into call position
    then failed certification on `maxstacksize`. The exemption fires from
    the read side (`do_read`/`read_open`), so a hand-built caller without a
    `span` keeps the pre-task-8 behaviour exactly.
    """
    if block_floor(d) == block_floor(r):
        return True
    return span is not None and _staging_span_ok(span, d, r,
                                                  entry_at_r_ok=False,
                                                  read_reg=read_reg)


def _renders_as_literal(fn: LirFunction, def_pc: int) -> bool:
    """True iff the definition at `def_pc` would be printed as a Lua *literal*
    (`1`, `"s"`, `nil`, `true`) rather than as a name or a compound
    expression -- i.e. iff `lparser.c` would read it back as VKNUM/VK/
    VNIL/VTRUE/VFALSE.
    """
    d = fn.instrs[def_pc].ri
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


def _bar_literal_operands(fn: LirFunction, li: LirInstr,
                          pending: list[_Pending]) -> None:
    """Disqualify pending definitions that this instruction reads in a
    position where luac would never have used a register at all.

    Barriers 2 AND 3 of the four (see the section header): they are one
    function because both ask the same shape of question about an operand
    position and both need the same lookup into `pending`. Barrier 3, the
    `MOVE d, s` rule, is the `if ri.op is Op.MOVE` block in the body and is
    documented there; the rest of this docstring is barrier 2.

    Two ways barrier 2 happens, both of them in `lcode.c`:

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
        # BARRIER 3. `MOVE d, s` with `s < d` proves `s` held a NAMED LOCAL,
        # not a temporary. `luaK_exp2nextreg` runs `freeexp` first, and
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
        ent = _pending_def(pending, ri.b)
        if ent is not None:
            ent.bad = True
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
        ent = _pending_def(pending, r)
        if ent is not None and _renders_as_literal(fn, ent.def_pc):
            ent.bad = True


def _bar_key_staged_below_table(li: LirInstr,
                                pending: list[_Pending]) -> None:
    """BARRIER 5 (M7 task 10): a register-keyed index whose KEY is staged
    BELOW its table was never an inline `t[k]` -- grade the key local.

    `lparser.c`'s every route to a register-keyed `GETTABLE`/`SETTABLE`
    discharges the TABLE prefix to a register first and parses the key
    after (`prefixexp`'s `[` arm: `luaK_exp2anyreg(fs, v)` then `yindex`;
    assignment targets go through the same `prefixexp`; constructor fields
    store into a table whose base register predates every field). So in
    bytecode produced by stock 5.1.5 from `prefix[key_expr]`, the key's
    defining instructions sit strictly AFTER the table's, and the key
    occupies a HIGHER register. The contrapositive is the barrier: when the
    key's pending definition predates the table's, the source cannot have
    been `prefix[key_expr]` -- the author materialized the key first, as
    its own named local:

        local k = sceneId2aCard.s3s_300_sel    -- key code at pc P
        ... = prefix[k].suffix                 -- table code at pc > P

    Measured shape (`snr_s3_10_s.lua:main_59`, pcs 745-749): GETGLOBAL/GETTABLE
    stage the key into R2, then GETGLOBAL/GETTABLE build the prefix into R3,
    then `GETTABLE 3 3 2` indexes by register. Without this barrier the key
    definition grades temp (single read), the reconstructor inlines it into
    the index, and the recompiled instruction stream inverts the two staging
    orders -- `mismatch: code`, same length, no semantic change (the
    certification gate, as always, is what kept that from shipping).

    Fires only when BOTH operands are pending (freshly staged, neither a
    known local): a named-local table with a fresh key is the ordinary
    `t_local[f(x)]` shape and must keep staging the key, and a named-local
    key under a fresh table is the ordinary `t[k_local]`. The register-equal
    case (`t[t]`) is excluded by the strict `<`.
    """
    ri = li.ri
    if ri.op is Op.GETTABLE:
        table_reg, key = ri.b, ri.c
    elif ri.op is Op.SETTABLE:
        table_reg, key = ri.a, ri.b
    else:
        return
    if isk(key):
        return                                  # constant key: no staging order
    key_ent = table_ent = None
    for ent in pending:
        if ent.reg == key:
            key_ent = ent
        elif ent.reg == table_reg:
            table_ent = ent
    if key_ent is not None and table_ent is not None \
            and key_ent.def_pc < table_ent.def_pc:
        key_ent.bad = True


def _constructor_field_target(fn: LirFunction, li: LirInstr,
                              pending: list[_Pending]) -> int | None:
    """The register this instruction reads *without consuming it*, or None.

    `SETTABLE`/`SETLIST` emitted by a **table constructor** read the table's
    own slot, and that read is not a use of the value. The two field forms
    restore `freereg` in two different files, and the citations are given
    separately because a reader who follows only the `lparser.c` one will not
    find the `SETLIST` half at all (round-1 review: this docstring's first
    version cited `lparser.c:596`/`:632`, which are inside `explist1` and
    `funcargs` -- the wrong functions entirely):

    * **hash field** -- `lparser.c::recfield` (`vendor/lua-5.1/src/lparser.c
      :443`) saves `int reg = ls->fs->freereg` on entry, pushes the key and
      value above the table, emits `luaK_codeABC(fs, OP_SETTABLE,
      cc->t->u.s.info, rkkey, ...)`, and restores `fs->freereg = reg;` at
      **`:460`**.
    * **array field** -- `lparser.c::closelistfield` (`:464`) and
      `lastlistfield` (`:475`) do NOT restore it themselves; they delegate to
      `luaK_setlist`, and the restore is in `lcode.c` --
      `vendor/lua-5.1/src/lcode.c:819` `luaK_setlist`, with
      `fs->freereg = base + 1;` at **`:829`**.

    Either way the table's own slot survives the store: the value stays on the
    expression stack, still unfinished, until whatever the literal is an
    operand of takes it. So a field store must not spend the one read the
    pop-once rule allows -- with N fields the table scored N + 1 reads and was
    graded a local, which is precisely backwards for `f({x = 1})`.

    `stack_discipline` already models the write half of exactly this
    (`SETTABLE`/`SETLIST` do `pop_ge(a + 1)`, "the table itself stays
    pending"); this is the read half of the same sentence.

    ## Why the discriminator is `OP_NEWTABLE`

    A `SETTABLE` is *also* how an assignment statement `v.k = e` stores, and
    there the target expression genuinely is consumed: `a().b = 1` leaves
    `a()`'s result on the stack precisely so the `SETTABLE` can take it, and
    `luaK_storevar` frees it. The two are told apart by what pushed the slot.
    Only a constructor's table is pushed by `OP_NEWTABLE`, and `lparser.c`
    emits `OP_NEWTABLE` from exactly one place (`constructor`), so "the most
    recent push into this slot was a `NEWTABLE`" is the same question as "this
    store is a field of a live constructor". It is also the same test
    `express/reconstruct.py::_dispatch` uses to decide whether to fold the
    store into a `TableExpr` (`self._table_ctx_stack[-1]["reg"] == a`), so the
    classification and the reconstruction agree by construction rather than by
    coincidence.

    ## Why the fold and this exemption must move together

    `_dispatch`'s fold is `op is Op.SETTABLE and a == reg` (keys constant OR
    register: `_fold_settable` builds `ConstExpr` keys from `isk(B)` and
    register keys from `_read_reg(ri.b)`). Until M7 task 6 the fold demanded
    `isk(ri.b)`, and this exemption demanded it too -- a **dynamic-key**
    constructor (`{[f] = 1, [g] = 2}`, `config.lua`'s main chunk) did not
    fold, the reconstructor materialized the table and emitted each field as
    its own `t[k] = v` statement, which reads the table once per field for
    real; exempting those reads back then told the classifier the table was
    a pop-once temporary, the reconstructor popped it at the first field and
    raised `register 0 is read again after its staged value was consumed` at
    the second. The two conditions therefore agree BY CONSTRUCTION -- the
    docstring's own invariant -- and M7 task 6 changed both in the same
    commit: the fold takes register keys, and the exemption follows. The
    corpus evidence for the pair is `config.lua` flipping whole-file from
    `mismatch: maxstacksize` to `L3`.

    The `c` check keeps the exemption from swallowing a store that reads the
    table in the *value* position too (`t[k] = t`). A constructor cannot
    produce that shape -- its values live above the table -- so declining the
    exemption there costs nothing and keeps the rule's statement true as
    written. **DEFENSIVE, not load-bearing:** measured over the corpus,
    **0** of 1944 protos contain a `SETTABLE` with a register `C` equal to
    `A`, so nothing here currently depends on it. Kept because the sentence
    above ("the exemption applies to the table's own slot") is only true as
    written with it, not because a fixture fails without it.

    Being wrong in either direction costs certifications, never correctness:
    the printed source is recompiled and compared field by field before
    anything ships.
    """
    ri = li.ri
    if ri.op is Op.SETTABLE:
        if not isk(ri.c) and ri.c == ri.a:
            return None
    elif ri.op is not Op.SETLIST:
        return None
    ent = _pending_def(pending, ri.a)
    if ent is None or fn.instrs[ent.def_pc].ri.op is not Op.NEWTABLE:
        return None
    return ri.a


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
    # `block_floor` is `classify_registers._block_floor`: the first pc of the
    # basic block containing a pc. It is required, not defaulted -- a default
    # would have to be either "everything is one block" (silently unsound: it
    # turns _same_block into a tautology) or an eager `build_cfg` (which a
    # hand-built LirFunction whose successors point past its own last
    # instruction cannot survive). Passing the caller's lazy one gets both:
    # sound, and no CFG is built for a function whose staging never crosses a
    # block boundary.
    pending: list[_Pending] = []
    verdict: dict[int, bool] = {}
    def_verdict: dict[tuple[int, int], bool] = {}
    last_def: dict[int, int] = {}           # reg -> pc of its most recent push

    # The skipped-kill veto (M7 task 7) needs jump and per-register mention
    # tables. Built in one pass over the same `ordered` walk below -- the
    # lists are pc-ascending by construction, which the bisections in the
    # veto helper rely on.
    jmp_list: list[tuple[int, int]] = []    # (pc, successor) per JMP
    span_view = build_span_view(fn)         # M7 task 8: _same_block's exemption
    reads_at: dict[int, list[int]] = {}     # reg -> its read pcs
    writes_at: dict[int, list[int]] = {}    # reg -> its write pcs
    open_reads: list[tuple[int, int]] = []  # (pc, base) per R[a..top) read
    for pc in ordered:
        li0 = fn.instrs[pc]
        ri0 = li0.ri
        if ri0.op is Op.JMP:
            jmp_list.append((pc, li0.successors[0]))
        for r in li0.effects.reads:
            reads_at.setdefault(r, []).append(pc)
        for r in li0.effects.writes:
            writes_at.setdefault(r, []).append(pc)
        if li0.effects.reads_open:
            open_reads.append((pc, ri0.a if ri0.op is Op.RETURN
                               else ri0.a + 1))

    def mark(reg: int, ok: bool) -> None:
        verdict[reg] = verdict.get(reg, True) and ok

    def mark_def(pc: int, reg: int, ok: bool) -> None:
        key = (pc, reg)
        def_verdict[key] = def_verdict.get(key, True) and ok

    def do_read(r: int, at: int, count: bool = True) -> None:
        for ent in pending:
            if ent.reg == r:
                # `count=False` is a live constructor reading its own table
                # slot to store a field (`_constructor_field_target`): a read
                # in the instruction stream that is not a *use* of the value.
                # The block check still applies -- a constructor and its field
                # stores are straight-line code, so a store in another block
                # means this is not the shape the exemption describes, and
                # `bad` drives the answer to `local`, the safe direction.
                if count:
                    ent.n_reads += 1
                if not _same_block(block_floor, ent.def_pc, at,
                                     span=span_view, read_reg=r):
                    ent.bad = True
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
            # BARRIER 4 of the four (see the section header above; the other
            # three are module-level functions). Per-definition, blame the
            # definition that produced the value being re-read -- the most
            # recent push into this slot, which the walk has already popped.
            # Grading THAT def local is what makes the reconstructor
            # materialize it as a named local, so the second read has a name
            # to refer to instead of an expression that was already inlined
            # somewhere else. A slot with no preceding def in this function
            # (an uninitialised read) has nothing to blame and simply
            # contributes no `temp_defs` entry, which is the local direction
            # anyway.
            #
            # Neuter proof, measured 2026-08-13 (M5 task 11, corrected in
            # round 1) by replacing the `if` below with `if False and ...`,
            # regenerating the ledger, and running the whole suite: 3 of 1944
            # corpus protos reclassify, `corpus/ledger.jsonl` moves by 2 lines
            # with no level change, and exactly two tests fail --
            # `tests/test_sir_loops_longtail.py::
            # test_repeat_fixture_claims_every_pc_and_certifies[6]` and
            # `tests/test_ledger_ratchet.py::
            # test_ledger_is_a_reproducible_fixed_point`.
            #
            # What is worth knowing is where that pin is NOT: nothing in
            # `tests/test_express_*.py` sees this line at all (126/126 of
            # those still pass with it neutered), so the runbook's "each is
            # pinned by a fixture ... (see tests/test_express_liverange.py)"
            # is true of barriers 1-3 only.
            #
            # This note's first version (commit `f99f307`) also called this
            # the only barrier whose absence moves the ledger. That was never
            # measured and is FALSE. Per-barrier, neutered one at a time and
            # the ledger regenerated each time: `_same_block` reclassifies 28
            # protos and moves 9 ledger lines, the `MOVE d, s` rule 3 protos
            # and 2 lines, this one 3 protos and 2 lines. The odd one out is
            # `_bar_literal_operands`' literal test, which reclassifies **0**
            # of 1944 -- the barrier the corpus genuinely cannot see, and the
            # one whose entire evidence is synthetic fixtures.
            if r in last_def:
                mark_def(last_def[r], r, False)

    def read_open(base: int, at: int) -> None:
        """An `R[base..top)` read (CALL/TAILCALL B==0, RETURN B==0, SETLIST
        B==0) consumes every pending value from `base` upwards. Counting
        those reads is what lets `print(string.format(...))` keep its two
        staged argument registers as temps."""
        for ent in pending:
            if ent.reg >= base:
                ent.n_reads += 1
                if not _same_block(block_floor, ent.def_pc, at,
                                   span=span_view, read_reg=ent.reg):
                    ent.bad = True

    def pop_ge(base: int, kill: LirInstr | None = None) -> None:
        while pending and pending[-1].reg >= base:
            ent = pending.pop()
            ok = ent.n_reads == 1 and not ent.bad
            if ok and kill is not None and _merge_veto_skipped_kill(
                    ent.reg, ent.def_pc, kill, jmp_list, reads_at,
                    writes_at, open_reads):
                # Skipped-kill veto (M7 task 7): a branch jumps past this
                # kill to a read of the slot, so the value is live on that
                # path and the definition is a named local. Only the generic
                # -write site below passes `kill`; every other pop is an
                # operand consumption or a statement boundary and keeps the
                # None default.
                ent.bad = True
                ok = False
            mark(ent.reg, ok)
            mark_def(ent.def_pc, ent.reg, ok)

    def promote_all() -> None:
        while pending:
            ent = pending.pop()
            mark(ent.reg, False)
            mark_def(ent.def_pc, ent.reg, False)

    def push(regs: Iterable[int], pc: int) -> None:
        for r in regs:
            if not known_local(r, pc):
                pending.append(_Pending(r, pc))
                last_def[r] = pc

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

        _bar_literal_operands(fn, li, pending)
        _bar_key_staged_below_table(li, pending)
        uncounted = _constructor_field_target(fn, li, pending)
        for r in sorted(li.effects.reads):
            do_read(r, pc, count=r != uncounted)
        if li.effects.reads_open:
            read_open(a if op is Op.RETURN else a + 1, pc)

        if op in (Op.CALL, Op.TAILCALL):
            pop_ge(a)
            if op is Op.TAILCALL or c == 1:
                promote_all()                      # call statement / tail return
            elif c == 0:
                push((a,), pc)                     # open producer
            else:
                push(range(a, a + c - 1), pc)
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
                pop_ge(a); push((a,), pc)
            elif b >= 2:
                pop_ge(a); push(range(a, a + b - 1), pc)
        else:
            writes = sorted(li.effects.writes)
            if writes:
                pop_ge(writes[0], kill=li)
                if named_local(writes[0], pc):
                    promote_all()                  # assignment to a named local
                else:
                    push(writes, pc)
    promote_all()
    return ({r for r, ok in verdict.items() if ok},
            {key for key, ok in def_verdict.items() if ok})

"""Dominator-driven region identification (spec §3 ③). Acyclic subset: Straight / Seq / If.

Discipline: recognize or raise StructureError — never emit a guessed structure.
The pc-claim audit (all_claimed == fn pcs) is asserted at every build_sir exit.
"""
from __future__ import annotations

from pyluadec.cfg import build_cfg, dominates, immediate_dominators
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import Op

from .regions import (Break, EndIter, GenericFor, If, NumericFor, Region,
                      RegionOverlap, Repeat, Return, Seq, Straight, While,
                      WhileTrue, all_claimed, _own_enditers, _tail_enditers)

_COMPARE = frozenset({Op.EQ, Op.LT, Op.LE, Op.TEST})
# TESTSET is deliberately NOT an if-condition: it is the and/or VALUE idiom
# (assigns on one branch). Reconstructing it is M4; in M3 a TESTSET reaches the
# unrecognized-transfer check (it has two successors) and the function falls back.
# Corpus impact: 16/1478 unique protos (1.1%).


class StructureError(Exception):
    pass


def has_back_edge(fn: LirFunction) -> bool:
    for pc, li in fn.instrs.items():
        for s in li.successors:
            if s <= pc:
                return True
    return False


def _pc_block_map(cfg) -> dict[int, int]:
    """Every instruction pc -> the start pc of the CFG block containing it."""
    m: dict[int, int] = {}
    for start, b in cfg.blocks.items():
        for li in b.instrs:
            m[li.ri.pc] = start
    return m


def _jmp_sites(fn: LirFunction) -> dict[int, tuple[int, ...]]:
    """target pc -> the pcs of the unconditional JMPs that target it.

    Computed once per `build_sir` and threaded down, so the loop-header test
    at every dispatch position is a dict lookup rather than a rescan of the
    range (which would make structuring quadratic in the function's length).
    """
    out: dict[int, list[int]] = {}
    for pc, li in fn.instrs.items():
        if li.ri.op is Op.JMP and len(li.successors) == 1:
            out.setdefault(li.successors[0], []).append(pc)
    return {k: tuple(sorted(v)) for k, v in out.items()}


def _verify_single_entry(cfg, idoms, pc2blk, cond_pc: int, lo: int, hi: int,
                         *, allow_unreachable: bool = False) -> None:
    """Refuse unless every CFG block starting in pc range [lo, hi) is dominated by
    the block containing cond_pc.

    This is the check the pc-interval arithmetic in _structure_range/_structure_if
    cannot do on its own: two disjoint, gap-free pc ranges can still each be
    reachable from outside the branch that "claims" them (e.g. a jump from
    earlier code straight into the middle of what looks like a then-body). The
    pc-claim audit at build_sir's exit only checks that pcs partition cleanly;
    it does not check *how* a block became reachable. A block absent from
    `idoms` is unreachable from the function entry per Cooper-Harvey-Kennedy's
    definition (idoms is keyed by the reachable set) -- refuse rather than
    assume that's harmless, since an unreachable block inside a claimed range
    is itself a sign the interval doesn't mean what we think it does.

    `allow_unreachable` (loop bodies only, M4 task 1): an unreachable block
    has no predecessor reachable from the function entry, so it cannot be an
    alternate *entry* into the region -- it is dead code that the pc-claim
    audit nonetheless requires somebody to claim. Refusing it is the right
    conservative choice for if/for bodies (luac emits no dead code there) but
    wrong for a `while true` body: luac emits a closing JMP for every such
    loop even when every path through the body breaks or returns, which makes
    that JMP unreachable, and when the loop is nested the dead JMP lands
    inside the ENCLOSING loop's body -- refusing it there would make the
    nested shape unrecognizable. The dominance requirement below still holds
    for every reachable block, which is what single-entry actually means.
    """
    cond_block = pc2blk[cond_pc]
    for start in cfg.blocks:
        if not (lo <= start < hi):
            continue
        if start not in idoms:
            if allow_unreachable:
                continue
            raise StructureError(
                f"pc {cond_pc}: branch body block at pc {start} is unreachable")
        if not dominates(idoms, cond_block, start):
            raise StructureError(
                f"pc {cond_pc}: branch body block at pc {start} is not dominated by "
                "the condition block (multi-entry branch)")


def build_sir(fn: LirFunction) -> Region:
    # No blanket has_back_edge early-exit: back edges are now recognized as
    # numeric-for / generic-for loops where the FORPREP/TFORLOOP+JMP shape
    # proves it, and refused (StructureError) everywhere else -- while,
    # repeat, and any back edge _structure_range cannot claim as a for loop
    # still fall back. has_back_edge itself stays exported for callers/tests
    # that want a cheap pre-check without paying for full structuring.
    cfg = build_cfg(fn)
    idoms = immediate_dominators(cfg)
    pc2blk = _pc_block_map(cfg)
    ordered = sorted(fn.instrs)
    try:
        region = _structure_range(fn, cfg, idoms, pc2blk, ordered[0], ordered[-1] + 1)
    except RegionOverlap as e:
        raise StructureError(str(e)) from e
    claimed = all_claimed(region)
    if claimed != set(fn.instrs):
        missing = set(fn.instrs) - claimed
        raise StructureError(f"pc-claim audit failed; unclaimed {sorted(missing)}")
    return region


def _exits_only_to(fn, lo: int, S: int, allow: tuple[int, ...] = ()) -> bool:
    """True iff no instruction in [lo, S] transfers control out of the loop
    except to S+1 (the `break` target / the loop's own fall-through exit) or
    to one of `allow`.

    A jump to a RETURN/TAILCALL beyond S+1 is tolerated here because luac
    threads `break` straight onto a following return when one is there; such
    a jump is still refused later by `_structure_range` (it matches neither
    break_target nor continue_target), so tolerating it costs no acceptance
    -- it only keeps this pre-filter from being the thing that reports it.

    `allow` carries the ENCLOSING loop's header (`continue_target`) when there
    is one: luac threads a nested loop's own false-exit onto the enclosing
    loop's closing JMP and thence to that header, so `while a do while b do
    c() end end` really does contain a jump out of the inner loop that lands
    on the outer header (measured 2026-08-11: pc 6 -> pc 1). Refusing it here
    would make every nested `while <cond>` unrecognizable. It costs no
    soundness: the body structuring below is the actual validator, and it
    still refuses any such jump that is not in tail position.
    """
    for p in range(lo, S + 1):
        li = fn.instrs.get(p)
        if li is None:                      # a pc consumed as a pseudo-instruction
            continue
        for t in li.successors:
            if lo <= t <= S + 1 or t in allow:
                continue
            tgt = fn.instrs.get(t)
            if tgt is not None and tgt.ri.op in (Op.RETURN, Op.TAILCALL):
                continue
            return False
    return True


def _match_while_header(fn, pc2blk, lo: int, S: int, hi: int,
                        continue_target: int | None):
    """The header half of `while <cond> do ... end` recognition.

    Given a candidate loop header `lo` and closing back edge `S`, decide
    whether `[lo, S)` opens with luac's `whilestat` layout:

        lo .. C-1   straight-line condition-operand code (may be empty)
        C           <compare / TEST>
        C+1         JMP -> E, the false-exit
        C+2 .. S-1  body
        S           JMP -> lo

    Returns `(header instrs, header pcs, C, C+1, E)` or None. Never raises.

    Two proofs are required beyond the opcode pattern:

    * **E == S+1.** The false-exit must land exactly on the loop's own
      fall-through exit. Anything else is a different shape (a compare whose
      exit stays inside the loop, e.g. an `if` in the header position) and
      must be left for the other recognizers, or refused.
    * **The header is one basic block.** Every pc in `[lo, C]` must live in
      `lo`'s CFG block. `build_cfg` makes every jump target a block leader,
      so this is exactly "nothing jumps into the middle of the condition
      code" -- the condition re-executes as a unit on every iteration, and a
      second entry point inside it would mean the pcs do not form a Lua
      `while` header at all. It also rules out a nested loop header hiding
      inside the run.

    `continue_target` handles the same `jpc` threading `_structure_if`
    documents: when this loop is the last statement of an enclosing loop's
    body, luac never patches this false-exit to a pc of its own -- it stays
    pending and is concatenated onto the enclosing loop's closing JMP, so it
    surfaces as a jump to the ENCLOSING header. Its source-level destination
    is "the end of the enclosing body", which inside this range is `hi`.
    """
    header: list = []
    header_pcs: list[int] = []
    pc = lo
    while pc < S:
        li = fn.instrs[pc]
        if li.ri.op in _COMPARE:
            break
        if len(li.successors) != 1 or li.successors[0] != pc + 1 + len(li.consumed):
            return None                      # not straight-line: not a header
        header.append(li)
        header_pcs.append(pc)
        pc += 1 + len(li.consumed)
    else:
        return None                          # no condition test before the back edge
    cond_pc = pc
    jmp_pc = cond_pc + 1
    if jmp_pc >= S or jmp_pc not in fn.instrs or fn.instrs[jmp_pc].ri.op is not Op.JMP:
        return None
    exit_pc = fn.instrs[jmp_pc].successors[0]
    if continue_target is not None and exit_pc == continue_target:
        exit_pc = hi
    if exit_pc != S + 1:
        return None
    header_blk = pc2blk[lo]
    if any(pc2blk[p] != header_blk for p in header_pcs + [cond_pc]):
        return None                          # something jumps into the condition
    return tuple(header), tuple(header_pcs), cond_pc, jmp_pc, exit_pc


def _match_while(fn, cfg, idoms, pc2blk, sites, memo, lo: int, hi: int,
                 break_target: int | None, continue_target: int | None):
    """Recognize `while <cond> do ... end` opening at range position `lo`.

    Returns `(While region, next pc)` or None; never raises, exactly like
    `_match_while_true` (a shape it cannot prove is simply not this loop, and
    the caller goes on to the other recognizers and ultimately refuses).

    Tried BEFORE `_match_while_true`, and the order is load-bearing. Once
    `_structure_if` recognizes "the compare's own jump targets `break_target`"
    (finding (A), M4 task 3), `_match_while_true` would also happily accept a
    `while <cond>` loop -- as `while true do ... if c then <body> else break
    end ... end`. That is semantically correct and it CANNOT certify: it
    recompiles to three instructions where the original has two (see
    `regions.While`). Recognizing the real shape first is what keeps the
    desugaring from being what ships. `_match_while_true` is left reachable
    as the fall-back for the shapes it genuinely owns.

    The header/dominance obligations are `_match_while_true`'s, unchanged:
    at least one JMP targeting `lo` must live in a block `lo`'s block
    dominates (pc-retreating alone is not a back edge), and the chosen
    closing JMP `S` must itself be unreachable or dominated by the header.
    The rest is `_match_while_header`'s, and the body structuring is the
    validator: no region is published until the body structures and claims
    exactly `[C+2, S)`.

    Unlike `_match_while_true`, only ONE candidate is ever tried: the LAST
    JMP-to-`lo` in range. That is not an optimization, it is the correctness
    condition. Every jump back to `lo` is by definition inside `lo`'s loop,
    so the closing JMP -- the loop's lexically last instruction -- is the
    last of them; a candidate with another back edge after it would be
    claiming a loop that demonstrably continues past its own `end`. Measured
    (M4 task 3, before this restriction): trying candidates last-first the
    way `_match_while_true` does made `while true do if f() then g() else
    h() end end` match as a `While` -- the `if`'s else-skip JMP@7 -> 1 read
    as a closing back edge and its false-exit JMP@4 -> 8 as an exit to
    S+1 == 8 -- silently amputating the else block, which then refused as an
    unrecognized transfer. `while true` loops CAN share a header (see
    `_match_while_true`); two `while <cond>` loops cannot, because each emits
    its own condition code at its own header.

    One relaxation of `_match_while_true`'s dominance precondition: a
    candidate whose block is UNREACHABLE also counts as evidence that `lo` is
    a header. luac emits a closing JMP for every loop even when every path
    through the body returns (`while a do f() return end`), and that JMP is
    then the loop's only back edge AND dead, so requiring a dominating one
    would make the shape unrecognizable. It cannot reintroduce the false
    positive the precondition exists for -- a rotated generic-for re-enters
    its body through a jump that is very much reachable. Measured: +0 corpus
    protos (the corpus has no such shape); `while a do f() return end` goes
    L1 -> L3.
    """
    cands = [s for s in sites.get(lo, ()) if lo <= s < hi]
    if not cands:
        return None
    header_blk = pc2blk[lo]
    if not any(dominates(idoms, header_blk, pc2blk[s]) or pc2blk[s] not in idoms
               for s in cands):
        return None                          # pc-retreating, but not a back edge
    allow = (continue_target,) if continue_target is not None else ()
    S = max(cands)
    s_blk = pc2blk[S]
    if s_blk in idoms and not dominates(idoms, header_blk, s_blk):
        return None                          # reachable from outside the loop
    m = _match_while_header(fn, pc2blk, lo, S, hi, continue_target)
    if m is None:
        return None
    header, header_pcs, cond_pc, jmp_pc, exit_pc = m
    if not _exits_only_to(fn, lo, S, allow=allow):
        return None
    body_lo = jmp_pc + 1
    try:
        _verify_single_entry(cfg, idoms, pc2blk, cond_pc, body_lo, S,
                             allow_unreachable=True)
        body = _structure_range(fn, cfg, idoms, pc2blk, body_lo, S,
                                break_target=exit_pc, continue_target=lo,
                                sites=sites, memo=memo) if body_lo < S \
            else Seq((), frozenset())
        if all_claimed(body) != {p for p in fn.instrs if body_lo <= p < S}:
            return None                      # under/over-claimed: not this shape
        if _own_enditers(body):
            # STRICTER than `_match_while_true`'s tail-position rule, and the
            # asymmetry is deliberate. An `EndIter` prints as nothing, which
            # is semantically faithful in tail position but always recompiles
            # one JMP SHORT (measured, M4 task 2: 9 of 9 generated shapes that
            # produce one run byte-identically and certify L1 on `code` --
            # luac re-threads a `break` and an `if`'s else-skip onto the same
            # header via `luaK_jump`'s jpc concat, and a source with only the
            # fall-through collapses them). `_match_while` is tried FIRST, so
            # accepting such a body here would PREEMPT readings that can
            # certify: measured on `while true do while true do if a then f()
            # else break end end end`, which certified L3 as a `WhileTrue` +
            # `If` in task 2 and would have dropped to L1 as a `While` whose
            # body ends in an EndIter. `_match_while_true` is the last
            # recognizer standing and preempts nothing, so it keeps the weaker
            # rule (its tail-position guard, which is about not dropping a
            # jump at all).
            return None
    except (StructureError, RegionOverlap):
        return None
    return (While(header=header, cond=fn.instrs[cond_pc],
                  negated=(fn.instrs[cond_pc].ri.a == 0), body=body,
                  closing=fn.instrs[S],
                  claimed_pcs=frozenset(header_pcs)
                  | {cond_pc, jmp_pc, S}), exit_pc)


def _match_repeat(fn, cfg, idoms, pc2blk, sites, memo, lo: int, hi: int,
                  break_target: int | None, continue_target: int | None):
    """Recognize `repeat <body> until <cond>` opening at range position `lo`.

    Returns `(Repeat region, next pc)` or None; never raises.

    luac's layout (`lparser.c:repeatstat`, lines 1019-1032) is the mirror of
    `whilestat`'s -- the condition lives at the BOTTOM and its jump goes
    backwards:

        lo .. S-2:  body
        S-1:        <compare / TEST>    -- the `until` condition
        S:          JMP -> lo           -- taken when the condition is FALSE
        S+1:        the loop's exit

    `repeatstat` calls `cond()` (which is `luaK_goiftrue`, yielding the jump
    taken when the source condition is FALSE) and patches THAT list back to
    `repeat_init`. So the backward JMP fires while `until <cond>` is false and
    falling through past it leaves the loop -- which is why `emit.lua`'s
    printer renders the un-negated fall-through expression after `until` and
    does not consult `Repeat.negated`. Same convention preserved here.

    The header proof is the same as the other two loop recognizers'
    (dominance, not pc order) and, as in `_match_while`, only the LAST
    JMP-to-`lo` in range is a candidate: every jump back to `lo` is inside
    `lo`'s loop, so the loop's lexically last instruction is the last of them.

    `continue_target` is deliberately NOT threaded into the body. A `repeat`
    has no instruction after its body that a pending jump could be
    concatenated onto -- the condition's own code is emitted next, and
    `luaK_code` flushes the pending list to that code's pc (see
    `_structure_if`'s lcode.c citation). So a bare JMP to `lo` from inside the
    body would be a shape this recognizer does not understand, and the body
    structuring refuses it rather than claiming it as an end-of-iteration
    jump.
    """
    if lo == continue_target:
        # AMBIGUITY TIE-BREAK, not a soundness requirement. When `lo` is the
        # enclosing loop's own header, a conditional backward JMP to it is
        # exactly what luac emits for an `if` in TAIL POSITION of that loop's
        # body whose false-exit was threaded onto the closing JMP -- the shape
        # `_structure_if`'s `jt == continue_target` rewrite already handles.
        # The two readings compile identically (`while true do if f() then
        # g() end end` and `while true do repeat until f() g() end` are the
        # same bytecode; verified against luac_sz4), so neither is "wrong" and
        # the gate cannot separate them. Preferring the incumbent `If` keeps
        # M3's reading of a very common shape rather than churning it for a
        # `repeat` the source almost certainly did not contain. Measured to
        # cost nothing: with and without this guard, an 8-shape
        # repeat-inside-a-loop battery certifies the same 3, and
        # `_match_repeat` fires ZERO times on the corpus either way.
        return None
    cands = [s for s in sites.get(lo, ()) if lo < s < hi]
    if not cands:
        return None
    header_blk = pc2blk[lo]
    if not any(dominates(idoms, header_blk, pc2blk[s]) for s in cands):
        return None                          # pc-retreating, but not a back edge
    S = max(cands)
    cond_pc = S - 1
    if cond_pc < lo or cond_pc not in fn.instrs \
            or fn.instrs[cond_pc].ri.op not in _COMPARE:
        return None
    if fn.instrs[cond_pc].successors != (S, S + 1):
        return None                          # the compare does not gate this JMP
    s_blk = pc2blk[S]
    if s_blk in idoms and not dominates(idoms, header_blk, s_blk):
        return None                          # reachable from outside the loop
    allow = (continue_target,) if continue_target is not None else ()
    if not _exits_only_to(fn, lo, S, allow=allow):
        return None
    try:
        _verify_single_entry(cfg, idoms, pc2blk, lo, lo, cond_pc,
                             allow_unreachable=True)
        body = _structure_range(fn, cfg, idoms, pc2blk, lo, cond_pc,
                                break_target=S + 1, sites=sites,
                                memo=memo) if lo < cond_pc \
            else Seq((), frozenset())
        if all_claimed(body) != {p for p in fn.instrs if lo <= p < cond_pc}:
            return None
        if _own_enditers(body):
            return None                      # see _match_while's guard
    except (StructureError, RegionOverlap):
        return None
    return (Repeat(body=body, cond=fn.instrs[cond_pc],
                   negated=(fn.instrs[cond_pc].ri.a == 0),
                   closing=fn.instrs[S],
                   claimed_pcs=frozenset({cond_pc, S})), S + 1)


def _match_while_true(fn, cfg, idoms, pc2blk, sites, memo, lo: int, hi: int):
    """Recognize `while true do ... end` opening at range position `lo`.

    Returns `(WhileTrue region, next pc)` or None. Never raises: a shape it
    cannot prove is simply not a while loop, and the caller goes on to try
    the other recognizers (and ultimately refuses).

    What proves `lo` is a loop header is **dominance, not pc order**: at
    least one JMP targeting `lo` must live in a block that `lo`'s block
    dominates. pc-retreating edges alone do not qualify -- a rotated
    generic-for re-enters its body with a pc-retreating JMP whose target does
    not dominate it (measured on the corpus 2026-08-11: 21 protos), and
    treating those as while headers would mis-claim them.

    The *closing* JMP is then the LAST site in range, which is not required
    to be a dominance back edge itself: luac emits a closing JMP for a `while
    true` body whose every path breaks or returns even though nothing can
    reach it, and that dead JMP is still the instruction that lexically ends
    the loop. (This is the one place the plan's invariant 2 -- which asks for
    dominance on the chosen S -- is unsatisfiable as written; requiring it
    makes `while true do while true do if f() then break end end ... end`
    unrecognizable. What is required instead: S's block is either unreachable
    or dominated, so an S reachable from OUTSIDE the loop is still refused.)

    Candidates are tried last-first and the body structuring itself is the
    validator: two `while true` loops can share a header (an inner loop as
    the first statement of an outer one), and then the outer loop's threaded
    end-of-iteration jumps are also JMPs targeting that shared header. Only
    attempting to structure `[lo, S)` distinguishes the real closing JMP from
    those. A candidate that fails leaves nothing behind -- no region is
    published until its whole body structures and claims exactly [lo, S).
    """
    cands = [s for s in sites.get(lo, ()) if lo <= s < hi]
    if not cands:
        return None
    header_blk = pc2blk[lo]
    if not any(dominates(idoms, header_blk, pc2blk[s]) for s in cands):
        return None                          # pc-retreating, but not a back edge
    for S in sorted(cands, reverse=True):
        s_blk = pc2blk[S]
        if s_blk in idoms and not dominates(idoms, header_blk, s_blk):
            continue                         # reachable from outside the loop
        if not _exits_only_to(fn, lo, S):
            continue
        try:
            _verify_single_entry(cfg, idoms, pc2blk, lo, lo, S, allow_unreachable=True)
            body = _structure_range(fn, cfg, idoms, pc2blk, lo, S,
                                    break_target=S + 1, continue_target=lo,
                                    sites=sites, memo=memo) if lo < S \
                else Seq((), frozenset())
            if all_claimed(body) != {p for p in fn.instrs if lo <= p < S}:
                continue                     # under/over-claimed: wrong candidate
            if not (_own_enditers(body) <= _tail_enditers(body)):
                # An EndIter prints as nothing, which is only faithful where
                # falling out of the body is what the jump does anyway. Each
                # one was already required to sit at the end of ITS range;
                # this is the missing half -- that the range is itself in tail
                # position of the whole loop body. Refuse rather than emit a
                # jump we would silently drop.
                continue
        except (StructureError, RegionOverlap):
            continue
        return (WhileTrue(body=body, closing=fn.instrs[S],
                          claimed_pcs=frozenset({S})), S + 1)
    return None


def _structure_range(fn, cfg, idoms, pc2blk, lo: int, hi: int,
                     break_target: int | None = None,
                     continue_target: int | None = None, sites=None,
                     memo=None) -> Region:
    """Memoizing front end for `_structure_range_impl`.

    `_match_while_true` validates each closing-JMP candidate by structuring
    the body, so a shape it ultimately refuses costs one full structuring per
    candidate -- and nested loops multiply. Measured before this memo, on
    luac-compiled input of d shared-header `while true` loops each ending in
    a refusable shape: d=6 0.011s, d=8 0.047s, d=10 0.207s -- a clean 4x per
    two levels, i.e. exponential, which at d=20 is minutes. This module
    already refuses to loop forever on a recognizer bug for the same reason
    (see the progress check below); hanging on legal-but-deep input is the
    same defect wearing a different hat.

    The result of structuring a range is a pure function of
    `(lo, hi, break_target, continue_target)` given the fixed
    fn/cfg/idoms/pc2blk/sites, so caching it -- refusals included, they are
    the expensive half -- is sound and collapses the blowup to linear in
    distinct ranges. The cache lives for one `build_sir` call.
    """
    if sites is None:
        sites = _jmp_sites(fn)
    if memo is None:
        memo = {}
    key = (lo, hi, break_target, continue_target)
    hit = memo.get(key)
    if hit is not None:
        if isinstance(hit, str):
            raise StructureError(hit)
        return hit
    try:
        region = _structure_range_impl(fn, cfg, idoms, pc2blk, lo, hi,
                                       break_target=break_target,
                                       continue_target=continue_target,
                                       sites=sites, memo=memo)
    except StructureError as e:
        memo[key] = str(e)
        raise
    memo[key] = region
    return region


def _structure_range_impl(fn, cfg, idoms, pc2blk, lo: int, hi: int,
                          break_target: int | None = None,
                          continue_target: int | None = None, sites=None,
                          memo=None) -> Region:
    """Structure the pc interval [lo, hi) into a Region. Assumes single-entry at lo.

    break_target: if this range is (transitively) a loop body, the pc a `break`
    JMP inside it must target to be recognized as Break rather than an
    unrecognized transfer. None outside any loop.

    continue_target: likewise the pc a threaded end-of-iteration JMP targets --
    the enclosing `while true` loop's header. None outside a while body, and
    deliberately None again inside a nested for body (a jump out of a for body
    to the enclosing while's header would skip the FORLOOP, so it is NOT an
    end-of-iteration jump for the for and must not be claimed as one).

    sites/memo: the `_jmp_sites` map and the per-`build_sir` result cache,
    both created once at the top call. Passed as optional keywords rather
    than positionals so the top-level call in build_sir keeps its M3
    signature -- but this function has exactly one caller, `_structure_range`
    (never `build_sir` directly), and it always resolves both to non-None
    before calling in. A lazy `is None` fallback here would be unreachable
    defense that could silently fork the memo cache (a fresh, unshared `{}`)
    if some future caller ever did pass `None` straight through -- assert
    instead, so that caller becomes a loud bug rather than a quiet one.
    """
    assert sites is not None and memo is not None
    parts: list[Region] = []
    pc = lo
    _last_pc: int | None = None
    pending: tuple[Region, int] | None = None
    while pc < hi:
        # Every path through this loop body must strictly advance pc -- if one
        # doesn't (a recognizer bug returns pc unchanged, or backwards), the
        # loop would otherwise spin forever re-attempting the same pc. This is
        # not just a test-hygiene concern: malformed or adversarial bytecode
        # that trips a latent recognizer bug in the field would hang the
        # decompiler rather than falling back, which the "recognize or
        # refuse" discipline this module is built on explicitly rules out.
        # Refuse instead of looping.
        if _last_pc is not None and pc <= _last_pc:
            raise StructureError(
                f"pc {pc}: structuring made no forward progress past pc {_last_pc} "
                f"(last op attempted: {fn.instrs[_last_pc].ri.op.name}); "
                "internal recognizer bug, refusing rather than looping forever")
        _last_pc = pc
        if pending is not None:
            # A while header the straight-run accumulator below already
            # matched (and paid for) on the previous iteration.
            region, nxt = pending
            pending = None
            parts.append(region)
            pc = nxt
            continue
        li = fn.instrs[pc]
        op = li.ri.op
        # Tried first: a loop header is a header whatever instruction sits on
        # it, and the for recognizers below key off the instruction alone.
        # `_match_while` before `_match_while_true` -- see its docstring: both
        # can match a `while <cond>`, but only the former's shape certifies.
        w = _match_while(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                         break_target, continue_target) \
            or _match_while_true(fn, cfg, idoms, pc2blk, sites, memo, pc, hi) \
            or _match_repeat(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                             break_target, continue_target)
        if w is not None:
            parts.append(w[0])
            pc = w[1]
            continue
        if op is Op.FORPREP:
            region, nxt = _structure_numeric_for(fn, cfg, idoms, pc2blk, pc,
                                                sites=sites, memo=memo)
            parts.append(region)
            pc = nxt
            continue
        gfor = _match_generic_for(fn, pc, hi) if op is Op.JMP else None
        if gfor is not None:
            region, nxt = _structure_generic_for(fn, cfg, idoms, pc2blk, pc, *gfor,
                                                 sites=sites, memo=memo)
            parts.append(region)
            pc = nxt
            continue
        if op in (Op.RETURN, Op.TAILCALL):
            parts.append(Return(instr=li, claimed_pcs=frozenset({pc})))
            pc += 1 + len(li.consumed)
            continue
        if op in _COMPARE:
            region, nxt = _structure_if(fn, cfg, idoms, pc2blk, pc, hi,
                                        break_target=break_target,
                                        continue_target=continue_target,
                                        sites=sites, memo=memo)
            parts.append(region)
            pc = nxt
            continue
        if op is Op.JMP and break_target is not None and li.successors == (break_target,):
            parts.append(Break(claimed_pcs=frozenset({pc})))
            pc += 1
            continue
        if op is Op.JMP and continue_target is not None \
                and li.successors == (continue_target,) and pc + 1 == hi:
            # A threaded end-of-iteration jump (see regions.EndIter). Only
            # claimed in TAIL position of the range: it prints as nothing, so
            # anywhere else the statements that follow it in the region tree
            # would be printed as if they executed after it, which they do
            # not. luac only ever leaves such a jump in tail position (the
            # jumps it threads onto the closing JMP's list are precisely the
            # ones whose destination was the end of the loop body), so a
            # non-tail one is a shape we do not understand -- refuse.
            parts.append(EndIter(claimed_pcs=frozenset({pc})))
            pc += 1
            continue
        if len(li.successors) != 1 or li.successors[0] != pc + 1 + len(li.consumed):
            # a non-fallthrough, non-recognized transfer inside acyclic code
            raise StructureError(f"pc {pc}: unrecognized transfer {op.name}")
        # accumulate a maximal straight run
        run = [li]
        run_pcs = {pc}
        pc += 1 + len(li.consumed)
        while pc < hi:
            nli = fn.instrs[pc]
            nop = nli.ri.op
            if nop is Op.FORPREP or (nop is Op.JMP and _match_generic_for(fn, pc, hi) is not None):
                # loop header: must be claimed by its own region, not swallowed
                # into this straight run -- stop and let the outer loop see it.
                # (Checked explicitly, not just via the fallthrough test below,
                # because a degenerate empty-body for-in's leading JMP targets
                # pc+1 -- indistinguishable from an ordinary fallthrough by
                # successor shape alone.)
                break
            if pc in sites:
                # Possible `while true` header in the middle of the run (the
                # loop's first instruction is an ordinary fallthrough one, so
                # nothing else here would stop). Matched for real rather than
                # on the cheap "is a JMP targeting it" precondition, and the
                # result is carried over in `pending`: breaking the run on a
                # precondition that then fails to recognize would split one
                # Straight into two for shapes M3 already accepts, changing
                # their printed output for no reason.
                w = _match_while(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                                 break_target, continue_target) \
                    or _match_while_true(fn, cfg, idoms, pc2blk, sites, memo, pc, hi) \
                    or _match_repeat(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                                     break_target, continue_target)
                if w is not None:
                    pending = w
                    break
            if nop in _COMPARE or nop in (Op.RETURN, Op.TAILCALL):
                break
            if nop is Op.JMP and break_target is not None and nli.successors == (break_target,):
                break
            if nop is Op.JMP and continue_target is not None \
                    and nli.successors == (continue_target,) and pc + 1 == hi:
                break
            if len(nli.successors) != 1 or nli.successors[0] != pc + 1 + len(nli.consumed):
                break
            run.append(nli); run_pcs.add(pc)
            pc += 1 + len(nli.consumed)
        parts.append(Straight(tuple(run), frozenset(run_pcs)))
    if len(parts) == 1 and isinstance(parts[0], (Straight, Return)):
        return parts[0]
    return Seq(tuple(parts), frozenset())


def _structure_if(fn, cfg, idoms, pc2blk, pc: int, hi: int, break_target: int | None = None,
                  continue_target: int | None = None, sites=None, memo=None):
    """pc is a compare instruction; the next pc is its JMP. Returns (If region, next pc)."""
    li = fn.instrs[pc]
    jmp_pc = pc + 1
    if jmp_pc not in fn.instrs or fn.instrs[jmp_pc].ri.op is not Op.JMP:
        raise StructureError(f"pc {pc}: compare not followed by JMP")
    jmp = fn.instrs[jmp_pc]
    jt = jmp.successors[0]                      # where the JMP goes (start of else / join)
    then_lo = jmp_pc + 1                        # fall-through: the 'then' body
    if continue_target is not None and jt == continue_target:
        # The false-exit was threaded onto the enclosing loop's closing JMP
        # and thence to its header (`while true do if c then x() end end`).
        # Its source-level destination is "the end of the loop body", which
        # inside this range is `hi`: the if is in tail position of the range
        # -- luac would have patched the jump to the join instead of leaving
        # it pending if any statement of this range followed the if.
        #
        # Why `jt == continue_target` is sufficient proof of that, rather
        # than a coincidence of pc arithmetic: this is luac's `jpc`
        # (pending-jump-list) mechanism (vendor/lua-5.1/src/lcode.c).
        # `luaK_jump` (lines 59-66) does NOT patch a pending jump list to a
        # fixed target when the next thing emitted is itself a JMP -- it
        # saves the pending list (line 60), clears it (line 62), emits the
        # new JMP, and then *concatenates* the saved list onto the new JMP's
        # own chain (line 64, `luaK_concat`) so they will all later be
        # patched to wherever that JMP itself ends up. Emitting any
        # non-JMP instruction instead flushes the pending list immediately,
        # to that instruction's own pc: `luaK_code` (lines 789-801) calls
        # `dischargejpc` (line 791) before every emission, which patches the
        # whole pending list to the current `fs->pc` (`dischargejpc`/
        # `patchlistaux`, lines 163-166) and clears it. So a jump that is
        # still pending by the time `whilestat` patches the loop's closing
        # JMP to the header -- which is what `jt == continue_target` here
        # observes -- proves every instruction between this JMP and the
        # closing JMP was itself a JMP; no non-JMP instruction could have
        # intervened without flushing it to a nearer target first. Hence the
        # if really is in tail position of the range, and `hi` (not some
        # earlier pc) is the correct rewritten destination.
        jt = hi
    if not (then_lo <= jt <= hi):
        raise StructureError(f"pc {pc}: if targets out of range")
    # Peek (do not recurse yet) at whether the then-body ends by jumping over an
    # else block, so the trailing JMP can be excluded from the then-body range
    # before we structure it -- recursing over [then_lo, jt) first and only
    # afterwards re-slicing would feed that trailing JMP into _structure_range,
    # which rejects it as an unrecognized (non-fallthrough) transfer.
    else_body = None
    join = jt
    then_hi = jt
    then_last = jt - 1
    is_break_jmp = (then_last >= then_lo and then_last in fn.instrs
                    and fn.instrs[then_last].ri.op is Op.JMP
                    and break_target is not None
                    and fn.instrs[then_last].successors == (break_target,))
    if then_last >= then_lo and then_last in fn.instrs \
            and fn.instrs[then_last].ri.op is Op.JMP and not is_break_jmp:
        # A trailing JMP at the end of the then-body normally means "skip over
        # the else block". But if its target is this loop's break_target, it
        # IS the user's `break` statement (e.g. `if x then break end`, no
        # else) -- not a compiler-inserted else-skip. Left alone (is_break_jmp
        # true), then_hi stays == jt (no else assumed) and the recursive
        # _structure_range call over the then-body recognizes it as Break
        # itself. Getting this backwards would silently misclaim the pcs
        # between jt and break_target as a fabricated "else" block.
        else_jmp = fn.instrs[then_last]
        cand = else_jmp.successors[0]
        if continue_target is not None and cand == continue_target:
            # Same threading as above, one level down: the else-skip of an
            # if/else in tail position of a loop body lands on the header.
            # It is still an else-skip -- rewriting it to `hi` is what keeps
            # the else block [jt, hi) from being dropped. Same jpc/luaK_jump
            # argument as the `jt == continue_target` rewrite above (see its
            # comment, ~30 lines up, for the vendor/lua-5.1/src/lcode.c line
            # numbers): `cand == continue_target` is proof that nothing but
            # JMPs sit between this else-skip and the loop's closing JMP, so
            # this else-skip is in tail position too and `hi` is correct.
            cand = hi
        if cand < jt:
            # Backward-targeting trailing JMP: not an else-skip at all (luac's
            # else-skips always jump forward over the else block), but an
            # instruction belonging to the then-body -- typically the closing
            # JMP of a `while`/`while true` loop, or a generic-for's own back
            # edge, that ends it. Leave it inside the then-body; there is no
            # else block.
            #
            # M3 raised "else-join out of range" here unconditionally, which
            # was the single largest refusal cluster on the corpus (139/169
            # remaining unique protos, of which 135 are this shape) and the
            # reason NO corpus loop ever reached the loop recognizer: the
            # loops are nested inside `if`s, and the `if` gave up on their
            # closing JMP first.
            #
            # M4 task 1 carved out one exclusion here -- a generic-for's own
            # back edge, i.e. `if c then for k, v in pairs(t) do ... end end`
            # -- purely to keep the ledger frozen for that task, since such a
            # proto has nothing unprintable left in it and would have
            # certified and moved a ledger row. That exclusion has now
            # expired: the loop printer landed in task 2 and this task moves
            # the ledger by design. Removed; `snr_common.lua:main_24_1` (the
            # measured single corpus instance) is accepted as a result.
            cond_pcs = frozenset({pc, jmp_pc})
        else:
            join = cand
            if not (jt <= join <= hi):
                raise StructureError(f"pc {pc}: else-join out of range")
            # the trailing JMP of the then-body is claimed by the If, not the then-body
            then_hi = then_last
            cond_pcs = frozenset({pc, jmp_pc, then_last})
    else:
        cond_pcs = frozenset({pc, jmp_pc})
    # The interval arithmetic above only proves the pc ranges are gap-free and
    # non-overlapping -- it says nothing about whether either range is actually
    # reachable *only* through this condition. Verify single-entry via the
    # dominator tree before trusting the ranges as branch bodies.
    _verify_single_entry(cfg, idoms, pc2blk, pc, then_lo, then_hi)
    if then_hi != jt:
        _verify_single_entry(cfg, idoms, pc2blk, pc, jt, join)
    then_body = _structure_range(fn, cfg, idoms, pc2blk, then_lo, then_hi,
                                 break_target=break_target,
                                 continue_target=continue_target,
                                 sites=sites, memo=memo) if then_lo < then_hi \
        else Seq((), frozenset())
    if else_body is None and then_hi != jt:
        else_body = _structure_range(fn, cfg, idoms, pc2blk, jt, join,
                                     break_target=break_target,
                                     continue_target=continue_target,
                                     sites=sites, memo=memo) if jt < join \
            else Seq((), frozenset())
    return (If(cond=li, negated=(li.ri.a == 0), then_body=then_body,
               else_body=else_body, join_pc=join, claimed_pcs=cond_pcs), join)


def _match_generic_for(fn, pc: int, hi: int):
    """pc is a candidate leading JMP of a generic-for's luac layout:

        pc:       JMP -> tf_pc          (skip the body on entry -- go straight
                                          to the TFORLOOP test first)
        body_lo:  [body instructions]   (body_lo == pc+1)
        tf_pc:    TFORLOOP A C
        jmp_pc:   JMP -> body_lo        (back edge: continue the loop)
        after:    tf_pc+2               (TFORLOOP's other successor: loop exit)

    This is luac's *only* for-in emission shape (body-first, TFORLOOP+JMP
    tail, leading skip-JMP straight to the test) -- matching all four links
    exactly is recognition, not a heuristic: any other JMP with a forward
    target, including a while-loop's superficially similar leading
    "jump to condition" JMP, fails at the "does it land on a TFORLOOP"
    check and is correctly left for the caller to treat as an ordinary
    (and here, unrecognized) transfer.

    Returns (tf_pc, jmp_pc, body_lo, after) or None.
    """
    li = fn.instrs[pc]
    if li.ri.op is not Op.JMP:
        return None
    tf_pc = li.successors[0]
    if not (pc < tf_pc < hi) or tf_pc not in fn.instrs \
            or fn.instrs[tf_pc].ri.op is not Op.TFORLOOP:
        return None
    jmp_pc = tf_pc + 1
    if jmp_pc not in fn.instrs or fn.instrs[jmp_pc].ri.op is not Op.JMP:
        return None
    body_lo = pc + 1 + len(li.consumed)
    if fn.instrs[jmp_pc].successors != (body_lo,):
        return None
    return (tf_pc, jmp_pc, body_lo, tf_pc + 2)


def _structure_numeric_for(fn, cfg, idoms, pc2blk, pc: int, sites=None, memo=None):
    """pc is a FORPREP. Returns (NumericFor region, next pc)."""
    prep = fn.instrs[pc]
    loop_pc = pc + 1 + prep.ri.sbx
    if loop_pc not in fn.instrs or fn.instrs[loop_pc].ri.op is not Op.FORLOOP:
        raise StructureError(f"pc {pc}: FORPREP does not reach a FORLOOP")
    loop = fn.instrs[loop_pc]
    body_lo = pc + 1
    body_after = loop_pc + 1                      # fall-through: after the loop
    # The body's only entry, on every execution path from the function entry,
    # is FORPREP -> FORLOOP -> (back-edge to body_lo); verify the dominator
    # tree agrees before trusting [body_lo, loop_pc) as a clean single-entry
    # region, exactly as _structure_if does for branch bodies.
    _verify_single_entry(cfg, idoms, pc2blk, pc, body_lo, loop_pc)
    # continue_target is deliberately NOT threaded into a for body: see
    # _structure_range's docstring.
    body = _structure_range(fn, cfg, idoms, pc2blk, body_lo, loop_pc,
                            break_target=body_after, sites=sites,
                            memo=memo) if body_lo < loop_pc \
        else Seq((), frozenset())
    return (NumericFor(prep=prep, loop=loop, body=body,
                       claimed_pcs=frozenset({pc, loop_pc})), body_after)


def _structure_generic_for(fn, cfg, idoms, pc2blk, lead_pc: int,
                           tf_pc: int, jmp_pc: int, body_lo: int, after: int,
                           sites=None, memo=None):
    """lead_pc is the leading JMP (lead_pc -> tf_pc) that _match_generic_for matched."""
    tf = fn.instrs[tf_pc]
    jmp = fn.instrs[jmp_pc]
    # lead_pc is the loop's sole external entry: the body is reached only via
    # the back-edge JMP (jmp_pc -> body_lo), never directly from lead_pc
    # (which always jumps straight past the body to tf_pc on first entry) --
    # so every path from the function entry into the body passes through
    # lead_pc first. Verify the dominator tree agrees before trusting
    # [body_lo, tf_pc) as a clean single-entry region.
    _verify_single_entry(cfg, idoms, pc2blk, lead_pc, body_lo, tf_pc)
    body = _structure_range(fn, cfg, idoms, pc2blk, body_lo, tf_pc,
                            break_target=after, sites=sites,
                            memo=memo) if body_lo < tf_pc \
        else Seq((), frozenset())
    return (GenericFor(call=tf, loop=jmp, body=body,
                       claimed_pcs=frozenset({lead_pc, tf_pc, jmp_pc})), after)

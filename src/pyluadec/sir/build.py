"""Dominator-driven region identification (spec §3 ③). Acyclic subset: Straight / Seq / If.

Discipline: recognize or raise StructureError — never emit a guessed structure.
The pc-claim audit (all_claimed == fn pcs) is asserted at every build_sir exit.
"""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.cfg import build_cfg, dominates, immediate_dominators
from pyluadec.lift.lift import LirFunction, LirInstr
from pyluadec.lift.opcodes import Op

from .regions import (Break, CondOp, CondTest, CondValue, EndIter, GenericFor,
                      If, NumericFor, Region, RegionOverlap, Repeat, Return,
                      Seq, Straight, VAlt, VTail, While, WhileTrue,
                      all_claimed, cond_claimed, value_claimed, _own_enditers,
                      _tail_enditers)

_COMPARE = frozenset({Op.EQ, Op.LT, Op.LE, Op.TEST})
# TESTSET is still NOT an if-condition -- it ASSIGNS on the branch it takes, so
# no if-statement reading of it exists. M3 therefore refused it outright (it
# has two successors and reached the unrecognized-transfer check). As of M4
# task 4 it is recognized for what it is: the and/or VALUE idiom, claimed by
# `_match_cond_value` as a `CondValue` region whose whole chain reconstructs to
# one assignment. A bare `TEST` is deliberately NOT claimed as a value test
# even though `lcode.c:patchtestreg` produces one whenever the destination
# register equals the tested one -- `x = x or 1` and `if not x then x = 1 end`
# are then the same bytecode, so the incumbent `if` reading is kept (the same
# ambiguity tie-break `_match_repeat` documents). `TEST` IS accepted as a
# chain's *gate*, where no `if` reading survives structuring anyway.
# Corpus impact of TESTSET, re-measured 2026-08-11: 16/1478 unique protos
# (1.1%), 53 TESTSET sites, every one of them C == 1 (`or`).


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


def _is_dead_else_skip(cfg, start: int) -> bool:
    """True iff the (unreachable) block at `start` is one of the two shapes
    luac emits unconditionally and then cannot reach: the else-skip JMP, or
    the RETURN that always follows a TAILCALL.

    `ifstat` runs `luaK_concat(&escapelist, luaK_jump(fs))` before it knows
    whether the then-block can fall out of itself, so `if c then break else
    x() end` and `if c then return else x() end` leave a JMP that nothing can
    reach sitting at the end of the then-block -- INSIDE whatever branch or
    loop body encloses the `if`. Measured 2026-08-12: ten unique corpus protos
    were refused as `branch body block at pc N is unreachable` for exactly
    this, every one of their dead blocks a single JMP preceded by another JMP
    (the smallest, `snr_common.lua:main_59`, 17 instrs: a numeric-for whose
    body is `if c then n = n + 1 else break end`).

    Deliberately narrow, and the narrowness is free. "One JMP" is not a proxy
    for "harmless dead code": it is the whole of what `ifstat` can leave
    behind, and it is always claimed by whichever region owns the construct
    it terminates -- usually the enclosing `If` itself, as its `then_last` /
    else-skip pc, but a `WhileTrue` whose body ends in `return` claims its own
    dead closing JMP the same way (`_match_while_true`) -- so admitting it
    adds nothing to what has to be printed. Dead code of any other shape is
    still refused -- `tests/test_sir_build_acyclic.py`'s two
    `test_dead_code_inside_a_claimed_*_range_raises` and
    `tests/test_sir_build_loops.py`'s two `test_dead_code_inside_a_*_for_body_
    raises` are hand-built MOVE chains after a RETURN, and they still raise.
    That matters beyond tidiness: printing a dead MOVE after a `return` would
    emit source Lua rejected outright (`return` must end its block).

    Measured 2026-08-12 on the finished tree: replacing this whole check with
    an unconditional `allow_unreachable=True` gives the SAME corpus figure (75
    unique protos below `L3`) and turns all four of those tests red. So the
    four are the neuter proof that admitting an unreachable block at all costs
    nothing -- but by themselves they only pin `len(blk.instrs) == 1`: all
    four are MOVE *chains*, so any single-instruction narrowing already
    refuses them, and they say nothing about the JMP/RETURN opcode test or
    the TAILCALL-predecessor test below.

    ## Fix round 1 (2026-08-12): the opcode/predecessor discrimination, proven

    A prior round of this docstring asserted "the predecessor pc must be that
    TAILCALL, so a RETURN dead for any other reason is still refused" without
    a test that could tell the difference -- reviewed and found unproven: with
    the whole function replaced by `return len(cfg.blocks[start].instrs) ==
    1`, every test that existed at the time (the four above, plus the corpus
    census) stayed exactly as green. Now proven by two more hand-built
    fixtures in `tests/test_sir_longtail2.py`:
    `test_dead_return_with_non_tailcall_predecessor_still_raises` (a lone dead
    RETURN whose predecessor is an ordinary RETURN, not a TAILCALL) and
    `test_dead_non_jmp_non_return_single_instruction_still_raises` (a lone
    dead MOVE -- satisfies `len == 1` but is neither JMP nor RETURN). Under
    the same `len == 1`-only neutering, `build_sir` ACCEPTS both -- the first
    folds two `Return` regions back to back into the `If`'s then-body, the
    second folds a dead `MOVE` into a `Straight` sequence after a `return` --
    with the pc-claim audit still satisfied in both cases. Restored, both
    raise again. So the opcode/predecessor narrowing is load-bearing exactly
    where the four-floor-test neuter proof is silent.
    """
    blk = cfg.blocks[start]
    if len(blk.instrs) != 1:
        return False
    op = blk.instrs[0].ri.op
    if op is Op.JMP:
        return True
    # `lparser.c:retstat` rewrites `return f(...)` to a TAILCALL and then
    # emits `luaK_ret` anyway (lparser.c:1100-1116), so every TAILCALL is
    # followed by a RETURN that the VM never executes. Same argument as the
    # else-skip's, and the same narrowness: the predecessor pc must be that
    # TAILCALL, so a RETURN dead for any other reason is still refused.
    # `snr_common.lua:main_29_0` (18 instrs, `if c then return f(a) else
    # return f(b) end`) is the corpus instance; both of its dead RETURNs and
    # both of its dead JMPs sit inside the branch bodies.
    if op is not Op.RETURN:
        return False
    for b in cfg.blocks.values():
        if b.instrs and b.instrs[-1].ri.pc == start - 1:
            return b.instrs[-1].ri.op is Op.TAILCALL
    return False


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
            if allow_unreachable or _is_dead_else_skip(cfg, start):
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
                        continue_target: int | None,
                        thread_target: int | None = None):
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

    `thread_target` (M5 task 4) is the same unwinding for the case where the
    enclosing construct is an `if` rather than a loop -- `while` as the last
    statement of a then-block whose else-skip absorbed the pending false-exit
    (`if a then while b do f() end else h() end`). See `_structure_if`'s
    docstring for the lcode.c argument. Both rewrites are self-limiting: they
    substitute `hi`, and the `exit_pc != S + 1` test immediately below then
    still has to hold, so a loop that is NOT the last thing in its range
    (`hi > S + 1`) is refused exactly as before.
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
    if (continue_target is not None and exit_pc == continue_target) \
            or (thread_target is not None and exit_pc == thread_target):
        exit_pc = hi
    if exit_pc != S + 1:
        return None
    header_blk = pc2blk[lo]
    if any(pc2blk[p] != header_blk for p in header_pcs + [cond_pc]):
        return None                          # something jumps into the condition
    return tuple(header), tuple(header_pcs), cond_pc, jmp_pc, exit_pc


def _match_while(fn, cfg, idoms, pc2blk, sites, memo, lo: int, hi: int,
                 break_target: int | None, continue_target: int | None,
                 thread_target: int | None = None):
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
    m = _match_while_header(fn, pc2blk, lo, S, hi, continue_target,
                            thread_target)
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
    not dominate it, and treating those as while headers would mis-claim them.

    Re-measured on the corpus 2026-08-12: **7** unique protos carry such an
    edge, 7 occurrences, 7 edges -- the same 7 on every basis, one edge each.
    They are exactly the 7 protos that contain a `TFORLOOP` at all (7/1478
    unique, 7/1944 occurrences), which also caps the figure: the corpus cannot
    hold more rotated generic-for shapes than it holds generic `for`s. An
    earlier "21 protos" here was a planner's figure that survived M4 task 1
    and every later review; it does not reproduce on any basis. The
    qualitative point is unaffected -- it holds at 7, and the counterexample
    set is exactly the shape the argument names.

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


def _match_loop(fn, cfg, idoms, pc2blk, sites, memo, pc: int, hi: int,
                break_target, continue_target, thread_target=None):
    """The loop-recognizer cascade: `(region, next pc)` for the first shape
    that proves out at `pc`, else None.

    The ORDER is load-bearing and is argued in `_match_while`'s docstring:
    `_match_while` before `_match_while_true` because both can match a
    `while <cond>` and only the former's shape certifies. It lives in one
    function because `_structure_range_impl` needs it at two different
    dispatch points -- once at the top of the range loop and once mid-`Straight`
    when a JMP site turns out to be a header -- and the two were previously
    verbatim copies with nothing asserting they agreed. A cascade duplicated
    at two call sites is precisely the shape that grew into the predecessor's
    `structure.py`; one definition means "which recognizer wins" cannot be
    answered differently depending on where structuring happened to be.
    """
    return (_match_while(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                         break_target, continue_target, thread_target)
            or _match_while_true(fn, cfg, idoms, pc2blk, sites, memo, pc, hi)
            or _match_repeat(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                             break_target, continue_target))


class _NoValueChain(Exception):
    """Internal: `_parse_value` found a shape it cannot prove. Never escapes
    `_match_cond_value`, which turns it into a plain `None` -- the caller then
    goes on to the other recognizers and ultimately refuses loudly with its
    own message, exactly like `_match_while`."""


def _straight_step(fn, pc: int) -> int | None:
    """`pc`'s successor if `pc` is an ordinary fall-through instruction, else
    None. Advances past the pseudo-instruction pcs a CLOSURE consumes, which
    `fn.instrs` does not contain (and which the pc-claim audit therefore never
    asks anyone to claim)."""
    li = fn.instrs[pc]
    nxt = pc + 1 + len(li.consumed)
    return nxt if li.successors == (nxt,) else None


def _is_value_test(li, target: int, *, committed: bool) -> bool:
    """True iff `li` is a value test for register `target` -- the instruction
    that short-circuits one alternative of an `and`/`or` chain.

    `TESTSET A B C` is one whenever A is the chain's target; every TESTSET in a
    chain is patched to the same destination by `lcode.c:patchlistaux`.

    A bare `TEST A 0 C` is `lcode.c:patchtestreg`'s rewrite of a TESTSET whose
    destination register IS the tested one -- `CREATE_ABC(OP_TEST,
    GETARG_B(*i), 0, GETARG_C(*i))`, hence A == target and B == 0 exactly.
    It is accepted ONLY once the chain is `committed` (some earlier
    alternative already carried a real TESTSET, or a gate anchored it),
    because an UNcommitted one is genuinely ambiguous: `x = x or 1` and
    `if not x then x = 1 end` compile to the same bytecode, and M3's `if`
    reading of that shape is the incumbent. Inside a committed chain the
    ambiguity is gone -- everything between an alternative's JMP and the join
    is that alternative's right operand, and a Lua expression cannot contain
    an `if` statement.
    """
    if li is None:
        return False
    if li.ri.op is Op.TESTSET:
        return li.ri.a == target
    if li.ri.op is Op.TEST:
        return committed and li.ri.a == target and li.ri.b == 0
    return False


def _parse_value(fn, lo: int, join: int, target: int, *, committed: bool):
    """Parse `[lo, join)` as one `and`/`or` value chain writing `R[target]`,
    where every short-circuit JMP inside targets `join`. Returns a VNode.

    Right-nested by construction, and that is the semantics rather than a
    formatting choice: a TESTSET short-circuits the ENTIRE remainder of the
    chain, so `A1 <op1> (A2 <op2> (... An))` is what the jump structure says.
    Left-nesting would be wrong the moment the operators differ -- `b or c and
    d` and `(b or c) and d` compile to visibly different bytecode (measured
    against luac_sz4 2026-08-11), and the former is the two-ungated-TESTSET
    shape this parser produces.

    Raises `_NoValueChain` for anything it cannot prove.
    """
    staging: list = []
    pc = lo
    while pc < join:
        li = fn.instrs.get(pc)
        if li is None:
            raise _NoValueChain
        op = li.ri.op
        if _is_value_test(li, target, committed=committed):
            jp = pc + 1
            jmp = fn.instrs.get(jp)
            if jp >= join or jmp is None or jmp.ri.op is not Op.JMP \
                    or jmp.successors != (join,):
                raise _NoValueChain
            if op is Op.TEST and not staging:
                # The TEST variant's operand is whatever `staging` left in
                # `target`; with no staging there is nothing that produced it,
                # so the shape is not understood. Refuse rather than read the
                # register and hope.
                raise _NoValueChain
            return VAlt(staging=tuple(staging), gate=None, gate_jmp_pc=None,
                        inner_staging=(), test=li, test_jmp_pc=jp,
                        rest=_parse_value(fn, jp + 1, join, target,
                                          committed=True))
        if op is Op.TESTSET:
            raise _NoValueChain            # a TESTSET writing some OTHER register
        if op in _COMPARE:
            jp = pc + 1
            jmp = fn.instrs.get(jp)
            if jp >= join or jmp is None or jmp.ri.op is not Op.JMP:
                raise _NoValueChain
            nxt_alt = jmp.successors[0]
            # `(<gate> and R[B]) or <rest>`: `luaK_patchtohere` retargets the
            # gate's jump at the pc where the NEXT alternative starts, which is
            # exactly two past the alternative's own TESTSET (test + its JMP).
            # Requiring that equality -- rather than merely "somewhere inside"
            # -- is what makes this recognition instead of a heuristic.
            t = nxt_alt - 2
            test = fn.instrs.get(t)
            test_jmp = fn.instrs.get(t + 1)
            if not (pc + 2 <= t and nxt_alt <= join) \
                    or not _is_value_test(test, target, committed=True) \
                    or test.ri.c != 1 \
                    or test_jmp is None or test_jmp.ri.op is not Op.JMP \
                    or test_jmp.successors != (join,):
                # `test.ri.c != 1` refuses `(<gate> or R[B]) and <rest>`, the
                # mirror shape: it is emitted (goiffalse leaves the gate
                # un-inverted, so the printed condition would need a `not` that
                # `codenot` then folds back into the comparison) and this
                # project has not derived its source form. Refuse, do not guess.
                raise _NoValueChain
            inner: list = []
            q = pc + 2
            while q < t:
                nq = _straight_step(fn, q)
                if nq is None:
                    raise _NoValueChain
                inner.append(fn.instrs[q])
                q = nq
            if q != t or (test.ri.op is Op.TEST and not inner):
                raise _NoValueChain
            return VAlt(staging=tuple(staging), gate=li, gate_jmp_pc=jp,
                        inner_staging=tuple(inner), test=test,
                        test_jmp_pc=t + 1,
                        rest=_parse_value(fn, nxt_alt, join, target,
                                          committed=True))
        nxt = _straight_step(fn, pc)
        if nxt is None:
            raise _NoValueChain
        staging.append(li)
        pc = nxt
    if pc != join:
        raise _NoValueChain                  # a run stepped past the join
    return VTail(instrs=tuple(staging))


def _match_cond_value(fn, cfg, idoms, pc2blk, lo: int, hi: int):
    """Recognize luac's `and`/`or` VALUE idiom opening at range position `lo`.

    Returns `(CondValue region, next pc)` or None; never raises.

    Only two openings can start a chain, and both are read straight off the
    instruction at `lo` rather than searched for:

      * `lo` is the chain's first TESTSET, or
      * `lo` is a gate (`EQ`/`LT`/`LE`/`TEST`) whose JMP lands two past a
        TESTSET -- the `(<gate> and X) or Y` shape.

    That is sufficient because `_structure_range_impl`'s straight-run
    accumulator breaks on both `_COMPARE` and on any non-fall-through
    successor, so the dispatch position always lands exactly on the
    construct's first instruction and never inside its operand staging.

    The dominance check is the same obligation every other recognizer here
    carries: pc-interval arithmetic alone cannot tell that `[lo, join)` is
    entered only through `lo`. Without it, a jump from earlier code into the
    middle of what looks like an alternative would be silently swallowed into
    a conditional expression. Proven load-bearing, not merely asserted:
    `tests/test_express_testset.py::
    test_reachable_jump_into_the_middle_of_a_cond_value_chain_raises` neuters
    it and shows `build_sir` wrongly succeeds, claiming a pc reachable via a
    path that bypasses `lo` entirely (fix round 1, M4 task 4 review,
    Important 1).

    The claim-equality check below (`claimed != {...}`) is different in kind:
    `_parse_value`'s own recursive descent and `value_claimed` are built from
    the same contiguous sub-ranges by construction, so success of the former
    provably implies the latter here -- no adversarial bytecode reaches this
    check today. It only has teeth against a FUTURE edit that changes one of
    the two without the other, and even then `build_sir`'s own top-level
    pc-claim audit independently catches it (less precisely). See
    `test_cond_value_claim_check_is_unreachable_from_real_parse_value_but_
    the_pc_claim_audit_still_catches_a_broken_value_claimed` in the same
    file. Kept for the clearer, local diagnosis -- not because anything wrong
    would otherwise ship."""
    li = fn.instrs[lo]
    op = li.ri.op
    if op is Op.TESTSET:
        t = lo
    elif op in _COMPARE:
        jmp = fn.instrs.get(lo + 1)
        if jmp is None or jmp.ri.op is not Op.JMP:
            return None
        t = jmp.successors[0] - 2
        cand = fn.instrs.get(t)
        if cand is None or (cand.ri.op is not Op.TESTSET
                             and not (cand.ri.op is Op.TEST and cand.ri.b == 0)):
            return None
    else:
        return None
    test_jmp = fn.instrs.get(t + 1)
    if test_jmp is None or test_jmp.ri.op is not Op.JMP:
        return None
    join = test_jmp.successors[0]
    if not (lo < join <= hi):
        return None
    target = fn.instrs[t].ri.a
    try:
        node = _parse_value(fn, lo, join, target, committed=False)
        _verify_single_entry(cfg, idoms, pc2blk, lo, lo, join)
    except (_NoValueChain, StructureError):
        return None
    claimed = value_claimed(node)
    if claimed != {p for p in fn.instrs if lo <= p < join}:
        return None                          # under/over-claimed: not this shape
    return CondValue(target=target, node=node, claimed_pcs=claimed), join


def _structure_range(fn, cfg, idoms, pc2blk, lo: int, hi: int,
                     break_target: int | None = None,
                     continue_target: int | None = None,
                     thread_target: int | None = None, sites=None,
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
    `(lo, hi, break_target, continue_target, thread_target)` given the fixed
    fn/cfg/idoms/pc2blk/sites, so caching it -- refusals included, they are
    the expensive half -- is sound and collapses the blowup to linear in
    distinct ranges. The cache lives for one `build_sir` call.

    `thread_target` is part of the key for the same reason the other two are:
    it changes which jumps `_structure_if` reads as "end of this range", so
    two calls over the same interval with different thread targets can
    legitimately produce different regions (or one refuse and one succeed).
    Omitting it would let whichever ran first answer for both.
    """
    if sites is None:
        sites = _jmp_sites(fn)
    if memo is None:
        memo = {}
    key = (lo, hi, break_target, continue_target, thread_target)
    hit = memo.get(key)
    if hit is not None:
        if isinstance(hit, str):
            raise StructureError(hit)
        return hit
    try:
        region = _structure_range_impl(fn, cfg, idoms, pc2blk, lo, hi,
                                       break_target=break_target,
                                       continue_target=continue_target,
                                       thread_target=thread_target,
                                       sites=sites, memo=memo)
    except StructureError as e:
        memo[key] = str(e)
        raise
    memo[key] = region
    return region


def _structure_range_impl(fn, cfg, idoms, pc2blk, lo: int, hi: int,
                          break_target: int | None = None,
                          continue_target: int | None = None,
                          thread_target: int | None = None, sites=None,
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

    thread_target: the pc that a jump still PENDING at the end of this range
    ends up carrying, when the instruction emitted at that point is itself a
    JMP (an enclosing `if`'s else-skip) and `luaK_jump` therefore concatenated
    the pending list onto it instead of flushing it. Such a jump's
    source-level destination is "the end of this range", i.e. `hi`, and
    `_structure_if` rewrites it accordingly -- see its `thread_target`
    paragraph for the lcode.c argument and for why the rewrite is a no-op
    anywhere but tail position. None at the top level, and None inside any
    loop body (there the analogous role is `continue_target`'s: what a loop
    body's pending jumps get concatenated onto is the loop's own closing JMP).

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
    # `thread_target`'s one invariant, and the whole reason the rewrite it
    # drives is safe: a jump threaded past the end of this range necessarily
    # targets a pc at or beyond `hi`. `_structure_if` combines it with the
    # `jt <= hi` bound it already enforced to conclude that the rewrite is a
    # no-op except on inputs the old code refused outright -- so a caller that
    # ever passed a target INSIDE the range would silently convert a legal
    # forward jump into "end of range", dropping every statement between.
    # Nothing reaches that today (`_structure_if` normalizes a backward raw
    # target to None just above its recursive call); the check exists so a
    # future miswiring is loud. Fault-injected in
    # `tests/test_sir_longtail2.py::test_a_thread_target_inside_the_range_is_
    # rejected_rather_than_silently_retargeting_a_jump`.
    #
    # Fix round 1 finding (F8): this is the SOLE mechanical backstop for the
    # one rewrite the pc-claim audit is blind to -- a dropped/misretargeted
    # threaded jump still partitions the pcs cleanly, so `all_claimed` would
    # not catch it. A bare `assert` vanishes under `python -O`; raising
    # explicitly instead means this backstop cannot be silently compiled away
    # by an interpreter flag no other invariant in this module depends on for
    # its safety (contrast `sites is not None and memo is not None` just
    # above, a parameter-wiring check with no such role, left as `assert`).
    if not (thread_target is None or thread_target >= hi):
        raise AssertionError((thread_target, hi))
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
        w = _match_loop(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                        break_target, continue_target, thread_target)
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
        # Tried BEFORE `_structure_if`, and the order is load-bearing for the
        # gated shape: `(<gate> and X) or Y` opens on a compare, and reading
        # that compare as an `if` puts the chain's TESTSET inside a branch
        # body, where `_structure_range` refuses it. Trying the value chain
        # first can therefore only turn refusals into acceptances -- it never
        # takes a shape away from `_structure_if`, because no shape this
        # matches survives `_structure_if` at all.
        cv = _match_cond_value(fn, cfg, idoms, pc2blk, pc, hi)
        if cv is not None:
            parts.append(cv[0])
            pc = cv[1]
            continue
        if op in _COMPARE:
            region, nxt = _structure_if(fn, cfg, idoms, pc2blk, pc, hi,
                                        break_target=break_target,
                                        continue_target=continue_target,
                                        thread_target=thread_target,
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
                w = _match_loop(fn, cfg, idoms, pc2blk, sites, memo, pc, hi,
                                break_target, continue_target, thread_target)
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


def _match_else_break(fn, cfg, idoms, pc2blk, sites, memo, li, pc: int,
                      jmp_pc: int, then_lo: int, hi: int, jt: int,
                      break_target, continue_target, thread_target):
    """`if <cond> then <body> else break end`: the third absorber of a pending
    false-exit, after the loop-closing JMP (`continue_target`) and the
    enclosing else-skip (`thread_target`).

    Returns `(If region, next pc)` or None; never raises. Only ever consulted
    once `_structure_if`'s `then_lo <= jt <= hi` bound has already failed, so
    like the two rewrites above it can turn refusals into acceptances and
    nothing else.

    `breakstat` (lparser.c:1054-1067) ends with
    `luaK_concat(fs, &bl->breaklist, luaK_jump(fs))`, and `luaK_jump`
    concatenates whatever is pending onto the new JMP. When the else block is
    exactly a `break`, the false-exit `ifstat` made pending one line earlier
    (`luaK_patchtohere(fs, flist)`) is still on `fs->jpc`, so it joins the
    breaklist and is patched to the loop exit -- past the end of the range it
    lives in. Layout, with P the break's own JMP:

        pc        <compare>
        jmp_pc    JMP -> break_target      (the threaded false-exit)
        ...       the then-body
        P-1       JMP -> P+1               (the else-skip, over a 1-instr else)
        P         JMP -> break_target      (the `break`; UNREACHABLE, because
                                             the only jump to it was threaded
                                             onto it rather than at it)
        P+1       the join

    Unlike the two rewrites, the correct destination cannot be read off a
    single number here -- `hi` is wrong (the join is `P+1`, and `P` must end
    up claimed as the else body, not swallowed into the then-body). P is found
    by the pattern above and then VALIDATED by structuring, the same way
    `_match_while_true` validates a closing-JMP candidate: candidates are
    tried last-first and no region is published until the then-body structures
    and claims exactly `[then_lo, P-1)`. Last-first is what makes nesting come
    out right -- for `if a then (if b then x() else break end) else break end`
    both breaks match the pattern, and the OUTER `if`'s else is the later one;
    picking the inner one leaves the outer's own else-skip stranded inside the
    then-body, where `_structure_range` refuses it as an unrecognized transfer
    and the candidate is discarded.

    `snr_common.lua:main_59` (17 instrs) is the smallest corpus instance: a
    numeric-for whose whole body is `if t[i] ~= -1 then n = n + 1 else break
    end`, P == 14.

    ## Fix round 1 (2026-08-12): `then_thread` aligned with `_structure_if`'s

    The recursive `_structure_range` call over the then-body used to be handed
    the ENCLOSING `thread_target` unchanged, while `_structure_if` 60 lines up
    is careful to hand its then-body the RAW target of the jump that actually
    terminates ITS range (`then_thread = raw_jt` / `raw_cand`), not whatever
    `thread_target` it was itself called with. Reviewed and found inconsistent
    -- not a bug (the assert `thread_target is None or thread_target >= hi`
    still held, so the mismatch could only ever cost an acceptance, never
    misstructure one), but the same jpc argument applies here as there: the
    else-skip at `P-1` is what any still-pending nested false-exit inside the
    then-body gets concatenated onto (`luaK_jump`, lcode.c:59-66), so what a
    NESTED if's own false-exit carries when threaded is `P-1`'s raw target --
    `join` (`P+1`) in the ordinary case, or whatever `P-1` itself was already
    threaded onto (`continue_target`/`thread_target`) in the nested-tail case
    `_is_else_skip`'s second branch covers -- not the enclosing `thread_target`
    passed into this function. Aligned to `fn.instrs[P - 1].successors[0]`,
    nulled back to `None` if it points backward of `then_hi` (the same
    `continue_target`-already-covers-it guard `_structure_if` applies to its
    own `then_thread`, keeping the `thread_target >= hi` invariant true for
    the recursive call).

    Measured, not merely argued: `corpus/ledger.jsonl` regenerated after this
    change is BYTE-IDENTICAL to the one committed before it (`git diff
    --stat corpus/ledger.jsonl` empty), and the full suite (561 tests) stays
    green. A hand-built nested fixture exercising the code path
    (`while true do if a then if b then x() else y() end else break end
    end`) was tried looking for a case the old value refused and the new one
    accepts; it structured under BOTH, i.e. it did not discriminate -- which
    is unsurprising given the change only ever converts a refusal into an
    acceptance and the corpus apparently never nests a same-shaped if in
    exactly the tail position that needs it. So this is carried by the
    `_structure_if` analogy and the ledger-neutrality measurement, not by a
    fixture that catches a regression -- honestly stated rather than claimed
    as proven the way the two floor-test-backed guards above are.

    ## Three narrowings, all measured INERT -- kept for diagnosis, not proof

    `pc2blk[P] not in idoms` (P must be unreachable), the last-first
    `sorted(..., reverse=True)`, and the `all_claimed(then_body) != ...`
    equality are each individually, and all three together, removable with the
    whole suite green and the corpus census unchanged at 75 unique protos
    below `L3` (measured 2026-08-12 on this tree; the nested fixture
    `while true do if a then if b then x() else break end else break end end`
    still comes out right under first-first ordering because the structuring
    attempt discards the wrong candidate anyway). They are recorded here as
    DEFENSIVE, in the same terms the runbook already uses for
    `_match_cond_value`'s claim check -- not asserted to be load-bearing.

    What actually carries correctness is the same thing that carries
    `_match_while_true`'s candidate loop: no region is published until the
    then-body structures, plus `_verify_single_entry` on that range, plus
    `build_sir`'s own pc-claim audit, plus the L3 gate. What was NOT tried:
    an adversarial hand-built CFG that separates them. luac cannot emit one
    (a `break` reachable at P implies this if's false-exit was patched at P,
    so `jt` would be in range and this function is never consulted), so such a
    test would have to be synthetic, and the honest statement is that it does
    not exist rather than that the checks are proven.
    """
    if break_target is None or jt != break_target:
        return None

    def _is_else_skip(P: int) -> bool:
        li_ = fn.instrs[P - 1]
        if li_.ri.op is not Op.JMP:
            return False
        if li_.successors == (P + 1,):
            return True
        # The else-skip can itself have been threaded, when the whole `if` is
        # the last statement of its range: then it carries the enclosing
        # loop's header or the enclosing else-skip's target instead of the
        # join. Same jpc argument as `_structure_if`'s two rewrites, and the
        # same self-limiting form -- the join must be `hi` for it to apply.
        threaded = {t for t in (continue_target, thread_target)
                    if t is not None}
        return P + 1 == hi and li_.successors[0] in threaded

    cands = [P for P in range(then_lo + 1, hi)
             if P in fn.instrs and P - 1 in fn.instrs
             and fn.instrs[P].ri.op is Op.JMP
             and fn.instrs[P].successors == (break_target,)
             and pc2blk[P] not in idoms and _is_else_skip(P)]
    for P in sorted(cands, reverse=True):
        then_hi = P - 1
        join = P + 1
        if join > hi:
            continue
        try:
            _verify_single_entry(cfg, idoms, pc2blk, pc, then_lo, then_hi)
            # See "Fix round 1" in this function's docstring: the raw target
            # the else-skip at P-1 carries -- `join` when untouched, or
            # whatever P-1 was itself already threaded onto -- not the
            # enclosing `thread_target` unchanged.
            raw_p = fn.instrs[P - 1].successors[0]
            then_thread = raw_p if raw_p >= then_hi else None
            then_body = _structure_range(fn, cfg, idoms, pc2blk, then_lo,
                                         then_hi, break_target=break_target,
                                         continue_target=continue_target,
                                         thread_target=then_thread,
                                         sites=sites, memo=memo) \
                if then_lo < then_hi else Seq((), frozenset())
            if all_claimed(then_body) != {p for p in fn.instrs
                                          if then_lo <= p < then_hi}:
                continue                     # under/over-claimed: wrong P
        except (StructureError, RegionOverlap):
            continue
        return (If(cond=li, negated=(li.ri.a == 0), then_body=then_body,
                   else_body=Break(claimed_pcs=frozenset({P})), join_pc=join,
                   claimed_pcs=frozenset({pc, jmp_pc, then_hi})), join)
    return None


def _structure_if(fn, cfg, idoms, pc2blk, pc: int, hi: int, break_target: int | None = None,
                  continue_target: int | None = None,
                  thread_target: int | None = None, sites=None, memo=None):
    """`if` dispatch: the incumbent ONE-compare reading first, an `and`/`or`
    condition TREE only if that reading refuses (M6 task 11).

    ## Why the order is this way round, and why it is not a preference

    `a and b` with no else branch is LITERALLY the same bytecode as
    `if a then if b then ... end end` -- both conjuncts' false-exits are
    patched to the same join either way -- so on that shape the two readings
    are both correct and the choice is free. On a shape where they differ, the
    interval arithmetic alone cannot tell them apart: `if a then x = 1 if b
    then f() end end` presents exactly the same two tests with the same two
    targets as `if a and b then` does, and differs only in that the
    instructions BETWEEN the tests are a statement rather than operand
    staging -- a distinction `sir.build` has no register model to make (it is
    `Reconstructor._stage_run` that makes it, one layer down, and only after
    the region tree is already fixed).

    So a chain-first dispatch would have to guess on exactly the shapes where
    guessing is wrong, and the guess would be paid for in the ledger: a proto
    that certifies today under the nested reading would move to `reconstruct:`
    and fall back. Trying the chain only after the incumbent has raised
    `StructureError` makes that impossible by construction -- every input the
    incumbent accepts is structured exactly as before, byte for byte, and the
    chain can only convert a REFUSAL into an acceptance. The same argument,
    and the same shape of it, as `_match_else_break`'s and as the two jpc
    rewrites in `_structure_if_single`.

    The cost is that a compound condition whose incumbent misreading happens
    to structure successfully is not reached here. That is not hypothetical --
    it is precisely the no-else `a and b` case above, which structures as
    nested `if`s and certifies, and which this dispatch therefore leaves
    alone. Measured 2026-08-14: `if a and b then f() end` still builds two
    `If` regions, not one `CondOp`.

    **The ordering is proven load-bearing, on the corpus** (2026-08-14):
    inverting it -- try `_match_cond_chain` first, fall back to the one-compare
    reading -- regenerates `corpus/ledger.jsonl` at `L3` **1432**/1478 and
    structured **1898**/1944, against **1437**/**1903** with the order as
    written. Five protos that certify today would be downgraded by a
    chain-first dispatch, which is the concrete form of the argument above.
    """
    try:
        return _structure_if_single(fn, cfg, idoms, pc2blk, pc, hi,
                                    break_target=break_target,
                                    continue_target=continue_target,
                                    thread_target=thread_target,
                                    sites=sites, memo=memo)
    except StructureError:
        chain = _match_cond_chain(fn, cfg, idoms, pc2blk, pc, hi,
                                  break_target, continue_target,
                                  thread_target, sites, memo)
        if chain is None:
            raise
        return chain


def _structure_if_single(fn, cfg, idoms, pc2blk, pc: int, hi: int, break_target: int | None = None,
                         continue_target: int | None = None,
                         thread_target: int | None = None, sites=None, memo=None):
    """pc is a compare instruction; the next pc is its JMP. Returns (If region, next pc).

    ## `thread_target`: the same jpc threading, one construct over (M5 task 4)

    `continue_target` below unwinds a false-exit that `luaK_jump` concatenated
    onto a LOOP's closing JMP. The identical thing happens with no loop in
    sight, because `luaK_jump` is also what emits an `if`'s else-skip
    (`lparser.c:ifstat`, `luaK_concat(&escapelist, luaK_jump(fs))`): a jump
    still pending when the enclosing `if`'s else-skip is emitted is
    concatenated onto it and ends up carrying the ENCLOSING if's join pc.

        if a then          -- 2: TEST  3: JMP -> 10
          if b then f() end   -- 5: TEST  6: JMP -> 12   <-- threaded
        else h() end        -- 9: JMP -> 12 (the else-skip)

    The inner false-exit at pc 6 targets 12, which is past the end of the
    then-body it lives in (`hi` == 9), so M3/M4 refused it as `if targets out
    of range`. Its source-level destination is "the end of this range", so the
    rewrite is `jt = hi`, exactly as for the loop case.

    Why `jt == thread_target` proves that, and not merely "these two numbers
    happen to agree": it is the same `lcode.c` argument spelled out in the
    `continue_target` comment below, applied to a different concatenation
    site. `luaK_patchtohere` (lcode.c:236-239) does not patch -- it
    concatenates the list onto `fs->jpc` -- and `dischargejpc` (lcode.c:163)
    flushes `fs->jpc` to the current pc before EVERY non-JMP emission
    (`luaK_code`, lcode.c:789-801). So a jump that still carries the enclosing
    else-skip's target was pending at the moment that else-skip was emitted,
    i.e. nothing but JMPs was emitted between the end of the construct that
    owns it and the end of the enclosing then-block. That is tail position.

    The rewrite cannot fire outside tail position even if that argument were
    wrong, which is what makes it safe rather than merely well-argued: every
    `thread_target` handed down is the raw target of the jump that TERMINATES
    the range, and that target is always `>= hi`. A non-tail `if` inside the
    range has its false-exit flushed to a real pc `< hi` by `dischargejpc`, so
    `jt == thread_target` forces `jt >= hi`, and combined with the
    `jt <= hi` bound the old code already enforced the rewrite is a no-op
    unless `jt == hi == thread_target`. Concretely: this rewrite can only ever
    convert a REFUSAL (`jt > hi`) into an acceptance -- it can never
    re-target a jump that structuring already understood.

    `thread_target` is threaded down as the RAW (un-rewritten) successor of
    the terminating jump, because that is the value a concatenated jump
    literally carries in the bytecode, and because multi-level nesting chains
    it: three `if`s deep in tail position all end up on the outermost
    else-skip's target, and each level passes that same raw pc inward.
    """
    li = fn.instrs[pc]
    jmp_pc = pc + 1
    if jmp_pc not in fn.instrs or fn.instrs[jmp_pc].ri.op is not Op.JMP:
        raise StructureError(f"pc {pc}: compare not followed by JMP")
    jmp = fn.instrs[jmp_pc]
    jt = jmp.successors[0]                      # where the JMP goes (start of else / join)
    raw_jt = jt                                 # pre-rewrite: what a threaded jump carries
    then_lo = jmp_pc + 1                        # fall-through: the 'then' body
    if thread_target is not None and jt == thread_target:
        jt = hi                                 # see this function's docstring
    elif continue_target is not None and jt == continue_target:
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
        eb = _match_else_break(fn, cfg, idoms, pc2blk, sites, memo, li, pc,
                               jmp_pc, then_lo, hi, jt, break_target,
                               continue_target, thread_target)
        if eb is not None:
            return eb
        raise StructureError(f"pc {pc}: if targets out of range")
    return _finish_if(fn, cfg, idoms, pc2blk, pc, li, frozenset({pc, jmp_pc}),
                      then_lo, jt, raw_jt, hi, negated=(li.ri.a == 0),
                      break_target=break_target,
                      continue_target=continue_target,
                      thread_target=thread_target, sites=sites, memo=memo)


def _finish_if(fn, cfg, idoms, pc2blk, pc: int, cond, cond_base: frozenset[int],
               then_lo: int, jt: int, raw_jt: int, hi: int, *, negated: bool,
               break_target, continue_target, thread_target, sites, memo):
    """Everything an `if` needs once its CONDITION is settled: splitting
    [then_lo, hi) into a then-body, an optional else-body, and a join.

    Extracted at M6 task 11 so the condition-tree recognizer
    (`_match_cond_chain`) reuses it verbatim rather than growing a second copy
    that could drift. `cond` is whatever goes in `If.cond` -- a single
    `LirInstr` from `_structure_if_single`, a `CondNode` from the chain --
    and `cond_base` is the set of pcs the condition itself occupies, to which
    this function adds the then-body's trailing else-skip when there is one.
    `raw_jt` is the PRE-rewrite target of the condition's false exit (what a
    jump threaded onto it literally carries in the bytecode); see
    `_structure_if_single`'s docstring for why that, and not the rewritten
    `jt`, is what the then-body's own pending jumps end up with.
    """
    # Peek (do not recurse yet) at whether the then-body ends by jumping over an
    # else block, so the trailing JMP can be excluded from the then-body range
    # before we structure it -- recursing over [then_lo, jt) first and only
    # afterwards re-slicing would feed that trailing JMP into _structure_range,
    # which rejects it as an unrecognized (non-fallthrough) transfer.
    else_body = None
    join = jt
    then_hi = jt
    then_last = jt - 1
    # What the then-body's own still-pending jumps end up carrying. With no
    # else-skip the then-body runs to `jt`, so it is this `if`'s own false-exit
    # they share a `jpc` flush with -- hence the RAW `jt`, which is `hi` in the
    # ordinary case (making the inner rewrite a no-op) and the enclosing
    # thread/continue target when this `if` was itself threaded.
    then_thread = raw_jt
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
        raw_cand = cand                   # pre-rewrite: what a threaded jump carries
        if thread_target is not None and cand == thread_target:
            # The else-skip of an if/else in tail position of an enclosing
            # then-block: threaded onto the ENCLOSING else-skip, so it carries
            # that if's join. Same argument as the `jt` rewrite above; see this
            # function's docstring. This is the `else-join out of range`
            # refusal cluster.
            cand = hi
        elif continue_target is not None and cand == continue_target:
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
            cond_pcs = cond_base
        else:
            join = cand
            if not (jt <= join <= hi):
                raise StructureError(f"pc {pc}: else-join out of range")
            # the trailing JMP of the then-body is claimed by the If, not the then-body
            then_hi = then_last
            cond_pcs = cond_base | {then_last}
            # The then-body is terminated by THIS else-skip, so it is this
            # else-skip that `luaK_jump` concatenates the body's still-pending
            # jumps onto -- and they carry its raw target, not the rewritten one.
            then_thread = raw_cand
    else:
        cond_pcs = cond_base
    # The interval arithmetic above only proves the pc ranges are gap-free and
    # non-overlapping -- it says nothing about whether either range is actually
    # reachable *only* through this condition. Verify single-entry via the
    # dominator tree before trusting the ranges as branch bodies.
    _verify_single_entry(cfg, idoms, pc2blk, pc, then_lo, then_hi)
    if then_hi != jt:
        _verify_single_entry(cfg, idoms, pc2blk, pc, jt, join)
    if then_thread < then_hi:
        # A BACKWARD raw target: the terminating jump was itself threaded onto
        # an enclosing LOOP's closing JMP, so what it carries is that loop's
        # header pc. `continue_target` -- unchanged down this same call --
        # already covers exactly that value, so dropping it here loses no
        # acceptance, and it keeps `thread_target`'s one invariant
        # (`thread_target >= hi`, asserted in `_structure_range_impl`) true.
        # Without this, `while true do if a then if b then f() end else g() end
        # end` hands the then-body a thread target BELOW its own range.
        then_thread = None
    then_body = _structure_range(fn, cfg, idoms, pc2blk, then_lo, then_hi,
                                 break_target=break_target,
                                 continue_target=continue_target,
                                 thread_target=then_thread,
                                 sites=sites, memo=memo) if then_lo < then_hi \
        else Seq((), frozenset())
    if else_body is None and then_hi != jt:
        # The else-body is terminated by falling through to `join`. If a real
        # instruction sits there (`join < hi`) `dischargejpc` flushes the
        # body's pending jumps to it and nothing is threaded; only when this
        # `if` is itself in tail position of its range (`join == hi`) can they
        # survive to whatever THIS range's terminator is.
        else_body = _structure_range(fn, cfg, idoms, pc2blk, jt, join,
                                     break_target=break_target,
                                     continue_target=continue_target,
                                     thread_target=(thread_target
                                                    if join == hi else None),
                                     sites=sites, memo=memo) if jt < join \
            else Seq((), frozenset())
    return (If(cond=cond, negated=negated, then_body=then_body,
               else_body=else_body, join_pc=join, claimed_pcs=cond_pcs), join)


# --------------------------------------------------------------------------
# and/or condition trees (M6 task 11)
#
# `lcode.c` compiles a boolean expression into a chain of test+JMP pairs plus
# the operand code each test needs, with two lists of pending jumps: the
# truelist and the falselist. `luaK_infix`/`luaK_posfix` (lcode.c:684-736)
# wire them:
#
#   `X and Y`  -- `luaK_goiftrue(X)` puts X's own jump on the FALSElist and
#                 patches X's truelist to here (the start of Y's code); the
#                 result's falselist is X's ∪ Y's, its truelist is Y's.
#   `X or Y`   -- `luaK_goiffalse(X)` puts X's own jump on the TRUElist and
#                 patches X's falselist to here (the start of Y's code); the
#                 result's truelist is X's ∪ Y's, its falselist is Y's.
#
# `lparser.c:ifstat` then runs `cond()` = `luaK_goiftrue` over the whole
# expression, so the FINAL test's jump is always a false exit, the falselist
# is patched to the else block (or the join), and the truelist is patched to
# the start of the then-block.
#
# Reading that backwards is what `_parse_cond` does. The information the
# instruction stream does NOT carry is which list each jump landed on --
# `EQ A=1` is `x == y` compiled for an `or` and `x ~= y` compiled for an
# `and`, identically encoded -- and it is recovered from the jump's TARGET:
# a jump to a member of the true-target set is a truelist jump, one to the
# false target is a falselist jump, and one to a pc INSIDE the chain is the
# "patched to here" boundary between the two operands of an `and`/`or`, which
# is what makes grouping (`(a or b) and c` vs `a or (b and c)`) recoverable.
#
# Nothing here guesses: every candidate that does not resolve to exactly one
# reading is discarded, and the caller re-raises the incumbent refusal.


@dataclass(frozen=True)
class _Span:
    """One test of a candidate condition chain, with the operand code that
    precedes it INSIDE the chain (empty for the first: the first operand's
    code was staged by the preceding sibling `Straight`, exactly as for a
    single-test `if`)."""
    start: int                       # first pc of this span (staging or test)
    staging: tuple[LirInstr, ...]
    test: LirInstr
    jmp_pc: int
    target: int


def _scan_chain_spans(fn, pc: int, hi: int) -> list[_Span]:
    """The maximal run of `<operand code> <compare> JMP` groups starting at
    `pc`. Purely syntactic -- no target is interpreted here; `_parse_cond`
    decides which prefix of this run (if any) is a condition.

    Staging is accepted only as plain fall-through instructions: anything with
    a second successor (another compare, a `TESTSET` value chain), any JMP,
    any `RETURN`/`TAILCALL`, and any `FORPREP` ends the scan. So a candidate
    chain can never straddle a jump the parse would then have to explain.
    """
    spans: list[_Span] = []
    start = pc
    staging: tuple[LirInstr, ...] = ()
    p = pc
    while True:
        li = fn.instrs.get(p)
        if li is None or li.ri.op not in _COMPARE:
            break
        jli = fn.instrs.get(p + 1)
        if jli is None or jli.ri.op is not Op.JMP or len(jli.successors) != 1:
            break
        spans.append(_Span(start=start, staging=staging, test=li,
                           jmp_pc=p + 1, target=jli.successors[0]))
        q = p + 2
        run: list[LirInstr] = []
        while q < hi:
            nli = fn.instrs.get(q)
            if nli is None or nli.ri.op in _COMPARE:
                break
            if nli.ri.op in (Op.JMP, Op.RETURN, Op.TAILCALL, Op.FORPREP):
                break
            if len(nli.successors) != 1 \
                    or nli.successors[0] != q + 1 + len(nli.consumed):
                break
            run.append(nli)
            q += 1 + len(nli.consumed)
        if q >= hi or q not in fn.instrs or fn.instrs[q].ri.op not in _COMPARE:
            break
        start = p + 2
        staging = tuple(run)
        p = q
    return spans


def _parse_cond(spans: list[_Span], i: int, j: int,
                tset: frozenset[int], fset: frozenset[int], memo: dict):
    """`spans[i:j]` as a condition subtree whose truelist targets are `tset`
    and whose falselist targets are `fset`, or None if it is not one.

    Left-recursive on the FIRST span, which is what makes the result unique
    rather than merely consistent:

      * jump ∈ fset -- the leaf was compiled by `luaK_goiftrue`, i.e. it is
        an `and`'s left operand, and the rest of the chain is the right one.
      * jump ∈ tset -- `luaK_goiffalse`, i.e. an `or`'s left operand.
      * jump lands on `spans[m].start` for some m > i+1 -- the "patched to
        here" boundary. `spans[i:m]` is a GROUP with its own list patched to
        that boundary, and the two possible readings (the group is an `or`'s
        left operand, so its FALSElist went there; or an `and`'s, so its
        TRUElist did) are both tried and exactly one must parse. `m > i+1` is
        required because a jump to `spans[i+1].start` is a jump to where the
        chain falls through anyway -- luac never emits one, and admitting it
        would make the split ambiguous with the two cases above.

    `tset` and `fset` are disjoint at every call (the top-level check refuses
    a chain whose false target is also a true target), so the first two arms
    cannot both fire.
    """
    key = (i, j, tset, fset)
    if key in memo:
        return memo[key]
    memo[key] = None                 # cycles are impossible, but be explicit
    out = _parse_cond_impl(spans, i, j, tset, fset, memo)
    memo[key] = out
    return out


def _parse_cond_impl(spans, i, j, tset, fset, memo):
    g = spans[i].target
    if j - i == 1:
        if g in fset:
            return CondTest(staging=spans[i].staging, test=spans[i].test,
                            jmp_pc=spans[i].jmp_pc, jump_is_true_exit=False)
        if g in tset:
            return CondTest(staging=spans[i].staging, test=spans[i].test,
                            jmp_pc=spans[i].jmp_pc, jump_is_true_exit=True)
        return None
    if g in fset or g in tset:
        left = CondTest(staging=spans[i].staging, test=spans[i].test,
                        jmp_pc=spans[i].jmp_pc, jump_is_true_exit=(g in tset))
        right = _parse_cond(spans, i + 1, j, tset, fset, memo)
        if right is None:
            return None
        return CondOp(op=("or" if g in tset else "and"), left=left, right=right)
    # `_scan_chain_spans` builds `start` strictly increasing (span k+1 starts at
    # span k's JMP pc plus one), so this lookup is single-valued by
    # construction -- written as a dict rather than as a filtered list with a
    # `len(...) == 1` check, which could never fail and would therefore be a
    # guard that only looked like one.
    m = {spans[x].start: x for x in range(i + 2, j)}.get(g)
    if m is None:
        return None
    rest = _parse_cond(spans, m, j, tset, fset, memo)
    if rest is None:
        return None
    boundary = frozenset({g})
    as_or = _parse_cond(spans, i, m, tset, boundary, memo)
    as_and = _parse_cond(spans, i, m, boundary, fset, memo)
    if (as_or is None) == (as_and is None):
        return None                  # neither reading, or an ambiguous pair
    if as_or is not None:
        return CondOp(op="or", left=as_or, right=rest)
    return CondOp(op="and", left=as_and, right=rest)


def _match_cond_chain(fn, cfg, idoms, pc2blk, pc: int, hi: int,
                      break_target, continue_target, thread_target,
                      sites, memo):
    """`if <a and/or b ...> then ... [else ...] end`. Returns `(If, join)` or
    None; never raises.

    Only consulted once the one-compare reading in `_structure_if_single` has
    already refused -- see `_structure_if`'s docstring for why that ordering
    is load-bearing rather than a preference.

    Candidate chain lengths are tried LONGEST first. Shorter prefixes are
    genuinely different conditions (`a and b` where the chain runs `a`, `b`,
    `c` means the `c` test belongs to a nested `if`), and the longest one that
    both parses and structures is the only one that can leave no unexplained
    jump behind: a shorter prefix leaves the remaining tests inside the
    then-body, where `_structure_range` has to make sense of them on their own.

    **That ordering is measured INERT, and is recorded as defensive rather
    than claimed load-bearing** (2026-08-14, MEMORY.md's "guards must be
    proven load-bearing"): replacing it with `range(2, len(spans) + 1)`
    (shortest-first) leaves `corpus/ledger.jsonl` at the same `L3` 1437/1478 /
    structured 1903/1944 and every fixture in `tests/test_sir_condtree.py` and
    `tests/test_sir_longtail2.py` green. The reason it cannot be observed is
    that a short prefix which parses usually goes on to FAIL in `_finish_if`
    -- the leftover tests do not structure as a then-body -- and the loop then
    falls through to the longer candidate anyway. Kept because relying on that
    self-correction is relying on an accident, but no fixture in this tree
    distinguishes the two.

    ## The two refusals here that ARE proven load-bearing

    `raw_jt in tset` and `_parse_cond_impl`'s `(as_or is None) == (as_and is
    None)` are both pinned by `tests/test_sir_condtree.py::
    test_an_ambiguous_group_split_is_refused_rather_than_guessed`, whose
    fixture is `if a and b or c then f() else g() end` with `b`'s JMP
    retargeted to the group boundary (pc 7). Neuter/restore, measured
    2026-08-14, both directions:

      * with `raw_jt in tset` disabled, the k=2 candidate is accepted and
        publishes `CondOp("or", a, b)` -- a condition that silently drops the
        third test out of the `if`;
      * with the ambiguity check disabled, the k=3 candidate is accepted and
        publishes `CondOp("or", CondOp("and", a, b), c)` from a chain that
        equally supports `CondOp("and", a, CondOp("or", b, c))`, i.e. a guess;
      * with both restored, `_match_cond_chain` returns None and the caller
        re-raises the incumbent refusal.

    luac cannot emit either input (both need a JMP whose target is its own
    fall-through), which is exactly why the fixture is hand-built.
    """
    spans = _scan_chain_spans(fn, pc, hi)
    if len(spans) < 2:
        return None
    for k in range(len(spans), 1, -1):
        end = spans[k - 1].jmp_pc + 1        # the then-block's first pc
        if not (pc < end <= hi):
            continue
        raw_jt = spans[k - 1].target
        # The truelist's destination. `luaK_patchtohere` leaves it on `fs->jpc`
        # and `dischargejpc` flushes it to the then-block's first emission --
        # unless that emission is itself a JMP (`break`, `return` threaded, an
        # else-skip over an empty then-block), in which case `luaK_jump`
        # concatenates the list onto that JMP and every member ends up with
        # ITS target instead. Both readings are admitted; one hop is all
        # `luaK_jump` can add, because the JMP it concatenates onto is itself
        # patched exactly once.
        tset = {end}
        eli = fn.instrs.get(end)
        if eli is not None and eli.ri.op is Op.JMP and len(eli.successors) == 1:
            tset.add(eli.successors[0])
        if raw_jt in tset:
            continue                          # ambiguous: refuse, never guess
        node = _parse_cond(spans, 0, k, frozenset(tset), frozenset({raw_jt}), {})
        if node is None:
            continue
        jt = raw_jt
        if thread_target is not None and raw_jt == thread_target:
            jt = hi                           # same rewrites as the one-compare
        elif continue_target is not None and raw_jt == continue_target:
            jt = hi                           # reading; see _structure_if_single
        if not (end <= jt <= hi):
            continue
        try:
            # Single-entry over the chain's own interior, not just over the
            # branch bodies: an operand run that some OTHER jump can land in
            # is not this condition's operand run, whatever the pc arithmetic
            # says. The bodies are checked by `_finish_if` as usual.
            #
            # **Defensive, not proven load-bearing** (measured 2026-08-14).
            # Deleting this call leaves the whole suite green, and the
            # adversarial input it exists for -- `if z then k() end if h(1) and
            # h(2) then f() else g() end` with the first `if`'s false-exit
            # retargeted into the chain's second operand run -- is still
            # refused without it, by `_finish_if`'s own `_verify_single_entry`
            # over the then-body. That is not a coincidence: a jump into the
            # chain from BEFORE it creates a path from the function entry that
            # bypasses `pc` entirely, so the then-body stops being dominated
            # by the condition block at the same moment the chain interior
            # does. A jump into the chain from AFTER it is a back edge, which
            # does not break dominance at all and which neither check refuses.
            # Kept because the region this claims really is a separate range
            # from the bodies and the invariant is stated for it too, and
            # because M6 task 11's brief asks for it explicitly -- but
            # recorded here as unproven rather than asserted as a guard.
            _verify_single_entry(cfg, idoms, pc2blk, pc, pc + 1, end)
            return _finish_if(fn, cfg, idoms, pc2blk, pc, node,
                              cond_claimed(node), end, jt, raw_jt, hi,
                              negated=False, break_target=break_target,
                              continue_target=continue_target,
                              thread_target=thread_target, sites=sites,
                              memo=memo)
        except (StructureError, RegionOverlap):
            continue
    return None


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

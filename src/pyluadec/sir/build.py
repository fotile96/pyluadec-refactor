"""Dominator-driven region identification (spec §3 ③). Acyclic subset: Straight / Seq / If.

Discipline: recognize or raise StructureError — never emit a guessed structure.
The pc-claim audit (all_claimed == fn pcs) is asserted at every build_sir exit.
"""
from __future__ import annotations

from pyluadec.cfg import build_cfg, dominates, immediate_dominators
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import Op

from .regions import (Break, GenericFor, If, NumericFor, Region, RegionOverlap,
                      Return, Seq, Straight, all_claimed)

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


def _verify_single_entry(cfg, idoms, pc2blk, cond_pc: int, lo: int, hi: int) -> None:
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
    """
    cond_block = pc2blk[cond_pc]
    for start in cfg.blocks:
        if not (lo <= start < hi):
            continue
        if start not in idoms:
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


def _structure_range(fn, cfg, idoms, pc2blk, lo: int, hi: int,
                     break_target: int | None = None) -> Region:
    """Structure the pc interval [lo, hi) into a Region. Assumes single-entry at lo.

    break_target: if this range is (transitively) a loop body, the pc a `break`
    JMP inside it must target to be recognized as Break rather than an
    unrecognized transfer. None outside any loop.
    """
    parts: list[Region] = []
    pc = lo
    _last_pc: int | None = None
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
        li = fn.instrs[pc]
        op = li.ri.op
        if op is Op.FORPREP:
            region, nxt = _structure_numeric_for(fn, cfg, idoms, pc2blk, pc)
            parts.append(region)
            pc = nxt
            continue
        gfor = _match_generic_for(fn, pc, hi) if op is Op.JMP else None
        if gfor is not None:
            region, nxt = _structure_generic_for(fn, cfg, idoms, pc2blk, pc, *gfor)
            parts.append(region)
            pc = nxt
            continue
        if op in (Op.RETURN, Op.TAILCALL):
            parts.append(Return(instr=li, claimed_pcs=frozenset({pc})))
            pc += 1 + len(li.consumed)
            continue
        if op in _COMPARE:
            region, nxt = _structure_if(fn, cfg, idoms, pc2blk, pc, hi, break_target=break_target)
            parts.append(region)
            pc = nxt
            continue
        if op is Op.JMP and break_target is not None and li.successors == (break_target,):
            parts.append(Break(claimed_pcs=frozenset({pc})))
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
            if nop in _COMPARE or nop in (Op.RETURN, Op.TAILCALL):
                break
            if nop is Op.JMP and break_target is not None and nli.successors == (break_target,):
                break
            if len(nli.successors) != 1 or nli.successors[0] != pc + 1 + len(nli.consumed):
                break
            run.append(nli); run_pcs.add(pc)
            pc += 1 + len(nli.consumed)
        parts.append(Straight(tuple(run), frozenset(run_pcs)))
    if len(parts) == 1 and isinstance(parts[0], (Straight, Return)):
        return parts[0]
    return Seq(tuple(parts), frozenset())


def _structure_if(fn, cfg, idoms, pc2blk, pc: int, hi: int, break_target: int | None = None):
    """pc is a compare instruction; the next pc is its JMP. Returns (If region, next pc)."""
    li = fn.instrs[pc]
    jmp_pc = pc + 1
    if jmp_pc not in fn.instrs or fn.instrs[jmp_pc].ri.op is not Op.JMP:
        raise StructureError(f"pc {pc}: compare not followed by JMP")
    jmp = fn.instrs[jmp_pc]
    jt = jmp.successors[0]                      # where the JMP goes (start of else / join)
    then_lo = jmp_pc + 1                        # fall-through: the 'then' body
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
        join = else_jmp.successors[0]
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
                                 break_target=break_target) if then_lo < then_hi \
        else Seq((), frozenset())
    if else_body is None and then_hi != jt:
        else_body = _structure_range(fn, cfg, idoms, pc2blk, jt, join,
                                     break_target=break_target) if jt < join \
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


def _structure_numeric_for(fn, cfg, idoms, pc2blk, pc: int):
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
    body = _structure_range(fn, cfg, idoms, pc2blk, body_lo, loop_pc,
                            break_target=body_after) if body_lo < loop_pc \
        else Seq((), frozenset())
    return (NumericFor(prep=prep, loop=loop, body=body,
                       claimed_pcs=frozenset({pc, loop_pc})), body_after)


def _structure_generic_for(fn, cfg, idoms, pc2blk, lead_pc: int,
                           tf_pc: int, jmp_pc: int, body_lo: int, after: int):
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
                            break_target=after) if body_lo < tf_pc \
        else Seq((), frozenset())
    return (GenericFor(call=tf, loop=jmp, body=body,
                       claimed_pcs=frozenset({lead_pc, tf_pc, jmp_pc})), after)

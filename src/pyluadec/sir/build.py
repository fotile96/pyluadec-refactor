"""Dominator-driven region identification (spec §3 ③). Acyclic subset: Straight / Seq / If.

Discipline: recognize or raise StructureError — never emit a guessed structure.
The pc-claim audit (all_claimed == fn pcs) is asserted at every build_sir exit.
"""
from __future__ import annotations

from pyluadec.cfg import build_cfg, immediate_dominators
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import Op

from .regions import (If, Region, RegionOverlap, Return, Seq, Straight,
                      all_claimed)

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


def build_sir(fn: LirFunction) -> Region:
    if has_back_edge(fn):
        raise StructureError("loops not supported in acyclic builder")
    cfg = build_cfg(fn)
    idoms = immediate_dominators(cfg)
    ordered = sorted(fn.instrs)
    try:
        region = _structure_range(fn, cfg, idoms, ordered[0], ordered[-1] + 1)
    except RegionOverlap as e:
        raise StructureError(str(e)) from e
    claimed = all_claimed(region)
    if claimed != set(fn.instrs):
        missing = set(fn.instrs) - claimed
        raise StructureError(f"pc-claim audit failed; unclaimed {sorted(missing)}")
    return region


def _structure_range(fn, cfg, idoms, lo: int, hi: int) -> Region:
    """Structure the pc interval [lo, hi) into a Region. Assumes single-entry at lo."""
    parts: list[Region] = []
    pc = lo
    while pc < hi:
        li = fn.instrs[pc]
        op = li.ri.op
        if op in (Op.RETURN, Op.TAILCALL):
            parts.append(Return(instr=li, claimed_pcs=frozenset({pc})))
            pc += 1 + len(li.consumed)
            continue
        if op in _COMPARE:
            region, nxt = _structure_if(fn, cfg, idoms, pc, hi)
            parts.append(region)
            pc = nxt
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
            if nli.ri.op in _COMPARE or nli.ri.op in (Op.RETURN, Op.TAILCALL):
                break
            if len(nli.successors) != 1 or nli.successors[0] != pc + 1 + len(nli.consumed):
                break
            run.append(nli); run_pcs.add(pc)
            pc += 1 + len(nli.consumed)
        parts.append(Straight(tuple(run), frozenset(run_pcs)))
    if len(parts) == 1 and isinstance(parts[0], (Straight, Return)):
        return parts[0]
    return Seq(tuple(parts), frozenset())


def _structure_if(fn, cfg, idoms, pc: int, hi: int):
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
    if then_last >= then_lo and then_last in fn.instrs \
            and fn.instrs[then_last].ri.op is Op.JMP:
        else_jmp = fn.instrs[then_last]
        join = else_jmp.successors[0]
        if not (jt <= join <= hi):
            raise StructureError(f"pc {pc}: else-join out of range")
        # the trailing JMP of the then-body is claimed by the If, not the then-body
        then_hi = then_last
        cond_pcs = frozenset({pc, jmp_pc, then_last})
    else:
        cond_pcs = frozenset({pc, jmp_pc})
    then_body = _structure_range(fn, cfg, idoms, then_lo, then_hi) if then_lo < then_hi \
        else Seq((), frozenset())
    if else_body is None and then_hi != jt:
        else_body = _structure_range(fn, cfg, idoms, jt, join) if jt < join else Seq((), frozenset())
    return (If(cond=li, negated=(li.ri.a == 0), then_body=then_body,
               else_body=else_body, join_pc=join, claimed_pcs=cond_pcs), join)

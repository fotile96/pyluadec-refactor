"""LIR → 基本块 CFG。fallback 发射器按块分状态（CFG 在 M2 即被实际使用）。"""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.lift.lift import LirFunction, LirInstr


@dataclass(frozen=True)
class BasicBlock:
    start: int
    instrs: tuple[LirInstr, ...]
    succs: tuple[int, ...]


@dataclass(frozen=True)
class Cfg:
    entry: int
    blocks: dict[int, BasicBlock]
    preds: dict[int, tuple[int, ...]]


def build_cfg(fn: LirFunction) -> Cfg:
    pcs = sorted(fn.instrs)
    leaders: set[int] = {1}
    for i, pc in enumerate(pcs):
        li = fn.instrs[pc]
        fallthrough = pc + 1 + len(li.consumed)
        if li.successors != (fallthrough,):
            # 分支/跳转/终结指令：所有后继都是 leader，其顺序下一条也是 leader
            leaders.update(li.successors)
            if i + 1 < len(pcs):
                leaders.add(pcs[i + 1])
    blocks: dict[int, BasicBlock] = {}
    cur: list[LirInstr] = []
    cur_start = None
    for pc in pcs:
        if pc in leaders and cur:
            blocks[cur_start] = _finish(cur, pc)
            cur, cur_start = [], None
        if cur_start is None:
            cur_start = pc
        cur.append(fn.instrs[pc])
        li = fn.instrs[pc]
        fallthrough = pc + 1 + len(li.consumed)
        if li.successors != (fallthrough,):
            blocks[cur_start] = BasicBlock(cur_start, tuple(cur), li.successors)
            cur, cur_start = [], None
    if cur:
        blocks[cur_start] = BasicBlock(cur_start, tuple(cur), cur[-1].successors)
    preds: dict[int, list[int]] = {b: [] for b in blocks}
    for b in blocks.values():
        for s in b.succs:
            preds[s].append(b.start)
    return Cfg(entry=1, blocks=blocks,
               preds={k: tuple(sorted(v)) for k, v in preds.items()})


def _finish(cur: list[LirInstr], next_leader: int) -> BasicBlock:
    # 块因「下一条是 leader」而截断：唯一后继即该 leader（顺序 fallthrough）
    return BasicBlock(cur[0].ri.pc, tuple(cur), (next_leader,))

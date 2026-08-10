"""Cooper–Harvey–Kennedy 迭代支配算法（对不可归约图正确）。"""
from __future__ import annotations

from .blocks import Cfg


def _reverse_postorder(cfg: Cfg) -> list[int]:
    seen: set[int] = set()
    order: list[int] = []

    def dfs(b: int) -> None:
        seen.add(b)
        for s in cfg.blocks[b].succs:
            if s not in seen:
                dfs(s)
        order.append(b)

    import sys
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, len(cfg.blocks) * 2 + 100))
    try:
        dfs(cfg.entry)
    finally:
        sys.setrecursionlimit(old)
    order.reverse()
    return order


def immediate_dominators(cfg: Cfg) -> dict[int, int]:
    rpo = _reverse_postorder(cfg)
    index = {b: i for i, b in enumerate(rpo)}
    idom: dict[int, int] = {cfg.entry: cfg.entry}

    def intersect(a: int, b: int) -> int:
        while a != b:
            while index[a] > index[b]:
                a = idom[a]
            while index[b] > index[a]:
                b = idom[b]
        return a

    changed = True
    while changed:
        changed = False
        for b in rpo:
            if b == cfg.entry:
                continue
            preds = [p for p in cfg.preds.get(b, ()) if p in idom]
            if not preds:
                continue
            new = preds[0]
            for p in preds[1:]:
                new = intersect(new, p)
            if idom.get(b) != new:
                idom[b] = new
                changed = True
    return idom


def dom_tree(idoms: dict[int, int]) -> dict[int, tuple[int, ...]]:
    children: dict[int, list[int]] = {}
    for b, d in idoms.items():
        if b != d:
            children.setdefault(d, []).append(b)
    return {k: tuple(sorted(v)) for k, v in children.items()}


def dominates(idoms: dict[int, int], a: int, b: int) -> bool:
    if b not in idoms or a not in idoms:
        return False
    while True:
        if a == b:
            return True
        parent = idoms[b]
        if parent == b:
            return False
        b = parent

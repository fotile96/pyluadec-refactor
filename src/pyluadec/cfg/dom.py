"""Cooper–Harvey–Kennedy 迭代支配算法（对不可归约图正确）。"""
from __future__ import annotations

from .blocks import Cfg


def _reverse_postorder(cfg: Cfg) -> list[int]:
    """Blocks reachable from the entry, in reverse DFS postorder.

    An explicit stack, not recursion. The recursive form this replaced (M2
    through M5 task 11) raised the **process-global** recursion limit to
    `max(old, len(cfg.blocks) * 2 + 100)` and restored it in a `finally` --
    correct single-threaded, and a mutation of interpreter-wide state visible
    to every other thread and to any callback that ran underneath it. Carried
    as a deferred M2 minor (`m3-backlog.md` §14, "revisit if M3 ever
    parallelises corpus runs"); the parallel run never arrived, but the fix is
    cheaper than the caveat. Fixed at M5 task 12.

    The traversal order is unchanged, deliberately and by construction: a
    block is pushed the first time it is reached (marked `seen` at push, as
    `dfs` marked it at entry), its successors are consumed in `succs` order
    through a stored iterator, and it is appended to `order` only when that
    iterator is exhausted -- which is where `dfs` appended it. Verified over
    all 1944 corpus protos: the two implementations return identical lists,
    and `corpus/ledger.jsonl` is byte-identical across the change.
    """
    seen: set[int] = {cfg.entry}
    order: list[int] = []
    stack: list[tuple[int, "object"]] = [(cfg.entry, iter(cfg.blocks[cfg.entry].succs))]
    while stack:
        b, it = stack[-1]
        for s in it:                      # type: ignore[union-attr]
            if s not in seen:
                seen.add(s)
                stack.append((s, iter(cfg.blocks[s].succs)))
                break
        else:
            stack.pop()
            order.append(b)
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

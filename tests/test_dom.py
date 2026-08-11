# 从邻接表手工构造 Cfg（instrs 为空元组，dom 计算只看图结构）。这里曾有一份
# 与 tests/synth.py::mk_cfg 逐行相同的本地副本 `_mk_cfg`；两个必须在 `preds`
# 构造上保持一致的手写 CFG 构造器是多余的一个，已折叠为共享的那一份。
from tests.synth import mk_cfg


def test_diamond():
    from pyluadec.cfg.dom import dominates, immediate_dominators
    #    1 → 2,3 ; 2 → 4 ; 3 → 4
    idoms = immediate_dominators(mk_cfg({1: (2, 3), 2: (4,), 3: (4,), 4: ()}))
    assert idoms == {1: 1, 2: 1, 3: 1, 4: 1}
    assert dominates(idoms, 1, 4) and not dominates(idoms, 2, 4)


def test_loop():
    from pyluadec.cfg.dom import immediate_dominators
    # 1 → 2 ; 2 → 3,4 ; 3 → 2 ; 4 → ()
    idoms = immediate_dominators(mk_cfg({1: (2,), 2: (3, 4), 3: (2,), 4: ()}))
    assert idoms == {1: 1, 2: 1, 3: 2, 4: 2}


def test_irreducible():
    from pyluadec.cfg.dom import immediate_dominators
    # 经典不可归约：1 → 2,3 ; 2 → 3 ; 3 → 2 （双入口循环）
    idoms = immediate_dominators(mk_cfg({1: (2, 3), 2: (3,), 3: (2,)}))
    assert idoms == {1: 1, 2: 1, 3: 1}


def test_unreachable_block_excluded():
    from pyluadec.cfg.dom import immediate_dominators
    idoms = immediate_dominators(mk_cfg({1: (2,), 2: (), 9: (2,)}))   # 9 不可达
    assert 9 not in idoms and set(idoms) == {1, 2}


def test_dom_tree_children():
    from pyluadec.cfg.dom import dom_tree, immediate_dominators
    idoms = immediate_dominators(mk_cfg({1: (2, 3), 2: (4,), 3: (4,), 4: ()}))
    tree = dom_tree(idoms)
    assert tree[1] == (2, 3, 4) and tree.get(2, ()) == ()


def test_irreducible_requires_fixpoint_iteration():
    """一个必须迭代 >=2 轮才能收敛的不可归约图：1->2,3 ; 2->1,4 ; 3->2,4 ; 4->2,3。

    到 4 有两条路径 1-2-4 与 1-3-4，交集只有 {1,4}，所以 idom(4) 必须是 1。手工推导：
      Dom(2) = {1,2}（路径 1-2 与 1-3-2 的交集）        -> idom(2)=1
      Dom(3) = {1,3}（路径 1-3 与 1-2-4-3 的交集）        -> idom(3)=1
      Dom(4) = {1,4}（路径 1-2-4 与 1-3-4 的交集）        -> idom(4)=1
    这份期望值是手推的，不是跑一遍实现再抄下来的。

    单趟逆后序（不做不动点迭代）会在处理 4 时，因为此时 idom[3] 还没算出来、3 被
    从候选前驱里滤掉，只用前驱 2 直接得到 idom(4)=2 ——这是错的，只有跑第二轮不动点
    迭代、让 idom[3] 参与进来做 intersect(2,3)=1，才能纠正为 1。这个用例专门用来防止
    `immediate_dominators` 退化成单趟遍历（丢掉 `while changed:` 不动点循环）的回归。
    """
    from pyluadec.cfg.dom import immediate_dominators
    idoms = immediate_dominators(mk_cfg({1: (2, 3), 2: (1, 4), 3: (2, 4), 4: (2, 3)}))
    assert idoms == {1: 1, 2: 1, 3: 1, 4: 1}


def _bfs_reachable(cfg) -> set[int]:
    """独立于 dom.py 的可达性计算：从 entry 沿 succs 做 BFS。"""
    seen = {cfg.entry}
    frontier = [cfg.entry]
    while frontier:
        nxt = []
        for b in frontier:
            for s in cfg.blocks[b].succs:
                if s not in seen:
                    seen.add(s)
                    nxt.append(s)
        frontier = nxt
    return seen


def test_corpus_dominator_sanity(corpus_dir):
    import subprocess
    from pyluadec.cfg import build_cfg
    from pyluadec.cfg.dom import dominates, immediate_dominators
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    f = sorted(corpus_dir.glob("*.lua"))[0]
    stack = [load_file(f)]
    while stack:
        p = stack.pop(); stack.extend(p.subprotos)
        cfg = build_cfg(lift_proto(p))
        idoms = immediate_dominators(cfg)
        assert idoms[cfg.entry] == cfg.entry
        for b in idoms:
            assert dominates(idoms, cfg.entry, b)      # entry 支配一切可达块


def test_corpus_dominator_reachability_exact(corpus_dir):
    """idoms 的键集合必须恰好等于从 entry 可达的块集合：既不能漏掉可达块，也不能让
    不可达块（luac 附加的尾部 RETURN 等）泄漏进来。用一个独立于 dom.py 的 BFS 做
    交叉校验，而不是只信任 dominates() 本身——后者即便不可达块泄漏进 idoms，也可能
    因为其 idom 恰好指向 entry 而"看起来"仍被 entry 支配，从而掩盖泄漏。

    已知事实（见 task brief）：luac 给每个 chunk 追加的尾部 RETURN 0 1，在前一条指令
    已是显式 RETURN 时会产生零前驱的不可达块。扫全量语料（229 个文件，< 1s）以确保
    真的撞见至少一次，这条校验才不是空对空的摆设。
    """
    from pyluadec.cfg import build_cfg
    from pyluadec.cfg.dom import immediate_dominators
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto

    saw_unreachable_block = False
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            cfg = build_cfg(lift_proto(p))
            idoms = immediate_dominators(cfg)
            reachable = _bfs_reachable(cfg)
            assert set(idoms) == reachable
            if len(cfg.blocks) > len(reachable):
                saw_unreachable_block = True
    assert saw_unreachable_block

import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _lift(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return lift_proto(load_file(o))


def test_straightline_single_block(tmp_path):
    from pyluadec.cfg import build_cfg
    cfg = build_cfg(_lift("local a = 1 local b = 2 return a + b", tmp_path))
    # luac 总在每个 chunk 末尾追加隐式 `RETURN 0 1`（见 test_lift.py 同名注释），
    # 即便源码已有显式 return；该隐式 RETURN 不可达（无 preds），自成一块。
    # 故这里是 2 块：可达的直线代码块 + 不可达的隐式尾 RETURN 块。
    assert len(cfg.blocks) == 2 and cfg.entry == 1
    assert cfg.blocks[1].succs == ()
    unreachable = [b for b in cfg.blocks.values() if b.start != 1]
    assert len(unreachable) == 1 and cfg.preds[unreachable[0].start] == ()


def test_if_splits_blocks(tmp_path):
    from pyluadec.cfg import build_cfg
    cfg = build_cfg(_lift(
        "local x = tonumber('1')\n"
        "if x then print('y') else print('n') end\n"
        "return x\n", tmp_path))
    assert len(cfg.blocks) >= 4                       # entry / then / else / join
    entry = cfg.blocks[cfg.entry]
    assert len(entry.succs) == 2                      # 条件分支两个出口
    joins = [b for b in cfg.blocks.values() if len(cfg.preds[b.start]) >= 2]
    assert joins                                      # 汇合块存在


def test_closure_with_upvalue_does_not_split_block(tmp_path):
    # CLOSURE 的自然 fallthrough 是 pc + 1 + len(consumed)（consumed 吞掉 upvalue
    # 伪指令字），不是 pc + 1。这里 up 是外层局部变量被内层闭包捕获，luac 在
    # CLOSURE 后附加 1 个 MOVE 伪指令字。若 build_cfg 误用 pc + 1 判断
    # fallthrough，会在 CLOSURE 处产生一次多余的块切分（真实后继仍然正确，但块
    # 粒度错了）——这正是 CFG 被下游按块发射消费时会导致状态机多切出一个不必要
    # 状态的 bug。
    from pyluadec.cfg import build_cfg
    cfg = build_cfg(_lift(
        "local up = 1\n"
        "local f = function() return up end\n"
        "local g = f\n"
        "return g\n", tmp_path))
    # 直线代码（无分支）：可达块 + 不可达的隐式尾 RETURN 块，恰好 2 块。
    assert len(cfg.blocks) == 2
    entry = cfg.blocks[cfg.entry]
    from pyluadec.lift.opcodes import Op
    ops_in_entry = [li.ri.op for li in entry.instrs]
    assert Op.CLOSURE in ops_in_entry
    # CLOSURE 之后的指令（MOVE g,f 等）必须仍在同一块内，而不是被切到新块。
    closure_idx = ops_in_entry.index(Op.CLOSURE)
    assert closure_idx < len(entry.instrs) - 1           # CLOSURE 不是块内最后一条


def test_while_loop_has_back_edge(tmp_path):
    from pyluadec.cfg import build_cfg
    cfg = build_cfg(_lift(
        "local i = 0\n"
        "while i < 3 do i = i + 1 end\n"
        "return i\n", tmp_path))
    back = [(b.start, s) for b in cfg.blocks.values() for s in b.succs if s <= b.start]
    assert back                                       # 回边存在


def test_block_invariants_on_corpus(corpus_dir):
    from pyluadec.cfg import build_cfg
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    import itertools
    files = sorted(corpus_dir.glob("*.lua"))[:20]      # 前 20 个文件足以覆盖形态
    for f in files:
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            fn = lift_proto(p)
            cfg = build_cfg(fn)
            covered = list(itertools.chain.from_iterable(
                (li.ri.pc for li in b.instrs) for b in cfg.blocks.values()))
            assert sorted(covered) == sorted(fn.instrs)        # 每条指令属于恰一块
            for b in cfg.blocks.values():
                for li in b.instrs[:-1]:
                    assert li.successors == (li.ri.pc + 1 + len(li.consumed),)
                for s in b.succs:
                    assert s in cfg.blocks                     # 后继指向块首
                    assert b.start in cfg.preds[s]

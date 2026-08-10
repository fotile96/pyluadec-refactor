import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _load(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return load_file(o)


def test_lift_simple(tmp_path):
    from pyluadec.lift.lift import lift_proto
    fn = lift_proto(_load("local x = 1 return x + 2", tmp_path))
    assert fn.n_pcs == len(fn.proto.code)
    assert set(fn.instrs) == set(range(1, fn.n_pcs + 1))    # 无伪指令时全 pc 都是指令
    last = fn.instrs[fn.n_pcs]
    assert last.successors == ()                             # 末条必是 RETURN


def test_lift_closure_pseudo_instructions(tmp_path):
    from pyluadec.lift.lift import lift_proto
    from pyluadec.lift.opcodes import Op
    # inner 捕获 a(寄存器) 与 up(外层 upvalue) → CLOSURE 后跟 MOVE + GETUPVAL 伪指令
    root = _load(
        "local up = 1\n"
        "local function outer()\n"
        "  local a = 2\n"
        "  return function() return a + up end\n"
        "end\n"
        "return outer()()\n", tmp_path)
    outer = root.subprotos[0]
    fn = lift_proto(outer)
    clo_pcs = [pc for pc, li in fn.instrs.items() if li.ri.op is Op.CLOSURE]
    assert len(clo_pcs) == 1
    li = fn.instrs[clo_pcs[0]]
    assert len(li.consumed) == outer.subprotos[0].nups == 2
    assert all(pc not in fn.instrs for pc in li.consumed)    # 伪指令 pc 不是指令
    pseudo = fn.closure_pseudo[clo_pcs[0]]
    assert {p.op for p in pseudo} <= {Op.MOVE, Op.GETUPVAL}
    moved = [p.b for p in pseudo if p.op is Op.MOVE]
    assert fn.captured_regs == frozenset(moved)
    assert frozenset(moved) <= li.effects.reads              # 捕获即读


def test_lift_rejects_truncated_code(tmp_path):
    import pytest
    from dataclasses import replace
    from pyluadec.lift.lift import LiftError, lift_proto
    p = _load("return 1", tmp_path)
    # luac 总在每个 chunk 末尾追加隐式 `RETURN 0 1`（即便已有显式 return），因此
    # "return 1" 实际编译为 3 条指令：LOADK; RETURN(显式); RETURN(隐式追加)。
    # 只砍掉最后 1 个字（隐式追加的那条）不会破坏结构——LOADK; RETURN(显式) 仍是
    # 合法的自终止程序。要真正制造"末条指令可 fallthrough 越界"的情形，须连显式
    # RETURN 一并砍掉，让 LOADK 变成末条（其后继 pc 越界）。
    with pytest.raises(LiftError):
        lift_proto(replace(p, code=p.code[:-2]))             # 砍掉末两条 RETURN → LOADK 可 fallthrough


def test_corpus_full_pc_claim_audit(corpus_dir):
    """spec §3 ③ 的认领纪律在 lift 层的前身：每个 pc 恰好被认领一次，后继全部在界内。"""
    from pyluadec.ingest import load_file
    from pyluadec.lift.lift import lift_proto
    n_fns = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            fn = lift_proto(p); n_fns += 1
            claimed = set(fn.instrs)
            for li in fn.instrs.values():
                overlap = claimed.intersection(li.consumed)
                assert not overlap, f"{f.name}: pc double-claimed {overlap}"
                claimed.update(li.consumed)
            assert claimed == set(range(1, fn.n_pcs + 1)), f"{f.name}: unclaimed pcs"
            for li in fn.instrs.values():
                for s in li.successors:
                    assert 1 <= s <= fn.n_pcs and s in fn.instrs, \
                        f"{f.name}: successor {s} invalid"
    assert n_fns == 1944

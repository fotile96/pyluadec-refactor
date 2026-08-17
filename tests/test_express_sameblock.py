"""机制 C——跨块暂存的 and/or 值语境（M7 任务 8）。

`_same_block` 是四个屏障之一，负载证明在其 docstring（执行次数正确性 +
scope 回滚）。它的严格形式把 luac 的 `and`/`or` **值**语境里处在操作数
位置的暂存值一并拒掉了：

    g(a and 1 or 2)   -- callee 在头部块暂存，链的 join 与消费 CALL 在后面的块

分类把 callee 判 local → `local l1_1 = g` → 重编译时物化 callee 被拷回调用
位（多两个 `MOVE`、maxstacksize 3→5）→ 认证失败。这正是 plan 记录的六行
（snr_graphic:main_2 / snr_memory:main_2 / snr_novel:main_2、main_3 /
snr_story_main:main_3 + 其 root）的 `mismatch: maxstacksize` 家族。

修法是**两个协同的扩展**，缺一不可（只修其一会让 local 槽位编排错位、
照样 mismatch）：

  * C1（`freereg._same_block` 的 `span` 豁免）：定义与读分处不同块时，
    若两 pc 之间的**跳转结构**不携带屏障所防的两个危险——内部分支全部
    前向且落在读之前（if 臂出口跳转/循环头跳出/FORPREP 都会越过臂内或
    体内的读，恰好被拒）、无外部分支跳入区间（phi 防护）、无包围区间
    的回边（repeat 防护）、跨度在预算内——则允许暂存。纯度**不**问：
    语料行的内部是 LT/CONCAT（STRICT 下不纯），「STRICT 纯内部」会把
    要修的行全部漏掉；而错误暂存由认证门兜底（mismatch → L1，绝不
    错发）。见 `_staging_span_ok` 的逐条论证。
  * C2（`reconstruct.cond_value`）：`CondValue` 链的结果是 region 级
    已归并的表达式（phi 已被表达式消化），当链尾到消费者读点之间同样
    无环/无臂结构时（`entry_at_r_ok=True`：落在读点上的分支是链自己的
    join，不是外部进入），整个 `a and 1 or 2` 作为暂存表达式交给消费者
    内联——`g(a and 1 or 2)` 一个 local 都不物化，这是唯一能把 callee
    留在原位重编译恒等的拼写。
"""
from __future__ import annotations

import pytest

from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source
from pyluadec.pipeline import decompile_chunk
from pyluadec.structure.structured import clear_certification_cache


def _levels_of(source: bytes) -> dict[str, str]:
    clear_certification_cache()
    root = load_bytes(compile_source(source, strip=True))
    return decompile_chunk(root).levels


_REPRO = (b"function f(a)\n"
          b"    return g(a and 1 or 2)\n"
          b"end\n")

_REPRO_SIMPLE = (b"function f(a)\n"
                 b"    return g(a and 1)\n"
                 b"end\n")

_SETTABLE = (b"function f(a, t)\n"
             b"    t.k = a and 1 or 2\n"
             b"    return t\n"
             b"end\n")

# 语料形状的合成版：callee 是闭包捕获的 upvalue（GETUPVAL，与
# snr_graphic:main_2 的 pc124 相同），链由 LT 门 + CALL 备选构成（内部
# 在 STRICT 下不纯——「纯内部」条件会漏掉这一行，故不设该条款）。
_GRAPHIC_LIKE = (b"local g2, h2\n"
                 b"g2 = function(a) return a end\n"
                 b"h2 = function(a) return a .. \"x\" end\n"
                 b"local function f(a)\n"
                 b"    return g2(a < 3 and h2(a) or a)\n"
                 b"end\n"
                 b"f = f\n")

# 多参数：callee 暂存跨链，链是中间实参（两侧都有其它暂存值）。
_ARG_MID = (b"function f(a, b)\n"
            b"    return g(b, a and 1 or 2, b)\n"
            b"end\n")


@pytest.mark.parametrize("src", [_REPRO, _REPRO_SIMPLE, _SETTABLE,
                                 _GRAPHIC_LIKE, _ARG_MID],
                         ids=["repro", "repro-simple", "settable",
                              "graphic-like", "arg-mid"])
def test_and_or_operand_positions_certify(src):
    assert _levels_of(src).get("main_0") == "L3"


# --------------------------------------------------------------------------
# 屏障仍然负载：豁免不得波及屏障存在的理由（liverange 的钉子已覆盖
# repeat/while/arm 形状，这里钉豁免自己的边界形状）。
# --------------------------------------------------------------------------
@pytest.mark.parametrize("src", [
    # 读在 if 臂内：臂的出口跳转越过读点——豁免必须拒绝，物化认证。
    b"function g2(v) return v end\n"
    b"function f(a, c)\n"
    b"    local x = a and 1 or 2\n"
    b"    if c then\n"
    b"        return g2(x)\n"
    b"    end\n"
    b"    return 0\n"
    b"end\n",
    # 读在 for 体内：FORPREP 越过体内的读——拒绝。
    b"function g2(v) return v end\n"
    b"function f(a)\n"
    b"    local x = a and 1 or 2\n"
    b"    for i = 1, 2 do\n"
    b"        g2(x)\n"
    b"    end\n"
    b"    return 0\n"
    b"end\n",
], ids=["read-in-if-arm", "read-in-for-body"])
def test_arm_and_loop_reads_still_materialize(src):
    assert _levels_of(src).get("main_0") == "L3"


# --------------------------------------------------------------------------
# 负载证明（neuter 实验）。C1 与 C2 各自必须负载：只修一边，另一边把
# local 槽位编排弄错，认证照样离开 L3。
#   - C1 neuter：callee 退回 local → `local l1_1 = g` 的额外 MOVE 回来。
#   - C2 neuter：链结果退回物化 → `local l1_2` 占槽，callee 内联后链
#     落错寄存器。
# 两次运行之间必须清认证缓存（判决是进程级 memo，键看不见分类层行为）。
# --------------------------------------------------------------------------
def test_c1_span_exemption_is_load_bearing():
    from pyluadec.express import freereg
    real = freereg._staging_span_ok
    try:
        freereg._staging_span_ok = lambda *a, **k: False
        assert _levels_of(_REPRO).get("main_0") != "L3"
    finally:
        freereg._staging_span_ok = real
    assert _levels_of(_REPRO).get("main_0") == "L3"


def test_c2_cond_value_staging_is_load_bearing():
    from pyluadec.express import reconstruct as rec
    real = rec.Reconstructor._cond_value_stages
    try:
        rec.Reconstructor._cond_value_stages = lambda self, cv: False
        assert _levels_of(_REPRO).get("main_0") != "L3"
    finally:
        rec.Reconstructor._cond_value_stages = real
    assert _levels_of(_REPRO).get("main_0") == "L3"


def test_or_chain_operand_reused_as_callee_in_loop_certifies():
    """M8 (the `snr_mainmenu:main_7` M-family): an `or` chain's operand
    register, reused after the chain as a CALLEE, must stay staged. The
    skipped-kill veto used to fire because the chain's exit jump lands on
    the FORLOOP latch, and the pc-sorted mention lists found a far read of
    the slot -- but every path from the latch (the back edge, and the loop
    exit) REWRITES the slot before any read; the value never survives the
    kill. With the veto misfiring, the operand materialized as a local and
    the callee's call-through-a-local cost a MOVE per gate site."""
    src = b"""local menu = {library = 3, novel = 5}
local function f(i, sel)
    local t = {}
    for i = 1, 4, 1 do
        if i < menu.library or i == menu.novel then
            t[i] = 1
        end
        sel(menu[i] + i, 50, 30)
    end
    return t
end
f({1, 2, 3, 4}, print)
"""
    out = _certify(src) if False else None
    from pyluadec.ingest import load_bytes
    from pyluadec.oracle import compile_source
    from pyluadec.structure.structured import certify_proto
    p = load_bytes(compile_source(src, strip=True))
    res = certify_proto(p, is_chunk_root=True)
    assert res.level == "L3", res.reason

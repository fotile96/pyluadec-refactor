"""条件重赋值家族的重建 -- M7 任务 7（机制 D，clamp/条件值形状）。

拒绝信息曾是 `reconstruct: register N is read again after its staged value
was consumed; classification called that definition a temporary`。字节码形状：

    def r; <test 读 r>; JMP; 重定义 r（不读 r）; join; 读 r

`local v = a - b  if v < 0 then v = 0 end  return v` 是语料原型
（snr_common:main_69 / snr_s5_10_s:main_42 / main_43）；同一数据流形状还覆
盖**非 TESTSET** 的 and/or 值语境（`local v = g and b`、`return g or b`）——
luac 只在首操作数已在寄存器里时才用 TESTSET，其余走 TEST/JMP + 重暂存，
此前全部拒绝（实测）。

根因在分类层：pc 线性 walk 把分支当直落。被跳过的 kill（重定义）让旧定义
看起来「恰好读一次」（条件读了它），join 读又归到新定义头上，旧定义被判
temp；重建层在 join 处发现 staged 值已被消费、又没有名字可读，拒绝。真实
luac 里一个表达式栈 temp **从不**跨过分支（分支在语句边界，此时栈已清空），
所以这个家族里的 pending 值是被错误模拟的具名局部。

修法（`express/freereg.py::_merge_veto_skipped_kill`，一条否决）：

  * 跳过杀死：pop 一个条目时，若弹出指令**不读**该寄存器（是 kill 而非
    操作数消费），且 def 与 kill 之间有 JMP 跳到 kill 之后、跳转目标之后
    对该槽的首次提及是**读**——值在跳过的路径上活着，promote 为 local。
  * 旧定义一旦 local，`write_reg` 的「`declared` 仍然获胜」闸门让 arm 内
    的重定义全部物化为赋值——**不需要**第二条对称规则（曾建的「归并读」
    否决全语料 0 差异，实测后删除，见 freereg.py 的记录）。

and/or 条件链（`if a and b then`）与 TESTSET 值链不受影响：前者的 join 不
再读该寄存器（分支决定已在 TEST 处做出，「首次提及是读」不成立）；后者
的条目本就因零读被判 local（TESTSET 不读自己写的槽）。语料实测见任务提
交：只升不降。

**已知缺口**（区域路线，不属本任务的分类修法）：then 臂 RHS 是寄存器暂存
表达式（NEWTABLE/CALL）时 if 形式不恒等——见下方
test_and_value_in_call_argument_position_is_a_known_gap 的分析。
"""
from __future__ import annotations

import pytest

from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source
from pyluadec.pipeline import decompile_chunk


def _levels_of(source: bytes) -> dict[str, str]:
    root = load_bytes(compile_source(source, strip=True))
    return decompile_chunk(root).levels


_CLAMP = (b"function f(a, b)\n"
          b"    local v = a - b\n"
          b"    if v < 0 then\n"
          b"        v = 0\n"
          b"    end\n"
          b"    return v\n"
          b"end\n")

_CLAMP_GLOBAL_BOUND = (b"function f(a, b, lim)\n"
                       b"    local v = a - b\n"
                       b"    if v < lim then\n"
                       b"        v = lim\n"
                       b"    end\n"
                       b"    return v\n"
                       b"end\n")

_TEST_REASSIGN = (b"g = g or {}\n"
                  b"function f(a, b)\n"
                  b"    local v = a\n"
                  b"    if v then\n"
                  b"        v = b\n"
                  b"    end\n"
                  b"    return v\n"
                  b"end\n")

_AND_VALUE_GLOBAL = (b"g = 1\n"
                     b"function f(b)\n"
                     b"    local v = g and b\n"
                     b"    return v\n"
                     b"end\n")

_OR_RETURN = (b"g = 1\n"
              b"function f(b)\n"
              b"    return g or b\n"
              b"end\n")

_AND_ARG = (b"g = g or {}\n"
            b"f2 = f2 or print\n"
            b"function f(b)\n"
            b"    return f2(g and b)\n"
            b"end\n")

# 已知缺口（区域路线，不属本任务的分类修法）：and/or 值处在**调用实参**位
# 置时，if 形式的 local 物化会移动后续暂存（`local l0_2 = g; if l0_2 then
# l0_2 = b end; return f2(l0_2)` 重编译后 f2 的暂存槽位改变，maxstacksize/
# code 失配）——只有表达式形 `f2(g and b)` 能重编译恒等，而那需要
# `CondValue` 认识非 TESTSET 开头（`_match_cond_value` 只认 TESTSET 与
# gate→TESTSET 两种开头）。当前实测 mismatch: maxstacksize，与语料无关
# （三个 exemplar 行都是语句位 clamp，见下）。钉住现状，防止将来无声变化。
def test_and_value_in_call_argument_position_is_a_known_gap():
    assert _levels_of(_AND_ARG).get("main_0") == "L1"

_CLAMP_EXPR_JOIN = (b"function f(a, b)\n"
                    b"    local v = a - b\n"
                    b"    if v < 0 then\n"
                    b"        v = 0\n"
                    b"    end\n"
                    b"    return v + 1\n"
                    b"end\n")

_CLAMP_NONLITERAL_ALT = (b"function f(a, b, c)\n"
                         b"    local v = a - b\n"
                         b"    if v < c then\n"
                         b"        v = c\n"
                         b"    end\n"
                         b"    return v\n"
                         b"end\n")

# join 之后还有对该槽的继续使用（v 被读多次，但都在 join 之后）。
_CLAMP_THEN_USE = (b"function f(a, b)\n"
                   b"    local v = a - b\n"
                   b"    if v < 0 then\n"
                   b"        v = 0\n"
                   b"    end\n"
                   b"    v = v + 2\n"
                   b"    return v\n"
                   b"end\n")


@pytest.mark.parametrize("src", [
    _CLAMP,
    _CLAMP_GLOBAL_BOUND,
    _TEST_REASSIGN,
    _AND_VALUE_GLOBAL,
    _OR_RETURN,
    _CLAMP_EXPR_JOIN,
    _CLAMP_NONLITERAL_ALT,
    _CLAMP_THEN_USE,
], ids=["clamp-literal", "clamp-bound-reg", "test-reassign",
        "and-value-global", "or-return",
        "clamp-expr-join", "clamp-nonliteral-alt", "clamp-then-use"])
def test_conditional_reassignment_family_certifies(src):
    assert _levels_of(src).get("main_0") == "L3"


# and/or 的既有认证通道不得被两条否决波及：TESTSET 值链与 if 条件链保持
# 表达式形态（认证等级不变即是回归的充分信号——文本形态由
# test_express_testset / test_sir_condtree 守护）。
@pytest.mark.parametrize("src", [
    b"function f(a, b)\n    local v = a and b\n    return v\nend\n",
    b"function f(a, b)\n    local v = a or b\n    return v\nend\n",
    b"a = a or {}\nb = b or {}\nfunction f()\n    if a and b then\n"
    b"        return 1\n    end\n    return 0\nend\n",
    b"a = a or {}\nb = b or {}\nc = c or {}\nfunction f()\n"
    b"    if a and b or c then\n        return 1\n    end\n    return 0\nend\n",
], ids=["testset-and", "testset-or", "cond-chain-and", "cond-chain-and-or"])
def test_and_or_expression_channels_stay_certified(src):
    assert _levels_of(src).get("main_0") == "L3"


# --------------------------------------------------------------------------
# 否决的负载证明（neuter 实验）：neuter 后 clamp-literal 必须离开 L3，恢复
# 后回到 L3（kill 是 LOADK，读不到 r；失去否决时旧定义退回 temp，join 处
# staged 值已被条件消费——正是本家族的原始拒绝）。
#
# 两次运行之间必须 `clear_certification_cache()`：`certify_proto` 的判决是
# 进程级 memo，键只含 (oracle identity, shash, debug fingerprint)，看不见
# 分类层的行为——neuter 运行写下的 L1 会让恢复后的运行读到毒化条目（同样
# 地，先前家族用例写下的 L3 会让 neuter 运行假绿）。
# --------------------------------------------------------------------------
def _fresh_levels(src: bytes) -> dict[str, str]:
    from pyluadec.structure.structured import clear_certification_cache
    clear_certification_cache()
    return _levels_of(src)


def test_skipped_kill_veto_is_load_bearing():
    from pyluadec.express import freereg
    real = freereg._merge_veto_skipped_kill
    try:
        freereg._merge_veto_skipped_kill = lambda *a, **k: False
        assert _fresh_levels(_CLAMP).get("main_0") != "L3"
    finally:
        freereg._merge_veto_skipped_kill = real
    assert _fresh_levels(_CLAMP).get("main_0") == "L3"


# 窄度注入（plan Task 7 Step 4 的另一半）：join 之后**没有**对槽的读时，
# 否决不得发火——被跳过的 kill 后面没有任何消费者，旧定义在两条路径上都
# 死透了，temp 判定是对的。这个形状因此以条件表达式形认证（`if a - b < 0
# then local l1_2 = 0 end`），而不是物化 `local`。若否决在这里也发火，它
# 就不是「值在跳过的路径上活着」而是「跳过存在即发火」——过宽。
def test_veto_is_narrow_no_read_after_the_join():
    src = (b"function f(a, b)\n"
           b"    local v = a - b\n"
           b"    if v < 0 then\n"
           b"        v = 0\n"
           b"    end\n"
           b"    return a\n"
           b"end\n")
    assert _levels_of(src).get("main_0") == "L3"

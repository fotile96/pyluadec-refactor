# Phase 3 (M3 结构化主干) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用支配树驱动的区域识别 + 证明门控的表达式重建，把直线代码、无环分支（if/else、and/or）与数值/泛型 for 循环从 fallback 状态机换成结构化 Lua，并用 L3 重编译比对逐函数认证——出口是**多数 unique proto 达到 L3（proved）**，其余诚实留在 fallback（L1）。

**Architecture:** 三层落地 spec §3/§4 的 ③structure（SIR 区域树，支配树识别 + PC 认领审计）、④express（寄存器→表达式树，活跃性证明门控的保守内联，首次让 `lift/effects.py` 公理层成为承重件）、⑥print（AST→Lua 源码）。每个函数走 `emit_structured → 重编译 → L3.1 归一化比对`：比对干净即认证 L3、脱离 fallback；比对脏或结构化失败即回落状态机、记 confession。**验证门（certify）是唯一落地关口**——错误的区域识别或内联不会产出错误代码，只会让该函数停在 L1，与 spec §4「验证门是唯一落地关口」一致。

**Tech Stack:** Python ≥3.12（uv），pytest。复用 Phase 1/2 全部产物：`pyluadec.ingest`、`pyluadec.lift`（`lift_proto`/`Op`/`RawInstr`/`analyze`/`EffectMode`/`Effect`）、`pyluadec.cfg`（`build_cfg`/`immediate_dominators`/`dom_tree`/`dominates`）、`pyluadec.verify.normalize`（L3.0 比对器）、`pyluadec.verify.ledger`、`pyluadec.oracle`、`pyluadec.structure.fallback`。无新第三方依赖。

## Global Constraints

- 代码中禁止绝对路径；语料一律经 `PYLUADEC_CORPUS_DIR`（依赖语料的测试无此变量时 `pytest.skip`）；构建产物经 `PYLUADEC_BUILD_DIR`（默认 `build/`）。
- 一切源自 bytecode 的字符串在 Python 侧一律 `bytes`，绝不 decode（打印层转义时才按字节展开）；数字常量携带原始 8 字节 payload，比较逐位。
- `corpus/golden/` 只读；`vendor/` pristine；一切 Lua 源修改经 `native/patches/*.patch`。
- 每个 Task 以 commit 结束；测试统一 `uv run pytest`，跑语料相关时必须带 `PYLUADEC_CORPUS_DIR`（否则 M3 出口门与语料认证静默 skip，见 `tests/conftest.py` 的醒目 skip 横幅——那是 Phase 2 装的，别拆）。
- PC 全程 **1-based**（与 luac listing 一致）。
- **认证纪律（spec §5，ratchet）**：等级只升不降；`corpus/ledger.jsonl` 只由 `scripts/run_corpus.py` 整体再生后提交，禁止手编；台账是其生成脚本的**不动点**（`tests/test_ledger_ratchet.py::test_ledger_is_a_reproducible_fixed_point` 守护，M3 改了 emit/express/ledger 后此门必须仍绿）；`oracle` 字段是 `git log -1 --format=%H -- vendor native`（oracle 构建溯源），不是 repo HEAD。
- **归一化健全性纪律（spec §5, §9 R3）**：归一化阶梯每加一级必须单独论证健全性 + 版本化 `LADDER_VERSION`；比对器用自造正负例测（同源两编=正例，微改源码=负例），做严宁可误拒（函数停在 L1），绝不做松放过语义 bug。
- **结构化 emitter 绝不猜（confess, don't guess，继承 Phase 2 纪律）**：任何区域识别不了 / 内联证明不出 / 认证不过的函数，整函数回落 `structure.fallback.emit_chunk`（语义精确的状态机），不得发射未经认证的结构化代码。

## 语料实测事实（2026-08-10 扫描 1478 unique proto，本计划的定量依据）

控制流形态分布（按 unique 结构哈希去重）：

| 类别 | unique proto | 占比 |
|---|---|---|
| 直线（1 个可达基本块） | 951 | 64.3% |
| 无环多块（纯 if/else，无回边） | 332 | 22.5% |
| 数值/泛型 for（回边仅来自 FORLOOP/TFORLOOP） | 43 | 2.9% |
| 含 while/repeat 或混合/不可归约回边 | 152 | 10.3% |

**子树闭合覆盖上界**（一个 proto 只有当它自己及其全部子闭包都能结构化时才能整体脱离 fallback——CLOSURE 子 proto 也必须结构化）：

| 能力集 | 子树闭合可结构化 | 占比 |
|---|---|---|
| 仅直线 | 785 | 53.1% |
| + 无环 if/else | 1147 | **77.6%** |
| + for 循环 | 1187 | 80.3% |
| + while/repeat/混合 | 1478 | 100% |

**结论**：本计划目标能力集 = 直线 + 无环 if/else + 数值/泛型 for，子树闭合上界 **80.3%**。出口门「多数 unique proto 达 L3」（>50%）由此有充裕余量；while/repeat/混合循环的 152 个（连同它们的祖先闭包）诚实留在 fallback，是 M3 之后的增量，**不是** M3 失败。

**核心假设已实测证实**：寄存器重建为具名局部 + staging 值内联进消费者，重编译后与原 proto **逐字节一致**（行信息归一化后）。7/7 手工样例通过，含：多次赋值的局部、if/else 单比较、自递归 `local function`、闭包捕获、表构造 `{1,2,3}`、主 chunk vararg 转发、开放多返回值调用链。这是 L3 认证可行的地基——错误的重建重编译后必然发散，被认证门挡下。

**表达式重建的定量约束**：直线 proto 中 714/951 存在被多次写的寄存器（即同一寄存器在函数内被重新赋值），故不能用朴素 SSA「一寄存器一 local」——必须区分「跨语句活跃 / 多次赋值 / 被捕获」的**局部变量**（发 `local`，可重新赋值）与「单次定义单次使用的纯 staging 值」的**临时值**（内联进消费者，不落地为 local）。这个区分正是 spec §4「内联需活跃性证明」，且是重编译能否字节一致的关键：把 staging 临时值错发成 local 会改变寄存器分配与 maxstacksize，认证立刻失败。

**effects 公理层在 M3 首次承重**：内联安全性判定读 `InstrEffects.reads/writes/may_error`（单定义、单使用、消费前无对其输入的写、无跨越副作用重排风险）。Phase 2 final review 记录 effects 字段「computed but unread」——M3 消除该状态。

**M4 边界（本计划显式不做）**：spec 的 M4「证明门控内联」指**效应格三档标定后的完整内联**（放开 READ_HEAP/元方法风险重排）。M3 只做**无条件健全的保守内联**——单定义单使用、消费者是紧邻或支配路径唯一使用点、且内联不跨越对其输入寄存器的写或对其可能读到的堆状态的写。保守内联足以让目标能力集重编译字节一致（已实测）；把完整效应格内联留给 M4。

## 文件结构

```
src/pyluadec/
├── sir/                      # ③ 结构化中间表示（区域树）
│   ├── __init__.py           #   公开 re-export
│   ├── regions.py            #   区域 frozen dataclass（Seq/If/NumericFor/GenericFor/Break/Return/Fallback）+ claimed_pcs
│   └── build.py              #   支配树驱动的区域识别 + PC 认领审计（build_sir）
├── express/                  # ④ 表达式重建（证明门控内联）
│   ├── __init__.py
│   ├── expr.py               #   表达式 AST（Const/Local/Global/Index/BinOp/UnOp/Call/... frozen）
│   ├── names.py              #   局部/临时分类 + 名字合成（classify_registers, name_for）
│   └── reconstruct.py        #   LIR → 语句/表达式（reconstruct_region），effects 门控内联，表构造重建
├── emit/                     # ⑥ 打印
│   ├── __init__.py
│   └── lua.py                #   SIR + Expr → Lua 源码（print_function）
├── structure/
│   ├── fallback.py           #   （已有，不动）
│   └── structured.py         #   新：emit_structured(proto) -> bytes | None，串起 sir+express+emit
└── verify/
    ├── normalize.py          #   改：加 L3.1 剥行信息归一化级，bump LADDER_VERSION
    ├── ledger.py             #   （已有）
    └── certify.py            #   新：certify_l3(original, structured_src) -> CertResult
tests/
├── synth.py                  # 手搓 Proto/RawInstr/Cfg 的测试夹具（backlog item 4）
└── test_*.py
scripts/
├── run_corpus.py             #   改：逐函数试结构化→认证→回落，台账记 L3/L1
├── ledger_dashboard.py       #   改：按等级分列、点名 L0/未认证
└── probe_global_state.py     #   新：L1.5 全局状态探针（backlog item 3）
```

---

### Task 0: L3.1 归一化级（剥行信息）+ 认证门 certify_l3

**Files:**
- Modify: `src/pyluadec/verify/normalize.py`
- Create: `src/pyluadec/verify/certify.py`
- Test: `tests/test_normalize_l31.py`, `tests/test_certify.py`

**Interfaces:**
- Consumes: `pyluadec.ingest`（`load_bytes`, `Proto`）；`pyluadec.oracle`（`compile_source`, `LuaCompileError`）；`pyluadec.verify.normalize`（`compare_protos`, `Mismatch`, `NORMALIZATIONS`, `normalize`）。
- Produces（后续全部 Task 依赖）:
  - `normalize.py`: `NORMALIZATIONS` 增加一项 `("strip-lineinfo", _strip_lineinfo)`；`LADDER_VERSION` 从 `"l3-ladder-v0"` → `"l3-ladder-v1"`。`_strip_lineinfo(p: Proto) -> Proto` 递归把 `source=None, linedefined=0, lastlinedefined=0, lineinfo=(), locvars=(), upvalues=(名字全部置 None 但保留长度)` —— 只剥 debug 段，**不动** code/constants/nups/numparams/is_vararg/maxstacksize/subprotos 结构。
  - `certify.py`:
    - `@dataclass(frozen=True) CertResult: level: str; rung: int | None; mismatches: tuple[Mismatch, ...]`（`level ∈ {"L3","L1"}`；`rung` 是通过的归一化级号，L1 时为 None）
    - `certify_l3(original: Proto, structured_src: bytes) -> CertResult`：把 `structured_src` 用 `oracle.compile_source(..., strip=True)` 重编译（失败→L1，mismatches 空）、`load_bytes` 得 proto、在归一化阶梯上从 0 升到 `len(NORMALIZATIONS)` 逐级 `compare_protos(original, recompiled, level=k)`，第一个返回空 mismatch 的级即认证 L3 且 `rung=k`；全部级都不空→L1，`mismatches` 取最高级（信息最全）的结果。

- [ ] **Step 1: 写 L3.1 归一化级失败测试**

`tests/test_normalize_l31.py`：

```python
def _bc(src: str):
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode(), strip=True), chunkname="=t")


def test_ladder_version_bumped():
    from pyluadec.verify.normalize import LADDER_VERSION, NORMALIZATIONS
    assert LADDER_VERSION == "l3-ladder-v1"
    assert len(NORMALIZATIONS) == 1
    assert NORMALIZATIONS[0][0] == "strip-lineinfo"


def test_l30_sees_line_layout_l31_does_not():
    from pyluadec.verify.normalize import compare_protos
    a, b = _bc("print(1)"), _bc("\n\n\nprint(1)")
    assert compare_protos(a, b, level=0) != []          # L3.0 strict: line info differs
    assert compare_protos(a, b, level=1) == []           # L3.1: line info stripped → equal


def test_l31_still_catches_real_difference():
    from pyluadec.verify.normalize import compare_protos
    # different constants must NOT be normalized away at L3.1
    assert compare_protos(_bc("return 1"), _bc("return 2"), level=1) != []
    assert compare_protos(_bc("return 0.0"), _bc("return -0.0"), level=1) != []  # payload-exact survives
    # different code
    assert compare_protos(_bc("local a=1 return a"), _bc("return 1"), level=1) != []


def test_l31_strips_locvar_and_upvalue_names_but_keeps_counts():
    # non-stripped compile carries locvar/upvalue names; L3.1 must ignore names, keep structure
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.verify.normalize import compare_protos
    a = load_bytes(oracle.compile_source(b"local x = 1 local function f() return x end return f()"))
    b = load_bytes(oracle.compile_source(b"local y = 1 local function g() return y end return g()"))
    # different local/upvalue NAMES, identical structure → L3.0 differs (names in locvars), L3.1 equal
    assert compare_protos(a, b, level=0) != []
    assert compare_protos(a, b, level=1) == []


def test_bad_level_still_raises():
    import pytest
    from pyluadec.verify.normalize import normalize
    with pytest.raises(ValueError):
        normalize(_bc("return 1"), level=99)
```

Run: `uv run pytest tests/test_normalize_l31.py -v` → FAIL

- [ ] **Step 2: 实现 L3.1 级**

`src/pyluadec/verify/normalize.py` —— 在 `LADDER_VERSION` 上方加：

```python
def _strip_lineinfo(p: Proto) -> Proto:
    import dataclasses
    return dataclasses.replace(
        p,
        source=None,
        linedefined=0,
        lastlinedefined=0,
        lineinfo=(),
        locvars=tuple(dataclasses.replace(v, name=None) for v in p.locvars),
        upvalues=tuple(None for _ in p.upvalues),      # drop names, keep count
        subprotos=tuple(_strip_lineinfo(s) for s in p.subprotos),
    )
```

改 `NORMALIZATIONS` 与 `LADDER_VERSION`：

```python
NORMALIZATIONS: tuple[tuple[str, Callable[[Proto], Proto]], ...] = (
    ("strip-lineinfo", _strip_lineinfo),
)
LADDER_VERSION = "l3-ladder-v1"
```

（`_cmp` 已比较 `source/lineinfo/locvars/upvalues`——L3.1 归一化后这些都被抹平，故 L3.1 只看结构字段。`locvars` 的 `LocVar` 有 `startpc/endpc`：本语料它们恒空，但 `_strip_lineinfo` 只置 `name=None` 保留 pc 区间，因为 pc 区间是作用域结构不是纯 debug——若将来非 strip 编译带作用域，保留它是对的。）

Run: `uv run pytest tests/test_normalize_l31.py -v` → PASS

- [ ] **Step 3: 写认证门失败测试**

`tests/test_certify.py`：

```python
def _proto(src: str):
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode(), strip=True))


def test_identical_source_certifies_l3_at_rung1():
    from pyluadec.verify.certify import certify_l3
    src = b"local a = 1 local b = 2 return a + b"
    r = certify_l3(_proto(src.decode()), src)
    assert r.level == "L3" and r.rung == 1 and r.mismatches == ()


def test_line_only_difference_still_certifies_l3():
    from pyluadec.verify.certify import certify_l3
    orig = _proto("print(1)")
    r = certify_l3(orig, b"\n\n\nprint(1)")         # same bytecode, different lines → L3 at rung 1
    assert r.level == "L3" and r.rung == 1


def test_semantic_difference_is_l1():
    from pyluadec.verify.certify import certify_l3
    r = certify_l3(_proto("return 1"), b"return 2")
    assert r.level == "L1" and r.rung is None and r.mismatches != ()


def test_uncompilable_structured_source_is_l1():
    from pyluadec.verify.certify import certify_l3
    r = certify_l3(_proto("return 1"), b"this is not ) valid lua (")
    assert r.level == "L1" and r.rung is None


def test_reconstructed_shape_certifies_l3():
    # the M3 hypothesis: register-as-local reconstruction round-trips
    from pyluadec.verify.certify import certify_l3
    orig = _proto("local a = 1 a = a + 1 print(a)")
    recon = b"local l0_0 = 1\nl0_0 = l0_0 + 1\nprint(l0_0)\n"
    r = certify_l3(orig, recon)
    assert r.level == "L3", r.mismatches
```

Run: `uv run pytest tests/test_certify.py -v` → FAIL

- [ ] **Step 4: 实现 `src/pyluadec/verify/certify.py`**

```python
"""L3 认证门（spec §5）：结构化产物重编译 → 归一化阶梯逐级比对 → 通过即 proved。"""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec import oracle
from pyluadec.ingest import Proto, load_bytes

from .normalize import NORMALIZATIONS, Mismatch, compare_protos


@dataclass(frozen=True)
class CertResult:
    level: str                       # "L3" | "L1"
    rung: int | None                 # normalization level that passed, or None
    mismatches: tuple[Mismatch, ...]


def certify_l3(original: Proto, structured_src: bytes) -> CertResult:
    try:
        recompiled = load_bytes(oracle.compile_source(structured_src, strip=True))
    except oracle.LuaCompileError:
        return CertResult(level="L1", rung=None, mismatches=())
    last: list[Mismatch] = []
    for k in range(len(NORMALIZATIONS) + 1):
        diffs = compare_protos(original, recompiled, level=k)
        if not diffs:
            return CertResult(level="L3", rung=k, mismatches=())
        last = diffs
    return CertResult(level="L1", rung=None, mismatches=tuple(last))
```

Run: `uv run pytest tests/test_certify.py tests/test_normalize_l31.py -v` → PASS

- [ ] **Step 5: 确认既有台账不动点门仍绿（LADDER_VERSION 变了但 emit 未变，ledger 只在 Task 8 重生成）**

Run: `PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/script_to_decompile uv run pytest -q`
Expected: 全绿。**注意**：`corpus/ledger.jsonl` 里每条的 `ladder` 字段仍是 `l3-ladder-v0`，而 `LADDER_VERSION` 现在是 `l3-ladder-v1`——`tests/test_ledger_ratchet.py` 不比较 `ladder` 常量（它只查不动点与不变量），故此刻仍绿；台账的 `ladder` 字段会在 Task 8 随 `run_corpus.py` 整体重生成时更新到 v1。若发现某测试硬断言 ledger 的 `ladder == "l3-ladder-v0"`，那是 Phase 2 遗留的过紧断言，改为 `== LADDER_VERSION` 并在 commit message 说明。

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: L3.1 line-info normalization rung and certify_l3 proof gate"
```

---

### Task 1: SIR 区域数据类 + 测试夹具 synth.py

**Files:**
- Create: `src/pyluadec/sir/__init__.py`, `src/pyluadec/sir/regions.py`, `tests/synth.py`
- Test: `tests/test_sir_regions.py`

**Interfaces:**
- Consumes: `pyluadec.lift`（`LirInstr`, `RawInstr`, `Op`, `decode`）；`pyluadec.ingest`（`Proto`, `LuaNumber`）；`pyluadec.cfg`（`BasicBlock`, `Cfg`）。
- Produces:
  - `regions.py`（全部 frozen dataclass，字段 `claimed_pcs: frozenset[int]` 是该区域**直接**认领的 pc；子区域的 pc 不重复计入父的 `claimed_pcs`，全树认领 = 各区域 `claimed_pcs` 的**不相交并集**）:
    - `Seq(body: tuple[Region, ...], claimed_pcs)` —— 顺序块；`claimed_pcs` 恒为空（认领委托给 body）
    - `Straight(instrs: tuple[LirInstr, ...], claimed_pcs)` —— 直线指令序列（叶子），`claimed_pcs` = 这些指令的 pc
    - `If(cond_pcs: frozenset[int], cond: LirInstr, negated: bool, then_body: Region, else_body: Region | None, join_pc: int, claimed_pcs)` —— `cond` 是比较/测试指令，`claimed_pcs` = `cond_pcs`（比较指令 + 其后随 JMP）
    - `NumericFor(prep: LirInstr, loop: LirInstr, body: Region, claimed_pcs)` —— `claimed_pcs` = {FORPREP.pc, FORLOOP.pc}
    - `GenericFor(call: LirInstr, loop: LirInstr, body: Region, claimed_pcs)` —— `call`=TFORLOOP，`loop`=其后随 JMP；`claimed_pcs`={TFORLOOP.pc, JMP.pc}
    - `Break(claimed_pcs)` —— 单条 JMP 跳出循环，`claimed_pcs`={该 JMP.pc}
    - `Return(instr: LirInstr, claimed_pcs)` —— RETURN/TAILCALL 叶子
    - `Fallback(instrs: tuple[LirInstr, ...], claimed_pcs)` —— 整函数降级标记，`claimed_pcs`=全部 pc
    - `Region = Seq | Straight | If | NumericFor | GenericFor | Break | Return | Fallback`（类型别名）
    - `all_claimed(r: Region) -> frozenset[int]`：递归收集全树 `claimed_pcs`，**若任意两子区域 claimed_pcs 相交则 raise `RegionOverlap`**
    - `class RegionOverlap(Exception)`
  - `tests/synth.py`（测试夹具，非生产代码）:
    - `mk_instr(op, a=0, b=0, c=0, *, bx=None, sbx=None, pc=1) -> RawInstr`：按字段编码指令字再 `decode`
    - `mk_proto(code_words, *, constants=(), numparams=0, is_vararg=0, maxstacksize=2, nups=0, subprotos=()) -> Proto`：手搓 Proto（用于测 SIR/emit 无法从 luac 逼出的形态）
    - `mk_cfg(edges: dict[int, tuple[int,...]], entry=1) -> Cfg`：从邻接表搓 Cfg（instrs 空，测纯图算法）

- [ ] **Step 1: 写区域认领审计失败测试**

`tests/test_sir_regions.py`：

```python
def test_claimed_pcs_disjoint_union():
    from pyluadec.sir.regions import Straight, Seq, all_claimed
    from tests.synth import mk_instr
    from pyluadec.lift import LirInstr
    from pyluadec.lift.effects import analyze, EffectMode
    def li(pc):
        ri = mk_instr(0, pc=pc)   # MOVE
        return LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT),
                        successors=(pc+1,), consumed=())
    seq = Seq(body=(Straight((li(1), li(2)), frozenset({1, 2})),
                    Straight((li(3),), frozenset({3}))), claimed_pcs=frozenset())
    assert all_claimed(seq) == frozenset({1, 2, 3})


def test_overlap_is_hard_fail():
    import pytest
    from pyluadec.sir.regions import Straight, Seq, all_claimed, RegionOverlap
    from tests.synth import mk_instr
    from pyluadec.lift import LirInstr
    from pyluadec.lift.effects import analyze, EffectMode
    def li(pc):
        ri = mk_instr(0, pc=pc)
        return LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT), successors=(pc+1,), consumed=())
    bad = Seq(body=(Straight((li(1),), frozenset({1})),
                    Straight((li(1),), frozenset({1}))), claimed_pcs=frozenset())
    with pytest.raises(RegionOverlap):
        all_claimed(bad)


def test_synth_mk_instr_roundtrips_fields():
    from tests.synth import mk_instr
    from pyluadec.lift import Op
    ri = mk_instr(Op.LOADK, a=2, bx=5, pc=7)
    assert ri.op is Op.LOADK and ri.a == 2 and ri.bx == 5 and ri.pc == 7
    ri = mk_instr(Op.JMP, sbx=-3, pc=10)
    assert ri.op is Op.JMP and ri.sbx == -3


def test_synth_mk_proto_lifts():
    from tests.synth import mk_proto, mk_instr
    from pyluadec.lift import lift_proto, Op
    # RETURN 0 1  (return with no values) — a valid 1-instruction proto
    p = mk_proto([mk_instr(Op.RETURN, a=0, b=1).word])
    fn = lift_proto(p)
    assert fn.n_pcs == 1 and fn.instrs[1].ri.op is Op.RETURN
```

Run: `uv run pytest tests/test_sir_regions.py -v` → FAIL

- [ ] **Step 2: 实现 `tests/synth.py`**

```python
"""Hand-built Proto/RawInstr/Cfg fixtures for testing shapes luac won't emit.

Instruction word layout (lopcodes.h): op:6 | A:8 | C:9 | B:9 ; Bx = bits 14..31.
"""
from __future__ import annotations

from pyluadec.cfg.blocks import BasicBlock, Cfg
from pyluadec.ingest.proto import Proto
from pyluadec.lift.opcodes import MAXARG_sBx, Op, RawInstr, decode


def _encode(op, a, b, c, bx, sbx) -> int:
    opn = int(op)
    if bx is not None:
        return opn | (a << 6) | (bx << 14)
    if sbx is not None:
        return opn | (a << 6) | ((sbx + MAXARG_sBx) << 14)
    return opn | (a << 6) | (c << 14) | (b << 23)


def mk_instr(op, a=0, b=0, c=0, *, bx=None, sbx=None, pc=1) -> RawInstr:
    return decode(_encode(op, a, b, c, bx, sbx), pc=pc)


def mk_proto(code_words, *, constants=(), numparams=0, is_vararg=0,
             maxstacksize=2, nups=0, subprotos=()) -> Proto:
    return Proto(
        source=None, linedefined=0, lastlinedefined=0, nups=nups,
        numparams=numparams, is_vararg=is_vararg, maxstacksize=maxstacksize,
        code=tuple(code_words), constants=tuple(constants), lineinfo=(),
        locvars=(), upvalues=tuple(None for _ in range(nups)),
        subprotos=tuple(subprotos))


def mk_cfg(edges: dict[int, tuple[int, ...]], entry: int = 1) -> Cfg:
    blocks = {s: BasicBlock(s, (), t) for s, t in edges.items()}
    preds: dict[int, list[int]] = {s: [] for s in edges}
    for s, ts in edges.items():
        for t in ts:
            preds[t].append(s)
    return Cfg(entry=entry, blocks=blocks,
               preds={k: tuple(sorted(v)) for k, v in preds.items()})
```

（`mk_proto` 的字段顺序须与 `pyluadec.ingest.proto.Proto` 一致——实施时打开 `proto.py` 核对；若 `Proto` 字段有变，以 `proto.py` 为准。）

- [ ] **Step 3: 实现 `src/pyluadec/sir/regions.py`**

```python
"""SIR region tree (spec §3 layer ③). Frozen; claimed_pcs are a disjoint partition of the function's pcs."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.lift.lift import LirInstr


class RegionOverlap(Exception):
    pass


@dataclass(frozen=True)
class Straight:
    instrs: tuple[LirInstr, ...]
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Seq:
    body: tuple["Region", ...]
    claimed_pcs: frozenset[int]      # always empty; claiming delegated to body


@dataclass(frozen=True)
class If:
    cond: LirInstr
    negated: bool
    then_body: "Region"
    else_body: "Region | None"
    join_pc: int
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class NumericFor:
    prep: LirInstr
    loop: LirInstr
    body: "Region"
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class GenericFor:
    call: LirInstr                   # TFORLOOP
    loop: LirInstr                   # trailing JMP
    body: "Region"
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Break:
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Return:
    instr: LirInstr
    claimed_pcs: frozenset[int]


@dataclass(frozen=True)
class Fallback:
    instrs: tuple[LirInstr, ...]
    claimed_pcs: frozenset[int]


Region = Straight | Seq | If | NumericFor | GenericFor | Break | Return | Fallback

_CHILDREN = {
    Seq: lambda r: r.body,
    If: lambda r: (r.then_body,) + ((r.else_body,) if r.else_body is not None else ()),
    NumericFor: lambda r: (r.body,),
    GenericFor: lambda r: (r.body,),
}


def all_claimed(r: Region) -> frozenset[int]:
    acc = set(r.claimed_pcs)
    for child in _CHILDREN.get(type(r), lambda _: ())(r):
        cc = all_claimed(child)
        if acc & cc:
            raise RegionOverlap(f"pcs {sorted(acc & cc)} claimed by more than one region")
        acc |= cc
    return frozenset(acc)
```

`src/pyluadec/sir/__init__.py`：

```python
from .regions import (Break, Fallback, GenericFor, If, NumericFor, Region,
                      RegionOverlap, Return, Seq, Straight, all_claimed)

__all__ = ["Break", "Fallback", "GenericFor", "If", "NumericFor", "Region",
           "RegionOverlap", "Return", "Seq", "Straight", "all_claimed"]
```

Run: `uv run pytest tests/test_sir_regions.py -v` → PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: SIR region dataclasses with disjoint pc-claim audit + synth fixtures"
```

---

### Task 2: 区域识别（直线 + 无环 if/else）+ PC 认领审计

**Files:**
- Create: `src/pyluadec/sir/build.py`
- Modify: `src/pyluadec/sir/__init__.py`
- Test: `tests/test_sir_build_acyclic.py`

**Interfaces:**
- Consumes: `pyluadec.lift`（`lift_proto`, `LirFunction`, `Op`）；`pyluadec.cfg`（`build_cfg`, `immediate_dominators`, `dominates`, `dom_tree`）；Task 1 regions。
- Produces:
  - `class StructureError(Exception)` —— 区域识别放弃（调用方据此回落 Fallback）
  - `build_sir(fn: LirFunction) -> Region`：把 `LirFunction` 结构化成区域树。**只处理**：单出口直线块（→Straight/Seq）、if/else 菱形（→If）。遇到回边、无法认领的 pc、或任何不认识的控制转移，raise `StructureError`。返回前用 `all_claimed(tree) == set(fn.instrs)` 断言（不等或 `RegionOverlap` → `StructureError`），把 PC 认领纪律钉死在构造出口。
  - `has_back_edge(fn) -> bool`（helper，Task 3 也用）

**识别算法**（本 Task 只到无环；Task 3 扩循环）：

顺着 CFG 用支配树识别 if/else 菱形。核心判据（对每个双后继的比较块 `b`，后继 `t=pc+1`（落入后随 JMP 那条）与 `e=pc+2`）：

- 比较指令 `EQ/LT/LE/TEST/TESTSET` 后必跟一条 JMP（luac codegen 恒真——本语料实测，识别时校验，否则 `StructureError`）。设该 JMP 目标为 `jt`。则 `then` 分支体 = 从 `pc+2`（跳过 JMP）到 `jt` 之前的区间被 `b` 支配的块；`else` 分支体 = 从 `jt` 到 join 的区间。join = `then`/`else` 的直接公共支配后继（两分支后继汇合处，用 `immediate_dominators` 找）。
- 无 else（`if ... then ... end`）：`jt` 直接就是 join，`else_body=None`。
- 递归：每个分支体自身再 `build_sir`（分区间调用）。
- **保守**：任何分支体不是被条件块单入口支配的连续 pc 区间（交叉跳转、分支互跳、`goto`-风格）→ `StructureError`，整函数回落。这是「宁可回落不猜」。

实现建议按「区间 + 支配」递归，而非全局模式匹配：`_structure_range(fn, cfg, idoms, lo, hi) -> Region` 处理 pc 区间 `[lo, hi)`，遇比较块分叉、遇顺序块串成 Seq。

- [ ] **Step 1: 写无环结构化失败测试**

`tests/test_sir_build_acyclic.py`：

```python
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return lift_proto(load_file(o))


def _claims_all(region, fn):
    from pyluadec.sir import all_claimed
    return all_claimed(region) == set(fn.instrs)


def test_straight_line_is_seq_of_straight(tmp_path):
    from pyluadec.sir import Seq, Straight
    from pyluadec.sir.build import build_sir
    fn = _fn("local a = 1 local b = 2 return a + b", tmp_path)
    r = build_sir(fn)
    assert _claims_all(r, fn)
    # a straight-line function is a Straight (or Seq of Straights), never an If
    from pyluadec.sir import If, NumericFor
    def has(kind, node):
        if isinstance(node, kind): return True
        for c in getattr(node, "body", ()) or ():
            if has(kind, c): return True
        return False
    assert not has(If, r) and not has(NumericFor, r)


def test_if_then_end_is_if_without_else(tmp_path):
    from pyluadec.sir import If
    from pyluadec.sir.build import build_sir
    fn = _fn("local a = tonumber('1') if a then print('y') end return a", tmp_path)
    r = build_sir(fn)
    assert _claims_all(r, fn)
    ifs = _find(r, If)
    assert ifs and ifs[0].else_body is None


def test_if_else_is_if_with_else(tmp_path):
    from pyluadec.sir import If
    from pyluadec.sir.build import build_sir
    fn = _fn("local a = tonumber('1') if a < 3 then print('s') else print('b') end", tmp_path)
    r = build_sir(fn)
    assert _claims_all(r, fn)
    ifs = _find(r, If)
    assert ifs and ifs[0].else_body is not None


def test_loop_raises_structure_error(tmp_path):
    import pytest
    from pyluadec.sir.build import StructureError, build_sir
    fn = _fn("local i = 0 while i < 3 do i = i + 1 end return i", tmp_path)
    with pytest.raises(StructureError):
        build_sir(fn)


def test_acyclic_corpus_claims_every_pc(corpus_dir):
    """Every acyclic proto that build_sir accepts must claim exactly its pc set."""
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    from pyluadec.sir import all_claimed
    from pyluadec.sir.build import StructureError, build_sir, has_back_edge
    accepted = rejected = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            fn = lift_proto(p)
            if has_back_edge(fn):
                continue                      # loops are Task 3
            try:
                r = build_sir(fn)
            except StructureError:
                rejected += 1
                continue
            assert all_claimed(r) == set(fn.instrs), f.name
            accepted += 1
    assert accepted > 500        # straight+acyclic acceptance is the bulk of the corpus


def _find(region, kind):
    out = []
    def walk(n):
        if isinstance(n, kind): out.append(n)
        for c in getattr(n, "body", ()) or ():
            walk(c)
        for attr in ("then_body", "else_body"):
            c = getattr(n, attr, None)
            if c is not None: walk(c)
    walk(region)
    return out
```

Run: `uv run pytest tests/test_sir_build_acyclic.py -v` → FAIL

- [ ] **Step 2: 实现 `src/pyluadec/sir/build.py`（直线 + if/else）**

（实现核心，按区间-支配递归。下面给出骨架与关键判据；实施者补全分支体区间计算的边界细节，以测试为行为契约。）

```python
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
    then_body = _structure_range(fn, cfg, idoms, then_lo, jt) if then_lo < jt else \
        Seq((), frozenset())
    # does the then-body end by jumping over an else block?
    else_body = None
    join = jt
    then_last = jt - 1
    if then_last >= then_lo and then_last in fn.instrs \
            and fn.instrs[then_last].ri.op is Op.JMP:
        else_jmp = fn.instrs[then_last]
        join = else_jmp.successors[0]
        if not (jt <= join <= hi):
            raise StructureError(f"pc {pc}: else-join out of range")
        # the trailing JMP of the then-body is claimed by the If, not the then-body
        then_body = _structure_range(fn, cfg, idoms, then_lo, then_last) if then_lo < then_last \
            else Seq((), frozenset())
        else_body = _structure_range(fn, cfg, idoms, jt, join) if jt < join else Seq((), frozenset())
        cond_pcs = frozenset({pc, jmp_pc, then_last})
    else:
        cond_pcs = frozenset({pc, jmp_pc})
    return (If(cond=li, negated=(li.ri.a == 0), then_body=then_body,
               else_body=else_body, join_pc=join, claimed_pcs=cond_pcs), join)
```

（实现说明：`_structure_if` 的分支边界推断是本 Task 最需要在真实语料上调试的部分。用 `test_acyclic_corpus_claims_every_pc` 逼出真实形态；若某形态导致认领审计失败，**先看 `luac_sz4 -l -l` 的实际跳转结构**再修边界逻辑，不要放宽审计。审计失败 = 该函数 `StructureError` 回落，是正确的保守退化，不是 bug。目标是 accepted > 500，不是 100% 接受——接受率上限由语料形态定，剩下的回落。）

`src/pyluadec/sir/__init__.py` 追加：

```python
from .build import StructureError, build_sir, has_back_edge
__all__ += ["StructureError", "build_sir", "has_back_edge"]
```

Run: `uv run pytest tests/test_sir_build_acyclic.py -v`（带 `PYLUADEC_CORPUS_DIR`）→ PASS

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: dominator-driven region identification for straight-line and if/else"
```

---

### Task 3: for 循环区域识别（数值 for + 泛型 for）

**Files:**
- Modify: `src/pyluadec/sir/build.py`
- Test: `tests/test_sir_build_loops.py`

**Interfaces:**
- Consumes/Produces: 扩展 `build_sir` 支持 `NumericFor`/`GenericFor`/`Break`。识别后 `has_back_edge` 不再是整函数一票否决——只否决**无法识别为 for 的**回边（while/repeat/混合）。
- Produces（Task 7 认证消费）: `build_sir` 对含且仅含 for 循环回边的函数返回结构树；含其它回边的仍 `StructureError`。

**识别算法**：

- **数值 for**：`FORPREP A sBx` 在循环头，跳到对应的 `FORLOOP A sBx'`（`FORPREP.pc + 1 + FORPREP.sbx == FORLOOP.pc`）。循环体 = `[FORPREP.pc+1, FORLOOP.pc)`。`FORLOOP` 的两后继：回跳目标（体首）与 fall-through（循环后）。体内递归 `_structure_range`。控制槽 `R(A)/R(A+1)/R(A+2)` 是 for 的 init/limit/step，`R(A+3)` 是可见循环变量。
- **泛型 for**：`TFORLOOP A C` 后必跟 `JMP` 回跳到循环头（体首）。循环体 = 从循环头到 `TFORLOOP.pc`（体在前，TFORLOOP 在后，这是 luac 的 `for-in` 布局）。`TFORLOOP` 的两后继：`pc+1`（落入回跳 JMP，继续循环）与 `pc+2`（循环后）。识别时定位循环头 = 回跳 JMP 的目标。
- **break**：循环体内一条 JMP，其目标 == 循环的 fall-through（循环后 pc）→ `Break`。非此目标的体内 JMP 走既有 if/else 逻辑或 `StructureError`。
- 循环体自身递归 `_structure_range`（可含嵌套 if/for）。体内出现无法识别的回边 → `StructureError` 整函数回落。

在 `_structure_range` 里，遇到 `FORPREP` 起头或「体首被 `TFORLOOP+JMP` 回跳」的块时进入循环识别分支；`build_sir` 开头的 `if has_back_edge: raise` 改为：先尝试结构化，仅当结构化过程遇到无法认领的回边时才 `StructureError`。

- [ ] **Step 1: 写循环识别失败测试**

`tests/test_sir_build_loops.py`：

```python
import subprocess
from pathlib import Path
import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"


def _fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return lift_proto(load_file(o))


def _find(region, kind):
    out = []
    def walk(n):
        if isinstance(n, kind): out.append(n)
        for c in getattr(n, "body", ()) or ():
            walk(c)
        for a in ("then_body", "else_body", "body"):
            c = getattr(n, a, None)
            if c is not None and not isinstance(c, tuple): walk(c)
    walk(region)
    return out


def test_numeric_for(tmp_path):
    from pyluadec.sir import NumericFor, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("local s = 0 for i = 1, 10 do s = s + i end return s", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, NumericFor)


def test_generic_for(tmp_path):
    from pyluadec.sir import GenericFor, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("local t = {1, 2} for i, v in ipairs(t) do print(i, v) end", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, GenericFor)


def test_break_in_for(tmp_path):
    from pyluadec.sir import Break, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("for i = 1, 10 do if i == 5 then break end print(i) end", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, Break)


def test_while_still_raises(tmp_path):
    from pyluadec.sir.build import StructureError, build_sir
    fn = _fn("local i = 0 while i < 3 do i = i + 1 end return i", tmp_path)
    with pytest.raises(StructureError):
        build_sir(fn)


def test_repeat_still_raises(tmp_path):
    from pyluadec.sir.build import StructureError, build_sir
    fn = _fn("local i = 0 repeat i = i + 1 until i >= 3 return i", tmp_path)
    with pytest.raises(StructureError):
        build_sir(fn)


def test_for_corpus_claims_every_pc(corpus_dir):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto, Op
    from pyluadec.sir import all_claimed
    from pyluadec.sir.build import StructureError, build_sir
    accepted_with_loop = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            fn = lift_proto(p)
            has_for = any(li.ri.op in (Op.FORLOOP, Op.TFORLOOP) for li in fn.instrs.values())
            try:
                r = build_sir(fn)
            except StructureError:
                continue
            assert all_claimed(r) == set(fn.instrs), f.name
            if has_for:
                accepted_with_loop += 1
    assert accepted_with_loop > 20      # for-loops are ~43 unique protos; many recur
```

Run: `uv run pytest tests/test_sir_build_loops.py -v` → FAIL

- [ ] **Step 2: 扩展 `build_sir` 支持 for 循环**

在 `build.py` 里：`build_sir` 去掉开头的 `if has_back_edge: raise`（改由 `_structure_range` 在遇到无法识别回边时抛 `StructureError`）；`_structure_range` 增加循环识别。关键代码：

```python
from .regions import Break, GenericFor, NumericFor

# 在 build_sir 内删除 has_back_edge 早退，保留 has_back_edge 供 Task 2 的测试与调用方用。

# _structure_range 循环头识别（放在 _COMPARE 分支之前）：
        if op is Op.FORPREP:
            region, nxt = _structure_numeric_for(fn, cfg, idoms, pc)
            parts.append(region); pc = nxt; continue
        # generic-for header: this block is the target of a trailing TFORLOOP+JMP back edge.
        # Detect by scanning forward for the matching TFORLOOP whose JMP targets `pc`.
        gfor = _match_generic_for(fn, pc, hi)
        if gfor is not None:
            region, nxt = gfor
            parts.append(region); pc = nxt; continue
```

```python
def _structure_numeric_for(fn, cfg, idoms, pc):
    prep = fn.instrs[pc]
    loop_pc = pc + 1 + prep.ri.sbx
    if loop_pc not in fn.instrs or fn.instrs[loop_pc].ri.op is not Op.FORLOOP:
        raise StructureError(f"pc {pc}: FORPREP does not reach a FORLOOP")
    loop = fn.instrs[loop_pc]
    body_after = loop_pc + 1                      # fall-through: after the loop
    body = _structure_loop_body(fn, cfg, idoms, pc + 1, loop_pc, break_target=body_after)
    return (NumericFor(prep=prep, loop=loop, body=body,
                       claimed_pcs=frozenset({pc, loop_pc})), body_after)


def _match_generic_for(fn, header_pc, hi):
    # find a TFORLOOP whose trailing JMP jumps back to header_pc
    for tf_pc in range(header_pc + 1, hi):
        if tf_pc not in fn.instrs:
            continue
        li = fn.instrs[tf_pc]
        if li.ri.op is not Op.TFORLOOP:
            continue
        jmp_pc = tf_pc + 1
        if jmp_pc in fn.instrs and fn.instrs[jmp_pc].ri.op is Op.JMP \
                and fn.instrs[jmp_pc].successors[0] == header_pc:
            after = tf_pc + 2
            body = _structure_loop_body(fn, cfg, idoms=None, lo=header_pc, hi=tf_pc,
                                        break_target=after)
            return (GenericFor(call=li, loop=fn.instrs[jmp_pc], body=body,
                               claimed_pcs=frozenset({tf_pc, jmp_pc})), after)
    return None


def _structure_loop_body(fn, cfg, idoms, lo, hi, break_target):
    """Structure a loop body interval; a bare JMP to break_target becomes Break."""
    return _structure_range(fn, cfg, idoms, lo, hi, break_target=break_target)
```

**签名改动（本 Task 唯一的一处）**：给 `_structure_range` 和 `_structure_if` 加 `break_target: int | None = None` 参数，并在所有递归调用处透传。`_structure_range` 的直线累积循环里，在检查「单后继且是 fallthrough」之前先插入 break 识别：

```python
        # inside _structure_range's main loop, before the fallthrough check:
        if (op is Op.JMP and break_target is not None
                and li.successors == (break_target,)):
            parts.append(Break(claimed_pcs=frozenset({pc})))
            pc += 1
            continue
```

同样在直线 run 的内层累积循环里，遇到这种 JMP 要 `break` 出内层循环（让它被上面的分支单独认领），否则会被误当成不可识别的转移。

`_structure_if` 透传：`_structure_range(fn, cfg, idoms, then_lo, jt, break_target=break_target)` —— 分支体里的 break 仍然是 break。

`_match_generic_for` 里 `idoms=None` 是错的：体内可能有嵌套 if，需要真实 idoms。`build_sir` 算一次 `idoms` 后一路传下去，`_match_generic_for` 也要接 `idoms` 参数并透传。实施时按此修正。

Run: `uv run pytest tests/test_sir_build_loops.py tests/test_sir_build_acyclic.py -v` → PASS（无环测试不回归）

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: numeric-for, generic-for, and break region identification"
```

---

### Task 4: 表达式 AST + 局部/临时分类 + 名字合成

**Files:**
- Create: `src/pyluadec/express/__init__.py`, `src/pyluadec/express/expr.py`, `src/pyluadec/express/names.py`
- Test: `tests/test_express_names.py`

**Interfaces:**
- Consumes: `pyluadec.lift`（`LirFunction`, `LirInstr`, `Op`, `RawInstr`, `isk`, `indexk`）；`pyluadec.ingest`（`LuaNumber`）。
- Produces:
  - `expr.py`（全部 frozen dataclass；数字/字符串字面量携带原始 payload/bytes）:
    - `ConstExpr(value)` —— `value ∈ {None, True, False, LuaNumber, bytes}`
    - `LocalExpr(reg: int)` —— 引用某寄存器对应的具名局部
    - `GlobalExpr(name: bytes)`
    - `IndexExpr(table: Expr, key: Expr)`
    - `UpvalExpr(idx: int)`
    - `BinExpr(op: str, lhs: Expr, rhs: Expr)` —— op ∈ `+ - * / % ^ .. == ~= < <= > >= and or`
    - `UnExpr(op: str, operand: Expr)` —— op ∈ `- not #`
    - `CallExpr(fn: Expr, args: tuple[Expr, ...], is_method: bool, method: bytes | None)`
    - `VarargExpr()` —— `...`
    - `ClosureExpr(proto_idx: int)` —— CLOSURE 的产物，指向 `Proto.subprotos` 下标；打印层递归打印子 proto 为 `function(...) ... end`
    - `TableExpr(array: tuple[Expr, ...], hash: tuple[tuple[Expr, Expr], ...])`
    - `Expr = Const|Local|Global|Index|Upval|Bin|Un|Call|Vararg|Table`
  - `names.py`:
    - `@dataclass(frozen=True) RegClass: locals: frozenset[int]; temps: frozenset[int]; loop_vars: frozenset[int]`
    - **for 循环寄存器特例**（重编译一致性所必需）：FORPREP/TFORLOOP 的控制槽 `a..a+2` **强制 temp**（它们的定义表达式被 for 头消费——`for v = init, limit, step` / `for ... in f, s, ctl`；发成 local 会插入多余 MOVE、寄存器错位、认证必败）；循环可见变量（FORPREP 的 `a+3`；TFORLOOP 的 `a+3..a+2+c`）**强制 local 且记入 `loop_vars`**——它们由 for 语句本身声明，重建时预标记 declared，绝不发 `LocalDecl`。
    - `classify_registers(fn: LirFunction) -> RegClass`：一个寄存器是 **local**（发 `local`，可重新赋值）当且仅当满足以下任一：被多次写；写点与读点跨越 pc（非紧邻单次消费）；被 CLOSURE 捕获（在 `fn.captured_regs`）；是函数参数（reg < numparams）。否则是 **temp**（单定义、紧邻单次使用、纯 staging），内联进消费者。
    - `name_for(reg: int, depth: int) -> str`：局部名合成，`f"l{depth}_{reg}"`（depth 是 proto 嵌套深度，防跨闭包同名遮蔽引起的重编译差异——不同 proto 各自 depth）。保证是合法 Lua 标识符、非关键字、非 `__pld_` 前缀。

**分类算法（classify_registers）**：先算每个寄存器的定义点集合（写它的 pc）与使用点集合（读它的 pc，含 open region 的 reads_open 保守当作读到 top 以下全部）。规则：
- FORPREP/TFORLOOP 控制槽（扫描全部该类指令的 `a..a+2`）→ temp（强制，优先级最高）
- FORPREP 的 `a+3` / TFORLOOP 的 `a+3..a+2+c` → local 且入 `loop_vars`（强制）
- `reg < fn.proto.numparams` → local
- `reg in fn.captured_regs` → local
- `len(defs[reg]) > 1` → local（多次赋值）
- `len(uses[reg]) != 1` → local（零使用或多使用；零使用的写是死值但保守发 local）
- 唯一 def `d`、唯一 use `u`：若 `u` 是 `d` 之后**紧邻**的消费（`d` 与 `u` 之间无对 `reg` 输入的写、无跨越的副作用指令）→ temp；否则 local。M3 的「紧邻」保守定义见下。

**「紧邻可内联」的保守判据**（M3 只认无条件健全的）：唯一 def `d` 唯一 use `u`，且 `d < u`，且 `[d+1, u)` 区间内没有任何指令写 `reg` 的输入寄存器、没有 `effect >= WRITE_HEAP` 或 `may_error` 的指令（保守：staging 值不跨越任何可能改变可见状态或抛错的操作）。这一档足以覆盖 luac 的 call-arg staging（LOADK/MOVE/GETGLOBAL/GETTABLE 紧接 CALL）与算术操作数 staging，已实测能字节一致。放宽到跨 READ_HEAP 内联是 M4。

- [ ] **Step 1: 写分类失败测试**

`tests/test_express_names.py`：

```python
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return lift_proto(load_file(o))


def test_reassigned_register_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    # 'a' is written twice (a=1; a=a+1) → its register is a local, not a temp
    fn = _fn("local a = 1 a = a + 1 print(a)", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps


def test_call_arg_staging_is_temp(tmp_path):
    from pyluadec.express.names import classify_registers
    # string.format('%d', 42): the GETGLOBAL/GETTABLE/LOADK staging registers feed
    # straight into the CALL — single def, adjacent single use → temp (inlined)
    fn = _fn("print(string.format('%d', 42))", tmp_path)
    rc = classify_registers(fn)
    assert rc.temps                      # at least the format-string/arg staging inlines


def test_parameter_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    fn = _fn("local function f(x, y) return x + y end return f", tmp_path)
    inner = fn.proto.subprotos[0]
    from pyluadec.lift import lift_proto
    rc = classify_registers(lift_proto(inner))
    assert 0 in rc.locals and 1 in rc.locals     # both params are locals


def test_captured_register_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import lift_proto
    root = _fn("local n = 0 local f = function() return n end return f()", tmp_path)
    rc = classify_registers(root)
    # n's register is captured by the closure → local
    assert root.captured_regs
    assert root.captured_regs <= rc.locals


def test_name_for_is_valid_identifier():
    from pyluadec.express.names import name_for
    from pyluadec.lift import LUA_KEYWORDS
    n = name_for(3, depth=1)
    assert n.isidentifier() and n not in LUA_KEYWORDS and not n.startswith("__pld_")
    assert name_for(3, 1) != name_for(3, 2)      # depth disambiguates across protos
```

Run: `uv run pytest tests/test_express_names.py -v` → FAIL

- [ ] **Step 2: 实现 `expr.py`、`names.py`**

`src/pyluadec/express/expr.py`：

```python
"""Expression AST (spec §4). Frozen; literals keep raw payload/bytes."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.ingest.proto import LuaNumber


@dataclass(frozen=True)
class ConstExpr:
    value: object            # None | bool | LuaNumber | bytes


@dataclass(frozen=True)
class LocalExpr:
    reg: int


@dataclass(frozen=True)
class GlobalExpr:
    name: bytes


@dataclass(frozen=True)
class UpvalExpr:
    idx: int


@dataclass(frozen=True)
class IndexExpr:
    table: "Expr"
    key: "Expr"


@dataclass(frozen=True)
class BinExpr:
    op: str
    lhs: "Expr"
    rhs: "Expr"


@dataclass(frozen=True)
class UnExpr:
    op: str
    operand: "Expr"


@dataclass(frozen=True)
class CallExpr:
    fn: "Expr"
    args: tuple["Expr", ...]
    is_method: bool = False
    method: bytes | None = None


@dataclass(frozen=True)
class VarargExpr:
    pass


@dataclass(frozen=True)
class ClosureExpr:
    proto_idx: int           # index into the enclosing Proto.subprotos


@dataclass(frozen=True)
class TableExpr:
    array: tuple["Expr", ...]
    hash: tuple[tuple["Expr", "Expr"], ...]


Expr = (ConstExpr | LocalExpr | GlobalExpr | UpvalExpr | IndexExpr | BinExpr
        | UnExpr | CallExpr | VarargExpr | ClosureExpr | TableExpr)
```

`src/pyluadec/express/names.py`：

```python
"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.lift.effects import Effect
from pyluadec.lift.lift import LirFunction

from pyluadec.lift import LUA_KEYWORDS


@dataclass(frozen=True)
class RegClass:
    locals: frozenset[int]
    temps: frozenset[int]
    loop_vars: frozenset[int]    # declared by the for statement itself, never by LocalDecl


def name_for(reg: int, depth: int) -> str:
    n = f"l{depth}_{reg}"
    assert n.isidentifier() and n not in LUA_KEYWORDS and not n.startswith("__pld_")
    return n


def classify_registers(fn: LirFunction) -> RegClass:
    defs: dict[int, list[int]] = {}
    uses: dict[int, list[int]] = {}
    ordered = sorted(fn.instrs)
    for pc in ordered:
        li = fn.instrs[pc]
        for r in li.effects.writes:
            defs.setdefault(r, []).append(pc)
        for r in li.effects.reads:
            uses.setdefault(r, []).append(pc)
    from pyluadec.lift.opcodes import Op
    controls: set[int] = set()
    loop_vars: set[int] = set()
    for pc in ordered:
        ri = fn.instrs[pc].ri
        if ri.op in (Op.FORPREP, Op.FORLOOP):
            controls |= {ri.a, ri.a + 1, ri.a + 2}
            loop_vars.add(ri.a + 3)
        elif ri.op is Op.TFORLOOP:
            controls |= {ri.a, ri.a + 1, ri.a + 2}
            loop_vars |= set(range(ri.a + 3, ri.a + 3 + ri.c))
    regs = set(defs) | set(uses) | controls | loop_vars
    locals_: set[int] = set()
    temps: set[int] = set()
    for r in sorted(regs):
        if r in controls:
            temps.add(r); continue
        if r in loop_vars:
            locals_.add(r); continue
        if r < fn.proto.numparams or r in fn.captured_regs:
            locals_.add(r); continue
        d, u = defs.get(r, []), uses.get(r, [])
        if len(d) != 1 or len(u) != 1:
            locals_.add(r); continue
        dp, up = d[0], u[0]
        if dp >= up or not _adjacent_pure(fn, r, dp, up, ordered):
            locals_.add(r); continue
        temps.add(r)
    return RegClass(locals=frozenset(locals_), temps=frozenset(temps),
                    loop_vars=frozenset(loop_vars))


def _adjacent_pure(fn: LirFunction, reg: int, dp: int, up: int, ordered) -> bool:
    """No write to reg's inputs and no WRITE_HEAP/may_error between the def and its use."""
    dli = fn.instrs[dp]
    inputs = set(dli.effects.reads)
    for pc in ordered:
        if not (dp < pc < up):
            continue
        li = fn.instrs[pc]
        if li.effects.writes & inputs:
            return False
        if li.effects.effect >= Effect.WRITE_HEAP or li.effects.may_error:
            return False
    return True
```

`src/pyluadec/express/__init__.py`：

```python
from .expr import (BinExpr, CallExpr, ConstExpr, Expr, GlobalExpr, IndexExpr,
                   LocalExpr, TableExpr, UnExpr, UpvalExpr, VarargExpr)
from .names import RegClass, classify_registers, name_for

__all__ = ["BinExpr", "CallExpr", "ConstExpr", "Expr", "GlobalExpr", "IndexExpr",
           "LocalExpr", "RegClass", "TableExpr", "UnExpr", "UpvalExpr", "VarargExpr",
           "classify_registers", "name_for"]
```

Run: `uv run pytest tests/test_express_names.py -v` → PASS

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: expression AST, register local/temp classification, name synthesis"
```

---

### Task 5: 表达式重建（LIR → 语句 + 内联 + 表构造）

**Files:**
- Create: `src/pyluadec/express/reconstruct.py`
- Modify: `src/pyluadec/express/__init__.py`
- Test: `tests/test_express_reconstruct.py`

**Interfaces:**
- Consumes: Task 4 `expr`/`names`；`pyluadec.lift`（`Op`, `isk`, `indexk`）；SIR 区域。
- Produces（Task 6 打印层消费）:
  - `@dataclass(frozen=True) Stmt` 家族（语句 IR，SIR 叶子重建的产物）:
    - `LocalDecl(regs: tuple[int, ...], exprs: tuple[Expr, ...])` —— `local a, b = e1, e2`（首次定义）
    - `Assign(targets: tuple[AssignTarget, ...], exprs: tuple[Expr, ...])` —— 重新赋值 / SETTABLE / SETGLOBAL / SETUPVAL
    - `ExprStmt(call: CallExpr)` —— 语句位置的调用（结果丢弃）
    - `ReturnStmt(exprs: tuple[Expr, ...], is_vararg_tail: bool)`
    - `AssignTarget = LocalTarget(reg) | GlobalTarget(name) | IndexTarget(table: Expr, key: Expr) | UpvalTarget(idx)`
  - `class Reconstructor(fn, rc: RegClass, depth: int, upval_names: tuple[str, ...])`——**环境跨区域流动的重建器**。区域树按程序序遍历时共用同一个实例，`reg -> Expr` 环境（temp 的待内联定义、local 的已声明状态）跨 Straight/If/For 区域边界存活。这是 for 头与 if 条件能消费**前一个区域**staging 出来的表达式的机制。方法：
    - `stmts_for(instrs: tuple[LirInstr, ...]) -> tuple[Stmt, ...]`：重建一段直线 LIR；temp 写 → 记环境不发语句；temp 读 → 取环境内联（**取后弹出**，单使用已证明）；local 写 → `LocalDecl`（首次，`loop_vars` 预标记 declared 故永不 LocalDecl）或 `Assign`；local 读 → `LocalExpr(reg)`。
    - `take_expr(reg: int) -> Expr`：弹出控制槽 temp 的定义表达式（NumericFor 的 init/limit/step、GenericFor 的迭代器三元组由打印层经此消费）；环境里没有 → `ReconstructError`。
    - `cond_operand(x: int) -> Expr`：if 条件的 RK 操作数（K → ConstExpr；temp 寄存器 → 弹出内联；local → LocalExpr）。
  - `reconstruct_straight(fn, instrs, rc, depth) -> tuple[Stmt, ...]`：薄封装（新建一次性 Reconstructor 调 `stmts_for`），供单元测试用。
  - `class ReconstructError(Exception)`。
  - 表构造重建：`NEWTABLE` 起一个待填表，后随 `SETLIST`（array 部分）与 `SETTABLE`（hash 部分，若键是常量且表寄存器是该 temp）折叠进 `TableExpr`——**仅当**表寄存器是 temp 且这些 SETLIST/SETTABLE 紧接构造、无中间副作用（否则退化为逐条 Assign，仍正确只是不美）。这是 backlog item 5（表布局保真）的落点：把 `{1,2,3}` 还原成构造式，重编译才会产生同样的 NEWTABLE presize + SETLIST。

**内联环境的核心不变式**：读一个 temp 寄存器时，它的定义表达式已在环境中且从定义到此处保持有效（Task 4 的 `_adjacent_pure` 已证明）。local 寄存器每次读都发 `LocalExpr`，其值由最近一次 `LocalDecl`/`Assign` 语句负责。这样重建出的语句序列，寄存器物化决策与 luac 的 local/temp 分配一致，是重编译字节一致的充要工程条件。

（本 Task 是 M3 最大且最需要在语料上迭代的部分。策略：先让直线 proto 全部走通 `reconstruct_straight` → Task 6 打印 → Task 7 认证，用「直线 proto L3 认证率」当回归指标，逐个 opcode 补重建规则。opcode 覆盖：MOVE/LOADK/LOADBOOL/LOADNIL/GETGLOBAL/SETGLOBAL/GETTABLE/SETTABLE/GETUPVAL/SETUPVAL/NEWTABLE/SELF/算术组/UNM/NOT/LEN/CONCAT/CALL(定长+开放)/TAILCALL/RETURN/VARARG/SETLIST/CLOSURE。控制类 opcode 由 SIR 区域处理，不在 reconstruct_straight 里。）

- [ ] **Step 1: 写重建失败测试（以认证为最终判据）**

`tests/test_express_reconstruct.py`：

```python
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _proto_and_fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    p = load_file(o)
    return p, lift_proto(p)


def test_move_and_arith_reconstruct(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight
    from pyluadec.express.expr import BinExpr
    p, fn = _proto_and_fn("local a = 1 local b = 2 local c = a + b return c", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    # somewhere a LocalDecl binds an ADD expression
    from pyluadec.express.reconstruct import LocalDecl
    adds = [s for s in stmts if isinstance(s, LocalDecl) and any(isinstance(e, BinExpr) and e.op == "+" for e in s.exprs)]
    assert adds


def test_call_arg_staging_inlines(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, ExprStmt
    from pyluadec.express.expr import CallExpr, ConstExpr
    p, fn = _proto_and_fn("print('a', 'b', 'c')", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    calls = [s for s in stmts if isinstance(s, ExprStmt)]
    assert calls and isinstance(calls[0].call, CallExpr)
    assert len(calls[0].call.args) == 3      # three literals inlined as args, no intermediate locals


def test_table_constructor_reconstructs(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl
    from pyluadec.express.expr import TableExpr
    p, fn = _proto_and_fn("local t = {10, 20, 30} return t", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    decls = [s for s in stmts if isinstance(s, LocalDecl) and any(isinstance(e, TableExpr) for e in s.exprs)]
    assert decls and len(decls[0].exprs[0].array) == 3


def test_reassignment_emits_assign_not_second_decl(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import reconstruct_straight, LocalDecl, Assign
    p, fn = _proto_and_fn("local a = 1 a = a + 1 return a", tmp_path)
    rc = classify_registers(fn)
    stmts = reconstruct_straight(fn, tuple(fn.instrs[i] for i in sorted(fn.instrs)), rc, depth=0)
    assert sum(isinstance(s, LocalDecl) for s in stmts) == 1
    assert sum(isinstance(s, Assign) for s in stmts) == 1
```

Run: `uv run pytest tests/test_express_reconstruct.py -v` → FAIL

- [ ] **Step 2: 实现 `reconstruct.py`（Stmt 家族 + reconstruct_straight）**

（给出 Stmt 定义与 reconstruct_straight 的骨架 + 环境机制；opcode 重建规则表在实现中补全，以测试 + Task 7 的语料认证率为契约。语义模板与 fallback emitter 共享同一套结论——可对照 `structure/fallback.py` 的 `_emit_simple` 逐 opcode 校验表达式形态，但这里产出 Expr 树而非字符串。）

```python
"""LIR straight-run → statement/expression IR with effect-gated temp inlining (spec §4)."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.lift.lift import LirFunction, LirInstr
from pyluadec.lift.opcodes import Op, indexk, isk

from .expr import (BinExpr, CallExpr, ConstExpr, Expr, GlobalExpr, IndexExpr,
                   LocalExpr, TableExpr, UnExpr, UpvalExpr, VarargExpr)
from .names import RegClass


# ---- statement IR ----
@dataclass(frozen=True)
class LocalTarget:
    reg: int
@dataclass(frozen=True)
class GlobalTarget:
    name: bytes
@dataclass(frozen=True)
class IndexTarget:
    table: Expr
    key: Expr
@dataclass(frozen=True)
class UpvalTarget:
    idx: int
AssignTarget = LocalTarget | GlobalTarget | IndexTarget | UpvalTarget

@dataclass(frozen=True)
class LocalDecl:
    regs: tuple[int, ...]
    exprs: tuple[Expr, ...]
@dataclass(frozen=True)
class Assign:
    targets: tuple[AssignTarget, ...]
    exprs: tuple[Expr, ...]
@dataclass(frozen=True)
class ExprStmt:
    call: CallExpr
@dataclass(frozen=True)
class ReturnStmt:
    exprs: tuple[Expr, ...]
    is_vararg_tail: bool
Stmt = LocalDecl | Assign | ExprStmt | ReturnStmt


class ReconstructError(Exception):
    pass


def reconstruct_straight(fn: LirFunction, instrs: tuple[LirInstr, ...],
                         rc: RegClass, depth: int) -> tuple[Stmt, ...]:
    proto = fn.proto
    env: dict[int, Expr] = {}          # reg -> current Expr (temps inlined; locals = LocalExpr)
    declared: set[int] = set()         # locals already `local`-declared
    out: list[Stmt] = []

    def rk(x: int) -> Expr:
        if isk(x):
            return ConstExpr(proto.constants[indexk(x)])
        return env.get(x, LocalExpr(x))

    def write_reg(reg: int, e: Expr) -> None:
        if reg in rc.temps:
            env[reg] = e                       # inline; no statement
        else:
            if reg in declared:
                out.append(Assign((LocalTarget(reg),), (e,)))
            else:
                out.append(LocalDecl((reg,), (e,)))
                declared.add(reg)
            env[reg] = LocalExpr(reg)

    for li in instrs:
        _reconstruct_one(li, proto, rk, env, write_reg, out, rc, depth)
    return tuple(out)


def _reconstruct_one(li, proto, rk, env, write_reg, out, rc, depth):
    ri = li.ri
    op, a, b, c, bx = ri.op, ri.a, ri.b, ri.c, ri.bx
    if op is Op.MOVE:
        write_reg(a, rk(b))
    elif op is Op.LOADK:
        write_reg(a, ConstExpr(proto.constants[bx]))
    elif op is Op.GETGLOBAL:
        write_reg(a, GlobalExpr(proto.constants[bx]))
    elif op is Op.GETTABLE:
        write_reg(a, IndexExpr(rk(b), rk(c)))
    # ... remaining opcodes per the mapping table below
    else:
        raise ReconstructError(f"pc {ri.pc}: opcode {op.name} not reconstructible")
```

（`_reconstruct_one` 的 opcode 规则是本 Task 的主体，逐条实现并对照 `structure/fallback.py::_emit_simple` 的语义结论（同一套 lvm.c 依据，只是产 Expr 而非字符串）。上面给出前四条作为形态示范，其余按下表补全；未覆盖的 opcode 必须 `raise ReconstructError` 而非静默跳过——回落是正确的，猜不是。关键映射：MOVE→`write_reg(a, rk(b))`；LOADK→`write_reg(a, ConstExpr(k[bx]))`；GETGLOBAL→`write_reg(a, GlobalExpr(k[bx]))`；GETTABLE→`write_reg(a, IndexExpr(rk(b), rk(c)))`；算术→`write_reg(a, BinExpr(sym, rk(b), rk(c)))`；CALL→构造 `CallExpr(env[a], args)`，C==1 发 `ExprStmt`，C>=2 发 `Assign`/`LocalDecl` 到结果寄存器，结果寄存器按 rc 分类；RETURN→`ReturnStmt`；NEWTABLE 起表、SETLIST/SETTABLE 折叠——细节以测试为准。SELF/method-call、开放 CALL/RETURN 按 fallback 的语义对应产 Expr；CLOSURE→`write_reg(a, ClosureExpr(bx))`（子 proto 打印在 Task 6，CLOSURE 的伪指令已被 lift 消耗、其捕获映射在 `fn.closure_pseudo[pc]`，随 ClosureExpr 所在的 write 一并传给打印层）；TESTSET → `ReconstructError`（and/or 值 idiom，M4）。）

`src/pyluadec/express/__init__.py` 追加 Stmt/target/reconstruct 导出。

Run: `uv run pytest tests/test_express_reconstruct.py -v` → PASS

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: statement/expression reconstruction with effect-gated inlining and table constructors"
```

---

### Task 6: Lua 打印层（SIR + Expr → 源码）

**Files:**
- Create: `src/pyluadec/emit/__init__.py`, `src/pyluadec/emit/lua.py`
- Test: `tests/test_emit_lua.py`

**Interfaces:**
- Consumes: Task 1 SIR 区域；Task 5 Stmt/Expr；`pyluadec.structure.fallback`（复用 `num_lit`/`str_lit`/`const_lit` 字面量渲染——它们已 payload/字节精确，别重写）。
- Produces:
  - `print_function(fn: LirFunction, region: Region, rc: RegClass, depth: int) -> str`：把区域树 + 重建语句打印成一个 Lua 函数体源码（不含外层 `function()...end` 包裹——由 chunk 组装层加）。
  - `print_chunk(proto: Proto) -> str | None`：结构化打印整个 proto 树为可编译 Lua chunk；任何子 proto 结构化失败返回 None（触发整 chunk 回落，Task 7 处理）。**注意**：CLOSURE 子 proto 递归打印为 `function(params) ... end` 内联在其构造点，或按 luac 的 local-function 惯用式——形态必须让重编译产生同构的 CLOSURE + 子 proto 结构。

**渲染纪律**：
- 数字/字符串字面量一律经 `fallback.num_lit`/`str_lit`（payload/字节精确）。
- 局部名经 `express.names.name_for(reg, depth)`。
- 缩进纯格式化，不影响语义（认证在 L3.1 剥行信息，缩进/换行不参与比对）。
- 运算符优先级：BinExpr/UnExpr 打印时按 Lua 优先级加最小必要括号（保守多加括号无害——重编译后 AST 同构、常量折叠不受括号影响，认证仍过）。

- [ ] **Step 1: 写打印失败测试**

`tests/test_emit_lua.py`：

```python
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _proto(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return load_file(o)


def _compiles(src: str) -> bool:
    from pyluadec import oracle
    try:
        oracle.compile_source(src.encode() if isinstance(src, str) else src)
        return True
    except oracle.LuaCompileError:
        return False


def test_straight_chunk_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local a = 1 local b = 2 print(a + b)", tmp_path))
    assert src is not None and _compiles(src)


def test_if_else_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local a = tonumber('1') if a < 3 then print('s') else print('b') end", tmp_path))
    assert src is not None and _compiles(src)


def test_numeric_for_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local s = 0 for i = 1, 10 do s = s + i end print(s)", tmp_path))
    assert src is not None and _compiles(src)


def test_closure_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local n = 0 local f = function() return n end print(f())", tmp_path))
    assert src is not None and _compiles(src)


def test_while_returns_none(tmp_path):
    from pyluadec.emit.lua import print_chunk
    # while is not structured in M3 → print_chunk returns None (caller falls back)
    assert print_chunk(_proto("local i=0 while i<3 do i=i+1 end return i", tmp_path)) is None
```

Run: `uv run pytest tests/test_emit_lua.py -v` → FAIL

- [ ] **Step 2: 实现 `emit/lua.py`**

（骨架 + 关键分派；语句/区域打印逐类实现，以「可编译」测试 + Task 7 认证为契约。`print_chunk` 内部：对每个 proto 试 `build_sir`→`classify_registers`→`reconstruct`→区域打印，任一步 `StructureError`/`ReconstructError` 返回 None。）

```python
"""AST/SIR → Lua source (spec §3 layer ⑥). Pure formatting; no semantic decisions."""
from __future__ import annotations

from pyluadec.express.names import RegClass, classify_registers, name_for
from pyluadec.express.reconstruct import (Assign, ExprStmt, GlobalTarget,
                                          IndexTarget, LocalDecl, LocalTarget,
                                          ReturnStmt, Stmt, UpvalTarget,
                                          reconstruct_straight)
from pyluadec.express.expr import (BinExpr, CallExpr, ConstExpr, Expr, GlobalExpr,
                                   IndexExpr, LocalExpr, TableExpr, UnExpr,
                                   UpvalExpr, VarargExpr)
from pyluadec.ingest.proto import Proto
from pyluadec.lift import lift_proto
from pyluadec.sir import (Break, GenericFor, If, NumericFor, Region, Return, Seq,
                          Straight)
from pyluadec.sir.build import StructureError, build_sir
from pyluadec.structure.fallback import const_lit, num_lit, str_lit


# Lua operator precedence (higher binds tighter); used to add minimal parentheses.
_PREC = {"or": 1, "and": 2,
         "<": 3, ">": 3, "<=": 3, ">=": 3, "~=": 3, "==": 3,
         "..": 4, "+": 5, "-": 5, "*": 6, "/": 6, "%": 6,
         "unary": 7, "^": 8}
_RIGHT_ASSOC = {"..", "^"}


def print_expr(e: Expr, depth: int, parent_prec: int = 0) -> str:
    """NOTE (implementation): print_expr/print_region/_print_stmt all need the
    current proto's upval_names and (for ClosureExpr) its Proto + closure capture
    mapping. Rather than threading four extra parameters through every call,
    implement these as methods of a small `Printer` class holding
    (proto, fn, recon, depth, upval_names); the module-level functions shown here
    document the dispatch logic and remain as thin wrappers used by the tests.
    """
    if isinstance(e, ConstExpr):
        return const_lit(e.value)
    if isinstance(e, LocalExpr):
        return name_for(e.reg, depth)
    if isinstance(e, GlobalExpr):
        return e.name.decode("ascii")          # validated identifier; see fallback.global_name
    if isinstance(e, UpvalExpr):
        return UPVAL_NAMES_IN_SCOPE[e.idx]     # Printer attribute in the real impl
    if isinstance(e, ClosureExpr):
        return _print_closure(e)               # Printer method in the real impl; see below
    if isinstance(e, VarargExpr):
        return "..."
    if isinstance(e, IndexExpr):
        return f"{print_expr(e.table, depth, 9)}[{print_expr(e.key, depth)}]"
    if isinstance(e, TableExpr):
        items = [print_expr(x, depth) for x in e.array]
        items += [f"[{print_expr(k, depth)}] = {print_expr(v, depth)}" for k, v in e.hash]
        return "{" + ", ".join(items) + "}"
    if isinstance(e, CallExpr):
        args = ", ".join(print_expr(a, depth) for a in e.args)
        if e.is_method:
            return f"{print_expr(e.fn, depth, 9)}:{e.method.decode('ascii')}({args})"
        return f"{print_expr(e.fn, depth, 9)}({args})"
    if isinstance(e, UnExpr):
        prec = _PREC["unary"]
        inner = print_expr(e.operand, depth, prec)
        sep = " " if e.op == "not" else ""
        out = f"{e.op}{sep}{inner}"
        return f"({out})" if prec < parent_prec else out
    if isinstance(e, BinExpr):
        prec = _PREC[e.op]
        lp = prec + (1 if e.op in _RIGHT_ASSOC else 0)
        rp = prec + (0 if e.op in _RIGHT_ASSOC else 1)
        out = f"{print_expr(e.lhs, depth, lp)} {e.op} {print_expr(e.rhs, depth, rp)}"
        return f"({out})" if prec < parent_prec else out
    raise ReconstructError(f"unprintable expression {type(e).__name__}")


# Upvalue printing: an UpvalExpr(idx) prints as upval_names[idx] — the tuple is
# threaded down from the parent at each ClosureExpr site (see _print_closure).
# There is no name synthesis for upvalues at print time; if a mapping is missing,
# that is a ReconstructError and the proto falls back.


def _print_stmt(s: Stmt, depth: int) -> str:
    if isinstance(s, LocalDecl):
        names = ", ".join(name_for(r, depth) for r in s.regs)
        vals = ", ".join(print_expr(e, depth) for e in s.exprs)
        return f"local {names} = {vals}"
    if isinstance(s, Assign):
        tgts = ", ".join(_print_target(t, depth) for t in s.targets)
        vals = ", ".join(print_expr(e, depth) for e in s.exprs)
        return f"{tgts} = {vals}"
    if isinstance(s, ExprStmt):
        return print_expr(s.call, depth)
    if isinstance(s, ReturnStmt):
        if not s.exprs:
            return "return"
        return "return " + ", ".join(print_expr(e, depth) for e in s.exprs)
    raise ReconstructError(f"unprintable statement {type(s).__name__}")


def _print_target(t, depth: int) -> str:
    if isinstance(t, LocalTarget):
        return name_for(t.reg, depth)
    if isinstance(t, GlobalTarget):
        return t.name.decode("ascii")
    if isinstance(t, IndexTarget):
        return f"{print_expr(t.table, depth, 9)}[{print_expr(t.key, depth)}]"
    if isinstance(t, UpvalTarget):
        return name_for_upval(t.idx, depth)
    raise ReconstructError(f"unprintable target {type(t).__name__}")


def print_region(r: Region, recon, depth: int, indent: int) -> list[str]:
    """recon is the function's shared Reconstructor — its env flows across regions
    in program order, which is what lets a for-header consume init/limit/step
    expressions staged by the PRECEDING Straight region (they are forced temps)."""
    pad = "  " * indent
    if isinstance(r, Straight):
        return [pad + _print_stmt(s, depth) for s in recon.stmts_for(r.instrs)]
    if isinstance(r, Seq):
        out: list[str] = []
        for child in r.body:
            out += print_region(child, recon, depth, indent)
        return out
    if isinstance(r, Return):
        return [pad + _print_stmt(s, depth) for s in recon.stmts_for((r.instr,))]
    if isinstance(r, Break):
        return [pad + "break"]
    if isinstance(r, If):
        cond = _print_condition(r, recon, depth)
        out = [f"{pad}if {cond} then"]
        out += print_region(r.then_body, recon, depth, indent + 1)
        if r.else_body is not None:
            out.append(f"{pad}else")
            out += print_region(r.else_body, recon, depth, indent + 1)
        out.append(f"{pad}end")
        return out
    if isinstance(r, NumericFor):
        a = r.prep.ri.a
        var = name_for(a + 3, depth)
        init = print_expr(recon.take_expr(a), depth)
        limit = print_expr(recon.take_expr(a + 1), depth)
        step = print_expr(recon.take_expr(a + 2), depth)
        out = [f"{pad}for {var} = {init}, {limit}, {step} do"]
        out += print_region(r.body, recon, depth, indent + 1)
        out.append(f"{pad}end")
        return out
    if isinstance(r, GenericFor):
        a, c = r.call.ri.a, r.call.ri.c
        vars_ = ", ".join(name_for(a + 3 + i, depth) for i in range(c))
        iter_ = ", ".join(print_expr(recon.take_expr(a + i), depth) for i in range(3))
        out = [f"{pad}for {vars_} in {iter_} do"]
        out += print_region(r.body, recon, depth, indent + 1)
        out.append(f"{pad}end")
        return out
    raise StructureError(f"unprintable region {type(r).__name__}")


def _print_condition(r: If, recon, depth: int) -> str:
    """Render the If's comparison instruction as a boolean expression.

    POLARITY IS ORACLE-ARBITRATED: the A-flag/C-flag mapping below is the
    reference guess. If if/else certification fails systematically with
    then/else swapped or `not` inverted, flip here and re-measure — the
    certification gate makes the wrong polarity impossible to ship, so this
    is a five-minute TDD loop against luac, not a correctness risk.
    """
    ri = r.cond.ri
    op = ri.op
    if op in (Op.EQ, Op.LT, Op.LE):
        sym = {Op.EQ: "==", Op.LT: "<", Op.LE: "<="}[op]
        lhs = print_expr(recon.cond_operand(ri.b), depth)
        rhs = print_expr(recon.cond_operand(ri.c), depth)
        base = f"{lhs} {sym} {rhs}"
        return base if ri.a else f"not ({base})"
    if op is Op.TEST:
        base = print_expr(recon.cond_operand(ri.a), depth)
        return base if ri.c else f"not {base}"
    raise StructureError(f"unprintable condition {op.name}")


def print_chunk(proto: Proto) -> str | None:
    from pyluadec.express.reconstruct import ReconstructError
    try:
        return _print_proto_body(proto, depth=0, upval_names=())
    except (StructureError, ReconstructError):
        return None


def _print_proto_body(proto: Proto, depth: int, upval_names: tuple[str, ...]) -> str:
    from pyluadec.express.reconstruct import Reconstructor
    fn = lift_proto(proto)
    region = build_sir(fn)
    rc = classify_registers(fn)
    recon = Reconstructor(fn, rc, depth, upval_names)
    lines = print_region(region, recon, depth, indent=0)
    return "\n".join(lines) + "\n"


def _print_closure(closure_expr, parent_proto, parent_fn, closure_pc, parent_depth,
                   parent_upval_names) -> str:
    """Print a CLOSURE site as an inline `function(params) ... end` literal.

    The child's upval_names are derived from the CLOSURE's pseudo-instructions
    (recorded by lift in parent_fn.closure_pseudo[closure_pc], in child upvalue
    index order):
      MOVE 0 B     -> child upvalue i is the parent LOCAL name_for(B, parent_depth)
      GETUPVAL 0 B -> child upvalue i is the parent's own upval_names[B]
    RECOMPILE CAVEAT (oracle-arbitrated): luac assigns child upvalue indices in
    first-reference order during parsing. If the child's first-reference order
    differs from its original index order, the recompiled GETUPVAL operands
    permute and certification fails — the proto falls back honestly. Measured
    risk is low (84% of protos have nups 0; most captured ones have 1). If it
    bites more than expected, an upvalue-permutation normalization rung is the
    M4 fix, not a reason to weaken this printer.
    """
    child = parent_proto.subprotos[closure_expr.proto_idx]
    names = []
    for ps in parent_fn.closure_pseudo[closure_pc]:
        if ps.op.name == "MOVE":
            names.append(name_for(ps.b, parent_depth))
        else:                                          # GETUPVAL pseudo
            names.append(parent_upval_names[ps.b])
    params = ", ".join(name_for(i, parent_depth + 1) for i in range(child.numparams))
    if child.is_vararg & 2:
        params = params + (", ..." if params else "...")
    body = _print_proto_body(child, parent_depth + 1, tuple(names))
    return f"function({params})\n{body}end"
```

（实现说明：`print_chunk` 的 `except Exception` 太宽——实现时收窄为 `except (StructureError, ReconstructError)`，其它异常应当冒出（是 bug 不是回落）。CLOSURE 子 proto 的打印是本 Task 的难点：它必须让重编译产生同构的 proto 树。最稳的形态是把子 proto 打印为匿名 `function(...) ... end` 内联在 CLOSURE 目标寄存器的赋值处（对 `local f = function()...end` 与 `local function f()...end` 两种 luac 布局，用 captured_regs/自引用判定选哪种——若判不准就 `StructureError` 回落）。用 `test_closure_prints_compilable` + Task 7 的闭包认证率逼出正确形态。）

`src/pyluadec/emit/__init__.py`：

```python
from .lua import print_chunk, print_expr, print_region

__all__ = ["print_chunk", "print_expr", "print_region"]
```

Run: `uv run pytest tests/test_emit_lua.py -v` → PASS

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: Lua printer for structured regions and reconstructed expressions"
```

---

### Task 7: 逐 proto 认证（wrapper 隔离）+ chunk 组装

**Files:**
- Create: `src/pyluadec/structure/structured.py`
- Test: `tests/test_structured_certify.py`

**Interfaces:**
- Consumes: Task 6 `print_chunk`/`_print_proto_body`；Task 0 `certify_l3`/`CertResult`；`pyluadec.structure.fallback.emit_chunk`；`pyluadec.pipeline.walk_proto_paths`。
- Produces（Task 8 pipeline 消费）:
  - `@dataclass(frozen=True) ProtoCert: level: str; rung: int | None; mismatches: tuple[Mismatch, ...]`
  - `certify_proto(proto: Proto, *, is_chunk_root: bool) -> ProtoCert`：**逐 proto 隔离认证**。结构化打印该 proto 的**整个子树**，重编译，与原 proto 子树在阶梯上比对：
    - `is_chunk_root=True`（main）：源码即 chunk 体，`compile_source(..., strip=True)` 后直接比对。
    - 嵌套 proto（nups=n, numparams=k）：包一层 wrapper 源码——`local u0, u1, ..., u{n-1}\nreturn function(<params>) <body> end`，编译后取 `.subprotos[0]` 比对。wrapper 里的 `u<i>` 名字与打印子树时传入的 `upval_names=(u0..u{n-1})` 一致，使子树里的 UpvalExpr 打印成 wrapper 声明的名字。**wrapper 自身的 main proto 不参与比对**（它只是脚手架）。
    - `print` 失败（StructureError/ReconstructError）或比对不过 → `ProtoCert("L1", None, mismatches)`。
  - `@dataclass(frozen=True) ChunkOutcome: source: bytes; certs: dict[str, ProtoCert]`（键 = proto_path）
  - `emit_certified_chunk(root: Proto) -> ChunkOutcome`：对树中每个 proto 独立 `certify_proto`（同一 chunk 内按 `structural_hash` 记忆化，避免重复认证重复函数）；**产物源码**：若 root 的认证是 L3（root 认证覆盖整树，蕴含全树结构化成功），产物 = 结构化 chunk 源码；否则产物 = `fallback.emit_chunk(root)`（整 chunk 回落，语义精确保底）。
  - **不变式**：(1) `ChunkOutcome.source` 永远可编译；(2) 任何 `certs[path].level == "L3"` 都蕴含该 proto 子树的结构化源码重编译后在阶梯内逐字段匹配；(3) 产物为结构化源码 ⟺ root 认证 L3。

**为什么逐 proto 而不是 chunk 级 all-or-nothing（定量依据，2026-08-10 实测）**：全语料只有 93/229 个文件的整树落在直线+无环+for 能力集内；chunk 级门会把出口指标压到 **13.1%**（unique proto 口径），M3 必死。逐 proto 子树认证的上界是 **80.3%**——一个 while 重灾文件里的直线子函数照样各自认证 L3，只有该文件的**产物**整体回落。台账等级（出口指标）与产物形态由此解耦：等级是逐 proto 的证明记录，产物是文件级的保守选择。

- [ ] **Step 1: 写认证失败测试**

`tests/test_structured_certify.py`：

```python
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _proto(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return load_file(o)


def test_straight_chunk_certifies_l3(tmp_path):
    from pyluadec.structure.structured import certify_proto
    c = certify_proto(_proto("local a = 1 local b = 2 print(a + b)", tmp_path),
                      is_chunk_root=True)
    assert c.level == "L3" and c.rung is not None


def test_while_chunk_is_l1(tmp_path):
    from pyluadec.structure.structured import certify_proto
    c = certify_proto(_proto("local i = 0 while i < 3 do i = i + 1 end return i", tmp_path),
                      is_chunk_root=True)
    assert c.level == "L1" and c.rung is None


def test_nested_proto_certifies_via_wrapper(tmp_path):
    from pyluadec.structure.structured import certify_proto
    root = _proto("local n = 5 local f = function(x) return x + n end print(f(1))", tmp_path)
    inner = root.subprotos[0]              # captures n → nups == 1
    assert inner.nups == 1
    c = certify_proto(inner, is_chunk_root=False)
    assert c.level == "L3", c.mismatches


def test_straight_child_certifies_even_when_parent_has_while(tmp_path):
    """The decoupling this design exists for: a while-y main must not poison its children."""
    from pyluadec.structure.structured import emit_certified_chunk
    root = _proto(
        "local f = function(a, b) return a + b end\n"
        "local i = 0 while i < 3 do i = i + f(1, 0) end return i", tmp_path)
    out = emit_certified_chunk(root)
    assert out.certs["main"].level == "L1"          # while → main falls back
    assert out.certs["main_0"].level == "L3"        # straight child certifies independently
    assert b"__pld_pc" in out.source                # artifact is the fallback chunk (root L1)


def test_fully_structured_chunk_ships_structured_source(tmp_path):
    from pyluadec import oracle
    from pyluadec.structure.structured import emit_certified_chunk
    root = _proto("local a = 1 if a < 2 then print('y') else print('n') end", tmp_path)
    out = emit_certified_chunk(root)
    assert out.certs["main"].level == "L3"
    assert b"__pld_pc" not in out.source            # structured artifact
    oracle.compile_source(out.source)


def test_output_always_compiles(tmp_path):
    from pyluadec import oracle
    from pyluadec.structure.structured import emit_certified_chunk
    for src in ("local a = 1 return a",
                "local i = 0 while i < 3 do i = i + 1 end return i",
                "for i = 1, 3 do print(i) end",
                "local n = 0 local f = function() return n end print(f())"):
        out = emit_certified_chunk(_proto(src, tmp_path))
        oracle.compile_source(out.source)


def test_l3_really_means_roundtrip(tmp_path):
    from pyluadec import oracle
    from pyluadec.emit.lua import print_chunk
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.structured import certify_proto
    from pyluadec.verify.normalize import NORMALIZATIONS, compare_protos
    p = _proto("local a = 1 local b = 2 print(a + b)", tmp_path)
    assert certify_proto(p, is_chunk_root=True).level == "L3"
    src = print_chunk(p)
    recompiled = load_bytes(oracle.compile_source(src.encode(), strip=True))
    assert compare_protos(p, recompiled, level=len(NORMALIZATIONS)) == []
```

Run: `uv run pytest tests/test_structured_certify.py -v` → FAIL

- [ ] **Step 2: 实现 `src/pyluadec/structure/structured.py`**

```python
"""Per-proto L3 certification with wrapper isolation, and chunk assembly (spec §4, §5).

A proto certifies L3 iff the structured print of ITS OWN SUBTREE recompiles to a
proto matching the original under the normalization ladder. Certification is
per-proto so one unstructurable function cannot poison its siblings' levels;
the shipped chunk source is structured only when the ROOT certifies (which
covers the whole tree), otherwise the semantically-exact fallback chunk ships.
No unverified structured code is ever returned.
"""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.emit.lua import print_chunk, _print_proto_body
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.ingest import Proto, load_bytes
from pyluadec import oracle
from pyluadec.sir.build import StructureError
from pyluadec.structure.fallback import emit_chunk
from pyluadec.verify.certify import certify_l3
from pyluadec.verify.ledger import structural_hash
from pyluadec.verify.normalize import Mismatch, NORMALIZATIONS, compare_protos


@dataclass(frozen=True)
class ProtoCert:
    level: str                       # "L3" | "L1"
    rung: int | None
    mismatches: tuple[Mismatch, ...]


@dataclass(frozen=True)
class ChunkOutcome:
    source: bytes
    certs: dict[str, ProtoCert]


_L1 = ProtoCert(level="L1", rung=None, mismatches=())


def certify_proto(proto: Proto, *, is_chunk_root: bool) -> ProtoCert:
    if is_chunk_root:
        src = print_chunk(proto)
        if src is None:
            return _L1
        cert = certify_l3(proto, src.encode())
        return ProtoCert(cert.level, cert.rung, cert.mismatches)
    upval_names = tuple(f"u{i}" for i in range(proto.nups))
    try:
        body = _print_proto_body(proto, depth=1, upval_names=upval_names)
    except (StructureError, ReconstructError):
        return _L1
    params = ", ".join(f"l1_{i}" for i in range(proto.numparams))
    if proto.is_vararg & 2:
        params = params + (", ..." if params else "...")
    decls = ("local " + ", ".join(upval_names) + "\n") if upval_names else ""
    wrapper = f"{decls}return function({params})\n{body}end\n"
    try:
        recompiled = load_bytes(oracle.compile_source(wrapper.encode(), strip=True))
    except oracle.LuaCompileError:
        return _L1
    if len(recompiled.subprotos) != 1:
        return _L1
    candidate = recompiled.subprotos[0]
    last: tuple[Mismatch, ...] = ()
    for k in range(len(NORMALIZATIONS) + 1):
        diffs = compare_protos(proto, candidate, level=k)
        if not diffs:
            return ProtoCert("L3", k, ())
        last = tuple(diffs)
    return ProtoCert("L1", None, last)


def emit_certified_chunk(root: Proto) -> ChunkOutcome:
    from pyluadec.pipeline import walk_proto_paths
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    memo: dict[str, ProtoCert] = {}
    certs: dict[str, ProtoCert] = {}
    for path, p in protos.items():
        h = structural_hash(p)
        if h not in memo:
            memo[h] = certify_proto(p, is_chunk_root=(path == "main"))
        certs[path] = memo[h]
    if certs["main"].level == "L3":
        src = print_chunk(root)
        assert src is not None            # main certified ⇒ print succeeded
        return ChunkOutcome(source=src.encode(), certs=certs)
    return ChunkOutcome(source=emit_chunk(root), certs=certs)
```

（实现说明：wrapper 的参数名 `l1_{i}` 必须与 `_print_proto_body(depth=1)` 里 `name_for(i, 1)` 的合成一致——若 `name_for` 实现是 `l{depth}_{reg}` 则二者天然一致，改任何一边都要同步。memo 键用 structural_hash 时注意：同哈希的 proto 出现在 main 位置与嵌套位置会共享结果，而 main 的认证走 chunk 路径——实践中 main 与嵌套函数结构哈希相同的概率为零（main 是 vararg 顶层），若真撞上，按第一次出现的路径认证，无碍健全性（两条路径的认证语义等价，只是 wrapper 不同）。）

Run: `uv run pytest tests/test_structured_certify.py -v` → PASS

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: per-proto L3 certification with wrapper isolation and certified chunk assembly"
```

---

### Task 8: pipeline/台账接线 + M3 出口门 + 面板升级

**Files:**
- Modify: `src/pyluadec/pipeline.py`, `scripts/run_corpus.py`, `scripts/ledger_dashboard.py`
- Modify (regenerate): `corpus/ledger.jsonl`
- Test: `tests/test_pipeline_structured.py`, `tests/test_m3_exit.py`

**Interfaces:**
- Consumes: Task 7 `emit_certified_chunk`/`ChunkOutcome`/`ProtoCert`。
- Produces:
  - `pipeline.decompile_chunk(root) -> DecompileResult`：改为调 `emit_certified_chunk`，逐 proto 等级来自 `ChunkOutcome.certs`。`DecompileResult` 增字段 `levels: dict[str, str]`（proto_path → "L3"|"L1"）与 `rungs: dict[str, int | None]`；confession 只对 `level=="L1"` 的 proto 记 `fallback-state-machine`，L3 的 proto **不记 confession**（这是「等级上升、confession 下降」的 ratchet 信号）。产物源码由 `ChunkOutcome.source` 决定（root L3 → 结构化文件；否则 fallback 文件——与逐 proto 等级解耦，见 Task 7 的定量依据）。
  - `run_corpus.py`：`LedgerEntry.level` 取自 outcome；`l3_level` 取 `rung`；`fallback` = `not structured`；打印新增 `structured N/M protos (P%)`。
  - `ledger_dashboard.py`：按等级分列计数、列出 L3 占比、**点名**任何 `compile_ok=false` 或 `L0` 的文件（backlog item：面板从不点名）。
  - `tests/test_m3_exit.py`：M3 出口门——L3 认证的 unique proto 占比 > 50%。

- [ ] **Step 1: 写 pipeline + 出口门失败测试**

`tests/test_pipeline_structured.py`：

```python
def test_decompile_chunk_records_levels():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(b"local a = 1 local b = 2 print(a + b)")
    res = decompile_chunk(load_bytes(bc))
    assert res.levels["main"] == "L3"
    assert res.confessions_by_proto.get("main", []) == []     # L3 protos confess nothing
    oracle.compile_source(res.source)


def test_fallback_chunk_still_confesses():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(b"local i = 0 while i < 3 do i = i + 1 end return i")
    res = decompile_chunk(load_bytes(bc))
    assert res.levels["main"] == "L1"
    assert res.confessions_by_proto["main"][0]["reason"] == "fallback-state-machine"


def test_mixed_chunk_levels_are_per_proto():
    """A while-y main must not poison its straight child's level (Task 7 design)."""
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(
        b"local f = function(a, b) return a + b end\n"
        b"local i = 0 while i < 3 do i = i + f(1, 0) end return i")
    res = decompile_chunk(load_bytes(bc))
    assert res.levels["main"] == "L1"
    assert res.levels["main_0"] == "L3"
    assert res.confessions_by_proto["main_0"] == []
```

`tests/test_m3_exit.py`：

```python
import json
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "corpus" / "ledger.jsonl"


def test_m3_exit_majority_of_unique_protos_are_l3():
    entries = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    assert entries
    l3 = sum(1 for e in entries if e["level"] == "L3")
    frac = l3 / len(entries)
    assert frac > 0.50, f"only {l3}/{len(entries)} ({frac:.1%}) unique protos are L3"


def test_every_entry_still_compiles_and_no_l0():
    entries = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    assert all(e["compile_ok"] for e in entries)
    assert all(e["level"] in ("L1", "L2", "L3") for e in entries)


def test_l3_entries_carry_a_rung_and_no_confessions():
    entries = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    for e in entries:
        if e["level"] == "L3":
            assert e["l3_level"] is not None
            assert e["confessions"] == []
            assert e["fallback"] is False


def test_ledger_still_covers_full_corpus(corpus_dir):
    entries = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    files = {o["file"] for e in entries for o in e["occurrences"]}
    assert files == {f.name for f in corpus_dir.glob("*.lua")}
    assert sum(len(e["occurrences"]) for e in entries) == 1944
```

Run: `uv run pytest tests/test_pipeline_structured.py -v` → FAIL

- [ ] **Step 2: 接线 pipeline / run_corpus / dashboard**

`pipeline.py` 的 `decompile_chunk` 改为：

```python
@dataclass
class DecompileResult:
    source: bytes
    confessions_by_proto: dict[str, list[dict]]
    levels: dict[str, str]
    rungs: dict[str, int | None]


def decompile_chunk(root: Proto) -> DecompileResult:
    from pyluadec.structure.structured import emit_certified_chunk
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    out = emit_certified_chunk(root)
    levels = {path: out.certs[path].level for path in protos}
    rungs = {path: out.certs[path].rung for path in protos}
    confessions = {
        path: ([] if levels[path] == "L3" else
               [{"pc_lo": 1, "pc_hi": len(p.code),
                 "reason": "fallback-state-machine", "pass": "structure.fallback"}])
        for path, p in protos.items()
    }
    return DecompileResult(source=out.source, confessions_by_proto=confessions,
                           levels=levels, rungs=rungs)
```

`run_corpus.py`：`LedgerEntry(... level=..., l3_level=res.rungs[path], fallback=(res.levels[path] != "L3") ...)`；合并同 shash 时 `level` 取**更高**者（L3 > L1，等级只升不降），`fallback` 相应取 and。打印行增加结构化比例。

`ledger_dashboard.py`：增加 `level L3` / `level L1` 计数与 L3 占比行；增加 `problem entries` 段落，遍历 `compile_ok=false` 或 `level=="L0"` 的条目并逐条打印 `shash[:12]` 与首个 `occurrences` 的 `file`/`proto_path`（面板从不点名的 deferred minor 到此关闭）。

- [ ] **Step 3: 全语料重跑，观察 L3 比例**

```bash
PYLUADEC_CORPUS_DIR=... uv run python scripts/run_corpus.py
PYLUADEC_CORPUS_DIR=... uv run python scripts/ledger_dashboard.py
```

Expected: `compiled 229/229`；L3 比例应落在 **55%–80%** 区间（逐 proto 子树认证的理论上界 80.3%；实际受重建覆盖度、条件极性、upvalue 顺序等影响）。产物层面：约 93/229 个文件（整树在能力集内的）应以结构化源码出货，其余仍是 fallback 文件——这是设计而非缺陷。若低于 50%：**不要放宽认证**，改为读 `ProtoCert.mismatches` 聚类（对全语料 L1 条目按 mismatch 的 field/首个 opcode 分组计数），找出最高频的重建缺陷（大概率是某个 opcode 的重建规则或 local/temp 分类边界），补 Task 5/6 的规则后重跑。认证门是资产不是障碍——它精确告诉你哪里错了。

- [ ] **Step 4: 提交重生成的台账 + 确认不动点门仍绿**

```bash
PYLUADEC_CORPUS_DIR=... uv run pytest tests/test_ledger_ratchet.py tests/test_m3_exit.py -v
git add -A && git commit -m "feat: M3 exit — structured emission wired into pipeline, ledger records L3 certification"
```

Expected: 不动点测试仍绿（重生成后台账与提交内容字节一致）；`test_m3_exit` 的 L3 占比 > 50%。

---

### Task 9: 全局状态探针（L1.5 门，backlog item 3）

**Files:**
- Create: `scripts/probe_global_state.py`, `scripts/probe_global_state.lua`
- Test: `tests/test_global_state_probe.py`

**Interfaces:**
- Consumes: `pyluadec.pipeline.decompile_file`；`pyluadec.oracle.run_bytes`/`lua_sz4`。
- Produces:
  - `probe_global_state.lua`：加载目标 chunk、`pcall` 执行、把全局表增量确定性序列化（键排序、深度上限 4、数字 `%.17g`、函数/userdata/thread 打类型占位、环检测）后打印。
  - `probe_global_state.py`：`probe(path_or_bytes, is_source) -> str` 与 CLI 全语料模式；对每个语料文件跑「原始字节码」与「反编译产物」两次，比对 stdout。
  - `tests/test_global_state_probe.py`：全语料 229/229 全局状态一致；且探针非空洞（对注入错误能报差异）。

**Phase 2 final review 已实测**：229 文件全部全局状态一致、0 发散、0 错误、且**无一为空**。本 Task 是把那次一次性验证固化成常驻门，并让它在 M3 的结构化产物上继续成立——结构化输出若语义错了，这个门会抓到（认证门管字节级、这个门管运行级，互补）。

- [ ] **Step 1: 写探针失败测试**

`tests/test_global_state_probe.py`：

```python
def test_probe_is_deterministic_and_nonempty(tmp_path):
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    bc = oracle.compile_source(b"X = {b = 2, a = 1} Y = 'hi' Z = 3.5")
    a = probe(bc, is_source=False)
    b = probe(bc, is_source=False)
    assert a == b and a.startswith("OK|") and "X=" in a and "Y=" in a


def test_probe_detects_a_difference():
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    a = probe(oracle.compile_source(b"X = 1"), is_source=False)
    b = probe(oracle.compile_source(b"X = 2"), is_source=False)
    assert a != b


def test_corpus_global_state_matches(corpus_dir):
    """Original bytecode and decompiled output must produce identical global state."""
    from pyluadec.pipeline import decompile_file
    from scripts.probe_global_state import probe
    bad = []
    files = sorted(corpus_dir.glob("*.lua"))
    for f in files:
        orig = probe(f.read_bytes(), is_source=False)
        dec = probe(decompile_file(f).source, is_source=True)
        if orig != dec:
            bad.append(f.name)
    assert len(files) == 229
    assert bad == [], f"{len(bad)} files diverge: {bad[:5]}"
```

Run: `uv run pytest tests/test_global_state_probe.py -v` → FAIL

- [ ] **Step 2: 实现探针**

`scripts/probe_global_state.lua` —— 用 Phase 2 final review 留下的版本（已在 `docs/runbooks/m3-backlog.md` 的「Global-state probe」节全文收录，直接取用）。

`scripts/probe_global_state.py`：

```python
"""L1.5 gate: compare observable global-table state between original bytecode and
decompiled output, without the game engine. See docs/runbooks/m3-backlog.md item 3."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "probe_global_state.lua"


def probe(payload: bytes, *, is_source: bool, timeout: float = 30.0) -> str:
    from pyluadec import oracle
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        r = subprocess.run([str(oracle.lua_sz4()), str(PROBE), str(f)],
                           capture_output=True, timeout=timeout, cwd=td)
        return r.stdout.decode("utf-8", "replace")


def main() -> int:
    from pyluadec.pipeline import decompile_file
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    files = sorted(corpus.glob("*.lua"))
    bad = []
    for f in files:
        if probe(f.read_bytes(), is_source=False) != probe(decompile_file(f).source, is_source=True):
            bad.append(f.name)
    print(f"global-state: {len(files) - len(bad)}/{len(files)} identical"
          + (f"; divergent: {bad[:10]}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
```

（`probe` 的 `is_source` 是关键字参数，测试里按关键字调用；实现签名保持一致。`scripts` 可导入依赖仓库根 `conftest.py`——Phase 1 已就位。）

Run: `uv run pytest tests/test_global_state_probe.py -v` → PASS（期望 229/229）

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: global-state probe as a standing L1.5 gate over the corpus"
```

---

### Task 10: 效应表-发射器一致性门 + 文档收尾

**Files:**
- Create: `tests/test_effects_emitter_consistency.py`
- Create: `docs/runbooks/structured-pipeline.md`
- Modify: `CHANGELOG.md`, `CLAUDE.md`, `docs/runbooks/m3-backlog.md`
- Test: 上述新测试

**Interfaces:** 无新代码接口；本 Task 固化 backlog item 2 并沉淀文档。

**effects-vs-emitter 一致性门**（backlog item 2，Phase 2 final review 已跑通、零发散）：对全语料每条指令，重建/发射模板触及的寄存器下标必须是 `effects.reads | effects.writes` 的子集（跳过 open region，那是 `__pld_top` 相对的）。这把 `lift/effects.py` 与两个发射器（fallback + structured）的**两份独立 lvm.c 转录**机械对齐，防止 M3 之后二者漂移。

- [ ] **Step 1: 写一致性门测试**

`tests/test_effects_emitter_consistency.py`：

```python
def test_effects_cover_registers_touched_by_reconstruction(corpus_dir):
    """effects.reads|writes must be a superset of the registers reconstruction touches.

    Guards against drift between lift/effects.py and the emitters — two independent
    hand-transcriptions of lvm.c. Open regions (reads_open/writes_open) are skipped:
    they are __pld_top-relative and not statically bounded.
    """
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    from pyluadec.lift.opcodes import Op, isk
    checked = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            fn = lift_proto(p)
            for li in fn.instrs.values():
                fx = li.effects
                if fx.reads_open or fx.writes_open:
                    continue
                touched = _registers_touched(li.ri)
                assert touched <= (fx.reads | fx.writes), (
                    f"{f.name} pc {li.ri.pc} {li.ri.op.name}: "
                    f"touches {sorted(touched - (fx.reads | fx.writes))} "
                    f"outside effects {sorted(fx.reads | fx.writes)}")
                checked += 1
    assert checked > 100_000


def _registers_touched(ri):
    """Registers an emitter template must read or write for this instruction."""
    from pyluadec.lift.opcodes import Op, isk
    op, a, b, c = ri.op, ri.a, ri.b, ri.c
    t = set()
    if op in (Op.MOVE, Op.UNM, Op.NOT, Op.LEN, Op.TESTSET):
        t = {a, b}
    elif op in (Op.LOADK, Op.LOADBOOL, Op.NEWTABLE, Op.GETGLOBAL, Op.GETUPVAL, Op.CLOSURE):
        t = {a}
    elif op in (Op.SETGLOBAL, Op.SETUPVAL, Op.TEST):
        t = {a}
    elif op is Op.LOADNIL:
        t = set(range(a, b + 1))
    elif op in (Op.GETTABLE,):
        t = {a, b} | ({c} if not isk(c) else set())
    elif op is Op.SELF:
        t = {a, a + 1, b} | ({c} if not isk(c) else set())
    elif op is Op.SETTABLE:
        t = {a} | ({b} if not isk(b) else set()) | ({c} if not isk(c) else set())
    elif op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
        t = {a} | ({b} if not isk(b) else set()) | ({c} if not isk(c) else set())
    elif op in (Op.EQ, Op.LT, Op.LE):
        t = ({b} if not isk(b) else set()) | ({c} if not isk(c) else set())
    elif op is Op.CONCAT:
        t = {a} | set(range(b, c + 1))
    elif op is Op.FORPREP:
        t = {a, a + 1, a + 2}
    elif op is Op.FORLOOP:
        t = {a, a + 1, a + 2, a + 3}
    elif op is Op.TFORLOOP:
        t = {a, a + 1, a + 2} | set(range(a + 3, a + 3 + c))
    elif op in (Op.CALL, Op.TAILCALL):
        t = {a} | (set(range(a + 1, a + b)) if b else set()) \
              | (set(range(a, a + c - 1)) if c else set())
    elif op is Op.RETURN:
        t = set(range(a, a + b - 1)) if b else set()
    elif op is Op.VARARG:
        t = set(range(a, a + b - 1)) if b else set()
    elif op is Op.SETLIST:
        t = {a} | (set(range(a + 1, a + b + 1)) if b else set())
    elif op in (Op.JMP, Op.CLOSE):
        t = set()
    return t
```

Run: `uv run pytest tests/test_effects_emitter_consistency.py -v` → 期望 PASS（Phase 2 已实测零发散）。若 FAIL：**这是真信号**——某条 effects 行与发射器不一致，逐条对照 `lvm.c` 判定哪边错，修错的那边，不要放宽断言。

- [ ] **Step 2: 写 `docs/runbooks/structured-pipeline.md`**

全文写入（不留提纲），涵盖：
- M3 管线形态：`ingest → lift → cfg → sir.build → express.reconstruct → emit.lua → certify_l3 →（通过用结构化 / 否则 fallback）→ ledger`，每层模块路径与关键函数名。
- **认证门是唯一落地关口**：`emit_certified_chunk` 的不变式（永不返回未认证的结构化代码；产物为结构化 ⟺ root 认证 L3），以及为什么这让区域识别/内联的 bug 只会降低 L3 比例、不会产出错误代码。
- 归一化阶梯现状：L3.0 严格、L3.1 剥行信息（`_strip_lineinfo` 的健全性论证：行信息不参与 VM 语义，只影响错误消息位置与调试；剥它不会放过任何语义差异，因为 code/constants/结构字段全部保留比对）。`LADDER_VERSION` 版本化纪律。
- local/temp 分类与保守内联判据（`_adjacent_pure`），以及**为什么放宽它属于 M4**（效应格三档标定）。
- 常用操作：单文件结构化反编译并看认证结果；全语料跑门；看面板；用 mismatches 调试某个未认证函数（打印 `certify_l3` 的 mismatches，对照 `luac_sz4 -l -l` 原始 listing）。
- 台账新字段语义：`level` L3/L1、`l3_level` 是通过的归一化级号、`fallback` 布尔、L3 条目 confession 为空。ratchet 纪律：等级只升不降、confession 只降不升。
- 现存能力边界：while/repeat/混合回边未结构化（连同其祖先闭包）诚实留在 L1，占语料约 20%；这是 M3 之后的增量。
- 与 fallback runbook（`decompile-pipeline.md`）的关系：fallback 仍是地板，两者共存。

- [ ] **Step 3: 更新 CHANGELOG / CLAUDE.md / m3-backlog.md**

- `CHANGELOG.md` 加 M3 条目：结构化主干上线，L3 认证比例（填实测值），L3.1 归一化级，全局状态探针与 effects 一致性门成为常驻门。**照实写能力边界**（while/repeat 未覆盖）。
- `CLAUDE.md` 追加 M3 现状节：新模块布局（`sir/`、`express/`、`emit/`）、认证门纪律、新命令（`scripts/probe_global_state.py`）、台账新字段。不重写既有 Phase 1/2 内容。
- `docs/runbooks/m3-backlog.md`：勾掉本计划完成的 item 0/1/2/3/4；item 5（表布局保真）标注部分完成（表构造重建已做，presize 保真由 L3 认证间接保证——凡认证 L3 的表构造，重编译必然产生同样的 NEWTABLE presize）；把未完成项与 M3 新发现的 deferred minor 重写为 M4 backlog。

- [ ] **Step 4: 全量回归**

Run: `PYLUADEC_CORPUS_DIR=... uv run pytest -v`
Expected: 全绿（Phase 1/2 全部既有测试 + M3 新增）。

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "docs: structured pipeline runbook, M3 changelog, effects-emitter consistency gate"
```

---

## 完成定义（M3 出口，对照 spec §7）

- [ ] **多数 unique proto 脱离 fallback 并达 L3**：`tests/test_m3_exit.py` 断言 L3 占比 > 50%（理论子树闭合上界 80.3%）。
- [ ] 支配树区域识别就位且被结构化发射实际消费（`sir.build` → `emit.lua`），CFG/支配树不再是「建而不用」。
- [ ] **PC 认领审计**：`all_claimed(region) == set(fn.instrs)` 在 `build_sir` 每次出口强制，全语料无违例。
- [ ] 归一化阶梯 L3.1 上线，健全性单独论证 + `LADDER_VERSION` 版本化。
- [ ] 认证门不变式：`emit_certified_chunk` 永不返回未认证的结构化代码（产物结构化 ⟺ root L3）；229/229 仍全部可编译。
- [ ] 台账记录逐 proto 等级与归一化级号；L3 条目无 confession；不动点门仍绿；等级只升不降。
- [ ] 全局状态探针（229/229）与 effects-发射器一致性门成为常驻测试。
- [ ] 里程碑收尾走 superpowers 流程：requesting-code-review + verification-before-completion。

## 显式非目标（M4+ 范围，本计划不做）

- **while / repeat / 混合与不可归约回边的结构化**——约 152 个 unique proto 及其祖先闭包留在 L1。这是 M3 之后最大的单项增量。
- **效应格三档标定与完整证明门控内联**（spec M4）：M3 只做无条件健全的保守内联（`_adjacent_pure`）；放开 READ_HEAP/元方法风险重排、用 229 语料实测标定默认档，属 M4。
- **L2 差分执行认证**（stub 环境 + trace 比对 + 覆盖率徽章）与按键序列回归——spec M5。Task 9 的全局状态探针是 L1.5，不是 L2。
- **美化 pass 链与 pass registry**（spec §4 的 `Pass` 协议、apply→verify→commit/rollback）——M4。M3 的结构化是单体重建，不是 pass 链。
- **变量名语义化**（`l0_0` → 有意义的名字）——需要 debug 段或启发式，本语料 strip 过，属 M4+ 且价值存疑。
- **完整 Ratchet CI**（baseline diff、等级降级即 fail、`git bisect` 集成）——spec §5 完整形态仍属后续；M3 只保证台账字段足以支撑它。
- 旧项目 `test_ir_pipeline.py` 86 例的转译清单——依 spec §8 用 M3 的逐函数等级数据生成，属 M4 输入。

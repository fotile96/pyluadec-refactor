# Phase 2 (M2 保底闭环) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立反编译最底层闭环：lift 层（38 opcode 效应表 = 公理层）、CFG + 支配树、fallback 状态机发射器（任何函数都能发射语义精确的 pc 派发循环）、L3.0 归一化比对器、认证台账 v1——出口是 229 语料 100% 产出可编译 Lua 源码 + 台账面板上线。

**Architecture:** 六层管线（spec §3）中的 ②lift/③structure(仅 fallback)/⑤verify 三层落地。指令解码与效应标注为纯查表；CFG 从 LIR 后继关系构建并被 fallback 发射器**实际使用**（按基本块分状态，避免旧项目 CFG 空转的教训）；发射器把寄存器放进 table、被捕获寄存器装箱（box），逐 opcode 用与 VM 语义逐条对应的 Lua 源码模板还原；正确性由差分执行测试（自编译源码 → 反编译 → 双跑 diff stdout）+ 全语料编译门保证。台账以归一化结构哈希为主键记录每个 proto 的认证等级（M2 全部为 L1 fallback）。

**Tech Stack:** Python ≥3.12（uv 管理）、pytest、既有 `pyluadec.ingest` 层与 `build/luac_sz4`/`lua_sz4` oracle（Phase 1 产物）。无新第三方依赖。

## Global Constraints

- 代码中禁止绝对路径；语料一律经 `PYLUADEC_CORPUS_DIR`；构建产物目录经 `PYLUADEC_BUILD_DIR`（默认仓库根 `build/`）。
- 一切源自 bytecode 的字符串在 Python 侧一律 `bytes`，绝不 decode；数字常量比较按原始 8 字节 payload 逐位。
- `corpus/golden/` 只读；`vendor/` pristine；一切 Lua 源修改经 `native/patches/*.patch`。
- 每个 Task 以 commit 结束；测试命令统一 `uv run pytest`；依赖语料的测试用 `corpus_dir` fixture（无语料自动 skip）。
- 指令语义与官方文档冲突时以 `a-no-frills-introduction-to-lua-5.1-vm-instructions.pdf` 为准；两者存疑时以 `vendor/lua-5.1/src/lvm.c` 实际代码为准（它就是本项目的执行 oracle）。
- PC 约定：Python 侧全程 **1-based**（与 luac listing 一致，便于对照 golden）。
- 发射器生成的一切辅助名以 `__pld_` 为前缀（语料扫描确认无 `__` 前缀全局名，发射时仍须 assert）。
- 台账 `corpus/ledger.jsonl` check-in；反编译产物 `build/decompiled/` 不入库（已被 `build/` gitignore 覆盖）。

## 语料实测事实（2026-08-10 扫描，设计依据）

- 1944 protos / 229 文件；单文件最多 **147** 个 proto（→ 闭包工厂放 table，不用 local，避开 200 局部变量上限）。
- 最大 `maxstacksize` 61；单 proto 最多 3305 指令。
- `is_vararg` 取值 {0, 2, 3}；**VARARG_NEEDSARG(4) 从未出现** → 无需 Lua 5.0 `arg` 表兼容。
- **SETLIST C==0 从未出现**；lift 层仍须正确处理（消耗下一指令字），但无语料压力。
- 全局名全部是合法标识符，无 `__` 前缀 → 全局访问可直接按标识符发射。
- 数字常量全部为整数值 double（22120 个），无小数/nan/inf/-0.0；bool 常量 231 个（EQ 与 bool 常量比较真实存在）。
- 语料未用到的 opcode：**SELF、POW、UNM、NOT、CLOSE**——效应表与发射器仍须完整实现（公理层不允许缺行），用自编译源码测试。

### 计划撰写时已实测验证的两条承重假设（2026-08-10，用 `build/luac_sz4` 实跑）

1. **大型 if/elseif 派发链可编译**：500 / 2000 / 4000 分支的 `while true do if __pld_pc == 1 then … elseif … end end` 全部 `luac_sz4` 编译通过（rc=0）。语料最大 proto 为 3305 指令 → 最坏情形也在实测头寸内。用 `elseif` 平铺链（而非嵌套 `if`）是必要的：嵌套会撞 `LUAI_MAXCCALLS`(200) 语法嵌套上限。
2. **三份 CASES 列表合计覆盖 38/38 opcode**（Task 6/7/8 的差分用例，用真实 luac 编译后统计）：STRAIGHT_LINE_CASES 覆盖 22 个、CONTROL_CASES 补 13 个、CLOSURE_CASES 补 CLOSE + SETUPVAL。
   - **实测踩坑，已修入用例表**：`local a = false or 3` 这类 **and/or 赋值只产 TESTSET，不产 TEST**；TEST 必须由 `if <local> then` / `while <local> do` 这种「真值测试且不赋值」的形态触发。CONTROL_CASES 中三条 TEST 专用例即为此。
   - `CLOSE` 由 CLOSURE_CASES 的循环捕获用例（`for i … fs[i] = function() return i end`）产出，**不是**由 do-end 块产出——被捕获的局部量声明在块外时离开块不发 CLOSE。
   - 常量间算术会被 luac 编译期折叠：`print(1 + 2)` 发不出 ADD。ADD/MUL/POW/DIV/MOD/SUB/UNM/LEN/NOT 的用例操作数**必须**放局部变量。

---

### Task 0: 工程杂务（uv_build 上界 + ingest 异常统一）

**Files:**
- Modify: `pyproject.toml:14`
- Modify: `src/pyluadec/ingest/header.py`
- Modify: `src/pyluadec/ingest/dispatch.py`
- Modify: `src/pyluadec/ingest/__init__.py`
- Test: `tests/test_ingest_errors.py`

**Interfaces:**
- Consumes: 现有 `pyluadec.ingest`（`parse_header`、`BadHeader`、`load_bytes`）。
- Produces:
  - `pyluadec.ingest.IngestError(Exception)` —— ingest 层一切错误的基类
  - `BadHeader(IngestError, ValueError)` —— 保持既有 ValueError 兼容
  - `parse_header` 校验全部 12 字节（fmt/endian/sizeof_int/sizeof_instr/sizeof_number/integral/sizeof_sizet），不再只查签名与版本
  - `load_bytes` 把 bridge 的裸 `RuntimeError` 包为 `IngestError`

- [ ] **Step 1: 放宽 uv_build 版本上界**

`pyproject.toml` 中 `requires = ["uv_build>=0.11.16,<0.12.0"]` 改为：

```toml
requires = ["uv_build>=0.11.16,<1"]
```

（Mac mini 上 Homebrew uv 已是 0.12.1，旧上界每次构建告警，且是未来硬失败的伏笔。）

Run: `uv sync && uv run pytest -q`
Expected: 无 `does not contain the current uv version` 告警；23 项测试全过。

- [ ] **Step 2: 写失败测试**

`tests/test_ingest_errors.py`：

```python
import subprocess
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"


def _compile_sz4(src: str, tmp: Path) -> bytes:
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return o.read_bytes()


def test_bad_header_fields_raise_badheader(tmp_path):
    from pyluadec.ingest import BadHeader, parse_header
    good = bytearray(_compile_sz4("return 1", tmp_path))
    for byte_idx, bad_value in [(5, 1), (6, 0), (7, 8), (9, 8), (10, 4), (11, 1)]:
        blob = bytearray(good)
        blob[byte_idx] = bad_value
        with pytest.raises(BadHeader):
            parse_header(bytes(blob))


def test_unsupported_sizet_width_raises_badheader(tmp_path):
    from pyluadec.ingest import BadHeader, parse_header
    blob = bytearray(_compile_sz4("return 1", tmp_path))
    blob[8] = 2
    with pytest.raises(BadHeader):
        parse_header(bytes(blob))


def test_truncated_body_raises_ingest_error(tmp_path):
    from pyluadec.ingest import BadHeader, IngestError, load_bytes
    blob = _compile_sz4("return 1", tmp_path)
    with pytest.raises(IngestError):
        load_bytes(blob[:40])          # header 完整、函数体截断 → bridge 报错须被包装
    with pytest.raises(BadHeader):
        load_bytes(b"\x1bLuaQ")        # header 都不完整


def test_badheader_is_ingest_error_and_valueerror():
    from pyluadec.ingest import BadHeader, IngestError
    assert issubclass(BadHeader, IngestError)
    assert issubclass(BadHeader, ValueError)
```

Run: `uv run pytest tests/test_ingest_errors.py -v`
Expected: FAIL（`IngestError` 不存在；坏 fmt 字节不抛错）

- [ ] **Step 3: 实现**

`src/pyluadec/ingest/header.py` —— `BadHeader` 定义与 `parse_header` 校验改为：

```python
class IngestError(Exception):
    """Base class for all ingest-layer failures."""


class BadHeader(IngestError, ValueError):
    pass


def parse_header(blob: bytes) -> Header:
    if len(blob) < 12 or blob[:4] != SIGNATURE:
        raise BadHeader("not a Lua bytecode chunk")
    h = Header(
        version=blob[4], fmt=blob[5], little_endian=blob[6] == 1,
        sizeof_int=blob[7], sizeof_sizet=blob[8], sizeof_instr=blob[9],
        sizeof_number=blob[10], integral=blob[11] == 1,
    )
    if h.version != 0x51:
        raise BadHeader(f"unsupported version 0x{h.version:02x}")
    if h.fmt != 0:
        raise BadHeader(f"unsupported format {h.fmt} (expected 0 = official)")
    if not h.little_endian:
        raise BadHeader("big-endian bytecode not supported")
    if h.sizeof_int != 4:
        raise BadHeader(f"unsupported sizeof(int)={h.sizeof_int} (expected 4)")
    if h.sizeof_sizet not in (4, 8):
        raise BadHeader(f"unsupported serialized size_t width {h.sizeof_sizet}")
    if h.sizeof_instr != 4:
        raise BadHeader(f"unsupported sizeof(Instruction)={h.sizeof_instr} (expected 4)")
    if h.sizeof_number != 8:
        raise BadHeader(f"unsupported sizeof(lua_Number)={h.sizeof_number} (expected 8)")
    if h.integral:
        raise BadHeader("integral lua_Number not supported (corpus is IEEE double)")
    return h
```

`src/pyluadec/ingest/dispatch.py` —— `load_bytes` 包装 bridge 错误：

```python
from .header import IngestError, parse_header


def load_bytes(blob: bytes, chunkname: str = "=chunk") -> Proto:
    h = parse_header(blob)
    bridge = _bridge_for(h.sizeof_sizet)
    try:
        d = bridge.load_bytecode(blob, chunkname)
    except RuntimeError as e:
        raise IngestError(f"bridge load failed: {e}") from e
    return from_bridge_dict(d)
```

`src/pyluadec/ingest/__init__.py` —— 导出追加 `IngestError`（`from .header import ... IngestError`，加入 `__all__`）。

（`dispatch._bridge_for` 对 4/8 之外宽度的 `ValueError` 分支已被 `parse_header` 前置拦截，保留作防御。）

- [ ] **Step 4: 运行测试**

Run: `uv run pytest tests/test_ingest_errors.py tests/test_ingest.py -v`
Expected: 全 PASS（既有 ingest 测试不回归）

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: widen uv_build bound; unify ingest exceptions under IngestError"
```

---

### Task 1: 指令解码器与 opcode 元数据表

**Files:**
- Create: `src/pyluadec/lift/__init__.py`, `src/pyluadec/lift/opcodes.py`
- Test: `tests/test_opcodes.py`

**Interfaces:**
- Consumes: `pyluadec.ingest.Proto`（`code: tuple[int, ...]` 原始 32 位指令字）；`corpus/golden/listing/*.txt`（解码 oracle）。
- Produces（Task 2/3/6+ 依赖，签名固定）:
  - `class Op(IntEnum)`：38 个成员，`MOVE=0 … VARARG=37`，与 `lopcodes.h` 顺序一致
  - `class Fmt(Enum)`: `iABC, iABx, iAsBx`；`class ArgMode(Enum)`: `N, U, R, K`
  - `OP_SPECS: dict[Op, OpSpec]`，`OpSpec(fmt: Fmt, bmode: ArgMode, cmode: ArgMode)`
  - `@dataclass(frozen=True) RawInstr: pc:int; word:int; op:Op; a:int; b:int; c:int; bx:int; sbx:int`
  - `decode(word: int, pc: int) -> RawInstr`（非法 opcode 抛 `DecodeError(ValueError)`）
  - `isk(x: int) -> bool`、`indexk(x: int) -> int`（RK 判定/取常量下标，BITRK=256）
  - `luac_operand_str(ri: RawInstr) -> str`（复刻 luac `print.c` 的操作数列，golden oracle 用）
  - `LUA_KEYWORDS: frozenset[str]`（发射器判定标识符用）

- [ ] **Step 1: 写失败测试（手工用例 + golden oracle + 合成 listing oracle）**

`tests/test_opcodes.py`：

```python
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
LISTING_DIR = ROOT / "corpus" / "golden" / "listing"

# luac listing 指令行：\t<pc>\t[<line>]\t<OPNAME 左对齐补空格>\t<operands>[\t; comment]
INSTR_LINE_RE = re.compile(r"^\t(\d+)\t\[[^\]]*\]\t(\w+) *\t([-0-9 ]+?)(?:\t;.*)?$")


def test_decode_known_words():
    from pyluadec.lift.opcodes import Op, decode
    # word = op | A<<6 | C<<14 | B<<23
    ri = decode(0x00000000, pc=1)                     # MOVE 0 0
    assert ri.op is Op.MOVE and ri.a == 0 and ri.b == 0
    ri = decode(1 | (2 << 6) | (5 << 14), pc=7)       # LOADK A=2 Bx=5
    assert ri.op is Op.LOADK and ri.a == 2 and ri.bx == 5 and ri.pc == 7
    ri = decode(22 | (0 << 6) | ((131071 - 3) << 14), pc=1)   # JMP sBx=-3
    assert ri.op is Op.JMP and ri.sbx == -3


def test_decode_rejects_bad_opcode():
    import pytest
    from pyluadec.lift.opcodes import DecodeError, decode
    with pytest.raises(DecodeError):
        decode(38, pc=1)          # opcode 38 不存在


def test_isk_indexk():
    from pyluadec.lift.opcodes import indexk, isk
    assert not isk(255) and isk(256) and isk(511)
    assert indexk(256) == 0 and indexk(300) == 44


def _check_against_listing(listing_text: str, protos_flat):
    """listing 的每条指令行 (opname, operand 列) 与我方 decode 结果逐条相等。"""
    from pyluadec.lift.opcodes import decode, luac_operand_str
    it = iter(protos_flat)
    cur = None; idx = 0; checked = 0
    for line in listing_text.splitlines():
        m = INSTR_LINE_RE.match(line)
        if not m:
            if line.startswith(("main <", "function <")):
                cur = next(it); idx = 0
            continue
        pc, opname, operands = int(m.group(1)), m.group(2), m.group(3).strip()
        assert pc == idx + 1
        ri = decode(cur.code[idx], pc=pc)
        assert ri.op.name == opname, f"pc {pc}: {ri.op.name} != {opname}"
        assert luac_operand_str(ri) == operands, f"pc {pc} {opname}: {luac_operand_str(ri)!r} != {operands!r}"
        idx += 1; checked += 1
    return checked


def test_decoder_matches_all_golden_listings(corpus_dir):
    from pyluadec.ingest import load_file
    total = 0
    for lst in sorted(LISTING_DIR.glob("*.txt")):
        name = lst.name[: -len(".txt")]
        root = load_file(corpus_dir / name)
        flat = []
        def walk(p):
            flat.append(p)
            for s in p.subprotos: walk(s)
        walk(root)
        total += _check_against_listing(lst.read_text(), flat)
    assert total > 200_000    # 语料约 21 万条指令，全部核对


def test_decoder_matches_fresh_listing_for_corpus_missing_ops(tmp_path):
    """SELF/POW/UNM/NOT/CLOSE 语料未用到，用现编译的源码补齐 oracle 覆盖。"""
    from pyluadec.ingest import load_file
    src = tmp_path / "t.lua"
    src.write_text(
        "local o = {}\n"
        "function o:m(x) return -x ^ 2, not x, #\"s\" end\n"   # SELF 在调用处
        "local function outer()\n"
        "  local cap = 1\n"
        "  do local inner = function() cap = cap + 1 end inner() end\n"  # CLOSE
        "  return o:m(cap)\n"
        "end\n"
        "return outer()\n")
    out = tmp_path / "t.out"
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(out), str(src)], check=True)
    listing = subprocess.run([str(BUILD / "luac_sz4"), "-l", "-l", str(out)],
                             capture_output=True, text=True, check=True).stdout
    for need in ("SELF", "POW", "UNM", "NOT"):
        assert need in listing        # 用例确实触发了这些 opcode
    root = load_file(out)
    flat = []
    def walk(p):
        flat.append(p)
        for s in p.subprotos: walk(s)
    walk(root)
    assert _check_against_listing(listing, flat) > 0
```

Run: `uv run pytest tests/test_opcodes.py -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 2: 实现 `src/pyluadec/lift/opcodes.py`**

`src/pyluadec/lift/__init__.py` 为空文件。opcodes.py：

```python
"""Lua 5.1 instruction decoding + per-opcode metadata (the axiom layer's ground truth).

Field layout (lopcodes.h): op:6 | A:8 | C:9 | B:9  (Bx = B..C 18 bits, sBx = Bx - 131071).
OP_SPECS 的 fmt/bmode/cmode 逐行转录自 vendor/lua-5.1/src/lopcodes.c 的 luaP_opmodes；
tests/test_opcodes.py 用 golden listing 全语料 21 万条指令核对该表的每一行。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class Op(IntEnum):
    MOVE = 0; LOADK = 1; LOADBOOL = 2; LOADNIL = 3; GETUPVAL = 4
    GETGLOBAL = 5; GETTABLE = 6; SETGLOBAL = 7; SETUPVAL = 8; SETTABLE = 9
    NEWTABLE = 10; SELF = 11; ADD = 12; SUB = 13; MUL = 14; DIV = 15
    MOD = 16; POW = 17; UNM = 18; NOT = 19; LEN = 20; CONCAT = 21
    JMP = 22; EQ = 23; LT = 24; LE = 25; TEST = 26; TESTSET = 27
    CALL = 28; TAILCALL = 29; RETURN = 30; FORLOOP = 31; FORPREP = 32
    TFORLOOP = 33; SETLIST = 34; CLOSE = 35; CLOSURE = 36; VARARG = 37


class Fmt(Enum):
    iABC = "iABC"; iABx = "iABx"; iAsBx = "iAsBx"


class ArgMode(Enum):
    N = "N"   # argument not used
    U = "U"   # used as plain value
    R = "R"   # register (or jump offset)
    K = "K"   # register/constant (RK) or constant index


@dataclass(frozen=True)
class OpSpec:
    fmt: Fmt
    bmode: ArgMode
    cmode: ArgMode


_A, _B, _X = Fmt.iABC, Fmt.iABx, Fmt.iAsBx
_N, _U, _R, _K = ArgMode.N, ArgMode.U, ArgMode.R, ArgMode.K

# 逐行对应 lopcodes.c luaP_opmodes（T/A 位与打印无关，不录）。
OP_SPECS: dict[Op, OpSpec] = {
    Op.MOVE: OpSpec(_A, _R, _N),      Op.LOADK: OpSpec(_B, _K, _N),
    Op.LOADBOOL: OpSpec(_A, _U, _U),  Op.LOADNIL: OpSpec(_A, _R, _N),
    Op.GETUPVAL: OpSpec(_A, _U, _N),  Op.GETGLOBAL: OpSpec(_B, _K, _N),
    Op.GETTABLE: OpSpec(_A, _R, _K),  Op.SETGLOBAL: OpSpec(_B, _K, _N),
    Op.SETUPVAL: OpSpec(_A, _U, _N),  Op.SETTABLE: OpSpec(_A, _K, _K),
    Op.NEWTABLE: OpSpec(_A, _U, _U),  Op.SELF: OpSpec(_A, _R, _K),
    Op.ADD: OpSpec(_A, _K, _K),       Op.SUB: OpSpec(_A, _K, _K),
    Op.MUL: OpSpec(_A, _K, _K),       Op.DIV: OpSpec(_A, _K, _K),
    Op.MOD: OpSpec(_A, _K, _K),       Op.POW: OpSpec(_A, _K, _K),
    Op.UNM: OpSpec(_A, _R, _N),       Op.NOT: OpSpec(_A, _R, _N),
    Op.LEN: OpSpec(_A, _R, _N),       Op.CONCAT: OpSpec(_A, _R, _R),
    Op.JMP: OpSpec(_X, _R, _N),       Op.EQ: OpSpec(_A, _K, _K),
    Op.LT: OpSpec(_A, _K, _K),        Op.LE: OpSpec(_A, _K, _K),
    Op.TEST: OpSpec(_A, _R, _U),      Op.TESTSET: OpSpec(_A, _R, _U),
    Op.CALL: OpSpec(_A, _U, _U),      Op.TAILCALL: OpSpec(_A, _U, _U),
    Op.RETURN: OpSpec(_A, _U, _N),    Op.FORLOOP: OpSpec(_X, _R, _N),
    Op.FORPREP: OpSpec(_X, _R, _N),   Op.TFORLOOP: OpSpec(_A, _N, _U),
    Op.SETLIST: OpSpec(_A, _U, _U),   Op.CLOSE: OpSpec(_A, _N, _N),
    Op.CLOSURE: OpSpec(_B, _U, _N),   Op.VARARG: OpSpec(_A, _U, _N),
}

BITRK = 1 << 8            # 256：operand 的 K 位
MAXARG_sBx = 131071       # (2^18 - 1) >> 1

LUA_KEYWORDS = frozenset(
    "and break do else elseif end false for function if in local nil not or "
    "repeat return then true until while".split())


class DecodeError(ValueError):
    pass


def isk(x: int) -> bool:
    return bool(x & BITRK)


def indexk(x: int) -> int:
    return x & ~BITRK


@dataclass(frozen=True)
class RawInstr:
    pc: int          # 1-based
    word: int
    op: Op
    a: int
    b: int
    c: int
    bx: int
    sbx: int


def decode(word: int, pc: int) -> RawInstr:
    opnum = word & 0x3F
    if opnum > 37:
        raise DecodeError(f"pc {pc}: invalid opcode {opnum} in word 0x{word:08x}")
    bx = (word >> 14) & 0x3FFFF
    return RawInstr(
        pc=pc, word=word, op=Op(opnum),
        a=(word >> 6) & 0xFF,
        c=(word >> 14) & 0x1FF,
        b=(word >> 23) & 0x1FF,
        bx=bx, sbx=bx - MAXARG_sBx,
    )


def luac_operand_str(ri: RawInstr) -> str:
    """复刻 print.c PrintCode 的操作数列（RK 常量打成 -1-index；JMP 只打 sBx）。"""
    spec = OP_SPECS[ri.op]
    if spec.fmt is Fmt.iABC:
        parts = [str(ri.a)]
        if spec.bmode is not ArgMode.N:
            parts.append(str(-1 - indexk(ri.b) if isk(ri.b) else ri.b))
        if spec.cmode is not ArgMode.N:
            parts.append(str(-1 - indexk(ri.c) if isk(ri.c) else ri.c))
        return " ".join(parts)
    if spec.fmt is Fmt.iABx:
        bx = -1 - ri.bx if spec.bmode is ArgMode.K else ri.bx
        return f"{ri.a} {bx}"
    # iAsBx
    if ri.op is Op.JMP:
        return str(ri.sbx)
    return f"{ri.a} {ri.sbx}"
```

- [ ] **Step 3: 逐行核对 OP_SPECS 与 vendor 源码**

打开 `vendor/lua-5.1/src/lopcodes.c` 的 `luaP_opmodes` 数组，逐行核对上表 38 行的 fmt/bmode/cmode 转录无误（尤其 TEST/TESTSET/TFORLOOP/SETLIST 几行）。此步是人工核对，golden oracle 测试是机器兜底。

- [ ] **Step 4: 运行测试**

Run: `uv run pytest tests/test_opcodes.py -v`（需 `PYLUADEC_CORPUS_DIR` 已设，否则 golden oracle 用例 skip——本计划所有语料测试同此，不再重复注明）
Expected: 全 PASS，`test_decoder_matches_all_golden_listings` 核对数 > 200,000

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: lua 5.1 instruction decoder with corpus-wide golden listing oracle"
```

---

### Task 2: 效应表（公理层）

**Files:**
- Create: `src/pyluadec/lift/effects.py`
- Test: `tests/test_effects.py`

**Interfaces:**
- Consumes: Task 1 的 `Op`、`RawInstr`、`isk`、`indexk`。
- Produces（Task 3/6+ 依赖）:
  - `class Effect(IntEnum)`: `PURE=0 < READ_HEAP=1 < WRITE_HEAP=2 < ARBITRARY=3`
  - `class EffectMode(Enum)`: `STRICT, NO_METAMETHOD, TRUSTING`（spec §9 R1 三档；M2 只编码，标定在 M4）
  - `@dataclass(frozen=True) InstrEffects: reads: frozenset[int]; writes: frozenset[int]; reads_open: bool; writes_open: bool; effect: Effect; may_error: bool`
    - `reads_open=True` 表示还读 `R[base..top-1]`（base 由发射器按 opcode 推导）；`writes_open` 同理
    - `may_error`：在 NO_METAMETHOD 假设下仍可能抛错（算术强转失败、nil 索引、不可比较类型、for 非数字等）
  - `analyze(ri: RawInstr, mode: EffectMode) -> InstrEffects`
  - `successors(ri: RawInstr, nups_of_closure: int | None = None) -> tuple[int, ...]`
    - 返回后继 pc 元组；RETURN/TAILCALL 为 `()`；CLOSURE 须传该 proto 的 nups（跳过伪指令）
  - `extra_words(ri: RawInstr, nups_of_closure: int | None = None) -> int`
    - 该指令额外消耗的指令字数：CLOSURE→nups；SETLIST C==0→1；其余 0

**语义依据**（no-frills PDF + lvm.c；发射器 Task 6-8 与此表共用同一套语义结论）：

| Op | reads | writes | STRICT | NO_MM | TRUSTING | may_error | 后继 |
|---|---|---|---|---|---|---|---|
| MOVE | {B} | {A} | PURE | PURE | PURE | no | pc+1 |
| LOADK / LOADNIL(A..B) / NEWTABLE / CLOSURE | –（CLOSURE 读 MOVE 伪指令捕获的寄存器，由 lift 补） | {A}（LOADNIL: A..B） | PURE | PURE | PURE | no | pc+1（CLOSURE: pc+1+nups） |
| LOADBOOL | – | {A} | PURE | PURE | PURE | no | C≠0→pc+2 否则 pc+1 |
| GETUPVAL | – | {A} | READ_HEAP | READ_HEAP | READ_HEAP | no | pc+1 |
| SETUPVAL | {A} | – | WRITE_HEAP | WRITE_HEAP | WRITE_HEAP | no | pc+1 |
| GETGLOBAL | – | {A} | ARBITRARY | READ_HEAP | PURE | no | pc+1 |
| GETTABLE / SELF | {B}∪rk(C)（SELF 写 {A,A+1}） | {A} | ARBITRARY | READ_HEAP | PURE | yes(nil 索引) | pc+1 |
| SETGLOBAL | {A} | – | ARBITRARY | WRITE_HEAP | WRITE_HEAP | no | pc+1 |
| SETTABLE / SETLIST | rk 各操作数 / A..A+B | – | ARBITRARY | WRITE_HEAP | WRITE_HEAP | yes | pc+1（SETLIST C==0: pc+2） |
| ADD..POW / UNM / LEN / CONCAT | rk(B)∪rk(C) 等 | {A} | ARBITRARY | PURE | PURE | yes(强转) | pc+1 |
| NOT | {B} | {A} | PURE | PURE | PURE | no | pc+1 |
| JMP | – | – | PURE | PURE | PURE | no | pc+1+sBx |
| EQ | rk(B)∪rk(C) | – | ARBITRARY | PURE | PURE | no（== 永不抛） | (pc+1, pc+2) |
| LT / LE | rk(B)∪rk(C) | – | ARBITRARY | PURE | PURE | yes(不可比较) | (pc+1, pc+2) |
| TEST | {A} | – | PURE | PURE | PURE | no | (pc+1, pc+2) |
| TESTSET | {B} | {A}（条件写） | PURE | PURE | PURE | no | (pc+1, pc+2) |
| CALL | {A}∪args（B==0 → reads_open） | 结果区（C==0 → writes_open） | ARBITRARY | ARBITRARY | ARBITRARY | yes | pc+1 |
| TAILCALL | 同 CALL | – | ARBITRARY×3 | yes | () |
| RETURN | {A..A+B-2}（B==0 → reads_open） | – | PURE | PURE | PURE | no | () |
| FORPREP | {A,A+1,A+2} | {A,A+1,A+2} | PURE | PURE | PURE | yes(非数字) | pc+1+sBx |
| FORLOOP | {A,A+1,A+2} | {A,A+3} | PURE | PURE | PURE | yes | (pc+1+sBx, pc+1) |
| TFORLOOP | {A,A+1,A+2} | {A+2, A+3..A+2+C} | ARBITRARY×3 | yes(调用) | (pc+1, pc+2) |
| CLOSE | – | – | WRITE_HEAP×3（改变 upvalue 绑定） | no | pc+1 |
| VARARG | – | {A..A+B-2}（B==0 → writes_open） | PURE | PURE | PURE | no | pc+1 |

- [ ] **Step 1: 写失败测试**

`tests/test_effects.py`：

```python
def _mk(op, a=0, b=0, c=0):
    from pyluadec.lift.opcodes import decode
    word = int(op) | (a << 6) | (c << 14) | (b << 23)
    return decode(word, pc=10)


def _mk_sbx(op, a, sbx):
    from pyluadec.lift.opcodes import decode
    word = int(op) | (a << 6) | ((sbx + 131071) << 14)
    return decode(word, pc=10)


def test_all_38_opcodes_covered():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    for op in Op:
        ri = _mk(op, a=1, b=1, c=1) if op.name not in ("JMP", "FORLOOP", "FORPREP") \
            else _mk_sbx(op, 1, 0)
        for mode in EffectMode:
            fx = analyze(ri, mode)          # 任何 opcode 任何档位都必须有定义
            assert fx.effect is not None


def test_getglobal_effect_ladder():
    from pyluadec.lift.effects import analyze, Effect, EffectMode
    from pyluadec.lift.opcodes import Op
    ri = _mk(Op.GETGLOBAL, a=0, b=0)
    assert analyze(ri, EffectMode.STRICT).effect is Effect.ARBITRARY
    assert analyze(ri, EffectMode.NO_METAMETHOD).effect is Effect.READ_HEAP
    assert analyze(ri, EffectMode.TRUSTING).effect is Effect.PURE


def test_gettable_rk_reads():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    ri = _mk(Op.GETTABLE, a=3, b=1, c=256 + 4)     # C 是常量 → 不读寄存器
    fx = analyze(ri, EffectMode.STRICT)
    assert fx.reads == frozenset({1}) and fx.writes == frozenset({3})
    ri = _mk(Op.GETTABLE, a=3, b=1, c=2)            # C 是寄存器
    assert analyze(ri, EffectMode.STRICT).reads == frozenset({1, 2})


def test_call_open_flags():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.CALL, a=2, b=0, c=1), EffectMode.STRICT)
    assert fx.reads_open and not fx.writes_open and 2 in fx.reads
    fx = analyze(_mk(Op.CALL, a=2, b=1, c=0), EffectMode.STRICT)
    assert fx.writes_open and not fx.reads_open
    fx = analyze(_mk(Op.CALL, a=2, b=3, c=2), EffectMode.STRICT)
    assert fx.reads == frozenset({2, 3, 4}) and fx.writes == frozenset({2})


def test_successors():
    from pyluadec.lift.effects import successors
    from pyluadec.lift.opcodes import Op
    assert successors(_mk_sbx(Op.JMP, 0, 5)) == (16,)          # pc=10 → 10+1+5
    assert successors(_mk_sbx(Op.FORLOOP, 0, -4)) == (7, 11)
    assert successors(_mk(Op.EQ, a=1, b=1, c=2)) == (11, 12)
    assert successors(_mk(Op.LOADBOOL, a=0, b=1, c=1)) == (12,)
    assert successors(_mk(Op.LOADBOOL, a=0, b=1, c=0)) == (11,)
    assert successors(_mk(Op.RETURN, a=0, b=1)) == ()
    assert successors(_mk(Op.TAILCALL, a=0, b=1, c=0)) == ()
    assert successors(_mk(Op.CLOSURE, a=0), nups_of_closure=2) == (13,)


def test_extra_words():
    from pyluadec.lift.effects import extra_words
    from pyluadec.lift.opcodes import Op
    assert extra_words(_mk(Op.CLOSURE, a=0), nups_of_closure=3) == 3
    assert extra_words(_mk(Op.SETLIST, a=0, b=1, c=0)) == 1
    assert extra_words(_mk(Op.SETLIST, a=0, b=1, c=1)) == 0
    assert extra_words(_mk(Op.MOVE)) == 0


def test_closure_requires_nups():
    import pytest
    from pyluadec.lift.effects import successors
    from pyluadec.lift.opcodes import Op
    with pytest.raises(ValueError):
        successors(_mk(Op.CLOSURE, a=0))            # 忘传 nups 必须炸，不许静默猜 0
```

Run: `uv run pytest tests/test_effects.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/lift/effects.py`**

```python
"""Per-opcode effect table — the project's axiom layer (spec §3 layer 2).

一切上层（内联门、pass 验证、fallback 发射）共享此处结论。改动本文件 = 改动公理，
必须同步 no-frills PDF / lvm.c 依据并跑全部差分测试。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

from .opcodes import Op, RawInstr, indexk, isk


class Effect(IntEnum):
    PURE = 0
    READ_HEAP = 1
    WRITE_HEAP = 2
    ARBITRARY = 3


class EffectMode(Enum):
    STRICT = "strict"                 # 任何表访问/算术都可能触发元方法
    NO_METAMETHOD = "no_metamethod"   # 假设语料不依赖元方法的副作用
    TRUSTING = "trusting"             # 进一步假设表读取可自由重排


@dataclass(frozen=True)
class InstrEffects:
    reads: frozenset[int]
    writes: frozenset[int]
    reads_open: bool      # 额外读 R[base..top-1]（CALL B==0 / RETURN B==0 / SETLIST B==0）
    writes_open: bool     # 额外写 R[base..top-1]（CALL C==0 / VARARG B==0）
    effect: Effect
    may_error: bool       # NO_METAMETHOD 假设下仍可能抛错


def _rk(x: int) -> frozenset[int]:
    return frozenset() if isk(x) else frozenset({x})


# 每项: (reads, writes, reads_open, writes_open,
#        effect@STRICT, effect@NO_METAMETHOD, effect@TRUSTING, may_error)
def _row(ri: RawInstr):
    op, a, b, c = ri.op, ri.a, ri.b, ri.c
    F = frozenset
    P, RH, WH, ARB = Effect.PURE, Effect.READ_HEAP, Effect.WRITE_HEAP, Effect.ARBITRARY
    if op is Op.MOVE:
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op in (Op.LOADK, Op.NEWTABLE):
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.LOADBOOL:
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.LOADNIL:
        return F(), F(range(a, b + 1)), 0, 0, P, P, P, False
    if op is Op.GETUPVAL:
        return F(), F({a}), 0, 0, RH, RH, RH, False
    if op is Op.SETUPVAL:
        return F({a}), F(), 0, 0, WH, WH, WH, False
    if op is Op.GETGLOBAL:
        return F(), F({a}), 0, 0, ARB, RH, P, False
    if op is Op.GETTABLE:
        return F({b}) | _rk(c), F({a}), 0, 0, ARB, RH, P, True
    if op is Op.SELF:
        return F({b}) | _rk(c), F({a, a + 1}), 0, 0, ARB, RH, P, True
    if op is Op.SETGLOBAL:
        return F({a}), F(), 0, 0, ARB, WH, WH, False
    if op is Op.SETTABLE:
        return F({a}) | _rk(b) | _rk(c), F(), 0, 0, ARB, WH, WH, True
    if op is Op.SETLIST:
        reads = F({a}) | (F(range(a + 1, a + b + 1)) if b else F())
        return reads, F(), b == 0, 0, ARB, WH, WH, True
    if op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
        return _rk(b) | _rk(c), F({a}), 0, 0, ARB, P, P, True
    if op in (Op.UNM, Op.LEN):
        return F({b}), F({a}), 0, 0, ARB, P, P, True
    if op is Op.NOT:
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op is Op.CONCAT:
        return F(range(b, c + 1)), F({a}), 0, 0, ARB, P, P, True
    if op is Op.JMP:
        return F(), F(), 0, 0, P, P, P, False
    if op is Op.EQ:
        return _rk(b) | _rk(c), F(), 0, 0, ARB, P, P, False
    if op in (Op.LT, Op.LE):
        return _rk(b) | _rk(c), F(), 0, 0, ARB, P, P, True
    if op is Op.TEST:
        return F({a}), F(), 0, 0, P, P, P, False
    if op is Op.TESTSET:
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op in (Op.CALL, Op.TAILCALL):
        reads = F({a}) | (F(range(a + 1, a + b)) if b else F())
        if op is Op.TAILCALL:
            return reads, F(), b == 0, 0, ARB, ARB, ARB, True
        writes = F(range(a, a + c - 1)) if c else F()
        return reads, writes, b == 0, c == 0, ARB, ARB, ARB, True
    if op is Op.RETURN:
        return (F(range(a, a + b - 1)) if b else F()), F(), b == 0, 0, P, P, P, False
    if op is Op.FORPREP:
        return F({a, a + 1, a + 2}), F({a, a + 1, a + 2}), 0, 0, P, P, P, True
    if op is Op.FORLOOP:
        return F({a, a + 1, a + 2}), F({a, a + 3}), 0, 0, P, P, P, True
    if op is Op.TFORLOOP:
        return F({a, a + 1, a + 2}), F({a + 2}) | F(range(a + 3, a + 3 + c)), 0, 0, ARB, ARB, ARB, True
    if op is Op.CLOSE:
        return F(), F(), 0, 0, WH, WH, WH, False
    if op is Op.CLOSURE:
        # 捕获寄存器的 reads 由 lift 层从 MOVE 伪指令补齐（此处不可见后续指令字）
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.VARARG:
        return F(), (F(range(a, a + b - 1)) if b else F()), 0, b == 0, P, P, P, False
    raise AssertionError(f"unhandled opcode {op!r}")


_MODE_COL = {EffectMode.STRICT: 4, EffectMode.NO_METAMETHOD: 5, EffectMode.TRUSTING: 6}


def analyze(ri: RawInstr, mode: EffectMode) -> InstrEffects:
    row = _row(ri)
    return InstrEffects(
        reads=row[0], writes=row[1],
        reads_open=bool(row[2]), writes_open=bool(row[3]),
        effect=row[_MODE_COL[mode]], may_error=row[7],
    )


def successors(ri: RawInstr, nups_of_closure: int | None = None) -> tuple[int, ...]:
    op, pc = ri.op, ri.pc
    if op in (Op.RETURN, Op.TAILCALL):
        return ()
    if op is Op.JMP or op is Op.FORPREP:
        return (pc + 1 + ri.sbx,)
    if op is Op.FORLOOP:
        return (pc + 1 + ri.sbx, pc + 1)
    if op in (Op.EQ, Op.LT, Op.LE, Op.TEST, Op.TESTSET, Op.TFORLOOP):
        return (pc + 1, pc + 2)
    if op is Op.LOADBOOL:
        return (pc + 2,) if ri.c else (pc + 1,)
    if op is Op.CLOSURE:
        if nups_of_closure is None:
            raise ValueError("successors(CLOSURE) requires nups_of_closure")
        return (pc + 1 + nups_of_closure,)
    if op is Op.SETLIST and ri.c == 0:
        return (pc + 2,)
    return (pc + 1,)


def extra_words(ri: RawInstr, nups_of_closure: int | None = None) -> int:
    if ri.op is Op.CLOSURE:
        if nups_of_closure is None:
            raise ValueError("extra_words(CLOSURE) requires nups_of_closure")
        return nups_of_closure
    if ri.op is Op.SETLIST and ri.c == 0:
        return 1
    return 0
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_effects.py -v`
Expected: 全 PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: 38-opcode effect table with 3-mode ladder, successors, extra-word accounting"
```

---

### Task 3: lift 层（Proto → LIR，PC 认领审计）

**Files:**
- Create: `src/pyluadec/lift/lift.py`
- Modify: `src/pyluadec/lift/__init__.py`
- Test: `tests/test_lift.py`

**Interfaces:**
- Consumes: `ingest.Proto`；Task 1 `decode`；Task 2 `analyze/successors/extra_words`。
- Produces（Task 4/6+ 依赖）:
  - `@dataclass(frozen=True) LirInstr: ri: RawInstr; effects: InstrEffects; successors: tuple[int, ...]; consumed: tuple[int, ...]`
    - `consumed`: 该指令额外占用的 pc（CLOSURE 伪指令 / SETLIST C==0 数据字）
    - CLOSURE 的 `effects.reads` 已补上 MOVE 伪指令捕获的寄存器
  - `@dataclass(frozen=True) LirFunction: proto: Proto; instrs: dict[int, LirInstr]; n_pcs: int; captured_regs: frozenset[int]; closure_pseudo: dict[int, tuple[RawInstr, ...]]`
    - `instrs` 键为真实指令 pc（1-based）；被消耗的 pc 不在键中
    - `captured_regs`: 本函数中被任何 CLOSURE 的 MOVE 伪指令捕获的寄存器集合（发射器装箱依据）
    - `closure_pseudo`: CLOSURE pc → 其 nups 条伪指令（MOVE/GETUPVAL）的 RawInstr 元组
  - `lift_proto(p: Proto, mode: EffectMode = EffectMode.STRICT) -> LirFunction`
  - `class LiftError(Exception)`：伪指令非 MOVE/GETUPVAL、跳转目标越界、最后一条指令可 fallthrough 等结构违例

- [ ] **Step 1: 写失败测试**

`tests/test_lift.py`：

```python
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
    with pytest.raises(LiftError):
        lift_proto(replace(p, code=p.code[:-1]))             # 砍掉末条 RETURN → 可 fallthrough


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
```

Run: `uv run pytest tests/test_lift.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/lift/lift.py`**

```python
"""Proto → LIR：解码 + 效应标注 + 伪指令消耗。零聪明处理，纯结构化转录。"""
from __future__ import annotations

from dataclasses import dataclass, replace

from pyluadec.ingest.proto import Proto

from .effects import EffectMode, InstrEffects, analyze, extra_words, successors
from .opcodes import Op, RawInstr, decode


class LiftError(Exception):
    pass


@dataclass(frozen=True)
class LirInstr:
    ri: RawInstr
    effects: InstrEffects
    successors: tuple[int, ...]
    consumed: tuple[int, ...]


@dataclass(frozen=True)
class LirFunction:
    proto: Proto
    instrs: dict[int, LirInstr]
    n_pcs: int
    captured_regs: frozenset[int]
    closure_pseudo: dict[int, tuple[RawInstr, ...]]


def lift_proto(p: Proto, mode: EffectMode = EffectMode.STRICT) -> LirFunction:
    n = len(p.code)
    if n == 0:
        raise LiftError("empty code array")
    instrs: dict[int, LirInstr] = {}
    closure_pseudo: dict[int, tuple[RawInstr, ...]] = {}
    captured: set[int] = set()
    pc = 1
    while pc <= n:
        ri = decode(p.code[pc - 1], pc=pc)
        nups = None
        if ri.op is Op.CLOSURE:
            if not (0 <= ri.bx < len(p.subprotos)):
                raise LiftError(f"pc {pc}: CLOSURE Bx={ri.bx} out of range")
            nups = p.subprotos[ri.bx].nups
        n_extra = extra_words(ri, nups)
        if pc + n_extra > n:
            raise LiftError(f"pc {pc}: {ri.op.name} consumes past end of code")
        consumed = tuple(range(pc + 1, pc + 1 + n_extra))
        fx = analyze(ri, mode)
        if ri.op is Op.CLOSURE:
            pseudo = tuple(decode(p.code[q - 1], pc=q) for q in consumed)
            for ps in pseudo:
                if ps.op not in (Op.MOVE, Op.GETUPVAL):
                    raise LiftError(
                        f"pc {ps.pc}: CLOSURE pseudo-instruction is {ps.op.name}, "
                        "expected MOVE/GETUPVAL")
            closure_pseudo[pc] = pseudo
            moved = frozenset(ps.b for ps in pseudo if ps.op is Op.MOVE)
            captured.update(moved)
            fx = replace(fx, reads=fx.reads | moved)
        succ = successors(ri, nups)
        for s in succ:
            if not (1 <= s <= n):
                raise LiftError(f"pc {pc}: successor {s} out of range 1..{n}")
        instrs[pc] = LirInstr(ri=ri, effects=fx, successors=succ, consumed=consumed)
        pc += 1 + n_extra
    return LirFunction(
        proto=p, instrs=instrs, n_pcs=n,
        captured_regs=frozenset(captured), closure_pseudo=closure_pseudo)
```

（末条指令的 fallthrough 越界由循环内 `for s in succ` 的界内检查天然覆盖——截断 `return 1` 的 code 后，被截断的前一条指令的 `pc+1` 后继会越界并抛 `LiftError`，即 `test_lift_rejects_truncated_code` 的行为契约；不要再加第二处检查。）

`src/pyluadec/lift/__init__.py`：

```python
from .effects import Effect, EffectMode, InstrEffects, analyze, extra_words, successors
from .lift import LiftError, LirFunction, LirInstr, lift_proto
from .opcodes import (ArgMode, DecodeError, Fmt, LUA_KEYWORDS, Op, OpSpec, OP_SPECS,
                      RawInstr, decode, indexk, isk, luac_operand_str)

__all__ = [
    "ArgMode", "DecodeError", "Effect", "EffectMode", "Fmt", "InstrEffects",
    "LUA_KEYWORDS", "LiftError", "LirFunction", "LirInstr", "Op", "OpSpec", "OP_SPECS",
    "RawInstr", "analyze", "decode", "extra_words", "indexk", "isk",
    "lift_proto", "luac_operand_str", "successors",
]
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_lift.py -v`
Expected: 全 PASS；语料审计核对 1944 个函数

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: lift layer with pseudo-instruction accounting and corpus-wide pc-claim audit"
```

---

### Task 4: CFG（基本块）

**Files:**
- Create: `src/pyluadec/cfg/__init__.py`, `src/pyluadec/cfg/blocks.py`
- Test: `tests/test_cfg.py`

**Interfaces:**
- Consumes: Task 3 `LirFunction`。
- Produces（Task 5/6+ 依赖）:
  - `@dataclass(frozen=True) BasicBlock: start: int; instrs: tuple[LirInstr, ...]; succs: tuple[int, ...]`（succs 为后继块的 start pc）
  - `@dataclass(frozen=True) Cfg: entry: int; blocks: dict[int, BasicBlock]; preds: dict[int, tuple[int, ...]]`
  - `build_cfg(fn: LirFunction) -> Cfg`
  - 块划分规则：leader = pc 1、任何指令的非顺序后继目标、任何多后继指令的两个后继；块在控制转移指令或下一 leader 前结束

- [ ] **Step 1: 写失败测试**

`tests/test_cfg.py`：

```python
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
    assert len(cfg.blocks) == 1 and cfg.entry == 1
    assert cfg.blocks[1].succs == ()


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
```

Run: `uv run pytest tests/test_cfg.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/cfg/blocks.py`**

```python
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
```

`src/pyluadec/cfg/__init__.py`：

```python
from .blocks import BasicBlock, Cfg, build_cfg

__all__ = ["BasicBlock", "Cfg", "build_cfg"]
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_cfg.py -v`
Expected: 全 PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: basic-block CFG from LIR with corpus invariants"
```

---

### Task 5: 支配树

**Files:**
- Create: `src/pyluadec/cfg/dom.py`
- Modify: `src/pyluadec/cfg/__init__.py`
- Test: `tests/test_dom.py`

**Interfaces:**
- Consumes: Task 4 `Cfg`。
- Produces（M3 区域识别的地基；M2 内仅测试消费）:
  - `immediate_dominators(cfg: Cfg) -> dict[int, int]`（块 start → idom 的 start；entry 映射到自身）
  - `dom_tree(idoms: dict[int, int]) -> dict[int, tuple[int, ...]]`（父 → 子块列表）
  - `dominates(idoms, a: int, b: int) -> bool`
  - 算法：Cooper–Harvey–Kennedy 迭代（逆后序），对不可归约图同样正确
  - 不可达块：返回的 idoms 仅含从 entry 可达的块；调用方以 `set(idoms)` 为可达集合

- [ ] **Step 1: 写失败测试**

`tests/test_dom.py`：

```python
def _mk_cfg(edges: dict[int, tuple[int, ...]], entry: int = 1):
    """从邻接表手工构造 Cfg（instrs 为空元组，dom 计算只看图结构）。"""
    from pyluadec.cfg.blocks import BasicBlock, Cfg
    blocks = {s: BasicBlock(s, (), t) for s, t in edges.items()}
    preds = {s: [] for s in edges}
    for s, ts in edges.items():
        for t in ts:
            preds[t].append(s)
    return Cfg(entry=entry, blocks=blocks,
               preds={k: tuple(sorted(v)) for k, v in preds.items()})


def test_diamond():
    from pyluadec.cfg.dom import dominates, immediate_dominators
    #    1 → 2,3 ; 2 → 4 ; 3 → 4
    idoms = immediate_dominators(_mk_cfg({1: (2, 3), 2: (4,), 3: (4,), 4: ()}))
    assert idoms == {1: 1, 2: 1, 3: 1, 4: 1}
    assert dominates(idoms, 1, 4) and not dominates(idoms, 2, 4)


def test_loop():
    from pyluadec.cfg.dom import immediate_dominators
    # 1 → 2 ; 2 → 3,4 ; 3 → 2 ; 4 → ()
    idoms = immediate_dominators(_mk_cfg({1: (2,), 2: (3, 4), 3: (2,), 4: ()}))
    assert idoms == {1: 1, 2: 1, 3: 2, 4: 2}


def test_irreducible():
    from pyluadec.cfg.dom import immediate_dominators
    # 经典不可归约：1 → 2,3 ; 2 → 3 ; 3 → 2 （双入口循环）
    idoms = immediate_dominators(_mk_cfg({1: (2, 3), 2: (3,), 3: (2,)}))
    assert idoms == {1: 1, 2: 1, 3: 1}


def test_unreachable_block_excluded():
    from pyluadec.cfg.dom import immediate_dominators
    idoms = immediate_dominators(_mk_cfg({1: (2,), 2: (), 9: (2,)}))   # 9 不可达
    assert 9 not in idoms and set(idoms) == {1, 2}


def test_dom_tree_children():
    from pyluadec.cfg.dom import dom_tree, immediate_dominators
    idoms = immediate_dominators(_mk_cfg({1: (2, 3), 2: (4,), 3: (4,), 4: ()}))
    tree = dom_tree(idoms)
    assert tree[1] == (2, 3, 4) and tree.get(2, ()) == ()


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
```

Run: `uv run pytest tests/test_dom.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/cfg/dom.py`**

```python
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
```

`src/pyluadec/cfg/__init__.py` 追加：

```python
from .dom import dom_tree, dominates, immediate_dominators
__all__ += ["dom_tree", "dominates", "immediate_dominators"]
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_dom.py -v`
Expected: 全 PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: CHK dominator tree over CFG, irreducible-safe"
```

---

### Task 6: oracle 助手 + fallback 发射器（直线代码子集）

**Files:**
- Create: `src/pyluadec/oracle.py`, `src/pyluadec/structure/__init__.py`, `src/pyluadec/structure/fallback.py`, `tests/diffexec.py`
- Test: `tests/test_oracle.py`, `tests/test_fallback_literals.py`, `tests/test_fallback_basic.py`

**Interfaces:**
- Consumes: Phase 1 构建产物 `build/luac_sz4`、`build/lua_sz4`；Task 3 `lift_proto`；Task 4 `build_cfg`。
- Produces:
  - `pyluadec.oracle`:
    - `build_dir() -> Path`（`PYLUADEC_BUILD_DIR` 或仓库根 `build/`；缺二进制抛 `OracleError`）
    - `compile_source(source: bytes, *, strip: bool = False) -> bytes`（失败抛 `LuaCompileError(OracleError)`，携带 luac stderr）
    - `run_bytes(payload: bytes, *, is_source: bool, args: tuple[str, ...] = (), timeout: float = 30.0) -> subprocess.CompletedProcess[bytes]`
  - `pyluadec.structure.fallback`:
    - `emit_chunk(root: Proto) -> bytes`（M2 出口的核心函数；本 Task 支持直线代码子集，Task 7/8 补全，未支持 opcode 抛 `EmitError`）
    - `class EmitError(Exception)`
    - `num_lit(k: LuaNumber) -> str`、`str_lit(bs: bytes) -> str`、`const_lit(c) -> str`（payload 精确/字节精确的字面量渲染）
  - `tests/diffexec.py`: `assert_fallback_roundtrip(lua_source: str, args: tuple[str, ...] = ()) -> bytes`（差分执行断言，返回反编译产物便于附加断言）

**发射模型**（Task 6-8 共用，语义依据 lvm.c；本 Task 先落直线部分）：

- 寄存器住 table `__pld_R`（语料单函数最多 61 slot，但 table 统一处理 open 区间且无 200 局部变量上限）；被 CLOSURE 捕获的寄存器（`LirFunction.captured_regs`）装箱为 `{v=...}`，读写经 `.v`（Task 8 落地，本 Task 的 rd/wr 已按此约定写）。
- 每个基本块一个状态：`while true do if __pld_pc == <start> then ... elseif ... end end`。块内非终结指令逐条发射；块尾按终结指令性质发射 pc 赋值/return。
- EQ/LT/LE/TEST/TESTSET 的「跳过下一条 JMP」语义直译为 `__pld_pc = pc+1 / pc+2` 二选一（pc+1 状态就是那条 JMP，多一次派发、零语义差）。
- 一切辅助名 `__pld_` 前缀；全局变量按标识符直接发射（发射前 assert 合法性）。
- 数字字面量渲染候选 `%d` → `%.14g` → `%.17g`，取第一个 struct payload 逐位一致者；nan/inf 渲染 `(0/0)`/`(1/0)`/`(-1/0)`；负数字面量加括号。字符串逐字节渲染，非可打印字节一律 `\%03d` 三位十进制转义（定长避免与后继数字字符粘连）。

- [ ] **Step 1: 写 oracle 失败测试**

`tests/test_oracle.py`：

```python
import pytest


def test_compile_and_run_roundtrip():
    from pyluadec import oracle
    bc = oracle.compile_source(b'print("hello from oracle")')
    assert bc[:4] == b"\x1bLua"
    r = oracle.run_bytes(bc, is_source=False)
    assert r.returncode == 0 and r.stdout == b"hello from oracle\n"


def test_run_source_directly():
    from pyluadec import oracle
    r = oracle.run_bytes(b"print(1 + 1)", is_source=True)
    assert r.stdout == b"2\n"


def test_compile_error_carries_stderr():
    from pyluadec import oracle
    with pytest.raises(oracle.LuaCompileError, match="near"):
        oracle.compile_source(b"local local local")


def test_strip_flag():
    from pyluadec import oracle
    plain = oracle.compile_source(b"return 1")
    stripped = oracle.compile_source(b"return 1", strip=True)
    assert len(stripped) < len(plain)
```

Run: `uv run pytest tests/test_oracle.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/oracle.py`**

```python
"""仓库内 lua/luac oracle 的定位与调用（Phase 1 构建产物）。"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


class OracleError(RuntimeError):
    pass


class LuaCompileError(OracleError):
    pass


def build_dir() -> Path:
    env = os.environ.get("PYLUADEC_BUILD_DIR")
    p = Path(env) if env else Path(__file__).resolve().parents[2] / "build"
    if not (p / "luac_sz4").exists():
        raise OracleError(
            f"oracle binaries not found in {p}; run ./scripts/build_native.sh "
            "(or set PYLUADEC_BUILD_DIR)")
    return p


def luac_sz4() -> Path:
    return build_dir() / "luac_sz4"


def lua_sz4() -> Path:
    return build_dir() / "lua_sz4"


def compile_source(source: bytes, *, strip: bool = False) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        s = Path(td) / "in.lua"
        o = Path(td) / "out.luac"
        s.write_bytes(source)
        cmd = [str(luac_sz4())] + (["-s"] if strip else []) + ["-o", str(o), str(s)]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0:
            raise LuaCompileError(r.stderr.decode(errors="replace"))
        return o.read_bytes()


def run_bytes(payload: bytes, *, is_source: bool, args: tuple[str, ...] = (),
              timeout: float = 30.0) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        return subprocess.run([str(lua_sz4()), str(f), *args],
                              capture_output=True, timeout=timeout)
```

Run: `uv run pytest tests/test_oracle.py -v` → 全 PASS

- [ ] **Step 3: 写字面量渲染失败测试**

`tests/test_fallback_literals.py`：

```python
import struct


def _num(v: float):
    from pyluadec.ingest.proto import LuaNumber
    return LuaNumber(value=v, payload=struct.pack("<d", v))


def test_num_lit_integral_and_fractional():
    from pyluadec.structure.fallback import num_lit
    assert num_lit(_num(42.0)) == "42"
    assert num_lit(_num(42.5)) == "42.5"
    assert num_lit(_num(-3.0)) == "(-3)"


def test_num_lit_payload_exact_roundtrip():
    from pyluadec.structure.fallback import num_lit
    for v in (0.1, 1e300, 16.000000000000004, -0.0, 123456789012345.6):
        s = num_lit(_num(v))
        rendered = s.strip("()")
        assert struct.pack("<d", float(rendered)) == struct.pack("<d", v)


def test_num_lit_nonfinite():
    from pyluadec.structure.fallback import num_lit
    assert num_lit(_num(float("inf"))) == "(1/0)"
    assert num_lit(_num(float("-inf"))) == "(-1/0)"
    assert num_lit(_num(float("nan"))) == "(0/0)"


def test_str_lit_escaping():
    from pyluadec.structure.fallback import str_lit
    assert str_lit(b"abc") == '"abc"'
    assert str_lit(b'a"b\\c') == '"a\\"b\\\\c"'
    assert str_lit(b"\x01" + b"23") == '"\\00123"'     # 定长转义防数字粘连
    assert str_lit(b"\xff\x00\n") == '"\\255\\000\\010"'


def test_str_lit_compiles_back_to_same_bytes():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import str_lit
    payload = bytes(range(256))
    bc = oracle.compile_source(f"return {str_lit(payload)}".encode())
    consts = load_bytes(bc).constants
    assert payload in consts                            # 字节精确穿越 lexer
```

Run: `uv run pytest tests/test_fallback_literals.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 4: 实现 `src/pyluadec/structure/fallback.py`（字面量 + 骨架 + 直线 opcode）**

`src/pyluadec/structure/__init__.py` 为空文件。fallback.py：

```python
"""Fallback 状态机发射器（spec §3 ③ 的保底路径）。

任何函数都发射为语义精确的 pc 派发循环。丑是特性：正确性来自逐 opcode 对照
lvm.c 的模板；可读性属于 M3+ 的结构化/美化层。语义模板与 lift/effects.py
共享同一套结论（no-frills PDF §per-opcode + lvm.c）。
"""
from __future__ import annotations

import re
import struct

from pyluadec.cfg import build_cfg
from pyluadec.ingest.proto import LuaNumber, Proto

from pyluadec.lift import LUA_KEYWORDS, LirInstr, Op, indexk, isk, lift_proto


class EmitError(Exception):
    pass


_IDENT_RE = re.compile(rb"[A-Za-z_][A-Za-z0-9_]*$")

PRELUDE = """\
local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_F = {}
"""


def num_lit(k: LuaNumber) -> str:
    v = struct.unpack("<d", k.payload)[0]
    if v != v:
        return "(0/0)"
    if v == float("inf"):
        return "(1/0)"
    if v == float("-inf"):
        return "(-1/0)"
    candidates = []
    if v == int(v) and abs(v) < 1e16:
        candidates.append("%d" % int(v))
    candidates += ["%.14g" % v, "%.17g" % v]
    for s in candidates:
        if struct.pack("<d", float(s)) == k.payload:
            return f"({s})" if s.startswith("-") else s
    raise EmitError(f"cannot render number payload {k.payload.hex()} losslessly")


def str_lit(bs: bytes) -> str:
    out = ['"']
    for byte in bs:
        if byte == 0x22:                  # '"'
            out.append('\\"')
        elif byte == 0x5C:                # '\\'
            out.append("\\\\")
        elif 32 <= byte <= 126:
            out.append(chr(byte))
        else:
            out.append("\\%03d" % byte)   # 定长三位，避免与后继数字字符粘连
    out.append('"')
    return "".join(out)


def const_lit(c) -> str:
    if c is None:
        return "nil"
    if c is True:
        return "true"
    if c is False:
        return "false"
    if isinstance(c, LuaNumber):
        return num_lit(c)
    if isinstance(c, bytes):
        return str_lit(c)
    raise EmitError(f"unexpected constant {c!r}")


_ARITH = {Op.ADD: "+", Op.SUB: "-", Op.MUL: "*", Op.DIV: "/", Op.MOD: "%", Op.POW: "^"}


class _FnEmitter:
    def __init__(self, path: str, proto: Proto):
        self.path = path
        self.proto = proto
        self.fn = lift_proto(proto)
        self.cfg = build_cfg(self.fn)
        self.boxed = self.fn.captured_regs
        self.lines: list[str] = []

    # ---- 访问助手 -------------------------------------------------------
    def rd(self, i: int) -> str:
        return f"__pld_R[{i}].v" if i in self.boxed else f"__pld_R[{i}]"

    def wr(self, i: int, expr: str) -> str:
        return f"{self.rd(i)} = {expr}"

    def rk(self, x: int) -> str:
        if isk(x):
            return const_lit(self.proto.constants[indexk(x)])
        return self.rd(x)

    def global_name(self, bx: int) -> str:
        k = self.proto.constants[bx]
        if (not isinstance(k, bytes) or not _IDENT_RE.fullmatch(k)
                or k.decode("ascii") in LUA_KEYWORDS or k.startswith(b"__pld_")):
            raise EmitError(f"global name {k!r} not emittable as identifier")
        return k.decode("ascii")

    # ---- 函数级发射 -----------------------------------------------------
    def emit(self) -> str:
        p = self.proto
        params = [f"__pld_p{i}" for i in range(p.numparams)]
        if p.is_vararg & 2:
            params.append("...")
        L = self.lines
        L.append(f'__pld_F["{self.path}"] = function(__pld_U)')
        L.append(f'return function({", ".join(params)})')
        boxed_init = ", ".join(f"[{i}]=true" for i in sorted(self.boxed))
        L.append(f"local __pld_R, __pld_B, __pld_top = {{}}, {{{boxed_init}}}, 0")
        for i in range(p.numparams):
            L.append(f"__pld_R[{i}] = {{v = __pld_p{i}}}" if i in self.boxed
                     else f"__pld_R[{i}] = __pld_p{i}")
        for i in sorted(self.boxed):
            if i >= p.numparams:
                L.append(f"__pld_R[{i}] = {{}}")
        L.append("local __pld_pc = 1")
        L.append("while true do")
        kw = "if"
        for start in sorted(self.cfg.blocks):
            L.append(f"{kw} __pld_pc == {start} then")
            kw = "elseif"
            self._emit_block(self.cfg.blocks[start])
        L.append('else __pld_error("pyluadec fallback: invalid pc") end')
        L.append("end")     # while
        L.append("end")     # inner function
        L.append("end")     # factory
        return "\n".join(L) + "\n"

    def _emit_block(self, blk) -> None:
        for li in blk.instrs[:-1]:
            self._emit_simple(li)
        last = blk.instrs[-1]
        if not self._emit_terminator(last):
            self._emit_simple(last)
            self.lines.append(f"__pld_pc = {blk.succs[0]}")

    # ---- 直线指令（本 Task 的子集；Task 7/8 扩展本方法与 _emit_terminator）
    def _emit_simple(self, li: LirInstr) -> None:
        ri = li.ri
        op, a, b, c, bx = ri.op, ri.a, ri.b, ri.c, ri.bx
        L, rd, wr, rk = self.lines, self.rd, self.wr, self.rk
        if op is Op.MOVE:
            L.append(wr(a, rd(b)))
        elif op is Op.LOADK:
            L.append(wr(a, const_lit(self.proto.constants[bx])))
        elif op is Op.LOADBOOL:
            L.append(wr(a, "true" if b else "false"))   # C≠0 时块尾由 terminator 跳 pc+2
        elif op is Op.LOADNIL:
            for i in range(a, b + 1):
                L.append(wr(i, "nil"))
        elif op is Op.GETGLOBAL:
            L.append(wr(a, self.global_name(bx)))
        elif op is Op.SETGLOBAL:
            L.append(f"{self.global_name(bx)} = {rd(a)}")
        elif op is Op.GETTABLE:
            L.append(wr(a, f"{rd(b)}[{rk(c)}]"))
        elif op is Op.SETTABLE:
            L.append(f"{rd(a)}[{rk(b)}] = {rk(c)}")
        elif op is Op.NEWTABLE:
            L.append(wr(a, "{}"))
        elif op is Op.SELF:
            # R(A+1) := R(B); R(A) := R(B)[RK(C)] —— 用临时变量抵御 A+1 == B 重叠
            L.append(f"do local __pld_t = {rd(b)} "
                     f"{wr(a + 1, '__pld_t')} {wr(a, f'__pld_t[{rk(c)}]')} end")
        elif op in _ARITH:
            L.append(wr(a, f"{rk(b)} {_ARITH[op]} {rk(c)}"))
        elif op is Op.UNM:
            L.append(wr(a, f"-({rd(b)})"))
        elif op is Op.NOT:
            L.append(wr(a, f"not ({rd(b)})"))
        elif op is Op.LEN:
            L.append(wr(a, f"#({rd(b)})"))
        elif op is Op.CONCAT:
            L.append(wr(a, " .. ".join(rd(i) for i in range(b, c + 1))))
        elif op is Op.CALL:
            self._emit_call(ri)
        else:
            raise EmitError(f"pc {ri.pc}: opcode {op.name} not yet supported by fallback")

    def _call_expr(self, ri) -> tuple[str, list[str]]:
        """返回 (调用表达式, 前置语句)。B==0（open args）在 Task 7 落地。"""
        a, b = ri.a, ri.b
        if b >= 1:
            args = ", ".join(self.rd(a + 1 + i) for i in range(b - 1))
            return f"{self.rd(a)}({args})", []
        raise EmitError(f"pc {ri.pc}: open-arg CALL not yet supported")

    def _emit_call(self, ri) -> None:
        a, c = ri.a, ri.c
        expr, pre = self._call_expr(ri)
        L = self.lines
        if c == 1 and not pre:
            L.append(expr)
        elif c >= 2 and not pre:
            targets = ", ".join(self.rd(a + i) for i in range(c - 1))
            L.append(f"{targets} = {expr}")
        elif c >= 1:
            body = [expr] if c == 1 else \
                [", ".join(self.rd(a + i) for i in range(c - 1)) + f" = {expr}"]
            L.append("do " + " ".join(pre + body) + " end")
        else:
            raise EmitError(f"pc {ri.pc}: open-result CALL not yet supported")

    # ---- 终结指令（本 Task 仅 RETURN 定长 + LOADBOOL 跳变体）
    def _emit_terminator(self, li: LirInstr) -> bool:
        ri = li.ri
        op, a, b = ri.op, ri.a, ri.b
        L, rd = self.lines, self.rd
        if op is Op.RETURN:
            if b == 1:
                L.append("return")
            elif b >= 2:
                L.append("return " + ", ".join(rd(a + i) for i in range(b - 1)))
            else:
                raise EmitError(f"pc {ri.pc}: open RETURN not yet supported")
            return True
        if op is Op.LOADBOOL and ri.c:
            L.append(self.wr(a, "true" if b else "false"))
            L.append(f"__pld_pc = {ri.pc + 2}")
            return True
        return False


def emit_chunk(root: Proto) -> bytes:
    parts: list[str] = [PRELUDE]

    def walk(path: str, p: Proto) -> None:
        for i, s in enumerate(p.subprotos):
            walk(f"{path}_{i}", s)
        parts.append(_FnEmitter(path, p).emit())

    walk("main", root)
    parts.append('return __pld_F["main"]({})(...)\n')
    return "".join(parts).encode()
```

- [ ] **Step 5: 写差分执行 harness 与直线用例**

`tests/diffexec.py`：

```python
"""差分执行 harness：源码 → luac_sz4 →（原字节码执行）vs（fallback 反编译再执行）。"""
from pyluadec import oracle
from pyluadec.ingest import load_bytes
from pyluadec.structure.fallback import emit_chunk


def assert_fallback_roundtrip(lua_source: str, args: tuple[str, ...] = ()) -> bytes:
    bc = oracle.compile_source(lua_source.encode())
    dec = emit_chunk(load_bytes(bc))
    r1 = oracle.run_bytes(bc, is_source=False, args=args)
    r2 = oracle.run_bytes(dec, is_source=True, args=args)
    assert r1.returncode == r2.returncode, (
        f"exit {r1.returncode} != {r2.returncode}\n"
        f"--- orig stderr ---\n{r1.stderr!r}\n--- dec stderr ---\n{r2.stderr!r}\n"
        f"--- decompiled ---\n{dec.decode()}")
    assert r1.stdout == r2.stdout, (
        f"--- orig ---\n{r1.stdout!r}\n--- dec ---\n{r2.stdout!r}\n"
        f"--- decompiled ---\n{dec.decode()}")
    return dec
```

`tests/test_fallback_basic.py`：

```python
STRAIGHT_LINE_CASES = [
    # 操作数放局部变量：常量间算术会被 luac 编译期折叠，发不出 ADD/MUL/POW/... opcode
    'local a = 2 local b = 3.5 print(a + b, a * b, a ^ b, a % b, a / b, a - b)',
    'local a = "x" print(a .. "y" .. 1 .. 2)',
    'local t = {} t.k = 3 t[1] = "v" print(t.k, t[1], #t)',
    'local s = "abc" local k = 3 print(#s, not s, -k)',      # LEN/NOT/UNM 须走寄存器
    'x_global = 42 print(x_global + 1)',
    'local a, b, c = 1 print(a, b, c)',
    'local s = "na" print(s:rep(4))',
    'local f = print f("via register call")',
    'print(true, false, nil)',
    'local t = {} t["\\001k"] = "bin" print(t["\\001k"])',
    'print("ab\\255\\001cd")',
]


def test_straightline_cases():
    from tests.diffexec import assert_fallback_roundtrip
    for src in STRAIGHT_LINE_CASES:
        assert_fallback_roundtrip(src)


def test_stripped_input_also_works():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import emit_chunk
    bc = oracle.compile_source(b'print("stripped")', strip=True)   # 语料同款 -s
    r = oracle.run_bytes(emit_chunk(load_bytes(bc)), is_source=True)
    assert r.stdout == b"stripped\n"


def test_emitted_source_compiles():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import emit_chunk
    bc = oracle.compile_source(b"local x = 1 + 2 return x")
    oracle.compile_source(emit_chunk(load_bytes(bc)))              # 不抛即过
```

（`tests/` 无 `__init__.py` 时 `from tests.diffexec import ...` 依赖仓库根 `conftest.py` 的 rootdir 注入——Phase 1 已就位，直接可用。）

- [ ] **Step 6: 运行测试**

Run: `uv run pytest tests/test_fallback_literals.py tests/test_fallback_basic.py -v`
Expected: 全 PASS（`s:rep(4)` 用例覆盖语料缺失的 SELF）

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat: oracle helpers and fallback emitter for straight-line opcodes with differential tests"
```

---

### Task 7: fallback 发射器——控制流、调用全形态、SETLIST

**Files:**
- Modify: `src/pyluadec/structure/fallback.py`
- Test: `tests/test_fallback_control.py`

**Interfaces:**
- Consumes/Produces: 同 Task 6（`emit_chunk` 扩展覆盖 JMP/EQ/LT/LE/TEST/TESTSET/FORPREP/FORLOOP/TFORLOOP/CALL(open)/TAILCALL/RETURN(open)/VARARG/SETLIST；此后仅剩 CLOSURE/GETUPVAL/SETUPVAL/CLOSE 未支持）。

**语义模板**（lvm.c 逐条对照；`p` 代指当前指令 pc）：

- JMP sBx → `__pld_pc = p+1+sBx`
- EQ/LT/LE A B C：`(RK(B) <op> RK(C)) == (A≠0)` 为真 → pc+1（落入后随 JMP 状态），否则 pc+2。源码级 `==`/`<`/`<=` 与 VM 的 equalobj/lessthan/lessequal 语义逐一对应（含元方法与不可比较报错）。
- TEST A C：真值匹配 C → pc+1 否则 pc+2。TESTSET A B C：匹配时先 `R(A) := R(B)` 再 pc+1。
- FORPREP A sBx：三个控制槽 tonumber 强转（失败报 VM 同文案错误），`R(A) -= R(A+2)`，跳 p+1+sBx。
- FORLOOP A sBx：`i = R(A)+R(A+2)`；步长正则 `i <= R(A+1)`、否则 `i >= R(A+1)` 决定回跳（写 R(A) 与 R(A+3)）或 fallthrough。nan 步长两分支皆假 → fallthrough，与 VM 一致。
- TFORLOOP A C：`R(A+3..A+2+C) = R(A)(R(A+1), R(A+2))`；`R(A+3) ~= nil` → `R(A+2) := R(A+3)` 且 pc+1，否则 pc+2。
- CALL B==0：实参 `R(A+1..top-1)` 收集进临时表后 `unpack(t, 1, n)`（显式区间，nil 洞安全）；C==0：结果经 `__pld_pack` 落回 `R(A..)` 并置 `__pld_top`。
- TAILCALL：`return <调用表达式>`（源码尾调用，栈语义等价）。
- RETURN B==0：返回 `R(A..top-1)`（同上 unpack 显式区间）。
- VARARG B==0：`__pld_pack(...)` 落回 + 置 top；B>=2 直接多重赋值 `= ...`；B==1 零目标为 no-op。
- SETLIST：`R(A)[(C-1)*50 + i] = R(A+i)`，i=1..B；B==0 用 top；C==0 取被消耗的下一指令字为真实 C（`LirInstr.consumed[0]`）。

- [ ] **Step 1: 写失败测试**

`tests/test_fallback_control.py`：

```python
CONTROL_CASES = [
    'local i = 0 while i < 5 do i = i + 1 end print(i)',
    'for i = 1, 5 do print(i) end',
    'for i = 10, 1, -2 do print(i) end',
    'for i = 1.5, 3.7, 0.5 do print(i) end',
    'for i = 1, 0 do print("never") end print("after")',
    'local t = {10, 20, 30} for i, v in ipairs(t) do print(i, v) end',
    'local x = 5 if x > 3 then print("big") elseif x > 1 then print("mid") '
    'else print("small") end',
    'local a = false or 3 local b = a and "yes" print(a, b)',
    # TEST（真值测试且不赋值）——注意 and/or 赋值形态只产 TESTSET，必须用 `if <local> then`
    'local a = tonumber("1") if a then print("truthy") end',
    'local a = tonumber("1") local b = tonumber("2") if a and b then print("and") end',
    'local t = {} while t do t = nil end print("done")',
    'print(1 == 1, 1 ~= 2, 2 < 3, 3 <= 3, "a" < "b", "a" == "a")',
    'local x = nil if x == nil then print("is nil") end',
    'repeat local x = 1 until x == 1 print("done")',
    'for i = 1, 3 do if i == 2 then break end print(i) end',
    'local s = 0 for i = 1, 100 do s = s + i end print(s)',
    'local function f(...) return ... end print(f(1, nil, 3))',
    'local function g() return 1, 2, 3 end print(g())',
    'local function g() return 1, 2 end local t = {g()} print(#t, t[1], t[2])',
    'local function g() return 1, 2 end print("x", g())',
    'print(select("#", (function(...) return ... end)(1, nil, nil)))',
    'local function tail(n) if n == 0 then return "done" end return tail(n - 1) end '
    'print(tail(10))',
    'local t = {%s} print(#t, t[1], t[51], t[60])' % ", ".join(
        str(i) for i in range(1, 61)),                     # SETLIST 两轮 flush（>50）
    'local t = {(function() return 7, 8, 9 end)()} print(#t, t[3])',   # SETLIST B==0
    'print((" "):rep(0) == "")',
    'while true do break end print("out")',
]


def test_control_flow_cases():
    from tests.diffexec import assert_fallback_roundtrip
    for src in CONTROL_CASES:
        assert_fallback_roundtrip(src)


def test_chunk_level_vararg():
    from tests.diffexec import assert_fallback_roundtrip
    assert_fallback_roundtrip("print(...)", args=("a1", "a2"))
    assert_fallback_roundtrip('local n = select("#", ...) print(n)', args=("x",))


def test_runtime_error_parity():
    """运行期报错：两边 exit code 一致（错误文案含 chunk 名，不比对 stderr 全文）。"""
    from tests.diffexec import assert_fallback_roundtrip
    assert_fallback_roundtrip('local ok = pcall(function() return {} + 1 end) print(ok)')
    assert_fallback_roundtrip(
        'local ok, e = pcall(function() local t = nil return t.k end) print(ok)')
    assert_fallback_roundtrip(
        'local ok = pcall(function() for i = 1, "x" do end end) print(ok)')
```

Run: `uv run pytest tests/test_fallback_control.py -v`
Expected: FAIL（`EmitError: ... not yet supported`）

- [ ] **Step 2: 实现——扩展 `_emit_simple` / `_emit_terminator` / `_call_expr`**

`_call_expr` 的 open-arg 分支替换为：

```python
    def _call_expr(self, ri) -> tuple[str, list[str]]:
        a, b = ri.a, ri.b
        if b >= 1:
            args = ", ".join(self.rd(a + 1 + i) for i in range(b - 1))
            return f"{self.rd(a)}({args})", []
        pre = [f"local __pld_t, __pld_n = {{}}, __pld_top - {a + 1}",
               f"for __pld_i = 1, __pld_n do "
               f"__pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, {a + 1} + __pld_i - 1) end"]
        return f"{self.rd(a)}(__pld_unpack(__pld_t, 1, __pld_n))", pre
```

`_emit_call` 的 open-result（c==0）分支替换为：

```python
        else:   # c == 0: open results
            L.append("do " + " ".join(pre))
            L.append(f"local __pld_rs = __pld_pack({expr})")
            L.append(f"for __pld_i = 1, __pld_rs.n do "
                     f"__pld_set(__pld_R, __pld_B, {a} + __pld_i - 1, __pld_rs[__pld_i]) end")
            L.append(f"__pld_top = {a} + __pld_rs.n end")
```

（c==0 且 pre 为空时 `"do " + " ".join([])` 产出 `do `，后随语句合法；保持简单。）

`_emit_simple` 追加分支：

```python
        elif op is Op.VARARG:
            if not (self.proto.is_vararg & 2):
                raise EmitError(f"pc {ri.pc}: VARARG in non-vararg function")
            if b == 1:
                pass                                    # 零目标 no-op
            elif b >= 2:
                targets = ", ".join(rd(a + i) for i in range(b - 1))
                L.append(f"{targets} = ...")
            else:
                L.append("do local __pld_rs = __pld_pack(...)")
                L.append(f"for __pld_i = 1, __pld_rs.n do "
                         f"__pld_set(__pld_R, __pld_B, {a} + __pld_i - 1, __pld_rs[__pld_i]) end")
                L.append(f"__pld_top = {a} + __pld_rs.n end")
        elif op is Op.SETLIST:
            eff_c = c if c != 0 else self.proto.code[li.consumed[0] - 1]
            base = (eff_c - 1) * 50                     # LFIELDS_PER_FLUSH
            if b >= 1:
                for i in range(1, b + 1):
                    L.append(f"{rd(a)}[{base + i}] = {rd(a + i)}")
            else:
                L.append(f"do local __pld_n = __pld_top - {a} - 1")
                L.append(f"for __pld_i = 1, __pld_n do {rd(a)}[{base} + __pld_i] = "
                         f"__pld_get(__pld_R, __pld_B, {a} + __pld_i) end end")
```

（注意 `_emit_simple` 签名把 `li` 传给 SETLIST 分支使用：将方法签名内已有的 `li` 直接用于 `li.consumed`。）

`_emit_terminator` 追加分支（放在 `return False` 之前）：

```python
        c = ri.c
        rk, wr = self.rk, self.wr
        if op is Op.JMP:
            L.append(f"__pld_pc = {ri.pc + 1 + ri.sbx}")
            return True
        if op in (Op.EQ, Op.LT, Op.LE):
            cmp = {Op.EQ: "==", Op.LT: "<", Op.LE: "<="}[op]
            cond = f"{rk(b)} {cmp} {rk(c)}"
            if a == 0:
                cond = f"not ({cond})"
            L.append(f"if {cond} then __pld_pc = {ri.pc + 1} "
                     f"else __pld_pc = {ri.pc + 2} end")
            return True
        if op is Op.TEST:
            t, f = (ri.pc + 1, ri.pc + 2) if c else (ri.pc + 2, ri.pc + 1)
            L.append(f"if {rd(a)} then __pld_pc = {t} else __pld_pc = {f} end")
            return True
        if op is Op.TESTSET:
            take = f"{wr(a, '__pld_t')} __pld_pc = {ri.pc + 1}"
            skip = f"__pld_pc = {ri.pc + 2}"
            branch = f"if __pld_t then {take} else {skip} end" if c else \
                     f"if __pld_t then {skip} else {take} end"
            L.append(f"do local __pld_t = {rd(b)} {branch} end")
            return True
        if op is Op.FORPREP:
            L.append("do")
            L.append(f"local __pld_i = __pld_tonumber({rd(a)}) "
                     f"if __pld_i == nil then __pld_error(\"'for' initial value must be a number\") end")
            L.append(f"local __pld_l = __pld_tonumber({rd(a + 1)}) "
                     f"if __pld_l == nil then __pld_error(\"'for' limit must be a number\") end")
            L.append(f"local __pld_s = __pld_tonumber({rd(a + 2)}) "
                     f"if __pld_s == nil then __pld_error(\"'for' step must be a number\") end")
            L.append(f"{wr(a, '__pld_i - __pld_s')} {wr(a + 1, '__pld_l')} {wr(a + 2, '__pld_s')}")
            L.append("end")
            L.append(f"__pld_pc = {ri.pc + 1 + ri.sbx}")
            return True
        if op is Op.FORLOOP:
            L.append(f"do local __pld_s = {rd(a + 2)} local __pld_i = {rd(a)} + __pld_s")
            L.append(f"if (__pld_s > 0 and __pld_i <= {rd(a + 1)}) or "
                     f"(__pld_s <= 0 and __pld_i >= {rd(a + 1)}) then")
            L.append(f"{wr(a, '__pld_i')} {wr(a + 3, '__pld_i')} "
                     f"__pld_pc = {ri.pc + 1 + ri.sbx}")
            L.append(f"else __pld_pc = {ri.pc + 1} end end")
            return True
        if op is Op.TFORLOOP:
            targets = ", ".join(rd(a + 3 + i) for i in range(c))
            L.append(f"{targets} = {rd(a)}({rd(a + 1)}, {rd(a + 2)})")
            L.append(f"if {rd(a + 3)} ~= nil then {wr(a + 2, rd(a + 3))} "
                     f"__pld_pc = {ri.pc + 1} else __pld_pc = {ri.pc + 2} end")
            return True
        if op is Op.TAILCALL:
            expr, pre = self._call_expr(ri)
            if pre:
                L.append("do " + " ".join(pre))
                L.append(f"return {expr} end")
            else:
                L.append(f"return {expr}")
            return True
        if op is Op.RETURN:            # 替换 Task 6 的 RETURN 分支，补齐 open 情形
            if b == 1:
                L.append("return")
            elif b >= 2:
                L.append("return " + ", ".join(rd(a + i) for i in range(b - 1)))
            else:
                L.append(f"do local __pld_t, __pld_n = {{}}, __pld_top - {a}")
                L.append(f"for __pld_i = 1, __pld_n do "
                         f"__pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, {a} + __pld_i - 1) end")
                L.append("return __pld_unpack(__pld_t, 1, __pld_n) end")
            return True
```

（FORLOOP 的 nan 步长：`__pld_s > 0` 与 `__pld_s <= 0` 对 nan 双双为假 → 走 else fallthrough，与 VM 双 luai_numle 皆假的行为一致。）

- [ ] **Step 3: 运行全部 fallback 测试**

Run: `uv run pytest tests/test_fallback_basic.py tests/test_fallback_control.py -v`
Expected: 全 PASS（Task 6 用例不回归）

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: fallback emitter control flow, full call forms, varargs, SETLIST"
```

---

### Task 8: fallback 发射器——闭包/upvalue/CLOSE 与整文件发射

**Files:**
- Modify: `src/pyluadec/structure/fallback.py`
- Test: `tests/test_fallback_closures.py`

**Interfaces:**
- Consumes/Produces: 同 Task 6/7；此 Task 后 `emit_chunk` 覆盖全部 38 opcode，任何 `Proto` 树可发射。

**闭包语义模型**（本 Task 的核心设计，逐条对照 lvm.c OP_CLOSURE/OP_CLOSE 与 lfunc.c）：

- 被捕获寄存器装箱：`captured_regs` 中的寄存器持有 `{v=...}` 盒而非裸值（Task 6 的 rd/wr 已按此发射，本 Task 起真正出现非空 `captured_regs`）。
- CLOSURE A Bx：子工厂调用 `__pld_F["<child>"]({[0]=盒0, [1]=盒1, ...})`；伪指令 MOVE 0 B → 传本函数 `__pld_R[B]`（盒对象本身，读写共享=VM 的开放 upvalue 别名）；GETUPVAL 0 B → 传本函数 `__pld_U[B]`（upvalue 转递）。
- GETUPVAL A B → `R(A) := __pld_U[B].v`；SETUPVAL A B → `__pld_U[B].v := R(A)`。
- CLOSE A：对每个 `>= A` 的被捕获寄存器换新盒 `__pld_R[i] = {v = __pld_R[i].v}`——已发出的闭包保留旧盒（=VM 关闭 upvalue），后续代码用新盒（=新一轮迭代新变量）。luac 在离开含被捕获局部量的块时必发 CLOSE（循环体尾、break、显式 do-end 尾），因此逐迭代捕获语义由此模板精确还原；RETURN 隐式关闭无需动作（帧亡盒存，闭包继续持有）。

- [ ] **Step 1: 写失败测试**

`tests/test_fallback_closures.py`：

```python
CLOSURE_CASES = [
    # upvalue 读写（GETUPVAL/SETUPVAL + 盒共享）
    'local c = 0 local function inc() c = c + 1 return c end '
    'print(inc(), inc(), c)',
    # 逐迭代捕获：循环体尾 CLOSE 换盒
    'local fs = {} for i = 1, 3 do fs[i] = function() return i end end '
    'print(fs[1](), fs[2](), fs[3]())',
    # 两个独立计数器：同一工厂两次实例化互不串盒
    'local function counter() local n = 0 return function() n = n + 1 return n end end '
    'local a, b = counter(), counter() print(a(), a(), b())',
    # do-end 块尾 CLOSE
    'local x = 1 local f do local y = 2 f = function() return x + y end end print(f())',
    # GETUPVAL 伪指令：孙函数经中间层转递 upvalue
    'local function outer() local v = 10 '
    'local function mid() local function inner() return v end return inner end '
    'return mid()() end print(outer())',
    # upvalue 写穿透两层
    'local n = 0 local function bump() local function go() n = n + 1 end go() end '
    'bump() bump() print(n)',
    # 闭包与寄存器复用：CLOSE 后同 slot 新变量不得污染旧闭包
    'local fs = {} for i = 1, 2 do local v = i * 10 fs[i] = function() return v end end '
    'print(fs[1](), fs[2]())',
    # 混合：捕获的循环变量被闭包内自增
    'local fs = {} for i = 1, 2 do fs[i] = function() i = i + 100 return i end end '
    'print(fs[1](), fs[1](), fs[2]())',
]


def test_closure_cases():
    from tests.diffexec import assert_fallback_roundtrip
    for src in CLOSURE_CASES:
        assert_fallback_roundtrip(src)


def test_deep_nesting_factory_table():
    """嵌套 5 层 + 同层多兄弟：工厂表命名路径唯一性。"""
    from tests.diffexec import assert_fallback_roundtrip
    src = (
        "local function l1() local a = 1\n"
        "  local function l2() local b = 2\n"
        "    local function l3() local c = 3\n"
        "      local function l4() local d = 4\n"
        "        local function l5() return a + b + c + d end\n"
        "        return l5() end\n"
        "      return l4() end\n"
        "    return l3() end\n"
        "  return l2() end\n"
        "local function sibling() return 100 end\n"
        "print(l1() + sibling())\n")
    dec = assert_fallback_roundtrip(src)
    assert dec.count(b'__pld_F["main_') >= 6          # 工厂逐一登记


def test_emitted_helper_names_cannot_collide_with_globals():
    """`__pld_` 前缀是发射器辅助名与字节码全局名之间的唯一防线。"""
    import pytest
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import EmitError, emit_chunk
    # 正常情形：全局名照常按标识符发射，产物可编译
    bc = oracle.compile_source(b"local x = 1 local f = function() return x end print(f())")
    dec = emit_chunk(load_bytes(bc))
    assert b"print" in dec
    oracle.compile_source(dec)
    # 冲突情形：字节码里出现 __pld_ 前缀的全局名 → 必须 hard fail，绝不静默串名
    bad = oracle.compile_source(b"__pld_R = 1 return __pld_R")
    with pytest.raises(EmitError):
        emit_chunk(load_bytes(bad))


def test_all_38_opcodes_reachable_in_emitter():
    """公理层完整性：每个 opcode 至少被一个差分用例吃过（含语料未用的 5 个）。"""
    from pyluadec.lift.opcodes import Op
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.lift import lift_proto
    from tests.diffexec import assert_fallback_roundtrip
    from tests.test_fallback_basic import STRAIGHT_LINE_CASES
    from tests.test_fallback_control import CONTROL_CASES
    seen: set[Op] = set()

    def collect(p):
        fn = lift_proto(p)
        seen.update(li.ri.op for li in fn.instrs.values())
        for s in p.subprotos:
            collect(s)

    # 语义补充用例（不为 opcode 覆盖，三份 CASES 已达 38/38——见下方实测注记）：
    # 元方法路径与浮点格式化是发射器最容易悄悄失真的两处。
    extra = [
        'local t = setmetatable({}, {__index = function() return "mm" end}) print(t.k)',
        'io.write(tostring(2 ^ 0.5):sub(1, 6), "\\n")',
    ]
    for src in [*STRAIGHT_LINE_CASES, *CONTROL_CASES, *CLOSURE_CASES, *extra]:
        assert_fallback_roundtrip(src)
        collect(load_bytes(oracle.compile_source(src.encode())))
    missing = {op.name for op in Op} - {op.name for op in seen}
    assert not missing, f"opcodes never exercised: {sorted(missing)}"
```

Run: `uv run pytest tests/test_fallback_closures.py -v`
Expected: FAIL（CLOSURE 不支持）

- [ ] **Step 2: 实现——`_emit_simple` 追加四个分支**

```python
        elif op is Op.GETUPVAL:
            L.append(wr(a, f"__pld_U[{b}].v"))
        elif op is Op.SETUPVAL:
            L.append(f"__pld_U[{b}].v = {rd(a)}")
        elif op is Op.CLOSE:
            for i in sorted(self.boxed):
                if i >= a:
                    L.append(f"__pld_R[{i}] = {{v = __pld_R[{i}].v}}")
        elif op is Op.CLOSURE:
            caps = []
            for idx, ps in enumerate(self.fn.closure_pseudo[ri.pc]):
                if ps.op is Op.MOVE:
                    if ps.b not in self.boxed:
                        raise EmitError(
                            f"pc {ri.pc}: captured register {ps.b} not boxed (lift bug)")
                    caps.append(f"[{idx}]=__pld_R[{ps.b}]")      # 盒对象本身
                else:                                            # GETUPVAL 伪指令
                    caps.append(f"[{idx}]=__pld_U[{ps.b}]")
            child = f"{self.path}_{bx}"
            L.append(wr(a, f'__pld_F["{child}"]({{{", ".join(caps)}}})'))
```

（`raise EmitError(... not yet supported)` 的兜底分支保留——38 opcode 已全覆盖后它只对损坏字节码可达，是诚实的 hard-fail 而非静默。）

- [ ] **Step 3: 运行 fallback 全部测试**

Run: `uv run pytest tests/test_fallback_basic.py tests/test_fallback_control.py tests/test_fallback_closures.py -v`
Expected: 全 PASS；`test_all_38_opcodes_reachable_in_emitter` 证实 38/38 覆盖

- [ ] **Step 4: 语料冒烟（正式门在 Task 11）**

```bash
uv run python - <<'PY'
import os, pathlib
from pyluadec import oracle
from pyluadec.ingest import load_file
from pyluadec.structure.fallback import emit_chunk
c = pathlib.Path(os.environ["PYLUADEC_CORPUS_DIR"])
files = sorted(c.glob("*.lua"))[:10]
for f in files:
    oracle.compile_source(emit_chunk(load_file(f)))
    print("ok", f.name)
PY
```

Expected: 10 个 `ok`（含嵌套闭包重灾区文件也可编译）

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: fallback emitter closures/upvalues/CLOSE; all 38 opcodes covered by differential tests"
```

---

### Task 9: L3.0 归一化比对器

**Files:**
- Create: `src/pyluadec/verify/__init__.py`, `src/pyluadec/verify/normalize.py`
- Test: `tests/test_normalize.py`

**Interfaces:**
- Consumes: `ingest.Proto`/`LuaNumber`。
- Produces（M3+ 的 pass 验证门与认证共用；M2 内被台账在 L3 试证时调用）:
  - `@dataclass(frozen=True) Mismatch: path: str; field: str; a: str; b: str`（`path` 形如 `root/1/0`，`a`/`b` 为 repr 串）
  - `NORMALIZATIONS: tuple[tuple[str, Callable[[Proto], Proto]], ...]`（版本化归一化阶梯；M2 为空元组 = 只有 L3.0）
  - `LADDER_VERSION: str = "l3-ladder-v0"`（阶梯内容变更时必须 bump，台账记录）
  - `normalize(p: Proto, level: int) -> Proto`（level 越界抛 ValueError）
  - `compare_protos(a: Proto, b: Proto, level: int = 0) -> list[Mismatch]`（空列表 = 该级等价；数字常量按 payload 逐位比较）

- [ ] **Step 1: 写失败测试**

`tests/test_normalize.py`：

```python
def _bc(src: str) -> "Proto":
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode()), chunkname="=t")


def test_same_source_twice_is_l30_equal():
    from pyluadec.verify.normalize import compare_protos
    src = 'local x = 1.5 local function f(a) return a + x end print(f(2))'
    assert compare_protos(_bc(src), _bc(src), level=0) == []


def test_negative_examples_are_caught():
    from pyluadec.verify.normalize import compare_protos
    cases = [
        ("return 1", "return 2"),                       # 常量 payload 不同
        ("return 0.0", "return -0.0"),                  # payload 逐位比较的招牌用例
        ("local a = 1 return a", "return 1"),           # code 不同
        ("print(1)", "print(1) print(2)"),              # code 长度不同
        ("local f = function() end", "local f = function() return 1 end"),  # 子 proto
    ]
    for sa, sb in cases:
        assert compare_protos(_bc(sa), _bc(sb), level=0) != [], (sa, sb)


def test_line_layout_difference_is_l30_visible():
    """L3.0 是全严格：只多一个空行（lineinfo 变了）也要报差异——诚实优先。"""
    from pyluadec.verify.normalize import compare_protos
    a, b = _bc("print(1)"), _bc("\nprint(1)")
    diffs = compare_protos(a, b, level=0)
    assert diffs and all("line" in d.field for d in diffs)


def test_mismatch_paths_point_into_subprotos():
    from pyluadec.verify.normalize import compare_protos
    a = _bc("local f = function() return 1 end print(f())")
    b = _bc("local f = function() return 2 end print(f())")
    diffs = compare_protos(a, b, level=0)
    assert any(d.path.startswith("root/0") for d in diffs)


def test_bad_level_raises():
    import pytest
    from pyluadec.verify.normalize import normalize
    p = _bc("return 1")
    with pytest.raises(ValueError):
        normalize(p, level=99)
```

Run: `uv run pytest tests/test_normalize.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/verify/normalize.py`**

`src/pyluadec/verify/__init__.py` 为空文件。normalize.py：

```python
"""L3 归一化比对器（spec §5）。

L3.0 = 严格逐字段相等（含 lineinfo/locvars —— 诚实的最严基线）。
L3.k = 依次应用 NORMALIZATIONS[:k] 后比较；每级归一化必须单独论证健全性
（spec §9 R3），并 bump LADDER_VERSION。M2 阶梯为空。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pyluadec.ingest.proto import LuaNumber, Proto

NORMALIZATIONS: tuple[tuple[str, Callable[[Proto], Proto]], ...] = ()
LADDER_VERSION = "l3-ladder-v0"


@dataclass(frozen=True)
class Mismatch:
    path: str
    field: str
    a: str
    b: str


def normalize(p: Proto, level: int) -> Proto:
    if not 0 <= level <= len(NORMALIZATIONS):
        raise ValueError(f"normalization level {level} out of range "
                         f"0..{len(NORMALIZATIONS)}")
    for _name, fn in NORMALIZATIONS[:level]:
        p = fn(p)
    return p


def compare_protos(a: Proto, b: Proto, level: int = 0) -> list[Mismatch]:
    out: list[Mismatch] = []
    _cmp(normalize(a, level), normalize(b, level), "root", out)
    return out


def _const_eq(x, y) -> bool:
    if isinstance(x, LuaNumber) and isinstance(y, LuaNumber):
        return x.payload == y.payload                  # 逐位，-0.0 ≠ 0.0
    if type(x) is not type(y):
        return False
    return x == y


def _cmp(a: Proto, b: Proto, path: str, out: list[Mismatch]) -> None:
    def diff(field: str, va, vb) -> None:
        out.append(Mismatch(path=path, field=field, a=repr(va), b=repr(vb)))

    for field in ("source", "linedefined", "lastlinedefined", "nups",
                  "numparams", "is_vararg", "maxstacksize"):
        va, vb = getattr(a, field), getattr(b, field)
        if va != vb:
            diff(field, va, vb)
    if a.code != b.code:
        diff("code", a.code, b.code)
    if len(a.constants) != len(b.constants):
        diff("constants.len", len(a.constants), len(b.constants))
    else:
        for i, (x, y) in enumerate(zip(a.constants, b.constants)):
            if not _const_eq(x, y):
                out.append(Mismatch(path=path, field=f"const[{i}]", a=repr(x), b=repr(y)))
    if a.lineinfo != b.lineinfo:
        diff("lineinfo", a.lineinfo, b.lineinfo)
    if a.locvars != b.locvars:
        diff("locvars", a.locvars, b.locvars)
    if a.upvalues != b.upvalues:
        diff("upvalues", a.upvalues, b.upvalues)
    if len(a.subprotos) != len(b.subprotos):
        diff("subprotos.len", len(a.subprotos), len(b.subprotos))
    else:
        for i, (sa, sb) in enumerate(zip(a.subprotos, b.subprotos)):
            _cmp(sa, sb, f"{path}/{i}", out)
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_normalize.py -v`
Expected: 全 PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: L3.0 strict proto comparator with versioned normalization ladder skeleton"
```

---

### Task 10: 认证台账（结构哈希 + jsonl 读写）

**Files:**
- Create: `src/pyluadec/verify/ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Consumes: `ingest.Proto`；Task 9 `LADDER_VERSION`。
- Produces（Task 11 与后续 ratchet CI 依赖）:
  - `structural_hash(p: Proto) -> str`（sha256 hex；只含结构字段：numparams/is_vararg/nups/maxstacksize/code/constants(payload|bytes hex)/len(upvalues)/subprotos 递归；**不含** source/行号/locvars/upvalue 名——同内容函数跨文件同哈希，spec §9 R4）
  - `@dataclass LedgerEntry: shash: str; level: str; l3_level: int | None; compile_ok: bool; fallback: bool; n_insns: int; confessions: list[dict]; occurrences: list[dict]; oracle: str; ladder: str`
    - `level ∈ {"L0","L1","L2","L3"}`；M2 产出恒 `"L1"`（可编译、未验证）
    - `confessions` 元素：`{"pc_lo": int, "pc_hi": int, "reason": str, "pass": str}`
    - `occurrences` 元素：`{"file": str, "proto_path": str}`（如 `"snr_crd_1.lua"`, `"main_0_3"`）
  - `entry_sort_key(e) -> tuple`、`write_ledger(entries, path)`、`read_ledger(path) -> list[LedgerEntry]`（jsonl，按 shash 排序写出，diff 稳定）
  - `oracle_version() -> str`（`git rev-parse HEAD`，取不到时 `"unknown"`）

- [ ] **Step 1: 写失败测试**

`tests/test_ledger.py`：

```python
def _bc(src: str):
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode()), chunkname="=t")


def test_structural_hash_ignores_debug_but_not_structure():
    from pyluadec.verify.ledger import structural_hash
    a = _bc("print(1)")
    b = _bc("\n\nprint(1)")                 # 只差行号布局
    c = _bc("print(2)")                     # 常量不同
    assert structural_hash(a) == structural_hash(b)
    assert structural_hash(a) != structural_hash(c)


def test_structural_hash_dedups_identical_functions_across_chunks():
    from pyluadec.verify.ledger import structural_hash
    a = _bc("local f = function(x) return x + 1 end return f")
    b = _bc("local g = function(y) return y + 1 end return g")
    # 子函数字节码同构（寄存器/常量布局一致）→ 同哈希；外层 chunk 常量名不同不影响子哈希
    assert structural_hash(a.subprotos[0]) == structural_hash(b.subprotos[0])


def test_payload_distinction():
    from pyluadec.verify.ledger import structural_hash
    assert structural_hash(_bc("return 0.0")) != structural_hash(_bc("return -0.0"))


def test_ledger_roundtrip(tmp_path):
    from pyluadec.verify.ledger import LedgerEntry, read_ledger, write_ledger
    entries = [
        LedgerEntry(shash="ff" * 32, level="L1", l3_level=None, compile_ok=True,
                    fallback=True, n_insns=7,
                    confessions=[{"pc_lo": 1, "pc_hi": 7, "reason": "fallback-state-machine",
                                  "pass": "structure.fallback"}],
                    occurrences=[{"file": "a.lua", "proto_path": "main"}],
                    oracle="deadbeef", ladder="l3-ladder-v0"),
        LedgerEntry(shash="aa" * 32, level="L1", l3_level=None, compile_ok=True,
                    fallback=True, n_insns=3, confessions=[],
                    occurrences=[{"file": "b.lua", "proto_path": "main_0"}],
                    oracle="deadbeef", ladder="l3-ladder-v0"),
    ]
    p = tmp_path / "ledger.jsonl"
    write_ledger(entries, p)
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"shash": "aa')          # 按 shash 排序写出
    back = read_ledger(p)
    assert back == sorted(entries, key=lambda e: e.shash)


def test_oracle_version_is_hexish():
    from pyluadec.verify.ledger import oracle_version
    v = oracle_version()
    assert v == "unknown" or (len(v) == 40 and all(ch in "0123456789abcdef" for ch in v))
```

Run: `uv run pytest tests/test_ledger.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/verify/ledger.py`**

```python
"""认证台账（spec §5）：主键 = 归一化结构哈希，jsonl 落盘，diff 稳定。"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pyluadec.ingest.proto import LuaNumber, Proto


def _structure_view(p: Proto) -> dict:
    def conv(c):
        if isinstance(c, LuaNumber):
            return {"t": "num", "p": c.payload.hex()}
        if isinstance(c, bytes):
            return {"t": "str", "v": c.hex()}
        if c is None:
            return {"t": "nil"}
        return {"t": "bool", "v": c}

    return {
        "numparams": p.numparams,
        "is_vararg": p.is_vararg,
        "nups": p.nups,
        "maxstacksize": p.maxstacksize,
        "code": list(p.code),
        "constants": [conv(c) for c in p.constants],
        "n_upvalues": len(p.upvalues),
        "subprotos": [_structure_view(s) for s in p.subprotos],
    }


def structural_hash(p: Proto) -> str:
    blob = json.dumps(_structure_view(p), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def oracle_version() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"],
                           cwd=Path(__file__).resolve().parents[3],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except OSError:
        return "unknown"


@dataclass
class LedgerEntry:
    shash: str
    level: str                    # L0 | L1 | L2 | L3
    l3_level: int | None
    compile_ok: bool
    fallback: bool
    n_insns: int
    confessions: list[dict]
    occurrences: list[dict]
    oracle: str
    ladder: str


def write_ledger(entries: list[LedgerEntry], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for e in sorted(entries, key=lambda e: e.shash):
            fh.write(json.dumps(dataclasses.asdict(e), ensure_ascii=False) + "\n")


def read_ledger(path: Path) -> list[LedgerEntry]:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(LedgerEntry(**json.loads(line)))
    return out
```

（`parents[3]`：`src/pyluadec/verify/ledger.py` → parents = [verify, pyluadec, src, 仓库根]。）

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_ledger.py -v`
Expected: 全 PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: certification ledger v1 with content-addressed structural hashing"
```

---

### Task 11: pipeline 驱动 + 全语料门 + 台账落盘 + 面板

**Files:**
- Create: `src/pyluadec/pipeline.py`, `scripts/run_corpus.py`, `scripts/ledger_dashboard.py`
- Create（由 run_corpus 产出并提交）: `corpus/ledger.jsonl`
- Test: `tests/test_pipeline.py`, `tests/test_corpus_compile.py`, `tests/test_ledger_ratchet.py`

**Interfaces:**
- Consumes: Tasks 6-10 全部。
- Produces:
  - `pyluadec.pipeline`:
    - `walk_proto_paths(path: str, p: Proto, out: dict[str, Proto]) -> None`（前序遍历，把 `proto_path → Proto` 填进 `out`；命名方案与 `fallback.emit_chunk` 的工厂键一致：`main`、`main_0`、`main_0_3`。公开 API —— `run_corpus.py` 与后续 M3 台账都要用）
    - `@dataclass DecompileResult: source: bytes; confessions_by_proto: dict[str, list[dict]]`（键为 proto_path，如 `"main_0_3"`）
    - `decompile_chunk(root: Proto) -> DecompileResult`（M2 恒走 fallback；每个 proto 记一条 confession `{"pc_lo": 1, "pc_hi": len(code), "reason": "fallback-state-machine", "pass": "structure.fallback"}`）
    - `decompile_file(path) -> DecompileResult`
  - `scripts/run_corpus.py`（CLI）：全语料反编译 → `build/decompiled/<name>.lua` → `luac_sz4` 编译验证 → 台账条目（按 shash 去重合并 occurrences）→ `corpus/ledger.jsonl`；打印 `compiled <ok>/<total>`；有编译失败则 exit 1
  - `scripts/ledger_dashboard.py`（CLI）：读 `corpus/ledger.jsonl`，输出面板（`--markdown` 可选）：唯一 proto 数 / 各等级计数 / compile_ok 比例 / fallback 比例 / confession 理由 TOP / oracle+ladder 版本

- [ ] **Step 1: 写失败测试**

`tests/test_pipeline.py`：

```python
def test_decompile_chunk_confesses_per_proto():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(
        b"local f = function() return 1 end local g = function() return 2 end print(f(), g())")
    res = decompile_chunk(load_bytes(bc))
    assert set(res.confessions_by_proto) == {"main", "main_0", "main_1"}
    for path, confs in res.confessions_by_proto.items():
        assert confs[0]["reason"] == "fallback-state-machine"
        assert confs[0]["pc_lo"] == 1 and confs[0]["pc_hi"] >= 1
    oracle.compile_source(res.source)      # 产物可编译


def test_decompile_file(tmp_path):
    from pyluadec import oracle
    from pyluadec.pipeline import decompile_file
    src = tmp_path / "x.lua"
    src.write_bytes(oracle.compile_source(b'print("file path entry")'))
    res = decompile_file(src)
    r = oracle.run_bytes(res.source, is_source=True)
    assert r.stdout == b"file path entry\n"
```

`tests/test_corpus_compile.py`（**M2 出口门**）：

```python
def test_all_229_corpus_files_produce_compilable_output(corpus_dir):
    from pyluadec import oracle
    from pyluadec.pipeline import decompile_file
    failures = []
    files = sorted(corpus_dir.glob("*.lua"))
    for f in files:
        try:
            oracle.compile_source(decompile_file(f).source)
        except Exception as e:                                    # noqa: BLE001
            failures.append((f.name, str(e)[:200]))
    assert len(files) == 229
    assert failures == [], f"{len(failures)} files failed: {failures[:5]}"
```

`tests/test_ledger_ratchet.py`（棘轮雏形：提交的台账必须保持 M2 底线）:

```python
import json
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "corpus" / "ledger.jsonl"


def test_committed_ledger_exists_and_holds_the_line():
    assert LEDGER.exists(), "corpus/ledger.jsonl 未提交（先跑 scripts/run_corpus.py）"
    entries = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    assert entries, "台账为空"
    assert all(e["compile_ok"] for e in entries), "存在不可编译 proto —— M2 底线被击穿"
    assert all(e["level"] in ("L1", "L2", "L3") for e in entries), "出现 L0 —— 不许倒退"
    hashes = [e["shash"] for e in entries]
    assert hashes == sorted(hashes) and len(set(hashes)) == len(hashes)


def test_ledger_covers_full_corpus(corpus_dir):
    entries = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    files_in_ledger = {o["file"] for e in entries for o in e["occurrences"]}
    corpus_files = {f.name for f in corpus_dir.glob("*.lua")}
    assert files_in_ledger == corpus_files
    n_occurrences = sum(len(e["occurrences"]) for e in entries)
    assert n_occurrences == 1944                    # 全部 proto 都有台账归属
```

Run: `uv run pytest tests/test_pipeline.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `src/pyluadec/pipeline.py`**

```python
"""反编译驱动：M2 阶段一切函数走 fallback 状态机（spec §7 M2）。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyluadec.ingest import load_file as _ingest_file
from pyluadec.ingest.proto import Proto
from pyluadec.structure.fallback import emit_chunk


@dataclass
class DecompileResult:
    source: bytes
    confessions_by_proto: dict[str, list[dict]]


def walk_proto_paths(path: str, p: Proto, out: dict[str, Proto]) -> None:
    out[path] = p
    for i, s in enumerate(p.subprotos):
        walk_proto_paths(f"{path}_{i}", s, out)


def decompile_chunk(root: Proto) -> DecompileResult:
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    confessions = {
        path: [{"pc_lo": 1, "pc_hi": len(p.code),
                "reason": "fallback-state-machine", "pass": "structure.fallback"}]
        for path, p in protos.items()
    }
    return DecompileResult(source=emit_chunk(root), confessions_by_proto=confessions)


def decompile_file(path) -> DecompileResult:
    return decompile_chunk(_ingest_file(Path(path)))
```

Run: `uv run pytest tests/test_pipeline.py -v` → 全 PASS

- [ ] **Step 3: 实现 `scripts/run_corpus.py`**

```python
"""全语料反编译 + 编译验证 + 台账落盘。

用法: PYLUADEC_CORPUS_DIR=... uv run python scripts/run_corpus.py
产出: build/decompiled/<name>.lua（不入库）与 corpus/ledger.jsonl（入库）。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    from pyluadec import oracle
    from pyluadec.ingest import load_file
    from pyluadec.pipeline import walk_proto_paths, decompile_chunk
    from pyluadec.verify.ledger import (LedgerEntry, oracle_version, structural_hash,
                                        write_ledger)
    from pyluadec.verify.normalize import LADDER_VERSION

    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    outdir = ROOT / "build" / "decompiled"
    outdir.mkdir(parents=True, exist_ok=True)
    orc = oracle_version()
    by_hash: dict[str, LedgerEntry] = {}
    n_ok = 0
    files = sorted(corpus.glob("*.lua"))
    for f in files:
        root = load_file(f)
        res = decompile_chunk(root)
        (outdir / f.name).write_bytes(res.source)
        try:
            oracle.compile_source(res.source)
            compile_ok = True
            n_ok += 1
        except oracle.LuaCompileError as e:
            compile_ok = False
            print(f"COMPILE FAIL {f.name}: {str(e)[:200]}", file=sys.stderr)
        protos = {}
        walk_proto_paths("main", root, protos)
        for path, p in protos.items():
            h = structural_hash(p)
            occ = {"file": f.name, "proto_path": path}
            if h in by_hash:
                e = by_hash[h]
                e.occurrences.append(occ)
                e.compile_ok = e.compile_ok and compile_ok
            else:
                by_hash[h] = LedgerEntry(
                    shash=h, level="L1" if compile_ok else "L0",
                    l3_level=None, compile_ok=compile_ok, fallback=True,
                    n_insns=len(p.code),
                    confessions=res.confessions_by_proto[path],
                    occurrences=[occ], oracle=orc, ladder=LADDER_VERSION)
    for e in by_hash.values():
        if not e.compile_ok:
            e.level = "L0"
    write_ledger(list(by_hash.values()), ROOT / "corpus" / "ledger.jsonl")
    print(f"compiled {n_ok}/{len(files)}; ledger: {len(by_hash)} unique protos "
          f"({sum(len(e.occurrences) for e in by_hash.values())} occurrences)")
    return 0 if n_ok == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 实现 `scripts/ledger_dashboard.py`**

```python
"""台账面板：corpus/ledger.jsonl 的可读汇总。用法: uv run python scripts/ledger_dashboard.py [--markdown]"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    md = "--markdown" in sys.argv[1:]
    path = ROOT / "corpus" / "ledger.jsonl"
    if not path.exists():
        print("no ledger; run scripts/run_corpus.py first", file=sys.stderr)
        return 1
    entries = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    levels = Counter(e["level"] for e in entries)
    reasons = Counter(c["reason"] for e in entries for c in e["confessions"])
    n_occ = sum(len(e["occurrences"]) for e in entries)
    n_files = len({o["file"] for e in entries for o in e["occurrences"]})
    compile_ok = sum(1 for e in entries if e["compile_ok"])
    fallback = sum(1 for e in entries if e["fallback"])
    oracle_v = {e["oracle"] for e in entries}
    ladder_v = {e["ladder"] for e in entries}

    rows = [
        ("unique protos", len(entries)),
        ("occurrences", n_occ),
        ("files", n_files),
        ("compile_ok", f"{compile_ok}/{len(entries)}"),
        ("fallback", f"{fallback}/{len(entries)}"),
        *[(f"level {k}", v) for k, v in sorted(levels.items())],
        *[(f"confession: {k}", v) for k, v in reasons.most_common(10)],
        ("oracle", ", ".join(sorted(oracle_v))),
        ("ladder", ", ".join(sorted(ladder_v))),
    ]
    if md:
        print("| metric | value |\n|---|---|")
        for k, v in rows:
            print(f"| {k} | {v} |")
    else:
        w = max(len(k) for k, _ in rows)
        for k, v in rows:
            print(f"{k:<{w}}  {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 全语料跑门 + 台账落盘 + 提交台账**

```bash
uv run python scripts/run_corpus.py          # 期望: compiled 229/229
uv run python scripts/ledger_dashboard.py    # 期望: level L1 = 全部唯一 proto 数，L0 = 0
uv run pytest tests/test_corpus_compile.py tests/test_ledger_ratchet.py -v
```

Expected: `compiled 229/229`；ratchet 测试 PASS。若个别文件编译失败：读 luac stderr 定位发射缺陷（通常是字面量转义或 open 调用形态边角），修复发射器后重跑——**不许**在 run_corpus 里跳过文件。

- [ ] **Step 6: 抽样差分执行冒烟（超出出口要求的诚实性检查）**

229 个文件的产物**编译**都过了；再抽 3 个小语料文件做**运行**冒烟（多数语料引擎 API 缺失跑不完，选择纯逻辑早退的文件；若全都需要引擎则记录并跳过，不算失败——运行级验证是 M5 的 L2 门，不是 M2 出口）：

```bash
uv run python - <<'PY'
import os, pathlib
from pyluadec import oracle
from pyluadec.pipeline import decompile_file
c = pathlib.Path(os.environ["PYLUADEC_CORPUS_DIR"])
for name in ("config.lua",):
    f = c / name
    r1 = oracle.run_bytes(f.read_bytes(), is_source=False, timeout=5)
    r2 = oracle.run_bytes(decompile_file(f).source, is_source=True, timeout=5)
    print(name, "exit", r1.returncode, r2.returncode,
          "stdout match" if r1.stdout == r2.stdout else "STDOUT DIFF")
PY
```

Expected: exit code 与 stdout 两侧一致（多为立即因缺全局函数而报错——两侧报一致即是有效信号）。

- [ ] **Step 7: Commit（含 corpus/ledger.jsonl）**

```bash
git add -A && git commit -m "feat: M2 exit — 229/229 corpus compilable via fallback, ledger v1 committed, dashboard online"
```

---

### Task 12: 文档沉淀与收尾

**Files:**
- Create: `docs/runbooks/decompile-pipeline.md`, `CHANGELOG.md`
- Modify: `CLAUDE.md`（「本仓库现状」一节）

**Interfaces:** 无代码接口；本 Task 是 spec「重开仓库正是因为缺文档」的落实。

- [ ] **Step 1: 写 `docs/runbooks/decompile-pipeline.md`**

全文写入（不留提纲），内容涵盖：
- M2 管线形态：`ingest → lift → cfg → structure.fallback → oracle 编译验证 → ledger`，每层的模块路径与关键函数名（`load_file` / `lift_proto` / `build_cfg` / `emit_chunk` / `decompile_file`）。
- 常用操作：单文件反编译（`uv run python -c "from pyluadec.pipeline import decompile_file; ..."`）；全语料跑门 `scripts/run_corpus.py`；面板 `scripts/ledger_dashboard.py [--markdown]`；差分执行调试单个用例（`tests/diffexec.assert_fallback_roundtrip` 的交互式用法）。
- fallback 产物的阅读指南：`__pld_R`/`__pld_U`/盒/`__pld_pc` 状态机与 pc↔golden listing 对照调试法（`luac_sz4 -l -l` 打印原字节码 listing，逐状态核对）。
- 台账字段语义与 ratchet 纪律：等级只升不降；`corpus/ledger.jsonl` 变更须由 `run_corpus.py` 产生并整体提交，禁止手编；`discrepancies.json` 属门产物不入库（Phase 1 遗留决定的正式记录）。
- 效应表三档（STRICT/NO_METAMETHOD/TRUSTING）的语义与「M4 才标定默认档」的现状。

- [ ] **Step 2: 写 `CHANGELOG.md`**

```markdown
# Changelog

## 2026-08-10 — M1 (partial): macOS arm64 migration gate green

- `./scripts/verify_migration.sh` → `ALL MIGRATION GATES PASSED on arm64 / Darwin`
  （首个 64 位平台；核心命题非空验证：luac_sz8 拒绝语料、luac_sz4 字节级 roundtrip）。
- Linux x86_64 侧验证仍待执行；两平台全绿后 M1 方告完成（runbook 双平台要求）。

## <Task 11 完成日期> — M2: fallback closed loop

- 229/229 语料文件产出可编译 Lua 源码（fallback 状态机）。
- 认证台账 corpus/ledger.jsonl v1 上线（主键=结构哈希，全部 L1）。
- 38 opcode 效应表、CFG+支配树、L3.0 严格比对器就位。
```

（M2 行的日期按实际完成日填写；若 Linux M1 验证先完成，则先补一条 M1 完成记录。）

- [ ] **Step 3: 更新 `CLAUDE.md`「本仓库现状」**

在既有 Phase 1 内容后追加 Phase 2 (M2) 现状段：管线模块布局（lift/cfg/structure/verify/pipeline）、新增常用命令（`scripts/run_corpus.py`、`scripts/ledger_dashboard.py`）、台账约定（check-in、只由脚本再生、ratchet 测试守护）、fallback 定位（语义精确但丑，M3 起结构化替换）。

- [ ] **Step 4: 全量回归**

Run: `uv run pytest -v`
Expected: 全 PASS（Phase 1 的 23 项 + Phase 2 全部新增）

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "docs: decompile pipeline runbook, changelog, CLAUDE.md phase 2 status"
```

---

## 完成定义（M2 出口，对照 spec §7）

- [ ] 229 语料文件 100% 产出可编译输出：`tests/test_corpus_compile.py` PASS + `run_corpus.py` 报 `compiled 229/229`。
- [ ] 台账面板上线：`corpus/ledger.jsonl` 提交入库，`ledger_dashboard.py` 可读汇总，ratchet 测试守护底线。
- [ ] 公理层完整：38/38 opcode 有效应表行 + 发射模板 + 差分执行覆盖（`test_all_38_opcodes_reachable_in_emitter`）。
- [ ] 解码器经 golden listing 全语料 21 万条指令核对（`test_decoder_matches_all_golden_listings`）。
- [ ] CFG/支配树就位且 CFG 被 fallback 实际消费；L3.0 比对器以正负例测试。
- [ ] 里程碑收尾走 superpowers 流程：requesting-code-review + verification-before-completion。

## 显式非目标（M3+ 范围，本计划不做）

- 结构化区域识别（if/while/for 还原）、表达式内联、变量命名合成——M3/M4。
- L2 差分执行认证与按键序列回归——M5（Task 11 Step 6 的运行冒烟只是诚实性抽查）。
- L3.1+ 归一化级（寄存器重编号等）——M3；效应档位标定——M4。
- 旧项目 `test_ir_pipeline.py` 86 例的转译清单——依 spec §8 在台账上线后（M2 完成时）作为 M3 输入生成。
- 完整 Ratchet CI（baseline diff、等级降级即 fail、`git bisect` 自动定位、oracle 升级触发全量重认证）——spec §5 的完整形态属 M3；本计划只交付 `tests/test_ledger_ratchet.py` 这一守底线的雏形（全部 compile_ok、无 L0、主键有序去重）。
- 公理层的生成式属性测试（源码生成 → luac → lift → 门控内联 → 打印 → 重编译 → 归一化比对，spec §7 金字塔第 1 层的完整形态）——依赖内联，属 M4；本计划以 golden listing 全语料 21 万条指令核对 + 1944 函数 PC 认领审计作为公理层的 M2 级证据。

# Phase 1（M0 基建 + M1 六四切换）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立双字长（sz4/sz8）Lua 构建 + 无损 pybind 摄入层，固化 golden 基线，通过 32→64 位迁移三道门。

**Architecture:** vendor 内 pristine Lua 5.1.5 源码在构建期打序列化宽度补丁，产出两套静态库/oracle 二进制/pybind 模块；Python 侧按 bytecode header 派发到对应模块，导出为不可变 Proto 数据类；golden 由旧项目工具一次性固化后只读，新摄入层与之全语料 parity 比对。

**Tech Stack:** uv + Python ≥3.12、CMake ≥3.24、pybind11（pip 安装）、pytest。语料与旧工具位于 `/root/pyluadec`（仅 Step 0 golden 固化时使用）。

## Global Constraints

- 代码中禁止绝对路径；语料位置一律经环境变量 `PYLUADEC_CORPUS_DIR` 获取（本机为 `/root/pyluadec/others/script_to_decompile`）。
- 一切源自 bytecode 的字符串在 Python 侧一律为 `bytes`，绝不 decode（打印/展示层才转义）。
- 数字常量必须携带原始 8 字节 payload，比较按 payload 逐位。
- CMake 平台条件化：Linux/Darwin 均须可配置（`LUA_USE_POSIX`，不用 readline，`m` 仅 Linux 链接）。
- `corpus/golden/` 在 Task 7 固化后只读，任何后续任务不得重写其内容。
- 每个 Task 以 commit 结束；测试命令统一 `uv run pytest`。
- vendor 内 Lua 源码保持 pristine，一切修改经 `native/patches/*.patch` 在构建目录中应用。

---

### Task 1: uv 项目骨架

**Files:**
- Create: `pyproject.toml`, `src/pyluadec/__init__.py`, `src/pyluadec/_native/__init__.py`, `tests/test_smoke.py`, `tests/conftest.py`, `.gitignore`

**Interfaces:**
- Produces: 包 `pyluadec`（src 布局）；pytest fixture `corpus_dir`（无语料时 skip）。

- [ ] **Step 1: 初始化项目与依赖**

```bash
cd /root/pyluadec-refactor
uv init --lib --name pyluadec --python ">=3.12"
uv add --dev pytest
uv add pybind11
```

若 `uv init` 生成的布局与下述文件冲突，以下述为准（保留 `pyproject.toml` 中 uv 生成的构建配置，`requires-python = ">=3.12"`）。

- [ ] **Step 2: 写 `.gitignore` 与 fixture**

`.gitignore`：

```
build/
.venv/
__pycache__/
src/pyluadec/_native/*.so
*.egg-info/
```

`src/pyluadec/_native/__init__.py`（空文件，占位使 gitignore 的 so 有归属包）。

`tests/conftest.py`：

```python
import os
from pathlib import Path
import pytest

@pytest.fixture(scope="session")
def corpus_dir() -> Path:
    p = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not p or not Path(p).is_dir():
        pytest.skip("PYLUADEC_CORPUS_DIR not set or missing (corpus tests skipped)")
    return Path(p)
```

`tests/test_smoke.py`：

```python
def test_package_importable():
    import pyluadec  # noqa: F401
```

- [ ] **Step 3: 运行测试确认通过**

Run: `uv run pytest -v`
Expected: `test_package_importable PASS`（corpus 相关无）

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: uv project skeleton with pytest and corpus fixture"
```

---

### Task 2: vendor 导入 vanilla Lua 5.1.5

**Files:**
- Create: `vendor/lua-5.1/`（src/、doc/、etc/、COPYRIGHT、README、HISTORY、INSTALL、Makefile、test/）
- Test: `tests/test_vendor.py`

**Interfaces:**
- Produces: `vendor/lua-5.1/src/*.c|h` pristine 源码（后续构建唯一来源）。

- [ ] **Step 1: 从旧仓库的 vanilla import commit 提取（避开工作树中的 .o/.a 污染）**

```bash
mkdir -p vendor
git -C /root/pyluadec archive 8068258 lua-5.1 | tar -x -C vendor/
rm -f vendor/lua-5.1/src/luac.out vendor/lua-5.1/.git vendor/lua-5.1/CMakeLists.txt
```

（`8068258` 是旧仓库 "add lua5.1 official sourcces" 提交；`luac.out` 是误提交的构建产物；`CMakeLists.txt` 是旧项目自加的，本仓库重写；`.git` 是残留 gitlink。若 `git archive` 因权限失败，改用 `git -C /root/pyluadec show 8068258 -- <file>` 逐目录导出或从 lua.org 官方 tarball lua-5.1.5.tar.gz 解压，二者内容一致。）

- [ ] **Step 2: 写校验测试**

`tests/test_vendor.py`：

```python
from pathlib import Path

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "lua-5.1"

def test_vendor_is_lua_515():
    lua_h = (VENDOR / "src" / "lua.h").read_text()
    assert 'LUA_RELEASE\t"Lua 5.1.5"' in lua_h

def test_vendor_has_no_build_artifacts():
    assert not list(VENDOR.rglob("*.o"))
    assert not list(VENDOR.rglob("*.a"))
    assert not (VENDOR / "src" / "luac.out").exists()

def test_undump_sources_present():
    for f in ("lundump.c", "lundump.h", "ldump.c", "luac.c", "print.c"):
        assert (VENDOR / "src" / f).exists()
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_vendor.py -v`
Expected: 3 PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: vendor pristine Lua 5.1.5 sources"
```

---

### Task 3: 序列化宽度补丁

**Files:**
- Create: `native/patches/0001-serial-sizet.patch`
- Test: `tests/test_patch.py`

**Interfaces:**
- Produces: 补丁引入类型 `lua_SerialSizet`（默认 `size_t`，可由 `-DLUAC_SERIAL_SIZET=uint32_t|uint64_t` 覆盖）；被 Task 4 的 CMake 应用。

- [ ] **Step 1: 在 scratch 目录制作补丁**

复制 `vendor/lua-5.1` 两份到 scratch（`a/`、`b/`），对 `b/` 做以下 4 处编辑：

`b/src/lundump.h` —— 在 `#include "lzio.h"` 之后插入：

```c
#include <stdint.h>
#ifndef LUAC_SERIAL_SIZET
#define LUAC_SERIAL_SIZET size_t
#endif
typedef LUAC_SERIAL_SIZET lua_SerialSizet;
```

`b/src/lundump.c` —— `LoadString`（原 76 行起）中 `size_t size;` 改为 `lua_SerialSizet size;`，其后三处使用加显式转换：

```c
static TString* LoadString(LoadState* S)
{
 lua_SerialSizet size;
 LoadVar(S,size);
 if (size==0)
  return NULL;
 else
 {
  char* s=luaZ_openspace(S->L,S->b,(size_t)size);
  LoadBlock(S,s,(size_t)size);
  return luaS_newlstr(S->L,s,(size_t)size-1);		/* remove trailing '\0' */
 }
}
```

`b/src/lundump.c` —— `luaU_header` 中 `*h++=(char)sizeof(size_t);` 改为 `*h++=(char)sizeof(lua_SerialSizet);`

`b/src/ldump.c` —— `DumpString` 中两处：

```c
static void DumpString(const TString* s, DumpState* D)
{
 if (s==NULL || getstr(s)==NULL)
 {
  lua_SerialSizet size=0;
  DumpVar(size,D);
 }
 else
 {
  lua_SerialSizet size=(lua_SerialSizet)(s->tsv.len+1);	/* include trailing '\0' */
  DumpVar(size,D);
  DumpBlock(getstr(s),(size_t)size,D);
 }
}
```

生成补丁：

```bash
cd <scratch> && diff -ruN a/src b/src | sed 's|^--- a/|--- lua-5.1/|; s|^+++ b/|+++ lua-5.1/|' \
  > /root/pyluadec-refactor/native/patches/0001-serial-sizet.patch
```

（补丁路径前缀设计为在"含 src/ 的目录"内以 `-p1` 应用——见 Task 4 的 `patch -p1 -d`。生成后人工核对 hunks 只覆盖上述 4 处。）

- [ ] **Step 2: 写补丁可应用性测试**

`tests/test_patch.py`：

```python
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_patch_applies_cleanly(tmp_path):
    shutil.copytree(ROOT / "vendor" / "lua-5.1" / "src", tmp_path / "src")
    r = subprocess.run(
        ["patch", "-p1", "-d", str(tmp_path), "-i",
         str(ROOT / "native" / "patches" / "0001-serial-sizet.patch")],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    patched = (tmp_path / "src" / "lundump.h").read_text()
    assert "lua_SerialSizet" in patched
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_patch.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: serialization-width patch (lua_SerialSizet) for lua undump/dump"
```

---

### Task 4: CMake 双字长构建

**Files:**
- Create: `CMakeLists.txt`, `native/CMakeLists.txt`（本 Task 只建 lua 目标，bridge 目标 Task 5 加）, `scripts/build_native.sh`
- Test: `tests/test_build_artifacts.py`

**Interfaces:**
- Produces: `build/lua_sz4`、`build/luac_sz4`、`build/lua_sz8`、`build/luac_sz8` 四个二进制；静态库目标 `lua_sz4`/`lua_sz8`（PIC，供 Task 5 链接）；CMake 变量 `LUA_PATCHED_SRC`。

- [ ] **Step 1: 写顶层 `CMakeLists.txt`**

```cmake
cmake_minimum_required(VERSION 3.24)
project(pyluadec_native LANGUAGES C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ---- apply serialization-width patch into build dir (vendor stays pristine)
set(LUA_PRISTINE ${CMAKE_SOURCE_DIR}/vendor/lua-5.1)
set(LUA_PATCHED ${CMAKE_BINARY_DIR}/lua-5.1-patched)
set(LUA_PATCHED_SRC ${LUA_PATCHED}/src)
file(REMOVE_RECURSE ${LUA_PATCHED})
file(MAKE_DIRECTORY ${LUA_PATCHED})
file(COPY ${LUA_PRISTINE}/src DESTINATION ${LUA_PATCHED})
execute_process(
  COMMAND patch -p1 -d ${LUA_PATCHED} -i ${CMAKE_SOURCE_DIR}/native/patches/0001-serial-sizet.patch
  RESULT_VARIABLE PATCH_RV OUTPUT_VARIABLE PATCH_OUT ERROR_VARIABLE PATCH_ERR)
if(NOT PATCH_RV EQUAL 0)
  message(FATAL_ERROR "lua patch failed: ${PATCH_OUT} ${PATCH_ERR}")
endif()

set(LUA_CORE_FILES
  lapi.c lcode.c ldebug.c ldo.c ldump.c lfunc.c lgc.c llex.c lmem.c
  lobject.c lopcodes.c lparser.c lstate.c lstring.c ltable.c ltm.c
  lundump.c lvm.c lzio.c
  lauxlib.c lbaselib.c ldblib.c liolib.c lmathlib.c loslib.c ltablib.c
  lstrlib.c loadlib.c linit.c)

function(add_lua_variant SUFFIX SERIAL_TYPE)
  set(srcs "")
  foreach(f ${LUA_CORE_FILES})
    list(APPEND srcs ${LUA_PATCHED_SRC}/${f})
  endforeach()
  add_library(lua_${SUFFIX} STATIC ${srcs})
  target_include_directories(lua_${SUFFIX} PUBLIC ${LUA_PATCHED_SRC})
  target_compile_definitions(lua_${SUFFIX}
    PUBLIC LUAC_SERIAL_SIZET=${SERIAL_TYPE}
    PRIVATE LUA_USE_POSIX LUA_COMPAT_ALL)

  add_executable(lua_${SUFFIX}_bin ${LUA_PATCHED_SRC}/lua.c)
  set_target_properties(lua_${SUFFIX}_bin PROPERTIES OUTPUT_NAME lua_${SUFFIX}
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
  target_link_libraries(lua_${SUFFIX}_bin PRIVATE lua_${SUFFIX} $<$<PLATFORM_ID:Linux>:m>)

  add_executable(luac_${SUFFIX}_bin ${LUA_PATCHED_SRC}/luac.c ${LUA_PATCHED_SRC}/print.c)
  set_target_properties(luac_${SUFFIX}_bin PROPERTIES OUTPUT_NAME luac_${SUFFIX}
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
  target_link_libraries(luac_${SUFFIX}_bin PRIVATE lua_${SUFFIX} $<$<PLATFORM_ID:Linux>:m>)
endfunction()

add_lua_variant(sz4 uint32_t)
add_lua_variant(sz8 uint64_t)

add_subdirectory(native)
```

`native/CMakeLists.txt`（本 Task 先留空壳）：

```cmake
# bridge modules added in Task 5
```

`scripts/build_native.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -Dpybind11_DIR="$(uv run python -m pybind11 --cmakedir)"
cmake --build build -j"$(nproc 2>/dev/null || sysctl -n hw.ncpu)"
```

`chmod +x scripts/build_native.sh`

- [ ] **Step 2: 写构建产物测试（header 字节 + 交叉执行）**

`tests/test_build_artifacts.py`：

```python
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"

def _compile(luac: Path, src: str, tmp: Path) -> bytes:
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src)
    subprocess.run([str(luac), "-o", str(o), str(s)], check=True)
    return o.read_bytes()

def test_sz4_header_byte(tmp_path):
    blob = _compile(BUILD / "luac_sz4", "return 1", tmp_path)
    assert blob[:4] == b"\x1bLua" and blob[4] == 0x51
    assert blob[8] == 4          # sizeof(serialized size_t)

def test_sz8_header_byte(tmp_path):
    blob = _compile(BUILD / "luac_sz8", "return 1", tmp_path)
    assert blob[8] == 8

def test_sz4_lua_runs_sz4_bytecode(tmp_path):
    s = tmp_path / "p.lua"; o = tmp_path / "p.out"
    s.write_text('print("ok")')
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    r = subprocess.run([str(BUILD / "lua_sz4"), str(o)], capture_output=True, text=True, check=True)
    assert r.stdout.strip() == "ok"
```

- [ ] **Step 3: 构建并运行测试**

Run: `./scripts/build_native.sh && uv run pytest tests/test_build_artifacts.py -v`
Expected: 3 PASS（当前 32 位环境同样满足：sz4=uint32_t、sz8=uint64_t 与宿主无关）

- [ ] **Step 4: 用真实语料抽查 sz4 加载**

```bash
BUILD=build; C=${PYLUADEC_CORPUS_DIR:-/root/pyluadec/others/script_to_decompile}
$BUILD/luac_sz4 -l "$C/snr_crd_1.lua" | head -5
```

Expected: 正常打印反汇编（说明 sz4 undump 接受 PSP 字节码）。

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: dual serialization-width lua builds (sz4/sz8) via CMake"
```

---

### Task 5: pybind bridge 双模块

**Files:**
- Create: `native/bridge_impl.hpp`, `native/bridge_sz4.cpp`, `native/bridge_sz8.cpp`
- Modify: `native/CMakeLists.txt`
- Test: `tests/test_bridge.py`

**Interfaces:**
- Produces: Python 模块 `pyluadec._native._bridge_sz4` / `_bridge_sz8`，各含：
  - `load_bytecode(blob: bytes, chunkname: str) -> dict`（proto 字典，字段见下）
  - `serial_sizet_width() -> int`（4 或 8）
- proto 字典字段：`source: bytes|None`、`linedefined/lastlinedefined/nups/numparams/is_vararg/maxstacksize: int`、`code: list[int]`（原始 32 位指令字）、`constants: list[None|bool|dict|bytes]`（number 为 `{"type":"number","value":float,"payload":bytes8}`）、`lineinfo: list[int]`、`locvars: list[dict(name:bytes,startpc:int,endpc:int)]`、`upvalues: list[bytes]`、`subprotos: list[dict]`。

- [ ] **Step 1: 写 `native/bridge_impl.hpp`**

```cpp
#pragma once
#include <pybind11/pybind11.h>
#include <memory>
#include <stdexcept>
#include <string>

extern "C" {
#include "lua.h"
#include "lauxlib.h"
#include "lobject.h"
#include "lstate.h"
#include "lundump.h"
}

namespace py = pybind11;

namespace pyluadec_bridge {

inline py::bytes tstring_to_bytes(const TString* ts) {
  return py::bytes(getstr(ts), ts->tsv.len);
}

inline py::object const_to_py(const TValue* o) {
  switch (ttype(o)) {
    case LUA_TNIL: return py::none();
    case LUA_TBOOLEAN: return py::bool_(bvalue(o) != 0);
    case LUA_TNUMBER: {
      lua_Number n = nvalue(o);
      py::dict d;
      d["type"] = "number";
      d["value"] = py::float_(static_cast<double>(n));
      d["payload"] = py::bytes(reinterpret_cast<const char*>(&n), sizeof n);
      return d;
    }
    case LUA_TSTRING: return tstring_to_bytes(rawtsvalue(o));
    default: throw std::runtime_error("unexpected constant type " + std::to_string(ttype(o)));
  }
}

inline py::dict proto_to_dict(const Proto* p) {
  py::dict d;
  d["source"] = p->source ? py::object(tstring_to_bytes(p->source)) : py::object(py::none());
  d["linedefined"] = p->linedefined;
  d["lastlinedefined"] = p->lastlinedefined;
  d["nups"] = static_cast<int>(p->nups);
  d["numparams"] = static_cast<int>(p->numparams);
  d["is_vararg"] = static_cast<int>(p->is_vararg);   // raw flags, not flattened
  d["maxstacksize"] = static_cast<int>(p->maxstacksize);

  py::list code;
  for (int i = 0; i < p->sizecode; i++)
    code.append(py::int_(static_cast<unsigned long long>(p->code[i])));
  d["code"] = code;

  py::list consts;
  for (int i = 0; i < p->sizek; i++) consts.append(const_to_py(&p->k[i]));
  d["constants"] = consts;

  py::list lineinfo;
  for (int i = 0; i < p->sizelineinfo; i++) lineinfo.append(p->lineinfo[i]);
  d["lineinfo"] = lineinfo;

  py::list locvars;
  for (int i = 0; i < p->sizelocvars; i++) {
    py::dict lv;
    lv["name"] = p->locvars[i].varname
                     ? py::object(tstring_to_bytes(p->locvars[i].varname))
                     : py::object(py::none());
    lv["startpc"] = p->locvars[i].startpc;
    lv["endpc"] = p->locvars[i].endpc;
    locvars.append(lv);
  }
  d["locvars"] = locvars;

  py::list upvalues;
  for (int i = 0; i < p->sizeupvalues; i++)
    upvalues.append(p->upvalues[i] ? py::object(tstring_to_bytes(p->upvalues[i]))
                                   : py::object(py::none()));
  d["upvalues"] = upvalues;

  py::list subs;
  for (int i = 0; i < p->sizep; i++) subs.append(proto_to_dict(p->p[i]));
  d["subprotos"] = subs;
  return d;
}

struct LuaCloser { void operator()(lua_State* L) const { if (L) lua_close(L); } };

inline py::dict load_bytecode(py::bytes blob, const std::string& chunkname) {
  std::string data = blob;   // copy; py::bytes -> std::string keeps embedded NULs
  std::unique_ptr<lua_State, LuaCloser> L(luaL_newstate());
  if (!L) throw std::runtime_error("luaL_newstate failed");
  int st = luaL_loadbuffer(L.get(), data.data(), data.size(), chunkname.c_str());
  if (st != 0) {
    const char* msg = lua_tostring(L.get(), -1);
    throw std::runtime_error(std::string("load failed (") + std::to_string(st) + "): " +
                             (msg ? msg : "?"));
  }
  const Closure* cl = static_cast<const Closure*>(lua_topointer(L.get(), -1));
  if (!cl || cl->l.isC) throw std::runtime_error("loaded chunk is not a Lua closure");
  return proto_to_dict(cl->l.p);
}

inline void register_bridge(py::module_& m) {
  m.def("load_bytecode", &load_bytecode, py::arg("blob"), py::arg("chunkname") = "=chunk");
  m.def("serial_sizet_width", [] { return static_cast<int>(sizeof(lua_SerialSizet)); });
}

}  // namespace pyluadec_bridge
```

`native/bridge_sz4.cpp`：

```cpp
#include "bridge_impl.hpp"
PYBIND11_MODULE(_bridge_sz4, m) { pyluadec_bridge::register_bridge(m); }
```

`native/bridge_sz8.cpp`：

```cpp
#include "bridge_impl.hpp"
PYBIND11_MODULE(_bridge_sz8, m) { pyluadec_bridge::register_bridge(m); }
```

- [ ] **Step 2: 更新 `native/CMakeLists.txt`**

```cmake
find_package(pybind11 CONFIG REQUIRED)

function(add_bridge SUFFIX)
  pybind11_add_module(_bridge_${SUFFIX} bridge_${SUFFIX}.cpp)
  target_link_libraries(_bridge_${SUFFIX} PRIVATE lua_${SUFFIX})
  set_target_properties(_bridge_${SUFFIX} PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/pyluadec/_native)
endfunction()

add_bridge(sz4)
add_bridge(sz8)
```

- [ ] **Step 3: 写 bridge 测试**

`tests/test_bridge.py`：

```python
import struct, subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"

def _compile(luac, src, tmp):
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src, encoding="utf-8")
    subprocess.run([str(BUILD / luac), "-o", str(o), str(s)], check=True)
    return o.read_bytes()

SRC = 'local answer = 42.5\nlocal name = "ab\\255cd"\nprint(name, answer)\n'

def test_sz4_bridge_full_fields(tmp_path):
    from pyluadec._native import _bridge_sz4 as b
    assert b.serial_sizet_width() == 4
    p = b.load_bytecode(_compile("luac_sz4", SRC, tmp_path))
    assert p["numparams"] == 0 and p["maxstacksize"] > 0
    assert p["lineinfo"] and p["locvars"]
    assert p["locvars"][0]["name"] == b"answer"
    nums = [c for c in p["constants"] if isinstance(c, dict)]
    assert nums and nums[0]["payload"] == struct.pack("<d", 42.5)
    strs = [c for c in p["constants"] if isinstance(c, bytes)]
    assert b"ab\xffcd" in strs          # non-UTF-8 bytes survive losslessly

def test_sz8_bridge_roundtrip_width(tmp_path):
    from pyluadec._native import _bridge_sz8 as b
    assert b.serial_sizet_width() == 8
    p = b.load_bytecode(_compile("luac_sz8", SRC, tmp_path))
    assert len(p["code"]) > 0

def test_sz4_bridge_loads_real_corpus_file(corpus_dir):
    from pyluadec._native import _bridge_sz4 as b
    p = b.load_bytecode((corpus_dir / "snr_crd_1.lua").read_bytes())
    assert p["subprotos"] or p["code"]
```

- [ ] **Step 4: 构建 + 运行测试**

Run: `./scripts/build_native.sh && PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile uv run pytest tests/test_bridge.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: dual-width pybind bridge with lossless proto export"
```

---

### Task 6: ingest 派发层与 Proto 数据类

**Files:**
- Create: `src/pyluadec/ingest/__init__.py`, `src/pyluadec/ingest/header.py`, `src/pyluadec/ingest/proto.py`, `src/pyluadec/ingest/dispatch.py`
- Test: `tests/test_ingest.py`

**Interfaces:**
- Consumes: Task 5 的 `_bridge_sz4/_bridge_sz8.load_bytecode`。
- Produces:
  - `pyluadec.ingest.header.Header`（frozen dataclass：`version:int, fmt:int, little_endian:bool, sizeof_int:int, sizeof_sizet:int, sizeof_instr:int, sizeof_number:int, integral:bool`）与 `parse_header(blob: bytes) -> Header`
  - `pyluadec.ingest.proto.Proto / LuaNumber / LocVar`（frozen dataclass；字段同 bridge dict，constants 为 `None|bool|LuaNumber|bytes`）
  - `pyluadec.ingest.load_bytes(blob: bytes, chunkname: str = "=chunk") -> Proto`、`load_file(path) -> Proto`
  - `pyluadec.ingest.proto.to_canonical(p: Proto) -> dict`（bytes→hex、LuaNumber→payload hex，JSON 可序列化、键序稳定）

- [ ] **Step 1: 写失败测试**

`tests/test_ingest.py`：

```python
import json, subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"

def _compile(luac, src, tmp):
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src)
    subprocess.run([str(BUILD / luac), "-o", str(o), str(s)], check=True)
    return o

def test_parse_header_sz4(tmp_path):
    from pyluadec.ingest.header import parse_header
    h = parse_header(_compile("luac_sz4", "return 1", tmp_path).read_bytes())
    assert h.version == 0x51 and h.sizeof_sizet == 4 and h.little_endian

def test_dispatch_by_header(tmp_path):
    from pyluadec.ingest import load_file
    p4 = load_file(_compile("luac_sz4", "local x=1 return x", tmp_path))
    assert p4.maxstacksize >= 2 and p4.locvars[0].name == b"x"
    p8 = load_file(_compile("luac_sz8", "local x=1 return x", tmp_path))
    assert p8.code == p4.code            # 同源同指令流，与序列化宽度无关

def test_canonical_dump_is_json_and_stable(tmp_path):
    from pyluadec.ingest import load_file
    from pyluadec.ingest.proto import to_canonical
    p = load_file(_compile("luac_sz4", 'return "\\255", 0.5', tmp_path))
    c1 = json.dumps(to_canonical(p), sort_keys=True)
    c2 = json.dumps(to_canonical(load_file(_compile("luac_sz4", 'return "\\255", 0.5', tmp_path))), sort_keys=True)
    assert c1 == c2
    assert "ff" in c1                    # bytes as hex
```

Run: `uv run pytest tests/test_ingest.py -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 2: 实现**

`src/pyluadec/ingest/header.py`：

```python
from dataclasses import dataclass

SIGNATURE = b"\x1bLua"

@dataclass(frozen=True)
class Header:
    version: int
    fmt: int
    little_endian: bool
    sizeof_int: int
    sizeof_sizet: int
    sizeof_instr: int
    sizeof_number: int
    integral: bool

class BadHeader(ValueError):
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
    return h
```

`src/pyluadec/ingest/proto.py`：

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LuaNumber:
    value: float
    payload: bytes          # 8 raw bytes, bit-exact

Const = None | bool | LuaNumber | bytes

@dataclass(frozen=True)
class LocVar:
    name: bytes | None
    startpc: int
    endpc: int

@dataclass(frozen=True)
class Proto:
    source: bytes | None
    linedefined: int
    lastlinedefined: int
    nups: int
    numparams: int
    is_vararg: int          # raw flag byte (HASARG|ISVARARG|NEEDSARG)
    maxstacksize: int
    code: tuple[int, ...]
    constants: tuple[Const, ...]
    lineinfo: tuple[int, ...]
    locvars: tuple[LocVar, ...]
    upvalues: tuple[bytes | None, ...]
    subprotos: tuple["Proto", ...]

def from_bridge_dict(d: dict) -> Proto:
    def conv_const(c):
        if isinstance(c, dict):
            return LuaNumber(value=c["value"], payload=c["payload"])
        return c
    return Proto(
        source=d["source"],
        linedefined=d["linedefined"], lastlinedefined=d["lastlinedefined"],
        nups=d["nups"], numparams=d["numparams"], is_vararg=d["is_vararg"],
        maxstacksize=d["maxstacksize"],
        code=tuple(d["code"]),
        constants=tuple(conv_const(c) for c in d["constants"]),
        lineinfo=tuple(d["lineinfo"]),
        locvars=tuple(LocVar(v["name"], v["startpc"], v["endpc"]) for v in d["locvars"]),
        upvalues=tuple(d["upvalues"]),
        subprotos=tuple(from_bridge_dict(s) for s in d["subprotos"]),
    )

def to_canonical(p: Proto) -> dict:
    def conv_const(c):
        if c is None:
            return {"t": "nil"}
        if isinstance(c, bool):
            return {"t": "bool", "v": c}
        if isinstance(c, LuaNumber):
            return {"t": "num", "payload": c.payload.hex()}
        return {"t": "str", "v": c.hex()}
    return {
        "source": p.source.hex() if p.source is not None else None,
        "linedefined": p.linedefined, "lastlinedefined": p.lastlinedefined,
        "nups": p.nups, "numparams": p.numparams, "is_vararg": p.is_vararg,
        "maxstacksize": p.maxstacksize,
        "code": list(p.code),
        "constants": [conv_const(c) for c in p.constants],
        "lineinfo": list(p.lineinfo),
        "locvars": [{"name": v.name.hex() if v.name is not None else None,
                     "startpc": v.startpc, "endpc": v.endpc} for v in p.locvars],
        "upvalues": [u.hex() if u is not None else None for u in p.upvalues],
        "subprotos": [to_canonical(s) for s in p.subprotos],
    }
```

`src/pyluadec/ingest/dispatch.py`：

```python
from pathlib import Path
from .header import parse_header
from .proto import Proto, from_bridge_dict

def _bridge_for(sizeof_sizet: int):
    if sizeof_sizet == 4:
        from pyluadec._native import _bridge_sz4 as b
    elif sizeof_sizet == 8:
        from pyluadec._native import _bridge_sz8 as b
    else:
        raise ValueError(f"unsupported serialized size_t width {sizeof_sizet}")
    return b

def load_bytes(blob: bytes, chunkname: str = "=chunk") -> Proto:
    h = parse_header(blob)
    return from_bridge_dict(_bridge_for(h.sizeof_sizet).load_bytecode(blob, chunkname))

def load_file(path) -> Proto:
    p = Path(path)
    return load_bytes(p.read_bytes(), chunkname="@" + p.name)
```

`src/pyluadec/ingest/__init__.py`：

```python
from .dispatch import load_bytes, load_file
from .header import Header, parse_header, BadHeader
from .proto import Proto, LuaNumber, LocVar, from_bridge_dict, to_canonical

__all__ = ["load_bytes", "load_file", "Header", "parse_header", "BadHeader",
           "Proto", "LuaNumber", "LocVar", "from_bridge_dict", "to_canonical"]
```

- [ ] **Step 3: 运行测试**

Run: `uv run pytest tests/test_ingest.py -v`
Expected: 3 PASS

- [ ] **Step 4: 全语料冒烟（无断言脚本，确认 229 文件全部可加载）**

```bash
PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile uv run python - <<'PY'
import os, pathlib
from pyluadec.ingest import load_file
c = pathlib.Path(os.environ["PYLUADEC_CORPUS_DIR"])
files = sorted(c.glob("*.lua")); n_ok = 0
for f in files:
    load_file(f); n_ok += 1
print(f"loaded {n_ok}/{len(files)}")
PY
```

Expected: `loaded 229/229`

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: header-dispatched ingest layer with immutable Proto dataclasses"
```

---

### Task 7: golden 固化（迁移 Step 0）

**Files:**
- Create: `scripts/capture_golden.py`, `corpus/golden/manifest.json`, `corpus/golden/proto_dump/*.json.gz`, `corpus/golden/listing/*.txt`
- Test: `tests/test_golden.py`

**Interfaces:**
- Consumes: 旧项目工具（`lua51_proto_extractor`、旧 `luac`），仅本 Task 使用。
- Produces: `corpus/golden/` 只读档案：`manifest.json`（`{filename: {"sha256": .., "size": ..}}`）、`proto_dump/<name>.json.gz`（旧 bridge 的 proto dict 原样 JSON）、`listing/<name>.txt`（旧 luac `-l -l` 输出）。

- [ ] **Step 1: 写 `scripts/capture_golden.py`**

```python
"""Capture golden baseline from the OLD project's tools. Run ONCE on the 32-bit env:

  PYTHONPATH=/root/pyluadec/cmake-build-debug/native_bridge \
  PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile \
  PYLUADEC_OLD_LUAC=/root/pyluadec/cmake-build-debug/lua-5.1/luac \
  python3 scripts/capture_golden.py

Golden derives ONLY from original bytecode + old tools; it is never regenerated
by new tools (spec §6 R5).
"""
import gzip, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "corpus" / "golden"

def main() -> int:
    import lua51_proto_extractor as old  # old bridge, 32-bit only
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    old_luac = os.environ["PYLUADEC_OLD_LUAC"]
    (GOLDEN / "proto_dump").mkdir(parents=True, exist_ok=True)
    (GOLDEN / "listing").mkdir(parents=True, exist_ok=True)
    manifest = {}
    files = sorted(corpus.glob("*.lua"))
    for f in files:
        blob = f.read_bytes()
        manifest[f.name] = {"sha256": hashlib.sha256(blob).hexdigest(), "size": len(blob)}
        dump = old.load_proto(str(f))
        with gzip.open(GOLDEN / "proto_dump" / (f.name + ".json.gz"), "wt", encoding="utf-8") as fh:
            json.dump(dump, fh, ensure_ascii=False, sort_keys=True)
        listing = subprocess.run([old_luac, "-l", "-l", str(f)],
                                 capture_output=True, text=True, check=True).stdout
        (GOLDEN / "listing" / (f.name + ".txt")).write_text(listing, encoding="utf-8")
    (GOLDEN / "manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(f"captured {len(files)} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 在 32 位环境执行捕获（一次性）**

按脚本 docstring 中的命令执行。
Expected: `captured 229`；`corpus/golden/` 下 229×2 文件 + manifest。

- [ ] **Step 3: 写 golden 完整性测试**

`tests/test_golden.py`：

```python
import json
from pathlib import Path

GOLDEN = Path(__file__).resolve().parents[1] / "corpus" / "golden"

def test_golden_complete():
    manifest = json.loads((GOLDEN / "manifest.json").read_text())
    assert len(manifest) == 229
    for name in manifest:
        assert (GOLDEN / "proto_dump" / (name + ".json.gz")).exists()
        assert (GOLDEN / "listing" / (name + ".txt")).exists()

def test_golden_matches_corpus_hashes(corpus_dir):
    import hashlib
    manifest = json.loads((GOLDEN / "manifest.json").read_text())
    for name, meta in manifest.items():
        blob = (corpus_dir / name).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == meta["sha256"], name
```

Run: `PYLUADEC_CORPUS_DIR=... uv run pytest tests/test_golden.py -v`
Expected: 2 PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: golden baseline captured from old bridge and luac listings (read-only)"
```

---

### Task 8: 新旧 parity 比对（迁移 Step 1）

**Files:**
- Create: `scripts/compare_bridge_golden.py`
- Test: `tests/test_parity.py`

**Interfaces:**
- Consumes: Task 6 `load_file`/`Proto`；Task 7 golden。
- Produces: `compare_file(name, corpus_dir) -> list[dict]`（差异记录）；CLI 全语料运行输出 `corpus/golden/discrepancies.json`。

**比对规则**（旧 bridge 有已知缺陷，映射如下）：
- `code`：旧 dump 每指令 dict 的 `raw_instr` 序列 == 新 `Proto.code`（逐字相等，最强信号）。
- `constants`：旧 float == 新 `LuaNumber.value`；旧 str == 新 bytes 按 UTF-8 解码（解码失败记 discrepancy）；bool/None 直等。
- `numparams` 直等；`is_vararg`：旧 bool == `bool(新 & 1)`（旧只导出 HASARG 位）。
- `upvalues`：旧 str|None == 新 bytes 解码。
- `subprotos` 递归，树形状必须一致。
- `lineinfo`：旧 bridge 不导出 → 与 listing 交叉验证：解析 listing 中每条指令行 `\t<n>\t[<line>]\t<OPNAME>` 的 line 序列 == 新 `Proto.lineinfo`；同时 listing 各函数头的 `(<N> instructions` == `len(code)`。

- [ ] **Step 1: 写失败测试**

`tests/test_parity.py`：

```python
import json
from pathlib import Path

def test_single_file_parity(corpus_dir):
    from scripts.compare_bridge_golden import compare_file
    assert compare_file("snr_crd_1.lua", corpus_dir) == []

def test_full_corpus_parity(corpus_dir):
    from scripts.compare_bridge_golden import compare_corpus
    report = compare_corpus(corpus_dir)
    unexpected = [d for d in report if d["verdict"] == "unexpected"]
    assert unexpected == [], f"{len(unexpected)} unexpected discrepancies"
```

（`scripts/` 需可导入：创建空 `scripts/__init__.py` **并**在仓库根创建空 `conftest.py`——pytest 加载根级 conftest 时会把仓库根目录放进 `sys.path`，`scripts` 包因此可导入；`tests/conftest.py` 的 fixture 不受影响。）

Run: `uv run pytest tests/test_parity.py -v`
Expected: FAIL（模块不存在）

- [ ] **Step 2: 实现 `scripts/compare_bridge_golden.py`**

```python
"""Compare new ingest layer against golden (old bridge dump + luac listings)."""
import gzip, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "corpus" / "golden"
LISTING_INSTR_RE = re.compile(r"^\t\d+\t\[(\d+)\]\t")

def _diff(path, field, old, new, verdict="unexpected"):
    return {"proto_path": path, "field": field,
            "old": repr(old), "new": repr(new), "verdict": verdict}

def _cmp_proto(old: dict, new, path: str, out: list):
    raw_old = [ins["raw_instr"] for ins in old["code"]]
    if list(new.code) != raw_old:
        out.append(_diff(path, "code", raw_old, list(new.code)))
    if old["numparams"] != new.numparams:
        out.append(_diff(path, "numparams", old["numparams"], new.numparams))
    if bool(old["is_vararg"]) != bool(new.is_vararg & 1):
        out.append(_diff(path, "is_vararg", old["is_vararg"], new.is_vararg))
    if len(old["constants"]) != len(new.constants):
        out.append(_diff(path, "constants.len", len(old["constants"]), len(new.constants)))
    else:
        from pyluadec.ingest.proto import LuaNumber
        for i, (oc, nc) in enumerate(zip(old["constants"], new.constants)):
            if isinstance(nc, LuaNumber):
                ok = isinstance(oc, (int, float)) and not isinstance(oc, bool) and float(oc) == nc.value
            elif isinstance(nc, bytes):
                try:
                    ok = oc == nc.decode("utf-8")
                except UnicodeDecodeError:
                    out.append(_diff(f"{path}/k{i}", "const.encoding", oc, nc, "expected"))
                    continue
            else:
                ok = oc == nc
            if not ok:
                out.append(_diff(f"{path}/k{i}", "const", oc, nc))
    old_ups = old["upvalues"]
    new_ups = [u.decode("utf-8", "replace") if u is not None else None for u in new.upvalues]
    if old_ups != new_ups:
        out.append(_diff(path, "upvalues", old_ups, new_ups))
    if len(old["subprotos"]) != len(new.subprotos):
        out.append(_diff(path, "subprotos.len", len(old["subprotos"]), len(new.subprotos)))
    else:
        for i, (os_, ns) in enumerate(zip(old["subprotos"], new.subprotos)):
            _cmp_proto(os_, ns, f"{path}/{i}", out)

def _listing_lineinfo(listing: str) -> list[list[int]]:
    """Per-function instruction line numbers, in listing order (main first)."""
    funcs, cur = [], None
    for line in listing.splitlines():
        if line.startswith(("main <", "function <")):
            cur = []
            funcs.append(cur)
        else:
            m = LISTING_INSTR_RE.match(line)
            if m and cur is not None:
                cur.append(int(m.group(1)))
    return funcs

def _flatten(p):
    yield p
    for s in p.subprotos:
        yield from _flatten(s)

def compare_file(name: str, corpus_dir: Path) -> list:
    from pyluadec.ingest import load_file
    new = load_file(Path(corpus_dir) / name)
    with gzip.open(GOLDEN / "proto_dump" / (name + ".json.gz"), "rt", encoding="utf-8") as fh:
        old = json.load(fh)
    out: list = []
    _cmp_proto(old, new, name, out)
    listing = (GOLDEN / "listing" / (name + ".txt")).read_text(encoding="utf-8")
    listed = _listing_lineinfo(listing)
    protos = list(_flatten(new))
    if len(listed) != len(protos):
        out.append(_diff(name, "listing.func_count", len(listed), len(protos)))
    else:
        for i, (lines, proto) in enumerate(zip(listed, protos)):
            if lines != list(proto.lineinfo):
                out.append(_diff(f"{name}#func{i}", "lineinfo", lines[:8], list(proto.lineinfo)[:8]))
    return out

def compare_corpus(corpus_dir: Path) -> list:
    manifest = json.loads((GOLDEN / "manifest.json").read_text())
    report = []
    for name in sorted(manifest):
        report.extend(compare_file(name, Path(corpus_dir)))
    return report

if __name__ == "__main__":
    import os
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    report = compare_corpus(corpus)
    outp = GOLDEN / "discrepancies.json"
    outp.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    unexpected = [d for d in report if d["verdict"] == "unexpected"]
    print(f"{len(report)} discrepancies ({len(unexpected)} unexpected) -> {outp}")
    sys.exit(1 if unexpected else 0)
```

**注意**：listing 遍历顺序（旧 luac 打印顺序为 main 后接各嵌套函数的深度优先前序）与 `_flatten` 的前序一致；若首跑发现顺序不匹配（表现为大量 `lineinfo` 差异但 `code` 全对），先人工核对一个小文件的 listing 结构再修正 `_flatten` 或 `_listing_lineinfo`，不要放宽比较。

- [ ] **Step 3: 运行测试与全语料比对**

Run:
```bash
PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile uv run pytest tests/test_parity.py -v
PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile uv run python scripts/compare_bridge_golden.py
```
Expected: 测试 PASS；`0 unexpected`，`discrepancies.json` 中仅 `expected` 类（非 UTF-8 常量等，若有）。若出现 unexpected：逐条核实是新摄入层 bug 还是旧 bridge 缺陷，前者修复、后者在 discrepancies.json 中人工改判为 `expected` 并在 commit message 说明理由。

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: bridge-vs-golden parity comparator; corpus parity clean"
```

---

### Task 9: sz4 roundtrip 门（迁移 Step 2 之门②，先在 32 位预跑）

**Files:**
- Create: `scripts/roundtrip_sz4.py`
- Test: `tests/test_roundtrip.py`

**Interfaces:**
- Consumes: Task 4 的 `build/luac_sz4`。
- Produces: `roundtrip_file(luac: Path, f: Path, tmp: Path) -> bool`；CLI 全语料运行。

- [ ] **Step 1: 写失败测试**

`tests/test_roundtrip.py`：

```python
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"

def test_corpus_roundtrip_byte_identical(corpus_dir, tmp_path):
    from scripts.roundtrip_sz4 import roundtrip_file
    bad = [f.name for f in sorted(corpus_dir.glob("*.lua"))
           if not roundtrip_file(BUILD / "luac_sz4", f, tmp_path)]
    assert bad == []
```

Run: `uv run pytest tests/test_roundtrip.py -v` → FAIL（模块不存在）

- [ ] **Step 2: 实现 `scripts/roundtrip_sz4.py`**

```python
"""Load->redump roundtrip: luac_sz4 must reproduce each corpus file byte-identically."""
import os, subprocess, sys, tempfile
from pathlib import Path

def roundtrip_file(luac: Path, f: Path, tmpdir: Path) -> bool:
    out = Path(tmpdir) / (f.name + ".rt")
    subprocess.run([str(luac), "-o", str(out), str(f)], check=True, capture_output=True)
    return out.read_bytes() == f.read_bytes()

if __name__ == "__main__":
    luac = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/luac_sz4")
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    with tempfile.TemporaryDirectory() as td:
        bad = [f.name for f in sorted(corpus.glob("*.lua"))
               if not roundtrip_file(luac, f, Path(td))]
    print(f"roundtrip: {'OK all' if not bad else 'FAIL ' + str(bad)}")
    sys.exit(1 if bad else 0)
```

- [ ] **Step 3: 运行**

Run: `PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile uv run pytest tests/test_roundtrip.py -v`
Expected: PASS（229/229 字节一致）。若个别文件不一致：用 `cmp -l` 定位首个差异字节、对照 listing 判断是 debug 段还是常量编码问题，记录后再修——这是"发现即阻塞"级问题，不许跳过。

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: sz4 load-redump roundtrip gate, corpus byte-identical"
```

---

### Task 10: 迁移一键验证与 runbook（M1）

**Files:**
- Create: `scripts/verify_migration.sh`, `docs/runbooks/64bit-migration.md`
- Modify: `CLAUDE.md`（回填本仓库构建/测试命令）

**Interfaces:**
- Consumes: Tasks 4-9 全部脚本。
- Produces: 单命令迁移验证；64 位新机开荒 runbook。

- [ ] **Step 1: 写 `scripts/verify_migration.sh`**

```bash
#!/usr/bin/env bash
# Migration gates (spec §6 Step 2). Run on any host; passing on a 64-bit host = M1 complete.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${PYLUADEC_CORPUS_DIR:?set PYLUADEC_CORPUS_DIR to the 229-file corpus}"

echo "== gate 1: build all artifacts =="
./scripts/build_native.sh

echo "== gate 2: sz4 load->redump byte-identical over corpus =="
uv run python scripts/roundtrip_sz4.py build/luac_sz4

echo "== gate 3: ingest parity vs golden =="
uv run python scripts/compare_bridge_golden.py

echo "== full test suite =="
uv run pytest -v

echo "ALL MIGRATION GATES PASSED on $(uname -m) / $(uname -s)"
```

`chmod +x scripts/verify_migration.sh`

- [ ] **Step 2: 写 `docs/runbooks/64bit-migration.md`**

内容（全文写入，不留提纲）：新机（Linux x86_64 / macOS arm64）前置依赖清单（git、cmake ≥3.24、C/C++ 编译器、uv、patch）；语料拷贝方式（`others/script_to_decompile` 整目录 → 任意路径，`export PYLUADEC_CORPUS_DIR=<路径>`）；执行 `git clone` 本仓库 → `uv sync` → `./scripts/verify_migration.sh`；三道门与 spec §6 的对应关系；**双平台要求**（Linux x86_64 与 macOS arm64 都必须全绿才算 M1 完成，防隐性平台假设）；门未过时的分诊指引（gate 2 失败 → `cmp -l` 首差异字节 + 对照 golden listing；gate 3 失败 → 读 `corpus/golden/discrepancies.json` 的 unexpected 条目）；32 位环境自此仅作仲裁复现（保留 `/root/pyluadec` 原样，不再开发）。

- [ ] **Step 3: 在当前 32 位环境全量预跑**

Run: `PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile ./scripts/verify_migration.sh`
Expected: `ALL MIGRATION GATES PASSED on i686/... 或 x86_64/...`（32 位预跑全绿 = M0 出口达成；M1 出口 = 同命令在 64 位机全绿）

- [ ] **Step 4: 回填 CLAUDE.md**

在 CLAUDE.md「本仓库现状」一节替换为实际命令：`uv sync`、`./scripts/build_native.sh`、`uv run pytest`、`./scripts/verify_migration.sh`、`PYLUADEC_CORPUS_DIR` 约定、单测运行方式（`uv run pytest tests/test_x.py::test_y -v`）。

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: one-shot migration verification script and 64-bit runbook"
```

---

## 完成定义

- M0 出口：Task 1-10 在 32 位环境全部完成、`verify_migration.sh` 全绿。
- M1 出口：用户在 64 位环境（Mac mini arm64 与/或 Linux x86_64）按 runbook 执行 `verify_migration.sh` 全绿；两个 64 位平台都绿后在台账/CHANGELOG 记录切换完成，此后开发不再回 32 位。

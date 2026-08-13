"""预测语料（predecessor corpus）读取插件 -- M6 任务 2。

`PYLUADEC_PRED_CORPUS_DIR`（约定值 `/Users/fotile96/Zndnovel/lua_scripts`）不是
字节码，是前身项目（`/root/pyluadec`）的产物：229 个反编译 **Lua 源码**文本文件，
文件名与本项目摄入的 229 个字节码文件（`PYLUADEC_CORPUS_DIR`）一一对应。这批产物
被重编译、打包回 PSP ISO、由人类通关验证过 -- 是本仓库能拿到的、唯一带真人语义
背书的参照。这个模块只做最基础的一步：把源码文本编译回字节码（走
`oracle.compile_source`，与我们自己的产物走同一条编译验证路径），再摄入成
`ingest.proto.Proto`，交给调用方去和原始字节码的 proto 树做结构/语义对比
（`verify.normalize.compare_protos`，本模块不碰）。

工程红线（CLAUDE.md）：字节码派生字符串一律 `bytes`，不解码。这条对预测语料同样
适用 -- 这里只编译/摄入，从不 decode 常量池字符串，也不把语料内容放进任何返回值
之外的地方（没有日志、没有打印）。

不属于 `tests.test_engineering_practice.GUARDED_PACKAGES` 的静态扫描范围：该测试
按包名逐个 `rglob` `ingest/`、`lift/`、`cfg/`、`sir/`、`express/`、`emit/`、
`verify/`、`structure/` 八个子目录，这个文件位于 `src/pyluadec/` 顶层，不在任何
一个子目录下，因此扫描不覆盖它（这不是问题：本模块不需要 `re`，也没有用它）。
"""
from __future__ import annotations

from pathlib import Path

from pyluadec import ingest, oracle
from pyluadec.ingest.proto import Proto
from pyluadec.pipeline import walk_proto_paths


def load_pred_proto(pred_dir: Path, name: str) -> Proto:
    """Compile predecessor source `pred_dir / name` with the oracle and
    ingest the result into a `Proto` tree.

    `name` is the corpus-relative filename (e.g. `"snr_common.lua"`), matched
    against the same basename in the sz4 bytecode corpus. Compilation goes
    through `oracle.compile_source`, process-memoized as of M6 task 1 on
    `(content hash, strip, oracle-binary identity)` -- callers that load the
    same file more than once in a process (e.g. a census walking the whole
    229-file corpus once for the tree comparison and once for anything else)
    pay the `luac_sz4` subprocess cost only the first time.

    Raises `oracle.LuaCompileError` (a subclass of `oracle.OracleError`) if
    the predecessor source does not compile -- this is intentionally NOT
    caught here; the file is source text produced by an entirely different
    project years apart from this one and "it might not compile" is a real,
    reportable outcome, not a bug in this function.
    """
    p = Path(pred_dir) / name
    source = p.read_bytes()
    compiled = oracle.compile_source(source)
    return ingest.load_bytes(compiled, chunkname="@" + name)


def tree_paths(p: Proto) -> list[str]:
    """The `main`/`main_0`/`main_0_1` proto-path convention, as a flat list
    in walk order (pre-order, `enumerate(p.subprotos)` at each level).

    A thin wrapper around `pipeline.walk_proto_paths`, not a reimplementation
    of its `f"{path}_{i}"` spelling: that function's own docstring records
    that spelling as already independently written in three places (itself,
    `structure/fallback.py`'s `CLOSURE` handler, and `fallback.emit_chunk`'s
    walk) and that their agreement is load-bearing -- this module needs the
    same convention only to compare path SETS between two independently
    compiled trees (the original bytecode's and the predecessor source's),
    so it reuses the existing walk instead of adding a fourth spelling.
    """
    out: dict[str, Proto] = {}
    walk_proto_paths("main", p, out)
    return list(out.keys())

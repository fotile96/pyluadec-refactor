"""仓库内 lua/luac oracle 的定位与调用（Phase 1 构建产物）。"""
from __future__ import annotations

import hashlib
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


def _oracle_binary_identity() -> tuple[str, int, int]:
    """`(path, mtime_ns, size)` of the `luac_sz4` a compile would actually
    run, resolved on every call rather than once per process.

    Mirrors `structure.structured._oracle_identity` (that module's docstring
    has the full argument; not reproduced here to keep this one import-free
    of `structure/`). Two channels move the binary underneath a live
    process and a purely content-keyed memo cannot see either: a rebuild in
    place (`./scripts/build_native.sh` rewrites `build/luac_sz4`, moving its
    mtime/size) and `PYLUADEC_BUILD_DIR` (a documented, supported knob read
    by `build_dir()` on every call, so it can swap the binary between two
    `compile_source` calls in one process). Both are exercised as regression
    tests in `tests/test_structured_certify.py` against the higher-level
    certification cache, which is why this module reuses the same
    `(path, mtime_ns, size)` shape rather than a bare content hash: measured
    directly (see task-1-report.md), omitting this component makes
    `test_process_cache_does_not_survive_a_build_dir_swap` fail once
    `compile_source` itself is memoized -- that test's fake refusing `luac`
    would otherwise never run, because the memo would keep answering with
    bytes compiled by the real one before the swap.
    """
    luac = luac_sz4()
    st = luac.stat()
    return (str(luac), st.st_mtime_ns, st.st_size)


# Process-level memo for `compile_source`, keyed on the source content, the
# `strip` flag, and the oracle binary's identity (see
# `_oracle_binary_identity`). No size cap: the corpus is 229 files at up to
# 124 KB source each, so even every distinct (source, strip, binary) triple
# compiled once in a process's lifetime is a small number of MB of compiled
# bytecode -- a measured decision (task-1-report.md), not an oversight.
_COMPILE_MEMO: dict[tuple[bytes, bool, str, int, int], bytes] = {}


def compile_source(source: bytes, *, strip: bool = False) -> bytes:
    # luac embeds the input filename it is given as Proto.source at compile
    # time (lundump.c LoadFunction reads it straight from the binary chunk,
    # independent of any chunkname passed at load time). Running luac with
    # cwd=td and a RELATIVE filename keeps that embedded name stable
    # ("@in.lua") regardless of where the random tempdir lands -- otherwise
    # two compiles of byte-identical source produce byte-DIFFERENT bytecode,
    # which would silently defeat any byte/field-level comparison of two
    # compilations (see verify.normalize's L3.0 comparator).
    key = (hashlib.sha256(source).digest(), strip) + _oracle_binary_identity()
    cached = _COMPILE_MEMO.get(key)
    if cached is not None:
        return cached
    with tempfile.TemporaryDirectory() as td:
        s = Path(td) / "in.lua"
        o = Path(td) / "out.luac"
        s.write_bytes(source)
        cmd = [str(luac_sz4())] + (["-s"] if strip else []) + ["-o", "out.luac", "in.lua"]
        r = subprocess.run(cmd, capture_output=True, cwd=td)
        if r.returncode != 0:
            raise LuaCompileError(r.stderr.decode(errors="replace"))
        result = o.read_bytes()
    _COMPILE_MEMO[key] = result
    return result


def run_bytes(payload: bytes, *, is_source: bool, args: tuple[str, ...] = (),
              timeout: float = 30.0) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        return subprocess.run([str(lua_sz4()), str(f), *args],
                              capture_output=True, timeout=timeout)

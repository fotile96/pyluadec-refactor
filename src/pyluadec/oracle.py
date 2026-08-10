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
    # luac embeds the input filename it is given as Proto.source at compile
    # time (lundump.c LoadFunction reads it straight from the binary chunk,
    # independent of any chunkname passed at load time). Running luac with
    # cwd=td and a RELATIVE filename keeps that embedded name stable
    # ("@in.lua") regardless of where the random tempdir lands -- otherwise
    # two compiles of byte-identical source produce byte-DIFFERENT bytecode,
    # which would silently defeat any byte/field-level comparison of two
    # compilations (see verify.normalize's L3.0 comparator).
    with tempfile.TemporaryDirectory() as td:
        s = Path(td) / "in.lua"
        o = Path(td) / "out.luac"
        s.write_bytes(source)
        cmd = [str(luac_sz4())] + (["-s"] if strip else []) + ["-o", "out.luac", "in.lua"]
        r = subprocess.run(cmd, capture_output=True, cwd=td)
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

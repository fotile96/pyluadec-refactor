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

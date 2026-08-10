import os
import subprocess
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"


@pytest.fixture(scope="session")
def corpus_dir() -> Path:
    p = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not p or not Path(p).is_dir():
        pytest.skip("PYLUADEC_CORPUS_DIR not set or missing (corpus tests skipped)")
    return Path(p)


@pytest.fixture
def compile_lua(tmp_path):
    """Compile a Lua source snippet with a built luac and return the path to
    the compiled output.

    `luac` may be either a name relative to `build/` (e.g. "luac_sz4") or a
    full Path to a luac binary. Skips the test (rather than raising a bare
    FileNotFoundError) if `build/` or the requested luac binary is missing --
    run ./scripts/build_native.sh first.
    """
    def _compile(luac, src: str) -> Path:
        luac_path = luac if isinstance(luac, Path) else BUILD / luac
        if not BUILD.is_dir() or not luac_path.is_file():
            pytest.skip(f"{luac_path} not found; run ./scripts/build_native.sh")
        s = tmp_path / "t.lua"
        o = tmp_path / "t.out"
        s.write_text(src, encoding="utf-8")
        subprocess.run([str(luac_path), "-o", str(o), str(s)], check=True)
        return o
    return _compile

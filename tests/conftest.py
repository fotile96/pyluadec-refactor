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


@pytest.fixture(scope="session")
def decompiled(corpus_dir):
    """Session-scoped, lazy `path -> DecompileResult` cache.

    `decompile_file` is by far the most expensive thing the corpus tests do
    (~7.6s for all 229 files), and several tests need the same 229 results:
    test_corpus_compile.py recompiles them, test_global_state_probe.py probes
    them. Without sharing, each test pays the full pass again. Returns a
    callable rather than a prebuilt dict so a test that needs one file
    (e.g. the probe sensitivity tests) does not trigger a whole-corpus
    decompile when run on its own.

    Deliberately NOT used by test_ledger_ratchet.py: that test's whole point
    is that a *fresh* run of scripts/run_corpus.py reproduces the committed
    ledger, so it must not consume anything another test already computed.
    """
    cache: dict[Path, object] = {}

    def get(path: Path):
        from pyluadec.pipeline import decompile_file
        p = Path(path)
        if p not in cache:
            cache[p] = decompile_file(p)
        return cache[p]

    return get


def _corpus_dir_missing() -> bool:
    p = os.environ.get("PYLUADEC_CORPUS_DIR")
    return not p or not Path(p).is_dir()


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    """Loud, hard-to-miss banner when PYLUADEC_CORPUS_DIR is unset/missing.

    A bare `uv run pytest` without the corpus env var still exits 0 and
    prints a green "N passed" -- correctly, per the `corpus_dir` fixture's
    deliberate skip-not-error design (corpus availability is an environment
    fact, not a code defect; see CLAUDE.md). But that green result silently
    excludes 13 corpus-gated tests, including the M2 exit gate
    (test_corpus_compile.py), both migration gates (test_golden.py,
    test_parity.py), and the ledger fixed-point test
    (test_ledger_ratchet.py). This hook does not change the exit code or
    turn the missing corpus into an error -- it only makes the consequence
    impossible to miss by skimming the summary line.
    """
    if not _corpus_dir_missing():
        return
    terminalreporter.write_sep("=", "PYLUADEC_CORPUS_DIR not set", red=True, bold=True)
    terminalreporter.write_line(
        "Corpus-gated tests were skipped, not run -- including the M2 exit "
        "gate (test_corpus_compile.py), the golden/parity migration gates "
        "(test_golden.py, test_parity.py), and the ledger fixed-point test "
        "(test_ledger_ratchet.py). A green result above does NOT mean those "
        "passed. Set PYLUADEC_CORPUS_DIR to the 229-file corpus directory "
        "and re-run before trusting this as a full-suite result -- see "
        "CLAUDE.md / docs/runbooks/decompile-pipeline.md.")


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

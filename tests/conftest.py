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


@pytest.fixture(scope="session")
def lifted_corpus(corpus_dir):
    """Session-scoped, eagerly-built list of every proto in the corpus,
    already ingested and lifted (round-1 fold-in of the M4 task-9 review's
    suite-budget recovery, 2026-08-12).

    Lifted to session scope from the pattern several corpus tests already
    used ad hoc, module-locally: `test_effects_emitter_consistency.py`'s
    `corpus_scan`, `test_effects_tailcall.py`'s `corpus_tailcall_census`, and
    two separate walks inside `test_express_names.py`
    (`test_corpus_no_open_region_in_pre_fix_temp_window`,
    `test_corpus_every_temp_write_has_exactly_one_consumer`) each paid their
    own full ingest+lift pass over the same 229 files. Building it once here
    rather than once per consumer module is the same "a slow suite blocks
    development" trade already made for `decompiled` above.

    **Cost, re-measured M4 task 12 (2026-08-12).** A full ingest+lift of all
    1944 proto occurrences costs **~0.97s** in a fresh process, and pytest
    attributes **~1.05s** to this fixture's `setup` (median of 3 runs of
    `pytest tests/test_effects_modes.py --durations=3`: 1.05 / 1.05 / 1.06s).
    Ingest alone is ~0.03s, so the lift is essentially all of it. An earlier
    revision of this docstring said "~0.69s"; that figure is real but it is a
    *warm-process repeated-pass* measurement (0.686-0.692s over 5 back-to-back
    passes in one interpreter), and the suite only ever pays the cold one. Two
    independent reviewers measured 0.97-1.04s and were right; the number here
    was describing a loop nobody runs. If you re-measure, say which of the two
    you measured.

    Returns a list of `(fname, path, proto, fn)` tuples, one per proto
    occurrence (1944 total): `fname` is the corpus file's basename, `path`
    is the tuple of subproto indices from that file's root proto (`()` for
    the root itself, matching the walk order `proto.subprotos[i]`), `proto`
    is the `Proto`, and `fn` is `lift_proto(proto)`. Depth-first order,
    root before its subprotos.

    NOT every corpus-walking test can use this. `test_effects_reconstructor_
    consistency.py`'s `corpus_scan` drives `emit.lua.print_chunk(proto)`
    under instrumentation and needs to observe a *fresh* `lift_proto` call
    happening live inside that call (there is no seam to hand it a
    pre-lifted `LirFunction` instead without a `src/` change, which is out
    of scope this round) -- sharing would save only the ~0.04s ingest step,
    not the dominant cost, so it is left alone (same reasoning as this
    module's `decompiled` fixture being unusable for that gate, recorded in
    task-9-report.md). `test_effects_tailcall.py`'s census also stays
    unconverted: it only ever needs `decode()`, not a full `lift_proto`, to
    find the 3 `TAILCALL` sites, so reusing this fixture would mean lifting
    all 1944 protos to answer a question a cheaper decode-only pass already
    answers in 0.23-0.25s, and its `path` is a dotted string from
    `walk_proto_paths` (`"main_29_0"`), not this fixture's index-tuple
    shape. `test_global_state_probe.py` does not lift the corpus directly at
    all (it goes through the `decompiled` fixture above, whose cost is the
    oracle compile/probe, not the lift), so there is nothing in it to
    convert.
    """
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto

    out = []

    def walk(proto, fname, path):
        fn = lift_proto(proto)
        out.append((fname, path, proto, fn))
        for i, sp in enumerate(proto.subprotos):
            walk(sp, fname, path + (i,))

    for f in sorted(corpus_dir.glob("*.lua")):
        walk(load_file(f), f.name, ())
    return out


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

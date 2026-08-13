import os
import subprocess
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"


@pytest.fixture(autouse=True)
def _fence_certification_cache():
    """Snapshot and restore `structure.structured._CERT_CACHE` around every
    test (round-1 fix of M5 task 2's Important 2).

    Since M5 task 2 that cache outlives the chunk and is shared by every test
    in the process. `monkeypatch` restores the attribute it patched at
    teardown; it does NOT remove cache entries computed while the patch was in
    force. A fault-injection test that patches the printer / the reconstructor
    / `build_cfg` and then certifies therefore writes a WRONG verdict under an
    ORDINARY key into a dict the `decompiled` fixture and the ledger ratchet
    both read -- a green suite carrying wrong verdicts, with the outcome
    depending on collection order. `tests/test_structured_certify.py`'s
    `test_a_patched_printer_writes_a_wrong_verdict_into_the_shared_cache` /
    `test_the_poisoned_verdict_did_not_outlive_the_test_that_wrote_it` pair is
    exactly that scenario, and the second of the two fails without this
    fixture.

    **Unconditional, and a prediction that did not survive measurement.** The
    obvious worry is that this throws away M5 task 2's whole saving: the
    corpus's ~1900 verdicts are computed during a test, so rolling the cache
    back after every test should force `test_ledger_ratchet` to pay the ~10s
    certification pass again. Measured, it does not, and the reason is fixture
    ordering: the corpus is certified in the setup of a MODULE-scoped fixture
    (`test_behaviour_probe.py::behaviour_traces`), and higher-scoped fixtures
    are set up before function-scoped autouse ones -- so those entries are
    already inside this fixture's snapshot and the restore puts them straight
    back. `test_ledger_ratchet` stays at its post-task-2 1.66-1.69s.

    Measured cost, 2026-08-12: **not resolvable against this suite's own
    noise.** Six interleaved A/B pairs of full-suite runs on the same tree
    (fence / fence body replaced by a bare `yield`), in two groups of three:

        fence    31.98  32.42  32.09  |  33.03  33.05  33.72
        no fence 31.80  31.67  31.69  |  33.34  33.35  33.47

    The first group makes the fence look ~0.4s slower, the second ~0.3s
    faster, while the absolute wall drifts ~2s upward across the session
    (thermal, on this laptop) -- so 523 x (copy + rebuild) of a ~1900-entry
    dict is somewhere under a few hundred ms and cannot be pinned tighter
    here. Interleave if you re-measure; absolute walls from different points
    in a session are not comparable.

    A narrower version gated on `"monkeypatch" in request.fixturenames` was
    built and measured first (31.70 / 31.82 / 31.82s, likewise
    indistinguishable) and covers every in-tree patching mechanism, since
    nothing here uses `unittest.mock` or import-time shims -- but it is a
    heuristic about HOW a future test patches, and an unmeasurable cost is not
    worth owning one. The no-fence arm of the runs above is also the standing
    red for the poisoning pair: it reports `1 failed, 522 passed` every time.

    The one thing to know if this ever shows up as a slow suite: an entry
    written from a TEST BODY (rather than from a higher-scoped fixture's
    setup) is discarded at that test's teardown and recomputed by the next
    reader. That is bounded by one corpus certification pass and today costs
    nothing, because the first population happens in the module-scoped setup
    above.
    """
    from pyluadec.structure import structured
    snapshot = dict(structured._CERT_CACHE)
    # M5 task 6 added a second process-level memo, `_HYBRID_CACHE`, holding
    # whole assembled hybrid chunk SOURCES. It is poisonable in exactly the
    # same way and by the same tests (a patched printer changes the assembled
    # bytes, not just a verdict), so it is fenced here rather than left to be
    # rediscovered.
    hybrid_snapshot = dict(structured._HYBRID_CACHE)
    yield
    # Re-read the attribute: a test may have swapped it for a private dict and
    # `monkeypatch`'s own teardown (which runs before this one, since it was
    # set up after) has just put the real one back.
    live = structured._CERT_CACHE
    live.clear()
    live.update(snapshot)
    live_hybrid = structured._HYBRID_CACHE
    live_hybrid.clear()
    live_hybrid.update(hybrid_snapshot)


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

    That last sentence needs one qualification as of M5 task 2. This fixture's
    *results* are still not shared with the ratchet test -- it re-ingests, re-
    walks, re-prints, re-assembles and re-writes every file for itself. But
    `structure.structured.certify_proto` now memoizes L3 verdicts for the life
    of the PROCESS, so whichever of the two corpus passes runs first pays the
    ~1900 `luac_sz4` certification subprocesses and the second gets those
    verdicts back from the cache (this fixture is first in practice:
    test_behaviour_probe.py sorts before test_ledger_ratchet.py). The verdict
    is a pure function of the proto and the oracle, and the cache key covers
    both in full (see `certify_proto`; as of the round-1 fix the oracle
    component is the `luac_sz4` binary's own identity, re-read per lookup --
    the original `git log` hash was memoized per process and did not actually
    cover it), so nothing the ratchet test asserts changes. What it does mean is that the ratchet no longer re-executes
    `luac` per proto, so a hypothetical NON-determinism in certification would
    be masked rather than caught -- recorded here because that is a real, if
    narrow, loss of coverage and it should not be rediscovered by surprise.
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
def pred_corpus_dir() -> Path:
    """`PYLUADEC_PRED_CORPUS_DIR`, mirroring `corpus_dir` exactly (M6 task 2):
    skip-not-error when unset or missing, same reasoning -- predecessor-
    corpus availability is an environment fact, not a code defect. Points at
    the predecessor project's 229 decompiled Lua SOURCE files (not
    bytecode), conventionally `/Users/fotile96/Zndnovel/lua_scripts`.
    """
    p = os.environ.get("PYLUADEC_PRED_CORPUS_DIR")
    if not p or not Path(p).is_dir():
        pytest.skip("PYLUADEC_PRED_CORPUS_DIR not set or missing "
                    "(predecessor-corpus tests skipped)")
    return Path(p)


@pytest.fixture(scope="session")
def pred_compiled(pred_corpus_dir):
    """Session-scoped, lazy `name -> Proto` cache for the predecessor corpus,
    the `pred_corpus_dir`-side twin of `decompiled` above.

    `predcorpus.load_pred_proto` itself is cheap even uncached (measured
    2026-08-13: the full 229-file compile+ingest pass is ~0.67s cold, most of
    it `oracle.compile_source`'s own process memo from M6 task 1 already
    doing the expensive part once per distinct source), so this fixture is
    here for the same reason `decompiled` is -- several tests wanting the
    same file's compiled proto should not each pay their own pass -- not
    because any single pass is expensive on its own.
    """
    cache: dict[str, object] = {}

    def get(name: str):
        from pyluadec.predcorpus import load_pred_proto
        if name not in cache:
            cache[name] = load_pred_proto(pred_corpus_dir, name)
        return cache[name]

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


def _pred_corpus_dir_missing() -> bool:
    p = os.environ.get("PYLUADEC_PRED_CORPUS_DIR")
    return not p or not Path(p).is_dir()


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    """Loud, hard-to-miss banner(s) when either corpus env var is unset/missing.

    A bare `uv run pytest` without one or both corpus env vars still exits 0
    and prints a green "N passed" -- correctly, per `corpus_dir`'s and (M6
    task 2) `pred_corpus_dir`'s deliberate skip-not-error design (corpus
    availability is an environment fact, not a code defect; see CLAUDE.md).
    But that green result silently excludes corpus-gated tests. Skip counts
    are the claim; the surrounding totals move with the suite and are dated
    evidence, not constants -- measured 2026-08-13, before M6 task 2's two
    new `test_predcorpus.py` tests existed, a bare `uv run pytest` reported
    `794 passed, 75 skipped`. Re-derive, do not copy: earlier revisions of
    this docstring quoted `792/75`, `789/864` and `13` in turn, each true of
    a tree that had since moved on.

    **After M6 task 2** the two env vars are independent and this hook
    prints a separate banner for each that is missing (both may fire in one
    run). With `PYLUADEC_CORPUS_DIR` set and `PYLUADEC_PRED_CORPUS_DIR`
    unset, only `test_predcorpus.py`'s 2 tests skip (`869 passed, 2
    skipped`, measured 2026-08-13); with both set, the whole suite runs
    (`871 passed`, measured 2026-08-13, ~37-38s, comfortably inside the 45s
    ceiling). With `PYLUADEC_CORPUS_DIR` unset the bare-run figure above
    already includes those same 2 tests among its 77 skips, since
    `test_predcorpus.py`'s tests request `corpus_dir` before
    `pred_corpus_dir` and so skip for the primary reason first.

    Among the corpus-gated tests are the M2 exit gate
    (test_corpus_compile.py), both migration gates (test_golden.py,
    test_parity.py), and the ledger fixed-point test
    (test_ledger_ratchet.py).

    **One skip in the suite is NOT corpus-gated and this hook says nothing
    about it** (M6 task 4): `test_observation_classes.py::
    test_classes_json_is_a_reproducible_fixed_point` is gated on
    `PYLUADEC_OBSERVATION_FIXED_POINT` because it is a whole-corpus
    regeneration that measured +4.0s against the 45s ceiling, and it runs as
    gate 4 of `scripts/ratchet_job.sh` instead. It therefore appears in the
    skip count of every run, corpus present or not, and it is the one skip
    a missing-corpus banner does not explain. This hook does not change the exit code or
    turn a missing corpus into an error -- it only makes the consequence
    impossible to miss by skimming the summary line.
    """
    primary_missing = _corpus_dir_missing()
    pred_missing = _pred_corpus_dir_missing()
    if not primary_missing and not pred_missing:
        return
    if primary_missing:
        terminalreporter.write_sep("=", "PYLUADEC_CORPUS_DIR not set", red=True, bold=True)
        terminalreporter.write_line(
            "Corpus-gated tests were skipped, not run -- including the M2 exit "
            "gate (test_corpus_compile.py), the golden/parity migration gates "
            "(test_golden.py, test_parity.py), and the ledger fixed-point test "
            "(test_ledger_ratchet.py). A green result above does NOT mean those "
            "passed. Set PYLUADEC_CORPUS_DIR to the 229-file corpus directory "
            "and re-run before trusting this as a full-suite result -- see "
            "CLAUDE.md / docs/runbooks/decompile-pipeline.md.")
    if pred_missing:
        terminalreporter.write_sep("=", "PYLUADEC_PRED_CORPUS_DIR not set", red=True, bold=True)
        terminalreporter.write_line(
            "Predecessor-corpus-gated tests were skipped, not run -- "
            "including the cross-corpus parity census (test_predcorpus.py). "
            "A green result above does NOT mean those passed. Set "
            "PYLUADEC_PRED_CORPUS_DIR to the predecessor's 229-file decompiled-"
            "source directory (conventionally the sibling Zndnovel/lua_scripts "
            "checkout) and re-run before trusting this as a full-suite result "
            "-- see CLAUDE.md.")


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

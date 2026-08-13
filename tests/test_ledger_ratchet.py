import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER = REPO_ROOT / "corpus" / "ledger.jsonl"


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


# This test re-runs the entire corpus pipeline: 229 files, 1944 proto
# occurrences, one `luac_sz4` subprocess per proto for certification plus one
# per chunk for the compile check. It was the slowest single test in the suite
# (9.5s on macOS arm64 2026-08-11; 13.2-13.6s by the M5 task 2 baseline).
#
# It now measures **1.66-1.69s** in a full-suite run (1.87-1.89s as first
# measured at M5 task 2; re-measured 2026-08-12 after the round-1 key change),
# because M5 task 2 made
# `structure.structured.certify_proto`'s memo process-wide: the corpus is
# certified once per process, and by the time this test runs the session
# `decompiled` fixture has already paid for it. What remains here is the real
# work this test exists to check -- ingest, walk, print/assemble, the 229
# whole-chunk compile checks, and the ledger write. Run ALONE (`uv run pytest
# tests/test_ledger_ratchet.py`) it is 9.8-10.0s, since then it is the one
# paying -- so the saving really is a transfer, not a disappearance. See
# tests/conftest.py's `decompiled` docstring for what that sharing does and
# does not cost in coverage.
#
# The global `timeout = 60` in pyproject.toml is a hang backstop sized for
# ordinary tests; this one is legitimately subprocess-bound and would be the
# first to trip it on a slower host (the documented primary environment is a
# 32-bit i686 userland under WSL2). Given its own budget rather than loosening
# the global one -- see pyproject.toml.
@pytest.mark.timeout(300)
def test_ledger_is_a_reproducible_fixed_point(corpus_dir, tmp_path, monkeypatch):
    """corpus/ledger.jsonl must be a fixed point of scripts/run_corpus.py: a
    fresh run against the same corpus must reproduce it byte-identically.

    This is the actual regression guard spec §5 describes ("台账 diff 即回归
    测试本体") -- if regeneration ever perturbs unrelated lines (e.g. because
    a field like `oracle` records something that moves on every commit
    rather than something that only changes when the oracle build changes),
    a real two-line regression would be buried in thousands of lines of
    diff noise. Runs run_corpus.main() against a scratch ROOT (via
    monkeypatch) so the committed ledger and build/decompiled/ are never
    touched as a side effect of running this test.
    """
    spec = importlib.util.spec_from_file_location(
        "run_corpus_fixedpoint_check", REPO_ROOT / "scripts" / "run_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(corpus_dir))

    rc = mod.main()

    assert rc == 0
    regenerated = (tmp_path / "corpus" / "ledger.jsonl").read_bytes()
    assert regenerated == LEDGER.read_bytes()


def _run_corpus_module():
    spec = importlib.util.spec_from_file_location(
        "run_corpus_keycheck", REPO_ROOT / "scripts" / "run_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_key_disagreement_check_accepts_an_agreeing_group():
    """Two occurrences of one shape with DIFFERENT debug fingerprints but the
    same verdict is the shape 16 of the 1478 committed groups actually have
    (M5 task 8, re-measured: 16 groups, 462 fingerprints between them). It
    must pass -- the check is about verdicts, not about fingerprints."""
    mod = _run_corpus_module()
    observed = {"aa" * 32: [
        {"file": "a.lua", "proto_path": "main_1", "dfp": "f1",
         "level": "L3", "rung": 1, "reason": None},
        {"file": "b.lua", "proto_path": "main_7", "dfp": "f2",
         "level": "L3", "rung": 1, "reason": None},
    ]}
    assert mod.key_disagreements(observed) == []


def test_key_disagreement_check_actually_rejects_a_split_group():
    """The corpus arm of this check is `test_ledger_is_a_reproducible_fixed_
    point` above (a disagreement makes `main()` return 1 before writing), and
    it runs against a corpus that satisfies the invariant -- so on its own it
    would go on passing if `key_disagreements` were weakened to `return []`.
    This is the committed proof that it cannot be.

    All three components of the verdict are covered separately: a level
    disagreement is the one that would corrupt a row outright, a rung
    disagreement is the one a future `L3.2` makes reachable, and a reason
    disagreement is the one that would silently pick whichever file sorted
    first."""
    mod = _run_corpus_module()

    def group(*verdicts):
        return {"aa" * 32: [
            {"file": f"f{i}.lua", "proto_path": "main", "dfp": f"f{i}",
             "level": v[0], "rung": v[1], "reason": v[2]}
            for i, v in enumerate(verdicts)]}

    for verdicts in (
        (("L3", 1, None), ("L1", None, "structure: pc 3: back edge")),   # level
        (("L3", 0, None), ("L3", 1, None)),                              # rung
        (("L1", None, "mismatch: code"), ("L1", None, "structure: pc 3")),  # reason
    ):
        bad = mod.key_disagreements(group(*verdicts))
        assert len(bad) == 1, verdicts
        assert "aa" * 32 in bad[0]
        assert "split it to" in bad[0]
        # names both offending occurrences, so the failure is actionable
        assert "f0.lua" in bad[0] and "f1.lua" in bad[0]


def test_key_disagreement_check_is_ordered_and_reports_fingerprints():
    mod = _run_corpus_module()
    observed = {
        "bb" * 32: [{"file": "b.lua", "proto_path": "main", "dfp": "x",
                     "level": "L3", "rung": 1, "reason": None},
                    {"file": "c.lua", "proto_path": "main", "dfp": "y",
                     "level": "L1", "rung": None, "reason": "mismatch: code"}],
        "aa" * 32: [{"file": "a.lua", "proto_path": "main", "dfp": "z",
                     "level": "L3", "rung": 1, "reason": None},
                    {"file": "d.lua", "proto_path": "main", "dfp": "z",
                     "level": "L1", "rung": None, "reason": "mismatch: code"}],
    }
    bad = mod.key_disagreements(observed)
    assert len(bad) == 2
    assert bad[0].startswith("aa" * 32) and bad[1].startswith("bb" * 32)
    assert "1 debug fingerprint(s)" in bad[0]     # both occurrences share dfp z
    assert "2 debug fingerprint(s)" in bad[1]

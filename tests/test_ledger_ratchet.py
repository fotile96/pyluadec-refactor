import importlib.util
import json
from pathlib import Path

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

"""M3 exit gate, read off the committed ledger.

The threshold is a milestone commitment, not a measurement: it must not be
edited down to match whatever the current implementation achieves. If the
corpus rate falls below it, the fix is in the reconstructor, not here.
"""
import json
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "corpus" / "ledger.jsonl"


def _entries():
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def test_m3_exit_majority_of_unique_protos_are_l3():
    entries = _entries()
    assert entries
    l3 = sum(1 for e in entries if e["level"] == "L3")
    frac = l3 / len(entries)
    assert frac > 0.50, f"only {l3}/{len(entries)} ({frac:.1%}) unique protos are L3"


def test_m3_exit_majority_of_proto_occurrences_are_l3():
    """The same gate on the un-deduplicated basis.

    `corpus/ledger.jsonl` keys by `structural_hash`, so its 1478 rows are
    unique proto SHAPES, not the 1944 protos that actually exist in the 229
    files. A filtered or deduplicated denominator has already hidden two real
    defects in this project, so the exit metric is checked both ways: a
    change that certified only the shapes that happen to be rare would move
    the unique-proto number without moving this one.
    """
    entries = _entries()
    total = sum(len(e["occurrences"]) for e in entries)
    l3 = sum(len(e["occurrences"]) for e in entries if e["level"] == "L3")
    assert total == 1944
    frac = l3 / total
    assert frac > 0.50, f"only {l3}/{total} ({frac:.1%}) proto occurrences are L3"


def test_every_entry_still_compiles_and_no_l0():
    entries = _entries()
    assert all(e["compile_ok"] for e in entries)
    assert all(e["level"] in ("L1", "L2", "L3") for e in entries)


def test_l3_entries_carry_a_rung_and_no_confessions():
    entries = _entries()
    assert any(e["level"] == "L3" for e in entries)
    for e in entries:
        if e["level"] == "L3":
            assert e["l3_level"] is not None
            assert e["confessions"] == []
            assert e["fallback"] is False


def test_non_l3_entries_confess():
    """The other half of the ratchet: a proto that did not certify must still
    say so. A level that rose without its confession being dropped, or a
    confession dropped without the level rising, is a bookkeeping bug."""
    for e in _entries():
        if e["level"] != "L3":
            assert e["fallback"] is True
            assert e["l3_level"] is None
            assert [c["reason"] for c in e["confessions"]] == ["fallback-state-machine"]


def test_ledger_still_covers_full_corpus(corpus_dir):
    entries = _entries()
    files = {o["file"] for e in entries for o in e["occurrences"]}
    assert files == {f.name for f in corpus_dir.glob("*.lua")}
    assert sum(len(e["occurrences"]) for e in entries) == 1944

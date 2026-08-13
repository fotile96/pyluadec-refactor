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
    """An `L3` row carries the rung it certified at and claims no refusal.

    **What this test lost in M5 task 6, and where it went.** It used to also
    assert `fallback is False` and `confessions == []` for every `L3` row,
    which was sound only while `fallback` was *defined* as `level != "L3"`.
    Since hybrid emission, `fallback` means "at least one occurrence of this
    proto shape shipped as the state machine", and that is genuinely possible
    for an `L3` shape: 7 corpus files still ship a whole-file fallback (their
    ROOT's own reconstruction does not certify), and every certified proto
    inside one of them ships as state-machine text. Asserting `confessions ==
    []` there would mean an artifact silently shipping unstructured text for a
    proto whose row says nothing about it -- the confession hole in the
    direction that actually matters. The coupling that replaces it, in both
    directions and per occurrence, is in `test_non_l3_entries_confess`.
    """
    entries = _entries()
    assert any(e["level"] == "L3" for e in entries)
    for e in entries:
        if e["level"] == "L3":
            assert e["l3_level"] is not None
            assert e["refusal_reason"] is None


def test_non_l3_entries_confess():
    """The other half of the ratchet: a proto that did not certify must still
    say so.

    **Rewritten for the M5 task 6 schema.** `fallback` used to be *defined* as
    `level != "L3"`, so "not certified" and "shipped as the state machine" were
    the same row and this test could assert one from the other. Hybrid emission
    separates them: a proto that misses `L3` on its own can still ship
    structured, because the chunk's hybrid certification compared its own
    fields against the original exactly (only the substituted subtrees are
    unclaimed). What survives, and is asserted here, is the coupling that
    actually encodes the confession discipline:

      * a non-`L3` row carries no rung and says why it is not `L3`;
      * `fallback` (an occurrence really did ship the state machine) holds
        exactly when the whole-range `fallback-state-machine` confession is
        present -- in both directions, so a confession dropped without the
        shipping changing, or shipping changed without the confession being
        dropped, still fails;
      * and `fallback` is exactly the OR over the per-occurrence `shipped`
        field, so the row-level aggregate cannot drift from the per-occurrence
        record it summarises.

    Note the last two run over EVERY row, not only the non-`L3` ones: an `L3`
    proto shipping as state-machine text inside a whole-file-fallback chunk is
    the case this has to catch, and it is 7 files' worth of rows today
    (`config`, `snr_common`, `snr_graphic`, `snr_mainmenu`, `snr_memory`,
    `snr_music`, `snr_novel` -- re-measured from the committed ledger
    2026-08-12; round 1 of this task wrote 8 in both places).
    """
    for e in _entries():
        if e["level"] != "L3":
            assert e["l3_level"] is None
            assert e["refusal_reason"]
        want = ["fallback-state-machine"] if e["fallback"] else []
        assert [c["reason"] for c in e["confessions"]] == want, e["shash"]
        assert e["fallback"] == any(o["shipped"] == "fallback"
                                    for o in e["occurrences"]), e["shash"]


def test_ledger_still_covers_full_corpus(corpus_dir):
    entries = _entries()
    files = {o["file"] for e in entries for o in e["occurrences"]}
    assert files == {f.name for f in corpus_dir.glob("*.lua")}
    assert sum(len(e["occurrences"]) for e in entries) == 1944

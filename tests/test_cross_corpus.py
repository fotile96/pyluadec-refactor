"""Cross-corpus scan harness -- M6 task 5 smoke subset + non-vacuity proof.

The harness itself is `scripts/cross_corpus.py`; the **full 229-file scan is a
job, not a suite member** (`uv run python scripts/cross_corpus.py --arm all`,
measured wall-clock in `docs/reports/m6-cross-corpus.md` §2). What lives here is
the smoke subset the plan asks for -- three named files on the fingerprint arm,
one file each on the state and behaviour arms -- plus the part that actually
earns its place in the suite: a **synthetic divergence** that the behaviour arm
is required to catch.

Direction. Every other probe gate in this repo runs "our decompiled artifact vs
the original bytecode". This one runs "the PREDECESSOR's shipped source vs the
original bytecode": same two-sided probe, different candidate. The predecessor
corpus is the shipped localization -- recompiled, repacked into a PSP ISO and
played to completion by a human -- so a divergence here is a defect in
something that shipped, not in us.

Why the synthetic proof is mandatory (plan Step 1, "the non-vacuity proof
committed before the first full scan"): an instrument that cannot fail licenses
exactly the claim it does not enforce, and this project has already been bitten
by the failure mode twice -- `probe_global_state.py` once returned "" for every
probe-side failure (a completely dead gate that compared equal on all 229
files), and `scripts/probe_keyseq.py` stubs the very gates that select the arms
of the two defects Task 4 found by hand, so its 5 authored sequences produce
byte-identical traces on original, predecessor AND repaired text.
`test_synthetic_numeric_mutation_is_caught_by_the_behaviour_arm` below flips ONE
numeric argument in ONE predecessor source inside a temp dir and requires the
arm to report it.

No game text anywhere: the evidence strings this harness produces are
opcode/pc/event-shape summaries, ASCII identifiers and SHA-256 prefixes, and
`test_evidence_is_ascii` asserts it over the smoke subset.
"""
from __future__ import annotations

import pytest

from scripts import cross_corpus


# Three files chosen for what they exercise, not at random:
#   config.lua      -- the smallest (934 B), and the one whose chunk errors out
#                      immediately, so it exercises the ERR/`R|` paths.
#   snr_crd_0.lua   -- an ordinary story script, runs to completion ("OK").
#   snr_music.lua   -- Task 4's hand-found defect #1 (the music gallery's poll
#                      loop is missing from the predecessor's `main`).
SMOKE = ["config.lua", "snr_crd_0.lua", "snr_music.lua"]

# The mutation site for the non-vacuity proof: a numeric literal argument in
# snr_crd_0.lua, unique in the file (asserted below, so a corpus that no longer
# contains it fails loudly rather than silently skipping the proof).
MUT_FROM = b"vms(104,"
MUT_TO = b"vms(999,"


@pytest.fixture
def smoke_scan(corpus_dir, pred_corpus_dir):
    def go(arm, files=SMOKE, pred=None):
        return cross_corpus.scan(arm, files, corpus_dir=corpus_dir,
                                 pred_dir=pred or pred_corpus_dir)
    return go


# --------------------------------------------------------------------------
# Step 1a: the three arms return something with content
# --------------------------------------------------------------------------

def test_fingerprint_arm_scores_three_named_files(smoke_scan):
    res = smoke_scan("fingerprint")
    assert sorted(res) == sorted(SMOKE)
    for name, r in res.items():
        assert r.arm == "fingerprint"
        assert r.kind in cross_corpus.KINDS
        # A score is a number in [0, 1] and the harness must carry it even for
        # the files it does NOT queue -- the queue criterion is the metric's own
        # sensitivity thresholds, not "score < 1.0" (137 of 229 files are below
        # 1.0 with zero hard issues; see the report).
        assert 0.0 <= r.detail["score"] <= 1.0, name
        assert r.detail["status"] in ("pass", "warn", "fail")


def test_state_arm_returns_a_payload_comparison(smoke_scan):
    res = smoke_scan("state", files=["snr_crd_0.lua"])
    r = res["snr_crd_0.lua"]
    assert r.arm == "state"
    assert r.detail["orig_marker"] in ("OK", "ERR", "LOADFAIL")
    assert r.detail["pred_marker"] == r.detail["orig_marker"]
    assert r.kind == "agree"


def test_behaviour_arm_returns_a_trace_comparison(smoke_scan):
    res = smoke_scan("behaviour", files=["snr_crd_0.lua"])
    r = res["snr_crd_0.lua"]
    assert r.arm == "behaviour"
    assert r.kind == "agree"
    # The reach vocabulary is the "silent arm" defence: an arm that never fired
    # is not evidence of agreement, and the harness has to say which it is.
    assert r.reach in cross_corpus.REACH
    assert r.detail["orig_events"] > 0


def test_behaviour_arm_catches_the_known_music_defect(smoke_scan):
    """Task 4 found this by hand: the predecessor's `snr_music.lua` `main` lost
    the poll loop, so the music gallery bounces straight back to the menu. The
    behaviour arm has to see it -- and it is a HEADER-level divergence (the
    original's run is truncated by the event cap, the predecessor's finishes on
    its own), not a subtle one."""
    r = smoke_scan("behaviour", files=["snr_music.lua"])["snr_music.lua"]
    assert r.kind == "divergent"
    assert r.detail["orig_status"] != r.detail["pred_status"]
    assert r.detail["orig_events"] > r.detail["pred_events"]
    assert cross_corpus.first_cut(r) == "candidate-defect"


# --------------------------------------------------------------------------
# Step 1b: the non-vacuity proof
# --------------------------------------------------------------------------

@pytest.fixture
def mutated_pred(pred_corpus_dir, tmp_path):
    """A temp predecessor dir holding one file with one numeric argument
    changed. Everything else is untouched; the real predecessor corpus is never
    written to (a Global Constraint)."""
    src = (pred_corpus_dir / "snr_crd_0.lua").read_bytes()
    assert src.count(MUT_FROM) == 1, (
        f"mutation site {MUT_FROM!r} is no longer unique in snr_crd_0.lua "
        f"({src.count(MUT_FROM)} occurrences) -- pick a new one rather than "
        f"letting the non-vacuity proof degrade")
    d = tmp_path / "pred"
    d.mkdir()
    (d / "snr_crd_0.lua").write_bytes(src.replace(MUT_FROM, MUT_TO, 1))
    return d


def test_unmutated_control_agrees(smoke_scan):
    """The control half of the proof: without the mutation this exact file
    agrees byte-for-byte, so the mutation is what the next test detects."""
    assert smoke_scan("behaviour", files=["snr_crd_0.lua"])[
        "snr_crd_0.lua"].kind == "agree"


def test_synthetic_numeric_mutation_is_caught_by_the_behaviour_arm(
        smoke_scan, mutated_pred):
    r = smoke_scan("behaviour", files=["snr_crd_0.lua"], pred=mutated_pred)[
        "snr_crd_0.lua"]
    assert r.kind == "divergent"
    # Deliberately a NON-structural mutation: both sides record the same number
    # of events with the same status, and the divergence is in one argument
    # value of one call.
    assert r.detail["orig_status"] == r.detail["pred_status"]
    assert r.detail["orig_events"] == r.detail["pred_events"]
    assert r.detail["first_diff_line"] > 1


def test_the_sha_discriminator_in_behaviour_evidence_is_load_bearing(
        smoke_scan, mutated_pred):
    """Measured (2026-08-14): the mutated call's EVENT SHAPE is identical on
    both sides -- `C|vms|3args` either way, because the shape deliberately drops
    argument VALUES (they can be game text; the red line forbids carrying them
    into a committed artifact). Shape alone would therefore produce an evidence
    pair whose two halves are equal, and `adjudicate_pins`' `moved` detection --
    the thing that fails a pin whose recorded explanation stopped describing
    what happens -- would be blind to any change that moves only argument
    values. The SHA-256 prefix of the raw line is what restores that
    discrimination without carrying the bytes.

    Neuter proof: drop `sha=` from `behaviour_evidence` and this test is what
    goes red; `test_synthetic_numeric_mutation_is_caught_by_the_behaviour_arm`
    stays green, because divergence detection is a whole-trace byte compare
    that does not consult the evidence at all."""
    r = smoke_scan("behaviour", files=["snr_crd_0.lua"], pred=mutated_pred)[
        "snr_crd_0.lua"]
    a, b = r.evidence
    assert a != b, "evidence pair must discriminate the two sides"
    # ... and the reason it has to: the shapes agree.
    assert r.detail["orig_shape"] == r.detail["pred_shape"]


# --------------------------------------------------------------------------
# Red line + pin discipline
# --------------------------------------------------------------------------

def test_evidence_is_ascii(smoke_scan):
    for arm in cross_corpus.ARMS:
        for name, r in smoke_scan(arm).items():
            for half in r.evidence:
                assert half.isascii(), (arm, name)
            assert cross_corpus.json_safe(r.detail)


def test_event_shape_degrades_non_ascii_rather_than_leaking_it():
    """Synthetic, and labelled as such: the corpus has zero non-UTF-8 string
    constants (CLAUDE.md, measured) and both real divergences below are pure
    ASCII, so nothing in the 229-file scan exercises this path. It is still the
    only thing standing between a Japanese string constant in a trace argument
    and a committed report, so it gets a fixture instead of an assumption."""
    line = b'C|\xe6\x97\xa5\xe6\x9c\xac|1|"\xe3\x83\x86"'
    shape = cross_corpus.event_shape(line)
    assert shape.isascii()
    assert "non-ascii" in shape


def test_pred_pins_are_a_separate_table_from_our_side_pins():
    """The spec forbids reusing our-side pins: the 4 L1.5 and 2 L1.75 pins were
    recorded for "our artifact vs original" and say nothing about a different
    candidate population. This asserts the tables are distinct objects AND that
    no pin key was copied across."""
    from scripts.probe_behaviour import EXPECTED_DIVERGENCE
    from scripts.probe_global_state import EXPECTED_ERROR_NAME_DIVERGENCE
    assert set(cross_corpus.PRED_PINS) == set(cross_corpus.ARMS)
    for arm in cross_corpus.ARMS:
        assert cross_corpus.PRED_PINS[arm] is not EXPECTED_DIVERGENCE
        assert cross_corpus.PRED_PINS[arm] is not EXPECTED_ERROR_NAME_DIVERGENCE
        for name, pair in cross_corpus.PRED_PINS[arm].items():
            assert pair != EXPECTED_DIVERGENCE.get(name)
            assert pair != EXPECTED_ERROR_NAME_DIVERGENCE.get(name)


def test_first_cut_labels_come_from_the_vocabulary(smoke_scan):
    seen = 0
    for arm in cross_corpus.ARMS:
        for r in smoke_scan(arm).values():
            if not r.diverges:
                # A triage label for an agreeing row is meaningless, and the
                # harness refuses to invent one.
                with pytest.raises(ValueError):
                    cross_corpus.first_cut(r)
                continue
            assert cross_corpus.first_cut(r) in cross_corpus.FIRST_CUT
            seen += 1
    assert seen > 0, "smoke subset must contain at least one divergent row"


def test_behaviour_arm_labels_the_reordering_class_as_probable_artifact(
        smoke_scan):
    """The second of the two real behaviour divergences, and the instance that
    makes `_same_multiset` load-bearing rather than decorative: snr_novel.lua's
    two traces hold the SAME 43 events in a different order plus one
    `getobjname` naming difference, so they become equal multisets once the
    nouns are erased. Both classes are already pinned on our own side with
    instruction-level evidence."""
    r = smoke_scan("behaviour", files=["snr_novel.lua"])["snr_novel.lua"]
    assert r.kind == "divergent"
    assert r.detail["multiset_equal_after_objname"] is True
    assert r.detail["orig_status"] == r.detail["pred_status"] == "OK"
    assert cross_corpus.first_cut(r) == "probable-artifact"


def test_getobjname_normalisation_collapses_the_naming_artifact():
    """The one rule in `first_cut` that has to be spelled out, because it is the
    rule that can HIDE a real defect if it over-fires. Lua 5.1 names a value in
    an error message by the BYTECODE SHAPE that produced it (`ldebug.c`'s
    `getobjname`), so two chunks that fail at the same point on the same value
    still print different nouns. Erasing `<kind> '<name>'` is what lets the
    first cut call that class `probable-artifact` -- and it is a TRIAGE label,
    not a verdict; Task 6 adjudicates."""
    n = cross_corpus.normalize_objname
    assert (n(b"attempt to concatenate field '?' (a nil value)")
            == n(b"attempt to concatenate local 'v1' (a nil value)"))
    assert (n(b"attempt to index global 'systemSave' (a nil value)")
            == n(b"attempt to index field 'v' (a nil value)"))
    # It must NOT collapse two different OPERATIONS on the same noun.
    assert (n(b"attempt to index local 'v1' (a nil value)")
            != n(b"attempt to concatenate local 'v1' (a nil value)"))
    # ... nor a difference outside the quoted noun.
    assert (n(b"attempt to index local 'v1' (a nil value)")
            != n(b"attempt to index local 'v1' (a number value)"))


def test_a_candidate_that_does_not_load_is_never_reported_as_agreement(
        corpus_dir, tmp_path):
    """The L1.5 gate's hardest-won lesson, re-asserted for this harness: it
    once returned "" for every probe-side failure, which compared equal on all
    229 files and passed a completely dead gate. Fixture is a temp predecessor
    dir holding a file that is not Lua at all.

    The three arms report it in two different ways, and the exact mapping is
    asserted rather than collapsed to `!= "agree"`, because the difference is
    real: `luac` refusing the source is an ORACLE error (the fingerprint arm
    never gets a proto tree at all), while the two probes load the chunk inside
    the sandbox and report `LOADFAIL` -- a legitimate observation, and one the
    original side does not share, so it is a genuine divergence."""
    d = tmp_path / "pred"
    d.mkdir()
    (d / "config.lua").write_bytes(b"this is not lua ][\n")

    def go(arm):
        return cross_corpus.scan(arm, ["config.lua"], corpus_dir=corpus_dir,
                                 pred_dir=d)["config.lua"]

    for arm in cross_corpus.ARMS:
        assert go(arm).kind != "agree", arm
        assert all(h.isascii() for h in go(arm).evidence), arm
    assert go("fingerprint").kind == "probe-error"
    assert go("fingerprint").detail["error"] == "LuaCompileError"
    assert go("state").kind == "divergent"
    assert go("state").detail["pred_marker"] == "LOADFAIL"
    assert go("behaviour").kind == "divergent"
    assert go("behaviour").detail["pred_status"] == "LOADFAIL"


def test_scan_rejects_an_unknown_arm(corpus_dir, pred_corpus_dir):
    with pytest.raises(ValueError):
        cross_corpus.scan("nonsense", ["config.lua"], corpus_dir=corpus_dir,
                          pred_dir=pred_corpus_dir)


def test_predecessor_corpus_is_never_written_to(pred_corpus_dir, tmp_path,
                                                corpus_dir):
    """A Global Constraint ("do not modify anything under either corpus
    directory") turned into a check: snapshot the mtimes/sizes of the files the
    smoke subset touches, run all three arms, compare."""
    before = {n: (pred_corpus_dir / n).stat() for n in SMOKE}
    for arm in cross_corpus.ARMS:
        cross_corpus.scan(arm, SMOKE, corpus_dir=corpus_dir,
                          pred_dir=pred_corpus_dir)
    for n in SMOKE:
        after = (pred_corpus_dir / n).stat()
        assert (after.st_size, after.st_mtime_ns) == (
            before[n].st_size, before[n].st_mtime_ns), n

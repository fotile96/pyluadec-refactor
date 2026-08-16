"""Guards for `corpus/observation/classes.json` and its generator (M6 task 4).

Three kinds of assertion, deliberately separated:

1. **Schema and internal coupling** over the committed file alone (no corpus
   needed). These are what catch a hand edit, a half-applied schema change, or
   a class assignment that stopped matching its own evidence.
2. **The fixed point** -- the committed file is byte-reproducible from
   `scripts/observation_classes.py`. The reason is the one recorded at
   `tests/test_ledger_ratchet.py` and `tests/test_footprint.py`: committed
   generated data that nothing regenerates rots, and a real two-line
   regression arrives buried in noise. It costs ~2.4s and its attribution
   under the raised ceiling is argued at the test itself.
3. **An independent cross-check of the leaf-refusal rule**, because that rule
   is the one piece of candidate selection that is an inference rather than a
   reading (see `observation_classes.refusal_origin`).
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ROOT / "corpus" / "observation" / "classes.json"

CLASS_NAMES = {"choice-branch", "ui-keyloop", "neither"}
POPULATIONS = {"leaf-refusal", "cap-dominant"}


def _cli():
    """Import `scripts/observation_classes.py` as a module."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(
        "observation_classes_cli", ROOT / "scripts" / "observation_classes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def doc():
    return json.loads(CLASSES.read_text())


# ------------------------------------------------------------------ schema

def test_version_and_top_level_shape(doc):
    assert doc["version"] == "m6-classes-v1"
    assert set(doc) <= {"version", "summary", "candidates",
                        "orphan_observations"}
    assert {"version", "summary", "candidates"} <= set(doc)
    assert doc["summary"]["n_candidates"] == len(doc["candidates"])
    assert doc["summary"]["n_orphan_observations"] == \
        len(doc.get("orphan_observations", []))


def test_candidates_are_sorted_and_unique(doc):
    keys = [(r["file"], r["proto_path"]) for r in doc["candidates"]]
    assert keys == sorted(keys)
    assert len(set(keys)) == len(keys)


def test_every_record_has_a_mechanical_half_and_a_known_population(doc):
    for r in doc["candidates"]:
        m = r["mechanical"]
        assert m["selected_as"], (r["file"], r["proto_path"])
        assert set(m["selected_as"]) <= POPULATIONS
        assert m["class"] in CLASS_NAMES
        assert m["class_evidence"]


def test_class_is_exactly_its_own_evidence(doc):
    """The class assignment is a rule over two measured predicates, so it must
    be recoverable from them. A record whose class no longer follows from its
    `poll_loops` / `option_calls` is either a hand edit or a generator whose
    rule and whose output have drifted apart."""
    for r in doc["candidates"]:
        m = r["mechanical"]
        poll = bool(m["poll_loops"])
        opt = bool(m["option_calls"])
        expected = ("ui-keyloop" if poll else
                    "choice-branch" if opt else "neither")
        assert m["class"] == expected, (r["file"], r["proto_path"], poll, opt)


def test_input_space_is_the_product_of_its_channel_domains(doc):
    for r in doc["candidates"]:
        m = r["mechanical"]
        n = 1
        for ch in m["channels"]:
            expected = len(ch["constants"]) + 1 if ch["constants"] else 2
            assert ch["domain"] == expected, (r["file"], ch["text"])
            n *= ch["domain"]
        assert m["input_space"] == n, (r["file"], r["proto_path"])
        assert m["drivable_within_budget"] == (n <= doc["summary"]["budget"])


def test_a_leaf_refusal_candidate_is_non_l3_with_an_own_refusal(doc):
    for r in doc["candidates"]:
        m = r["mechanical"]
        if "leaf-refusal" in m["selected_as"]:
            assert m["level"] != "L3"
            assert m["refusal_reason"]
            assert m["refusal_origin"] == "own"
        if m["level"] == "L3":
            assert m["refusal_reason"] is None
            assert m["refusal_origin"] is None


def test_a_cap_dominant_candidate_names_its_probe_evidence(doc):
    for r in doc["candidates"]:
        m = r["mechanical"]
        if "cap-dominant" in m["selected_as"]:
            assert m["probe"]["file_status"] == "CAP"
            assert m["probe"]["dominant_global"]
            assert m["probe"]["dominant_global_events"] >= 1
        else:
            assert m["probe"]["dominant_global"] is None


def test_summary_counts_agree_with_the_candidate_list(doc):
    s = doc["summary"]
    cand = doc["candidates"]
    census: dict[str, int] = {}
    for r in cand:
        census[r["mechanical"]["class"]] = census.get(r["mechanical"]["class"], 0) + 1
    assert s["class_census"] == census
    assert s["n_leaf_refusals"] == sum(
        1 for r in cand if "leaf-refusal" in r["mechanical"]["selected_as"])
    assert s["n_cap_dominants"] == sum(
        1 for r in cand if "cap-dominant" in r["mechanical"]["selected_as"])
    assert s["n_in_both_populations"] == sum(
        1 for r in cand if len(r["mechanical"]["selected_as"]) > 1)
    assert s["n_observed_records"] == sum(1 for r in cand if "observed" in r)
    for cls, (ok, tot) in s["drivable_within_budget_by_class"].items():
        assert tot == census[cls]
        assert ok == sum(1 for r in cand
                         if r["mechanical"]["class"] == cls
                         and r["mechanical"]["drivable_within_budget"])


def test_observed_records_have_the_reviewed_shape(doc):
    """The observed half is frozen by review, so nothing here checks its
    CONTENT -- only that a record which claims to be reviewed says who, gives
    a verdict on the mechanical class, and carries a note. A `class_agrees`
    of False is legitimate and expected: it is how an audit disagreement is
    recorded without the mechanical rule quietly changing under it."""
    for r in doc["candidates"]:
        obs = r.get("observed")
        if obs is None:
            continue
        assert set(obs) == {"reviewed_by", "class_agrees", "note"}
        assert isinstance(obs["reviewed_by"], str) and obs["reviewed_by"]
        assert isinstance(obs["class_agrees"], bool)
        assert isinstance(obs["note"], str) and len(obs["note"]) > 20


#: SHA-256 over the canonical JSON of every `observed` block (with its owning
#: `(file, proto_path)`) plus `orphan_observations`. Re-derive with:
#:
#:   uv run python -c "import json,hashlib; d=json.load(open('corpus/observation/classes.json')); \
#:   obs=[{'file':r['file'],'proto_path':r['proto_path'],'observed':r['observed']} \
#:   for r in d['candidates'] if 'observed' in r]; \
#:   print(hashlib.sha256(json.dumps({'observed':obs,'orphans':d.get('orphan_observations',[])}, \
#:   sort_keys=True,ensure_ascii=True).encode('ascii')).hexdigest())"
# 57 blocks / 7 orphans at the M6 close; 56 / 8 after M7 task 6, 54 / 10
# after M7 task 7, 52 / 12 after M7 task 8, 50 / 14 after M7 task 9, and
# 48 / 16 after M7 task 10 (2026-08-16: the key-staged-below-table barrier
# certified snr_s3_10_s:main_59 + its root and the NEWTABLE-position
# lookahead certified snr_common:main_29 -- their observation records moved
# to orphan quarantine (preserved, not lost).
# Re-derived 2026-08-16 with the command above.
_OBSERVED_DIGEST = "acbd1ef8bbe2e56a47e344e41db366d08c98af71ea7bb453c65baaadc476ea7f"


def test_the_observed_half_is_pinned_by_digest():
    """Completes the fixed point. `test_classes_json_is_a_reproducible_fixed_
    point` regenerates the MECHANICAL half and then re-inserts the committed
    `observed` blocks by hand -- it has to, because nothing generates them --
    so an edit INSIDE an observed block passes it silently (M6 final review,
    item 19).

    There is no generator to check them against, so the check is a digest:
    changing a reviewer's note, a `class_agrees` verdict, or the orphan list
    now requires changing this literal in the same commit, which puts the edit
    in the diff as a deliberate act instead of a byte nobody adjudicated.
    Measured 2026-08-14: 57 observed blocks, 7 orphans; 56 / 8 after M7
    task 6, 54 / 10 after task 7, 52 / 12 after task 8, 50 / 14 after
    task 9, 48 / 16 after task 10 (2026-08-16).
    """
    import hashlib
    doc = json.loads(CLASSES.read_text())
    obs = [{"file": r["file"], "proto_path": r["proto_path"],
            "observed": r["observed"]}
           for r in doc["candidates"] if "observed" in r]
    orphans = doc.get("orphan_observations", [])
    assert (len(obs), len(orphans)) == (48, 16)
    blob = json.dumps({"observed": obs, "orphans": orphans},
                      sort_keys=True, ensure_ascii=True)
    assert hashlib.sha256(blob.encode("ascii")).hexdigest() == _OBSERVED_DIGEST, (
        "the hand-authored observed half of classes.json changed. If that was "
        "intended, re-derive _OBSERVED_DIGEST with the command above and say "
        "in the commit message what was reviewed.")


def test_a_loop_is_a_header_not_a_back_edge(doc):
    """`n_natural_loops` counts loop HEADERS; `n_back_edges` counts back
    edges, and the two differ on real records (a `while` whose tail luac wrote
    out twice has one header and several latches). Counting back edges as
    loops published a false structural claim about
    `snr_common.lua:main_76_2` -- see `poll_loops`' docstring."""
    for r in doc["candidates"]:
        m = r["mechanical"]
        assert m["n_back_edges"] >= m["n_natural_loops"]
        assert len(m["poll_loops"]) <= m["n_natural_loops"]
        headers = [p["header_block"] for p in m["poll_loops"]]
        assert len(set(headers)) == len(headers), (r["file"], headers)
        for p in m["poll_loops"]:
            assert set(p) == {"header_block", "back_edge_blocks", "poll_pc"}
            assert p["back_edge_blocks"]
            assert p["back_edge_blocks"] == sorted(p["back_edge_blocks"])
    assert any(m["n_back_edges"] > m["n_natural_loops"]
               for m in (r["mechanical"] for r in doc["candidates"])), \
        "no record distinguishes the two counts -- the field split is untested"


def test_per_iteration_polling_follows_from_its_own_evidence(doc):
    """The Class-1/Class-2 overlap is a published number, so it has to be
    recoverable from the record rather than taken on trust."""
    for r in doc["candidates"]:
        m = r["mechanical"]
        expected = bool(m["poll_loops"]) or bool(m["in_loop_callees_reaching_poll"])
        assert m["loop_polls_per_iteration"] == expected, (r["file"],
                                                           r["proto_path"])
    census = {}
    for r in doc["candidates"]:
        m = r["mechanical"]
        if m["loop_polls_per_iteration"]:
            census[m["class"]] = census.get(m["class"], 0) + 1
    assert doc["summary"]["candidates_polling_per_iteration"] == census


def test_every_record_carries_task_3s_interaction_surface(doc):
    """The brief's Step-1 deliverable: the stub-call set and table-key read
    set from `corpus/observation/footprints.json`, joined by
    `(file, proto_path)`. `channels` is the branch-reaching SUBSET and does
    not replace it."""
    for r in doc["candidates"]:
        fp = r["mechanical"]["footprint"]
        assert set(fp) == {"global_reads", "table_key_reads", "calls",
                           "table_key_calls", "dynamic_reads", "read_sites",
                           "call_sites"}
        for pair in fp["table_key_reads"] + fp["table_key_calls"]:
            assert len(pair) == 2


def test_an_option_call_site_records_whether_it_is_polled_in_a_loop(doc):
    """`in_loop` exists because the plan's original reading of `input_space`
    for Class 1 ("fix one value per channel, run once") was falsified by the
    corpus. Every option call site carries the flag so the claim is checkable
    per site."""
    for r in doc["candidates"]:
        for o in r["mechanical"]["option_calls"]:
            assert set(o) == {"callee", "pc", "in_loop"}
            assert isinstance(o["in_loop"], bool)
            assert o["pc"] >= 1


def test_every_option_callee_resolves_to_a_proto(doc):
    """A `null` here means `OPTION_CALLEES` names something the corpus does not
    define, i.e. the vocabulary has drifted away from the call graph."""
    for name, target in doc["summary"]["option_callee_targets"].items():
        assert target is not None, name
        assert ":" in target


def test_the_committed_document_is_printable_ascii_throughout(doc):
    """The red line, checked on the artifact rather than on the emission
    sites. `footprints.json` measured `non_identifier_names == 0` over all 229
    files, so this cannot currently fail on corpus content -- it is here to
    catch a future field that interpolates a constant."""
    blob = CLASSES.read_bytes()
    bad = [b for b in blob if not (0x20 <= b <= 0x7e or b == 0x0a)]
    assert bad == []


def test_ascii_guard_actually_refuses_a_non_ascii_document():
    """Proof that the generator's belt is load-bearing rather than decorative:
    the corpus cannot reach it, so this is the only evidence it works."""
    mod = _cli()
    mod._assert_ascii({"a": ["ok", {"b": "also ok"}]})       # no raise
    with pytest.raises(AssertionError) as exc:
        mod._assert_ascii({"a": ["ok", {"b": "not é ok"}]})
    assert "doc.a[1].b" in str(exc.value)


def test_cfg_cache_entries_pin_their_proto():
    """`cfg_of` keys on `id(proto)`, so an entry that did not hold a reference
    would let CPython recycle the address and serve one proto's CFG for
    another. Measured failure of the unpinned version: `IndexError: tuple index
    out of range` inside `GETGLOBAL` handling, from indexing one proto's
    constants with another proto's operand. This asserts the shape of the fix;
    the failure itself is not deterministically reproducible."""
    from tests.synth import mk_instr, mk_proto
    from pyluadec.lift.opcodes import Op
    mod = _cli()
    p = mk_proto([mk_instr(Op.RETURN, 0, 1).word])
    mod.cfg_of(p)
    entry = mod._CFG_CACHE[id(p)]
    assert entry[0] is p


# ------------------------------------------------------------------ corpus arms

def _real_footprints():
    doc = json.loads(
        (ROOT / "corpus" / "observation" / "footprints.json").read_text())
    return {(fe["file"], pr["proto_path"]): pr
            for fe in doc["files"] for pr in fe["protos"]}


def _real_ledger():
    out = {}
    with (ROOT / "corpus" / "ledger.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            for occ in row["occurrences"]:
                out[(occ["file"], occ["proto_path"])] = (row, occ)
    return out


@pytest.mark.timeout(300)
def test_classes_json_is_a_reproducible_fixed_point(corpus_dir, tmp_path, monkeypatch):
    """The committed file is byte-reproducible from its own generator, AND its
    mechanical half does not depend on its observed half. Both from ONE
    whole-corpus run.

    **In the default suite, and the round-1 decision is why.** Round 0 gated
    this out on measured grounds: it cost +4.0s against a 45s ceiling. Two
    things changed. The ceiling was raised to ~120s (CLAUDE.md, `d97e3bc`) as
    an EARMARK for M6's formal-verification instruments, so at ~44s there is
    no longer any competition for the earmarked headroom; and the round-1
    review demonstrated by neuter/restore that this test is the ONLY thing
    that catches a whole class of mutation -- perturbing `mechanical.n_insns`
    passes the entire default suite and fails only here. That is the same
    argument the coordinator accepted for `tests/test_footprint.py`'s 0.9s
    regeneration, applied to the same kind of artifact.

    **The attribution, stated because the earmark requires it:** ~2.4s, for
    the fixed-point gate of the observation data Task 7 and Task 8 consume.
    That is adjacent to the earmark rather than squarely inside it -- this is
    not itself one of the named instruments -- and it is flagged as such in
    `docs/reports/m6-observation.md` so it can be overruled without
    archaeology.

    The run is `--fresh`, i.e. with the observation store empty, so what comes
    out is the mechanical half alone. Re-inserting the committed `observed`
    records -- the only thing a normal run does differently, and the only place
    an observation is allowed to touch the output -- must then give back the
    committed bytes exactly. So a generator that computed anything from an
    observation, or that rewrote one, fails here.

    That the generator's own carry-over code performs that re-insertion
    correctly is a separate, cheap test below.

    Runs against a scratch ROOT so the committed file is never touched as a
    side effect (the `tests/test_ledger_ratchet.py` precedent). `read_ledger`
    reads `ROOT/corpus/ledger.jsonl`, which the scratch tree does not have, so
    it is pointed back at the real one rather than copying 1478 rows.
    """
    mod = _cli()
    (tmp_path / "corpus" / "observation").mkdir(parents=True)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(corpus_dir))
    monkeypatch.setattr(mod, "read_ledger", lambda: _real_ledger())
    monkeypatch.setattr(mod, "read_footprints", lambda: _real_footprints())
    monkeypatch.setattr(sys, "argv", ["observation_classes.py", "--fresh"])
    assert mod.main() == 0
    fresh = json.loads(
        (tmp_path / "corpus" / "observation" / "classes.json").read_text())
    committed = json.loads(CLASSES.read_text())

    for r in fresh["candidates"]:
        assert "observed" not in r
    assert fresh["summary"]["n_observed_records"] == 0

    observed = {(r["file"], r["proto_path"]): r["observed"]
                for r in committed["candidates"] if "observed" in r}
    live = {(r["file"], r["proto_path"]) for r in fresh["candidates"]}
    for r in fresh["candidates"]:
        obs = observed.get((r["file"], r["proto_path"]))
        if obs is not None:
            r["observed"] = obs
    fresh["summary"]["n_observed_records"] = len(observed)
    # An observation whose proto has LEFT the candidate set is an orphan, not a
    # loss: the generator moves it to `orphan_observations` rather than
    # dropping it. Seven are quarantined as of M6 task 12, in two batches and
    # for two different reasons -- re-measured 2026-08-14, because the earlier
    # wording here ("Five ... all of which certified `L3`") was both the wrong
    # count and the wrong rule once the second batch arrived:
    #
    #   * five at M6 task 11 -- `snr_common.lua:main_74_13`, `main_76_8`,
    #     `main_81`, `snr_fragment_main.lua:main_1` and
    #     `snr_story_main.lua:main_1`. All five certify `L3`, so they are no
    #     longer non-`L3` candidates.
    #   * two at M6 task 12 -- `snr_mainmenu.lua:main_2`, which certifies `L3`
    #     like the first batch, and `snr_graphic.lua:main`, which **does
    #     not**: it is still `L1`, but its reason moved to
    #     `mismatch: maxstacksize at root/2`, which `refusal_origin` reads as
    #     `inherited`, so it stopped being a LEAF refusal. Leaving the
    #     candidate set does not require certifying.
    #
    # Reconstructed here for the same reason the
    # `observed` records are: this test's claim is that the generator computes
    # NOTHING from an observation, so every observation-derived field has to be
    # re-inserted by hand and still reproduce the committed bytes.
    orphans = sorted(
        (dict(committed_orphan) for committed_orphan in
         committed.get("orphan_observations", [])),
        key=lambda o: (o["file"], o["proto_path"]))
    if orphans:
        fresh["orphan_observations"] = orphans
        fresh["summary"]["n_orphan_observations"] = len(orphans)
    assert {(o["file"], o["proto_path"]) for o in orphans}.isdisjoint(live), \
        "an orphan is an observation whose proto is no longer a candidate"
    assert json.dumps(fresh, indent=1, ensure_ascii=True) + "\n" \
        == CLASSES.read_text()


@pytest.mark.timeout(120)
def test_a_regeneration_carries_observed_records_across(corpus_dir, tmp_path,
                                                        monkeypatch):
    """The generator's own carry-over path, end to end, over a ONE-FILE corpus
    so it costs a fraction of a second instead of repeating the whole-corpus
    run above.

    Round 1 (`--fresh`) produces mechanical-only records. An `observed` block
    is then written into the scratch file by hand -- which is exactly how a
    review adds one. Round 2 (normal) must give back byte-identical mechanical
    halves AND the hand-written observation, unedited.
    """
    mod = _cli()
    one = tmp_path / "corpus_one"
    one.mkdir()
    src = corpus_dir / "snr_music.lua"
    (one / src.name).write_bytes(src.read_bytes())
    (tmp_path / "corpus" / "observation").mkdir(parents=True)
    dest = tmp_path / "corpus" / "observation" / "classes.json"
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(one))
    monkeypatch.setattr(mod, "read_ledger", lambda: _real_ledger())
    monkeypatch.setattr(mod, "read_footprints", lambda: _real_footprints())

    monkeypatch.setattr(sys, "argv", ["observation_classes.py", "--fresh"])
    assert mod.main() == 0
    round1 = json.loads(dest.read_text())
    assert round1["candidates"], "one-file corpus produced no candidate"

    # The real schema (`test_observed_records_have_the_reviewed_shape`); an
    # earlier version wrote `reviewed`, which nothing here validates, so the
    # test would have passed over a block the committed file could not hold.
    note = {"reviewed_by": "test", "class_agrees": True,
            "note": "synthetic observation for the carry-over round trip"}
    round1["candidates"][0]["observed"] = note
    round1["summary"]["n_observed_records"] = 1
    dest.write_text(json.dumps(round1, indent=1, ensure_ascii=True) + "\n")

    monkeypatch.setattr(sys, "argv", ["observation_classes.py"])
    assert mod.main() == 0
    round2 = json.loads(dest.read_text())
    assert round2["candidates"][0]["observed"] == note
    assert round2["summary"]["n_observed_records"] == 1
    assert [r["mechanical"] for r in round2["candidates"]] \
        == [r["mechanical"] for r in round1["candidates"]]
    assert sum(1 for r in round2["candidates"] if "observed" in r) == 1
    assert round2["summary"]["n_orphan_observations"] == 0


@pytest.mark.timeout(120)
def test_an_observation_whose_candidate_is_gone_is_quarantined_not_dropped(
        corpus_dir, tmp_path, monkeypatch, capsys):
    """The realistic trigger is the milestone's own goal: a proto certifies
    `L3`, leaves the leaf-refusal population, and its human-reviewed note has
    nothing to attach to. The first version dropped it silently -- 162 records
    and 64 observations regenerated to 1 and 1 with exit 0 and no warning.

    A quarantined observation is also RE-ATTACHED if its candidate comes back,
    which is the half that makes the quarantine a fix rather than a graveyard,
    so this checks the round trip.
    """
    mod = _cli()
    one = tmp_path / "corpus_one"
    one.mkdir()
    src = corpus_dir / "snr_music.lua"
    (one / src.name).write_bytes(src.read_bytes())
    (tmp_path / "corpus" / "observation").mkdir(parents=True)
    dest = tmp_path / "corpus" / "observation" / "classes.json"
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(one))
    monkeypatch.setattr(mod, "read_ledger", lambda: _real_ledger())
    monkeypatch.setattr(mod, "read_footprints", lambda: _real_footprints())

    monkeypatch.setattr(sys, "argv", ["observation_classes.py", "--fresh"])
    assert mod.main() == 0
    doc = json.loads(dest.read_text())
    note = {"reviewed_by": "test", "class_agrees": True,
            "note": "an observation on a candidate that is about to vanish"}
    doc["candidates"][0]["observed"] = note
    gone = (doc["candidates"][0]["file"], doc["candidates"][0]["proto_path"])
    doc["summary"]["n_observed_records"] = 1
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=True) + "\n")

    # Now regenerate over a corpus that does NOT contain that file at all.
    other = tmp_path / "corpus_other"
    other.mkdir()
    src2 = corpus_dir / "snr_lib.lua"
    (other / src2.name).write_bytes(src2.read_bytes())
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(other))
    monkeypatch.setattr(sys, "argv", ["observation_classes.py"])
    capsys.readouterr()
    assert mod.main() == 0
    err = capsys.readouterr().err
    orphaned = json.loads(dest.read_text())
    assert orphaned["summary"]["n_orphan_observations"] == 1
    assert orphaned["orphan_observations"] == [
        {"file": gone[0], "proto_path": gone[1], "observed": note}]
    assert f"{gone[0]}:{gone[1]}" in err
    assert "NO LONGER MATCH A CANDIDATE" in err

    # ... and it comes back when the candidate does.
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(one))
    assert mod.main() == 0
    back = json.loads(dest.read_text())
    assert back["summary"]["n_orphan_observations"] == 0
    assert "orphan_observations" not in back
    assert [r for r in back["candidates"]
            if (r["file"], r["proto_path"]) == gone][0]["observed"] == note


@pytest.mark.timeout(300)
def test_leaf_refusal_rule_agrees_with_an_independent_stubbing_experiment(corpus_dir):
    """`refusal_origin` decides "own vs inherited" by three rules over the
    ledger's `refusal_reason`. This checks it against a different question
    entirely: replace every subproto with a trivial `function(...) end` of the
    same arity, re-print the proto, and see whether the same refusal survives.

    The two disagree by construction on `mismatch` rows -- a comparison
    rejection is not a print refusal, so the stubbed print succeeds there and
    the rule falls back to `Mismatch.path`. So the assertion is: on every row
    whose reason is a PRINT refusal (`structure:` / `reconstruct:`), surviving
    the stub is exactly `refusal_origin == "own"`, and the surviving message is
    byte-identical to the ledger's.
    """
    from pyluadec import ingest
    from pyluadec.pipeline import walk_proto_paths
    from pyluadec.lift.opcodes import Op
    from pyluadec.sir.build import StructureError
    from pyluadec.express.reconstruct import ReconstructError
    from pyluadec.emit.lua import _print_proto_body
    from tests.synth import mk_instr

    mod = _cli()
    ret = mk_instr(Op.RETURN, 0, 1).word
    ledger = _real_ledger()
    non_l3 = {}
    protos: dict[tuple[str, str], object] = {}
    for f in sorted({k[0] for k, (r, _o) in ledger.items() if r["level"] != "L3"}):
        tree: dict = {}
        walk_proto_paths("main", ingest.load_file(corpus_dir / f), tree)
        for path, p in tree.items():
            protos[(f, path)] = p
    for k, (row, _occ) in ledger.items():
        if row["level"] != "L3" and k in protos:
            non_l3[k] = (row, protos[k])

    # 48 before M6 task 11 closed 20 of the 21 `structure:` shapes (7 to `L3`,
    # 13 to `mismatch:`), then 41 before task 12's constructor/capture
    # classification fixes lifted one more, 40 at the M6 close (2026-08-14);
    # 39 after M7 task 6's dynamic-key constructor fix certified
    # config.lua:main; 35 after M7 task 7's skipped-kill veto certified the
    # clamp family; 33 after M7 task 8's staging-span exemption certified
    # snr_graphic:main_2 and snr_memory:main_2 (2026-08-15); 28 after M7
    # task 9's reaching-definition `>` recogniser and hint-0 constructor
    # budget gate; 22 after M7 task 10's key-staged-below-table barrier and
    # NEWTABLE-position lookahead (2026-08-16).
    assert len(non_l3) == 22, len(non_l3)
    checked = 0
    for (f, path), (row, p) in sorted(non_l3.items()):
        kind = row["refusal_reason"].split(":", 1)[0]
        stubbed = dataclasses.replace(p, subprotos=tuple(
            dataclasses.replace(s, code=(ret,), constants=(), lineinfo=(),
                                locvars=(), maxstacksize=max(2, s.numparams + 1),
                                subprotos=())
            for s in p.subprotos))
        try:
            _print_proto_body(stubbed, depth=1,
                              upval_names=tuple(f"u{i}" for i in range(p.nups)))
            survived = None
        except StructureError as exc:
            survived = f"structure: {exc}"
        except ReconstructError as exc:
            survived = f"reconstruct: {exc}"
        origin = mod.refusal_origin(f, path, row, non_l3)
        if kind in ("structure", "reconstruct"):
            checked += 1
            assert (survived is not None) == (origin == "own"), (f, path, origin)
            if survived is not None:
                assert survived == row["refusal_reason"], (f, path)
        else:
            assert survived is None, (f, path, survived)
    # 26 before M6 task 11: 21 `structure:` + 5 `reconstruct:`. The
    # condition-tree recognizer left 1 + 5 (2026-08-14); empty after M7
    # task 7's clamp fix, 4 again after M7 task 8 moved snr_graphic/memory's
    # ancestor+ sibling rows from `mismatch:` to `reconstruct:` refusals
    # (still L1 either way; 2026-08-15) -- plus the 2 `structure:` rows.
    assert checked == 6, checked

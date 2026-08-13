"""Guards for `corpus/observation/classes.json` and its generator (M6 task 4).

Three kinds of assertion, deliberately separated:

1. **Schema and internal coupling** over the committed file alone (no corpus
   needed). These are what catch a hand edit, a half-applied schema change, or
   a class assignment that stopped matching its own evidence.
2. **The fixed point** -- the committed file is byte-reproducible from
   `scripts/observation_classes.py`. The reason is the one recorded at
   `tests/test_ledger_ratchet.py` and `tests/test_footprint.py`: committed
   generated data that nothing regenerates rots, and a real two-line
   regression arrives buried in noise. **Unlike those two it is NOT in the
   per-commit suite** -- it is a whole-corpus pass that measured +4.0s against
   a 45s ceiling, so it is gated on `PYLUADEC_OBSERVATION_FIXED_POINT` and
   runs as gate 4 of `scripts/ratchet_job.sh`. The measurement and the
   departure are argued at the test itself.
3. **An independent cross-check of the leaf-refusal rule**, because that rule
   is the one piece of candidate selection that is an inference rather than a
   reading (see `observation_classes.refusal_origin`).
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
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
    assert set(doc) == {"version", "summary", "candidates"}
    assert doc["summary"]["n_candidates"] == len(doc["candidates"])


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

def _real_ledger():
    out = {}
    with (ROOT / "corpus" / "ledger.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            for occ in row["occurrences"]:
                out[(occ["file"], occ["proto_path"])] = (row, occ)
    return out


JOB_ENV = "PYLUADEC_OBSERVATION_FIXED_POINT"


@pytest.mark.timeout(300)
@pytest.mark.skipif(
    not os.environ.get(JOB_ENV),
    reason=f"whole-corpus regeneration; set {JOB_ENV}=1, or run "
           "./scripts/ratchet_job.sh which does")
def test_classes_json_is_a_reproducible_fixed_point(corpus_dir, tmp_path, monkeypatch):
    """The committed file is byte-reproducible from its own generator, AND its
    mechanical half does not depend on its observed half. Both from ONE
    whole-corpus run.

    **Gated out of the per-commit suite, and the measurement is why.** The run
    costs 2.3s standalone and measured **+4.0s** on the whole suite (913 passed
    in 44.85-44.88s with, 896 in 40.81-40.90s without, two A/B pairs on this
    host), i.e. it put a 45s ceiling at 44.9s. The plan's own rule is that a
    corpus-wide pass is a JOB, not a silent per-run suite cost; this is one, so
    it runs on `scripts/ratchet_job.sh` (gate 4) with the rest of them. The
    cheap half of this file -- schema, class-vs-evidence coupling, the
    input-space arithmetic, the ASCII guard, the observation carry-over over a
    ONE-FILE corpus, and the leaf-refusal cross-check -- stays in the suite and
    costs 0.4s.

    This is a deliberate departure from `tests/test_footprint.py`'s 0.9s
    regeneration, which the coordinator ruled stays in the suite. The
    difference is the number, not the principle.

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
    for r in fresh["candidates"]:
        obs = observed.get((r["file"], r["proto_path"]))
        if obs is not None:
            r["observed"] = obs
    fresh["summary"]["n_observed_records"] = len(observed)
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

    monkeypatch.setattr(sys, "argv", ["observation_classes.py", "--fresh"])
    assert mod.main() == 0
    round1 = json.loads(dest.read_text())
    assert round1["candidates"], "one-file corpus produced no candidate"

    note = {"reviewed": True, "class_agrees": True, "note": "synthetic"}
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

    assert len(non_l3) == 48, len(non_l3)
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
    assert checked == 26, checked

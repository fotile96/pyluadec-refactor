"""M6 exit gate.

Same contract as `tests/test_m3_exit.py`, `test_m4_exit.py` and
`test_m5_exit.py`, none of which this file replaces: M3's `> 0.50`, M4's
`> 0.85` and M5's `0.94 / 0.96 / 0.85 / 0.96` floors all stay asserted where
they are. **The thresholds here are milestone COMMITMENTS, not
measurements.** Each sits deliberately below its achieved value and states
that value in its own assert message. If one goes red the fix is in the
decompiler or in the observation data, not in the number: M5 measured that a
floor set AT the measurement is a tripwire, and the standard repair for a
tripwire is to edit the threshold, which is how a gate stops meaning
anything.

## What M6 committed, and therefore what is gated here

M6's spec (`docs/superpowers/specs/2026-08-13-m6-cross-corpus-validation-
design.md` §3) exits on four things. Three of them are asserted below and the
fourth is asserted by measurement elsewhere:

1. **Track 1.0 observation complete** -- `corpus/observation/classes.json`
   covers every leaf refusal and every CAP-dominant proto.
   `test_m6_exit_observation_covers_every_leaf_refusal` and
   `..._every_cap_file`.
2. **The divergence queue is adjudicated** --
   `test_m6_exit_every_divergence_is_adjudicated`.
3. **`L3` does not regress** -- `test_m6_exit_l3_no_regression_unique`.
4. Track 3's two defects: closed or re-characterised with a measurement. That
   one is not a threshold, it is a signal, and it lives where it can actually
   fail: `tests/test_semantic_regressions.py::
   test_if_and_elseif_conjunctions_preserved` (moved `L1` -> `L3` by task 11)
   and `tests/test_express_aliasing.py` (task 12).

## What this file deliberately does NOT assert, and why

* **Reconstruction coverage.** The plan's exit sketch carried
  `test_m6_exit_reconstruction_coverage(recon_index)` -- "~20/~20 leaves"
  from Task 10's LLM meta-reconstruction. **Tasks 9 and 10 were dropped on
  2026-08-14 with their premise falsified by measurement** (`build_sir`
  succeeds on 12 of the predecessor's 13 corresponding leaf protos, 92.3%, so
  the mechanical reference is essentially free and the ~1-2M-token pass buys
  nothing). There is no `docs/reports/m6-reconstruction/` and no index to
  assert over. Recorded here rather than silently omitted; see the spec's §2
  decision log.
* **The quality score.** M6 removed `avg_score >= 0.997` as a gate (human
  partner, 2026-08-13; spec §2 decision log) and kept it as a dashboard
  observable. It measures **0.977328** at this tree (`scripts/quality_score.py`,
  2026-08-14), and `test_m5_exit.py::test_m5_exit_quality_no_regression`
  already re-derives it against a 0.96 floor at a cost of 229 `luac_sz4`
  runs. Computing it a second time here would double the most expensive check
  in the exit family to assert a floor that is already asserted.
* **Occurrence `L3` and structured reach.** M5's floors (0.96 and 0.85) carry
  unchanged; achieved at this tree are **1904/1944 (97.94%)** and
  **1763/1944 (90.69%)**. M6 tightened neither, because neither is what M6
  was about, and re-stating a floor at its existing value in a second file
  buys nothing but a second place to edit.

## What this file is worth on its own, and what it borrows

`test_m6_exit_l3_no_regression_unique` reads the committed
`corpus/ledger.jsonl` and re-derives nothing, so on its own it proves that a
committed JSON file says the right thing. Its force is borrowed from
`tests/test_ledger_ratchet.py`, which re-runs the whole corpus pipeline and
requires the committed ledger to come back byte-identical; treat the two as
one gate, exactly as `test_m4_exit.py`'s and `test_m5_exit.py`'s docstrings
spell out.

The two observation tests are different in kind: they are a **cross-artifact
join**, and neither artifact can satisfy them alone. `classes.json` is
generated from the corpus and the ledger; if a decompiler change moves a
refusal and the observation data is not regenerated, the join goes red here
even though each file is internally consistent and
`tests/test_observation_classes.py`'s own schema gates stay green. That is
the rot mode this pair exists for, and it needs no corpus to catch it.
"""
from __future__ import annotations

import collections
import copy
import json
from pathlib import Path

import pytest

from scripts import cross_corpus

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "corpus" / "ledger.jsonl"
CLASSES = ROOT / "corpus" / "observation" / "classes.json"

#: The one ledger floor M6 sets for itself. M5's is 0.94; achieved at this
#: tree is 1438/1478 = **97.29%**, so 0.96 is **19 rows** of margin (0.96 *
#: 1478 = 1418.88, i.e. 1419 rows would still pass). That is thinner than the
#: 41 rows M5 left itself and it is a deliberate trade: 0.96 is also the
#: coarse statement "M6 must not end below where M5 ended" (M5 achieved
#: 96.8%), and 19 rows is the smallest headroom this project has been willing
#: to call a commitment rather than a tripwire. The fine-grained instrument is
#: not this floor and never was -- `scripts/ratchet_diff.py` fails on a SINGLE
#: row's downgrade against a committed baseline, which is strictly stronger
#: than any aggregate.
UNIQUE_L3_FLOOR = 0.96


def _rows():
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def _classes():
    return json.loads(CLASSES.read_text())


# --------------------------------------------------------------------------
# Pure functions. Every gate below is a call to one of these over parsed data,
# so that the same code can be driven over MUTATED data and required to go red
# -- an assertion written inline over a committed artifact only ever runs
# against data that satisfies it and so can never be shown to fail.
# --------------------------------------------------------------------------

def unique_l3(rows) -> tuple[int, int]:
    return sum(1 for r in rows if r["level"] == "L3"), len(rows)


def occurrence_index(rows) -> dict[tuple[str, str], dict]:
    return {(o["file"], o["proto_path"]): r
            for r in rows for o in r["occurrences"]}


def leaf_refusals(doc) -> set[tuple[str, str]]:
    return {(r["file"], r["proto_path"]) for r in doc["candidates"]
            if "leaf-refusal" in r["mechanical"]["selected_as"]}


def coverage_gaps(rows, doc) -> list[tuple]:
    """Every way the observation data can fail to cover the ledger's residual.

    Three directions, because a one-directional check is satisfiable by an
    empty artifact in one direction and by a stale one in the other:

    * **forward** -- every non-`L3` occurrence is accounted for: either it is
      itself a `leaf-refusal` candidate, or it is an ancestor that inherited
      its refusal, which is witnessed by a non-`L3` DESCENDANT that is one.
      Measured at this tree: 40 non-`L3` occurrences = 29 leaf refusals + 11
      inherited ancestors, and every one of the 11 has such a witness.
    * **backward** -- every `leaf-refusal` candidate really is a non-`L3`
      ledger occurrence, and carries the same `level` and `refusal_reason`
      the ledger does. This is what goes red when the decompiler moves a
      refusal and `classes.json` is not regenerated.
    * **the summary** -- `n_non_l3` agrees with the ledger it was derived
      from.

    The ancestor rule is `proto_path` prefixing (`main_76` -> `main_76_2`),
    which is `pipeline.walk_proto_paths`' convention and carries no corpus
    payload.
    """
    occ = occurrence_index(rows)
    non_l3 = {k for k, r in occ.items() if r["level"] != "L3"}
    leaves = leaf_refusals(doc)
    mech = {(r["file"], r["proto_path"]): r["mechanical"]
            for r in doc["candidates"]}
    gaps: list[tuple] = []

    for key in sorted(non_l3 - leaves):
        f, path = key
        witness = [q for (g, q) in non_l3
                   if g == f and q.startswith(path + "_") and (g, q) in leaves]
        if not witness:
            gaps.append(("uncovered-refusal", key))

    for key in sorted(leaves):
        row = occ.get(key)
        if row is None:
            gaps.append(("candidate-not-in-ledger", key))
            continue
        if row["level"] == "L3":
            gaps.append(("candidate-is-l3", key))
            continue
        if row["level"] != mech[key]["level"]:
            gaps.append(("level-disagrees", key))
        if row["refusal_reason"] != mech[key]["refusal_reason"]:
            gaps.append(("reason-disagrees", key))

    if doc["summary"]["n_non_l3"] != len(non_l3):
        gaps.append(("summary-n_non_l3", doc["summary"]["n_non_l3"],
                     len(non_l3)))
    return gaps


def cap_coverage_gaps(doc) -> list[tuple]:
    """Every file the behaviour probe capped contributed exactly one
    `cap-dominant` candidate.

    The probe's own census is not committed anywhere else, so what is checked
    here is the internal completeness statement `n_cap_dominants ==
    n_cap_files`, plus that the candidate list really does carry one record
    per distinct file. `tests/test_observation_classes.py`'s corpus-gated
    fixed-point test is what ties `n_cap_files` back to a live probe run.
    """
    s = doc["summary"]
    files = collections.Counter(
        r["file"] for r in doc["candidates"]
        if "cap-dominant" in r["mechanical"]["selected_as"])
    gaps: list[tuple] = []
    if s["n_cap_dominants"] != s["n_cap_files"]:
        gaps.append(("dominants-vs-files", s["n_cap_dominants"],
                     s["n_cap_files"]))
    if sum(files.values()) != s["n_cap_dominants"]:
        gaps.append(("record-count", sum(files.values()), s["n_cap_dominants"]))
    if len(files) != s["n_cap_files"]:
        gaps.append(("distinct-files", len(files), s["n_cap_files"]))
    dupes = sorted(f for f, n in files.items() if n > 1)
    if dupes:
        gaps.append(("two-dominants-for-one-file", tuple(dupes)))
    return gaps


def unadjudicated(pins) -> list[tuple[str, str, str]]:
    """Rows in `PRED_PINS` that are not a settled verdict.

    `suspect` is in `cross_corpus.VERDICTS` on purpose -- it is the honest
    answer while two stories fit the evidence -- and it is exactly what "the
    queue is adjudicated" excludes. A verdict outside the vocabulary is the
    other way the same commitment breaks.
    """
    out = []
    for arm, table in pins.items():
        for name, pin in table.items():
            if pin.verdict not in cross_corpus.VERDICTS:
                out.append((arm, name, pin.verdict))
            elif pin.verdict == "suspect":
                out.append((arm, name, pin.verdict))
    return sorted(out)


# --------------------------------------------------------------------------
# The gates
# --------------------------------------------------------------------------

def test_m6_exit_l3_no_regression_unique():
    """M5 exit **1430/1478 (96.8%)** -> **1438/1478 (97.29%) achieved**,
    measured 2026-08-14 by `scripts/ledger_dashboard.py` and by this test,
    which agree. Floor **0.96**, see `UNIQUE_L3_FLOOR` for why that number.

    The eight rows are M6 tasks 11 and 12; `scripts/ratchet_diff.py` against
    the M5 merge baseline `0957364` reports **8 upgraded, 0 downgraded** at
    this tree.
    """
    rows = _rows()
    assert rows
    num, den = unique_l3(rows)
    frac = num / den
    assert frac >= UNIQUE_L3_FLOOR, (
        f"unique L3 {num}/{den} = {frac:.2%}, floor {UNIQUE_L3_FLOOR:.0%}")


def test_m6_exit_observation_covers_every_leaf_refusal():
    """Spec §3's first exit clause, as a join rather than as a count.

    Achieved 2026-08-14: **29 leaf refusals** and **11 inherited ancestors**
    over the ledger's 40 non-`L3` rows. `classes.json` carries **156
    candidates**: 29 leaf refusals plus 132 CAP dominants, less the **5**
    protos that are in both populations.
    """
    gaps = coverage_gaps(_rows(), _classes())
    assert gaps == [], f"observation does not cover the ledger residual: {gaps}"


def test_m6_exit_observation_covers_every_cap_file():
    """Spec §3's first exit clause, other half: **132 of 132** behaviour-probe
    CAP files contributed a dominant proto (measured 2026-08-14)."""
    gaps = cap_coverage_gaps(_classes())
    assert gaps == [], f"CAP-dominant population is incomplete: {gaps}"


def test_m6_exit_every_divergence_is_adjudicated():
    """Spec §3's second exit clause. Achieved 2026-08-14: **18 rows over 16
    files**, verdicts **6 `real-bug` / 12 `equivalent-transform`**, zero
    `suspect`, zero `probe-artifact`.

    What this asserts is the COMMITMENT ("nothing is left unresolved"), not
    the histogram. `tests/test_cross_corpus.py::
    test_the_six_real_bug_verdicts_are_the_committed_headline` pins the exact
    counts, and it should: those are the milestone's payload. But that test is
    the one a nineteenth adjudicated row legitimately edits, and this
    commitment has to survive that edit -- so the two are deliberately not the
    same assertion.

    The floor on `real-bug` is 1 rather than 6 for the same reason, and it is
    not decoration: with six confirmed defects in shipped software, a table
    that adjudicated its way to zero of them would be a finding about the
    table.
    """
    bad = unadjudicated(cross_corpus.PRED_PINS)
    assert bad == [], f"divergence queue is not fully adjudicated: {bad}"
    counts = collections.Counter(
        pin.verdict for table in cross_corpus.PRED_PINS.values()
        for pin in table.values())
    assert counts["real-bug"] >= 1, (
        f"no `real-bug` verdict survives; histogram {dict(counts)}")


def test_the_floor_is_below_what_is_achieved_and_can_still_fail():
    """A floor is only a commitment if it is reachable from below, and only
    meaningful if it is not already tripped. A future edit that sets it AT the
    measurement -- the standard way a gate is quietly retired -- shows up here
    as a zero margin.

    Deliberately NOT asserting the achieved value itself: that is a
    measurement and it moves. What is asserted is the RELATION.
    """
    num, den = unique_l3(_rows())
    assert num / den > UNIQUE_L3_FLOOR, (
        f"unique L3 achieved {num/den:.4f} is AT or below its floor "
        f"{UNIQUE_L3_FLOOR}; a floor with no margin is a tripwire, not a "
        f"commitment")
    assert 0.0 < UNIQUE_L3_FLOOR < 1.0


def test_the_l3_floor_actually_rejects_a_worse_ledger():
    """Drive `unique_l3` -- the exact code the gate runs -- over rows mutated
    to look like a regression, and require the comparison to go red.

    The mutation is minimal and computed rather than guessed: demote exactly
    enough `L3` rows to cross the floor (**20** at this tree), and check that
    one fewer leaves the gate green. Without this, the only evidence the floor
    can fail is that it looks like it could (MEMORY.md, "guards must be proven
    load-bearing").
    """
    rows = copy.deepcopy(_rows())
    num, den = unique_l3(rows)
    assert num / den >= UNIQUE_L3_FLOOR                      # clean: green

    need = num - int(UNIQUE_L3_FLOOR * den)
    assert need >= 1
    demoted = []
    for r in rows:
        if len(demoted) >= need:
            break
        if r["level"] == "L3":
            r["level"] = "L1"
            demoted.append(r)
    assert len(demoted) == need, "could not construct a regression"

    n2, d2 = unique_l3(rows)
    assert n2 / d2 < UNIQUE_L3_FLOOR
    # ... and one demotion fewer does NOT trip it, which is what makes `need`
    # the floor's real crossing point rather than an overshoot.
    demoted[0]["level"] = "L3"
    n3, d3 = unique_l3(rows)
    assert n3 == n2 + 1 and n3 / d3 >= UNIQUE_L3_FLOOR


@pytest.mark.parametrize("mutation", ["drop-candidate", "wrong-reason",
                                      "wrong-level", "stale-summary",
                                      "orphan-candidate"])
def test_the_observation_coverage_check_rejects_each_way_it_can_rot(mutation):
    """Five ways the ledger/`classes.json` join can go stale, each required to
    be named by `coverage_gaps`. The five are not hypothetical shapes: they
    are what a decompiler change does to this pair if the observation data is
    not regenerated with it (a refusal closes, a refusal's reason changes, a
    refusal moves to another proto, the summary counter goes stale).
    """
    rows = copy.deepcopy(_rows())
    doc = copy.deepcopy(_classes())
    assert coverage_gaps(rows, doc) == []                    # clean: green

    leaves = sorted(leaf_refusals(doc))
    assert leaves, "no leaf refusals left -- this test needs re-scoping"
    victim = leaves[0]

    if mutation == "drop-candidate":
        doc["candidates"] = [r for r in doc["candidates"]
                             if (r["file"], r["proto_path"]) != victim]
        expected = "uncovered-refusal"
    elif mutation == "wrong-reason":
        for r in doc["candidates"]:
            if (r["file"], r["proto_path"]) == victim:
                r["mechanical"]["refusal_reason"] = "mismatch: not this one"
        expected = "reason-disagrees"
    elif mutation == "wrong-level":
        # The ledger upgraded this shape and the observation did not follow.
        occ = occurrence_index(rows)
        occ[victim]["level"] = "L3"
        occ[victim]["refusal_reason"] = None
        expected = "candidate-is-l3"
    elif mutation == "stale-summary":
        doc["summary"]["n_non_l3"] += 1
        expected = "summary-n_non_l3"
    else:
        for r in doc["candidates"]:
            if (r["file"], r["proto_path"]) == victim:
                r["proto_path"] = victim[1] + "_999"
        expected = "candidate-not-in-ledger"

    gaps = coverage_gaps(rows, doc)
    assert gaps, f"{mutation} was not caught"
    assert expected in {g[0] for g in gaps}, (mutation, gaps)


def test_the_cap_coverage_check_rejects_a_missing_dominant():
    """Same discipline for the CAP half: drop one dominant record and require
    `cap_coverage_gaps` to notice, then break the summary counter itself."""
    doc = copy.deepcopy(_classes())
    assert cap_coverage_gaps(doc) == []                      # clean: green

    caps = [r for r in doc["candidates"]
            if "cap-dominant" in r["mechanical"]["selected_as"]]
    assert caps
    doc["candidates"].remove(caps[0])
    assert {g[0] for g in cap_coverage_gaps(doc)} >= {"record-count",
                                                      "distinct-files"}

    doc2 = copy.deepcopy(_classes())
    doc2["summary"]["n_cap_files"] += 1
    assert "dominants-vs-files" in {g[0] for g in cap_coverage_gaps(doc2)}


def test_the_adjudication_check_rejects_an_unresolved_verdict():
    """`unadjudicated` over a tampered copy of the real pin table: a `suspect`
    row and a row with a verdict outside the vocabulary must each be named.
    The real table is never mutated -- `PRED_PINS` holds frozen `Pin`s and the
    copy replaces whole entries."""
    real = {arm: dict(table) for arm, table in cross_corpus.PRED_PINS.items()}
    assert unadjudicated(real) == []                         # clean: green

    arm = "fingerprint"
    name = sorted(real[arm])[0]
    old = real[arm][name]

    real[arm][name] = cross_corpus.Pin("suspect", old.evidence, old.note)
    assert unadjudicated(real) == [(arm, name, "suspect")]

    real[arm][name] = cross_corpus.Pin("probably-fine", old.evidence, old.note)
    assert unadjudicated(real) == [(arm, name, "probably-fine")]

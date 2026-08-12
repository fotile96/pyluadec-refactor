"""M5 exit gate.

Same contract as `tests/test_m3_exit.py` and `tests/test_m4_exit.py`, which
this file does not replace -- M3's `> 0.50` and M4's `> 0.85` floors stay
asserted, so a regression past them fails three times. **The thresholds here
are milestone COMMITMENTS, not measurements.** Each sits deliberately below
its achieved value and states the achieved value in its own assert message. If
one goes red the fix is in the decompiler, not in the number: editing a
threshold down to match what the tree currently does is how a gate stops
meaning anything, and this project has watched that happen to other people's
gates.

## What this file is worth on its own, and what it borrows

Three of the four tests read `corpus/ledger.jsonl` and re-derive nothing, so
on their own they prove that a committed JSON file says the right things.
Their force is borrowed from `tests/test_ledger_ratchet.py`, which re-runs the
whole corpus pipeline and requires the committed ledger to come back
byte-identical -- treat the two as one gate, exactly as `test_m4_exit.py`'s
docstring spells out. The fourth, `test_m5_exit_quality_no_regression`, is
different in kind: it re-decompiles all 229 files and recompiles each one
through the real `luac_sz4`, so it cannot be satisfied by a stale file.

## The exit criterion was RE-SCOPED, by the human partner, 2026-08-12

Spec §1 goal 4 set the acceptance bar at the predecessor's stated
`avg_score 0.997`. M5 task 3 ported the metric and measured **0.935633** at
milestone start; tasks 4, 5 and 6 moved it to 0.946390 -> 0.950580 ->
**0.968833**. The arithmetic then closed the original gate off: with 216 files
at exactly 1.000000, the remaining 13 must average >= 0.947, and converting
all 7 remaining whole-file fallbacks to hybrids *at the measured hybrid
quality of 0.816791* reaches only 0.9896. Clearing 0.997 needs essentially
every file at ~1.0 -- i.e. closing the reconstruction residual, which is M6's
work, not a different way of assembling chunks.

So M5 exits on metrics already on track and **0.997 is carried to M6 as its
exit**. That modifies a spec acceptance criterion the user confirmed section
by section, so it is recorded in the spec's own decision log
(`docs/superpowers/specs/2026-08-09-pyluadec-refactor-overall-design.md` §2),
not only here.

## What is deliberately NOT gated

The whole-file-fallback count. It went 17 -> **7** across M5 and is reported
as data in `docs/reports/m5-quality.md`; the 7 are blocked on their own ROOT
proto, which a hybrid substitution cannot replace, so gating on zero would be
gating on M6's work. The L2 badge likewise: measured reach is **one file**
(`snr_lib.lua`), and the two historical key-sequence checkpoints live in
`snr_common.lua`, which the L2 gate refuses `taint-static`. That is the honest
outcome and it is written down rather than legislated away.
"""
import json
from pathlib import Path

import pytest

LEDGER = Path(__file__).resolve().parents[1] / "corpus" / "ledger.jsonl"


def _rows():
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


# The three ledger-derived floors, as `name -> (numerator, denominator, floor)`
# computed by ONE pure function over already-parsed rows.
#
# Pure and parameterised on `rows` deliberately: an assertion written inline
# over the committed ledger only ever runs against data that satisfies it, so
# it cannot be shown to fail. `test_the_ledger_metrics_actually_reject_a_worse_ledger`
# feeds this same function rows that have been mutated to look like a
# regression, which is the only way the floors below are more than decoration.
LEDGER_FLOORS = {"unique L3": 0.96, "occurrence L3": 0.96, "structured reach": 0.85}

#: The fourth floor. Not in `LEDGER_FLOORS` because it is not derived from the
#: ledger at all -- `test_m5_exit_quality_no_regression` re-decompiles and
#: recompiles the whole corpus to get it.
QUALITY_FLOOR = 0.96


def ledger_metrics(rows) -> dict[str, tuple[int, int]]:
    occ = [o for r in rows for o in r["occurrences"]]
    return {
        "unique L3": (sum(1 for r in rows if r["level"] == "L3"), len(rows)),
        "occurrence L3": (sum(len(r["occurrences"]) for r in rows
                              if r["level"] == "L3"), len(occ)),
        "structured reach": (sum(1 for o in occ if o["shipped"] == "structured"),
                             len(occ)),
    }


def _check(rows, name):
    num, den = ledger_metrics(rows)[name]
    floor = LEDGER_FLOORS[name]
    frac = num / den
    assert frac >= floor, f"{name} {num}/{den} = {frac:.1%}, floor {floor:.1%}"


def test_m5_exit_l3_no_regression_unique():
    """M4 exit 94.0% unique -> **96.8% achieved** (1430/1478), measured
    2026-08-13. Floor 0.96."""
    rows = _rows()
    assert rows
    _check(rows, "unique L3")


def test_m5_exit_l3_no_regression_occurrences():
    """The un-deduplicated basis, for the reason `test_m4_exit.py` gives: the
    ledger keys by `structural_hash`, so its rows are proto SHAPES, and a
    change that certified only the rare shapes would move the unique rate
    without moving this one. M4 exit 95.4% -> **97.5% achieved** (1896/1944).
    Floor 0.96, and the denominator is pinned at `== 1944` because a filtered
    denominator has already hidden two real defects in this project."""
    rows = _rows()
    assert sum(len(r["occurrences"]) for r in rows) == 1944
    _check(rows, "occurrence L3")


def test_m5_exit_structured_reach():
    """Proto occurrences whose SHIPPED text came from the structured printer
    rather than the `__pld_pc` state machine. 70.9% at M5 start -> **89.9%
    achieved** (1747/1944), measured 2026-08-13. Floor 0.85.

    This is not the same question as `level`, and M5 task 6 is why: `level` is
    a per-proto proof record, `shipped` is a fact about the artifact, and
    hybrid emission decoupled them in both directions (6 rows are `L1` and
    ship structured; 150 rows are `L3` and ship the state machine because they
    live in one of the 7 whole-file-fallback files). A milestone whose headline
    was readability has to assert the artifact, not only the proof.
    """
    _check(_rows(), "structured reach")


def test_m5_exit_quality_no_regression(corpus_dir, decompiled):
    """The ported predecessor metric over all 229 files.

    M5 start **0.935633** -> **0.968833 achieved** (measured 2026-08-13 by
    this test and by `scripts/quality_score.py`, which agree to six decimals).
    Floor 0.96. NOT the predecessor's 0.997: that is M6's exit, see the module
    docstring and the spec decision log.

    This one really re-derives: each file is decompiled and its source is
    recompiled by the real `luac_sz4`, then scored against the original proto
    tree. It is the only test in this file a stale `corpus/ledger.jsonl` could
    not satisfy. Cost is paid mostly by the session `decompiled` fixture,
    which other corpus tests need anyway; the marginal cost measured here is
    the 229 `luac_sz4` runs plus the scoring, **2.1s** (2026-08-13, warm
    decompile cache), against a 45s suite ceiling.

    Why an aggregate rather than a per-file floor: per-row monotonicity is
    `scripts/ratchet_diff.py`'s job and it enforces it against a committed
    baseline, which a fixture cannot. This asserts that M5's aggregate gain is
    not given back.
    """
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes, load_file
    from pyluadec.verify.semantic_score import score_protos

    files = sorted(Path(corpus_dir).glob("*.lua"))
    assert len(files) == 229, len(files)
    total = 0.0
    for f in files:
        original = load_file(f)
        candidate = load_bytes(oracle.compile_source(decompiled(f).source))
        total += score_protos(original, candidate,
                              file_size=f.stat().st_size, small_kb=10).score
    avg = total / len(files)
    assert avg >= QUALITY_FLOOR, f"corpus average {avg:.6f}, floor {QUALITY_FLOOR:.6f}"
    # The margin half of `test_the_floors_are_below_what_is_achieved...`, made
    # here rather than there because re-deriving this number costs 229
    # `luac_sz4` runs and doing it twice would double the most expensive test
    # in the file (M5 task 12 round 1, minor 5). It is the THINNEST margin of
    # the four floors and the ONLY one that can move without the ledger
    # moving -- `semantic_score` is a coarsening of the certification
    # comparison, so a reconstruction change can shift it while every `level`
    # stays put -- which is exactly why it needs the check rather than why it
    # can skip it. A strict `>` is the whole assertion: a floor set AT the
    # measurement is a tripwire, and the standard repair for a tripwire is to
    # edit the threshold.
    assert avg > QUALITY_FLOOR, (
        f"corpus average {avg:.6f} is AT or below its floor {QUALITY_FLOOR:.6f}; "
        f"a floor with no margin is a tripwire, not a commitment")


def test_the_floors_are_below_what_is_achieved_and_can_still_fail():
    """The floors are only commitments if they are reachable from below, and
    only meaningful if they are not already tripped. A future edit that sets a
    floor AT the measurement -- the standard way a gate is quietly retired --
    shows up here as a zero margin.

    Covers the **three ledger-derived** floors. The fourth, the quality floor,
    asserts its own margin inside
    `test_m5_exit_quality_no_regression` rather than here, because re-deriving
    it costs 229 `luac_sz4` runs and doing it in two places would double the
    file's cost (M5 task 12 round 1, minor 5).

    Deliberately NOT asserting the achieved values themselves -- those are
    measurements and they move. What is asserted is the RELATION.
    """
    rows = _rows()
    for name, (num, den) in ledger_metrics(rows).items():
        floor = LEDGER_FLOORS[name]
        assert num / den > floor, \
            f"{name}: achieved {num/den:.4f} is AT or below its floor {floor}"
        assert 0.0 < floor < 1.0


@pytest.mark.parametrize("name", sorted(LEDGER_FLOORS))
def test_the_ledger_metrics_actually_reject_a_worse_ledger(name):
    """Drive `ledger_metrics` + `_check` -- the exact code the three
    ledger-derived gates run -- over rows mutated to look like a regression,
    and require each to go red.

    This replaces a version that asserted `(frac >= floor) is ok` over literal
    constants, i.e. that tested Python's `>=` rather than anything in this
    file, and could be deleted with a green tree and nothing lost (M5 task 12
    round 1, minor 6). The committed ledger satisfies all three gates, so
    without this the only evidence they can fail is that they look like they
    could.

    The mutation is per metric and minimal: demote enough `L3` rows, or flip
    enough `shipped` values, to cross that metric's floor -- then assert the
    OTHER metrics are untouched, which is what makes each gate's failure
    attributable to its own quantity rather than to a ledger that is broken
    everywhere.
    """
    import copy
    rows = copy.deepcopy(_rows())
    _check(rows, name)                                   # clean: green

    num, den = ledger_metrics(rows)[name]
    # Demotions needed to push `num/den` strictly below the floor. Computed,
    # not guessed: a first draft used `den - int(floor*den) + 1`, which is the
    # count of rows ALREADY below and needs 61 demotions where 12 suffice --
    # and 61 was enough to trip the sibling gate too, which is exactly the
    # confusion this test's second half exists to detect.
    need = num - int(LEDGER_FLOORS[name] * den)

    if name == "structured reach":
        for r in rows:
            for o in r["occurrences"]:
                if need <= 0:
                    break
                if o["shipped"] == "structured":
                    o["shipped"], need = "fallback", need - 1
    elif name == "unique L3":
        # Demote rows carrying ONE occurrence each, so the sibling occurrence
        # rate falls by as little as possible. Measured: 12 demotions cross
        # this floor, and 1896 - 12 = 1884 of 1944 = 96.9% keeps the sibling up.
        for r in rows:
            if need <= 0:
                break
            if r["level"] == "L3" and len(r["occurrences"]) == 1:
                r["level"], need = "L1", need - 1
    else:
        # Demote the FATTEST rows, so the occurrence rate crosses its floor
        # while the unique rate barely moves. Measured: the largest row alone
        # carries 292 occurrences against a 30-occurrence budget, so exactly
        # one row moves and unique goes 1430 -> 1429 of 1478 = 96.7%.
        for r in sorted(rows, key=lambda r: -len(r["occurrences"])):
            if need <= 0:
                break
            if r["level"] == "L3":
                r["level"], need = "L1", need - len(r["occurrences"])
    assert need <= 0, f"could not construct a {name} regression"

    with pytest.raises(AssertionError, match=name):
        _check(rows, name)

    # ... and ONLY that one. A mutation broad enough to trip every gate would
    # show the gates are not independent rather than that this one works.
    for other in LEDGER_FLOORS:
        if other != name:
            _check(rows, other)

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


def test_m5_exit_l3_no_regression_unique():
    """M4 exit 94.0% unique -> **96.8% achieved** (1430/1478), measured
    2026-08-13. Floor 0.96."""
    rows = _rows()
    assert rows
    l3 = sum(1 for r in rows if r["level"] == "L3")
    frac = l3 / len(rows)
    assert frac >= 0.96, f"unique L3 {l3}/{len(rows)} = {frac:.1%}, floor 96.0%"


def test_m5_exit_l3_no_regression_occurrences():
    """The un-deduplicated basis, for the reason `test_m4_exit.py` gives: the
    ledger keys by `structural_hash`, so its rows are proto SHAPES, and a
    change that certified only the rare shapes would move the unique rate
    without moving this one. M4 exit 95.4% -> **97.5% achieved** (1896/1944).
    Floor 0.96, and the denominator is pinned at `== 1944` because a filtered
    denominator has already hidden two real defects in this project."""
    rows = _rows()
    total = sum(len(r["occurrences"]) for r in rows)
    assert total == 1944
    l3 = sum(len(r["occurrences"]) for r in rows if r["level"] == "L3")
    frac = l3 / total
    assert frac >= 0.96, f"occurrence L3 {l3}/{total} = {frac:.1%}, floor 96.0%"


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
    occ = [o for r in _rows() for o in r["occurrences"]]
    structured = sum(1 for o in occ if o["shipped"] == "structured")
    frac = structured / len(occ)
    assert frac >= 0.85, \
        f"structured occurrences {structured}/{len(occ)} = {frac:.1%}, floor 85.0%"


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
    assert avg >= 0.96, f"corpus average {avg:.6f}, floor 0.960000"


def test_the_floors_are_below_what_is_achieved_and_can_still_fail():
    """The floors are only commitments if they are reachable from below, and
    only meaningful if they are not already tripped. Both halves, on the same
    arithmetic the four tests above use, so a future edit that sets a floor AT
    the measurement (the standard way a gate is quietly retired) is visible
    here as a zero margin.

    Deliberately NOT asserting the achieved values themselves -- those are
    measurements and they move. What is asserted is the RELATION.
    """
    rows = _rows()
    occ = [o for r in rows for o in r["occurrences"]]
    achieved = {
        "unique L3": (sum(1 for r in rows if r["level"] == "L3") / len(rows), 0.96),
        "occurrence L3": (sum(len(r["occurrences"]) for r in rows
                              if r["level"] == "L3") / len(occ), 0.96),
        "structured reach": (sum(1 for o in occ if o["shipped"] == "structured")
                             / len(occ), 0.85),
    }
    for name, (value, floor) in achieved.items():
        assert value > floor, f"{name}: achieved {value:.4f} is AT or below its floor {floor}"
        assert floor > 0.0


@pytest.mark.parametrize("frac,floor,ok", [
    (0.9675, 0.96, True),
    (0.9599, 0.96, False),
    (0.8986, 0.85, True),
    (0.8499, 0.85, False),
])
def test_the_floor_comparison_rejects_what_it_should(frac, floor, ok):
    """Prove the comparison the four gates use can fail. Each of them passes on
    today's ledger and would go on passing if `>=` were quietly changed to
    something vacuous; four M4 reviews in a row found guards that were
    deletable with a green tree."""
    assert (frac >= floor) is ok

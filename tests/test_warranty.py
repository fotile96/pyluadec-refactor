"""Warranty 生成器与选择规则 -- M7 task 11。

选择规则是纯函数（spec §6 逐字）：资格（pred 侧 unpinned>0 取消资格、无等级
=不资格）、字典序 (T, E)（T3>T2>T-；id>wm>panel-pass>panel-pinned）、平级归
ours。本文件的纯函数部分不需要语料；不动点部分需要两个语料环境变量，与
`test_ledger_ratchet.py` 同纪律（重新生成 → 与提交产物逐字节比对）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.warranty_build import (  # noqa: E402
    PROVENANCE, SelectionError, select)


# ---------------------------------------------------------------------------
# The selection rule (pure; spec §6; the plan's four properties verbatim
# plus the ordering table they exercise).

def test_unpinned_disqualifies():
    assert select(ours=("T-", "id"), pred=("T3", "panel-pass", 1)) == "ours"


def test_pred_recert_beats_our_fallback():
    assert select(ours=("T-", "id"),
                  pred=("T3", "panel-pass", 0)).startswith("pred")


def test_tie_goes_ours():
    assert select(ours=("T3", "id"), pred=("T3", "panel-pass", 0)) == "ours"


def test_no_eligible_side_raises():
    with pytest.raises(SelectionError):
        select(ours=None, pred=("T3", "panel-pass", 1))


def test_t_ordering_is_t3_t2_tminus():
    assert select(ours=("T2", "id"), pred=("T-", "panel-pass", 0)) == "ours"
    assert select(ours=("T-", "id"), pred=("T2", "panel-pass", 0)) == "pred"


def test_e_ordering_id_wm_pass_pinned():
    # ours' E is graded, not hardcoded to id, so the E ladder is drivable.
    assert select(ours=("T-", "wm"), pred=("T-", "panel-pass", 0)) == "ours"
    assert select(ours=("T-", "panel-pass"),
                  pred=("T-", "panel-pinned", 0)) == "ours"
    assert select(ours=("T-", "panel-pinned"),
                  pred=("T-", "panel-pass", 0)) == "pred"


def test_ungraded_pred_side_loses_to_any_graded_ours():
    assert select(ours=("T-", "id"), pred=None) == "ours"


def test_ungraded_ours_side_pred_wins_when_eligible():
    assert select(ours=None, pred=("T-", "panel-pinned", 0)) == "pred"


# ---------------------------------------------------------------------------
# The committed artifact's cheap invariants (no corpus): shape, vocabulary,
# occurrence coverage, and the ours/pred agreement the schema promises.

def _rows():
    return [json.loads(l) for l
            in (ROOT / "corpus" / "warranty.jsonl").read_text().splitlines()
            if l.strip()]


def test_warranty_rows_exist_with_the_selection_vocabulary():
    rows = _rows()
    assert len(rows) == 229
    names = [r["file"] for r in rows]
    assert names == sorted(names)
    assert all(r["selection"] in PROVENANCE for r in rows)


def test_every_occurrence_is_graded_on_both_factors():
    for r in _rows():
        assert r["ours"]["t_min"] in ("T3", "T2", "T-")
        for o in r["occurrences"]:
            assert o["t"] in ("T3", "T2", "T-")
            assert o["e"] in ("id", "wm", "panel-pass", "panel-pinned")


def test_no_unpinned_side_is_shipped():
    # spec §8.2: zero panel-unpinned shipped. The selected side's per-
    # occurrence e never carries it, and a pred side with unpinned>0 never
    # wins selection -- checked on the artifact, not just in select().
    for r in _rows():
        for o in r["occurrences"]:
            assert o["e"] != "panel-unpinned"
        if r["selection"].startswith("pred"):
            assert r["pred"]["unpinned"] == 0
        else:
            assert all(o["e"] == "id" for o in r["occurrences"])


def test_ours_side_minima_match_the_occurrence_grades():
    order = ("T3", "T2", "T-")
    for r in _rows():
        worst = max((o["t"] for o in r["occurrences"]),
                    key=order.index)
        assert r["ours"]["t_min"] == worst


# ---------------------------------------------------------------------------
# The fixed point (corpus-gated on BOTH env vars; regeneration must
# reproduce warranty.jsonl and every corpus/final/*.lua byte-identically).
# One module-scoped build serves both tests (the `panel_scan` precedent) --
# a full build is ~17s standalone (measured 2026-08-16), paid once.

@pytest.fixture(scope="module")
def built(corpus_dir, pred_corpus_dir):
    from scripts import warranty_build as wb

    return wb.build_all(corpus_dir, pred_corpus_dir)


@pytest.mark.timeout(300)
def test_warranty_artifacts_are_a_reproducible_fixed_point(built):
    warranty, finals, _summary = built
    committed = (ROOT / "corpus" / "warranty.jsonl").read_bytes()
    assert warranty == committed
    final_dir = ROOT / "corpus" / "final"
    committed_names = sorted(p.name for p in final_dir.glob("*.lua"))
    assert sorted(finals) == committed_names
    for name, text in finals.items():
        assert (final_dir / name).read_bytes() == text, name


@pytest.mark.timeout(300)
def test_warranty_fixed_point_is_not_vacuous(built):
    """Neuter proof (the test_invariant_panel precedent): a hand-edit inside
    the committed artifact must break the byte comparison -- the gate reads
    the artifact, not just the generator's own output."""
    warranty, _finals, _summary = built
    committed = (ROOT / "corpus" / "warranty.jsonl").read_bytes()
    tampered = committed.replace(b'"selection": "ours"',
                                 b'"selection": "pred-recert"', 1)
    assert tampered != committed
    assert warranty != tampered

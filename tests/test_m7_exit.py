"""M7 出口门 -- task 12（spec §8；地板刻意低于实测值，断言消息报实测数）。

本文件全部用例读**提交产物**（`corpus/ledger.jsonl`、`corpus/warranty.jsonl`、
`corpus/final/`），不需要语料环境变量——生成侧的不动点门在
`tests/test_warranty.py`（需要双环境变量），这里只问提交下来的东西。
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.warranty_build import PROVENANCE, select, T_ORDER  # noqa: E402

WARRANTY = ROOT / "corpus" / "warranty.jsonl"
LEDGER = ROOT / "corpus" / "ledger.jsonl"
FINAL = ROOT / "corpus" / "final"


def _warranty_rows():
    return [json.loads(l) for l in WARRANTY.read_text().splitlines() if l.strip()]


def _ledger_rows():
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def test_m7_exit_artifacts_complete():
    rows = _warranty_rows()
    assert len(rows) == 229
    names = [r["file"] for r in rows]
    assert names == sorted(names)
    assert all(r["selection"] in PROVENANCE for r in rows)
    # every occurrence graded on both factors; occurrence count matches the
    # corpus (measured at close: 1944)
    n = sum(len(r["occurrences"]) for r in rows)
    assert n == 1944
    for r in rows:
        for o in r["occurrences"]:
            assert o["t"] in T_ORDER
            assert o["e"] in ("id", "wm", "panel-pass", "panel-pinned")


def test_m7_exit_no_unpinned_shipped():
    # spec §8.2: every shipped occurrence's E is id / panel-pass /
    # panel-pinned; zero panel-unpinned shipped (measured: all 229 files
    # select ours, all 1944 occurrences ship e="id").
    for r in _warranty_rows():
        side = r["pred"] if r["selection"].startswith("pred") else None
        assert side is None or side["unpinned"] == 0
        for o in r["occurrences"]:
            assert o["e"] != "panel-unpinned"


def test_m7_exit_residual_strictly_below_40():
    # spec §8.4: our-side non-L3 unique rows strictly < 40 (measured at
    # close: 22 = 15 own + 7 inherited, every row attributed in the
    # runbook's "What is left" census).
    non_l3 = [e for e in _ledger_rows() if e["level"] != "L3"]
    assert len(non_l3) < 40, f"measured {len(non_l3)}"


def test_m7_exit_readability_floor():
    """spec §4 acceptance, encoding half: the fraction of non-ASCII string
    literals in corpus/final/ presented as raw UTF-8 (task 5 approved;
    measured at close: 17727/17727 = 1.0000)."""
    total = raw = 0
    for f in sorted(FINAL.glob("*.lua")):
        for m in re.finditer(rb'"(?:[^"\\]|\\.)*"', f.read_bytes()):
            lit = m.group()
            try:
                s = lit[1:-1].decode("utf-8")
            except UnicodeDecodeError:
                continue
            if s.isascii():
                continue
            total += 1
            if any(b > 127 for b in lit):
                raw += 1
    assert total > 0
    assert raw / total >= 0.99


def test_m7_exit_box_model_game_text_is_a_pinned_residual():
    """spec §4 acceptance, call-context half: NOT met, and pinned rather
    than exempted. The census口径 is "a non-ASCII string literal assigned
    into a `__pld_R` box" (the fallback state machine's register model) --
    NOT `doScriptScene` counting, whose call-form has zero sites corpus
    -wide while the game text itself travels through the boxes (controller
    review 2026-08-16; the review measured 49 lines -- the closing
    re-census found 52, three more outside snr_common). Disposition:
    recorded residual, fix routed to the M8 agenda (M8-scale work, not a
    closing-round change); this pin makes the residue unable to grow
    silently."""
    counts: Counter[str] = Counter()
    pat = re.compile(rb'__pld_R\[\d+\] = "([^"\\]|\\.)*"')
    for f in sorted(FINAL.glob("*.lua")):
        for m in pat.finditer(f.read_bytes()):
            if any(b > 127 for b in m.group()):
                counts[f.name] += 1
    assert dict(counts) == {
        "snr_common.lua": 49, "snr_story_main.lua": 2, "snr_novel.lua": 1}


def test_m7_exit_factor_e_never_decides_a_selection():
    """The structural observation, pinned as a property (controller review
    2026-08-16): with ours' e = "id" (constructive identity, spec §2),
    pred wins ONLY on a strictly better Factor T -- no T tie is ever
    decided by E, because "id" is the top of the E order. Factor E's
    entire decisive role is the unpinned>0 eligibility veto plus the
    record itself."""
    pred_e_grades = ("id", "wm", "panel-pass", "panel-pinned")
    wins = []
    combos = 0
    for o_t in T_ORDER:
        for p_t in T_ORDER:
            for p_e in pred_e_grades:
                combos += 1
                if select((o_t, "id"), (p_t, p_e, 0)) == "pred":
                    wins.append((o_t, p_t))
    assert combos == 36
    assert len(wins) == 12
    assert all(T_ORDER.index(p) < T_ORDER.index(o) for o, p in wins)
    # and the veto is the other half of E's role:
    assert select(("T3", "id"), ("T3", "panel-pass", 1)) == "ours"

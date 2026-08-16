"""脚注门（footprint gate）-- M8 task 1（spec §3）。

每文件 `footprint_ratio` = len(重编译产物字节码, strip=True) / len(原始文件字节)，
由生成器记录进 `corpus/warranty.jsonl`，套件只读提交产物、**不在测试时编译**。
三门 + 一个篡改 neuter：

(a) 每行都带 `footprint_ratio`；
(b) `{ratio != 1.0}` 恰等于「有任何 fallback occurrence 的文件」集合——
    M8 收口实测的 1:1 事实（结构化文件重编译逐字段相同 ⇒ 字节级相同 ⇒ 恰
    1.00×）从此是常驻门；
(c) 单调钉子：7 个非 1.0 文件的值不得上升（修复只会降低；修复提交在同一
    commit 更新钉子，ratchet 式）；
(d) 篡改 neuter：抄本里改一个 ratio，(b) 的判定必须翻红。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.warranty_build import footprint_ratios  # noqa: E402

WARRANTY = ROOT / "corpus" / "warranty.jsonl"
LEDGER = ROOT / "corpus" / "ledger.jsonl"

#: Monotone pin. Campaign start (task 1, 2026-08-16): 7 files. Task 3
#: (2026-08-16) flipped `snr_memory` fully structured (ratio 1.0 -- left the
#: dict) and dropped `snr_graphic` 2.3969 -> 1.9509 (main_3 certifies; the
#: root still inherits main_4's mismatch). A repair LOWERS a value (or drops
#: the file to 1.0 and out of the dict) -- never raises one. Update in the
#: same commit as the repair that moved it.
FOOTPRINT_PIN = {
    "snr_common.lua": 1.3994,
    "snr_graphic.lua": 1.9509,
    "snr_mainmenu.lua": 3.5598,
    "snr_music.lua": 3.344,
    "snr_novel.lua": 2.8752,
    "snr_story_main.lua": 1.6956,
}

#: The ceiling (partner-set, spec §3): policy line, not a hardware limit.
FOOTPRINT_CEILING = 1.5


def _warranty_rows():
    return [json.loads(l) for l in WARRANTY.read_text().splitlines() if l.strip()]


def _fallback_carriers():
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    return {o["file"] for r in rows for o in r["occurrences"]
            if o["shipped"] == "fallback"}


def test_every_row_carries_a_footprint_ratio():
    for r in _warranty_rows():
        assert "footprint_ratio" in r, r["file"]
        assert isinstance(r["footprint_ratio"], float)
        assert r["footprint_ratio"] > 0


def test_non_unit_ratios_are_exactly_the_fallback_carriers():
    ratios = footprint_ratios()
    assert len(ratios) == 229
    non_one = {f for f, r in ratios.items() if r != 1.0}
    assert non_one == _fallback_carriers()


def test_footprint_ratios_are_monotone_against_the_pin():
    ratios = footprint_ratios()
    for name, pinned in FOOTPRINT_PIN.items():
        assert ratios[name] <= pinned, (
            f"{name}: ratio {ratios[name]} rose above the committed "
            f"{pinned} -- a footprint regression")
    # files outside the pin are all exactly 1.0 by (b); assert it here too
    # so the pin dict's completeness is checkable: anything != 1.0 must be
    # in the pin (or have been added to it by a repair that kept it > 1.0).
    for f, r in ratios.items():
        if r != 1.0:
            assert f in FOOTPRINT_PIN, f"{f}: {r} != 1.0 but not pinned"


def test_footprint_ceiling_is_the_exit_gates_job_not_the_suites():
    """The ≤ 1.5 ceiling (partner-set, spec §3) is EXIT criterion 3 --
    asserted by `tests/test_m8_exit.py` at Task 10, once the campaign has
    driven the fallback carriers to 1.0. As a suite member now it would
    hold the whole suite red for the campaign's duration; this test exists
    only to record that routing decision next to the instrument."""
    assert FOOTPRINT_CEILING == 1.5


def test_tampered_ratio_breaks_the_one_to_one_gate():
    """Neuter: a doctored ratio in a copied artifact must flip the (b)
    predicate -- the gate reads the artifact, not the world."""
    rows = _warranty_rows()
    doctored = json.loads(json.dumps(rows[0]))
    doctored["footprint_ratio"] = 9.9
    assert doctored["footprint_ratio"] != rows[0]["footprint_ratio"]
    non_one = {r["file"] for r in rows if r["footprint_ratio"] != 1.0}
    non_one_doctored = {r["file"] for r in
                        [doctored] + rows[1:] if r["footprint_ratio"] != 1.0}
    assert non_one != non_one_doctored

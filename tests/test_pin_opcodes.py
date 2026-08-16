"""Pin 表 opcode 常驻检查 -- M7 task 11 Step 2（吸收 M7 agenda 6 路由项）。

`PRED_PINS` / `LOSS_PINS` 在 M6 final review 里被重定为 1-based 并逐对机检
过，但那次检查是一次性的（agenda 6 的原话：「future edits to either table
are unguarded against the exact defect the re-base fixed」）。本文件把检查器
（`scripts/warranty_build.py::pin_opcode_violations`，生成器写盘前跑同一
断言）作为常驻门：真实表全过 + 三种篡改各必红。

Proto 上下文解析规则（检查器实现的一部分，这里钉住）：LOSS pin 用键里的
proto；PRED pin 用 evidence 元组开头的 `main_X code=`；note 内 `main_X:`
标记切换其后所有对的归属。
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.warranty_build import pin_opcode_violations  # noqa: E402


@pytest.fixture(scope="module")
def _dirs():
    import os

    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    pred = os.environ.get("PYLUADEC_PRED_CORPUS_DIR")
    if not corpus or not Path(corpus).is_dir():
        pytest.skip("PYLUADEC_CORPUS_DIR not set or missing")
    if not pred or not Path(pred).is_dir():
        pytest.skip("PYLUADEC_PRED_CORPUS_DIR not set or missing")
    return Path(corpus), Path(pred)


def test_standing_tables_decode_clean(_dirs):
    """The corpus arm: every `O<n> OPNAME` / `P<n> OPNAME` pair in the
    committed tables holds at 1-based pc n in the resolved proto of the
    respective corpus. Measured 2026-08-16: 62 pairs (26 PRED + 36 LOSS)."""
    violations = pin_opcode_violations(*_dirs)
    assert violations == []


def test_off_by_one_pc_is_caught(_dirs):
    """The defect class the gate exists for (agenda 6): a 0-based pc
    copied from prose is off by one at decode time."""
    from scripts.loss_sweep import LOSS_PINS

    key = "snr_common.lua:main_75"
    note = LOSS_PINS[key].note
    assert "O159 JMP" in note
    tampered = {key: replace(LOSS_PINS[key], note=note.replace(
        "O159 JMP", "O158 JMP"))}
    violations = pin_opcode_violations(
        *_dirs, loss_pins=tampered, pred_pins={})
    assert len(violations) == 1
    assert "O158" in violations[0] and "main_75" in violations[0]


def test_wrong_opcode_name_is_caught(_dirs):
    from scripts.loss_sweep import LOSS_PINS

    key = "snr_common.lua:main_75"
    note = LOSS_PINS[key].note
    tampered = {key: replace(LOSS_PINS[key], note=note.replace(
        "O159 JMP", "O159 MOVE"))}
    violations = pin_opcode_violations(
        *_dirs, loss_pins=tampered, pred_pins={})
    assert len(violations) == 1
    assert "MOVE" in violations[0]


def test_pred_side_and_evidence_context_resolve(_dirs):
    """A P-side pair with a wrong pc is caught through the evidence-lead
    context (file-keyed PRED pin, proto from the `main_X code=` prefix)."""
    from scripts.cross_corpus import Pin, PRED_PINS

    pin = PRED_PINS["fingerprint"]["snr_music.lua"]
    assert "O368 JMP" in pin.note  # main_3 via the evidence lead
    tampered = {"fingerprint": {"snr_music.lua": replace(
        pin, note=pin.note.replace("O368 JMP", "P368 JMP"))}}
    violations = pin_opcode_violations(
        *_dirs, pred_pins=tampered, loss_pins={})
    assert len(violations) == 1
    assert "P368" in violations[0]

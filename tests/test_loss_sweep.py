"""The standing gate for M6's four loss sweeps (`scripts/loss_sweep.py`).

M6 task 6 ran these sweeps by hand while adjudicating the divergence queue,
and one of them -- the reachable back edge -- found defect (6),
`snr_common.lua:main_75`, on a proto the fingerprint arm scores at
`cfg_reachable == 1.0`. This module is what makes a *future* such loss fail a
gate rather than wait for someone to look.

The corpus-gated tests below run the full 1944-pair sweep. That is deliberate
and it is measured: §4 of `docs/reports/m6-cross-corpus.md` carries the
attribution. What is asserted here and NOT in the CLI, and vice versa:

  * here -- the pin table is well formed and every pinned loss still happens
    with the recorded numbers (`moved`/`gone` empty), no proto anywhere in the
    corpus loses something unpinned (`unexpected` empty), sweep 4 is empty,
    and the two loop numbers are genuinely two numbers;
  * in the CLI -- nothing extra. Unlike `cross_corpus.py`, whose `unexpected`
    claim needs 229 files and so had to stay a job, this sweep is cheap enough
    that the gate and the CLI make the same claim; the CLI exists to print the
    rows and the notes for a human, not to carry an assertion the suite
    cannot.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cross_corpus import VERDICTS, json_safe  # noqa: E402
from scripts.loss_sweep import (BASES, LOSS_KINDS, LOSS_PINS,  # noqa: E402
                                SWEEPS, LossPin, loop_shape, n_pairs,
                                pin_evidence, sweep)
from scripts.probe_common import adjudicate_pins  # noqa: E402

#: Sweep 4: the four fields that no proto in the corpus loses. Kept as a name
#: because the emptiness is the claim, not an omission.
SWEEP4 = ("global_writes", "call_targets", "call_shapes", "return_arity")

#: Headline totals, measured 2026-08-14 over all 1944 proto pairs. Pinned so a
#: change has to be a deliberate edit here with a re-measurement behind it.
EXPECTED_SWEEP_HITS = {1: 1, 2: 4, 3: 24, 4: 0}
EXPECTED_PAIRS = 1944
EXPECTED_ROWS = 25


@pytest.fixture(scope="module")
def rows(corpus_dir, pred_corpus_dir):
    return sweep(corpus_dir=corpus_dir, pred_dir=pred_corpus_dir)


# -------------------------------------------------------------- no corpus

def test_pin_table_is_well_formed():
    """Vocabulary, shape and the red line. No corpus needed, so this half of
    the gate keeps working in a bare `uv run pytest`."""
    assert LOSS_PINS, "an empty pin table would make every gate below vacuous"
    for key, pin in LOSS_PINS.items():
        assert isinstance(pin, LossPin), key
        assert ":main" in key, key
        assert key.split(":")[0].endswith(".lua"), key
        assert pin.verdict in VERDICTS, (key, pin.verdict)
        assert pin.basis in BASES, (key, pin.basis)
        assert pin.defect == "none" or (
            pin.defect.startswith("defect-")
            and pin.defect[len("defect-"):] in "123456"), (key, pin.defect)
        assert len(pin.evidence) == 2 and all(pin.evidence), key
        assert len(pin.note) >= 40, (key, "a pin with no reason is a silenced "
                                          "alarm")
        assert json_safe([*pin.evidence, pin.note, pin.verdict, pin.defect]), key


def test_every_real_bug_pin_rests_on_an_instruction_walk():
    """`VERDICTS`' own rule for `real-bug`: "nothing weaker than a pc-level
    argument earns it". `family-fingerprint` is allowed for the benign
    residual and nowhere else."""
    for key, pin in LOSS_PINS.items():
        if pin.verdict == "real-bug":
            assert pin.basis == "instruction-walk", key
            assert pin.defect != "none", key


def test_every_loss_kind_belongs_to_exactly_one_sweep():
    assert set(SWEEPS) == set(LOSS_KINDS)
    assert set(SWEEPS.values()) == {1, 2, 3, 4}


def test_the_pin_gate_can_fail():
    """Non-vacuity for the corpus-gated adjudication below: perturbing a copy
    of the table must make `adjudicate_pins` NAME the row.

    Three ways a pin can rot, one assertion each -- a new unpinned loss, a
    pinned loss whose numbers changed, and a pin whose proto no longer loses
    anything.
    """
    key = "snr_common.lua:main_75"
    assert key in LOSS_PINS
    divergent = pin_evidence()

    unexpected, moved, gone = adjudicate_pins(divergent, pin_evidence())
    assert (unexpected, moved, gone) == ([], [], [])

    extra = dict(divergent) | {"snr_zzz.lua:main_1": ("a=1", "a=0")}
    assert adjudicate_pins(extra, pin_evidence())[0] == ["snr_zzz.lua:main_1"]

    bent = dict(divergent) | {key: ("bogus", divergent[key][1])}
    assert adjudicate_pins(bent, pin_evidence())[1] == [key]

    short = {k: v for k, v in divergent.items() if k != key}
    assert adjudicate_pins(short, pin_evidence())[2] == [key]


def test_loop_shape_counts_headers_and_latches_separately():
    """A loop is a HEADER, not a back edge -- the correction M6 task 4 was
    given. Synthetic (LABELLED as such: the corpus arm of this claim is
    `test_the_benign_back_edge_loss_keeps_every_loop_header` below), because
    a two-latch loop is easy to write and hard to find on demand.

        while true do
            if <cond> then <something> end
        end

    compiles to one header with two jumps back to it when both the `then` arm
    and the fall-through end the iteration.
    """
    from pyluadec import ingest, oracle
    src = b"""
        local n = 0
        while true do
            n = n + 1
            if n > 3 then n = n + 10 else n = n + 20 end
        end
    """
    proto = ingest.load_bytes(oracle.compile_source(src, strip=True))
    loops, backs = loop_shape(proto)
    assert loops == 1, "one `while`, one header"
    assert backs == 2, "both arms jump back, so two latches on that header"


# ------------------------------------------------------------- with corpus

def test_the_sweep_covers_every_proto_pair(corpus_dir, pred_corpus_dir):
    """The denominator. `sweep_file` raises `MissingPath` rather than skipping
    a path the predecessor tree does not have, so a green `rows` fixture is
    already proof that all 1944 pairs were compared; this pins the number so a
    shrunken corpus cannot quietly weaken every claim below."""
    assert n_pairs(corpus_dir=corpus_dir) == EXPECTED_PAIRS


def test_no_proto_loses_something_unpinned(rows):
    """The gate. `unexpected` names any proto that lost a global read, a back
    edge, a loop header, a test op, a global write, a call target, a call
    shape or a return arity and is not in the table."""
    unexpected, moved, gone = adjudicate_pins(
        {k: r.evidence for k, r in rows.items()}, pin_evidence())
    assert unexpected == [], "unpinned loss(es) -- adjudicate before pinning"
    assert moved == [], "pinned evidence moved: the recorded note no longer "\
                        "describes the numbers"
    assert gone == [], "stale pin(s): delete, do not leave passing silently"
    assert len(rows) == EXPECTED_ROWS


def test_sweep_4_is_empty(rows):
    """No proto in the corpus loses a global write, a call target, a call
    shape or a return arity. This is the sweep with no instances, and its
    emptiness is a positive claim about the shipped output: nothing was
    *deleted* along those four channels anywhere in 1944 protos."""
    hits = {k: r.losses for k, r in rows.items()
            if any(f in r.losses for f in SWEEP4)}
    assert hits == {}


def test_the_four_sweeps_hit_what_they_were_measured_to_hit(rows):
    per_sweep: dict[int, set[str]] = {s: set() for s in (1, 2, 3, 4)}
    for key, r in rows.items():
        for kind in r.losses:
            per_sweep[SWEEPS[kind]].add(key)
    assert {s: len(v) for s, v in per_sweep.items()} == EXPECTED_SWEEP_HITS
    assert per_sweep[1] == {"snr_mainmenu.lua:main_7"}
    assert per_sweep[2] == {"snr_common.lua:main_75",
                            "snr_mainmenu.lua:main_7",
                            "snr_music.lua:main_3",
                            "snr_s5_10_s.lua:main_46"}


def test_the_two_loop_defects_are_the_two_header_losses(rows):
    """`n_natural_loops` is the sharper of the two loop fields: on this corpus
    it fires on exactly the two protos where a loop became straight-line code,
    with no benign instance. `n_back_edges` fires on those two plus two more.
    """
    headers = {k for k, r in rows.items() if "n_natural_loops" in r.losses}
    assert headers == {"snr_music.lua:main_3", "snr_common.lua:main_75"}
    assert all(LOSS_PINS[k].verdict == "real-bug" for k in headers)


def test_the_benign_back_edge_loss_keeps_every_loop_header(rows):
    """The one back-edge loss that is not a defect, and the reason both
    numbers are swept. `snr_s5_10_s.lua:main_46` keeps both of its loop
    headers and loses two latches on one of them: the corpus arm of
    `test_loop_shape_counts_headers_and_latches_separately`."""
    r = rows["snr_s5_10_s.lua:main_46"]
    assert "n_natural_loops" not in r.losses
    assert r.losses["n_back_edges"] == 2
    pin = LOSS_PINS["snr_s5_10_s.lua:main_46"]
    assert pin.verdict == "equivalent-transform" and pin.defect == "none"


def test_the_per_opcode_test_op_reading_catches_defect_2(rows):
    """Why `test_ops` is compared per opcode and not on the five-opcode total.
    `snr_common.lua:main_76_2` gains 3 `EQ` and loses 3 `TESTSET`; the totals
    are equal, so the aggregate reading §3.7 published (23 protos) does not
    see it, and it is a confirmed defect site."""
    r = rows["snr_common.lua:main_76_2"]
    assert r.losses == {"test_ops": 3}
    assert LOSS_PINS["snr_common.lua:main_76_2"].defect == "defect-2"


def test_every_confirmed_defect_site_that_lost_something_is_pinned_as_one(rows):
    """The payload, asserted so it cannot be quietly downgraded. Five of the
    six defects of `docs/reports/m6-cross-corpus.md` §3 lose something under
    these sweeps; defect (5) `snr_memory.lua:main_4` and defect (4)
    `snr_graphic.lua:main_4` come in through `test_ops` alone."""
    expected = {
        "snr_music.lua:main_3": "defect-1",
        "snr_common.lua:main_76_2": "defect-2",
        "snr_mainmenu.lua:main_7": "defect-3",
        "snr_graphic.lua:main_4": "defect-4",
        "snr_memory.lua:main_4": "defect-5",
        "snr_common.lua:main_75": "defect-6",
    }
    for key, defect in expected.items():
        assert key in rows, key
        assert LOSS_PINS[key].defect == defect, key
        assert LOSS_PINS[key].verdict == "real-bug", key

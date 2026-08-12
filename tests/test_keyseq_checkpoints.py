"""The predecessor's two historical checkpoints, as standing regressions.

`DEBUG_KEY_SEQUENCE_HARNESS.md` (the predecessor project's playbook) lists two
"已验证的高价值检查点" in `snr_common.lua`, both of which were live bugs there:

1. `SystemOption.OptionMain`'s RIGHT/LEFT must keep **two mutually exclusive
   clamps** (`1..5` and `0..1`), and must not "先正确赋值，再无条件二次赋值覆盖"
   -- assign correctly and then unconditionally overwrite.
2. `SystemConfig.ConfigMain`'s CIRCLE branch must keep its **gate/wait**: the
   `firstFragment` / `memoryFlag` / `storyLineSkip` gates decide whether the
   press does anything at all, `break` may fire only on the gated path and must
   not be promoted to an unconditional one, and the no-state-change path must
   `wait(1)` so the same frame is not re-polled forever.

There are two checkpoint tests. Each drives the **original bytecode** and
**our shipped artifact** through task 9's harness (`scripts/probe_keyseq.py`)
with one authored key sequence, requires the traces to be byte-equal, and then
asserts the checkpoint's own property **on both traces separately**. The
second half is the point: trace equality alone is already the L2 gate's job
(`tests/test_l2_keyseq.py`), and it says nothing if the two sides regress
together. The property is derived from the historical bug, not from our own
output, so it still fails when both sides agree on the wrong behaviour --
demonstrated, for all seven injected bug shapes at the bottom of this module,
by replacing the original side with `luac_sz4`-compiled mutated source so that
the two traces are byte-equal and only the property can fire.

## What this proves, and what it does not

`snr_common.lua` ships **whole-file fallback** text (it is one of the 7 files
that are neither fully structured nor hybrid), and its L2 verdict is
`refused: taint-static` -- both re-measured this session, and neither changed
by this module. So these checkpoints are **not** an L2 grant and do not widen
one. They are behavioural regressions over the fallback state machine's output
along two input-driven paths, which is exactly the ground the L2 badge does
not cover (the badge is `snr_lib.lua` only, and only structured text).

The trace pair is compared byte-for-byte with no normalisation, and no
comparison here is relaxed.

## Corpus content, and the red line

CLAUDE.md's red line is that bytecode-derived strings stay `bytes` through
ingest/lift/verify/comparison and never reach committed diagnostic text.
Nothing here decodes anything -- the traces are `bytes` end to end -- and
every property is a statement about **numbers and event structure**: how many
distinct clip rectangles a display layer took, which frames a key was down on,
how far the frame counter advanced, whether any poll happened after a given
one. No Japanese game text and no menu label is matched or asserted on, and
the checkpoints deliberately avoid needing one: the thing a property could not
be phrased around is *which* menu row is which, and that is handled
positionally ("the first and last display layer to be redrawn") rather than by
naming a row.

Being exact about what *is* named, since these are constant-pool strings too:
the two entry-point names in the specs, the button names, `layerClip` and
`wait`. Those are global/API identifiers, the same category as the button
names already in `scripts/probe_keyseq.KEY_SEQUENCES`, the entry names task 9
authored there, and the `cBrStr` pin in `scripts/probe_behaviour.py`. Assertion
messages can also interpolate trace lines, which carry engine call names; that
is a pytest failure message on a console, never serialised, and is the same
accepted exposure `probe_keyseq.L2Result.as_ledger_field` documents for
`detail`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.probe_keyseq import header, probe_raw

CORPUS_FILE = "snr_common.lua"

# --------------------------------------------------------------------------
# The two authored sequences
#
# Deliberately NOT added to `scripts.probe_keyseq.KEY_SEQUENCES`. That table is
# the L2 gate's input: every sequence in it must pass on its own for the file
# to be granted, and it feeds `corpus/ledger.jsonl`'s `l2` field. These two
# sequences are a regression instrument for one file, not a widening of the
# gate, and keeping them here leaves the ledger untouched -- this module adds
# no production code at all, so `corpus/ledger.jsonl` cannot move, and it is
# byte-unchanged in the commit that landed it.
#
# Frame arithmetic. `wait(n)` advances the frame by `max(floor(n), 1)` (the
# predecessor's rule, reproduced by `probe_keyseq.lua`'s `waitf`). In both menu
# loops an accepted cursor move or value change answers with `wait(5)` and the
# iteration then closes with `wait(1)`, so such a press costs **6** frames and
# the next press has to be scheduled 6 frames later; measured on the original
# side, the polls land on frames 1, 7, 13, ... A press that changes nothing
# costs **1**.
# --------------------------------------------------------------------------

# OptionMain, cursor row 1 (a member of the `1..5` clamp group) driven to its
# floor with four LEFTs and then to its ceiling with six RIGHTs; one DOWN to
# row 2 (a member of the `0..1` group); then the same treatment there. The
# over-pressing at each end is what makes the clamp observable: a press that
# produces no change is what a clamp IS.
OPTION_CLAMP_SPEC = (
    "entry=systemOption.OptionMain;"
    "k=1,LEFT;k=7,LEFT;k=13,LEFT;k=19,LEFT;"
    "k=25,RIGHT;k=31,RIGHT;k=37,RIGHT;k=43,RIGHT;k=49,RIGHT;k=55,RIGHT;"
    "k=61,DOWN;"
    "k=67,LEFT;k=73,LEFT;k=79,LEFT;"
    "k=85,RIGHT;k=91,RIGHT;k=97,RIGHT;k=103,RIGHT;tail=CROSS"
)

# ConfigMain: five DOWNs walk the cursor to a row the CIRCLE gates do NOT
# accept under this environment, one CIRCLE there (which must do nothing and
# advance exactly one frame), one DOWN to a row the gates DO accept, and one
# CIRCLE there (which must leave the loop). `tail=CROSS` is the safety net --
# it is never reached on a clean run, and it is what stops a regression that
# breaks the exit from spinning to the event cap silently.
CONFIG_GATE_SPEC = (
    "entry=systemConfig.ConfigMain;"
    "k=1,DOWN;k=7,DOWN;k=13,DOWN;k=19,DOWN;k=25,DOWN;"
    "k=31,CIRCLE;k=32,DOWN;k=38,CIRCLE;tail=CROSS"
)


# --------------------------------------------------------------------------
# Trace reading. Bytes in, numbers out.
# --------------------------------------------------------------------------

def _lines(trace: bytes) -> list[bytes]:
    return [l for l in trace.split(b"\n") if l]


def _polls(trace: bytes) -> list[tuple[bytes, int, bool]]:
    """`(key, frame, down)` for every `K|` poll, in order."""
    out = []
    for l in _lines(trace):
        if l.startswith(b"K|"):
            _, key, frame, down = l.split(b"|")
            out.append((key, int(frame), down == b"true"))
    return out


def _clip_states(trace: bytes) -> list[tuple[bytes, tuple[bytes, ...]]]:
    """`(layer, rectangle)` for every `layerClip` call, in order.

    The display layer is argument 1 and the clip rectangle is the rest. A menu
    option's *value* is not visible anywhere in the trace -- it lives in a
    table the chunk itself built, so no stub metamethod sees it -- but the
    handler that redraws the option turns the value into a rectangle, and two
    different values give two different rectangles. Counting distinct
    rectangles is therefore counting distinct values, without ever having to
    know what the value means.
    """
    out = []
    for l in _lines(trace):
        if l.startswith(b"C|layerClip|"):
            args = l.split(b"|")[3].split(b",")
            out.append((args[0], tuple(args[1:])))
    return out


# --------------------------------------------------------------------------
# Checkpoint 1: the two mutually exclusive clamps
# --------------------------------------------------------------------------

def assert_double_clamp(trace: bytes, who: str) -> None:
    """`OptionMain` holds two clamps with **different** bounds at once.

    Structurally, with no reference to what any menu row means:

    * the first `layerClip` of the run names row 1's display layer and the
      last names row 2's -- the sequence drives row 1, moves the cursor once,
      then drives row 2, so those two layers differ;
    * row 1 is driven 4 + 6 = 10 times, row 2 3 + 4 = 7 times;
    * **both saturate**: within each row, the last three presses in each
      direction leave the rectangle unchanged. A clamp is exactly "a press
      that changes nothing", so this is the clamps being *present*;
    * **row 1 reaches strictly more distinct rectangles than row 2.** That is
      the checkpoint: two ranges of different size are in force in the same
      function under the same two keys, which is what "两套互斥 clamp" means.
      The historical bug -- the second clamp applied unconditionally after the
      first, overwriting it -- collapses row 1 onto row 2's range and the two
      counts become equal;
    * the exact counts are **5** and **2**, pinned two-directionally so that a
      clamp bound that moves in either direction is adjudicated rather than
      absorbed by the inequality above.

    The order of the three assertions is load-bearing and was chosen by
    measurement (see the injection cases at the bottom of this module): each
    of the three is the FIRST to fire for one injected bug shape, so none of
    them is decoration.
    """
    states = _clip_states(trace)
    assert states, f"{who}: no layerClip recorded -- the drive did nothing"
    first_layer, last_layer = states[0][0], states[-1][0]
    row1 = [r for lay, r in states if lay == first_layer]
    row2 = [r for lay, r in states if lay == last_layer]
    assert (first_layer != last_layer, len(row1), len(row2)) == (True, 10, 7), (
        f"{who}: expected 10 redraws of one layer then 7 of a different one, "
        f"got {len(row1)} of {first_layer!r} and {len(row2)} of "
        f"{last_layer!r} -- the sequence no longer lands the presses it was "
        f"authored to land, so nothing below means anything")
    saturated = (row1[1] == row1[2] == row1[3],
                 row1[7] == row1[8] == row1[9],
                 row2[0] == row2[1] == row2[2],
                 row2[4] == row2[5] == row2[6])
    assert saturated == (True, True, True, True), (
        f"{who}: repeated presses kept changing the display -- "
        f"(row1 floor, row1 ceiling, row2 floor, row2 ceiling) held = "
        f"{saturated}; a clamp that does not hold is not a clamp")
    n1, n2 = len(set(row1)), len(set(row2))
    assert n1 > n2, (
        f"{who}: both rows reached {n1} display states, so ONE clamp is in "
        f"force for both -- the two clamps are no longer mutually exclusive")
    assert (n1, n2) == (5, 2), (
        f"{who}: the two rows reached {n1} and {n2} distinct display states, "
        f"pinned at 5 and 2 -- a clamp bound moved")


# --------------------------------------------------------------------------
# Checkpoint 2: the CIRCLE branch's gate and its wait
# --------------------------------------------------------------------------

def assert_circle_gate_and_wait(trace: bytes, who: str) -> None:
    """`ConfigMain`'s CIRCLE branch keeps its gate, its `break` and its wait.

    The sequence presses CIRCLE twice: once on a row the gates reject and once
    on a row they accept. Structurally, in the order the assertions fire:

    * the run ends `OK`, not `CAP`. A lost `wait(1)` on the no-state-change
      path re-polls the same frame forever, so the trace runs to the event cap
      instead of finishing -- "无状态变化路径必须有 `wait(1)` 避免同帧重复触发
      导致卡死";
    * **the first CIRCLE-down is not the last CIRCLE poll of the run.** That
      is "`break` 只能在原始路径触发，不能被提升为无条件 break" as a property
      of the trace: an unconditional `break` leaves the loop on the first
      press;
    * CIRCLE is down on exactly two polls -- sequence sanity, not a bug
      property, and labelled as such;
    * between the rejected press and the next iteration's poll the run records
      exactly one call, `wait(1)`, and the frame advances by exactly 1. So the
      press changed nothing (the `firstFragment` / `memoryFlag` /
      `storyLineSkip` gates stayed shut) *and* the wait is intact;
    * after the accepted press there is no further poll, no further `wait`,
      and the last line of the trace is the entry's return -- the loop was
      left, on the gated path, at the press the gates accept.
    """
    assert header(trace)[0] == "OK", (
        f"{who}: the run ended {header(trace)[0]}, not OK -- the loop did not "
        f"finish, which is what a lost wait(1) on the no-state-change path "
        f"looks like")
    polls = _polls(trace)
    circles = [(f, down) for key, f, down in polls if key == b"CIRCLE"]
    down_at = [i for i, (_, down) in enumerate(circles) if down]
    # FIRST among the poll assertions, because it is the historical bug and
    # every other one here is downstream of it: an unconditional `break` ends
    # the run at the first press, so the press count, the call window and the
    # tail all cease to exist. Ordered after the count check in round 1 of this
    # task, where the count check fired instead and left this line
    # unfalsifiable -- measured, not supposed.
    assert down_at and down_at[0] < len(circles) - 1, (
        f"{who}: the loop ended at the FIRST CIRCLE press (down on "
        f"{down_at} of {len(circles)} polls); the gate no longer decides "
        f"whether break fires -- it has been promoted to unconditional")
    # Sequence sanity rather than a bug property.
    assert len(down_at) == 2, (
        f"{who}: CIRCLE was down on {len(down_at)} of {len(circles)} polls, "
        f"expected 2 -- the authored sequence no longer lands both presses")
    rejected, accepted = down_at
    between = _calls_between_circle_polls(trace, circles[rejected][0],
                                          circles[rejected + 1][0])
    advance = circles[rejected + 1][0] - circles[rejected][0]
    assert (between, advance) == ([b"C|wait|1|1"], 1), (
        f"{who}: the rejected CIRCLE press recorded {between!r} and advanced "
        f"the frame by {advance}, expected a single wait(1) and 1 -- either a "
        f"gate that should have stayed shut let something through, or the "
        f"no-state-change path's wait changed")
    after = _lines(trace)[_line_of_circle(trace, circles[accepted][0]) + 1:]
    tail = ([l for l in after if l.startswith(b"K|")],
            [l for l in after if l.startswith(b"C|wait|")],
            after[-1][:2])
    assert tail == ([], [], b"R|"), (
        f"{who}: after the accepted CIRCLE press the run recorded "
        f"{len(tail[0])} more poll(s) and {len(tail[1])} more wait(s) and "
        f"ended with {tail[2]!r} -- the break on the gated path is gone")


def _line_of_circle(trace: bytes, frame: int) -> int:
    """Index of the `K|CIRCLE|<frame>|true` line."""
    want = b"K|CIRCLE|" + str(frame).encode("ascii") + b"|true"
    return _lines(trace).index(want)


def _calls_between_circle_polls(trace: bytes, f0: int, f1: int) -> list[bytes]:
    """Every `C|` line between the CIRCLE poll at frame `f0` and the next
    CIRCLE poll, at frame `f1`. CIRCLE is polled once per loop iteration, so
    those two lines bound exactly one iteration."""
    lines = _lines(trace)
    a = _line_of_circle(trace, f0)
    b = lines.index(b"K|CIRCLE|" + str(f1).encode("ascii") + b"|false", a)
    return [l for l in lines[a + 1:b] if l.startswith(b"C|")]


# --------------------------------------------------------------------------
# The two checkpoints
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def checkpoint_traces(corpus_dir, decompiled):
    """`{spec: (original trace, artifact trace)}`.

    Four probe runs, measured this session at 5-11 ms each (the original side
    is bytecode and loads faster than the 632 KB artifact source); the
    decompiled source comes from conftest's session-scoped cache, so this
    module never re-walks the corpus.
    """
    f = Path(corpus_dir) / CORPUS_FILE
    original = f.read_bytes()
    artifact = decompiled(f).source
    return {spec: (probe_raw(original, is_source=False, spec=spec),
                   probe_raw(artifact, is_source=True, spec=spec))
            for spec in (OPTION_CLAMP_SPEC, CONFIG_GATE_SPEC)}


@pytest.fixture(scope="module")
def artifact_source(corpus_dir, decompiled):
    return decompiled(Path(corpus_dir) / CORPUS_FILE).source


def test_option_main_double_clamp(checkpoint_traces):
    """Checkpoint 1. Traces equal AND the clamp property holds on each side."""
    original, artifact = checkpoint_traces[OPTION_CLAMP_SPEC]
    assert header(original)[0] == "OK", header(original)
    assert original == artifact, (
        "the two sides diverged; run scripts/probe_keyseq.py for a dump")
    assert_double_clamp(original, "original")
    assert_double_clamp(artifact, "artifact")


def test_config_main_circle_gate_and_wait(checkpoint_traces):
    """Checkpoint 2. Traces equal AND the gate/wait property holds on each."""
    original, artifact = checkpoint_traces[CONFIG_GATE_SPEC]
    # No header check in the body: `assert_circle_gate_and_wait` owns it,
    # because "the run finished instead of spinning" IS one third of this
    # checkpoint. Duplicating it here would make the property function's own
    # line unfalsifiable from this test.
    assert original == artifact, (
        "the two sides diverged; run scripts/probe_keyseq.py for a dump")
    assert_circle_gate_and_wait(original, "original")
    assert_circle_gate_and_wait(artifact, "artifact")


# --------------------------------------------------------------------------
# Load-bearing: every assertion in both property functions, against an
# injected bug shape that makes it -- and only it -- fire.
#
# Three of the seven are the predecessor's own bugs (`playbook` below); the
# other four exist because without them an assertion above would be shadowed
# by the one before it and could be deleted with the suite still green.
#
# Each case asserts the property function rejects the mutated trace **on its
# own**, with no reference to the original, and names the assertion that
# fired. That is what makes these tests survive a both-sides regression: the
# same demonstration was run this session with the ORIGINAL side replaced by
# `oracle.compile_source(mutated)`, so that the two traces are byte-equal and
# only the property can fail -- see the task report.
#
# The anchors are `structure.fallback`'s pc-dispatch text, because
# `snr_common.lua` ships whole-file fallback. Each is asserted unique before
# use: an anchor that matched nothing would make the injection a no-op and the
# case would pass while proving nothing. If the file ever ships structured,
# these assertions fail loudly and the anchors have to be re-derived against
# the new text; that is the intended failure, not a maintenance accident.
# --------------------------------------------------------------------------

_CLAMP_UPPER_TEST = (b"if not (5 < __pld_R[10]) then __pld_pc = 105 "
                     b"else __pld_pc = 106 end\n"
                     b"elseif __pld_pc == 105 then\n__pld_pc = 109\n"
                     b"elseif __pld_pc == 106 then\n__pld_R[10] = 5\n")

_ACCEPTED_BREAK = (b"elseif __pld_pc == 89 then\n"
                   b"__pld_R[3] = keyPlaySE\n__pld_R[4] = seName\n"
                   b"__pld_R[4] = __pld_R[4][\"circle\"]\n"
                   b"__pld_R[3](__pld_R[4])\n__pld_pc = 173\n")

INJECTIONS = [
    # (id, spec, anchor, replacement, expected fragment of the failure)
    ("playbook: the 1..5 clamp writes, then the 0..1 clamp overwrites it",
     "clamp", OPTION_CLAMP_SPEC,
     b"elseif __pld_pc == 115 then\n"
     b"__pld_R[8][__pld_R[9]] = __pld_R[10]\n__pld_pc = 139\n",
     b"elseif __pld_pc == 115 then\n"
     b"__pld_R[8][__pld_R[9]] = __pld_R[10]\n__pld_pc = 117\n",
     "no longer mutually exclusive"),
    ("the wide clamp's bound moves from 5 to 4",
     "clamp", OPTION_CLAMP_SPEC,
     _CLAMP_UPPER_TEST,
     _CLAMP_UPPER_TEST.replace(b"5 <", b"4 <").replace(b"[10] = 5",
                                                       b"[10] = 4"),
     "pinned at 5 and 2"),
    ("the wide clamp is removed and the value runs away",
     "clamp", OPTION_CLAMP_SPEC,
     b"__pld_R[10] = __pld_R[10] + 1\n"
     b"if not (5 < __pld_R[10]) then __pld_pc = 105 else __pld_pc = 106 end\n",
     b"__pld_R[10] = __pld_R[10] + 1\n__pld_pc = 105\n",
     "is not a clamp"),
    ("playbook: break promoted to unconditional",
     "gate", CONFIG_GATE_SPEC,
     b"elseif __pld_pc == 82 then\n__pld_pc = 94\n",
     b"elseif __pld_pc == 82 then\n__pld_pc = 83\n",
     "promoted to unconditional"),
    ("playbook: the no-state-change path loses its wait(1)",
     "gate", CONFIG_GATE_SPEC,
     b"elseif __pld_pc == 169 then\n"
     b"__pld_R[3] = wait\n__pld_R[4] = 1\n__pld_R[3](__pld_R[4])\n"
     b"__pld_pc = 4\n",
     b"elseif __pld_pc == 169 then\n__pld_pc = 4\n",
     "not OK"),
    ("the firstFragment gate is forced open",
     "gate", CONFIG_GATE_SPEC,
     b"elseif __pld_pc == 17 then\n__pld_pc = 75\n",
     b"elseif __pld_pc == 17 then\n__pld_pc = 18\n",
     "let something through"),
    ("the break on the gated path is removed",
     "gate", CONFIG_GATE_SPEC,
     _ACCEPTED_BREAK,
     _ACCEPTED_BREAK.replace(b"__pld_pc = 173\n", b"__pld_pc = 94\n"),
     "the break on the gated path is gone"),
]


@pytest.mark.parametrize(
    "which,spec,anchor,replacement,fragment",
    [c[1:] for c in INJECTIONS], ids=[c[0] for c in INJECTIONS])
def test_injected_bug_shape_is_caught(checkpoint_traces, artifact_source,
                                      which, spec, anchor, replacement,
                                      fragment):
    assert artifact_source.count(anchor) == 1, (
        f"injection anchor is no longer unique "
        f"(count={artifact_source.count(anchor)}); re-derive it -- an anchor "
        f"that matches nothing would make this case pass without injecting "
        f"anything")
    trace = probe_raw(artifact_source.replace(anchor, replacement),
                      is_source=True, spec=spec)
    assert trace != checkpoint_traces[spec][0], "the injection changed nothing"
    check = (assert_double_clamp if which == "clamp"
             else assert_circle_gate_and_wait)
    with pytest.raises(AssertionError) as e:
        check(trace, "mutated")
    assert fragment in str(e.value), str(e.value)

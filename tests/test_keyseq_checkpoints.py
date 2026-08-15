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
   **Of those three gates this module covers `firstFragment`, and `memoryFlag`
   in one direction only; `storyLineSkip` it does not cover at all** -- see
   `assert_circle_gate_and_wait` for the measurements. Round 1 of this task
   corrected a docstring that claimed all three.

There are two checkpoint tests. Each drives the **original bytecode** and
**our shipped artifact** through task 9's harness (`scripts/probe_keyseq.py`)
with one authored key sequence, requires the traces to be byte-equal, and then
asserts the checkpoint's own property **on both traces separately**. The
second half is the point: trace equality alone is already the L2 gate's job
(`tests/test_l2_keyseq.py`), and it says nothing if the two sides regress
together. The property is derived from the historical bug, not from our own
output, so it still fails when both sides agree on the wrong behaviour --
demonstrated, for all ten injected bug shapes at the bottom of this module,
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

Being exact about what *is* named, since these are constant-pool strings too.
An earlier version of this paragraph listed four and stopped; the full list,
re-derived from the file in round 1, is: the two entry-point names
(`systemOption.OptionMain`, `systemConfig.ConfigMain`), the six button names
used as spec keys (`UP`, `DOWN`, `LEFT`, `RIGHT`, `CIRCLE`, `CROSS`),
`layerClip` and `wait` in the trace readers, and -- inside the injection
anchors and the comments that explain them, which quote our own emitted source
-- `pressButton`, `keyPlaySE`, `seName`, `"circle"`, `memoryFlag`, `gameSave`,
plus `"RIGHT"`/`"LEFT"` again as string literals. Every one is a global/API
identifier or a button name: the same
category as the button names already in `scripts/probe_keyseq.KEY_SEQUENCES`,
the entry names task 9 authored there, and the `cBrStr` pin in
`scripts/probe_behaviour.py`. None is game text. Assertion messages can also
interpolate trace lines, which carry engine call names; that is a pytest
failure message on a console, never serialised, and is the same accepted
exposure `probe_keyseq.L2Result.as_ledger_field` documents for `detail`.
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
# gate, and keeping them here leaves the ledger untouched: this module adds no
# production code, so `corpus/ledger.jsonl` cannot move on its account, and it
# is byte-unchanged in both commits of this task. (Round 1 *did* re-time the
# sequences that are in `KEY_SEQUENCES`, for a separate reason recorded there;
# that moved no verdict and no `cov`, so the ledger is unchanged by it too --
# checked by `tests/test_ledger_ratchet.py`, which regenerates the whole file
# including its `l2` field and requires byte equality.)
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
# advance exactly one frame), three UPs to the one row whose CIRCLE is decided
# by the `memoryFlag` gate, and one CIRCLE there (which must leave the loop).
# `tail=CROSS` is the safety net -- it is never reached on a clean run, and it
# is what stops a regression that breaks the exit from spinning to the cap
# silently.
#
# The three UPs are round 1's fix for a claim this module made and did not
# earn. The first version walked DOWN one row instead, onto a row whose CIRCLE
# is ungated, so the `memoryFlag` gate was walked past and never pressed:
# measured, forcing that gate open (fallback pc 85 -> 88) and forcing it shut
# (-> 87) both left the trace BYTE-IDENTICAL. Ending on the gated row makes
# the open direction detectable (it is now an injection case). The shut
# direction still is not, and cannot be: the probe environment fixes
# `memoryFlag` false, which is the arm the run already takes.
#
# `storyLineSkip` is NOT covered and cannot be from here: it is written only
# inside the `firstFragment == 1` region, and this environment's `gameSave`
# takes the other arm. Measured: changing the toggle's value (fallback pc 32,
# `R[4] = 2` -> `5`) leaves the trace byte-identical.
CONFIG_GATE_SPEC = (
    "entry=systemConfig.ConfigMain;"
    "k=1,DOWN;k=7,DOWN;k=13,DOWN;k=19,DOWN;k=25,DOWN;"
    "k=31,CIRCLE;k=32,UP;k=38,UP;k=44,UP;k=50,CIRCLE;tail=CROSS"
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


def _clip_states(trace: bytes) -> list[tuple[bytes, tuple[int, ...]]]:
    """`(layer, rectangle)` for every `layerClip` call, in order.

    The display layer is argument 1 and the clip rectangle is the rest, as
    numbers. A menu option's *value* is not visible anywhere in the trace --
    it lives in a table the chunk itself built, so no stub metamethod sees it
    -- but the handler that redraws the option turns the value into a
    rectangle, and two different values give two different rectangles.
    Counting distinct rectangles is therefore counting distinct values,
    without ever having to know what the value means.

    The rectangle is `tuple[int, ...]` rather than raw bytes because the
    direction assertion ORDERS two of them; measured on the original side,
    each option's rectangle moves monotonically with its value, so "greater
    rectangle" is "greater value" without either being named.
    """
    out = []
    for l in _lines(trace):
        if l.startswith(b"C|layerClip|"):
            args = l.split(b"|")[3].split(b",")
            out.append((args[0], tuple(int(x) for x in args[1:])))
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
      absorbed by the inequality above;
    * **the two keys move row 1's rectangle in opposite directions.** Round 1
      of this task added this: without it, swapping the two key names in the
      decompiled source -- a branch-arm-polarity regression, the class this
      pipeline actually risks -- passed everything else, because the same five
      rectangles are reached in reverse order and `set()` erases order.

    Five assertions. The first is sequence sanity -- it checks the drive
    landed the presses it was authored to land, and nothing below means
    anything without it. The other **four** are load-bearing, and their order
    was chosen by measurement: each of the four is the FIRST to fire for one
    injected bug shape at the bottom of this module, so none is decoration.
    """
    states = _clip_states(trace)
    first_layer = states[0][0] if states else None
    last_layer = states[-1][0] if states else None
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
    # `row1[0..3]` are the four presses of one key and `row1[4..9]` the six of
    # the other, so `row1[1] vs row1[0]` is a step under the first key and
    # `row1[4] vs row1[3]` a step under the second. They must go opposite ways.
    # Row 2 cannot supply this: measured, it is already at its floor, so its
    # first key produces no step at all.
    #
    # LAST, and that position is measured. Placed before the count assertions
    # it fired for the clamp-overwrite injection too (which pins row 1 at its
    # floor, so the second key's step is zero rather than reversed) and stole
    # that case's attribution.
    direction = (row1[1] < row1[0], row1[4] > row1[3])
    assert direction == (True, True), (
        f"{who}: the two keys moved the first row's display the same way "
        f"(down-then-up = {direction}); the branch arms have swapped")


# --------------------------------------------------------------------------
# Checkpoint 2: the CIRCLE branch's gate and its wait
# --------------------------------------------------------------------------

def assert_circle_gate_and_wait(trace: bytes, who: str) -> None:
    """`ConfigMain`'s CIRCLE branch keeps its gate, its `break` and its wait.

    The sequence presses CIRCLE twice: once on a row the gates reject and once
    on the row whose CIRCLE the `memoryFlag` gate decides. Structurally, in the
    order the assertions fire:

    * the run ends `OK`, not `CAP`. A lost `wait(1)` on the no-state-change
      path re-polls the same frame forever, so the trace runs to the event cap
      instead of finishing -- "无状态变化路径必须有 `wait(1)` 避免同帧重复触发
      导致卡死";
    * CIRCLE was down at least once -- sequence sanity, split out from the
      assertion below in round 1 because a frame desync (`wait(1)` -> `wait(2)`,
      measured) made that one report "the loop ended at the FIRST CIRCLE press"
      when there had been no press at all;
    * **the first CIRCLE-down is not the last CIRCLE poll of the run.** That
      is "`break` 只能在原始路径触发，不能被提升为无条件 break" as a property
      of the trace: an unconditional `break` leaves the loop on the first
      press;
    * CIRCLE is down on exactly two polls -- sequence sanity;
    * between the rejected press and the next iteration's poll the run records
      exactly one call, `wait(1)`, and the frame advances by exactly 1. So the
      press changed nothing (the `firstFragment` gate stayed shut) *and* the
      wait is intact;
    * after the accepted press there is no further poll, no further `wait`,
      and the last line of the trace is the entry's return -- the loop was
      left, at the press the gates accept.

    **Which gates this actually covers**, measured rather than asserted in
    prose (round 1 corrected a claim of all three): `firstFragment` yes --
    forcing it open changes the trace and fires the call-window assertion.
    `memoryFlag` in one direction only -- forcing it *open* changes the trace
    and fires the tail assertion; forcing it *shut* cannot be seen, because
    the probe environment fixes `memoryFlag` false and that is the arm the run
    already takes. `storyLineSkip` **not at all**: it is written only inside
    the `firstFragment == 1` region, which this environment never enters, and
    changing the value it toggles to leaves the trace byte-identical.
    """
    assert header(trace)[0] == "OK", (
        f"{who}: the run ended {header(trace)[0]}, not OK -- the loop did not "
        f"finish, which is what a lost wait(1) on the no-state-change path "
        f"looks like")
    polls = _polls(trace)
    circles = [(f, down) for key, f, down in polls if key == b"CIRCLE"]
    down_at = [i for i, (_, down) in enumerate(circles) if down]
    # Sequence sanity, and separate from the assertion below so that a run
    # where CIRCLE is never down is not diagnosed as an unconditional break.
    assert down_at, (
        f"{who}: CIRCLE was never down across {len(circles)} polls -- the "
        f"sequence and the loop's frames have gone out of step")
    # FIRST among the bug assertions, because it is the historical one and
    # every other is downstream of it: an unconditional `break` ends the run at
    # the first press, so the press count, the call window and the tail all
    # cease to exist. Ordered after the count check in round 1 of this task,
    # where the count check fired instead and left this line unfalsifiable --
    # measured, not supposed.
    assert down_at[0] < len(circles) - 1, (
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


def _circle_poll_at(trace: bytes, frame: int, start: int) -> int:
    """Index of the first `K|CIRCLE|<frame>|…` line at or after `start`,
    whatever its result.

    Round 1 fix: this used to look for `|false` specifically. Two consecutive
    CIRCLE polls both being *down* is unreachable today -- the assertions
    above fire first -- but a `ValueError` out of a helper is not an
    `AssertionError`, so `pytest.raises(AssertionError)` in the injection
    cases would not have caught it, and the ordering that made it unreachable
    was nowhere written down.
    """
    want = b"K|CIRCLE|" + str(frame).encode("ascii") + b"|"
    lines = _lines(trace)
    for i in range(start, len(lines)):
        if lines[i].startswith(want):
            return i
    raise AssertionError(
        f"no CIRCLE poll at frame {frame} after line {start} -- the loop "
        f"stopped polling between the two presses")


def _calls_between_circle_polls(trace: bytes, f0: int, f1: int) -> list[bytes]:
    """Every `C|` line between the CIRCLE poll at frame `f0` and the next
    CIRCLE poll, at frame `f1`. CIRCLE is polled once per loop iteration, so
    those two lines bound exactly one iteration."""
    lines = _lines(trace)
    a = _line_of_circle(trace, f0)
    b = _circle_poll_at(trace, f1, a + 1)
    return [l for l in lines[a + 1:b] if l.startswith(b"C|")]


# --------------------------------------------------------------------------
# The two checkpoints
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def checkpoint_traces(corpus_dir, decompiled):
    """`{spec: (original trace, artifact trace)}`.

    Four probe runs. Re-measured in round 1, 10 runs each side: the bytecode
    side is **3.5-5.3 ms** (median 3.7) and the source side **10.6-11.2 ms**
    (median 10.7), the gap being the 632 KB of artifact source the second one
    has to parse. The round-0 report's single "5-11 ms each" band covered
    neither honestly. The decompiled source comes from conftest's
    session-scoped cache, so this module never re-walks the corpus.
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
# Load-bearing: every bug assertion in both property functions, against an
# injected bug shape that makes it -- and only it -- fire.
#
# Three of the ten are the predecessor's own bugs (`playbook` below). Six more
# exist because without them an assertion above would be shadowed by the one
# before it and could be deleted with the suite still green -- that includes
# the three added in round 1 (the key-polarity swap, the frame desync, and the
# `memoryFlag` gate). The tenth is `memoryFlag`, which round 1 added because
# the docstring claimed a gate the sequence never pressed.
#
# Each case asserts the property function rejects the mutated trace **on its
# own**, with no reference to the original, and names the assertion that
# fired. That is what makes these tests survive a both-sides regression: the
# same demonstration is re-run every round with the ORIGINAL side replaced by
# `oracle.compile_source(mutated)`, so the two traces are byte-equal and only
# the property can fail -- see the task report.
#
# Each anchor is asserted unique before use: an anchor that matched nothing
# would make the injection a no-op and the case would pass while proving
# nothing. Since M7 task 6 `snr_common.lua` ships HYBRID, so the two
# checkpoints anchor different text -- OptionMain's territory is the
# re-emitted structured form, ConfigMain's (the `gate` cases below) still the
# `__pld_R`/`__pld_pc` pc-dispatch text of the fallback subtree it lives in.
# If either side's emitter output changes again, these assertions fail loudly
# and the anchors have to be re-derived against the new text; that is the
# intended failure, not a maintenance accident.
#
# A case may carry MORE than one (anchor, replacement) pair -- the key-polarity
# swap needs two, because a swap is not a substitution. Both of its anchors
# extend into the arm's first distinguishing body line (the RIGHT arm carries
# the `5 < ... + 1` increment, the LEFT arm the `- 1 < 1` decrement): after
# the first edit renames a key, the renamed site still matches the OTHER
# anchor's pressButton line, and without the body line the second anchor
# would count 2 and abort (measured, 2026-08-15).
# --------------------------------------------------------------------------

# The clamp anchors were re-derived 2026-08-15 (M7 task 6): snr_common
# flipped whole-file fallback -> HYBRID, so OptionMain's territory now ships
# structured text and the old `__pld_R`/`__pld_pc` carriers matched nothing.
# The injected BUG SHAPES are unchanged -- the specs are trace-level.
_CLAMP_WIDE = (b"local l2_10 = 5 < systemSave[l1_0.optionKey0[l2_1]] + 1 "
               b"and 5 or systemSave[l1_0.optionKey0[l2_1]] + 1")
# The wide-clamp line is the uniqueness carrier (`5 < ... + 1` appears once
# in the chunk); the store + `else` tail alone matches the LEFT arm too.
_CLAMP_THEN_TAIL = (_CLAMP_WIDE + b"\n"
                    b"                                l2_8[l2_9] = l2_10\n"
                    b"                            else\n")

_CLAMP_LEFT = (b"local l2_10 = systemSave[l1_0.optionKey0[l2_1]] - 1 < 1 "
               b"and 1 or systemSave[l1_0.optionKey0[l2_1]] - 1")


def _press_arm(key: bytes, clamp: bytes) -> bytes:
    """One direction-handler arm: pressButton key, gate, class test, and the
    arm's own clamp line (the distinguishing carrier -- see the block comment
    above the injections)."""
    return (b'if pressButton("' + key + b'") == true then\n'
            b'                        if l2_2 == false then\n'
            b'                            if l2_1 == 1 or l2_1 == 5 '
            b'or l2_1 == 6 then\n'
            b'                                local l2_8 = systemSave\n'
            b'                                local l2_9 = l1_0.optionKey0[l2_1]\n'
            b'                                ' + clamp)

_ACCEPTED_BREAK = (b"elseif __pld_pc == 89 then\n"
                   b"__pld_R[3] = keyPlaySE\n__pld_R[4] = seName\n"
                   b"__pld_R[4] = __pld_R[4][\"circle\"]\n"
                   b"__pld_R[3](__pld_R[4])\n__pld_pc = 173\n")

_LOOP_WAIT = (b"elseif __pld_pc == 169 then\n"
              b"__pld_R[3] = wait\n__pld_R[4] = 1\n__pld_R[3](__pld_R[4])\n"
              b"__pld_pc = 4\n")

_MEMORY_GATE = (b"elseif __pld_pc == 85 then\n__pld_R[3] = memoryFlag\n"
                b"if not (__pld_R[3] == true) then __pld_pc = 87 "
                b"else __pld_pc = 88 end\n")

_POLL_RIGHT = (b"elseif __pld_pc == 81 then\n__pld_R[8] = pressButton\n"
               b"__pld_R[9] = \"RIGHT\"\n")
_POLL_LEFT = (b"elseif __pld_pc == 146 then\n__pld_R[8] = pressButton\n"
              b"__pld_R[9] = \"LEFT\"\n")

INJECTIONS = [
    # (id, which property, spec, [(anchor, replacement), ...], failure fragment)
    ("playbook: the 1..5 clamp writes, then the 0..1 clamp overwrites it",
     "clamp", OPTION_CLAMP_SPEC,
     [(_CLAMP_THEN_TAIL,
       # close the then-arm after the wide clamp's store and run the else
       # arm's narrow clamp unconditionally right after it (`end do`): for a
       # wide-class key both stores run and the narrow one overwrites -- the
       # historical "assign correctly, then unconditionally overwrite". The
       # old fallback form said the same thing by redirecting pc 115 -> 117;
       # `if not (wide)` instead of `do` would be a semantic NO-OP (the
       # else-arm already runs exactly on `not wide`) and dies on the
       # "the injection changed nothing" assertion below.
       _CLAMP_WIDE + b"\n"
       b"                                l2_8[l2_9] = l2_10\n"
       b"                            end\n"
       b"                            do\n")],
     "no longer mutually exclusive"),
    ("the wide clamp's bound moves from 5 to 4",
     "clamp", OPTION_CLAMP_SPEC,
     [(_CLAMP_WIDE,
       _CLAMP_WIDE.replace(b"5 < ", b"4 < ").replace(b"and 5 or",
                                                     b"and 4 or"))],
     "pinned at 5 and 2"),
    ("the wide clamp is removed and the value runs away",
     "clamp", OPTION_CLAMP_SPEC,
     [(_CLAMP_WIDE,
       b"local l2_10 = systemSave[l1_0.optionKey0[l2_1]] + 1")],
     "is not a clamp"),
    # Round 1, from review: this passes every other clamp assertion. The same
    # five rectangles are reached in reverse order and `set()` erases order.
    # Anchors extend into the arm's clamp line so the two stay distinguishable
    # mid-swap (see the block comment above).
    ("the two direction keys are swapped",
     "clamp", OPTION_CLAMP_SPEC,
     [(_press_arm(b"RIGHT", _CLAMP_WIDE), _press_arm(b"LEFT", _CLAMP_WIDE)),
      (_press_arm(b"LEFT", _CLAMP_LEFT), _press_arm(b"RIGHT", _CLAMP_LEFT))],
     "the branch arms have swapped"),
    ("playbook: break promoted to unconditional",
     "gate", CONFIG_GATE_SPEC,
     [(b"elseif __pld_pc == 82 then\n__pld_pc = 94\n",
       b"elseif __pld_pc == 82 then\n__pld_pc = 83\n")],
     "promoted to unconditional"),
    ("playbook: the no-state-change path loses its wait(1)",
     "gate", CONFIG_GATE_SPEC,
     [(_LOOP_WAIT, b"elseif __pld_pc == 169 then\n__pld_pc = 4\n")],
     "not OK"),
    # Round 1: the loop's wait changing DURATION rather than disappearing. The
    # run still finishes, but every scheduled frame misses, so CIRCLE is never
    # down -- which the break assertion used to report as "the loop ended at
    # the FIRST CIRCLE press" with no press to speak of.
    ("the loop's wait changes from 1 frame to 2",
     "gate", CONFIG_GATE_SPEC,
     [(_LOOP_WAIT, _LOOP_WAIT.replace(b"__pld_R[4] = 1\n",
                                      b"__pld_R[4] = 2\n"))],
     "gone out of step"),
    ("the firstFragment gate is forced open",
     "gate", CONFIG_GATE_SPEC,
     [(b"elseif __pld_pc == 17 then\n__pld_pc = 75\n",
       b"elseif __pld_pc == 17 then\n__pld_pc = 18\n")],
     "let something through"),
    # Round 1: the gate the first version of this module claimed and did not
    # press. Only the "forced open" direction is detectable -- see
    # `assert_circle_gate_and_wait`.
    ("the memoryFlag gate is forced open",
     "gate", CONFIG_GATE_SPEC,
     [(_MEMORY_GATE,
       b"elseif __pld_pc == 85 then\n__pld_R[3] = memoryFlag\n"
       b"__pld_pc = 88\n")],
     "the break on the gated path is gone"),
    ("the break on the gated path is removed",
     "gate", CONFIG_GATE_SPEC,
     [(_ACCEPTED_BREAK,
       _ACCEPTED_BREAK.replace(b"__pld_pc = 173\n", b"__pld_pc = 94\n"))],
     "the break on the gated path is gone"),
]


@pytest.mark.parametrize(
    "which,spec,edits,fragment",
    [c[1:] for c in INJECTIONS], ids=[c[0] for c in INJECTIONS])
def test_injected_bug_shape_is_caught(checkpoint_traces, artifact_source,
                                      which, spec, edits, fragment):
    mutated = artifact_source
    for anchor, replacement in edits:
        assert mutated.count(anchor) == 1, (
            f"injection anchor is no longer unique "
            f"(count={mutated.count(anchor)}); re-derive it -- an anchor that "
            f"matches nothing would make this case pass without injecting "
            f"anything")
        mutated = mutated.replace(anchor, replacement)
    trace = probe_raw(mutated, is_source=True, spec=spec)
    assert trace != checkpoint_traces[spec][0], "the injection changed nothing"
    check = (assert_double_clamp if which == "clamp"
             else assert_circle_gate_and_wait)
    with pytest.raises(AssertionError) as e:
        check(trace, "mutated")
    assert fragment in str(e.value), str(e.value)

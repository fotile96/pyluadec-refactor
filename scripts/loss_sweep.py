"""Loss sweeps over all 1944 original/predecessor proto pairs -- M6 task X3.

用法: PYLUADEC_CORPUS_DIR=... PYLUADEC_PRED_CORPUS_DIR=... \
      uv run python scripts/loss_sweep.py
      (`--file NAME` repeatable, `--json PATH` for a machine-readable dump)
产出: 退出码 0 当且仅当 `adjudicate_pins` 三个列表都空；报告见
      docs/reports/m6-cross-corpus.md §4。

## Why this exists, and why it is not a fourth arm of `cross_corpus.py`

M6 task 6 adjudicated the 18-row divergence queue `scripts/cross_corpus.py`
produces and confirmed six defects in the shipped localization. While doing so
it ran four sweeps over **all 1944 proto pairs, independent of the queue
criterion**, each asking the same question from a different angle: *did the
predecessor LOSE something?* One of them -- the reachable back edge -- found
defect (6), `snr_common.lua:main_75`, on a proto the fingerprint arm's own
`cfg_reachable` component scores at exactly **1.0**. Had that sweep not been
run by hand, no rule in this harness would have ranked it.

This module is those sweeps promoted from one-off adjudication scripts to a
standing, pinned check. It lives **beside** `cross_corpus.py` rather than
inside it, for three measured reasons:

1. **Granularity.** `cross_corpus.ArmResult` and `PRED_PINS` are keyed per
   FILE and carry one `(original, predecessor)` evidence pair each.
   `_fingerprint_one`'s own round-1 comment records what that costs: a file's
   other flagged paths vanish behind its worst one (`snr_common.lua` hid
   `main_23`, `main_59` and `main_76_8` behind `main_76_2`). The sweeps are
   per-PROTO and naming the proto is the whole point of the gate. A fourth arm
   would either re-lose that or force a shape change on the three existing
   arms.
2. **Criterion independence is the payload.** The sweeps are valuable
   *because* they are not the queue criterion. Routing them through
   `first_cut` and `_queue_rows` would file them under a triage vocabulary
   built for a graded similarity metric, which is exactly the instrument they
   exist to backstop.
3. **Cost placement.** `cross_corpus.py --arm all` is deliberately a JOB and
   not a suite cost, because its `unexpected` claim needs all 229 files and
   the behaviour arm executes both sides. This sweep is static and cheap
   enough to be a suite gate (`tests/test_loss_sweep.py`), and keeping it
   separate is what lets it be one without dragging the dynamic arms in.

What it does reuse, deliberately rather than re-spelling: `probe_common.
adjudicate_pins` (the pin protocol, shared with both probe gates and with
`cross_corpus.py`), `cross_corpus.json_safe` (the red line) and
`cross_corpus.VERDICTS` (the adjudication vocabulary -- read by
`tests/test_loss_sweep.py`, which is where `LossPin.verdict` is checked
against it, rather than imported here for a runtime this module has no need
of), `verify.semantic_score.
collect_proto_signatures` (the per-proto counters -- the fingerprint arm's own
source, so the two instruments cannot disagree about what a "global read" is),
`predcorpus.load_pred_proto` and `cfg.blocks`/`cfg.dom`.

## The eight fields, in four sweeps

`LOSS_KINDS` is eight names; a proto is flagged if ANY of them is smaller on
the predecessor side.

  * **`global_reads`** -- sweep 1. `GETGLOBAL` counts per name, summed over
    names that fell.
  * **`n_natural_loops` / `n_back_edges`** -- sweep 2, and they are two
    numbers, not one. See the next section.
  * **`test_ops`** -- sweep 3. `EQ`/`LT`/`LE`/`TEST`/`TESTSET`.
  * **`global_writes` / `call_targets` / `call_shapes` / `return_arity`** --
    sweep 4, the one that is empty on this corpus and whose emptiness is the
    claim.

Counts come from `ProtoSignature`, so `call_targets` is the crude symbolic
fingerprint that module documents, not a call graph; the sweep inherits that
limitation and the pin notes say where it bites.

## A loop is a HEADER; a latch is a BACK EDGE. Both are emitted.

M6 task 4 published a false structural claim by counting back edges and
calling them loops: the predecessor's `snr_common.lua:main_76_2` is **one**
`while` loop whose tail `luac` wrote out four times, and it was reported as
four loops. `corpus/observation/classes.json` has published `n_natural_loops`
and `n_back_edges` under separate names ever since, and so does this module.

The distinction is load-bearing here, not bookkeeping. Measured 2026-08-14
over all 1944 pairs:

  * **4** protos lose a back edge; **2** lose a natural loop header.
  * The two header losses are exactly defects (1) `snr_music.lua:main_3` and
    (6) `snr_common.lua:main_75` -- both "a loop became straight-line code".
  * Of the two protos that lose back edges while keeping every header, one is
    defect (3) `snr_mainmenu.lua:main_7` (16 headers both sides, 32 -> 28 back
    edges: the four deleted progress gates each removed one latch from a
    header that keeps its others) and one is **benign**,
    `snr_s5_10_s.lua:main_46`, adjudicated `equivalent-transform` -- see its
    pin.

So `n_natural_loops` is the sharper field (2 hits, 2 defects, 0 benign) and
`n_back_edges` is the more sensitive one (4 hits, 3 defects, 1 benign). Both
are swept because a loop can lose latches without losing its header and a
header can vanish without the back-edge count reaching zero; neither number
implies the other.

Both are computed over **reachable blocks only**: `cfg.dom.
immediate_dominators` returns a map whose keys are precisely the blocks
reachable from the entry, and a back edge is `s -> h` with `h` dominating `s`
and both in that map. An unreachable latch is not a loop.

## `test_ops` is counted PER OPCODE, and that is not a free choice

Task 6's sweep summed the five opcodes and compared the totals; that reading
hits **23** protos. Comparing each opcode separately and summing the shortfalls
hits **24**, and the extra one is `snr_common.lua:main_76_2` -- **defect (2)**,
whose predecessor gains three `EQ` while losing three `TESTSET`, netting zero.
The aggregate reading misses a known defect site, so this module counts per
opcode. Both numbers are recorded because the 23 is what §3.7 of the report
published.

## The red line

Every committed string here is opcodes, counts, pcs, block numbers and ASCII
identifiers. `cross_corpus.json_safe` is asserted over the whole pin table by
`tests/test_loss_sweep.py::test_pin_table_is_well_formed`, and over every
evidence pair the sweep produces before it is returned. Nothing in this module
decodes a constant: the counters it reads are already hashed/normalised by
`semantic_score._normalize_const`, and no name ever reaches an evidence string.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cross_corpus import json_safe  # noqa: E402
from scripts.probe_common import adjudicate_pins  # noqa: E402

VERSION = "loss-sweep-v1"

#: The five test opcodes, `semantic_score._TEST_OPS` verbatim in content. Not
#: imported from there because that name is private and means "block breaker"
#: at its home; here it means "a branch the predecessor could have deleted".
TEST_OPCODES = ("EQ", "LT", "LE", "TEST", "TESTSET")

#: Every swept field. A proto is flagged if the predecessor's value for ANY of
#: these is smaller than the original's. Order is the order they print in.
LOSS_KINDS = ("global_reads", "global_writes", "call_targets", "call_shapes",
              "return_arity", "test_ops", "n_natural_loops", "n_back_edges")

#: Which sweep each field belongs to, for the CLI's summary and for the
#: report. Sweep 4's four fields have **0** hits on this corpus and that is
#: the assertion, not an omission.
SWEEPS = {
    "global_reads": 1,
    "n_natural_loops": 2,
    "n_back_edges": 2,
    "test_ops": 3,
    "global_writes": 4,
    "call_targets": 4,
    "call_shapes": 4,
    "return_arity": 4,
}

#: How well a pin's `note` is supported. A pin with no reason is a silenced
#: alarm, and a pin whose reason is "it looks like the others" is a weaker
#: claim than one whose reason is a pc walk -- so the two are distinguished in
#: the table rather than blurred by prose.
#:
#: * `instruction-walk` -- the pcs are named and the mechanism was followed
#:   through the two disassemblies. Every `real-bug` pin is this, by rule.
#: * `family-fingerprint` -- the opcode delta matches a mechanism already
#:   proven elsewhere on this corpus at instruction level, and the proto was
#:   NOT walked end to end. Honest and weaker; `docs/reports/
#:   m6-cross-corpus.md` §3.12 already carries four of these as open residual.
BASES = ("instruction-walk", "family-fingerprint")


@dataclass(frozen=True)
class LossPin:
    """One adjudicated per-proto loss.

    `evidence` is the `ProtoLoss.evidence` pair verbatim so `adjudicate_pins`
    can compare it; `defect` is `"defect-1"`..`"defect-6"` (the numbering of
    `docs/reports/m6-cross-corpus.md` §3) or `"none"`; `basis` says how hard
    the note's evidence is.
    """
    verdict: str
    defect: str
    basis: str
    evidence: tuple[str, str]
    note: str


#: Adjudicated pins, keyed `"<file>:<proto path>"`. A clean gate is
#: `adjudicate_pins` returning three empty lists.
#:
#: 25 rows over 11 files, all adjudicated 2026-08-14. Six carry a defect
#: number from `docs/reports/m6-cross-corpus.md` §3; the other 19 are
#: `equivalent-transform`. `O<n>`/`P<n>` are ORIGINAL/PREDECESSOR pcs, **1-based**,
#: matching `pyluadec.lift` (which decodes `p.code[pc - 1]` at pc) and
#: `luac_sz4 -l -l`; the report's §3/§4 PROSE numbers pcs from 0, so a pc here
#: is one greater than the same instruction there.
#:
#: That claim was FALSE for three of these notes until the M6 final review
#: (2026-08-14): `snr_common.lua:main_76_2`, `snr_graphic.lua:main_4` and
#: `snr_memory.lua:main_4` quoted §3 verbatim and were therefore 0-based, in a
#: table whose own docstring said 1-based. All three were re-based, and the
#: whole table is now machine-checked -- for every `O<n> OPNAME` / `P<n> OPNAME`
#: pair here, the opcode at 1-based pc `n` is `OPNAME`.
#:
#: The recurring benign mechanism, stated once rather than in nineteen notes:
#: a `TEST`/`TESTSET` whose tested register was written by the immediately
#: preceding instruction with a value whose truth is fixed at compile time is a
#: branch `luac` had to emit and a differently-phrased source does not need.
#: Census over every `TEST`/`TESTSET` site in the 17 protos below that lose
#: one (2026-08-14): **39** are preceded by a `LOADK` and every one of the 39
#: loads a `LuaNumber` -- never a boolean or nil constant, which `luac` would
#: emit as `LOADBOOL`/`LOADNIL` anyway -- and every Lua number is truthy,
#: **0 included**. The other fixed-truth producers that occur are `OP_LEN` and
#: the arithmetic ops (always a number, or they raise) and `OP_CONCAT` (always
#: a string, or it raises). A register that is an operand of `OP_LT`/`OP_LE` is
#: fixed the same way: `lvm.c::luaV_lessthan` admits two numbers or two
#: strings and raises otherwise.
LOSS_PINS: dict[str, LossPin] = {
    "snr_common.lua:main_27": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=66 global_writes=0 call_targets=43 call_shapes=43 return_arity=2 test_ops=24 n_natural_loops=1 n_back_edges=1",
         "global_reads=66 global_writes=0 call_targets=43 call_shapes=43 return_arity=2 test_ops=22 n_natural_loops=1 n_back_edges=1"),
        "test_ops-2: TESTSET at O80 and O103, each preceded by a LOADK of a "
        "number into the tested register, so both are statically true. The "
        "predecessor has 0 TEST/TESTSET at all; MOVE 3->11, LOADNIL 0->1, "
        "JMP 27->29 is the register churn that replaces them. Loops 1=1, "
        "back edges 1=1, every other swept field equal"),
    "snr_common.lua:main_28": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=118 global_writes=0 call_targets=75 call_shapes=75 return_arity=4 test_ops=28 n_natural_loops=1 n_back_edges=1",
         "global_reads=119 global_writes=0 call_targets=75 call_shapes=75 return_arity=4 test_ops=26 n_natural_loops=1 n_back_edges=1"),
        "test_ops-2: TESTSET at O209 and O232, both LOADK-of-a-number "
        "preceded, both statically true; the predecessor has 0. MOVE 2->11, "
        "JMP 34->37. global_reads 118->119 is a GAIN and gains are not swept. "
        "Loops 1=1, back edges 1=1"),
    "snr_common.lua:main_55": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=76 global_writes=0 call_targets=48 call_shapes=48 return_arity=2 test_ops=23 n_natural_loops=1 n_back_edges=1",
         "global_reads=76 global_writes=0 call_targets=48 call_shapes=48 return_arity=2 test_ops=21 n_natural_loops=1 n_back_edges=1"),
        "test_ops-2: TESTSET at O110 and O133, both LOADK-of-a-number "
        "preceded, both statically true; the predecessor has 0. MOVE 0->12, "
        "JMP 28->30. Loops 1=1, back edges 1=1. One of the four paths section 3.12 "
        "left as unwalked residual; this closes it for these fields"),
    "snr_common.lua:main_71": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=49 global_writes=0 call_targets=42 call_shapes=42 return_arity=2 test_ops=24 n_natural_loops=6 n_back_edges=8",
         "global_reads=49 global_writes=0 call_targets=42 call_shapes=42 return_arity=2 test_ops=21 n_natural_loops=6 n_back_edges=8"),
        "test_ops-4 = EQ-2 + TESTSET-2, and the EQ pair is the interesting "
        "half: O336 EQ A=0 R19 K[true] is followed by O337 JMP->338 while its "
        "not-taken path also lands on 338, and O341 / O342 JMP->343 is the "
        "same shape -- two ifs whose arms converge on the next pc, so deleting "
        "them cannot change control flow and EQ has no side effect. The "
        "pressButton CALLs they tested (O335 LEFT, O340 RIGHT) both survive; "
        "call_targets 42=42. TESTSET O327 is LOADK-of-a-number preceded; "
        "TESTSET O309 is decomposed into P342 TEST + P346 MOVE, which is what "
        "TESTSET means. Loops 6=6, back edges 8=8"),
    "snr_common.lua:main_74_13": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=56 global_writes=0 call_targets=42 call_shapes=42 return_arity=1 test_ops=104 n_natural_loops=1 n_back_edges=1",
         "global_reads=56 global_writes=0 call_targets=42 call_shapes=42 return_arity=1 test_ops=89 n_natural_loops=1 n_back_edges=1"),
        "test_ops-15 = TEST-8 + TESTSET-7, the largest row. Site census rather "
        "than a pc-by-pc match: the original has 30 TEST/TESTSET of which "
        "exactly 15 are preceded by an instruction fixing the tested "
        "register's truth value, the predecessor has 15 of which 0 are, so by "
        "count the 15 that vanished are the 15 statically-decided ones. That "
        "is an inference from two censuses, not a matching. MOVE 5->24, "
        "LOADNIL 0->1, JMP 117->119; loops 1=1, back edges 1=1"),
    "snr_common.lua:main_75": LossPin(
        "real-bug", "defect-6", "instruction-walk",
        ("global_reads=33 global_writes=0 call_targets=29 call_shapes=29 return_arity=4 test_ops=18 n_natural_loops=1 n_back_edges=1",
         "global_reads=33 global_writes=0 call_targets=29 call_shapes=29 return_arity=4 test_ops=18 n_natural_loops=0 n_back_edges=0"),
        "the row this whole module exists for. n_natural_loops 1->0 and "
        "n_back_edges 1->0: the only loop is gone. Original header is the "
        "block at O87 and its only latch the block at O156, whose O159 JMP "
        "sBx=-73 targets O87; the predecessor's CFG has no back edge at all, "
        "so a retry while became an if. Every other swept field is equal, "
        "and this proto's fingerprint cfg_reachable component measures "
        "exactly 1.0 (re-measured 2026-08-14) -- no rule in cross_corpus.py "
        "ranks it"),
    "snr_common.lua:main_76_2": LossPin(
        "real-bug", "defect-2", "instruction-walk",
        ("global_reads=27 global_writes=0 call_targets=16 call_shapes=16 return_arity=2 test_ops=27 n_natural_loops=1 n_back_edges=1",
         "global_reads=42 global_writes=0 call_targets=27 call_shapes=27 return_arity=2 test_ops=33 n_natural_loops=1 n_back_edges=4"),
        "visible only under the per-opcode reading of test_ops: TEST 1->0 and "
        "TESTSET 2->0 against EQ +7 and LT +2, so the five-opcode total goes "
        "27->33 and the aggregate sweep section 3.7 published never saw this proto. "
        "The defect is adjudicated in PRED_PINS[fingerprint][snr_common.lua]: "
        "an EQ polarity flip at O86/P93 makes a break unconditional and P68 "
        "JMP->5 re-enters the header, skipping the wait(1) at P274-276. "
        "n_back_edges 1->4 is a GAIN -- one loop whose tail luac wrote four "
        "times, the M6 task 4 correction -- and gains are not swept"),
    "snr_common.lua:main_76_7": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=34 global_writes=2 call_targets=27 call_shapes=27 return_arity=2 test_ops=23 n_natural_loops=4 n_back_edges=4",
         "global_reads=34 global_writes=2 call_targets=27 call_shapes=27 return_arity=2 test_ops=21 n_natural_loops=4 n_back_edges=4"),
        "test_ops-2: TESTSET at O99 and O122, both LOADK-of-a-number "
        "preceded, both statically true; the predecessor has 0. MOVE 3->24, "
        "LOADNIL 0->1, JMP 26->28. Loops 4=4 and back edges 4=4, so the four "
        "loops here keep both their headers and their latches. Closes another "
        "of section 3.12's four unwalked residual paths for these fields"),
    "snr_common.lua:main_77_24": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=38 global_writes=0 call_targets=34 call_shapes=34 return_arity=2 test_ops=34 n_natural_loops=1 n_back_edges=1",
         "global_reads=38 global_writes=0 call_targets=34 call_shapes=34 return_arity=2 test_ops=33 n_natural_loops=1 n_back_edges=1"),
        "test_ops-1: the single lost TESTSET is O285, preceded by a LOADK of "
        "a number, statically true; the predecessor has 0 TEST/TESTSET. "
        "MOVE 21->33, LOADNIL 0->1. Loops 1=1, back edges 1=1. section 3.12 recorded "
        "this path as not opened at all; it is opened now for these fields"),
    "snr_fragment_main.lua:main_3": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=147 global_writes=8 call_targets=96 call_shapes=96 return_arity=1 test_ops=45 n_natural_loops=3 n_back_edges=3",
         "global_reads=147 global_writes=8 call_targets=96 call_shapes=96 return_arity=1 test_ops=43 n_natural_loops=3 n_back_edges=3"),
        "test_ops-2: TESTSET O253 is LOADK-of-a-number preceded. TESTSET O118 "
        "(a=4 b=0 c=1) becomes P120 MOVE a=4 b=0 + P121 JMP, and that is "
        "sound because R0 is the left operand of O116 LT R0 R10, so "
        "luaV_lessthan has already constrained it to a number or a string and "
        "the test cannot fail. Loops 3=3, back edges 3=3"),
    "snr_graphic.lua:main_2": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=16 global_writes=0 call_targets=19 call_shapes=19 return_arity=1 test_ops=5 n_natural_loops=1 n_back_edges=2",
         "global_reads=16 global_writes=0 call_targets=19 call_shapes=19 return_arity=1 test_ops=4 n_natural_loops=1 n_back_edges=2"),
        "test_ops-1: the proto's only TEST, O134, tests the register O133 "
        "CONCAT just wrote. OP_CONCAT yields a string or raises and every "
        "string is truthy, so the test is statically true; the predecessor "
        "has 0. MOVE 2->17, LOADNIL 0->1. Loops 1=1, back edges 2=2"),
    "snr_graphic.lua:main_3": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=33 global_writes=0 call_targets=34 call_shapes=34 return_arity=1 test_ops=17 n_natural_loops=3 n_back_edges=5",
         "global_reads=33 global_writes=0 call_targets=34 call_shapes=34 return_arity=1 test_ops=14 n_natural_loops=3 n_back_edges=5"),
        "test_ops-3: O25 TEST on an OP_SUB result (a number or the op raises), "
        "O31 TEST on a LOADK of a number, O139 TEST on an OP_CONCAT result (a "
        "string) -- all three statically true. The one surviving predecessor "
        "test, P38 TESTSET, is the original's O39. MOVE 7->43, LOADNIL 0->1. "
        "Loops 3=3, back edges 5=5"),
    "snr_graphic.lua:main_4": LossPin(
        "real-bug", "defect-4", "instruction-walk",
        ("global_reads=67 global_writes=0 call_targets=63 call_shapes=63 return_arity=1 test_ops=67 n_natural_loops=7 n_back_edges=8",
         "global_reads=67 global_writes=0 call_targets=65 call_shapes=65 return_arity=1 test_ops=60 n_natural_loops=7 n_back_edges=8"),
        "test_ops-9 = EQ-6 + TEST-3, and the EQ half is the defect: an "
        "or-chain lost a disjunct and its else arm was un-nested, walked pc by "
        "pc in PRED_PINS[fingerprint][snr_graphic.lua] (O117/O120/O123 test "
        "K[3]/K[6]/K[9]; the predecessor tests only 3 and 9, and the LEFT "
        "handler drops == 4 the same way). Site census bounds the benign "
        "half: 8 TEST/TESTSET in the original of which 1 is statically "
        "decided, 5 in the predecessor of which 0 are. Loops 7=7 and back "
        "edges 8=8 -- this defect deletes tests, not loops"),
    "snr_lib.lua:main_1": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=36 global_writes=1 call_targets=26 call_shapes=26 return_arity=1 test_ops=16 n_natural_loops=2 n_back_edges=2",
         "global_reads=36 global_writes=1 call_targets=26 call_shapes=26 return_arity=1 test_ops=14 n_natural_loops=2 n_back_edges=2"),
        "test_ops-2: TESTSET at O49 and O64, both LOADK-of-a-number preceded, "
        "so the skip edge is dead and the op always means R := constant. This "
        "is the proto PRED_PINS[fingerprint][snr_lib.lua] already walked and "
        "adjudicated; MOVE 0->6 is the whole rest of the delta. Loops 2=2, "
        "back edges 2=2"),
    "snr_mainmenu.lua:main_7": LossPin(
        "real-bug", "defect-3", "instruction-walk",
        ("global_reads=291 global_writes=2 call_targets=271 call_shapes=271 return_arity=1 test_ops=226 n_natural_loops=16 n_back_edges=32",
         "global_reads=283 global_writes=2 call_targets=271 call_shapes=271 return_arity=1 test_ops=210 n_natural_loops=16 n_back_edges=28"),
        "the only global_read loss anywhere in the corpus, and the only proto "
        "that trips three sweeps at once. global_reads-8 is GETGLOBAL "
        "systemSave 24->16, the four deleted progress gates walked in "
        "PRED_PINS[fingerprint][snr_mainmenu.lua]. test_ops-36 = EQ-16 (four "
        "gates, four EQ each) + TESTSET-20, the latter re-expressed as TEST "
        "0->20, a gain. n_back_edges 32->28 with n_natural_loops 16=16: the "
        "headers at O253, O791, O1326 and O1871 have four latches each and "
        "the predecessor's corresponding headers have three each, one lost "
        "per header -- consistent with the four gates, which is an inference, "
        "while the latch counts are the measurement"),
    "snr_memory.lua:main_2": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=17 global_writes=0 call_targets=20 call_shapes=20 return_arity=1 test_ops=5 n_natural_loops=1 n_back_edges=2",
         "global_reads=17 global_writes=0 call_targets=20 call_shapes=20 return_arity=1 test_ops=4 n_natural_loops=1 n_back_edges=2"),
        "test_ops-1, the same shape as snr_graphic.lua:main_2 and measured "
        "separately: the proto's only TEST, O133, tests the register O132 "
        "CONCAT wrote, so it is statically true; the predecessor has 0. "
        "MOVE 2->17, LOADNIL 0->1. Loops 1=1, back edges 2=2"),
    "snr_memory.lua:main_3": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=33 global_writes=0 call_targets=34 call_shapes=34 return_arity=1 test_ops=17 n_natural_loops=3 n_back_edges=5",
         "global_reads=33 global_writes=0 call_targets=34 call_shapes=34 return_arity=1 test_ops=14 n_natural_loops=3 n_back_edges=5"),
        "test_ops-3, the same three producers as snr_graphic.lua:main_3 and "
        "at the same pcs: O25 TEST on an OP_SUB result, O31 TEST on a LOADK "
        "of a number, O139 TEST on an OP_CONCAT result; P38 TESTSET is the "
        "original's O39. MOVE 7->43, LOADNIL 0->1. Loops 3=3, back edges 5=5"),
    "snr_memory.lua:main_4": LossPin(
        "real-bug", "defect-5", "instruction-walk",
        ("global_reads=41 global_writes=3 call_targets=42 call_shapes=42 return_arity=1 test_ops=55 n_natural_loops=2 n_back_edges=2",
         "global_reads=41 global_writes=3 call_targets=44 call_shapes=44 return_arity=1 test_ops=49 n_natural_loops=2 n_back_edges=2"),
        "test_ops-8 = EQ-6 + TEST-2, the same defect as snr_graphic.lua:"
        "main_4 and walked in PRED_PINS[fingerprint][snr_memory.lua] "
        "(O118/O121/O124 test K[3]/K[6]/K[9], the predecessor only 3 and 9; "
        "the LEFT handler drops == 4). Site census: 7 TEST/TESTSET in the "
        "original, 0 of them statically decided, 5 in the predecessor -- so "
        "unlike main_3 above, none of this proto's lost tests is the benign "
        "family. Loops 2=2, back edges 2=2"),
    "snr_music.lua:main_3": LossPin(
        "real-bug", "defect-1", "instruction-walk",
        ("global_reads=20 global_writes=0 call_targets=23 call_shapes=23 return_arity=1 test_ops=38 n_natural_loops=2 n_back_edges=2",
         "global_reads=22 global_writes=0 call_targets=26 call_shapes=26 return_arity=1 test_ops=35 n_natural_loops=1 n_back_edges=1"),
        "n_natural_loops 2->1 and n_back_edges 2->1: the gallery poll loop is "
        "gone. The original's header block at O12 has one latch, the block at "
        "O365 whose O368 JMP sBx=-357 targets O12, and the predecessor has no "
        "counterpart; the surviving loop is O328 with latch O325 against P346 "
        "with latch P343. The test_ops-4 in the same row is NOT the defect: "
        "all four lost TESTs (O41 and O93 on LOADK numbers, O156 on an OP_SUB "
        "result, O219 on an OP_ADD result) are statically true"),
    "snr_novel.lua:main_12": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=25 global_writes=0 call_targets=30 call_shapes=30 return_arity=1 test_ops=27 n_natural_loops=2 n_back_edges=2",
         "global_reads=25 global_writes=0 call_targets=30 call_shapes=30 return_arity=1 test_ops=26 n_natural_loops=2 n_back_edges=2"),
        "test_ops-2: TESTSET O62 is LOADK-of-a-number preceded; TESTSET O46 "
        "(a=1 b=4) tests R4, which O44 LT R4 R9 has already constrained to a "
        "number or a string, so it too is statically true. The predecessor's "
        "P55 TEST on a GETTABLE result is a GAIN and gains are not swept. "
        "This proto is already walked at its jump sites in "
        "PRED_PINS[fingerprint][snr_novel.lua]. Loops 2=2, back edges 2=2"),
    "snr_novel.lua:main_2": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=6 global_writes=0 call_targets=6 call_shapes=6 return_arity=1 test_ops=4 n_natural_loops=0 n_back_edges=0",
         "global_reads=6 global_writes=0 call_targets=6 call_shapes=6 return_arity=1 test_ops=2 n_natural_loops=0 n_back_edges=0"),
        "test_ops-2: O41 TEST on an OP_LEN result (always a number) and O76 "
        "TEST on a LOADK of a number, both statically true; the predecessor "
        "has 0 TEST/TESTSET. MOVE 0->7. This proto has no loop on either "
        "side (0 headers, 0 back edges), so the loop fields cannot fall"),
    "snr_novel.lua:main_3": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=35 global_writes=0 call_targets=35 call_shapes=35 return_arity=1 test_ops=6 n_natural_loops=0 n_back_edges=0",
         "global_reads=35 global_writes=0 call_targets=35 call_shapes=35 return_arity=1 test_ops=4 n_natural_loops=0 n_back_edges=0"),
        "test_ops-2: O118 TEST on an OP_LEN result and O271 TEST on a LOADK "
        "of a number, both statically true; the predecessor has 0. "
        "MOVE 11->23. No loop on either side"),
    "snr_novel.lua:main_7": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=11 global_writes=0 call_targets=11 call_shapes=11 return_arity=2 test_ops=14 n_natural_loops=1 n_back_edges=1",
         "global_reads=11 global_writes=0 call_targets=11 call_shapes=11 return_arity=2 test_ops=13 n_natural_loops=1 n_back_edges=1"),
        "test_ops-3 is TESTSET-3 against TEST +2, so the aggregate is only 1. "
        "O25 TESTSET is LOADK-of-a-number preceded and simply collapses; O1 "
        "TESTSET and O44 TESTSET are decomposed into P1 TEST and P47 TEST "
        "plus their MOVEs, which is what TESTSET means. O44/P47 test an "
        "OP_LEN result, the case PRED_PINS[fingerprint][snr_novel.lua] "
        "already names. n_back_edges 1=1: the two escape jumps P42 and P58 that "
        "pin calls gained back edges have preds=[], and this module counts "
        "only REACHABLE back edges, so they do not appear here at all"),
    "snr_s5_10_s.lua:main_46": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=153 global_writes=34 call_targets=90 call_shapes=90 return_arity=1 test_ops=49 n_natural_loops=2 n_back_edges=5",
         "global_reads=153 global_writes=34 call_targets=90 call_shapes=90 return_arity=1 test_ops=48 n_natural_loops=2 n_back_edges=3"),
        "THE BENIGN BACK-EDGE LOSS, and the reason both loop numbers are "
        "swept. n_natural_loops 2=2: the headers are the blocks at O4 and O48 "
        "on the original side and at P4 and P48 on the predecessor's. The O4 "
        "loop keeps its single latch (O818 -> P796); the O48 loop goes from "
        "four latches (O80, O91, O101, O102) to two (P98, P99). One loop with "
        "fewer latches -- exactly the shape M6 task 4 was corrected on. The "
        "mechanism is the one PRED_PINS[fingerprint][snr_s5_10_s.lua] walked: "
        "the original's if/elseif chain gives each arm its own jump back to "
        "the shared header, the predecessor's sequential ifs let an arm fall "
        "through the remaining equality tests to a shared latch. EQ 49->48 "
        "and JMP 93->89 are that re-phrasing and test_ops-1 is that same EQ; "
        "no path into the header is lost"),
    "snr_story_main.lua:main_3": LossPin(
        "equivalent-transform", "none", "instruction-walk",
        ("global_reads=111 global_writes=9 call_targets=78 call_shapes=78 return_arity=1 test_ops=39 n_natural_loops=3 n_back_edges=3",
         "global_reads=112 global_writes=9 call_targets=79 call_shapes=79 return_arity=1 test_ops=37 n_natural_loops=3 n_back_edges=3"),
        "test_ops-2: TESTSET O239 is LOADK-of-a-number preceded. TESTSET O99 "
        "(a=4 b=0) becomes P101 MOVE a=4 b=0 + P102 JMP, sound because R0 is "
        "the left operand of O97 LT R0 R10 and so is already constrained to a "
        "number or a string. O299 TEST survives as P313. The call_targets and "
        "global_reads +1 are the duplicated or-fallback arm "
        "PRED_PINS[fingerprint][snr_story_main.lua] walked, and they are "
        "gains. Loops 3=3, back edges 3=3"),
}


def pin_evidence() -> dict[str, tuple[str, str]]:
    """`LOSS_PINS` projected to the pair form `adjudicate_pins` compares."""
    return {k: p.evidence for k, p in LOSS_PINS.items()}


@dataclass(frozen=True)
class ProtoLoss:
    file: str
    path: str                       # "main_75"
    evidence: tuple[str, str]       # (original side, predecessor side), ASCII
    losses: dict[str, int]          # LOSS_KINDS subset -> shortfall, all > 0

    @property
    def key(self) -> str:
        return f"{self.file}:{self.path}"


# --------------------------------------------------------------------------
# per-proto measurement
# --------------------------------------------------------------------------

def loop_shape(proto) -> tuple[int, int]:
    """`(n_natural_loops, n_back_edges)` over the REACHABLE blocks of `proto`.

    A back edge is `s -> h` where `h` dominates `s`; the natural loop of `h`
    is the union of the backward closures of every back edge targeting `h`, so
    the number of LOOPS is the number of distinct headers and the number of
    BACK EDGES is the number of `(s, h)` pairs. Four latches on one header is
    one loop -- the correction M6 task 4 was given, and the reason both
    numbers are returned instead of one.

    Reachability is `immediate_dominators`' key set, which `_reverse_postorder`
    builds from the entry: an unreachable latch cannot execute and so cannot be
    a loop.
    """
    from pyluadec.cfg.blocks import build_cfg
    from pyluadec.cfg.dom import dominates, immediate_dominators
    from pyluadec.lift import lift_proto

    cfg = build_cfg(lift_proto(proto))
    idom = immediate_dominators(cfg)
    headers: dict[int, int] = {}
    for s in idom:
        for t in cfg.blocks[s].succs:
            if t in idom and dominates(idom, t, s):
                headers[t] = headers.get(t, 0) + 1
    return len(headers), sum(headers.values())


def _fields(sig, proto) -> dict[str, int]:
    """The eight swept quantities for one proto."""
    loops, backs = loop_shape(proto)
    return {
        "global_reads": sum(sig.global_reads.values()),
        "global_writes": sum(sig.global_writes.values()),
        "call_targets": sum(sig.call_targets.values()),
        "call_shapes": sum(sig.call_shapes.values()),
        "return_arity": sum(sig.return_arity.values()),
        "test_ops": sum(sig.opcode_counts[op] for op in TEST_OPCODES),
        "n_natural_loops": loops,
        "n_back_edges": backs,
    }


def _evidence(fields: dict[str, int]) -> str:
    return " ".join(f"{k}={fields[k]}" for k in LOSS_KINDS)


def _shortfalls(orig_sig, pred_sig, orig_fields, pred_fields) -> dict[str, int]:
    """Which of `LOSS_KINDS` fell, and by how much.

    The five `Counter`-backed fields are compared **per key** and the four
    opcode-backed `test_ops` per **opcode**, not on their totals: a
    predecessor that reads `a` twice more and `b` twice less has lost a global
    read even though the sum is unchanged, and `snr_common.lua:main_76_2`
    (defect 2) is the measured instance of exactly that for `test_ops`
    (`EQ` +3, `TESTSET` -3). `n_natural_loops`/`n_back_edges` are scalars and
    are compared as such.
    """
    out: dict[str, int] = {}
    for k in ("global_reads", "global_writes", "call_targets", "call_shapes",
              "return_arity"):
        a, b = getattr(orig_sig, k), getattr(pred_sig, k)
        lost = sum(a[key] - b[key] for key in a if a[key] > b[key])
        if lost:
            out[k] = lost
    lost = sum(max(0, orig_sig.opcode_counts[op] - pred_sig.opcode_counts[op])
               for op in TEST_OPCODES)
    if lost:
        out["test_ops"] = lost
    for k in ("n_natural_loops", "n_back_edges"):
        if orig_fields[k] > pred_fields[k]:
            out[k] = orig_fields[k] - pred_fields[k]
    return out


def _path_name(path: tuple[int, ...]) -> str:
    """`(76, 2)` -> `main_76_2`, the repo-wide proto-path spelling."""
    return "main" + "".join(f"_{i}" for i in path)


def _subprotos(proto, path: tuple[int, ...] = ()) -> dict[tuple[int, ...], object]:
    out = {path: proto}
    for i, sub in enumerate(proto.subprotos):
        out.update(_subprotos(sub, path + (i,)))
    return out


class MissingPath(Exception):
    """A proto path present in the original tree and absent from the
    predecessor's. Not swallowed: the sweep's denominator is 1944 pairs and a
    silently smaller one would weaken every "no proto loses X" claim in the
    report. Measured 2026-08-14: 0 instances."""


def sweep_file(corpus_dir: Path, pred_dir: Path, name: str) -> list[ProtoLoss]:
    """Every proto in `name` whose predecessor side lost one of `LOSS_KINDS`.

    The predecessor is compiled with `strip=not carries_debug(original)`,
    `verify.certify.certify_l3`'s precedent -- see `predcorpus.load_pred_proto`
    for what compiling it unstripped costs. It changes nothing that this
    module reads (no counter here touches `lineinfo`, `locvars` or the upvalue
    name table), and is passed anyway for the same reason `_fingerprint_one`
    passes it: being right by construction costs one call.
    """
    from pyluadec import ingest
    from pyluadec.predcorpus import load_pred_proto
    from pyluadec.verify.certify import carries_debug
    from pyluadec.verify.semantic_score import collect_proto_signatures

    original = ingest.load_file(Path(corpus_dir) / name)
    candidate = load_pred_proto(Path(pred_dir), name,
                                strip=not carries_debug(original))
    osigs = collect_proto_signatures(original)
    psigs = collect_proto_signatures(candidate)
    oprotos, pprotos = _subprotos(original), _subprotos(candidate)

    out: list[ProtoLoss] = []
    for path in sorted(osigs):
        if path not in psigs:
            raise MissingPath(f"{name}:{_path_name(path)}")
        of = _fields(osigs[path], oprotos[path])
        pf = _fields(psigs[path], pprotos[path])
        losses = _shortfalls(osigs[path], psigs[path], of, pf)
        if not losses:
            continue
        ev = (_evidence(of), _evidence(pf))
        if not json_safe(list(ev)):
            raise ValueError(f"non-ASCII in loss-sweep evidence: {name}")
        out.append(ProtoLoss(name, _path_name(path), ev, losses))
    return out


def sweep(files=None, *, corpus_dir=None, pred_dir=None) -> dict[str, ProtoLoss]:
    """`{"<file>:<path>": ProtoLoss}` over every proto pair in the corpus.

    Single-threaded on purpose. The work is CPython bytecode decoding and CFG
    construction, which the GIL serialises anyway; measured 2026-08-14, an
    8-thread `ThreadPoolExecutor` over the same 229 files came in at 3.09s
    against 3.4s serial, a 9% return for a thread pool in a suite gate.
    """
    corpus_dir = Path(corpus_dir or os.environ["PYLUADEC_CORPUS_DIR"])
    pred_dir = Path(pred_dir or os.environ["PYLUADEC_PRED_CORPUS_DIR"])
    names = (sorted(f.name for f in corpus_dir.glob("*.lua"))
             if files is None else list(files))
    out: dict[str, ProtoLoss] = {}
    for name in names:
        for row in sweep_file(corpus_dir, pred_dir, name):
            out[row.key] = row
    return out


def n_pairs(files=None, *, corpus_dir=None) -> int:
    """How many proto pairs a `sweep()` over `files` covers -- the denominator
    every "N protos lose X" statement in the report is against."""
    from pyluadec import ingest
    corpus_dir = Path(corpus_dir or os.environ["PYLUADEC_CORPUS_DIR"])
    names = (sorted(f.name for f in corpus_dir.glob("*.lua"))
             if files is None else list(files))
    return sum(len(_subprotos(ingest.load_file(corpus_dir / n))) for n in names)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file", action="append", dest="files", default=None,
                    help="corpus-relative filename; repeatable (default: all)")
    ap.add_argument("--json", default=None,
                    help="also write the rows as JSON to this path")
    args = ap.parse_args(argv)

    rows = sweep(args.files)
    unexpected, moved, gone = adjudicate_pins(
        {k: r.evidence for k, r in rows.items()}, pin_evidence())

    per_sweep: dict[int, set[str]] = {}
    for key, r in rows.items():
        for kind in r.losses:
            per_sweep.setdefault(SWEEPS[kind], set()).add(key)
    print(f"{len(rows)} proto(s) lost something over "
          f"{n_pairs(args.files)} proto pair(s); "
          f"{len(rows) - len(unexpected)} pinned")
    for s in sorted(set(SWEEPS.values())):
        print(f"  sweep {s}: {len(per_sweep.get(s, ()))} proto(s) "
              f"[{', '.join(k for k, v in SWEEPS.items() if v == s)}]")
    for key in sorted(rows):
        r = rows[key]
        pin = LOSS_PINS.get(key)
        losses = " ".join(f"{k}-{v}" for k, v in r.losses.items())
        print(f"  {key:34s} {losses}")
        if pin:
            print(f"      {pin.verdict}/{pin.defect}/{pin.basis}: {pin.note}")
        else:
            print("      UNADJUDICATED")
    if unexpected:
        print(f"  UNPINNED loss(es): {unexpected}")
    if moved:
        print(f"  pinned evidence moved: {moved}")
    if gone:
        print(f"  pinned loss(es) converged or vanished: {gone}")

    if args.json:
        doc = {"version": VERSION, "n_pairs": n_pairs(args.files),
               "rows": [asdict(r) | {"evidence": list(r.evidence)}
                        for r in (rows[k] for k in sorted(rows))]}
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(doc, indent=1) + "\n")
    return 1 if (unexpected or moved or gone) else 0


if __name__ == "__main__":
    sys.exit(main())

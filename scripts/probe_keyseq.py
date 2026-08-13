"""L2 gate: key-sequence-driven differential execution, with taint and a
branch-coverage badge.

The Lua side is `scripts/probe_keyseq.lua`; that file is the source of truth
for the spec grammar, the trace format, the event budget, the stub-return
policy and what the taint marks mean. This module runs it, refuses to turn a
probe-side failure into a comparable value, and decides the grant.

## The grant rule

A file is granted `L2` when, under one authored key sequence:

1. both sides produce a recognisable trace (no probe-side failure),
2. the two traces are **byte-equal over everything the probe observed**,
3. the run actually consumed the sequence -- at least one `K|` poll event,
4. neither side recorded any **taint**,

5. **at least one authored sequence ran to completion** (`header(...)[0] ==
   "OK"`). A run stopped at `MAX_EVENTS` reports `CAP`, and "byte-equal" then
   means "equal over the first 3000 events"; such a run is still required to
   agree, but it cannot be the ONLY evidence a grant rests on. It CAN still be
   the only evidence for a branch no completing sequence enters -- a known-open
   route with a committed fixture; see `evaluate`, which also says why this is
   "at least one" and not "all" (a measurement, not a preference).

6. **no stub-derived value can decide a branch unobserved** -- the static
   backstop over the original bytecode (`static_taint`) finds none of the six
   kinds of blind site in `_KINDS`,

7. **every proto in the chunk is `L3`**. Condition 6 reads the ORIGINAL, so it
   only speaks for the artifact while the two are field-identical; see
   `evaluate` for the measurement that they otherwise are not.

Anything else refuses, with a reason from `REFUSAL_KINDS`. The badge that
rides along is `cov`: the fraction of the *shipped artifact's protos* the
COMPLETED runs entered (see `coverage` for why it is protos and not basic
blocks, and `evaluate` for why the capped runs are left out of it).

## Taint: two instruments, because one of them is structurally blind

**Runtime marks** (`scripts/probe_keyseq.lua`) see what a metatable can see:

* `cmp:lt` / `cmp:le` / `cmp:eq` -- a stub proxy reached a comparison
  metamethod. Where it applies this is not an approximation: Lua 5.1's
  `OP_LT`, `OP_LE` and `OP_EQ` produce no value, they select the following
  `JMP`, so the metamethod firing *is* a stub value deciding a branch.
  **But `__eq` applies only to proxy-vs-proxy.** `lvm.c`'s `equalobj` is
  `ttype(o1) == ttype(o2) && luaV_equalval(...)`, so `stub == "str"`,
  `stub == nil` and `stub == 1` fire nothing at all. `__lt`/`__le` are
  narrower still: Lua 5.1 raises on mixed types before reaching a metamethod.
* `intro:type` / `intro:rawequal` / `intro:getmetatable` -- a stub proxy was
  introspected. Nothing proves the result reached a branch; it is assumed to
  have.

**The static backstop** (`static_taint`, over the ORIGINAL lifted bytecode)
exists because of that blindness. Measured 2026-08-12, twelve laundering
routes were granted with zero runtime marks -- `== "str"`, `== nil`,
`~= nil`, `== 1`, `== {}`, `#stub > 0`, `next(stub)`, `tostring(stub)`,
`tonumber(stub)`, `stub .. ""`, `select("#", stub)`, `pcall(stub)` -- and the
idiom is not a corner: on the original bytecode it occurs **427 times across
23 of the 229 corpus files** (a `GETGLOBAL "doScriptScene"` whose destination
register is an `EQ` operand within three instructions). The 310-across-20
figure this paragraph used to carry counts `doScriptScene ==` in the decompiled
ARTIFACT text -- a different, 27% smaller population, since three of the 23
ship fallback and never spell the idiom. All twelve routes are now refused.

## What the pair still cannot see

Stated as gaps, not as a complete list -- the previous version of this comment
claimed to be complete and was not, which is what let the twelve routes ship:

* **A stub passed as an ARGUMENT.** `static_taint` is intra-proto and a
  parameter is a root, so `decide(sys.a)` with the comparison inside `decide`
  is not seen. (The RETURN direction -- an accessor handing an engine value
  back -- WAS uncovered for one round and is now caught: a call's result is
  stub-derived unless the callee is provably a base or driver global.)
* **A value stored into a script-built table and read back.** `t.x = stub`
  then `if t.x == "a"`; `SETTABLE` is not tracked, only indexing off a
  stub-derived table or at a stub-derived key.
* **Any other harness state carried between calls.** `waitf(n)` does
  `tonumber(n)`, which is `nil` for a proxy, so `wait(sys.delay)` advances one
  frame instead of N -- and the frame counter decides every later
  `pressButton`. Measured: byte-equal traces, zero runtime marks, empty
  `static_taint`, GRANT. `blind-harness` closes that at the ARGUMENT BOUNDARY
  of the callees in `_CLEAN_CALLEES`; a register may-analysis still cannot
  *follow* taint into the harness, so a future driver that keeps state a stub
  can perturb some other way needs the same treatment at its own boundary.
  **This is the one limit here that is not a propagation gap** -- and this
  list omitted it through M5, while the runbook and
  `docs/reports/m5-quality.md` §4 both named it.
* **`VARARG`.** `local a = ...` compared against a literal is not flagged.

The four above are the residue I could not close, not an inventory of what
exists.

A granted `L2` therefore says "these two programs behaved identically under
this stub policy and this input, over everything the probe observed, and no
*directly* stub-derived value decided a branch we could not observe" -- not
"this decompilation is correct under the real engine".
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Run as `uv run python scripts/probe_keyseq.py`, sys.path[0] is scripts/, not
# the repo root, so `scripts.probe_keyseq` would not resolve. Imported as a
# module by the tests it already resolves and this is a no-op.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROBE = ROOT / "scripts" / "probe_keyseq.lua"

# Every result the probe is allowed to produce and still be COMPARED starts
# with one of these. `SPECFAIL|` and `ENTRYFAIL|` are deliberately absent: a
# mistyped entry name produces the same string on both sides, so treating one
# as a value would grant `L2` for a run that never happened. This is the L1.5
# probe's hardest-won lesson (it shipped once with every probe-side failure
# returning "", which compared equal on all 229 files).
_MARKERS = (b"KEYSEQ1|", b"LOADFAIL|")

REFUSAL_KINDS = ("divergent", "taint", "taint-static", "no-key-poll",
                 "truncated", "not-l3", "probe-error")


class ProbeError(RuntimeError):
    """The probe did not produce a usable result (crash, non-zero exit, a spec
    or entry-point failure, or unrecognisable stdout). Never silently turned
    into a comparable value."""


# --------------------------------------------------------------------------
# The authored key sequences. Data, deliberately: a sequence is an input, not
# an algorithm.
#
# Measured 2026-08-12, on the original side of all 229 corpus files under the
# L1.75 stub policy: exactly five files reach a `pressButton` poll at all, and
# they are the five below. Every other corpus file either never polls input
# (the linear story scripts, which hit the event cap on sheer `vms()` volume,
# something no key sequence changes) or errors before reaching its poll. So
# "which files does L2 apply to" is a measurement, not a choice -- and
# corpus-wide L2 is explicitly not promised for this milestone.
#
# A file may carry MORE than one sequence: every one must pass on its own and
# the coverage badge is the union. `snr_common.lua` needs that -- it holds both
# historical checkpoints (`systemOption.OptionMain`, `systemConfig.ConfigMain`)
# and neither is reachable from the other.
#
# Grammar: see `scripts/probe_keyseq.lua`'s header.
#
# ## THE FRAME MODEL, and why every `k=` frame below is a measured one
#
# A `k=<frame>,<KEY>` directive is only ever READ if the target polls on that
# exact frame. The frame counter is advanced by `wait` alone
# (`probe_keyseq.lua`'s `waitf`: `frame += max(floor(n), 1)`), and these menu
# loops answer an accepted press with `wait(5)` and then close the iteration
# with `wait(1)` -- so an accepted press costs **6 frames**, and a directive
# scheduled 1 or 2 frames after another is delivered while the loop is inside
# a `wait` and is never seen.
#
# The sequences shipped through M5 task 9 were written on 1-frame spacing.
# Measured in task 10 round 1, on the original side of all five files: of the
# 13 sequences, 11 carry `k=` directives and **all 11 dropped at least one**.
# Nine landed exactly their first directive; `snr_common`#1 landed 2 of 5; and
# BOTH `snr_music` sequences landed **0 of their directives**, because that
# file's first poll is at frame **31** and every directive was delivered
# before it. Nine of the eleven were then reachable by re-timing alone; the
# two that were not each ended in a directive whose key is not polled on the
# path the rest of the sequence takes (`snr_common`#1's trailing `CIRCLE`,
# which `OptionMain` polls only on the L/R page this key order never enters,
# and `snr_graphic`#2's second `CROSS`, after the first has already left the
# loop). Those two directives were dropped rather than left as text that is
# delivered and never read.
#
# Every frame below was derived by probing: directive *i* is placed at the
# first frame after directive *i-1* at which the target actually polls that
# key. Re-measured after the change: **11 of 11 land every directive.** No L2
# verdict moved (still 1 granted / 4 `taint-static`) and `snr_lib`'s badge is
# `cov` 1.0 either way, so `corpus/ledger.jsonl` is unchanged. The one cost is
# in the BLOCK diagnostic, which never enters the ledger: `snr_lib`'s interval
# goes [0.386, 0.9474] -> [0.3509, 0.9123] of 57 blocks (upper bound 54 -> 52).
# Two blocks were reached only by the old timing's accident of holding the tail
# key across a `wait`, and three longer honest variants were measured without
# recovering them.
# --------------------------------------------------------------------------
KEY_SEQUENCES: dict[str, tuple[str, ...]] = {
    # The debug menu: UP is clamped at the top, four DOWNs walk to the bottom
    # entry and are clamped there, CIRCLE selects. The third sequence is the
    # degenerate one -- CIRCLE held from the first frame -- kept because it
    # reaches the "already pressed" gate (`l1_2 == 0`) that the others skip.
    "snr_lib.lua": (
        "k=1,UP;k=7,DOWN;k=13,DOWN;k=19,DOWN;k=25,DOWN;k=31,CIRCLE;tail=CIRCLE",
        "k=1,DOWN;k=7,DOWN;k=13,CIRCLE;tail=CIRCLE",
        "tail=CIRCLE",
    ),
    # The gallery browsers. Both poll eight buttons (UP/DOWN/LEFT/RIGHT/L/R/
    # CIRCLE/CROSS); CROSS is what leaves, CIRCLE what descends. The long gaps
    # before `CIRCLE` are not padding: they are the frame at which the loop
    # next polls that key after the preceding press, which is what the
    # derivation above returns. Why the loop takes that long there was not
    # investigated.
    "snr_graphic.lua": (
        "k=1,RIGHT;k=8,DOWN;k=15,L;k=17,R;k=57,CIRCLE;k=59,CROSS;tail=CROSS",
        "k=1,DOWN;k=8,RIGHT;k=15,LEFT;k=22,UP;k=29,L;k=31,R;k=71,CIRCLE;"
        "k=73,CROSS;tail=CROSS",
        "k=1,DOWN;k=8,DOWN;k=15,CIRCLE;tail=CIRCLE",
    ),
    "snr_memory.lua": (
        "k=1,DOWN;k=8,RIGHT;k=15,LEFT;k=22,UP;k=29,L;k=31,R;k=71,CIRCLE;"
        "k=73,CROSS;tail=CROSS",
        "k=1,DOWN;k=8,DOWN;k=15,CIRCLE;tail=CIRCLE",
    ),
    # This file does not poll at all until frame 31 (its opening animation),
    # which is why its directives start there rather than at 1.
    "snr_music.lua": (
        "k=31,DOWN;k=36,RIGHT;k=41,LEFT;k=46,UP;k=51,CIRCLE;k=54,CROSS;"
        "tail=CROSS",
        "k=31,DOWN;k=36,DOWN;k=41,CIRCLE;tail=CIRCLE",
    ),
    # The two historical checkpoints from the predecessor's playbook
    # (`DEBUG_KEY_SEQUENCE_HARNESS.md`): `OptionMain`'s RIGHT/LEFT must keep
    # two mutually exclusive clamps, and `ConfigMain`'s CIRCLE branch must
    # keep its gate/wait. Both are METHODS on the instances the chunk builds
    # (`systemOption = SystemOption.new()`), not on the class tables, which is
    # why the entry names are the lower-case globals.
    #
    # These two exist to make the entry points REACHABLE by the gate. What the
    # checkpoints ASSERT lives in `tests/test_keyseq_checkpoints.py`, which
    # authors its own longer sequences there rather than here: those are a
    # regression instrument for one file, and adding them here would make them
    # part of the L2 grant rule and of `corpus/ledger.jsonl`.
    #
    # The third sequence drives the whole chunk instead, and is what makes the
    # `pressButton` loop inside `autoSystemSave` reachable.
    "snr_common.lua": (
        "entry=systemOption.OptionMain;k=1,RIGHT;k=7,RIGHT;k=13,LEFT;"
        "k=19,DOWN;tail=CROSS",
        "entry=systemConfig.ConfigMain;k=1,DOWN;k=7,DOWN;k=13,CIRCLE;"
        "tail=CROSS",
        "tail=CROSS",
    ),
}

# The verdict every authored file is expected to reach, asserted two-
# directionally by `tests/test_l2_keyseq.py` so that a file which silently
# stops being granted, and a refusal that quietly converges, both fail.
#
# Measured 2026-08-12, after the static backstop landed: **one of the five is
# granted**. The other four all carry `blind-compare` sites -- a stub-derived
# value compared against something that cannot fire `__eq` -- and are refused
# whole-file, because the analysis is static and does not know which of those
# sites the key sequences actually reach. Their sequences are kept: they still
# drive, their traces still agree, and if the analysis or the emitter ever
# makes one of them clean, that shows up here as a change to be adjudicated
# rather than as silence.
EXPECTED_VERDICT: dict[str, str] = {
    "snr_lib.lua": "granted",
    "snr_common.lua": "taint-static",
    "snr_graphic.lua": "taint-static",
    "snr_memory.lua": "taint-static",
    "snr_music.lua": "taint-static",
}


def probe_raw(payload: bytes, *, is_source: bool, spec: str,
              timeout: float = 120.0) -> bytes:
    """Run the L2 probe over one chunk and return its raw stdout.

    Bytes, not str: the trace embeds string constants straight from the
    corpus, which is Japanese game text. Nothing here decodes them -- the
    digest is taken over the bytes, so no decoding policy can affect what the
    gate compares.
    """
    from pyluadec import oracle
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        # stdin=DEVNULL, not inherited: a chunk that calls io.read() would
        # otherwise block on whatever the caller's stdin happens to be.
        r = subprocess.run([str(oracle.lua_sz4()), str(PROBE), str(f), spec],
                           capture_output=True, stdin=subprocess.DEVNULL,
                           timeout=timeout, cwd=td)
    # `returncode != 0` is DEFENSIVE and subsumed in every shape I could
    # build. Tried: neutering it leaves the module green, because the probe
    # exits 0 through `osexit(0)` on every path it controls, and every path it
    # does NOT control (a missing script, a segfault) produces stdout that
    # fails the `_MARKERS` check two lines below. It survives because a crash
    # AFTER a valid trace was written would otherwise pass, and because its
    # message names the exit status where the marker check cannot. (M3,
    # round 2.)
    if r.returncode != 0:
        raise ProbeError(
            f"probe exited {r.returncode} (is_source={is_source}, "
            f"spec={spec!r}); "
            f"stderr={r.stderr.decode('utf-8', 'replace')!r}; "
            f"stdout={r.stdout[:400].decode('utf-8', 'replace')!r}")
    if not r.stdout.startswith(_MARKERS):
        raise ProbeError(
            f"probe produced an unrecognisable or non-comparable result "
            f"(is_source={is_source}, spec={spec!r}); expected one of "
            f"{[m.decode() for m in _MARKERS]}; "
            f"stdout={r.stdout[:400].decode('utf-8', 'replace')!r}; "
            f"stderr={r.stderr.decode('utf-8', 'replace')!r}")
    return r.stdout


def header(trace: bytes) -> tuple[str, int, int]:
    """`(status, event_count, taint_count)` from line 1. status is OK / CAP /
    INSN, or LOADFAIL with counts of -1 (a chunk that did not load recorded
    nothing)."""
    parts = trace.split(b"\n", 1)[0].split(b"|")
    if parts[0] == b"LOADFAIL":
        return "LOADFAIL", -1, -1
    return parts[1].decode("ascii"), int(parts[2]), int(parts[3])


def taint_marks(trace: bytes) -> list[bytes]:
    """The `T|<kind>|<name>` lines, in the order the probe emitted them
    (sorted). Bytes, like everything else derived from a trace -- the name is
    a dotted path built from the chunk's own global names."""
    return [l for l in trace.split(b"\n") if l.startswith(b"T|")]


def poll_count(trace: bytes) -> int:
    """How many `pressButton` polls the run made. Zero means the authored
    sequence was never consulted, which is a refusal: it would otherwise be
    possible to grant `L2` to a file the sequence has nothing to do with."""
    return sum(1 for l in trace.split(b"\n") if l.startswith(b"K|"))


def covered_protos(trace: bytes) -> int:
    """The number of distinct protos of the target the run ENTERED, from the
    `COVF|` line a `cov=1` run appends. `-1` when the probe was not asked for
    coverage, so a missing measurement can never be read as zero."""
    for line in trace.split(b"\n"):
        if line.startswith(b"COVF|"):
            return int(line[5:])
    return -1


def covered_lines(trace: bytes) -> set[int]:
    """The source lines the run executed, from the `COV|` line a `cov=1` run
    appends. Empty set when the probe was not asked for coverage."""
    for line in trace.split(b"\n"):
        if line.startswith(b"COV|"):
            body = line[4:]
            return {int(x) for x in body.split(b",") if x}
    return set()


def first_difference(orig: bytes, dec: bytes) -> tuple[int, bytes, bytes]:
    """`(line number, original line, decompiled line)` for the first differing
    trace line, as raw bytes -- the same type the trace itself is in. Decode
    only at the point of display."""
    a = orig.split(b"\n")
    b = dec.split(b"\n")
    for i in range(max(len(a), len(b))):
        la = a[i] if i < len(a) else b"<end of trace>"
        lb = b[i] if i < len(b) else b"<end of trace>"
        if la != lb:
            return (i + 1, la, lb)
    return (0, b"", b"")


def dump_mismatch(name: str, orig: bytes, dec: bytes, where: Path) -> Path:
    where.mkdir(parents=True, exist_ok=True)
    (where / f"{name}.original.l2trace").write_bytes(orig)
    (where / f"{name}.decompiled.l2trace").write_bytes(dec)
    return where


# --------------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------------

def block_entry_lines(artifact_src: bytes) -> tuple[list[int], int]:
    """`(entry line of every basic block in the artifact, collisions)`.

    The artifact is recompiled with the repo's `luac_sz4` WITHOUT `-s`, so it
    carries `lineinfo`; every proto in the result is lifted and run through
    the existing `cfg.blocks.build_cfg`, and each basic block contributes the
    source line of its first instruction.

    **Why the artifact and not the original.** The original corpus bytecode is
    stripped -- `lineinfo` is empty and `debug.getinfo(...).currentline` is -1
    for every frame -- so there is no way to observe which of ITS blocks a run
    entered from inside Lua. Coverage is therefore a statement about the
    shipped artifact's blocks. That is also why the badge is per FILE: for the
    13 corpus files that ship fallback or hybrid text, our artifact's proto
    tree is not in field-for-field correspondence with the original's (that
    correspondence is exactly what `L3` certification establishes, and those
    files do not have it), so a per-proto attribution would be inventing a
    mapping the pipeline does not have.

    `collisions` is the number of blocks whose entry line is shared with at
    least one other block -- the measured size of the over-approximation, since
    a block whose entry line was executed by a *different* block on the same
    line counts as entered. Reported rather than hidden.
    """
    from pyluadec import oracle
    from pyluadec.cfg.blocks import build_cfg
    from pyluadec.ingest import load_bytes
    from pyluadec.lift import lift_proto

    root = load_bytes(oracle.compile_source(artifact_src))
    lines: list[int] = []

    def walk(p):
        fn = lift_proto(p)
        cfg = build_cfg(fn)
        for start in cfg.blocks:
            lines.append(p.lineinfo[start - 1])
        for sp in p.subprotos:
            walk(sp)

    walk(root)
    seen: dict[int, int] = {}
    for ln in lines:
        seen[ln] = seen.get(ln, 0) + 1
    collisions = sum(n for n in seen.values() if n > 1)
    return lines, collisions


# The coverage run executes the artifact with this many blank lines prepended,
# and the reported lines are shifted back. It removes the one flaw in the
# probe's first-sight line classifier by construction.
#
# The classifier decides "is this line number the target's?" once per distinct
# line, because asking `debug.getinfo` on every line event costs 8x (measured
# on 6,000,004 line events: 0.31s vs 2.39s). Without the shift, a line NUMBER
# first seen from the probe's own source -- its recorder and proxy metamethods
# run interleaved with the target -- is classified foreign for the rest of the
# run, and the target's line with that number is then never counted. Measured
# 2026-08-12 on a 602-line straight-line fixture where every line executes:
# 60 of 602 lines lost (10.0%), and the lost line numbers are exactly the
# probe's own executed ranges (129-179 = the serialisers, 308-399 = the proxy
# metamethods, 549-560 = the invocation loop).
#
# Pushing the artifact past every line number the probe can occupy makes the
# collision impossible instead of merely rare. This only affects the BLOCK
# diagnostic -- the ledger badge is proto coverage, which has no line in it --
# but the diagnostic is quoted in the runbook, so it has to be right.
# `tests/test_l2_keyseq.py` pins both halves: that LINE_SHIFT still clears both
# probe scripts, and that shifting does not change what the program does.
LINE_SHIFT = 2000


@dataclass(frozen=True)
class Coverage:
    """Two measurements of one run, kept apart on purpose.

    `protos_entered / protos` is the BADGE, and it is the only one that
    reaches `corpus/ledger.jsonl`. `blocks_*` is a diagnostic printed by the
    CLI and quoted in the runbook.
    """
    protos_entered: int
    protos: int
    blocks_upper: int         # blocks whose entry LINE was executed
    blocks_lower: int         # ... restricted to lines that name one block
    blocks: int
    collisions: int           # blocks sharing an entry line with another

    @property
    def fraction(self) -> float:
        # 4 decimals: the ledger has to be a byte-stable fixed point of its
        # own generator, and a bare float would put the platform's repr in the
        # committed file.
        # `if self.protos` is DEFENSIVE. Tried: no artifact can compile to
        # zero protos (a chunk is itself one), so neutering it to a bare
        # division leaves the module green; it exists so a future caller that
        # constructs a `Coverage` by hand cannot get a ZeroDivisionError out of
        # a property. (M3, round 2.)
        return round(self.protos_entered / self.protos, 4) if self.protos else 0.0

    @property
    def block_interval(self) -> tuple[float, float]:
        if not self.blocks:
            return (0.0, 0.0)
        return (round(self.blocks_lower / self.blocks, 4),
                round(self.blocks_upper / self.blocks, 4))


class CoverageError(RuntimeError):
    """The coverage measurement could not be trusted (see `coverage`)."""


def coverage(artifact_src: bytes, specs: Sequence[str]) -> Coverage:
    """Run the artifact once more per spec with `cov=1`.

    ## The badge is PROTO coverage, and why it had to stop being block coverage

    Block coverage is attributed by source line -- there is no other seam --
    so it moves when the emitter moves a newline. Measured on one program,
    one sequence, the same 10 blocks: the block interval reads **[0.30, 0.50]
    spread over lines and [0.00, 0.90] compacted**, while proto coverage is
    0.6667 either way. That breaks a project-level invariant, not just a
    number: CLAUDE.md defines a
    presentation-layer change as one that leaves `corpus/ledger.jsonl`
    byte-unchanged, and M5 task 7 shipped five printer changes on exactly that
    evidence. A layout-sensitive `cov` in the ledger would have made those
    commits look like reach regressions, and would make `ratchet_diff`'s
    `l2-coverage-downgrade` fire on cosmetics.

    Proto coverage has no line in it at all. The probe counts distinct protos
    ENTERED from `call` hook events; the denominator is the number of protos
    in the compiled artifact. Neither depends on where newlines go.

    The one place a line number still appears is the de-duplication KEY --
    `(linedefined, lastlinedefined)`, so two closures of one proto count once
    -- and that key is only sound while it is injective over the artifact's
    protos. **Checked here, per run, rather than assumed**: measured
    2026-08-12 over eight artifacts (the five authored files plus snr_novel,
    snr_crd_0 and config), 390 protos and 390 distinct keys, injective
    everywhere. A hand-written one-liner like
    `local f = function() end g = function() end` does collide, which is why
    this is a check and not a remark.

    ## The block diagnostic, and its width

    Kept because it is the finer instrument when it is trustworthy, reported
    as an INTERVAL because it is a bound, not a value:

    * upper = blocks whose entry line ran (a block sharing a line with an
      executed neighbour is credited),
    * lower = the same, restricted to lines that name exactly one block.

    `collisions` is the number of blocks sharing an entry line, i.e. the width
    of the ignorance. Never enters the ledger.

    An extra process per spec, not a reuse of the comparison runs: the two
    runs a grant compares should differ in no respect at all, including the
    hook mask.
    """
    shifted = b"\n" * LINE_SHIFT + artifact_src
    hit: set[int] = set()
    entered = -1
    for spec in specs:
        t = probe_raw(shifted, is_source=True, spec=_with_cov(spec))
        raw = covered_lines(t)
        # `ln > LINE_SHIFT` is DEFENSIVE, not load-bearing. Tried: neutering
        # it to `for ln in raw` leaves the whole module green, because the
        # probe only ever puts lines it classified as the TARGET's into
        # `cov_ours`, and every target line is past the shift. It makes the
        # subtraction total rather than trusting that classification, which is
        # the one thing this file already had to fix once (M3, round 2).
        hit |= {ln - LINE_SHIFT for ln in raw if ln > LINE_SHIFT}
        n = covered_protos(t)
        if n < 0:
            raise CoverageError(f"no COVF line for spec {spec!r}")
        # MAX over the sequences, not a union: proto identity is not
        # transferable between two processes (the de-dup key is per-artifact
        # but the counts are not addable), and a max is the conservative read.
        entered = max(entered, n)
    lines, collisions, n_protos, n_keys = _artifact_shape(artifact_src)
    if n_keys != n_protos:
        raise CoverageError(
            f"(linedefined, lastlinedefined) is not injective over this "
            f"artifact ({n_protos} protos, {n_keys} distinct keys); the proto "
            f"coverage count would silently merge protos")
    by_line: dict[int, int] = {}
    for ln in lines:
        by_line[ln] = by_line.get(ln, 0) + 1
    # No `min(entered, n_protos)` clamp: it was unexercisable (the `call`
    # hook filters on `info.source == tsource`, and the injectivity check
    # above makes the de-dup key exact, so `COVF` equals the artifact's proto
    # count at most). Neutering the clamp left the whole module green, which
    # is the definition of decoration -- New-4.
    return Coverage(
        protos_entered=entered, protos=n_protos,
        blocks_upper=sum(1 for ln in lines if ln in hit),
        blocks_lower=sum(1 for ln in lines if ln in hit and by_line[ln] == 1),
        blocks=len(lines), collisions=collisions)


def _artifact_shape(artifact_src: bytes) -> tuple[list[int], int, int, int]:
    """`(block entry lines, colliding blocks, protos, distinct proto keys)`."""
    lines, collisions = block_entry_lines(artifact_src)
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    root = load_bytes(oracle.compile_source(artifact_src))
    keys: list[tuple[int, int]] = []

    def walk(p):
        keys.append((p.linedefined, p.lastlinedefined))
        for sp in p.subprotos:
            walk(sp)

    walk(root)
    return lines, collisions, len(keys), len(set(keys))


def _with_cov(spec: str) -> str:
    return spec if "cov=1" in spec.split(";") else (spec + ";cov=1" if spec else "cov=1")


# --------------------------------------------------------------------------
# The static backstop: stub values that decide a branch the runtime cannot see
# --------------------------------------------------------------------------
#
# Runtime marking is structurally blind to most of the idiom it was supposed
# to catch, and this was found by review rather than by construction. Lua
# 5.1's `equalobj` (`lvm.c`) is
#
#     ttype(o1) == ttype(o2) && luaV_equalval(L, o1, o2)
#
# so `__eq` is consulted ONLY when both operands are tables sharing the
# handler. A stub proxy compared against a string, a number, `nil` or a
# script-built table fires no metamethod at all: the branch is decided by our
# stubbing and nothing observes it. Measured 2026-08-12, twelve routes, every
# one of them granted with zero taint marks:
#
#     stub == "str" / == nil / ~= nil / == 1 / == {}, #stub > 0,
#     next(stub) == nil, tostring(stub) == "x", tonumber(stub),
#     stub .. "" == "x", select("#", stub) == 1, pcall(stub)
#
# And it is not a corner: on the original bytecode the idiom occurs 427
# times across 23 of the 229 corpus files (a `GETGLOBAL "doScriptScene"` whose
# destination is an `EQ` operand within three instructions). The 310/20 figure
# this comment used to carry counts `doScriptScene ==` in the decompiled
# ARTIFACT text, which is a different -- and 27% smaller -- population.
#
# There is no runtime fix -- no Lua 5.1 value can observe a comparison against
# a value of a different type. So the grant gets a STATIC backstop over the
# ORIGINAL lifted bytecode instead, and the runtime marks are kept for the
# routes they do see (they are the more precise instrument where they apply,
# since they only fire on paths actually executed).

# Every name the probe's environment resolves BEFORE it would build a stub
# proxy. `env.__index` tries `envfields[k]` (globals the chunk wrote), then
# `DRIVER[k]`, then `G[k]`, then makes a proxy -- so a `GETGLOBAL` of anything
# in this set or written by the chunk is not stub-derived.
# Re-derived from the vendored interpreter itself, not from memory, by
# `tests/test_l2_keyseq.py::test_the_base_global_set_is_the_interpreter_s_own`.
_BASE_GLOBALS = frozenset("""
_G _VERSION arg assert collectgarbage coroutine debug dofile error gcinfo
getfenv getmetatable io ipairs load loadfile loadstring math module newproxy
next os package pairs pcall print rawequal rawget rawset require select setfenv
setmetatable string table tonumber tostring type unpack xpcall
""".split())

# The probe's own driver overrides. This is a HAND COPY of
# `scripts/probe_keyseq.lua`'s `DRIVER` table, and a name that disappears from
# the Lua side without disappearing here would silently SHRINK the seed set --
# the same failure `_BASE_GLOBALS`' derivation test exists to prevent, in the
# unsound direction. `tests/test_l2_keyseq.py::
# test_the_driver_global_set_matches_the_probe_s_own_driver_table` parses the
# Lua table out of the probe's text and requires the two to be equal (New-6).
_DRIVER_GLOBALS = frozenset({"pressButton", "wait", "type", "rawequal",
                             "getmetatable"})


def driver_globals_in_probe() -> frozenset[str]:
    """The keys of `scripts/probe_keyseq.lua`'s `DRIVER` table, read out of the
    file. Plain byte scanning, no regex, matching the repo rule for the probe
    side even though this is script code."""
    text = PROBE.read_text(encoding="utf-8")
    i = text.index("local DRIVER = {")
    body = text[i + len("local DRIVER = {"):text.index("}", i)]
    out = set()
    for part in body.split(","):
        head = part.split("=", 1)[0].strip()
        if head:
            out.add(head)
    return frozenset(out)


# Base globals whose VALUE is, or reflects, the environment. `env.__index`
# resolves these for real -- they are not proxies -- but what they hand back is
# the STUB environment's own shape, which is exactly as much an artifact as a
# proxy is. Measured 2026-08-12: `_G` and `getfenv()` route straight to a
# proxy (`local q = getfenv().doScriptScene` traces as `C|miss|1|@doScriptScene`
# and granted), and `_G.doScriptScene == nil` is decided by the fact that the
# probe keeps the chunk's globals in `envfields` rather than in `_G` at all.
# These are therefore treated as stub seeds, not as clean reads. The corpus
# reads none of them (measured: 0 `GETGLOBAL _G`, 0 `getfenv`), so this costs
# nothing.
_REFLECTIVE_BASE = frozenset({
    "_G", "getfenv", "setfenv", "load", "loadstring", "loadfile", "dofile",
    "require", "module", "package", "arg", "newproxy",
})

# Callees whose RESULT may be treated as clean -- and only when no argument in
# the call window is stub-derived.
#
# This replaces "anything in `_BASE_GLOBALS` or `_DRIVER_GLOBALS`", which was
# round 2's fix for New-3 and re-opened New-3 in the same breath: it declared a
# list of callees trusted **without checking what those callees do**. Measured,
# every one of these granted with a proxy visibly reaching the comparison:
#
#     local ok, v = pcall(f)   -- pcall FORWARDS the callee's returns
#     local x = assert(sys.a)  -- assert is the identity function
#     rawget(_G, "doScriptScene") == nil    -- reflects the environment
#
# So the rule is now an explicit allowlist of functions that provably cannot
# hand back a value derived from their arguments or from the environment: the
# probe's own driver overrides, plus the two base coercions. Everything else --
# including every other base global -- returns a stub. The corpus calls only
# `wait`, `pressButton`, `string`, `select`, `math` and `pairs` as recognised
# callees, and `snr_lib.lua` (the one granted file) calls no base global at
# all, so the narrowing costs no reach.
_CLEAN_CALLEES = frozenset({
    "pressButton",   # driver: returns the scripted boolean, by construction
    "wait",          # driver: returns nil
    "type", "rawequal", "getmetatable",   # driver overrides; string/boolean/
                                          # our own metatable, never an argument
    "tostring", "tonumber",               # coercions: string / number / nil
    "print",                              # returns nothing
})


# Reading any of these means the chunk can substitute or rewrite the very
# environment the exemption sets describe, so name-by-name reasoning stops
# being possible. `_shadowed_names` only sees `SETGLOBAL`; measured, four more
# mechanisms reach the same end and each granted:
#
#     _G.tostring = sys.conv            -- SETTABLE on the real _G
#     rawset(_G, "tostring", sys.conv)  -- same, through a function
#     getfenv().tostring = sys.conv     -- through env.__newindex
#     setfenv(1, sys.env)               -- replaces the environment WHOLESALE,
#                                          so every exempt base read is a proxy
#
# The last one is why this is a blanket answer rather than four more cases:
# after `setfenv` the exemption SET is wrong, not one name in it. Measured
# across all 229 files / 1944 protos, the corpus reads none of these
# (`GETGLOBAL` counts: `_G` 0, `getfenv` 0, `setfenv` 0, `rawset` 0, `rawget`
# 0, `require` 0, `package` 0, `arg` 0, `newproxy` 0, `load`/`loadstring`/
# `loadfile`/`dofile`/`module` 0) and writes 0 base or driver names with
# `SETGLOBAL`, so dropping every exemption on sight costs nothing.
_ENV_SUBSTITUTING = frozenset({
    "_G", "getfenv", "setfenv", "rawset", "rawget", "load", "loadstring",
    "loadfile", "dofile", "require", "module", "package", "newproxy", "arg",
})


def _reads_globals(root) -> set[str]:
    from pyluadec.lift.opcodes import Op, decode

    out: set[str] = set()

    def walk(p):
        for i, w in enumerate(p.code):
            ins = decode(w, i + 1)
            if ins.op is Op.GETGLOBAL:
                out.add(p.constants[ins.bx].decode("latin-1"))
        for sp in p.subprotos:
            walk(sp)

    walk(root)
    return out


def _substitutes_environment(root) -> bool:
    """Does this chunk so much as MENTION a name that can rewrite or replace
    the environment? If so no exemption survives -- see `_ENV_SUBSTITUTING`."""
    return bool(_reads_globals(root) & _ENV_SUBSTITUTING)


def _shadowed_names(root) -> set[str]:
    """Base/driver names this chunk ever writes as a global.

    `env.__index` consults `envfields` BEFORE `G`, so a chunk-level
    `tostring = sys.conv` makes every later `tostring(...)` call a proxy.
    Measured: that fixture granted. A shadowed name loses both exemptions --
    it becomes a stub seed and stops being a clean callee -- for the whole
    chunk, without any attempt to order the write against the reads (the same
    reasoning that killed the `read - written` exemption in round 2).
    """
    from pyluadec.lift.opcodes import Op, decode

    out: set[str] = set()

    def walk(p):
        for i, w in enumerate(p.code):
            ins = decode(w, i + 1)
            if ins.op is Op.SETGLOBAL:
                n = p.constants[ins.bx].decode("latin-1")
                if n in _BASE_GLOBALS or n in _DRIVER_GLOBALS:
                    out.add(n)
        for sp in p.subprotos:
            walk(sp)

    walk(root)
    return out


def _stub_globals(root) -> set[bytes]:
    """Every global name this chunk READS that the probe environment resolves
    to something other than a real, non-reflective library value.

    ## There is no "the chunk defines it, so it is not a stub" exemption

    There was, for one round: `read - written`, computed over the whole chunk
    with no ordering. It was unsound in exactly the way the runtime marks were
    (round-1 C1). `env.__index` consults `envfields`, which is EMPTY until the
    chunk actually executes the write, so a global read before its write -- or
    whose write is inside a function nobody calls -- is a proxy at that read.
    Three fixtures granted through it, including laundering THROUGH it
    (`stash = sys.a` then `if stash == "x"`). Removing it was measured to cost
    no reach: `snr_lib` has 0 globals that are both read and written,
    `snr_common` has 72.

    What IS exempt is `_BASE_GLOBALS` -- names `env.__index` answers from the
    real `_G` -- minus `_REFLECTIVE_BASE` and minus anything this chunk
    shadows.
    """
    from pyluadec.lift.opcodes import Op, decode

    read: set[bytes] = set()

    def walk(p):
        for i, w in enumerate(p.code):
            ins = decode(w, i + 1)
            if ins.op is Op.GETGLOBAL:
                read.add(p.constants[ins.bx])
        for sp in p.subprotos:
            walk(sp)

    walk(root)
    if _substitutes_environment(root):
        return set(read)
    shadowed = _shadowed_names(root)
    exempt = (_BASE_GLOBALS | _DRIVER_GLOBALS) - _REFLECTIVE_BASE - shadowed
    return {n for n in read if n.decode("latin-1") not in exempt}


# Library functions that turn a stub proxy into a plain value a branch can
# then read without any metamethod firing. `type`, `rawequal` and
# `getmetatable` are also marked at runtime; the rest have no runtime seam at
# all.
_LAUNDERERS = frozenset({b"type", b"rawequal", b"getmetatable", b"next",
                         b"tostring", b"tonumber", b"select", b"pcall",
                         b"unpack", b"rawget", b"pairs", b"ipairs", b"xpcall"})

# The six kinds of site, and the subset that refuses. They are equal today --
# all six refuse -- but they are two names because they answer two questions
# ("what can this analysis find" vs "what does a grant require"), and because
# a single tuple made `_DECIDING` unreferenced and therefore unfalsifiable:
# `tests/test_l2_keyseq.py::test_the_same_fixture_with_the_branch_taken_off_a_
# local_is_granted` goes red when `_TRUTHINESS` is removed from `_DECIDING`,
# and did not before this split.
_TRUTHINESS = "blind-truthiness"
_LOOP = "blind-loop"
_HARNESS = "blind-harness"
_KINDS = ("blind-compare", "blind-length", "blind-launder", _HARNESS, _LOOP,
          _TRUTHINESS)
_DECIDING = _KINDS


def static_taint(root) -> dict[str, int]:
    """`{site kind: count}` for the whole chunk: places where a stub-derived
    value reaches a decision the runtime cannot observe.

    ## The analysis

    A conservative may-analysis over registers, per proto, to a fixed point on
    the existing `cfg.blocks.build_cfg`. A register is *stub-derived* if it
    was defined by `GETGLOBAL` of a stub global, by indexing a stub-derived
    table OR indexing at a stub-derived key, by `GETUPVAL`, by a `CALL` whose
    callee is not provably a base/driver global, or by any arithmetic /
    concatenation / length / negation whose operand is stub-derived. Block
    entry takes the UNION of predecessors. Everything that loads a constant,
    a new table or a closure kills.

    Over-approximating on purpose, in four named ways: every `GETUPVAL` is
    stub, every unrecognised callee returns a stub, every global the chunk
    does not resolve for real is a stub at every read of it, and the union
    merge ignores which path was actually taken. All four push towards
    refusing, and all four are measured to cost no reach on this corpus.

    ## What is flagged

    * `blind-compare` -- `EQ`/`LT`/`LE` with a stub-derived operand. Flagged
      even when both operands are stub-derived: "both stub" does not mean
      "both proxies" (a stub `CALL` result is a plain `nil`/`0`/`"stub"`), so
      the runtime `__eq` route cannot be assumed to cover it.
    * `blind-length` -- `LEN` on a stub-derived register. Lua 5.1's `OP_LEN`
      never consults a metamethod for a table, so `#stub` is silently `0`.
    * `blind-launder` -- a `CALL` of one of `_LAUNDERERS` with a stub-derived
      argument in the call window. Only the `GETGLOBAL f; ...; CALL f` shape
      is recognised as naming `f`; an aliased launderer (`local ts = tostring`)
      is not a `blind-launder`, but its RESULT is stub-derived by the rule
      below, so a comparison on it still refuses as `blind-compare`.
    * `blind-truthiness` -- `TEST`/`TESTSET` on a stub-derived register.
    * `blind-loop` -- `FORPREP`/`FORLOOP`/`TFORLOOP` whose control triple
      `R(A)..R(A+2)` is stub-derived. A loop's trip count is a branch, and the
      body can then write a perfectly clean register.
    * `blind-harness` -- a stub-derived value in the argument window of a
      `_CLEAN_CALLEES` callee. The harness's own state (`waitf`'s frame
      counter) is a channel a register may-analysis is structurally unable to
      follow, so it is closed at the boundary instead; see the runbook's
      "Harness state is a channel, not a propagation gap".

    **All six refuse** (`_DECIDING is _KINDS`). This list said "four" and
    closed with "All four refuse" through M5, silently omitting the last two,
    which are not cosmetic: re-measured 2026-08-13, `blind-loop` is **50**
    sites on `snr_common` and **19** on `snr_graphic`.

    `blind-truthiness` was very nearly left out on the prediction that
    `if someGlobal then` is so common that refusing on it would take L2 reach
    to zero. **That prediction was wrong and the measurement is the reason it
    is in:** re-measured 2026-08-13 over the five authored files, the counts
    are `snr_common` **20**, `snr_graphic` 9, `snr_memory` 9, `snr_music` 2
    and `snr_lib` **0** (the 17 this line carried for `snr_common` predates
    the later rounds' widening of what counts as stub-derived) -- so including
    it costs nothing on this corpus (the only file that survives the other
    kinds survives this one too) and it makes the refusal condition the
    literal property, not an approximation of it.

    `blind-harness` is **0 on all five authored files**, so its evidence is
    entirely synthetic: a green corpus says nothing about whether it works.
    What does is the `wait(sys.delay)` fixture in `tests/test_l2_keyseq.py::
    test_harness_state_is_a_channel_the_register_analysis_cannot_see`.

    STATIC, so it does not know which paths ran: a site in a function the key
    sequence never enters still refuses the file. That is the conservative
    direction and it is the whole point of a backstop.
    """
    from pyluadec.cfg.blocks import build_cfg
    from pyluadec.lift import lift_proto
    from pyluadec.lift.opcodes import Op, decode

    stubs = _stub_globals(root)
    shadowed = _shadowed_names(root)
    clean_callees = (frozenset() if _substitutes_environment(root)
                     else _CLEAN_CALLEES - shadowed)
    counts = {k: 0 for k in _KINDS}

    def rk_stub(p, v: int, live: set[int]) -> bool:
        # RK operand: bit 9 set means "constant index", which is never stub.
        return not (v & 0x100) and v in live

    def walk(p):
        fn = lift_proto(p)
        cfg = build_cfg(fn)
        # U-4: a closure created here can write the parent's local through
        # `SETUPVAL`, and the parent's register keeps whatever this analysis
        # last decided about it. `lift_proto` already knows which registers are
        # captured; treating every one of them as stub-derived for the whole
        # proto is the cheap sound answer. Measured corpus reach: 102
        # `SETUPVAL`s in 6 of 229 files, 20 parent registers written this way,
        # 0 of them reaching a decision operand -- and `snr_lib.lua` has 0
        # captured registers, so this costs no reach either.
        captured = set(fn.captured_regs)
        entry: dict[int, set[int]] = {b: set() for b in cfg.blocks}
        exits: dict[int, set[int]] = {b: set() for b in cfg.blocks}
        sites: dict[int, str] = {}
        changed = True
        while changed:
            changed = False
            for start in sorted(cfg.blocks):
                inb: set[int] = set(captured)
                for pred in cfg.preds.get(start, ()):
                    inb |= exits[pred]
                entry[start] = inb
                live = set(inb)
                for li in cfg.blocks[start].instrs:
                    _step(p, li.ri, live, sites)
                    # Re-added after EVERY instruction, not just at the block
                    # boundaries: a captured register is written by a closure
                    # at a point this analysis cannot see, so no `LOADK` or
                    # `MOVE` in the parent may ever be taken as clearing it.
                    # Measured with boundary-only seeding, the U-4 fixture
                    # still granted -- `local v = 0` discarded it inside the
                    # same block that then compared it.
                    live |= captured
                if live != exits[start]:
                    exits[start] = live
                    changed = True
        for kind in sites.values():
            counts[kind] += 1
        for sp in p.subprotos:
            walk(sp)

    def _defined(p, ins) -> range:
        """Every register `ins` writes. Used to invalidate `index_globals`'
        holder, which used to pop only `A` -- U-8. `LOADNIL A B`,
        multi-result `CALL`, `VARARG A B`, `SELF` and the `for` opcodes all
        write registers other than `A`, so a stale base-global name could
        stay attached to a register that now holds something else."""
        op, a, b, c = ins.op, ins.a, ins.b, ins.c
        top = p.maxstacksize
        if op is Op.LOADNIL:
            return range(a, b + 1)
        if op is Op.SELF:
            return range(a, a + 2)
        if op in (Op.CALL, Op.TAILCALL):
            return range(a, (a + c - 1) if c > 0 else top + 1)
        if op is Op.VARARG:
            return range(a, (a + b - 1) if b > 0 else top + 1)
        if op is Op.FORLOOP:
            return range(a, a + 4)
        if op is Op.FORPREP:
            return range(a, a + 1)
        if op is Op.TFORLOOP:
            # `TFORLOOP A C` defines R(A+3)..R(A+2+C) and then copies R(A+3)
            # into R(A+2) when it is non-nil. Derived from C, not the
            # hard-coded `a..a+6` window this used to carry: with more than
            # four loop variables the tail was left CLEAN, which is a taint
            # LOSS. Measured before the fix: `for x1..x6 in sys.iter` with the
            # comparison on `x6` granted; with two variables it refused.
            return range(a + 2, a + 3 + max(c, 1))
        if op in (Op.SETGLOBAL, Op.SETUPVAL, Op.SETTABLE, Op.SETLIST,
                  Op.JMP, Op.EQ, Op.LT, Op.LE, Op.TEST, Op.RETURN, Op.CLOSE):
            return range(a, a)
        return range(a, a + 1)

    def _step(p, ins, live: set[int], sites: dict[int, str]) -> None:
        op, a, b, c = ins.op, ins.a, ins.b, ins.c
        if op in (Op.EQ, Op.LT, Op.LE):
            if rk_stub(p, b, live) or rk_stub(p, c, live):
                sites[ins.pc] = "blind-compare"
            return
        if op is Op.TEST:
            if a in live:
                sites[ins.pc] = _TRUTHINESS
            return
        if op is Op.TESTSET:
            if b in live:
                sites[ins.pc] = _TRUTHINESS
            live.add(a) if b in live else live.discard(a)
            return
        if op is Op.LEN:
            if b in live:
                sites[ins.pc] = "blind-length"
            live.add(a) if b in live else live.discard(a)
            return
        if op is Op.GETGLOBAL:
            live.add(a) if p.constants[ins.bx] in stubs else live.discard(a)
            return
        if op in (Op.SETGLOBAL, Op.SETTABLE, Op.SETUPVAL, Op.SETLIST):
            return
        if op is Op.MOVE:
            live.add(a) if b in live else live.discard(a)
            return
        if op is Op.GETUPVAL:
            # NOT decoration, and it went unpinned for two rounds because the
            # whole module stayed green when it was neutered. `local up = nil;
            # function seed() up = sys.a end` then comparing `up` inside a
            # sibling closure refuses only because of this line -- pinned by
            # `test_a_value_written_into_an_upvalue_is_stub_derived`.
            live.add(a)
            return
        if op in (Op.GETTABLE, Op.SELF):
            # The KEY as well as the table (New-2). `local t = {} t.real = 1
            # if t[sys.k] == nil` reads a script table at a stub-derived key
            # and gets nil every time; the table is clean and the result is
            # not.
            hot = b in live or rk_stub(p, c, live)
            if op is Op.SELF:
                # DEFENSIVE: `SELF` also writes A+1 (the receiver), and luac
                # only ever emits `SELF` immediately before a `CALL` that
                # consumes both, so A+1 is never read as a value on its own.
                # Tried: neutering this line leaves the whole module green.
                # It stays because the transfer function is written against
                # the opcode, not against luac's habits.
                live.add(a + 1) if hot else live.discard(a + 1)
            live.add(a) if hot else live.discard(a)
            return
        if op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
            live.add(a) if (rk_stub(p, b, live) or rk_stub(p, c, live)) \
                else live.discard(a)
            return
        if op in (Op.UNM, Op.NOT):
            live.add(a) if b in live else live.discard(a)
            return
        if op is Op.CONCAT:
            live.add(a) if any(r in live for r in range(b, c + 1)) \
                else live.discard(a)
            return
        if op in (Op.FORPREP, Op.TFORLOOP):
            # U-5: a loop is a branch, and its TRIP COUNT can be stub-decided
            # while the body writes a perfectly clean register. `local n = 0
            # for k in sys.iter do n = 1 end if n == 1 then` granted before
            # this arm existed -- the proxy's `__call` returns nil, the body
            # never runs, and the comparison reads a clean 0.
            #
            # The control triple is R(A)..R(A+2) for both forms (init/limit/
            # step, or generator/state/control).
            if any(r in live for r in range(a, a + 3)):
                sites[ins.pc] = _LOOP
                for r in _defined(p, ins):
                    live.add(r)
            else:
                for r in _defined(p, ins):
                    live.discard(r)
            return
        if op is Op.FORLOOP:
            if any(r in live for r in range(a, a + 3)):
                sites[ins.pc] = _LOOP
                for r in _defined(p, ins):
                    live.add(r)
            else:
                for r in _defined(p, ins):
                    live.discard(r)
            return
        if op in (Op.CALL, Op.TAILCALL):
            # Argument window: a+1 .. a+b-1 (b == 0 means "to the top", which
            # this analysis cannot bound, so it reads the whole frame).
            top = p.maxstacksize
            hi = (a + b - 1) if b > 0 else top
            args = [r for r in range(a + 1, hi + 1) if r in live]
            fname = _called_global(p, ins)
            cname = fname.decode("latin-1") if fname is not None else None
            if fname in _LAUNDERERS and args:
                sites[ins.pc] = "blind-launder"
            elif cname in clean_callees and args:
                # A stub-derived value reached a callee the HARNESS depends
                # on. This is a channel a register may-analysis is otherwise
                # blind to, and it is not hypothetical: `waitf(n)` does
                # `tonumber(n)`, which is `nil` for a proxy, so `wait(sys.d)`
                # advances ONE frame instead of N -- and the frame counter
                # decides every later `pressButton`. Measured: the two sides
                # traced identically, zero runtime marks (the probe's `waitf`
                # calls its own local `tonumber`, so no override sees it), and
                # `wait(sys.delay)` vs `wait(3)` took opposite branches under
                # the same key spec. The return value is honestly clean; the
                # harness state it left behind is not.
                #
                # Recording a site rather than only refusing the result is
                # measured free: 0 `blind-harness` sites across the corpus.
                sites[ins.pc] = _HARNESS
            # A call's RESULT is clean only when the callee is provably one of
            # the few functions that cannot hand back a value derived from its
            # arguments or from the environment (`_CLEAN_CALLEES`, minus
            # anything this chunk shadows) AND no argument is stub-derived.
            # BOTH halves are load-bearing, and the round-3 comment here was
            # wrong about the second. It claimed every allowlisted name "either
            # is in `_LAUNDERERS` or genuinely ignores its arguments' values".
            # `pressButton` is in neither category: `press(name)` is
            # `if set and type(name) == "string" then down = set[name] == true`,
            # so the ARGUMENT'S VALUE selects the result. Measured with `not
            # args` neutered to `True`, `if pressButton(sys.k) == true then`
            # flips from `refuse{blind-compare: 1}` to a GRANT while the module
            # stayed 132/132 green -- the guard did real work and the suite had
            # the hole. Pinned on site counts by
            # `test_a_stub_reaching_an_allowlisted_callee_is_both_a_site_and_a_
            # taint`, since the `blind-harness` arm above now refuses the same
            # file either way.
            #
            # Emptying `_CLEAN_CALLEES` changes the taint of 9 corpus files
            # including `snr_lib.lua`, so the allowlist is load-bearing for the
            # one shipped grant, not decoration.
            fexempt = (fname is not None
                       and fname.decode("latin-1") in clean_callees
                       and not args)
            stub_call = (a in live) or not fexempt
            for r in _defined(p, ins):
                live.add(r) if stub_call else live.discard(r)
            if op is Op.CALL and c == 1:
                live.discard(a)      # no results kept
            return
        if op in (Op.LOADK, Op.LOADBOOL, Op.LOADNIL, Op.NEWTABLE, Op.CLOSURE,
                  Op.VARARG):
            for r in _defined(p, ins):
                live.discard(r)
            return
        # JMP, RETURN, CLOSE: no register definition this cares about.

    # `_called_global` needs the two instructions before the CALL, so it is a
    # separate scan over the proto's own code rather than part of the walk.
    prev_global: dict[int, bytes] = {}

    def _called_global(p, ins) -> bytes | None:
        return prev_global.get((id(p), ins.a, ins.pc))

    def index_globals(p):
        # `GETGLOBAL A K` followed (not necessarily immediately) by a CALL of
        # register A, with no intervening redefinition of ANY register the
        # holder covers. U-8: this used to pop only `x.a`, so a multi-result
        # `CALL`, a `LOADNIL A B`, a `VARARG A B`, a `SELF` or a `for` opcode
        # could leave a stale base-global name attached to a register that now
        # holds something else -- and `_called_global` would then exempt a
        # call of it. Not reachable from luac output (luac fills a call slot
        # with an instruction whose `A` is that slot), so it was a weakness of
        # the mechanism rather than a demonstrated grant; fixed rather than
        # documented, since `_defined` had to exist for the loop windows
        # anyway.
        holder: dict[int, bytes] = {}
        for i, w in enumerate(p.code):
            x = decode(w, i + 1)
            if x.op is Op.GETGLOBAL:
                holder[x.a] = p.constants[x.bx]
                continue
            if x.op in (Op.CALL, Op.TAILCALL) and x.a in holder:
                prev_global[(id(p), x.a, x.pc)] = holder[x.a]
            for r in _defined(p, x):
                holder.pop(r, None)
        for sp in p.subprotos:
            index_globals(sp)

    index_globals(root)
    walk(root)
    return counts


def static_refusal(root) -> dict[str, int]:
    """The non-zero site kinds a grant is refused on. Empty = nothing found."""
    return {k: v for k, v in static_taint(root).items() if v and k in _DECIDING}


# --------------------------------------------------------------------------
# The grant
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class L2Result:
    granted: bool
    reason: str | None          # one of REFUSAL_KINDS when not granted
    cov: float | None
    detail: str = ""            # human-facing only; never enters the ledger

    def as_ledger_field(self) -> dict | None:
        """What `scripts/run_corpus.py` writes.

        No corpus content, ever: `cov` is a number and `refused` is a word
        from `REFUSAL_KINDS`. `detail` stays out, and it has to: for the
        `probe-error` reason it is `str(ProbeError)[:400]`, which interpolates
        the probe's own stdout -- trace lines that can carry Japanese string
        constants.

        **Decision, taken explicitly rather than left implicit (round 2,
        New-7): that console exposure is accepted.** The red line CLAUDE.md
        draws is about ingest/lift/verify/comparison and about the diagnostic
        text that ends up in a committed artifact (`refusal_reason`,
        confessions); `detail` is neither -- it is printed by a CLI a human
        ran, is never serialised, and `scripts/probe_behaviour.py::probe_raw`
        has embedded `stdout[:400]` the same way since M4. Suppressing it
        would reproduce the L1.5 failure of a probe that cannot say why it
        failed. Nothing decodes: the bytes are rendered by `repr` on a
        `bytes.decode(errors="replace")` at the point of display only.
        """
        if self.granted:
            return {"cov": self.cov}
        return {"refused": self.reason}


def chunk_levels(original: bytes, root=None) -> dict[str, str]:
    """`{proto path: certification level}` for a chunk, from the pipeline.

    Split out so `evaluate` can be handed the result a caller already has
    (`scripts/run_corpus.py` computes it for every file anyway) instead of
    paying for a second certification, while a caller that has nothing still
    cannot skip the check.
    """
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    return decompile_chunk(load_bytes(original) if root is None
                           else root).levels


def evaluate(original: bytes, artifact_src: bytes,
             specs: Sequence[str], *, original_root=None,
             levels: dict[str, str] | None = None) -> L2Result:
    """The whole grant rule, over one file and ALL of its authored sequences.

    Every sequence must pass on its own; the coverage badge is taken over the
    union of the sequences that RAN TO COMPLETION. A file gets more than one
    sequence when one entry point is not the whole story -- `snr_common.lua`
    carries the two historical checkpoints (`systemOption.OptionMain`,
    `systemConfig.ConfigMain`) plus a whole-chunk run, and a single spec could
    only drive one of them.

    ## Truncation is part of the verdict, and it was not

    Through M5 this function never called `header`, so a sequence stopped at
    `MAX_EVENTS` compared equal *over its prefix* and that was recorded
    nowhere -- not in the verdict, not in `detail`, not in the ledger.
    Demonstrated by `tests/test_l2_keyseq.py::test_a_pair_that_only_agrees_up_
    to_the_event_cap_cannot_be_the_whole_grant`:
    `for i=1,5000 do engine.Go(i) end engine.OriginalTail()` against the same
    loop ending in `engine.COMPLETELY_DIFFERENT_TAIL()` both stop at
    `CAP|3001`, are byte-equal, carry no taint, and returned
    `granted=True, cov=1.0`.

    A capped sequence now proves only what it observed. It is still REQUIRED
    to agree -- nothing was relaxed -- and it can no longer be the ONLY
    evidence a grant rests on: at least one sequence must reach `OK`, and the
    coverage badge is computed over those sequences alone, so no proto is
    credited to the badge on the strength of a run that was cut off.

    ## What the guard does NOT buy, measured

    **A capped run can still be the only evidence for a BRANCH that no
    completing sequence enters.** Constructed by review and reproduced
    2026-08-13 -- `tests/test_l2_keyseq.py::test_a_branch_only_a_capped_
    sequence_enters_is_granted_on_a_truncated_prefix` is that fixture,
    committed as a KNOWN-OPEN ROUTE that grants and should not, in the same
    style as `test_what_the_two_taint_instruments_still_cannot_see`:

        if pressButton("CIRCLE")==true then
          for i=1,5000 do engine.Go(i) end engine.OriginalTail()
        else engine.Short() end

    with the artifact differing only in the tail call. Specs `["tail=",
    "k=1,CIRCLE;tail="]` give `OK|5` (equal) and `CAP|3001` (equal prefix),
    taint is empty, both protos are `L3` -- `granted=True, cov=1.0`. The
    divergence lives in the branch only the capped sequence enters, so the
    completed run says nothing about it.

    `cov` does not notice, and cannot: **both** specs enter 2 of 2 protos, so
    proto granularity is blind to a branch. Closing this needs branch-level
    coverage or a post-cap divergence check, neither of which is cheap; routed
    to M6 (`docs/runbooks/m3-backlog.md`, M6 agenda 2).

    **The one live grant is not resting on this**, and that is a measurement
    rather than an argument: `snr_lib.lua`'s capped `tail=CIRCLE` was re-run
    at 10x the budget with every decimal token normalised out, and it produces
    **15 distinct event shapes at 3000 events and the same 15 at 30000, none
    new** -- the post-cap tail is pure repetition of the menu's redraw/poll
    cycle. That is a property of THIS sequence that was measured once; **the
    gate does not check it**, and a future sequence would need its own
    measurement.

    **Not "every sequence must reach `OK`", and that is a measurement, not a
    preference.** These menu loops are re-entrant, and the degenerate
    sequences (`snr_lib`'s `tail=CIRCLE`, which holds select from frame 1)
    never halt at all: measured 2026-08-13 with `MAX_EVENTS` raised 1000x for
    the experiment, `snr_lib.lua` under `tail=CIRCLE` reports `CAP|3000001`.
    Every one of the five authored files carries at least one such sequence,
    so requiring all of them to complete would put L2 reach on this corpus at
    0 permanently -- not because any decompilation is in doubt, but because an
    authored input does not terminate.

    What a grant therefore claims: every authored run agreed over everything
    observed, and at least one of them was observed to completion. What it
    does not claim: anything about a capped run past its cap. `detail` prints
    the completed/total count, so a CLI reader can see which it is.

    ## Why a grant requires the whole chunk to be `L3`

    `static_taint` analyses the ORIGINAL only (`root = original_root or
    load_bytes(original)`), so the shipped artifact's own blind sites are
    invisible to it. While the artifact is field-identical to the original
    that is harmless -- the two have the same sites by construction -- and it
    is exactly what `L3` establishes.

    The two genuinely diverge otherwise. Measured 2026-08-13 on
    `snr_music.lua`, whose artifact is not fully `L3`: the original taints
    `{compare 36, length 1, launder 1, loop 3, truthiness 2}` while its
    shipped text taints `{compare 3, loop 16}` -- the fallback state machine's
    `__pld_R` box model *hides* 33 compare sites and *invents* 13 loop sites.
    An analysis of one is not an analysis of the other.

    So the precondition is made structural rather than left accidental: every
    proto in the chunk must be `L3`. Measured cost on this corpus: none. The
    sole granted file (`snr_lib.lua`) is `L3` on all 3 protos, and the four
    refused files are refused by `taint-static` first anyway -- they are also
    all non-`L3` (17 of 147, 4 of 6, 4 of 6, 2 of 5), so the ORDER of the last
    two checks is what decides which reason they report. It is deliberate:
    an actual taint finding says more than "not field-identical", and keeping
    it also leaves `corpus/ledger.jsonl` byte-unchanged.

    **L2 therefore certifies only field-identical artifacts today.** Extending
    it to hybrids or to fallback text requires analysing the ARTIFACT too, not
    just relaxing this check; that is M6 work.

    Pure with respect to the ledger: it takes bytes and returns a verdict.
    """
    if not specs:
        # Pinned by `test_a_file_with_no_sequence_is_refused_not_granted`. With
        # this gone, `evaluate(bc, src, [])` returned `granted=True, cov=0.0`:
        # the loop body never ran, so none of the four conditions was ever
        # evaluated, and the whole grant rule was skipped rather than failed.
        return L2Result(False, "no-key-poll", None, "no sequence authored")
    try:
        complete: list[str] = []
        for spec in specs:
            o = probe_raw(original, is_source=False, spec=spec)
            d = probe_raw(artifact_src, is_source=True, spec=spec)
            if o != d:
                n, _a, _b = first_difference(o, d)
                return L2Result(False, "divergent", None,
                                f"{spec}: first differing line {n}")
            if poll_count(o) == 0:
                return L2Result(False, "no-key-poll", None,
                                f"{spec}: never polled")
            marks = taint_marks(o) + taint_marks(d)
            if marks:
                kinds = sorted({m.split(b"|")[1].decode("ascii") for m in marks})
                return L2Result(False, "taint", None,
                                f"{spec}: {len(marks)} mark(s): {kinds}")
            # `o == d` was established above, so one header speaks for both.
            if header(o)[0] == "OK":
                complete.append(spec)
        if not complete:
            # Every observation was cut off, so "byte-equal" means "equal over
            # a prefix" and nothing more. See the docstring.
            return L2Result(False, "truncated", None,
                            f"all {len(specs)} sequence(s) stopped at the "
                            f"event cap")
        # The STATIC backstop, over the ORIGINAL bytecode. Last of the
        # refusals because it is the coarsest -- it does not know which paths
        # ran -- but it is the only one that sees the idiom the runtime marks
        # are structurally blind to. See `static_taint`.
        root = original_root
        if root is None:
            from pyluadec.ingest import load_bytes
            root = load_bytes(original)
        blind = static_refusal(root)
        if blind:
            kinds = ", ".join(f"{k}={v}" for k, v in sorted(blind.items()))
            return L2Result(False, "taint-static", None, kinds)
        # The backstop above read the ORIGINAL; this is what makes that the
        # same program as the artifact. See the docstring.
        #
        # `levels` is TRUSTED, not verified: it exists so a caller that has
        # already certified this chunk does not pay for a second pass, and the
        # only in-tree caller (`scripts/run_corpus.py`) passes the `res.levels`
        # of the very `decompile_chunk` whose `res.source` is `artifact_src`.
        # A caller could hand over a map that says whatever it likes -- and one
        # does, in `tests/test_l2_keyseq.py::test_a_chunk_that_is_not_fully_l3_
        # cannot_be_granted`, deliberately, to show the check is what decides.
        # That is a test affordance; if a second production caller ever appears
        # this should recompute and compare rather than trust.
        lv = chunk_levels(original, root) if levels is None else levels
        not_l3 = sum(1 for v in lv.values() if v != "L3")
        if not_l3:
            return L2Result(False, "not-l3", None,
                            f"{not_l3} of {len(lv)} proto(s) are not L3")
        c = coverage(artifact_src, complete)
    except (ProbeError, subprocess.SubprocessError, CoverageError) as e:
        return L2Result(False, "probe-error", None, str(e)[:400])
    lo, hi = c.block_interval
    return L2Result(True, None, c.fraction,
                    f"{c.protos_entered}/{c.protos} protos; blocks in "
                    f"[{lo:.2f}, {hi:.2f}] of {c.blocks} "
                    f"({c.collisions} share an entry line); "
                    f"{len(complete)}/{len(specs)} sequence(s) completed")


def evaluate_corpus(corpus: Path, artifact_of, *, jobs: int = 5
                    ) -> dict[str, L2Result]:
    """`{file name: L2Result}` for every file with an authored sequence.

    `artifact_of(Path) -> bytes` supplies the shipped source, so the caller
    decides whether that comes from a fresh `decompile_file` or a cache.
    """
    names = sorted(KEY_SEQUENCES)

    def one(name: str):
        f = corpus / name
        return name, evaluate(f.read_bytes(), artifact_of(f), KEY_SEQUENCES[name])

    if not names:
        return {}
    with ThreadPoolExecutor(max_workers=min(jobs, len(names))) as ex:
        return dict(ex.map(one, names))


def main(argv: list[str] | None = None) -> int:
    """A CLEAN run prints the reach and exits 0, including the four files that
    are expected to refuse. The L1.5 probe shipped once with a CLI that did not
    know about its own pins and printed a red 225/229 while the suite was
    green; the adjudication lives in `EXPECTED_VERDICT` so the CLI and the gate
    cannot disagree on what "pass" means."""
    from pyluadec.pipeline import decompile_file
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    scratch = ROOT / "build" / "l2-mismatch"
    results = evaluate_corpus(corpus, lambda f: decompile_file(f).source)
    granted = [n for n, r in results.items() if r.granted]
    unexpected = []
    for name in sorted(results):
        r = results[name]
        got = "granted" if r.granted else r.reason
        badge = f"L2@{r.cov:.0%}" if r.granted else f"refused ({r.reason})"
        flag = "" if got == EXPECTED_VERDICT.get(name) else "  <-- UNEXPECTED"
        if flag:
            unexpected.append(name)
            if r.reason == "divergent":
                o, d = _reprobe(corpus, name, r.detail.split(":", 1)[0])
                dump_mismatch(name, o, d, scratch)
        print(f"  {name:<24} {badge:<22} {r.detail}{flag}")
    n_specs = sum(len(v) for v in KEY_SEQUENCES.values())
    print(f"L2: {len(granted)}/{len(results)} authored file(s) granted, "
          f"{len(results) - len(granted) - len(unexpected)} refused as "
          f"expected "
          f"({n_specs} sequence(s) over {len(KEY_SEQUENCES)} file(s), "
          f"{len(list(corpus.glob('*.lua')))} files in the corpus)")
    if unexpected:
        print(f"UNEXPECTED verdict(s): {unexpected}; any diverging traces are "
              f"in {scratch}")
    return 1 if unexpected else 0


def _reprobe(corpus: Path, name: str, spec: str) -> tuple[bytes, bytes]:
    from pyluadec.pipeline import decompile_file
    f = corpus / name
    return (probe_raw(f.read_bytes(), is_source=False, spec=spec),
            probe_raw(decompile_file(f).source, is_source=True, spec=spec))


if __name__ == "__main__":
    sys.exit(main())

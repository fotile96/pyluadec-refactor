"""L2 gate: key-sequence-driven differential execution, with taint and a
branch-coverage badge.

The Lua side is `scripts/probe_keyseq.lua`; that file is the source of truth
for the spec grammar, the trace format, the event budget, the stub-return
policy and what the taint marks mean. This module runs it, refuses to turn a
probe-side failure into a comparable value, and decides the grant.

## The grant rule

A file is granted `L2` when, under one authored key sequence:

1. both sides produce a recognisable trace (no probe-side failure),
2. the two traces are **byte-equal**,
3. the run actually consumed the sequence -- at least one `K|` poll event,
4. neither side recorded any **taint**.

5. **no stub-derived value can decide a branch unobserved** -- the static
   backstop over the original bytecode (`static_taint`) finds no
   `blind-compare`, `blind-length`, `blind-launder` or `blind-truthiness`
   site.

Anything else refuses, with a reason from `REFUSAL_KINDS`. The badge that
rides along is `cov`: the fraction of the *shipped artifact's protos* the run
entered (see `coverage` for why it is protos and not basic blocks).

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
* **`VARARG`.** `local a = ...` compared against a literal is not flagged.

A granted `L2` therefore says "these two programs behaved identically under
this stub policy and this input, and no *directly* stub-derived value decided
a branch we could not observe" -- not "this decompilation is correct under the
real engine".
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
                 "probe-error")


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
# --------------------------------------------------------------------------
KEY_SEQUENCES: dict[str, tuple[str, ...]] = {
    # The debug menu: UP is clamped at the top, four DOWNs walk to the bottom
    # entry and are clamped there, CIRCLE selects. The third sequence is the
    # degenerate one -- CIRCLE held from the first frame -- kept because it
    # reaches the "already pressed" gate (`l1_2 == 0`) that the others skip.
    "snr_lib.lua": (
        "k=1,UP;k=2,DOWN;k=3,DOWN;k=4,DOWN;k=5,DOWN;k=6,CIRCLE;tail=CIRCLE",
        "k=1,DOWN;k=2,DOWN;k=3,CIRCLE;tail=CIRCLE",
        "tail=CIRCLE",
    ),
    # The gallery browsers. Both poll eight buttons (UP/DOWN/LEFT/RIGHT/L/R/
    # CIRCLE/CROSS); CROSS is what leaves, CIRCLE what descends.
    "snr_graphic.lua": (
        "k=1,RIGHT;k=2,DOWN;k=3,L;k=4,R;k=5,CIRCLE;k=7,CROSS;tail=CROSS",
        "k=1,DOWN;k=2,RIGHT;k=3,LEFT;k=4,UP;k=5,L;k=6,R;k=7,CIRCLE;"
        "k=9,CROSS;k=11,CROSS;tail=CROSS",
        "k=1,DOWN;k=2,DOWN;k=3,CIRCLE;tail=CIRCLE",
    ),
    "snr_memory.lua": (
        "k=1,DOWN;k=2,RIGHT;k=3,LEFT;k=4,UP;k=5,L;k=6,R;k=7,CIRCLE;"
        "k=9,CROSS;tail=CROSS",
        "k=1,DOWN;k=2,DOWN;k=3,CIRCLE;tail=CIRCLE",
    ),
    "snr_music.lua": (
        "k=1,DOWN;k=2,RIGHT;k=3,LEFT;k=4,UP;k=5,CIRCLE;k=7,CROSS;tail=CROSS",
        "k=1,DOWN;k=2,DOWN;k=3,CIRCLE;tail=CIRCLE",
    ),
    # The two historical checkpoints from the predecessor's playbook
    # (`DEBUG_KEY_SEQUENCE_HARNESS.md`): `OptionMain`'s RIGHT/LEFT must keep
    # two mutually exclusive clamps, and `ConfigMain`'s CIRCLE branch must
    # keep its gate/wait. Both are METHODS on the instances the chunk builds
    # (`systemOption = SystemOption.new()`), not on the class tables, which is
    # why the entry names are the lower-case globals. What those sequences
    # ASSERT is M5 task 10's job; this file only has to make them runnable.
    #
    # The third sequence drives the whole chunk instead, and is what makes the
    # `pressButton` loop inside `autoSystemSave` reachable.
    "snr_common.lua": (
        "entry=systemOption.OptionMain;k=1,RIGHT;k=3,RIGHT;k=5,LEFT;"
        "k=7,DOWN;k=9,CIRCLE;tail=CROSS",
        "entry=systemConfig.ConfigMain;k=1,DOWN;k=3,DOWN;k=5,CIRCLE;tail=CROSS",
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


def _stub_globals(root) -> set[bytes]:
    """Every global name this chunk READS that the probe environment does not
    resolve for real. Anything else is a stub proxy at that read.

    ## There is no "the chunk defines it, so it is not a stub" exemption

    There was, for one round: `read - written`, computed over the whole chunk
    with no ordering. It was unsound in exactly the way the runtime marks were
    (round-1 C1), and by the same author. `env.__index` consults `envfields`,
    which is EMPTY until the chunk actually executes the write, so a global
    read before its write -- or whose write is inside a function nobody calls
    -- is a proxy at that read. Three fixtures, each with byte-equal traces,
    zero runtime marks, the stub-forced branch taken, and a GRANT:

        function setup() mode = "a" end   -- setup is never called
        if mode == "a" then ... end; mode = "a"    -- write after the read
        stash = sys.a; if stash == "x" then ...    -- laundering THROUGH it

    A sound exemption would have to show the write MUST precede every read
    along all paths AND that the written value is not itself stub-derived.
    That is a real dataflow problem, and it is not worth building here,
    because the exemption buys **nothing**: measured 2026-08-12, removing it
    leaves the CLI at 1/5 granted with `snr_lib` still granted. `snr_lib` has
    **0** globals that are both read and written; `snr_common` has 72, and it
    refuses for other reasons anyway.
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
    return {n for n in read
            if n.decode("latin-1") not in _BASE_GLOBALS
            and n.decode("latin-1") not in _DRIVER_GLOBALS}


# Library functions that turn a stub proxy into a plain value a branch can
# then read without any metamethod firing. `type`, `rawequal` and
# `getmetatable` are also marked at runtime; the rest have no runtime seam at
# all.
_LAUNDERERS = frozenset({b"type", b"rawequal", b"getmetatable", b"next",
                         b"tostring", b"tonumber", b"select", b"pcall",
                         b"unpack", b"rawget", b"pairs", b"ipairs", b"xpcall"})

# The four kinds of site, and the subset that refuses. They are equal today --
# all four refuse -- but they are two names because they answer two questions
# ("what can this analysis find" vs "what does a grant require"), and because
# a single tuple made `_DECIDING` unreferenced and therefore unfalsifiable:
# `tests/test_l2_keyseq.py::test_the_same_fixture_with_the_branch_taken_off_a_
# local_is_granted` goes red when `_TRUTHINESS` is removed from `_DECIDING`,
# and did not before this split.
_TRUTHINESS = "blind-truthiness"
_KINDS = ("blind-compare", "blind-length", "blind-launder", _TRUTHINESS)
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

    All four refuse. `blind-truthiness` was very nearly left out on the
    prediction that `if someGlobal then` is so common that refusing on it
    would take L2 reach to zero. **That prediction was wrong and the
    measurement is the reason it is in:** over the five authored files the
    counts are `snr_common` 17, `snr_graphic` 9, `snr_memory` 9, `snr_music`
    2 and `snr_lib` **0** -- so including it costs nothing on this corpus (the
    only file that survives the other three kinds survives this one too) and
    it makes the refusal condition the literal property, not an approximation
    of it.

    STATIC, so it does not know which paths ran: a site in a function the key
    sequence never enters still refuses the file. That is the conservative
    direction and it is the whole point of a backstop.
    """
    from pyluadec.cfg.blocks import build_cfg
    from pyluadec.lift import lift_proto
    from pyluadec.lift.opcodes import Op, decode

    stubs = _stub_globals(root)
    counts = {k: 0 for k in _KINDS}

    def rk_stub(p, v: int, live: set[int]) -> bool:
        # RK operand: bit 9 set means "constant index", which is never stub.
        return not (v & 0x100) and v in live

    def walk(p):
        fn = lift_proto(p)
        cfg = build_cfg(fn)
        entry: dict[int, set[int]] = {b: set() for b in cfg.blocks}
        exits: dict[int, set[int]] = {b: set() for b in cfg.blocks}
        sites: dict[int, str] = {}
        changed = True
        while changed:
            changed = False
            for start in sorted(cfg.blocks):
                inb: set[int] = set()
                for pred in cfg.preds.get(start, ()):
                    inb |= exits[pred]
                entry[start] = inb
                live = set(inb)
                for li in cfg.blocks[start].instrs:
                    _step(p, li.ri, live, sites)
                if live != exits[start]:
                    exits[start] = live
                    changed = True
        for kind in sites.values():
            counts[kind] += 1
        for sp in p.subprotos:
            walk(sp)

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
            live.discard(a) if b not in live else live.add(a)
            return
        if op is Op.LEN:
            if b in live:
                sites[ins.pc] = "blind-length"
            live.add(a) if b in live else live.discard(a)
            return
        if op is Op.GETGLOBAL:
            live.add(a) if p.constants[ins.bx] in stubs else live.discard(a)
            return
        if op is Op.SETGLOBAL or op is Op.SETTABLE or op is Op.SETUPVAL:
            return
        if op is Op.MOVE:
            live.add(a) if b in live else live.discard(a)
            return
        if op is Op.GETUPVAL:
            live.add(a)
            return
        if op in (Op.GETTABLE, Op.SELF):
            # The KEY as well as the table (New-2). `local t = {} t.real = 1
            # if t[sys.k] == nil` reads a script table at a stub-derived key
            # and gets nil every time; the table is clean and the result is
            # not. Measured before this line existed: granted, stub branch
            # taken, zero marks.
            hot = b in live or rk_stub(p, c, live)
            if op is Op.SELF:
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
        if op in (Op.CALL, Op.TAILCALL):
            # Argument window: a+1 .. a+b-1 (b == 0 means "to the top", which
            # this analysis cannot bound, so it reads the whole frame).
            top = p.maxstacksize
            hi = (a + b - 1) if b > 0 else top
            args = [r for r in range(a + 1, hi + 1) if r in live]
            fname = _called_global(p, ins)
            if fname in _LAUNDERERS and args:
                sites[ins.pc] = "blind-launder"
            # A call's RESULT is stub-derived unless the callee is provably
            # one of the names the probe environment resolves for real
            # (New-3). The argument direction was the only one documented;
            # the RETURN direction is the shape this corpus actually uses --
            # an accessor handing back an engine value. Measured before this
            # line: `function getMode() return sys.mode end` compared against
            # a literal granted, and so did a closure built inside the driven
            # function. Conservative: an unrecognised callee (a field call, a
            # local holding a closure, anything reached through a MOVE) is
            # treated as returning a stub.
            fexempt = fname is not None and (
                fname.decode("latin-1") in _BASE_GLOBALS
                or fname.decode("latin-1") in _DRIVER_GLOBALS)
            stub_call = (a in live) or not fexempt
            nres = (c - 1) if c > 0 else (top - a)
            for r in range(a, a + max(nres, 1)):
                live.add(r) if stub_call else live.discard(r)
            return
        if op in (Op.LOADK, Op.LOADBOOL, Op.LOADNIL, Op.NEWTABLE, Op.CLOSURE,
                  Op.VARARG):
            hi = a if op is not Op.LOADNIL else b
            for r in range(a, hi + 1):
                live.discard(r)
            return
        if op in (Op.FORLOOP, Op.FORPREP, Op.TFORLOOP):
            # The control registers become whatever the iterator yields; if
            # any of the loop's own registers is stub-derived, treat the
            # induction variables as stub too.
            hot = any(r in live for r in range(a, a + 4))
            for r in range(a, min(a + 6, p.maxstacksize) + 1):
                live.add(r) if hot else live.discard(r)
            return
        # JMP, RETURN, CLOSE, SETLIST: no register definition this cares about.

    # `_called_global` needs the two instructions before the CALL, so it is a
    # separate scan over the proto's own code rather than part of the walk.
    prev_global: dict[int, bytes] = {}

    def _called_global(p, ins) -> bytes | None:
        return prev_global.get((id(p), ins.a, ins.pc))

    def index_globals(p):
        # `GETGLOBAL A K` followed (not necessarily immediately) by a CALL of
        # register A, with no intervening redefinition of A. Only the simple
        # form is recognised; anything else is not flagged as a launder, which
        # is a KNOWN gap and is stated in the runbook.
        holder: dict[int, bytes] = {}
        for i, w in enumerate(p.code):
            x = decode(w, i + 1)
            if x.op is Op.GETGLOBAL:
                holder[x.a] = p.constants[x.bx]
            elif x.op in (Op.CALL, Op.TAILCALL):
                if x.a in holder:
                    prev_global[(id(p), x.a, x.pc)] = holder[x.a]
                holder.pop(x.a, None)
            elif x.op is not Op.JMP:
                holder.pop(x.a, None)
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


def evaluate(original: bytes, artifact_src: bytes,
             specs: Sequence[str], *, original_root=None) -> L2Result:
    """The whole grant rule, over one file and ALL of its authored sequences.

    Every sequence must pass on its own; the coverage badge is taken over
    their union. A file gets more than one sequence when one entry point is
    not the whole story -- `snr_common.lua` carries the two historical
    checkpoints (`systemOption.OptionMain`, `systemConfig.ConfigMain`) plus a
    whole-chunk run, and a single spec could only drive one of them.

    Pure with respect to the ledger: it takes bytes and returns a verdict.
    """
    if not specs:
        # Pinned by `test_a_file_with_no_sequence_is_refused_not_granted`. With
        # this gone, `evaluate(bc, src, [])` returned `granted=True, cov=0.0`:
        # the loop body never ran, so none of the four conditions was ever
        # evaluated, and the whole grant rule was skipped rather than failed.
        return L2Result(False, "no-key-poll", None, "no sequence authored")
    try:
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
        c = coverage(artifact_src, specs)
    except (ProbeError, subprocess.SubprocessError, CoverageError) as e:
        return L2Result(False, "probe-error", None, str(e)[:400])
    lo, hi = c.block_interval
    return L2Result(True, None, c.fraction,
                    f"{c.protos_entered}/{c.protos} protos; blocks in "
                    f"[{lo:.2f}, {hi:.2f}] of {c.blocks} "
                    f"({c.collisions} share an entry line)")


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

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

Anything else refuses, with a reason from `REFUSAL_KINDS`. The badge that
rides along is `cov`: the fraction of the *shipped artifact's* basic blocks
whose entry line was executed during the run (see `coverage`).

## What the taint analysis refuses, and what it provably cannot catch

Refused (`scripts/probe_keyseq.lua`):

* `cmp:lt` / `cmp:le` / `cmp:eq` -- a stub proxy reached a comparison
  metamethod. This half is not an approximation: Lua 5.1's `OP_LT`, `OP_LE`
  and `OP_EQ` produce no value, they select the following `JMP`, so the
  metamethod firing *is* a stub value deciding a branch.
* `intro:type` / `intro:rawequal` / `intro:getmetatable` -- a stub proxy was
  introspected. Nothing here proves the result reached a branch; it is assumed
  to have. Conservative over-refusal, which is the honest direction.

**Provably not caught**, because Lua 5.1 offers no seam to observe it:

* A raw proxy used directly as a truth value (`if sys.flag then`). `OP_TEST`
  consults no metamethod on a table, so both sides silently take the truthy
  branch and nothing is recorded.
* A stub *return* value used as a condition (`if engine.IsDone() then`). What
  `stub_result` hands back is a plain `nil`/`false`/`0`/`"stub"`; a Lua value
  carries no provenance, so once returned it is indistinguishable from one the
  script computed.
* An arithmetic result (`if sys.n + 1 > 0 then`). The proxy's `__add` returns
  the number `0`; the comparison is then number-vs-number and fires no
  metamethod.

That list is why a granted `L2` says "these two programs behaved identically
under this stub policy and this input", not "this decompilation is correct
under the real engine".
"""
from __future__ import annotations

import hashlib
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

REFUSAL_KINDS = ("divergent", "taint", "no-key-poll", "probe-error")


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
# stops being granted, or a refusal that quietly converges, both fail.
EXPECTED_VERDICT: dict[str, str] = {name: "granted" for name in KEY_SEQUENCES}


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


def digest(trace: bytes) -> str:
    """The comparison unit, for reporting. The traces themselves are large;
    only materialise one when two digests differ."""
    return hashlib.sha256(trace).hexdigest()


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


@dataclass(frozen=True)
class Coverage:
    entered: int
    blocks: int
    collisions: int

    @property
    def fraction(self) -> float:
        # 4 decimals: the ledger has to be a byte-stable fixed point of its
        # own generator, and a bare float would put the platform's repr in the
        # committed file.
        return round(self.entered / self.blocks, 4) if self.blocks else 0.0


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
# collision impossible instead of merely rare. `tests/test_l2_keyseq.py`
# pins both halves: that LINE_SHIFT still clears both probe scripts, and that
# shifting does not change what the program does.
LINE_SHIFT = 2000


def coverage(artifact_src: bytes, specs: Sequence[str]) -> Coverage:
    """Run the artifact once more per spec with `cov=1` and map the UNION of
    the executed lines onto its basic blocks.

    An extra process per spec, not a reuse of the comparison runs: enabling
    the line hook changes the cost of the decompiled side and nothing else,
    but the two runs a grant compares should differ in no respect at all,
    including the hook mask they ran under. Measured cost of the extra runs:
    see the report.
    """
    shifted = b"\n" * LINE_SHIFT + artifact_src
    hit: set[int] = set()
    for spec in specs:
        raw = covered_lines(
            probe_raw(shifted, is_source=True, spec=_with_cov(spec)))
        hit |= {ln - LINE_SHIFT for ln in raw if ln > LINE_SHIFT}
    lines, collisions = block_entry_lines(artifact_src)
    return Coverage(entered=sum(1 for ln in lines if ln in hit),
                    blocks=len(lines), collisions=collisions)


def _with_cov(spec: str) -> str:
    return spec if "cov=1" in spec.split(";") else (spec + ";cov=1" if spec else "cov=1")


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

        No corpus content, ever: `cov` is a number and `refused` is a fixed
        vocabulary word. `detail` -- which can quote a trace line, and a trace
        line can carry a Japanese string constant -- stays out.
        """
        if self.granted:
            return {"cov": self.cov}
        return {"refused": self.reason}


def evaluate(original: bytes, artifact_src: bytes,
             specs: Sequence[str]) -> L2Result:
    """The whole grant rule, over one file and ALL of its authored sequences.

    Every sequence must pass on its own; the coverage badge is taken over
    their union. A file gets more than one sequence when one entry point is
    not the whole story -- `snr_common.lua` carries the two historical
    checkpoints (`systemOption.OptionMain`, `systemConfig.ConfigMain`) plus a
    whole-chunk run, and a single spec could only drive one of them.

    Pure with respect to the ledger: it takes bytes and returns a verdict.
    """
    if not specs:
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
        c = coverage(artifact_src, specs)
    except (ProbeError, subprocess.SubprocessError) as e:
        return L2Result(False, "probe-error", None, str(e)[:400])
    return L2Result(True, None, c.fraction,
                    f"{c.entered}/{c.blocks} blocks, {c.collisions} on a "
                    f"shared entry line")


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
    from pyluadec.pipeline import decompile_file
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    results = evaluate_corpus(corpus, lambda f: decompile_file(f).source)
    granted = [n for n, r in results.items() if r.granted]
    for name in sorted(results):
        r = results[name]
        badge = f"L2@{r.cov:.0%}" if r.granted else f"refused ({r.reason})"
        print(f"  {name:<24} {badge:<22} {r.detail}")
    print(f"L2: {len(granted)}/{len(results)} authored file(s) granted "
          f"({len(KEY_SEQUENCES)} sequence(s) authored, "
          f"{len(list(corpus.glob('*.lua')))} files in the corpus)")
    return 0 if len(granted) == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

"""Cross-corpus scan harness -- M6 task 5.

用法: PYLUADEC_CORPUS_DIR=... PYLUADEC_PRED_CORPUS_DIR=... \
      uv run python scripts/cross_corpus.py --arm all
      (`--arm fingerprint|state|behaviour|all`, `--file NAME` repeatable,
       `--queue PATH` for the machine-readable divergence queue)
产出: build/cross-corpus/queue.json（不入库，纯 job 产物）；报告见
      docs/reports/m6-cross-corpus.md §2。

**This is a JOB, not a suite cost.** `tests/test_cross_corpus.py` keeps only a
smoke subset plus the synthetic non-vacuity proof; the 229-file scan runs from
this CLI.

## The direction, and why it is worth pointing an instrument this way

Every probe gate in this repo so far runs *our decompiled artifact* against the
original bytecode. This one keeps the original bytecode on the left and puts the
**predecessor project's shipped source** on the right
(`PYLUADEC_PRED_CORPUS_DIR`, conventionally `/Users/fotile96/Zndnovel/
lua_scripts`): 229 decompiled Lua source files that were recompiled, repacked
into a PSP ISO and played through to completion by a human. The probes are
already two-sided ("candidate source vs original bytecode"), so the predecessor
side enters exactly where our artifact does -- no forked stubs, no second
implementation of the trace format. A divergence found here is a defect in
something that *shipped*.

That is not speculative. M6 task 4 found two by hand before this harness
existed, and both are in the corpus this file scans (see
`corpus/pred_repairs/`, an out-of-plan safety net that is NOT an input here --
this scans the unmodified predecessor corpus).

## Three arms, three different kinds of evidence

  * **`fingerprint`** -- static. `verify.semantic_score.score_protos`, the
    predecessor's project's own similarity metric, over the two proto trees.
    Sees every proto including ones no probe ever executes; sees no runtime
    behaviour at all.
  * **`state`** -- L1.5. `scripts/probe_global_state.py`: what the chunk's
    top-level body leaves in the global table. Measured shallow: for 222 of 229
    corpus files our own gate's payload is exactly `string:main=<function>`.
  * **`behaviour`** -- L1.75. `scripts/probe_behaviour.py`: actually INVOKES the
    global functions the chunk defines, under a stubbing environment, and
    byte-compares the event trace.

## What counts as a divergence, per arm (the part that carries the judgement)

The `state` and `behaviour` arms are byte comparisons -- no threshold to
choose. The `fingerprint` arm is a graded metric and needs one, so:

    a fingerprint row is queued iff `FileScore.hard_issues` is non-empty
    or `FileScore.drift_type == "semantic_candidate"`.

NOT `score < 1.0`. Measured over all 229 files (2026-08-14): 92 score exactly
1.0, 137 do not, and **zero** have a hard issue. Task 2's census already
established that byte-level divergence is the normal state on this pair
(0/229 byte-faithful, 3903 substantive mismatches), so "score < 1.0" would
queue 60% of the corpus and mean nothing. `drift_type` is the metric's own
answer to "is this difference in a semantically sensitive dimension"
(`SEMANTIC_SENSITIVE_THRESHOLDS`: global reads/writes, call targets, call
shapes, return arity, plus a non-numeric constant difference) and it selects 5.

## Reach: an arm that never fired is not evidence of agreement

The brief's standing warning, and it is not hypothetical here. Measured
2026-08-14 on the original side: 132 of 229 files end in `CAP` (the probe's
3000-event budget), so their "identical" verdict covers a *prefix*, not a run.
`snr_common.lua` is the extreme case -- it defines **79** function-valued
globals and the capped run invokes **1** of them; corpus-wide 307 are defined
and 229 invoked, and every one of the 78 never-invoked ones is in that file.
So every `ArmResult` carries a `reach` token and the CLI prints the split;
`agree` at `reach="truncated"` is a weaker claim than `agree` at
`reach="complete"` and the queue must not blur them.

## The red line

Divergence evidence in committed artifacts is opcode/pc/event-shape summaries,
ASCII identifiers and SHA-256 prefixes. Trace lines carry argument values that
may be Japanese game text, so `event_shape` projects them away and
`_assert_ascii` refuses anything that still is not ASCII. The SHA of the raw
line is what keeps the evidence discriminating after that projection --
`tests/test_cross_corpus.py::
test_the_sha_discriminator_in_behaviour_evidence_is_load_bearing` is the neuter
proof, built on a measured case where the two sides' event shapes agree and
only an argument value differs.

## Pins

`PRED_PINS` is a **separate table per arm**, empty as of task 5. The spec
forbids reusing the 4 L1.5 / 2 L1.75 our-side pins: those were recorded for a
different candidate population and say nothing about this one. Task 6 fills
these in with adjudicated verdicts; until then the CLI exits 1 on any
divergence, which is the honest state -- divergences exist and none is
adjudicated.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Run as `uv run python scripts/cross_corpus.py`, sys.path[0] is scripts/, not
# the repo root, so `scripts.probe_common` would not resolve. Imported as a
# module by the tests it already resolves and this is a no-op. Same preamble as
# probe_global_state.py / probe_behaviour.py.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import probe_behaviour, probe_global_state  # noqa: E402
from scripts.probe_common import adjudicate_pins  # noqa: E402

VERSION = "cross-corpus-v1"

ARMS = ("fingerprint", "state", "behaviour")

#: `kind` vocabulary. `probe-error` is deliberately NOT folded into
#: `divergent`: a candidate that does not compile or does not load is a
#: reportable outcome about the FILE, not a disagreement about what two chunks
#: compute, and the two must not be counted together. It is also never `agree`
#: -- that is the L1.5 gate's hardest-won lesson (it once returned "" for every
#: probe-side failure and compared equal on all 229 files).
KINDS = ("agree", "divergent", "probe-error")

#: `reach` vocabulary -- how much of the original this arm actually exercised.
#: `static` is the fingerprint arm (it compares every proto but executes none);
#: `loaded`/`load-error` are the L1.5 arm's two outcomes; `complete`/
#: `truncated`/`silent` are the L1.75 arm's.
REACH = ("static", "loaded", "load-error", "complete", "truncated", "silent",
         "unknown")

#: First-cut triage vocabulary. NOT verdicts -- Task 6 adjudicates with the
#: pin vocabulary (`real-bug` / `suspect` / `probe-artifact`).
FIRST_CUT = ("candidate-defect", "probable-artifact", "suspect")

#: Adjudicated pins, per arm, in `adjudicate_pins`' `(original, predecessor)`
#: evidence-pair form. EMPTY at task 5 by design; task 6 fills them.
PRED_PINS: dict[str, dict[str, tuple[str, str]]] = {
    "fingerprint": {},
    "state": {},
    "behaviour": {},
}


@dataclass(frozen=True)
class ArmResult:
    file: str
    arm: str
    kind: str                       # one of KINDS
    reach: str                      # one of REACH
    evidence: tuple[str, str]       # (original side, predecessor side), ASCII
    detail: dict = field(default_factory=dict)

    @property
    def diverges(self) -> bool:
        return self.kind != "agree"


# --------------------------------------------------------------------------
# ASCII discipline
# --------------------------------------------------------------------------

def _assert_ascii(value) -> None:
    """Refuse to let anything non-ASCII reach a committed artifact.

    Raises rather than sanitising: a sanitiser would make the red line
    unfalsifiable (every leak would be silently repaired and nothing would ever
    show it had happened), whereas a raise names the field. The projections
    below (`event_shape`, `_short`) are where degradation is supposed to
    happen, and they degrade to a literal `<non-ascii>` marker.
    """
    if isinstance(value, str):
        if not value.isascii():
            raise ValueError("non-ASCII in cross-corpus evidence")
    elif isinstance(value, dict):
        for k, v in value.items():
            _assert_ascii(k)
            _assert_ascii(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _assert_ascii(v)


def json_safe(value) -> bool:
    """True iff `value` is ASCII throughout. The predicate form of
    `_assert_ascii`, for tests."""
    try:
        _assert_ascii(value)
    except ValueError:
        return False
    return True


def _short(raw: bytes, limit: int = 48) -> str:
    """An ASCII-only, bounded rendering of a raw field. Anything that is not
    plain ASCII becomes `<non-ascii:N>` (N = byte length), which is a shape
    fact, not content."""
    if not raw.isascii():
        return f"<non-ascii:{len(raw)}>"
    s = raw.decode("ascii")
    return s if len(s) <= limit else s[:limit] + "..."


# --------------------------------------------------------------------------
# Trace projections
# --------------------------------------------------------------------------

#: The nouns `ldebug.c`'s `getobjname` can produce. Fixed vocabulary, quoted
#: from the C source's `getobjname`/`funcnamefromcode` return strings, not
#: derived from the corpus.
_OBJ_KINDS = (b"global", b"local", b"field", b"upvalue", b"method",
              b"constant", b"for iterator")


def normalize_objname(msg: bytes) -> bytes:
    """Erase `<kind> '<name>'` groups from a Lua error message.

    Lua 5.1 names a value in an error message by the BYTECODE SHAPE that
    produced it, so two chunks that fail at the same point, on the same value,
    for the same reason still print different nouns -- `field '?'` where one
    read a table with a numeric key, `local 'v1'` where the other held it in a
    register. That is the class already pinned twice on our own side
    (`probe_global_state.EXPECTED_ERROR_NAME_DIVERGENCE`,
    `probe_behaviour.EXPECTED_DIVERGENCE`), with instruction-level evidence
    recorded there.

    Only the `<kind> '<name>'` group is erased: the operation ("attempt to
    index" / "attempt to concatenate") and the trailing type ("a nil value")
    survive, so this cannot collapse two genuinely different failures. It CAN
    still over-fire -- two sides that index genuinely different values -- which
    is why it only ever produces a `probable-artifact` TRIAGE label here and
    never a verdict.

    No `re`: the no-regex rule is scoped to `src/pyluadec/{...}` and does not
    reach `scripts/`, but a hand scan is shorter than the pattern would be and
    keeps this file consistent with the rest of the probe tooling.
    """
    out = bytearray()
    i = 0
    n = len(msg)
    while i < n:
        if msg[i:i + 2] == b" '":
            close = msg.find(b"'", i + 2)
            if close >= 0:
                head = bytes(out)
                for kind in _OBJ_KINDS:
                    if head.endswith(kind):
                        del out[len(out) - len(kind):]
                        out += b"<obj>"
                        i = close + 1
                        break
                else:
                    out.append(msg[i])
                    i += 1
                continue
        out.append(msg[i])
        i += 1
    return bytes(out)


def event_shape(line: bytes) -> str:
    """One trace line reduced to an ASCII SHAPE: event kind, the ASCII
    identifier it names, and a size/type projection of the payload.

    Argument VALUES are dropped on purpose. They are the part of a trace that
    can hold Japanese game text, and a committed divergence queue must not
    carry it. What survives is what a reader adjudicating a divergence needs
    and is allowed to see: which event fired, on which name, with how many
    arguments.

    The line's raw SHA is added separately by `behaviour_evidence` -- the shape
    alone is measurably not discriminating (a changed argument value leaves it
    identical).
    """
    if not line:
        return "<end of trace>"
    parts = line.split(b"|")
    kind = _short(parts[0], 16)
    if parts[0] == b"PROBE1" and len(parts) >= 3:
        return f"hdr|{_short(parts[1], 8)}|{_short(parts[2], 12)}"
    if parts[0] == b"C" and len(parts) >= 3:
        return f"C|{_short(parts[1])}|{_short(parts[2], 8)}args"
    if parts[0] == b"I" and len(parts) >= 2:
        return f"I|{_short(parts[1])}"
    if parts[0] == b"R" and len(parts) >= 3:
        msg = normalize_objname(b"|".join(parts[2:]))
        return f"R|{_short(parts[1])}|{_short(msg, 64)}"
    if parts[0] in (b"G", b"S") and len(parts) >= 3:
        return f"{kind}|{_short(parts[1])}|{_value_shape(b'|'.join(parts[2:]))}"
    if parts[0] in (b"P", b"W") and len(parts) >= 2:
        return f"{kind}|{len(b'|'.join(parts[1:]))}B"
    return kind


def _value_shape(raw: bytes) -> str:
    if raw.startswith(b"<function#"):
        return "<function>"
    if raw.startswith(b'"'):
        return f"<string:{len(raw) - 2}B>"
    return _short(raw, 24)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:12]


def behaviour_evidence(orig: bytes, pred: bytes) -> tuple[str, str]:
    """`(original, predecessor)` -- the first differing trace line, as
    `L<n> <shape> sha=<12 hex>`."""
    i, a, b = probe_behaviour.first_difference(orig, pred)
    return (f"L{i} {event_shape(a)} sha={_sha(a)}",
            f"L{i} {event_shape(b)} sha={_sha(b)}")


# --------------------------------------------------------------------------
# Arm: fingerprint (static)
# --------------------------------------------------------------------------

def _path_name(path: tuple[int, ...]) -> str:
    """`(76, 2)` -> `main_76_2`, the repo-wide proto-path spelling."""
    return "main" + "".join(f"_{i}" for i in path)


def _fingerprint_one(corpus_dir: Path, pred_dir: Path, name: str) -> ArmResult:
    from pyluadec import ingest, oracle
    from pyluadec.predcorpus import load_pred_proto
    from pyluadec.verify.certify import carries_debug
    from pyluadec.verify.semantic_score import (collect_proto_signatures,
                                                score_protos)

    src = corpus_dir / name
    original = ingest.load_file(src)
    try:
        # `strip=not carries_debug(original)`: `verify.certify.certify_l3`'s
        # precedent, and the fix M6 task 2 round 1 needed after compiling the
        # predecessor side unstripped manufactured an `upvalues`-LENGTH
        # mismatch on all 260 `nups > 0` protos.
        #
        # **Measured here (2026-08-14): it changes nothing on THIS arm.**
        # Compiling all 229 files both ways produces identical
        # score/status/drift_type/sensitive-paths/hard-issues on 229/229,
        # because `score_protos` never reads `lineinfo`/`locvars`/the upvalue
        # NAME table -- its only upvalue input is `upvalue_count=proto.nups`
        # (semantic_score.py D6), a scalar `luac -s` does not touch, and it is
        # not in `WEIGHTS` at all. The strip trap is a `compare_protos` trap,
        # not a `score_protos` trap. Passed correctly anyway: being right by
        # construction costs one call and does not depend on a measurement that
        # a future corpus could overturn.
        candidate = load_pred_proto(pred_dir, name,
                                    strip=not carries_debug(original))
    except oracle.OracleError as e:
        return ArmResult(name, "fingerprint", "probe-error", "static",
                         ("compiled", f"oracle-error:{type(e).__name__}"),
                         {"error": type(e).__name__})

    fs = score_protos(original, candidate, file_size=src.stat().st_size)
    detail = {
        "score": fs.score,
        "status": fs.status,
        "drift_type": fs.drift_type,
        "hard_issues": list(fs.hard_issues),
        "sensitive_paths": [_path_name(p) for p in fs.semantic_sensitive_paths],
    }
    queued = bool(fs.hard_issues) or fs.drift_type == "semantic_candidate"
    if not queued:
        return ArmResult(name, "fingerprint", "agree", "static",
                         (f"score={fs.score:.6f}", f"score={fs.score:.6f}"),
                         detail)

    # Evidence pair = the WORST sensitive path's per-side signature summary.
    # Per-file granularity necessarily loses information when a file carries
    # several (snr_common.lua carries 5, one of which is a deliberate
    # localization edit and another is Task 4's hand-found defect); the full
    # list stays in `detail.sensitive_paths` and the pair names the worst.
    sensitive = set(fs.semantic_sensitive_paths)
    worst = min((p for p in fs.proto_scores if p.path in sensitive),
                key=lambda p: p.score, default=None)
    if worst is None:
        return ArmResult(name, "fingerprint", "divergent", "static",
                         (f"score={fs.score:.6f} hard={','.join(fs.hard_issues)}",
                          f"score={fs.score:.6f}"), detail)
    osig = collect_proto_signatures(original).get(worst.path)
    csig = collect_proto_signatures(candidate).get(worst.path)
    detail["worst_path"] = _path_name(worst.path)
    detail["worst_score"] = worst.score
    detail["worst_components"] = {k: v for k, v in (worst.components or {}).items()
                                  if v < 1.0}
    return ArmResult(name, "fingerprint", "divergent", "static",
                     (_sig_summary(worst.path, osig), _sig_summary(worst.path, csig)),
                     detail)


def _sig_summary(path, sig) -> str:
    """A proto signature as opcode/block counts only -- no constants, no
    names."""
    if sig is None:
        return f"{_path_name(path)} <missing>"
    return (f"{_path_name(path)} code={sig.code_len} "
            f"reach={sig.cfg_reachable} all={sig.cfg_all} "
            f"reads={sum(sig.global_reads.values())} "
            f"calls={sum(sig.call_targets.values())}")


# --------------------------------------------------------------------------
# Arm: state (L1.5)
# --------------------------------------------------------------------------

def _state_one(corpus_dir: Path, pred_dir: Path, name: str) -> ArmResult:
    try:
        orig = probe_global_state.probe((corpus_dir / name).read_bytes(),
                                        is_source=False)
        pred = probe_global_state.probe((pred_dir / name).read_bytes(),
                                        is_source=True)
    except probe_global_state.ProbeError as e:
        return ArmResult(name, "state", "probe-error", "unknown",
                         ("probe-error", f"probe-error:{_short(str(e).encode()[:64])}"),
                         {"error": "ProbeError"})
    om, pm = orig.split("|", 1)[0], pred.split("|", 1)[0]
    detail = {"orig_marker": om, "pred_marker": pm,
              "orig_payload_len": len(probe_global_state.payload_of(orig)),
              "pred_payload_len": len(probe_global_state.payload_of(pred))}
    reach = "loaded" if om == "OK" else "load-error"
    if orig == pred:
        return ArmResult(name, "state", "agree", reach,
                         (f"{om} len={detail['orig_payload_len']}",
                          f"{pm} len={detail['pred_payload_len']}"), detail)
    # The L1.5 payload is a deterministic ASCII serialisation (sorted
    # "type:key" keys, "%.17g" numbers, "<type>" placeholders) but a table key
    # or an error message can still carry corpus bytes, so it goes through the
    # same projection as everything else.
    da, db = _first_diff_str(orig, pred)
    return ArmResult(name, "state", "divergent", reach,
                     (_short(da.encode("utf-8", "replace"), 96),
                      _short(db.encode("utf-8", "replace"), 96)),
                     detail | {"orig_sha": _sha(orig.encode("utf-8", "replace")),
                               "pred_sha": _sha(pred.encode("utf-8", "replace"))})


def _first_diff_str(a: str, b: str) -> tuple[str, str]:
    al, bl = a.split("\n"), b.split("\n")
    for i in range(max(len(al), len(bl))):
        x = al[i] if i < len(al) else "<end>"
        y = bl[i] if i < len(bl) else "<end>"
        if x != y:
            return x, y
    return "", ""


# --------------------------------------------------------------------------
# Arm: behaviour (L1.75)
# --------------------------------------------------------------------------

def _behaviour_one(corpus_dir: Path, pred_dir: Path, name: str) -> ArmResult:
    try:
        orig = probe_behaviour.probe_raw((corpus_dir / name).read_bytes(),
                                         is_source=False)
        pred = probe_behaviour.probe_raw((pred_dir / name).read_bytes(),
                                         is_source=True)
    except probe_behaviour.ProbeError as e:
        return ArmResult(name, "behaviour", "probe-error", "unknown",
                         ("probe-error", f"probe-error:{_short(str(e).encode()[:64])}"),
                         {"error": "ProbeError"})
    ost, oev = probe_behaviour.header(orig)
    pst, pev = probe_behaviour.header(pred)
    defined, invoked = _invocation_reach(orig)
    if ost != "OK":
        reach = "truncated"
    elif defined and not invoked:
        reach = "silent"
    elif invoked < defined:
        reach = "truncated"
    else:
        reach = "complete"
    detail = {"orig_status": ost, "orig_events": oev,
              "pred_status": pst, "pred_events": pev,
              "fn_globals_defined": defined, "fn_globals_invoked": invoked}
    if orig == pred:
        return ArmResult(name, "behaviour", "agree", reach,
                         (f"hdr|{ost}|{oev}", f"hdr|{pst}|{pev}"), detail)
    i, a, b = probe_behaviour.first_difference(orig, pred)
    ev = behaviour_evidence(orig, pred)
    detail |= {"first_diff_line": i,
               "orig_shape": event_shape(a), "pred_shape": event_shape(b),
               "multiset_equal_after_objname": _same_multiset(orig, pred)}
    return ArmResult(name, "behaviour", "divergent", reach, ev, detail)


def _same_multiset(orig: bytes, pred: bytes) -> bool:
    """True iff the two traces record the SAME events, in any order, once
    `getobjname` nouns are erased.

    Two documented artifact classes at once, and only computed on a divergence
    so it costs nothing on the 227 agreeing files:

    * **Order.** Lua table iteration order is the node array's, and the node
      array depends on `NEWTABLE`'s size hint -- a constructor that luac gave
      `NEWTABLE ... 0 23` iterates differently from one it gave `0 0` and grew
      by rehash. Already pinned on our own side (`probe_behaviour.
      EXPECTED_DIVERGENCE["snr_novel.lua"]`) with the pcs quoted.
    * **Naming.** `normalize_objname`'s class, above.

    Strict on purpose: a file that reorders AND does something else falls
    through to `suspect` rather than being absorbed here.
    """
    return (collections.Counter(normalize_objname(x) for x in orig.split(b"\n"))
            == collections.Counter(normalize_objname(x) for x in pred.split(b"\n")))


def _invocation_reach(trace: bytes) -> tuple[int, int]:
    """`(function-valued globals defined, of those invoked)` on one side.

    Same last-write-wins reading as `probe_behaviour.invocation_gap`, but
    unconditional: that function deliberately returns `[]` for non-`OK` runs
    because a gap there is expected rather than a defect. Here the gap IS the
    measurement -- it is how a `truncated` reach is distinguished from a
    `complete` one, and 132 of 229 files are non-`OK`.
    """
    last: dict[bytes, bool] = {}
    invoked: set[bytes] = set()
    for line in trace.split(b"\n")[1:]:
        if line.startswith(b"G|"):
            parts = line.split(b"|")
            if len(parts) >= 3:
                last[parts[1]] = parts[2].startswith(b"<function#")
        elif line.startswith(b"I|"):
            invoked.add(line.split(b"|")[1])
    fns = {k for k, is_fn in last.items() if is_fn}
    return len(fns), len(fns & invoked)


# --------------------------------------------------------------------------
# First cut
# --------------------------------------------------------------------------

def first_cut(r: ArmResult) -> str:
    """Mechanical triage of one divergent row. **Not a verdict** -- Task 6
    adjudicates each row to `real-bug` / `suspect` / `probe-artifact` with
    instruction-level evidence. Three rules, each of which fires on this corpus
    (a rule with no instance is not added; see MEMORY.md "guards must be proven
    load-bearing"):

    * `candidate-defect` -- **control-flow evidence**. Behaviour arm: the two
      headers disagree, i.e. one side's run reached a different status or a
      different event count, which cannot happen without the two chunks taking
      different paths. Fingerprint arm: a hard issue, or a sensitive path whose
      `cfg_reachable`/`cfg_all` component is below 1.0 -- the block/edge counts
      of the reconstructed control-flow graph differ.
    * `probable-artifact` -- the two traces are the SAME MULTISET of events once
      `getobjname` nouns are erased (`_same_multiset`): a reordering plus a
      naming difference, both classes already pinned on our own side with
      instruction-level evidence.
    * `suspect` -- everything else. Divergent, no mechanical story yet.

    Raises on a non-divergent row: a triage label for a row that agrees would
    be meaningless, and returning `"suspect"` for it would quietly inflate that
    bucket if the queue construction ever stopped filtering.
    """
    if not r.diverges:
        raise ValueError(f"first_cut on a non-divergent row: {r.file}/{r.arm}")
    if r.kind == "probe-error":
        # Not a disagreement about what two chunks compute, so none of the
        # rules below apply; the row keeps `kind == "probe-error"`, which is
        # what a reader should act on. Zero instances in the 229-file scan.
        return "suspect"
    if r.arm == "behaviour":
        if r.detail.get("multiset_equal_after_objname"):
            return "probable-artifact"
        if (r.detail.get("orig_status") != r.detail.get("pred_status")
                or r.detail.get("orig_events") != r.detail.get("pred_events")):
            return "candidate-defect"
        return "suspect"
    if r.arm == "fingerprint":
        if r.detail.get("hard_issues"):
            return "candidate-defect"
        comps = r.detail.get("worst_components") or {}
        if any(comps.get(k, 1.0) < 1.0 for k in ("cfg_reachable", "cfg_all")):
            return "candidate-defect"
        return "suspect"
    return "suspect"


# --------------------------------------------------------------------------
# scan
# --------------------------------------------------------------------------

_RUNNERS = {"fingerprint": _fingerprint_one,
            "state": _state_one,
            "behaviour": _behaviour_one}


def _resolve(corpus_dir, pred_dir) -> tuple[Path, Path]:
    corpus_dir = Path(corpus_dir or os.environ["PYLUADEC_CORPUS_DIR"])
    pred_dir = Path(pred_dir or os.environ["PYLUADEC_PRED_CORPUS_DIR"])
    return corpus_dir, pred_dir


def scan(arm: str, files=None, *, corpus_dir=None, pred_dir=None,
         jobs: int = 8) -> dict[str, ArmResult]:
    """`{file name: ArmResult}` for one arm.

    `files` defaults to every `*.lua` in the corpus directory, sorted. `arm`
    must be one of `ARMS` -- `"all"` is a CLI convenience, not a scan mode,
    because the return type is one result per file and three arms would need
    a different shape.
    """
    if arm not in _RUNNERS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    corpus_dir, pred_dir = _resolve(corpus_dir, pred_dir)
    names = (sorted(f.name for f in corpus_dir.glob("*.lua"))
             if files is None else list(files))
    run = _RUNNERS[arm]

    def one(name: str) -> ArmResult:
        r = run(corpus_dir, pred_dir, name)
        _assert_ascii(list(r.evidence))
        _assert_ascii(r.detail)
        return r

    if jobs <= 1 or len(names) == 1:
        return {n: one(n) for n in names}
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        return {r.file: r for r in ex.map(one, names)}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _queue_rows(results: dict[str, dict[str, ArmResult]]) -> list[dict]:
    rows = []
    for arm in ARMS:
        for name in sorted(results.get(arm, {})):
            r = results[arm][name]
            if not r.diverges:
                continue
            rows.append(asdict(r) | {"first_cut": first_cut(r),
                                     "evidence": list(r.evidence)})
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arm", default="all",
                    choices=(*ARMS, "all"))
    ap.add_argument("--file", action="append", dest="files", default=None,
                    help="corpus-relative filename; repeatable (default: all)")
    ap.add_argument("--queue", default=str(ROOT / "build" / "cross-corpus"
                                           / "queue.json"),
                    help="where to write the machine-readable divergence queue")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args(argv)

    arms = ARMS if args.arm == "all" else (args.arm,)
    corpus_dir, pred_dir = _resolve(None, None)
    results: dict[str, dict[str, ArmResult]] = {}
    bad = False
    for arm in arms:
        res = scan(arm, args.files, corpus_dir=corpus_dir, pred_dir=pred_dir,
                   jobs=args.jobs)
        results[arm] = res
        divergent = {n: r.evidence for n, r in res.items() if r.diverges}
        unexpected, moved, gone = adjudicate_pins(divergent, PRED_PINS[arm])
        reach = _reach_census(res)
        print(f"{arm}: {len(res) - len(divergent)}/{len(res)} agree, "
              f"{len(divergent)} divergent "
              f"({len(divergent) - len(unexpected)} pinned); reach {reach}")
        for n in sorted(divergent):
            r = res[n]
            print(f"    {n:24s} {first_cut(r):18s} reach={r.reach}")
            print(f"      orig: {r.evidence[0]}")
            print(f"      pred: {r.evidence[1]}")
        if moved:
            print(f"  pinned evidence moved: {moved}")
        if gone:
            print(f"  pinned divergence(s) converged or vanished: {gone}")
        bad = bad or bool(unexpected or moved or gone)

    rows = _queue_rows(results)
    dest = Path(args.queue)
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = {"version": VERSION, "arms": list(arms),
           "n_files": {a: len(results[a]) for a in arms},
           "summary": _summary(results, rows), "rows": rows}
    _assert_ascii(doc)
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=True) + "\n")
    print(f"queue: {len(rows)} row(s) over "
          f"{len({r['file'] for r in rows})} file(s) -> {dest}")
    return 1 if bad else 0


def _reach_census(res: dict[str, ArmResult]) -> str:
    counts: dict[str, int] = {}
    for r in res.values():
        counts[r.reach] = counts.get(r.reach, 0) + 1
    return " ".join(f"{k}={counts[k]}" for k in sorted(counts))


def _summary(results, rows) -> dict:
    cut: dict[str, int] = {}
    for row in rows:
        cut[row["first_cut"]] = cut.get(row["first_cut"], 0) + 1
    reach: dict[str, dict[str, int]] = {}
    for arm, res in results.items():
        per: dict[str, int] = {}
        for r in res.values():
            per[r.reach] = per.get(r.reach, 0) + 1
        reach[arm] = {k: per[k] for k in sorted(per)}
    return {"first_cut": {k: cut[k] for k in sorted(cut)},
            "reach": reach,
            "divergent_files": sorted({r["file"] for r in rows}),
            "divergent_rows_per_arm": {
                a: sum(1 for r in rows if r["arm"] == a) for a in results}}


if __name__ == "__main__":
    sys.exit(main())

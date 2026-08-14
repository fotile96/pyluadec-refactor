#!/usr/bin/env python3
"""Invariant panel -- M7 task 3 (spec §2.1): per-proto pred-vs-original Factor E.

Every family is a **two-sided equality** check over machinery that already
exists -- nothing here re-derives a counter:

* ``loss:<kind>`` x8 -- the two-sided form of ``scripts/loss_sweep.py``'s
  ``LOSS_KINDS``. The sweep flags only what the predecessor LOST (its
  ``_shortfalls``); a proto that GAINED a counter passes it. The panel's
  ``panel-pass`` means *equal*, so both directions flag here. The corpus
  already measured why that matters: ``snr_common.lua:main_76_2`` (defect 2)
  gains three ``EQ`` while losing three ``TESTSET`` -- a direction-aware
  blind spot is not hypothetical.
* ``fingerprint`` -- ``ProtoSignature`` equality over every field EXCEPT
  ``constant_fingerprint`` (a deliberate narrowing, see below). This is the
  per-proto promotion of the fingerprint arm's comparison
  (``cross_corpus._fingerprint_one`` reports per FILE and its summary prints
  opcode/block counts only).
* ``constant_values`` -- NEW (added after the glm-5.3 cross-review verified
  no existing family compares constant values): the multiset of constants
  **referenced by load-class operands** -- ``LOADK``/``GETGLOBAL``/
  ``SETGLOBAL`` ``Bx`` and every RK-encoded operand with the K bit set
  (``ADD/SUB/MUL/DIV/MOD/POW/SELF``'s C; ``EQ/LT/LE/SETTABLE``'s B and C) --
  compared **by value, never by pool index**: luac pools follow first
  reference, so pool reordering is the known-benign bulk of the census's
  3903 mismatches and must not flag. Numbers compare by their 8-byte
  ``LuaNumber.payload`` (bit-exact); strings as ``bytes``.

``constant_fingerprint`` is excluded from ``fingerprint`` because it hashes
the whole POOL: a pool-only (unreferenced) constant would flag there while
having no semantic effect -- nothing loads it. Referenced VALUES are covered
exactly once, by ``constant_values``. Cost of this split: a difference
limited to unreferenced pool entries flags nothing; recorded as blindness.

## Blindness list (spec §2.1 requires it; the warranty inherits it)

* **Instruction ORDER within equal counts** -- two protos with identical
  per-key counters and identical opcode counts can still execute the same
  effects in a different order.
* **Control-flow SHAPE beyond loop/test counts** -- ``cfg_reachable``/
  ``cfg_all`` and the two loop scalars cover gross shape; anything finer
  (e.g. which branch of a test carries which body) is not compared.
* **Cross-proto behavioural integration** -- every family is per-proto; no
  factor grades whether protos INTERACT correctly. A blind spot shared by
  both M7 spec proposals and recorded here so the warranty inherits it.
* **Bit-exact numbers** -- ``constant_values`` compares number constants by
  raw payload: two mathematically equal doubles with different bit patterns
  flag. Deliberate (bit-exactness has no false negatives on value change).
* **Unreferenced pool constants** (above).
* Whatever ``ProtoSignature`` itself does not measure -- e.g.
  ``call_targets`` is the crude symbolic fingerprint that module documents,
  not a call graph.

The red line: every evidence string is opcodes, counts, pcs and field names
-- never a constant value or a corpus string; ``cross_corpus.json_safe`` is
asserted over every evidence string at ``PanelResult`` construction.
"""
from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass, fields as dc_fields
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cross_corpus import json_safe  # noqa: E402
from loss_sweep import TEST_OPCODES, _path_name, _subprotos, loop_shape  # noqa: E402

from pyluadec.ingest import load_file  # noqa: E402
from pyluadec.ingest.proto import LuaNumber, Proto  # noqa: E402
from pyluadec.lift import lift_proto  # noqa: E402
from pyluadec.lift.opcodes import Op, indexk, isk  # noqa: E402
from pyluadec.predcorpus import load_pred_proto  # noqa: E402
from pyluadec.verify.certify import carries_debug  # noqa: E402
from pyluadec.verify.semantic_score import (  # noqa: E402
    ProtoSignature, collect_proto_signatures)

#: The eight two-sided loss families, named exactly as `LOSS_KINDS`.
LOSS_FAMILIES = ("global_reads", "global_writes", "call_targets", "call_shapes",
                 "return_arity", "test_ops", "n_natural_loops", "n_back_edges")

#: Which `ProtoSignature` fields the fingerprint family compares: all of
#: them except the pool-level `constant_fingerprint` (see module docstring).
_FINGERPRINT_FIELDS = tuple(
    f.name for f in dc_fields(ProtoSignature) if f.name != "constant_fingerprint")

_BX_CONST_OPS = (Op.LOADK, Op.GETGLOBAL, Op.SETGLOBAL)
_RK_C_OPS = frozenset({Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW, Op.SELF})
_RK_BC_OPS = frozenset({Op.EQ, Op.LT, Op.LE, Op.SETTABLE})


class MissingProtoPath(Exception):
    """A proto path present in one tree and absent from the other. The 1:1
    tree correspondence is established (229/229, `tests/test_predcorpus.py`);
    a violation is a finding, not a verdict -- raise, never swallow."""


@dataclass(frozen=True)
class PanelResult:
    """One proto pair's panel verdict: `diffs` maps family name -> ASCII
    evidence and is EMPTY on pass."""

    diffs: dict[str, str]

    def __post_init__(self) -> None:
        for ev in self.diffs.values():
            if not json_safe(ev):
                raise ValueError(f"non-ASCII evidence string: {ev!r}")


def _canon(c) -> tuple:
    """A hashable, never-decoded canonical form of one constant."""
    if isinstance(c, LuaNumber):
        return ("num", c.payload)
    if isinstance(c, bytes):
        return ("str", c)
    if isinstance(c, bool):
        return ("bool", c)
    if c is None:
        return ("nil",)
    raise TypeError(f"unknown constant type: {type(c)!r}")


def _references(proto: Proto) -> list[tuple[int, str, tuple]]:
    """Every load-class constant reference as `(pc, opname, canon)`, in pc
    order -- the operand walk `constant_values` compares."""
    fn = lift_proto(proto)
    out: list[tuple[int, str, tuple]] = []
    for pc in sorted(fn.instrs):
        ri = fn.instrs[pc].ri
        idxs: list[int] = []
        if ri.op in _BX_CONST_OPS:
            idxs.append(ri.bx)
        if ri.op in _RK_C_OPS and isk(ri.c):
            idxs.append(indexk(ri.c))
        if ri.op in _RK_BC_OPS:
            if isk(ri.b):
                idxs.append(indexk(ri.b))
            if isk(ri.c):
                idxs.append(indexk(ri.c))
        out.extend((pc, ri.op.name, _canon(proto.constants[i])) for i in idxs)
    return out


def _two_sided_loss(o_sig: ProtoSignature, p_sig: ProtoSignature,
                    orig: Proto, pred: Proto) -> dict[str, str]:
    out: dict[str, str] = {}
    for k in ("global_reads", "global_writes", "call_targets", "call_shapes",
              "return_arity"):
        a, b = getattr(o_sig, k), getattr(p_sig, k)
        n_differ = sum(1 for key in set(a) | set(b) if a[key] != b[key])
        if n_differ:
            out[f"loss:{k}"] = (f"totals orig {sum(a.values())} != pred "
                                f"{sum(b.values())}, {n_differ} key(s) differ")
    ops_differ = [op for op in TEST_OPCODES
                  if o_sig.opcode_counts[op] != p_sig.opcode_counts[op]]
    if ops_differ:
        detail = ", ".join(f"{op} {o_sig.opcode_counts[op]}!={p_sig.opcode_counts[op]}"
                           for op in ops_differ)
        out["loss:test_ops"] = f"per-opcode {detail}"
    o_loops, o_backs = loop_shape(orig)
    p_loops, p_backs = loop_shape(pred)
    if o_loops != p_loops:
        out["loss:n_natural_loops"] = f"orig {o_loops} != pred {p_loops}"
    if o_backs != p_backs:
        out["loss:n_back_edges"] = f"orig {o_backs} != pred {p_backs}"
    return out


def _fingerprint(o_sig: ProtoSignature, p_sig: ProtoSignature) -> dict[str, str]:
    differ = [name for name in _FINGERPRINT_FIELDS
              if getattr(o_sig, name) != getattr(p_sig, name)]
    if not differ:
        return {}
    return {"fingerprint": "differing field(s): " + ", ".join(differ)}


def _constant_values(orig: Proto, pred: Proto) -> dict[str, str]:
    o_refs, p_refs = _references(orig), _references(pred)
    o_ms = Counter(v for _, _, v in o_refs)
    p_ms = Counter(v for _, _, v in p_refs)
    if o_ms == p_ms:
        return {}
    o_only = o_ms - p_ms
    p_only = p_ms - o_ms
    first = next(((pc, op) for pc, op, v in o_refs if v in o_only),
                 next(((pc, op) for pc, op, v in p_refs if v in p_only), None))
    where = f", first divergence at pc {first[0]} {first[1]}" if first else ""
    return {"constant_values": (
        f"orig-only {sum(o_only.values())} value(s), pred-only "
        f"{sum(p_only.values())} value(s){where}")}


def proto_panel(orig: Proto, pred: Proto) -> PanelResult:
    """The panel verdict for one aligned proto pair (same tree path)."""
    o_sig = collect_proto_signatures(orig)[()]
    p_sig = collect_proto_signatures(pred)[()]
    diffs: dict[str, str] = {}
    diffs.update(_two_sided_loss(o_sig, p_sig, orig, pred))
    diffs.update(_fingerprint(o_sig, p_sig))
    diffs.update(_constant_values(orig, pred))
    return PanelResult(diffs=diffs)


def file_panel(corpus_dir: Path, pred_dir: Path, name: str) -> dict[str, PanelResult]:
    """Panel verdicts for every proto of `name`, keyed by the repo-wide
    proto-path spelling (`main_0_1`). The pred side is compiled with the
    documented strip rule (`strip=not carries_debug(original)`)."""
    orig = load_file(Path(corpus_dir) / name)
    pred = load_pred_proto(Path(pred_dir), name, strip=not carries_debug(orig))
    o_all = _subprotos(orig)
    p_all = _subprotos(pred)
    if set(o_all) != set(p_all):
        missing = set(o_all) ^ set(p_all)
        raise MissingProtoPath(
            f"{name}: path set mismatch at "
            + ", ".join(_path_name(p) for p in sorted(missing)))
    return {_path_name(p): proto_panel(o_all[p], p_all[p])
            for p in sorted(o_all)}

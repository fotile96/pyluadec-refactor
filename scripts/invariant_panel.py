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


def scan_all(corpus_dir: Path, pred_dir: Path) -> dict[str, dict[str, PanelResult]]:
    """`file_panel` over every corpus file, sorted (deterministic order)."""
    names = sorted(p.name for p in Path(corpus_dir).glob("*.lua"))
    return {name: file_panel(corpus_dir, pred_dir, name) for name in names}


def _non_pass(scan: dict[str, dict[str, PanelResult]]) -> dict[str, dict[str, str]]:
    """The divergent population: `<file>:<proto>` -> family -> evidence."""
    out: dict[str, dict[str, str]] = {}
    for name, protos in scan.items():
        for path, res in protos.items():
            if res.diffs:
                out[f"{name}:{path}"] = res.diffs
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI: `--all` scans both corpora and prints the divergent population
    bucketed by family and file, then gates the observation fixed point (the
    live scan must reproduce `corpus/observation/panel.json` byte-for-byte;
    `--file NAME` for one file).

    **Job conditions** (the out-of-suite four): home = this script;
    trigger = **before M7 Task 11, at milestone close, and after any change
    to `sir/`/`express/`/`emit/`/`structure/` or to this module** (the panel
    itself is invariant to our repairs -- it compares pred vs original --
    but the pins' evidence is not invariant to panel-code changes); one
    command = the `--all` invocation below; last run's numbers live in
    `docs/reports/m7-warranty.md` §2.

    Cost (measured, 2026-08-15): **5.9-6.1 s** over 229 files / 1944 pairs,
    linear in files (one compile+ingest+panel per file; compile memoized).
    The suite keeps only the fixed-point/pin-currency/summary tests
    (`tests/test_invariant_panel.py`, 6.1 s) plus the synthetic Task-3 unit
    tests; regeneration-with-adjudication is this job.
    """
    import argparse
    import time

    from probe_common import adjudicate_pins  # noqa: E402 (sibling import)

    ap = argparse.ArgumentParser(prog="invariant_panel")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--file")
    args = ap.parse_args(argv)
    corpus = Path(__import__("os").environ.get("PYLUADEC_CORPUS_DIR", ""))
    pred = Path(__import__("os").environ.get("PYLUADEC_PRED_CORPUS_DIR", ""))
    if args.all:
        if not corpus.is_dir() or not pred.is_dir():
            print("both corpus env vars must be set for --all", file=sys.stderr)
            return 1
        t0 = time.monotonic()
        scan = scan_all(corpus, pred)
        dt = time.monotonic() - t0
    elif args.file:
        scan = {args.file: file_panel(corpus, pred, args.file)}
        dt = 0.0
    else:
        ap.error("need --all or --file NAME")
        return 1  # unreachable
    divergent = _non_pass(scan)
    by_family: Counter[str] = Counter()
    by_file: Counter[str] = Counter()
    for key, diffs in divergent.items():
        by_family.update(diffs.keys())
        by_file[key.split(":")[0]] += 1
    n_total = sum(len(p) for p in scan.values())
    print(f"panel: {n_total - len(divergent)}/{n_total} pass, "
          f"{len(divergent)} divergent ({dt:.2f}s)")
    for fam, n in sorted(by_family.items(), key=lambda kv: -kv[1]):
        print(f"  {fam:24s} {n}")
    for f, n in sorted(by_file.items()):
        print(f"  file {f}: {n} divergent proto(s)")
    if args.all:
        # The gate is the observation-artifact fixed point: the live scan must
        # reproduce the committed panel.json byte-for-byte. `adjudicate_pins`
        # over the PINNED subset adds the diagnosis the byte compare lacks
        # (a pin whose evidence moved, a pin whose row converged -- both are
        # byte changes too, but the pin protocol names them). Unpinned rows
        # are part of the record, not failures: they disqualify the pred side
        # per-file at selection time and never ship (spec §6).
        committed = (Path(__file__).resolve().parents[1]
                     / "corpus" / "observation" / "panel.json").read_bytes()
        fresh = panel_bytes(scan)
        if fresh != committed:
            fresh_rows = {f"{n}:{p}": v
                          for n, protos in scan.items()
                          for p, v in protos.items()}
            import json
            old = json.loads(committed)
            for key, verdict in sorted(fresh_rows.items()):
                name, path = key.split(":", 1)
                was = old.get(name, {}).get(path)
                if verdict.diffs and was == "pass":
                    print(f"FIXED-POINT BREAK: {key} pass -> divergent "
                          f"({', '.join(sorted(verdict.diffs))})", file=sys.stderr)
                if not verdict.diffs and was != "pass" and was is not None:
                    print(f"FIXED-POINT BREAK: {key} divergent -> pass",
                          file=sys.stderr)
            divergent_ev = {k: tuple(sorted(d.items()))
                            for k, d in divergent.items()}
            _, moved, gone = adjudicate_pins(divergent_ev, pin_evidence())
            for kind, rows in (("moved", moved), ("gone", gone)):
                for r in rows:
                    print(f"PIN {kind}: {r}", file=sys.stderr)
            print("panel: regenerated bytes differ from committed "
                  "corpus/observation/panel.json -- regenerate and adjudicate "
                  "the change (pins only via the rules in the module)",
                  file=sys.stderr)
            return 1
        print(f"panel: fixed point holds; {len(PANEL_PINS)} pin(s) live, "
              f"{len(divergent) - len(PANEL_PINS)} unpinned row(s) recorded")
    return 0


#: Adjudicated pins, keyed `"<file>:<proto path>"` (Task 4). Populated by the
#: corpus run; the pin-gate/fixed-point/summary tests in
#: `tests/test_invariant_panel.py` hold them to the live scan. Notes cite the
#: M6 verdicts (`PRED_PINS` / `LOSS_PINS` / report §§3-4) -- never re-litigated.
@dataclass(frozen=True)
class PanelPin:
    """One adjudicated divergence: `note` cites the M6 verdict that covers
    it (never re-litigated); `evidence` is the exact family->evidence map at
    pin time, the form `adjudicate_pins` compares for movement."""

    note: str
    evidence: tuple


PANEL_PINS: dict[str, PanelPin] = {
    # Generated by M7 task 4 (2026-08-15); rules in docs/reports/m7-warranty.md
    # 2 -- defect protos cite the M6 report section and the pred_repairs
    # disposition; LOSS_PINS rows cite their per-proto M6 verdict; rows in
    # per-file equivalent-transform files cite that verdict, and only when
    # their family set is fingerprint/loss (constant_values is new evidence no
    # M6 verdict saw -- such rows stay unpinned). Held to the live scan by
    # tests/test_invariant_panel.py.
    "snr_common.lua:main_27": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TESTSET 2!=0')),
    ),
    "snr_common.lua:main_55": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TESTSET 2!=0')),
    ),
    "snr_common.lua:main_74_13": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TEST 23!=15, TESTSET 7!=0')),
    ),
    "snr_common.lua:main_75": PanelPin(
        note="defect 6 (M6 report 3.4; repaired, corpus/pred_repairs)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:n_back_edges', 'orig 1 != pred 0'), ('loss:n_natural_loops', 'orig 1 != pred 0')),
    ),
    "snr_common.lua:main_76_2": PanelPin(
        note="defect 2 (M6 report 3.4; repaired, corpus/pred_repairs)",
        evidence=(('constant_values', 'orig-only 0 value(s), pred-only 48 value(s), first divergence at pc 1 LOADK'), ('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts, global_reads, call_targets, call_shapes'), ('loss:call_shapes', 'totals orig 16 != pred 27, 5 key(s) differ'), ('loss:call_targets', 'totals orig 16 != pred 27, 5 key(s) differ'), ('loss:global_reads', 'totals orig 27 != pred 42, 6 key(s) differ'), ('loss:n_back_edges', 'orig 1 != pred 4'), ('loss:test_ops', 'per-opcode EQ 21!=28, LT 3!=5, TEST 1!=0, TESTSET 2!=0')),
    ),
    "snr_common.lua:main_76_7": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TESTSET 2!=0')),
    ),
    "snr_common.lua:main_77_24": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TESTSET 1!=0')),
    ),
    "snr_common.lua:main_83": PanelPin(
        note="row-level real-bug, path-level intentional-edit (M6 report 3.5; font resource path)",
        evidence=(('constant_values', 'orig-only 1 value(s), pred-only 1 value(s), first divergence at pc 47 LOADK'), ('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts')),
    ),
    "snr_fragment_main.lua:main_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_fragment_main.lua:main_1": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_reachable, opcode_counts, opcode_family_counts'),),
    ),
    "snr_fragment_main.lua:main_3": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TESTSET 2!=0')),
    ),
    "snr_graphic.lua:main_2": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TEST 1!=0')),
    ),
    "snr_graphic.lua:main_3": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TEST 3!=0')),
    ),
    "snr_graphic.lua:main_4": PanelPin(
        note="defect 4 (M6 report 3.4; repaired, corpus/pred_repairs)",
        evidence=(('constant_values', 'orig-only 2 value(s), pred-only 17 value(s), first divergence at pc 120 EQ'), ('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts, call_targets, call_shapes'), ('loss:call_shapes', 'totals orig 63 != pred 65, 1 key(s) differ'), ('loss:call_targets', 'totals orig 63 != pred 65, 1 key(s) differ'), ('loss:test_ops', 'per-opcode EQ 42!=36, LT 13!=15, TEST 8!=5')),
    ),
    "snr_lib.lua:main_1": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TESTSET 2!=0')),
    ),
    "snr_mainmenu.lua:main_7": PanelPin(
        note="defect 3 (M6 report 3.4; repaired, corpus/pred_repairs)",
        evidence=(('constant_values', 'orig-only 16 value(s), pred-only 20 value(s), first divergence at pc 27 EQ'), ('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts, global_reads'), ('loss:global_reads', 'totals orig 291 != pred 283, 1 key(s) differ'), ('loss:n_back_edges', 'orig 32 != pred 28'), ('loss:test_ops', 'per-opcode EQ 170!=154, TEST 0!=20, TESTSET 20!=0')),
    ),
    "snr_memory.lua:main_2": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TEST 1!=0')),
    ),
    "snr_memory.lua:main_3": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TEST 3!=0')),
    ),
    "snr_memory.lua:main_4": PanelPin(
        note="defect 5 (M6 report 3.4; repaired, corpus/pred_repairs)",
        evidence=(('constant_values', 'orig-only 2 value(s), pred-only 17 value(s), first divergence at pc 121 EQ'), ('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts, call_targets, call_shapes'), ('loss:call_shapes', 'totals orig 42 != pred 44, 1 key(s) differ'), ('loss:call_targets', 'totals orig 42 != pred 44, 1 key(s) differ'), ('loss:test_ops', 'per-opcode EQ 34!=28, LT 10!=12, TEST 7!=5')),
    ),
    "snr_music.lua:main_3": PanelPin(
        note="defect 1 (M6 report 3.4; repaired, corpus/pred_repairs)",
        evidence=(('constant_values', 'orig-only 0 value(s), pred-only 7 value(s), first divergence at pc 16 EQ'), ('fingerprint', 'differing field(s): code_len, cfg_reachable, cfg_all, opcode_counts, opcode_family_counts, global_reads, call_targets, call_shapes'), ('loss:call_shapes', 'totals orig 23 != pred 26, 2 key(s) differ'), ('loss:call_targets', 'totals orig 23 != pred 26, 2 key(s) differ'), ('loss:global_reads', 'totals orig 20 != pred 22, 1 key(s) differ'), ('loss:n_back_edges', 'orig 2 != pred 1'), ('loss:n_natural_loops', 'orig 2 != pred 1'), ('loss:test_ops', 'per-opcode EQ 30!=31, TEST 4!=0')),
    ),
    "snr_novel.lua:main_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_novel.lua:main_1": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_novel.lua:main_10": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_novel.lua:main_13": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_novel.lua:main_2": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TEST 2!=0')),
    ),
    "snr_novel.lua:main_3": PanelPin(
        note="equivalent-transform (M6 LOSS_PINS per-proto verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'), ('loss:test_ops', 'per-opcode TEST 2!=0')),
    ),
    "snr_novel.lua:main_4": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_novel.lua:main_5": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_novel.lua:main_6": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_novel.lua:main_9": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_0_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_11": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_11_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_12": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_12_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_13": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_13_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_14_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_15": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_15_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_16": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_16_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_2": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_2_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_30": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_30_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_31": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_31_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_32": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_32_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_33_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_34": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_34_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_35": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_35_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_36": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_36_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_37_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_3_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_40": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_40_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_41": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_41_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_42_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_43": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_43_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_44": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_44_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_45": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_45_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_46": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_46_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_47": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_53": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_53_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_55": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_55_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_56": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_56_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_57": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_57_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_58": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_58_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_6": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_6_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s2_10_s.lua:main_7_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_0_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_10": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_10_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_11": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_1_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_2_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_34_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_35": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_35_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_36": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_36_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_37": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_37_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_38_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_3_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_4": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_41": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_41_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_42": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_43": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_43_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_44": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_44_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_45": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_45_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_46": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_46_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_47": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_47_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_48": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_48_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_4_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_50": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_50_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_51_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_52": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_52_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_53": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_53_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_54_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_55": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_55_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_56": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_56_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_59": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_6": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_6_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_8": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s3_10_s.lua:main_9": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_0_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_12": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_12_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_13": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_1_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_2": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_29": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_29_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_2_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_3": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_31_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_32": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_32_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_33": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_33_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_35": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_35_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_36_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_37": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_37_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_39": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_39_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_3_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_4": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_40_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_42": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_42_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_43": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_47_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_48": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_48_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_4_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_5": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_51": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_51_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_52_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_53": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_53_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_55": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_55_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_56": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_56_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_5_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_6_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_8": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_8_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s4_10_s.lua:main_9_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_11": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_13": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_15": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_16": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_2": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_21": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_22": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_26": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_27": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_28": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_29": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_2_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_3": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_30": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_34": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_37": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_37_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_38": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_38_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_39": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_39_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_3_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_4": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_40": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_40_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_42": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_43": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_44": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s5_10_s.lua:main_45": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s7_10_f.lua:main_0": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, opcode_counts, opcode_family_counts'),),
    ),
    "snr_s7_10_f.lua:main_52": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_all, opcode_counts, opcode_family_counts'),),
    ),
    "snr_story_main.lua:main_1": PanelPin(
        note="equivalent-transform (M6 fingerprint queue, per-file verdict)",
        evidence=(('fingerprint', 'differing field(s): code_len, cfg_reachable, opcode_counts, opcode_family_counts'),),
    ),
}


def write_panel(scan: dict[str, dict[str, PanelResult]], path: Path) -> None:
    """Serialize a scan to `path` as the committed observation artifact:
    per file, per proto -- `"pass"` | `{"pinned": <note>}` |
    `{"unpinned": {family: evidence}}`. Deterministic (sorted keys,
    `indent=1`, ASCII-only -- `PanelResult` already guarantees ASCII
    evidence)."""
    path.write_bytes(panel_bytes(scan))


def panel_bytes(scan: dict[str, dict[str, PanelResult]]) -> bytes:
    """The canonical serialization `write_panel` commits (and the fixed-point
    gate byte-compares)."""
    import json

    verdicts: dict[str, dict[str, object]] = {}
    for name, protos in scan.items():
        row: dict[str, object] = {}
        for proto_path, res in protos.items():
            key = f"{name}:{proto_path}"
            if not res.diffs:
                row[proto_path] = "pass"
            elif key in PANEL_PINS:
                row[proto_path] = {"pinned": PANEL_PINS[key].note}
            else:
                row[proto_path] = {"unpinned": dict(res.diffs)}
        verdicts[name] = row
    return (json.dumps(verdicts, indent=1, sort_keys=True,
                       ensure_ascii=True) + "\n").encode()


def pin_evidence() -> dict[str, tuple]:
    """`PANEL_PINS` projected to the evidence-tuple form `adjudicate_pins`
    compares (the `loss_sweep.pin_evidence` precedent)."""
    return {k: p.evidence for k, p in PANEL_PINS.items()}


if __name__ == "__main__":
    raise SystemExit(main())

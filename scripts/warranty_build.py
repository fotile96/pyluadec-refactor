#!/usr/bin/env python3
"""Warranty generator -- M7 task 11 (spec §6): the selection rule, and the
two committed artifacts it produces, ``corpus/warranty.jsonl`` and
``corpus/final/`` (229 files).

Per file, both sides are graded and a pure function picks the winner:

* **ours** -- ``(t_min, "id")`` from ``corpus/ledger.jsonl`` (``level`` +
  ``occurrences[].shipped`` through ``predrecert.t_grade``). Factor E is
  identity by construction: our text's source bytecode IS the original.
* **pred** -- ``(t_min, e_min, unpinned)``. T grades come from
  ``predrecert.recert_bytes`` over the pred side's text (the REPAIRED text
  for the five ``corpus/pred_repairs/`` files -- provenance vocabulary
  ``pred_repaired-*`` -- upstream text otherwise). E grades come from the
  committed panel observation (``corpus/observation/panel.json``, task 4):
  ``panel-pass`` / ``panel-pinned`` / ``panel-unpinned`` (disqualifying),
  with ``wm`` replacing the grade of exactly the six repaired protos --
  their panel.json rows describe the UPSTREAM divergence the M6 repairs
  addressed, not the repaired text; Wm (instruction-level walkthrough +
  runtime driver validation, ``corpus/pred_repairs/README.md`` ### 1-6) is
  stronger Factor-E evidence than a clean panel (spec §2, the glm reorder
  adoption), so ``id > wm > panel-pass > panel-pinned``.

Selection (``select``, spec §6 verbatim): eligibility -- ``panel-unpinned >
0`` disqualifies the pred side, a side with no grade is ineligible (pred
text that fails to compile); winner -- lexicographic on ``(T min, E min)``
with ``T3 > T2 > T-``; tie goes to ours (maintainability, one style). No
eligible side raises :class:`SelectionError` and the generator refuses to
write, naming the file.

**Why the ``*-verbatim`` vocabulary is structurally empty here.** An
ungradable pred side is ineligible, so a pred side that WINS always has a
``RecertOutcome`` whose ``source`` ships (``*-recert``); and a pred side
whose recert falls to whole-file fallback grades ``t_min = "T-"``, which
loses to ours' ``E = id`` on the tie before E is even reached. The plan's
file-level emission rule therefore never reaches ``*-verbatim`` on this
corpus -- recorded rather than papered over, and the report names the
residue as empty for this reason.

**The standing pin-table opcode check** (spec §7, absorbing M7 agenda 6's
routed item): before writing anything, every ``O<n> OPNAME`` / ``P<n>
OPNAME`` pair in ``PRED_PINS`` and ``LOSS_PINS`` notes is decoded at
1-based pc ``n`` in the resolved proto of the respective corpus (O ->
original, P -> pred). Proto resolution: a ``main_X:`` marker inside the
note switches context from that point on; the initial context is the LOSS
pin's own key (``<file>:<proto>``) or, for file-keyed PRED pins, the
leading ``main_X code=`` of the evidence tuple. A violation is a finding,
not a verdict: :class:`PinOpcodeError` aborts the run naming every bad
pair. Measured at this task's tree: 62 pairs, all hold.

Red line: this module emits committed artifacts but never puts corpus
bytes into diagnostics -- violation messages are side/pc/opcode/proto-path
only; the final/ texts are the selected side's decompiler output verbatim.

**One symbol, two guarantees (recorded limitation, task 12).** ``T-`` in
``warranty.jsonl`` means different things per side: OUR ``T-`` is the M2
floor -- the fallback state machine, semantically exact by construction
(38/38 opcode differential tests), compileable, and covered by the
L1.5/L1.75 probes -- while PRED ``T-`` means "no positive verification at
all". The schema does not distinguish them (a spec §2 consequence,
faithfully implemented); a reader inferring "no evidence" from our 64
``{"t": "T-", "e": "id"}`` occurrences would understate the strongest
constructive guarantee this project ships. Splitting the symbol is an M8
schema candidate, recorded in the milestone close-out, not done here --
it would churn the committed artifact without moving any selection.

**Job conditions** (the out-of-suite four -- full generation is a job, the
suite keeps only ``tests/test_warranty.py``'s selection-rule and
fixed-point arms): home = this script; trigger = **any ledger, panel or
recert movement** (i.e. before committing a change that moves
``corpus/ledger.jsonl`` or ``corpus/observation/panel.json``, or on any
``sir/``/``express/``/``emit/``/``structure/`` change that could) **and at
milestone close**; one command = the ``--all`` invocation below; the last
run's numbers live in ``docs/reports/m7-warranty.md`` §3. Cost basis
(measured 2026-08-16): linear in files -- one ``decompile_file`` + one
``recert_bytes`` per file, oracle compiles memoized.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cross_corpus import PRED_PINS  # noqa: E402
from loss_sweep import LOSS_PINS  # noqa: E402

from pyluadec.ingest import load_file  # noqa: E402
from pyluadec.lift.opcodes import Op, decode  # noqa: E402
from pyluadec.oracle import LuaCompileError, compile_source  # noqa: E402
from pyluadec.pipeline import decompile_chunk, walk_proto_paths  # noqa: E402
from pyluadec.structure import proposals  # noqa: E402
from pyluadec.predcorpus import load_pred_proto  # noqa: E402
from pyluadec.predrecert import recert_bytes, t_grade  # noqa: E402
from pyluadec.verify.certify import carries_debug  # noqa: E402
from pyluadec.verify.ledger import oracle_version  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The selection vocabulary (committed artifact field ``selection``).
PROVENANCE = ("ours", "pred-recert", "pred-verbatim",
              "pred_repaired-recert", "pred_repaired-verbatim")

#: Best-to-worst orders of the two factors (spec §2/§6).
T_ORDER = ("T3", "T2", "T-")
E_ORDER = ("id", "wm", "panel-pass", "panel-pinned", "panel-unpinned")

#: The five repaired pred files -> the six Wm protos (M6 defects;
#: ``corpus/pred_repairs/README.md`` headings ### 1-6). The pred side of
#: these files is the REPAIRED text; Wm replaces the Factor-E grade of
#: exactly these protos (see module docstring).
REPAIRED: dict[str, tuple[str, ...]] = {
    "snr_music.lua": ("main_3",),                       # defect 1
    "snr_common.lua": ("main_76_2", "main_75"),         # defects 2, 6
    "snr_mainmenu.lua": ("main_7",),                    # defect 3
    "snr_graphic.lua": ("main_4",),                     # defect 4
    "snr_memory.lua": ("main_4",),                      # defect 5
}


class SelectionError(Exception):
    """No eligible side for a file (spec §6 step 4) -- must not occur at
    close; the generator refuses to write, naming the file."""


class PinOpcodeError(Exception):
    """A pin-table ``O<n> OPNAME`` / ``P<n> OPNAME`` pair that does not
    decode to the named opcode -- the generator refuses to write. The
    exact defect class the re-base fixed (a 0-based pc copied from prose),
    now a standing gate instead of a one-off (M7 agenda 6)."""


def select(ours: tuple[str, str] | None,
           pred: tuple[str, str, int] | None) -> str:
    """The selection rule as a pure function (spec §6 verbatim).

    ``ours`` is ``(t_min, e_min)``; ``pred`` is ``(t_min, e_min,
    unpinned_count)``. Either side may be ``None`` (no grade ->
    ineligible); a pred side with ``unpinned > 0`` is likewise
    ineligible. Returns ``"ours"`` | ``"pred"``; ties go to ours.

    Ours' ``e_min`` is ``"id"`` **by construction** (spec §2: our text's
    source bytecode IS the original) -- `build_all` passes the constant,
    and that is the correct shape; what this function does NOT do is
    special-case the ours side internally, so the rule stays total if a
    caller ever grades ours differently. Exhaustively (task 12, pinned in
    `tests/test_m7_exit.py`): over all 36 grade combinations with ours at
    ``e = id``, pred wins in exactly 12 -- every one a STRICT Factor-T
    advantage. Factor E never decides a selection; its entire decisive
    role is the ``unpinned > 0`` eligibility veto.
    """
    pred_eligible = pred is not None and pred[2] == 0
    ours_eligible = ours is not None
    if not ours_eligible and not pred_eligible:
        raise SelectionError("no eligible side")
    if not pred_eligible:
        return "ours"
    if not ours_eligible:
        return "pred"
    for o, p, order in ((ours[0], pred[0], T_ORDER), (ours[1], pred[1], E_ORDER)):
        if order.index(o) != order.index(p):
            return "ours" if order.index(o) < order.index(p) else "pred"
    return "ours"


# ---------------------------------------------------------------------------
# The standing pin-table opcode check (spec §7).

_OPNAMES = sorted((o.name for o in Op), key=len, reverse=True)
_PAIR_RE = re.compile(r"\b([OP])(\d+)\s+(" + "|".join(_OPNAMES) + r")\b")
_PROTO_MARKER_RE = re.compile(r"\b(main(?:_\d+)*)\s*:")
_EVIDENCE_LEAD_RE = re.compile(r"^\s*(main(?:_\d+)*)\s+code=")


def _pairs_in_context(note: str, start_proto: str | None):
    """Yield ``(proto, side, pc, opname)`` for every `O<n> OPNAME` /
    `P<n> OPNAME` pair, resolving proto context left-to-right: a
    ``main_X:`` marker switches it, the caller's initial context otherwise
    (the LOSS pin key's proto, or the evidence tuple's leading proto)."""
    current = start_proto
    for tok in re.finditer(_PROTO_MARKER_RE.pattern + "|" + _PAIR_RE.pattern,
                           note):
        if tok.group(1):
            current = tok.group(1)
        else:
            yield current, tok.group(2), int(tok.group(3)), tok.group(4)


def pin_opcode_violations(corpus_dir: Path, pred_dir: Path, *,
                          pred_pins=None, loss_pins=None) -> list[str]:
    """Every pin-table opcode pair that fails to decode, as ASCII
    diagnostics (side/pc/opcode/proto-path only). Empty on a clean table."""
    pred_pins = PRED_PINS if pred_pins is None else pred_pins
    loss_pins = LOSS_PINS if loss_pins is None else loss_pins
    orig_protos: dict[str, dict[str, object]] = {}
    pred_protos: dict[str, dict[str, object]] = {}

    def table_for(side: str, name: str):
        cache = orig_protos if side == "O" else pred_protos
        if name not in cache:
            root = load_file(Path(corpus_dir) / name)
            if side == "P":
                root = load_pred_proto(Path(pred_dir), name,
                                       strip=not carries_debug(root))
            d: dict[str, object] = {}
            walk_proto_paths("main", root, d)
            cache[name] = d
        return cache[name]

    def opcode_at(side: str, name: str, proto: str, pc: int) -> str | None:
        protos = table_for(side, name)
        if proto not in protos:
            return None
        code = protos[proto].code
        if not (1 <= pc <= len(code)):
            return None
        return decode(code[pc - 1], pc).op.name

    out: list[str] = []
    for arm, table in pred_pins.items():
        for name, pin in table.items():
            start = None
            for ev in pin.evidence:
                m = _EVIDENCE_LEAD_RE.match(ev)
                if m:
                    start = m.group(1)
            for proto, side, pc, op in _pairs_in_context(pin.note, start):
                if proto is None:
                    out.append(f"PRED_PINS[{arm}][{name}]: {side}{pc} {op} "
                               "has no proto context to resolve")
                    continue
                actual = opcode_at(side, name, proto, pc)
                if actual != op:
                    out.append(f"PRED_PINS[{arm}][{name}]: {name}:{proto} "
                               f"{side}{pc} {op} != {actual}")
    for key, pin in loss_pins.items():
        name, proto0 = key.rsplit(":", 1)
        for proto, side, pc, op in _pairs_in_context(pin.note, proto0):
            actual = opcode_at(side, name, proto, pc)
            if actual != op:
                out.append(f"LOSS_PINS[{key}]: {name}:{proto} "
                           f"{side}{pc} {op} != {actual}")
    return out


# ---------------------------------------------------------------------------
# The generator.

def _worst(grades) -> str:
    return max(grades, key=lambda g: T_ORDER.index(g) if g in T_ORDER
               else E_ORDER.index(g))


def _hist(grades, order) -> dict[str, int]:
    counts = {g: 0 for g in order}
    for g in grades:
        counts[g] += 1
    return {g: n for g, n in counts.items() if n}


def _read_ledger_by_file() -> dict[str, dict[str, dict]]:
    """file -> proto_path -> {level, shipped, l2} from the committed ledger."""
    rows = [json.loads(line) for line
            in (REPO_ROOT / "corpus" / "ledger.jsonl").read_text().splitlines()
            if line.strip()]
    by_file: dict[str, dict[str, dict]] = {}
    for row in rows:
        for occ in row["occurrences"]:
            by_file.setdefault(occ["file"], {})[occ["proto_path"]] = {
                "level": row["level"], "shipped": occ["shipped"],
                "hybrid": occ.get("hybrid", False), "l2": occ.get("l2")}
    return by_file


def build_all(corpus_dir: Path, pred_dir: Path):
    """Regenerate both artifacts in memory: ``(warranty_bytes, finals,
    summary)``. ``finals`` maps file name -> the selected side's text
    (bytes). Raises :class:`PinOpcodeError` / :class:`SelectionError` /
    ``AssertionError`` (a coverage or tree-correspondence break is a
    finding, not a verdict) before anything is written."""
    corpus_dir, pred_dir = Path(corpus_dir), Path(pred_dir)

    violations = pin_opcode_violations(corpus_dir, pred_dir)
    if violations:
        raise PinOpcodeError("; ".join(violations))

    panel = json.loads(
        (REPO_ROOT / "corpus" / "observation" / "panel.json").read_text())
    ledger = _read_ledger_by_file()
    orc = oracle_version()

    names = sorted(p.name for p in corpus_dir.glob("*.lua"))
    rows: list[dict] = []
    finals: dict[str, bytes] = {}
    summary = {"files": len(names), "selections": {},
               "hybrid_files": [], "ours_t": {}}
    hybrid_flags: dict[str, bool] = {}
    for name in names:
        orig_path = corpus_dir / name
        protos: dict[str, object] = {}
        walk_proto_paths("main", load_file(orig_path), protos)
        paths = list(protos)

        ours_led = ledger[name]
        assert set(ours_led) == set(paths), f"{name}: ledger coverage break"
        for p, occ in ours_led.items():
            if occ.get("hybrid"):
                hybrid_flags[name] = True

        ours_result = decompile_chunk(load_file(orig_path),
                                      proposals.for_file(name))
        # Proposal-shipped text IS certified (the chunk's whole-tree round),
        # so Factor T grades it by level -- the shipped-first ladder's T-
        # arm exists for UNCERTIFIED fallback text, which this is not. The
        # M7 task-2/11 shipped-first history is exactly why this mapping is
        # written out instead of folded into t_grade: the distinction is
        # provenance, not verdict.
        ours_t = {p: t_grade(ours_led[p]["level"],
                             ours_led[p]["shipped"] == "fallback")
                  for p in paths}
        ours_grade = (_worst(ours_t.values()), "id")

        pred_text = ((REPO_ROOT / "corpus" / "pred_repairs" / name).read_bytes()
                     if name in REPAIRED else (pred_dir / name).read_bytes())
        try:
            recert = recert_bytes(pred_text)
        except LuaCompileError:
            recert = None

        if recert is None:
            pred_grade = None
            pred_obj = None
        else:
            assert set(recert.t_grades) == set(paths), \
                f"{name}: pred tree correspondence break"
            e_grades: dict[str, str] = {}
            unpinned = 0
            for p in paths:
                if p in REPAIRED.get(name, ()):
                    e_grades[p] = "wm"
                    continue
                verdict = panel[name][p]
                if verdict == "pass":
                    e_grades[p] = "panel-pass"
                elif "pinned" in verdict:
                    e_grades[p] = "panel-pinned"
                else:
                    e_grades[p] = "panel-unpinned"
                    unpinned += 1
            pred_grade = (_worst(recert.t_grades.values()),
                          _worst(e_grades.values()), unpinned)
            pred_obj = {
                "t_min": pred_grade[0],
                "t_hist": _hist(recert.t_grades.values(), T_ORDER),
                "e_min": pred_grade[1],
                "e_hist": _hist(e_grades.values(), E_ORDER),
                "unpinned": unpinned,
                "wm": sorted(REPAIRED.get(name, ())),
            }

        side = select(ours_grade, pred_grade)
        if side == "ours":
            selection = "ours"
            text = ours_result.source
            occurrences = [{"proto_path": p, "t": ours_t[p], "e": "id",
                            "l2": ours_led[p]["l2"]} for p in paths]
        else:
            # An eligible pred side always has a recert outcome (no grade
            # is ineligible), so *-verbatim is structurally unreachable --
            # see the module docstring; the assert documents the invariant.
            assert recert is not None
            selection = ("pred_repaired-" if name in REPAIRED else "pred-"
                         ) + "recert"
            text = recert.source
            occurrences = [{"proto_path": p, "t": recert.t_grades[p],
                            "e": e_grades[p], "l2": None} for p in paths]

        finals[name] = text
        # Footprint (spec §3 / M8 task 1): recompiled-bytecode size of the
        # SHIPPED text over the original file, both stripped, whole-file
        # bytes incl. the 12-byte header. Rounded to 4 decimals -- Python's
        # round on an IEEE quotient of two ints is deterministic across
        # platforms, and the fixed-point gate compares the recorded value.
        # An L3 file recompiles field-exact => byte-exact => exactly 1.0;
        # the M8 campaign-start census measured the non-1.0 set to be
        # exactly the fallback carriers (7 files).
        rows.append({
            "file": name,
            "selection": selection,
            "ours": {"t_min": ours_grade[0],
                     "t_hist": _hist(ours_t.values(), T_ORDER)},
            "pred": pred_obj,
            "footprint_ratio": round(
                len(compile_source(text, strip=True))
                / orig_path.stat().st_size, 4),
            "occurrences": occurrences,
            "oracle": orc,
        })

    summary["hybrid_files"] = sorted(hybrid_flags)
    for row in rows:
        summary["selections"][row["selection"]] = \
            summary["selections"].get(row["selection"], 0) + 1
    warranty_bytes = "".join(
        json.dumps(row) + "\n" for row in rows).encode()
    return warranty_bytes, finals, summary


def footprint_ratios() -> dict[str, float]:
    """`file -> footprint_ratio` read from the COMMITTED warranty artifact
    (no compiling at test time; the generator records the value). The
    suite's footprint gate reads this."""
    rows = [json.loads(line) for line
            in (REPO_ROOT / "corpus" / "warranty.jsonl").read_text()
            .splitlines() if line.strip()]
    return {r["file"]: r["footprint_ratio"] for r in rows}


def main(argv: list[str] | None = None) -> int:
    """CLI: ``--all`` regenerates and WRITES ``corpus/warranty.jsonl`` and
    ``corpus/final/`` (refusing on any pin-opcode violation, selection
    error, or coverage break), then prints the selection histogram."""
    import argparse

    ap = argparse.ArgumentParser(prog="warranty_build")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)
    if not args.all:
        ap.error("need --all")
        return 1  # unreachable
    corpus = Path(os.environ.get("PYLUADEC_CORPUS_DIR", ""))
    pred = Path(os.environ.get("PYLUADEC_PRED_CORPUS_DIR", ""))
    if not corpus.is_dir() or not pred.is_dir():
        print("both corpus env vars must be set for --all", file=sys.stderr)
        return 1
    t0 = time.monotonic()
    try:
        warranty, finals, summary = build_all(corpus, pred)
    except PinOpcodeError as e:
        print(f"warranty: PIN-TABLE OPCODE CHECK FAILED -- {e}",
              file=sys.stderr)
        return 1
    except SelectionError as e:
        print(f"warranty: NO ELIGIBLE SIDE -- {e}", file=sys.stderr)
        return 1
    out_root = REPO_ROOT / "corpus"
    (out_root / "warranty.jsonl").write_bytes(warranty)
    final_dir = out_root / "final"
    final_dir.mkdir(exist_ok=True)
    for stale in final_dir.glob("*.lua"):
        if stale.name not in finals:
            stale.unlink()
    for name, text in finals.items():
        (final_dir / name).write_bytes(text)
    dt = time.monotonic() - t0
    hist = " ".join(f"{k}={v}" for k, v in sorted(
        summary["selections"].items()))
    print(f"warranty: {summary['files']} files ({dt:.2f}s): {hist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

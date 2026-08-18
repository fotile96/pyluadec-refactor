"""Harvest the old project's readable-rename surface into name_map.jsonl.

The old localization chain renamed its decompiled output in several passes
(``/Users/fotile96/pyluadec/post_process/tools/rename_*.py``); the final
naming surface lives in the TEXT of
``/Users/fotile96/pyluadec/post_process/stage1_output/`` (the apply reports
are cross-validation only -- measured 2026-08-18: three of the crd-prefix
report's claimed targets do not exist in the final text, see
``docs/reports/m8-naming-t0.md``).  This generator ports that surface onto
OUR output coordinates and refuses to write anything it cannot port
unambiguously.

The alignment construction (why it is sound although the old text never
recompiles instruction-identical -- M6 measured 3903 substantive code
mismatches over 229 files, so register numbers do NOT correspond):

* **Function names** are anchored on the CLOSURE instruction's Bx operand,
  which IS the subproto index on both sides.  For proto path ``P`` the
  original's CLOSURE with ``Bx == j`` targets register ``r`` (our
  ``l<depth>_<r>``); the old compile's CLOSURE with the same ``Bx == j``
  targets its own register, and the locvar live at that pc in that slot
  carries the old name.  Same ``j`` (M6 tree parity: identical path sets on
  all 229 files) means same function, so ``(file, P, r) -> name`` needs no
  code equality at all.
* **Parameter names** are positional: numparams parity is 229/229 files
  (measured), and params occupy slots ``0..numparams-1`` in declaration
  order on both sides.

Excluded from the table by the partner's decision (2026-08-18, handoff
``docs/reports/m8-handoff-naming-alignment.md`` decision 1): the old
project's own auto-names -- ``v\\d+`` / ``p\\d+`` locals and params,
``i\\d+`` / ``g\\d+`` iterator temps, ``arg``, and the compiler's
``(for ...)`` internals.  Our ``l<depth>_<reg>`` scheme stays for those.
The old text's ``local NAME`` inside a function that shares its parent's
assigned name is the old decompiler's self-reference materialization; our
printer expresses the same capture via ``local function`` sugar and upvalue
name threading, so those names arrive for free with the parent's entry
(389 occurrences, none of them an independent table row).

Refusals (exit 1, nothing written): proto-tree mismatch, numparams
mismatch, two different names mapped to one ``(file, path, reg)``, a name
that is not a valid Lua identifier, a keyword, or collides with the
printer's synthesized ``l<k>_<r>`` / ``u<k>`` spellings, or a function-name
entry whose register our printer does not declare as a local (inlined into
a constructor -- the name would never print).

Usage:
    PYLUADEC_CORPUS_DIR=<229-file bytecode corpus> \
    [PYLUADEC_STAGE1_DIR=<old renamed sources>] \
    uv run python corpus/naming/harvest_naming.py [--check]

``--check`` regenerates the table in memory and byte-compares it against
the committed ``name_map.jsonl``; any drift exits 1 naming the file.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pyluadec import ingest, oracle                      # noqa: E402
from pyluadec.lift import LUA_KEYWORDS                   # noqa: E402
from pyluadec.lift.lift import lift_proto                # noqa: E402
from pyluadec.pipeline import walk_proto_paths           # noqa: E402
from pyluadec.express.names import classify_registers    # noqa: E402

#: The 6 M6-confirmed real-bug protos plus the one path-level
#: ``intentional-edit`` (``docs/reports/m6-cross-corpus.md`` §3.1/§3.2).
#: Old translation units anchored on these protos sat on wrong code; the
#: migration guide carries them as a separate section (P4).
DEFECT_ZONES: tuple[tuple[str, str], ...] = (
    ("snr_music.lua", "main_3"),
    ("snr_common.lua", "main_76_2"),
    ("snr_mainmenu.lua", "main_7"),
    ("snr_graphic.lua", "main_4"),
    ("snr_memory.lua", "main_4"),
    ("snr_common.lua", "main_75"),
    ("snr_common.lua", "main_83"),
)

#: The propose-and-certify channel's manifest
#: (``src/pyluadec/structure/proposals.py``).  Entries inside these
#: subtrees ship the hand-written body, whose internal naming is the
#: proposal author's, not the table's.
PROPOSAL_SITES: tuple[tuple[str, str], ...] = (
    ("snr_common.lua", "main_24"),
    ("snr_common.lua", "main_25"),
    ("snr_common.lua", "main_25_4"),
    ("snr_common.lua", "main_71"),
    ("snr_common.lua", "main_74_18"),
    ("snr_common.lua", "main_76_2"),
    ("snr_common.lua", "main_77"),
    ("snr_graphic.lua", "main_4"),
    ("snr_mainmenu.lua", "main_7"),
    ("snr_story_main.lua", "main_3"),
)

#: The old decompiler's / renamers' non-semantic name spellings.  Anything
#: else found on a portable slot is a readable name and goes in the table.
_RESDUAL = re.compile(r"v\d+$|p\d+$|[ig]\d+$|^arg$|^\(for ")

_SYNTH = re.compile(r"l\d+_\d+$|u\d+$")


def _is_readable(name: str) -> bool:
    return _RESDUAL.match(name) is None


def _closures(code: tuple[int, ...]) -> list[tuple[int, int, int]]:
    """``(pc, target register A, subproto index Bx)`` for every CLOSURE."""
    return [(pc, (w >> 6) & 0xFF, w >> 14)
            for pc, w in enumerate(code) if (w & 0x3F) == 36]


def _locvar_name_at(proto: ingest.proto.Proto, pc: int, slot: int) -> str | None:
    """The locvar name occupying ``slot`` at ``pc``: the ``slot``-th locvar
    (dump order = declaration order) whose ``[startpc, endpc)`` covers ``pc``
    -- the same counting ``luaF_getlocalname`` does."""
    live = [lv for lv in proto.locvars if lv.startpc <= pc < lv.endpc]
    if slot < len(live) and live[slot].name is not None:
        return live[slot].name.decode()
    return None


def _valid_name(name: str) -> str | None:
    """``None`` when usable, else the reason it is not."""
    if not name.isidentifier():
        return "not an identifier"
    if name in LUA_KEYWORDS:
        return "Lua keyword"
    if _SYNTH.match(name):
        return "collides with a synthesized printer name"
    if name.startswith("__pld_"):
        return "reserved state-machine prefix"
    return None


def harvest(corpus_dir: Path, stage1_dir: Path) -> tuple[list[dict], dict]:
    """The table (sorted, one dict per row) and the measurement report.

    Raises ``SystemExit(1)`` with a named violation on any refusal
    condition; the caller must not write the table when it fires.
    """
    rows: list[dict] = []
    seen: dict[tuple[str, str, int], str] = {}
    report = {"files": 0, "fn_ported": 0, "param_ported": 0,
              "fn_unprinted": 0, "old_unnamed_or_residual": 0,
              "param_residual": 0, "flagged": 0}

    for f in sorted(corpus_dir.glob("*.lua")):
        orig = ingest.load_file(f)
        try:
            old = ingest.load_bytes(
                oracle.compile_source((stage1_dir / f.name).read_bytes(),
                                      strip=False),
                chunkname="@" + f.name)
        except oracle.LuaCompileError as exc:
            sys.exit(f"REFUSED: {f.name} does not compile: {exc}")
        po: dict[str, ingest.proto.Proto] = {}
        pu: dict[str, ingest.proto.Proto] = {}
        walk_proto_paths("main", orig, po)
        walk_proto_paths("main", old, pu)
        if set(po) != set(pu):
            sys.exit(f"REFUSED: {f.name} proto-tree paths differ from the "
                     f"old compile ({len(set(po) ^ set(pu))} paths)")
        report["files"] += 1

        ours_locals: dict[str, frozenset[int]] = {}
        for path, p in po.items():
            rc = classify_registers(lift_proto(p))
            ours_locals[path] = rc.locals | rc.loop_vars

        for path in po:
            a, b = po[path], pu[path]
            if a.numparams != b.numparams:
                sys.exit(f"REFUSED: {f.name}:{path} numparams "
                         f"{a.numparams} vs old {b.numparams}")
            flags: list[str] = []
            if any(fname == f.name and (path == z or path.startswith(z + "_"))
                   for fname, z in DEFECT_ZONES):
                flags.append("defect-zone")
            if any(fname == f.name and (path == z or path.startswith(z + "_"))
                   for fname, z in PROPOSAL_SITES):
                flags.append("proposal-site")
            ours_closure_reg = {j: r for _, r, j in _closures(a.code)}
            for pc, r_old, j in _closures(b.code):
                name = _locvar_name_at(b, pc, r_old)
                if name is None or not _is_readable(name):
                    report["old_unnamed_or_residual"] += 1
                    continue
                if j not in ours_closure_reg:
                    sys.exit(f"REFUSED: {f.name}:{path} old CLOSURE Bx={j} "
                             f"has no original counterpart")
                r_ours = ours_closure_reg[j]
                if r_ours not in ours_locals[path]:
                    # Inlined into a constructor or call: the printer never
                    # spells this register as a name, so the port has no
                    # landing site.  Counted, not refused (our
                    # reconstruction legitimately eliminated it).
                    report["fn_unprinted"] += 1
                    continue
                key = (f.name, path, r_ours)
                if key in seen and seen[key] != name:
                    sys.exit(f"REFUSED: {f.name}:{path} reg {r_ours} mapped "
                             f"to both {seen[key]!r} and {name!r}")
                bad = _valid_name(name)
                if bad:
                    sys.exit(f"REFUSED: {f.name}:{path} name {name!r}: {bad}")
                seen[key] = name
                rows.append({"file": f.name, "path": path, "reg": r_ours,
                             "name": name, "kind": "function",
                             "anchor": j, "flags": flags})
                report["fn_ported"] += 1
                report["flagged"] += bool(flags)
            for i in range(b.numparams):
                name = _locvar_name_at(b, 0, i)
                if name is None or not _is_readable(name):
                    report["param_residual"] += 1
                    continue
                key = (f.name, path, i)
                if key in seen and seen[key] != name:
                    sys.exit(f"REFUSED: {f.name}:{path} param {i} mapped "
                             f"to both {seen[key]!r} and {name!r}")
                bad = _valid_name(name)
                if bad:
                    sys.exit(f"REFUSED: {f.name}:{path} param name "
                             f"{name!r}: {bad}")
                seen[key] = name
                rows.append({"file": f.name, "path": path, "reg": i,
                             "name": name, "kind": "param",
                             "anchor": i, "flags": flags})
                report["param_ported"] += 1
                report["flagged"] += bool(flags)

    rows.sort(key=lambda r: (r["file"], r["path"], r["reg"]))
    return rows, report


def render(rows: list[dict]) -> bytes:
    out = bytearray()
    for r in rows:
        out += json.dumps(r, sort_keys=True,
                          ensure_ascii=True).encode("ascii") + b"\n"
    return bytes(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="byte-compare the regeneration against the "
                         "committed table instead of writing it")
    args = ap.parse_args(argv)

    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not corpus or not Path(corpus).is_dir():
        print("PYLUADEC_CORPUS_DIR is unset or not a directory", file=sys.stderr)
        return 2
    stage1 = Path(os.environ.get(
        "PYLUADEC_STAGE1_DIR",
        "/Users/fotile96/pyluadec/post_process/stage1_output"))
    if not stage1.is_dir():
        print(f"PYLUADEC_STAGE1_DIR ({stage1}) is not a directory",
              file=sys.stderr)
        return 2

    rows, report = harvest(Path(corpus), stage1)
    blob = render(rows)
    target = Path(__file__).resolve().parent / "name_map.jsonl"

    if args.check:
        current = target.read_bytes() if target.is_file() else b""
        if blob != current:
            print(f"NAME MAP DRIFT: {target} does not match a fresh "
                  f"harvest ({len(current)} bytes committed, {len(blob)} "
                  f"regenerated); rerun without --check and review the diff")
            return 1
        print(f"name_map.jsonl: fixed point ({len(rows)} rows)")

    print(f"files: {report['files']}")
    print(f"function names ported: {report['fn_ported']} "
          f"(+{report['fn_unprinted']} unprintable on our side, "
          f"+{report['old_unnamed_or_residual']} old-side residual/unnamed "
          f"closures)")
    print(f"params ported: {report['param_ported']} "
          f"(+{report['param_residual']} residual params)")
    print(f"flagged rows: {report['flagged']}")

    if not args.check:
        target.write_bytes(blob)
        print(f"wrote {target} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

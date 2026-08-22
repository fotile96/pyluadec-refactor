"""Build the translation-unit ID map (T2): old unit id -> new unit id +
our coordinates + defect-zone flags.

The old translation assets live in ``post_process/translation_ir/`` as one
directory per unit, named by the OLD readable function name (the renamers'
output) -- e.g. ``card_100_s6s_60_sel_intro/``.  Because the naming
alignment (T1) reproduces those names verbatim on our output, the NEW unit
id is the SAME STRING; the value this map adds is the coordinate
(``file``, ``proto_path`` -- and ``reg`` for local-function units) on OUR
side, plus the P4 flags the downstream has to respect before back-filling
old translations onto fixed code.

Unit name shapes (measured 2026-08-18: 1003 dirs = 319 card_* + 498
scene_* + 186 file__main):

* readable-name units (817): looked up in ``name_map.jsonl`` by name.
* ``<file>__main`` units (186): the GLOBAL ``main`` assignment.  Located
  from the ORIGINAL instruction stream -- scan main's code for SETGLOBAL
  whose constant is ``main``, then walk back to the CLOSURE that fed that
  register; its Bx is the proto index (measured: exactly one per file,
  229 files scanned).  Old and new id are both ``<file>__main``.

Red lines: only DIRECTORY NAMES are read from ``translation_ir/`` -- the
``meta.json`` files inside carry game text and are never opened.  Nothing
in this script's diagnostics contains unit text content.

Usage:
    PYLUADEC_CORPUS_DIR=<229-file bytecode corpus> \
    [PYLUADEC_TRANSLATION_IR=<old unit dirs>] \
    uv run python corpus/naming/build_unit_map.py [--check]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from harvest_naming import DEFECT_ZONES                            # noqa: E402

from pyluadec import ingest                                        # noqa: E402

_DEFAULT_IR = Path("/Users/fotile96/pyluadec/post_process/translation_ir")


def _flags_for(file: str, path: str) -> list[str]:
    out = []
    for fname, zone in DEFECT_ZONES:
        if fname == file and (path == zone or path.startswith(zone + "_")):
            out.append("defect-zone")
    return out


def _locate_global_main(root: ingest.proto.Proto) -> int | None:
    """The subproto index of the closure assigned to the global ``main``
    (exactly one per corpus file, measured; ``None`` otherwise)."""
    for pc, w in enumerate(root.code):
        if (w & 0x3F) == 7:                      # SETGLOBAL iABx
            bx = w >> 14
            if root.constants[bx] == b"main":
                a = (w >> 6) & 0xFF
                for pc2 in range(pc, -1, -1):
                    w2 = root.code[pc2]
                    if (w2 & 0x3F) == 36 and ((w2 >> 6) & 0xFF) == a:
                        return w2 >> 14
    return None


def build(corpus_dir: Path, ir_dir: Path) -> tuple[list[dict], dict]:
    table = [json.loads(line) for line
             in (HERE / "name_map.jsonl").read_text(encoding="ascii")
             .splitlines()]
    by_name = {r["name"]: r for r in table if r["kind"] == "function"}

    units = sorted(p.name for p in ir_dir.iterdir() if p.is_dir())
    rows: list[dict] = []
    report = {"units": 0, "by_name": 0, "file_main": 0, "unmatched": 0,
              "flagged": 0}
    for unit in units:
        report["units"] += 1
        flags: list[str] = []
        if unit.endswith("__main"):
            stem = unit[:-len("__main")]
            fname = stem + ".lua"
            root = ingest.load_file(corpus_dir / fname)
            idx = _locate_global_main(root)
            if idx is None:
                sys.exit(f"REFUSED: {fname} has a {unit} unit but no "
                         f"SETGLOBAL 'main' in its bytecode")
            path = f"main_{idx}"
            rows.append({"old_id": unit, "new_id": unit, "file": fname,
                         "path": path, "reg": None,
                         "flags": _flags_for(fname, path)})
            report["file_main"] += 1
        elif unit in by_name:
            r = by_name[unit]
            rows.append({"old_id": unit, "new_id": r["name"],
                         "file": r["file"], "path": r["path"],
                         "reg": r["reg"],
                         "flags": _flags_for(r["file"], r["path"])})
            report["by_name"] += 1
        else:
            report["unmatched"] += 1
            rows.append({"old_id": unit, "new_id": None, "file": None,
                         "path": None, "reg": None, "flags": ["unmatched"]})
        if rows[-1]["flags"]:
            report["flagged"] += 1
    rows.sort(key=lambda r: (r["old_id"],))
    return rows, report


def render(rows: list[dict]) -> bytes:
    return b"".join(json.dumps(r, sort_keys=True,
                               ensure_ascii=True).encode("ascii") + b"\n"
                    for r in rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not corpus or not Path(corpus).is_dir():
        print("PYLUADEC_CORPUS_DIR is unset or not a directory",
             file=sys.stderr)
        return 2
    ir = Path(os.environ.get("PYLUADEC_TRANSLATION_IR", _DEFAULT_IR))
    if not ir.is_dir():
        print(f"translation_ir dir ({ir}) is missing", file=sys.stderr)
        return 2

    rows, report = build(Path(corpus), ir)
    blob = render(rows)
    target = HERE / "unit_map.jsonl"
    if args.check:
        current = target.read_bytes() if target.is_file() else b""
        if blob != current:
            print(f"UNIT MAP DRIFT: {target} does not match a fresh build "
                  f"({len(current)} vs {len(blob)} bytes)")
            return 1
        print(f"unit_map.jsonl: fixed point ({len(rows)} rows)")
    print(f"units: {report['units']} = {report['by_name']} name-anchored "
          f"+ {report['file_main']} file__main; "
          f"unmatched: {report['unmatched']}; flagged: {report['flagged']}")
    if report["unmatched"]:
        print("REFUSED: unmatched units present -- see rows flagged "
              "'unmatched'; adjudicate before shipping the map",
              file=sys.stderr)
        return 1
    if not args.check:
        target.write_bytes(blob)
        print(f"wrote {target} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""The naming-alignment table: ``(proto_path, register) -> readable name``
for the printer (M8 naming alignment).

Data: ``corpus/naming/name_map.jsonl``, generated whole-file by
``corpus/naming/harvest_naming.py`` from the old project's renamed output
(``post_process/stage1_output/``) -- same discipline as the proposals and
the ledger: nothing hand-edits a line, the committed file must be a fixed
point of the generator, and the generator refuses (exit 1, nothing written)
on any ambiguous port.  See that script's docstring for the alignment
construction and ``docs/reports/m8-naming-t0.md`` for the measured
portability numbers.

Consumption: the printer consults the table every place it would otherwise
synthesize ``l<depth>_<reg>`` and falls back to that spelling on a miss --
this module never rewrites emitted text.  Because names ride the ordinary
print path, the certification ladder already guards them: a rename that
changed name resolution (a local shadowing a referenced global flips
GETGLOBAL to MOVE, a keyword breaks the compile) changes the compiled
bytecode and is refused by the same whole-tree compare that certifies the
chunk, so a bad table degrades the ledger instead of shipping.

Red lines (CLAUDE.md) hold here as everywhere: the table itself contains
only identifiers (validated ASCII by the generator) and file names; no
game text passes through this module in either direction.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from pyluadec.lift import LUA_KEYWORDS

_REPO_ROOT = Path(__file__).resolve().parents[3]

#: One jsonl row per ported name.  Keys: file, path, reg, name, kind
#: ("function" | "param"), anchor (the CLOSURE Bx / param index it was
#: aligned on), flags (defect-zone / proposal-site; measured 0 today --
#: the readable surface and the 6 M6 defect protos do not intersect).

_DEFAULT_MAP = _REPO_ROOT / "corpus" / "naming" / "name_map.jsonl"

_cache: dict[str, dict[tuple[str, int], str]] | None = None


def map_path() -> Path:
    """Where the table lives.  ``PYLUADEC_NAMING_MAP`` overrides the
    repo-relative default (used by the tests to prove the loader actually
    reads this file)."""
    env = os.environ.get("PYLUADEC_NAMING_MAP")
    return Path(env) if env else _DEFAULT_MAP


def _valid_loaded_name(name: str) -> str | None:
    """``None`` when usable, else the reason -- the loader's own copy of the
    generator's gate, so a hand-edited or tampered table is refused at load
    time with the offender named instead of degrading a certification
    somewhere downstream. No ``re`` (this is ``src/``): the identifier and
    synthesized-name checks are spelled out by hand."""
    if not name or not name.isascii():
        return "not an ASCII identifier"
    if not (name[0].isalpha() or name[0] == "_"):
        return "not an identifier"
    if not all(c == "_" or c.isalnum() for c in name):
        return "not an identifier"
    if name in LUA_KEYWORDS:
        return "Lua keyword"
    if name.startswith("__pld_"):
        return "reserved state-machine prefix"
    if name.startswith(("l", "u")):
        stem = name[1:]
        if name[0] == "u" and stem.isdigit():
            return "collides with an upvalue spelling u<k>"
        head, sep, tail = stem.partition("_")
        if name[0] == "l" and sep and head.isdigit() and tail.isdigit():
            return "collides with a synthesized l<k>_<r>"
    return None


def _load() -> dict[str, dict[tuple[str, int], str]]:
    global _cache
    if _cache is not None:
        return _cache
    out: dict[str, dict[tuple[str, int], str]] = {}
    p = map_path()
    if not p.is_file():
        raise FileNotFoundError(
            f"naming table {p} is missing (regenerate with "
            f"`corpus/naming/harvest_naming.py`)")
    with p.open("r", encoding="ascii") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.endswith("\n"):
                raise ValueError(f"{p}:{lineno} not newline-terminated")
            row = json.loads(line)
            bad = _valid_loaded_name(row["name"])
            if bad:
                raise ValueError(f"{p}:{lineno} name {row['name']!r}: {bad}")
            key = (row["path"], row["reg"])
            per_file = out.setdefault(row["file"], {})
            if key in per_file and per_file[key] != row["name"]:
                raise ValueError(f"{p}:{lineno} maps {row['file']} {key} "
                                 f"to two names")
            per_file[key] = row["name"]
    _cache = out
    return out


def for_file(corpus_name: str) -> dict[tuple[str, int], str]:
    """``(proto_path, register) -> name`` for one corpus file.  Empty dict
    for files with no ported names.  Raises when the table is missing or
    self-inconsistent -- a broken table is a broken tree, not a silent
    revert to ``l<k>_<r>``."""
    return dict(_load().get(corpus_name, {}))


def reset_cache() -> None:
    """Test seam: the module-level cache is keyed on nothing, so an env
    override set after the first load would be ignored; tests flip
    ``PYLUADEC_NAMING_MAP`` and call this."""
    global _cache
    _cache = None

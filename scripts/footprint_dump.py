"""Corpus-wide static interaction-surface dump (M6 task 3).

用法: PYLUADEC_CORPUS_DIR=... uv run python scripts/footprint_dump.py
产出: corpus/observation/footprints.json（入库；生成数据，纪律同 corpus/ledger.jsonl）

This is a JOB, not a suite cost: the whole-corpus pass costs ~1.3s and the
committed JSON is what the suite reads. `tests/test_footprint.py::
test_footprints_json_is_a_reproducible_fixed_point` is the ledger-ratchet-style
guard that the committed file is byte-reproducible from this script.

## The name emission rule (and why it is not a decode)

A name is emitted verbatim iff every byte is in `0x20..0x7e` AND the whole
thing is Lua-identifier-shaped (`[A-Za-z_][A-Za-z0-9_]*`, non-empty). Anything
else becomes `{"nonascii": "<hex>"}`, built from the bytes with `.hex()`.

CLAUDE.md's red line binds ingest/lift/cfg/verify/comparison; this file is a
printing layer, the same scope the `emit/lua.py::_str_lit` exception lives in.
Even so the verbatim branch does not call `.decode()`: it builds the `str` with
`"".join(chr(b) for b in name)`, which is provably identical to an ASCII decode
on the byte range the branch has already checked, and leaves nothing to argue
about. The committed data therefore carries **ASCII identifier strings only** --
the precedent is the probe pins, which already name `doScriptScene` and
`memoryFlag`.

The `"nonascii"` key name is the plan's, kept verbatim, and is a slight
misnomer: it also catches printable-ASCII names that are not identifier-shaped
(`"has space"`, `"9lives"`). Measured on this corpus, 2026-08-13: **0** names
of either kind reach it (every global name, table key and callee name in all
229 files is an ASCII identifier), so the branch's only evidence is synthetic
(`tests/test_footprint.py::test_name_emission_rule`) -- MEMORY.md's "the corpus
is a weaker oracle than it looks" applies exactly here.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VERSION = "footprint-v1"

_ID_HEAD = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_")
_ID_TAIL = _ID_HEAD | frozenset(b"0123456789")


def is_ascii_identifier(name: bytes) -> bool:
    """Lua identifier shape over raw bytes, spelled without `re`.

    `src/pyluadec/lift/` bans regex statically; this script is outside that
    scan, but a second, regex-flavoured spelling of the same predicate is
    exactly the drift this project keeps paying for -- so it is written once,
    here, as a byte-set test. Keywords are NOT excluded: this is a shape test
    for a JSON key, not a code generator.
    """
    if not name:
        return False
    if name[0] not in _ID_HEAD:
        return False
    return all(b in _ID_TAIL for b in name[1:])


def emit_name(name: bytes):
    """`str` if `name` is an ASCII identifier, else `{"nonascii": hex}`."""
    if is_ascii_identifier(name):
        # Not `.decode()`: see the module docstring. Every byte is already
        # known to be in 0x41..0x7a / 0x30..0x39 / 0x5f, so chr() is exact.
        return "".join(chr(b) for b in name)
    return {"nonascii": name.hex()}


def emit_pair(pair: tuple[bytes, bytes]):
    return [emit_name(pair[0]), emit_name(pair[1])]


def _sorted_names(s):
    return [emit_name(x) for x in sorted(s)]


def _sorted_pairs(s):
    return [emit_pair(x) for x in sorted(s)]


_COUNTERS = (
    "read_sites", "attributed_reads", "unattributed_reads", "dynamic_reads",
    "nonstring_key_reads",
    "write_sites", "attributed_writes", "unattributed_writes", "dynamic_writes",
    "nonstring_key_writes", "setlist_sites",
    "call_sites", "global_call_sites", "table_key_call_sites", "unattributed_calls",
    # overlay, not partition members -- see Footprint's field comment
    "register_const_key_reads", "register_const_key_writes",
)


def proto_record(proto_path: str, n_insns: int, fp) -> dict:
    rec = {"proto_path": proto_path, "n_insns": n_insns,
           "global_reads": _sorted_names(fp.global_reads),
           "global_writes": _sorted_names(fp.global_writes),
           "table_key_reads": _sorted_pairs(fp.table_key_reads),
           "table_key_writes": _sorted_pairs(fp.table_key_writes),
           "calls": _sorted_names(fp.calls),
           "table_key_calls": _sorted_pairs(fp.table_key_calls)}
    for c in _COUNTERS:
        rec[c] = getattr(fp, c)
    return rec


def _hist(counter: Counter) -> dict:
    return {str(k): counter[k] for k in sorted(counter)}


def _weighted_quantile(counter: Counter, q: float) -> int:
    """The `q`-quantile of the POPULATION the histogram describes (protos),
    not of its distinct keys -- a size histogram is heavily zero-weighted here
    and quantiling the key list instead would misreport it by an order of
    magnitude."""
    total = sum(counter.values())
    seen = 0
    target = q * total
    for k in sorted(counter):
        seen += counter[k]
        if seen >= target:
            return k
    return max(counter)


def _weighted_median(counter: Counter) -> int:
    return _weighted_quantile(counter, 0.5)


def main() -> int:
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    from pyluadec.lift.footprint import proto_footprint
    from pyluadec.pipeline import walk_proto_paths

    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    files = sorted(corpus.glob("*.lua"))
    if not files:
        print(f"no *.lua under {corpus}", file=sys.stderr)
        return 1

    out_files = []
    totals = Counter()
    dyn_hist = Counter()
    keyread_hist = Counter()
    keywrite_hist = Counter()
    globalread_hist = Counter()
    all_globals_read: set[bytes] = set()
    all_globals_written: set[bytes] = set()
    all_key_reads: set[tuple[bytes, bytes]] = set()
    all_key_writes: set[tuple[bytes, bytes]] = set()
    all_calls: set[bytes] = set()
    all_key_calls: set[tuple[bytes, bytes]] = set()
    n_protos = 0
    n_nonidentifier_names = 0

    for f in files:
        protos: dict = {}
        walk_proto_paths("main", load_file(f), protos)
        recs = []
        for path, p in protos.items():
            fp = proto_footprint(lift_proto(p))
            n_protos += 1
            recs.append(proto_record(path, len(p.code), fp))
            for c in _COUNTERS:
                totals[c] += getattr(fp, c)
            dyn_hist[fp.dynamic_reads] += 1
            keyread_hist[len(fp.table_key_reads)] += 1
            keywrite_hist[len(fp.table_key_writes)] += 1
            globalread_hist[len(fp.global_reads)] += 1
            all_globals_read |= fp.global_reads
            all_globals_written |= fp.global_writes
            all_key_reads |= fp.table_key_reads
            all_key_writes |= fp.table_key_writes
            all_calls |= fp.calls
            all_key_calls |= fp.table_key_calls
        out_files.append({"file": f.name, "protos": recs})

    for name in (all_globals_read | all_globals_written | all_calls
                 | {x for pr in all_key_reads | all_key_writes | all_key_calls for x in pr}):
        if not is_ascii_identifier(name):
            n_nonidentifier_names += 1

    summary = {
        "n_files": len(files),
        "n_protos": n_protos,
        "distinct_globals_read": len(all_globals_read),
        "distinct_globals_written": len(all_globals_written),
        "distinct_table_key_reads": len(all_key_reads),
        "distinct_table_key_writes": len(all_key_writes),
        "distinct_calls": len(all_calls),
        "distinct_table_key_calls": len(all_key_calls),
        # How many distinct names in the whole dump are NOT ASCII identifiers,
        # i.e. how much of the file uses the `{"nonascii": ...}` form.
        "non_identifier_names": n_nonidentifier_names,
    }
    for c in _COUNTERS:
        summary[c] = totals[c]
    summary["dynamic_reads_per_proto"] = _hist(dyn_hist)
    summary["table_key_reads_per_proto"] = _hist(keyread_hist)
    summary["table_key_writes_per_proto"] = _hist(keywrite_hist)
    summary["global_reads_per_proto"] = _hist(globalread_hist)

    doc = {"version": VERSION, "summary": summary, "files": out_files}
    dest = ROOT / "corpus" / "observation" / "footprints.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # indent=1 so every set element and counter is its own line: a footprint
    # diff should read like a ledger diff, not like one 4 MB line.
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=True) + "\n")

    print(f"footprints: {n_protos} protos over {len(files)} files -> {dest}")
    print(f"  table reads : {totals['read_sites']} sites = "
          f"{totals['attributed_reads']} attributed + "
          f"{totals['unattributed_reads']} unattributed + "
          f"{totals['dynamic_reads']} dynamic + "
          f"{totals['nonstring_key_reads']} non-string-const")
    print(f"  table writes: {totals['write_sites']} sites = "
          f"{totals['attributed_writes']} attributed + "
          f"{totals['unattributed_writes']} unattributed + "
          f"{totals['dynamic_writes']} dynamic + "
          f"{totals['nonstring_key_writes']} non-string-const "
          f"(+{totals['setlist_sites']} SETLIST)")
    print(f"  calls       : {totals['call_sites']} sites = "
          f"{totals['global_call_sites']} global + "
          f"{totals['table_key_call_sites']} table-key + "
          f"{totals['unattributed_calls']} unattributed")
    zero = dyn_hist[0]
    print(f"  dynamic_reads == 0 in {zero}/{n_protos} protos "
          f"({zero / n_protos:.1%}); max {max(dyn_hist)}")
    print(f"  |table_key_reads| == 0 in {keyread_hist[0]}/{n_protos} protos; "
          f"max {max(keyread_hist)}; "
          f"median {_weighted_median(keyread_hist)}, "
          f"p90 {_weighted_quantile(keyread_hist, 0.9)}, "
          f"p99 {_weighted_quantile(keyread_hist, 0.99)}")
    print(f"  keys resolved via a LOADK register (lcode.c's >255-constant "
          f"fallback): {totals['register_const_key_reads']} read, "
          f"{totals['register_const_key_writes']} write")
    print(f"  non-identifier names in dump: {n_nonidentifier_names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

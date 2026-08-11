"""台账面板：corpus/ledger.jsonl 的可读汇总。用法: uv run python scripts/ledger_dashboard.py [--markdown]"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    md = "--markdown" in sys.argv[1:]
    path = ROOT / "corpus" / "ledger.jsonl"
    if not path.exists():
        print("no ledger; run scripts/run_corpus.py first", file=sys.stderr)
        return 1
    entries = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    levels = Counter(e["level"] for e in entries)
    reasons = Counter(c["reason"] for e in entries for c in e["confessions"])
    n_occ = sum(len(e["occurrences"]) for e in entries)
    n_files = len({o["file"] for e in entries for o in e["occurrences"]})
    compile_ok = sum(1 for e in entries if e["compile_ok"])
    fallback = sum(1 for e in entries if e["fallback"])
    oracle_v = {e["oracle"] for e in entries}
    ladder_v = {e["ladder"] for e in entries}

    l3 = levels.get("L3", 0)
    # Occurrence basis as well as unique-shape basis: the ledger dedups by
    # structural_hash, so "% of unique protos" and "% of the 1944 protos that
    # actually exist" are different numbers and can move independently.
    occ_l3 = sum(len(e["occurrences"]) for e in entries if e["level"] == "L3")
    rungs = Counter(e["l3_level"] for e in entries if e["level"] == "L3")

    rows = [
        ("unique protos", len(entries)),
        ("occurrences", n_occ),
        ("files", n_files),
        ("compile_ok", f"{compile_ok}/{len(entries)}"),
        ("fallback", f"{fallback}/{len(entries)}"),
        *[(f"level {k}", v) for k, v in sorted(levels.items())],
        ("L3 share (unique)", f"{l3}/{len(entries)} ({l3 / len(entries):.1%})"),
        ("L3 share (occurrences)", f"{occ_l3}/{n_occ} ({occ_l3 / n_occ:.1%})"),
        *[(f"L3 rung {k}", v) for k, v in sorted(rungs.items(), key=lambda kv: kv[0])],
        *[(f"confession: {k}", v) for k, v in reasons.most_common(10)],
        ("oracle", ", ".join(sorted(oracle_v))),
        ("ladder", ", ".join(sorted(ladder_v))),
    ]
    if md:
        print("| metric | value |\n|---|---|")
        for k, v in rows:
            print(f"| {k} | {v} |")
    else:
        w = max(len(k) for k, _ in rows)
        for k, v in rows:
            print(f"{k:<{w}}  {v}")

    # Name names. A dashboard that only ever reports aggregates cannot be
    # acted on: "compile_ok 1477/1478" tells you something is broken but not
    # what to open. Every entry that failed to compile or is still L0 is
    # printed individually, identified by its shash prefix and the first file
    # / proto_path it occurs in (deferred minor from the M2 review; closed
    # in M3 task 8).
    problems = [e for e in entries if not e["compile_ok"] or e["level"] == "L0"]
    print()
    if md:
        print("### problem entries\n")
    else:
        print("problem entries")
    if not problems:
        print("_(none)_" if md else "(none)")
        return 0
    if md:
        print("| shash | file | proto_path | level | compile_ok |\n|---|---|---|---|---|")
    for e in sorted(problems, key=lambda e: e["shash"]):
        occ = e["occurrences"][0]
        if md:
            print(f"| {e['shash'][:12]} | {occ['file']} | {occ['proto_path']} "
                  f"| {e['level']} | {e['compile_ok']} |")
        else:
            print(f"  {e['shash'][:12]}  {occ['file']}:{occ['proto_path']}  "
                  f"level={e['level']} compile_ok={e['compile_ok']} "
                  f"(+{len(e['occurrences']) - 1} more occurrences)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

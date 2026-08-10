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

    rows = [
        ("unique protos", len(entries)),
        ("occurrences", n_occ),
        ("files", n_files),
        ("compile_ok", f"{compile_ok}/{len(entries)}"),
        ("fallback", f"{fallback}/{len(entries)}"),
        *[(f"level {k}", v) for k, v in sorted(levels.items())],
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
    return 0


if __name__ == "__main__":
    sys.exit(main())

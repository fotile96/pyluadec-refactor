"""全语料质量分（预任项目 `semantic_eval.py` 度量的移植版驱动）。

用法: PYLUADEC_CORPUS_DIR=... uv run python scripts/quality_score.py [options]

Prints a per-file table and the corpus average under
`pyluadec.verify.semantic_score` -- the ported form of the predecessor's
metric, and the only instrument comparable to its stated `avg_score 0.997`
(spec §1 goal 4, §7 M5's exit row). Read that module's docstring before
believing any number here: it lists every place the port had to decide
between reproducing the predecessor's comparison and reproducing its bridge's
information loss.

**A CLI, not a test.** One sweep decompiles all 229 files and runs 229
`luac_sz4` subprocesses; the suite has a 45s ceiling and this does not belong
inside it. `tests/test_semantic_score.py::test_corpus_smoke_three_small_files`
is the committed arm and only pins that this path works.

**Read-only with respect to everything the repository tracks.** It writes no
file at all -- in particular it does not touch `corpus/ledger.jsonl`, which is
regenerated only by `scripts/run_corpus.py`. The score is an evaluation
number; it gates nothing and can never promote a level.

Exit status is 0 unless a file failed to decompile or recompile (`--strict`
additionally fails when any file scores below `--threshold`).
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus-dir", default=os.environ.get("PYLUADEC_CORPUS_DIR"),
                    help="defaults to $PYLUADEC_CORPUS_DIR")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--threshold", type=float, default=0.997,
                    help="report how many files fall below this (default: the "
                         "predecessor's stated avg_score baseline)")
    ap.add_argument("--small-kb", type=int, default=10,
                    help="files up to this size also get the predecessor's "
                         "stricter opcode/cfg/callshape/const equality check")
    ap.add_argument("--all", action="store_true",
                    help="list every file, not just fallback files and files "
                         "below the threshold")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any file scores below --threshold")
    args = ap.parse_args()

    if not args.corpus_dir or not Path(args.corpus_dir).is_dir():
        print("PYLUADEC_CORPUS_DIR not set or not a directory", file=sys.stderr)
        return 2

    from pyluadec import oracle
    from pyluadec.ingest import load_bytes, load_file
    from pyluadec.pipeline import decompile_chunk
    from pyluadec.verify.semantic_score import score_protos

    files = sorted(Path(args.corpus_dir).glob("*.lua"))
    if args.limit is not None:
        files = files[:args.limit]

    rows: list[tuple[str, float, str, bool, str, int]] = []
    errors: list[tuple[str, str]] = []
    for f in files:
        try:
            original = load_file(f)
            res = decompile_chunk(original)
            candidate = load_bytes(oracle.compile_source(res.source))
        except Exception as exc:                                  # noqa: BLE001
            errors.append((f.name, f"{type(exc).__name__}: {exc}"))
            continue
        fs = score_protos(original, candidate,
                          file_size=f.stat().st_size, small_kb=args.small_kb)
        # "fallback" is the pipeline's own verdict on the SHIPPED artifact
        # (root not L3 => the M2 state machine was emitted), read straight
        # from the decompile result rather than inferred from the score.
        rows.append((f.name, fs.score, fs.status, res.levels["main"] != "L3",
                     fs.drift_type, len(fs.hard_issues)))

    if not rows:
        print("no files scored", file=sys.stderr)
        return 2

    below = [r for r in rows if r[1] < args.threshold]
    fallback = [r for r in rows if r[3]]
    avg = sum(r[1] for r in rows) / len(rows)

    width = max(len(r[0]) for r in rows)
    shown = rows if args.all else sorted(set(below) | set(fallback),
                                         key=lambda r: r[1])
    if shown:
        title = ("all files" if args.all
                 else f"files below {args.threshold} or on fallback")
        print(f"{'file':<{width}}  {'score':>8}  {'status':<6}  "
              f"{'artifact':<10}  drift")
        print("-" * (width + 40))
        for name, score, status, fb, drift, _ in shown:
            print(f"{name:<{width}}  {score:>8.6f}  {status:<6}  "
                  f"{'fallback' if fb else 'structured':<10}  {drift}")
        print(f"({len(shown)} rows: {title})")
        print()

    for name, msg in errors:
        print(f"ERROR {name}: {msg}", file=sys.stderr)

    n = len(rows)
    print(f"files scored      : {n}" + (f"  (+{len(errors)} errored)" if errors else ""))
    print(f"avg_score         : {avg:.6f}")
    print(f"below {args.threshold:<12}: {len(below)}")
    print(f"on M2 fallback    : {len(fallback)}"
          + (f"  (avg {sum(r[1] for r in fallback) / len(fallback):.6f})"
             if fallback else ""))
    structured = [r for r in rows if not r[3]]
    if structured:
        print(f"structured        : {len(structured)}"
              f"  (avg {sum(r[1] for r in structured) / len(structured):.6f})")
    counts = {s: sum(1 for r in rows if r[2] == s) for s in ("pass", "warn", "fail")}
    print(f"status            : " + "  ".join(f"{k}={v}" for k, v in counts.items()))

    if errors:
        return 1
    if args.strict and below:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

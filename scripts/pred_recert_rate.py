#!/usr/bin/env python3
"""Full-population pred re-certification rate -- M7 task 2 (spec §3 go/no-go).

Over every file in ``PYLUADEC_PRED_CORPUS_DIR`` (229 pred source files,
1944 proto occurrences expected): run ``pyluadec.predrecert.recert_file`` and
aggregate the Factor-T grades by OCCURRENCE (a proto counts once per file it
occurs in, matching the ledger's occurrence convention). Prints the corpus
line::

    recert: T3 a/1944, T2 b/1944, T- c/1944

plus one row per file that ships any ``T-`` occurrence (the ``*-verbatim``
residue the warranty generator will have to name), and the wall-clock.

This is a JOB, not a suite member (the suite keeps only
``tests/test_predrecert.py``'s unit tests).

**Trigger** (out-of-suite condition 2): run before M7 Task 11, and whenever
``sir/``, ``express/``, ``emit/``, or ``structure/`` change during this
milestone -- the rate moves with the recognizer, and the warranty generator
consumes per-file outcomes regenerated at generation time, so this number is
the instrument's health check, not a frozen artifact.

**Cost** (measured-not-predicted, out-of-suite condition 3): linear in files
(one compile + ingest + full decompile-and-certify per file; no per-proto
superlinear pass). ``oracle.compile_source`` is process-memoized on
``(content hash, strip, binary identity)`` (M6 task 1), so re-runs in one
process skip the compile, not the certify. Measured wall-clock: **14.21 s**
over 229 files (first full run, 2026-08-15; last run recorded in
``docs/reports/m7-warranty.md`` §1).

**Go/no-go** (spec §3): if ``(T3 + T2) / total < 0.70`` the script prints
``GO/NO-GO: BELOW 0.70 -- report to the human partner before Task 11 work``
and exits 2 (a policy line chosen in the spec to force the report, not a
prediction); otherwise exit 0.
"""
from __future__ import annotations

import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyluadec.predrecert import recert_file  # noqa: E402


def main() -> int:
    pred_dir = os.environ.get("PYLUADEC_PRED_CORPUS_DIR")
    if not pred_dir or not Path(pred_dir).is_dir():
        print("PYLUADEC_PRED_CORPUS_DIR not set or missing", file=sys.stderr)
        return 1
    names = sorted(p.name for p in Path(pred_dir).glob("*.lua"))
    totals: Counter[str] = Counter()
    t_minus_files: list[str] = []
    t0 = time.monotonic()
    for name in names:
        out = recert_file(Path(pred_dir), name)
        file_hist = Counter(out.t_grades.values())
        totals.update(file_hist)
        if file_hist.get("T-", 0):
            t_minus_files.append(
                f"  {name}: T3 {file_hist.get('T3', 0)}  T2 {file_hist.get('T2', 0)}"
                f"  T- {file_hist['T-']}"
            )
    dt = time.monotonic() - t0
    total = sum(totals.values())
    print(
        f"recert: T3 {totals['T3']}/{total}, T2 {totals['T2']}/{total},"
        f" T- {totals['T-']}/{total}  ({len(names)} files, {dt:.2f}s)"
    )
    for row in t_minus_files:
        print(row)
    rate = (totals["T3"] + totals["T2"]) / total if total else 0.0
    print(f"recert rate (T3+T2)/total: {rate:.4f}")
    if rate < 0.70:
        print(
            "GO/NO-GO: BELOW 0.70 -- report to the human partner before Task 11 work",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

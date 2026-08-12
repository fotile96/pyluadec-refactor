#!/usr/bin/env bash
# The ratchet job (M5 task 8): everything that is too slow, too stateful or too
# baseline-dependent to belong in the per-commit suite.
#
#   ./scripts/ratchet_job.sh [BASELINE_REF]
#
# BASELINE_REF is any git ref whose `corpus/ledger.jsonl` is the historical
# baseline to ratchet against; it defaults to the previous milestone's tip.
# Exits non-zero on the first gate that fails.
#
# Gate 3 is here rather than in the suite ON PURPOSE. The standing suite runs
# DEFAULT_LIMIT = 3 of tests/test_generated_semantic_cases.py's CASE_COUNT = 24
# differential-execution cases (0.31s); the full 24 costs 2.48s (both measured
# 2026-08-12 on macOS arm64), and the suite has ~8s of headroom against its 45s
# ceiling with an L2 harness still to land. So the ported fuzz harness runs in
# full HERE, on the ratchet, and one eighth of it per commit.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${PYLUADEC_CORPUS_DIR:?set PYLUADEC_CORPUS_DIR to the 229-file corpus}"

# eb08890 = "Merge phase4-m4-loops", the last merged milestone tip and this
# branch's fork point. Override with any ref that has a corpus/ledger.jsonl
# (e.g. bbe74f6, the M3 tip, for a two-milestone diff).
BASELINE_REF="${1:-eb08890}"
# Portability, not style (M5 task 8 round 1). `mktemp -t NAME` is the BSD
# spelling and works on macOS, but GNU coreutils treats -t's argument as a
# TEMPLATE and rejects one without trailing X's: src/mktemp.c does
# `x_count = count_consecutive_X_s(...); if (x_count < 3) error(EXIT_FAILURE,
# 0, _("too few X's in template %s"))`, and -t only sets `use_dest_dir`, so it
# does not bypass that check (read from upstream coreutils master this
# session; NOT run -- no GNU userland was available on this host). Under
# `set -e` the job would have died on this line on Linux, i.e. on the
# project's documented primary environment. A positional template with six X's
# is the one spelling both accept, and it was run on macOS here.
BASELINE_FILE="$(mktemp "${TMPDIR:-/tmp}/pyluadec-ledger-baseline.XXXXXX")"
trap 'rm -f "$BASELINE_FILE"' EXIT

echo "== gate 1: full test suite (includes the ledger fixed point) =="
uv run pytest -q

echo "== gate 2: ledger ratchet vs $BASELINE_REF =="
# Gate 1 already proved corpus/ledger.jsonl is a byte-exact fixed point of
# scripts/run_corpus.py against this corpus and this oracle
# (tests/test_ledger_ratchet.py), so the committed file is the live artifact
# and there is nothing to regenerate here. The bisect predicate documented in
# docs/runbooks/structured-pipeline.md regenerates instead, because at an
# arbitrary bisected commit the committed ledger is NOT known to be current.
git show "$BASELINE_REF:corpus/ledger.jsonl" > "$BASELINE_FILE"
uv run python scripts/ratchet_diff.py "$BASELINE_FILE" corpus/ledger.jsonl

echo "== gate 3: full generated differential-execution sweep (24 cases) =="
PYLUADEC_GENERATED_CASE_LIMIT=24 uv run pytest tests/test_generated_semantic_cases.py -q

echo "RATCHET JOB PASSED (baseline $BASELINE_REF) on $(uname -m) / $(uname -s)"

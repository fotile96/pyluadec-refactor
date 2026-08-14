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
# differential-execution cases (~0.3s); the full 24 costs UNDER 3 SECONDS.
# That is deliberately an order of magnitude and not a range: 13 runs across
# M5 task 8 measured 2.21-2.54s on macOS arm64, and two successive attempts to
# quote a tight range were falsified by the next routine run. The placement
# argument was originally written against a 45s suite ceiling with ~7s of
# headroom; that premise is retired (the ceiling is now the ~120s EARMARK
# described in CLAUDE.md, and the suite measured 57.90s at the M6 wrap). What
# survives the premise change is the rule the earmark itself states: budget
# goes to the formal-verification instruments, and a whole-corpus / full-fuzz
# sweep is a JOB, not a suite member. So the ported fuzz harness runs in full
# HERE, on the ratchet, and one eighth of it per commit.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${PYLUADEC_CORPUS_DIR:?set PYLUADEC_CORPUS_DIR to the 229-file corpus}"
# M6's own gates -- the loss sweeps, the cross-corpus scan and the parity
# census -- are all keyed on the PREDECESSOR corpus, and conftest.py skips
# them (it does not fail) when it is unset. Without this line the documented
# milestone gate printed RATCHET JOB PASSED while 32 tests skipped, including
# the whole-corpus loss sweep that found defect 6 and the pin-rot gate
# `test_every_pin_still_diverges_with_the_recorded_evidence`. Measured on this
# tree (2026-08-14): with PYLUADEC_PRED_CORPUS_DIR unset, `uv run pytest -q`
# reports `1055 passed, 32 skipped` -- 22 in test_cross_corpus.py, 8 in
# test_loss_sweep.py, 2 in test_predcorpus.py -- and still exits 0.
: "${PYLUADEC_PRED_CORPUS_DIR:?set it to the predecessor corpus of 229 decompiled .lua sources -- 32 M6 gate tests skip SILENTLY without it}"

# 0957364 = "Merge phase5-m5-longtail", the last merged milestone tip and the
# M6 branch's fork point. Override with any ref that has a corpus/ledger.jsonl
# (e.g. eb08890, the M4 tip, or bbe74f6, the M3 tip, for a multi-milestone
# diff). Updated at the M6 wrap (task 13): the default had been left at
# eb08890 through M5's merge, which still catches every downgrade but grades
# against a two-milestone-old baseline. Comparing against the NEWEST merged
# tip is the stricter reading and is what the line above always claimed to be.
BASELINE_REF="${1:-0957364}"
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

echo "== gate 1: full test suite (includes the ledger and observation fixed points) =="
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

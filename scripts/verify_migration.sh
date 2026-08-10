#!/usr/bin/env bash
# Migration gates (spec §6 Step 2). Run on any host; passing on a 64-bit host = M1 complete.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${PYLUADEC_CORPUS_DIR:?set PYLUADEC_CORPUS_DIR to the 229-file corpus}"
if [ ! -d "$PYLUADEC_CORPUS_DIR" ] || [ -z "$(find "$PYLUADEC_CORPUS_DIR" -maxdepth 1 -name '*.lua' -print -quit)" ]; then
  echo "PYLUADEC_CORPUS_DIR ('$PYLUADEC_CORPUS_DIR') does not exist or contains no *.lua files" >&2
  exit 1
fi

echo "== gate 1: build all artifacts =="
./scripts/build_native.sh

echo "== gate 2: sz4 load->redump byte-identical over corpus =="
uv run python scripts/roundtrip_sz4.py build/luac_sz4

echo "== gate 3: ingest parity vs golden =="
uv run python scripts/compare_bridge_golden.py

echo "== full test suite =="
uv run pytest -v

echo "ALL MIGRATION GATES PASSED on $(uname -m) / $(uname -s)"

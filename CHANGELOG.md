# Changelog

## 2026-08-10 — M1 (partial): macOS arm64 migration gate green

- `PYLUADEC_CORPUS_DIR=<corpus> ./scripts/verify_migration.sh` →
  `ALL MIGRATION GATES PASSED on arm64 / Darwin` (120 tests passed). First
  64-bit platform proven: the ingest layer's header-dispatched serialization
  width holds on a host where `sizeof(size_t) == 8`, both non-vacuously
  (`luac_sz8` correctly rejects this 32-bit corpus rather than silently
  misparsing it) and constructively (`luac_sz4` byte-for-byte roundtrips the
  whole corpus on this host).
- Linux x86_64 verification is still outstanding. Per
  `docs/runbooks/64bit-migration.md`, M1 requires both 64-bit platforms
  green, not either — this entry closes the macOS arm64 half only.

## 2026-08-10 — M2: fallback closed loop

- 229/229 corpus files produce compilable Lua source via the fallback
  state-machine emitter (`pyluadec.structure.fallback.emit_chunk`), verified
  by `tests/test_corpus_compile.py` and `scripts/run_corpus.py` (`compiled
  229/229`).
- Certification ledger v1 online: `corpus/ledger.jsonl` committed, 1478
  unique proto shapes / 1944 total proto occurrences across the corpus, all
  at level `L1` (fallback emission compiles clean against the in-repo
  oracle). Regeneration is a fixed point of `scripts/run_corpus.py`, guarded
  by `tests/test_ledger_ratchet.py`.
- All 38 Lua 5.1 opcodes covered end-to-end by differential-execution tests
  (`tests/test_fallback_*.py` via `tests/diffexec.assert_fallback_roundtrip`,
  `tests/test_fallback_closures.py::test_all_38_opcodes_reachable_in_emitter`):
  original bytecode and fallback-decompiled source run through the real
  `lua` interpreter and must agree on stdout and exit code.
- L3.0 strict proto comparator (`pyluadec.verify.normalize`) online with a
  versioned, currently-empty normalization ladder (`l3-ladder-v0`); basic-
  block CFG (`pyluadec.cfg.blocks`) and an irreducible-graph-safe dominator
  tree (`pyluadec.cfg.dom`, Cooper–Harvey–Kennedy) are built and actually
  consumed by the fallback emitter (unlike the CFG in the original
  `pyluadec`, which was built but never read by its structuring pass).
- See `docs/runbooks/decompile-pipeline.md` for the full pipeline reference
  and a reading guide for fallback output.

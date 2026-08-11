# Changelog

## 2026-08-11 — M3: structured backbone

- **Structural recovery online.** Three new packages replace the fallback path
  for the majority of the corpus: `pyluadec.sir` (dominator-driven region
  identification — `Straight`/`Seq`/`If`/`NumericFor`/`GenericFor`/`Break`/
  `Return`), `pyluadec.express` (register classification + statement/expression
  reconstruction), and `pyluadec.emit.lua` (a 561-line pure structural printer:
  one walk of the typed trees, no regex, no post-processing of its own output).
  The *absence of `re`* across
  `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}` is
  statically enforced by
  `tests/test_engineering_practice.py::test_no_regex_in_analysis_or_emission_layers`
  (one narrowly-scoped pre-existing exception in `structure/fallback.py`).
  "One walk, no post-processing" is a design discipline held by review and by
  the module docstring, not by a static check.
- **1112 of 1478 unique proto shapes (75.2%) and 1577 of 1944 proto
  occurrences (81.1%) now certify `L3`** — the printed source recompiled
  through the real `luac_sz4` and compared field-by-field against the original.
  92 of the 229 files ship genuinely structured source; the other 137 still
  ship the M2 fallback. Gated by `tests/test_m3_exit.py` (threshold >50%, a
  milestone commitment that must not be edited down).
- **Certification is the only landing gate.** `emit_certified_chunk` ships
  structured source **iff** the root proto certified `L3`, and the semantically
  exact fallback chunk otherwise. A bug in region identification or inlining
  can therefore only lower the L3 rate; it cannot produce wrong output.
  Certification is per proto subtree, so one unstructurable function does not
  poison its siblings' recorded levels.
- **Normalization ladder rung 1 (`L3.1`, `strip-lineinfo`)** added;
  `LADDER_VERSION` bumped to `l3-ladder-v1`. Its soundness argument is
  co-located with the rung in `verify/normalize.py` and is made from what
  `compare_protos` still compares afterwards (`code`, `constants` bitwise,
  frame sizes, locvar scope ranges, upvalue count, subprotos), not from a
  hand-wave. Measured: 0 of the 1112 `L3` entries certify at rung 0 — the
  corpus's `source = "=?"` and surviving `linedefined` make rung 0 unreachable
  here.
- **Two new standing gates.** `tests/test_global_state_probe.py` compares the
  observable global-table delta between original bytecode and decompiled output
  on real corpus content: **225 of 229 files byte-identical, 4 pinned
  divergences** that are error-message *text* only (an `ldebug.c` `getobjname`
  naming artifact of the fallback's register-box model — instruction-level
  evidence in `docs/runbooks/m3-backlog.md`). `tests/test_effects_emitter_consistency.py`
  mechanically reconciles `lift/effects.py` against the emitter templates:
  207214 of 214192 corpus instructions checked, 0 disagreements, plus a
  synthetic operand grid reaching all 38 opcodes.
- **Capability boundary, stated honestly.** `while`, `repeat`, and mixed or
  irreducible back edges are **not** structured: `build_sir` refuses 169 unique
  protos, 162 of them carrying such an edge, plus 7 acyclic refusals — all 16
  unique protos containing `TESTSET` (the `and`/`or` value idiom) are among
  these 169 refusals. A further 139 unique protos build a region tree but do
  not print because a descendant closure does not, and 58 print but do not
  certify. All of them stay at `L1` with a confession. This is the largest
  single M4 increment; see `docs/runbooks/m3-backlog.md`.
- **Ledger ratchet — what is machine-checked and what is not.** Asserted: no
  `L0`, `compile_ok` everywhere, `shash` sortedness/uniqueness, full-corpus
  coverage at 1944 occurrences, byte-identical regeneration from
  `run_corpus.py`, and *within-row* coupling between level and confession in
  both directions (`test_m3_exit.py`). **Not** asserted: cross-revision
  monotonicity — no test compares against a historical baseline, so a
  regenerated ledger with fewer `L3` rows passes the suite as long as the rate
  stays above 50%. "Levels only ever go up" is discipline plus review of the
  ledger diff; full ratchet CI is an explicit M4 item.
- See `docs/runbooks/structured-pipeline.md` for the full reference: layer
  layout, the certification invariant, the ladder, the `freereg` register model
  that was worth +63.6 points of L3 rate (and the pre-identified effect-mode
  lever that was worth exactly 0.0), and the day-to-day commands.

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
  versioned, currently-empty normalization ladder (`l3-ladder-v0`). Basic-
  block CFG (`pyluadec.cfg.blocks::build_cfg`) is built and actually consumed
  by the fallback emitter — one dispatch state per basic block (unlike the
  CFG in the original `pyluadec`, which was built but never read by its
  structuring pass). The irreducible-graph-safe dominator tree
  (`pyluadec.cfg.dom`, Cooper–Harvey–Kennedy) is implemented and tested
  (`tests/test_dom.py`) but has **no production consumer yet** — it is M3
  substrate, not something M2 reads. Likewise, `lift/effects.py`'s per-opcode
  `InstrEffects` (`effect`, `may_error`, `reads`, `writes`, `reads_open`,
  `writes_open`) are computed and attached to every `LirInstr` but not yet
  read by the emitter — also M3/M4 substrate (see "Effect modes" in
  `docs/runbooks/decompile-pipeline.md`).
- See `docs/runbooks/decompile-pipeline.md` for the full pipeline reference
  and a reading guide for fallback output.

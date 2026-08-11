# Changelog

## 2026-08-12 — M4: loops, and verification hardening

- **Loops recovered.** `while <cond>`, `while true`, `repeat`, threaded
  end-of-iteration jumps and the `and`/`or` *value* idiom are now region kinds
  (`sir/regions.py`: `While`, `WhileTrue`, `Repeat`, `EndIter`, `CondValue`;
  recognizers in `sir/build.py`). `build_sir` acceptance went **1309 -> 1447**
  of 1478 unique proto shapes. Measured against the predecessor's shipped
  output on the 212 files we structure, our line-leading `while` and `break`
  counts match it **exactly** (190/190 and 175/175) —
  `docs/reports/m4-readability.md`. **`repeat` is recognized but this corpus
  contains none** (0 `repeat`/`until` lines in all 229 decompiled files
  against 971 `while`), so its only evidence is synthetic; corpus green says
  nothing about it.
- **The real bottleneck was register classification, not loops.** `RegClass`
  gave one verdict per register *number* per function; task 13 made it per
  `(register, definition)`. That single change took the print-but-do-not-
  certify residual from 283 unique protos to **35**, and the "differs from the
  original only by extra `MOVE`s" cluster inside it from 253 to **4**. The
  three loop tasks before it moved the top two capability rows and the `L3`
  rate not at all.
- **`L3` is 1389/1478 unique (94.0%) and 1855/1944 occurrences (95.4%)**, from
  1112 (75.2%) / 1577 (81.1%) at M3 close, against an M4 exit floor of 85% on
  both bases (`tests/test_m4_exit.py`, which also pins the denominator at
  `== 1944`). **212 of 229 files ship structured source**, up from 92. The
  floors are milestone commitments and are deliberately ~9 points below the
  achievement: a floor set at the measurement is a tripwire, and the standard
  repair for a tripwire is to edit the threshold.
- **The ledger now says WHY a proto is not `L3`.** New `refusal_reason` field,
  four committed kinds (`structure:` / `reconstruct:` / `compile:` /
  `mismatch: <field>`), coupled to `level` in both directions and asserted as
  such. The residual census in `docs/runbooks/structured-pipeline.md` is
  derived from this field rather than from a scratch script, and
  `scripts/ledger_dashboard.py` prints its histogram. Two deliberate
  exclusions keep corpus payload out of a checked-in file: the reason carries a
  `Mismatch`'s field NAME and never its values, and never `luac`'s error text.
- **A behavioural probe (L1.75) is a standing gate.** `tests/test_behaviour_probe.py`
  loads each chunk under a stubbing environment, **invokes every global
  function it defined**, and compares a deterministic event trace between the
  original bytecode and our output: **229 files, 227 byte-identical, 2 pinned
  divergences, 0 probe failures, 398196 recorded events.** Read the reach split
  before over-crediting it — the 3000-event cap truncates 132 of 229 files, and
  those contribute 99.5% of the events while the other 97 contribute a median
  of **10** each. One feasibility claim carried into it was measured false: the
  stub-return policy is **not** agreement-invariant (227/227/226/226 across four
  policies).
- **Semantic-regression port.** The predecessor's 5 named semantic cases and 6
  roundtrip cases are ported, plus a generated differential harness; **3 of
  the 5 named cases ship structured, 2 ship the M2 fallback** —
  `test_counter_closure_and_dispatch_mix` and
  `test_if_and_elseif_conjunctions_preserved`, each pinned by an `== "L1"`
  assertion and a `b"__pld_pc" in out.source` check in
  `tests/test_semantic_regressions.py`, with the cause named in that case's
  own docstring (the "prints but does not certify" `mismatch` residual, and
  `build_sir`'s "if targets out of range" refusal, respectively — both in the
  M5 agenda's residual clusters).
- **Certification got stricter, not just wider.** `certify_l3` now compiles the
  candidate with `strip=not carries_debug(original)`, so rung 1 compares real
  locvar scope ranges on unstripped input. The corpus did not move (all 1944
  protos read as stripped). "Stricter" is the accurate word, not "strictly
  stronger": a gate that starts examining a dimension cannot also promise never
  to reject on it, and a reconstruction that materializes a `local` the
  original never declared is now refused.
- **`TAILCALL` gained `writes_open` in the axiom layer**, with the differential
  run CLAUDE.md requires: `classify_registers`' four fields plus every proto's
  level/rung/reason swept over all 1944 occurrences before and after —
  byte-identical, and `corpus/ledger.jsonl` reproduced byte-for-byte. The reason
  it moved nothing is structural (`effects.successors(TAILCALL) == ()`, so a
  `TAILCALL` always ends its basic block), now pinned by a test rather than
  left as prose. A knock-on: the effects–emitter consistency gate's blanket
  open-region skip was removed rather than accepted, taking it from 207214 to
  **all 214192** corpus instructions checked.
- **A second consistency gate**, `tests/test_effects_reconstructor_consistency.py`,
  reconciles `lift/effects.py` against the *structured* path
  (`express/reconstruct.py` -> `emit/lua.py`) — a third independent hand
  transcription of `lvm.c` that nothing had been checking. **0 violations**, by
  instrumentation rather than by a fourth transcription. Its own docstring
  records what it does NOT assert, including that `FORPREP`'s row backs no
  checked touch.
- **Effect-lattice calibration done.** `STRICT` stays the pipeline-wide default
  and is the only mode any `src/` code selects (enforced by a test).
  `NO_METAMETHOD` is a permitted per-pass opt-in **scoped to script-constructed
  tables** — the census finds 0 metamethod-related constants in 71414, but 56
  of the 164 global names the corpus reads are never written by it and come
  from the engine, where the census is blind. `TRUSTING` is recommended against
  for any pass: its whole delta is three rows and the corpus falsifies all
  three. `lift/effects.py`'s behaviour is unchanged (replayed identical over
  82080 comparisons). Two rows were found under-graded and left alone pending
  the full axiom protocol; the `LEN` one is a real defect and is M5 agenda
  item 1.
- **Readability evaluated honestly** against the predecessor's shipped
  localization input, in `docs/reports/m4-readability.md`. Structured output is
  0.98× the predecessor's line count in aggregate with all 212 files inside
  0.78×–1.03×, and carries **zero** `__pld_*` artifacts. It reads *worse* in
  five named printer-level places — non-ASCII strings as decimal escapes, no
  `elseif` (208 of them become nested `if`s, worst case 61 levels of nesting
  against 5), no dot sugar for string keys, un-indented function bodies, unary
  minus printing as `(-1)` — plus a sixth, structural one: the 17 files still
  on fallback are 47.6% of the corpus **by line volume**, so "212 of 229 files" is
  the flattering way to count.
- **Not done in M4, and now the M5 agenda** (`docs/runbooks/m3-backlog.md`):
  full ratchet CI (baseline diff, downgrade = fail) — M4 delivered the field
  that makes it cluster usefully but not the CI; the `LEN` regrade; the 89
  remaining uncertified proto occurrences, which are all inside those 17 files
  and hold 692 individually-certified siblings hostage; L2 differential
  certification and the key-sequence harness.

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

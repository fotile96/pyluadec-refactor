# Phase 5 (M5): Long-Tail Closure, Hybrid Emission, L2, and the Predecessor Baseline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the 89-proto structuring residual as far as measurement allows, ship **every** file mostly-structured via per-proto hybrid emission, land the L2 differential gate with the two historical key-sequence checkpoints, and demonstrate ≥ the predecessor's 229-corpus quality baseline (avg_score 0.997) with a ported apples-to-apples metric.

**Architecture:** Extends the M4 pipeline in place. No new subsystem: **the spec §4 pass registry is retired permanently** (decision by the human partner, 2026-08-12 — the certification gate already provides per-function apply→verify→commit/rollback plus confession bookkeeping, and two milestones of idiom work closed hundreds of shapes without it; if the M6+ GPU proposer ever needs a plugin interface, re-raise with it as the client). Hybrid emission replaces the chunk-level all-or-nothing shipping rule with a per-proto rule under a new, explicitly stated invariant. The L2 harness builds on the M4 behaviour probe (L1.75), adding a key-sequence driver, taint marking, and a coverage badge.

**Tech Stack:** Python 3.13 (uv), pytest (+pytest-timeout), vendored Lua 5.1.5 dual-width oracles (`luac_sz4`/`lua_sz4`), pybind11 ingest bridges. No new dependencies.

## Global Constraints

Copied from CLAUDE.md, the spec, and standing directives. Every task implicitly includes this section.

- **Certification must never be relaxed to raise a number.** `verify/normalize.py` (`NORMALIZATIONS`, `LADDER_VERSION`, `compare_protos`, `_cmp`), `verify/certify.py`'s comparison logic, `structural_hash` in `verify/ledger.py` may only be tightened. A new ladder rung needs a standalone soundness argument argued from what `_cmp` still compares, a `LADDER_VERSION` bump, and isolating positive/negative tests (pattern: `tests/test_normalize_l31.py`).
- **Recognize or raise `StructureError` — never emit a guessed structure.** No best-effort branch in `sir/build.py`.
- **The pc-claim audit does not bend:** `all_claimed(region) == set(fn.instrs)` at every `build_sir` exit. Standing lesson: the audit does **not** catch a dropped threaded jump — separate guards do; ask what each new construct could silently drop.
- **Every proto in a shipped artifact is either its certified structured text or the semantically-exact fallback.** This is the M5 restatement of "uncertified output must not ship" — Task 6 defines it precisely and it REPLACES the M4 invariant "artifact structured ⟺ root L3" when hybrid emission lands. Until Task 6, the M4 invariant stands unchanged.
- **The ledger ratchets upward only** — no `L3`→`L1`, no `L0`; regenerated wholesale by `scripts/run_corpus.py`; byte-identical fixed point of its own generator. Schema changes (Tasks 6, 8, 9) are expected and reviewed as schema changes.
- **`corpus/golden/` is a read-only archive**, never regenerated. **`vendor/` pristine** — all Lua changes via `native/patches/*.patch`; reading `lvm.c`/`lparser.c`/`lcode.c`/`ltable.c`/`ldebug.c` is expected.
- **Bytecode-derived strings are `bytes` and are never decoded in `ingest`/`lift`/the comparison layer.** *Amended by the human partner 2026-08-12 (Task 7):* the **print layer** may apply a presentation-level decode with a documented, lossless-round-trip-gated fallback. The amendment is scoped to `emit/` and must be recorded in CLAUDE.md when Task 7 lands.
- **No regex** in `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}` (`tests/test_engineering_practice.py`); the printer stays a **pure structural fold** — one walk of the typed tree, never re-reading or post-processing its own output.
- **Corpus access only via `PYLUADEC_CORPUS_DIR`**; `tests/conftest.py`'s skip behavior unchanged.
- **Engineering practice, standing directive (verbatim):** "在实现过程中，你可看情况插入一些额外的review轮，用于检查是否有滥用regex匹配等不合适的编程风格与工程实践，这些东西最大的问题是可能把单元测试变得极慢，从而阻塞正常的开发流程。" Suite at M5 start: **512 tests / 40–42s against the 45s ceiling** — Task 2 exists to buy headroom before anything else spends it.
- **Measurement provenance.** Twenty-plus confidently-worded numbers were overturned across M3–M4, several planted inside review findings. Every number below is marked with provenance; implementers **re-derive before relying, and if a number here does not reproduce, the measurement wins and you report it.** Re-verify citations and counts **after** editing, not before (three sweeps introduced their own staleness). Prefer symbol references over `file:line`.
- **Guard discipline.** Four consecutive M4 reviews found guards deletable with a fully green tree. Every new guard/invariant/refusal ships with a committed neuter→named-test-fails→restore proof, or is explicitly marked defensive with what was tried.
- **Axiom-layer changes** (`lift/effects.py` grading) need an `lvm.c` citation **plus a differential run** (worked example: M4 task 8).
- **Opcode semantics:** the predecessor's `a-no-frills-introduction-to-lua-5.1-vm-instructions.pdf` outranks official docs, **except its p.37 `OP_TESTSET` prose, which is a recorded erratum** (see CLAUDE.md); vendored source is ground truth.
- **Confess, don't guess.**

## Measurement grounding (2026-08-12, on master `eb08890` unless noted)

| fact | value | provenance |
|---|---|---|
| L3 | 1389/1478 unique (94.0%), 1855/1944 occurrences (95.4%); 212/229 files structured | committed ledger; dashboard |
| non-`L3` rows | 89 = 49 `structure:` / 35 `mismatch:` / 5 `reconstruct:` | ledger `refusal_reason` |
| **leaf defects** (non-`L3` protos whose every descendant is `L3`) | **67**, vs 22 poisoned ancestors | measured this session (scratch script; Task 3 Step 1 recreates it as the standing census) |
| leaf clusters | 18 `mismatch: maxstacksize`, 15 `mismatch: code`, 11 else-join, 9 unreachable-branch-body, 9 if-targets, 3 consumed-read, 1 while-header-statements, 1 and/or-alternative-statements | same |
| smallest exemplar per cluster | `snr_common.lua:main_24_1` (19 insns, maxstacksize); `main_77_0` (5, code — the known upvalue-index residual); `main_59` (17, unreachable); `main_68` (22, if-targets); `main_74_12` (102, else-join); `snr_novel.lua:main_13` (75, while-header); `snr_s5_10_s.lua:main_43` (227, consumed-read); `snr_story_main.lua:main_3` (461, and/or-alt) | same |
| the 17 fallback files | 47.6% of corpus line volume; 692 of their 781 protos already certify `L3`; **all** 89 non-`L3` protos live inside them | `docs/reports/m4-readability.md`, re-verified at M4 final review |
| suite | 512 / 40.2–42.7s; `test_ledger_ratchet` ~11.7s + behaviour-probe setup ~10.0s = 54% of wall | M4 task 12 + agenda item 12 |
| predecessor baseline | avg_score **0.997** under `semantic_eval.py`'s weighted counter-similarity (opcode families, global reads/writes, call targets/shapes, return arity, const fingerprint — 546 lines, pure Python over proto dicts, portable) | spec §1 goal 4; metric read this session at `/Users/fotile96/pyluadec/pyluadec/semantic_eval.py` |
| key-sequence checkpoints | `SystemOption.OptionMain` double-clamp; `SystemConfig.ConfigMain` CIRCLE gate/wait | predecessor `DEBUG_KEY_SEQUENCE_HARNESS.md` (on this machine) |
| behaviour probe ceiling | 3000-event cap truncates 132/229 files (99.5% of events); other 97 files median 10 events | M4 task 10, re-verified at review |
| `LEN` at `NO_METAMETHOD` | confirmed-wrong axiom row (`PURE`, should be `READ_HEAP`); 22 corpus `LEN` sites | M5 agenda item 1, adjudicated against `lvm.c`/`ltable.c` by two parties |
| downstream coupling | `post_process/` expects `v\d+` naming — **already broken** by our `l0_0` names, so the old chain is incompatible regardless; CLAUDE.md: "不必字节级复刻旧输出…要么显式版本化" | CLAUDE.md 下游耦合; readability report |

Scope decisions by the human partner (2026-08-12): **pass registry retired permanently**; **hybrid emission in scope**; **presentation-layer string decode in scope**.

## What M3–M4 learned that binds every task

1. **The corpus is a weak oracle** — synthetic fixtures (`tests/synth.py`, oracle-compiled sources) before corpus numbers; fault-injection proof for every gate.
2. **State the property, not the mechanism.** Sketches are starting points; invariants govern.
3. **Certification adjudicates byte fidelity** — print natural source, recompile, let the gate decide. Never simulate luac's threading by hand.
4. **Bottlenecks move.** Task 3 of M4 bought +27 protos where the plan expected the milestone; the unplanned Task 13 bought +250. Each closure task here re-measures before and after, and the plan expects to be amended mid-flight.

## File structure

```
src/pyluadec/lift/effects.py          # T1: LEN regrade (axiom protocol)
src/pyluadec/structure/structured.py  # T2: process-level memo; T6: hybrid assembly
src/pyluadec/sir/build.py             # T4: refusal-cluster closure
src/pyluadec/express/{names,reconstruct}.py  # T5: mismatch closure; T11: extraction
src/pyluadec/emit/lua.py              # T7: elseif/dot-sugar/unary-minus/indent/presentation
src/pyluadec/verify/semantic_score.py # T3: ported predecessor metric
src/pyluadec/verify/ledger.py         # T6/T8: schema (hybrid flag; Mismatch.path in reason)
scripts/ratchet_diff.py               # T8: baseline diff CI
scripts/probe_keyseq.{py,lua}         # T9: L2 key-sequence harness
tests/test_effects_len.py             # T1
tests/test_semantic_score.py          # T3
tests/test_sir_longtail2.py           # T4
tests/test_express_residual.py        # T5
tests/test_hybrid_chunk.py            # T6
tests/test_emit_readability.py        # T7
tests/test_ratchet_diff.py            # T8
tests/test_l2_keyseq.py               # T9
tests/test_keyseq_checkpoints.py      # T10
docs/runbooks/*, CHANGELOG.md, CLAUDE.md, docs/reports/m5-quality.md  # T12
```

Execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12. Tasks 1–3 are independent of each other; 4–5 feed 6; 9 feeds 10.

---

### Task 1: Regrade `LEN` at `NO_METAMETHOD` — the axiom protocol, third rehearsal

**Files:** Modify `src/pyluadec/lift/effects.py` (one cell of one row). Test `tests/test_effects_len.py`.

**Interfaces:** consumes `analyze(ri, mode)`; produces no new names.

The row is **confirmed wrong** (M4 task 11, adjudicated by two parties against vendored source): `lvm.c`'s `OP_LEN` routes a `LUA_TTABLE` operand to `luaH_getn`, which reads `t->array` and calls `luaH_getnum` (`ltable.c`) — removing metamethod assumptions changes nothing (Lua 5.1 has no table `__len`). As graded, `PURE` under `NO_METAMETHOD` licenses reordering a `SETTABLE` across `#t`.

- [ ] **Step 1: differential sweep BEFORE the change.** Record `classify_registers`' four fields plus level/rung/refusal_reason for all 1944 occurrences (M4 task 8's sweep is the template — read its report of record in `docs/runbooks/m3-backlog.md` §"Regrade LEN"). Expected: no consumer selects `NO_METAMETHOD` today (`test_strict_is_the_default_and_the_only_mode_in_use` pins it), so **the differential should be null**; if it is not, stop and report.
- [ ] **Step 2: failing test** — `analyze(LEN_ri, EffectMode.NO_METAMETHOD).effect is Effect.READ_HEAP` (currently `PURE`); plus a test pinning that `STRICT` and `TRUSTING` cells are untouched, and that the pre-existing 45-row exhaustive table (`tests/test_effects.py`) needs exactly one cell updated.
- [ ] **Step 3: apply, with the `lvm.c`/`ltable.c` citations in the row comment** (verify line ranges against the vendored file — the ranges above are from M4 and must be re-checked). Update the mode-column census tests from M4 task 11 (`NO_METAMETHOD`'s `# UNARGUED` count drops 1→0; the 20/18 entailment split moves — re-derive, don't arithmetic it).
- [ ] **Step 4: sweep after; diff; ledger.** Expected null differential and byte-identical ledger. Record the result in the test docstring. Full suite green.
- [ ] **Step 5: commit** (`fix: M5 task 1 -- LEN at NO_METAMETHOD is READ_HEAP, null differential`). Strike M5 agenda item 1 with the commit hash.

---

### Task 2: Process-level certification memo — buy the suite headroom first

**Files:** Modify `src/pyluadec/structure/structured.py` (memo scope), `tests/conftest.py` (session cache wiring). Test: existing suite + a new invalidation test in `tests/test_structured_certify.py`.

**Interfaces:** consumes `_memo_key(proto)` (= `structural_hash` + `_debug_fingerprint`, proven to cover every field `compare_protos` reads); produces a session-shareable certification cache.

Measured (M5 agenda item 12): `emit_certified_chunk`'s memo is per-chunk while the corpus holds 1478 unique `_memo_key`s over 1944 protos; `test_ledger_ratchet` (~11.7s) and the behaviour-probe setup (~10.0s) are 54% of a 40s wall against a 45s ceiling, and a review has already ruled neither may be *sampled*. Caching is the only lever.

**Binding invariants:**
1. The cache key is `_memo_key` — **nothing weaker**. The unsoundness of `structural_hash` alone is documented at `_debug_fingerprint`'s docstring and measured (16 of 1478 shash groups carry >1 fingerprint).
2. Cache correctness is proven, not assumed: a committed test constructs two protos sharing `structural_hash` but not `_debug_fingerprint` (the M3 task 7 grafted-pair fixture is the template) and asserts independent verdicts **through the process-level cache**.
3. **The ledger must not change.** The cache changes who pays, not what is computed.
4. The cache must not leak across oracle rebuilds: key includes the oracle identity (`git log -1 --format=%H -- vendor native` — the same value the ledger's `oracle` field uses, read once).
- [ ] Steps: failing invalidation test → implement (module-level dict in `structured.py`, or a conftest fixture handing the dict in — implementer's choice, stated) → measure `test_ledger_ratchet` and full-suite wall before/after → ledger byte-identity check → commit with both timings in the message. **Target: ≥6s recovered** (estimate from agenda item 12's ~24% subprocess figure — re-derive; if the recovery is materially less, report the measured number and why).

---

### Task 3: Port the predecessor's quality metric — the exit instrument

**Files:** Create `src/pyluadec/verify/semantic_score.py`, `tests/test_semantic_score.py`, `scripts/quality_score.py` (CLI).

**Interfaces:**
- Consumes: `pyluadec.ingest.load_file`/`load_bytes`, `oracle.compile_source`, `pipeline.decompile_file`.
- Produces: `score_protos(original: Proto, candidate: Proto) -> FileScore` (per-proto weighted similarities + weighted file score, mirroring the predecessor's `_classify_file`), and `scripts/quality_score.py` printing per-file and corpus-average scores.

Spec §1 goal 4 and §7 M5's exit both cite the predecessor baseline: **avg_score 0.997** under `semantic_eval.py` — a weighted counter-similarity over proto signatures (opcode families, global reads/writes, call targets/shapes, return arity, constant fingerprint; weights in `_classify_file`, e.g. `const_fingerprint 0.10`). The original is 546 lines of pure Python over proto dicts at `/Users/fotile96/pyluadec/pyluadec/semantic_eval.py`, on this machine — **read it and port the metric faithfully** (mechanism-equivalent rewrite over our `Proto`; spec §8's rule). It cannot run here itself (32-bit bridge), which is exactly why the port is the only apples-to-apples instrument.

**Binding invariants:**
1. **Port fidelity is the deliverable.** Same signature fields, same weights, same normalization of constants (`_normalize_const` — note it stringifies; our port must produce identical strings for identical constants, from `bytes`/`LuaNumber` payloads **without decoding corpus text** — hex-tag non-UTF-8 bytes exactly as the predecessor's dict-based pipeline would have seen them; where the predecessor's bridge lossily converted (numbers→float), document the divergence rather than replicating the loss).
2. Two calibration tests: identical protos score 1.0 on every component; the M2 fallback output of a structured-certifying file scores **< 1.0** (the metric must be able to see the difference certification sees — if it cannot, say so; that is a finding about the metric, not a licence to tune it).
3. First measurement, in the report and the runbook: corpus average at M5 start, per-file table for the 17 fallback files. Sets the baseline every later task's re-measurement is compared against. **Do not assert it will already exceed 0.997** — measure it.
- [ ] Steps: calibration tests red → port → green → corpus run (CLI; not in the committed suite — one full decompile+score sweep, report its cost) → one committed smoke test (3 small files, budget ≤1s) → commit.

---

### Task 4: Close the structure-refusal leaves (30: else-join 11, unreachable 9, if-targets 9, while-header 1)

**Files:** Modify `src/pyluadec/sir/build.py` (and `express/reconstruct.py` only if diagnosis demands). Test `tests/test_sir_longtail2.py`.

Diagnose-first, per cluster, smallest exemplar first (grounding table above). The refusal messages name the *symptom*; M4's experience says the causes will regroup once measured. Known context per cluster:

- **else-join out of range (11)** and **if targets out of range (9)**: jump-threading interactions at region boundaries. `snr_common.lua:main_68` (22 insns) and `main_74_12` (102) are the entry points. One of the two pinned semantic-regression cases (`test_if_and_elseif_conjunctions_preserved`, nested AND inside an elseif chain) sits in the if-targets cluster — **closing it flips that test's `== "L1"` assertion on purpose**; update the test in the same commit, per its docstring.
- **branch body block unreachable (9)**: `snr_common.lua:main_59` (17 insns) — dead code inside an if arm following a `return`. M3 deliberately refused these; decide per-shape whether a `Dead`-region claim (printing nothing certifies only if luac re-emits the dead code — it will, from the same source — so the shape needs the dead statements *printed*, which means recognizing them as unreachable-but-claimed straight code) is sound. The certification gate adjudicates.
- **while-header statements (1)**: `snr_novel.lua:main_13` — a `While` whose header reconstructs to statements (the guard added in M4 task 13). Needs header-statement hoisting or a `WhileTrue`+`If` re-expression that certifies; measure which.

**Binding invariants:** pc-claim exactness; recognize-or-refuse; every new guard neuter-proven; ledger upgrades-only, regenerated per commit with before/after in the message; **no floor tests adjusted toward achievements**.

- [ ] Steps per cluster: diagnosis script (output into fixture comments) → oracle-compiled failing fixtures asserting `all_claimed` + `L3` → implement → corpus + ledger → commit. Report the residual honestly — clusters that resist get their resistance documented with the shape, not forced.

---

### Task 5: Close the mismatch/reconstruct leaves (37: maxstacksize 18, code 15, consumed-read 3, and/or-alt 1) + the pool-order decision

**Files:** Modify `src/pyluadec/express/names.py` / `express/reconstruct.py`. Test `tests/test_express_residual.py`.

The `mismatch:` clusters are register/reconstruction fidelity residue — the same class M4 task 13 reduced from 253 to 4 `MOVE`-only plus these. Known hard case: `snr_common.lua:main_77_0` (5 insns, `mismatch: code`) is a **genuine upvalue-index divergence** found at the M4 final review — start there, it is the smallest and the most likely to be a distinct mechanism. `snr_s5_10_s.lua:main_43`'s consumed-read cluster is the refusal M4 task 13 measured reachable on exactly 3 real protos.

The second pinned semantic-regression case (`test_counter_closure_and_dispatch_mix`, maxstacksize 18 vs 20 + constants 13 vs 15) sits in the maxstacksize cluster — closing it flips that pin on purpose.

**Fold in: the `L3.2` constant-pool-order rung, decided by data (M5 agenda item 4 — declined at 9, declined again at 10; a third re-measurement without a decision is waste).** After this task's fixes, re-measure the differ-only-by-pool-order population with the exact method committed in `structured-pipeline.md`. **Decision rule, stated now:** ≥20 → design the rung with its soundness argument (a pool permutation is meaning-preserving iff every RK/Bx reference is remapped by the same permutation and no instruction depends on an index's numeric value), `LADDER_VERSION` bump, isolating tests. <20 → **close the item permanently** with the final number, recorded in the runbook as decided-not-doing.

- [ ] Steps: re-cluster first (the 33+4 will have moved if Task 4 landed) → smallest-exemplar fixtures red → fix per cluster, commit per cluster with corpus movement → pool-order measurement and decision → honest residual table for Task 6.

---

### Task 6: Hybrid chunk emission — no whole-file state machine survives

**Files:** Modify `src/pyluadec/structure/structured.py` (assembly), `src/pyluadec/structure/fallback.py` (per-function emission entry — it already emits functions as `__pld_F` factories; verify and reuse), `scripts/run_corpus.py` + `verify/ledger.py` (schema: per-chunk `hybrid` flag; confession scoped to the protos actually shipped as fallback), `scripts/ledger_dashboard.py`. Test `tests/test_hybrid_chunk.py`.

**Decision (human partner, 2026-08-12):** in scope, as its own task, after residual closure — it handles whatever Tasks 4–5 leave.

**The new shipping invariant (replaces "artifact structured ⟺ root L3"):**

> Every proto in a shipped artifact is EITHER the exact bytes its certification compiled (`ProtoCert.source`, level `L3`) OR emitted by the semantically-exact fallback, and the ledger row for each proto says which. A proto's own certification level is unchanged by how its neighbors ship. The assembled chunk must itself compile (`oracle.compile_source` succeeds), and the fallback-emitted protos carry their confession exactly as before.

Design constraints (properties, not mechanisms — the implementer picks the composition):
1. At a `CLOSURE` site whose subtree did not certify, the structured printer must not guess — the composition point is where the certified/uncertified boundary lives. The fallback already has a per-function form; whether the hybrid embeds it as a `__pld_F`-style factory expression, a local function with the state-machine body, or hoists it, is the implementer's design — **adjudicated by: the chunk compiles, the behavioural probe (L1.75) agrees, and the global-state probe (L1.5) agrees for that file**.
2. Certified subtrees embedded in a hybrid ship the **same bytes** `certify_proto` compiled (the "shipped == certified" discipline, per-proto now).
3. The two standing probes are the semantic gate for hybrids (certification cannot bless a hybrid whole — its fallback parts are not byte-exact by construction). Both probes must run over all 229 files in the corpus gate and agree. Expected: the pins shrink again (the `snr_novel` table-layout pin may close if its `pairs` loop lands in a certified subtree — M5 agenda item 5 says this item shrinks as closure progresses; measure and update the pins two-directionally).
4. **Rollout is measured:** report per-file structured-proto fraction before/after; the readability report's 47.6%-by-volume figure is the target metric — re-measure it. `docs/reports/` gets the number.
- [ ] Steps: invariant test red (a file with one uncertifiable proto ships hybrid; the uncertified proto's text is the fallback's; the certified siblings' text is byte-equal to their `ProtoCert.source`; the chunk compiles; both probes agree) → implement assembly → schema + dashboard → corpus + ledger regenerated (schema change, reviewed as such) → non-vacuity: fault-inject (make a certified proto's stored source wrong → the byte-equality test fails; make the fallback part semantically wrong → a probe fails) → commit.

---

### Task 7: Readability — elseif, dot sugar, unary minus, indentation, and the presentation-layer decode

**Files:** Modify `src/pyluadec/emit/lua.py`. Test `tests/test_emit_readability.py`. CLAUDE.md (the bytes-rule amendment, exact wording below).

**Decision (human partner, 2026-08-12):** presentation-layer decode in scope. Downstream-coupling: the old `post_process/` chain is **already incompatible** (`v\d+` naming broken by our `l0_0`), and CLAUDE.md licenses a versioned new surface — record "output surface v2" in the runbook rather than preserving v1 quirks.

Five changes, each **individually proven certification-invariant** (the ledger must be byte-identical after each — that is the definition of a presentation change; a change that moves the ledger is mis-scoped and must be reported):

1. **`elseif`**: an `If` whose else-arm is exactly one `If` prints `elseif`. Identical bytecode by construction (Lua 5.1 compiles `elseif` and nested `if`-in-`else` to the same code — verify against `lparser.c::ifstat` before asserting). Measured stake: 208 occurrences; max nesting 61 → predecessor's 5.
2. **Dot sugar**: `t["k"]` → `t.k` when `k` is a valid identifier and not a keyword (`_ident`'s test, reused in reverse). Also method-ish chains `a.b.c`.
3. **Unary minus**: `(-1)` → `-1` where precedence allows (the printer's precedence table already exists; extend, don't special-case).
4. **Indentation**: uniform 4-space, function bodies included. This is the "output surface v2" break — one line in the runbook.
5. **Presentation-layer string decode**: in `str_lit`'s presentation path only — if the byte sequence decodes as UTF-8 **and** re-encodes to the identical bytes, print it raw inside the double-quoted literal (escaping only what Lua requires: `"` `\` newline and control bytes); otherwise keep decimal escapes. The round-trip condition is the documented fallback. **CLAUDE.md amendment to land verbatim in the red-line bullet:** "字节红线适用于 ingest/lift/比对层；打印层允许做**有回退的呈现判定**（UTF-8 可逆则原样输出，否则十进制转义）——两种写法编译出相同常量，认证门裁决不变性。" Non-UTF-8 fixtures required (corpus has them; also synthesize one).

- [ ] Steps per change: readability fixture (asserts the printed text) + certification-invariance check (targeted: recompile the fixture, `compare_protos` clean; corpus-wide: ledger byte-identity after the change) → implement → commit per change. After all five: re-run the readability comparison (Task 12 will publish it) and the two probes (raw UTF-8 in source must not perturb them — the probes compare runtime behaviour, but verify).

---

### Task 8: Full ratchet CI — baseline diff, downgrade = fail (spec §5's complete form)

**Files:** Create `scripts/ratchet_diff.py`, `tests/test_ratchet_diff.py`; modify `scripts/run_corpus.py` (ledger key split — see below), `.github/workflows/` **only if** a CI runner config already exists (check; otherwise the runbook documents the manual invocation and `git bisect` wiring).

M5 agenda item 2, verbatim scope. What exists: fixed-point, within-row coupling, rate floors. What does not: **any comparison against a committed historical baseline** — a regenerated ledger with fewer `L3` rows passes everything today, and both known tripwire gaps (census floor at measured−10; exit floor 9 points under achieved) are closed by the same instrument.

1. `scripts/ratchet_diff.py OLD NEW`: exit non-zero on any per-row level downgrade, rung downgrade, removed row, `refusal_reason` regression (an `L3` row acquiring one), or hybrid-flag regression (Task 6's schema); print the offending rows with their `refusal_reason` clusters. Upgrades and schema-annotated changes pass with a summary. This is the `git bisect run` predicate — document the exact bisect invocation in the runbook.
2. **Fold in the ledger-key soundness fix** (agenda item 2's second half): `run_corpus.py` groups by `structural_hash` alone with max-by-rank; either split the key to `_memo_key` or pin "no shash group disagrees on (level, rung)" as an assertion — this moves or annotates the committed artifact **once**, reviewed as a key change. Measured basis: 16/1478 groups carry >1 fingerprint, 0 disagree today.
3. **Fold in the full generated sweep** (`PYLUADEC_GENERATED_CASE_LIMIT=24`) as part of the ratchet job, not the per-commit suite.
4. Non-vacuity: committed test feeds `ratchet_diff` a hand-downgraded ledger copy and asserts it fails naming the row; feeds an upgraded one and asserts it passes.
- [ ] Steps: red (diff script absent) → implement → key decision + one reviewed ledger movement (or pin) → wire + document → commit.

---

### Task 9: The L2 gate — key-sequence-driven differential execution with taint and coverage

**Files:** Create `scripts/probe_keyseq.lua`, `scripts/probe_keyseq.py`, `tests/test_l2_keyseq.py`; modify `verify/ledger.py` + `scripts/run_corpus.py` (schema: `l2` field, `L2@cov%` form) and `scripts/ledger_dashboard.py`.

Spec M5 proper (§5's L2 row): differential execution — original bytecode and our artifact run in the same stub environment, driven by the **same scripted key sequence**; trace equality grants `L2@cov%` with a branch-coverage badge; stub introspection marks taint, and **taint reaching a branch decision refuses the grant**. The M4 behaviour probe is the base (determinism guards, event-count budget with instruction backstop, shadow tables, `bytes` payloads, SHA-256 comparison units); its measured ceiling — the 3000-event cap truncating 132/229 files mid-loop — is exactly what key-sequence driving addresses: the game loops block on input, and scripted input walks them.

Design properties (mechanisms are the implementer's, adjudicated by the committed tests):
1. **Key delivery**: the predecessor's harness (read `DEBUG_KEY_SEQUENCE_HARNESS.md` — on this machine under `/Users/fotile96/pyluadec/pyluadec/`) documents how the scripts poll input; stub the polled function(s) to return a scripted sequence, then exhaust to a quit/idle key. Sequences live in the test as data.
2. **Trace** = the behaviour probe's event stream (calls + args + writes), byte-compared.
3. **Coverage**: fraction of the proto's basic blocks entered during the run (the CFG layer already exists — count entered blocks per proto via a line-hook mapping or an entered-set the stub env accumulates; state the mechanism chosen and its cost). Badge lands in the ledger as `l2: {"cov": 0.xx}` on rows whose file passed.
4. **Taint**: any stub value flowing through `type`/`rawequal`/`getmetatable`/comparison-against-stub marks the run tainted at that point; a tainted value controlling a branch (the condition register of a TEST/EQ/LT/LE that decides a taken/not-taken difference — approximate conservatively) refuses `L2` for that file with a `taint` reason. Conservative over-refusal is acceptable and honest; silent under-refusal is not (this is spec risk R2).
5. **Budget**: event-count with instruction backstop (the measured M4 design finding — an instruction budget alone destroyed agreement 226→95).
6. Non-vacuity: committed fault injections (arithmetic swap must diverge the trace; a taint-laundering fixture must be refused).
- [ ] Steps: harness red on a synthetic menu-loop fixture (a small Lua script that polls a key, branches, writes globals) → implement probe + taint + coverage → run over the corpus files the key sequences apply to (start with the two checkpoint files; corpus-wide L2 is NOT promised this milestone — report reach honestly) → schema + dashboard → commit.

---

### Task 10: The two historical key-sequence checkpoints as standing regressions

**Files:** Create `tests/test_keyseq_checkpoints.py`.

Spec §7 test item 3's last clause, deferred through two milestones, now unblocked by Task 9:
1. **`SystemOption.OptionMain` double clamp** — the two clamps are mutually exclusive; the historical bug broke one.
2. **`SystemConfig.ConfigMain` CIRCLE branch gate/wait** — the CIRCLE branch must keep its gate/wait behaviour.

Port from the predecessor's `DEBUG_KEY_SEQUENCE_HARNESS.md` playbook (read it; the checkpoints are described as key sequences plus expected trace properties). Each becomes: drive the **original bytecode** and **our shipped artifact** for the named file with the checkpoint's key sequence through Task 9's harness; assert trace equality **and** the checkpoint's specific property (the clamp exclusivity / the gate-wait presence) as an explicit assertion on the trace, so the test fails meaningfully even if both sides regress together.

- [ ] Steps: red (harness drives, property assertions unwritten) → port sequences and properties → prove each load-bearing (inject the historical bug's shape into a copy of our artifact source → the named test fails; both-sides-regress guard: assert the property on the ORIGINAL's trace too) → measure cost (budget ≤2s; these are two files, not a sweep) → commit.

---

### Task 11: Extract `_stack_discipline` (M5 agenda item 7) — pure refactor behind the gate

**Files:** Modify `src/pyluadec/express/names.py` (possibly splitting a `names_barriers.py` sibling — implementer's structure choice, stated). Tests: existing suite is the harness.

Measured (re-derive): `_stack_discipline` is 462 lines / 33 `if`s / 11 nested closures inside an 831-line module — 56% of it — and it is the most load-bearing code in the project (+63.6 points). The extraction is safe **because** the gate refuses behaviour change: the acceptance test is *corpus invariance*.

**Binding invariants:** the ledger is byte-identical after; `classify_registers`' public contract unchanged; each extracted barrier keeps its docstring's measured claims attached (they were individually verified in M4 reviews — moving them must not orphan the evidence); the four barriers that have neuter-proof tests keep them passing unmodified.
- [ ] Steps: characterize (run the four barrier neuter-tests, confirm red/green before touching anything) → extract in ≤3 commits, ledger-checked each → full suite + timing (must not regress the Task 2 recovery) → commit.

---

### Task 12: Documents of record, minors sweep, quality report, M5 exit

**Files:** Modify `CHANGELOG.md`, `CLAUDE.md` (M5 section + the two standing amendments: bytes-rule presentation clause, registry retirement), `docs/runbooks/structured-pipeline.md` / `decompile-pipeline.md` / `m3-backlog.md` (M5-completed items struck with commits; remainder becomes the M6 agenda seed), `docs/reports/m5-quality.md`. Finalize `tests/test_m5_exit.py`.

**The registry retirement is recorded here** in the spec decision log (append to `docs/superpowers/specs/…overall-design.md` §2's decision table with date and rationale — the certification gate subsumed the Pass protocol's verify/rollback/confession duties; plugin surface deferred to an M6+ client).

**Minors sweep** — agenda items 8 (add `Mismatch.path` to `refusal_reason` — schema change, fold with any Task 6/8 ledger movement), 9 (a synthetic fixture exercising the `compile:` vocabulary), 10 (the six test-hygiene items, with the suite-time measurement pass they were deferred for), 11 (probe minors: fix the cheap ones, re-defer the future-corpus traps with reasons), 14 (M2/M3 inherited minors: fix `ingest/dispatch.py`'s try-scope and `cfg/dom.py`'s recursion-limit mutation; decide-or-re-defer the rest, none silently dropped). Each: fixed / re-deferred with one line / closed-as-wrong with the measurement.

**`docs/reports/m5-quality.md`** — the milestone's evaluation:
1. The ported metric's corpus average vs the **0.997 baseline**, per-file table, and the honest note about any file below baseline.
2. Structured coverage by volume (the 47.6% figure re-measured post-hybrid).
3. Readability deltas from Task 7 (nesting depth, `elseif` counts, dot-sugar counts, a UTF-8 sample side-by-side with the predecessor).
4. L2 reach: which files carry `L2@cov%`, at what coverage, and the taint-refusal count.

### AMENDED 2026-08-12 — the exit criterion was re-scoped, by the human partner's decision

**What was measured.** Task 3 ported the predecessor's metric and Tasks 4–6 moved it: **0.935633 → 0.946390 → 0.950580 → 0.968833**, with 17 → 7 files still shipping a whole-file state machine. The arithmetic then closed off the original gate: with 216 files at exactly 1.000000, the remaining 13 must average **≥0.947**, and even converting all 7 remaining fallbacks to hybrids *at the current hybrid quality of 0.816791* reaches only **0.9896**. Clearing 0.997 requires essentially every file at ~1.0 — i.e. closing the reconstruction residual, not just changing how chunks are assembled.

**What remains, diagnosed** (this is now M6's agenda, not hand-waving): **13 compound-`if` refusals** — one defect, needing a condition tree in `regions.If`, with a committed 26-instruction repro at `tests/test_sir_longtail2.py::COMPOUND_CONDITION_EXEMPLAR` — and **4 root reconstruction defects** that hybrid emission *unmasked* (their certification previously died on a descendant's refusal before any comparison ran), of which `snr_music.lua`'s main is adjudicated: it collapses four distinct nested table constructors into one aliased table, the same `classify_registers` temp-as-local family as `snr_common.lua`'s consumed-register read.

**The decision** (human partner, 2026-08-12): **re-scope M5's exit to metrics already on track, and carry 0.997 to M6 as its exit.** This modifies a spec §1 goal-4 acceptance criterion that was confirmed section-by-section with the user, so Task 12 must record it in the spec's decision log with this rationale — not merely in a runbook.

**`tests/test_m5_exit.py`** — floors are commitments, **not** measurements; each sits deliberately below its achieved value so legitimate variation does not trip it, and each states its achieved value in the assert message:

```python
def test_m5_exit_quality_no_regression(scored_corpus):
    # M5 start 0.935633 -> achieved 0.968833. NOT the predecessor's 0.997:
    # that is M6's exit (see the spec decision log). This floor pins that M5's
    # gain is not lost, and it is what the ratchet diff (Task 8) enforces
    # per-row rather than in aggregate.
    assert scored_corpus.average >= 0.96

def test_m5_exit_structured_reach(ledger_rows):
    # Proto occurrences shipping structured text: 70.9% -> 89.9% achieved.
    occ = [o for r in ledger_rows for o in r["occurrences"]]
    structured = sum(1 for o in occ if o["shipped"] == "structured")
    assert structured / len(occ) >= 0.85

def test_m5_exit_l3_no_regression(ledger_rows):
    # M4 exit 94.0% -> achieved 96.8% unique.
    l3 = sum(1 for r in ledger_rows if r["level"] == "L3")
    assert l3 / len(ledger_rows) >= 0.96
```

**Field names must be confirmed against the Task 6/8 schema when finalizing — read them, don't guess** (Task 6 redefined `fallback` and added per-occurrence `shipped`/`hybrid`).

**Exit checklist (verify each in-tree, evidence per item):** quality ≥0.96 with the achieved value reported · structured reach ≥85% of occurrences · L3 ≥96% unique · both key-sequence checkpoints green · L2 badge on ≥ the two checkpoint files · ratchet diff wired and non-vacuous · suite ≤45s with `--durations` recorded · docs current, every number measured-or-cited · **the re-scope recorded in the spec decision log with the 0.997-to-M6 carry and its diagnosed agenda** · milestone wrap via superpowers flow (controller's step).

**Report the whole-file-fallback count as data, not as a gate.** It went 17 → 7 and the 7 are blocked on their own root protos, which a hybrid cannot substitute; gating on zero would be gating on M6's work.

---

## Explicit non-goals (M6+, recorded so they are not re-litigated)

- **Corpus-wide L2** — Task 9 lands the instrument and Task 10 the two checkpoint files; sweeping all 229 with per-file key sequences is M6 (needs sequence authoring per file).
- **GPU proposer, lparser/lcode instrumentation mining, Lua 5.2 ingest** — M6+ (spec).
- **Variable-name semanticisation** (`l0_0` → meaningful names) — corpus is stripped; still of questionable value.
- **Re-plumbing `post_process/`** to the v2 output surface — downstream is frozen on stage3 artifacts (CLAUDE.md); v2 is versioned, not reconciled.
- **The pass registry** — retired, not deferred (decision recorded in Task 12).
- **M1's Linux x86_64 verification** — still outstanding, tracked outside this milestone's scope; flag at wrap.

## Self-review notes

- Spec coverage: §7 M5 row → idiom closure = Tasks 4–5 (confession-ranking = the `refusal_reason` clusters), L2 gate = Task 9, key-sequence regressions = Task 10, baseline = Tasks 3 + 12 exit. §5 ratchet CI = Task 8. §1 goal 4 = Task 3/12. Agenda items 1→T1, 2→T8, 3→T4/5/6, 4→T5, 5→T6(probes), 6→T9/10, 7→T11, 8/9/10/11/14→T12, 12→T2, 13→T7.
- Type consistency: `FileScore`/`score_protos` (T3) consumed by T12's `scored_corpus`; `ProtoCert.source` byte-equality reused in T6; `_memo_key` in T2; ledger schema fields introduced T6/T8/T9 and consumed T12 with an explicit read-don't-guess note.
- Placeholder scan: none; diagnosis-first steps specify their concrete outputs.
- Numbers: all carry provenance; the 67/22 split and cluster table were measured this session and Task 4 Step 1 re-derives them as the standing census.

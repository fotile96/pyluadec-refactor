# M6: Cross-Corpus Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use the predecessor's human-verified 229-script corpus in both directions — our instruments hunt its unknown defects (查漏补缺); its verified structure feeds the closure of our two named defects.

**Architecture:** Three tracks behind a budget repair. Track 1: a cross-corpus differential harness (predecessor text → our oracle → layered comparison against original bytecode), preceded by a meta-observation pass that classifies difficult protos into two interaction classes and measures their surfaces. Track 2: structure-reference diagnosis + LLM meta-reconstruction over the ~20 leaf refusing protos. Track 3: close the compound-`if` and register-classification defects using Track 2's output. Certification remains the only judge; references and reconstructions are hints that can only fail to certify.

**Tech Stack:** existing `pyluadec` packages (`ingest`/`lift`/`cfg`/`sir`/`express`/`emit`/`verify`/`oracle`), `luac_sz4`/`lua_sz4` oracle binaries, the L1.5/L1.75/L2 probe family, pytest.

**Spec:** `docs/superpowers/specs/2026-08-13-m6-cross-corpus-validation-design.md` (committed `2a7efdd`). Baselines measured 2026-08-13 at master `0957364`.

## Global Constraints

- **Certification logic untouchable:** `NORMALIZATIONS`, `LADDER_VERSION`, `compare_protos`, `_cmp`, `structural_hash`; `key_disagreements` unchanged. Never relax a comparison, floor, or gate to make something pass.
- **`corpus/ledger.jsonl`** written only by `scripts/run_corpus.py`; any movement goes through `scripts/ratchet_diff.py` vs the M5 merge baseline (`0957364`) with 0 downgrades. **`corpus/golden/` read-only; `vendor/` pristine.**
- **Bytecode-derived strings stay `bytes`** in ingest/lift/cfg/verify/comparison layers; the scoped exception is `emit/lua.py::_str_lit`. Committed observation data may carry **ASCII identifier** strings only (the precedent: probe pins already name `doScriptScene`, `memoryFlag`); non-ASCII constants are excluded, never decoded.
- **No `re`** in `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}` (statically enforced); no Lua patterns in probes (`sfind` with `plain=true` only).
- Corpora only via env vars: `PYLUADEC_CORPUS_DIR` (original bytecode; here `/Users/fotile96/pyluadec/others/script_to_decompile`), **`PYLUADEC_PRED_CORPUS_DIR`** (predecessor text; here `/Users/fotile96/Zndnovel/lua_scripts`). Missing ⇒ `pytest.skip`, mirroring `tests/conftest.py::corpus_dir`.
- **Suite ceiling 45s.** Full cross-corpus scans are **jobs** (script CLIs, `ratchet_job.sh` pattern), never default-suite members; the suite gets gated smoke subsets.
- **No 0.997 gate** (human partner, 2026-08-13; Task 13 records the decision-log row). Quality score stays a dashboard observable.
- **Standing lessons bind every task**: every number in this plan is a hypothesis measured 2026-08-13 at `0957364` — re-derive before relying on it, and if it does not reproduce the measurement wins and you report it. Every new guard: neuter → named test red → restore → green, or label `DEFENSIVE` with what was tried. Measure every behavioural sentence you write, including ones no test asserts — superlatives ("only", "all", "cannot", "complete") each need a measurement or a rewording.

## Baseline numbers (measured 2026-08-13 at `0957364` — re-derive at task start)

Suite 867 tests, 44.07–44.85s over four runs (ceiling 45s, **budget exhausted**). 13 files below the predecessor baseline: 7 whole-file fallback (`snr_mainmenu` 0.075, `snr_memory` 0.104, `snr_graphic` 0.126, `snr_novel` 0.147, `snr_music` 0.154, `snr_common` 0.174, `config` 0.181), 6 hybrid (`snr_story_main` 0.457, `snr_fragment_main` 0.659, `snr_s4_10_s` 0.926, `snr_s3_10_s` 0.931, `snr_s1_10_s` 0.957, `snr_s5_10_s` 0.971). 48 non-`L3` unique shapes: `structure` 21 / `mismatch: maxstacksize` 11 / `mismatch: code` 11 / `reconstruct` 5; ~20 leaf refusal sites, 8–3305 insns. Predecessor text: 13/13 gap files compile under `oracle.compile_source`, proto trees match 1:1 (snr_common 147=147), **not** byte-exact (snr_common 390 substantive rung-1 mismatches over 106 paths; snr_s4_10_s 308/81; minimum snr_story_main 17/5).

---

### Task 1: Suite-budget repair

**Files:**
- Modify: `src/pyluadec/oracle.py` (memoize `compile_source`)
- Modify: `pyproject.toml` (register a `corpus_slow` marker)
- Modify: `tests/test_generated_semantic_cases.py`, `tests/test_behaviour_probe.py` (marker only if needed after measurement)
- Test: `tests/test_oracle_memo.py`

**Interfaces:**
- Consumes: `oracle.compile_source(source: bytes, *, strip: bool = False) -> bytes` (no cache today; verified at M5 final review — `tests/test_corpus_compile.py` and `tests/test_m5_exit.py` compile the identical 229 sources in separate passes).
- Produces: same signature, process-level memo keyed `(sha256(source), strip)`. Later tasks assume repeated `compile_source` of identical bytes is ~free.

- [ ] **Step 1: measure the baseline.** Three timed full-suite runs with corpus; record `--durations=15`. Expected ballpark 44–45s (re-derive; do not copy).
- [ ] **Step 2: failing test.**

```python
# tests/test_oracle_memo.py
"""The memo is process-level, keyed on content, and invisible in results."""
import time
from pyluadec import oracle

def test_recompiling_identical_bytes_hits_the_memo():
    src = b"local x = 1\nreturn x\n"
    a = oracle.compile_source(src)
    t0 = time.perf_counter()
    for _ in range(50):
        b = oracle.compile_source(src)
    dt = time.perf_counter() - t0
    assert b == a
    assert dt < 0.05, f"50 memo hits took {dt:.3f}s -- not memoized"

def test_strip_variants_do_not_collide():
    src = b"local y = 2\nreturn y\n"
    assert oracle.compile_source(src) != oracle.compile_source(src, strip=True)
```

- [ ] **Step 3: red** (`dt` assertion fails — 50 subprocess spawns are not <50ms).
- [ ] **Step 4: implement.** Module-level `dict[tuple[bytes, bool], bytes]` guarded by content hash; keep the subprocess path as the miss branch. No size cap needed (229 sources ≈ small MBs) — state that as a measured decision, not an oversight.
- [ ] **Step 5: green; full suite; measure again.** Three timed runs. Report the delta. If the suite is not comfortably under 45s (target ≤42s), split the heaviest corpus arms behind a `corpus_slow` marker run by `ratchet_job.sh` gate 1 but not the default suite — and document the new "all tests" invocation in CLAUDE.md.
- [ ] **Step 6: neuter proof** (empty the memo dict permanently → `test_recompiling_identical_bytes_hits_the_memo` red; restore). **Step 7: commit.**

### Task 2: Predecessor corpus plumbing + corpus-wide parity census

**Files:**
- Create: `src/pyluadec/predcorpus.py`
- Modify: `tests/conftest.py` (add `pred_corpus_dir` fixture, session-scoped `pred_compiled` cache, terminal-summary note)
- Test: `tests/test_predcorpus.py`

**Interfaces:**
- Consumes: `oracle.compile_source` (memoized, Task 1), `ingest.load_bytes`, `ingest.load_file`.
- Produces: `predcorpus.load_pred_proto(pred_dir: Path, name: str) -> Proto` (compile + ingest, memo-backed); `predcorpus.tree_paths(p: Proto) -> list[str]` (the `main`/`main_N`/`main_N_M` path convention already used by the ledger — reuse `pipeline.walk_proto_paths` if its signature fits; check before writing a twin).

- [ ] **Step 1: failing test** — `load_pred_proto` compiles `snr_common.lua` from `PYLUADEC_PRED_CORPUS_DIR` and its tree has 147 protos with paths matching the original's exactly.
- [ ] **Step 2: implement.** Skip-if-unset fixture per the `corpus_dir` precedent.
- [ ] **Step 3: the census (this is the task's real deliverable).** Script arm inside the test file (corpus-gated): over **all 229** files — compile-ok count, tree-match count, and per-file substantive rung-1 mismatch counts (excluding debug fields `source`/`lineinfo`/`locvars`/`upvalue_names`/`linedefined`/`lastlinedefined`). The 13-file numbers above were measured; **the other 216 are unmeasured** — this census is the first corpus-wide look. Pin only what the measurement supports (e.g., `compile_ok == 229` if true; if any file fails to compile, that is a finding to report, not to force).
- [ ] **Step 4: commit** census summary into the task report; raw per-file table into `docs/reports/m6-cross-corpus.md` §1 (create the file with just this section; later tasks append).

### Task 3: Interaction-surface extractor (static footprint)

**Files:**
- Create: `src/pyluadec/lift/footprint.py`
- Create: `scripts/footprint_dump.py` (CLI; writes `corpus/observation/footprints.json`)
- Test: `tests/test_footprint.py`

**Interfaces:**
- Consumes: `lift.lift_proto` (LIR), `cfg.build_cfg`, the constant pool (`bytes` values).
- Produces: `footprint.proto_footprint(fn) -> Footprint` where `Footprint` is a frozen dataclass: `global_reads: frozenset[bytes]`, `global_writes: frozenset[bytes]`, `table_key_reads: frozenset[tuple[bytes, bytes]]` (base-global-name, key) for `GETGLOBAL g; GETTABLE d, g, K[k]` shapes and `SELF`, `table_key_writes` likewise, `calls: frozenset[bytes]` (called global names), `dynamic_reads: int` (count of table reads whose key is **not** a constant — the honesty counter: the spec's "keys are almost always string constants" is a hypothesis this field tests corpus-wide).

- [ ] **Step 1: failing tests** on synthetic sources (compile with `oracle.compile_source`): a chunk reading `gameSave.startMenuState` yields `(b"gameSave", b"startMenuState") in table_key_reads`; a computed-key read (`t[k]` with `k` a local) increments `dynamic_reads` and lands in no set; a `SELF` call site attributes both the key and the call.
- [ ] **Step 2: implement.** All values stay `bytes`; **no decoding anywhere in this module** (it sits inside the guarded packages — the static `re` ban covers it automatically; confirm `GUARDED_PACKAGES` picks it up since it scans by package, not by file list).
- [ ] **Step 3: the dump CLI.** JSON with ASCII-identifier keys only: a name is emitted verbatim iff `all(0x20 <= b < 0x7f)` and it matches Lua identifier shape; anything else is emitted as `{"nonascii": <hex>}` — never decoded. Fixed-point discipline: regenerating must be byte-identical (test asserts it, ledger-ratchet style).
- [ ] **Step 4: corpus measurement** (the number the spec's Class-1 feasibility rests on): over all 1944 protos — distribution of `dynamic_reads` (hypothesis: overwhelmingly 0), size distribution of `table_key_reads` per proto. Report both; they decide Task 7's enumeration strategy.
- [ ] **Step 5: commit** (`corpus/observation/footprints.json` committed; it is generated data with the same regeneration discipline as the ledger).

### Task 4: Meta-observation pass (Track 1.0)

**Files:**
- Create: `docs/reports/m6-observation.md`
- Create: `corpus/observation/classes.json` (per-proto class assignments, generated + committed)

**Interfaces:**
- Consumes: Task 3's footprints; the 48-shape refusal census; `build/decompiled/` fallback text (regenerate first — it has been left stale by past sessions); predecessor source files.
- Produces: for every difficult proto (the ~20 leaves + the 132 event-cap files' dominant protos): class assignment (`choice-branch` / `ui-keyloop` / `neither`), interaction surface (stub-call set + table-key read set from Task 3), and for class-1 protos the **measured input-space size** (per read key: value domain observed from corpus writes to that key — boolean/small-int/string/unbounded).

This task is dispatch-shaped: the controller sends subagents to read listings and classify; the plan binds the **deliverable schema**, not the reading order.

- [ ] **Step 1: mechanical pre-pass** (script, committed with the report): candidate protos = the 20 leaf refusals + per-file dominant protos of the 132 CAP files; join against footprints; emit draft `classes.json` with surface data filled and class `null`.
- [ ] **Step 2: subagent observation rounds** fill the class and input-space fields, with a one-paragraph justification per proto in `m6-observation.md`. Class assignments must cite evidence (a `pressButton` poll reached / a choice-stub call / neither).
- [ ] **Step 3: the two Class-2 pre-measurements the spec's risk section demands:** (a) on 2–3 real UI protos, hand-cut the poll-loop body on both sides (original and predecessor-recompiled) and record whether the cut points correspond — the per-iteration-comparison design assumption; (b) input-space sizes for the class-1 population — how many protos are exhaustively drivable (product of domains ≤ a stated budget, e.g. 4096 combinations).
- [ ] **Step 4: commit.** `classes.json` regeneration-stable for the mechanical fields; observation fields frozen by review, not regeneration.

### Task 5: Cross-corpus scan harness — fingerprint + L1.5 + L1.75 arms

**Files:**
- Create: `scripts/cross_corpus.py` (CLI: `--arm fingerprint|state|behaviour|all`, `--file NAME`)
- Test: `tests/test_cross_corpus.py`

**Interfaces:**
- Consumes: `predcorpus.load_pred_proto`, `verify.semantic_score.score_protos(original, candidate) -> FileScore`, the probe drivers (`scripts/probe_global_state.py`, `scripts/probe_behaviour.py` — reuse their run functions; do **not** fork the Lua stubs), `probe_common.adjudicate_pins(divergent, pinned)`.
- Produces: `cross_corpus.scan(arm, files) -> dict[str, ArmResult]`; a **separate pin table `PRED_PINS`** (the spec forbids reusing our-side pins); report appended to `docs/reports/m6-cross-corpus.md`.

- [ ] **Step 1: failing smoke test** (corpus-gated, small): fingerprint arm on 3 named files returns scores; behaviour arm on 1 file returns a trace comparison; a synthetic divergence fixture (mutate one predecessor source in a temp dir, e.g. flip a numeric constant) is **caught** by the behaviour arm — the non-vacuity proof committed before the first full scan.
- [ ] **Step 2: implement the three arms** as thin orchestration over existing machinery. The predecessor side enters each probe exactly where our decompiled artifact does today (both are "candidate source vs original bytecode" runs — the probes are already two-sided).
- [ ] **Step 3: full scan as a job, not a test.** `PYLUADEC_CORPUS_DIR=… PYLUADEC_PRED_CORPUS_DIR=… uv run python scripts/cross_corpus.py --arm all` over 229 files; wall-clock reported. Suite keeps only the smoke subset.
- [ ] **Step 4: first divergence queue.** Every file where any arm diverges → a row: `(file, arm, evidence-pair)`, evidence restricted to opcode/pc/event-shape summaries (no game text). Expect engine-artifact noise (the risk section's prediction — the artifact rate is itself the first measurement); adjudication happens in Task 6.
- [ ] **Step 5: commit** harness + smoke tests + scan output summary.

### Task 6: Full-corpus scan + adjudication round 1

**Files:**
- Modify: `scripts/cross_corpus.py` (`PRED_PINS` filled), `docs/reports/m6-cross-corpus.md` (§divergence ledger)
- Test: `tests/test_cross_corpus.py` (pin-gate test in the `adjudicate_pins` style: unexpected/moved/gone all empty)

Dispatch-shaped adjudication: each divergence gets a verdict from the pin vocabulary — **`real-bug`** (predecessor text provably departs from original bytecode semantics; evidence = instruction-level walk, and where our proto is `L3`, our certified text as the readable reference), **`suspect`** (divergent, not yet adjudicated to root cause), **`probe-artifact`** (stub-environment effect; same class as the existing 4+2 pins). Verdicts are committed pins; a clean gate = every divergence pinned.

- [ ] **Step 1: run the full scan; bucket divergences by arm and file.**
- [ ] **Step 2: adjudication rounds** (subagents; our-side `L3` text supplied as reference where available — that is 96.8% of unique shapes). Every `real-bug` verdict needs the instruction-level evidence quoted in the report by pc/opcode, never by game text.
- [ ] **Step 3: the pin-gate test goes green** (all three `adjudicate_pins` lists empty) and the report's summary table states: divergent files per arm, verdict histogram, artifact rate.
- [ ] **Step 4: commit.** If any `real-bug` is found, it is the milestone's headline — flag it to the controller immediately rather than batching.

### Task 7: Class-1 instrument — enumerated differential driving

**Files:**
- Create: `scripts/probe_enum.py`, `scripts/probe_enum.lua` (extend `probe_common.lua`; the ~250-line duplication precedent from `probe_keyseq.lua` is *not* to be repeated — extract shared driver pieces into `probe_common.lua` first if needed)
- Test: `tests/test_probe_enum.py`

**Interfaces:**
- Consumes: Task 3 footprints (read-key sets), Task 4 input-space measurements (value domains), `oracle.run_bytes`.
- Produces: `probe_enum.drive(file, proto_path, assignments) -> Trace` and `probe_enum.exhaust(file, proto_path) -> EnumVerdict` — for each assignment in the enumerated product (read-key values × scripted stub returns), run **both sides** under identical assignment, byte-compare traces. `EnumVerdict`: `identical | divergent(assignment, first-diff) | budget-exceeded(space_size)`.

- [ ] **Step 1: failing tests on synthetic fixtures**: a two-flag chunk (4 assignments) driven exhaustively both sides identical; an injected arm-swap fixture (the two sides differ in one branch arm) **divergent, naming the assignment** that exposes it — the assignment-space analogue of the M5 fault-injection discipline; a proto whose measured space exceeds the budget refuses `budget-exceeded` rather than sampling silently.
- [ ] **Step 2: implement.** Assignment injection via the stub env's global-table pre-seeding (the L1.75 shadow-table machinery already writes globals; reuse). Budget: the Task 4-measured threshold, stated in one place.
- [ ] **Step 3: corpus run over the class-1 population** (from `classes.json`): three-way — original vs predecessor-recompiled (Track 1) and original vs our artifact where we ship structured. Exhaustive where the space allows; explicit `budget-exceeded` rows otherwise (**no silent sampling** — if sampling is added later it is labelled as such in the verdict type).
- [ ] **Step 4: results into the divergence ledger** (same pin vocabulary); commit.

### Task 8: Class-2 design + prototype

**Files:**
- Create: `docs/reports/m6-uiloop-design.md`; prototype under `scripts/probe_uiloop.py` (explicitly marked prototype)
- Test: `tests/test_probe_uiloop.py` (prototype-scoped)

Spec commitment is **observation + design + prototype**, not closure. Inputs: Task 4's step-3 hand-cut measurement (do the loop-body boundaries correspond across sides?). Candidate design: per-iteration transition comparison — treat the poll-loop body as `(state, key) -> (state', effects)`, snapshot state at the poll site both sides, compare single-iteration effects over the enumerated `(reachable-state × key)` frontier, sidestepping whole-loop termination. If Task 4's measurement kills the boundary assumption, the fallback deliverable is the design note recording why, with the measurement — that is a legitimate outcome.

- [ ] **Step 1: write the design note against Task 4's measurements** (not against hopes): boundary-correspondence result, state-snapshot feasibility (what is "state" — the footprint's read/write keys at the poll site), termination-of-iteration argument.
- [ ] **Step 2: prototype on the 2–3 hand-cut protos**; one committed injection proving it can fail (a swapped key-branch arm caught at the iteration level).
- [ ] **Step 3: L2 lower bound on the predecessor side**: run the existing `probe_keyseq.evaluate` with the 5 driveable files' sequences, predecessor text as candidate — this needs no new design and lands in the divergence ledger either way.
- [ ] **Step 4: commit; route the full instrument (or its refutation) to the M7 agenda seed.**

### Task 9: Structure-reference diagnosis (Track 2a)

**Files:**
- Create: `scripts/structure_reference.py`; output `docs/reports/m6-structure-reference.md` + per-proto files under `build/diagnosis/` (gitignored)
- Test: `tests/test_structure_reference.py` (smoke: one known leaf produces a diagnosis with both sides present)

**Interfaces:**
- Consumes: `sir.build.build_sir` (returns `Region` or raises `StructureError`), `predcorpus.load_pred_proto`, the leaf-refusal list.
- Produces: per leaf proto: our refusal (reason, pc) side-by-side with the predecessor proto's `build_sir` outcome — region-tree sketch if it structures, its own `StructureError` if not. **Step 1 measures the structuring success rate before anything else is built on it** (the spec names this the track's first risk).

- [ ] **Step 1: the rate.** `build_sir` over the predecessor-side protos corresponding to the ~20 leaves; report N structured / M refused, with reasons. If the rate is low, the reference value collapses — report and stop for controller adjudication rather than pushing on.
- [ ] **Step 2: diagnosis emitter** — region tree rendered structurally (node kinds, pc ranges, condition operand chains by register/pc; **no source text, no constants** beyond ASCII identifiers).
- [ ] **Step 3: run over all leaves; summary table into the report; commit.**

### Task 10: LLM meta-reconstruction pass (Track 2b)

**Files:**
- Create: `docs/reports/m6-reconstruction/<file>--<proto_path>.md` (one per leaf, committed)
- Create: `docs/reports/m6-reconstruction/INDEX.md`

Controller-dispatched: one opus-level subagent per leaf proto (~20, sized 8–3305 insns; measured estimate 30–80k tokens each, ~1–2M total, accepted by the human partner 2026-08-13). Each dispatch carries the four-piece input: (1) `luac_sz4 -l -l` listing of the **original** proto, (2) our refusal reason + fallback text for that pc range, (3) the predecessor's corresponding source slice, (4) Task 9's structure-reference diagnosis. Each record's fixed schema: **logic reconstruction** (prose, may quote identifiers, must not quote non-ASCII constants), **refusal-cause classification** (which of the two named defects, or a third thing — a third thing is a finding), **mechanism suggestion** (what `regions.If`/`classify_registers` would need). Records are hints for Track 3 and adjudication aids for Track 1; they gate nothing.

- [ ] **Step 1: emit the four-piece input bundles mechanically** (script, so bundles are regenerable).
- [ ] **Step 2: dispatch in batches; INDEX tracks coverage** (~20/~20 required by the exit).
- [ ] **Step 3: controller cross-check** — for at least 3 records, verify the reconstruction against the listing before accepting the batch (the corpus of M5 lessons says unverified prose is this project's dominant defect; LLM prose triply so).
- [ ] **Step 4: commit.**

### Task 11: Close defect 1 — compound-`if` condition trees

**Files:**
- Modify: `src/pyluadec/sir/regions.py` (condition-tree node in `If`), `src/pyluadec/sir/build.py` (`_match_*` recognizer), `src/pyluadec/express/reconstruct.py` (cond expression over the tree), `src/pyluadec/emit/lua.py` (printing `and`/`or` chains with correct precedence/parens)
- Test: `tests/test_sir_condtree.py` (new), plus the standing signal

**Interfaces:**
- Consumes: `tests/test_sir_longtail2.py::COMPOUND_CONDITION_EXEMPLAR` (committed 26-insn repro); Task 9/10 references for the 21 corpus shapes.
- Produces: certification of the compound-`if` family. **The signal named by the M6 agenda:** `tests/test_semantic_regressions.py::test_if_and_elseif_conjunctions_preserved` moves from `L1` to green-at-`L3` — that assertion flips **by measurement, not by editing the test**.

- [ ] **Step 1: red on the exemplar** — a new test asserting the exemplar certifies `L3`; currently refuses `structure:`.
- [ ] **Step 2: recognizer + representation.** Discipline unchanged: recognize or `StructureError`, never guess; pc-claim audit (`all_claimed`) holds; dominator single-entry checks extend to condition-chain blocks.
- [ ] **Step 3: reconstruction + printing**; certify the exemplar; then the corpus: regenerate ledger, `ratchet_diff.py` vs `0957364` — expect upgrades only; report how many of the 21 shapes certify and name the ones that do not, with reasons.
- [ ] **Step 4: fault injections** (swap `and`/`or`, drop an arm, mis-parenthesize) each caught by certification — committed per the guard discipline. **Step 5: ledger + ratchet + commit.**

### Task 12: Close defect 2 — register-classification family

**Files:**
- Modify: `src/pyluadec/express/names.py` / `src/pyluadec/express/freereg.py` (whichever the diagnosis lands in), possibly `express/reconstruct.py`
- Test: `tests/test_express_aliasing.py` (new)

**Interfaces:**
- Consumes: the adjudicated `snr_music` case (main collapses four nested table constructors into one aliased table — temp graded as local), the 5 `reconstruct: register N read again…` shapes, Task 10 records for the 16-shape family.
- Produces: certification of some measured subset; the honest form of this task is **diagnosis-first** — the family was never claimed to be one defect.

- [ ] **Step 1: build the minimal repro** for the `snr_music` collapse (synthetic source whose luac output reproduces the constructor-aliasing shape; the M5 pattern: never start from a 124KB corpus file).
- [ ] **Step 2: fix the classification for that repro; red→green; corpus measurement** (how many of the 16 shapes move; per-shape outcomes named).
- [ ] **Step 3: same for the consumed-register read shape (`snr_common` main)** if the diagnosis says it is the same mechanism; if it is a different mechanism, say so and scope it explicitly rather than stretching.
- [ ] **Step 4: ledger + ratchet (0 downgrades) + fault injections + commit.**

### Task 13: Documents of record, decision log, exit

**Files:**
- Modify: `docs/superpowers/specs/2026-08-09-pyluadec-refactor-overall-design.md` (§2 decision table: the 0.997-drop row, dated, with rationale), `CLAUDE.md` (M6 section), `CHANGELOG.md`, `docs/runbooks/m3-backlog.md` (M6-closed items struck; **M7 agenda seed** including the Class-2 full instrument disposition, Task 9's rate if it collapsed, L2 truncation residue, taint gaps, M1 Linux), `docs/reports/m6-cross-corpus.md` (final summary)
- Create: `tests/test_m6_exit.py`

Exit assertions mirror the spec §3 (no quality floor):

```python
def test_m6_exit_observation_complete(observation):
    # classes.json covers every leaf refusal and every CAP-dominant proto
    assert observation.unclassified == []

def test_m6_exit_divergences_all_adjudicated(cross_pins):
    unexpected, moved, gone = adjudicate_pins(cross_pins.divergent, cross_pins.pinned)
    assert (unexpected, moved, gone) == ([], [], [])

def test_m6_exit_reconstruction_coverage(recon_index):
    assert recon_index.missing == []          # ~20/~20 leaves

def test_m6_exit_l3_no_regression(ledger_rows):
    l3 = sum(1 for r in ledger_rows if r["level"] == "L3")
    assert l3 / len(ledger_rows) >= 0.96      # M5 floor carried, not tightened
```

- [ ] **Step 1: write the exit test against the real artifact schemas** (read them; every M5 exit-test field name was checked against the tree, keep that discipline). Floors sit below achieved values; each assert message reports the achieved number.
- [ ] **Step 2: docs sweep** — every M6 number re-measured at the closing tree; the concept-search discipline for stale invariants (search co-occurring terms, not phrases). **Step 3: decision-log rows.** **Step 4: full suite + `ratchet_job.sh` + commit.**

---

## Explicit non-goals (spec §5 — recorded so they are not re-litigated)

- Shipping predecessor text through our L3 gate (measured dead: 0/13).
- Relaxing any comparison or certification level to absorb predecessor output.
- 0.997 as a gate (dropped 2026-08-13; observable only).
- Corpus-wide key-sequence coverage (220/229 files have no input loop — structural ceiling).
- The rest of the backlog's M6 agenda items (taint gaps, truncation residue, M1 Linux) stay recorded, not gated here.

## Self-review notes

- Spec coverage: §0 both directions → T5/6 (them←us) + T9/10/11/12 (us←them); §2 Track 1.0 → T3/4, 1.1 arms 1–3 → T5, arm 4 → T7, arm 5 → T8, arm 6 → T2 census; Track 2 → T9/10; Track 3 → T11/12; §3 exit → T13; §4 Task-1 mandate → T1; §6 risks → T4 step 3 (both pre-measurements), T9 step 1 (rate first), T7 verdict types (no silent sampling).
- Type consistency: `Footprint` (T3) consumed by T4/T7; `load_pred_proto` (T2) by T5/T9; `classes.json` (T4) by T7/T13; pin vocabulary (`real-bug`/`suspect`/`probe-artifact`) shared T6/T7/T8; `adjudicate_pins` signature verified against `scripts/probe_common.py` this session.
- Numbers: all carry provenance (2026-08-13 at `0957364`) and are marked re-derive.

---

## AMENDED 2026-08-14 — Tasks 7 and 8 re-scoped, by the project owner's decision

**What changed the scope: measurement, not opinion.** Tasks 5, 6 and the two inserted
out-of-plan tasks produced evidence the plan did not have when it was written.

**The evidence.**

1. **Six defects were confirmed in the predecessor's shipped output, four previously
   unknown — and all six were found by the *static* arm.** Five of the six are invisible
   to both dynamic arms: for `snr_mainmenu:main_7` the behaviour arm returned `agree`
   over an 18-event run, and `snr_common.lua`'s behaviour row is silent
   (`truncated:1/79` — its original-side run invoked 1 of the 79 function-valued globals
   it defines before the 3000-event cap, and all 78 uninvoked function-valued globals
   corpus-wide are in that one file).
2. **The cheapest static instrument outperformed the designed one.** The four per-proto
   loss sweeps (`scripts/loss_sweep.py`, one walk per proto, 3.5s over all 1944 pairs)
   found everything the graded fingerprint found **plus** a defect the fingerprint's
   `cfg_reachable` scored **1.0** on, and **plus** a defect that Task 6's own aggregate
   test-op count had hidden (`snr_common:main_76_2`'s `EQ +7 / LT +2` against
   `TEST −1 / TESTSET −2` nets a *gain* on the five-opcode total).
3. **Task 7's first justification is therefore spent.** It was to serve two ends —
   hunting predecessor defects, and proving semantic equivalence where bytes differ.
   The first is better served by the sweeps.
4. **Task 8's premise did not survive Task 4.** The owner's framing treats
   non-termination as Class 2's *distinguishing* difficulty; measured, **127 of 162
   candidates (78%) poll the key every iteration, including 113/113 `choice-branch`**,
   and the option channel bottoms out in corpus-defined poll loops inside
   `snr_common.lua` rather than in engine primitives. The two classes are not
   independent, and the termination problem is not confined to the 11 protos labelled
   `ui-keyloop`.

**Task 7 — re-scoped to a feasibility demonstration.** Build `probe_enum` and prove it
works on **the 13 compound-`if` refusal protos** (the population Task 11 will fix), not
over the whole Class-1 candidate set. Deliverables unchanged in kind: the instrument,
its fault-injection proof, and `EnumVerdict`'s `budget-exceeded` honesty. What is
dropped is the corpus-wide run, which becomes an M7 item. Task 4 measured the budget
question already settled — **1940/1944 protos and 110/113 Class-1 candidates fit 4096
combinations, median 4** — so feasibility is about the instrument, not the arithmetic.

**Task 8 — re-scoped to a design note.** `docs/reports/m6-uiloop-design.md` only; no
`scripts/probe_uiloop.py` prototype. The note must record Task 4's two pre-measurements
(loop-body cut correspondence **18/19**, sole failure `snr_music:main_3`; and the
78% per-iteration overlap), state what a per-iteration transition-comparison prototype
would need, and say plainly which of its assumptions are measured and which are not.
The prototype moves to M7 with that note as its starting point.

**Weight moves to Tasks 9–12**, the half that improves the decompiler itself and is
already verified by the existing L3 certification gate.

**Exit criteria (plan §3) are amended accordingly:** Task 7's clause becomes
"exhaustive over the 13 compound-`if` protos, with `budget-exceeded` rows explicit and
no silent sampling"; Task 8's becomes "design note delivered with its assumptions
labelled measured or unmeasured". Task 13 records this amendment in the spec decision
log alongside the 0.997 drop.

---

## AMENDED 2026-08-14 (second) — Tasks 9 and 10 dropped, by the project owner's decision

**Both are cut from M6.** The reason is a measurement, not a re-prioritisation.

**Task 10's premise is falsified.** It was commissioned because a mechanical structure
reference might not be available, so LLM meta-reconstruction would have to substitute.
Task 9's Step 1 is the gate the plan itself set for that ("if the rate is low, the
reference value collapses; report and stop for controller adjudication"). Measured at
Task 11, and independently re-derived by its review: **`build_sir` succeeds on 12 of the
predecessor's 13 corresponding leaf protos — 92.3%** (sole failure
`snr_common.lua:main_76_2`, `pc 63: unrecognized transfer JMP`). The pre-fix figure was
**6/13 (46.2%)** and is confounded: six of its seven failures were the compound-`if`
defect Task 11 closed, so it measured *our own* recognizer, not the predecessor's
quality. The reference is essentially free; the ~1–2M-token pass buys nothing it does
not already have.

**Task 9's own value is reduced by what Task 11 found.** Its deliverable is a
region-tree reference. The blocker in the remaining population is
`Reconstructor.write_reg`'s `reg not in self.declared` gate — a **register
classification** defect, measured on `snr_common:main_76_2` (a staged temp materialised
as a `local` re-assignment, `LOADK R5,K0` vs `MOVE R5,R3` at pc 43) and on
`snr_graphic:main` (four table constructors collapsed by aliasing: `local l0_1 = {…15…}`
then `l0_1 = {…7…}` and six more reassignments, so every field of the line-17 table
aliases the last one written). A region tree does not say which registers are locals and
which are temporaries, which is exactly what Task 12 needs.

**Task 12 proceeds directly**, with what Task 11 handed it: a named mechanism, two
diagnosed exemplars, the 13 rows that left the `structure:` family and now fail
comparison (`mismatch: maxstacksize` ×6, `mismatch: code` ×5, `mismatch: code at root/N`
×2), and the existing `L3` gate as acceptance.

**M7 agenda seed:** Task 9's structure-reference diagnosis and Task 10's LLM pass are
recorded as *premise falsified by measurement*, not as unfinished work. If a future
population arises where `build_sir` fails on the predecessor side at a materially lower
rate than 92.3%, the argument for them returns and this measurement is the thing to
re-run first.

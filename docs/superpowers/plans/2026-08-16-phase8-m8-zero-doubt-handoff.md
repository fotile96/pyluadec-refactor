# M8 Zero-Doubt Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **READ FIRST — controller handoff**: `docs/reports/m8-handoff.md`
> (2026-08-16). It carries M7's final-review findings routed into M8, the
> verified tree state, **three corrections to this plan** (Task 6's
> petition unit, the ≤1.5× gate's collapse to two named rows, the primary
> metric), and one committed number to fix. Tasks 1–3 are already done;
> the handoff records what reproduced.

**Goal:** Close the 22 non-`L3` rows so every text-carrying occurrence ships
structured (fallback → 0 expected), gate the shipped corpus's recompiled
footprint at ≤ 1.5× per file, and deliver the readability layer (semantic
naming + text-unit inventory + Zndnovel migration guide).

**Architecture:** Three serial tracks on the M7 pipeline (spec:
`docs/superpowers/specs/2026-08-16-m8-zero-doubt-handoff-design-fable5.md`,
rev 2). Instrument-first: the footprint recorder lands before the first
repair so every campaign step's effect is observable. Byte-exact first;
normalization rungs only by per-rung partner petition.

**Tech Stack:** existing `pyluadec` packages; `scripts/warranty_build.py`;
`luac_sz4` oracle (memoized); Zndnovel tree read-only at its commit
`380a577`.

**Plan provenance:** authored by Claude Fable 5, 2026-08-16, at `ac50c4d`
(spec rev 2), same session as the spec. Baselines below were measured at
`72cb6a8` — re-derive at each task start; a figure that does not reproduce
is a finding to record, not to overwrite silently.

## Global Constraints

- **Never relax a comparison, floor, threshold, or gate to make something
  pass.** The certification invariant stands: a recognizer/classifier bug
  may only lower the L3 rate, never ship wrong code.
- Certification logic untouchable without a §2-licensed petition:
  `NORMALIZATIONS`, `LADDER_VERSION`, `compare_protos`, `_cmp`,
  `structural_hash`, `key_disagreements`. A licensed rung change bumps
  `LADDER_VERSION`, co-locates its soundness argument with its code, and
  carries the partner's recorded approval. **Anything else touching these
  names is out of bounds.**
- `corpus/ledger.jsonl` written only by `scripts/run_corpus.py`;
  `corpus/warranty.jsonl` + `corpus/final/` + `corpus/text_units.jsonl`
  (Task 8+) only by their generators. No hand edits, fixed points guarded.
- After every repair commit: `scripts/ratchet_diff.py` vs the M8 baseline —
  zero downgrades, including rung downgrades on existing `L3` rows.
- Bytes red line: no bytecode-derived string decoded outside the two
  sanctioned presentation sites (`emit/lua.py::_str_lit` delegating to
  `structure/fallback.py::str_lit`); no corpus content in diagnostics,
  pins, or committed analysis artifacts. The Task-8 inventory is
  *sanctioned product output* — its partner gate is Step 0 of Task 8.
- No `re` in `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}`.
- Corpora via env vars only: `PYLUADEC_CORPUS_DIR` (originals),
  `PYLUADEC_PRED_CORPUS_DIR` (Zndnovel `lua_scripts/`). Never modify either
  corpus, `/Users/fotile96/pyluadec/`, or the Zndnovel tree.
- Suite ceiling: ~120 s earmark for formal-verification instruments; every
  task reports its added seconds with attribution. Whole-corpus scans are
  jobs, not suite members (out-of-suite checks need the four conditions +
  measured cost with growth quantity).
- Campaign discipline: synthetic minimal repro before touching pipeline
  code; new guards ship with neuter/restore proofs or are labelled
  DEFENSIVE with a measurement; stage explicit paths, never `git add -A`.
- Footprint convention (spec §3): both sides stripped
  (`compile_source(…, strip=True)`; originals are already stripped),
  whole-file bytes including the 12-byte header.

## Prerequisites (outside this plan, before Task 1)

1. M7 finishing flow: final whole-branch review of
   `phase7-m7-semantic-warranty-glm53` (one dispatched subagent per the M7
   mode ruling), then the partner's integration decision. **This plan
   assumes master sits at the M7 merge tip when Task 1 starts.**
2. M8 branch created from that tip (phase-branch precedent).

---

### Task 1: Footprint instrument + recorded ratios + monotone pin; ratchet baseline move

**Files:**
- Modify: `scripts/warranty_build.py` (add `footprint_ratio` to each row)
- Modify: `scripts/ratchet_job.sh` (default `BASELINE_REF` → the M7 merge
  tip; update its comment, the M6/M7 task-1 precedent)
- Create: `tests/test_footprint_gate.py`
- Regenerate: `corpus/warranty.jsonl` (legitimate — generator change)

**Interfaces:**
- Produces: `warranty.jsonl` rows gain `"footprint_ratio": <float>` —
  `len(compile_source(shipped_text, strip=True)) / len(original_file_bytes)`,
  rounded to 4 decimals (stable across platforms; document the rounding in
  the generator docstring).
- Produces: `footprint_ratios() -> dict[str, float]` helper importable by
  tests (reads the committed artifact, no compiling at test time).

**Steps:**

- [ ] **Step 1: re-measure the baseline.** Run the spec's measurement over
  all 229 files; expected shape (re-derive, from `72cb6a8` + cross-review):
  exactly 7 files ≠ 1.00× and they are exactly the fallback carriers —
  `snr_mainmenu` ≈3.56, `snr_music` ≈3.34, `snr_novel` ≈2.88,
  `snr_graphic` ≈2.40, `snr_story_main` ≈1.70, `snr_memory` ≈1.62,
  `snr_common` ≈1.40. Record actual values in the task report.
- [ ] **Step 2: failing test.** `test_footprint_gate.py`:
  (a) every warranty row carries `footprint_ratio`;
  (b) the set `{file: ratio != 1.0}` equals the set of files with any
  `shipped == "fallback"` occurrence (the 1:1 fact, now a standing gate);
  (c) **monotone pin**: no file's ratio exceeds its committed value
  (pin the 7 non-1.0 values as a dict in the test; a repair lowers them —
  update the pin in the same commit as the repair, ratchet-style);
  (d) fixture tamper-neuter: a doctored ratio in a copied artifact fails (b).
  Run: expect FAIL (`footprint_ratio` missing).
- [ ] **Step 3: implement** the generator field + helper; regenerate
  warranty artifacts via `scripts/warranty_build.py --all`.
- [ ] **Step 4:** suite green; fixed-point test still green (regeneration
  byte-identical on a second run); ratchet_job exit 0 at the NEW default
  baseline. Report suite delta with attribution (this is
  formal-verification instrumentation).
- [ ] **Step 5: commit** (generator + artifacts + test + ratchet default,
  explicit paths).

### Task 2: The `structure:` recognizer gap — `snr_common:main_71` (2 rows)

**Files:**
- Modify: `src/pyluadec/sir/build.py` (`_match_loop` family)
- Test: `tests/test_sir_loops_longtail.py` (or a new module if cleaner)

**Interfaces:**
- Consumes: the M6 diagnosis (runbook `structured-pipeline.md`,
  `main_71` walkthrough): the `if` at pc 284 structures **only** with
  `break_target=410`; `_match_loop(279)` returns `None` for the enclosing
  `while true` (back edge `JMP 409 → 279`, break `JMP 295 → 410`).
- Produces: `_match_loop` recognizes the `while true`-with-`break`-to-exit
  shape; both ledger rows (`main_71` + its inherited ancestor) certify.

**Steps:**

- [ ] **Step 1: synthetic repro.** Write the minimal Lua whose bytecode
  reproduces the refusal (a `while true do … if c then break end … end`
  whose latch is an unconditional back-jump and whose break exits past the
  latch). Compile with the oracle; assert `build_sir` raises
  `StructureError` with the `else-join out of range` message. This failing
  test is the repro; commit nothing yet.
- [ ] **Step 2: fix in `_match_loop`** (recognize the back-edge/exit pair;
  claim the break target as loop exit). Discipline: recognize or
  `StructureError` — no guessing; `all_claimed` audit must still pass.
- [ ] **Step 3:** synthetic test green; adjacent SIR batch green
  (`test_sir_*`).
- [ ] **Step 4: corpus.** Regenerate ledger (`scripts/run_corpus.py`);
  expected: both rows flip `L3` (22 → 20); `snr_common` fallback
  occurrences shrink; footprint ratio for `snr_common` drops — update the
  Task-1 pin in this commit. `ratchet_diff` zero downgrades. Warranty
  regenerated (its trigger: ledger moved).
- [ ] **Step 5:** full suite + pin cascade (census pins, m7/m8 exit
  fixtures, observation digests if they reference the moved rows);
  ratchet_job exit 0. Commit.

### Task 3: The `reconstruct:` staging family (4 rows)

**Files:**
- Modify: `src/pyluadec/express/reconstruct.py` and/or
  `src/pyluadec/express/freereg.py` (follow the diagnosis)
- Test: `tests/test_express_sameblock.py` / `tests/test_express_residual.py`

**Interfaces:**
- Consumes: the 4 rows are `snr_graphic`/`snr_memory` `main` + `main_3`
  ("register 7 is read again after it was consumed" class) — the M7
  task-8-linked refusals that appeared when those protos' earlier
  `mismatch` cleared. Re-derive the exact refusal text and pcs first.
- Produces: 4 rows certify (20 → 16 expected).

**Steps:**

- [ ] **Step 1: diagnose.** Dump each refusal (single-file decompile +
  certify per runbook "Common operations"); locate the staged-value
  consumption pattern; write it down at instruction level in the report.
- [ ] **Step 2: synthetic repro** per the M7 task-8 pattern (staging-span
  clauses): minimal Lua reproducing the refusal. FAIL first.
- [ ] **Step 3: fix.** Likely an extension of the staging-span exemption
  or the conditional-value convergence (`_staging_span_ok` /
  `_cond_value_stages`); whatever mechanism the diagnosis names. Guards
  neuter-proven (clear the certification memo between neuter runs — the
  M7 task-7 lesson).
- [ ] **Step 4: corpus** regen + ratchet 0 downgrades + footprint pins
  updated (`snr_graphic`/`snr_memory` ratios drop; if either file goes
  fully structured its ratio hits 1.0 and leaves the pin dict). Suite +
  pin cascade + ratchet_job. Commit.

### Task 4: `mismatch: maxstacksize` cluster (8 rows) — byte-exact attempts

**Files:**
- Modify: `src/pyluadec/express/` (classification/staging) or
  `src/pyluadec/emit/lua.py` (emission order) per diagnosis
- Test: `tests/test_express_residual.py` + synthetic modules as needed

**Interfaces:**
- Consumes: 8 rows = the K1 NEWTABLE-hint-position family (5, M8 agenda 3)
  + dead-slack residue (re-derive the split). K1's M7 task-10 ruling
  deferred it to a possible `L3.3` rung — **but §2 requires the byte-exact
  attempt first and its failure documented as a parser-direction argument
  before any petition.**
- Produces: rows certify byte-exact where possible; for survivors, a
  written parser-direction argument per row (input to Task 6).

**Steps:**

- [ ] **Step 1:** per-row first-divergence dump (which proto, which field,
  what hint/slack value on each side).
- [ ] **Step 2:** for each sub-cluster, attempt an emitter-side form that
  makes luac produce the original hint/stack shape (e.g. materialize the
  constructor in the original's statement order; emit the dead local the
  original's register pressure implies). Synthetic repro first, as always.
- [ ] **Step 3:** corpus regen + ratchet + footprint pins + suite per
  repair batch (one commit per mechanism, the M7 task-9 precedent).
- [ ] **Step 4:** for every row that resists: a parser-direction argument
  ("no source luac compiles to this sequence because …") recorded in the
  runbook's residual section, named per row. These rows go to Task 6.

### Task 5: `mismatch: code` cluster (8 rows) — byte-exact attempts

**Files:**
- Modify: `src/pyluadec/emit/lua.py` (statement/reference ordering) or
  `express/` per diagnosis
- Test: synthetic + `tests/test_express_residual.py`

**Interfaces:**
- Consumes: known sub-clusters — constant-pool order
  (`snr_story_main:main_3`, const[70] `fileName`/`sysgim`; pool order =
  luac first-reference order, which our statement ordering influences) and
  expression layout (`snr_novel:main`, root). Re-derive the full 8-row
  census first.
- Produces: rows certify byte-exact where achievable; parser-direction
  arguments for survivors (input to Task 6).

**Steps:**

- [ ] **Step 1:** census + first-divergence dump for all 8.
- [ ] **Step 2:** pool-order rows: determine whether a
  semantics-preserving reordering of our emitted statements reproduces the
  original first-reference order (it may be genuinely unreachable — the
  M7 s3/s4 parser-direction precedent; prove whichever way it falls).
- [ ] **Step 3:** layout rows: same treatment for expression shape
  (ADD-vs-GETUPVAL staging order class).
- [ ] **Step 4:** repairs commit per mechanism with the full gate battery;
  survivors get named arguments → Task 6.

### Task 6: Rung petitions (conditional — possibly empty)

**Files:**
- Modify (per approved petition only): `src/pyluadec/verify/normalize.py`
  (`NORMALIZATIONS`, `LADDER_VERSION`), `tests/` for the rung's own gates
- Create: soundness argument as the rung function's docstring (the
  `_strip_lineinfo` precedent)

**Interfaces:**
- Consumes: Task 4/5's parser-direction arguments — **a petition without
  one is not presentable.**
- Produces: for each approved rung: the normalization, its
  `LADDER_VERSION` bump, its "what does `compare_protos` still prove"
  statement, and the affected rows at the new rung. Anticipated candidates
  (not pre-approved): `L3.2` pool-order (instruction-resolved constant
  multiset + index-remap bijection), `L3.3` NEWTABLE hint mask,
  maxstacksize tight-bound comparison.

**Steps:**

- [ ] **Step 0 (BLOCKING per petition): present to the partner** — the
  argument, the rung's exact comparison change, the affected rows, the
  soundness sketch. No code before approval. One petition, one decision.
- [ ] **Step 1:** implement the approved rung; soundness argument in the
  docstring; `LADDER_VERSION` bump; the rung's own negative tests (a
  difference the rung must NOT mask — e.g. a *value* change under L3.2, a
  *count* change under L3.3 — stays refused).
- [ ] **Step 2:** corpus regen. Ratchet check must show upgrades only;
  **assert no pre-existing row's rung weakened** (exit 4's clause).
  Footprint unchanged (rungs are length-preserving — verify on the flipped
  rows, don't assume).
- [ ] **Step 3:** suite + ratchet_job; commit with the approval recorded
  in the message and the overall-design §2 decision table row added.

### Task 7: Semantic naming pass

**Files:**
- Modify: `src/pyluadec/express/names.py` (naming rules)
- Test: `tests/test_express_names.py` + new `tests/test_naming_semantic.py`
- Regenerate: `corpus/final/` + `corpus/warranty.jsonl` (presentation-layer
  change: **ledger must be byte-identical**)

**Interfaces:**
- Consumes: reference implementations
  `/Users/fotile96/pyluadec/post_process/tools/rename_semantic_locals.py`
  and `rename_scene_locals.py` (read-only, concept only — our
  implementation lives in the naming layer, not a text post-processor).
- Produces: deterministic rules, minimum set:
  (1) a local bound by `CLOSURE` in file `snr_crd_N.lua` whose proto is
  the card entry → `card_N_main`-style; scene closures in chapter files →
  `scene_<chapter>_<n>(scene_id, scene_title)`-style (derive the exact
  rule from call-site constants, not the file name alone);
  (2) a table local whose `SETTABLE` string keys are drawn from one
  recognizable constant family → that family's name (`plotTitle` class);
  (3) everything without rule-derivable evidence keeps the synthetic name
  — **wrong names are worse than ugly names**.
- Produces: coverage figure (fraction of closure-bound locals in
  text-carrying files renamed) with derivation.

**Steps:**

- [ ] **Step 1:** failing spot-check tests naming exact expected names on
  exact files (write against the rule spec, e.g. `snr_crd_0.lua` contains
  `card_0_main`; pick 5–8 pinned samples across rule classes).
- [ ] **Step 2:** implement rules in `names.py`; determinism = same
  bytecode → same names (no dict-order dependence; sort candidates).
- [ ] **Step 3:** regenerate `corpus/final/` + warranty. **Assert ledger
  byte-identical** (`git diff --stat corpus/ledger.jsonl` empty) and full
  re-certification green — the presentation-layer definition.
- [ ] **Step 4:** fixed point (second regeneration byte-identical);
  coverage figure measured and reported; sample listing (30–50 renamed
  sites) attached to the report for partner quality review.
- [ ] **Step 5:** suite + ratchet_job; commit.

### Task 8: Text-unit inventory (`corpus/text_units.jsonl`)

**Files:**
- Create: `scripts/text_units_build.py`, `corpus/text_units.jsonl`
- Test: `tests/test_text_units.py`

**Interfaces:**
- Produces: one JSONL row per translatable text unit:
  `{"id": <vms message id | null>, "file", "proto_path", "pc",
  "kind": "vms" | "structural", "voice": <voice id | null>,
  "speaker": <prefix or null>, "text": "<raw UTF-8 via str_lit>",
  "context": "<call target name>"}`. Keyed by message ID where present
  (`vms` static sites; Zndnovel census: 16749 sites, IDs within 1..17220 —
  re-derive our own count from bytecode and reconcile), `file:pc`
  otherwise (the `tr_line` class: string constants reaching call
  arguments of display-family targets).
- Extraction is from **bytecode constants** (ingest/lift layer data,
  rendered through the existing `str_lit` body) — not from parsing our own
  emitted text.

**Steps:**

- [ ] **Step 0 (BLOCKING, partner gate — spec §4.3):** present the
  overall-design §2 decision-table row sanctioning this artifact class
  (product output containing game text, same class as `corpus/final/`).
  No generation code before approval.
- [ ] **Step 1:** failing tests: row schema; the vms-count reconciliation
  (our extracted static-site count vs the Zndnovel census, with any
  difference itemized, not averaged away); fixed point; tamper-neuter.
- [ ] **Step 2:** implement generator (walk lifted instrs for CALL sites
  whose callee resolves to the `vms` family / display family; collect
  constant args). No `re` (it lives in `scripts/`, but string work on
  corpus bytes stays in `bytes` until the `str_lit` boundary).
- [ ] **Step 3:** generate, commit artifact + generator + tests; suite
  cost attributed (inventory fixed point = instrument).
- [ ] **Step 4:** `tr_line` reconciliation: map Zndnovel's 678 annotation
  lines (162 files) onto inventory rows; report matched/unmatched with
  reasons. Unmatched entries are findings for the guide, not silent drops.

### Task 9: Migration guide + read-only validation + backfill smoke

**Files:**
- Create: `docs/migration/zndnovel-handoff.md`
- Create: `tests/test_backfill_smoke.py` (or a job script if >2 s)

**Interfaces:**
- Consumes: Zndnovel tree read-only at `380a577` (pin the commit in the
  guide; if their HEAD moved, re-run against then-HEAD and say which).
- Produces: the guide per spec §4.2 items 1–6, every behavioural sentence
  about Zndnovel tools backed by a run in this task.

**Steps:**

- [ ] **Step 1: validation runs.** Execute `extract_text.py`,
  `extract_dag.py`, `extract_crd.py` read-only against `corpus/final/`
  (copy scripts to scratchpad, point inputs at our artifact — never write
  into their tree); diff outputs against their committed `analysis/`
  snapshots; classify per tool: identical / benign-formatting /
  needs-adaptation, with counted diff lines.
- [ ] **Step 2: backfill smoke.** Via the inventory: pick one vms row,
  substitute its text in a scratch copy of the file, recompile with the
  oracle, assert the proto tree matches the pre-substitution compile
  everywhere except that one constant. Commit as a test (cheap) or a
  documented job (if slow — measure, then decide, with the out-of-suite
  four conditions if routed out).
- [ ] **Step 3: write the guide**: the three tools (what breaks, what
  adapts, the inventory-consumption recommendation with a worked
  example); `tr_line` reconciliation results (Task 8 Step 4); the
  hand-edit patch layer (diff pred text vs its own recompile to enumerate
  hand edits: the `fontLoad` swap + readable-name edits + anything found —
  measured list, not remembered list); the vms-ID preservation statement
  citing certification evidence; the backfill path with the smoke result.
- [ ] **Step 4:** partner review of the guide (it is a cross-project
  deliverable); commit.

### Task 10: Exit gates, documents of record, close

**Files:**
- Create: `tests/test_m8_exit.py`
- Modify: `CLAUDE.md` (Phase 8 section), `docs/runbooks/m3-backlog.md`
  (M8 agenda closeout + M9 agenda seed),
  `docs/runbooks/structured-pipeline.md` (capability boundary re-measure),
  spec §2 decision table rows for anything decided mid-milestone

**Steps:**

- [ ] **Step 1:** `test_m8_exit.py`, asserting from committed artifacts
  (no corpus needed where possible):
  (1) zero occurrences with `shipped == "fallback"` whose proto carries
  translatable text (constant census per spec §1(b), occurrence-granular);
  (2) every remaining non-`L3` row (expected none) satisfies the
  stop-loss triple, machine-checked;
  (3) every `footprint_ratio` ≤ 1.5;
  (4) naming determinism + ledger-untouched assertions still green;
  (5) inventory reconciliation counts pinned;
  (6) each gate driven over mutated data to prove it can fail
  (the M7 exit-test pattern).
- [ ] **Step 2:** re-measure every headline number on the closing tree;
  update the three documents; agenda items closed out item-by-item with
  their disposition (the M7 wrap precedent).
- [ ] **Step 3:** full suite ×3 with timings; `ratchet_job.sh` end-to-end;
  ratchet vs the M8 baseline quoted in the close report.
- [ ] **Step 4:** commit; hand off to the final whole-branch review per
  the session's execution-mode ruling.

## Verification battery (every repair task: Tasks 2–6)

1. Synthetic repro test green (and was red first).
2. Adjacent test batch green.
3. `scripts/run_corpus.py` → ledger regen; `ratchet_diff.py` vs M8
   baseline: 0 downgrades (levels AND rungs).
4. Footprint pins updated in the same commit; monotone (never up).
5. Warranty regenerated when the ledger moved; fixed points hold.
6. Full suite + `ratchet_job.sh` exit 0.
7. Report: rows flipped, rows remaining, mechanism named, numbers
   re-measured (not copied from this plan).

## Self-review notes (writing-plans checklist)

- Spec coverage: §1→Tasks 2–6; §2→Task 6 + global constraints; §3→Task 1 +
  exit (3); §4.1→Task 7; §4.2→Task 9; §4.3→Task 8; §5→Task 10; §7→
  Prerequisites. No spec requirement without a task.
- The two partner gates inside the plan (Task 6 Step 0 per petition,
  Task 8 Step 0) are stops, not rulings — they go to the partner verbatim.
- Campaign tasks (3–5) are investigation-first by design; their "exact
  values" are named exemplars + re-derivation commands, per the M7 plan's
  precedent for residual work. Interface names from this plan are
  hypotheses to verify against the tree (standing lessons clause).

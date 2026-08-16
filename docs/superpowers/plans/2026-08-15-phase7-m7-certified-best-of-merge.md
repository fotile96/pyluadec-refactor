# M7: Certified Best-of Merge with a Two-Factor Warranty — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `corpus/final/` (the merged 229-file corpus the localization
project translates against) and `corpus/warranty.jsonl` (per-occurrence
two-factor grades, per-file selection verdicts, provenance), with the repair
campaign moving as many files as possible from the pred column to the ours
column first.

**Architecture:** Four strands behind a baseline move. (1) Re-decompile the
predecessor side through our own pipeline so pred-won files ship in output
surface v2 with arithmetic Factor-T warranties (§3 of the spec), gated by a
full-population recert-rate measurement. (2) An invariant panel — the
two-sided form of the eight `LOSS_KINDS` families, per-proto fingerprint
verdicts, and a new `constant_values` family — grades Factor E (pred bytecode
vs original bytecode) per proto. (3) The repair campaign closes mechanisms
D/C/E and attributes every surviving non-`L3` row. (4) A pure-function
selection rule consumes the records and emits both artifacts under ledger
discipline. Certification remains the only judge of text; the panel judges
only pred-vs-original equivalence.

**Tech Stack:** existing `pyluadec` packages (`ingest`/`lift`/`cfg`/`sir`/
`express`/`emit`/`verify`/`structure`/`oracle`/`pipeline`/`predcorpus`),
`luac_sz4`/`lua_sz4`, `scripts/loss_sweep.py` + `scripts/cross_corpus.py`
machinery, pytest.

**Spec:** `docs/superpowers/specs/2026-08-15-m7-certified-best-of-merge-design-opus5.md`
(rev 3, commit `6b6c1e3`). Its sibling
`2026-08-15-m7-semantic-warranty-merge-design-glm53.md` records the rejected
alternatives — consult it only to avoid re-litigating them.

## Global Constraints

- **Certification logic untouchable:** `NORMALIZATIONS`, `LADDER_VERSION`,
  `compare_protos`, `_cmp`, `structural_hash`, `key_disagreements`. Never
  relax a comparison, floor, or gate to make something pass.
- **`corpus/ledger.jsonl`** written only by `scripts/run_corpus.py`; every
  ledger movement goes through `scripts/ratchet_diff.py` vs the M6 merge
  baseline **`3669950`** with 0 downgrades (Task 1 moves the default).
  `corpus/golden/` read-only; `vendor/` pristine.
- **Bytecode-derived strings stay `bytes`** in ingest/lift/cfg/sir/express/
  verify/comparison layers. The panel's evidence strings and every committed
  observation value carry opcode/pc/count/ASCII-identifier data only — never
  constant content. The one presentation-layer change this milestone makes
  (`structure/fallback.py::str_lit`, Task 5) **reverses a written
  prohibition and requires its own partner approval before any code is
  written** (spec §4).
- **No `re`** in `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}`
  (statically enforced by `tests/test_engineering_practice.py`).
- Corpora only via env vars: `PYLUADEC_CORPUS_DIR` (original bytecode),
  `PYLUADEC_PRED_CORPUS_DIR` (predecessor text). Missing ⇒ `pytest.skip`
  (fixtures in `tests/conftest.py`). `scripts/ratchet_job.sh` hard-requires
  both.
- **Suite earmark ~120 s**, new cost attributable to formal-verification
  instruments (panel, recert, fixed-point gates). Full-corpus scans are jobs
  with the four out-of-suite conditions (named home, documented trigger, one
  command, traceable last run) and the measured-not-predicted rule
  (real timing + growth dimension + hard budget with `budget-exceeded`-style
  refusal — never silent sampling).
- **Strip convention (spec §3, rev 3):** any comparison touching
  pred-compiled bytecode states its strip choice explicitly.
  `predcorpus.load_pred_proto`'s docstring and M6's polluted survey are the
  precedent; Task 2 fixes the convention for the whole milestone.
- **No re-litigation** of the 12 `equivalent-transform` verdicts or the six
  `corpus/pred_repairs/` repairs; their evidence is consumed as recorded.
- **Standing lessons bind every task:** every number in this plan is a
  hypothesis measured 2026-08-15 at `6b6c1e3` (ledger identical to
  `3669950`) — re-derive at task start; if it does not reproduce, the
  measurement wins and the discrepancy is reported. Every new guard:
  neuter → named test red → restore → green, or label `DEFENSIVE` with what
  was tried. Every behavioural sentence gets measured before it is written;
  superlatives each need a measurement or a rewording.

## Baseline numbers (measured 2026-08-15 at `6b6c1e3` — re-derive at task start)

`L3` 1438/1478 unique (97.3%) / 1904/1944 occurrences (97.9%). Products:
217 fully structured / 8 hybrid / 4 whole-file fallback (`config.lua` 1 occ,
`snr_common.lua` 147, `snr_music.lua` 5, `snr_novel.lua` 15). 40 non-`L3`
rows = 29 own + 11 inherited; by reason `mismatch: code` 19 (14 root + 5
`at root/*`), `mismatch: maxstacksize` 15 (11 + 4), `reconstruct:` 5 (3 own
clamp + 2 inherited), `structure:` 1. Attributed 9 (6 mechanism C, 3
mechanism D). Non-`L3` occurrences per file: `snr_common` 14, `snr_memory` 4,
`snr_graphic` 4, `snr_novel` 3, `snr_s5_10_s` 3, `snr_s3_10_s`/
`snr_story_main`/`snr_s4_10_s`/`snr_mainmenu`/`snr_s1_10_s` 2 each,
`config`/`snr_music` 1 each. `config.lua:main` refuses
`mismatch: maxstacksize` at root. Suite 1087 passed, 52.7–56.8s. Pred parity:
229/229 compile, 229/229 tree-match, 0/229 byte-exact, 3903 substantive
mismatches / 1433 paths. Loss sweeps: 25 flagged protos, 3.31s. `build_sir`
on pred: 12/13 leaves (full population unmeasured — Task 2's whole point).

---

### Task 1: Baseline re-measure + ratchet default move

**Files:**
- Modify: `scripts/ratchet_job.sh` (default `BASELINE_REF` `0957364` → `3669950`)
- Modify: `CLAUDE.md` (the one line quoting the default, in the M5/M6 ratchet bullet)

**Interfaces:**
- Consumes: `scripts/ratchet_diff.py OLD NEW` (exit 0/1/125/128).
- Produces: the milestone's measured starting state, recorded in the task
  report; all later tasks diff against `3669950`.

- [ ] **Step 1: re-measure the baseline block above** (ledger breakdown via a
  throwaway read of `corpus/ledger.jsonl`, suite timing ×3, `ratchet_job.sh`
  end-to-end). Report deltas from the plan's numbers; a non-reproducing
  number is a finding.
- [ ] **Step 2: move the default.** One-line edit in `ratchet_job.sh` (its
  comment already promises "the last merged milestone tip"); update the
  CLAUDE.md sentence that quotes `0957364` as the default.
- [ ] **Step 3: verify** — `PYLUADEC_CORPUS_DIR=… PYLUADEC_PRED_CORPUS_DIR=…
  ./scripts/ratchet_job.sh` exits 0 with no argument (now diffing `3669950`
  vs itself-equivalent tree: expect 0 upgrades, 0 downgrades).
- [ ] **Step 4: commit** (`chore: M7 ratchet baseline -> 3669950`).

### Task 2: Pred re-certification machinery + the full-population rate (§3 go/no-go)

**Files:**
- Create: `src/pyluadec/predrecert.py`
- Create: `scripts/pred_recert_rate.py` (job CLI)
- Test: `tests/test_predrecert.py`
- Modify: `docs/reports/m7-warranty.md` (create; §1 = the rate)

**Interfaces:**
- Consumes: `oracle.compile_source(source: bytes, *, strip: bool) -> bytes`,
  `ingest.load_bytes`, `pipeline.decompile_chunk(root: Proto) ->
  DecompileResult` (fields: `source: bytes`, `levels`, `rungs`, `reasons`,
  `shipped_fallback`, `hybrid`, `confessions_by_proto` — all keyed by
  `proto_path`).
- Produces:
  `predrecert.recert_file(pred_dir: Path, name: str) -> RecertOutcome` where
  `RecertOutcome` is a frozen dataclass: `source: bytes` (our v2 text, or the
  chunk's hybrid/fallback assembly exactly as `decompile_chunk` shipped it),
  `t_grades: dict[str, str]` (`proto_path -> "T3" | "T2" | "T-"`),
  `reasons: dict[str, str | None]`, `reference: bytes` (the stripped pred
  bytecode the certification ran against). Task 11's generator consumes this
  signature verbatim.

**The strip convention, fixed here for the milestone (spec §3 rev 3):** the
reference is `oracle.compile_source(pred_text, strip=True)`. Rationale to
state in the module docstring: the pred text compiled unstripped carries real
`lineinfo`/`locvars`, our re-emitted text cannot reproduce those names, and
`verify.certify.carries_debug` would then compile candidates unstripped and
fail on debug tables — the exact phantom-mismatch class M6 measured (260
`nups > 0` protos). Stripping the reference matches the original corpus's
shape and makes certification compare semantic fields only, which is the
claim Factor T actually makes.

**T-grade mapping** (from `DecompileResult`, one place, tested): `T3` ⟺
`levels[p] == "L3"`; `T2` ⟺ `levels[p] != "L3"` and `not
shipped_fallback[p]` (the hybrid contract compared this proto's own fields);
`T-` ⟺ `shipped_fallback[p]`.

- [ ] **Step 1: failing tests.**

```python
# tests/test_predrecert.py (corpus-gated by pred_corpus_dir fixture)
def test_recert_reference_is_stripped(pred_corpus_dir):
    out = predrecert.recert_file(pred_corpus_dir, "snr_title.lua")
    from pyluadec.verify.certify import carries_debug
    from pyluadec.ingest import load_bytes
    assert carries_debug(load_bytes(out.reference)) is False

def test_recert_grades_cover_every_proto(pred_corpus_dir):
    out = predrecert.recert_file(pred_corpus_dir, "snr_title.lua")
    assert set(out.t_grades) == set(out.reasons)
    assert all(g in ("T3", "T2", "T-") for g in out.t_grades.values())

def test_t_grade_mapping_is_the_stated_function():
    # synthetic: a source that fully certifies -> all T3
    src = b"Config = function(a)\n    return a + 1\nend\n"
    out = predrecert.recert_bytes(src)
    assert set(out.t_grades.values()) == {"T3"}
```

- [ ] **Step 2: implement** (`recert_bytes(source: bytes) -> RecertOutcome`
  as the core; `recert_file` wraps file loading). No new certification code —
  this is plumbing around `decompile_chunk`.
- [ ] **Step 3: the rate (the task's real deliverable).**
  `scripts/pred_recert_rate.py`: over all 229 pred files → per-file and
  corpus-total T-grade histograms by occurrence. Print
  `recert: T3 a/1944, T2 b/1944, T- c/1944` and per-file rows for every file
  with any `T-`. Record wall-clock and the growth dimension (linear in
  files; `compile_source` memo makes reruns cheap) in the script docstring
  with the trigger ("before Task 11, and whenever `sir/`, `express/`,
  `emit/`, or `structure/` change during this milestone").
- [ ] **Step 4: the go/no-go.** If `(T3+T2) / 1944 < 0.70`, **stop and
  report to the human partner before any Task 11 work** (spec §3's policy
  line). Either way, `docs/reports/m7-warranty.md` §1 records the full
  histogram, the disposition, and the strip-convention statement.
- [ ] **Step 5: commit.**

### Task 3: The invariant panel — two-sided families + `constant_values`

**Files:**
- Create: `scripts/invariant_panel.py`
- Test: `tests/test_invariant_panel.py`

**Interfaces:**
- Consumes: `scripts/loss_sweep.py`'s per-proto field extraction (the
  function that computes the eight `LOSS_KINDS` counters for one proto —
  locate its exact name before writing a twin; `loss_sweep` prints via
  `LOSS_KINDS`-ordered `fields`), `scripts/cross_corpus.py`'s per-proto
  signature machinery (the thing `_sig_summary` prints), `predcorpus.
  load_pred_proto(pred_dir, name, *, strip: bool)` with
  `strip=not carries_debug(original)` (the documented rule — here originals
  are stripped, so `strip=True`), `lift.lift_proto`, decoded operands from
  `lift.opcodes`.
- Produces: `invariant_panel.proto_panel(orig: Proto, pred: Proto) ->
  PanelResult` where `PanelResult.diffs: dict[str, str]` maps family name →
  ASCII evidence (`"global_writes: orig 3 != pred 4"`,
  `"constant_values: 2 value(s) only in pred, first at pc 17 LOADK"`) and is
  empty on pass; `invariant_panel.file_panel(corpus_dir, pred_dir, name) ->
  dict[str, PanelResult]` keyed by proto_path. Family names:
  `"loss:<kind>"` ×8 (two-sided), `"fingerprint"`, `"constant_values"`.
- Docstring: the **blindness list** required by spec §2.1 — instruction
  order within equal counts, control-flow shape beyond loop/test counts,
  cross-proto behavioural integration — plus anything discovered while
  building.

**`constant_values` (spec §2.1, new work):** per proto, the multiset of
constant **values** (as `bytes`/numeric, never decoded) referenced by
load-class operands — `LOADK`'s `Bx`, `GETGLOBAL`/`SETGLOBAL`'s `Bx`, and
every RK-encoded B/C operand with the K bit set — compared as multisets.
Pool *index* differences must not flag (the known-benign bulk of the 3903
mismatches). Evidence strings carry counts/opcodes/pcs only.

- [ ] **Step 1: failing tests on synthetic fixtures** (compile pairs with
  `oracle.compile_source`):

```python
def _panel(a: bytes, b: bytes):
    pa = ingest.load_bytes(oracle.compile_source(a, strip=True))
    pb = ingest.load_bytes(oracle.compile_source(b, strip=True))
    return invariant_panel.proto_panel(pa, pb)

def test_gain_side_flags():          # the two-sided proof loss_sweep lacks
    d = _panel(b"f()\n", b"f()\ng = 1\n").diffs
    assert any(k.startswith("loss:global_writes") or k == "loss:global_writes"
               for k in d)

def test_constant_value_swap_flags_only_constant_family():
    d = _panel(b'f("abc")\n', b'f("abd")\n').diffs
    assert set(d) == {"constant_values"}

def test_pool_reorder_passes():
    # same constants, different pool order via reference order
    a = b'f("x")\ng("y")\n'
    b = b'g("y")\nf("x")\n'
    # call-order change flags call families legitimately; isolate constants:
    assert "constant_values" not in _panel(a, b).diffs or True  # refine at impl
    d = _panel(b'local t = {"x", "y"}\n', b'local t = {"y", "x"}\n').diffs
    # identical multisets regardless of pool index order
    assert "constant_values" not in _panel(
        b'f("x", "y")\n', b'f("x", "y")\n').diffs

def test_evidence_carries_no_constant_bytes():
    d = _panel(b'f("SECRETTOKEN")\n', b'f("OTHERTOKEN1")\n').diffs
    assert "SECRETTOKEN" not in d["constant_values"]
```

  (The pool-reorder fixture above is a sketch — at implementation build a
  pair whose pools genuinely reorder with identical referenced multisets;
  `luac` pools follow first-reference order, so reorder the *unreferenced
  duplicate* path or construct via two chunks with swapped statement order
  whose per-proto constants are identical. If no such pair is constructible,
  say so in the test file and cover the property with a unit test on the
  multiset extractor instead — do not fake it.)
- [ ] **Step 2: implement.** Two-sided families are `orig_counter !=
  pred_counter` over the same extraction `loss_sweep` uses (import, don't
  copy); fingerprint family is per-proto signature equality; constant family
  is the operand walk above. All comparisons on `bytes`; the module lives in
  `scripts/` (outside the guarded packages) but honors the red line by
  construction — add the `cross_corpus.json_safe` assertion over every
  evidence string.
- [ ] **Step 3: the loss-sweep contrast proof** (the plan's replacement for a
  neuter): a one-directional check of `test_gain_side_flags`' fixture using
  `loss_sweep`'s own predicate must **pass** (pred lost nothing), while the
  panel flags it — committed as a test documenting *why* the two-sided form
  is new work.
- [ ] **Step 4: commit** (no corpus run yet — that is Task 4).

### Task 4: Panel corpus run, adjudication, committed verdicts

**Files:**
- Modify: `scripts/invariant_panel.py` (CLI arm + `PANEL_PINS`)
- Create: `corpus/observation/panel.json` (generated, committed)
- Test: `tests/test_invariant_panel.py` (pin gate + fixed point + summary pin)
- Modify: `docs/reports/m7-warranty.md` (§2: verdict histogram, runtime, pins)

**Interfaces:**
- Consumes: Task 3's `file_panel`; `probe_common.adjudicate_pins(divergent,
  pinned)`; the recorded M6 verdicts (`PRED_PINS`, `LOSS_PINS`, report §§3–4)
  as adjudication *sources* — never re-litigated.
- Produces: `corpus/observation/panel.json` — per proto_path per file:
  `"pass"` | `{"pinned": <pin-name>}` | `{"unpinned": {family: evidence}}`;
  `PANEL_PINS: dict[str, Pin]` in the module (separate table; do not reuse
  `PRED_PINS` rows — cite them in pin notes instead). Task 11 reads this
  file as Factor E.

- [ ] **Step 1: run over all 1944 pairs** (job: `uv run python
  scripts/invariant_panel.py --all`). Measure wall-clock (hypothesis: same
  order as the sweeps' 3.31 s + fingerprint cost; report actual). Bucket
  every non-pass by family and file.
- [ ] **Step 2: adjudication.** Expected structure of the diff population
  (hypotheses): the 6 `real-bug` files flag (pin each with a note citing the
  M6 report section and the `pred_repairs` disposition); the 12
  `equivalent-transform` files may flag on gain-side counters or constants
  (pin citing the recorded verdict); genuinely new unpinned rows are
  **findings — escalate to the controller before pinning**, since a new
  unpinned row is exactly the class the panel exists to catch. Every pin
  carries an ASCII pc/opcode note.
- [ ] **Step 3: gates.** (a) pin-gate test: `adjudicate_pins` over the fresh
  scan's non-pass set vs `PANEL_PINS` → unexpected/moved/gone all empty;
  (b) fixed-point test: regenerating `panel.json` is byte-identical;
  (c) a cheap summary pin (counts per verdict class) so the suite arm stays
  small — the full scan is a job with the four out-of-suite conditions
  written into the CLI docstring (trigger: before Task 11 and at close).
- [ ] **Step 4: suite-cost attribution** — measure the added suite time,
  attribute to the formal-verification earmark in the task report.
- [ ] **Step 5: commit.**

### Task 5: Readability revision — fallback `str_lit` UTF-8 (partner gate FIRST)

**Files:**
- Modify: `src/pyluadec/structure/fallback.py` (`str_lit`)
- Modify: `src/pyluadec/emit/lua.py` (`_str_lit` delegates to the single
  implementation instead of carrying its own copy — one judgment, two call
  sites; verify current shape before editing)
- Modify: `CLAUDE.md` (red-line section: the second scope revision),
  `docs/superpowers/specs/2026-08-09-pyluadec-refactor-overall-design.md`
  (§2 decision-table row)
- Test: `tests/test_fallback_readability.py`

**Interfaces:**
- Consumes: the existing reversibility judgment (strict UTF-8 decode →
  re-encode reproduces the bytes → non-pure-ASCII prints raw; else decimal
  escape) currently implemented in `emit/lua.py::_str_lit`.
- Produces: `structure/fallback.py::str_lit(b: bytes) -> bytes` applying the
  same judgment. Both spellings compile to the same constant.

- [ ] **Step 0 (BLOCKING): partner approval.** Present to the human partner,
  as its own decision: the exact CLAUDE.md amendment text (the 2026-08-12
  carve-out's "只落在 `emit/`" / "不得扩大这个口子" sentences replaced by a
  two-site scope with the same machine-checked invariance), the spec §2
  decision-table row, and the evidence plan below. **No code before the
  yes.** If the partner declines, the task closes as "declined, recorded"
  and Task 11 ships fallback text escaped — the spec's exit criterion 3
  drops with a recorded disposition, not silently.
- [ ] **Step 1: failing test** — a synthetic chunk that ships fallback
  (e.g. any `while` with a shape `build_sir` refuses, or force via
  `structure.fallback.emit_chunk` directly) containing a Japanese string
  constant; assert the emitted bytes contain the raw UTF-8 sequence and not
  its decimal escape; a `_LONE_CONT`-style invalid sequence still escapes
  (reuse the fixtures in `tests/test_emit_readability.py`).
- [ ] **Step 2: implement** — move the judgment into
  `structure/fallback.py::str_lit`, make `emit/lua.py::_str_lit` call it
  (or keep `_str_lit` as the judgment's home and have fallback call it —
  pick the direction that keeps `emit` importable from `structure` without a
  cycle; state which and why in the commit).
- [ ] **Step 3: invariance evidence** — `PYLUADEC_CORPUS_DIR=… uv run python
  scripts/run_corpus.py` then `git diff --exit-code corpus/ledger.jsonl`
  (byte-identical = the presentation-layer definition holds); full suite
  green (the fallback differential tests re-run under the new spelling).
- [ ] **Step 4: the measurement** (spec §4 acceptance): over
  `build/decompiled/`, fraction of non-ASCII string constants presented raw
  (expect ≈ 1.0 — the corpus measured 0 non-UTF-8 in 49063); a spot-check
  test asserting `doScriptScene(` call sites in the still-fallback files
  carry raw UTF-8 arguments.
- [ ] **Step 5: CLAUDE.md + spec decision row** (the approved text,
  verbatim). **Step 6: commit.**

### Task 6: `config.lua` — investigate-first repair

**Files:**
- Test: extend whichever mechanism test file the diagnosis lands in
- Modify: TBD by diagnosis (candidates: `express/names.py`,
  `express/freereg.py`, `express/reconstruct.py`)

Current hypothesis (re-derive): `config.lua:main` refuses
`mismatch: maxstacksize` at root — one row, one occurrence, holds the whole
file. It is in the `mismatch: maxstacksize` ×11 own-root family, so its
diagnosis likely names mechanism C or E territory — or a new mechanism,
which is a finding to report, not to stretch.

- [ ] **Step 1: diagnose.** Single-file run (`structured-pipeline.md`
  "Common operations"), compare `luac_sz4 -l -l` of original vs our
  recompile, locate the first stack-size divergence, and name the mechanism
  (A–E or new). Report before fixing if it is new.
- [ ] **Step 2: minimal synthetic repro** (never start from the corpus
  file) → red test asserting the repro certifies `L3`.
- [ ] **Step 3: fix; green; corpus.** Regenerate ledger; expect
  `config.lua` → fully structured (whole-file flip, +1 occurrence at least);
  `ratchet_diff.py` vs `3669950` upgrades only.
- [ ] **Step 4: fault injection** per the guard discipline if a guard was
  touched; **Step 5: ledger + ratchet + commit.**

### Task 7: Mechanism D — the clamp / conditional-value shape (3 own rows)

**Files:**
- Modify: `src/pyluadec/sir/regions.py`, `src/pyluadec/sir/build.py`,
  `src/pyluadec/express/reconstruct.py`, `src/pyluadec/emit/lua.py` (only
  the subset the design lands on)
- Test: `tests/test_sir_condassign.py` (new)

**Interfaces:**
- Consumes: the runbook's diagnosed shape (`structured-pipeline.md` "a
  fourth mechanism"): `SUB/ADD r; LT/LE test; JMP; LOADK r; join; read r` —
  source `local v = a - b  if v < LIM then v = LIM end  use(v)`. Exemplars:
  `snr_common:main_69` (R7), `snr_s5_10_s:main_42` (R11), `main_43` (R9).
- Produces: certification of the clamp family. The spec's mechanism sketch
  (a statement-level conditional-assignment region; `regions.CondValue`
  covers only the `TESTSET` idiom) is a **hypothesis** — if the diagnosis
  shows a classification fix (grading the clamped register a local across
  the join) certifies without a new region, take the smaller change and
  record why. Prescribe the property (the three rows certify, ledger
  monotone), not the mechanism.

- [ ] **Step 1: synthetic repro red** — compile the clamp source, assert
  `L3`; currently refuses `reconstruct: register … staged value`.
- [ ] **Step 2: design decision measured** — try the classification route
  first (cheaper); if it breaks any existing test or the pc-claim audit,
  build the region node (recognize or `StructureError`, `all_claimed` holds,
  dominator single-entry extended).
- [ ] **Step 3: corpus** — expect the 3 own rows `L3` and the 2 inherited
  `reconstruct:` ancestors (`snr_common:main`, `snr_s5_10_s:main`) to lose
  this particular reason (they may still refuse on other descendants —
  measure, don't assert). Ledger + `ratchet_diff.py` zero downgrades.
- [ ] **Step 4: fault injections** (mis-grade the clamp register, drop the
  join read) each caught by certification. **Step 5: commit.**

### Task 8: Mechanism C — `_same_block` (6 rows)

**Files:**
- Modify: `src/pyluadec/express/freereg.py` and/or `express/reconstruct.py`
- Test: `tests/test_express_sameblock.py` (new)

**Interfaces:**
- Consumes: the one-line repro (`g(a and 1 or 2)` → staged callee split from
  its `CALL` by the `and`/`or` jump → `maxstacksize` mismatch); the 6
  measured rows (`snr_graphic:main_2`, `snr_memory:main_2`,
  `snr_novel:main_2`, `snr_novel:main_3`, `snr_story_main:main_3` + its
  root). The `_same_block` guard is **load-bearing for execution-count
  correctness** (its docstring carries the proof) — the fix must extend what
  can be safely staged across a jump (e.g. when every instruction between
  definition and consumer is effect-free under `STRICT`), never neuter the
  guard.
- Produces: certification of the 6 rows (or a measured subset with named
  survivors).

- [ ] **Step 1: repro red** (`g(a and 1 or 2)` certifies `L3`).
- [ ] **Step 2: implement the safe extension**; the guard's existing
  neuter-proof test must stay red-on-neuter (re-run it).
- [ ] **Step 3: corpus measure** — how many of the 6 flip; name survivors
  with reasons. Ledger + ratchet. **Step 4: fault injection** (an
  effectful instruction between definition and consumer must still refuse).
  **Step 5: commit.**

### Task 9: Mechanism E + the attribution campaign (21 own unattributed rows)

**Files:**
- Modify: diagnosis-driven (likely `express/names.py` hazard sets)
- Modify: `docs/runbooks/structured-pipeline.md` ("What is left" section —
  every row's disposition recorded there, the residual census's home)
- Test: per-fix new tests; no test for attribution-only rows

**Interfaces:**
- Consumes: whatever remains non-`L3` after Tasks 6–8 (re-measure first —
  the 21 is a pre-campaign hypothesis and Tasks 6–8 will have moved it);
  M6 task 12's neuter-experiment methodology (neuter a candidate mechanism,
  re-certify the population, count movers — measurement only, guard
  restored).
- Produces: the spec §5 stop-loss — **every remaining non-`L3` row is either
  fixed or carries a named, recorded attribution attempt**. An attribution
  attempt = the mechanism hypotheses tried, the experiment run, and the
  observed result, one paragraph per row in the runbook section.

- [ ] **Step 1: re-measure the population.** Fresh ledger census; report the
  post-Task-6–8 counts against the plan's 21/10 hypothesis.
- [ ] **Step 2: mechanism E first** (the `hazard`-set consequence of A):
  build its minimal repro from the M6 diagnosis, fix if it names a
  fixable defect, measure movers.
- [ ] **Step 3: the campaign.** For each surviving own row: diagnose →
  either fix (with repro + injection discipline) or record the attempt.
  Batch ledger regenerations (one per fix, not per attempt); ratchet zero
  downgrades throughout.
- [ ] **Step 4: runbook census updated; commit** (may be several commits,
  one per fix).

### Task 10: Inherited-row verification

**Files:**
- Modify: `docs/runbooks/structured-pipeline.md` (census)

- [ ] **Step 1: regenerate + measure.** After Tasks 6–9, the 11 inherited
  rows (hypothesis) should dissolve exactly where their descendants were
  fixed — verify per row, don't assert. A row that persists after all its
  descendants certify is a **finding** (the inheritance join
  `tests/test_m6_exit.py::coverage_gaps` says it shouldn't happen).
- [ ] **Step 2: final campaign census** into the runbook + task report:
  fixed / attributed / inherited-dissolved counts, the spec §8.4 numbers
  (`< 40` strict, attribution-complete). **Step 3: ledger + ratchet +
  commit.**

### Task 11: Warranty generator, selection rule, `corpus/final/`

**Files:**
- Create: `scripts/warranty_build.py`
- Create: `corpus/final/` (229 files, generated, committed),
  `corpus/warranty.jsonl` (generated, committed)
- Test: `tests/test_warranty.py`, `tests/test_pin_opcodes.py`
- Modify: `docs/reports/m7-warranty.md` (§3: selection outcomes)

**Interfaces:**
- Consumes: `corpus/ledger.jsonl` (our side: `level`, `occurrences[].shipped`
  / `.hybrid` / `.l2`), `predrecert.recert_file` (Task 2),
  `corpus/observation/panel.json` (Task 4), `corpus/pred_repairs/` (the six
  repaired files + README), `pipeline.decompile_file` (our side's text),
  `PRED_PINS` / `LOSS_PINS` (for the standing opcode check),
  `ingest.load_file` + `lift.opcodes` decoding.
- Produces:
  - `corpus/warranty.jsonl` — one row per file:
    `{"file", "selection": "ours" | "pred-recert" | "pred-verbatim" |
    "pred_repaired-recert" | "pred_repaired-verbatim", "ours": {"t_min",
    "t_hist"}, "pred": {"t_min", "t_hist", "e_min", "e_hist",
    "unpinned": n, "wm": [proto_paths]} | null, "occurrences":
    [{"proto_path", "t", "e", "l2"}], "oracle": <same provenance rule as
    the ledger — `git log -1 -- vendor native`, never HEAD>}`.
  - `corpus/final/<name>.lua` — the selected side's text; for
    `*-recert` selections, `RecertOutcome.source`; for ours, the pipeline's
    chunk text; for `*-verbatim`, the pred file's bytes unmodified.
  - The selection rule as a pure function
    `warranty_build.select(ours_grade, pred_grade) -> str` implementing
    spec §6 verbatim: eligibility (unpinned > 0 disqualifies; no grade =
    ineligible), lexicographic `(T-min, E-min)` with `T3 > T2 > T-` and
    `id > Wm-strengthened panel-pass > panel-pass > panel-pinned`, tie →
    ours, no-eligible-side → generator refuses to write (exit non-zero,
    naming the file).

- [ ] **Step 1: failing tests for the selection rule** (pure function, no
  corpus):

```python
def test_unpinned_disqualifies():
    assert select(ours=("T-", "id"), pred=("T3", "panel-pass", 1)) == "ours"

def test_pred_recert_beats_our_fallback():
    assert select(ours=("T-", "id"), pred=("T3", "panel-pass", 0)).startswith("pred")

def test_tie_goes_ours():
    assert select(ours=("T3", "id"), pred=("T3", "panel-pass", 0)) == "ours"

def test_no_eligible_side_raises():
    with pytest.raises(SelectionError):
        select(ours=None, pred=("T3", "panel-pass", 1))
```

  (Exact signature refined at implementation; the four properties are the
  contract.)
- [ ] **Step 2: the standing pin-table opcode check**
  (`tests/test_pin_opcodes.py`, corpus-gated): every `O<n> OPNAME` /
  `P<n> OPNAME` pair in `PRED_PINS` and `LOSS_PINS` decodes to the named
  opcode at that 1-based pc in the respective corpus (absorbs M7 agenda 6's
  routed item). The generator runs the same assertion and refuses to write
  on mismatch.
- [ ] **Step 3: implement the generator.** Deterministic (sorted file
  order); Wm marking from the `pred_repairs` README's named protos;
  `l2` copied from the ledger where present.
- [ ] **Step 4: generate; fixed-point test** (regeneration byte-identical,
  corpus-gated with both env vars — same discipline as
  `test_ledger_ratchet.py`). Measure generator wall-clock; suite arm keeps
  only the fixed-point + selection-rule tests, full generation is a job
  (docstring: trigger = any ledger/panel/recert movement, and at close).
- [ ] **Step 5: worked outcomes into `docs/reports/m7-warranty.md` §3** —
  per-file selection table, the §6 "worked consequences" hypotheses checked
  against reality, every `*-verbatim` residue named with its refusal
  reason. **Step 6: commit** (two commits if the artifacts are large: code
  + tests, then generated data).

### Task 12: Documents of record, exit gates, close

**Files:**
- Create: `tests/test_m7_exit.py`
- Modify: `CLAUDE.md` (Phase 7 section), `CHANGELOG.md`,
  `docs/runbooks/m3-backlog.md` (M7 disposition table + M8 agenda seed),
  `docs/runbooks/structured-pipeline.md` (new regions/mechanisms,
  warranty pointer), `docs/superpowers/specs/2026-08-09-…overall-design.md`
  (§2 decision rows: the §4 red-line revision if approved, any go/no-go
  disposition), `docs/reports/m7-warranty.md` (final summary)

Exit assertions mirror spec §8 (floors below achieved values; every assert
message reports the achieved number):

```python
def test_m7_exit_artifacts_complete(warranty_rows):
    assert len(warranty_rows) == 229
    assert all(r["selection"] in PROVENANCE for r in warranty_rows)
    assert all(o["t"] and o["e"] for r in warranty_rows
               for o in r["occurrences"])

def test_m7_exit_no_unpinned_shipped(warranty_rows):
    for r in warranty_rows:
        side = r["pred"] if r["selection"].startswith("pred") else None
        assert side is None or side["unpinned"] == 0

def test_m7_exit_residual_strictly_below_40(ledger_rows):
    non_l3 = [r for r in ledger_rows if r["level"] != "L3"]
    assert len(non_l3) < 40

def test_m7_exit_readability_floor():
    # only if Task 5 was approved; otherwise this test records the
    # declined disposition and is skipped with that reason
    assert raw_utf8_fraction() >= 0.99
```

- [ ] **Step 1: write the exit test against the real schemas** (read the
  generated artifacts; check every field name against the tree).
- [ ] **Step 2: docs sweep** — every M7 number re-measured at the closing
  tree; superlative scan over everything written this milestone; CLAUDE.md
  Phase 7 section follows the house shape (定位 + 速查, details in runbook
  and report).
- [ ] **Step 3: decision-log rows**; **Step 4: full suite +
  `ratchet_job.sh` (exit 0, zero downgrades vs `3669950`) + suite-time
  attribution report + commit.**

---

## Explicit non-goals (spec §9 — recorded so they are not re-litigated)

- Corpus-wide L2 / enumerated driving (agenda 2/8/9); the `next`/`pairs`
  gap (3); probe wire-format hardening (4); `StructureError` attribution
  (5) — untouched unless the repair campaign trips over one.
- No `post_process/` / Zndnovel stage3 migration; `corpus/final/` is a new
  base in this repo.
- Quality aggregate stays an ungated observable.
- M1's Linux x86_64 verification (agenda 7) — still open, still not this
  milestone (flag in the M8 seed again).

## Self-review notes

- Spec coverage: §1 deliverables → T11; §2/§2.1 (two factors, panel,
  blindness) → T3/T4 + T2 (Factor T mapping); §3 (recert + go/no-go +
  strip trap) → T2; §4 (readability + partner gate) → T5; §5 (repair
  order + stop-loss) → T6–T10; §6 (selection) → T11; §7 (gates: fixed
  point, pin-table check, baseline move, suite terms) → T1/T4/T11/T12;
  §8 exit → T12; §10 shape followed with panel split into build (T3) +
  run (T4).
- Type consistency: `RecertOutcome` (T2) consumed by T11; `PanelResult`/
  `panel.json` (T3/T4) consumed by T11; `select` contract (T11) asserted by
  T12; T-grade vocabulary (`T3`/`T2`/`T-`) defined once in T2 and used in
  T11/T12; provenance vocabulary defined in T11 and asserted in T12.
- Numbers: all carry provenance (2026-08-15 at `6b6c1e3`) and are marked
  re-derive. The panel fixture sketches are labelled as sketches with an
  honesty escape hatch rather than pretending the pool-reorder pair is
  already constructed.

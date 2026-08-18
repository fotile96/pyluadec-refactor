# M8 Task 6 petition pack — prepared for the human partner, 2026-08-16

Per the amended plan (rung-bundle unit; one petition, one decision; no
comparator code before approval). Everything below is measured at the
current tree; the falsification record lives in the runbook census.

## Petition A — the NEWTABLE hint-masking rung (L3.3): RECOMMEND DECLINE

**What it is.** A new ladder rung that compares `NEWTABLE`'s B/C size
hints as always-equal (they are int2fb preallocation hints; the exact
boundary is 1..16 with 17 ambiguous, re-pinned this campaign).

**Affected rows (measured, not estimated).** Exactly ONE: 
`snr_common:main_24` — its recompile differs from the original by ONE 
instruction, the hint (`C=1` vs `C=3`); every other field, including the
constant lists, is byte-identical. The two other K1-census rows are NOT 
hint rows: `main_25`'s remaining mismatches live in its descendant 
`main_25_4` (busy-slot family), and `main_71` differs by **197 
instructions** (a constructor-shape cascade, register-shifted) plus a 
27-entry constant reorder. The inherited `snr_common:main` row does not 
dissolve with `main_24` alone (other descendants still refuse).

**The soundness argument FOR, stated fairly.** Hints affect only 
`luaH_new`'s initial array/hash sizing; table contents are set by the 
(elsewhere-identical) SETTABLE/SETLIST stream; `#t` follows value 
boundaries, not allocation.

**The hole AGAINST, with evidence.** The internal node-array layout 
depends on the allocation history, and **`next()`/`pairs()` order is 
observable through it** — this project has a measured instance: 
`snr_novel`'s L1.75 divergence existed precisely because the fallback 
emitted `{}` (hint 0) where the original carried a 29-entry hint, and 
CONVERGED when the constructor fix restored the real hint (M8 campaign, 
pin deleted as converged). A hint-masking rung would certify text whose 
iteration order can differ from the original's. `main_24`'s table is 
returned to its parent — whether anything iterates it is a cross-proto 
question no current instrument answers statically.

**Recommendation.** DECLINE. One row of yield against a comparator 
weakening with an observable-behaviour hole is the trade the amended 
plan itself names as the worst possible. If the partner wants the row, 
the precondition is a pairs-absence analysis over the table's consumers 
(new instrument, its own task).

## Decision B — the busy-slot family (emitter-side; NOT a rung)

Three gate-critical files, each held by one own row, all the SAME root: 
`snr_mainmenu:main_7` (3.5598x), `snr_graphic:main_4` (1.9509x), 
`snr_story_main:main_3` (1.6956x), plus `snr_common:main_25_4`, 
`main_76_2`. Root: the original re-evaluates loads fresh per use 
(callees, upvalue chains — `u1.library` twice, `keyPlaySE(...)` direct, 
`u10` as a bare for-init); our whole-function `declared` merges the busy 
slot's per-statement lifetimes, so the first materialization forces 
every later write through `lD_R = v; lD_R(...)` (+MOVE per site).

**Falsified approaches (all measured, all reverted clean).** (1) Let 
temp-graded defs stage over `declared`: 35 shipping regressions. (2) The 
K1-style fold cap: 157 (different family, same lesson: mid-stream 
emission changes reorder staging). (3) Reaching-def veto refinement: 
moot for main_7 — the value genuinely reaches the open reads.

**Options for ruling.**
- **B1 (review round).** A per-statement slot-liveness release of 
  `declared` — the principled fix, touches a load-bearing guard, needs 
  its own review round with neuter proofs. Cost: a dedicated session; 
  yield: potentially all five rows and all three gate files.
- **B2 (corpus-informed opt-in).** Emit fresh re-evaluation for 
  pure-under-this-corpus loads (GETUPVAL always; GETGLOBAL given the 
  measured absence of `_G.__index` in all 229 files — the M4 census). 
  This is a knowledge-based emission choice, sibling to the M4 
  NO_METAMETHOD precedent (opt-in, corpus-measured, stated where used). 
  Cost: smaller than B1; the argument is corpus-scoped, not universal.
- **B2 — MEASURED AND REJECTED (2026-08-16, the day of the ruling).**
  Implemented at `write_reg` (pure loads — `UpvalExpr` always,
  `GlobalExpr` under the measured no-`_G.__index` corpus argument —
  staging over a `declared` slot when the def grades temp): the emission
  improves exactly as intended (`keyPlaySE(seName.circle)` direct where
  the text had `l1_11 = keyPlaySE; l1_11(...)`) but the corpus moved
  **8 rows to regression** (`snr_memory:main_4` structured -> fallback
  among them; 1929 -> 1926 shipped structured) with **zero
  improvements**. The mechanism is the same invariant the broad
  inversion broke, just rarer: a staged load pops at its first read; a
  LATER name-read of the slot then prints a local that was never
  assigned the new value. Whether such a later read exists is precisely
  the liveness question -- which only B1's machinery can see. **B2 at
  the write_reg layer therefore requires B1 as a precondition, not as a
  successor**; the partner's "provided B2 does not foreclose B1"
  condition resolves as: B2 cannot stand alone. Reverted same session;
  ledger verified byte-identical post-revert.
- **B3 (stop-loss).** The five rows stay attributed (they already are). 
  CONSEQUENCE THE PARTNER MUST WEIGH: `snr_mainmenu` stays 3.56x and 
  **exit criterion 3 (<= 1.5x per file) fails** — B3 therefore also 
  requires re-scoping that criterion, a separate decision.

## Disposition C — `snr_common:main_74_18` (slack + code)

Maxstacksize BELOW the original plus a code co-mismatch — the slack is 
dead-register reservation invisible in the bytecode (no source exists to 
reconstruct it from); the code half has not been decomposed further. Not 
rung-amenable (code differs). Options: attribute-and-hold (it is one 
occurrence in a hybrid file at 1.16x footprint — within the ceiling), or 
one more diagnosis round on the code half. Recommendation: hold; the 
file is already within every gate.

## main_71 — recorded, no petition

197-instruction constructor split + pool reorder. Byte-exact was 
attempted (the fold cap) and falsified. Any masking deep enough to cover 
197 reordered instructions would not be a normalization, it would be 
"compare nothing". Stays attributed unless the busy-slot ruling (B1/B2) 
changes the constructor emission underneath it.

## B1 charter and first-increment record (2026-08-16)

**Charter (the review round's terms, per the ruling).**
- Goal: align the TEXT's local scopes with the ORIGINAL's register
  lifetimes, releasing the busy-slot family (`main_3`, `main_4`,
  `main_7`'s callee half, `main_25_4`, `main_76_2`).
- Mechanism: (1) a bytecode-liveness oracle (per-pc live-in sets,
  backward fixpoint over the instruction graph; open reads conservatively
  live-in every register at/above their base — the veto's own
  conservatism, costing certifications never correctness); (2) at
  `force_materialize`, wrap the LocalDecl in a `do ... end` when the
  slot's death pc (first live-in excluding it) falls within the current
  `stmts_for` batch AND the slot is in no CLOSURE's captures (the
  lifter's whole-function `captured_regs` — a captured local's block end
  emits CLOSE, bytecode-visible); (3) release `declared[reg]` at the
  death pc so later temp-graded defs stage into the freed slot.
- Neuter obligations (before any keep): (a) liveness bug injection — a
  name-read after release prints a GLOBAL read, certification-visible;
  (b) capture-guard neuter — a captured slot scoped anyway must gain a
  CLOSE and fail; (c) unbalanced-block injection — DoEnd landing outside
  its batch must fail, not print malformed Lua; (d) the three refusal
  pins (`main_7`/`main_3`/`main_4`) flip to L3.
- Standing evidence for the design: B2's 8 regressions proved staging
  without scope-release breaks on later name-reads — B1 releases the
  SCOPE ITSELF, which is the structural fix; the 35-regression broad
  inversion and the 157-regression fold cap bound the design space from
  the other side.

**First increment: implemented and REVERTED same session (15 synthetic
regressions, `mismatch: maxstacksize` family).** The full mechanism
above was coded (liveness oracle, death-pc scoping with the batch and
capture guards, DoBegin/DoEnd statements + printer arms) and the
adjacent batches went 15-red — the release timing fires too early for
at least one shape (a released slot's later read degrades, maxstack
grows). The tree was restored to green (66 passed batch, refusal pins
intact); the increment's design survives in this charter. Next entry
point: instrument ONE failing fixture (`test_a_generic_for_over_a_call_
prints_one_iterator_expression[0]`) — the generic-for iterator triple's
control slots are the likely collision (their staging may legitimately
outlive the batch-window liveness model).

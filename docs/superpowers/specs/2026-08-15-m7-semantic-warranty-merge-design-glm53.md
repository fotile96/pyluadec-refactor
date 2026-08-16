# M7 — Semantic warranty and best-of merge (design spec)

> **Provenance (this document is one of several independently authored M7
> proposals, comparison intended).**
>
> - **Author**: Claude Code agent session (Claude Agent SDK harness), underlying
>   model **glm-5.3[1m]** (1M context). Filename suffix `glm53` keys this copy.
> - **Session context**: this session closed the M6 final-review loop — it
>   dispatched the fix-round re-review and committed its corrections
>   (`e726d1f`), then merged-clean was confirmed by the controller session
>   (`3b5f780` independently re-ran eight of the re-review's claims). The
>   author therefore carries first-hand context on the M6 instruments, their
>   measured capability boundaries, and the residual populations this spec
>   targets.
> - **Written at**: master `3669950` (the M6 merge point), branch
>   `phase7-m7-semantic-warranty-glm53`, 2026-08-15.
> - **Numbers**: every figure below was measured in this session against
>   `3669950` unless a date says otherwise; all are marked re-derive at task
>   start per the house rule (a stated number is a hypothesis about a tree).

## 0. Problem

The M6 close left the decompiler at `L3` **1438/1478 unique protos (97.3%) /
1904/1944 occurrences (97.9%)**, with **217 files fully structured / 8 hybrid /
4 whole-file fallback** (M6-close figures, 2026-08-14). The predecessor's
shipped corpus — the only artifact with real human-through-playthrough backing —
carried **6 confirmed defects, all repaired** in `corpus/pred_repairs/`
(instruction-level + runtime dual validation). Neither artifact is uniformly
the best: our side has uncertified fallback text in 4 files and unverified
hybrid holes in 8; the pred side is byte-divergent everywhere
(0/229 files recompile field-exact) and its warranty is adjudicative, not
arithmetic.

The localization project needs **one corpus to translate against, with a
defensible per-file statement of how sure we are**. Bytecode-level strict
identity is not attainable for the whole corpus; what is attainable is a
**graded, quantified, recorded warranty** — every file carrying the strongest
evidence its protos can actually support, and the source (ours vs predecessor
vs repaired-predecessor) chosen per file by that evidence.

## 1. Deliverable (decided with the human partner, 2026-08-15)

1. **`corpus/final/`** — the merged 229-file corpus, per-file best-of
   selection between our structured output and the predecessor corpus
   (including its six repaired files), plus a provenance column per file.
2. **`corpus/warranty.jsonl`** — the per-file semantic warranty record:
   per-occurrence rung, file-level minimum and histogram, evidence pointers,
   selection decision with both sides' grades.

Both are **generated artifacts**: produced whole by a script, committed,
regeneration byte-identical (ledger-ratchet discipline, no hand edits).

## 2. Scope (decided with the human partner, 2026-08-15)

**Active work** (fix, not just record):

- the structural residual: **40 non-`L3` ledger rows**, the **4 whole-file
  fallback files**, the **8 hybrid files' uncured subtrees** — mechanisms
  C/D/E of `Reconstructor.write_reg`'s `declared` gate plus the unattributed
  population;
- **pred_repairs same-criterion-ization**: the six repaired files enter the
  same record schema and the same selection rule (no re-litigation of the
  repairs themselves — their instruction-level + runtime evidence is the
  `Wm` rung, M6 already closed it).

**Record-only** (evidence assembled from existing adjudications, zero new
evidence work):

- the **12 `equivalent-transform`** cross-corpus divergences;
- the **dynamic-coverage boundary**: L2 reach stays 1 file, 164
  `taint-static` refusals and the truncation residue stay as recorded
  limitations (M7 agenda item 2 remains open for a later milestone).

## 3. The warranty ladder

Five rungs, each **anchored to an existing instrument's output** — the record
invents no new evidence, it aggregates. Ordered by evidence strength:

| rung | name | quantified meaning | anchored to |
|---|---|---|---|
| **W3** | bytecode-exact | recompilation matches the original proto tree field-for-field at the L3.1 rung (strip-lineinfo) | `verify.certify.certify_l3` |
| **W2** | structure-exact | the hybrid contract: this proto's own fields (`code`, `maxstacksize`, …) compared field-exact in the recompiled hybrid chunk; descendant closures replaced by fallback inlines are excluded from the claim and carry their own rung | `structure.structured.certify_hybrid` |
| **W1** | differential-agreement | original-vs-artifact trace byte-equality over a driven space (key sequences with coverage, or enumerated assignment product), with budgets and refusals explicit — never silently sampled | `probe_keyseq` (L2 gate), `probe_enum` |
| **Wm** | manual-verified | named instruction-level walkthrough **plus** runtime driver validation of the specific proto | the `corpus/pred_repairs/` pattern |
| **W0** | static-clean | zero **unpinned** signals across the applicable file-level instruments for that side; pins are adjudicated divergences and are recorded, not demerits | ours: `probe_global_state` / `probe_behaviour`; pred: the three cross-corpus arms + `loss_sweep` |

**Where `Wm` sits, and why it moved from the draft.** The design discussion
drafted the order `W3 > W2 > W1 > W0 > Wm`; this spec places **`Wm` above
`W0`** (flagged to the human partner at write time). Reason: `Wm` is targeted
dynamic-plus-instructional evidence on a named proto — defect-class-specific
and runtime-backed — while `W0` is whole-file static cleanliness with no
per-proto discrimination. Under the draft order, a repaired-and-playtested
predecessor file would lose to our uncertified fallback text on a file whose
probes are weak (exactly `snr_common.lua`'s situation: its L1.75 row is
`truncated:1/79`), which inverts the evidence. The reorder makes the selection
rule do what "best-of" means.

**Honesty notes the record must carry** (stated per file, not buried in a
doc): W1's reach is thin — 1 key-sequence file, 13 enumerated leaves (9
identical / 1 pinned-divergent / 1 budget-exceeded / 2 never-reached) — and
its known open paths (truncation residue, taint gaps) are documented in
`docs/runbooks/structured-pipeline.md` «The L2 gate». A W1 row therefore
states its coverage fraction and its instrument's caveats by reference. W0's
probes are structural (event-shape) comparisons; their blindness classes are
the L2 gate's documented "what it cannot see" list.

## 4. Artifacts and gates

- `scripts/warranty_build.py` — the generator (a **job**, not a suite member;
  suite-visible parts must be cheap and budget-attributed per the earmark
  rule). Inputs: `corpus/ledger.jsonl`, the probe/cross-corpus/loss-sweep
  adjudication tables, `corpus/pred_repairs/`, both corpora. Output:
  `corpus/warranty.jsonl` + `corpus/final/`.
- **Fixed point**: regeneration on unchanged inputs is byte-identical —
  guarded by a suite test, ledger-ratchet style.
- **Standing pin-table check** (absorbs the routed M7-agenda-6 item): the
  generator re-derives both corpora through `ingest` anyway; it asserts every
  `O<n> OPNAME` / `P<n> OPNAME` pair in `PRED_PINS` / `LOSS_PINS` against the
  decoded stream, making the M6 fix round's one-off re-base a standing gate.
- **Determinism**: the selection rule is a pure function of the record;
  same inputs, same output, tested.
- Engineering red lines unchanged: bytes stay `bytes` outside `emit/`'s
  sanctioned surface, no `re` in guarded packages, diagnostics carry no
  corpus-derived strings.

## 5. Residual repair plan (the critical path)

Baseline, measured 2026-08-15 at `3669950` from `corpus/ledger.jsonl`:

- **Whole-file fallback (4)**: `config.lua` (**1** occurrence — one refusal
  holds the whole file), `snr_common.lua` (**147**), `snr_music.lua` (**5**),
  `snr_novel.lua` (**15**).
- **Hybrid (8)**: `snr_graphic`, `snr_mainmenu`, `snr_memory`, `snr_s1_10_s`,
  `snr_s3_10_s`, `snr_s4_10_s`, `snr_s5_10_s`, `snr_story_main`.
- **40 non-`L3` rows by reason**: `mismatch: code` 14 · `mismatch:
  maxstacksize` 11 · `maxstacksize at root/*` 4 · `code at root/*` 5 ·
  `reconstruct: register … staged value` 5 (the clamp shape, mechanism D) ·
  `structure: pc 286 else-join` 1 (`snr_common:main_71`, the surviving
  `while true` recognizer gap). Of the 40, **29 own refusals / 11 inherited**;
  attributed 9 (6 `_same_block` = mechanism C, 3 clamp = D), **21 own + 10
  inherited unattributed** (M6 task-12 accounting).

**Order of attack** (mechanism × impact):

1. **`config.lua` first** — cheapest whole-file flip; investigation before
   commitment (a "trivial" root refusal may reveal a new mechanism class;
   report rather than stretch).
2. **Mechanism D** (clamp / conditional-value shape; the 5 `reconstruct:`
   rows) — minimal synthetic repro, fix, ledger monotone.
3. **Mechanism C** (`_same_block`; 6 rows inside the mismatch family).
4. **Mechanism E** (the `hazard`-set consequence of A) and the **21
   unattributed rows**: attribute each; attribution that names a fixable
   mechanism gets fixed in the same pass, attribution that meets real
   resistance is recorded with the attempt.
5. **11 inherited rows** dissolve with their ancestors — verify, don't re-fix.

**Discipline** (inherited from M6 tasks 11/12, non-negotiable): synthetic
minimal repro before any code change (never start from a 124 KB corpus file);
`ratchet_diff.py` against the milestone baseline after every repair (zero
downgrades); new guards ship with neuter/restore proofs; baseline numbers
re-measured at each task's start.

**Stop-loss** (the exit's residual floor): at close, ≤ **10** non-`L3` unique
rows may remain as "W0 + named attribution attempt" — **and
`snr_common.lua` must not be among them** (147 occurrences is too much weight
to leave on the fallback side; if its root-refusal family turns out to be a
new mechanism class needing more than this milestone, that is a controller
escalation and re-scope, not a silent stop-loss).

> **Amended 2026-08-16 (human partner, via the escalation clause above;
> recorded in the overall design's §2 decision table):** the floor is
> **22 rows + attribution-complete**. The escalation clause fired as
> designed: the attribution campaign measured the residual at **8 mechanism
> families**, 7 of whose rows prior decisions already exclude (the int2fb
> hint encoding, the closed `L3.2` pool-order rung), so ≤10 was unreachable
> without reopening decided questions. Two known-fix families were fixed
> first (the key-staged-below-table barrier, the NEWTABLE-position
> lookahead) taking 28 → 22. The `snr_common` clause is rewritten to the
> measurement: the file ships **hybrid** with 106 of its 147 occurrences on
> structured text; the "147 on the fallback side" fear is 41, not 147. The
> `L3.3` NEWTABLE-hint-masking rung (which would certify the K1 five) is
> recorded as an M8 candidate, not opened here.

## 6. pred_repairs under the same criterion

The six files' per-proto grading, from the committed ledger (2026-08-14):
`snr_common:main_75` and `snr_music:main_3` are `L3` on our side (W3 when we
ship them); the four mismatch protos (`snr_common:main_76_2`,
`snr_mainmenu:main_7`, `snr_graphic:main_4`, `snr_memory:main_4`) carry
`mismatch: code` / `mismatch: maxstacksize` on our side and **Wm** on the
repaired side. The six
files' current our-side split — `snr_common`/`snr_music` whole-file fallback,
`snr_mainmenu`/`snr_graphic`/`snr_memory` hybrid — means the winner is
genuinely per-file measured, not preset. Every selected file records its
provenance (`ours | pred | pred_repaired`).

## 7. Selection rule

Per file, per side (our artifact; pred corpus incl. repairs):

1. **Grade** each shipped occurrence (rungs per §3); file grade =
   `(min rung, rung histogram, unpinned-signal count)`.
2. **Eligibility**: a side is eligible iff min rung ≥ W0 **and** unpinned
   signals == 0. A **pin** is a divergence sitting in the instrument's
   adjudicated table (`PRED_PINS`, `LOSS_PINS`, the probes' `EXPECTED_*`
   entries); **unpinned** is a signal the instrument reports that no table
   explains. Pins are fine (recorded); unpinned signals disqualify that
   side's text for that file.
3. **Winner**: among eligible sides, higher min rung; tie → histogram
   compared from W3 down; still tied → **ours** (maintainability, output
   surface v2).
4. No eligible side = milestone failure for that file (exit-gated; must not
   happen at close).

Worked consequences (checked against current populations): our structured
files win outright (W3-density); the six pred_repaired files win over our
fallback/hybrid text until our side there reaches W2+; `snr_common` stays
`pred_repaired`-sourced until the key path fixes its root refusals, then
flips to ours.

## 8. Exit criteria

Floors sit below expected achieved values (house rule: a floor at the
measured value is a tripwire, and the standard fix for a tripwire is the
threshold — which is how gates die).

1. `corpus/warranty.jsonl` + `corpus/final/` regenerate byte-identical
   (fixed-point test in suite).
2. Coverage: 229/229 files, every occurrence graded, selection and
   provenance recorded for each.
3. Every file has ≥ 1 eligible side; the selected side's min rung ≥ W0 with
   zero unpinned signals.
4. Our-side non-`L3` unique rows ≤ **10**, `snr_common.lua` not among them.
5. Every sub-W2 proto on a selected side carries a named reason (count
   reported; the count itself is not gated — a missing reason is the
   failure, not the number).
6. Ledger ratchet vs **`3669950`** (default baseline moved at exit): zero
   downgrades.
7. Full suite green; `scripts/ratchet_job.sh` exit 0 with both corpus vars
   (the M6 requirement stands).
8. The standing pin-table check (§4) green.

## 9. Non-goals

- **No new dynamic instruments**: corpus-wide Class-1 / Class-2 driving
  (M7 agenda 8/9) stays deferred; W1 remains as thin as its existing reach —
  the records say so.
- **No taint-gap work** (agenda 2): the 164 refusals and truncation residue
  stay recorded limitations.
- **No re-litigation** of the 12 `equivalent-transform` verdicts or the 6
  pred_repairs repairs.
- **No gate relaxation** of any kind; the certification ladder, ledger
  discipline, and bytes red line are untouched.
- **No downstream migration**: `post_process/` / Zndnovel stage3 are out of
  scope; the merged corpus is a new base in this repo. The heterogeneous
  surface (our v2 style + pred text where pred wins) is a recorded property;
  whoever consumes it decides how to cope.
- Quality aggregate (`0.977328` at M6 close) stays a dashboard observable
  per the 2026-08-13 decision — it appears per file in the record ungated.

## 10. Milestone shape (sketch; writing-plans details it)

1. Baseline re-measure + ladder formalization: schema, generator skeleton,
   fixed-point gate, standing pin-table check.
2. `config.lua` quick win (investigate-first).
3. Mechanism D close.
4. Mechanism C close.
5. Mechanism E + the 21-row attribution campaign.
6. Inherited-row verification.
7. Full merge run + pred_repairs ingestion.
8. Documents of record, decision-log rows, exit gates, ratchet.

## 11. Risks

- **Mechanism E / the 21 unattributed rows resist.** Mitigation: the
  stop-loss is explicit and evidenced (named attempts), and the milestone's
  value does not rest on zero — it rests on every remaining row being
  attributed and every file having an eligible side.
- **`snr_common.lua` scale**: 147 occurrences, 124 KB, the surviving
  `structure:` refusal and the deepest inherited chains live there. It is
  the single largest risk to the stop-loss; §5's escalation clause covers
  the bad case.
- **Heterogeneous merged surface** (two text styles in one corpus) — a real
  downstream cost, consciously accepted and recorded, not hidden.
- **W1/W0 thinness**: for most files the warranty below W2 rests on static
  evidence; this is the accepted boundary of this milestone, stated per
  record. The alternative — extending dynamic reach — was explicitly
  descoped by the human partner.
- **Instrument aggregation ≠ new evidence**: the record is exactly as honest
  as the instruments it cites. Their honesty notes travel with the records
  (§3).

## 12. Relation to the M7 agenda in `docs/runbooks/m3-backlog.md`

- Item 1 (reconstruction residual) **is** §5 — absorbed.
- Item 6 (engineering debt): the pin-table checker bullet is absorbed (§4);
  the rest untouched.
- Item 10 (cross-corpus leftovers): the 12 equivalent-transforms and the
  path-level `intentional-edit` caveat become record rows (§2); nothing
  re-adjudicated.
- Items 2, 3, 4, 5, 7, 8, 9 untouched and still open after this milestone.

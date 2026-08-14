# M7 — Certified best-of merge with a two-factor warranty (design spec)

> **Provenance (this document is one of several independently authored M7
> proposals, comparison intended).**
>
> - **Author**: Claude Code, underlying model **Claude Opus 5**
>   (`claude-opus-5`). Filename suffix `opus5` keys this copy.
> - **Session context**: this session was the **controller of the M5 and M6
>   SDD runs** — it dispatched and reviewed every M6 task, ran the final
>   whole-branch review loop, audited the re-review round executed by a
>   glm-5.3 session, and performed the merge to master (`3669950`). It
>   carries first-hand context on every M6 instrument, the review rounds'
>   evidence gaps (`docs/reports/m6-cross-corpus.md` §7), and the residual
>   populations this spec targets.
> - **Written at**: master `3669950` + one committed sibling spec
>   (`a947141`, the glm-5.3 proposal), 2026-08-15.
> - **Sibling proposal**: `2026-08-15-m7-semantic-warranty-merge-design-glm53.md`.
>   This spec **adopts** two of its calls and **rejects** three, each with the
>   reason stated inline (§2, §5, §11). Divergences are flagged `[vs glm]`.
> - **Numbers**: every figure below was re-verified against `corpus/ledger.jsonl`
>   at `3669950` on 2026-08-15 unless a date says otherwise. House rule stands:
>   a stated number is a hypothesis about a tree — re-derive at task start.

## 0. Problem

The localization project needs **one corpus to translate against**, with a
defensible, quantified, per-file statement of how sure we are that it means
what the original bytecode means. Neither existing artifact is uniformly
best:

- **Ours** (M6 close): `L3` 1438/1478 unique protos (97.3%) / 1904/1944
  occurrences (97.9%); 217 files fully structured, **8 hybrid, 4 whole-file
  fallback** (`config.lua` 1 occ, `snr_common.lua` 147, `snr_music.lua` 5,
  `snr_novel.lua` 15). Fallback text is semantically exact but unreadable
  (`__pld_R` box model, decimal-escaped strings).
- **Predecessor** (with the six M6 repairs in `corpus/pred_repairs/`): human
  full-playthrough backing, but byte-divergent everywhere (0/229 recompiles
  field-exact; 3903 substantive mismatches over 1433 paths), its warranty
  adjudicative rather than arithmetic, and M6 proved the adjudication's
  reach: 6 real defects, 4 previously unknown.

Bytecode-level strict identity corpus-wide is not attainable. What is
attainable: every file ships the strongest text its evidence supports, the
evidence is *arithmetic wherever possible*, and the residual doubt is
quantified per proto — not per file, because M6 measured that file-level
cleanliness does not represent per-proto cleanliness (all 6 defects were
found by per-proto static comparison; 5 of 6 are invisible to both dynamic
arms).

## 1. Deliverables (decided with the human partner, 2026-08-15)

1. **`corpus/final/`** — the merged 229-file corpus. Per-file best-of
   selection; text is our **output surface v2 wherever certification
   permits**, including for predecessor-won files (§3).
2. **`corpus/warranty.jsonl`** — per file: every occurrence's two-factor
   grade (§2), the file-level minimum and histogram, the selection verdict
   with both sides' grades, and provenance
   (`ours | pred-recert | pred-verbatim | pred_repaired-recert | pred_repaired-verbatim`).
3. The repair campaign (§5) is **first-class work**, not a side effect: its
   purpose under this deliverable is to move files from the pred column to
   the ours column, and its results land in the same ledger/ratchet
   discipline as every prior milestone.

Both artifacts are **generated**: produced whole by one script, committed,
byte-identical on regeneration (ledger-ratchet discipline, no hand edits),
with the fixed point guarded by a suite test.

## 2. The two-factor warranty `[vs glm — the central divergence]`

The glm proposal grades each file on a single five-rung ladder
(`W3 > W2 > W1 > Wm > W0`). This spec splits the grade into **two orthogonal,
separately quantified factors**, because a single ladder conflates two
different questions and its bottom rung (`W0`, file-level probe cleanliness)
was measured in M6 to be the wrong granularity:

- **Factor T (text fidelity): how faithful is the shipped text to its source
  bytecode?** Arithmetic, per proto:
  - `T3` — `verify.certify.certify_l3` field-exact at the committed ladder
    (`l3-ladder-v1`, rung ≤ 1);
  - `T2` — the hybrid contract (`certify_hybrid`): this proto's own fields
    compared field-exact; replaced descendants carry their own grade;
  - `T-` — shipped verbatim without certification (fallback text, or
    pred text that our pipeline could not re-certify).
- **Factor E (source equivalence): how equivalent is that source bytecode to
  the ORIGINAL bytecode?** For our text the source *is* the original —
  Factor E is identity by construction and is recorded as `E=id`. For
  pred-side text it is graded per proto by the **invariant panel** (§2.1):
  - `panel-pass` — all panel families equal;
  - `panel-pinned` — every difference lies inside an adjudicated pin
    (`PRED_PINS` / `LOSS_PINS` / the probes' expected-divergence tables);
  - `panel-unpinned` — a difference no table explains. **Disqualifying.**
  The six repaired files additionally carry `Wm` — the M6 pattern of named
  instruction-level walkthrough plus runtime driver validation — as
  strengthening evidence on Factor E for the repaired protos. `[vs glm:
  their reorder of Wm above W0 is adopted; in this frame it needs no special
  pleading — Wm is simply stronger Factor-E evidence than a clean panel.]`

A file's grade is the pair of per-occurrence minima plus histograms. There
is no `W1` rung: dynamic evidence (L2, `probe_enum`) is **recorded where it
exists** (reach today: 1 file L2; 13 enumerated leaves) but grades nothing —
M6 measured 5 of 6 real defects invisible to both dynamic arms, so dynamic
cleanliness must not outrank or substitute for static per-proto comparison.

### 2.1 The invariant panel

A per-proto static equivalence verdict between a pred proto and its original
counterpart (the 1:1 tree correspondence is established — 229/229 files,
`tests/test_predcorpus.py`). Families, all already implemented by M6
instruments and here promoted from file-aggregates to per-proto verdicts:

- the four `loss_sweep` groups: `global_reads`; `n_natural_loops` +
  `n_back_edges`; `test_ops` (per-opcode: EQ/LT/LE/TEST/TESTSET); the
  fourth group (`global_writes`, `call_targets`, `call_shapes`,
  `return_arity`);
- the fingerprint arm's per-proto comparisons from `cross_corpus.py`.

Cost basis: the four sweeps measured **3.31 s** corpus-wide at the M6 wrap.
The panel is a pure function of two ingested trees; it lives beside the
existing sweeps, is corpus-gated in the suite the way `test_loss_sweep.py`
already is, and its runtime is attributed to the formal-verification earmark.

## 3. Approach A: re-decompile the predecessor side, don't transcribe it

For every file the selection rule awards to `pred` / `pred_repaired`, the
merged corpus does **not** copy the pred text. Instead:

```
pred .lua text → oracle luac_sz4 → ingest → our pipeline → certify_l3
                                                against the PRED bytecode
```

A proto that certifies ships as **`T3`-of-pred in output surface v2** —
byte-exact against what the pred text means, in our style, with readable
UTF-8. Factor E (pred vs original) is carried by the panel per §2.1.
A proto that refuses ships the pred text verbatim for its subtree
(`*-verbatim`), with the refusal reason recorded in the warranty row.

Feasibility evidence (M6, re-derive at task start): `build_sir` succeeded on
**12/13** pred leaf protos (92.3%); pred text is real-luac-compiled source,
structurally *easier* than the original stripped corpus. **The first task of
the milestone measures the full-population recert rate over all 1944 pred
protos** — that number sizes the `*-verbatim` residue and is a go/no-go
gate on this section: if the rate comes back so low that the merged corpus
would be mostly verbatim pred text (< 70% of pred-side occurrences
recertifying), the mechanism is reported to the human partner before any
merge work proceeds, not silently absorbed.

Gains over transcription `[vs glm]`: their spec lists "heterogeneous merged
surface (two text styles in one corpus)" as an accepted risk; this mechanism
removes most of it, converts the pred side's warranty from adjudicative to
arithmetic where it certifies, and pulls pred-won files under the same
certification discipline as everything else.

## 4. Readability repair (added by the human partner, 2026-08-15)

Requirement: calls carrying game text — `doScriptScene("…")` and its family
— must be readable in the merged corpus, because the downstream is
translation.

State: our v2 output already prints reversible UTF-8 as-is
(`emit/lua.py::_str_lit`, M5 task 7). The gap is
**`structure/fallback.py::str_lit`**, which decimal-escapes everything —
so the 4 fallback files and every hybrid-inlined fallback subtree print
Japanese as `\230\151\165…`.

Fix: extend the same reversible-UTF-8 presentation judgment to
`structure/fallback.py::str_lit` (strict decode → re-encode must reproduce
the original bytes → non-pure-ASCII prints as-is; anything else keeps the
decimal escape). **This is the second scope revision of the bytes red
line**, same shape as the 2026-08-12 revision recorded in CLAUDE.md:
presentation layer only, both spellings compile to the same constant, the
certification verdict is unchanged — and that invariance is machine-checked
by certification itself plus the fallback path's existing differential
tests. The revision must be recorded in CLAUDE.md's red-line section and in
the overall spec's decision table when implemented; `ingest`/`lift`/`verify`
still never decode.

Acceptance is measured, not asserted: the merged corpus reports the fraction
of non-ASCII string constants presented as raw UTF-8 (expected ≈ 100% —
the corpus measured 0 non-UTF-8 strings in 49063), and a test spot-checks
`doScriptScene`-family call sites in whichever files still ship any
fallback text.

## 5. The repair campaign

Baseline (re-verified 2026-08-15 at `3669950`): 40 non-`L3` rows = 29 own
refusals + 11 inherited. By reason: `mismatch: code` 19 (14 root + 5
`at root/*`), `mismatch: maxstacksize` 15 (11 + 4), `reconstruct:` clamp
shape 5, `structure:` 1 (`snr_common.lua:main_71`, the `while true`
recognizer gap). Attributed: 9 (6 mechanism C `_same_block`, 3 mechanism D
clamp); unattributed 21 own + 10 inherited.

Order of attack — adopted from the glm spec §5, which sequences it
correctly `[vs glm: adopted]`:

1. **`config.lua`** first — one own refusal holds the whole file;
   investigate before committing (a "trivial" refusal may name a new
   mechanism; report rather than stretch).
2. **Mechanism D** (clamp / conditional-value): the 5 `reconstruct:` rows.
   Needs a statement-level conditional-assignment region;
   `regions.CondValue` covers only the `TESTSET` idiom and there is no
   `TESTSET` here.
3. **Mechanism C** (`_same_block`): 6 rows.
4. **Mechanism E** (the `hazard`-set consequence of A) + the 21-row
   attribution campaign: every unattributed row gets either a fix or a
   named, recorded attribution attempt.
5. The 11 inherited rows dissolve with their ancestors — verify, don't
   re-fix.

Discipline unchanged: synthetic minimal repro before any pipeline change
(never start from a 124 KB corpus file); `ratchet_diff.py` zero downgrades
after every repair; new guards ship with neuter/restore proofs; baselines
re-measured at each task start.

**No `snr_common.lua` hard gate** `[vs glm — rejected]`. The glm spec makes
"`snr_common` must not remain non-`L3`" an exit condition with a controller
escalation. Under the merge deliverable that inverts the design's own logic:
if `snr_common` does not flip, it ships `pred_repaired-recert` — carrying
`Wm` on the two repaired protos, the panel on all 79, and re-certification
of the text — which is an acceptable *outcome*, not a milestone failure.
Gating the milestone on the single largest-risk file (147 occurrences, the
deepest inherited chains, the last `structure:` gap) converts the stop-loss
into a tripwire. The stop-loss here: **at close, every remaining non-`L3`
row is either fixed or carries a named attribution attempt** — the count is
reported, not gated.

## 6. The selection rule

Pure function of the warranty record; per file:

1. Grade both sides: ours `(min T, E=id, unpinned=0 by construction)`;
   pred side `(min T after re-certification, min panel verdict, unpinned
   count)`.
2. **Eligibility**: `panel-unpinned > 0` disqualifies a side. A side with
   no grade (e.g. pred text that fails even to compile) is ineligible.
3. **Winner**: lexicographic on `(Factor T minimum, Factor E minimum)`,
   comparing `T3 > T2 > T-` then `id > Wm-strengthened panel-pass >
   panel-pass > panel-pinned`. Tie → **ours** (maintainability; one style).
4. A file with no eligible side is an exit-gate failure and must not occur
   at close.

Worked consequences at today's populations (hypotheses — the generator
recomputes): 217 fully-structured files stay ours; `config`, `snr_music`,
`snr_novel`, `snr_common` and some hybrids contest, with the six
`pred_repairs` files favoured on their repaired protos until our side
closes the corresponding mechanisms.

## 7. Gates and engineering constraints

- Fixed-point regeneration of `corpus/final/` + `corpus/warranty.jsonl`
  (suite-gated, corpus-gated).
- **The standing pin-table opcode check** — absorbs the M7-agenda-6 item
  routed there by the M6 re-review: the warranty generator ingests both
  corpora anyway, so it asserts every `O<n> OPNAME` / `P<n> OPNAME` pair in
  `PRED_PINS` and `LOSS_PINS` against the decoded streams and refuses to
  write on mismatch.
- **Ratchet baseline moves to `3669950`** as the milestone's first commit
  (the default is still `0957364`; its own comment already promises "the
  last merged milestone tip").
- Suite: new cost must be attributable to the panel / re-certification /
  fixed-point instruments (the ~120 s earmark's terms, including the
  measured-not-predicted rule for anything routed out of suite).
- Red lines: unchanged except §4's explicit revision. Certification logic
  (`NORMALIZATIONS`, `LADDER_VERSION`, `compare_protos`, `_cmp`,
  `structural_hash`, `key_disagreements`) untouchable. `corpus/golden/`
  read-only; `vendor/` pristine; corpora only via env vars; no `re` in
  guarded packages; ledger written only by `run_corpus.py`.
- No re-litigation of the 12 `equivalent-transform` verdicts or of the six
  repairs; their evidence is consumed as recorded.

## 8. Exit criteria (floors below expected values, per house rule)

1. `corpus/final/` + `corpus/warranty.jsonl` exist, regenerate
   byte-identical, 229/229 files, every occurrence graded, provenance
   recorded.
2. Every file has an eligible side; every shipped occurrence's Factor E is
   `id`, `panel-pass`, or `panel-pinned` — zero `panel-unpinned` shipped.
3. Readability: the measured raw-UTF-8 fraction for non-ASCII constants in
   `corpus/final/` is reported and ≥ 0.99; the `doScriptScene`-family
   spot-check passes.
4. Our-side non-`L3` unique rows strictly < 40, and **every** remaining row
   fixed-or-attributed (§5 stop-loss). No numeric floor on the count
   `[vs glm: their ≤ 10 floor is rejected as unmeasurable-in-advance;
   the attribution requirement is the enforceable form]`.
5. Ledger ratchet vs `3669950`: zero downgrades. Full suite green;
   `ratchet_job.sh` exit 0 with both corpus vars.
6. The standing pin-table check green.
7. The §3 recert-rate measurement recorded, with the go/no-go disposition
   if it fell below the stated threshold.

## 9. Non-goals

- Corpus-wide L2 / enumerated driving (M7 agenda 2/8/9) — dynamic reach
  stays as recorded; the warranty says so per file.
- The `next`/`pairs` gap (agenda 3), probe wire-format hardening (agenda 4),
  `StructureError` attribution (agenda 5) — untouched unless the repair
  campaign trips over one, in which case it is fixed as part of that task
  with its own evidence.
- No `post_process/` / Zndnovel stage3 migration. `corpus/final/` is a new
  base in this repo; consuming it is the localization project's decision.
- The quality aggregate stays an ungated observable (spec §2 decision,
  2026-08-13).

## 10. Milestone shape (sketch; writing-plans details it)

1. Baseline re-measure; ratchet baseline move; **full-population pred
   recert-rate measurement** (the §3 go/no-go number); panel skeleton.
2. Panel implementation + per-proto verdicts committed as an observation
   artifact (fixed-point).
3. Readability revision (§4) with its red-line paperwork.
4. Repair campaign §5.1–5.3 (config.lua, D, C).
5. Repair campaign §5.4–5.5 (E, attribution, inherited).
6. Warranty generator + selection + `corpus/final/` emission.
7. Documents of record, decision-log rows, exit gates, ratchet.

## 11. Risks

- **The pred recert rate is unmeasured beyond 13 leaves.** Mitigated by
  measuring it first (§3's go/no-go) before any dependent work.
- **Mechanism E / the 21 unattributed rows resist.** The stop-loss is
  attribution-complete, not count-bounded; the milestone's value does not
  rest on zero.
- **`snr_common.lua`** may stay pred-sourced. Accepted outcome by design
  (§5); the risk is reputational ("the biggest file isn't ours"), not
  semantic — its shipped text would carry Wm + panel + recert.
- **Panel families may be too coarse for some proto pairs** (a real defect
  inside a family the panel doesn't measure). The panel's blindness classes
  must be listed in its module docstring the way the L2 gate's are; the
  warranty inherits exactly that honesty. `[vs glm: adopted — their §3
  "honesty notes travel with the records" clause, generalized to the panel.]`
- **Two generated artifacts of nontrivial size** (`corpus/final/` ~2–3 MB).
  Same discipline that already governs `footprints.json` (2.1 MB) applies.

## 12. Relation to the M7 agenda (`docs/runbooks/m3-backlog.md`)

- Agenda 1 (reconstruction residual) **is** §5.
- Agenda 6: the pin-table checker bullet is absorbed (§7); the ratchet
  baseline bullet is absorbed (§7); the rest untouched.
- Agenda 10 (cross-corpus leftovers): consumed as warranty rows (§2/§6).
- Agenda 2, 3, 4, 5, 7, 8, 9: open after this milestone (§9).

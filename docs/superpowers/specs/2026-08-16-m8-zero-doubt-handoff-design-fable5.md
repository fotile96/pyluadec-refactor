# M8 — Zero-doubt handoff: certification completion, footprint gate, readability port (design spec)

> **Provenance.**
>
> - **Author**: Claude Code, underlying model **Claude Fable 5** (filename
>   suffix `fable5`). Same physical session as the `opus5` M7 spec — the
>   human partner switched models mid-session (recorded here because this
>   repo's spec provenance is keyed by model; the M7 spec's rev 3 review was
>   likewise a Fable 5 pass on an Opus 5 document).
> - **Session context**: controller of the M5/M6 SDD runs; author of the M7
>   design spec; independent reviewer of M7 task 11 (five findings, all
>   confirmed and disposed by task 12).
> - **Written at**: `72cb6a8` (M7 task 12, milestone close) on branch
>   `phase7-m7-semantic-warranty-glm53`, 2026-08-16. **The M7 branch is not
>   yet merged**; §7 makes the merge a prerequisite, not part of M8.
> - **Numbers**: measured 2026-08-16 at `72cb6a8` unless dated otherwise.
>   House rule: a stated number is a hypothesis about a tree — re-derive at
>   task start.
> - **Partner decisions recorded in this spec** (2026-08-16, this session):
>   byte-exact-first with rungs as licensed exceptions (§2); the 1.5×
>   footprint ceiling (§3); readability targets the new artifact itself, with
>   a migration guide for Zndnovel rather than surface compatibility (§4);
>   fallback is tolerable for text-free protos only within the footprint
>   budget (§1).

## 0. Problem

M7 shipped `corpus/final/` + `corpus/warranty.jsonl` with **1456/1478 unique
protos (98.5%) / 1922/1944 occurrences at `L3`**, 222/229 files fully
structured. What stands between this artifact and a genuinely seamless
localization handoff is three residues, and they turn out to be mostly the
same residue:

1. **64 occurrences still ship fallback text** (5 hybrid files + 2
   whole-file: `snr_music`, `snr_novel`), caused by the **22 non-`L3`
   rows**. Fallback text is unreadable (the `__pld_R` box model carries 52
   lines of game dialogue — the pinned M8-agenda-1 residual), untranslatable
   in place, and — decisive, measured this session — **compiles to 2.4–3.6×
   the original bytecode** (`snr_mainmenu` 3.56×, `snr_music` 3.34×,
   `snr_novel` 2.88×, `snr_graphic` 2.40×, `snr_common` 1.40×; fully
   structured files are exactly 1.00×). The localization project's bilingual
   experiment (every `vms` line duplicated ≈ 2× text) already produced PSP
   runtime heap exhaustion at save/load, so 2.4–3.6× on `snr_mainmenu` — a
   permanently loaded script — is a real hardware risk, not an aesthetic
   one.
2. **Unknown semantic inconsistencies** are, by construction, confined to
   exactly the non-`L3` residue: an `L3` proto is field-exact bytecode, so
   closing the 22 rows closes this too. The only way M8 could *create* a new
   inconsistency channel is by weakening the comparator — hence §2's
   licensing regime for normalization rungs.
3. **Readability**: our synthetic names (`l0_3`, `card`-less closures) are a
   real regression against the predecessor's hand-curated corpus, whose
   translation tooling (Zndnovel) additionally depends on hand-added
   annotations our regenerated artifact does not carry.

Eliminating fallback therefore discharges the dialogue residual, the heap
risk, the ours-side `T-` duality (M8 agenda 2) and the unknown-inconsistency
surface **in one campaign**; readability and the handoff guide then operate
on a uniform, fully certified artifact.

**Partner tolerance, recorded**: for protos containing **no translatable
text**, fallback is acceptable *provided the file stays within the §3
footprint budget*. Measured today, every fallback-carrying file except
`snr_common` (1.40×) exceeds it, so this tolerance is expected to be
exercised rarely if at all — it is a stop-loss, not a plan.

## 1. Track 1 — certification completion: 22 rows → 0

Baseline (re-verified 2026-08-16 at `72cb6a8`; re-derive at task start):
**22 non-`L3` unique rows** = 15 own + 7 inherited, by reason:

| reason | rows | known clusters (M7 task 9/10 attribution) |
|---|---|---|
| `mismatch: code` | 8 | constant-pool order (`snr_story_main:main_3` const[70] `fileName`/`sysgim` class); expression layout (`snr_novel:main_2` pc-69 ADD-vs-GETUPVAL class) |
| `mismatch: maxstacksize` | 8 | K1 NEWTABLE hint-position masking (5 rows, M8 agenda 3); dead-slack residue |
| `reconstruct: register … read again` | 4 | task-8-linked staging refusals (`snr_graphic`/`snr_memory` `main`/`main_3` family) |
| `structure: pc 286: else-join out of range` | 2 | `snr_common:main_71` `while true` recognizer gap + its inherited ancestor |

**Discipline (partner decision, 2026-08-16): byte-exact first, rungs as
licensed exceptions.**

1. For every cluster, the first attempt is an **emitter/reconstruction
   change that makes recompilation byte-exact at the existing ladder**
   (rung ≤ 1). Example: constant-pool order follows luac's first-reference
   order, which our emitter controls by statement ordering choices that are
   themselves semantics-preserving — try that before touching the
   comparator.
2. A normalization rung may be **petitioned** only with evidence that
   byte-exactness is impossible by construction (a parser-direction
   argument: no Lua source luac would compile to that byte sequence — the
   M7 task-9 s3/s4 precedent). Each petition is **one rung, one partner
   approval, one `LADDER_VERSION` bump**, and the soundness argument lives
   with the rung's code (the `_strip_lineinfo` precedent). Candidates
   anticipated (not pre-approved): `L3.2` constant-pool order (compare
   constants as the instruction-resolved multiset plus an index-remap
   bijection check), `L3.3` NEWTABLE size-hint masking (preallocation only;
   argument from `ltable.c` — hints affect allocation, never observable
   semantics), maxstacksize dead-slack (ours ≥ actual usage, compared
   against a recomputed tight bound rather than luac's). **Every rung must
   state what `compare_protos` still proves after it** — the M3 rule.
3. The 2 `structure:` rows are recognizer work (extend `_match_loop` for
   the `while true` + `break`-to-exit shape), no comparator involvement.
4. Campaign discipline unchanged from M5–M7: synthetic minimal repro before
   any pipeline change; `ratchet_diff.py` zero downgrades after every
   repair; guards ship with neuter/restore proofs; certification gate,
   ledger, and the governing invariant untouched (a recognizer bug can
   still only lower the rate, never ship wrong code).

**Stop-loss**: any row still non-`L3` at close must be (a) attributed with
a named attempt record, (b) shipping fallback only if its proto carries no
translatable text (constant census: zero non-ASCII string constants and
zero `vms`-family call targets), and (c) inside the §3 footprint budget.
Expected count: 0; the stop-loss exists so the milestone fails loudly
rather than quietly if a cluster resists.

## 2. What "eliminating unknown inconsistencies" means here

With track 1 complete, every shipped occurrence is field-exact under the
ladder, and the ladder's rungs each carry a co-located soundness argument.
The *only* residual doubt channels are then (a) the rungs themselves —
bounded by the licensing regime above — and (b) anything outside bytecode
semantics (engine stub behavior, which no bytecode-level tool can see; the
L2/panel blindness lists already document this). M8 adds **no new dynamic
instruments** (M8 agenda 5 items stay open); it removes doubt by finishing
the arithmetic, not by adding probes.

## 3. Track 2 — the footprint gate

New instrument, cheap (one `compile_source` per file, memoized oracle):
per-file **`footprint_ratio` = len(recompiled bytecode of shipped text) /
len(original bytecode)**, recorded as a new field in `corpus/warranty.jsonl`
rows.

- **Exit gate (partner-set, 2026-08-16): every file ≤ 1.5×.** The expected
  end state after track 1 is 1.00× everywhere (an `L3` file's recompiled
  bytecode is field-identical), so 1.5 is a floor-below-achieved per house
  rule — headroom for the §1 stop-loss, not a target. The ceiling's
  motivation is the bilingual-experiment heap failure at ≈2× text; 1.5× is
  a policy line, **not** a hardware-measured limit, and the spec says so —
  if the localization project ever measures a real PSP heap budget, that
  number supersedes this one.
- The gate is a suite test over the committed warranty artifact (no
  compile at test time — the generator records the ratio; the fixed-point
  test already proves the artifact regenerates identically).
- The instrument also closes a blind spot permanently: any future
  regression that flips a big file back to fallback now fails **two**
  gates (ratchet + footprint) instead of one.

## 4. Track 3 — readability port + the Zndnovel migration guide

### 4.1 Semantic naming pass

Port the predecessor's stage-1 idea (semantic local renaming) into **our
naming layer** (`express/names.py` — names are already synthesized there;
this is not a text post-processor):

- **Mechanical, deterministic rules first** — names derived from evidence
  in the bytecode itself: a local receiving `CLOSURE` of proto N in a file
  whose call sites use it as a card/scene entry gets the predecessor-style
  name (`card_0_main`, `scene_s1s_20`); a table whose `SETTABLE` keys are
  drawn from a recognizable constant family gets that family's name
  (`plotTitle`-like); loop/index temps keep synthetic names. Rules are
  data-driven and deterministic (same bytecode → same names; the
  `corpus/final/` fixed point extends over naming).
- **Certification invariance is structural but re-proven**: local names do
  not exist in stripped bytecode, so renaming cannot move certification —
  nevertheless every naming change re-runs full certification and the
  ledger must be byte-identical (the M7 task-11 "presentation-layer change
  = ledger byte-unchanged" definition applies verbatim).
- Acceptance is measured, not asserted: a coverage figure (fraction of
  closure-bound locals in text-carrying files receiving semantic names)
  reported with its derivation, plus spot-check tests pinning specific
  names on specific files. No numeric floor — the floor is the spot-checks
  plus determinism; name *quality* judgments route to the partner via the
  guide's sample listings.

### 4.2 The migration guide (`docs/migration/zndnovel-handoff.md`)

The predecessor toolchain is retired; Zndnovel will develop its own
components, and accepts a controlled modification surface (partner
decision). The guide is a **deliverable document** covering, per facility
read from the Zndnovel tree at its commit `380a577`:

1. **`tools/extract_text.py` / `extract_dag.py` / `extract_crd.py`** —
   what each greps from the predecessor surface, what changes on ours
   (v2 style, `l<depth>_<reg>` → semantic names), and the recommended
   adaptation. **Recommendation, stated in the guide with a worked
   example: consume the new machine-readable text-unit inventory (§4.3)
   instead of re-anchoring regexes** — it removes the surface coupling
   that broke once already (the M5 `v\d+` anchor break).
2. **The `-- tr_line:N` annotations** (162 hand-annotated files): these
   mark translatable text embedded in structural calls. The guide maps the
   annotation *concept* onto our artifact: the inventory (§4.3) carries
   the same sites mechanically (string constants reaching call arguments,
   classified by call target), so hand re-annotation is not needed; the
   guide includes a reconciliation listing (pred `tr_line` sites ↔
   inventory rows) so Zndnovel can verify nothing was lost.
3. **The hand-edit patch layer**: known hand modifications in
   `lua_scripts/` (the `fontLoad` Chinese-font swap in `snr_common`,
   readable-name edits, any others found by diffing pred text against its
   own recompile) are enumerated so they can be re-expressed as explicit
   patches on `corpus/final/` rather than lost in the switch.
4. **The invariant that makes the switch safe**: `vms` message IDs
   (1..17220, the translation database's primary key) live in bytecode
   constants; on `L3` protos they are preserved **field-exactly** — cited
   to the certification evidence, not asserted.
5. **Validation, run from this repo without modifying Zndnovel**: run the
   three Zndnovel tools read-only against `corpus/final/` and diff their
   outputs against the committed `analysis/` snapshots; the guide reports
   the diff shape (identical / benign-formatting / needs-adaptation, per
   tool) so "controlled modification surface" is a measured claim.

### 4.3 The text-unit inventory (new generated artifact)

`corpus/text_units.jsonl` (or similar), generated from **bytecode
constants through the sanctioned presentation layer**, keyed by `vms`
message ID (plus file/proto_path/pc for non-`vms` translatable sites —
the `tr_line` class): one row per translatable text unit with its speaker
prefix, voice ID, and call context.

**Red-line consideration (explicit, because this artifact contains game
text)**: this is a *product output* in the same class as `corpus/final/` —
game text rendered through the same reversible-UTF-8 presentation judgment
(`str_lit`), not a diagnostic. The bytes red line's prohibition on corpus
content in diagnostics/pins/committed *analysis* artifacts is untouched;
the spec's §2 decision table gains a row naming this artifact class as
sanctioned output. Generation is a fixed point (regeneration
byte-identical), gated like the other artifacts.

## 5. Exit criteria (floors below expected values)

1. **Fallback occurrences shipping text: 0.** Every occurrence whose proto
   carries any translatable text ships structured (`shipped = "structured"`).
   Expected: 0 fallback anywhere; the gate is the text-carrying subset so
   the §1 stop-loss remains expressible.
2. Every remaining non-`L3` row (expected: none) satisfies the §1
   stop-loss triple (attributed / text-free / within budget).
3. **Footprint: every file's `footprint_ratio` ≤ 1.5** (§3), recorded in
   the warranty.
4. Any comparator change went through the §2 licensing (petition, partner
   approval, `LADDER_VERSION` bump, co-located soundness argument);
   `scripts/ratchet_diff.py` vs the M8 baseline: **zero downgrades** —
   including zero *rung* downgrades on rows that were already `L3`
   (a pre-existing `L3.0`/`L3.1` row must not drift to a weaker new rung).
5. Naming: deterministic (fixed point over `corpus/final/` holds), ledger
   byte-identical across naming commits, coverage figure reported,
   spot-check pins green.
6. Migration guide delivered with the §4.2 item-5 validation actually run
   and its per-tool verdicts recorded; text-unit inventory committed as a
   fixed point, with the `vms`-ID reconciliation (16749 static sites per
   Zndnovel's census — re-derive) accounted for.
7. Suite green; new suite cost attributed (footprint gate and inventory
   fixed point are formal-verification-adjacent instruments under the
   ~120 s earmark; naming spot-checks are ordinary tests and must be cheap).
8. `ratchet_job.sh` exit 0 with both corpus vars at the M8 baseline.

## 6. Non-goals

- No new dynamic instruments (L2 expansion, Class-1/Class-2 runs — M8
  agenda 5 carries).
- No `T≈` schema split (agenda 2): expected moot once ours-side `T-` count
  is 0; revisit only if a consumer appears.
- No mechanism-F work (agenda 4): the degenerate merge is accepted; pred
  re-certifiability buys nothing this milestone.
- No edits to the Zndnovel repository from this project — the guide and
  the read-only validation runs are the entire footprint there.
- No PSP-hardware heap measurement (the 1.5× line is policy; §3 records
  the supersession rule).
- M1's Linux x86_64 verification stays open (agenda 5 / M7 agenda 7) —
  called out so its omission is a decision, not an oversight.

## 7. Prerequisites (before M8 task 1)

1. Complete the M7 finishing flow: final whole-branch review (per the M7
   mode ruling: one dispatched subagent) if not already run, then the
   partner's integration decision for `phase7-m7-semantic-warranty-glm53`.
2. Move `ratchet_job.sh`'s default baseline to the M7 merge tip (the
   task-1 precedent from M6 and M7; M8 agenda 6 housekeeping).

## 8. Milestone shape (sketch; writing-plans details it)

1. Baseline re-measure + footprint instrument + its gate (the instrument
   lands before the campaign so every repair's footprint effect is
   observable).
2–4. Campaign clusters in rising difficulty: `structure:` recognizer gap;
   `reconstruct:` staging family; `mismatch` clusters with emitter-side
   byte-exact attempts.
5. Rung petitions for whatever survives with a parser-direction argument
   (each its own partner gate; possibly zero tasks if byte-exact wins).
6. Naming pass + its determinism/invariance gates.
7. Text-unit inventory + reconciliation.
8. Migration guide + read-only validation runs.
9. Documents of record, exit gates, close.

## 9. Risks

- **Constant-pool order may be genuinely unreachable** from any source for
  some rows (the s3/s4 parser-direction precedent) → the L3.2 petition
  path exists; the risk is schedule, not correctness.
- **The 1.5× ceiling is policy, not hardware truth.** Stated in §3; the
  supersession rule bounds the damage in both directions.
- **Naming quality is judgment.** Bounded by mechanical-rules-only scope,
  determinism, and partner review of sample listings; anything requiring
  taste beyond rule-derivable evidence stays synthetic rather than guessed
  (wrong names are worse than ugly ones for translators).
- **Zndnovel drift**: the guide is pinned to Zndnovel commit `380a577`;
  if that tree moves before delivery, the validation runs re-execute
  against its then-HEAD and the guide says which commit it describes.
- **The inventory doubles game text into a second committed artifact**
  (~1–2 MB estimated — measure, don't trust this number). Same discipline
  as `corpus/final/`; if size becomes a concern the inventory can ship
  gzipped with the fixed point defined over the uncompressed bytes.

## 10. Relation to the M8 agenda (`docs/runbooks/m3-backlog.md`)

- Agenda 1 (52-line dialogue residual) — dissolved by track 1 (the pinned
  census test flips to asserting zero).
- Agenda 2 (`T-` duality) — expected moot (§6).
- Agenda 3 (L3.3 hint rung) — subsumed by §2's licensing path.
- Agenda 4 (mechanism F) — explicitly not done (§6).
- Agenda 5 (carried items incl. Linux M1) — untouched, named in §6.
- Agenda 6 (housekeeping) — §7 prerequisite 2.

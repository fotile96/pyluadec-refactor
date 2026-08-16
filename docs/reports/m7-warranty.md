# M7 warranty report

This file collects M7's warranty-chain evidence as each task closes. §1 is
task 2's deliverable (the pred re-certification rate, spec §3's go/no-go
number); later tasks append below it. **Evidence, not a gate** -- the
assertions live in the test suite; this file exists so the numbers are
inspectable without re-running anything.

## §1. The pred re-certification rate (task 2, measured 2026-08-15 at c853e0e+)

`scripts/pred_recert_rate.py` over all 229 pred files (14.21 s, one process,
linear in files):

```
recert: T3 712/1944, T2 0/1944, T- 1232/1944  (229 files, 14.21s)
recert rate (T3+T2)/total: 0.3663        GO/NO-GO: BELOW 0.70
```

**The go/no-go line fired.** Per spec §3 this is reported to the human
partner before any Task 11 (merge) work proceeds; the disposition lives in
the task/ledger record and the milestone decision log at close.

### Strip convention (spec §3 rev 3, fixed in `pyluadec.predrecert`)

The recert reference is always `oracle.compile_source(pred_text, strip=True)`.
Pred text compiled unstripped carries `lineinfo`/`locvars` our re-emission
cannot reproduce; stripping matches the original corpus's shape (all 1944
original protos are stripped) and confines certification to semantic fields
-- the claim Factor T actually makes. `tests/test_predrecert.py` asserts
`carries_debug(load_bytes(reference)) is False`.

### T2 = 0 and the T- population's shape: a diagnosed mechanism, not noise

Corpus-wide correlation (every pred proto, Δ = pred maxstacksize − original
maxstacksize, against its T grade):

| grade | Δ=0 | Δ=−1 | Δ≥1 | total |
|---|---:|---:|---:|---:|
| T3 | 512 | 130 | 70 | 712 |
| T2 | 0 | 0 | 0 | 0 |
| T- | 70 | 1 | **1161** | 1232 |

**All 229 pred files carry at least one proto with Δ>0.** The mechanism
(walked at instruction level on `snr_crd_0.lua`, uniform across the crd
family): the predecessor's decompiler emits boilerplate locals in **every**
function scope -- `local card_0_main, v1, v2` in main, `local card_0_main,
v1` in each child -- so the pred recompilation's every proto carries 1–2
**dead locals the original never had**: maxstacksize +1/+2 (crd_0 measured:
main 2→4, main_0 5→7, main_1 5→7, with ncode/nconst/nparams/nups identical).
Our re-emission does not re-materialize dead locals, so the recompiled
candidate's maxstacksize is 2 under the pred reference (`mismatch:
maxstacksize` at the root), the root fails, `certify_hybrid` cannot save it
(hybrid requires the root's own fields to match), and the chunk falls to
whole-file fallback -- which is why **T2 is exactly 0**: no pred file ever
reached the hybrid middle rung.

The 70 Δ=0 T- occurrences are the non-boilerplate residue (the original
corpus's own 40-row families plus additional pred-shape refusals), and
70 Δ≥1 protos certify despite the boilerplate -- our emitter sometimes
re-materializes the slots (Δ=2 T3: 22, Δ=4: 14; the boundary is a
classification detail the repair campaign will formalize).

### Disposition (reported to the human partner 2026-08-15)

The rate as measured is real for the current pipeline -- the instrument
compares against the pred bytecode faithfully; the text genuinely does not
round-trip it. The dominant blocker is a **newly diagnosed mechanism** (pred
boilerplate dead locals), corpus-wide, larger by occurrence count than
mechanisms C/D/E combined. The decision (continue repair campaign including
this mechanism and re-measure; ship verbatim residue; or re-scope) is the
partner's; recorded here and in the milestone decision log.

### Addendum (2026-08-16, Task 11 round 1): the T-grade mapping's order was
### wrong, and §1's rate with it

Task 2's `t_grade` ladder checked `L3` first, so a proto that individually
certified but **shipped fallback text** (whole-file fallback or a
hybrid-replaced subtree) graded `T3`. Spec §2 grades "how faithful is THE
SHIPPED TEXT" and defines `T-` as "shipped verbatim without certification
(fallback text, ...)" — the state machine was never the text any
`certify_l3` run verified. Flipped to shipped-first in
`src/pyluadec/predrecert.py` (dated amendment in its docstring; the order
pin test rewritten). Re-measured rate under the corrected mapping:

```
recert: T3 10/1944, T2 3/1944, T- 1931/1944  (229 files, 15.90s)
recert rate (T3+T2)/total: 0.0067
```

The collapse from 0.3683 is the honest number: the task 2 §1 table's 713
`T3` included **703 phantom grades** — descendants that certify individually
inside chunks that fall to whole-file fallback, whose structured text is
never emitted. The mechanism diagnosis (boilerplate dead locals → root
`mismatch: maxstacksize` → whole-file fallback) is unchanged and explains
the corrected shape too: only 13 occurrences anywhere ship structured pred
text, and only `config.lua`'s pred side (1 occurrence) is all-`T3`.

File-level selection is invariant to the order (measured both ways: 222
ours-`T3` minima + 7 ours-`T-` minima), so nothing in §3's outcomes depends
on this amendment — it exists because the warranty's per-occurrence records
must not overclaim shipped text (49 our-side occurrences and the pred-side
analog would have).

**Go/no-go disposition (2026-08-16).** With the corrected rate at 0.0067 —
far below the 0.70 policy line — the human partner instructed Task 11 to
proceed (this session). The consequence is arithmetic, not discretionary:
a pred side needs `t_min` above `T-` to beat anything (ours' `E = id` wins
every tie), and only `config.lua`'s pred side qualifies — where ours ties
`T3` and wins on `E`. All 229 files select ours (§3). The `*-verbatim`
residue is **empty, structurally**: an ungradable pred side is ineligible,
so a pred side that wins always has a `RecertOutcome.source` to ship
(`*-recert`), and a `T-` pred side can never win.

## §2. Panel corpus run + adjudication (task 4, 2026-08-15)

`scripts/invariant_panel.py --all` over all 229 files / 1944 pairs
(**5.94–6.13 s**, three runs):

```
panel: 1411/1944 pass, 533 divergent
  fingerprint 533 · constant_values 30 · loss:test_ops 24 · loss:global_reads 10
  loss:call_targets 7 · loss:call_shapes 7 · loss:n_back_edges 6 · loss:n_natural_loops 2
panel: fixed point holds; 217 pin(s) live, 316 unpinned row(s) recorded
```

`corpus/observation/panel.json` (98 KB) committed: per proto, `pass` |
`{"pinned": <note>}` | `{"unpinned": {family: evidence}}`.

### The population is 40x the plan's hypothesis, and that is the finding

The plan's Step-2 hypothesis was "the 12 `equivalent-transform` files may
flag". Measured: **533 divergent rows across 129 files** -- consistent with,
not contradicting, the M6 census (0/229 files recompile field-exact; 1433
paths carry substantive mismatches; the panel is simply the first instrument
to ask per-proto two-sided). The bulk (488 rows) is the
`code_len + opcode_counts` fingerprint family: the pred text's different
phrasing of the same program. All six M6 defect protos flag as expected
(`snr_music:main_3` on 8 fields, `mainmenu:main_7`, `graphic:main_4`,
`memory:main_4`, `common:main_76_2`, `common:main_75`), plus `common:main_83`
(the font-path `intentional-edit`).

### Adjudication rules (controller ruling, recorded)

Pins are inherited from M6 verdicts under three rules -- **the 6+1 defect
protos pin citing the M6 report §3.4/§3.5 and the `pred_repairs`
disposition; rows with a per-proto `LOSS_PINS` verdict pin citing it; rows
in per-file `equivalent-transform` files pin citing the file verdict, and
only when their family set is fingerprint/loss** (a `constant_values` flag
is evidence no M6 verdict saw -- 6 such rows stay unpinned on that ground).
Result: **217 pinned / 316 unpinned**. Unpinned rows are part of the record,
not failures: they disqualify the pred side per-file at selection time and
never ship (spec §6/§8.2). The load-bearing adjudication debt -- divergent
rows in files whose pred side could actually win (the 4 fallback + 8 hybrid
files): **321 rows, 168 unpinned** -- is re-scoped to Task 11, where the
post-repair-campaign selection decides which files contest at all (the job's
own trigger: re-run before Task 11).

### A fabrication the fixed point caught

The first generation of the pin table cited the defect walkthroughs as
"M6 report 3.1–3.6" -- **subsection numbers that do not exist as
defect-per-section mappings** (§3.4 is *all five* defects at instruction
level; §3.5 is the `intentional-edit`). The second generation wrote plain
"§3"; the byte-comparison gate between the committed artifact and the
module's table caught the disagreement before anything shipped. Corrected to
the real sections (§3.4 defects, §3.5 intentional-edit); recorded here
because inventing a citation is this repo's named defect class, and the gate
that caught it is the one this task built.

### Gates and suite cost

- `tests/test_invariant_panel.py`: **14 tests, 6.13 s** -- the synthetic
  Task-3 unit tests plus the fixed point + pin currency (one shared 6 s
  scan), the byte-comparison neuter proof (a tampered artifact must fail
  it), the summary pin (1411/217/316, no corpus needed), and the
  defect-proto pin assertion. All 6.13 s attributable to the
  formal-verification earmark (the panel is M7's Factor-E instrument).
- The job (regeneration + adjudication) is out-of-suite with the four
  conditions in the CLI docstring.

## §3. Selection outcomes (task 11, 2026-08-16)

`scripts/warranty_build.py --all` (job; trigger in its docstring — any
ledger/panel/recert movement and at close): **22.84 s**, one `decompile_file`
+ one `recert_bytes` per file, linear in files. Committed artifacts:
`corpus/warranty.jsonl` (188 KB, 229 rows) + `corpus/final/` (229 files,
3.7 MB). Both regenerate byte-identically
(`tests/test_warranty.py::test_warranty_artifacts_are_a_reproducible_fixed_
point`, corpus-gated on both env vars, one shared ~17 s build per module —
the `panel_scan` precedent; a tamper-neuter proves the gate reads the
artifact).

### The selection table

**All 229 files select `ours`.** The distribution is not close:

| | ours side | pred side |
|---|---|---|
| file-level `t_min` | 222 × `T3`, 7 × `T-` | 1 × `T3` (`config.lua`), 228 × `T-` |
| occurrences | T3 1873 / T2 7 / T- 64 | ships nothing |
| shipped `e` | `id` × 1944 | (n/a) |

The seven files whose ours side is not fully structured (5 hybrid:
`snr_common`, `snr_graphic`, `snr_mainmenu`, `snr_memory`, `snr_story_main`;
2 whole-file fallback: `snr_music`, `snr_novel`) all contest and all lose on
Factor T before E is reached — their pred sides are `t_min = T-` (the
corrected mapping: no pred chunk outside `config.lua` ships structured text,
§1 addendum), and five are additionally unpinned-disqualified
(`snr_music` 3, `snr_novel` 3, `snr_common` 80, `snr_graphic` 3,
`snr_mainmenu` 5, `snr_memory` 3, `snr_story_main` 1 unpinned rows).
`config.lua`'s pred side is the only `T3` minimum and loses the tie to
ours' `E = id` (and carries 1 unpinned row regardless).

### The spec §6 worked consequences, checked against reality

- "217 fully-structured files stay ours" — reality: **222** (the repair
  campaign moved 5 more files to fully structured since the spec was
  written).
- "the six `pred_repairs` files favoured on their repaired protos **until
  our side closes the corresponding mechanisms**" — the campaign closed
  them: every repaired-proto file now ships ours, and the warranty records
  the pred side's `wm` marks anyway (`snr_music` `main_3`;
  `snr_common` `main_75`/`main_76_2`; `snr_mainmenu` `main_7`;
  `snr_graphic` `main_4`; `snr_memory` `main_4`).
- The `*-verbatim` residue: **empty, structurally** (§1 addendum) — named
  here with its refusal reason per the plan; there is no file whose
  selection is `pred-verbatim` or `pred_repaired-verbatim`, and the
  generator's dead branch for them is documented in its module docstring.

### The standing pin-table opcode check (spec §7 / agenda 6)

`tests/test_pin_opcodes.py` (corpus-gated, both env vars): every
`O<n> OPNAME` / `P<n> OPNAME` pair in `PRED_PINS`/`LOSS_PINS` — **62 pairs**
(26 PRED + 36 LOSS) — decodes to the named opcode at 1-based pc `n` in the
resolved proto of the respective corpus. Proto context resolves through the
LOSS pin key, the PRED evidence tuple's leading `main_X code=`, and
in-note `main_X:` markers. Three tamper neuters prove the net catches the
defect class it exists for: an off-by-one pc, a wrong opcode name, and a
side swap (O→P). The generator runs the same assertion before writing and
refuses on any violation (`PinOpcodeError`).

### Readability of the shipped corpus (spec §4 acceptance, measured)

Over `corpus/final/`: **17727 of 17727 non-ASCII string literals present as
raw UTF-8 (fraction 1.0000)**. The `doScriptScene` idiom ships as the
global-comparison shape (`if doScriptScene == "s6f-10" then`) with Japanese
arguments raw (`l0_0(doScriptScene, "オープニング")`, `snr_s1_10_s.lua`);
measured, the `doScriptScene` carriers are the fully-structured `snr_crd_*`/
`snr_s*` files and **none of the 7 files still shipping fallback text
references `doScriptScene` at all** — so the spec's "in whichever files
still ship any fallback text" spot-check instantiates, on this corpus, as
"wherever the sites are". Task 12 formalizes the ≥ 0.99 exit floor.

### Gates and suite cost

- Suite: **1168 passed in 76.76 s** (was 1150 / ~57 s; +18 tests). The
  +19.8 s is the warranty fixed-point build (~17 s, shared module fixture)
  plus the pin-opcode arms (~3 s) — all attributable to the
  formal-verification earmark (the warranty is M7's Factor-T/E instrument
  and its fixed point).
- `./scripts/ratchet_job.sh` (baseline `3669950`): **PASSED** — 18
  upgrades, 0 downgrades (all from tasks 6–10's committed repairs; task 11
  moved the ledger not at all — `git diff corpus/ledger.jsonl` empty).
- Panel + recert jobs re-run at task start per their triggers: panel fixed
  point holds (217 pins / 316 unpinned); recert rate 0.3683 under the old
  mapping, 0.0067 corrected (§1 addendum).

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
§1 addendum), and **all seven** are additionally unpinned-disqualified
(every one carries ≥ 1 unpinned row: `snr_common` 80, `snr_mainmenu` 5,
`snr_music`/`snr_novel`/`snr_graphic`/`snr_memory` 3 each, `snr_story_main`
1 — an earlier revision of this paragraph said "five" while listing seven;
corrected at close).
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

### Readability of the shipped corpus (spec §4 acceptance, both halves measured)

The **encoding half is complete**: over `corpus/final/`, **17727 of 17727
non-ASCII string literals present as raw UTF-8 (fraction 1.0000)** — task 5's
deliverable, reproduced at close. The structured text carries its Japanese in
readable call form (`l0_0(doScriptScene, "オープニング")`,
`snr_s1_10_s.lua`; `plotTitle[...]`/`vms(...)` in `snr_common`).

The **call-context half is NOT met, and is pinned rather than exempted**. The
first draft of this section claimed "none of the 7 files still shipping
fallback text references `doScriptScene` at all" — a sentence generalized
from a **truncated grep listing** (the controller review of 2026-08-16
caught it; this repo's named defect class). The measured facts:

- `doScriptScene` has **zero direct call sites** corpus-wide in the
  `doScriptScene("...")` form (the idiom ships as global assignment /
  comparison); as a raw substring the still-fallback files carry **8
  references** — `snr_mainmenu` 2, `snr_memory` 3, `snr_story_main` 3 — of
  which 5 are themselves box-shaped (`doScriptScene = __pld_R[4]`);
  `snr_memory`'s 3 sit in structured text (a table key and an indexed
  assignment).
- The game text inside fallback-shipped subtrees travels as
  **`__pld_R[n] = "<Japanese>"` — 52 lines corpus-wide** (`snr_common` 49,
  `snr_story_main` 2, `snr_novel` 1; the review counted 49, all in
  `snr_common` — the closing re-census found the three lines it missed).
  That is dialogue text without call context: a translator cannot tell who
  says it or which branch it lives in. Same file, same milestone:
  `snr_common`'s structured part carries 346 further non-ASCII lines in
  readable form.

**Disposition (task 12)**: the 52 lines are a recorded residual —
`tests/test_m7_exit.py::test_m7_exit_box_model_game_text_is_a_pinned_
residual` pins the exact census so it cannot grow silently, and the FIX
(promoting box-model string constants into readable call shape) is routed
to the **M8 agenda** per the controller review: it is M8-scale work and was
deliberately not started in the closing round. The exit floor test asserts
the encoding half (≥ 0.99; measured 1.0000) and this pin asserts the
residual — spec §4's two clauses are now two separate, honest assertions
instead of one clause measured and one exempted by a false sentence.

### Gates and suite cost (re-measured at close; the task 11 split corrected)

- Suite: task 11 measured **1168 passed in 76.76 s**; the controller review
  independently measured **67.49 s** on the same tree, and the closing runs
  below add a third sample — cross-host/session jitter, all inside the
  ~120 s earmark.
- **The task 11 attribution split was wrong and is corrected here**: it
  said "+19.8 s ≈ warranty build ~17 s + pin arms ~3 s". Measured
  (pytest `--durations`, 2026-08-16): the pin-opcode module is
  **0.08 s total / 0.04 s slowest call** — two orders below the claimed
  ~3 s — and the warranty fixed-point fixture setup is **22.47 s
  standalone** (20.81 s in the review's session). Essentially the entire
  suite delta is the warranty fixed-point build; the total (+19.8 s in
  suite) was right, the split was written without being measured.
  Attributable in full to the formal-verification earmark (the warranty is
  M7's Factor-T/E instrument and its fixed point).
- `./scripts/ratchet_job.sh` (baseline `3669950`): **PASSED** — 18
  upgrades, 0 downgrades (all from tasks 6–10's committed repairs; task 11
  moved the ledger not at all — `git diff corpus/ledger.jsonl` empty).
- Panel + recert jobs re-run at task start per their triggers: panel fixed
  point holds (217 pins / 316 unpinned); recert rate 0.3683 under the old
  mapping, 0.0067 corrected (§1 addendum).

### The task 4 adjudication debt, settled

Task 4 re-scoped the load-bearing adjudication question — divergent rows in
files whose pred side could then contest (the 4 fallback + 8 hybrid files of
the task 4 tree: 321 rows, 168 unpinned) — to "Task 11, where selection
decides which files contest at all". Settled by measurement: after the
repair campaign the contestable set is 7 files, every one of them loses on
Factor T before eligibility could matter, and **zero rows from the debt
population ship** (nothing pred-side ships at all). The debt is closed not
by adjudicating it away but by the selection outcome making it inert; had
any pred side won a file, its unpinned rows would have disqualified it —
the mechanism was never bypassed.

### One symbol, two guarantees (recorded limitation)

`T-` in `warranty.jsonl` denotes different things per side. OUR `T-` (64
occurrences, all `{"t": "T-", "e": "id"}`) is the M2 floor: the fallback
state machine — semantically exact by construction (38/38 opcode
differential tests), compileable, L1.5/L1.75-probe-covered. PRED `T-` means
no positive verification at all. A reader cannot tell them apart in the
artifact and will read ours as "no evidence", understating the strongest
constructive guarantee this project ships; for a translation downstream the
difference is "64 places too unreliable to use" versus "64 ugly-but-reliable
places". This is a spec §2 consequence faithfully implemented, documented
in the generator's module docstring; splitting the symbol is an M8 schema
candidate (it would churn the committed artifact without moving any
selection), not a closing-round change.

### Two structural facts about the selection rule (pinned as tests)

- **Factor E never decides a selection.** Exhaustively over all 36 grade
  combinations with ours at `e = id`: pred wins in exactly 12, every one a
  strict Factor-T advantage; no T tie is ever decided by E (`id` is the top
  of the E order). Factor E's entire decisive role is the `unpinned > 0`
  eligibility veto plus the record itself. The spec §6 wording ("then E")
  implies a tie-break that structurally cannot fire for ours; pinned in
  `tests/test_m7_exit.py::test_m7_exit_factor_e_never_decides_a_selection`.
- **The merge is degenerate, and the reason should be quoted precisely.**
  `corpus/final/` is byte-identical to our own product (229/229 selections
  ours, verified per-file against `decompile_file().source`). Pred did not
  lose on semantics — it lost on **re-certifiability**: the predecessor's
  boilerplate dead locals (mechanism F, §1) fail the root `maxstacksize`
  comparison in 228 of 229 files, which is a diagnosed, plausibly-benign
  cause, not a quality verdict on pred's text. The honest headline is "our
  criterion measures re-certifiability through our own pipeline; pred fails
  it 99.3 % for one diagnosed reason" — the conclusion still stands on
  independent grounds (our fallback is semantically exact; pred carries the
  six confirmed M6 defects), but "the distribution is not close" (an
  earlier sentence here) read like a quality judgment and is withdrawn.

### Independent verification at close (controller review 2026-08-16 + this round)

The controller review re-ran the suite, both fixed points, the ratchet, and
the tamper neuters, and verified the **Wm-over-panel inheritance premise**:
the five repaired files differ from upstream pred **only in the six Wm
protos** on every semantic field (code/constants/maxstacksize/numparams/
is_vararg/nups). Re-derived in this round with one addition: `snr_common`
has **42 further protos whose `linedefined`/`lastlinedefined` shifted**
(hand edits move later functions' line spans) — line fields no panel family
compares, so the inherited verdicts stay sound; recorded because it is the
boundary of that verification, not because it changes anything.

## §4. Milestone close (task 12, 2026-08-16)

Every M7 number re-measured at the closing tree (this section supersedes
task-time figures where they moved; nothing else in this file was edited
except where a correction is dated in place).

**The deliverables.** `corpus/final/` (229 files, 3.7 MB) and
`corpus/warranty.jsonl` (188 KB, 229 rows, 1944 graded occurrences),
generated whole by `scripts/warranty_build.py`, byte-identical on
regeneration, suite-gated on both corpus env vars. Selection: **229/229
ours** (§3). Exit gate `tests/test_m7_exit.py`: 6 tests, **0.14 s**,
env-free (reads committed artifacts) — artifacts complete / no unpinned
shipped / non-`L3` strictly < 40 (**measured 22**) / raw-UTF-8 floor
(**measured 1.0000**) / the 52-line box-model residual pinned / Factor-E
never-decides pinned.

**The repair campaign's ledger** (vs the M6 merge baseline `3669950`):
`L3` **1456/1478 unique (98.5%) / 1922/1944 occurrences (97.9%)** (M6 close
97.3% / 97.9%); products **222 fully structured / 5 hybrid / 2 whole-file
fallback** (M6 close 217/8/4); **18 upgrades, 0 downgrades** on the
ratchet; 117 occurrences moved fallback → structured. The 22-row residual:
15 own + 7 inherited, every row attributed in the runbook's "What is left"
census (8 mechanism clusters; K1's 5 rows are the L3.3-rung M8 candidate).

**The warranty chain's verified links**, each re-run this milestone: pred
re-certification (rate **0.0067** corrected, mechanism F diagnosed at
instruction level); the invariant panel (1411 pass / 217 pinned / 316
unpinned over 1944 pairs, fixed point green); the six M6 repairs carried
as `wm` with the repaired-vs-upstream difference verified to be exactly
the Wm protos on semantic fields (42 line-only shifts in `snr_common`,
invisible to every panel family); the standing pin-table opcode gate (62
pairs, three tamper neuters); readability (encoding half complete at
1.0000; call-context half pinned as the 52-line residual, routed to M8).

**Suite**: **1174 passed, 73.60 / 74.71 / 75.73 s** (×3, closing tree,
macOS arm64; the controller review measured 67.49 s for the 1168-test
tree in its session — cross-host jitter, all inside the ~120 s earmark).
Attribution: the task 11 +19.8 s is the warranty fixed-point build
(22.47 s standalone; pin-opcode arms 0.08 s — corrected split in §3);
task 12 added 6 env-free tests at 0.14 s.

**`ratchet_job.sh` at close: PASSED** (18 upgrades, 0 downgrades, 24/24
differential cases; third gate re-run for this section, output below in
the task log).

**What M7 leaves open** (seeded in `docs/runbooks/m3-backlog.md`'s M8
agenda): the 52-line box-model dialogue residual and its fix; the `T-`
duality schema candidate; mechanism F if pred-side re-certifiability ever
matters; the L3.3 NEWTABLE-hint-masking rung; plus the M7 agenda items
carried unmodified (corpus-wide L2, `next`/`pairs`, probe wire-format,
`StructureError` attribution, Linux x86_64 verification).

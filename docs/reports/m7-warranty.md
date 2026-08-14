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

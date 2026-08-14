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

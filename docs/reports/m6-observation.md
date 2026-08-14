# M6 task 4 — meta-observation of the corpus's hard protos

Everything here was measured on 2026-08-13 on macOS 15.2 / arm64 (Mac mini,
Darwin 24.2.0), against `PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/
script_to_decompile` (229 files, 1944 protos) and, where the predecessor is
named, `PYLUADEC_PRED_CORPUS_DIR=/Users/fotile96/Zndnovel/lua_scripts`.

**Round 1 rewrote §§1, 3.3, 3.4, 3.6, 5, 6.2, 6.4, 7, 8 and 10 and added §9.**
Every figure below was re-derived after the round-1 code changes; §10 lists what
moved and why. Where an earlier revision of this file said something else, §10
says so rather than the sentence quietly changing.

Artifacts: `scripts/observation_classes.py` (the generator, a JOB),
`corpus/observation/classes.json` (committed generated data, 162 candidate
records), `tests/test_observation_classes.py` (21 guards). The generator's
module docstring is the reference for the schema and the vocabularies; this
report is the measurement record and the argument.

**Which statements rest on the predecessor's text.** Marked `[P]` in place.
Each is a corroboration of a bytecode measurement stated alongside it; none is
load-bearing on its own, with one exception that is flagged where it appears
(§9.2's consequence sentence, which is attributed to the review).

---

## 1. Headline

| | |
|---|---|
| candidates | **162** over **137** files |
| leaf refusal sites | **36** of the 48 non-`L3` ledger rows |
| event-cap dominant protos | **132** (one per `CAP` file) |
| in both populations | **6** |
| class census | **`choice-branch` 113 / `ui-keyloop` 11 / `neither` 38** |
| candidates whose loop polls the key every iteration | **127 of 162 (78%)** — 113/113 `choice-branch`, 11/11 `ui-keyloop`, 3/38 `neither` |
| drivable within a 4096 budget | `choice-branch` **110/113**, `ui-keyloop` 11/11, `neither` 38/38 |
| corpus-wide input space ≤ 4096 | **1940 / 1944 protos (99.8%)** |
| (a) poll-loop cuts that correspond | **18 of 19**; **1 structural failure** (`snr_music.lua:main_3`) |

Both pre-measurements land on the useful side and neither is clean. (a) holds
on 18 of 19, and the one failure turns out to be a **shipped semantic defect in
the predecessor** (§9.1). (b) says the milestone does not have to degrade to
sampling on account of input-space size — but the product model that produces
the number is measurably the wrong model for the largest protos, so
"exhaustive" must be said about a stated channel set, not about behaviour.

**And one thing the framing got wrong.** The owner's Class 2 is distinguished by
non-termination under a finite key sequence. Measured: **127 of 162 candidates
(78%), including 113 of 113 Class-1 protos, poll the key on every iteration of
a loop** — Class 1 through `oCard.selectCardObj` / `comDlg*`, Class 2 through
`pressButton`. The termination problem is not confined to the 11 `ui-keyloop`
protos. §3.6.

---

## 2. Candidate selection, and the leaf-refusal rule

### 2.1 Leaf refusal sites — 36, not the ~20 the brief carried

A non-`L3` proto's `refusal_reason` propagates upward: `print_chunk` inlines
the whole subtree at each `CLOSURE`, so an ancestor reports its descendant's
message verbatim. "Leaf" therefore has to mean *the refusal originates in this
proto's own body*, and the generator decides it with three rules, one per
`refusal_reason` kind:

| kind | rule | rows | own |
|---|---|---|---|
| `structure:` | `build_sir` on this proto alone raises | 21 | 13 |
| `reconstruct:` | no non-`L3` descendant carries a byte-identical reason | 5 | 3 |
| `mismatch:` | the reason has no ` at root/...` suffix | 22 | 20 |
| | | **48** | **36** |

**Cross-checked against a different question entirely**, and the check is in
the suite (`test_leaf_refusal_rule_agrees_with_an_independent_stubbing_
experiment`): replace every subproto of a non-`L3` proto with a trivial
`function(...) end` of the same arity, re-print the proto, and see whether a
refusal survives. On all 26 rows whose reason is a *print* refusal
(`structure:` / `reconstruct:`), surviving the stub is **exactly**
`refusal_origin == "own"`, and the surviving message is **byte-identical** to
the ledger's. On the 22 `mismatch:` rows the stubbed print always succeeds —
a comparison rejection is not a print refusal — so there the rule falls back
to `Mismatch.path`, and that is asserted too.

**The brief's "~20 leaf refusal sites" does not reproduce under any reading I
could construct.** The nearest figures are **20** (the `mismatch:` rows whose
first differing field is their own) and **32** (non-`L3` protos with no
non-`L3` descendant — the naive prefix definition, which mis-files
`snr_graphic.lua:main`, whose own `build_sir` refuses at pc 340 while its
non-`L3` descendant `main_4` refuses at pc 120). The measured answer under the
definition above is **36**.

### 2.2 Event-cap dominant protos — 132

The L1.75 behaviour probe run over all 229 originals reproduces its pinned
headline exactly this session: **132 `CAP` / 97 `OK`, 398196 events**. The
probe emits `I|<name>` before each global-function invocation, so events
attribute to an invocation window directly off the trace; the dominant global
is `main` in **131** of the 132 files and `autoSystemSave` in one. Resolving
the name to a `proto_path` through the chunk's own `CLOSURE`/`SETGLOBAL` pairs
succeeded for **132 of 132**.

Also re-derived: the dominant *callee* split over the 132 is **101 `vms` / 26
`wait` / 5 `pressButton`**, exactly the M5 figure.

---

## 3. The classes, and what is underneath them

### 3.1 The rule

- **`ui-keyloop`** — the proto's own body has a natural loop whose body
  contains a direct `pressButton` call.
- **`choice-branch`** — it does not, but it calls an option-reading function
  from `OPTION_CALLEES`.
- **`neither`** — neither, *in its own body* (§3.4).

`test_class_is_exactly_its_own_evidence` recomputes the class from the two
published predicates on every record, so a hand edit or a rule/output drift
fails the suite.

**A loop is a HEADER, not a back edge**, and round 0 got that wrong. The
natural loop of a header is the union of the backward closures of *all* back
edges targeting it. Counting per back edge overstated `n_natural_loops` on
**14 of 162** records (`snr_mainmenu.lua:main_7`: 32 back edges over **16**
headers) and produced one false structural claim, corrected in §5.4. Both
counts are now published under their own names.

The rule's Class-1 half was checked against a reading of `snr_crd_10.lua`'s
`main_2`: guard `gameSave.myCard[9].hold == -1` at pcs 7–11, then
`oCard.selectCardObj` at pc 39 inside the single natural loop (header block
35, back edge from block 82), result compared at pc 40 (`9`, break) and pc 43
(`-1`, cancel). `[P]` The predecessor's `snr_crd_10.lua` shows the same shape
as `while v2 < 1 do v5 = oCard.selectCardObj() ... end`.

### 3.2 `POLL_GLOBALS` is `pressButton` and nothing else — measured

Three globals looked like key polls. Two are not:

- **`keyWait` is defined by the corpus.** `snr_common.lua`'s chunk-level
  `CLOSURE`/`SETGLOBAL` pair resolves the global `keyWait` to **`main_81`**,
  and `main_81` is itself a `pressButton` poll loop (26 instructions, loop pcs
  3–25, polls at CALL 5 and 11, timeout via `DIV`/`LE` at pcs 16–17). So it is
  a Class-2 *proto*, not a primitive; calling it delegates a poll. `[P]` The
  predecessor's `snr_common.lua:4966` shows the same body, read first and then
  re-derived from the bytecode.
- **`functionButton` registers a handler** (`unsetConfigButton` /
  `setConfigButton` in `SystemConfig`), never returns a key state, and its
  result is never branched on. `[P]` same status.

Measured over all 229 files: **19 protos call `pressButton` directly**, and an
independent audit measured that **all 19 have that call inside a natural
loop**. Eleven are candidates; the other eight are not in the candidate set at
all — every one is `L3` in the ledger and none is a `CAP` file's dominant
global: `snr_common.lua` `main_27` (`comDlgYesNoSel`), `main_28`
(`comDlgStorylineSkip`), `main_55` (`comStorySceneEnd`), `main_76_7`
(`SystemConfig.confirm`), `main_77_24` (`ObjectCard.cardModeSelect`);
`snr_fragment_main.lua:main_3`; `snr_novel.lua:main_7` and `main_12`.

### 3.3 What the option channel bottoms out in — the finding, restated

**The option channel bottoms out in CORPUS-DEFINED code rather than in an
engine primitive.** Every entry in `OPTION_CALLEES` resolves, through the
corpus's own `CLOSURE`/`SETGLOBAL` and `CLOSURE`/`SETTABLE` pairs, to a proto
in `snr_common.lua`:

| callee | proto | loop headers | polls directly? |
|---|---|---|---|
| `comDlgSelectItem` | `main_29` | 6 | yes |
| `comDlgYesNoSel` | `main_27` | 1 | yes |
| `comDlgStorylineSkip` | `main_28` | 1 | yes |
| `comSelectMap` | `main_71` | 6 | yes |
| `comDlgYesNo` | `main_26` | **0** | no — 8 instructions, `TAILCALL` to `comDlgYesNoSel` |
| `oCard.selectCardObj` | `main_77_17` | **0** | no — 48 instructions, `self.cardModeSelect` at pcs 22–28 |
| `oCard.selectCardNotCancelObj` | `main_77_18` | **0** | no — same shape |

**Round 0 said all seven "are Class-2 poll loops living in `snr_common.lua`",
and that is false for three of the seven** — including the two `oCard`
selectors, which are the callees for **105 of the 113** Class-1 candidates.
They reach a poll one hop further, at `main_77_24` (`cardModeSelect`) and
`main_27`.

The structural point survives, and it is the one Tasks 7 and 8 need: the class
boundary falls on the corpus's own module boundary, so a Class-1 proto can
treat an option call as an uninterpreted oracle over a small value domain
precisely because what is behind it is somebody else's problem *in the same
corpus*.

The same construction identifies the peripheral-UI screens the owner named:
`SystemOption.OptionMain` = `main_74_13` and `SystemConfig.ConfigMain` =
`main_76_2` — **these two are the `DEBUG_KEY_SEQUENCE_HARNESS.md`
checkpoints**; `SystemConfig.Config` = `main_76_8` is their caller and is not
a checkpoint.

**The `OPTION_CALLEES` list is incomplete, by four protos that pass its own
test**: `comStorySceneEnd` = `main_55`, `SystemConfig.confirm` = `main_76_7`,
`SystemConfig.ConfigMain` = `main_76_2`, `ObjectCard.cardModeSelect` =
`main_77_24`. Only the first is a global name a list edit could add, and
measured: **no candidate of the 162 calls it**, so adding it would change
nothing. The other three are reached as `self.<method>()` and need the call
graph, not the list. Recorded rather than patched.

### 3.4 `neither` does not mean "no interaction channel" — 9 of 38

An independent audit of all 38 `neither` candidates confirmed that **none of
them calls `pressButton` or any option global in its own body**, so the rule is
applied correctly on all 38. Under the *gloss* round 0 attached to it, **9 are
wrong**. Round 0 also said those nine "reach an interaction one call out";
**that is wrong too.** Measured hop distance to the nearest direct poller:

| | hops |
|---|---|
| `snr_common.lua:main_74_18`, `main_76_8` | **1** |
| `snr_e2_10_f.lua:main_35` | 2 |
| `snr_e1_10_s.lua:main_29`, `snr_e2_10_s.lua:main_13` | 4 |
| `snr_crd_102.lua:main_5`, `snr_s0_10_f.lua:main_7`, `snr_s7_10_f.lua:main_53`, `snr_s8_10_s.lua:main_5` | **not reached by this graph at all** |

And only **2 of the 9** actually read a value and branch on it —
`main_76_8` (`GETUPVAL R2,0; GETTABLE R2 R2 K"ConfigMain"; CALL` at pcs 18–20,
branched at 25/38/40/55) and `main_74_18`. The other seven merely call into
something that eventually polls.

**The mechanism, and round 1 closed half of it.** Round 0's `_call_graph` built
edges only for callees with **global-rooted** provenance, so `self.method()`
was invisible and `protos_reaching_poll` read **331**. Seeding a sentinel on
`GETUPVAL` and resolving the method key in the proto's own ancestor chain
raises it to **443**, and it is what makes `oCard.selectCardObj` report
`reaches_poll == True` at last — round 0 published `False` for the callee
behind 105 of 113 Class-1 candidates. What is **still** invisible is a call
through an upvalue-held *local closure* (`GETUPVAL R0; CALL R0`), which needs
the parent's `CLOSURE` binding pseudo-instructions; that is exactly the four
rows above that this graph does not reach. **443 remains a floor.**

The nine carry the audit's verdict in their `observed` half with
`class_agrees: false`. The mechanical class is left as the rule computes it: a
class that quietly disagreed with its own published evidence would be worse
than one that is narrow and says where.

### 3.5 Census by population

| | `choice-branch` | `ui-keyloop` | `neither` |
|---|---|---|---|
| leaf refusal sites (36) | 5 | 10 | 21 |
| CAP dominants (132) | 111 | 4 | 17 |
| union (162) | **113** | **11** | **38** |

The `choice-branch` population is dominated by one shape: **103 of 113** are a
`snr_crd_*` file's `main`, calling `oCard.selectCardObj`.

### 3.6 The classes overlap on the difficulty that is supposed to separate them

The owner's framing treats non-termination under a finite key sequence as
**Class 2's** distinguishing difficulty. Measured, most of Class 1 shares it:

> **127 of 162 candidates (78%) have a natural loop that polls the key on every
> iteration**, directly or through a callee that reaches a poll —
> **113 of 113 `choice-branch`**, 11 of 11 `ui-keyloop`, 3 of 38 `neither`.
> Corpus-wide the same predicate holds for **122 protos**. Published per record
> as `loop_polls_per_iteration` with the in-loop callees that justify it, and
> per class in the summary, so it is checkable rather than asserted.

A story fragment re-polls its option channel per iteration exactly as a UI
screen re-polls the key, through `oCard.selectCardObj` / `comDlg*` instead of
`pressButton`. **What separates the classes is the shape of the termination
argument, not whether one is needed**: a card choice leaves its loop when the
returned value matches an expected id (a value in the measured domain), while
a UI screen's exit can depend on accumulated state — or, in the worst measured
case, on nothing at all (§4, `snr_mainmenu.lua:main_7`).

Task 8's design note must therefore know its termination problem is not
confined to 11 protos, and Task 7 must know its Class-1 targets are loops too.
Since the number is a floor of the call graph (§3.4), it can only go up.

---

## 4. Per-proto observation

64 of the 162 records carry an individually reviewed `observed` block: **all
11 `ui-keyloop`**, **all 38 `neither`**, and **15 `choice-branch`** (a
systematic sample of 12 — the sorted list at indices 0, 10, …, 110 — plus the
three whose input space exceeds the budget). The other 98 `choice-branch`
records are the `snr_crd_*` family, whose evidence signature is identical
across the sample. They are **not** individually reviewed and carry no
`observed` block, so `n_observed_records` reports 64 rather than 162.

The per-proto justifications live in the records themselves:
`corpus/observation/classes.json`, field `observed.note`, keyed by
`(file, proto_path)`. Every note names opcodes, pcs, registers and ASCII
identifiers only. Highlights that bear on Tasks 7 and 8:

- **`snr_mainmenu.lua:main_7`** — 16 loop headers over 32 back edges, four of
  them poll loops (headers 22 / 562 / 1113 / 1638; latches 553 / 1098 / 1633 /
  2178), and **measured: none of the four has a CFG exit edge at all**. They
  are left only through engine calls that do not return — 23 `quit()` sites,
  each preceded by `run(cGetFileName("script", ...))`. This is the strongest
  form of the owner's Class-2 worry in the corpus: not "a finite key sequence
  may not terminate the loop" but "no key sequence terminates the loop".
- **`snr_music.lua:main_3`** — exits only when a `TFORLOOP` scan over
  `selectFlag` (pcs 319–329) finds nothing, i.e. termination depends on
  accumulated table state, not on the key alone.
- **`snr_common.lua:main_81`** (`keyWait`) — mechanically `ui-keyloop`, but a
  26-instruction input helper with no screen state. The label is right and the
  phrase "peripheral UI" is not.

---

## 5. Pre-measurement (a) — loop-body boundary correspondence

### 5.1 What was cut, and the criterion stated before looking

For each proto that polls, on **both** sides — the original bytecode and the
predecessor source recompiled with the in-repo `luac_sz4`
(`predcorpus.load_pred_proto(..., strip=True)`, matching `certify_l3`'s strip
precedent) — I cut the natural loop (by **header**, union of all its back
edges' bodies) whose body contains a `pressButton` call, and recorded how many
such loops there are, the header and latches, the body's block count, and the
sequence of resolvable callee names inside the body in pc order.

The cut points **correspond** iff both sides yield the same number of poll
loops and the same body call-name sequence. pcs are not expected to match:
Task 2 measured that the predecessor's output is byte-faithful nowhere.

Run on **all 19 protos that call `pressButton`**, not the 2–3 the brief asked
for.

### 5.2 Result: 18 of 19 correspond, 1 structural failure

| proto | o hdr/be | p hdr/be | o poll | p poll | o body | p body | o calls | p calls | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `snr_common.lua:main_27` | 1/1 | 1/1 | 1 | 1 | 55 | 53 | 12 | 12 | match |
| `snr_common.lua:main_28` | 1/1 | 1/1 | 1 | 1 | 57 | 55 | 13 | 13 | match |
| `snr_common.lua:main_29` | 6/8 | 6/8 | 1 | 1 | 79 | 79 | 18 | 18 | match |
| `snr_common.lua:main_55` | 1/1 | 1/1 | 1 | 1 | 52 | 50 | 13 | 13 | match |
| `snr_common.lua:main_71` | 6/8 | 6/8 | 1 | 1 | 38 | 36 | 10 | 10 | match |
| `snr_common.lua:main_74_13` | 1/1 | 1/1 | 1 | 1 | 266 | 252 | 24 | 24 | match |
| **`snr_common.lua:main_76_2`** | 1/1 | **1/4** | 1 | 1 | 62 | **78** | 13 | **21** | cut corresponds, body differs (§5.4) |
| `snr_common.lua:main_76_7` | 4/4 | 4/4 | 1 | 1 | 55 | 53 | 12 | 12 | match |
| `snr_common.lua:main_77_24` | 1/1 | 1/1 | 1 | 1 | 91 | 90 | 26 | 26 | match |
| `snr_common.lua:main_81` | 1/1 | 1/1 | 1 | 1 | 11 | 12 | 3 | 3 | match |
| `snr_fragment_main.lua:main_3` | 3/3 | 3/3 | 1 | 1 | 103 | 101 | 65 | 65 | match |
| **`snr_story_main.lua:main_3`** | 3/3 | 3/3 | 1 | 1 | 92 | 91 | 50 | **51** | cut corresponds, body differs (§5.3) |
| `snr_novel.lua:main_7` | 1/1 | 1/1 | 1 | 1 | 32 | 33 | 6 | 6 | match |
| `snr_novel.lua:main_12` | 2/2 | 2/2 | 1 | 1 | 69 | 71 | 21 | 21 | match |
| `snr_lib.lua:main_1` | 2/2 | 2/2 | 1 | 1 | 46 | 44 | 14 | 14 | match |
| **`snr_graphic.lua:main_4`** | 7/8 | 7/8 | 1 | 1 | 178 | 175 | 44 | **42** | naming artifact, not a divergence |
| `snr_memory.lua:main_4` | 2/2 | 2/2 | 1 | 1 | 135 | 132 | 22 | 22 | match |
| `snr_mainmenu.lua:main_7` | 16/32 | 16/28 | 4 | 4 | 158 | 161 | 55 | 55 | match |
| **`snr_music.lua:main_3`** | 2/2 | **1/1** | 1 | **0** | 108 | **0** | 15 | **0** | **FAILS** |

`snr_graphic.lua:main_4` is not a real divergence: the two missing names are
`layerLoadAsync` and `layerIsLoad`, and my tracker cannot name a callee reached
through a temp. `[P]` The predecessor's source shows `g4 = layerLoadAsync ...
g4(...)` at line 776 and `v10 = layerIsLoad ... v10(...)` at line 845 — the
call still happens, inside the same loop, through a local alias.

**So the poll-loop cut corresponds on 18 of 19, and fails on one.**

### 5.3 `snr_story_main.lua:main_3` — the cut corresponds, the body has one
extra call

Read off both sides' bytecode:

```
ORIGINAL  pc 293-305
  EQ …; JMP
  GETGLOBAL cGetFileName; LOADK "sysgim"; LOADK "sys_5_b"; CALL
  TEST R11, C=1 ; JMP            -- the `or` fallthrough
  GETGLOBAL cGetFileName; LOADK "sysgim"; LOADK "sys_5_a"; CALL
  SETGLOBAL fileName             -- 2 call sites, tail shared by both arms

PREDECESSOR  pc 306-326
  … "sys_5_b"; CALL; MOVE; TEST; JMP
  … "sys_5_a"; CALL; MOVE; JMP
  … "sys_5_a"; CALL; MOVE
  SETGLOBAL fileName             -- 3 call sites: the shared `or` tail
                                    duplicated into the else arm
```

Semantically equivalent, structurally divergent.

### 5.4 `snr_common.lua:main_76_2` — one loop, four latches, and a tail written
out twice

**Round 0 published "1 poll loop → 4" and that was an artifact of counting back
edges as loops.** Grouped by header the predecessor has **one** poll loop
(header block 5) with **four** back edges (latches 60 / 68 / 188 / 274), union
body **78 blocks / 21 named calls**, against the original's one loop / one
latch / 62 blocks / 13 calls. `[P]` The predecessor source at
`snr_common.lua:3948` is a single `while v1 < 1 do … end` whose tail luac wrote
out twice.

So the *cut* corresponds and the *body* does not: the predecessor's loop body
carries 8 extra named calls, three of them `pressButton`. Round 0's "the
innermost with a 9-block body" named nothing and is withdrawn.

**The real finding here is behavioural, and it is in §9.2.**

### 5.5 `snr_music.lua:main_3` — the one structural failure

Raw back edges, as (source → header): original **`[(325,328), (365,12)]`**,
predecessor-recompiled **`[(343,346)]`**. (Round 0 published these tuples
inverted; the counts and the verdict were right.) The original's poll loop is
header 12, latch 365, 108-block body, 15 named calls including six
`pressButton`. The predecessor has no poll loop at all — its only back edge is
the `pairs()` `TFORLOOP`. Both sides' proto paths agree (`nups=7`,
`numparams=0`; 377 instructions against 407).

**This one is a shipped defect, and §9.1 has the behavioural evidence.**

### 5.6 The side that matters for Task 8 — our own output

The brief's cut is against the predecessor because that is the only other
*source* available. Task 8 compares against **our** reconstruction, and there
the answer is sharper:

> **CORRECTED 2026-08-14 by M6 task 8 (`docs/reports/m6-uiloop-design.md`
> §6). Two claims in this subsection were wrong; both were re-measured and the
> subsection's conclusion is unaffected.**
>
> 1. **The first column is labelled "headers" and its numbers are BACK
>    EDGES** — the same header/latch conflation §3.1 and §5.4 of this report
>    correct at length, surviving in this hand-built table. Re-measured, both
>    ways: `snr_music.lua` **3 headers / 4 back edges** (ours 13 / 203),
>    `snr_memory.lua` **8 / 12** (ours 12 / 320), `snr_mainmenu.lua`
>    **20 / 40** (ours 57 / 1210); `snr_lib.lua` is 2 either way. The poll and
>    proto columns are correct as published.
> 2. **"`pressButton` is never called through a `GETGLOBAL`-loaded register at
>    all" is FALSE.** The `GETGLOBAL pressButton` sites survive the fallback
>    **exactly** — 6→6 in `snr_music.lua`, 8→8 in `snr_memory.lua`, 36→36 in
>    `snr_mainmenu.lua`, 3→3 in `snr_lib.lua`. What breaks is register
>    *adjacency*: the loaded value is spilled into the numerically-keyed
>    `__pld_R` box and reloaded before the `CALL`, so a tracker keyed on
>    `GETGLOBAL`-to-`CALL` register provenance loses it while a tracker
>    following constant-numeric table keys would not. The call site is
>    displaced, not erased.
>
> The table and prose below are left as originally published so the correction
> is auditable rather than silent.

| file | original (**back edges** / poll / protos) | our shipped artifact |
|---|---|---|
| `snr_lib.lua` (ships structured, root `L3`) | 2 / 1 / 3 | **2 / 1 / 3 — identical** |
| `snr_music.lua` (whole-file fallback) | 4 / 1 / 5 | 203 / **0** / 14 |
| `snr_memory.lua` (fallback) | 12 / 1 / 6 | 320 / **0** / 16 |
| `snr_mainmenu.lua` (fallback) | 40 / 4 / 9 | 1210 / **0** / 22 |

Where a proto certifies `L3` the correspondence is **exact by construction** —
the recompiled `code` array is byte-identical. Where it ships the M2 fallback
there is **no correspondence to have**: the state machine dissolves control
flow into a pc dispatch, and `pressButton` is never called through a
`GETGLOBAL`-loaded register at all — it is stored into and re-read from the
`__pld_R` register array, so there is no syntactic call site to cut against.
The 203/320/1210 "loops" are the dispatcher's, not the program's.

Of the 19 poll protos, 9 are `L3` and 10 are `L1`; **2 ship structured text**
(`snr_lib.lua:main_1`, `snr_fragment_main.lua:main_3`) and 17 ship fallback.

### 5.7 Verdict on (a)

**The design assumption holds on 18 of 19 and its one failure is a real
defect, not a boundary disagreement.** Against our own output the cut is exact
where we certify and absent where we fall back.

**What Task 8 should take from this**: the per-iteration cut is well-defined on
the original side for every one of the 19; it is well-defined on our side only
for protos that already certify `L3`; and on the 17 that ship fallback the
instrument has to cut the *original* against a reconstruction it produces for
the purpose, not against `build/decompiled/`.

---

## 6. Pre-measurement (b) — input-space sizes

### 6.1 The model

A **channel** is a dotted access path whose value reaches a branch decision
(`EQ`/`LT`/`LE` against a constant, or `TEST`/`TESTSET`) and is rooted at a
global read or a call result — the owner's (a) and (b). Its **domain size** is
`|distinct constants compared against| + 1`, or 2 when there are none. The
**input space** is the product; `drivable` means the product is at most 4096.

`channels` is deliberately **narrower** than Task 3's footprint: it is the
branch-reaching subset. Both now ship on every record — `mechanical.footprint`
carries Task 3's full read/call surface, joined by `(file, proto_path)` (§7).

### 6.2 The result

**1940 of 1944 protos corpus-wide (99.8%) have an input space ≤ 4096**, and
within the candidate set **110 of 113 `choice-branch`**, 11/11 `ui-keyloop`
and 38/38 `neither`.

The `choice-branch` distribution, re-derived after the dataflow replaced the
block-local pass (§6.3) — **round 0's figures here were stale and are the
second defect of that kind in this task**:

```
input_space :  2   4    6   12   16   32   40   96  192  240  384  448
records     :  2   1   74    7   13    1    1    3    1    1    1    1
input_space : 1152 2304 3456 4608 12288 262144
records     :    2    1    1    1     1      1
```

**median 6, mode 6 with 74 records.** Representative sets straight from the
records:

```
snr_crd_10.lua:main_2   6       gameSave.myCard[9].hold (2), oCard.selectCardObj() (3: -1, 9)
snr_lib.lua:main_1      2       pressButton() (2)
snr_memory.lua:main_4   4       pressButton() (2), systemSave.memoryFlag[*] (2)
snr_mainmenu.lua:main_7 128     pressButton(), gameSave.startMenuState (4),
                                systemSave.libFlag/novelFlag/musicFlag,
                                gameSave.myCard[140].hold
snr_crd_89.lua:main_9   4608    over budget
snr_crd_103.lua:main_12 12288   over budget
snr_crd_104.lua:main_16 262144  over budget
```

The four over-budget protos corpus-wide, all named: `snr_crd_104.lua:main_16`
262144, **`snr_mainmenu.lua:main` 32768** (not a `choice-branch` candidate and
never named in round 0), `snr_crd_103.lua:main_12` 12288,
`snr_crd_89.lua:main_9` 4608.

**So Task 7 does not have to degrade to sampling on account of size.** But see
§6.4 before writing "exhaustive" anywhere.

### 6.3 The block-local pass was wrong, and an audit caught it

Round 0 implemented the pass block-local with an empty entry state, on the
strength of `lift/footprint.py`'s measurement that a full dataflow moves **0
of 11910** table-read sites. **That measurement does not transfer.** Footprint
attribution asks "which global is this `GETTABLE`'s base", and `lparser.c`
emits the pair adjacently inside one expression. This pass asks "which
constants is this value compared against", and a comparison is a block
*terminator*, so the second comparison of `if x == a then ... elseif x == b`
is always in a different block from the definition of `x`.

| | block-local | dataflow |
|---|---|---|
| candidate records differing | — | **110 of 162** (always upward) |
| worst ratio | — | **36×** (`snr_s4_10_s.lua:main_58`, 32 → 1152) |
| `snr_crd_13.lua:main_2` | 4 | **6** |
| `snr_crd_103.lua:main_12` | 11264 | **12288** |
| `snr_crd_104.lua:main_16` | 245760 | **262144** |
| `choice-branch` drivable | 111/113 | **110/113** |
| corpus-wide ≤ 4096 | 1941/1944 | **1940/1944** |

The concrete instance: `snr_crd_13.lua:main_2` does `CALL a=3` at pc 39,
`EQ 0 R3 K(132)` at pc 40 (which ends the block), and `EQ 0 R3 K(-1)` at pc
43 in the next block. One record crossed the budget on this alone
(`snr_crd_89.lua:main_9`, 4096 → 4608).

`MOVE` provenance propagation is carried here for the same reason and with its
own measurement: `footprint.py` records 0 deltas from it; here it changes the
input space of **13 of 1944** protos.

**The dataflow needed a real termination argument.** Agreement-meet from an
empty (bottom) initial entry makes entries *grow* in the first sweeps, and a
register can then flip between two paths forever: `snr_common.lua:main_72`
(236 instructions, 111 blocks, 40 `EQ`/`JMP` pairs) is the one proto of 1944
that does it, and it was still churning after 64 sweeps. The shipped form is
the standard MFP shape — unreached entry is `None` (top), the CFG entry starts
empty, each entry is intersected with its own previous value so it only
descends — with entry and exit computed per block in ascending block order so
a straight-line region settles in one sweep. Sweeps to convergence over all
1944 protos: **2 → 1753, 3 → 161, 4 → 29, 5 → 1** (`snr_graphic.lua:main`).

### 6.4 Three limits, all measured, none closed

**(i) `input_space` is a PER-ITERATION figure for Class 1 too**, and more
generally §3.6: 113/113 `choice-branch` candidates have an option call inside
a natural loop, 112/113 have all of them inside one, 258 of 260 sites overall.

**(ii) Parameters are not channels.** `snr_common.lua:main_75` has
`numparams=1` and branches on that parameter at pcs 1, 16, 48 and 95; none is
counted. `snr_s5_10_s.lua:main_43`'s only option branch is `EQ 0 R8 R1` with
R1 a parameter. `input_space` is a **per-argument-vector** figure. Related and
separately counted: a comparison against another register contributes no
domain and falls back to a floor of 2 — `corpus_register_comparisons` is
**24** over 16 protos out of 3371 `EQ`/`LT`/`LE` sites corpus-wide.

**(iii) The product assumes independence, and on the largest protos it is the
wrong model in both directions at once.** `snr_crd_104.lua:main_16` reads 14
distinct `gameSave.myCard[N].hold` flags. The 2^14 is *real in the CFG*: each
guard is the same 23-instruction block and its two successors reconverge
(`blk 1 succs=(12,13)`, `blk 12 succs=(30,)`, `blk 13 succs=(30,)`), the only
`RETURN` is at pc 1162, and there is no forward jump past the remaining
guards. But each guard's failing arm ends in `GETGLOBAL quit; CALL` — verified
for all 14 bail blocks (starts 13, 36, 59, …, 312) — and **no corpus file ever
`SETGLOBAL`s `quit`** (checked across all 229, same for `run` and
`pressButton`), so `quit` is engine-provided and the bytecode cannot say
whether it returns. If it does not, the 14 guards collapse to **15** semantic
outcomes. Meanwhile the single aggregated `oCard.selectCardObj()` channel of
domain **16** (15 constants + 1) **under**-counts: the 14 call sites sit in 14
*sequential, independent* natural loops (headers 335, 393, …, 1089; latches
384 … 1138; option calls at pcs 339, 397, …, 1093), each comparing against its
own card id **and `-1`** — so the constant sets are *not* pairwise disjoint,
they all share `-1`, and each loop's own domain is 3. At least 3^14 per run.
`[P]` The predecessor's `snr_crd_104.lua` shows the same shape as fourteen
`if gameSave.myCard[N].hold == -1 then … quit() end` blocks followed by
fourteen `while … do … oCard.selectCardObj() … end` loops. (Round 0 cited
`snr_crd_103.lua` in this paragraph, which is a different file with ten of
each.)

**So the answer to (b):** the input spaces are small enough that Task 7 need
not sample *on grounds of size* — 110/113 Class-1 candidates and 1940/1944
protos corpus-wide fit a 4096 budget, and the median Class-1 space is **6**.
But "strict formal verification" cannot be claimed over *behaviour*; it can be
claimed over **a stated channel set with a stated exclusion list** —
parameters excluded, register comparisons floored at 2, the independence
assumption declared, and (§3.6) the iteration count unbounded. The three
over-budget candidates are exactly the ones where the independence assumption
is measurably false, so they should be handled by their loop structure rather
than by a product.

---

## 7. The schema, and which half a regeneration may rewrite

Every record has two halves, explicit in the JSON:

- **`mechanical`** — recomputed on every run from the original bytecode, the
  committed ledger, Task 3's footprints and the behaviour probe. A
  regeneration may rewrite any of it. The class assignment lives here because
  it is a rule over measured predicates.
- **`observed`** — copied verbatim from the committed file, keyed by
  `(file, proto_path)`. `reviewed_by`, `class_agrees`, `note`. A regeneration
  never invents or edits one.

**The footprint join, which round 0 shipped without.** The brief's Step-1
deliverable is that each record carries "the interaction surface (stub-call set
+ table-key read set from Task 3)". Round 0 shipped only the narrower
branch-reaching `channels` and did not say so. Every record now carries
`mechanical.footprint` — `global_reads`, `table_key_reads`, `calls`,
`table_key_calls`, `dynamic_reads`, `read_sites`, `call_sites` — read straight
out of `corpus/observation/footprints.json` and joined by `(file,
proto_path)`. `corpus/observation/footprints.json` is now a **required** input:
a missing file raises rather than silently degrading, which is how the
omission happened. Task 7 wants `channels` to enumerate and `footprint` to
stub.

**Orphan observations, which round 0 dropped silently.** An observation whose
`(file, proto_path)` no longer names a candidate is now moved to a top-level
`orphan_observations` list, counted in the summary, and announced on stderr
with a `!`-banner naming each one. It is **re-attached** if the candidate comes
back. The realistic trigger is the milestone's own goal — a proto certifies
`L3`, leaves the leaf-refusal population, and a human-reviewed note has
nothing to attach to. Round 0's behaviour was measured by review: 162 records
/ 64 observations regenerated to 1 / 1, exit 0, no warning. The round trip
(drop → quarantine → re-attach) is a test.

**`--fresh` now refuses** to overwrite a file that carries observations unless
`--force` is also given; in-repo it prints the count and exits 1. Round 0's
`--fresh` would have erased all 64.

**Regeneration-stability proof.** `test_classes_json_is_a_reproducible_fixed_
point` runs the generator once with `--fresh` against a scratch `ROOT` (so the
committed file is never touched as a side effect — the
`tests/test_ledger_ratchet.py` precedent), asserts no record came back with an
`observed` key, re-inserts the committed observations, and asserts the result
is **byte-identical** to the committed file. So one test proves both halves:
the mechanical half is a fixed point, and it cannot depend on an observation.
The generator's own carry-over is proved separately over a **one-file** corpus
(0.05s). Three serial runs of the job produce a byte-identical file (sha256
`395d53d2…`), and `corpus/ledger.jsonl` did not move.

**Red line.** Every string in the document is printable ASCII: name emission
reuses `scripts/footprint_dump.py`'s rule verbatim, and structural segments
are `{"index": n}` / `{"dynamic": true}` / `{"call": true}`. The generator
refuses to write a document containing a byte outside `0x20..0x7e`
(`_assert_ascii`); that guard is **defensive** (`non_identifier_names == 0`
over all 229 files) with a synthetic test as its only evidence. The
`SELF_BASE` sentinel added in round 1 is `b"<upvalue>"`, deliberately not
identifier-shaped so it cannot collide with a corpus name, and it never
reaches the emitted JSON.

---

## 8. Suite cost, and the attribution

`tests/test_observation_classes.py` is **21 tests**. Full run **3.1s
standalone**, of which **~2.4s is the whole-corpus fixed-point regeneration**.
Suite total after round 1: **917 passed in 45.20–45.63s**.

**Round 0 gated the regeneration out of the default suite** on measured
grounds: two A/B pairs gave **913 passed in 44.88 / 44.85s** with it against
**896 in 40.81 / 40.90s** without — **+4.0s** against a 45s ceiling.

**Round 1 puts it back, and two things changed.** The ceiling was raised to
~120s (CLAUDE.md, `d97e3bc`) as an **earmark** for M6's formal-verification
instruments, so at ~45s nothing is competing for the earmarked headroom. And
the round-1 review demonstrated by neuter/restore that this test is the **only
thing that catches a whole class of mutation**: perturbing
`mechanical.n_insns` passes the entire default suite and fails only here. That
is the argument the coordinator accepted for `tests/test_footprint.py`'s 0.9s
regeneration, applied to the same kind of artifact. `scripts/ratchet_job.sh`'s
gate 4 is removed again; gate 1 covers it.

Re-measured after the change, two clean in-batch A/B pairs: **917 passed in
45.41 / 45.20s** with, **896 in 41.58 / 41.65s** without — **+3.8 / +3.6s**,
reproducing round 0's +4.0s. (A third pair taken while background jobs were
running gave 45.63 vs 44.78s; only within-batch deltas are comparable on this
host, and that pair's baseline was contaminated.) Against a ~120s ceiling the
margin is ~75s.

**The attribution, stated because the earmark requires it: ~2.4s, for the
fixed-point gate of the observation data Tasks 7 and 8 consume.** That is
*adjacent to* the earmark rather than squarely inside it — this is not itself
one of the named instruments (Track 1.1 arm 4 / Task 7 / Task 8's prototype).
It is flagged here and at the test so it can be overruled without archaeology.
The standing headroom lever (`tests/test_behaviour_probe.py::
test_corpus_behaviour_matches`, ~10s setup) was not touched.

The job itself (`PYLUADEC_CORPUS_DIR=... uv run python
scripts/observation_classes.py`) measures **2.4–2.8s** wall, dominated by
lifting all 1944 protos (1.09s, the same cost `footprint_dump.py` pays) plus
the 229-file behaviour probe (0.47s with 8 threads) and the channel dataflow
(0.33s on warm CFGs).

---

## 9. The two predecessor divergences, and what they say about our instruments

These are the milestone's first genuine cross-corpus return, and they came out
of running (a) on all 19 protos instead of the 2–3 the brief asked for.

### 9.1 `snr_music.lua` — the music gallery is unusable, and it shipped

Structural evidence: §5.5. Behavioural evidence, measured this session through
the repo's own L2 harness (`scripts/probe_keyseq.py`, spec
`entry=main;tail=`, i.e. no key ever pressed):

| | status | events | polls | frames polled on |
|---|---|---|---|---|
| original bytecode | `CAP` | 3001 | **2502** | many (101, 103, 105, …) |
| predecessor source | `OK` | **94** | **6** | **31 only** |

The original spins waiting for input, which is what a gallery screen does. The
predecessor polls each of the six keys once, on one frame, and falls out of the
function into `run(cGetFileName("script", "snr_mainmenu"))`. **The music
gallery bounces straight back to the main menu.** `[P]` The predecessor's
`main` (source line 176) is straight-line with no `while`; the bytecode
measurement above does not depend on reading it.

### 9.2 `snr_common.lua:main_76_2` (`SystemConfig.ConfigMain`) — the
restructuring is not semantics-preserving

The structural claim round 0 made about this proto is withdrawn (§5.4); the
real finding is behavioural, and one half is verifiable from both sides
directly.

**(a) A `break` promoted from gated to unconditional.** Original bytecode,
pcs 83–94:

```
83 EQ 0 R1 K(3.0)        ; 84 JMP -> 89
85 GETGLOBAL memoryFlag  ; 86 EQ 0 R3 KTrue ; 87 JMP -> 89 ; 88 JMP -> 94
89 keyPlaySE(seName.circle) …                ; 93 JMP -> 173   (leaves the loop)
94 GETGLOBAL pressButton ; LOADK "CROSS" …                     (the loop tail)
```

So when the cursor row is 3 **and** `memoryFlag == true`, the original takes pc
88 to **94** — the loop tail — with **no `keyPlaySE` and no exit**. `[P]` The
predecessor's source at lines 3981–3990 puts the `break` *outside*
`if not (memoryFlag == true)`, so it fires unconditionally. Both readings are
independent: the original's is bytecode, the predecessor's is its own text.

**(b) An empty `else` where the original reaches the tail's `wait`.** The
same gate in the `firstFragment == 1` arm (original pcs 63–74) jumps to 94 on
`memoryFlag == true`, entering the CROSS/UP/DOWN chain; `[P]` the predecessor
(lines 3971–3979) has `else` with an empty body. **The consequence — a
same-frame re-poll with no `wait`, i.e. a hang — is the review's reading, not
a measurement of mine**, and is recorded as such.

**Both are verbatim the two historical checkpoints in
`DEBUG_KEY_SEQUENCE_HARNESS.md`.**

### 9.3 The finding about our own instruments

**M5 task 10 built `tests/test_keyseq_checkpoints.py` for exactly these two
historical bugs, and it is blind to them.** Two reasons, one structural and one
measured:

- Structural: the checkpoint tests drive the **original** against **our
  artifact**. The predecessor is not one of the two sides, so a predecessor
  defect cannot appear by construction.
- Measured this session: driving the original bytecode and the predecessor
  source through `scripts/probe_keyseq.py` with the module's own two authored
  specs (`OPTION_CLAMP_SPEC`, `CONFIG_GATE_SPEC`) gives **byte-identical
  traces** — `OK|376|0`, 129 polls on both sides, and `OK|202|0`, 37 polls on
  both sides. The sequences never reach the arms the gates select.

This is a statement about the instrument, not only about the predecessor, and
it should be routed to Task 5/6 (the divergence queue) and to Task 8: a
checkpoint test that cannot fail on the bug it was written for is a guard whose
load-bearingness has not been established against the shape it names.

---

## 10. Numbers that did not reproduce, and things I got wrong

Round 0's table, plus what round 1 overturned.

| figure | as carried in | measured | round |
|---|---|---|---|
| "~20 leaf refusal sites" | the brief | **36** | 0 |
| block-local channel pass | mine | wrong on **110/162**, worst ratio **36×** | 0 |
| "`input_space` is per-call for Class 1" | mine | per-iteration, 113/113 | 0 |
| "`neither` = no interaction channel" | mine | 9 of 38 have one | 0 |
| naive dataflow terminates | mine | it does not (`snr_common.lua:main_72`) | 0 |
| id-keyed CFG cache is safe | mine | not unless the entry pins the proto | 0 |
| **`n_natural_loops`** | **mine** | **a back-edge count; wrong on 14 of 162** (`snr_mainmenu:main_7` 32 vs **16**) | **1** |
| **`main_76_2`: "1 poll loop → 4"** | **mine** | **one loop, four latches**; (a) is **18/19**, not 17/19 | **1** |
| **"all seven option callees are poll loops"** | **mine** | **3 of 7 have zero loops**, incl. both `oCard` selectors | **1** |
| **§6.2 "76 records at 4, median 4"** | **mine, stale** | **74 at 6, median 6**; `snr_crd_10:main_2` is **6** | **1** |
| **`snr_crd_104` option domain "15"** | **mine** | **16**; and the 14 constant sets share `-1`, so not disjoint | **1** |
| **"the nine reach an interaction one call out"** | **mine** | hops **1,1,2,4,4** and 4 unreached; only **2** read-and-branch | **1** |
| **`protos_reaching_poll` 331** | **mine** | **443** with `self.method()` edges; still a floor | **1** |
| **§5.4/§5.5 raw back-edge tuples** | **mine** | **inverted**; orig `[(325,328),(365,12)]`, pred `[(343,346)]` | **1** |
| **`snr_mainmenu:main_7` latches 556/1101/1636/2181** | **mine** | **553/1098/1633/2178** | **1** |
| **`corpus_register_comparisons` "20 (1.3%)"** | **mine** | **24** under the dataflow | **1** |
| **the 4th over-budget proto unnamed** | **mine** | **`snr_mainmenu.lua:main`, 32768** | **1** |
| **`[P]` citing `snr_crd_103` in a `snr_crd_104` paragraph** | **mine** | wrong file | **1** |
| **the Step-1 footprint join** | **mine** | **never done**, and never acknowledged | **1** |
| **"a regeneration never drops an observation"** | **mine** | it did, silently: 64 → 1, exit 0 | **1** |
| **§5.6's first column, labelled "headers"** | **mine** | **back edges**; headers are 2 / **3** / **8** / **20** (ours 2 / **13** / **12** / **57**) | **T8** |
| **§5.6 "`pressButton` is never called through a `GETGLOBAL`-loaded register at all"** | **mine** | **false** — those sites survive the fallback exactly (6→6, 8→8, 36→36, 3→3); register *adjacency* is what breaks, via `__pld_R` | **T8** |

Rows marked **T8** were found by M6 task 8 on 2026-08-14 and are corrected
inline at §5.6; see `docs/reports/m6-uiloop-design.md` §6. Neither changes
§5.6's or §5.7's conclusion.

Figures from earlier tasks that **did** reproduce this session: 229 files /
1944 protos; 48 non-`L3` rows splitting `structure` 21 / `mismatch` 22 /
`reconstruct` 5; the behaviour probe's 132 `CAP` / 97 `OK` / 398196 events and
its 101 `vms` / 26 `wait` / 5 `pressButton` split; 19 `pressButton` protos over
9 files; `corpus/ledger.jsonl` byte-identical after a full `run_corpus.py`. The
round-0 dataflow figures all re-derived unchanged, including the 36× on
`snr_s4_10_s:main_58` (32 → 1152).

---

## 11. What Tasks 7 and 8 inherit

1. **The option channel bottoms out in corpus-defined code** (§3.3) — but only
   4 of the 7 callees are themselves poll loops; the other 3 are one hop
   further. Task 7's oracle abstraction is sound because what is behind an
   option call is another proto in the same corpus, not because it is a loop.
2. **Class 1 is not one-shot, and shares Class 2's termination problem**
   (§3.6): 127 of 162 candidates poll the key every iteration, 113/113 of
   Class 1 among them. Task 7 needs a per-iteration schedule; Task 8's design
   note must not scope its termination argument to 11 protos.
3. **Task 8's cut exists on the original for all 19 poll protos, on our side
   only where we certify** (§5.6); the 17 that ship fallback need a
   purpose-built reconstruction.
4. **`neither` is about a proto's own body, and `protos_reaching_poll` (443) is
   a floor** (§3.4) — local-closure upvalue calls are still not edges, and
   four named candidates sit behind exactly that gap.
5. **Three candidates are over budget and are exactly where the product model
   is measurably wrong** (§6.4 iii); a fourth corpus proto,
   `snr_mainmenu.lua:main`, is over budget outside the candidate set.
6. **`snr_mainmenu.lua:main_7`'s four poll loops have zero CFG exit edges**
   (§4) — the strongest form of the Class-2 worry present in the corpus.
7. **Two predecessor defects and one blind instrument** (§9) — route to the
   divergence queue and to Task 8.

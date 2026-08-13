# M6 task 4 — meta-observation of the corpus's hard protos

Everything here was measured on 2026-08-13 on macOS 15.2 / arm64 (Mac mini,
Darwin 24.2.0), against `PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/
script_to_decompile` (229 files, 1944 protos) and, where the predecessor is
named, `PYLUADEC_PRED_CORPUS_DIR=/Users/fotile96/Zndnovel/lua_scripts`.

Artifacts: `scripts/observation_classes.py` (the generator, a JOB),
`corpus/observation/classes.json` (committed generated data, 162 candidate
records), `tests/test_observation_classes.py` (17 guards). The generator's
module docstring is the reference for the schema and the vocabularies; this
report is the measurement record and the argument.

**Which statements rest on the predecessor's text.** Only four, each marked
`[P]` in place: the identification of `snr_crd_10.lua`'s card-choice idiom
(§3.1), the `layerLoadAsync` / `layerIsLoad` local-alias artifact in
`snr_graphic.lua` (§5.2), the `keyWait` / `functionButton` readings that were
then re-derived from bytecode (§3.2), and the collapse reading of
`snr_crd_103.lua` (§6.4). Every one is a corroboration of a bytecode
measurement that is stated alongside it; none is load-bearing on its own.
Everything else in this document comes from the original bytecode, the
committed ledger, or the L1.75 behaviour probe.

---

## 1. Headline

| | |
|---|---|
| candidates | **162** over **137** files |
| leaf refusal sites | **36** of the 48 non-`L3` ledger rows |
| event-cap dominant protos | **132** (one per `CAP` file) |
| in both populations | **6** |
| class census | **`choice-branch` 113 / `ui-keyloop` 11 / `neither` 38** |
| drivable within a 4096 budget | `choice-branch` **110/113**, `ui-keyloop` 11/11, `neither` 38/38 |
| corpus-wide input space ≤ 4096 | **1940 / 1944 protos (99.8%)** |
| pre-measurement (a): poll-loop cuts that correspond | **15 of 19** outright; 17 of 19 once two measured artifacts are accounted for; **2 genuine failures** |

**Both pre-measurements land on the useful side, and neither is clean.** (a)
holds on the large majority but not universally, and the two failures are
instructive rather than marginal. (b) says the milestone does **not** have to
degrade to sampling on account of input-space size — but the product model
that produces the number is measurably the wrong model for the largest
protos, so "exhaustive" must be said about a stated channel set, not about
behaviour.

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

## 3. The classes, and the structural finding underneath them

### 3.1 The rule

- **`ui-keyloop`** — the proto's own body has a natural loop whose body
  contains a direct `pressButton` call.
- **`choice-branch`** — it does not, but it calls an option-reading function
  from `OPTION_CALLEES`.
- **`neither`** — neither, *in its own body* (see §3.4, which is where this
  label is weaker than it sounds).

`test_class_is_exactly_its_own_evidence` recomputes the class from the two
published predicates on every record, so a hand edit or a rule/output drift
fails the suite.

The rule's Class-1 half was checked against a reading of `snr_crd_10.lua`'s
`main_2`: guard `gameSave.myCard[9].hold == -1` at pcs 7–11, then
`oCard.selectCardObj` at pc 39 inside the single natural loop (header block
35, back edge from block 82), result compared at pc 40 (`9`, break) and pc 43
(`-1`, cancel). `[P]` The predecessor's `snr_crd_10.lua` shows the same shape
as `while v2 < 1 do v5 = oCard.selectCardObj() ... end` — a corroboration of
the bytecode, in the shape Task 3 used.

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
loop**. Eleven of the 19 are candidates; the other eight are not in the
candidate set at all — every one of them is `L3` in the ledger and none is a
`CAP` file's dominant global. Named, with their identities recovered from
`CLOSURE`/`SETGLOBAL` and `CLOSURE`/`SETTABLE` pairs: `snr_common.lua`
`main_27` (`comDlgYesNoSel`), `main_28` (`comDlgStorylineSkip`), `main_55`
(`comStorySceneEnd`), `main_76_7` (`SystemConfig.confirm`), `main_77_24`
(`ObjectCard.cardModeSelect`); `snr_fragment_main.lua:main_3`;
`snr_novel.lua:main_7` and `main_12`.

### 3.3 The finding the classification rests on

**The option-display "stubs" the owner describes are not engine primitives —
they are Class-2 poll loops living in `snr_common.lua`.** Every entry in
`OPTION_CALLEES` resolves, through the corpus's own definitions, to a proto in
that file:

```
comDlgSelectItem              -> snr_common.lua:main_29
comDlgYesNo                   -> snr_common.lua:main_26
comDlgYesNoSel                -> snr_common.lua:main_27
comDlgStorylineSkip           -> snr_common.lua:main_28
comSelectMap                  -> snr_common.lua:main_71
oCard.selectCardObj           -> snr_common.lua:main_77_17
oCard.selectCardNotCancelObj  -> snr_common.lua:main_77_18
```

and the same construction identifies the peripheral-UI screens the owner named
as `SystemOption.OptionMain` = `main_74_13`, `SystemConfig.ConfigMain` =
`main_76_2`, `SystemConfig.Config` = `main_76_8` — which are exactly the two
checkpoints `DEBUG_KEY_SEQUENCE_HARNESS.md` records.

**Consequence for Tasks 7 and 8, and it is a good one.** The class boundary
falls on the corpus's own module boundary. A Class-1 proto can treat an option
call as an uninterpreted oracle over a small value domain *precisely because*
the implementation behind it is a separate proto that Task 8 owns as Class 2.
The decomposition the owner proposed is the one the program already has.

Two consequences the labels do not carry, both from the audits and both real:
`snr_common.lua:main_29` and `main_71` are classified `ui-keyloop` **and** are
themselves two of the seven option callees — the two predicates are being
applied at different levels of one call graph. And
`snr_story_main.lua:main_3` satisfies **both** predicates (it calls
`comDlgYesNo` at pc 314, inside its poll loop); `ui-keyloop` wins by priority
and the option call is still recorded on the row, so the data is not lost —
only the label is one-hot.

### 3.4 `neither` does not mean "no interaction channel" — 9 of 38 are
false negatives under that gloss

An independent audit of all 38 `neither` candidates confirmed that **none of
them calls `pressButton` or any option global in its own body**, so the rule
is applied correctly on all 38. Under the *gloss* the first version of the
docstring attached to it, **9 are wrong**, and the mechanism is a single
measured gap:

> `_call_graph` only builds an edge when the callee register carries
> **global-rooted** provenance. A call through an upvalue-held local closure
> (`GETUPVAL R0; CALL R0`) or through a `self` upvalue (`GETUPVAL R2,0;
> GETTABLE R2 R2 K"ConfigMain"; CALL`) is invisible.

The audit followed those chains and measured `protos_reaching_poll` = **390**
where the committed graph reports **331** (+59); a maximally permissive
method-key resolution gives 503. **The published 331 is a floor**, and now
says so at the site.

The clearest instance is `snr_common.lua:main_76_8` (`SystemConfig.Config`):
`GETUPVAL R2,0; GETTABLE R2 R2 K"ConfigMain"; CALL` at pcs 18–20, result
branched at pcs 25/38/40/55, `confirm` called at pcs 33/48 with `EQ 0 R2
KFalse` at 34/49 — the canonical read-then-branch shape, on two callees
(`main_76_2`, `main_76_7`) that both poll directly.

**The mechanical class was left as the rule computes it, and the nine
disagreements are recorded in the `observed` half** with `class_agrees:
false` and the bytecode evidence. A class that quietly disagreed with its own
published evidence would be worse than one that is narrow and says where it
is narrow. The nine: `snr_common.lua` `main_74_18` and `main_76_8`;
`snr_crd_102.lua:main_5`; `snr_e1_10_s.lua:main_29`; `snr_e2_10_f.lua:main_35`;
`snr_e2_10_s.lua:main_13`; `snr_s0_10_f.lua:main_7`; `snr_s7_10_f.lua:main_53`;
`snr_s8_10_s.lua:main_5`.

### 3.5 Census by population

| | `choice-branch` | `ui-keyloop` | `neither` |
|---|---|---|---|
| leaf refusal sites (36) | 5 | 10 | 21 |
| CAP dominants (132) | 111 | 4 | 17 |
| union (162) | **113** | **11** | **38** |

The `choice-branch` population is dominated by one shape: **103 of 113** are a
`snr_crd_*` file's `main`, calling `oCard.selectCardObj`. The remaining ten
are `snr_common.lua:main_75` (`comDlgYesNo` ×4), the six `snr_s*_10_s` /
`snr_s4_10_fb` story dispatchers (`comDlgSelectItem`, some with
`comSelectMap`), and `snr_s5_10_s.lua`'s `main_42` / `main_43`
(`oCard.selectCardNotCancelObj`).

---

## 4. Per-proto observation

64 of the 162 records carry an individually reviewed `observed` block: **all
11 `ui-keyloop`**, **all 38 `neither`**, and **15 `choice-branch`** (a
systematic sample of 12 — the sorted list at indices 0, 10, …, 110 — plus the
three whose input space exceeds the budget). The other 98 `choice-branch`
records are the `snr_crd_*` family, whose evidence signature is identical
across the sample: one `myCard[N].hold` guard, one `oCard.selectCardObj` at pc
39 inside the single natural loop, and comparisons against the card id and
`-1`. They are **not** individually reviewed and carry no `observed` block, so
`n_observed_records` reports 64 rather than 162 and a later reader can see
which is which.

The per-proto justifications live in the records themselves rather than being
copied here: `corpus/observation/classes.json`, field `observed.note`, keyed by
`(file, proto_path)`. Every note names opcodes, pcs, registers and ASCII
identifiers only. Highlights that bear on Tasks 7 and 8:

- **`snr_mainmenu.lua:main_7`** — four poll loops (back edges from blocks 556,
  1101, 1636, 2181), and **measured: none of the four has a CFG exit edge at
  all**. They are left only through engine calls that do not return — 23
  `quit()` sites, each preceded by `run(cGetFileName("script", ...))`. This is
  the strongest form of the owner's Class-2 worry in the corpus: not "a finite
  key sequence may not terminate the loop" but "no key sequence terminates the
  loop; only a non-returning call does".
- **`snr_music.lua:main_3`** — exits only when a `TFORLOOP` scan over
  `selectFlag` (pcs 319–329) finds nothing, i.e. termination depends on
  accumulated table state, not on the key alone.
- **`snr_common.lua:main_81`** (`keyWait`) — mechanically `ui-keyloop`, but it
  is a 26-instruction input helper with no screen state. The label is right
  and the phrase "peripheral UI" is not.

---

## 5. Pre-measurement (a) — loop-body boundary correspondence

### 5.1 What was cut, and the criterion stated before looking

For each proto that polls, on **both** sides — the original bytecode and the
predecessor source recompiled with the in-repo `luac_sz4` (`predcorpus.
load_pred_proto(..., strip=True)`, matching `certify_l3`'s strip precedent) —
I cut the natural loop whose body contains a `pressButton` call and recorded
(i) how many such loops there are, (ii) the loop's header and back-edge
blocks, (iii) the body's block count, and (iv) the sequence of resolvable
callee names inside the body, in pc order.

The cut points **correspond** iff both sides yield the same number of poll
loops and the same body call-name sequence. pcs are *not* expected to match:
Task 2 measured that the predecessor's output is byte-faithful nowhere.

This was run on **all 19 protos that call `pressButton`**, not the 2–3 the
brief asked for.

### 5.2 Result: 15 outright, 17 after two measured artifacts, 2 failures

| proto | orig loops | pred loops | orig body | pred body | orig calls | pred calls | verdict |
|---|---|---|---|---|---|---|---|
| `snr_common.lua:main_27` | 1 | 1 | 55 | 53 | 12 | 12 | match |
| `snr_common.lua:main_28` | 1 | 1 | 57 | 55 | 13 | 13 | match |
| `snr_common.lua:main_29` | 1 | 1 | 79 | 79 | 18 | 18 | match |
| `snr_common.lua:main_55` | 1 | 1 | 52 | 50 | 13 | 13 | match |
| `snr_common.lua:main_71` | 1 | 1 | 38 | 36 | 10 | 10 | match |
| `snr_common.lua:main_74_13` | 1 | 1 | 266 | 252 | 24 | 24 | match |
| **`snr_common.lua:main_76_2`** | **1** | **4** | **62** | **9** | **13** | **1** | **DIFFER** |
| `snr_common.lua:main_76_7` | 1 | 1 | 55 | 53 | 12 | 12 | match |
| `snr_common.lua:main_77_24` | 1 | 1 | 91 | 90 | 26 | 26 | match |
| `snr_common.lua:main_81` | 1 | 1 | 11 | 12 | 3 | 3 | match |
| `snr_fragment_main.lua:main_3` | 1 | 1 | 103 | 101 | 65 | 65 | match |
| **`snr_story_main.lua:main_3`** | 1 | 1 | 92 | 91 | **50** | **51** | differ (§5.3) |
| `snr_novel.lua:main_7` | 1 | 1 | 32 | 33 | 6 | 6 | match |
| `snr_novel.lua:main_12` | 1 | 1 | 69 | 71 | 21 | 21 | match |
| `snr_lib.lua:main_1` | 1 | 1 | 46 | 44 | 14 | 14 | match |
| **`snr_graphic.lua:main_4`** | 1 | 1 | 178 | 175 | **44** | **42** | differ (§5.2) |
| `snr_memory.lua:main_4` | 1 | 1 | 135 | 132 | 22 | 22 | match |
| `snr_mainmenu.lua:main_7` | 4 | 4 | 145 | 144 | 60 | 60 | match |
| **`snr_music.lua:main_3`** | **1** | **0** | **108** | **0** | **15** | **0** | **DIFFER** |

`snr_graphic.lua:main_4` is **not** a real divergence. The two missing names
are `layerLoadAsync` and `layerIsLoad`, and my tracker cannot name a callee
reached through a temp. `[P]` The predecessor's source shows
`g4 = layerLoadAsync ... g4(...)` at line 776 and `v10 = layerIsLoad ...
v10(...)` at line 845 — the call still happens, inside the same loop, through
a local alias. Counting this as corresponding gives **16 of 19**.

### 5.3 `snr_story_main.lua:main_3` — the cut corresponds, the body does not

The predecessor's loop body has one extra `cGetFileName` call site. Read off
both sides' bytecode:

```
ORIGINAL  pc 293-305
  EQ …; JMP
  GETGLOBAL cGetFileName; LOADK "sysgim"; LOADK "sys_5_b"; CALL
  TEST R11, C=1 ; JMP            -- the `or` fallthrough
  GETGLOBAL cGetFileName; LOADK "sysgim"; LOADK "sys_5_a"; CALL
  SETGLOBAL fileName             -- 2 call sites, tail shared by both arms

PREDECESSOR  pc 306-326
  … GETGLOBAL cGetFileName; …"sys_5_b"; CALL; MOVE
  TEST; JMP
  GETGLOBAL cGetFileName; …"sys_5_a"; CALL; MOVE; JMP
  GETGLOBAL cGetFileName; …"sys_5_a"; CALL; MOVE
  SETGLOBAL fileName             -- 3 call sites, the shared `or` tail
                                    duplicated into the else arm
```

Semantically equivalent, structurally divergent: the predecessor turned
`a() or b()` into an `if`/`else` and copied the `or` tail into both arms.
Counting the *cut* as corresponding (it does — one loop each, same header
region, same 91/92-block body) gives **17 of 19**.

### 5.4 The two genuine failures

- **`snr_common.lua:main_76_2` (`SystemConfig.ConfigMain`).** Original: one
  poll loop, 62-block body, 13 named calls. Predecessor-recompiled: **four**
  poll loops, the innermost with a 9-block body and one call. 174 original
  instructions become 279. The predecessor tail-duplicated the poll loop into
  each branch arm.
- **`snr_music.lua:main_3`.** Original: two natural loops, one of them the
  poll loop (back edge from block 365 to block 12, 108-block body, 15 named
  calls including six `pressButton`). Predecessor-recompiled: **one** natural
  loop and **no** poll loop — raw back edges are `[(347, 342)]` on the
  predecessor side against `[(329, 324), (365, 12)]` on the original's. The
  outer `while` is simply **gone**: `[P]` the predecessor's `main` polls each
  key once, straight-line, and falls through to
  `run(cGetFileName("script", "snr_mainmenu"))`, with the loop's tail
  duplicated into two arms. Both sides' proto paths agree (`nups=7`,
  `numparams=0` on both; 377 instructions against 407).

### 5.5 The side that actually matters for Task 8 — our own output

The brief's cut is against the predecessor because that is the only other
*source* available. But Task 8 compares against **our** reconstruction, and
there the answer is sharper and was measured separately:

| file | original (natural / poll / protos) | our shipped artifact |
|---|---|---|
| `snr_lib.lua` (ships structured, root `L3`) | 2 / 1 / 3 | **2 / 1 / 3 — identical** |
| `snr_music.lua` (ships whole-file fallback) | 4 / 1 / 5 | 203 / **0** / 14 |
| `snr_memory.lua` (fallback) | 12 / 1 / 6 | 320 / **0** / 16 |
| `snr_mainmenu.lua` (fallback) | 40 / 4 / 9 | 1210 / **0** / 22 |

Where a proto certifies `L3` the correspondence is **exact by construction** —
the recompiled `code` array is byte-identical, so the loop is the same loop.
Where it ships the M2 fallback there is **no correspondence to have**: the
state machine dissolves the program's control flow into a pc dispatch, and
`pressButton` is never called through a `GETGLOBAL`-loaded register at all —
it is stored into and re-read from the `__pld_R` register array
(`GETGLOBAL R4 K"pressButton"; SETTABLE R0 K R4; ... GETTABLE R4 R0 K; CALL`),
so there is no syntactic call site to cut against. The 203/320/1210 "natural
loops" are the dispatcher's, not the program's.

Of the 19 poll protos: 9 are `L3` and 10 are `L1`; **2 ship structured text**
(`snr_lib.lua:main_1`, `snr_fragment_main.lua:main_3`) and 17 ship the
fallback.

### 5.6 Verdict on (a)

**The design assumption holds well enough to build on, and its failure mode is
now named.** Against the predecessor: 15/19 outright, 17/19 counting the two
artifacts above, 2 hard failures — both of which are the predecessor
restructuring a loop (duplicating it, or losing it), not a boundary
disagreement. Against our own output: exact where we certify, absent where we
fall back.

**What Task 8 should take from this**: the per-iteration cut is well-defined on
the original side for every one of the 19; it is well-defined on our side only
for protos that already certify `L3`; and on the 17 that ship fallback the
instrument has to cut the *original* against a *reconstruction it produces for
the purpose*, not against `build/decompiled/`. That is a design constraint the
plan did not state.

---

## 6. Pre-measurement (b) — input-space sizes

### 6.1 The model

A **channel** is a dotted access path whose value reaches a branch decision
(`EQ`/`LT`/`LE` against a constant, or `TEST`/`TESTSET`) and is rooted at a
global read or a call result — the owner's (a) and (b). Its **domain size** is
`|distinct constants compared against| + 1`, or 2 when there are none. The
**input space** is the product; `drivable` means the product is at most 4096.

### 6.2 The result

**1940 of 1944 protos corpus-wide (99.8%) have an input space ≤ 4096**, and
within the candidate set **110 of 113 `choice-branch`**, 11/11 `ui-keyloop`
and 38/38 `neither`. The `choice-branch` distribution is extremely
concentrated: 76 records at exactly **4** (one `hold` guard × one
`selectCardObj` channel of domain 2), a long thin tail, and three over budget.

Representative channel sets, straight from the records:

```
snr_crd_10.lua:main_2   4       gameSave.myCard[9].hold (2), oCard.selectCardObj() (2)
snr_lib.lua:main_1      2       pressButton() (2)
snr_memory.lua:main_4   4       pressButton() (2), systemSave.memoryFlag[*] (2)
snr_mainmenu.lua:main_7 128     pressButton(), gameSave.startMenuState (4),
                                systemSave.libFlag/novelFlag/musicFlag,
                                gameSave.myCard[140].hold
snr_crd_89.lua:main_9   4608    over budget
snr_crd_103.lua:main_12 12288   over budget
snr_crd_104.lua:main_16 262144  over budget
```

**So Task 7 does not have to degrade to sampling on account of size.** But see
§6.4 before writing "exhaustive" anywhere.

### 6.3 The block-local pass was wrong, and an audit caught it

The first implementation was block-local with an empty entry state, on the
strength of `lift/footprint.py`'s measurement that a full dataflow moves **0
of 11910** table-read sites. **That measurement does not transfer, and I
should not have inherited it.** Footprint attribution asks "which global is
this `GETTABLE`'s base", and `lparser.c` emits the pair adjacently inside one
expression. This pass asks "which constants is this value compared against",
and a comparison is a block *terminator*, so the second comparison of
`if x == a then ... elseif x == b then` is always in a different block from
the definition of `x`.

Measured, after rebuilding the pass as a forward dataflow and re-running:

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
43 in the next block. Nothing writes R3 between, so the true domain is 3 and
the block-local pass saw 2. One record crossed the budget on this alone
(`snr_crd_89.lua:main_9`, 4096 → 4608).

`MOVE` provenance propagation is carried here for the same reason and with its
own measurement: `footprint.py` records 0 deltas from it; here it changes the
input space of **13 of 1944** protos.

**The dataflow needed a real termination argument, and the naive one is
wrong.** Agreement-meet from an empty (bottom) initial entry makes entries
*grow* in the first sweeps, and a register can then flip between two paths
forever: `snr_common.lua:main_72` (236 instructions, 111 blocks, 40 `EQ`/`JMP`
pairs) is the one proto of 1944 that does it, and it was still churning after
64 sweeps. The shipped form is the standard MFP shape — unreached entry is
`None` (top), the CFG entry starts empty, and each entry is intersected with
its own previous value so it only descends — with entry and exit computed
per block in ascending block order so a straight-line region settles in one
sweep. Measured sweeps to convergence over all 1944 protos: **2 → 1753,
3 → 161, 4 → 29, 5 → 1** (`snr_graphic.lua:main`). The 64-sweep cap raises
rather than truncates.

### 6.4 Three limits, all measured, none closed — and the third is the one
that matters

**(i) `input_space` is a PER-ITERATION figure for Class 1 too.** The
generator's first docstring called it per-call — "fix one value per channel,
run once" — and the corpus falsified that flat: **113 of 113** `choice-branch`
candidates have at least one option call **inside a natural loop**, 112 of 113
have all of them inside one, and **258 of 260** option call sites overall are
in a loop. A story fragment re-polls its option channel per iteration exactly
as a UI screen re-polls the key, through `oCard.selectCardObj` /
`comDlg*` instead of `pressButton`. Each site carries `in_loop` so this is
checkable per site. **What separates the two classes is the termination
argument, not the shape of the input** — and the milestone's language should
say that rather than implying Class 1 is a one-shot.

**(ii) Parameters are not channels.** `snr_common.lua:main_75` has
`numparams=1` and branches on that parameter at pcs 1, 16, 48 and 95; none is
counted. `snr_s5_10_s.lua:main_43`'s only option branch is `EQ 0 R8 R1` with
R1 a parameter. `input_space` is therefore a **per-argument-vector** figure.
Related and separately counted: a comparison against another register
contributes no domain and falls back to a floor of 2 —
`corpus_register_comparisons` is **24** over 16 protos out of 3371 `EQ`/`LT`/
`LE` sites corpus-wide, so this one is small.

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
domain 15 **under**-counts: the 14 call sites sit in 14 *sequential,
independent* natural loops (headers 335, 393, …, 1089; back edges 384 … 1138;
option calls at pcs 339, 397, …, 1093), each comparing only against its own
card id and `-1`, with pairwise disjoint constant sets — at least 3^14 per
run. `[P]` The predecessor's `snr_crd_103.lua` shows the same shape as ten
`if gameSave.myCard[N].hold == -1 then … quit() end` blocks followed by ten
`while … do … oCard.selectCardObj() … end` loops.

**So the answer to (b), stated so the milestone can be honest:** the input
spaces are small enough that Task 7 need not sample *on grounds of size* —
110/113 Class-1 candidates and 1940/1944 protos corpus-wide fit a 4096 budget,
and the median Class-1 space is 4. But "strict formal verification" cannot be
claimed over *behaviour*; it can be claimed over **a stated channel set with a
stated exclusion list** — parameters excluded, register comparisons floored at
2, and the independence assumption declared. The three over-budget protos
(`snr_crd_89.lua:main_9`, `snr_crd_103.lua:main_12`, `snr_crd_104.lua:main_16`)
are exactly the ones where the last assumption is measurably false, so they
should be handled by their loop structure rather than by a product.

---

## 7. The schema, and which half a regeneration may rewrite

Every record has two halves, and the split is explicit in the JSON:

- **`mechanical`** — recomputed on every run from the original bytecode, the
  committed ledger and the behaviour probe. A regeneration may rewrite any of
  it. The class assignment lives here because it is a rule over measured
  predicates, not a judgement.
- **`observed`** — copied verbatim from the committed file, keyed by
  `(file, proto_path)`. `reviewed_by`, `class_agrees`, `note`. A regeneration
  never invents, edits or drops one. `--fresh` drops them all, which is how
  the independence is proved rather than promised.

**Regeneration-stability proof.** `test_classes_json_is_a_reproducible_fixed_
point` runs the generator once with `--fresh` against a scratch `ROOT` (so the
committed file is never touched as a side effect — the
`tests/test_ledger_ratchet.py` precedent), asserts no record came back with an
`observed` key, re-inserts the committed observations, and asserts the result
is **byte-identical** to the committed file. So one test proves both halves:
the mechanical half is a fixed point, and it cannot depend on an observation.
That the generator's own carry-over performs the re-insertion correctly is a
separate test over a **one-file** corpus (0.05s), which writes an `observed`
block by hand between two runs and checks it survives with the mechanical
halves unchanged.

Three serial runs of the job produce a byte-identical file (sha256
`414da95a…`), and `corpus/ledger.jsonl` did not move: `run_corpus.py` was
re-run at the start of this task to refresh `build/decompiled/` and `git
status` reported the ledger unchanged.

**Red line.** Every string in the document is printable ASCII: name emission
reuses `scripts/footprint_dump.py`'s rule verbatim (verbatim iff `0x20..0x7e`
and identifier-shaped, else `{"nonascii": "<hex>"}` built with `.hex()`, never
via `.decode()`), and structural segments are `{"index": n}`,
`{"dynamic": true}`, `{"call": true}`. The generator also refuses to write a
document containing a byte outside `0x20..0x7e` (`_assert_ascii`). That guard
is **defensive** — `footprints.json` measured `non_identifier_names == 0` over
all 229 files, so no corpus content can reach it — and its only evidence is
`test_ascii_guard_actually_refuses_a_non_ascii_document`, which is labelled as
synthetic in place.

---

## 8. Suite cost — measured, and then mostly moved out

`tests/test_observation_classes.py` is 17 tests. Run in full it costs **2.70s**,
of which **2.3s is the whole-corpus fixed-point regeneration**.

**The A/B said no.** Two serial pairs on this host, with everything in the
suite: **913 passed in 44.88 / 44.85s** against **896 in 40.81 / 40.90s**
without the file — **+4.0s**, putting a 45s ceiling at 44.9s. That is the
largest single addition any M6 task has made, and it is a corpus-wide
regeneration, which the plan's own rule calls a JOB rather than a per-run
suite cost.

So the regeneration is gated on `PYLUADEC_OBSERVATION_FIXED_POINT` and runs as
**gate 4 of `scripts/ratchet_job.sh`**, next to gate 3's full 24-case
differential sweep, which is there for exactly the same reason. What stays in
the per-commit suite is the cheap half — schema, class-vs-evidence coupling,
the input-space arithmetic, the `observed` shape, the ASCII guard, the
CFG-cache pin, the observation carry-over over a **one-file** corpus (0.05s),
and the leaf-refusal cross-check (0.26s):

```
tests/test_observation_classes.py, gated out:  16 passed, 1 skipped in 0.39s
tests/test_observation_classes.py, gate set :  17 passed in 2.70s
full suite with this task    : 912 passed, 1 skipped in 41.14 / 41.74s
full suite without this file : 896 passed             in 40.81 / 40.90s
bare (no corpus env vars)    : 832 passed, 81 skipped in  7.41s
```

so the standing cost is **~+0.4s**, and the standing headroom lever is
unchanged and untouched (`tests/test_behaviour_probe.py::
test_corpus_behaviour_matches`, ~10s setup).

**This is a deliberate departure from `test_footprint.py`'s 0.9s regeneration,
which the coordinator ruled stays in the suite. The difference is the number,
not the principle**, and it is recorded at the test, in the ratchet script and
in `tests/conftest.py`'s terminal-summary docstring — the last because the new
skip is the one skip a missing-corpus banner does not explain.

The job itself (`PYLUADEC_CORPUS_DIR=... uv run python
scripts/observation_classes.py`) measures **2.4–2.8s** wall, dominated by
lifting all 1944 protos (1.09s, the same cost `footprint_dump.py` pays) plus
the 229-file behaviour probe (0.47s with 8 threads) and the channel dataflow
(0.33s on warm CFGs).

---

## 9. What Tasks 7 and 8 inherit

1. **The class boundary is the corpus's own module boundary** (§3.3). Task 7
   can treat every `OPTION_CALLEES` entry as an oracle over a small domain
   because each one is a Class-2 proto in `snr_common.lua` that Task 8 owns.
2. **Class 1 is not one-shot** (§6.4 i). 113/113 poll their option channel in
   a loop. Task 7's driver needs a per-iteration schedule, not a single
   assignment.
3. **Task 8's cut exists on the original side for all 19 poll protos, on our
   side only where we certify** (§5.5). The 17 that ship fallback need a
   reconstruction produced for the purpose.
4. **`neither` is a statement about a proto's own body, not about its
   interaction** (§3.4), and `protos_reaching_poll` is a floor (331 published,
   390 measured with upvalue edges). Closing that gap is a bounded, named
   piece of work.
5. **Three protos are over budget and are exactly the ones the product model
   describes worst** (§6.4 iii).

---

## 10. Numbers that did not reproduce, and things I got wrong

| figure | as carried in | measured | why |
|---|---|---|---|
| "~20 leaf refusal sites" | the brief | **36** | §2.1; 20 is the `mismatch`-own subset, 32 the naive prefix definition |
| `input_space`, block-local | my own first implementation | wrong on **110/162** | §6.3; `footprint.py`'s "dataflow buys 0" does not transfer to comparison sites |
| `choice-branch` drivable 111/113 | my own first run | **110/113** | same |
| corpus-wide ≤ 4096: 1941/1944 | my own first run | **1940/1944** | same |
| `input_space` is per-call for Class 1 | my own first docstring | **per-iteration**, 113/113 | §6.4 i |
| `neither` = "no interaction channel" | my own first docstring | **9 of 38 have one** | §3.4 |
| `protos_reaching_poll` = 331 | this task's own summary | floor; **390** with upvalue edges | §3.4 |
| naive dataflow terminates | my own assumption | **it does not** | §6.3, `snr_common.lua:main_72` |
| id-keyed CFG cache is safe | my own first implementation | **it is not** unless the entry pins the proto | a scratch census that loaded one file at a time crashed with `IndexError` inside `GETGLOBAL` handling, indexing one proto's constants with another's operand |

Figures from earlier tasks that **did** reproduce this session: 229 files /
1944 protos; 48 non-`L3` rows splitting `structure` 21 / `mismatch` 22 /
`reconstruct` 5; the behaviour probe's 132 `CAP` / 97 `OK` / 398196 events and
its 101 `vms` / 26 `wait` / 5 `pressButton` dominant-callee split; 19
`pressButton` protos over 9 files; `corpus/ledger.jsonl` byte-identical after
a full `run_corpus.py`.

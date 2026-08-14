# `corpus/pred_repairs/` — repaired predecessor scripts (derived artifacts)

**These files are NOT produced by this repository's decompiler, and they are
NOT byte-faithful to the original bytecode.** They are hand-edited copies of
five files from the shipped localization, repaired at the meta level (by reading
the original bytecode and understanding the code) to fix six specific,
identified behavioural defects — the six that M6's cross-corpus adjudication
(`docs/reports/m6-cross-corpus.md` §3) confirmed. **Nothing else about them was
reconciled**, and none of them is byte-faithful to the original bytecode
anywhere; that was never attempted and is not claimed.

## Provenance

| | |
|---|---|
| upstream | `$PYLUADEC_PRED_CORPUS_DIR` (`/Users/fotile96/Zndnovel/lua_scripts`), the predecessor project's decompiled output — recompiled, repacked into a PSP ISO and played to completion by a human |
| ground truth used for every repair decision | the original Lua 5.1 bytecode in `$PYLUADEC_CORPUS_DIR`, read through `build/luac_sz4 -l -l` and this repo's `lift`/`cfg` layers |
| upstream is untouched | yes — `$PYLUADEC_PRED_CORPUS_DIR` is an input to `tests/test_predcorpus.py`'s census, to `corpus/observation/classes.json` and to `scripts/cross_corpus.py`, and must stay reproducible |

Why the files live under `corpus/`: this directory already holds versioned
corpus-derived data that no pipeline code reads at import time (`corpus/golden/`,
`corpus/observation/`, `corpus/ledger.jsonl`). These files are the same kind of
thing — committed data with a stated provenance, consumed by nothing in
`src/pyluadec/`. No test in the default suite reads them, and nothing in
`scripts/` or `tests/` references this directory except one comment in
`scripts/cross_corpus.py` saying it is *not* an input.

### A note on pc numbering

Defects 1–2 below quote **cfg block ids and `luac`-listing pcs as the first
repair round recorded them**. Defects 3–6 quote **1-based listing pcs**
(`build/luac_sz4 -l -l`, where `JMP` at pc *n* with `sBx = s` targets
`n + 1 + s`). `docs/reports/m6-cross-corpus.md` §3 states the same instructions
0-based, so every pc there is one less than the pc here. The instructions
themselves reproduced exactly; only the origin differs.

## What was repaired

### 1. `snr_music.lua` — the music gallery's poll loop

The predecessor's `main` is straight-line: it has the six `pressButton` call
sites the original has, but no `while` at all, and the loop tail is written out
twice as the `else` arms of two nested `if`s. Entering the gallery therefore
polled once and fell straight through to
`run(cGetFileName("script", "snr_mainmenu"))`.

Three edits, against the original's `main_3` (377 instructions, back edge
`365 → 12`, single loop exit at `330 → 331`):

1. `while true do` inserted before the first `pressButton` (original pc 12),
   `end` restored before the exit code (original pc 369).
2. the `CROSS` handler's `if not (v7 == "") then … end` given the `else break end`
   the original's pc 331 jump is (`EQ 1 R0 ""` / `JMP → 369`).
3. the two duplicated loop tails replaced by one unconditional tail at the end
   of the loop body, which is where the original has it (pc 355–367).

### 2. `snr_common.lua` — `systemConfig.ConfigMain` (`main_76_2`)

Both defects are verbatim the historical checkpoints in the predecessor
project's `pyluadec/DEBUG_KEY_SEQUENCE_HARNESS.md`.

1. **The `break` fired unconditionally.** In the original, the state
   *(cursor row == 3) ∧ (memoryFlag == true)* leaves the `CIRCLE` handler with
   no `keyPlaySE` and no break (original pcs 83, 85–88 → pc 94). The
   predecessor put the `break` outside `if not (memoryFlag == true)`, so all
   three arms reached the loop exit. The `break` is now inside each arm that
   the original breaks from.
2. **A same-frame hang.** In the `firstFragment == 1` arm the same state fell
   through an empty `else` straight back to the `while` test with no `wait`,
   where the original reaches the loop tail's `wait(1)`. Both such arms now
   call `wait(1)`.

### 3. `snr_mainmenu.lua` — four deleted menu-refresh gates (`main_7`)

The menu-rebuild `for` loop has a two-way branch on each entry. The original
gates it (pcs 207–222 at the first of four sites): *hide* iff
`(i == v1.novel and systemSave.novelFlag ~= true) or
(i == v1.music and systemSave.musicFlag ~= true)`; the hide arm is
`layerVisible(menu + i, false)` at 223–229 followed by `JMP → 253` (the
`FORLOOP`), the show arm is `layerAlpha(…, 0)` / `layerVisible(…, true)` /
`layerMoveAlpha(…, 100, 30)` at 231–252.

The predecessor has **no gate**: its hide block falls straight through into the
show block, so both mutually exclusive arms run and a locked entry is faded
back in with no intervening `wait`. Measured over the whole proto, original
vs predecessor: `GETGLOBAL systemSave` **24 → 16**, `GETTABLE novelFlag`
**12 → 8**, `GETTABLE musicFlag` **8 → 4** — four gate sites deleted
(original pcs 207, 745, 1280, 1825).

Repair: at each of the four sites the bare `else` becomes
`elseif (i4 == v1.novel and not (systemSave.novelFlag == true)) or
(i4 == v1.music and not (systemSave.musicFlag == true)) then`, and a new bare
`else` is inserted after the `layerVisible(…, false)` line. **8 lines
changed/added, nothing else touched, no line re-indented.** All three global-read
counts are restored to the original's, and each repaired loop body is
instruction-for-instruction identical to the original's 190–253 modulo register
numbers (the predecessor holds the loop bounds in extra locals) and a uniform
pc offset.

### 4 & 5. `snr_graphic.lua` and `snr_memory.lua` — a dropped `or` disjunct (`main_4`)

Identical shape in both files, at two sites each. The original's RIGHT handler
is `if c == 3 or c == 6 or c == 9 then A else B end` and its LEFT handler is
`if c == 1 or c == 4 or c == 7 then A' else B' end`. The predecessor drops the
middle disjunct in each (`== 6` and `== 4`), writes `A` out twice, and lets both
copies **fall through into `B`**:

| | original | predecessor | repaired |
|---|---|---|---|
| `snr_graphic` `EQ`-vs-numeric census | 12 tests in 4 chains of 3 | **10** in chains of 2/3/2/3 | **12**, chains and polarities as the original |
| `snr_memory` same | 12 | **10** | **12** |
| preds of the RIGHT handler's `A` entry (`snr_graphic`) | `{118, 121, 123}` | `{137}` | `{137, 140, 142}` |
| preds of its `B` entry | `{124}` | `{140, 173, 205}` | `{143}` |

So in the shipped build `c == 6` (resp. `c == 4`) ran **`B` only** where the
original runs `A` only — the page never turned — and `c == 3`/`c == 9`
(resp. `1`/`7`) ran **`A` then `B`**.

Repair: in each of the four handlers the outer test becomes the three-way `or`
chain, the duplicated inner copy of `A` is deleted, and `B` becomes the `else`
arm. `snr_graphic.lua` −50/+21 lines, `snr_memory.lua` −51/+21; ignoring
whitespace those fall to **−33/+4** and **−34/+4** (the duplicated `A` copies
and the two rewritten conditions), so the rest is the `else`-arm bodies
re-indented one level — 19 lines in each file. That re-indentation is the one
place these repairs churn lines they did not have to; it was taken because the
affected lines are pure arithmetic with no string constant, so no stage-3
translation overlay hunk can sit on them.

### 6. `snr_common.lua` — a retry `while` that became an `if` (`main_75`, `autoSystemSave`)

The original's `O159 JMP sBx=-73 → 87` is the proto's **only** back edge:
`wait(1); while succeedLoadSystemdata() == false do <re-prompt>; wait(1) end;
applySystemdata()`, with `preds(O87) = {86, 159}`. Each of the loop body's four
confirm-dialog arms is `if <dialog>() == true then runAutoSave() else break end`
— all four false-jumps (`O105`, `O120`, `O136`, `O151`) target `O160`, the loop
exit.

The predecessor has **no back edge at all**: `preds(P92) = {91}`, its tail
`P160–162 wait(1)` falls through into `P163 applySystemdata`, and its four
false-jumps target its own `wait(1)` rather than a loop exit. On repeated load
failure the original re-prompts indefinitely; the shipped build proceeds after
one pass.

Repair (+9/−2 lines): `v1 = succeedLoadSystemdata()` / `if v1 == false then`
becomes `while succeedLoadSystemdata() == false do`, and each of the four
`if v1 == true then runAutoSave() end` gains `else break`. Verified: the
repaired proto has back edge `170 → 93` with `preds(93) = {92, 170}`, and all
four false-jumps now target `171`, the loop exit.

**Independent corroboration for this one, and only this one.** `main_75`
certifies `L3` in `corpus/ledger.jsonl`, so this repository's own structured
print of it *is* byte-faithful to the original bytecode, and it reads
`while succeedLoadSystemdata() == false do … else break … wait(1) end
applySystemdata()` — the same structure. (Reproduce with
`structure.structured._print_proto_body(proto, depth=1, upval_names=())`.)
The other three protos repaired here are `L1` with
`refusal_reason = "structure: … if targets out of range"`, and all four ship
fallback text, so for those the only reference used was the original bytecode.

## What was **not** repaired

- **The duplicated loop tail in `main_76_2`** (predecessor source lines
  3991–4030 and 4033–4072). It is one loop with four back edges, not a defect,
  and neither repair required touching it. Left alone.
- **The residual fall-through divergence it causes.** Because the tail is
  duplicated rather than shared, the states repaired above reach a `wait(1)`
  but do **not** reach that frame's `CROSS`/`UP`/`DOWN` polls, which the
  original does. Measured with `check_config_gates.lua`: the repaired file's
  trace for that state is 20 events against the original's 23 — exactly the
  three missing polls — with the same return value and the same exit frame.
- **The `cursor row == 6` arm under `firstFragment == 1`.** It likewise skips
  the tail, but it calls `wait(5)` on its own, so it neither hangs nor changes
  an outcome; measured cost is one extra `pressButton` poll per activation
  (45 events against the original's 44). Unchanged from the predecessor.
- **Every other divergence in these five files.** In `snr_mainmenu.lua:main_7`
  alone, the predecessor turns all 20 of the original's `TESTSET` into
  `TEST` + `MOVE` (`or`-idiom rewriting) and carries 120 `MOVE` against the
  original's 28; the repair leaves those counts exactly where the predecessor
  had them. `snr_graphic`/`snr_memory` keep the predecessor's rendering of
  `v4 = (a == b)` as an `if`/`else`. None of this was touched.
- **Byte fidelity, anywhere.** Instruction counts after repair, original →
  predecessor → repaired: `snr_mainmenu:main_7` 2182 → 2266 → **2334**;
  `snr_graphic:main_4` 769 → 848 → **810**; `snr_memory:main_4` 482 → 533 →
  **493**; `snr_common:main_75` 162 → 165 → **173**. Two of the four moved
  *closer* and two moved *further*; the repairs buy behaviour, not bytes.
  For the first two defects, `tests/test_predcorpus.py`'s substantive-mismatch
  count was **unchanged** (`snr_music.lua` 23, `snr_common.lua` 351), because
  `_cmp` records at most one `code` mismatch per proto.

## Re-verifying

All five files compile with this repo's oracle (`pyluadec.oracle.compile_source`,
i.e. the vendored `luac_sz4`). Sizes, measured 2026-08-14:

| file | source | bytecode (`strip=True`) |
|---|---|---|
| `snr_music.lua` | 9 608 B | 5 769 B |
| `snr_common.lua` | 168 366 B | 128 114 B |
| `snr_mainmenu.lua` | 57 897 B | 19 192 B |
| `snr_graphic.lua` | 26 626 B | 14 419 B |
| `snr_memory.lua` | 16 908 B | 9 213 B |

### The three standalone drivers

None is collected by pytest and none adds any suite cost. Each exists because
`scripts/probe_keyseq.py` stubs the very gate that selects the arm under test,
so its traces are byte-identical across all three files and prove nothing there.

`check_config_gates.lua` — the `ConfigMain` checkpoints (defect 2).

```sh
./build/lua_sz4 corpus/pred_repairs/check_config_gates.lua \
    <chunk.lua|chunk-bytecode> <firstFragment> <memoryFlag> \
    "1,DOWN;7,DOWN;13,CIRCLE;tail=CROSS"
```

| `firstFragment` | `memoryFlag` | original | predecessor | repaired |
|---|---|---|---|---|
| 0 | true | `OK` returns −1, 23 events | `OK` returns **3**, 17 events | `OK` returns −1, 20 events |
| 1 | true | `OK` returns −1, 23 events | **HANG** (frame stuck, budget exhausted) | `OK` returns −1, 20 events |
| 0 | false | `OK` returns 3, 17 events | identical | identical |
| 1 | false | `OK` returns 3, 17 events | identical | identical |

`check_menu_gates.lua` — the four menu gates (defect 3). It gives
`gameSave.startMenuState`, `systemSave.libFlag` and the two flags concrete
values, because with the standard stub `gameSave.startMenuState == 0` is false
against a proxy and the menu loop never runs at all.

```sh
./build/lua_sz4 corpus/pred_repairs/check_menu_gates.lua \
    <chunk> <novelFlag> <musicFlag> "181,DOWN;186,CIRCLE;tail=NONE"
```

Measured 2026-08-14 over the first 4000 recorded events, for all four
`(novelFlag, musicFlag)` settings: **original vs predecessor differs; original
vs repaired is byte-identical.** With both flags false the counts are
`layerVisible(_,false)` / `layerVisible(_,true)` / `layerAlpha` /
`layerMoveAlpha` = 6/2/2/6 for the original, **8/4/4/8** for the predecessor
(the hidden `novel` and `music` rows are faded straight back in), and 6/2/2/6
for the repaired file.

`check_autosave_retry.lua` — the retry loop (defect 6). It scripts
`succeedLoadSystemdata`'s return sequence and the dialog answers.

```sh
./build/lua_sz4 corpus/pred_repairs/check_autosave_retry.lua \
    <chunk> <false_runs> <answers>
```

Measured 2026-08-14 over a 16-cell matrix (`false_runs ∈ {0,1,3,6}` ×
`answers ∈ {true, false, "true,false", "true,true,false"}`): 10 cells agree on
all three files, 6 diverge original-vs-predecessor, and the repaired file is
**byte-identical to the original in all 16**.

* `false_runs=3, answers=true` — original: 4 `succeedLoadSystemdata` calls,
  3 `runAutoSave`, 3 `wait(1)`, then `applySystemdata` (17 events);
  predecessor: 2 calls, 2 saves, `applySystemdata` (11 events).
* `false_runs=3, answers=true,false` (the `break`) — original goes straight to
  `applySystemdata` after the declined dialog (9 events); predecessor runs an
  extra `wait(1)` first (10 events).

### Defects 4 and 5 need no new driver

`scripts/probe_keyseq.py`'s own harness reaches them; its three *authored*
`snr_graphic` specs do not, because they never move the cursor onto a multiple
of 3. Measured 2026-08-14 with these specs, original vs predecessor vs repaired:

```sh
./build/lua_sz4 scripts/probe_keyseq.lua <chunk> "<spec>"
```

| spec | original vs predecessor | original vs repaired |
|---|---|---|
| `tail=RIGHT` | differ at line 211 (`snr_graphic`) / 185 (`snr_memory`) | **identical** |
| `k=1,RIGHT;k=8,RIGHT;k=15,RIGHT;tail=LEFT` | differ at line 207 / 181 | **identical** |
| `k=1,DOWN;k=8,RIGHT;k=15,RIGHT;k=22,RIGHT;tail=LEFT` | differ at line 119 / 116 | **identical** |
| `k=1,DOWN;k=8,DOWN;tail=RIGHT` | differ at line 241 / 215 | **identical** |
| `k=1,DOWN;k=8,R;k=50,LEFT;tail=NONE` | differ at line 201 / 175 | **identical** |
| `tail=LEFT`, `tail=UP`, `tail=DOWN` | identical (arm never entered) | identical |

The last spec isolates the LEFT handler's dropped `== 4`: `DOWN` moves the
cursor 1 → 4, `R` turns the page without touching either `or` chain, and `LEFT`
at cursor 4 on page 2 is exactly the missing disjunct. The original runs the
page-back animation there; the predecessor does not.

## Note on content

These are game scripts and contain Japanese text in their string constants
(sizes in the table above). They are the deliverable, so the text is present
here; no analysis, diagnostic, driver output or prose in this repository quotes
it — the drivers record string arguments as `s<len>` and nothing else.

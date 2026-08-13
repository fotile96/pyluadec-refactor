# `corpus/pred_repairs/` — repaired predecessor scripts (derived artifacts)

**These files are NOT produced by this repository's decompiler, and they are
NOT byte-faithful to the original bytecode.** They are hand-edited copies of
two files from the shipped localization, repaired at the meta level (by reading
the original bytecode and understanding the code) to fix two specific,
identified behavioural defects. Nothing else about them was reconciled.

## Provenance

| | |
|---|---|
| upstream | `$PYLUADEC_PRED_CORPUS_DIR` (`/Users/fotile96/Zndnovel/lua_scripts`), the predecessor project's decompiled output — recompiled, repacked into a PSP ISO and played to completion by a human |
| ground truth used for every repair decision | the original Lua 5.1 bytecode in `$PYLUADEC_CORPUS_DIR`, read through `build/luac_sz4 -l -l` and this repo's `lift`/`cfg` layers |
| upstream is untouched | yes — `$PYLUADEC_PRED_CORPUS_DIR` is an input to `tests/test_predcorpus.py`'s census and to `corpus/observation/classes.json`, and must stay reproducible |

Why the files live under `corpus/`: this directory already holds versioned
corpus-derived data that no pipeline code reads at import time (`corpus/golden/`,
`corpus/observation/`, `corpus/ledger.jsonl`). These files are the same kind of
thing — committed data with a stated provenance, consumed by nothing in
`src/pyluadec/`. No test in the default suite reads them.

## What was repaired

### `snr_music.lua` — the music gallery's poll loop

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

### `snr_common.lua` — `systemConfig.ConfigMain` (`main_76_2`)

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
- **Everything else.** Neither file is byte-faithful to the original bytecode,
  and no attempt was made to make it so. Against the original,
  `tests/test_predcorpus.py`'s substantive-mismatch count is **unchanged** by
  these repairs (`snr_music.lua` 23, `snr_common.lua` 351).

## Re-verifying

Both files compile with this repo's oracle (`pyluadec.oracle.compile_source`,
i.e. the vendored `luac_sz4`).

`check_config_gates.lua` is a standalone driver for the `ConfigMain`
checkpoints; it exists because `scripts/probe_keyseq.py` stubs
`gameSave.tutorial.firstFragment` and `memoryFlag`, which are exactly the two
gates that select the arms under test — all five of that harness's `snr_common`
sequences produce byte-identical traces for the original, the predecessor and
the repaired file, so it cannot see either defect. It is not collected by
pytest and adds no suite cost.

```sh
./build/lua_sz4 corpus/pred_repairs/check_config_gates.lua \
    <chunk.lua|chunk-bytecode> <firstFragment> <memoryFlag> \
    "1,DOWN;7,DOWN;13,CIRCLE;tail=CROSS"
```

Measured 2026-08-13 with that sequence (cursor walked to row 3, `CIRCLE`
there), `<chunk>` being the original bytecode / the predecessor source / this
directory's repaired source:

| `firstFragment` | `memoryFlag` | original | predecessor | repaired |
|---|---|---|---|---|
| 0 | true | `OK` returns −1, 23 events | `OK` returns **3**, 17 events | `OK` returns −1, 20 events |
| 1 | true | `OK` returns −1, 23 events | **HANG** (frame stuck, budget exhausted) | `OK` returns −1, 20 events |
| 0 | false | `OK` returns 3, 17 events | identical | identical |
| 1 | false | `OK` returns 3, 17 events | identical | identical |

For `snr_music.lua`, `scripts/probe_keyseq.py`'s two authored sequences give
byte-identical traces between the original bytecode and the repaired source
(42 polls over 8 frames / 542 events, and 228 polls / `CAP` at 3001 events);
the predecessor gives 6 polls on one frame, 161 events, on both.

## Note on content

These are game scripts and contain Japanese text in their string constants
(`snr_music.lua` 9 608 bytes, `snr_common.lua` 168 205 bytes). They are the
deliverable, so the text is present here; no analysis, diagnostic or prose
output in this repository quotes it.

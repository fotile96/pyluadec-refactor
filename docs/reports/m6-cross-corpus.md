# M6 cross-corpus report

This file collects the raw per-file evidence for M6's cross-corpus work.
Section 1 is M6 task 2's deliverable (plumbing + first corpus-wide parity
census against the predecessor's human-verified output); later M6 tasks
append their own sections below it. **This is evidence, not a gate** -- the
task's assertions live in `tests/test_predcorpus.py`; this file exists so the
per-file numbers behind those assertions are inspectable without re-running
anything.

**Milestone closed 2026-08-14. Read §6 first** -- it is the summary of record
(exit clauses one by one, the six defects, where the decompiler ended up, the
three spec decision-log rows, the deferred minors' disposition, and the
figures from earlier sections that did not reproduce at the wrap). Sections 1
to 5 are each a task's evidence **as it stood when that task closed**, kept
that way on purpose; where a later task moved one of their numbers, §6.6 or a
dated note at the number itself says so.

## 1. Predecessor-corpus parity census (task 2)

> **Round 1 correction (2026-08-13).** The first version of this section
> pinned `total_substantive = 4163` / `total_paths = 1443`. Both were
> inflated by a strip-mode bug: the predecessor side was compiled
> unconditionally unstripped while the true original is always stripped, so
> every one of the 260 upvalue-bearing protos in the corpus picked up a
> manufactured `upvalues`-tuple-length mismatch that had nothing to do with
> what the two chunks compute. Fixed by matching
> `verify.certify.certify_l3`'s own precedent (`strip=not
> carries_debug(original)`) — see `predcorpus.load_pred_proto`'s `strip`
> parameter. Corrected figures below; the `0/229` "no perfect
> recompilation" headline is unchanged by the fix (re-checked explicitly).
> This section also adds a second, coarser-grained measure
> (`substantive_signals`) the round-1 review asked for — see "Granularity"
> below.

**What this measures.** `PYLUADEC_PRED_CORPUS_DIR` (conventionally
`/Users/fotile96/Zndnovel/lua_scripts`) holds 229 Lua **source** files: the
predecessor project's (`/root/pyluadec`) decompiled output, which was
recompiled, repacked into a PSP ISO, and played through to completion by a
human, over a dozen human-in-the-loop fix rounds. It is the only artifact in
this project's reach with real semantic backing. This census asks, file by
file: does the predecessor's recompiled bytecode agree with the TRUE
original bytecode (`PYLUADEC_CORPUS_DIR`, the same 229 files by basename)
that this project also ingests?

**Method**, implemented in `src/pyluadec/predcorpus.py` and
`tests/test_predcorpus.py::_census_one`:

1. Ingest the original bytecode file directly (`ingest.load_file`) -- no
   decompilation involved, this is the ground truth this project already
   trusts as a faithful parse of the PSP ISO's shipped bytecode.
2. Compile the predecessor's source file with the same oracle this project
   uses everywhere else (`oracle.compile_source`), **in the same strip mode
   as the original** (`predcorpus.load_pred_proto(..., strip=not
   carries_debug(original))`, matching `verify.certify.certify_l3`'s
   precedent -- both sides then carry, or both omit, the same debug tables,
   so a length comparison on `upvalues`/`locvars` stays a statement about
   the two chunks' *shape*, not about which one happened to be compiled
   `-s`). Every file in this corpus takes the `strip=True` branch:
   `carries_debug` is `False` for all 1944 original protos (documented in
   CLAUDE.md and re-affirmed by this task). Then ingest the result
   (`predcorpus.load_pred_proto`).
3. Compare the two proto trees' **shapes**: `pipeline.walk_proto_paths`'s
   `main`/`main_0`/`main_0_1` path convention, computed independently on
   each tree (`predcorpus.tree_paths`), must produce the identical ordered
   path list (`tree_match`).
4. If the shapes match, run `verify.normalize.compare_protos(original,
   predecessor, level=1)` -- the L3.1 strip-lineinfo rung, unmodified,
   already used everywhere else in this project's certification path --
   and count the resulting `Mismatch` list, **excluding** the debug-only
   fields the brief named: `source`, `lineinfo`, `locvars`,
   `linedefined`, `lastlinedefined` (the brief's fifth name,
   `upvalue_names`, does not exist as a `Mismatch.field` string; the real
   field, `upvalues`, is deliberately **not** excluded -- see the
   `DEBUG_FIELDS` comment in `test_predcorpus.py` for why folding it in
   would have hidden the round-1 bug's symptom rather than fixed its
   cause). `level=1` and `level=0` are numerically inert on this corpus
   after the strip-mode fix (checked directly, both before and after); the
   code calls `level=1` because that is what this prose describes, not
   because the choice is free in general -- a corpus where the original
   carried real debug info would make the two diverge.

Nothing here modifies `NORMALIZATIONS`, `LADDER_VERSION`, `compare_protos`,
or `_cmp` -- certification logic is read-only in this task; only what is FED
to it (the predecessor compile's strip mode) changed.

### Granularity: three measures, not one

`_cmp` (verify/normalize.py) records **at most one** `Mismatch` for `code`,
`maxstacksize`, `nups`, `numparams`, `is_vararg`, `upvalues` — but **one per
differing index** for `constants` (`"const[3]"`, `"const[17]"`, ...). Raw
`substantive_mismatches` therefore mixes a coarse per-proto flag with a fine
per-element count: a proto whose only disagreement is a dozen differing
string constants outweighs one whose entire `code` array diverges, even
though the latter is the "bigger" disagreement in every functional sense.
Three figures are reported per file and corpus-wide, and none of them alone
is "the" answer:

- **`substantive_mismatches`** — raw `Mismatch` count (debug fields
  excluded). Dominated by files with many differing constants.
- **`substantive_paths`** — distinct proto paths carrying >=1 substantive
  mismatch. Closer to uniform (a proto counts once regardless of how many
  fields disagree) but does not distinguish "one field differs" from
  "every field differs".
- **`substantive_signals`** (new, round 1) — distinct `(path, category)`
  pairs, where `_field_category` collapses every `"const[i]"` (and
  `"constants.len"`) into one `"constants"` bucket per proto. Each semantic
  dimension (code / constants / maxstacksize / nups / numparams / is_vararg
  / upvalues) counts once per proto no matter how many elements within it
  differ -- the uniform measure the round-1 review asked for.

**Measured 2026-08-13**, macOS arm64, against
`PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/script_to_decompile` and
`PYLUADEC_PRED_CORPUS_DIR=/Users/fotile96/Zndnovel/lua_scripts` (full pass
~0.7s cold):

| metric | value |
| --- | --- |
| files | 229/229 |
| compile_ok | **229/229** -- every predecessor source file compiles under `luac_sz4` |
| tree_match | **229/229** -- every predecessor recompilation has the identical proto-tree shape (same path set, same order) as the true original bytecode |
| files with 0 substantive mismatches | **0/229** -- unchanged by the strip-mode fix (re-checked explicitly); no file's predecessor recompilation is byte-for-byte semantically identical to the original at rung 1 |
| total substantive mismatches (sum) | **3903** (was 4163 before the strip-mode fix, −6.25%) |
| total distinct substantive paths (sum) | **1433** (was 1443) |
| total substantive signals (sum, uniform measure) | **2989** |
| substantive mismatches per file: min / median / max | 3 / 8 / 351 (`snr_common.lua`) |
| substantive signals per file: min / median / max | 3 / 8 / 215 (`snr_common.lua`) |

No compile failure and no tree-shape mismatch occurred anywhere in the
corpus -- both were open questions going in (the brief explicitly warned
against forcing a tidy result), and the honest finding is that this
particular census surface came back clean on both. The interesting variation
is in the third question, substantive mismatch count: it is **never zero**,
ranging from 3 (many small `snr_crd_*.lua` files, each a handful of protos)
up to 351 (`snr_common.lua`, the largest file at 147 protos). The 13 files
measured before this task's implementation (see task brief) reproduced
exactly against the round-0 measurement; the round-1 strip-mode fix then
moved every file with `nups > 0` protos downward by exactly one
`Mismatch` per such proto (corpus-wide: 4163 − 3903 = 260, matching the
260 upvalue-bearing protos exactly).

### Full per-file table (all 229 files, sorted by filename)

`protos` is the original bytecode's proto count (`tree_match` guarantees the
predecessor side has the same count in the same order). `compiled` and
`tree_match` are `yes` everywhere in this run, included per-row rather than
omitted so a future re-run's diff against this table is a plain text diff.

| file | protos | compiled | tree_match | substantive_mismatches | substantive_paths | substantive_signals |
|---|---:|:---:|:---:|---:|---:|---:|
| config.lua | 1 | yes | yes | 15 | 1 | 3 |
| snr_common.lua | 147 | yes | yes | 351 | 100 | 215 |
| snr_crd_0.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_1.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_10.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_100.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_101.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_102.lua | 7 | yes | yes | 8 | 4 | 8 |
| snr_crd_103.lua | 14 | yes | yes | 12 | 6 | 12 |
| snr_crd_104.lua | 18 | yes | yes | 10 | 5 | 10 |
| snr_crd_105.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_106.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_107.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_108.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_109.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_11.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_110.lua | 8 | yes | yes | 10 | 5 | 10 |
| snr_crd_111.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_112.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_113.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_114.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_115.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_116.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_117.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_118.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_119.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_12.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_120.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_121.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_122.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_123.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_124.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_125.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_126.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_127.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_128.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_129.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_13.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_130.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_131.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_132.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_133.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_134.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_135.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_136.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_137.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_138.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_139.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_14.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_140.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_141.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_142.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_143.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_144.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_145.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_146.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_147.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_148.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_149.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_15.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_150.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_151.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_152.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_153.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_154.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_155.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_156.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_157.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_158.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_159.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_16.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_160.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_161.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_162.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_163.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_164.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_165.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_166.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_167.lua | 9 | yes | yes | 10 | 5 | 10 |
| snr_crd_168.lua | 5 | yes | yes | 8 | 4 | 8 |
| snr_crd_169.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_17.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_170.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_171.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_172.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_173.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_174.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_175.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_176.lua | 8 | yes | yes | 10 | 5 | 10 |
| snr_crd_177.lua | 10 | yes | yes | 8 | 4 | 8 |
| snr_crd_178.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_179.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_18.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_180.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_181.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_182.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_183.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_184.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_185.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_186.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_187.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_188.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_189.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_19.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_190.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_191.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_192.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_193.lua | 7 | yes | yes | 10 | 5 | 10 |
| snr_crd_194.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_195.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_2.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_20.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_21.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_22.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_23.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_24.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_25.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_26.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_27.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_28.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_29.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_3.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_30.lua | 11 | yes | yes | 10 | 5 | 10 |
| snr_crd_31.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_32.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_33.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_34.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_35.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_36.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_37.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_38.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_39.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_4.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_40.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_41.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_42.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_43.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_44.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_45.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_46.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_47.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_48.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_49.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_5.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_50.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_51.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_52.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_53.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_54.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_55.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_56.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_57.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_58.lua | 8 | yes | yes | 10 | 5 | 10 |
| snr_crd_59.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_6.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_60.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_61.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_62.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_63.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_64.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_65.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_66.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_67.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_68.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_69.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_7.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_70.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_71.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_72.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_73.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_74.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_75.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_76.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_77.lua | 5 | yes | yes | 8 | 4 | 8 |
| snr_crd_78.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_79.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_8.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_80.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_81.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_82.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_83.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_84.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_85.lua | 5 | yes | yes | 8 | 4 | 8 |
| snr_crd_86.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_87.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_88.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_89.lua | 11 | yes | yes | 10 | 5 | 10 |
| snr_crd_9.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_90.lua | 5 | yes | yes | 10 | 5 | 10 |
| snr_crd_91.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_92.lua | 4 | yes | yes | 8 | 4 | 8 |
| snr_crd_93.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_94.lua | 4 | yes | yes | 6 | 3 | 6 |
| snr_crd_95.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_96.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_97.lua | 2 | yes | yes | 3 | 2 | 3 |
| snr_crd_98.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_crd_99.lua | 3 | yes | yes | 6 | 3 | 6 |
| snr_e1_10_f.lua | 6 | yes | yes | 8 | 4 | 8 |
| snr_e1_10_s.lua | 58 | yes | yes | 56 | 28 | 56 |
| snr_e2_10_f.lua | 72 | yes | yes | 62 | 31 | 62 |
| snr_e2_10_s.lua | 26 | yes | yes | 33 | 14 | 29 |
| snr_fragment_main.lua | 5 | yes | yes | 19 | 5 | 11 |
| snr_graphic.lua | 6 | yes | yes | 153 | 6 | 18 |
| snr_lib.lua | 3 | yes | yes | 4 | 2 | 4 |
| snr_mainmenu.lua | 9 | yes | yes | 29 | 6 | 15 |
| snr_memory.lua | 6 | yes | yes | 38 | 6 | 18 |
| snr_music.lua | 5 | yes | yes | 23 | 4 | 11 |
| snr_novel.lua | 15 | yes | yes | 78 | 14 | 38 |
| snr_s0_10_f.lua | 16 | yes | yes | 16 | 8 | 16 |
| snr_s1_10_f.lua | 16 | yes | yes | 18 | 9 | 18 |
| snr_s1_10_s.lua | 82 | yes | yes | 273 | 73 | 173 |
| snr_s2_10_f.lua | 18 | yes | yes | 20 | 10 | 20 |
| snr_s2_10_s.lua | 118 | yes | yes | 314 | 78 | 188 |
| snr_s3_10_fa.lua | 16 | yes | yes | 18 | 9 | 18 |
| snr_s3_10_fb.lua | 12 | yes | yes | 14 | 7 | 14 |
| snr_s3_10_fc.lua | 20 | yes | yes | 18 | 9 | 18 |
| snr_s3_10_s.lua | 98 | yes | yes | 290 | 77 | 181 |
| snr_s4_10_fa.lua | 36 | yes | yes | 34 | 17 | 34 |
| snr_s4_10_fb.lua | 34 | yes | yes | 32 | 16 | 32 |
| snr_s4_10_s.lua | 98 | yes | yes | 303 | 81 | 190 |
| snr_s5_10_f.lua | 16 | yes | yes | 18 | 9 | 18 |
| snr_s5_10_s.lua | 88 | yes | yes | 112 | 40 | 87 |
| snr_s6_10_f.lua | 14 | yes | yes | 16 | 8 | 16 |
| snr_s6_10_s.lua | 37 | yes | yes | 104 | 27 | 63 |
| snr_s7_10_f.lua | 103 | yes | yes | 96 | 48 | 96 |
| snr_s8_10_f.lua | 32 | yes | yes | 34 | 17 | 34 |
| snr_s8_10_s.lua | 12 | yes | yes | 42 | 11 | 26 |
| snr_story_main.lua | 5 | yes | yes | 14 | 5 | 11 |

**Regenerating this table**: `PYLUADEC_CORPUS_DIR=... PYLUADEC_PRED_CORPUS_DIR=... uv run python tests/test_predcorpus.py` prints the same rows (plus totals) in fixed-width form; `tests/test_predcorpus.py::test_corpus_wide_parity_census` pins the headline totals (`compile_ok == 229`, `tree_match == 229`, `total_substantive == 3903`, `total_paths == 1433`, `total_signals == 2989`) as a regression check.

<!-- Later M6 tasks append their own `## N. ...` sections below this line. -->

## 2. Cross-corpus scan, first full pass (task 5)

> **Round 1 correction (2026-08-14).** The first version of this section
> reported **5** fingerprint divergences over 6 files and claimed that three
> of the four `candidate-defect` rows "agree on `cfg_reachable` and differ
> only on `cfg_all`". Both were wrong, and the second one was wrong in the way
> that matters — `snr_common.lua` and `snr_s2_10_s.lua` carry **call-site**
> differences (CALL 16→27 and 93→97), so grouping them with
> `snr_mainmenu.lua` (CALL 271→271, textbook hoisting) treated the queue's
> weakest row as equivalent to one carrying the same signature as the known
> defects. The deeper problem underneath: `SEMANTIC_SENSITIVE_THRESHOLDS` has
> **no control-flow term**, so the arm was silent on purely control-flow
> defects — the class of *both* hand-found defects — and caught `snr_music.lua`
> by luck. The queue criterion now carries a control-flow disjunct
> (§2.4), the queue is **16 files / 18 rows**, `first_cut` separates
> reachable-CFG and call-target evidence from `cfg_all`-only evidence
> (§2.2), and the fingerprint arm has its own non-vacuity proof *and* a pinned
> statement of what it cannot see (§2.6). Everything below is re-measured
> after those changes.

Harness: `scripts/cross_corpus.py` (job) + `tests/test_cross_corpus.py` (24
smoke tests, 0.40–0.45 s, corpus-gated). Command and wall-clock:

```
PYLUADEC_CORPUS_DIR=... PYLUADEC_PRED_CORPUS_DIR=... \
  uv run python scripts/cross_corpus.py --arm all
```

**3.59 / 3.88 s** for all three arms over all 229 files (two round-1 runs,
2026-08-14, host: macOS arm64 / Darwin 24.2.0; 4.40–4.58 s user + 2.89–3.20 s
system at 200–202 % CPU, i.e. the 8-way probe pool; the round-0 runs were
3.51 / 3.51 / 3.60 s). Exit code
**1**, correctly: 18 divergences exist and `PRED_PINS` is empty by design at
this task, so `adjudicate_pins` reports all 18 as `unexpected`. Task 6
adjudicates them into pins.

### 2.1 Headline

| arm | agree | divergent | probe-error | what it compares |
|---|---:|---:|---:|---|
| `fingerprint` | 213/229 | 16 | 0 | `score_protos` over both proto trees, statically |
| `state` (L1.5) | 229/229 | 0 | 0 | global-table delta after the chunk body runs |
| `behaviour` (L1.75) | 227/229 | 2 | 0 | event trace of invoking the chunk's global functions |

**18 rows over 16 distinct files.** First-cut triage (mechanical rules in
`cross_corpus.first_cut`; **triage labels, not verdicts**): **10
`candidate-defect`, 1 `probable-artifact`, 7 `suspect`**.

**Engine-artifact rate, first measurement.** The risk section predicted noise
from running the predecessor's text through a stub environment it was never
exercised against. Measured: **1 of 18 rows** (6 %) falls to the mechanical
artifact rule, and **0 of 229 files** failed to compile, load or probe on any
arm. That is far less noise than the prediction allowed for. §2.5 is the
counterweight: both dynamic arms have shallow reach, so they produce few rows
of any kind, and a low artifact rate is not the same claim as good coverage.

### 2.2 The divergence queue

Evidence is opcode/pc/event-shape summaries, ASCII identifiers and SHA-256
prefixes only (`build/cross-corpus/queue.json` carries the same rows
machine-readably; it is a job product and is **not** committed).

`reach`/`all` triples are `(blocks, edges, back-edges)` from
`verify.semantic_score._cfg_shape` — the predecessor project's own **crude
shape hash**, faithfully reproduced (block breaking after terminators and test
ops; back edge = `succ_block_id <= block_id`, an ordering heuristic, not a
dominance test). Read them as a hash that changed, not as a dominance claim.

The evidence pair names each file's **worst flagged path**; a file's other
flagged paths are in `detail.flagged_paths` (round-1 fix — `snr_common.lua`
alone has **18** flagged paths, and `main_23` `(7,6,0)→(3,2,0)`, `main_59`
`(5,5,1)→(6,6,1)` and `main_76_8` `(25,24,0)→(21,20,0)` were previously
invisible behind `main_76_2`).

| file | arm | first cut | original | predecessor |
|---|---|---|---|---|
| `snr_music.lua` | behaviour | candidate-defect | `L1 hdr\|CAP\|3001 sha=a4e1d9425fdf` | `L1 hdr\|OK\|94 sha=22694cadd5c2` |
| `snr_common.lua` | fingerprint | candidate-defect | `main_76_2 code=174 reach=(4, 3, 0) all=(73, 71, 1) reads=27 calls=16` | `main_76_2 code=279 reach=(4, 3, 0) all=(103, 101, 10) reads=42 calls=27` |
| `snr_fragment_main.lua` | fingerprint | candidate-defect | `main_1 code=891 reach=(24, 25, 2) all=(136, 137, 2) reads=155 calls=62` | `main_1 code=919 reach=(45, 46, 2) all=(136, 137, 2) reads=155 calls=62` |
| `snr_graphic.lua` | fingerprint | candidate-defect | `main_4 code=769 reach=(4, 4, 1) all=(185, 188, 7) reads=67 calls=63` | `main_4 code=848 reach=(4, 4, 1) all=(182, 185, 7) reads=67 calls=65` |
| `snr_memory.lua` | fingerprint | candidate-defect | `main_4 code=482 reach=(4, 4, 1) all=(142, 141, 2) reads=41 calls=42` | `main_4 code=533 reach=(4, 4, 1) all=(140, 139, 3) reads=41 calls=44` |
| `snr_music.lua` | fingerprint | candidate-defect | `main_3 code=377 reach=(16, 16, 1) all=(112, 111, 2) reads=20 calls=23` | `main_3 code=407 reach=(16, 15, 0) all=(112, 111, 1) reads=22 calls=26` |
| `snr_novel.lua` | fingerprint | candidate-defect | `main_7 code=96 reach=(14, 14, 1) all=(40, 38, 1) reads=11 calls=11` | `main_7 code=107 reach=(15, 15, 1) all=(44, 42, 3) reads=11 calls=11` |
| `snr_s2_10_s.lua` | fingerprint | candidate-defect | `main_60 code=1182 reach=(4, 3, 0) all=(259, 258, 3) reads=157 calls=93` | `main_60 code=1200 reach=(4, 3, 0) all=(263, 262, 7) reads=161 calls=97` |
| `snr_s4_10_s.lua` | fingerprint | candidate-defect | `main_58 code=1372 reach=(4, 3, 0) all=(402, 401, 3) reads=147 calls=114` | `main_58 code=1379 reach=(4, 3, 0) all=(404, 403, 3) reads=147 calls=116` |
| `snr_story_main.lua` | fingerprint | candidate-defect | `main_1 code=1009 reach=(24, 25, 2) all=(136, 137, 2) reads=189 calls=78` | `main_1 code=1045 reach=(45, 46, 2) all=(136, 137, 2) reads=189 calls=78` |
| `snr_novel.lua` | behaviour | probable-artifact | `L15 C\|comLayerLoadFalse\|2args sha=73a98ce48474` | `L15 C\|comLayerLoadFalse\|2args sha=48e2cf828d42` |
| `config.lua` | fingerprint | suspect | `main code=57 reach=(1, 0, 0) all=(1, 0, 0) reads=24 calls=0` | `main code=71 reach=(1, 0, 0) all=(1, 0, 0) reads=38 calls=0` |
| `snr_crd_102.lua` | fingerprint | suspect | `main_3 code=150 reach=(4, 3, 0) all=(14, 13, 1) reads=22 calls=27` | `main_3 code=149 reach=(4, 3, 0) all=(15, 14, 2) reads=22 calls=27` |
| `snr_lib.lua` | fingerprint | suspect | `main_1 code=226 reach=(11, 11, 1) all=(55, 55, 2) reads=36 calls=26` | `main_1 code=230 reach=(11, 11, 1) all=(53, 53, 2) reads=36 calls=26` |
| `snr_mainmenu.lua` | fingerprint | suspect | `main_7 code=2182 reach=(7, 6, 0) all=(624, 635, 16) reads=291 calls=271` | `main_7 code=2266 reach=(7, 6, 0) all=(628, 639, 16) reads=283 calls=271` |
| `snr_s3_10_s.lua` | fingerprint | suspect | `main_59 code=1292 reach=(4, 3, 0) all=(335, 334, 4) reads=160 calls=109` | `main_59 code=1297 reach=(4, 3, 0) all=(337, 336, 6) reads=160 calls=109` |
| `snr_s5_10_s.lua` | fingerprint | suspect | `main_46 code=830 reach=(4, 3, 0) all=(151, 150, 5) reads=153 calls=90` | `main_46 code=808 reach=(4, 3, 0) all=(146, 145, 3) reads=153 calls=90` |
| `snr_s7_10_f.lua` | fingerprint | suspect | `main_52 code=95 reach=(6, 5, 0) all=(22, 20, 1) reads=19 calls=19` | `main_52 code=98 reach=(6, 5, 0) all=(24, 22, 3) reads=19 calls=19` |

**Which term fired, per queued file** (measured; `cfgR` = some path's
`cfg_reachable < 1.0`, `cfgA` = `cfg_all < 1.0`, `call` = `call_targets < 1.0`,
`sens` = `drift_type == "semantic_candidate"`):

| file | sens | cfgR | cfgA | call | flagged paths | first cut |
|---|:-:|:-:|:-:|:-:|---:|---|
| `snr_common.lua` | ✓ | ✓ | ✓ | ✓ | 18 | candidate-defect |
| `snr_music.lua` | ✓ | ✓ | ✓ | ✓ | 1 | candidate-defect |
| `snr_story_main.lua` | | ✓ | ✓ | ✓ | 2 | candidate-defect |
| `snr_fragment_main.lua` | | ✓ | ✓ | | 2 | candidate-defect |
| `snr_novel.lua` | | ✓ | ✓ | | 4 | candidate-defect |
| `snr_graphic.lua` | | | ✓ | ✓ | 3 | candidate-defect |
| `snr_memory.lua` | | | ✓ | ✓ | 3 | candidate-defect |
| `snr_s2_10_s.lua` | ✓ | | ✓ | ✓ | 1 | candidate-defect |
| `snr_s4_10_s.lua` | | | ✓ | ✓ | 1 | candidate-defect |
| `config.lua` | ✓ | | | | 1 | suspect |
| `snr_mainmenu.lua` | ✓ | | ✓ | | 1 | suspect |
| `snr_crd_102.lua` | | | ✓ | | 1 | suspect |
| `snr_lib.lua` | | | ✓ | | 1 | suspect |
| `snr_s3_10_s.lua` | | | ✓ | | 1 | suspect |
| `snr_s5_10_s.lua` | | | ✓ | | 3 | suspect |
| `snr_s7_10_f.lua` | | | ✓ | | 1 | suspect |

Rows with mechanical detail worth carrying into Task 6:

* **`wait` +2 is a recurring call-target signature.** Exactly three protos in
  the corpus gain calls to the global `wait` (constant fingerprint
  `str:4:daaad336276d`): `snr_music.lua:main_3` (+2, alongside one upvalue
  target), `snr_common.lua:main_76_2` (+2, alongside `pressButton`
  `str:11:01b5742a1082` **+3** and three further global targets) and
  `snr_s2_10_s.lua:main_60` (+2, alongside two upvalue targets). **Two of the
  three are the hand-confirmed defects**, which is what makes the third worth
  adjudicating first.
* **`snr_mainmenu.lua:main_7` is the weakest row in the queue**, and the
  round-0 text was wrong to group it with `snr_s2_10_s.lua`. Measured
  components `{cfg_all 0.0, opcode_family 0.9667, global_reads 0.9861}` —
  `call_targets` and `cfg_reachable` are both exactly **1.0**, CALL is
  **271 → 271**, and the **complete** opcode delta (round-2 correction — the
  first version listed five of the ten entries and read as if it were the whole
  delta) is: ADD 80→90, EQ 170→154, GETGLOBAL 291→283, GETTABLE 380→364,
  GETUPVAL 273→265, JMP 291→311, MOVE 28→120, SUB 24→34, TEST 0→20,
  TESTSET 20→0. Textbook hoisting (fewer GETGLOBAL/GETTABLE/GETUPVAL, far more
  MOVE) plus `or`-chain re-expression (TESTSET → TEST + JMP).
* **`snr_common.lua:main_76_2`**, measured components
  `{cfg_all 0.0, opcode_family 0.7682, global_reads 0.7826, call_targets 0.7442,
  call_shapes 0.7442}`; **CALL 16 → 27**.
* **`snr_s2_10_s.lua:main_60`**, measured components
  `{cfg_all 0.0, opcode_family 0.9924, global_reads 0.9874, call_targets 0.9789,
  call_shapes 0.9789}`; **CALL 93 → 97**.
* **`config.lua`** (`suspect`). The two chunks' opcode multisets differ in
  **exactly one opcode**: `GETGLOBAL` 24 → 38 (+14). `NEWTABLE` 3, `SETTABLE`
  26, `SETGLOBAL` 3, `RETURN` 1 are identical on both sides, and the CFG shape
  is identical (one block, no edges). That is the signature of a value re-read
  from `_G` where the original held it in a register, not of a different
  computation — but it is 14 extra global reads and is left unadjudicated.
* **`snr_novel.lua`** (behaviour, `probable-artifact`). The two traces are the
  **same multiset of 43 lines** (41 events plus header and trailing blank) once
  `getobjname` nouns are erased — a reordering plus one naming difference. Both
  classes are already pinned on our own side with instruction-level evidence
  (`probe_behaviour.EXPECTED_DIVERGENCE`: `NEWTABLE` size hint → different node
  array → different `next()` order; and
  `probe_global_state.EXPECTED_ERROR_NAME_DIVERGENCE`: `ldebug.c` names a value
  by the bytecode shape that produced it). **See §2.9.3 for what that rule can
  hide.**

### 2.3 Are the two known defects visible? One each way — and that is the finding

M6 task 4 found two defects by hand. They land in **different arms**, and
neither arm sees both:

| defect | fingerprint | state | behaviour |
|---|:---:|:---:|:---:|
| `snr_music.lua` — `main`'s poll loop is gone | **yes** | no | **yes** |
| `snr_common.lua:main_76_2` — unconditional `break` / empty `else` | **yes** | no | **no** |

The behaviour arm's miss on `snr_common.lua` is **not** an agreement. It is a
silent arm, and the harness says so: that file's original-side run ends in
`CAP` (3000-event budget), it defines **79** function-valued globals, and the
capped run invokes **1** of them (`reach = truncated:1/79`). `main_76_2` sits
under `systemConfig` (subproto 76 of the root, read off the root's
`CLOSURE`/`SETGLOBAL` pair), which is never invoked. Corpus-wide the same
measurement is 307 function-valued globals defined, 229 invoked — and **all
78** never-invoked ones are in `snr_common.lua`.

This is the same blindness the brief records for `scripts/probe_keyseq.py`,
arrived at by a different route (there: the stubs neutralise the gates that
select the broken arm; here: the event budget stops before the function is
reached). The instrument that *does* see it is the **static** one.

**But "static" is a reach claim, not a coverage claim.** The fingerprint arm
*inspects* all **1944** proto occurrences; what it can *detect* in them is
bounded by §2.6's measurements — it is blind to statement deletion and to a
dropped call argument. Do not read "all 1944 protos" as "everything in them".

### 2.4 The fingerprint queue criterion

> a fingerprint row is queued iff `FileScore.hard_issues` is non-empty, or
> `FileScore.drift_type == "semantic_candidate"`, or **any proto path's
> `cfg_reachable`/`cfg_all` component is below 1.0**.

NOT `score < 1.0`. Measured over all 229 files: **92 score exactly 1.0**, 137
do not, minimum **0.890039**, median **0.999753**; status `pass` 226 / `warn` 3
/ `fail` 0; **zero** files carry a `hard_issue`. Task 2's census already
established that byte-level divergence is the normal state on this pair (0/229
byte-faithful, 3903 substantive mismatches over 1433 paths), so a
`score < 1.0` criterion would queue 60 % of the corpus and carry no signal.

The third disjunct is the round-1 repair (§2.6). Without it the queue is 5
files; with it, 16.

### 2.5 Reach: what "agree" is worth, per arm

| arm | reach census (229 files) |
|---|---|
| `fingerprint` | `static=229` — every proto compared, nothing executed |
| `state` | `ran=224`, `raised=5` |
| `behaviour` | `complete=96`, `truncated=132`, `silent=1` |

* **`state` (L1.5) agreement is nearly vacuous on this corpus.** The compared
  payload has a median length of **22 characters**, **227 of 229** are ≤ 40,
  and **222 of 229** are exactly `string:main=<function>`; only
  `snr_common.lua` (59512) and `snr_lib.lua` (50) are longer. `229/229 agree`
  on this arm should be read as "nothing contradicted", not as evidence of
  equivalence. **Round-1 correction:** the round-0 text reported this arm's
  reach as `load-error=5` unqualified. That was a misnomer — **no corpus file
  fails to load**; those 5 files load and then raise at run time, so the token
  is now `raised`, and `load-fail` (a chunk the loader refuses) occurs on 0 of
  229.
* **`behaviour` (L1.75) agreement covers a prefix on 132 of 229 files.** Those
  runs end at the 3000-event cap. Total recorded events: **398196** original
  side, **395289** predecessor side (the 2907 gap is `snr_music.lua` alone:
  3001 vs 94). **Round-1 correction:** the reach token now carries the
  invocation gap (`truncated:1/79`), because the old status-derived token
  measured out as a pure function of the header (`truncated` ⟺
  `status != "OK"` on 132/132) and left `snr_common.lua` indistinguishable from
  the other 131 capped files. `silent` now means `invoked == 0` and fires on
  **1** file — `config.lua`, which executes 3 events, defines **0**
  function-valued globals and invokes **0**, and which the old rule labelled
  `complete` because `defined and not invoked` short-circuits on
  `defined == 0`. The old `silent` branch fired on **0 of 229** files.
* **`fingerprint` has full static reach and zero dynamic reach.** It is the
  only arm that looked at `snr_common.lua:main_76_2` at all.

### 2.6 Non-vacuity proofs — one per arm that has a threshold

**Behaviour arm** (committed in `eedb4bf`, before the first full scan).
`tests/test_cross_corpus.py::test_synthetic_numeric_mutation_is_caught_by_the_behaviour_arm`
copies `snr_crd_0.lua` from the predecessor corpus into a pytest `tmp_path`,
replaces its unique `vms(104,` with `vms(999,` — one numeric call argument —
and requires `kind == "divergent"`. `test_unmutated_control_agrees` is the
control half. Deliberately a **non-structural** mutation: both sides keep
status `OK` and **292 events**, and the differing event's *shape* is identical
(`C|vms|3args` either way, because the shape drops argument values — they can
be game text). So the mutation is caught only by the whole-trace byte compare.
`test_the_sha_discriminator_in_behaviour_evidence_is_load_bearing` uses the
same fixture to show why the evidence pair carries a SHA-256 prefix: without
it the two halves would be equal and `adjudicate_pins`' `moved` check would be
blind to any change that moves only argument values.

**Fingerprint arm** (round 1 — it had none, and measured it would have failed
one). Same file, same temp-dir technique, three mutations at one call
statement:

| mutation | file score | `drift_type` | control-flow term | queued by round-0 criterion | queued now |
|---|---:|---|:-:|:-:|:-:|
| none (control) | 1.000000 | structural_only | — | no | no |
| wrap in `if 1 == 2 then … end` | **0.854665** | structural_only | `cfg_reachable` < 1 | **no** | **yes** |
| delete the call statement | 0.999077 | structural_only | — | no | **no** |
| drop one call argument | 0.999574 | structural_only | — | no | **no** |

The guarded call is a **purely control-flow** defect — the class of *both*
hand-found defects — and at 0.854665 it scores *below* `snr_music.lua`'s
queued 0.890039 while the round-0 criterion called it `agree`. That is what
the control-flow disjunct fixes
(`test_fingerprint_arm_catches_a_synthetic_control_flow_defect`; neuter proof:
delete the two `below(...)` terms from `_fingerprint_one`'s `flagged` and that
test alone goes red).

The last two rows are **pinned as blind spots of the fingerprint arm**
(`test_fingerprint_arm_is_blind_to_statement_level_edits`, parametrised): a
deleted statement and a dropped argument leave every control-flow component at
1.0 and every sensitivity threshold unbreached. No threshold on
`semantic_score._cfg_shape` reaches a statement-level edit.

> **Round-2 correction — the third false behavioural sentence this section has
> carried.** It previously read "the behaviour arm catches the deletion;
> **nothing in this harness catches the dropped argument**". Measured
> 2026-08-14: **the behaviour arm catches both.** Deletion diverges at the
> header (`OK|292` vs `OK|291`); the dropped argument keeps both sides at 292
> events and diverges at `L16`, `C|comPoseLoad|1args` vs
> `C|comPoseLoad|0args`, `multiset_equal_after_objname = False`. The claim was
> believed only because the test asserted the behaviour arm inside
> `if mutation == "delete":`, so the other parameter was never measured. The
> assertion is now unconditional for both parameters, and each has its own
> route pinned (event-count change vs. argument shape at a fixed position).
>
> **What is true:** the **fingerprint arm** is blind to both mutations; the
> **harness** is blind to neither. The error was in the conservative direction
> — it understated reach — but Task 6 would have read it as a limit that does
> not exist.

Two further instrument checks:
`test_a_candidate_that_does_not_load_is_never_reported_as_agreement` (the L1.5
gate's historical failure — it once returned `""` for every probe-side failure
and compared equal on all 229 files), `test_assert_ascii_actually_refuses`
(round-1 pin: the red-line guard's raise was replaceable with `pass` and the
file stayed green), and `test_predecessor_corpus_is_never_written_to` (round-1
widening: a whole-directory size/mtime snapshot, not just the 3 smoke files).

### 2.7 Near-miss census — what sits just below the queue line

Over the **213 non-queued files** (**1230** proto occurrences): **212 protos in
121 files carry at least one sub-1.0 component, and every one of them is
`opcode_family` — nothing else.** Lowest non-queued proto score
**0.988235**, and **28 protos tie at it**, across 4 files —
`snr_s1_10_s.lua` ×14, `snr_s6_10_s.lua` ×9, `snr_s8_10_s.lua` ×4,
`snr_e2_10_s.lua` ×1. (Round-2 correction: the first version named
`snr_e2_10_s.lua:main_2_0` "and four `snr_s1_10_s.lua` siblings", which was a
transcription of the first five rows of a sorted list, not the tie.)

Stated the other way, and this is the useful form: **outside the queue there
is not one control-flow difference, not one call-target or call-shape
difference, not one global-read or global-write difference, not one
return-arity difference and not one constant difference in the entire corpus.**
The residual is exclusively opcode-family drift — register allocation and
expression shape.

That is a stronger statement than round 0 could make, and it is a *direct
consequence* of the control-flow disjunct: the three files round 0 left just
outside the line on a reachable-CFG difference (`snr_fragment_main.lua:main_1`
and `snr_story_main.lua:main_1`, both `(24,25,2) → (45,46,2)`;
`snr_novel.lua:main_7` `(14,14,1) → (15,15,1)`) and the four left outside on a
CALL-count difference (`snr_graphic:main_4` 63→65, `snr_memory:main_4` 42→44,
`snr_s4_10_s:main_58` 114→116, `snr_story_main:main_3` 78→79) are now **all
inside it**. The `call_targets = 0.9767` vs a 0.97 threshold near-miss on
`snr_memory:main_4` — queued or not on the third decimal — no longer decides
anything, because that file is queued on its control-flow term.

The census does **not** say the corpus is otherwise clean; it says this
instrument sees nothing else. §2.6's blind spots are the bound.

**And one clause of it cannot fail, by construction — read the rest.** The
queue criterion *is* "any path with `cfg_reachable`/`cfg_all` below 1.0", so
"no control-flow difference outside the queue" is a tautology, not a
measurement. The same holds for `return_arity` and for the below-threshold
parts of `global_reads`/`call_targets`, which `drift_type` already queues. The
**genuinely informative** content of §2.7 is the three bands the criterion does
*not* cover:

| band | outside the queue |
|---|---|
| `0.97 ≤ call_targets < 1.0` (below 1.0, above the sensitivity threshold) | **0** |
| `0.995 ≤ global_reads < 1.0` | **0** |
| numeric-only constant differences (`_has_sensitive_constant_diff` skips `num:` keys) | **0** |

Those three being empty is a real finding. Corpus-wide there are **7** paths
with `call_targets < 1.0` at all, **5** of them in the `[0.97, 1.0)` band, and
every one of the 7 is inside the queue on another term.

### 2.8 Suite-cost attribution

`tests/test_cross_corpus.py`: **24 tests**, 0.40–0.45 s measured standalone
(round 0: 16 at 0.28–0.33 s; round 1: 23 at 0.37–0.46 s).

**Within-batch A/B** (the only comparable form on this host), alternating
`--ignore=tests/test_cross_corpus.py` with the full suite, twice each in one
batch. pytest-reported totals:

| | run 1 | run 2 | mean |
|---|---:|---:|---:|
| round 0, without (901 tests) | 44.85 s | 44.68 s | 44.77 s |
| round 0, with (917) | 45.15 s | 45.44 s | 45.30 s |
| round 1, without (917) | 44.67 s | 44.58 s | 44.63 s |
| round 1, with (940) | 44.56 s | 44.91 s | 44.74 s |
| round 2, without (917) | 44.69 s | 44.03 s | 44.36 s |
| round 2, with (941) | 44.56 s | 44.84 s | 44.70 s |

Deltas: round 0 **+0.53 s**, round 1 **+0.11 s**, round 2 **+0.34 s**. **None
of the three is resolvable against this host's run-to-run noise, and the
variation between them is the proof** — the `with` and `without` arms overlap
in every round (round 2: `without` spans 44.03–44.69, `with` spans
44.56–44.84). The honest bound is therefore the standalone figure — **this
module costs at most ~0.45 s** — and most of that is absorbed by session
fixtures (`pred_corpus_dir`, the oracle compile memo) the suite already builds
for `test_predcorpus.py`. Round 0's +0.53 s was reported as if it were a
measurement of this module; it was a two-run mean of a noisy quantity.

**All of it is M6 formal-verification instrument cost** — the cross-corpus
scan harness and its non-vacuity proofs — and therefore inside the ~120 s
earmark rather than the old discipline. Nothing else was added. The 229-file
scan is a job (3.59–3.88 s) and is **not** in the suite.

### 2.9 Round-1 findings that change what "divergent" means for Task 6

#### 2.9.1 A fourth verdict is needed: `intentional-edit`

Task 6's pin vocabulary is `real-bug` / `suspect` / `probe-artifact`. **None of
them fits a difference the predecessor project put there on purpose**, and the
corpus contains at least one: the sole differing *string* constant corpus-wide
is a 24 B → 26 B ASCII font-asset path under `pgf/` in `snr_common.lua:main_83`
— the Japanese-font filename swapped for a Chinese-font one. That is the
localization doing its job. Calling it `real-bug` is false and calling it
`probe-artifact` is false; it needs its own verdict.

**Proposed:** `intentional-edit` — *the predecessor's text differs from the
original bytecode because a human changed it deliberately, and the change is
consistent with the localization's purpose.*

**Distinguishing evidence — four clauses, all runnable from this repo**
(round-2 tightening; the first version's third clause named "a corresponding
change in the shipped ISO's assets", which Task 6 cannot execute — no `.pgf`
and no ISO is reachable under either corpus root, verified 2026-08-14 — and
its "control flow identical" phrasing was loose enough to admit
`snr_mainmenu.lua`, which is compiler drift):

1. **Every structural component is exactly 1.0**: `cfg_reachable`, `cfg_all`,
   `call_targets`, `call_shapes`, `global_reads`, `global_writes`,
   `return_arity`.
2. **The numeric-constant multiset is identical**, and the only constant
   difference is in *string* constants, each of which is an asset path or
   identifier — never dialogue.
3. **The opcode delta is confined to register-shuffling opcodes** (`MOVE`,
   `LOADNIL`). No change to `CALL`, `GETGLOBAL`/`SETGLOBAL`, or any test or
   jump opcode.
4. **Corroboration is a documented decision in the localization project's own
   repository**, `/Users/fotile96/Zndnovel` — not an artifact nobody can open.

Measured against the instance, `snr_common.lua:main_83`: components below 1.0
are only `opcode_family` 0.991846 and `const_fingerprint` 0.992188 (clause 1
✓); numeric multiset identical, string difference exactly 1-for-1 and it is a
`pgf/` asset path (clause 2 ✓); opcode delta is exactly `LOADNIL` 0→1 and
`MOVE` 1→11 (clause 3 ✓); and `Zndnovel/CLAUDE.md:47` records the swap
explicitly — it states that these Lua files are decompiler output *that has
been hand-modified*, and that `snr_common.lua` has had font 0 replaced with
`pgf/LXGWWenKai-Regular.pgf` with the original Japanese-font line kept as a
comment (clause 4 ✓).

**And `snr_mainmenu.lua` falls out, as it must.** It has
`call_targets == cfg_reachable == 1.0` *and* a numeric-constant delta, so a
loose reading of the first version would have admitted it. Under the tightened
clauses it fails **1** (`global_reads` 0.9861) and fails **3** decisively (EQ
170→154, JMP 291→311, GETGLOBAL 291→283, GETTABLE 380→364, TESTSET 20→0,
TEST 0→20 — control-flow and global-access opcodes, not register shuffling).
Its verdict is compiler drift, not a deliberate edit.

#### 2.9.2 The census behind that claim is string-only, and other classes exist

Round 0 wrote "divergent ≠ defect by construction" on the strength of a
**string-constant** census. Two limits, both measured 2026-08-14:

* **Tighter than round 0 stated:** the constant multiset is identical *per
  file* across all 229 except `snr_common.lua` (1 orig-only, 1 pred-only) —
  not merely the corpus-wide set.
* **But numeric constants were never censused.** Doing so: **4 files** differ
  on the numeric-constant multiset (`snr_common.lua`, `snr_mainmenu.lua`,
  `snr_memory.lua`, `snr_music.lua`), all in the direction "predecessor has
  more"; and in **2** of them there are values present *only* on the
  predecessor side — `snr_memory.lua` {8.0} and `snr_music.lua` {4, 6, 7, 8, 9,
  12, 13, 14, 15, 16, 17, 18, 19}. The second is direct corroboration of the
  `snr_music.lua` defect: a run of consecutive integer literals is what an
  unrolled loop leaves behind.

So the "intentional edit" class is established for *strings*; for numbers the
census says the opposite — those differences look like defect residue, and
`snr_memory.lua` is now queued (on its control-flow term) where round 0 left it
out entirely.

#### 2.9.3 `_same_multiset` is over-broad, with a constructed instance

Swapping two adjacent side-effecting calls in a predecessor source —
`comEffectFadeOut(100)` and the `vms(...)` line after it in `snr_crd_0.lua`, in
a temp dir — yields `divergent` with `multiset_equal_after_objname == True`, so
the rule labels a genuine semantic change (the fade now runs *after* the line
displays) `probable-artifact`. The rule's two justifications are table
*iteration* order and error-message nouns; **neither covers intra-function
statement order**, and nothing in the rule distinguishes them. This is recorded
in `_same_multiset`'s docstring. It is tolerable only because the label is
triage and Task 6 adjudicates every row by hand — it would not be tolerable as
a filter that drops rows.

### 2.10 Two notes Task 6 should read before triaging

**(a) Prioritise the call-target rows above the reachability-only rows.**
`snr_fragment_main.lua:main_1` and `snr_story_main.lua:main_1` are labelled
`candidate-defect` on `cfg_reachable` **alone**. Measured 2026-08-14: their
`cfg_all` is identical `(136, 137, 2)` on both sides, `call_targets`,
`call_shapes`, `global_reads`, `global_writes`, `return_arity` and
`const_fingerprint` are all exactly **1.0**, and the entire opcode delta is
`LOADNIL` 0→1 with `MOVE` +27 (fragment) / +35 (story). Their whole label rests
on `cfg_reachable` going `(24,25,2) → (45,46,2)` — a *crude reachability walk*
that this same report tells you to "read as a hash that changed, not as a
dominance claim" (§2.2). Both files' profiles are, opcode for opcode, the same
`LOADNIL`+`MOVE` shape as `snr_common.lua:main_83`, whose verdict is
`intentional-edit`/drift.

Suggested triage order: the `wait`-bearing call-target rows
(`snr_s2_10_s.lua:main_60` first, since `snr_music` and `snr_common` are
already adjudicated), then the remaining call-target rows
(`snr_graphic`, `snr_memory`, `snr_s4_10_s`, `snr_story_main:main_3`), then the
reachability-only rows, then the `cfg_all`-only `suspect` rows.

**(b) Half of §2.7's headline is a tautology; the informative half is the
band table.** See §2.7 — "no control-flow difference outside the queue" cannot
fail, because the queue criterion is that difference. What is measured, and
what is worth knowing, is that the three bands the criterion does *not* cover
(`0.97 ≤ call_targets < 1.0`, `0.995 ≤ global_reads < 1.0`, numeric-only
constant differences) are all empty outside the queue.

## 3. Adjudication of the divergence queue (task 6)

Task 5 produced 18 divergence rows over 16 files and adjudicated none of them.
This section adjudicates **all 18**, with a verdict per row and instruction-level
evidence for each. The verdicts are committed as `cross_corpus.PRED_PINS`, so
`scripts/cross_corpus.py --arm all` now exits **0**: `adjudicate_pins` returns
three empty lists (`unexpected`, `moved`, `gone`) on every arm.

Command and wall-clock, re-measured this session (2026-08-14, host macOS arm64 /
Darwin 24.2.0): `uv run python scripts/cross_corpus.py --arm all`, **3.25 s**,
229 files, three arms. Every row below was re-derived from the two proto trees in
this session; nothing is carried over from task 5's text.

### 3.1 Headline: six shipped defects, four of them previously unknown

| | |
|---|---|
| rows adjudicated | **18 / 18** |
| `real-bug` | **6 rows / 5 files / 6 distinct defects** |
| `equivalent-transform` | 12 rows |
| `probe-artifact` | 0 rows |
| `intentional-edit` | 0 rows *as a row verdict* (1 path-level instance) |
| `suspect` | 0 rows |

M6 task 4 found two defects by hand before the scanner existed. The scan plus
this adjudication **confirms both and adds four more**, all in the shipped
localization:

| file / proto | defect | previously known |
|---|---|---|
| `snr_music.lua:main_3` | the gallery poll loop's back edge is gone | yes (task 4) |
| `snr_common.lua:main_76_2` | unconditional break, and a continue that skips the frame wait | yes (task 4) |
| `snr_mainmenu.lua:main_7` | **four progress gates deleted**; the two arms of the branch now both run | **no** |
| `snr_graphic.lua:main_4` | **an `or`-chain lost a disjunct and its `else` arm was un-nested** | **no** |
| `snr_memory.lua:main_4` | same shape as `snr_graphic:main_4` | **no** |
| `snr_common.lua:main_75` | **a retry `while` became an `if`** -- the proto has no back edge left | **no** |

`snr_common.lua` carries two of the six, so 6 defects live in 5 files and produce
6 rows (5 fingerprint, 1 behaviour).

### 3.2 The verdict vocabulary, and why it has five members

Task 5's plan named three verdicts (`real-bug`, `suspect`, `probe-artifact`) and
task 5's report proposed a fourth (`intentional-edit`). Adjudicating the rows
needed **five**. The vocabulary and its evidentiary requirements live in
`scripts/cross_corpus.py::VERDICTS`, next to the table that uses them; the two
additions:

* **`intentional-edit` — adopted, exactly as task 5 proposed, with all four
  clauses.** It applies to `snr_common.lua:main_83` and to nothing else in the
  corpus. It is **not** any row's verdict, because a row is a *file* and
  `snr_common.lua`'s file verdict is `real-bug`; §3.5 records it at path level.
* **`equivalent-transform` — added.** Neither `probe-artifact` (which asserts a
  *stub-environment* cause, and the fingerprint arm has no stub environment) nor
  `suspect` (which asserts the root cause is *not* established) is true of a
  divergence whose mechanism has been walked instruction by instruction and shown
  to preserve semantics. Using either would have been a false sentence about 12 of
  the 18 rows. Five mechanisms were found; they are enumerated in `VERDICTS`.

`suspect` ends at **0** rows. That is a claim about this queue, not a policy: the
verdict remains in the vocabulary and remains the honest answer when two stories
fit.

### 3.3 The full verdict table

`first cut` is `cross_corpus.first_cut`'s mechanical label; `verdict` is this
section's. The two vocabularies are not the same, so the useful comparison is by
bucket: of the 10 `candidate-defect` rows **5** are defects and **5** are
`equivalent-transform`; of the 7 `suspect` rows **1** is a defect and 6 are
`equivalent-transform`; the single `probable-artifact` row is
`equivalent-transform`.

| file | arm | first cut | verdict | mechanism |
|---|---|---|---|---|
| `snr_common.lua` | fingerprint | candidate-defect | **real-bug** | `EQ` polarity flip -> unconditional return; continue-to-loop-header skips `wait`; and, separately, a lost retry loop in `main_75` |
| `snr_graphic.lua` | fingerprint | candidate-defect | **real-bug** | `or`-chain disjunct dropped; `else` arm un-nested into fallthrough |
| `snr_mainmenu.lua` | fingerprint | **suspect** | **real-bug** | four `systemSave` gate blocks deleted; both arms run |
| `snr_memory.lua` | fingerprint | candidate-defect | **real-bug** | as `snr_graphic` |
| `snr_music.lua` | fingerprint | candidate-defect | **real-bug** | outer back edge absent; tail duplicated, neither copy loops |
| `snr_music.lua` | behaviour | candidate-defect | **real-bug** | same defect, dynamically: `CAP\|3001` vs `OK\|94` |
| `config.lua` | fingerprint | suspect | equivalent-transform | constructor lowering (3) |
| `snr_crd_102.lua` | fingerprint | suspect | equivalent-transform | dead store + dead escape jump (2, 5) |
| `snr_fragment_main.lua` | fingerprint | candidate-defect | equivalent-transform | test-polarity flip; sunk callee `GETGLOBAL` (5) |
| `snr_lib.lua` | fingerprint | suspect | equivalent-transform | `TESTSET` collapse (4) |
| `snr_s2_10_s.lua` | fingerprint | candidate-defect | equivalent-transform | tail duplication (1) |
| `snr_s3_10_s.lua` | fingerprint | suspect | equivalent-transform | dead escape jumps (2) |
| `snr_s4_10_s.lua` | fingerprint | candidate-defect | equivalent-transform | tail duplication (1) |
| `snr_s5_10_s.lua` | fingerprint | suspect | equivalent-transform | `elseif` arms fall through instead of jumping back |
| `snr_s7_10_f.lua` | fingerprint | suspect | equivalent-transform | dead escape jumps (2) |
| `snr_story_main.lua` | fingerprint | candidate-defect | equivalent-transform | test-polarity flip; tail duplication (1) |
| `snr_novel.lua` | fingerprint | candidate-defect | equivalent-transform | dead escape jumps; tail duplication; statically-true `TEST` drops |
| `snr_novel.lua` | behaviour | probable-artifact | equivalent-transform | constructor lowering (3) -> `pairs()` order permutation |

**What the disagreement means for the triage rules.** `first_cut`'s
`candidate-defect` bucket has 10 rows and 5 of them are real; its `suspect`
bucket has 7 rows and **1 of them is real** — `snr_mainmenu.lua`, which §2.10
explicitly told task 6 to rank *last*. The mechanical rules are a work-ordering
device and nothing more; on this corpus their precision is 5/10, and a reader who
had trusted the buckets and left `suspect` unopened would have shipped with one
of the six defects unfound.

§2.10's prioritisation advice was **partly wrong and worth recording as wrong**.
It was right that `snr_fragment_main:main_1` and `snr_story_main:main_1` are
low-value (both adjudicate to `equivalent-transform`, both on a `cfg_reachable`
change that is a test-polarity flip). It was wrong to rank `snr_mainmenu.lua`
below them.

### 3.4 The five defects, at instruction level

Evidence is pc/opcode/register and ASCII identifiers only. `O<n>` is an original
pc, `P<n>` a predecessor pc, and **this section numbers them from 0** — the pin
tables in `scripts/cross_corpus.py` and `scripts/loss_sweep.py` number from 1
(see §4.6), so the same instruction is one greater there. Every fact below was re-derived this session with
`scripts/cross_corpus.py`, `verify.semantic_score.collect_proto_signatures` and a
reachability walk over the decoded instruction stream. `EQ` semantics are
`lvm.c`'s: `if (equalobj(RK(B), RK(C)) == GETARG_A(i)) dojump`, i.e. the
*following* `JMP` is taken when equality equals `A`.

#### (1) `snr_music.lua:main_3` — the poll loop is gone (task 4's defect #1)

Original `main_3` has **two** negative-`sBx` jumps: `O328 JMP sBx=-6 -> 323` and
**`O367 JMP sBx=-357 -> 11`**. The second is the gallery's outer poll loop: the
whole body from `O11` re-executes. The predecessor's `main_3` has **one**
(`P346 JMP sBx=-6 -> 341`); no instruction in its 407 targets `P11`. Its tail is
duplicated instead — `P371-384` and `P385-397` are the same block twice — and
**neither copy loops**: `P384 JMP -> 398` is forward and `P397` falls through to
`P398`, which is `GETUPVAL`/`CALL` followed by
`run(cGetFileName("script", "snr_mainmenu"))` at `P400-405` and `RETURN`.

Dynamically the behaviour arm shows the same thing and is the reason this file
has **two** rows: the original's stubbed run polls until the 3000-event budget
(`CAP|3001`, 2502 `pressButton` and 417 `wait` events), the predecessor's returns
after **94** (6 `pressButton`, 1 `wait`, then `cInitGame`, `switchScreen`,
`cGetFileName`, `run`). The gallery falls straight back to the main menu.

#### (2) `snr_common.lua:main_76_2` — unconditional break, and a frame hang

Both of `DEBUG_KEY_SEQUENCE_HARNESS.md`'s recorded checkpoints for
`SystemConfig.ConfigMain`, confirmed:

* **"`break` must not be promoted to an unconditional `break`."** Original
  `O84 GETGLOBAL 'memoryFlag'`, `O85 EQ A=0` — the `JMP` at `O86` is taken when
  the value is **not** `true`, so the equal case falls to `O87 JMP -> 93` and
  **continues the poll loop**. Predecessor `P91 GETGLOBAL 'memoryFlag'`,
  `P92 EQ A=1` — the `JMP` at `P93` is taken when the value **is** `true`, and its
  target is `P277 RETURN A=1 B=2`. Both outcomes of the test now return: `P93 ->
  P277` on equal, `P94-97` (`keyPlaySE`) then `P98 -> P277` otherwise. The gate is
  gone.
* **"a no-state-change path must reach `wait(1)`."** The sibling site: original
  `O65 EQ A=0` falls through on equal to `O67 JMP -> 93`, and every original
  iteration reaches `O168 GETGLOBAL 'wait'` / `O169 LOADK 1` / `O170 CALL` before
  `O171 JMP sBx=-169 -> 3`. The predecessor's `P66 EQ A=1` sends the equal case to
  `P67 JMP -> 4` — the loop **header** — bypassing `P273-275`, its own `wait(1)`.
  Register 0, the loop's induction variable, is written exactly once in each proto
  (`O0` / `P0`), so `while R0 < 1` never terminates on its own: the path spins
  without yielding a frame.

#### (3) `snr_mainmenu.lua:main_7` — four progress gates deleted (new)

The original's menu loop body branches two ways. `O206-O221` is the gate:
`GETUPVAL`/`GETTABLE 'novel'`, `EQ`; `GETGLOBAL 'systemSave'`/`GETTABLE
'novelFlag'`, `EQ K[bool:true]`; the same pair for `'music'`/`'musicFlag'`. It
selects between `O222-O228` (`layerVisible(layerNumber.menu + i, false)`, followed
by **`O229 JMP -> 252`**, the `FORLOOP`) and `O230-O251`
(`layerAlpha(...,0)`, `layerVisible(...,true)`, `layerMoveAlpha(...,100,30)`).

The predecessor has **no gate at all**. `P215 LT A=0` sends `i >= menu.novel`
straight to `P230`, which is `layerVisible(..., false)` — and `P230-236` **falls
through** into `P237` (`layerAlpha`), `P244` (`layerVisible(..., true)`) and
`P251` (`layerMoveAlpha(...,100,30)`). The two mutually exclusive arms are now
concatenated, and the later `layerVisible(..., true)` overrides the earlier
`false` with no intervening `wait`.

The count, measured over the whole proto: `GETGLOBAL 'systemSave'` **24 -> 16**,
`GETTABLE 'novelFlag'` **12 -> 8**, `GETTABLE 'musicFlag'` **8 -> 4** — exactly
**four** gate sites deleted (`O206`, `O744`, `O1279`, `O1824`), each reading one
of each flag. (The fourth was written `O1810` until the M6 final review; that pc
is wrong under either base — 0-based `O1810` is the `JMP` at 1-based 1811,
1-based 1810 is an `LT`. Re-derived 2026-08-14: the four `GETUPVAL` /
`GETTABLE 'novel'` / `EQ` gate heads are at 1-based **207, 745, 1280, 1825**,
i.e. 0-based 206, 744, 1279, **1824**.) Menu entries the save data has not unlocked are faded in instead of
staying hidden.

This row's first cut was **`suspect`**, and §2.10 recommended ranking it last.

#### (4) `snr_graphic.lua:main_4` and (5) `snr_memory.lua:main_4` — a lost disjunct (new)

Identical shape in both files. The original's cursor handler is
`if c == 3 or c == 6 or c == 9 then A else B end`, compiled as three
`GETUPVAL`/`EQ` pairs. In `snr_graphic`: `O116 EQ A=1 K[3]` and `O119 EQ A=1
K[6]` jump to the `A` block at `O124`; `O122 EQ A=0 K[9]` jumps to `B` at `O160`
when **not** equal. `preds(O124) = {117, 120, 122}` — three ways in. `A` ends
`O158 CALL` / **`O159 JMP -> 212`**, which skips `B` entirely.

The predecessor tests **two** values: `P135 EQ A=1 K[3]` -> `P173`, `P138 EQ A=0
K[9]` -> `P205`. `preds(P205) = {139, 172, 204}`: the `B` block is reached by the
not-equal jump **and by the fall-out of both copies of `A`** (`P172 JMP -> 205`,
`P204` falling through). So:

* `c == 6` runs **`B` only**, where the original runs `A` only — the page never
  turns;
* `c == 3` and `c == 9` run **`A` then `B`**, where the original runs `A` only.

`snr_memory.lua` is the same, at `O117/O120/O123` -> `P136/P139`. Each file loses
the disjunct **twice**: the RIGHT handler drops `== 6` and the LEFT handler drops
`== 4` (`snr_graphic` `O230`, `snr_memory` `O231`). The full `EQ`-against-numeric
census per proto, original vs predecessor, is
`snr_graphic` `[(116,3),(119,6),(122,9),(183,3),(186,6),(189,9),(227,1),(230,4),(233,7),(259,1),(262,4),(265,7)]`
vs `[(135,3),(138,9),(228,3),(231,6),(234,9),(273,1),(276,7),(311,1),(314,4),(317,7)]`.

**Reachability of the dropped values is settled inside the predecessor itself**:
its own second chain (`P228/P231/P234`) still tests `== 6` on the *same* upvalue
index, and its fourth chain still tests `== 4`. The two chains are separated by
an `LE` on `cursor + 1` against another upvalue, which places no constraint on the
cursor modulo 3. The gained `CALL`s (`snr_graphic` 63 -> 65, `snr_memory` 42 -> 44,
both `U:8|args:4|rets:0`) are the duplicated `A` block, not new call sites.

#### (6) `snr_common.lua:main_75` — a retry `while` became an `if` (new)

The only proto in the corpus whose predecessor side has **no negative-`sBx`
instruction at all** where the original has one.

Original: `O83-85 wait(1)`; `O86 GETGLOBAL 'succeedLoadSystemdata'` / `O87 CALL`;
`O88 EQ A=0 C=K[bool:false]`, so `O89 JMP -> 159` (`applySystemdata()`) is taken
when the result is **not** `false`. On `false` the body `O90-O157` runs and ends
`O155-157 wait(1)`, **`O158 JMP sBx=-73 -> 86`** — back to the call. `preds(O86)
= {85, 158}`: a live loop header.

Predecessor: the same head (`P89-91 wait(1)`, `P92-93` the call, `P94 MOVE`,
`P95 EQ A=0 C=K[bool:false]`, `P96 JMP -> 162`), the same body, and then
`P159-161 wait(1)` **falling through to `P162 GETGLOBAL 'applySystemdata'`**.
`preds(P92) = {91}` — nothing loops back; `preds(P162) = {96, 161}`.

So a `while <call>() == false do ... end` retry became a single `if`. On repeated
failure the original re-prompts indefinitely; the shipped build proceeds after one
pass. This sits on a system-data load-failure path, which may never fire in normal
play — the verdict is about semantics, and the departure is provable.

**This is the row the instrument ranked worst.** `main_75`'s measured components
are `{cfg_all 0.0, opcode_family 0.9358}`: its **`cfg_reachable` scores exactly
1.0** even though the proto's only loop disappeared, because
`semantic_score._cfg_shape`'s reachability walk follows a block's terminator only
and never the conditional-skip edge of `EQ`/`LT`/`TEST`. It was queued as one of
`snr_common.lua`'s 18 flagged paths, ranked 9th of 18 by score.

### 3.5 `intentional-edit`: adopted, and it fits exactly one path

Task 5 proposed the verdict with four runnable clauses. **Adopted unchanged.**
Verified independently this session against `snr_common.lua:main_83`, the only
path in the corpus it fits:

1. `cfg_reachable (5,5,1) -> (5,5,1)`, `cfg_all (12,11,1) -> (12,11,1)`, and no
   `global_reads` / `global_writes` / `call_targets` / `call_shapes` /
   `return_arity` delta at all — all seven components exactly 1.0. ✓
2. Constant delta is exactly `str:24:0a5c2a0bd820 1->0`, `str:26:7d47f033614e
   0->1`. No numeric constant differs anywhere in the proto, and the one string
   that does is an asset path under `pgf/` — the Japanese font filename swapped
   for a Chinese one. Both appear as the second argument of `fontLoad` with first
   argument `num:0` (`O46` / `P48`); the sibling `fontLoad(1, ...)` at `O50` /
   `P52` is byte-identical. ✓
3. Opcode delta is `LOADNIL 0->1` and `MOVE 1->11`. No `CALL`, `GETGLOBAL`,
   `SETGLOBAL`, test or jump change. ✓
4. `/Users/fotile96/Zndnovel/CLAUDE.md:47` records the swap, and states these Lua
   files are hand-modified decompiler output. ✓

Corpus-wide corroboration re-measured this session: the string-constant multiset
differs in **exactly 1 of 229 files** (`snr_common.lua`, one original-only and one
predecessor-only entry) — so this is not one instance of a class, it is the whole
class.

It is **not a row verdict**, because a row is a file and `snr_common.lua`'s file
verdict is `real-bug`. A vocabulary member with no row is still load-bearing here:
without it, this path would have had to be called `equivalent-transform`, which is
false (the chunk loads a different font), or `real-bug`, which is worse.

### 3.6 The other twelve rows

All twelve are `equivalent-transform`. The mechanisms are listed in
`cross_corpus.VERDICTS`; what follows is what each row's proof turned on.

* **`config.lua`** — the sole opcode delta is `GETGLOBAL 24 -> 38`, and the
  `global_reads` delta is exactly two names, `+12` and `+2`, summing to the 14.
  The chunk is one straight-line block with **0 `CALL` instructions on both
  sides**, and each extra read is dominated by a `SETGLOBAL` of a value that came
  straight from a `NEWTABLE`; with no call in between, nothing can rebind the
  global. Constructor lowering.
* **`snr_lib.lua`** — `TESTSET 2 -> 0`, `MOVE 0 -> 6`. Both `TESTSET`s test a
  register loaded by the immediately preceding `LOADK` of a number, so the skip
  edge is dead and the instruction always means `R := <constant>`. Fewer blocks
  from *more* instructions, because `MOVE` does not split a block and `TESTSET`
  does.
* **`snr_s2_10_s.lua`** and **`snr_s4_10_s.lua`** — tail duplication, proven by
  the three-part test. `snr_s2_10_s:main_60`: original block `O541-549` has
  `preds {506, 508, 538}`; the predecessor emits it at `P540-548` (`preds {536}`)
  and `P549-557` (`preds {504, 506}`), the two copies are equal
  instruction-for-instruction modulo registers and equal to the original's, and
  the third apparent copy `P539` has `preds = []`. Same at the proto's second
  site. This is where the `wait` +2 signature comes from: the duplicated block
  contains one `wait` call each, so the *static* count rises while the dynamic
  count per path does not.
* **`snr_s3_10_s.lua`**, **`snr_s7_10_f.lua`**, **`snr_s5_10_s.lua:main_42/43`**,
  **`snr_novel.lua:main_7/main_12`**, **`snr_crd_102.lua`** — dead escape jumps.
  `luac` emits a jump after an `if ... then ... break end` whose `then` arm
  already ended in an unconditional jump; `luaK_patchlist` aims it at the loop
  header, and it is unreachable. Every one was confirmed with `preds = []`. These
  are the reason `cfg_all` back-edge counts rise while `cfg_reachable` stays 1.0.
* **`snr_s5_10_s.lua:main_46`** — the one row where a *live* back edge count
  falls (5 -> 3) without a defect. The original's `if/elseif/elseif` on a selector
  gives each arm its own jump back to the loop head (`O87`, `O98`, `O100`,
  `O106`); the predecessor writes three sequential `if`s, so a taken arm falls
  through the remaining equality tests and takes a shared back edge (`P97`,
  `P103`). The selector register is written once before the chain and never inside
  an arm, and the tests are against distinct numeric constants, so the residual
  tests are false and effect-free. `preds(O47) = {46, 87, 98, 100, 106}` vs
  `preds(P47) = {46, 97, 103}` — same head, no path lost.
* **`snr_fragment_main.lua`** and **`snr_story_main.lua`** — test-polarity flips
  plus sunk callee `GETGLOBAL`s. `cfg_all` is identical `(136,137,2)` on both
  sides for both `main_1`s; the whole `cfg_reachable` `(24,25,2) -> (45,46,2)`
  move is one site where `EQ A=1` became `EQ A=0` plus an added unconditional
  jump, which changes which way the crude walk falls. `snr_story_main:main_3`'s
  `CALL 78 -> 79` is a duplicated `or`-fallback arm; enumerating the three paths
  gives identical dynamic call counts.
* **`snr_novel.lua` (behaviour arm)** — `probable-artifact` was the right
  *impact* and the wrong *cause*, so the verdict is not `probe-artifact`. The
  trace difference is six `C|comLayerLoadFalse|2args` lines that are a
  **permutation** of the same 29 (id, path) pairs, produced by a `pairs()` loop
  over a table the original builds with a constructor (`NEWTABLE A=1 B=0 C=23`)
  and the predecessor builds empty and fills field by field (`NEWTABLE A=21 B=0
  C=0`). Reproduced from first principles this session: the 29 constant key/value
  pairs were extracted from the original's own `main`, written out both ways, and
  run under `build/lua_sz4` — the two `pairs()` orders differ at positions
  **5, 9, 18, 20, 22, 27**, exactly the six differing trace lines. The
  constant/constant `SETTABLE` multiset in `main` is *identical* on the two sides
  (54 pairs, same SHA-256). The seventh differing line is the terminal
  `R|main|attempt to concatenate ...` and is the already-pinned `getobjname`
  noun class. **Caveat, recorded rather than assumed:** `pairs()` order is
  unspecified by Lua, so the two chunks are equivalent as *programs*; if the
  engine's `comLayerLoadFalse` were order-sensitive the divergence would be real,
  and nothing reachable from this repository can settle that. This is mechanism 3
  hitting the exclusion its own definition names.

### 3.7 Four corpus-wide sweeps, independent of the queue criterion

A verdict per queued row answers "is this row a defect". It does not answer "did
the queue miss a defect". Four sweeps over **all 1944 proto pairs** were run this
session; each looks for the predecessor *losing* something, which no
`equivalent-transform` mechanism can do.

| sweep | protos hit | where |
|---|---:|---|
| loses a **global read** (any name, any count) | **1** | `snr_mainmenu.lua:main_7` — defect (3) |
| loses a **reachable back edge** | **3** | `snr_music:main_3` (1), `snr_common:main_75` (6), `snr_s5_10_s:main_46` (adjudicated `equivalent-transform`, §3.6) |
| loses a **test op** (`EQ`/`LT`/`LE`/`TEST`/`TESTSET`) | **23** | all 23 inside queued files; includes defects (3), (4), (5) |
| loses a **`global_write`, `call_target`, `call_shape` or `return_arity`** | **0** | — |

Read together: **no call site, no global write and no return was deleted anywhere
in the corpus**; exactly one proto loses a global read and it is a defect; exactly
three lose a reachable back edge and two are defects. The 23 test-op losses are
dominated by the statically-decided `TEST`/`TESTSET` family — the largest,
`snr_common:main_74_13` at 15, is 7 `TESTSET` plus 8 `TEST`, and four `TEST` sites
were opened at instruction level (`O386`, `O405`, `O497`, `O561`): each is
`LOADK R, <number>` immediately followed by `TEST A=R C=1`, i.e. a test on a
numeric literal, always truthy in Lua (**including `0`**), so the following jump is
unconditional. `EQ` counts are unchanged in that proto.

**The back-edge sweep is the one that mattered**, and it is not the queue
criterion. `snr_common:main_75` scores `cfg_reachable = 1.0`; had the sweep not
been run, defect (6) would have been missed by every rule in this harness. The
sweep is cheap (one reachability walk per proto) and is the obvious candidate for
promotion to a standing check.

### 3.8 Which verdicts rest on a fired arm, and which on a silent one

Every `real-bug` except one rests on the **static** arm alone.

Measured this session over the 16 queued files: the `state` arm agrees on all 16,
and its compared payload is `ERR len=0` on 5, `len=22` on 9, `len=50` on
`snr_lib.lua` and `len=59512` on `snr_common.lua` — it contradicts nothing and
confirms nothing. The `behaviour` arm's reach on the same 16: `truncated` on
**11**, `silent:0/0` on **1** (`config.lua`), `complete` on **4** — and three of
those four complete runs are **12, 18 and 11 events** (`snr_fragment_main`,
`snr_mainmenu`, `snr_story_main`); the fourth is `snr_novel.lua`, one of the two
files that produced a behaviour row at all.

| defect | static arm | behaviour arm |
|---|---|---|
| (1) `snr_music:main_3` | fired, divergent | **fired, divergent** (`CAP\|3001` vs `OK\|94`) |
| (2) `snr_common:main_76_2` | fired, divergent | silent — `truncated:1/79`, and `main_76_2` sits under a global that is never invoked |
| (3) `snr_mainmenu:main_7` | fired, divergent | fired and **agreed**, on an 18-event run |
| (4) `snr_graphic:main_4` | fired, divergent | agreed at `truncated:1/1` (`CAP`) |
| (5) `snr_memory:main_4` | fired, divergent | agreed at `truncated:1/1` (`CAP`) |
| (6) `snr_common:main_75` | fired, divergent | silent, as (2) |

So **five of the six defects are invisible to both dynamic arms**, and for (3) the
behaviour arm returned `agree` — a positive statement of agreement over a run that
never reached the defective loop. That is the §2.5 warning arriving: `agree` at
shallow reach is not evidence of equivalence, and this section is the first place
in the project where the two can be separated defect by defect.

### 3.9 Numbers from the brief and from §2 that did not reproduce

Every figure in §3 was measured this session. Three inherited statements did not
survive re-measurement:

1. **"`snr_memory.lua` … not queued by any arm."** False. `snr_memory.lua` is
   queued on the fingerprint arm and has been since task 5 round 1 (§2.9.2 says so
   correctly; the brief's summary contradicted it). All **4** files with a
   numeric-constant multiset difference — `snr_common`, `snr_mainmenu`,
   `snr_memory`, `snr_music` — are inside the queue.
2. **"`snr_music.lua`'s 13 predecessor-only numeric constants are unrolled-loop
   residue that corroborates the known defect"** (§2.9.2). They are not. Measured:
   `snr_music:main_3`, the defective proto, has an **identical constant
   fingerprint multiset** — its `proto` delta prints no `const` line at all. All
   21 gained numeric constants are in the chunk root `main`, where an array
   constructor (`NEWTABLE B=19` + 22 `LOADK` + `SETLIST`) was rewritten as 22
   indexed `SETTABLE`s with explicit keys `1..22`, plus `GETTABLE 0 -> 70` for the
   re-read receiver. That is mechanism 3, not loop residue. The same rewrite
   accounts for `snr_memory.lua`'s `{8.0}` (a 9-element `SETLIST` array becoming
   nine indexed stores, contributing `num:3..num:8`) and for `snr_mainmenu`'s and
   `snr_common`'s numeric deltas.
3. **§2.10's prioritisation.** `snr_mainmenu.lua` was named "the weakest row in
   the queue" and placed last; it is defect (3). See §3.3.

Reproduced exactly, on the other hand: the queue shape (16 files / 18 rows / 10
`candidate-defect`, 1 `probable-artifact`, 7 `suspect`), the three §2.7 bands
(`0.97 <= call_targets < 1.0`, `0.995 <= global_reads < 1.0`, numeric-only
constant differences) all **0** outside the queue over 213 files / 1230 protos
with `opcode_family` the only sub-1.0 component there (212 protos), the
string-constant census (**1** differing file), the numeric-constant census (**4**
differing files, predecessor-only values in 2), the `wait` +2 signature (exactly
3 protos), and the behaviour-arm reach census.

### 3.10 One more measurement worth recording: where our own decompiler stands

Of the **44** flagged proto paths in the queue, our own pipeline certifies
**20 as `L3`** — so for 24 of them our text is *not* a faithful reference and was
not used as one. That includes 5 of the 6 defect sites: only
`snr_common:main_75` among them is `L3` on our side (`snr_common:main_76_2`,
`snr_music:main_3`, `snr_graphic:main_4`, `snr_memory:main_4` and
`snr_mainmenu:main_7` are all `L1`, and **all five carry the same refusal kind**,
`structure: pc N: if targets out of range` — at pc 11, 144, 120, 121 and 213
respectively). The brief's "96.8 % of unique shapes"
is a corpus-wide figure; **inside this queue the rate is 20/44**, and the queued
paths are enriched precisely in the shapes our own recognizer refuses. Where our
text was used it is named in the row's evidence; everywhere else the adjudication
rests on the two disassemblies.

### 3.11 What went into the suite, what stayed a job, and what it costs

**Suite (5 new tests in `tests/test_cross_corpus.py`, 24 -> 29 in that module,
941 -> 946 overall).** The half of the pin gate that rots silently:

* `test_pin_table_is_well_formed` — vocabulary, shape, 18 rows, and the red line
  (`json_safe` over every evidence string and every note). No corpus.
* `test_the_state_arm_has_no_pins_because_it_has_no_divergences` — turns an empty
  table into a claim: the L1.5 arm must keep agreeing on all 16 pinned files.
* `test_every_pin_still_diverges_with_the_recorded_evidence` — `moved` and `gone`
  empty on all three arms over the 16 pinned files.
* `test_the_pin_gate_can_fail` — the non-vacuity proof for the one above,
  perturbing a *copy* of the table two ways and requiring `adjudicate_pins` to
  name the row.
* `test_the_six_real_bug_verdicts_are_the_committed_headline` — the payload,
  asserted so it cannot be quietly downgraded.

**Job.** `unexpected` — "no divergence anywhere in the corpus is unpinned" —
needs all 229 files and stays in
`uv run python scripts/cross_corpus.py --arm all`, which now **exits 0**
(measured 3.25 s this session; §2.8's 3.5–3.9 s band). Asserting `unexpected` over
only the pinned files would have made it vacuous, so it is deliberately not
asserted in the suite; the test's docstring says so.

**Neuter proof, run and restored (2026-08-14).** One pinned evidence string was
edited (`snr_s7_10_f.lua`, `calls=19` -> `calls=99`);
`test_every_pin_still_diverges_with_the_recorded_evidence` — and only that test —
went red (`1 failed, 28 passed`), and the file was restored to green.

**Cost.** Standalone: the module is **1.61–1.70 s** for 29 tests, against
0.40–0.46 s for the 24 it had, so **~1.2 s attributable to task 6**. Whole-suite
A/B in one batch, alternating: without `test_cross_corpus.py` 42.72 s / 44.99 s
(917 tests), with 46.28 s / 46.84 s (946). The `without` arm's own spread is
2.3 s, so — exactly as in §2.8 — the batch difference is not resolvable against
this host's noise and the standalone figure is the honest bound. Full suite with
both corpus variables set: **946 passed in 44.53 s** (host macOS arm64 / Darwin
24.2.0), inside the ~120 s earmark, and the ~1.2 s is M6 formal-verification
instrument cost: it is the pin gate for the cross-corpus scan.

### 3.12 What this leaves open

* **Four of the six defects are newly found and none is repaired here.**
  `corpus/pred_repairs/` (task X, out of plan — this section originally cited
  it as "M6 task 4", which is the in-plan observation pass; corrected at the
  M6 wrap) covered `snr_music.lua` and `snr_common.lua:main_76_2` when this
  was written. **A second out-of-plan round, task X2, repaired the other four**
  — see §6.2. Both rounds are downstream of this adjudication, which
  deliberately ran against the *unmodified* predecessor corpus, as does every
  arm and sweep in this report.
* **Promote the reachable-back-edge sweep** (§3.7). It is one reachability walk
  per proto, it found a defect no rule in this harness ranks, and
  `semantic_score._cfg_shape`'s `cfg_reachable` demonstrably scores 1.0 on a proto
  whose only loop vanished.
* **`snr_common.lua`'s remaining flagged paths.** `main_55`, `main_28`,
  `main_76_7` were checked at their back-edge and reachability sites but not
  walked end to end, and `main_77_24` was not opened; all four match the
  `+MOVE / +LOADNIL / -TESTSET / dead-escape-JMP` family fingerprint and none
  loses a global read, a call target, a call shape, a return or a reachable back
  edge (§3.7's sweeps cover all 1944 protos, so this residual is bounded). They do
  not affect the row verdict, which is `real-bug` on `main_76_2` and `main_75`.
* **Two premises that bytecode cannot settle**, both named where they are used:
  no side-effecting `__index`/`__newindex` on `_G` or on engine-owned tables
  (mechanisms 3 and 5 reorder a global read against pure table reads), and
  `pairs()` order-insensitivity in the engine's own callees (§3.6,
  `snr_novel.lua`). Supporting but **not conclusive**, measured this session on
  both sides: `setmetatable`, `getmetatable`, `rawset`, `rawget`, `__index`,
  `__newindex`, `__len` and `__eq` occur in **0 of 229 predecessor source files**
  and, as a substring of any string constant, in **0 of 229 original bytecode
  files**. Not conclusive because the metatables that matter would be installed by
  the PSP engine's C side, which neither corpus can see — the same limit M4's
  effect-lattice calibration recorded for the 56 engine-owned globals the corpus
  reads but never writes.

## 4. The four loss sweeps, promoted to a standing gate (task X3, out of plan)

§3.7 ran four sweeps over all 1944 proto pairs by hand, and one of them — the
reachable back edge — found defect (6) on a proto whose `cfg_reachable`
component measures exactly **1.0**. This section is those sweeps turned into a
committed, pinned check: `scripts/loss_sweep.py` plus `tests/test_loss_sweep.py`
(13 tests, 6 of which need no corpus).

### 4.1 Where they live, and why beside rather than inside

`scripts/loss_sweep.py`, a sibling of `cross_corpus.py` rather than a fourth
arm of it. Three reasons, all recorded in that module's own docstring: the
scanner's `ArmResult`/`PRED_PINS` are keyed **per file** with one evidence pair
each (and `_fingerprint_one`'s own comment records what that costs — three of
`snr_common.lua`'s flagged paths hide behind `main_76_2`), while the sweeps are
per-**proto** and naming the proto is the point; the sweeps' value is precisely
that they are *not* the queue criterion, so routing them through `first_cut`
would file them under a triage vocabulary built for a graded metric; and
`--arm all` is deliberately a job while this is cheap enough to be a suite
gate. It reuses `probe_common.adjudicate_pins`, `cross_corpus.json_safe`,
`cross_corpus.VERDICTS`, `verify.semantic_score.collect_proto_signatures`
(so the two instruments cannot disagree about what a global read is),
`predcorpus.load_pred_proto` with `strip=not carries_debug(original)`, and
`cfg.blocks`/`cfg.dom`.

### 4.2 The four sweeps as re-measured 2026-08-14

| sweep | field(s) | protos hit | §3.7 said |
|---|---|---:|---:|
| 1 | `global_reads` | **1** | 1 |
| 2 | `n_natural_loops`, `n_back_edges` | **4** | 3 |
| 3 | `test_ops` | **24** | 23 |
| 4 | `global_writes`, `call_targets`, `call_shapes`, `return_arity` | **0** | 0 |

25 distinct protos over 10 files, all pinned. Two figures did not reproduce and
in both cases the difference is a *definition* the sweep is now explicit about:

* **Back edges: 4, not 3.** The fourth is `snr_mainmenu.lua:main_7` — defect
  (3), which §3.7 caught on the global-read sweep instead. Its 16 loop headers
  are unchanged and four of them lose exactly one latch each (O253, O791,
  O1326, O1871, four latches → three).
* **Test ops: 24 under a per-opcode reading, 23 under §3.7's aggregate.** The
  extra proto is `snr_common.lua:main_76_2` — **defect (2)** — whose
  predecessor gains 7 `EQ` and 2 `LT` while losing 1 `TEST` and 2 `TESTSET`, so
  the five-opcode total goes 27 → 33 and the aggregate reading never sees it.
  The gate counts per opcode for that reason.

### 4.3 A loop is a header; a latch is a back edge

Both numbers are emitted under the names `corpus/observation/classes.json`
already uses, and the distinction is load-bearing, not bookkeeping:

* `n_natural_loops` fires on **2** protos and both are defects —
  `snr_music.lua:main_3` (2 → 1) and `snr_common.lua:main_75` (1 → 0), each "a
  loop became straight-line code". No benign instance.
* `n_back_edges` fires on **4**: those two, plus defect (3), plus one benign.

Both are computed over **reachable blocks only** (`immediate_dominators`' key
set), so an unreachable latch — the dead escape jump that `snr_novel.lua`'s and
`snr_s7_10_f.lua`'s pins walk — is not counted at all.

### 4.4 The one benign back-edge loss, explained

`snr_s5_10_s.lua:main_46`, `equivalent-transform`. Measured this session:

| | headers | latches |
|---|---|---|
| original | O4, O48 | O4 ← {O818}; O48 ← {O80, O91, O101, O102} |
| predecessor | P4, P48 | P4 ← {P796}; P48 ← {P98, P99} |

`n_natural_loops` 2 = 2; `n_back_edges` 5 → 3. **One loop with fewer latches** —
the same shape M6 task 4 was corrected on. The mechanism is the one §3.6
already walked: the original's `if`/`elseif` chain gives each arm its own jump
back to the shared header, the predecessor's sequential `if`s let an arm fall
through the remaining equality tests to a shared latch; `EQ` 49 → 48 and `JMP`
93 → 89 are that re-phrasing, and `preds` of the header still partition the
original's. No path into the header is lost. It is explained, not merely
pinned.

### 4.5 Two things the sweeps settled that §3.12 left open

* **`snr_common.lua:main_71` is not a seventh defect.** It loses 2 `EQ` and 2
  `TESTSET`. The `EQ` pair is *dead*: O336 `EQ A=0 R19 K[true]` is followed by
  O337 `JMP -> 338` while its not-taken path also lands on 338, and
  O341/O342 `JMP -> 343` is the same shape — two `if`s whose arms converge on
  the next pc. The `pressButton` calls they tested (O335 LEFT, O340 RIGHT)
  survive, `call_targets` 42 = 42. `TESTSET` O327 is `LOADK`-of-a-number
  preceded; `TESTSET` O309 is decomposed into P342 `TEST` + P346 `MOVE`, which
  is what `TESTSET` means.
* **Three of §3.12's four unwalked `snr_common.lua` residual paths** —
  `main_55`, `main_76_7`, `main_77_24` — are now walked *for these fields*
  (`main_28` too), each losing only statically-decided `TESTSET`s at named pcs.
  That is not a full end-to-end walk of those protos; it is a walk of every
  site the sweeps flag.

### 4.6 The recurring benign mechanism, measured rather than assumed

Nineteen of the 25 rows are `equivalent-transform`, and most are the same
thing: a `TEST`/`TESTSET` whose tested register was written by the immediately
preceding instruction with a compile-time-fixed truth value. Census over every
such site in the 17 protos that lose one: **39** are `LOADK`-preceded and every
one of the 39 loads a `LuaNumber` — never a boolean or `nil` constant, which
`luac` emits as `LOADBOOL`/`LOADNIL` — and every Lua number is truthy, **0
included**. The other fixed-truth producers that occur are `OP_LEN` and the
arithmetic ops (a number, or they raise) and `OP_CONCAT` (a string, or it
raises); a register that is an operand of `OP_LT`/`OP_LE` is fixed the same way
because `lvm.c::luaV_lessthan` admits two numbers or two strings and raises
otherwise.

**Pc bases, corrected at the M6 final review (2026-08-14).** This paragraph
used to assert that the pin notes were already 1-based. They were not:
`scripts/cross_corpus.py::PRED_PINS` was **uniformly 0-based on both sides**,
and `scripts/loss_sweep.py::LOSS_PINS` was **mixed** — 1-based except for the
three notes that quoted §3 verbatim. Both tables were re-based to 1-based in
that pass and every `O<n> OPNAME` / `P<n> OPNAME` pair in either table was
machine-checked in it: the opcode at 1-based pc `n` is `OPNAME`, and every
quoted predecessor set, jump target and unreachable-pc claim was re-derived
from the decoded instruction stream. The checker was a one-off, not a standing
gate (M7 agenda 6).

So, in force now:

- **Pin notes** (`PRED_PINS`, `LOSS_PINS`) quote **1-based** pcs (`O<n>`
  original, `P<n>` predecessor), matching `pyluadec.lift` — which decodes
  `p.code[pc - 1]` at pc — and `luac_sz4 -l -l`.
- **This report's §3 and §4 prose** quotes **0-based** pcs, so the same
  instruction is **one greater** in a pin note than in the prose above. (Left
  0-based deliberately: renumbering the prose is a much larger edit with no
  gate behind it, and an undisclosed base is the defect, not a base.)

### 4.7 Non-vacuity: the gate can fail, and it names the proto

Injection rather than a table edit, so the whole pipeline is exercised. The
predecessor corpus was copied to a temp dir (neither corpus was modified) and
one loop in `snr_crd_10.lua` was turned into an `if` (`while v2 < 1 do` →
`if v2 < 1 then`, with the `break` inside it replaced so the chunk still
compiles). Against that copy:

```
26 proto(s) lost something over 1944 proto pair(s); 25 pinned
  sweep 2: 5 proto(s) [n_natural_loops, n_back_edges]
  snr_crd_10.lua:main_2              n_natural_loops-1 n_back_edges-1
  UNPINNED loss(es): ['snr_crd_10.lua:main_2']
```

`scripts/loss_sweep.py` exits **1**; `pytest tests/test_loss_sweep.py` reports
`3 failed, 10 passed`, with
`test_no_proto_loses_something_unpinned` failing on
`assert ['snr_crd_10.lua:main_2'] == []`. Against the real corpus, both are
green again (`13 passed`, CLI exit 0).

### 4.8 Cost

`scripts/loss_sweep.py` standalone: **3.43 s** wall for all 229 files / 1944
pairs. Breakdown measured in one process on this host: ingest of the original
side 0.06 s, compile+ingest of the predecessor side 0.63 s cold and 0.04 s once
`oracle.compile_source`'s memo is warm, `collect_proto_signatures` over 3888
protos 1.16 s, `lift_proto` + `build_cfg` + `immediate_dominators` over the same
3888 protos 1.52 s. A `ThreadPoolExecutor(8)` came in at 3.09 s against 3.4 s
serial — a 9 % return for a thread pool in a suite gate, so `sweep()` is serial.

In the suite the module measures **3.50 s / 3.58 s standalone** and the whole
suite goes 946 → 959 tests. Alternating A/B, two rounds, both corpus variables
set: without it **47.36 s / 47.62 s**, with it **51.39 s / 51.10 s** — a
**3.5–4.0 s** delta that agrees with the standalone figure, so unlike §2.8's and
§3.11's batch A/Bs this one is resolvable against host noise (the `without`
arm's own spread is 0.26 s). Bare, with neither corpus variable set:
**845 passed, 114 skipped in 7.88 s**; 6 of the 13 new tests run there. This is
M6 formal-verification instrument cost: it is the
standing gate for the four corpus-wide loss sweeps, and it is the second
instrument (after the `PRED_PINS` gate) that turns an adjudication into
something that fails on regression.

---

## 5. The enumerated differential instrument (task 7)

Task 7 was **re-scoped on 2026-08-14** (plan amendment): the corpus-wide run
over the whole Class-1 candidate population moves to M7, and what remains is
the instrument itself plus a demonstration on the compound-`if` refusal
protos — the population Task 11 will fix. The reason is §3's and §4's
measurements, not a preference: all six confirmed predecessor defects were
found by the *static* arm, five of them invisible to both dynamic arms, and
the cheapest static instrument in the tree outperformed the designed one.
What survives of Task 7's justification is its *other* purpose — proving
semantic equivalence where bytes differ — which is what Tasks 9–12 need.

Files: `scripts/probe_enum.py`, `scripts/probe_enum.lua`,
`tests/test_probe_enum.py`. CLI:
`PYLUADEC_CORPUS_DIR=... uv run python scripts/probe_enum.py [FILE PROTO_PATH]`.

### 5.1 The population: 13 leaves, not 21 shapes

The amendment says "the 13 compound-`if` refusal protos"; the ledger's
`structure:` family is **21 shapes**. Both are right, about different things.
The ledger copies a refusing descendant's reason **verbatim** up to its
ancestors, so `snr_story_main.lua:main` — 10 instructions — is recorded as
`structure: pc 131: if targets out of range`. Re-running `build_sir` on each
of the 21 protos **alone** splits them **13 leaves / 8 ancestors**, and the
leaf set agrees exactly with the one `corpus/observation/classes.json` already
publishes as `refusal_origin == "own"` (two independent derivations, same 13).
The 8 ancestors are collateral and clear when the leaves do; they are not
driven here.

Leaves: `snr_common.lua` `main_71` `main_74_13` `main_76_2` `main_76_8`
`main_81`; `snr_fragment_main.lua:main_1`; `snr_graphic.lua` `main` `main_4`;
`snr_mainmenu.lua:main_7`; `snr_memory.lua:main_4`; `snr_music.lua:main_3`;
`snr_s4_10_s.lua:main_58`; `snr_story_main.lua:main_1`.

### 5.2 What the instrument does

For a chosen proto it takes that proto's **branch channels** — the access
paths its own `EQ`/`LT`/`LE`/`TEST` conditions read, from
`observation_classes.channels`, the same dataflow Task 4 published — and
enumerates the **full product** of their value domains. Each point of the
product is an *assignment*; each assignment is installed into the L1.75 stub
environment and both sides (original bytecode, our shipped artifact) are run
under it and compared byte-for-byte.

`EnumVerdict` has four kinds. Three are the brief's: `identical`,
`divergent(assignment, first-diff)`, `budget-exceeded(space_size)` — over
budget refuses and states the size, and **nothing is run** (`n_assignments ==
0`), never a silent sample. The fourth, `never-reached`, exists because of a
measurement this milestone kept making: `probe_keyseq.py` stubs the very gates
that select two of the six confirmed defects, and five authored sequences gave
byte-identical traces across three versions of one file. An arm that never
fired is not evidence of agreement, so a run whose target was never entered
says so and never says `identical`.

**How reach is established on both sides.** The obvious test — a `debug` call
hook keyed on the target's `(linedefined, lastlinedefined)` — works only on
the original: every one of these 13 protos ships as fallback output, whose
proto tree is deliberately reshaped into `__pld_F` factories, so no line- or
path-keyed correspondence exists on our side. What both sides share is the
**name** the function is published under. So the probe has a `discover` mode
that runs the **original** (where `linedefined` survives stripping and does
name the ledger's proto tree), walks the globals the chunk defined, and
reports the access paths at which a function with the target's line span is
published; both sides are then driven with that path and each records its own
`I|<path>` event. A side that does not publish the name reports `ENTRYFAIL`,
which is deliberately **not** in the comparable-marker set. Ambiguity is
refused rather than guessed: if two protos in the file share a line span,
`discover_entries` raises.

**What the ENUMERATION bought here, separately from the targeted entry.**
Two things are easy to conflate and are worth very different amounts on this
population. The **targeted named entry** (`discover` + `E`) is what reached
new behaviour: the L1.75 gate invokes every function-valued global in one
process under one 3000-event budget, and on `snr_common.lua` that budget is
spent inside the FIRST of 79 (`PROBE1|CAP|3001`, one `I|autoSystemSave`) — the
`truncated:1/79` already on record from §3. The **enumerated product** bought
**nothing a single default-stub drive would not also have got**: both pinned
divergences reproduce under a no-assignment drive, measured directly. What the
enumeration did establish is quantitative and about sampling rather than
finding: on `snr_mainmenu.lua:main_7` only **16 of 128** assignments diverge,
so a sampler had a ~12 % chance of seeing it. **No row on this population
makes the enumeration load-bearing**, and M7 should weigh extending it on that
basis; the case for keeping it is prospective (Tasks 9–12 change
reconstruction, and a representation change wrong on one arm of one branch is
exactly what a single stub policy cannot see).

**Values drive, indices are published.** A branch constant may be a string out
of the constant pool, i.e. game text. `classes.json` renders every string as
the literal `"str"` (that is how it stays ASCII), which makes it unusable as a
source of the value that takes the `== "..."` arm. So `channels_of` reads the
real constants — held as `bytes`, passed to the probe as hex — while every
ASCII surface (`Assignment.name`, the CLI, this report) names a value by its
**index** in the channel's domain (`v0`, `v1`, …). The one change to Task 4's
generator is a parallel `rec["raw"]` set alongside the existing `rec["cmp"]`;
`corpus/observation/classes.json` regenerates **byte-identical**, verified by
`cmp` this session, and its published figures reproduce (`110/113`
choice-branch drivable, `1940/1944` corpus-wide).

### 5.3 Result over the 13 leaves

`identical 8, divergent 2, budget-exceeded 1, never-reached 2`; 5.7 s wall for
the whole population, CLI exit 0 (both divergences pinned).

| file:proto | ch | space | `classes.json` | adjudicated | distinct traces | verdict |
|---|---|---|---|---|---|---|
| `snr_common.lua:main_71` | 2 | 4 | 4 | 4 | **1 / 4** | identical (CAP) |
| `snr_common.lua:main_74_13` | 2 | 4 | 4 | 4 | 2 / 4 | identical (CAP) |
| `snr_common.lua:main_76_2` | 4 | 24 | 24 | 24 | 2 / 24 | identical (CAP, OK) |
| `snr_common.lua:main_76_8` | 2 | 4 | 4 | 4 | **1 / 4** | identical (CAP) |
| `snr_common.lua:main_81` | 1 | 2 | 2 | 1 | **1 / 2** | **divergent** (OK) |
| `snr_fragment_main.lua:main_1` | 4 | 16 | 16 | 0 | — | **never-reached** |
| `snr_graphic.lua:main` | 1 | 2 | 2 | 2 | **1 / 2** | identical (OK) |
| `snr_graphic.lua:main_4` | 3 | 8 | 8 | 8 | 4 / 8 | identical (CAP, OK) |
| `snr_mainmenu.lua:main_7` | 6 | 128 | 128 | 53 | 14 / 128 | **divergent** (CAP, OK) |
| `snr_memory.lua:main_4` | 2 | 4 | 4 | 4 | 4 / 4 | identical (CAP, OK) |
| `snr_music.lua:main_3` | 1 | 2 | 2 | 2 | 2 / 2 | identical (CAP) |
| `snr_s4_10_s.lua:main_58` | 7 | **23616** | **1152** | 0 | — | **budget-exceeded** |
| `snr_story_main.lua:main_1` | 4 | 16 | 16 | 0 | — | **never-reached** |

**The arithmetic, stated three ways because they are three different
numbers.** The enumerated product over the ten drivable rows is **182**
assignments (not 186 — an earlier draft of this section mis-added the column).
**106** are ADJUDICATED, because `exhaust` returns at the first difference:
`main_81` at index 1, `main_7` at index 53. The number of Lua subprocesses
actually launched is larger still and is not guaranteed deterministic —
`ThreadPoolExecutor.map` keeps up to `jobs` comparisons in flight and cancels
the rest when the generator is abandoned. Counted by instrumenting
`probe_enum._run`, three runs this session: **230** drive processes and **11**
discover processes each time; round 1's independent count saw **230 / 232 /
230**, so it is near-deterministic rather than fixed.
`EnumVerdict.n_assignments` is the adjudicated count, and its docstring now
says so.

**"Distinct traces" is how much an `identical` is worth** (measured over the
whole product, not the adjudicated prefix; `tests/test_probe_enum.py::
test_what_an_identical_verdict_explored_on_each_corpus_row` pins every row).
**Four of the ten driven rows select nothing** — their whole product produces
one trace, so their `identical` says no more than a single point would — and
`snr_graphic.lua:main`'s entire evidence is a **one-event** trace
(`G|main|<function#1>`: it is a chunk root whose body only publishes a
function). That is not a defect in the verdict, it is the verdict being read
too generously without this column, which is why the count now rides on
`EnumVerdict` and in the CLI output.

`CAP` in the status column means that assignment hit the 3000-event budget —
the same frozen budget the L1.75 gate uses, so both sides truncate at the same
point in the observable behaviour; it is recorded in the verdict so a
truncated run can never be read as a completed one.

**The one number that did not reproduce — and it generalises.**
`snr_s4_10_s.lua:main_58`'s input space is **23616** here against the **1152**
`classes.json` publishes. Neither is wrong: `classes.json`'s `domain` is
`len(cmp) + 1` over `const_lit` renderings, which collapse every string to
`"str"` and every non-integer number to `"num"`; this instrument needs the
distinct constants, because supplying `"a"` does not take the `== "b"` arm.
The other twelve leaves agree exactly between the two.

Re-derived corpus-wide this session with `probe_enum.channels_of`:

| population | protos | differ | within budget (coarse → fine) |
|---|---|---|---|
| whole corpus | 1944 | **26** | 1940 → **1936** |
| `classes.json` candidates | 162 | **23** | 159 → **155** |
| — `choice-branch` | 113 | — | 110 → **106** |
| — `ui-keyloop` | 11 | — | 11 → 11 |
| — `neither` | 38 | — | 38 → 38 |

Worst ratios: `snr_s7_10_f.lua:main_53` 4 → 118 (**29.5×**),
`snr_s2_10_s.lua:main_60` 240 → 5280 (22.0×), `snr_s3_10_s.lua:main_59`
3456 → 72576 (21.0×), `snr_s4_10_s.lua:main_58` 1152 → 23616 (20.5×).

> **The candidate rows of that table moved after task 12, and the corpus rows
> did not** (re-derived at the M6 wrap, 2026-08-14, same
> `probe_enum.channels_of` walk). Task 12 closed leaf refusals, so
> `classes.json` regenerated with **156** candidates instead of 162:
> candidates **156**, within budget **153 → 149**; `ui-keyloop` **9** (all 9
> within budget under both models); `neither` **34** (all 34). `choice-branch`
> is unchanged at **113**, and so is its headline **110 → 106**. The whole-
> corpus row is unchanged too: 1944 protos, **26** differ, **1940 → 1936**.
> Every "worst ratio" above reproduces exactly. The lesson stands unchanged;
> only the population it is quoted over moved.

So **Task 4's "110 of 113 Class-1 candidates fit 4096" is 106 of 113 for an
enumeration**, and the corpus-wide "1940 of 1944" is 1936. This was a defect
in `observation_classes.py`'s own documentation — its module docstring defined
`domain` as "`|distinct constants compared against| + 1`", which the
`const_lit` collapse makes false — and the fix landed in that docstring's
"Channels and input space" section, where a sizing consumer reads, not only in
the new `canon` helper. `classes.json` itself is unchanged and still
byte-identical: what it publishes was never wrong, only its stated
definition.

**The two never-reached rows** (`snr_fragment_main.lua:main_1`,
`snr_story_main.lua:main_1`) are protos the chunk does not publish under any
name the discovery walk reaches — consistent with the static scan in
`observation_classes._defs_and_calls`, which finds no global or method
definition for either. They have 16-point spaces that could be enumerated the
moment a caller-driven entry exists; that is M7 work, and reporting them as
`identical` would have been the exact failure this verdict exists to prevent.

### 5.4 The two divergences: one already-pinned class, one new instance

Both are the **`getobjname` naming artifact of the fallback's `__pld_R` box
model**, already pinned for `snr_mainmenu.lua` in `probe_global_state.py` and
`probe_behaviour.py` since M3. `ldebug.c`'s `kname()` names an operand only
when the producing instruction is a `GETTABLE`/`GETGLOBAL` with a **string**
constant key; the fallback routes every register through `__pld_R[<number>]`,
so `kname` says `field '?'`. Only the noun in an error **message** differs —
both sides fail at the same instruction with the same error kind.

`snr_common.lua:main_81` (`keyWait`) is a **new instance**. **The first
version of this paragraph gave the wrong reason and round 1 falsified it**; the
measured mechanism follows. Original bytecode, 1-based pcs (matching
`pyluadec.lift` and `luac -l -l`):

```
 2 LOADK R2 K(1)
 3 GETGLOBAL R3 "pressButton"   4 LOADK R4 "CIRCLE"   5 CALL R3 2 2
 6 EQ 1 R3 K(true)              7 JMP -> 9
12 EQ 0 R3 K(true)             13 JMP -> 16
14 EQ 1 R2 K(0)                15 JMP -> 26        (RETURN)
16 DIV R3 R0 K(<number>)
```

**Both** values of `pressButton()` reach pc 16, and their traces are
byte-identical at 116 events. `false` fails pc 12's `EQ 0` and takes pc 13's
`JMP -> 16` straight to the `DIV`; `true` skips pc 13, falls through pc 14's
`EQ 1 R2 K(0)` — R2 is `1` from pc 2's `LOADK`, it is **not** R1 as an earlier
draft said — and skips pc 15's `JMP -> 26`. Driving `keyWait` with **no
assignment at all** already produces the divergence.

What the L1.75 gate actually misses it by is **truncation**:
`probe_raw(snr_common.lua)` returns `PROBE1|CAP|3001` having invoked exactly
**one** of the file's 79 function-valued globals (`I|autoSystemSave` →
`R|autoSystemSave|CAP`) — the `truncated:1/79` already on record from §3.
`keyWait` is never invoked. So the credit belongs to the **targeted named
entry**, not to the enumerated product; `test_the_targeted_entry_reaches_
what_the_l1_75_gate_truncates` asserts each clause of that.

`R0` is the parameter and the probe calls every function with no arguments, so
`R0` is `nil`: the original says "arithmetic on a nil value" (a bare register,
and `locvars` are stripped, so `kname` finds no name at all) and the fallback
says "field '?'". The pin carries `pressButton()=v0` only because it is first
in enumeration order; `v1` diverges identically.

Both pins should **converge** when Task 11 makes these protos certify `L3` and
stop shipping through the box model. Adjudication is two-directional
(`scripts/probe_common.py::adjudicate_pins`, the same function the L1.5 and
L1.75 gates use), so convergence reports `gone` and forces the pins to be
deleted rather than left passing silently.

### 5.5 Fault injection: the instrument can fail, and it names the assignment

Two committed injections, both synthetic (`tests/test_probe_enum.py`), both
against the **decompiled** side of a fixture whose original is real `luac`
output:

1. `test_an_injected_arm_swap_is_divergent_and_names_the_assignment` — the two
   arms of one `if` are swapped. Verdict `divergent`; the named assignment is
   re-driven on its own and its traces must differ, and the recomputed
   first-diff must equal the one the verdict carried.
2. `test_a_swap_on_only_one_arm_is_still_named` — the sharper form: only the
   `== 1` arm is wrong, so **exactly one** of the two assignments exposes it.
   The verdict must name that one (`sys.flagA=v0`, the compared constant) and
   its first-diff must be `engine.TrueArm` against `engine.Wrong`. Naming the
   other assignment would be a verdict that does not reproduce.

Non-vacuity for the agreeing direction is separate and explicit:
`test_every_arm_of_every_branch_is_actually_taken` requires the 4 assignments
of the two-flag fixture to produce **4 distinct traces** and, between them, all
four of `engine.A0/A1/B0/B1` — an enumeration that agreed because every point
took the same path would prove nothing. Its **corpus counterpart** is
`test_what_an_identical_verdict_explored_on_each_corpus_row`, which pins the
distinct-trace count of all ten driven rows; four of them are 1, and §5.3 says
what that is worth.

### 5.6 Guards proven load-bearing

* **Reach: no published name (`never-reached`)** — in-test neuter,
  `test_the_reach_guard_is_load_bearing`: with `discover_entries` made to fall
  back on "we called *something*", the unpublished-helper fixture flips from
  `never-reached` to `identical`. Restored by `monkeypatch`.
* **Reach is keyed on the `R|` COMPLETION event, not the `I|` intent event** —
  round 1 constructed the hole: a chunk body emitting exactly
  `MAX_EVENTS - 2` events makes the `I|` itself the event that trips the cap,
  so the call is skipped, the target executes nothing, and an `I|`-keyed test
  returns `identical`. Measured at 2996 / 2997 / 2998 / 2999 chunk-body
  iterations: `identical` / `identical` / **`never-reached`** /
  `never-reached`; before the fix the 2998 row was `identical`. Pinned by
  `test_reach_requires_the_completion_event_not_the_intent_event` and neutered
  by `test_the_completion_keyed_reach_is_load_bearing`. No instance among the
  13 shipped protos (all 182 driven assignments carry an `R|`), so no
  committed verdict changed.
* **Partial reach (`n_entered != n_adjudicated`)** — round 1 found this clause
  deletable with a green tree. The reaching shape needs the SAME access path
  read by both the target's branch (which is what makes it a channel) and the
  chunk body (which is what lets an assignment decide whether the budget
  survives to the call); `test_the_partial_reach_guard_is_load_bearing` builds
  it and pins `entered on 1 of 2`.
* **Per-side reach conjunction (`t0.entered and t1.entered`)** — likewise
  found deletable. `test_the_per_side_reach_conjunction_is_load_bearing` gives
  it a reaching shape: two sides that agree on every recorded event where only
  one of them entered the target.
* **Ambiguous line span** — out-of-tree neuter: `if len(twins) != 1:` →
  `if False:`. `test_an_ambiguous_line_span_is_refused_rather_than_guessed`
  goes red with `Failed: DID NOT RAISE ProbeError`; restored, green.
* **`ENTRYFAIL` is not a comparable value** — out-of-tree neuter: adding
  `b"ENTRYFAIL|"` to `_MARKERS`.
  `test_an_entry_that_does_not_resolve_is_not_a_comparable_value` goes red;
  restored, green. (It fails with an `IndexError` out of `_header` rather than
  a clean message — the marker check is the only thing that keeps a
  probe-side failure out of the comparison path, and nothing downstream is a
  second line of defence. That is recorded, not fixed: a second check there
  would be a guard with no reaching shape.)

### 5.7 One implementation of the stub driver, not a fourth copy

`probe_keyseq.lua` was written by copying `probe_behaviour.lua`; measured this
session with `difflib.SequenceMatcher`, **257 lines were identical** in blocks
of 4 or more. M5 recorded that as debt and Task 7's brief forbade a fourth
copy. The serialiser, the recorder, the frozen stub-return policy, the proxy
metatable, the determinism overrides and the environment shadow table now live
in `scripts/probe_common.lua` as closure factories with optional hooks
(`taint` for L2's comparison metamethods, `on_read`/`on_call`/`track_segs` for
this task's assignment injection), and **all three** probes consume them.
`scripts/probe_enum.lua` was written against the shared factories from the
start.

The evidence that the extraction changed nothing is the standing gates
themselves: the L1.75 corpus gate (229 files, both sides, byte-identical
traces) and the L2 checkpoint gate pass unchanged. `probe_global_state.lua`
already used `probe_common.lua` and was not touched.
`test_l2_keyseq.py::test_the_semantically_shared_parts_of_the_two_probes_are_identical`
— which pinned five of those regions as *text* and policed the duplication —
is replaced by
`test_the_semantically_shared_parts_of_the_probes_are_one_implementation`,
which asserts the strictly stronger property: the bodies exist once, both
probes obtain them, and neither re-declares them.

### 5.8 Cost

Standalone: the CLI over all 13 leaves is **5.70 / 5.78 / 5.74 s** wall for an
input of **182 enumerated assignments over 13 protos / 8 corpus files**, of
which 106 are adjudicated — 230 drive subprocesses plus 11 discover. About
3.3 s of that is the first `decompile_file` of `snr_common.lua`, not the
driving. **The cost is data-driven and the quantity it grows with is the
enumerated product**, `prod(domain sizes)`, which is exponential in the
channel count. That is exactly what the `budget-exceeded` refusal bounds, at
`BUDGET = 4096` per proto, and it is the self-imposed bound this instrument
ships with. Measured throughput on a warm decompile
(`snr_mainmenu.lua:main_7`, 128 assignments driven both sides): **256 drives
in 0.76 s = 338 drives/s**, so a proto sitting exactly at the budget would be
8192 drives ≈ **24 s** on this host.

`pytest tests/test_probe_enum.py` with the corpus is **7.17 s / 37 tests**, of
which **5.63 s** is the full-population gate (3.3 s of that is the first
`decompile_file` of `snr_common.lua`), **0.62 s** the distinct-trace census
(original side only, no decompile) and **0.09 s** the bounded single-proto
demonstration on `snr_music.lua:main_3`.

In the suite, alternating A/B, four rounds across two review rounds, both
corpus variables set: `without` **52.40 / 53.74 / 52.71 / 50.85 s**, `with`
**55.05 / 55.97 / 54.54 / 59.68 s**. The apparent delta is 1.8–2.7 s on the
closest pairs — smaller than the standalone figure, because the corpus files
this gate decompiles are decompiled by other tests in the same process and
`structured._CERT_CACHE` is process-level. **It is not resolvable against host
noise**: the `with` arm's own spread is 5.14 s, twice the delta, and the two
ranges nearly touch. Unlike §4.8's loss-sweep A/B (`without` spread 0.26 s)
this one does not clear the bar, so **the 7.17 s standalone figure is the only
sound bound**. Suite goes **959 → 996** tests. Bare, with neither corpus
variable set: **876 passed, 120 skipped in 9.59 s**; 31 of the 37 new tests run
there. This is M6 formal-verification instrument
cost — it is the instrument the amendment asked for, and it is a standing gate
over the population Task 11 will change.

### 5.9 Scope note, and the smaller dispositions

**The brief's predecessor-recompiled arm is not here.** Task 7's original Step
3 asked for three-way driving — original vs predecessor-recompiled (Track 1)
and original vs our artifact. `probe_enum._payload` accepts `original` and
`decompiled` only. That arm belonged to the corpus-wide Class-1 run the
2026-08-14 amendment moved to M7, and §3/§4 already adjudicate the
predecessor corpus statically with better yield; adding a third side to a
feasibility demonstration would have been surface with no consumer. Recorded
as dropped rather than left implicit.

Smaller things, each recorded rather than silently accepted:

* **`_entry_for` picks `hits[0]`** when a proto is published under several
  names. The names denote the same function, so driving either drives the
  proto — but the whole hit list now rides on `EnumVerdict.entries` so the
  choice is visible. No corpus row has more than one (measured over all 13).
* **`|` and `\` in an access-path key** are hex-escaped by *both* renderings
  (`probe_enum.lua::path_text` and `probe_enum.py::path_text_of`) because the
  trace line passes through the probe's `esc`, which rewrites exactly those
  two bytes; without the escape the driver could never match its own `R|`
  event and every verdict would be a spurious `never-reached`. Unreachable on
  this corpus (`non_identifier_names == 0`), so it is covered synthetically.
* **A non-finite comparison constant** would render as `inf` under `%.17g`,
  and the probe's `tonumber` reads that as `nil` — a silently wrong
  assignment. `encode_value` now refuses it. Unreachable here; synthetic test.
* **`probe_common.py::adjudicate_pins`** was annotated `dict[str, tuple[str,
  str]]` while two of its three callers already passed something else
  (`probe_behaviour.py` passes `bytes` pairs on purpose). Widened to
  `dict[str, tuple]` with the reason recorded; only `==` is ever applied.
* **The no-Lua-patterns rule** was asserted per probe against each probe's own
  `PROBE` path, so the ~460 driver lines that moved into `probe_common.lua`
  were covered by nothing. `test_no_lua_patterns_in_the_probe` is now
  parametrised over both files.

## 6. Milestone summary (task 13)

Every figure in this section was **re-measured at the closing tree on
2026-08-14** unless it is explicitly attributed to an earlier task. Where a
figure from an earlier section did not reproduce, §6.6 says so rather than
quietly restating it.

### 6.1 The exit clauses, one by one

The spec's exit conditions
(`docs/superpowers/specs/2026-08-13-m6-cross-corpus-validation-design.md` §3),
with the verdict and the evidence for each:

| spec §3 clause | verdict | evidence |
|---|---|---|
| Track 1.0 observation complete: per-proto class list + interaction surfaces committed | **met** | `corpus/observation/classes.json`, **156 candidates** = 29 leaf refusals + 132 CAP dominants (5 in both); classes `choice-branch` 113 / `neither` 34 / `ui-keyloop` 9. Gated by `tests/test_m6_exit.py::test_m6_exit_observation_covers_every_leaf_refusal` (a ledger↔`classes.json` join) and `..._every_cap_file`, plus `tests/test_observation_classes.py`'s corpus-gated fixed point |
| Track 1 harness landed; full-corpus scan of the fingerprint / L1.5 / L1.75 arms | **met** | `scripts/cross_corpus.py --arm all` over 229 files; §2 |
| Class-1 enumerated differential over the observed-enumerable protos | **re-scoped 2026-08-14**, met in its amended form | `scripts/probe_enum.py`, exhaustive over the **13** compound-`if` leaves with explicit `budget-exceeded` rows and no silent sampling; §5. The corpus-wide run is M7 agenda 8 |
| Class-2: design + prototype | **re-scoped 2026-08-14**, met in its amended form | `docs/reports/m6-uiloop-design.md`, assumptions labelled measured / unmeasured. The prototype is M7 agenda 9 |
| divergence queue adjudicated row by row, verdicts committed as pins | **met** | `cross_corpus.PRED_PINS`: **18 rows over 16 files**, **6 `real-bug` / 12 `equivalent-transform`**, 0 `probe-artifact`, **0 `suspect`**; §3. Gated by `tests/test_m6_exit.py::test_m6_exit_every_divergence_is_adjudicated` and by `tests/test_cross_corpus.py`'s pin gate |
| Track 2 (structure reference + LLM meta-reconstruction) over the leaf refusals | **dropped 2026-08-14 — premise falsified by measurement** | `build_sir` structures **12 of the predecessor's 13** corresponding leaves (92.3%) after task 11, so the mechanical reference is nearly free and the ~1–2M-token pass buys nothing. Spec §2 decision table |
| Track 3: the two named defects closed, or re-characterised with a measurement | **met, as a partial with the residual named** | compound `if`: `structure:` family **21 ledger shapes → 1** (task 11). Register classification: two of **five** measured mechanisms closed (task 12); the other three are M7 agenda 1 with their row counts |
| suite discipline | **met** | **1077 tests**; ceiling was raised from 45s to a ~120s earmark by the human partner on 2026-08-13. Measured at the wrap: **55.07-55.61s over three runs** (macOS 15.2 / Apple M4, arm64) |
| **no** 0.997 gate; quality stays an observable | **met by decision** | spec §2 decision table; measured **0.977328**, reported by `scripts/quality_score.py` and the dashboard, gated by nothing |

### 6.2 The headline: six defects, and two repair rounds

Six defects confirmed in the predecessor's shipped output, **four previously
unknown**, each walked at instruction level (§3.4, §4.2). Two of them —
`snr_common.lua:main_76_2`'s unconditional `break` and empty `else` — are
**verbatim the two historical checkpoints in the predecessor project's own
debug playbook**, which is the strongest available statement that this corpus
is a live oracle and not a museum piece.

**All six were found by the static arm, and five of the six are invisible to
both dynamic arms** (§3.8): `snr_mainmenu:main_7` returns `agree` on an
18-event behaviour run, and `snr_common.lua`'s behaviour row is silent at
`truncated:1/79`.

Two out-of-plan tasks repaired all six by hand under `corpus/pred_repairs/`
(task X: `snr_music.lua`, `snr_common.lua:main_76_2`; task X2: the other
four), each verified at instruction level and at runtime with a bespoke
driver. What was deliberately **not** repaired is listed in that directory's
README — the duplicated loop tail in `main_76_2` and the three-poll
fall-through it causes, the `cursor row == 6` arm, and byte fidelity anywhere
(two of four instruction counts moved closer to the original, two moved
further: the repairs buy behaviour, not bytes). `$PYLUADEC_PRED_CORPUS_DIR` was
not modified, and the only mention of the repair directory anywhere in `src/`,
`tests/` or `scripts/` is one comment in `scripts/cross_corpus.py` saying it is
**not** an input (grepped 2026-08-14).

### 6.3 Where our own decompiler ended up

| | M6 start (`0957364`) | M6 wrap | gate |
|---|---|---|---|
| `L3`, unique shapes | 1430/1478 (96.8%) | **1438/1478 (97.3%)** | `tests/test_m6_exit.py`, floor 0.96 |
| `L3`, occurrences | 1896/1944 (97.5%) | **1904/1944 (97.9%)** | `tests/test_m5_exit.py`, floor 0.96 |
| occurrences shipping structured text | 1747/1944 (89.9%) | **1763/1944 (90.7%)** | `tests/test_m5_exit.py`, floor 0.85 |
| files fully structured / hybrid / whole-file fallback | 216 / 6 / 7 | **217 / 8 / 4** | not gated (data) |
| ported quality metric | 0.968833 | **0.977328** | `tests/test_m5_exit.py`, floor 0.96 — **not** 0.997 |
| non-`L3` ledger rows | 48 | **40** (29 own + 11 inherited) | — |

`scripts/ratchet_diff.py` against `0957364`: **8 upgraded, 0 downgraded**, 16
occurrences moved fallback → structured, none the other way.
`./scripts/ratchet_job.sh` exits 0 (its default baseline was moved from
`eb08890` to `0957364` at this wrap — the same line always claimed to name the
last merged milestone tip, and M5's merge had not been picked up).

### 6.4 The three decision-log rows

All three modify clauses the user confirmed section by section, so all three
are recorded in
`docs/superpowers/specs/2026-08-09-pyluadec-refactor-overall-design.md` §2 and
not only here.

1. **`avg_score 0.997` is no longer a gate anywhere** (2026-08-13). Not
   because it was out of reach — the reason is that M6 measured it to be
   uncorrelated with defect detection: `semantic_score`'s `cfg_reachable`
   component scores exactly **1.0** on `snr_common.lua:main_75`, the proto
   whose only loop the predecessor had deleted (§4.4, §4.7).
2. **Tasks 7 and 8 re-scoped** (2026-08-14), on the three measurements in
   §6.1's table plus the one that falsified Task 8's framing.
3. **Tasks 9 and 10 dropped** (2026-08-14), premise falsified. If a future
   population ever shows `build_sir` failing on the predecessor side at a
   materially lower rate than 92.3%, the argument returns and that measurement
   is the thing to re-run first.

### 6.5 Deferred minors, disposed of at the wrap

None was dropped silently. Each is fixed, re-deferred with a reason, or closed
as wrong with the measurement.

* **Task 2 — `tests/conftest.py::pred_compiled` defaulted to `strip=False`.**
  **Fixed.** The fixture's callable now takes `strip` as a required
  keyword-only argument and keys its cache on it. A naive consumer would
  otherwise have reintroduced the manufactured `upvalues`-tuple-length
  mismatch on all **260** `nups > 0` protos — the artifact that inflated §1's
  round-0 census. Measured at the wrap: the fixture had **zero consumers**, so
  the change costs nothing and removes the trap before it has a victim.
* **Task 2 — a 1–2s suite delta attributed to "the extra `carries_debug`
  walk".** **Closed as wrong**, on the task-2 review's own re-measurement,
  which found cross-day host variance rather than a walk over 229 files. It is
  recorded here because the task report that carried the claim is not a
  committed artifact and would otherwise take the correction with it. This
  session's independent corroboration of the variance: four interleaved
  full-suite runs on trees differing by one 13-test file measured 55.79 /
  56.47s (without) against 56.73 / 56.81s (with), a spread inside the arms
  comparable to the difference between them.
* **Task 4 — `loop_polls_per_iteration` overstates, and
  `mechanical.footprint` is a projection.** **Documented rather than fixed**,
  because both fixes regenerate a committed artifact and the wrap's own
  constraint was that `corpus/observation/*.json` must not move. Both now have
  a section in `scripts/observation_classes.py`'s module docstring — where a
  consumer reads — with the figures re-derived this session: the dominance
  reading holds for **116 of the 125** flagged records (the nine exceptions
  named), and **142 of 156** candidates have `unattributed_calls > 0` (908
  sites), invisible in the 7-key projection. Renaming/joining is M7 agenda 6.
* **Task 7 — `classes.json`'s `input_space` is not a sizing figure.**
  **Already fixed in place** by task 7 (in `observation_classes.py`'s
  "Channels and input space" section) and **re-derived here**: corpus-wide
  within budget is **1936 of 1944**, `choice-branch` **106 of 113**. See the
  note added under §5.3's table for what moved when the candidate population
  shrank.
* **Task 12 — the residual's unattributed shapes and mechanisms C/D/E.**
  **Re-deferred, with the accounting reconciled** (M7 agenda 1): 40 rows = 29
  own refusals + 11 inherited; 9 rows attributed (6 `_same_block`, of which one
  is the inherited `snr_story_main:main`; 3 clamp); **21 own + 10 inherited
  unattributed**. The two circulating figures are the same fact under
  different denominators: `docs/runbooks/structured-pipeline.md` says "31 of
  the 40 unattributed", counting rows; "21" counts own refusals only. Both are
  correct and neither is complete without saying which.
* **Standing, out of milestone scope — M1's Linux x86_64 verification.**
  **Re-deferred and flagged at the wrap** (M7 agenda 7): unchanged since
  2026-08-10, macOS arm64 only, and `docs/runbooks/64bit-migration.md`
  requires both platforms.

### 6.6 Numbers from earlier sections that did not reproduce at the wrap

* **The candidate population is 156, not 162.** Tasks 11 and 12 closed leaf
  refusals after task 4 and task 7 ran, and `classes.json` regenerated. Every
  figure quoted over "162 candidates" needs its denominator moved:
  per-iteration polling is **125 of 156** (was 127 of 162 — `choice-branch`
  stays 113/113); the review figure "146 of 162 candidates have unattributed
  calls, 946 total" is **142 of 156, 908 total**; §5.3's candidate rows are in
  the note added there. **Nothing that is quoted over the whole corpus or over
  `choice-branch` moved.**
* **The loss sweep is 3.31s, not 3.5s**, over the same 1944 pairs — inside the
  variance §4.8 already documents, recorded only so the two figures are not
  read as a change.
* **The `_same_block` attribution "6 of the 40" includes one inherited row.**
  Not a retraction — task 12's own list names `snr_story_main:main_3` **and
  its root** — but the root is an ancestor, so the own-refusal share is 5, and
  that is what makes 21 and 31 both correct.

### 6.7 What M6 did not do

The full list is the **M7 agenda** at the end of
`docs/runbooks/m3-backlog.md`, written at this wrap and numbered so its items
can be cited. The headline items: the reconstruction residual's three open
mechanisms (agenda 1); corpus-wide L2, whose reach is still **1 file**, and
the four taint gaps and the truncation residue (agenda 2); the Class-1
corpus-wide enumerated run and the Class-2 prototype, both routed there by the
2026-08-14 amendments rather than abandoned (agendas 8 and 9); and M1's Linux
verification (agenda 7).

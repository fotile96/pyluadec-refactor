# M6 cross-corpus report

This file collects the raw per-file evidence for M6's cross-corpus work.
Section 1 is M6 task 2's deliverable (plumbing + first corpus-wide parity
census against the predecessor's human-verified output); later M6 tasks
append their own sections below it. **This is evidence, not a gate** -- the
task's assertions live in `tests/test_predcorpus.py`; this file exists so the
per-file numbers behind those assertions are inspectable without re-running
anything.

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

Harness: `scripts/cross_corpus.py` (job) + `tests/test_cross_corpus.py` (23
smoke tests, 0.37–0.46 s, corpus-gated). Command and wall-clock:

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
  **271 → 271**, and the opcode delta (GETGLOBAL −8 on one name, GETTABLE −16,
  GETUPVAL −8, MOVE +92, TESTSET 20→0 / TEST 0→20) is textbook hoisting plus
  `or`-chain re-expression.
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

The last two rows are **pinned as blind spots**
(`test_fingerprint_arm_is_blind_to_statement_level_edits`, parametrised): a
deleted statement and a dropped argument leave every control-flow component at
1.0 and every sensitivity threshold unbreached. No threshold on
`semantic_score._cfg_shape` reaches a statement-level edit. The behaviour arm
catches the deletion (asserted in the same test); **nothing in this harness
catches the dropped argument.** Read §2.2's queue with that bound in mind.

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
`opcode_family` — nothing else.** Lowest non-queued proto score **0.9882**
(`snr_e2_10_s.lua:main_2_0` and four `snr_s1_10_s.lua` siblings).

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

### 2.8 Suite-cost attribution

`tests/test_cross_corpus.py`: **23 tests**, 0.37–0.46 s measured standalone
(round 0 had 16 at 0.28–0.33 s).

**Within-batch A/B** (the only comparable form on this host), alternating
`--ignore=tests/test_cross_corpus.py` with the full suite, twice each in one
batch. pytest-reported totals:

| | run 1 | run 2 | mean |
|---|---:|---:|---:|
| round 0, without (901 tests) | 44.85 s | 44.68 s | 44.77 s |
| round 0, with (917) | 45.15 s | 45.44 s | 45.30 s |
| round 1, without (917) | 44.67 s | 44.58 s | 44.63 s |
| round 1, with (940) | 44.56 s | 44.91 s | 44.74 s |

Round-0 delta **+0.53 s**; round-1 delta **+0.11 s**. **Do not read the second
number as the first one getting cheaper.** The two arms overlap: round 1's
`with` runs span 44.56–44.91 s and its `without` runs span 44.58–44.67 s, so
the delta is at the edge of this host's run-to-run noise and the honest bound
is the standalone figure — **this module costs at most ~0.46 s**, and most of
that is absorbed by session fixtures (`pred_corpus_dir`, the oracle compile
memo) the suite already builds for `test_predcorpus.py`. Round 0's +0.53 s
should be read the same way.

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
consistent with the localization's purpose.* Distinguishing evidence: the
difference is confined to constants or to an asset reference, the surrounding
control flow and call-target multiset are identical, and there is a
corresponding change in the shipped ISO's assets.

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

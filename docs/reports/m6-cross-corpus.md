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

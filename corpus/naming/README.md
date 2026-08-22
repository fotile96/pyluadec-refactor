# `corpus/naming/` -- the naming-alignment channel (M8)

Aligns our decompiled output's naming surface with the old project's
post-rename artifacts (`/Users/fotile96/pyluadec/post_process/stage1_output/`,
downstream `Zndnovel/lua_scripts/`), so the translation assets keyed by
function names re-anchor onto our output unchanged.

## Files

| file | what |
|---|---|
| `harvest_naming.py` | the generator: ports the old readable names onto our `(file, proto_path, register)` coordinates. Refuses (exit 1, nothing written) on any ambiguous port. `--check` asserts the committed table is a fixed point. |
| `name_map.jsonl` | the table (generated; 1754 rows). One JSON object per line: `file`, `path`, `reg`, `name`, `kind` (`function`/`param`), `anchor`, `flags`. Never hand-edited. |
| `verify_naming.py` | the guard command: P1 byte identity (229/229 finals vs originals, survey §8.2 normalizer), table fixed point, flag completeness. `--tamper` runs the neuter demos. |
| `build_unit_map.py` | T2: joins the old translation units (`post_process/translation_ir/` directory names only -- no unit content is read, those `meta.json` files carry game text) with the table, producing `unit_map.jsonl`. |
| `unit_map.jsonl` | the translation-asset migration artifact: old unit id -> new unit id + our coordinates + defect-zone flags. |

## What is aligned (measured 2026-08-18, see `docs/reports/m8-naming-t0.md`)

* **Function names, 846** -- all main-level readable names across 161 files
  (`scene_*`, `card_*`, dispatch/shared/helper variants). Aligned on the
  CLOSURE instruction's Bx operand (the subproto index, identical on both
  sides by M6 tree parity), not on register numbers (the old text never
  recompiles instruction-identical -- M6 measured 3903 substantive code
  mismatches corpus-wide -- so register correspondence is not a thing).
* **Parameters, 908** (454 `scene_id` + 454 `scene_title`) -- positional;
  `numparams` parity measured on all 229 files.
* **Not aligned, by partner decision (2026-08-18)**: the old project's own
  auto-names (`v\d+`/`p\d+` locals and params, `i\d+`/`g\d+` iterator
  temps, `arg`, `(for ...)` internals). Our `l<depth>_<reg>` spellings stay
  for those. The old text's self-reference `local NAME` inside a function
  is our `local function` sugar; those names arrive with the parent's row.

## The runtime wiring

`src/pyluadec/structure/naming.py` loads the table;
`emit/lua.py`'s `Printer.local_name` consults it at every site that would
synthesize `l<depth>_<reg>` (declarations, references, child params,
captured-upvalue naming); misses fall back to the synthesized spelling.
`pipeline.decompile_file` threads the file's table automatically, so the
probes and every shipped artifact see the same named surface.

Safety is not a separate checker: the table rides the ordinary print
path, so a rename that changes name resolution changes the compiled
bytecode and is refused by the certification ladder itself (a degraded
ledger row, never a shipped wrong name). The committed artifact is
additionally guarded by `verify_naming.py`'s P1 scan (229/229
byte-identical, re-run after any regeneration).

## Regeneration

```sh
export PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/script_to_decompile
uv run python corpus/naming/harvest_naming.py            # (re)write the table
uv run python scripts/run_corpus.py                      # ledger (must be a no-op diff)
PYLUADEC_PRED_CORPUS_DIR=/Users/fotile96/Zndnovel/lua_scripts \
  uv run python scripts/warranty_build.py --all          # corpus/final + warranty
uv run python corpus/naming/verify_naming.py             # all three guards
uv run python corpus/naming/build_unit_map.py            # T2 unit map
```

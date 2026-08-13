"""预测语料（predecessor corpus）插件测试 -- M6 任务 2。

`PYLUADEC_PRED_CORPUS_DIR` 指向前身项目（`/root/pyluadec`）产出并被人类通关验证过的
229 个反编译 Lua **源码**文件（`/Users/fotile96/Zndnovel/lua_scripts`），与本项目的
229 个字节码文件（`PYLUADEC_CORPUS_DIR`）同名。这个文件先证明插件本身能用（Step 1：
`snr_common.lua` 编译后的 proto 树与原始字节码逐 proto 路径一致），再跑全语料 229
文件的普查（Step 3，任务真正的交付物）：compile-ok 计数、树形状匹配计数、以及排除
debug 字段后的 rung-1 实质性 mismatch 分布。

Certification logic (`verify.normalize.compare_protos` 及其 `NORMALIZATIONS`/
`LADDER_VERSION`) is read here, never modified -- this file only counts what it
already reports and controls what it FEEDS the comparison (strip mode of the
predecessor compile -- see `_census_one`).

**Comparison level: `level=1`** (the `L3.1` strip-lineinfo rung, same rung
`verify.certify.certify_l3` uses), matching what this module's own prose and
`docs/reports/m6-cross-corpus.md` describe. Measured directly (round 1,
2026-08-13, after the strip-mode fix below): `level=0` and `level=1` produce
byte-identical `total_substantive`/`total_paths` on this corpus, because
`_strip_lineinfo` only neutralises `source`/`linedefined`/`lastlinedefined`/
`lineinfo`/locvar-and-upvalue-NAMES, and every one of those fields is either
already excluded by `DEBUG_FIELDS` below or (post strip-mode-fix) already
identical on both sides before normalisation runs. `level=1` is still the one actually called: choosing the rung that matches
the prose costs nothing here, but "costs nothing either way, so match the
docs" is not the same claim as "the level is irrelevant" -- a corpus where
the original carried real debug info would make the two levels diverge, and
this file should keep matching what it says it does.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

# Debug-only fields per the task brief. The brief named "upvalue_names",
# which does not exist as a `Proto` field or a `Mismatch.field` string --
# `verify.normalize._cmp` calls its whole-tuple upvalue comparison
# "upvalues". Round 1 (2026-08-13) fixed a real bug here, but NOT by adding
# "upvalues" to this set: that field's tuple LENGTH is functional (it is what
# `nups` counts), so filtering it out would hide genuine frame-shape
# disagreements, not just debug noise. The actual defect was that the
# predecessor side was always compiled unstripped while the original corpus
# is always stripped (`carries_debug` is False for all 1944 protos), so every
# upvalue-bearing proto (260 of them) got a manufactured length mismatch —
# empty tuple vs. a full one — regardless of whether the two chunks agreed on
# anything. Fixed at the source in `_census_one`, by compiling the
# predecessor side with the same strip mode as the original
# (`verify.certify.certify_l3`'s own precedent: `strip=not
# carries_debug(original)`), so both sides carry the same (empty, here)
# upvalue/locvar/lineinfo tables and only genuine `nups`/`code`/`constants`/
# `maxstacksize`/etc. disagreements remain "upvalues" mismatches at all.
#
# **Measured (round 1, neuter proof): this filter is currently a no-op on
# this corpus at level=1.** Disabling it (`substantive = list(mismatches)`)
# produces the exact same `total_substantive == 3903` as filtering it.
# Two different reasons, not one: `_strip_lineinfo` (verify/normalize.py)
# unconditionally forces `source`/`linedefined`/`lastlinedefined`/`lineinfo`
# to the SAME fixed value on both sides before `_cmp` ever runs, so those
# four can never produce a `Mismatch` at level>=1 on ANY corpus -- that part
# is a structural fact, not one this corpus happens to exhibit. `locvars` is
# different: `_strip_lineinfo` keeps each locvar's count/pc-range (only
# blanks the name), so a `locvars` mismatch IS possible at level 1 in
# general -- it merely does not occur HERE, because this corpus's original
# is always stripped (`locvars == ()` on every proto) and the strip-mode fix
# now makes the predecessor side match. Kept anyway, not deleted: it is what
# the brief asked for, it is what a `level=0` comparison (raw, no
# normalisation) would actually need, and it documents the five fields whose
# disagreement is DEBUG information rather than a difference in what the two
# chunks compute -- even though none of them is what is currently doing the
# work on this specific corpus at level=1. The `_field_category`/
# `substantive_signals` uniform measure below is unaffected either way.
DEBUG_FIELDS = {"source", "lineinfo", "locvars", "linedefined", "lastlinedefined"}


def _field_category(field: str) -> str:
    """Collapse `compare_protos`' per-element field names to one bucket per
    semantic dimension.

    `_cmp` (verify/normalize.py) records AT MOST ONE `Mismatch` for `code`,
    `maxstacksize`, `nups`, `numparams`, `is_vararg`, `upvalues`,
    `constants.len` -- but ONE PER DIFFERING INDEX for `constants`
    (`"const[3]"`, `"const[17]"`, ...). Raw mismatch counts therefore mix a
    coarse per-proto flag with a fine per-element count: a proto whose only
    disagreement is a handful of differing string constants can outweigh one
    whose entire `code` array diverges. This collapses every `"const[i]"`
    (and `"constants.len"`) into one `"constants"` bucket so a
    distinct-`(path, category)` count treats "this proto's constants differ"
    as ONE signal, comparable to "this proto's `code` differs" being one
    signal -- see `_FileCensus.substantive_signals` / the module docstring's
    reviewer-requested granularity caveat.
    """
    if field.startswith("const[") or field == "constants.len":
        return "constants"
    return field


def test_load_pred_proto_snr_common_tree_matches_original(corpus_dir, pred_corpus_dir):
    """Step 1 (brief): compiling `snr_common.lua` from the predecessor corpus
    and ingesting it produces a proto tree with 147 protos whose
    `pipeline.walk_proto_paths` paths match the original bytecode's exactly.
    """
    from pyluadec import ingest
    from pyluadec.predcorpus import load_pred_proto, tree_paths

    orig = ingest.load_file(corpus_dir / "snr_common.lua")
    pred = load_pred_proto(pred_corpus_dir, "snr_common.lua")

    orig_paths = tree_paths(orig)
    pred_paths = tree_paths(pred)

    assert len(orig_paths) == 147
    assert len(pred_paths) == 147
    assert pred_paths == orig_paths


@dataclass(frozen=True)
class _FileCensus:
    name: str
    proto_count: int
    compiled: bool
    compile_error: str | None
    tree_match: bool
    substantive_mismatches: int   # raw Mismatch count, DEBUG_FIELDS excluded
    substantive_paths: int        # distinct proto paths carrying >=1 of those
    substantive_signals: int      # distinct (path, category) pairs -- see _field_category


def _census_one(corpus_dir, pred_corpus_dir, name: str) -> _FileCensus:
    from pyluadec import ingest
    from pyluadec.predcorpus import load_pred_proto, tree_paths
    from pyluadec.oracle import OracleError
    from pyluadec.verify.certify import carries_debug
    from pyluadec.verify.normalize import compare_protos

    orig = ingest.load_file(corpus_dir / name)
    orig_paths = tree_paths(orig)
    try:
        # Strip mode follows the ORIGINAL, matching verify.certify.certify_l3's
        # own precedent -- see load_pred_proto's docstring and this module's
        # DEBUG_FIELDS comment for why compiling the predecessor unconditionally
        # unstripped (round-1 defect) manufactured 260 fake upvalue mismatches.
        pred = load_pred_proto(pred_corpus_dir, name, strip=not carries_debug(orig))
    except OracleError as e:
        return _FileCensus(name, len(orig_paths), False, str(e)[:200],
                            False, -1, -1, -1)

    pred_paths = tree_paths(pred)
    tree_match = pred_paths == orig_paths
    mismatches = compare_protos(orig, pred, level=1)
    substantive = [m for m in mismatches if m.field not in DEBUG_FIELDS]
    signals = {(m.path, _field_category(m.field)) for m in substantive}
    return _FileCensus(
        name, len(orig_paths), True, None, tree_match,
        len(substantive), len(set(m.path for m in substantive)), len(signals),
    )


def _run_census(corpus_dir, pred_corpus_dir) -> list[_FileCensus]:
    names = sorted(f.name for f in corpus_dir.glob("*.lua"))
    return [_census_one(corpus_dir, pred_corpus_dir, n) for n in names]


def test_corpus_wide_parity_census(corpus_dir, pred_corpus_dir):
    """Step 3 (brief), the task's real deliverable: over all 229 files, how
    close is the predecessor's human-verified output to the true original
    bytecode this project also ingests? Corpus-gated, not a standalone
    script, because the whole pass (229 compiles + ingests + rung-1
    compares) measured 2026-08-13 at well under a second (~0.73s cold on
    this host, round 1) -- see the report for the measured suite-cost delta.

    Only the headline totals are pinned here as regression assertions; the
    full per-file table lives in `docs/reports/m6-cross-corpus.md` §1
    (regenerable via this file's `__main__` arm, see bottom of file).

    **Granularity caveat (round 1, reviewer Important finding).**
    `substantive_mismatches`/`total_substantive` mixes a coarse per-proto
    flag (`code`, `maxstacksize`, ... -- `_cmp` records at most one
    `Mismatch` each) with a fine per-element count (`constants` -- one
    `Mismatch` per differing index), so it is not a uniform "how different"
    measure across files: a file whose divergence is concentrated in many
    differing constants outweighs one whose only divergence is its `code`
    array, even if the latter is a "bigger" disagreement in every intuitive
    sense. `total_paths` (distinct proto paths carrying >=1 substantive
    mismatch) is already closer to uniform -- a proto counts once no matter
    how many fields disagree -- but does not distinguish "one field differs"
    from "every field differs". `total_signals` (`substantive_signals` per
    file, via `_field_category`) is the additional uniform measure: distinct
    `(path, category)` pairs, with every `"const[i]"` collapsed into one
    `"constants"` bucket per proto, so each semantic dimension counts once
    per proto regardless of how many elements within it differ. Report all
    three; none of them alone is "the" answer.
    """
    rows = _run_census(corpus_dir, pred_corpus_dir)
    assert len(rows) == 229

    compile_ok = sum(1 for r in rows if r.compiled)
    tree_match = sum(1 for r in rows if r.compiled and r.tree_match)

    # Pin only what was actually measured -- if a future run of this test
    # sees a different corpus content (either directory), THAT is the
    # finding; do not weaken these to "make it green" per the brief.
    assert compile_ok == 229, (
        f"{229 - compile_ok} predecessor file(s) failed to compile: "
        f"{[(r.name, r.compile_error) for r in rows if not r.compiled][:5]}")
    assert tree_match == 229, (
        f"{229 - tree_match} file(s) have a proto-tree shape that does not "
        f"match the original: "
        f"{[r.name for r in rows if r.compiled and not r.tree_match][:5]}")

    total_substantive = sum(r.substantive_mismatches for r in rows if r.compiled)
    total_paths = sum(r.substantive_paths for r in rows if r.compiled)
    total_signals = sum(r.substantive_signals for r in rows if r.compiled)
    # Re-derived round 1 (2026-08-13) after the strip-mode fix: 4163/1443 (the
    # values pinned before the fix) included 260 upvalue-length mismatches
    # manufactured by comparing a stripped original's empty upvalue-name
    # tuple against an unstripped predecessor recompile's full one -- an
    # artifact of HOW the two sides were compiled, not a real disagreement.
    assert total_substantive == 3903
    assert total_paths == 1433
    assert total_signals == 2989

    # No file is a perfect (0-mismatch) recompilation of the true original --
    # measured, not assumed; re-derive if this ever flips (it would be good
    # news, not a bug).
    zero_mismatch = [r.name for r in rows if r.compiled and r.substantive_mismatches == 0]
    assert zero_mismatch == []


if __name__ == "__main__":
    # Script arm (brief step 3's "script arm inside the test file"): print the
    # full per-file table used to populate docs/reports/m6-cross-corpus.md §1,
    # without pytest's output capture getting in the way. Reads the same two
    # env vars as the fixtures, but does not go through pytest.skip -- run
    # this directly (`uv run python tests/test_predcorpus.py`) with both set.
    import os
    import sys
    from pathlib import Path

    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    pred = os.environ.get("PYLUADEC_PRED_CORPUS_DIR")
    if not corpus or not Path(corpus).is_dir():
        sys.exit("PYLUADEC_CORPUS_DIR not set or missing")
    if not pred or not Path(pred).is_dir():
        sys.exit("PYLUADEC_PRED_CORPUS_DIR not set or missing")

    rows = _run_census(Path(corpus), Path(pred))
    print(f"{'file':<24}{'protos':>7}{'compiled':>10}{'tree_match':>12}"
          f"{'substantive':>13}{'paths':>7}{'signals':>9}")
    for r in rows:
        print(f"{r.name:<24}{r.proto_count:>7}{str(r.compiled):>10}"
              f"{str(r.tree_match):>12}{r.substantive_mismatches:>13}"
              f"{r.substantive_paths:>7}{r.substantive_signals:>9}")
    ok = sum(1 for r in rows if r.compiled)
    tm = sum(1 for r in rows if r.compiled and r.tree_match)
    tot = sum(r.substantive_mismatches for r in rows if r.compiled)
    totp = sum(r.substantive_paths for r in rows if r.compiled)
    tots = sum(r.substantive_signals for r in rows if r.compiled)
    print(f"\ncompile_ok {ok}/229  tree_match {tm}/229  "
          f"total_substantive {tot}  total_paths {totp}  total_signals {tots}")

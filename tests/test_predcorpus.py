"""预测语料（predecessor corpus）插件测试 -- M6 任务 2。

`PYLUADEC_PRED_CORPUS_DIR` 指向前身项目（`/root/pyluadec`）产出并被人类通关验证过的
229 个反编译 Lua **源码**文件（`/Users/fotile96/Zndnovel/lua_scripts`），与本项目的
229 个字节码文件（`PYLUADEC_CORPUS_DIR`）同名。这个文件先证明插件本身能用（Step 1：
`snr_common.lua` 编译后的 proto 树与原始字节码逐 proto 路径一致），再跑全语料 229
文件的普查（Step 3，任务真正的交付物）：compile-ok 计数、树形状匹配计数、以及排除
debug 字段后的 rung-1 实质性 mismatch 分布。

Certification logic (`verify.normalize.compare_protos` 及其 `NORMALIZATIONS`/
`LADDER_VERSION`) is read here, never modified -- this file only counts what it
already reports.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

# Debug-only fields per the task brief -- these are the ones `_strip_lineinfo`
# (verify/normalize.py, rung 1) neutralises to a fixed value on both sides, or
# that are otherwise about names/debug info rather than the VM's semantics.
# Note the brief's field name is "upvalue_names"; `verify.normalize._cmp`
# actually names that comparison "upvalues" (it compares the whole
# now-name-stripped tuple, which still carries the upvalue COUNT -- see that
# module's docstring) -- so "upvalues" is deliberately NOT in this set, and a
# count mismatch there counts as substantive.
DEBUG_FIELDS = {"source", "lineinfo", "locvars", "upvalue_names",
                "linedefined", "lastlinedefined"}


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
    substantive_mismatches: int
    substantive_paths: int


def _census_one(corpus_dir, pred_corpus_dir, name: str) -> _FileCensus:
    from pyluadec import ingest
    from pyluadec.predcorpus import load_pred_proto, tree_paths
    from pyluadec.oracle import OracleError
    from pyluadec.verify.normalize import compare_protos

    orig = ingest.load_file(corpus_dir / name)
    orig_paths = tree_paths(orig)
    try:
        pred = load_pred_proto(pred_corpus_dir, name)
    except OracleError as e:
        return _FileCensus(name, len(orig_paths), False, str(e)[:200],
                            False, -1, -1)

    pred_paths = tree_paths(pred)
    tree_match = pred_paths == orig_paths
    mismatches = compare_protos(orig, pred, level=0)
    substantive = [m for m in mismatches if m.field not in DEBUG_FIELDS]
    return _FileCensus(
        name, len(orig_paths), True, None, tree_match,
        len(substantive), len(set(m.path for m in substantive)),
    )


def _run_census(corpus_dir, pred_corpus_dir) -> list[_FileCensus]:
    names = sorted(f.name for f in corpus_dir.glob("*.lua"))
    return [_census_one(corpus_dir, pred_corpus_dir, n) for n in names]


def test_corpus_wide_parity_census(corpus_dir, pred_corpus_dir):
    """Step 3 (brief), the task's real deliverable: over all 229 files, how
    close is the predecessor's human-verified output to the true original
    bytecode this project also ingests? Corpus-gated, not a standalone
    script, because the whole pass (229 compiles + ingests + rung-1
    compares) measured 2026-08-13 at well under a second (~0.67s cold on
    this host) -- see the report for the measured suite-cost delta.

    Only the headline totals are pinned here as regression assertions; the
    full per-file table lives in `docs/reports/m6-cross-corpus.md` §1
    (regenerable via this file's `__main__` arm, see bottom of file).
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
    assert total_substantive == 4163
    assert total_paths == 1443

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
          f"{'substantive':>13}{'paths':>7}")
    for r in rows:
        print(f"{r.name:<24}{r.proto_count:>7}{str(r.compiled):>10}"
              f"{str(r.tree_match):>12}{r.substantive_mismatches:>13}{r.substantive_paths:>7}")
    ok = sum(1 for r in rows if r.compiled)
    tm = sum(1 for r in rows if r.compiled and r.tree_match)
    tot = sum(r.substantive_mismatches for r in rows if r.compiled)
    totp = sum(r.substantive_paths for r in rows if r.compiled)
    print(f"\ncompile_ok {ok}/229  tree_match {tm}/229  "
          f"total_substantive {tot}  total_paths {totp}")

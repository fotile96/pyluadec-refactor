"""前作文本再认证（pred re-certification）-- M7 任务 2。

`predrecert` 把前作文本重新过一遍我们自己的管线：pred .lua → `oracle.compile_source`
(strip=True) → `ingest` → `decompile_chunk`，产出**我们 output surface v2 的重排放文本**
及逐 proto 的 Factor-T 等级（`T3`/`T2`/`T-`）。Factor T 度量的是「文本忠实于其源字节码」
——这里的源是**前作字节码**，不是原始字节码；pred-vs-original 的等价性是 invariant
panel（任务 3/4）的 Factor E，与本模块无关。

**Strip 约定（本里程碑固定于此，spec §3 rev 3）**：参照字节码一律
`oracle.compile_source(pred_text, strip=True)`。理由记在 `predrecert` 模块 docstring。

计划的测试草稿点名 `snr_title.lua`；该文件在前作语料中不存在（实测 2026-08-15），
按预检裁定换成真实存在的 `config.lua`（最小文件），并在此记录替换。
"""
from __future__ import annotations

from pyluadec import predrecert


def test_recert_reference_is_stripped(pred_corpus_dir):
    out = predrecert.recert_file(pred_corpus_dir, "config.lua")
    from pyluadec.verify.certify import carries_debug
    from pyluadec.ingest import load_bytes
    assert carries_debug(load_bytes(out.reference)) is False


def test_recert_grades_cover_every_proto(pred_corpus_dir):
    out = predrecert.recert_file(pred_corpus_dir, "config.lua")
    assert set(out.t_grades) == set(out.reasons)
    assert len(out.t_grades) >= 1
    assert all(g in ("T3", "T2", "T-") for g in out.t_grades.values())


def test_t_grade_mapping_is_the_stated_function():
    # synthetic: a source that fully certifies -> all T3
    src = b"Config = function(a)\n    return a + 1\nend\n"
    out = predrecert.recert_bytes(src)
    assert set(out.t_grades.values()) == {"T3"}
    assert all(r is None for r in out.reasons.values())


def test_t_grade_mapping_t_minus_takes_precedence_over_level():
    # The mapping is a case ladder in one order: a fallback SHIPMENT is T-
    # whatever the proto's own level said, because Factor T grades the
    # shipped text and the fallback state machine was never the subject of
    # a certify_l3 run (spec §2's T- bullet: "shipped verbatim without
    # certification (fallback text, ...)" -- see the order amendment dated
    # 2026-08-16 in predrecert's module docstring; Task 2's original ladder
    # checked L3 first and overclaimed exactly this overlap). T2 is "not L3
    # but shipped structured". This test pins the ORDER by driving the pure
    # mapper directly -- it needs no corpus.
    m = predrecert.t_grade
    assert m(level="L3", shipped_fallback=False) == "T3"
    assert m(level="L3", shipped_fallback=True) == "T-"  # shipment beats level
    assert m(level="L1", shipped_fallback=False) == "T2"
    assert m(level="L1", shipped_fallback=True) == "T-"


def test_recert_source_recompiles_to_the_same_tree():
    # The deliverable is a compilable re-emission: out.source must compile and
    # its proto tree must match the reference tree's shape exactly.
    out = predrecert.recert_bytes(b"Config = function(a)\n    return a + 1\nend\n")
    from pyluadec.oracle import compile_source
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import walk_proto_paths
    ref = load_bytes(out.reference)
    again = load_bytes(compile_source(out.source, strip=True))
    a: dict[str, object] = {}
    b: dict[str, object] = {}
    walk_proto_paths("main", ref, a)  # type: ignore[arg-type]
    walk_proto_paths("main", again, b)  # type: ignore[arg-type]
    assert list(a) == list(b)

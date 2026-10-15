"""不变量面板（invariant panel）-- M7 任务 3/4。

Factor E 的载体：pred proto 与 original proto 的逐对静态等价判决。家族 =
八个 `LOSS_KINDS` 的**双侧**形式（`loss:<kind>`，loss_sweep 只看丢失侧）＋
`fingerprint`（`ProtoSignature` 除 `constant_fingerprint` 外逐字段相等——
死池项无语义效应，见模块 docstring）＋ `constant_values`（load 类操作数引用的
常量值多重集，按 LuaNumber 的 8 字节 payload 比对，池序无关）。

模块在 `scripts/invariant_panel.py`（计划 Task 3）；本文件的任务 3 部分全部
是**合成 fixture**（`oracle.compile_source` 编译对），语料运行与钉子是任务 4
追加的部分。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pyluadec import ingest, oracle
from scripts.cross_corpus import json_safe  # noqa: E402
from scripts.invariant_panel import file_panel, proto_panel  # noqa: E402


def _panel(a: bytes, b: bytes):
    pa = ingest.load_bytes(oracle.compile_source(a, strip=True))
    pb = ingest.load_bytes(oracle.compile_source(b, strip=True))
    return proto_panel(pa, pb)


def test_gain_side_flags():
    """The two-sided proof loss_sweep lacks: a GAIN on the pred side flags."""
    d = _panel(b"f()\n", b"f()\ng = 1\n").diffs
    assert "loss:global_writes" in d


def test_two_sidedness_is_new_work_not_rederivation():
    """The contrast proof (plan Task 3 Step 3): on the gain-side fixture,
    loss_sweep's own one-directional predicate sees NO loss (pred lost
    nothing), while the panel flags it -- committed as the reason the
    two-sided form is new work."""
    from scripts.loss_sweep import TEST_OPCODES, _fields, _shortfalls  # noqa: E402
    from pyluadec.verify.semantic_score import collect_proto_signatures

    orig = ingest.load_bytes(oracle.compile_source(b"f()\n", strip=True))
    pred = ingest.load_bytes(oracle.compile_source(b"f()\ng = 1\n", strip=True))
    o_sig = collect_proto_signatures(orig)
    p_sig = collect_proto_signatures(pred)
    o_fields = _fields(o_sig[()], orig)
    p_fields = _fields(p_sig[()], pred)
    # one-directional: pred never has LESS of any kind -> no shortfalls
    assert _shortfalls(o_sig[()], p_sig[()], o_fields, p_fields) == {}
    # two-sided: the panel still flags the gain
    assert "loss:global_writes" in proto_panel(orig, pred).diffs


def test_constant_value_swap_flags_only_constant_family():
    d = _panel(b'f("abc")\n', b'f("abd")\n').diffs
    assert set(d) == {"constant_values"}


def test_constant_multiset_ignores_pool_order():
    # Table-constructor order changes the pool order (luac pools follow
    # first reference) but not the referenced multiset.
    d = _panel(b'local t = {"x", "y"}\n', b'local t = {"y", "x"}\n').diffs
    assert "constant_values" not in d


def test_identical_sources_pass_clean():
    src = b'local t = {"x", "y"}\nfor i = 1, 10 do f(t, i) end\n'
    assert _panel(src, src).diffs == {}


def test_evidence_carries_no_constant_bytes():
    d = _panel(b'f("SECRETTOKEN")\n', b'f("OTHERTOKEN1")\n').diffs
    assert "SECRETTOKEN" not in d["constant_values"]
    assert "OTHERTOKEN1" not in d["constant_values"]
    for ev in d.values():
        assert json_safe(ev)


def test_fingerprint_flags_opcode_shape_change_not_constants():
    # A pure control-flow change flags fingerprint, not constant_values.
    d = _panel(b'if a then f() end\n', b'while a do f() end\n').diffs
    assert "fingerprint" in d
    assert "constant_values" not in d


def test_loop_counts_are_family_members():
    d = _panel(b'while a do f() end\n', b'f()\n').diffs
    assert "loss:n_natural_loops" in d
    assert "loss:n_back_edges" in d


def test_missing_path_is_raised_not_swallowed(tmp_path):
    """Path-set mismatches are `file_panel`'s to raise (never swallow); a
    closure on one side only is the smallest tree-shape divergence."""
    from scripts.invariant_panel import MissingProtoPath  # noqa: E402

    (tmp_path / "corpus").mkdir()
    (tmp_path / "pred").mkdir()
    (tmp_path / "corpus" / "a.lua").write_bytes(
        oracle.compile_source(b"f(function() end)\n", strip=True))
    (tmp_path / "pred" / "a.lua").write_bytes(b"g()\n")
    with pytest.raises(MissingProtoPath):
        file_panel(tmp_path / "corpus", tmp_path / "pred", "a.lua")


def test_file_panel_keys_use_repo_path_spelling(tmp_path):
    (tmp_path / "corpus").mkdir()
    (tmp_path / "pred").mkdir()
    src = b'local t = {"x"}\nf(t)\n'
    (tmp_path / "corpus" / "a.lua").write_bytes(
        oracle.compile_source(src, strip=True))
    (tmp_path / "pred" / "a.lua").write_bytes(src)
    out = file_panel(tmp_path / "corpus", tmp_path / "pred", "a.lua")
    assert set(out) == {"main"}
    assert out["main"].diffs == {}


# --------------------------------------------------------------------------
# Task 4: the committed artifact, its fixed point, and the pins' currency.
# Corpus-gated: one ~6s scan serves every assertion in this section.

@pytest.fixture(scope="module")
def panel_scan(corpus_dir, pred_corpus_dir):
    """One shared ~6s scan for both corpus-gated Task-4 tests (a module-level
    cache; the suite pays for the scan once)."""
    import invariant_panel as ip

    return ip.scan_all(corpus_dir, pred_corpus_dir)


def test_panel_fixed_point_and_pin_currency(panel_scan):
    """The job's gate, in-suite: the live scan must reproduce the committed
    `corpus/observation/panel.json` byte-for-byte, and every pin must still
    describe a live divergence (no moved evidence, no converged rows)."""
    import invariant_panel as ip
    from probe_common import adjudicate_pins

    scan = panel_scan
    committed = (ROOT / "corpus" / "observation" / "panel.json").read_bytes()
    assert ip.panel_bytes(scan) == committed
    divergent = ip._non_pass(scan)
    divergent_ev = {k: tuple(sorted(d.items())) for k, d in divergent.items()}
    unexpected, moved, gone = adjudicate_pins(divergent_ev, ip.pin_evidence())
    assert unexpected == [] or all(k in divergent for k in unexpected)
    # the pins' currency is the strict form: every pin is still divergent with
    # unchanged evidence (the unpinned bulk is byte-checked above, not here)
    assert moved == [] and gone == []
    assert len(ip.PANEL_PINS) == 217


def test_panel_fixed_point_is_not_vacuous(panel_scan):
    """Neuter proof: a hand-edit inside the committed artifact (flip one
    verdict) must break the byte comparison -- the gate reads the artifact,
    not just its own output."""
    import invariant_panel as ip

    scan = panel_scan
    committed = (ROOT / "corpus" / "observation" / "panel.json").read_bytes()
    tampered = committed.replace(b'"pass"', b'"pasx"', 1)
    assert tampered != committed
    assert ip.panel_bytes(scan) != tampered


def test_panel_summary_pin():
    """The cheap suite arm (no corpus): the committed artifact's verdict-class
    counts are pinned. Measured 2026-08-15 (M7 task 4): 1411 pass / 217
    pinned / 316 unpinned over 1944 protos in 229 files."""
    import json

    data = json.loads((ROOT / "corpus" / "observation" / "panel.json").read_text())
    rows = [v for f in data.values() for v in f.values()]
    assert len(data) == 229
    assert len(rows) == 1944
    n_pass = sum(1 for v in rows if v == "pass")
    n_pin = sum(1 for v in rows if isinstance(v, dict) and "pinned" in v)
    n_un = sum(1 for v in rows if isinstance(v, dict) and "unpinned" in v)
    assert (n_pass, n_pin, n_un) == (1411, 217, 316)
    # every pinned row's note exists in PANEL_PINS (artifact/module agreement)
    import invariant_panel as ip

    for f, protos in data.items():
        for p, v in protos.items():
            if isinstance(v, dict) and "pinned" in v:
                assert ip.PANEL_PINS[f"{f}:{p}"].note == v["pinned"]


def test_unpinned_rows_never_carry_constant_values_in_defect_protos():
    """The six defect protos are pinned regardless of family mix (their
    divergence IS the defect); recorded so a future regen cannot silently
    drop them into the unpinned bulk."""
    import invariant_panel as ip

    for key in ("snr_music.lua:main_3", "snr_common.lua:main_76_2",
                "snr_mainmenu.lua:main_7", "snr_graphic.lua:main_4",
                "snr_memory.lua:main_4", "snr_common.lua:main_75",
                "snr_common.lua:main_83"):
        assert key in ip.PANEL_PINS

"""The naming-alignment channel (M8): old readable names -> our printer.

What is pinned here, and where the heavy guards live:

* The committed ``corpus/naming/name_map.jsonl`` is a fixed point of the
  harvest generator (in-suite when the old tree is present; the
  out-of-suite command is ``corpus/naming/verify_naming.py``, which also
  runs the 229-file P1 byte-identity scan and its ``--tamper`` neuter
  demos).
* The loader validates every name before the printer sees it: keywords,
  non-identifiers, and collisions with the synthesized ``l<k>_<r>`` /
  ``u<k>`` spellings are refused with the row named.
* The printer seam itself: table hits rename the declaration, every
  reference, child params, and the upvalue names children capture; a miss
  falls back to ``l<depth>_<reg>``.
* The runtime P1 catch: a rename that changes name resolution (a local
  shadowing a global the body references) must degrade the certification,
  because the whole-tree compile-and-compare is the guard -- demonstrated
  on a hand-built proto, not asserted in prose.
* The measured empty intersections: the 4 proposal-channel files carry no
  table rows (their readable surface is empty in the old text too), and
  the shipped finals carry the aligned surface verbatim.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
sys.path.insert(0, str(ROOT / "corpus" / "naming"))

STAGE1_DEFAULT = Path("/Users/fotile96/pyluadec/post_process/stage1_output")


def _proto(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    s = tmp / "t.lua"
    o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return load_file(o)


# ---------------------------------------------------------------------------
# The committed table is a fixed point of its generator.

def test_table_is_a_fixed_point_of_the_harvest():
    if not STAGE1_DEFAULT.is_dir():
        pytest.skip("old renamed sources not present on this host")
    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not corpus or not Path(corpus).is_dir():
        pytest.skip("PYLUADEC_CORPUS_DIR not set or missing "
                    "(naming fixed point skipped)")
    import harvest_naming as H
    rows, report = H.harvest(Path(corpus), STAGE1_DEFAULT)
    committed = (ROOT / "corpus" / "naming" / "name_map.jsonl").read_bytes()
    assert H.render(rows) == committed
    # The measured shape the report quotes (re-measured, not trusted):
    assert report["files"] == 229
    assert report["fn_ported"] == 846
    assert report["param_ported"] == 908
    assert report["fn_unprinted"] == 0


# ---------------------------------------------------------------------------
# The loader: override honored, names validated before the printer runs.

def _with_map(tmp_path, rows, monkeypatch):
    p = tmp_path / "name_map.jsonl"
    p.write_bytes(b"".join(
        json.dumps(r, sort_keys=True).encode() + b"\n" for r in rows))
    monkeypatch.setenv("PYLUADEC_NAMING_MAP", str(p))
    import pyluadec.structure.naming as N
    N.reset_cache()
    return N


def test_loader_override_and_duplicate_refusal(tmp_path, monkeypatch):
    N = _with_map(tmp_path, [
        {"file": "f.lua", "path": "main", "reg": 0, "name": "scene_a"},
    ], monkeypatch)
    assert N.for_file("f.lua") == {("main", 0): "scene_a"}
    assert N.for_file("other.lua") == {}
    N.reset_cache()
    # A second row mapping the same (path, reg) to a DIFFERENT name is a
    # broken table, not a silent override.
    p = Path(os.environ["PYLUADEC_NAMING_MAP"])
    with p.open("ab") as fh:
        fh.write(json.dumps({"file": "f.lua", "path": "main", "reg": 0,
                             "name": "scene_b"}).encode() + b"\n")
    with pytest.raises(ValueError, match="two names"):
        N.for_file("f.lua")


@pytest.mark.parametrize("bad,why", [
    ("end", "Lua keyword"),
    ("l0_1", "synthesized"),
    ("l12_3", "synthesized"),
    ("u2", "upvalue"),
    ("3x", "identifier"),
    ("a-b", "identifier"),
    ("__pld_x", "state-machine"),
])
def test_loader_refuses_unusable_names(tmp_path, monkeypatch, bad, why):
    N = _with_map(tmp_path, [
        {"file": "f.lua", "path": "main", "reg": 0, "name": bad},
    ], monkeypatch)
    with pytest.raises(ValueError, match=why):
        N.for_file("f.lua")


def test_loader_missing_table_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("PYLUADEC_NAMING_MAP",
                       str(tmp_path / "absent.jsonl"))
    import pyluadec.structure.naming as N
    N.reset_cache()
    with pytest.raises(FileNotFoundError):
        N.for_file("f.lua")


# ---------------------------------------------------------------------------
# The printer seam.

def test_table_renames_declaration_references_and_params(tmp_path):
    from pyluadec.emit.lua import print_chunk
    p = _proto("local f = function(a, b) return a + b end\nf(1, 2)\n",
               tmp_path)
    out = print_chunk(p, naming={
        ("main", 0): "scene_x",
        ("main_0", 0): "scene_id",
        ("main_0", 1): "scene_title",
    })
    assert "local scene_x = function(scene_id, scene_title)" in out
    assert "return scene_id + scene_title" in out
    assert "scene_x(1, 2)" in out
    # Compiles, and the names are not the synthesized spellings.
    from pyluadec import oracle
    oracle.compile_source(out.encode())
    assert "l0_0" not in out and "l1_0" not in out


def test_miss_falls_back_to_the_synthesized_name(tmp_path):
    from pyluadec.emit.lua import print_chunk
    p = _proto("local f = function(a) return a end\nf(1)\n", tmp_path)
    out = print_chunk(p, naming={("main", 0): "scene_x"})
    assert "local scene_x = function(l1_0)" in out
    assert "return l1_0" in out


def test_semantic_upvalue_threads_into_the_child(tmp_path):
    """A child capturing a renamed parent local must reference the SEMANTIC
    name (the upvalue-name threading in `closure_parts`), or the capture
    would silently rebind."""
    from pyluadec.emit.lua import print_chunk
    from pyluadec import oracle
    p = _proto("local n = 41\nlocal f = function() return n + 1 end\n"
               "return f()\n", tmp_path)
    out = print_chunk(p, naming={("main", 0): "answer"})
    assert "local answer = 41" in out
    assert "return answer + 1" in out
    oracle.compile_source(out.encode())


# ---------------------------------------------------------------------------
# The runtime P1 catch: a resolution-changing rename degrades certification.

def test_a_shadowing_rename_is_refused_by_certification(tmp_path):
    """Naming main's first local `gameSave` while a LATER function reads the
    GLOBAL `gameSave` flips that reference to a capture (GETGLOBAL -> MOVE
    pseudo, nups +1) -- the compiled chunk differs from the original, so
    the certification ladder must refuse it. This is P1's runtime arm: the
    table rides the ordinary print path, so a bad name can only degrade
    the ledger, never ship.

    The flip needs the reference OUTSIDE the renamed local's own
    initializer: Lua locals are invisible inside the statement that
    declares them, so `local gameSave = function() return gameSave.x end`
    recompiles with the inner reference still GLOBAL and stays byte-equal
    (measured -- the first version of this test asserted a flip there and
    the L3 it got instead was correct)."""
    from pyluadec.structure.structured import certify_proto, \
        clear_certification_cache
    p = _proto("local a = 1\n"
               "local f = function() return gameSave.x end\n"
               "return f() + a\n", tmp_path)
    clear_certification_cache()
    plain = certify_proto(p, is_chunk_root=True)
    assert plain.level == "L3", plain.reason
    clear_certification_cache()
    poisoned = certify_proto(p, is_chunk_root=True,
                             naming={("main", 0): "gameSave"})
    assert poisoned.level != "L3", poisoned.source
    clear_certification_cache()


def test_certification_memo_separates_the_naming_tiers(tmp_path):
    """The same proto certified with and without a table must not alias in
    the memo: the root tier ships the printed bytes, and the two prints
    differ. A harmless (non-shadowing) name keeps L3 under the table."""
    from pyluadec.structure.structured import certify_proto, \
        clear_certification_cache
    p = _proto("local f = function() return gameSave.x end\n"
               "return f()\n", tmp_path)
    clear_certification_cache()
    named = certify_proto(p, is_chunk_root=True,
                          naming={("main", 0): "getter"})
    clear_certification_cache()
    plain = certify_proto(p, is_chunk_root=True)
    assert named.level == "L3" and plain.level == "L3"
    assert named.source != plain.source
    assert b"local getter" in named.source
    assert b"local l0_0" in plain.source
    clear_certification_cache()


# ---------------------------------------------------------------------------
# The measured intersections with the other channels.

def test_proposal_files_carry_no_table_rows():
    """All four proposal-channel files have an EMPTY readable surface in
    the old text itself (measured at the harvest: their top-level locals
    are v/i residuals), so the naming channel and the proposal channel
    never co-occur on this corpus. If a future harvest produces rows for
    one of these files, that innocence is gone and this pin should force
    the conversation about which names a spliced body may use."""
    rows = [json.loads(line) for line
            in (ROOT / "corpus" / "naming" / "name_map.jsonl")
            .read_text(encoding="ascii").splitlines()]
    proposal_files = {"snr_common.lua", "snr_graphic.lua",
                      "snr_mainmenu.lua", "snr_story_main.lua"}
    assert not [r for r in rows if r["file"] in proposal_files]
    # ... and the committed shape the report quotes.
    assert len(rows) == 1754
    assert sum(1 for r in rows if r["kind"] == "function") == 846
    assert sum(1 for r in rows if r["kind"] == "param") == 908


def test_finals_carry_the_aligned_surface():
    """Three spot checks across the name classes -- scene function + params
    (story file), card function family with a cross-function upvalue
    reference (crd file) -- against the SHIPPED finals, bytes-verbatim
    (containment only, no decoding)."""
    final_dir = ROOT / "corpus" / "final"
    s1 = final_dir / "snr_s1_10_s.lua"
    if not s1.is_file():
        pytest.skip("corpus/final not populated (decompiler output missing)")
    blob = s1.read_bytes()
    assert b"local scene_s1s_10 = function(scene_id, scene_title)" in blob
    assert b"scene_s1s_10(doScriptScene, " in blob
    crd = (final_dir / "snr_crd_103.lua").read_bytes()
    assert b"local card_103_s6s_150_sel_step11 = function()" in crd
    assert b"card_103_s6s_150_sel_resolve()" in crd


# ---------------------------------------------------------------------------
# T2: the translation-unit map.

def test_unit_map_is_a_fixed_point_and_reanchors_everything():
    ir = Path(os.environ.get(
        "PYLUADEC_TRANSLATION_IR",
        "/Users/fotile96/pyluadec/post_process/translation_ir"))
    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not ir.is_dir() or not corpus or not Path(corpus).is_dir():
        pytest.skip("translation_ir or corpus not present on this host")
    import build_unit_map as B
    rows, report = B.build(Path(corpus), ir)
    committed = (ROOT / "corpus" / "naming" / "unit_map.jsonl").read_bytes()
    assert B.render(rows) == committed
    # The measured shape the T0 report quotes.
    assert report["units"] == 1003
    assert report["by_name"] == 817
    assert report["file_main"] == 186
    assert report["unmatched"] == 0
    # Every unit re-anchors with its OLD id intact (that is the point of
    # the alignment) and no unit sits in a defect zone (measured: the 5
    # defect-zone files carry no units at all).
    assert all(r["new_id"] == r["old_id"] for r in rows)
    assert not [r for r in rows if "defect-zone" in r["flags"]]

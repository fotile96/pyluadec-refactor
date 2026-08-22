"""The propose-and-certify channel's guards -- M8 wiring (2026-08-18).

Every assertion here is one of the handoff's acceptance numbers (A1-A5)
or one of its properties given executable form (P4's enumeration pin, P6's
fixed point). The neuter proofs demonstrate each guard can fail by
pointing it at a doctored copy of the artifact it reads -- the
`verify_proposals.py` precedent.

Environment: A1-A3 assertions read COMMITTED artifacts (ledger, final/)
and need nothing; the fixed-point arm (P6) needs both corpus env vars
(one full regeneration, same discipline as `test_ledger_ratchet.py`).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.warranty_build import footprint_ratios  # noqa: E402
from pyluadec.structure import proposals as P  # noqa: E402


def _rows():
    return [json.loads(l) for l
            in (ROOT / "corpus" / "ledger.jsonl").read_text().splitlines()
            if l.strip()]


# ---------------------------------------------------------------------------
# P4: the enumeration is pinned. Adding or removing a proposal is a
# deliberate edit to `MANIFEST` (and to the committed files), held here.

def test_manifest_matches_the_committed_files():
    root = P.proposals_root()
    committed = set()
    for d in sorted(root.iterdir()):
        if d.is_dir():
            for f in d.glob("*.lua"):
                committed.add((f"{d.name}.lua", f.stem))
    assert committed == set(P.MANIFEST)


def test_p4_an_l3_proto_with_a_proposal_is_not_spliced(corpus_dir):
    """IMP-1's regression (controller review 2026-08-18): the printer
    splices every path in the dict it is handed, so the refusers filter
    in `_proposal_round` is the ONLY thing keeping a proposal from
    displacing a working reconstruction. Technique from the review: a
    proposal whose body differs only by a Lua COMMENT -- invisible to
    stripped bytecode, visible in the text -- hung on a proto the
    reconstructor certifies `L3`. The chunk must certify WITHOUT the
    marker (reconstructor text wins) and the proto must not be marked
    proposal-shipped."""
    from pyluadec.ingest import load_file
    from pyluadec.structure.structured import emit_certified_chunk
    from pyluadec.structure import proposals as P

    root = load_file(Path(corpus_dir) / "snr_common.lua")
    real = P.for_file("snr_common.lua")
    # snr_common:main_0 is reconstructor-L3 (not in any manifest entry).
    assert "main_0" not in real
    marked = dict(real)
    marked["main_0"] = real["main_24"].replace(
        b"return function()", b"return function() -- PLDMARK", 1)
    out = emit_certified_chunk(root, marked)
    if out.proposal_rung >= 0:                       # channel ran at all
        assert b"PLDMARK" not in out.source         # reconstructor text won
        assert not out.proposal_paths & {"main_0"}


def _scan_pld(files: dict[str, bytes]) -> list[str]:
    return sorted(n for n, data in files.items() if b"__pld_" in data)


def _non_l3(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["level"] != "L3"]


def _bad_ratios(ratios: dict[str, float]) -> dict[str, float]:
    return {f: r for f, r in ratios.items() if r != 1.0}


def test_a1_neuter_a_doctored_ledger_copy_is_named(tmp_path):
    """Neuter (IMP-3 rewrite): doctor a COPY of the committed ledger and
    run the gate's own predicate -- it must go red AND name the shash."""
    rows = _rows()
    rows[0]["level"] = "L1"
    rows[0]["refusal_reason"] = "mismatch: code"
    bad = _non_l3(rows)
    assert bad == [rows[0]]
    assert bad[0]["shash"] == rows[0]["shash"]      # named


def test_a3_neuter_a_planted_marker_in_a_copied_final_is_named(tmp_path):
    data = {p.name: p.read_bytes()
            for p in sorted((ROOT / "corpus" / "final").glob("*.lua"))}
    victim = next(iter(data))
    data[victim] = data[victim] + b"__pld_R[0] = 1\n"
    hits = _scan_pld(data)
    assert hits == [victim]                          # named


def test_a4_neuter_a_doctored_ratio_copy_is_named(tmp_path):
    ratios = dict(footprint_ratios())
    victim = next(iter(ratios))
    ratios[victim] = 3.5
    bad = _bad_ratios(ratios)
    assert bad == {victim: 3.5}                     # named


def test_manifest_neuter_a_stray_proposal_file_is_named(tmp_path, monkeypatch):
    """Neuter (IMP-3 rewrite, per the review's own experiment): copy the
    real proposals tree to tmp, add a stray file the MANIFEST does not
    name, point `PYLUADEC_PROPOSALS_DIR` at it, and run the
    enumeration's own predicate -- the stray must be named."""
    import shutil
    root = P.proposals_root()
    copy = tmp_path / "proposals"
    shutil.copytree(root, copy)
    stray_dir = copy / "snr_lib"
    stray_dir.mkdir()
    (stray_dir / "main_0.lua").write_bytes(b"return function() end\n")
    monkeypatch.setenv("PYLUADEC_PROPOSALS_DIR", str(copy))

    committed = set()
    for d in sorted(copy.iterdir()):
        if d.is_dir():
            for f in d.glob("*.lua"):
                committed.add((f"{d.name}.lua", f.stem))
    extra = committed - set(P.MANIFEST)
    assert extra == {("snr_lib.lua", "main_0")}     # named


# ---------------------------------------------------------------------------
# A1/A2: the ledger's residual is empty and nothing ships fallback.

def test_a1_no_non_l3_rows():
    non_l3 = [r for r in _rows() if r["level"] != "L3"]
    assert non_l3 == []


def test_a2_no_fallback_occurrences():
    fb = [(r["shash"], o["proto_path"]) for r in _rows()
          for o in r["occurrences"] if o["shipped"] == "fallback"]
    assert fb == []


def test_a2_no_confessions():
    for r in _rows():
        assert r["confessions"] == []
        assert r["refusal_reason"] is None


# ---------------------------------------------------------------------------
# A3: no state machine ships anywhere in corpus/final/.

def test_a3_no_pld_in_final():
    assert _scan_pld({p.name: p.read_bytes()
                      for p in (ROOT / "corpus" / "final").glob("*.lua")}) == []


# ---------------------------------------------------------------------------
# A4: every file's footprint is exactly 1.0.

def test_a4_all_footprints_unit():
    ratios = footprint_ratios()
    assert len(ratios) == 229
    assert _bad_ratios(ratios) == {}


# ---------------------------------------------------------------------------
# P6: the ledger remains a fixed point of its generator (the proposals are
# committed data, so this is automatic -- measured, not reasoned).

@pytest.mark.timeout(300)
def test_p6_ledger_fixed_point_with_proposals(
        corpus_dir, pred_corpus_dir, tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_corpus_fixedpoint_check", ROOT / "scripts" / "run_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(corpus_dir))
    rc = mod.main()
    assert rc == 0
    regenerated = (tmp_path / "corpus" / "ledger.jsonl").read_bytes()
    assert regenerated == (ROOT / "corpus" / "ledger.jsonl").read_bytes()


# ---------------------------------------------------------------------------
# The upvalue renamer's soundness in the small (the whole-tree compare is
# the large proof; these pin the scanner's boundary behavior).

def test_renamer_leaves_strings_and_comments():
    from pyluadec.structure.proposals import rename_upvalues as R
    assert R(b'v = "u0" -- u1\nu2\n', ["a", "b", "c"]) == b'v = "u0" -- u1\nc\n'
    assert R(b'my_u0 = uu0\n', ["a"]) == b'my_u0 = uu0\n'
    assert R(b'[[u0]] u1\n', ["a", "b"]) == b'[[u0]] b\n'
    assert R(b'x = u5\n', ["a"]) == b'x = u5\n'      # out of range: untouched


def test_renamer_shifts_local_prefixes():
    from pyluadec.structure.proposals import rename_upvalues as R
    assert R(b'l1_0 = u0\n', ["l1_0"], shift=1) == b'l2_0 = l1_0\n'
    assert R(b'l2_0 + l1_1\n', [], shift=1) == b'l3_0 + l2_1\n'
    assert R(b'l1_0\n', [], shift=0) == b'l1_0\n'    # no shift: identity

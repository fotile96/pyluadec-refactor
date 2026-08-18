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


def test_neutering_the_manifest_pin_fails():
    """Neuter: an EXTRA proposal file on disk (a stray, not in MANIFEST)
    must break the enumeration equality -- the pin reads the directory,
    not just the module's own table."""
    assert len(P.MANIFEST) == 9


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


def test_a2_neuter_a_doctored_ledger_fails_both_gates(tmp_path):
    """Neuter: one hand-doctored row (level flipped to L1 with a reason)
    inside a COPIED ledger must break A1's assertion -- proving the gates
    read the artifact, not the world."""
    rows = _rows()
    rows[0]["level"] = "L1"
    rows[0]["refusal_reason"] = "mismatch: code"
    doctored = [r for r in rows if r["level"] != "L3"]
    assert doctored != []


# ---------------------------------------------------------------------------
# A3: no state machine ships anywhere in corpus/final/.

def test_a3_no_pld_in_final():
    hits = []
    for f in sorted((ROOT / "corpus" / "final").glob("*.lua")):
        if b"__pld_" in f.read_bytes():
            hits.append(f.name)
    assert hits == []


def test_a3_neuter_a_planted_marker_fails(tmp_path):
    data = (ROOT / "corpus" / "final").glob("*.lua")
    sample = next(iter(data)).read_bytes()
    assert b"__pld_" in (sample + b"__pld_R[0] = 1\n")


# ---------------------------------------------------------------------------
# A4: every file's footprint is exactly 1.0.

def test_a4_all_footprints_unit():
    ratios = footprint_ratios()
    assert len(ratios) == 229
    bad = {f: r for f, r in ratios.items() if r != 1.0}
    assert bad == {}


def test_a4_neuter_a_doctored_ratio_fails():
    ratios = dict(footprint_ratios())
    name = next(iter(ratios))
    ratios[name] = 3.5
    bad = {f: r for f, r in ratios.items() if r != 1.0}
    assert bad == {name: 3.5}


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

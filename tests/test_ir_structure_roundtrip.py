"""Ported intent from the predecessor's `pyluadec/test_ir_structure_roundtrip.py`
(M4 task 5). Mechanism-equivalent rewrite (spec §8): the predecessor's 6
cases each assert some form of "the recompiled proto has the same shape as
the original" (opcode counts, `numparams`/`is_vararg`/subproto-count shape,
CFG block/edge/back-edge counts). This repo's `certify_proto(...).level ==
"L3"` is a STRICTLY STRONGER form of that same claim: `L3` means the
recompiled candidate matches the original FIELD BY FIELD under the
normalization ladder (`verify.normalize.compare_protos`), which subsumes
opcode-count equality, param/vararg/subproto shape, and CFG shape all at
once, plus everything else `compare_protos` checks (constants, line info
under the ladder, locvars, maxstacksize, ...). See `structure/structured.py`'s
module docstring.

Where the predecessor's cases used literal Lua sources, this port keeps them
verbatim and asserts `L3` directly. Where the predecessor iterated named
files under a hardcoded `/root/pyluadec/others/script_to_decompile/` path
(a convention this repo's CLAUDE.md forbids -- corpus location is always
`PYLUADEC_CORPUS_DIR`, never hardcoded), this port uses the `corpus_dir`/
`decompiled` fixtures from `tests/conftest.py` and is therefore corpus-gated
(`pytest.skip`s without `PYLUADEC_CORPUS_DIR`, same as every other corpus
test in this repo) -- these three cases inherently need real corpus files,
unlike `test_semantic_regressions.py`'s five cases and the generated-case
scheme, which compile their own sources and must not be corpus-gated.

Measured 2026-08-11 against the same 22-file subset the predecessor used
(`ROUNDTRIP_SCRIPT_SUBSET`), plus `snr_graphic.lua` for its dedicated 6th
case: 4 of those files' `main` proto do NOT certify `L3` (`config.lua`,
`snr_common.lua`, `snr_graphic.lua`, `snr_memory.lua` -- all ship fallback);
the 18 `snr_crd_*` files do. This is a measured fact pinned below per file
(this repo's "measure, don't assert" convention -- see e.g.
`tests/test_structured_certify.py`), not something the predecessor's cases
could have distinguished (they only checked "compiles, no TODO_IR marker" /
"CFG shape survives", both of which `structure.fallback`'s state machine
also satisfies -- it is semantically exact and pc-total by construction, see
its module docstring), so this is a strictly more informative port of the
same two cases, not a contradiction of the predecessor's green result on
them.
"""
from __future__ import annotations

import pytest

from pyluadec import oracle
from pyluadec.ingest import load_bytes
from pyluadec.structure.structured import certify_proto


def _proto(src: str):
    bc = oracle.compile_source(src.encode(), strip=True)
    return load_bytes(bc)


def test_for_and_if_structuring_certifies_l3():
    """Predecessor: test_structure_detects_for_and_if (checked that
    NumericForNode/IfNode IR node types were present in the old `structure.py`
    tree). This repo's structurer has no equivalent node-type IR to
    introspect the same way (see `pyluadec.sir`/`pyluadec.express`'s
    region/expression trees, which are a different shape entirely) -- the
    strictly stronger, architecture-appropriate replacement is that the
    WHOLE chunk (a for-loop wrapping an if/else) recompiles byte-for-byte
    under the ladder.
    """
    src = """
        local x = 0
        for i=1,3 do
            if i < 3 then
                x = x + i
            else
                x = x + 10
            end
        end
        return x
    """
    c = certify_proto(_proto(src), is_chunk_root=True)
    assert c.level == "L3", c.mismatches


def test_closure_node_structuring_certifies_l3():
    """Predecessor: test_structure_detects_closure_node (checked a
    ClosureNode was present in the IR). Strictly stronger equivalent: the
    chunk containing the closure literal certifies L3."""
    src = """
        local x = 5
        local f = function()
            return x
        end
        return f
    """
    c = certify_proto(_proto(src), is_chunk_root=True)
    assert c.level == "L3", c.mismatches


def test_roundtrip_preserves_core_opcodes_via_l3():
    """Predecessor: test_roundtrip_compiles_and_preserves_core_opcodes
    (asserted FORPREP/FORLOOP/LT/ADD/RETURN/JMP/LOADK counts matched between
    original and roundtripped proto). `L3` implies exact `code` array
    equality at rung 0 (verify.normalize's strict comparator), which is a
    strictly stronger claim than matching per-opcode counts alone."""
    src = """
        local x = 0
        for i=1,5 do
            if i < 3 then
                x = x + i
            else
                x = x + 1
            end
        end
        return x
    """
    c = certify_proto(_proto(src), is_chunk_root=True)
    assert c.level == "L3", c.mismatches


# The predecessor's ROUNDTRIP_SCRIPT_SUBSET, unchanged (spec §8: keep the
# subset, port the assertion). Measured 2026-08-11 main-proto levels are
# pinned explicitly rather than left implicit, per this repo's "measure,
# don't assert" convention -- 4 of 22 ship fallback.
_SCRIPT_SUBSET_LEVELS = {
    "config.lua": "L3",  # M7 task 6: dynamic-key constructor fix (was L1)
    "snr_common.lua": "L1",
    "snr_crd_0.lua": "L3",
    "snr_crd_1.lua": "L3",
    "snr_crd_10.lua": "L3",
    "snr_crd_100.lua": "L3",
    "snr_crd_101.lua": "L3",
    "snr_crd_102.lua": "L3",
    "snr_crd_103.lua": "L3",
    "snr_crd_104.lua": "L3",
    "snr_crd_105.lua": "L3",
    "snr_crd_106.lua": "L3",
    "snr_crd_107.lua": "L3",
    "snr_crd_108.lua": "L3",
    "snr_crd_109.lua": "L3",
    "snr_crd_11.lua": "L3",
    "snr_crd_110.lua": "L3",
    "snr_crd_111.lua": "L3",
    "snr_crd_112.lua": "L3",
    "snr_crd_113.lua": "L3",
    "snr_graphic.lua": "L1",
    "snr_memory.lua": "L1",
}


# Of the four non-`L3` mains above, the two whose chunk ships HYBRID rather
# than whole-file fallback (measured 2026-08-14, M6 task 12; both were
# whole-file fallback before it).
# snr_common joined at M7 task 6 (dynamic-key constructor fix flipped it
# whole-file fallback -> hybrid; 2026-08-15).
_SUBSET_HYBRID = frozenset({"snr_graphic.lua", "snr_memory.lua", "snr_common.lua"})


def _skip_if_subset_missing(corpus_dir) -> None:
    missing = [f for f in _SCRIPT_SUBSET_LEVELS if not (corpus_dir / f).is_file()]
    if missing:
        pytest.skip(f"corpus subset files missing from PYLUADEC_CORPUS_DIR: {missing}")


def test_real_script_subset_roundtrip_compiles(corpus_dir, decompiled):
    """Predecessor: test_real_script_subset_roundtrip_compiles (asserted no
    TODO_IR marker and that the roundtripped proto has nonempty code, i.e.
    "the old structurer didn't choke on this file"). This repo's floor is
    stronger than "no unhandled marker": EVERY corpus file compiles, always
    (M2's exit gate, `test_corpus_compile.py`) -- fallback is total by
    construction, never partial. So the meaningful per-file check left to add
    here is the certification LEVEL, pinned exactly per file above.
    """
    _skip_if_subset_missing(corpus_dir)
    for name, expected_level in _SCRIPT_SUBSET_LEVELS.items():
        res = decompiled(corpus_dir / name)
        oracle.compile_source(res.source)                 # never raises: M2 floor
        assert res.levels["main"] == expected_level, name


def test_real_script_subset_preserves_shape(corpus_dir, decompiled):
    """Predecessor: test_real_script_subset_preserves_shape (asserted
    function-shape and reachable-CFG-shape equality between original and
    roundtripped proto, for the same 22 files). Where a file's `main`
    certifies `L3`, `certify_proto`'s comparison already proved field-by-field
    equality (a strict superset of shape equality) as a side effect of
    reaching that ledger row -- nothing further to check. Where it does not
    (the 4 files pinned `L1` above), shape preservation in the predecessor's
    sense does not apply: the fallback artifact is a pc-dispatch state
    machine, not a structural re-derivation of the original's control flow,
    so there is no "CFG shape" of the output left to compare against the
    original's. What IS still true for those 4 -- and is exactly the
    invariant `pyluadec.structure.fallback` exists to guarantee, standing in
    for "preserves shape" at the M2 floor -- is that every original pc is
    claimed and re-executed; that totality is proven elsewhere (the fallback
    module's own pc-claim coverage, exercised corpus-wide, and
    `test_corpus_compile.py`'s all-229-compile gate), not re-proven here.

    Two of the four are HYBRID chunks (M6 task 12; measured 2026-08-14):
    `snr_graphic.lua` and `snr_memory.lua` have an unproved `main`, but
    `certify_hybrid` compared `main`'s OWN fields against a real recompile and
    replaced only the descendant `CLOSURE` sites it could not certify, so
    `main` itself ships structured text and confesses nothing. The
    non-`L3`-implies-`fallback-state-machine` shorthand this test used is a
    property of whole-file fallback, not of non-certification, and it stopped
    holding for those two here -- so which of the two shapes each file ships
    is pinned by name below rather than inferred from the level.
    """
    _skip_if_subset_missing(corpus_dir)
    for name, expected_level in _SCRIPT_SUBSET_LEVELS.items():
        res = decompiled(corpus_dir / name)
        assert res.levels["main"] == expected_level, name
        if expected_level == "L3":
            assert res.confessions_by_proto["main"] == []
            assert res.rungs["main"] is not None
        elif name in _SUBSET_HYBRID:
            # `main` is unproved but its own fields were compared; only
            # descendants were replaced, so there is nothing for it to confess.
            assert res.confessions_by_proto["main"] == []
        else:
            assert res.confessions_by_proto["main"][0]["reason"] == "fallback-state-machine"


def test_fidelity_preserves_unreachable_code_for_graphic(corpus_dir, decompiled):
    """Predecessor: test_fidelity_mode_preserves_unreachable_cfg_shape_for_graphic
    (asserted the `ir_lua_fidelity` pipeline mode -- unlike the default
    `ir_lua` mode -- kept dead/unreachable blocks in `snr_graphic.lua`'s CFG
    shape, because the predecessor's non-fidelity structurer could drop
    unreachable blocks). This repo has no such mode split and no such risk:
    every proto that does not certify `L3` ships `structure.fallback`'s
    pc-dispatch state machine, which is total over the ORIGINAL instruction
    stream by construction -- every pc, reachable or not, gets a
    `__pld_pc == N` arm (see `pyluadec.structure.fallback`'s module
    docstring: "pc 派发状态机，38/38 opcode 全覆盖"). `snr_graphic.lua`'s
    `main` measured `L1` on 2026-08-11 -- the same file the predecessor
    used, still exercising the same "does dead code survive" concern, now by
    construction rather than by a mode flag this repo does not have.
    """
    path = corpus_dir / "snr_graphic.lua"
    if not path.is_file():
        pytest.skip("snr_graphic.lua missing from PYLUADEC_CORPUS_DIR")
    res = decompiled(path)
    assert res.levels["main"] == "L1"
    assert b"__pld_pc" in res.source
    oracle.compile_source(res.source)          # never raises: M2 floor

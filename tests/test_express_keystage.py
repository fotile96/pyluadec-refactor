"""The key-staged-below-table barrier -- M7 task 10, cluster O (freereg.py).

Stock Lua 5.1.5 discharges the table prefix of `prefix[key]` to a register
BEFORE parsing the key (`lparser.c`'s `[` arm: `luaK_exp2anyreg` on the
prefix, then `yindex`), so bytecode from an INLINE key always carries the
key's definition strictly after the table's. The contrapositive is this
barrier: when a register-keyed `GETTABLE`/`SETTABLE` reads a key whose
pending definition PREDATES the table operand's, the source was never
`prefix[key_expr]` -- the author materialized the key as its own named
local first:

    local k = sceneId2aCard.s3s_300_sel    -- key code, lower pc
    ... = prefix[k].suffix                 -- table code, higher pc

Measured corpus shape: `snr_s3_10_s.lua:main_59` pcs 745-749 and
`snr_s4_10_s.lua:main_58` pc 1120 -- without the barrier the key graded temp
(single read), the reconstructor inlined it into the index, and the
recompiled instruction stream inverted the staging order (`mismatch: code`,
same length). Both files' whole-file flips ride on it.
"""
from __future__ import annotations

import pyluadec.express.freereg as freereg
from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source
from pyluadec.pipeline import decompile_chunk
from pyluadec.structure.structured import clear_certification_cache


def _levels_of(source: bytes) -> dict[str, str]:
    root = load_bytes(compile_source(source, strip=True))
    return decompile_chunk(root).levels


# The key, materialized first in the source and read exactly once, with the
# def and the read in the SAME block -- everything the temp classifier wants
# (and everything `_same_block` would permit), and exactly what this barrier
# must refuse to stage. Two shapes of the surrounding code had to be tried
# before this fixture isolates the barrier (both wrong ways are recorded
# because they are each a REAL pin owned by another rule): an `if`-condition
# read puts the read in another region and `_same_block` materializes the
# key on its own; and a trailing call statement (`print(n)`) hits the CALL
# promote, which grades every still-pending def local. What isolates THIS
# barrier is the corpus's own shape (`snr_s3_10_s:main_59` pcs 745-767):
# the key's pending entry is popped with exactly one read by a LATER LOW
# WRITE -- the `MOVE 1 3` at pc 767, i.e. an assignment to a local below
# the key's slot -- which is the one pop that would otherwise grade it temp.
_MATERIALIZED_KEY = (b"local a = 1\n"
                     b"local k = t1.a\n"
                     b"local n = t2.b[k].c\n"
                     b"a = t3.d\n"
                     b"return n, a\n")

# The same expression with the key INLINE -- the shape stock 5.1.5 compiles
# with the key's code after the table's. The barrier must not touch it.
_INLINE_KEY = (b"local n = t2.b[t1.a].c\n"
               b"return n\n")


def test_a_materialized_key_certifies():
    assert _levels_of(_MATERIALIZED_KEY) == {"main": "L3"}


def test_the_inline_key_still_stages_and_certifies():
    """The counterfactual, and it must go on certifying: an inline key is
    the ordinary `t[f(x)]` shape, and inlining it back recompiles to the
    same instruction stream."""
    assert _levels_of(_INLINE_KEY) == {"main": "L3"}


def test_the_two_sources_produce_different_bytecode():
    """Non-vacuity for the pair above: if the two sources compiled
    identically the barrier would be grading one shape two ways and neither
    test could fail. They differ -- the register staging order is the whole
    difference the barrier reads."""
    a = compile_source(_MATERIALIZED_KEY, strip=True)
    b = compile_source(_INLINE_KEY, strip=True)
    ra, rb = load_bytes(a), load_bytes(b)
    assert ra.code != rb.code


def test_a_local_table_with_a_fresh_key_keeps_staging():
    """Narrowness: a NAMED-LOCAL table (`t[k]` with `t` declared) read by a
    register key must not fire the barrier -- that is the ordinary inline
    shape seen from the key's side. Without the both-pending guard this
    fixture would materialize the key and lose the L3."""
    src = (b"local t = {}\n"
           b"local n = 0\n"
           b"t[f(n)] = 1\n"
           b"return t\n")
    assert _levels_of(src) == {"main": "L3"}


def test_neutering_the_barrier_costs_the_materialized_key(monkeypatch):
    """Neuter proof (load-bearing, not decorative): the barrier's absence
    takes the repro from `L3` to `L1` -- the key inlines, the staging order
    inverts, and the recompile mismatches. Cache cleared across runs because
    certification memoizes per process."""
    clear_certification_cache()
    assert _levels_of(_MATERIALIZED_KEY) == {"main": "L3"}
    monkeypatch.setattr(freereg, "_bar_key_staged_below_table",
                        lambda li, pending: None)
    clear_certification_cache()
    assert _levels_of(_MATERIALIZED_KEY) == {"main": "L1"}
    monkeypatch.undo()
    clear_certification_cache()
    assert _levels_of(_MATERIALIZED_KEY) == {"main": "L3"}


def test_the_barrier_fires_on_the_corpus_shape():
    """The `snr_s3_10_s:main_59` pc-745 shape end to end: this whole file
    was hybrid before task 10 (frontier `main_59`) and ships fully
    structured after -- pinned so it cannot silently drop back."""
    import os
    from pathlib import Path

    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not corpus:
        import pytest
        pytest.skip("PYLUADEC_CORPUS_DIR not set")
    clear_certification_cache()
    res = decompile_chunk(
        load_bytes(Path(corpus, "snr_s3_10_s.lua").read_bytes()))
    assert res.levels["main_59"] == "L3"
    assert res.levels["main"] == "L3"
    assert not any(res.shipped_fallback.values())

"""M3 exit wiring: decompile_chunk reports a per-proto certification level.

`decompile_chunk` no longer confesses unconditionally. A proto that certified
L3 has a machine-checked proof that its structured print recompiles to it, so
it records no confession; a proto that fell back to the M2 state machine still
records `fallback-state-machine`. Ledger levels going up while confessions go
down is the ratchet signal M3 exists to produce.

The shipped SOURCE and the per-proto LEVEL are deliberately decoupled (see
`structure.structured`'s module docstring): the artifact is structured only
when the ROOT certifies, because a chunk file is all-or-nothing, while a level
is a per-proto proof record. `test_mixed_chunk_levels_are_per_proto` pins that
decoupling directly.
"""


def test_decompile_chunk_records_levels():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(b"local a = 1 local b = 2 print(a + b)", strip=True)
    res = decompile_chunk(load_bytes(bc))
    assert res.levels["main"] == "L3"
    assert res.rungs["main"] is not None
    assert res.confessions_by_proto.get("main", []) == []     # L3 protos confess nothing
    oracle.compile_source(res.source)


# A chunk `build_sir` still refuses, used throughout this module as the
# "falls back" sample. Was `local i = 0 while i < 3 do i = i + 1 end return i`
# until M4 task 3 structured `while`; the and/or VALUE idiom compiles to
# TESTSET, which is still refused.
# EXPIRY: M4 task 4 reconstructs TESTSET. When it lands, every use of this
# constant needs a different still-unstructurable sample -- and if none
# remains, these tests have lost their subject and should be re-thought
# rather than patched.
_UNSTRUCTURABLE = b"local a, b local x = a or b return x"


def test_fallback_chunk_still_confesses():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(_UNSTRUCTURABLE, strip=True)
    res = decompile_chunk(load_bytes(bc))
    assert res.levels["main"] == "L1"
    assert res.rungs["main"] is None
    assert res.confessions_by_proto["main"][0]["reason"] == "fallback-state-machine"
    assert b"__pld_pc" in res.source


def test_mixed_chunk_levels_are_per_proto():
    """An unstructurable main must not poison its straight child's level."""
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(
        b"local f = function(a, b) return a + b end\n"
        b"local p, q local x = p or q return f(x, 1)", strip=True)
    res = decompile_chunk(load_bytes(bc))
    assert res.levels["main"] == "L1"
    assert res.levels["main_0"] == "L3"
    assert res.confessions_by_proto["main_0"] == []
    # ...but the ARTIFACT is still the fallback chunk, because the root did
    # not certify. Level and shipped source are decoupled by design.
    assert b"__pld_pc" in res.source


def test_uncertified_source_is_never_shipped():
    """The one invariant emit_certified_chunk exists to hold, restated at the
    pipeline boundary: if any proto is not L3, the emitted source must be the
    semantically-exact fallback, never a partially-structured print."""
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    for src in (_UNSTRUCTURABLE,
                b"local t = {} t[1] = 2 return t"):
        res = decompile_chunk(load_bytes(oracle.compile_source(src, strip=True)))
        assert res.levels["main"] == "L1"
        assert b"__pld_pc" in res.source
        oracle.compile_source(res.source)


def test_every_proto_path_gets_a_level_and_a_rung_key():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk, walk_proto_paths
    bc = oracle.compile_source(
        b"local f = function(x) local g = function(y) return y end return g(x) end\n"
        b"return f(1)", strip=True)
    root = load_bytes(bc)
    protos: dict = {}
    walk_proto_paths("main", root, protos)
    res = decompile_chunk(root)
    assert set(res.levels) == set(protos)
    assert set(res.rungs) == set(protos)
    assert set(res.confessions_by_proto) == set(protos)
    for path, level in res.levels.items():
        assert level in ("L1", "L3")
        assert (res.rungs[path] is not None) == (level == "L3")
        assert (res.confessions_by_proto[path] == []) == (level == "L3")

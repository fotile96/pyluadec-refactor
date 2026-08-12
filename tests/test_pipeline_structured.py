"""M3 exit wiring: decompile_chunk reports a per-proto certification level.

`decompile_chunk` no longer confesses unconditionally. A proto that certified
L3 has a machine-checked proof that its structured print recompiles to it, so
it records no confession; a proto that fell back to the M2 state machine still
records `fallback-state-machine`. Ledger levels going up while confessions go
down is the ratchet signal M3 exists to produce.

The shipped SOURCE and the per-proto LEVEL are deliberately decoupled (see
`structure.structured`'s module docstring): a level is a per-proto proof
record, while the shipped artifact is a chunk-level choice among three tiers
-- the root's own certified bytes, a hybrid (structured everywhere except at
the CLOSURE sites a hybrid certification could not clear, M5 task 6), or the
whole-chunk fallback -- not the all-or-nothing "root certifies or the whole
file falls back" rule this docstring stated before the task-6 review's F6/
Residual A correction. `test_mixed_chunk_levels_are_per_proto` pins the
decoupling directly, and `tests/test_hybrid_chunk.py` pins the hybrid tier.
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
# "falls back" sample. It has moved twice: `local i = 0 while i < 3 do ... end`
# until M4 task 3 structured `while`, then the and/or VALUE idiom until M4
# task 4 reconstructed TESTSET. It is now the BOOLEAN-value family -- a
# comparison used as a value, which `lcode.c:exp2reg` materialises with a
# LOADBOOL pair (`need_value` is true when the jump list's control instruction
# is not a TESTSET), and which `build_sir` refuses as an unrecognized transfer.
# EXPIRY: whichever task reconstructs LOADBOOL value expressions. When it
# lands, every use of this constant needs a different still-unstructurable
# sample -- and if none remains, these tests have lost their subject and
# should be re-thought rather than patched.
_UNSTRUCTURABLE = b"local a, b = 1, 2 local x = (a or b) == 1 return x"


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
        b"local p, q = 1, 2 local x = (p or q) == 1 return f(x, 1)", strip=True)
    res = decompile_chunk(load_bytes(bc))
    assert res.levels["main"] == "L1"
    assert res.levels["main_0"] == "L3"
    # ...but the ARTIFACT is still the fallback chunk: the root's OWN body does
    # not print (`(p or q) == 1`), so there is no structured code to keep and
    # hybrid emission has nothing to assemble. Level and shipped source are
    # decoupled by design.
    assert b"__pld_pc" in res.source
    assert res.hybrid is False
    # M5 task 6 corrected the confession here. `main_0` certified `L3` on its
    # own, and until this task that alone cleared its confession -- while its
    # text in `res.source` was, and still is, the state machine. The confession
    # says which PASS emitted a proto's text ("pass": "structure.fallback"), so
    # it now tracks shipping rather than level, and this chunk's `L3` child
    # confesses because it really did ship as a state machine. The level is
    # untouched: that is the proof record, and it stays `L3`.
    assert res.shipped_fallback["main_0"] is True
    assert (res.confessions_by_proto["main_0"][0]["reason"]
            == "fallback-state-machine")


def test_uncertified_source_is_never_shipped():
    """The invariant `emit_certified_chunk` exists to hold, at the pipeline
    boundary: no proto's structured print ships unless something compiled and
    compared those exact bytes.

    **The docstring this replaces was retired by M5 task 6 and said so nowhere**
    (round-1 review, F6). It read "if any proto is not L3, the emitted source
    must be the semantically-exact fallback, never a partially-structured
    print", which was the M3/M4 all-or-nothing rule. Hybrid emission is
    *deliberately* a partially-structured print: a root that misses `L3` ships
    structured everywhere except at the CLOSURE sites it could not certify.
    This test kept passing only because both fixtures below have nothing to
    substitute -- neither root has a subproto that is both non-`L3` and
    printable-around -- so the whole-file fallback is still the only artifact
    available for them.

    What it guards, restated for the current gate: a root that does not certify
    and has no hybrid ships the semantically-exact state machine, and the
    result compiles. The hybrid branch is guarded in `tests/test_hybrid_chunk.py`,
    which is where the shipping invariant now lives in full.
    """
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    for src in (_UNSTRUCTURABLE,
                b"local t = {} t[1] = 2 return t"):
        root = load_bytes(oracle.compile_source(src, strip=True))
        # The premise the assertions below rest on, asserted rather than
        # assumed: there is no hybrid for these two, so "not L3" really does
        # mean "the whole-file fallback".
        assert root.subprotos == ()
        res = decompile_chunk(root)
        assert res.levels["main"] == "L1"
        assert res.hybrid is False
        assert all(res.shipped_fallback.values())
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

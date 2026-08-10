def _bc(src: str):
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode(), strip=True), chunkname="=t")


def _bc_debug(src: str):
    # BRIEF DEFECT (documented in task-0-report.md): oracle.compile_source(strip=True)
    # already empties lineinfo at compile time, so a helper built on it cannot
    # demonstrate "L3.0 sees a line-layout difference that L3.1 normalizes away" --
    # there is no line info left to differ. This variant keeps debug info (strip=False)
    # so the test can exercise what it claims to exercise.
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode(), strip=False), chunkname="=t")


def test_ladder_version_bumped():
    from pyluadec.verify.normalize import LADDER_VERSION, NORMALIZATIONS
    assert LADDER_VERSION == "l3-ladder-v1"
    assert len(NORMALIZATIONS) == 1
    assert NORMALIZATIONS[0][0] == "strip-lineinfo"


def test_l30_sees_line_layout_l31_does_not():
    from pyluadec.verify.normalize import compare_protos
    a, b = _bc_debug("print(1)"), _bc_debug("\n\n\nprint(1)")
    assert compare_protos(a, b, level=0) != []          # L3.0 strict: line info differs
    assert compare_protos(a, b, level=1) == []           # L3.1: line info stripped → equal


def test_l31_still_catches_real_difference():
    from pyluadec.verify.normalize import compare_protos
    # different constants must NOT be normalized away at L3.1
    assert compare_protos(_bc("return 1"), _bc("return 2"), level=1) != []
    assert compare_protos(_bc("return 0.0"), _bc("return -0.0"), level=1) != []  # payload-exact survives
    # different code
    # BRIEF DEFECT (documented in task-0-report.md): "local a=1 return a" compiles
    # byte-identical to "return 1" under Lua 5.1's register-direct-return
    # optimization (both: LOADK r0 K0; RETURN r0 2) -- not a valid "different code"
    # example. Substituted a pair that provably differs (LOADK; MOVE; RETURN vs
    # LOADK; RETURN).
    assert compare_protos(_bc("local a=1 local b=a return b"), _bc("return 1"), level=1) != []


def test_l31_strips_locvar_and_upvalue_names_but_keeps_counts():
    # non-stripped compile carries locvar/upvalue names; L3.1 must ignore names, keep structure
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.verify.normalize import compare_protos
    a = load_bytes(oracle.compile_source(b"local x = 1 local function f() return x end return f()"))
    b = load_bytes(oracle.compile_source(b"local y = 1 local function g() return y end return g()"))
    # different local/upvalue NAMES, identical structure → L3.0 differs (names in locvars), L3.1 equal
    assert compare_protos(a, b, level=0) != []
    assert compare_protos(a, b, level=1) == []


def test_l31_does_not_normalize_away_maxstacksize():
    # maxstacksize is register-frame-size, not debug decoration -- L3.1 must
    # not paper over a real difference in it. Constructed directly (rather than
    # via compiling two source snippets) so the assertion pins the exact
    # semantic field under test, independent of compiler-chosen register counts.
    from pyluadec.ingest.proto import Proto
    from pyluadec.verify.normalize import compare_protos

    def mkproto(maxstacksize: int) -> Proto:
        return Proto(source=b"x", linedefined=1, lastlinedefined=1, nups=0,
                     numparams=0, is_vararg=0, maxstacksize=maxstacksize,
                     code=(1, 2, 3), constants=(), lineinfo=(), locvars=(),
                     upvalues=(), subprotos=())

    assert compare_protos(mkproto(2), mkproto(5), level=1) != []


def test_bad_level_still_raises():
    import pytest
    from pyluadec.verify.normalize import normalize
    with pytest.raises(ValueError):
        normalize(_bc("return 1"), level=99)

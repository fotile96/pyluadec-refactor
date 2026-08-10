def _bc(src: str) -> "Proto":
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode()), chunkname="=t")


def test_same_source_twice_is_l30_equal():
    from pyluadec.verify.normalize import compare_protos
    src = 'local x = 1.5 local function f(a) return a + x end print(f(2))'
    assert compare_protos(_bc(src), _bc(src), level=0) == []


def test_negative_examples_are_caught():
    from pyluadec.verify.normalize import compare_protos
    cases = [
        ("return 1", "return 2"),                       # 常量 payload 不同
        ("return 0.0", "return -0.0"),                  # payload 逐位比较的招牌用例
        ("local a = 1 return a", "return 1"),           # code 不同
        ("print(1)", "print(1) print(2)"),              # code 长度不同
        ("local f = function() end", "local f = function() return 1 end"),  # 子 proto
    ]
    for sa, sb in cases:
        assert compare_protos(_bc(sa), _bc(sb), level=0) != [], (sa, sb)


def test_line_layout_difference_is_l30_visible():
    """L3.0 是全严格：只多一个空行（lineinfo 变了）也要报差异——诚实优先。"""
    from pyluadec.verify.normalize import compare_protos
    a, b = _bc("print(1)"), _bc("\nprint(1)")
    diffs = compare_protos(a, b, level=0)
    assert diffs and all("line" in d.field for d in diffs)


def test_mismatch_paths_point_into_subprotos():
    from pyluadec.verify.normalize import compare_protos
    a = _bc("local f = function() return 1 end print(f())")
    b = _bc("local f = function() return 2 end print(f())")
    diffs = compare_protos(a, b, level=0)
    assert any(d.path.startswith("root/0") for d in diffs)


def test_maxstacksize_difference_is_caught():
    """Closes a real coverage gap: before this test existed, dropping
    `maxstacksize` from `_cmp` was caught by zero tests in this suite.

    `local a=1 return a+a+a+a+a+a` and `local a=1 return (a+a)*(a+a)*(a+a)`
    compile to genuinely different register-pressure profiles (maxstacksize
    2 vs 3, confirmed by decoding below) while keeping
    constants/lineinfo/locvars/numparams/nups/is_vararg identical -- only
    `code` differs incidentally too (different instruction sequence for the
    different expression shape, an unavoidable side effect of using
    different source to provoke different register pressure). Because
    `code` also differs, this asserts on the specific `maxstacksize` field
    name rather than merely `!= []`, so the test isolates the maxstacksize
    comparison itself rather than riding on the incidental `code` diff.
    """
    from pyluadec.verify.normalize import compare_protos
    sa = "local a=1 return a+a+a+a+a+a"
    sb = "local a=1 return (a+a)*(a+a)*(a+a)"
    a, b = _bc(sa), _bc(sb)
    assert a.maxstacksize != b.maxstacksize, (a.maxstacksize, b.maxstacksize)
    assert a.constants == b.constants
    assert a.lineinfo == b.lineinfo
    assert a.locvars == b.locvars
    diffs = compare_protos(a, b, level=0)
    assert any(d.field == "maxstacksize" for d in diffs), diffs


def test_numparams_difference_is_caught():
    """Closes a real coverage hole: before this test existed, dropping
    `numparams` from `_cmp`'s field loop left all 120 tests passing.

    `local function f(a) end` vs `local function f(a,b) end` isolates
    cleanly to the subproto's `numparams` -- confirmed below that both
    subprotos' `code` and `maxstacksize` are otherwise identical, so this
    asserts on the specific field name rather than riding on an incidental
    `code` diff.
    """
    from pyluadec.verify.normalize import compare_protos
    a, b = _bc("local function f(a) end"), _bc("local function f(a,b) end")
    sa, sb = a.subprotos[0], b.subprotos[0]
    assert sa.numparams != sb.numparams, (sa.numparams, sb.numparams)
    assert sa.code == sb.code
    assert sa.maxstacksize == sb.maxstacksize
    diffs = compare_protos(a, b, level=0)
    assert any(d.field == "numparams" for d in diffs), diffs


def test_is_vararg_difference_is_caught():
    """Closes a real coverage hole: dropping `is_vararg` from `_cmp` left
    all 120 tests passing. `function()` vs `function(...)` isolates
    cleanly -- both subprotos' `code` and `maxstacksize` are identical,
    only the ISVARARG bit of `is_vararg` differs.
    """
    from pyluadec.verify.normalize import compare_protos
    a, b = _bc("local function f() end"), _bc("local function f(...) end")
    sa, sb = a.subprotos[0], b.subprotos[0]
    assert sa.is_vararg != sb.is_vararg, (sa.is_vararg, sb.is_vararg)
    assert sa.code == sb.code
    assert sa.maxstacksize == sb.maxstacksize
    diffs = compare_protos(a, b, level=0)
    assert any(d.field == "is_vararg" for d in diffs), diffs


def test_nups_difference_is_caught():
    """Closes a real coverage hole: dropping `nups` from `_cmp` left all
    120 tests passing. Two closures capturing a different number of
    upvalues differ in `nups`; `code` also differs here (an unavoidable
    side effect of the extra GETUPVAL for the second capture, same
    reasoning as test_maxstacksize_difference_is_caught above), so this
    asserts on the specific `nups` field name rather than merely `!= []`.
    """
    from pyluadec.verify.normalize import compare_protos
    a = _bc("local x=1 local function f() return x end print(f)")
    b = _bc("local x=1 local y=2 local function f() return x,y end print(f)")
    sa, sb = a.subprotos[0], b.subprotos[0]
    assert sa.nups != sb.nups, (sa.nups, sb.nups)
    diffs = compare_protos(a, b, level=0)
    assert any(d.field == "nups" for d in diffs), diffs


def test_upvalues_names_difference_is_caught():
    """Closes a real coverage hole: dropping `upvalues` from `_cmp` alone
    left all 120 tests passing (unlike the other four fields in this
    file, dropping `upvalues` doesn't ride along with any other field's
    assertion elsewhere in the suite). Requires a non-stripped compile
    (compare_protos.py's default -- `oracle.compile_source`'s `strip`
    defaults to False) so upvalue names survive to `Proto.upvalues`.

    `xxx` vs `yyy` as the captured local's name isolates *completely*:
    confirmed below that code/nups/numparams/maxstacksize/is_vararg/
    constants/lineinfo are all identical between the two subprotos, only
    `upvalues` (the captured name) differs.
    """
    from pyluadec.verify.normalize import compare_protos
    a = _bc("local xxx = 1 local function f() return xxx end print(f)")
    b = _bc("local yyy = 1 local function f() return yyy end print(f)")
    sa, sb = a.subprotos[0], b.subprotos[0]
    assert sa.upvalues != sb.upvalues, (sa.upvalues, sb.upvalues)
    assert sa.code == sb.code
    assert sa.nups == sb.nups
    assert sa.numparams == sb.numparams
    assert sa.maxstacksize == sb.maxstacksize
    assert sa.is_vararg == sb.is_vararg
    assert sa.constants == sb.constants
    assert sa.lineinfo == sb.lineinfo
    diffs = compare_protos(a, b, level=0)
    assert any(d.field == "upvalues" for d in diffs), diffs


def test_source_difference_is_caught():
    """Closes a real coverage hole: dropping `source` from `_cmp` left all
    120 tests passing -- unsurprising, since `oracle.compile_source` always
    runs `luac` against a fixed relative filename (`in.lua`, see the
    comment in `oracle.py` about why: a stable embedded `source` is what
    makes byte/field-level comparison meaningful at all), so two ordinary
    `_bc(...)` calls can never actually produce different `source` values
    to compare. `dataclasses.replace` sidesteps that by mutating a copy of
    an otherwise-identical Proto, isolating purely to `source`.
    """
    import dataclasses
    from pyluadec.verify.normalize import compare_protos
    a = _bc("return 1")
    b = dataclasses.replace(a, source=b"@other.lua")
    assert a.source != b.source
    diffs = compare_protos(a, b, level=0)
    assert len(diffs) == 1 and diffs[0].field == "source", diffs


def test_bad_level_raises():
    import pytest
    from pyluadec.verify.normalize import normalize
    p = _bc("return 1")
    with pytest.raises(ValueError):
        normalize(p, level=99)

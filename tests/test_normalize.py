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


def test_bad_level_raises():
    import pytest
    from pyluadec.verify.normalize import normalize
    p = _bc("return 1")
    with pytest.raises(ValueError):
        normalize(p, level=99)

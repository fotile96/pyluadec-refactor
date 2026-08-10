import struct


def _num(v: float):
    from pyluadec.ingest.proto import LuaNumber
    return LuaNumber(value=v, payload=struct.pack("<d", v))


def test_num_lit_integral_and_fractional():
    from pyluadec.structure.fallback import num_lit
    assert num_lit(_num(42.0)) == "42"
    assert num_lit(_num(42.5)) == "42.5"
    assert num_lit(_num(-3.0)) == "(-3)"


def test_num_lit_payload_exact_roundtrip():
    from pyluadec.structure.fallback import num_lit
    # -0.0 is intentionally excluded here: it is no longer rendered as a
    # plain numeral (see test_num_lit_negative_zero_is_not_a_plain_numeral)
    # because luac's constant-folder/interner collapses `-0.0` numerals into
    # `+0.0`, so a Python-only round-trip through float() is not the
    # relevant correctness criterion for that value.
    for v in (0.1, 1e300, 16.000000000000004, 123456789012345.6):
        s = num_lit(_num(v))
        rendered = s.strip("()")
        assert struct.pack("<d", float(rendered)) == struct.pack("<d", v)


def test_num_lit_negative_zero_is_not_a_plain_numeral():
    """-0.0 must not be rendered as a numeral luac could fold/intern back to
    +0.0 (`luaH_get` normalises integral number constant keys via
    `lua_number2int`, so a `-0.0` numeral collides with `0.0` in the
    constant table -- see num_lit's docstring comment). Asserting the
    rendered form contains no bare `-0` numeral is a cheap unit-level
    guard; test_negative_zero_survives_decompile_roundtrip below is the
    real (differential, luac-backed) proof.
    """
    from pyluadec.structure.fallback import num_lit
    s = num_lit(_num(-0.0))
    assert s == "(-1/(1/0))", s
    # float(s) must not even parse as a plain numeral (it is an expression):
    import pytest
    with pytest.raises(ValueError):
        float(s.strip("()"))


def test_negative_zero_survives_decompile_roundtrip():
    """Reproduces the bug fixed in fallback.num_lit: `local x = -0.0
    print(1/x)` prints -inf originally; before the fix, the decompiled
    source's `-0.0` numeral collided with the `0` numeral the emitter's own
    preamble emits for every function (fallback.py's boxed-register init),
    so luac's constant interning silently rewrote it to +0.0 and the
    decompiled program printed +inf instead.
    """
    from tests.diffexec import assert_fallback_roundtrip
    assert_fallback_roundtrip("local x = -0.0 print(1/x)")


def test_num_lit_nonfinite():
    from pyluadec.structure.fallback import num_lit
    assert num_lit(_num(float("inf"))) == "(1/0)"
    assert num_lit(_num(float("-inf"))) == "(-1/0)"
    assert num_lit(_num(float("nan"))) == "(0/0)"


def test_str_lit_escaping():
    from pyluadec.structure.fallback import str_lit
    assert str_lit(b"abc") == '"abc"'
    assert str_lit(b'a"b\\c') == '"a\\"b\\\\c"'
    assert str_lit(b"\x01" + b"23") == '"\\00123"'     # 定长转义防数字粘连
    assert str_lit(b"\xff\x00\n") == '"\\255\\000\\010"'


def test_str_lit_compiles_back_to_same_bytes():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import str_lit
    payload = bytes(range(256))
    bc = oracle.compile_source(f"return {str_lit(payload)}".encode())
    consts = load_bytes(bc).constants
    assert payload in consts                            # 字节精确穿越 lexer

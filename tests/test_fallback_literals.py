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
    for v in (0.1, 1e300, 16.000000000000004, -0.0, 123456789012345.6):
        s = num_lit(_num(v))
        rendered = s.strip("()")
        assert struct.pack("<d", float(rendered)) == struct.pack("<d", v)


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

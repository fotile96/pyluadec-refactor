import pytest


def test_compile_and_run_roundtrip():
    from pyluadec import oracle
    bc = oracle.compile_source(b'print("hello from oracle")')
    assert bc[:4] == b"\x1bLua"
    r = oracle.run_bytes(bc, is_source=False)
    assert r.returncode == 0 and r.stdout == b"hello from oracle\n"


def test_run_source_directly():
    from pyluadec import oracle
    r = oracle.run_bytes(b"print(1 + 1)", is_source=True)
    assert r.stdout == b"2\n"


def test_compile_error_carries_stderr():
    from pyluadec import oracle
    with pytest.raises(oracle.LuaCompileError, match="near"):
        oracle.compile_source(b"local local local")


def test_strip_flag():
    from pyluadec import oracle
    plain = oracle.compile_source(b"return 1")
    stripped = oracle.compile_source(b"return 1", strip=True)
    assert len(stripped) < len(plain)

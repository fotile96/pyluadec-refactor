"""差分执行 harness：源码 → luac_sz4 →（原字节码执行）vs（fallback 反编译再执行）。"""
from pyluadec import oracle
from pyluadec.ingest import load_bytes
from pyluadec.structure.fallback import emit_chunk


def assert_fallback_roundtrip(lua_source: str, args: tuple[str, ...] = ()) -> bytes:
    bc = oracle.compile_source(lua_source.encode())
    dec = emit_chunk(load_bytes(bc))
    r1 = oracle.run_bytes(bc, is_source=False, args=args)
    r2 = oracle.run_bytes(dec, is_source=True, args=args)
    assert r1.returncode == r2.returncode, (
        f"exit {r1.returncode} != {r2.returncode}\n"
        f"--- orig stderr ---\n{r1.stderr!r}\n--- dec stderr ---\n{r2.stderr!r}\n"
        f"--- decompiled ---\n{dec.decode()}")
    assert r1.stdout == r2.stdout, (
        f"--- orig ---\n{r1.stdout!r}\n--- dec ---\n{r2.stdout!r}\n"
        f"--- decompiled ---\n{dec.decode()}")
    return dec

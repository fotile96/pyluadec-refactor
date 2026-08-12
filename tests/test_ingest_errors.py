import subprocess
from pathlib import Path

import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"


def _compile_sz4(src: str, tmp: Path) -> bytes:
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return o.read_bytes()


def test_bad_header_fields_raise_badheader(tmp_path):
    from pyluadec.ingest import BadHeader, parse_header
    good = bytearray(_compile_sz4("return 1", tmp_path))
    for byte_idx, bad_value in [(5, 1), (6, 0), (7, 8), (9, 8), (10, 4), (11, 1)]:
        blob = bytearray(good)
        blob[byte_idx] = bad_value
        with pytest.raises(BadHeader):
            parse_header(bytes(blob))


def test_unsupported_sizet_width_raises_badheader(tmp_path):
    from pyluadec.ingest import BadHeader, parse_header
    blob = bytearray(_compile_sz4("return 1", tmp_path))
    blob[8] = 2
    with pytest.raises(BadHeader):
        parse_header(bytes(blob))


def test_truncated_body_raises_ingest_error(tmp_path):
    from pyluadec.ingest import BadHeader, IngestError, load_bytes
    blob = _compile_sz4("return 1", tmp_path)
    with pytest.raises(IngestError):
        load_bytes(blob[:40])          # header 完整、函数体截断 → bridge 报错须被包装
    with pytest.raises(BadHeader):
        load_bytes(b"\x1bLuaQ")        # header 都不完整


def test_a_stale_bridge_so_raises_ingest_error_not_bare_runtimeerror(monkeypatch, tmp_path):
    """`_bridge_for` cross-checks the selected `.so`'s own
    `serial_sizet_width()` against the width the header asked for, so an
    interrupted rebuild that leaves an sz8 module where sz4 is expected is
    caught rather than silently misparsed. Until M5 task 12 that check ran
    OUTSIDE `load_bytes`' `try`, so it escaped as a bare `RuntimeError` -- past
    every caller that catches `IngestError`, which is the documented way to
    catch an ingest failure (`test_truncated_body_raises_ingest_error` above
    is the same fault class through the other path).

    Neuter proof: move the `_bridge_for(...)` call back above the `try` in
    `ingest/dispatch.py::load_bytes` and this test fails with the
    `RuntimeError` propagating out of `pytest.raises(IngestError)`.
    """
    from pyluadec._native import _bridge_sz4
    from pyluadec.ingest import IngestError, load_bytes

    monkeypatch.setattr(_bridge_sz4, "serial_sizet_width", lambda: 8)
    blob = _compile_sz4("return 1", tmp_path)
    with pytest.raises(IngestError) as ei:
        load_bytes(blob)
    # `_bridge_for`'s own message survives -- it names the cause and the repair
    # command, and re-wording it here would only make the two drift.
    assert "does not match the width it was selected for" in str(ei.value)


def test_badheader_is_ingest_error_and_valueerror():
    from pyluadec.ingest import BadHeader, IngestError
    assert issubclass(BadHeader, IngestError)
    assert issubclass(BadHeader, ValueError)

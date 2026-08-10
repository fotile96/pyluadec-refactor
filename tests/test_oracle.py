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


def test_compile_source_is_deterministic():
    """Regression test: compile_source used to write the input into a freshly
    randomized tempfile.TemporaryDirectory() and hand luac that absolute path,
    which luac embeds verbatim as Proto.source (lundump.c LoadFunction reads
    it straight out of the binary chunk). Two compiles of byte-identical
    source therefore produced byte-DIFFERENT bytecode blobs -- which would
    silently defeat any byte/field-level comparison of two compilations (see
    verify.normalize's L3.0 comparator, whose whole point is exact equality).
    compile_source must now run luac with cwd=tempdir and a RELATIVE
    filename, so the embedded source name is stable regardless of where the
    tempdir lands.
    """
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes

    src = b"local x = 1 return x"

    plain_a = oracle.compile_source(src)
    plain_b = oracle.compile_source(src)
    assert plain_a == plain_b

    proto = load_bytes(plain_a, chunkname="=t")
    assert proto.source == b"@in.lua"
    assert b"/tmp" not in proto.source
    assert b"var/folders" not in proto.source

    stripped_a = oracle.compile_source(src, strip=True)
    stripped_b = oracle.compile_source(src, strip=True)
    assert stripped_a == stripped_b

    stripped_proto = load_bytes(stripped_a, chunkname="=t")
    # strip=True dumps NULL for source unconditionally (ldump.c DumpFunction),
    # so this was already deterministic pre-fix -- included for completeness
    # and to guard against a future regression that starts leaking the path
    # even under stripping.
    assert stripped_proto.source == b"=?"
    if stripped_proto.source is not None:
        assert b"/tmp" not in stripped_proto.source
        assert b"var/folders" not in stripped_proto.source

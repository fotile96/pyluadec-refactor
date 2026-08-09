import struct, subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"

def _compile(luac, src, tmp):
    s = tmp / "t.lua"; o = tmp / "t.out"
    s.write_text(src, encoding="utf-8")
    subprocess.run([str(BUILD / luac), "-o", str(o), str(s)], check=True)
    return o.read_bytes()

SRC = 'local answer = 42.5\nlocal name = "ab\\255cd"\nprint(name, answer)\n'

def test_sz4_bridge_full_fields(tmp_path):
    from pyluadec._native import _bridge_sz4 as b
    assert b.serial_sizet_width() == 4
    p = b.load_bytecode(_compile("luac_sz4", SRC, tmp_path))
    assert p["numparams"] == 0 and p["maxstacksize"] > 0
    assert p["lineinfo"] and p["locvars"]
    assert p["locvars"][0]["name"] == b"answer"
    nums = [c for c in p["constants"] if isinstance(c, dict)]
    assert nums and nums[0]["payload"] == struct.pack("<d", 42.5)
    strs = [c for c in p["constants"] if isinstance(c, bytes)]
    assert b"ab\xffcd" in strs          # non-UTF-8 bytes survive losslessly

def test_sz8_bridge_roundtrip_width(tmp_path):
    from pyluadec._native import _bridge_sz8 as b
    assert b.serial_sizet_width() == 8
    p = b.load_bytecode(_compile("luac_sz8", SRC, tmp_path))
    assert len(p["code"]) > 0

def test_sz4_bridge_loads_real_corpus_file(corpus_dir):
    from pyluadec._native import _bridge_sz4 as b
    p = b.load_bytecode((corpus_dir / "snr_crd_1.lua").read_bytes())
    assert p["subprotos"] or p["code"]


# Lua 5.1's VARARG_HASARG bit is 1; the old bridge flattened is_vararg via
# `& VARARG_HASARG`. A top-level chunk's raw flag is VARARG_ISVARARG (2),
# which has bit 1 clear -- so a masked-and-coerced-to-bool implementation
# would silently report False/0 here even though the chunk *is* vararg.
SRC_PLAIN_FN = 'local function plain(x)\n  return x\nend\nreturn plain\n'

def test_sz4_bridge_is_vararg_raw_flags(tmp_path):
    from pyluadec._native import _bridge_sz4 as b
    p = b.load_bytecode(_compile("luac_sz4", SRC_PLAIN_FN, tmp_path))
    # main chunk: raw VARARG_ISVARARG flag (2), not masked to VARARG_HASARG (1),
    # and not coerced to a Python bool.
    assert p["is_vararg"] == 2
    assert type(p["is_vararg"]) is int
    # a plain (non-vararg) nested function must contrast with a clean 0.
    plain = p["subprotos"][0]
    assert plain["is_vararg"] == 0
    assert type(plain["is_vararg"]) is int


# A nested closure that captures an outer local (making it an upvalue) and
# compares it against true/false/nil forces those literals into the
# constant table (rather than the LOADBOOL/LOADNIL fast paths used for
# simple local assignment), and gives the enclosing function real
# startpc/endpc ranges on its locvars.
SRC_UPVAL = (
    "local function outer(x)\n"
    "  local y = x\n"
    "  local function inner()\n"
    "    return y == true, y == nil, y == false\n"
    "  end\n"
    "  return inner\n"
    "end\n"
    "return outer\n"
)

def test_sz4_bridge_upvalues_nil_bool_and_locvar_ranges(tmp_path):
    from pyluadec._native import _bridge_sz4 as b
    p = b.load_bytecode(_compile("luac_sz4", SRC_UPVAL, tmp_path))
    outer = p["subprotos"][0]
    assert [lv["name"] for lv in outer["locvars"]] == [b"x", b"y", b"inner"]
    assert all(lv["endpc"] > lv["startpc"] for lv in outer["locvars"])

    inner = outer["subprotos"][0]
    assert inner["upvalues"] == [b"y"]
    consts = inner["constants"]
    assert any(c is True for c in consts)
    assert any(c is False for c in consts)
    assert any(c is None for c in consts)


def test_sz4_bridge_malformed_blob_raises_cleanly():
    from pyluadec._native import _bridge_sz4 as b
    # RAII (LuaCloser/unique_ptr) must close the lua_State on the throw
    # path too; a modest repeat loop guards against a leak or crash there
    # without slowing the suite down.
    for _ in range(25):
        try:
            b.load_bytecode(b"not lua bytecode at all")
        except RuntimeError as e:
            assert "load failed" in str(e)
        else:
            raise AssertionError("expected RuntimeError for malformed blob")

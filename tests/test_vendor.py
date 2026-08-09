from pathlib import Path

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "lua-5.1"

def test_vendor_is_lua_515():
    lua_h = (VENDOR / "src" / "lua.h").read_text()
    assert 'LUA_RELEASE\t"Lua 5.1.5"' in lua_h

def test_vendor_has_no_build_artifacts():
    assert not list(VENDOR.rglob("*.o"))
    assert not list(VENDOR.rglob("*.a"))
    assert not (VENDOR / "src" / "luac.out").exists()

def test_undump_sources_present():
    for f in ("lundump.c", "lundump.h", "ldump.c", "luac.c", "print.c"):
        assert (VENDOR / "src" / f).exists()

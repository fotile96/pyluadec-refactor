import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"

def test_sz4_header_byte(compile_lua):
    blob = compile_lua("luac_sz4", "return 1").read_bytes()
    assert blob[:4] == b"\x1bLua" and blob[4] == 0x51
    assert blob[8] == 4          # sizeof(serialized size_t)

def test_sz8_header_byte(compile_lua):
    blob = compile_lua("luac_sz8", "return 1").read_bytes()
    assert blob[8] == 8

def test_sz4_lua_runs_sz4_bytecode(tmp_path):
    s = tmp_path / "p.lua"; o = tmp_path / "p.out"
    s.write_text('print("ok")')
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    r = subprocess.run([str(BUILD / "lua_sz4"), str(o)], capture_output=True, text=True, check=True)
    assert r.stdout.strip() == "ok"

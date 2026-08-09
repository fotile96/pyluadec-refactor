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

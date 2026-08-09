import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_patch_applies_cleanly(tmp_path):
    shutil.copytree(ROOT / "vendor" / "lua-5.1" / "src", tmp_path / "src")
    r = subprocess.run(
        ["patch", "-p1", "-d", str(tmp_path), "-i",
         str(ROOT / "native" / "patches" / "0001-serial-sizet.patch")],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    patched = (tmp_path / "src" / "lundump.h").read_text()
    assert "lua_SerialSizet" in patched

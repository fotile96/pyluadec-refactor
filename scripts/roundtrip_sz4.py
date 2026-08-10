"""Load->redump roundtrip: luac_sz4 must reproduce each corpus file byte-identically."""
import os, subprocess, sys, tempfile
from pathlib import Path

def roundtrip_file(luac: Path, f: Path, tmpdir: Path) -> bool:
    # -s (strip) is required: the corpus was produced by `luac -s`, which
    # forces DumpFunction to write the main chunk's source as NULL (see
    # ldump.c: DumpString((f->source==p || D->strip) ? NULL : f->source, D)).
    # luaU_undump loads that NULL source as the synthetic "=?" literal
    # (lundump.c: LoadFunction(&S, luaS_newliteral(L,"=?"))). Re-dumping
    # without -s would write that synthesized "=?" back out as a real
    # string, adding 3 bytes and breaking byte-identity even though the
    # bytecode/constants are otherwise reproduced exactly.
    out = Path(tmpdir) / (f.name + ".rt")
    subprocess.run([str(luac), "-s", "-o", str(out), str(f)], check=True, capture_output=True)
    return out.read_bytes() == f.read_bytes()

if __name__ == "__main__":
    luac = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("build/luac_sz4")
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    with tempfile.TemporaryDirectory() as td:
        bad = [f.name for f in sorted(corpus.glob("*.lua"))
               if not roundtrip_file(luac, f, Path(td))]
    print(f"roundtrip: {'OK all' if not bad else 'FAIL ' + str(bad)}")
    sys.exit(1 if bad else 0)

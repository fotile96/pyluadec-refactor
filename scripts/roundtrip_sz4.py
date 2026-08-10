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
    corpus_env = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not corpus_env:
        print("roundtrip: FAIL PYLUADEC_CORPUS_DIR is not set", file=sys.stderr)
        sys.exit(1)
    corpus = Path(corpus_env)
    files = sorted(corpus.glob("*.lua"))
    if not files:
        # A wrong path or an empty directory must fail loudly -- an empty
        # glob() here would otherwise make "OK all" mean "checked nothing".
        print(f"roundtrip: FAIL no *.lua files found under {corpus} "
              f"(check PYLUADEC_CORPUS_DIR)", file=sys.stderr)
        sys.exit(1)

    bad = []
    with tempfile.TemporaryDirectory() as td:
        for f in files:
            try:
                ok = roundtrip_file(luac, f, Path(td))
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
                bad.append(f"{f.name} (luac failed: {stderr.strip()})")
                continue
            if not ok:
                bad.append(f.name)

    if bad:
        print(f"roundtrip: FAIL {bad}")
        sys.exit(1)
    print(f"roundtrip: OK all ({len(files)} files)")
    sys.exit(0)

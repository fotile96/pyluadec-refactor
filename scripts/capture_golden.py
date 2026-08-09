"""Capture golden baseline from the OLD project's tools. Run ONCE on the 32-bit env:

  PYTHONPATH=/root/pyluadec/cmake-build-debug/native_bridge \
  PYLUADEC_CORPUS_DIR=/root/pyluadec/others/script_to_decompile \
  PYLUADEC_OLD_LUAC=/root/pyluadec/cmake-build-debug/lua-5.1/luac \
  python3 scripts/capture_golden.py

Golden derives ONLY from original bytecode + old tools; it is never regenerated
by new tools (spec §6 R5).
"""
import gzip, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "corpus" / "golden"

def main() -> int:
    import lua51_proto_extractor as old  # old bridge, 32-bit only
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    old_luac = os.environ["PYLUADEC_OLD_LUAC"]
    (GOLDEN / "proto_dump").mkdir(parents=True, exist_ok=True)
    (GOLDEN / "listing").mkdir(parents=True, exist_ok=True)
    manifest = {}
    files = sorted(corpus.glob("*.lua"))
    for f in files:
        blob = f.read_bytes()
        manifest[f.name] = {"sha256": hashlib.sha256(blob).hexdigest(), "size": len(blob)}
        dump = old.load_proto(str(f))
        with gzip.open(GOLDEN / "proto_dump" / (f.name + ".json.gz"), "wt", encoding="utf-8") as fh:
            json.dump(dump, fh, ensure_ascii=False, sort_keys=True)
        # -p (parse only) prevents luac from also writing a "luac.out" compiled
        # blob into the current working directory; only the -l -l listing on
        # stdout is captured. Verified this does not change listing content.
        listing = subprocess.run([old_luac, "-p", "-l", "-l", str(f)],
                                 capture_output=True, text=True, check=True).stdout
        (GOLDEN / "listing" / (f.name + ".txt")).write_text(listing, encoding="utf-8")
    (GOLDEN / "manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print(f"captured {len(files)} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())

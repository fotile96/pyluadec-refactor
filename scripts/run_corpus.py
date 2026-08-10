"""全语料反编译 + 编译验证 + 台账落盘。

用法: PYLUADEC_CORPUS_DIR=... uv run python scripts/run_corpus.py
产出: build/decompiled/<name>.lua（不入库）与 corpus/ledger.jsonl（入库）。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    from pyluadec import oracle
    from pyluadec.ingest import load_file
    from pyluadec.pipeline import walk_proto_paths, decompile_chunk
    from pyluadec.verify.ledger import (LedgerEntry, oracle_version, structural_hash,
                                        write_ledger)
    from pyluadec.verify.normalize import LADDER_VERSION

    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    outdir = ROOT / "build" / "decompiled"
    outdir.mkdir(parents=True, exist_ok=True)
    orc = oracle_version()
    by_hash: dict[str, LedgerEntry] = {}
    n_ok = 0
    files = sorted(corpus.glob("*.lua"))
    for f in files:
        root = load_file(f)
        res = decompile_chunk(root)
        (outdir / f.name).write_bytes(res.source)
        try:
            oracle.compile_source(res.source)
            compile_ok = True
            n_ok += 1
        except oracle.LuaCompileError as e:
            compile_ok = False
            print(f"COMPILE FAIL {f.name}: {str(e)[:200]}", file=sys.stderr)
        protos = {}
        walk_proto_paths("main", root, protos)
        for path, p in protos.items():
            h = structural_hash(p)
            occ = {"file": f.name, "proto_path": path}
            if h in by_hash:
                e = by_hash[h]
                e.occurrences.append(occ)
                e.compile_ok = e.compile_ok and compile_ok
            else:
                by_hash[h] = LedgerEntry(
                    shash=h, level="L1" if compile_ok else "L0",
                    l3_level=None, compile_ok=compile_ok, fallback=True,
                    n_insns=len(p.code),
                    confessions=res.confessions_by_proto[path],
                    occurrences=[occ], oracle=orc, ladder=LADDER_VERSION)
    for e in by_hash.values():
        if not e.compile_ok:
            e.level = "L0"
    write_ledger(list(by_hash.values()), ROOT / "corpus" / "ledger.jsonl")
    print(f"compiled {n_ok}/{len(files)}; ledger: {len(by_hash)} unique protos "
          f"({sum(len(e.occurrences) for e in by_hash.values())} occurrences)")
    return 0 if n_ok == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())

"""全语料反编译 + 编译验证 + 台账落盘。

用法: PYLUADEC_CORPUS_DIR=... uv run python scripts/run_corpus.py
产出: build/decompiled/<name>.lua（不入库）与 corpus/ledger.jsonl（入库）。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ledger levels are a ratchet: they only ever go up.
_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}

_L0_REASON = "compile: shipped chunk did not compile"


def _force_l0(e) -> None:
    """Demote an entry whose SHIPPED CHUNK did not compile, and make it say so.

    A proto can certify `L3` on its own while the file it lives in fails the
    whole-chunk compile check; the chunk is what ships, so the row is `L0`
    regardless of the per-proto verdict. Before M4 task 6 this path rewrote
    `level`/`l3_level`/`fallback` and left `confessions` alone -- which for an
    individually-`L3` proto is the empty list, so an `L0` row could ship
    UNCONFESSED, exactly the shape "confess, don't guess" forbids. It is
    latent (229/229 files compile today, so no `L0` row has ever been written,
    and `tests/test_m3_exit.py::test_non_l3_entries_confess` would fail loudly
    if one appeared unconfessed), but a latent hole in the confession
    discipline is still a hole.

    The confession's `reason` stays `fallback-state-machine`, the vocabulary
    the existing coupling tests assert on: a chunk that did not compile ships
    the fallback state machine's output, so that IS what happened. The new
    `refusal_reason` field carries the finer distinction.
    Pinned by `tests/test_ledger.py::test_forced_l0_entry_is_confessed`.
    """
    e.level = "L0"
    e.l3_level = None
    e.fallback = True
    e.refusal_reason = _L0_REASON
    if not e.confessions:
        e.confessions = [{"pc_lo": 1, "pc_hi": e.n_insns,
                          "reason": "fallback-state-machine",
                          "pass": "structure.fallback"}]


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
    n_protos = 0
    n_structured = 0
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
            level = res.levels[path] if compile_ok else "L0"
            if level == "L3":
                n_structured += 1
            n_protos += 1
            if h in by_hash:
                e = by_hash[h]
                e.occurrences.append(occ)
                e.compile_ok = e.compile_ok and compile_ok
                # Levels only ever go up: take the higher level and keep its
                # evidence rather than silently keeping whichever file happened
                # to be walked first.
                #
                # KNOWN GAP, deliberately not closed here (M5 item; see
                # `docs/runbooks/m3-backlog.md`). The ledger groups by
                # `structural_hash` ALONE, and that key is NOT sufficient to
                # imply an equal verdict -- `structure.structured._memo_key`
                # keys its certification memo on `(structural_hash,
                # _debug_fingerprint)` precisely because `structural_hash`
                # drops `source`/`linedefined`/`lineinfo`/`locvars`/upvalue
                # names, all of which `compare_protos` checks (see
                # `_debug_fingerprint`'s docstring). So "a disagreement means a
                # bug" is an assumption this script makes and does not check.
                # Measured 2026-08-12: 16 of the 1478 shash groups contain more
                # than one debug fingerprint, and 0 groups disagree on level or
                # rung -- the max-by-rank above is vacuous today. Splitting the
                # ledger key would MOVE `corpus/ledger.jsonl`, so it is an M5
                # change made together with the ratchet CI, not a drive-by one.
                if _RANK[level] > _RANK[e.level]:
                    e.level = level
                    e.l3_level = res.rungs[path]
                    e.confessions = res.confessions_by_proto[path]
                    e.refusal_reason = res.reasons[path]
                e.fallback = e.level != "L3"
            else:
                by_hash[h] = LedgerEntry(
                    shash=h, level=level,
                    l3_level=res.rungs[path] if level == "L3" else None,
                    compile_ok=compile_ok, fallback=level != "L3",
                    n_insns=len(p.code),
                    confessions=res.confessions_by_proto[path],
                    occurrences=[occ], oracle=orc, ladder=LADDER_VERSION,
                    refusal_reason=res.reasons[path] if level != "L3" else None)
    for e in by_hash.values():
        if not e.compile_ok:
            _force_l0(e)
    write_ledger(list(by_hash.values()), ROOT / "corpus" / "ledger.jsonl")
    n_l3 = sum(1 for e in by_hash.values() if e.level == "L3")
    print(f"compiled {n_ok}/{len(files)}; ledger: {len(by_hash)} unique protos "
          f"({sum(len(e.occurrences) for e in by_hash.values())} occurrences)")
    print(f"structured {n_structured}/{n_protos} protos "
          f"({n_structured / n_protos:.1%}); "
          f"L3 {n_l3}/{len(by_hash)} unique ({n_l3 / len(by_hash):.1%})")
    return 0 if n_ok == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())

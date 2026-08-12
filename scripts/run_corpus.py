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

    **The per-occurrence `shipped` field moves with it** (M5 task 6 round 1,
    F8). M5 task 6 made `fallback` an aggregate *over the occurrences*, and
    `tests/test_m3_exit.py::test_non_l3_entries_confess` asserts `fallback ==
    any(o["shipped"] == "fallback")` over every row. Setting `fallback = True`
    here without touching the occurrences would contradict that coupling by
    construction rather than by accident -- still latent (229/229 files
    compile, so no `L0` row has ever been written), but a demotion path that
    writes a row its own exit test would reject is not a hole worth keeping.

    **What this is actually entitled to claim, and what it overclaims (M5
    task 6 round 2 review, New 2).** `e.compile_ok` is AND-ed across every
    occurrence of this SHAPE (`e.compile_ok = e.compile_ok and compile_ok` in
    the walk above), so it goes false the moment ANY file the shape occurs in
    fails to compile -- "a shipped chunk that does not compile cannot be a
    certified artifact" is a true statement about THAT chunk, not about a
    sibling file that shares the shape and compiled fine. This loop below
    nonetheless stamps `shipped = "fallback"` on every occurrence in `e`,
    including the ones that live in a different, compiling file, whose text in
    `build/decompiled/` really was shipped structured. Re-measured
    2026-08-12 (round 2): 13 of the 1478 shapes occur in more than one file
    (max 27 files sharing one shape), so a false claim here would touch at
    most those 13 rows' occurrences, never the other 1465. Still 0 rows today
    (229/229 compile, so `_force_l0` has never fired on this corpus) -- a
    trade against the pre-M5-task-6 state, which had a different latent
    inconsistency (an L0 row could ship with an empty confession list), not a
    regression against it, and not fixed here: narrowing this to only the
    occurrences that actually live in a non-compiling file needs per-file
    compile tracking this script does not currently keep per shape, and doing
    that is out of this round's scope (no production behaviour change beyond
    the docstring, per the round-2 brief).
    """
    e.level = "L0"
    e.l3_level = None
    e.fallback = True
    e.refusal_reason = _L0_REASON
    for o in e.occurrences:
        o["shipped"] = "fallback"
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
    # shash -> did ANY occurrence of this proto shape ship as the fallback
    # state machine? A row aggregates occurrences across files, and since M5
    # task 6 two occurrences of the SAME shape can ship differently (one inside
    # a hybrid's structured part, one inside a substituted subtree elsewhere).
    # OR, not AND: `fallback` is the field the confession hangs off, and a row
    # that confesses when at least one occurrence really did fall back is the
    # conservative reading. The per-occurrence `shipped` field is exact.
    shipped_fallback_any: dict[str, bool] = {}
    n_ok = 0
    n_protos = 0
    n_structured = 0
    n_shipped_structured = 0
    n_hybrid_files = 0
    n_fallback_files = 0
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
        if res.hybrid:
            n_hybrid_files += 1
        elif res.shipped_fallback.get("main"):
            n_fallback_files += 1
        protos = {}
        walk_proto_paths("main", root, protos)
        for path, p in protos.items():
            h = structural_hash(p)
            # `shipped` is the M5 task 6 schema change: which EMITTER produced
            # this proto's text in `build/decompiled/<file>.lua`. It is a
            # different question from `level` (which emitter's output was
            # *proved* equal to the original, per proto and in isolation), and
            # since hybrid emission the two genuinely disagree -- a proto that
            # is not `L3` on its own can still ship structured inside a chunk
            # whose hybrid certification compared its fields exactly. `hybrid`
            # is a property of the whole chunk, recorded per occurrence because
            # that is where the chunk identity (`file`) lives.
            shipped_fb = res.shipped_fallback[path]
            occ = {"file": f.name, "proto_path": path,
                   "shipped": "fallback" if shipped_fb else "structured",
                   "hybrid": res.hybrid}
            level = res.levels[path] if compile_ok else "L0"
            if level == "L3":
                n_structured += 1
            if not shipped_fb:
                n_shipped_structured += 1
            n_protos += 1
            if h in by_hash:
                e = by_hash[h]
                e.occurrences.append(occ)
                e.compile_ok = e.compile_ok and compile_ok
                shipped_fallback_any[h] = shipped_fallback_any[h] or shipped_fb
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
                    e.refusal_reason = res.reasons[path]
            else:
                shipped_fallback_any[h] = shipped_fb
                by_hash[h] = LedgerEntry(
                    shash=h, level=level,
                    l3_level=res.rungs[path] if level == "L3" else None,
                    compile_ok=compile_ok, fallback=shipped_fb,
                    n_insns=len(p.code),
                    confessions=[],
                    occurrences=[occ], oracle=orc, ladder=LADDER_VERSION,
                    refusal_reason=res.reasons[path] if level != "L3" else None)
    for h, e in by_hash.items():
        # `fallback` and its confession are decided ONCE, at the end, from the
        # occurrence aggregate -- not carried along from whichever occurrence
        # happened to hold the highest level. Before M5 task 6 the two were the
        # same thing (`fallback = level != "L3"`), so the confession could ride
        # along with the level; now that a proto's shipping is independent of
        # its level, tying them together would produce rows that confess a
        # state machine they did not ship, or ship one silently.
        e.fallback = shipped_fallback_any[h]
        e.confessions = ([{"pc_lo": 1, "pc_hi": e.n_insns,
                           "reason": "fallback-state-machine",
                           "pass": "structure.fallback"}] if e.fallback else [])
        if not e.compile_ok:
            _force_l0(e)
    write_ledger(list(by_hash.values()), ROOT / "corpus" / "ledger.jsonl")
    n_l3 = sum(1 for e in by_hash.values() if e.level == "L3")
    print(f"compiled {n_ok}/{len(files)}; ledger: {len(by_hash)} unique protos "
          f"({sum(len(e.occurrences) for e in by_hash.values())} occurrences)")
    print(f"structured {n_structured}/{n_protos} protos "
          f"({n_structured / n_protos:.1%}); "
          f"L3 {n_l3}/{len(by_hash)} unique ({n_l3 / len(by_hash):.1%})")
    print(f"shipped: {n_shipped_structured}/{n_protos} protos structured "
          f"({n_shipped_structured / n_protos:.1%}); "
          f"{len(files) - n_hybrid_files - n_fallback_files} files fully "
          f"structured, {n_hybrid_files} hybrid, {n_fallback_files} whole-file "
          f"fallback")
    return 0 if n_ok == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())

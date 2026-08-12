"""全语料反编译 + 编译验证 + 台账落盘。

用法: PYLUADEC_CORPUS_DIR=... uv run python scripts/run_corpus.py
产出: build/decompiled/<name>.lua（不入库）与 corpus/ledger.jsonl（入库）。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Run as `uv run python scripts/run_corpus.py`, sys.path[0] is scripts/, not
# the repo root, so the `scripts.probe_keyseq` import inside main() would not
# resolve. Under pytest the rootdir is already on the path and this is a
# no-op. NOTE: this is the real repo root, deliberately not the `ROOT` the
# ledger fixed-point test monkeypatches to a scratch directory -- that patch
# redirects where OUTPUT goes, not where code is imported from.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ledger levels are a ratchet: they only ever go up.
_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}

_L0_REASON = "compile: shipped chunk did not compile"


def key_disagreements(observed: dict[str, list[dict]]) -> list[str]:
    """Rows whose `structural_hash` group does not agree on its certification
    verdict. Empty list = the ledger's grouping key is sound for this run.

    ## The gap this closes

    The ledger's primary key is `structural_hash` ALONE, and the walk below
    resolves any disagreement inside a group by taking the higher level.
    `structure.structured._memo_key` deliberately does NOT make that
    assumption: it keys the certification memo on `(structural_hash,
    _debug_fingerprint)`, because `structural_hash` drops `source`,
    `linedefined`/`lastlinedefined`, `lineinfo`, `locvars` and upvalue names,
    every one of which `verify.normalize.compare_protos` checks. So "one
    structural hash implies one verdict" was an assumption this script MADE and
    did not CHECK, and the max-by-rank that papers over a violation is not
    reached on this corpus -- meaning a violation would have shipped a row
    whose `level` came from a different proto than its `n_insns` did.

    ## Pin, not split -- and what would flip that

    Measured 2026-08-12 (M5 task 8, re-measured from the M4 figures and
    reproducing them exactly): **16 of the 1478 shash groups carry more than
    one debug fingerprint**, holding **462** fingerprints between them (446
    more than one each), and **0 groups disagree on (level, rung, reason)** --
    so the max-by-rank is vacuous today. Splitting the key to `(shash, dfp)`
    would take the committed ledger from **1478 rows to 1924** (also measured),
    all 446 additions being duplicate verdicts, and would land in the same
    commit as `scripts/ratchet_diff.py`, whose whole job is to diff the ledger
    by row identity -- the first baseline diff would read as 1478 removed +
    1924 added. The soundness content is not the extra rows, it is that the
    assumption stops being unchecked: this function turns it into a per-run
    assertion, and `main()` refuses to write a ledger that violates it.

    **If this ever returns non-empty, the fix is to split the key**, not to
    weaken this. A disagreement means two protos with equal code shape and
    unequal debug fields certified differently, which is exactly the case
    `_debug_fingerprint` exists for.

    ## What is pinned, and what is not

    Pinned: the CERTIFICATION verdict `(level, rung, refusal_reason)` from
    `decompile_chunk`, which is what `_memo_key` claims is a function of
    `(shash, dfp)`. NOT pinned: the compile-adjusted level the ledger stores
    (`level if compile_ok else "L0"`). Two occurrences of one shape can
    legitimately differ there, because whether the whole CHUNK compiled is a
    property of the file, not of the shape -- and that case is already handled
    downstream by `_force_l0`, which AND-s `compile_ok` across the group.

    `observed` maps shash -> list of per-occurrence dicts with keys
    `file`, `proto_path`, `dfp`, `level`, `rung`, `reason`. A pure function
    over already-collected observations so it can be exercised against input
    that VIOLATES it (`tests/test_ledger_ratchet.py::
    test_key_disagreement_check_actually_rejects_a_split_group`) -- a check
    written inline over a corpus that satisfies it would go on passing if it
    were quietly weakened.
    """
    bad = []
    for shash, obs in sorted(observed.items()):
        verdicts = {(o["level"], o["rung"], o["reason"]) for o in obs}
        if len(verdicts) <= 1:
            continue
        fps = len({o["dfp"] for o in obs})
        detail = "; ".join(
            f"{o['file']}:{o['proto_path']} -> "
            f"({o['level']}, rung {o['rung']}, {o['reason']!r})"
            for o in sorted(obs, key=lambda o: (o["file"], o["proto_path"])))
        bad.append(
            f"{shash}: {len(verdicts)} distinct verdicts across {len(obs)} "
            f"occurrence(s) / {fps} debug fingerprint(s) -- the ledger key "
            f"(structural_hash alone) is not sufficient here; split it to "
            f"(structural_hash, _debug_fingerprint). {detail}")
    return bad


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
    # Private on purpose (see its docstring): the ledger key check below needs
    # exactly the fingerprint the certification memo uses, and a second,
    # public transcription of that field list is the drift this import avoids.
    from pyluadec.structure.structured import _debug_fingerprint
    from pyluadec.verify.ledger import (LedgerEntry, oracle_version, row_l2,
                                        structural_hash, write_ledger)
    from pyluadec.verify.normalize import LADDER_VERSION
    # The L2 gate (M5 task 9). Only the files with an authored key sequence
    # are probed -- five of 229, measured to be exactly the files that reach a
    # `pressButton` poll at all -- so this costs a bounded handful of
    # subprocesses, not a second corpus pass. See scripts/probe_keyseq.py.
    from scripts.probe_keyseq import KEY_SEQUENCES, evaluate as l2_evaluate

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
    # shash -> every occurrence's certification verdict, for `key_disagreements`.
    observed: dict[str, list[dict]] = {}
    n_ok = 0
    n_protos = 0
    n_structured = 0
    n_shipped_structured = 0
    n_hybrid_files = 0
    n_fallback_files = 0
    n_l2_granted = 0
    files = sorted(corpus.glob("*.lua"))
    for f in files:
        root_bytes = f.read_bytes()
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
        # Per-FILE, and recorded on every occurrence in it. `None` for the 224
        # files with no authored sequence: "not driven" and "driven and
        # refused" are different facts and the ledger keeps them apart.
        l2_field = None
        if f.name in KEY_SEQUENCES:
            l2_res = l2_evaluate(root_bytes, res.source, KEY_SEQUENCES[f.name])
            l2_field = l2_res.as_ledger_field()
            if not l2_res.granted:
                print(f"L2 REFUSED {f.name}: {l2_res.reason} "
                      f"({l2_res.detail[:160]})", file=sys.stderr)
            n_l2_granted += bool(l2_res.granted)
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
                   "hybrid": res.hybrid, "l2": l2_field}
            level = res.levels[path] if compile_ok else "L0"
            # The un-compile-adjusted verdict, which is what `_memo_key`
            # claims is a function of `(structural_hash, _debug_fingerprint)`.
            observed.setdefault(h, []).append(
                {"file": f.name, "proto_path": path, "dfp": _debug_fingerprint(p),
                 "level": res.levels[path], "rung": res.rungs[path],
                 "reason": res.reasons[path]})
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
                # The gap this used to carry -- "one structural hash implies
                # one verdict" was assumed and not checked -- is CLOSED as of
                # M5 task 8, by assertion rather than by splitting the key:
                # `key_disagreements` above is evaluated over every occurrence
                # before the ledger is written, and `main()` refuses to write a
                # ledger that violates it. The max-by-rank below therefore
                # still cannot silently paper over a real disagreement; it
                # remains vacuous on this corpus (measured 0 disagreements),
                # and if it ever stops being vacuous the run fails loudly with
                # the shash and the disagreeing occurrences named. See
                # `key_disagreements`' docstring for why pin rather than split.
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
        # Row-level `l2` is an AGGREGATE of the per-occurrence records and is
        # never measured independently; `verify.ledger.row_l2` holds the rule
        # and the argument for why it does not belong in `key_disagreements`'
        # pinned verdict.
        e.l2 = row_l2(e.occurrences)
        if not e.compile_ok:
            _force_l0(e)
    # BEFORE writing: refuse to emit a ledger whose grouping key is unsound.
    # A disagreement here means a row's `level` came from a different proto
    # than its `n_insns` did, which is not something to discover by reading a
    # diff later.
    bad_keys = key_disagreements(observed)
    if bad_keys:
        print(f"LEDGER KEY UNSOUND: {len(bad_keys)} structural_hash group(s) "
              f"disagree on their certification verdict; ledger NOT written.",
              file=sys.stderr)
        for line in bad_keys:
            print(f"  {line}", file=sys.stderr)
        return 1
    write_ledger(list(by_hash.values()), ROOT / "corpus" / "ledger.jsonl")
    n_l3 = sum(1 for e in by_hash.values() if e.level == "L3")
    # Report the exposure the check above covers, so the figure quoted in
    # `key_disagreements`' docstring is re-derivable from an ordinary run
    # rather than from a scratch script.
    multi_fp = [obs for obs in observed.values() if len({o["dfp"] for o in obs}) > 1]
    n_fps = sum(len({o["dfp"] for o in obs}) for obs in multi_fp)
    print(f"ledger key: {len(multi_fp)}/{len(by_hash)} shash group(s) carry >1 "
          f"debug fingerprint ({n_fps} fingerprints between them); "
          f"{len(bad_keys)} disagree on (level, rung, reason)")
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
    n_l2_rows = sum(1 for e in by_hash.values() if e.l2)
    print(f"L2: {n_l2_granted}/{len(KEY_SEQUENCES)} authored file(s) granted; "
          f"{n_l2_rows}/{len(by_hash)} row(s) carry the badge "
          f"({len(KEY_SEQUENCES)}/{len(files)} files have a key sequence)")
    return 0 if n_ok == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())

"""台账面板：corpus/ledger.jsonl 的可读汇总。用法: uv run python scripts/ledger_dashboard.py [--markdown]"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _refusal_key(reason: str) -> str:
    """Collapse a row's `refusal_reason` to its cluster.

    The reason is per-proto and carries positions (`structure: pc 41: if
    targets out of range`, `structure: pc 4: branch body block at pc 702 is
    unreachable`, `mismatch: const[7]`); a histogram over the raw strings has
    nearly as many buckets as rows, which defeats the point of putting it on
    the dashboard. The varying parts are numbers -- a pc, a register, a
    statement count, a constant index -- but **not always as a standalone
    decimal token**, which is where this function has already been wrong once:
    it was written when "every varying part is a NUMBER [token]" was true, and
    M5 task 6 added the `mismatch: <field> at root/<N>` form (a mismatch found
    in a DESCENDANT during hybrid certification) without that premise being
    re-checked. `root/48` and `root/59` are not decimal tokens, so the
    committed ledger's 11 `code` mismatches showed up as three buckets
    (`mismatch: code` 9, `... at root/48` 1, `... at root/59` 1) where they
    are one cluster.

    Three shapes are normalised, and the third is the M5 addition:

      "structure: pc 41: if targets out of range"
        -> "structure: pc N: if targets out of range"
      "mismatch: const[7]"          -> "mismatch: const[i]"
      "mismatch: code at root/59"   -> "mismatch: code at root/N"

    That leaves the committed ledger's 11 `code` mismatches as **two** rows,
    not one: `mismatch: code` 9 and `mismatch: code at root/N` 2. Deliberate.
    Only the INDEX varies and it is gone; what remains is a kind distinction
    the same normalisation preserves everywhere else -- `pc 41` collapses to
    `pc N` rather than disappearing -- and it is the difference between "this
    proto's own field differed" and "a descendant's did, during hybrid
    certification", which is the more useful of the two facts to see on a
    dashboard.

    If the vocabulary grows another shape, this needs the same treatment --
    the histogram silently splitting a cluster is the failure mode, and it is
    quiet.

    Cosmetic only: this function exists for the dashboard's histogram. The
    ledger keeps the exact reason, and `tests/test_m4_exit.py` asserts on
    that, not on this.
    """
    out = []
    for tok in reason.split(" "):
        core = tok.rstrip(":,;")
        tail = tok[len(core):]
        head, sep, idx = core.rpartition("/")
        if core.isdigit():
            out.append("N" + tail)
        elif core.startswith("const[") and core.endswith("]"):
            out.append("const[i]" + tail)
        elif sep and idx.isdigit():
            out.append(f"{head}/N" + tail)
        else:
            out.append(tok)
    return " ".join(out)


def main() -> int:
    md = "--markdown" in sys.argv[1:]
    path = ROOT / "corpus" / "ledger.jsonl"
    if not path.exists():
        print("no ledger; run scripts/run_corpus.py first", file=sys.stderr)
        return 1
    entries = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    levels = Counter(e["level"] for e in entries)
    refusals = Counter(_refusal_key(e.get("refusal_reason")) for e in entries
                       if e.get("refusal_reason"))
    reasons = Counter(c["reason"] for e in entries for c in e["confessions"])
    n_occ = sum(len(e["occurrences"]) for e in entries)
    n_files = len({o["file"] for e in entries for o in e["occurrences"]})
    compile_ok = sum(1 for e in entries if e["compile_ok"])
    fallback = sum(1 for e in entries if e["fallback"])
    oracle_v = {e["oracle"] for e in entries}
    ladder_v = {e["ladder"] for e in entries}

    # Shipping, as opposed to certification (M5 task 6). `level` says which
    # protos were PROVED equal to the original; these say which emitter
    # actually produced the text in `build/decompiled/`. The two are
    # independent since hybrid emission, and a dashboard that only reported
    # the first would not show a file quietly dropping back to a whole-file
    # state machine.
    # Indexed, not `.get(...)`-with-a-default (M5 task 6 round 1, F8): the
    # defaults were `"structured"` and `False`, so a pre-M5-task-6 row -- one
    # written before the schema existed, or by a half-migrated writer -- would
    # be silently counted as fully structured. That is exactly the "a file
    # quietly dropped back to a whole-file state machine" case the comment
    # above says this panel exists to show, reported as its opposite. A
    # `KeyError` naming the missing field is the better failure: this is a
    # read-only panel over a ledger that `scripts/run_corpus.py` regenerates
    # whole, so there is no partial-schema ledger worth tolerating.
    occs = [o for e in entries for o in e["occurrences"]]
    shipped = Counter(o["shipped"] for o in occs)
    by_file: dict[str, dict] = {}
    for o in occs:
        f = by_file.setdefault(o["file"], {"hybrid": False, "fb": 0, "n": 0})
        f["hybrid"] = f["hybrid"] or o["hybrid"]
        f["fb"] += o["shipped"] == "fallback"
        f["n"] += 1
    n_hybrid = sum(1 for f in by_file.values() if f["hybrid"])
    n_whole_fb = sum(1 for f in by_file.values()
                     if not f["hybrid"] and f["fb"] == f["n"])

    # L2 differential execution (M5 task 9). Reported in the `L2@cov%` form the
    # spec asks for, and reported on BOTH bases -- rows and occurrences --
    # because `l2` is measured per FILE and aggregated onto rows by
    # `verify.ledger.row_l2`, so the two numbers answer different questions.
    # The refusal histogram is next to it for the same reason
    # `refusal_reason`'s is: a file that stops being granted must show up as
    # data, not as an absence.
    l2_rows = [e for e in entries if e.get("l2") and "cov" in e["l2"]]
    l2_occs = [o for o in occs if o.get("l2") and "cov" in o["l2"]]
    l2_refused = Counter(o["l2"]["refused"] for o in occs
                         if o.get("l2") and "refused" in o["l2"])
    l2_files = {o["file"] for o in occs if o.get("l2")}
    l2_files_granted = {o["file"] for o in l2_occs}
    l2_by_file = {o["file"]: o["l2"]["cov"] for o in l2_occs}

    l3 = levels.get("L3", 0)
    # Occurrence basis as well as unique-shape basis: the ledger dedups by
    # structural_hash, so "% of unique protos" and "% of the 1944 protos that
    # actually exist" are different numbers and can move independently.
    occ_l3 = sum(len(e["occurrences"]) for e in entries if e["level"] == "L3")
    rungs = Counter(e["l3_level"] for e in entries if e["level"] == "L3")

    rows = [
        ("unique protos", len(entries)),
        ("occurrences", n_occ),
        ("files", n_files),
        ("compile_ok", f"{compile_ok}/{len(entries)}"),
        ("fallback", f"{fallback}/{len(entries)}"),
        *[(f"level {k}", v) for k, v in sorted(levels.items())],
        ("L3 share (unique)", f"{l3}/{len(entries)} ({l3 / len(entries):.1%})"),
        ("L3 share (occurrences)", f"{occ_l3}/{n_occ} ({occ_l3 / n_occ:.1%})"),
        ("shipped structured", f"{shipped['structured']}/{n_occ} "
                               f"({shipped['structured'] / n_occ:.1%})"),
        ("files fully structured", n_files - n_hybrid - n_whole_fb),
        ("files hybrid", n_hybrid),
        ("files whole-file fallback", n_whole_fb),
        ("L2 files driven", f"{len(l2_files_granted)}/{len(l2_files)} granted "
                            f"(of {n_files} in the corpus)"),
        ("L2 share (rows)", f"{len(l2_rows)}/{len(entries)} "
                            f"({len(l2_rows) / len(entries):.1%})"),
        ("L2 share (occurrences)", f"{len(l2_occs)}/{n_occ} "
                                   f"({len(l2_occs) / n_occ:.1%})"),
        # Per FILE, not per row. A row-basis median is dominated by whichever
        # driven file happens to have the most protos -- with the M5 task 9
        # sequence set that was snr_common, 147 of 161 badged rows, so the
        # panel printed its badge as both the min and the median of a
        # five-file population. Files are the population `l2` is measured over.
        *([("L2 badge per file, min/median/max",
            "L2@{:.0%} / L2@{:.0%} / L2@{:.0%}".format(
                min(l2_by_file.values()),
                sorted(l2_by_file.values())[len(l2_by_file) // 2],
                max(l2_by_file.values())))] if l2_by_file else []),
        *[(f"L2 refused: {k}", v) for k, v in l2_refused.most_common()],
        # `(kv[0] is None, kv[0])`, not `kv[0]`: an `L3` row is supposed to
        # carry a rung, but if one ever did not, plain `sorted` would raise
        # `TypeError: '<' not supported between 'NoneType' and 'int'` -- and
        # this dashboard is precisely the tool you reach for when that
        # invariant has broken. Sorting Nones last keeps it printable.
        *[(f"L3 rung {k}", v)
          for k, v in sorted(rungs.items(), key=lambda kv: (kv[0] is None, kv[0]))],
        *[(f"confession: {k}", v) for k, v in reasons.most_common(10)],
        # Standing residual census: `refusal_reason` is the field that says
        # WHY a row is not L3 (M4 task 6). Truncated to the kind + first line
        # so the histogram clusters rather than listing 89 distinct strings.
        *[(f"refusal: {k[:68] + '...' if len(k) > 71 else k}", v)
          for k, v in refusals.most_common(12)],
        ("oracle", ", ".join(sorted(oracle_v))),
        ("ladder", ", ".join(sorted(ladder_v))),
    ]
    if md:
        print("| metric | value |\n|---|---|")
        for k, v in rows:
            print(f"| {k} | {v} |")
    else:
        w = max(len(k) for k, _ in rows)
        for k, v in rows:
            print(f"{k:<{w}}  {v}")

    # Name names. A dashboard that only ever reports aggregates cannot be
    # acted on: "compile_ok 1477/1478" tells you something is broken but not
    # what to open. Every entry that failed to compile or is still L0 is
    # printed individually, identified by its shash prefix and the first file
    # / proto_path it occurs in (deferred minor from the M2 review; closed
    # in M3 task 8).
    problems = [e for e in entries if not e["compile_ok"] or e["level"] == "L0"]
    print()
    if md:
        print("### problem entries\n")
    else:
        print("problem entries")
    if not problems:
        print("_(none)_" if md else "(none)")
        return 0
    if md:
        print("| shash | file | proto_path | level | compile_ok |\n|---|---|---|---|---|")
    for e in sorted(problems, key=lambda e: e["shash"]):
        occ = e["occurrences"][0]
        if md:
            print(f"| {e['shash'][:12]} | {occ['file']} | {occ['proto_path']} "
                  f"| {e['level']} | {e['compile_ok']} |")
        else:
            print(f"  {e['shash'][:12]}  {occ['file']}:{occ['proto_path']}  "
                  f"level={e['level']} compile_ok={e['compile_ok']} "
                  f"(+{len(e['occurrences']) - 1} more occurrences)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

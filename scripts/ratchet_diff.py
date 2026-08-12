"""台账 ratchet：把历史 baseline 与当前 `corpus/ledger.jsonl` 逐行对比，
任何降级即失败（spec §5 的完整形态，M5 task 8）。

    uv run python scripts/ratchet_diff.py OLD.jsonl NEW.jsonl

Exit codes -- chosen for `git bisect run`, which reads 0 as good, 125 as skip,
and anything else in 1..127 as bad:

    0   no regression (upgrades, added rows and schema differences are fine)
    1   at least one regression; the offending rows are printed
    2   usage / unreadable input -- NOT a verdict about the tree

## What this adds that the existing gates do not

`tests/test_ledger_ratchet.py` proves the committed ledger is a byte-exact
fixed point of `scripts/run_corpus.py`, and `tests/test_m3_exit.py` /
`tests/test_m4_exit.py` pin within-row coupling (level vs rung vs confession vs
reason) and rate floors. None of them compares against a **committed historical
baseline**: before this script, a regenerated ledger with fewer `L3` rows
passed the whole suite as long as the rate stayed above the floor and no `L0`
appeared. "Levels only ever go up" was discipline plus a human reading the
diff.

It is also what makes the deliberately slack floors safe. A floor set at the
measurement is a tripwire, not a gate (`test_m4_exit.py` argues this at
length), so `tests/test_sir_while.py`'s census floor is measured-minus-10 and
the exit floors sit points below what is achieved. Both gaps are the same gap,
and this is the instrument that closes it: the floors keep catching
catastrophes without churning, and the baseline diff catches the 1-row
regression that stays inside them.

## The six regressions

| kind | meaning |
| --- | --- |
| `level-downgrade` | a row's `level` fell (`L3` -> `L1`, anything -> `L0`) |
| `rung-downgrade` | a row is `L3` in both but needed MORE normalization, or lost its rung entirely |
| `row-removed` | a `shash` present in the baseline is gone |
| `reason-regression` | an `L3` row carries a `refusal_reason` |
| `shipping-regression` | an occurrence's `shipped` went `structured` -> `fallback` |
| `new-l0` | a row arrived at `L0` |

`rung-downgrade` reads the ladder in the right direction: `l3_level` = k means
`verify/normalize.NORMALIZATIONS[:k]` were applied before comparing, so a
HIGHER number is a WEAKER proof (rung 0 is strict field-for-field equality).

Regressions print grouped by `refusal_reason` cluster -- the kind before the
first colon, the vocabulary `tests/test_m4_exit.py::REASON_KINDS` commits to.
That clustering is why M4 added the field: a regression that shows up as
"12 rows, all `structure: ... back edge`" names the recognizer that broke,
where 12 unequal strings name nothing.

## What is deliberately NOT a regression

Added rows, level upgrades, rung improvements, `fallback -> structured`
shipping changes, and fields present on one side only. The last is the
"schema-annotated change" case: a baseline written before M4's
`refusal_reason` or M5 task 6's per-occurrence `shipped` must stay diffable on
what it does carry, and the omission is reported in the summary rather than
read as a mass regression. Schema tolerance is per-field and per-row, so a
level downgrade in a ledger whose baseline lacks `refusal_reason` still fails
(`tests/test_ratchet_diff.py::test_a_missing_field_does_not_hide_a_real_downgrade`).

Non-vacuity is the deliverable: every kind above has its own committed test
that feeds a hand-mutated copy of the real ledger and asserts a non-zero exit
naming the row. See `tests/test_ratchet_diff.py`.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Same ordering as `scripts/run_corpus.py::_RANK`; duplicated rather than
# imported because this script must be runnable from a copy OUTSIDE the tree
# (the `git bisect run` predicate keeps it in /tmp so it survives checkouts of
# commits that predate it -- see docs/runbooks/structured-pipeline.md).
LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}

NO_REASON = "(no reason recorded)"


def cluster_of(reason: str | None) -> str:
    """The `refusal_reason` KIND: everything before the first colon.

    `tests/test_m4_exit.py::REASON_KINDS` is the committed vocabulary
    (`structure`, `reconstruct`, `compile`, `mismatch`); the rest of the string
    carries pcs and register numbers and is expected to churn, which is exactly
    why grouping is by kind. Unknown kinds are not rejected here -- an
    unclustered regression is still a regression, and it is `test_m4_exit.py`'s
    job to notice a reason outside the vocabulary."""
    if not reason or not reason.strip():
        return NO_REASON
    head = reason.split(":", 1)[0].strip()
    return head or NO_REASON


@dataclass(frozen=True)
class Regression:
    kind: str
    shash: str
    cluster: str
    detail: str


@dataclass
class DiffReport:
    old_rows: int = 0
    new_rows: int = 0
    common: int = 0
    removed: int = 0
    added: int = 0
    level_upgrades: int = 0
    level_downgrades: int = 0
    rung_downgrades: int = 0
    shipping_gained: int = 0
    shipping_lost: int = 0
    old_l3: int = 0
    new_l3: int = 0
    old_occurrences: int = 0
    new_occurrences: int = 0
    schema_notes: list[str] = field(default_factory=list)
    regressions: list[Regression] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.regressions


def load_rows(path: Path | str) -> list[dict]:
    """Parse a ledger jsonl into plain dicts.

    Deliberately NOT `verify.ledger.read_ledger`: that constructs
    `LedgerEntry`, which would reject a baseline carrying a field this version
    has since dropped and would silently DEFAULT one it has since added --
    both of which this script needs to see as schema facts rather than have
    normalized away. Plain dicts also keep the script importable from a copy
    outside the tree."""
    out = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{n}: not JSON: {e}") from e
    return out


def _occurrence_index(rows: list[dict]) -> dict[tuple[str, str], tuple[str, dict]]:
    """`(file, proto_path)` -> `(shash, occurrence)`.

    Indexed globally rather than within a row because a proto occurrence is
    identified by where it lives, not by which shape row happens to hold it: if
    a proto's `structural_hash` changes, the shipping comparison should still
    work (the row identity change is separately reported as removed + added)."""
    idx: dict[tuple[str, str], tuple[str, dict]] = {}
    for r in rows:
        for o in r.get("occurrences", ()):
            idx[(o.get("file", ""), o.get("proto_path", ""))] = (r["shash"], o)
    return idx


def _rank(level: str) -> int:
    return LEVEL_RANK.get(level, -1)


def _schema_notes(old: list[dict], new: list[dict], rep: DiffReport) -> None:
    def row_keys(rows) -> set[str]:
        out: set[str] = set()
        for r in rows:
            out |= set(r)
        return out

    def occ_keys(rows) -> set[str]:
        out: set[str] = set()
        for r in rows:
            for o in r.get("occurrences", ()):
                out |= set(o)
        return out

    row_old, row_new = row_keys(old), row_keys(new)
    occ_old, occ_new = occ_keys(old), occ_keys(new)
    for label, a, b in (("row", row_old, row_new), ("occurrence", occ_old, occ_new)):
        for f in sorted(b - a):
            rep.schema_notes.append(
                f"schema: NEW adds {label} field `{f}`; baseline lacks it, so "
                f"checks needing it are skipped for baseline rows")
        for f in sorted(a - b):
            rep.schema_notes.append(
                f"schema: NEW drops {label} field `{f}` present in the baseline")


def diff_ledgers(old: list[dict], new: list[dict]) -> DiffReport:
    """Compare two parsed ledgers. Pure over already-parsed rows so the checks
    can be exercised against rows that VIOLATE them -- an assertion written
    inline over the committed ledger only ever runs against data that satisfies
    it (`test_m4_exit.py::reason_violations` makes the same move)."""
    rep = DiffReport(old_rows=len(old), new_rows=len(new))
    old_by = {r["shash"]: r for r in old}
    new_by = {r["shash"]: r for r in new}
    rep.old_l3 = sum(1 for r in old if r.get("level") == "L3")
    rep.new_l3 = sum(1 for r in new if r.get("level") == "L3")
    rep.old_occurrences = sum(len(r.get("occurrences", ())) for r in old)
    rep.new_occurrences = sum(len(r.get("occurrences", ())) for r in new)
    rep.added = len(set(new_by) - set(old_by))
    rep.common = len(set(new_by) & set(old_by))
    _schema_notes(old, new, rep)

    for shash in sorted(set(old_by) - set(new_by)):
        rep.removed += 1
        o = old_by[shash]
        rep.regressions.append(Regression(
            kind="row-removed", shash=shash,
            cluster=cluster_of(o.get("refusal_reason")),
            detail=f"present in baseline at {o.get('level')}, absent now "
                   f"({len(o.get('occurrences', ()))} occurrence(s), "
                   f"first {_first_occ(o)})"))

    for shash in sorted(set(new_by) - set(old_by)):
        n = new_by[shash]
        if n.get("level") == "L0":
            rep.regressions.append(Regression(
                kind="new-l0", shash=shash,
                cluster=cluster_of(n.get("refusal_reason")),
                detail=f"new row arrives at L0 (first {_first_occ(n)})"))

    for shash in sorted(set(old_by) & set(new_by)):
        o, n = old_by[shash], new_by[shash]
        ol, nl = o.get("level"), n.get("level")
        if _rank(nl) < _rank(ol):
            rep.level_downgrades += 1
            rep.regressions.append(Regression(
                kind="level-downgrade", shash=shash,
                cluster=cluster_of(n.get("refusal_reason")),
                detail=f"{ol} -> {nl} (first {_first_occ(n)})"
                       f"{_reason_suffix(n)}"))
            continue          # its rung/reason follow from the level; one row,
                              # one finding, so the cluster counts are row counts
        if _rank(nl) > _rank(ol):
            rep.level_upgrades += 1
        # A rung is only comparable when BOTH sides certified: `l3_level` is
        # `None` by construction on a non-`L3` row.
        if ol == "L3" and nl == "L3":
            orung, nrung = o.get("l3_level"), n.get("l3_level")
            if nrung is None and orung is not None:
                rep.rung_downgrades += 1
                rep.regressions.append(Regression(
                    kind="rung-downgrade", shash=shash,
                    cluster=cluster_of(n.get("refusal_reason")),
                    detail=f"still L3 but lost its rung (was rung {orung}, now "
                           f"None) -- a certification claim with no recorded "
                           f"evidence"))
            elif (isinstance(orung, int) and isinstance(nrung, int)
                  and nrung > orung):
                rep.rung_downgrades += 1
                rep.regressions.append(Regression(
                    kind="rung-downgrade", shash=shash,
                    cluster=cluster_of(n.get("refusal_reason")),
                    detail=f"rung {orung} -> {nrung}: more normalization was "
                           f"needed, so the proof is weaker"))
        # `refusal_reason` is present-only-if-carried, so an absent key on the
        # NEW side is a schema fact (reported above), not a silent pass: the
        # check below fires on what NEW actually says.
        if nl == "L3" and (r := n.get("refusal_reason")) and str(r).strip():
            rep.regressions.append(Regression(
                kind="reason-regression", shash=shash, cluster=cluster_of(r),
                detail=f"certified L3 yet claims a refusal reason {r!r}"))

    old_occ, new_occ = _occurrence_index(old), _occurrence_index(new)
    for key in sorted(set(old_occ) & set(new_occ)):
        _, oo = old_occ[key]
        nshash, no = new_occ[key]
        os_, ns = oo.get("shipped"), no.get("shipped")
        if os_ is None or ns is None:      # baseline predates M5 task 6
            continue
        if os_ == "structured" and ns == "fallback":
            rep.shipping_lost += 1
            rep.regressions.append(Regression(
                kind="shipping-regression", shash=nshash,
                cluster=cluster_of(new_by.get(nshash, {}).get("refusal_reason")),
                detail=f"{key[0]}:{key[1]} shipped structured, now fallback"))
        elif os_ == "fallback" and ns == "structured":
            rep.shipping_gained += 1
    return rep


def _first_occ(row: dict) -> str:
    occ = row.get("occurrences") or []
    if not occ:
        return "no occurrences"
    return f"{occ[0].get('file', '?')}:{occ[0].get('proto_path', '?')}"


def _reason_suffix(row: dict) -> str:
    r = row.get("refusal_reason")
    return f" now says {r!r}" if r else ""


def _pct(n: int, d: int) -> str:
    return f"{n}/{d} ({n / d:.1%})" if d else f"{n}/0"


def format_report(rep: DiffReport, old_path: str, new_path: str) -> str:
    out: list[str] = []
    out.append(f"ratchet: OLD {old_path} ({rep.old_rows} rows, "
               f"{rep.old_occurrences} occurrences)")
    out.append(f"         NEW {new_path} ({rep.new_rows} rows, "
               f"{rep.new_occurrences} occurrences)")
    out.append(f"  rows:     {rep.common} common, {rep.removed} removed, "
               f"{rep.added} added")
    out.append(f"  levels:   {rep.level_upgrades} upgraded, "
               f"{rep.level_downgrades} downgraded")
    out.append(f"  rungs:    {rep.rung_downgrades} downgraded")
    out.append(f"  shipping: {rep.shipping_gained} occurrence(s) "
               f"fallback -> structured, {rep.shipping_lost} structured -> "
               f"fallback")
    out.append(f"  L3 rate:  {_pct(rep.old_l3, rep.old_rows)} -> "
               f"{_pct(rep.new_l3, rep.new_rows)}")
    for note in rep.schema_notes:
        out.append(f"  {note}")
    if rep.ok:
        out.append("OK: no regression.")
        return "\n".join(out)

    by_cluster: dict[str, list[Regression]] = defaultdict(list)
    for r in rep.regressions:
        by_cluster[r.cluster].append(r)
    out.append("")
    out.append(f"REGRESSIONS ({len(rep.regressions)}), grouped by "
               f"refusal_reason cluster:")
    for cluster in sorted(by_cluster):
        rows = sorted(by_cluster[cluster], key=lambda r: (r.kind, r.shash))
        out.append("")
        out.append(f"  cluster `{cluster}` ({len(rows)} row(s)):")
        for r in rows:
            out.append(f"    {r.kind:<20} {r.shash}")
            out.append(f"      {r.detail}")
    out.append("")
    out.append(f"ratchet FAILED: {len(rep.regressions)} regression(s). Levels "
               f"only ever go up -- fix the decompiler, not the ledger.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) != 2:
        print("usage: ratchet_diff.py OLD.jsonl NEW.jsonl\n"
              "  compares two corpus/ledger.jsonl snapshots; exits 1 on any "
              "downgrade,\n  2 on a usage or I/O error (never 1 -- `git bisect "
              "run` reads 1 as 'bad').", file=sys.stderr)
        return 2
    try:
        old = load_rows(args[0])
        new = load_rows(args[1])
    except (OSError, ValueError) as e:
        print(f"ratchet_diff: cannot read ledger: {e}", file=sys.stderr)
        return 2
    rep = diff_ledgers(old, new)
    print(format_report(rep, args[0], args[1]))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())

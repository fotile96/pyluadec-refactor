"""台账 ratchet：把历史 baseline 与当前 `corpus/ledger.jsonl` 逐行对比，
任何降级即失败（spec §5 的完整形态，M5 task 8）。

    uv run python scripts/ratchet_diff.py OLD.jsonl NEW.jsonl

## Exit codes, and the `git bisect run` contract they are built against

`git-bisect(1)` (git 2.39.5, verified on this host 2026-08-12) says: *"the
script ... should exit with code 0 if the current source code is good/old, and
exit with a code between 1 and 127 (inclusive), **except 125**, if the current
source code is bad/new. Any other exit code will abort the bisect process. The
special exit code 125 should be used when the current source code cannot be
tested."*

**So there is no low exit code that means "no verdict".** An earlier revision
of this script returned 2 for usage/IO errors and claimed that was safer than
1; it is not -- 2 is in 1..127 and is read as BAD, exactly like 1. Measured, on
a scratch repo with six commits and a predicate that unconditionally `exit 2`s:
`git bisect run` reported *"b07bfbd ... is the first bad commit"*, i.e. it
blamed the first commit after the known-good one. A mistyped predicate would
therefore have converged, silently and confidently, on an innocent commit.
(`python /tmp/rd.py` on a path that does not exist also exits 2 -- from the
interpreter, before this file is even read -- so 2 was doubly the wrong choice.)

The two codes that are genuinely not a verdict are 125 and >=128, and both were
measured on the same scratch repo:

    0     good: no regression (upgrades, added rows, schema additions)
    1     bad:  at least one regression; the offending rows are printed
    125   this TREE cannot be judged -- the NEW ledger is missing, unreadable
          or malformed. git SKIPS the commit; a predicate that returns it
          everywhere ends the bisect with "There are only 'skip'ped commits
          left to test", which names the problem instead of blaming a commit.
    128   this INSTRUMENT is misconfigured -- wrong arguments, or a baseline
          that cannot be read or is itself malformed. Neither depends on the
          commit under test, so the right response is to stop the whole run,
          and git does: "error: bisect run failed: exit code 128 ... is < 0 or
          >= 128".

Both non-verdict codes are also outside the range CPython itself produces (1 on
an uncaught exception, 2 on a missing script or an argparse error), so a fault
in the *runner* can never be confused with a verdict from this script.

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

## The seven regressions

| kind | meaning |
| --- | --- |
| `level-downgrade` | a row's `level` fell (`L3` -> `L1`, anything -> `L0`) |
| `rung-downgrade` | a row is `L3` in both but needed MORE normalization, or lost its rung entirely |
| `row-removed` | a `shash` present in the baseline is gone |
| `occurrence-removed` | a `(file, proto_path)` the baseline walked is no longer walked, while its row survives |
| `reason-regression` | an `L3` row carries a `refusal_reason` |
| `shipping-regression` | an occurrence's `shipped` went `structured` -> `fallback` |
| `new-l0` | a row arrived at `L0` |

`occurrence-removed` covers the shape a per-ROW diff cannot see: the ledger's
1944 occurrences are 1478 rows, so a proto vanishing from `walk_proto_paths`
leaves every row intact and only shortens one `occurrences` list. It is pinned
inside `scripts/ratchet_job.sh` by gate 1 (`tests/test_ledger_ratchet.py` fixes
the count at 1944), but the `git bisect run` predicate runs this script ALONE,
where before M5 task 8 round 1 a lost proto was invisible: measured on the
committed ledger, popping one occurrence off a two-occurrence row gave 0
regressions and exit 0 while the summary line printed `1944 -> 1943` two lines
above. Occurrences whose row also disappeared are reported once, as
`row-removed`, rather than twice.

`rung-downgrade` reads the ladder in the right direction: `l3_level` = k means
`verify/normalize.NORMALIZATIONS[:k]` were applied before comparing, so a
HIGHER number is a WEAKER proof (rung 0 is strict field-for-field equality).

Regressions print grouped by `refusal_reason` cluster -- the kind before the
first colon, the vocabulary `tests/test_m4_exit.py::REASON_KINDS` commits to.
That clustering is why M4 added the field: a regression that shows up as
"12 rows, all `structure: ... back edge`" names the recognizer that broke,
where 12 unequal strings name nothing.

## What is deliberately NOT a regression

Added rows, level upgrades, rung improvements, and `fallback -> structured`
shipping changes.

Also **fields the OLD side lacks** -- the "schema-annotated change" case: a
baseline written before M4's `refusal_reason` or M5 task 6's per-occurrence
`shipped` must stay diffable on what it does carry, and the omission is
reported in the summary rather than read as a mass regression. Tolerance is
per-field and per-row, so a level downgrade in a ledger whose baseline lacks
`refusal_reason` still fails
(`tests/test_ratchet_diff.py::test_a_missing_field_does_not_hide_a_real_downgrade`).

The **other** direction -- a field the NEW side has DROPPED -- is not tolerated,
and deliberately so: the checks read NEW's own words, so a dropped field either
reads as the regression it would be or is reported as a schema note. Measured
on the committed ledger, dropping a field from every NEW row: `level` -> 1478
`level-downgrade`s, `l3_level` -> 1430 `rung-downgrade`s (every `L3` row loses
its evidence), `refusal_reason` -> 0 (its check fires on what NEW says, and NEW
says nothing), per-occurrence `shipped` -> 0 (the comparison needs both sides).
The first two are fail-safe, the last two fail-open but are covered by the
schema note. Do not read the "schema" line as an amnesty in either direction.

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

# See the module docstring for the measured `git bisect run` contract behind
# these four values. 2 is NOT among them: git reads it as "bad".
EXIT_OK = 0
EXIT_REGRESSION = 1
EXIT_UNTESTABLE = 125     # git bisect: skip this commit
EXIT_BROKEN = 128         # git bisect: abort the run


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
    occurrences_removed: int = 0
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
    """Parse a ledger jsonl into plain dicts, and check the little the diff
    actually relies on. Raises `ValueError` (or `OSError`) on anything it
    cannot diff; `main` turns that into a non-verdict exit code.

    Deliberately NOT `verify.ledger.read_ledger`: that constructs
    `LedgerEntry`, which would reject a baseline carrying a field this version
    has since dropped and would silently DEFAULT one it has since added --
    both of which this script needs to see as schema facts rather than have
    normalized away. Plain dicts also keep the script importable from a copy
    outside the tree.

    Validating here rather than inside `diff_ledgers` is what keeps a malformed
    ledger from being reported as a verdict about the tree. Before M5 task 8
    round 1 a row missing `shash` raised `KeyError: 'shash'` out of
    `diff_ledgers`, straight past `main`'s handler (which wrapped only the
    parse), and CPython turned the traceback into exit 1 -- which `git bisect
    run` reads as "bad commit". An instrument fault must never be reported as a
    tree verdict.

    Row identity is `shash`, so duplicates are rejected too: `dict`
    construction downstream is last-wins, and a downgraded duplicate placed
    BEFORE the good row was measured to pass with 0 regressions (it fails
    correctly when placed after). `write_ledger` cannot emit duplicates and
    `tests/test_ledger_ratchet.py` pins uniqueness, but the bisect predicate
    runs this script alone, against files it did not produce.

    ## Which fields are type-checked, and why exactly these

    Every field `diff_ledgers` DEREFERENCES rather than merely compares:

    | field | why the diff would break without the check | measured, guard removed |
    | --- | --- | --- |
    | the row itself | `.get` on a scalar -> `AttributeError`, which is not `ValueError` and so escaped `main`'s handler entirely (round 2, N1) | traceback, **exit 1** |
    | `shash` | dict key and row identity | traceback, **exit 1** |
    | `occurrences` | iterated, and each entry is `.get`-ed | `TypeError` traceback, **exit 1** (non-list) / **128** (list of non-objects) |
    | `file` / `proto_path` | tuple-keyed into `_occurrence_index`; a list here is unhashable | **128** |
    | `level` | `LEVEL_RANK.get(level)` -- a dict lookup, so an UNHASHABLE level raises `TypeError` (round 3, New 1) | **128** |
    | `l3_level` | compared with `>`; a str slipped past both the `is None` and the `isinstance(int)` branch, so rung `0` -> `"one"` scored 0 regressions (round 2, N2) | **exit 0**, a missed downgrade |
    | `refusal_reason` | `.split(":", 1)` in `cluster_of` (round 2, N3) | **128** -- but only when the row ALSO regresses; on a non-regressing row `cluster_of` is never called and it is **exit 0** |

    Every "measured, guard removed" cell above was run this session against the
    real ledger, mutated whole rather than as a one-row fixture.

    **`level` is the correction round 3 had to make to this very table.** Round
    2 argued that fields which are only COMPARED need no check, "because an
    unknown or missing `level` ranks -1 via `LEVEL_RANK.get`, so it reads as a
    downgrade". Measured: that is true of `3`, `None`, `"L9"` and `True`, and
    false of `["L3"]` and `{"a": 1}` -- `_rank` raises `TypeError: cannot use
    'list' as a dict key`, and end to end a NEW ledger with an unhashable
    `level` exited **128 (abort)** where the contract says 125. `LEVEL_RANK.get`
    is a dereference, not a comparison, so `level` belongs in the table above.

    With the guard, measured end to end this session: a present non-string
    `level` -- `["L3"]`, `{"a": 1}`, `3`, `true` alike -- is **125**, while
    `null`/absent and an unknown STRING such as `"L9"` still rank -1 and read
    as a `level-downgrade` (**exit 1**), which is what keeps the module
    docstring's "NEW dropped `level` -> 1478 downgrades" true.

    What is still deliberately NOT checked is `shipped`: it is only ever
    compared with `==`, which is total, and a value of any type simply is not
    `"structured"`. Nor is any field CHECKED FOR PRESENCE -- absent is not
    malformed, so a missing field stays a schema note. That distinction is what
    keeps the module docstring's "NEW dropped a field" measurements (1478 /
    1430 / 0 / 0) findings rather than load errors; re-measured this session,
    unchanged.

    Absent is not the same as malformed, throughout: a field that is missing
    stays missing and is reported as a schema note. Only a field that is
    PRESENT with an undiffable type is an error.
    """
    def bad(n: int, msg: str) -> ValueError:
        return ValueError(f"{path}:{n}: {msg}")

    out = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{n}: not JSON: {e}") from e
        if not isinstance(row, dict):
            raise bad(n, f"ledger row is {type(row).__name__}, expected a JSON "
                         f"object")
        shash = row.get("shash")
        if not isinstance(shash, str) or not shash:
            raise bad(n, f"ledger row has no usable `shash` ({shash!r}); row "
                         f"identity is undefined")
        occ = row.get("occurrences", ())
        if not isinstance(occ, (list, tuple)) or any(
                not isinstance(o, dict) for o in occ):
            raise bad(n, f"`occurrences` of {shash} is not a list of objects")
        for o in occ:
            for f in ("file", "proto_path"):
                if f in o and not isinstance(o[f], str):
                    raise bad(n, f"occurrence `{f}` of {shash} is "
                                 f"{type(o[f]).__name__}, expected a string")
        level = row.get("level")
        if level is not None and not isinstance(level, str):
            raise bad(n, f"`level` of {shash} is {type(level).__name__}; "
                         f"`LEVEL_RANK.get` is a dict lookup, so an unhashable "
                         f"level crashes the rank comparison")
        rung = row.get("l3_level")
        # `bool` is an `int` subclass and would compare as 0/1 -- not a rung.
        if rung is not None and (isinstance(rung, bool)
                                 or not isinstance(rung, int)):
            raise bad(n, f"`l3_level` of {shash} is {rung!r}; a rung must be an "
                         f"integer or null, and a non-integer would slip past "
                         f"the rung comparison unnoticed")
        reason = row.get("refusal_reason")
        if reason is not None and not isinstance(reason, str):
            raise bad(n, f"`refusal_reason` of {shash} is "
                         f"{type(reason).__name__}, expected a string or null")
        out.append(row)
    seen: set[str] = set()
    for row in out:
        if row["shash"] in seen:
            raise ValueError(f"{path}: duplicate row for shash "
                             f"{row['shash']}; row identity must be unique")
        seen.add(row["shash"])
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
    # A proto the baseline walked and this ledger does not. Rows survive it
    # (1944 occurrences live in 1478 rows), so the per-row loop above sees
    # nothing; only `old_occurrences -> new_occurrences` in the summary moved,
    # and a summary line is not a verdict. Occurrences whose ROW also vanished
    # are already reported as `row-removed`, so they are skipped here: one
    # cause, one finding, and the cluster counts stay row counts.
    for key in sorted(set(old_occ) - set(new_occ)):
        oshash, oo = old_occ[key]
        if oshash not in new_by:
            continue
        rep.occurrences_removed += 1
        rep.regressions.append(Regression(
            kind="occurrence-removed", shash=oshash,
            cluster=cluster_of(new_by[oshash].get("refusal_reason")),
            detail=f"{key[0]}:{key[1]} was walked in the baseline "
                   f"(shipped {oo.get('shipped', '?')}) and is not walked now, "
                   f"though its row survives"))
    for key in sorted(set(old_occ) & set(new_occ)):
        _, oo = old_occ[key]
        nshash, no = new_occ[key]
        # A baseline predating M5 task 6 has no `shipped` at all, and this
        # comparison handles that WITHOUT a guard: `.get` returns None and
        # `None == "structured"` is False, so both branches simply do not fire.
        # There used to be an explicit `if os_ is None or ns is None: continue`
        # here. Round 3 deleted it as provably dead, measured both ways: the
        # suite is 37 passed WITH it and 37 passed WITHOUT it, and the CLI's
        # clean-diff exit is 0 either way. A conditional whose presence changes
        # nothing observable is decoration, and this file's whole argument is
        # that its checks are load-bearing. The case it was meant to describe
        # is covered by behaviour instead, in
        # `tests/test_ratchet_diff.py::test_a_baseline_without_shipped_needs_no_guard`.
        os_, ns = oo.get("shipped"), no.get("shipped")
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
    out.append(f"  protos:   {rep.occurrences_removed} occurrence(s) no longer "
               f"walked (surviving rows)")
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
    """The CLI, and the `git bisect run` predicate.

    Every path that is not a verdict about the tree returns 125 or 128 -- see
    the module docstring for the measured contract. The split is by whose fault
    it is: the BASELINE and the argument list are the same at every bisected
    commit, so a fault there should abort the whole run (128) rather than mark
    a hundred commits skipped; the NEW ledger is produced by the tree under
    test, so a fault there means only that THIS commit cannot be judged (125).

    **The split holds for faults `load_rows` recognises, and only those.** An
    UNANTICIPATED fault in a NEW ledger reaches the `diff_ledgers` handler
    below and exits 128 -- abort -- where the rule above would say 125. That is
    deliberate and it is the safe direction: once the diff has crashed, this
    script cannot tell a bad ledger from a bug in itself, and stopping the run
    with a message beats skipping N commits and reporting nothing. Round 2's
    N3 was one such case that had a knowable shape (a non-string
    `refusal_reason`), so it moved into `load_rows` and now returns 125; the
    residual class stays at 128 by design rather than by omission.
    """
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) != 2:
        print(f"usage: ratchet_diff.py OLD.jsonl NEW.jsonl\n"
              f"  Compares two corpus/ledger.jsonl snapshots. Exit "
              f"{EXIT_OK}=no regression, {EXIT_REGRESSION}=regression,\n"
              f"  {EXIT_UNTESTABLE}=NEW unreadable (git bisect skips), "
              f"{EXIT_BROKEN}=usage or bad baseline (git bisect aborts).\n"
              f"  Not 2: `git bisect run` reads every code in 1..127 except "
              f"125 as 'bad commit'.", file=sys.stderr)
        return EXIT_BROKEN
    try:
        old = load_rows(args[0])
    except (OSError, ValueError) as e:
        print(f"ratchet_diff: baseline {args[0]} is unusable: {e}\n"
              f"  This is the instrument, not the tree: exiting "
              f"{EXIT_BROKEN} so `git bisect run` aborts rather than blaming "
              f"a commit.", file=sys.stderr)
        return EXIT_BROKEN
    try:
        new = load_rows(args[1])
    except (OSError, ValueError) as e:
        print(f"ratchet_diff: ledger under test {args[1]} is unusable: {e}\n"
              f"  No verdict is possible for this tree: exiting "
              f"{EXIT_UNTESTABLE} so `git bisect run` skips it.",
              file=sys.stderr)
        return EXIT_UNTESTABLE
    try:
        rep = diff_ledgers(old, new)
    except Exception as e:                     # noqa: BLE001 -- see docstring
        # A crash HERE is a bug in this script, not evidence about the tree.
        # Letting it propagate would print a traceback and exit 1, which git
        # reads as "bad commit" -- the exact confusion this file exists to
        # avoid. Abort the run instead, loudly.
        print(f"ratchet_diff: internal error while diffing "
              f"({type(e).__name__}: {e}); this is a bug in ratchet_diff.py, "
              f"not a verdict. Exiting {EXIT_BROKEN} to abort the bisect.",
              file=sys.stderr)
        return EXIT_BROKEN
    print(format_report(rep, args[0], args[1]))
    return EXIT_OK if rep.ok else EXIT_REGRESSION


if __name__ == "__main__":
    sys.exit(main())

"""Non-vacuity suite for `scripts/ratchet_diff.py` (M5 task 8).

**The point of this file is that the ratchet can fail.** For four milestones
"levels only ever go up" has been discipline plus a human reading the ledger
diff; `test_ledger_ratchet.py` pins the ledger as a fixed point of its own
generator and `test_m3_exit.py` / `test_m4_exit.py` pin within-row coupling and
rate floors, but nothing compared the committed artifact against a historical
baseline. A ratchet that cannot fail is worse than no ratchet, because it
licenses exactly the claim it does not enforce -- so every failure mode below
gets its own committed test that feeds `ratchet_diff` a hand-mutated copy of
the REAL committed ledger and asserts a non-zero exit that NAMES the offending
row. Neutering any one check turns at least one NAMED case red, and only cases
that belong to that check -- the red sets are disjoint, so a mutation that
trips two checks at once is visible rather than absorbed.

**That sentence used to say "exactly one", and it was false.** Round 2 found
two guards in `load_rows` that no test touched at all: deleting the
`isinstance(row, dict)` check left the entire suite green while a ledger line
of `5` raised `AttributeError` straight out of `load_rows`, past `main`'s
`(OSError, ValueError)` handler, to a traceback and exit 1 -- the very failure
round 1 was fixing. It is also not "exactly one" numerically: several checks
own two or three named cases (see the parametrised
`test_every_undiffable_row_shape_is_skipped_not_blamed`). Both corrections are
kept in the text rather than smoothed away, because "one check, one red test"
is the claim that stopped being checked.

The mutations are deliberately minimal (one field of one row) so that a test
going green for the wrong reason -- e.g. because the mutation also tripped a
different check -- is visible in the asserted `kind`.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.ratchet_diff import (
    EXIT_BROKEN, EXIT_OK, EXIT_REGRESSION, EXIT_UNTESTABLE,
    Regression, cluster_of, diff_ledgers, load_rows, main,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER = REPO_ROOT / "corpus" / "ledger.jsonl"


@pytest.fixture(scope="module")
def committed() -> list[dict]:
    """The real `corpus/ledger.jsonl`, parsed once for this module."""
    return load_rows(LEDGER)


def _write(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                    encoding="utf-8")
    return path


def _pick(rows: list[dict], level: str) -> dict:
    for r in rows:
        if r["level"] == level:
            return r
    raise AssertionError(f"no {level} row in the committed ledger")


def _run(tmp_path: Path, old: list[dict], new: list[dict], capsys) -> tuple[int, str]:
    o = _write(tmp_path / "old.jsonl", old)
    n = _write(tmp_path / "new.jsonl", new)
    rc = main([str(o), str(n)])
    return rc, capsys.readouterr().out


def _kinds(old: list[dict], new: list[dict]) -> list[str]:
    return [r.kind for r in diff_ledgers(old, new).regressions]


# --------------------------------------------------------------------------
# The clean directions: identical, and genuinely better.
# --------------------------------------------------------------------------

def test_the_committed_ledger_against_itself_passes(committed, tmp_path, capsys):
    rc, out = _run(tmp_path, committed, committed, capsys)
    assert rc == 0
    assert "no regression" in out
    assert f"{len(committed)} rows" in out


def test_an_upgraded_copy_passes_with_a_summary(committed, tmp_path, capsys):
    new = copy.deepcopy(committed)
    row = _pick(new, "L1")
    row["level"] = "L3"
    row["l3_level"] = 1
    row["refusal_reason"] = None
    row["fallback"] = False
    row["confessions"] = []
    for o in row["occurrences"]:
        o["shipped"] = "structured"

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 0
    assert "1 upgraded" in out
    assert "no regression" in out


def test_a_new_row_is_not_a_regression(committed, tmp_path, capsys):
    new = copy.deepcopy(committed)
    added = copy.deepcopy(_pick(new, "L3"))
    added["shash"] = "ff" * 32
    added["occurrences"] = [{"file": "brand_new.lua", "proto_path": "main",
                             "shipped": "structured", "hybrid": False}]
    new.append(added)

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 0
    assert "1 added" in out


# --------------------------------------------------------------------------
# One test per failure mode. Each asserts the kind AND that the row is named.
# --------------------------------------------------------------------------

def test_a_level_downgrade_fails_naming_the_row(committed, tmp_path, capsys):
    new = copy.deepcopy(committed)
    row = _pick(new, "L3")
    row["level"] = "L1"
    row["l3_level"] = None
    row["fallback"] = True
    row["refusal_reason"] = "structure: pc 7: unstructurable back edge"

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert row["shash"] in out
    assert "level-downgrade" in out
    assert "L3 -> L1" in out
    assert _kinds(committed, new) == ["level-downgrade"]


def test_a_rung_downgrade_fails_naming_the_row(committed, tmp_path, capsys):
    """A HIGHER `l3_level` is a WEAKER proof: rung k means `NORMALIZATIONS[:k]`
    were applied before comparing (`verify/normalize.py`), so rung 0 is strict
    equality and each rung above it discards more. Every `L3` row today is at
    rung 1, so the downgrade has to be built by pretending the baseline reached
    rung 0 -- which is exactly the shape a future `L3.2` rung would make real."""
    old = copy.deepcopy(committed)
    new = copy.deepcopy(committed)
    o_row, n_row = _pick(old, "L3"), _pick(new, "L3")
    assert o_row["shash"] == n_row["shash"]
    o_row["l3_level"] = 0
    n_row["l3_level"] = 1

    rc, out = _run(tmp_path, old, new, capsys)
    assert rc == 1
    assert n_row["shash"] in out
    assert "rung-downgrade" in out
    assert "rung 0 -> 1" in out
    assert _kinds(old, new) == ["rung-downgrade"]


def test_an_l3_row_losing_its_rung_is_a_rung_downgrade(committed, tmp_path, capsys):
    """`level == "L3"` with `l3_level is None` is a certification claim with no
    recorded evidence -- the bookkeeping shape M4's within-row coupling
    forbids, seen across versions."""
    new = copy.deepcopy(committed)
    row = _pick(new, "L3")
    row["l3_level"] = None

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert row["shash"] in out
    assert _kinds(committed, new) == ["rung-downgrade"]


def test_a_removed_row_fails_naming_the_row(committed, tmp_path, capsys):
    new = copy.deepcopy(committed)
    gone = new.pop(3)

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert gone["shash"] in out
    assert "row-removed" in out
    assert _kinds(committed, new) == ["row-removed"]


def test_a_proto_dropping_out_of_the_walk_fails(committed, tmp_path, capsys):
    """The 1944 occurrences live in 1478 rows, so a proto vanishing from
    `walk_proto_paths` leaves every ROW intact and only shortens one
    `occurrences` list. Measured before this check existed: popping one
    occurrence off a two-occurrence row gave 0 regressions and exit 0, with
    `1944 -> 1943` printed two lines above. Gate 1 of `scripts/ratchet_job.sh`
    covers it (`test_ledger_ratchet.py` pins 1944), but the `git bisect run`
    predicate runs the diff ALONE."""
    new = copy.deepcopy(committed)
    row = next(r for r in new if len(r["occurrences"]) > 1)
    lost = row["occurrences"].pop()

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert row["shash"] in out
    assert "occurrence-removed" in out
    assert lost["file"] in out and lost["proto_path"] in out
    assert _kinds(committed, new) == ["occurrence-removed"]
    assert diff_ledgers(committed, new).occurrences_removed == 1


def test_a_removed_row_is_reported_once_not_per_occurrence(committed, tmp_path,
                                                           capsys):
    """One cause, one finding. A vanished row takes its occurrences with it;
    reporting both would multiply a single regression by its occurrence count
    and stop the cluster counts from being row counts."""
    new = copy.deepcopy(committed)
    gone = next(r for r in new if len(r["occurrences"]) > 1)
    new.remove(gone)

    rc, _ = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert _kinds(committed, new) == ["row-removed"]
    assert diff_ledgers(committed, new).occurrences_removed == 0


def test_an_l3_row_acquiring_a_refusal_reason_fails(committed, tmp_path, capsys):
    new = copy.deepcopy(committed)
    row = _pick(new, "L3")
    row["refusal_reason"] = "mismatch: code"

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert row["shash"] in out
    assert "reason-regression" in out
    assert _kinds(committed, new) == ["reason-regression"]


def test_an_occurrence_shipping_structured_then_fallback_fails(committed, tmp_path,
                                                               capsys):
    """M5 task 6's per-occurrence `shipped`. This is independent of `level`: a
    proto that is not `L3` on its own can still ship structured inside a
    hybrid chunk, so a row can keep its level and still stop shipping."""
    new = copy.deepcopy(committed)
    row = next(r for r in new
               if any(o["shipped"] == "structured" for o in r["occurrences"]))
    occ = next(o for o in row["occurrences"] if o["shipped"] == "structured")
    occ["shipped"] = "fallback"

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert row["shash"] in out
    assert "shipping-regression" in out
    assert occ["file"] in out
    assert _kinds(committed, new) == ["shipping-regression"]


def test_a_new_row_at_l0_fails(committed, tmp_path, capsys):
    """`L0` is banned outright (`test_ledger_ratchet.py`), so it cannot be
    reached by downgrading an existing row without also tripping
    `level-downgrade`. A row that arrives at `L0` is the one shape the
    per-row diff would otherwise wave through."""
    new = copy.deepcopy(committed)
    added = copy.deepcopy(_pick(new, "L3"))
    added["shash"] = "ee" * 32
    added["level"] = "L0"
    added["l3_level"] = None
    added["compile_ok"] = False
    added["refusal_reason"] = "compile: shipped chunk did not compile"
    added["occurrences"] = [{"file": "broken.lua", "proto_path": "main",
                             "shipped": "fallback", "hybrid": False}]
    new.append(added)

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert added["shash"] in out
    assert "new-l0" in out
    assert _kinds(committed, new) == ["new-l0"]


# --------------------------------------------------------------------------
# Clustering: the reason M4 added `refusal_reason` at all.
# --------------------------------------------------------------------------

def test_regressions_are_grouped_by_refusal_reason_cluster(committed, tmp_path,
                                                           capsys):
    new = copy.deepcopy(committed)
    l3 = [r for r in new if r["level"] == "L3"][:2]
    assert len(l3) == 2
    reasons = ["structure: pc 7: unstructurable back edge",
               "mismatch: code"]
    for row, reason in zip(l3, reasons):
        row["level"] = "L1"
        row["l3_level"] = None
        row["fallback"] = True
        row["refusal_reason"] = reason

    rc, out = _run(tmp_path, committed, new, capsys)
    assert rc == 1
    assert "cluster `structure`" in out
    assert "cluster `mismatch`" in out
    rep = diff_ledgers(committed, new)
    assert sorted(r.cluster for r in rep.regressions) == ["mismatch", "structure"]


def test_cluster_of_reads_the_kind_not_the_message():
    assert cluster_of("structure: pc 12: if targets out of range") == "structure"
    assert cluster_of("mismatch: code") == "mismatch"
    assert cluster_of(None) == "(no reason recorded)"
    assert cluster_of("") == "(no reason recorded)"


# --------------------------------------------------------------------------
# Schema tolerance: an older baseline must still be diffable.
# --------------------------------------------------------------------------

def test_a_baseline_predating_a_field_is_diffed_on_what_it_has(committed, tmp_path,
                                                               capsys):
    """A baseline written before M4's `refusal_reason` / M5 task 6's `shipped`
    must not read as a mass regression. The checks that need a missing field
    are skipped for the rows that lack it and the omission is reported."""
    old = copy.deepcopy(committed)
    for r in old:
        r.pop("refusal_reason", None)
        for o in r["occurrences"]:
            o.pop("shipped", None)
            o.pop("hybrid", None)

    rc, out = _run(tmp_path, old, committed, capsys)
    assert rc == 0
    assert "schema" in out
    assert "refusal_reason" in out
    assert "shipped" in out


def test_a_missing_field_does_not_hide_a_real_downgrade(committed, tmp_path, capsys):
    """Schema tolerance must not become a blanket amnesty: a level downgrade
    still fails even when the baseline predates the reason field."""
    old = copy.deepcopy(committed)
    for r in old:
        r.pop("refusal_reason", None)
    new = copy.deepcopy(committed)
    row = _pick(new, "L3")
    row["level"] = "L1"
    row["l3_level"] = None

    rc, out = _run(tmp_path, old, new, capsys)
    assert rc == 1
    assert row["shash"] in out
    assert "level-downgrade" in out


# --------------------------------------------------------------------------
# CLI contract (this is a `git bisect run` predicate).
# --------------------------------------------------------------------------

def test_the_exit_codes_are_literally_the_ones_git_treats_as_non_verdicts():
    """Every other test in this section is written in terms of the SYMBOLS, so
    without this one they all stay green if the values are wrong — verified by
    mutation: setting both non-verdict constants back to 2 left all 24 tests
    passing. The contract is about the integers, so the integers are pinned
    here.

    `git-bisect(1)`, git 2.39.5, read on this host 2026-08-12: *"exit with code
    0 if the current source code is good/old, and exit with a code between 1
    and 127 (inclusive), except 125, if the current source code is bad/new. Any
    other exit code will abort the bisect process. The special exit code 125
    should be used when the current source code cannot be tested."*

    So the only non-verdicts are 125 and >=128. **2 is a verdict**: measured on
    a scratch repo, a predicate that unconditionally `exit 2`s made
    `git bisect run` announce a first bad commit."""
    assert EXIT_OK == 0
    assert EXIT_REGRESSION == 1
    assert EXIT_UNTESTABLE == 125
    assert EXIT_BROKEN >= 128
    # The trap this round closed: anything in 1..127 except 125 reads as "bad".
    for code in (EXIT_UNTESTABLE, EXIT_BROKEN):
        assert not (1 <= code <= 127 and code != 125), (
            f"{code} is in git's bad-commit range")


def test_an_unreadable_new_ledger_is_untestable_not_bad(tmp_path, capsys):
    """`git bisect run` reads EVERY code in 1..127 except 125 as "bad commit"
    -- 2 included. Measured 2026-08-12 with git 2.39.5 on a scratch repo: a
    predicate that unconditionally `exit 2`s makes bisect announce a first bad
    commit, blaming the first commit after the known-good one. So an
    unreadable ledger under test must be 125 (skip), never 1 and never 2."""
    good = _write(tmp_path / "a.jsonl", [])
    assert main([str(good), str(tmp_path / "nope.jsonl")]) == EXIT_UNTESTABLE
    err = capsys.readouterr().err
    assert "nope.jsonl" in err and "skips it" in err


def test_an_unreadable_baseline_aborts_the_whole_bisect(tmp_path, capsys):
    """The baseline is the same file at every bisected commit, so a fault in
    it is not "this commit cannot be tested" but "this run is misconfigured".
    >=128 makes git stop: measured, `git bisect run` prints "error: bisect run
    failed: exit code 128 ... is < 0 or >= 128" and halts."""
    good = _write(tmp_path / "b.jsonl", [])
    assert main([str(tmp_path / "nope.jsonl"), str(good)]) == EXIT_BROKEN
    assert "baseline" in capsys.readouterr().err


def test_a_usage_error_aborts_rather_than_condemning_a_commit(tmp_path, capsys):
    """Wrong argument count cannot depend on the commit, so it must not
    produce a per-commit verdict of any kind."""
    assert main([]) == EXIT_BROKEN
    assert main(["only-one.jsonl"]) == EXIT_BROKEN
    assert "usage" in capsys.readouterr().err


def test_a_malformed_new_row_is_skipped_not_blamed(committed, tmp_path, capsys):
    """Regression test for the fault this round fixed: a ledger line without
    `shash` used to raise `KeyError: 'shash'` out of `diff_ledgers`, past
    `main`'s handler (which wrapped only the parse), and CPython turned the
    traceback into exit 1 -- read by `git bisect run` as "bad commit". An
    instrument fault reported as a tree verdict is the one outcome a bisect
    predicate must never produce."""
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"level": "L3"}\n', encoding="utf-8")
    old = _write(tmp_path / "old.jsonl", committed)
    assert main([str(old), str(bad)]) == EXIT_UNTESTABLE
    err = capsys.readouterr().err
    assert "shash" in err and "No verdict" in err


@pytest.mark.parametrize("label,line,neutered_behaviour", [
    # The guard this parametrisation exists for. Round 2 found it UNPINNED:
    # deleting `isinstance(row, dict)` left the whole 664-test suite green,
    # while a scalar line raised `AttributeError: 'int' object has no attribute
    # 'get'` out of `load_rows` -- past `main`'s `(OSError, ValueError)`
    # handler, traceback, exit 1. That is round 1's finding 2 reintroduced by
    # round 1's fix for finding 2, which is why each guard now gets a name.
    ("scalar row", "5", "AttributeError escapes load_rows -> exit 1"),
    ("string row", '"not a row"', "AttributeError escapes load_rows -> exit 1"),
    ("occurrences not a list",
     '{"shash": "aa", "level": "L3", "occurrences": {"file": "a.lua"}}',
     "diff handler catches it -> 128 (abort), not 125"),
    ("occurrence not an object",
     '{"shash": "aa", "level": "L3", "occurrences": ["a.lua"]}',
     "diff handler catches it -> 128 (abort), not 125"),
    ("unhashable occurrence key",
     '{"shash": "aa", "level": "L3", "occurrences": [{"file": ["a"], '
     '"proto_path": "main"}]}',
     "TypeError: unhashable list -> 128 (abort), not 125"),
    # N2: a str rung slipped past BOTH the `is None` and the `isinstance(int)`
    # branch, so baseline rung 0 vs new rung "one" scored 0 regressions.
    ("rung of the wrong type",
     '{"shash": "aa", "level": "L3", "l3_level": "one", "occurrences": []}',
     "rung comparison silently skipped -> exit 0, a MISSED downgrade"),
    ("rung is a bool",
     '{"shash": "aa", "level": "L3", "l3_level": true, "occurrences": []}',
     "bool is an int subclass; compares as rung 1"),
    # N3: `cluster_of` does `.split(":", 1)`.
    ("reason of the wrong type",
     '{"shash": "aa", "level": "L1", "refusal_reason": 12345, '
     '"occurrences": []}',
     "AttributeError in cluster_of -> 128 (abort) where the contract says 125"),
])
def test_every_undiffable_row_shape_is_skipped_not_blamed(
        committed, tmp_path, capsys, label, line, neutered_behaviour):
    """One case per type guard in `load_rows`, each named, because round 2
    found two guards that no test touched.

    The rule: a ledger this script cannot diff is **125** (git skips the
    commit), never 1 and never a traceback. `neutered_behaviour` records what
    each guard's removal was measured to do -- three distinct failure modes,
    so this is not one check wearing eight hats."""
    bad = tmp_path / "bad.jsonl"
    bad.write_text(line + "\n", encoding="utf-8")
    old = _write(tmp_path / "old.jsonl", committed)
    assert main([str(old), str(bad)]) == EXIT_UNTESTABLE, label
    assert "No verdict" in capsys.readouterr().err, label


def test_a_malformed_rung_cannot_hide_a_rung_downgrade(committed, tmp_path,
                                                       capsys):
    """N2 stated as the regression it actually is, rather than as a type
    error. Measured before the guard: baseline rung 0 against new rung "one"
    gave **0 regressions, exit 0** -- a genuine `L3.0` -> non-numeric rung
    change waved through. It must not be exit 0 or 1; it is 125."""
    old = copy.deepcopy(committed)
    new = copy.deepcopy(committed)
    o_row, n_row = _pick(old, "L3"), _pick(new, "L3")
    o_row["l3_level"] = 0
    n_row["l3_level"] = "one"
    o = _write(tmp_path / "old.jsonl", old)
    n = _write(tmp_path / "new.jsonl", new)

    assert main([str(o), str(n)]) == EXIT_UNTESTABLE
    assert "l3_level" in capsys.readouterr().err


def test_duplicate_rows_are_rejected_rather_than_last_wins(committed, tmp_path,
                                                           capsys):
    """`shash` is row identity, and the diff builds `{r["shash"]: r}` on both
    sides -- last wins. Measured on the committed ledger: a downgraded
    duplicate appended AFTER the good row is caught (1 regression), but the
    same duplicate inserted BEFORE it yields 0. Uniqueness is pinned by
    `tests/test_ledger_ratchet.py`, but the bisect predicate runs the diff
    alone, against files it did not produce."""
    dup = copy.deepcopy(_pick(committed, "L3"))
    dup["level"] = "L1"
    dup["l3_level"] = None
    idx = next(i for i, r in enumerate(committed) if r["shash"] == dup["shash"])
    rows = copy.deepcopy(committed)
    rows.insert(idx, dup)                        # the order that used to pass
    path = _write(tmp_path / "dup.jsonl", rows)
    good = _write(tmp_path / "good.jsonl", committed)

    assert main([str(good), str(path)]) == EXIT_UNTESTABLE
    assert main([str(path), str(good)]) == EXIT_BROKEN
    assert "duplicate row" in capsys.readouterr().err


def test_an_internal_crash_aborts_instead_of_condemning_the_commit(
        committed, tmp_path, capsys, monkeypatch):
    """`load_rows` now rejects the malformed inputs we know about, so the
    handler around `diff_ledgers` is defence in depth — and defence in depth
    that is never exercised is decoration. Forced here: any residual bug in
    the diff must abort the run (128), never exit 1 and be recorded as a bad
    commit."""
    import scripts.ratchet_diff as rd

    def boom(_old, _new):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(rd, "diff_ledgers", boom)
    path = _write(tmp_path / "x.jsonl", committed)
    assert rd.main([str(path), str(path)]) == EXIT_BROKEN
    err = capsys.readouterr().err
    assert "internal error" in err and "not a verdict" in err


def test_a_clean_diff_of_the_committed_ledger_exits_zero(tmp_path, capsys):
    """The `git bisect run` "good" verdict, through the CLI rather than
    `diff_ledgers`, so the exit constants themselves are covered."""
    assert main([str(LEDGER), str(LEDGER)]) == EXIT_OK
    assert "no regression" in capsys.readouterr().out


def test_regression_rows_are_hashable_and_ordered():
    """`Regression` is a frozen dataclass so the report can sort and group
    deterministically -- a bisect predicate whose output reorders between runs
    is unreadable in a bisect log."""
    a = Regression(kind="level-downgrade", shash="a" * 64, cluster="structure",
                   detail="L3 -> L1")
    b = Regression(kind="level-downgrade", shash="a" * 64, cluster="structure",
                   detail="L3 -> L1")
    assert a == b and len({a, b}) == 1

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
row. Narrowing any one check makes exactly one of these go red.

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

def test_a_missing_file_exits_2_not_1(tmp_path, capsys):
    """`git bisect run` reads 1 as "bad commit" and would blame an innocent
    commit for an unreadable file. 2 is distinguishable, and 125 (skip) is
    what the documented bisect wrapper turns a failed regeneration into."""
    good = _write(tmp_path / "a.jsonl", [])
    assert main([str(good), str(tmp_path / "nope.jsonl")]) == 2
    assert "nope.jsonl" in capsys.readouterr().err


def test_regression_rows_are_hashable_and_ordered():
    """`Regression` is a frozen dataclass so the report can sort and group
    deterministically -- a bisect predicate whose output reorders between runs
    is unreadable in a bisect log."""
    a = Regression(kind="level-downgrade", shash="a" * 64, cluster="structure",
                   detail="L3 -> L1")
    b = Regression(kind="level-downgrade", shash="a" * 64, cluster="structure",
                   detail="L3 -> L1")
    assert a == b and len({a, b}) == 1

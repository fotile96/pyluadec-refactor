"""M4 exit gate, read off the committed ledger.

**This gate borrows all of its force from `tests/test_ledger_ratchet.py`, and
is decoration without it.** Everything here reads
`corpus/ledger.jsonl` and nothing here re-derives it, so on its own it proves
only that a committed JSON file says the right things -- it runs in
hundredths of a second and cannot notice a decompiler that stopped working.
What makes the composite real is the M2-era ratchet test, which re-runs the
whole corpus pipeline and requires the committed ledger to come back
byte-identical: a semantic bug in the structured path moves the live rate,
the regenerated ledger stops matching, and the ratchet fails. Demonstrated at
the M4 whole-branch review by injecting such a bug -- the live unique-`L3`
rate fell to 78.1% (100 chunks demoted to fallback) and *this* file stayed
green. Weakening, skipping or `xfail`ing the ratchet test therefore silently
reduces this milestone's headline gate to a JSON schema check; treat the two
as one gate.

Same contract as `tests/test_m3_exit.py` (which this file does not touch and
does not replace -- M3's `> 0.50` floors stay asserted, so a regression past
them fails twice): the thresholds are milestone COMMITMENTS, not measurements.
They must not be edited to match whatever the implementation currently
achieves. If the corpus rate falls below one, the fix is in the reconstructor.

**Why the floors are 0.85 when the achieved rates are 96.8% / 97.5%** (measured
2026-08-12 at M5 task 8; they were 94.0% / 95.4% at the M4 wrap, and this
paragraph did not move as M5 tasks 4-6 raised them). A floor
set at the measurement is not a floor, it is a tripwire: every legitimate
variation -- a corpus refresh, an oracle rebuild, a refactor that trades three
protos in one cluster for four in another -- becomes a red suite with nothing
actually broken, and the standard repair is to edit the threshold, which is
how a gate stops meaning anything. 0.85 is what M4 promised; the ~12 points
above it are headroom (~9 at the M4 wrap), and the achieved figure is reported
in the assertion message so a drop is still visible in the failure text of
whatever else breaks.
Cross-revision monotonicity (no `L3` -> `L1` on any individual row) is NOT
asserted here, and not anywhere in the suite: it needs a committed baseline to
diff against, and a baseline is a git ref rather than a fixture. Since M5 task
8 it IS asserted, by `scripts/ratchet_diff.py` as gate 2 of
`scripts/ratchet_job.sh` -- run at a milestone wrap and before any merge that
touches the ledger, not per commit. That is what makes the 0.85 floor above
safe to leave slack: the floor catches a catastrophe without churning, the
baseline diff catches the single row this file would wave through. See
`docs/runbooks/structured-pipeline.md`, "Ratchet the ledger against a
baseline".

**Measured at the M4 wrap (task 12, 2026-08-12), when nothing asserted it.**
Diffing `corpus/ledger.jsonl` at `bbe74f6` (the M4 branch point) against the
M4 tip: the two files carry the *same* 1478 `shash` keys, **277 rows upgraded
`L1` -> `L3`, 1201 unchanged, 0 downgraded**, 0 `L0`, `compile_ok` true on all
1478, 1944 occurrences on both sides. So M4's ledger change is monotone in
fact. It was monotone by review; it no longer has to be. The same diff is now
one command, and re-run at M5 task 8 it reports `bbe74f6` -> HEAD as **318
upgraded, 0 downgraded** (L3 1112 -> 1430):

    git show bbe74f6:corpus/ledger.jsonl > /tmp/base.jsonl
    uv run python scripts/ratchet_diff.py /tmp/base.jsonl corpus/ledger.jsonl
"""
import json
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "corpus" / "ledger.jsonl"

# The kinds `structure.structured.ProtoCert.reason` can produce, as the
# committed vocabulary of the ledger's `refusal_reason` field. Asserting the
# kind (not the whole message, which carries pcs and register numbers and is
# expected to churn) is what lets the ratchet (`scripts/ratchet_diff.py`, M5
# task 8) cluster a regression by cause instead of by string equality. Adding
# a kind is a deliberate act: extend this tuple in the same commit that
# introduces it.
REASON_KINDS = ("structure: ", "reconstruct: ", "compile: ", "mismatch: ")


def _entries():
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def reason_violations(entries) -> list[str]:
    """Rows whose `refusal_reason` does not agree with their `level`.

    A pure function over already-parsed rows so that the coupling it encodes
    can be tested against rows that VIOLATE it -- see
    `test_reason_coupling_actually_rejects_bad_rows`. An assertion written
    inline over the committed ledger only ever runs against data that
    satisfies it, and would go on passing if it were quietly weakened.
    """
    bad = []
    for e in entries:
        r = e.get("refusal_reason")
        who = f"{e['shash'][:12]} ({e['level']})"
        if e["level"] == "L3":
            if r is not None:
                bad.append(f"{who}: certified, but claims a refusal reason {r!r}")
        elif not isinstance(r, str) or not r.strip():
            bad.append(f"{who}: not certified, but does not say why (reason={r!r})")
        elif not r.startswith(REASON_KINDS):
            bad.append(f"{who}: reason {r!r} is outside the committed vocabulary")
    return bad


def test_m4_exit_unique_l3_rate():
    entries = _entries()
    assert entries
    l3 = sum(1 for e in entries if e["level"] == "L3")
    frac = l3 / len(entries)
    assert frac > 0.85, f"unique L3 {l3}/{len(entries)} = {frac:.1%}, floor 85.0%"


def test_m4_exit_occurrence_l3_rate():
    """The un-deduplicated basis. `corpus/ledger.jsonl` keys by
    `structural_hash`, so its rows are unique proto SHAPES; a change that
    certified only the shapes that happen to be rare would move the unique
    rate without moving this one. `== 1944` pins the denominator itself: a
    filtered or deduplicated denominator has already hidden two real defects
    in this project."""
    entries = _entries()
    total = sum(len(e["occurrences"]) for e in entries)
    assert total == 1944
    l3 = sum(len(e["occurrences"]) for e in entries if e["level"] == "L3")
    frac = l3 / total
    assert frac > 0.85, f"occurrence L3 {l3}/{total} = {frac:.1%}, floor 85.0%"


def test_every_non_l3_row_says_why():
    """The M4 task 6 field. Before it, a `build_sir` refusal and a
    print-then-certify-rejection were indistinguishable in the ledger -- both
    carried the same generic whole-range `fallback-state-machine` confession.
    That was harmless while nothing structured cleanly and then failed the
    comparison; M4's loop work made that the second-largest residual cluster
    (35 of 89 rows as of this commit), so the ledger has to record which one
    happened. The converse is asserted too: an `L3` row claiming a refusal
    reason is the same bookkeeping inconsistency in the other direction, and
    is exactly what a level that rose without its evidence being cleared would
    look like.
    """
    assert reason_violations(_entries()) == []


def test_reason_coupling_actually_rejects_bad_rows():
    """Prove `reason_violations` can fail -- all three ways.

    The corpus assertion above passes on today's ledger, and would go on
    passing if the check were weakened to `True`. Four M4 reviews in a row
    found guards that were deletable with a green tree; this is the committed
    proof that this one is not."""
    good_l3 = {"shash": "aa" * 32, "level": "L3", "refusal_reason": None}
    good_l1 = {"shash": "bb" * 32, "level": "L1",
               "refusal_reason": "structure: pc 4: if targets out of range"}
    assert reason_violations([good_l3, good_l1]) == []

    # 1. not certified and silent about it -- the shape that existed before
    #    this field, and the one `scripts/ratchet_diff.py` cannot cluster
    #    without.
    silent = dict(good_l1, refusal_reason=None)
    assert len(reason_violations([silent])) == 1
    assert len(reason_violations([dict(good_l1, refusal_reason="  ")])) == 1

    # 2. certified but still carrying evidence of a refusal.
    assert len(reason_violations([dict(good_l3, refusal_reason="mismatch: code")])) == 1

    # 3. a reason outside the committed vocabulary: unclustered, so M5 could
    #    not tell which regression it was even though the row is not silent.
    assert len(reason_violations([dict(good_l1, refusal_reason="something odd")])) == 1


def test_reasons_cluster_into_the_known_causes():
    """The residual is not a mystery: every non-`L3` row's reason falls into
    one of the four kinds, and the census in
    `docs/runbooks/structured-pipeline.md` is derived from exactly this field
    rather than from a scratch script. Asserted as a non-empty partition
    rather than as fixed counts -- counts are measurements and move."""
    entries = _entries()
    non_l3 = [e for e in entries if e["level"] != "L3"]
    assert non_l3, "nothing left to census (delete this test if that is real)"
    # `isinstance` guard, not an assertion: a missing reason is
    # `test_every_non_l3_row_says_why`'s finding to report, and this test
    # crashing with an AttributeError first would only obscure it.
    kinds = {r.split(":")[0] for e in non_l3
             if isinstance(r := e["refusal_reason"], str)}
    assert kinds <= {k.rstrip(": ") for k in REASON_KINDS}
    # Both residual families are present today. If one ever empties, that is a
    # real (good) change and this line is the place to record it.
    # M8 task 2 (2026-08-16): the `structure:` family emptied -- the last two
    # rows (`snr_common:main_71` + its root) now pass `build_sir` and refuse
    # at certification instead (`mismatch: code`, the constructor-layout
    # class; the recognizer gap itself is closed with synthetic L3 fixtures).
    # The milestone goal "structure: == 0" is real, so this pin now expects
    # only `mismatch` and `reconstruct` until their campaign tasks land.
    assert {"mismatch", "reconstruct"} <= kinds
    assert "structure" not in kinds

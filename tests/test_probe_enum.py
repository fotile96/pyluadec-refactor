"""M6 task 7: the enumerated differential instrument.

`scripts/probe_enum.py` drives ONE proto over the WHOLE product of its branch
channels' value domains, both sides under the same assignment, and compares
byte-for-byte. What it is for, and what it deliberately is not for, is in that
module's docstring; the stub environment and the spec grammar are in
`scripts/probe_enum.lua`.

The corpus arm of this file is a bounded demonstration over the SMALLEST of
the 13 compound-`if` leaf refusals. The full 13-proto run is a job
(`uv run python scripts/probe_enum.py`), not a suite gate, because its
enumerated product is 1256 assignments and every one of them is two Lua
subprocesses; its measured cost is in the task report.

Every synthetic fixture here is labelled as synthetic. The corpus is a weak
oracle -- it has zero `repeat` loops and misses six opcodes -- so an
instrument proved only on it is proved on a sample, and the fault injections
below are exactly the shapes the corpus cannot produce.
"""
from __future__ import annotations

import pytest

from scripts import probe_enum
from scripts.probe_enum import (
    BUDGET, ProbeError, channels_of, discover_entries, drive, encode_path,
    encode_value, enumerate_assignments, exhaust, first_difference, space_size,
)


# --------------------------------------------------------------------------
# Fixtures (SYNTHETIC: hand-written Lua, compiled by the vendored luac)
# --------------------------------------------------------------------------

def _compiled(tmp_path, source: bytes, name: str = "t.luac"):
    from pyluadec import oracle
    p = tmp_path / name
    p.write_bytes(oracle.compile_source(source))
    return p


TWO_FLAGS = b"""
function main()
  if sys.flagA == 1 then
    engine.A1()
  else
    engine.A0()
  end
  if sys.flagB == 2 then
    engine.B1()
  else
    engine.B0()
  end
end
"""


# --------------------------------------------------------------------------
# Channels and the enumerated space
# --------------------------------------------------------------------------

def test_a_two_flag_chunk_has_two_channels_and_four_assignments(tmp_path):
    """SYNTHETIC. Two independent equality tests, each against one constant:
    two channels of domain 2 (`{1, something else}`, `{2, something else}`),
    so the product is exactly 4."""
    f = _compiled(tmp_path, TWO_FLAGS)
    _protos, proto = probe_enum._proto_at(f, "main_0")
    chans = channels_of(proto)
    assert [c.text for c in chans] == ["sys.flagA", "sys.flagB"]
    assert [len(c.values) for c in chans] == [2, 2]
    assert space_size(chans) == 4
    assert len(list(enumerate_assignments(chans))) == 4


def test_the_enumeration_order_is_fixed_and_names_values_by_index(tmp_path):
    """SYNTHETIC. A `divergent` verdict names an assignment, so the order has
    to be reproducible and the name has to be free of corpus text."""
    f = _compiled(tmp_path, TWO_FLAGS)
    _protos, proto = probe_enum._proto_at(f, "main_0")
    chans = channels_of(proto)
    names = [a.name for a in enumerate_assignments(chans)]
    assert names == ["sys.flagA=v0,sys.flagB=v0",
                     "sys.flagA=v0,sys.flagB=v1",
                     "sys.flagA=v1,sys.flagB=v0",
                     "sys.flagA=v1,sys.flagB=v1"]


def test_a_string_compared_branch_enumerates_the_real_constant(tmp_path):
    """SYNTHETIC, and the reason `channels_of` does not read `classes.json`:
    that file renders every string constant as the literal text `"str"`
    (deliberately -- it is how it stays free of corpus text), so an
    enumeration built from it could never construct the value that takes the
    `== "..."` arm. Here the domain holds the real bytes and the ASCII name
    holds only `v0`/`v1`."""
    f = _compiled(tmp_path, b"""
function main()
  if sys.mode == "alpha" then engine.A() else engine.B() end
end
""")
    _protos, proto = probe_enum._proto_at(f, "main_0")
    (ch,) = channels_of(proto)
    assert ch.values[0] == b"alpha"
    assert len(ch.values) == 2
    assert "alpha" not in ch.value_name(0)


def test_the_value_domain_is_finer_than_the_published_input_space(tmp_path):
    """SYNTHETIC. Two DISTINCT strings compared against one channel are one
    element of `classes.json`'s `cmp` (both render as `"str"`) and two here.
    `exhaust` therefore checks its OWN size against the budget, never the
    published `input_space`."""
    f = _compiled(tmp_path, b"""
function main()
  if sys.mode == "alpha" then engine.A()
  elseif sys.mode == "beta" then engine.B()
  else engine.C() end
end
""")
    _protos, proto = probe_enum._proto_at(f, "main_0")
    (ch,) = channels_of(proto)
    assert len(ch.values) == 3                    # alpha, beta, other
    assert probe_enum.published_space(proto) == 2  # "str", other


# --------------------------------------------------------------------------
# Exhaustive drive: both sides identical
# --------------------------------------------------------------------------

def test_two_flag_chunk_is_identical_over_the_whole_product(tmp_path):
    """SYNTHETIC. The end-to-end shape the brief asks for: a two-flag chunk
    (4 assignments) driven exhaustively on both sides, identical."""
    f = _compiled(tmp_path, TWO_FLAGS)
    v = exhaust(f, "main_0")
    assert v.kind == "identical", v
    assert (v.space_size, v.n_assignments) == (4, 4)
    assert v.entry == encode_path((("k", b"main"),))


def test_every_arm_of_every_branch_is_actually_taken(tmp_path):
    """The non-vacuity check for the fixture above: an enumeration that agreed
    because all four runs took the same path would prove nothing. Each of the
    four assignments must produce a DIFFERENT trace, and between them the four
    engine calls `A0/A1/B0/B1` must all appear."""
    f = _compiled(tmp_path, TWO_FLAGS)
    _protos, proto = probe_enum._proto_at(f, "main_0")
    chans = channels_of(proto)
    entry = encode_path((("k", b"main"),))
    seen = set()
    traces = set()
    for a in enumerate_assignments(chans):
        t = drive(f, "main_0", a, side="original", entry=entry)
        traces.add(t.raw)
        for line in t.raw.split(b"\n"):
            if line.startswith(b"C|engine."):
                seen.add(line.split(b"|")[1])
    assert seen == {b"engine.A0", b"engine.A1", b"engine.B0", b"engine.B1"}
    assert len(traces) == 4


def test_with_no_assignments_the_probe_matches_the_l1_75_stub_policy(tmp_path):
    """The stub environment is `probe_behaviour.lua`'s, shared through
    `probe_common.lua` rather than copied. With no assignments installed the
    injection hooks must be invisible: driving the chunk body alone here must
    produce the same EVENTS the L1.75 probe records, modulo that probe's extra
    invocation loop."""
    from scripts.probe_behaviour import probe_raw
    src = b"""
X = 1
function main() engine.Init() print("hi", engine.GetCount()) end
"""
    f = _compiled(tmp_path, src)
    t = drive(f, "main_0", None, side="original",
              entry=encode_path((("k", b"main"),)))
    beh = probe_raw(f.read_bytes(), is_source=False)
    assert t.raw.split(b"\n")[1:] == beh.split(b"\n")[1:]


# --------------------------------------------------------------------------
# Fault injection: an arm swap must be divergent AND name the assignment
# --------------------------------------------------------------------------

ARM_SWAP_ORIGINAL = b"""
function main()
  if sys.flagA == 1 then
    engine.TrueArm()
  else
    engine.FalseArm()
  end
end
"""

ARM_SWAP_BROKEN = b"""
function main()
  if sys.flagA == 1 then
    engine.FalseArm()
  else
    engine.TrueArm()
  end
end
"""


def test_an_injected_arm_swap_is_divergent_and_names_the_assignment(
        tmp_path, monkeypatch):
    """SYNTHETIC FAULT INJECTION, the assignment-space analogue of Task 5's
    byte-level proof: an instrument that cannot fail licenses exactly the
    claim it does not enforce.

    The two arms of the one branch are swapped on the DECOMPILED side. The
    swap is invisible to any run that does not select the branch, so a driver
    that quietly sampled one point of the space could easily miss it. The
    verdict must be `divergent` and must NAME the assignment -- and the named
    assignment must be one that actually exposes the swap, which is asserted
    by re-driving that one assignment and confirming the traces differ, and
    by confirming a hand-built *other* assignment also differs (both arms are
    swapped, so both points expose it here).
    """
    f = _compiled(tmp_path, ARM_SWAP_ORIGINAL)
    broken = ARM_SWAP_BROKEN
    monkeypatch.setattr(probe_enum, "_decompiled", lambda _p: broken)

    v = exhaust(f, "main_0")
    assert v.kind == "divergent", v
    assert v.assignment is not None
    assert v.assignment.name in ("sys.flagA=v0", "sys.flagA=v1")
    assert v.first_diff is not None and v.first_diff[0] > 1

    # The named assignment really is one that exposes it.
    entry = encode_path((("k", b"main"),))
    a = v.assignment
    t0 = drive(f, "main_0", a, side="original", entry=entry)
    t1 = drive(f, "main_0", a, side="decompiled", entry=entry)
    assert t0.raw != t1.raw
    assert first_difference(t0.raw, t1.raw) == v.first_diff


def test_a_swap_on_only_one_arm_is_still_named(tmp_path, monkeypatch):
    """The sharper form: only the `== 1` arm is wrong, so exactly ONE of the
    two assignments exposes it. The verdict must name THAT one -- naming the
    other would be a verdict that does not reproduce."""
    f = _compiled(tmp_path, ARM_SWAP_ORIGINAL)
    broken = b"""
function main()
  if sys.flagA == 1 then
    engine.Wrong()
  else
    engine.FalseArm()
  end
end
"""
    monkeypatch.setattr(probe_enum, "_decompiled", lambda _p: broken)
    v = exhaust(f, "main_0")
    assert v.kind == "divergent", v
    # v0 is the compared constant 1 (see `_sort_key`), so it is the assignment
    # that enters the wrong arm.
    assert v.assignment.name == "sys.flagA=v0"
    assert b"engine.TrueArm" in v.first_diff[1]
    assert b"engine.Wrong" in v.first_diff[2]


# --------------------------------------------------------------------------
# Budget: refusal, never a silent sample
# --------------------------------------------------------------------------

def _wide_source(n: int) -> bytes:
    body = b"".join(
        b"  if sys.f%d == 1 then engine.H%d() end\n" % (i, i) for i in range(n))
    return b"function main()\n" + body + b"end\n"


def test_a_space_over_the_budget_refuses_and_states_the_size(tmp_path):
    """SYNTHETIC. 13 independent two-valued channels is 8192 > 4096. The
    verdict states the size and NOTHING is run -- `n_assignments` is 0, which
    is what makes "over budget" distinguishable from "ran and agreed" by a
    reader who checks only one field."""
    f = _compiled(tmp_path, _wide_source(13))
    v = exhaust(f, "main_0")
    assert v.kind == "budget-exceeded", v
    assert v.space_size == 8192 > BUDGET
    assert v.n_assignments == 0


def test_the_budget_lives_in_exactly_one_place():
    """`BUDGET` is `scripts/observation_classes.py`'s, not a second copy: Task
    4 measured 1940/1944 protos and 110/113 Class-1 candidates inside it, and
    two figures that could drift would make that measurement unquotable."""
    import scripts.observation_classes as oc
    assert probe_enum.BUDGET is oc.BUDGET
    text = (probe_enum.ROOT / "scripts" / "probe_enum.py").read_text()
    assert "4096" not in text


def test_no_silent_sampling(tmp_path):
    """The property the verdict type exists to protect: an `identical` verdict
    ran the WHOLE product. If a future change adds sampling it has to add a
    verdict value, and this test is what fails if it does not."""
    f = _compiled(tmp_path, _wide_source(5))
    v = exhaust(f, "main_0")
    assert v.kind == "identical"
    assert v.n_assignments == v.space_size == 32


# --------------------------------------------------------------------------
# Reach: `identical` is never returned for a target that was never entered
# --------------------------------------------------------------------------

UNPUBLISHED = b"""
local function helper()
  if sys.flag == 1 then engine.Deep() else engine.Shallow() end
end
function main() engine.Init() end
"""


def test_a_proto_no_name_reaches_is_never_reached_not_identical(tmp_path):
    """SYNTHETIC. `helper` is a local: the chunk publishes no name that
    reaches it, so no assignment can enter it. Both sides would agree -- they
    agree about a function neither of them runs -- and reporting that as
    `identical` is exactly the failure mode this milestone kept finding in its
    other probe arms (an arm that never fired is not evidence of agreement)."""
    f = _compiled(tmp_path, UNPUBLISHED)
    _protos, proto = probe_enum._proto_at(f, "main_0")
    assert channels_of(proto)                  # it does have a channel
    v = exhaust(f, "main_0")
    assert v.kind == "never-reached", v
    assert "no published name" in v.detail
    assert v.n_assignments == 0


def test_a_published_nested_method_is_discovered_by_line_span(tmp_path):
    """SYNTHETIC. The mechanism that makes a NESTED proto drivable: the
    original's `linedefined`/`lastlinedefined` survive stripping, so the probe
    can find which published NAME carries the target function, and that name
    -- not a line number -- is what both sides are driven with."""
    f = _compiled(tmp_path, b"""
local t = {}
t.Inner = function()
  if sys.flag == 1 then engine.A() else engine.B() end
end
Outer = t
function main() engine.Init() end
""")
    hits = discover_entries(str(f), "main_0")
    assert hits == (encode_path((("k", b"Outer"), ("k", b"Inner"))),)
    v = exhaust(f, "main_0")
    assert v.kind == "identical", v
    assert v.n_assignments == 2


def test_an_ambiguous_line_span_is_refused_rather_than_guessed(tmp_path):
    """Two protos with the same line span make the discovered name ambiguous,
    and an ambiguous reach claim is worse than no claim. SYNTHETIC: real luac
    output gives one-line functions on the same line this shape."""
    f = _compiled(tmp_path, b"""
A = function() engine.A() end  B = function() engine.B() end
function main() engine.Init() end
""")
    with pytest.raises(ProbeError) as e:
        discover_entries(str(f), "main_0")
    assert "ambiguous" in str(e.value)


# --------------------------------------------------------------------------
# Probe-side failures are never comparable values
# --------------------------------------------------------------------------

def test_an_entry_that_does_not_resolve_is_not_a_comparable_value(tmp_path):
    """`ENTRYFAIL|` is not in `_MARKERS`. It produces the SAME string on both
    sides, so accepting it as a trace would report agreement for a run that
    never happened -- the L1.5 probe shipped exactly that bug once (every
    probe-side failure returned `""` and compared equal on all 229 files)."""
    f = _compiled(tmp_path, TWO_FLAGS)
    with pytest.raises(ProbeError) as e:
        drive(f, "main_0", None, side="original",
              entry=encode_path((("k", b"nosuchglobal"),)))
    assert "unrecognisable" in str(e.value)


def test_a_spec_failure_is_not_a_comparable_value(tmp_path):
    """Same rule for a malformed spec file."""
    f = _compiled(tmp_path, TWO_FLAGS)
    out = probe_enum._run(f.read_bytes(), False, b"M sideways\n")
    assert out.startswith(b"SPECFAIL|")
    assert not out.startswith(probe_enum._MARKERS)


# --------------------------------------------------------------------------
# Encoding
# --------------------------------------------------------------------------

def test_paths_and_values_encode_to_ascii_hex():
    """Keys and string values reach the probe as hex, so the spec file, the
    command line and anything that logs them stay inside the project's
    ASCII rule with no decoding policy in play."""
    p = (("k", b"gameSave"), ("k", b"myCard"), ("d", None), ("k", b"hold"))
    enc = encode_path(p)
    assert enc == "k67616d6553617665/k6d7943617264/d/k686f6c64"
    assert probe_enum.path_text_of(enc) == "gameSave.myCard[*].hold"
    assert encode_value(b"\xe3\x81\x82") == "se38182"
    assert encode_value(True) == "b1"
    assert encode_value(None) == "x"
    assert encode_value(-1.0) == "n-1"


def test_a_non_identifier_key_never_reaches_an_ascii_surface():
    """SYNTHETIC (`footprints.json` measured `non_identifier_names == 0`
    corpus-wide, so nothing real reaches this): a key that is not printable
    ASCII renders as hex in the `I|` event and in a verdict's name, never as
    the bytes."""
    enc = encode_path((("k", b"\xe3\x81\x82"),))
    text = probe_enum.path_text_of(enc)
    assert text == "0xe38182"
    assert text.isascii()


# --------------------------------------------------------------------------
# The frozen constants
# --------------------------------------------------------------------------

def test_frozen_constants_agree_with_the_l1_75_probe():
    """Both sides of every comparison must truncate at the same point, and an
    enumeration whose truncation point moved between assignments would be
    comparing two different amounts of behaviour."""
    from scripts.probe_behaviour import PROBE as L175
    a = L175.read_text(encoding="utf-8")
    b = probe_enum.PROBE.read_text(encoding="utf-8")
    for const in ("local MAX_EVENTS = 3000",
                  "local HOOK_STEP = 1000000",
                  "local INSN_BACKSTOP = 400000000"):
        assert const in a and const in b, const


def test_the_probe_uses_the_shared_driver_and_does_not_copy_it():
    """The brief's standing constraint: `probe_keyseq.lua` duplicating ~250
    lines of `probe_behaviour.lua` is recorded debt and a fourth copy was
    forbidden. Measured 2026-08-14 before the extraction: 257 identical lines
    between those two, in blocks of 4 or more."""
    b = probe_enum.PROBE.read_text(encoding="utf-8")
    for use in ("C.serialiser()", "C.recorder{", "C.proxies{",
                "C.install_determinism(", "C.stub_env{"):
        assert use in b, use
    for copied in ("local function stub_result(name)", "proxy_mt.__add = zero",
                   "G.os.exit = function", "local envfields = {}"):
        assert copied not in b, copied


def test_no_lua_patterns_in_the_probe():
    """Repo-wide rule: plain `string.find(..., true)` and byte indexing only."""
    b = probe_enum.PROBE.read_text(encoding="utf-8")
    for banned in ("string.gsub", "string.match", "string.gmatch",
                   ":gsub(", ":match(", ":gmatch("):
        assert banned not in b, banned
    for i, line in enumerate(b.splitlines(), 1):
        if "sfind(" in line and "--" not in line.split("sfind(")[0]:
            assert ", true)" in line, f"line {i}: sfind without plain=true"


# --------------------------------------------------------------------------
# The population, and the corpus demonstration
# --------------------------------------------------------------------------

def _ledger_rows():
    return probe_enum._read_ledger()


def test_the_compound_if_population_is_thirteen_leaves_of_twentyone_shapes(
        corpus_dir):
    """The number the amendment carried ("the 13 compound-`if` refusal
    protos") is the LEAF count, and the ledger's `structure:` family is 21
    shapes: the ledger copies a descendant's refusal reason up to its
    ancestors verbatim, so `snr_story_main.lua:main` (10 instructions) is
    recorded as refusing at "pc 131". Re-measured 2026-08-14: 21 shapes, 13
    leaves, 8 ancestors -- and the leaf set agrees exactly with the one
    `corpus/observation/classes.json` publishes as `refusal_origin == "own"`.
    """
    import json
    rows = _ledger_rows()
    shapes = [r for r in rows
              if (r.get("refusal_reason") or "").startswith("structure:")]
    assert len(shapes) == 21
    leaves = probe_enum.compound_if_leaves(rows)
    assert len(leaves) == 13
    classes = json.loads(
        (probe_enum.ROOT / "corpus" / "observation" / "classes.json")
        .read_text())
    published = sorted(
        (r["file"], r["proto_path"]) for r in classes["candidates"]
        if (r["mechanical"]["refusal_reason"] or "").startswith("structure:")
        and r["mechanical"]["refusal_origin"] == "own")
    assert leaves == published


def test_the_smallest_leaf_refusal_is_identical_over_its_whole_space(
        corpus_dir):
    """The bounded corpus demonstration. `snr_music.lua:main_3` is the
    cheapest of the 13 -- one channel (`pressButton()`), a two-point space --
    so it is affordable as a standing gate; the other twelve are the job.

    Its `pressButton()=v1` assignment holds the poll false forever, so that
    run is truncated at the event cap. That is a bounded truncation at the
    SAME point on both sides, and the status is recorded in the verdict so it
    can never be mistaken for a run that finished.
    """
    v = exhaust(corpus_dir / "snr_music.lua", "main_3")
    assert v.kind == "identical", v
    assert (v.n_channels, v.space_size, v.n_assignments) == (1, 2, 2)
    assert set(v.statuses) <= {"OK", "CAP"}


def test_the_full_leaf_population_verdicts_are_pinned(corpus_dir):
    """The task's deliverable, as a gate. All 13 leaves, every assignment of
    every one that fits the budget, both sides.

    Measured 2026-08-14 (standalone CLI, 5.5s wall on this host): **identical
    8, divergent 2, budget-exceeded 1, never-reached 2**. The two divergences
    are pinned in `probe_enum.EXPECTED_DIVERGENCE` with instruction-level
    evidence and are both the already-documented `__pld_R` `getobjname`
    class; adjudication is two-directional, so a changed message, a different
    diverging assignment, a converged pair or a vanished proto all fail here.

    The counts are asserted as an exact partition rather than as floors: this
    is a fixed 13-element population, so a floor would be a number that could
    only move by someone editing it.
    """
    from scripts.probe_common import adjudicate_pins
    rows = probe_enum._read_ledger()
    population = probe_enum.compound_if_leaves(rows)
    assert len(population) == 13
    counts = {k: 0 for k in probe_enum.VERDICTS}
    divergent = {}
    for f, path in population:
        v = exhaust(corpus_dir / f, path)
        counts[v.kind] += 1
        if v.kind == "divergent":
            divergent[f"{f}:{path}"] = probe_enum.evidence(v)
        if v.kind == "identical":
            # The property `identical` actually asserts, restated at the
            # call site so it cannot rot into "the run did not crash".
            assert v.n_assignments == v.space_size > 0
    assert counts == {"identical": 8, "divergent": 2,
                      "budget-exceeded": 1, "never-reached": 2}, counts
    assert adjudicate_pins(divergent, probe_enum.EXPECTED_DIVERGENCE) \
        == ([], [], [])


def test_the_one_over_budget_leaf_is_refused_with_its_size(corpus_dir):
    """`snr_s4_10_s.lua:main_58` is the only leaf outside the budget, and the
    size this instrument computes (**23616**) is not the one
    `corpus/observation/classes.json` publishes (**1152**).

    Neither is wrong: `classes.json` renders every string constant as `"str"`,
    so a channel compared against N distinct strings is ONE element there. The
    enumeration needs the real values, so it sees the finer domain. Task 4's
    "110 of 113 Class-1 candidates fit 4096" is therefore a statement about
    the coarse space, and this row is the measured example of where the two
    part company -- re-derive before quoting either as "the" input space.
    """
    _protos, proto = probe_enum._proto_at(
        corpus_dir / "snr_s4_10_s.lua", "main_58")
    assert probe_enum.published_space(proto) == 1152
    v = exhaust(corpus_dir / "snr_s4_10_s.lua", "main_58")
    assert v.kind == "budget-exceeded"
    assert (v.space_size, v.n_assignments) == (23616, 0)


def test_the_enumeration_reaches_states_the_l1_75_gate_cannot(corpus_dir):
    """Why this instrument is not redundant with the L1.75 gate, measured
    rather than argued.

    `snr_common.lua:main_81` is `keyWait`. The L1.75 gate drives one fixed
    stub policy, under which `pressButton` returns `false`; the function then
    takes `EQ 1 R3 K(true)` at pc 6, falls to `EQ 1 R1 K(0)` at pc 14 and
    returns at pc 15's `JMP -> 26`, never reaching the `DIV` at pc 16. So the
    L1.75 trace for this file records no such error at all, while the
    `pressButton()=v0` assignment reaches it on both sides.
    """
    from scripts.probe_behaviour import probe_raw
    f = corpus_dir / "snr_common.lua"
    beh = probe_raw(f.read_bytes(), is_source=False)
    assert b"R|keyWait|" not in beh
    v = exhaust(f, "main_81")
    assert v.kind == "divergent"
    assert b"arithmetic" in v.first_diff[1]


# --------------------------------------------------------------------------
# Guards: neutered, named test red, restored
# --------------------------------------------------------------------------

def test_the_reach_guard_is_load_bearing(tmp_path, monkeypatch):
    """NEUTER PROOF for the `never-reached` verdict. With the reach check
    disabled, the unpublished-helper fixture reports `identical` -- an
    agreement about a function neither side ever ran. Restored by
    `monkeypatch` at teardown; the assertion here is that the two behaviours
    genuinely differ, so the check cannot be deleted with a green tree.
    """
    f = _compiled(tmp_path, UNPUBLISHED)
    assert exhaust(f, "main_0").kind == "never-reached"

    real = probe_enum.discover_entries

    def neutered(file_str, proto_path):
        # Pretend the target is published under the chunk's only real global,
        # which is what a reach test that trusted "we called SOMETHING" would
        # effectively do.
        hits = real(file_str, proto_path)
        return hits or (encode_path((("k", b"main"),)),)

    monkeypatch.setattr(probe_enum, "discover_entries", neutered)
    assert exhaust(f, "main_0").kind == "identical"

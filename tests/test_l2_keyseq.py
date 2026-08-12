"""L2 gate: key-sequence-driven differential execution, with taint and a
coverage badge.

The L1.75 behaviour gate (`test_behaviour_probe.py`) calls every global
function a chunk defines and compares the resulting event traces. Its measured
ceiling is that the scripts *block on input*: re-measured this session over all
229 corpus files on the original side, exactly five reach a `pressButton` poll
at all, and each of them burns most of its 3000-event budget there --
snr_common 2557, snr_graphic 2606, snr_lib 2243, snr_memory 2608, snr_music
2502 poll events out of 3001 -- because the frozen stub policy answers every
button `false` and the loop never exits. This gate drives the same loops with a
scripted key sequence instead, so the state machine walks.

The other 127 files that hit the cap are NOT input-blocked: they are the linear
story scripts, truncated by sheer `vms()` volume, and no key sequence changes
that. The plan's framing ("the 3000-event cap truncating 132/229 files
mid-loop ... the game loops block on input") is right about the mechanism and
wrong about the count -- it is 5, not 132. That is the honest reach.

Design and constants live in `scripts/probe_keyseq.lua`; the sequences, the
grant rule and the pinned verdicts live in `scripts/probe_keyseq.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.probe_keyseq import (EXPECTED_VERDICT, KEY_SEQUENCES, LINE_SHIFT,
                                  PROBE, ProbeError, probe_raw)

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER = REPO_ROOT / "corpus" / "ledger.jsonl"


def _lines(trace: bytes) -> list[bytes]:
    return trace.split(b"\n")


def _bytecode(src: bytes) -> bytes:
    from pyluadec import oracle
    return oracle.compile_source(src)


# A menu loop shaped like `snr_lib.lua`'s: poll a key, branch on it, write a
# global, `wait(1)` to advance the frame, leave on CIRCLE.
MENU = b"""
sel = 1
function main()
  local done = false
  while not done do
    if pressButton("DOWN") == true then sel = sel + 1 end
    if pressButton("CIRCLE") == true then done = true end
    wait(1)
  end
  result = sel
  engine.Done(sel)
end
"""


# --------------------------------------------------------------------------
# What the key sequence buys (synthetic; no corpus needed)
# --------------------------------------------------------------------------

def test_key_sequence_walks_a_menu_loop_the_stub_policy_cannot():
    """The whole point of L2: under a sequence the loop takes DOWN twice, then
    CIRCLE, and finishes."""
    from scripts.probe_keyseq import header
    t = probe_raw(MENU, is_source=True, spec="k=1,DOWN;k=2,DOWN;k=3,CIRCLE;tail=")
    assert header(t)[0] == "OK"
    assert b"G|result|3" in _lines(t)
    assert b"C|engine.Done|1|3" in _lines(t)


def test_without_a_sequence_the_same_fixture_never_leaves_the_loop():
    """The falsification of the test above. `tail=` holds every button up
    forever, which is exactly the L1.75 stub policy for `pressButton`, and the
    fixture then runs to the event cap having decided nothing. If the key
    delivery were a no-op, the previous test's `G|result|3` would be the only
    thing distinguishing the two runs -- so this is what makes the grant
    non-vacuous rather than an artefact of the fixture being short."""
    from scripts.probe_keyseq import header
    t = probe_raw(MENU, is_source=True, spec="tail=")
    assert header(t)[0] == "CAP"
    assert not any(l.startswith(b"G|result") for l in _lines(t))


def test_the_frame_advances_only_on_wait():
    """The predecessor's harness rule (`DEBUG_KEY_SEQUENCE_HARNESS.md`:
    `frame = frame + math.max(n, 1)`), which is what makes a sequence
    reproducible: polls within one iteration all see the same frame, and only
    `wait` moves it. `wait(0)` and `wait(nil)` still advance by one, or a
    script that waits zero would spin on one frame forever."""
    t = probe_raw(b"""
function main()
  pressButton("A") pressButton("B")
  wait(3)
  pressButton("A")
  wait(0)
  pressButton("A")
  wait()
  pressButton("A")
end
""", is_source=True, spec="tail=")
    got = [l for l in _lines(t) if l.startswith(b"K|")]
    assert got == [b"K|A|1|false", b"K|B|1|false", b"K|A|4|false",
                   b"K|A|5|false", b"K|A|6|false"]


def test_scripted_frames_and_the_tail_are_both_delivered():
    """`k=` frames are exact and `tail=` applies to every frame past the LAST
    scripted one -- not to gaps between them, which stay empty."""
    t = probe_raw(b"""
function main()
  for i = 1, 5 do pressButton("X") pressButton("Y") wait(1) end
end
""", is_source=True, spec="k=1,X;k=3,X+Y;tail=Y")
    got = [l for l in _lines(t) if l.startswith(b"K|")]
    assert got == [
        b"K|X|1|true", b"K|Y|1|false",       # scripted
        b"K|X|2|false", b"K|Y|2|false",      # gap: no keys at all
        b"K|X|3|true", b"K|Y|3|true",        # scripted, two keys
        b"K|X|4|false", b"K|Y|4|true",       # tail
        b"K|X|5|false", b"K|Y|5|true",
    ]


def test_entry_point_drives_one_named_function_instead_of_everything():
    """`entry=` is what the two historical checkpoints need: they are methods
    on instances the chunk builds (`systemOption = SystemOption.new()`), and
    driving the whole file instead would run every other global function in it
    -- which for `snr_common.lua` diverges on the already-documented
    `getobjname` naming artifact and would refuse the file outright."""
    src = b"""
T = {}
function T.Go() engine.Hit(1) end
function main() engine.Never() end
"""
    t = probe_raw(src, is_source=True, spec="entry=T.Go;tail=")
    assert _lines(t) == [b"KEYSEQ1|OK|5|0", b"G|T|<table#1>",
                         b"G|main|<function#2>", b"I|T.Go",
                         b"C|engine.Hit|1|1", b"R|T.Go|ok", b""]


# --------------------------------------------------------------------------
# Non-vacuity of the instrument itself
# --------------------------------------------------------------------------

@pytest.mark.parametrize("spec,marker", [
    ("entry=T.Nope;tail=", "ENTRYFAIL"),      # names something that is not there
    ("entry=main.field;tail=", "ENTRYFAIL"),  # indexes a function
    ("nonsense", "SPECFAIL"),                 # directive without '='
    ("k=zero,X", "SPECFAIL"),                 # frame is not a number
    ("k=1", "SPECFAIL"),                      # k= without a key list
    ("cov=2", "SPECFAIL"),                    # cov takes only 1
    ("bogus=1", "SPECFAIL"),                  # unknown directive
    ("k=1,X+", "SPECFAIL"),                   # empty key name
])
def test_a_probe_side_failure_never_becomes_a_comparable_value(spec, marker):
    """`SPECFAIL` and `ENTRYFAIL` are deliberately NOT in `_MARKERS`. Both
    would produce the SAME string on both sides of a comparison -- a mistyped
    entry name is a property of the spec, not of the program -- so accepting
    one as a value would grant `L2` for a run that never happened. This is the
    L1.5 probe's hardest-won lesson: it shipped once with every probe-side
    failure returning "", and the whole 229-file gate passed while comparing
    nothing at all."""
    src = b"T = {}\nfunction main() end\n"
    with pytest.raises(ProbeError) as e:
        probe_raw(src, is_source=True, spec=spec)
    assert marker in str(e.value)


def test_a_missing_probe_script_raises_rather_than_returning_blank(tmp_path):
    import scripts.probe_keyseq as pk
    old = pk.PROBE
    pk.PROBE = tmp_path / "nope.lua"
    try:
        with pytest.raises(ProbeError):
            probe_raw(b"X = 1", is_source=True, spec="tail=")
    finally:
        pk.PROBE = Path(old)


def test_target_cannot_truncate_the_probe_with_os_exit():
    from scripts.probe_keyseq import header
    t = probe_raw(b"function main() sink(1) os.exit(0) sink(2) end",
                  is_source=True, spec="tail=")
    assert header(t)[0] == "OK"
    assert b"R|main|OSEXIT" in _lines(t)
    assert b"C|sink|1|2" not in _lines(t)


@pytest.mark.parametrize("snippet,expected", [
    (b"sink(os.time(), os.clock(), os.date())",
     b'C|sink|3|0,0,"1970-01-01"'),
    (b"math.randomseed(os.time()) sink(math.random(), math.random(1, 100))",
     b'C|sink|2|5.7485885918140411e-06,66'),
    (b"sink(collectgarbage('count'))", b'C|sink|1|0'),
    (b"sink(tostring({}), tostring(print))",
     b'C|sink|2|"table: #2","function: #3"'),
    (b"sink(os.getenv('HOME'))", b'C|sink|1|nil'),
    (b"sink(os.tmpname())", b'C|sink|1|"/tmp/pld_probe_tmp"'),
])
def test_nondeterminism_sources_are_neutralised(snippet, expected):
    """Same set, and the same EXACT-value discipline, as the L1.75 gate's: a
    two-run agreement check leaves three of these unfalsifiable (two runs a few
    milliseconds apart see the same second, the same libc `rand()` default seed
    and the same allocation total), so the assertion is the frozen value."""
    src = b"function main() " + snippet + b" end"
    assert expected in _lines(probe_raw(src, is_source=True, spec="tail="))


def test_budget_is_an_event_count_not_an_instruction_count():
    """Inherited, load-bearing: an instruction budget alone drops L1.75
    agreement from 226/229 to 95/229, because two representations of one
    program execute different numbers of VM instructions and get truncated at
    different points. Two chunks with identical observable behaviour and wildly
    different instruction counts must produce identical traces."""
    from scripts.probe_keyseq import header
    lean = b"function main() while true do tick() end end"
    fat = (b"function main() local q = 0 "
           b"while true do for i = 1, 500 do q = q + i end tick() end end")
    a = probe_raw(lean, is_source=True, spec="tail=")
    b = probe_raw(fat, is_source=True, spec="tail=")
    assert header(a) == header(b) == ("CAP", 3001, 0)
    assert a == b


def test_instruction_backstop_stops_a_loop_that_records_nothing(monkeypatch):
    """The event budget cannot see a loop that never records an event. Uses
    `PYLUADEC_PROBE_INSN_BACKSTOP` to shrink the backstop for this process
    only; see the guard below for why that cannot leak into what ships."""
    from scripts.probe_keyseq import header
    monkeypatch.setenv("PYLUADEC_PROBE_INSN_BACKSTOP", "2000000")
    t = probe_raw(b"function main() local x = 0 while true do x = x + 1 end end",
                  is_source=True, spec="tail=")
    assert header(t)[0] == "INSN"
    assert b"R|main|INSN" in _lines(t)


def test_target_pcall_cannot_defeat_the_event_cap():
    """A `pcall` inside the TARGET wrapping a stub call would otherwise catch
    the `__PLD_CAP__` raise every iteration and loop forever."""
    from scripts.probe_keyseq import header
    t = probe_raw(
        b"function main() while true do pcall(function() tick() end) end end",
        is_source=True, spec="tail=")
    assert header(t)[0] == "CAP"


def test_production_insn_backstop_constant_is_unconditionally_400_million():
    assert "local INSN_BACKSTOP = 400000000" in PROBE.read_text(encoding="utf-8")


def test_frozen_constants_agree_with_the_l1_75_probe():
    """This probe is a SEPARATE file from `probe_behaviour.lua` on purpose --
    the L1.75 gate's traces are frozen artefacts and threading two formats
    through one script would put its evidence at risk of every L2 edit. The
    price is duplication, and this is what keeps the duplicated parts from
    drifting: the budget constants and the whole stub-return policy have to be
    textually identical in both files, because a run under a different policy
    is not comparable to the L1.75 evidence that justified this one."""
    from scripts.probe_behaviour import PROBE as L175
    a = L175.read_text(encoding="utf-8")
    b = PROBE.read_text(encoding="utf-8")
    for const in ("local MAX_EVENTS = 3000",
                  "local HOOK_STEP = 1000000",
                  "local INSN_BACKSTOP = 400000000"):
        assert const in a and const in b, const
    policy = a[a.index("local function stub_result(name)"):]
    policy = policy[:policy.index("\nend\n") + 5]
    assert policy in b, "the stub-return policy has drifted between the probes"


# --------------------------------------------------------------------------
# Taint
# --------------------------------------------------------------------------

def _taint_kinds(src: bytes, spec: str = "k=1,GO;tail=") -> list[str]:
    t = probe_raw(src, is_source=True, spec=spec)
    return [l.decode("ascii", "replace") for l in _lines(t) if l.startswith(b"T|")]


@pytest.mark.parametrize("body,expected", [
    (b'if type(sys.thing) == "table" then hit() else miss() end',
     "T|intro:type|sys.thing"),
    (b"if rawequal(sys.a, sys.b) then hit() else miss() end",
     "T|intro:rawequal|sys.a"),
    (b"if getmetatable(sys.m) then hit() else miss() end",
     "T|intro:getmetatable|sys.m"),
    (b"if sys.p < sys.q then hit() else miss() end", "T|cmp:lt|sys.p"),
    (b"if sys.p <= sys.q then hit() else miss() end", "T|cmp:le|sys.p"),
    (b"if sys.p == sys.q then hit() else miss() end", "T|cmp:eq|sys.p"),
])
def test_every_taint_route_is_recorded(body, expected):
    """One case per route, so none of them is unfalsifiable surface. The three
    `cmp:` routes are the provable half -- Lua 5.1's `OP_LT`/`OP_LE`/`OP_EQ`
    produce no value, they select the following `JMP`, so a comparison
    metamethod firing on a stub IS a stub deciding a branch. The three
    `intro:` routes are the conservative half: nothing observes where their
    result went, so they are treated as if it went to a branch."""
    assert expected in _taint_kinds(b"function main() " + body + b" end")


def test_taint_is_deduplicated_and_does_not_consume_the_event_budget():
    """Taint is a SET appended after the events, not an event. A `type()`
    inside a hot loop would otherwise eat the whole budget and change what the
    gate compares -- the trace would be shorter *because* it was tainted."""
    from scripts.probe_keyseq import header
    t = probe_raw(b"""
function main()
  for i = 1, 50 do local _ = type(sys.thing) end
  sink(1)
end
""", is_source=True, spec="tail=")
    st, n, taints = header(t)
    assert (st, taints) == ("OK", 1)
    assert [l for l in _lines(t) if l.startswith(b"T|")] == \
        [b"T|intro:type|sys.thing"]
    assert b"C|sink|1|1" in _lines(t)          # the budget was not spent


def test_a_tainted_run_is_refused_even_though_the_two_sides_agree():
    """The taint-laundering fixture the plan asks for, and the shape spec risk
    R2 names: the two sides trace IDENTICALLY -- `type()` on a stub proxy says
    "table" in both -- and the gate must still refuse, because the branch that
    decided which engine call to make was decided by our stubbing rather than
    by the program."""
    from scripts.probe_keyseq import evaluate
    src = b"""
function main()
  pressButton("CIRCLE")
  if type(sys.thing) == "table" then engine.Laundered() else engine.Real() end
end
"""
    bc = _bytecode(src)
    assert probe_raw(bc, is_source=False, spec="k=1,CIRCLE;tail=") == \
        probe_raw(src, is_source=True, spec="k=1,CIRCLE;tail=")
    r = evaluate(bc, src, ["k=1,CIRCLE;tail="])
    assert (r.granted, r.reason) == (False, "taint")
    assert "intro:type" in r.detail


def test_the_same_fixture_without_the_introspection_is_granted():
    """The falsification of the test above: identical shape, identical stub
    dependence, one call removed. If the refusal came from anything other than
    the `type()` call, this would refuse too."""
    from scripts.probe_keyseq import evaluate
    src = b"""
function main()
  pressButton("CIRCLE")
  if sys.thing then engine.Laundered() else engine.Real() end
end
"""
    r = evaluate(_bytecode(src), src, ["k=1,CIRCLE;tail="])
    assert (r.granted, r.reason) == (True, None)


def test_what_the_taint_analysis_provably_cannot_catch():
    """Committed statement of the blind spots, so they are data rather than a
    claim in a docstring. All three of these ARE stub values deciding
    branches, and none of them records a mark:

    * a raw proxy as a truth value -- `OP_TEST` consults no metamethod on a
      table, so nothing fires;
    * a stub RETURN value -- `stub_result` hands back plain `nil`/`false`/`0`/
      `"stub"`, and a Lua value carries no provenance;
    * an arithmetic result -- `__add` returns the number `0`, and the
      comparison that follows is number-vs-number.

    Each line below took the stub-forced branch, and the taint count is 0.
    """
    from scripts.probe_keyseq import header
    t = probe_raw(b"""
function main()
  if sys.flag then engine.Truthy() else engine.Falsy() end
  if engine.IsDone() then engine.Done() else engine.NotDone() end
  if sys.n + 1 > 0 then engine.Pos() else engine.NonPos() end
end
""", is_source=True, spec="tail=")
    assert header(t)[2] == 0
    got = [l for l in _lines(t) if l.startswith(b"C|engine.")]
    # Measured, not predicted: the third line reads `0 > 0`, because `__add`
    # already flattened the proxy to the number 0, so the stub-forced branch is
    # the NEGATIVE one. Written the other way round first and corrected here.
    assert got == [b"C|engine.Truthy|0|", b"C|engine.IsDone|0|",
                   b"C|engine.NotDone|0|", b"C|engine.NonPos|0|"]


def test_eq_metamethod_does_not_change_what_the_program_computes():
    """`__eq` is new here relative to `probe_behaviour.lua`, which deliberately
    omits it. lvm.c consults `__eq` only after `rawequal` has already failed,
    so returning `false` is exactly the no-metamethod behaviour; it exists only
    so the EQ case can be observed. Assert both directions."""
    t = probe_raw(b"""
function main()
  local a = sys.a
  sink(a == a, sys.a == sys.b, a == sys.a)
end
""", is_source=True, spec="tail=")
    assert b"C|sink|3|true,false,true" in _lines(t)


# --------------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------------

def test_line_shift_clears_every_line_number_either_probe_can_occupy():
    """The guard behind `LINE_SHIFT`'s exactness. Without the shift the
    first-sight line classifier misclassifies any line NUMBER it saw from the
    probe's own source first -- measured this session on a 602-line
    straight-line fixture where every line executes: 60 lines lost (10.0%),
    and the lost numbers are exactly the probe's executed ranges. This is what
    makes the collision impossible rather than rare, so it has to keep
    clearing both Lua files as they grow."""
    common = REPO_ROOT / "scripts" / "probe_common.lua"
    for f in (PROBE, common):
        n = len(f.read_bytes().split(b"\n"))
        assert LINE_SHIFT > n, f"{f.name} has {n} lines, LINE_SHIFT is {LINE_SHIFT}"


def test_the_line_shift_is_what_makes_the_coverage_number_exact():
    """The mechanism, measured rather than argued: a straight-line fixture
    where EVERY line executes must come back fully covered.

    Run unshifted, it does not -- the probe's own recorder and proxy
    metamethods occupy line numbers in the same range, and the first-sight
    classifier files those numbers as foreign for the rest of the run.
    Measured this session: 60 of 602 lines lost (10.0%), and the lost numbers
    are exactly the probe's executed ranges. Shifted, nothing is lost.

    The direction is also asserted: the unshifted run is a strict SUBSET, so
    the flaw this removes could only ever under-report, never over-report.
    """
    from scripts.probe_keyseq import covered_lines, _with_cov
    n = 600
    src = ("function main()\n"
           + "\n".join(f"engine.A{i}()" for i in range(1, n + 1))
           + "\nend\n").encode()
    spec = _with_cov("k=1,X;tail=")
    truth = set(range(1, n + 3))          # 1 = the header, n+2 = the `end`

    plain = covered_lines(probe_raw(src, is_source=True, spec=spec))
    shifted = {ln - LINE_SHIFT for ln
               in covered_lines(probe_raw(b"\n" * LINE_SHIFT + src,
                                          is_source=True, spec=spec))
               if ln > LINE_SHIFT}
    assert shifted == truth
    assert plain < truth                  # strict subset: it lost lines
    assert 40 < len(truth - plain) < 120   # ~60 measured; a loose band


def test_the_line_shift_does_not_change_what_the_program_does():
    """Prepending blank lines moves `lineinfo` and `linedefined` and nothing
    else, so the coverage run measures the artifact that ships. Asserted two
    ways: the compiled code and constants are identical, and the probe's trace
    is byte-identical (which also covers the error messages, since
    `probe_common.strip_location` removes the `<source>:<line>: ` prefix)."""
    from pyluadec.ingest import load_bytes
    src = MENU + b"\nfunction boom() error('bang') end\n"
    a = load_bytes(_bytecode(src))
    b = load_bytes(_bytecode(b"\n" * LINE_SHIFT + src))
    assert a.code == b.code and a.constants == b.constants
    # ... and the shift really did land somewhere: a main chunk's
    # `linedefined` is 0 either way, so `lineinfo` is what moves.
    assert a.lineinfo != b.lineinfo
    spec = "k=1,DOWN;k=2,CIRCLE;tail="
    assert probe_raw(src, is_source=True, spec=spec) == \
        probe_raw(b"\n" * LINE_SHIFT + src, is_source=True, spec=spec)


def test_coverage_counts_the_blocks_the_run_entered():
    """Two sequences over the same artifact: one that never leaves the menu
    and one that walks it. The second must strictly dominate, and both must be
    under the block total (a fixture with an unreachable arm)."""
    from scripts.probe_keyseq import coverage
    # The unreachable arm has to live INSIDE a driven function: the probe's
    # invocation loop calls every global function the chunk defines, so a
    # top-level `function unreached()` is not unreached at all -- measured, it
    # came out at 13/13 blocks entered.
    src = b"""
sel = 1
function main()
  local done = false
  while not done do
    if pressButton("DOWN") == true then
      sel = sel + 1
    end
    if pressButton("CIRCLE") == true then
      done = true
    end
    wait(1)
  end
  if sel == 99 then
    engine.X()
    engine.Y()
    engine.Z()
  end
  engine.Done(sel)
end
"""
    shallow = coverage(src, ["tail="])
    deep = coverage(src, ["k=1,DOWN;k=2,DOWN;k=3,CIRCLE;tail="])
    assert 0 < shallow.entered < deep.entered < deep.blocks
    assert deep.fraction == round(deep.entered / deep.blocks, 4)


def test_coverage_takes_the_union_over_a_file_s_sequences():
    """A file may carry several sequences -- `snr_common.lua` needs three --
    and the badge is their union, not the best single one."""
    from scripts.probe_keyseq import coverage
    src = b"""
function main()
  if pressButton("A") == true then
    engine.A()
  end
  if pressButton("B") == true then
    engine.B()
  end
end
"""
    a = coverage(src, ["k=1,A;tail="])
    b = coverage(src, ["k=1,B;tail="])
    both = coverage(src, ["k=1,A;tail=", "k=1,B;tail="])
    assert both.entered > a.entered and both.entered > b.entered


def test_collisions_are_reported_not_hidden():
    """`Coverage.collisions` is the measured size of the one over-approximation
    left: a block whose entry line is shared with another block counts as
    entered when either of them runs. A single-line `if` has several blocks on
    one line, so it must be reported."""
    from scripts.probe_keyseq import block_entry_lines
    one_line = b"function main() if sys.a then engine.X() else engine.Y() end end"
    spread = b"""
function main()
  if sys.a then
    engine.X()
  else
    engine.Y()
  end
end
"""
    assert block_entry_lines(one_line)[1] > block_entry_lines(spread)[1]


# --------------------------------------------------------------------------
# The grant rule
# --------------------------------------------------------------------------

def test_a_divergent_pair_is_refused():
    from scripts.probe_keyseq import evaluate
    src = MENU
    mutated = MENU.replace(b"sel = sel + 1", b"sel = sel - 1")
    r = evaluate(_bytecode(src), mutated, ["k=1,DOWN;k=2,CIRCLE;tail="])
    assert (r.granted, r.reason) == (False, "divergent")


def test_a_file_the_sequence_never_polls_is_refused():
    """Otherwise every corpus file would be grantable by handing it a sequence
    it has nothing to do with: two identical traces of a program that never
    read an input are an L1.75 result wearing an L2 badge."""
    from scripts.probe_keyseq import evaluate
    src = b"function main() engine.Go() end"
    r = evaluate(_bytecode(src), src, ["k=1,X;tail="])
    assert (r.granted, r.reason) == (False, "no-key-poll")


def test_a_probe_side_failure_refuses_rather_than_propagating():
    """Refusing is not comparing, so catching the failure here does not break
    the "never turn a probe failure into a value" rule -- but it must produce
    the `probe-error` reason, not a silent grant."""
    from scripts.probe_keyseq import evaluate
    r = evaluate(_bytecode(b"function main() end"), b"function main() end",
                 ["entry=nope.nope;tail="])
    assert (r.granted, r.reason) == (False, "probe-error")


def test_a_source_that_does_not_compile_is_refused_not_crashed():
    from scripts.probe_keyseq import evaluate
    r = evaluate(_bytecode(MENU), b"function main() this is not lua end",
                 ["k=1,CIRCLE;tail="])
    assert (r.granted, r.reason) == (False, "divergent")


def test_every_sequence_must_pass_not_just_one():
    """The grant is over ALL of a file's sequences. A defect on a path only the
    second sequence reaches must not be masked by the first one passing."""
    from scripts.probe_keyseq import evaluate
    src = b"""
function main()
  if pressButton("A") == true then engine.A() end
  if pressButton("B") == true then engine.B() end
end
"""
    mutated = src.replace(b"engine.B()", b"engine.WRONG()")
    r = evaluate(_bytecode(src), mutated, ["k=1,A;tail="])
    assert r.granted, "the A-only sequence cannot see the defect"
    r = evaluate(_bytecode(src), mutated, ["k=1,A;tail=", "k=1,B;tail="])
    assert (r.granted, r.reason) == (False, "divergent")


def test_the_ledger_field_never_carries_corpus_content():
    """`refusal_reason`-style discipline: `detail` can quote a trace line and a
    trace line can carry a Japanese string constant, so it stays out of the
    ledger. What goes in is a number or a word from a fixed vocabulary."""
    from scripts.probe_keyseq import REFUSAL_KINDS, L2Result
    assert L2Result(True, None, 0.5).as_ledger_field() == {"cov": 0.5}
    for kind in REFUSAL_KINDS:
        assert L2Result(False, kind, None, "sink(\"日本語\")").as_ledger_field() \
            == {"refused": kind}


# --------------------------------------------------------------------------
# The ledger schema
# --------------------------------------------------------------------------

def test_row_l2_is_granted_only_when_every_occurrence_is():
    """The aggregation rule, and the reason it is conservative: a shape occurs
    in up to 27 files, and a max-based rule would lend one granted file's badge
    to 26 nobody ran."""
    from pyluadec.verify.ledger import row_l2
    assert row_l2([{"l2": {"cov": 0.8}}, {"l2": {"cov": 0.6}}]) == {"cov": 0.6}
    assert row_l2([{"l2": {"cov": 0.8}}, {"l2": None}]) is None
    assert row_l2([{"l2": {"cov": 0.8}}, {"l2": {"refused": "taint"}}]) is None
    assert row_l2([{"l2": {"cov": 0.8}}, {}]) is None          # pre-schema row
    assert row_l2([]) is None


def test_committed_ledger_l2_fields_are_coherent():
    """Row-level `l2` is an aggregate of the occurrences and nothing else, and
    the per-occurrence records use exactly the vocabulary
    `scripts/probe_keyseq.py` commits to. Both are checked against the
    committed file, so a hand-edit or a half-migrated writer fails here."""
    from scripts.probe_keyseq import REFUSAL_KINDS
    from pyluadec.verify.ledger import row_l2
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    driven = set()
    for r in rows:
        assert r["l2"] == row_l2(r["occurrences"]), r["shash"]
        for o in r["occurrences"]:
            v = o["l2"]
            if v is None:
                continue
            driven.add(o["file"])
            assert set(v) in ({"cov"}, {"refused"}), v
            if "cov" in v:
                assert 0.0 <= v["cov"] <= 1.0
            else:
                assert v["refused"] in REFUSAL_KINDS
    assert driven == set(KEY_SEQUENCES), (
        "the files carrying an l2 record must be exactly the files with an "
        "authored key sequence")


# --------------------------------------------------------------------------
# The corpus gate
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def l2_results(corpus_dir, decompiled):
    """`{name: L2Result}` for the five files with an authored sequence.

    Measured cost this session: see the task report. The decompiled sources
    come from conftest's session-scoped `decompiled` cache, so this gate never
    re-walks the corpus itself.
    """
    from scripts.probe_keyseq import evaluate_corpus
    return evaluate_corpus(corpus_dir, lambda f: decompiled(f).source)


def test_corpus_l2_verdicts_are_what_is_pinned(l2_results):
    """Two-directional, like the probe gates' divergence pins: a file that
    silently stops being granted AND a refusal that quietly converges both
    fail. Measured 2026-08-12: all five authored files are granted."""
    got = {n: ("granted" if r.granted else r.reason) for n, r in l2_results.items()}
    assert got == EXPECTED_VERDICT, {
        n: l2_results[n].detail for n in got if got[n] != EXPECTED_VERDICT.get(n)}


def test_corpus_l2_reach_is_not_vacuous(l2_results):
    """The gate must not be passing because the sequences drove nothing.

    Floors are deliberately well under the measurement (2026-08-12:
    snr_lib 0.9474, snr_music 0.7235, snr_graphic 0.5349, snr_memory 0.5110,
    snr_common 0.2052) so ordinary drift does not fail them, but a collapse of
    the instrument does. `snr_common.lua`'s badge is low for a real reason and
    not a defect: its denominator is all 10,332 blocks of a 20k-line file, and
    three sequences driving two menu functions cannot reach the story code.
    """
    assert set(l2_results) == set(KEY_SEQUENCES)
    for name, r in l2_results.items():
        assert r.granted, f"{name}: {r.reason} ({r.detail})"
        assert r.cov > 0.15, f"{name} reaches only {r.cov:.1%} of its blocks"
    assert max(r.cov for r in l2_results.values()) > 0.8


def test_the_sequences_actually_drive_the_corpus_loops(corpus_dir):
    """The reach ratchet. Every authored sequence must record at least one
    poll on the ORIGINAL side -- a sequence whose buttons the file never reads
    would still let the file be granted on trace equality alone, which is the
    L1.75 result with a better name.

    Also the measurement this gate exists for: under the L1.75 policy these
    five files spend 2243-2608 of their 3000 events polling. Driven, the ones
    that leave their loops finish in double digits.
    """
    from scripts.probe_keyseq import header, poll_count
    for name, specs in sorted(KEY_SEQUENCES.items()):
        raw = (corpus_dir / name).read_bytes()
        for spec in specs:
            t = probe_raw(raw, is_source=False, spec=spec)
            assert poll_count(t) > 0, f"{name} never polled under {spec}"
            assert header(t)[0] in ("OK", "CAP"), f"{name}/{spec}: {header(t)}"


def test_injected_arithmetic_swap_is_caught(corpus_dir, decompiled):
    """Fault injection on a real corpus file: swap one `+` for a `-` in the
    emitted source -- the smallest possible decompiler defect -- and require
    the gate to refuse. `snr_lib.lua` ships fully structured (certified `L3`),
    and the mutated line is the menu's own clamp, i.e. on the path the key
    sequence walks."""
    from scripts.probe_keyseq import evaluate
    f = corpus_dir / "snr_lib.lua"
    src = decompiled(f).source
    anchor = b"l1_0 = l1_0 + 1 > 4 and 4 or l1_0 + 1"
    assert src.count(anchor) == 1, (
        f"injection anchor {anchor!r} is no longer unique in snr_lib.lua "
        f"(count={src.count(anchor)}); re-derive it -- an anchor that matches "
        "nothing would make this test pass without injecting anything")
    mutated = src.replace(anchor, b"l1_0 = l1_0 - 1 > 4 and 4 or l1_0 - 1")
    r = evaluate(f.read_bytes(), mutated, KEY_SEQUENCES["snr_lib.lua"])
    assert (r.granted, r.reason) == (False, "divergent")


def test_injected_gate_removal_is_caught(corpus_dir, decompiled):
    """The defect class the predecessor's playbook was written for: a
    conditional gate promoted to unconditional (`DEBUG_KEY_SEQUENCE_HARNESS.md`
    -- "`break` 只能在原始路径触发，不能被提升为无条件 `break`"). Here the
    "already pressed" gate in `snr_lib.lua`'s CIRCLE branch is removed, which
    no static comparison of the two sources would call a semantic change and
    which only shows up when a key sequence actually presses CIRCLE twice."""
    from scripts.probe_keyseq import evaluate
    f = corpus_dir / "snr_lib.lua"
    src = decompiled(f).source
    anchor = b"""        if pressButton("CIRCLE") == true then
            if l1_2 == 0 then
                break
            end"""
    assert src.count(anchor) == 1, "re-derive the injection anchor"
    mutated = src.replace(anchor, b"""        if pressButton("CIRCLE") == true then
            if true then
                break
            end""")
    r = evaluate(f.read_bytes(), mutated, KEY_SEQUENCES["snr_lib.lua"])
    assert (r.granted, r.reason) == (False, "divergent")

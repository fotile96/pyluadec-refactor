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


def test_the_coverage_run_has_a_working_backstop(monkeypatch):
    """I1. `INSN_BACKSTOP` is structurally UNREACHABLE in a coverage run, and
    this was found by review, not by construction.

    With `LUA_MASKLINE` set, `lvm.c::traceexec` fires the count hook only when
    `L->hookcount` is exactly 0 at its own entry, but the line hook's Lua body
    runs with `L->allowhook == 0` (`ldo.c::luaD_callhook`), where `traceexec`
    still calls `resethookcount` while `luaD_callhook` silently does nothing;
    with a hook body executing on most instructions the zero-crossing almost
    always lands inside it. Measured on this VM over 3,000,003 line events:
    mask `""` -> 6 count events, mask `"l"` -> **0**, mask `"lc"` -> **0**.

    Before this fix the reviewer's `while true do x = x + 1 end` returned
    `INSN` under `tail=` and ran to the 120s subprocess timeout under
    `tail=;cov=1`. It now stops, on a LINE-event budget -- a genuine bound,
    since every line event costs at least one VM instruction.
    """
    from scripts.probe_keyseq import _with_cov, header
    monkeypatch.setenv("PYLUADEC_PROBE_LINE_BACKSTOP", "50000")
    src = b"function main() local x = 0 while true do x = x + 1 end end"
    t = probe_raw(src, is_source=True, spec=_with_cov("tail="), timeout=30.0)
    assert header(t)[0] == "INSN"
    # No `R|main|INSN` event here, unlike the non-coverage path: the raise
    # comes from inside the LINE hook, which re-enters with `stopped` already
    # set and flushes before the invocation loop can append its result. The
    # status is the observable, and it is the one the driver reads.
    assert not any(l.startswith(b"R|main") for l in _lines(t))


def test_production_line_backstop_constant_is_unconditionally_20_million():
    """Same contract as the instruction backstop's: the env var may only
    shrink it for a test process that opts in, never change what the corpus
    gate or the CLI run with."""
    assert "local LINE_BACKSTOP = 20000000" in PROBE.read_text(encoding="utf-8")


def test_production_insn_backstop_constant_is_unconditionally_400_million():
    assert "local INSN_BACKSTOP = 400000000" in PROBE.read_text(encoding="utf-8")


def test_the_semantically_shared_parts_of_the_two_probes_are_identical():
    """This probe is a SEPARATE file from `probe_behaviour.lua` on purpose --
    the L1.75 gate's traces are frozen artefacts and threading two formats
    through one script would put its evidence at risk of every L2 edit. The
    price is duplication.

    **What this pins, stated as a measurement rather than as "the two files
    cannot drift".** They can: `difflib` reports 297 identical lines between
    them, in runs of 5 or more totalling 245 (re-measured this session), and
    an earlier version of this test pinned about 14 of those. It now pins every region whose drift would
    make an L2 result incomparable with the L1.75 evidence that justified it
    -- the budget constants, the whole stub-return policy, the whole proxy
    arithmetic/index/newindex/call block, and the whole determinism-override
    block. Comments, the serialisers and the recorder are NOT pinned, and a
    change there is free.
    """
    from scripts.probe_behaviour import PROBE as L175
    a = L175.read_text(encoding="utf-8")
    b = PROBE.read_text(encoding="utf-8")
    for const in ("local MAX_EVENTS = 3000",
                  "local HOOK_STEP = 1000000",
                  "local INSN_BACKSTOP = 400000000"):
        assert const in a and const in b, const

    def code_only(text: str) -> str:
        # Comments are free to differ -- they document two different gates.
        return "\n".join(l for l in text.splitlines()
                          if l.strip() and not l.strip().startswith("--"))

    def region(text, start, end):
        i = text.index(start)
        return code_only(text[i:text.index(end, i)])

    b_code = code_only(b)

    shared = [
        ("stub-return policy",
         region(a, "local function stub_result(name)", "\nend\n") + "\nend"),
        ("proxy construction",
         region(a, "local proxies = {}", "local function zero()")),
        ("proxy index/newindex/call",
         region(a, "proxy_mt.__index = function", "proxy_mt.__add = zero")),
        ("proxy arithmetic",
         region(a, "proxy_mt.__add = zero", "proxy_mt.__lt")),
        ("determinism overrides",
         region(a, "G.os.exit = function", "G.print = function")),
    ]
    for what, text in shared:
        assert text in b_code, f"{what} has drifted between the two probes"
    assert sum(len(t.splitlines()) for _, t in shared) > 60


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


def test_the_same_fixture_with_the_branch_taken_off_a_local_is_granted():
    """The falsification of the test above, in two steps, because the first
    one measured differently than predicted.

    Dropping only the `type()` call leaves `if sys.thing then` -- a raw proxy
    as a truth value -- which the STATIC backstop now refuses as
    `blind-truthiness`. So that is asserted too, rather than quietly rewritten
    away: it is the same property, caught by the other instrument. Only when
    the branch is taken off a value the stub environment did not produce does
    the file grant."""
    from scripts.probe_keyseq import evaluate
    truthy = b"""
function main()
  pressButton("CIRCLE")
  if sys.thing then engine.Laundered() else engine.Real() end
end
"""
    r = evaluate(_bytecode(truthy), truthy, ["k=1,CIRCLE;tail="])
    assert (r.granted, r.reason) == (False, "taint-static")
    assert "blind-truthiness" in r.detail

    clean = b"""
function main()
  local n = 1
  if pressButton("CIRCLE") == true then n = 2 end
  if n == 1 then engine.Laundered() else engine.Real() end
end
"""
    r = evaluate(_bytecode(clean), clean, ["k=1,CIRCLE;tail="])
    assert (r.granted, r.reason) == (True, None)


# The twelve routes that shipped granted, one parametrised case each. Every
# one takes a stub-forced branch; NONE of them fires a metamethod, because
# `lvm.c`'s `equalobj` is `ttype(o1) == ttype(o2) && luaV_equalval(...)` -- so
# `__eq` is consulted only for proxy-vs-proxy. Measured 2026-08-12 before the
# static backstop: all twelve granted with a taint count of 0.
_LAUNDERING_ROUTES = [
    ("eq-vs-string", b'if sys.s == "x" then hit() else miss() end'),
    ("eq-vs-nil", b'if sys.s == nil then hit() else miss() end'),
    ("ne-vs-nil", b'if sys.s ~= nil then hit() else miss() end'),
    ("eq-vs-number", b'if sys.s == 1 then hit() else miss() end'),
    ("eq-vs-plain-table", b'local t = {} if sys.s == t then hit() else miss() end'),
    ("len", b'if #sys.s > 0 then hit() else miss() end'),
    ("next", b'if next(sys.s) == nil then hit() else miss() end'),
    ("tostring", b'if tostring(sys.s) == "x" then hit() else miss() end'),
    ("tonumber", b'if tonumber(sys.s) then hit() else miss() end'),
    ("concat", b'if sys.s .. "" == "x" then hit() else miss() end'),
    ("select", b'if select("#", sys.s) == 1 then hit() else miss() end'),
    ("pcall", b'if pcall(sys.s) then hit() else miss() end'),
]


def _route_src(body: bytes) -> bytes:
    return b"function main()\n  pressButton('CIRCLE')\n  " + body + b"\nend\n"


@pytest.mark.parametrize("name,body", _LAUNDERING_ROUTES,
                         ids=[n for n, _ in _LAUNDERING_ROUTES])
def test_the_runtime_marks_are_blind_to_this_route(name, body):
    """Half of the C1 pair, and the reason a static backstop exists at all:
    the RUNTIME instrument records nothing for any of these. Asserted rather
    than described, so that if a future change makes one of them observable
    the claim fails instead of quietly becoming stale."""
    from scripts.probe_keyseq import header
    t = probe_raw(_route_src(body), is_source=True, spec="k=1,CIRCLE;tail=")
    assert header(t)[2] == 0
    assert [l for l in _lines(t) if l.startswith(b"T|")] == []


@pytest.mark.parametrize("name,body", _LAUNDERING_ROUTES,
                         ids=[n for n, _ in _LAUNDERING_ROUTES])
def test_every_laundering_route_is_refused_by_the_static_backstop(name, body):
    """The other half: each of the twelve is refused, and the two traces agree
    byte-for-byte while it happens -- which is exactly why trace equality on
    its own could not be the whole grant rule."""
    from scripts.probe_keyseq import evaluate
    src = _route_src(body)
    bc = _bytecode(src)
    assert probe_raw(bc, is_source=False, spec="k=1,CIRCLE;tail=") == \
        probe_raw(src, is_source=True, spec="k=1,CIRCLE;tail="), name
    r = evaluate(bc, src, ["k=1,CIRCLE;tail="])
    assert (r.granted, r.reason) == (False, "taint-static"), name


def test_the_static_backstop_does_not_refuse_a_clean_program():
    """Non-vacuity: a refusal rule that refuses everything is not a gate. Same
    shape, branch taken off a local the stub environment did not produce."""
    from scripts.probe_keyseq import static_refusal
    from pyluadec.ingest import load_bytes
    src = _route_src(b'local n = 0 if n == 1 then hit() else miss() end')
    assert static_refusal(load_bytes(_bytecode(src))) == {}


@pytest.mark.parametrize("body,kind", [
    (b'if sys.a == "x" then hit() end', "blind-compare"),
    (b'local v = sys.a if v == "x" then hit() end', "blind-compare"),
    (b'if #sys.a > 0 then hit() end', "blind-length"),
    (b'if type(sys.a) == "table" then hit() end', "blind-launder"),
    (b'if sys.a then hit() end', "blind-truthiness"),
    (b'if sys.a.b.c then hit() end', "blind-truthiness"),
    (b'if sys.a() then hit() end', "blind-truthiness"),
    (b'if sys.a + 1 == 2 then hit() end', "blind-compare"),
])
def test_static_taint_names_the_kind_it_found(body, kind):
    """One case per propagation rule the analysis implements: a direct global
    read, a `MOVE` through a local, `LEN`, a launderer call, raw truthiness,
    a `GETTABLE` chain, a `CALL` result, and arithmetic."""
    from scripts.probe_keyseq import static_taint
    from pyluadec.ingest import load_bytes
    src = b"function main() " + body + b" end"
    counts = static_taint(load_bytes(_bytecode(src)))
    assert counts[kind] > 0, counts


def test_a_global_the_chunk_defines_is_not_a_stub():
    """The analysis' seed set is globals READ and never WRITTEN, minus the
    ones the probe environment resolves for real. A chunk that defines its own
    global and then compares it is not stub-derived and must not refuse --
    otherwise the backstop would refuse every file that has a state variable."""
    from scripts.probe_keyseq import static_refusal
    from pyluadec.ingest import load_bytes
    src = b'mode = "a"\nfunction main() if mode == "a" then hit() end end\n'
    assert static_refusal(load_bytes(_bytecode(src))) == {}


def test_the_base_global_set_is_the_interpreter_s_own():
    """`_BASE_GLOBALS` decides which `GETGLOBAL`s are NOT stubs, so a name
    missing from it makes the backstop refuse a clean file and a name wrongly
    in it makes the backstop miss a real stub. Re-derived from the vendored
    interpreter rather than trusted."""
    import subprocess
    from pyluadec import oracle
    from scripts.probe_keyseq import _BASE_GLOBALS
    prog = ("local k = {} for n in pairs(_G) do if type(n) == 'string' then "
            "k[#k+1] = n end end table.sort(k) print(table.concat(k, ' '))")
    with __import__("tempfile").TemporaryDirectory() as td:
        f = Path(td) / "g.lua"
        f.write_text(prog)
        out = subprocess.run([str(oracle.lua_sz4()), str(f)],
                             capture_output=True, text=True, check=True).stdout
    assert set(out.split()) == set(_BASE_GLOBALS)


def test_what_the_two_taint_instruments_still_cannot_see():
    """Committed statement of the RESIDUAL gaps, as data.

    The previous version of this test presented three blind spots as the
    complete list. It was not complete -- twelve laundering routes were
    granted -- and that framing is what let them ship. These are gaps in the
    STATIC analysis (the runtime marks are blind to all of them too), each
    demonstrated rather than asserted in prose: the file grants, and it should
    not.
    """
    from scripts.probe_keyseq import evaluate, static_refusal
    from pyluadec.ingest import load_bytes

    gaps = {
        # Across a call boundary: `static_taint` is intra-proto, so a stub
        # passed as an ARGUMENT is a plain parameter inside the callee.
        "call-argument": b"""
function decide(v) if v == "x" then hit() else miss() end end
function main() pressButton("CIRCLE") decide(sys.a) end
""",
        # Through a script-built table: only indexing off a stub-derived
        # table propagates, not a round trip through one the chunk made.
        "table-round-trip": b"""
function main()
  pressButton("CIRCLE")
  local t = {}
  t.x = sys.a
  if t.x == "x" then hit() else miss() end
end
""",
        # Through an indirectly-reached launderer: `blind-launder` recognises
        # `GETGLOBAL f; ...; CALL f` only, and a `MOVE` into the call window
        # breaks that pattern.
        #
        # Written first with `local ty = type`, which MEASURED as caught --
        # `type` is one of the probe's driver overrides, so the RUNTIME mark
        # fires on the aliased call too. `tostring` has no runtime seam, so it
        # is the honest example of this gap.
        "aliased-launderer": b"""
function main()
  pressButton("CIRCLE")
  local ts = tostring
  if ts(sys.a) == "x" then hit() else miss() end
end
""",
    }
    for name, src in gaps.items():
        assert static_refusal(load_bytes(_bytecode(src))) == {}, name
        r = evaluate(_bytecode(src), src, ["k=1,CIRCLE;tail="])
        assert r.granted, f"{name} unexpectedly refused -- update this list"


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


def test_coverage_counts_the_protos_and_the_blocks_the_run_entered():
    """Two sequences over the same artifact: one that never leaves the menu and
    one that walks it. The block diagnostic must strictly improve and stay
    under the total (the fixture has an arm no sequence reaches)."""
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
    assert 0 < shallow.blocks_upper < deep.blocks_upper < deep.blocks
    assert deep.blocks_lower <= deep.blocks_upper
    assert deep.protos_entered == deep.protos == 2   # the chunk and `main`
    assert deep.fraction == 1.0


def test_the_badge_is_proto_coverage_and_does_not_move_with_source_layout():
    """I3, and the reason the badge is not block coverage.

    Two byte-different sources with identical semantics -- the same program,
    one spread over lines and one compacted. Measured this session over the
    same 10 blocks: the block interval reads [0.30, 0.50] spread and
    [0.00, 0.90] compacted, while the proto badge is 0.6667 both times,
    because it counts protos entered by call-hook identity and never consults
    a line.

    That is not a nicety. CLAUDE.md defines a presentation-layer change as one
    that leaves `corpus/ledger.jsonl` byte-unchanged, and M5 task 7 shipped
    five printer changes on exactly that evidence; a layout-sensitive `cov`
    would have made them read as reach regressions and would make
    `ratchet_diff`'s `l2-coverage-downgrade` fire on cosmetics.
    """
    from scripts.probe_keyseq import coverage
    spread = b"""
function main()
  pressButton("A")
  if sys.a then
    engine.X()
  elseif sys.b then
    engine.Y()
  else
    engine.Z()
  end
end
function never()
  engine.N()
end
"""
    compact = (b'function main() pressButton("A") '
               b'if sys.a then engine.X() elseif sys.b then engine.Y() '
               b'else engine.Z() end end\n'
               b'function never()\n  engine.N()\nend\n')
    # `entry=main`, so the probe's invocation loop does not run and `never`
    # really is never entered -- without that the badge is 3/3 either way and
    # the assertion below would hold vacuously.
    a = coverage(spread, ["entry=main;k=1,A;tail="])
    b = coverage(compact, ["entry=main;k=1,A;tail="])
    assert a.blocks == b.blocks                      # same program
    assert a.block_interval != b.block_interval      # layout moved the blocks
    assert a.fraction == b.fraction                  # the badge did not
    assert a.protos_entered == b.protos_entered == 2 and a.protos == 3


def test_the_block_diagnostic_is_an_interval_not_a_value():
    """`collisions` is the width of the ignorance and the interval is how it
    is reported. The lower bound counts only blocks whose entry line names
    exactly one block; the upper credits any block sharing an executed line."""
    from scripts.probe_keyseq import coverage
    c = coverage(MENU, ["k=1,DOWN;k=2,CIRCLE;tail="])
    lo, hi = c.block_interval
    assert 0 < lo < hi <= 1.0
    assert c.collisions > 0
    assert c.blocks_lower < c.blocks_upper <= c.blocks


def test_a_non_injective_proto_key_refuses_rather_than_merging_protos():
    """The badge's de-duplication key is `(linedefined, lastlinedefined)`, so
    two closures of one proto count once. Measured over eight artifacts (the
    five authored files plus snr_novel, snr_crd_0, config): 390 protos, 390
    distinct keys. But a hand-written one-liner collides, and a silent merge
    would under-report the badge, so the check is per run."""
    from scripts.probe_keyseq import CoverageError, coverage
    src = (b'function main() pressButton("A") local f = function() engine.A() end'
           b' local g = function() engine.B() end f() g() end')
    with pytest.raises(CoverageError) as e:
        coverage(src, ["k=1,A;tail="])
    assert "not injective" in str(e.value)


def test_the_block_diagnostic_unions_the_sequences_and_the_badge_maxes_them():
    """A file may carry several sequences -- `snr_common.lua` has three. Lines
    are unioned (they are just numbers). Proto counts are NOT: proto identity
    is per-process and the counts are not addable, so the badge takes the max,
    which is the conservative read."""
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
    assert both.blocks_upper > a.blocks_upper and both.blocks_upper > b.blocks_upper
    assert both.protos_entered == max(a.protos_entered, b.protos_entered)


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


def test_a_file_with_no_sequence_is_refused_not_granted():
    """I2. With `evaluate`'s `if not specs:` removed, `evaluate(bc, src, [])`
    returned `granted=True, cov=0.0` -- measured. The per-spec loop simply
    never ran, so not one of the grant conditions was evaluated: the rule was
    skipped rather than failed, which is the worst available failure mode for
    a gate."""
    from scripts.probe_keyseq import evaluate
    r = evaluate(_bytecode(MENU), MENU, [])
    assert (r.granted, r.reason, r.cov) == (False, "no-key-poll", None)


def test_a_chunk_that_defines_pressButton_itself_wins_over_the_driver():
    """M3, `env.__index`'s `envfields`-before-`DRIVER` precedence. Reachable,
    not defensive: a chunk that defines its own `wait` must see its own, or
    the probe would silently replace program logic with harness logic."""
    t = probe_raw(b"""
function wait(n) engine.MyWait(n) end
function main() wait(7) end
""", is_source=True, spec="tail=")
    assert b"C|engine.MyWait|1|7" in _lines(t)
    assert not any(l.startswith(b"C|wait|") for l in _lines(t))


@pytest.mark.parametrize("call,expected", [
    (b"pressButton(nil)", b"K|nil|1|false"),
    (b"pressButton(7)", b"K|7|1|false"),
    (b"pressButton('A')", b"K|A|1|true"),
])
def test_a_non_string_key_name_polls_false_instead_of_erroring(call, expected):
    """M3, `press`'s `type(name) == "string"` guard. Reachable: indexing the
    scripted key set with a non-string would not error, but it would let a
    table-valued argument alias a key name; the guard makes the answer `false`
    and the event still records what was asked for."""
    t = probe_raw(b"function main() " + call + b" end", is_source=True,
                  spec="k=1,A;tail=")
    assert expected in _lines(t)


def test_wait_with_a_nan_or_negative_argument_still_advances_one_frame():
    """M3, `waitf`'s NaN and `< 1` guards. Reachable: `wait(0/0)` and
    `wait(-5)` both appear plausible in generated code, and either would
    freeze or rewind the frame counter, turning a scripted sequence into an
    unreproducible one."""
    t = probe_raw(b"""
function main()
  pressButton("A") wait(0/0)
  pressButton("A") wait(-5)
  pressButton("A")
end
""", is_source=True, spec="k=1,A;k=2,A;k=3,A;tail=")
    got = [l for l in _lines(t) if l.startswith(b"K|")]
    assert got == [b"K|A|1|true", b"K|A|2|true", b"K|A|3|true"]


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
    """The gate must not be passing because the sequences drove nothing, and
    it must not be passing because it refuses everything either.

    Measured 2026-08-12, after the static backstop landed: **one of the five
    authored files is granted** (`snr_lib.lua`, 3/3 protos entered, block
    coverage in [0.39, 0.95] of 57 blocks). The other four all carry
    `blind-compare` sites and are refused whole-file. That is the honest
    reach, and it is much smaller than the reach before the backstop -- when
    all five were granted and four of them should not have been.
    """
    assert set(l2_results) == set(KEY_SEQUENCES)
    granted = {n: r for n, r in l2_results.items() if r.granted}
    assert granted, "every authored file refuses -- the gate proves nothing"
    for name, r in granted.items():
        assert r.cov > 0.5, f"{name} entered only {r.cov:.1%} of its protos"
    refused = {n: r.reason for n, r in l2_results.items() if not r.granted}
    assert set(refused.values()) <= {"taint-static"}, refused


def test_what_the_l2_badge_actually_exercises(l2_results):
    """Reported as a number rather than left to be inferred. The badge covers
    `snr_lib.lua` only: 3 proto occurrences of 1944, and all three ship
    STRUCTURED text (`snr_lib.lua` is one of the 216 fully-structured files).

    So L2 currently validates the structured emitter on one file, and says
    nothing at all about the fallback state machine -- the four refused files
    are exactly the ones that ship fallback or hybrid.
    """
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    badged = [o for r in rows for o in r["occurrences"]
              if o.get("l2") and "cov" in o["l2"]]
    assert {o["file"] for o in badged} == {n for n, r in l2_results.items()
                                           if r.granted} == {"snr_lib.lua"}
    assert len(badged) == 3
    assert {o["shipped"] for o in badged} == {"structured"}


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

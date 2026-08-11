"""L1.75 gate: compare observable *behaviour* -- the engine calls a chunk's
global functions make -- between original bytecode and decompiled output.

The L1.5 gate (`test_global_state_probe.py`) compares only the delta a chunk
makes to the global table. Re-measured this session over all 229 corpus files,
that payload has a median of 22 characters, 227 of 229 are under 40, and for
222 files it is exactly `string:main=<function>`: it asserts that a global
named `main` exists and is a function, while every statement inside it is never
executed. This gate calls it.

Design and constants live in `scripts/probe_behaviour.lua`; the pinned
divergences and the adjudication rule live in `scripts/probe_behaviour.py` and
`scripts/probe_common.py` so that the CLI and this gate cannot disagree.
"""
import collections
import hashlib
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.probe_behaviour import EXPECTED_DIVERGENCE
from scripts.probe_common import adjudicate_pins


def _probe_src(src: bytes) -> bytes:
    from scripts.probe_behaviour import probe_raw
    return probe_raw(src, is_source=True)


def _lines(trace: bytes) -> list[bytes]:
    return trace.split(b"\n")


# --------------------------------------------------------------------------
# What the probe observes (synthetic; no corpus needed)
# --------------------------------------------------------------------------

def test_probe_invokes_the_functions_the_chunk_defines():
    """The whole point of L1.75: `main` is CALLED, not merely reported to be a
    function. The L1.5 payload for this chunk would be `string:main=<function>`
    and nothing else."""
    from scripts.probe_behaviour import header
    t = _probe_src(b"""
X = 1
function main()
  engine.Init()
  local n = engine.GetCount()
  print("hello", n)
  for i = 1, 3 do engine.Draw(i, "cg" .. i) end
  if engine.IsDone() then engine.Never() end
end
""")
    assert header(t) == ("OK", 11)
    assert _lines(t) == [
        b"PROBE1|OK|11",
        b"G|X|1",
        b"G|main|<function#1>",
        b"I|main",
        b"C|engine.Init|0|",
        b"C|engine.GetCount|0|",
        b'P|hello\t0',
        b'C|engine.Draw|2|1,"cg1"',
        b'C|engine.Draw|2|2,"cg2"',
        b'C|engine.Draw|2|3,"cg3"',
        b"C|engine.IsDone|0|",
        b"R|main|ok",
        b"",
    ]


def test_stub_return_policy_is_the_frozen_one():
    """`nil` by default, with the name heuristic in front of it. Measured this
    session over the corpus: this policy and a bare always-nil both give
    227/229 agreement, while always-zero and the predecessor's zero-defaulted
    guess give 226/229 (they surface one extra instance of the same pinned
    getobjname class in snr_common.lua). The policy is frozen, not tuned."""
    t = _probe_src(b"""
function main()
  sink(IsThing(), thingCount(), thingIndex(), thingNum(), curTime(),
       fileName(), curScene(), pressButtonA(), sceneOf(), anythingElse())
end
""")
    # ...and the last two show the default: the heuristic is a plain,
    # case-sensitive substring test, so `sceneOf` does NOT match "Scene" and
    # falls through to nil exactly like an unrecognised name.
    assert (b'C|sink|10|false,0,0,0,0,"stub","stub",false,nil,nil'
            in _lines(t))


def test_stub_proxy_survives_indexing_and_arithmetic():
    """An unknown global must be indexable and arithmetic-tolerant, otherwise
    execution stops at the first missing engine symbol and the trace is a
    single line. This is what buys the reach.

    One case per metamethod the proxy defines, so none of them is unfalsifiable
    surface: without the corresponding entry this chunk raises instead of
    recording a call.
    """
    t = _probe_src(b"""
function main()
  local s = systemSave
  sink(s.memoryFlag.deep, -s.n, s.a + 1, s.b - 1, s.c * 2, s.d / 2,
       s.e % 2, s.f ^ 2, "x" .. s.g, s.h < s.i, s.j <= s.k)
end
""")
    assert (b'C|sink|11|@systemSave.memoryFlag.deep,0,0,0,0,0,0,0,'
            b'"x@systemSave.g",false,false' in _lines(t))


# --------------------------------------------------------------------------
# Non-vacuity of the instrument itself
# --------------------------------------------------------------------------

def test_probe_raises_instead_of_returning_a_comparable_blank(tmp_path):
    """A probe-side failure must never become a value that compares equal.

    The L1.5 probe shipped once with every failure path returning "": a chunk
    calling os.exit(3), a chunk that blinded the probe, even pointing the
    driver at a probe file that does not exist, all produced "" on both sides,
    so the whole 229-file gate passed while comparing nothing at all.
    """
    from pathlib import Path

    import scripts.probe_behaviour as pb

    missing = tmp_path / "nope.lua"
    old = pb.PROBE
    pb.PROBE = missing
    try:
        with pytest.raises(pb.ProbeError):
            _probe_src(b"X = 1")
    finally:
        pb.PROBE = Path(old)


def test_target_cannot_truncate_the_probe_with_os_exit():
    """`os.exit` in the target would end the process with status 0 and a
    partial trace on stdout -- which would compare equal to any other target
    that exits at the same point, and would not even look like a failure."""
    from scripts.probe_behaviour import header
    t = _probe_src(b"function main() sink(1) os.exit(0) sink(2) end")
    assert header(t)[0] == "OK"
    assert b"R|main|OSEXIT" in _lines(t)
    assert b"C|sink|1|1" in _lines(t)
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
    """Every one of these leaks wall-clock time, an RNG, a heap address, a
    fresh temp path or the host environment into the trace, and a trace that
    differs run to run is a gate that cannot fail for a real reason. The corpus
    was measured not to call any of them, which is exactly why they need
    synthetic cover: without it these overrides would be unfalsifiable.

    The assertion is the EXACT frozen value, not "two runs agree". That
    distinction is load-bearing and was found the hard way: with a two-run
    check, deleting the os.time, math.random and collectgarbage overrides left
    this test green (two runs a few milliseconds apart see the same second, the
    same libc rand() default seed, and the same allocation total), so three of
    the five guards were unfalsifiable. Deleting any one of them now fails the
    corresponding case.
    """
    src = b"function main() " + snippet + b" end"
    assert expected in _lines(_probe_src(src))


def test_target_stdout_becomes_events_instead_of_corrupting_the_trace():
    """The trace IS the probe's stdout. A chunk that prints or io.writes would
    otherwise interleave arbitrary bytes -- including newlines -- into it, and
    the result would still parse as a trace."""
    t = _probe_src(b"function main() io.write('raw\\n') print('p', 2) end")
    assert _lines(t) == [b"PROBE1|OK|5", b"G|main|<function#1>", b"I|main",
                         b"W|raw\\n", b"P|p\t2", b"R|main|ok", b""]


def test_budget_is_an_event_count_not_an_instruction_count():
    """The load-bearing design constraint, measured at feasibility: an
    instruction budget alone drops agreement from 226/229 to 95/229 because two
    representations of the same program execute a different number of VM
    instructions and get truncated at different points. Re-measured this
    session on the real corpus: at the same 3000-event cap, snr_s4_10_s.lua's
    decompiled side executes 78.35M VM instructions against the original's
    6.51M -- a 12x ratio -- and still produces a byte-identical trace.

    Here the same effect in miniature: two chunks with identical observable
    behaviour and wildly different instruction counts must produce identical
    traces.
    """
    from scripts.probe_behaviour import header
    lean = b"function main() while true do tick() end end"
    fat = (b"function main() local q = 0 "
           b"while true do for i = 1, 500 do q = q + i end tick() end end")
    a, b = _probe_src(lean), _probe_src(fat)
    assert header(a) == header(b) == ("CAP", 3001)
    assert a == b


def test_instruction_backstop_stops_a_loop_that_records_nothing():
    """The event budget cannot see a loop that never records an event. Without
    the backstop this run does not terminate."""
    from scripts.probe_behaviour import header
    t = _probe_src(b"function main() local x = 0 while true do x = x + 1 end end")
    assert header(t) == ("INSN", 3)
    assert b"R|main|INSN" in _lines(t)


def test_probe_result_is_never_silently_decoded():
    """The trace embeds corpus string constants verbatim, and the corpus is
    Japanese game text that is frequently not UTF-8. The comparison unit is
    bytes; nothing in the gate path decodes them."""
    from scripts.probe_behaviour import digest, probe_raw
    raw = b'function main() sink("\x93\xfa\x96{\x8c\xea") end'
    t = probe_raw(raw, is_source=True)
    assert isinstance(t, bytes)
    assert b'C|sink|1|"\x93\xfa\x96{\x8c\xea"' in _lines(t)
    assert digest(t) == hashlib.sha256(t).hexdigest()


def test_pin_adjudication_is_two_directional():
    """A pin that converged, a pin whose evidence moved, and an unpinned
    divergence must each fail; only an exactly-matching pin passes."""
    pinned = {"a.lua": ("O", "D")}
    assert adjudicate_pins({"a.lua": ("O", "D")}, pinned) == ([], [], [])
    assert adjudicate_pins({}, pinned) == ([], [], ["a.lua"])
    assert adjudicate_pins({"a.lua": ("O", "D2")}, pinned) == ([], ["a.lua"], [])
    assert adjudicate_pins({"a.lua": ("O", "D"), "b.lua": ("x", "y")},
                           pinned) == (["b.lua"], [], [])


# --------------------------------------------------------------------------
# The corpus gate
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def behaviour_traces(corpus_dir, decompiled):
    """`{name: (original_trace, decompiled_trace)}` for all 229 corpus files.

    458 probe subprocesses, measured this session at 3.14s serially and 1.06s
    across 8 threads on this machine; the probes are independent processes, so
    the threads only wait. Built once for the whole module -- three tests below
    consume it. The decompiled sources come from conftest's session-scoped
    `decompiled` cache (~8.6s for the corpus), which test_corpus_compile.py has
    normally already paid; this gate never re-walks the corpus itself.
    """
    from scripts.probe_behaviour import probe_raw
    files = sorted(corpus_dir.glob("*.lua"))
    work = [(f, decompiled(f).source) for f in files]

    def one(item):
        f, src = item
        return (f.name, probe_raw(f.read_bytes(), is_source=False),
                probe_raw(src, is_source=True))

    with ThreadPoolExecutor(max_workers=8) as ex:
        return {n: (o, d) for n, o, d in ex.map(one, work)}


def test_corpus_behaviour_matches(behaviour_traces, tmp_path):
    """Original bytecode and decompiled output must make the same engine calls.

    Measured 2026-08-12: 227/229 byte-identical, 2 pinned. Pins are exact
    (original, decompiled) first-differing-line pairs compared two-
    directionally, so a changed message, a converged pair or a vanished file
    all fail -- see EXPECTED_DIVERGENCE for the instruction-level evidence
    behind each.
    """
    from scripts.probe_behaviour import dump_mismatch, first_difference
    assert len(behaviour_traces) == 229
    divergent = {n: first_difference(o, d)[1:]
                 for n, (o, d) in behaviour_traces.items() if o != d}
    unexpected, moved, gone = adjudicate_pins(divergent, EXPECTED_DIVERGENCE)
    for n in unexpected + moved:
        dump_mismatch(n, *behaviour_traces[n], tmp_path)
    assert unexpected == [], (
        f"{len(unexpected)} file(s) diverge behaviourally and are not pinned: "
        f"{unexpected[:5]}; full traces written to {tmp_path}. Adjudicate each "
        "with instruction-level evidence before pinning it.")
    assert moved == [], (
        f"pinned divergence(s) {moved} no longer match their recorded "
        f"evidence; traces in {tmp_path}. Re-derive the pin.")
    assert gone == [], (
        f"pinned divergence(s) {gone} converged or vanished -- delete the "
        "entry, do not leave a pin that can no longer fail.")


def test_pinned_divergences_are_only_what_they_are_claimed_to_be(behaviour_traces):
    """The adjudication above is a claim about *why* each pin diverges. Assert
    the claims, so they cannot quietly become wrong:

    * snr_mainmenu -- exactly one differing line, and everything before it is
      identical, i.e. both sides made the same 18 engine calls and then both
      failed with the same operation on the same nil; only getobjname's noun
      differs (`field 'library'` vs `field '?'`, the __pld_R box model).
    * snr_novel -- the two traces are the same MULTISET of lines, i.e. the same
      calls with the same arguments in a different order: table iteration
      order, not a behavioural difference.
    """
    o, d = behaviour_traces["snr_mainmenu.lua"]
    lo, ld = _lines(o), _lines(d)
    assert len(lo) == len(ld)
    assert sum(1 for a, b in zip(lo, ld) if a != b) == 1
    assert b"attempt to perform arithmetic" in lo[-2]
    assert b"attempt to perform arithmetic" in ld[-2]

    o, d = behaviour_traces["snr_novel.lua"]
    assert o != d
    assert collections.Counter(_lines(o)) == collections.Counter(_lines(d))


def test_corpus_reach_is_not_vacuous(behaviour_traces):
    """The gate must not be passing because both sides observed nothing.

    Re-measured 2026-08-12 against the L1.5 gate it deepens:

    | measure                       | L1.5    | L1.75      |
    | ----------------------------- | ------- | ---------- |
    | files with a non-empty payload| 224/229 | 229/229    |
    | compared units                | 452     | 398,196    |
    |                               | globals | events     |
    | payload, median               | 22 B    | 33,068 B   |
    | payload, total                | ~65 KB  | 13.6 MB    |

    The thresholds below are deliberately far under the measurements so that
    normal drift does not fail them, but a collapse of the instrument does.
    """
    from scripts.probe_behaviour import header
    statuses = collections.Counter()
    events = 0
    for name, (o, d) in behaviour_traces.items():
        st, n = header(o)
        statuses[st] += 1
        assert n > 0, f"{name}: original side recorded no events at all"
        assert header(d)[1] > 0, f"{name}: decompiled side recorded no events"
        events += n
    assert statuses["LOADFAIL"] == 0
    assert statuses["INSN"] == 0, (
        "a corpus file hit the 400M-instruction backstop; the event budget is "
        "supposed to bind first, so this is a reach regression to explain")
    assert events > 300_000, (
        f"only {events} events recorded across the corpus; the deep probe's "
        "reach has collapsed towards the shallow gate's 452 globals")
    # Two-thirds of the files run into the event cap: that is the reach
    # ceiling, recorded so a change in it is visible rather than silent.
    assert statuses["CAP"] > 100


# --------------------------------------------------------------------------
# Fault injection: the gate must fail when the decompiler is wrong
# --------------------------------------------------------------------------

def _injected(corpus_dir, decompiled, name, anchor, replacement):
    """Probe an original corpus file and its decompiled source, plus a
    deliberately corrupted copy of that source. Returns (original, mutated)."""
    from scripts.probe_behaviour import probe_raw
    f = corpus_dir / name
    src = decompiled(f).source
    assert src.count(anchor) == 1, (
        f"injection anchor {anchor!r} is no longer unique in {name}'s emitted "
        "source (count="
        f"{src.count(anchor)}); re-derive it -- an anchor that matches nothing "
        "would make this test pass without injecting anything")
    orig = probe_raw(f.read_bytes(), is_source=False)
    assert probe_raw(src, is_source=True) == orig, (
        f"{name} does not agree before injection; fix that first")
    return orig, probe_raw(src.replace(anchor, replacement), is_source=True)


def test_injected_arithmetic_swap_is_caught(corpus_dir, decompiled):
    """Swap one `+` for a `-` in the emitted source of a real corpus file --
    the smallest possible decompiler defect -- and require the gate to notice.
    snr_crd_10.lua ships structured (certified L3) source, so this exercises
    the majority path: 212 of 229 files ship structured output."""
    orig, mutated = _injected(
        corpus_dir, decompiled, "snr_crd_10.lua",
        b"\n    l1_1 = l1_1 + 1\n", b"\n    l1_1 = l1_1 - 1\n")
    assert mutated != orig


def test_injected_loop_bound_is_caught(corpus_dir, decompiled):
    """Move a `while` loop's bound by one in the emitted source of a
    structured corpus file and require the gate to notice. M4 structures
    `while`/`repeat`; no corpus file's structured output contains a numeric
    `for` (measured this session: 0 occurrences across all 212 structured
    files), so the FORLOOP form of this injection is the fallback test
    below."""
    orig, mutated = _injected(
        corpus_dir, decompiled, "snr_crd_10.lua",
        b"\nwhile l1_0 < 1 do\n", b"\nwhile l1_0 < 0 do\n")
    assert mutated != orig


def test_injected_forloop_bound_is_caught(corpus_dir, decompiled):
    """The same injection against the FORLOOP the fallback emitter writes out
    by hand: turn `__pld_i <= limit` into `__pld_i < limit`, i.e. run the loop
    one iteration short. snr_memory.lua is one of the 17 files still shipping
    fallback, so the floor is covered as well as the structured path."""
    orig, mutated = _injected(
        corpus_dir, decompiled, "snr_memory.lua",
        b"\nif (__pld_s > 0 and __pld_i <= __pld_R[5]) or "
        b"(__pld_s <= 0 and __pld_i >= __pld_R[5]) then\n",
        b"\nif (__pld_s > 0 and __pld_i < __pld_R[5]) or "
        b"(__pld_s <= 0 and __pld_i >= __pld_R[5]) then\n")
    assert mutated != orig


def test_probe_is_deterministic_across_separate_processes(corpus_dir, decompiled):
    """Every probe run is its own OS process, so this is a real cross-process
    check, not a same-process replay. Measured this session over all 229 files
    x both sides x three whole-corpus runs in three separate Python processes:
    458/458 digests identical every time. Here a cheap sample of the same
    property, on files chosen for the features that would leak (a `pairs` loop,
    the biggest file, and a table-heavy one)."""
    from scripts.probe_behaviour import digest, probe_raw
    for name in ("snr_novel.lua", "snr_common.lua", "snr_graphic.lua"):
        f = corpus_dir / name
        bc = f.read_bytes()
        src = decompiled(f).source
        assert digest(probe_raw(bc, is_source=False)) == \
            digest(probe_raw(bc, is_source=False))
        assert digest(probe_raw(src, is_source=True)) == \
            digest(probe_raw(src, is_source=True))

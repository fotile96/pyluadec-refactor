"""L1.5 gate: compare observable global-table state between original bytecode
and decompiled output, without the game engine.

See docs/runbooks/m3-backlog.md item 3 ("Global-state probe") for the probe
design, its measured reach, and the known incomparable dimension recorded in
`EXPECTED_ERROR_NAME_DIVERGENCE` below.
"""
import pytest

# The pin itself lives next to the CLI that has to honour it
# (scripts/probe_global_state.py), so the gate and the documented script cannot
# disagree about what is pinned; see the comment there for the getobjname
# argument and the instruction-level evidence.
from scripts.probe_global_state import EXPECTED_ERROR_NAME_DIVERGENCE


def test_probe_is_deterministic():
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    bc = oracle.compile_source(b"X = {b = 2, a = 1} Y = 'hi' Z = 3.5")
    a = probe(bc, is_source=False)
    b = probe(bc, is_source=False)
    assert a == b


def test_probe_serialises_every_assigned_global():
    from pyluadec import oracle
    from scripts.probe_global_state import probe, payload_of
    a = probe(oracle.compile_source(b"X = {b = 2, a = 1} Y = 'hi' Z = 3.5"),
              is_source=False)
    assert a.startswith("OK|")
    # Full-line matching, not `"X=" in a`: a substring test also matches a
    # value that happens to contain "X=" and says nothing about the value.
    assert sorted(payload_of(a).splitlines()) == [
        "string:X={string:a=1,string:b=2}", "string:Y=hi", "string:Z=3.5"]


def test_probe_detects_a_difference():
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    a = probe(oracle.compile_source(b"X = 1"), is_source=False)
    b = probe(oracle.compile_source(b"X = 2"), is_source=False)
    assert a != b


def test_probe_raises_instead_of_returning_a_comparable_blank(tmp_path):
    """A probe-side failure must never become a value that compares equal.

    Before this was fixed, every failure path returned "": a chunk calling
    os.exit(3), a chunk that blinded the probe, even pointing PROBE at a file
    that does not exist, all produced "" on both sides and the whole
    229-file corpus gate passed while comparing nothing at all.
    """
    from pathlib import Path

    from pyluadec import oracle
    import scripts.probe_global_state as psg

    bc = oracle.compile_source(b"A = 1 os.exit(3)")
    with pytest.raises(psg.ProbeError) as e:
        psg.probe(bc, is_source=False)
    assert "exited 3" in str(e.value)

    missing = tmp_path / "nope.lua"
    old = psg.PROBE
    psg.PROBE = missing
    try:
        with pytest.raises(psg.ProbeError):
            psg.probe(oracle.compile_source(b"X = 1"), is_source=False)
    finally:
        psg.PROBE = Path(old)


def test_probe_distinguishes_different_runtime_errors():
    """`ERR|` alone collapses every failure into one constant."""
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    a = probe(oracle.compile_source(b"nosuchfn()"), is_source=False)
    b = probe(oracle.compile_source(b"local t = nil t.x = 1"), is_source=False)
    assert a.startswith("ERR|") and b.startswith("ERR|")
    assert a != b
    # The source:line: prefix is stripped, the message itself is kept.
    assert "attempt to call global 'nosuchfn'" in a
    assert "attempt to index local 't'" in b


def test_probe_error_location_prefix_is_stripped_across_source_and_bytecode():
    """The same failing program must give the same ERR text whether it is fed
    in as .lua source or as compiled (and stripped) bytecode -- the
    `<source>:<line>: ` prefix differs there and must not be compared."""
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    src = b"\n\n\nX = 1\nnosuchfn()"
    a = probe(src, is_source=True)
    b = probe(oracle.compile_source(src), is_source=False)
    c = probe(oracle.compile_source(src, strip=True), is_source=False)
    assert a == b == c
    assert a.startswith("ERR|attempt to call global 'nosuchfn' (a nil value)|")


def test_probe_distinguishes_different_load_failures():
    from scripts.probe_global_state import probe
    a = probe(b"X = = 1", is_source=True)
    b = probe(b"if true then", is_source=True)
    assert a.startswith("LOADFAIL|") and b.startswith("LOADFAIL|")
    assert a != b


def test_probe_does_not_collapse_keys_with_equal_tostring():
    """The number 1 and the string "1" are different table keys.

    Keying the serialisation on tostring(k) alone dropped one of them and
    emitted the other twice, so these two genuinely different tables both
    serialised as `X={1=A,1=A}` -- a false pass on exactly the numeric keys
    the corpus uses (`cardSort={1={1=1},10={1=106},...}`).
    """
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    a = probe(oracle.compile_source(b'X = {} X[1] = "A" X["1"] = "B"'), is_source=False)
    b = probe(oracle.compile_source(b'X = {} X[1] = "A" X["1"] = "C"'), is_source=False)
    assert a != b
    assert "number:1=A" in a and "string:1=B" in a


@pytest.mark.parametrize("clobber", ["tostring", "pairs", "ipairs", "type",
                                     "print", "table", "string"])
def test_target_chunk_cannot_blind_the_probe(clobber):
    """A chunk that nils out a name the probe uses must not silence it."""
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    a = probe(oracle.compile_source(b"A = 1 " + clobber.encode() + b" = nil"), is_source=False)
    b = probe(oracle.compile_source(b"A = 2 " + clobber.encode() + b" = nil"), is_source=False)
    assert a == "OK|string:A=1\n" and b == "OK|string:A=2\n"


def test_corpus_global_state_matches(corpus_dir, decompiled):
    """Original bytecode and decompiled output must produce identical global state."""
    from scripts.probe_common import adjudicate_pins
    from scripts.probe_global_state import probe, payload_of
    divergent = {}
    nonempty = 0
    files = sorted(corpus_dir.glob("*.lua"))
    for f in files:
        orig = probe(f.read_bytes(), is_source=False)
        dec = probe(decompiled(f).source, is_source=True)
        if orig != dec:
            divergent[f.name] = (orig, dec)
        if orig.startswith("OK|") and payload_of(orig):
            nonempty += 1
    assert len(files) == 229
    # `adjudicate_pins`, not a second hand-rolled implementation of it. This
    # test used to build `bad` / `pinned_seen` itself and compare the latter to
    # the table -- equivalent today, but it is the SAME rule the CLI applies
    # and `probe_common`'s whole reason for existing is that the two must not
    # be able to drift (M6 final review, item 19).
    unexpected, moved, gone = adjudicate_pins(
        divergent, EXPECTED_ERROR_NAME_DIVERGENCE)
    assert unexpected == [], (
        f"{len(unexpected)} file(s) diverge and are not pinned: "
        f"{[(n, divergent[n][0][:200], divergent[n][1][:200]) for n in unexpected[:3]]}")
    assert moved == [], (
        f"pinned getobjname-name divergence(s) {moved} no longer match their "
        "recorded evidence; re-derive the pin")
    assert gone == [], (
        f"pinned divergence(s) {gone} converged or vanished -- delete the "
        "entry, do not leave a pin that can no longer fail")
    # Non-vacuity: the gate must not be passing because both sides produce
    # nothing. A bare marker with an empty payload does NOT count, and a
    # probe-side failure can no longer produce a comparable value at all
    # (probe() raises). 224/229 corpus files write at least one global; the
    # other 5 error before their first global write.
    assert nonempty > 200, (
        f"only {nonempty}/229 corpus files produced a non-empty global-state "
        "payload; the comparison may be trivially vacuous")


def test_corpus_probe_detects_a_value_mutation(corpus_dir, decompiled):
    """Sensitivity on the real gate path: decompile_file -> probe -> compare.

    Everything else in this file exercises probe() on synthetic snippets.
    This mutates a numeric literal in an actual corpus file's decompiled
    source and requires the gate to notice. One file only -- it must stay
    fast.
    """
    from scripts.probe_global_state import probe
    src = decompiled(corpus_dir / "snr_common.lua").source
    anchor = b"__pld_R[0] = 195"           # feeds `myCardMax` and a for-limit
    assert src.count(anchor) == 1, (
        "sensitivity anchor no longer unique in snr_common.lua's emitted "
        "source; re-derive it from a top-level numeric literal that reaches "
        "a global (the probe only observes globals the chunk writes)")
    orig = probe((corpus_dir / "snr_common.lua").read_bytes(), is_source=False)
    mutated = probe(src.replace(anchor, b"__pld_R[0] = 196"), is_source=True)
    assert probe(src, is_source=True) == orig
    assert mutated != orig
    assert "string:myCardMax=196" in mutated


def test_corpus_probe_detects_a_different_error(corpus_dir, decompiled):
    """The ERR| text must discriminate on corpus content, not just synthetics.

    config.lua is one of the 5 corpus files that error before writing any
    global; with a bare `ERR|` marker its comparison held unconditionally.
    Inject a *different* failure into the decompiled source and require the
    gate to notice.
    """
    from scripts.probe_global_state import probe
    f = corpus_dir / "config.lua"
    orig = probe(f.read_bytes(), is_source=False)
    src = decompiled(f).source
    assert orig.startswith("ERR|table index is nil|")
    assert probe(src, is_source=True) == orig
    injected = probe(b"__pld_no_such_function_zz()\n" + src, is_source=True)
    assert injected != orig
    assert injected.startswith(
        "ERR|attempt to call global '__pld_no_such_function_zz' (a nil value)|")

"""L1.5 gate: compare observable global-table state between original bytecode
and decompiled output, without the game engine.

See docs/runbooks/m3-backlog.md item 3 ("Global-state probe") for the probe
design and the Phase 2 final-review results this test promotes into a
standing gate.
"""


def test_probe_is_deterministic_and_nonempty(tmp_path):
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    bc = oracle.compile_source(b"X = {b = 2, a = 1} Y = 'hi' Z = 3.5")
    a = probe(bc, is_source=False)
    b = probe(bc, is_source=False)
    assert a == b and a.startswith("OK|") and "X=" in a and "Y=" in a


def test_probe_detects_a_difference():
    from pyluadec import oracle
    from scripts.probe_global_state import probe
    a = probe(oracle.compile_source(b"X = 1"), is_source=False)
    b = probe(oracle.compile_source(b"X = 2"), is_source=False)
    assert a != b


def test_corpus_global_state_matches(corpus_dir):
    """Original bytecode and decompiled output must produce identical global state."""
    from pyluadec.pipeline import decompile_file
    from scripts.probe_global_state import probe
    bad = []
    nonempty = 0
    files = sorted(corpus_dir.glob("*.lua"))
    for f in files:
        orig = probe(f.read_bytes(), is_source=False)
        dec = probe(decompile_file(f).source, is_source=True)
        if orig != dec:
            bad.append(f.name)
        if orig.strip() not in ("OK|", "ERR|"):
            nonempty += 1
    assert len(files) == 229
    assert bad == [], f"{len(bad)} files diverge: {bad[:5]}"
    # Non-vacuity: the comparison must not be trivially passing because both
    # sides produce empty global-state output. Phase 2 final review found
    # none of the 229 files trivially empty; guard that property here too.
    assert nonempty > 200, (
        f"only {nonempty}/229 corpus files produced non-empty global state; "
        "the comparison may be trivially vacuous")

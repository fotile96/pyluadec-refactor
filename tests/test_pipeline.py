def test_decompile_chunk_confesses_per_proto():
    """Confessions are keyed by proto path, one well-formed record per proto
    that did not certify.

    Since M3 task 8 a proto that certified L3 confesses NOTHING (its structured
    print is machine-checked against the original), so this no longer asserts
    that every path confesses -- see tests/test_pipeline_structured.py for the
    level/confession coupling itself. What is still pinned here: every proto in
    the tree gets an entry, and any confession that IS recorded has the M2
    reason and a sane pc range. The input is deliberately left UNSTRIPPED,
    which is also the regression pin for the debug-completeness assertion
    removed in M3 task 8 (it used to fire on exactly this source, because
    `function() return 1 end` declares no locals).
    """
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(
        b"local f = function() return 1 end local g = function() return 2 end print(f(), g())")
    res = decompile_chunk(load_bytes(bc))
    assert set(res.confessions_by_proto) == {"main", "main_0", "main_1"}
    assert set(res.levels) == {"main", "main_0", "main_1"}
    for path, confs in res.confessions_by_proto.items():
        assert (confs == []) == (res.levels[path] == "L3")
        for c in confs:
            assert c["reason"] == "fallback-state-machine"
            assert c["pc_lo"] == 1 and c["pc_hi"] >= 1
    oracle.compile_source(res.source)      # 产物可编译


def test_decompile_file(tmp_path):
    from pyluadec import oracle
    from pyluadec.pipeline import decompile_file
    src = tmp_path / "x.lua"
    src.write_bytes(oracle.compile_source(b'print("file path entry")'))
    res = decompile_file(src)
    r = oracle.run_bytes(res.source, is_source=True)
    assert r.stdout == b"file path entry\n"

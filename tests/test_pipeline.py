def test_decompile_chunk_confesses_per_proto():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.pipeline import decompile_chunk
    bc = oracle.compile_source(
        b"local f = function() return 1 end local g = function() return 2 end print(f(), g())")
    res = decompile_chunk(load_bytes(bc))
    assert set(res.confessions_by_proto) == {"main", "main_0", "main_1"}
    for path, confs in res.confessions_by_proto.items():
        assert confs[0]["reason"] == "fallback-state-machine"
        assert confs[0]["pc_lo"] == 1 and confs[0]["pc_hi"] >= 1
    oracle.compile_source(res.source)      # 产物可编译


def test_decompile_file(tmp_path):
    from pyluadec import oracle
    from pyluadec.pipeline import decompile_file
    src = tmp_path / "x.lua"
    src.write_bytes(oracle.compile_source(b'print("file path entry")'))
    res = decompile_file(src)
    r = oracle.run_bytes(res.source, is_source=True)
    assert r.stdout == b"file path entry\n"

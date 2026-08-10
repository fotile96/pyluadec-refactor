import json

def test_parse_header_sz4(compile_lua):
    from pyluadec.ingest.header import parse_header
    h = parse_header(compile_lua("luac_sz4", "return 1").read_bytes())
    assert h.version == 0x51 and h.sizeof_sizet == 4 and h.little_endian

def test_dispatch_by_header(compile_lua):
    from pyluadec.ingest import load_file
    p4 = load_file(compile_lua("luac_sz4", "local x=1 return x"))
    assert p4.maxstacksize >= 2 and p4.locvars[0].name == b"x"
    p8 = load_file(compile_lua("luac_sz8", "local x=1 return x"))
    assert p8.code == p4.code            # 同源同指令流，与序列化宽度无关

def test_canonical_dump_is_json_and_stable(compile_lua):
    from pyluadec.ingest import load_file
    from pyluadec.ingest.proto import to_canonical
    p = load_file(compile_lua("luac_sz4", 'return "\\255", 0.5'))
    c1 = json.dumps(to_canonical(p), sort_keys=True)
    c2 = json.dumps(to_canonical(load_file(compile_lua("luac_sz4", 'return "\\255", 0.5'))), sort_keys=True)
    assert c1 == c2
    assert "ff" in c1                    # bytes as hex

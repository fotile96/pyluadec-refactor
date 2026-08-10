STRAIGHT_LINE_CASES = [
    # 操作数放局部变量：常量间算术会被 luac 编译期折叠，发不出 ADD/MUL/POW/... opcode
    'local a = 2 local b = 3.5 print(a + b, a * b, a ^ b, a % b, a / b, a - b)',
    'local a = "x" print(a .. "y" .. 1 .. 2)',
    'local t = {} t.k = 3 t[1] = "v" print(t.k, t[1], #t)',
    'local s = "abc" local k = 3 print(#s, not s, -k)',      # LEN/NOT/UNM 须走寄存器
    'x_global = 42 print(x_global + 1)',
    'local a, b, c = 1 print(a, b, c)',
    # SELF 语料未用到，须靠合成用例覆盖；结果先落 local 再传参，避免方法调用
    # 落在实参尾位触发 open-result/open-arg CALL（B=0/C=0，Task 7 才支持）。
    'local s = "na" local r = s:rep(4) print(r)',
    'local f = print f("via register call")',
    'print(true, false, nil)',
    'local t = {} t["\\001k"] = "bin" print(t["\\001k"])',
    'print("ab\\255\\001cd")',
    # 非可打印字节后紧跟数字字符：定长 \%03d 转义下 \001 后的 '2' 不会被
    # 吞并；若发射器错用变长转义（\%d），"\0012" 会被重新解析成 "\12"
    # （单字节 12），与原始 2 字节内容不同——专为捕获该类 off-by-format 而设。
    'print("\\0012")',
]


def test_straightline_cases():
    from tests.diffexec import assert_fallback_roundtrip
    for src in STRAIGHT_LINE_CASES:
        assert_fallback_roundtrip(src)


def test_stripped_input_also_works():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import emit_chunk
    bc = oracle.compile_source(b'print("stripped")', strip=True)   # 语料同款 -s
    r = oracle.run_bytes(emit_chunk(load_bytes(bc)), is_source=True)
    assert r.stdout == b"stripped\n"


def test_emitted_source_compiles():
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.fallback import emit_chunk
    bc = oracle.compile_source(b"local x = 1 + 2 return x")
    oracle.compile_source(emit_chunk(load_bytes(bc)))              # 不抛即过

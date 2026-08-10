def _bc(src: str):
    from pyluadec import oracle
    from pyluadec.ingest import load_bytes
    return load_bytes(oracle.compile_source(src.encode()), chunkname="=t")


def test_structural_hash_ignores_debug_but_not_structure():
    from pyluadec.verify.ledger import structural_hash
    a = _bc("print(1)")
    b = _bc("\n\nprint(1)")                 # 只差行号布局
    c = _bc("print(2)")                     # 常量不同
    assert structural_hash(a) == structural_hash(b)
    assert structural_hash(a) != structural_hash(c)


def test_structural_hash_dedups_identical_functions_across_chunks():
    from pyluadec.verify.ledger import structural_hash
    a = _bc("local f = function(x) return x + 1 end return f")
    b = _bc("local g = function(y) return y + 1 end return g")
    # 子函数字节码同构（寄存器/常量布局一致）→ 同哈希；外层 chunk 常量名不同不影响子哈希
    assert structural_hash(a.subprotos[0]) == structural_hash(b.subprotos[0])


def test_payload_distinction():
    from pyluadec.verify.ledger import structural_hash
    assert structural_hash(_bc("return 0.0")) != structural_hash(_bc("return -0.0"))


def test_payload_distinction_nan_bitpatterns():
    # Two distinct NaN bit patterns both repr/json as the same float value
    # ("nan"), so a .value-based hash would collide them even though they
    # are bit-distinct payloads (spec: numeric constants bit-exact, not
    # float-value-exact). This is a sharper discriminator than 0.0 vs -0.0:
    # that pair happens to still differ under json.dumps(float) because
    # Python's float repr preserves the sign of zero, so a .value-based
    # hash accidentally still separates them. NaN payloads do not get that
    # accidental protection.
    import struct
    from pyluadec.ingest.proto import LuaNumber, Proto
    from pyluadec.verify.ledger import structural_hash

    def mkproto(payload: bytes) -> Proto:
        return Proto(source=None, linedefined=0, lastlinedefined=0, nups=0,
                     numparams=0, is_vararg=0, maxstacksize=2, code=(1, 2, 3),
                     constants=(LuaNumber(value=struct.unpack("<d", payload)[0],
                                          payload=payload),),
                     lineinfo=(), locvars=(), upvalues=(), subprotos=())

    p1 = mkproto(bytes([0, 0, 0, 0, 0, 0, 0xf8, 0x7f]))
    p2 = mkproto(bytes([0, 0, 0, 0, 0, 0, 0xf8, 0xff]))
    assert struct.unpack("<d", p1.constants[0].payload)[0] != \
        struct.unpack("<d", p1.constants[0].payload)[0]  # sanity: it is NaN
    assert structural_hash(p1) != structural_hash(p2)


def test_structural_hash_recurses_into_subprotos():
    from pyluadec.verify.ledger import structural_hash
    # Outer functions are structurally identical at the top level; only the
    # nested closure's body differs (x + 1 vs x + 2). If structural_hash
    # ever stopped recursing into subprotos, these two outer functions would
    # collide despite being semantically different -- a false collision the
    # ratchet must never produce.
    a = _bc("local function outer() return function(x) return x + 1 end end return outer")
    b = _bc("local function outer() return function(x) return x + 2 end end return outer")
    assert structural_hash(a.subprotos[0]) != structural_hash(b.subprotos[0])


def test_ledger_roundtrip(tmp_path):
    from pyluadec.verify.ledger import LedgerEntry, read_ledger, write_ledger
    entries = [
        LedgerEntry(shash="ff" * 32, level="L1", l3_level=None, compile_ok=True,
                    fallback=True, n_insns=7,
                    confessions=[{"pc_lo": 1, "pc_hi": 7, "reason": "fallback-state-machine",
                                  "pass": "structure.fallback"}],
                    occurrences=[{"file": "a.lua", "proto_path": "main"}],
                    oracle="deadbeef", ladder="l3-ladder-v0"),
        LedgerEntry(shash="aa" * 32, level="L1", l3_level=None, compile_ok=True,
                    fallback=True, n_insns=3, confessions=[],
                    occurrences=[{"file": "b.lua", "proto_path": "main_0"}],
                    oracle="deadbeef", ladder="l3-ladder-v0"),
    ]
    p = tmp_path / "ledger.jsonl"
    write_ledger(entries, p)
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"shash": "aa')          # 按 shash 排序写出
    back = read_ledger(p)
    assert back == sorted(entries, key=lambda e: e.shash)


def test_oracle_version_is_hexish():
    from pyluadec.verify.ledger import oracle_version
    v = oracle_version()
    assert v == "unknown" or (len(v) == 40 and all(ch in "0123456789abcdef" for ch in v))

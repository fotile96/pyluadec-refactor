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


def _run_corpus_module():
    """scripts/run_corpus.py is a script, not a package module; load it the
    same way tests/test_ledger_ratchet.py does."""
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_corpus.py"
    spec = importlib.util.spec_from_file_location("run_corpus_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _entry(**kw):
    from pyluadec.verify.ledger import LedgerEntry
    base = dict(shash="ff" * 32, level="L3", l3_level=1, compile_ok=False,
                fallback=False, n_insns=9, confessions=[],
                occurrences=[{"file": "a.lua", "proto_path": "main_0"}],
                oracle="deadbeef", ladder="l3-ladder-v1")
    base.update(kw)
    return LedgerEntry(**base)


def test_forced_l0_entry_is_confessed():
    """A proto can certify L3 on its own while its FILE fails the whole-chunk
    compile check; the chunk is what ships, so the row is forced to L0. That
    path used to rewrite level/l3_level/fallback and keep `confessions`, which
    for an individually-L3 proto is `[]` -- so an L0 row could ship
    unconfessed, which "confess, don't guess" forbids and
    tests/test_m3_exit.py::test_non_l3_entries_confess would (loudly, and only
    after the fact) fail on.

    Load-bearing check: deleting `_force_l0`'s confession block makes this
    test fail on the `confessions` assertion; deleting its `refusal_reason`
    line makes it fail on the next one. Verified by neutering both,
    2026-08-11. Not reachable from the corpus today (229/229 files compile),
    which is exactly why it needs a unit test rather than a corpus run.
    """
    mod = _run_corpus_module()
    e = _entry()
    mod._force_l0(e)
    assert e.level == "L0" and e.l3_level is None and e.fallback is True
    assert [c["reason"] for c in e.confessions] == ["fallback-state-machine"]
    assert e.confessions[0]["pc_lo"] == 1 and e.confessions[0]["pc_hi"] == 9
    assert e.refusal_reason == "compile: shipped chunk did not compile"


def test_forced_l0_keeps_an_existing_confession():
    """The demotion must not overwrite a real confession with a synthetic
    whole-range one: a proto that was already L1 arrives here with the
    fallback state machine's own confession, and that is the more specific
    record of what shipped."""
    mod = _run_corpus_module()
    existing = [{"pc_lo": 1, "pc_hi": 9, "reason": "fallback-state-machine",
                 "pass": "structure.fallback"}]
    e = _entry(level="L1", l3_level=None, fallback=True, confessions=existing,
               refusal_reason="structure: pc 3: if targets out of range")
    mod._force_l0(e)
    assert e.confessions is existing
    assert e.refusal_reason == "compile: shipped chunk did not compile"

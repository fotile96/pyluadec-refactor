"""Static interaction-surface extraction (`lift/footprint.py`) + its dump CLI.

The measurement this file exists to protect is M6's Class-1 feasibility bet:
"even when a proto is not perfectly reconstructed, extracting WHICH table keys
it reads is easy, because those keys are string constants that are not built at
runtime". `Footprint.dynamic_reads` is the honesty counter that tests it, and
`test_corpus_headline_census` pins the corpus-wide answer so a future change
cannot move it silently.

Synthetic fixtures are compiled with the in-repo `luac_sz4` and are labelled as
such where they cover a shape the corpus cannot exercise -- notably `SELF`,
which is one of the five opcodes the 229-file corpus never emits.
"""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FOOTPRINTS = REPO_ROOT / "corpus" / "observation" / "footprints.json"


def _fp(src: str):
    """Compile `src` with the oracle, ingest it, lift the main chunk, and
    return its `Footprint`."""
    from pyluadec import ingest, oracle
    from pyluadec.lift import lift_proto
    from pyluadec.lift.footprint import proto_footprint
    root = ingest.load_bytes(oracle.compile_source(src.encode("ascii")),
                             chunkname="@t.lua")
    return proto_footprint(lift_proto(root))


# --------------------------------------------------------------------------
# Step 1 of the brief: the three shapes that define the extractor
# --------------------------------------------------------------------------

def test_constant_key_read_off_a_global_is_attributed():
    fp = _fp("local a = gameSave.startMenuState return a")
    assert (b"gameSave", b"startMenuState") in fp.table_key_reads
    assert b"gameSave" in fp.global_reads
    assert fp.dynamic_reads == 0
    assert fp.attributed_reads == 1
    assert fp.unattributed_reads == 0


def test_computed_key_read_counts_as_dynamic_and_lands_in_no_set():
    fp = _fp("local k = someKey() local b = tbl[k] return b")
    assert fp.dynamic_reads == 1
    assert fp.table_key_reads == frozenset()
    # the base global is still seen -- only the KEY is unknown
    assert b"tbl" in fp.global_reads


def test_self_attributes_both_the_key_and_the_call():
    """SYNTHETIC ONLY. `SELF` is one of the five opcodes the 229-file corpus
    never emits (CLAUDE.md / MEMORY.md's "the corpus is a weak oracle"), so
    nothing in `corpus/observation/footprints.json` exercises this path."""
    fp = _fp("local r = gameSave:save(1) return r")
    assert (b"gameSave", b"save") in fp.table_key_reads
    assert (b"gameSave", b"save") in fp.table_key_calls
    assert fp.table_key_call_sites == 1
    assert fp.calls == frozenset()          # no depth-1 global callee here


# --------------------------------------------------------------------------
# the rest of the surface
# --------------------------------------------------------------------------

def test_global_call_and_global_write():
    fp = _fp("setFlag(1) score = 2")
    assert fp.calls == frozenset({b"setFlag"})
    assert fp.global_call_sites == 1
    assert fp.global_writes == frozenset({b"score"})


def test_dotted_call_is_a_table_key_call_and_a_table_key_read():
    fp = _fp("local x = math.floor(1.5) return x")
    assert (b"math", b"floor") in fp.table_key_reads
    assert (b"math", b"floor") in fp.table_key_calls
    assert fp.calls == frozenset()


def test_constant_write_off_a_global_is_attributed():
    fp = _fp("gameSave.startMenuState = 3")
    assert (b"gameSave", b"startMenuState") in fp.table_key_writes
    assert fp.attributed_writes == 1
    assert fp.dynamic_writes == 0


def test_computed_key_write_counts_as_dynamic():
    fp = _fp("local k = someKey() tbl[k] = 1")
    assert fp.dynamic_writes == 1
    assert fp.table_key_writes == frozenset()


def test_numeric_constant_key_is_a_constant_but_not_a_string_key():
    """`arr[1]` is neither `dynamic_reads` (the key IS a constant) nor a
    `table_key_reads` member (that set is typed `(bytes, bytes)`). Without
    `nonstring_key_reads` those sites would vanish from the accounting."""
    fp = _fp("local x = arr[1] return x")
    assert fp.dynamic_reads == 0
    assert fp.nonstring_key_reads == 1
    assert fp.table_key_reads == frozenset()


def test_a_constant_key_that_could_not_fit_an_rk_operand_is_still_constant():
    """`lcode.c::luaK_exp2RK` falls back to a register for a `VK` operand whose
    constant index exceeds `MAXINDEXRK` (255), and for a `VKNUM` created once
    `fs->nk` already exceeds it. Both then look like `GETTABLE a b <register>`
    -- indistinguishable from a runtime-computed key unless the `LOADK` is
    tracked.

    This is not a hypothetical: `snr_common.lua`'s main chunk (920 constants)
    reported 209 of 209 reads as `dynamic_reads` before this was handled. The
    fixture pads the constant table past 255 and then does one numeric-key read
    and one long-index STRING-key read.
    """
    pad = ",".join(f"{i}.5" for i in range(300))
    fp = _fp(f"local pad = {{{pad}}}\n"
             "cardSort[1] = 2\n"
             "local v = cardSort[1]\n"
             'local w = cfg["deepKeyName"]\n'
             "return pad, v, w\n")
    assert fp.dynamic_reads == 0
    assert fp.dynamic_writes == 0
    assert fp.nonstring_key_reads == 1          # cardSort[1]
    assert fp.nonstring_key_writes == 1         # cardSort[1] = 2
    assert (b"cfg", b"deepKeyName") in fp.table_key_reads
    assert fp.register_const_key_reads == 2
    assert fp.register_const_key_writes == 1


def test_unattributed_read_when_the_base_is_not_a_global():
    """A table that arrives from a call result has no global provenance, so
    the read is counted but not attributed. This is the shape behind the
    corpus's `unattributed_reads`."""
    fp = _fp("local t = makeTable() local x = t.field return x")
    assert fp.unattributed_reads == 1
    assert fp.table_key_reads == frozenset()
    assert fp.read_sites == 1


def test_nested_read_attributes_only_the_depth_one_pair():
    """`a.b.c` yields `(a, b)` and then a depth-2 base for `c`. The pair set
    is `(base-global-name, key)`, so `(a, c)` would be a FALSE attribution --
    `c` is not a key of `a`. The deeper site is counted as unattributed."""
    fp = _fp("local x = conf.video.width return x")
    assert (b"conf", b"video") in fp.table_key_reads
    assert (b"conf", b"width") not in fp.table_key_reads
    assert fp.read_sites == 2
    assert fp.attributed_reads == 1
    assert fp.unattributed_reads == 1


def test_accounting_identities_hold_on_a_mixed_chunk():
    fp = _fp(
        "local k = someKey()\n"
        "local a = gameSave.startMenuState\n"
        "local b = tbl[k]\n"
        "local c = arr[1]\n"
        "gameSave.startMenuState = 3\n"
        "tbl[k] = 1\n"
        "arr[2] = 4\n"
        "setFlag(a, b, c)\n"
        "local d = math.floor(a)\n"
    )
    assert fp.read_sites == (fp.attributed_reads + fp.unattributed_reads
                             + fp.dynamic_reads + fp.nonstring_key_reads)
    assert fp.write_sites == (fp.attributed_writes + fp.unattributed_writes
                              + fp.dynamic_writes + fp.nonstring_key_writes)
    assert fp.call_sites == (fp.global_call_sites + fp.table_key_call_sites
                             + fp.unattributed_calls)


def test_footprint_is_frozen_and_hashable():
    fp = _fp("local a = g.k return a")
    with pytest.raises(Exception):
        fp.dynamic_reads = 5                                  # type: ignore[misc]
    assert isinstance(hash(fp), int)


# --------------------------------------------------------------------------
# guards, proven load-bearing (see the report for the neuter/restore runs)
# --------------------------------------------------------------------------

def test_a_non_string_global_name_never_reaches_the_pair_sets():
    """Hand-assembled `Proto` (NOT compiled -- `lparser.c` cannot emit this):
    `GETGLOBAL 0 0` where `K[0]` is a number, then `GETTABLE 0 0 K[1]`.

    The `isinstance(name, bytes)` guard in the GETGLOBAL arm is what keeps a
    `LuaNumber` out of `table_key_reads`, whose declared element type is
    `(bytes, bytes)`. Neuter it and this test fails with a non-bytes base in
    the set.
    """
    from pyluadec.ingest.proto import LuaNumber
    from pyluadec.lift import lift_proto
    from pyluadec.lift.footprint import proto_footprint

    p = _hand_proto(
        [_iABx(5, 0, 0),                     # GETGLOBAL R0, K0 (a number!)
         _iABC(6, 0, 0, 256 + 1),            # GETTABLE  R0, R0, K1
         _iABC(30, 0, 1, 0)],                # RETURN    R0, 1
        [LuaNumber(value=1.0, payload=b"\x00" * 8), b"field"])
    fp = proto_footprint(lift_proto(p))
    assert fp.global_reads == frozenset()
    assert fp.table_key_reads == frozenset()
    assert fp.unattributed_reads == 1
    assert all(isinstance(g, bytes) for g in fp.global_reads)


def _hand_proto(code, constants, maxstack=4):
    from pyluadec.ingest.proto import Proto
    return Proto(source=b"@x", linedefined=0, lastlinedefined=0, nups=0,
                 numparams=0, is_vararg=2, maxstacksize=maxstack, code=tuple(code),
                 constants=tuple(constants), lineinfo=(), locvars=(), upvalues=(),
                 subprotos=())


def _iABC(op, a, b, c):
    return op | (a << 6) | (c << 14) | (b << 23)


def _iABx(op, a, bx):
    return op | (a << 6) | (bx << 14)


def test_every_writes_open_window_starts_at_operand_a():
    """`footprint.py` drops provenance for registers `>= A` on `writes_open`.
    That is only correct if every instruction carrying the flag opens its
    window at `A`. Checked over the opcode x operand grid rather than assumed:
    the flag may appear on `CALL`/`TAILCALL`/`VARARG` only, and `lvm.c` gives
    all three a window of `R[A..top)`.
    """
    from pyluadec.lift.effects import EffectMode, analyze
    from pyluadec.lift.opcodes import Op, RawInstr

    carriers = set()
    for op in Op:
        for a in (0, 3):
            for b in (0, 1, 2, 256):
                for c in (0, 1, 2, 256):
                    ri = RawInstr(pc=1, word=0, op=op, a=a, b=b, c=c, bx=0, sbx=0)
                    if analyze(ri, EffectMode.STRICT).writes_open:
                        carriers.add(op)
    assert carriers == {Op.CALL, Op.TAILCALL, Op.VARARG}


def test_an_open_call_region_drops_provenance_at_and_above_a():
    """DEFENSIVE, and the corpus says so: with the `>= A` restriction in place,
    deleting this handling entirely changes **nothing** on all 229 files
    (measured 2026-08-13 -- byte-identical `footprints.json`). `lparser.c`
    never re-reads a multret call's result slot as a table base, so no
    luac-reachable shape exercises it.

    It is still a real correctness rule, so it gets a hand-assembled witness
    rather than a green tree and a shrug:

        GETGLOBAL R0, K"gg"
        CALL      R0 1 0        ; multret: R0 now holds gg's RESULT
        GETTABLE  R1, R0, K"k"

    Without the drop, `(gg, k)` is attributed -- a false claim about which
    table key this proto reads, which is precisely what Task 7 would enumerate
    over. Neuter the two `del` loops and this test fails.

    (The over-broad version -- clearing the WHOLE map instead of `>= A` -- is
    what the corpus *does* discriminate: it costs 3450 of 44812 call sites,
    because `h(g())` leaves `h`'s register below the inner call's window.)
    """
    from pyluadec.lift import lift_proto
    from pyluadec.lift.footprint import proto_footprint
    p = _hand_proto(
        [_iABx(5, 0, 0),                 # GETGLOBAL R0, K0 "gg"
         _iABC(28, 0, 1, 0),             # CALL      R0, 1, 0   (multret)
         _iABC(6, 1, 0, 256 + 1),        # GETTABLE  R1, R0, K1 "k"
         _iABC(30, 0, 1, 0)],            # RETURN    R0, 1
        [b"gg", b"k"])
    fp = proto_footprint(lift_proto(p))
    assert fp.global_reads == frozenset({b"gg"})
    assert fp.table_key_reads == frozenset()
    assert fp.unattributed_reads == 1
    # the CALL itself is correctly attributed -- R0 still holds `gg` when it
    # executes. Only the read AFTER it must not be.
    assert fp.calls == frozenset({b"gg"})
    assert fp.unattributed_calls == 0


def test_the_key_register_is_read_before_the_instructions_own_writes():
    """`GETTABLE A B C` with `A == C` is real luac output -- the key temp is
    freed and immediately reallocated as the destination:

        local t = {} ; local q = t[1]   (past 255 constants)
        -> LOADK R2, K"1" ; GETTABLE R2, R1, R2

    The `pre_kregs` snapshot is what keeps the `LOADK`'d constant readable at
    the site that consumes it; without it the key register is invalidated by
    this instruction's own write first and the site is miscounted as dynamic.
    """
    pad = ",".join(f"{i}.5" for i in range(300))
    fp = _fp(f"local pad = {{{pad}}}\nlocal t = {{}}\nlocal q = t[1]\nreturn pad, q\n")
    assert fp.dynamic_reads == 0
    assert fp.nonstring_key_reads == 1
    assert fp.register_const_key_reads == 1


def test_the_extractor_never_decodes_a_bytecode_derived_string():
    """`lift/footprint.py` is inside the guarded packages and handles constant
    -pool bytes; CLAUDE.md's red line says those stay `bytes`. Static AST check
    (never imports the module): no `.decode(`, no `str(...)`, no `bytes.decode`
    attribute reference anywhere in it.
    """
    path = REPO_ROOT / "src" / "pyluadec" / "lift" / "footprint.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    offenders = [
        f"{path}:{n.lineno}: .{n.attr}"
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr in ("decode", "encode")
    ]
    assert not offenders, "\n".join(offenders)


def test_footprint_module_is_covered_by_the_regex_ban():
    """`tests/test_engineering_practice.py::GUARDED_PACKAGES` scans BY PACKAGE
    (`rglob` under each), so a new file under `lift/` is covered without any
    edit there. Task 2 measured that a top-level `src/pyluadec/` module is NOT;
    this one is not top-level. Asserted rather than assumed."""
    from test_engineering_practice import _iter_guarded_files
    target = REPO_ROOT / "src" / "pyluadec" / "lift" / "footprint.py"
    assert target in _iter_guarded_files()


# --------------------------------------------------------------------------
# the dump CLI: name emission, and the fixed point
# --------------------------------------------------------------------------

def _cli():
    spec = importlib.util.spec_from_file_location(
        "footprint_dump_under_test", REPO_ROOT / "scripts" / "footprint_dump.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_name_emission_rule():
    mod = _cli()
    assert mod.emit_name(b"gameSave") == "gameSave"
    assert mod.emit_name(b"_x9") == "_x9"
    # printable ASCII but not identifier-shaped -> hex form
    assert mod.emit_name(b"has space") == {"nonascii": b"has space".hex()}
    assert mod.emit_name(b"9lives") == {"nonascii": b"9lives".hex()}
    assert mod.emit_name(b"") == {"nonascii": ""}
    # non-ASCII -> hex form, built from the bytes, never decoded
    assert mod.emit_name(b"\xe3\x81\x82") == {"nonascii": "e38182"}
    # control characters are outside 0x20..0x7e
    assert mod.emit_name(b"a\tb") == {"nonascii": b"a\tb".hex()}


@pytest.fixture(scope="module")
def doc():
    """Parse the 2 MB committed dump ONCE for the module (it is read by four
    tests; parsing it per test was measurable against the 45s suite ceiling)."""
    assert FOOTPRINTS.exists(), (
        "corpus/observation/footprints.json missing -- run "
        "PYLUADEC_CORPUS_DIR=... uv run python scripts/footprint_dump.py")
    return json.loads(FOOTPRINTS.read_text())


def test_committed_footprints_exist_and_are_well_formed(doc):
    assert doc["version"] == "footprint-v1"
    assert doc["summary"]["n_files"] == 229
    assert doc["summary"]["n_protos"] == 1944
    n = sum(len(f["protos"]) for f in doc["files"])
    assert n == 1944


def test_corpus_headline_census(doc):
    """The two numbers M6 Task 7's strategy rests on, pinned so they cannot
    move silently. Measured 2026-08-13 over all 229 files / 1944 protos."""
    s = doc["summary"]
    assert s["read_sites"] == 11910
    assert s["dynamic_reads"] == 880
    assert s["attributed_reads"] == 8061
    assert s["unattributed_reads"] == 2450
    assert s["nonstring_key_reads"] == 519
    assert s["write_sites"] == 1667
    assert s["dynamic_writes"] == 66
    # the `lcode.c` >255-constant fallback, kept visible rather than folded in
    assert s["register_const_key_reads"] == 256
    assert s["register_const_key_writes"] == 585
    assert s["call_sites"] == 44812
    assert s["global_call_sites"] == 41649
    assert s["table_key_call_sites"] == 1486
    assert s["unattributed_calls"] == 1677
    assert s["distinct_globals_read"] == 164        # agrees with effects.py's census
    assert s["distinct_calls"] == 125
    assert s["distinct_table_key_reads"] == 206
    # per-proto distribution of `dynamic_reads`: the hypothesis was
    # "overwhelmingly 0". Keys are strings in the JSON.
    dist = s["dynamic_reads_per_proto"]
    assert dist["0"] == 1755
    assert sum(dist.values()) == 1944
    assert max(int(k) for k in dist) == 60
    # size distribution of `table_key_reads` -- the other number Task 7 needs
    sizes = s["table_key_reads_per_proto"]
    assert sizes["0"] == 783
    assert sum(sizes.values()) == 1944
    assert max(int(k) for k in sizes) == 58
    # every name in the whole dump is an ASCII identifier, so the
    # `{"nonascii": ...}` branch has NO corpus evidence (synthetic only)
    assert s["non_identifier_names"] == 0


def test_accounting_identities_hold_over_the_whole_corpus(doc):
    for f in doc["files"]:
        for pr in f["protos"]:
            assert pr["read_sites"] == (
                pr["attributed_reads"] + pr["unattributed_reads"]
                + pr["dynamic_reads"] + pr["nonstring_key_reads"]), (f["file"], pr["proto_path"])
            assert pr["write_sites"] == (
                pr["attributed_writes"] + pr["unattributed_writes"]
                + pr["dynamic_writes"] + pr["nonstring_key_writes"]), (f["file"], pr["proto_path"])
            assert pr["call_sites"] == (
                pr["global_call_sites"] + pr["table_key_call_sites"]
                + pr["unattributed_calls"]), (f["file"], pr["proto_path"])


@pytest.mark.timeout(300)
def test_footprints_json_is_a_reproducible_fixed_point(corpus_dir, tmp_path, monkeypatch):
    """Same discipline as `tests/test_ledger_ratchet.py::
    test_ledger_is_a_reproducible_fixed_point`: committed generated data must
    be byte-reproducible from its own generator, or a real two-line regression
    would arrive buried in diff noise. Runs against a scratch ROOT so the
    committed file is never touched as a side effect."""
    mod = _cli()
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setenv("PYLUADEC_CORPUS_DIR", str(corpus_dir))
    assert mod.main() == 0
    regenerated = (tmp_path / "corpus" / "observation" / "footprints.json").read_bytes()
    assert regenerated == FOOTPRINTS.read_bytes()

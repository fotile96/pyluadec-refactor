"""The `and`/`or` VALUE idiom (`TESTSET`), M4 task 4.

Every fixture here is oracle-compiled with the real `luac_sz4` and adjudicated
by the real L3 gate (`certify_proto(..., is_chunk_root=True)`): the printed
source is recompiled and compared field-by-field under the versioned
normalization ladder. Nothing here relaxes the gate. A fixture that produces
semantically-right-but-differently-compiled source is a FAILURE of the
reconstruction, not something to absorb with a new ladder rung.

## What luac emits, and how it was confirmed (2026-08-11)

`lvm.c:577-585` (vendored, pristine):

    case OP_TESTSET: {
      TValue *rb = RB(i);
      if (l_isfalse(rb) != GETARG_C(i)) {
        setobjs2s(L, ra, rb);
        dojump(L, pc, GETARG_sBx(*pc));
      }
      pc++;

`pc` already points at the FOLLOWING instruction, which is always a `JMP`
(`lcode.c:condjump` emits the pair). So: when `bool(R[B]) == C`, the value is
kept (`R[A] := R[B]`) and control lands on that JMP's own target; otherwise
control falls through PAST the JMP. That is exactly the reading in the
no-frills VM-instruction PDF (`others/a-no-frills-introduction-to-lua-5.1-vm-
instructions.pdf` §TESTSET), which CLAUDE.md makes authoritative over the
official docs.

`C == 1` is `or` (keep a truthy left operand), `C == 0` is `and` (keep a falsy
one) -- `lcode.c:jumponcond` is reached from `luaK_goiffalse` with `cond=1`
for `or` and from `luaK_goiftrue` with `cond=0` for `and`.

Two rewrites in `lcode.c:patchtestreg` matter here and are pinned by fixtures
below:

  * when the destination register equals the tested one, the TESTSET is
    REWRITTEN to `TEST B 0 C` -- so `x = x or 1` and `if not x then x = 1 end`
    are the *same bytecode*. This recognizer therefore never claims a bare
    `TEST` as a value test (see
    `test_test_variant_is_left_to_the_if_recognizer`).
  * when a jump list is patched with `NO_REG` (`luaK_patchtohere`), a pending
    TESTSET is rewritten to `TEST` and its jump is retargeted at the *next*
    alternative rather than at the join. That is the `(F and X) or Y` shape --
    the only shape in this corpus -- and it is what the recognizer's "gate"
    handles.
"""
import pytest

from pyluadec.emit.lua import print_chunk, print_function
from pyluadec.express.names import RegClass, classify_registers
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.oracle import compile_source
from pyluadec.sir.build import StructureError, build_sir
from pyluadec.sir.regions import CondValue, Seq, all_claimed
from pyluadec.structure.structured import certify_proto

# Each of these contains at least one real `TESTSET` and certifies L3 --
# measured 2026-08-11.
#
# Every operand local is INITIALISED (`local b, c = 1, 2`, never `local b, c`).
# That is not decoration: `local b, c` with no initialiser at the top of a
# chunk compiles to NOTHING at all (`lcode.c:luaK_nil` elides the LOADNIL when
# `fs->pc == 0`, since the registers are already nil), so a stripped proto
# carries no trace of those declarations and no decompiler can reproduce them.
# The first draft of this list used them and every fixture failed
# certification on `constants`/`maxstacksize` -- the reconstruction was
# already right, the fixtures were not.
CASES = [
    b"local b, c = 1, 2 local a = b or c print(a)",                 # plain `or`
    b"local b, c = 1, 2 local a = b and c print(a)",                # plain `and`
    b"local b, c, d = 1, 2, 3 local a = b or c or d print(a)",      # or-chain
    b"local b, c, d = 1, 2, 3 local a = b and (c or d) print(a)",   # and/or chain
    b"local b, c, d = 1, 2, 3 local a = b or c and d print(a)",     # or/and chain
    b"local b, c, d = 1, 2, 3 local a = b and c or d print(a)",     # TEST gate
    b'local b, c = 1, 2 local a = b or c or "x" or 4 print(a)',     # TEST-variant links
    b"local x, y, a = 1, 2, 3 a = (x < 1 and 1) or (y - 1) print(a)",   # LT gate
    b"local x, y = 1, 2 local a = (x < 1 and 1) or (y - 1) print(a)",   # LT gate, TEST variant
    b"local x = 1 x = (x > 9 and 9) or x print(x)",                 # empty tail (corpus shape)
    b"local a = 0 a = f() or {} print(a)",                          # call / table operands
    b"local a = 0 a = f() or g() print(a)",
    b"local b = 1 local a = b or {1, 2} print(a)",
    b"local b, c = 1, 2 local a = b or c while a do a = b or c end print(a)",   # while body
    b"local b, c = 1, 2 for i = 1, 3 do local a = b or c print(a) end",         # for body
    b"local b, c = 1, 2 if b then local a = b or c print(a) end",              # if arm
    b"local function m(p, q) local a = p or q return a end print(m(1))",       # closure
]

# Shapes this task deliberately does NOT claim, with the reason. Each is
# asserted separately below rather than silently omitted.
UNCLAIMED = [
    # The brief's `x = f() or {}`: the destination register is the tested one,
    # so `patchtestreg` emits a bare `TEST` and the incumbent `if` reading
    # stands (see test_test_variant_is_left_to_the_if_recognizer). It does not
    # certify today, and not because of anything here -- it prints
    # `local l0_0 = f  l0_0 = l0_0()` for `local x = f()`, the extra-MOVE /
    # call-binding register-classification cluster that is M4 Task 13's.
    b"local x = f() or {} print(x)",
    # Same TEST-variant shape reached through upvalues; refused one layer
    # earlier ("temp register 0 read before it was staged"). Verified
    # unchanged by this task: it behaves identically at HEAD~ (2026-08-11).
    b"local b, c = 1, 2 local function m() return b or c end print(m())",
]


def _proto(src: bytes):
    return load_bytes(compile_source(src, strip=True))


def test_fixtures_certify_l3():
    bad = []
    for src in CASES:
        cert = certify_proto(_proto(src), is_chunk_root=True)
        if cert.level != "L3":
            bad.append((src, cert.mismatches))
    assert bad == []


def test_unclaimed_shapes_stay_unclaimed_and_are_not_silently_wrong():
    """The shapes this task declines still fail SAFELY: either they refuse to
    print at all, or they print something that does not certify. What must
    never happen is uncertified structured output shipping, and that is
    `structure.structured`'s invariant, not this module's -- asserted here so
    a future widening of the recognizer has to move these rows deliberately."""
    for src in UNCLAIMED:
        cert = certify_proto(_proto(src), is_chunk_root=True)
        assert cert.level == "L1", src
        assert cert.source is None, src


def test_plain_or_prints_as_or():
    out = print_chunk(_proto(b"local b, c local a = b or c print(a)"))
    assert out is not None
    assert "local l0_2 = l0_0 or l0_1" in out


def test_plain_and_prints_as_and():
    out = print_chunk(_proto(b"local b, c local a = b and c print(a)"))
    assert out is not None
    assert "local l0_2 = l0_0 and l0_1" in out


def test_gate_prints_the_and_or_idiom():
    out = print_chunk(_proto(b"local b, c, d local a = b and c or d print(a)"))
    assert out is not None
    assert "local l0_3 = l0_0 and l0_1 or l0_2" in out


def test_claims_exactly_its_pc_range():
    """The TESTSET, its JMP, the gate/gate-JMP and the alternative-value
    producers are claimed exactly once -- `build_sir` asserts the audit at
    exit, so reaching a region tree at all already proves it; this pins the
    shape of the claim so a future edit cannot move pcs between the CondValue
    and a sibling Straight without a test noticing."""
    fn = lift_proto(_proto(b"local x, y, a a = (x < 1 and 1) or (y - 1) print(a)"))
    #  1 LT     2 JMP->6   3 LOADK r3   4 TESTSET r2<-r3  5 JMP->7   6 SUB r2
    region = build_sir(fn)
    assert isinstance(region, Seq)
    (cv,) = [r for r in region.body if isinstance(r, CondValue)]
    assert cv.target == 2
    assert cv.claimed_pcs == frozenset({1, 2, 3, 4, 5, 6})
    assert all_claimed(region) == set(fn.instrs)


def test_test_variant_is_left_to_the_if_recognizer():
    """`x = x or 1` and `if not x then x = 1 end` compile to the SAME bytecode
    (`patchtestreg` rewrites the TESTSET to `TEST` when the destination is the
    tested register). Neither reading is provably right, so the incumbent M3
    `if` reading is kept -- exactly the tie-break `_match_repeat` documents.
    Pinned so that widening the recognizer to bare `TEST` becomes a
    deliberate, measured decision rather than a silent churn of a very common
    shape."""
    a = compile_source(b"local x = f() x = x or 1 print(x)", strip=True)
    b = compile_source(b"local x = f() if not x then x = 1 end print(x)", strip=True)
    assert load_bytes(a).code == load_bytes(b).code
    fn = lift_proto(load_bytes(a))
    region = build_sir(fn)
    assert not [r for r in getattr(region, "body", ()) if isinstance(r, CondValue)]


def test_unprovable_testset_shape_still_refuses_loudly():
    """A TESTSET whose following JMP does not close a value chain is not a
    shape this recognizer understands. It must raise, not be guessed at.

    Built by hand (`tests/synth.py` style, straight from a Proto) because luac
    cannot be coaxed into emitting a TESTSET whose JMP jumps BACKWARDS: every
    TESTSET luac writes is patched to a forward `final` label."""
    from tests.synth import mk_proto, mk_instr
    from pyluadec.lift.opcodes import Op
    words = [
        mk_instr(Op.LOADK, 0, bx=0).word,        # 1: r0 = 1
        mk_instr(Op.TESTSET, 1, 0, 1).word,      # 2: r1 := r0 if truthy -> jump
        mk_instr(Op.JMP, sbx=-2).word,           # 3: JMP -> 2 (backwards!)
        mk_instr(Op.RETURN, 0, 1).word,          # 4
    ]
    from pyluadec.ingest.proto import LuaNumber
    import struct
    p = mk_proto(words, constants=(LuaNumber(1.0, struct.pack("<d", 1.0)),),
                 maxstacksize=3)
    with pytest.raises(StructureError, match="TESTSET"):
        build_sir(lift_proto(p))


# ---------------------------------------------------------------------------
# Corpus census (the diagnosis this task started from, committed as a ratchet).
# ---------------------------------------------------------------------------

def test_corpus_testset_census(corpus_dir):
    """Measured 2026-08-11 over the 229-file corpus, 1478 unique protos:

        unique protos containing TESTSET                16
        TESTSET sites                                   53   -- every one C == 1
        of the 16, refused by build_sir before task 4   16
        of the 16, refused by build_sir after task 4     8   (none for TESTSET)
        unique protos build_sir accepts                 1447 (was 1435)
        unique protos with >= 1 CondValue region        12   (28 regions)
        of those 12, protos with NO TESTSET at all       4   -- gate + TEST
                                                             variant chains

    None of the 16 certifies L3 yet, and the reasons are all downstream of
    this task (see task-4-report.md): 8 are still refused by `build_sir` for
    if/else shapes M4 tasks 5-6 own, 6 hit this module's guard because
    `classify_registers` calls the operand's staging register a LOCAL, and 2
    print but diverge on `code` by extra `MOVE`s only. The last two clusters
    are one defect -- whole-function, per-register-number classification --
    which is M4 Task 13's. Measured: replacing the guard with unconditional
    force-temping (which would print output this module cannot justify) moves
    that count from 0 to 0.
    """
    from pyluadec.lift.opcodes import Op, decode
    from pyluadec.ingest import load_file
    from pyluadec.pipeline import walk_proto_paths
    from pyluadec.verify.ledger import structural_hash

    uniq = {}
    for f in sorted(corpus_dir.glob("*.lua")):
        protos = {}
        walk_proto_paths("main", load_file(f), protos)
        for p in protos.values():
            uniq.setdefault(structural_hash(p), p)
    sites = refused = 0
    ts_protos = []
    for p in uniq.values():
        ops = [decode(w, pc=i + 1) for i, w in enumerate(p.code)]
        n = sum(1 for ri in ops if ri.op is Op.TESTSET)
        if not n:
            continue
        ts_protos.append(p)
        sites += n
        assert all(ri.c == 1 for ri in ops if ri.op is Op.TESTSET)
        try:
            build_sir(lift_proto(p))
        except StructureError as exc:
            refused += 1
            assert "TESTSET" not in str(exc), str(exc)
    assert len(ts_protos) == 16
    assert sites == 53
    assert refused == 8


# ---------------------------------------------------------------------------
# The guard, and the proof that it is load-bearing.
# ---------------------------------------------------------------------------

_GUARDED = b"local x, y, a a = (x < 1 and 1) or (y - 1) print(a)"


def _forced_local(fn, reg: int) -> RegClass:
    """`classify_registers(fn)` with `reg` demoted from temp to local."""
    rc = classify_registers(fn)
    return RegClass(locals=rc.locals | {reg}, temps=rc.temps - {reg},
                    loop_vars=rc.loop_vars)


def test_operand_code_that_needs_a_statement_is_refused():
    """THE guard for this node. A short-circuit alternative's operand code is
    reconstructed as a pure expression; if it reconstructs to a *statement*
    instead, printing only the `and`/`or` expression would DROP that statement
    while the pc-claim audit still passed (the pcs are claimed by the
    CondValue either way). Refuse instead.

    Unreachable from real luac output on this corpus -- `lparser.c` reads an
    `and`/`or` operand with `fs->freereg == fs->nactvar`, so every register it
    writes is above every live local and classifies temp -- but
    `classify_registers` is a whole-function, per-register-NUMBER analysis
    (see its docstring's "Modeling limitation"), so a register that is a temp
    here can be a local elsewhere in the same function. Demoting register 3
    (the `LOADK 1` that feeds the TESTSET) is exactly that situation."""
    fn = lift_proto(_proto(_GUARDED))
    region = build_sir(fn)
    with pytest.raises(ReconstructError, match="statement"):
        print_function(fn, region, _forced_local(fn, 3), 0)


def test_without_the_guard_the_statement_is_silently_dropped(monkeypatch):
    """Fault injection: neuter the guard and show what it is buying.

    Without it the `local l0_3 = 1` never prints, yet `l0_3` is still
    referenced by the emitted expression -- where Lua resolves it as a GLOBAL.
    That is silently wrong output, and the pc-claim audit does not catch it
    (the LOADK's pc is claimed by the CondValue in both worlds). Task 1's
    lesson, restated: the audit proves nothing was left unclaimed, never that
    everything claimed was printed."""
    from pyluadec.express import reconstruct as R

    monkeypatch.setattr(R.Reconstructor, "_refuse_statements",
                        lambda self, emitted, where: None)
    fn = lift_proto(_proto(_GUARDED))
    region = build_sir(fn)
    out = print_function(fn, region, _forced_local(fn, 3), 0)
    assert "l0_3" in out                       # still referenced ...
    assert "local l0_3" not in out             # ... but never declared: dropped

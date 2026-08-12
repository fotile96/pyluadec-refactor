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
control falls through PAST the JMP.

`C == 1` is `or` (keep a truthy left operand), `C == 0` is `and` (keep a falsy
one) -- `lcode.c:jumponcond` is reached from `luaK_goiffalse` with `cond=1`
for `or` and from `luaK_goiftrue` with `cond=0` for `and`.

## The no-frills PDF confirms this, but its prose does not (erratum)

CLAUDE.md makes `others/a-no-frills-introduction-to-lua-5.1-vm-instructions.pdf`
authoritative over the official Lua docs, so it was checked directly (p. 37).
Three of its four statements agree with the above; one contradicts the other
three and must be discarded:

  * pseudocode, AGREES: `TESTSET A B C   if (R(B) <=> C) then R(A) := R(B)
    else PC++`;
  * operator mapping, AGREES: "The `and` operator uses a C of 0 (false) while
    `or` uses a C value of 1 (true)";
  * worked example, AGREES -- `local a,b,c; c = a and b` compiles to
    `[1] testset 2 0 0  ; to [3] if true / [2] jmp -> [4] / [3] move 2 1`, i.e.
    a TRUTHY `a` (not matching C==0) falls through to evaluate `b`, and a falsy
    one takes the JMP with `c := a`;
  * prose, CONTRADICTS ITS OWN PSEUDOCODE: "If R(B) matches C, the next
    instruction is skipped, otherwise R(B) is assigned to R(A) and the VM
    continues with the next instruction." That is the mapping inverted. It
    also disagrees with `lvm.c`, which is the ground truth here. Recorded so
    the next reader of that page does not have to re-derive it.

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


@pytest.mark.parametrize("src", CASES, ids=range(len(CASES)))
def test_fixtures_certify_l3(src):
    """One case per test id (M5 agenda item 10, closed at task 12). This was a
    plain `for` over `CASES` collecting into a `bad` list, so a failure named
    the loop and printed the whole batch; now the failing case is the test id.
    The item said 15 cases; there are **17** -- measured 2026-08-13, and the
    parametrisation makes the count self-maintaining."""
    cert = certify_proto(_proto(src), is_chunk_root=True)
    assert cert.level == "L3", cert.mismatches


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
# The two guards inside `_match_cond_value` itself (fix round 1, Important 1).
#
# `_match_cond_value` carries two checks beyond `_parse_value`'s own recursive
# descent: the dominance check (the `_verify_single_entry` call inside
# `_match_cond_value`) and the claimed-range equality check (`claimed != {...}`
# inside `_match_cond_value`, now parenthesized by F5 below). The review found
# neither pinned by any fixture: neutering both together left 128/128 tests
# green and the corpus census unchanged. What follows pins each SEPARATELY,
# and is honest about the two turning out to be different in kind.
# ---------------------------------------------------------------------------

def test_reachable_jump_into_the_middle_of_a_cond_value_chain_raises(monkeypatch):
    """Fix round finding (M4 task 4 review, Important 1, dominance half): the
    `_verify_single_entry` call inside `_match_cond_value`
    was pinned by nothing -- the reviewer neutered it (together with the
    claim-equality check below) and got 128/128 tests passing and corpus
    behaviour byte-for-byte unchanged (accepts 1447, CondValue protos 12).

    No real (luac-compiled) TESTSET shape can exercise it: every other
    recognizer's own exact-equality boundary conditions (an if's else-skip, a
    break, a loop's closing JMP) already prevent a jump from landing strictly
    INSIDE a sibling construct's interior without first tripping that OTHER
    construct's own refusal -- confirmed by the reviewer's own attempted
    construction (`LOADK / EQ / JMP->7 / TESTSET / JMP->8 / LOADK / MOVE /
    RETURN`, which never reached `_match_cond_value` at all: `_structure_if`
    claimed the range first and refused with `pc 4: unrecognized transfer
    TESTSET`, guarded and neutered identically).

    So, exactly like `test_reachable_non_dominating_block_inside_a_while_
    body_raises` in `tests/test_sir_while.py` (M4 task 3's fix round, the
    identical problem one level simpler): this fixture's instructions are
    real (`mk_instr`/`lift_proto`) and drive everything `build_sir` does NOT
    get from the CFG (opcode dispatch, `_parse_value`'s recursive descent).
    Only the CFG/dominance machinery is hand-built (`tests/synth.py`'s
    `mk_cfg`) and substituted via monkeypatch for `build_cfg` /
    `immediate_dominators` / `_pc_block_map`, so `build_sir` sees a
    deliberately-impossible-for-luac CFG layered onto a self-consistent
    instruction stream: an ungated `r1 = r0 or k1` chain (TESTSET at pc 2,
    JMP->5, VTail at pc 4) where pc 4 -- the second alternative's operand code,
    i.e. exactly "the middle of what looks like an alternative" the
    recognizer's own docstring warns about -- is ALSO reachable directly from
    the function entry, bypassing the TESTSET at pc 2 entirely."""
    from tests.synth import mk_instr, mk_proto, mk_cfg
    from pyluadec.lift import lift_proto, Op
    from pyluadec.cfg import immediate_dominators
    from pyluadec.ingest.proto import LuaNumber
    from pyluadec.sir.regions import CondValue
    import struct
    import pyluadec.sir.build as build_mod

    words = [
        mk_instr(Op.LOADK, a=0, bx=0, pc=1).word,        # pc1: r0 = k0
        mk_instr(Op.TESTSET, a=1, b=0, c=1, pc=2).word,  # pc2: TESTSET r1<-r0 C=1 (lo)
        mk_instr(Op.JMP, sbx=5 - 3 - 1, pc=3).word,      # pc3: JMP -> 5 (join)
        mk_instr(Op.LOADK, a=1, bx=1, pc=4).word,        # pc4: r1 = k1 (VTail -- the intruded pc)
        mk_instr(Op.RETURN, a=1, b=2, pc=5).word,        # pc5: return r1
    ]
    p = mk_proto(words, constants=(LuaNumber(1.0, struct.pack("<d", 1.0)),
                                    LuaNumber(2.0, struct.pack("<d", 2.0))),
                 maxstacksize=4)
    fn = lift_proto(p)
    assert fn.instrs[2].ri.op is Op.TESTSET and fn.instrs[2].successors == (3, 4), \
        "sanity: TESTSET's real successors are (match-case JMP, no-match rest)"

    edges = {
        0: (1, 99),   # function entry reaches both the chain AND the intruder
        1: (2,),      # real: pc1 -> pc2 (lo)
        2: (3, 4),    # real: TESTSET's own two successors
        3: (5,),      # real: the TESTSET's JMP -> join
        4: (5,),      # real: VTail -> join
        5: (),
        99: (4,),     # THE INTRUDER: reaches the VTail directly, without going
                      # through the TESTSET at pc 2 (lo) at all
    }
    cfg = mk_cfg(edges, entry=0)
    idoms = immediate_dominators(cfg)
    pc2blk = {s: s for s in edges}
    assert idoms[4] == 0 and not build_mod.dominates(idoms, 2, 4), \
        "sanity: pc 4 must be reachable but NOT dominated by pc 2's (lo's) block"

    monkeypatch.setattr(build_mod, "build_cfg", lambda fn_: cfg)
    monkeypatch.setattr(build_mod, "immediate_dominators", lambda cfg_: idoms)
    monkeypatch.setattr(build_mod, "_pc_block_map", lambda cfg_: pc2blk)

    with pytest.raises(StructureError, match="unrecognized transfer TESTSET"):
        build_sir(fn)

    monkeypatch.setattr(build_mod, "_verify_single_entry", lambda *a, **k: None)
    region = build_sir(fn)             # must NOT raise once the guard is neutered
    (cv,) = [r for r in region.body if isinstance(r, CondValue)]
    assert 4 in cv.claimed_pcs, \
        "neutered run did not even claim the intruded pc -- fixture stopped exercising the guard"


def test_cond_value_claim_check_is_unreachable_from_real_parse_value_but_the_pc_claim_audit_still_catches_a_broken_value_claimed(monkeypatch):
    """Fix round finding (M4 task 4 review, Important 1, claim-equality half):
    the `claimed != {p for p in fn.instrs if lo <= p < join}` check inside
    `_match_cond_value` was likewise pinned by nothing.

    Unlike the dominance guard above, this one is not merely hard to reach --
    it is PROVABLY unreachable from any input given the current
    `_parse_value`/`value_claimed` pairing. `_parse_value` walks `pc`
    monotonically from `lo`, and refuses with `_NoValueChain` unless
    `pc == join` at its own exit (`sir.build._parse_value`'s closing
    `if pc != join`), and every VAlt/VTail it returns is built from
    CONTIGUOUS sub-ranges of exactly the pcs `_parse_value` itself consumed
    at each step (gate+gate_jmp, inner_staging, test+test_jmp, staging, then
    `rest` starting exactly where the previous piece ended).
    `sir/regions.py::value_claimed` mirrors that same field-by-field -- so
    `_parse_value` succeeding implies `value_claimed(node) == {lo..join-1}`
    by construction, not by luck. No amount of adversarial bytecode can pull
    the two apart; only a FUTURE bug that edits one without the other could
    (exactly what `value_claimed`'s own docstring warns against: "a new field
    cannot be added without this function being the obvious place that has to
    learn about it").

    So the only way to make this guard decide anything is to fault-inject
    that future bug directly, the same technique `test_without_the_guard_the_
    statement_is_silently_dropped` already uses for `_refuse_statements`.
    Measured here, and the answer is nuanced: even with the check DELETED,
    `build_sir`'s own top-level pc-claim audit (`sir/build.py:126-129`) still
    refuses -- just less precisely, with a different message. So the guard
    buys locality and a clearer diagnosis, not the difference between wrong
    output and no output; the pipeline's overall soundness does not depend on
    it. That is a real reason to keep it (a clear, local diagnosis is worth
    something) and an equally real reason not to claim more for it than that.
    """
    from tests.synth import mk_instr, mk_proto
    from pyluadec.lift import lift_proto, Op
    from pyluadec.ingest.proto import LuaNumber
    from pyluadec.sir import regions as regions_mod
    from pyluadec.sir.regions import CondValue
    import struct
    import pyluadec.sir.build as build_mod

    words = [
        mk_instr(Op.LOADK, a=0, bx=0, pc=1).word,
        mk_instr(Op.TESTSET, a=1, b=0, c=1, pc=2).word,
        mk_instr(Op.JMP, sbx=5 - 3 - 1, pc=3).word,
        mk_instr(Op.LOADK, a=1, bx=1, pc=4).word,
        mk_instr(Op.RETURN, a=1, b=2, pc=5).word,
    ]
    p = mk_proto(words, constants=(LuaNumber(1.0, struct.pack("<d", 1.0)),
                                    LuaNumber(2.0, struct.pack("<d", 2.0))),
                 maxstacksize=4)
    fn = lift_proto(p)

    # Baseline: unmodified, this fixture is an ordinary single-entry chain
    # and build_sir accepts it (no CFG tampering needed for this half).
    baseline = build_sir(fn)
    (cv,) = [r for r in baseline.body if isinstance(r, CondValue)]
    assert cv.claimed_pcs == frozenset({2, 3, 4})

    real_value_claimed = regions_mod.value_claimed

    def broken_value_claimed(node):
        # Simulates the future bug the check exists for: value_claimed
        # under-reports (drops pc 3, the TESTSET's own JMP).
        return frozenset(pc for pc in real_value_claimed(node) if pc != 3)

    monkeypatch.setattr(build_mod, "value_claimed", broken_value_claimed)

    # With the guard PRESENT and value_claimed broken: the mismatch is
    # caught locally, `_match_cond_value` returns None ("not this shape"),
    # and dispatch falls through to the generic downstream refusal.
    with pytest.raises(StructureError, match="unrecognized transfer TESTSET"):
        build_sir(fn)

    # Now ALSO neuter the check itself: a verbatim copy of
    # `_match_cond_value` with exactly the `claimed != {...}` guard deleted
    # -- the same "minus check" technique
    # `test_reachable_jump_into_the_middle_of_a_while_header_raises` in
    # `tests/test_sir_while.py` uses for _match_while_header's inline check.
    def _match_cond_value_minus_claim_check(fn_, cfg, idoms, pc2blk, lo, hi):
        li = fn_.instrs[lo]
        op = li.ri.op
        if op is Op.TESTSET:
            t = lo
        elif op in build_mod._COMPARE:
            jmp = fn_.instrs.get(lo + 1)
            if jmp is None or jmp.ri.op is not Op.JMP:
                return None
            t = jmp.successors[0] - 2
            cand = fn_.instrs.get(t)
            if cand is None or (cand.ri.op is not Op.TESTSET
                                 and not (cand.ri.op is Op.TEST and cand.ri.b == 0)):
                return None
        else:
            return None
        test_jmp = fn_.instrs.get(t + 1)
        if test_jmp is None or test_jmp.ri.op is not Op.JMP:
            return None
        join = test_jmp.successors[0]
        if not (lo < join <= hi):
            return None
        target = fn_.instrs[t].ri.a
        try:
            node = build_mod._parse_value(fn_, lo, join, target, committed=False)
            build_mod._verify_single_entry(cfg, idoms, pc2blk, lo, lo, join)
        except (build_mod._NoValueChain, StructureError):
            return None
        claimed = build_mod.value_claimed(node)
        # claim-equality check DELETED here -- this is the neutered copy.
        return CondValue(target=target, node=node, claimed_pcs=claimed), join

    monkeypatch.setattr(build_mod, "_match_cond_value",
                        _match_cond_value_minus_claim_check)

    # Neutered check + broken value_claimed: _match_cond_value now WRONGLY
    # accepts an under-claiming CondValue (pc 3 missing from claimed_pcs) --
    # but build_sir's own final pc-claim audit still refuses, just with a
    # different, less specific message. No silently-wrong output escapes.
    with pytest.raises(StructureError, match=r"pc-claim audit failed; unclaimed \[3\]"):
        build_sir(fn)


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
    # `refused` is a progress metric, not a fixed fact about the corpus: M4
    # tasks 5-6 (if/else threading) are expected to close some of the 8
    # remaining `build_sir` refusals from this set, which would DECREASE this
    # number. An exact `==` here would go red on that improvement -- the same
    # measured-minus-slack `>=`-in-the-good-direction protocol
    # `tests/test_sir_while.py`'s `test_corpus_build_sir_acceptance_floor`
    # uses for the analogous acceptance-count ratchet. A regression (this
    # number going UP) is what must fail; a decrease must not.
    assert refused <= 8, f"regression: {refused} TESTSET protos refused, was 8"


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
    `classify_registers` is a heuristic reconstruction of luac's input, and
    since M4 task 13 it answers per DEFINITION rather than per register
    number -- which removed the whole-function bleed this used to describe,
    but not the possibility of a definition its barriers grade local.
    Demoting register 3 (the `LOADK 1` that feeds the TESTSET) is exactly
    that situation."""
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

"""M6 task 11: compound `if` conditions -- `and`/`or` chains as a condition TREE.

The defect this file closes: `sir.regions.If` carried exactly ONE compare
instruction, so `a and b` could only be read as nested `if`s. That reading is
the SAME bytecode when the `if` has no else branch (which is why
`if a and b then f() end` certified all along) and a DIFFERENT one when it
does -- with an else, both conjuncts' false-exits are patched by
`luaK_patchtohere` straight to the else block, whereas the nested reading
sends the inner one to the end of the outer then-block, skipping the else.
`or` had no nested-`if` reading at all: its truelist is patched to the START
of the then-block (`luaK_goiffalse`, lcode.c:196-208), so the first compare's
jump goes FORWARD over the second condition.

Discipline, same as every other recognizer file here: every fixture is
oracle-compiled with the real `luac_sz4`, and each asserts BOTH halves --
the pc-claim audit (`all_claimed(build_sir(fn)) == set(fn.instrs)`) and the
`L3` certification gate. Nothing here relaxes the gate.

All fixture sources are pure ASCII by construction, so assertions that
inspect printed text may decode; bytecode-derived strings elsewhere stay
`bytes`.
"""
import pytest

from pyluadec.emit.lua import print_chunk
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.sir.build import StructureError, build_sir
from pyluadec.sir.regions import CondOp, CondTest, If, all_claimed
from pyluadec.structure.structured import certify_proto


def _sir(src: bytes):
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    return fn, r


def _certifies(src: bytes) -> None:
    proto = load_bytes(compile_source(src, strip=True))
    fn = lift_proto(proto)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    cert = certify_proto(proto, is_chunk_root=True)
    assert cert.level == "L3", cert.reason


def _find(r, ty):
    out = []

    def walk(n):
        if n is None:
            return
        if isinstance(n, ty):
            out.append(n)
        b = getattr(n, "body", None)
        if isinstance(b, tuple):
            for c in b:
                walk(c)
        elif b is not None:
            walk(b)
        for a in ("then_body", "else_body"):
            walk(getattr(n, a, None))
    walk(r)
    return out


def _source(src: bytes) -> str:
    proto = load_bytes(compile_source(src, strip=True))
    out = print_chunk(proto)
    assert out is not None, src
    return out


# --------------------------------------------------------------- the two
# --------------------------------------------------------------- minimal shapes
#
# These are the two entries `tests/test_sir_longtail2.py::KNOWN_REFUSALS`
# carried as the compound-`if` gap through M5; they are asserted positively
# here now that the recognizer exists, and removed from that list.
CERTIFYING = [
    b"if a and b then f() else g() end",
    b"if a or b then f() end",
    b"if a or b then f() else g() end",
    b"if a and b then f() end",
    b"if a and b and c then f() else g() end",
    b"if a or b or c then f() else g() end",
    b"if a and b or c then f() else g() end",
    b"if a or b and c then f() else g() end",
    b"if (a or b) and c then f() else g() end",
    b"if (a and b) or (c and d) then f() else g() end",
    b"if a == 1 and b ~= 2 then f() else g() end",
    b"if a == 1 or b < 2 then f() else g() end",
    b"if not a and b then f() else g() end",
    b"if a and not b then f() else g() end",
    b"if h(1) and h(2) then f() else g() end",
    b"if h(1) or h(2) then f() else g() end",
    b"if a and b then f() elseif c or d then g() else h() end",
    b"local t = {} if t.x and t.y then f() else g() end",
    b"if a and b then while c do f() end else g() end",
    b"for i = 1, 10 do if a and b then f() else g() end end",
]


@pytest.mark.parametrize("src", CERTIFYING, ids=[s.decode() for s in CERTIFYING])
def test_compound_conditions_certify(src):
    _certifies(src)


# The condition tree is an `If` node's, and only an `If`'s. `While`'s header is
# a separate recognizer (`_match_while_header`) with an invariant the chain
# breaks -- "every pc in [lo, C] lives in `lo`'s CFG block", i.e. the header is
# ONE basic block, which a two-test chain is not. Left as a NAMED gap rather
# than half-extended, and pinned below so it cannot rot into a silent one.
#
# No corpus proto needs it: after this task the corpus's `structure:` family is
# one row (`snr_common.lua:main_71`) and its refusal is a loop/break
# recognition failure, not a header condition. `repeat ... until a and b` is
# only HALF in this gap -- measured 2026-08-14, `until a and b` certifies and
# `until a or b` refuses.
WHILE_HEADER_GAP = [
    (b"while a and b do f() end", "pc 9: unrecognized transfer JMP"),
    (b"while a or b do f() end", "pc 5: if targets out of range"),
    (b"repeat f() until a or b", "pc 7: if targets out of range"),
]


@pytest.mark.parametrize("src,msg", WHILE_HEADER_GAP,
                         ids=[s.decode() for s, _ in WHILE_HEADER_GAP])
def test_a_compound_while_header_is_still_refused_loudly(src, msg):
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    with pytest.raises(StructureError) as e:
        build_sir(fn)
    assert msg in str(e.value), str(e.value)


def test_a_conjunctive_repeat_condition_is_not_in_that_gap():
    """Measured 2026-08-14, and worth pinning because the `repeat` split is not
    the one a reader would guess from the `while` row above.

    `repeat f() until a and b` certifies. Not via the condition tree: both
    conjuncts' TRUE exits are the loop's own fall-through, so
    `_match_repeat` reads `a` as a bottom test whose false-exit re-enters the
    body and `b` likewise -- the incumbent one-compare reading already
    describes it, and this task's dispatch (chain only after a refusal) leaves
    it exactly alone.

    `repeat f() until a or b` does NOT, and is pinned in `WHILE_HEADER_GAP`
    above with its measured message. Recorded as a split rather than smoothed
    over: "compound `repeat` conditions work" would be half false.
    """
    _certifies(b"repeat f() until a and b")


def test_and_with_else_builds_a_cond_tree_not_nested_ifs():
    """The representation claim, not just the gate: ONE `If` whose `cond` is a
    `CondOp("and", ...)`, rather than two nested `If`s."""
    fn, r = _sir(b"if a and b then f() else g() end")
    ifs = _find(r, If)
    assert len(ifs) == 1, ifs
    cond = ifs[0].cond
    assert isinstance(cond, CondOp) and cond.op == "and"
    assert isinstance(cond.left, CondTest) and isinstance(cond.right, CondTest)
    # The tree claims BOTH tests and both JMPs; nothing is left to a body.
    assert {cond.left.test.ri.pc, cond.left.jmp_pc,
            cond.right.test.ri.pc, cond.right.jmp_pc} <= ifs[0].claimed_pcs


def test_or_precedence_is_printed_without_spurious_parentheses():
    """`a and b or c` and `a or b and c` are printed at the precedence the
    `_PREC` table already encodes (`and` 2, `or` 1, both left-associative), so
    neither needs parentheses. `a and (b or c)` does, and gets them."""
    assert "if a and b or c then" in _source(
        b"if a and b or c then f() else g() end")
    assert "if a or b and c then" in _source(
        b"if a or b and c then f() else g() end")
    assert "if a and (b or c) then" in _source(
        b"if a and (b or c) then f() else g() end")


def test_polarity_is_read_from_the_jump_sense_not_from_a_second_copy():
    """A test whose jump is the chain's TRUE exit reads with the OPPOSITE
    polarity to one whose jump is the false exit. `a or b`: `a`'s jump is the
    truelist, so `a` prints un-negated even though `Reconstructor
    .condition_expr`'s fall-through reading of the same instruction is its
    negation."""
    assert "if a or b then" in _source(b"if a or b then f() end")
    assert "if not a or b then" in _source(b"if not a or b then f() end")
    # `~=` prints as `not (x == y)` here, and that is the INCUMBENT rendering
    # (`_CMP_SYM` has no `~=` entry, deliberately -- see its comment), measured
    # unchanged on the single-test form `if a ~= 1 then f() end`. What this
    # line pins is that the `or`'s left operand is not additionally negated.
    assert "if not (a == 1) or b then" in _source(b"if a ~= 1 or b then f() end")


def test_pc_claim_audit_holds_over_the_whole_chain():
    """The chain's operand staging is claimed by the `If`, not left to a body
    or dropped. `_sir` already asserts the audit; this pins that the staging
    pcs really are inside the `If`'s own claim."""
    fn, r = _sir(b"if h(1) and h(2) then f() else g() end")
    ifs = _find(r, If)
    assert len(ifs) == 1
    # h(2)'s GETGLOBAL/LOADK/CALL sit between the two tests and belong to the
    # condition; the then-body starts after the second JMP.
    claimed = ifs[0].claimed_pcs
    assert len(claimed) >= 7, sorted(claimed)


def test_a_statement_between_two_tests_is_not_swallowed_into_the_condition():
    """The hazard the chain scan creates: `if a then x = 1 if b then ... end end`
    has an instruction between the two tests that is a STATEMENT, not operand
    staging, and both false-exits go to the same join -- so the arithmetic
    alone cannot tell it from `a and b`. It must NOT be read as one condition.

    It is not, and by construction: the chain is only attempted after the
    incumbent single-test reading has already raised, and this shape structures
    fine as nested `if`s. Asserted through the output text, which still carries
    the assignment.
    """
    src = b"local x = 0 if a then x = 1 if b then f() end end return x"
    out = _source(src)
    assert "x = 1" in out or "l0_0 = 1" in out, out
    _certifies(src)


def test_differential_execution_of_a_compound_condition():
    """Semantics, not just bytes: run the original and the decompiled source
    under the oracle VM and diff stdout, over all four truth assignments."""
    src = (b"local function f(a, b) if a and b then return 1 else return 2 end end\n"
           b"local function g(a, b) if a or b then return 3 else return 4 end end\n"
           b"print(f(true,true), f(true,false), f(false,true), f(false,false))\n"
           b"print(g(true,true), g(true,false), g(false,true), g(false,false))\n")
    original = compile_source(src, strip=True)
    expect = run_bytes(original, is_source=False)
    printed = print_chunk(load_bytes(original))
    assert printed is not None
    got = run_bytes(printed.encode(), is_source=True)
    assert (got.returncode, got.stdout) == (expect.returncode, expect.stdout)
    assert expect.stdout.splitlines() == [b"1\t2\t2\t2", b"3\t3\t3\t4"]


# ------------------------------------------------------------- fault injections
#
# Each mutates ONE thing the recognizer decides and requires certification to
# catch it. An instrument that cannot fail licenses exactly the claim it does
# not enforce (MEMORY.md, "guards must be proven load-bearing").
FAULTS = [
    # 1. swap the operator: `and` <-> `or`
    ("swap-and-or", b"if a and b then f() else g() end",
     b"if a or b then f() else g() end"),
    # 2. drop an arm: lose the else
    ("drop-else", b"if a and b then f() else g() end",
     b"if a and b then f() end"),
    # 3. drop a conjunct
    ("drop-conjunct", b"if a and b then f() else g() end",
     b"if a then f() else g() end"),
    # 4. mis-parenthesize: regroup the same three operands
    ("mis-parenthesize", b"if a and b or c then f() else g() end",
     b"if a and (b or c) then f() else g() end"),
    # 5. mis-parenthesize the other way
    ("mis-parenthesize-2", b"if a or b and c then f() else g() end",
     b"if (a or b) and c then f() else g() end"),
    # 6. flip one operand's polarity
    ("flip-polarity", b"if a and b then f() else g() end",
     b"if not a and b then f() else g() end"),
]


@pytest.mark.parametrize("name,truth,mutant", FAULTS, ids=[f[0] for f in FAULTS])
def test_certification_rejects_a_mutated_condition(name, truth, mutant):
    """The mutant is compiled as if it were what the printer had emitted for
    the truth's bytecode; `compare_protos` must reject it.

    This exercises the same comparison `certify_l3` runs, on the same pair of
    protos, so a mutation that survives here is one certification would ship.
    """
    from pyluadec.verify.normalize import compare_protos

    original = load_bytes(compile_source(truth, strip=True))
    mutated = load_bytes(compile_source(mutant, strip=True))
    assert compare_protos(original, mutated), (
        f"{name}: mutation produced identical bytecode -- not a fault injection")
    # ...and the truthful print does certify, so the pair above is a real
    # discrimination and not a comparator that rejects everything.
    assert certify_proto(load_bytes(compile_source(truth, strip=True)),
                         is_chunk_root=True).level == "L3"


def _chain_at(fn, pc):
    """`_match_cond_chain` on a whole (possibly hand-mutated) function."""
    from pyluadec.cfg import build_cfg, immediate_dominators
    from pyluadec.sir import build as B

    cfg = build_cfg(fn)
    return B._match_cond_chain(fn, cfg, immediate_dominators(cfg),
                               B._pc_block_map(cfg), pc, max(fn.instrs) + 1,
                               None, None, None, B._jmp_sites(fn), {})


def test_an_ambiguous_group_split_is_refused_rather_than_guessed():
    """Two refusals in `sir.build`, both proven load-bearing on this one input
    by neuter/restore (2026-08-14; the outputs are recorded in
    `_match_cond_chain`'s docstring).

    `if a and b or c then f() else g() end` compiles to (measured):
        1 GETGLOBAL a  2 TEST  3 JMP -> 7    <- A's false-exit, to C's code
        4 GETGLOBAL b  5 TEST  6 JMP -> 10   <- the AND's true-exit
        7 GETGLOBAL c  8 TEST  9 JMP -> 13   <- the chain's false-exit
        10-12 f()  13-14 g()  15 RETURN

    Retarget JMP@6 to 7 -- its own fall-through, which luac never emits, which
    is why this is hand-built -- and the chain becomes genuinely ambiguous:
    reading the group `[a, b]` as an `or`'s left operand gives `(a and b) or
    c`, reading it as an `and`'s gives `a and (b or c)`, and the jump targets
    support both. There is no evidence in the bytecode that picks one, so
    `_match_cond_chain` returns None and the caller re-raises.

    The unmutated control is asserted first, so this is a discrimination and
    not a function that returns None for everything.
    """
    import dataclasses

    fn = lift_proto(load_bytes(compile_source(
        b"if a and b or c then f() else g() end", strip=True)))
    assert fn.instrs[3].successors == (7,)
    assert fn.instrs[6].successors == (10,)
    assert fn.instrs[9].successors == (13,)
    got = _chain_at(fn, 2)
    assert got is not None and isinstance(got[0].cond, CondOp)      # control

    instrs = dict(fn.instrs)
    instrs[6] = dataclasses.replace(instrs[6], successors=(7,))
    assert _chain_at(dataclasses.replace(fn, instrs=instrs), 2) is None


def test_a_wrong_operator_cannot_ship(monkeypatch):
    """The injection that matters: break the RECOGNIZER's own output and show
    certification refuses it, so a bug here can only cost `L3`, never ship.

    `Reconstructor.cond_tree_expr` is patched to swap every `and` for an `or`
    and vice versa -- the exact mistake a mis-read jump target would make --
    and each fixture is then re-certified. Every one must drop out of `L3`.
    The clean run above it is the control.
    """
    from pyluadec.express.reconstruct import Reconstructor
    from pyluadec.express.expr import BinExpr
    from pyluadec.structure import structured as S

    cases = [b"if a and b then f() else g() end",
             b"if a or b then f() else g() end",
             b"if a and b or c then f() else g() end",
             b"if a or b and c then f() else g() end"]
    protos = [load_bytes(compile_source(c, strip=True)) for c in cases]
    clean = []
    for c, p in zip(cases, protos):
        assert certify_proto(p, is_chunk_root=True).level == "L3", c
        clean.append(print_chunk(p))

    real = Reconstructor.cond_tree_expr

    def swapped(self, node):
        e = real(self, node)
        if isinstance(e, BinExpr) and e.op in ("and", "or"):
            return BinExpr("or" if e.op == "and" else "and", e.lhs, e.rhs)
        return e

    monkeypatch.setattr(Reconstructor, "cond_tree_expr", swapped)
    S.clear_certification_cache()
    for c, p, before in zip(cases, protos, clean):
        # An injection that failed to apply would "pass" the line below while
        # proving nothing, so the change is asserted first.
        assert print_chunk(p) != before, f"the swap did not apply: {c!r}"
        assert certify_proto(p, is_chunk_root=True).level != "L3", (
            f"a swapped and/or survived certification: {c!r}")


def test_a_dropped_or_regrouped_operand_cannot_ship(monkeypatch):
    """The other two injections the brief names, at the same seam.

    `drop an arm`: return only the tree's LEFT subtree, so one operand of every
    compound condition vanishes. `mis-parenthesize`: re-associate
    `(x op y) op2 z` to `x op (y op2 z)`, which changes nothing about which
    tests run but changes which jump each one needs.

    Each case asserts that the injection ACTUALLY CHANGED the printed source
    before asserting that certification rejects it -- an injection that
    silently fails to apply would otherwise "pass" this test while proving
    nothing. (`if a or b and c` is deliberately not in the regrouped set: its
    tree is already right-leaning, `Or(a, And(b, c))`, so the re-association
    is a no-op on it -- measured 2026-08-14, and it certifies unchanged.)
    """
    from pyluadec.express.reconstruct import Reconstructor
    from pyluadec.express.expr import BinExpr
    from pyluadec.structure import structured as S

    dropped = [b"if a and b then f() else g() end",
               b"if a or b then f() else g() end"]
    regrouped = [b"if a and b or c then f() else g() end",
                 b"if (a or b) and c then f() else g() end"]
    real = Reconstructor.cond_tree_expr

    def drop_right(self, node):
        e = real(self, node)
        return e.lhs if isinstance(e, BinExpr) and e.op in ("and", "or") else e

    def reassociate(self, node):
        e = real(self, node)
        if isinstance(e, BinExpr) and e.op in ("and", "or") \
                and isinstance(e.lhs, BinExpr) and e.lhs.op in ("and", "or"):
            return BinExpr(e.lhs.op, e.lhs.lhs,
                           BinExpr(e.op, e.lhs.rhs, e.rhs))
        return e

    for patch, sources in ((drop_right, dropped), (reassociate, regrouped)):
        protos = [load_bytes(compile_source(c, strip=True)) for c in sources]
        S.clear_certification_cache()
        clean = []
        for c, p_ in zip(sources, protos):
            cert = certify_proto(p_, is_chunk_root=True)
            assert cert.level == "L3", c
            clean.append(print_chunk(p_))
        monkeypatch.setattr(Reconstructor, "cond_tree_expr", patch)
        S.clear_certification_cache()
        for c, p_, before in zip(sources, protos, clean):
            assert print_chunk(p_) != before, (
                f"{patch.__name__} did not change the printed source: {c!r}")
            assert certify_proto(p_, is_chunk_root=True).level != "L3", (
                f"{patch.__name__} survived certification: {c!r}")
        monkeypatch.undo()
        S.clear_certification_cache()


def test_a_true_exit_target_that_is_neither_the_then_block_nor_a_one_hop_jmp_refuses():
    """The recognizer resolves the chain's TRUE target as either the
    fall-through pc after the last JMP, or -- when a JMP sits there -- that
    JMP's own target (`luaK_jump` concatenates the pending truelist onto it).
    A chain whose jump matches neither, and does not land on a later span's
    start either, is NOT recognized: `_match_cond_chain` returns None and the
    caller re-raises the incumbent refusal rather than publishing a guess.

    Hand-built, because luac cannot emit it -- which is the point. The
    unmutated call is the positive control, so this is a discrimination and
    not a function that returns None for everything.

    `if a and b then f() else g() end` compiles to (measured 2026-08-14):
        1 GETGLOBAL a   2 TEST  3 JMP -> 10
        4 GETGLOBAL b   5 TEST  6 JMP -> 10      <- the chain's false exit
        7 GETGLOBAL f   8 CALL  9 JMP -> 12      <- the else-skip
        10 GETGLOBAL g  11 CALL              12 RETURN
    """
    import dataclasses

    from pyluadec.cfg import build_cfg, immediate_dominators
    from pyluadec.sir import build as B

    fn = lift_proto(load_bytes(compile_source(
        b"if a and b then f() else g() end", strip=True)))

    def _chain(f):
        cfg = build_cfg(f)
        return B._match_cond_chain(f, cfg, immediate_dominators(cfg),
                                   B._pc_block_map(cfg), 2, max(f.instrs) + 1,
                                   None, None, None, B._jmp_sites(f), {})

    got = _chain(fn)
    assert got is not None and isinstance(got[0].cond, CondOp)   # control

    instrs = dict(fn.instrs)
    instrs[3] = dataclasses.replace(instrs[3], successors=(8,))
    assert _chain(dataclasses.replace(fn, instrs=instrs)) is None

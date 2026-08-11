"""WhileTrue recognition. Fixtures are oracle-compiled; expected instruction
shapes were verified against luac_sz4 output on 2026-08-11 -- if luac emits
something different on your machine, the fixture comment is stale, not luac."""
import pytest
from pyluadec.oracle import compile_source
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.sir.build import build_sir, StructureError
from pyluadec.sir.regions import (While, WhileTrue, EndIter, Break, If, Seq,
                                  Straight, Return, all_claimed)


def _sir(src: bytes):
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)   # pc-claim audit, every fixture
    return fn, r


def _find(r, ty):
    # NOTE: only Seq.body is a tuple; WhileTrue.body / NumericFor.body /
    # GenericFor.body are single Region objects (same trap documented in
    # tests/test_sir_build_loops.py::_find).
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
            c = getattr(n, a, None)
            if c is not None:
                walk(c)
    walk(r)
    return out


def test_minimal_while_true():
    # 1 GETGLOBAL 2 LOADK 3 CALL 4 JMP->1 5 RETURN
    fn, r = _sir(b"while true do print(1) end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 4 and w.claimed_pcs == frozenset({4})


def test_empty_while_true():
    # 1 JMP->1 (S == L: the body is empty) 2 RETURN
    fn, r = _sir(b"while true do end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 1 and w.claimed_pcs == frozenset({1})
    assert all_claimed(w.body) == frozenset()


def test_while_true_with_break_in_if():
    # break JMP@5 targets 9 == closing_pc+1
    fn, r = _sir(b"while true do if f() then break end g() end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 8
    assert len(_find(w.body, Break)) == 1


def test_while_true_after_straight_line_code():
    # The header is NOT at a range start: `h()` precedes it, so the straight-run
    # accumulator has to stop at the header instead of swallowing it (it would
    # then hit the closing JMP as an unrecognized transfer and refuse).
    # 1-2 h() 3-4 g() 5 JMP->3 6 RETURN
    fn, r = _sir(b"h() while true do g() end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 5 and w.closing.successors == (3,)


def test_threaded_if_join_is_claimed_by_the_if():
    # `if c then x() end` as the WHOLE body: luac threads the if's false-exit
    # jump straight back to the header (luaK_jump concatenates the pending
    # jump list into the closing JMP's list, then patches the lot to the loop
    # header), producing a second backward JMP -> header at pc 4.
    # 1-2 f() 3 TEST 4 JMP->1 5-6 g() 7 JMP->1 8 RETURN
    fn, r = _sir(b"while true do if f() then g() end end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 7
    (i,) = _find(w.body, If)
    # The threaded jump is *claimed*, not refused -- by the If, as its
    # false-exit (see _structure_if's continue_target rewrite). It is not an
    # EndIter: an EndIter there would print as nothing and drop the `end`.
    assert i.claimed_pcs == frozenset({3, 4})
    assert _find(w.body, EndIter) == []


def test_threaded_else_skip_keeps_the_else_body():
    """if/else as the whole body of a `while true`: the else body [8,10) must
    not be lost. 1-2 f() 3 TEST 4 JMP->8 5-6 g() 7 JMP->1 8-9 h() 10 JMP->1

    M4 TASK 3 CHANGED WHICH READING WINS, and the shape turns out to be
    genuinely ambiguous rather than one of the two readings being wrong.
    `while true do if f() then g() else h() end end` and
    `while true do while f() do g() end h() end` compile to BYTE-IDENTICAL
    bytecode (asserted below, not argued): after `g()` control returns to the
    top of the enclosing loop and re-tests `f()`, which is exactly what a
    `while f()` header does. Task 1's recognizer had only the `If` reading
    available and picked it; `_match_while` is tried first now, so the `While`
    reading wins. Both certify L3 -- the whole point of the gate is that it
    does not care which of two equivalent sources produced the bytecode.

    What this test still guards, and what it was always really about, is that
    the else body is NOT amputated: the pc-claim audit in `_sir` covers every
    instruction, and the region carrying pcs 8-9 is asserted explicitly.
    """
    fn, r = _sir(b"while true do if f() then g() else h() end end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 10
    # The `while f() do g() end` reading: header 1-2, cond 3, exit-JMP 4,
    # body 5-6, closing 7. pcs 8-9 (`h()`) follow it inside the outer body.
    (inner,) = _find(w.body, While)
    assert inner.claimed_pcs == frozenset({1, 2, 3, 4, 7})
    assert all_claimed(inner.body) == frozenset({5, 6})
    assert (frozenset({8, 9}) & all_claimed(w.body)) == frozenset({8, 9})
    # The two sources really are the same bytecode.
    alt = compile_source(b"while true do while f() do g() end h() end", strip=True)
    assert alt == compile_source(
        b"while true do if f() then g() else h() end end", strip=True)


def test_threaded_jump_becomes_enditer():
    # The brief expected `while true do if f() then g() end end` to produce an
    # EndIter; it does not (see the test above -- the threaded jump there IS
    # the if's own false-exit and the If claims it, which is the only correct
    # reading: an EndIter there would print as nothing and drop the `end`).
    # This is a shape that really does produce one. Two loops sharing a header
    # (the inner loop is the outer's whole body), inner body = `if a() then
    # break else b() end`:
    # 1-2 a() 3 TEST 4 JMP->7 5 JMP->1 6 JMP->1 7-8 b() 9 JMP->1 10 JMP->1
    # pc 5 is the inner `break`; luac threaded it through the inner loop's
    # exit and the outer body's end onto the outer header, pc 1. It is claimed
    # as an EndIter of the INNER loop (whose header is pc 1 too) and prints as
    # nothing, which is faithful precisely because it sits in tail position:
    # falling out of the if ends the inner body, whose closing JMP@9 goes to
    # pc 1 as well.
    fn, r = _sir(b"while true do while true do if a() then break else b() end end end")
    inner = min(_find(r, WhileTrue), key=lambda w: w.closing.ri.pc)
    (e,) = _find(inner.body, EndIter)
    assert e.claimed_pcs == frozenset({5})


def test_non_tail_threaded_jump_refuses_rather_than_dropping_it():
    # Same shape with a statement after the inner if: pc 5 still jumps to the
    # shared header, but printing it as nothing would let f() run, which the
    # jump skips. An EndIter is only sound in tail position -- refuse.
    fn = lift_proto(load_bytes(compile_source(
        b"while true do while true do if a() then break else b() end f() end end",
        strip=True)))
    with pytest.raises(StructureError):
        build_sir(fn)


def test_nested_while_true():
    src = b"while true do while true do if f() then break end end if g() then break end end"
    fn, r = _sir(src)
    assert len(_find(r, WhileTrue)) == 2


def test_while_true_inside_an_if_body():
    # The inner loop's closing JMP@7 sits at the END of the then-body, where
    # _structure_if would otherwise mistake it for an else-skip (it jumps
    # backwards, so it cannot be one).
    # 1-2 a() 3 TEST 4 JMP->1 5-6 b() 7 JMP->5 8 JMP->1 9 RETURN
    fn, r = _sir(b"while true do if a() then while true do b() end end end")
    ws = _find(r, WhileTrue)
    assert sorted(w.closing.ri.pc for w in ws) == [7, 8]


def test_for_loop_inside_while_true():
    # A numeric for is the whole body; the while's closing JMP follows FORLOOP.
    fn, r = _sir(b"while true do for i = 1, 10 do f(i) end end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 9


def test_while_cond_is_recognized():
    """XFAIL LIFTED IN M4 TASK 3. `while <cond>` is a `While` region node now
    -- deliberately NOT the `WhileTrue` + leading-negated-If-Break desugaring
    the predecessor left open, which recompiles to three instructions where
    the original has two and can never certify (see `sir.regions.While`).

    Task 1's census also said "corpus has zero of these"; that was the
    measurement its own report retracted. `while <cond>` is the dominant
    corpus loop form: `_match_while` fires 195 times across 126 unique protos
    (measured 2026-08-11), and `_match_while_true`/`_match_repeat` fire zero
    times."""
    fn, r = _sir(b"local i = 1 while i < 10 do i = i + 1 end")
    (w,) = _find(r, While)
    # 1 LOADK  2 LT  3 JMP->6  4 ADD  5 JMP->2  6 RETURN
    assert w.header == ()                       # cond starts at the header pc
    assert w.cond.ri.pc == 2 and w.closing.ri.pc == 5
    assert w.claimed_pcs == frozenset({2, 3, 5})
    assert all_claimed(w.body) == frozenset({4})


def test_refusals_still_refuse():
    # `repeat` is recognized as of M4 task 3 (see test_sir_loops_longtail.py);
    # the acyclic TESTSET family stays refused until task 4.
    fn = lift_proto(load_bytes(compile_source(
        b"local a, b local x = a or b return x", strip=True)))
    with pytest.raises(StructureError, match="TESTSET"):
        build_sir(fn)


def test_conditional_exit_from_the_top_still_refuses():
    # `else break` threads the if's false-exit straight past the loop
    # (JMP@4 -> 10 == the loop exit), so the loop is left through a jump that
    # is neither the closing JMP nor a break *statement*. That is the same
    # shape as a `while <cond>` header and belongs to Task 3 -- until then it
    # must refuse rather than mis-claim.
    fn = lift_proto(load_bytes(compile_source(
        b"while true do if f() then g() else break end end", strip=True)))
    with pytest.raises(StructureError):
        build_sir(fn)


def test_pc_retreating_edge_that_is_not_a_dominance_back_edge_is_not_a_header():
    # The recognizer's back-edge test is dominance, not pc order. A generic
    # for's leading JMP is jumped OVER on entry and its body is re-entered by
    # a pc-retreating JMP -- but that JMP's target (the body head) is only a
    # loop header because it dominates the jump, which is exactly what
    # _match_while_true checks. Assert the for is still recognized as a for
    # (not hijacked into a WhileTrue by the pc-retreating edge alone).
    fn, r = _sir(b"for k, v in pairs(t) do f(k) end")
    from pyluadec.sir.regions import GenericFor
    assert len(_find(r, GenericFor)) == 1
    assert _find(r, WhileTrue) == []


def test_generic_for_back_edge_inside_if_is_recognized():
    """INVERTED IN M4 TASK 3, as its predecessor's docstring said it would be.

    M4 task 1 excluded exactly one shape from `_structure_if`'s "a backward
    trailing JMP belongs to the then-body" relaxation -- a generic-for's own
    trailing back edge sitting inside an `if` body -- via a
    `_is_generic_for_back_edge` guard whose only purpose was keeping
    `corpus/ledger.jsonl` frozen while task 1 landed (that proto has nothing
    unprintable left in it, so admitting it would have certified and moved a
    ledger row). Task 2 landed the loop printer and task 3 moves the ledger by
    design, so the guard expired and was deleted; this test is its inverse.

    Compiled shape, verified 2026-08-11 (unchanged from the predecessor):
        1 GETGLOBAL 2 TEST 3 JMP->13 4-6 f()'s callee/args 7 JMP->11
        8-10 pairs(t) call  11 TFORLOOP  12 JMP->8  13 RETURN
    pc 12 is the generic-for's back edge; it is the then-body's last
    instruction and targets pc 8, backwards, so it is now left inside the
    then-body (there is no else block) instead of being read as an else-skip
    to an out-of-range join.

    Corpus effect, measured: exactly one unique proto,
    `snr_common.lua:main_24_1` -- the brief's own scope-item-1 exemplar,
    whose refusal was `pc 2: else-join out of range` and whose shape is this
    one, not a distinct "rotated generic-for" defect.
    """
    fn = lift_proto(load_bytes(compile_source(
        b"if c then for k, v in pairs(t) do f(k) end end", strip=True)))
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    from pyluadec.sir.regions import GenericFor
    (g,) = _find(r, GenericFor)
    assert g.claimed_pcs == frozenset({7, 11, 12})


def test_unreachable_block_inside_a_loop_body_is_still_claimed():
    # luac emits a dead closing JMP for any `while true` body all of whose
    # paths break/return; when such a loop is nested, that dead JMP lands
    # INSIDE the outer loop's body. _verify_single_entry refuses unreachable
    # blocks for if/for bodies (M3) -- for a loop body it must not, or the
    # nested shape above is unrecognizable. This is the direct assertion of
    # that; test_nested_while_true is the end-to-end one.
    src = b"while true do while true do if f() then break end end if g() then break end end"
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    from pyluadec.cfg import build_cfg, immediate_dominators
    cfg = build_cfg(fn)
    idoms = immediate_dominators(cfg)
    dead = [b for b in cfg.blocks if b not in idoms]
    assert dead, "fixture no longer contains an unreachable block"
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert set(dead) <= all_claimed(r)


def test_reachable_non_dominating_block_inside_a_while_body_raises(monkeypatch):
    """Fix round finding (M4 task 3 review, Important 1, first half): the
    _verify_single_entry call inside _match_while that verifies the BODY
    (build.py, right after _match_while_header succeeds) was pinned by
    nothing -- the reviewer neutered it and got 76/76 tests passing and
    corpus acceptance unchanged at 1435/1478. This is the direct fixture: a
    block reachable from the function entry, but NOT through the loop
    header, lands in the MIDDLE of the while body.

    luac cannot emit this (a while body is always single-entry by
    construction), and unlike the dead-code trick used elsewhere in this file
    (a RETURN cutting off reachability so the "extra" pcs go UNREACHABLE,
    which _match_while's own allow_unreachable=True explicitly permits and so
    would NOT even exercise this guard) there is no way to construct a
    *reachable* multi-entry body through self-consistent bytecode routed
    end-to-end through build_sir's own dispatch: every real instruction whose
    target lands inside [body_lo, S) must itself be recognized by SOME
    recognizer, and every recognizer that could produce such a jump (an
    enclosing if's false-exit, a break, a continue) necessarily bounds its
    own recursive dispatch's `hi` to something <= that target -- too small
    for _match_while to ever see its own closing JMP S as a candidate, so the
    shape can never reach a genuinely-recognized While in the first place.
    (Confirmed by construction while writing this fixture.) This is the same
    impossibility test_verify_single_entry_catches_block_reachable_via_a_non_
    dominating_path in test_sir_build_acyclic.py already documents for If,
    one level simpler -- that test sidesteps it by calling
    _verify_single_entry directly instead of through build_sir.

    This fixture routes through the REAL build_sir entry point anyway: fn's
    instructions are real (mk_instr/lift_proto) and drive everything build_sir
    does NOT get from the CFG (opcode dispatch, straight-run accumulation,
    _jmp_sites, _exits_only_to). Only the CFG/dominance machinery is
    hand-built (tests/synth.py's mk_cfg) and substituted via monkeypatch for
    build_cfg / immediate_dominators / _pc_block_map, so build_sir sees a
    deliberately-impossible-for-luac CFG layered onto a self-consistent
    instruction stream.
    """
    from tests.synth import mk_instr, mk_proto, mk_cfg
    from pyluadec.lift import lift_proto, Op
    from pyluadec.cfg import immediate_dominators
    import pyluadec.sir.build as build_mod

    words = [
        mk_instr(Op.LT, a=1, b=0, c=1, pc=1).word,    # cond_pc=1, empty header
        mk_instr(Op.JMP, sbx=6 - 2 - 1, pc=2).word,    # jmp_pc=2 -> 6 (exit)
        mk_instr(Op.MOVE, a=0, b=1, pc=3).word,        # body_lo=3
        mk_instr(Op.MOVE, a=0, b=1, pc=4).word,        # body interior -- the intruded pc
        mk_instr(Op.JMP, sbx=1 - 5 - 1, pc=5).word,    # closing S=5 -> 1
        mk_instr(Op.RETURN, a=0, b=1, pc=6).word,      # exit
    ]
    fn = lift_proto(mk_proto(words, maxstacksize=4))
    edges = {
        0: (1, 99),   # function entry reaches both the loop header and the intruder
        1: (2, 3),    # cond_pc's real successors (jmp_pc, body_lo)
        2: (6,),
        3: (4, 5),    # body_lo -> body interior, AND a synthetic direct edge to
                      # S (keeps S's own dominance clean of the tainted node
                      # below -- S must stay a valid back-edge candidate)
        4: (),        # body interior: a dead end in this synthetic graph
        5: (),
        6: (),
        99: (4,),     # THE INTRUDER: reaches the body interior without going
                      # through the loop header at all
    }
    cfg = mk_cfg(edges, entry=0)
    idoms = immediate_dominators(cfg)
    pc2blk = {s: s for s in edges}
    assert idoms[4] == 0 and not build_mod.dominates(idoms, 1, 4), \
        "sanity: pc 4 must be reachable but NOT dominated by pc 1's block"

    monkeypatch.setattr(build_mod, "build_cfg", lambda fn_: cfg)
    monkeypatch.setattr(build_mod, "immediate_dominators", lambda cfg_: idoms)
    monkeypatch.setattr(build_mod, "_pc_block_map", lambda cfg_: pc2blk)

    with pytest.raises(StructureError, match="not dominated"):
        build_sir(fn)

    monkeypatch.setattr(build_mod, "_verify_single_entry", lambda *a, **k: None)
    region = build_sir(fn)             # must NOT raise once the guard is neutered
    (w,) = _find(region, While)
    assert 4 in w.body.claimed_pcs, \
        "neutered run did not even claim the intruded pc -- fixture stopped exercising the guard"


def test_reachable_jump_into_the_middle_of_a_while_header_raises(monkeypatch):
    """Fix round finding (M4 task 3 review, Important 1, second half): the
    block-uniformity check in _match_while_header (build.py -- "the header is
    one basic block", the second of its docstring's "two proofs required
    beyond the opcode pattern") was likewise pinned by nothing -- the
    reviewer deleted that hunk and got the identical 76/76 passed,
    1435/1478. Direct fixture: an outside jump lands on the SECOND
    instruction of a two-instruction while header (the `while f() do ... end`
    shape, non-empty header), splitting it into two CFG blocks.

    Same impossibility-via-self-consistent-bytecode argument as
    test_reachable_non_dominating_block_inside_a_while_body_raises applies
    here (any real recognized construct whose jt lands inside the header
    entangles the recursive dispatch the same way -- confirmed by
    construction), so this uses the identical hand-built-CFG-through-
    build_sir technique.

    The guard itself is inline (`if any(pc2blk[p] != header_blk for p in
    header_pcs + [cond_pc]): return None`), not a separately-callable
    function, so "neutered" here is a verbatim copy of _match_while_header
    with exactly that check deleted -- the same edit the reviewer applied
    directly to source before rerunning the corpus.
    """
    from tests.synth import mk_instr, mk_proto, mk_cfg
    from pyluadec.lift import lift_proto, Op
    from pyluadec.cfg import immediate_dominators
    import pyluadec.sir.build as build_mod

    words = [
        mk_instr(Op.MOVE, a=0, b=1, pc=1).word,       # header op1, lo=1
        mk_instr(Op.MOVE, a=0, b=1, pc=2).word,       # header op2 -- the intruded pc
        mk_instr(Op.LT, a=1, b=0, c=1, pc=3).word,    # cond_pc=3
        mk_instr(Op.JMP, sbx=7 - 4 - 1, pc=4).word,   # jmp_pc=4 -> 7 (exit)
        mk_instr(Op.MOVE, a=0, b=1, pc=5).word,       # body_lo=5
        mk_instr(Op.JMP, sbx=1 - 6 - 1, pc=6).word,   # closing S=6 -> 1
        mk_instr(Op.RETURN, a=0, b=1, pc=7).word,     # exit
    ]
    fn = lift_proto(mk_proto(words, maxstacksize=4))
    edges = {
        0: (1, 99),
        1: (2, 3),    # header op1 -> header op2 (normal), AND a synthetic
                      # direct edge to cond_pc (keeps everything downstream of
                      # the tainted node dominated, so ONLY the header check
                      # -- not the earlier back-edge precondition -- is what
                      # is on trial)
        2: (),        # dead end -- doesn't need to forward anywhere for the
                      # uniformity check to see it as a distinct, reachable block
        3: (4, 5),
        4: (7,),
        5: (6,),
        6: (1,),
        7: (),
        99: (2,),     # THE INTRUDER: lands on the header's second instruction
    }
    cfg = mk_cfg(edges, entry=0)
    idoms = immediate_dominators(cfg)
    pc2blk = {s: s for s in edges}
    assert pc2blk[2] != pc2blk[1], "sanity: intruded pc must be a distinct block"

    monkeypatch.setattr(build_mod, "build_cfg", lambda fn_: cfg)
    monkeypatch.setattr(build_mod, "immediate_dominators", lambda cfg_: idoms)
    monkeypatch.setattr(build_mod, "_pc_block_map", lambda cfg_: pc2blk)

    with pytest.raises(StructureError):
        build_sir(fn)

    def _match_while_header_minus_uniformity_check(fn_, pc2blk_, lo, S, hi, continue_target):
        header, header_pcs = [], []
        pc = lo
        while pc < S:
            li = fn_.instrs[pc]
            if li.ri.op in build_mod._COMPARE:
                break
            if len(li.successors) != 1 or li.successors[0] != pc + 1 + len(li.consumed):
                return None
            header.append(li)
            header_pcs.append(pc)
            pc += 1 + len(li.consumed)
        else:
            return None
        cond_pc = pc
        jmp_pc = cond_pc + 1
        if jmp_pc >= S or jmp_pc not in fn_.instrs or fn_.instrs[jmp_pc].ri.op is not Op.JMP:
            return None
        exit_pc = fn_.instrs[jmp_pc].successors[0]
        if continue_target is not None and exit_pc == continue_target:
            exit_pc = hi
        if exit_pc != S + 1:
            return None
        # block-uniformity check (build.py's "the header is one basic block"
        # proof) deliberately omitted -- this is the neutered copy.
        return tuple(header), tuple(header_pcs), cond_pc, jmp_pc, exit_pc

    monkeypatch.setattr(build_mod, "_match_while_header",
                        _match_while_header_minus_uniformity_check)
    region = build_sir(fn)             # must NOT raise once the guard is neutered
    (w,) = _find(region, While)
    assert [li.ri.pc for li in w.header] == [1, 2], \
        "neutered run did not even claim the intruded pc as header -- fixture stopped exercising the guard"


def test_nested_loop_backtracking_does_not_blow_up(monkeypatch):
    """`_match_while_true` validates each closing-JMP candidate by structuring
    the body, so nesting multiplies the work unless results are cached. This
    pins that they are: the number of `_structure_range_impl` calls must stay
    LINEAR in nesting depth, not exponential.

    Measured 2026-08-11: 18 / 34 / 50 calls at depth 4 / 8 / 12 (4d + 2).
    Without the memo the same shape cost 0.011s / 0.047s / 0.207s of wall
    clock at depth 6 / 8 / 10 -- a clean 4x per two levels, minutes by depth
    20. Asserting the call count rather than a wall clock keeps this
    deterministic on a loaded machine."""
    import pyluadec.sir.build as build_mod
    body = "if a() then break end"
    for _ in range(12):
        body = ("while true do while true do " + body + " end "
                + "f() " * 4 + " if b() then break end end")
    fn = lift_proto(load_bytes(compile_source(body.encode(), strip=True)))
    calls = []
    orig = build_mod._structure_range_impl

    def counting(*a, **k):
        calls.append(1)
        return orig(*a, **k)

    monkeypatch.setattr(build_mod, "_structure_range_impl", counting)
    try:
        build_sir(fn)
    except StructureError:
        pass                       # this shape refuses; the COST is the point
    assert len(calls) < 200, f"{len(calls)} calls -- memoization regressed?"


def test_corpus_build_sir_acceptance_floor(corpus_dir):
    """Committed census: build_sir acceptance over unique protos must not fall
    below the measured floor. M3 baseline: 1309/1478; measured after task 1:
    1309/1478 -- unchanged, see the floor comment below for why. (The brief
    named this test `..._grows`; it does not grow, and calling it that would
    be the assertion doing the measuring rather than the other way round.)"""
    from pyluadec.pipeline import walk_proto_paths
    from pyluadec.ingest import load_file
    from pyluadec.verify.ledger import structural_hash
    uniq = {}
    for f in sorted(corpus_dir.glob("*.lua")):
        protos = {}
        walk_proto_paths("main", load_file(f), protos)
        for path, p in protos.items():
            uniq.setdefault(structural_hash(p), p)
    ok = 0
    for p in uniq.values():
        try:
            fn = lift_proto(p)
            r = build_sir(fn)
            assert all_claimed(r) == set(fn.instrs)
            ok += 1
        except StructureError:
            pass
    print(f"build_sir accepts {ok}/{len(uniq)} unique protos")
    # M4 TASK 3 MOVED THIS. History and the measurements behind it:
    #   M3 baseline / after task 1 / after task 2:  1309
    #   after task 3 (`While` + `Repeat` recognition, generic-for back-edge
    #   exclusion removed, dead-closing-JMP relaxation):  1435
    #
    # Where the 126 came from, measured 2026-08-11 by instrumenting the three
    # loop recognizers inside real `build_sir` runs over all 1478 unique
    # protos:
    #     _match_while       195 matches across 126 unique protos
    #     _match_while_true    0 matches
    #     _match_repeat        0 matches
    # (+1 more from removing the generic-for back-edge exclusion:
    #  snr_common.lua:main_24_1.) So the corpus's loops are `while <cond>`
    # and nothing else -- task 1's corrected census (134 protos) stands as
    # the right order of magnitude; the exact figure this recognizer reaches
    # is 126, and the difference is protos that contain a `while <cond>` AND
    # something else still refused.
    #
    # The 43 that remain refuse for reasons this task did not address:
    #     15  "if targets out of range", ALL of them jt > hi -- an `if` whose
    #         false-exit was threaded onto an enclosing `if`'s else-skip
    #         (the same luaK_jump jpc mechanism `_structure_if` already
    #         handles for loop headers, one level up). NOT one of them is
    #         `jt == break_target`.
    #     10  "else-join out of range"
    #      8  "unrecognized transfer TESTSET"   (M4 task 4)
    #     10  "branch body block ... is unreachable"
    #
    # Floor is measured-minus-10, a ratchet against regression rather than a
    # claim of growth (same protocol as the previous value).
    assert ok >= 1425   # measured after task 3: 1435

"""Loop printing (`while true`, threaded end-of-iteration jumps, `repeat`),
adjudicated by the real L3 gate rather than by prose.

Every fixture is oracle-compiled and then either certified end-to-end
(`certify_proto(..., is_chunk_root=True)`: recompiled with the real
`luac_sz4`, compared field-by-field under the versioned normalization ladder)
or -- for `Repeat`, which `build_sir` does not construct yet (Task 3) --
printed from a hand-assembled region tree and put through that same
`compare_protos` ladder. Nothing here relaxes the gate; a fixture that will
not certify is a defect on the reconstruction/printing side.

All fixture sources are pure ASCII by construction, so the assertions that
inspect printed text may decode; bytecode-derived strings elsewhere in the
project stay `bytes`.
"""
import pytest

from pyluadec.emit.lua import print_chunk, print_function
from pyluadec.express.names import classify_registers
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.sir.build import build_sir
from pyluadec.sir.regions import (EndIter, Repeat, Return, Seq, Straight,
                                  WhileTrue, all_claimed)
from pyluadec.structure.structured import certify_proto, emit_certified_chunk
from pyluadec.verify.normalize import NORMALIZATIONS, compare_protos

# Every one of these certifies L3 (measured 2026-08-11, M4 tasks 2 and 13).
#
# The last two entries were originally excluded. `local NAME = <call>` did not
# certify -- with or without a loop -- because `classify_registers` was
# whole-function and per register *number*, so the register luac writes twice
# (GETGLOBAL then CALL in place) came out a local and the printer emitted
# `local l0_0 = h` + `l0_0 = l0_0()`, four instructions where the original had
# two. M4 task 13 made classification per definition and both shapes certify,
# so they are folded back in here as the test that used to record the gap
# instructed (`test_local_bound_to_a_call_is_a_pre_existing_gap_not_a_loop_defect`,
# deleted with its EXPIRY condition met).
CASES = [
    b"while true do print(1) end",                                    # unreachable RETURN after loop
    b"while true do end",                                             # empty body
    b"h() while true do g() end",                                     # header mid straight-run
    b"while true do if f() then break end g() end",
    b"while true do if f() then g() end end",                         # threaded false-exit
    b"while true do if f() then g() else h() end end",                # threaded else-skip
    b"while true do if a then break end if b then break end f() end",
    b"local n = 0 while true do n = n + 1 if n > 3 then break end end print(n)",
    b"local t = {} while true do t.n = t.n + 1 if t.n > 2 then break end end print(t.n)",
    b"while true do for i = 1, 10 do f(i) end end",                   # numeric for in a while body
    b"while true do if a then while true do b() end end end",         # while inside an if arm
    b"while true do while true do if a then f() else break end end end",
    b"while true do while true do if a then g() else b() end end end",
    b"while true do while true do if a then break else b() end end c() end",
    # A body-local whose register is reused by a DIFFERENT local after the
    # loop -- the direct regression for close_scope; see
    # test_body_local_register_reused_after_the_loop.
    b"while true do local x = 1 f(x, x) if b then break end end local y = 2 f(y, y)",
    # Formerly the two "pre-existing gap" shapes; see the note above.
    b"local a = f() print(a)",                                        # no loop at all
    b"while true do local x = h() if x then break end end",
]


def test_while_fixtures_certify_l3():
    for src in CASES:
        p = load_bytes(compile_source(src, strip=True))
        cert = certify_proto(p, is_chunk_root=True)
        assert cert.level == "L3", (src, cert.mismatches)


def test_while_output_runs_identically():
    src = b"local n = 0 while true do n = n + 1 if n > 3 then break end end print(n)"
    p = load_bytes(compile_source(src, strip=True))
    out = emit_certified_chunk(p)
    # `ChunkOutcome` has no `.structured` flag: "the artifact is structured"
    # IS "the root certified L3" (structure/structured.py's invariant).
    assert out.certs["main"].level == "L3"
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(out.source, is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode)
    assert a.stdout.split() == [b"4"]


def test_body_local_register_reused_after_the_loop():
    """Loop bodies are their own Lua block: `close_scope` at `end`.

    Register 0 here is a body-local inside the loop and a *different* local
    after it. Without restoring `declared`, the second one prints as a bare
    `l0_0 = ...`, which Lua parses as a write to a GLOBAL (SETGLOBAL where the
    original had a register write) -- silently wrong code that only the
    certification gate would stop from shipping. Certifying L3 is the proof it
    does not happen; the textual assertions make a regression legible.
    """
    src = b"while true do local x = 1 f(x, x) if b then break end end local y = 2 f(y, y)"
    p = load_bytes(compile_source(src, strip=True))
    out = emit_certified_chunk(p)
    assert out.certs["main"].level == "L3", out.certs["main"].mismatches
    text = out.source.decode("ascii")           # fixture is pure ASCII by construction
    # Two separate `local` declarations, and the first one is inside the loop
    # (a leak would print the second as a bare assignment, i.e. one `local`).
    assert text.count("local ") == 2
    assert text.index("local ") > text.index("while true do")
    assert text.rindex("local ") > text.index("\nend")


# ---- EndIter -------------------------------------------------------------
_ENDITER_SRC = b"while true do while true do if a then break else b() end end end"


def _count(r, ty):
    n = 1 if isinstance(r, ty) else 0
    body = getattr(r, "body", None)
    if isinstance(body, tuple):                 # only Seq.body is a tuple
        for c in body:
            n += _count(c, ty)
    elif body is not None:
        n += _count(body, ty)
    for attr in ("then_body", "else_body"):
        c = getattr(r, attr, None)
        if c is not None:
            n += _count(c, ty)
    return n


def test_enditer_prints_nothing():
    """`EndIter` contributes no line to the output.

    The shape: two `while true` loops sharing a header (the inner loop is the
    outer's whole body). luac threads the inner `break` through the inner
    loop's exit and the outer body's end onto that shared header, so it
    survives as a bare backward JMP the recognizer claims as an `EndIter`
    (tests/test_sir_while.py::test_threaded_jump_becomes_enditer pins the
    recognition side).

    The soundness argument for printing nothing is checked mechanically below
    rather than asserted in prose: the dropped jump's target and the target
    reached by falling out of the printed block (the loop's own closing JMP)
    are the same pc, so executing nothing in its place goes where it went.
    """
    p = load_bytes(compile_source(_ENDITER_SRC, strip=True))
    fn = lift_proto(p)
    region = build_sir(fn)
    assert _count(region, EndIter) == 1, "fixture no longer contains an EndIter"

    # Mechanical soundness check: the EndIter's JMP and the innermost loop's
    # closing JMP go to the same pc.
    enditer_pc, = (pc for pc in fn.instrs
                   if _count(region, EndIter) and pc in _enditer_pcs(region))
    inner = min(_whiletrues(region), key=lambda w: w.closing.ri.pc)
    assert fn.instrs[enditer_pc].successors == inner.closing.successors

    src = print_chunk(p)
    assert src is not None                      # the printer does not refuse
    assert src == ("while true do\n"
                   "  while true do\n"
                   "    if a then\n"            # <- the EndIter's arm: empty
                   "    else\n"
                   "      b()\n"
                   "    end\n"
                   "  end\n"
                   "end\n")


def _enditer_pcs(r):
    out = set()
    if isinstance(r, EndIter):
        out |= set(r.claimed_pcs)
    body = getattr(r, "body", None)
    if isinstance(body, tuple):
        for c in body:
            out |= _enditer_pcs(c)
    elif body is not None:
        out |= _enditer_pcs(body)
    for attr in ("then_body", "else_body"):
        c = getattr(r, attr, None)
        if c is not None:
            out |= _enditer_pcs(c)
    return out


def _whiletrues(r):
    out = [r] if isinstance(r, WhileTrue) else []
    body = getattr(r, "body", None)
    if isinstance(body, tuple):
        for c in body:
            out += _whiletrues(c)
    elif body is not None:
        out += _whiletrues(body)
    for attr in ("then_body", "else_body"):
        c = getattr(r, attr, None)
        if c is not None:
            out += _whiletrues(c)
    return out


def test_enditer_shape_does_not_certify_and_therefore_ships_fallback():
    """Measured contradiction of the brief (2026-08-11), recorded rather than
    papered over: the brief said an EndIter fixture "must certify L3". No
    `while true` shape that produces an EndIter does.

    Reason, and it is structural, not a bug in this printer: within a `while
    true` family the ONLY jumps luac leaves pending on the loop header other
    than those an `If` already claims (its false-exit, its else-skip) are an
    *inner loop's* `break`s, threaded there by `leaveblock` when nothing
    follows the inner loop in the outer body. Printing such a jump as nothing
    is semantically faithful (both it and the fall-through reach the same pc
    -- asserted in test_enditer_prints_nothing) but the recompiled source has
    no `break` at that spot, so it is one JMP shorter and the cert fails on
    `code`. A search over 54 generated nested-loop shapes found 4 that produce
    an EndIter and structure; all 4 certify L1.

    The invariant still holds and is what this test really guards: the
    uncertified structured print does NOT ship -- the M2 fallback does.

    EXPIRY DISCHARGED, NOT LIFTED (M4 task 3). The expiry note here said
    task 3's `while <cond>` loops "may well produce an EndIter that
    certifies". They do not, and the evidence went the other way: measured on
    `while true do while true do if a then f() else break end end end`, a
    `While` whose body ends in an EndIter recompiles one JMP short and drops
    that fixture from L3 to L1, exactly as this test's mechanism predicts.
    `_match_while` therefore REFUSES any body with an EndIter of its own
    (stricter than `_match_while_true`'s tail-position rule) rather than
    preempt a reading that can certify. So the L1 assertion below stands on
    strictly more evidence than before; the next thing that could lift it is
    an emitter that can express the extra threaded jump, not another loop
    recognizer. The fallback-shipping assertion is permanent.
    """
    p = load_bytes(compile_source(_ENDITER_SRC, strip=True))
    cert = certify_proto(p, is_chunk_root=True)
    assert cert.level == "L1"
    assert cert.mismatches and cert.mismatches[0].field == "code"
    out = emit_certified_chunk(p)
    assert out.certs["main"].level == "L1"
    assert out.source.startswith(b"local __pld_")   # the M2 fallback preamble


# ---- Repeat -------------------------------------------------------------
# `build_sir` does not construct a `Repeat` yet (recognition is Task 3), so
# the printer arm is exercised from a hand-assembled region tree. The check is
# still the real one: recompile the printed chunk with luac_sz4 and run it
# through the same `compare_protos` ladder `verify.certify` uses.

_REPEAT_SRC = b"local i = 0 repeat i = i + 1 print(i) until i > 2"


def _repeat_region(fn):
    """The region tree `build_sir` will build for `_REPEAT_SRC` once Task 3
    recognizes `repeat`. Shape verified against luac_sz4 on 2026-08-11:

        1 LOADK 0 K0        (local i = 0)
        2 ADD 0 0 K1        \\
        3 GETGLOBAL 1 print  |  repeat body, [2, 6)
        4 MOVE 2 0           |
        5 CALL 1 2 1        /
        6 LT 0 K3 0         (the bottom condition, `2 < i`; A==0)
        7 JMP -> 2          (the conditional backward jump closing the loop)
        8 RETURN 0 1        (luac's implicit trailing return)
    """
    body = Straight(tuple(fn.instrs[pc] for pc in range(2, 6)),
                    frozenset(range(2, 6)))
    rep = Repeat(body=body, cond=fn.instrs[6],
                 negated=(fn.instrs[6].ri.a == 0), closing=fn.instrs[7],
                 claimed_pcs=frozenset({6, 7}))
    return Seq((Straight((fn.instrs[1],), frozenset({1})), rep,
                Return(fn.instrs[8], frozenset({8}))), frozenset())


def _print_repeat_fixture():
    p = load_bytes(compile_source(_REPEAT_SRC, strip=True))
    fn = lift_proto(p)
    region = _repeat_region(fn)
    assert all_claimed(region) == set(fn.instrs)
    return p, print_function(fn, region, classify_registers(fn), 0).encode()


def test_repeat_prints_and_recompiles_to_the_original():
    """Polarity pin, adjudicated rather than argued.

    `until <cond>` takes the loop-EXIT condition, which is exactly the
    "fallthrough past the JMP" expression `If` already computes: `repeatstat`
    patches `luaK_goiftrue`'s FALSE list back to the loop header, so the
    backward JMP is taken when the source condition is false and falling
    through means leaving the loop. Hence `condition()` is reused un-negated.

    A sign-flipped `until` still compiles -- it just compiles to `LT 1 ...`
    instead of `LT 0 ...`, which comparing the recompiled proto catches.

    The expected text says `until l0_0 > 2`, not `until 2 < l0_0`, since M5
    task 5: the fixture's source is `until i > 2` and `_reads_as_gt` now
    recovers the `>`. Both forms compile to the same instruction (see that
    method), so this line of the assertion is about faithfulness, and the
    recompile comparison below is what pins polarity.
    """
    original, printed = _print_repeat_fixture()
    assert printed == (b"local l0_0 = 0\n"
                       b"repeat\n"
                       b"  l0_0 = l0_0 + 1\n"
                       b"  print(l0_0)\n"
                       b"until l0_0 > 2\n")
    candidate = load_bytes(compile_source(printed, strip=True))
    for k in range(len(NORMALIZATIONS) + 1):
        if not compare_protos(original, candidate, level=k):
            break
    else:
        pytest.fail("repeat print did not recompile to the original: "
                    f"{compare_protos(original, candidate, level=len(NORMALIZATIONS))}")


def test_repeat_output_runs_identically():
    _, printed = _print_repeat_fixture()
    a = run_bytes(compile_source(_REPEAT_SRC, strip=True), is_source=False)
    b = run_bytes(printed, is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode)
    # A sign-flipped `until` compiles and exits after ONE iteration; pinning
    # the actual output is what makes the polarity visible rather than merely
    # syntactically plausible.
    assert a.stdout.split() == [b"1", b"2", b"3"]


def test_repeat_condition_is_printed_inside_the_body_scope():
    """`until`'s condition is read INSIDE the repeat block (`lparser.c`'s
    `repeatstat`: `enterblock` ... `chunk` ... `cond` ... `leaveblock`), which
    is why `repeat local a = f() until a` is legal Lua. The printer must
    therefore render the condition BEFORE `close_scope`.

    This fixture pins it observably: `y`'s `GETGLOBAL` is the body's last
    instruction and register 0 is a genuine `rc.temps` member here, so the
    condition's operand is a *staged* expression that lives only in
    `Reconstructor.env`. Closing the scope first restores `env` from the
    snapshot, the staged temp is gone, and `cond_operand` raises "temp
    register 0 read before it was staged" (verified by inverting the two
    lines, M4 task 2). A body *local* would not expose the inversion: a
    register merely dropped from `declared` still prints as `l0_N`, and it is
    still in scope in the printed Lua, so text and recompile are unchanged.
    """
    src = b"repeat f() until y == 1 g()"
    p = load_bytes(compile_source(src, strip=True))
    fn = lift_proto(p)
    rc = classify_registers(fn)
    assert 0 in rc.temps, "fixture no longer stages the condition operand"
    pcs = sorted(fn.instrs)
    cond_pc, = (pc for pc in pcs if fn.instrs[pc].ri.op.name == "EQ")
    body = Straight(tuple(fn.instrs[pc] for pc in range(pcs[0], cond_pc)),
                    frozenset(range(pcs[0], cond_pc)))
    rep = Repeat(body=body, cond=fn.instrs[cond_pc],
                 negated=(fn.instrs[cond_pc].ri.a == 0),
                 closing=fn.instrs[cond_pc + 1],
                 claimed_pcs=frozenset({cond_pc, cond_pc + 1}))
    tail = range(cond_pc + 2, pcs[-1])
    region = Seq((rep,
                  Straight(tuple(fn.instrs[pc] for pc in tail), frozenset(tail)),
                  Return(fn.instrs[pcs[-1]], frozenset({pcs[-1]}))), frozenset())
    assert all_claimed(region) == set(fn.instrs)
    printed = print_function(fn, region, rc, 0).encode()
    assert printed == b"repeat\n  f()\nuntil y == 1\ng()\n"
    candidate = load_bytes(compile_source(printed, strip=True))
    assert not compare_protos(p, candidate, level=0), printed

"""M4 task 3: `while <cond>` and `repeat` recognition, adjudicated by the L3 gate.

Every fixture is oracle-compiled with the real `luac_sz4` and asserts BOTH
halves of the discipline this project runs on:

  * `all_claimed(build_sir(fn)) == set(fn.instrs)` -- the pc-claim audit, so a
    recognizer that quietly drops an instruction is caught even when the
    printed source happens to look right; and
  * `certify_proto(..., is_chunk_root=True).level == "L3"` -- the printed
    source, recompiled by `luac_sz4`, is equal to the original proto
    field-by-field under the versioned normalization ladder.

Nothing here relaxes the gate. A shape that does not certify is recorded as a
known gap with its measured cause and an expiry, never asserted away.

All fixture sources are pure ASCII by construction, so assertions that inspect
printed text may decode; bytecode-derived strings elsewhere stay `bytes`.
"""
import pytest

from pyluadec.emit.lua import print_chunk
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.sir.build import StructureError, build_sir
from pyluadec.sir.regions import (Break, GenericFor, NumericFor, Repeat, While,
                                  WhileTrue, all_claimed)
from pyluadec.structure.structured import certify_proto


def _sir(src: bytes):
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)   # pc-claim audit, every fixture
    return fn, r


def _find(r, ty):
    # Only Seq.body is a tuple; every other `body` is a single Region (the
    # trap documented in tests/test_sir_build_loops.py::_find).
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


# ---------------------------------------------------------------- while <cond>

# Each entry certifies L3 (measured 2026-08-11, M4 task 3). The list is the
# shape census this task was written against: header forms (bare local
# compare, call, `not`, indexed), body forms (empty-ish, if, if/else, break,
# return), and every nesting combination with the loop kinds that already
# existed.
WHILE_CASES = [
    b"local i = 1 while i < 10 do i = i + 1 end",              # minimal
    b"while f() do g() end",                                   # call header
    b"while not a do f() end",                                 # negated header
    b"while a.b[c] do f() end",                                # multi-instr header
    b"local t = {} while t.n do t.n = t.n - 1 end",
    b"local i = 1 while i < 10 do i = i + 1 if i == 5 then break end end",
    b"while a do if b then break end f() end",
    b"while a do if b then break else f() end end",
    b"while a do f() return end",                              # dead closing JMP
    b"local i = 0 while i < 3 do i = i + 1 end return i",
    b"while a do f() end g()",                                 # code after
    b"h() while a do f() end",                                 # header mid-run
    b"while a do if b then c() end end",                       # threaded false-exit
    b"while a do if b then c() else d() end end",              # threaded else-skip
    b"while a do while b do c() end end",                      # nested
    b"while a do while b do while c do f() end end end",       # triple
    b"for i=1,10 do while a do f() end end",                   # while in numeric for
    b"while true do while a do f() end end",                   # shared header
    b"while true do while a do f() end g() end",
    # A body-local whose register is reused by a different local after the
    # loop -- the `close_scope` regression, restated for `While`.
    b"local i = 0 while i < 3 do local x = i * 2 f(x) i = i + 1 end local y = 9 f(y)",
]


@pytest.mark.parametrize("src", WHILE_CASES, ids=range(len(WHILE_CASES)))
def test_while_cond_fixture_claims_every_pc_and_certifies(src):
    _sir(src)                                    # pc-claim audit
    cert = certify_proto(load_bytes(compile_source(src, strip=True)),
                         is_chunk_root=True)
    assert cert.level == "L3", (src, cert.mismatches)


def test_while_cond_region_shape():
    """The `While` node's fields, on the canonical shape.

    1 LOADK  2 LT  3 JMP->6  4 ADD  5 JMP->2  6 RETURN
    `header` is empty here because the condition's operands are already in
    registers; `while a.b[c] do` below is the case where it is not.
    """
    fn, r = _sir(b"local i = 1 while i < 10 do i = i + 1 end")
    (w,) = _find(r, While)
    assert w.header == ()
    assert w.cond.ri.pc == 2
    assert w.closing.ri.pc == 5 and w.closing.successors == (2,)
    assert w.claimed_pcs == frozenset({2, 3, 5})       # cond + exit-JMP + closing
    assert all_claimed(w.body) == frozenset({4})


def test_while_header_code_is_claimed_by_the_loop_not_by_a_sibling():
    """The condition's operand code re-runs every iteration, so it belongs to
    the `While` -- not to a `Straight` in front of it, which would print those
    instructions once, before the loop.

    1 GETGLOBAL a  2 GETTABLE "b"  3 GETGLOBAL c  4 GETTABLE  5 TEST
    6 JMP->10  7-8 f()  9 JMP->1  10 RETURN
    """
    fn, r = _sir(b"while a.b[c] do f() end")
    (w,) = _find(r, While)
    assert tuple(i.ri.pc for i in w.header) == (1, 2, 3, 4)
    assert w.cond.ri.pc == 5
    assert w.claimed_pcs == frozenset({1, 2, 3, 4, 5, 6, 9})
    src = print_chunk(load_bytes(compile_source(b"while a.b[c] do f() end", strip=True)))
    assert src is not None
    # One line, and the whole header is inside it -- which is what this test is
    # about. The spelling of the index is not: `a.b` since M5 task 7's dot
    # sugar (`t["k"]` -> `t.k` for a constant string key that is a Lua Name),
    # `a["b"]` before it. `[c]` stays bracketed because `c` is a register, not
    # a constant.
    assert src.splitlines()[0] == "while a.b[c] do"


def test_while_cond_body_break_is_a_break():
    fn, r = _sir(b"local i = 1 while i < 10 do i = i + 1 if i == 5 then break end end")
    (w,) = _find(r, While)
    assert len(_find(w.body, Break)) == 1


def test_nested_while_cond_and_for_kinds():
    fn, r = _sir(b"for i=1,10 do while a do f() end end")
    assert len(_find(r, NumericFor)) == 1 and len(_find(r, While)) == 1
    fn, r = _sir(b"while true do while a do f() end g() end")
    assert len(_find(r, WhileTrue)) == 1 and len(_find(r, While)) == 1


def test_while_cond_output_runs_identically():
    src = b"local i = 0 local n = 0 while i < 4 do i = i + 1 n = n + i end print(n)"
    p = load_bytes(compile_source(src, strip=True))
    assert certify_proto(p, is_chunk_root=True).level == "L3"
    printed = print_chunk(p)
    assert printed is not None
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode)
    assert a.stdout.split() == [b"10"]


def test_while_header_that_would_need_a_statement_is_refused_not_dropped():
    """THE guard for the `While` node (see `emit.lua`'s arm).

    `While` claims its header instructions, so if reconstructing them yields
    a *statement* rather than pure operand staging, printing only `while
    <cond> do` would drop it -- and the pc-claim audit would NOT catch that,
    because the pcs are claimed either way. This is Task 1's lesson applied to
    the new node: ask what it could silently drop, then guard it.

    Pinned by INJECTION, not by a compiled source. Until M4 task 13 this shape
    came straight out of `luac`: in `while a do for i = 1, 10 do f(i) end end`
    register 0 is both the condition's slot and the numeric for's control
    base, and `classify_registers` -- whole-function and per register *number*
    -- called it a local, so the header's `GETGLOBAL a` reconstructed to
    `local l0_0 = a`. Per-definition classification now gets that register
    right and the fixture certifies `L3` (it is in `test_emit_while.py`'s
    `CASES`), so there is no longer a known luac output that reaches the
    guard. Rather than delete the guard or leave it unpinned, the register
    classification is demoted by hand here: `rc` with every definition of
    register 0 forced local is exactly what the printer would receive if a
    future classification change regressed, and the guard must still refuse
    rather than drop the header's statement. (Register 0 is still in
    `rc.locals` for real -- it is a control slot the `while` condition also
    uses, so no single whole-register verdict fits it; what changed is that
    its individual definitions now carry their own.)

    Neuter check (M4 task 13): deleting the `if stmts:` raise in
    `emit.lua`'s `While` arm makes this test fail with the header statement
    silently gone from the output.
    """
    from pyluadec.emit.lua import print_function
    from pyluadec.express.names import RegClass, classify_registers
    src = b"while a do for i = 1, 10 do f(i) end end"
    fn, r = _sir(src)                            # structure is fine...
    assert _find(r, While) and _find(r, NumericFor)
    rc = classify_registers(fn)
    header_pc = min(pc for pc in fn.instrs if 0 in fn.instrs[pc].effects.writes)
    assert (header_pc, 0) in rc.temp_defs, \
        "fixture no longer stages the while condition"
    demoted = RegClass(locals=rc.locals | {0}, temps=rc.temps - {0},
                       loop_vars=rc.loop_vars,
                       temp_defs=frozenset((pc, g) for pc, g in rc.temp_defs
                                           if g != 0))
    with pytest.raises(StructureError, match="while header"):
        print_function(fn, r, demoted, depth=0)


def test_while_header_fixture_certifies_with_real_classification():
    """The other half of the test above: with the classification
    `classify_registers` actually produces, the same source certifies `L3`.
    Without this, demoting register 0 by hand could be pinning a guard against
    a shape the pipeline can no longer produce OR against one it produces all
    the time, and the two are not distinguishable from the injection alone.
    """
    src = b"while a do for i = 1, 10 do f(i) end end"
    p = load_bytes(compile_source(src, strip=True))
    assert print_chunk(p) is not None
    assert certify_proto(p, is_chunk_root=True).level == "L3"


# -------------------------------------------------------------------- repeat

REPEAT_CASES = [
    b"local i = 0 repeat i = i + 1 until i > 5",
    b"local i = 0 repeat i = i + 1 print(i) until i > 2",
    b"repeat f() until y == 1 g()",
    b"repeat until x",                                        # empty body
    b"local i = 0 repeat i = i + 1 until not (i < 5)",
    b"local i = 0 repeat i = i + 1 if i == 2 then break end until i > 5",
    b"local i = 0 repeat local a = i i = a + 1 until a > 5",   # until reads a body local
    b"local i = 0 while i < 3 do repeat i = i + 1 until i > 1 end",
    b"local i = 0 repeat while i < 3 do i = i + 1 end until i > 5",
]


@pytest.mark.parametrize("src", REPEAT_CASES, ids=range(len(REPEAT_CASES)))
def test_repeat_fixture_claims_every_pc_and_certifies(src):
    _sir(src)
    cert = certify_proto(load_bytes(compile_source(src, strip=True)),
                         is_chunk_root=True)
    assert cert.level == "L3", (src, cert.mismatches)


def test_repeat_region_shape():
    """1 LOADK  2 ADD  3 LT (the `until`)  4 JMP->2  5 RETURN

    The condition sits at the BOTTOM and its JMP goes backwards -- the mirror
    of `While`. `Repeat` claims exactly the condition and that JMP; the body
    claims everything before them.
    """
    fn, r = _sir(b"local i = 0 repeat i = i + 1 until i > 5")
    (rep,) = _find(r, Repeat)
    assert rep.cond.ri.pc == 3 and rep.closing.ri.pc == 4
    assert rep.closing.successors == (2,)
    assert rep.claimed_pcs == frozenset({3, 4})
    assert all_claimed(rep.body) == frozenset({2})


def test_repeat_polarity_is_the_untouched_fallthrough_expression():
    """`Repeat.negated` is still not consulted (M4 task 2's derivation from
    `lparser.c:965-972`/`:1021-1024` and `lcode.c:539-560` stands); this pins
    that recognition constructs it with the same convention `If` uses, and
    that the printed `until` is the un-negated exit condition."""
    src = b"local i = 0 repeat i = i + 1 print(i) until i > 2"
    fn, r = _sir(src)
    (rep,) = _find(r, Repeat)
    assert rep.negated == (rep.cond.ri.a == 0)
    printed = print_chunk(load_bytes(compile_source(src, strip=True)))
    # `until l0_0 > 2` since M5 task 5: the source is `until i > 2` and
    # `Reconstructor._reads_as_gt` recovers the `>`. Same instruction either
    # way; the differential run below is what pins the polarity.
    assert printed is not None and printed.rstrip().endswith("until l0_0 > 2")
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    # A sign-flipped `until` compiles and exits after ONE iteration.
    assert a.stdout.split() == [b"1", b"2", b"3"] == b.stdout.split()


def test_repeat_is_not_claimed_at_an_enclosing_loop_header():
    """The `lo == continue_target` tie-break (see `_match_repeat`).

    `while true do if f() then g() end end` and
    `while true do repeat until f() g() end` are the same bytecode, so both
    readings are legal; the recognizer keeps M3's `If` reading rather than
    churning a very common shape into a `repeat` the source almost certainly
    did not contain.
    """
    assert (compile_source(b"while true do if f() then g() end end", strip=True)
            == compile_source(b"while true do repeat until f() g() end", strip=True))
    fn, r = _sir(b"while true do if f() then g() end end")
    assert _find(r, Repeat) == []


# ---------------------------------------------------- known gaps, with causes

def test_empty_while_body_is_a_register_classification_gap_not_a_loop_defect():
    """`while a do end` structures and refuses to print, for a reason that has
    nothing to do with loops.

    `_stack_discipline` (express/names.py) is a pc-LINEAR simulation of luac's
    `freereg = nactvar` discipline with no control-flow model. With an empty
    body, nothing between the header's `GETGLOBAL a` and the function's
    trailing `RETURN` ever pops register 0, so the final `promote_all()` grades
    it a local -- and the `While` printer then correctly refuses a header that
    would need a statement. Add one call to the body (`while a do f() end`)
    and the body's own `GETGLOBAL` pops it, so it is a temp and the shape
    certifies; that case is in WHILE_CASES.

    EXPIRY: this is M3 reconstruction debt (the documented whole-function,
    per-register-number approximation in `RegClass`'s docstring), not M4 loop
    work. If a later task gives `classify_registers` a live-range model, this
    becomes L3 and this test should be deleted and the shape folded into
    WHILE_CASES -- not patched.
    """
    from pyluadec.express.names import classify_registers
    fn, r = _sir(b"while a do end")               # structures cleanly
    assert _find(r, While)
    assert 0 in classify_registers(fn).locals
    p = load_bytes(compile_source(b"while a do end", strip=True))
    assert print_chunk(p) is None
    assert certify_proto(p, is_chunk_root=True).level == "L1"
    # The same loop with a non-empty body certifies.
    assert certify_proto(load_bytes(compile_source(b"while a do f() end", strip=True)),
                         is_chunk_root=True).level == "L3"

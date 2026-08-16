"""M5 task 5: the `mismatch:` residual -- protos that print and recompile but
whose recompiled proto is not the original.

Everything here is adjudicated by `certify_proto`, which recompiles the
printed source with the real `luac_sz4` and compares the resulting proto
field-by-field under the normalization ladder. Nothing in this file relaxes
that gate: a fixture that is semantically right but differently compiled is a
FAILURE, not a pass.

Fixture sources are pure ASCII by construction, so assertions that inspect
printed text may decode; bytecode-derived strings elsewhere stay `bytes`.

## Cluster 1: a `for` statement owns its slots only for its own extent

`lparser.c`'s `fornum`/`forlist` `new_localvar` the control triple and the
visible variables and wrap the body in `enterblock`/`leaveblock`; `leaveblock`
restores `fs->freereg = fs->nactvar`, so the moment the loop's `end` is
reached slots `a..a+3+n` are ordinary expression-stack scratch again and luac
reuses them for the very next statement.

Through M4, `express.names.classify_registers` treated that ownership as a
whole-FUNCTION property (a register number in any `for` header's triple was a
control slot everywhere, and a loop variable was a named local everywhere),
and `Reconstructor.__init__` seeded every loop variable into `declared` for
the whole function. Both are wrong on exactly the same shape -- a `for` loop
followed by a statement that reuses its slots -- and both were wrong in a way
that certification caught but that a reader of the output would not:

  * the classifier saw the reuse as "a write to a named local", which ends a
    statement in the freereg simulation, and promoted the *preceding*
    expression-stack values to named locals;
  * the reconstructor printed the reuse as `l0_9 = ...`, a bare assignment to
    a name that is no longer in scope -- which Lua compiles as a write to a
    GLOBAL. That is a semantic change, not merely an unfaithful one; only the
    certification gate kept it from shipping.

Corpus movement for the fix: 1403 -> 1415 unique proto shapes at `L3`
(1869 -> 1881 occurrences), 215 -> 216 of 229 files shipping structured
source, measured 2026-08-12.
"""
import pytest

from pyluadec.emit.lua import print_chunk
from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.structure.structured import certify_proto


def _certify(src: bytes):
    proto = load_bytes(compile_source(src, strip=True))
    return proto, certify_proto(proto, is_chunk_root=True)


# Each entry is (source, expected stdout). The stdout expectation is measured
# from the ORIGINAL bytecode inside the test rather than trusted from here;
# it is recorded so a fixture that silently stops exercising anything shows up.
LOOP_SLOT_REUSE = [
    # `snr_novel.lua:main_6`, reduced to its shape and made self-contained.
    # The third argument of the trailing call lands in the loop VARIABLE's
    # slot; before the fix that printed as `l0_3 = 60` (a SETGLOBAL) and
    # dragged the callee and the first two arguments into named locals.
    (b"local n = 0 for i = 0, 20 do n = n + i end print(0, '', 60) print(n)",
     [b"0\t\t60", b"210"]),
    # Two sequential numeric `for`s where the second's CONTROL TRIPLE lands in
    # the first's variable + the slots just above it. This is the shape that
    # made `tests/test_semantic_regressions.py::
    # test_counter_closure_and_dispatch_mix` ship fallback through M4.
    (b"local t = {} for i = 1, 6 do t[i] = i * 2 end "
     b"local s = 0 for i = 1, 8 do s = s + i end print(s, t[6])",
     [b"36\t12"]),
    # The trailing statement is a plain call whose CALLEE lands in the loop's
    # control base -- before the fix, `l0_1 = print` and then `l0_1(l0_2)`.
    (b"local s = 0 for i = 1, 4 do s = s + i end print(s)", [b"10"]),
    # A loop whose body writes BACK to the loop variable (legal Lua; does not
    # affect iteration), followed by slot reuse. This is the one shape that
    # needs the declaration to be present INSIDE the body and absent after it,
    # so it fails if `declare_loop_vars` is dropped in either direction.
    (b"local s = 0 for i = 1, 3 do i = i + 10 s = s + i end print(s, 1, 2, 3)",
     [b"36\t1\t2\t3"]),
    # Nested loops sharing the outer's slots after the inner one closes.
    (b"local s = 0 for i = 1, 3 do for j = 1, 3 do s = s + j end s = s + i end "
     b"print(s)", [b"24"]),
]


@pytest.mark.parametrize("src,words", LOOP_SLOT_REUSE,
                         ids=range(len(LOOP_SLOT_REUSE)))
def test_slots_a_for_statement_released_are_not_still_its_own(src, words):
    """The `for` header's registers become ordinary scratch at its `end`.

    Certification is the adjudicator: the printed source has to recompile to
    the original proto, so "close enough" does not pass.
    """
    proto, cert = _certify(src)
    assert cert.level == "L3", (cert.reason, print_chunk(proto))


@pytest.mark.parametrize("src,words", LOOP_SLOT_REUSE,
                         ids=range(len(LOOP_SLOT_REUSE)))
def test_the_printed_source_computes_what_the_bytecode_computes(src, words):
    """Differential execution: run the original bytecode and the printed
    source under `lua_sz4` and diff stdout.

    **Honest about what this does NOT catch.** Measured 2026-08-12 by running
    this arm against the pre-fix tree: all five fixtures were GREEN before the
    fix, while three of the five failed certification. The pre-fix output for
    fixture 0 really did contain `l0_3 = 60`, a write to a *global* (the name
    left scope at the loop's `end`) -- but it is read back by the very next
    expression in the same statement, so the value observed is the same and
    stdout is identical. The leak is only observable to something that
    inspects `_G`, which none of these fixtures do.

    So the certification test above is the one that adjudicates this cluster,
    and this one is a companion that would catch the *other* direction (an
    over-inlined local that silently disappears, the failure mode
    `test_express_liverange.py` guards) if a future change to the loop-window
    rules produced it here. It is cheap and it is not load-bearing; recorded
    that way rather than written up as the proof.
    """
    proto = load_bytes(compile_source(src, strip=True))
    printed = print_chunk(proto)
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    assert a.returncode == 0 and b.returncode == 0, (a.stderr, b.stderr)
    assert a.stdout == b.stdout, printed
    # measured from the original; `words` above is only a tripwire against a
    # fixture that has quietly stopped exercising anything.
    assert a.stdout.splitlines() == words


# ---------------------------------------------------------------------------
# Cluster 2: a generic `for` over a CALL is one expression, not three
#
# `forlist` (lparser.c:1113-1130) parses the header's `explist1` and
# `adjust_assign`s it to exactly 3 values, so `for k, v in pairs(t) do`
# compiles to `CALL a b 4` writing the control triple directly -- one source
# expression across three slots. `Reconstructor._emit_multi` had no way to
# express that (no `Expr` node means "the second value of `f()`") and
# materialized all three, printing
#
#     local l0_1, l0_2, l0_3 = pairs(l0_0)
#     for l0_4, l0_5 in l0_1, l0_2, l0_3 do
#
# which is semantically identical and costs three registers and three `MOVE`s
# -- recorded as a known residual in `structured-pipeline.md` since M4.
#
# The fix stages the call into the base slot and puts a `MultiSpill`
# placeholder in the other two; `emit.lua`'s `GenericFor` arm drops the
# spills and prints the single expression. `MultiSpill` is deliberately
# unprintable, so a spill reaching any other position refuses instead of
# emitting something wrong.
#
# Corpus movement: 1415 -> 1418 unique proto shapes at `L3` (1881 -> 1884
# occurrences), measured 2026-08-12.

GENERIC_FOR_ITERATOR = [
    # The shape itself, both stdlib iterators.
    (b"local t = {7, 8, 9} for k, v in ipairs(t) do print(k, v) end "
     b"print(1, 2, 3, 4)", [b"1\t7", b"2\t8", b"3\t9", b"1\t2\t3\t4"]),
    (b"local t = {7, 8, 9} for k, v in pairs(t) do print(k, v) end "
     b"print(1, 2, 3)", [b"1\t7", b"2\t8", b"3\t9", b"1\t2\t3"]),
    # The NEGATIVE side of the same rule: an explicit iterator list is three
    # independent expressions and must keep printing as three. `explist1`
    # gives 2 values here and `adjust_assign` pads with a LOADNIL, which is
    # why the printed header is `next, t, nil` and not `next, t`.
    (b"local t = {7, 8, 9} for k, v in next, t do print(k, v) end "
     b"print(1, 2, 3)", [b"1\t7", b"2\t8", b"3\t9", b"1\t2\t3"]),
    # The other negative: the same `CALL ... 4` bytecode whose three targets
    # are genuine locals (they survive the statement), so it must stay
    # materialized. It fails BOTH of the recogniser's first two conditions --
    # there is no TFORLOOP at that base AND none of the three defs is a temp
    # at that pc (measured 2026-08-12, fix round 1) -- so it does not isolate
    # either one; see `test_the_iterator_recogniser_needs_a_tforloop_at_the_base`
    # for the clause-isolating pin.
    (b"local a, b, c = string.find('xyz', 'y') print(a, b, c)", [b"2\t2\tnil"]),
    # The exact shape that was `tests/test_express_liverange.py`'s
    # `KNOWN_RESIDUAL[0]` from M4 task 13 until this task closed it (promoted
    # here per that test's own instruction).
    (b"local t = {} for k, v in pairs(t) do f(k, v) g(k) end", None),
    # Cluster 1 and cluster 2 in one function: a numeric `for` whose slots are
    # reused, then a generic `for` over a call.
    (b'local n = 0 for i = 0, 20 do n = n + i end print(0, "", 60) '
     b'local c = 0 for k in pairs(_G) do c = c + 1 end print(n, c)', None),
]


@pytest.mark.parametrize("src,words", GENERIC_FOR_ITERATOR,
                         ids=range(len(GENERIC_FOR_ITERATOR)))
def test_a_generic_for_over_a_call_prints_one_iterator_expression(src, words):
    proto, cert = _certify(src)
    assert cert.level == "L3", (cert.reason, print_chunk(proto))
    if words is not None:
        a = run_bytes(compile_source(src, strip=True), is_source=False)
        b = run_bytes(print_chunk(proto).encode(), is_source=True)
        assert a.stdout == b.stdout == b"\n".join(words) + b"\n"


def test_the_iterator_recogniser_rejects_a_multi_assign_to_real_locals():
    """`local a, b, c = f()` and `for k, v in f() do` compile to the same
    `CALL a b 4`. The first must NOT be staged -- its three targets survive
    the statement -- and this pins the outcome end to end.

    What it does NOT do is isolate any single condition of
    `_is_generic_for_iterator`. Measured 2026-08-12 (fix round 1, Important
    1): this fixture fails the TFORLOOP condition AND the "every def is a
    temp at this pc" condition, so deleting either one on its own leaves this
    assertion green. The clause-level pin is
    `test_the_iterator_recogniser_needs_a_tforloop_at_the_base` below.
    """
    proto = load_bytes(compile_source(
        b"local a, b, c = string.find('xyz', 'y') print(a, b, c)", strip=True))
    printed = print_chunk(proto)
    assert "local l0_0, l0_1, l0_2 = " in printed, printed


def test_the_iterator_recogniser_needs_a_tforloop_at_the_base():
    """`_is_generic_for_iterator`'s TFORLOOP condition, isolated -- the only
    way it CAN be isolated.

    The condition is defensive (see its docstring): on real `luac` output it
    has never been observed to reject anything the temp condition does not
    already reject, and there is a structural reason it cannot -- three
    simultaneously-defined registers can only all be temps at one pc when
    they are a `for` header's control triple. Measured this session: 0 of 4
    shape-passing sites on the 229-file corpus lack a TFORLOOP at the base,
    and 0 of 35 hand-written non-TFORLOOP `luac` shapes has all three targets
    temp.

    So the isolating fixture is real bytecode (`local a, b, c =
    string.find(...)`, a genuine `CALL 0 3 4` with no TFORLOOP anywhere) with
    a hand-built `RegClass` that satisfies the other two conditions by fiat:
    all three targets temp, none `declared`. That is a legal `RegClass` --
    `_is_generic_for_iterator`'s own docstring names `rc.temps` as the
    hand-built-classification path -- and it is exactly the state a future
    "simplification" that dropped the TFORLOOP clause would be relying on the
    classifier never to produce. With the clause present the write
    materializes; with it removed the three values are staged and two
    unprintable `MultiSpill`s leak into the `print` call.
    """
    import dataclasses

    from pyluadec.express.expr import MultiSpill
    from pyluadec.express.names import classify_registers
    from pyluadec.express.reconstruct import LocalDecl, reconstruct_straight
    from pyluadec.lift import lift_proto
    from pyluadec.lift.opcodes import Op

    proto = load_bytes(compile_source(
        b"local a, b, c = string.find('xyz', 'y') print(a, b, c)", strip=True))
    fn = lift_proto(proto)
    assert not any(li.ri.op is Op.TFORLOOP for li in fn.instrs.values())
    rc = dataclasses.replace(classify_registers(fn),
                             temps=frozenset({0, 1, 2}))
    stmts = reconstruct_straight(
        fn, tuple(fn.instrs[pc] for pc in sorted(fn.instrs)), rc, depth=0)

    def spills(node) -> int:
        if isinstance(node, MultiSpill):
            return 1
        total = 0
        for f in dataclasses.fields(node) if dataclasses.is_dataclass(node) else ():
            v = getattr(node, f.name)
            for item in (v if isinstance(v, tuple) else (v,)):
                if dataclasses.is_dataclass(item):
                    total += spills(item)
                elif isinstance(item, tuple):
                    total += sum(spills(x) for x in item
                                 if dataclasses.is_dataclass(x))
        return total

    assert sum(spills(s) for s in stmts) == 0, stmts
    decls = [s for s in stmts
             if isinstance(s, LocalDecl) and s.regs == (0, 1, 2)]
    assert decls, stmts


def test_a_multispill_is_unprintable_anywhere_else():
    """`MultiSpill` has no Lua syntax, and `emit.lua._expr`'s fallback is what
    guarantees a stray one refuses rather than printing something wrong.

    Checked directly rather than trusted: this is the whole safety argument
    for staging a value into a slot no expression can name.
    """
    from pyluadec.emit.lua import print_expr
    from pyluadec.express.expr import MultiSpill
    with pytest.raises(ReconstructError, match="unprintable expression"):
        print_expr(MultiSpill(3), depth=0)


# ---------------------------------------------------------------------------
# Cluster 3: `>` / `>=` are not `<` / `<=` with the operands swapped
#
# `lcode.c`'s `codecomp` (673-686) compiles `a > b` by evaluating `a` then `b`
# and then EXCHANGING the operands so it can emit `OP_LT` (`luaK_posfix`,
# 775-778). So `x < y` and `y > x` are byte-identical instructions and
# printing every `LT` as `<` is a guess, not a canonicalisation. When the
# guess is wrong the recompile evaluates the two operands in the other order,
# which reorders their own code and -- decisively -- their constants:
# `luaK_infix`'s default arm (710-733) interns `e1` via `luaK_exp2RK` before
# the parser has seen `e2`.
#
# That is the whole of what M3 and M4 measured as the "differs only by
# constant-pool order" population and twice declined an `L3.2` normalization
# rung for (9 protos at M3, 10 at M4 task 6, 11 re-measured at the start of
# this task). Recovering the `>` closes it as a defect instead: re-measured
# after this cluster with the same recursive, K-operand-aware method,
# **0 protos** differ only by pool order. See
# `docs/runbooks/structured-pipeline.md` for the rung's final disposition.
#
# Corpus movement: 1418 -> 1430 unique proto shapes at `L3` (1884 -> 1896
# occurrences), measured 2026-08-12.

GT_RECOVERY = [
    # Both operands constants -> decided by their pool indices. Neutering the
    # `bk and ck` arm turns these two red (verified this session).
    (b'if 2 > 1 then print("a") end', [b"a"]),
    (b'if 2 >= 1 then print("a") end', [b"a"]),
    # Both operands registers AND both expression-stack temporaries -> decided
    # by their register numbers: the operand evaluated first was pushed first
    # and sits lower. Neutering the `not bk and not ck` arm turns this and the
    # table-index case red. The temp gate is what makes the "pushed first"
    # argument apply at all -- see
    # `test_the_gt_recogniser_leaves_a_local_operand_alone`.
    (b'local function f() return 4 end local function g() return 3 end '
     b'if f() > g() then print("a") end', [b"a"]),
    (b'local t = {a = 2, b = 1} if t.a > t.b then print("a") end', [b"a"]),
    # One constant, in field B -> the corpus shape. `select` and `"#"` are
    # interned by the call and `0` only afterwards, so the original pool is
    # `select, #, 0`; printing `0 < select("#", ...)` recompiles to
    # `0, select, #`. Neutering the `if bk:` arm turns this red.
    (b'local function f(...) if select("#", ...) > 0 then print("a") end end '
     b'f(1)', [b"a"]),
    # The `<` direction of each of the three, unchanged.
    (b'if 1 < 2 then print("a") end', [b"a"]),
    (b'local function f() return 3 end local function g() return 4 end '
     b'if f() < g() then print("a") end', [b"a"]),
    (b'local t = {a = 1, b = 2} if t.a < t.b then print("a") end', [b"a"]),
    # `repeat ... until i > 2` -- the `until` is the same expression path.
    (b"local i = 0 repeat i = i + 1 print(i) until i > 2",
     [b"1", b"2", b"3"]),
]


@pytest.mark.parametrize("src,words", GT_RECOVERY, ids=range(len(GT_RECOVERY)))
def test_a_comparison_is_printed_the_way_it_was_written(src, words):
    proto, cert = _certify(src)
    assert cert.level == "L3", (cert.reason, print_chunk(proto))
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(print_chunk(proto).encode(), is_source=True)
    assert a.stdout == b.stdout == b"\n".join(words) + b"\n"


def test_the_gt_recogniser_leaves_a_constant_in_field_c_alone():
    """The deliberate gap in `_reads_as_gt`, pinned so it stays deliberate.

    `x < 5` puts the constant in field C, and so does `5 > x`. Telling them
    apart would need "C's constant is OLDER than what B's own code created",
    which `_max_const_index_before` cannot distinguish from the very common
    case of `5` already being in the pool. The recogniser therefore never
    flips this shape -- and it does not need to, because a bare local
    contributes no code and no constants, so BOTH sources compile to the
    identical instruction and the `<` print certifies either way. Both
    directions are checked here; if a future refinement starts flipping this
    shape, the second assertion is what will notice.
    """
    for src in (b'local x = 1 if x < 5 then print("a") end',
                b'local x = 1 if 5 > x then print("a") end'):
        proto, cert = _certify(src)
        assert cert.level == "L3", (src, cert.reason)
        assert "if l0_0 < 5 then" in print_chunk(proto), print_chunk(proto)


def test_the_gt_recogniser_leaves_a_local_operand_alone():
    """The SECOND deliberate gap in `_reads_as_gt` (fix round 1, Important 2),
    pinned in the same shape as the C-constant one above.

    The both-registers arm's evidence is "the operand evaluated first sits in
    a LOWER register, because it was pushed onto the expression stack first".
    That is a fact about the expression *stack*, and `luaK_exp2RK` on a
    `VLOCAL` pushes nothing at all -- it returns the variable's declaration
    slot (`discharge2anyreg`, lcode.c:400-420, never reaches
    `luaK_reserveregs`). So in `f(0) < y` the call's result is a fresh
    temporary allocated ABOVE every live local while `y` sits low, `B > C`
    holds, and an ungated arm prints `y > f(0)` -- the opposite of the source,
    on no evidence at all.

    Both directions are checked, and they must print the SAME text: `y` is a
    bare local, so it contributes no code and no constants and the two
    sources compile to byte-identical protos. That is why withdrawing the
    flip costs nothing (measured: the corpus `L3` count is unchanged, and the
    ledger is byte-identical) -- and why the direction the ungated arm picked
    was arbitrary rather than derived.

    `(local, local)` is covered by the same gate for a stronger reason still:
    two declaration slots are pure declaration order and carry no evaluation
    information whatsoever.
    """
    for src in (b'local y = 1 if f(0) < y then print("a") end',
                b'local y = 1 if y > f(0) then print("a") end'):
        proto, cert = _certify(src)
        assert cert.level == "L3", (src, cert)
        assert "if f(0) < l0_0 then" in print_chunk(proto), print_chunk(proto)
    # And the arm still fires where its argument DOES hold: two temporaries.
    proto, cert = _certify(b'if g(1) > f(0) then print("a") end')
    assert cert.level == "L3", cert
    assert "if g(1) > f(0) then" in print_chunk(proto), print_chunk(proto)


def test_an_eq_is_never_flipped():
    """`codecomp`'s operand exchange is guarded by `op != OP_EQ` (lcode.c:679),
    so an `EQ`'s operands are always already in source order. `_GT_SYM` has no
    `EQ` entry, and this is the fixture that would catch one being added.
    """
    from pyluadec.lift.opcodes import Op
    from pyluadec.express.reconstruct import _GT_SYM
    assert Op.EQ not in _GT_SYM
    proto, cert = _certify(b'local x = 1 if 5 == x then print("a") end')
    assert cert.level == "L3", cert.reason
    assert "if 5 == l0_0 then" in print_chunk(proto), print_chunk(proto)


# ---------------------------------------------------------------------------
# The residual, pinned with its diagnosis rather than fixed.

def test_a_multiple_assignment_prints_as_separate_statements():
    """`snr_common.lua:main_77_0` -- the smallest residual proto in the corpus
    (5 instructions), and NOT what the M4 final review recorded.

    That review called it "a genuine upvalue-index divergence". The index
    divergence is real but it is the symptom; the mechanism is a **multiple
    assignment**. Measured this session by reverse-engineering the source and
    recompiling it: `u0, u1 = 1, 0` reproduces the original proto exactly
    (`compare_protos(..., level=1) == []`, asserted below).

    `lparser.c`'s `assignment` (:1052-1090) resolves every left-hand variable,
    left to right, BEFORE `explist1` evaluates the right-hand side, and then
    stores them in REVERSE order as its own recursion unwinds. So `u0` becomes
    upvalue 0 and `u1` upvalue 1 (`singlevar` -> `indexupvalue` appends in
    order of first lexical reference), while the two `SETUPVAL`s come out
    `u1` first:

        LOADK 0 K(1)   LOADK 1 K(0)   SETUPVAL 1 -> upval 1   SETUPVAL 0 -> upval 0

    Printing that as three separate statements -- which is what `Reconstructor`
    does, one statement per instruction -- makes `u1` the first upvalue
    *referenced*, so the recompiled closure numbers the upvalues the other way
    round and the two `SETUPVAL` operands swap.

    Not fixed, and deliberately: recognising this needs lookahead over an
    emitted-statement run (a descending run of stores immediately after a
    matching run of value producers), which is a peephole over this layer's
    own output -- the shape this project exists to avoid -- and the whole
    229-file corpus contains **exactly one** instance of the signature
    (measured this session: one descending `SETUPVAL`/`SETGLOBAL` run of
    length >= 2, in this proto). Recorded here so the next census inherits the
    diagnosis instead of re-deriving it.

    The corpus tie itself is asserted by
    `test_the_multiple_assignment_residual_really_is_snr_common_main_77_0`
    below (fix round 1, F4): until then the load-bearing sentence of this
    docstring -- that `u0, u1 = 1, 0` IS `snr_common.lua:main_77_0` -- was a
    recorded measurement that nothing would have noticed going stale.
    """
    src = b"local u0, u1\nreturn function()\nu0, u1 = 1, 0\nend\n"
    original = load_bytes(compile_source(src, strip=True)).subprotos[0]
    # The reverse-engineered source really is this proto, bit for bit.
    from pyluadec.verify.normalize import compare_protos
    from pyluadec.emit.lua import _print_proto_body
    body = _print_proto_body(original, depth=1, upval_names=("u0", "u1"))
    wrapper = f"local u0, u1\nreturn function()\n{body}end\n".encode()
    candidate = load_bytes(compile_source(wrapper, strip=True)).subprotos[0]
    diffs = compare_protos(original, candidate, level=1)
    assert [d.field for d in diffs] == ["code"], diffs
    # ... and what we print instead is the three-statement form.
    assert body.splitlines() == ["local l1_0 = 1", "u1 = 0", "u0 = l1_0"], body


def test_the_multiple_assignment_residual_really_is_snr_common_main_77_0(corpus_dir):
    """The corpus half of the claim above, asserted rather than recorded.

    `u0, u1 = 1, 0` compiled by `luac_sz4` and `snr_common.lua:main_77_0` are
    the same proto under the rung-1 comparison -- which is the whole reason
    the reverse-engineering counts as a diagnosis of the residual and not
    merely as a plausible story about it. Skipped without a corpus, like
    every other corpus-gated test here.
    """
    from pyluadec.ingest import load_file
    from pyluadec.pipeline import walk_proto_paths
    from pyluadec.verify.normalize import compare_protos

    protos: dict = {}
    walk_proto_paths("main", load_file(corpus_dir / "snr_common.lua"), protos)
    target = protos["main_77_0"]
    src = b"local u0, u1\nreturn function()\nu0, u1 = 1, 0\nend\n"
    mine = load_bytes(compile_source(src, strip=True)).subprotos[0]
    assert compare_protos(target, mine, level=1) == []


# ---------------------------------------------------------------------------
# M8 task 3: the empty-tail alternative re-reading the chain target (the
# `snr_graphic`/`snr_memory` `main`/`main_3` family -- "register 7 is read
# again after its staged value was consumed").

def test_empty_tail_reread_clamp_on_staged_chain_certifies():
    """The corpus geometry, mirrored: A = a CondValue chain whose result is
    STAGED for its one explicit reader, B = the clamp `x = (9 < x) and 9 or
    x` whose EMPTY final alternative re-reads x's incoming value with no
    instruction (invisible to the pc-linear read-count that graded A's
    definition temp). Before task 3 this refused with exactly the family's
    message; the fix materializes the incoming value as a local before the
    chain is built -- the shape the original source has."""
    src = b"""local function f(a, b, c)
    local s = 0
    local x = c and 9 or (a.v - b * 9)
    x = (9 < x) and 9 or x
    for i = 1, x, 1 do s = s + i end
    return s
end
f({v = 1}, 2, 3)
"""
    _proto, out = _certify(src)
    assert out.level == "L3", out.reason


def test_settable_consumer_of_a_staged_clamp_is_a_recorded_gap():
    """A DIFFERENT synthetic shape found while building the repro above
    (recorded, not asserted away): when the clamp chain's consumer is a
    table store (`t[1] = x = (9 < x) and 9 or x` reading a materialized
    local -- no staging at all), our emission stages the chain result into
    a fresh register and recompiles TEST+MOVE where luac discharged
    TESTSET into the original slot -- `mismatch: code`, caught by
    certification. Corpus census (2026-08-16): no corpus proto carries
    this exact shape (the 4 family rows all refuse earlier, at the empty
    tail); revisit if a campaign row ever names it."""
    src = b"""local function f(a, b)
    local t = {}
    local x = a - b
    x = (9 < x) and 9 or x
    t[1] = x
    return t[1]
end
f({v = 1}, 2)
"""
    _proto, out = _certify(src)
    assert out.level == "L1"
    assert (out.reason or "").startswith("mismatch: code")

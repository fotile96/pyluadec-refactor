"""Readability of the structured printer's text (M5 task 7).

Every assertion here is about **presentation** -- what a human translator
reads -- and every one of them is paired with a proof that the presentation
change cannot move the certification verdict. Two levels of proof are used,
and they are different things:

* **Oracle equivalence** (`compile_source(A) == compile_source(B)`): the two
  spellings are the same program to the real `luac_sz4`, byte for byte, on
  stripped output. This is the mechanical form of the `lparser.c` reading
  quoted in each test's docstring, and it is the strongest available evidence
  that a spelling change is invisible below the printer.
* **End-to-end certification** (`certify_proto(..., is_chunk_root=True)`
  returns `L3`): the fixture, printed by THIS printer and recompiled by the
  real `luac_sz4`, matches the original proto field by field under the
  versioned normalization ladder.

The corpus-wide half of the proof is not here and cannot be: it is
`corpus/ledger.jsonl` staying byte-identical across each of this task's
commits, which `tests/test_ledger_ratchet.py` re-derives from a fresh
`scripts/run_corpus.py` pass.

All fixture sources are ASCII except where a test is specifically about
non-ASCII bytes, and those tests hold their payload as `bytes` and compare
against `bytes`.
"""
from pyluadec.emit.lua import print_chunk
from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.structure.structured import certify_proto


def printed(src: bytes) -> str:
    """Structurally print `src`'s compiled chunk, refusing to paper over a
    refusal (a `None` here would make every text assertion below fail with an
    unhelpful `TypeError`)."""
    out = print_chunk(load_bytes(compile_source(src, strip=True)))
    assert out is not None, f"printer refused: {src!r}"
    return out


def certifies(src: bytes) -> None:
    p = load_bytes(compile_source(src, strip=True))
    cert = certify_proto(p, is_chunk_root=True)
    assert cert.level == "L3", (src, cert.mismatches)


# --------------------------------------------------------------------------
# 1. elseif
# --------------------------------------------------------------------------

ELSEIF_SRC = b"if a then f() elseif b then g() elseif c then h() else k() end"


def test_elseif_and_nested_if_in_else_compile_identically():
    """`lparser.c::ifstat` (lines 1141-1162), mechanized.

    `ifstat` reads `IF cond THEN block {ELSEIF cond THEN block} [ELSE block]
    END`. For an ELSEIF it does exactly three things -- concat a fresh
    `luaK_jump` onto `escapelist`, `luaK_patchtohere(flist)`, then another
    `test_then_block`. For an ELSE it does the first two and then `block()`.
    So `else if ... end` differs from `elseif ...` only by the extra
    `enterblock`/`leaveblock` pair around the inner `ifstat`, and
    `leaveblock` emits an instruction only when `bl->upval` is set --
    `markupval` sets that on the innermost block whose `nactvar <= level`,
    which is the inner `then` block, never the wrapper. The inner `ifstat`'s
    own closing `luaK_patchtohere(escapelist)` and the outer one then both
    resolve to the same `fs->pc`, because nothing is emitted between them.

    Reading the parser is what says *why*; this assertion is what says *that*.
    """
    assert (compile_source(b"if x then f() elseif y then g() else h() end", strip=True)
            == compile_source(b"if x then f() else if y then g() else h() end end",
                              strip=True))
    # ... and with no trailing `else`, the arm where `ifstat` takes its
    # `luaK_concat(fs, &escapelist, flist)` branch instead of patching.
    assert (compile_source(b"if x then f() elseif y then g() end", strip=True)
            == compile_source(b"if x then f() else if y then g() end end", strip=True))


def test_else_arm_that_is_a_single_if_prints_elseif():
    assert printed(ELSEIF_SRC) == (
        "if a then\n"
        "  f()\n"
        "elseif b then\n"
        "  g()\n"
        "elseif c then\n"
        "  h()\n"
        "else\n"
        "  k()\n"
        "end\n")


def test_else_arm_with_more_than_one_statement_stays_an_else():
    """The collapse is exact, not "an `if` appears somewhere in the else".

    `else g() if b then h() end end` has two statements in its else arm, so
    printing `elseif` would DROP `g()`. The guard is that the arm must be
    *exactly* one `If` and nothing else.
    """
    assert printed(b"if a then f() else g() if b then h() end end") == (
        "if a then\n"
        "  f()\n"
        "else\n"
        "  g()\n"
        "  if b then\n"
        "    h()\n"
        "  end\n"
        "end\n")


def test_elseif_chain_certifies_l3():
    certifies(ELSEIF_SRC)
    certifies(b"if a then f() elseif b then g() end")
    certifies(b"if a then f() else g() if b then h() end end")


def test_elseif_chain_runs_identically():
    src = (b"local r = {} for i = 1, 4 do "
           b"if i == 1 then r[i] = 'a' elseif i == 2 then r[i] = 'b' "
           b"elseif i == 3 then r[i] = 'c' else r[i] = 'd' end end "
           b"print(r[1], r[2], r[3], r[4])")
    bc = compile_source(src, strip=True)
    out = print_chunk(load_bytes(bc))
    assert out is not None and "elseif" in out
    a = run_bytes(bc, is_source=False)
    b = run_bytes(out.encode(), is_source=True)
    assert (a.returncode, a.stdout, a.stderr) == (b.returncode, b.stdout, b.stderr)
    assert a.stdout == b"a\tb\tc\td\n"


# --------------------------------------------------------------------------
# 2. dot sugar
# --------------------------------------------------------------------------

DOT_SRC = (b'local t = f() t["k"] = 1 '
           b'g(t["k"], t["a"]["b"], t[1], t["end"], t[""], t["2x"])')
DOT_CTOR_SRC = b'return {["k"] = 1, ["end"] = 2, [1] = 3}'
# NOT `{..., 9}`: a constructor that mixes array and hash items is a
# PRE-EXISTING L1 gap in this printer, unrelated to dot sugar. It prints the
# array items first (`{9, k = 1, ...}`), which reorders the constant pool, and
# it certified L1 at 923b41b -- the commit before this task -- exactly as it
# does now. Measured 2026-08-12; recorded here so the gap is not rediscovered
# as a regression of this change.


def test_bracketed_string_key_and_dot_key_compile_identically():
    """`lparser.c`, two places, both reducing to the same `VK` constant.

    * `t.k` / `t["k"]`: `primaryexp`'s `'.'` case calls `field(ls, &v)` ->
      `checkname` -> `codestring`, and its `'['` case calls
      `yindex` -> `expr` + `luaK_exp2val`. A string literal's `expr` is
      already `VK`, so both arrive at `luaK_indexed` with the same
      constant-table index.
    * `{k = 1}` / `{["k"] = 1}`: `recfield` branches on `TK_NAME` ->
      `checkname` vs `'['` -> `yindex`, then joins on the same
      `luaK_codeABC(fs, OP_SETTABLE, ...)`.

    So the sugar is a lexical alternative for the same constant, and the
    discrimination that decides when it is available -- "a valid Lua Name that
    is not a reserved word" -- is exactly what `_ident` already implements for
    globals and method names.
    """
    assert (compile_source(b'local t = {} t.k = 1 print(t.k)', strip=True)
            == compile_source(b'local t = {} t["k"] = 1 print(t["k"])', strip=True))
    assert (compile_source(b'return {k = 1}', strip=True)
            == compile_source(b'return {["k"] = 1}', strip=True))


def test_identifier_string_keys_print_as_dot_access():
    assert printed(DOT_SRC) == (
        "local l0_0 = f()\n"
        "l0_0.k = 1\n"
        'g(l0_0.k, l0_0.a.b, l0_0[1], l0_0["end"], l0_0[""], l0_0["2x"])\n')


def test_non_identifier_and_keyword_keys_keep_their_brackets():
    """The three ways a string key fails the test, all in one line above:
    `"end"` is a reserved word, `""` is not a Name at all, and `"2x"` does not
    start with a Name character. A fourth -- a non-ASCII key -- is covered by
    `test_non_ascii_table_key_keeps_its_brackets` further down, once the
    presentation decode makes it printable at all.
    """
    out = printed(DOT_SRC)
    for bad in ('l0_0["end"]', 'l0_0[""]', 'l0_0["2x"]'):
        assert bad in out
    assert ".end" not in out and ".2x" not in out


def test_table_constructor_identifier_keys_lose_their_brackets():
    assert printed(DOT_CTOR_SRC) == (
        'local l0_0 = {k = 1, ["end"] = 2, [1] = 3}\n'
        "return l0_0\n")


def test_dot_sugar_fixtures_certify_l3():
    certifies(DOT_SRC)
    certifies(DOT_CTOR_SRC)


# --------------------------------------------------------------------------
# 3. unary minus
# --------------------------------------------------------------------------

NEG_SRC = (b"local x = -1 "
           b"f(-1, -1.5, x ^ -1, -1 ^ 2, -1 .. 'a', 'a' .. -1, -x, - -x, (-1)[1])")


def test_parenthesised_and_bare_negative_numerals_compile_identically():
    """`(-1)` and `-1` differ only in `lparser.c::primaryexp`'s `'('` case,
    which wraps the inner `expr` in `luaK_dischargevars` + `luaK_exp2reg`-free
    `VRELOCABLE` handling and emits nothing of its own for a constant.

    The interesting half is not that; it is that dropping the parentheses is
    only safe where precedence allows, which is why this change extends
    `_PREC` rather than stripping a pair of characters. Lua 5.1 §2.5.6 binds
    `^` tighter than unary minus on BOTH sides (`-1 ^ 2` is `-(1 ^ 2)`), so
    a negative numeral used as the left operand of `^` still needs its
    parentheses -- and `luac` proves it: the two spellings below are NOT the
    same program.
    """
    assert (compile_source(b"f(-1)", strip=True)
            == compile_source(b"f((-1))", strip=True))
    assert (compile_source(b"return -1 ^ 2", strip=True)
            != compile_source(b"return (-1) ^ 2", strip=True))


def test_negative_numerals_lose_their_parentheses_where_precedence_allows():
    assert printed(NEG_SRC) == (
        "local l0_0 = -1\n"
        'f(-1, -1.5, l0_0 ^ (-1), -1, -1 .. "a", "a" .. -1, -l0_0, - -l0_0, '
        "(-1)[1])\n")


def test_negative_numeral_keeps_its_parentheses_where_precedence_demands():
    """Three positions where dropping them would change the parse, all in
    `NEG_SRC` above:

    * `(-1)[1]` -- an index base must be a `prefixexp`, and `-1[1]` parses as
      `-(1[1])`.
    * `- -l0_0` -- the space is `UnExpr`'s existing anti-`--`-comment rule;
      what this change adds is that `- -1` would be spelled the same way
      rather than as `- (-1)`.
    * `-1 ^ 2` in the SOURCE folds to the constant `-1` before it ever
      reaches the printer (`lcode.c::constfolding`), which is why the printed
      form is a bare `-1` and not `(-1) ^ 2`; the left-operand-of-`^` rule is
      exercised directly by test_unary_minus_precedence_table_is_the_rule.
    """
    out = printed(NEG_SRC)
    assert "(-1)[1]" in out
    assert "- -l0_0" in out and "--" not in out


def test_unary_minus_precedence_table_is_the_rule():
    """The printer must wrap a negative numeral in exactly the positions
    `_PREC` says it must, so this drives `print_expr` directly rather than
    hoping a fixture happens to compile into each shape.
    """
    from pyluadec.emit.lua import _PREC, print_expr
    from pyluadec.express.expr import BinExpr, ConstExpr, IndexExpr
    from pyluadec.ingest.proto import LuaNumber
    import struct

    neg = ConstExpr(LuaNumber(value=-1.0, payload=struct.pack("<d", -1.0)))
    two = ConstExpr(LuaNumber(value=2.0, payload=struct.pack("<d", 2.0)))
    # `^` is right-associative and binds tighter than unary on the left.
    assert print_expr(BinExpr("^", neg, two), 0) == "(-1) ^ 2"
    # Conservative, and deliberately so: Lua would accept `2 ^ -1` (`subexpr`
    # admits a unary operator at the start of any operand regardless of the
    # limit it was given), but `_expr` has always over-parenthesised a `UnExpr`
    # in this position and a negative numeral is spelled the same way as one.
    assert print_expr(BinExpr("^", two, neg), 0) == "(2) ^ (-1)"
    # `(2)` there is a PRE-EXISTING wart, not this change: `_SIMPLE_PREC` is
    # `_PRIMARY_PREC - 1 == _PREC["^"]`, and `^`'s right-associativity asks its
    # left operand for `_PREC["^"] + 1`, so ANY constant left of `^` is
    # parenthesised. Harmless (over-parenthesising never changes a parse) and
    # unreachable on this corpus -- measured 0 `^` operators in all 229
    # decompiled files. Recorded rather than fixed; out of this task's scope.
    assert print_expr(BinExpr("*", neg, two), 0) == "-1 * 2"
    assert print_expr(BinExpr("..", neg, two), 0) == '-1 .. 2'
    assert print_expr(IndexExpr(neg, two), 0) == "(-1)[2]"
    assert _PREC["unary"] < _PREC["^"]


def test_negative_numeral_fixtures_certify_l3():
    certifies(NEG_SRC)

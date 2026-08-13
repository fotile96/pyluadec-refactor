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
import pytest

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
        "    f()\n"
        "elseif b then\n"
        "    g()\n"
        "elseif c then\n"
        "    h()\n"
        "else\n"
        "    k()\n"
        "end\n")


def test_else_arm_with_more_than_one_statement_stays_an_else():
    """The collapse is exact, not "an `if` appears somewhere in the else".

    `else g() if b then h() end end` has two statements in its else arm, so
    printing `elseif` would DROP `g()`. The guard is that the arm must be
    *exactly* one `If` and nothing else.
    """
    assert printed(b"if a then f() else g() if b then h() end end") == (
        "if a then\n"
        "    f()\n"
        "else\n"
        "    g()\n"
        "    if b then\n"
        "        h()\n"
        "    end\n"
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


# --------------------------------------------------------------------------
# 4. indentation (output surface v2)
# --------------------------------------------------------------------------

INDENT_SRC = (b"local f = function(a) "
              b"  if a then "
              b"    local g = function() return 1 end "
              b"    return g() + g() "
              b"  end "
              b"  return 0 "
              b"end "
              b"return f(1), f(2)")
# `f` and `g` are each read twice on purpose. A synthesized local that is read
# ONCE is inlined into its consumer by the reconstructor, so a single-use
# `local f = function() ... end` never reaches the printer as a statement at
# all -- it comes out as `return function(l1_0) ... end` and there is no
# closure-inside-a-block to indent.
LOCALFN_SRC = b"local function r(n) if n then return r(n) end return 0 end return r(1)"


def test_function_bodies_are_indented_like_every_other_block():
    """The M4 readability report's third "ours reads worse" item: the body of
    a chunk-level `local f = function()` sat at column 0 while an `if` inside
    it indented normally, so the function looked like it had no block at all.
    """
    assert printed(INDENT_SRC) == (
        "local l0_0 = function(l1_0)\n"
        "    if l1_0 then\n"
        "        local l1_1 = function()\n"
        "            return 1\n"
        "        end\n"
        "        return l1_1() + l1_1()\n"
        "    end\n"
        "    return 0\n"
        "end\n"
        "return l0_0(1), l0_0(2)\n")


def test_indentation_is_four_spaces_at_every_level():
    out = printed(INDENT_SRC)
    starts = [line[:len(line) - len(line.lstrip(" "))] for line in out.splitlines()]
    assert starts == ["", "    ", "        ", "            ", "        ",
                      "        ", "    ", "    ", "", ""]
    assert all(len(s) % 4 == 0 for s in starts)


def test_local_function_sugar_closes_at_its_own_indent():
    """`local function NAME` is printed by `_local_decl`, not by the generic
    closure path, so its `end` needs the same treatment."""
    assert printed(LOCALFN_SRC) == (
        "local function l0_0(l1_0)\n"
        "    if l1_0 then\n"
        "        return l0_0(l1_0)\n"
        "    end\n"
        "    return 0\n"
        "end\n"
        "return l0_0(1)\n")


def test_indentation_fixtures_certify_l3():
    certifies(INDENT_SRC)
    certifies(LOCALFN_SRC)


# --------------------------------------------------------------------------
# 5. presentation-layer string decode
# --------------------------------------------------------------------------
#
# The one place in this project where a bytecode-derived byte string is
# decoded. CLAUDE.md's red-line bullet was amended (human partner,
# 2026-08-12) to scope the no-decode rule to ingest/lift/comparison and allow
# the PRINTING layer a decision with a fallback. These tests pin both halves:
# what the decision prints, and what the fallback prints.
#
# `UTF8_SRC`'s payloads are held as `bytes` and compared against `bytes` --
# the test file never assumes a decode succeeded.

_HELLO = "你好".encode()            # U+4F60 U+597D, 6 bytes of UTF-8
_LONE_CONT = b"\xff\xfe"                    # not UTF-8 in any position
_TRUNCATED = b"\xe3\x81"                    # first two bytes of a 3-byte char


def _lua_escaped(bs: bytes) -> bytes:
    """`bs` spelled as a Lua source-level decimal-escaped literal body."""
    return b"".join(b"\\%03d" % c for c in bs)


UTF8_SRC = (b'return "' + _lua_escaped(_HELLO) + b'", "'
            + _lua_escaped(_LONE_CONT) + b'", "' + _lua_escaped(_TRUNCATED)
            + b'", "' + _lua_escaped(b'a\\"b\nc\x7f') + b'", "ascii"')


def test_reversible_utf8_prints_raw_and_everything_else_stays_escaped():
    out = printed(UTF8_SRC)
    assert out == (
        'return "你好", "\\255\\254", "\\227\\129", '
        '"a\\\\\\"b\\010c\\127", "ascii"\n')
    # Stated as bytes, since that is what reaches the compiler.
    assert out.encode() .count(_HELLO) == 1


def test_non_utf8_corpus_scan_found_none_so_the_fallback_is_synthetic_here():
    """**A claim in this task's brief that did not reproduce.**

    The brief and the task prompt both assert that the corpus "genuinely
    contains non-UTF-8 constants -- the predecessor project crashed on exactly
    this". Measured 2026-08-12 over all 229 files / 1944 protos: **49063**
    string constants, **17411** of them non-ASCII, and **0** that fail a
    strict UTF-8 decode. Re-derive with the loop in this task's report.

    What CLAUDE.md actually records is a property of the predecessor's
    *bridge* ("非 UTF-8 字符串会抛异常"), which is a statement about that
    code's fragility, not evidence about this corpus's contents.

    So the escape fallback's evidence is synthetic, by construction, and this
    test exists to say so rather than to let a green corpus imply coverage it
    does not have -- MEMORY.md's "the corpus is a weaker oracle than it
    looks". `_LONE_CONT` and `_TRUNCATED` above are the two distinct ways a
    byte string fails: an invalid lead byte, and a valid lead byte with the
    continuation missing.
    """
    assert _HELLO.decode("utf-8")           # reversible UTF-8: takes the raw path
    for bad in (_LONE_CONT, _TRUNCATED):
        with pytest.raises(UnicodeDecodeError):
            bad.decode("utf-8")


def test_raw_utf8_recompiles_to_the_identical_constant():
    """The whole justification for the amendment: both spellings compile to
    the same constant, so certification is indifferent to which is used."""
    escaped = compile_source(UTF8_SRC, strip=True)
    raw = compile_source(printed(UTF8_SRC).encode(), strip=True)
    assert load_bytes(escaped).constants == load_bytes(raw).constants
    certifies(UTF8_SRC)


def test_raw_utf8_output_runs_identically():
    src = b'print("' + _lua_escaped(_HELLO) + b'")'
    bc = compile_source(src, strip=True)
    out = printed(src)
    a = run_bytes(bc, is_source=False)
    b = run_bytes(out.encode(), is_source=True)
    assert (a.returncode, a.stdout, a.stderr) == (b.returncode, b.stdout, b.stderr)
    assert a.stdout == _HELLO + b"\n"


def test_ascii_strings_are_byte_identical_to_the_pre_amendment_spelling():
    """The raw path is entered only for non-ASCII; a pure-ASCII constant is
    delegated to `structure.fallback.str_lit` unchanged, so the amendment
    cannot have moved any ASCII output."""
    from pyluadec.emit.lua import _str_lit
    from pyluadec.structure.fallback import str_lit
    for bs in (b"", b"abc", b'a"b\\c', b"\x01\n\x7f", b"end", bytes(range(128))):
        assert _str_lit(bs) == str_lit(bs)


def test_non_ascii_table_key_keeps_its_brackets():
    """The fourth way a string key fails `_as_ident` (see change 2): it is not
    ASCII. Now that such a key is PRINTABLE raw, the bracketed form has to
    survive -- `t.你好` is not a Lua Name."""
    src = b'local t = f() t["' + _lua_escaped(_HELLO) + b'"] = 1 return t'
    out = printed(src)
    assert ('l0_0["你好"] = 1') in out
    certifies(src)


def _decimal_escapes(src: bytes) -> set[int]:
    """Every `\\ddd` decimal escape in `src`, as the byte VALUE it denotes.

    A scanner rather than a substring test, because `\\\\` (an escaped
    backslash) may be followed by digits that are ordinary text: the printed
    form of a constant holding `\\1` is the three bytes `\\`, `\\`, `1`, and a
    substring search for `\\1` finds the tail of it. Lua 5.1's `read_string`
    reads at most three digits after a backslash (`llex.c`), which is the same
    rule applied here.
    """
    out: set[int] = set()
    i = 0
    while i < len(src):
        if src[i] != 0x5C:                      # not a backslash
            i += 1
            continue
        j = i + 1
        if j < len(src) and src[j] == 0x5C:     # "\\\\" -- consume both
            i = j + 1
            continue
        k = j
        while k < len(src) and k - j < 3 and 0x30 <= src[k] <= 0x39:
            k += 1
        if k > j:
            out.add(int(src[j:k]))
        i = k if k > j else j + 1
    return out


def test_decimal_escape_scanner_sees_what_the_substring_test_could_not():
    """`_decimal_escapes` is the check `test_a_real_corpus_string_prints_raw`
    rests on, and that arm is vacuous on today's corpus (0 escapes in all 216
    structured files). So the discriminating cases are here.

    The two rows the old `b"\\\\1" not in src` form got wrong are the last
    two: `\\127` is a DEL that the RAW path legitimately emits, and `"\\\\\\\\1"`
    is a constant holding a backslash and the digit 1, whose printed form
    contains the bytes `\\1` without being an escape at all."""
    assert _decimal_escapes(b'"abc"') == set()
    assert _decimal_escapes(b'"\\227\\128\\144"') == {227, 128, 144}   # caught
    assert _decimal_escapes(b'"\\010\\013"') == {10, 13}               # ASCII
    assert _decimal_escapes(b'"\\127"') == {127}                       # ASCII
    assert _decimal_escapes(b'"\\\\1"') == set()                       # not an escape
    assert _decimal_escapes(b'"\\\\\\\\200"') == set()                 # two escaped \\


def test_a_real_corpus_string_prints_raw(corpus_dir, decompiled):
    """The real-data arm. `snr_crd_10.lua` ships fully structured source and
    its constants are the visual novel's Japanese script -- exactly the text a
    translator has to read.
    """
    import pathlib
    from pyluadec.ingest import load_file

    f = pathlib.Path(corpus_dir) / "snr_crd_10.lua"
    src = decompiled(f).source
    proto = load_file(f)

    def consts(p):
        yield from (c for c in p.constants if isinstance(c, bytes))
        for sp in p.subprotos:
            yield from consts(sp)

    non_ascii = [c for c in consts(proto) if not c.isascii()]
    assert len(non_ascii) >= 10, len(non_ascii)
    # Every one of them decodes, and every one appears RAW in the artifact.
    for c in non_ascii:
        c.decode("utf-8")
        assert c in src, c[:16].hex()
    # ... and no decimal escape of a non-ASCII byte survives anywhere in it.
    #
    # Decoded properly rather than by substring. The old form was
    # `b"\\2" not in src and b"\\1" not in src`, which is over-broad in two
    # ways that this corpus happens not to exhibit (M5 task 7 review; fixed at
    # task 12): `\\1` also forbids `\\127`, a DEL that `_str_lit`'s RAW path
    # legitimately emits, and it forbids the tail of `"\\\\1"` -- the printed
    # form of a constant holding a backslash followed by the digit 1. What the
    # test means is the value, so read the value.
    #
    # Measured 2026-08-13: this artifact contains NO decimal escape at all,
    # and neither does any of the other 215 fully-structured files -- the set
    # of escape values over all 216 is empty. So the assertion below is
    # currently vacuous on the corpus, which is why `_decimal_escapes` has its
    # own positive/negative test next door: the corpus arm shows the artifact
    # is clean, and that test shows the check can see a violation.
    high = {v for v in _decimal_escapes(src) if v >= 128}
    assert high == set(), sorted(high)[:8]

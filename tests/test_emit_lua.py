"""Lua printer (SIR + Expr -> source text). Every test either compiles the
printed output through luac_sz4 or, where "compiles" alone wouldn't catch a
plausible bug (branch polarity, precedence, method-call sugar), actually
*runs* it and checks the observed behaviour -- see the module docstring in
src/pyluadec/emit/lua.py for the brief defects (backwards if/else polarity,
unparenthesised TEST negation) this distinction caught.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _proto(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return load_file(o)


def _compiles(src: str) -> bool:
    from pyluadec import oracle
    try:
        oracle.compile_source(src.encode() if isinstance(src, str) else src)
        return True
    except oracle.LuaCompileError:
        return False


def _run(src: str, tmp: Path) -> str:
    """Compile+run printed Lua source (via the repo's own lua_sz4 oracle) and
    return its stdout, decoded. Raises if it doesn't run cleanly.
    """
    from pyluadec import oracle
    r = oracle.run_bytes(src.encode(), is_source=True)
    assert r.returncode == 0, f"lua_sz4 run failed: {r.stderr.decode(errors='replace')}"
    return r.stdout.decode()


# ---- Step 1 tests (brief's exact sources) ---------------------------------

def test_straight_chunk_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local a = 1 local b = 2 print(a + b)", tmp_path))
    assert src is not None and _compiles(src)


def test_if_else_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local a = tonumber('1') if a < 3 then print('s') else print('b') end", tmp_path))
    assert src is not None and _compiles(src)


def test_numeric_for_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local s = 0 for i = 1, 10 do s = s + i end print(s)", tmp_path))
    assert src is not None and _compiles(src)


def test_closure_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = print_chunk(_proto("local n = 0 local f = function() return n end print(f())", tmp_path))
    assert src is not None and _compiles(src)


def test_unstructurable_chunk_returns_none(tmp_path):
    from pyluadec.emit.lua import print_chunk
    # `print_chunk` returns None (caller falls back) for anything build_sir
    # refuses. The sample has moved twice: `while` (structured by M4 task 3),
    # then the and/or VALUE idiom (reconstructed by M4 task 4). It is now the
    # BOOLEAN-value family -- a comparison used as a value rather than as a
    # branch condition, which `lcode.c:exp2reg` materialises with a LOADBOOL
    # pair (`need_value` is true because the jump list's control instruction
    # is not a TESTSET). Nothing in M4 recognizes that.
    # EXPIRY: whichever task reconstructs LOADBOOL value expressions; when it
    # lands this needs a different still-unstructurable sample (or deleting,
    # if none remains).
    assert print_chunk(_proto("local a, b = 1, 2 local x = (a or b) == 1 return x",
                              tmp_path)) is None
    # ...and both shapes it used to use now print.
    assert print_chunk(_proto("local i=0 while i<3 do i=i+1 end return i",
                              tmp_path)) is not None
    assert print_chunk(_proto("local a, b = 1, 2 local x = a or b return x",
                              tmp_path)) is not None


# ---- semantic tests: not just "compiles", but "runs to the right answer" --

def test_if_else_picks_the_correct_branch_both_ways(tmp_path):
    """A compiles-only check can't tell a correctly-polarised if/else from
    one with then/else silently swapped (both are syntactically valid Lua).
    Runs both the true and false side of an EQ-based condition and checks
    stdout picks the branch the *original* source would have picked --
    this is what actually pins the if/else polarity (see lua.py's module
    docstring, "Brief defects" #1) and is fault-injection target (c).
    """
    from pyluadec.emit.lua import print_chunk
    src_true = ("local a, b = 1, 1\n"
                "if a == b then print('EQ') else print('NE') end\n")
    src_false = ("local a, b = 1, 2\n"
                "if a == b then print('EQ') else print('NE') end\n")
    (tmp_path / "t1").mkdir(); (tmp_path / "t2").mkdir()
    printed_true = print_chunk(_proto(src_true, tmp_path / "t1"))
    printed_false = print_chunk(_proto(src_false, tmp_path / "t2"))
    assert printed_true is not None and printed_false is not None
    assert _run(printed_true, tmp_path).strip() == "EQ"
    assert _run(printed_false, tmp_path).strip() == "NE"


def test_test_opcode_if_picks_the_correct_branch_both_ways(tmp_path):
    """Same idea as above but for the TEST-opcode form of `if` (a bare
    truthiness test, not a comparison) -- EQ/LT/LE and TEST have
    independently-coded polarity in lua.py's condition(), so both need their
    own semantic pin.
    """
    from pyluadec.emit.lua import print_chunk
    src_truthy = "local x = true\nif x then print('T') else print('F') end\n"
    src_falsy = "local x = false\nif x then print('T') else print('F') end\n"
    (tmp_path / "t3").mkdir(); (tmp_path / "t4").mkdir()
    printed_truthy = print_chunk(_proto(src_truthy, tmp_path / "t3"))
    printed_falsy = print_chunk(_proto(src_falsy, tmp_path / "t4"))
    assert printed_truthy is not None and printed_falsy is not None
    assert _run(printed_truthy, tmp_path).strip() == "T"
    assert _run(printed_falsy, tmp_path).strip() == "F"


def _num(v: float):
    import struct
    from pyluadec.express.expr import ConstExpr
    from pyluadec.ingest import LuaNumber
    return ConstExpr(LuaNumber(value=float(v), payload=struct.pack("<d", float(v))))


# The next three tests hand-build Expr trees rather than compiling real Lua
# arithmetic through luac_sz4, deliberately: an earlier draft compiled
# `(a + b) * c` and `- -x` through real bytecode and found luac's register
# allocator reuses the ADD/first-UNM's destination register in place for the
# following MUL/second-UNM (`l4 = a+b` then `l4 = l4*c`, never a single
# nested expression) -- classify_registers correctly calls that register
# `local` (two static defs), so reconstruct.py never produces a *nested*
# BinExpr/UnExpr tree for it at all, and the test would have passed even
# with the precedence/comment-safety logic completely broken. Hand-building
# the tree and calling print_expr directly exercises the precedence logic
# itself, independent of whether any particular luac register allocation
# happens to produce a nested tree.

def test_nested_arithmetic_precedence_prints_correctly(tmp_path):
    """`(2 + 3) * 10` must not print as `2 + 3 * 10` (which reparses as
    `2 + (3 * 10)` = 32, not 50). Fault-injection target (a): dropping the
    parenthesisation logic entirely still compiles, it just computes the
    wrong answer -- so this runs the printed source and checks the number,
    not just that it compiles.
    """
    from pyluadec.emit.lua import print_expr
    from pyluadec.express.expr import BinExpr
    tree = BinExpr("*", BinExpr("+", _num(2), _num(3)), _num(10))
    text = print_expr(tree, depth=0)
    src = f"print({text})\n"
    assert _compiles(src)
    assert _run(src, tmp_path).strip() == "50"


def test_right_associative_subtraction_prints_correctly(tmp_path):
    """`10 - (3 - 1)` = 8 != `(10 - 3) - 1` = 6 for non-associative `-`;
    concat/pow right-associativity and `-`/`/` left-associativity hinge on
    the same lp/rp precedence arithmetic in lua.py's BinExpr branch, so a
    left-assoc case pins the general mechanism. Fault-injection target (a)."""
    from pyluadec.emit.lua import print_expr
    from pyluadec.express.expr import BinExpr
    tree = BinExpr("-", _num(10), BinExpr("-", _num(3), _num(1)))
    text = print_expr(tree, depth=0)
    src = f"print({text})\n"
    assert _compiles(src)
    assert _run(src, tmp_path).strip() == "8"


def test_double_unary_minus_does_not_become_a_comment(tmp_path):
    """`- -5` must never print as `--5`, which Lua's lexer reads as a line
    comment and silently deletes the rest of the line."""
    from pyluadec.emit.lua import print_expr
    from pyluadec.express.expr import UnExpr
    tree = UnExpr("-", UnExpr("-", _num(5)))
    text = print_expr(tree, depth=0)
    assert "--" not in text, f"comment-starting '--' token in: {text!r}"
    src = f"print({text})\n"
    assert _compiles(src)
    assert _run(src, tmp_path).strip() == "5"


def test_method_call_prints_colon_sugar(tmp_path):
    """`recv:foo(args)`, not `recv.foo(args)` (which passes one fewer
    argument -- no implicit self). Fault-injection target (d)."""
    from pyluadec.emit.lua import print_chunk
    src = ("local t = {}\n"
          "function t:greet(who) print('hi', self, who) end\n"
          "t:greet('world')\n")
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    # exact table address is unstable across runs; check the call actually
    # dispatched with `self` bound (three args printed, not two -- a dotted
    # call would print only "hi\tworld" with self silently absent).
    out = _run(printed, tmp_path).strip().split("\t")
    assert out[0] == "hi" and out[2] == "world" and len(out) == 3


def test_bare_local_decl_has_no_trailing_equals():
    """A LocalDecl with an empty exprs tuple (a bare `local a, b` from a
    mixed multi-result write, see Task 5's report) must print without a
    trailing `=` -- `local a, b = ` is a syntax error. Fault-injection
    target (b).

    Driven DIRECTLY on the printer since M7 task 8 (2026-08-15), by
    hand-building the statement. The mixed branch in
    `express/reconstruct.py` that produces such a decl (`_emit_multi`'s
    partially-demoted generic-for triple) is reachable only through a
    register the classifier gets *wrong*, and three classification fixes in
    a row each broke the previous end-to-end carrier: M4 task 13
    (per-definition classification killed `local ok, a = f()`), M6 task 12
    (constructor materialization stopped), M7 task 8 (the `_same_block`
    staging-span exemption stopped materializing the `and`/`or` iterator
    argument of `for k, v in pairs(x and {x} or {})`). Each break required
    re-deriving a source that mis-classifies in a NEW way -- pinning the
    printer to the classifier's bugs. The branch was measured at 0 corpus
    occurrences even before task 8 (12 distinct multi-register call sites:
    10 all-fresh, 2 all-declared, 0 mixed), so the hand-built form is the
    honest test: it asserts exactly what the branch does, independent of
    whether any input still reaches it.
    """
    from pyluadec.emit.lua import Printer
    from pyluadec.express.reconstruct import LocalDecl
    p = Printer.__new__(Printer)
    p.depth = 0
    line = p._local_decl(LocalDecl((3,), ()))
    assert line == "local l0_3"
    assert not line.rstrip().endswith("=")


def test_closure_captures_outer_local_and_returns_it(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = "local n = 41\nlocal f = function() return n + 1 end\nprint(f())\n"
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    assert _run(printed, tmp_path).strip() == "42"


def test_closure_in_call_position_is_parenthesised(tmp_path):
    """A `function() ... end` literal is a `simpleexp`, not a `prefixexp`,
    in the Lua 5.1 grammar -- it cannot be written directly before `(` the
    way a variable or another call can. This is reachable from unremarkable
    source: whenever an anonymous closure is called exactly once,
    immediately, and never bound to anything else afterward (e.g. an IIFE,
    or -- as here -- a helper defined then invoked once right after,
    register-classified single-use by classify_registers so reconstruct.py
    inlines the CLOSURE straight into the CALL's own `fn` position), the
    closure literal itself becomes `CallExpr.fn` and must print as
    `(function() ... end)()`, not `function() ... end()` (which luac_sz4
    rejects with "'end' expected ... near '('").
    """
    from pyluadec.emit.lua import print_chunk
    src = ("local function f()\n"
          "  return (function() return 42 end)()\n"
          "end\n"
          "print(f())\n")
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    assert _run(printed, tmp_path).strip() == "42"


def test_two_level_nested_closure_resolves_grandchild_upvalue_correctly(tmp_path):
    """A closure whose body is itself a closure whose body is a THIRD,
    innermost closure that references a local from the OUTERMOST scope
    (skipping the middle one, which never touches it directly) requires the
    middle closure to also capture that local as its own upvalue purely to
    hand it down (a GETUPVAL-sourced capture, not a MOVE-sourced one) --
    Printer.closure_parts' upvalue-name threading has to get this right at
    two levels of nesting, not just one. Every existing closure test before
    this one materialises its closure to a named local before calling it
    (never triggering the closure-in-call-position shape above), so this is
    the first test that exercises depth-2 upvalue chaining through to an
    actual compile-and-run.

    Uses subtraction (`a - b`, not `a + b`) so that a scrambled/swapped
    upvalue mapping between the two capture levels would produce a visibly
    wrong (sign-flipped) number rather than an accidentally-correct one:
    a=100, b=7 -> 93; if the two captures were swapped the result would
    print -93 instead.
    """
    from pyluadec.emit.lua import print_chunk
    src = ("local a = 100\n"
          "local function outer()\n"
          "  local b = 7\n"
          "  local function middle()\n"
          "    local function inner()\n"
          "      return a - b\n"
          "    end\n"
          "    return inner()\n"
          "  end\n"
          "  return middle()\n"
          "end\n"
          "print(outer())\n")
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    # Confirms this genuinely exercises three nesting levels, and that the
    # innermost body names BOTH captured locals at their own defining depths
    # (`a` from depth 0, `b` from depth 1) -- which is the depth-2 upvalue
    # chaining this test exists for. Until M3 task 8 the assertion here was
    # `printed.count("(function()") >= 2`, because the register classifier
    # inlined each `local function` literal straight into its call site; the
    # freereg model now correctly keeps them as the named locals the source
    # declared, so counting inlined closure-call sites no longer measures
    # nesting depth. `_run` below is unchanged and remains the real check.
    assert printed.count("function(") == 3, \
        f"expected 3 nested function literals in:\n{printed}"
    assert "l0_0 - l1_0" in printed, \
        f"innermost body must name both captured locals at their own depths:\n{printed}"
    assert _run(printed, tmp_path).strip() == "93"


def test_self_referential_local_function_prints_recursion_correctly(tmp_path):
    """`local function fact(n) ... fact(n-1) ... end` requires the
    `local function NAME(...) ... end` sugar (NAME visible to itself before
    the closure literal is even fully assigned) -- plain
    `local fact = function(n) ... fact(n-1) ... end` would resolve the
    inner `fact` as a global (nil), crashing at call time. Runs the printed
    recursive function and checks the actual numeric result.
    """
    from pyluadec.emit.lua import print_chunk
    src = ("local function fact(n)\n"
          "  if n <= 1 then return 1 end\n"
          "  return n * fact(n - 1)\n"
          "end\n"
          "print(fact(5))\n")
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    assert _run(printed, tmp_path).strip() == "120"


def test_generic_for_prints_compilable_and_runs(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = ("local t = {10, 20, 30}\n"
          "local sum = 0\n"
          "for i, v in ipairs(t) do sum = sum + v end\n"
          "print(sum)\n")
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    assert _run(printed, tmp_path).strip() == "60"


def test_table_constructor_with_nested_table_prints_compilable(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = "local t = {a = 1, b = {2, 3}, c = 4}\nprint(t.a, t.b[1], t.b[2], t.c)\n"
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    assert _run(printed, tmp_path).strip() == "1\t2\t3\t4"


def test_if_arms_do_not_share_local_declaration_state(tmp_path):
    """Each `if` arm is its own Lua block: a `local` declared in one arm must
    be re-declared in the other, not assigned to.

    Regression pin for the defect the L3 gate caught and M3 task 8 fixed. The
    `Reconstructor`'s `declared` set is deliberately shared across the whole
    SIR walk (a `for` header's staging temps are produced by the region before
    it), but Lua block scoping is not: with no per-block snapshot, the FIRST
    arm to write register 1 emitted `local l0_1 = 1` and recorded register 1
    as declared, so the second arm's write printed as a bare `l0_1 = 2` --
    which, register 1 not being in scope there, is a **write to a global**.
    Semantically wrong (SETGLOBAL where the original had a register write) and
    silent.

    Running the output does not catch this on its own: reading a global that
    the same chunk just wrote still prints 2. What catches it is that both
    arms must DECLARE, and that the chunk must certify -- luac confirming the
    printed source recompiles to this exact proto, which a stray SETGLOBAL
    cannot do.
    """
    from pyluadec import oracle
    from pyluadec.emit.lua import print_chunk
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.structured import certify_proto
    src = ("local c = false\n"
          "if c then local a = 1 print(a) else local b = 2 print(b) end\n")
    proto = _proto(src, tmp_path)
    printed = print_chunk(proto)
    assert printed is not None
    lines = [l.strip() for l in printed.splitlines()]
    i_if = next(i for i, l in enumerate(lines) if l.startswith("if "))
    i_else = lines.index("else")
    i_end = next(i for i in range(i_else, len(lines)) if lines[i] == "end")
    then_arm, else_arm = lines[i_if + 1:i_else], lines[i_else + 1:i_end]
    assert any(l.startswith("local ") for l in then_arm), printed
    assert any(l.startswith("local ") for l in else_arm), printed
    # This module's `_proto` compiles UNSTRIPPED (it exists to exercise the
    # printer), while certification compiles its candidate with -s to match
    # the golden dump path -- so the certification half needs its own stripped
    # copy of the same source, or it would fail on lineinfo/locvars alone.
    stripped = load_bytes(oracle.compile_source(src.encode(), strip=True))
    assert certify_proto(stripped, is_chunk_root=True).level == "L3"
    assert _run(printed, tmp_path).strip() == "2"


def test_non_ascii_string_constant_survives_print_certify_and_execution(tmp_path):
    r"""A non-UTF-8 string constant, used as both a value and a table key.

    This project exists to decompile a Japanese PSP visual novel: 17411 of the
    corpus's 49063 string constants contain a byte > 0x7f (measured 2026-08-11),
    and the predecessor project's documented crash mode was a bridge that threw
    on any constant that would not decode as UTF-8. Yet 0 of the 92 structured
    artifacts M3 ships contains a high byte -- every one of them is pure ASCII
    -- so nothing on the STRUCTURED path had ever printed one. (The fallback
    path has `tests/test_fallback_literals.py`; the structured printer shares
    `const_lit`/`str_lit` with it via `emit/lua.py`'s import, but sharing a
    helper is not the same as exercising it.)

    The bytes below are Shift-JIS 日本語. They are deliberately chosen so that a
    naive implementation is caught twice over:

    - the sequence is not valid UTF-8, so any decode-then-re-encode round trip
      (or `errors="replace"`) corrupts it;
    - `\x7b` is the trail byte of `\x96\x7b` and is also ASCII `{`, so a
      printer that escapes only "non-printable" bytes emits a bare `{` in the
      middle of a string literal. That happens to be harmless inside quotes,
      which is exactly why it needs a test rather than an eyeball.

    Three independent assertions, because each catches something the others do
    not: the printed text stays pure ASCII (so the artifact is safe to write to
    disk and hand to a downstream tool that assumes a byte-oriented surface),
    the chunk CERTIFIES (so luac's own constant table -- compared bitwise by
    `compare_protos` -- came back byte-identical), and it RUNS and writes the
    original bytes back out (so the escaping is semantically right, not merely
    stable under a round trip through our own two functions).
    """
    from pyluadec import oracle
    from pyluadec.emit.lua import print_chunk
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.structured import certify_proto

    RAW = b"\x93\xfa\x96\x7b\x8c\xea"                 # Shift-JIS 日本語
    assert any(b > 0x7f for b in RAW)
    try:
        RAW.decode("utf-8")
        raise AssertionError("fixture must not be valid UTF-8")
    except UnicodeDecodeError:
        pass

    src = (b'local t = {["' + RAW + b'"] = "' + RAW + b'"}\n'
           b'io.write(t["' + RAW + b'"])\n')
    original = load_bytes(oracle.compile_source(src, strip=True))

    printed = print_chunk(original)
    assert printed is not None
    payload = printed.encode()
    assert all(b <= 0x7f for b in payload), printed
    # Every high byte must appear as a fixed-width decimal escape, and the
    # ASCII-valued trail byte must NOT have been merged into the neighbouring
    # escape (`\150{`, not `\150123`, which Lua would read as one char).
    assert "\\147\\250\\150{\\140\\234" in printed, printed

    assert certify_proto(original, is_chunk_root=True).level == "L3"

    recompiled = load_bytes(oracle.compile_source(payload, strip=True))
    assert [k for k in recompiled.constants if isinstance(k, bytes)] == \
           [k for k in original.constants if isinstance(k, bytes)]

    r = oracle.run_bytes(payload, is_source=True)
    assert r.returncode == 0, r.stderr.decode(errors="replace")
    assert r.stdout == RAW


def test_ident_refusal_messages_do_not_quote_the_constant():
    """`_ident`'s two refusal messages must not carry the rejected constant.

    They travel: `structure.structured.certify_proto` catches the
    `ReconstructError` and writes its text into `corpus/ledger.jsonl` as the
    row's `refusal_reason`, so anything interpolated here ends up in a
    checked-in file. `name` is bytecode-derived string data (a global's name, a
    table key) out of a Japanese visual novel's script; the project rule is
    that such strings stay `bytes` and never reach a diagnostic. The messages
    carry the byte LENGTH instead, which is enough to find the constant in
    `luac_sz4 -l -l` output.

    Load-bearing check: restoring either message to its pre-M4-task-6 form
    (`f"identifier {name!r} ..."`) makes this test fail on the `"\\x93"` /
    `"world"` assertions -- verified by neutering both, 2026-08-11.
    """
    from pyluadec.emit.lua import _ident
    from pyluadec.express.reconstruct import ReconstructError

    assert _ident(b"hello") == "hello"

    RAW = b"\x93\xfa\x96\x7b"                          # Shift-JIS, not ASCII
    try:
        _ident(RAW)
        raise AssertionError("expected a refusal")
    except ReconstructError as exc:
        msg = str(exc)
    assert "4 bytes" in msg and "not ASCII" in msg
    assert "\\x93" not in msg and "\x93" not in msg

    try:
        _ident(b"hello world")                          # ASCII, not an identifier
        raise AssertionError("expected a refusal")
    except ReconstructError as exc:
        msg = str(exc)
    assert "11 bytes" in msg
    assert "world" not in msg

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


def test_while_returns_none(tmp_path):
    from pyluadec.emit.lua import print_chunk
    # while is not structured in M3 -> print_chunk returns None (caller falls back)
    assert print_chunk(_proto("local i=0 while i<3 do i=i+1 end return i", tmp_path)) is None


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


def test_bare_local_decl_has_no_trailing_equals(tmp_path):
    """A LocalDecl with an empty exprs tuple (a bare `local a, b` from a
    mixed multi-result write, see Task 5's report) must print without a
    trailing `=` -- `local a, b = ` is a syntax error. Fault-injection
    target (b). Source: `local function f() return 1, 2 end` followed by
    `local ok, a = f()` then a later use of `a` makes classify_registers
    treat `a`'s slot as an ordinary local while `ok`'s slot is genuinely
    single-use -- reconstruct.py's `_emit_multi` mixed case (confirmed by
    inspecting the printed source below: it contains a bare `local l0_2`
    line with no initialiser) declares the fresh one bare, then assigns the
    whole tuple. f() returns (1, 2), so the observable result of running
    this is deterministic: ok=1, a=2+1=3.
    """
    from pyluadec.emit.lua import print_chunk
    src = ("local function f() return 1, 2 end\n"
          "local ok, a = f()\n"
          "a = a + 1\n"
          "print(ok, a)\n")
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    assert any(line.strip().startswith("local ") and "=" not in line
              for line in printed.splitlines()), \
        f"expected a bare (no '=') local decl line in:\n{printed}"
    for line in printed.splitlines():
        stripped = line.rstrip()
        assert not stripped.endswith("="), f"trailing bare '=' in: {line!r}"
    assert _run(printed, tmp_path).strip() == "1\t3"


def test_closure_captures_outer_local_and_returns_it(tmp_path):
    from pyluadec.emit.lua import print_chunk
    src = "local n = 41\nlocal f = function() return n + 1 end\nprint(f())\n"
    printed = print_chunk(_proto(src, tmp_path))
    assert printed is not None
    assert _run(printed, tmp_path).strip() == "42"


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

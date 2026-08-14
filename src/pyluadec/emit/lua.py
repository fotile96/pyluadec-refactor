"""SIR + Expr -> Lua source text (spec §3 layer ⑥).

Discipline: this module is a **pure structural fold**. It walks the typed
region/expression trees this project already built (Task 1's SIR, Task 5's
Stmt/Expr) exactly once and emits strings on the way out. It never reads back,
re-scans, or post-processes any string it has already produced -- no peephole
passes, no fixed-point loops, no counting `do`/`then`/`end` tokens to find
block boundaries. That is precisely the failure mode that sank the
predecessor project (a 3712-line emitter with two layers of regex rewriting
over its own output); see tests/test_engineering_practice.py for the static
guard (`import re` is forbidden anywhere under this package).

Numeric/string literals always go through structure.fallback's `const_lit`
(itself `num_lit`/`str_lit`) -- those are already payload/byte-exact and are
not reimplemented here. Local names always go through
`express.names.name_for(reg, depth)`.

## Brief defects found (see task-6-report.md for the full account)

1. **If-condition polarity was backwards for both branches.** The task
   brief's illustrative `_print_condition` used `base if ri.a else not(base)`
   for EQ/LT/LE and `base if ri.c else not base` for TEST. Empirically
   probing real `luac_sz4` output for `if a==b then`/`if a~=b then` and
   `if x then`/`if not x then` (decoded via this project's own
   ingest/lift, cross-referenced against lvm.c's `dojump` mechanics) shows
   the OPPOSITE mapping: for EQ/LT/LE the fallthrough ("then") branch is the
   un-negated comparison when A==0 and the negated one when A==1; for TEST
   the fallthrough branch is the un-negated operand when C==0 and negated
   when C==1. `condition()` below uses the empirically-verified polarity.
   The brief itself flagged this exact risk as "oracle-arbitrated" and
   pre-authorized a TDD-against-luac fix, so this was corrected without
   pausing for confirmation; both `test_if_else_prints_compilable`-style
   semantic tests (which check *which branch actually runs*, not just that
   the output compiles) and the fault-injection round (c) pin the correct
   polarity.
2. **TEST's negation was unparenthesized in the brief's skeleton**
   (`f"not {base}"`), which is wrong whenever the tested operand itself has
   lower precedence than unary `not` (e.g. `if not (a + b) then` would have
   printed as `not a + b`, which reparses as `(not a) + b`). Fixed by
   building a real `UnExpr("not", operand)` and delegating to the same
   precedence-correct expression printer used everywhere else, rather than
   hand-formatting a second, less careful copy of the same logic.
3. **`ClosureExpr` was missing from the brief's own import list** for
   `express.expr`, even though the skeleton's `print_expr` dispatches on it
   and `_print_closure` is a whole documented section. Imported here.
4. **The documented interfaces don't quite line up with the skeleton.** The
   brief's prose promises `print_function(fn, region, rc, depth) -> str` but
   the skeleton never defines it (only `print_region`, which takes a bare
   `recon`); `recon` alone lacks the proto/fn/upval_names a `ClosureExpr`
   inside a statement needs. Resolved by introducing `Printer` (proto + fn +
   rc + recon + depth + upval_names bundled together) as the actual
   implementation; `print_function`, `print_chunk`, `print_expr`, and
   `print_region` are the public functions built on top of it -- matching
   the brief's own suggestion ("implement these as methods of a small
   `Printer` class... the module-level functions... remain as thin
   wrappers").
"""
from __future__ import annotations

from pyluadec.express.expr import (BinExpr, CallExpr, ClosureExpr, ConstExpr,
                                   Expr, GlobalExpr, IndexExpr, LocalExpr,
                                   MultiSpill, TableExpr, UnExpr, UpvalExpr,
                                   VarargExpr)
from pyluadec.express.names import RegClass, classify_registers, name_for
from pyluadec.express.reconstruct import (Assign, AssignTarget, ExprStmt,
                                          GlobalTarget, IndexTarget,
                                          LocalDecl, LocalTarget,
                                          Reconstructor, ReconstructError,
                                          ReturnStmt, Stmt, UpvalTarget)
from pyluadec.ingest.proto import Proto
from pyluadec.lift import LUA_KEYWORDS, Op
from pyluadec.lift.lift import LirFunction, LirInstr, lift_proto
from pyluadec.sir import (Break, CondNode, CondOp, CondTest, CondValue,
                          EndIter, GenericFor, If, NumericFor, Region, Repeat,
                          Return, Seq, Straight, While, WhileTrue)
from pyluadec.sir.build import StructureError, build_sir
# `emit` importing from `structure` is an emit -> structure dependency, and
# `structure.structured` itself imports FROM `emit.lua` (`print_chunk_or_raise`,
# `_print_proto_body`) -- so the two modules are mutually dependent through
# `fallback.py`, which is the layering half of M5 task 6's F9 finding (round 2
# review, Residual B). `const_lit` predates task 6 (peephole-era shared
# formatting); `inline_function_parts` is this task's own addition, needed
# because the hybrid boundary has to bind the substituted state machine to the
# ENCLOSING structured scope's own names (see `structured.py`'s module
# docstring, "Shipping"). Left as-is rather than given a new neutral home:
# this is the same unresolved-layering question already tracked for
# `LUA_KEYWORDS` (`lift/opcodes.py`, a decoder, holding a codegen concern) and
# the `f"{path}_{i}"` proto-path convention (`docs/runbooks/m3-backlog.md`
# section 14) -- a third instance of "the neutral home doesn't exist yet"
# does not get its own answer; it is recorded there rather than invented here.
from pyluadec.structure.fallback import (const_lit, inline_function_parts,
                                        str_lit)

# Lua 5.1 operator precedence (higher binds tighter; Lua reference manual
# §2.5.6). Used to add the minimal necessary parentheses when printing
# BinExpr/UnExpr -- over-parenthesising is always safe, under-parenthesising
# changes meaning.
_PREC = {"or": 1, "and": 2,
         "<": 3, ">": 3, "<=": 3, ">=": 3, "~=": 3, "==": 3,
         "..": 4, "+": 5, "-": 5, "*": 6, "/": 6, "%": 6,
         "unary": 7, "^": 8}
_RIGHT_ASSOC = frozenset({"..", "^"})
# Operators whose RIGHT operand needs no parentheses at its own precedence,
# because regrouping them changes neither the value nor the emitted code.
# `and`/`or` only, and the claim is narrow and measured rather than a general
# appeal to associativity: `lparser.c`'s `'(' expr ')'` arm calls
# `luaK_dischargevars`, which leaves an expression's true/false jump LISTS
# intact, so a parenthesised short-circuit operand is not "closed off" the way
# a parenthesised arithmetic sub-expression is. Measured 2026-08-14, six pairs
# compiled with the real `luac_sz4` and compared byte-for-byte
# (`tests/test_emit_readability.py::
# test_associative_and_or_chains_compile_identically`):
# `a and b and c`, `a or b or c`, `a and b and c and d` and their fully
# right-nested spellings are identical in `if`-condition and in value position.
#
# `and`/`or` are also the only ops that could benefit: they are the only two
# entries at their own precedence levels, so "same precedence" and "same
# operator" coincide, and a right child at a DIFFERENT precedence is still
# governed by the ordinary `prec < parent_prec` rule (`a and (b or c)` keeps
# its parentheses, `a or b and c` never had any). Added at M6 task 11 fix
# round 1: `sir.build._parse_cond` builds right-leaning trees, so without this
# every multi-operand condition printed as `a and (b and c)` -- the same class
# of output-surface regression M5 task 7 closed for `(-1)`.
_ASSOCIATIVE = frozenset({"and", "or"})
# Precedence demanded of the base of a call/index/method-call position
# (`X(...)`, `X[...]`, `X:m(...)`) -- higher than any real operator's own
# precedence, so any Bin/UnExpr used there always gets wrapped: `(a+b)()`,
# never `a+b()` (which would parse as `a + (b())`).
_PRIMARY_PREC = _PREC["^"] + 1
# Precedence assigned to every `simpleexp` node that is NOT also a
# `prefixexp` per the Lua 5.1 grammar (§8): `prefixexp ::= var |
# functioncall | '(' exp ')'`. A numeral/string/`nil`/`true`/`false`
# constant, a table constructor, a function literal (ClosureExpr), and `...`
# are all `simpleexp` but none of them is a `var`, a `functioncall`, or an
# already-parenthesised `exp` -- so none can be used bare immediately before
# `(`, `[`, `.`, or `:` (a position that grammatically requires a
# `prefixexp`). `_SIMPLE_PREC` sits one below `_PRIMARY_PREC` so these nodes
# print unparenthesised everywhere else (any ordinary operator/argument/
# table-item/return-value position only needs an `exp`) but get wrapped
# exactly when `parent_prec == _PRIMARY_PREC`, the same "prec < parent_prec"
# rule BinExpr/UnExpr already use. LocalExpr/GlobalExpr/UpvalExpr (all
# print as a bare `Name`, i.e. `var`) and IndexExpr/CallExpr (`var`/
# `functioncall` themselves) are true prefixexp and never need this.
_SIMPLE_PREC = _PRIMARY_PREC - 1


#: One indentation level. Four spaces, everywhere, function bodies included
#: -- "output surface v2" (M5 task 7 change 4; see
#: docs/runbooks/structured-pipeline.md). Through M5 task 6 this was two
#: spaces AND function bodies were not indented at all, so a chunk-level
#: `local f = function()` had its body flush at column 0 while an `if`
#: inside that body indented normally.
_INDENT = "    "


def _pad(indent: int) -> str:
    return _INDENT * indent


def _wrap_if_primary(text: str, parent_prec: int) -> str:
    return f"({text})" if _SIMPLE_PREC < parent_prec else text


def _as_ident(name: bytes) -> str | None:
    """`name` decoded as an emittable Lua identifier, or None if it is not one.

    No regex (forbidden in this package -- see module docstring): Python's
    `str.isidentifier()` covers the same character class as Lua's
    `[A-Za-z_][A-Za-z0-9_]*` once the string is known to be pure ASCII.

    THE single discrimination for "is this byte string a Lua Name", used in
    both directions: `_ident` below turns a `None` into a refusal (a global's
    name or a method name has no bracketed spelling to fall back to), while
    the index/table-key printers turn a non-`None` into `t.k` / `{k = 1}` and
    a `None` into `t["k"]` / `{["k"] = 1}`. Writing a second copy of the test
    for the sugar direction is exactly how the two would drift.
    """
    try:
        s = name.decode("ascii")
    except UnicodeDecodeError:
        return None
    if not s.isidentifier() or s in LUA_KEYWORDS:
        return None
    return s


def _ident(name: bytes) -> str:
    """Validate+decode a constant byte-string as an emittable Lua identifier,
    refusing if it is not one.

    ## Why the rejected constant is NOT in the message (M4 task 6)

    These two messages travel: a `ReconstructError` raised here is caught by
    `structure.structured.certify_proto`, and its text is written verbatim
    into the committed ledger as the row's `refusal_reason`. `name` is a
    bytecode-derived string -- a global's name, a table key -- straight out of
    the corpus's constant pool, so interpolating it would put corpus payload
    (this corpus is a Japanese visual novel's script) into a checked-in file,
    and `{name!r}` on non-ASCII bytes would put its hex escapes there. The
    project rule is that bytecode-derived strings stay `bytes` and are never
    decoded into diagnostics; a refusal message may name opcodes, pcs and
    registers, never data. The length is enough to find the constant in
    `luac_sz4 -l -l` output. Pinned by
    `tests/test_emit_lua.py::test_ident_refusal_messages_do_not_quote_the_constant`.
    """
    s = _as_ident(name)
    if s is None:
        # The two refusals stay distinct (ASCII vs not-a-Name): they say
        # different things about the constant and the ASCII one is the
        # informative case for this corpus.
        try:
            name.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ReconstructError(
                f"identifier constant ({len(name)} bytes) is not ASCII") from exc
        raise ReconstructError(f"identifier constant ({len(name)} bytes) "
                               "is not emittable as a Lua name")
    return s


def _str_lit(bs: bytes) -> str:
    """A string constant as a double-quoted Lua literal, printing readable
    UTF-8 raw and falling back to `structure.fallback.str_lit`'s decimal
    escapes for anything else.

    ## The red line, and the amendment this implements

    The standing project rule is that bytecode-derived strings are `bytes` and
    are never decoded. CLAUDE.md's red-line bullet now scopes that: it binds
    ingest, lift and the comparison layer absolutely, and allows the PRINTING
    layer a **decision with a fallback** -- print raw when the bytes are
    reversible UTF-8, decimal-escape otherwise -- because both spellings
    compile to the same constant and the certification gate adjudicates that
    they do. Approved by the human partner 2026-08-12; landed in M5 task 7.

    It is scoped to `emit/`. `structure/fallback.py::str_lit` is unchanged and
    still escapes everything, which is why a whole-file fallback artifact (and
    the substituted subtree of a hybrid one) still shows `"\\227\\128\\144"`.
    Nothing under `ingest`, `lift` or `verify` decodes anything.

    Why it matters here and not in most decompilers: this corpus is a Japanese
    visual novel's script and the artifact's whole purpose is translation.
    `"\\227\\128\\144\\231\\155\\180\\229\\147\\137\\227\\128\\145"` against
    the predecessor's `"【直哉】"` was named the single largest readability
    gap in `docs/reports/m4-readability.md`.

    ## The gate

    Three conditions, all of which must hold to print raw:

    1. `bs.decode("utf-8")` succeeds (strict: no overlongs, no surrogates,
       nothing above U+10FFFF).
    2. Re-encoding gives back exactly `bs`. **This second check is
       DEFENSIVE**, not a case anyone has produced: Python's strict UTF-8
       codec is a bijection on the sequences it accepts. Measured 2026-08-12
       by brute force -- all 18432 decodable 1- and 2-byte sequences and all
       61440 decodable 3-byte sequences with a lead byte in `E0..F4` re-encode
       identically, 0 mismatches. Kept because it is the property that makes
       the raw form provably byte-exact, and because it is one comparison
       against a rule the whole amendment rests on.
    3. The string is not pure ASCII. A pure-ASCII string gains nothing from
       this path and is delegated to `str_lit`, which makes "ASCII output is
       unchanged by the amendment" a one-line argument rather than a diff.

    What still gets escaped in the raw form: `"` and `\\` (Lua would
    misparse them), and every byte below 32 plus DEL. `llex.c::read_string`
    errors on a raw `\\n`/`\\r` inside a string and treats EOZ as unterminated,
    so those must not appear literally; every other byte, including every
    multi-byte UTF-8 continuation, is copied verbatim by the lexer. That is
    also why nothing here needs to worry about U+2028 and friends -- Lua 5.1's
    lexer is byte-oriented and has no notion of them.
    """
    try:
        s = bs.decode("utf-8")
    except UnicodeDecodeError:
        return str_lit(bs)
    if s.encode("utf-8") != bs or s.isascii():
        return str_lit(bs)
    out = ['"']
    for ch in s:
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ord(ch) < 32 or ord(ch) == 127:
            # Same fixed three-digit form `str_lit` uses, and for the same
            # reason: `"\\10" "0"` would otherwise read as `\\100`.
            out.append("\\%03d" % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _index(base: str, key: Expr, depth: int, ctx: "Printer | None",
           indent: int) -> str:
    """`base.k` when `key` is a constant string that is a Lua Name, else
    `base[<key>]`.

    Sugar only. `lparser.c`'s `primaryexp` reaches `luaK_indexed` with the
    same `VK` constant either way -- `'.'` goes through `field` ->
    `checkname` -> `codestring`, `'['` through `yindex` -> `expr` +
    `luaK_exp2val`, and a string literal's `expr` is already `VK`. Measured:
    `luac_sz4` compiles `t.k = 1 print(t.k)` and `t["k"] = 1 print(t["k"])`
    byte-identically (tests/test_emit_readability.py::
    test_bracketed_string_key_and_dot_key_compile_identically).

    Shared by the expression printer and `Printer.target` so an index and an
    assignment to that same index cannot spell themselves differently.
    """
    if isinstance(key, ConstExpr) and isinstance(key.value, bytes):
        name = _as_ident(key.value)
        if name is not None:
            return f"{base}.{name}"
    return f"{base}[{_expr(key, depth, 0, ctx, indent)}]"


def _expr(e: Expr, depth: int, parent_prec: int, ctx: "Printer | None",
          indent: int) -> str:
    """The real expression-printing dispatch, shared by the context-free
    `print_expr` (ctx=None; usable on any tree with no ClosureExpr/UpvalExpr)
    and `Printer.expr` (ctx=the enclosing function's Printer, needed to name
    upvalues and to print nested closures' bodies).
    """
    if isinstance(e, ConstExpr):
        if isinstance(e.value, bytes):
            # The presentation path (M5 task 7 change 5). `const_lit` would
            # route this to `structure.fallback.str_lit`; `_str_lit` prints
            # reversible UTF-8 raw and delegates to that same function for
            # everything else, so the fallback emitter's spelling stays the
            # single escape implementation.
            return _wrap_if_primary(_str_lit(e.value), parent_prec)
        txt = const_lit(e.value, parenthesize_negative=False)
        if txt.startswith("-"):
            # A negative numeral is, to Lua's grammar, unary minus applied to
            # a numeral (`llex.c` never produces a signed number token; the
            # `-` is `subexpr`'s UNARY_PRIORITY operator, and `lcode.c`'s
            # `constfolding` is what turns it back into one constant). So it
            # takes unary precedence from the table above, and gets its
            # parentheses in exactly the positions any other unary expression
            # would: left of `^`, and as the base of a call/index/method.
            # `_SIMPLE_PREC`, which every other constant uses, would
            # under-parenthesise it (`-1 ^ 2` reparses as `-(1 ^ 2)`).
            #
            # This is a property of the numeral token, read off the single
            # character that makes it one; it is not a re-parse of emitted
            # output (`num_lit` makes the same test one line lower to decide
            # whether the default wrapping applies).
            prec = _PREC["unary"]
            return txt if prec >= parent_prec else f"({txt})"
        return _wrap_if_primary(txt, parent_prec)
    if isinstance(e, LocalExpr):
        return name_for(e.reg, depth)
    if isinstance(e, GlobalExpr):
        return _ident(e.name)
    if isinstance(e, UpvalExpr):
        if ctx is None:
            raise ReconstructError("UpvalExpr needs Printer context; use print_function")
        return ctx.upval_name(e.idx)
    if isinstance(e, VarargExpr):
        return _wrap_if_primary("...", parent_prec)
    if isinstance(e, ClosureExpr):
        if ctx is None:
            raise ReconstructError("ClosureExpr needs Printer context; use print_function")
        params, body = ctx.closure_parts(e, indent)
        # The body was printed at `indent + 1` and the closing `end` sits at
        # `indent` -- the same shape every block gets, and the reason a
        # closure literal appearing anywhere inside an expression still lines
        # up with the statement that contains it.
        return _wrap_if_primary(
            f"function({params})\n{body}{_pad(indent)}end", parent_prec)
    if isinstance(e, IndexExpr):
        return _index(_expr(e.table, depth, _PRIMARY_PREC, ctx, indent),
                      e.key, depth, ctx, indent)
    if isinstance(e, TableExpr):
        items = [_expr(x, depth, 0, ctx, indent) for x in e.array]
        for k, v in e.hash:
            # Same sugar as `_index`, at the constructor's own syntax:
            # `lparser.c::recfield` takes `TK_NAME` -> `checkname` or `'['` ->
            # `yindex` and joins on one `luaK_codeABC(fs, OP_SETTABLE, ...)`,
            # so `{k = 1}` and `{["k"] = 1}` are the same constant in the same
            # instruction (measured byte-identical).
            name = (_as_ident(k.value)
                    if isinstance(k, ConstExpr) and isinstance(k.value, bytes)
                    else None)
            # Key BEFORE value, as before: `_expr` runs against a stateful
            # Reconstructor and a `[<expr>] = <expr>` pair can consume staged
            # registers in either slot. (A key that took the sugar is a
            # `ConstExpr` and renders nothing, so skipping it is free.)
            key_txt = None if name is not None else _expr(k, depth, 0, ctx, indent)
            val = _expr(v, depth, 0, ctx, indent)
            items.append(f"{name} = {val}" if name is not None
                         else f"[{key_txt}] = {val}")
        return _wrap_if_primary("{" + ", ".join(items) + "}", parent_prec)
    if isinstance(e, CallExpr):
        args = ", ".join(_expr(a, depth, 0, ctx, indent) for a in e.args)
        fn_txt = _expr(e.fn, depth, _PRIMARY_PREC, ctx, indent)
        if e.is_method:
            assert e.method is not None
            return f"{fn_txt}:{_ident(e.method)}({args})"
        return f"{fn_txt}({args})"
    if isinstance(e, UnExpr):
        prec = _PREC["unary"]
        inner = _expr(e.operand, depth, prec, ctx, indent)
        # `not` always needs a separator (`notx` is one identifier). `-` needs
        # one only against another leading `-`: `--` is a Lua COMMENT, so
        # `- -x` (two UNM instructions) or `- -1` (UNM over a negative
        # numeral, newly reachable since change 3 stopped parenthesising those)
        # would silently delete the rest of the line. `#` never needs one.
        #
        # Through M5 task 6 this was `e.op in ("not", "-")` -- unconditional,
        # "simpler than special-casing the one dangerous adjacency". Change 3
        # narrows it to the dangerous adjacency itself, because `- l0_0` is
        # exactly the kind of thing this task exists to fix and because the
        # numeral case makes the adjacency more common, not less. Testing the
        # first character of the operand's own text is a lexical
        # token-separation decision made while composing the token, not a
        # re-parse of emitted statements.
        sep = " " if (e.op == "not" or (e.op == "-" and inner.startswith("-"))) else ""
        out = f"{e.op}{sep}{inner}"
        return f"({out})" if prec < parent_prec else out
    if isinstance(e, BinExpr):
        prec = _PREC[e.op]
        lp = prec + (1 if e.op in _RIGHT_ASSOC else 0)
        rp = prec + (0 if e.op in _RIGHT_ASSOC or e.op in _ASSOCIATIVE else 1)
        out = (f"{_expr(e.lhs, depth, lp, ctx, indent)} {e.op} "
               f"{_expr(e.rhs, depth, rp, ctx, indent)}")
        return f"({out})" if prec < parent_prec else out
    raise ReconstructError(f"unprintable expression {type(e).__name__}")


def print_expr(e: Expr, depth: int, parent_prec: int = 0, indent: int = 0) -> str:
    """Print an expression tree that contains no ClosureExpr/UpvalExpr node.

    Convenience entry point (precedence/formatting can be tested without
    building a whole function's Printer context). ClosureExpr/UpvalExpr need
    to know their enclosing function's proto/fn/upval_names, which only a
    `Printer` (see `print_function`) carries.
    """
    return _expr(e, depth, parent_prec, None, indent)


class Printer:
    """Per-function printing context.

    Bundles what every part of one function's region tree needs while being
    printed: its own LIR (`fn`, for CLOSURE pseudo-instruction lookup), its
    Proto (`proto`, for subprotos), its register classification (`rc`), the
    ONE `Reconstructor` shared across every region of this function walked in
    program order (see `express.reconstruct.Reconstructor`'s docstring for
    why sharing matters -- a `for` header's init/limit/step are staged as
    temps by the Straight region immediately before it), this function's
    nesting `depth` (disambiguates `name_for` across nested closures reusing
    the same register numbers), and the upvalue names visible inside it
    (threaded down from the enclosing CLOSURE site; empty for the top-level
    chunk).
    """

    def __init__(self, fn: LirFunction, rc: RegClass, depth: int,
                upval_names: tuple[str, ...] = (), path: str = "main",
                fallback_paths: frozenset[str] = frozenset()):
        self.fn = fn
        self.proto = fn.proto
        self.rc = rc
        self.depth = depth
        self.upval_names = upval_names
        # This function's `proto_path` (the `walk_proto_paths` convention) and
        # the set of paths whose subtree ships as the fallback state machine
        # instead of as structured code (M5 task 6). Empty for an ordinary
        # whole-tree print, in which case nothing below behaves differently.
        self.path = path
        self.fallback_paths = fallback_paths
        self.recon = Reconstructor(fn, rc, depth, upval_names)
        # proto_idx -> the pc of the (single) CLOSURE instruction that
        # produced it. A subproto index is only ever the Bx operand of
        # exactly one CLOSURE instruction in its parent (each `function...
        # end` literal in the source compiles to its own unique subproto
        # entry); a duplicate would mean this function's bytecode is not
        # what lift_proto assumed, so refuse rather than pick one silently.
        self._closure_pc_by_idx: dict[int, int] = {}
        for pc, li in fn.instrs.items():
            if li.ri.op is Op.CLOSURE:
                if li.ri.bx in self._closure_pc_by_idx:
                    raise ReconstructError(
                        f"subproto index {li.ri.bx} produced by more than "
                        "one CLOSURE instruction")
                self._closure_pc_by_idx[li.ri.bx] = pc
        self._implicit_return_pc = _implicit_return_pc(fn)

    # ---- expressions --------------------------------------------------
    def expr(self, e: Expr, parent_prec: int = 0, *, indent: int = 0) -> str:
        return _expr(e, self.depth, parent_prec, self, indent)

    def upval_name(self, idx: int) -> str:
        if not (0 <= idx < len(self.upval_names)):
            raise ReconstructError(f"upvalue index {idx} has no name (nups mismatch)")
        return self.upval_names[idx]

    def _closure_pc(self, idx: int) -> int:
        pc = self._closure_pc_by_idx.get(idx)
        if pc is None:
            raise ReconstructError(f"no CLOSURE instruction found for subproto index {idx}")
        return pc

    def closure_parts(self, e: ClosureExpr, indent: int = 0) -> tuple[str, str]:
        """(params, body) for a CLOSURE literal -- `function(params)\\nbody`
        with the caller responsible for the leading `function`/`local
        function NAME` keyword and the trailing `end`.

        Upvalue names come from the CLOSURE's own pseudo-instructions
        (recorded by lift.py in `fn.closure_pseudo[pc]`, in child-upvalue-
        index order): a MOVE pseudo means the child's upvalue is this
        (parent) function's local `name_for(B, self.depth)`; a GETUPVAL
        pseudo means it is this function's own `upval_names[B]`.
        """
        pc = self._closure_pc(e.proto_idx)
        child = self.proto.subprotos[e.proto_idx]
        names: list[str] = []
        for ps in self.fn.closure_pseudo[pc]:
            if ps.op is Op.MOVE:
                names.append(name_for(ps.b, self.depth))
            elif ps.op is Op.GETUPVAL:
                names.append(self.upval_name(ps.b))
            else:
                raise ReconstructError(
                    f"pc {pc}: unexpected CLOSURE pseudo-instruction {ps.op.name}")
        # Fourth (and, unlike the three in `walk_proto_paths`' docstring,
        # load-bearing at *certification* time) spelling of the proto_path
        # convention: this is the key looked up in `fallback_paths`, so a
        # disagreement here would substitute the wrong function.
        child_path = f"{self.path}_{e.proto_idx}"
        if child_path in self.fallback_paths:
            # The hybrid boundary. The structured printer must not guess at a
            # subtree it could not certify, so the hole is filled by the
            # semantically-exact state machine, bound to THESE names.
            return inline_function_parts(child, child_path, tuple(names))
        params = ", ".join(name_for(i, self.depth + 1) for i in range(child.numparams))
        if child.is_vararg & 2:
            params = params + (", ..." if params else "...")
        # One call shape, always. Round 1 of M5 task 6 branched here on `if not
        # self.fallback_paths` and called a 3-argument form, purely to keep the
        # monkeypatch seam `tests/test_effects_reconstructor_consistency.py`
        # installs over this module's `_print_proto_body` working unchanged.
        # The cost of that convenience was that the hybrid print path silently
        # bypassed the instrumentation -- the one path where a
        # reconstructor/effects disagreement is hardest to spot -- while
        # `structured._plan_substitutions` called the 5-argument form
        # unconditionally anyway. The seam now takes what production passes.
        return params, _print_proto_body(child, self.depth + 1, tuple(names),
                                         child_path, self.fallback_paths,
                                         indent + 1)

    def _closure_self_ref(self, e: ClosureExpr, target_reg: int) -> bool:
        """True iff the closure captures its own assignment target as an
        upvalue -- the bytecode shape luac emits for `local function NAME(
        ...) ... NAME() ... end` (NAME visible to itself for recursion).
        Printing that as plain `local NAME = function()...end` would be
        wrong: at that statement's RHS, NAME is not in scope yet (Lua local
        declarations only become visible after their own statement), so the
        reference inside the body would resolve to something else entirely
        (typically a global), changing the closure's upvalue count on
        recompile. `local function NAME(...)...end` sugar (NAME declared
        bare, then assigned) is required instead -- see `_local_decl`.
        """
        pc = self._closure_pc(e.proto_idx)
        return any(ps.op is Op.MOVE and ps.b == target_reg
                   for ps in self.fn.closure_pseudo[pc])

    # ---- statements -----------------------------------------------------
    def target(self, t: AssignTarget, indent: int = 0) -> str:
        if isinstance(t, LocalTarget):
            return name_for(t.reg, self.depth)
        if isinstance(t, GlobalTarget):
            return _ident(t.name)
        if isinstance(t, IndexTarget):
            return _index(self.expr(t.table, _PRIMARY_PREC, indent=indent),
                          t.key, self.depth, self, indent)
        if isinstance(t, UpvalTarget):
            return self.upval_name(t.idx)
        raise ReconstructError(f"unprintable target {type(t).__name__}")

    def stmt(self, s: Stmt, indent: int = 0) -> str:
        if isinstance(s, LocalDecl):
            return self._local_decl(s, indent)
        if isinstance(s, Assign):
            tgts = ", ".join(self.target(t, indent) for t in s.targets)
            vals = ", ".join(self.expr(e, indent=indent) for e in s.exprs)
            return f"{tgts} = {vals}"
        if isinstance(s, ExprStmt):
            return self.expr(s.call, indent=indent)
        if isinstance(s, ReturnStmt):
            if not s.exprs:
                return "return"
            return "return " + ", ".join(self.expr(e, indent=indent)
                                         for e in s.exprs)
        raise ReconstructError(f"unprintable statement {type(s).__name__}")

    def _local_decl(self, s: LocalDecl, indent: int = 0) -> str:
        names = ", ".join(name_for(r, self.depth) for r in s.regs)
        if not s.exprs:
            # A bare declaration (`local a, b`, no initialiser -- see the
            # module docstring / task-6-report "fault injection (b)"): NOT
            # "local a, b = ", which is a syntax error (an `=` demands at
            # least one expression on its right).
            return f"local {names}"
        if (len(s.regs) == 1 and len(s.exprs) == 1
                and isinstance(s.exprs[0], ClosureExpr)
                and self._closure_self_ref(s.exprs[0], s.regs[0])):
            params, body = self.closure_parts(s.exprs[0], indent)
            return (f"local function {names}({params})\n"
                    f"{body}{_pad(indent)}end")
        vals = ", ".join(self.expr(e, indent=indent) for e in s.exprs)
        return f"local {names} = {vals}"

    def condition(self, cond: "LirInstr | CondNode", indent: int = 0) -> str:
        """Render a comparison/TEST instruction -- or a whole `and`/`or`
        condition TREE -- as the boolean expression that is true exactly when
        control **falls through** past the JMP that follows it.

        Three callers, all wanting exactly that expression:
          - `If`: the fallthrough is the `then_body`, so this IS the `if`
            condition.
          - `While`: the fallthrough is the loop body, so this IS the `while`
            condition.
          - `Repeat`: `lparser.c`'s `repeatstat` patches the condition's
            *false* list back to the loop header (`cond()` is
            `luaK_goiftrue`, which yields the jump taken when the source
            condition is false), so the backward JMP is taken exactly when the
            source's `until` condition is false and the fallthrough -- past
            the JMP, out of the loop -- is exactly the `until` condition. So
            `until <this expression>` is right, un-negated.

        Polarity, and the reason it is not decided here: it lives in
        `Reconstructor.condition_expr`, which returns the same condition as a
        typed Expr. `CondValue` (M4 task 4) needs it as an Expr rather than as
        text -- an `and`/`or` gate nests the condition inside a
        `BinExpr("and", ...)` and lets the expression printer decide the
        parentheses -- and two independent copies of a polarity rule this
        project has already gotten backwards once (see module docstring "Brief
        defects" #1) is exactly the drift worth designing out. This method is
        now a `self.expr(...)` around that single source of truth; the
        rendered text is unchanged.

        `indent` is the enclosing block's depth and reaches exactly one thing:
        the body of a closure literal appearing INSIDE the condition, which
        `_expr` prints at `indent + 1` with its `end` at `indent`. Every other
        expression form ignores it. All three callers pass it as of M5 task
        12; before that `While`/`Repeat` passed nothing, so a closure in a
        `while`/`until` condition would have had its body printed at column 0.
        Cosmetic only, and unobservable on this corpus: over all 1944 protos
        `build_sir` produces 208 `While` regions and 0 `Repeat` regions, and
        **0** of the pcs those regions claim outside their bodies decode to
        `CLOSURE` (measured 2026-08-13; `build/decompiled/` and
        `corpus/ledger.jsonl` are byte-identical across the change). It is fixed
        anyway because "the printer indents uniformly" is a property, and a
        property with a hole in it that only a future corpus can show is the
        kind this project has been repeatedly wrong about.

        `If.negated`/`Repeat.negated` are deliberately NOT consulted: the
        polarity is derived from the instruction's own A/C field, which is the
        single source of truth both region kinds carry. (`If.negated` has
        always been informational in this printer; `Repeat.negated` is defined
        the same way so the two cannot drift apart.)

        A `CondNode` (M6 task 11, `If` only) delegates to
        `Reconstructor.cond_tree_expr` instead, and stays a fold for the same
        reason the single-instruction case is: the whole `and`/`or` structure
        lives in the Expr tree, and every parenthesis comes from `_PREC`
        (`or` 1, `and` 2, both left-associative), never from this method
        deciding anything. `a and b or c` therefore prints bare, `a and (b or
        c)` gets exactly one pair, and no constant/closure/`...` node can
        acquire a spurious pair the way one left of `^` does -- `_SIMPLE_PREC`
        is 9, above both.
        """
        try:
            if isinstance(cond, (CondTest, CondOp)):
                return self.expr(self.recon.cond_tree_expr(cond), indent=indent)
            return self.expr(self.recon.condition_expr(cond), indent=indent)
        except ReconstructError as exc:
            # Region-level refusal, as before: a region whose condition slot
            # holds a non-condition opcode is an unstructurable shape, not a
            # reconstruction accident. `print_chunk` catches both, but the
            # distinction is what the callers' own tests assert on.
            raise StructureError(str(exc)) from exc

    # ---- regions --------------------------------------------------------
    def region(self, r: Region, indent: int) -> list[str]:
        pad = _pad(indent)
        if isinstance(r, Straight):
            return [pad + self.stmt(s, indent)
                    for s in self.recon.stmts_for(r.instrs)]
        if isinstance(r, Seq):
            out: list[str] = []
            for child in r.body:
                out += self.region(child, indent)
                if _terminates(child):
                    # Everything after an unconditional return/break in the
                    # same block is unreachable padding (typically luac's
                    # own trailing implicit `RETURN 0 1`) -- printing it
                    # would be a Lua 5.1 syntax error, not just dead code.
                    # See _terminates' docstring.
                    break
            return out
        if isinstance(r, Return):
            if r.instr.ri.pc == self._implicit_return_pc:
                # luac's own appended `RETURN 0 1` -- has no source-level
                # counterpart, so printing it would make the recompile emit
                # two. See `_implicit_return_pc`.
                return []
            return [pad + self.stmt(s, indent)
                    for s in self.recon.stmts_for((r.instr,))]
        if isinstance(r, Break):
            return [pad + "break"]
        if isinstance(r, CondValue):
            # The whole and/or chain is ONE assignment (or, when the target is
            # an inlinable temp, zero statements plus a staged expression the
            # consumer inlines). All the structure lives in the Expr tree
            # `Reconstructor.cond_value` builds; this arm stays a fold.
            return [pad + self.stmt(s, indent) for s in self.recon.cond_value(r)]
        if isinstance(r, If):
            out = []
            # Each arm is its own Lua block: a `local` one arm declares is not
            # in scope in the other, nor after the `end`. See
            # Reconstructor.open_scope for what went wrong without this.
            #
            # ONE snapshot PER RUNG, kept on a stack. What is load-bearing is
            # WHEN each snapshot is taken, not any property of the object:
            # `open_scope` returns a fresh value (frozensets plus a dict copy)
            # and holds no reference to the Reconstructor, so two rungs cannot
            # "share" one in the aliasing sense at all. Rung k's snapshot has
            # to be taken after rung k's own condition -- and after any staging
            # its `Straight` prefix did -- because the recursive form this
            # loop replaced called `open_scope()` at exactly that point, and a
            # later rung's snapshot legitimately contains staged temps that an
            # earlier one predates. Rolling a later rung back to an earlier
            # snapshot discards them.
            #
            # Measured 2026-08-13 (M5 task 12), two neuters, each named:
            #   (a) take ONE snapshot above the chain and roll every rung back
            #       to it (per-rung `close_scope` kept), and
            #   (b) take ONE snapshot above the chain and close it once after
            #       the chain,
            # both turn tests/test_semantic_regressions.py::
            # test_while_true_break_guard_recovers_loop from `L3` to `L1`
            # (`assert 'L1' == 'L3'`; the printer refuses with "register 0 is
            # being given a new value while the expression staged in register 2
            # still refers to it by name"). An M5 task 7 review reported that
            # "sharing the snapshot OBJECT changes nothing" and that only the
            # hoist reproduces; re-measured here, (a) is the hoist -- there is
            # no third variant, because a value cannot be shared any other way.
            #
            # The stack is unwound after the loop, innermost first, which is
            # exactly the sequence of `close_scope(snap)` calls the recursive
            # form made on its way back out.
            snaps: list = []
            node, keyword = r, "if"
            while True:
                # Rendered INSIDE the loop and before this rung's snapshot,
                # matching where the recursive form evaluated a nested `If`'s
                # condition (`self.condition(r.cond)` precedes
                # `self.recon.open_scope()`).
                cond = self.condition(node.cond, indent)
                out.append(f"{pad}{keyword} {cond} then")
                snap = self.recon.open_scope()
                snaps.append(snap)
                out += self.region(node.then_body, indent + 1)
                self.recon.close_scope(snap)
                nested, prefix = _split_else(node.else_body)
                staged: list[str] = []
                if nested is not None:
                    # The else-arm of an `elseif` is never *just* the nested
                    # `If`: `sir.build` gives the nested condition's operand
                    # code (`GETGLOBAL b`, ...) its own `Straight` sibling in
                    # front of it. Those siblings reconstruct to ZERO
                    # statements -- pure staging into the Reconstructor's env
                    # -- and that is exactly the condition under which the
                    # collapse is safe. Rendering them first and checking that
                    # they produced no lines is what makes it a fold: they are
                    # rendered once, in program order, at the indent they
                    # would need in the `else` spelling, and their emptiness
                    # (not their text) picks the keyword. A sibling that DOES
                    # produce statements falls through to a real `else` below
                    # with those statements in place -- printing `elseif`
                    # there would silently drop them.
                    for pre in prefix:
                        staged += self.region(pre, indent + 1)
                if nested is not None and not staged:
                    # `else` + exactly one `if` IS `elseif`, and this is a
                    # spelling change only. `lparser.c::ifstat` handles ELSEIF
                    # by `luaK_concat(escapelist, luaK_jump())` +
                    # `luaK_patchtohere(flist)` + `test_then_block`, and ELSE
                    # by the same two calls + `block()`; the only difference
                    # is the wrapper `enterblock`/`leaveblock` that `block()`
                    # adds around the inner `ifstat`, which emits an
                    # instruction only when `bl->upval` is set -- and
                    # `markupval` sets that on the inner THEN block, never on
                    # the wrapper. Both forms then close with
                    # `luaK_patchtohere(escapelist)` at the same `fs->pc`.
                    # Mechanized in tests/test_emit_readability.py::
                    # test_elseif_and_nested_if_in_else_compile_identically
                    # (the two spellings compile byte-identically).
                    #
                    # This is a fold, not a post-pass: the chain is walked
                    # once, top down, and no emitted line is ever revisited.
                    node, keyword = nested, "elseif"
                    continue
                if nested is not None:
                    # Collapse refused: the arm has real statements before its
                    # `if`. `prefix` has already been rendered into `staged`
                    # (in program order, at the `else` block's indent), so
                    # emit the `else` header, then those lines, then the
                    # trailing `If` -- the same text the plain recursive
                    # `self.region(else_body, indent + 1)` would have produced.
                    out.append(f"{pad}else")
                    out += staged
                    out += self.region(nested, indent + 1)
                    self.recon.close_scope(snap)
                elif node.else_body is not None:
                    out.append(f"{pad}else")
                    out += self.region(node.else_body, indent + 1)
                    self.recon.close_scope(snap)
                break
            # Unwind the enclosing rungs' snapshots, innermost first. The
            # innermost (`snaps[-1]`) was already closed inside the loop, by
            # whichever arm ended the chain -- the same double `close_scope`
            # the recursive form did for a leaf `If`.
            for outer in reversed(snaps[:-1]):
                self.recon.close_scope(outer)
            out.append(f"{pad}end")
            return out
        if isinstance(r, NumericFor):
            a = r.prep.ri.a
            var = name_for(a + 3, self.depth)
            init = self.expr(self.recon.take_expr(a), indent=indent)
            limit = self.expr(self.recon.take_expr(a + 1), indent=indent)
            step = self.expr(self.recon.take_expr(a + 2), indent=indent)
            out = [f"{pad}for {var} = {init}, {limit}, {step} do"]
            # A loop body is its own block, same as an `if` arm. Unlike the
            # `if` case this is defensive rather than a fixed defect: a
            # register whose FIRST write is inside a loop body sits above
            # everything still live after the loop (the body's locals and the
            # header's own slots are all released at `end`), so luac cannot
            # produce a shape where such a register is written again
            # afterwards -- there is no reachable leak to regress against.
            # Kept for symmetry and for non-luac input; see
            # Reconstructor.open_scope.
            snap = self.recon.open_scope()
            self.recon.declare_loop_vars((a + 3,))
            out += self.region(r.body, indent + 1)
            self.recon.close_scope(snap)
            out.append(f"{pad}end")
            return out
        if isinstance(r, GenericFor):
            a, c = r.call.ri.a, r.call.ri.c
            vars_ = ", ".join(name_for(a + 3 + i, self.depth) for i in range(c))
            # `for k, v in pairs(t) do` staged ONE expression across the whole
            # control triple, so slots a+1/a+2 come back as `MultiSpill`
            # placeholders and the header prints the single expression (see
            # `Reconstructor._emit_multi`). `for k, v in next, t do` stages
            # three independent expressions and prints all three. A
            # `MultiSpill` reaching any other position is unprintable and
            # refuses in `_expr`.
            #
            # This is the ONE consumer that drops a `MultiSpill` instead of
            # refusing, so it must check the spill is its own: `base` names
            # the producer whose extra values the spill stands for, and only
            # a spill based at `a` was left here by the very `CALL a b 4`
            # this header is printing. A spill based anywhere else in these
            # slots means some other multi-value producer's staging leaked
            # into the control triple, and silently dropping it would print a
            # short header (`for k, v in f() do` where the bytecode had three
            # independent operands) -- exactly the class of silent wrong
            # output `MultiSpill`'s unprintability exists to prevent. Route
            # it to the same refusal by simply not filtering it out: `_expr`
            # raises on it.
            #
            # Defensive rather than a fixed defect (fix round 1, F3): every
            # `MultiSpill` in this codebase is created by `_emit_multi` with
            # `base == regs[0]`, and `_is_generic_for_iterator` only stages
            # one when a `TFORLOOP` sits at that same base, so producing a
            # foreign spill here needs two `TFORLOOP`s based one register
            # apart in the same function. Not observed on the corpus and not
            # constructed. Kept because "drop whatever is in these slots" is
            # the wrong default for a placeholder whose entire contract is
            # that it never prints.
            taken = [self.recon.take_expr(a + i) for i in range(3)]
            iters = ", ".join(self.expr(e, indent=indent) for e in taken
                              if not (isinstance(e, MultiSpill) and e.base == a))
            out = [f"{pad}for {vars_} in {iters} do"]
            # A loop body is its own block, same as an `if` arm. Unlike the
            # `if` case this is defensive rather than a fixed defect: a
            # register whose FIRST write is inside a loop body sits above
            # everything still live after the loop (the body's locals and the
            # header's own slots are all released at `end`), so luac cannot
            # produce a shape where such a register is written again
            # afterwards -- there is no reachable leak to regress against.
            # Kept for symmetry and for non-luac input; see
            # Reconstructor.open_scope.
            snap = self.recon.open_scope()
            self.recon.declare_loop_vars(range(a + 3, a + 3 + c))
            out += self.region(r.body, indent + 1)
            self.recon.close_scope(snap)
            out.append(f"{pad}end")
            return out
        if isinstance(r, WhileTrue):
            # No header expression to render: `while true` has no condition,
            # and the region claims only the closing JMP (`r.closing`), which
            # is the `end` itself and produces no statement. So unlike the
            # `for` arms there is nothing to `take_expr` before opening the
            # body's scope -- the "take before open" ordering those arms need
            # is vacuous here rather than violated.
            out = [f"{pad}while true do"]
            # The body is its own Lua block, exactly like an `if` arm: a
            # `local` it declares is out of scope after the `end`, and unlike
            # the `for` arms this is NOT merely defensive. luac reuses a
            # while-body local's register for a *different* local after the
            # loop (`while true do local x = 1 ... end local y = 2 ...`), so
            # without restoring `declared` the second one prints as a bare
            # `l0_0 = ...` -- a write to a GLOBAL. Measured by inverting this
            # (M4 task 2): the recompile grows a constant and diverges on
            # `code`, so certification refuses and the proto drops to L1. See
            # Reconstructor.open_scope, and
            # tests/test_emit_while.py::test_body_local_register_reused_after_the_loop.
            snap = self.recon.open_scope()
            out += self.region(r.body, indent + 1)
            self.recon.close_scope(snap)
            out.append(f"{pad}end")
            return out
        if isinstance(r, While):
            # The scope opens BEFORE the header is staged, not after: the
            # condition's operand code is part of the loop, it re-runs every
            # iteration, and the temps it stages must not survive the `end`
            # (the same leak `close_scope` exists to stop for body locals --
            # see the WhileTrue arm).
            snap = self.recon.open_scope()
            stmts = self.recon.stmts_for(r.header)
            if stmts:
                # THE guard for this node. `While` claims its header
                # instructions, so if reconstructing them yields statements
                # rather than pure operand staging, printing only `while
                # <cond> do` would DROP those statements silently -- the
                # pc-claim audit would still pass (the pcs are claimed) and
                # the output would be wrong. There is nowhere in a Lua
                # `while` header to put a statement, so this shape is not a
                # `while` at all: refuse, and the chunk falls back.
                #
                # It should be unreachable on luac output: `whilestat` reads
                # the condition with `fs->freereg == fs->nactvar`, so every
                # register the condition writes is above every live local and
                # is classified a temp (staged, never a statement). Kept as a
                # loud refusal rather than an assert because
                # `classify_registers` is a heuristic reconstruction of luac's
                # input, not a proof: since M4 task 13 it answers per
                # DEFINITION rather than per register number, which removed
                # the shape that used to reach this from compiled source
                # (`while a do for i = 1, 10 do f(i) end end`, now `L3`), but
                # its own barriers and the whole-function `declared` set can
                # still grade a header definition local. Pinned by injection:
                # tests/test_sir_loops_longtail.py::
                # test_while_header_that_would_need_a_statement_is_refused_not_dropped.
                raise StructureError(
                    f"pc {r.cond.ri.pc}: while-header code reconstructs to "
                    f"{len(stmts)} statement(s), which a Lua while header "
                    "cannot carry")
            cond = self.condition(r.cond, indent)
            out = [f"{pad}while {cond} do"]
            out += self.region(r.body, indent + 1)
            self.recon.close_scope(snap)
            out.append(f"{pad}end")
            return out
        if isinstance(r, Repeat):
            out = [f"{pad}repeat"]
            snap = self.recon.open_scope()
            out += self.region(r.body, indent + 1)
            # The `until` condition is rendered INSIDE the body's scope and the
            # scope is closed only afterwards. That is not a stylistic choice:
            # `lparser.c`'s `repeatstat` reads the condition inside the scope
            # block (`enterblock(fs, &bl2, 0)` ... `chunk` ... `cond`, with
            # `leaveblock` only after), which is why `repeat local a = f()
            # until a` is legal Lua. Closing first would drop `a` from
            # `declared`/`env` and make the condition reference a global.
            cond = self.condition(r.cond, indent)
            self.recon.close_scope(snap)
            out.append(f"{pad}until {cond}")
            return out
        if isinstance(r, EndIter):
            # A threaded end-of-iteration JMP prints as nothing: its
            # source-level destination was "the end of the loop body", and
            # `sir.build` only claims one in tail position of its range (and
            # only when that range is itself in tail position of the whole
            # loop body -- `_own_enditers <= _tail_enditers`), so falling out
            # of the printed block does exactly what the jump did. That this
            # is faithful is not argued here, it is adjudicated by
            # certification: luac must re-thread the printed source into the
            # identical instruction stream.
            return []
        raise StructureError(f"unprintable region {type(r).__name__}")


def _sole_if(r: Region | None) -> "If | None":
    """The single `If` that `r` consists of, or None.

    `sir.build._structure_range` always returns a `Seq` (line 1079), so an
    else-arm holding one `if` statement arrives wrapped rather than as a bare
    `If`. A `Seq` claims no pcs of its own and prints its children at its own
    indent, so looking through a single-child one changes nothing but the
    spelling.
    """
    while isinstance(r, Seq) and len(r.body) == 1:
        r = r.body[0]
    return r if isinstance(r, If) else None


def _split_else(r: Region | None) -> tuple["If | None", tuple[Region, ...]]:
    """Split an else-arm into `(trailing If, everything before it)`, or
    `(None, ())` if it does not end in an `If` at all.

    An `elseif` candidate is an else-arm whose LAST region is an `If`. It is
    not usually the arm's *only* region: `sir.build` puts the nested
    condition's operand code in a `Straight` sibling ahead of it. Whether that
    sibling is really "nothing" is a reconstruction question, not a structural
    one, so this function does not try to answer it -- the caller renders the
    prefix and collapses only if it printed no lines.

    The one structural refusal here is a prefix region that `_terminates`:
    after an unconditional `return`/`break` the `Seq` arm of `Printer.region`
    stops, so the trailing `If` would never be printed at all, and pulling it
    out to an `elseif` would resurrect unreachable code (which recompiles to
    extra instructions, i.e. costs the proto its certification).

    **That refusal is DEFENSIVE, not proven by a failing test.** Measured
    2026-08-12 by wrapping this function over the whole 229-file corpus: the
    `_terminates` branch fires **0** times against **504** collapses that do
    happen, and deleting it leaves the full suite green. Three synthetic
    shapes were tried to reach it and none did: `if x then f() else if a then
    return 1 else return 2 end if b then g() end end` and its `return`-only
    variant both make the printer refuse the whole chunk for unrelated
    reasons (so nothing is printed at all), and the single-armed `if a then
    return end` variant does not `_terminate` (one arm falls through), so the
    guard is not consulted. Source-level Lua cannot write the shape directly
    either -- `return`/`break` are `laststat`, legal only as the final
    statement of a block. Kept because "print whatever precedes the `if`" is
    the wrong default for a region the recursive form would have suppressed.
    """
    sole = _sole_if(r)
    if sole is not None:
        return sole, ()
    while isinstance(r, Seq) and len(r.body) == 1:
        r = r.body[0]
    if not isinstance(r, Seq) or not r.body:
        return None, ()
    last = _sole_if(r.body[-1])
    if last is None:
        return None, ()
    prefix = r.body[:-1]
    if any(_terminates(p) for p in prefix):
        return None, ()
    return last, prefix


def _implicit_return_pc(fn: LirFunction) -> int | None:
    """The pc of the `RETURN A 1` luac appends to every function body, or
    None if this function's last instruction isn't one.

    `lparser.c`'s `close_func` unconditionally calls `luaK_ret(fs, 0, 0)`,
    so the final instruction of every compiled Lua 5.1 proto is `RETURN 0 1`
    whether or not the source itself ended in a `return`. That instruction
    has NO source-level counterpart -- it is what the compiler *adds*. If
    the printer emits a `return` statement for it, recompiling the printed
    source produces that `return`'s own `RETURN 0 1` *plus* a freshly
    appended one, so a proto whose original tail was a single `RETURN 0 1`
    comes back with two and fails certification on `code` (measured: this
    was the single largest `code`-only mismatch cluster on the corpus).

    Suppressing it is exact rather than heuristic in both directions:
      - Source that did NOT end in `return`: the region tree has exactly one
        trailing `Return`, this one. Suppressed -> nothing printed ->
        recompile re-appends exactly one. Match.
      - Source that DID end in an explicit `return`/`return e`: luac emitted
        that statement's own RETURN *and then* appended this one, so the
        explicit return has its own earlier pc and is printed normally --
        `Printer.region`'s `Seq` branch stops at it (`_terminates`) and
        never reaches this pc at all. Match.
    So this never deletes a source-level `return`: the suppressed pc is by
    construction the one instruction no source statement produced.
    """
    last_pc = max(fn.instrs)
    ri = fn.instrs[last_pc].ri
    return last_pc if (ri.op is Op.RETURN and ri.b == 1) else None


def _terminates(r: Region) -> bool:
    """True iff `r`, once printed, unconditionally ends its enclosing block
    (no statement can legally or meaningfully follow it in the same Seq).

    Needed because luac's compiler always appends an implicit trailing
    `RETURN 0 1` to *every* function body, whether or not the source already
    ended in an explicit `return` -- so a function like `function() return
    n + 1 end` has TWO Return instructions back to back in its bytecode, and
    `_structure_range`'s pc-linear walk (which has no reachability model of
    its own -- see sir/build.py) faithfully gives both their own `Return`
    region in the same `Seq`. Printing both literally is not just dead code,
    it is a Lua 5.1 SYNTAX ERROR: `return` (like `break`) is only legal as
    the last statement of a block (Lua 5.1 grammar: `laststat -> return
    [explist] | break`). `Printer.region`'s `Seq` branch stops emitting
    further siblings once one of them `_terminates`.

    An `If` only terminates when it has an else and BOTH branches terminate
    (otherwise the false path can still fall through). A `NumericFor`/
    `GenericFor` never counts as terminating here: a loop's own natural
    "iteration finished" exit always falls through to whatever follows it,
    independent of what any single iteration's body does.

    The M4 loop nodes fall through to the default `False` for the same reason,
    deliberately: a `WhileTrue`/`Repeat` may be followed by ordinary
    statements (luac happily compiles code after an unconditionally-infinite
    loop, and printing it is legal Lua that recompiles the same), and an
    `EndIter` prints nothing and is only ever claimed in tail position of its
    range, so it has no siblings for a `True` here to suppress.
    """
    if isinstance(r, (Return, Break)):
        return True
    if isinstance(r, Seq):
        return bool(r.body) and _terminates(r.body[-1])
    if isinstance(r, If):
        return r.else_body is not None and _terminates(r.then_body) and _terminates(r.else_body)
    return False


def print_region(region: Region, printer: Printer, indent: int = 0) -> list[str]:
    """Thin wrapper around `Printer.region`. Needs a full `Printer` (not a
    bare `Reconstructor`, per module docstring "Brief defects" #4) because a
    statement inside the region tree may print a nested closure, which needs
    this function's own Proto/LIR/upvalue-name context.
    """
    return printer.region(region, indent)


def print_function(fn: LirFunction, region: Region, rc: RegClass, depth: int,
                   upval_names: tuple[str, ...] = (), path: str = "main",
                   fallback_paths: frozenset[str] = frozenset(),
                   indent: int = 0) -> str:
    """Print one function's body (its SIR region tree + register
    classification) as Lua source -- no enclosing `function(...) ... end`;
    the caller (chunk assembly for the top level, `Printer.closure_parts` for
    a nested CLOSURE) adds that.
    """
    printer = Printer(fn, rc, depth, upval_names, path, fallback_paths)
    lines = printer.region(region, indent)
    return "\n".join(lines) + ("\n" if lines else "")


def _print_proto_body(proto: Proto, depth: int, upval_names: tuple[str, ...],
                      path: str = "main",
                      fallback_paths: frozenset[str] = frozenset(),
                      indent: int = 0) -> str:
    fn = lift_proto(proto)
    region = build_sir(fn)
    rc = classify_registers(fn)
    return print_function(fn, region, rc, depth, upval_names, path,
                          fallback_paths, indent)


def print_chunk_or_raise(proto: Proto) -> str:
    """`print_chunk`, but letting the refusal propagate instead of turning it
    into `None`.

    Both forms exist because two callers want different things out of the same
    computation. `print_chunk`'s `None` says *that* the tree was refused;
    `structure.structured.certify_proto` needs to know *why*, because the
    refusal message becomes the non-`L3` ledger row's `refusal_reason` (M4
    task 6). A `None` cannot carry that message, and re-deriving it by calling
    the printer a second time inside an `except` would be both wasteful and a
    lie waiting to happen if the two calls ever disagreed.
    """
    return _print_proto_body(proto, depth=0, upval_names=())


def print_chunk(proto: Proto) -> str | None:
    """Structurally print an entire proto tree (this proto and, inline at
    their CLOSURE sites, every descendant) as a compilable Lua chunk.

    Returns None if any part of the tree -- this proto or any descendant --
    cannot be structured (`StructureError`) or reconstructed
    (`ReconstructError`); the caller (Task 7) falls back to the whole-chunk
    fallback emitter in that case. Anything else propagates: it is a bug in
    this printer or an upstream layer, not a legitimate refusal.
    """
    try:
        return print_chunk_or_raise(proto)
    except (StructureError, ReconstructError):
        return None

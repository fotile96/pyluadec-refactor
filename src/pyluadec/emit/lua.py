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
                                   TableExpr, UnExpr, UpvalExpr, VarargExpr)
from pyluadec.express.names import RegClass, classify_registers, name_for
from pyluadec.express.reconstruct import (Assign, AssignTarget, ExprStmt,
                                          GlobalTarget, IndexTarget,
                                          LocalDecl, LocalTarget,
                                          Reconstructor, ReconstructError,
                                          ReturnStmt, Stmt, UpvalTarget)
from pyluadec.ingest.proto import Proto
from pyluadec.lift import LUA_KEYWORDS, Op
from pyluadec.lift.lift import LirFunction, lift_proto
from pyluadec.sir import (Break, GenericFor, If, NumericFor, Region, Return,
                          Seq, Straight)
from pyluadec.sir.build import StructureError, build_sir
from pyluadec.structure.fallback import const_lit

# Lua 5.1 operator precedence (higher binds tighter; Lua reference manual
# §2.5.6). Used to add the minimal necessary parentheses when printing
# BinExpr/UnExpr -- over-parenthesising is always safe, under-parenthesising
# changes meaning.
_PREC = {"or": 1, "and": 2,
         "<": 3, ">": 3, "<=": 3, ">=": 3, "~=": 3, "==": 3,
         "..": 4, "+": 5, "-": 5, "*": 6, "/": 6, "%": 6,
         "unary": 7, "^": 8}
_RIGHT_ASSOC = frozenset({"..", "^"})
# Precedence demanded of the base of a call/index/method-call position
# (`X(...)`, `X[...]`, `X:m(...)`) -- higher than any real operator's own
# precedence, so any Bin/UnExpr used there always gets wrapped: `(a+b)()`,
# never `a+b()` (which would parse as `a + (b())`).
_PRIMARY_PREC = _PREC["^"] + 1


def _ident(name: bytes) -> str:
    """Validate+decode a constant byte-string as an emittable Lua identifier.

    No regex (forbidden in this package -- see module docstring): Python's
    `str.isidentifier()` covers the same character class as Lua's
    `[A-Za-z_][A-Za-z0-9_]*` once the string is known to be pure ASCII.
    """
    try:
        s = name.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ReconstructError(f"identifier {name!r} is not ASCII") from exc
    if not s.isidentifier() or s in LUA_KEYWORDS:
        raise ReconstructError(f"identifier {name!r} not emittable as a Lua name")
    return s


def _expr(e: Expr, depth: int, parent_prec: int, ctx: "Printer | None") -> str:
    """The real expression-printing dispatch, shared by the context-free
    `print_expr` (ctx=None; usable on any tree with no ClosureExpr/UpvalExpr)
    and `Printer.expr` (ctx=the enclosing function's Printer, needed to name
    upvalues and to print nested closures' bodies).
    """
    if isinstance(e, ConstExpr):
        return const_lit(e.value)
    if isinstance(e, LocalExpr):
        return name_for(e.reg, depth)
    if isinstance(e, GlobalExpr):
        return _ident(e.name)
    if isinstance(e, UpvalExpr):
        if ctx is None:
            raise ReconstructError("UpvalExpr needs Printer context; use print_function")
        return ctx.upval_name(e.idx)
    if isinstance(e, VarargExpr):
        return "..."
    if isinstance(e, ClosureExpr):
        if ctx is None:
            raise ReconstructError("ClosureExpr needs Printer context; use print_function")
        params, body = ctx.closure_parts(e)
        return f"function({params})\n{body}end"
    if isinstance(e, IndexExpr):
        return f"{_expr(e.table, depth, _PRIMARY_PREC, ctx)}[{_expr(e.key, depth, 0, ctx)}]"
    if isinstance(e, TableExpr):
        items = [_expr(x, depth, 0, ctx) for x in e.array]
        items += [f"[{_expr(k, depth, 0, ctx)}] = {_expr(v, depth, 0, ctx)}"
                 for k, v in e.hash]
        return "{" + ", ".join(items) + "}"
    if isinstance(e, CallExpr):
        args = ", ".join(_expr(a, depth, 0, ctx) for a in e.args)
        fn_txt = _expr(e.fn, depth, _PRIMARY_PREC, ctx)
        if e.is_method:
            assert e.method is not None
            return f"{fn_txt}:{_ident(e.method)}({args})"
        return f"{fn_txt}({args})"
    if isinstance(e, UnExpr):
        prec = _PREC["unary"]
        inner = _expr(e.operand, depth, prec, ctx)
        # "-" always gets a trailing space: without it, a nested unary minus
        # (`- -x`, reconstructed from two UNM instructions) would print as
        # "--x", which Lua's lexer reads as a comment, silently deleting the
        # rest of the line. BinExpr already separates its operator with
        # spaces on both sides, so this is only strictly required here, but
        # applying it unconditionally is simpler than special-casing the one
        # dangerous adjacency.
        sep = " " if e.op in ("not", "-") else ""
        out = f"{e.op}{sep}{inner}"
        return f"({out})" if prec < parent_prec else out
    if isinstance(e, BinExpr):
        prec = _PREC[e.op]
        lp = prec + (1 if e.op in _RIGHT_ASSOC else 0)
        rp = prec + (0 if e.op in _RIGHT_ASSOC else 1)
        out = f"{_expr(e.lhs, depth, lp, ctx)} {e.op} {_expr(e.rhs, depth, rp, ctx)}"
        return f"({out})" if prec < parent_prec else out
    raise ReconstructError(f"unprintable expression {type(e).__name__}")


def print_expr(e: Expr, depth: int, parent_prec: int = 0) -> str:
    """Print an expression tree that contains no ClosureExpr/UpvalExpr node.

    Convenience entry point (precedence/formatting can be tested without
    building a whole function's Printer context). ClosureExpr/UpvalExpr need
    to know their enclosing function's proto/fn/upval_names, which only a
    `Printer` (see `print_function`) carries.
    """
    return _expr(e, depth, parent_prec, None)


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
                upval_names: tuple[str, ...] = ()):
        self.fn = fn
        self.proto = fn.proto
        self.rc = rc
        self.depth = depth
        self.upval_names = upval_names
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

    # ---- expressions --------------------------------------------------
    def expr(self, e: Expr, parent_prec: int = 0) -> str:
        return _expr(e, self.depth, parent_prec, self)

    def upval_name(self, idx: int) -> str:
        if not (0 <= idx < len(self.upval_names)):
            raise ReconstructError(f"upvalue index {idx} has no name (nups mismatch)")
        return self.upval_names[idx]

    def _closure_pc(self, idx: int) -> int:
        pc = self._closure_pc_by_idx.get(idx)
        if pc is None:
            raise ReconstructError(f"no CLOSURE instruction found for subproto index {idx}")
        return pc

    def closure_parts(self, e: ClosureExpr) -> tuple[str, str]:
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
        params = ", ".join(name_for(i, self.depth + 1) for i in range(child.numparams))
        if child.is_vararg & 2:
            params = params + (", ..." if params else "...")
        body = _print_proto_body(child, self.depth + 1, tuple(names))
        return params, body

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
    def target(self, t: AssignTarget) -> str:
        if isinstance(t, LocalTarget):
            return name_for(t.reg, self.depth)
        if isinstance(t, GlobalTarget):
            return _ident(t.name)
        if isinstance(t, IndexTarget):
            return f"{self.expr(t.table, _PRIMARY_PREC)}[{self.expr(t.key)}]"
        if isinstance(t, UpvalTarget):
            return self.upval_name(t.idx)
        raise ReconstructError(f"unprintable target {type(t).__name__}")

    def stmt(self, s: Stmt) -> str:
        if isinstance(s, LocalDecl):
            return self._local_decl(s)
        if isinstance(s, Assign):
            tgts = ", ".join(self.target(t) for t in s.targets)
            vals = ", ".join(self.expr(e) for e in s.exprs)
            return f"{tgts} = {vals}"
        if isinstance(s, ExprStmt):
            return self.expr(s.call)
        if isinstance(s, ReturnStmt):
            if not s.exprs:
                return "return"
            return "return " + ", ".join(self.expr(e) for e in s.exprs)
        raise ReconstructError(f"unprintable statement {type(s).__name__}")

    def _local_decl(self, s: LocalDecl) -> str:
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
            params, body = self.closure_parts(s.exprs[0])
            return f"local function {names}({params})\n{body}end"
        vals = ", ".join(self.expr(e) for e in s.exprs)
        return f"local {names} = {vals}"

    def condition(self, r: If) -> str:
        """Render an If's comparison instruction as a boolean expression that
        is true exactly when the region tree's `then_body` should run.

        Polarity (empirically measured against real `luac_sz4` output and
        lvm.c's dojump mechanics -- see module docstring "Brief defects" #1):
        for EQ/LT/LE, `then_body` is the fallthrough after the JMP, which
        lvm.c takes exactly when the comparison result is UNEQUAL to A; so
        A==0 means `then` is the un-negated comparison, A==1 means `then` is
        its negation. For TEST A C, `then_body` runs when
        `l_isfalse(R(A)) == C`; so C==0 means `then` is R(A) itself
        (truthy-tested), C==1 means `then` is `not R(A)`.
        """
        ri = r.cond.ri
        op = ri.op
        if op in (Op.EQ, Op.LT, Op.LE):
            sym = {Op.EQ: "==", Op.LT: "<", Op.LE: "<="}[op]
            lhs = self.expr(self.recon.cond_operand(ri.b))
            rhs = self.expr(self.recon.cond_operand(ri.c))
            base = f"{lhs} {sym} {rhs}"
            return base if ri.a == 0 else f"not ({base})"
        if op is Op.TEST:
            operand = self.recon.cond_operand(ri.a)
            if ri.c == 0:
                return self.expr(operand)
            # Delegate to UnExpr's own precedence-correct printing rather
            # than hand-formatting "not {text}" here: the brief's skeleton
            # did the latter, which is wrong whenever `operand` itself binds
            # looser than unary `not` (e.g. `if not (a + b) then` would
            # print as "not a + b", reparsing as "(not a) + b"; see module
            # docstring "Brief defects" #2).
            return self.expr(UnExpr("not", operand))
        raise StructureError(f"unprintable condition {op.name}")

    # ---- regions --------------------------------------------------------
    def region(self, r: Region, indent: int) -> list[str]:
        pad = "  " * indent
        if isinstance(r, Straight):
            return [pad + self.stmt(s) for s in self.recon.stmts_for(r.instrs)]
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
            return [pad + self.stmt(s) for s in self.recon.stmts_for((r.instr,))]
        if isinstance(r, Break):
            return [pad + "break"]
        if isinstance(r, If):
            cond = self.condition(r)
            out = [f"{pad}if {cond} then"]
            out += self.region(r.then_body, indent + 1)
            if r.else_body is not None:
                out.append(f"{pad}else")
                out += self.region(r.else_body, indent + 1)
            out.append(f"{pad}end")
            return out
        if isinstance(r, NumericFor):
            a = r.prep.ri.a
            var = name_for(a + 3, self.depth)
            init = self.expr(self.recon.take_expr(a))
            limit = self.expr(self.recon.take_expr(a + 1))
            step = self.expr(self.recon.take_expr(a + 2))
            out = [f"{pad}for {var} = {init}, {limit}, {step} do"]
            out += self.region(r.body, indent + 1)
            out.append(f"{pad}end")
            return out
        if isinstance(r, GenericFor):
            a, c = r.call.ri.a, r.call.ri.c
            vars_ = ", ".join(name_for(a + 3 + i, self.depth) for i in range(c))
            iters = ", ".join(self.expr(self.recon.take_expr(a + i)) for i in range(3))
            out = [f"{pad}for {vars_} in {iters} do"]
            out += self.region(r.body, indent + 1)
            out.append(f"{pad}end")
            return out
        raise StructureError(f"unprintable region {type(r).__name__}")


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
                   upval_names: tuple[str, ...] = ()) -> str:
    """Print one function's body (its SIR region tree + register
    classification) as Lua source -- no enclosing `function(...) ... end`;
    the caller (chunk assembly for the top level, `Printer.closure_parts` for
    a nested CLOSURE) adds that.
    """
    printer = Printer(fn, rc, depth, upval_names)
    lines = printer.region(region, 0)
    return "\n".join(lines) + ("\n" if lines else "")


def _print_proto_body(proto: Proto, depth: int, upval_names: tuple[str, ...]) -> str:
    fn = lift_proto(proto)
    region = build_sir(fn)
    rc = classify_registers(fn)
    return print_function(fn, region, rc, depth, upval_names)


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
        return _print_proto_body(proto, depth=0, upval_names=())
    except (StructureError, ReconstructError):
        return None

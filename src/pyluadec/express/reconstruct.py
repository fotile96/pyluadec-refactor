"""LIR straight-run -> statement/expression IR with effect-gated temp inlining (spec §4).

No text anywhere: every leaf here is a frozen dataclass. Task 6 (the printer)
walks this tree structurally; there is no string formatting, no regex, and no
re-parsing of anything this module produces (see tests/test_engineering_practice.py
for the guard that enforces the "no regex in this package" half of that rule).

Design: a single `Reconstructor` instance owns a `reg -> Expr` environment
(`self.env`) and a `declared` set that both survive across separate
`stmts_for()` calls -- the SIR region tree walks Straight/If/For regions in
program order sharing one Reconstructor, so a temp staged in one region (e.g.
a `for` loop's init/limit/step, computed in the region immediately before the
loop) is still in `self.env` when the loop header (built by Task 6/7) calls
`take_expr` on it.

Reading a *temp* register pops its staged definition out of the environment.
Single-use is what `express.names._stack_discipline` proves before a register
is ever classified `temp`: it simulates `lparser.c`'s `freereg = nactvar`
allocation discipline and disqualifies any register with a definition that is
read zero times or more than once (see that module's docstring -- this used to
cite `_adjacent_pure`, the effect-based barrier the freereg simulation replaced
in M3 task 8). Reading a *local* register never pops; it always yields a fresh
`LocalExpr(reg)` reference, which is safe to embed more than once (printing a
variable name twice has no evaluation-order consequence, unlike printing a
pending expression tree twice).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from pyluadec.ingest.proto import LuaNumber
from pyluadec.lift.lift import LirFunction, LirInstr
from pyluadec.lift.opcodes import Op, indexk, isk

from .expr import (BinExpr, CallExpr, ClosureExpr, ConstExpr, Expr, GlobalExpr,
                   IndexExpr, LocalExpr, TableExpr, UnExpr, UpvalExpr, VarargExpr)
from .names import RegClass


# ---- statement IR -----------------------------------------------------
@dataclass(frozen=True)
class LocalTarget:
    reg: int


@dataclass(frozen=True)
class GlobalTarget:
    name: bytes


@dataclass(frozen=True)
class IndexTarget:
    table: Expr
    key: Expr


@dataclass(frozen=True)
class UpvalTarget:
    idx: int


AssignTarget = LocalTarget | GlobalTarget | IndexTarget | UpvalTarget


@dataclass(frozen=True)
class LocalDecl:
    regs: tuple[int, ...]
    exprs: tuple[Expr, ...]


@dataclass(frozen=True)
class Assign:
    targets: tuple[AssignTarget, ...]
    exprs: tuple[Expr, ...]


@dataclass(frozen=True)
class ExprStmt:
    call: CallExpr


@dataclass(frozen=True)
class ReturnStmt:
    exprs: tuple[Expr, ...]
    is_vararg_tail: bool


Stmt = LocalDecl | Assign | ExprStmt | ReturnStmt


class ReconstructError(Exception):
    pass


_ARITH = {Op.ADD: "+", Op.SUB: "-", Op.MUL: "*", Op.DIV: "/", Op.MOD: "%", Op.POW: "^"}


def _local_regs_in(e: Expr) -> frozenset[int]:
    """Every register a LocalExpr anywhere inside `e` refers to.

    Used by the table-constructor folder to know which *other* registers a
    deferred table's already-folded array/hash items depend on (see
    `_dispatch`'s hazard check below) -- an item captured as `LocalExpr(reg)`
    is a live reference, not a value snapshot, so if `reg` gets reassigned
    before the table's own register is finally touched (which is when
    `_close_table_ctx` actually emits the `local ... = {...}` statement),
    the deferred TableExpr would silently pick up the *new* value instead of
    the one that was live when the array item was folded.
    """
    if isinstance(e, LocalExpr):
        return frozenset({e.reg})
    if isinstance(e, IndexExpr):
        return _local_regs_in(e.table) | _local_regs_in(e.key)
    if isinstance(e, BinExpr):
        return _local_regs_in(e.lhs) | _local_regs_in(e.rhs)
    if isinstance(e, UnExpr):
        return _local_regs_in(e.operand)
    if isinstance(e, CallExpr):
        regs = _local_regs_in(e.fn)
        for arg in e.args:
            regs |= _local_regs_in(arg)
        return regs
    if isinstance(e, TableExpr):
        regs = frozenset()
        for item in e.array:
            regs |= _local_regs_in(item)
        for k, v in e.hash:
            regs |= _local_regs_in(k) | _local_regs_in(v)
        return regs
    # ConstExpr / GlobalExpr / UpvalExpr / VarargExpr / ClosureExpr: no
    # LocalExpr reachable from any of these node types' own fields.
    # (ClosureExpr's captures live in fn.closure_pseudo, not in the Expr
    # tree itself, and are out of scope for this hazard check -- a closure
    # literal folded directly as a table array/hash item whose captured
    # register is later reassigned before the table closes is a known,
    # narrower residual risk, not fixed here.)
    return frozenset()


def _int_const(i: int) -> LuaNumber:
    """A LuaNumber constant carrying the raw 8-byte double payload for integer
    i -- used for the synthetic array indices the standalone-SETLIST degrade
    path emits (see Reconstructor._standalone_setlist). Never derived from
    bytecode, but must still carry a bit-exact payload like every other
    numeric constant in this project (see CLAUDE.md global constraints).
    """
    return LuaNumber(value=float(i), payload=struct.pack("<d", float(i)))


class Reconstructor:
    """Shared-environment LIR -> Stmt/Expr reconstructor.

    One instance is created per function and walked across that function's
    entire SIR region tree in program order (Straight/If/For regions all
    call back into the same instance's `stmts_for`/`take_expr`/`cond_operand`).
    `env`/`declared` and the smaller pieces of cross-instruction state below
    (`_open`, `_self_pending`, `_table_ctx`) persist across those calls.
    """

    def __init__(self, fn: LirFunction, rc: RegClass, depth: int,
                 upval_names: tuple[str, ...] = ()):
        self.fn = fn
        self.proto = fn.proto
        self.rc = rc
        self.depth = depth
        self.upval_names = upval_names
        self.env: dict[int, Expr] = {}
        # rc.temps is trusted directly: express.names.classify_registers now
        # applies its own staging-window check before its `controls` override
        # (FORPREP/FORLOOP/TFORLOOP force a register temp by register number)
        # is allowed to win, so a register that's a control slot for one
        # loop's range *and* an ordinary, multiply-written/read local
        # elsewhere in the same function is already classified local by the
        # time it reaches this Reconstructor (M3 task-5 round-2 review; a
        # round-1 defensive census duplicating that check used to live here
        # instead -- moved into names.py so RegClass.temps means what its
        # docstring says for every reader, not just this module).
        # loop_vars are declared by the `for` statement itself (Task 6/7's
        # NumericFor/GenericFor printer), never by this module -- pre-seed
        # them into `declared` so that if the loop body ever writes back to
        # the loop variable (legal Lua: `for i=1,3 do i=i+10 ... end`
        # reassigns i without affecting iteration), write_reg emits an
        # Assign, never a second LocalDecl.
        # Parameters are already in scope, and already named, when the body
        # starts -- `numparams` registers at the bottom of the frame. Without
        # seeding them, the first write to a parameter's register goes through
        # force_materialize's LocalDecl branch and emits `local l1_0 = ...`,
        # which SHADOWS the parameter with a brand-new variable instead of
        # assigning to it. That is not merely ugly: it costs a stack slot and
        # a `local` the original never had, so the recompiled proto's
        # maxstacksize (and often its code) diverge. Measured on the corpus,
        # `function(s) s = string.gsub(s, ...) ... end` -- a very common shape
        # here -- printed a spurious `local l1_0 = ...` on its first line
        # before this seeding (M3 task 8).
        self.declared: set[int] = set(rc.loop_vars) | set(range(fn.proto.numparams))
        # (base_reg, expr) for a not-yet-consumed open-result producer
        # (CALL C==0 or VARARG B==0): the instruction that will read the
        # open range [base_reg, dynamic top) consumes this via _consume_open.
        self._open: tuple[int, Expr] | None = None
        # (fn_reg, self_reg, obj_expr, method_name) staged by a SELF whose
        # matching CALL/TAILCALL (same `a`) hasn't been seen yet.
        self._self_pending: tuple[int, int, Expr, bytes] | None = None
        # Stack of {"reg": int, "array": list[Expr], "hash": list[tuple[Expr,
        # Expr]]} for NEWTABLE-started constructors still accepting
        # SETLIST/SETTABLE. A stack, not a single slot, so a table literal
        # nested as another's *value* (`{a=1, b={2,3}, c=4}`) pushes its own
        # context instead of forcing the outer one closed -- only a genuine
        # register conflict (the new NEWTABLE reuses the top context's own
        # register) closes anything (see _dispatch).
        self._table_ctx_stack: list[dict] = []
        self._out: list[Stmt] = []

    # ---- public API (spec) --------------------------------------------
    def stmts_for(self, instrs: tuple[LirInstr, ...]) -> tuple[Stmt, ...]:
        self._out = []
        for li in instrs:
            self._dispatch(li)
        self._finalize_pending()
        return tuple(self._out)

    def open_scope(self) -> tuple[frozenset[int], dict[int, Expr]]:
        """Snapshot the declaration/staging state before walking a nested Lua
        block (an `if` arm, a loop body).

        `declared` and `env` are deliberately shared across the whole SIR walk
        (see the class docstring), but Lua block scoping is not: a `local`
        emitted inside one `if` arm is out of scope in the sibling arm and
        after the `end`. Without a snapshot, the FIRST arm to write register
        R emits `local lD_R = ...` and adds R to `declared`, and then the
        second arm's write to the same register goes through
        `force_materialize`'s Assign branch and prints a bare `lD_R = ...`.
        At that point `lD_R` is not in scope, so Lua parses it as a **write
        to a global** -- a silent semantic change (SETGLOBAL where the
        original had a register write). L3 certification has always refused
        that output, so it never shipped, but it cost every affected proto
        its certification and it would have been a real defect in any
        consumer that trusted the printer without the gate.

        `env` is restored alongside `declared` because the two are coupled:
        `force_materialize` writes `env[reg] = LocalExpr(reg)` when it
        declares, and rolling back one without the other would leave a
        placeholder `LocalExpr` for a name that is no longer in scope.
        """
        return frozenset(self.declared), dict(self.env)

    def close_scope(self, snap: tuple[frozenset[int], dict[int, Expr]]) -> None:
        self.declared = set(snap[0])
        self.env = dict(snap[1])

    def take_expr(self, reg: int) -> Expr:
        """Pop a control slot's staged definition (NumericFor init/limit/step,
        GenericFor's iterator triple). Raises if nothing is staged there --
        guessing a default would silently fabricate semantics.
        """
        if reg not in self.env:
            raise ReconstructError(f"register {reg} has no staged expression to take")
        return self.env.pop(reg)

    def cond_operand(self, x: int) -> Expr:
        """If-condition RK operand: K bit set -> ConstExpr; temp register ->
        popped and inlined; local register -> LocalExpr (not popped).
        """
        return self.rk(x)

    # ---- operand helpers -------------------------------------------------
    def rk(self, x: int) -> Expr:
        if isk(x):
            return ConstExpr(self.proto.constants[indexk(x)])
        return self._read_reg(x)

    def _read_reg(self, reg: int) -> Expr:
        # `declared` wins over rc's static classification: once a register has
        # been force-materialized (a real `local`/reassignment statement was
        # emitted for it -- see force_materialize), it is a stable, reread-many
        # -times reference forever after, regardless of what rc.temps says.
        # This matters for the few opcodes (SELF, the SETLIST degrade path)
        # that deliberately force-materialize a register rc.temps still calls
        # temp, so it can be safely referenced more than once.
        if reg in self.declared:
            return self.env.get(reg, LocalExpr(reg))
        if reg in self.rc.temps:
            if reg not in self.env:
                raise ReconstructError(f"temp register {reg} read before it was staged")
            return self.env.pop(reg)
        return self.env.get(reg, LocalExpr(reg))

    def _stable_ref(self, reg: int) -> Expr:
        """A reference to `reg`'s current value that is safe to embed more
        than once. If `reg` is still a pending (unpopped) temp, force it to
        materialize as a real local first -- see the standalone-SETLIST
        degrade path, the one place this reconstructor needs to reference a
        register's value from more than one emitted statement.

        The `reg not in self.declared` guard matters: once a register is
        declared, self.env[reg] already holds the placeholder LocalExpr(reg)
        (not a raw pending expression), so without this guard a
        declared-but-still-rc.temps register would
        force_materialize(reg, LocalExpr(reg)) -- emitting a do-nothing
        `vN = vN` self-reassignment statement.
        """
        if reg not in self.declared and reg in self.rc.temps and reg in self.env:
            self.force_materialize(reg, self.env.pop(reg))
        return LocalExpr(reg)

    def write_reg(self, reg: int, e: Expr) -> None:
        # Symmetric with _read_reg: a register already `declared` is a stable
        # local from here on -- a fresh write to it is a reassignment
        # (force_materialize's Assign branch), never a re-inlinable temp
        # binding, regardless of rc.temps.
        if reg not in self.declared and reg in self.rc.temps:
            self.env[reg] = e
        else:
            self.force_materialize(reg, e)

    def force_materialize(self, reg: int, e: Expr) -> None:
        """Emit reg's value as a real statement (LocalDecl the first time,
        Assign on every subsequent write) regardless of rc's classification.
        Used both for genuinely-local registers and for the few opcodes
        (SELF, the SETLIST degrade path) where a value must be safely
        re-referenceable more than once -- inlining a pending temp expr into
        two tree positions would print (and re-evaluate) it twice.
        """
        if reg in self.declared:
            self._out.append(Assign((LocalTarget(reg),), (e,)))
        else:
            self._out.append(LocalDecl((reg,), (e,)))
            self.declared.add(reg)
        self.env[reg] = LocalExpr(reg)

    def _emit_assign(self, targets: tuple[AssignTarget, ...], exprs: tuple[Expr, ...]) -> None:
        self._out.append(Assign(targets, exprs))

    def _emit_multi(self, regs: tuple[int, ...], expr: Expr) -> None:
        """Multi-register write from a single source expression (CALL with
        >=2 fixed results, VARARG with >=2 fixed targets). A single Expr
        cannot be split into independently-inlineable per-register pieces
        (no such Expr node exists), so every register in `regs` is always
        materialized -- never treated as a poppable temp, even if rc says
        one individually would qualify. Correct, per the brief's stated
        fallback: "otherwise degrades to a plain Assign, still correct, just
        less pretty."
        """
        if len(regs) == 1:
            self.write_reg(regs[0], expr)
            return
        flags = [r in self.declared for r in regs]
        if all(flags):
            self._out.append(Assign(tuple(LocalTarget(r) for r in regs), (expr,)))
        elif not any(flags):
            self._out.append(LocalDecl(regs, (expr,)))
            self.declared.update(regs)
        else:
            # Mixed: some targets already exist as locals, some are fresh.
            # `local a, b, c = f()` would *shadow* the ones that exist rather
            # than assign to them (a second `local` of the same name is a new
            # variable in Lua), so split it in two: bring the fresh registers
            # into scope uninitialised, then assign the whole tuple at once.
            #   local <fresh...>
            #   <all regs...> = f()
            # A LocalDecl with an empty `exprs` is `local a, b` with no
            # initialiser -- the same "fewer exprs than regs" shape this
            # method already emits for the all-fresh case, taken to zero.
            #
            # Reached when a generic-for's TFORLOOP triple is partially
            # demoted: the staging `CALL a b 4` writes all three control
            # slots at once, and classify_registers can legitimately call the
            # base a reused local (round-4 review) while a+1/a+2 stay temp.
            # This used to raise, which turned a round-3 silent statement
            # deletion into a hard refusal for the whole function (M3 task-5
            # round-5 review).
            fresh = tuple(r for r in regs if r not in self.declared)
            self._out.append(LocalDecl(fresh, ()))
            self.declared.update(fresh)
            self._out.append(Assign(tuple(LocalTarget(r) for r in regs), (expr,)))
        for r in regs:
            self.env[r] = LocalExpr(r)

    def _consume_open(self, start: int) -> tuple[Expr, ...]:
        """Build the expression tuple for an open range [start, dynamic top):
        any fixed registers between `start` and the staged open producer's
        base are read normally, then the open producer's own (multi-value)
        expression is appended as the final element -- exactly how a
        CallExpr/VarargExpr in the last position of a Lua expression list
        already means "expand all values" at the source level.
        """
        if self._open is None:
            raise ReconstructError(
                f"open register range starting at {start} has no staged producer")
        base, expr = self._open
        if base < start:
            raise ReconstructError(
                f"open producer at base {base} precedes open range start {start}")
        fixed = tuple(self._read_reg(r) for r in range(start, base))
        self._open = None
        return fixed + (expr,)

    # ---- table constructor folding ----------------------------------------
    def _close_table_ctx(self) -> None:
        """Pop and finalize the innermost pending table constructor.

        Goes through write_reg -- not a blanket force_materialize -- so a
        genuinely single-use table register (per rc.temps) still gets to
        pop-once-inline as a real nested TableExpr (e.g. `{a=1, b={}, c=2}`'s
        inner `{}` folding straight into the outer table's hash value)
        rather than being needlessly declared as its own separate local. A
        table register rc.temps doesn't (or no longer, once declared) trust
        as single-use -- the "table register that will be re-read across
        statements needs a materialized, re-readable reference, not a
        pop-once temp binding" case _standalone_setlist handles via
        _stable_ref -- still gets a real LocalDecl/Assign here, because
        write_reg defers to force_materialize whenever the register isn't a
        trustworthy rc.temps member.
        """
        if not self._table_ctx_stack:
            return
        ctx = self._table_ctx_stack.pop()
        table = TableExpr(array=tuple(ctx["array"]), hash=tuple(ctx["hash"]))
        self.write_reg(ctx["reg"], table)

    def _setlist_batch_offset(self, li: LirInstr) -> int:
        """The 1-based starting array index this SETLIST's b elements land
        at. Only batch 1 (the common case: a table literal with <=50 array
        elements, one SETLIST) is supported -- a second/later batch (C==2+,
        LFIELDS_PER_FLUSH boundary at 50 elements) would need each element's
        Lua-side index offset by (C-1)*50 (see fallback.py's `base` calc),
        which this reconstructor does not compute. Refusing is correct and
        cheap; silently writing 1..b instead of 51..50+b would overwrite the
        first batch outright. Unreachable on the current 229-file corpus
        (all 92 SETLIST instructions have C==1) but a >50-element array
        literal would hit this, and guessing would be wrong, not just ugly.
        """
        ri = li.ri
        eff_c = ri.c if ri.c != 0 else self.proto.code[li.consumed[0] - 1]
        if eff_c != 1:
            raise ReconstructError(
                f"pc {ri.pc}: SETLIST batch C={eff_c} (only the first "
                "LFIELDS_PER_FLUSH batch, C==1, is reconstructed)")
        return 1

    def _fold_setlist(self, li: LirInstr) -> None:
        self._setlist_batch_offset(li)
        ri = li.ri
        a, b = ri.a, ri.b
        ctx = self._table_ctx_stack[-1]
        if b == 0:
            items = self._consume_open(a + 1)
        else:
            items = tuple(self._read_reg(a + i) for i in range(1, b + 1))
        ctx["array"].extend(items)
        for item in items:
            ctx["hazard"] |= _local_regs_in(item)

    def _fold_settable(self, ri) -> None:
        key = ConstExpr(self.proto.constants[indexk(ri.b)])
        val = self.rk(ri.c)
        ctx = self._table_ctx_stack[-1]
        ctx["hash"].append((key, val))
        ctx["hazard"] |= _local_regs_in(val)

    def _standalone_setlist(self, li: LirInstr) -> None:
        """SETLIST with no active matching table-ctx (NEWTABLE and its
        SETLIST were not adjacent -- an intervening effectful instruction
        broke the fold, see _dispatch). Degrades to individual index
        assignments: correct, not pretty, per the brief's stated fallback.
        """
        self._setlist_batch_offset(li)
        ri = li.ri
        a, b = ri.a, ri.b
        table = self._stable_ref(a)
        if b == 0:
            elems = self._consume_open(a + 1)
        else:
            elems = tuple(self._read_reg(a + i) for i in range(1, b + 1))
        for i, e in enumerate(elems, start=1):
            self._emit_assign((IndexTarget(table, ConstExpr(_int_const(i))),), (e,))

    # ---- SELF / method-call fusion ----------------------------------------
    def _self(self, a: int, b: int, c: int) -> None:
        if self._self_pending is not None:
            # A prior SELF's matching CALL/TAILCALL was never seen before
            # this one arrived -- silently overwriting it would drop the
            # earlier receiver's materialization on the floor. Not expected
            # from real luac output (SELF is always immediately followed by
            # its own CALL), so surface it rather than guess.
            raise ReconstructError(
                f"SELF at register {a} arrived while an earlier SELF's "
                f"receiver (registers {self._self_pending[0]}/"
                f"{self._self_pending[1]}) is still unconsumed")
        obj = self._read_reg(b)
        if isk(c) and isinstance(self.proto.constants[indexk(c)], bytes):
            name = self.proto.constants[indexk(c)]
            self._self_pending = (a, a + 1, obj, name)
        else:
            # Dynamic (register) method key: cannot use `:` sugar -- fall
            # back to plain indexing, but still avoid embedding `obj` twice
            # by materializing the receiver once and referencing it by its
            # now-declared register (LocalExpr), never the raw `obj` tree
            # again -- re-embedding `obj` itself here would print (and
            # re-evaluate) it a second time if it were an effectful
            # expression (e.g. a chained method call).
            self.force_materialize(a + 1, obj)
            self.write_reg(a, IndexExpr(LocalExpr(a + 1), self.rk(c)))

    def _finalize_pending(self) -> None:
        while self._table_ctx_stack:
            self._close_table_ctx()
        pending = self._self_pending
        if pending is not None:
            self._self_pending = None
            a, a1, obj, name = pending
            self.force_materialize(a1, obj)
            # Reference the just-materialized register, not the raw `obj`
            # tree -- same duplicate-evaluation hazard as the dynamic-key
            # branch of _self above.
            self.write_reg(a, IndexExpr(LocalExpr(a1), ConstExpr(name)))

    # ---- calls / returns / vararg ------------------------------------------
    def _call(self, li: LirInstr, tail: bool) -> None:
        ri = li.ri
        a, b, c = ri.a, ri.b, ri.c
        pending = self._self_pending
        if pending is not None and pending[0] == a:
            self._self_pending = None
            _, _a1, obj, name = pending
            fn_expr, is_method, method, arg_start = obj, True, name, a + 2
        else:
            fn_expr, is_method, method, arg_start = self._read_reg(a), False, None, a + 1

        if b == 0:
            args = self._consume_open(arg_start)
        else:
            n_fixed = (a + b) - arg_start
            args = tuple(self._read_reg(arg_start + i) for i in range(n_fixed))

        call_expr = CallExpr(fn_expr, args, is_method=is_method, method=method)

        if tail:
            self._out.append(ReturnStmt((call_expr,), True))
            return

        if c == 0:
            if self._open is not None:
                raise ReconstructError(f"pc {ri.pc}: an open producer is already pending")
            self._open = (a, call_expr)
        elif c == 1:
            self._out.append(ExprStmt(call_expr))
        else:
            regs = tuple(range(a, a + c - 1))
            self._emit_multi(regs, call_expr)

    def _return(self, a: int, b: int) -> None:
        if b == 1:
            self._out.append(ReturnStmt((), False))
        elif b >= 2:
            exprs = tuple(self._read_reg(a + i) for i in range(b - 1))
            self._out.append(ReturnStmt(exprs, False))
        else:
            exprs = self._consume_open(a)
            self._out.append(ReturnStmt(exprs, True))

    def _vararg(self, a: int, b: int) -> None:
        if b == 0:
            if self._open is not None:
                raise ReconstructError("an open producer is already pending")
            self._open = (a, VarargExpr())
        elif b == 1:
            pass                                        # zero targets requested: no-op
        else:
            regs = tuple(range(a, a + b - 1))
            self._emit_multi(regs, VarargExpr())

    @staticmethod
    def _fold_concat(parts: tuple[Expr, ...]) -> Expr:
        # Lua's `..` is right-associative and luaV_concat itself combines
        # right-to-left; nesting this way is both source-faithful and
        # matches the runtime's own combining order.
        expr = parts[-1]
        for p in reversed(parts[:-1]):
            expr = BinExpr("..", p, expr)
        return expr

    def _settable(self, a: int, b: int, c: int) -> None:
        table = self._read_reg(a)
        key = self.rk(b)
        val = self.rk(c)
        self._emit_assign((IndexTarget(table, key),), (val,))

    # ---- main dispatch ------------------------------------------------------
    def _dispatch(self, li: LirInstr) -> None:
        ri = li.ri
        op, a = ri.op, ri.a

        if op is Op.NEWTABLE:
            # Only a genuine register conflict (this NEWTABLE reuses the
            # innermost active context's own register) forces a close --
            # a table literal nested as another's *value* pushes its own
            # context instead, so it can still fold into a real nested
            # TableExpr rather than degrading the outer constructor too.
            if self._table_ctx_stack and self._table_ctx_stack[-1]["reg"] == a:
                self._close_table_ctx()
            self._table_ctx_stack.append({"reg": a, "array": [], "hash": [], "hazard": frozenset()})
            return

        if self._table_ctx_stack:
            ctx = self._table_ctx_stack[-1]
            reg = ctx["reg"]
            if op is Op.SETLIST and a == reg:
                self._fold_setlist(li)
                return
            if op is Op.SETTABLE and a == reg and isk(ri.b):
                self._fold_settable(ri)
                return
            fx = li.effects
            # Close (materializing the table with its array/hash items AS
            # THEY WERE when folded) before letting this instruction touch
            # either the ctx's own register (`reg`) or any register one of
            # its already-folded items references by LocalExpr (`hazard`,
            # see _local_regs_in). Missing the hazard half of this check is
            # exactly the bug task-6-report.md documents: `local t = {a, b,
            # c}` followed by any statement that reassigns `a`/`b`/`c` before
            # something finally reads `t` (e.g. luac reusing those same
            # register numbers for a subsequent generic-for's staging, an
            # extremely common shape) silently changed the printed table's
            # contents to the *reassigned* values instead of the ones that
            # were live at fold time -- reading only fx.writes/fx.reads for
            # the ctx's own base register never caught a write to one of the
            # *item* registers.
            if (reg in fx.reads or fx.writes & ({reg} | ctx["hazard"])
                   or fx.reads_open or fx.writes_open):
                # This instruction interacts with the innermost pending
                # context's register (typically: it's about to read a nested
                # table literal's register as its own value) -- close just
                # that innermost context and re-evaluate the same
                # instruction from scratch. It may now match the next-outer
                # context (e.g. a SETTABLE folding the just-closed nested
                # table in as a hash value), or bottom out at
                # _dispatch_simple; either way the stack strictly shrinks on
                # this branch, so this cannot recurse forever.
                self._close_table_ctx()
                self._dispatch(li)
                return

        self._dispatch_simple(li)

    def _dispatch_simple(self, li: LirInstr) -> None:
        ri = li.ri
        op, a, b, c, bx = ri.op, ri.a, ri.b, ri.c, ri.bx
        k = self.proto.constants

        if op is Op.MOVE:
            self.write_reg(a, self.rk(b))
        elif op is Op.LOADK:
            self.write_reg(a, ConstExpr(k[bx]))
        elif op is Op.LOADBOOL:
            if c != 0:
                # C!=0 means "skip the next instruction" (lvm.c's
                # dojump(L, pc, 1)) -- a control-flow effect this dispatch
                # (straight-line-only) cannot represent. Currently
                # unreachable: a LOADBOOL with C!=0 always has a
                # non-fallthrough successor (successors() gives it (pc+2,)
                # instead of (pc+1,)), which fails the SIR straight-run
                # check and sends the whole function to the M2 fallback
                # before reconstruct_straight ever sees it -- but that is an
                # upstream invariant this module should not rely on
                # silently. Refuse explicitly rather than dropping the skip.
                raise ReconstructError(
                    f"pc {ri.pc}: LOADBOOL C={c} (skip-next form) is a "
                    "control-flow effect, not reconstructible as a plain write")
            self.write_reg(a, ConstExpr(bool(b)))
        elif op is Op.LOADNIL:
            for i in range(a, b + 1):
                self.write_reg(i, ConstExpr(None))
        elif op is Op.GETGLOBAL:
            self.write_reg(a, GlobalExpr(k[bx]))
        elif op is Op.SETGLOBAL:
            self._emit_assign((GlobalTarget(k[bx]),), (self._read_reg(a),))
        elif op is Op.GETTABLE:
            self.write_reg(a, IndexExpr(self._read_reg(b), self.rk(c)))
        elif op is Op.SETTABLE:
            self._settable(a, b, c)
        elif op is Op.GETUPVAL:
            self.write_reg(a, UpvalExpr(b))
        elif op is Op.SETUPVAL:
            self._emit_assign((UpvalTarget(b),), (self._read_reg(a),))
        elif op is Op.SELF:
            self._self(a, b, c)
        elif op in _ARITH:
            self.write_reg(a, BinExpr(_ARITH[op], self.rk(b), self.rk(c)))
        elif op is Op.UNM:
            self.write_reg(a, UnExpr("-", self._read_reg(b)))
        elif op is Op.NOT:
            self.write_reg(a, UnExpr("not", self._read_reg(b)))
        elif op is Op.LEN:
            self.write_reg(a, UnExpr("#", self._read_reg(b)))
        elif op is Op.CONCAT:
            parts = tuple(self._read_reg(i) for i in range(b, c + 1))
            self.write_reg(a, self._fold_concat(parts))
        elif op is Op.CALL:
            self._call(li, tail=False)
        elif op is Op.TAILCALL:
            self._call(li, tail=True)
        elif op is Op.RETURN:
            self._return(a, b)
        elif op is Op.VARARG:
            self._vararg(a, b)
        elif op is Op.SETLIST:
            self._standalone_setlist(li)
        elif op is Op.CLOSURE:
            self.write_reg(a, ClosureExpr(bx))
        else:
            raise ReconstructError(f"pc {ri.pc}: opcode {op.name} not reconstructible")


def reconstruct_straight(fn: LirFunction, instrs: tuple[LirInstr, ...],
                         rc: RegClass, depth: int) -> tuple[Stmt, ...]:
    """Thin one-shot wrapper: build a fresh Reconstructor and reconstruct a
    single straight-line instruction run. Real (multi-region) callers share
    one Reconstructor across the whole SIR walk instead -- see the class
    docstring.
    """
    return Reconstructor(fn, rc, depth).stmts_for(instrs)

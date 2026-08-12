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

Reading a *staged* register pops its definition out of the environment.
Single-use is what `express.freereg.stack_discipline` proves before a
definition is ever classified a temporary: it simulates `lparser.c`'s
`freereg = nactvar` allocation discipline and disqualifies any definition
read zero times or more than once (see that module's docstring -- this used
to cite `_adjacent_pure`, the effect-based barrier the freereg simulation
replaced in M3 task 8). Reading a *materialized* register never pops; it
yields a fresh `LocalExpr(reg)` reference, which is safe to embed more than
once (printing a variable name twice has no evaluation-order consequence,
unlike printing a pending expression tree twice).

The question "is this register staged or materialized?" is answered per
DEFINITION, not per register number (M4 task 13): `write_reg` keys on
`(pc, reg)` against `RegClass.temp_defs`, and `self._pending` records what
each write decided so `_read_reg` can act on it. One register number is
routinely a declared local in one statement and expression-stack scratch in
the next, because `lparser.c` resets `freereg = nactvar` at every statement
boundary.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from pyluadec.ingest.proto import LuaNumber
from pyluadec.lift.lift import LirFunction, LirInstr
from pyluadec.lift.opcodes import ArgMode, Fmt, OP_SPECS, Op, indexk, isk
from pyluadec.sir.regions import CondValue, VAlt, VNode, VTail

from .expr import (BinExpr, CallExpr, ClosureExpr, ConstExpr, Expr, GlobalExpr,
                   IndexExpr, LocalExpr, MultiSpill, TableExpr, UnExpr, UpvalExpr,
                   VarargExpr)
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
_CMP_SYM = {Op.EQ: "==", Op.LT: "<", Op.LE: "<="}
# The same instruction read the other way round; see `_reads_as_gt`. `EQ` is
# absent on purpose -- `codecomp`'s operand exchange is guarded by
# `op != OP_EQ`, so an `EQ`'s operands are always in source order.
_GT_SYM = {Op.LT: ">", Op.LE: ">="}


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
        # NumericFor/GenericFor printer), never by this module. They are NOT
        # seeded here: their scope is the loop's body, so the printer calls
        # `declare_loop_vars` INSIDE the `open_scope`/`close_scope` pair that
        # brackets that body (M5 task 5). Seeding them whole-function -- which
        # is what this line did through M4 -- makes `write_reg` print a bare
        # `l1_3 = 60` for a write to the same slot AFTER the loop, where the
        # name is out of scope and Lua reads it as a write to a global. See
        # `declare_loop_vars`.
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
        self.declared: set[int] = set(range(fn.proto.numparams))
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
        # Registers `write_reg` must stage into `env` instead of materializing,
        # regardless of `rc`. Held only for the duration of one `_value_run`
        # (see it): a short-circuit alternative's final value is an EXPRESSION
        # feeding an `and`/`or`, so the instruction that computes it must not
        # emit the `local ... = ...` statement `rc` would otherwise ask for.
        self._force_temp: set[int] = set()
        # Registers whose `env` entry is an UNCONSUMED staged temp expression
        # (as opposed to the `LocalExpr(reg)` placeholder force_materialize
        # leaves behind). Made explicit because classification is now per
        # definition: the same register number can hold a staged temp at one
        # pc and a materialized local at another, so "is env[reg] poppable?"
        # can no longer be answered from `rc`/`declared` alone.
        self._pending: set[int] = set()
        # Registers that have had a staged temp popped and inlined and have
        # not been re-staged or materialized since. Reading one again would
        # print a name that was never declared -- see _read_reg.
        self._consumed: set[int] = set()
        self._pc: int | None = None
        self._out: list[Stmt] = []
        # pc -> largest constant index referenced strictly before it;
        # built on first use by `_max_const_index_before`.
        self._maxk_before: dict[int, int] | None = None

    # ---- public API (spec) --------------------------------------------
    def stmts_for(self, instrs: tuple[LirInstr, ...]) -> tuple[Stmt, ...]:
        self._out = []
        for li in instrs:
            self._dispatch(li)
        self._finalize_pending()
        return tuple(self._out)

    def open_scope(self) -> tuple[frozenset[int], dict[int, Expr], frozenset[int], frozenset[int]]:
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
        `_pending`/`_consumed` are restored for the same reason: they index
        into `env` and would otherwise describe entries the rollback removed.
        """
        return (frozenset(self.declared), dict(self.env),
                frozenset(self._pending), frozenset(self._consumed))

    def close_scope(self, snap: tuple[frozenset[int], dict[int, Expr], frozenset[int], frozenset[int]]) -> None:
        """Roll `declared`/`env`/`_pending`/`_consumed` back to `snap`.

        **The one hazard this rollback could create, argued in BOTH
        directions** (M3 left a deferred minor here because only the forward
        half was written down). Restoring `env` and `_pending` wholesale can in
        principle RESURRECT a staged expression: if register R is pending when
        the block opens, the block consumes it (pops and inlines it), and a
        read after the `end` pops it a second time, one effectful expression
        gets printed twice.

        Forward: it does not happen, because a region's condition and control
        operands are consumed *before* `open_scope` is called (see
        `sir.build`'s region construction and `emit.lua.Printer.region`), so
        nothing that a block body could consume is pending across the
        snapshot boundary.

        Backward, which is what was missing: measured over the whole corpus
        (M4 task 12), **0 of 1853 `open_scope`/`close_scope` pairs re-added any
        register to `_pending`**, so the antecedent of the hazard never once
        arises on real bytecode -- not merely "the consequent was never
        observed". Re-derive by wrapping these two methods and diffing
        `self._pending` across `orig_close`. This is a measurement, not a
        guarantee: a future region type that stages an operand and then opens a
        scope before consuming it would create the antecedent, and the fix then
        is to consume before snapshotting rather than to weaken the rollback.
        """
        self.declared = set(snap[0])
        self.env = dict(snap[1])
        self._pending = set(snap[2])
        self._consumed = set(snap[3])

    def declare_loop_vars(self, regs) -> None:
        """Bring a `for` statement's own variables into scope for its body.

        Called by `emit.lua`'s `NumericFor`/`GenericFor` arms immediately
        after `open_scope`, so `close_scope` at the loop's `end` takes them
        back out again -- which is exactly `lparser.c`'s `forbody`
        (`new_localvar` for the control triple and the visible variables,
        then `enterblock`/`leaveblock` around the body).

        Two things depend on the registers being in `declared` while the body
        is walked: a body that writes back to the loop variable (legal Lua --
        `for i = 1, 3 do i = i + 10 end` reassigns `i` without affecting
        iteration) must print an `Assign`, not a second `local`; and a body
        that only reads it must find a name rather than a staged expression.

        Two things depend on them being OUT of `declared` afterwards. luac
        hands the slots straight back to the next statement's expression stack
        (`leaveblock` restores `fs->freereg = fs->nactvar`), so a later write
        to the same slot is an ordinary temp or an ordinary fresh local -- and
        printing it as `l1_3 = ...` names a variable that is no longer in
        scope, which Lua compiles as a write to a GLOBAL. Measured on
        `snr_novel.lua:main_6` (`for l1_3 = 0, 20 do ... end` followed by
        `switchScreen(0, "", 60)`, whose third argument lands in slot 3):
        before this change the printed chunk carried a `SETGLOBAL "l1_3"` the
        original never had.
        """
        self.declared.update(regs)

    def stage(self, reg: int, e: Expr) -> None:
        """Put `e` into `reg` as an UNCONSUMED expression-stack temporary: the
        next read of `reg` pops it and inlines it, and nothing is emitted as a
        statement.

        The one supported way to seed staged state, for `write_reg` and for
        tests that drive this class directly. Assigning to `self.env` is not
        equivalent -- `env` also holds the `LocalExpr` placeholders
        `force_materialize` leaves for declared locals, so `_pending` is what
        separates "poppable temp" from "name of a live local".
        """
        self.env[reg] = e
        self._pending.add(reg)
        self._consumed.discard(reg)

    def take_expr(self, reg: int) -> Expr:
        """Pop a control slot's staged definition (NumericFor init/limit/step,
        GenericFor's iterator triple). Raises if nothing is staged there --
        guessing a default would silently fabricate semantics.
        """
        if reg not in self.env:
            raise ReconstructError(f"register {reg} has no staged expression to take")
        if reg in self._pending:
            self._pending.discard(reg)
            self._consumed.add(reg)
        return self.env.pop(reg)

    def cond_operand(self, x: int) -> Expr:
        """If-condition RK operand: K bit set -> ConstExpr; temp register ->
        popped and inlined; local register -> LocalExpr (not popped).
        """
        return self.rk(x)

    def _is_stack_temp(self, reg: int, pc: int) -> bool:
        """Is `reg` an expression-stack temporary at `pc`, rather than a live
        named local?

        The one place the register model is asked a question about *evaluation
        order* rather than about how to print a value, so it is worth being
        explicit about what it does and does not answer. `rc.temp_defs` is
        keyed by DEFINITION pc, so for a read operand (which is what both
        callers pass) the `(pc, reg)` disjunct is essentially never the one
        that fires -- the load-bearing half is the whole-register `rc.temps`
        verdict, "every tracked definition of this register is a luac
        temporary". That is the conservative direction: a register the
        classifier could not fully vouch for is treated as a local, and every
        caller's fallback for "local" is the behaviour that was already
        shipping.

        Kept as one named predicate because `_reads_as_gt` and
        `_is_generic_for_iterator` must agree on what "temp at this pc" means
        -- they are the two rules in this class that consult the register
        classification to decide the SHAPE of the source luac saw, not merely
        how to render a value.
        """
        return reg in self.rc.temps or (pc, reg) in self.rc.temp_defs

    def _max_const_index_before(self, pc: int) -> int:
        """The largest constant-table index any instruction BEFORE `pc`
        references, or -1 if none does. Cached per function.

        This is a proxy for "how far luac's constant table had grown by the
        time it reached this instruction". It is a proxy rather than the exact
        answer because `luaK_exp2RK` interns a constant *before* emitting the
        instruction that names it -- which is exactly the phenomenon
        `_reads_as_gt` is reading -- so a constant can carry an index lower
        than one referenced earlier in the code. Every K-mode operand is
        counted, taken from `OP_SPECS` (transcribed from `lopcodes.c`), so
        `LOADK`/`GETGLOBAL`/`SETGLOBAL`'s Bx and every RK B/C slot are all in.
        """
        if self._maxk_before is None:
            table: dict[int, int] = {}
            running = -1
            for p in sorted(self.fn.instrs):
                table[p] = running
                ri = self.fn.instrs[p].ri
                spec = OP_SPECS[ri.op]
                if spec.fmt is Fmt.iABx and spec.bmode is ArgMode.K:
                    running = max(running, ri.bx)
                elif spec.fmt is Fmt.iABC:
                    if spec.bmode is ArgMode.K and isk(ri.b):
                        running = max(running, indexk(ri.b))
                    if spec.cmode is ArgMode.K and isk(ri.c):
                        running = max(running, indexk(ri.c))
            self._maxk_before = table
        return self._maxk_before.get(pc, -1)

    def _reads_as_gt(self, ri) -> bool:
        """Was this `LT`/`LE` written `>`/`>=` in the source?

        ## Why the question exists

        `lcode.c`'s `codecomp` (673-686) compiles `a > b` by evaluating `a`
        and `b` in that order and then **exchanging the operands** so it can
        emit `OP_LT`:

            OPR_LT: codecomp(OP_LT, 1, e1, e2)   ->  LT 1 RK(e1) RK(e2)
            OPR_GT: codecomp(OP_LT, 0, e1, e2)   ->  LT 1 RK(e2) RK(e1)

        (`luaK_posfix`, 775-778; both then have `cond == 1` and an enclosing
        `if` inverts A to 0.) So `x < y` and `y > x` produce the *identical*
        instruction, and printing every `LT` as `<` is not "the canonical
        form" -- it is a guess about which of two sources luac saw, and when
        the guess is wrong the recompile puts the operands' own code and
        constants in the other order.

        ## What is observable

        The operands are evaluated **left to right**: `luaK_infix`'s default
        arm (710-733) calls `luaK_exp2RK(fs, e1)` before the parser has even
        seen `e2`. Two consequences, and they are the whole decision:

        * a register operand evaluated first sits in a LOWER register (it was
          pushed onto the expression stack first) -- **but only if it is an
          expression-stack temporary at all**, see the gate below;
        * a constant operand evaluated first is interned into the constant
          table before anything the other operand creates, so it carries a
          LOWER index.

        In the `<` reading the operand in field B was evaluated first; in the
        `>` reading it is the one in field C. So:

        * both operands registers **and both expression-stack temporaries at
          this pc** -> `>` iff `B > C`;
        * both operands constants -> `>` iff `idx(B) > idx(C)`;
        * B constant, C register -> `>` iff B's constant is newer than
          everything the code before this instruction has referenced, i.e.
          `idx(B) > _max_const_index_before(pc)`. That is the corpus shape:
          `if select("#", ...) > 0 then`, where `select` and `"#"` are
          interned by the call and `0` only afterwards, so the original pool
          is `select, #, 0` and printing `0 < select("#", ...)` recompiles to
          `0, select, #`.
        * C constant, B register -> never flipped. The evidence would be
          "C's constant is OLDER than what B's own code created", and
          `_max_const_index_before` cannot distinguish that from the very
          common `x < 5` where `5` was already in the pool. Both readings of
          that shape compile identically anyway (a bare local contributes no
          code and no constants), so there is nothing to win and a
          false positive to lose. Recorded as a deliberate gap, not an
          oversight; `tests/test_express_residual.py::
          test_the_gt_recogniser_leaves_a_constant_in_field_c_alone` pins it.

        ## The second deliberate gap: a register operand that is a LIVE LOCAL

        The "evaluated first sits in a lower register" step is a statement
        about the **expression stack**, and it only holds for values that
        were pushed onto it. `luaK_exp2RK` on a `VLOCAL` (via `luaK_exp2anyreg`
        -> `discharge2anyreg`, lcode.c:400-420) returns the variable's
        **existing** register and pushes nothing: `luaK_reserveregs` is never
        called, `freereg` does not move, and the operand's register number is
        its declaration slot -- an artefact of where the enclosing function
        happened to declare it, carrying no information about evaluation
        order at all. So for `f(x) < y_local`, `f(x)`'s result is a fresh
        temporary allocated *above* every live local while `y_local` sits
        low, the raw `B > C` test sees the flip condition satisfied, and the
        arm would print `y_local > f(x)` -- the opposite of the source, on no
        evidence. `(local, local)` is pure declaration order and says even
        less.

        Hence the gate: the arm fires only when **both** register operands
        are expression-stack temporaries at this pc, using the same
        `rc.temps` / `rc.temp_defs` predicate `_is_generic_for_iterator`
        uses. `(temp, local)`, `(local, temp)` and `(local, local)` are
        recorded as **undecidable** and left in the `<` reading, exactly like
        the C-constant gap above -- and for the same reason, the cost is
        nothing: a bare local contributes no code and no constants, so both
        readings of those shapes compile identically and certification cannot
        tell them apart. Measured over the corpus this session (fix round 1,
        Important 2): 43 static both-register sites satisfy `B > C`, of which
        only **3** are `(temp, temp)` (17 `(temp, local)`, 13
        `(local, local)`, 10 `(local, temp)`); 20 firings reached the arm
        while printing, of which 4 were `(temp, temp)`; and adding this gate
        moved the corpus `L3` count by **0** protos. The ~15 flips it
        withdraws were arbitrary readability choices dressed as an `lcode.c`
        derivation. `tests/test_express_residual.py::
        test_the_gt_recogniser_leaves_a_local_operand_alone` pins it.

        ## Why being wrong is cheap

        Both readings are the same boolean, so a wrong answer is never a
        semantic error -- it costs a certification, exactly as the
        always-`<` reading did. Certification is what adjudicates; this is a
        reconstruction heuristic, like every other rule in this layer.
        """
        if ri.op not in _GT_SYM:
            return False
        bk, ck = isk(ri.b), isk(ri.c)
        if not bk and not ck:
            return (ri.b > ri.c
                    and self._is_stack_temp(ri.b, ri.pc)
                    and self._is_stack_temp(ri.c, ri.pc))
        if bk and ck:
            return indexk(ri.b) > indexk(ri.c)
        if bk:
            return indexk(ri.b) > self._max_const_index_before(ri.pc)
        return False

    def condition_expr(self, cond: LirInstr) -> Expr:
        """A comparison/`TEST` instruction as the boolean expression that is
        true exactly when control **falls through** past the JMP following it.

        The single source of truth for condition polarity in this project:
        `emit.lua`'s `Printer.condition` (used by `If`/`While`/`Repeat`) is a
        thin `self.expr(...)` around this, and `_value_expr` needs the same
        thing as an Expr rather than as text so it can nest a gate inside a
        `BinExpr("and", ...)` with correct precedence.

        Polarity (empirically measured against real `luac_sz4` output and
        `lvm.c`'s dojump mechanics -- see `emit.lua`'s module docstring "Brief
        defects" #1): for `EQ`/`LT`/`LE` the jump fires when the comparison
        result equals A, so A==0 means the fall-through is the un-negated
        comparison and A==1 means it is its negation. For `TEST A _ C` the
        fall-through is taken when `l_isfalse(R(A)) == C`, so C==0 means R(A)
        itself and C==1 means `not R(A)`.

        `not` is built as a real `UnExpr` rather than formatted as text so the
        expression printer adds exactly the parentheses precedence requires
        (`not (a + b)`, never `not a + b`).
        """
        ri = cond.ri
        if ri.op in _CMP_SYM:
            lhs, rhs = self.cond_operand(ri.b), self.cond_operand(ri.c)
            sym = _CMP_SYM[ri.op]
            if self._reads_as_gt(ri):
                lhs, rhs, sym = rhs, lhs, _GT_SYM[ri.op]
            base = BinExpr(sym, lhs, rhs)
            return base if ri.a == 0 else UnExpr("not", base)
        if ri.op is Op.TEST:
            operand = self.cond_operand(ri.a)
            return operand if ri.c == 0 else UnExpr("not", operand)
        raise ReconstructError(f"pc {ri.pc}: {ri.op.name} is not a condition")

    # ---- the and/or VALUE idiom (sir.regions.CondValue) --------------------
    def cond_value(self, cv: CondValue) -> tuple[Stmt, ...]:
        """Reconstruct a whole short-circuit value chain as ONE assignment to
        its target register (or, when the target is an inlinable temp, as zero
        statements plus a staged expression the consumer inlines).

        The chain writes `cv.target` once per alternative, but only the LAST
        of those writes -- in pc order, the one belonging to the fall-through
        tail -- is the definition whose value leaves the region, so that is
        the definition site `write_reg`'s temp/local decision is passed
        (`pc=self._last_target_def(cv)`) rather than left to default (which
        would key on `self._pc`, whatever instruction the shared dispatch
        loop last processed -- not necessarily anything to do with this
        chain). Using an earlier alternative's write instead of the last one
        would consult a definition `stack_discipline` grades by how the
        *next* alternative overwrote it (a `TESTSET`'s write is popped with
        zero reads by the alternative that follows it, so it always grades
        local) rather than by how the chain's result is actually used.

        **Status (fix round 1, M4 task 13, Important 3(b)): defensive, not
        proven load-bearing.** The paragraph above states the reasoning that
        motivated passing an explicit `pc` rather than defaulting; it is not
        a claim that a reaching fixture exists. Measured this session:
        replacing `pc=self._last_target_def(cv)` with no `pc` argument (so
        `write_reg` falls back to `self._pc`) changes nothing observable --
        the full `test_express_*`/`test_emit_*`/`test_sir_loops_longtail.py`
        suite (162 tests, including `LOCAL_CASES_CERT_ONLY[0]`, the one
        fixture whose `CondValue` target register -- `a` in `local b, c = 1,
        2 local a = b or c while a do a = b or c end print(a)` -- is also a
        declared local elsewhere in the function, exactly the shape the
        first paragraph's "declared local somewhere else" scenario
        describes) stays green, and the full corpus's `L3` count stays
        1389/1478 unique, byte-for-byte, with the explicit `pc` removed. No
        fixture in this codebase currently distinguishes the two. Kept
        because the reasoning above is still sound as far as it goes (a
        default `self._pc` is a stale, arbitrary value with no defined
        relationship to `cv` at all, so relying on it would be an accident
        even where it happens not to matter today) and because deleting it
        would silently reintroduce exactly the dependency on dispatch-loop
        ordering the explicit `pc` was written to avoid -- but the docstring
        no longer claims this is proven necessary by any test in the suite.
        """
        self._out = []
        expr = self._value_expr(cv.node, cv.target)
        self.write_reg(cv.target, expr, pc=self._last_target_def(cv))
        self._finalize_pending()
        return tuple(self._out)

    def _last_target_def(self, cv: CondValue) -> int | None:
        """The highest pc in `cv.claimed_pcs` that writes `cv.target`, or None
        (no such instruction -> no `temp_defs` entry -> materialize).

        See `cond_value`'s docstring, "Status" -- defensive rather than
        proven load-bearing by any fixture in this suite as of fix round 1.
        """
        writes = [pc for pc in cv.claimed_pcs
                  if pc in self.fn.instrs
                  and cv.target in self.fn.instrs[pc].effects.writes]
        return max(writes) if writes else None

    def _value_expr(self, node: VNode, target: int) -> Expr:
        """The Expr for one VNode chain. Every sub-part is reconstructed in
        PROGRAM order -- staging, then gate, then inner staging, then the
        tested operand, then the rest -- because reading a temp register pops
        it out of `self.env`, so evaluating out of order would hand one
        alternative another's staged expression."""
        if isinstance(node, VTail):
            return self._value_run(node.instrs, target)
        if node.gate is not None:
            self._stage_run(node.staging)
            cond = self.condition_expr(node.gate)
            # `sir.build._parse_value` proved node.test.ri.c == 1 for a gated
            # alternative, so the outer operator is `or` and the gate binds to
            # the tested value with `and`.
            left: Expr = BinExpr("and", cond,
                                 self._tested_value(node, node.inner_staging, target))
            op = "or"
        else:
            left = self._tested_value(node, node.staging, target)
            op = "or" if node.test.ri.c == 1 else "and"
        return BinExpr(op, left, self._value_expr(node.rest, target))

    def _tested_value(self, node: VAlt, staging: tuple[LirInstr, ...],
                      target: int) -> Expr:
        """The value one alternative short-circuits on.

        `TESTSET A B C` tests a register B distinct from the destination, so
        `staging` merely stages operands and the value is `R[B]`.

        A bare `TEST A 0 C` is `lcode.c:patchtestreg`'s rewrite for the case
        where the destination register IS the tested one (A == target); the
        value is then exactly what `staging` computes into `target`, so it goes
        through `_value_run` -- which also carries the "no statements" guard.
        """
        if node.test.ri.op is Op.TESTSET:
            self._stage_run(staging)
            return self._read_reg(node.test.ri.b)
        return self._value_run(staging, target)

    def _refuse_statements(self, emitted: list[Stmt], where: str) -> None:
        """THE guard for `CondValue`. A short-circuit alternative's operand
        code is reconstructed as an expression; if it reconstructs to a
        *statement* instead, printing only the `and`/`or` expression would
        DROP that statement silently -- and the pc-claim audit would not
        notice, because the pcs are claimed by the CondValue either way (the
        audit proves nothing was left unclaimed, never that everything claimed
        was printed). Worse than dead output: the dropped statement is
        typically a `local` the surviving expression still references, which
        Lua then resolves as a GLOBAL.

        It should be unreachable on real luac output -- `lparser.c` reads an
        `and`/`or` operand with `fs->freereg == fs->nactvar`, so every register
        it writes sits above every live local and classifies temp -- and since
        M4 task 13 `classify_registers` answers per DEFINITION rather than per
        register number, so a slot that is a local elsewhere in the function
        no longer drags this operand's definition down with it. What can still
        reach here is a definition one of `stack_discipline`'s own barriers
        refuses (`_same_block`, the RK/literal barrier, the `MOVE`-from-a
        -lower-slot rule) or that `declared` already holds from an exited
        scope. Kept as a loud refusal, not an assert; the chunk then falls
        back.

        Scope, precisely (fix round finding F6): this guard inspects `emitted`
        -- what `_run_isolated` captured in `self._out`, i.e. STATEMENTS. It
        says nothing about an operand-run instruction whose staged VALUE is
        never consumed: that instruction's effect lives only in `self.env`
        (an entry keyed by register, never appended to `self._out`), so its pc
        is claimed and `emitted` stays empty either way -- this guard cannot
        see the difference and does not try to. The general property in the
        first paragraph above ("the audit proves nothing was left unclaimed,
        never that everything claimed was printed") is about the pc-claim
        audit, not about this guard; this guard is one, narrower, instance of
        acting on it, for the statement case specifically. Unreached on this
        corpus (0 occurrences across the 12 `CondValue`-containing protos and
        both fuzz runs backing this module) and, if it ever fires, would still
        be caught downstream -- an unconsumed staged value that carried a real
        side effect changes `code`/`constants` under certification, so the
        chunk fails to certify and falls back rather than shipping silently
        wrong output. Recorded here so a future reader does not read the
        general framing above as a claim this specific check independently
        makes true.
        """
        if emitted:
            raise ReconstructError(
                f"{where} reconstructs to {len(emitted)} statement(s), which an "
                "and/or expression cannot carry")

    def _run_isolated(self, instrs: tuple[LirInstr, ...]) -> list[Stmt]:
        """Dispatch `instrs` with `self._out` swapped out, returning whatever
        statements they produced instead of appending them."""
        saved = self._out
        self._out = []
        try:
            for li in instrs:
                self._dispatch(li)
            self._finalize_pending()
            return self._out
        finally:
            self._out = saved

    def _stage_run(self, instrs: tuple[LirInstr, ...]) -> None:
        """Reconstruct operand code that only stages values into `self.env`."""
        if not instrs:
            return
        self._refuse_statements(
            self._run_isolated(instrs),
            f"pc {instrs[0].ri.pc}: and/or operand code")

    def _value_run(self, instrs: tuple[LirInstr, ...], reg: int) -> Expr:
        """The value an alternative's straight run leaves in `reg`, as an Expr.

        An EMPTY run is not a failure: `lcode.c:discharge2reg` emits nothing
        when the operand already sits in the destination register, so the value
        on that path is `reg`'s incoming value -- which `_read_reg` is exactly
        the right way to obtain (it pops a still-pending temp, or yields the
        live local's name). Measured on the corpus at
        `snr_graphic.lua:main_3` pc 39, `x = <cond> and 9 or x`.
        """
        if not instrs:
            return self._read_reg(reg)
        if not any(reg in li.effects.writes for li in instrs):
            raise ReconstructError(
                f"pc {instrs[0].ri.pc}: and/or alternative does not write "
                f"register {reg}")
        self._force_temp.add(reg)
        try:
            emitted = self._run_isolated(instrs)
        finally:
            self._force_temp.discard(reg)
        self._refuse_statements(
            emitted, f"pc {instrs[0].ri.pc}: and/or alternative")
        if reg not in self.env:
            raise ReconstructError(
                f"pc {instrs[0].ri.pc}: and/or alternative left no expression "
                f"in register {reg}")
        return self.env.pop(reg)

    # ---- operand helpers -------------------------------------------------
    def rk(self, x: int) -> Expr:
        if isk(x):
            return ConstExpr(self.proto.constants[indexk(x)])
        return self._read_reg(x)

    def _read_reg(self, reg: int) -> Expr:
        # A register with an unconsumed staged temp pops, whatever else is
        # true of it: `_pending` records what the WRITE decided (see
        # write_reg), and that decision is per definition-pc now, so neither
        # `declared` nor `rc.temps` can answer this on their own. A register
        # can be a materialized local at one pc and hold a staged temp at a
        # later one, once luac has released the slot.
        if reg in self._pending:
            self._pending.discard(reg)
            self._consumed.add(reg)
            return self.env.pop(reg)
        # `declared` otherwise wins over rc's static classification: once a
        # register has been force-materialized (a real `local`/reassignment
        # statement was emitted for it -- see force_materialize), it is a
        # stable, reread-many-times reference. This matters for the few
        # opcodes (SELF, the SETLIST degrade path) that deliberately
        # force-materialize a register rc still calls temp.
        if reg in self.declared:
            return self.env.get(reg, LocalExpr(reg))
        if reg in self._consumed:
            # THE guard for per-definition staging. The value staged into
            # `reg` was inlined into some earlier expression and popped; there
            # is no `local` carrying it, so emitting `LocalExpr(reg)` here
            # would print a name this function never declares -- which Lua
            # resolves as a GLOBAL read, silently. `stack_discipline` only
            # grades a definition a temp when its value is read exactly once
            # before the statement ends, so a second read means the pc-linear
            # simulation mismodelled this shape (its own documented
            # approximation: it has no control-flow model). Refuse loudly and
            # let the chunk fall back rather than ship a global reference.
            raise ReconstructError(
                f"register {reg} is read again after its staged value was "
                "consumed; classification called that definition a temporary")
        if reg in self.rc.temps:
            raise ReconstructError(f"temp register {reg} read before it was staged")
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
        if reg in self._pending:
            self._pending.discard(reg)
            self.force_materialize(reg, self.env.pop(reg))
        return LocalExpr(reg)

    def write_reg(self, reg: int, e: Expr, pc: int | None = None) -> None:
        """Stage `e` into `reg` if the definition at `pc` is a luac expression
        -stack temporary, otherwise emit it as a real statement.

        `pc` is the definition site, and it is what the decision keys on --
        `rc.temp_defs` is a set of `(pc, reg)` pairs. Consulting the
        whole-function `rc.temps` instead (what this did before M4 task 13)
        forced every definition of a register down to the most conservative
        verdict any one of them earned, which materialized luac's expression
        stack as named locals and emitted the `MOVE`s that copy into it: 253
        of the 1478 corpus protos differed from the original by extra `MOVE`s
        and nothing else. `pc` defaults to the instruction currently being
        dispatched; callers whose write belongs to an *earlier* instruction
        (a deferred table constructor, a pending SELF receiver) pass that
        instruction's pc explicitly.

        The `rc.temps` disjunct is `RegClass`'s own documented invariant read
        directly ("for every `r in temps`, every tracked def `(pc, r)` is in
        `temp_defs`") rather than relied upon: it is redundant for anything
        `classify_registers` produces, and it keeps a hand-built `RegClass`
        -- which gets `temp_defs=frozenset()` from the field default -- meaning
        what its `temps` field says.

        `declared` still wins: once a register has been materialized as a
        named local, a later write to it is a reassignment. That is
        deliberately more conservative than `temp_defs` alone -- `declared` is
        a whole-function set outside of the block scopes `open_scope`/
        `close_scope` model, so a slot luac released at a scope exit this
        module cannot see is still treated as holding a live local. Being
        wrong that way costs certifications; staging over a live local would
        cost correctness (the local's later reads would silently see the wrong
        value), so the asymmetry is on purpose.
        """
        if reg in self._force_temp:
            self.stage(reg, e)
            return
        if pc is None:
            pc = self._pc
        if reg not in self.declared and (reg in self.rc.temps
                                         or (pc, reg) in self.rc.temp_defs):
            self.stage(reg, e)
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
        self._refuse_stale_reference(reg)
        if reg in self.declared:
            self._out.append(Assign((LocalTarget(reg),), (e,)))
        else:
            self._out.append(LocalDecl((reg,), (e,)))
            self.declared.add(reg)
        self.env[reg] = LocalExpr(reg)
        self._pending.discard(reg)
        self._consumed.discard(reg)

    def _refuse_stale_reference(self, reg: int) -> None:
        """Refuse to give `reg` a new value while a still-staged expression
        refers to its old one by name.

        `_read_reg` hands out `LocalExpr(reg)` -- a NAME, not a value snapshot
        -- for a materialized register, and a staged expression is not printed
        until whatever finally consumes it is. So if `reg` is reassigned in
        between, the staged tree silently prints the new value. Two
        materializations into one slot inside a single emitted statement is
        the shape that does it: `gameSave[k1][k2][k3] = v`, staged through one
        register, printed as `gameSave[l1_1][l1_1][l1_1] = l1_2`.

        This is the same hazard `_dispatch`'s table-constructor `hazard` set
        handles for a deferred `TableExpr`, generalized to every staged
        expression -- and unlike that one it cannot be repaired by emitting
        earlier, because the staged tree may already be half-built. Refusing
        drops the chunk to fallback, which is the correct trade: the
        alternative is output that is not merely unfaithful but wrong.

        Reachability, measured 2026-08-11: 0 of 1478 unique corpus protos
        reach this. It was reached before this task's `VKNUM`/`MAXINDEXRK`
        correction (`snr_crd_15.lua:main_1` printed exactly the line above),
        so it is a live hazard of the per-definition classification rather
        than a hypothetical, and it is pinned by injection in
        tests/test_express_liverange.py::
        test_reassigning_a_register_a_staged_expression_names_is_refused.
        """
        for other, staged in self.env.items():
            if other != reg and other in self._pending \
                    and reg in _local_regs_in(staged):
                raise ReconstructError(
                    f"register {reg} is being given a new value while the "
                    f"expression staged in register {other} still refers to "
                    "it by name")

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
        if self._is_generic_for_iterator(regs):
            # `for k, v in pairs(t) do` -- one source expression adjusted to
            # three values, which `forlist` (lparser.c:1102-1130) stages
            # straight into the control triple. Materializing it prints
            # `local a, b, c = pairs(t)  for k, v in a, b, c do`, which is
            # semantically identical and compiles to three more registers and
            # three `MOVE`s. Staged instead, `emit.lua`'s `GenericFor` arm
            # takes all three back and prints the single expression.
            self.stage(regs[0], expr)
            for r in regs[1:]:
                self.stage(r, MultiSpill(regs[0]))
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
            self._pending.discard(r)
            self._consumed.discard(r)

    def _is_generic_for_iterator(self, regs: tuple[int, ...]) -> bool:
        """Is this multi-register write the staging of a generic `for`'s
        iterator triple, and may it be staged rather than materialized?

        Three conditions. The second and third are load-bearing; the first is
        **defensive** -- see the note below it.

        * `regs` is exactly `(a, a+1, a+2)` and this function contains a
          `TFORLOOP` based at that same `a`. That is the bytecode signature of
          `forlist`: `explist1` adjusted to exactly 3 values landing in the
          three slots `TFORLOOP` then reads every iteration.

          **Status (fix round 1, Important 1): defensive rather than a fixed
          defect -- no reachable leak to regress against.** The `TFORLOOP`
          clause has never been observed to reject anything the next
          condition does not already reject, and there is a structural reason
          why it cannot. For all three of `(a, a+1, a+2)` to be temporaries
          at the same pc, either they are `dedicated_controls` -- which
          `names.classify_registers` only ever derives from a `FORPREP`/
          `FORLOOP`/`TFORLOOP` at that base -- or the freereg simulation must
          grade three simultaneous definitions temp, and it structurally
          cannot: the only other way luac emits `CALL a b 4` / `VARARG a 4` is
          `adjust_assign` to three targets, whose reverse-order stores are
          either statement-ending (`SETGLOBAL`/`SETUPVAL`, which promotes
          everything still pending to local) or bulk-popping (`SETTABLE`,
          which pops every pending entry above the table's own register, so
          all but the topmost are popped with zero reads and disqualified),
          and three targets that survive the statement are locals by
          definition. Measured this session: 0 of 4 shape-passing sites on
          the 229-file corpus lack a `TFORLOOP` at the base, and 0 of 35
          hand-written non-`TFORLOOP` `luac` shapes (`a,b,c = f()`,
          `t[1],t[2],t[3] = f()`, `local a,b,c = ...`, the same inside `for`/
          `while`/`repeat`/nested functions, ...) has all three targets temp.
          So no fixture built from real `luac` output can isolate this clause,
          and `tests/test_express_residual.py::
          test_the_iterator_recogniser_needs_a_tforloop_at_the_base` pins it
          the only way that is left: real bytecode with a hand-built
          `RegClass` that satisfies the other two conditions. Kept because
          "the `TFORLOOP` is what makes this a generic `for`" is the actual
          proposition being tested and inferring it from the register grading
          alone would be an accident.
        * every one of the three definitions is a temporary at THIS pc
          (`rc.temp_defs`, or the whole-register `rc.temps` for a hand-built
          `RegClass`). A generic-for whose control slots the classifier had to
          call locals -- because the register numbers do other work elsewhere
          in the function that `classify_registers` could not separate -- must
          keep the materialized form; staging it would inline the iterator
          into a header whose slots something else is relying on.
        * none of the three is already `declared`, i.e. already a live named
          local in the printed output. Same rule as `write_reg`'s.

        Nothing here is a soundness argument for the OUTPUT -- certification
        is that. It is the "is this the shape luac compiled from" question,
        and every one of the three conditions failing sends the shape back to
        the materialized print, which is always valid Lua.
        """
        if len(regs) != 3 or regs != tuple(range(regs[0], regs[0] + 3)):
            return False
        a = regs[0]
        if not any(li.ri.op is Op.TFORLOOP and li.ri.a == a
                   for li in self.fn.instrs.values()):
            return False
        pc = self._pc
        return all(r not in self.declared and self._is_stack_temp(r, pc)
                   for r in regs)

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
        # The table's definition site is its NEWTABLE, not whatever
        # instruction happened to force this context closed.
        self.write_reg(ctx["reg"], table, pc=ctx["pc"])

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
            self._self_pending = (a, a + 1, obj, name, self._pc)
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
            a, a1, obj, name, self_pc = pending
            self.force_materialize(a1, obj)
            # Reference the just-materialized register, not the raw `obj`
            # tree -- same duplicate-evaluation hazard as the dynamic-key
            # branch of _self above.
            self.write_reg(a, IndexExpr(LocalExpr(a1), ConstExpr(name)), pc=self_pc)

    # ---- calls / returns / vararg ------------------------------------------
    def _call(self, li: LirInstr, tail: bool) -> None:
        ri = li.ri
        a, b, c = ri.a, ri.b, ri.c
        pending = self._self_pending
        if pending is not None and pending[0] == a:
            self._self_pending = None
            _, _a1, obj, name, _self_pc = pending
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
        # The definition site every write_reg below keys its temp/local
        # decision on. Set here rather than passed down through a dozen
        # helpers; the two writes that belong to an EARLIER instruction (a
        # deferred table constructor's NEWTABLE, a pending SELF's receiver)
        # carry their own pc and pass it explicitly.
        self._pc = ri.pc

        if op is Op.NEWTABLE:
            # Only a genuine register conflict (this NEWTABLE reuses the
            # innermost active context's own register) forces a close --
            # a table literal nested as another's *value* pushes its own
            # context instead, so it can still fold into a real nested
            # TableExpr rather than degrading the outer constructor too.
            if self._table_ctx_stack and self._table_ctx_stack[-1]["reg"] == a:
                self._close_table_ctx()
            self._table_ctx_stack.append({"reg": a, "pc": ri.pc, "array": [],
                                          "hash": [], "hazard": frozenset()})
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
            # `fx.reads_open`/`fx.writes_open` close unconditionally: an open
            # region's extent is `L->top` at runtime, so neither `reg` nor
            # anything in `hazard` can be proved outside it. THIS IS
            # `writes_open`'s SECOND CONSUMER (named here because it kept
            # getting missed): the other is `express.names.classify_registers`,
            # which folds `writes_open` pcs into `open_write_pcs` and uses them
            # as a barrier in `_staging_slice`. Any change to which opcodes
            # carry an open region has to be swept over both -- see M4 task 8,
            # where adding `writes_open` to TAILCALL needed a differential run
            # precisely because of these two.
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

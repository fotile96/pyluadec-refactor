"""Effects-table / structured-reconstructor reconciliation (M4 backlog item 8).

`tests/test_effects_emitter_consistency.py` reconciles `lift/effects.py`
against `structure/fallback.py`'s emitter templates -- two independent hand
transcriptions of `vendor/lua-5.1/src/lvm.c`. Its own module docstring names
its blind spot: `express/reconstruct.py` -> `emit/lua.py` is a **third**
independent transcription and nothing reconciled it. This module does.

Re-derived this session (M4 task 9), against the sibling gate's M3-task-10
counts of "9 direct `ri.a/b/c` decode sites in reconstruct, 16 `ri.` reaches
in the printer, zero `effects` consumption as an operand source":

- `express/reconstruct.py`: **23** reads of a register-bearing operand field
  (`.a`/`.b`/`.c`) off an `ri`-rooted expression, on **16** distinct source
  lines, outside docstrings and comments (`:341,342,343,345,346,428,445,812,
  822,833,834,847,899,970,996,1033`); **42** `ri.<field>` reaches in total
  across 30 lines (`pc` 11, `c` 8, `b` 8, `op` 7, `a` 7, `bx` 1). The
  9-call-site figure did not reproduce -- it was counted before M4 added
  `condition_expr` and the whole `CondValue` reconstructor
  (`_value_expr`/`_tested_value`). `effects` is still reached exactly **3**
  times (`:406`, `:529` -- both writer-set membership tests -- and `:999`,
  the table-constructor hazard check), **none of them an operand source**,
  which is the property that mattered.
- `emit/lua.py`: **11** `ri.<field>` reaches in non-docstring code across 9
  lines (`:248,249,251,253,418,448,469,544,610`), not 16 -- `bx` 3, `a` 2,
  `op` 2, `pc` 2, `c` 1, `b` 1. Of those exactly **3** are register indices
  (`:448` `NumericFor`'s `prep.ri.a`, `:469` `GenericFor`'s `call.ri.a` and
  `.c`); the rest are pcs, subproto indices and opcode/operand-value tests
  (`:610`'s `ri.b == 1` is `RETURN`'s B field, not a register). One further
  register decode does not go through an `ri` at all and so is invisible to
  that count: `:287` reads `ps.b` off a `CLOSURE` pseudo-instruction. So
  **4** register decodes in the printer, all four covered by Arm 2 below.
  `effects` still appears **0** times.

## What this gate asserts

For every pc the structured path processes, every register the
`Reconstructor` and the `Printer` touch while processing it is in that pc's
`effects.reads | effects.writes`.

It is established in two composed arms, because the two layers touch
registers in two different ways:

**Arm 1 -- the reconstructor's accessors, pc-precise.** `_read_reg`,
`take_expr`, `_stable_ref`, `_value_run`, `stage`, `write_reg`,
`force_materialize` and `_emit_multi` are the complete set of methods through
which `Reconstructor` reads or writes a register slot. Every one of them is
wrapped by `_Recorder` below and its argument checked against the effects row
of the instruction whose handling is in progress. Attribution is taken from
the code's own structure, never re-derived: `_dispatch(li)` fixes `li.ri.pc`,
`condition_expr(cond)` fixes `cond.ri.pc`, `_tested_value` fixes its
`TESTSET`'s pc, `_finalize_pending` fixes the deferred `SELF`'s pc, and
`write_reg`'s explicit `pc=` argument (the definition site a deferred table
constructor or pending `SELF` receiver passes) is used verbatim when present.

**Arm 2 -- the printer, via `name_for`.** `express.names.name_for(reg, depth)`
is the *only* way a register becomes text in `emit/lua.py` (7 call sites, all
checked below). Every call is recorded. A printed register passes if EITHER
it was already reconciled against its own pc by Arm 1 during this function,
OR it is in the effects union of the pcs the region being printed claims.
The second disjunct is what covers the printer's own three register decodes
(`NumericFor`'s `A+3` loop variable, `GenericFor`'s `A+3+i` variables, a
`CLOSURE`'s captured `ps.b`), which no reconstructor accessor ever sees; the
first is what lets an inlined expression carry a register from an *earlier*
pc into a later region's text without that being a violation. Composed with
Arm 1, every register in the emitted source is in the effects union of the
function's own instructions.

Neither arm re-transcribes `lvm.c`. There is no fourth copy of the operand
model in this file: the reconstructor's real accessors are the only source of
"which register", and `effects.py` is the only source of "which registers are
allowed". That is the whole point -- the sibling gate's `_registers_touched`
is a frozen hand-copy of `fallback.py` and its docstring says so; this one
imports the thing it is checking.

## What it does NOT assert

- **Not equality, only containment**, exactly as the sibling gate. A row that
  over-approximates is safe; a row that omits a register a layer touches is
  not.
- **The open part of an open region.** `reads_open`/`writes_open` describe
  `R[base..top)`, which is `top`-relative at run time. The reconstructor does
  genuinely index into it: `_consume_open(start)` calls `_read_reg` on every
  fixed slot between `start` and the staged open producer's base. For a pc
  whose row carries either open flag, this gate therefore also accepts any
  register `>= ri.a`. That bound is read off the *decoded operand field*, not
  transcribed from `lvm.c` semantics, and it is uniformly valid: for all four
  open-carrying opcodes the open region begins at or above `R[A]` (`CALL`
  `R[A+1..top)`/`R[A..top)`, `TAILCALL` `R[A+1..top)`/`R[A..top)`, `RETURN`
  `R[A..top)`, `SETLIST` `R[A+1..top)`, `VARARG` `R[A..top)`). The allowance
  is measured, not assumed: `test_the_open_region_allowance_is_load_bearing`
  pins that it is used, and how much it excuses.
- **Parameters.** `name_for(i, depth + 1)` in `Printer.closure_parts` names
  the *child* function's parameter slots `0..numparams-1` while the parent is
  still the active frame. Parameter registers are a proto-header fact
  (`numparams`), not derived from any instruction word, so they are outside
  what an effects-table reconciliation can speak to. They are excluded by
  depth -- and the exclusion is bounded rather than open-ended: a name at
  `depth + 1` must be a register below the child's `numparams` or it is a
  violation.
- **Protos the structured path never reaches.** The corpus arm drives
  `emit.lua.print_chunk` once per file; a chunk that refuses part-way leaves
  its remaining descendants unprinted. Measured: 213/229 chunks print, 1821
  of the corpus's 1944 proto occurrences are entered. Re-running each proto
  as its own root would raise that but costs 3.4s against a 2.0s whole-corpus
  pass, which the suite budget does not have.
- **`JMP` and `CLOSE`.** Neither is reconstructible by the structured path at
  all (`_dispatch_simple` refuses `CLOSE`; `JMP` is consumed by region
  recognition and never dispatched), so neither can be reached here. `JMP`
  does appear inside the claimed-pc sets of `If`/`While` frames and so shows
  up in the reach measurement; `CLOSE` cannot and is pinned as absent.
"""
from __future__ import annotations

import dataclasses
import time
from contextlib import contextmanager

import pytest

from pyluadec.express.names import RegClass
from pyluadec.express.reconstruct import ReconstructError, Reconstructor
from pyluadec.emit import lua as _lua_mod
from pyluadec.emit.lua import Printer
from pyluadec.lift.effects import EffectMode, analyze
from pyluadec.lift.lift import LirFunction, LirInstr
from pyluadec.lift.opcodes import Op
from pyluadec.sir.regions import VAlt, VTail

from tests.synth import mk_instr, mk_proto
# Imported, never copied: the same operand grid the sibling gate runs, so the
# two gates cannot drift apart on which operand shapes they consider.
from tests.test_effects_emitter_consistency import _grid_instrs


class _Frame:
    """One attribution scope: the pcs a touch made inside it belongs to."""

    __slots__ = ("pcs", "covered", "ops", "open_floor", "depth", "kind",
                 "param_depth", "param_limit")

    def __init__(self, pcs, covered, ops, open_floor, depth, kind,
                 param_depth=None, param_limit=None):
        self.pcs = pcs
        self.covered = covered
        self.ops = ops
        self.open_floor = open_floor
        self.depth = depth
        self.kind = kind
        self.param_depth = param_depth
        self.param_limit = param_limit


class _Recorder:
    """Records every register the reconstructor/printer touch, and checks it.

    Deliberately holds no model of any opcode. `covered` always comes from
    `LirInstr.effects`; the register always comes from the real accessor's
    own argument.
    """

    def __init__(self):
        self.stack: list[_Frame] = []
        self.violations: list[str] = []
        self.acc_touches = 0
        self.open_excused = 0
        self.printed = 0
        self.printed_via_arm1 = 0
        self.printed_via_frame = 0
        self.params_named = 0
        self.functions = 0
        self.ops: set[Op] = set()
        self._fn_regs: list[set[int]] = []

    # -- frames ---------------------------------------------------------
    def _top(self):
        return self.stack[-1] if self.stack else None

    @contextmanager
    def pcs_frame(self, fn, pcs, depth, kind, param_depth=None, param_limit=None):
        covered: set[int] = set()
        ops: set[Op] = set()
        floor = None
        for pc in pcs:
            li = fn.instrs.get(pc)
            if li is None:                 # a claimed pc with no instruction
                continue                   # (CLOSURE pseudo-words): nothing to say
            fx = li.effects
            ops.add(li.ri.op)
            covered |= fx.reads
            covered |= fx.writes
            if fx.reads_open or fx.writes_open:
                floor = li.ri.a if floor is None else min(floor, li.ri.a)
        self.stack.append(_Frame(tuple(pcs), covered, frozenset(ops), floor,
                                 depth, kind, param_depth, param_limit))
        try:
            yield
        finally:
            self.stack.pop()

    @contextmanager
    def function_frame(self, depth):
        """Barrier between an enclosing function's frames and a nested one's.

        Without it a `CLOSURE`'s frame in the parent would still be innermost
        while the child's whole body is printed, and every one of the child's
        registers would be checked against the parent's `CLOSURE` row.
        """
        self.stack.append(_Frame((), set(), frozenset(), None, depth, "function"))
        self._fn_regs.append(set())
        self.functions += 1
        try:
            yield
        finally:
            self.stack.pop()
            self._fn_regs.pop()

    # -- touches --------------------------------------------------------
    def accessor(self, reg: int, kind: str) -> None:
        fr = self._top()
        if fr is None or fr.kind == "function":
            self.violations.append(
                f"{kind} of R{reg} outside any instruction's scope "
                "(unattributable touch -- the instrumentation cannot say "
                "which effects row should cover it)")
            return
        self.acc_touches += 1
        self.ops |= fr.ops
        if self._fn_regs:
            self._fn_regs[-1].add(reg)
        if reg in fr.covered:
            return
        if fr.open_floor is not None and reg >= fr.open_floor:
            self.open_excused += 1
            return
        self.violations.append(
            f"{kind} of R{reg} at pc(s) {sorted(fr.pcs)} [{fr.kind}] "
            f"outside effects {sorted(fr.covered)}")

    def named(self, reg: int, depth: int) -> None:
        fr = self._top()
        if fr is None:
            # Reported rather than ignored, for the same reason `accessor`
            # reports its own: a name reaching text with no active scope is
            # the shape of this instrumentation going blind, not a benign
            # case to wave through.
            self.violations.append(
                f"printed name R{reg} outside any function's scope "
                "(unattributable touch)")
            return
        if fr.param_depth is not None and depth == fr.param_depth:
            self.params_named += 1
            if not 0 <= reg < fr.param_limit:
                self.violations.append(
                    f"parameter name R{reg} at depth {depth} is not below the "
                    f"callee's numparams {fr.param_limit}")
            return
        if depth != fr.depth:
            self.violations.append(
                f"name_for(R{reg}, depth={depth}) under a depth-{fr.depth} "
                f"frame [{fr.kind}]")
            return
        self.printed += 1
        self.ops |= fr.ops
        if self._fn_regs and reg in self._fn_regs[-1]:
            self.printed_via_arm1 += 1
            return
        if reg in fr.covered or (fr.open_floor is not None
                                 and reg >= fr.open_floor):
            self.printed_via_frame += 1
            return
        self.violations.append(
            f"printed name R{reg} at pc(s) {sorted(fr.pcs)} [{fr.kind}]: "
            "neither reconciled at its own pc nor in the printed region's "
            f"effects {sorted(fr.covered)}")


@contextmanager
def instrumented(rec: _Recorder):
    """Wrap every register accessor of `Reconstructor`/`Printer` for `rec`.

    Monkeypatching rather than subclassing on purpose: the structured path
    constructs its own `Reconstructor`/`Printer` instances deep inside
    `emit.lua._print_proto_body`, so there is no seam to inject a subclass
    through, and a `print_chunk`-level driver is the only way to exercise the
    real region walk. Everything is restored in `finally`.
    """
    R, P = Reconstructor, Printer
    saved = {
        "_dispatch": R._dispatch, "condition_expr": R.condition_expr,
        "_tested_value": R._tested_value, "cond_value": R.cond_value,
        "_finalize_pending": R._finalize_pending, "_value_run": R._value_run,
        "_read_reg": R._read_reg, "take_expr": R.take_expr,
        "_stable_ref": R._stable_ref, "stage": R.stage,
        "force_materialize": R.force_materialize, "write_reg": R.write_reg,
        "_emit_multi": R._emit_multi,
        "region": P.region, "closure_parts": P.closure_parts,
        "_print_proto_body": _lua_mod._print_proto_body,
        "name_for": _lua_mod.name_for,
    }

    # ---- attribution scopes (pc taken from the code's own structure) ----
    def _dispatch(self, li):
        with rec.pcs_frame(self.fn, (li.ri.pc,), self.depth, "dispatch"):
            return saved["_dispatch"](self, li)

    def condition_expr(self, cond):
        with rec.pcs_frame(self.fn, (cond.ri.pc,), self.depth, "condition"):
            return saved["condition_expr"](self, cond)

    def _tested_value(self, node, staging, target):
        with rec.pcs_frame(self.fn, (node.test.ri.pc,), self.depth, "tested-value"):
            return saved["_tested_value"](self, node, staging, target)

    def cond_value(self, cv):
        with rec.pcs_frame(self.fn, tuple(cv.claimed_pcs), self.depth, "CondValue"):
            return saved["cond_value"](self, cv)

    def _finalize_pending(self):
        pending = self._self_pending
        if pending is None:
            return saved["_finalize_pending"](self)
        with rec.pcs_frame(self.fn, (pending[4],), self.depth, "deferred-SELF"):
            return saved["_finalize_pending"](self)

    # ---- register accessors --------------------------------------------
    def _read_reg(self, reg):
        rec.accessor(reg, "read")
        return saved["_read_reg"](self, reg)

    def take_expr(self, reg):
        rec.accessor(reg, "read(take_expr)")
        return saved["take_expr"](self, reg)

    def _stable_ref(self, reg):
        rec.accessor(reg, "read(stable_ref)")
        return saved["_stable_ref"](self, reg)

    def _value_run(self, instrs, reg):
        # The chain alternative's value leaves `reg` by `self.env.pop(reg)`,
        # which is a read of that slot that goes through no accessor.
        out = saved["_value_run"](self, instrs, reg)
        rec.accessor(reg, "read(value-run)")
        return out

    def stage(self, reg, e):
        rec.accessor(reg, "write(stage)")
        return saved["stage"](self, reg, e)

    def force_materialize(self, reg, e):
        rec.accessor(reg, "write(materialize)")
        return saved["force_materialize"](self, reg, e)

    def write_reg(self, reg, e, pc=None):
        if pc is None:
            rec.accessor(reg, "write")
            return saved["write_reg"](self, reg, e, pc)
        # An explicit `pc` is the definition site the caller is writing on
        # behalf of (a deferred table constructor's NEWTABLE, a pending
        # SELF's receiver) -- attribute the write there, not to whatever
        # instruction happened to force the flush.
        with rec.pcs_frame(self.fn, (pc,), self.depth, "write@defsite"):
            rec.accessor(reg, "write")
            return saved["write_reg"](self, reg, e, pc)

    def _emit_multi(self, regs, expr):
        for r in regs:
            rec.accessor(r, "write(multi)")
        return saved["_emit_multi"](self, regs, expr)

    # ---- printer --------------------------------------------------------
    def region(self, r, indent):
        with rec.pcs_frame(self.fn, tuple(r.claimed_pcs), self.depth,
                           type(r).__name__):
            return saved["region"](self, r, indent)

    def closure_parts(self, e):
        pc = self._closure_pc(e.proto_idx)
        child = self.proto.subprotos[e.proto_idx]
        with rec.pcs_frame(self.fn, (pc,), self.depth, "CLOSURE",
                           param_depth=self.depth + 1,
                           param_limit=child.numparams):
            return saved["closure_parts"](self, e)

    def _print_proto_body(proto, depth, upval_names):
        with rec.function_frame(depth):
            return saved["_print_proto_body"](proto, depth, upval_names)

    def name_for(reg, depth):
        rec.named(reg, depth)
        return saved["name_for"](reg, depth)

    for name, fn_ in (("_dispatch", _dispatch), ("condition_expr", condition_expr),
                      ("_tested_value", _tested_value), ("cond_value", cond_value),
                      ("_finalize_pending", _finalize_pending),
                      ("_value_run", _value_run), ("_read_reg", _read_reg),
                      ("take_expr", take_expr), ("_stable_ref", _stable_ref),
                      ("stage", stage), ("force_materialize", force_materialize),
                      ("write_reg", write_reg), ("_emit_multi", _emit_multi)):
        setattr(R, name, fn_)
    P.region = region
    P.closure_parts = closure_parts
    _lua_mod._print_proto_body = _print_proto_body
    _lua_mod.name_for = name_for
    try:
        yield rec
    finally:
        for name, orig in saved.items():
            if name in ("region", "closure_parts"):
                setattr(P, name, orig)
            elif name in ("_print_proto_body", "name_for"):
                setattr(_lua_mod, name, orig)
            else:
                setattr(R, name, orig)


# The register-bearing accessors this gate claims to cover. Pinned so that a
# new accessor added to `Reconstructor` -- a new way to touch a register that
# nothing here wraps -- fails a named test instead of silently shrinking what
# "touch" means (invariant 2 of the task brief).
_WRAPPED_ACCESSORS = frozenset({
    "_read_reg", "take_expr", "_stable_ref", "_value_run",
    "stage", "force_materialize", "write_reg", "_emit_multi"})

# The one `reg`-taking method deliberately NOT wrapped. It neither reads nor
# writes `reg`'s slot: it scans the *other* still-staged entries of `env` for
# a `LocalExpr(reg)` that a pending write would invalidate. Its `reg` is
# always the register `force_materialize` is about to write and has already
# recorded, so wrapping it would double-count, not add coverage.
_UNWRAPPED_BY_DESIGN = frozenset({"_refuse_stale_reference"})

# `_consume_open(start)` is not in either set: its parameter is a range start
# rather than a register, and every slot it reads goes through `_read_reg`.

# Opcodes whose effects row backs at least one checked touch on the corpus
# arm (measured M4 task 9: 32 of 38). Asserted as a lower bound, like the
# sibling gate's version: a bigger corpus is fine, a shrinking reach is not.
#
# `LOADNIL` is absent, and that is a corpus fact rather than a gap in the
# structured path: the whole 229-file corpus contains exactly ONE `LOADNIL`
# (in `snr_common.lua`), and the proto holding it is not among the ones
# `print_chunk` reaches. The synthetic arm covers it.
_CORPUS_REACHED = frozenset({
    Op.MOVE, Op.LOADK, Op.LOADBOOL, Op.GETUPVAL, Op.GETGLOBAL,
    Op.GETTABLE, Op.SETGLOBAL, Op.SETUPVAL, Op.SETTABLE, Op.NEWTABLE,
    Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.LEN, Op.CONCAT, Op.JMP,
    Op.EQ, Op.LT, Op.LE, Op.TEST, Op.TESTSET, Op.CALL, Op.TAILCALL,
    Op.RETURN, Op.FORLOOP, Op.FORPREP, Op.TFORLOOP, Op.SETLIST, Op.CLOSURE,
    Op.VARARG,
})

# The synthetic arm's reach (measured: 33 of 38). Five opcodes are outside
# what a `Reconstructor`-level driver can reach at all:
#   - `JMP`/`CLOSE`: not reconstructible by the structured path (module
#     docstring). `JMP` still shows up on the corpus arm because it sits
#     inside the claimed-pc set of `If`/`While` region frames.
#   - `FORPREP`/`FORLOOP`/`TFORLOOP`: reached only through the *printer*'s
#     `NumericFor`/`GenericFor` arms, which need a whole SIR region tree and
#     a Reconstructor already holding the header's staged temps. The corpus
#     arm reaches all three.
_SYNTH_UNREACHABLE = frozenset({Op.JMP, Op.CLOSE, Op.FORPREP, Op.FORLOOP,
                                Op.TFORLOOP})

# `CLOSE` is the single opcode neither arm reaches, and it cannot be: the
# structured reconstructor refuses it outright, so a proto containing one
# never produces structured output at all.
_UNREACHABLE_BY_BOTH_ARMS = frozenset({Op.CLOSE})


# ------------------------------------------------------------------ corpus arm
@pytest.fixture(scope="module")
def corpus_scan(corpus_dir):
    """One instrumented `print_chunk` pass over the whole corpus.

    Module-scoped for the same reason the sibling gate's is: several
    assertions below read the same walk, and re-walking 229 files per
    assertion would put this gate on the suite's critical path.
    """
    from pyluadec.ingest import load_file

    rec = _Recorder()
    t0 = time.perf_counter()
    chunks = 0
    files = 0
    with instrumented(rec):
        for f in sorted(corpus_dir.glob("*.lua")):
            files += 1
            if _lua_mod.print_chunk(load_file(f)) is not None:
                chunks += 1
    return {"rec": rec, "files": files, "chunks": chunks,
            "seconds": time.perf_counter() - t0}


def test_effects_cover_every_register_the_structured_path_touches(corpus_scan):
    """The headline invariant, over every corpus proto the printer reaches.

    A violation here is a REAL BUG on one side or the other: either
    `reconstruct.py`/`emit/lua.py` decoded an operand `lvm.c` does not give
    that opcode, or `effects.py` omits a register the VM really touches.
    Adjudicate against `vendor/lua-5.1/src/lvm.c` and fix the wrong side --
    the assertion is not relaxable.
    """
    rec = corpus_scan["rec"]
    assert not rec.violations, (
        f"{len(rec.violations)} effects/reconstructor disagreements:\n"
        + "\n".join(rec.violations[:20]))


def test_the_corpus_arm_actually_walked_the_corpus(corpus_scan):
    """Collapse guard: floors well below the measured values.

    Measured M4 task 9: 229 files, 213 chunks printed, 1821 proto bodies
    entered, 423336 accessor touches, 12118 printed names. The floors sit far
    below those so they fail on a collapse (an exception swallowed, a corpus
    that stopped loading, a shim that stopped being installed) rather than on
    ordinary drift.
    """
    rec = corpus_scan["rec"]
    assert corpus_scan["files"] == 229, corpus_scan["files"]
    assert corpus_scan["chunks"] > 150, corpus_scan["chunks"]
    assert rec.functions > 1_000, rec.functions
    assert rec.acc_touches > 300_000, rec.acc_touches
    assert rec.printed > 8_000, rec.printed


def test_the_corpus_arm_reaches_the_opcodes_it_claims_to(corpus_scan):
    """Reach pin. `acc_touches > 300_000` alone would stay green if a whole
    opcode family stopped being reached -- `LOADK` and `MOVE` dominate the
    count, so it is a poor proxy for coverage. Same discipline as the sibling
    gate's `_CORPUS_CHECKED_OPCODES`.
    """
    missing = _CORPUS_REACHED - corpus_scan["rec"].ops
    assert not missing, sorted(op.name for op in missing)


def test_the_printer_arm_is_not_carried_entirely_by_arm_one(corpus_scan):
    """Arm 2's *second* disjunct must be load-bearing.

    If every printed register were already reconciled by Arm 1, the
    `reg in fr.covered` branch would be dead and the printer's own three
    register decodes (`NumericFor` `A+3`, `GenericFor` `A+3+i`, a `CLOSURE`'s
    captured `ps.b`) would be unchecked by anything. Measured: 21 of the 12118
    printed names on this corpus reach text without any reconstructor accessor
    having touched them first.
    """
    rec = corpus_scan["rec"]
    assert rec.printed_via_frame > 0, rec.printed_via_frame
    assert rec.printed_via_arm1 > 0, rec.printed_via_arm1
    assert rec.printed_via_arm1 + rec.printed_via_frame == rec.printed


def test_parameter_names_are_the_only_cross_depth_names(corpus_scan):
    """The one documented exclusion is exercised and stays bounded.

    `Printer.closure_parts` names the callee's parameter slots at
    `depth + 1`. That exclusion is not open-ended: each such name must be a
    register below the callee's `numparams`, and a violation is recorded
    otherwise (there are none -- see the headline test).
    """
    assert corpus_scan["rec"].params_named > 500, corpus_scan["rec"].params_named


def test_the_open_region_allowance_is_load_bearing(corpus_scan):
    """The `>= ri.a` allowance for open rows is used, and is not a blanket.

    1697 of the corpus arm's 423336 accessor touches are accepted only by it
    -- `_consume_open` indexing the fixed slots below a staged open producer's
    base. Pinned so the allowance cannot quietly become dead (which would mean
    the reconstructor stopped reading open ranges) and so its size stays
    visible: it excuses 0.4% of touches, not the gate.
    """
    rec = corpus_scan["rec"]
    assert rec.open_excused > 100, rec.open_excused
    assert rec.open_excused < rec.acc_touches // 50, (rec.open_excused,
                                                      rec.acc_touches)


def test_the_gate_stays_inside_its_time_budget(corpus_scan):
    """Standing directive: a slow suite blocks development.

    Measured ~2.0s for the whole instrumented corpus pass against a 3s
    budget. Asserted at 6s -- loose enough not to flake on a loaded machine,
    tight enough that an accidental quadratic (a per-touch corpus rescan, a
    frame built per register instead of per instruction) fails here.
    """
    assert corpus_scan["seconds"] < 6.0, corpus_scan["seconds"]


# --------------------------------------------------------------- synthetic arm
class _ConstPool:
    """An unbounded constant pool for the synthetic grid.

    The grid's `B`/`C` values encode `Bx` up to 262143, so a real tuple would
    have to be that long. Only `__getitem__` is ever used. Alternating bytes
    and a float keeps both of `SELF`'s branches (constant method name vs
    dynamic key) reachable.
    """

    def __getitem__(self, i):
        if i < 0:
            raise IndexError(i)
        return b"k" if i % 2 == 0 else 1.0


_GRID_PROTO = dataclasses.replace(mk_proto((0,), maxstacksize=255),
                                  constants=_ConstPool())
_GRID_RC = RegClass(locals=frozenset(), temps=frozenset(),
                    loop_vars=frozenset())


def _synthetic_fn(ri, fx=None) -> LirFunction:
    """A one-instruction `LirFunction` carrying `ri` and its real effects row."""
    li = LirInstr(ri=ri, effects=fx if fx is not None
                  else analyze(ri, EffectMode.STRICT),
                  successors=(), consumed=())
    return LirFunction(proto=_GRID_PROTO, instrs={ri.pc: li}, n_pcs=1,
                       captured_regs=frozenset(), closure_pseudo={})


# Operand shapes the grid produces but luac never would (a CONCAT with B > C,
# a SETLIST whose extra word is missing, an open form with no staged producer)
# make the reconstructor refuse. That is fine and is not swallowed evidence:
# every touch is checked at the moment it happens, so a refusal only ends a
# row early, it never hides a violation the row already committed.
_EXPECTED_REFUSALS = (ReconstructError, IndexError)


def _drive_grid(rec: _Recorder) -> int:
    rows = 0
    with instrumented(rec), rec.function_frame(0):
        for ri in _grid_instrs():
            fn = _synthetic_fn(ri)
            li = fn.instrs[ri.pc]
            r = Reconstructor(fn, _GRID_RC, 0)
            rows += 1
            try:
                r.stmts_for((li,))
            except _EXPECTED_REFUSALS:
                pass
            try:
                r.condition_expr(li)
            except _EXPECTED_REFUSALS:
                pass
            if ri.op is Op.TESTSET:
                alt = VAlt(staging=(), gate=None, gate_jmp_pc=None,
                           inner_staging=(), test=li, test_jmp_pc=ri.pc + 1,
                           rest=VTail(()))
                try:
                    r._tested_value(alt, (), ri.a)
                except _EXPECTED_REFUSALS:
                    pass
    return rows


@pytest.fixture(scope="module")
def grid_scan():
    rec = _Recorder()
    t0 = time.perf_counter()
    rows = _drive_grid(rec)
    return {"rec": rec, "rows": rows, "seconds": time.perf_counter() - t0}


def test_effects_cover_the_reconstructor_over_a_synthetic_operand_grid(grid_scan):
    """The same invariant over the sibling gate's operand grid.

    The corpus contains no `SELF`, `POW`, `UNM` or `NOT` at all, so the corpus
    arm cannot speak for those rows. Driving `Reconstructor` directly on
    hand-built instructions can: its operand decoding is a pure function of
    the decoded fields, so a word built by `tests/synth.mk_instr` exercises
    exactly the same code path a real one would.
    """
    rec = grid_scan["rec"]
    assert not rec.violations, (
        f"{len(rec.violations)} disagreements:\n" + "\n".join(rec.violations[:20]))
    assert grid_scan["rows"] > 5_000, grid_scan["rows"]


def test_the_synthetic_arm_reaches_every_reconstructor_level_opcode(grid_scan):
    """33/38 -- see `_SYNTH_UNREACHABLE` for the five and why. Equality, not a
    lower bound: this is a closed grid, so a shrinking reach is always a
    regression and a growing one means the pin needs re-deriving.
    """
    assert grid_scan["rec"].ops == set(Op) - _SYNTH_UNREACHABLE, sorted(
        op.name for op in (set(Op) - _SYNTH_UNREACHABLE) ^ grid_scan["rec"].ops)


def test_the_two_arms_together_reach_37_of_38_opcodes(grid_scan, corpus_scan):
    """The combined reach, and the one hole, both pinned.

    This is the number that matters: neither arm alone speaks for the whole
    instruction set, and leaving that as folklore is how a gate quietly stops
    covering a family. `SELF`/`POW`/`UNM`/`NOT` (and, on this corpus,
    `LOADNIL`) come only from the grid; `JMP` and the three loop-control
    opcodes come only from the corpus; `CLOSE` comes from neither.
    """
    both = grid_scan["rec"].ops | corpus_scan["rec"].ops
    assert both == set(Op) - _UNREACHABLE_BY_BOTH_ARMS, sorted(
        op.name for op in (set(Op) - _UNREACHABLE_BY_BOTH_ARMS) ^ both)
    only_synth = {Op.SELF, Op.POW, Op.UNM, Op.NOT, Op.LOADNIL}
    assert only_synth <= grid_scan["rec"].ops
    assert not only_synth & corpus_scan["rec"].ops
    only_corpus = {Op.JMP, Op.FORPREP, Op.FORLOOP, Op.TFORLOOP}
    assert only_corpus <= corpus_scan["rec"].ops
    assert not only_corpus & grid_scan["rec"].ops


# ----------------------------------------------------------- non-vacuity arms
def test_every_register_accessor_of_the_reconstructor_is_wrapped():
    """Invariant 2 of the brief, mechanically: if `Reconstructor` grows a new
    way to touch a register slot, this fails rather than the gate silently
    narrowing what "touch" means.

    The pin is the set of methods taking a `reg`/`regs` first parameter. A new
    one must either be wrapped above or be deliberately added here with a
    reason.
    """
    import inspect

    reg_taking = set()
    for name, fn_ in vars(Reconstructor).items():
        if not callable(fn_) or name.startswith("__"):
            continue
        params = list(inspect.signature(fn_).parameters)[1:]
        if {"reg", "regs"} & set(params):
            reg_taking.add(name)
    assert reg_taking == _WRAPPED_ACCESSORS | _UNWRAPPED_BY_DESIGN, sorted(
        reg_taking ^ (_WRAPPED_ACCESSORS | _UNWRAPPED_BY_DESIGN))


def test_the_subset_check_is_not_vacuous_for_any_reached_opcode(grid_scan):
    """Every opcode the grid reaches produced at least one *checked* touch.

    `rec.ops` is only updated from inside `accessor()`/`named()`, after the
    touch counter, so an opcode appearing there cannot have been reached
    without a register having been compared against its row. This is the
    cheap guard against the failure mode this project has shipped before
    (`docs/runbooks/m3-backlog.md`, "Tests that could not fail at the end of
    M2"): a branch that stops touching registers passes a subset check
    forever, because the empty set is a subset of everything.
    """
    assert grid_scan["rec"].acc_touches > 5_000, grid_scan["rec"].acc_touches
    assert len(grid_scan["rec"].ops) == 33, sorted(
        op.name for op in grid_scan["rec"].ops)


def test_a_dropped_effects_row_entry_is_caught():
    """Fault injection for Arm 1: the assertion has teeth.

    Removes one register from a real row's `reads`/`writes` and confirms the
    recorder reports it. Without this, a genuinely incomplete effects row
    could pass the gate and the gate would be decoration.
    """
    ri = mk_instr(Op.GETTABLE, a=1, b=2, c=3, pc=1)
    honest = analyze(ri, EffectMode.STRICT)

    clean = _Recorder()
    with instrumented(clean), clean.function_frame(0):
        fn = _synthetic_fn(ri, honest)
        Reconstructor(fn, _GRID_RC, 0).stmts_for((fn.instrs[1],))
    assert not clean.violations, clean.violations
    assert clean.acc_touches >= 3, clean.acc_touches

    for drop in sorted(honest.reads | honest.writes):
        broken = dataclasses.replace(honest, reads=honest.reads - {drop},
                                     writes=honest.writes - {drop})
        rec = _Recorder()
        with instrumented(rec), rec.function_frame(0):
            fn = _synthetic_fn(ri, broken)
            Reconstructor(fn, _GRID_RC, 0).stmts_for((fn.instrs[1],))
        assert rec.violations, (
            f"dropping R{drop} from GETTABLE's effects row went undetected; "
            "the subset check is not load-bearing for it")


def test_a_dropped_effects_row_entry_is_caught_on_the_printer_arm(
        compile_lua, monkeypatch):
    """Fault injection for Arm 2, end to end through the real printer.

    `NumericFor`'s loop-variable register `A+3` is decoded by `emit/lua.py`
    itself and reaches text through `name_for` without any reconstructor
    accessor seeing it -- it is precisely the touch Arm 1 cannot cover. Drop
    `A+3` from `FORLOOP`'s `writes` and the printed `for l0_3 = ...` must be
    reported.

    Compiled with `luac_sz4` from real source rather than hand-built, so the
    shape being checked is one luac actually emits.

    The neutering patches `pyluadec.lift.lift.analyze`, not
    `pyluadec.lift.effects.analyze`: `lift.py` binds the name at import
    (`from .effects import ... analyze ...`), so patching the defining module
    is a no-op -- a mistake this test made in its first draft and which made
    the injection silently pass.
    """
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift as lift_mod

    path = compile_lua("luac_sz4", "for i = 1, 3 do print(i) end\n")

    clean = _Recorder()
    with instrumented(clean):
        assert _lua_mod.print_chunk(load_file(path)) is not None
    assert not clean.violations, clean.violations
    assert clean.printed_via_frame > 0, "FORLOOP's A+3 was already in Arm 1"

    real_analyze = lift_mod.analyze

    def neutered(ri, mode):
        fx = real_analyze(ri, mode)
        if ri.op is Op.FORLOOP:
            fx = dataclasses.replace(fx, writes=fx.writes - {ri.a + 3})
        return fx

    rec = _Recorder()
    monkeypatch.setattr(lift_mod, "analyze", neutered)
    with instrumented(rec):
        printed = _lua_mod.print_chunk(load_file(path))
    # If this ever fails, check `printed` first: a future change could make the
    # neutered row refuse *structurally* (no output at all), which would also
    # produce no violation but for an unrelated reason.
    assert printed is not None, "neutered run refused before it could print"
    assert rec.violations, (
        "dropping FORLOOP's loop-variable write went undetected; the printer "
        "arm is not load-bearing")
    assert any("printed name" in v for v in rec.violations), rec.violations


def test_the_recorder_reports_an_unattributable_touch():
    """The "no active scope" arms of `accessor`/`named` are real refusals, not
    silent passes.

    If a future accessor or `name_for` call happens outside every attribution
    scope -- the exact way this instrumentation could go quietly blind -- the
    touch is reported rather than dropped. Exercised directly because no
    current code path reaches it (measured: 0 on the corpus and on the grid).
    """
    rec = _Recorder()
    rec.accessor(7, "read")
    assert rec.violations and "unattributable" in rec.violations[0]

    rec2 = _Recorder()
    with rec2.function_frame(0):
        rec2.accessor(7, "read")            # barrier frame is not a scope
    assert rec2.violations and "unattributable" in rec2.violations[0]

    rec3 = _Recorder()
    rec3.named(7, 0)
    assert rec3.violations and "unattributable" in rec3.violations[0]

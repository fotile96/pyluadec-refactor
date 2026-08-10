"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

import bisect
from dataclasses import dataclass

from pyluadec.lift.effects import Effect
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import Op

from pyluadec.lift import LUA_KEYWORDS


@dataclass(frozen=True)
class RegClass:
    """Local/temp/loop-var partition of a function's registers.

    Only covers registers with at least one *tracked* (explicit, present in
    an instruction's .writes/.reads) def or use. A register classify_registers
    never sees at all -- dead stack space that is never written or read, or a
    register touched only implicitly by an open-region read/write outside any
    candidate's own def/use window -- appears in none of locals/temps/
    loop_vars. Callers must not assume every register in
    range(fn.proto.maxstacksize) is classified; a register missing from all
    three sets is untracked, not "temp by default."

    Modeling limitation: this is a whole-function, per-register-*number*
    classification, but luac freely reuses a register number for different,
    lexically disjoint local variables across a single function (once one
    variable's scope ends, the compiler is free to hand that slot to the
    next). classify_registers has no live-range/scope model, so any verdict
    it gives is necessarily an approximation for a register reused this way
    -- the `controls` handling below is the one place this project has
    already had to correct for it (a register can be a control slot for one
    loop's range and an ordinary, multiply-written/read local everywhere
    else in the same function; see that code's comment). A future
    consumer that needs more precision than "one verdict per register
    number for the whole function" will need actual live-range analysis,
    which this module does not attempt (M3 task-5 round-2 review).
    """
    locals: frozenset[int]
    temps: frozenset[int]
    loop_vars: frozenset[int]    # declared by the for statement itself, never by LocalDecl


def name_for(reg: int, depth: int) -> str:
    n = f"l{depth}_{reg}"
    assert n.isidentifier() and n not in LUA_KEYWORDS and not n.startswith("__pld_")
    return n


def classify_registers(fn: LirFunction) -> RegClass:
    defs: dict[int, list[int]] = {}
    uses: dict[int, list[int]] = {}
    ordered = sorted(fn.instrs)
    for pc in ordered:
        li = fn.instrs[pc]
        for r in li.effects.writes:
            defs.setdefault(r, []).append(pc)
        for r in li.effects.reads:
            uses.setdefault(r, []).append(pc)
    controls: set[int] = set()
    loop_vars: set[int] = set()
    control_pcs: set[int] = set()             # pcs of FORPREP/FORLOOP/TFORLOOP themselves
    claims: dict[int, set[int]] = {}          # register -> control_pcs that claim it
    for pc in ordered:
        ri = fn.instrs[pc].ri
        if ri.op in (Op.FORPREP, Op.FORLOOP):
            for r in (ri.a, ri.a + 1, ri.a + 2):
                claims.setdefault(r, set()).add(pc)
            controls |= {ri.a, ri.a + 1, ri.a + 2}
            loop_vars.add(ri.a + 3)
            control_pcs.add(pc)
        elif ri.op is Op.TFORLOOP:
            for r in (ri.a, ri.a + 1, ri.a + 2):
                claims.setdefault(r, set()).add(pc)
            controls |= {ri.a, ri.a + 1, ri.a + 2}
            loop_vars |= set(range(ri.a + 3, ri.a + 3 + ri.c))
            control_pcs.add(pc)
    control_pcs_sorted = sorted(control_pcs)

    def _window_start(cp: int) -> int:
        """The pc of the control_pc immediately preceding cp in the whole
        function (of any loop, not just ones sharing a register with cp),
        or 0 if cp is the first. The open lower bound of cp's staging
        window: nothing before the previous loop ended could plausibly be
        staging for this one.
        """
        i = bisect.bisect_left(control_pcs_sorted, cp)
        return control_pcs_sorted[i - 1] if i > 0 else 0

    def _staging_window_ok(r: int) -> bool:
        """True iff every def/use of r *outside* the FORPREP/FORLOOP/TFORLOOP
        instructions that claim it falls in the staging window immediately
        before one of those claiming instructions.

        `controls` is accumulated over EVERY FORPREP/FORLOOP/TFORLOOP in the
        function, purely by register number -- it says nothing about whether
        THIS register is genuinely dedicated to being some loop's control
        slot, or whether luac later reused the same number for a completely
        unrelated, ordinary local (round-2 review: measured 188/188
        controls-forced registers on the corpus that the ordinary def/use
        rules below would have classified local -- register 0 in one file
        alone had hundreds of ordinary defs/uses spread across the whole
        function, entirely unrelated to any loop).

        A plain "exactly one def, exactly one use" count (as used for
        ordinary temps below) cannot be applied directly here: a genuinely
        dedicated control register still has MULTIPLE tracked defs/uses of
        its own even with control_pcs excluded. FORPREP and FORLOOP (for the
        same loop) both claim their registers, but only FORPREP is a
        control_pc that also *writes* a's/a+1's/a+2's staged values in one
        step; the real complication is TFORLOOP's iterator/state registers,
        whose staging CALL (e.g. `pairs(t)`) both reads its own base
        register (the callee) and overwrites it with its own first result --
        one non-control-pc instruction contributing to both an extra def
        AND an extra use of the same register, entirely legitimately.

        What actually distinguishes "legitimately staging for this loop"
        from "reused for something else" is not a count but *where*: every
        extra activity pc must land strictly between the previous
        control_pc in the whole function (of any loop, 0 if none) and some
        control_pc that claims r -- i.e. in the gap since the last loop
        ended, leading directly into this one. Anything outside every such
        window is provably unrelated reuse and must be local -- being wrong
        toward local costs a certification failure; being wrong toward temp
        risks inlining a popped or clobbered value.
        """
        extra = sorted(
            {pc for pc in defs.get(r, []) if pc not in control_pcs}
            | {pc for pc in uses.get(r, []) if pc not in control_pcs})
        if not extra:
            return True
        for pc in extra:
            if not any(_window_start(cp) < pc < cp
                       for cp in claims.get(r, ()) if pc < cp):
                return False
        return True

    regs = set(defs) | set(uses) | controls | loop_vars
    locals_: set[int] = set()
    temps: set[int] = set()
    for r in sorted(regs):
        if r in controls:
            if _staging_window_ok(r):
                temps.add(r)
            else:
                locals_.add(r)
            continue
        if r in loop_vars:
            locals_.add(r); continue
        if r < fn.proto.numparams or r in fn.captured_regs:
            locals_.add(r); continue
        d, u = defs.get(r, []), uses.get(r, [])
        if len(d) != 1 or len(u) != 1:
            locals_.add(r); continue
        dp, up = d[0], u[0]
        if dp >= up or not _adjacent_pure(fn, r, dp, up, ordered):
            locals_.add(r); continue
        temps.add(r)
    return RegClass(locals=frozenset(locals_), temps=frozenset(temps),
                    loop_vars=frozenset(loop_vars))


def _adjacent_pure(fn: LirFunction, reg: int, dp: int, up: int, ordered) -> bool:
    """No open region through the use (inclusive), no write to reg's inputs,
    and no WRITE_HEAP/may_error strictly between the def and its use.

    Two different windows, deliberately:
      - The open-region check (reads_open/writes_open) scans (dp, up] --
        including the use instruction itself. An open WRITE at the very use
        pc (e.g. a CALL C==0 whose own execution both reads reg as an
        explicit argument and, via its open result-write, overwrites reg's
        slot with a return value right after) is a same-pc hazard a
        strictly-between scan cannot see -- this is the
        print(string.format(...)) corpus case (M3 task-4 round-2 review).
        Checked without regard to which specific registers the open region
        touches: its affected range has a known base but an unbounded top,
        so this function cannot prove reg falls outside it. This check is
        NOT scoped to any wider range than a single candidate's own (dp, up]
        window -- unlike an earlier version of this function, it must never
        disqualify a register for an open-region instruction that has
        nothing to do with that register's own def/use pair (see round-2
        review: over-broad global open-region bookkeeping had flipped 154 of
        342 registers to local for zero soundness gain, verified on the
        229-file corpus).
      - The other barriers (a write to one of the def's own inputs, or an
        intervening WRITE_HEAP-effect/may_error instruction) are checked
        over the strictly-between window (dp, up), as before: they are
        about what happens *before* reg is consumed, not about the
        consuming instruction's own other effects.
    """
    dli = fn.instrs[dp]
    inputs = set(dli.effects.reads)
    for pc in ordered:
        if not (dp < pc <= up):
            continue
        li = fn.instrs[pc]
        if li.effects.reads_open or li.effects.writes_open:
            return False
        if pc == up:
            continue
        if li.effects.writes & inputs:
            return False
        if li.effects.effect >= Effect.WRITE_HEAP or li.effects.may_error:
            return False
    return True

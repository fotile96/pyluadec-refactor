"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

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
    for pc in ordered:
        ri = fn.instrs[pc].ri
        if ri.op in (Op.FORPREP, Op.FORLOOP):
            controls |= {ri.a, ri.a + 1, ri.a + 2}
            loop_vars.add(ri.a + 3)
        elif ri.op is Op.TFORLOOP:
            controls |= {ri.a, ri.a + 1, ri.a + 2}
            loop_vars |= set(range(ri.a + 3, ri.a + 3 + ri.c))
    regs = set(defs) | set(uses) | controls | loop_vars
    locals_: set[int] = set()
    temps: set[int] = set()
    for r in sorted(regs):
        if r in controls:
            temps.add(r); continue
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

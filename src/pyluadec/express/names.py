"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.lift.effects import Effect
from pyluadec.lift.lift import LirFunction

from pyluadec.lift import LUA_KEYWORDS


@dataclass(frozen=True)
class RegClass:
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
    from pyluadec.lift.opcodes import Op
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
    """No write to reg's inputs and no WRITE_HEAP/may_error between the def and its use."""
    dli = fn.instrs[dp]
    inputs = set(dli.effects.reads)
    for pc in ordered:
        if not (dp < pc < up):
            continue
        li = fn.instrs[pc]
        if li.effects.writes & inputs:
            return False
        if li.effects.effect >= Effect.WRITE_HEAP or li.effects.may_error:
            return False
    return True

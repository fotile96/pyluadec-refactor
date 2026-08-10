"""Register classification (local vs inlinable temp) + local name synthesis (spec §4)."""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.lift.effects import Effect
from pyluadec.lift.lift import LirFunction
from pyluadec.lift.opcodes import Op, RawInstr

from pyluadec.lift import LUA_KEYWORDS


@dataclass(frozen=True)
class RegClass:
    """Local/temp/loop-var partition of a function's registers.

    Only covers registers with at least one *tracked* def or use -- either an
    explicit one (present in an instruction's .writes/.reads) or one
    conservatively synthesized from an open-region read/write (see
    classify_registers). A register classify_registers never sees at all --
    dead stack space that is never written or read, explicitly or via an
    open region -- appears in none of locals/temps/loop_vars. Callers must
    not assume every register in range(fn.proto.maxstacksize) is classified;
    a register missing from all three sets is untracked, not "temp by
    default."
    """
    locals: frozenset[int]
    temps: frozenset[int]
    loop_vars: frozenset[int]    # declared by the for statement itself, never by LocalDecl


def name_for(reg: int, depth: int) -> str:
    n = f"l{depth}_{reg}"
    assert n.isidentifier() and n not in LUA_KEYWORDS and not n.startswith("__pld_")
    return n


def _open_region_base(ri: RawInstr, *, is_write: bool) -> int:
    """First register touched by ri's open (statically-unbounded) read/write range.

    Open regions are R[base..top) where top is a dynamic stack depth this
    module does not simulate -- base is always known from the instruction's
    own fields, though. Callers pair this with fn.proto.maxstacksize as a
    sound (if coarse) upper bound on top: real "top" is always <=
    maxstacksize, so treating every register in [base, maxstacksize) as
    possibly touched is a safe over-approximation, never an under-approximation.
    """
    if ri.op is Op.VARARG:                        # writes R(A..top)
        return ri.a
    if ri.op in (Op.CALL, Op.TAILCALL):
        return ri.a if is_write else ri.a + 1      # writes R(A..): results; reads R(A+1..): args
    if ri.op is Op.RETURN:                         # reads R(A..top)
        return ri.a
    if ri.op is Op.SETLIST:                        # reads R(A+1..top): values to insert
        return ri.a + 1
    raise AssertionError(f"unexpected open-region opcode {ri.op!r}")


def classify_registers(fn: LirFunction) -> RegClass:
    defs: dict[int, list[int]] = {}
    uses: dict[int, list[int]] = {}
    ordered = sorted(fn.instrs)
    top = fn.proto.maxstacksize
    for pc in ordered:
        li = fn.instrs[pc]
        for r in li.effects.writes:
            defs.setdefault(r, []).append(pc)
        for r in li.effects.reads:
            uses.setdefault(r, []).append(pc)
        # Open regions (R[base..top)) are not statically bounded, so they
        # never appear in .writes/.reads at all -- an instruction with
        # writes_open/reads_open can silently def or use any register from
        # its base up to the function's maxstacksize (VARARG B==0; CALL
        # C==0 on the write side; CALL/TAILCALL/RETURN/SETLIST B==0 on the
        # read side). A register that could be touched this way must not be
        # treated as single-def/single-use: the single-use/single-def
        # precondition below cannot be established for it, and the safe
        # answer when a precondition can't be established is to refuse and
        # classify local. Materializing conservative def/use entries here
        # (instead of only guarding _adjacent_pure) makes that refusal fall
        # out of the existing len(d) != 1 / len(u) != 1 checks for free, not
        # just for candidates whose open-region instruction happens to land
        # strictly between a def and its use.
        if li.effects.writes_open:
            for r in range(_open_region_base(li.ri, is_write=True), top):
                defs.setdefault(r, []).append(pc)
        if li.effects.reads_open:
            for r in range(_open_region_base(li.ri, is_write=False), top):
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
    """No write to reg's inputs, no open region, and no WRITE_HEAP/may_error
    between the def and its use.

    Open regions (reads_open/writes_open) are an unconditional barrier here
    regardless of which specific registers they touch: their affected range
    is not statically bounded (see _open_region_base), so this function
    cannot prove reg falls outside it. This is defense in depth on top of
    the conservative defs/uses entries classify_registers already adds for
    open regions -- it also catches an open-region instruction that sits
    between dp and up but, for whatever reason, was not attributed a def/use
    entry for reg specifically.
    """
    dli = fn.instrs[dp]
    inputs = set(dli.effects.reads)
    for pc in ordered:
        if not (dp < pc < up):
            continue
        li = fn.instrs[pc]
        if li.effects.reads_open or li.effects.writes_open:
            return False
        if li.effects.writes & inputs:
            return False
        if li.effects.effect >= Effect.WRITE_HEAP or li.effects.may_error:
            return False
    return True

"""Proto → LIR：解码 + 效应标注 + 伪指令消耗。零聪明处理，纯结构化转录。"""
from __future__ import annotations

from dataclasses import dataclass, replace

from pyluadec.ingest.proto import Proto

from .effects import EffectMode, InstrEffects, analyze, extra_words, successors
from .opcodes import Op, RawInstr, decode


class LiftError(Exception):
    pass


@dataclass(frozen=True)
class LirInstr:
    ri: RawInstr
    effects: InstrEffects
    successors: tuple[int, ...]
    consumed: tuple[int, ...]


@dataclass(frozen=True)
class LirFunction:
    proto: Proto
    instrs: dict[int, LirInstr]
    n_pcs: int
    captured_regs: frozenset[int]
    closure_pseudo: dict[int, tuple[RawInstr, ...]]


def lift_proto(p: Proto, mode: EffectMode = EffectMode.STRICT) -> LirFunction:
    n = len(p.code)
    if n == 0:
        raise LiftError("empty code array")
    instrs: dict[int, LirInstr] = {}
    closure_pseudo: dict[int, tuple[RawInstr, ...]] = {}
    captured: set[int] = set()
    pc = 1
    while pc <= n:
        ri = decode(p.code[pc - 1], pc=pc)
        nups = None
        if ri.op is Op.CLOSURE:
            if not (0 <= ri.bx < len(p.subprotos)):
                raise LiftError(f"pc {pc}: CLOSURE Bx={ri.bx} out of range")
            nups = p.subprotos[ri.bx].nups
        n_extra = extra_words(ri, nups)
        if pc + n_extra > n:
            raise LiftError(f"pc {pc}: {ri.op.name} consumes past end of code")
        consumed = tuple(range(pc + 1, pc + 1 + n_extra))
        fx = analyze(ri, mode)
        if ri.op is Op.CLOSURE:
            pseudo = tuple(decode(p.code[q - 1], pc=q) for q in consumed)
            for ps in pseudo:
                if ps.op not in (Op.MOVE, Op.GETUPVAL):
                    raise LiftError(
                        f"pc {ps.pc}: CLOSURE pseudo-instruction is {ps.op.name}, "
                        "expected MOVE/GETUPVAL")
            closure_pseudo[pc] = pseudo
            moved = frozenset(ps.b for ps in pseudo if ps.op is Op.MOVE)
            captured.update(moved)
            fx = replace(fx, reads=fx.reads | moved)
        succ = successors(ri, nups)
        for s in succ:
            if not (1 <= s <= n):
                raise LiftError(f"pc {pc}: successor {s} out of range 1..{n}")
        instrs[pc] = LirInstr(ri=ri, effects=fx, successors=succ, consumed=consumed)
        pc += 1 + n_extra
    return LirFunction(
        proto=p, instrs=instrs, n_pcs=n,
        captured_regs=frozenset(captured), closure_pseudo=closure_pseudo)

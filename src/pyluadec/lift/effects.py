"""Per-opcode effect table — the project's axiom layer (spec §3 layer 2).

一切上层（内联门、pass 验证、fallback 发射）共享此处结论。改动本文件 = 改动公理，
必须同步 no-frills PDF / lvm.c 依据并跑全部差分测试。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

from .opcodes import Op, RawInstr, indexk, isk


class Effect(IntEnum):
    PURE = 0
    READ_HEAP = 1
    WRITE_HEAP = 2
    ARBITRARY = 3


class EffectMode(Enum):
    STRICT = "strict"                 # 任何表访问/算术都可能触发元方法
    NO_METAMETHOD = "no_metamethod"   # 假设语料不依赖元方法的副作用
    TRUSTING = "trusting"             # 进一步假设表读取可自由重排


@dataclass(frozen=True)
class InstrEffects:
    reads: frozenset[int]
    writes: frozenset[int]
    reads_open: bool      # 额外读 R[base..top-1]（CALL B==0 / RETURN B==0 / SETLIST B==0）
    writes_open: bool     # 额外写 R[base..top-1]（CALL C==0 / VARARG B==0）
    effect: Effect
    may_error: bool       # NO_METAMETHOD 假设下仍可能抛错


def _rk(x: int) -> frozenset[int]:
    return frozenset() if isk(x) else frozenset({x})


# 每项: (reads, writes, reads_open, writes_open,
#        effect@STRICT, effect@NO_METAMETHOD, effect@TRUSTING, may_error)
def _row(ri: RawInstr):
    op, a, b, c = ri.op, ri.a, ri.b, ri.c
    F = frozenset
    P, RH, WH, ARB = Effect.PURE, Effect.READ_HEAP, Effect.WRITE_HEAP, Effect.ARBITRARY
    if op is Op.MOVE:
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op in (Op.LOADK, Op.NEWTABLE):
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.LOADBOOL:
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.LOADNIL:
        return F(), F(range(a, b + 1)), 0, 0, P, P, P, False
    if op is Op.GETUPVAL:
        return F(), F({a}), 0, 0, RH, RH, RH, False
    if op is Op.SETUPVAL:
        return F({a}), F(), 0, 0, WH, WH, WH, False
    if op is Op.GETGLOBAL:
        return F(), F({a}), 0, 0, ARB, RH, P, False
    if op is Op.GETTABLE:
        return F({b}) | _rk(c), F({a}), 0, 0, ARB, RH, P, True
    if op is Op.SELF:
        return F({b}) | _rk(c), F({a, a + 1}), 0, 0, ARB, RH, P, True
    if op is Op.SETGLOBAL:
        return F({a}), F(), 0, 0, ARB, WH, WH, False
    if op is Op.SETTABLE:
        return F({a}) | _rk(b) | _rk(c), F(), 0, 0, ARB, WH, WH, True
    if op is Op.SETLIST:
        reads = F({a}) | (F(range(a + 1, a + b + 1)) if b else F())
        return reads, F(), b == 0, 0, ARB, WH, WH, True
    if op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
        return _rk(b) | _rk(c), F({a}), 0, 0, ARB, P, P, True
    if op in (Op.UNM, Op.LEN):
        return F({b}), F({a}), 0, 0, ARB, P, P, True
    if op is Op.NOT:
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op is Op.CONCAT:
        return F(range(b, c + 1)), F({a}), 0, 0, ARB, P, P, True
    if op is Op.JMP:
        return F(), F(), 0, 0, P, P, P, False
    if op is Op.EQ:
        return _rk(b) | _rk(c), F(), 0, 0, ARB, P, P, False
    if op in (Op.LT, Op.LE):
        return _rk(b) | _rk(c), F(), 0, 0, ARB, P, P, True
    if op is Op.TEST:
        return F({a}), F(), 0, 0, P, P, P, False
    if op is Op.TESTSET:
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op in (Op.CALL, Op.TAILCALL):
        reads = F({a}) | (F(range(a + 1, a + b)) if b else F())
        if op is Op.TAILCALL:
            return reads, F(), b == 0, 0, ARB, ARB, ARB, True
        writes = F(range(a, a + c - 1)) if c else F()
        return reads, writes, b == 0, c == 0, ARB, ARB, ARB, True
    if op is Op.RETURN:
        return (F(range(a, a + b - 1)) if b else F()), F(), b == 0, 0, P, P, P, False
    if op is Op.FORPREP:
        return F({a, a + 1, a + 2}), F({a, a + 1, a + 2}), 0, 0, P, P, P, True
    if op is Op.FORLOOP:
        return F({a, a + 1, a + 2}), F({a, a + 3}), 0, 0, P, P, P, True
    if op is Op.TFORLOOP:
        return F({a, a + 1, a + 2}), F({a + 2}) | F(range(a + 3, a + 3 + c)), 0, 0, ARB, ARB, ARB, True
    if op is Op.CLOSE:
        return F(), F(), 0, 0, WH, WH, WH, False
    if op is Op.CLOSURE:
        # 捕获寄存器的 reads 由 lift 层从 MOVE 伪指令补齐（此处不可见后续指令字）
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.VARARG:
        return F(), (F(range(a, a + b - 1)) if b else F()), 0, b == 0, P, P, P, False
    raise AssertionError(f"unhandled opcode {op!r}")


_MODE_COL = {EffectMode.STRICT: 4, EffectMode.NO_METAMETHOD: 5, EffectMode.TRUSTING: 6}


def analyze(ri: RawInstr, mode: EffectMode) -> InstrEffects:
    row = _row(ri)
    return InstrEffects(
        reads=row[0], writes=row[1],
        reads_open=bool(row[2]), writes_open=bool(row[3]),
        effect=row[_MODE_COL[mode]], may_error=row[7],
    )


def successors(ri: RawInstr, nups_of_closure: int | None = None) -> tuple[int, ...]:
    op, pc = ri.op, ri.pc
    if op in (Op.RETURN, Op.TAILCALL):
        return ()
    if op is Op.JMP or op is Op.FORPREP:
        return (pc + 1 + ri.sbx,)
    if op is Op.FORLOOP:
        return (pc + 1 + ri.sbx, pc + 1)
    if op in (Op.EQ, Op.LT, Op.LE, Op.TEST, Op.TESTSET, Op.TFORLOOP):
        return (pc + 1, pc + 2)
    if op is Op.LOADBOOL:
        return (pc + 2,) if ri.c else (pc + 1,)
    if op is Op.CLOSURE:
        if nups_of_closure is None:
            raise ValueError("successors(CLOSURE) requires nups_of_closure")
        return (pc + 1 + nups_of_closure,)
    if op is Op.SETLIST and ri.c == 0:
        return (pc + 2,)
    return (pc + 1,)


def extra_words(ri: RawInstr, nups_of_closure: int | None = None) -> int:
    if ri.op is Op.CLOSURE:
        if nups_of_closure is None:
            raise ValueError("extra_words(CLOSURE) requires nups_of_closure")
        return nups_of_closure
    if ri.op is Op.SETLIST and ri.c == 0:
        return 1
    return 0

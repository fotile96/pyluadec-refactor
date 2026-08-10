"""Lua 5.1 instruction decoding + per-opcode metadata (the axiom layer's ground truth).

Field layout (lopcodes.h): op:6 | A:8 | C:9 | B:9  (Bx = B..C 18 bits, sBx = Bx - 131071).
OP_SPECS 的 fmt/bmode/cmode 逐行转录自 vendor/lua-5.1/src/lopcodes.c 的 luaP_opmodes；
tests/test_opcodes.py 用 golden listing 全语料 21 万条指令核对该表的每一行。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class Op(IntEnum):
    MOVE = 0; LOADK = 1; LOADBOOL = 2; LOADNIL = 3; GETUPVAL = 4
    GETGLOBAL = 5; GETTABLE = 6; SETGLOBAL = 7; SETUPVAL = 8; SETTABLE = 9
    NEWTABLE = 10; SELF = 11; ADD = 12; SUB = 13; MUL = 14; DIV = 15
    MOD = 16; POW = 17; UNM = 18; NOT = 19; LEN = 20; CONCAT = 21
    JMP = 22; EQ = 23; LT = 24; LE = 25; TEST = 26; TESTSET = 27
    CALL = 28; TAILCALL = 29; RETURN = 30; FORLOOP = 31; FORPREP = 32
    TFORLOOP = 33; SETLIST = 34; CLOSE = 35; CLOSURE = 36; VARARG = 37


class Fmt(Enum):
    iABC = "iABC"; iABx = "iABx"; iAsBx = "iAsBx"


class ArgMode(Enum):
    N = "N"   # argument not used
    U = "U"   # used as plain value
    R = "R"   # register (or jump offset)
    K = "K"   # register/constant (RK) or constant index


@dataclass(frozen=True)
class OpSpec:
    fmt: Fmt
    bmode: ArgMode
    cmode: ArgMode


_A, _B, _X = Fmt.iABC, Fmt.iABx, Fmt.iAsBx
_N, _U, _R, _K = ArgMode.N, ArgMode.U, ArgMode.R, ArgMode.K

# 逐行对应 lopcodes.c luaP_opmodes（T/A 位与打印无关，不录）。
OP_SPECS: dict[Op, OpSpec] = {
    Op.MOVE: OpSpec(_A, _R, _N),      Op.LOADK: OpSpec(_B, _K, _N),
    Op.LOADBOOL: OpSpec(_A, _U, _U),  Op.LOADNIL: OpSpec(_A, _R, _N),
    Op.GETUPVAL: OpSpec(_A, _U, _N),  Op.GETGLOBAL: OpSpec(_B, _K, _N),
    Op.GETTABLE: OpSpec(_A, _R, _K),  Op.SETGLOBAL: OpSpec(_B, _K, _N),
    Op.SETUPVAL: OpSpec(_A, _U, _N),  Op.SETTABLE: OpSpec(_A, _K, _K),
    Op.NEWTABLE: OpSpec(_A, _U, _U),  Op.SELF: OpSpec(_A, _R, _K),
    Op.ADD: OpSpec(_A, _K, _K),       Op.SUB: OpSpec(_A, _K, _K),
    Op.MUL: OpSpec(_A, _K, _K),       Op.DIV: OpSpec(_A, _K, _K),
    Op.MOD: OpSpec(_A, _K, _K),       Op.POW: OpSpec(_A, _K, _K),
    Op.UNM: OpSpec(_A, _R, _N),       Op.NOT: OpSpec(_A, _R, _N),
    Op.LEN: OpSpec(_A, _R, _N),       Op.CONCAT: OpSpec(_A, _R, _R),
    Op.JMP: OpSpec(_X, _R, _N),       Op.EQ: OpSpec(_A, _K, _K),
    Op.LT: OpSpec(_A, _K, _K),        Op.LE: OpSpec(_A, _K, _K),
    Op.TEST: OpSpec(_A, _R, _U),      Op.TESTSET: OpSpec(_A, _R, _U),
    Op.CALL: OpSpec(_A, _U, _U),      Op.TAILCALL: OpSpec(_A, _U, _U),
    Op.RETURN: OpSpec(_A, _U, _N),    Op.FORLOOP: OpSpec(_X, _R, _N),
    Op.FORPREP: OpSpec(_X, _R, _N),   Op.TFORLOOP: OpSpec(_A, _N, _U),
    Op.SETLIST: OpSpec(_A, _U, _U),   Op.CLOSE: OpSpec(_A, _N, _N),
    Op.CLOSURE: OpSpec(_B, _U, _N),   Op.VARARG: OpSpec(_A, _U, _N),
}

BITRK = 1 << 8            # 256：operand 的 K 位
MAXARG_sBx = 131071       # (2^18 - 1) >> 1

LUA_KEYWORDS = frozenset(
    "and break do else elseif end false for function if in local nil not or "
    "repeat return then true until while".split())


class DecodeError(ValueError):
    pass


def isk(x: int) -> bool:
    return bool(x & BITRK)


def indexk(x: int) -> int:
    return x & ~BITRK


@dataclass(frozen=True)
class RawInstr:
    pc: int          # 1-based
    word: int
    op: Op
    a: int
    b: int
    c: int
    bx: int
    sbx: int


def decode(word: int, pc: int) -> RawInstr:
    opnum = word & 0x3F
    if opnum > 37:
        raise DecodeError(f"pc {pc}: invalid opcode {opnum} in word 0x{word:08x}")
    bx = (word >> 14) & 0x3FFFF
    return RawInstr(
        pc=pc, word=word, op=Op(opnum),
        a=(word >> 6) & 0xFF,
        c=(word >> 14) & 0x1FF,
        b=(word >> 23) & 0x1FF,
        bx=bx, sbx=bx - MAXARG_sBx,
    )


def luac_operand_str(ri: RawInstr) -> str:
    """复刻 print.c PrintCode 的操作数列（RK 常量打成 -1-index；JMP 只打 sBx）。"""
    spec = OP_SPECS[ri.op]
    if spec.fmt is Fmt.iABC:
        parts = [str(ri.a)]
        if spec.bmode is not ArgMode.N:
            parts.append(str(-1 - indexk(ri.b) if isk(ri.b) else ri.b))
        if spec.cmode is not ArgMode.N:
            parts.append(str(-1 - indexk(ri.c) if isk(ri.c) else ri.c))
        return " ".join(parts)
    if spec.fmt is Fmt.iABx:
        bx = -1 - ri.bx if spec.bmode is ArgMode.K else ri.bx
        return f"{ri.a} {bx}"
    # iAsBx
    if ri.op is Op.JMP:
        return str(ri.sbx)
    return f"{ri.a} {ri.sbx}"

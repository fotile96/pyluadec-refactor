"""Hand-built Proto/RawInstr/Cfg fixtures for testing shapes luac won't emit.

Instruction word layout (lopcodes.h): op:6 | A:8 | C:9 | B:9 ; Bx = bits 14..31.
"""
from __future__ import annotations

from pyluadec.cfg.blocks import BasicBlock, Cfg
from pyluadec.ingest.proto import Proto
from pyluadec.lift.opcodes import MAXARG_sBx, Op, RawInstr, decode


def _encode(op, a, b, c, bx, sbx) -> int:
    opn = int(op)
    if bx is not None:
        return opn | (a << 6) | (bx << 14)
    if sbx is not None:
        return opn | (a << 6) | ((sbx + MAXARG_sBx) << 14)
    return opn | (a << 6) | (c << 14) | (b << 23)


def mk_instr(op, a=0, b=0, c=0, *, bx=None, sbx=None, pc=1) -> RawInstr:
    return decode(_encode(op, a, b, c, bx, sbx), pc=pc)


def mk_proto(code_words, *, constants=(), numparams=0, is_vararg=0,
             maxstacksize=2, nups=0, subprotos=()) -> Proto:
    return Proto(
        source=None, linedefined=0, lastlinedefined=0, nups=nups,
        numparams=numparams, is_vararg=is_vararg, maxstacksize=maxstacksize,
        code=tuple(code_words), constants=tuple(constants), lineinfo=(),
        locvars=(), upvalues=tuple(None for _ in range(nups)),
        subprotos=tuple(subprotos))


def mk_cfg(edges: dict[int, tuple[int, ...]], entry: int = 1) -> Cfg:
    blocks = {s: BasicBlock(s, (), t) for s, t in edges.items()}
    preds: dict[int, list[int]] = {s: [] for s in edges}
    for s, ts in edges.items():
        for t in ts:
            preds[t].append(s)
    return Cfg(entry=entry, blocks=blocks,
               preds={k: tuple(sorted(v)) for k, v in preds.items()})

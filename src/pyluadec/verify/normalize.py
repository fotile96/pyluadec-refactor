"""L3 归一化比对器（spec §5）。

L3.0 = 严格逐字段相等（含 lineinfo/locvars —— 诚实的最严基线）。
L3.k = 依次应用 NORMALIZATIONS[:k] 后比较；每级归一化必须单独论证健全性
（spec §9 R3），并 bump LADDER_VERSION。

阶梯现状（M3）：一级 `strip-lineinfo`，`LADDER_VERSION = "l3-ladder-v1"`。
该级的健全性论证与 `_strip_lineinfo` 本体同处一地（见其 docstring）——
M4 加第二级时请照此就地论证，不要只写在计划/报告里。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pyluadec.ingest.proto import LuaNumber, Proto

def _strip_lineinfo(p: Proto) -> Proto:
    """Ladder rung 1 (`L3.1`): neutralise the fields that only ever reach
    `ldebug.c`, recursively over the whole subtree.

    ## What it neutralises

    `source`, `linedefined`, `lastlinedefined`, `lineinfo`, every
    `LocVar.name`, and every upvalue name. Nothing else. `LocVar.startpc`/
    `endpc` survive, and the upvalue tuple keeps its LENGTH (only the names
    become `None`), so both remain comparable.

    ## Soundness -- argued from what `compare_protos` still compares

    The argument is not "line info isn't semantic"; it is that after this rung
    runs, `_cmp` below still compares, bit for bit, everything the VM reads:

      * `code` -- the complete instruction word tuple, elementwise. Every
        opcode and every operand still has to match exactly.
      * `constants` -- length and elementwise, with `LuaNumber` compared on its
        raw 8-byte payload (`_const_eq`), so `-0.0` != `0.0` and there is no
        float-formatting slack.
      * `nups`, `numparams`, `is_vararg`, `maxstacksize` -- the frame contract
        `luaD_precall` allocates against.
      * `locvars` -- still compared as a tuple, so the NUMBER of locals and
        each one's `startpc`/`endpc` scope range still have to match; only the
        names are dropped.
      * `upvalues` -- still compared, so the upvalue COUNT still has to match.
      * `subprotos` -- length, and recursively all of the above.

    So a difference in what the recompiled function computes, in what it
    allocates, in which constants it can reach, or in how many nested
    prototypes it has, is still a mismatch at this rung. The only differences
    this rung admits are in the debug segment, which `lvm.c`'s interpreter loop
    never reads: `lundump.c`'s `LoadDebug`/`ldump.c`'s `DumpDebug` carry it,
    `luac -s` omits it entirely, and it is consumed only by `ldebug.c` when
    composing an error message or answering `debug.getinfo`.
    (`linedefined`/`lastlinedefined` are not in the debug segment -- they sit
    in `DumpFunction`'s body and survive `-s` -- but they have the same single
    consumer.)

    ## What this rung therefore does NOT prove

    Error-message TEXT and `debug.getinfo` output are outside the rung. In
    particular `ldebug.c`'s `getobjname` consults `luaF_getlocalname`, so a
    local's name can appear in `attempt to index local 'x'`. An `L3.1`
    certification says the two protos compute the same thing; it does not say
    they would produce byte-identical diagnostics. (The global-state probe
    gate has four standing divergences that are exactly error text -- from a
    different cause, the fallback emitter's box model; see
    `docs/runbooks/m3-backlog.md`.)

    ## Why the rung is needed at all on this corpus (measured)

    Every corpus chunk carries `source = b"=?"` (the dumps are `-s`-stripped),
    while `oracle.compile_source(..., strip=True)` produces `source = None`;
    and the 1715 non-main corpus protos kept their ORIGINAL file's
    `linedefined`/`lastlinedefined`, which a re-printed source with a different
    line layout cannot reproduce. Measured over `corpus/ledger.jsonl`: 0 of the
    1112 `L3` entries certify at rung 0, all 1112 are at rung 1. Without this
    rung the L3 rate on this corpus would be exactly zero.
    """
    import dataclasses
    return dataclasses.replace(
        p,
        source=None,
        linedefined=0,
        lastlinedefined=0,
        lineinfo=(),
        locvars=tuple(dataclasses.replace(v, name=None) for v in p.locvars),
        upvalues=tuple(None for _ in p.upvalues),      # drop names, keep count
        subprotos=tuple(_strip_lineinfo(s) for s in p.subprotos),
    )


NORMALIZATIONS: tuple[tuple[str, Callable[[Proto], Proto]], ...] = (
    ("strip-lineinfo", _strip_lineinfo),
)
LADDER_VERSION = "l3-ladder-v1"


@dataclass(frozen=True)
class Mismatch:
    path: str
    field: str
    a: str
    b: str


def normalize(p: Proto, level: int) -> Proto:
    if not 0 <= level <= len(NORMALIZATIONS):
        raise ValueError(f"normalization level {level} out of range "
                         f"0..{len(NORMALIZATIONS)}")
    for _name, fn in NORMALIZATIONS[:level]:
        p = fn(p)
    return p


def compare_protos(a: Proto, b: Proto, level: int = 0) -> list[Mismatch]:
    out: list[Mismatch] = []
    _cmp(normalize(a, level), normalize(b, level), "root", out)
    return out


def _const_eq(x, y) -> bool:
    if isinstance(x, LuaNumber) and isinstance(y, LuaNumber):
        return x.payload == y.payload                  # 逐位，-0.0 ≠ 0.0
    if type(x) is not type(y):
        return False
    return x == y


def _cmp(a: Proto, b: Proto, path: str, out: list[Mismatch]) -> None:
    def diff(field: str, va, vb) -> None:
        out.append(Mismatch(path=path, field=field, a=repr(va), b=repr(vb)))

    for field in ("source", "linedefined", "lastlinedefined", "nups",
                  "numparams", "is_vararg", "maxstacksize"):
        va, vb = getattr(a, field), getattr(b, field)
        if va != vb:
            diff(field, va, vb)
    if a.code != b.code:
        diff("code", a.code, b.code)
    if len(a.constants) != len(b.constants):
        diff("constants.len", len(a.constants), len(b.constants))
    else:
        for i, (x, y) in enumerate(zip(a.constants, b.constants)):
            if not _const_eq(x, y):
                out.append(Mismatch(path=path, field=f"const[{i}]", a=repr(x), b=repr(y)))
    if a.lineinfo != b.lineinfo:
        diff("lineinfo", a.lineinfo, b.lineinfo)
    if a.locvars != b.locvars:
        diff("locvars", a.locvars, b.locvars)
    if a.upvalues != b.upvalues:
        diff("upvalues", a.upvalues, b.upvalues)
    if len(a.subprotos) != len(b.subprotos):
        diff("subprotos.len", len(a.subprotos), len(b.subprotos))
    else:
        for i, (sa, sb) in enumerate(zip(a.subprotos, b.subprotos)):
            _cmp(sa, sb, f"{path}/{i}", out)

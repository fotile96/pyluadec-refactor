"""L3 归一化比对器（spec §5）。

L3.0 = 严格逐字段相等（含 lineinfo/locvars —— 诚实的最严基线）。
L3.k = 依次应用 NORMALIZATIONS[:k] 后比较；每级归一化必须单独论证健全性
（spec §9 R3），并 bump LADDER_VERSION。M2 阶梯为空。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pyluadec.ingest.proto import LuaNumber, Proto

def _strip_lineinfo(p: Proto) -> Proto:
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

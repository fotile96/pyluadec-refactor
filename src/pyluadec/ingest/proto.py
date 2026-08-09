from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LuaNumber:
    value: float
    payload: bytes          # 8 raw bytes, bit-exact

Const = None | bool | LuaNumber | bytes

@dataclass(frozen=True)
class LocVar:
    name: bytes | None
    startpc: int
    endpc: int

@dataclass(frozen=True)
class Proto:
    source: bytes | None
    linedefined: int
    lastlinedefined: int
    nups: int
    numparams: int
    is_vararg: int          # raw flag byte (HASARG|ISVARARG|NEEDSARG)
    maxstacksize: int
    code: tuple[int, ...]
    constants: tuple[Const, ...]
    lineinfo: tuple[int, ...]
    locvars: tuple[LocVar, ...]
    upvalues: tuple[bytes | None, ...]
    subprotos: tuple["Proto", ...]

def from_bridge_dict(d: dict) -> Proto:
    def conv_const(c):
        if isinstance(c, dict):
            return LuaNumber(value=c["value"], payload=c["payload"])
        return c
    return Proto(
        source=d["source"],
        linedefined=d["linedefined"], lastlinedefined=d["lastlinedefined"],
        nups=d["nups"], numparams=d["numparams"], is_vararg=d["is_vararg"],
        maxstacksize=d["maxstacksize"],
        code=tuple(d["code"]),
        constants=tuple(conv_const(c) for c in d["constants"]),
        lineinfo=tuple(d["lineinfo"]),
        locvars=tuple(LocVar(v["name"], v["startpc"], v["endpc"]) for v in d["locvars"]),
        upvalues=tuple(d["upvalues"]),
        subprotos=tuple(from_bridge_dict(s) for s in d["subprotos"]),
    )

def to_canonical(p: Proto) -> dict:
    def conv_const(c):
        if c is None:
            return {"t": "nil"}
        if isinstance(c, bool):
            return {"t": "bool", "v": c}
        if isinstance(c, LuaNumber):
            return {"t": "num", "payload": c.payload.hex()}
        return {"t": "str", "v": c.hex()}
    return {
        "source": p.source.hex() if p.source is not None else None,
        "linedefined": p.linedefined, "lastlinedefined": p.lastlinedefined,
        "nups": p.nups, "numparams": p.numparams, "is_vararg": p.is_vararg,
        "maxstacksize": p.maxstacksize,
        "code": list(p.code),
        "constants": [conv_const(c) for c in p.constants],
        "lineinfo": list(p.lineinfo),
        "locvars": [{"name": v.name.hex() if v.name is not None else None,
                     "startpc": v.startpc, "endpc": v.endpc} for v in p.locvars],
        "upvalues": [u.hex() if u is not None else None for u in p.upvalues],
        "subprotos": [to_canonical(s) for s in p.subprotos],
    }

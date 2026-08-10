from dataclasses import dataclass

SIGNATURE = b"\x1bLua"

@dataclass(frozen=True)
class Header:
    version: int
    fmt: int
    little_endian: bool
    sizeof_int: int
    sizeof_sizet: int
    sizeof_instr: int
    sizeof_number: int
    integral: bool

class BadHeader(ValueError):
    pass

def parse_header(blob: bytes) -> Header:
    if len(blob) < 12 or blob[:4] != SIGNATURE:
        raise BadHeader("not a Lua bytecode chunk")
    h = Header(
        version=blob[4], fmt=blob[5], little_endian=blob[6] == 1,
        sizeof_int=blob[7], sizeof_sizet=blob[8], sizeof_instr=blob[9],
        sizeof_number=blob[10], integral=blob[11] == 1,
    )
    if h.version != 0x51:
        raise BadHeader(f"unsupported version 0x{h.version:02x}")
    return h

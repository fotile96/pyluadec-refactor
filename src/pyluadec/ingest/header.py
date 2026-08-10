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

class IngestError(Exception):
    """Base class for all ingest-layer failures."""


class BadHeader(IngestError, ValueError):
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
    if h.fmt != 0:
        raise BadHeader(f"unsupported format {h.fmt} (expected 0 = official)")
    if not h.little_endian:
        raise BadHeader("big-endian bytecode not supported")
    if h.sizeof_int != 4:
        raise BadHeader(f"unsupported sizeof(int)={h.sizeof_int} (expected 4)")
    if h.sizeof_sizet not in (4, 8):
        raise BadHeader(f"unsupported serialized size_t width {h.sizeof_sizet}")
    if h.sizeof_instr != 4:
        raise BadHeader(f"unsupported sizeof(Instruction)={h.sizeof_instr} (expected 4)")
    if h.sizeof_number != 8:
        raise BadHeader(f"unsupported sizeof(lua_Number)={h.sizeof_number} (expected 8)")
    if h.integral:
        raise BadHeader("integral lua_Number not supported (corpus is IEEE double)")
    return h

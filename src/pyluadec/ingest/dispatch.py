from pathlib import Path
from .header import parse_header
from .proto import Proto, from_bridge_dict

def _bridge_for(sizeof_sizet: int):
    if sizeof_sizet == 4:
        from pyluadec._native import _bridge_sz4 as b
    elif sizeof_sizet == 8:
        from pyluadec._native import _bridge_sz8 as b
    else:
        raise ValueError(f"unsupported serialized size_t width {sizeof_sizet}")
    return b

def load_bytes(blob: bytes, chunkname: str = "=chunk") -> Proto:
    h = parse_header(blob)
    return from_bridge_dict(_bridge_for(h.sizeof_sizet).load_bytecode(blob, chunkname))

def load_file(path) -> Proto:
    p = Path(path)
    return load_bytes(p.read_bytes(), chunkname="@" + p.name)

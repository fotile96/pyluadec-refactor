from pathlib import Path
from .header import IngestError, parse_header
from .proto import Proto, from_bridge_dict

def _bridge_for(sizeof_sizet: int):
    if sizeof_sizet == 4:
        from pyluadec._native import _bridge_sz4 as b
    elif sizeof_sizet == 8:
        from pyluadec._native import _bridge_sz8 as b
    else:
        raise ValueError(f"unsupported serialized size_t width {sizeof_sizet}")
    actual = b.serial_sizet_width()
    if actual != sizeof_sizet:
        raise RuntimeError(
            f"bridge module for sizeof_sizet={sizeof_sizet} actually reports "
            f"serial_sizet_width()={actual}; the loaded .so does not match the "
            f"width it was selected for. Likely cause: a stale build artifact "
            f"from an interrupted rebuild -- try ./scripts/build_native.sh"
        )
    return b

def load_bytes(blob: bytes, chunkname: str = "=chunk") -> Proto:
    h = parse_header(blob)
    bridge = _bridge_for(h.sizeof_sizet)
    try:
        d = bridge.load_bytecode(blob, chunkname)
    except RuntimeError as e:
        raise IngestError(f"bridge load failed: {e}") from e
    return from_bridge_dict(d)

def load_file(path) -> Proto:
    p = Path(path)
    return load_bytes(p.read_bytes(), chunkname="@" + p.name)

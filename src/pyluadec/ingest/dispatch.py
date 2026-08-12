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
    try:
        bridge = _bridge_for(h.sizeof_sizet)
    except RuntimeError as e:
        # The stale-`.so` width mismatch above. It used to be raised OUTSIDE
        # any handler, so a caller that had wrapped ingest in
        # `except IngestError` -- the documented way to catch a load failure --
        # saw a bare `RuntimeError` escape instead. Carried as a deferred M2
        # minor through M3 and M4 (`m3-backlog.md` §14); fixed at M5 task 12.
        # The message is `_bridge_for`'s own, which already names the likely
        # cause and the repair command, so it is re-raised rather than
        # re-worded. `ValueError` is deliberately NOT caught here: an
        # unsupported width is a `BadHeader`-class fact about the input and
        # `parse_header` is what owns rejecting it.
        raise IngestError(str(e)) from e
    try:
        d = bridge.load_bytecode(blob, chunkname)
    except RuntimeError as e:
        raise IngestError(f"bridge load failed: {e}") from e
    return from_bridge_dict(d)

def load_file(path) -> Proto:
    p = Path(path)
    return load_bytes(p.read_bytes(), chunkname="@" + p.name)

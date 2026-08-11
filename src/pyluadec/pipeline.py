"""反编译驱动（spec §7）。

M3 起，每个 proto 都先经 `structure.structured.emit_certified_chunk` 做逐 proto
L3 认证；等级（proof record，逐 proto）与产物源码（逐 chunk，root 认证才发结构化
源码）**刻意解耦**——见 `structure.structured` 的模块文档。confession 只记在未认证
的 proto 上：等级上升、confession 下降，正是台账的 ratchet 信号。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pyluadec.ingest import load_file as _ingest_file
from pyluadec.ingest.proto import Proto


@dataclass
class DecompileResult:
    source: bytes
    confessions_by_proto: dict[str, list[dict]]
    levels: dict[str, str] = field(default_factory=dict)      # proto_path -> "L3" | "L1"
    rungs: dict[str, int | None] = field(default_factory=dict)


def walk_proto_paths(path: str, p: Proto, out: dict[str, Proto]) -> None:
    out[path] = p
    for i, s in enumerate(p.subprotos):
        walk_proto_paths(f"{path}_{i}", s, out)


def decompile_chunk(root: Proto) -> DecompileResult:
    from pyluadec.structure.structured import emit_certified_chunk
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    out = emit_certified_chunk(root)
    levels = {path: out.certs[path].level for path in protos}
    rungs = {path: out.certs[path].rung for path in protos}
    confessions = {
        path: ([] if levels[path] == "L3" else
               [{"pc_lo": 1, "pc_hi": len(p.code),
                 "reason": "fallback-state-machine", "pass": "structure.fallback"}])
        for path, p in protos.items()
    }
    return DecompileResult(source=out.source, confessions_by_proto=confessions,
                           levels=levels, rungs=rungs)


def decompile_file(path) -> DecompileResult:
    return decompile_chunk(_ingest_file(Path(path)))

"""反编译驱动：M2 阶段一切函数走 fallback 状态机（spec §7 M2）。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyluadec.ingest import load_file as _ingest_file
from pyluadec.ingest.proto import Proto
from pyluadec.structure.fallback import emit_chunk


@dataclass
class DecompileResult:
    source: bytes
    confessions_by_proto: dict[str, list[dict]]


def walk_proto_paths(path: str, p: Proto, out: dict[str, Proto]) -> None:
    out[path] = p
    for i, s in enumerate(p.subprotos):
        walk_proto_paths(f"{path}_{i}", s, out)


def decompile_chunk(root: Proto) -> DecompileResult:
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    confessions = {
        path: [{"pc_lo": 1, "pc_hi": len(p.code),
                "reason": "fallback-state-machine", "pass": "structure.fallback"}]
        for path, p in protos.items()
    }
    return DecompileResult(source=emit_chunk(root), confessions_by_proto=confessions)


def decompile_file(path) -> DecompileResult:
    return decompile_chunk(_ingest_file(Path(path)))

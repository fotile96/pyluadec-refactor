"""L3 认证门（spec §5）：结构化产物重编译 → 归一化阶梯逐级比对 → 通过即 proved。"""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec import oracle
from pyluadec.ingest import Proto, load_bytes

from .normalize import NORMALIZATIONS, Mismatch, compare_protos


@dataclass(frozen=True)
class CertResult:
    level: str                       # "L3" | "L1"
    rung: int | None                 # normalization level that passed, or None
    mismatches: tuple[Mismatch, ...]


def certify_l3(original: Proto, structured_src: bytes) -> CertResult:
    try:
        recompiled = load_bytes(oracle.compile_source(structured_src, strip=True))
    except oracle.LuaCompileError:
        return CertResult(level="L1", rung=None, mismatches=())
    last: list[Mismatch] = []
    for k in range(len(NORMALIZATIONS) + 1):
        diffs = compare_protos(original, recompiled, level=k)
        if not diffs:
            return CertResult(level="L3", rung=k, mismatches=())
        last = diffs
    return CertResult(level="L1", rung=None, mismatches=tuple(last))

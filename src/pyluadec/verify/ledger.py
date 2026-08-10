"""认证台账（spec §5）：主键 = 归一化结构哈希，jsonl 落盘，diff 稳定。"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pyluadec.ingest.proto import LuaNumber, Proto


def _structure_view(p: Proto) -> dict:
    def conv(c):
        if isinstance(c, LuaNumber):
            return {"t": "num", "p": c.payload.hex()}
        if isinstance(c, bytes):
            return {"t": "str", "v": c.hex()}
        if c is None:
            return {"t": "nil"}
        return {"t": "bool", "v": c}

    return {
        "numparams": p.numparams,
        "is_vararg": p.is_vararg,
        "nups": p.nups,
        "maxstacksize": p.maxstacksize,
        "code": list(p.code),
        "constants": [conv(c) for c in p.constants],
        "n_upvalues": len(p.upvalues),
        "subprotos": [_structure_view(s) for s in p.subprotos],
    }


def structural_hash(p: Proto) -> str:
    blob = json.dumps(_structure_view(p), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def oracle_version() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"],
                           cwd=Path(__file__).resolve().parents[3],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except OSError:
        return "unknown"


@dataclass
class LedgerEntry:
    shash: str
    level: str                    # L0 | L1 | L2 | L3
    l3_level: int | None
    compile_ok: bool
    fallback: bool
    n_insns: int
    confessions: list[dict]
    occurrences: list[dict]
    oracle: str
    ladder: str


def write_ledger(entries: list[LedgerEntry], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for e in sorted(entries, key=lambda e: e.shash):
            fh.write(json.dumps(dataclasses.asdict(e), ensure_ascii=False) + "\n")


def read_ledger(path: Path) -> list[LedgerEntry]:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(LedgerEntry(**json.loads(line)))
    return out

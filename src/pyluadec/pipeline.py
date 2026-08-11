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
    # proto_path -> why it is not L3 (None for the L3 ones). The generic
    # `fallback-state-machine` confession says only THAT a proto fell back;
    # this says why -- a `build_sir` refusal and a print-then-reject used to be
    # indistinguishable in the ledger. Vocabulary and payload rules:
    # `structure.structured.ProtoCert.reason`.
    reasons: dict[str, str | None] = field(default_factory=dict)


def walk_proto_paths(path: str, p: Proto, out: dict[str, Proto]) -> None:
    """Assign every proto in the tree its `proto_path` ("main", "main_0",
    "main_0_1", ...). These are the keys of `DecompileResult.levels` /
    `.confessions_by_proto` and of every `occurrences[].proto_path` in
    `corpus/ledger.jsonl`.

    ## Coupling: `f"{path}_{i}"` is written independently in THREE places

    Here, at `structure/fallback.py`'s CLOSURE handler (`f"{self.path}_{bx}"`,
    the `__pld_F` factory key it emits), and in `fallback.emit_chunk`'s own
    `walk`. That they agree is not decoration: it is what lets you take a
    `proto_path` out of a ledger row and find the corresponding
    `__pld_F["main_3_0"]` factory in `build/decompiled/<file>.lua`, which is
    the normal way to chase a single proto's fallback output. Nothing tests
    it. A one-line edit to any of the three would silently break the
    cross-reference, and only a careful reader of the ledger diff would
    notice.

    Two halves to the agreement, and note that a shared format helper would
    only fix the first:

    1. the *spelling* — `"_"` and decimal, all three sites;
    2. the *index* — this function uses `enumerate(p.subprotos)`, while the
       CLOSURE handler uses the instruction's `Bx`, which is the subproto
       index by `lparser.c` construction. Those must denote the same child.

    Extracting a shared helper (and, better, a test asserting the emitted
    `__pld_F` key set equals the ledger's `proto_path` set for one file) is
    recorded in `docs/runbooks/m3-backlog.md` under the deferred minors.
    """
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
    reasons = {path: out.certs[path].reason for path in protos}
    # The confession names `structure.fallback` as the pass that emitted this
    # proto's text, and that is only literally true when the CHUNK shipped
    # fallback -- i.e. when the root is not `L3`. A non-`L3` proto inside a
    # chunk whose root DID certify would be stamped with it anyway, and its
    # text actually came from the structured printer. Measured 2026-08-12 over
    # all 229 files: **0** such protos, because a root that certifies has had
    # its whole subtree compared field by field, and the per-proto wrapper
    # verdict has not yet disagreed with that on this corpus. Left unguarded
    # rather than made conditional on `levels["main"]`, because adding the
    # guard would change nothing today and `tests/test_m4_exit.py` asserts the
    # row-local coupling (non-`L3` => exactly one such confession) that a
    # conditional would break. If the measurement ever comes back non-zero,
    # the fix is a second confession `reason`, not dropping this one.
    confessions = {
        path: ([] if levels[path] == "L3" else
               [{"pc_lo": 1, "pc_hi": len(p.code),
                 "reason": "fallback-state-machine", "pass": "structure.fallback"}])
        for path, p in protos.items()
    }
    return DecompileResult(source=out.source, confessions_by_proto=confessions,
                           levels=levels, rungs=rungs, reasons=reasons)


def decompile_file(path) -> DecompileResult:
    return decompile_chunk(_ingest_file(Path(path)))

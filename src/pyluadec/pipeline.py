"""反编译驱动（spec §7）。

M3 起，每个 proto 都先经 `structure.structured.emit_certified_chunk` 做逐 proto
L3 认证；等级（proof record，逐 proto）与产物源码（逐 chunk）**刻意解耦**——见
`structure.structured` 的模块文档。confession 只记在实际发了 fallback 文本的
proto 上：等级上升、confession 下降，正是台账的 ratchet 信号。

**「root 认证才发结构化源码」这条自 M5 task 6 起不成立**（本行原文如此，M5 task 12
更正）。产物有三档，按顺序试：root 自己认证过的字节；否则 `certify_hybrid` 认证过
的 hybrid——结构化代码，只在无法认证的 CLOSURE 站点填入语义精确的 fallback，此时
**root 并未认证**却仍发结构化文本；否则整块 fallback。语料上 216 / 6 / 7。不变的
是更弱也更真的那句：产物里每个 proto 要么被「编译了这串字节」的那次认证逐字段覆盖，
要么由 fallback 发射并在台账 confess。
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
    # proto_path -> did THIS proto's text in `source` come from the fallback
    # state machine? (M5 task 6.) This is a fact about the shipped artifact,
    # and it is deliberately NOT `levels[path] != "L3"`: in a hybrid chunk a
    # proto can miss `L3` on its own (its subtree contains something the
    # recognizer refuses) and still ship structured, because the hybrid
    # certification compared its own fields against the original exactly. It
    # is what `confessions_by_proto` is keyed on.
    shipped_fallback: dict[str, bool] = field(default_factory=dict)
    # Did the chunk ship as a hybrid at all? False for a fully-structured
    # chunk and for a whole-file fallback.
    hybrid: bool = False
    # The propose-and-certify channel (M8): proto_path -> did THIS proto's
    # text in `source` come from a hand-written proposal? The closure of
    # the substituted sites, same shape as `shipped_fallback`. Protos in
    # here are certified (the chunk passed a whole-tree compare); the
    # distinction is provenance, not verdict.
    shipped_proposal: dict[str, bool] = field(default_factory=dict)
    # The proposal round's ladder rung; -1 when no proposal tier ran.
    proposal_rung: int = -1


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


def decompile_chunk(root: Proto,
                    proposals: dict[str, bytes] | None = None,
                    ) -> DecompileResult:
    from pyluadec.structure.structured import emit_certified_chunk
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    out = emit_certified_chunk(root, proposals)
    levels = {path: out.certs[path].level for path in protos}
    rungs = {path: out.certs[path].rung for path in protos}
    reasons = {path: out.certs[path].reason for path in protos}
    # The confession names `structure.fallback` as the pass that emitted this
    # proto's text, so it is keyed on what actually happened to this proto in
    # THIS chunk -- `out.fallback_paths` -- and not on its certification level.
    #
    # Until M5 task 6 the two were the same predicate (`levels[path] != "L3"`),
    # because a chunk was all-structured or all-fallback and the root's `L3`
    # covered its whole subtree. The comment that stood here noted the one way
    # they could come apart (a non-`L3` proto inside a certified root) and
    # recorded 0 such protos on this corpus. Hybrid emission makes the OTHER
    # direction real: **6 of the 13** formerly-fallback files became hybrids
    # (`snr_story_main`, `snr_fragment_main`, `snr_s1_10_s`, `snr_s3_10_s`,
    # `snr_s4_10_s`, `snr_s5_10_s`), and each ships **one** proto occurrence
    # that is not individually `L3` -- 6 occurrences in 6 files, re-derived
    # from the committed ledger 2026-08-13. (This comment said "12 of the 13",
    # which is 2x the count of hybrids that exist; the other 7 still ship the
    # whole-file fallback.) Stamping those 6 with `fallback-state-machine`
    # would be a false confession -- the
    # text came from the structured printer and was compared field for field
    # by `certify_hybrid`. The level stays exactly what `certify_proto` said;
    # only the confession moved to the shipped-artifact fact it was always
    # describing.
    shipped_fallback = {path: path in out.fallback_paths for path in protos}
    shipped_proposal = {path: path in out.proposal_paths for path in protos}
    confessions = {
        path: ([{"pc_lo": 1, "pc_hi": len(p.code),
                 "reason": "fallback-state-machine", "pass": "structure.fallback"}]
               if shipped_fallback[path] else [])
        for path, p in protos.items()
    }
    return DecompileResult(source=out.source, confessions_by_proto=confessions,
                           levels=levels, rungs=rungs, reasons=reasons,
                           shipped_fallback=shipped_fallback, hybrid=out.hybrid,
                           shipped_proposal=shipped_proposal,
                           proposal_rung=out.proposal_rung)


def decompile_file(path) -> DecompileResult:
    return decompile_chunk(_ingest_file(Path(path)))

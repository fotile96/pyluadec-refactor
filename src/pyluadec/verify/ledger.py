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
    # Provenance of the in-repo lua/luac ORACLE BUILD, not of repo HEAD:
    # `git rev-parse HEAD` moves the instant this ledger is committed (the
    # commit containing the ledger becomes the new HEAD), making every
    # regeneration rewrite all entries even when the oracle itself is
    # unchanged. The last commit that touched the oracle's sources is stable
    # across doc/test/ledger-only commits and only changes when the actual
    # luac/lua build inputs change -- which is the event this field exists
    # to invalidate results on. native/patches/ lives under native/, so the
    # serialization-width patch is covered.
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", "vendor", "native"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True, text=True, timeout=10)
        out = r.stdout.strip()
        return out if r.returncode == 0 and out else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


@dataclass
class LedgerEntry:
    shash: str
    # `L0 | L1 | L3`. **There is no `L2` level and there never was one** --
    # M5 task 9 landed L2 as the separate `l2` field below, deliberately,
    # because `L2` and `L3` are independent proofs and a single rank would
    # force a row that has both to discard one (`decompile-pipeline.md`, "the
    # ledger's fields"). `scripts/run_corpus.py::_RANK` still carries an
    # `"L2": 2` entry; it is dead and is documented as dead there.
    level: str
    l3_level: int | None
    compile_ok: bool
    fallback: bool
    n_insns: int
    confessions: list[dict]
    occurrences: list[dict]
    oracle: str
    ladder: str
    # Why this proto is not `L3`; `None` exactly when it is (M4 task 6). The
    # `confessions` list says only THAT a proto's text came from the fallback
    # state machine, which was enough while a refusal was the only way to miss
    # `L3` and stopped being enough once M4 produced protos that structure and
    # print cleanly and then fail the comparison.
    #
    # It also no longer LINES UP with this field, and M5 task 6 is why: since
    # hybrid emission, `confessions` tracks the shipped artifact and `level`
    # tracks the proof, so the two disagree in both directions. Measured on
    # the committed ledger 2026-08-13: **6 of the 48 non-`L3` rows carry no
    # confession** (they ship structured inside a hybrid), and **150 `L3` rows
    # do** (they live in the 7 whole-file-fallback chunks). The sentence that
    # stood here -- "every non-`L3` row carries the same whole-range
    # `fallback-state-machine` entry" -- was a pre-task-6 fact left in the
    # present tense. Produced by `structure.structured.ProtoCert.reason`;
    # its vocabulary, and the rule that it never carries bytecode-derived
    # payload, are documented there. Defaulted so that a ledger written before
    # this field existed still loads through `read_ledger`.
    refusal_reason: str | None = None
    # The L2 differential-execution badge (M5 task 9). `{"cov": 0.xx}` when
    # every occurrence of this shape lives in a file that passed the L2 gate,
    # `None` otherwise. Computed by `row_l2` from the per-occurrence records,
    # never independently -- see that function for why the row-level field is
    # an aggregate rather than a measurement of its own. Defaulted so a ledger
    # written before this field existed still loads through `read_ledger`.
    #
    # **What a grant proves, and what it does not.** It proves that the
    # original bytecode and the shipped artifact produced byte-identical event
    # traces under a stub environment and a scripted key sequence, that at
    # least one of those runs reached its end rather than the event cap, that
    # no stub-derived value was seen deciding a branch, and that every proto in
    # the chunk is `L3`. It does NOT prove behaviour under the real engine, and
    # it says nothing about paths the sequence did not take -- `cov` is exactly
    # the fraction of the artifact's protos the completed runs entered, and
    # `scripts/probe_keyseq.py`'s module docstring lists four gaps the pair
    # still cannot see. The full rule is `probe_keyseq.evaluate`.
    #
    # **What this field does NOT record: truncation.** A granted row stores
    # `{"cov": <n>}` and nothing else, so "1 of 2 sequences ran to completion"
    # lives only in `L2Result.detail`, which is CLI-facing and never
    # serialised. `snr_lib.lua`'s granted row is `{"cov": 1.0}` today. Left as
    # is on purpose for the M5 branch -- adding a key rewrites every driven
    # row and this file is the branch's byte-frozen artifact -- but it is
    # OPEN, not closed: `tests/test_l2_keyseq.py::test_a_branch_only_a_capped_
    # sequence_enters_is_granted_on_a_truncated_prefix` shows a grant a capped
    # run can still carry alone for one branch, and the ledger says nothing
    # about it. M6 (`m3-backlog.md`, M6 agenda 2).
    l2: dict | None = None


def row_l2(occurrences: list[dict]) -> dict | None:
    """The row-level `l2` field, as a pure function of the occurrences.

    ## Why `l2` is per-OCCURRENCE first and per-row only as an aggregate

    `l2` is a property of running a whole CHUNK under a key sequence, i.e. of
    a FILE. A ledger row is a `structural_hash` group, and one shape occurs in
    up to 27 different files (measured 2026-08-12 on the committed ledger: 13
    of 1478 shapes occur in more than one file). So a per-file fact cannot be
    a row-level measurement without an aggregation rule, and it must not be
    pushed into the verdict `scripts/run_corpus.py::key_disagreements` pins.

    That function's stated policy -- "if this ever returns non-empty, the fix
    is to split the key" -- applies to the CERTIFICATION verdict `(level,
    rung, refusal_reason)`, which `structure.structured._memo_key` claims is a
    function of `(structural_hash, _debug_fingerprint)`. `l2` makes no such
    claim and could not: two occurrences of one shape can legitimately differ,
    because one file has an authored key sequence and the other does not.
    That is the same reason its docstring already excludes `compile_ok` ("a
    property of the file, not of the shape"), and it is why `hybrid` and
    `shipped` live on the occurrence. Adding `l2` to the pinned verdict would
    manufacture disagreements and force a key split that carries no soundness
    content -- so `key_disagreements` is left exactly as it is.

    ## The aggregation rule, and why this direction

    Granted only when EVERY occurrence is granted, at the MINIMUM coverage
    seen. A row's badge is a claim about the shape wherever it ships, so one
    occurrence in a file that was never driven (or that diverged) has to sink
    the row -- the same conservative direction `fallback` takes with its OR
    over occurrences. A max-based rule would let one granted file lend its
    badge to 26 files nobody ran.
    """
    if not occurrences:
        return None
    covs = []
    for o in occurrences:
        v = o.get("l2")
        if not isinstance(v, dict) or "cov" not in v:
            return None
        covs.append(v["cov"])
    return {"cov": min(covs)}


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

"""Predecessor-text re-certification -- M7 task 2 (spec §3).

Runs the predecessor's decompiled SOURCE back through our own pipeline::

    pred .lua text --oracle.compile_source(strip=True)--> bytecode
                    --ingest.load_bytes--> Proto tree
                    --pipeline.decompile_chunk--> OUR output-surface-v2 text
                                                  + per-proto Factor-T grades

Factor T measures *text fidelity to its source bytecode* -- here the source is
the PREDECESSOR's bytecode, not the original's. Whether that bytecode is
equivalent to the original is the invariant panel's job (Factor E, M7 tasks
3-4); this module says nothing about it.

**Strip convention, fixed here for the milestone (spec §3 rev 3).** The
reference is always ``oracle.compile_source(pred_text, strip=True)``. Pred
text compiled unstripped carries real ``lineinfo``/``locvars`` our re-emitted
text cannot reproduce, and ``verify.certify.carries_debug`` would then compile
candidates unstripped and fail on debug tables -- the exact phantom-mismatch
class M6 measured once (260 ``nups > 0`` protos sprouting manufactured
``upvalues``-length mismatches, ``docs/reports/m6-cross-corpus.md`` §1 round 1).
Stripping the reference matches the original corpus's shape (all 1944 original
protos are stripped) and makes certification compare semantic fields only,
which is the claim Factor T actually makes.

**T-grade mapping** (one place, ``t_grade``): ``T3`` iff the proto certified
``L3``; ``T2`` iff it missed ``L3`` but shipped structured text (the hybrid
contract compared this proto's own fields field-exactly); ``T-`` iff it
shipped fallback text. The case order is part of the contract: ``L3`` is
checked first, so a level beats the shipped flag when both are present
(``shipped_fallback`` and ``level != "L3"`` are not the same predicate --
`pipeline.DecompileResult` documents the two directions they come apart).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ingest import load_bytes
from .oracle import compile_source
from .pipeline import decompile_chunk


@dataclass(frozen=True)
class RecertOutcome:
    """One pred file's re-certification result.

    ``source`` is OUR re-emitted text (or the chunk's hybrid/fallback
    assembly exactly as ``decompile_chunk`` shipped it) -- never the pred
    text copied through. ``reference`` is the stripped pred bytecode the
    certification ran against. ``t_grades``/``reasons`` are keyed by
    ``proto_path`` with identical key sets.
    """

    source: bytes
    t_grades: dict[str, str]
    reasons: dict[str, str | None]
    reference: bytes


def t_grade(level: str | None, shipped_fallback: bool) -> str:
    """The stated mapping, as one case ladder. ``L3`` is checked first."""
    if level == "L3":
        return "T3"
    if not shipped_fallback:
        return "T2"
    return "T-"


def recert_bytes(source: bytes) -> RecertOutcome:
    """Re-certify one pred source text (see module docstring for the flow)."""
    reference = compile_source(source, strip=True)
    result = decompile_chunk(load_bytes(reference))
    t_grades = {
        path: t_grade(result.levels.get(path), result.shipped_fallback.get(path, True))
        for path in result.levels
    }
    reasons = {path: result.reasons.get(path) for path in result.levels}
    return RecertOutcome(
        source=result.source,
        t_grades=t_grades,
        reasons=reasons,
        reference=reference,
    )


def recert_file(pred_dir: Path, name: str) -> RecertOutcome:
    """``recert_bytes`` over ``pred_dir / name``."""
    return recert_bytes((Path(pred_dir) / name).read_bytes())

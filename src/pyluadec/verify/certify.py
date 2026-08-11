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
    """Recompile `structured_src` and compare it to `original` up the ladder.

    **The candidate is always compiled with `strip=True`,** which matches the
    corpus (every one of the 229 target files is `-s`-stripped; see CLAUDE.md)
    but has a consequence worth knowing before you point this at anything else:

    An `original` that still CARRIES debug info can essentially never reach
    `L3`. Rung 1 (`_strip_lineinfo`) deliberately blanks locvar and upvalue
    *names* while KEEPING each locvar's count/`startpc`/`endpc` -- that is a
    stronger check, not an oversight -- so an unstripped original's non-empty
    `locvars` is compared against the stripped candidate's empty one and
    mismatches at every rung. Measured 2026-08-11 with the repo's own
    `luac_sz4`:

        b"x = 1\\n"                       strip=True -> L3 rung 0
                                          strip=False -> L3 rung 1
        b"local a = 1\\nprint(a)\\n"       strip=True -> L3 rung 0
                                          strip=False -> L1, field `locvars`
        b"for i = 1, 10 do print(i) end"  strip=True -> L3 rung 0
                                          strip=False -> L1, field `locvars`

    So the rule is: a proto that declares no locals is unaffected, and a proto
    that declares even one can only certify if the original was stripped.
    Ordinary `luac` output (no `-s`) therefore falls back for nearly every
    real function, with `Mismatch(field="locvars")` as the only clue. Compile
    your fixtures with `-s`, as `tests/test_certify.py`'s and
    `tests/test_structured_certify.py`'s `_proto` helpers do.

    The stronger fix -- matching the candidate's strip mode to the original's,
    which would let rung 1 compare real locvar scope ranges -- is recorded in
    `docs/runbooks/m3-backlog.md` as M4 work. It is a behaviour change that
    can move the committed ledger, so it is not made here.
    """
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

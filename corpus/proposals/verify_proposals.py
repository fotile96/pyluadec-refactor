"""Verify every hand-written proposal in corpus/proposals/ against the
original bytecode through the UNMODIFIED certification ladder.

Status: staging artifacts for the propose-and-certify channel (approved for
M8/M9 by the human partner, 2026-08-18; see
docs/reports/m8-strategy-survey-fable5.md §4 and its §9 addendum).  These
files are NOT yet consumed by the pipeline -- the channel task will define
their final home and wiring.  Until then this driver is the only thing that
keeps them honest.

Trigger (out-of-suite check, per CLAUDE.md's four conditions): run whenever
a proposal is added or edited, after any oracle (`build/luac_sz4`) rebuild,
and at the start of the channel-implementation task.  Last-run record lives
in the survey's §9 table.

Usage:
    PYLUADEC_CORPUS_DIR=<corpus> uv run python corpus/proposals/verify_proposals.py

Exit 0: every proposal certifies at rung <= 1.  Exit 1: at least one does
not (the failing proto is named on stdout).  Exit 2: environment problem
(corpus dir missing) -- not a verdict about the proposals.

Format of a proposal file: the exact wrapper `certify_proto` compiles for a
non-root proto -- `local u0, ... <n>` declarations when the proto has
upvalues, then `return function(<params>)` with the body, matching
`structure/structured.py`'s convention.  The compiled chunk's
`subprotos[0]` is the candidate; comparison is `verify.normalize`'s ladder,
strict first, then rung 1 (strip-lineinfo), exactly as certification runs
it.  Nothing here relaxes or reimplements the comparators.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pyluadec import oracle                              # noqa: E402
from pyluadec.ingest import load_bytes, load_file        # noqa: E402
from pyluadec.verify.certify import carries_debug        # noqa: E402
from pyluadec.verify.normalize import NORMALIZATIONS, compare_protos  # noqa: E402

#: (corpus file, proto path, subproto index chain from the chunk root)
TARGETS = [
    ("snr_common.lua", "main_24", (24,)),
    ("snr_common.lua", "main_25", (25,)),
    ("snr_common.lua", "main_25_4", (25, 4)),
    ("snr_common.lua", "main_71", (71,)),
    ("snr_common.lua", "main_74_18", (74, 18)),
    ("snr_common.lua", "main_76_2", (76, 2)),
    ("snr_graphic.lua", "main_4", (4,)),
    ("snr_mainmenu.lua", "main_7", (7,)),
    ("snr_story_main.lua", "main_3", (3,)),
]


def main() -> int:
    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not corpus or not Path(corpus).is_dir():
        print("PYLUADEC_CORPUS_DIR is unset or not a directory", file=sys.stderr)
        return 2
    here = Path(__file__).resolve().parent
    failures = []
    for fname, proto_path, chain in TARGETS:
        proposal = here / fname.removesuffix(".lua") / f"{proto_path}.lua"
        original = load_file(Path(corpus) / fname)
        for i in chain:
            original = original.subprotos[i]
        cand = load_bytes(oracle.compile_source(
            proposal.read_bytes(),
            strip=not carries_debug(original))).subprotos[0]
        rung = None
        if not compare_protos(original, cand):
            rung = 0
        else:
            for r, (_, norm) in enumerate(NORMALIZATIONS, start=1):
                if not compare_protos(norm(original), norm(cand)):
                    rung = r
                    break
        if rung is None:
            failures.append(f"{fname}:{proto_path}")
            print(f"FAIL  {fname}:{proto_path} -- no rung passes")
        else:
            print(f"pass  {fname}:{proto_path} (rung {rung})")
    if failures:
        print(f"proposals: {len(failures)} FAILING: {failures}")
        return 1
    print(f"proposals: {len(TARGETS)}/{len(TARGETS)} certify through the unmodified ladder")
    return 0


if __name__ == "__main__":
    sys.exit(main())

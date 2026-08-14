"""L1.5 gate: compare observable global-table state between original bytecode and
decompiled output, without the game engine. See docs/runbooks/m3-backlog.md item 3.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Run as `uv run python scripts/probe_global_state.py`, sys.path[0] is
# scripts/, not the repo root, so `scripts.probe_common` would not resolve.
# Imported as a module by the tests it already resolves and this is a no-op.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.probe_common import adjudicate_pins  # noqa: E402

PROBE = ROOT / "scripts" / "probe_global_state.lua"

# Every result the probe script is allowed to produce starts with one of these.
# Anything else means the probe itself did not run to completion, and comparing
# two such results would be comparing two failures, not two program states.
_MARKERS = (b"OK|", b"ERR|", b"LOADFAIL")


class ProbeError(RuntimeError):
    """The probe did not produce a usable result (crash, non-zero exit, or
    unrecognisable stdout). Never silently turned into a comparable value:
    every probe-side failure used to yield "" on both sides, so a completely
    dead probe compared equal for all 229 corpus files and the gate passed."""


def probe(payload: bytes, *, is_source: bool, timeout: float = 30.0) -> str:
    from pyluadec import oracle
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        r = subprocess.run([str(oracle.lua_sz4()), str(PROBE), str(f)],
                           capture_output=True, timeout=timeout, cwd=td)
        if r.returncode != 0:
            raise ProbeError(
                f"probe exited {r.returncode} (is_source={is_source}, "
                f"probe={PROBE}); stderr="
                f"{r.stderr.decode('utf-8', 'replace')!r}; stdout="
                f"{r.stdout[:400].decode('utf-8', 'replace')!r}")
        if not r.stdout.startswith(_MARKERS):
            raise ProbeError(
                f"probe produced an unrecognisable result (is_source="
                f"{is_source}); expected one of "
                f"{[m.decode() for m in _MARKERS]}; stdout="
                f"{r.stdout[:400].decode('utf-8', 'replace')!r}; stderr="
                f"{r.stderr.decode('utf-8', 'replace')!r}")
        # The probe's stdout is a deterministic ASCII/UTF-8 serialisation format
        # (see probe_global_state.lua: sorted "type:key" keys, "%.17g" numbers,
        # "<type>" placeholders) that we only ever compare for equality or
        # search for known ASCII markers. It is not a bytecode-derived string
        # kept on the Python side (that constraint is about Proto string
        # constants, not this probe's own output format), so decoding it for
        # comparison is safe. errors="replace" is deliberate: a corpus file's
        # Japanese string constants are not guaranteed UTF-8, and if such a byte
        # sequence ever leaked into a table key's tostring() output, replacing
        # the undecodable bytes still yields a *stable* (deterministic) string
        # that two runs of the same input decode identically -- which is all
        # equality comparison needs. Raising instead would turn a legitimate
        # non-UTF-8 corpus file into a spurious probe crash rather than a real
        # semantic finding.
        return r.stdout.decode("utf-8", "replace")


def payload_of(result: str) -> str:
    """The serialised global-state delta, with the OK|/ERR|/LOADFAIL marker
    stripped -- i.e. the part that is actual observed program state."""
    if result.startswith("OK|"):
        return result[3:].strip()
    if result.startswith("ERR|"):
        # "ERR|<stripped error message>|<globals written before the error>"
        #
        # KNOWN AMBIGUITY, deliberately not fixed (M5 agenda item 11, decided
        # at task 12). The message is `probe_global_state.lua`'s
        # `strip_location(err)` output, which is NOT escaped, so a message
        # containing a `|` splits here in the wrong place. The two candidate
        # repairs both cost more than the defect: escaping `|` on the Lua side
        # changes the probe's wire format, and the pinned divergences in
        # `EXPECTED_ERROR_NAME_DIVERGENCE` below are exact strings in that format;
        # splitting from the right is no better, because the globals block can
        # contain `|` inside a serialised string value.
        #
        # It is latent, and measurably so: this branch has **no live caller**
        # -- both call sites (`tests/test_global_state_probe.py`, two of them)
        # only reach `payload_of` for results starting `OK|`. Re-check that
        # before relying on the split.
        rest = result[4:]
        bar = rest.find("|")
        return rest[bar + 1:].strip() if bar >= 0 else ""
    return ""


# The corpus files whose ORIGINAL bytecode and DECOMPILED output both fail, at
# the same point and with the same error class, but whose error text carries a
# different variable name.
#
# Lua 5.1 builds "attempt to index <kind> '<name>'" / "bad argument #n to
# '<name>'" from ldebug.c's getobjname(), which names a value by the BYTECODE
# SHAPE that produced it -- global read, local, upvalue, table field. The
# fallback emitter routes every register through the `__pld_R` box table, so a
# value the original read with GETGLOBAL is read from a table field in our
# output, and getobjname names it "field 'v'" / "field '?'" instead of
# "global 'gameSave'". The failing operation, the offending value's type and
# the set of globals written before the failure all match. Instruction-level
# evidence for each is in docs/runbooks/m3-backlog.md (written when there were
# four; two of those four have since converged, see below).
#
# Pinned as EXACT PAIRS, not as an exclusion list: if either side's text
# changes -- including if they start agreeing -- the gate fails and the pin
# must be re-derived. Do not add entries to make a divergence go away.
#
# Lives here rather than in the test so that the CLI below and
# tests/test_global_state_probe.py cannot disagree about what is pinned. They
# used to: main() knew nothing about the pins and printed a red "225/229" plus
# a non-zero exit while the test suite was green.
#
# Was four entries; `snr_graphic.lua`, `snr_memory.lua` and `snr_mainmenu.lua`
# were deleted in M6 task 12 because their pairs CONVERGED. Deleting them was
# not a judgement call: `probe_common.adjudicate_pins` reports a converged pin
# as `gone`, main() below returns 1 on it and the gate asserts it empty, so a
# stale pin fails loudly until it is removed.
#
# All three converged by the SAME mechanism, and it is NOT certification --
# none of the three `main`s certifies `L3` (round-1 correction; this comment
# first claimed `snr_mainmenu.lua`'s did, and it is `L1`, `mismatch: code at
# root/7`). What changed is that all three moved from whole-file fallback to
# HYBRID: enough of each chunk now ships structured text that the read which
# fails is a real `GETGLOBAL` there rather than a `__pld_R[<number>]` lookup,
# so `getobjname` names it identically on both sides.
#
# They still ship plenty of box model -- "converged" is not "stopped". Lines
# carrying `__pld_R`, measured 2026-08-14 across M6 task 12:
#     snr_graphic.lua    1862/2411 -> 1324/1849
#     snr_memory.lua     1225/1673 -> 1038/1469
#     snr_mainmenu.lua   3220/4782 -> 1974/3325   (of which 18 are still the
#                                                  `["library"]` lines this
#                                                  file's pin was about)
# Measured 2026-08-14: 228/229 identical, 1 pinned divergence.
EXPECTED_ERROR_NAME_DIVERGENCE = {
    "snr_novel.lua": (
        "ERR|attempt to index global 'systemSave' (a nil value)|\n",
        "ERR|attempt to index field 'v' (a nil value)|\n"),
}


def main() -> int:
    from pyluadec.pipeline import decompile_file
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    files = sorted(corpus.glob("*.lua"))
    divergent = {}
    for f in files:
        orig = probe(f.read_bytes(), is_source=False)
        dec = probe(decompile_file(f).source, is_source=True)
        if orig != dec:
            divergent[f.name] = (orig, dec)
    # Two-directional, exactly as the test asserts: a pinned pair that changed
    # text, converged, or vanished is a failure, not a silent pass.
    unexpected, moved, gone = adjudicate_pins(
        divergent, EXPECTED_ERROR_NAME_DIVERGENCE)
    print(f"global-state: {len(files) - len(divergent)}/{len(files)} identical, "
          f"{len(divergent) - len(unexpected)} pinned divergence(s)"
          + (f"; UNEXPECTED: {unexpected[:10]}" if unexpected else ""))
    if moved:
        print(f"pinned text moved: {moved}")
    if gone:
        print(f"pinned divergence(s) converged or vanished: {gone}")
    return 1 if (unexpected or moved or gone) else 0


if __name__ == "__main__":
    sys.exit(main())

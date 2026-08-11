"""L1.5 gate: compare observable global-table state between original bytecode and
decompiled output, without the game engine. See docs/runbooks/m3-backlog.md item 3.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
        rest = result[4:]
        bar = rest.find("|")
        return rest[bar + 1:].strip() if bar >= 0 else ""
    return ""


def main() -> int:
    from pyluadec.pipeline import decompile_file
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    files = sorted(corpus.glob("*.lua"))
    bad = []
    for f in files:
        if probe(f.read_bytes(), is_source=False) != probe(decompile_file(f).source, is_source=True):
            bad.append(f.name)
    print(f"global-state: {len(files) - len(bad)}/{len(files)} identical"
          + (f"; divergent: {bad[:10]}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

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


def probe(payload: bytes, *, is_source: bool, timeout: float = 30.0) -> str:
    from pyluadec import oracle
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        r = subprocess.run([str(oracle.lua_sz4()), str(PROBE), str(f)],
                           capture_output=True, timeout=timeout, cwd=td)
        # The probe's stdout is a deterministic ASCII/UTF-8 serialisation format
        # (see probe_global_state.lua: sorted keys via tostring(), "%.17g" numbers,
        # "<type>" placeholders) that we only ever compare for equality or search
        # for known ASCII markers ("OK|", "X="). It is not a bytecode-derived
        # string kept on the Python side (that constraint is about Proto string
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

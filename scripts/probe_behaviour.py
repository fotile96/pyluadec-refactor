"""L1.75 gate: compare observable *behaviour* between original bytecode and
decompiled output by invoking the global functions each chunk defines under a
stubbing environment.

The Lua side is `scripts/probe_behaviour.lua`; that file is the source of truth
for the trace format, the event budget and the stub-return policy. This module
only runs it, refuses to turn a probe-side failure into a comparable value, and
reduces a trace to a digest.

See docs/runbooks/m3-backlog.md for the L1.5 probe this deepens and the
measured reason its payload was too shallow to be worth much.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Run as `uv run python scripts/probe_behaviour.py`, sys.path[0] is scripts/,
# not the repo root, so `scripts.probe_common` would not resolve. Imported as a
# module by the tests it already resolves and this is a no-op.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.probe_common import adjudicate_pins  # noqa: E402

PROBE = ROOT / "scripts" / "probe_behaviour.lua"

# Every result the probe script is allowed to produce starts with one of these.
# Anything else means the probe itself did not run to completion, and comparing
# two such results would be comparing two failures, not two program behaviours.
# This is the L1.5 probe's hardest-won lesson: it shipped once with every
# probe-side failure returning "", which compared equal on all 229 files and
# passed a completely dead gate.
_MARKERS = (b"PROBE1|", b"LOADFAIL|")


class ProbeError(RuntimeError):
    """The probe did not produce a usable result (crash, non-zero exit, or
    unrecognisable stdout). Never silently turned into a comparable value."""


def probe_raw(payload: bytes, *, is_source: bool, timeout: float = 120.0) -> bytes:
    """Run the behaviour probe over one chunk and return its raw stdout.

    Bytes, not str: the trace embeds string constants straight from the corpus,
    which is Japanese game text. Nothing here decodes them -- the digest is
    taken over the bytes, so no decoding policy can affect what the gate
    compares. (This said "and frequently not UTF-8"; CLAUDE.md records that as
    measured-FALSE -- 49063 constants, 0 non-UTF-8. The reason is the red line,
    not the encoding. M5 task 9 round 1.)
    """
    from pyluadec import oracle
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / ("t.lua" if is_source else "t.luac")
        f.write_bytes(payload)
        # stdin=DEVNULL, not inherited: a chunk that calls io.read() would
        # otherwise block on whatever the caller's stdin happens to be (a
        # terminal, when the CLI is run by hand), and a probe that hangs is a
        # gate that never reports.
        r = subprocess.run([str(oracle.lua_sz4()), str(PROBE), str(f)],
                           capture_output=True, stdin=subprocess.DEVNULL,
                           timeout=timeout, cwd=td)
    if r.returncode != 0:
        raise ProbeError(
            f"probe exited {r.returncode} (is_source={is_source}, "
            f"probe={PROBE}); stderr={r.stderr.decode('utf-8', 'replace')!r}; "
            f"stdout={r.stdout[:400].decode('utf-8', 'replace')!r}")
    if not r.stdout.startswith(_MARKERS):
        raise ProbeError(
            f"probe produced an unrecognisable result (is_source={is_source}); "
            f"expected one of {[m.decode() for m in _MARKERS]}; "
            f"stdout={r.stdout[:400].decode('utf-8', 'replace')!r}; "
            f"stderr={r.stderr.decode('utf-8', 'replace')!r}")
    return r.stdout


def digest(trace: bytes) -> str:
    """The comparison unit. A full trace has a median of 33,068 B and the
    corpus total is 13,606,371 B (measured 2026-08-12, both sides), which is
    not something to hold 458 of in memory or to print into a test failure;
    the trace itself is only materialised when two digests differ."""
    return hashlib.sha256(trace).hexdigest()


def header(trace: bytes) -> tuple[str, int]:
    """`(status, event_count)` from line 1. status is OK / CAP / INSN, or
    LOADFAIL with a count of -1 (a chunk that did not load recorded nothing)."""
    line = trace.split(b"\n", 1)[0]
    parts = line.split(b"|")
    if parts[0] == b"LOADFAIL":
        return "LOADFAIL", -1
    return parts[1].decode("ascii"), int(parts[2])


def invocation_gap(trace: bytes) -> list[bytes]:
    """Names with a `G|<name>|<function#...>` event whose LAST write leaves
    them holding a function, but with no matching `I|<name>` event -- i.e. a
    global the chunk defined as a function that the invocation loop never
    called, on a run that finished on its own (status "OK").

    Only asserted for "OK" runs: a "CAP"/"INSN" run can legitimately truncate
    the invocation loop partway through (or before it even starts, if the cap
    is hit inside the chunk's own top-level body), so a gap there is expected,
    not a defect.

    Exists to close a real hole in `test_corpus_reach_is_not_vacuous`: that
    test's `assert n > 0` is satisfied by `config.lua`'s 3 bookkeeping events
    (it errors before defining anything) with no invocation at all, so a bug
    that silently broke every `pcall(envfields[k])` in the probe's own
    invocation loop -- e.g. always short-circuiting to the next name -- would
    leave `events > 300_000` and `CAP > 100` both green on the 97 files that
    finish as "OK" (the 132 "CAP" files would not obviously look different
    either, since most of their events come from inside the chunk body, not
    the invocation loop). Falsified by neutering the invocation loop in
    `probe_behaviour.lua` and confirming this check (not the existing
    non-vacuity assert) is what catches it -- see the M4 task 10 round-1
    report.

    Only the LAST write per name is consulted (not "any write"): a name
    written as a function and then overwritten with a non-function before the
    chunk finishes must not be flagged, since the invocation loop -- which
    enumerates `envfields` after the chunk runs -- correctly never calls it
    either.
    """
    st, _ = header(trace)
    if st != "OK":
        return []
    last_is_function: dict[bytes, bool] = {}
    invoked: set[bytes] = set()
    for line in trace.split(b"\n")[1:]:
        if not line:
            continue
        parts = line.split(b"|")
        if parts[0] == b"G" and len(parts) >= 3:
            last_is_function[parts[1]] = parts[2].startswith(b"<function#")
        elif parts[0] == b"I":
            invoked.add(parts[1])
    written = {name for name, is_fn in last_is_function.items() if is_fn}
    return sorted(written - invoked)


def dump_mismatch(name: str, orig: bytes, dec: bytes, where: Path) -> Path:
    """Write both traces side by side for a diverging file and return the
    directory. Only ever called on mismatch -- the traces are large."""
    where.mkdir(parents=True, exist_ok=True)
    (where / f"{name}.original.trace").write_bytes(orig)
    (where / f"{name}.decompiled.trace").write_bytes(dec)
    return where


def first_difference(orig: bytes, dec: bytes) -> tuple[int, bytes, bytes]:
    """`(line number, original line, decompiled line)` for the first differing
    trace line, as raw bytes -- the same type the trace itself is in.

    Pins (`EXPECTED_DIVERGENCE` below) are matched against this return value,
    so it has to stay bytes: decoding first (as an earlier version of this
    function did, with errors="replace") would make a pin adjudication-proof
    against a class of bug where the divergent bytes move but happen to decode
    to the same replacement text -- e.g. two different undecodable byte runs
    that both become U+FFFD. Both pins currently in EXPECTED_DIVERGENCE are
    pure ASCII, so this was never observed, but pinning bytes costs nothing and
    closes the gap on principle. Decode only at the point of display (see
    `dump_mismatch`, which writes the full raw traces to files, and the CLI's
    print statements, which never print this tuple's contents directly)."""
    a = orig.split(b"\n")
    b = dec.split(b"\n")
    for i in range(max(len(a), len(b))):
        la = a[i] if i < len(a) else b"<end of trace>"
        lb = b[i] if i < len(b) else b"<end of trace>"
        if la != lb:
            return (i + 1, la, lb)
    return (0, b"", b"")


# The corpus files whose original and decompiled behaviour traces do NOT agree,
# pinned as the exact (original, decompiled) FIRST DIFFERING LINE, so that a
# changed message, a converged pair or a vanished file all fail the gate.
# Re-measured 2026-08-14 (M6 task 12) over all 229 files: 228 agree
# byte-for-byte, this 1 does not, and it was adjudicated to a known, documented
# cause rather than to a decompiler defect.
#
# snr_mainmenu.lua was the second entry and was DELETED here because its pair
#   converged. Deletion was forced, not chosen: `probe_common.adjudicate_pins`
#   reports a converged pin as `gone`, main() returns 1 on it and the gate
#   asserts it empty. It was the getobjname naming artifact of the fallback's
#   `__pld_R` box model: the original does `GETTABLE 6 6 "library"`
#   immediately followed by `ADD 5 5 6`, so ldebug.c's kname() finds a STRING
#   constant and says `field 'library'`, whereas the fallback's
#   `__pld_R[5] = __pld_R[5] + __pld_R[6]` gives kname() a NUMBER key and it
#   says `field '?'`.
#
#   What changed in M6 task 12 is NOT that the chunk certifies -- round-1
#   correction: this comment first said task 12 "lifted that chunk's `main` to
#   `L3`, so it no longer ships through the box model at all", and BOTH halves
#   are false. `snr_mainmenu.lua:main` is `L1` (`mismatch: code at root/7`) and
#   the file still emits `__pld_R` on 1974 of its 3325 lines, 18 of them the
#   very `["library"]` lines above. The file moved from whole-file fallback to
#   HYBRID (3220/4782 box-model lines before, 1974/3325 after), and the
#   *specific* proto on the failing path now ships structured text, so both
#   sides reach the same `GETTABLE` with a string key.
#
#   The attribution matters too: closure-capture classification ALONE moves
#   nothing here. Measured by a source-level 4-way ablation over all 229 files
#   (checking out BASE/HEAD `names.py` and `freereg.py` independently), the
#   shipped artifact is byte-identical to BASE under either fix on its own;
#   only both together change anything, and they change exactly three files.
#   The same convergence removed three of the four pins in
#   `probe_global_state.py`.
#
# snr_novel.lua -- table iteration order. The two traces are the SAME MULTISET
#   of 43 lines in a different order (asserted in the test), and the file's
#   only `pairs` loop is at main-chunk-subproto pcs 24..37 (`GETGLOBAL pairs`,
#   `TFORLOOP 0 2`), iterating `<upvalue>.layerNumber`. The original builds
#   that table with `NEWTABLE 1 0 23` (a 29-entry hash-size hint) followed by
#   29 SETTABLEs; the fallback emits a bare `{}` constructor, so luac gives it
#   `NEWTABLE ... 0 0` and the 29 inserts grow the node array by rehash
#   instead. Different node array, different `next()` order. This is backlog
#   item 5 (table internal layout), now with runtime evidence.
EXPECTED_DIVERGENCE: dict[str, tuple[bytes, bytes]] = {
    "snr_novel.lua": (
        b'C|comLayerLoadFalse|2|58,"novel/novel_3_ad.gim"',
        b'C|comLayerLoadFalse|2|64,"novel/novel_3_cb.gim"'),
}


def run_corpus(corpus: Path, *, jobs: int = 8):
    """Yield `(name, orig_trace, dec_trace)` for every corpus file."""
    from pyluadec.pipeline import decompile_file
    files = sorted(corpus.glob("*.lua"))
    srcs = [(f, decompile_file(f).source) for f in files]

    def one(item):
        f, src = item
        return (f.name,
                probe_raw(f.read_bytes(), is_source=False),
                probe_raw(src, is_source=True))

    with ThreadPoolExecutor(max_workers=jobs) as ex:
        yield from ex.map(one, srcs)


def main(argv: list[str] | None = None) -> int:
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    scratch = ROOT / "build" / "behaviour-mismatch"
    total = events = 0
    divergent: dict[str, tuple[bytes, bytes]] = {}
    for name, orig, dec in run_corpus(corpus):
        total += 1
        events += header(orig)[1]
        if orig == dec:
            continue
        _, a, b = first_difference(orig, dec)
        divergent[name] = (a, b)
        if name not in EXPECTED_DIVERGENCE:
            dump_mismatch(name, orig, dec, scratch)
    # The CLI knows about the pins, so a clean run prints a clean line and
    # returns 0. (The L1.5 CLI did not, and printed a red 225/229 while its
    # own test suite was green -- fixed in the same change as this file.)
    unexpected, moved, gone = adjudicate_pins(divergent, EXPECTED_DIVERGENCE)
    print(f"behaviour: {total - len(divergent)}/{total} identical, "
          f"{len(divergent) - len(unexpected)} pinned divergence(s), "
          f"{events} recorded events on the original side"
          + (f"; UNEXPECTED: {unexpected[:10]} (traces in {scratch})"
             if unexpected else ""))
    if moved:
        print(f"pinned evidence moved: {moved} (traces in {scratch})")
        for n in moved:
            dump_mismatch(n, *_reprobe(corpus, n), scratch)
    if gone:
        print(f"pinned divergence(s) converged or vanished: {gone}")
    return 1 if (unexpected or moved or gone) else 0


def _reprobe(corpus: Path, name: str) -> tuple[bytes, bytes]:
    from pyluadec.pipeline import decompile_file
    f = corpus / name
    return (probe_raw(f.read_bytes(), is_source=False),
            probe_raw(decompile_file(f).source, is_source=True))


if __name__ == "__main__":
    sys.exit(main())

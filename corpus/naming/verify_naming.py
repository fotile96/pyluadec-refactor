"""The naming-alignment guards, as one command (M8 naming alignment).

Three checks, each refusing loudly (non-zero exit, victim named):

* **P1 -- byte identity.**  Every ``corpus/final/*.lua`` recompiles (via
  ``luac_sz4 -s``) to bytecode byte-identical to its original, modulo the
  ``linedefined``/``lastlinedefined`` fields (the survey §8.2 normalizer,
  transcribed here -- this is the same guard the proposal channel's A5
  ran, now standing).  Local names never enter stripped bytecode, so any
  naming change that altered name resolution (a local shadowing a
  referenced global flips GETGLOBAL to MOVE; a keyword breaks the
  compile) breaks this equality and is named per file.
* **Fixed point.**  ``name_map.jsonl`` equals a fresh harvest (the
  generator's own ``--check``, invoked here so one command covers both).
* **Flag completeness (P4).**  Every table row inside one of the 6 M6
  defect zones (or the path-level intentional edit) carries the
  ``defect-zone`` flag; every row inside a proposal site carries
  ``proposal-site``.  Measured content today: 0 such rows -- the
  readable surface does not intersect the defect protos -- and the check
  is what keeps that sentence true as the table evolves.

``--tamper`` demonstrates all three guards dying on purpose (the neuter
proof, P6): it flips one byte in a COPY of each input and runs the same
predicate, expecting each to fail and name its victim.  Nothing under
``/Users/fotile96/pyluadec`` or ``/Users/fotile96/Zndnovel`` is touched.

Usage:
    PYLUADEC_CORPUS_DIR=<229-file bytecode corpus> \
    uv run python corpus/naming/verify_naming.py [--tamper]
"""
from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from harvest_naming import DEFECT_ZONES, PROPOSAL_SITES, render  # noqa: E402

from pyluadec import oracle                                # noqa: E402


def normalize(data: bytes) -> bytes:
    """Survey §8.2: zero ``linedefined``/``lastlinedefined`` everywhere in
    the sz4 dump, in place. Name-free fields only -- everything else must
    already be equal for the caller to report identity."""
    buf = bytearray(data)
    pos = 12

    def rd_int() -> int:
        nonlocal pos
        v = struct.unpack_from('<i', buf, pos)[0]
        pos += 4
        return v

    def rd_string() -> None:
        nonlocal pos
        # NB: bind the length FIRST. `pos += rd_int()` would load `pos`
        # before the call and store stale_pos + length, silently re-reading
        # the 4 size bytes as payload on every string (found by diffing
        # against the survey recipe after config.lua desynced).
        n = rd_int()
        pos += n

    def func() -> None:
        nonlocal pos
        rd_string()
        struct.pack_into('<i', buf, pos, 0); pos += 4
        struct.pack_into('<i', buf, pos, 0); pos += 4
        pos += 4
        n_code = rd_int()      # bind first: see rd_string's NB
        pos += 4 * n_code
        n_const = rd_int()
        for _ in range(n_const):
            t = buf[pos]; pos += 1
            if t == 0:
                pass
            elif t == 1:
                pos += 1
            elif t == 3:
                pos += 8
            elif t == 4:
                rd_string()
            else:
                raise ValueError(t)
        for _ in range(rd_int()):
            func()
        n_line = rd_int()
        pos += 4 * n_line
        for _ in range(rd_int()):
            rd_string(); pos += 8
        for _ in range(rd_int()):
            rd_string()

    func()
    assert pos == len(buf), (pos, len(buf))
    return bytes(buf)


def check_p1(final_dir: Path) -> list[str]:
    """Victim file names whose recompiled final is not byte-identical (mod
    line fields) to the original. Also names compile failures."""
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    bad: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "rt.bin"
        for f in sorted(corpus.glob("*.lua")):
            src = final_dir / f.name
            if not src.is_file():
                bad.append(f"{f.name}: no final")
                continue
            r = subprocess.run([str(oracle.luac_sz4()), "-s", "-o",
                                str(out), str(src)], capture_output=True)
            if r.returncode != 0:
                bad.append(f"{f.name}: does not compile")
                continue
            a, b = out.read_bytes(), f.read_bytes()
            if len(a) != len(b):
                bad.append(f"{f.name}: size {len(a)} vs original {len(b)}")
            elif normalize(a) != normalize(b):
                bad.append(f"{f.name}: bytecode differs mod line fields")
    return bad


def check_fixed_point() -> list[str]:
    """The map must equal a fresh harvest (empty = it does)."""
    import harvest_naming as H
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    stage1 = Path(os.environ.get(
        "PYLUADEC_STAGE1_DIR",
        "/Users/fotile96/pyluadec/post_process/stage1_output"))
    rows, _report = H.harvest(corpus, stage1)
    committed = (HERE / "name_map.jsonl").read_bytes() \
        if (HERE / "name_map.jsonl").is_file() else b""
    if committed == render(rows):
        return []
    return [f"name_map.jsonl: {len(committed)} committed bytes vs "
            f"{len(render(rows))} regenerated"]


def check_flags(map_file: Path | None = None) -> list[str]:
    """P4: rows inside flagged zones must carry the flag (empty = clean)."""
    import json
    victims: list[str] = []
    p = map_file or (HERE / "name_map.jsonl")
    with p.open("r", encoding="ascii") as fh:
        for line in fh:
            row = json.loads(line)
            for zone in DEFECT_ZONES:
                if row["file"] == zone[0] and (
                        row["path"] == zone[1]
                        or row["path"].startswith(zone[1] + "_")):
                    if "defect-zone" not in row["flags"]:
                        victims.append(f"{row['file']}:{row['path']} "
                                       f"reg {row['reg']} lacks defect-zone")
            for site in PROPOSAL_SITES:
                if row["file"] == site[0] and (
                        row["path"] == site[1]
                        or row["path"].startswith(site[1] + "_")):
                    if "proposal-site" not in row["flags"]:
                        victims.append(f"{row['file']}:{row['path']} "
                                       f"reg {row['reg']} lacks proposal-site")
    return victims


def _tamper_demo() -> None:
    """P6: prove each guard dies on a one-byte flip in a COPY."""
    # P1: corrupt one final's name (same length, different identifier) and
    # expect the recompile to disagree with the original. The FULL final
    # tree is copied so the only reported victim is the tampered file --
    # the demo must fail on the name flip, not on missing files.
    import shutil
    with tempfile.TemporaryDirectory() as td:
        fake_final = Path(td) / "final"
        shutil.copytree(ROOT / "corpus" / "final", fake_final)
        victim = "snr_crd_103.lua"
        blob = bytearray((fake_final / victim).read_bytes())
        idx = blob.find(b"card_103_s6s_150_sel_step11")
        assert idx >= 0
        blob[idx + 2] = ord("X")     # cadr_... -- a name the original lacks
        (fake_final / victim).write_bytes(bytes(blob))
        bad = check_p1(fake_final)
        # The flip un-declares the local: every later reference to the
        # original spelling recompiles as a GETGLOBAL (new string constant,
        # new opcode), so the honest victim line is either the size or the
        # byte difference -- both are the catch, measured both ways here.
        assert len(bad) == 1 and victim in bad[0], bad
        print(f"tamper P1: refused and named -- {bad[0]}")

    # Fixed point: append one row to a copy and expect the drift check.
    with tempfile.TemporaryDirectory() as td:
        import harvest_naming as H
        import shutil
        fake = Path(td) / "name_map.jsonl"
        shutil.copy(HERE / "name_map.jsonl", fake)
        with fake.open("ab") as fh:
            fh.write(b'{"anchor": 0, "file": "zzz.lua", "flags": [], '
                     b'"kind": "function", "name": "tampered", '
                     b'"path": "main", "reg": 0}\n')
        real = (HERE / "name_map.jsonl").read_bytes()
        (HERE / "name_map.jsonl").rename(Path(td) / "stashed")
        shutil.copy(fake, HERE / "name_map.jsonl")
        try:
            bad = check_fixed_point()
            assert bad, "fixed-point guard did not fire"
            print(f"tamper fixed point: refused and named -- {bad[0]}")
        finally:
            (HERE / "name_map.jsonl").unlink()
            Path(td, "stashed").rename(HERE / "name_map.jsonl")
            assert (HERE / "name_map.jsonl").read_bytes() == real

    # Flags: append an unflagged row INSIDE a defect zone to a copy and
    # expect the completeness check to name it. (No committed row sits in
    # a zone today -- measured -- so the tampered row is the only way this
    # predicate has ever been observed firing.)
    with tempfile.TemporaryDirectory() as td:
        import shutil
        fake = Path(td) / "name_map.jsonl"
        shutil.copy(HERE / "name_map.jsonl", fake)
        with fake.open("ab") as fh:
            fh.write(b'{"anchor": 0, "file": "snr_music.lua", "flags": [], '
                     b'"kind": "param", "name": "tampered", '
                     b'"path": "main_3", "reg": 0}\n')
        bad = check_flags(fake)
        assert bad, "flag guard did not fire"
        print(f"tamper flags: refused and named -- {bad[0]}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tamper", action="store_true",
                    help="run the neuter demonstrations and exit")
    args = ap.parse_args(argv)

    if args.tamper:
        if "PYLUADEC_CORPUS_DIR" not in os.environ:
            print("PYLUADEC_CORPUS_DIR is unset", file=sys.stderr)
            return 2
        _tamper_demo()
        print("tamper demos: every guard fired and named its victim")
        return 0

    corpus = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not corpus or not Path(corpus).is_dir():
        print("PYLUADEC_CORPUS_DIR is unset or not a directory",
              file=sys.stderr)
        return 2

    ok = True

    bad = check_p1(ROOT / "corpus" / "final")
    n_files = len(list(Path(corpus).glob("*.lua")))
    if bad:
        ok = False
        for v in bad[:10]:
            print(f"P1 FAIL: {v}")
        if len(bad) > 10:
            print(f"... and {len(bad) - 10} more")
    else:
        print(f"P1: {n_files}/{n_files} finals byte-identical to the "
              f"originals mod line fields")

    bad = check_fixed_point()
    if bad:
        ok = False
        for v in bad:
            print(f"FIXED POINT FAIL: {v}")
    else:
        print("name_map.jsonl: fixed point of the harvest")

    bad = check_flags()
    if bad:
        ok = False
        for v in bad[:10]:
            print(f"FLAG FAIL: {v}")
    else:
        print("flags: every zone row carries its flag (0 rows today)")

    print("NAMING VERIFY:", "OK" if ok else "REFUSED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

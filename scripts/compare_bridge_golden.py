"""Compare new ingest layer against golden (old bridge dump + luac listings)."""
import gzip, json, re, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "corpus" / "golden"
LISTING_HEAD_RE = re.compile(
    r"^(?:main|function) <[^>]*:(\d+),(\d+)> \((\d+) instructions?, \d+ bytes at 0x[0-9a-f]+\)$")
LISTING_META_RE = re.compile(
    r"^(\d+)(\+?) params?, (\d+) slots?, (\d+) upvalues?, "
    r"(\d+) locals?, (\d+) constants?, (\d+) functions?$")

def _diff(path, field, old, new, verdict="unexpected"):
    return {"proto_path": path, "field": field,
            "old": repr(old), "new": repr(new), "verdict": verdict}

def _cmp_proto(old: dict, new, path: str, out: list):
    raw_old = [ins["raw_instr"] for ins in old["code"]]
    if list(new.code) != raw_old:
        out.append(_diff(path, "code", raw_old, list(new.code)))
    if old["numparams"] != new.numparams:
        out.append(_diff(path, "numparams", old["numparams"], new.numparams))
    if bool(old["is_vararg"]) != bool(new.is_vararg & 1):
        out.append(_diff(path, "is_vararg", old["is_vararg"], new.is_vararg))
    if len(old["constants"]) != len(new.constants):
        out.append(_diff(path, "constants.len", len(old["constants"]), len(new.constants)))
    else:
        from pyluadec.ingest.proto import LuaNumber
        for i, (oc, nc) in enumerate(zip(old["constants"], new.constants)):
            if isinstance(nc, LuaNumber):
                ok = isinstance(oc, (int, float)) and not isinstance(oc, bool) and float(oc) == nc.value
                # Self-consistency invariant, independent of any oracle: the
                # raw 8-byte payload must decode (native byte order) to the
                # same value LuaNumber already parsed it as.
                expected_payload = struct.pack("=d", nc.value)
                if expected_payload != nc.payload:
                    out.append(_diff(f"{path}/k{i}", "const.payload", expected_payload, nc.payload))
            elif isinstance(nc, bytes):
                try:
                    ok = oc == nc.decode("utf-8")
                except UnicodeDecodeError:
                    out.append(_diff(f"{path}/k{i}", "const.encoding", oc, nc, "expected"))
                    continue
            else:
                ok = type(oc) is type(nc) and oc == nc
            if not ok:
                out.append(_diff(f"{path}/k{i}", "const", oc, nc))
    old_ups = old["upvalues"]
    try:
        new_ups = [u.decode("utf-8") if u is not None else None for u in new.upvalues]
    except UnicodeDecodeError:
        out.append(_diff(path, "upvalues.encoding", old_ups, new.upvalues, "expected"))
    else:
        if old_ups != new_ups:
            out.append(_diff(path, "upvalues", old_ups, new_ups))
    if len(old["subprotos"]) != len(new.subprotos):
        out.append(_diff(path, "subprotos.len", len(old["subprotos"]), len(new.subprotos)))
    else:
        for i, (os_, ns) in enumerate(zip(old["subprotos"], new.subprotos)):
            _cmp_proto(os_, ns, f"{path}/{i}", out)

def _listing_headers(listing: str) -> list[dict]:
    """Per-function header metadata, in listing order (main first).

    Each function's header is exactly two consecutive lines; the metadata line
    immediately follows the `main <...>` / `function <...>` line.
    """
    lines = listing.splitlines()
    funcs = []
    for i, line in enumerate(lines):
        m = LISTING_HEAD_RE.match(line)
        if not m:
            continue
        if i + 1 >= len(lines):
            raise ValueError(f"header line {i} has no metadata line following it")
        m2 = LISTING_META_RE.match(lines[i + 1])
        if not m2:
            raise ValueError(f"unparsable metadata line after header: {lines[i + 1]!r}")
        funcs.append({
            "linedefined": int(m.group(1)),
            "lastlinedefined": int(m.group(2)),
            "n_instructions": int(m.group(3)),
            "numparams": int(m2.group(1)),
            "is_vararg_marker": m2.group(2) == "+",
            "maxstacksize": int(m2.group(3)),
            "nups": int(m2.group(4)),
            "n_locals": int(m2.group(5)),
            "n_constants": int(m2.group(6)),
            "n_functions": int(m2.group(7)),
        })
    return funcs

def _cmp_listing_header(h: dict, p, path: str, out: list):
    checks = [
        ("linedefined", h["linedefined"], p.linedefined),
        ("lastlinedefined", h["lastlinedefined"], p.lastlinedefined),
        ("n_instructions", h["n_instructions"], len(p.code)),
        ("numparams", h["numparams"], p.numparams),
        ("maxstacksize", h["maxstacksize"], p.maxstacksize),
        ("nups", h["nups"], p.nups),
        ("n_locals", h["n_locals"], len(p.locvars)),
        ("n_constants", h["n_constants"], len(p.constants)),
        ("n_functions", h["n_functions"], len(p.subprotos)),
    ]
    for field, want, got in checks:
        if want != got:
            out.append(_diff(path, f"listing.{field}", want, got))
    # luac prints a trailing '+' on the param count iff VARARG_ISVARARG is set
    if h["is_vararg_marker"] != bool(p.is_vararg & 2):
        out.append(_diff(path, "listing.is_vararg", h["is_vararg_marker"], p.is_vararg))

def _flatten(p):
    yield p
    for s in p.subprotos:
        yield from _flatten(s)

def compare_file(name: str, corpus_dir: Path) -> list:
    from pyluadec.ingest import load_file
    new = load_file(Path(corpus_dir) / name)
    with gzip.open(GOLDEN / "proto_dump" / (name + ".json.gz"), "rt", encoding="utf-8") as fh:
        old = json.load(fh)
    out: list = []
    _cmp_proto(old, new, name, out)
    listing = (GOLDEN / "listing" / (name + ".txt")).read_text(encoding="utf-8")
    listed = _listing_headers(listing)
    protos = list(_flatten(new))
    if len(listed) != len(protos):
        out.append(_diff(name, "listing.func_count", len(listed), len(protos)))
    else:
        for i, (h, proto) in enumerate(zip(listed, protos)):
            _cmp_listing_header(h, proto, f"{name}#func{i}", out)
    return out

def compare_corpus(corpus_dir: Path) -> list:
    manifest = json.loads((GOLDEN / "manifest.json").read_text())
    report = []
    for name in sorted(manifest):
        report.extend(compare_file(name, Path(corpus_dir)))
    return report

if __name__ == "__main__":
    import os
    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    report = compare_corpus(corpus)
    outp = ROOT / "corpus" / "discrepancies.json"
    outp.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    unexpected = [d for d in report if d["verdict"] == "unexpected"]
    print(f"{len(report)} discrepancies ({len(unexpected)} unexpected) -> {outp}")
    sys.exit(1 if unexpected else 0)

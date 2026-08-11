"""Per-proto L3 certification with wrapper isolation, and chunk assembly (spec §4, §5).

A proto certifies L3 iff the structured print of ITS OWN SUBTREE recompiles to a
proto matching the original under the normalization ladder. Certification is
per-proto so one unstructurable function cannot poison its siblings' levels;
the shipped chunk source is structured only when the ROOT certifies (which
covers the whole tree), otherwise the semantically-exact fallback chunk ships.
No unverified structured code is ever returned.

Why per-proto rather than chunk-level all-or-nothing (quantified 2026-08-10):
only 93/229 corpus files have their ENTIRE proto tree inside the structurable
subset -- a chunk-level gate would cap the exit metric at ~13.1% (unique-proto
basis). Per-proto subtree certification lifts that ceiling because a
straight-line child function certifies independently even when its parent
contains a `while` loop the recognizer refuses. Ledger level (per proto) and
shipped artifact (per chunk) are therefore deliberately decoupled: the level
is a proof record, the artifact is a conservative file-level choice.

The ceiling that per-proto certification actually has is **printability**:
1170/1478 unique proto shapes (79.16%) and 1636/1944 occurrences (84.16%)
print their whole subtree, and only a proto that prints can certify. Achieved
at M3 exit: 1112/1478 (75.2%) unique, 1577/1944 (81.12%) occurrences. (An
earlier planning estimate of "~80.3%" was quoted here as the ceiling; it
reproduces on neither basis, and 81.12% occurrences already exceeds it. The
measurement scripts for all three rows are inlined in
`docs/runbooks/structured-pipeline.md`, "Current capability boundary".)

## Memoization key (round-1 fix, superseded in M3 task 8)

`emit_certified_chunk` memoizes `certify_proto`'s verdict. The obvious key,
`verify.ledger.structural_hash`, is NOT sufficient: it is a *code-shape* key
that deliberately omits `source`, `linedefined`/`lastlinedefined`,
`lineinfo`, `locvars`, and upvalue names, all of which `compare_protos`
checks. Two protos can therefore share a `structural_hash` while genuinely
certifying differently, and whichever is processed first would win for both,
silently.

Round 1 handled this by asserting the tree had uniform debug-completeness
(true of any real `load_file`/`load_bytes` dump, which is `-s`-stripped or
not for its entire tree). That assertion had a documented false positive and
started firing on ordinary unstripped input once this module acquired a
production caller. It is gone: the memo is now keyed on `_memo_key` =
`structural_hash` + `_debug_fingerprint`, which together cover every field
`compare_protos` examines, so equal keys imply equal verdicts by
construction and no assumption about the caller's tree is needed. See
`_debug_fingerprint`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pyluadec.emit.lua import print_chunk, _print_proto_body
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.ingest import Proto, load_bytes
from pyluadec import oracle
from pyluadec.sir.build import StructureError
from pyluadec.structure.fallback import emit_chunk
from pyluadec.verify.certify import certify_l3
from pyluadec.verify.ledger import structural_hash
from pyluadec.verify.normalize import Mismatch, NORMALIZATIONS, compare_protos


@dataclass(frozen=True)
class ProtoCert:
    level: str                       # "L3" | "L1"
    rung: int | None
    mismatches: tuple[Mismatch, ...]
    # The exact bytes that were compiled and compared to reach this verdict,
    # for a chunk-root `L3` certification; `None` otherwise (non-root
    # certifications compile a wrapper, not a shippable chunk, and a non-`L3`
    # verdict has nothing certified to hand out). One caveat on "otherwise":
    # a descendant sharing the root's `_memo_key` would be handed the root's
    # entry, `source` included. That cannot happen -- `structural_hash` folds
    # subprotos recursively, so a proto cannot equal a strict descendant of
    # itself (well-founded on depth) absent a hash collision -- and nothing
    # reads `source` off a non-root cert. Stated because the field comment
    # would otherwise be a stronger promise than the code makes.
    # `emit_certified_chunk`
    # ships THIS object rather than calling `print_chunk` a second time, so
    # "shipped == certified" holds by construction rather than by the
    # printer happening to be deterministic.
    source: bytes | None = None


@dataclass(frozen=True)
class ChunkOutcome:
    source: bytes
    certs: dict[str, ProtoCert]


_L1 = ProtoCert(level="L1", rung=None, mismatches=())


def _debug_fingerprint(p: Proto) -> str:
    """Hash of exactly the fields `compare_protos` checks that
    `structural_hash` omits, recursively over the subtree.

    `structural_hash` is a *code-shape* key (see its own docstring): it folds
    in numparams/is_vararg/nups/maxstacksize/code/constants/subprotos and the
    upvalue COUNT, and deliberately drops `source`, `linedefined`,
    `lastlinedefined`, `lineinfo`, `locvars`, and upvalue NAMES.
    `compare_protos` checks every one of those. So two protos can share a
    structural hash and still certify differently, and memoizing one's verdict
    for the other would be silently wrong.

    `structural_hash(p) + _debug_fingerprint(p)` together cover every field
    `compare_protos` examines, which makes the memoization in
    `emit_certified_chunk` sound by construction rather than by an assumption
    about the caller. What the printed source looks like depends only on
    fields `structural_hash` already covers, and what the comparison accepts
    depends only on those two together -- so equal keys imply equal verdicts.

    ## Why this replaced the round-1 tree-uniformity assertion (M3 task 8)

    Round 1 addressed the same hazard with a coarse `(has_locvars,
    has_upvalue_names, has_source)` signature and an assertion that every
    proto in the tree agreed on it -- sound only because a real dump is
    uniformly `-s`-stripped or not. Its own docstring flagged the false
    positive: an unstripped tree containing one function that declares no
    locals has legitimately-empty `locvars` for that proto, so the tree read
    as "mixed" and the assertion fired. That was harmless while
    `emit_certified_chunk` had no production caller; this task wired it into
    `pipeline.decompile_chunk`, at which point it became an AssertionError on
    ordinary unstripped input (the exact source tests/test_pipeline.py has
    always used). Keying the memo correctly removes both the false positive
    and the underlying unsoundness, rather than trading one for the other.
    """
    def view(q: Proto) -> dict:
        return {
            "source": q.source.hex() if q.source is not None else None,
            "linedefined": q.linedefined,
            "lastlinedefined": q.lastlinedefined,
            "lineinfo": list(q.lineinfo),
            "locvars": [[v.name.hex() if v.name is not None else None,
                         v.startpc, v.endpc] for v in q.locvars],
            "upvalues": [u.hex() if u is not None else None for u in q.upvalues],
            "subprotos": [view(s) for s in q.subprotos],
        }
    blob = json.dumps(view(p), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def certify_proto(proto: Proto, *, is_chunk_root: bool) -> ProtoCert:
    """Certify one proto's own subtree in isolation.

    `is_chunk_root=True`: the proto IS the chunk main -- its structured print
    already is a complete compilable chunk, so it is compiled and compared
    directly (via `certify_l3`, `strip=True` to match the golden dump path).

    `is_chunk_root=False`: the proto is nested. It is printed as its own
    subtree (`_print_proto_body`, depth=1, synthetic upvalue names `u0..u{n-1}`)
    and wrapped in scaffolding that declares those upvalues as locals and
    returns a function literal built from that body:

        local u0, u1, ...
        return function(l1_0, l1_1, ...)
        <body>
        end

    The wrapper's own main proto is discarded; only `.subprotos[0]` (the
    returned function literal) is compared against the original. The
    parameter names `l1_{i}` must match what `_print_proto_body(depth=1)`
    itself synthesizes for register i via `name_for(reg, 1)` -- both go
    through the same "l{depth}_{reg}" convention, so this is not duplicated
    formatting logic so much as the one place that convention is spelled
    out for code that isn't itself inside the printer.
    """
    if is_chunk_root:
        src = print_chunk(proto)
        if src is None:
            return _L1
        payload = src.encode()
        cert = certify_l3(proto, payload)
        return ProtoCert(cert.level, cert.rung, cert.mismatches,
                         payload if cert.level == "L3" else None)

    upval_names = tuple(f"u{i}" for i in range(proto.nups))
    try:
        body = _print_proto_body(proto, depth=1, upval_names=upval_names)
    except (StructureError, ReconstructError):
        return _L1
    params = ", ".join(f"l1_{i}" for i in range(proto.numparams))
    if proto.is_vararg & 2:
        params = params + (", ..." if params else "...")
    decls = ("local " + ", ".join(upval_names) + "\n") if upval_names else ""
    wrapper = f"{decls}return function({params})\n{body}end\n"
    try:
        recompiled = load_bytes(oracle.compile_source(wrapper.encode(), strip=True))
    except oracle.LuaCompileError:
        return _L1
    if len(recompiled.subprotos) != 1:
        return _L1
    candidate = recompiled.subprotos[0]
    last: tuple[Mismatch, ...] = ()
    for k in range(len(NORMALIZATIONS) + 1):
        diffs = compare_protos(proto, candidate, level=k)
        if not diffs:
            return ProtoCert("L3", k, ())
        last = tuple(diffs)
    return ProtoCert("L1", None, last)


def emit_certified_chunk(root: Proto) -> ChunkOutcome:
    """Certify every proto in `root`'s tree independently, then choose the
    shipped artifact: structured chunk source iff the ROOT certified L3
    (which, per `certify_proto`'s wrapper-isolation contract, implies every
    descendant printed and recompiled correctly as part of that same
    structured print -- `print_chunk` prints the whole tree inline at each
    CLOSURE site); the semantically-exact fallback chunk otherwise.

    Identical protos recurring within one chunk are certified once and the
    result is shared -- corpus functions frequently repeat verbatim (e.g.
    identical small helper closures), and certification's dominant cost is one
    `luac_sz4` subprocess per proto. "Identical" here means `_memo_key`:
    `structural_hash` (code shape) plus `_debug_fingerprint` (everything else
    `compare_protos` looks at). Together those cover every field the
    comparison examines, so equal keys imply equal verdicts by construction --
    see `_debug_fingerprint` for why keying on `structural_hash` alone was not
    enough, and for what replaced the round-1 assertion that used to stand in
    for this.
    """
    from pyluadec.pipeline import walk_proto_paths
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)

    memo: dict[tuple[str, str], ProtoCert] = {}
    certs: dict[str, ProtoCert] = {}
    # `main` is certified first and unconditionally, NOT because
    # walk_proto_paths's pre-order recursion plus dict insertion order
    # happens to put it first in `protos.items()` (true, but this does not
    # rely on it): relying on iteration order would make the "main
    # certified L3 => print succeeded" assertion below correct only by
    # coincidence if some future change reordered `protos` or introduced a
    # same-hash collision between `root` and one of its own descendants.
    root_key = _memo_key(root)
    memo[root_key] = certify_proto(root, is_chunk_root=True)
    certs["main"] = memo[root_key]
    for path, p in protos.items():
        if path == "main":
            continue
        k = _memo_key(p)
        if k not in memo:
            memo[k] = certify_proto(p, is_chunk_root=False)
        certs[path] = memo[k]

    # Ship the very bytes certification compiled and compared, NOT a second
    # `print_chunk(root)` call. Re-printing would make "shipped == certified"
    # depend on `print_chunk` being deterministic -- true today, and measured
    # (92/92 shipped artifacts re-print identically), but a property of the
    # printer rather than of this gate, and one no test here would notice
    # losing. Reusing `ProtoCert.source` makes the invariant structural.
    if certs["main"].level == "L3":
        certified = certs["main"].source
        assert certified is not None      # main certified L3 => print succeeded
        return ChunkOutcome(source=certified, certs=certs)
    return ChunkOutcome(source=emit_chunk(root), certs=certs)


def _memo_key(p: Proto) -> tuple[str, str]:
    return (structural_hash(p), _debug_fingerprint(p))

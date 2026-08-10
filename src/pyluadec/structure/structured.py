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
basis). Per-proto subtree certification has a ceiling of ~80.3%: a straight-
line child function certifies independently even when its parent contains a
`while` loop the recognizer refuses. Ledger level (per proto) and shipped
artifact (per chunk) are therefore deliberately decoupled: the level is a
proof record, the artifact is a conservative file-level choice.
"""
from __future__ import annotations

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


@dataclass(frozen=True)
class ChunkOutcome:
    source: bytes
    certs: dict[str, ProtoCert]


_L1 = ProtoCert(level="L1", rung=None, mismatches=())


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
        cert = certify_l3(proto, src.encode())
        return ProtoCert(cert.level, cert.rung, cert.mismatches)

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

    Identical (by `structural_hash`) protos recurring within one chunk are
    certified once and the result is shared -- corpus functions frequently
    repeat verbatim (e.g. identical small helper closures), and
    certification's dominant cost is one `luac_sz4` subprocess per proto.
    """
    from pyluadec.pipeline import walk_proto_paths
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    memo: dict[str, ProtoCert] = {}
    certs: dict[str, ProtoCert] = {}
    for path, p in protos.items():
        h = structural_hash(p)
        if h not in memo:
            memo[h] = certify_proto(p, is_chunk_root=(path == "main"))
        certs[path] = memo[h]
    if certs["main"].level == "L3":
        src = print_chunk(root)
        assert src is not None            # main certified L3 => print succeeded
        return ChunkOutcome(source=src.encode(), certs=certs)
    return ChunkOutcome(source=emit_chunk(root), certs=certs)

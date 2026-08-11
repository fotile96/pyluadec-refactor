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

## Round-1 fix: memoization's unstated debug-completeness invariant

`emit_certified_chunk` memoizes `certify_proto`'s verdict by
`verify.ledger.structural_hash`. That hash deliberately omits `locvars`
entirely and reduces `upvalues`/`source` to a bare count (see its own
docstring/`_structure_view`) -- it is a *code-shape* key, not a full-proto
key. `compare_protos`, by contrast, DOES check `locvars` (and
`_strip_lineinfo`'s normalization only blanks locvar *names*, not their
count/pc ranges -- see `verify/normalize.py`'s own docstring). So two protos
can share a `structural_hash` while genuinely certifying differently, and
whichever is processed first in the memo loop wins for both -- silently.

This is real but not reachable from any actual `load_file`/`load_bytes`
tree: a compiled dump is `-s`-stripped or not for its ENTIRE tree, uniformly
(there is no partial-strip mode), so within one real chunk every proto's
locvars/upvalue-names/source presence agrees, and a same-hash pair that
would genuinely disagree on `locvars` cannot arise. The invariant that makes
memoization safe is therefore "the tree has uniform debug-completeness",
not anything `structural_hash` itself guarantees -- so `emit_certified_chunk`
below asserts it explicitly rather than leaving it as an unstated assumption
a future caller (e.g. one handing in a synthesized or grafted tree) could
silently violate.
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


def _debug_shape(p: Proto) -> tuple[bool, bool, bool]:
    """Coarse per-proto debug-completeness signature: does it carry any
    locvar record, any named upvalue, and a non-null `source`.

    This is the cheapest predicate that actually captures the invariant
    `emit_certified_chunk`'s memoization relies on (see module docstring
    "Round-1 fix"): `structural_hash` folds in none of these three fields
    (not even a count, for locvars), yet `compare_protos` checks `locvars`
    directly and `_strip_lineinfo` only anonymizes locvar names -- it keeps
    their count and pc ranges. Two same-hash protos that disagree on any of
    these three booleans are exactly the case where memoizing one's verdict
    for the other could be wrong (proven by `dataclasses.replace`-grafting a
    stray `LocVar` onto an otherwise-identical, otherwise-stripped proto in
    the accompanying test -- same hash, genuinely different certify_proto
    verdict).

    A real compiled dump (`load_file`/`load_bytes`) is always uniformly
    `-s`-stripped or not for its ENTIRE tree -- there is no partial-strip
    mode -- so on any actual proto tree every node's signature is identical
    and this predicate never distinguishes them. It is intentionally a
    coarse presence check, not an exact-value comparison: a tree that is
    uniformly non-stripped but happens to contain one proto with zero
    declared locals (legitimately empty `locvars` even though debug info is
    present) would false-positive this predicate into "mixed shape" -- an
    over-eager but SAFE failure direction (loudly refusing to memoize rather
    than silently trusting a hash that doesn't cover the field in
    question), and one that does not occur on this project's actual corpus,
    which is uniformly stripped tree-wide (verified: zero real-corpus
    protos trip the assertion below -- see task-7-report.md's round-1
    section).
    """
    return (bool(p.locvars), any(u is not None for u in p.upvalues), p.source is not None)


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
    This memoization is only sound if every proto in the tree agrees on
    debug-completeness (see module docstring "Round-1 fix" and
    `_debug_shape`); asserted below rather than assumed, so a future caller
    that hands in a synthesized or grafted tree fails loudly instead of
    silently inheriting a wrong verdict.
    """
    from pyluadec.pipeline import walk_proto_paths
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)

    shapes = {_debug_shape(p) for p in protos.values()}
    assert len(shapes) <= 1, (
        f"proto tree has {len(shapes)} distinct (has_locvars, "
        f"has_upvalue_names, has_source) debug-completeness shapes "
        f"{sorted(shapes)} -- structural_hash-keyed memoization below "
        "assumes a uniform tree (locvars/upvalue-names/source aren't part "
        "of structural_hash, so two same-hash protos with different "
        "debug-completeness can certify differently yet share a memo "
        "entry); a real load_file/load_bytes tree is always uniformly "
        "-s-stripped or not, so this indicates a synthesized/grafted tree, "
        "not real bytecode")

    memo: dict[str, ProtoCert] = {}
    certs: dict[str, ProtoCert] = {}
    # `main` is certified first and unconditionally, NOT because
    # walk_proto_paths's pre-order recursion plus dict insertion order
    # happens to put it first in `protos.items()` (true, but this does not
    # rely on it): relying on iteration order would make the "main
    # certified L3 => print succeeded" assertion below correct only by
    # coincidence if some future change reordered `protos` or introduced a
    # same-hash collision between `root` and one of its own descendants.
    root_hash = structural_hash(root)
    memo[root_hash] = certify_proto(root, is_chunk_root=True)
    certs["main"] = memo[root_hash]
    for path, p in protos.items():
        if path == "main":
            continue
        h = structural_hash(p)
        if h not in memo:
            memo[h] = certify_proto(p, is_chunk_root=False)
        certs[path] = memo[h]

    if certs["main"].level == "L3":
        src = print_chunk(root)
        assert src is not None            # main certified L3 => print succeeded
        return ChunkOutcome(source=src.encode(), certs=certs)
    return ChunkOutcome(source=emit_chunk(root), certs=certs)

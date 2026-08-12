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
print their whole subtree, and only a proto that prints can certify -- those
were the M3-exit figures; after M4 tasks 1-4 and 13 printability is 1424/1478
(96.3%) and 1890/1944 (97.2%). Achieved at M3 exit: 1112/1478 (75.2%) unique,
1577/1944 (81.12%) occurrences; achieved after M4 task 13: 1389/1478 (94.0%)
unique, 1855/1944 (95.4%) occurrences. (An earlier planning estimate of
"~80.3%" was quoted here as the ceiling; it reproduces on neither basis, and
even 81.12% occurrences already exceeded it. The measurement scripts for all
three rows are inlined in `docs/runbooks/structured-pipeline.md`, "Current
capability boundary".)

## Memoization key (round-1 fix, superseded in M3 task 8; widened in M5 task 2)

`certify_proto`'s verdict is memoized. The obvious key,
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
production caller. It is gone: the memo is keyed on `_memo_key` =
`structural_hash` + `_debug_fingerprint`, which together cover every field
`compare_protos` examines, so equal keys imply equal verdicts by
construction and no assumption about the caller's tree is needed. See
`_debug_fingerprint`.

M5 task 2 moved that memo out of `emit_certified_chunk` (per chunk) and into
`certify_proto` (per process), and added `is_chunk_root` and the oracle's
identity to the key. Rationale, measured savings, and the trade of putting
process-lifetime state in a `src/` module are all at `certify_proto`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pyluadec.emit.lua import print_chunk_or_raise, _print_proto_body
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.ingest import Proto, load_bytes
from pyluadec import oracle
from pyluadec.sir.build import StructureError
from pyluadec.structure.fallback import emit_chunk
from pyluadec.verify.certify import carries_debug, certify_l3, debug_view
from pyluadec.verify.ledger import oracle_version, structural_hash
from pyluadec.verify.normalize import Mismatch, NORMALIZATIONS, compare_protos


# Process-level certification cache; see `certify_proto`. Keyed on
# `(oracle identity, is_chunk_root) + _memo_key(proto)` -- never on anything
# weaker, see `_debug_fingerprint`.
_CERT_CACHE: dict[tuple[str, bool, str, str], "ProtoCert"] = {}

# Memoized `oracle_version()`. `None` until the first certification asks:
# resolving it costs a `git log` subprocess, and paying that per lookup would
# cost more than the cache saves.
_ORACLE_ID: str | None = None


@dataclass(frozen=True)
class ProtoCert:
    level: str                       # "L3" | "L1"
    rung: int | None
    mismatches: tuple[Mismatch, ...]
    # The exact bytes that were compiled and compared to reach this verdict,
    # for a chunk-root `L3` certification; `None` otherwise (non-root
    # certifications compile a wrapper, not a shippable chunk, and a non-`L3`
    # verdict has nothing certified to hand out). "Otherwise" used to need a
    # caveat: a proto certified as a descendant could be handed a root's memo
    # entry, `source` included, and the only thing ruling that out was that a
    # proto cannot equal a strict descendant of itself (`structural_hash`
    # folds subprotos recursively, so the key is well-founded on depth). Since
    # M5 task 2 `is_chunk_root` is part of the cache key, so the two forms
    # cannot share an entry at all and the promise is structural.
    # `emit_certified_chunk`
    # ships THIS object rather than calling `print_chunk` a second time, so
    # "shipped == certified" holds by construction rather than by the
    # printer happening to be deterministic.
    source: bytes | None = None
    # Why this proto is not `L3`, or `None` when it is (M4 task 6). This is
    # the string `scripts/run_corpus.py` writes into the ledger row's
    # `refusal_reason` field, so its vocabulary is a committed interface:
    # `tests/test_m4_exit.py` asserts every non-`L3` row carries one and that
    # its kind is one of the four below. Four kinds, in the order the
    # certification pipeline can reach them:
    #
    #   "structure: <StructureError message>"    the region builder refused
    #   "reconstruct: <ReconstructError message>" the expression layer refused
    #   "compile: <fixed phrase>"                 the printed candidate did not
    #                                             recompile, or the wrapper
    #                                             came back the wrong shape
    #   "mismatch: <field>"                       it printed and recompiled,
    #                                             but `compare_protos` differed
    #
    # Two deliberate exclusions. The `Mismatch`'s `a`/`b` reprs are NOT in the
    # reason -- they hold the actual constants and code words, i.e. corpus
    # payload -- only the field name is. And `oracle.LuaCompileError`'s text is
    # not either: `luac` echoes the offending source line, which for this
    # corpus is bytecode-derived string data. See `emit.lua._ident` for the one
    # raise site that used to interpolate a constant and no longer does.
    reason: str | None = None


@dataclass(frozen=True)
class ChunkOutcome:
    source: bytes
    certs: dict[str, ProtoCert]


def _refused(exc: Exception) -> ProtoCert:
    """An `L1` verdict from a printer refusal, carrying the refusal's own
    message as the ledger reason. `StructureError` and `ReconstructError` are
    distinguished because they are different failures: the first means no
    region tree could be built, the second that a region printed but an
    expression under it could not be reconstructed."""
    kind = "structure" if isinstance(exc, StructureError) else "reconstruct"
    return ProtoCert(level="L1", rung=None, mismatches=(),
                     reason=f"{kind}: {exc}")


def _rejected(mismatches: tuple[Mismatch, ...]) -> ProtoCert:
    """An `L1` verdict from the comparison: the candidate recompiled but did
    not match at any rung. The reason names the FIRST differing field only --
    never the values, which are corpus payload (see `ProtoCert.reason`)."""
    return ProtoCert(level="L1", rung=None, mismatches=mismatches,
                     reason=f"mismatch: {mismatches[0].field}")


def _debug_fingerprint(p: Proto) -> str:
    """Hash of exactly the fields `compare_protos` checks that
    `structural_hash` omits, recursively over the subtree.

    The field enumeration itself lives in `verify.certify.debug_view`, whose
    other consumer is `carries_debug` (the candidate's strip-mode decision,
    M4 task 7). Sharing it is deliberate: a debug field that matters to the
    comparison matters to both, and splitting the list would let one drift.

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
    blob = json.dumps(debug_view(p), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def _oracle_identity() -> str:
    """This process's oracle identity, resolved once.

    `oracle_version()` shells out to `git log`; at ~1900 certifications per
    corpus pass, paying that per cache lookup would cost more than the cache
    saves. Memoized in a module global rather than `functools.lru_cache` so a
    test can move it (see
    `test_process_cache_does_not_survive_an_oracle_rebuild`).
    """
    global _ORACLE_ID
    if _ORACLE_ID is None:
        _ORACLE_ID = oracle_version()
    return _ORACLE_ID


def certify_proto(proto: Proto, *, is_chunk_root: bool) -> ProtoCert:
    """Certify one proto's own subtree in isolation, memoized for the life of
    the process. See `_certify_proto_uncached` for what certification is; this
    wrapper is only about who pays for it.

    ## The key

    `(oracle identity, is_chunk_root) + _memo_key(proto)`, and every component
    is load-bearing:

    * `_memo_key` = `structural_hash` + `_debug_fingerprint`. Together they
      cover every field `compare_protos` examines, so equal keys imply equal
      verdicts by construction. `structural_hash` ALONE is not sufficient and
      never was -- it is a code-shape key that drops `source`,
      `linedefined`/`lastlinedefined`, `lineinfo`, `locvars` and upvalue
      names, all of which the comparison checks. Measured over the corpus
      2026-08-12: 16 of the 1478 `structural_hash` groups carry more than one
      debug fingerprint, so this is a live hazard, not a theoretical one. See
      `_debug_fingerprint`.
    * `is_chunk_root` selects an entirely different procedure (compile the
      print as a whole chunk vs. wrap it in `local u0 ... return
      function(...) ... end`) and a different verdict shape (only the root
      form carries `source`). The old per-chunk memo could omit it because a
      proto cannot equal a strict descendant of itself -- `structural_hash`
      folds subprotos recursively, so the key is well-founded on depth. A
      process-level cache spans chunks, where no such relation holds between
      the two callers, so the flag goes in the key and that argument is
      retired.
    * The oracle identity is `verify.ledger.oracle_version()`, the same value
      the ledger's `oracle` field records (`git log -1 --format=%H --
      vendor native`). A `luac_sz4` rebuilt underneath a live process would
      otherwise be certified against by proxy from the previous build's
      verdicts, and a byte-identical ledger would NOT catch it: the stale
      verdicts would be internally consistent and simply describe the wrong
      compiler.

    ## Why process-level, and what it costs

    Suite budget (M5 task 2). The corpus tests decompile all 229 files at
    least twice per process -- once through `tests/conftest.py`'s session
    `decompiled` fixture, once more inside
    `test_ledger_ratchet.py`'s fresh `scripts/run_corpus.py` run -- and
    certification's dominant cost is one `luac_sz4` subprocess per proto.
    Note what this does NOT buy: the *intra*-pass redundancy is 1.0% (1944
    certifications, 1924 distinct keys, measured 2026-08-12), not the ~24%
    a planning estimate predicted from the 1478 `structural_hash` groups.
    The saving is entirely cross-pass.

    The trade taken by putting the dict in `src/` rather than in a test
    fixture: this is a real behaviour change to a production module, and a
    long-running process accumulates entries (a full corpus pass leaves 1924
    of them; the chunk-root entries hold their `source` bytes, so the corpus
    footprint is a few MB). `scripts/run_corpus.py` gets the 1.0%. In
    exchange, `test_ledger_ratchet` -- which deliberately consumes no other
    test's fixtures, so a conftest-scoped dict would have to be injected into
    this module anyway to reach it -- gets its verdicts for free. Call
    `clear_certification_cache()` to drop it.
    """
    key = (_oracle_identity(), is_chunk_root) + _memo_key(proto)
    hit = _CERT_CACHE.get(key)
    if hit is not None:
        return hit
    cert = _certify_proto_uncached(proto, is_chunk_root=is_chunk_root)
    _CERT_CACHE[key] = cert
    return cert


def clear_certification_cache() -> None:
    """Drop every memoized verdict. Nothing in-tree needs this -- the cache is
    a pure-function memo over a key that covers everything a verdict depends
    on -- but a long-running embedder that has finished with one corpus has no
    other way to release the `source` bytes the chunk-root entries hold."""
    _CERT_CACHE.clear()


def _certify_proto_uncached(proto: Proto, *, is_chunk_root: bool) -> ProtoCert:
    """Certify one proto's own subtree in isolation.

    `is_chunk_root=True`: the proto IS the chunk main -- its structured print
    already is a complete compilable chunk, so it is compiled and compared
    directly (via `certify_l3`, which picks the candidate's strip mode from
    the original's own debug-completeness; `-s` for this corpus).

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
        try:
            src = print_chunk_or_raise(proto)
        except (StructureError, ReconstructError) as exc:
            return _refused(exc)
        payload = src.encode()
        cert = certify_l3(proto, payload)
        if cert.level == "L3":
            return ProtoCert(cert.level, cert.rung, cert.mismatches, payload)
        # `certify_l3` reports a compile failure as `L1` with no mismatches --
        # it never got as far as comparing anything.
        if not cert.mismatches:
            return ProtoCert(level="L1", rung=None, mismatches=(),
                             reason="compile: candidate chunk did not recompile")
        return _rejected(cert.mismatches)

    upval_names = tuple(f"u{i}" for i in range(proto.nups))
    try:
        body = _print_proto_body(proto, depth=1, upval_names=upval_names)
    except (StructureError, ReconstructError) as exc:
        return _refused(exc)
    params = ", ".join(f"l1_{i}" for i in range(proto.numparams))
    if proto.is_vararg & 2:
        params = params + (", ..." if params else "...")
    decls = ("local " + ", ".join(upval_names) + "\n") if upval_names else ""
    wrapper = f"{decls}return function({params})\n{body}end\n"
    try:
        recompiled = load_bytes(oracle.compile_source(
            wrapper.encode(), strip=not carries_debug(proto)))
    except oracle.LuaCompileError:
        return ProtoCert(level="L1", rung=None, mismatches=(),
                         reason="compile: candidate wrapper did not recompile")
    if len(recompiled.subprotos) != 1:
        return ProtoCert(
            level="L1", rung=None, mismatches=(),
            reason=f"compile: wrapper yielded {len(recompiled.subprotos)} "
                   "nested functions, expected 1")
    candidate = recompiled.subprotos[0]
    last: tuple[Mismatch, ...] = ()
    for k in range(len(NORMALIZATIONS) + 1):
        diffs = compare_protos(proto, candidate, level=k)
        if not diffs:
            return ProtoCert("L3", k, ())
        last = tuple(diffs)
    return _rejected(last)


def emit_certified_chunk(root: Proto) -> ChunkOutcome:
    """Certify every proto in `root`'s tree independently, then choose the
    shipped artifact: structured chunk source iff the ROOT certified L3
    (which, per `certify_proto`'s wrapper-isolation contract, implies every
    descendant printed and recompiled correctly as part of that same
    structured print -- `print_chunk` prints the whole tree inline at each
    CLOSURE site); the semantically-exact fallback chunk otherwise.

    Identical protos are certified once and the result is shared -- corpus
    functions repeat verbatim (identical small helper closures), and
    certification's dominant cost is one `luac_sz4` subprocess per proto.
    That memo used to live here, per chunk; since M5 task 2 it lives in
    `certify_proto` itself and spans the process, which is strictly wider (a
    repeat decompile of the same file is now free too) and strictly stricter
    (`is_chunk_root` joined the key). This function no longer memoizes
    anything of its own -- every call below goes through that one cache, so
    two protos in this tree with the same key still come back as the same
    object.
    """
    from pyluadec.pipeline import walk_proto_paths
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)

    certs: dict[str, ProtoCert] = {}
    # `main` is certified first and unconditionally, NOT because
    # walk_proto_paths's pre-order recursion plus dict insertion order
    # happens to put it first in `protos.items()` (true, but this does not
    # rely on it): relying on iteration order would make the "main
    # certified L3 => print succeeded" assertion below correct only by
    # coincidence if some future change reordered `protos`.
    certs["main"] = certify_proto(root, is_chunk_root=True)
    for path, p in protos.items():
        if path == "main":
            continue
        certs[path] = certify_proto(p, is_chunk_root=False)

    # Ship the very bytes certification compiled and compared, NOT a second
    # `print_chunk(root)` call. Re-printing would make "shipped == certified"
    # depend on `print_chunk` being deterministic -- true today, and measured
    # (M4 task 12: 212/212 shipped artifacts re-print identically; it was
    # 92/92 at M3 close, before the loop work), but a property of the
    # printer rather than of this gate, and one no test here would notice
    # losing. Reusing `ProtoCert.source` makes the invariant structural.
    if certs["main"].level == "L3":
        certified = certs["main"].source
        if certified is None:
            # main certified L3 => print succeeded, so this is unreachable.
            # A `raise`, not an `assert`: this is the last check between a
            # certification verdict and what gets written to
            # `build/decompiled/`, and `python -O` deletes asserts.
            raise RuntimeError(
                "root certified L3 with no source -- certification and "
                "printing disagree")
        return ChunkOutcome(source=certified, certs=certs)
    return ChunkOutcome(source=emit_chunk(root), certs=certs)


def _memo_key(p: Proto) -> tuple[str, str]:
    return (structural_hash(p), _debug_fingerprint(p))

"""Per-proto L3 certification with wrapper isolation, and chunk assembly (spec §4, §5).

A proto certifies L3 iff the structured print of ITS OWN SUBTREE recompiles to a
proto matching the original under the normalization ladder. Certification is
per-proto so one unstructurable function cannot poison its siblings' levels.

**Shipping (M5 task 6 retired the all-or-nothing rule here; corrected in
round 2 of that task's review, F6/Residual A -- this paragraph used to say
"structured only when the ROOT certifies, otherwise the fallback chunk
ships" verbatim, which is the invariant this task replaced).** Three tiers,
tried in order: the ROOT's own certified bytes ship if the root certifies L3
(covers the whole tree); else a hybrid ships if `certify_hybrid` can certify
one -- structured code everywhere except at the CLOSURE sites its
`fallback_paths` names, each such site filled by the semantically-exact
fallback state machine and bound to the enclosing scope's own names; else the
whole-chunk semantically-exact fallback ships. No unverified structured code
is ever returned, and a hybrid's fallback-emitted protos are confessed in the
ledger exactly as a whole-file fallback's are. See `emit_certified_chunk` and
`ChunkOutcome`/`HybridCert` below for the mechanism.

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
`certify_proto` (per process), and added `is_chunk_root` and the oracle
binary's identity to the key. Rationale, measured savings, and the trade of
putting process-lifetime state in a `src/` module are all at `certify_proto`.
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
from pyluadec.structure.fallback import EmitError, emit_chunk
from pyluadec.verify.certify import carries_debug, certify_l3, debug_view
from pyluadec.verify.ledger import structural_hash
from pyluadec.verify.normalize import Mismatch, NORMALIZATIONS, compare_protos


# Process-level certification cache; see `certify_proto`. Keyed on
# `_oracle_identity() + (is_chunk_root,) + _memo_key(proto)` -- never on
# anything weaker, see `_debug_fingerprint`.
#
# This dict is module state that outlives any one chunk, so a TEST that
# monkeypatches production internals (the printer, the reconstructor, the CFG
# builder) and then certifies writes a verdict computed under the patch into
# it, under an ordinary key -- and `monkeypatch` undoes the attribute at
# teardown but cannot undo cache entries written while it was in force. The
# next reader (the corpus fixture, the ledger ratchet) would then consume a
# wrong verdict and stay green. `tests/conftest.py`'s autouse
# `_fence_certification_cache` fixture is the fence: an UNCONDITIONAL autouse
# fixture that snapshots and restores this dict (and `_HYBRID_CACHE`) around
# EVERY test. If you write a fault-injection test, do not disable it.
#
# This comment used to say "around every test that requests `monkeypatch`",
# which describes the narrower variant that was built, measured and then
# REJECTED -- it is a heuristic about how a future test happens to patch, and
# the two variants were indistinguishable against the suite's own noise.
# `tests/conftest.py` records that measurement in full.
_CERT_CACHE: dict[tuple[str, int, int, bool, str, str], "ProtoCert"] = {}


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
    # Did this chunk ship as a HYBRID -- structured code everywhere except at
    # the CLOSURE sites in `fallback_paths` (M5 task 6)? False both for a
    # fully-structured chunk (root certified `L3`) and for a whole-file
    # fallback (nothing structured survived).
    hybrid: bool = False
    # The propose-and-certify channel (M8): the `proto_path`s whose text
    # in `source` came from a hand-written proposal rather than from the
    # structured printer. Like `fallback_paths`, a path covers its whole
    # subtree; unlike it, these protos ARE certified -- the chunk shipped
    # only after a whole-tree compare with zero excluded paths.
    # `proposal_rung` is that round's ladder rung; -1 when no proposal
    # tier ran.
    proposal_paths: frozenset[str] = frozenset()
    proposal_rung: int = -1
    # The `proto_path`s whose text in `source` came from the fallback state
    # machine rather than from the structured printer. A path in this set
    # covers its whole subtree. Empty for a fully-structured chunk; every path
    # in the tree for a whole-file fallback. This is what the ledger's
    # confessions are scoped to, and it is a statement about the SHIPPED
    # ARTIFACT -- not about any proto's certification level, which
    # `certs` still reports per proto and independently.
    fallback_paths: frozenset[str] = frozenset()


@dataclass(frozen=True)
class HybridCert:
    """A certified hybrid chunk: `source` compiles to a proto tree that matches
    the original field for field EXCEPT under `fallback_paths`."""
    source: bytes
    rung: int
    fallback_paths: frozenset[str]


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
    not match at any rung. The reason names the FIRST differing field, and the
    subproto path when that field is not this proto's own -- never the values,
    which are corpus payload (see `ProtoCert.reason`).

    `Mismatch.path` used to be dropped alongside `.a`/`.b` (M5 agenda item 8).
    Dropping the values is required; dropping the path was collateral, and it
    is safe to keep because a path is built by `verify.normalize._cmp` out of
    `"root"` and subproto INDICES -- `f"{path}/{i}"` -- so it carries no
    bytecode-derived text by construction. Without it a row saying
    `mismatch: code` on a 5-instruction root was indistinguishable from one
    whose own `code` really differed.

    Measured on this corpus 2026-08-13, over all 22 occurrences whose reason is
    a `mismatch`: **20 are at `root` and 2 are not** (`snr_s1_10_s.lua:main` at
    `root/48` and `snr_s3_10_s.lua:main` at `root/59`, the two hybrid roots
    whose real defect is a descendant's `code`). So this buys two rows today.
    It is worth the schema move anyway because the two it buys are exactly the
    misattributions the item describes, and because M6's residual work reads
    this field.
    """
    m = mismatches[0]
    where = "" if m.path == "root" else f" at {m.path}"
    return ProtoCert(level="L1", rung=None, mismatches=mismatches,
                     reason=f"mismatch: {m.field}{where}")


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


def _oracle_identity() -> tuple[str, int, int]:
    """The identity of the `luac_sz4` binary a certification would actually
    run, resolved ON EVERY LOOKUP: `(path, mtime_ns, size)`.

    Resolved per lookup rather than memoized because the point of this
    component is to partition the cache when the oracle moves underneath a
    LIVE process, and there are exactly two ways that happens -- both of which
    this catches and neither of which a once-per-process value can:

    * a rebuild in place (`./scripts/build_native.sh`) rewrites
      `build/luac_sz4`, moving its mtime and usually its size;
    * `PYLUADEC_BUILD_DIR` (a documented, supported knob -- see
      `docs/runbooks/decompile-pipeline.md`) is read by `oracle.build_dir()`
      on every `compile_source` call, so it can swap the binary between two
      certifications within one process.

    **`(mtime_ns, size)` is a heuristic, not a content hash** (M5 task 2
    deferred minor, recorded at task 12). Two different `luac_sz4` binaries of
    identical size, rebuilt within the same filesystem timestamp granularity,
    would share a key -- the "catches both channels" claim above is about the
    two channels, not about being collision-free. It is not practically
    exploitable: a real compiler invocation takes milliseconds and APFS/ext4
    carry nanosecond mtimes, so the window needs a rebuild faster than the
    clock's resolution AND a byte-length-preserving change. Hashing the binary
    per lookup would close it at ~1 MB of I/O per `certify_proto` call, which
    is the wrong trade for a memo whose miss costs one `luac` subprocess. If
    this ever needs to be exact, hash once per `(path, mtime_ns, size)` and
    cache that.

    The M5 task 2 original keyed on `verify.ledger.oracle_version()` (`git
    log -1 --format=%H -- vendor native`) memoized into a module global. That
    is what the ledger's `oracle` field records, and the symmetry was
    appealing, but as a cache key it was inert: memoized, it is constant for
    the life of the process, so it could not partition the cache in any
    scenario a real rebuild produces -- only a test assigning the global moved
    it. The round-1 review demonstrated the consequence live (warm cache +
    `PYLUADEC_BUILD_DIR` pointed at a `luac_sz4` that refuses everything: a
    stale `L3` served for a proto that no longer compiles). The git hash is
    NOT kept alongside: it is strictly weaker than this tuple (a commit under
    `vendor/`/`native/` without a rebuild leaves the same compiler in place,
    where the cached verdicts are still correct) and keeping an inert
    component in the key is what invited the overclaim in the first place.

    Cost: two `stat`s (`build_dir()` checks existence, then this reads the
    metadata), microseconds, against the ~1-2ms `luac` subprocess this guards.
    Measured over the corpus 2026-08-12: full-suite wall unchanged within
    run-to-run noise (task-2-report.md, round 1).

    Raises `oracle.OracleError` when no `luac_sz4` can be found. That is a
    small behaviour change: a certification whose printer refuses used to
    return `L1` without ever touching the oracle, and now needs the oracle to
    exist to compute its key. It is the same exception this module already
    raises from `compile_source` for any proto that DOES print, so a build
    tree without an oracle fails the same way, just earlier.
    """
    luac = oracle.luac_sz4()
    st = luac.stat()
    return (str(luac), st.st_mtime_ns, st.st_size)


def certify_proto(proto: Proto, *, is_chunk_root: bool) -> ProtoCert:
    """Certify one proto's own subtree in isolation, memoized for the life of
    the process. See `_certify_proto_uncached` for what certification is; this
    wrapper is only about who pays for it.

    ## The key

    `_oracle_identity() + (is_chunk_root,) + _memo_key(proto)`, and every
    component is load-bearing:

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
    * The oracle identity is the `luac_sz4` binary's own `(path, mtime_ns,
      size)`, re-read on every lookup. A `luac_sz4` rebuilt underneath a live
      process -- or swapped by `PYLUADEC_BUILD_DIR`, which `oracle.build_dir()`
      re-reads per compile -- would otherwise be certified against by proxy
      from the previous build's verdicts, and a byte-identical ledger would
      NOT catch it: the stale verdicts would be internally consistent and
      simply describe the wrong compiler. Round 1 of the M5 task 2 review
      demonstrated exactly that against the first version of this key, which
      used a once-per-process `git log` hash; see `_oracle_identity` for why
      that could never partition anything and why the hash is not kept
      alongside.

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
    key = _oracle_identity() + (is_chunk_root,) + _memo_key(proto)
    hit = _CERT_CACHE.get(key)
    if hit is not None:
        return hit
    cert = _certify_proto_uncached(proto, is_chunk_root=is_chunk_root)
    _CERT_CACHE[key] = cert
    return cert


def clear_certification_cache() -> None:
    """Drop every memoized verdict.

    Nothing in-tree needs this for CORRECTNESS -- the cache is a pure-function
    memo over a key that covers the proto in full (`_memo_key`), the procedure
    (`is_chunk_root`), and the compiler the verdict was measured against
    (`_oracle_identity`, re-read per lookup). It exists so a long-running
    embedder that has finished with one corpus can release the `source` bytes
    the chunk-root entries hold (a full 229-file pass leaves 1924 entries
    holding ~4 MB).

    Pinned by `test_clear_certification_cache_drops_every_entry`: as the only
    escape hatch from this dict it is exactly the kind of untested helper that
    rots into a no-op.

    Drops `_HYBRID_CACHE` too (M5 task 6): it holds whole assembled chunk
    sources for the files that ship hybrid, keyed the same way, and an escape
    hatch that released one memo and not the other would be a leak with a
    plausible-looking name.
    """
    _CERT_CACHE.clear()
    _HYBRID_CACHE.clear()


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


# A hybrid attempt costs one whole-chunk `luac_sz4` run per round, so the
# rounds are bounded rather than run to a fixed point. Each round substitutes
# at least one more proto (or gives up), and the corpus needs at most 2
# (measured 2026-08-12, see task-6-report.md), so 6 is slack, not a tuning
# knob: exceeding it means the substitution set is oscillating, and shipping
# the whole-file fallback is the honest answer.
_HYBRID_ROUNDS = 6

# Process-level memo for `certify_hybrid`, keyed exactly like `_CERT_CACHE`
# (oracle identity + `_memo_key(root)`), and fenced by the same autouse
# `tests/conftest.py::_fence_certification_cache` fixture -- a test that
# monkeypatches the printer and then decompiles would otherwise leave a wrong
# hybrid artifact behind for the corpus fixtures to consume. Only chunks whose
# root is NOT `L3` ever reach it (13 of 229 files), so it holds a handful of
# entries; `clear_certification_cache()` drops it with the other one.
_HYBRID_CACHE: dict[tuple[str, int, int, str, str], "HybridCert | None"] = {}


def _proto_path_of(mismatch_path: str) -> str:
    """`Mismatch.path` (`"root"`, `"root/59/2"` -- `verify.normalize._cmp`'s
    own spelling) as a `walk_proto_paths` `proto_path` (`"main"`,
    `"main_59_2"`). The two walks agree by construction: `_cmp` recurses over
    `zip(a.subprotos, b.subprotos)` with the index appended, which is the same
    `enumerate(p.subprotos)` `walk_proto_paths` uses."""
    parts = mismatch_path.split("/")
    return "main" + "".join(f"_{i}" for i in parts[1:])


def _excused(proto_path: str, fallback_paths: frozenset[str]) -> bool:
    """Is `proto_path` inside a substituted subtree?

    Prefix test on `f"{fp}_"` rather than on `fp`: `"main_71"` is not a
    descendant of `"main_7"`, and only the separator keeps those apart."""
    return any(proto_path == fp or proto_path.startswith(fp + "_")
               for fp in fallback_paths)


def _add_to_frontier(fb: set[str], path: str) -> None:
    """Add `path` to the substitution frontier, dropping any entry it now
    covers (M5 task 6 round 1).

    A frontier is an ANTICHAIN: no member is a strict descendant of another.
    That is not cosmetic. Two consumers read `HybridCert.fallback_paths` as
    "the CLOSURE sites the printer left a hole at" and break on a redundant
    entry:

    * `emit.lua.Printer.closure_parts` only ever consults the frontier at a
      site it actually reaches, and it never reaches a site *inside* an already
      substituted subtree -- so a descendant entry describes a hole that does
      not exist.
    * `tests/test_hybrid_chunk.py::shipping_violations`' third check skips
      protos below the frontier (their shape deliberately differs: nested
      functions become immediately-invoked factories) with `_excused(path,
      frontier) and path not in frontier`. A redundant entry IS in the
      frontier, so the skip misses it, the check indexes into the substituted
      function's factory shape, finds no state machine there and reports a
      false breach. Reproduced by the round-1 review on the `loop_close`
      fixture in that file, where `mk` and its per-iteration closure both
      refuse: the artifact was correct and the ledger closure was correct, and
      the invariant checker was the thing that was wrong.

    Latent on this corpus only by shape luck -- all 8 substituted protos across
    the 6 hybrids have zero subprotos (measured 2026-08-12), so no nesting can
    arise. Pruning here rather than at the readers keeps the antichain a
    property of the value, not an obligation on everyone who reads it.
    """
    if _excused(path, frozenset(fb)):
        return                      # already covered by an ancestor (or itself)
    for covered in [p for p in fb if p.startswith(path + "_")]:
        fb.discard(covered)
    fb.add(path)


def _plan_substitutions(root: Proto, certs: dict[str, ProtoCert]) -> set[str]:
    """The protos whose own body cannot be printed at all, bottom-up.

    A proto certified `L3` printed its entire subtree as part of that
    certification, so it is skipped: only the non-`L3` protos are probed, and
    they are probed deepest-first so that by the time a proto's turn comes,
    every descendant that had to be substituted already is. What is left after
    this pass is a set closed downward (substituting a proto substitutes its
    whole subtree) and minimal with respect to *printability* -- it says
    nothing yet about whether the result COMPARES equal, which is
    `certify_hybrid`'s round loop.

    Minimality needs `_add_to_frontier`, not just the deepest-first order: a
    descendant that refuses is added first, and then its ancestor can refuse
    too (typically for an unrelated reason in its own body), at which point the
    descendant's entry has to go. Round 1 of this task did not prune and
    emitted a non-minimal frontier for exactly that shape.
    """
    from pyluadec.pipeline import walk_proto_paths
    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    fb: set[str] = set()
    # `path.count("_")` is the proto's depth in the tree (`main`, `main_3`,
    # `main_3_0`), so descending depth is deepest-first.
    for path in sorted((p for p in protos if certs[p].level != "L3"),
                       key=lambda s: -s.count("_")):
        p = protos[path]
        if _excused(path, frozenset(fb)):
            continue                      # already inside a substituted subtree
        try:
            _print_proto_body(p, 1, tuple(f"u{i}" for i in range(p.nups)),
                              path, frozenset(fb))
        except (StructureError, ReconstructError, EmitError):
            _add_to_frontier(fb, path)
    return fb


def _hybrid_round(root: Proto, fb: frozenset[str]
                  ) -> tuple[bytes, int | None, tuple[Mismatch, ...]] | None:
    """Print, compile and compare one candidate substitution set.

    Returns `None` if the candidate could not even be produced (the root's own
    body refuses, the fallback cannot express one of the substituted protos, or
    the assembled chunk does not compile), else `(source, rung, mismatches)`
    with `rung is None` exactly when mismatches remain OUTSIDE the substituted
    subtrees.
    """
    try:
        src = _print_proto_body(root, 0, (), "main", fb)
    except (StructureError, ReconstructError, EmitError):
        return None
    payload = src.encode()
    try:
        cand = load_bytes(oracle.compile_source(
            payload, strip=not carries_debug(root)))
    except oracle.LuaCompileError:
        return None
    last: tuple[Mismatch, ...] = ()
    for k in range(len(NORMALIZATIONS) + 1):
        # `compare_protos` itself is untouched -- the ladder, the field list
        # and `_cmp` are exactly what a whole-chunk certification runs. What is
        # scoped is only WHICH protos the verdict is claimed over: a mismatch
        # under a substituted path is not excused as harmless, it is a proto
        # this chunk never claimed to have reconstructed and which ships the
        # fallback's own semantics, confessed as such in the ledger.
        last = tuple(m for m in compare_protos(root, cand, level=k)
                     if not _excused(_proto_path_of(m.path), fb))
        if not last:
            return payload, k, ()
    return payload, None, last


def _proposal_round(root: Proto, sites: frozenset[str],
                    proposals: dict[str, bytes]) -> tuple[bytes, int] | None:
    """Print the tree with proposal bodies at `sites`, compile, and compare
    with no excluded paths. `(source, rung)` or `None` (refused -- the
    caller falls to the hybrid/fallback tiers exactly as before).

    Structurally `_hybrid_round` with an empty excuse set: the compare
    loop is the same untouched `compare_protos` ladder, but nothing is
    filtered out, so the verdict covers every proto in the tree
    including each proposal's own subtree."""
    try:
        src = _print_proto_body(root, 0, (), "main", frozenset(), 0,
                                proposals)
    except (StructureError, ReconstructError, EmitError):
        return None
    payload = src.encode()
    try:
        cand = load_bytes(oracle.compile_source(
            payload, strip=not carries_debug(root)))
    except oracle.LuaCompileError:
        return None
    for k in range(len(NORMALIZATIONS) + 1):
        if not compare_protos(root, cand, level=k):
            return payload, k
    return None


def certify_hybrid(root: Proto, certs: dict[str, ProtoCert]) -> HybridCert | None:
    """Assemble and certify a hybrid chunk for a root that did not certify
    `L3`, or return `None` if no hybrid survives (the caller then ships the
    whole-file fallback).

    The claim a successful return makes, in full: **every proto of `root`'s
    tree that is not inside `fallback_paths` compares equal to the original,
    field for field, at rung `rung` of the untouched normalization ladder,
    after `source` was compiled by the real `luac_sz4`.** That is the same
    `compare_protos` a whole-chunk `L3` runs, over the same recompiled tree;
    the only difference is that the subtrees this chunk openly ships as
    fallback are not claimed. In particular the root's own `code` -- including
    the `CLOSURE` instruction and the `MOVE`/`GETUPVAL` pseudo-instructions
    that follow it at each substituted site -- and its `constants`,
    `maxstacksize` and frame contract are all still compared exactly, which is
    what makes `structure.fallback.inline_function_parts`' "one subproto slot,
    same captures, same order" obligations checkable rather than assumed.

    Cached per process; see `_HYBRID_CACHE`.
    """
    key = _oracle_identity() + _memo_key(root)
    if key in _HYBRID_CACHE:
        return _HYBRID_CACHE[key]
    result = _certify_hybrid_uncached(root, certs)
    _HYBRID_CACHE[key] = result
    return result


def _certify_hybrid_uncached(root: Proto,
                             certs: dict[str, ProtoCert]) -> HybridCert | None:
    fb = _plan_substitutions(root, certs)
    if "main" in fb:
        # The root's own body does not print. There is no structured code to
        # keep, so there is no hybrid -- only the whole-file fallback.
        return None
    for _round in range(_HYBRID_ROUNDS):
        got = _hybrid_round(root, frozenset(fb))
        if got is None:
            return None
        payload, rung, mismatches = got
        if rung is not None:
            return HybridCert(source=payload, rung=rung,
                              fallback_paths=frozenset(fb))
        grow = {_proto_path_of(m.path) for m in mismatches}
        if any(certs[g].level == "L3" for g in grow):
            # A proto that certified `L3` on its own (whole subtree, compared
            # field by field in wrapper isolation) mismatched here. That is not
            # a proto to substitute -- it is the hybrid assembly disagreeing
            # with the per-proto verdict, i.e. a defect in this composition.
            # Ship the whole-file fallback rather than paper over it, and keep
            # the ledger's "an `L3` row never confesses" coupling structural
            # instead of empirical. Never observed on this corpus (measured
            # 2026-08-12, all 229 files).
            return None
        grown = set(fb)
        for g in grow:
            _add_to_frontier(grown, g)
        if "main" in grow or grown == fb:
            # Either the chunk's own main proto is what differs (nothing left
            # to substitute), or a round made no progress. Both are "no
            # hybrid", not "substitute more".
            #
            # `grown == fb` rather than the round-1 `grow <= fb`: with pruning,
            # a round CAN move the frontier without adding a new member (it
            # replaces two entries by their common ancestor), and can also
            # report a `grow` already covered by the frontier. "The frontier
            # did not move" is the property meant; `grow <= fb` was a proxy for
            # it that stops being equivalent once entries can be removed.
            return None
        fb = grown
    return None


def emit_certified_chunk(root: Proto,
                         proposals: dict[str, bytes] | None = None,
                         ) -> ChunkOutcome:
    """Certify every proto in `root`'s tree independently, then choose the
    shipped artifact, in order: the ROOT's own certified bytes if it
    certified L3 (which, per `certify_proto`'s wrapper-isolation contract,
    implies every descendant printed and recompiled correctly as part of
    that same structured print -- `print_chunk` prints the whole tree inline
    at each CLOSURE site); else a hybrid (`certify_hybrid` below) -- structured
    everywhere except at the CLOSURE sites its own certification could not
    clear, each filled by the semantically-exact fallback and bound to the
    enclosing scope's own names; else the whole-chunk semantically-exact
    fallback (this docstring corrected round 2 of the task-6 review, F6/
    Residual A -- it used to name only the root-certifies/whole-fallback
    pair and omitted the hybrid tier this function's own body has had since
    the feature landed).

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
    # The propose-and-certify tier (M8, partner-approved 2026-08-18).
    # Tried between the root's own certification and the hybrid: at the
    # CLOSURE sites whose protos refused reconstruction AND have a
    # proposal, splice the proposal body (rebound to the enclosing
    # scope's own upvalue names), then recompile the WHOLE chunk and
    # compare with ZERO excluded paths -- the strongest form of P1: any
    # splicing or renaming error anywhere in the tree refuses the chunk.
    # Only refusers consult proposals (a proto that certified `L3` keeps
    # the reconstructor's text), so a proposal can never mask a
    # reconstruction that would have printed (P4).
    if proposals:
        refusers = {path for path, cert in certs.items()
                    if cert.level != "L3" and path in proposals}
        if refusers:
            got = _proposal_round(root, frozenset(refusers), proposals)
            if got is not None:
                payload, rung = got
                shipped_pr = frozenset(
                    path for path in protos
                    if _excused(path, frozenset(refusers)))
                return ChunkOutcome(source=payload, certs=certs,
                                    proposal_paths=shipped_pr,
                                    proposal_rung=rung)
    hybrid = certify_hybrid(root, certs)
    if hybrid is not None:
        # `HybridCert.fallback_paths` is the substitution FRONTIER (the CLOSURE
        # sites the printer left holes at); `ChunkOutcome.fallback_paths` is
        # the closure of that downward, i.e. every proto whose text in the
        # shipped source came from the state machine. The ledger confesses per
        # proto, so it needs the closure -- a descendant of a substituted
        # function is just as much fallback-emitted as its root is.
        shipped_fb = frozenset(
            path for path in protos
            if _excused(path, hybrid.fallback_paths))
        return ChunkOutcome(source=hybrid.source, certs=certs, hybrid=True,
                            fallback_paths=shipped_fb)
    return ChunkOutcome(source=emit_chunk(root), certs=certs,
                        fallback_paths=frozenset(protos))


def _memo_key(p: Proto) -> tuple[str, str]:
    return (structural_hash(p), _debug_fingerprint(p))

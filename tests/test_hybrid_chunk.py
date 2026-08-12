"""Hybrid chunk emission (M5 task 6): structured code with fallback holes.

Until this task a chunk was all-or-nothing -- structured source iff its ROOT
proto certified `L3`, the whole-file state machine otherwise. 13 of the 229
corpus files failed that test and shipped as state machines even though the
great majority of their protos certified individually.

The shipping invariant that replaces it:

> Every proto in a shipped artifact is EITHER covered by the certification that
> compiled those exact bytes, OR emitted by the semantically-exact fallback and
> confessed as such in the ledger. A proto's own certification level is
> unchanged by how its neighbours ship.

`shipping_violations` below is that invariant, as a pure function over a
`(root, ChunkOutcome, HybridCert)` triple so it can be run against triples that
VIOLATE it -- see `test_shipping_check_rejects_a_tampered_artifact`, which is
the committed proof that the check is not vacuous.

The two standing probes (`scripts/probe_global_state.py`,
`scripts/probe_behaviour.py`) are the *semantic* gate for the hybrid boundary,
because certification structurally cannot bless a hybrid whole: its fallback
parts are not byte-exact by construction. This file carries the small
differential-execution arm of the same idea, including the injection that
proves it can fail.
"""
import pytest

from pyluadec import oracle
from pyluadec.ingest import Proto, load_bytes
from pyluadec.structure import structured as S
from pyluadec.structure.fallback import _FnEmitter
from pyluadec.verify.certify import carries_debug
from pyluadec.verify.normalize import compare_protos

# A chunk whose root and two of its three children reconstruct cleanly, and
# whose middle child (`bad`) does not: `(p or q) == 1` is the `and`/`or`-fed
# comparison the recognizer refuses (`tests/test_pipeline_structured.py` uses
# the same shape for the all-or-nothing case). `bad` both READS and WRITES the
# main chunk's local `n`, so the hybrid boundary has to bind a real Lua upvalue
# in both directions -- the case the fallback's `__pld_U` box protocol cannot
# express and `inline_function_parts` exists for.
HYBRID_SOURCE = b"""
local n = 0
setN = function(v) n = v return n end
bad = function(p, q) n = (p or q) == 1 return n end
good = function(x) return n + x end
getN = function() return n end
"""

# A chunk where a REFUSING function contains a REFUSING descendant, so
# deepest-first planning adds the descendant and then its ancestor. The shape
# the round-1 review used to show the frontier was not an antichain; `acc[i] =
# function() ... end` inside the numeric `for` also makes the enclosing
# function close a loop-scoped local per iteration (`OP_CLOSE`), which the
# substituted subtree's box protocol has to express on its own.
LOOP_CLOSE_SOURCE = b"""
local acc = {}
mk = function(p, q)
  local r = (p or q) == 1
  for i = 1, 3 do
    local x = i
    acc[i] = function() local s = (p or q) == 1 return x + (s and 10 or 0) end
  end
  return r
end
getacc = function(i) return acc[i]() end
"""

# A substituted function containing a nested closure that captures BOTH kinds
# of upvalue slot the inline emission has to mix:
#
#   * `slot` and `mine` are locals of the substituted `mk`, so the nested
#     closure gets them as BOX slots (`__pld_U[i].v`), handed in as factory
#     arguments evaluated in `mk`'s own scope;
#   * `outer` is `mk`'s OWN upvalue, which at the hybrid boundary is a NAME
#     slot (the enclosing structured chunk's local `l0_0`), and is therefore
#     inherited lexically by the nested closure rather than passed.
#
# `slot` is loop-scoped, so each iteration closes over its own -- the
# per-iteration-closure shape, inside a substituted subtree.
NESTED_SOURCE = b"""
local outer = 0
mk = function(p, q)
  local flag = (p or q) == 1
  local mine = 100
  local acc = {}
  for i = 1, 2 do
    local slot = i * 10
    acc[i] = function()
      slot = slot + 1
      mine = mine + slot
      outer = outer + 1
      return slot, mine, outer
    end
  end
  return acc, flag
end
getouter = function() return outer end
"""

# The one constant every `_FnEmitter` body carries and no structured print can:
# the dispatch loop's own "unreachable pc" error message. Used to tell, from
# the RECOMPILED artifact rather than from its text, which protos really
# shipped as state machines.
_STATE_MACHINE_MARKER = b"pyluadec fallback: invalid pc"


def hybrid_fixture(source: bytes = HYBRID_SOURCE):
    """`(root, outcome, hybrid_cert)` for `source`, with both process caches
    cleared first.

    Clearing matters: `_CERT_CACHE` and `_HYBRID_CACHE` outlive a test, so an
    injection test that patches an emitter and then decompiles a chunk another
    test already decompiled would silently get the UNPATCHED artifact back and
    pass for the wrong reason. `tests/conftest.py`'s autouse fence restores
    both dicts afterwards, so clearing here costs the next reader one
    recomputation of this three-proto chunk and nothing else.
    """
    S.clear_certification_cache()
    root = load_bytes(oracle.compile_source(source, strip=True))
    outcome = S.emit_certified_chunk(root)
    certs = outcome.certs
    return root, outcome, S.certify_hybrid(root, certs)


def _proto_at(p: Proto, path: str) -> Proto | None:
    for part in path.split("_")[1:]:
        i = int(part)
        if i >= len(p.subprotos):
            return None
        p = p.subprotos[i]
    return p


def shipping_violations(root: Proto, outcome, hybrid_cert) -> list[str]:
    """The hybrid shipping invariant, as a list of human-readable breaches.

    Four checks, each of which a plausible defect would trip:

    1. **shipped == certified.** `outcome.source` is byte-for-byte the payload
       `certify_hybrid` compiled and compared. A future `emit_certified_chunk`
       that re-printed the tree instead of shipping `HybridCert.source` would
       pass only for as long as the printer stayed deterministic.
    2. **Nothing structured is unverified.** The claim is re-derived from the
       SHIPPED bytes: recompile them and run the untouched `compare_protos` at
       the certified rung; every mismatch must fall inside a substituted
       subtree.
    3. **Nothing fallback is unconfessed, and nothing confessed is structured.**
       Read off the recompiled artifact, not its text: a proto shipped by
       `_FnEmitter` carries the dispatch loop's error constant, a structured
       one cannot. Checked over every proto that is not *inside* a substituted
       subtree (below the frontier the candidate's tree shape deliberately
       differs -- nested functions become immediately-invoked factories -- so
       there is nothing to line up).
    4. **The substitution is not gratuitous.** At least one mismatch must
       actually fall inside a substituted subtree; a hybrid that substituted a
       function whose structured print was fine would be shipping worse code
       for no reason, and check 2 alone would never notice.
    """
    from pyluadec.pipeline import walk_proto_paths
    out: list[str] = []
    if hybrid_cert is None:
        return ["no hybrid certification (chunk did not ship hybrid)"]
    if outcome.source != hybrid_cert.source:
        out.append("shipped bytes are not the certified bytes")
    if not outcome.hybrid:
        out.append("outcome is not marked hybrid")

    protos: dict[str, Proto] = {}
    walk_proto_paths("main", root, protos)
    fb = outcome.fallback_paths
    cand = load_bytes(oracle.compile_source(
        outcome.source, strip=not carries_debug(root)))

    inside = 0
    for m in compare_protos(root, cand, level=hybrid_cert.rung):
        path = S._proto_path_of(m.path)
        if S._excused(path, fb):
            inside += 1
        else:
            out.append(f"{path}: {m.field} differs but shipped structured")
    if not inside:
        out.append("no mismatch inside any substituted subtree: the "
                   "substitution bought nothing")

    frontier = hybrid_cert.fallback_paths
    for path in protos:
        if S._excused(path, frontier) and path not in frontier:
            continue                    # below the frontier: shape differs
        cp = _proto_at(cand, path)
        if cp is None:
            out.append(f"{path}: missing from the recompiled artifact")
            continue
        is_sm = _STATE_MACHINE_MARKER in cp.constants
        if is_sm and path not in fb:
            out.append(f"{path}: shipped a state machine but is not confessed")
        if not is_sm and path in fb:
            out.append(f"{path}: confessed as fallback but is not a state machine")
    return out


# --------------------------------------------------------------------------
# The invariant, on a synthetic chunk with exactly one uncertifiable proto.
# --------------------------------------------------------------------------

def test_synthetic_chunk_ships_hybrid():
    root, outcome, hc = hybrid_fixture()
    assert outcome.hybrid is True
    # Exactly the middle child is substituted; its siblings and the root are
    # kept. Levels are untouched by any of it: `main` and `main_1` miss `L3`
    # on their own (the root's own certification prints the WHOLE tree, so
    # `bad`'s refusal is its refusal too), and the two straight-line children
    # certify.
    assert outcome.fallback_paths == frozenset({"main_1"})
    assert {p: c.level for p, c in outcome.certs.items()} == {
        "main": "L1", "main_0": "L3", "main_1": "L1", "main_2": "L3",
        "main_3": "L3"}


def test_hybrid_shipping_invariant_holds():
    root, outcome, hc = hybrid_fixture()
    assert shipping_violations(root, outcome, hc) == []


def test_hybrid_chunk_compiles():
    _root, outcome, _hc = hybrid_fixture()
    oracle.compile_source(outcome.source)          # raises on failure


def test_substituted_proto_is_the_fallbacks_text_and_siblings_are_not():
    """The text-level reading of the same fact, for a human debugging a hybrid:
    the substituted function's body is a dispatch loop bound to the enclosing
    scope's OWN name for the captured local, and the kept siblings are ordinary
    Lua."""
    _root, outcome, _hc = hybrid_fixture()
    src = outcome.source.decode()
    assert "bad = function(__pld_p0, __pld_p1)" in src
    assert "local __pld_ord = {l0_0}" in src       # upvalue-order prologue
    assert "l0_0 = __pld_R[2]" in src              # SETUPVAL through the name
    assert "setN = function(l1_0)" in src
    assert "good = function(l1_0)" in src
    assert "return l0_0 + l1_0" in src
    # ...and the state machine is confined to the substituted function.
    assert src.count("while true do") == 1


# --------------------------------------------------------------------------
# Fault injection (a): a certified proto's shipped text is wrong.
# --------------------------------------------------------------------------

def test_shipping_check_rejects_a_tampered_artifact():
    """`shipping_violations` must be able to fail. Three tampered artifacts,
    one per check that could rot into a no-op."""
    import dataclasses
    root, outcome, hc = hybrid_fixture()
    assert shipping_violations(root, outcome, hc) == []

    # 1. A certified proto's shipped text is not what was certified: `good`'s
    #    body is rewritten in the ARTIFACT only, leaving the certification
    #    untouched. Both the byte-equality check and the re-derived comparison
    #    must fire -- the first because the bytes moved, the second because the
    #    recompiled `main_2` no longer matches the original.
    tampered = outcome.source.replace(b"return l0_0 + l1_0", b"return l0_0 - l1_0")
    assert tampered != outcome.source
    bad = dataclasses.replace(outcome, source=tampered)
    breaches = shipping_violations(root, bad, hc)
    assert "shipped bytes are not the certified bytes" in breaches
    assert any("main_2" in b and "shipped structured" in b for b in breaches)

    # 2. A proto that shipped as a state machine is not confessed.
    unconfessed = dataclasses.replace(outcome, fallback_paths=frozenset())
    assert any("main_1: shipped a state machine but is not confessed" == b
               for b in shipping_violations(root, unconfessed, hc))

    # 3. A proto confessed as fallback that is in fact structured -- the shape
    #    a confession left behind after the code stopped falling back.
    overconfessed = dataclasses.replace(
        outcome, fallback_paths=frozenset({"main_1", "main_2"}))
    assert any("main_2: confessed as fallback but is not a state machine" == b
               for b in shipping_violations(root, overconfessed, hc))


def test_a_refusing_ancestor_replaces_its_refusing_descendant_in_the_frontier():
    """The substitution frontier must be an ANTICHAIN (M5 task 6 round 1).

    `mk` refuses (`(p or q) == 1`) and so does the per-iteration closure it
    creates. Deepest-first planning reaches `main_0_0` first and adds it, then
    reaches `main_0` and adds that too; without `_add_to_frontier`'s prune the
    frontier came out as `{main_0, main_0_0}`. The artifact was still correct
    -- the printer never reaches a CLOSURE site inside an already substituted
    subtree, so the redundant entry described a hole that does not exist -- and
    so was the ledger's downward closure. What broke was the invariant checker:
    `shipping_violations`' third check skips protos BELOW the frontier (their
    shape deliberately differs) and a redundant entry is IN the frontier, so it
    indexed into the inline factory, found no state machine and reported
    `main_0_0: confessed as fallback but is not a state machine`.

    Red without the prune (measured 2026-08-12): frontier
    `['main_0', 'main_0_0']`, one false breach.
    """
    root, outcome, hc = hybrid_fixture(LOOP_CLOSE_SOURCE)
    assert {p: c.level for p, c in outcome.certs.items()} == {
        "main": "L1", "main_0": "L1", "main_0_0": "L1", "main_1": "L3"}
    assert S._plan_substitutions(root, outcome.certs) == {"main_0"}
    assert hc is not None and hc.fallback_paths == frozenset({"main_0"})
    # The ledger's closure is unchanged by the prune: it is derived by
    # `_excused`, which covers the whole subtree from the ancestor alone.
    assert outcome.fallback_paths == frozenset({"main_0", "main_0_0"})
    assert shipping_violations(root, outcome, hc) == []


def test_shipping_check_rejects_a_gratuitous_substitution():
    """Check 4 on its own: substituting a proto whose structured print was
    perfectly good leaves every mismatch outside the substituted subtree, so
    the artifact "certifies" while being strictly worse code."""
    import dataclasses
    root, outcome, hc = hybrid_fixture()
    fb = frozenset({"main_0", "main_1"})
    src = S._print_proto_body(root, 0, (), "main", fb).encode()
    got = S._hybrid_round(root, fb)
    assert got is not None and got[1] is not None, "gratuitous set still certifies"
    fake_hc = S.HybridCert(source=src, rung=got[1], fallback_paths=fb)
    fake_out = dataclasses.replace(outcome, source=src, fallback_paths=fb)
    breaches = shipping_violations(root, fake_out, fake_hc)
    assert breaches == [], breaches       # checks 1-3 are satisfied...
    # ...so it takes check 4 to notice. Restated: `main_0` mismatching nothing
    # is exactly why the real planner never substitutes an `L3` proto.
    assert S._plan_substitutions(root, outcome.certs) == {"main_1"}


# --------------------------------------------------------------------------
# Fault injection (b): a fallback part is semantically wrong.
# --------------------------------------------------------------------------

def _run_both(source: bytes, driver: bytes) -> tuple[bytes, bytes]:
    """Run `source + driver` as original bytecode and as the hybrid artifact,
    returning both stdouts. The driver is appended to the ORIGINAL source and
    compiled with it, then the same driver text is appended to the decompiled
    chunk -- so both sides execute the same observable program."""
    root = load_bytes(oracle.compile_source(source, strip=True))
    out = S.emit_certified_chunk(root)
    orig = oracle.run_bytes(oracle.compile_source(source + driver),
                            is_source=False)
    dec = oracle.run_bytes(out.source + driver, is_source=True)
    assert orig.returncode == 0, orig.stderr
    return orig.stdout, dec.stdout


# Globals only: `n` is a chunk LOCAL, so a driver that mentioned it by name
# would read the original's local and the artifact's global (nil) and diverge
# for a reason that has nothing to do with the boundary. `getN` exists in the
# chunk to observe it from outside.
_DRIVER = (b"print(setN(5), good(2), bad(1, 2), getN(), "
           b"bad(false, false), getN())\n")


def test_hybrid_chunk_runs_identically_to_the_original():
    """Differential execution across the boundary. The driver reads `n` through
    `getN` AFTER `bad` has written it, so a boundary that copied the upvalue
    instead of aliasing it would show up here and nowhere in the
    certification."""
    a, b = _run_both(HYBRID_SOURCE, _DRIVER)
    assert a == b, (a, b)
    assert a.strip(), "driver printed nothing -- the comparison is vacuous"


def test_a_broken_upvalue_write_at_the_boundary_diverges(monkeypatch):
    """Fault injection: make the substituted function's upvalue WRITE go to a
    scratch local instead of the enclosing scope's variable.

    This is the single most load-bearing thing `inline_function_parts` does
    that the old `__pld_U` box protocol did differently, so it is the injection
    worth committing. Certification does not see it (the fallback subtree is
    excluded from the comparison by construction), the chunk still compiles,
    and only running it tells them apart -- which is precisely why the two
    standing probes, not certification, are this boundary's gate.
    """
    real = _FnEmitter.up_write

    def broken(self, b, expr):
        kind, text = self.up_slot(b)
        if kind == "name":
            return f"local __pld_dropped = {expr}"
        return real(self, b, expr)

    monkeypatch.setattr(_FnEmitter, "up_write", broken)
    S.clear_certification_cache()
    a, b = _run_both(HYBRID_SOURCE, _DRIVER)
    assert a != b, ("the injected boundary defect was not observed", a, b)


def test_a_refusing_ancestor_frontier_chunk_runs_identically():
    """The `loop_close` shape, executed. Pruning the frontier must not change
    what the artifact does: the redundant entry never described a real hole."""
    a, b = _run_both(
        LOOP_CLOSE_SOURCE,
        b"print(mk(1, 2), getacc(1), getacc(2), getacc(3), "
        b"mk(false, false), getacc(2))\n")
    assert a == b, (a, b)
    assert a.strip(), "driver printed nothing -- the comparison is vacuous"


def test_a_closure_nested_inside_a_substituted_function_runs_identically():
    """The inline nested-closure path, differentially executed.

    Measured 2026-08-12: every substituted proto in the 6 corpus hybrids has
    zero subprotos, so nothing in the corpus reaches
    `fallback._FnEmitter._emit_simple`'s `inline=True` CLOSURE branch -- the
    immediately-invoked `(function(__pld_U) return function(...) ... end
    end)({...})` factory, the mixed `_BOX`/`_NAME` slot inheritance, and the
    ordering rule that box arguments are evaluated in the enclosing function's
    scope BEFORE `__pld_U` shadows the name. It is also the one piece of this
    composition the identify-or-refuse discipline structurally cannot protect,
    because a substituted subtree is excluded from `compare_protos` by
    construction. This is its guard.

    The driver reads `outer` through `getouter` AFTER the nested closures have
    written it, and calls `acc[1]` twice with `acc[2]` in between, so a
    per-iteration `slot` that leaked into a shared box, a `mine` that was
    copied instead of aliased, and an `outer` that resolved to a fresh box
    instead of the enclosing scope's own variable would each change the
    output."""
    driver = (b"local a, f = mk(1, 2)\n"
              b"print(f, getouter())\n"
              b"print(a[1]()) print(a[2]()) print(a[1]())\n"
              b"print(getouter())\n"
              b"local b = mk(false, false)\n"
              b"print(b[2]()) print(getouter())\n")
    a, b = _run_both(NESTED_SOURCE, driver)
    assert a == b, (a, b)
    assert a.strip(), "driver printed nothing -- the comparison is vacuous"


def test_a_closure_nested_inside_a_substituted_function_mixes_both_slot_kinds():
    """The text-level reading of the same fixture, so a regression that stopped
    MIXING the two slot kinds (e.g. boxing the inherited name) is caught as
    itself rather than only as a behaviour diff."""
    root, outcome, hc = hybrid_fixture(NESTED_SOURCE)
    assert hc is not None and hc.fallback_paths == frozenset({"main_0"})
    assert outcome.fallback_paths == frozenset({"main_0", "main_0_0"})
    assert shipping_violations(root, outcome, hc) == []
    # `mk` really does contain a nested function -- the property the corpus
    # cannot supply, asserted rather than assumed.
    assert len(root.subprotos[0].subprotos) == 1
    src = outcome.source.decode()
    assert "(function(__pld_U) return function()" in src   # inline factory
    assert "__pld_U[0].v" in src and "__pld_U[1].v" in src  # box slots
    assert "\nl0_0 = __pld_R[0]" in src                    # name slot, written
    # ...and the box arguments are the enclosing state machine's own registers,
    # evaluated before `__pld_U` shadows anything.
    assert "end end)({[0]=__pld_R[" in src


def test_dropping_the_upvalue_order_prologue_breaks_certification(monkeypatch):
    """Guard proof for `emit_inline`'s `order_prologue`.

    `lparser.c` assigns a nested function's upvalue INDICES in order of first
    mention and `pushclosure` emits the enclosing function's
    `MOVE`/`GETUPVAL` pseudo-instruction sequence in that same order, so a
    state machine that happens to touch its upvalues in a different order than
    the original did changes the ENCLOSING function's `code` -- and the
    enclosing function is the one whose fields the hybrid certification
    compares. Neutered here (prologue suppressed); the hybrid must stop
    certifying.

    `a = b` is the shape that separates the two orders. `lparser.c` registers
    an upvalue when the NAME is parsed, so the assignment target `a` takes
    index 0 and `b` index 1 -- but the code it generates is `GETUPVAL <-b`
    followed by `SETUPVAL ->a`, so `b` is what a pc-ordered state machine
    mentions first. Without the prologue the substituted function's upvalues
    come out as `(b, a)` and the enclosing chunk's pseudo-instruction pair
    after `CLOSURE` swaps with them.
    """
    src = b"""
local a, b = 1, 2
mixed = function(p, q) local r = (p or q) == 1 a = b return r end
"""
    S.clear_certification_cache()
    root = load_bytes(oracle.compile_source(src, strip=True))
    certs = {"main": S.certify_proto(root, is_chunk_root=True)}
    for i, sp in enumerate(root.subprotos):
        certs[f"main_{i}"] = S.certify_proto(sp, is_chunk_root=False)
    assert S.certify_hybrid(root, certs) is not None, "no hybrid to neuter"

    real = _FnEmitter.emit_inline
    monkeypatch.setattr(_FnEmitter, "emit_inline",
                        lambda self, *, order_prologue: real(
                            self, order_prologue=False))
    S.clear_certification_cache()
    assert S.certify_hybrid(root, certs) is None, (
        "the hybrid still certified without the upvalue-order prologue")


# --------------------------------------------------------------------------
# Corpus arm.
# --------------------------------------------------------------------------

HYBRID_FILES = ("snr_fragment_main.lua", "snr_s1_10_s.lua", "snr_s3_10_s.lua",
                "snr_s4_10_s.lua", "snr_s5_10_s.lua", "snr_story_main.lua")


def test_corpus_hybrid_files_ship_hybrid(corpus_dir, decompiled):
    """The six corpus files hybrid emission recovered, named so that one
    silently dropping back to a whole-file state machine fails here rather than
    only moving a score. Not a threshold: a file that starts shipping FULLY
    structured (a residual fix) also fails, and the right response is to move
    it out of this tuple in the same commit."""
    for name in HYBRID_FILES:
        res = decompiled(corpus_dir / name)
        assert res.hybrid is True, name
        assert any(res.shipped_fallback.values()), name
        assert not res.shipped_fallback["main"], name


def test_corpus_hybrid_invariant_on_one_file(corpus_dir):
    """The full `shipping_violations` check on a real corpus hybrid.

    One file, not six: this re-compiles the artifact and re-runs
    `compare_protos` over a 98-proto tree, and the suite has a 45s ceiling.
    `snr_s5_10_s.lua` is chosen because it is the only corpus hybrid with more
    than one substituted subtree, so the frontier logic is exercised rather
    than assumed."""
    from pyluadec.ingest import load_file
    root = load_file(corpus_dir / "snr_s5_10_s.lua")
    outcome = S.emit_certified_chunk(root)
    hc = S.certify_hybrid(root, outcome.certs)
    assert hc is not None
    assert len(hc.fallback_paths) == 2, sorted(hc.fallback_paths)
    assert shipping_violations(root, outcome, hc) == []


# --------------------------------------------------------------------------
# How much of the substituted code the two standing probes actually run.
# --------------------------------------------------------------------------

# Substituted functions per hybrid file (the frontier's size), measured
# 2026-08-12. Pinned so the reach measurement below cannot silently start
# injecting nothing.
SENTINELS_PER_FILE = {
    "snr_fragment_main.lua": 1, "snr_s1_10_s.lua": 1, "snr_s3_10_s.lua": 1,
    "snr_s4_10_s.lua": 1, "snr_s5_10_s.lua": 2, "snr_story_main.lua": 2,
}

# The files whose substituted code each standing probe EXECUTES, measured
# 2026-08-12 (round 1) by the test below. This is the honest scope of the
# claim "the probes are the semantic gate for the hybrid boundary": they gate
# it on 4 of the 6 files and on neither of the other two.
#
# `snr_fragment_main.lua`: its only global, `main`, errors after 12 recorded
# events, and the substituted `main_1` is a chunk LOCAL called from another
# chunk local -- nothing the invocation loop can reach.
# `snr_s5_10_s.lua`: the run hits the 3000-event cap before the invocation
# loop reaches the code that calls `main_42`/`main_43`. It is also the file
# `test_corpus_hybrid_invariant_on_one_file` picks, so it is doubly the least
# covered of the six.
PROBE_REACH_GLOBAL_STATE: frozenset[str] = frozenset()
PROBE_REACH_BEHAVIOUR = frozenset({
    "snr_s1_10_s.lua", "snr_s3_10_s.lua", "snr_s4_10_s.lua",
    "snr_story_main.lua"})


def test_probe_reach_of_the_substituted_code(corpus_dir, decompiled,
                                             monkeypatch):
    """Measure, two-directionally, which hybrids' substituted code the standing
    probes run at all.

    Inject an unconditional `error("PLD_SENTINEL")` at the entry of every
    substituted function and re-probe: if a probe's result moves, that probe
    executes the substituted code and would therefore catch a defect in it; if
    it does not move, the probe is blind to that file's boundary and its green
    says nothing about it.

    This exists because round 1 of this task claimed the probes were the
    boundary's semantic evidence for all 6 hybrids. They are not -- the
    committed injection (`test_a_broken_upvalue_write_at_the_boundary_diverges`)
    is also a no-op on the corpus, since none of the 8 substituted functions
    performs a `SETUPVAL` through a name slot (measured: all 6 artifacts stay
    byte-identical under that patch). Pinned rather than asserted-away so that
    a future hybrid landing in an unreached region is noticed: a file joining
    or leaving either set fails here and the pin must be re-derived in the same
    commit.

    Directly driving the two unreached files' substituted functions is not
    available: both are chunk LOCALS, and the original side is stripped
    bytecode with no source to append a driver to, so there is no symmetric way
    to call them. The synthetic differential tests above cover the boundary's
    mechanisms; this test bounds what the corpus gate adds to that.
    """
    from concurrent.futures import ThreadPoolExecutor
    import scripts.probe_behaviour as probe_behaviour
    import scripts.probe_global_state as probe_global_state
    from pyluadec.emit import lua as emit_lua
    from pyluadec.ingest import load_file

    real = emit_lua.inline_function_parts

    def injected(proto, path, upval_names):
        params, body = real(proto, path, upval_names)
        return params, 'error("PLD_SENTINEL")\n' + body

    monkeypatch.setattr(emit_lua, "inline_function_parts", injected)
    # Only the HYBRID memo is dropped: per-proto certification never consults
    # `fallback_paths` (`Printer.closure_parts` takes its no-substitutions
    # branch), so the warm `_CERT_CACHE` is still valid under the patch and
    # re-deriving ~50 verdicts per file would dominate this test's cost. The
    # autouse fence in conftest restores both dicts afterwards.
    sentinel: dict[str, bytes] = {}
    for name in HYBRID_FILES:
        S._HYBRID_CACHE.clear()
        out = S.emit_certified_chunk(load_file(corpus_dir / name))
        assert out.hybrid is True, name
        sentinel[name] = out.source
    S._HYBRID_CACHE.clear()

    assert {n: sentinel[n].count(b'error("PLD_SENTINEL")')
            for n in HYBRID_FILES} == SENTINELS_PER_FILE

    def one(name):
        clean = decompiled(corpus_dir / name).source
        g = (probe_global_state.probe(clean, is_source=True)
             != probe_global_state.probe(sentinel[name], is_source=True))
        b = (probe_behaviour.digest(probe_behaviour.probe_raw(
                 clean, is_source=True))
             != probe_behaviour.digest(probe_behaviour.probe_raw(
                 sentinel[name], is_source=True)))
        return name, g, b

    with ThreadPoolExecutor(max_workers=6) as ex:
        seen = list(ex.map(one, HYBRID_FILES))

    assert frozenset(n for n, g, _ in seen if g) == PROBE_REACH_GLOBAL_STATE
    assert frozenset(n for n, _, b in seen if b) == PROBE_REACH_BEHAVIOUR


def test_whole_file_fallback_still_confesses_every_proto():
    """The other branch is unchanged: when the ROOT's own body cannot be
    printed there is no structured code to keep, so the whole file falls back
    and every proto in it -- including the ones that certified `L3` on their
    own -- is confessed as state-machine text."""
    from pyluadec.pipeline import decompile_chunk
    S.clear_certification_cache()
    root = load_bytes(oracle.compile_source(
        b"local p, q = 1, 2 local x = (p or q) == 1\n"
        b"f = function(a) return a + 1 end\n", strip=True))
    res = decompile_chunk(root)
    assert res.hybrid is False
    assert res.levels["main_0"] == "L3"
    assert all(res.shipped_fallback.values())
    assert all(c and c[0]["reason"] == "fallback-state-machine"
               for c in res.confessions_by_proto.values())

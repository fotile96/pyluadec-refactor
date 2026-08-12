"""Per-proto L3 certification with wrapper isolation, and chunk assembly
(spec §4, §5; task 7). See src/pyluadec/structure/structured.py's module
docstring for the design this pins: a proto certifies L3 iff the structured
print of ITS OWN SUBTREE recompiles to a proto matching the original under
the normalization ladder, independently of whether its parent or siblings
certify.

BRIEF DEFECT (task-7-report.md has the full account): the task brief's own
Step-1 `_proto` helper compiled fixtures WITHOUT `-s`, while `certify_proto`
always recompiles the structured candidate WITH `strip=True`. Because
`verify.normalize._strip_lineinfo` is deliberately designed to blank locvar
*names* while keeping their count/startpc/endpc (see
`test_l31_strips_locvar_and_upvalue_names_but_keeps_counts` in
tests/test_normalize_l31.py -- a stronger, intentional check, not a bug),
comparing a debug-info-carrying original against an always-stripped
candidate can never match at any rung: the locvar record *count* never goes
to zero on the original's side. Real corpus protos are always pre-stripped
(CLAUDE.md), so the correct fixture convention -- already used by this
project's own tests/test_certify.py `_proto` helper -- is `-s` at compile
time. Fixed here by always compiling fixtures stripped.

A second, larger empirical finding (full detail and counts in
task-7-report.md's "mismatch breakdown"): several of the brief's own
illustrative sources (`local a=1 local b=2 print(a+b)`, the if/else
example) do NOT actually certify L3 against the real printer/classifier,
for reasons that have nothing to do with this module.
Both causes were diagnosed here and both are fixed as of M3 task 8, so what
follows is history rather than a live caveat. `classify_registers`' old
`_adjacent_pure` barrier (any `may_error`/heap-effect instruction -- which
includes any CALL -- between a register's def and use forced it "local"
rather than inlining it) turned almost any call-adjacent temp into an
explicit `local lN_M = ...` declaration that real `luac` never emits, so
`maxstacksize`/`code` diverged; it has been replaced by a simulation of
luac's own freereg discipline. Separately, a genuine reconstruction bug was
found here: an `If`'s two branches shared one `Reconstructor` "have I
emitted `local` for this register yet" state that was NOT scoped per-branch,
so a register given its first `local` declaration in the `then` branch
printed as a bare (unscoped -- silently a global write) assignment if the
`else` branch was the first to touch that same register number along ITS OWN
path. It was never observed in shipped output -- `certify_proto` correctly
returned L1 for every case that hit it, so the fallback state machine
shipped instead -- and it is now fixed by `Reconstructor.open_scope`/
`close_scope`. Every source below was verified against the real oracle
before being used as an expected-L3 fixture.
"""
import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _proto(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    # -s: real corpus protos are always pre-stripped (see module docstring's
    # "BRIEF DEFECT" note) -- an unstripped original can never match a
    # strip=True-recompiled candidate even when reconstruction is perfect.
    subprocess.run([str(BUILD / "luac_sz4"), "-s", "-o", str(o), str(s)], check=True)
    return load_file(o)


def test_straight_chunk_certifies_l3(tmp_path):
    from pyluadec.structure.structured import certify_proto
    c = certify_proto(_proto("local a = 1 return a", tmp_path), is_chunk_root=True)
    assert c.level == "L3" and c.rung is not None


def test_unstructurable_chunk_is_l1(tmp_path):
    """A chunk `print_chunk` refuses outright is L1 with no rung -- it never
    reaches the `certify_l3` comparison at all.

    Was `test_while_chunk_is_l1` until M4 task 3 structured `while`, then the
    and/or VALUE idiom until M4 task 4 reconstructed TESTSET -- both asserted
    below, so this test also pins those two gains. The sample is now the
    boolean-VALUE family (a comparison used as a value, materialised by
    `lcode.c:exp2reg` as a LOADBOOL pair).
    EXPIRY: whichever task reconstructs LOADBOOL value expressions."""
    from pyluadec.structure.structured import certify_proto
    c = certify_proto(_proto("local a, b = 1, 2 local x = (a or b) == 1 return x",
                             tmp_path), is_chunk_root=True)
    assert c.level == "L1" and c.rung is None
    w = certify_proto(_proto("local i = 0 while i < 3 do i = i + 1 end return i",
                             tmp_path), is_chunk_root=True)
    assert w.level == "L3"
    v = certify_proto(_proto("local a, b = 1, 2 local x = a or b return x",
                             tmp_path), is_chunk_root=True)
    assert v.level == "L3"


def test_printable_but_shape_mismatched_chunk_is_l1(tmp_path):
    """print_chunk SUCCEEDS here (unlike test_while_chunk_is_l1, which never
    reaches certify_l3 at all because print_chunk returns None) but the
    recompiled candidate's shape genuinely differs from the original, so this
    is the test that exercises the certify_l3 *comparison* path rather than
    the print_chunk-returns-None early-out.

    `local t = {} t[1] = 2 return t` prints as `local l0_0 = {[1] = 2}`.
    That is semantically identical and it compiles, but it is not the same
    bytecode: `NEWTABLE` carries array/hash size *hints* derived from the
    literal the parser saw, so a table built empty and then indexed differs
    from one built with the field inline -- `NEWTABLE 0 0 0` versus
    `NEWTABLE 0 0 1`. Nothing downstream of this module can recover which of
    the two the author wrote, which makes it a stable example of "printable,
    semantically right, still not certified".

    Until M3 task 8 this test used `local a = 1 local b = 2 print(a + b)`,
    which no longer serves: with the freereg-based register classification
    that source now certifies L3 (as the task-8 brief's own pipeline test
    expects it to).
    """
    from pyluadec.structure.structured import certify_proto
    c = certify_proto(_proto("local t = {} t[1] = 2 return t", tmp_path),
                      is_chunk_root=True)
    assert c.level == "L1" and c.rung is None and c.mismatches != ()


def test_printable_but_uncertified_chunk_falls_back_to_semantic_state_machine(tmp_path):
    """The invariant emit_certified_chunk exists to hold: printable is not
    certified. Unlike test_while_chunk_is_l1/test_straight_child_certifies_
    even_when_parent_has_while (where print_chunk(root) itself returns None,
    so falling back is trivially forced), this source's print_chunk SUCCEEDS
    -- it is the same shape-mismatched-but-printable chunk as
    test_printable_but_shape_mismatched_chunk_is_l1 -- so this is the one
    test in this file that actually exercises the "root printed fine but
    didn't certify -> still must fall back" branch of emit_certified_chunk,
    rather than the "didn't even print" branch every other fallback test
    here takes.
    """
    from pyluadec.structure.structured import emit_certified_chunk
    root = _proto("local t = {} t[1] = 2 return t", tmp_path)
    out = emit_certified_chunk(root)
    assert out.certs["main"].level == "L1"
    assert b"__pld_pc" in out.source


def test_nested_proto_certifies_via_wrapper(tmp_path):
    from pyluadec.structure.structured import certify_proto
    root = _proto("local n = 5 local f = function(x) return x + n end print(f(1))", tmp_path)
    inner = root.subprotos[0]              # captures n -> nups == 1
    assert inner.nups == 1
    c = certify_proto(inner, is_chunk_root=False)
    assert c.level == "L3", c.mismatches


def test_straight_child_certifies_even_when_parent_is_unstructurable(tmp_path):
    """The decoupling this design exists for: an unstructurable main must not
    poison its children. (Was `..._when_parent_has_while`, then TESTSET; the
    parent's blocker is now the boolean-VALUE family's LOADBOOL pair.
    EXPIRY: whichever task reconstructs LOADBOOL value expressions.)"""
    from pyluadec.structure.structured import emit_certified_chunk
    root = _proto(
        "local f = function(a, b) return a + b end\n"
        "local p, q = 1, 2 local x = (p or q) == 1 return f(x, 1)", tmp_path)
    out = emit_certified_chunk(root)
    assert out.certs["main"].level == "L1"          # LOADBOOL -> main falls back
    assert out.certs["main_0"].level == "L3"        # straight child certifies independently
    assert b"__pld_pc" in out.source                # artifact is the fallback chunk (root L1)


def test_fully_structured_chunk_ships_structured_source(tmp_path):
    """A root whose print recompiles to a matching proto -> structured source ships.

    Uses a numeric-for chunk rather than the brief's if/else example: see the
    module docstring's "BRIEF DEFECT" note -- no if/else example in this
    corpus's reach actually certifies L3, because of the branch-local-scope
    reconstruction bug documented there. This source was verified to
    certify L3 (rung 0) before being used here.
    """
    from pyluadec import oracle
    from pyluadec.structure.structured import emit_certified_chunk
    root = _proto("local s = 0 for i = 1, 3 do s = s + 1 end return s", tmp_path)
    out = emit_certified_chunk(root)
    assert out.certs["main"].level == "L3"
    assert b"__pld_pc" not in out.source            # structured artifact
    oracle.compile_source(out.source)


def test_output_always_compiles(tmp_path):
    from pyluadec import oracle
    from pyluadec.structure.structured import emit_certified_chunk
    for src in ("local a = 1 return a",
                "local i = 0 while i < 3 do i = i + 1 end return i",
                "for i = 1, 3 do print(i) end",
                "local n = 0 local f = function() return n end print(f())"):
        out = emit_certified_chunk(_proto(src, tmp_path))
        oracle.compile_source(out.source)


def test_l3_really_means_roundtrip(tmp_path):
    from pyluadec import oracle
    from pyluadec.emit.lua import print_chunk
    from pyluadec.ingest import load_bytes
    from pyluadec.structure.structured import certify_proto
    from pyluadec.verify.normalize import NORMALIZATIONS, compare_protos
    p = _proto("local s = 0 for i = 1, 3 do s = s + 1 end return s", tmp_path)
    assert certify_proto(p, is_chunk_root=True).level == "L3"
    src = print_chunk(p)
    recompiled = load_bytes(oracle.compile_source(src.encode(), strip=True))
    assert compare_protos(p, recompiled, level=len(NORMALIZATIONS)) == []


def test_deeply_nested_proto_certifies_via_wrapper(tmp_path):
    """A grandchild (root.subprotos[0].subprotos[0]) certified in isolation:
    its wrapper always prints at depth=1 regardless of its true nesting
    depth in the real tree, since the wrapper source treats it as if it
    were a fresh top-level closure. Guards against a depth-mismatch
    regression between the wrapper's declared parameter names and
    _print_proto_body's own name_for(reg, depth) synthesis. x and y are
    both real parameters (never inlined, per classify_registers' "a
    parameter's register is always local" rule), so this sidesteps the
    temp-inlining divergence documented in the module docstring.
    """
    from pyluadec.structure.structured import certify_proto
    root = _proto(
        "local function outer(x)\n"
        "  local function inner(y)\n"
        "    return x + y\n"
        "  end\n"
        "  return inner(1)\n"
        "end\n"
        "print(outer(2))\n", tmp_path)
    grandchild = root.subprotos[0].subprotos[0]
    assert grandchild.nups >= 1
    c = certify_proto(grandchild, is_chunk_root=False)
    assert c.level == "L3", c.mismatches


def test_memoization_reuses_cert_for_structurally_identical_protos(tmp_path):
    """Two syntactically distinct but structurally identical closures must
    certify to the SAME outcome via emit_certified_chunk's structural_hash
    memoization. The chunk's main itself does not certify L3 here (the
    call-argument staging in `print(f(1,2), g(3,4))` hits the same
    inlining-barrier divergence documented in the module docstring), which
    is fine -- this test is about the two identical children, not main.
    """
    from pyluadec.structure.structured import emit_certified_chunk
    root = _proto(
        "local f = function(a, b) return a + b end\n"
        "local g = function(a, b) return a + b end\n"
        "print(f(1, 2), g(3, 4))\n", tmp_path)
    out = emit_certified_chunk(root)
    assert out.certs["main_0"].level == "L3", out.certs["main_0"].mismatches
    assert out.certs["main_1"].level == "L3", out.certs["main_1"].mismatches
    assert out.certs["main_0"] == out.certs["main_1"]


def test_same_structural_hash_different_debug_info_certify_independently(tmp_path):
    """Round-1 review finding: structural_hash omits locvars entirely (and
    reduces upvalues/source to a bare count -- see verify/ledger.py's own
    _structure_view), while compare_protos DOES check locvars, and
    _strip_lineinfo only blanks locvar NAMES, not their count/pc ranges. So
    two protos can share a structural_hash while genuinely certifying
    differently -- and a structural_hash-keyed memo would silently share
    whichever verdict was computed first.

    This is not reachable from any real load_file/load_bytes tree (a compiled
    dump is uniformly -s-stripped or not, tree-wide), so the counterexample
    has to be built by hand: take a genuinely-L3 nested proto, and
    dataclasses.replace a stray LocVar onto an otherwise byte-identical
    sibling -- same structural_hash, but an independently computed
    certify_proto disagrees (L1, locvars mismatch). Grafted as an extra,
    CLOSURE-unreferenced subprotos[1] entry alongside the real subprotos[0] so
    main's own bytecode/CLOSURE-pseudo table (which only ever indexes
    subprotos[0]) is untouched and doesn't itself crash.

    Before the round-1 fix, emit_certified_chunk did not detect this at all:
    `main_0_1` (the fake) silently inherited `main_0_0`'s (the real proto's)
    L3 verdict via the shared memo entry, and an `is` check confirmed they
    were literally the same ProtoCert object.

    Round 1 fixed it by asserting uniform debug-completeness across the tree
    and refusing to memoize otherwise. M3 task 8 replaced that assertion with
    a memo key that is correct instead of merely defended -- `_memo_key` =
    structural_hash + _debug_fingerprint, covering every field compare_protos
    examines -- so the two protos now get INDEPENDENT verdicts rather than a
    refusal. That is a strictly better outcome (the round-1 assertion also had
    a false positive that fired on ordinary unstripped input once
    emit_certified_chunk acquired a production caller in pipeline.py), and
    this test now pins the independence directly, which is the property that
    actually matters.
    """
    import dataclasses
    from pyluadec.ingest.proto import LocVar
    from pyluadec.verify.ledger import structural_hash
    from pyluadec.structure.structured import emit_certified_chunk, certify_proto

    root = _proto(
        "local function outer(x)\n"
        "  local function inner(y)\n"
        "    return x + y\n"
        "  end\n"
        "  return inner(1)\n"
        "end\n"
        "print(outer(2))\n", tmp_path)
    outer = root.subprotos[0]
    grandchild = outer.subprotos[0]
    fake = dataclasses.replace(grandchild, locvars=(LocVar(name=None, startpc=0, endpc=1),))
    assert structural_hash(grandchild) == structural_hash(fake)
    # The two genuinely disagree when certified independently -- that is what
    # makes sharing a memo entry between them a defect and not an optimisation.
    assert certify_proto(grandchild, is_chunk_root=False).level == "L3"
    assert certify_proto(fake, is_chunk_root=False).level == "L1"

    outer2 = dataclasses.replace(outer, subprotos=(grandchild, fake))
    synthetic_root = dataclasses.replace(root, subprotos=(outer2,))

    out = emit_certified_chunk(synthetic_root)
    assert out.certs["main_0_0"].level == "L3"
    assert out.certs["main_0_1"].level == "L1"
    assert out.certs["main_0_0"] is not out.certs["main_0_1"]


def test_identical_protos_still_share_one_memo_entry(tmp_path):
    """The other half of _memo_key: two byte-identical protos in one tree must
    still be certified once and share the result, or the extra precision
    would have cost the memoization its whole purpose (one luac_sz4 subprocess
    per proto is certification's dominant cost)."""
    import dataclasses
    from pyluadec.structure.structured import emit_certified_chunk

    root = _proto(
        "local function outer(x)\n"
        "  local function inner(y)\n"
        "    return x + y\n"
        "  end\n"
        "  return inner(1)\n"
        "end\n"
        "print(outer(2))\n", tmp_path)
    outer = root.subprotos[0]
    grandchild = outer.subprotos[0]
    outer2 = dataclasses.replace(outer, subprotos=(grandchild, grandchild))
    synthetic_root = dataclasses.replace(root, subprotos=(outer2,))

    out = emit_certified_chunk(synthetic_root)
    assert out.certs["main_0_0"] is out.certs["main_0_1"]


def test_refusal_and_rejection_carry_distinguishable_reasons(tmp_path):
    """The M4 task 6 field: a non-`L3` verdict must say WHY, and a printer
    refusal must not read the same as a comparison rejection.

    Before this field the ledger recorded both as the same generic
    `fallback-state-machine` confession, which was harmless only while
    "printed fine, failed the comparison" did not happen; M4's loop work
    made it the second-largest residual cluster. The two fixtures below are
    the same ones `test_unstructurable_chunk_is_l1` and
    `test_printable_but_shape_mismatched_chunk_is_l1` use, so the shapes are
    already pinned -- what is new is that their reasons differ in KIND.
    """
    from pyluadec.structure.structured import certify_proto

    ok = certify_proto(_proto("local a = 1 return a", tmp_path), is_chunk_root=True)
    assert ok.level == "L3" and ok.reason is None

    refused = certify_proto(
        _proto("local a, b = 1, 2 local x = (a or b) == 1 return x", tmp_path),
        is_chunk_root=True)
    assert refused.level == "L1"
    assert refused.reason.startswith("structure: "), refused.reason

    rejected = certify_proto(_proto("local t = {} t[1] = 2 return t", tmp_path),
                             is_chunk_root=True)
    assert rejected.level == "L1"
    # `NEWTABLE`'s array/hash size hints differ -> the first mismatch is on
    # `code`. The field NAME is the whole reason: the mismatch's `a`/`b`
    # reprs hold the actual instruction words and constants, which are
    # bytecode-derived payload and must not reach the committed ledger.
    assert rejected.reason == "mismatch: code", rejected.reason
    assert repr(rejected.mismatches[0].a) not in rejected.reason


def test_nested_refusal_also_carries_a_reason(tmp_path):
    """The wrapper path (`is_chunk_root=False`) has its own refusal/rejection
    returns; a reason added only to the chunk-root path would leave every
    nested proto's ledger row blank, which is 1715 of the corpus's 1944."""
    from pyluadec.structure.structured import certify_proto
    root = _proto(
        "local f = function(p, q) local x = (p or q) == 1 return x end return f",
        tmp_path)
    c = certify_proto(root.subprotos[0], is_chunk_root=False)
    assert c.level == "L1"
    assert c.reason.startswith("structure: ") or c.reason.startswith("reconstruct: "), c.reason


def test_table_constructor_fold_reorders_statements_but_cannot_ship(tmp_path):
    """A real, pre-existing evaluation-order defect in the constructor fold,
    pinned as the census entry it is (M4 task 6; the defect predates M4 task
    13 -- verified against `dec39c5`-era behaviour by the task 13 reviewer).

    `express.reconstruct` folds a table's later field assignments back into
    its constructor, and prints the constructor at the position of the LAST
    folded assignment. Any effectful statement that stood between the first
    folded item and that position is therefore printed BEFORE that item is
    evaluated. Measured here: the original prints `1 x 2`, the structured
    print prints `x 1 2`.

    Two things this test asserts, and one it deliberately does not:

    * the reordering is real and observable (the two stdouts differ);
    * it is UNSHIPPABLE -- the root does not certify, so `emit_certified_chunk`
      ships the fallback chunk, whose stdout matches the original exactly.
      This is the whole point of the certification gate: a reconstruction bug
      can only ever cost L3 rate, never correctness.
    * it does NOT assert the reordering is fixed. When someone does fix it,
      the `!=` below starts failing, which is the intended notification.

    (The brief's own one-liner repro, `local t = {} print(1)`, does reorder
    the statements -- the `local` moves after the `print` -- but is NOT
    observable: the only statement that moves there is a pure `NEWTABLE`.
    Making the divergence observable needs two folded items straddling an
    effectful statement, which is what this fixture is.)
    """
    from pyluadec import oracle
    from pyluadec.emit.lua import print_chunk
    from pyluadec.structure.structured import emit_certified_chunk

    src = ("local function s(n) print(n) return n end\n"
           "local t = {}\n"
           "t.a = s(1)\n"
           'print("x")\n'
           "t.b = s(2)\n"
           "print(t.a, t.b)\n")
    root = _proto(src, tmp_path)

    printed = print_chunk(root)
    assert printed is not None                      # it prints...
    original_out = oracle.run_bytes(src.encode(), is_source=True).stdout
    printed_out = oracle.run_bytes(printed.encode(), is_source=True).stdout
    assert original_out == b"1\nx\n2\n1\t2\n"
    assert printed_out == b"x\n1\n2\n1\t2\n"
    assert printed_out != original_out              # ...wrongly

    out = emit_certified_chunk(root)
    assert out.certs["main"].level == "L1"          # ...and does not certify
    assert b"__pld_pc" in out.source                # ...so the fallback ships
    assert oracle.run_bytes(out.source, is_source=True).stdout == original_out


# --------------------------------------------------------------------------
# Process-level certification cache (M5 task 2)
#
# The three tests below pin the cache's two soundness invariants and its one
# performance property. Each monkeypatches `_CERT_CACHE` to a private empty
# dict rather than clearing the module's own: the real cache is warm by the
# time this module runs (test_behaviour_probe.py and test_ledger_ratchet.py
# both sort before it), and wiping it would silently hand the rest of the
# suite a cold cache -- an invisible several-second regression rather than a
# failure.
# --------------------------------------------------------------------------

def _grafted_pair(tmp_path):
    """A genuinely-L3 nested proto and a byte-identical sibling carrying one
    stray `LocVar`: same `structural_hash`, different `_debug_fingerprint`,
    and genuinely different verdicts. Same construction as
    `test_same_structural_hash_different_debug_info_certify_independently`
    above (which pins the per-chunk case); factored out here because the
    process-cache test needs the same counterexample across SEPARATE
    top-level calls, which is the case the per-chunk memo never saw.
    """
    import dataclasses
    from pyluadec.ingest.proto import LocVar

    root = _proto(
        "local function outer(x)\n"
        "  local function inner(y)\n"
        "    return x + y\n"
        "  end\n"
        "  return inner(1)\n"
        "end\n"
        "print(outer(2))\n", tmp_path)
    grandchild = root.subprotos[0].subprotos[0]
    fake = dataclasses.replace(
        grandchild, locvars=(LocVar(name=None, startpc=0, endpc=1),))
    return root, grandchild, fake


def test_process_cache_is_live_and_keyed_on_more_than_structural_hash(
        tmp_path, monkeypatch):
    """Invariant 1, through the PROCESS-level cache rather than the per-chunk
    memo: two protos sharing a `structural_hash` but not a
    `_debug_fingerprint` must get independent verdicts even when certified by
    two unrelated top-level calls, and repeat certifications of either must be
    served from the cache rather than recomputed.

    Both halves are load-bearing and they fail differently, which is what
    makes this test meaningful rather than vacuous:

    * With NO cache at all the `is` assertions fail -- a fresh
      `certify_proto` call always builds a new `ProtoCert` -- so the test
      cannot pass by the cache simply not existing.
    * With a cache keyed on `structural_hash` alone the verdict assertions
      fail: `fake` inherits `grandchild`'s L3 rather than earning its own L1.

    Both were run as neuter proofs (task-2-report.md).
    """
    from pyluadec.structure import structured as S

    monkeypatch.setattr(S, "_CERT_CACHE", {})
    _, grandchild, fake = _grafted_pair(tmp_path)

    a = S.certify_proto(grandchild, is_chunk_root=False)
    b = S.certify_proto(fake, is_chunk_root=False)
    assert a.level == "L3", a.mismatches
    assert b.level == "L1"
    assert a is not b

    # ...and the cache is what is being tested: a repeat of either call must
    # return the very object already computed, across call boundaries.
    assert S.certify_proto(grandchild, is_chunk_root=False) is a
    assert S.certify_proto(fake, is_chunk_root=False) is b
    assert len(S._CERT_CACHE) == 2


def test_process_cache_separates_chunk_root_from_nested_certification(
        tmp_path, monkeypatch):
    """`is_chunk_root` is part of the cache key, because it selects an
    entirely different certification procedure (compile the print as a whole
    chunk vs. wrap it in `local u0 ... return function(...) ... end`) for the
    same `_memo_key`.

    The per-chunk memo did not need this: a root and a strict descendant of
    itself cannot share a `_memo_key` (`structural_hash` folds subprotos
    recursively, so the key is well-founded on depth), which is the argument
    `ProtoCert.source`'s field comment used to have to make. A process-level
    cache spans chunks, where no such relation constrains the two callers, so
    the flag goes in the key and the argument is no longer needed.

    Observable difference: a chunk-root L3 carries `source` (the exact bytes
    that were compiled and compared); the nested certification of the same
    proto never does. Neuter proof: drop `is_chunk_root` from the key and the
    second call returns the first's object, `source` included.
    """
    from pyluadec.structure import structured as S

    monkeypatch.setattr(S, "_CERT_CACHE", {})
    p = _proto("local a = 1 return a", tmp_path)

    as_root = S.certify_proto(p, is_chunk_root=True)
    as_nested = S.certify_proto(p, is_chunk_root=False)
    assert as_root.level == "L3", as_root.mismatches
    assert as_root.source is not None
    assert as_nested is not as_root
    assert as_nested.source is None
    assert len(S._CERT_CACHE) == 2


def _refusing_luac(d: Path) -> Path:
    """A directory holding a `luac_sz4` that refuses every input.

    `oracle.build_dir()` only checks that the file exists, and
    `oracle.compile_source` reports a non-zero exit as `LuaCompileError`, so
    this turns every certification into `L1 compile: candidate chunk did not
    recompile`. That is the loudest possible "the compiler changed" signal: a
    proto that certified `L3` against the real oracle cannot certify against
    this one, so a cache that still answers `L3` is unambiguously serving a
    verdict measured against a compiler that is no longer there.
    """
    d.mkdir(parents=True, exist_ok=True)
    stub = d / "luac_sz4"
    stub.write_text("#!/bin/sh\nexit 1\n")
    stub.chmod(0o755)
    return stub


def test_process_cache_does_not_survive_a_build_dir_swap(tmp_path, monkeypatch):
    """Invariant 4, channel 1: `PYLUADEC_BUILD_DIR` swaps the oracle binary
    underneath a live process, and the cache must not answer from the old
    one's verdicts.

    `oracle.build_dir()` re-reads that environment variable on every
    `compile_source` call -- it is a documented, supported knob
    (docs/runbooks/decompile-pipeline.md), not a test-only seam -- so this is
    a real way for the compiler to move mid-process, and the round-1 review of
    M5 task 2 demonstrated it serving a stale `L3` against the original
    `git log`-hash key. Three steps; the middle one is the neuter target
    (drop `_oracle_identity()` from the key and step 2 returns `first`), and
    step 3 proves the identity PARTITIONS the cache rather than overwriting a
    single slot.

    A byte-identical ledger would not catch this failure: the stale verdicts
    are internally consistent and simply describe the wrong compiler.
    """
    from pyluadec.structure import structured as S

    monkeypatch.setattr(S, "_CERT_CACHE", {})
    p = _proto("local a = 1 return a", tmp_path)

    first = S.certify_proto(p, is_chunk_root=True)
    assert first.level == "L3", first.mismatches
    assert S.certify_proto(p, is_chunk_root=True) is first      # 1. cached

    _refusing_luac(tmp_path / "fake_build")                     # 2. swap
    monkeypatch.setenv("PYLUADEC_BUILD_DIR", str(tmp_path / "fake_build"))
    after = S.certify_proto(p, is_chunk_root=True)
    assert after is not first, (
        "the pre-swap verdict was reused after PYLUADEC_BUILD_DIR moved the "
        "oracle binary")
    assert after.level == "L1"
    assert after.reason == "compile: candidate chunk did not recompile"

    monkeypatch.delenv("PYLUADEC_BUILD_DIR")                    # 3. back again
    assert S.certify_proto(p, is_chunk_root=True) is first, (
        "the real oracle's entry did not survive the detour -- the identity "
        "is not in the key, it is merely overwriting one")


def test_process_cache_does_not_survive_a_luac_rebuilt_in_place(
        tmp_path, monkeypatch):
    """Invariant 4, channel 2: the oracle binary is REPLACED AT THE SAME PATH,
    which is what `./scripts/build_native.sh` does to `build/luac_sz4`.

    Distinct from the swap test above and it is the reason the key carries
    `(mtime_ns, size)` and not just the path: here `oracle.luac_sz4()` returns
    the identical string before and after (asserted), so a path-only identity
    would serve the pre-rebuild verdict. Neuter target: key on
    `str(oracle.luac_sz4())` alone and this test fails while the swap test
    still passes.
    """
    import shutil
    from pyluadec import oracle
    from pyluadec.structure import structured as S

    build = tmp_path / "build"
    build.mkdir()
    shutil.copy2(BUILD / "luac_sz4", build / "luac_sz4")
    monkeypatch.setenv("PYLUADEC_BUILD_DIR", str(build))
    monkeypatch.setattr(S, "_CERT_CACHE", {})
    p = _proto("local a = 1 return a", tmp_path)

    before_path = str(oracle.luac_sz4())
    first = S.certify_proto(p, is_chunk_root=True)
    assert first.level == "L3", first.mismatches
    assert S.certify_proto(p, is_chunk_root=True) is first

    _refusing_luac(build)                       # same path, new bytes
    assert str(oracle.luac_sz4()) == before_path

    after = S.certify_proto(p, is_chunk_root=True)
    assert after is not first, (
        "the pre-rebuild verdict was reused after luac_sz4 was rebuilt in "
        "place -- the key does not distinguish two binaries at one path")
    assert after.level == "L1"
    assert after.reason == "compile: candidate chunk did not recompile"


def test_clear_certification_cache_drops_every_entry(tmp_path, monkeypatch):
    """`clear_certification_cache()` is the only escape hatch from this
    module's process-lifetime dict, so it gets the three lines that keep it
    from rotting into a no-op.

    Asserted through the public surface rather than by poking the dict: after
    the clear, a repeat `certify_proto` must return a DIFFERENT object with
    the SAME verdict -- recomputed, not served, and recomputed correctly.
    """
    from pyluadec.structure import structured as S

    cache: dict = {}
    monkeypatch.setattr(S, "_CERT_CACHE", cache)
    p = _proto("local a = 1 return a", tmp_path)

    first = S.certify_proto(p, is_chunk_root=True)
    assert S.certify_proto(p, is_chunk_root=True) is first
    assert cache

    S.clear_certification_cache()
    assert cache == {}

    again = S.certify_proto(p, is_chunk_root=True)
    assert again is not first
    assert again.level == first.level == "L3"
    assert again.source == first.source


# --- The shared cache versus fault injection (round-1 Important 2) ----------
#
# These two tests are a PAIR and their order matters: the first deliberately
# poisons `structure.structured`'s real, process-lifetime cache from under a
# monkeypatch, and the second checks the poison did not outlive it. What makes
# the second one pass is tests/conftest.py's autouse `_fence_certification_
# cache` fixture. Without the fence the second test fails (verified by
# disabling the fixture: `L1` instead of `L3`), which is the whole point --
# `monkeypatch` restores the attribute it patched and cannot restore cache
# entries computed while it was in force.
#
# They are written against the REAL cache on purpose. Every other test in this
# section monkeypatches `_CERT_CACHE` to a private dict, which is the right
# thing for a test about the cache's key; it is also exactly the discipline a
# future fault-injection author will not know to follow, so something has to
# test the case where nobody followed it.
#
# The source is unique to this pair, and that is load-bearing: the first
# draft used `local a = 1 return a`, which `test_straight_chunk_certifies_l3`
# above has already certified through the real cache, so the poisoner got a
# cache HIT and never wrote anything (it asserted `L1` and saw `L3`). A shared
# cache makes fixture sources shared state; this one is used nowhere else.
_POISON_SRC = "local q1, q2 = 11, 22 return q1 + q2"


def test_a_patched_printer_writes_a_wrong_verdict_into_the_shared_cache(
        tmp_path, monkeypatch):
    """Half 1 of the pair: poison the real cache under an ordinary key.

    The patched printer emits `return 0` for every proto, so the candidate
    recompiles fine and simply is not the original -- an `L1 mismatch` verdict
    for a proto that genuinely certifies `L3`. The key is untouched by the
    patch (it is a function of the proto and the oracle binary, neither of
    which moved), so this entry is indistinguishable from a real one.
    """
    from pyluadec.structure import structured as S

    p = _proto(_POISON_SRC, tmp_path)
    monkeypatch.setattr(S, "print_chunk_or_raise", lambda proto: "return 0\n")

    poisoned = S.certify_proto(p, is_chunk_root=True)
    assert poisoned.level == "L1"
    assert poisoned.reason is not None
    assert poisoned.reason.startswith("mismatch:")


def test_the_poisoned_verdict_did_not_outlive_the_test_that_wrote_it(tmp_path):
    """Half 2: the same proto, no patch, no private cache -- the verdict must
    be the true one.

    `_proto` compiles the same source in a different tmp dir, and `-s` strips
    the source name, so the two protos have the same `_memo_key` (verified:
    the key is content-derived, `source` is `b'=?'` in both). This test would
    therefore consume the previous test's entry if anything kept it.
    """
    from pyluadec.structure import structured as S

    c = S.certify_proto(_proto(_POISON_SRC, tmp_path), is_chunk_root=True)
    assert c.level == "L3", (
        "a verdict computed under a monkeypatched printer survived into "
        "another test -- tests/conftest.py::_fence_certification_cache is "
        "not fencing the shared cache")

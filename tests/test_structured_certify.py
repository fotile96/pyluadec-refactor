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


def test_while_chunk_is_l1(tmp_path):
    from pyluadec.structure.structured import certify_proto
    c = certify_proto(_proto("local i = 0 while i < 3 do i = i + 1 end return i", tmp_path),
                      is_chunk_root=True)
    assert c.level == "L1" and c.rung is None


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


def test_straight_child_certifies_even_when_parent_has_while(tmp_path):
    """The decoupling this design exists for: a while-y main must not poison its children."""
    from pyluadec.structure.structured import emit_certified_chunk
    root = _proto(
        "local f = function(a, b) return a + b end\n"
        "local i = 0 while i < 3 do i = i + f(1, 0) end return i", tmp_path)
    out = emit_certified_chunk(root)
    assert out.certs["main"].level == "L1"          # while -> main falls back
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

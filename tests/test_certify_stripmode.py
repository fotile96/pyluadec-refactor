"""M4 task 7: the candidate's strip mode follows the original's.

`certify_l3` and `certify_proto`'s wrapper path used to compile the structured
candidate with `strip=True` unconditionally. That is right for this corpus (all
229 files are `-s`-stripped) but it made the gate weaker than it could be and
made the decompiler behave badly on ordinary `luac` output. Both halves are
pinned here.

**The weakness, stated precisely.** Rung 1 (`_strip_lineinfo`) blanks each
`LocVar`'s NAME but keeps its `startpc`/`endpc`. That is meant to be a
scope-range check. When both sides are stripped, though, both `locvars` tuples
are empty and the check compares `() == ()` -- it cannot fail, so it proves
nothing. Compiling the candidate unstripped whenever the original is unstripped
turns that vacuous comparison into a real one: it checks that every `local` was
reconstructed into the same lexical block over the same pc range.

The negative control below is what makes that claim falsifiable rather than
decorative: a candidate that hoists a local out of a `do` block, whose `code` is
byte-identical to the original's, is accepted when both sides are stripped and
refused when the original carries debug info.
"""
import pytest

from pyluadec import oracle
from pyluadec.ingest import load_bytes
from pyluadec.ingest.proto import LocVar, Proto
from pyluadec.verify.certify import carries_debug, certify_l3


def _proto(src: bytes, *, strip: bool) -> Proto:
    return load_bytes(oracle.compile_source(src, strip=strip))


# --- the negative control -------------------------------------------------
#
# Three sources chosen (measured 2026-08-12) so that all three compile to
# BYTE-IDENTICAL `code`, `constants` and `maxstacksize`, and differ only in one
# `LocVar`'s `endpc`:
#
#   _ORIG  the original: `a` lives inside the `do` block, endpc=5
#   _GOOD  a faithful reconstruction: same block, decompiler-style name, endpc=5
#   _BAD   the defect: `a` hoisted out of the `do` block, endpc=6
#
# The trailing bare `return` is load-bearing. Lua 5.1's `close_func` calls
# `removevars` BEFORE emitting the function's implicit final RETURN, so a
# chunk-level local's `endpc` lands one pc later than a `do` block's
# `leaveblock` would put it -- while the explicit `return` statement, which
# allocates no register, leaves the instruction stream identical. Without it
# (`do local a = f() g(a) end` vs `local a = f() g(a)`) both `endpc`s are 5 and
# there is nothing to detect; with anything that allocates a register after the
# block (`h()`, `return 1`) the hoisted local shifts every later register and
# the mismatch lands on `code` instead of `locvars`, proving nothing about
# scopes.
_ORIG = b"do local a = f() g(a) end\nreturn\n"
_GOOD = b"do local l0_0 = f() g(l0_0) end\nreturn\n"
_BAD = b"local l0_0 = f() g(l0_0)\nreturn\n"


def test_wrong_lexical_block_has_identical_code():
    """The premise of the negative control: the hoist is invisible in `code`.

    If this ever stops holding, the two tests below would be rejecting `_BAD`
    on the instruction stream rather than on scope ranges, and would no longer
    say anything about what rung 1 compares.
    """
    orig, bad = _proto(_ORIG, strip=True), _proto(_BAD, strip=True)
    assert orig.code == bad.code
    assert orig.constants == bad.constants
    assert orig.maxstacksize == bad.maxstacksize


def test_wrong_lexical_block_is_invisible_when_both_sides_stripped():
    """The weakness this task removes, stated as a passing test.

    A stripped original cannot distinguish the faithful reconstruction from the
    one that put the local in the wrong block: both certify. This is not a bug
    -- a stripped dump genuinely does not record scopes -- but it is why the
    corpus result cannot move, and why the gate had to be pointed at unstripped
    input to gain anything.
    """
    orig = _proto(_ORIG, strip=True)
    assert certify_l3(orig, _GOOD).level == "L3"
    assert certify_l3(orig, _BAD).level == "L3"


def test_correct_lexical_block_certifies_when_original_carries_debug():
    """Paired positive control -- without this, the negative control below
    would be satisfied by a gate that simply refuses all unstripped input
    (which is exactly what the gate did before this task)."""
    r = certify_l3(_proto(_ORIG, strip=False), _GOOD)
    assert r.level == "L3", r.mismatches
    assert r.rung == 1          # names differ (`a` vs `l0_0`), scopes do not


def test_wrong_lexical_block_is_refused_when_original_carries_debug():
    """The task's reason to exist: rung 1 compares REAL scope ranges.

    Refused on `locvars` alone -- not on `code`, not on a vacuous
    empty-vs-nonempty tuple. Both sides carry one named-blanked `LocVar` and
    they differ only in `endpc`, i.e. in which lexical block the local was
    declared in.
    """
    r = certify_l3(_proto(_ORIG, strip=False), _BAD)
    assert r.level == "L1"
    assert [m.field for m in r.mismatches] == ["locvars"]
    m = r.mismatches[0]
    # Both sides non-empty is the whole point: before this task the candidate
    # side was `()` and the comparison carried no information about scopes.
    assert m.a == "(LocVar(name=None, startpc=2, endpc=5),)"
    assert m.b == "(LocVar(name=None, startpc=2, endpc=6),)"


# --- positive controls ----------------------------------------------------


@pytest.mark.parametrize("src", [
    b"local a = 1\nprint(a)\n",
    b"for i = 1, 10 do print(i) end\n",
    b"local function f(x) local y = x + 1 return y end\nreturn f(2)\n",
])
def test_unstripped_originals_with_locals_now_certify(src):
    """Measured 2026-08-11 and re-measured 2026-08-12 before the change: each
    of these certified `L3` rung 0 compiled `-s` and `L1` with
    `Mismatch(field='locvars')` compiled without. The rule was "a proto whose
    SUBTREE declares even one local can only certify if the original was
    stripped", which is nearly every real function."""
    r = certify_l3(_proto(src, strip=False), src)
    assert r.level == "L3", r.mismatches


@pytest.mark.parametrize("src", [b"x = 1\n", b"print(1)\n"])
def test_unstripped_originals_without_locals_still_certify(src):
    """These already certified before the change (nothing in their subtree
    declares a local, so the vacuous `() == ()` comparison passed). Pinned so
    the change is visibly additive here rather than a swap."""
    assert certify_l3(_proto(src, strip=False), src).level == "L3"


@pytest.mark.parametrize("src", [
    b"local a = 1\nprint(a)\n",
    b"do local a = f() g(a) end\nreturn\n",
    b"x = 1\n",
])
def test_stripped_originals_are_untouched(src):
    """The corpus path. A stripped original still gets a stripped candidate, so
    every verdict on this side of the branch is bit-for-bit what it was --
    which is why `corpus/ledger.jsonl` must not move."""
    r = certify_l3(_proto(src, strip=True), src)
    assert r.level == "L3" and r.rung == 0


def test_nested_wrapper_path_certifies_unstripped_original():
    """`certify_proto(is_chunk_root=False)` compiles a wrapper, not a chunk, so
    it selects the strip mode itself; this pins that it makes the same choice.

    Measured 2026-08-12: before the change this nested proto came back `L1`
    with `Mismatch(field='locvars', b='()')` -- the wrapper's candidate had no
    debug segment at all. It now certifies at rung 1, and the two locvars it
    matches (the parameter and the body local) carry real, equal scope ranges.
    """
    from pyluadec.structure.structured import certify_proto
    root = _proto(b"local function f(x) local y = g(x) h(y) return y end\n"
                  b"return f(2)\n", strip=False)
    nested = root.subprotos[0]
    assert len(nested.locvars) == 2, "fixture must declare locals to exercise the branch"
    cert = certify_proto(nested, is_chunk_root=False)
    assert cert.level == "L3", cert.mismatches
    assert cert.rung == 1


# --- the other direction: a stricter gate also refuses more ---------------
#
# The brief for this task asked for a change that is "strictly stronger": no
# input that certified before may stop certifying. Measured 2026-08-12 over 30
# hand-written sources compiled both ways, that is FALSE, and it is false for a
# reason inherent to the change rather than a defect in it. 12 unstripped
# sources went `L1 -> L3`; 2 went `L3 -> L1`. Both of the latter are the
# newly-non-vacuous `locvars` comparison firing correctly: the printer
# materialises a `local` the original source never declared. The bytecode is
# byte-identical (`code` matches), so under the old always-`-s` candidate the
# invented local was invisible.
#
# That is what "stricter" means. A gate cannot start examining a dimension and
# also promise never to reject on it. The stripped branch -- the corpus, and
# every fixture in the rest of the suite -- is untouched code and cannot move;
# see `test_stripped_originals_are_untouched` and
# `test_every_corpus_proto_reads_as_stripped`.

@pytest.mark.parametrize("src,invented", [
    (b"repeat f() until g()", "(LocVar(name=None, startpc=4, endpc=6),)"),
    (b"return a and b or c", "(LocVar(name=None, startpc=7, endpc=8),)"),
])
def test_stricter_gate_refuses_reconstructions_that_invent_a_local(src, invented):
    """These two certified `L3` rung 1 before this task and are refused now.

    The original declares no locals; our structured print declares one (for
    `repeat`'s condition value, and for the `and`/`or` chain's result). The
    instruction stream is unaffected -- `luac` would have used the same
    register either way -- so the ONLY evidence of the difference is the
    locvar the old gate threw away.
    """
    from pyluadec.emit.lua import print_chunk
    orig = _proto(src, strip=False)
    assert orig.locvars == ()
    printed = print_chunk(orig).encode()
    candidate = _proto(printed, strip=False)
    assert candidate.code == orig.code, "premise: the invention is invisible in `code`"

    r = certify_l3(orig, printed)
    assert r.level == "L1"
    assert [m.field for m in r.mismatches] == ["locvars"]
    assert r.mismatches[0].a == "()" and r.mismatches[0].b == invented

    # ... and the same input still certifies on the stripped branch, which is
    # the branch the corpus takes.
    assert certify_l3(_proto(src, strip=True), printed).level == "L3"


def test_wrapper_path_refuses_when_reconstruction_drops_a_local():
    """The mirror image, on the nested path: single-use inlining removes a
    local the original had. `local y = x + 1 return y` prints as
    `return l1_0 + 1`, same `code`, one locvar fewer. Certified `L3` before
    this task (the candidate had no locvars to disagree with), refused now."""
    from pyluadec.structure.structured import certify_proto
    root = _proto(b"local function f(x) local y = x + 1 return y end\nreturn f(2)\n",
                  strip=False)
    cert = certify_proto(root.subprotos[0], is_chunk_root=False)
    assert cert.level == "L1"
    assert [m.field for m in cert.mismatches] == ["locvars"]


# --- detection ------------------------------------------------------------
#
# `carries_debug` reads the same per-proto field view `_debug_fingerprint`
# hashes (`certify.debug_view`), so there is exactly one enumeration of "the
# fields `compare_protos` checks that `structural_hash` omits" in the tree.
# Each disjunct below is separately load-bearing: neuter any one of the three
# and the correspondingly named test fails.

def _bare(**kw) -> Proto:
    base = dict(source=b"=?", linedefined=0, lastlinedefined=0, nups=0,
                numparams=0, is_vararg=2, maxstacksize=2, code=(0x800000,),
                constants=(), lineinfo=(), locvars=(), upvalues=(), subprotos=())
    base.update(kw)
    return Proto(**base)


def test_corpus_shaped_proto_reads_as_stripped():
    assert carries_debug(_bare()) is False


def test_source_placeholder_alone_is_not_debug():
    """`source` is deliberately NOT a disjunct. Measured 2026-08-12: all 1944
    corpus protos carry `source = b"=?"` while `lineinfo`/`locvars`/`upvalues`
    are empty in every one of them. Counting a non-`None` `source` as debug
    info would flip all 229 files to unstripped candidates and move the
    ledger."""
    assert carries_debug(_bare(source=b"=?")) is False
    assert carries_debug(_bare(source=b"@x.lua")) is False


def test_lineinfo_disjunct():
    assert carries_debug(_bare(lineinfo=(1,))) is True


def test_locvars_disjunct():
    """Non-empty `locvars` with empty `lineinfo` is not something `luac`
    emits, but the predicate must not depend on that: `compare_protos` will
    compare these ranges, so the candidate has to be able to produce them."""
    assert carries_debug(_bare(locvars=(LocVar(b"a", 0, 1),))) is True


def test_upvalue_names_disjunct():
    assert carries_debug(_bare(nups=1, upvalues=(b"u",))) is True


def test_detection_is_over_the_subtree():
    """`compare_protos` recurses, so debug info anywhere under the proto has to
    be reproducible by the candidate. The corpus's own shape -- a main chunk
    whose statements are all `Name = function() ... end` -- is exactly the case
    where the root looks clean and the children do not."""
    deep = _bare(subprotos=(_bare(subprotos=(_bare(locvars=(LocVar(b"a", 0, 1),)),)),))
    assert carries_debug(deep) is True


def test_real_dumps_are_classified_both_ways():
    src = b"local a = 1\nprint(a)\n"
    assert carries_debug(_proto(src, strip=True)) is False
    assert carries_debug(_proto(src, strip=False)) is True


def test_every_corpus_proto_reads_as_stripped(corpus_dir):
    """The acceptance argument for "the ledger must not move", checked directly
    rather than inferred from the ledger's byte-identity: if every corpus proto
    takes the `strip=True` branch, the corpus path is unchanged code."""
    from pyluadec.ingest import load_file
    files = sorted(corpus_dir.glob("*.lua"))
    assert len(files) == 229
    for f in files:
        assert carries_debug(load_file(f)) is False, f.name

"""M5 task 4: the structure-refusal long tail, adjudicated by the L3 gate.

Same discipline as `tests/test_sir_loops_longtail.py`: every fixture is
oracle-compiled with the real `luac_sz4` and asserts BOTH halves --

  * `all_claimed(build_sir(fn)) == set(fn.instrs)` (the pc-claim audit), and
  * `certify_proto(..., is_chunk_root=True).level == "L3"`, i.e. the printed
    source recompiles to a proto equal to the original field-by-field under
    the versioned normalization ladder.

Nothing here relaxes the gate. Shapes that still refuse are recorded as known
gaps with their measured cause, never asserted away.

All fixture sources are pure ASCII by construction, so assertions that inspect
printed text may decode; bytecode-derived strings elsewhere stay `bytes`.
"""
import pytest

from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.sir import build as build_mod
from pyluadec.sir.build import StructureError, build_sir
from pyluadec.sir.regions import If, While, all_claimed
from pyluadec.structure.structured import certify_proto


def _sir(src: bytes):
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)   # pc-claim audit, every fixture
    return fn, r


def _certifies(src: bytes) -> None:
    """Both halves at once: the audit above, and the L3 gate on the chunk."""
    proto = load_bytes(compile_source(src, strip=True))
    fn = lift_proto(proto)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    cert = certify_proto(proto, is_chunk_root=True)
    assert cert.level == "L3", cert.reason


def _find(r, ty):
    # Only Seq.body is a tuple; every other `body` is a single Region (the
    # trap documented in tests/test_sir_build_loops.py::_find).
    out = []

    def walk(n):
        if n is None:
            return
        if isinstance(n, ty):
            out.append(n)
        b = getattr(n, "body", None)
        if isinstance(b, tuple):
            for c in b:
                walk(c)
        elif b is not None:
            walk(b)
        for a in ("then_body", "else_body"):
            walk(getattr(n, a, None))
    walk(r)
    return out


# ---------------------------------------------------- jpc threading onto an
# ---------------------------------------------------- enclosing if's else-skip
#
# Diagnosis (measured 2026-08-12). `luaK_jump` (lcode.c:59-66) is what emits an
# `if`'s else-skip as well as a loop's closing JMP -- `lparser.c:ifstat` does
# `luaK_concat(&escapelist, luaK_jump(fs))`. Anything still on `fs->jpc` at
# that moment is concatenated onto it and ends up carrying the ENCLOSING if's
# join pc rather than the end of the block it lives in. `luaK_patchtohere`
# (lcode.c:236-239) is why a nested `if`'s false-exit is on that list at all:
# it does not patch, it appends to `fs->jpc`, and only the next NON-JMP
# emission flushes it (`dischargejpc`, lcode.c:163, called from `luaK_code`,
# lcode.c:789-801).
#
# Before M5 task 4 these refused, at the pcs named:
#
#   if a then if b then f() end else h() end
#       1 GETGLOBAL 2 TEST 3 JMP->10 4 GETGLOBAL 5 TEST 6 JMP->12  <-- threaded
#       7-8 f()  9 JMP->12 (the else-skip)  10-11 h()  12 RETURN
#       -> StructureError: pc 5: if targets out of range
#   if a then if b then f() else g() end else h() end
#       -> StructureError: pc 5: else-join out of range
#   if a then while b do f() end else h() end
#       -> StructureError: pc 5: if targets out of range
#
# `snr_common.lua:main_68` (22 instrs) was the smallest corpus instance of the
# first ("pc 7: if targets out of range": EQ@7's false-exit at JMP@8 -> 22
# threaded onto the outer else-skip JMP@12 -> 22, where the outer then-body
# ends at 12); `snr_common.lua:main_74_12` (102 instrs, "pc 11: else-join out
# of range") of the second. Both certify L3 now.

THREADED_CASES = [
    # (source, the refusal it used to raise)
    (b"if a then if b then f() end else h() end",
     "pc 5: if targets out of range"),
    (b"if a then if b then f() else g() end else h() end",
     "pc 5: else-join out of range"),
    (b"if a then if b then if c then f() end end else h() end",
     "pc 5: if targets out of range"),
    (b"if a then if b then f() else if c then g() end end else h() end",
     "pc 5: else-join out of range"),
    (b"if a then if b then f() end else h() end k()",
     "pc 5: if targets out of range"),
    (b"if a then if b then f() end elseif c then g() end",
     "pc 5: if targets out of range"),
    (b"if a then while b do f() end else h() end",
     "pc 5: if targets out of range"),
    (b"if a then repeat f() until b else h() end",
     "pc 5: if targets out of range"),
    (b"if a then for i = 1, 10 do f() end else h() end",
     "pc 5: if targets out of range"),
    # The threading survives one more construct out: the whole if/else above
    # sitting in tail position of a LOOP body, where `continue_target`'s
    # rewrite and this one both apply and must not fight.
    (b"while true do if a then if b then f() end else g() end end",
     "(accepted before: continue_target already covered the outer level)"),
    (b"while true do if a then if b then f() else g() end else h() end end",
     "(accepted before)"),
    (b"for i = 1, 3 do if a then if b then f() end else h() end end",
     "pc 6: if targets out of range"),
]


@pytest.mark.parametrize("src,was", THREADED_CASES,
                         ids=[s.decode() for s, _ in THREADED_CASES])
def test_threaded_false_exit_onto_an_enclosing_else_skip_certifies(src, was):
    _certifies(src)


def test_threaded_case_claims_the_threaded_jump_rather_than_dropping_it():
    """The pc-claim audit alone cannot catch a dropped threaded jump (the
    standing lesson from M4), so name the claim explicitly: the inner if's
    false-exit JMP@6 is claimed by the INNER `If`, as part of its cond_pcs,
    and the outer else-skip JMP@9 by the outer one.
    """
    fn, r = _sir(b"if a then if b then f() end else h() end")
    outer, inner = sorted(_find(r, If), key=lambda i: i.cond.ri.pc)
    assert outer.cond.ri.pc == 2 and outer.claimed_pcs == frozenset({2, 3, 9})
    assert inner.cond.ri.pc == 5 and inner.claimed_pcs == frozenset({5, 6})
    assert inner.else_body is None                # the inner if really has no else
    assert all_claimed(inner.then_body) == frozenset({7, 8})


def test_threaded_while_exit_is_the_loops_own_false_exit():
    """`while` as the last statement of a then-block: the loop's false-exit is
    what gets threaded, so `_match_while_header` needs the same rewrite. The
    region must still be a `While` claiming its own header/cond/JMP/closing.
    """
    fn, r = _sir(b"if a then while b do f() end else h() end")
    (w,) = _find(r, While)
    assert w.claimed_pcs == frozenset({4, 5, 6, 9})
    assert all_claimed(w.body) == frozenset({7, 8})


def test_threaded_cases_run_identically_to_the_original():
    """Differential execution, not just field equality: the three shapes with
    an observable side effect in every arm print the same thing before and
    after a decompile/recompile round trip.
    """
    src = (b"local function t(a, b) "
           b"  if a then if b then print('ab') else print('a') end "
           b"  else print('none') end "
           b"end "
           b"t(true, true) t(true, false) t(false, false)")
    proto = load_bytes(compile_source(src, strip=True))
    cert = certify_proto(proto, is_chunk_root=True)
    assert cert.level == "L3", cert.reason
    assert run_bytes(src, is_source=True).stdout == b"ab\na\nnone\n"
    assert run_bytes(cert.source, is_source=True).stdout == b"ab\na\nnone\n"


def test_a_thread_target_inside_the_range_is_rejected_rather_than_silently_retargeting_a_jump():
    """The load-bearing proof for `_structure_range_impl`'s
    `thread_target >= hi` assert.

    The rewrite `_structure_if` performs is safe only because every thread
    target handed down is at or beyond the range's own `hi`: combined with the
    `then_lo <= jt <= hi` bound the recognizer already enforced, that makes the
    rewrite a no-op unless `jt > hi`, i.e. unless the old code refused. A
    target INSIDE the range breaks that argument -- a false-exit that legally
    points at a pc in the middle of the range gets rewritten to "end of range",
    and everything after the `if` is swallowed into its then-body. The
    pc-claim audit is blind to it: every pc is still claimed, just by the
    wrong region.

    Nothing reaches that state today (`_structure_if` normalizes a backward raw
    target to `None`, and every forward one is a terminating jump's target,
    hence `>= hi`). This drives it directly, through the real
    `_structure_range`, on real luac output.

    NEUTER PROOF (2026-08-12): with the assert line deleted from
    `_structure_range_impl`, this test fails `Failed: DID NOT RAISE
    AssertionError` and the region built in its place is
    `Seq(Straight{1}, If(cond@2, then_body=Straight{4,5,6,7} + Return{8}))` --
    `g()` and the function's own `RETURN` moved INSIDE the `if`, while
    `all_claimed(region) == set(fn.instrs)` still holds. Restored.
    """
    # 1 GETGLOBAL a  2 TEST  3 JMP->6  4-5 f()  6-7 g()  8 RETURN
    # The if's false-exit legally targets pc 6, in the middle of the range.
    src = b"if a then f() end g()"
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    cfg = build_mod.build_cfg(fn)
    idoms = build_mod.immediate_dominators(cfg)
    pc2blk = build_mod._pc_block_map(cfg)
    lo, hi = min(fn.instrs), max(fn.instrs) + 1
    assert fn.instrs[3].successors == (6,), fn.instrs[3].successors
    assert lo < 6 < hi, (lo, hi)               # sanity: the target really is inside
    with pytest.raises(AssertionError):
        build_mod._structure_range(fn, cfg, idoms, pc2blk, lo, hi,
                                   thread_target=6)


def test_the_memo_key_separates_ranges_that_differ_only_in_thread_target():
    """`_structure_range` caches on `(lo, hi, break_target, continue_target,
    thread_target)`. The last component is not decoration: the same interval
    structures differently (here, refuses vs succeeds) depending on it, so a
    key without it would let whichever call ran first answer for both.
    """
    fn = lift_proto(load_bytes(compile_source(
        b"if a then if b then f() end else h() end", strip=True)))
    cfg = build_mod.build_cfg(fn)
    idoms = build_mod.immediate_dominators(cfg)
    pc2blk = build_mod._pc_block_map(cfg)
    sites = build_mod._jmp_sites(fn)
    memo: dict = {}
    # The then-body of the outer if, [4, 9): refuses with no thread target,
    # succeeds with the else-skip's raw target (12).
    with pytest.raises(StructureError):
        build_mod._structure_range(fn, cfg, idoms, pc2blk, 4, 9,
                                   sites=sites, memo=memo)
    r = build_mod._structure_range(fn, cfg, idoms, pc2blk, 4, 9,
                                   thread_target=12, sites=sites, memo=memo)
    assert all_claimed(r) == {4, 5, 6, 7, 8}
    # The refusal and the success are two SEPARATE entries -- same interval,
    # different thread target -- and the refusal is still recorded as one.
    assert memo[(4, 9, None, None, None)] == "pc 5: if targets out of range"
    assert memo[(4, 9, None, None, 12)] is r


# ------------------------------------------ dead code luac emits unconditionally
#
# Diagnosis (measured 2026-08-12). Two things `lparser.c` emits without knowing
# whether anything can reach them:
#
#   * the else-skip, `ifstat`'s `luaK_concat(&escapelist, luaK_jump(fs))`,
#     which is dead whenever the then-block ends in `break` or `return`; and
#   * the RETURN after a TAILCALL, `retstat`'s `luaK_ret` (lparser.c:1100-1116).
#
# Both land INSIDE the enclosing branch or loop body, where
# `_verify_single_entry` refused them as `branch body block at pc N is
# unreachable` -- 10 unique corpus protos, smallest `snr_common.lua:main_59`
# (17 instrs) and `snr_common.lua:main_29_0` (18). `_is_dead_else_skip` now
# admits exactly those two shapes and nothing else.
#
# `else break end` needs a second thing on top: `breakstat`'s own `luaK_jump`
# absorbs the pending false-exit (lparser.c:1054-1067), so the `if`'s
# false-exit points at the loop exit and the correct join has to be recovered
# from the layout -- `_match_else_break`.

DEAD_CODE_CASES = [
    # main_59's shape: the false-exit threaded onto the else block's `break`.
    b"local n = 0 for i = 1, 10 do if t[i] ~= -1 then n = n + 1 else break end end return n",
    b"for i = 1, 10 do if t[i] then return i else break end end",
    b"while c do if a then f() else break end end",
    b"while c do if a then f() else break end g() end",
    b"while true do if a then f() else break end end",
    b"for i = 1, 3 do if a then f() else break end end",
    # nested: BOTH breaks match `_match_else_break`'s pattern, and only the
    # outer one is the outer if's else (the last-first ordering).
    b"while true do if a then if b then x() else break end else break end end",
    # main_29_0's shape: TAILCALL leaves a dead RETURN in each branch body.
    b'local function f(a, b) if a == true then return g(b .. "_on") '
    b'else return g(b .. "_off") end end',
    # the dead else-skip with a `return` rather than a `break` in the then-arm
    b"local function f(a) if a then return 1 else h() end return 2 end",
]


@pytest.mark.parametrize("src", DEAD_CODE_CASES,
                         ids=[s.decode()[:48] for s in DEAD_CODE_CASES])
def test_dead_code_luac_emits_unconditionally_certifies(src):
    _certifies(src)


def test_else_break_claims_the_break_as_the_else_body():
    """Name the claim rather than trusting the pc-claim audit: the threaded
    false-exit JMP and the dead else-skip belong to the `If`, and the break's
    own JMP is the else body.

    1-4 LOADK (n = 0 and the for control triple)  5 FORPREP->13
    6-7 t[i]  8 EQ  9 JMP->14  (the threaded false-exit: 14 is the loop exit)
    10 ADD  11 JMP->13 (the else-skip, over a one-instruction else)
    12 JMP->14 (the break; unreachable)  13 FORLOOP  14 RETURN
    """
    src = (b"local n = 0 for i = 1, 10 do if t[i] ~= -1 then n = n + 1 "
           b"else break end end return n")
    fn, r = _sir(src)
    (i,) = _find(r, If)
    from pyluadec.sir.regions import Break
    assert isinstance(i.else_body, Break)
    assert i.else_body.claimed_pcs == frozenset({12})
    assert i.claimed_pcs == frozenset({8, 9, 11})
    assert i.join_pc == 13
    assert all_claimed(i.then_body) == frozenset({10})


def test_dead_code_of_any_other_shape_is_still_refused():
    """`_is_dead_else_skip` is deliberately narrow, and these four committed
    floor tests are its neuter proof -- not a hypothetical one.

    NEUTER PROOF (2026-08-12, on the finished tree): replacing the whole
    check with an unconditional `if True:` buys exactly the same corpus figure
    -- 75 unique protos below `L3`, the same as the narrow rule -- and makes
    all four of these fail with `DID NOT RAISE StructureError`. So the narrow
    rule costs nothing and these four are what pins it. Their dead code is a
    MOVE chain after a RETURN, which is neither a lone JMP nor a RETURN behind
    a TAILCALL, and which could not be printed as live Lua anyway (`return`
    must end its block).

    This test only asserts they exist and are about this; they carry their own
    assertions.
    """
    import tests.test_sir_build_acyclic as acyclic
    import tests.test_sir_build_loops as loops
    for mod, name in ((acyclic, "test_dead_code_inside_a_claimed_then_range_raises"),
                      (acyclic, "test_dead_code_inside_a_claimed_else_range_raises"),
                      (loops, "test_dead_code_inside_a_numeric_for_body_raises"),
                      (loops, "test_dead_code_inside_a_generic_for_body_raises")):
        assert hasattr(mod, name), f"{mod.__name__}::{name} went missing"
        getattr(mod, name)()


# ------------------------------------------------------------- known gaps
#
# Recorded, not asserted away. Each one is the SHAPE that still refuses, with
# the message measured on 2026-08-12 after the threading fix above.

KNOWN_REFUSALS = [
    # A `break` in tail position of a loop body is patched by `leaveblock`'s
    # `luaK_patchtohere(fs, bl->breaklist)`, i.e. onto `fs->jpc` -- so when the
    # loop is itself the last statement of a then-block the break gets threaded
    # onto the enclosing else-skip too. `_exits_only_to` then sees a jump out
    # of the loop that is neither `S+1` nor a RETURN and the loop is not
    # recognized. Not addressed here: the fix belongs with `break_target`, not
    # with `_structure_if`, and no corpus proto is refused for this reason.
    (b"if a then while true do if b then break end f() end else h() end",
     "unrecognized transfer JMP"),
    # Compound `if` conditions. `sir.regions.If` carries ONE compare
    # instruction, so `a and b` is read as nested `if`s -- which is the same
    # bytecode when there is no else branch, and a DIFFERENT one when there is
    # (the inner false-exit goes to the elseif's test, not to the outer
    # else-skip). `or` has no nested-if reading at all. This is the residual
    # `if targets out of range` cluster; see the M5 task-4 report.
    (b"if a and b then f() else g() end", "if targets out of range"),
    (b"if a or b then f() end", "if targets out of range"),
]


@pytest.mark.parametrize("src,msg", KNOWN_REFUSALS,
                         ids=[s.decode() for s, _ in KNOWN_REFUSALS])
def test_known_refusals_still_refuse_loudly(src, msg):
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    with pytest.raises(StructureError) as e:
        build_sir(fn)
    assert msg in str(e.value), str(e.value)

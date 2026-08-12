"""Spec §7/§8 standing semantic-regression gate, ported from the
predecessor's `pyluadec/test_semantic_regressions.py` (M4 task 5).

Mechanism-equivalent rewrite, assertions' semantics unchanged (spec §8):
unittest -> pytest; `DecompilerPipeline.decompile_source` + a subprocess
`lua -` call -> `oracle.compile_source` + `structure.structured.
emit_certified_chunk` + `oracle.run_bytes`. Every expected stdout below was
re-verified against this repo's own `lua_sz4` oracle in this session
(2026-08-11) by compiling and running each source directly -- not copied
blind from the predecessor's docstrings or from the M4 task-5 brief.

Each case asserts BOTH the stdout match AND the shipped artifact's
certification level (`out.certs["main"].level`). The level assertion is the
point, not a decoration: `structure.fallback`'s state machine is semantically
exact by construction (M2's floor), so a silent regression from structured
output back to fallback would still pass the stdout diff. Only checking the
level catches it.

Two of the five named cases ship fallback (`L1`), not structured (`L3`).
That is a genuine, measured finding about the current structurer -- not a
test defect and not something papered over by weakening the assertion. Each
such case's test function documents which recognizer gap it hits and cites
the corresponding cluster in `docs/runbooks/structured-pipeline.md`'s
"Current capability boundary" section.

## Explicit non-goal (recorded here per the M4 task-5 brief)

The predecessor's two key-sequence checkpoints from
`DEBUG_KEY_SEQUENCE_HARNESS.md` -- `SystemOption.OptionMain`'s double-clamp
mutual exclusion, and `SystemConfig.ConfigMain`'s CIRCLE-branch gate/wait
preservation -- need the L2 stub harness (metatable-proxy global stubbing,
call tracing, a driven button/key sequence). That harness does not exist in
this repo yet; it is spec **M5**. Nothing here approximates those two
checkpoints with partial stubs.
"""
from __future__ import annotations

from pyluadec import oracle
from pyluadec.ingest import load_bytes
from pyluadec.structure.structured import emit_certified_chunk


def _run(src: str, expected_stdout: str, expected_rc: int = 0):
    bc = oracle.compile_source(src.encode(), strip=True)
    out = emit_certified_chunk(load_bytes(bc))
    r = oracle.run_bytes(out.source, is_source=True)
    assert (r.returncode, r.stdout.decode()) == (expected_rc, expected_stdout)
    return out


def test_closure_capture_const_does_not_alias_param():
    src = """
        local function mk(a)
          return function(v)
            return a + v
          end
        end
        local f = mk(5)
        local s = 0
        for i = 1, 40 do
          s = s + f(i)
        end
        print(s)
    """
    out = _run(src, "1020\n")
    assert out.certs["main"].level == "L3"


def test_closure_capture_rw_upvalue_preserved():
    src = """
        local function mk(a)
          local x = a
          return function(v)
            x = x + v
            return x
          end
        end
        local f = mk(3)
        local s = 0
        for i = 1, 10 do
          s = s + f(i)
        end
        print(s)
    """
    out = _run(src, "250\n")
    assert out.certs["main"].level == "L3"


def test_while_true_break_guard_recovers_loop():
    src = """
        local i = 1
        local s = 0
        while true do
          if i > 80 then
            break
          end
          if i % 2 == 0 then
            s = s + i
          else
            s = s - (i % 5)
          end
          i = i + 1
        end
        print(s)
    """
    out = _run(src, "1560\n")
    assert out.certs["main"].level == "L3"


def test_counter_closure_and_dispatch_mix():
    """KNOWN GAP: ships fallback (`L1`), not `L3` -- measured 2026-08-11.

    `main`'s own body DOES structure and print (`build_sir` accepts it,
    `print_chunk` succeeds), but the recompiled candidate genuinely differs
    in shape from the original: `maxstacksize` 18 vs 20, 13 vs 15 constants,
    and the `code` array differs from early in the function (verified via
    `certify_proto(root, is_chunk_root=True).mismatches`). This is the
    "prints but does not certify" residual documented in
    `docs/runbooks/structured-pipeline.md`'s "Current capability boundary"
    (35 unique protos, post-task-13) -- specifically Task 6's "re-census"
    material (constant-table-ordering / extra-instruction clusters B/D), NOT
    the per-register-number classification bug task 13 already fixed (that
    cluster is down to 4). Every OTHER proto in this chunk -- `make_counter`
    and its returned closure, and all four `op_N` helpers -- certifies `L3`
    independently; only the call-heavy dispatcher body of `main` itself does
    not, which is exactly the point of per-proto (not per-chunk)
    certification: one proto's gap does not poison its siblings' levels,
    only the shipped chunk artifact (which is all-or-nothing on the root).
    """
    src = """
        local function make_counter(base, twist)
          local total = base
          return function(x)
            total = (total + x * twist + (x % 13)) % 1000003
            if total % 2 == 0 then
              total = total + twist
            else
              total = total - (twist % 7)
            end
            if total < 0 then
              total = total + 1000003
            end
            return total
          end
        end

        local function op1(x, y) return (x * 7 + y * 11 + 17) % 1000003 end
        local function op2(x, y) return (x * 13 + y * 5 + 31) % 1000003 end
        local function op3(x, y) return (x * 3 + y * 19 + 47) % 1000003 end
        local function op4(x, y) return (x * 23 + y * 2 + 71) % 1000003 end

        local counters = {}
        for i = 1, 6 do
          counters[i] = make_counter((i * 17) % 97, (i * 9) % 23 + 1)
        end

        local sum = 0
        for i = 1, 80 do
          local c = counters[(i % 6) + 1]
          local t = c(i * 3)
          local idx = ((i + t) % 4) + 1
          local merged = 0
          if idx == 1 then
            merged = op1(t, i)
          elseif idx == 2 then
            merged = op2(t, i)
          elseif idx == 3 then
            merged = op3(t, i)
          else
            merged = op4(t, i)
          end
          if merged % 3 == 0 then
            sum = sum + merged
          elseif merged % 3 == 1 then
            sum = sum - (merged % 97)
          else
            sum = sum + (merged % 53)
          end
        end
        print(sum)
    """
    out = _run(src, "1271004\n")
    assert out.certs["main"].level == "L1"       # measured; see docstring
    assert out.certs["main_0"].level == "L3"     # make_counter
    assert out.certs["main_0_0"].level == "L3"   # make_counter's returned closure
    assert out.certs["main_1"].level == "L3"     # op1
    assert out.certs["main_2"].level == "L3"     # op2
    assert out.certs["main_3"].level == "L3"     # op3
    assert out.certs["main_4"].level == "L3"     # op4
    assert b"__pld_pc" in out.source             # artifact: fallback chunk (root not L3)


def test_if_and_elseif_conjunctions_preserved():
    """KNOWN GAP: ships fallback (`L1`), not `L3`.

    `f`'s body -- `if p0 < p1 and v4 == -1 then ... elseif 3 < p0 and v4 == 1
    then ... end` -- is refused by `build_sir` with
    `StructureError: pc 4: if targets out of range` at the second condition's
    `AND`, still, after M5 task 4.

    **The M4-era diagnosis recorded here was wrong and is corrected in
    place** (re-measured 2026-08-12 by dumping `f`'s lifted stream). It read:
    "the inner if's AND-chain false-exit is threaded (`luaK_jump`'s `jpc`
    pending-list concatenation) onto the ENCLOSING elseif chain's else-skip",
    and predicted that M5 task 4's threading work would flip this case. It
    did not, because there is no threading here at all. `f` compiles to

        2 LT   ->(3,4)    3 JMP -> 8      <- first conjunct's false-exit
        4 EQ   ->(5,6)    5 JMP -> 8      <- second conjunct's false-exit
        6 LOADK x=1       7 JMP -> 13     <- the else-skip
        8 LT   ...        (the elseif)

    Both conjuncts' false-exits are patched DIRECTLY to pc 8, the elseif's
    own test -- `luaK_patchtohere(flist)` at the head of the else branch, not
    a pending-list concatenation onto JMP@7. JMP@5's target (8) is past the
    end of the then-body (which ends at 7, the else-skip), and no rewrite can
    make it mean "end of the then-body", because it does not: falling through
    to 7 would SKIP the elseif entirely.

    The real cause is that `sir.regions.If` carries exactly ONE compare
    instruction. `a and b` is therefore read as nested `if`s, which is the
    same bytecode when the `if` has no else branch (why `if a and b then X
    end` certifies today) and a DIFFERENT one when it does. `or` has no
    nested-`if` reading at all. Closing this needs a condition TREE in the
    region/expression/printer layers; see the M5 task-4 report's residual and
    `tests/test_sir_longtail2.py::KNOWN_REFUSALS`, whose two-line synthetic
    exemplars (`if a and b then f() else g() end`, `if a or b then f() end`)
    are this same shape.

    `main` (the wrapper chunk) falls back too, since `print_chunk` inlines
    `f`'s body at its `CLOSURE` site, so one unstructurable descendant takes
    the whole ancestor chain with it.
    """
    src = """
        local function f(p0, p1, v4)
          local x = 0
          if p0 < p1 and v4 == -1 then
            x = 1
          elseif 3 < p0 and v4 == 1 then
            x = 2
          end
          return x
        end
        print(f(2, 5, -1), f(2, 5, 0), f(4, 5, 1), f(4, 5, 0))
    """
    out = _run(src, "1\t0\t2\t0\n")
    assert out.certs["main"].level == "L1"       # measured; see docstring
    assert out.certs["main_0"].level == "L1"     # f() itself: build_sir refuses
    assert b"__pld_pc" in out.source             # artifact: fallback chunk

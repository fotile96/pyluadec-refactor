"""Effects-table / emitter-template reconciliation (M3 backlog item 2).

`lift/effects.py` and the emitters are two independent hand-transcriptions of
`vendor/lua-5.1/src/lvm.c`. Nothing else in this project mechanically reconciles
them, so they can drift silently: `effects.py` feeds the register
classification, the inlining decisions and the SIR/CFG layers, while
`structure/fallback.py` and `emit/lua.py` decide which registers actually appear
in the emitted text. A register the emitter reads but the effects table does not
list is exactly the shape of bug that produces plausible-looking, wrong Lua.

## What this gate asserts

For every instruction, the register indices an emitter template must read or
write are a **subset** of `effects.reads | effects.writes`.

`_registers_touched` below is the transcription of the emitter side. It is
derived from `structure/fallback.py`'s per-opcode templates (`_emit_simple`,
`_emit_call`, `_emit_terminator`) -- the fallback emitter is the one place in
the tree where every opcode has an explicit, hand-written register list, so it
is the honest reference for "which registers does emission touch".

**This gate does not cover the structured path** -- `express/reconstruct.py`
-> `emit/lua.py` is a **third** independent hand-transcription of `lvm.c`'s
per-opcode semantics, sitting right next to the two this gate reconciles.
`express/names.py`'s register *classification* (`classify_registers`) does
consume `effects`, but the reconstructor's per-opcode operand decoding does
not: as re-measured at M4 task 9, `reconstruct.py` reads `ri.a`/`ri.b`/`ri.c`
directly 23 times on 16 lines and reaches `.effects` 3 times (`:406`, `:529`,
`:999`), none of them an operand source; `emit/lua.py` reaches `ri.<field>`
11 times and `effects` 0 times.

**That blind spot is now covered by
`tests/test_effects_reconstructor_consistency.py`** (M4 task 9), which
instruments the reconstructor's real accessors and `name_for` rather than
transcribing anything, and reports 0 violations over the corpus and over the
grid below. This module is still the only thing reconciling
`structure/fallback.py`, and the `_registers_touched` caveat at the end of
this docstring still applies to it.

(Historical note, kept because this project treats retracted numbers as
load-bearing: the paragraph this replaces said "9 call sites (`:434, :444,
:455, :456, :469, :521, :592, :611, :648`)", "mentions `effects` exactly
once (`:614`)" and "`ri.` 16 times" in the printer. All three were measured
false at M4 task 9 -- the first two because M4 added `condition_expr` and the
whole `CondValue` reconstructor after they were counted, the third because it
over-counted and simultaneously missed the `ps.b` decode at `emit/lua.py:287`,
which is a register index that never goes through an `ri`.)

## What it does NOT assert

- **Not equality, only containment.** The effects table is allowed to be a
  conservative over-approximation (it is, deliberately, in at least two places:
  `CLOSURE`'s reads are widened by `lift.py` with the captured registers from
  the following MOVE pseudo-instructions, and `FORLOOP`'s `may_error` is a
  documented over-approximation). A row that lists registers no emitter touches
  is safe; a row that omits one an emitter touches is not.
- **The open part of an open region.** `reads_open`/`writes_open` describe
  `R[base..top)`, which is `__pld_top`-relative at run time and has no static
  register set to compare against, so nothing here reconciles it.

  Rows carrying one are nevertheless **checked, not skipped**, for their
  static part (M4 task 8). They used to be skipped outright, on the reading
  that an open region makes the comparison ill-posed. It does not: every
  `_registers_touched` branch that could name an open region's registers is
  guarded by `if b` / `if c` and degenerates to the empty set at exactly the
  operand values that open the region (`CALL B==0` -> no argument range,
  `CALL C==0` -> no result range, `RETURN`/`VARARG`/`SETLIST B==0` -> empty),
  so `touched` never contains a register only the open region reaches and the
  subset assertion stays both well-posed and non-vacuous for these rows. What
  the skip actually discarded was the *static* half of the check --
  `CALL A B==0`'s callee slot, `TAILCALL`'s explicit argument range -- for
  6981 of 214192 corpus instructions (6949 `CALL`, 26 `VARARG`, 3 `RETURN`,
  3 `TAILCALL`). Measured with the skip removed: 0 violations on either arm.

  The immediate cause was M4 task 8 giving `TAILCALL` its `writes_open`
  (`lvm.c:630-632`): with a blanket skip, every `TAILCALL` in the corpus and
  in the grid silently dropped out of this gate, which is precisely the
  "invisible loss of coverage" `_NO_REGISTER_OPCODES` below exists to
  prevent.
- **The corpus does not reach every opcode.** Of the 38 opcodes, 33 occur in
  the corpus at all, and the corpus arm now checks all 33 (before M4 task 8's
  skip removal it checked 32 -- `VARARG`'s 26 occurrences are all `B == 0`,
  so it was skipped away entirely). `SELF`, `POW`, `UNM`, `NOT` and `CLOSE`
  never occur. That is why the synthetic arm below exists: it runs the same
  invariant over an exhaustive operand grid and reaches 38/38.
- **`_registers_touched` is a frozen hand-copy of `structure/fallback.py`'s
  templates, not a live reference to them.** If `fallback.py` changes which
  registers a template touches and this copy is not updated to match, the
  gate keeps checking the old model against `effects.py` and stays green --
  it would not notice the fallback emitter drifting out from under it. This
  is inherent to transcribing rather than importing; do not over-trust a
  green run here as proof the *current* `fallback.py` agrees with `effects.py`
  without also checking this copy is still current.
"""
from __future__ import annotations

import time

import pytest

from pyluadec.lift.effects import EffectMode, analyze
from pyluadec.lift.opcodes import BITRK, Op, RawInstr, isk

from tests.synth import mk_instr


def _registers_touched(ri: RawInstr) -> set[int]:
    """Registers an emitter template must read or write for this instruction.

    Transcribed from `structure/fallback.py`. Two notes where this deviates
    from the shape the Task 10 brief proposed, both corrected against
    `vendor/lua-5.1/src/lvm.c`:

    - `TAILCALL` is NOT grouped with `CALL`. The brief applied `CALL`'s
      "C-1 result registers at R[a..a+c-2]" term to both, but `OP_TAILCALL`
      has no result registers: `lvm.c:611` asserts
      `GETARG_C(i) - 1 == LUA_MULTRET`, i.e. C is always 0, and `lparser.c:1251`
      only ever rewrites a `VCALL` into `OP_TAILCALL` after `luaK_setmultret`,
      which is what forces C to 0. `fallback.py::_emit_terminator`'s TAILCALL
      arm accordingly emits a bare `return <call>` and never mentions C.
      Grouping them makes the synthetic grid below fail on **64** of its 196
      `TAILCALL` rows (re-measured M4 task 8 by temporarily restoring the
      brief's grouping over the committed grid). Not every `TAILCALL` with
      `C != 0` fails: 48 of the 64 are the `B != 0` rows where `C > B + 1`
      -- the 12 `(b, c)` pairs in the operand grid satisfying that
      inequality, times the grid's 4 `a`-values -- and the other 16 are
      `B == 0` rows with `C >= 3`, where the fixed argument range is empty
      so only `{a}` is covered. (The 48/16 split is new: before M4 task 8
      removed the blanket open-region skip, the `B == 0` rows never reached
      the comparison at all and the measured total was 48.) The helper was
      the wrong side and was fixed rather than the assertion relaxed.
    - `CLOSURE` lists only `{a}`. `fallback.py` also emits
      `__pld_R[ps.b]` for each captured register, but those are supplied to the
      effects table by `lift.py` (`fx.reads | moved`), so the subset holds with
      room to spare; listing them here would duplicate the same derivation on
      both sides of the comparison and stop the check from being independent.
    """
    op, a, b, c = ri.op, ri.a, ri.b, ri.c
    t: set[int] = set()
    if op in (Op.MOVE, Op.UNM, Op.NOT, Op.LEN, Op.TESTSET):
        t = {a, b}
    elif op in (Op.LOADK, Op.LOADBOOL, Op.NEWTABLE, Op.GETGLOBAL, Op.GETUPVAL,
                Op.CLOSURE):
        t = {a}
    elif op in (Op.SETGLOBAL, Op.SETUPVAL, Op.TEST):
        t = {a}
    elif op is Op.LOADNIL:
        t = set(range(a, b + 1))
    elif op is Op.GETTABLE:
        t = {a, b} | ({c} if not isk(c) else set())
    elif op is Op.SELF:
        t = {a, a + 1, b} | ({c} if not isk(c) else set())
    elif op is Op.SETTABLE:
        t = {a} | ({b} if not isk(b) else set()) | ({c} if not isk(c) else set())
    elif op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
        t = {a} | ({b} if not isk(b) else set()) | ({c} if not isk(c) else set())
    elif op in (Op.EQ, Op.LT, Op.LE):
        t = ({b} if not isk(b) else set()) | ({c} if not isk(c) else set())
    elif op is Op.CONCAT:
        t = {a} | set(range(b, c + 1))
    elif op is Op.FORPREP:
        t = {a, a + 1, a + 2}
    elif op is Op.FORLOOP:
        t = {a, a + 1, a + 2, a + 3}
    elif op is Op.TFORLOOP:
        t = {a, a + 1, a + 2} | set(range(a + 3, a + 3 + c))
    elif op is Op.CALL:
        t = {a} | (set(range(a + 1, a + b)) if b else set()) \
              | (set(range(a, a + c - 1)) if c else set())
    elif op is Op.TAILCALL:
        t = {a} | (set(range(a + 1, a + b)) if b else set())
    elif op is Op.RETURN:
        t = set(range(a, a + b - 1)) if b else set()
    elif op is Op.VARARG:
        t = set(range(a, a + b - 1)) if b else set()
    elif op is Op.SETLIST:
        t = {a} | (set(range(a + 1, a + b + 1)) if b else set())
    elif op in (Op.JMP, Op.CLOSE):
        t = set()
    return t


# Opcodes for which `_registers_touched` is always empty, so the subset
# assertion is vacuously true for them. Both are correct: `OP_JMP` only calls
# `dojump(L, pc, GETARG_sBx(i))` (lvm.c:541-544) and `OP_CLOSE` only calls
# `luaF_close(L, ra)` (lvm.c:719-722), which migrates open upvalues off the
# stack without reading or writing any register's value. Named here so that an
# opcode silently JOINING this set -- a helper branch that stops listing
# registers -- is a test failure rather than an invisible loss of coverage.
_NO_REGISTER_OPCODES = frozenset({Op.JMP, Op.CLOSE})

# Opcodes the 229-file corpus actually exercises through this gate (measured;
# see the module docstring). Asserted as a lower bound, not equality, so a
# larger corpus is not a failure -- but a shrinking one is.
_CORPUS_CHECKED_OPCODES = frozenset({
    Op.MOVE, Op.LOADK, Op.LOADBOOL, Op.LOADNIL, Op.GETUPVAL, Op.GETGLOBAL,
    Op.GETTABLE, Op.SETGLOBAL, Op.SETUPVAL, Op.SETTABLE, Op.NEWTABLE,
    Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.LEN, Op.CONCAT, Op.JMP,
    Op.EQ, Op.LT, Op.LE, Op.TEST, Op.TESTSET, Op.CALL, Op.TAILCALL,
    Op.RETURN, Op.FORLOOP, Op.FORPREP, Op.TFORLOOP, Op.SETLIST, Op.CLOSURE,
    Op.VARARG,
})


@pytest.fixture(scope="module")
def corpus_scan(corpus_dir):
    """One pass over the whole corpus, shared by every corpus-gated test here.

    Walking 229 files and lifting all 1944 protos costs ~0.9s; doing it once
    per assertion instead of once per test keeps this gate off the suite's
    critical path (standing directive: a slow suite blocks development).
    """
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto

    t0 = time.perf_counter()
    violations: list[str] = []
    checked = 0
    open_rows = 0
    total = 0
    ops_checked: set[Op] = set()
    protos = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop()
            stack.extend(p.subprotos)
            protos += 1
            fn = lift_proto(p)
            for li in fn.instrs.values():
                total += 1
                fx = li.effects
                if fx.reads_open or fx.writes_open:
                    # Counted, not skipped -- see the module docstring's
                    # "open part of an open region" bullet (M4 task 8).
                    open_rows += 1
                touched = _registers_touched(li.ri)
                covered = fx.reads | fx.writes
                if not touched <= covered:
                    violations.append(
                        f"{f.name} pc {li.ri.pc} {li.ri.op.name}: "
                        f"touches {sorted(touched - covered)} "
                        f"outside effects {sorted(covered)}")
                ops_checked.add(li.ri.op)
                checked += 1
    return {
        "violations": violations, "checked": checked, "open_rows": open_rows,
        "total": total, "ops_checked": ops_checked, "protos": protos,
        "seconds": time.perf_counter() - t0,
    }


def test_effects_cover_registers_touched_by_reconstruction(corpus_scan):
    """effects.reads|writes must be a superset of the registers reconstruction touches.

    Guards against drift between lift/effects.py and the emitters -- two
    independent hand-transcriptions of lvm.c. The unbounded `R[base..top)`
    part of an open region is outside what this can reconcile, but the rows
    carrying one are still checked for their static part (M4 task 8; see the
    module docstring).
    """
    assert not corpus_scan["violations"], (
        f"{len(corpus_scan['violations'])} effects/emitter disagreements:\n"
        + "\n".join(corpus_scan["violations"][:20]))
    # Measured (M4 task 8): all 214192 corpus instructions are checked, 6981
    # of them carrying an open region. The equality is the load-bearing one --
    # it is what stops a future blanket skip from silently shrinking this gate
    # again. The two floors are deliberately well below the measured values so
    # they fail on a collapse (an exception swallowed, a corpus that stopped
    # loading) rather than on ordinary drift.
    assert corpus_scan["checked"] == corpus_scan["total"], (
        corpus_scan["checked"], corpus_scan["total"])
    assert corpus_scan["checked"] > 100_000, corpus_scan["checked"]
    assert corpus_scan["open_rows"] > 5_000, corpus_scan["open_rows"]
    assert corpus_scan["protos"] == 1944, corpus_scan["protos"]


def test_corpus_arm_still_reaches_the_opcodes_it_claims_to(corpus_scan):
    """The corpus arm's reach is 33/38 opcodes -- pin it so it cannot shrink.

    `checked > 100_000` alone would stay green if a whole opcode family
    stopped being reached (e.g. a lift-layer change that started marking
    everything as an open region): 81227 of the checked rows are `LOADK`
    alone, so the count is dominated by one opcode and is a poor proxy for
    coverage.
    """
    missing = _CORPUS_CHECKED_OPCODES - corpus_scan["ops_checked"]
    assert not missing, sorted(op.name for op in missing)


def _grid_instrs():
    """Every opcode crossed with an operand grid: register indices, RK-encoded
    constants (>= BITRK), and the 9-bit maximum. Reaches all 38 opcodes,
    including the five the corpus never contains (SELF, POW, UNM, NOT, CLOSE)
    and VARARG with a fixed result count.
    """
    values = (0, 1, 2, 3, BITRK, BITRK + 1, 511)
    for op in Op:
        for a in (0, 1, 4, 255):
            for b in values:
                for c in values:
                    yield mk_instr(op, a, b, c, pc=1)


def test_effects_cover_registers_touched_over_a_synthetic_operand_grid():
    """The same invariant over hand-built instructions, reaching 38/38 opcodes.

    luac never emits SELF/POW/UNM/NOT/CLOSE for this corpus and never emits a
    VARARG with `B != 0`, so the corpus arm cannot speak for those rows at all.
    A synthetic grid can: `analyze()` is a pure function of the decoded operand
    fields, so an instruction word built by `tests/synth.mk_instr` exercises
    exactly the same table row a real one would.

    Operand combinations luac would never produce (a `CONCAT` with `B > C`, a
    `LOADNIL` with `B < A`) are deliberately left in: the invariant must hold
    for them too, and both sides degenerate to the same empty range.

    Rows carrying an open region are checked here too, for their static part
    (M4 task 8). Skipping them used to cost this arm every `TAILCALL` row the
    moment `TAILCALL` gained its unconditional `writes_open`, i.e. 196 of the
    grid's rows and one whole opcode of the `ops_checked == set(Op)`
    assertion below.
    """
    violations = []
    ops_checked: set[Op] = set()
    rows = 0
    for ri in _grid_instrs():
        fx = analyze(ri, EffectMode.STRICT)
        touched = _registers_touched(ri)
        covered = fx.reads | fx.writes
        if not touched <= covered:
            violations.append(f"{ri.op.name} A={ri.a} B={ri.b} C={ri.c}: "
                              f"touches {sorted(touched - covered)[:8]} "
                              f"outside effects {sorted(covered)[:8]}")
        ops_checked.add(ri.op)
        rows += 1
    assert not violations, (f"{len(violations)} disagreements:\n"
                            + "\n".join(violations[:20]))
    assert ops_checked == set(Op), sorted(op.name for op in set(Op) - ops_checked)
    assert rows > 5000, rows


def test_the_subset_check_is_not_vacuous_for_any_opcode():
    """Every opcode except JMP/CLOSE has at least one grid row with a non-empty
    `touched` set.

    Without this, an opcode whose `_registers_touched` branch was deleted (or
    fell through to the implicit `set()`) would still pass the subset assertion
    forever -- the empty set is a subset of everything. This project has
    already shipped tests that could not fail (see `docs/runbooks/m3-backlog.md`,
    "Tests that could not fail at the end of M2"); this is the cheap guard
    against adding another.
    """
    nonempty: set[Op] = set()
    for ri in _grid_instrs():
        if _registers_touched(ri):
            nonempty.add(ri.op)
    assert nonempty == set(Op) - _NO_REGISTER_OPCODES, sorted(
        op.name for op in (set(Op) - _NO_REGISTER_OPCODES) ^ nonempty)


def test_a_dropped_effects_row_entry_is_caught():
    """Fault injection: the assertion has teeth.

    Removes one register from a real row's `reads`/`writes` and confirms the
    subset check fails -- the check is only worth running if a genuinely
    incomplete effects row cannot pass it.
    """
    import dataclasses

    ri = mk_instr(Op.GETTABLE, a=1, b=2, c=3, pc=1)
    fx = analyze(ri, EffectMode.STRICT)
    touched = _registers_touched(ri)
    assert touched <= (fx.reads | fx.writes)          # the honest table passes
    for drop in sorted(touched):
        broken = dataclasses.replace(
            fx, reads=fx.reads - {drop}, writes=fx.writes - {drop})
        assert not touched <= (broken.reads | broken.writes), (
            f"dropping register {drop} from GETTABLE's effects row went "
            "undetected; the subset check is not load-bearing for it")

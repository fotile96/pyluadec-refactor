"""`LEN` at `NO_METAMETHOD`: `PURE` -> `READ_HEAP` (M5 task 1).

`lift/effects.py` is the axiom layer, so a grading change here needs an
`lvm.c` citation *plus* a differential run (CLAUDE.md; M4 task 8 is the worked
example). This module is where both live for this one cell.

## The citation, re-verified against `vendor/lua-5.1/src/` this session

`OP_LEN` is `lvm.c:514-533`. It switches on the operand's type *before* any
metamethod is considered:

* `lvm.c:517-520` -- `case LUA_TTABLE:` is
  `setnvalue(ra, cast_num(luaH_getn(hvalue(rb))))`.
* `lvm.c:521-524` -- `case LUA_TSTRING:` reads `tsvalue(rb)->len`, an
  immutable field of the string object. This arm really is `PURE`.
* `lvm.c:525-530` -- `default:` is the only metamethod arm
  (`call_binTM(..., TM_LEN)`, else `luaG_typeerror`). **A table never reaches
  it**: the `LUA_TTABLE` case above returns first. Lua 5.1 therefore has no
  `__len` for tables at all, which is exactly why `NO_METAMETHOD` -- whose
  whole content is "assume no metamethod fires" -- cannot make the table arm
  go away.

And the table arm reads the table. `luaH_getn` (`ltable.c:560-576`) reads
`t->sizearray` and `t->array[...]` while binary-searching for a boundary in
the array part (`ltable.c:561-571`); when the boundary is in the hash part it
delegates to `unbound_search` (`ltable.c:532-553`), which calls `luaH_getnum`
(`ltable.c:435-449`) repeatedly, walking hash nodes. Every one of those is a
read of a heap object whose contents a `SETTABLE` can change.

So the pre-M5 grading (`PURE` under `NO_METAMETHOD`) licensed reordering a
`SETTABLE` across a `#t`, which changes the result. `READ_HEAP` is the exact
grading: it reads the heap, and writes nothing but `ra`. `STRICT` (`ARBITRARY`,
for the `default:` arm's arbitrary `__len` on a non-table) and `TRUSTING`
(`PURE` -- reordering table reads freely is precisely what `TRUSTING` assumes)
are correct as they stand and are pinned below so this change stays confined
to one cell.

## The differential run, measured 2026-08-12

`classify_registers`' four fields (`locals`/`temps`/`loop_vars`/`temp_defs`)
plus every proto's certification `level`/`rung`/`refusal_reason`, swept over
**all 1944 proto occurrences of the 229 corpus files** before and after the
change: **the two sweeps are byte-identical -- 0 protos changed in any field,
0 levels moved** (sweep output sha256
`5d5e433519db956e93766f0b504b8660712d0d8229cb5c7631d5036e0efea3fe` both
times), and `corpus/ledger.jsonl` is unchanged
(`a45d8e065657a94bce7391eebfcf450aa1bdc1fee0a614092862ce317ddb1039`,
reproduced byte-for-byte by `scripts/run_corpus.py`).

**Null was the prediction, and it holds for two independent reasons, both
measured rather than assumed:**

1. Nothing in `src/` selects a looser mode -- `lift_proto`'s default is
   `STRICT` and no module names `EffectMode.NO_METAMETHOD`, pinned by
   `test_effects_modes.py::test_strict_is_the_default_and_the_only_mode_in_use`.
   The changed column is therefore never read by the pipeline.
2. Stronger, and the reason the sweep could not have moved even at
   `NO_METAMETHOD`: **no module under `src/pyluadec/` reads `InstrEffects.effect`
   at all.** Downstream consumes only `reads`/`writes`/`reads_open`/
   `writes_open` (`express/names.py`, `express/reconstruct.py`). The effect
   lattice stopped being the inlining gate at M3 task 8 and has had no
   consumer since. `test_nothing_in_src_reads_the_effect_field` below pins
   that, so the first pass to start consuming `.effect` has to notice that
   this differential's second leg no longer holds.

Consequence worth stating plainly rather than dressing up: **this correction
is unobservable in today's pipeline.** It is made because the axiom layer is
supposed to be true, not because anything downstream moved. No synthetic
fixture can show the row load-bearing the way M4 task 8's `TAILCALL` fixture
could -- that row moved `classify_registers`, which reads `writes_open`;
this one moves `effect`, which nothing reads.
"""


def test_len_is_read_heap_under_no_metamethod():
    """`#t` reads the table under `NO_METAMETHOD`; it is not `PURE`.

    See the module docstring for the `lvm.c`/`ltable.c` citations. The
    condition that must be TRUE of the runtime for this grading to be sound:
    nothing, beyond `NO_METAMETHOD`'s own assumption. `READ_HEAP` says the
    opcode may read heap objects and writes none, which is what
    `luaH_getn`/`luaH_getnum` do; the string arm reads only immutable bytes,
    which `READ_HEAP` also permits (it is an over-approximation there, and the
    grading is per-opcode, not per-operand-type).

    `may_error` stays True at every mode: `luaG_typeerror` (`lvm.c:528`) fires
    on an operand that is neither table nor string and carries no `__len`,
    with no metamethod anywhere in sight.
    """
    from pyluadec.lift.effects import Effect, EffectMode, analyze
    from pyluadec.lift.opcodes import Op, decode
    ri = decode(int(Op.LEN) | (1 << 6) | (2 << 23), pc=0)
    assert analyze(ri, EffectMode.NO_METAMETHOD).effect is Effect.READ_HEAP


def test_len_strict_and_trusting_columns_are_untouched():
    """The defect was one cell; the other two columns and the operand model stay put.

    `STRICT` = `ARBITRARY` because `lvm.c:525-530`'s `default:` arm can run an
    arbitrary `__len` on a non-table operand. `TRUSTING` = `PURE` because
    reordering a table *read* against anything else is exactly the assumption
    `TRUSTING` adds -- the very licence `NO_METAMETHOD` must not grant.
    """
    from pyluadec.lift.effects import Effect, EffectMode, analyze
    from pyluadec.lift.opcodes import Op, decode
    ri = decode(int(Op.LEN) | (1 << 6) | (2 << 23), pc=0)
    assert analyze(ri, EffectMode.STRICT).effect is Effect.ARBITRARY
    assert analyze(ri, EffectMode.TRUSTING).effect is Effect.PURE
    for mode in EffectMode:
        fx = analyze(ri, mode)
        assert fx.reads == frozenset({2}), mode
        assert fx.writes == frozenset({1}), mode
        assert not fx.reads_open and not fx.writes_open, mode
        assert fx.may_error, mode


def test_unm_keeps_pure_under_no_metamethod():
    """`UNM` shared `LEN`'s `_row` branch and must NOT move with it.

    Before this task the table read `if op in (Op.UNM, Op.LEN):`, so the
    obvious edit -- change the branch's `NO_METAMETHOD` column -- would have
    regraded `UNM` too. `UNM` genuinely is `PURE` there: `lvm.c:498-508`'s
    non-number path is `Arith(ra, rb, rb, TM_UNM)` (`lvm.c:317-337`), whose
    only heap-touching step is `call_binTM`; strip that and `luaV_tonumber`
    parses the operand's own immutable bytes and writes `ra`. This test is the
    reason the branch had to be split rather than edited in place.
    """
    from pyluadec.lift.effects import Effect, EffectMode, analyze
    from pyluadec.lift.opcodes import Op, decode
    ri = decode(int(Op.UNM) | (1 << 6) | (2 << 23), pc=0)
    assert analyze(ri, EffectMode.STRICT).effect is Effect.ARBITRARY
    assert analyze(ri, EffectMode.NO_METAMETHOD).effect is Effect.PURE
    assert analyze(ri, EffectMode.TRUSTING).effect is Effect.PURE
    assert analyze(ri, EffectMode.STRICT).reads == frozenset({2})
    assert analyze(ri, EffectMode.STRICT).writes == frozenset({1})


def test_nothing_in_src_reads_the_effect_field():
    """Leg 2 of this task's null differential, pinned instead of narrated.

    The differential above is null partly because no pipeline module reads
    `InstrEffects.effect` -- only `reads`/`writes`/`reads_open`/`writes_open`
    are consumed. That is a fact about the tree, and facts about the tree go
    stale. If a future pass starts gating on `.effect`, this test fails and
    whoever wrote that pass learns that the M5 task 1 differential's second
    leg no longer holds -- i.e. that an axiom-layer grading change now has to
    be re-swept for real rather than predicted null.

    Failing this test is not a defect. It means: re-run the sweep, then update
    this test and the module docstring with what you measured.
    """
    import ast
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / "src" / "pyluadec"
    offenders = []
    for path in sorted(src.rglob("*.py")):
        if path.name == "effects.py" and path.parent.name == "lift":
            continue          # the table itself defines and returns the field
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            # An AST walk, not a text scan: `.effects` (the LirInstr field
            # that IS consumed everywhere) contains `.effect` as a substring,
            # so a substring scan would flag every real user and prove
            # nothing.
            if isinstance(node, ast.Attribute) and node.attr == "effect":
                offenders.append((str(path.relative_to(src)), node.lineno))
    assert offenders == [], (
        f"a src/ module now reads InstrEffects.effect: {offenders}. The M5 "
        f"task 1 differential predicted null partly because nothing did; "
        f"re-measure before trusting that prediction again.")

def _mk(op, a=0, b=0, c=0):
    from pyluadec.lift.opcodes import decode
    word = int(op) | (a << 6) | (c << 14) | (b << 23)
    return decode(word, pc=10)


def _mk_sbx(op, a, sbx):
    from pyluadec.lift.opcodes import decode
    word = int(op) | (a << 6) | ((sbx + 131071) << 14)
    return decode(word, pc=10)


def test_all_38_opcodes_covered():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    for op in Op:
        ri = _mk(op, a=1, b=1, c=1) if op.name not in ("JMP", "FORLOOP", "FORPREP") \
            else _mk_sbx(op, 1, 0)
        for mode in EffectMode:
            fx = analyze(ri, mode)          # 任何 opcode 任何档位都必须有定义
            assert fx.effect is not None


def test_getglobal_effect_ladder():
    from pyluadec.lift.effects import analyze, Effect, EffectMode
    from pyluadec.lift.opcodes import Op
    ri = _mk(Op.GETGLOBAL, a=0, b=0)
    assert analyze(ri, EffectMode.STRICT).effect is Effect.ARBITRARY
    assert analyze(ri, EffectMode.NO_METAMETHOD).effect is Effect.READ_HEAP
    assert analyze(ri, EffectMode.TRUSTING).effect is Effect.PURE


def test_gettable_rk_reads():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    ri = _mk(Op.GETTABLE, a=3, b=1, c=256 + 4)     # C 是常量 → 不读寄存器
    fx = analyze(ri, EffectMode.STRICT)
    assert fx.reads == frozenset({1}) and fx.writes == frozenset({3})
    ri = _mk(Op.GETTABLE, a=3, b=1, c=2)            # C 是寄存器
    assert analyze(ri, EffectMode.STRICT).reads == frozenset({1, 2})


def test_call_open_flags():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.CALL, a=2, b=0, c=1), EffectMode.STRICT)
    assert fx.reads_open and not fx.writes_open and 2 in fx.reads
    fx = analyze(_mk(Op.CALL, a=2, b=1, c=0), EffectMode.STRICT)
    assert fx.writes_open and not fx.reads_open
    fx = analyze(_mk(Op.CALL, a=2, b=3, c=2), EffectMode.STRICT)
    assert fx.reads == frozenset({2, 3, 4}) and fx.writes == frozenset({2})


def test_successors():
    from pyluadec.lift.effects import successors
    from pyluadec.lift.opcodes import Op
    assert successors(_mk_sbx(Op.JMP, 0, 5)) == (16,)          # pc=10 → 10+1+5
    assert successors(_mk_sbx(Op.FORLOOP, 0, -4)) == (7, 11)
    assert successors(_mk(Op.EQ, a=1, b=1, c=2)) == (11, 12)
    assert successors(_mk(Op.LOADBOOL, a=0, b=1, c=1)) == (12,)
    assert successors(_mk(Op.LOADBOOL, a=0, b=1, c=0)) == (11,)
    assert successors(_mk(Op.RETURN, a=0, b=1)) == ()
    assert successors(_mk(Op.TAILCALL, a=0, b=1, c=0)) == ()
    assert successors(_mk(Op.CLOSURE, a=0), nups_of_closure=2) == (13,)


def test_extra_words():
    from pyluadec.lift.effects import extra_words
    from pyluadec.lift.opcodes import Op
    assert extra_words(_mk(Op.CLOSURE, a=0), nups_of_closure=3) == 3
    assert extra_words(_mk(Op.SETLIST, a=0, b=1, c=0)) == 1
    assert extra_words(_mk(Op.SETLIST, a=0, b=1, c=1)) == 0
    assert extra_words(_mk(Op.MOVE)) == 0


def test_closure_requires_nups():
    import pytest
    from pyluadec.lift.effects import successors
    from pyluadec.lift.opcodes import Op
    with pytest.raises(ValueError):
        successors(_mk(Op.CLOSURE, a=0))            # 忘传 nups 必须炸，不许静默猜 0

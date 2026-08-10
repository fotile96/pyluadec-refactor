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


# ---------------------------------------------------------------------------
# Per-opcode value assertions (reads/writes/may_error), not just "didn't crash".
#
# test_all_38_opcodes_covered above only proves analyze() returns *something*
# for every opcode — it cannot catch a wrong reads/writes/may_error set. These
# tests pin down the actual values for every opcode named in the fix-round
# review as under-tested, with particular attention to every B==0/C==0 "open"
# formula (not just CALL's) and to the FORLOOP/TFORLOOP/RETURN traps that were
# fault-injected and previously slipped through undetected.
# ---------------------------------------------------------------------------


def test_loadnil_writes_range():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.LOADNIL, a=2, b=5), EffectMode.STRICT)
    assert fx.reads == frozenset()
    assert fx.writes == frozenset({2, 3, 4, 5})
    assert not fx.may_error


def test_self_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.SELF, a=3, b=1, c=256 + 4), EffectMode.STRICT)  # C 常量
    assert fx.reads == frozenset({1})
    assert fx.writes == frozenset({3, 4})
    assert fx.may_error
    fx = analyze(_mk(Op.SELF, a=3, b=1, c=2), EffectMode.STRICT)        # C 寄存器
    assert fx.reads == frozenset({1, 2})
    assert fx.writes == frozenset({3, 4})


def test_settable_rk_reads():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.SETTABLE, a=1, b=2, c=3), EffectMode.STRICT)    # B,C 都是寄存器
    assert fx.reads == frozenset({1, 2, 3})
    assert fx.writes == frozenset()
    assert fx.may_error
    fx = analyze(_mk(Op.SETTABLE, a=1, b=256 + 5, c=256 + 6), EffectMode.STRICT)  # 都是常量
    assert fx.reads == frozenset({1})


def test_setlist_effect_and_open_flag():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.SETLIST, a=1, b=3, c=1), EffectMode.STRICT)     # B!=0 固定
    assert fx.reads == frozenset({1, 2, 3, 4})    # A ∪ A+1..A+B
    assert not fx.reads_open
    assert fx.may_error
    fx = analyze(_mk(Op.SETLIST, a=1, b=0, c=1), EffectMode.STRICT)     # B==0 open
    assert fx.reads == frozenset({1})             # 只有表寄存器是确定的
    assert fx.reads_open


def test_arith_group_rk_reads_and_error():
    from pyluadec.lift.effects import analyze, Effect, EffectMode
    from pyluadec.lift.opcodes import Op
    for op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
        fx = analyze(_mk(op, a=1, b=2, c=3), EffectMode.STRICT)         # B,C 寄存器
        assert fx.reads == frozenset({2, 3}), op
        assert fx.writes == frozenset({1}), op
        assert fx.may_error, op
        assert analyze(_mk(op, a=1, b=2, c=3), EffectMode.NO_METAMETHOD).effect is Effect.PURE, op
        fx_k = analyze(_mk(op, a=1, b=256 + 2, c=256 + 3), EffectMode.STRICT)  # B,C 常量
        assert fx_k.reads == frozenset(), op


def test_unm_len_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    for op in (Op.UNM, Op.LEN):
        fx = analyze(_mk(op, a=1, b=2), EffectMode.STRICT)
        assert fx.reads == frozenset({2}), op
        assert fx.writes == frozenset({1}), op
        assert fx.may_error, op


def test_not_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.NOT, a=1, b=2), EffectMode.STRICT)
    assert fx.reads == frozenset({2})
    assert fx.writes == frozenset({1})
    assert not fx.may_error


def test_concat_reads_register_range():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.CONCAT, a=1, b=2, c=5), EffectMode.STRICT)
    assert fx.reads == frozenset({2, 3, 4, 5})    # B..C 寄存器区间，不是 RK
    assert fx.writes == frozenset({1})
    assert fx.may_error


def test_lt_le_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    for op in (Op.LT, Op.LE):
        fx = analyze(_mk(op, a=1, b=2, c=3), EffectMode.STRICT)
        assert fx.reads == frozenset({2, 3}), op
        assert fx.writes == frozenset(), op
        assert fx.may_error, op                   # 与 EQ（永不抛）明确区分


def test_test_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.TEST, a=3, c=1), EffectMode.STRICT)
    assert fx.reads == frozenset({3})
    assert fx.writes == frozenset()
    assert not fx.may_error


def test_testset_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.TESTSET, a=3, b=4, c=1), EffectMode.STRICT)
    assert fx.reads == frozenset({4})
    assert fx.writes == frozenset({3})
    assert not fx.may_error


def test_return_effect_fixed_and_open():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.RETURN, a=2, b=3), EffectMode.STRICT)           # B>=2: 固定 B-1 个值
    assert fx.reads == frozenset({2, 3})
    assert not fx.reads_open
    assert not fx.may_error
    fx = analyze(_mk(Op.RETURN, a=2, b=0), EffectMode.STRICT)           # B==0: open
    assert fx.reads == frozenset()
    assert fx.reads_open


def test_vararg_effect_fixed_and_open():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.VARARG, a=2, b=3), EffectMode.STRICT)           # B>=2: 固定 B-1 个值
    assert fx.writes == frozenset({2, 3})
    assert not fx.writes_open
    fx = analyze(_mk(Op.VARARG, a=2, b=0), EffectMode.STRICT)           # B==0: open
    assert fx.writes == frozenset()
    assert fx.writes_open


def test_tailcall_effect_fixed_and_open():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.TAILCALL, a=2, b=3, c=0), EffectMode.STRICT)    # B!=0: 固定参数
    assert fx.reads == frozenset({2, 3, 4})
    assert not fx.reads_open
    assert fx.writes == frozenset()
    fx = analyze(_mk(Op.TAILCALL, a=2, b=0, c=0), EffectMode.STRICT)    # B==0: open
    assert fx.reads == frozenset({2})
    assert fx.reads_open


def test_forprep_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk_sbx(Op.FORPREP, 3, 0), EffectMode.STRICT)
    assert fx.reads == frozenset({3, 4, 5})
    assert fx.writes == frozenset({3, 4, 5})
    assert fx.may_error


def test_forloop_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk_sbx(Op.FORLOOP, 3, 0), EffectMode.STRICT)
    assert fx.reads == frozenset({3, 4, 5})
    assert fx.writes == frozenset({3, 6})         # A（内部索引）∪ A+3（用户可见循环变量）


def test_tforloop_effect():
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.TFORLOOP, a=3, c=2), EffectMode.STRICT)
    assert fx.reads == frozenset({3, 4, 5})
    assert fx.writes == frozenset({5, 6, 7})      # A+2（控制变量）∪ A+3..A+2+C（结果）
    assert fx.may_error


def test_close_effect():
    from pyluadec.lift.effects import analyze, Effect, EffectMode
    from pyluadec.lift.opcodes import Op
    fx = analyze(_mk(Op.CLOSE, a=3), EffectMode.STRICT)
    assert fx.reads == frozenset()
    assert fx.writes == frozenset()
    assert not fx.may_error
    assert fx.effect is Effect.WRITE_HEAP


def test_effect_ladder_monotonic_for_all_opcodes():
    """STRICT >= NO_METAMETHOD >= TRUSTING 必须对每个 opcode 都成立（Effect 是 IntEnum 全序）。"""
    from pyluadec.lift.effects import analyze, EffectMode
    from pyluadec.lift.opcodes import Op
    for op in Op:
        ri = _mk(op, a=1, b=1, c=1) if op.name not in ("JMP", "FORLOOP", "FORPREP") \
            else _mk_sbx(op, 1, 0)
        strict = analyze(ri, EffectMode.STRICT).effect
        no_mm = analyze(ri, EffectMode.NO_METAMETHOD).effect
        trusting = analyze(ri, EffectMode.TRUSTING).effect
        assert strict >= no_mm >= trusting, op

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


# ---------------------------------------------------------------------------
# Exhaustive table-driven backstop.
#
# The targeted tests above (and test_all_38_opcodes_covered / the monotonicity
# check) can miss a wrong-but-plausible row: "effect is not None" holds for any
# row, and a monotonic-but-wrong row passes the ladder check too. Neither of
# those — nor any targeted test for an opcode nobody thought to hand-test — can
# catch e.g. EQ silently dropping its C operand from reads, or SETGLOBAL's
# may_error flipped.
#
# This table pins the COMPLETE expected InstrEffects (reads, writes,
# reads_open, writes_open, may_error, effect@STRICT/NO_METAMETHOD/TRUSTING)
# for every opcode, with a separate row per meaningfully distinct operand form
# (the B==0/C==0 "open" branches of CALL, TAILCALL, RETURN, VARARG, SETLIST).
# Every value below was worked out by hand from vendor/lua-5.1/src/lvm.c's
# luaV_execute switch (register/RK reads per case, what gets written, which
# case can reach luaG_typeerror/luaG_runerror/ordererror/concaterror without a
# metamethod) — not by reading effects.py's return tuples back to itself.
#
# test_exhaustive_effects_table_covers_all_opcodes additionally asserts every
# one of the 38 Op members appears at least once, so a forgotten row (or an
# unhandled 39th opcode down the line) fails loudly instead of silently
# passing by omission.
# ---------------------------------------------------------------------------

from pyluadec.lift.effects import Effect as _Effect          # noqa: E402
from pyluadec.lift.opcodes import Op as _Op                  # noqa: E402

_PURE, _RH, _WH, _ARB = _Effect.PURE, _Effect.READ_HEAP, _Effect.WRITE_HEAP, _Effect.ARBITRARY

# (label, RawInstr, reads, writes, reads_open, writes_open, may_error,
#  effect@STRICT, effect@NO_METAMETHOD, effect@TRUSTING)
_EXHAUSTIVE_CASES = [
    ("MOVE",
     _mk(_Op.MOVE, a=1, b=2),
     frozenset({2}), frozenset({1}), False, False, False, _PURE, _PURE, _PURE),

    ("LOADK",  # Bx is a constant-table index, not a register; lvm.c: setobj2s(ra, KBx(i))
     _mk(_Op.LOADK, a=1),
     frozenset(), frozenset({1}), False, False, False, _PURE, _PURE, _PURE),

    ("LOADBOOL",  # lvm.c: setbvalue(ra, B); B/C are plain values, not registers
     _mk(_Op.LOADBOOL, a=1, b=1, c=0),
     frozenset(), frozenset({1}), False, False, False, _PURE, _PURE, _PURE),

    ("LOADNIL",  # lvm.c: walks rb=RB(i) down to ra inclusive, writing nil each step
     _mk(_Op.LOADNIL, a=1, b=3),
     frozenset(), frozenset({1, 2, 3}), False, False, False, _PURE, _PURE, _PURE),

    ("NEWTABLE",  # lvm.c: sethvalue(ra, luaH_new(...)); no TM path, B/C are size hints
     _mk(_Op.NEWTABLE, a=1),
     frozenset(), frozenset({1}), False, False, False, _PURE, _PURE, _PURE),

    ("GETUPVAL",  # lvm.c: setobj2s(ra, cl->upvals[b]->v); B is an upvalue index, not a register
     _mk(_Op.GETUPVAL, a=1, b=2),
     frozenset(), frozenset({1}), False, False, False, _RH, _RH, _RH),

    ("GETGLOBAL",  # lvm.c: Protect(luaV_gettable(&g, rb, ra)); g is always a table -> no direct type error
     _mk(_Op.GETGLOBAL, a=1),
     frozenset(), frozenset({1}), False, False, False, _ARB, _RH, _PURE),

    ("GETTABLE",  # lvm.c: Protect(luaV_gettable(RB(i), RKC(i), ra)); non-table B with no __index -> typeerror
     _mk(_Op.GETTABLE, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1}), False, False, True, _ARB, _RH, _PURE),

    ("SETGLOBAL",  # lvm.c: Protect(luaV_settable(&g, KBx(i), ra)); g always a table -> no direct type error
     _mk(_Op.SETGLOBAL, a=1),
     frozenset({1}), frozenset(), False, False, False, _ARB, _WH, _WH),

    ("SETUPVAL",  # lvm.c: setobj(uv->v, ra); luaC_barrier -- B is an upvalue index, not a register
     _mk(_Op.SETUPVAL, a=1, b=2),
     frozenset({1}), frozenset(), False, False, False, _WH, _WH, _WH),

    ("SETTABLE",  # lvm.c: Protect(luaV_settable(ra, RKB(i), RKC(i))); can typeerror like GETTABLE
     _mk(_Op.SETTABLE, a=1, b=2, c=3),
     frozenset({1, 2, 3}), frozenset(), False, False, True, _ARB, _WH, _WH),

    ("SELF",  # lvm.c: setobjs2s(ra+1, rb); Protect(luaV_gettable(rb, RKC(i), ra))
     _mk(_Op.SELF, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1, 2}), False, False, True, _ARB, _RH, _PURE),

    ("ADD",  # arith_op macro: fast path if both numbers, else Protect(Arith(...)) w/ coercion-or-TM-or-error
     _mk(_Op.ADD, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),
    ("SUB",
     _mk(_Op.SUB, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),
    ("MUL",
     _mk(_Op.MUL, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),
    ("DIV",
     _mk(_Op.DIV, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),
    ("MOD",
     _mk(_Op.MOD, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),
    ("POW",
     _mk(_Op.POW, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),

    ("UNM",  # lvm.c: number fast path, else Protect(Arith(ra, rb, rb, TM_UNM)); B is register-only (OpArgR)
     _mk(_Op.UNM, a=1, b=2),
     frozenset({2}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),

    ("NOT",  # lvm.c: l_isfalse(RB(i)); never errors
     _mk(_Op.NOT, a=1, b=2),
     frozenset({2}), frozenset({1}), False, False, False, _PURE, _PURE, _PURE),

    # NO_METAMETHOD is READ_HEAP, not PURE: the LUA_TTABLE arm (lvm.c:517-520)
    # runs luaH_getn, which reads the table, and a table never reaches the
    # metamethod arm at all (Lua 5.1 has no table `__len`). M5 task 1; the
    # citation and the differential run are in tests/test_effects_len.py.
    ("LEN",  # lvm.c: table/string fast path, else Protect(call_binTM(...)) or typeerror
     _mk(_Op.LEN, a=1, b=2),
     frozenset({2}), frozenset({1}), False, False, True, _ARB, _RH, _PURE),

    ("CONCAT",  # lvm.c: B..C is a register RANGE (OpArgR/OpArgR), not RK; luaV_concat can TM or concaterror
     _mk(_Op.CONCAT, a=1, b=2, c=4),
     frozenset({2, 3, 4}), frozenset({1}), False, False, True, _ARB, _PURE, _PURE),

    ("JMP",  # lvm.c: dojump only
     _mk_sbx(_Op.JMP, 1, 0),
     frozenset(), frozenset(), False, False, False, _PURE, _PURE, _PURE),

    ("EQ",  # lvm.c: equalobj(rb, rc); reads BOTH operands; never errors without a TM
     _mk(_Op.EQ, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset(), False, False, False, _ARB, _PURE, _PURE),

    ("LT",  # lvm.c: luaV_lessthan; luaG_ordererror on incomparable types even with no TM
     _mk(_Op.LT, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset(), False, False, True, _ARB, _PURE, _PURE),
    ("LE",
     _mk(_Op.LE, a=1, b=2, c=3),
     frozenset({2, 3}), frozenset(), False, False, True, _ARB, _PURE, _PURE),

    ("TEST",  # lvm.c: l_isfalse(ra) != C; B unused (bmode N), C is a sense flag not a register
     _mk(_Op.TEST, a=1, c=1),
     frozenset({1}), frozenset(), False, False, False, _PURE, _PURE, _PURE),

    ("TESTSET",  # lvm.c: conditionally setobjs2s(ra, rb); reads B always, writes A on the taken branch
     _mk(_Op.TESTSET, a=1, b=2, c=1),
     frozenset({2}), frozenset({1}), False, False, False, _PURE, _PURE, _PURE),

    ("CALL fixed args/results",  # lvm.c: if(b!=0) top=ra+b; nresults=c-1
     _mk(_Op.CALL, a=2, b=3, c=2),
     frozenset({2, 3, 4}), frozenset({2}), False, False, True, _ARB, _ARB, _ARB),
    ("CALL open args (B==0)",
     _mk(_Op.CALL, a=2, b=0, c=1),
     frozenset({2}), frozenset(), True, False, True, _ARB, _ARB, _ARB),
    ("CALL open results (C==0)",
     _mk(_Op.CALL, a=2, b=1, c=0),
     frozenset({2}), frozenset(), False, True, True, _ARB, _ARB, _ARB),

    # lvm.c:611 asserts C is always 0, so TAILCALL has no fixed-result form:
    # writes_open is unconditional. On the PCRLUA path (lvm.c:613-629) the
    # frame is replaced and control never returns to the next instruction, but
    # on the PCRC path (lvm.c:630-632, a C-function callee) luaD_precall has
    # already left the results at R[a..top) and execution falls through --
    # so the union of the two paths writes an open region and nothing fixed.
    # (M4 task 8; `writes` stays empty because the region is top-relative.)
    ("TAILCALL fixed args",
     _mk(_Op.TAILCALL, a=2, b=3, c=0),
     frozenset({2, 3, 4}), frozenset(), False, True, True, _ARB, _ARB, _ARB),
    ("TAILCALL open args (B==0)",
     _mk(_Op.TAILCALL, a=2, b=0, c=0),
     frozenset({2}), frozenset(), True, True, True, _ARB, _ARB, _ARB),

    ("RETURN fixed",  # lvm.c: if(b!=0) top=ra+b-1 -> b-1 values at ra..ra+b-2
     _mk(_Op.RETURN, a=2, b=3),
     frozenset({2, 3}), frozenset(), False, False, False, _PURE, _PURE, _PURE),
    ("RETURN open (B==0)",
     _mk(_Op.RETURN, a=2, b=0),
     frozenset(), frozenset(), True, False, False, _PURE, _PURE, _PURE),

    ("FORPREP",  # lvm.c: 3x tonumber (can rewrite in place) then setnvalue(ra, init-step); errors on non-number
     _mk_sbx(_Op.FORPREP, 3, 0),
     frozenset({3, 4, 5}), frozenset({3, 4, 5}), False, False, True, _PURE, _PURE, _PURE),

    ("FORLOOP",  # lvm.c: reads idx/limit/step at A,A+1,A+2; on the taken branch writes A (internal) and A+3 (external)
     _mk_sbx(_Op.FORLOOP, 3, 0),
     frozenset({3, 4, 5}), frozenset({3, 6}), False, False, True, _PURE, _PURE, _PURE),

    ("TFORLOOP",  # lvm.c: calls iterator(A,A+1,A+2) -> C results at A+3..A+2+C, control var updated at A+2
     _mk(_Op.TFORLOOP, a=3, c=2),
     frozenset({3, 4, 5}), frozenset({5, 6, 7}), False, False, True, _ARB, _ARB, _ARB),

    ("SETLIST fixed (B!=0)",  # lvm.c: n=B fixed count -> reads A (table) and A+1..A+B
     _mk(_Op.SETLIST, a=1, b=3, c=1),
     frozenset({1, 2, 3, 4}), frozenset(), False, False, True, _ARB, _WH, _WH),
    ("SETLIST open (B==0)",  # lvm.c: n = top-ra-1 -- open register range above A
     _mk(_Op.SETLIST, a=1, b=0, c=1),
     frozenset({1}), frozenset(), True, False, True, _ARB, _WH, _WH),

    ("CLOSE",  # lvm.c: luaF_close(L, ra) -- mutates the upvalue-binding side channel, not a numbered register
     _mk(_Op.CLOSE, a=3),
     frozenset(), frozenset(), False, False, False, _WH, _WH, _WH),

    ("CLOSURE",  # lvm.c: setclvalue(ra, ncl); captured-register reads come from the trailing pseudo-instructions
     _mk(_Op.CLOSURE, a=1),
     frozenset(), frozenset({1}), False, False, False, _PURE, _PURE, _PURE),

    ("VARARG fixed",  # lvm.c: b=B-1 concrete -> writes ra..ra+b-1
     _mk(_Op.VARARG, a=2, b=3),
     frozenset(), frozenset({2, 3}), False, False, False, _PURE, _PURE, _PURE),
    ("VARARG open (B==0)",  # lvm.c: b==LUA_MULTRET -> writes the open L->top range
     _mk(_Op.VARARG, a=2, b=0),
     frozenset(), frozenset(), False, True, False, _PURE, _PURE, _PURE),
]


def test_exhaustive_effects_table_covers_all_opcodes():
    """A forgotten row (or an unhandled 39th opcode) must fail loudly, not silently pass by omission."""
    seen = {case[1].op for case in _EXHAUSTIVE_CASES}
    missing = set(_Op) - seen
    assert not missing, f"opcodes missing from the exhaustive table: {sorted(op.name for op in missing)}"


def test_exhaustive_effects_table_values():
    from pyluadec.lift.effects import analyze, EffectMode
    for (label, ri, reads, writes, reads_open, writes_open,
         may_error, strict, no_mm, trusting) in _EXHAUSTIVE_CASES:
        fx = analyze(ri, EffectMode.STRICT)
        assert fx.reads == reads, label
        assert fx.writes == writes, label
        assert fx.reads_open == reads_open, label
        assert fx.writes_open == writes_open, label
        assert fx.may_error == may_error, label
        assert fx.effect is strict, label
        assert analyze(ri, EffectMode.NO_METAMETHOD).effect is no_mm, label
        assert analyze(ri, EffectMode.TRUSTING).effect is trusting, label

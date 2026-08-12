"""Per-opcode effect table — the project's axiom layer (spec §3 layer 2).

改动本文件 = 改动公理，必须同步 no-frills PDF / lvm.c 依据并跑全部差分测试。

**谁在读这张表，以及谁不读（2026-08-13 实测，M5 task 1 发现 / task 12 收口）。**
`reads` / `writes` / `reads_open` / `writes_open` 被 `structure/fallback.py`、
`express/`、两道 effects 一致性门实际消费。`InstrEffects.effect`（三档效应格
本身）**在 `src/pyluadec/` 里没有任何消费者**——由
`tests/test_effects_len.py::test_nothing_in_src_reads_the_effect_field` 以 AST
扫描钉住（该测试失败不等于缺陷，见其 docstring）。

本 docstring 原文写的是「一切上层（内联门、pass 验证、fallback 发射）共享此处
结论」。三个例子里有两个已经不成立：内联门自 M3 task 8 起改为模拟 `lparser.c`
的 freereg 分配纪律（`express/freereg.py`），不再读效应格；spec §4 的 pass
registry 已于 M5 永久退役（决策记录在 spec §2 决策表）。`fallback` 发射那一项
仍然成立，且读的是 `reads`/`writes` 而不是 `effect`。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum

from .opcodes import Op, RawInstr, isk


class Effect(IntEnum):
    PURE = 0
    READ_HEAP = 1
    WRITE_HEAP = 2
    ARBITRARY = 3


class EffectMode(Enum):
    """The three assumption sets a consumer may grade an opcode under.

    The modes form a *chain of added assumptions*, not three independent
    tables:

        STRICT        assumes nothing beyond the Lua 5.1 VM itself.
        NO_METAMETHOD assumes, additionally, that no value an instruction
                      touches carries a metatable whose event this opcode
                      could fire (`__index`, `__newindex`, `__add` .. `__pow`,
                      `__unm`, `__len`, `__concat`, `__eq`, `__lt`, `__le`).
        TRUSTING      assumes, additionally, that a table *read* may be
                      reordered freely against anything else in the region
                      being transformed -- i.e. that no intervening store or
                      call can change what the read returns.

    Because the assumption sets are nested, a grading that is sound in a
    weaker mode is sound in every stronger one. That is the calibration's
    main lever (M4 task 11): for the 20 opcodes whose three columns are
    *identical*, the two looser columns need no separate argument -- they are
    entailed by STRICT, the column CLAUDE.md says is the argued one. Only the
    18 rows where a looser column is strictly below STRICT carry an assumption
    of their own, and only those get a per-row `# nm:` / `# tr:` note in
    `_row` below.

    Calibration evidence for NO_METAMETHOD, re-derived 2026-08-12
    (`tests/test_effects_modes.py::test_corpus_never_names_metamethod_machinery`):
    across all 229 corpus files / 1944 protos / 71414 constants (49063 of them
    strings, 23586 distinct), **no constant contains the substring `__`**, and
    none contains `setmetatable`, `getmetatable`, `rawget`, `rawset`,
    `rawequal`, `getfenv` or `setfenv`. A Lua 5.1 script cannot install a
    metatable without naming `setmetatable`, and cannot name a metamethod
    event without a `__`-prefixed string, so **no table this corpus builds
    itself carries a metatable**.

    **The limit of that evidence, which must not be dropped when quoting it.**
    The census sees only what the scripts name. It says nothing about values
    the host engine injects. Measured the same session: of the 164 distinct
    global names the corpus reads (51497 `GETGLOBAL` sites), **56 are never
    written by any of the 229 files**, so they arrive from outside the corpus
    (52 are game-engine API -- `layerLoad`, `playBGM`, `fontPrint`, `wait` ...
    -- and 4 are Lua stdlib: `math`, `string`, `pairs`, `select`);
    and 8379 of the 11910 `GETTABLE` sites index a value whose nearest
    textually-preceding writer is a `GETGLOBAL`, against only 188 that index a
    freshly `NEWTABLE`-d one (that last split comes from a straight-line
    backward scan that ignores control flow, so treat it as an order of
    magnitude, not an exact attribution; the 164/56 global-name split above is
    exact). Engine-supplied globals and userdata may carry
    metatables (including `__index`, `__newindex` and `__gc`) that no constant
    table can reveal. Therefore **NO_METAMETHOD is NOT proven for
    `GETGLOBAL`/`GETTABLE`/`SELF`/`SETTABLE` applied to engine values** -- it
    is proven only for tables the script constructed. Enable it per pass, on
    a value class you have separately established, never globally.

    TRUSTING is a strictly weaker footing again, and the corpus *falsifies*
    it rather than merely failing to support it: 892 `SETGLOBAL` sites over
    108 global names that are also read, 29 protos that read and write the
    same global name, 1667 `SETTABLE` + 92 `SETLIST` sites, and 44809 `CALL`
    sites any of which may store into any reachable table. See the four
    `# tr:` rows below (`GETGLOBAL`, `GETTABLE`, `SELF`, `LEN`) -- they are the
    only four rows TRUSTING moves at all, and all four are `# UNARGUED`.
    (`LEN` joined them at M5 task 1: once `#t` is `READ_HEAP` under
    `NO_METAMETHOD`, `TRUSTING` is what takes it back to `PURE`.)

    Default: `STRICT`, and the only consumer in the tree
    (`lift.lift_proto`) takes it as its default argument. See
    `docs/runbooks/structured-pipeline.md`, "The effect lattice".
    """

    STRICT = "strict"                 # 任何表访问/算术都可能触发元方法
    NO_METAMETHOD = "no_metamethod"   # 假设语料不依赖元方法的副作用
    TRUSTING = "trusting"             # 进一步假设表读取可自由重排


@dataclass(frozen=True)
class InstrEffects:
    reads: frozenset[int]
    writes: frozenset[int]
    # The two open-region flags name a `R[base..top)` window whose extent is a
    # RUNTIME value (`L->top`), so it cannot be enumerated into `reads`/`writes`
    # at all. Keep these two enumerations in step with `_row` -- they were
    # already one opcode stale once (M4 task 8 gave TAILCALL `writes_open` and
    # this comment kept saying CALL/VARARG). Verified against `_row` over the
    # full opcode x operand grid, M4 task 12:
    reads_open: bool      # 额外读 R[base..top-1]：CALL B==0 / TAILCALL B==0 /
                          # RETURN B==0 / SETLIST B==0
    writes_open: bool     # 额外写 R[base..top-1]：CALL C==0 / VARARG B==0 /
                          # TAILCALL (unconditional -- see the TAILCALL row)
    effect: Effect
    may_error: bool       # NO_METAMETHOD 假设下仍可能抛错


def _rk(x: int) -> frozenset[int]:
    return frozenset() if isk(x) else frozenset({x})


# 每项: (reads, writes, reads_open, writes_open,
#        effect@STRICT, effect@NO_METAMETHOD, effect@TRUSTING, may_error)
#
# ---------------------------------------------------------------------------
# Per-row mode argument (M4 task 11). Convention:
#
#   `# nm,tr = STRICT (entailed)` -- the two looser columns hold the same
#       grading as STRICT. Since STRICT assumes nothing and the modes only
#       *add* assumptions (see EffectMode's docstring), a grading sound at
#       STRICT is sound at both looser modes for free. No separate argument
#       is owed and none is invented. 20 of the 38 rows are of this shape:
#       MOVE LOADK LOADBOOL LOADNIL NEWTABLE GETUPVAL SETUPVAL NOT JMP TEST
#       TESTSET CALL TAILCALL RETURN FORPREP FORLOOP TFORLOOP CLOSE CLOSURE
#       VARARG.
#
#   `# nm:` / `# tr:` -- that column is strictly below STRICT, so it rests on
#       the mode's own assumption and owes a one-line argument. 18 rows.
#       `# UNARGUED` means exactly that: this revision cannot support the
#       grading, and says so rather than inventing a plausible sentence.
#
# Standing (2026-08-12, after M5 task 1): NO_METAMETHOD is argued on all 38
# rows and `# UNARGUED` on 0 -- LEN was the last one, and was regraded rather
# than argued, because the grading it carried was wrong. TRUSTING moves 4 rows
# below NO_METAMETHOD (GETGLOBAL, GETTABLE, SELF, LEN) and all 4 are
# `# UNARGUED`; the other 34 are entailed. The 20/18 entailment split did NOT
# move with the regrade: LEN was already in the relaxed 18 (its STRICT column
# is ARB and its looser columns were not), and it still is.
# `tests/test_effects_modes.py` pins that 20/18 split and the 4-row TRUSTING
# delta mechanically, so a future grading change that silently invalidates
# this block fails a test.
#
# NOTE (finding, deliberately NOT fixed here -- an axiom-layer grading change
# needs the full protocol): NEWTABLE (lvm.c:461-467) and CLOSURE
# (lvm.c:723-742) both end in `Protect(luaC_checkGC(L))`, and `luaC_checkGC`
# (lgc.h:80) can advance the collector into `GCSfinalize` (lgc.c:592-595),
# where `GCTM` (lgc.c:445-473) calls a userdata's `__gc` metamethod via
# `luaD_call`. Both rows are graded PURE with may_error=False at all three
# modes. That is unobservable for this corpus (no userdata is script-created,
# and no `__gc` string exists in any constant table) but it is an
# under-approximation in general.
# ---------------------------------------------------------------------------
def _row(ri: RawInstr):
    op, a, b, c = ri.op, ri.a, ri.b, ri.c
    F = frozenset
    P, RH, WH, ARB = Effect.PURE, Effect.READ_HEAP, Effect.WRITE_HEAP, Effect.ARBITRARY
    if op is Op.MOVE:
        # nm,tr = STRICT (entailed). lvm.c:407-410 setobjs2s, register-local.
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op in (Op.LOADK, Op.NEWTABLE):
        # nm,tr = STRICT (entailed). LOADK lvm.c:411-414 reads the immutable
        # constant table; NEWTABLE lvm.c:461-467 allocates (see the GC finding
        # in the block above). Neither has a TM path.
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.LOADBOOL:
        # nm,tr = STRICT (entailed). lvm.c:415-419 setbvalue; B/C are literals.
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.LOADNIL:
        # nm,tr = STRICT (entailed). lvm.c:420-426 setnilvalue loop, registers only.
        return F(), F(range(a, b + 1)), 0, 0, P, P, P, False
    if op is Op.GETUPVAL:
        # nm,tr = STRICT (entailed). lvm.c:427-431 reads the upvalue cell; that
        # is a heap read at every mode -- no metatable is consulted, so no mode
        # assumption can remove it.
        return F(), F({a}), 0, 0, RH, RH, RH, False
    if op is Op.SETUPVAL:
        # nm,tr = STRICT (entailed). lvm.c:451-456 writes the upvalue cell; no TM path.
        return F({a}), F(), 0, 0, WH, WH, WH, False
    if op is Op.GETGLOBAL:
        # nm: RH. lvm.c:432-439 wraps `cl->env` (always a table, sethvalue) and
        #     calls luaV_gettable. With no `__index` on the globals table that
        #     reduces to one raw luaH_get -- exactly READ_HEAP, nothing more.
        # tr: PURE -- # UNARGUED. PURE claims the read can be reordered against
        #     any store, which the corpus falsifies: 892 SETGLOBAL sites over
        #     108 global names that are also read, and 29 protos read and write
        #     the same global name. Any consumer selecting TRUSTING must first
        #     establish, per region, that no store to _G intervenes.
        return F(), F({a}), 0, 0, ARB, RH, P, False
    if op is Op.GETTABLE:
        # nm: RH. lvm.c:440-443 Protect(luaV_gettable(RB, RKC, ra)); with no
        #     `__index` on RB this is one raw luaH_get (luaV_gettable,
        #     lvm.c:108-133). may_error stays True: a non-table RB with no
        #     metatable still reaches luaG_typeerror.
        #     Scope: proven only for script-built tables (the census sees no
        #     metatable machinery); NOT proven for engine values.
        # tr: PURE -- # UNARGUED. Same shape as GETGLOBAL: 1667 SETTABLE + 92
        #     SETLIST sites, and 44809 CALL sites that may store anywhere.
        return F({b}) | _rk(c), F({a}), 0, 0, ARB, RH, P, True
    if op is Op.SELF:
        # nm: RH. lvm.c:468-473 is a register copy plus the same
        #     luaV_gettable as GETTABLE; identical argument and identical scope.
        # tr: PURE -- # UNARGUED, identical to GETTABLE's.
        return F({b}) | _rk(c), F({a, a + 1}), 0, 0, ARB, RH, P, True
    if op is Op.SETGLOBAL:
        # nm: WH. lvm.c:444-450 luaV_settable into `cl->env`; with no
        #     `__newindex` that is one raw luaH_set -- exactly WRITE_HEAP.
        # tr = nm (entailed): TRUSTING only licenses reordering table *reads*,
        #     and this row is a write, so TRUSTING adds nothing here.
        return F({a}), F(), 0, 0, ARB, WH, WH, False
    if op is Op.SETTABLE:
        # nm: WH. lvm.c:457-460 Protect(luaV_settable(ra, RKB, RKC)); no
        #     `__newindex` => raw luaH_set. may_error stays True (non-table ra
        #     still reaches luaG_typeerror). Same engine-value scope as GETTABLE.
        # tr = nm (entailed), same reason as SETGLOBAL.
        return F({a}) | _rk(b) | _rk(c), F(), 0, 0, ARB, WH, WH, True
    if op is Op.SETLIST:
        # nm: WH. lvm.c:697-718 has no TM path at all -- luaH_setnum is raw --
        #     so WRITE_HEAP is exact and STRICT's ARB is already conservative.
        # tr = nm (entailed), same reason as SETGLOBAL.
        reads = F({a}) | (F(range(a + 1, a + b + 1)) if b else F())
        return reads, F(), b == 0, 0, ARB, WH, WH, True
    if op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
        # nm: PURE. The arith_op macro (lvm.c:364-373) writes ra directly when
        #     both operands are numbers; otherwise Arith (lvm.c:317-337) coerces
        #     via luaV_tonumber -- string-to-number parsing, which reads only the
        #     operand's own immutable bytes -- and only *then* reaches
        #     call_binTM. Strip the TM branch and nothing outside ra/rb/rc is
        #     touched, so PURE is exact. may_error stays True for
        #     luaG_aritherror on a non-coercible operand.
        # tr = nm (entailed): already PURE, nothing left to relax.
        return _rk(b) | _rk(c), F({a}), 0, 0, ARB, P, P, True
    if op is Op.UNM:
        # nm: PURE, exactly the arith_op argument above (lvm.c:498-508 routes
        #     the non-number case to Arith(.., TM_UNM)).
        # tr = nm (entailed): already PURE, nothing left to relax.
        #
        # UNM shared this branch with LEN until M5 task 1 regraded LEN's
        # NO_METAMETHOD column; the branch was split so that regrade could not
        # drag UNM with it (tests/test_effects_len.py pins both halves).
        return F({b}), F({a}), 0, 0, ARB, P, P, True
    if op is Op.LEN:
        # nm: READ_HEAP (M5 task 1; was PURE and unargued, a defect found
        #     by M4 task 11 and corrected here under the full axiom protocol
        #     -- citation + differential run, recorded in
        #     tests/test_effects_len.py's module docstring).
        #     OP_LEN is lvm.c:514-533 and switches on the operand's TYPE before
        #     any metamethod is consulted: the LUA_TTABLE arm (lvm.c:517-520)
        #     is `setnvalue(ra, cast_num(luaH_getn(hvalue(rb))))`, and a table
        #     therefore NEVER reaches the `default:` metamethod arm
        #     (lvm.c:525-530). Lua 5.1 has no `__len` for tables at all, so
        #     NO_METAMETHOD's assumption removes nothing from this path.
        #     luaH_getn (ltable.c:560-576) reads t->sizearray and t->array[...]
        #     while binary-searching the array part (ltable.c:561-571), and for
        #     a boundary in the hash part delegates to unbound_search
        #     (ltable.c:532-553), which calls luaH_getnum (ltable.c:435-449)
        #     repeatedly. That is a heap read a SETTABLE can invalidate; PURE
        #     licensed reordering a SETTABLE across a `#t`. 22 LEN sites in the
        #     corpus, so the row is not vacuous -- though nothing in src/ reads
        #     InstrEffects.effect today, so the differential was null.
        #     (The LUA_TSTRING arm, lvm.c:521-524, really is PURE -- READ_HEAP
        #     over-approximates it. An earlier draft cited lvm.c:523-526, which
        #     straddles the string and metamethod arms.)
        # tr: PURE -- # UNARGUED. TRUSTING's own assumption is exactly "a table
        #     read may be reordered freely", so PURE is what it licenses by
        #     construction; but the corpus falsifies that assumption (1667
        #     SETTABLE + 92 SETLIST + 44809 CALL sites), same as GETTABLE's.
        return F({b}), F({a}), 0, 0, ARB, RH, P, True
    if op is Op.NOT:
        # nm,tr = STRICT (entailed). lvm.c:509-513 l_isfalse, no TM, no heap.
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op is Op.CONCAT:
        # nm: PURE. lvm.c:534-540 luaV_concat; with no `__concat` every operand
        #     is already a string or number, so the loop only interns a new
        #     string (luaS_newlstr) and writes ra. Interning mutates the global
        #     string table and can trigger GC, which is the same allocation
        #     effect NEWTABLE/CLOSURE are graded PURE for -- consistent with
        #     those rows, and subject to the same GC finding noted above.
        #     may_error stays True for luaG_concaterror.
        # tr = nm (entailed).
        return F(range(b, c + 1)), F({a}), 0, 0, ARB, P, P, True
    if op is Op.JMP:
        # nm,tr = STRICT (entailed). lvm.c:541-544 dojump only.
        return F(), F(), 0, 0, P, P, P, False
    if op is Op.EQ:
        # nm: PURE. lvm.c:545-554 equalobj -> luaV_equalval (lvm.c:255-279):
        #     different types are unequal outright, and same-type primitives
        #     compare by value; the *only* heap-touching path is the TM_EQ
        #     lookup for two distinct tables/userdata. Remove that and the
        #     comparison reads nothing but the two TValues. may_error is
        #     already False at STRICT.
        # tr = nm (entailed).
        return _rk(b) | _rk(c), F(), 0, 0, ARB, P, P, False
    if op in (Op.LT, Op.LE):
        # nm: PURE. lvm.c:555-570; luaV_lessthan/lessequal (lvm.c:225-254)
        #     compare numbers numerically and strings via l_strcmp, which reads
        #     only the operands' own immutable bytes. Everything else is
        #     call_orderTM. may_error stays True for luaG_ordererror on
        #     incomparable types -- that path exists with no metamethod at all.
        # tr = nm (entailed).
        return _rk(b) | _rk(c), F(), 0, 0, ARB, P, P, True
    if op is Op.TEST:
        # nm,tr = STRICT (entailed). lvm.c:571-576 l_isfalse, no TM, no heap.
        return F({a}), F(), 0, 0, P, P, P, False
    if op is Op.TESTSET:
        # nm,tr = STRICT (entailed). lvm.c:577-585 l_isfalse + register copy.
        return F({b}), F({a}), 0, 0, P, P, P, False
    if op in (Op.CALL, Op.TAILCALL):
        # nm,tr = STRICT (entailed). lvm.c:586-638 luaD_precall: the callee is
        # arbitrary Lua or C code, which no metamethod assumption constrains.
        # ARB at every mode.
        reads = F({a}) | (F(range(a + 1, a + b)) if b else F())
        if op is Op.TAILCALL:
            # writes_open is unconditional, unlike CALL's `c == 0` gate.
            # lvm.c:611 asserts `GETARG_C(i) - 1 == LUA_MULTRET` (C is always
            # 0), so there is no fixed-result form to gate on, and the PCRC
            # branch (lvm.c:630-632 -- the callee was a C function, already
            # run to completion by luaD_precall) falls through to the next
            # instruction with the callee's results sitting at R[a..top).
            # `luaD_precall` has THREE outcomes (ldo.h:32-34), and OP_TAILCALL
            # switches on all three -- an earlier revision of this comment
            # enumerated only two, which understated the case analysis even
            # though it did not change the grading. The other two both leave
            # this dispatch rather than falling through: PCRLUA (lvm.c:613-629)
            # replaces the frame and `goto reentry`s, and PCRYIELD arrives at
            # the `default:` arm (lvm.c:633-635), a bare `return` out of
            # luaV_execute because the C callee yielded (ldo.c:323). So exactly
            # one of the three continues to the next pc, and modelling the
            # union of the three means modelling that one's write.
            # `writes` stays empty because the region is top-relative (same
            # convention as CALL C==0 / VARARG B==0). M4 task 8.
            return reads, F(), b == 0, 1, ARB, ARB, ARB, True
        writes = F(range(a, a + c - 1)) if c else F()
        return reads, writes, b == 0, c == 0, ARB, ARB, ARB, True
    if op is Op.RETURN:
        # nm,tr = STRICT (entailed). lvm.c:639-653 moves values and pops the
        # frame; luaF_close touches the upvalue side channel, not a table, and
        # no TM is reachable.
        return (F(range(a, a + b - 1)) if b else F()), F(), b == 0, 0, P, P, P, False
    if op is Op.FORPREP:
        # nm,tr = STRICT (entailed). lvm.c:666-680: the three `tonumber`s are
        # luaV_tonumber (string->number parsing only, no TM), so this row is
        # already PURE at STRICT; may_error covers the three luaG_runerrors.
        return F({a, a + 1, a + 2}), F({a, a + 1, a + 2}), 0, 0, P, P, P, True
    if op is Op.FORLOOP:
        # may_error=True is a deliberate conservative over-approximation, not a claim
        # that lvm.c can raise here: OP_FORLOOP has no Protect() and calls no luaG_*
        # error function (FORPREP already validated the three slots are numbers, so
        # the arithmetic here cannot fail in practice). Kept True per spec so that no
        # downstream consumer (inlining gates, M4 effect-mode calibration) ever treats
        # FORLOOP as *proven* error-free; flip only with a matching lvm.c citation.
        #
        # nm,tr = STRICT (entailed). lvm.c:654-665 is pure float arithmetic on
        # three registers; no heap, no TM.
        return F({a, a + 1, a + 2}), F({a, a + 3}), 0, 0, P, P, P, True
    if op is Op.TFORLOOP:
        # nm,tr = STRICT (entailed). lvm.c:681-696 Protect(luaD_call(...)) --
        # the iterator is arbitrary code, same as CALL. ARB at every mode.
        return F({a, a + 1, a + 2}), F({a + 2}) | F(range(a + 3, a + 3 + c)), 0, 0, ARB, ARB, ARB, True
    if op is Op.CLOSE:
        # nm,tr = STRICT (entailed). lvm.c:719-722 luaF_close mutates the
        # open-upvalue side channel; no metatable is involved, so no mode
        # assumption can weaken it below WRITE_HEAP.
        return F(), F(), 0, 0, WH, WH, WH, False
    if op is Op.CLOSURE:
        # 捕获寄存器的 reads 由 lift 层从 MOVE 伪指令补齐（此处不可见后续指令字）
        # nm,tr = STRICT (entailed). lvm.c:723-742 allocates a closure and binds
        # upvalues; no TM path (see the GC finding in the block above).
        return F(), F({a}), 0, 0, P, P, P, False
    if op is Op.VARARG:
        # nm,tr = STRICT (entailed). lvm.c:743-761 copies from the frame's
        # vararg area into registers; no heap object, no TM.
        return F(), (F(range(a, a + b - 1)) if b else F()), 0, b == 0, P, P, P, False
    raise AssertionError(f"unhandled opcode {op!r}")


_MODE_COL = {EffectMode.STRICT: 4, EffectMode.NO_METAMETHOD: 5, EffectMode.TRUSTING: 6}


def analyze(ri: RawInstr, mode: EffectMode) -> InstrEffects:
    row = _row(ri)
    return InstrEffects(
        reads=row[0], writes=row[1],
        reads_open=bool(row[2]), writes_open=bool(row[3]),
        effect=row[_MODE_COL[mode]], may_error=row[7],
    )


def successors(ri: RawInstr, nups_of_closure: int | None = None) -> tuple[int, ...]:
    op, pc = ri.op, ri.pc
    if op in (Op.RETURN, Op.TAILCALL):
        return ()
    if op is Op.JMP or op is Op.FORPREP:
        return (pc + 1 + ri.sbx,)
    if op is Op.FORLOOP:
        return (pc + 1 + ri.sbx, pc + 1)
    if op in (Op.EQ, Op.LT, Op.LE, Op.TEST, Op.TESTSET, Op.TFORLOOP):
        return (pc + 1, pc + 2)
    if op is Op.LOADBOOL:
        return (pc + 2,) if ri.c else (pc + 1,)
    if op is Op.CLOSURE:
        if nups_of_closure is None:
            raise ValueError("successors(CLOSURE) requires nups_of_closure")
        return (pc + 1 + nups_of_closure,)
    if op is Op.SETLIST and ri.c == 0:
        return (pc + 2,)
    return (pc + 1,)


def extra_words(ri: RawInstr, nups_of_closure: int | None = None) -> int:
    if ri.op is Op.CLOSURE:
        if nups_of_closure is None:
            raise ValueError("extra_words(CLOSURE) requires nups_of_closure")
        return nups_of_closure
    if ri.op is Op.SETLIST and ri.c == 0:
        return 1
    return 0

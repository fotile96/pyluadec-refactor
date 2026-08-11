"""`OP_TAILCALL`'s open write region — the axiom row and its one live consumer.

## The axiom (`vendor/lua-5.1/src/lvm.c`, verified this session)

`case OP_TAILCALL` is `lvm.c:607-638`. Three lines matter:

  * `lvm.c:611` — `lua_assert(GETARG_C(i) - 1 == LUA_MULTRET);`. `C` is
    always 0, so the "C-1 results at `R[a..a+c-2]`" term that `OP_CALL`
    carries degenerates to nothing and the result region is open by
    construction, never fixed.
  * `lvm.c:612` — `luaD_precall(L, ra, LUA_MULTRET)`. The callee is called
    with `ra` as its function slot and an unbounded result count.
  * `lvm.c:630-632` — `case PCRC: { base = L->base; continue; }`. When the
    callee was a **C function**, `luaD_precall` has already run it to
    completion and left its results starting at `ra`, with `L->top` marking
    the end; `luaV_execute` simply carries on at the next instruction. So on
    that path `OP_TAILCALL` has written `R[a..top)` — an open region.
    (The other reachable path, `PCRLUA` at `lvm.c:613-629`, replaces the
    frame and `goto reentry`s, so it never returns to the next instruction
    at all; modelling the union of the two paths means modelling the write.)

`writes=∅, writes_open=0` — the row before M4 task 8 — is therefore an
under-approximation of the `PCRC` path. This module pins the corrected row
and the one place the correction is observable.

## What the corpus can and cannot say (differential run, M4 task 8)

The corpus contains exactly **3** `TAILCALL` occurrences, all in
`snr_common.lua` (re-derived this session; `docs/runbooks/m3-backlog.md` §4
carries the inlined script):

    snr_common.lua:main_26    TAILCALL@6  A=3 B=5 C=0  next=RETURN A=3 B=0 C=0
    snr_common.lua:main_29_0  TAILCALL@8  A=2 B=3 C=0  next=RETURN A=2 B=0 C=0
    snr_common.lua:main_29_0  TAILCALL@16 A=2 B=3 C=0  next=RETURN A=2 B=0 C=0

`classify_registers` was swept over all 1944 proto occurrences (1478 unique)
before and after the row change, recording `locals`/`temps`/`loop_vars`/
`temp_defs` and the per-proto certification verdict. **Result: 0 protos
changed, in any field, and 0 levels moved.** The committed ledger is
byte-identical.

That is not because the effect is nil — it is because of `_block_floor`.
`effects.successors(TAILCALL)` is `()`, so `build_cfg` always ends a basic
block at a `TAILCALL` and makes the next pc a leader. `_staging_slice` never
looks below the loop header's own block entry, so a `TAILCALL` can never lie
strictly between a staging producer and the header that consumes it in real
lifted code — the block floor rejects the producer first, and the open-write
barrier is never consulted. (The reason is *not* that a `TAILCALL` ends the
function: all 3 corpus occurrences are non-terminal, and an earlier revision
of the backlog that claimed otherwise was measured false.)

So the corpus arm below proves the shape of real `TAILCALL`s, and the
synthetic arm proves the row is load-bearing: it hands `classify_registers`
a `TAILCALL` that does *not* end its block — an LIR luac will not emit, the
same licence `tests/test_effects_emitter_consistency.py`'s operand grid uses
for the five opcodes the corpus lacks — and the verdict flips with the row.
"""
from __future__ import annotations

import pytest

from pyluadec.lift import (Effect, EffectMode, LirFunction, LirInstr, Op, analyze,
                           lift_proto)
from pyluadec.lift.opcodes import decode

from tests.synth import mk_instr, mk_proto


def test_tailcall_declares_an_open_write_region_for_every_operand_form():
    """`lvm.c:630-632` (PCRC) leaves results at `R[a..top)` whatever B and C are.

    Gridded over B and C rather than asserted once because the row is
    unconditional: unlike `OP_CALL`, whose open-result branch is gated on
    `C == 0`, `OP_TAILCALL` has no fixed-result form to gate on
    (`lvm.c:611` asserts C is always 0). A future edit that made
    `writes_open` conditional on `c == 0` would look right and would still
    be a narrower claim than lvm.c makes.

    `writes` stays empty: the region is `top`-relative, and `InstrEffects`
    only ever lists statically bounded registers there (same convention as
    `CALL` C==0 and `VARARG` B==0).
    """
    for b in (0, 1, 2, 3, 255):
        for c in (0, 1, 2):
            fx = analyze(mk_instr(Op.TAILCALL, a=2, b=b, c=c, pc=1),
                         EffectMode.STRICT)
            assert fx.writes_open, (b, c)
            assert fx.writes == frozenset(), (b, c)
            assert fx.reads_open is (b == 0), (b, c)


def test_open_write_barrier_refuses_a_staging_chain_across_a_tailcall():
    """The row's one live consumer: `open_write_pcs` in `classify_registers`.

    Shape (hand-built LIR, effects taken from the real `analyze()` so the
    assertion is sensitive to the axiom row and to nothing else):

        1 LOADK    R10 <- K0        |
        2 LOADK    R11 <- K0        |  staging for the `for` header
        3 LOADK    R12 <- K0        |
        4 TAILCALL A=0 B=1 C=0      <- successors forced to (5,), see below
        5 FORPREP  A=10
        6 MOVE     R14 <- R13       (body)
        7 FORLOOP  A=10
        8 RETURN

    `_staging_slice` walks back from the `FORPREP` looking for the producers
    of its control triple {10,11,12}. Without `writes_open` on the
    `TAILCALL` it walks straight through pc 4, attributes pcs 1-3, and
    `_control_lifetime_ok` grades 10/11/12 dedicated control slots -> temps.
    With the row corrected, pc 4 is an `R[a..top)` write standing between the
    producers and the consumer, so the slice refuses to attribute them and
    all three fall to `locals` — the barrier got stronger, which is the safe
    direction (a materialized local is always printable).

    The forced successors are the point of the fixture. Real lifted code
    cannot reach this: `effects.successors(TAILCALL) == ()` makes every
    `TAILCALL` end its basic block, and `_block_floor` then rejects any
    producer below it before the open-write barrier is consulted. That is
    why the 1944-proto differential moved nothing (module docstring) and why
    the corpus cannot stand in for this test.
    """
    from pyluadec.express.names import classify_registers

    plan = [
        (mk_instr(Op.LOADK, a=10, bx=0, pc=1), (2,)),
        (mk_instr(Op.LOADK, a=11, bx=0, pc=2), (3,)),
        (mk_instr(Op.LOADK, a=12, bx=0, pc=3), (4,)),
        (mk_instr(Op.TAILCALL, a=0, b=1, c=0, pc=4), (5,)),
        (mk_instr(Op.FORPREP, a=10, sbx=1, pc=5), (7,)),
        (mk_instr(Op.MOVE, a=14, b=13, pc=6), (7,)),
        (mk_instr(Op.FORLOOP, a=10, sbx=-2, pc=7), (6, 8)),
        (mk_instr(Op.RETURN, a=0, b=1, pc=8), ()),
    ]
    instrs = {
        ri.pc: LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT),
                        successors=succ, consumed=())
        for ri, succ in plan
    }
    proto = mk_proto((0,) * len(plan), constants=(1.0,), maxstacksize=16)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=len(plan),
                     captured_regs=frozenset(), closure_pseudo={})

    rc = classify_registers(fn)
    assert {10, 11, 12} <= rc.locals, sorted(rc.locals)
    assert not ({10, 11, 12} & rc.temps), sorted(rc.temps)


def test_effect_is_pure_bookkeeping_not_a_new_read(monkeypatch):
    """Neuter check for the assertion above (guard discipline).

    `classify_registers` consults `writes_open` in exactly one place. Forcing
    that lookup to `False` for `TAILCALL` — i.e. restoring the pre-M4-task-8
    row — must make the previous test's verdict flip back to `temps`,
    otherwise that test is passing for some other reason and proves nothing
    about the row.
    """
    from dataclasses import replace as _replace

    from pyluadec.express import names as names_mod
    from pyluadec.lift import effects as effects_mod

    real = effects_mod.analyze

    def neutered(ri, mode):
        fx = real(ri, mode)
        if ri.op is Op.TAILCALL:
            fx = _replace(fx, writes_open=False)
        return fx

    plan = [
        (mk_instr(Op.LOADK, a=10, bx=0, pc=1), (2,)),
        (mk_instr(Op.LOADK, a=11, bx=0, pc=2), (3,)),
        (mk_instr(Op.LOADK, a=12, bx=0, pc=3), (4,)),
        (mk_instr(Op.TAILCALL, a=0, b=1, c=0, pc=4), (5,)),
        (mk_instr(Op.FORPREP, a=10, sbx=1, pc=5), (7,)),
        (mk_instr(Op.MOVE, a=14, b=13, pc=6), (7,)),
        (mk_instr(Op.FORLOOP, a=10, sbx=-2, pc=7), (6, 8)),
        (mk_instr(Op.RETURN, a=0, b=1, pc=8), ()),
    ]
    instrs = {
        ri.pc: LirInstr(ri=ri, effects=neutered(ri, EffectMode.STRICT),
                        successors=succ, consumed=())
        for ri, succ in plan
    }
    proto = mk_proto((0,) * len(plan), constants=(1.0,), maxstacksize=16)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=len(plan),
                     captured_regs=frozenset(), closure_pseudo={})

    rc = names_mod.classify_registers(fn)
    assert {10, 11, 12} <= rc.temps, sorted(rc.temps)


@pytest.fixture(scope="module")
def corpus_tailcall_census(corpus_dir):
    """One decode pass over the whole corpus, shared by both corpus arms here.

    Both tests below need the same census (which protos contain a `TAILCALL`,
    and what surrounds each one) and each used to re-walk all 229 files for
    itself — the second one also lifting every one of the 1944 protos just to
    find the 2 that matter. Measured (M4 task 9): 0.95s for the pair before,
    0.26s after, on an otherwise unchanged pair of assertions. Same pattern as
    `test_effects_emitter_consistency.py::corpus_scan`; the standing directive
    is that a slow suite blocks development.
    """
    from pyluadec.ingest import load_file
    from pyluadec.pipeline import walk_proto_paths

    sites = []
    carriers = []
    protos_seen = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        protos: dict[str, object] = {}
        walk_proto_paths("main", load_file(f), protos)
        for path, p in protos.items():
            protos_seen += 1
            hit = False
            for i, w in enumerate(p.code):
                ri = decode(w, i + 1)
                if ri.op is not Op.TAILCALL:
                    continue
                hit = True
                nxt = decode(p.code[i + 1], i + 2) if i + 1 < len(p.code) else None
                sites.append((f.name, path, ri, nxt, len(p.code)))
            if hit:
                carriers.append((f.name, path, p))
    return {"sites": sites, "carriers": carriers, "protos": protos_seen}


def test_corpus_tailcalls_are_all_c_zero_and_followed_by_return_a_0(
        corpus_tailcall_census):
    """The corpus arm: what the 3 real `TAILCALL`s do and do not establish.

    Establishes (and re-derives, rather than trusting the backlog's table):
    every corpus `TAILCALL` has `C == 0` and is immediately followed by
    exactly one `RETURN A 0` with the same A — the `lparser.c:1251`
    (`retstat` -> `luaK_ret(fs, first, LUA_MULTRET)`) shape.

    Does NOT establish terminality: all 3 sit inside an `if` arm with more
    code after them, so `pc + 1 != len(code)` for every one. Pinned as an
    assertion because a previous revision of `m3-backlog.md` §4 claimed the
    opposite and the claim was load-bearing for an argument that the
    open-write barrier could never be reached.
    """
    found = corpus_tailcall_census["sites"]
    assert corpus_tailcall_census["protos"] == 1944, corpus_tailcall_census["protos"]
    assert len(found) == 3, [(f, p, ri.pc) for f, p, ri, _, _ in found]
    assert {f for f, _, _, _, _ in found} == {"snr_common.lua"}
    for _f, _path, ri, nxt, lastpc in found:
        assert ri.c == 0
        assert nxt is not None and nxt.op is Op.RETURN
        assert (nxt.a, nxt.b, nxt.c) == (ri.a, 0, 0)
        assert ri.pc + 1 != lastpc, "terminality is NOT a property of TAILCALL"


def test_corpus_lifted_tailcalls_all_end_their_basic_block(corpus_tailcall_census):
    """Why the differential moved nothing — asserted, not argued.

    `_staging_slice`'s open-write barrier only fires for an open write lying
    strictly between a staging producer and the loop header that consumes it,
    and it never looks below the header's own basic-block entry. A
    `TAILCALL` whose successor set is empty always terminates its block, so
    it can never occupy that window. This pins the premise over the real
    corpus so that a lift-layer change which gave `TAILCALL` a fall-through
    successor would fail here rather than silently re-open the question.

    Lifts only the protos the census found a `TAILCALL` in, rather than all
    1944 and then discarding 1942 of them (M4 task 9). The assertions are
    unchanged: they only ever ran on tailcall-carrying protos, and the census
    that selects them decodes the *same* whole corpus this used to lift.
    """
    from pyluadec.cfg import build_cfg

    n = 0
    for fname, _path, p in corpus_tailcall_census["carriers"]:
        fn = lift_proto(p)
        cfg = build_cfg(fn)
        for blk in cfg.blocks.values():
            for li in blk.instrs[:-1]:
                assert li.ri.op is not Op.TAILCALL, (fname, li.ri.pc)
        for li in fn.instrs.values():
            if li.ri.op is Op.TAILCALL:
                assert li.successors == (), (fname, li.ri.pc)
                n += 1
    assert n == 3, n


@pytest.mark.parametrize("op", [Op.CALL, Op.VARARG])
def test_other_open_write_rows_are_unchanged(op):
    """Regression fence: the fix is `TAILCALL`-only.

    `CALL` keeps its `C == 0` gate and `VARARG` its `B == 0` gate; both have
    a fixed-result form that must NOT be declared open, or every call in the
    corpus becomes a staging barrier.
    """
    fixed = mk_instr(op, a=2, b=2, c=2, pc=1)
    assert not analyze(fixed, EffectMode.STRICT).writes_open
    open_form = (mk_instr(Op.CALL, a=2, b=1, c=0, pc=1) if op is Op.CALL
                 else mk_instr(Op.VARARG, a=2, b=0, pc=1))
    assert analyze(open_form, EffectMode.STRICT).writes_open
    assert analyze(fixed, EffectMode.STRICT).effect in (Effect.PURE, Effect.ARBITRARY)

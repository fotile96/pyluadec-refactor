def test_claimed_pcs_disjoint_union():
    from pyluadec.sir.regions import Straight, Seq, all_claimed
    from tests.synth import mk_instr
    from pyluadec.lift import LirInstr
    from pyluadec.lift.effects import analyze, EffectMode
    def li(pc):
        ri = mk_instr(0, pc=pc)   # MOVE
        return LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT),
                        successors=(pc+1,), consumed=())
    seq = Seq(body=(Straight((li(1), li(2)), frozenset({1, 2})),
                    Straight((li(3),), frozenset({3}))), claimed_pcs=frozenset())
    assert all_claimed(seq) == frozenset({1, 2, 3})


def test_overlap_is_hard_fail():
    import pytest
    from pyluadec.sir.regions import Straight, Seq, all_claimed, RegionOverlap
    from tests.synth import mk_instr
    from pyluadec.lift import LirInstr
    from pyluadec.lift.effects import analyze, EffectMode
    def li(pc):
        ri = mk_instr(0, pc=pc)
        return LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT), successors=(pc+1,), consumed=())
    bad = Seq(body=(Straight((li(1),), frozenset({1})),
                    Straight((li(1),), frozenset({1}))), claimed_pcs=frozenset())
    with pytest.raises(RegionOverlap):
        all_claimed(bad)


def test_synth_mk_instr_roundtrips_fields():
    from tests.synth import mk_instr
    from pyluadec.lift import Op
    ri = mk_instr(Op.LOADK, a=2, bx=5, pc=7)
    assert ri.op is Op.LOADK and ri.a == 2 and ri.bx == 5 and ri.pc == 7
    ri = mk_instr(Op.JMP, sbx=-3, pc=10)
    assert ri.op is Op.JMP and ri.sbx == -3


def test_if_region_claims_then_and_else_children():
    # Regression guard for the pc-claim audit: If has two child regions
    # (then_body, else_body). A recursion bug that visits only one of them
    # must show up as missing pcs here, not as a silent pass.
    from pyluadec.sir.regions import Straight, If, all_claimed
    from tests.synth import mk_instr
    from pyluadec.lift import LirInstr, Op
    from pyluadec.lift.effects import analyze, EffectMode
    def li(pc, op=Op.MOVE):
        ri = mk_instr(op, pc=pc)
        return LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT),
                        successors=(pc+1,), consumed=())
    node = If(cond=li(1, Op.EQ), negated=False,
              then_body=Straight((li(3),), frozenset({3})),
              else_body=Straight((li(4),), frozenset({4})),
              join_pc=5, claimed_pcs=frozenset({1, 2}))
    assert all_claimed(node) == frozenset({1, 2, 3, 4})


def test_synth_mk_proto_lifts():
    from tests.synth import mk_proto, mk_instr
    from pyluadec.lift import lift_proto, Op
    # RETURN 0 1  (return with no values) — a valid 1-instruction proto
    p = mk_proto([mk_instr(Op.RETURN, a=0, b=1).word])
    fn = lift_proto(p)
    assert fn.n_pcs == 1 and fn.instrs[1].ri.op is Op.RETURN

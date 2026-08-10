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


def test_numeric_for_region_claims_body_children():
    # Same gap class as If.else_body: NumericFor.body is a child region whose
    # pcs must be recursed into. Nothing else in the suite constructs a
    # NumericFor, so without this test a dropped `_CHILDREN[NumericFor]`
    # entry silently loses an entire loop body's pcs from the audit.
    from pyluadec.sir.regions import Straight, NumericFor, all_claimed
    from tests.synth import mk_instr
    from pyluadec.lift import LirInstr, Op
    from pyluadec.lift.effects import analyze, EffectMode
    def li(pc, op=Op.MOVE):
        ri = mk_instr(op, pc=pc)
        return LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT),
                        successors=(pc+1,), consumed=())
    node = NumericFor(prep=li(1, Op.FORPREP), loop=li(5, Op.FORLOOP),
                       body=Straight((li(2), li(3), li(4)), frozenset({2, 3, 4})),
                       claimed_pcs=frozenset({1, 5}))
    assert all_claimed(node) == frozenset({1, 2, 3, 4, 5})


def test_generic_for_region_claims_body_children():
    # Same gap class as NumericFor above, for the other loop-region kind.
    from pyluadec.sir.regions import Straight, GenericFor, all_claimed
    from tests.synth import mk_instr
    from pyluadec.lift import LirInstr, Op
    from pyluadec.lift.effects import analyze, EffectMode
    def li(pc, op=Op.MOVE):
        ri = mk_instr(op, pc=pc)
        return LirInstr(ri=ri, effects=analyze(ri, EffectMode.STRICT),
                        successors=(pc+1,), consumed=())
    node = GenericFor(call=li(5, Op.TFORLOOP), loop=li(6, Op.JMP),
                       body=Straight((li(2), li(3), li(4)), frozenset({2, 3, 4})),
                       claimed_pcs=frozenset({5, 6}))
    assert all_claimed(node) == frozenset({2, 3, 4, 5, 6})


def test_children_dispatch_is_complete_for_region_kinds_with_child_fields():
    # Structural completeness check, not per-kind coverage: any region
    # dataclass with a field annotated as `Region`/`Region | None`/
    # `tuple[Region, ...]` must have a `_CHILDREN` entry, or a future region
    # kind (M4) added without wiring `_CHILDREN` would silently drop its
    # children from the audit the same way If.else_body / NumericFor.body /
    # GenericFor.body did before an earlier fix round. The set of classes to
    # check is read off `Region.__args__` (the `Region = A | B | ...` type
    # alias's own members), not a hand-maintained list, so a ninth region
    # kind added to the union in M4 is picked up automatically instead of
    # requiring someone to remember to add it here too. The child-bearing
    # *predicate* is likewise derived from each class's dataclass fields.
    import dataclasses
    from pyluadec.sir import regions
    all_region_classes = list(regions.Region.__args__)
    # Guard against Region.__args__ silently degrading to something with no
    # members (e.g. Region reassigned to a single class, or a TypeAlias form
    # that erases __args__) — that would make the loop below iterate zero
    # times and pass vacuously, hiding the exact failure this test exists to
    # catch. Fixed at today's 8 kinds so growing the union (M4) doesn't need
    # this bound raised, but shrinking below it fails loudly.
    assert len(all_region_classes) >= 8, (
        f"expected at least 8 region kinds in Region.__args__, "
        f"got {len(all_region_classes)}: {all_region_classes}")
    for cls in all_region_classes:
        has_child_field = any(
            "Region" in (f.type if isinstance(f.type, str) else str(f.type))
            for f in dataclasses.fields(cls)
        )
        if has_child_field:
            assert cls in regions._CHILDREN, (
                f"{cls.__name__} has a Region-typed field but no _CHILDREN entry")
        else:
            assert cls not in regions._CHILDREN, (
                f"{cls.__name__} has no Region-typed field but has a _CHILDREN entry")


def test_synth_mk_proto_lifts():
    from tests.synth import mk_proto, mk_instr
    from pyluadec.lift import lift_proto, Op
    # RETURN 0 1  (return with no values) — a valid 1-instruction proto
    p = mk_proto([mk_instr(Op.RETURN, a=0, b=1).word])
    fn = lift_proto(p)
    assert fn.n_pcs == 1 and fn.instrs[1].ri.op is Op.RETURN

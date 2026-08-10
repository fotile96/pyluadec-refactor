import subprocess
from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"


def _fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return lift_proto(load_file(o))


def _claims_all(region, fn):
    from pyluadec.sir import all_claimed
    return all_claimed(region) == set(fn.instrs)


def test_straight_line_is_seq_of_straight(tmp_path):
    from pyluadec.sir import Seq, Straight
    from pyluadec.sir.build import build_sir
    fn = _fn("local a = 1 local b = 2 return a + b", tmp_path)
    r = build_sir(fn)
    assert _claims_all(r, fn)
    # a straight-line function is a Straight (or Seq of Straights), never an If
    from pyluadec.sir import If, NumericFor
    def has(kind, node):
        if isinstance(node, kind): return True
        for c in getattr(node, "body", ()) or ():
            if has(kind, c): return True
        return False
    assert not has(If, r) and not has(NumericFor, r)


def test_if_then_end_is_if_without_else(tmp_path):
    from pyluadec.sir import If
    from pyluadec.sir.build import build_sir
    fn = _fn("local a = tonumber('1') if a then print('y') end return a", tmp_path)
    r = build_sir(fn)
    assert _claims_all(r, fn)
    ifs = _find(r, If)
    assert ifs and ifs[0].else_body is None


def test_if_else_is_if_with_else(tmp_path):
    from pyluadec.sir import If
    from pyluadec.sir.build import build_sir
    fn = _fn("local a = tonumber('1') if a < 3 then print('s') else print('b') end", tmp_path)
    r = build_sir(fn)
    assert _claims_all(r, fn)
    ifs = _find(r, If)
    assert ifs and ifs[0].else_body is not None


def test_straight_line_with_closure_is_accepted(tmp_path):
    # Regression guard for the pc+1-vs-pc+1+len(consumed) fallthrough bug: a
    # CLOSURE instruction swallows a trailing MOVE/GETUPVAL pseudo-word per
    # captured upvalue, so its real successor is pc+1+nups, not pc+1. This
    # function is otherwise pure straight-line code (no branches) -- if the
    # straight-run accumulator instead assumed plain pc+1 fallthrough, the
    # CLOSURE would look like an unrecognized transfer and the whole function
    # would wrongly fall back with StructureError instead of being accepted.
    from pyluadec.sir import Straight, Seq
    from pyluadec.sir.build import build_sir
    fn = _fn("local x = 1\nlocal function f() return x end\nreturn f\n", tmp_path)
    from pyluadec.lift import Op
    assert any(li.ri.op is Op.CLOSURE and len(li.consumed) > 0
               for li in fn.instrs.values()), "fixture must actually exercise a closure"
    r = build_sir(fn)  # must not raise StructureError
    assert _claims_all(r, fn)
    assert isinstance(r, (Straight, Seq))


def test_build_sir_audit_catches_unclaimed_pcs_from_a_buggy_recognizer(tmp_path, monkeypatch):
    # The pc-claim audit at build_sir's exit (claimed == set(fn.instrs)) is the
    # last line of defense against a recognizer bug that silently drops a pc
    # from its claim without any overlap (all_claimed's RegionOverlap check
    # alone would miss this -- a strict subset of the pcs is still disjoint).
    # None of our real fixtures happen to trigger such a gap today, so this
    # test forces the case by monkeypatching _structure_range to return a
    # region that under-claims by one pc, and asserts build_sir still refuses
    # rather than silently returning a bad tree.
    import pytest
    from pyluadec.sir import Straight
    from pyluadec.sir.build import StructureError, build_sir
    import pyluadec.sir.build as build_mod
    fn = _fn("local a = 1 local b = 2 return a + b", tmp_path)
    all_pcs = sorted(fn.instrs)
    short = frozenset(all_pcs[:-1])  # drop the last pc -- no overlap, just a gap

    def _fake_structure_range(fn_, cfg, idoms, lo, hi):
        return Straight(tuple(fn_.instrs[pc] for pc in sorted(short)), short)

    monkeypatch.setattr(build_mod, "_structure_range", _fake_structure_range)
    with pytest.raises(StructureError):
        build_sir(fn)


def test_compare_not_followed_by_jmp_raises():
    # luac always emits a JMP right after EQ/LT/LE/TEST -- real corpus/compiler
    # output can't exercise the violation path. Build the shape by hand with
    # the synth fixtures (per the brief: "hand-built Proto/RawInstr fixtures
    # for shapes luac won't emit") to prove _structure_if actually checks this
    # rather than assuming it, per the brief's explicit "verify rather than
    # assume" instruction for this invariant.
    from tests.synth import mk_instr, mk_proto
    from pyluadec.lift import lift_proto, Op
    from pyluadec.sir.build import StructureError, build_sir
    # pc1: LT 0 0 1 (compare)   pc2: MOVE 0 1 (NOT a JMP)   pc3: RETURN 0 1
    words = [
        mk_instr(Op.LT, a=0, b=0, c=1, pc=1).word,
        mk_instr(Op.MOVE, a=0, b=1, pc=2).word,
        mk_instr(Op.RETURN, a=0, b=1, pc=3).word,
    ]
    fn = lift_proto(mk_proto(words, maxstacksize=2))
    import pytest
    with pytest.raises(StructureError):
        build_sir(fn)


def test_loop_raises_structure_error(tmp_path):
    import pytest
    from pyluadec.sir.build import StructureError, build_sir
    fn = _fn("local i = 0 while i < 3 do i = i + 1 end return i", tmp_path)
    with pytest.raises(StructureError):
        build_sir(fn)


def test_acyclic_corpus_claims_every_pc(corpus_dir):
    """Every acyclic proto that build_sir accepts must claim exactly its pc set."""
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    from pyluadec.sir import all_claimed
    from pyluadec.sir.build import StructureError, build_sir, has_back_edge
    accepted = rejected = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            fn = lift_proto(p)
            if has_back_edge(fn):
                continue                      # loops are Task 3
            try:
                r = build_sir(fn)
            except StructureError:
                rejected += 1
                continue
            assert all_claimed(r) == set(fn.instrs), f.name
            accepted += 1
    assert accepted > 500        # straight+acyclic acceptance is the bulk of the corpus


def _find(region, kind):
    out = []
    def walk(n):
        if isinstance(n, kind): out.append(n)
        for c in getattr(n, "body", ()) or ():
            walk(c)
        for attr in ("then_body", "else_body"):
            c = getattr(n, attr, None)
            if c is not None: walk(c)
    walk(region)
    return out

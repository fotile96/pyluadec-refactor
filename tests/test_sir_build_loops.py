import subprocess
from pathlib import Path
import pytest

BUILD = Path(__file__).resolve().parents[1] / "build"


def _fn(src: str, tmp: Path):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto
    s = tmp / "t.lua"; o = tmp / "o"
    s.write_text(src)
    subprocess.run([str(BUILD / "luac_sz4"), "-o", str(o), str(s)], check=True)
    return lift_proto(load_file(o))


def _find(region, kind):
    # NOTE: NumericFor.body / GenericFor.body are single Region objects, not
    # tuples (only Seq.body is a tuple) -- treating "body" as always-iterable
    # (as an earlier draft of this helper did, mirroring the brief's own
    # skeleton) throws TypeError on the very NumericFor/GenericFor nodes this
    # helper exists to find. Walk Seq.body as a tuple; walk every other
    # `body`/`then_body`/`else_body` attribute as a single child.
    out = []
    def walk(n):
        if n is None:
            return
        if isinstance(n, kind):
            out.append(n)
        b = getattr(n, "body", None)
        if isinstance(b, tuple):
            for c in b:
                walk(c)
        elif b is not None:
            walk(b)
        for a in ("then_body", "else_body"):
            c = getattr(n, a, None)
            if c is not None:
                walk(c)
    walk(region)
    return out


def test_numeric_for(tmp_path):
    from pyluadec.sir import NumericFor, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("local s = 0 for i = 1, 10 do s = s + i end return s", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, NumericFor)


def test_generic_for(tmp_path):
    from pyluadec.sir import GenericFor, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("local t = {1, 2} for i, v in ipairs(t) do print(i, v) end", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, GenericFor)


def test_break_in_for(tmp_path):
    from pyluadec.sir import Break, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("for i = 1, 10 do if i == 5 then break end print(i) end", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, Break)


def test_while_is_recognized(tmp_path):
    """INVERTED IN M4 TASK 3 (was `test_while_still_raises`). `while <cond>`
    is a real region node now; see tests/test_sir_loops_longtail.py for the
    shape fixtures and tests/test_emit_while.py for the L3 adjudication."""
    from pyluadec.sir import While, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("local i = 0 while i < 3 do i = i + 1 end return i", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, While)


def test_repeat_is_recognized(tmp_path):
    """INVERTED IN M4 TASK 3 (was `test_repeat_still_raises`)."""
    from pyluadec.sir import Repeat, all_claimed
    from pyluadec.sir.build import build_sir
    fn = _fn("local i = 0 repeat i = i + 1 until i >= 3 return i", tmp_path)
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)
    assert _find(r, Repeat)


def test_testset_still_raises(tmp_path):
    """The remaining acyclic refusal family, kept as the "build_sir really
    does still refuse things" anchor the two tests above used to be.
    EXPIRY: M4 task 4 reconstructs TESTSET."""
    from pyluadec.sir.build import StructureError, build_sir
    fn = _fn("local a, b local x = a or b return x", tmp_path)
    with pytest.raises(StructureError, match="TESTSET"):
        build_sir(fn)


def test_dead_code_inside_a_numeric_for_body_raises():
    # A for body is a region entered only through the loop header (FORPREP ->
    # FORLOOP -> back-edge), exactly like an if/else branch body is entered
    # only through its condition -- so it deserves the same
    # _verify_single_entry dominance check that
    # test_dead_code_inside_a_claimed_then_range_raises (test_sir_build_acyclic.py)
    # exercises for If. This constructs the analogous shape by hand (luac
    # would never emit unreachable code): FORPREP at pc1 jumps to FORLOOP at
    # pc5, so the body interval is [2, 5). pc2 (the body head, reachable only
    # via FORLOOP's back edge) is a RETURN -- terminal, no successors -- so
    # pc3/pc4 are never actually reachable from pc2 onward and are absent
    # from the CFG's dominator tree entirely, even though the pc interval
    # [2, 5) is gap-free and contiguous. Confirmed both directions while
    # writing this test: raises with the check in _structure_numeric_for
    # present, does not raise with it commented out.
    from tests.synth import mk_instr, mk_proto
    from pyluadec.lift import lift_proto, Op
    from pyluadec.sir.build import StructureError, build_sir
    words = [
        mk_instr(Op.FORPREP, a=0, sbx=3, pc=1).word,   # -> loop_pc=5
        mk_instr(Op.RETURN, a=0, b=1, pc=2).word,        # body head (reachable only via back-edge)
        mk_instr(Op.MOVE, a=0, b=1, pc=3).word,          # unreachable from pc2 onward
        mk_instr(Op.MOVE, a=0, b=1, pc=4).word,
        mk_instr(Op.FORLOOP, a=0, sbx=-4, pc=5).word,    # -> body_lo=2 / fall-through=6
        mk_instr(Op.RETURN, a=0, b=1, pc=6).word,        # after the loop
    ]
    fn = lift_proto(mk_proto(words, maxstacksize=4))
    with pytest.raises(StructureError):
        build_sir(fn)


def test_dead_code_inside_a_generic_for_body_raises():
    # Same argument as test_dead_code_inside_a_numeric_for_body_raises, but
    # for GenericFor: the body's sole external entry is the leading JMP
    # (lead_pc -> tf_pc); the body itself is only ever reached via the
    # back-edge JMP after tf_pc, never directly from lead_pc. Shape: lead JMP
    # at pc1 -> TFORLOOP at pc5, so body_lo=2; pc2 is a RETURN cutting the
    # chain, leaving pc3/pc4 unreachable inside the contiguous [2, 5)
    # interval. Confirmed both directions: raises with the
    # _verify_single_entry call present in _structure_generic_for, does not
    # raise with it commented out.
    from tests.synth import mk_instr, mk_proto
    from pyluadec.lift import lift_proto, Op
    from pyluadec.sir.build import StructureError, build_sir
    words = [
        mk_instr(Op.JMP, sbx=3, pc=1).word,              # -> tf_pc=5
        mk_instr(Op.RETURN, a=0, b=1, pc=2).word,         # body head (reachable only via back-edge)
        mk_instr(Op.MOVE, a=0, b=1, pc=3).word,           # unreachable from pc2 onward
        mk_instr(Op.MOVE, a=0, b=1, pc=4).word,
        mk_instr(Op.TFORLOOP, a=0, c=1, pc=5).word,
        mk_instr(Op.JMP, sbx=-5, pc=6).word,              # -> body_lo=2
        mk_instr(Op.RETURN, a=0, b=1, pc=7).word,         # after the loop
    ]
    fn = lift_proto(mk_proto(words, maxstacksize=4))
    with pytest.raises(StructureError):
        build_sir(fn)


def test_for_corpus_claims_every_pc(corpus_dir):
    from pyluadec.ingest import load_file
    from pyluadec.lift import lift_proto, Op
    from pyluadec.sir import all_claimed
    from pyluadec.sir.build import StructureError, build_sir
    accepted_with_loop = 0
    for f in sorted(corpus_dir.glob("*.lua")):
        stack = [load_file(f)]
        while stack:
            p = stack.pop(); stack.extend(p.subprotos)
            fn = lift_proto(p)
            has_for = any(li.ri.op in (Op.FORLOOP, Op.TFORLOOP) for li in fn.instrs.values())
            try:
                r = build_sir(fn)
            except StructureError:
                continue
            assert all_claimed(r) == set(fn.instrs), f.name
            if has_for:
                accepted_with_loop += 1
    assert accepted_with_loop > 20      # for-loops are ~43 unique protos; many recur

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


def test_reassigned_register_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    # 'a' is written twice (a=1; a=a+1) → its register is a local, not a temp
    fn = _fn("local a = 1 a = a + 1 print(a)", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps


def test_call_arg_staging_is_temp(tmp_path):
    from pyluadec.express.names import classify_registers
    # string.format('%d', 42): the GETGLOBAL/GETTABLE/LOADK staging registers feed
    # straight into the CALL — single def, adjacent single use → temp (inlined)
    fn = _fn("print(string.format('%d', 42))", tmp_path)
    rc = classify_registers(fn)
    assert rc.temps                      # at least the format-string/arg staging inlines


def test_parameter_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    fn = _fn("local function f(x, y) return x + y end return f", tmp_path)
    inner = fn.proto.subprotos[0]
    from pyluadec.lift import lift_proto
    rc = classify_registers(lift_proto(inner))
    assert 0 in rc.locals and 1 in rc.locals     # both params are locals


def test_captured_register_is_local(tmp_path):
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import lift_proto
    root = _fn("local n = 0 local f = function() return n end return f()", tmp_path)
    rc = classify_registers(root)
    # n's register is captured by the closure → local
    assert root.captured_regs
    assert root.captured_regs <= rc.locals


def test_name_for_is_valid_identifier():
    from pyluadec.express.names import name_for
    from pyluadec.lift import LUA_KEYWORDS
    n = name_for(3, depth=1)
    assert n.isidentifier() and n not in LUA_KEYWORDS and not n.startswith("__pld_")
    assert name_for(3, 1) != name_for(3, 2)      # depth disambiguates across protos


def test_multiply_written_dead_write_is_still_local(tmp_path):
    """Isolates the def-count rule from the use-count rule.

    'local a = 1 a = 2 local b = a': the first write to a's register is dead
    (overwritten before any read), so there is exactly one *use* (the final
    read feeding b) with nothing writing that use's inputs in between -- the
    def/use pair alone would look "adjacent pure" and inline as a temp. Only
    the def-count check (2 writes) forces it local. This is the register.py
    docs example that test_reassigned_register_is_local does not actually
    isolate: that test's register also fails the use-count check (its 'a' is
    read twice: once by the ADD that recomputes it, once by print), so it
    would still classify as local even if the def-count check were deleted.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("local a = 1 a = 2 local b = a", tmp_path)
    rc = classify_registers(fn)
    assert 0 in rc.locals and 0 not in rc.temps


def test_numeric_for_control_slots_are_temp_and_loop_var_is_local(tmp_path):
    """'for i=1,3 do print(i) end': FORPREP/FORLOOP control slots R(A..A+2)
    must be temps (they're consumed by the for-header, not real locals) and
    the visible loop variable R(A+3) must be local and recorded in loop_vars.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("for i=1,3 do print(i) end", tmp_path)
    rc = classify_registers(fn)
    assert {0, 1, 2} <= rc.temps
    assert 3 in rc.locals and 3 in rc.loop_vars
    assert not ({0, 1, 2} & rc.locals)


def test_generic_for_control_slots_are_temp_and_loop_vars_are_local(tmp_path):
    """'for k,v in pairs(t) do end': TFORLOOP control slots R(A..A+2) must be
    temps and the visible loop variables R(A+3..A+2+C) must be local and
    recorded in loop_vars.
    """
    from pyluadec.express.names import classify_registers
    fn = _fn("local t = {} for k, v in pairs(t) do print(k, v) end", tmp_path)
    rc = classify_registers(fn)
    assert {1, 2, 3} <= rc.temps
    assert {4, 5} <= rc.locals
    assert {4, 5} <= rc.loop_vars
    assert not ({1, 2, 3} & rc.locals)


def test_adjacent_pure_blocks_inlining_across_may_error_pure_instruction():
    """_adjacent_pure's may_error term, isolated from its effect-level term.

    FORPREP/FORLOOP are the only opcodes that are PURE at every EffectMode
    yet may_error=True (see lift/effects.py's FORLOOP comment) -- so they are
    the only way to build a def/use pair whose intervening instruction is
    blocked *solely* by the may_error check, never by the effect>=WRITE_HEAP
    check. This hand-built shape (real luac never stages a temp's def and use
    across a for-loop header) isolates exactly that: register 5 has one def,
    one use, and nothing writes its (empty) input set in between -- only
    may_error keeps it out of temps.
    """
    from pyluadec.express.names import classify_registers
    from pyluadec.lift import Effect, InstrEffects, LirFunction, LirInstr, Op
    from tests.synth import mk_instr, mk_proto

    def_ri = mk_instr(Op.LOADK, a=5, bx=0, pc=1)
    def_fx = InstrEffects(reads=frozenset(), writes=frozenset({5}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    forprep_ri = mk_instr(Op.FORPREP, a=10, sbx=1, pc=2)
    forprep_fx = InstrEffects(reads=frozenset({10, 11, 12}), writes=frozenset({10, 11, 12}),
                               reads_open=False, writes_open=False,
                               effect=Effect.PURE, may_error=True)
    use_ri = mk_instr(Op.MOVE, a=6, b=5, pc=3)
    use_fx = InstrEffects(reads=frozenset({5}), writes=frozenset({6}),
                           reads_open=False, writes_open=False,
                           effect=Effect.PURE, may_error=False)
    instrs = {
        1: LirInstr(ri=def_ri, effects=def_fx, successors=(2,), consumed=()),
        2: LirInstr(ri=forprep_ri, effects=forprep_fx, successors=(3,), consumed=()),
        3: LirInstr(ri=use_ri, effects=use_fx, successors=(), consumed=()),
    }
    proto = mk_proto((0, 0, 0), numparams=0, maxstacksize=16)
    fn = LirFunction(proto=proto, instrs=instrs, n_pcs=3,
                      captured_regs=frozenset(), closure_pseudo={})
    rc = classify_registers(fn)
    assert 5 in rc.locals and 5 not in rc.temps

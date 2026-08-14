"""M6 task 12: a table constructor's own field stores are not *reads* of the
table.

The property under test, stated once:

    `lparser.c`'s `constructor` keeps the table on the expression stack for
    the whole literal. `recfield`/`closelistfield` push the key and value,
    emit `OP_SETTABLE`/`OP_SETLIST`, and then restore `fs->freereg = reg`
    -- the slot *above* the table (`lparser.c:596`, `:632`). The table's own
    register is never freed by a field store, so a field store is not the
    consuming read that ends a staged value's life; it is bookkeeping inside
    one still-unfinished expression.

`express/freereg.py::stack_discipline` already models half of this: `SETTABLE`/
`SETLIST` `pop_ge(a + 1)` so "the table itself stays pending". The read half
was missing, so every field store counted as one more read of the table
register, and the pop-once rule (`n_reads == 1`) then graded any constructor
with a field a *local*.

Two faces, both measured on the corpus at this task's BASE (`7d36e2d`) and
both reproduced by one-line fixtures here:

  * **stack inflation** -- `f({x = 1})` printed `local l0_1 = {x = 1} f(l0_1)`,
    which recompiles with one more stack slot than luac used
    (`mismatch: maxstacksize`).
  * **constructor aliasing** -- `local t = {a = {..}, b = {..}}` printed
    `local l0_1 = {..}` then `l0_1 = {..}` then
    `local l0_0 = {a = l0_1, b = l0_1}`. Once the first inner constructor is
    materialized, `Reconstructor.write_reg`'s `reg not in self.declared` gate
    turns every later constructor in that slot into a *reassignment*, and the
    outer table's fields all alias the last one. Four distinct tables
    collapsed into one at `snr_graphic.lua:main`; the same shape was
    adjudicated at `snr_music.lua:main` in M5. **This is a genuinely different
    program**, not merely an unfaithful rendering -- which is why the
    `run_bytes` diff below is asserted, not just certification.

The discriminator is the pending definition's own opcode: only a register
whose most recent push was `OP_NEWTABLE` gets the exemption, because only a
constructor's field stores behave this way. `a().b = 1` is an *assignment
statement* whose target expression `a()` really is consumed by its `SETTABLE`,
and `NOT_A_CONSTRUCTOR_CASES` pins that it stays consumed.

Every fixture is oracle-compiled with the real `luac_sz4` and adjudicated by
`certify_proto`, which recompiles the printed source and compares field by
field under the normalization ladder. Nothing here relaxes the gate.

All fixture sources are pure ASCII by construction, so assertions that inspect
printed text may decode; bytecode-derived strings elsewhere stay `bytes`.
"""
import dataclasses

import pytest

from pyluadec.emit import lua as _lua
from pyluadec.emit.lua import print_chunk
from pyluadec.express import freereg, names
from pyluadec.express.names import classify_registers
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.lift.opcodes import Op
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.structure.structured import certify_proto
from pyluadec.verify.certify import certify_l3

# --- the minimal repro -----------------------------------------------------
# One line, two inner constructors in the same slot. This is the reduction of
# `snr_graphic.lua:main` (eight inner tables, `code` 385 -> 650) and of the
# `snr_music.lua:main` case adjudicated in M5.
ALIASING_EXEMPLAR = b"local t = {a = {x = 1, y = 2}, b = {p = 3, q = 4}}\n" \
                    b"print(t.a.x, t.b.p)\n"

# Sources that must certify `L3` AND run identically to their own bytecode.
# The stdout half is what separates "unfaithful" from "wrong": under the
# aliasing defect `print(t.a.x, t.b.p)` prints `3 3` instead of `1 3`.
CONSTRUCTOR_CASES = [
    # The exemplar itself.
    ALIASING_EXEMPLAR,
    # The same collapse with array parts (SETLIST rather than SETTABLE).
    b"local t = {{1, 2}, {3, 4}} print(t[1][1], t[2][1])",
    # Mixed: a hash field whose value is an array-part constructor.
    b"local t = {a = {1, 2}, b = {3, 4}} print(t.a[1], t.b[1])",
    # The stack-inflation face, at its minimum: ONE field store is enough,
    # because the consuming read (here the `SETGLOBAL`) is then the second.
    b"g = {x = 1} print(g.x)",
    # ... and as a call argument, the shape `f({x = 1})`.
    b"local function f(u) print(u.x) end f({x = 1})",
    # An empty constructor already certified at BASE (no field store, so
    # `n_reads` was 1); kept so a change that starts *over*-counting is
    # visible from this file too.
    b"local function f(u) print(type(u)) end f({})",
    # Three levels of nesting in three different slots.
    b"local t = {a = {b = {c = 7}}} print(t.a.b.c)",
    # The `snr_graphic` shape reduced: several inner tables of differing
    # sizes, including empty ones, all reusing the same slot.
    # (`type(...)` rather than the tables themselves: a printed table is its
    # address, which differs between the two runs of the stdout diff below.)
    b"local T = {A = {a = 1, b = 2, c = 3}, B = {d = 4}, C = {}, D = {}}"
    b" print(T.A.a, T.B.d, type(T.C), type(T.D))",
]

# The other direction: a `SETTABLE` whose table register was NOT pushed by a
# `NEWTABLE` is an ordinary assignment statement, and its read really does
# consume the staged value. Exempting it would materialize `a().b = 1` as
# `local l0_0 = a() l0_0.b = 1`, losing an `L3` that holds at BASE.
NOT_A_CONSTRUCTOR_CASES = [
    b"function a() return {} end a().b = 1 print('ok')",
    b"function a() return {} end a().b = 1 a().c = 2 print('ok')",
    b"local u = {v = {}} u.v.w = 1 print(u.v.w)",
]

# A DYNAMIC-key constructor. `_fold_settable` has no register-key form
# (`_dispatch` folds only `isk(ri.b)`), so the reconstructor materializes the
# table and emits one `t[k] = v` statement per field -- each of which really
# does read it. `config.lua`'s main chunk is this shape twelve times over;
# exempting these reads told the classifier the table was a pop-once
# temporary, and the reconstructor then popped it at the first field and
# raised `register 0 is read again after its staged value was consumed` at the
# second -- taking that file from a `maxstacksize` mismatch to a
# reconstruction refusal and out of the printable set entirely.
#
# It is a PRE-EXISTING `L1` gap either way (measured at BASE `7d36e2d`:
# `mismatch: code`, printed as `local l0_0 = {} l0_0[k1()] = 1 ...`, whose
# recompile loses the constructor's `NEWTABLE` size hint), so what is pinned
# here is not certification but that the reconstruction still SUCCEEDS and
# still means the same thing.
DYNAMIC_KEY_SRC = (b"function k1() return 'a' end function k2() return 'b' end"
                   b" local t = {[k1()] = 1, [k2()] = 2} print(t.a, t.b)")


def _load(src: bytes):
    return load_bytes(compile_source(src, strip=True))


def _certify(src: bytes):
    p = _load(src)
    return p, certify_proto(p, is_chunk_root=True)


@pytest.mark.parametrize("src", CONSTRUCTOR_CASES,
                         ids=range(len(CONSTRUCTOR_CASES)))
def test_constructor_fields_do_not_consume_the_table(src):
    p, cert = _certify(src)
    assert cert.level == "L3", (src, cert.reason, cert.mismatches)
    printed = print_chunk(p)
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode), printed


@pytest.mark.parametrize("src", NOT_A_CONSTRUCTOR_CASES,
                         ids=range(len(NOT_A_CONSTRUCTOR_CASES)))
def test_a_field_store_on_a_non_constructor_still_consumes(src):
    p, cert = _certify(src)
    assert cert.level == "L3", (src, cert.reason, cert.mismatches)
    printed = print_chunk(p)
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode), printed


def test_a_dynamic_key_constructor_still_reconstructs():
    """See `DYNAMIC_KEY_SRC`: the exemption must not reach a constructor the
    reconstructor cannot fold. Certification is not the assertion (this shape
    is an `L1` gap at BASE and still is); reconstruction succeeding is."""
    p = _load(DYNAMIC_KEY_SRC)
    printed = print_chunk(p)                    # must not raise, must not be None
    assert printed is not None
    a = run_bytes(compile_source(DYNAMIC_KEY_SRC, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode), printed
    assert a.stdout.split() == [b"1", b"2"]


# --------------------------------------------------------------------------
# Fault injection: the gate must still REJECT the reconstruction this task
# stopped producing. A fix that only makes protos certify proves nothing on
# its own -- every injection below asserts the printed/candidate source
# actually CHANGED before asserting the rejection.
# --------------------------------------------------------------------------

def test_the_gate_rejects_the_aliased_reconstruction():
    """Hand-build the exact source shape this task removed -- two constructors
    written into one slot, the second a re-assignment, the outer table's
    fields aliasing both to the last one -- and require `certify_l3` to refuse
    it against the exemplar's own bytecode.

    This is the injection with no decompiler internals in it at all: the
    candidate is a literal string, so it cannot be made to pass by anything
    changing in `express/`.
    """
    p = _load(ALIASING_EXEMPLAR)
    good = print_chunk(p).encode()
    aliased = (b"local l0_1 = {x = 1, y = 2}\n"
               b"l0_1 = {p = 3, q = 4}\n"
               b"local l0_0 = {a = l0_1, b = l0_1}\n"
               b"print(l0_0.a.x, l0_0.b.p)\n")
    assert aliased != good                      # the injection really is one
    assert certify_l3(p, good).level == "L3"
    bad = certify_l3(p, aliased)
    assert bad.level != "L3", bad
    # ... and it is not merely "compiles differently": it is a different
    # program. `t.a.x` is 3 under the alias and 1 under the original.
    a = run_bytes(compile_source(ALIASING_EXEMPLAR, strip=True), is_source=False)
    b = run_bytes(aliased, is_source=True)
    assert a.stdout != b.stdout
    assert a.stdout.split() == [b"1", b"3"]


def test_neutering_the_exemption_reproduces_the_defect():
    """Neuter `_constructor_field_target` (the whole rule) and require BOTH
    halves: the printed source changes back to the aliased shape, and the
    certification that this task gained is lost again. Restores it afterwards.

    This is the load-bearing proof for the rule -- with it neutered the
    exemplar prints a materially different program, so the rule is not
    cosmetic and not inert.
    """
    p = _load(ALIASING_EXEMPLAR)
    before = print_chunk(p)
    real = freereg._constructor_field_target
    try:
        freereg._constructor_field_target = lambda fn, li, pending: None
        after = print_chunk(p)
        cert = certify_proto(p, is_chunk_root=True)
    finally:
        freereg._constructor_field_target = real
    assert after != before
    assert "l0_1 = {" in after and "local l0_1 = {" in after   # the alias
    assert cert.level != "L3", cert
    assert print_chunk(p) == before             # restored


# A constructor whose table has a single consumer AND non-constant keys: the
# shape `config.lua`'s main chunk is made of. `T = {...}` (a `SETGLOBAL`
# consumer) rather than `local t = ... print(t.a, t.b)`, because two reads
# would make the table a local under any rule and the neuter below would have
# nothing to move.
DYNAMIC_KEY_SINGLE_CONSUMER = (
    b"function k1() return 'a' end function k2() return 'b' end\n"
    b"T = {[k1()] = 1, [k2()] = 2}\nprint(T.a, T.b)\n")

# A captured register whose EARLIER definitions are constructor scratch: the
# `snr_graphic.lua:main` shape, reduced. Slot 1 holds two inner table
# constructors, then a real local that a closure captures. Certifies `L3`.
CAPTURE_REUSE_SRC = (b"local a = {x = {p = 1}, y = {q = 2}}\nprint(a.x.p)\n"
                     b"local b = 5\nlocal f = function() return b end\n"
                     b"print(a.y.q, f())\n")


def test_neutering_the_constant_key_condition_breaks_the_dynamic_key_shape():
    """The `isk(ri.b)` half of the rule, neutered on its own: the exemption
    then reaches a constructor `_dispatch` cannot fold, the reconstructor
    refuses on the second field store, and the chunk stops printing at all.
    Pins that this condition is load-bearing rather than defensive --
    `config.lua` is the corpus instance, and it was measured going exactly
    this way while the rule was being written."""
    p = _load(DYNAMIC_KEY_SINGLE_CONSUMER)
    assert print_chunk(p) is not None
    real = freereg._constructor_field_target

    def loose(fn, li, pending):
        ri = li.ri
        if ri.op not in (Op.SETTABLE, Op.SETLIST):
            return None
        ent = freereg._pending_def(pending, ri.a)
        if ent is None or fn.instrs[ent.def_pc].ri.op is not Op.NEWTABLE:
            return None
        return ri.a

    try:
        freereg._constructor_field_target = loose
        assert print_chunk(p) is None           # ReconstructError, swallowed
    finally:
        freereg._constructor_field_target = real
    assert print_chunk(p) is not None           # restored


def test_neutering_per_definition_capture_reproduces_the_whole_function_defect():
    """The closure-capture half of the task, same shape of proof.

    Neutering `_captured_here` to `False` would be the wrong direction (it
    would simply seed nothing and could only inline MORE), so the neuter is
    the pre-task reading: seed every captured register at every pc. The
    fixture then materializes slot 1's inner constructors again, aliases the
    outer table's two fields to the last one, and loses its `L3`."""
    p = _load(CAPTURE_REUSE_SRC)
    before = print_chunk(p)
    assert certify_proto(p, is_chunk_root=True).level == "L3"
    real = names.classify_registers

    def whole_function(fn):
        rc = real(fn)
        return dataclasses.replace(rc, temp_defs=frozenset(
            k for k in rc.temp_defs if k[1] not in fn.captured_regs),
            temps=frozenset(rc.temps - fn.captured_regs),
            locals=frozenset(rc.locals | fn.captured_regs))

    try:
        _lua.classify_registers = whole_function
        after = print_chunk(p)
    finally:
        _lua.classify_registers = real
    assert after != before
    assert "l0_1 = {q = 2}" in after            # the alias, spelled out
    # `certify_l3` on the printed text, not `certify_proto`: the latter is
    # memoized per (proto, oracle) and would answer with the pre-neuter run.
    assert certify_l3(p, after.encode()).level != "L3"
    assert print_chunk(p) == before             # restored


def test_the_exemplar_aliased_before_the_fix():
    """The defect's signature, asserted directly rather than only through the
    gate: the exemplar's two inner constructors must land in *different*
    registers in the printed source, and each `NEWTABLE` definition must be
    classified a temporary.

    Stated as a property of `classify_registers` so a regression that
    re-materializes them is caught here even if some later change makes the
    recompile coincidentally match.
    """
    p = _load(ALIASING_EXEMPLAR)
    fn = lift_proto(p)
    rc = classify_registers(fn)
    newtables = [pc for pc, li in fn.instrs.items()
                 if li.ri.op is Op.NEWTABLE]
    assert len(newtables) == 3          # outer + two inner
    inner = [pc for pc in newtables if fn.instrs[pc].ri.a != 0]
    assert len(inner) == 2
    for pc in inner:
        assert (pc, fn.instrs[pc].ri.a) in rc.temp_defs, pc
    printed = print_chunk(p)
    assert printed.count("local l0_0 = {") == 1
    # No reassignment of a constructor slot anywhere: that is the aliasing
    # signature (`l0_1 = {` with no `local`).
    for line in printed.splitlines():
        assert not line.strip().startswith("l0_1 = {"), printed

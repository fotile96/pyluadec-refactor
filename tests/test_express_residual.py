"""M5 task 5: the `mismatch:` residual -- protos that print and recompile but
whose recompiled proto is not the original.

Everything here is adjudicated by `certify_proto`, which recompiles the
printed source with the real `luac_sz4` and compares the resulting proto
field-by-field under the normalization ladder. Nothing in this file relaxes
that gate: a fixture that is semantically right but differently compiled is a
FAILURE, not a pass.

Fixture sources are pure ASCII by construction, so assertions that inspect
printed text may decode; bytecode-derived strings elsewhere stay `bytes`.

## Cluster 1: a `for` statement owns its slots only for its own extent

`lparser.c`'s `fornum`/`forlist` `new_localvar` the control triple and the
visible variables and wrap the body in `enterblock`/`leaveblock`; `leaveblock`
restores `fs->freereg = fs->nactvar`, so the moment the loop's `end` is
reached slots `a..a+3+n` are ordinary expression-stack scratch again and luac
reuses them for the very next statement.

Through M4, `express.names.classify_registers` treated that ownership as a
whole-FUNCTION property (a register number in any `for` header's triple was a
control slot everywhere, and a loop variable was a named local everywhere),
and `Reconstructor.__init__` seeded every loop variable into `declared` for
the whole function. Both are wrong on exactly the same shape -- a `for` loop
followed by a statement that reuses its slots -- and both were wrong in a way
that certification caught but that a reader of the output would not:

  * the classifier saw the reuse as "a write to a named local", which ends a
    statement in the freereg simulation, and promoted the *preceding*
    expression-stack values to named locals;
  * the reconstructor printed the reuse as `l0_9 = ...`, a bare assignment to
    a name that is no longer in scope -- which Lua compiles as a write to a
    GLOBAL. That is a semantic change, not merely an unfaithful one; only the
    certification gate kept it from shipping.

Corpus movement for the fix: 1403 -> 1415 unique proto shapes at `L3`
(1869 -> 1881 occurrences), 215 -> 216 of 229 files shipping structured
source, measured 2026-08-12.
"""
import pytest

from pyluadec.emit.lua import print_chunk
from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.structure.structured import certify_proto


def _certify(src: bytes):
    proto = load_bytes(compile_source(src, strip=True))
    return proto, certify_proto(proto, is_chunk_root=True)


# Each entry is (source, expected stdout). The stdout expectation is measured
# from the ORIGINAL bytecode inside the test rather than trusted from here;
# it is recorded so a fixture that silently stops exercising anything shows up.
LOOP_SLOT_REUSE = [
    # `snr_novel.lua:main_6`, reduced to its shape and made self-contained.
    # The third argument of the trailing call lands in the loop VARIABLE's
    # slot; before the fix that printed as `l0_3 = 60` (a SETGLOBAL) and
    # dragged the callee and the first two arguments into named locals.
    (b"local n = 0 for i = 0, 20 do n = n + i end print(0, '', 60) print(n)",
     [b"0\t\t60", b"210"]),
    # Two sequential numeric `for`s where the second's CONTROL TRIPLE lands in
    # the first's variable + the slots just above it. This is the shape that
    # made `tests/test_semantic_regressions.py::
    # test_counter_closure_and_dispatch_mix` ship fallback through M4.
    (b"local t = {} for i = 1, 6 do t[i] = i * 2 end "
     b"local s = 0 for i = 1, 8 do s = s + i end print(s, t[6])",
     [b"36\t12"]),
    # The trailing statement is a plain call whose CALLEE lands in the loop's
    # control base -- before the fix, `l0_1 = print` and then `l0_1(l0_2)`.
    (b"local s = 0 for i = 1, 4 do s = s + i end print(s)", [b"10"]),
    # A loop whose body writes BACK to the loop variable (legal Lua; does not
    # affect iteration), followed by slot reuse. This is the one shape that
    # needs the declaration to be present INSIDE the body and absent after it,
    # so it fails if `declare_loop_vars` is dropped in either direction.
    (b"local s = 0 for i = 1, 3 do i = i + 10 s = s + i end print(s, 1, 2, 3)",
     [b"36\t1\t2\t3"]),
    # Nested loops sharing the outer's slots after the inner one closes.
    (b"local s = 0 for i = 1, 3 do for j = 1, 3 do s = s + j end s = s + i end "
     b"print(s)", [b"24"]),
]


@pytest.mark.parametrize("src,words", LOOP_SLOT_REUSE,
                         ids=range(len(LOOP_SLOT_REUSE)))
def test_slots_a_for_statement_released_are_not_still_its_own(src, words):
    """The `for` header's registers become ordinary scratch at its `end`.

    Certification is the adjudicator: the printed source has to recompile to
    the original proto, so "close enough" does not pass.
    """
    proto, cert = _certify(src)
    assert cert.level == "L3", (cert.reason, print_chunk(proto))


@pytest.mark.parametrize("src,words", LOOP_SLOT_REUSE,
                         ids=range(len(LOOP_SLOT_REUSE)))
def test_the_printed_source_computes_what_the_bytecode_computes(src, words):
    """Differential execution: run the original bytecode and the printed
    source under `lua_sz4` and diff stdout.

    **Honest about what this does NOT catch.** Measured 2026-08-12 by running
    this arm against the pre-fix tree: all five fixtures were GREEN before the
    fix, while three of the five failed certification. The pre-fix output for
    fixture 0 really did contain `l0_3 = 60`, a write to a *global* (the name
    left scope at the loop's `end`) -- but it is read back by the very next
    expression in the same statement, so the value observed is the same and
    stdout is identical. The leak is only observable to something that
    inspects `_G`, which none of these fixtures do.

    So the certification test above is the one that adjudicates this cluster,
    and this one is a companion that would catch the *other* direction (an
    over-inlined local that silently disappears, the failure mode
    `test_express_liverange.py` guards) if a future change to the loop-window
    rules produced it here. It is cheap and it is not load-bearing; recorded
    that way rather than written up as the proof.
    """
    proto = load_bytes(compile_source(src, strip=True))
    printed = print_chunk(proto)
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(printed.encode(), is_source=True)
    assert a.returncode == 0 and b.returncode == 0, (a.stderr, b.stderr)
    assert a.stdout == b.stdout, printed
    # measured from the original; `words` above is only a tripwire against a
    # fixture that has quietly stopped exercising anything.
    assert a.stdout.splitlines() == words

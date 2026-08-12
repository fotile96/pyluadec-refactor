"""Readability of the structured printer's text (M5 task 7).

Every assertion here is about **presentation** -- what a human translator
reads -- and every one of them is paired with a proof that the presentation
change cannot move the certification verdict. Two levels of proof are used,
and they are different things:

* **Oracle equivalence** (`compile_source(A) == compile_source(B)`): the two
  spellings are the same program to the real `luac_sz4`, byte for byte, on
  stripped output. This is the mechanical form of the `lparser.c` reading
  quoted in each test's docstring, and it is the strongest available evidence
  that a spelling change is invisible below the printer.
* **End-to-end certification** (`certify_proto(..., is_chunk_root=True)`
  returns `L3`): the fixture, printed by THIS printer and recompiled by the
  real `luac_sz4`, matches the original proto field by field under the
  versioned normalization ladder.

The corpus-wide half of the proof is not here and cannot be: it is
`corpus/ledger.jsonl` staying byte-identical across each of this task's
commits, which `tests/test_ledger_ratchet.py` re-derives from a fresh
`scripts/run_corpus.py` pass.

All fixture sources are ASCII except where a test is specifically about
non-ASCII bytes, and those tests hold their payload as `bytes` and compare
against `bytes`.
"""
from pyluadec.emit.lua import print_chunk
from pyluadec.ingest import load_bytes
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.structure.structured import certify_proto


def printed(src: bytes) -> str:
    """Structurally print `src`'s compiled chunk, refusing to paper over a
    refusal (a `None` here would make every text assertion below fail with an
    unhelpful `TypeError`)."""
    out = print_chunk(load_bytes(compile_source(src, strip=True)))
    assert out is not None, f"printer refused: {src!r}"
    return out


def certifies(src: bytes) -> None:
    p = load_bytes(compile_source(src, strip=True))
    cert = certify_proto(p, is_chunk_root=True)
    assert cert.level == "L3", (src, cert.mismatches)


# --------------------------------------------------------------------------
# 1. elseif
# --------------------------------------------------------------------------

ELSEIF_SRC = b"if a then f() elseif b then g() elseif c then h() else k() end"


def test_elseif_and_nested_if_in_else_compile_identically():
    """`lparser.c::ifstat` (lines 1141-1162), mechanized.

    `ifstat` reads `IF cond THEN block {ELSEIF cond THEN block} [ELSE block]
    END`. For an ELSEIF it does exactly three things -- concat a fresh
    `luaK_jump` onto `escapelist`, `luaK_patchtohere(flist)`, then another
    `test_then_block`. For an ELSE it does the first two and then `block()`.
    So `else if ... end` differs from `elseif ...` only by the extra
    `enterblock`/`leaveblock` pair around the inner `ifstat`, and
    `leaveblock` emits an instruction only when `bl->upval` is set --
    `markupval` sets that on the innermost block whose `nactvar <= level`,
    which is the inner `then` block, never the wrapper. The inner `ifstat`'s
    own closing `luaK_patchtohere(escapelist)` and the outer one then both
    resolve to the same `fs->pc`, because nothing is emitted between them.

    Reading the parser is what says *why*; this assertion is what says *that*.
    """
    assert (compile_source(b"if x then f() elseif y then g() else h() end", strip=True)
            == compile_source(b"if x then f() else if y then g() else h() end end",
                              strip=True))
    # ... and with no trailing `else`, the arm where `ifstat` takes its
    # `luaK_concat(fs, &escapelist, flist)` branch instead of patching.
    assert (compile_source(b"if x then f() elseif y then g() end", strip=True)
            == compile_source(b"if x then f() else if y then g() end end", strip=True))


def test_else_arm_that_is_a_single_if_prints_elseif():
    assert printed(ELSEIF_SRC) == (
        "if a then\n"
        "  f()\n"
        "elseif b then\n"
        "  g()\n"
        "elseif c then\n"
        "  h()\n"
        "else\n"
        "  k()\n"
        "end\n")


def test_else_arm_with_more_than_one_statement_stays_an_else():
    """The collapse is exact, not "an `if` appears somewhere in the else".

    `else g() if b then h() end end` has two statements in its else arm, so
    printing `elseif` would DROP `g()`. The guard is that the arm must be
    *exactly* one `If` and nothing else.
    """
    assert printed(b"if a then f() else g() if b then h() end end") == (
        "if a then\n"
        "  f()\n"
        "else\n"
        "  g()\n"
        "  if b then\n"
        "    h()\n"
        "  end\n"
        "end\n")


def test_elseif_chain_certifies_l3():
    certifies(ELSEIF_SRC)
    certifies(b"if a then f() elseif b then g() end")
    certifies(b"if a then f() else g() if b then h() end end")


def test_elseif_chain_runs_identically():
    src = (b"local r = {} for i = 1, 4 do "
           b"if i == 1 then r[i] = 'a' elseif i == 2 then r[i] = 'b' "
           b"elseif i == 3 then r[i] = 'c' else r[i] = 'd' end end "
           b"print(r[1], r[2], r[3], r[4])")
    bc = compile_source(src, strip=True)
    out = print_chunk(load_bytes(bc))
    assert out is not None and "elseif" in out
    a = run_bytes(bc, is_source=False)
    b = run_bytes(out.encode(), is_source=True)
    assert (a.returncode, a.stdout, a.stderr) == (b.returncode, b.stdout, b.stderr)
    assert a.stdout == b"a\tb\tc\td\n"

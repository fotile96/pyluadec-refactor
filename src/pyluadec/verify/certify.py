"""L3 认证门（spec §5）：结构化产物重编译 → 归一化阶梯逐级比对 → 通过即 proved。"""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec import oracle
from pyluadec.ingest import Proto, load_bytes

from .normalize import NORMALIZATIONS, Mismatch, compare_protos


def debug_view(p: Proto) -> dict:
    """Exactly the fields `compare_protos` checks that `structural_hash` omits,
    recursively over the subtree, as plain JSON-able data.

    One enumeration of "the debug picture", with two consumers:
    `structure.structured._debug_fingerprint` hashes it (to key the
    certification memo soundly -- see that docstring for why
    `structural_hash` alone is not enough), and `carries_debug` below reads
    it to decide the candidate's strip mode. Keeping them on one view is the
    point: a field added here is automatically both memo-relevant and
    strip-mode-relevant, which is the only combination `compare_protos`
    supports.
    """
    return {
        "source": p.source.hex() if p.source is not None else None,
        "linedefined": p.linedefined,
        "lastlinedefined": p.lastlinedefined,
        "lineinfo": list(p.lineinfo),
        "locvars": [[v.name.hex() if v.name is not None else None,
                     v.startpc, v.endpc] for v in p.locvars],
        "upvalues": [u.hex() if u is not None else None for u in p.upvalues],
        "subprotos": [debug_view(s) for s in p.subprotos],
    }


def carries_debug(p: Proto) -> bool:
    """Does anything in `p`'s subtree carry debug-segment data that `luac -s`
    would have removed?

    This is the strip-mode decision (see `certify_l3`). Three of
    `debug_view`'s fields are disjuncts -- `lineinfo`, `locvars`, `upvalues`
    -- and they are exactly `lundump.c` `LoadDebug`'s three sized lists, i.e.
    exactly what `-s` zeroes out.

    ## Why `source` is not a disjunct

    Measured 2026-08-12 over the full corpus: all 1944 protos carry
    `source = b"=?"` (a non-`None` placeholder) while all three debug lists
    are empty in every one of them. `ldump.c`'s `DumpFunction` writes `source`
    as `DumpString((f->source==p || D->strip) ? NULL : f->source, D)`, where
    `p` is the *parent* proto's `source` (`NULL` at the root call). That guard
    has two independent ways to produce `NULL`, not one: `D->strip` (a `-s`
    dump from THIS `luac` has `source = None` unconditionally), and
    `f->source==p` -- a nested proto whose own `source` string is
    *object-identical* to its parent's writes `NULL` and is expected to
    inherit the parent's `source` on load, **even when the dump is
    unstripped**. So "this proto's `source` is non-`None`" proves nothing
    about strippedness in general, not only on this corpus: an ordinary
    unstripped multi-function dump also has `NULL` `source` on every nested
    proto that shares its chunk's source string, which is the common case.
    Counting a non-`None` `source` as debug info would therefore misclassify
    both that ordinary case and, on this corpus specifically, classify all 229
    corpus files as unstripped, compile every candidate unstripped, and move
    the committed ledger. `linedefined`/`lastlinedefined` are excluded for the
    plainer reason that they are not in the debug segment at all (they sit in
    `DumpFunction`'s body and survive `-s`, per CLAUDE.md), so they say
    nothing about strippedness.

    ## Why all three, and why the subtree

    `lineinfo` alone would in fact separate real `luac` output both ways
    (an unstripped dump always has `sizelineinfo == sizecode >= 1`, since
    every function ends in a RETURN). `locvars` and `upvalues` are included
    because the predicate must hold for any dump `compare_protos` will be
    pointed at, not just this `luac`'s: if the original records scope ranges
    or upvalue names, a stripped candidate cannot reproduce them, whatever
    its `lineinfo` looks like. Each disjunct has its own test in
    `tests/test_certify_stripmode.py`. The walk is over the subtree because
    `compare_protos` recurses -- a main chunk of `Name = function() ... end`
    assignments has empty debug lists of its own and unstripped children,
    which is the shape this corpus is made of.
    """
    def walk(v: dict) -> bool:
        if v["lineinfo"] or v["locvars"] or v["upvalues"]:
            return True
        return any(walk(s) for s in v["subprotos"])
    return walk(debug_view(p))


@dataclass(frozen=True)
class CertResult:
    level: str                       # "L3" | "L1"
    rung: int | None                 # normalization level that passed, or None
    mismatches: tuple[Mismatch, ...]


def certify_l3(original: Proto, structured_src: bytes) -> CertResult:
    """Recompile `structured_src` and compare it to `original` up the ladder.

    **The candidate's strip mode follows the original's** (`carries_debug`):
    `-s` when the original is stripped, unstripped when it is not. Both sides
    then record the same kinds of thing, and the ladder compares like with
    like.

    ## What that buys, on unstripped input

    Rung 1 (`_strip_lineinfo`) blanks locvar and upvalue *names* while KEEPING
    each locvar's count/`startpc`/`endpc`. Against an unstripped original the
    candidate now carries real `locvars` too, so that rung checks that every
    `local` was reconstructed into the **same lexical block over the same pc
    range** -- a structural claim about scopes that nothing else in the gate
    makes. `tests/test_certify_stripmode.py` pins it with a candidate that
    hoists a local out of a `do` block: its `code` is byte-identical to the
    original's, and it is refused on `locvars` alone.

    ## What it does NOT buy, on stripped input

    When the original is stripped, both `locvars` tuples are empty and rung 1's
    scope comparison is `() == ()` -- vacuous, exactly as before this change.
    That is not a regression, it is what a stripped dump can support: it does
    not record scopes. Every one of the 229 corpus files is stripped (measured
    2026-08-12: 1944/1944 protos have empty `lineinfo`, `locvars` and
    `upvalues`), so the corpus takes the `strip=True` branch throughout and its
    result is bit-for-bit what it was.

    ## History

    Before M4 task 7 the candidate was ALWAYS compiled `-s`. Against an
    unstripped original that meant a non-empty `locvars` compared against an
    empty one, mismatching at every rung, so any proto whose SUBTREE declared
    even one local could not certify -- note "subtree", not "this proto":
    `compare_protos` recurses, so `f = function() local a = 1 return a end`
    has `len(main.locvars) == 0` and still refused, on the subproto's
    `locvars`. Ordinary `luac` output therefore fell back for nearly every
    real function, with `Mismatch(field="locvars")` as the only clue.
    Re-measured 2026-08-12 with the repo's own `luac_sz4`, before and after
    ("before" = the candidate compiled `-s` whatever the original is; "after" =
    this function as it stands):

        source                            strip  before        after
        b"x = 1\\n"                        -s     L3 rung 0     L3 rung 0
        b"x = 1\\n"                        --     L3 rung 1     L3 rung 0
        b"local a = 1\\nprint(a)\\n"        -s     L3 rung 0     L3 rung 0
        b"local a = 1\\nprint(a)\\n"        --     L1, locvars   L3 rung 1
        b"for i = 1, 10 do print(i) end"  -s     L3 rung 0     L3 rung 0
        b"for i = 1, 10 do print(i) end"  --     L1, locvars   L3 rung 1

    Read the `after` column's rung this way: an unstripped one-liner that
    declares no local reproduces `source`/`lineinfo`/`locvars` exactly and
    lands on rung 0 (row 2, which is why it *drops* a rung -- the always-`-s`
    candidate could never match `source`). One that declares a local lands on
    rung 1, because the printer synthesizes the NAME (`l0_0` where the
    original wrote `a` or `i`) and rung 1 is the rung that blanks names while
    keeping each locvar's count and pc range. Rows 4 and 6 are that case;
    measured, their rung-0 mismatch fields are `locvars` for row 4 and
    `lineinfo` + `locvars` for row 6 (the `for` is printed over three lines
    where the original was one). `docs/runbooks/structured-pipeline.md`'s
    30-source table reports the same three unstripped rung-1 -> rung-0 rows
    (`x = 1`, `print(1)`, `return 1`) -- all three declare nothing, and all
    three re-measured at rung 0 here.

    The direction is **stricter, not "strictly stronger"** -- a distinction
    the M4 task 7 brief got wrong and measurement corrected. The stripped
    column above is untouched code and cannot move. The unstripped column
    mostly gains, but it also loses, and the loss is not a corner case:
    **any statement whose reconstruction materialises a table-base,
    index-target, or condition value as a `local` the original never declared
    now refuses on unstripped input** -- the printer names it because it is a
    genuine `freereg` local by the stack-discipline rule (survives to the end
    of its statement), but the original source never bound it to a name, and
    an unstripped candidate can now show that difference. An ordinary example,
    not an exotic one: `a.b = 1` prints as

        local l0_0 = a
        l0_0["b"] = 1

    -- same `code` as the original, one locvar the original doesn't have.
    `L3` rung 1 before this task (the always-`-s` candidate had no locvars to
    disagree with), `L1` on `locvars` after. `repeat f() until g()` and
    `return a and b or c` (the two losses in the M4 task 7 report's own
    30-source sample, reproduced below) are the identical mechanism applied to
    a loop condition and an `and`/`or` chain, not a separate phenomenon.

    **The 12:2 gain:loss ratio is a property of that particular 30-source
    sample, not of the change.** A second, independently-chosen sample of 30
    ordinary one-liners (plain/table/index assignments, calls, arithmetic,
    comparisons, method calls, table constructors, `if`/`while`/`for`,
    `local function`) measured 2026-08-12 gives, of 29 sources that printed:
    4 gains, 4 losses, 21 unchanged -- roughly 1:1, not 12:1. Losses track how
    often reconstruction invents a table-base or condition local, not how
    unusual the Lua construct looks. A gate cannot start examining a
    dimension and also promise never to reject on it. The narrower property
    that IS strictly true across both samples: every level-changed row's
    losing side mismatches only on `locvars` (and, in the first sample, two
    rows also on `upvalues`' count) -- never on `code`, `constants`,
    `maxstacksize` or the frame contract. Losses are pinned in
    `tests/test_certify_stripmode.py`; both samples' full tables are in
    `docs/runbooks/structured-pipeline.md`.
    """
    try:
        recompiled = load_bytes(
            oracle.compile_source(structured_src, strip=not carries_debug(original)))
    except oracle.LuaCompileError:
        return CertResult(level="L1", rung=None, mismatches=())
    last: list[Mismatch] = []
    for k in range(len(NORMALIZATIONS) + 1):
        diffs = compare_protos(original, recompiled, level=k)
        if not diffs:
            return CertResult(level="L3", rung=k, mismatches=())
        last = diffs
    return CertResult(level="L1", rung=None, mismatches=tuple(last))

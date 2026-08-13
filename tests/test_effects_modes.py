"""Calibration of `lift/effects.py`'s three effect modes (M4 task 11).

`lift/effects.py` grades every opcode under `STRICT`, `NO_METAMETHOD` and
`TRUSTING`. Per CLAUDE.md only `STRICT` ever had a justification; the other two
columns were asserted. This module is the evidence half of making them
arguable:

* the corpus census that is the *only* empirical support `NO_METAMETHOD` has,
  committed so it re-runs (and can fail) rather than living in a report;
* a mechanical pin of which rows the two looser modes actually move, so the
  per-row `# nm:` / `# tr:` block in `effects.py` cannot silently go stale;
* mode-difference tests for three representative opcodes, each stating in its
  docstring what would have to be TRUE of the runtime for the grading to be
  sound.

Nothing here changes a grading. `effects.py` is the axiom layer; a grading
change needs an `lvm.c` citation plus a differential run (M4 task 8 is the
worked example). Two under-gradings this task found are recorded as findings
in `effects.py`'s comments rather than fixed in it. **One of the two, `LEN`'s
`NO_METAMETHOD` column, was corrected at M5 task 1** under that protocol --
see `tests/test_effects_len.py`, which owns the citation and the differential.
The other (the `luaC_checkGC` blind spot shared by `NEWTABLE`/`CLOSURE`/
`CONCAT`) is deliberately left standing; `docs/runbooks/m3-backlog.md` §M5.1
says why.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "pyluadec"


# ---------------------------------------------------------------------------
# 1. The census.
# ---------------------------------------------------------------------------

# Every way a Lua 5.1 *script* can reach metatable machinery. A script cannot
# attach a metatable without naming `setmetatable` (or `debug.setmetatable`,
# which needs `debug`), cannot read one back without `getmetatable`, cannot
# manufacture userdata without `newproxy`, cannot bypass a metamethod without
# `rawget`/`rawset`/`rawequal`, and cannot swap an environment table without
# `getfenv`/`setfenv`. All of those are *global names*, so if the script uses
# one it must appear verbatim in some proto's constant table -- `GETGLOBAL`
# takes its key from `KBx(i)` (lvm.c:432-439), and `t.setmetatable` /
# `t:setmetatable()` likewise take theirs from a `RK` constant.
_METAMETHOD_MACHINERY = (
    b"setmetatable", b"getmetatable", b"rawget", b"rawset", b"rawequal",
    b"newproxy", b"getfenv", b"setfenv", b"debug",
)

# A static census over constant tables is only as good as its claim to see all
# the script code there is. These are Lua 5.1's runtime code-loading entry
# points: if a script could compile a chunk at runtime, that chunk's constants
# would never appear in any of the 229 files and the census would be blind to
# whatever it does with metatables. (`load` is deliberately not a substring
# needle -- it matches game names like `layerLoad`; it is checked separately
# below as a *global read*, of which there are zero.)
_RUNTIME_CODE_LOADING = (b"loadstring", b"dofile", b"require")

# Every metamethod event name in Lua 5.1 begins with two underscores
# (`ltm.c`'s luaT_init: "__index", "__newindex", "__gc", "__mode", "__eq",
# "__add" ... "__le", "__concat", "__call", plus "__metatable" and
# "__tostring" in the libraries). Searching for the bare `__` prefix is
# strictly more general than listing them, and is what makes the census a
# statement about *all* metamethods rather than the ones we remembered.
_METAMETHOD_PREFIX = b"__"

# Re-derived 2026-08-12 against the 229-file corpus. These are asserted, not
# just reported: if the corpus ever changes shape, this test should say so
# loudly rather than quietly re-scoping the NO_METAMETHOD argument that rests
# on it.
_CENSUS_FILES = 229
_CENSUS_PROTOS = 1944
_CENSUS_CONSTANTS = 71414
_CENSUS_STRING_CONSTANTS = 49063
_CENSUS_DISTINCT_STRINGS = 23586

# Positive control. A census whose answer is "zero, everywhere" is worthless if
# the scan is broken -- an empty needle list, a decode that throws and gets
# swallowed, a `constants` attribute that silently became empty would all
# produce the same green. `b"vms"` is the corpus's most-read global (16748
# GETGLOBAL sites) and appears as a substring of 993 constants across the 1944
# proto occurrences; running it through the *same* loop proves the loop can
# find something.
_CONTROL_NEEDLE = b"vms"
_CONTROL_HITS = 993
# Same idea for the GETGLOBAL scan that checks `load` is never read as a
# global: `vms` is read at 16748 GETGLOBAL sites, cross-checked against an
# independent decode-only walk of the corpus.
_CONTROL_GLOBAL_READS = 16748


def test_corpus_never_names_metamethod_machinery(lifted_corpus):
    """No corpus constant names metatable machinery or any `__*` event.

    This is the empirical basis for `EffectMode.NO_METAMETHOD` being
    *plausible* -- and the census's own limit is the more important half of
    the result, so it is restated here and in the mode's docstring: the census
    sees only what the scripts name. The PSP engine injects globals and can
    inject userdata, and either may carry a metatable (`__index`,
    `__newindex`, `__gc`) that no constant table can reveal. So
    `NO_METAMETHOD` is established for tables the scripts *construct*, and is
    **not** established for `GETGLOBAL`/`GETTABLE`/`SELF`/`SETTABLE` applied
    to engine values.

    All comparisons are on `bytes`. Corpus strings are Shift-JIS-ish Japanese
    game text and are never decoded.
    """
    from pyluadec.lift.opcodes import Op

    files = set()
    protos = 0
    constants = 0
    string_constants = 0
    distinct: set[bytes] = set()
    hits: dict[bytes, list[tuple[str, tuple[int, ...], int]]] = {
        needle: [] for needle in _METAMETHOD_MACHINERY + _RUNTIME_CODE_LOADING
    }
    load_globals = 0
    control_globals = 0
    dunder: list[tuple[str, tuple[int, ...], int]] = []
    control = 0

    for fname, path, proto, fn in lifted_corpus:
        files.add(fname)
        protos += 1
        for instr in fn.instrs.values():
            if instr.ri.op is not Op.GETGLOBAL:
                continue
            key = proto.constants[instr.ri.bx]
            if key == b"load":
                load_globals += 1
            elif key == _CONTROL_NEEDLE:
                control_globals += 1
        for i, k in enumerate(proto.constants):
            constants += 1
            if not isinstance(k, bytes):
                continue
            string_constants += 1
            distinct.add(k)
            for needle in _METAMETHOD_MACHINERY + _RUNTIME_CODE_LOADING:
                if needle in k:
                    hits[needle].append((fname, path, i))
            if _METAMETHOD_PREFIX in k:
                dunder.append((fname, path, i))
            if _CONTROL_NEEDLE in k:
                control += 1

    # Census shape first: a silently shrunken corpus would make the zero
    # results below meaningless.
    assert len(files) == _CENSUS_FILES
    assert protos == _CENSUS_PROTOS
    assert constants == _CENSUS_CONSTANTS
    assert string_constants == _CENSUS_STRING_CONSTANTS
    assert len(distinct) == _CENSUS_DISTINCT_STRINGS
    assert control == _CONTROL_HITS, (
        f"positive control {_CONTROL_NEEDLE!r} found {control} times, expected "
        f"{_CONTROL_HITS}: the scan below cannot be trusted to find anything")

    # The result. Report locations, not the constants themselves -- they are
    # undecoded game text.
    for needle in _METAMETHOD_MACHINERY + _RUNTIME_CODE_LOADING:
        assert hits[needle] == [], (
            f"{needle!r} appears in {len(hits[needle])} corpus constants "
            f"(first at {hits[needle][:3]}); the NO_METAMETHOD argument in "
            f"lift/effects.py rests on this being empty")
    assert control_globals == _CONTROL_GLOBAL_READS, (
        f"positive control: {_CONTROL_NEEDLE!r} read at {control_globals} "
        f"GETGLOBAL sites, expected {_CONTROL_GLOBAL_READS}; the `load` check "
        f"below cannot be trusted to find anything")
    assert load_globals == 0, (
        f"`load` is read as a global at {load_globals} sites; the scripts may "
        f"be compiling chunks this census cannot see")
    assert dunder == [], (
        f"{len(dunder)} corpus constants contain b'__' (first at "
        f"{dunder[:3]}); a metamethod event name may have appeared")


# ---------------------------------------------------------------------------
# 2. Which rows the looser modes actually move.
#
# The per-row argument in effects.py leans on one structural fact: the modes
# are a chain of *added* assumptions, so a row whose three columns are equal
# needs no argument beyond STRICT's. That makes the 20/18 split load-bearing
# prose, and prose goes stale. These two tests derive the split from
# `analyze()` itself, so a future grading change that invalidates the comment
# block fails here instead of quietly making it a lie.
# ---------------------------------------------------------------------------

# 20 rows: all three modes agree, so NO_METAMETHOD/TRUSTING are entailed by
# STRICT and owe no separate argument.
_ENTAILED = {
    "MOVE", "LOADK", "LOADBOOL", "LOADNIL", "NEWTABLE", "GETUPVAL", "SETUPVAL",
    "NOT", "JMP", "TEST", "TESTSET", "CALL", "TAILCALL", "RETURN", "FORPREP",
    "FORLOOP", "TFORLOOP", "CLOSE", "CLOSURE", "VARARG",
}

# 18 rows: at least one looser column is strictly below STRICT, so it rests on
# the mode's own assumption and carries a `# nm:` / `# tr:` note.
_RELAXED = {
    "GETGLOBAL", "GETTABLE", "SELF", "SETGLOBAL", "SETTABLE", "SETLIST",
    "ADD", "SUB", "MUL", "DIV", "MOD", "POW", "UNM", "LEN", "CONCAT",
    "EQ", "LT", "LE",
}

# The only 4 rows TRUSTING moves below NO_METAMETHOD -- i.e. the entire value
# TRUSTING adds over NO_METAMETHOD. All four are `# UNARGUED` in effects.py,
# and all four are ones the corpus actively falsifies (892 SETGLOBAL,
# 1667 SETTABLE, 92 SETLIST, 44809 CALL sites; measured 2026-08-12).
#
# LEN joined this set at M5 task 1, and that is a direct consequence of the
# regrade rather than a separate decision: once `#t` is READ_HEAP under
# NO_METAMETHOD, TRUSTING's own assumption ("a table read may be reordered
# freely") is exactly what takes it back down to PURE. Before the regrade both
# looser columns read PURE, so TRUSTING moved nothing there. See
# tests/test_effects_len.py.
_TRUSTING_ONLY = {"GETGLOBAL", "GETTABLE", "SELF", "LEN"}


def _probe(op):
    """A decoded instruction for `op` with operands that are legal for it."""
    from pyluadec.lift.opcodes import decode
    if op.name in ("JMP", "FORLOOP", "FORPREP"):
        return decode(int(op) | (1 << 6) | ((0 + 131071) << 14), pc=10)
    return decode(int(op) | (1 << 6) | (1 << 14) | (1 << 23), pc=10)


def _columns(op):
    from pyluadec.lift.effects import EffectMode, analyze
    ri = _probe(op)
    return tuple(analyze(ri, m).effect for m in
                 (EffectMode.STRICT, EffectMode.NO_METAMETHOD, EffectMode.TRUSTING))


def test_mode_columns_split_20_entailed_18_relaxed():
    """20 rows grade identically in all three modes; 18 do not. Derived, not asserted."""
    from pyluadec.lift.opcodes import Op
    entailed = set()
    relaxed = set()
    for op in Op:
        strict, no_mm, trusting = _columns(op)
        (entailed if strict == no_mm == trusting else relaxed).add(op.name)
    assert entailed == _ENTAILED, f"entailed set moved: {entailed ^ _ENTAILED}"
    assert relaxed == _RELAXED, f"relaxed set moved: {relaxed ^ _RELAXED}"
    assert len(entailed) == 20 and len(relaxed) == 18
    assert len(entailed) + len(relaxed) == len(list(Op)) == 38


def test_trusting_moves_only_four_rows_below_no_metamethod():
    """TRUSTING's entire delta over NO_METAMETHOD is four table-read opcodes.

    This is the load-bearing fact behind the default-mode decision. Everything
    TRUSTING buys over NO_METAMETHOD is "treat GETGLOBAL/GETTABLE/SELF/LEN as
    PURE", and PURE means "reorderable against any store" -- which the corpus
    contradicts outright (globals and table fields are both written). So
    TRUSTING has no defensible whole-pipeline use here; NO_METAMETHOD is the
    only looser mode a future pass should consider opting into.

    Was three rows until M5 task 1 regraded LEN's NO_METAMETHOD column; `#t`
    is a table read like the other three, so it lands in the same set for the
    same reason.
    """
    from pyluadec.lift.opcodes import Op
    moved = {op.name for op in Op if _columns(op)[2] != _columns(op)[1]}
    assert moved == _TRUSTING_ONLY, f"TRUSTING delta moved: {moved ^ _TRUSTING_ONLY}"


# ---------------------------------------------------------------------------
# 3. Mode-difference tests for three representative opcodes.
#
# Each pins all three gradings and states, in its docstring, what would have to
# be TRUE of the runtime for the looser gradings to be sound. `test_effects.py`
# already pins the same values inside a 44-row exhaustive table (counted from
# `_EXHAUSTIVE_CASES` at M5 task 1; it said 45); the point of
# repeating three of them here is that the *soundness condition* lives next to
# the value, which is the deliverable a pass author will actually read before
# selecting a mode.
# ---------------------------------------------------------------------------


def test_mode_difference_gettable():
    """GETTABLE: ARBITRARY -> READ_HEAP -> PURE.

    What must be TRUE of the runtime for each grading to be sound:

    * `STRICT` = ARBITRARY: nothing. `lvm.c:440-443` calls `luaV_gettable`,
      which follows `__index` (`lvm.c:108-133`), and `__index` may be a
      function running arbitrary code. Always sound.
    * `NO_METAMETHOD` = READ_HEAP: the table in `R[B]` must have no `__index`
      (nor be a non-table with an `__index`-bearing metatable). Then
      `luaV_gettable` is one raw `luaH_get`, which reads the heap and does not
      write it. **The census establishes this for tables the script built and
      does NOT establish it for engine-supplied values** -- and 8379 of the
      corpus's 11910 GETTABLE sites index something that came from a
      `GETGLOBAL`, so the unproven case is the common one.
    * `TRUSTING` = PURE: additionally, nothing between the two points being
      reordered may change what the read returns -- no `SETTABLE`/`SETLIST`
      into that table, and no `CALL` that could reach it. The corpus has 1667
      SETTABLE, 92 SETLIST and 44809 CALL sites, so this must be established
      per region by the pass, never assumed globally. `# UNARGUED`.

    `may_error` stays True in every mode: a non-table `R[B]` with no metatable
    still reaches `luaG_typeerror`, which no metamethod assumption removes.
    """
    from pyluadec.lift.effects import Effect, EffectMode, analyze
    from pyluadec.lift.opcodes import Op, decode
    ri = decode(int(Op.GETTABLE) | (3 << 6) | (2 << 14) | (1 << 23), pc=0)
    assert analyze(ri, EffectMode.STRICT).effect is Effect.ARBITRARY
    assert analyze(ri, EffectMode.NO_METAMETHOD).effect is Effect.READ_HEAP
    assert analyze(ri, EffectMode.TRUSTING).effect is Effect.PURE
    for mode in EffectMode:
        assert analyze(ri, mode).may_error, mode
        assert analyze(ri, mode).reads == frozenset({1, 2}), mode
        assert analyze(ri, mode).writes == frozenset({3}), mode


def test_mode_difference_add():
    """ADD (and every `arith_op` sibling): ARBITRARY -> PURE -> PURE.

    What must be TRUE of the runtime:

    * `STRICT` = ARBITRARY: nothing. The `arith_op` macro (`lvm.c:364-373`)
      falls through to `Arith` (`lvm.c:317-337`), which calls `call_binTM` for
      `__add`; that metamethod is arbitrary code.
    * `NO_METAMETHOD` = PURE: neither operand may carry an `__add` metatable.
      Then the whole opcode is `setnvalue(ra, ...)` on the number fast path,
      or `luaV_tonumber` string coercion, which parses the operand's own
      immutable bytes. Nothing outside `ra`/`rb`/`rc` is touched, so PURE is
      *exact*, not merely permitted. In Lua 5.1 only strings and userdata can
      carry a shared metatable set from C; the census shows the scripts never
      set one, and the stock string metatable has no arithmetic events.
    * `TRUSTING` = PURE: identical to `NO_METAMETHOD` -- TRUSTING only
      licenses reordering table *reads*, and this row has none left. Entailed,
      no extra runtime condition.

    `may_error` stays True in every mode: `luaG_aritherror` (`lvm.c:336`)
    fires on a non-coercible operand with no metamethod anywhere in sight.
    """
    from pyluadec.lift.effects import Effect, EffectMode, analyze
    from pyluadec.lift.opcodes import Op, decode
    for op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD, Op.POW):
        ri = decode(int(op) | (1 << 6) | (3 << 14) | (2 << 23), pc=0)
        assert analyze(ri, EffectMode.STRICT).effect is Effect.ARBITRARY, op
        assert analyze(ri, EffectMode.NO_METAMETHOD).effect is Effect.PURE, op
        assert analyze(ri, EffectMode.TRUSTING).effect is Effect.PURE, op
        for mode in EffectMode:
            assert analyze(ri, mode).may_error, (op, mode)
            assert analyze(ri, mode).reads == frozenset({2, 3}), (op, mode)


def test_mode_difference_getglobal():
    """GETGLOBAL: ARBITRARY -> READ_HEAP -> PURE.

    What must be TRUE of the runtime:

    * `STRICT` = ARBITRARY: nothing. `lvm.c:432-439` wraps `cl->env` and calls
      `luaV_gettable`, so an `__index` on the globals table runs arbitrary
      code. (This is not hypothetical for a game engine: a sandbox that
      resolves unknown globals through `__index` is a standard trick.)
    * `NO_METAMETHOD` = READ_HEAP: the environment table must have no
      `__index`. Then this is one raw `luaH_get` on a table -- a heap read,
      and nothing more. Note `cl->env` is *always* a table (`sethvalue`), so
      unlike GETTABLE there is no type-error path: `may_error` is False in
      every mode.
    * `TRUSTING` = PURE: additionally, no store to `_G` may intervene. The
      corpus contradicts this: 892 `SETGLOBAL` sites over 108 global names
      that are also read, and 29 protos read *and* write the same global name.
      `# UNARGUED`, and a pass that wants it must prove absence of stores over
      the specific region.
    """
    from pyluadec.lift.effects import Effect, EffectMode, analyze
    from pyluadec.lift.opcodes import Op, decode
    ri = decode(int(Op.GETGLOBAL) | (4 << 6) | (7 << 14), pc=0)
    assert analyze(ri, EffectMode.STRICT).effect is Effect.ARBITRARY
    assert analyze(ri, EffectMode.NO_METAMETHOD).effect is Effect.READ_HEAP
    assert analyze(ri, EffectMode.TRUSTING).effect is Effect.PURE
    for mode in EffectMode:
        assert not analyze(ri, mode).may_error, mode
        assert analyze(ri, mode).reads == frozenset(), mode
        assert analyze(ri, mode).writes == frozenset({4}), mode


# ---------------------------------------------------------------------------
# 4. The default-mode decision, as a test.
# ---------------------------------------------------------------------------


def test_strict_is_the_default_and_the_only_mode_in_use():
    """STRICT stays the default, and nothing in `src/` selects a looser mode.

    The decision (M4 task 11, documented in `structured-pipeline.md`): keep
    `STRICT` as the pipeline-wide default. The census makes `NO_METAMETHOD` a
    *permitted per-pass opt-in* for M5, scoped to script-constructed tables;
    it does not make it a safe global default, because the engine values that
    dominate the corpus's table reads are exactly what the census cannot see.
    `TRUSTING` is not recommended at all -- see
    `test_trusting_moves_only_four_rows_below_no_metamethod`.

    This test is the enforcement: if a later change starts lifting the whole
    corpus under a looser mode, it has to delete this test and say why.
    """
    import inspect
    from pyluadec.lift import lift_proto
    from pyluadec.lift.effects import EffectMode

    assert inspect.signature(lift_proto).parameters["mode"].default is EffectMode.STRICT

    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "effects.py" and path.parent.name == "lift":
            continue          # the table itself names all three modes
        text = path.read_text(encoding="utf-8")
        for name in ("EffectMode.NO_METAMETHOD", "EffectMode.TRUSTING"):
            if name in text:
                offenders.append((str(path.relative_to(SRC)), name))
    assert offenders == [], (
        f"a looser effect mode is selected in src/: {offenders}. That is a "
        f"default-mode change and needs the argument in "
        f"docs/runbooks/structured-pipeline.md updated with it.")

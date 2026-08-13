"""Static interaction surface of one proto (M6 task 3).

M6's Class-1 bet, stated by the project owner: a story-fragment proto's only
channels to the outside world are (a) calls to stub functions that display
options and read user actions, and (b) reads of global tables -- and **even
when the proto is not perfectly reconstructed, extracting WHICH table keys it
reads is easy, because those keys are string constants rather than values
built at runtime**. If that holds, Task 7 can enumerate the input space
(stub returns x global-table values) and drive both sides exhaustively.

This module is the measurement. `dynamic_reads` is deliberately NOT
bookkeeping: it counts the table reads whose key is *not* a constant, i.e.
exactly the sites that falsify the bet. Every other counter here exists so
that a site cannot silently disappear from the accounting -- see "Why so many
counters" below.

## What it does

One pass per basic block over the LIR, tracking a *provenance path* for each
register: `R[a] -> (b"gameSave",)` after `GETGLOBAL a K"gameSave"`, and
`(b"gameSave", b"save")` after a constant-key read off that register. A table
access whose base register carries a depth-1 path is attributed to that global
name; anything else is counted as unattributed. Provenance is dropped whenever
an instruction writes the register (`InstrEffects.writes`, reused rather than
respelled -- see below) and the whole map is dropped on `writes_open`, the
`R[base..top)` window whose extent is a runtime value.

**Block-local, not a fixed point, and that is a measured choice.** A full
forward dataflow with intersection-meet over predecessors was built against
*this* module (not a sketch) and run over the whole corpus, 2026-08-13: it
moved **0** of the 11910 table-read sites, **1** of 1667 write sites and
**4** of 44812 call sites. `lparser.c` builds `a.b` inside one expression, so
the `GETGLOBAL`/`GETTABLE` pair is essentially always adjacent and never
crosses a block boundary. The fixed point is not worth its cost or its
subtlety, so this pass does not have one; a block's entry state is empty.

**`MOVE` provenance propagation is deliberately absent** for the same reason:
adding `prov[a] = prov[b]` on `MOVE` moved **0** sites of any kind on the
corpus (measured the same session). `local t = g; t.k` compiles to
`GETGLOBAL R0; GETTABLE R1 R0 K` with no `MOVE` at all, so the rule has no
reaching shape here and would be an unproven guard.

## A constant key does not have to be an RK operand (measured, not assumed)

The first version of this module read "key is a constant" as "the key operand
has the RK bit set", and the corpus falsified it immediately: `snr_common.lua`'s
main chunk reported **209 of 209** table reads as `dynamic_reads`, all of them
of the shape

    GETGLOBAL R0, K420   ; "cardSort"
    LOADK     R1, K5     ; 1.0
    GETTABLE  R0, R0, R1

which is `cardSort[1]` -- a compile-time constant key that simply could not be
encoded in the 9-bit RK operand. `lcode.c::luaK_exp2RK` falls back to
`luaK_exp2anyreg` in two cases: a `VK` operand whose constant INDEX exceeds
`MAXINDEXRK` (255), and a `VKNUM`/`VTRUE`/`VFALSE`/`VNIL` operand created when
the function ALREADY holds more than 255 constants (that arm tests `fs->nk`,
the running total, not the index). `snr_common`'s main chunk has 920 constants,
so every numeric literal key in it takes the register path.

So the pass also tracks `LOADK`-defined registers as constants. Measured effect
over the whole corpus (delete the two lines in `rk_key` and re-run the dump):
`dynamic_reads` 1136 -> 880, `dynamic_writes` 651 -> 66, and it also recovers
59 attributed reads, 65 attributed writes and 8 table-key call sites -- long
constant indices push STRING keys through the same register path, so this is
not only about numeric keys. Reporting the unfixed figure would have overstated
the Class-1 obstacle by 29% on reads and by a factor of ten on writes.

A census of what defines the remaining non-constant key registers (block-local
last writer, 2026-08-13) is the evidence that nothing else of this kind is
hiding. It covers the **946** sites that are still register-keyed after
`LOADK` tracking -- 880 reads: `GETTABLE` 462, live-in 292, `GETUPVAL` 65,
`ADD` 44, `CONCAT` 14, `SUB` 3; and 66 writes: live-in 29, `GETTABLE` 25,
`GETGLOBAL` 12. (An earlier revision said "all 1787 sites"; 1787 = 1136 + 651
is the register-keyed population *before* `LOADK` tracking, a different set.)

**`LOADBOOL` and `LOADNIL` never define a key register** -- true over both
populations, the 946 above and the 1787 before -- which is why they are not
tracked here (`t[nil]` is a runtime error in Lua 5.1 and `t[true]` is exotic);
adding them would be an unreachable rule.

## Reuse: `lift/effects.py` answers "what does this write"

Register invalidation reads `InstrEffects.writes` / `.writes_open` from the
38-opcode effect table rather than re-deriving per-opcode write sets. That
table is the project's axiom layer, already checked against `lvm.c` row by row
and pinned by two consistency gates. The only opcode facts spelled here are
the ones the effect table does not carry because they are about *operands*,
not registers: which operand of `GETTABLE`/`SETTABLE`/`SELF` is the key, and
which constant index `GETGLOBAL`/`SETGLOBAL` names. Those come from
`lopcodes.h` field layout via `opcodes.py` (`isk`/`indexk`), the single
existing spelling.

## Why so many counters

`table_key_reads` is a `frozenset[tuple[bytes, bytes]]`, so three whole classes
of table read cannot appear in it: a non-constant key, a constant key that is
not a string (`arr[1]`), and a constant string key on a base with no depth-1
global provenance. If the only published number were the set's size, those
sites would vanish and the "keys are string constants" claim would look
stronger than the corpus supports. Each has its own counter and the identity

    read_sites == attributed_reads + unattributed_reads
                  + dynamic_reads + nonstring_key_reads

is asserted per proto over the whole corpus by `tests/test_footprint.py`.
Writes and calls carry the same shape.

### What the 2450 `unattributed_reads` actually are

This matters to whoever enumerates an input space from these sets, so it is
measured rather than illustrated. Every one of the 2450 traced back to the
root of its base register's chain (2026-08-13, all 229 files):

| root of the base register                     | sites | share  |
|-----------------------------------------------|-------|--------|
| `GETUPVAL`                                    |  1793 | 73.2%  |
| chain through a non-extending `GETTABLE`      |   530 | 21.6%  |
| live-in (parameter or local)                  |   105 |  4.3%  |
| depth-2 global chain (`a.b.c`'s second hop)   |    12 |  0.5%  |
| `NEWTABLE`                                    |    10 |  0.4%  |
| **call result**                               | **0** | **0%** |

An earlier revision of this section led with "the table came from a call
result" -- a cause with **zero** instances. The 530 splits 306 (the
intervening `GETTABLE` had a dynamic key) + 224 (it had a non-string constant
key, e.g. `cardSort[1].foo`); both stop the chain because provenance is only
extended through a constant STRING key.

**The dominant slice, decomposed -- and it does NOT collapse to one answer.**
All 1793 resolve to their parent's `CLOSURE` binding: the binding
pseudo-instruction is `MOVE` in **1793/1793** (never `GETUPVAL`), **0 of 1793**
bind a register carrying depth-1 global provenance at the `CLOSURE` site, and
the bound register was last written by `NEWTABLE` in **100%** of cases. So no
`GETUPVAL`-rooted read names a global *directly*. But the 1793 come from only
**10 distinct captured tables**, and they split three ways:

| group                                              | sites | what it is |
|----------------------------------------------------|-------|------------|
| top-level `local v0 = {}` (5 files, `main` R0)      |   953 | chunk-private state table |
| constructor `self` returned and then `SETGLOBAL`-ed |   601 | **globally reachable, one step out** |
| `snr_mainmenu` `main` R1, a reused scratch register |   239 | chunk-private, but not "the table at line 1" |

- **953 (53.2%) are safely excludable.** `snr_mainmenu`/`snr_novel`/
  `snr_graphic`/`snr_memory`/`snr_music` `main` R0, the `local v0 = {}` that is
  literally line 1 of the predecessor's `snr_mainmenu.lua`. Measured: across
  those five chunks the register's ONLY uses are table-base reads/writes and
  `CLOSURE` capture -- no `SETGLOBAL`, no `RETURN`, no call argument, no
  comparison. Nothing outside the chunk can reach the table.
- **601 (33.5%) are nameable one inter-proto step out**, and must NOT be
  written off. They are the `self` of four constructors in `snr_common.lua`
  (`main_25`/`main_74`/`main_76`/`main_77`, each `NEWTABLE R0` at pc 1 and
  `RETURN R0 2` at its last pc). The main chunk then does, verbatim per
  constructor, `GETGLOBAL <Class>; GETTABLE _, _, K"new"; CALL; SETGLOBAL
  <instance>` -- yielding the globals `oHour`, `systemOption`, `systemConfig`
  and `oCard`. A key read off the upvalue inside those closures IS a key of a
  named global table; only the intra-`CLOSURE` analysis above cannot see it.
- **239 (13.3%)** are `snr_mainmenu`'s `main` R1, a scratch register
  successively reloaded with `{}` sub-tables; it is also an `EQ` operand and a
  `SETTABLE` value, so it is chunk-private but not the same shape as the 953.

**Caveat that must travel with the exclusion claim.** The four constructor
globals above are read but never written as tables anywhere in the corpus: 0
`table_key_writes` on `oCard`/`systemOption`/`systemConfig`/`oHour` against 933
read-pair instances (`oCard` 884, `systemConfig` 28, `oHour` 19,
`systemOption` 2). That makes exclusion safe *within the corpus* -- and the
corpus is a weak oracle here, exactly as `lift/effects.py`'s mode calibration
warns: these globals live in the engine's world too, and no census of the 229
scripts can rule out an engine-side write.

(The `1248` figure an earlier revision reported as "attributes 1248 (69.6%)"
was a miscount of scope, not of value: attribution is 100%, and 1248 is the
subset whose base register is defined by `GETUPVAL` *immediately*, against 545
reached by chaining through a constant-string-key `GETTABLE`. 1248 + 545 =
1793.)


## Deliberate exclusions, and their measured size

- `SETLIST` writes consecutive INTEGER keys into a freshly-built table
  (`lvm.c:697-718`, raw `luaH_setnum`). It is never a named-key write, so it
  is outside the pair sets; `setlist_sites` records it so "SETTABLE and
  SETGLOBAL are the only named-key writers" is auditable rather than assumed.
  92 sites corpus-wide.
- Upvalue reads/writes (`GETUPVAL`/`SETUPVAL`) carry no name in this corpus --
  all 1944 protos are debug-stripped, so `Proto.upvalues` is empty everywhere
  (M6 task 2's census). A register loaded from an upvalue therefore gets no
  provenance and its table accesses land in `unattributed_*`. This is the
  single largest such class -- 1793 of 2450, quantified in the table above,
  and not a footnote.
- Method receivers: `SELF a b c` also copies `R[b]` into `R[a+1]`, and
  propagating provenance there was considered and dropped -- `R[a+1]` is
  immediately consumed as the call's first argument, so no shape reads it as
  a table base, and a line with no reaching shape is an unproven guard.

## Red line

Nothing here decodes. Constant-pool strings are compared and stored as
`bytes`; the identifier-shaped-ASCII presentation rule lives in
`scripts/footprint_dump.py`, which is a printing layer.

## Not re-exported from `pyluadec.lift`

Deliberately: this module consumes `pyluadec.cfg`, which itself imports
`pyluadec.lift.lift`. Adding it to `lift/__init__.py` would make merely
importing the package pull the whole `lift -> cfg -> lift` cycle in, and the
package init would stop describing the dependency direction. Import it as
`from pyluadec.lift.footprint import proto_footprint`.
"""
from __future__ import annotations

from dataclasses import dataclass

from pyluadec.cfg.blocks import build_cfg
from pyluadec.ingest.proto import Const

from .lift import LirFunction
from .opcodes import Op, indexk, isk

_MISSING = object()      # "no constant known for this register" sentinel;
                         # `None` is a legitimate Lua constant (nil).


@dataclass(frozen=True)
class Footprint:
    """One proto's static interaction surface. All names are raw `bytes`.

    The five sets named in the M6 plan are `global_reads`, `global_writes`,
    `table_key_reads`, `table_key_writes` and `calls`; `table_key_calls` was
    added because `a.b()` and `a:b()` are callee sites whose name is a
    `(global, key)` pair, and `calls` is typed for depth-1 global names only.
    """

    # -- the surface itself ------------------------------------------------
    global_reads: frozenset[bytes]
    global_writes: frozenset[bytes]
    table_key_reads: frozenset[tuple[bytes, bytes]]
    table_key_writes: frozenset[tuple[bytes, bytes]]
    calls: frozenset[bytes]
    table_key_calls: frozenset[tuple[bytes, bytes]]

    # -- read accounting (SITE counts, not deduped) ------------------------
    read_sites: int
    attributed_reads: int          # constant string key on a depth-1 global base
    unattributed_reads: int        # constant string key, base not a depth-1 global
    dynamic_reads: int             # key is a register, not a constant
    nonstring_key_reads: int       # key is a constant but not a string

    # -- write accounting --------------------------------------------------
    write_sites: int
    attributed_writes: int
    unattributed_writes: int
    dynamic_writes: int
    nonstring_key_writes: int
    setlist_sites: int             # excluded from write_sites; see module doc

    # -- overlay, NOT partition members ------------------------------------
    # How many of the sites above resolved their key through a `LOADK`-defined
    # REGISTER rather than an RK constant operand (the >255-constant fallback
    # in `lcode.c::luaK_exp2RK`). A subset of attributed/unattributed/
    # nonstring, so these are deliberately absent from the accounting
    # identities; they exist so the size of that compiler artifact stays
    # visible instead of being silently folded into "constant".
    register_const_key_reads: int
    register_const_key_writes: int

    # -- call accounting ---------------------------------------------------
    call_sites: int
    global_call_sites: int
    table_key_call_sites: int
    unattributed_calls: int


def _const_str(fn: LirFunction, idx: int) -> bytes | None:
    """`K[idx]` if it is a string constant, else None.

    Out-of-range is a real possibility for hand-assembled or corrupt bytecode
    (`decode()` validates the opcode, not the operand), and this module is a
    census that must be total over whatever it is handed.
    """
    ks = fn.proto.constants
    if not (0 <= idx < len(ks)):
        return None
    k = ks[idx]
    return k if isinstance(k, bytes) else None


def proto_footprint(fn: LirFunction) -> Footprint:
    """The static interaction surface of `fn` alone -- NOT of its subprotos.

    A `CLOSURE` site contributes nothing here; the caller walks the proto tree
    (`pipeline.walk_proto_paths`) and takes one footprint per proto, which is
    what keeps the per-proto distributions in `corpus/observation/
    footprints.json` meaningful.
    """
    cfg = build_cfg(fn)

    global_reads: set[bytes] = set()
    global_writes: set[bytes] = set()
    key_reads: set[tuple[bytes, bytes]] = set()
    key_writes: set[tuple[bytes, bytes]] = set()
    calls: set[bytes] = set()
    key_calls: set[tuple[bytes, bytes]] = set()

    n_read = n_read_attr = n_read_unattr = n_read_dyn = n_read_nonstr = 0
    n_write = n_write_attr = n_write_unattr = n_write_dyn = n_write_nonstr = 0
    n_setlist = 0
    n_call = n_call_global = n_call_key = n_call_unattr = 0
    n_regk_read = n_regk_write = 0

    def rk_key(operand: int, kregs: dict) -> tuple[object, bool]:
        """`(constant, came_from_a_register)` for an RK key operand.

        Returns `(_MISSING, False)` when the key is genuinely computed at
        runtime -- that is what `dynamic_*` counts.
        """
        if isk(operand):
            ks = fn.proto.constants
            i = indexk(operand)
            return (ks[i] if 0 <= i < len(ks) else _MISSING), False
        if operand in kregs:
            return kregs[operand], True
        return _MISSING, False

    for start in sorted(cfg.blocks):
        # Empty entry state per block: see the module docstring's measurement
        # of what a real fixed point would buy (0 read sites).
        prov: dict[int, tuple[bytes, ...]] = {}
        kregs: dict[int, Const] = {}
        for li in cfg.blocks[start].instrs:
            ri = li.ri
            op = ri.op
            # Read the operands' provenance BEFORE invalidating: `GETGLOBAL R0;
            # GETTABLE R0 R0 K` reuses one register, so invalidating first
            # would erase the very path this instruction is about. (Measured:
            # getting this order wrong drops attributed reads from 8002 to 0.)
            base_b = prov.get(ri.b)
            base_a = prov.get(ri.a)
            # Snapshot, for the same reason: `GETTABLE A B C` with `A == C` is
            # real luac output (the key temp is freed and immediately
            # reallocated as the destination), so this instruction's own write
            # must not erase the `LOADK` constant it is about to consume. Only
            # the three key-reading opcodes pay the copy.
            pre_kregs = dict(kregs) if op in (Op.GETTABLE, Op.SELF, Op.SETTABLE) else {}

            for w in li.effects.writes:
                prov.pop(w, None)
                kregs.pop(w, None)
            if li.effects.writes_open:
                # `R[a..top)`: the extent is a runtime value, so every register
                # from `a` up is unknown -- but registers BELOW `a` are
                # untouched and keep their provenance. All three opcodes that
                # can carry this flag (`CALL` C==0, `TAILCALL`, `VARARG` B==0)
                # open their window at `A`; that is asserted over the whole
                # opcode x operand grid by `tests/test_footprint.py::
                # test_every_writes_open_window_starts_at_operand_a`, so this
                # is a checked assumption rather than a fourth hand-copy of
                # `lvm.c`.
                #
                # Clearing the WHOLE map instead costs 3450 of 44812 call
                # sites (measured 2026-08-13: `unattributed_calls` 1677 ->
                # 5165), because `h(g())` leaves `h`'s own register below the
                # inner multret call's window.
                for r in [r for r in prov if r >= ri.a]:
                    del prov[r]
                for r in [r for r in kregs if r >= ri.a]:
                    del kregs[r]

            if op is Op.LOADK:
                ks = fn.proto.constants
                if 0 <= ri.bx < len(ks):
                    kregs[ri.a] = ks[ri.bx]
            elif op is Op.GETGLOBAL:
                name = _const_str(fn, ri.bx)
                if name is not None:
                    global_reads.add(name)
                    prov[ri.a] = (name,)
            elif op is Op.SETGLOBAL:
                name = _const_str(fn, ri.bx)
                if name is not None:
                    global_writes.add(name)
            elif op is Op.GETTABLE or op is Op.SELF:
                n_read += 1
                kv, from_reg = rk_key(ri.c, pre_kregs)
                n_regk_read += from_reg
                key = kv if isinstance(kv, bytes) else None
                if kv is _MISSING:
                    n_read_dyn += 1
                elif key is None:
                    n_read_nonstr += 1
                if key is not None:
                    if base_b is not None and len(base_b) == 1:
                        n_read_attr += 1
                        key_reads.add((base_b[0], key))
                    else:
                        n_read_unattr += 1
                    if base_b is not None:
                        prov[ri.a] = base_b + (key,)
            elif op is Op.SETTABLE:
                n_write += 1
                kv, from_reg = rk_key(ri.b, pre_kregs)
                n_regk_write += from_reg
                key = kv if isinstance(kv, bytes) else None
                if kv is _MISSING:
                    n_write_dyn += 1
                elif key is None:
                    n_write_nonstr += 1
                elif base_a is not None and len(base_a) == 1:
                    n_write_attr += 1
                    key_writes.add((base_a[0], key))
                else:
                    n_write_unattr += 1
            elif op is Op.SETLIST:
                n_setlist += 1
            elif op is Op.CALL or op is Op.TAILCALL:
                n_call += 1
                if base_a is None:
                    n_call_unattr += 1
                elif len(base_a) == 1:
                    n_call_global += 1
                    calls.add(base_a[0])
                elif len(base_a) == 2:
                    n_call_key += 1
                    key_calls.add((base_a[0], base_a[1]))
                else:
                    n_call_unattr += 1

    return Footprint(
        global_reads=frozenset(global_reads),
        global_writes=frozenset(global_writes),
        table_key_reads=frozenset(key_reads),
        table_key_writes=frozenset(key_writes),
        calls=frozenset(calls),
        table_key_calls=frozenset(key_calls),
        read_sites=n_read, attributed_reads=n_read_attr,
        unattributed_reads=n_read_unattr, dynamic_reads=n_read_dyn,
        nonstring_key_reads=n_read_nonstr,
        write_sites=n_write, attributed_writes=n_write_attr,
        unattributed_writes=n_write_unattr, dynamic_writes=n_write_dyn,
        nonstring_key_writes=n_write_nonstr, setlist_sites=n_setlist,
        register_const_key_reads=n_regk_read,
        register_const_key_writes=n_regk_write,
        call_sites=n_call, global_call_sites=n_call_global,
        table_key_call_sites=n_call_key, unattributed_calls=n_call_unattr,
    )

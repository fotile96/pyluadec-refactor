"""Meta-observation pass over the corpus's hard protos (M6 task 4).

用法: PYLUADEC_CORPUS_DIR=... uv run python scripts/observation_classes.py
      (`--fresh` regenerates with an EMPTY observation store; it refuses to
       overwrite a file that carries observations unless `--force` is added)
产出: corpus/observation/classes.json（入库；生成数据，纪律同 corpus/ledger.jsonl）

This is a JOB, not a suite cost. The committed JSON is what the suite reads;
`tests/test_observation_classes.py::test_classes_json_is_a_reproducible_fixed_
point` is the ledger-ratchet-style guard that it is byte-reproducible from this
script.

## What it produces, and the two halves of every record

The project owner's framing for M6: the corpus's remaining hard protos are of
two kinds.

  * **Class 1, `choice-branch`** -- story fragments whose only channels to the
    outside are (a) calls to functions that display options and read the user's
    action and (b) reads of global table contents. Strict verification is
    tractable here because the read keys are string constants and the value
    domains are small.
  * **Class 2, `ui-keyloop`** -- the peripheral UI (main menu, CG and music
    galleries, settings screens), which polls arrow/action keys inside a loop.
    Harder, because a finite key sequence does not guarantee the loop halts.

Each candidate record has two halves, and the split is load-bearing:

  * `mechanical` -- **recomputed on every run** from the original bytecode, the
    committed ledger and the L1.75 behaviour probe. A regeneration may rewrite
    any of it. Nothing here is a judgement call; the class assignment itself is
    a rule over measured predicates (see `classify`), so it is mechanical too.
  * `observed`   -- **copied verbatim from the committed file**, keyed by
    `(file, proto_path)`. This is the review's verdict on the mechanical class
    plus a short ASCII note. A regeneration never invents, edits or drops one:
    it carries them across. `--fresh` drops them, which is how the mechanical
    half alone is shown to be a fixed point independent of the observations.

## Two fields whose NAME promises more than the field measures

Both are consumer traps rather than errors -- the values are what this module
computes, and the tests assert exactly that -- so they are documented here,
where a consumer reads, rather than renamed (a rename regenerates a committed
artifact). Recorded at the M6 wrap, task 13, with the figures measured
2026-08-14 at that tree.

  * **`loop_polls_per_iteration` does not mean "every iteration".** It is
    `bool(poll_loops(...)) or bool(in_loop_callees_reaching_poll)`, i.e. *a
    poll site lies **somewhere** in some natural loop's body* -- directly, or
    through an in-loop call to a callee that transitively reaches a poll. A
    poll inside a conditional arm of the body satisfies it and does not run
    every iteration. Under the stronger reading -- some loop has a poll site
    whose CFG block **dominates every latch** of that loop -- it holds for
    **116 of the 125** records that carry the flag (`choice-branch` 110/113,
    `ui-keyloop` 6/9, `neither` 0/3). The nine exceptions:
    `snr_common:main_71`, `snr_common:main_75`, `snr_e1_10_s:main_29`,
    `snr_e2_10_f:main_35`, `snr_e2_10_s:main_13`, `snr_graphic:main_4`,
    `snr_mainmenu:main_7`, `snr_s4_10_fb:main_16`, `snr_s6_10_s:main_19`. The
    conclusion the flag was measured for is unaffected either way -- the two
    interaction classes overlap on termination, so non-termination does not
    distinguish Class 2 -- because 110/113 `choice-branch` survives the
    stricter test too.
  * **`mechanical.footprint` is a 7-key PROJECTION** of `footprints.json`'s 23
    per-proto fields (`global_reads`, `table_key_reads`, `calls`,
    `table_key_calls`, `dynamic_reads`, `read_sites`, `call_sites`). The two
    honesty counters a consumer most needs are **not** joined:
    `unattributed_calls` and `unattributed_reads`. Measured over the 156
    candidates: **142 have `unattributed_calls > 0`, 908 sites in total**, and
    127 have `unattributed_reads > 0`, 1171 sites. A consumer sizing a stub
    surface from `footprint` alone will therefore under-count the call sites it
    has to stub; join `corpus/observation/footprints.json` by
    `(file, proto_path)` for the full record.

## Candidate selection (the brief's Step 1)

Two populations, unioned:

  * **leaf refusal sites** -- the non-`L3` ledger rows whose refusal originates
    in the proto's OWN body rather than in a descendant's. Three mechanical
    rules, one per `refusal_reason` kind (`structure.structured.ProtoCert.
    reason` is the vocabulary):
      - `structure:`   -- `build_sir` on this proto alone raises. Direct.
      - `reconstruct:` -- no non-`L3` descendant carries a byte-identical
        reason (the reconstructor's message has no path in it, so this is the
        available test).
      - `mismatch:`    -- the reason carries no ` at root/...` suffix, i.e.
        `verify.normalize._cmp`'s first difference is in this proto's own
        field rather than a subproto's.
    Cross-checked in `docs/reports/m6-observation.md` §2 against an independent
    experiment (replace every subproto with a trivial stub, re-print, see
    whether the same refusal survives): the two agree on all 48 non-`L3` rows.
  * **event-cap dominant protos** -- for each file whose L1.75 behaviour probe
    run ends in `CAP`, the proto bound to the global function under whose
    invocation the most events were recorded. The probe emits `I|<name>`
    before each invocation, so the attribution is read straight off the trace;
    the name is resolved to a `proto_path` through the chunk's own
    `CLOSURE`/`SETGLOBAL` pairs.

## The two call vocabularies, and why they are what they are

`POLL_GLOBALS` is `pressButton` and nothing else. Measured 2026-08-13 over all
229 files: `keyWait` and `functionButton` are the only other candidates, and
neither is an engine key poll --

  * `keyWait` is DEFINED BY THE CORPUS (`snr_common.lua`'s global `keyWait`
    resolves to `main_81` through that chunk's own `CLOSURE`/`SETGLOBAL` pair),
    and `main_81` is itself a `pressButton` poll loop. So it is a Class-2 proto,
    not a poll primitive; a caller of `keyWait` delegates its poll rather than
    running one.
  * `functionButton` registers a handler (`unsetConfigButton` / `setConfigButton`
    in `snr_common.lua`'s `SystemConfig`), never returns a key state, and its
    result is never branched on.

`OPTION_CALLEES` -- the "stub functions that display options and read the user's
action" -- is likewise not guessed. Every one of them resolves, through the
corpus's own definitions, to a proto in `snr_common.lua` (uniqueness of each
name corpus-wide verified):

    comDlgSelectItem             -> main_29      6 loop headers, polls directly
    comDlgYesNoSel               -> main_27      1 loop header,  polls directly
    comDlgStorylineSkip          -> main_28      1 loop header,  polls directly
    comSelectMap                 -> main_71      6 loop headers, polls directly
    comDlgYesNo                  -> main_26      NO loop: 8 instructions,
                                                 TAILCALL to comDlgYesNoSel
    oCard.selectCardObj          -> main_77_17   NO loop: 48 instructions,
                                                 self.cardModeSelect at pcs 22-28
    oCard.selectCardNotCancelObj -> main_77_18   NO loop: same shape

**The finding the classification rests on, stated to what actually holds: the
option channel bottoms out in CORPUS-DEFINED code rather than in an engine
primitive.** A first version of this docstring said all seven "are Class-2 poll
loops", and the corpus refuted it -- three of the seven have **zero** natural
loops, and two of those three are the callees for 105 of the 113 Class-1
candidates. They reach a poll one hop further: `comDlgYesNo` tail-calls
`comDlgYesNoSel`, and both `oCard` selectors call `cardModeSelect`
(`main_77_24`), which does poll directly.

The structural point survives, and it is the one Tasks 7 and 8 need: the class
boundary falls on the corpus's own module boundary, so a Class-1 proto can
treat an option call as an uninterpreted oracle over a small value domain
precisely because what is behind it is somebody else's problem in the same
corpus.

The generator does not hard-code those resolutions: it rebuilds the call graph
(`_call_graph`) from `CLOSURE`/`SETGLOBAL` and `CLOSURE`/`SETTABLE` pairs each
run and records the resolved target in the summary, so a wrong entry in
`OPTION_CALLEES` shows up as a `null` target rather than as silence.

**The list is incomplete, by four protos that pass its own test** (defined in
the corpus, reached by a caller, and themselves reaching a poll):
`comStorySceneEnd` = `main_55`, `SystemConfig.confirm` = `main_76_7`,
`SystemConfig.ConfigMain` = `main_76_2`, `ObjectCard.cardModeSelect` =
`main_77_24`. Only the first is a global name a list edit could add, and
measured 2026-08-13 **no candidate of the 162 calls it**, so adding it would
change nothing; the other three are reached as `self.<method>()` and need the
call graph rather than this list. Recorded rather than patched.

## Channels and input space (the brief's Step 3b)

A CHANNEL of a proto is a dotted access path whose value reaches a branch
decision (`EQ`/`LT`/`LE` against a constant, or `TEST`/`TESTSET`) and is rooted
at a global read or a call result -- exactly the owner's (a) and (b). Its
DOMAIN SIZE is `|distinct const_lit RENDERINGS compared against| + 1` (one
witness for "none of the above"), or 2 when it is compared against no constant
at all -- a truth test, or a comparison against another register. The
INPUT SPACE is the product, and a proto is `drivable` iff that product is at
most `BUDGET` (4096, the figure the plan names).

**The `const_lit` rendering is a fourth limit of `input_space`, and it is the
one that bites hardest.** This definition used to read "`|distinct constants
compared against| + 1`", which is FALSE whenever a channel meets two or more
distinct strings (or two distinct non-integer numbers): `const_lit` collapses
every string to `"str"` and every non-integer number to `"num"`, deliberately,
because that is how this file stays free of corpus text. So a channel compared
against N different scene names is ONE element here and N (+1) to anything
that has to SUPPLY a value -- `x == "a"` does not take the `== "b"` arm.

Re-derived 2026-08-14 against `scripts/probe_enum.py::channels_of`, which
keeps the distinct constants (as `bytes`, never published):

  * corpus-wide **1944 protos: 26 differ**; within budget **1940 -> 1936**.
  * candidates **162: 23 differ**; within budget **159 -> 155**.
  * by class: **`choice-branch` 110/113 -> 106/113**; `ui-keyloop` 11/11 and
    `neither` 38/38 unchanged.
  * worst ratios: `snr_s7_10_f.lua:main_53` 4 -> 118 (**29.5x**),
    `snr_s2_10_s.lua:main_60` 240 -> 5280 (22.0x),
    `snr_s3_10_s.lua:main_59` 3456 -> 72576 (21.0x),
    `snr_s4_10_s.lua:main_58` 1152 -> 23616 (20.5x).

Both figures are correct about their own question -- `input_space` sizes the
BRANCH-OUTCOME space, `channels_of` sizes the ENUMERABLE space -- and a
consumer that has to drive a proto must re-derive with the latter. `channels`
now records both: `rec["cmp"]` (renderings, what this file publishes) and
`rec["raw"]` (the distinct constants, in memory only).

The provenance pass is a forward DATAFLOW, not the block-local pass
`lift/footprint.py` uses -- see `channels`' docstring for the measurement that
forced the difference (block-locality was wrong on 110 of 162 records, always
downward, worst ratio 36x). It also tracks paths of ARBITRARY depth
(`gameSave.myCard.[9].hold`) and call results, neither of which the footprint
needs.

**`input_space` is a PER-ITERATION figure for both classes.** An earlier
revision of this docstring called it per-CALL for Class 1 -- "fix one value per
channel, run once" -- and the corpus falsified that flat: measured 2026-08-13,
**113 of 113** `choice-branch` candidates have at least one option call INSIDE
a natural loop, and 112 of 113 have all of them inside one (258 of 260 option
call sites overall). A story fragment re-polls its option channel per iteration
exactly as a UI screen re-polls the key, only through `oCard.selectCardObj` /
`comDlg*` instead of `pressButton`. Each option call site carries `in_loop` so
this is checkable per site rather than taken on trust. What separates the
classes is therefore the TERMINATION ARGUMENT, not the shape of the input.

Three further limits of `input_space` (the `const_lit` collapse above is a
fourth), all measured, none closed:

  * **Parameters are not channels.** A proto that branches on an argument
    (e.g. `snr_common.lua:main_75`, `numparams=1`, branching on it at four
    pcs) has that dimension missing. The figure is per-argument-vector.
  * **Comparisons against another register** contribute no domain; the channel
    falls back to a floor of 2. Counted per record in `register_comparisons`
    and corpus-wide in `corpus_register_comparisons`.
  * **Independence is assumed.** A product treats channels as freely
    combinable. Measured counter-example: `snr_crd_104.lua:main_16` reads 14
    distinct `gameSave.myCard[N].hold` flags, each guard's failing arm ending
    in `GETGLOBAL quit; CALL`. The CFG really does reconverge (so 2^14 paths
    are statically reachable) but if `quit` does not return -- and no corpus
    file ever `SETGLOBAL`s `quit`, so the bytecode cannot say -- the semantic
    outcome space is 15, not 16384.

## Red line

Every string in the output is an ASCII identifier or a structural marker.
Name emission reuses `scripts/footprint_dump.py`'s rule verbatim (verbatim iff
`0x20..0x7e` and identifier-shaped, else `{"nonascii": "<hex>"}` built with
`.hex()`, never via `.decode()`), rather than respelling it. Numeric table keys
become `{"index": n}`, runtime keys `{"dynamic": true}`, call results
`{"call": true}` -- all structural, none derived from corpus text.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.footprint_dump import emit_name  # noqa: E402

VERSION = "m6-classes-v1"
BUDGET = 4096

POLL_GLOBALS = ("pressButton",)

# Marker for a call base that came from an upvalue rather than a global.
# Deliberately NOT identifier-shaped, so it can never collide with a corpus
# name: `footprints.json` measured `non_identifier_names == 0` over all 229
# files, i.e. every global name, table key and callee name in the corpus IS an
# ASCII identifier. It never reaches the emitted JSON as a name -- option
# callees are matched by exact tuple and this tuple matches none of them.
SELF_BASE = b"<upvalue>"

# (base, key) is a method call; a bare name is a global call.
OPTION_CALLEES = (
    ("comDlgSelectItem",),
    ("comDlgYesNo",),
    ("comDlgYesNoSel",),
    ("comDlgStorylineSkip",),
    ("comSelectMap",),
    ("oCard", "selectCardObj"),
    ("oCard", "selectCardNotCancelObj"),
)

# Instance global -> the constructor proto whose SETTABLE closures are its
# methods. Measured at M6 task 3 (the "601 sites" group): each constructor does
# `NEWTABLE R0` at pc 1 and `RETURN R0 2` at its last pc, and the main chunk
# then runs `<Class>.new()` and SETGLOBALs the result under these names.
INSTANCE_GLOBALS = {
    "systemOption": ("snr_common.lua", "main_74"),
    "systemConfig": ("snr_common.lua", "main_76"),
    "oCard": ("snr_common.lua", "main_77"),
    "oHour": ("snr_common.lua", "main_25"),
}


# ---------------------------------------------------------------- name emission

def emit_seg(seg) -> object:
    """One segment of a dotted access path, as ASCII-only structural JSON."""
    kind, val = seg
    if kind == "k":
        return {"key": emit_name(val)}
    if kind == "i":
        return {"index": val}
    if kind == "d":
        return {"dynamic": True}
    return {"call": True}


def emit_path(path) -> list:
    return [emit_seg(s) for s in path]


def _assert_ascii(node, where="doc") -> None:
    """Every string anywhere in the document is printable ASCII.

    The red line is enforced at each emission site (`emit_name`, `emit_seg`,
    `path_text`, `_callee_text`), but a single new field that interpolates a
    constant would slip past all of them. This is the belt: it walks the
    finished document and refuses to write a file that carries a byte outside
    `0x20..0x7e`. It is a guard against a FUTURE edit, so it is DEFENSIVE by
    construction on today's corpus -- `footprints.json` measured
    `non_identifier_names == 0` over all 229 files, so nothing here can
    currently reach it. `tests/test_observation_classes.py` reaches it with a
    synthetic document instead.
    """
    if isinstance(node, str):
        bad = [c for c in node if not (0x20 <= ord(c) <= 0x7e)]
        if bad:
            raise AssertionError(
                f"non-ASCII string at {where}: {len(bad)} byte(s) outside "
                f"0x20..0x7e")
    elif isinstance(node, dict):
        for k, v in node.items():
            _assert_ascii(k, where)
            _assert_ascii(v, f"{where}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _assert_ascii(v, f"{where}[{i}]")


def _callee_text(name: tuple[bytes, ...]) -> str:
    """Dotted callee name, through `emit_name` so the red line holds."""
    parts = []
    for s in name:
        n = emit_name(s)
        parts.append(n if isinstance(n, str) else "0x" + n["nonascii"])
    return ".".join(parts)


def path_text(path) -> str:
    """A compact ASCII rendering for the human-facing evidence strings.

    Only ever built from segments that already passed `is_ascii_identifier`
    (or are structural markers), so it carries no corpus text; a non-identifier
    key would render as its hex form, same as `emit_name`."""
    out = []
    for kind, val in path:
        if kind == "k":
            n = emit_name(val)
            out.append("." + (n if isinstance(n, str) else "0x" + n["nonascii"]))
        elif kind == "i":
            out.append(f"[{val}]")
        elif kind == "d":
            out.append("[*]")
        else:
            out.append("()")
    s = "".join(out)
    return s[1:] if s.startswith(".") else s


# ---------------------------------------------------------------- static passes

_CFG_CACHE: dict[int, object] = {}


def cfg_of(proto):
    """`build_cfg(lift_proto(proto))`, memoized for this run.

    Three passes here want the same CFG for the same proto (`scan_proto`,
    `channels`, `poll_loops`), and the whole-corpus lift is the dominant cost
    of the job (1.07s of the job's 2.4s, measured 2026-08-13).

    **The entry holds a reference to the proto, and that is load-bearing, not
    tidiness.** An id-keyed cache that does not pin its key is wrong the moment
    the caller drops a proto: CPython reuses the address and the next proto
    allocated there gets served somebody else's CFG. That is not hypothetical
    here -- the first version omitted the reference and a scratch census that
    loaded one file at a time crashed inside `GETGLOBAL` handling with
    `IndexError: tuple index out of range`, because it was indexing one
    proto's constants with another proto's operand. Pinning makes the key
    unrecyclable for the cache's lifetime, so a hit is exact; `Proto` is frozen,
    so it also cannot go stale.
    """
    from pyluadec.lift import lift_proto
    from pyluadec.cfg.blocks import build_cfg
    hit = _CFG_CACHE.get(id(proto))
    if hit is None:
        hit = (proto, build_cfg(lift_proto(proto)))
        _CFG_CACHE[id(proto)] = hit
    return hit[1]


def scan_proto(proto):
    """One block-local pass: `(call sites, global defs, method defs)`.

    * call sites -- `[(pc, (name,) | (base, key))]` in pc order, for `CALL` /
      `TAILCALL` whose callee register carries a resolvable dotted path.
    * global defs -- `{name: subproto index}` from `CLOSURE Ra, Bx` ...
      `SETGLOBAL Ra`.
    * method defs -- `{key: subproto index}` from `CLOSURE Rc, Bx` ...
      `SETTABLE Ra Kb Rc`.

    Invalidation goes through `InstrEffects.writes` / `.writes_open`, the same
    axiom-layer table `lift/footprint.py` reuses, rather than a hand-written
    per-opcode write set; and each instruction's operands are read from a
    snapshot taken BEFORE its own writes are applied, because
    `GETGLOBAL R0; GETTABLE R0 R0 K` reuses one register (the measurement
    behind that rule is in `lift/footprint.py`'s docstring: getting the order
    wrong drops attributed reads from 8061 to 0).
    """
    from pyluadec.lift.opcodes import Op, isk, indexk
    ks = proto.constants
    cfg = cfg_of(proto)
    sites: list[tuple[int, tuple[bytes, ...]]] = []
    gdef: dict[bytes, int] = {}
    mdef: dict[bytes, int] = {}
    for start in sorted(cfg.blocks):
        prov: dict[int, tuple[bytes, ...]] = {}
        clos: dict[int, int] = {}
        for li in cfg.blocks[start].instrs:
            ri, op = li.ri, li.ri.op
            pre_prov, pre_clos = dict(prov), dict(clos)
            for w in li.effects.writes:
                prov.pop(w, None)
                clos.pop(w, None)
            if li.effects.writes_open:
                for r in [r for r in prov if r >= ri.a]:
                    del prov[r]
                for r in [r for r in clos if r >= ri.a]:
                    del clos[r]
            if op is Op.CLOSURE:
                clos[ri.a] = ri.bx
            elif op is Op.SETGLOBAL:
                n = ks[ri.bx]
                if ri.a in pre_clos and isinstance(n, bytes):
                    gdef.setdefault(n, pre_clos[ri.a])
            elif op is Op.SETTABLE:
                if not isk(ri.c) and ri.c in pre_clos and isk(ri.b):
                    k = ks[indexk(ri.b)]
                    if isinstance(k, bytes):
                        mdef.setdefault(k, pre_clos[ri.c])
            elif op is Op.GETUPVAL:
                # `self.method()` inside a constructor's closure compiles to
                # `GETUPVAL Rx,u; GETTABLE Rx Rx K"name"; CALL Rx`, and the
                # base is an upvalue, not a global. Seeding a sentinel here is
                # what makes that an edge at all. Measured cost of NOT doing
                # it: `oCard.selectCardObj` (`main_77_17`) calls
                # `cardModeSelect` (`main_77_24`, a direct `pressButton`
                # caller) at pcs 22-28 and the graph saw nothing, so the
                # option callee behind 105 of 113 Class-1 candidates reported
                # `reaches_poll == False`.
                prov[ri.a] = (SELF_BASE,)
            elif op is Op.GETGLOBAL:
                n = ks[ri.bx]
                if isinstance(n, bytes):
                    prov[ri.a] = (n,)
            elif op is Op.GETTABLE or op is Op.SELF:
                b = pre_prov.get(ri.b)
                if b is not None and isk(ri.c):
                    k = ks[indexk(ri.c)]
                    if isinstance(k, bytes):
                        prov[ri.a] = b + (k,)
            elif op is Op.CALL or op is Op.TAILCALL:
                b = pre_prov.get(ri.a)
                if b is not None:
                    sites.append((ri.pc, b))
    return sites, gdef, mdef


def _defs_and_calls(f: str, protos: dict):
    """Per file: global/method definitions, and each proto's callee names."""
    gdef: dict[bytes, tuple[str, str]] = {}
    by_path: dict[str, dict[bytes, str]] = {}
    methods: dict[str, dict[bytes, str]] = {}
    calls: dict[str, list[tuple[int, tuple[bytes, ...]]]] = {}
    for path, p in protos.items():
        sites, g, m = scan_proto(p)
        by_path[path] = {k: f"{path}_{bx}" for k, bx in g.items()}
        for k, bx in g.items():
            gdef.setdefault(k, (f, f"{path}_{bx}"))
        if m:
            methods[path] = {k: f"{path}_{bx}" for k, bx in m.items()}
        calls[path] = sites
    return gdef, methods, calls, by_path


def _call_graph(all_protos, gdefs, all_methods, all_calls):
    """Edges over `(file, proto_path)`, plus the set that reaches a poll."""
    poll = {n.encode() for n in POLL_GLOBALS}
    mdef: dict[tuple[bytes, bytes], tuple[str, str]] = {}
    for iname, (cf, cpath) in INSTANCE_GLOBALS.items():
        for k, path in all_methods.get(cf, {}).get(cpath, {}).items():
            mdef[(iname.encode(), k)] = (cf, path)
    # KNOWN UNDER-APPROXIMATION, and it is now smaller than it was. Round 0
    # built edges only for callees with GLOBAL-rooted provenance, so
    # `self.method()` was invisible and `protos_reaching_poll` read 331; with
    # the `SELF_BASE` seeding above it reads **443** (measured 2026-08-13).
    #
    # What is STILL invisible: a call through an upvalue-held LOCAL CLOSURE
    # (`GETUPVAL R0; CALL R0`), which needs the parent's `CLOSURE` binding
    # pseudo-instructions to resolve. Measured cost, over the nine `neither`
    # candidates an independent audit reclassified: five are now reached (at
    # 1, 1, 2, 4 and 4 hops) and **four are not** -- `snr_crd_102.lua:main_5`,
    # `snr_s0_10_f.lua:main_7`, `snr_s7_10_f.lua:main_53`,
    # `snr_s8_10_s.lua:main_5`, every one of them a local-closure upvalue
    # call. So the published count remains a FLOOR.
    edges: dict[tuple[str, str], set] = defaultdict(set)
    direct = set()
    def self_method(f: str, path: str, key: bytes):
        """`self.<key>()` -- resolve `key` in the nearest enclosing proto that
        defines methods, walking `main_77_17` -> `main_77` -> `main`.

        Precise rather than permissive: it resolves within THIS proto's own
        ancestor chain, so two constructors that both define `show` do not get
        confused for each other. `_defs_and_calls` records a method table per
        proto path, which is what makes the walk possible."""
        parts = path.split("_")
        while parts:
            anc = "_".join(parts)
            hit = all_methods.get(f, {}).get(anc, {}).get(key)
            if hit is not None:
                return (f, hit)
            parts.pop()
        return None

    for (f, path), sites in all_calls.items():
        for _pc, b in sites:
            if len(b) == 1:
                if b[0] == SELF_BASE:
                    continue
                if b[0] in poll:
                    direct.add((f, path))
                t = gdefs.get(b[0])
            elif len(b) == 2:
                t = (self_method(f, path, b[1]) if b[0] == SELF_BASE
                     else mdef.get((b[0], b[1])))
            else:
                t = None
            if t is not None:
                edges[(f, path)].add(t)
    rev: dict[tuple[str, str], set] = defaultdict(set)
    for a, bs in edges.items():
        for b in bs:
            rev[b].add(a)
    reach = set(direct)
    stack = list(direct)
    while stack:
        n = stack.pop()
        for a in rev.get(n, ()):
            if a not in reach:
                reach.add(a)
                stack.append(a)
    return edges, direct, reach, mdef, self_method


def poll_loops(proto):
    """Natural loops of this proto whose body contains a direct poll call.

    Returns `(n_headers, n_back_edges, [(header, back_edges, poll_pc), ...],
    pcs)`; `pcs` is every pc inside SOME natural loop, used to say whether an
    option call is polled per iteration.

    **A loop is a HEADER, not a back edge, and getting that wrong published a
    false structural claim.** A back edge is `s -> h` with `h` dominating `s`;
    the natural loop of `h` is the union of the backward closures of ALL back
    edges targeting `h`. The first version emitted one entry per back edge, so
    the predecessor-recompiled `snr_common.lua:main_76_2` -- a single
    `while v1 < 1 do ... end` whose tail luac wrote out twice -- reported as
    "4 poll loops" with a 9-block innermost body, against the original's 1.
    Grouped by header it is **one** loop, header block 5, four back edges
    (60/68/188/274), union body 78 blocks. The same conflation made the
    published `n_natural_loops` a back-edge count on 14 of 162 records
    (`snr_mainmenu.lua:main_7`: 32 back edges over 16 headers), which is why
    both numbers are now emitted under their own names.

    `cfg/dom.py` roots the tree at `idom[entry] == entry`, so the dominance
    walk stops at the fixed point rather than looping forever.
    """
    from pyluadec.lift.opcodes import Op
    from pyluadec.cfg.dom import immediate_dominators
    poll = {n.encode() for n in POLL_GLOBALS}
    cfg = cfg_of(proto)
    idom = immediate_dominators(cfg)
    ks = proto.constants

    def dom(a, b):
        while b is not None:
            if b == a:
                return True
            nb = idom.get(b)
            if nb == b:
                return False
            b = nb
        return False

    poll_pcs: dict[int, list[int]] = {}
    for start, blk in cfg.blocks.items():
        prov: dict[int, bytes] = {}
        for li in blk.instrs:
            ri = li.ri
            pre = dict(prov)
            for w in li.effects.writes:
                prov.pop(w, None)
            if ri.op is Op.GETGLOBAL and ks[ri.bx] in poll:
                prov[ri.a] = ks[ri.bx]
            elif ri.op in (Op.CALL, Op.TAILCALL) and pre.get(ri.a) in poll:
                poll_pcs.setdefault(start, []).append(ri.pc)

    back: dict[int, list[int]] = {}
    for s, blk in cfg.blocks.items():
        for t in blk.succs:
            if t in cfg.blocks and dom(t, s):
                back.setdefault(t, []).append(s)
    loops = []
    in_loop: set[int] = set()
    n_back = 0
    for h in sorted(back):
        latches = sorted(back[h])
        n_back += len(latches)
        body = {h}
        stack = list(latches)
        while stack:
            n = stack.pop()
            if n not in body:
                body.add(n)
                stack.extend(cfg.preds.get(n, ()))
        in_loop |= body
        pcs = sorted(pc for n in body for pc in poll_pcs.get(n, ()))
        if pcs:
            loops.append((h, tuple(latches), pcs[0]))
    looped_pcs = {li.ri.pc for b in in_loop for li in cfg.blocks[b].instrs}
    return len(back), n_back, sorted(loops), looped_pcs


MAX_PATH_DEPTH = 8


def channels(proto):
    """`({path: {'cmp': set[str], 'test': int}}, n_register_comparisons)`.

    Forward dataflow to a fixed point over the CFG, meet = agreement
    (a register keeps its provenance at a join only if every predecessor
    agrees on it), entry state empty. Provenance paths are dotted access paths
    of arbitrary depth up to `MAX_PATH_DEPTH`, plus call results.

    ## Why this is NOT block-local, unlike `lift/footprint.py`

    The first version was block-local, on the strength of `lift/footprint.py`'s
    measurement that a full dataflow moves **0 of 11910** table-read sites.
    **That measurement does not transfer, and the corpus said so.** Footprint
    attribution asks "which global is this GETTABLE's base", and `lparser.c`
    emits `GETGLOBAL`/`GETTABLE` adjacent inside one expression, so the answer
    never crosses a block boundary. This pass asks a different question --
    "which constants is this value compared against" -- and a comparison is a
    block TERMINATOR, so the second comparison of `if x == a then ... elseif
    x == b then` is always in a different block from the definition of `x`.

    Measured over the 162 candidates, 2026-08-13: the block-local form differs
    from this one on **110 of 162** records, always downward, worst ratio
    **36x** (`snr_s4_10_s.lua:main_58`), and it put one record on the wrong
    side of the budget (`snr_crd_89.lua:main_9`, 4096 -> 4608). Concrete
    instance, `snr_crd_13.lua:main_2`: `CALL a=3` at pc 39 defines the option
    channel, `EQ 0 R3 K(132)` at pc 40 ends the block, and `EQ 0 R3 K(-1)` at
    pc 43 is in the next one -- so the block-local pass saw a domain of 2 where
    the true one is 3.

    `MOVE` provenance propagation IS carried here, for the same reason and with
    its own measurement: `footprint.py` records 0 deltas from it, but here it
    changes the input space of **13 of 1944** protos.
    """
    from pyluadec.ingest.proto import LuaNumber
    from pyluadec.lift.opcodes import Op, isk, indexk

    ks = proto.constants

    def const_lit(c) -> str:
        if c is None:
            return "nil"
        if c is True or c is False:
            return "true" if c else "false"
        if isinstance(c, LuaNumber):
            return str(int(c.value)) if c.value == int(c.value) else "num"
        return "str"

    def key_seg(c):
        if isinstance(c, bytes):
            return ("k", c)
        if isinstance(c, LuaNumber) and c.value == int(c.value):
            return ("i", int(c.value))
        return ("d", None)

    cfg = cfg_of(proto)
    out: dict[tuple, dict] = {}
    # Comparisons where a channel-carrying register is compared against ANOTHER
    # REGISTER rather than a constant. Those cannot contribute a domain, so
    # they are the measured blind spot of `input_space` and are published
    # rather than left implicit. Corpus-wide 2026-08-13: 3371 EQ/LT/LE sites,
    # 1524 with a channel operand, of which 1504 (98.7%) compare against a
    # constant and 24 (over 16 protos) against a register (measured under
    # the dataflow below; the block-local pass it replaced saw 20).
    unresolved = [0]

    def canon(c):
        """A hashable, ASCII-free-of-corpus-text identity for a comparison
        constant, keeping the VALUE that `const_lit` throws away.

        `const_lit` collapses every string to `"str"` and every non-integer
        number to `"num"`, which is what keeps `corpus/observation/classes.json`
        free of corpus text -- and it is also what makes that file unusable as
        the source of an ACTUAL value to drive a branch with. `scripts/probe_enum.py`
        needs the real constant to construct the assignment that takes the
        `==` arm; it holds these as `bytes` in memory and never writes one
        into an artifact (it publishes an INDEX into this set instead).

        `rec["cmp"]` is untouched, so `chan_out`, `domain_size` and therefore
        `classes.json` are byte-for-byte what they were.
        """
        if c is None:
            return ("nil",)
        if c is True or c is False:
            return ("b", c)
        if isinstance(c, LuaNumber):
            return ("n", c.value)
        return ("s", c)

    def slot(p):
        return out.setdefault(p, {"cmp": set(), "test": 0, "raw": set()})

    def transfer(start, state, record):
        prov: dict[int, tuple] = dict(state[0])
        kreg: dict[int, object] = dict(state[1])
        for li in cfg.blocks[start].instrs:
            ri, op = li.ri, li.ri.op
            pre_prov, pre_k = dict(prov), dict(kreg)

            def rk(x):
                if isk(x):
                    i = indexk(x)
                    return ("K", ks[i]) if 0 <= i < len(ks) else ("?", None)
                if x in pre_k:
                    return ("K", pre_k[x])
                return ("R", x)

            for w in li.effects.writes:
                prov.pop(w, None)
                kreg.pop(w, None)
            if li.effects.writes_open:
                for r in [r for r in prov if r >= ri.a]:
                    del prov[r]
                for r in [r for r in kreg if r >= ri.a]:
                    del kreg[r]

            if op is Op.LOADK:
                if 0 <= ri.bx < len(ks):
                    kreg[ri.a] = ks[ri.bx]
            elif op is Op.LOADBOOL:
                kreg[ri.a] = bool(ri.b)
            elif op is Op.LOADNIL:
                for r in range(ri.a, ri.b + 1):
                    kreg[r] = None
            elif op is Op.MOVE:
                if ri.b in pre_prov:
                    prov[ri.a] = pre_prov[ri.b]
                if ri.b in pre_k:
                    kreg[ri.a] = pre_k[ri.b]
            elif op is Op.GETGLOBAL:
                n = ks[ri.bx]
                if isinstance(n, bytes):
                    prov[ri.a] = (("k", n),)
            elif op is Op.GETTABLE or op is Op.SELF:
                base = pre_prov.get(ri.b)
                if base is not None and len(base) < MAX_PATH_DEPTH:
                    kk = rk(ri.c)
                    prov[ri.a] = base + (key_seg(kk[1]) if kk[0] == "K"
                                         else ("d", None),)
            elif op is Op.CALL:
                base = pre_prov.get(ri.a)
                if base is not None and ri.c >= 2 \
                        and len(base) < MAX_PATH_DEPTH:
                    p2 = base + (("c", None),)
                    for r in range(ri.a, ri.a + ri.c - 1):
                        prov[r] = p2
            elif op in (Op.EQ, Op.LT, Op.LE):
                bb, cc = rk(ri.b), rk(ri.c)
                hit = False
                for x, y in ((bb, cc), (cc, bb)):
                    if x[0] == "R" and x[1] in pre_prov:
                        if y[0] == "K":
                            if record:
                                rc = slot(pre_prov[x[1]])
                                rc["cmp"].add(const_lit(y[1]))
                                rc["raw"].add(canon(y[1]))
                            hit = True
                        elif record:
                            slot(pre_prov[x[1]])
                if not hit and (bb[0] == "R" and bb[1] in pre_prov
                                or cc[0] == "R" and cc[1] in pre_prov):
                    if record:
                        unresolved[0] += 1
            elif op is Op.TEST:
                if record and ri.a in pre_prov:
                    slot(pre_prov[ri.a])["test"] += 1
            elif op is Op.TESTSET:
                if record and ri.b in pre_prov:
                    slot(pre_prov[ri.b])["test"] += 1
        return prov, kreg

    # ## Termination, and why the obvious iteration does not terminate
    #
    # The meet is agreement: a register keeps its provenance at a join only if
    # every reached predecessor agrees on it. Run naively -- every block's
    # entry initialised to the EMPTY map and recomputed from scratch each
    # sweep -- that iteration can churn forever, because an empty initial
    # entry is the BOTTOM of this lattice, so the first sweeps make entries
    # GROW and a register can then flip between two paths as its predecessors
    # flip. Measured: `snr_common.lua:main_72` (236 instructions, 111 blocks,
    # 40 `EQ`/`JMP` pairs) is the one proto of 1944 that does it, and it was
    # still churning after 64 sweeps.
    #
    # The fix is the standard MFP shape for a must-analysis. An unreached
    # block's entry is TOP (`None`), not the empty map; the CFG entry starts
    # at the empty map; a block becomes reached when some predecessor has an
    # exit. From then on its entry is intersected with its own previous value,
    # so it only ever DESCENDS. Descent through a finite lattice (registers x
    # paths capped at `MAX_PATH_DEPTH`) terminates by construction. The sweep
    # cap below is a detector for that argument being wrong, not a tuning
    # knob; measured worst case on this corpus after the fix: see the report.
    order = sorted(cfg.blocks)
    entry: dict[int, tuple[dict, dict] | None] = {b: None for b in order}
    entry[cfg.entry] = ({}, {})
    exits: dict[int, tuple[dict, dict] | None] = {b: None for b in order}

    def agree(a, b):
        pa, ka = a
        pb, kb = b
        return ({r: v for r, v in pa.items() if pb.get(r) == v},
                {r: v for r, v in ka.items()
                 if r in kb and type(kb[r]) is type(v) and kb[r] == v})

    changed = True
    sweeps = 0
    while changed:
        sweeps += 1
        if sweeps > 64:
            raise AssertionError("channel dataflow did not converge")
        changed = False
        # One block at a time, entry THEN exit, in ascending block order.
        # `lparser.c` emits forward jumps for everything except loop back
        # edges, so ascending pc order is a topological order of the forward
        # edges and a whole straight-line region settles in ONE sweep. Doing
        # the two phases as separate whole-CFG loops instead (the first
        # version) advanced reachability by only one block per sweep and
        # needed ~|blocks| sweeps: 9 of 1944 protos blew a 64-sweep cap that
        # way, the largest being `snr_common.lua:main_74_13` at 271 blocks.
        for b in order:
            if b != cfg.entry:
                preds = [q for q in cfg.preds.get(b, ())
                         if exits[q] is not None]
                if not preds:
                    continue
                new = exits[preds[0]]
                for q in preds[1:]:
                    new = agree(new, exits[q])
                if entry[b] is not None:
                    new = agree(new, entry[b])
                if entry[b] != new:
                    entry[b] = new
                    changed = True
            if entry[b] is None:
                continue
            ex = transfer(b, entry[b], record=False)
            if exits[b] != ex:
                exits[b] = ex
                changed = True

    for b in order:
        if entry[b] is not None:
            transfer(b, entry[b], record=True)
    return out, unresolved[0]


def domain_size(rec) -> int:
    """`|constants compared against| + 1`, or 2 when there are none.

    The 2 covers two shapes: a plain truth test (`TEST`/`TESTSET`, so the
    domain really is {truthy, falsy}), and a comparison against another
    REGISTER, where the domain is unknown and 2 is a floor rather than a
    measurement. `register_comparisons` publishes how many of the second kind
    a proto has, so an `input_space` resting on that floor is visible instead
    of implicit.
    """
    return len(rec["cmp"]) + 1 if rec["cmp"] else 2


# ---------------------------------------------------------------- classification

def classify(poll_loop_sites, option_call_sites, chans):
    """`(class, evidence)` -- a rule over measured predicates, not a judgement.

    * `ui-keyloop`   : this proto's own body has a natural loop containing a
                       direct `pressButton` call.
    * `choice-branch`: it does not, but it calls an option-reading function
                       (`OPTION_CALLEES`, each of which resolves to a Class-2
                       proto).
    * `neither`      : everything else -- no poll loop and no option call IN
                       ITS OWN BODY.

    **`neither` does NOT mean "no user-interaction channel".** An independent
    audit of all 38 `neither` candidates (2026-08-13) found 9 that reach one
    through a callee. **Not "one call out"** -- measured hop distance to the
    nearest direct poller is 1, 1, 2, 4, 4 for the five this graph reaches and
    unbounded-by-this-graph for the other four (see `_call_graph`). Only
    **2 of the 9** actually read a value and branch on it:
    `snr_common.lua:main_76_8` (`systemConfig.Config`), which does
    `GETUPVAL R2,0; GETTABLE R2 R2 K"ConfigMain"; CALL` at pcs 18-20 and
    branches at 25/38/40/55, and `main_74_18`. The other seven merely call
    into something that eventually polls.

    Those nine carry the audit's verdict in their `observed` half; the
    mechanical class is left as the rule computes it, because a class that
    quietly disagreed with its own published evidence would be worse than one
    that is narrow and says so.

    The number of branch channels is deliberately NOT a condition. It was one
    in a first version, and the corpus falsified it: `snr_s5_10_s.lua`'s
    `main_42` and `main_43` each call `oCard.selectCardNotCancelObj` and branch
    on the result against a REGISTER (`EQ 0 R8 R1`), not against a constant, so
    they carry an option call and zero measured channels. Demoting them to
    `neither` would have said "no user interaction" about two protos whose
    whole body is a card choice.
    """
    if poll_loop_sites:
        h, s, pc = poll_loop_sites[0]
        return "ui-keyloop", (f"poll loop: header block {h}, back edge from "
                              f"block {s}, pressButton call at pc {pc}"
                              f"; {len(poll_loop_sites)} such loop(s)")
    if option_call_sites:
        nm, pc = option_call_sites[0][0], option_call_sites[0][1]
        return "choice-branch", (f"no poll loop; option call {nm} at pc {pc}"
                                 f" ({len(option_call_sites)} option call site(s));"
                                 f" {len(chans)} branch channel(s)")
    return "neither", ("no poll loop and no option call"
                       + (f"; {len(chans)} branch channel(s)" if chans else
                          "; no branch channel"))


# ---------------------------------------------------------------- probe

def probe_corpus(files):
    """`{file: (status, events, {global name: events})}` from the L1.75 probe.

    The trace's `I|<name>` markers open an invocation window; every event up
    to the next marker is attributed to it. Events before the first marker are
    the chunk body's own and are attributed to `None`.
    """
    from scripts.probe_behaviour import probe_raw

    def one(p: Path):
        raw = probe_raw(p.read_bytes(), is_source=False)
        lines = raw.split(b"\n")
        head = lines[0].split(b"|")
        status, nev = head[1].decode(), int(head[2])
        cur = None
        per: Counter = Counter()
        for ln in lines[1:]:
            if not ln:
                continue
            if ln[:1] == b"I":
                cur = ln[2:]
            per[cur] += 1
        return p.name, status, nev, per

    with ThreadPoolExecutor(max_workers=8) as ex:
        return {n: (s, e, per) for n, s, e, per in ex.map(one, files)}


# ---------------------------------------------------------------- ledger

def read_footprints():
    """`{(file, proto_path): footprint record}` over Task 3's dump.

    A REQUIRED input, not an optional enrichment: the brief's Step-1
    deliverable is that each candidate carries "the interaction surface
    (stub-call set + table-key read set from Task 3)". Degrading silently to
    a record without a `footprint` key is how the first version of this
    script shipped without the join at all, so a missing file raises.
    """
    path = ROOT / "corpus" / "observation" / "footprints.json"
    doc = json.loads(path.read_text())
    return {(fe["file"], pr["proto_path"]): pr
            for fe in doc["files"] for pr in fe["protos"]}


def read_ledger():
    """`{(file, proto_path): row}` over `corpus/ledger.jsonl`."""
    out = {}
    with (ROOT / "corpus" / "ledger.jsonl").open() as fh:
        for line in fh:
            row = json.loads(line)
            for occ in row["occurrences"]:
                out[(occ["file"], occ["proto_path"])] = (row, occ)
    return out


def refusal_origin(f, path, row, non_l3):
    """`"own"` or `"inherited"` -- see the module docstring for the three rules."""
    from pyluadec.lift import lift_proto
    from pyluadec.sir.build import build_sir, StructureError
    reason = row["refusal_reason"]
    kind = reason.split(":", 1)[0]
    if kind == "mismatch":
        return "own" if " at root/" not in reason else "inherited"
    if kind == "structure":
        try:
            build_sir(lift_proto(non_l3[(f, path)][1]))
            return "inherited"
        except StructureError:
            return "own"
    if kind == "reconstruct":
        for (g, q), (r, _p) in non_l3.items():
            if g == f and q != path and q.startswith(path + "_") \
                    and r["refusal_reason"] == reason:
                return "inherited"
        return "own"
    return "own"


# ---------------------------------------------------------------- main

def main() -> int:
    from pyluadec.ingest import load_file
    from pyluadec.pipeline import walk_proto_paths

    corpus = Path(os.environ["PYLUADEC_CORPUS_DIR"])
    files = sorted(corpus.glob("*.lua"))
    if not files:
        print(f"no *.lua under {corpus}", file=sys.stderr)
        return 1

    dest = ROOT / "corpus" / "observation" / "classes.json"
    keep_observed = "--fresh" not in sys.argv
    if not keep_observed and dest.exists() and "--force" not in sys.argv:
        prev = json.loads(dest.read_text())
        n_obs = (sum(1 for r in prev["candidates"] if r.get("observed"))
                 + len(prev.get("orphan_observations", [])))
        if n_obs:
            print(f"refusing --fresh: {dest} carries {n_obs} review "
                  f"observation(s) that --fresh would erase. Pass --force if "
                  f"that is really what you want.", file=sys.stderr)
            return 1
    observed: dict[tuple[str, str], dict] = {}
    # The orphan set the COMMITTED file already carried, so the banner at the
    # end can report what this run newly quarantined rather than the running
    # total. It printed the total under delta wording ("were moved to") for
    # three milestones, and M6 task 12 read a 7-line banner as "7 newly
    # quarantined" when 5 of them had been quarantined by task 11 and only 2
    # were new. Empty under `--fresh`, which is correct: nothing is carried
    # over, so nothing can be pre-existing.
    prev_orphans: set[tuple[str, str]] = set()
    if keep_observed and dest.exists():
        prev = json.loads(dest.read_text())
        for rec in prev["candidates"]:
            obs = rec.get("observed")
            if obs:
                observed[(rec["file"], rec["proto_path"])] = obs
        for orph in prev.get("orphan_observations", []):
            observed[(orph["file"], orph["proto_path"])] = orph["observed"]
            prev_orphans.add((orph["file"], orph["proto_path"]))

    all_protos: dict[tuple[str, str], object] = {}
    per_file: dict[str, dict] = {}
    gdefs: dict[bytes, tuple[str, str]] = {}
    all_methods: dict[str, dict] = {}
    all_calls: dict[tuple[str, str], set] = {}
    chunk_gl: dict[str, dict[bytes, str]] = {}
    for f in files:
        root = load_file(f)
        protos: dict = {}
        walk_proto_paths("main", root, protos)
        per_file[f.name] = protos
        g, meth, calls, by_path = _defs_and_calls(f.name, protos)
        # The behaviour probe invokes globals the CHUNK itself wrote whose
        # value is a function, so the dominant-global resolution uses the
        # chunk's own top-level definitions only, not the file-wide ones.
        chunk_gl[f.name] = by_path["main"]
        for k, v in g.items():
            gdefs.setdefault(k, v)
        all_methods[f.name] = meth
        for path, p in protos.items():
            all_protos[(f.name, path)] = p
            all_calls[(f.name, path)] = calls[path]

    edges, direct_poll, poll_reach, mdef, self_method = _call_graph(
        all_protos, gdefs, all_methods, all_calls)

    def callee_target(f: str, path: str, nm: tuple[bytes, ...]):
        if len(nm) == 1:
            return None if nm[0] == SELF_BASE else gdefs.get(nm[0])
        if len(nm) == 2:
            return (self_method(f, path, nm[1]) if nm[0] == SELF_BASE
                    else mdef.get(nm))
        return None

    option_targets = {}
    option_names = set()
    for spec in OPTION_CALLEES:
        raw = tuple(s.encode() for s in spec)
        t = gdefs.get(raw[0]) if len(raw) == 1 else mdef.get(raw)
        option_targets[".".join(spec)] = f"{t[0]}:{t[1]}" if t else None
        option_names.add(raw)

    # Task 3's interaction surface, joined by (file, proto_path). The brief's
    # Step-1 deliverable names it explicitly ("stub-call set + table-key read
    # set from Task 3") and the first version of this script silently shipped
    # the narrower branch-reaching `channels` instead. Both are now carried:
    # `footprint` is EVERY read/call the proto makes, `channels` is the subset
    # that reaches a branch decision. Task 7 wants the second to enumerate and
    # the first to stub.
    footprints = read_footprints()

    ledger = read_ledger()
    # Restricted to the files actually ingested. On the full 229-file corpus
    # that is every row; the restriction exists so the generator can be run
    # over a subset (which is how `tests/test_observation_classes.py` exercises
    # the observation carry-over cheaply) instead of dying on a KeyError. A
    # row for an INGESTED file that does not resolve is still a hard error --
    # that would mean the ledger and `walk_proto_paths` disagree about a proto
    # tree, which is exactly the coupling the ledger's `proto_path` rests on.
    seen_files = {f.name for f in files}
    for k, (r, _o) in ledger.items():
        if k[0] in seen_files and k not in all_protos:
            raise AssertionError(f"ledger row {k} has no proto in the tree")
    non_l3 = {k: (r, all_protos[k]) for k, (r, o) in ledger.items()
              if r["level"] != "L3" and k[0] in seen_files}
    leaves = {k for k in non_l3
              if refusal_origin(k[0], k[1], non_l3[k][0], non_l3) == "own"}

    probe = probe_corpus(files)
    caps = {}
    for f, (status, nev, per) in probe.items():
        if status != "CAP":
            continue
        named = {k: v for k, v in per.items() if k is not None}
        if not named:
            continue
        dom = max(sorted(named), key=lambda k: named[k])
        path = chunk_gl[f].get(dom)
        if path is not None:
            caps[(f, path)] = (dom, named[dom], nev)

    selected: dict[tuple[str, str], list[str]] = defaultdict(list)
    for k in sorted(leaves):
        selected[k].append("leaf-refusal")
    for k in sorted(caps):
        selected[k].append("cap-dominant")

    # corpus-wide input-space census (context for the candidate figures)
    corpus_space = Counter()
    corpus_unresolved = 0
    for k, p in all_protos.items():
        ch, _unres = channels(p)
        corpus_unresolved += _unres
        n = 1
        for rec in ch.values():
            n *= domain_size(rec)
        corpus_space[n <= BUDGET] += 1

    records = []
    per_iter_by_class: Counter = Counter()
    census: Counter = Counter()
    census_by_pop: dict[str, Counter] = {"leaf-refusal": Counter(),
                                         "cap-dominant": Counter()}
    drivable_by_class: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for key in sorted(selected):
        f, path = key
        p = all_protos[key]
        row, occ = ledger[key]
        n_hdr, n_back, ploops, looped = poll_loops(p)
        ch, n_unresolved = channels(p)
        opt_sites = [(_callee_text(b), pc, pc in looped)
                     for pc, b in all_calls[key] if b in option_names]
        # Does SOME natural loop of this proto poll the key on every
        # iteration, directly or through a callee that reaches one? This is
        # the measurement behind the report's Class-1/Class-2 overlap: the
        # owner's framing treats non-termination as Class 2's distinguishing
        # difficulty, and it is not.
        indirect = sorted({_callee_text(nm) for pc, nm in all_calls[key]
                           if pc in looped
                           and callee_target(f, path, nm) in poll_reach})
        per_iter = bool(ploops) or bool(indirect)
        cls, evidence = classify(ploops, opt_sites, ch)
        space = 1
        chan_out = []
        for cpath in sorted(ch, key=path_text):
            rec = ch[cpath]
            d = domain_size(rec)
            space *= d
            chan_out.append({"path": emit_path(cpath),
                             "text": path_text(cpath),
                             "domain": d,
                             "constants": sorted(rec["cmp"]),
                             "truth_tested": rec["test"] > 0})
        drivable = space <= BUDGET
        census[cls] += 1
        if per_iter:
            per_iter_by_class[cls] += 1
        for pop in selected[key]:
            census_by_pop[pop][cls] += 1
        drivable_by_class[cls][0] += 1 if drivable else 0
        drivable_by_class[cls][1] += 1
        pr = probe[f]
        rec = {
            "file": f,
            "proto_path": path,
            "mechanical": {
                "selected_as": selected[key],
                "n_insns": len(p.code),
                "nups": p.nups,
                "numparams": p.numparams,
                "level": row["level"],
                "refusal_reason": row["refusal_reason"],
                "refusal_origin": (refusal_origin(f, path, row, non_l3)
                                   if row["level"] != "L3" else None),
                "shipped": occ["shipped"],
                "hybrid_chunk": occ["hybrid"],
                "probe": {
                    "file_status": pr[0],
                    "file_events": pr[1],
                    "dominant_global": (emit_name(caps[key][0])
                                        if key in caps else None),
                    "dominant_global_events": caps[key][1] if key in caps else None,
                },
                # Headers, not back edges -- see `poll_loops`. Both are
                # published because the two differ on 14 of 162 records and
                # the earlier field name meant the wrong one.
                "n_natural_loops": n_hdr,
                "n_back_edges": n_back,
                "poll_loops": [{"header_block": h,
                                "back_edge_blocks": list(bs),
                                "poll_pc": pc} for h, bs, pc in ploops],
                "calls_poll_directly": key in direct_poll,
                "reaches_poll": key in poll_reach,
                "loop_polls_per_iteration": per_iter,
                "in_loop_callees_reaching_poll": indirect,
                "option_calls": [{"callee": nm, "pc": pc, "in_loop": lo}
                                 for nm, pc, lo in opt_sites],
                "channels": chan_out,
                "register_comparisons": n_unresolved,
                "input_space": space,
                "drivable_within_budget": drivable,
                "class": cls,
                "class_evidence": evidence,
            },
        }
        fp = footprints[key]
        rec["mechanical"]["footprint"] = {
            k: fp[k] for k in ("global_reads", "table_key_reads",
                               "calls", "table_key_calls",
                               "dynamic_reads", "read_sites", "call_sites")}
        obs = observed.pop(key, None)
        if obs is not None:
            rec["observed"] = obs
        records.append(rec)

    summary = {
        "n_files": len(files),
        "n_protos": len(all_protos),
        "n_candidates": len(records),
        "n_leaf_refusals": len(leaves),
        "n_non_l3": len(non_l3),
        "n_cap_files": sum(1 for v in probe.values() if v[0] == "CAP"),
        "n_cap_dominants": len(caps),
        "n_in_both_populations": sum(1 for v in selected.values() if len(v) > 1),
        "class_census": {k: census[k] for k in sorted(census)},
        "class_census_leaf_refusals": {k: census_by_pop["leaf-refusal"][k]
                                       for k in sorted(census_by_pop["leaf-refusal"])},
        "class_census_cap_dominants": {k: census_by_pop["cap-dominant"][k]
                                       for k in sorted(census_by_pop["cap-dominant"])},
        "drivable_within_budget_by_class": {
            k: drivable_by_class[k] for k in sorted(drivable_by_class)},
        "budget": BUDGET,
        "corpus_protos_within_budget": corpus_space[True],
        "corpus_protos_over_budget": corpus_space[False],
        # The measured blind spot of every `input_space` figure: a branch that
        # compares a channel against another REGISTER contributes no domain.
        "corpus_register_comparisons": corpus_unresolved,
        "poll_globals": list(POLL_GLOBALS),
        "candidates_polling_per_iteration": {
            k: per_iter_by_class[k] for k in sorted(per_iter_by_class)},
        "protos_calling_poll_directly": len(direct_poll),
        "protos_reaching_poll": len(poll_reach),
        "option_callee_targets": {k: option_targets[k] for k in sorted(option_targets)},
        "n_observed_records": sum(1 for r in records if "observed" in r),
    }
    # Whatever is left in `observed` had no candidate to attach to. Dropping
    # it silently is exactly the failure the milestone's own goal makes likely:
    # a proto certifies `L3`, leaves the leaf-refusal population, and a
    # human-reviewed note evaporates. Quarantine, and shout.
    #
    # There is a SECOND way to leave, and it is not the documented one --
    # measured at M6 task 12, which is when it first happened.
    # `snr_graphic.lua:main` was quarantined **without certifying**: its
    # refusal reason moved from `mismatch: maxstacksize` to
    # `mismatch: maxstacksize at root/2` (its own fields now match; a
    # descendant's do not), and `refusal_origin` reads any `... at root/N` as
    # `inherited`, so it stopped being a LEAF refusal while staying non-`L3`.
    # An improvement that pushes a proto's first mismatch down into a
    # descendant therefore orphans its observation just as an improvement that
    # certifies it does. Both are quarantine, not loss, and both re-attach if
    # the candidate returns -- but a reader who only knows the `L3` trigger
    # will misread the banner.
    orphans = [{"file": f, "proto_path": path, "observed": obs}
               for (f, path), obs in sorted(observed.items())]
    doc = {"version": VERSION, "summary": summary, "candidates": records}
    if orphans:
        doc["orphan_observations"] = orphans
    summary["n_orphan_observations"] = len(orphans)
    _assert_ascii(doc)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=True) + "\n")

    print(f"classes: {len(records)} candidates over {len(files)} files -> {dest}")
    print(f"  populations : {len(leaves)} leaf refusal site(s) of {len(non_l3)} "
          f"non-L3 rows; {len(caps)} CAP-dominant proto(s) of "
          f"{summary['n_cap_files']} CAP files; "
          f"{summary['n_in_both_populations']} in both")
    print(f"  classes     : " + ", ".join(f"{k} {census[k]}" for k in sorted(census)))
    print(f"  poll reach  : {len(direct_poll)} protos call {POLL_GLOBALS[0]} "
          f"directly, {len(poll_reach)} reach it transitively")
    for k in sorted(drivable_by_class):
        ok, tot = drivable_by_class[k]
        print(f"  drivable <= {BUDGET} : {k} {ok}/{tot}")
    print(f"  corpus-wide : {corpus_space[True]}/{len(all_protos)} protos have "
          f"input space <= {BUDGET}")
    print(f"  observed    : {summary['n_observed_records']} record(s) carried over")
    if orphans:
        fresh_orphans = [o for o in orphans
                         if (o["file"], o["proto_path"]) not in prev_orphans]
        carried = len(orphans) - len(fresh_orphans)
        print("!" * 72, file=sys.stderr)
        # The count and the wording must agree: this run only MOVED the ones
        # that were not already in `orphan_observations`. Printing the running
        # total under "were moved to" is what misled M6 task 12 into reporting
        # 7 newly quarantined observations when 2 were new.
        print(f"!! {len(fresh_orphans)} OBSERVATION(S) NO LONGER MATCH A "
              f"CANDIDATE and were moved to `orphan_observations` BY THIS RUN"
              + (f" ({carried} more were already quarantined):"
                 if carried else ":"), file=sys.stderr)
        for o in fresh_orphans:
            print(f"!!   {o['file']}:{o['proto_path']} "
                  f"(reviewed_by {o['observed'].get('reviewed_by')})",
                  file=sys.stderr)
        if carried:
            print(f"!! already quarantined before this run ({carried}):",
                  file=sys.stderr)
            for o in orphans:
                if (o["file"], o["proto_path"]) in prev_orphans:
                    print(f"!!   {o['file']}:{o['proto_path']} "
                          f"(reviewed_by {o['observed'].get('reviewed_by')})",
                          file=sys.stderr)
        print("!! They are NOT lost -- they are quarantined in the JSON and "
              "will re-attach if the candidate returns.", file=sys.stderr)
        print("!" * 72, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

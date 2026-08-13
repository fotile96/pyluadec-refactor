"""预任项目质量度量的移植（spec §1 目标 4 / §7 M5 出口的 `avg_score` 基线）。

Port of `/root/pyluadec/pyluadec/semantic_eval.py` (546 lines) onto our
`Proto`. This is the **only apples-to-apples instrument** we have against the
predecessor's stated `avg_score 0.997`: that number was produced by this
metric and by nothing else, and the predecessor's pipeline cannot run here
(32-bit in-process bridge). Spec §8's rule for porting predecessor assets is a
mechanism-equivalent rewrite with the assertions' semantics unchanged, so the
signature fields, the nine components, their weights, the sensitivity
thresholds and the pass/warn cut-offs below are transcribed, not redesigned.

## What it is, and what it is emphatically not

It is an **evaluation** instrument. It reports a number; it gates nothing.
`verify.normalize` / `verify.certify` decide what is `L3`, and this module
must never become a second, weaker path to that verdict -- a chunk that scores
1.0 here is still fallback unless certification says otherwise. The direction
that matters is the other one: certification is a *predicate* (the recompiled
proto matches field for field, or it does not), so it cannot say how far off a
non-matching artifact is. That is the gap this fills, and it is why the score
is defined over lossy per-proto *signatures* (counters of opcode families,
global reads/writes, call targets/shapes, return arities, constants) rather
than over the protos themselves.

The score is a weighted mean over protos, weighted by `code_len`, of a
weighted sum of nine component similarities. `_counter_similarity` is
1 - L1(a,b)/(|a|+|b|), i.e. 1.0 for equal counters and 0.0 for disjoint ones.

## Divergences from the predecessor's implementation

Their `semantic_eval` consumed plain dicts from a bridge that lost
information (`tvalue_to_py` in `native_bridge/proto_extractor.cpp`: numbers
via `py::float_`, strings via `py::str(svalue(tv))` -- NUL-terminated and
raising on non-UTF-8). Ours consumes `Proto`, with `bytes` string constants
and `LuaNumber` payloads. **The rule applied throughout: reproduce their
COMPARISON, not their LOSSES.** Every case decided differently is listed
here, with what it can do to the number. Corpus counts below were measured
this session over all 229 files / 1944 protos.

D1. `_const_name` on a string constant. Theirs returned the decoded `str`
    itself (`"print"`); a first version of this port routed it through
    `_normalize_const(value)` (`"str:5:<sha1>"`) instead, on the theory that
    it is an injective relabelling applied identically to both sides and
    `_counter_similarity` only ever tests keys for equality. **That theory
    was wrong** (found in round-1 review, 2026-08-12): `_table_access_tag`
    tests a *prefix*, `key.startswith("K:str:")`, not equality. Theirs could
    never satisfy that test through `_const_name`'s output (a raw string
    constant is never `str:`-prefixed by construction), so the LOADK-into-
    register path -- taken whenever a GETTABLE's key constant index is >=
    256 and so cannot be RK-embedded -- always fell through to
    `"TABLE:access"` for them. The first port version, by contrast, tagged
    that same register `K:str:5:<sha1>`, which *does* start with `K:str:`,
    so it took the `.field` branch instead. `_rk_tag`'s *direct* embed path
    (constant index < 256) was never affected either way -- it calls
    `_normalize_const` directly in both implementations, not `_const_name`,
    so it already agreed.

    Measured this session: **60** such GETTABLE sites across **9** corpus
    files flip classification (one-off instrumented replay of this module's
    forward pass over every proto in every original corpus file, not
    committed -- the number is reproducible from the mechanism above).
    Corpus `avg_score`: **0.935579** (first-version behaviour) ->
    **0.935633** (fixed) -- one file's score moves,
    `snr_common.lua` **0.161667 -> 0.174230**. Direction: the first version
    was strictly *stricter* than the predecessor in this corner (finer, not
    coarser), so the fix raises the score; it never lowers one.

    **Fix applied**: `_const_name` now special-cases `bytes` with its own
    injective, non-`str:`-prefixed tag (`cn:{len}:{sha1}`) instead of
    delegating to `_normalize_const`. This reproduces the predecessor's
    *behavioural class* for the register-indirect path (injective, but the
    `.field` branch stays unreachable through LOADK, exactly as it was for
    them) without decoding any bytes -- `_normalize_const` itself, and every
    other caller of it (`_rk_tag`'s embed path, `constant_fingerprint`),
    is untouched. This was chosen over documenting the stricter behaviour
    as accepted, because "port fidelity is the deliverable" (task brief) and
    this file's stated rule is to reproduce their *comparison*; a prefix
    scheme that accidentally changes a downstream `startswith` verdict is a
    comparison difference, not a bridge-loss difference, so it belongs in
    the "match" column rather than the "diverge, but harmlessly" column.

D2. String fingerprint. Theirs `str:{len(str)}:{sha1(str.encode("utf-8"))}`;
    ours `str:{len(bytes)}:{sha1(bytes)}`. Measured: **0** of 49063 corpus
    string constants are invalid UTF-8, so the digest is bit-identical to
    theirs; the length prefix differs for **17411** of them (multi-byte
    Japanese: characters vs bytes). **No effect on any score** -- same
    partition of constants, both sides relabelled the same way. It does mean
    an individual key string from this module is not comparable to one from
    theirs; only the scores are.

D3. NUL truncation. `svalue()` is a `char*`, so their bridge silently cut
    every string constant at its first NUL and could not represent one at
    all if it was not UTF-8. We keep the whole byte string. Measured: **0**
    corpus constants contain a NUL and **0** are non-UTF-8, and **0**
    truncation-collision groups exist, so this changes nothing here.
    Direction if it ever did: ours is strictly finer (keeps apart what they
    conflated), so it could only ever *lower* a score relative to theirs.

D4. Numbers. Their bridge did `lua_Number -> py::float_`, which on this
    target is **not** actually lossy: `lua_Number` is IEEE double
    (`sizeof(lua_Number)=8, is_integral=0` in the corpus header), so their
    float was the exact value. We therefore use `LuaNumber.value` and
    produce byte-identical normalization strings -- **no divergence at all**
    in the ported behaviour. We deliberately do NOT switch to
    `LuaNumber.payload`, even though we have it: `_normalize_const`'s
    stringification (`is_integer() -> num:{int}`, else `%.17g`) is part of
    their *comparison*, not of the bridge's loss, and payload-keying would
    change it by making `-0.0` distinguishable from `0.0` and NaN bit
    patterns distinguishable from each other. Measured: **0** negative zeros
    and **0** non-finite values among 22120 corpus number constants, so the
    choice cannot move this corpus's number either way. Direction if it
    could: payload-keyed would be finer, so it could only lower the score.

D5. `is_vararg`. Their bridge exposed `bool(is_vararg & VARARG_HASARG)`,
    dropping `ISVARARG`/`NEEDSARG`; we compare the raw flag byte.
    **No effect on the score**: `is_vararg` feeds only `hard_issues` and
    hence `status`, never one of the nine weighted components. It is finer
    for status purposes -- a `...` function emitted without `...` is now
    visible. Corpus flag census: `2` on all 229 main chunks (`ISVARARG`,
    as `lparser.c:luaY_parser` sets it), `0` on 1704 protos, `3` on 11.

D6. `upvalue_count`. Theirs was `len(proto.upvalues)`, i.e. the size of the
    upvalue-NAME vector, which is debug-section data: **0** for our stripped
    corpus originals and the true count for the freshly compiled candidate,
    so they were comparing 0 against N. We use `nups`. Neither the score nor
    the issue list reads this field in either implementation; it is carried
    for signature fidelity and recorded here so the next reader does not
    "fix" a field that was never wired up.

D7. CFG. Reimplemented here over decoded instructions rather than reusing
    `pyluadec.cfg.build_cfg`, which partitions LIR into a *different* block
    set (LIR merges the pseudo-instruction words a `SETLIST`/`LOADNIL` pair
    consumes, and numbers pcs from 1). Reusing it would have silently
    changed two of the nine components. Their partition and its quirks are
    preserved verbatim, including the ones that are arguably wrong:
      - `TFORLOOP` gets **no** jump target. Their `calculate_jump_target`
        read `inst["Bx"]`, and the bridge only put `Bx` in the dict for
        `iABx`/`iAsBx` instructions -- `TFORLOOP` is `iABC`, so the lookup
        missed and returned `None`. (Had it hit, `pc+1+Bx` would have been
        meaningless anyway: `TFORLOOP`'s loop-back jump is the `JMP` that
        follows it.)
      - `FORPREP` has no fallthrough edge (`has_fallthrough = False`).
      - a back edge is `succ_block_id <= block_id`, an ordering heuristic,
        not a dominance test.
    These make `cfg_reachable`/`cfg_all` a crude shape hash. That is what
    the 0.997 baseline was measured with, so it is what we measure with.

D8. Driver. They recompiled the candidate in-process via
    `lua51_proto_extractor.load_from_source`; we go through
    `oracle.compile_source` (a `luac_sz4` subprocess) and `ingest.load_bytes`.
    Same vendored vanilla 5.1.5 front end (`lparser.c`/`lcode.c`) either way,
    so the emitted protos agree; the difference is only that ours crosses a
    process and a serialized chunk. Kept out of this module entirely --
    `score_protos` takes two `Proto`s and never compiles anything.

No `re` anywhere (the `tests/test_engineering_practice.py` ban binds this
file); the predecessor's version used none either.
"""
from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from pyluadec.ingest.proto import Const, LuaNumber, Proto
from pyluadec.lift.opcodes import OP_SPECS, ArgMode, Fmt, decode

# Transcribed from semantic_eval.py's _OP_FAMILIES. It is INCOMPLETE, and
# left that way: exactly two of the 38 opcodes are missing upstream -- SELF
# and CLOSE (verified against `lift.opcodes.Op` this session) -- and they fall
# to "other" through the `.get` default. Completing the table would change
# what `opcode_family` measures on every proto that calls a method, i.e. it
# would be a different metric than the one the 0.997 baseline came from.
_OP_FAMILIES: dict[str, str] = {
    "MOVE": "data", "LOADK": "data", "LOADBOOL": "data", "LOADNIL": "data",
    "GETUPVAL": "upvalue", "SETUPVAL": "upvalue",
    "GETGLOBAL": "global", "SETGLOBAL": "global",
    "GETTABLE": "table", "SETTABLE": "table", "NEWTABLE": "table",
    "SETLIST": "table",
    "ADD": "arith", "SUB": "arith", "MUL": "arith", "DIV": "arith",
    "MOD": "arith", "POW": "arith", "UNM": "arith", "NOT": "arith",
    "LEN": "arith", "CONCAT": "arith",
    "JMP": "control", "EQ": "control", "LT": "control", "LE": "control",
    "TEST": "control", "TESTSET": "control",
    "FORPREP": "loop", "FORLOOP": "loop", "TFORLOOP": "loop",
    "CALL": "call", "TAILCALL": "call",
    "RETURN": "return", "CLOSURE": "closure", "VARARG": "vararg",
}

PASS_SCORE_THRESHOLD = 0.93
WARN_SCORE_THRESHOLD = 0.70
SEMANTIC_SENSITIVE_THRESHOLDS = {
    "global_reads": 0.995,
    "global_writes": 0.995,
    "call_targets": 0.97,
    "call_shapes": 0.97,
    "return_arity": 1.0,
}

WEIGHTS = {
    "cfg_reachable": 0.10,
    "cfg_all": 0.05,
    "opcode_family": 0.20,
    "global_reads": 0.10,
    "global_writes": 0.10,
    "call_targets": 0.20,
    "call_shapes": 0.10,
    "return_arity": 0.05,
    "const_fingerprint": 0.10,
}

# Their _collect_block_starts breaks after TERMINATORS, TEST_OPS, and any
# instruction whose opcode carries lopcodes.h's T flag. Read off
# `vendor/lua-5.1/src/lopcodes.c:86-96` this session, the T-flag set is
# {EQ, LT, LE, TEST, TESTSET, TFORLOOP} -- wholly inside the first two sets,
# so their three-way union is exactly this. Folded into one frozenset rather
# than re-deriving a per-opcode `test` bit we do not otherwise carry.
_TERMINATORS = frozenset({"JMP", "RETURN", "FORLOOP", "FORPREP", "TFORLOOP"})
_TEST_OPS = frozenset({"TEST", "TESTSET", "EQ", "LT", "LE"})
_BLOCK_BREAKERS = _TERMINATORS | _TEST_OPS

_ARITH_TAGGED = frozenset({"ADD", "SUB", "MUL", "DIV", "MOD", "POW",
                           "LEN", "CONCAT", "UNM", "NOT"})


@dataclass(frozen=True)
class _Ins:
    """A decoded instruction shaped exactly like the predecessor's dict.

    `A`/`B`/`C`/`Bx`/`sBx` are `None` in precisely the positions
    `decode_instruction` left out of the dict for that format -- `iABC` ->
    `Bx`, `sBx` are `None` (`B`, `C` present); `iABx` -> `B`, `C`, `sBx` are
    `None` (`Bx` present); `iAsBx` -> `B`, `C` are `None` (`Bx` and `sBx`
    both present) -- because `_extract_semantic_counters` branches on
    `is not None` and would classify differently otherwise.
    `pc` is 0-based, matching their `enumerate(raw_proto["code"])`.
    """
    pc: int
    opname: str
    A: int | None
    B: int | None
    C: int | None
    Bx: int | None
    sBx: int | None
    cmode: ArgMode
    jump_target: int | None


def _decode_all(proto: Proto) -> list[_Ins]:
    out: list[_Ins] = []
    for pc, word in enumerate(proto.code):
        # decode()'s `pc` parameter is 1-based repo-wide (see lift.py, which
        # loops `pc = 1; while pc <= n`); it reaches only DecodeError's
        # message text here, never a returned field. `_Ins.pc` below is
        # deliberately 0-based instead, to match the predecessor's
        # `enumerate(raw_proto["code"])` -- the two conventions coexist on
        # purpose, not by oversight.
        ri = decode(word, pc + 1)
        spec = OP_SPECS[ri.op]
        name = ri.op.name
        if spec.fmt is Fmt.iABC:
            b, c, bx, sbx = ri.b, ri.c, None, None
        elif spec.fmt is Fmt.iABx:
            b, c, bx, sbx = None, None, ri.bx, None
        else:
            b, c, bx, sbx = None, None, ri.bx, ri.sbx
        # calculate_jump_target: sBx-relative for JMP/FORLOOP/FORPREP;
        # TFORLOOP's branch needed `Bx`, which the bridge never set on an
        # iABC instruction, so it produced None (D7).
        target = pc + 1 + sbx if (name in ("JMP", "FORLOOP", "FORPREP")
                                  and sbx is not None) else None
        out.append(_Ins(pc=pc, opname=name, A=ri.a, B=b, C=c, Bx=bx, sBx=sbx,
                        cmode=spec.cmode, jump_target=target))
    return out


@dataclass(frozen=True)
class ProtoSignature:
    path: tuple[int, ...]
    code_len: int
    numparams: int
    is_vararg: int
    upvalue_count: int
    subproto_count: int
    cfg_reachable: tuple[int, int, int]
    cfg_all: tuple[int, int, int]
    opcode_counts: Counter
    opcode_family_counts: Counter
    constant_fingerprint: Counter
    global_reads: Counter
    global_writes: Counter
    call_targets: Counter
    call_shapes: Counter
    return_arity: Counter


@dataclass(frozen=True)
class ProtoScore:
    path: tuple[int, ...]
    score: float
    components: dict[str, float] = field(default_factory=dict)
    issues: tuple[str, ...] = ()
    code_len: int = 0


@dataclass(frozen=True)
class FileScore:
    score: float
    status: str                       # "pass" | "warn" | "fail"
    strict_ok: bool | None            # None unless a small `file_size` was given
    drift_type: str                   # "semantic_candidate" | "structural_only"
    semantic_sensitive_paths: tuple[tuple[int, ...], ...]
    hard_issues: tuple[str, ...]
    proto_scores: tuple[ProtoScore, ...]


def _normalize_const(value: Const) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "bool:true" if value else "bool:false"
    if isinstance(value, LuaNumber):
        # D4: `.value` is the exact double their `py::float_` carried.
        v = value.value
        if v.is_integer():
            return f"num:{int(v)}"
        return f"num:{v:.17g}"
    if isinstance(value, bytes):
        # D2/D3: hash the raw bytes, length in bytes. Never decoded.
        return f"str:{len(value)}:{hashlib.sha1(value).hexdigest()[:12]}"
    if isinstance(value, int):
        # Unreachable through `ingest` (numeric constants are LuaNumber), kept
        # so a hand-built Proto in a test cannot silently fall to `other:`.
        return f"num:{value}"
    return f"other:{type(value).__name__}:{value!r}"


def _cfg_shape(instrs: list[_Ins], reachable_only: bool) -> tuple[int, int, int]:
    """(block count, edge count, back-edge count) -- their `_cfg_shape`.

    Faithful down to the degenerate trailing block a jump-past-the-end
    produces (start > end, `instructions[end_pc]` re-reading the final
    instruction) and to the `succ <= bid` back-edge heuristic. See D7.
    """
    if not instrs:
        return (0, 0, 0)

    starts = {0}
    n = len(instrs)
    for ins in instrs:
        if ins.jump_target is not None:
            starts.add(ins.jump_target)
        if ins.opname in _BLOCK_BREAKERS and ins.pc + 1 < n:
            starts.add(ins.pc + 1)
    ordered = sorted(starts)

    pc_to_block: dict[int, int] = {}
    ends: list[int] = []
    for idx, start in enumerate(ordered):
        end = ordered[idx + 1] - 1 if idx + 1 < len(ordered) else n - 1
        ends.append(end)
        for pc in range(start, end + 1):
            pc_to_block[pc] = idx

    succs: dict[int, set[int]] = {idx: set() for idx in range(len(ordered))}
    for idx in range(len(ordered)):
        ins = instrs[ends[idx]]
        if ins.jump_target is not None and ins.jump_target in pc_to_block:
            succs[idx].add(pc_to_block[ins.jump_target])
        has_fallthrough = ins.opname not in {"JMP", "RETURN", "FORPREP"}
        if has_fallthrough and ends[idx] + 1 < n:
            succs[idx].add(pc_to_block[ends[idx] + 1])

    if reachable_only:
        block_set: set[int] = set()
        stack = [0]
        while stack:
            bid = stack.pop()
            if bid in block_set or bid not in succs:
                continue
            block_set.add(bid)
            stack.extend(succs[bid])
    else:
        block_set = set(succs.keys())

    edge_count = 0
    back_edge_count = 0
    for bid in block_set:
        for succ in succs[bid]:
            if succ in block_set:
                edge_count += 1
                if succ <= bid:
                    back_edge_count += 1
    return (len(block_set), edge_count, back_edge_count)


def _const_name(constants: tuple[Const, ...], idx: int | None) -> str:
    if idx is None or idx < 0 or idx >= len(constants):
        return "<bad_const>"
    value = constants[idx]
    # D1 (round 1, Important 1): predecessor's `_const_name` short-circuited
    # string constants to the decoded value itself (`"print"`), so the tag
    # a LOADK-into-register assigns is `K:print`, which can never satisfy
    # `_table_access_tag`'s `key.startswith("K:str:")` test. That test is
    # satisfied only via `_rk_tag`'s *direct* constant-embed path, which
    # calls `_normalize_const` directly (not `_const_name`) in both
    # implementations and so already agrees. We cannot decode (bytes stay
    # bytes), so this reproduces the predecessor's *behavioural class* for
    # the register-indirect path instead: injective, but never `str:`-
    # prefixed, so `.field` stays unreachable through LOADK exactly as it
    # was for them. Measured this session: 60 GETTABLE sites across 9 corpus
    # files flip from `.field` to `TABLE:access` under this fix; corpus
    # avg_score 0.935579 -> 0.935633 (see module docstring D1).
    if isinstance(value, bytes):
        return f"cn:{len(value)}:{hashlib.sha1(value).hexdigest()[:12]}"
    return _normalize_const(value)


def _rk_tag(proto: Proto, reg_tags: dict[int, str], value: int | None,
            mode: ArgMode) -> str:
    if value is None:
        return "?"
    if mode is ArgMode.K and value >= 0x100:
        kidx = value - 0x100
        if 0 <= kidx < len(proto.constants):
            return f"K:{_normalize_const(proto.constants[kidx])}"
        return "K:<bad>"
    return reg_tags.get(value, f"R:{value}")


def _table_access_tag(base: str, key: str) -> str:
    # Keep signature compact/stable; preserve only meaningful global/upvalue
    # table roots.
    if key.startswith("K:str:"):
        if base.startswith("G:") or base.startswith("U:"):
            return f"{base}.field"
    return "TABLE:access"


def _call_arity(ins: _Ins) -> str:
    if ins.B is None:
        nargs = "?"
    elif ins.B == 0:
        nargs = "*"
    else:
        nargs = str(max(ins.B - 1, 0))

    if ins.opname == "TAILCALL":
        nret = "tail"
    elif ins.C is None:
        nret = "?"
    elif ins.C == 0:
        nret = "*"
    else:
        nret = str(max(ins.C - 1, 0))
    return f"args:{nargs}|rets:{nret}"


def _extract_semantic_counters(
    proto: Proto, instrs: list[_Ins]
) -> tuple[Counter, Counter, Counter, Counter, Counter]:
    """Their `_extract_semantic_counters`, transcribed.

    A single forward pass with a symbolic register-tag map -- no dataflow, no
    joins at merge points, tags simply overwritten in pc order. That is
    deliberately crude and is why `call_targets` is a *fingerprint* rather
    than a call graph; it is also why the fallback's `__pld_R[...]` register
    array scores badly on it, which is the property the calibration test
    depends on.
    """
    global_reads: Counter = Counter()
    global_writes: Counter = Counter()
    call_targets: Counter = Counter()
    call_shapes: Counter = Counter()
    return_arity: Counter = Counter()

    reg_tags: dict[int, str] = {}
    for ins in instrs:
        op = ins.opname
        if op == "GETGLOBAL" and ins.A is not None and ins.Bx is not None:
            name = _const_name(proto.constants, ins.Bx)
            reg_tags[ins.A] = f"G:{name}"
            global_reads[name] += 1
            continue
        if op == "SETGLOBAL" and ins.A is not None and ins.Bx is not None:
            global_writes[_const_name(proto.constants, ins.Bx)] += 1
            continue
        if op == "GETUPVAL" and ins.A is not None and ins.B is not None:
            reg_tags[ins.A] = f"U:{ins.B}"
            continue
        if op == "MOVE" and ins.A is not None and ins.B is not None:
            reg_tags[ins.A] = reg_tags.get(ins.B, f"R:{ins.B}")
            continue
        if op == "LOADK" and ins.A is not None and ins.Bx is not None:
            reg_tags[ins.A] = f"K:{_const_name(proto.constants, ins.Bx)}"
            continue
        if op == "LOADBOOL" and ins.A is not None and ins.B is not None:
            reg_tags[ins.A] = "K:bool:true" if ins.B else "K:bool:false"
            continue
        if op == "LOADNIL" and ins.A is not None and ins.B is not None:
            for reg in range(ins.A, ins.B + 1):
                reg_tags[reg] = "K:nil"
            continue
        if op == "CLOSURE" and ins.A is not None:
            reg_tags[ins.A] = f"CLOSURE:{ins.Bx if ins.Bx is not None else '?'}"
            continue
        if (op == "GETTABLE" and ins.A is not None and ins.B is not None
                and ins.C is not None):
            base = reg_tags.get(ins.B, f"R:{ins.B}")
            key = _rk_tag(proto, reg_tags, ins.C, ins.cmode)
            reg_tags[ins.A] = _table_access_tag(base, key)
            continue
        if op in _ARITH_TAGGED and ins.A is not None:
            reg_tags[ins.A] = "EXPR"
            continue
        if op in ("CALL", "TAILCALL") and ins.A is not None:
            callee = reg_tags.get(ins.A, f"R:{ins.A}")
            call_targets[callee] += 1
            call_shapes[f"{callee}|{_call_arity(ins)}"] += 1
            if op == "CALL" and ins.C is not None:
                if ins.C == 0:
                    reg_tags[ins.A] = f"RET:{callee}:*"
                elif ins.C > 1:
                    for reg in range(ins.A, ins.A + ins.C - 1):
                        reg_tags[reg] = f"RET:{callee}"
            continue
        if op == "RETURN" and ins.B is not None:
            if ins.B == 0:
                return_arity["*"] += 1
            else:
                return_arity[str(max(ins.B - 1, 0))] += 1
            continue

    return global_reads, global_writes, call_targets, call_shapes, return_arity


def collect_proto_signatures(
    proto: Proto, path: tuple[int, ...] = ()
) -> dict[tuple[int, ...], ProtoSignature]:
    """Signature for every proto in the tree, keyed by subproto-index path.

    Public because the calibration tests use it to prove the "identical
    scores 1.0" case is not vacuous (every counter must be non-empty
    somewhere in the sample; an all-empty Counter pair scores 1.0 for free).
    """
    instrs = _decode_all(proto)
    reads, writes, targets, shapes, rets = _extract_semantic_counters(proto, instrs)
    out = {
        path: ProtoSignature(
            path=path,
            code_len=len(instrs),
            numparams=proto.numparams,
            is_vararg=proto.is_vararg,            # D5: raw flag byte
            upvalue_count=proto.nups,             # D6
            subproto_count=len(proto.subprotos),
            cfg_reachable=_cfg_shape(instrs, reachable_only=True),
            cfg_all=_cfg_shape(instrs, reachable_only=False),
            opcode_counts=Counter(i.opname for i in instrs),
            opcode_family_counts=Counter(
                _OP_FAMILIES.get(i.opname, "other") for i in instrs),
            constant_fingerprint=Counter(_normalize_const(c) for c in proto.constants),
            global_reads=reads,
            global_writes=writes,
            call_targets=targets,
            call_shapes=shapes,
            return_arity=rets,
        )
    }
    for i, sub in enumerate(proto.subprotos):
        out.update(collect_proto_signatures(sub, path + (i,)))
    return out


def _counter_similarity(a: Counter, b: Counter) -> float:
    keys = set(a.keys()) | set(b.keys())
    if not keys:
        return 1.0
    total = sum(a.values()) + sum(b.values())
    if total == 0:
        return 1.0
    diff = sum(abs(a[k] - b[k]) for k in keys)
    return max(0.0, 1.0 - (diff / total))


def _has_sensitive_constant_diff(a: Counter, b: Counter) -> bool:
    # Numeric literal set drift is often introduced by source-level
    # normalization (integer formatting, table index emission) and is usually
    # structural. Treat non-numeric constant drift as semantic-sensitive.
    for k in set(a.keys()) | set(b.keys()):
        if a[k] == b[k]:
            continue
        if k.startswith("num:"):
            continue
        return True
    return False


def _collect_function_shape(proto: Proto, path: tuple[int, ...] = ()) -> list[tuple]:
    out = [(path, proto.numparams, proto.is_vararg, len(proto.subprotos))]
    for i, sub in enumerate(proto.subprotos):
        out.extend(_collect_function_shape(sub, path + (i,)))
    return out


def score_protos(original: Proto, candidate: Proto, *,
                 file_size: int | None = None, small_kb: int = 10) -> FileScore:
    """Their `_classify_file`, over two `Proto` trees.

    `original` is the corpus bytecode; `candidate` is what our decompiled
    source recompiles to. `file_size`/`small_kb` reproduce their extra strict
    check for small files and set `strict_ok`; omit `file_size` and
    `strict_ok` is `None` (their "not applicable" value for large files).
    Neither influences `score`.
    """
    hard_issues: list[str] = []
    if _collect_function_shape(original) != _collect_function_shape(candidate):
        hard_issues.append("function_shape_mismatch")

    orig_sigs = collect_proto_signatures(original)
    cand_sigs = collect_proto_signatures(candidate)
    if set(orig_sigs.keys()) != set(cand_sigs.keys()):
        hard_issues.append("proto_path_set_mismatch")

    all_paths = sorted(set(orig_sigs.keys()) | set(cand_sigs.keys()))
    proto_scores: list[ProtoScore] = []
    weighted_score = 0.0
    total_weight = 0
    strict_ok = True
    sensitive_paths: list[tuple[int, ...]] = []

    for path in all_paths:
        left = orig_sigs.get(path)
        right = cand_sigs.get(path)
        if left is None or right is None:
            proto_scores.append(
                ProtoScore(path=path, score=0.0, issues=("missing_proto",)))
            strict_ok = False
            continue

        issues: list[str] = []
        if left.numparams != right.numparams:
            issues.append("numparams")
        if left.is_vararg != right.is_vararg:
            issues.append("is_vararg")
        if left.subproto_count != right.subproto_count:
            issues.append("subproto_count")
        if issues:
            hard_issues.append(f"signature_mismatch@{path}")

        components = {
            "cfg_reachable": 1.0 if left.cfg_reachable == right.cfg_reachable else 0.0,
            "cfg_all": 1.0 if left.cfg_all == right.cfg_all else 0.0,
            "opcode_family": _counter_similarity(left.opcode_family_counts,
                                                 right.opcode_family_counts),
            "global_reads": _counter_similarity(left.global_reads, right.global_reads),
            "global_writes": _counter_similarity(left.global_writes, right.global_writes),
            "call_targets": _counter_similarity(left.call_targets, right.call_targets),
            "call_shapes": _counter_similarity(left.call_shapes, right.call_shapes),
            "return_arity": _counter_similarity(left.return_arity, right.return_arity),
            "const_fingerprint": _counter_similarity(left.constant_fingerprint,
                                                     right.constant_fingerprint),
        }
        score = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)

        sensitive = any(components[k] < threshold
                        for k, threshold in SEMANTIC_SENSITIVE_THRESHOLDS.items())
        if not sensitive and components["const_fingerprint"] < 1.0:
            sensitive = _has_sensitive_constant_diff(left.constant_fingerprint,
                                                     right.constant_fingerprint)
        if sensitive:
            sensitive_paths.append(path)

        if file_size is not None and file_size <= small_kb * 1024:
            strict_match = (
                left.opcode_counts == right.opcode_counts
                and left.cfg_reachable == right.cfg_reachable
                and left.call_shapes == right.call_shapes
                and left.constant_fingerprint == right.constant_fingerprint
            )
            if not strict_match:
                strict_ok = False

        code_weight = max(left.code_len, 1)
        weighted_score += score * code_weight
        total_weight += code_weight
        proto_scores.append(ProtoScore(
            path=path, score=round(score, 6),
            components={k: round(v, 6) for k, v in components.items()},
            issues=tuple(issues), code_len=left.code_len))

    file_score = (weighted_score / total_weight) if total_weight else 0.0
    if hard_issues:
        status = "fail"
    elif file_score >= PASS_SCORE_THRESHOLD:
        status = "pass"
    elif file_score >= WARN_SCORE_THRESHOLD:
        status = "warn"
    else:
        status = "fail"

    ordered = tuple(sorted(proto_scores, key=lambda p: (not p.issues, p.score)))
    small = file_size is not None and file_size <= small_kb * 1024
    return FileScore(
        score=round(file_score, 6),
        status=status,
        strict_ok=strict_ok if small else None,
        drift_type=("semantic_candidate" if sensitive_paths or hard_issues
                    else "structural_only"),
        semantic_sensitive_paths=tuple(sensitive_paths[:16]),
        hard_issues=tuple(hard_issues),
        proto_scores=ordered,
    )

# M3 backlog (produced by the Phase 2 final whole-branch review)

This file exists because the M2 execution workspace (`.superpowers/sdd/...`) is
scratch and gets deleted; everything below came out of the final review of the
`phase2-m2-fallback` branch and would otherwise be lost. It is a starting
agenda for M3 (structural recovery), not a plan — plans get written with
`superpowers:writing-plans` when M3 begins.

Status at the end of M2: 229/229 corpus files produce compilable Lua via the
fallback emitter; 130 tests pass; `corpus/ledger.jsonl` holds 1478 unique proto
hashes over 1944 occurrences, all at level `L1`.

## Ordered backlog

**0. Harden `verify/normalize._cmp` before adding any normalization rung.**
Done for the five fields that were unguarded at M2 (`source`, `nups`,
`numparams`, `is_vararg`, `upvalues` — see `tests/test_normalize.py`). The
standing rule: every field the comparator claims to compare needs an isolating
negative example, verified by removing that field from `_cmp` and watching a
named test fail. This is M3's central verification instrument; presence in the
code is not coverage.

**1. Cross-check `Cfg.succs` against terminator ground truth in the corpus
invariant.** Done at the end of M2 (`tests/test_cfg.py`). Keep the discipline
as M3 starts consuming `succs` for structuring: a self-consistent corruption
(e.g. truncating to the first successor) is exactly what would silently
mis-structure a function.

**2. Land the effects-vs-emitter reconciliation as a permanent test.**
`lift/effects.py` and `structure/fallback.py` are two independent hand
transcriptions of `lvm.c`. Nothing mechanically reconciles them. The final
review built the check and ran it over all 1944 corpus protos with **zero
discrepancies**: for every instruction, the register indices the emitted
template touches must be a subset of `effects.reads | effects.writes` (skipping
open regions, which are `__pld_top`-relative). Worth landing permanently — it
keeps the two transcriptions agreeing as M3 stacks passes on the effects table.

**3. Promote the global-state probe to an L1.5 gate.** See "Global-state probe"
below. It turns the corpus gate from "compiles" into "produces byte-identical
observable global state on real game content", without needing the game engine.
Not full L2 (it does not exercise engine-driven code paths), but a genuine rung
between L1 and L2, and cheap.

**4. Build `tests/synth.py` — a synthetic `Proto`/`RawInstr` fixture.** Three
correct-but-untestable paths remain at M2, all because luac cannot be coaxed
into emitting them: SELF's `A+1 == B` aliasing guard (`fallback.py`), TESTSET's
no-write-on-non-matching-branch, and `lift.py`'s "empty code array" raise.
A fixture that constructs protos directly and drives `_FnEmitter` closes all
three at once, and M3 will want it constantly.

**5. Table-layout fidelity — an explicit M3 structuring requirement.** The
fallback emitter does not reproduce table internal layout (see "Known semantic
gaps" in `decompile-pipeline.md`). This is corpus-reachable and needs real
table-constructor reconstruction, not a fallback patch. Pin it with a
differential test when M3 implements it.

## Deferred minors carried out of M2

Non-blocking, each verified as correct code with a documentation or coverage
gap rather than a defect:

- `ingest/dispatch.py` — `_bridge_for()` is called outside the `try/except`, so
  a stale-`.so` width mismatch escapes as a bare `RuntimeError` instead of
  `IngestError`. Only reachable via a corrupt build.
- `lift/effects.py` — the LEN row is grouped with UNM under a "coercion"
  rationale, but `lvm.c`'s `OP_LEN` never invokes a metamethod for table or
  string operands (Lua 5.1 has no `__len` on tables). The classification is a
  safe over-approximation; the comment is imprecise. SETLIST's `may_error=True`
  is conservative-not-literal in the same way and deserves the same explanatory
  comment FORLOOP already has.
- `cfg/blocks.py` — `leaders.add(pcs[i + 1])` is a proven equivalent mutant
  (verified structurally, over 20k randomized synthetic CFGs, and over all 1944
  corpus protos). Harmless today; it becomes silently load-bearing if the
  block-closing condition in the second loop is ever refactored to diverge from
  the leader-computation condition in the first.
- `cfg/blocks.py` — `Cfg.preds` sortedness is untested (replacing
  `tuple(sorted(v))` with `tuple(v)` breaks nothing today). Becomes a
  determinism hazard once M3 structuring iterates predecessors.
- `cfg/dom.py` — `_reverse_postorder` uses recursive DFS and mutates the
  process-global recursion limit in a `finally`. Fine single-threaded at corpus
  scale (max 624 blocks); revisit if M3 ever parallelises corpus runs.
- `lift/lift.py` — validates `1 <= s <= n` for successors but not
  `s in instrs`, so a successor landing on a consumed pseudo-instruction slot
  surfaces later as a bare `KeyError` from `blocks.py` rather than a
  `LiftError`. Not reachable from luac output; matters for hand-crafted or
  corrupted bytecode.
- Package convention drift — `structure/__init__.py` and `verify/__init__.py`
  are empty while `lift/` and `cfg/` export curated `__all__`. Also
  `LUA_KEYWORDS` lives in `lift/opcodes.py` (a decoder) but is a codegen
  concern consumed only by `structure/fallback.py`.
- Duplicated proto-path convention — `pipeline.walk_proto_paths` and
  `fallback.py`'s CLOSURE child key / `emit_chunk` walk independently implement
  `f"{path}_{i}"`. If they drift, ledger `proto_path` stops identifying the
  emitted `__pld_F` factory, and only the committed ledger bytes would catch it.
  Extract one shared helper.
- `verify/ledger.py` — `LedgerEntry.l3_level` and `n_insns` are written by
  `run_corpus.py` and read by nothing, not even the dashboard. Fine as forward
  schema; do not mistake them for verified data.
- `scripts/ledger_dashboard.py` — reports aggregate counts only, never naming
  which files or protos are `L0` / `compile_ok: false`. At 1478 entries a bare
  byte-diff is unusable for chasing a regression.
- `docs/runbooks/decompile-pipeline.md` — the sentence "92 carry a non-zero
  array presize (B) or hash presize" is loosely worded: 92 is the count for
  `B != 0` alone; `B != 0 or C != 0` is 154. The other counts in that section
  (62 `NEWTABLE` with `C != 0`, 92 `SETLIST`, 7 `TFORLOOP`) are correct.
- `tests/test_oracle.py` — a dead `if stripped_proto.source is not None:`
  guard; the preceding line already asserts the value.

## Tests that could not fail at the end of M2

Found by mutation during the final review, all in the emitter, none
corpus-reachable — but they are real holes in the evidence:

- Boxed **parameters** emitted unboxed: no test captures a function *parameter*
  in a closure. The shipped code is correct.
- `UNM` rendered as `0-(x)` instead of `-(x)`: differs on `__unm` vs `__sub`
  metamethod dispatch, and on `-0.0`. No test exercises either.
- `FORLOOP`'s `step > 0` weakened to `step >= 0`: `for i = 1, 10, 0` runs zero
  times in the VM but loops forever in the mutant. This was the fifth mutation
  in this project to manifest as a **hang rather than an assertion failure** —
  `oracle.run_bytes`'s built-in timeout is what makes such mutations visible at
  all, and any future mutation testing must keep a timeout in place.

## Global-state probe

Loads a chunk, `pcall`s it, and deterministically serialises the resulting
delta to the global table (sorted keys, depth-limited, `%.17g` numbers), so the
original bytecode and the fallback output can be compared on real corpus
content without the game engine.

Result over the full corpus: **229 files, 229 with identical global state, 0
divergent, 0 errors — and none trivially empty.** Non-vacuity was confirmed by
injecting a `FORLOOP` bound error and an arithmetic operand swap; each produced
a divergence within the first 60 files.

```lua
local target = ...
local base = {}
for k in pairs(_G) do base[k] = true end
local f = loadfile(target)
if not f then print("LOADFAIL") os.exit(0) end
local ok, err = pcall(f)
local out = {}
local function ser(v, depth, seen)
  local t = type(v)
  if t == "table" then
    if depth > 4 then return "<deep>" end
    if seen[v] then return "<cycle>" end
    seen[v] = true
    local keys = {}
    for k in pairs(v) do keys[#keys+1] = tostring(k) end
    table.sort(keys)
    local parts = {}
    for _, ks in ipairs(keys) do
      local val
      for k, vv in pairs(v) do if tostring(k) == ks then val = vv break end end
      parts[#parts+1] = ks .. "=" .. ser(val, depth + 1, seen)
    end
    seen[v] = nil
    return "{" .. table.concat(parts, ",") .. "}"
  elseif t == "number" then
    return string.format("%.17g", v)
  elseif t == "function" or t == "userdata" or t == "thread" then
    return "<" .. t .. ">"
  else
    return tostring(v)
  end
end
local names = {}
for k in pairs(_G) do if not base[k] then names[#names+1] = tostring(k) end end
table.sort(names)
for _, n in ipairs(names) do
  local val
  for k, vv in pairs(_G) do if tostring(k) == n then val = vv break end end
  out[#out+1] = n .. "=" .. ser(val, 0, {})
end
print((ok and "OK|" or "ERR|") .. table.concat(out, "\n"))
```

Drive it by running the probe under `build/lua_sz4` twice — once with the
original corpus file, once with the emitted source from
`pyluadec.pipeline.decompile_file` — and comparing stdout. Serialisation is
depth-limited and sorts by `tostring(k)`, so it is insensitive to `pairs`
order; that is deliberate, since table layout is a known M2 gap (see
"Known semantic gaps" in `decompile-pipeline.md`) and would otherwise swamp the
signal. Tightening that is part of backlog item 5.

## What M2 did and did not prove

Proven: 229/229 corpus files emit and recompile through the real `luac_sz4`;
differential execution equivalence (stdout and exit code) over ~70 synthetic
cases covering all 38 opcodes; the ledger is self-reproducing and covers
1944/1944 protos.

Not proven: semantic equivalence on real corpus content. The differential
harness runs only on synthetic cases — the game scripts need an engine. The
uniform `L1` level is an honest representation of this: the plan defines `L1`
as "compilable, unverified", `l3_level` is `null`, and every entry carries a
confession covering its whole pc range stating the function was emitted by the
fallback state machine. Backlog item 3 is the cheapest way to strengthen this.

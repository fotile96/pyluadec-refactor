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

**3. Promote the global-state probe to an L1.5 gate.** *(Landed — M3 Task 9;
see "Global-state probe" below for what it does and does not reach.)* It turns
the corpus gate from "compiles" into "produces byte-identical observable global
state on real game content", without needing the game engine. Not full L2 (it
does not exercise engine-driven code paths), but a genuine rung between L1 and
L2, and cheap. Read the reach table before treating it as strong evidence: for
222 of 229 files the entire compared payload is `string:main=<function>`.

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

**The probe is `scripts/probe_global_state.lua`; that file is the single source
of truth.** An earlier revision of this section carried a full inline copy,
which went stale the moment the probe was fixed. Do not paste it back —
describe it here, read it there. The Python driver is
`scripts/probe_global_state.py` (`probe(payload, *, is_source) -> str`, plus a
whole-corpus `main()`); the standing gate is
`tests/test_global_state_probe.py`.

Drive it by running the probe under `build/lua_sz4` twice — once with the
original corpus file, once with the emitted source from
`pyluadec.pipeline.decompile_file` — and comparing stdout. Output is one of
`OK|<globals>`, `ERR|<message>|<globals written before the failure>`, or
`LOADFAIL|<message>`; any other stdout, or a non-zero exit, raises
`ProbeError` rather than becoming a comparable value.

### Result over the full corpus (re-measured, M3 Task 9 round 1)

**229 files, 225 with byte-identical probe output, 4 divergent, 0 probe
failures.** The 4 divergences are pinned exactly in
`EXPECTED_ERROR_NAME_DIVERGENCE` (`tests/test_global_state_probe.py`) and are
explained below — they are a naming artifact of the emitter's register-box
model, not a state difference. 5 files (`config.lua`, `snr_graphic.lua`,
`snr_mainmenu.lua`, `snr_memory.lua`, `snr_novel.lua`) error before writing any
global, so their compared payload is the error message alone.

### What the gate actually reaches — read this before trusting it

The compared payload is small. Measured across all 229 files:

| measure | value |
| --- | --- |
| payload length, median | 22 chars |
| files with payload < 40 chars | 227 / 229 |
| top-level globals compared, total | 452 |
| of those, the bare placeholder `<function>` | 303 (67%) |
| files whose entire payload is `string:main=<function>` | 222 |
| files with a substantive payload | 1 (`snr_common.lua`, 228 globals, 59512 chars) |
| `<deep>` truncations / `<cycle>` markers | 0 / 0 |

So for 222 of 229 files this gate verifies exactly one fact: a global named
`main` exists and is a function. Every statement inside `main` — the whole
content of the file — is invisible, because nothing calls it. Depth and cycle
truncation are not live hazards at these sizes. The earlier claim in this
section ("229 with identical global state, 0 errors, none trivially empty")
was measurably wrong on all three counts and has been replaced. Deepening the
reach by actually invoking the newly-added global functions under a stubbing
`_G` is recorded as M4 input.

### Known incomparable dimension: getobjname-derived names in error text

Lua 5.1 composes `attempt to index <kind> '<name>'` and `bad argument #n to
'<name>'` via `getobjname` (ldebug.c), which names a value by the *bytecode
shape* that produced it — global read, local, upvalue, table field. The
fallback emitter routes every register through the `__pld_R` box table, so a
value the original obtained with `GETGLOBAL` is obtained from a table field in
our output, and the message reads `field 'v'` where the original read
`global 'gameSave'`. This is not the `.luac`/`.lua` split: recompiling our
output with `luac_sz4` (stripped or not) reproduces the same text, and under an
auto-stubbing `_G` all four files advance further in lockstep and diverge again
only in the same noun. Operation, offending value type, and the set of globals
written before the failure all agree.

The four are pinned as exact `(original, decompiled)` string pairs, not
excluded: if either side's text moves — including if they start agreeing, which
moving off the box model in M4 should cause — the test fails and the pin must
be re-derived.

### Design notes that are load-bearing

- Serialisation sorts by `type(k) .. ":" .. tostring(k)`, so it is insensitive
  to `pairs` order — deliberate, since table layout is a known M2 gap (see
  "Known semantic gaps" in `decompile-pipeline.md`) and would otherwise swamp
  the signal. Tightening that is part of backlog item 5. The `type(k)` prefix
  is not cosmetic: keying on `tostring(k)` alone collapses the number `1` and
  the string `"1"` onto one entry, dropping one value and emitting the other
  twice, so two different tables serialised identically.
- Only globals that did **not** exist before the chunk ran are compared.
  Assignments to pre-existing globals and in-place mutation of an existing
  global table are invisible.
- The probe binds every name it uses to a local before running the target, and
  restores pre-existing globals afterwards (Lua's C `print` re-resolves the
  global `tostring` on each call, so `tostring = nil` in the target would
  otherwise silence the probe entirely).
- No Lua string patterns in the probe: the `<source>:<line>: ` prefix is
  stripped with plain `string.find(..., true)` and byte indexing.

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

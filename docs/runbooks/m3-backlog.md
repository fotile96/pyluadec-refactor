# M3/M4 backlog, and the M5 agenda

This file exists because the SDD execution workspaces (`.superpowers/sdd/...`)
are scratch and get deleted. It started as the M2 final-review backlog for M3;
at the close of M3 it absorbed M3's own deferred findings, and at the close of
M4 it absorbed M4's, for the same reason. It is an agenda, not a plan — plans
get written with `superpowers:writing-plans` when the milestone begins.

**Reading order.** The "M4 agenda" section below is now a *record*: its items
are marked DONE with the task that closed them, and the entries kept verbatim
underneath contain retracted claims that must not be re-derived. **What is
still open is the "M5 agenda" section at the very end of this file.** Start
there.

Status at the end of M2: 229/229 corpus files produce compilable Lua via the
fallback emitter; 130 tests pass; `corpus/ledger.jsonl` holds 1478 unique proto
hashes over 1944 occurrences, all at level `L1`.

Status at the end of M3 (ledger figures measured at commit `fb85f2f` and
unchanged since; suite re-measured 2026-08-11 after the final-review round):
229/229 still compile; 285 tests pass in 29.5s; the ledger holds the same 1478 unique hashes over 1944
occurrences, of which **1112 unique (75.2%) / 1577 occurrences (81.1%)** are
`L3` — recompiled through the real `luac_sz4` and matched field-by-field at
ladder rung 1. 92 of the 229 files ship genuinely structured source. See
`docs/runbooks/structured-pipeline.md`.

Status at the end of M4 (all figures re-measured 2026-08-12 at commit
`3ae72c6`, the M4 task-11 tip): 229/229 still compile; **512 tests pass in
40.0s** (462 passed / 50 skipped in 4.4s without `PYLUADEC_CORPUS_DIR`); the
ledger holds the same 1478 unique hashes over 1944 occurrences, of which
**1389 unique (94.0%) / 1855 occurrences (95.4%)** are `L3` — against an M4
exit floor of 85% on both bases (`tests/test_m4_exit.py`). **212 of the 229
files ship genuinely structured source** (92 at M3 close); the other 17 still
ship the M2 fallback. Every non-`L3` row now records `refusal_reason` saying
why. Readability against the predecessor's shipped output is evaluated in
`docs/reports/m4-readability.md`.

## Ordered backlog (M2 → M3)

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
*(Landed — M3 Task 10: `tests/test_effects_emitter_consistency.py`.)*
`lift/effects.py` and `structure/fallback.py` are two independent hand
transcriptions of `lvm.c`. Nothing mechanically reconciled them. For every
instruction, the register indices the emitted template touches must be a subset
of `effects.reads | effects.writes`. Re-measured M4 task 8, after that task
removed the gate's blanket open-region skip: **all 214192 corpus instructions
checked, 0 disagreements**; 6981 of them carry an open (`__pld_top`-relative)
region — 6949 `CALL`, 26 `VARARG`, 3 `RETURN`, 3 `TAILCALL` — and are checked
for their static part only. The corpus arm reaches 33 of 38 opcodes, so a
synthetic operand grid covers the remaining 5. (Before task 8: 207214 of
214192 checked, 32 of 38 opcodes.) See "The effects–emitter consistency gate"
in `structured-pipeline.md` for the two findings that came out of writing it,
including the `TAILCALL` `writes_open` gap, now closed — §4 below.

**3. Promote the global-state probe to an L1.5 gate.** *(Landed — M3 Task 9;
see "Global-state probe" below for what it does and does not reach.)* It turns
the corpus gate from "compiles" into "produces byte-identical observable global
state on real game content", without needing the game engine. Not full L2 (it
does not exercise engine-driven code paths), but a genuine rung between L1 and
L2, and cheap. Read the reach table before treating it as strong evidence: for
222 of 229 files the entire compared payload is `string:main=<function>`.

**4. Build `tests/synth.py` — a synthetic `Proto`/`RawInstr` fixture.**
*(Landed — M3 Task 1: `tests/synth.py`, `mk_instr` / `mk_proto` / `mk_cfg`.)*
Three correct-but-untestable paths remained at M2, all because luac cannot be
coaxed into emitting them: SELF's `A+1 == B` aliasing guard (`fallback.py`),
TESTSET's no-write-on-non-matching-branch, and `lift.py`'s "empty code array"
raise. M3 used the fixture constantly, most recently for the synthetic arm of
backlog item 2 (the only way to reach the 6 opcodes the corpus never contains).

**5. Table-layout fidelity.** *(Partially done — M3 Task 5.)* Real table
constructors are now reconstructed (`express/reconstruct.py`: `TableExpr`,
`_fold_setlist`, `_fold_settable`, `_close_table_ctx`), so the fallback's
"assign fields one at a time into a bare `{}`" shape is no longer what a
structured file emits. **Presize fidelity is guaranteed indirectly rather than
tested directly**: any table constructor inside a proto that certifies `L3` was
recompiled by the real `luac_sz4` into byte-identical `code`, and `NEWTABLE`'s
`B`/`C` presize hints are part of `code` — so a wrong array/hash split cannot
certify. What is *not* covered: the 366 unique protos still at `L1`, where the
fallback's table shape (and hence `pairs` iteration order) is unconstrained.
That is why the global-state probe sorts its keys; see "Design notes that are
load-bearing" below. A direct differential test on `next`/`pairs` order remains
open; the first corpus-level runtime evidence that it is a live gap (not a
theoretical one) came out of Task 9's deliverable B — see M4 agenda §5,
`snr_novel`.

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
  concern. *(Corrected 2026-08-11: the original entry said "consumed only by
  `structure/fallback.py`" and proposed moving it there. That rationale is
  gone — M3 added two more consumers, `express/names.py` (imported at module
  top, asserted inside `name_for`) and `emit/lua.py::_ident`, so it is now
  shared by three modules across two layers.
  The misplacement is still real; the fix is no longer "move it into
  fallback.py" but a shared codegen-side home. Lower priority than when it
  had one consumer.)* **M5 task 6 round 2 review (Residual B) added a third
  instance of the same open question**: `emit/lua.py` imports `const_lit,
  inline_function_parts` from `structure/fallback.py` (an emit -> structure
  dependency), while `structure/structured.py` imports FROM `emit/lua.py` --
  mutual dependency through `fallback.py`. `const_lit` predates task 6;
  `inline_function_parts` is the hybrid boundary's own addition and cannot
  currently live anywhere neutral because nowhere neutral exists yet.
  Recorded at the import site in `emit/lua.py` rather than given a bespoke
  fix; folds into whatever shared codegen-side home eventually gets built for
  `LUA_KEYWORDS` and the proto-path convention below.
- Duplicated proto-path convention — `pipeline.walk_proto_paths`'s own
  `f"{path}_{i}"` call (line 57 at the M4 branch point; a docstring expansion
  since pushed it to line 63 without this citation being re-swept — found
  fixing task 12's Important-1 finding, same drift pattern, so cited by
  symbol only from here on), `fallback.py:254` (the CLOSURE child key) and
  `fallback.emit_chunk:379`
  independently implement `f"{path}_{i}"`. If they drift, ledger `proto_path`
  stops identifying the emitted `__pld_F` factory — an undocumented but real
  debugging affordance — and nothing would catch it. *(M3 final-review round:
  **documented at all three sites** rather than extracted, deliberately.
  Extraction is not the one-liner it looks like: `fallback.py` importing from
  `pipeline.py` inverts the layering, so the helper needs a new neutral home,
  which is the same open question as the `LUA_KEYWORDS` entry above. And a
  shared format helper would only unify the *spelling*; the other half of the
  coupling is that `walk_proto_paths`' `enumerate` index and the CLOSURE
  handler's `Bx` must denote the same child, which a shared f-string does not
  check.)* **M4:** extract the helper into a shared home **and** add the test
  that actually closes this — assert the `__pld_F` key set of one file's
  fallback artifact equals the set of `proto_path`s the ledger records for
  that file.
- `verify/ledger.py` — `LedgerEntry.l3_level` and `n_insns` are written by
  `run_corpus.py` and read by nothing, not even the dashboard. Fine as forward
  schema; do not mistake them for verified data. *(Half-closed in M3:
  `l3_level` is now read by `scripts/ledger_dashboard.py::main` (the `rungs`
  Counter, rendered by the `L3 rung {k}` rows) and asserted by
  `tests/test_m3_exit.py`.
  `n_insns` is still write-only.)*
- ~~`scripts/ledger_dashboard.py` — reports aggregate counts only, never naming
  which files or protos are `L0` / `compile_ok: false`.~~ **CLOSED in M3
  task 8.** `ledger_dashboard.py::main`'s "Name names" block (its `problems`
  list) prints
  every entry with `compile_ok: false` or `level == "L0"` individually —
  `shash` prefix, first file and `proto_path`, level, and the count of further
  occurrences — in both plain and `--markdown` modes. Verified 2026-08-11.
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

#### Instruction-level evidence for the four pins

This is the load-bearing part of the justification and it is recorded here
because it lived only in a scratch workspace. All four files fail at the **same
original instruction on both sides**, indexing the **same nil value** produced
by the **immediately preceding global read**. Derived with
`./build/luac_sz4 -o /dev/null -l <corpus>/<file>` (the `-o /dev/null` matters:
luac dumps unless told not to, so a bare `-l` litters `luac.out` into your cwd;
pcs are luac's own 1-based listing
numbers) and cross-checked against `lift_proto(...).captured_regs`:

| file | global read | index that fails | reg boxed? | decompiled text |
| --- | --- | --- | --- | --- |
| `snr_memory.lua` | pc 81 `GETGLOBAL 7 systemSave` | pc 82 `GETTABLE 7 7 "memoryFlag"` | reg 7 boxed | `field 'v'` |
| `snr_novel.lua` | pc 82 `GETGLOBAL 7 systemSave` | pc 83 `GETTABLE 7 7 "novelGetFlag"` | reg 7 boxed | `field 'v'` |
| `snr_mainmenu.lua` | pc 85 `GETGLOBAL 1 gameSave` | pc 86 `GETTABLE 1 1 "startMenuState"` | reg 1 boxed | `field 'v'` |
| `snr_graphic.lua` | pc 344 `GETGLOBAL 18 systemSave` | pc 345 `GETTABLE 18 18 "cgFlag"` | reg 18 **not** boxed | `field '?'` |

For `snr_memory`, `snr_novel` and `snr_graphic` the listed pair is the *only*
`GETGLOBAL <that name>` immediately followed by a `GETTABLE` on the same
register anywhere in the file's main chunk. `snr_mainmenu` has 22 such
`gameSave` pairs; pc 85/86 is the earliest in program order and every one of
them would compose the identical message.

**Why three say `field 'v'` and one says `field '?'`.** `ldebug.c:567-578`
(`luaG_typeerror`) asks `getobjname` for a name and formats
`attempt to %s %s '%s' (a %s value)`. In `getobjname`, `OP_GETGLOBAL` yields
`"global"` with the name taken straight from `p->k[Bx]` (`ldebug.c:509-514`),
while `OP_GETTABLE` yields `"field"` with the name from
`kname(p, GETARG_C(i))` (`ldebug.c:522-526`) — and `kname`
(`ldebug.c:489-494`) returns the constant only when it is an RK **string**
constant, otherwise the literal `"?"`.

The fallback emitter reads a register as `__pld_R[n].v` when the register is
boxed (captured by some closure) and as `__pld_R[n]` when it is not. In the
first three files the failing register is boxed, so the value being indexed was
produced by a `GETTABLE` with the *string* key `"v"` → `field 'v'`. In
`snr_graphic` register 18 sits above every captured register (main's boxed set
is 0–13), so it is emitted unboxed and the value came from a `GETTABLE` whose
key is the *numeric* constant `18` → `kname` refuses it → `field '?'`.

That is the whole divergence: same instruction, same nil, same operation, same
set of globals written before the failure (empty on both sides for all four) —
only `getobjname`'s noun differs, and it differs because it names values by the
bytecode shape that produced them.

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

---

# M4 agenda

Everything below came out of M3 and would otherwise be lost with the SDD
workspace. Ordered by size, not by urgency.

## 1. Loops: `while` / `repeat` / mixed and irreducible back edges — DONE (M4 tasks 1-4, 13)

*Closed 2026-08-12. `b05ce12` (dominance-defined back edges, `WhileTrue`),
`ea5257a` (printer arms + loop scoping), `d36ccc0` (`while <cond>` + `repeat`
recognition), `c1b10a9` (`_match_cond_value` for the `and`/`or` VALUE idiom),
`783d15c` (register classification per definition, which was the actual
bottleneck), each with its review round. Result: `build_sir` acceptance went
1309 -> **1447** unique protos, whole-subtree printing 1170 -> **1424**, and
`L3` 1112 -> **1389** unique / 1577 -> **1855** occurrences. The residual is
89 unique protos, censused two independent ways in
`structured-pipeline.md` -> "Current capability boundary" (which is the
authority for these figures; do not re-derive them from the pre-M4 table
below). One premise in the original entry was overturned by measurement
before task 2 even started — see `c50200f` — and the entry is kept verbatim
because of it. The remaining loop-shaped work is M5 agenda item 3.*

The single largest remaining increment, and the reason ~19% of unique protos
are still `L1`. Measured over 1478 unique proto shapes / 1944 occurrences
(originally at commit `fb85f2f`, re-verified 2026-08-11). **The runnable
scripts for this table and for the refusal breakdown below are inlined in
`docs/runbooks/structured-pipeline.md`, "Current capability boundary" →
"Re-deriving the three rows"**, each with the output it produced:

| stage | unique | occurrences |
| --- | --- | --- |
| `build_sir` accepts the proto's own body | 1309 (88.6%) | 1775 (91.3%) |
| whole subtree prints (proto and every descendant) | 1170 (79.2%) | 1636 (84.2%) |
| certifies `L3` | 1112 (75.2%) | 1577 (81.1%) |

`build_sir` refuses 169 unique protos: **162 carry a back edge** it will not
claim (195 unique protos have a back edge at all; 33 of those are recognized as
`for` loops), and 7 are acyclic refusals. All 16 unique protos containing
`TESTSET` — the `and`/`or` *value* idiom, deliberately not treated as an
if-condition (the note at the top of `sir/build.py`; M4 task 4 has since
replaced that refusal with `_match_cond_value`/`CondValue`, see
`structured-pipeline.md`) — are among the refusals.

Note the second row: **139 unique protos build a region tree but still do not
print, purely because a descendant closure does not.** `print_chunk` inlines
the whole tree at each `CLOSURE` site, so one unstructurable inner function
takes its entire ancestor chain with it. Recognizing `while` therefore pays off
super-linearly.

## 2. The printed-but-uncertified residual (58 unique protos) — LARGELY CLOSED (M4 task 13)

*The 58 became 283 as tasks 1-4 pushed more protos through the printer, then
**35** after `783d15c` made register classification per `(register,
definition)` rather than per register number — the extra-`MOVE` cluster this
entry is about went from 253 to 4. The 35 that remain are broken down by
opcode-histogram delta AND by first differing field in
`structured-pipeline.md` -> "Current capability boundary" point 3; the two
decompositions agree exactly. The constant-pool-order sub-case below was
re-measured at 10 (from 9) and the rung declined again — M5 agenda item 4,
which M5 task 5 then CLOSED at 0 by fixing the defect that produced the
population (see item 4 below). Original entry follows.*

These print fine and recompile to a *different* proto. All 58 differ on `code`;
24 also on `maxstacksize`, 11 on `constants.len`, 11 on an individual constant.
This is the residual approximation in the freereg simulation
(`express/names.py::_stack_discipline`) — statement grouping and register
allocation that do not quite match luac's.

(An earlier pass of this breakdown also reported 1 of the 58 differing on
`is_vararg`. Re-measured (round 1): that entry is basis-dependent, not a real
member of this set. Certifying all 58 with `is_chunk_root` matched correctly
to whether each proto actually is a file's main chunk yields **zero**
`is_vararg` mismatches; the "1" appeared only when the one main chunk among
the 58 was certified in wrapper isolation (`is_chunk_root=False`, the
nested-proto path) instead. Every other figure in this breakdown holds under
both bases.)

**Sub-case worth deciding explicitly: constant-pool interning order.** Measured
at `fb85f2f`: 22 of the 58 have a differing constant pool, and **9 of them
differ ONLY by the pool's order** — the same constant multiset, and `code`
becomes identical once our constant indices are permuted onto the original's,
with `maxstacksize` already equal. That is arguably a legitimate ladder rung
(`L3.2 = canonicalise constant-pool order`) and it was **deliberately not
added** during M3: it would need its own soundness argument (a permutation of
the pool is only meaning-preserving if every RK reference is remapped
consistently and no instruction depends on an index's numeric value), and
adding a rung to buy 9 protos while `while` is worth 162 was the wrong order of
work. An earlier measurement, at the code state before the "pre-declare
parameters" change, put this at 8; do not treat either number as fixed.

## 3. Effect-lattice calibration (spec M4) — DONE (M4 task 11)

*Closed 2026-08-12. Evidence `tests/test_effects_modes.py`, per-row argument
in `lift/effects.py`'s `_row` comment block and `EffectMode` docstring, write-up
in `structured-pipeline.md` → "The effect lattice". Outcome: `STRICT` stays the
default; `NO_METAMETHOD` is a permitted per-pass opt-in scoped to
script-constructed tables (the census finds 0 metamethod-related constants in
71414 constants, but 56 of 164 global names read are never written by the corpus
and so come from the engine, where the census is blind); `TRUSTING` is not
recommended — it moves only 3 rows (`GETGLOBAL`/`GETTABLE`/`SELF`) and the corpus
falsifies all three. `lift/effects.py`'s behaviour is unchanged. Two rows were
found under-graded and left alone pending the full axiom-change protocol: `LEN`
at `NO_METAMETHOD`, and `NEWTABLE`/`CLOSURE`'s GC path. The original entry
follows.*

`lift/effects.py` grades every opcode under three modes — `STRICT`,
`NO_METAMETHOD`, `TRUSTING`. Per CLAUDE.md **only `STRICT` has a
justification**; the other two columns are asserted, not argued. Calibrating
them against the 229-file corpus (which metamethod assumptions actually hold
for this game's scripts?) and choosing a defensible default is M4 work.

Note what M3 established about *why* this matters, because it is easy to
overrate: the effect lattice is **no longer the inlining gate**. M3 task 8
deleted `_adjacent_pure` and the `EffectMode` knob from `express/names.py` and
replaced them with a simulation of `lparser.c`'s own `freereg = nactvar`
discipline. Loosening the effect-based barrier was measured at **+0.0 protos**;
the freereg simulation was worth **+63.6 points**. So calibrate the lattice
because downstream passes (a real pass registry, reordering-based
beautification) will need it — not because it is expected to move the L3 rate.
Full story in `structured-pipeline.md`, "Register classification".

## 4. `TAILCALL` is missing `writes_open` in the axiom layer — DONE (M4 task 8)

*Everything until "Closed — M4 task 8" below is the record as it stood before
the fix, kept verbatim because it contains a retracted claim that must not be
re-derived. Present tense in it means "before M4 task 8". The resolution, and
the reason the differential moved nothing, are in that closing subsection.*

`lift/effects.py`'s `TAILCALL` row returns `writes=∅, writes_open=0`. That is
under-approximate: in `lvm.c`'s `OP_TAILCALL`, the `PCRC` branch
(`lvm.c:630-632`, a non-Lua callee) leaves the callee's results at
`R[a..top)` for the immediately following `RETURN A 0` to read.

It does **not** currently break anything — `OP_TAILCALL` always has `C == 0`
(`lvm.c:611`: `lua_assert(GETARG_C(i) - 1 == LUA_MULTRET)`), so no emitter
template touches a register beyond `R[a..a+b)`, and the consistency gate
(3 corpus `TAILCALL` rows, all with `B != 0`) passes. Fixing it properly needs
what CLAUDE.md requires of any axiom-layer change: the `lvm.c` citation above
*plus* a differential run, because adding `writes_open` puts every `TAILCALL`
pc into `classify_registers`' `open_write_pcs` and can move classifications and
therefore the committed ledger.

This was argued above only on the emitter side. `open_write_pcs` has a second
consumer, `express/names.py::classify_registers` (which builds
`open_write_pcs`) and its nested `_staging_slice`, where it gates a for-loop's
backward staging-producer search (`_staging_slice`): if an open-write
instruction sits between a candidate producer and the loop header consuming
it, the search gives up rather than attribute the register. A missing
`writes_open` on `TAILCALL` could let that search walk straight through one.

What *is* established: `OP_TAILCALL` is emitted from exactly one call site,
`lparser.c:1251` inside `retstat`, which unconditionally calls
`luaK_ret(fs, first, LUA_MULTRET)` immediately afterward with no intervening
`luaK_code*` call — `luaK_ret` compiles to `OP_RETURN A 0` (`lcode.c:69-71`:
`luaK_codeABC(fs, OP_RETURN, first, nret+1, 0)` with
`nret == LUA_MULTRET == -1`). So **a `TAILCALL` is always immediately followed
by exactly one `RETURN A 0`**. All 3 corpus occurrences confirm this half
(re-measured 2026-08-11, script below).

**What is NOT established — and a previous revision of this file claimed it
was.** That `RETURN` is *not* the end of the function. It is the end of a
`return` *statement*, which can sit inside an `if` arm with more code after
it. Every corpus `TAILCALL` contradicts the terminality claim:

```
snr_common.lua:main_26  TAILCALL@6  next=RETURN A=3 B=0 C=0  lastpc=8  terminal? False
snr_common.lua:main_29_0  TAILCALL@8  next=RETURN A=2 B=0 C=0  lastpc=18  terminal? False
snr_common.lua:main_29_0  TAILCALL@16  next=RETURN A=2 B=0 C=0  lastpc=18  terminal? False
```

`main_29_0` is the clearest case — an if/else where each arm tail-calls:

```
  8 TAILCALL A=2 B=3 C=0
  9 RETURN   A=2 B=0 C=0     <- ends the `return` statement, not the function
 10 JMP      ...             <- ...and there are 8 more pcs after it
 ...
 18 RETURN   A=0 B=1 C=0
```

So a for-loop header downstream of a `TAILCALL` is **not** structurally
excluded, and the `_staging_slice` argument is unsupported. **The
differential run stays required** before touching the `TAILCALL` row — it is
the thing that would settle this, and it is M4 work. Do not let the
`lparser.c` citation, which only covers the first half, be read as a licence
to skip it.

### Closed — M4 task 8

The differential run was done: `classify_registers`' four fields
(`locals`/`temps`/`loop_vars`/`temp_defs`) plus each proto's certification
level, rung and refusal reason, swept over all **1944 proto occurrences of
229 files** before and after the row change. **The two sweeps are
byte-identical: 0 protos changed in any field, 0 levels moved**, and
`scripts/run_corpus.py` reproduced `corpus/ledger.jsonl` byte-for-byte
(1389/1478 unique `L3`, 94.0%; 1855/1944 occurrences, 95.4%).

The reason it moved nothing is **not** the terminality argument retracted
above, and not "C is always 0" either. It is `_block_floor`:
`effects.successors(TAILCALL) == ()`, so `build_cfg` always ends a basic
block at a `TAILCALL` and makes the next pc a leader; `_staging_slice` never
looks below the loop header's own block entry, so a `TAILCALL` can never lie
strictly between a staging producer and the header consuming it. The
open-write barrier is unreachable for `TAILCALL` in real lifted code — a
structural argument, now pinned over the corpus by
`tests/test_effects_tailcall.py::test_corpus_lifted_tailcalls_all_end_their_basic_block`
rather than left as prose.

The row is nevertheless load-bearing, which a synthetic fixture proves: hand
a `LirFunction` a `TAILCALL` with a fall-through successor (an LIR luac will
not emit) sitting between three staging writes and a `FORPREP`, and the
control triple's verdict flips `temps -> locals` with the row. Neuter check
included.

One knock-on, worth knowing before touching the row again: the
effects–emitter consistency gate used to skip every instruction carrying an
open region, so an unconditional `writes_open` on `TAILCALL` silently removed
all 3 corpus `TAILCALL`s and all 196 grid `TAILCALL` rows from it. Task 8
removed that skip rather than accept the coverage loss (`_registers_touched`
never names an open region's registers, so the subset assertion was well
posed for those rows all along and the skip was discarding their static
half). Measured: 0 violations, +6981 corpus rows, +1 corpus opcode.

Re-derive the table:

```python
# PYLUADEC_CORPUS_DIR=... uv run python -
import os
from pathlib import Path
from pyluadec.ingest import load_file
from pyluadec.lift.opcodes import decode, Op
from pyluadec.pipeline import walk_proto_paths

for f in sorted(Path(os.environ["PYLUADEC_CORPUS_DIR"]).glob("*.lua")):
    protos = {}
    walk_proto_paths("main", load_file(f), protos)
    for path, p in protos.items():
        for i, w in enumerate(p.code):
            if decode(w, i + 1).op is not Op.TAILCALL:
                continue
            pc, lastpc = i + 1, len(p.code)
            n = decode(p.code[i + 1], pc + 1) if i + 1 < lastpc else None
            print(f"{f.name}:{path}  TAILCALL@{pc}  "
                  f"next={n.op.name} A={n.a} B={n.b} C={n.c}  "
                  f"lastpc={lastpc}  terminal? {pc + 1 == lastpc}")
```

## 5. Deepen the global-state probe toward L2 (Task 9 Deliverable B) — DONE (M4 task 10)

*Everything until "Closed — M4 task 10" below is the feasibility record as it
stood before the gate was built, kept verbatim because several of its numbers
were re-measured and two of them did not reproduce.*

**These are Task 9 measurements, recorded here rather than re-derived.** The
question was whether invoking each newly-defined global function under a
stubbing `_G` — instead of only serialising the globals a chunk writes — is a
viable standing gate. Verdict: **viable, as an M4 task.**

- **Reach.** 228/229 files produce a non-empty behavioural trace (only
  `config.lua` defines no function). **397,317 recorded engine calls** versus
  today's **452 compared globals** — three orders of magnitude more observed
  behaviour.
- **Determinism.** 229/229 byte-identical across three separate processes,
  after neutralising `tostring(table)` addresses and instruction-count budgets.
  No time/random/`pairs` leakage found.
- **Agreement.** 226/229 between original and decompiled, with **zero new
  decompiler defects**. Two divergences (`snr_common`, `snr_mainmenu`) are the
  same `getobjname` naming artifact documented above; the third (`snr_novel`)
  is the **same multiset of calls in a different order**, driven by the file's
  single `pairs` loop — i.e. the first corpus-level *runtime* evidence for
  backlog item 5 (table internal layout).
- **Cost.** 2.7s for all 458 probe runs; ~**+3s** as a standing gate. Payload
  median 48,081 B, 11.5 MB total, so store a per-file SHA-256 and dump the full
  trace only on mismatch.
- **Stub-return policy** (guess / zero / nil) changes 202–203 of 229 traces but
  agreement stays 226/229 under all three: the guess decides *what you
  observe*, not *whether the two sides agree*.

**The design finding that matters more than the numbers: the budget must be a
recorded-EVENT count with a generous instruction backstop.** An instruction
budget alone — the shape the predecessor's `blackbox_runtime.py` uses — drops
agreement from 226/229 to **95/229**, purely by truncating the two
representations at different points. Measured, not assumed.

Deferred out of M3 because it wants the `__pld_R` naming noise pinned or
normalised first; it will stay red on `snr_novel` until backlog item 5 lands;
and a 3000-event cap truncating 132/229 game loops is a reach ceiling that
argues for a key-sequence-driven harness rather than a bare `pcall(main)`
(cf. the predecessor's `DEBUG_KEY_SEQUENCE_HARNESS.md`).

### Closed — M4 task 10

Built as `scripts/probe_behaviour.lua` + `scripts/probe_behaviour.py`, gated by
`tests/test_behaviour_probe.py`. See "Behaviour probe (L1.75)" below for what it
does, what it reaches and what it does not. Everything re-measured 2026-08-12 on
macOS arm64 against the M4 tree (212/229 files shipping structured source):

| claim above | re-measured | verdict |
| --- | --- | --- |
| 228/229 non-empty traces | **229/229** | improved (this probe records the chunk's own global writes, so `config.lua` is no longer empty) |
| 397,317 recorded engine calls | **398,196 events** | reproduces |
| 226/229 agreement | **227/229** | improved (M4's loop work flipped 120 more files to structured) |
| divergences: `snr_common`, `snr_mainmenu`, `snr_novel` | **`snr_mainmenu`, `snr_novel`** | `snr_common` converged |
| 2.7s for 458 probe runs | **3.14s serial, 1.06s over 8 threads** | reproduces |
| payload median 48,081 B, 11.5 MB total | **median 33,068 B, 13.6 MB total** | different shape, same order |
| 3000-event cap truncates 132/229 | **132/229** | reproduces exactly |
| stub policy is agreement-invariant | **NO — see below** | contradicted |

**Contradicted: the stub-return policy is not agreement-invariant.** Measured
over the corpus at 227 / 227 / 226 / 226 for
nil-with-name-heuristic / always-nil / always-zero / the predecessor's
zero-defaulted guess. The two zero-defaulted policies surface one *extra*
instance of the same pinned `getobjname` class (`snr_common.lua`:
`bad argument #1 to 'len'` vs `to '?'`), not a new defect — so the feasibility
claim is right about the *class* of what the policy decides, and wrong that the
count is invariant. The frozen policy is the nil-defaulted heuristic, which is
both the best-agreeing and (by 9 events out of 398,196) the deepest-reaching.

**The event-budget finding held, and now has corpus-scale evidence.** At the
same 3000-event cap, `snr_s4_10_s.lua` executes **6.51M** VM instructions on the
original side and **78.35M** on the decompiled side — a **12x** ratio — and
still produces a byte-identical trace. Any instruction-count budget between
those two numbers truncates one side and not the other. Across the corpus the
worst case is that same 78.35M, so the frozen 400M backstop has **5.1x**
headroom over the deepest real run; no corpus file reaches it (asserted).

Still open after this task: the 3000-event cap truncates 132/229 files
mid-loop, so a key-sequence-driven harness (spec M5, cf. the predecessor's
`DEBUG_KEY_SEQUENCE_HARNESS.md`) remains the way past the reach ceiling; and
`snr_novel` stays pinned until backlog item 5 (table internal layout) lands.

## Behaviour probe (L1.75)

Loads a chunk under a stubbing environment, runs it, then **invokes every global
function the chunk defined**, recording a deterministic trace of the engine
calls, stub-table writes, prints and errors that result. The original bytecode
and our decompiled output are compared on that trace.

**`scripts/probe_behaviour.lua` is the single source of truth** for the trace
format, the frozen constants and the stub policy — describe it here, read it
there; the earlier inline copy of the L1.5 probe in this file went stale the
moment the probe was fixed. The Python driver is `scripts/probe_behaviour.py`
(`probe_raw(payload, *, is_source) -> bytes`, `digest`, `header`,
`first_difference`, `dump_mismatch`, a whole-corpus `main()`); the standing gate
is `tests/test_behaviour_probe.py`.

Output is `PROBE1|<status>|<event count>` followed by one line per event, or
`LOADFAIL|<message>`; anything else, or a non-zero exit, raises `ProbeError`
rather than becoming a comparable value. The comparison unit is a SHA-256 over
the raw bytes — nothing decodes the trace, because it embeds corpus string
constants that are frequently not UTF-8.

### Result over the full corpus (M4 task 10)

**229 files, 227 byte-identical, 2 pinned divergent, 0 probe failures,
398,196 recorded events.** Status split on the original side: 97 `OK`,
132 `CAP` (hit the 3000-event budget), 0 `INSN`.

**Reach is bimodal, not a uniform deepening — read the split, not just the
total.** The 132 `CAP` files contribute exactly 3001 events each (396,132 of
398,196, i.e. 99.5%); the other 97 `OK` files contribute a median of just
**10** events (min 3, max 292; 62 of the 97 at ≤20, 96 of the 97 at ≤100).
"398,196 compared units" reads as a uniform three-orders-of-magnitude
deepening over the L1.5 gate's 452 globals; for 97 of the 229 files it is
closer to "9–10 engine calls where L1.5 saw 1 global". Measured 2026-08-12,
same session as the table below. `test_invocation_loop_covers_every_recorded_function_global`
(`tests/test_behaviour_probe.py`) is the cheap ratchet against this: it
asserts that every function-valued global an `OK`-status run recorded a `G|`
write for also has a matching `I|` invocation event, which
`test_corpus_reach_is_not_vacuous`'s bare `assert n > 0` cannot catch (that
assertion is satisfied by `config.lua`'s 3 bookkeeping events with no
invocation at all).

Reach against the L1.5 gate it deepens (both columns measured 2026-08-12):

| measure | L1.5 global-state | L1.75 behaviour |
| --- | --- | --- |
| files with a non-empty payload | 224 / 229 | 229 / 229 |
| compared units | 452 globals | 398,196 events |
| payload, median | 22 B | 33,068 B |
| payload, total | ~65 KB | 13.6 MB |
| files whose payload is only `main=<function>` | 222 | 0 |

### The two pins, and the evidence for each

Both are pinned in `EXPECTED_DIVERGENCE` (`scripts/probe_behaviour.py`) as
exact `(original, decompiled)` first-differing-line pairs, adjudicated two-
directionally by `adjudicate_pins` (`scripts/probe_common.py`): a changed
message, a converged pair or a vanished file all fail the gate.

- **`snr_mainmenu.lua` — the `getobjname` artifact of the `__pld_R` box model**,
  the same class already pinned in the L1.5 gate. Both traces are 20 lines
  (header + 17 preceding events + the differing event + a trailing blank);
  both sides record the same 17 preceding events, then both fail with an
  arithmetic-on-nil error; exactly one trace line differs (asserted). The
  original does `GETTABLE 6 6 "library"`
  immediately followed by `ADD 5 5 6` (luac listing pcs 117/118, and identically
  at 299/300, 518/519, 743/744, 883/884 — every one composes the same message),
  so `kname` finds a *string* constant and says `field 'library'`. Our fallback
  emits that pair as `__pld_R[6] = __pld_R[6]["library"]` /
  `__pld_R[5] = __pld_R[5] + __pld_R[6]`, so the ADD's operand came from a
  `GETTABLE` whose key is the *number* constant 6; `kname` refuses a non-string
  RK and says `field '?'`.
- **`snr_novel.lua` — table iteration order.** The two traces are the same
  *multiset* of 43 lines in a different order (asserted). The file's only
  `pairs` loop is at pcs 24…37 of a main-chunk subproto and iterates
  `<upvalue>.layerNumber`. The original builds that table with
  `NEWTABLE 1 0 23` — a 29-entry hash-size hint — followed by 29 `SETTABLE`s;
  the fallback emits a bare `{}`, so luac gives it `NEWTABLE ... 0 0` and the 29
  inserts grow the node array by rehash instead. Different node array,
  different `next()` order. This is backlog item 5 with runtime evidence.

Both remaining pins are on files that still ship **fallback** output; the 212
files that ship structured source all agree.

### Non-vacuity

The L1.5 probe shipped once in a state where any probe-side failure returned
`""`, compared equal on all 229 files, and was counted as non-empty by the very
assertion meant to prevent vacuity. `tests/test_behaviour_probe.py` therefore
commits, rather than merely reporting, the checks that make the gate falsifiable:

- three **fault injections** on the real gate path — `+`→`-` and a `while` bound
  moved by one in `snr_crd_10.lua`'s *structured* output, and a FORLOOP limit
  `<=`→`<` in `snr_memory.lua`'s *fallback* output — each asserted to be a
  unique anchor first, so an anchor that stopped matching fails loudly instead
  of injecting nothing;
- an `os.exit` in the target must not truncate the trace and exit 0;
- five determinism overrides (`os.time`/`os.clock`/`os.date`, `math.random`,
  `collectgarbage`, `tostring(table)`, `os.getenv`) each covered by a synthetic
  case, precisely because the corpus never calls them and corpus green could
  never falsify them;
- the event budget asserted to be an event budget: two chunks with identical
  observable behaviour and wildly different instruction counts must produce
  identical traces;
- the instruction backstop asserted to fire on a loop that records nothing.

### Scope — do not assume more than this

Only top-level globals the chunk itself wrote are invoked, only those whose
value is a function, and always with **no arguments**. Functions reachable only
through a table field are never called. Unknown globals resolve to a stub proxy,
so what is observed is behaviour *under the frozen stub policy*, not under the
real PSP engine. State accumulates across the invocations in one run
(deliberately: deterministic, and it exercises code that depends on what an
earlier function set up).

## 6. Deferred minors carried out of M3

Non-blocking; each was verified as correct code with a documentation, coverage,
or robustness gap rather than a defect. Same status as the M2 list above.

**Provenance.** These are carried out of M3's per-task review ledger. At task 10
every `file:line` reference below was re-checked against the tree and corrected
where it had drifted; the *magnitudes* (event counts, timings) were **not**
re-measured and should be treated as the original observation, not as current
data. One entry was found to be outright stale on re-check and is annotated as
such — assume the same is possible of the others.

**Tests / fixtures**

- ~~`tests/synth.py` — the `_encode` iABC path (non-zero `b`/`c`) has no
  persisted regression test.~~ **CLOSED in `f97e61d`.**
  `tests/test_sir_regions.py::test_synth_mk_instr_roundtrips_fields:41-44`
  now covers it: a plain `mk_instr(Op.ADD, a=3, b=4, c=6)` case plus the
  `A=255`/`B=511`/`C=511` boundary that had previously only been
  hand-verified. Verified 2026-08-11; the entry above was stale when this
  file was written. (`tests/test_effects_emitter_consistency.py`'s synthetic
  grid also drives this path over 7448 rows, all of them since M4 task 8
  removed its open-region skip.)
- ~~`tests/synth.py` — `mk_cfg` duplicates `test_dom.py`'s own local
  `_mk_cfg`.~~ **CLOSED (M3 final-review round).** `test_dom.py` now imports
  `tests.synth.mk_cfg`; the bodies were line-for-line identical, so the swap
  needed no behaviour change. (The entry was itself corrected twice: recorded
  during M3 as "zero call sites", re-measured at task 10 as one call site
  (`tests/test_sir_build_acyclic.py`'s `mk_cfg(edges, entry=1)` call in
  `test_verify_single_entry_catches_block_reachable_via_a_non_dominating_path`)
  plus `test_dom.py`'s six.)
- ~~No shared corpus-proto cache across the corpus-scanning tests — roughly
  5–6s of redundant `load_file` + `lift_proto` suite-wide.~~ **CLOSED (M4
  task 9 round 1).** `tests/conftest.py::lifted_corpus` is that session-scoped
  fixture. Its docstring names the three consumers it could NOT absorb and why.
  Cost re-measured M4 task 12: **~0.97s** cold, **~1.05s** as pytest `setup`
  (the docstring's earlier "~0.69s" was a warm-process repeated-pass figure and
  understated what the suite pays; corrected in place).

**Code**

- `express/reconstruct.py::_emit_multi` — its justifying comment overstates the
  shadowing argument as runtime semantics; the real reason is the declare-once
  invariant.
- ~~`express/reconstruct.py::close_scope` — restores `env`, which could in
  principle resurrect an arm-consumed staged expression. Argued only in the
  forward direction.~~ **CLOSED (M4 task 12).** The backward direction is now
  in `close_scope`'s docstring and is a measurement, not an argument:
  **0 of 1853 `open_scope`/`close_scope` pairs over the whole corpus re-added
  any register to `_pending`**, so the hazard's antecedent never arises, not
  merely its consequent. Re-derive by wrapping the two methods and diffing
  `self._pending` across the restore.
- ~~`structure/structured.py` — `emit_certified_chunk` memoizes the root under
  `_memo_key(root)` in the same dict descendants read.~~ **CLOSED (M3 final
  review + M4 task 6).** Verified 2026-08-12: `ProtoCert.source`'s field
  comment now carries the well-foundedness argument (`structural_hash` folds
  subprotos recursively, so a proto cannot equal a strict descendant of itself
  absent a collision) *and* states that nothing reads `source` off a non-root
  cert, and the `root_key` block says why `main` is certified first rather
  than relying on `walk_proto_paths` iteration order. One stale number in that
  block was corrected at task 12: the re-print determinism check is **212/212**
  shipped artifacts, not the M3-era 92/92.
- ~~`scripts/run_corpus.py` — the forced-`L0` loop keeps
  `res.confessions_by_proto[path]`, which is `[]` for an individually-`L3`
  proto, so an `L0` row could ship **unconfessed**.~~ **CLOSED (M4 task 6).**
  `scripts/run_corpus.py::_force_l0` now writes both `refusal_reason` and, if
  the entry has none, a whole-range `fallback-state-machine` confession;
  pinned by `tests/test_ledger.py::test_forced_l0_entry_is_confessed`.
  Verified in place 2026-08-12.
- ~~`scripts/ledger_dashboard.py` — sorts the rung histogram by `kv[0]`,
  raising `TypeError` if any `L3` entry ever carried `l3_level: null`.~~
  **CLOSED (M4 task 6).** The sort key is now
  `(kv[0] is None, kv[0])`, which keeps the dashboard printable exactly when
  the invariant it would diagnose has broken. Verified in place 2026-08-12.
- `tests/test_express_names.py::_temp_write_violations` — its open-read model credits an
  `R[base..top)` read to *every* register `>= base`, so 14,369 corpus
  temp-writes pass "exactly one consumer" with no explicit reader. A genuine
  fix, but the accepted ceiling is undocumented.

**Probe (`scripts/probe_global_state.lua` / `.py`)**

- The *value* side of serialisation is still ambiguous (same family as the
  fixed key collision): `X="a" Y=1` and `X="a\nstring:Y=1"` serialise
  identically. Latent — 222/229 payloads are `string:main=<function>`.
- `strip_location` strips only the FIRST `<src>:<line>: ` prefix, so a
  re-raised error carries a second location that necessarily differs between
  the stripped `.luac` (`?:0:`) and our `.lua`. The one remaining way `ERR|`
  residue can be representation-dependent for a reason other than
  `getobjname`.
- ~~The CLI `main()` knows nothing about the pinned divergences — it prints
  `225/229` and returns 1, so anyone running the documented script sees a RED
  gate while the suite is green.~~ **CLOSED (M4 task 10).** The pin moved out
  of the test and into `scripts/probe_global_state.py` next to the CLI that has
  to honour it, and both CLIs now adjudicate through the shared
  `scripts/probe_common.py::adjudicate_pins` (unexpected / moved / gone), so a
  clean run prints `225/229 identical, 4 pinned divergence(s)` and returns 0
  while a converged or moved pin still returns 1.
- Table/function-valued **keys** still serialise via `tostring(k)` (an address,
  non-deterministic across the two probe processes). 0 occurrences today.
- `payload_of` splits `ERR|` on the first `|`, mis-splitting a message
  containing `|`. Harmless today.

**Performance**

- Suite went 12s → ~30s over M3 (task 10: 284 tests, 30.79s; re-measured
  2026-08-11 after the final-review round, 285 tests, 29.5s on macOS arm64),
  inherently: `test_ledger_ratchet` (10.2s at task 10, 9.5s on re-measure) and
  `test_corpus_compile` (8.7s / 8.6s) now pay one `luac_sz4` subprocess per proto, and
  a review agreed neither should be sampled. But `emit_certified_chunk`'s memo
  is per-chunk while the corpus has 1478 unique keys over 1944 protos — a
  process-level memo would cut roughly 24% of the subprocess cost.
  **Re-measured at the M4 wrap (2026-08-12): 512 tests, 40.0-40.7s against a
  45s ceiling.** The two heaviest entries are now `test_ledger_ratchet` at
  **11.7-12.1s** (29%) and `test_behaviour_probe`'s setup at **10.0-10.1s**;
  `test_corpus_compile` has dropped to 0.6s because it consumes the
  session-scoped `decompiled` fixture. So the memo item did not get done and
  the two subprocess-bound tests are now 54% of the wall clock — carried
  forward as **M5 agenda item 12**.

## 7. Not in scope for M4, recorded so it is not re-litigated

*Disposition at the M4 wrap (task 12) added to each. None was done in M4; the
first and third are now M5 agenda items 6 and 2.*

- **L2 differential-execution certification** (stub environment + trace
  comparison + coverage badge) and key-sequence regression — spec M5. The
  global-state probe is L1.5, not L2. *(M4 built an L1.75 behaviour probe,
  which deepens the evidence but is still not L2 — see M5 agenda item 6 for
  the measured reach ceiling.)*
- **Variable-name semanticisation** (`l0_0` → a meaningful name) — needs a
  debug segment or heuristics; this corpus is stripped. M4+ at best, and of
  questionable value. *(Still open, still of questionable value. The M4
  readability evaluation compared our `l0_0` against the predecessor's `v0`
  and found them roughly equivalent — both synthesized, ours additionally
  encoding closure depth — so this buys less than it looks like. 4443
  `l<d>_<d>` occurrences in our structured output; 19419 `v<d>` in the
  predecessor's.)*
- **Full ratchet CI** (baseline diff, downgrade = fail, `git bisect`
  integration) — spec §5's complete form. M3 only guarantees the ledger fields
  can support it. *(Not done in M4 either; M4 added `refusal_reason`, which is
  what makes it cluster usefully. Now M5 agenda item 2.)*
- The predecessor's `test_ir_pipeline.py` (86 cases) translation list — per
  spec §8 this is generated from M3's per-function level data, so it is an M4
  *input*, not an M4 deliverable. *(Not consumed in M4; the semantic
  regression port (`70fede6`) took the 5 named + 6 roundtrip cases instead.
  Still available as an M5 input.)*

## 8. The effects–emitter consistency gate does not cover the structured reconstructor — DONE (M4 task 9)

*Everything until "Closed — M4 task 9" below is the record as it stood before
the gate was built, kept verbatim because two of its counts were measured
false when the work was actually done.*

`tests/test_effects_emitter_consistency.py` (backlog item 2) reconciles
`lift/effects.py` against `structure/fallback.py`'s templates. It does **not**
reconcile it against `express/reconstruct.py` -> `emit/lua.py`, the structured
path. `express/names.py`'s register *classification* does consume `effects`,
but the reconstructor's per-opcode operand decoding is independent of it:
`reconstruct.py` reads `ri.a`/`ri.b`/`ri.c` directly at 9 call sites (`:434,
:444, :455, :456, :469, :521, :592, :611, :648`) and mentions `effects` at
exactly one place in the whole file (`:614`, a hazard check on
`reads_open`/`writes_open`, not an operand source); `emit/lua.py` reaches
operand fields through `ri.` 16 times in its non-docstring code and never
references `effects` at all. So `reconstruct.py` -> `emit/lua.py` is a
**third** independent hand-transcription of `lvm.c`'s per-opcode semantics,
sitting right next to the two the existing gate reconciles, with nothing
mechanically checking it against the table. Extending
`test_effects_emitter_consistency.py` (or a sibling test) to walk the
structured path the same way — assert the registers `Reconstructor`/`Printer`
touch for each pc are a subset of that pc's `effects.reads | effects.writes`
— is real M4 work, not a footnote.

### Closed — M4 task 9

`tests/test_effects_reconstructor_consistency.py` is that gate. Its module
docstring carries the full account; the essentials:

- **0 violations.** The reconstructor and the effects table agree everywhere
  the structured path reaches, on both arms. Nothing had to be adjudicated
  against `lvm.c`.
- **Mechanism: instrumentation, not a fourth transcription.** A recording
  shim wraps all 8 register-taking accessors of `Reconstructor` plus
  `express.names.name_for` (the only way a register becomes text in
  `emit/lua.py`), and attributes each touch to a pc taken from the code's own
  structure (`_dispatch`'s `li.ri.pc`, `condition_expr`'s `cond.ri.pc`,
  `write_reg`'s explicit `pc=` definition site, and so on). The `covered` set
  always comes from `LirInstr.effects`; nothing in the file models an opcode.
- **Two counts above were measured false.** `reconstruct.py` has **23**
  `ri.<a|b|c>` operand reads on 16 lines (not 9 call sites) and reaches
  `.effects` 3 times (not 1) — none of the three an operand source, which was
  the load-bearing half of the claim. `emit/lua.py` has **11** `ri.<field>`
  reaches (not 16), of which 3 are register indices; a fourth register decode
  (`ps.b` off a `CLOSURE` pseudo-instruction) is not an `ri.` reach at all and
  the old count missed it. `effects` is still 0 there, as claimed.
- **Reach: 37/38 opcodes** across the two arms — corpus 32, synthetic grid 33
  (imported from the sibling gate, not copied). Only `CLOSE` is unreachable,
  and it cannot be reached: the structured reconstructor refuses it, so a
  proto containing one never produces structured output. **Correction
  (round-1 review, 2026-08-12):** "reachable" here means "appears in
  `rec.ops`", which is weaker than "backed by a checked touch of its own
  row" for a handful of opcodes reached only through a multi-pc region
  frame. `FORPREP` is the sharpest case: it genuinely appears in
  `rec.ops`, but measured this round, emptying its `reads`/`writes`
  entirely produces **0** violations — no accessor or `name_for` call is
  ever compared against its own row, only against the row of whichever
  other pc in the same `NumericFor` region actually got touched. So the
  set of opcodes independently verified by their own row is `{CLOSE,
  FORPREP}` short of 38, not `{CLOSE}` alone. `JMP`/`FORLOOP`/`TFORLOOP`/
  `VARARG` are also reached via a multi-pc frame at least some of the
  time but, unlike `FORPREP`, are each independently load-bearing too
  (own-row fault injections still report violations: 19 for `FORLOOP`, 8
  for `TFORLOOP`, measured round-1). See
  `tests/test_effects_reconstructor_consistency.py`'s module docstring
  ("What it does NOT assert") and `test_forpreps_row_backs_no_checked_touch`
  for the full account.
- **A fourth register decode's coverage claim was also wrong.** The printer
  decodes 4 registers of its own (`NumericFor`'s `A+3`, `GenericFor`'s
  `A+3+i`, and a `CLOSURE`'s captured `ps.b`, i.e. 3 named spots but 4
  decodes counting `GenericFor`'s pair) — this doc and the gate's own
  docstring originally claimed "all four covered by Arm 2". Measured
  (round-1, 2026-08-12): of 907 corpus calls to `name_for(ps.b, depth)`
  under a `CLOSURE` frame, **907 pass via Arm 2's first disjunct and 0 via
  the frame's covered set** — only `NumericFor`'s `A+3` and `GenericFor`'s
  `A+3+i` are actually covered by the second disjunct. Worse, a strict
  `CLOSURE`-only check would be tautological: `lift.py` defines the row's
  extra reads as exactly `{ps.b for ps in closure_pseudo if MOVE}`, the
  same tuple `emit/lua.py` reads, so no effects-subset gate could ever
  fail on it even if miswired. Restated as an exclusion, not a coverage
  claim, in the gate's own docstring.
- **Cost: 2.0s** for the instrumented whole-corpus pass (229 files, 213
  chunks printed, 1821 proto bodies entered, 423336 accessor touches, 12118
  printed names), 0.23s for the grid. Paid for by folding
  `test_effects_tailcall.py`'s two independent corpus walks into one shared
  module-scoped census: 0.95s -> **0.25s** (re-measured round-1,
  2026-08-12, median of 3; this entry and the task-9 report previously said
  0.26s, which did not reproduce), assertions unchanged.
- **Round-1 fix round (2026-08-12).** Beyond the two corrections above: `F3`
  moved `_Recorder.accessor`'s `_fn_regs` bookkeeping onto its accepting
  paths only, so Arm 2 can independently corroborate an Arm 1 failure
  instead of always seeing the register as already-reconciled; `F4`
  replaced a bare `IndexError` catch with counted-and-pinned refusal shapes
  after narrowing it outright turned out to break an already-anticipated
  refusal (`_fold_concat` on a CONCAT-B>C grid row); `F6` measured
  `pcs_frame`'s "no LirInstr for this claimed pc" branch at **0/374725**
  hits on the corpus rather than leaving it asserted-and-unmeasured. No
  `src/` change; four new pinned tests
  (`test_closures_captured_upvalue_is_covered_by_arm_one_only`,
  `test_forpreps_row_backs_no_checked_touch`,
  `test_the_grids_refusals_are_the_known_shapes_only`,
  `test_no_claimed_pc_is_missing_a_lir_instr_on_this_corpus`).

## 9. Match the candidate's strip mode to the original's — DONE (M4 task 7)

**Closed.** `certify_l3` and `certify_proto`'s wrapper path now compile the
candidate with `strip=not carries_debug(original)`. The corpus did not move:
`corpus/ledger.jsonl` and all 229 files in `build/decompiled/` are byte-identical
after `scripts/run_corpus.py`, because every corpus proto reads as stripped
(measured 2026-08-12: 1944/1944 have empty `lineinfo`, `locvars` and
`upvalues`). Rung 1 now compares real locvar scope ranges on unstripped input,
which the negative control in `tests/test_certify_stripmode.py` proves is
falsifiable: a candidate hoisting a local out of a `do` block, with
byte-identical `code`, is refused on `locvars` alone.

One thing this entry got wrong, worth keeping: it called the change **strictly
stronger**. Measured over 30 sources compiled both ways, 12 unstripped rows went
`L1 -> L3` and **2 went `L3 -> L1`** (`repeat f() until g()`,
`return a and b or c` — the printer materialises a `local` the original never
declared, invisible in `code`, invisible to a stripped candidate). A gate cannot
start examining a dimension and also promise never to reject on it; "stricter"
is the accurate word.

**That 12:2 ratio is a property of the one 30-source sample it was measured
on, not of the change** (round-1 correction, 2026-08-12) — the general rule is
"any reconstruction that materialises a table-base, index-target, or
condition value as a `local` the original never declared now refuses",
and it fires on ordinary code, not just `repeat`/`and`-`or`: a
second, independently-chosen sample of 30 ordinary one-liners gave 4 gains and
4 losses out of 29 printable sources, roughly 1:1, because that sample
happened to include four plain table/index assignments (`a.b = 1` and
similar). The full before/after tables for both samples, the two 12:2-sample
losses in full, and the general rule with an ordinary-assignment example are
in `structured-pipeline.md`, "The candidate's strip mode follows the
original's".

---

# M5 agenda

Everything below is **open unless its heading says otherwise**. It came out of
M4 and, like the M3 material above, would otherwise be lost with the SDD
workspace. Written at the M4 wrap (task 12, 2026-08-12). Numbered so items can
be cited; the numbering is not a priority order — sizes are noted per item.
Items closed during M5 keep their record verbatim and gain a "Closed" section,
same convention as §§1–9 above.

Provenance and honesty rules, same as the sections above: every figure quoted
here was measured this session unless it says otherwise, and where a figure
carried forward from an earlier task did not reproduce, the discrepancy is
stated rather than smoothed over.

## 1. Regrade `LEN` at `NO_METAMETHOD`: `PURE` → `READ_HEAP` (axiom layer) — DONE (M5 task 1)

*Everything until "Closed — M5 task 1" below is the record as it stood before
the change; present tense in it means "before M5 task 1". Its figures and
citations were re-measured and all of them reproduced. The figure that did
**not** reproduce is one the M5 plan added on top of this item — see the Closed
section.*

**This is a confirmed-wrong row in the axiom table.** It was found by M4 task
11 and left alone deliberately, because CLAUDE.md requires an `lvm.c` citation
*plus* a differential run for any axiom-layer grading change and task 11's
scope was the argument, not the change. It is filed here as a numbered OPEN
item because §3 above — where the finding is recorded — is marked DONE, and a
reader scanning for open work would skip it.

The evidence, already gathered:

- `lvm.c`'s `OP_LEN` routes a `LUA_TTABLE` operand to
  `setnvalue(ra, cast_num(luaH_getn(hvalue(rb))))`. `luaH_getn` (`ltable.c`)
  reads `t->array` — an unbound search plus, for the hash part, repeated
  `luaH_getnum` calls. It **reads the table**, and removing metamethods does
  not make it stop; Lua 5.1 has no `__len` for tables, so `NO_METAMETHOD`
  changes nothing about this path at all.
- As graded (`PURE` under `NO_METAMETHOD`), the row licenses reordering a
  `SETTABLE` across a `#t`, which changes its result. `READ_HEAP` is the exact
  grading. The string case (`lvm.c`'s `LUA_TSTRING` arm) really is `PURE`, and
  `LEN` at `TRUSTING` is fine — `PURE` is precisely what `TRUSTING` licenses.
  **The defect is confined to one column of one row.**
- **22 `LEN` sites in the corpus**, so it is not vacuous.
- It is the one row where the monotonicity heuristic would have passed it:
  `test_effects.py::test_effect_ladder_monotonic_for_all_opcodes` is satisfied
  by `ARB ≥ PURE ≥ PURE`.

Protocol to close it: the citation above, plus a differential run of
`classify_registers`' four fields and every proto's certification level/rung/
reason before and after, plus `scripts/run_corpus.py` reproducing
`corpus/ledger.jsonl` byte-for-byte. **M4 task 8 is the worked example** —
follow its shape, including the synthetic fixture that proves the row is
load-bearing even when the corpus cannot move.

### Closed — M5 task 1 (commit `b0852ff`)

The row is now `ARB / READ_HEAP / PURE`. `src/pyluadec/lift/effects.py`'s
`UNM | LEN` branch was **split** so the regrade could not drag `UNM` with it
(`UNM` at `NO_METAMETHOD` genuinely is `PURE`); `tests/test_effects_len.py`
pins both halves and owns the full record.

**Citations, all re-verified against `vendor/lua-5.1/src/` after the edit** —
the M4 ranges quoted above reproduced exactly:

| range | what it is |
| --- | --- |
| `lvm.c:514-533` | the whole `case OP_LEN:` |
| `lvm.c:517-520` | `case LUA_TTABLE:` → `luaH_getn` — a table never reaches the metamethod arm, so `NO_METAMETHOD` removes nothing |
| `lvm.c:521-524` | `case LUA_TSTRING:` → `tsvalue(rb)->len`, genuinely pure |
| `lvm.c:525-530` | `default:` → `call_binTM(..., TM_LEN)` / `luaG_typeerror` — the only metamethod arm |
| `ltable.c:560-576` | `luaH_getn`: reads `t->sizearray`, binary-searches `t->array[...]` (561-571) |
| `ltable.c:532-553` | `unbound_search`, the hash-part path |
| `ltable.c:435-449` | `luaH_getnum`, called repeatedly by the above |

**The differential run was null.** `classify_registers`' four fields
(`locals`/`temps`/`loop_vars`/`temp_defs`) plus every proto's certification
level, rung and refusal reason, swept over all **1944 proto occurrences of
229 files** before and after: the two sweeps are byte-identical (sha256
`5d5e4335…0efea3fe`), and `scripts/run_corpus.py` reproduced
`corpus/ledger.jsonl` byte-for-byte (`a45d8e06…7ddb1039`; 1389/1478 unique
`L3`, 94.0%; 1855/1944 occurrences, 95.4%).

Null was predicted, and the *reason* is stronger than the prediction: not only
does nothing in `src/` select `NO_METAMETHOD`, **nothing in `src/` reads
`InstrEffects.effect` at all.** Downstream consumes only
`reads`/`writes`/`reads_open`/`writes_open`; the lattice stopped being the
inlining gate at M3 task 8 and has had no consumer since. That is measured and
pinned (`test_nothing_in_src_reads_the_effect_field`), and it means **no
synthetic fixture can show this row load-bearing** the way M4 task 8's
`TAILCALL` fixture could — that row moved `classify_registers`, which reads
`writes_open`. Stated rather than papered over: this correction is
unobservable in today's pipeline and was made because the axiom layer is
supposed to be true.

**One knock-on, and one figure from the M5 plan that did not reproduce:**

- Knock-on: `LEN` **joins `TRUSTING`'s delta**. With both looser columns at
  `PURE`, `TRUSTING` moved nothing on this row; with `NO_METAMETHOD` at
  `READ_HEAP`, `TRUSTING`'s own assumption ("a table read may be reordered
  freely") is what takes it back to `PURE`. So `TRUSTING` now moves **4** rows
  below `NO_METAMETHOD`, not 3 — `GETGLOBAL`, `GETTABLE`, `SELF`, `LEN` — and
  all 4 are `# UNARGUED`. `NO_METAMETHOD`'s `# UNARGUED` count went 1 → 0 as
  planned.
- Did not reproduce: the M5 plan predicted "the 20/18 entailment split moves".
  **It does not.** `test_mode_columns_split_20_entailed_18_relaxed` passed
  unmodified: `LEN` was already one of the relaxed 18 (its `STRICT` column is
  `ARBITRARY` and its looser columns were below it) and it still is. The split
  is derived from `analyze()` rather than asserted in prose, which is exactly
  why the test settled this instead of a person arithmetic-ing it.
- Also re-measured and reproduced: **22 `LEN` sites** in the corpus, across
  **8** protos of the 1944.

Suite after: **516 passed in 42.09s** (4 new tests, all in
`tests/test_effects_len.py`, which costs 0.04s on its own).

### Recorded beneath item 1, deliberately NOT to be fixed

These two came out of the same review and are **not** defects to schedule.
They are here so they are not rediscovered and re-litigated:

- **`NEWTABLE`/`CLOSURE` are `PURE` with `may_error=False` despite
  `Protect(luaC_checkGC)`.** `luaC_checkGC` can advance the collector into
  `GCSfinalize`, where `GCTM` fetches a userdata's `TM_GC` and calls it via
  `luaD_call` — so an allocation *can* run arbitrary Lua and *can* raise. The
  scoping is nevertheless correct for Lua 5.1: the allocator has no emergency
  `luaC_fullgc`, a script can only manufacture userdata via `newproxy`, and
  the census finds 0 `newproxy` and 0 `__` anywhere in 71414 constants.
  Flipping these rows would make every allocating opcode `ARBITRARY` —
  technically defensible, practically useless. `CONCAT`'s `NO_METAMETHOD =
  PURE` inherits the same blind spot (string interning allocates) and is
  graded consistently with them rather than singled out.
- **`OP_CONCAT` declares `writes = {a}`, but `luaV_concat` mutates the operand
  stack slots in place**, so it clobbers registers in `[b, c]` at *all* modes,
  not just under a relaxed one. **231 `CONCAT` sites in the corpus.** No
  documented scratch-register convention exists anywhere in `lift/` or in
  either runbook, which is the actual gap: the emitter and the reconstructor
  happen not to depend on those slots surviving, but nothing says so and
  nothing checks it. If item 1 is picked up, write that convention down in the
  same pass — it is cheaper than rediscovering why a future pass that reuses
  `[b, c]` after a `CONCAT` produces wrong code.
  **Status after M5 task 1: item 1 was picked up and this was NOT done.** The
  task's brief scoped it to one cell of the `LEN` row plus the mode-column
  census, and writing a scratch-register convention means auditing every
  consumer of `CONCAT`'s operand range, which is its own piece of work. The
  trigger is left standing here deliberately, pointed at whoever next touches
  `express/reconstruct.py`'s handling of `CONCAT`.

## 2. Full ratchet CI — baseline diff, downgrade = fail (spec §5's complete form) — DONE (M5 task 8)

*Everything from "Carried from §7" to the "Closed" heading below is the record
as it stood before the change; present tense in it means "before M5 task 8".
All three of its figures were re-measured and reproduced exactly. The one
number it did not carry — what splitting the key would cost — is in the Closed
section.*

Carried from §7 above, where it was scoped to M4 and did **not** get done. M4
delivered the field that makes it *useful* (`refusal_reason`, so a regression
clusters by cause rather than by string equality) but not the CI itself.

What exists: `tests/test_ledger_ratchet.py` (the ledger is a byte-exact fixed
point of its own generator), `tests/test_m3_exit.py` and
`tests/test_m4_exit.py` (within-row coupling between level, rung, confession
and reason; rate floors at 50% and 85%).

What does not: **any comparison against a committed historical baseline.** A
regenerated ledger with fewer `L3` rows passes the entire suite as long as the
rate stays above the floor and no `L0` appears. "Levels only ever go up" is
discipline plus a human reading the ledger diff. Two places quantify the
resulting exposure: `tests/test_sir_while.py`'s census floor is
measured-minus-10, so a 9-proto recognizer regression is green; and
`test_m4_exit.py`'s 85% floor sits ~9 points below the achieved 94.0%. Both
gaps are deliberate (a floor set at the measurement is a tripwire), and both
are closed by the same instrument: a baseline diff.

**Fold in with it: the ledger's grouping key is unsound, though vacuously so
today.** `scripts/run_corpus.py` groups rows by `structural_hash` **alone**
and resolves any disagreement by taking the higher level, on the stated
assumption that one structural hash implies one verdict.
`structure.structured._memo_key` deliberately does *not* make that assumption
— it keys the certification memo on `(structural_hash, _debug_fingerprint)`,
because `structural_hash` drops `source`, `linedefined`/`lastlinedefined`,
`lineinfo`, `locvars` and upvalue names, every one of which `compare_protos`
checks. Measured 2026-08-12: **16 of the 1478 shash groups carry more than one
debug fingerprint**, and **0** groups disagree on level or rung, so the
max-by-rank is vacuous on this corpus and nothing asserts that it is. Two
things to do here, and they belong to this item because both move the
committed artifact: split the ledger key (or add a test pinning "no shash
group disagrees"), and do it in the same change that lands the baseline diff,
so the one-off ledger movement is reviewed as a key change rather than as a
regression. The stale claim in `run_corpus.py`'s comment was corrected at the
M4 whole-branch review; the behaviour was deliberately left alone.

**Also fold in: `tests/test_generated_semantic_cases.py` runs 1/8 of itself by
default.** `DEFAULT_LIMIT = 3` against `CASE_COUNT = 24`, so the standing suite
exercises 3 of the 24 ported differential-execution cases; the full sweep is a
manual `PYLUADEC_GENERATED_CASE_LIMIT=24` run. That was a deliberate
suite-budget choice (the full sweep costs ~1.7s, but the budget was tight at
the time), and it means the ported fuzz harness is mostly *available* rather
than *standing*. A ratchet CI is the natural place to run the full 24 —
nightly or on the baseline-diff job — rather than in the per-commit suite.

### Closed — M5 task 8 (commits `1127e25`, docs to follow)

All three parts landed. Authority for the details is
`docs/runbooks/structured-pipeline.md` → "Ratchet the ledger against a
baseline", "The `git bisect run` predicate", "CI: there is none", and "The
ledger's grouping key — pinned, not split".

**1. `scripts/ratchet_diff.py OLD NEW`.** Exits 1 on six regressions — level
downgrade, rung downgrade (a *higher* `l3_level` is a *weaker* proof), removed
row, an `L3` row carrying a `refusal_reason`, a per-occurrence `shipped` going
`structured` → `fallback`, and a row arriving at `L0` — printing the offending
rows grouped by `refusal_reason` cluster. 0 on upgrades, added rows and
schema-only differences; 2, never 1, on an unreadable input (bisect reads 1 as
"bad"). Two real diffs at the M5 task-8 commit: `eb08890` → HEAD is **41
upgraded, 0 downgraded** (L3 1389 → 1430); `bbe74f6` → HEAD is **318 upgraded,
0 downgraded** (1112 → 1430).

Non-vacuity is the deliverable and was treated as one. `tests/test_ratchet_diff.py`
is 16 tests, one per failure mode, each feeding a hand-mutated copy of the real
committed ledger and asserting a non-zero exit **naming the row**; and each of
the seven checks was individually neutered, with exactly its own test(s) going
red (level-downgrade takes 3 tests with it, the other six take 1 each).

The `git bisect run` predicate was **verified by running a bisect**, not
described: a scratch branch with four commits, one of which injects an early
`StructureError` into `sir/build.py`, was bisected against this commit's ledger
as baseline; it found the injecting commit in 20.1s / 2 probes and reported 681
clustered regressions. Scratch branch deleted.

**2. The ledger key: PINNED, not split. The ledger did not move** —
`corpus/ledger.jsonl` is byte-identical. Re-measured 2026-08-12 and reproducing
the figures above exactly: **16 of 1478** groups carry >1 debug fingerprint,
**462** fingerprints between them (446 more than one each), **0** groups
disagree on `(level, rung, refusal_reason)` — the last re-measured on the
*triple*, one field stronger than the `(level, rung)` this entry claimed, and
still 0. The number this entry did not have: splitting would take the ledger
from **1478 rows to 1924**, all 446 additions duplicate verdicts, landing in
the same commit as the instrument that diffs the ledger by row identity. So
`run_corpus.py::key_disagreements` asserts the invariant over every occurrence
instead, and `main()` refuses to write a violating ledger; the exposure figures
now print on every run. If it ever fires, the fix is to split the key.

**3. The full generated sweep** is gate 3 of `scripts/ratchet_job.sh`.
Re-measured: **24 cases in 2.48s** against **0.31s** for the standing 3 — so
this entry's "~1.7s" did not reproduce and the fold-in costs the ratchet ~2.2s
and the per-commit suite nothing.

**CI: there is none.** Checked — no `.github/workflows/`, no `.gitlab-ci.yml`,
no runner config anywhere in the repo. No workflow was invented for a repo that
has never had one; the ratchet is `scripts/ratchet_job.sh` (suite + baseline
diff + full sweep, 40.6s end to end), run at a wrap and before any merge that
touches the ledger. If a runner is ever added, that script is the job body.

Suite after: **655 passed in 36.6s** (636 in 36.0s before), against the 45s
ceiling; +19 tests, +0.6s, and the 16 new `ratchet_diff` tests need no corpus.

## 3. The 89 non-`L3` unique protos, and the 17 files still on fallback

The structuring residual after M4. `structured-pipeline.md` → "Current
capability boundary" is the authority; it censuses the 89 two independent
ways (by opcode-histogram delta at the divergence point, and by the first
field `_cmp` reported) and the two decompositions agree exactly. Summary:
54 refuse structuring somewhere in the subtree, 35 print and recompile to a
different proto.

The leverage is superlinear and is worth restating: `print_chunk` inlines the
whole tree at each `CLOSURE` site, so **one unstructurable inner function
takes its entire ancestor chain down with it**. That is why 54 of the 89 are
ancestor chains rather than independent defects, and why the 17 fallback files
are 17 rather than 89.

The 17 files, measured 2026-08-12: `config.lua`, `snr_common.lua`,
`snr_e1_10_s.lua`, `snr_fragment_main.lua`, `snr_graphic.lua`, `snr_lib.lua`,
`snr_mainmenu.lua`, `snr_memory.lua`, `snr_music.lua`, `snr_novel.lua`,
`snr_s1_10_s.lua` … `snr_s6_10_s.lua`, `snr_story_main.lua`. They are the
*large* ones: they are 17 of 229 files but **27623 of 57998 predecessor lines
(47.6%)** of the corpus's shipped text. Counting files overstates how much of
the corpus is structured; see `docs/reports/m4-readability.md`.

This item is not only a corpus statistic: two of `tests/test_semantic_regressions.py`'s
five named (synthetic, compiled-from-source-in-test, not corpus) cases hit the
same two clusters and stay pinned at `L1` today —
`test_counter_closure_and_dispatch_mix` (the `mismatch` "prints but does not
certify" residual) and `test_if_and_elseif_conjunctions_preserved` (the
`build_sir` "if targets out of range" refusal). Closing this item should make
both assertions in those two tests go stale on purpose, which is the signal
to update them.

## 4. The `L3.2 = canonical constant-pool order` rung: CLOSED at 0 (M5 task 5)

*Closed 2026-08-12. Do not re-open or re-measure. Original entry after the
verdict.*

**Verdict: the population is 0 and the rung is decided-not-doing.** M5 task 5
found that every proto that had ever been in this population was one defect,
not a normalization problem: `codecomp` (lcode.c:673-686) compiles `a > b` by
evaluating `a` then `b` and then exchanging the operands to emit `OP_LT`, and
`luaK_infix` interns `e1` before `e2` is parsed — so printing every `LT` as
`<` reversed the interning order of the two operands' constants.
`Reconstructor._reads_as_gt` recovers the `>`, and the re-measurement after
it (same exact method) returns **0 of the 48 remaining non-`L3` protos**.
`NORMALIZATIONS` and `LADDER_VERSION` were never touched. Full account:
`structured-pipeline.md` → "The `L3.2 = canonical constant-pool order` rung:
CLOSED, decided-not-doing".

*Original entry:* M3 measured 9 protos that differ from the original ONLY by
constant-pool order; M4 task 6 re-measured **10** against a bar of ≥20 and
declined again. (M5 task 5 re-measured **11** at its start, before its
fixes.) Buying 10 rows costs a permanent widening of the certification gate —
rung 2 would have to argue that permuting a pool is meaning-preserving, and
every future certification would then run under that admission. The full
measurement method (exact, not a proxy) is in `structured-pipeline.md`. Either
argue the rung properly or close this item; it has been re-measured twice at
essentially the same number and re-deciding it a third time is waste.

## 5. Table internal layout: `next`/`pairs` order (M2 backlog item 5, still open)

The last remaining behavioural-probe pin, and the one place we have
**corpus-level runtime evidence** of a real semantic gap rather than a
theoretical one. `snr_novel.lua`'s single `pairs` loop iterates a table the
original builds with `NEWTABLE 1 0 23` (a 29-entry hash-size hint) followed by
29 `SETTABLE`s; the fallback emits a bare `{}`, luac gives it `NEWTABLE ... 0
0`, and the 29 inserts grow the node array by rehash instead. Different node
array, different `next()` order — the two traces are the same *multiset* of 43
lines in a different order.

Note the scope carefully: presize fidelity is already guaranteed *indirectly*
for anything that certifies `L3` (`NEWTABLE`'s `B`/`C` are part of `code`, so
a wrong split cannot certify). The gap is confined to protos still on the
fallback path, which is why this item shrinks as item 3 progresses and why
`snr_novel` is one of the 17.

## 6. L2 differential-execution certification, and the key-sequence harness

Spec M5 proper. The behaviour probe (L1.75) is the deepest instrument today
and its reach ceiling is measured, not guessed: **the 3000-event cap truncates
132 of 229 files mid-loop**, and those 132 contribute 396132 of the 398196
recorded events (99.5%) while the other 97 files contribute a median of **10**
events each. "398,196 compared units" therefore reads as a uniform
three-orders-of-magnitude deepening and is not one. Getting past that ceiling
wants a key-sequence-driven harness rather than a bare `pcall(main)` — cf. the
predecessor's `pyluadec/DEBUG_KEY_SEQUENCE_HARNESS.md`, which carries two
concrete historical bug checkpoints that convert directly into regression
cases.

## 7. Extract `express/names.py::_stack_discipline`

Deferred during M4 task 13 and recorded **only in a gitignored report**, which
is exactly the failure mode this file exists to prevent. Re-derived
2026-08-12: `_stack_discipline` is **462 lines with 33 `if`s and 11 nested
closures** (`_same_block`, `_pending_def`, `_renders_as_literal`,
`_bar_literal_operands`, `mark`, `mark_def`, `do_read`, `read_open`, `pop_ge`,
`promote_all`, `push`) inside an **831-line** `names.py`; its sibling
`classify_registers` is another 278 lines with 4 nested closures. So one
function is 56% of the module.

It is also the most load-bearing code in the project by measured effect: the
`freereg = nactvar` simulation it implements was worth **+63.6 percentage
points** of L3 rate where the effect-mode lever it replaced was worth +0.0.
That is an argument for extracting it carefully and behind the certification
gate — which will refuse any behaviour change, making this unusually safe —
not for leaving it alone. (An earlier note put `names.py` at 832 lines; it is
831. Trivial, recorded because carried-forward numbers are how this project
gets bitten.)

## 8. The ledger's `refusal_reason` drops `Mismatch.path`

`structure/structured.py::_rejected` builds the reason as
`f"mismatch: {mismatches[0].field}"`, discarding `Mismatch.path`. Because
`compare_protos` recurses, the pc or field named in a chunk-root row's reason
can belong to a **deep subproto**, with nothing in the string saying so.
Verified 2026-08-12 on the committed ledger: `snr_lib.lua:main` has
`n_insns: 5` and reports `structure: pc 73: if targets out of range`.

Not a defect — the omission is deliberate, since `Mismatch.a`/`.b` are corpus
payload (actual code words and constants) that must not enter a checked-in
file, and `path` was dropped alongside them. But `path` is a proto path, not
payload, so it can be included; doing so is what makes the field usable for
item 2's clustering without opening the artifact to corpus text.

## 9. The `compile:` refusal vocabulary is unexercised

`test_m4_exit.py`'s `REASON_KINDS` commits four kinds. Measured on the
committed ledger 2026-08-12: `structure` 49, `mismatch` 35, `reconstruct` 5,
**`compile` 0**. The three producers in `structure/structured.py`
(`"compile: candidate chunk did not recompile"`, `"compile: candidate wrapper
did not recompile"`, and the `wrapper yielded N subprotos` form) are reached
by **no test and no corpus row**; the only `compile:` string any test asserts
is `run_corpus.py::_L0_REASON`, a different producer. A synthetic fixture that
makes the printer emit something `luac_sz4` rejects would close this; until
then a fourth of the committed vocabulary is asserted but not demonstrated.

## 10. Test-hygiene set (carried from the M4 task 2 review, unfixed)

Re-deferred at task 12 as a group rather than piecemeal, with one reason: they
are all in `tests/`, none changes behaviour, and the suite is at 40.0s against
a 45s ceiling — a batch that touches six test modules wants its own
measurement pass, not a wrap commit's leftover headroom. Individually:

- A dead loop-invariant condition inside an unpack generator.
- Three hand-rolled region walks that should be one `_CHILDREN`-driven
  generator. (`sir/regions.py::_CHILDREN` already exists and
  `tests/test_sir_regions.py` already asserts every Region-typed field has an
  entry, so the generator has a correct basis to be built on.)
- `mismatches[0].field` assertions that pin `_cmp`'s field *ordering* as a
  side effect of pinning its result.
- A fallback assertion coupled to the `__pld_` textual preamble rather than to
  the outcome it stands for.
- 15 `CASES` driven by a plain `for` loop that should be `pytest.mark.parametrize`
  (a failure currently names the loop, not the case).
- `Repeat.negated`'s name is inverted relative to its value (`A == 0` is the
  *un*-negated case). Recorded in `sir/regions.py::While`'s docstring and true
  of all three nodes carrying the field; left unrenamed **because no consumer
  reads it** — the printer derives polarity from the instruction's own A/C
  field. If a consumer ever appears, the rename must happen first.

## 11. Probe minors (`scripts/probe_global_state.*`, `scripts/probe_behaviour.*`)

All latent on today's corpus; each is a correctness trap for a *future* corpus
or a future probe user, which is why they are recorded rather than closed.

- The **value** side of global-state serialisation is ambiguous in the same
  family as the key collision that was fixed: `X="a" Y=1` and
  `X="a\nstring:Y=1"` serialise identically. Latent — 222/229 payloads are
  `string:main=<function>`.
- `strip_location` strips only the FIRST `<src>:<line>: ` prefix, so a
  re-raised error carries a second location that necessarily differs between
  the stripped `.luac` (`?:0:`) and our `.lua`. The one remaining way `ERR|`
  residue can be representation-dependent for a reason other than
  `getobjname`.
- Table/function-valued **keys** serialise via `tostring(k)`, an address that
  is not stable across the two probe processes. 0 occurrences today.
- `payload_of` splits `ERR|` on the first `|`, mis-splitting a message that
  contains one.
- The behaviour probe's shadow-table shape (`pfields`/`envfields`) keeps the
  proxy and `env` raw tables permanently empty, so `pairs`/`next`/`rawget` on
  a stub proxy or on `env` report them as EMPTY regardless of what was
  written — those three bypass metamethods and Lua 5.1 has no `__pairs`.
  Unexercised by this corpus; now commented at both sites (M4 task 12) rather
  than left to be rediscovered.

## 12. Process-level certification memo (suite performance)

`emit_certified_chunk`'s memo is per-chunk while the corpus holds 1478 unique
`_memo_key`s over 1944 protos, so the two heaviest tests pay redundant
`luac_sz4` subprocesses. Measured headroom: `test_ledger_ratchet` is **11.7s**
of a **40.0s** suite (29%) and `test_behaviour_probe`'s setup another 10.0s —
together 54% of the wall clock. A process-level memo was estimated at ~24% of
the subprocess cost. A review has already agreed neither test should be
*sampled*, so caching is the only lever left. The ceiling is 45s.

### Closed — M5 task 2 (commit `5b7d893`)

Done, and **two of the numbers above are wrong**; the mechanism that actually
paid is not the one this item describes.

- "the corpus holds 1478 unique `_memo_key`s over 1944 protos" — **false**.
  1478 is the number of distinct `structural_hash`es (it is the ledger's own
  unique-proto count). Distinct `_memo_key`s, which is what the memo is keyed
  on and must stay keyed on, number **1924** over the same 1944 occurrences
  (229 chunk roots + 1695 nested). Only 16 `structural_hash` groups carry more
  than one debug fingerprint, but those 16 hold **462** fingerprints between
  them, i.e. **446 more than one each** — and 446 is exactly 1924 − 1478, so
  the whole gap between the two counts lives in those 16 groups. (An earlier
  revision of this bullet said "~446 fingerprints", attaching the right number
  to the wrong quantity; re-measured 2026-08-12, both figures above reproduce
  exactly.) They are tiny repeated closures: 482 occurrences with 1–39
  instructions each, at 444 distinct `linedefined` values, and the largest
  single group is a **one-instruction** proto appearing 292 times under 273
  different line numbers.
- "~24% of the subprocess cost" — **false**, and it is 466/1944 = 24.0%, i.e.
  arithmetic on the wrong 1478. The true *intra*-pass redundancy is
  **20/1944 = 1.0%**. `scripts/run_corpus.py`, which makes exactly one pass,
  gains ~1%.

What actually recovered the time is **cross-pass** reuse, which this item did
not identify: the suite certifies the whole corpus at least twice per process
(conftest's session `decompiled` fixture, then `test_ledger_ratchet`'s fresh
`run_corpus.main()`), and the second pass is now free. A second full corpus
pass in one process costs **0.65s** against ~9s cold.

Measured on macOS arm64, 2026-08-12, same machine both sides:

| | before | after |
|---|---|---|
| full suite | 43.90 / 43.42 / 46.10 / 44.85 / 43.75s (516 tests) | 32.04 / 32.04 / 32.42s (519 tests) |
| `test_ledger_ratchet` (in suite) | 13.64 / 13.17s | 1.89 / 1.87 / 1.89s |
| `test_behaviour_probe` setup | 11.40 / 11.06s | 10.68 / 10.82 / 10.95s |

**~11.9s recovered** on the median (43.90 → 32.04), against a ≥6s target. Note
the "before" row: the item's own 11.7s/40.0s figures had already drifted to
13.2-13.6s of 43.4-46.1s, i.e. the suite was over the 45s ceiling on one run
of five before this landed.

The behaviour-probe setup is unchanged by design — it is the *first* payer.
`test_ledger_ratchet` run alone is still 9.8-10.0s. The saving is a transfer,
not a disappearance.

Implementation: the memo moved from `emit_certified_chunk` (per chunk) into
`structure.structured.certify_proto` (module-level dict, per process), keyed on
`_oracle_identity() + (is_chunk_root,) + _memo_key(proto)`. `is_chunk_root` is new
to the key and is a genuine soundness fix for the wider scope — it retires the
"a proto cannot equal a strict descendant of itself" argument that
`ProtoCert.source`'s field comment used to have to make. `corpus/ledger.jsonl`
is byte-identical (md5 `d4a5ac56938ef0e19f22e7d36a6be0d7` before and after).

Two costs, both accepted rather than hidden: a long-running process accumulates
1924 entries holding 4.08 MB of chunk `source` bytes (`clear_certification_cache()`
releases them), and `test_ledger_ratchet` no longer re-executes `luac` per
proto, so a hypothetical non-determinism in certification would now be masked
there rather than caught — recorded in `tests/conftest.py`'s `decompiled`
docstring, which previously promised the ratchet consumed nothing another test
computed.

**Round 1 (fix commit `0d3d1b6`)** changed two things and re-measured a third.
The oracle component of the key was `oracle_version()` memoized into a module
global, which is constant for the life of a process and therefore could not
partition the cache in any real scenario: the review demonstrated a warm cache
serving a stale `L3` after `PYLUADEC_BUILD_DIR` (a supported knob that
`oracle.build_dir()` re-reads per compile) was pointed at a `luac_sz4` that
refuses everything. It is now the binary's own `(path, mtime_ns, size)`,
re-`stat`ed per lookup, which catches both that swap and an in-place rebuild;
cost 17.8 µs per lookup, ~45 ms on a warm corpus pass, nothing measurable on
the suite. Second, the shared cache had no fence against a test poisoning it
under a `monkeypatch` (whose teardown restores the attribute but not the cache
entries computed under it): `tests/conftest.py` now snapshots and restores the
dict around every test, at a cost that six interleaved A/B full-suite runs
could not resolve against the suite's own noise (the fixture's docstring has
the table). Suite after both: **523 tests, 31.98–34.18 s over 12 runs**, the
spread being session-long thermal drift rather than anything in the diff;
`corpus/ledger.jsonl` still byte-identical (md5
`d4a5ac56938ef0e19f22e7d36a6be0d7`).

## 13. Readability items surfaced by the M4 evaluation

From `docs/reports/m4-readability.md`, which compares our output against the
predecessor's shipped text at `<predecessor>/post_process/input/` (229 UTF-8
files; `/root/pyluadec` in the original environment, measured at
`/Users/fotile96/pyluadec` on the machine that wrote the report). Each is a
place our output reads **worse**; none affects correctness, and none should be
done without deciding the downstream-coupling question in CLAUDE.md's
"下游耦合" section first.

- **Non-ASCII string constants print as decimal escapes** (`"\227\128\144…"`)
  where the predecessor prints readable UTF-8. For a Japanese visual novel
  whose entire downstream purpose is translation, this is the single largest
  readability gap in the output. It follows directly from the standing rule
  that bytecode-derived strings stay `bytes` and are never decoded, so
  changing it means adding a *presentation-layer* decode (with a documented
  fallback for the non-UTF-8 constants the corpus does contain), not relaxing
  the rule in `ingest`/`lift`.
- **No dot sugar for string keys**: we print `gameSave["myCard"][126]["hold"]`
  where the predecessor prints `gameSave.myCard[126].hold`. Purely an
  `emit/lua.py` change (a valid-identifier-and-not-a-keyword test, which
  `_ident` already implements for the other direction).
- **Function bodies are not indented.** A chunk-level `local f = function()`
  has its body at column 0 while an `if` inside that body indents normally,
  which reads as if the function had no block. The predecessor indents
  uniformly at 4 spaces. Note this may be *deliberate* downstream coupling
  (CLAUDE.md records that `post_process/`'s line-anchored regexes expect
  "顶层无缩进"), so check that before changing it.
- Unary minus prints as `(-1)` where the predecessor prints `-1`.

## 14. Still-open minors inherited from M2 and M3

Not re-verified at task 12 except where noted; see "Deferred minors carried
out of M2" and §6 above for the full text of each.

- `ingest/dispatch.py` — `_bridge_for()` outside the `try/except`, so a
  stale-`.so` width mismatch escapes as bare `RuntimeError`.
- `cfg/blocks.py` — the proven-equivalent `leaders.add(pcs[i + 1])` mutant;
  `Cfg.preds` sortedness untested.
- `cfg/dom.py` — `_reverse_postorder`'s recursive DFS mutates the
  process-global recursion limit in a `finally`.
- `lift/lift.py` — successor validation does not check `s in instrs`.
- `LUA_KEYWORDS` lives in `lift/opcodes.py` (a decoder) but is a codegen
  concern shared by three modules across two layers; `structure/__init__.py`
  and `verify/__init__.py` are empty while `lift/` and `cfg/` export curated
  `__all__`. (`emit/__init__.py` was brought into line at task 12 —
  `print_chunk_or_raise` is now exported.) Same open question, third
  instance (M5 task 6 round 2, Residual B): `emit/lua.py` imports from
  `structure/fallback.py` while `structure/structured.py` imports from
  `emit/lua.py` — a mutual dependency through `fallback.py`, undissolved
  because the shared codegen-side home neither of these needs yet exists.
- The `f"{path}_{i}"` proto-path convention is implemented independently at
  three sites; documented at all three rather than extracted, because the
  extraction needs a neutral home (same open question as `LUA_KEYWORDS`) and
  because a shared f-string would unify only the *spelling*, not the
  requirement that `walk_proto_paths`' index and the CLOSURE handler's `Bx`
  denote the same child. The test that would actually close it: assert one
  file's fallback `__pld_F` key set equals the set of `proto_path`s the ledger
  records for it.
- `verify/ledger.py` — `n_insns` is still write-only.
- `express/reconstruct.py::_emit_multi` — its justifying comment overstates the
  shadowing argument as runtime semantics; the real reason is the declare-once
  invariant.
- `tests/test_express_names.py::_temp_write_violations` — its open-read model
  credits an `R[base..top)` read to every register `>= base`, so 14369 corpus
  temp-writes pass "exactly one consumer" with no explicit reader. The
  accepted ceiling is undocumented.
- The three M2-era mutants that no test can fail (boxed parameters emitted
  unboxed, `UNM` as `0-(x)`, `FORLOOP`'s `step > 0` weakened to `>= 0`). The
  third manifests as a **hang**, not an assertion failure — any future mutation
  testing must keep `oracle.run_bytes`'s timeout in place.

# M3 backlog, and the M4 agenda

This file exists because the SDD execution workspaces (`.superpowers/sdd/...`)
are scratch and get deleted. It started as the M2 final-review backlog for M3;
at the close of M3 it absorbed M3's own deferred findings for the same reason.
It is an agenda, not a plan — plans get written with
`superpowers:writing-plans` when the milestone begins.

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
  gone — M3 added two more consumers, `express/names.py:57` and
  `emit/lua.py:123`, so it is now shared by three modules across two layers.
  The misplacement is still real; the fix is no longer "move it into
  fallback.py" but a shared codegen-side home. Lower priority than when it
  had one consumer.)*
- Duplicated proto-path convention — `pipeline.walk_proto_paths:57`,
  `fallback.py:254` (the CLOSURE child key) and `fallback.emit_chunk:379`
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
  `l3_level` is now read by `scripts/ledger_dashboard.py:31` (the `rungs`
  Counter, rendered at `:42`) and asserted by `tests/test_m3_exit.py`.
  `n_insns` is still write-only.)*
- ~~`scripts/ledger_dashboard.py` — reports aggregate counts only, never naming
  which files or protos are `L0` / `compile_ok: false`.~~ **CLOSED in M3
  task 8.** `ledger_dashboard.py:56-81` is a "Name names" block that prints
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

## 1. Loops: `while` / `repeat` / mixed and irreducible back edges

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

## 2. The printed-but-uncertified residual (58 unique protos)

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

## 3. Effect-lattice calibration (spec M4)

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
consumer, `express/names.py:129,203-205`, where it gates a for-loop's
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

## 5. Deepen the global-state probe toward L2 (Task 9 Deliverable B)

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
  (`tests/test_sir_build_acyclic.py:189`) plus `test_dom.py`'s six.)
- No shared corpus-proto cache across the corpus-scanning tests — roughly
  5–6s of redundant `load_file` + `lift_proto` suite-wide. A session-scoped
  fixture would fix it. (`tests/conftest.py` already does this for the far more
  expensive `decompile_file`; `test_effects_emitter_consistency.py` does it
  module-locally.)

**Code**

- `express/reconstruct.py::_emit_multi` — its justifying comment overstates the
  shadowing argument as runtime semantics; the real reason is the declare-once
  invariant.
- `express/reconstruct.py::close_scope` — restores `env`, which could in
  principle resurrect an arm-consumed staged expression. Unreachable (condition
  operands are consumed before `open_scope`), but only argued in the forward
  direction.
- `structure/structured.py` — `emit_certified_chunk` memoizes the root under
  `_memo_key(root)` in the same dict descendants read. Unreachable (the root's
  own structural view contains any descendant's), but the comment above it
  explicitly worries about exactly what the code still permits.
- `scripts/run_corpus.py:77-81` — the forced-`L0` loop keeps
  `res.confessions_by_proto[path]`, which is `[]` for an individually-`L3`
  proto, so an `L0` row could ship **unconfessed**. Latent (229/229 compile
  today) and `tests/test_m3_exit.py` would fail loudly, but "confess, don't
  guess" wants the `L0` path to record its own confession.
- `scripts/ledger_dashboard.py:42` — sorts the rung histogram by `kv[0]`,
  raising `TypeError` if any `L3` entry ever carried `l3_level: null`. The
  dashboard is exactly the tool you reach for when that invariant breaks.
- `tests/test_express_names.py:692` — `_temp_write_violations`' open-read model credits an
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
- The CLI `main()` knows nothing about the pinned divergences — it prints
  `225/229` and returns 1, so anyone running the documented script sees a RED
  gate while the suite is green.
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

## 7. Not in scope for M4, recorded so it is not re-litigated

- **L2 differential-execution certification** (stub environment + trace
  comparison + coverage badge) and key-sequence regression — spec M5. The
  global-state probe is L1.5, not L2.
- **Variable-name semanticisation** (`l0_0` → a meaningful name) — needs a
  debug segment or heuristics; this corpus is stripped. M4+ at best, and of
  questionable value.
- **Full ratchet CI** (baseline diff, downgrade = fail, `git bisect`
  integration) — spec §5's complete form. M3 only guarantees the ledger fields
  can support it.
- The predecessor's `test_ir_pipeline.py` (86 cases) translation list — per
  spec §8 this is generated from M3's per-function level data, so it is an M4
  *input*, not an M4 deliverable.

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
  proto containing one never produces structured output.
- **Cost: 2.0s** for the instrumented whole-corpus pass (229 files, 213
  chunks printed, 1821 proto bodies entered, 423336 accessor touches, 12118
  printed names), 0.23s for the grid. Paid for by folding
  `test_effects_tailcall.py`'s two independent corpus walks into one shared
  module-scoped census: 0.95s -> 0.26s, assertions unchanged.

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

# M3/M4/M5 backlog, and the M6 agenda

This file exists because the SDD execution workspaces (`.superpowers/sdd/...`)
are scratch and get deleted. It started as the M2 final-review backlog for M3;
at the close of M3 it absorbed M3's own deferred findings, and at the close of
M4 it absorbed M4's, for the same reason. It is an agenda, not a plan — plans
get written with `superpowers:writing-plans` when the milestone begins.

**Reading order.** The "M4 agenda" and "M5 agenda" sections below are now
*records*: their items are marked DONE / CLOSED / SWEPT with the task that
closed them, and the entries kept verbatim underneath contain retracted claims
that must not be re-derived. **What is still open is the "M6 agenda" section at
the very end of this file.** Start there.

**File name.** It is still `m3-backlog.md` because three milestones of
cross-references point at that path; renaming it would break more than it would
clarify.

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

Status at the end of M5 (all figures measured 2026-08-13, at the task-12 tree
or, where the final fix and residual rounds moved them, after those):
229/229 still compile; **867 tests pass in 42.1–44.1s** on macOS 15.2 /
Apple M4 (arm64) against a 45s ceiling — **test ordering is UNMEASURED**: no
randomiser is installed, so neither M5 claim about it varied the order at all;
see M6 agenda item 6; the ledger
holds the same 1478 unique hashes over 1944 occurrences, of which **1430 unique
(96.8%) / 1896 occurrences (97.5%)** are `L3`, against M5 exit floors of
**0.94 unique** and 0.96 occurrences, plus 0.85 structured reach and 0.96 quality
(`tests/test_m5_exit.py`). **216 files ship fully structured source, 6 ship
hybrid (structured with fallback holes), 7 still ship the whole-file M2
fallback**; per occurrence, **1747/1944 (89.9%) ship structured text**. The
ported quality metric reads **0.968833** (0.935633 at M5 start); the
predecessor's 0.997 was carried to M6 as its exit by the human partner's
decision of 2026-08-12. L2 differential certification is online with a measured
reach of **one file**. Evaluated in `docs/reports/m5-quality.md`.

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
(`express/freereg.py::stack_discipline`) — statement grouping and register
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
recommended — ~~it moves only 3 rows (`GETGLOBAL`/`GETTABLE`/`SELF`)~~ **it
moves 4 rows since M5 task 1 regraded `LEN`** (`GETGLOBAL`/`GETTABLE`/`SELF`
plus `LEN`, which joined the delta because with `NO_METAMETHOD` at `READ_HEAP`
it is `TRUSTING`'s own "a table read may be reordered freely" that takes it back
to `PURE`) — and the corpus falsifies the first three. `lift/effects.py`'s
behaviour ~~is unchanged~~ **changed in exactly one row at M5 task 1**. Two rows
were found under-graded and left alone pending the full axiom-change protocol:
~~`LEN` at `NO_METAMETHOD`~~ **`LEN` was regraded `PURE` → `READ_HEAP` at
`NO_METAMETHOD` by M5 task 1 (§1 of the M5 agenda below), with a null
differential over all 1944 protos**, and `NEWTABLE`/`CLOSURE`'s GC path, which
is still open and still not recommended.

*Two corrections above, both landed at M5 task 12; the strikethroughs are kept
rather than silently rewritten, because this paragraph is cited from CLAUDE.md
as the place the M4 finding is recorded and a reader arriving from there needs
to see what moved. The third correction from the same M5 task 1 note is in
`lift/effects.py`'s own module docstring, which claimed the inlining gate
consumes this table — untrue since M3 task 8, and the paragraph two below says
so.*

The original entry follows.*

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
constants and the engineering red line forbids decoding them. (This sentence
used to justify that with "constants that are frequently not UTF-8"; CLAUDE.md
records the measurement that falsifies it — 0 non-UTF-8 out of 49063. The rule
is the reason, not the encoding.)

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
  clean run prints a clean line and returns 0
  while a converged or moved pin still returns 1. (At M4 task 10 that line was
  `225/229 identical, 4 pinned divergence(s)`; M6 task 12 converged three of
  the four pins, and the live run at the M6 final review — 2026-08-14 — prints
  `global-state: 228/229 identical, 1 pinned divergence(s)`.)
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

**1. `scripts/ratchet_diff.py OLD NEW`.** Exits 1 on seven regressions — level
downgrade, rung downgrade (a *higher* `l3_level` is a *weaker* proof), removed
row, an occurrence no longer walked while its row survives, an `L3` row
carrying a `refusal_reason`, a per-occurrence `shipped` going `structured` →
`fallback`, and a row arriving at `L0` — printing the offending rows grouped by
`refusal_reason` cluster. 0 on upgrades, added rows and fields the *baseline*
lacks. Two real diffs at the M5 task-8 commit: `eb08890` → HEAD is **41
upgraded, 0 downgraded** (L3 1389 → 1430); `bbe74f6` → HEAD is **318 upgraded,
0 downgraded** (1112 → 1430).

**Exit codes, corrected in round 1.** This entry previously said "2, never 1,
on an unreadable input (bisect reads 1 as 'bad')". That protection did not
exist: `git-bisect(1)` reads **every** code in 1..127 except 125 as bad, so 2
was a verdict too, and a mistyped predicate would have converged silently on an
innocent commit (measured on a scratch repo — `git bisect run` with an
unconditional `exit 2` announced a first bad commit). The non-verdict codes are
now **125** (this tree cannot be judged: the ledger under test is missing,
malformed, or has duplicate `shash` rows → git skips) and **128** (the
instrument is misconfigured: usage, a bad baseline, or an internal error in the
diff → git aborts). The internal-error case matters on its own: an uncaught
`KeyError` used to escape `main` and become exit 1, i.e. an instrument fault
reported as a tree verdict.

Non-vacuity is the deliverable and was treated as one. `tests/test_ratchet_diff.py`
is **43** tests (37 at this task's close; M5 task 9 added 6 more for the
`l2-lost` and `l2-coverage-downgrade` kinds — re-counted 2026-08-13),
one named case per failure mode plus the CLI contract, each
feeding a hand-mutated copy of the real committed ledger and asserting a
non-zero exit **naming the row**. The standing claim is that neutering any one
check turns at least one named case red and only cases belonging to that
check — deliberately weaker than the "exactly its own test(s)" this entry used
to assert, because the mutation pass caught something on each of the last two
rounds: round 1's exit-code tests were written against the *symbols*, so
reverting both constants to 2 left all 24 green; round 2 found that the pass
had never been run over round 1's `load_rows` guards, two of which were
unpinned and one load-bearing (deleting `isinstance(row, dict)` left the whole
664-test suite green while a scalar ledger line escaped as an `AttributeError`
and exited 1 — a tree verdict from an instrument fault, which is finding 2
reintroduced by its own fix). Both are pinned now; see
`structured-pipeline.md` → "Non-vacuity".

The `git bisect run` predicate was **verified by running a bisect**, not
described. Round 1 rewrote it: the original `run_corpus.py … || exit 125`
mapped a **compile regression** to *skip*, because `run_corpus.py` returns 1
when a file fails to compile *after* writing a ledger full of `L0` rows — so
the loudest regression class the ratchet exists for was unbisectable, and the
original verification (an injected `StructureError`, which falls back and still
compiles) never touched that path. The predicate now asks whether a ledger was
produced (`rm -f corpus/ledger.jsonl` … `test -s corpus/ledger.jsonl || exit
125`) rather than what `run_corpus.py` returned, and was re-verified against an
injected compile regression: at the injecting commit `run_corpus.py` exits 1
with `compiled 222/229` and a ledger holding **188 `L0` rows**, the old
predicate returns **125 (skip)**, and the new one bisects to that commit in
**22s / 2 probes** with 191 clustered regressions. Details and evidence:
`structured-pipeline.md` → "The `git bisect run` predicate".

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
Re-measured: **24 cases in under 3 seconds** (13 runs across this task span
2.21–2.54s) against **~0.3s** for the standing 3 — so this entry's "~1.7s" did
not reproduce, and neither the point value "2.48s" nor the range
"2.29–2.54s" survived contact with the next routine run. The fold-in costs the
ratchet ~2s and the per-commit suite nothing.

**Known limitation, recorded not fixed (round 2, N4).**
`src/pyluadec/verify/ledger.py::write_ledger` writes `corpus/ledger.jsonl` in
place, with no write-to-temp-then-rename. So a `run_corpus.py` killed
mid-write can leave a *shorter but syntactically valid* ledger, and the two
truncation shapes land on opposite sides of the verdict/non-verdict line:

- truncated at a **line** boundary → valid JSONL with rows missing →
  `ratchet_diff.py` reports `row-removed` and exits **1**, i.e. an I/O
  interruption reported as a bad commit;
- truncated **mid-line** → `json.JSONDecodeError` in `load_rows` → exits
  **125**, correctly.

The fix is a tmp+rename in `write_ledger`, which is a change to how the
committed artifact is produced and does not belong in a round whose constraint
is that the ledger stay byte-identical. Recorded here so the next person does
not rediscover it from a confusing bisect.

**CI: there is none.** Checked — no `.github/workflows/`, no `.gitlab-ci.yml`,
no runner config anywhere in the repo. No workflow was invented for a repo that
has never had one; the ratchet is `scripts/ratchet_job.sh` (suite + baseline
diff + full sweep, 37.9s end to end), run at a wrap and before any merge that
touches the ledger. If a runner is ever added, that script is the job body.

Suite after round 3: **676 passed in 35.0-35.3s** (3 runs; 636 in 36.0s before
the task, 655 at the task commit, 664 after round 1, 673 after round 2),
against the 45s ceiling; +40 tests over the whole task at no measurable time
cost, and all 37 `ratchet_diff` tests need no corpus.

## 3. The 89 non-`L3` unique protos, and the 17 files still on fallback — LARGELY CLOSED (M5 tasks 4, 5, 6); the remainder is M6 agenda 1

### Closed — M5 tasks 4/5/6 (measured 2026-08-13 at the task 12 tree)

**89 non-`L3` occurrences → 48. 17 whole-file fallbacks → 7.** Route by route:

- Task 4 closed the `build_sir` refusal leaves: refusals 31 → 13, `L3` unique
  1389 → 1403, 3 files off fallback. The residual collapsed to **one defect**:
  all 13 remaining refusals are **compound `if` conditions** (`and`/`or` with
  an else arm) needing a condition tree in `regions.If`, with a committed
  26-instruction repro at
  `tests/test_sir_longtail2.py::COMPOUND_CONDITION_EXEMPLAR`.
- Task 5 closed the mismatch/reconstruct leaves: `L3` unique 1403 → 1430, one
  more file off fallback.
- Task 6 added **hybrid emission**, which is what took the file count from 13
  to 7 without needing every leaf closed: a chunk whose root does not certify
  now ships structured text with fallback holes at the `CLOSURE` sites it
  could not certify. 6 files ship that way.

**The finding that matters for M6** is task 6's: the 7 remaining whole-file
fallbacks are blocked on their own **root** proto, which a hybrid substitution
cannot replace — and hybrid emission *unmasked* 4 roots whose faithfulness had
never been compared at all, because certification used to die on a descendant's
refusal before any comparison ran. One is adjudicated: `snr_music.lua`'s main
collapses four distinct nested table constructors into **one aliased table**,
i.e. `classify_registers` treating a temp as a local. Certification catches it,
so nothing wrong ships. **The residual in the 7 is RECONSTRUCTION, not
unrecognised control flow.** Carried to M6 agenda 1.

The two `tests/test_semantic_regressions.py` cases this item said would go
stale on purpose both did: `test_counter_closure_and_dispatch_mix` now
certifies `L3` (closed by task 5, and its assertion was *strengthened* to pin
both the level and the absence of `__pld_pc`), and
`test_if_and_elseif_conjunctions_preserved` did not flip — it is one of the 13
compound-`if` refusals, i.e. exactly the one defect above.

*Original entry follows.*

## 3 (original). The 89 non-`L3` unique protos, and the 17 files still on fallback

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

## 6. L2 differential-execution certification, and the key-sequence harness — DONE (M5 task 9)

*Everything until "Closed — M5 task 9" below is the record as it stood before
the change. One of its figures is right about the mechanism and wrong about
the count; the correction is in the Closed section, not smoothed away here.*

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

### Closed — M5 task 9

`scripts/probe_keyseq.{lua,py}`, `tests/test_l2_keyseq.py`, the `l2` ledger
field, the dashboard rows, and two new `ratchet_diff` regression kinds
(`l2-lost`, `l2-coverage-downgrade`). Full design, grammar, taint argument and
coverage caveats: `docs/runbooks/structured-pipeline.md`, "The L2 gate".

**The figure above that did not reproduce.** "The 3000-event cap truncates 132
of 229 files mid-loop … getting past that ceiling wants a key-sequence-driven
harness" is right that the cap binds on 132 files and right that key sequences
are the lever for input-blocked ones — but the two sets barely overlap.
Measured 2026-08-12, taking each capped file's most frequent recorded call
over the whole trace: **101 are `vms`-dominated** (linear story scripts
truncated by volume), **26 are `wait`-dominated** (24 of them containing
`doScriptScene`, i.e. spinning in a dispatch loop), and only **5 are
`pressButton`-dominated**. Nine files contain `pressButton` at all; five reach
the poll, and the other four (`snr_mainmenu`, `snr_novel`,
`snr_fragment_main`, `snr_story_main`) error before getting there under the
frozen stub policy — a live M6 lead rather than dead ground.

**Reach delivered: one file.** `snr_lib.lua` at L2@100% (3/3 protos entered,
block coverage in [0.39, 0.95] of 57). The other four authored files are
refused `taint-static`. In the committed ledger that is 2 rows / 3 proto
occurrences badged and 164 occurrences carrying an explicit refusal.

**The reason reach is one and not five** is the round-1 Critical: runtime
taint marking is structurally blind to `stub == "literal"`, because `lvm.c`'s
`equalobj` checks `ttype(o1) == ttype(o2)` before ever consulting `__eq`.
Twelve laundering routes were measured granted with zero marks, and the idiom
is the corpus' dominant one (`doScriptScene == "<literal>"`, **427 sites
across 23 of the 229 files** measured on the original bytecode; the
310-across-20 figure that first appeared here counts the decompiled artifact
text, a 27% smaller population). A static stub-taint analysis over the
original lifted bytecode now refuses them. It is path-insensitive, so a single
site anywhere in a file refuses the whole file — conservative on purpose.

Rounds 2, 3 and 4 each closed further holes **inside the code written to
close the previous one** — twelve laundering routes in round 0, four in round
2 (the `read - written` seed exemption, a stub table key, an accessor's return
value), eight more in round 3 (the trusted-callee list trusting `pcall` /
`assert` / `rawget`, a shadowed base name, `_G` and `getfenv()`, a closure
writing the parent's local, a stub-decided loop trip count, and a hard-coded
loop-variable window that lost taint past four variables), and six in round 4
(a stub in an allowlisted callee's arguments, harness state carried between
calls, and four more environment-substitution mechanisms). Every one was a
byte-equal trace with zero runtime marks and a grant. **Reach stayed at 1/5
through all four rounds** — every fix refused fixtures, never a corpus file. Read the
"what the pair still cannot see" list in `structured-pipeline.md` as *what
could be constructed*, not as a proof.

Round 2 closed a hole of the same class in that analysis' own seed rule: it
exempted globals the chunk writes, computed as `read - written` over the whole
chunk with no ordering, and `env.__index` resolves a global from `envfields`
only once the write has actually executed. Three fixtures granted through it,
including laundering *through* the exemption. The exemption is deleted rather
than made sound, because it was measured to buy no reach. Round 2 also made a
stub table KEY and a call's RETURN value stub-derived; the remaining gaps are
arguments, script-table round trips and `VARARG`, each a committed test.

**What is still open after this.** The two historical checkpoints from
`DEBUG_KEY_SEQUENCE_HARNESS.md` are *runnable* (their sequences are authored:
`entry=systemOption.OptionMain`, `entry=systemConfig.ConfigMain`) but
`snr_common.lua` refuses on `taint-static`, so they carry no badge; what they
ASSERT is M5 task 10 either way. Making the static analysis path-sensitive
(only refusing on sites the sequences actually reach) is the obvious lever for
reach and needs proto correspondence between original and artifact that the
fallback files do not have. The three named gaps in the analysis — call
arguments, script-table round trips, aliased launderers — are each a committed
failing-by-construction test in `tests/test_l2_keyseq.py`.

## 7. Extract `express/names.py::_stack_discipline` — DONE (M5 task 11)

*Everything until "Closed" below is the record as it stood before the
change. Three of its five figures did not reproduce; see the Closed
section.*

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

### Closed — M5 task 11 (commits `61f55af`, `b01894a`, and this one)

Split into `src/pyluadec/express/freereg.py`, exporting `stack_discipline`.
`names.py` keeps the half of the analysis that is about `for` headers (which
slots a loop header owns, over which pcs) and calls the other half through the
four callbacks that were **already** its whole interface — `_stack_discipline`
never closed over `classify_registers`' state, which is why step 1 could move
the body textually.

**Three of the five figures above did not reproduce** (re-derived 2026-08-13 at
`e1dc62c` by AST, before any edit):

| figure | this item said | measured |
| --- | --- | --- |
| `_stack_discipline` lines | 462 | **467** |
| `if`s in it | 33 | 33 ✓ |
| nested closures in it | 11 | 11 ✓ |
| `names.py` lines | 831 | **968** |
| `classify_registers` lines / closures | 278 / 4 | **410 / 11** |
| "one function is 56% of the module" | 56% | **48.2%** |

The module and `classify_registers` had both grown since 2026-08-12 (M5 task 5
put the loop-ownership windows in), which is the whole reason the fraction
moved the *opposite* way from what a growing extraction target would suggest.

After (measured the same way at the tip):

| | before | after |
| --- | --- | --- |
| `names.py` | 968 lines | **494** |
| `freereg.py` | — | **558** |
| the walk itself | 467 lines / 33 `if` / 11 closures | **308 / 22 / 7** |

A fourth figure worth recording because it reframes the item: of the walk's 467
lines, **only ~192 were code** — 121 docstring, 117 comment-only, 37 blank. The
prose is the asset here (each claim in it was individually verified in an M4
review), so "extract" had to mean *move the evidence with the code it
describes*, not compress it. Nothing was deleted except one dangling
half-sentence (below).

What changed inside, beyond the move:

- The three state-independent barriers became module-level functions
  (`_same_block(block_floor, d, r)`, `_renders_as_literal(fn, def_pc)`,
  `_bar_literal_operands(fn, li, pending)`) under a section heading matching
  `structured-pipeline.md`'s "The four barriers on top of the pop-once rule",
  so the runbook's map and the module's layout are isomorphic. The fourth
  barrier stayed put and is marked in place — see the finding below.
- The `pending` entry was a 4-element list read by magic index (`ent[3] = 1`);
  it is now a `@dataclass(slots=True)` `_Pending` (`ent.bad = True`). Crossing
  a function boundary with the raw list would have made the indices worse, not
  better.
- `push` was defined **inside** the `for pc in ordered` loop, rebuilt once per
  instruction. It now takes `pc` and is defined once.
- Deleted a dangling half-sentence comment, "`# Back-edge spans [target,
  source]. luac's loops are natural and its`", which has sat above
  `_same_block` since M4 task 13 (`783d15c`) describing nothing in the code.

**Finding: the "four barriers" pin claim was true of three of them.**
`structured-pipeline.md` said each of the four "is pinned by a fixture that
fails when it is neutered (see `tests/test_express_liverange.py`)". Neutering
each in turn (2026-08-13, before and again after the extraction, with identical
results both times):

| barrier | full-suite failing test ids with it neutered |
| --- | --- |
| 1 `_same_block` | 7: `test_express_liverange.py::…_cert_only[0]`, `test_express_testset.py::test_fixtures_certify_l3`, `test_certify_stripmode.py::test_stricter_gate_refuses_reconstructions_that_invent_a_local[return a and b or c-…]`, `test_effects_reconstructor_consistency.py::test_the_printer_arm_is_not_carried_entirely_by_arm_one`, `…::test_closures_captured_upvalue_is_covered_by_arm_one_only`, `test_hybrid_chunk.py::test_probe_reach_of_the_substituted_code`, `test_ledger_ratchet.py::…fixed_point` |
| 2 RK/literal | 7, all of them in `tests/test_express_*.py`: `test_express_liverange.py::test_genuine_locals_are_not_inlined_away[5,8,9]`, `test_express_testset.py::test_fixtures_certify_l3`, three in `test_express_reconstruct.py` |
| 3 `MOVE d, s` | 6: `test_express_liverange.py::…[13]`, `[14]`, `test_hybrid_chunk.py::test_corpus_hybrid_invariant_on_one_file`, `…::test_probe_reach_of_the_substituted_code`, `test_ledger_ratchet.py::…fixed_point`, `test_semantic_regressions.py::test_counter_closure_and_dispatch_mix` |
| 4 read-poison blame | 2, and **nothing in any `test_express_*.py`** (126/126 still pass): `test_sir_loops_longtail.py::test_repeat_fixture_claims_every_pc_and_certifies[6]`, `test_ledger_ratchet.py::…fixed_point` |

The express-scoped sets (which is what the first version of this table
reported, without saying so) are identical before and after the extraction.

### What each barrier is worth on the corpus

Measured in round 1 by neutering each alone and **regenerating the ledger**:

| barrier | corpus protos reclassified | `corpus/ledger.jsonl` |
| --- | --- | --- |
| 1 `_same_block` | 28 / 1944 | moves, 9 lines — 5 rows `L1`→`L3`, 1 `L3`→`L1` |
| 2 RK/literal | **0 / 1944** | unchanged |
| 3 `MOVE d, s` | 3 / 1944 | moves, 2 lines — 2 rows `L3`→`L1` |
| 4 read-poison blame | 3 / 1944 | moves, 2 lines — no level change |

So barrier 4 is load-bearing, and its pin is nowhere near where the runbook
sent a reader — that finding stands. **But this section's first version bolted
an unmeasured superlative onto it**: "it is in fact the only one of the four
whose absence *moves the committed ledger*". That is FALSE — three of the four
move it. The sole exception is barrier **2**, and that is the sharper result:
`_bar_literal_operands`' literal test (and, separately, its RK C-slot arm
alone) reclassifies **zero** corpus protos, so the corpus can say nothing at
all about it and its entire evidence is the seven synthetic fixtures in the
row above. It is the cleanest instance in this module of "the corpus is a
weaker oracle than it looks", and the first version put the sentence on the
wrong barrier. Corrected here, in `structured-pipeline.md`, in `CLAUDE.md`,
and in the code comment on barrier 4 — the false claim shipped in commit
`f99f307`, whose message repeats it; the message is left as written and this
is the record.

**Acceptance.** `corpus/ledger.jsonl` regenerated and byte-identical after each
of the three commits. Suite 833 passed. Timing, interleaved OLD/NEW with
`-p no:randomly` (which is a **no-op here** — no randomiser is installed; see
§6 of the M6 agenda, added in the M5 final fix round — so this was an
OLD-vs-NEW comparison in one fixed order, which is what it needed to be
anyway), three pairs: OLD 37.40 / 37.93 / 38.61s, NEW 37.82 / 37.80 /
38.42s — means 37.98 vs 38.01s, a 0.03s difference against a 1.21s spread
*within* the OLD arm, i.e. no measurable change and no regression of M5 task
2's recovery. Because the suite is dominated by `luac_sz4` subprocesses and
would hide even a large regression in this function, `classify_registers` was
also benchmarked directly over all 1944 corpus protos (best of 5, three
interleaved pairs): OLD 509.6 / 507.9 / 511.7 ms, NEW 492.6 / 477.0 / 489.9 ms
— **4.6% faster**, plausibly the per-instruction closure construction that
`push` no longer does. That benchmark also sums `len(temp_defs)` over all 1944
protos and gets **157236** on both arms, which is a behaviour-identity check
that does not route through the ledger.

**What corpus invariance does and does not prove.** A byte-identical ledger and
an identical `temp_defs` total say the 1944 corpus protos classify identically.
They say nothing about inputs the corpus lacks — and the corpus reaches 33 of
38 opcodes, so the `VARARG` and `SETLIST`-open arms of the dispatch, among
others, are exercised only by synthetic fixtures in the suite. Those fixtures
pass; that is the evidence, and it is weaker than the corpus number looks.


## 8. The ledger's `refusal_reason` drops `Mismatch.path` — DONE (M5 task 12)

### Closed — M5 task 12

`structure/structured.py::_rejected` now emits `mismatch: <field> at <path>`
when the first mismatch is not at `root`, and the bare `mismatch: <field>` when
it is. The path is safe for a checked-in file for the reason the item gives:
`verify/normalize.py::_cmp` builds it from `"root"` and subproto INDICES
(`f"{path}/{i}"`), so it carries no bytecode-derived text by construction,
unlike `Mismatch.a`/`.b`.

**What it bought, measured 2026-08-13 over all 22 `mismatch` occurrences: 20
are at `root`, 2 are not** — `snr_s1_10_s.lua:main` at `root/48` and
`snr_s3_10_s.lua:main` at `root/59`, both hybrid roots whose real defect is a
descendant's `code`. So the ledger moved exactly 2 rows;
`scripts/ratchet_diff.py` against `affd56f` reports 0 removed / 0 downgraded /
0 rung downgrades, exit 0, and the `refusal_reason` KIND is unchanged
(`cluster_of` splits at the first colon), so `test_m3_exit.py` and
`test_m4_exit.py`'s vocabulary coupling holds untouched.

**One correction to the item's own text.** Its verification example —
"`snr_lib.lua:main` has `n_insns: 5` and reports `structure: pc 73: if targets
out of range`" — does not illustrate the defect it names. That is a
`structure:` reason from `_refused`, produced when an ancestor adopts a
descendant's `StructureError`; `_rejected` and `Mismatch.path` are not
involved. The ancestor-adopts-descendant confusion is real and is a **separate**
gap that this fix does not close: a `StructureError`'s `pc` is relative to
whichever proto raised it and nothing in the string says which. Carried to M6
agenda 5.

*Original entry follows.*

## 8 (original). The ledger's `refusal_reason` drops `Mismatch.path`

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

## 9. The `compile:` refusal vocabulary is unexercised — DONE (M5 task 12)

### Closed — M5 task 12

`tests/test_structured_certify.py::test_the_compile_refusal_vocabulary_is_reachable`
drives all **three** producers by monkeypatching the printer to emit text
`luac_sz4` rejects, and asserts each reason string exactly:

* `compile: candidate chunk did not recompile` (chunk-root path),
* `compile: candidate wrapper did not recompile` (nested path),
* `compile: wrapper yielded 2 nested functions, expected 1` (nested path,
  wrapper shape) — reached with a body that closes the wrapper's own function
  early and adds a second one to the same `return` list, which is what makes
  the wrapper's *main* proto carry two children.

Two things worth keeping. Each case needs a **distinct** proto, because
`certify_proto` memoizes per `(oracle identity, is_chunk_root, _memo_key)` and
would otherwise hand case 3 case 2's verdict — the first draft did exactly
that and failed. And a patch is the *only* way in: M5 task 8 measured that a
compile fault cannot be injected into the structured emitter at all, because
the certification gate converts it into an `L1` verdict and a fallback
artifact. The counts the item quotes are re-measured 2026-08-13 on the
committed ledger: `structure` 21, `mismatch` 22, `reconstruct` 5, **`compile`
still 0** — this closes the *demonstration* gap, not the corpus one, and the
corpus one is not a defect.

*Original entry follows.*

## 9 (original). The `compile:` refusal vocabulary is unexercised

`test_m4_exit.py`'s `REASON_KINDS` commits four kinds. Measured on the
committed ledger 2026-08-12: `structure` 49, `mismatch` 35, `reconstruct` 5,
**`compile` 0**. The three producers in `structure/structured.py`
(`"compile: candidate chunk did not recompile"`, `"compile: candidate wrapper
did not recompile"`, and the `wrapper yielded N subprotos` form) are reached
by **no test and no corpus row**; the only `compile:` string any test asserts
is `run_corpus.py::_L0_REASON`, a different producer. A synthetic fixture that
makes the printer emit something `luac_sz4` rejects would close this; until
then a fourth of the committed vocabulary is asserted but not demonstrated.

## 10. Test-hygiene set — SWEPT (M5 task 12): 2 fixed, 1 closed-as-unlocatable, 3 re-deferred

### Closed — M5 task 12, item by item

The suite-time measurement pass this set was deferred for: **860 passed,
42.2–43.4s** on macOS 15.2 / Apple M4 (arm64), against a 45s ceiling. That is
**1.6s** of headroom at worst on this host (a reviewer's host measures the same
tree at 39.4–41.1s, i.e. ~4s — quote the host with the number), which is itself
now an M6 item (agenda 6) — and it is the reason the three remaining entries
were re-deferred rather than swept: each adds test code, and two of them add
test *count*.

1. **"A dead loop-invariant condition inside an unpack generator" —
   CLOSED AS UNLOCATABLE, with the measurement.** Two AST scans over all 62
   `tests/*.py` and all `scripts/*.py`: (a) every comprehension whose `if`
   condition uses no name bound by its own `for` target → **0 hits**;
   (b) every `for` inside a generator function whose nested `if`/`while` test
   uses no loop-target name → 2 hits, both false positives
   (`tests/test_effects_reconstructor_consistency.py::pcs_frame`, where the
   tested names `li` and `fx` are assigned in the loop BODY). Either it was
   fixed incidentally between M4 and now, or the description does not match
   what was found. Not re-deferred: an unlocatable item is not an item.
2. **`mismatches[0].field` assertions pinning `_cmp`'s field ordering —
   RE-DEFERRED**, and the item overstates it: there is **one** such site in the
   whole suite (`tests/test_emit_while.py:242`), not several. It is a genuine
   coupling and the repair (assert set membership over all mismatches) is two
   lines, but it would weaken the only test that pins *which* field diverges
   for that shape. Re-deferred as M6 agenda 6.
3. **A fallback assertion coupled to the `__pld_` textual preamble —
   RE-DEFERRED.** Same shape as 2 and same reason; note that M5 task 5
   deliberately *added* a `b"__pld_pc" not in out.source` assertion in
   `tests/test_semantic_regressions.py` as a strengthening, so "coupled to the
   preamble" is now sometimes the right coupling. Needs a per-site judgement,
   not a blanket sweep. M6 agenda 6.
4. **Three hand-rolled region walks → one `_CHILDREN`-driven generator —
   RE-DEFERRED.** Still correct, still worth doing, still pure test-code churn
   at a milestone wrap. M6 agenda 6.
5. **15 `CASES` driven by a plain `for` loop — FIXED.**
   `tests/test_express_testset.py::test_fixtures_certify_l3` is now
   `pytest.mark.parametrize`d, so a failure names the case rather than the
   loop. There are **17** cases, not 15 (measured 2026-08-13); the
   parametrisation makes the count self-maintaining.
6. **`Repeat.negated`'s inverted name — DECISION REAFFIRMED, unchanged.** No
   consumer reads it (the printer derives polarity from the instruction's own
   A/C field, and `Printer.condition`'s docstring says so). Renaming a field
   nothing reads is churn; the rule stands that if a consumer ever appears,
   the rename happens first.

*Original entry follows.*

## 10 (original). Test-hygiene set (carried from the M4 task 2 review, unfixed)

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

## 11. Probe minors — SWEPT (M5 task 12): 1 documented in place, 4 re-deferred as future-corpus traps

### Closed — M5 task 12

Every entry here is latent on today's corpus by the item's own admission, so
the sweep asked one question per entry: *is there a repair that does not change
the probes' wire format?* The wire format is load-bearing — `_PINNED_DIVERGENCES`
in `scripts/probe_global_state.py` and the behaviour probe's two pins are exact
strings in it — so "escape it on the Lua side" is not the cheap fix it looks
like.

- **`payload_of` mis-splits an `ERR|` message containing `|` — DOCUMENTED IN
  PLACE, not fixed.** Both candidate repairs cost more than the defect
  (escaping `|` moves the wire format under four pinned strings; splitting from
  the right is no better, since the globals block can contain `|` inside a
  serialised string value). And it is measurably dead: **this branch has no
  live caller** — both call sites in `tests/test_global_state_probe.py` reach
  `payload_of` only for results starting `OK|`. That fact is now a comment at
  the site, so the next reader does not have to re-derive it.
- **Value-side serialisation ambiguity (`X="a" Y=1` vs `X="a\nstring:Y=1"`) —
  RE-DEFERRED.** Same family as the key collision that WAS fixed, and the fix
  is the same shape (a length-prefixed or escaped encoding), which is a wire
  format change. 222/229 payloads are `string:main=<function>`. M6 agenda 4.
- **`strip_location` strips only the FIRST location prefix — RE-DEFERRED.**
  This is the one remaining way `ERR|` residue can be representation-dependent
  for a reason other than `getobjname`, and it needs a re-raised error to fire.
  M6 agenda 4.
- **Table/function-valued KEYS serialise via `tostring(k)` (an address) —
  RE-DEFERRED.** 0 occurrences today; would make the probe non-deterministic
  across its two processes the moment one appears, which is a loud failure, not
  a silent one. M6 agenda 4.
- **`pfields`/`envfields` keep the proxy and `env` raw tables permanently
  empty, so `pairs`/`next`/`rawget` on them report empty — RE-DEFERRED.** Lua
  5.1 has no `__pairs`, so this is not fixable inside the metatable design at
  all; it needs a different stub representation. Already commented at both
  sites (M4 task 12). M6 agenda 4.

*Original entry follows.*

## 11 (original). Probe minors (`scripts/probe_global_state.*`, `scripts/probe_behaviour.*`)

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

## 13. Readability items surfaced by the M4 evaluation — DONE (M5 task 7)

### Closed — M5 task 7 (output surface v2), re-measured at task 12

All four printer-level items below landed, plus `elseif` (which the M4 report
named as the highest-value one and this entry does not list). Re-measured
2026-08-13 over the **216** fully-structured files against the predecessor's
same 216: `["` **6085 → 0**, high-byte decimal escapes **991233 → 0**, `(-`
**570 → 0**, line-leading `elseif` **0 → 282** (predecessor 278), and maximum
nesting depth **61 → 8** against the predecessor's **10** — with ours deeper
than the predecessor in **0 of 216** files. Non-ASCII bytes in our output:
991233, against the predecessor's 991263.

The downstream-coupling question this entry said to decide first WAS decided,
by the human partner, and the answer is explicit versioning rather than
preservation: the `post_process/` chain had already been broken two milestones
earlier by our `l<depth>_<reg>` names, so v1's quirks are not kept. See
CLAUDE.md's 「下游耦合」 section and `structured-pipeline.md`'s "Output surface
v2" table. The bytes red line got a scoped, human-approved amendment for the
UTF-8 item, implemented in exactly one function (`emit/lua.py::_str_lit`).

Each of the five changes was verified by regenerating the whole ledger and
requiring it byte-identical — which is the operational definition of a
presentation-layer change, and which caught the one attempt that was not one
(the first `elseif` draft dropped a semantic-regression case from `L3` to
`L1`).

*Original entry follows.*

## 13 (original). Readability items surfaced by the M4 evaluation

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

## 14. Still-open minors inherited from M2 and M3 — SWEPT (M5 task 12): 2 fixed, the rest decided

### Closed — M5 task 12, item by item. None silently dropped.

**Fixed:**

- **`ingest/dispatch.py` — `_bridge_for()` outside the `try/except`.** Now
  inside its own handler, re-raising `_bridge_for`'s own message as
  `IngestError` (the message already names the cause and the repair command, so
  re-wording it would only let the two drift). `ValueError` is deliberately NOT
  caught: an unsupported width is a `BadHeader`-class fact about the input and
  `parse_header` owns rejecting it. Pinned by
  `tests/test_ingest_errors.py::test_a_stale_bridge_so_raises_ingest_error_not_bare_runtimeerror`,
  which monkeypatches `serial_sizet_width()` to lie; neuter-proved by moving
  the call back above the `try` and watching the `RuntimeError` escape
  `pytest.raises(IngestError)`.
- **`cfg/dom.py` — `_reverse_postorder`'s recursive DFS mutating the
  process-global recursion limit.** Rewritten with an explicit stack; the
  `sys.setrecursionlimit` pair is gone. Order preservation is argued
  structurally in the docstring (mark at push = mark at `dfs` entry; append on
  iterator exhaustion = append after the recursive loop) **and measured**: over
  all 1944 corpus protos the old and new implementations return identical
  lists, 0 differing, and `corpus/ledger.jsonl` is unaffected.

**Decided, not fixed, each with the reason:**

- **`cfg/blocks.py`'s proven-equivalent `leaders.add(pcs[i + 1])` mutant, and
  `Cfg.preds` sortedness being untested** — the first is proven equivalent over
  20k synthetic CFGs and all 1944 corpus protos and the entry's own text says
  it only becomes load-bearing under a refactor that has not happened; the
  second is a determinism hazard whose consumer (M3 structuring) now exists, so
  it is the one of the pair worth doing. Both to M6 agenda 6.
- **`lift/lift.py`'s successor validation not checking `s in instrs`** — not
  reachable from luac output; matters for hand-crafted or corrupted bytecode,
  which is the same population `tests/synth.py` serves. M6 agenda 6.
- **`LUA_KEYWORDS`' home / empty `__init__.py`s / the `emit` ↔ `structure`
  mutual dependency through `fallback.py`** — one open question with three
  instances, and the answer is the same for all three: it needs a shared
  codegen-side package that does not exist and that nothing yet needs badly
  enough to justify. Third instance recorded at the import site in
  `emit/lua.py` (M5 task 6). M6 agenda 6.
- **The `f"{path}_{i}"` proto-path convention at three sites** — documented at
  all three; the closing test named in the entry ("assert one file's fallback
  `__pld_F` key set equals the set of `proto_path`s the ledger records for it")
  is still the right one and is still unwritten. M6 agenda 6.
- **`verify/ledger.py`'s write-only `n_insns`** — it acquired a reader in M5:
  `docs/reports/m5-quality.md` §2's instruction-volume basis is computed from
  it, and so is `scripts/run_corpus.py`'s own reporting. It is no longer
  "forward schema nobody reads"; leaving it is now correct rather than
  tolerated.
- **`express/reconstruct.py::_emit_multi`'s overstated shadowing comment**, and
  **`tests/test_express_names.py::_temp_write_violations`' undocumented open-read
  ceiling (14369 corpus temp-writes with no explicit reader)** — both are prose
  defects of the exact kind this milestone kept producing, and both need a
  measurement pass rather than a wording pass. M6 agenda 6.
- **The three M2-era mutants no test can fail** (boxed parameters emitted
  unboxed, `UNM` as `0-(x)`, `FORLOOP`'s `step > 0` weakened to `>=`) — two of
  the three involve opcodes the corpus does not contain (`UNM`), and the third
  manifests as a **hang**. Still open, and the standing warning stands: any
  mutation testing must keep `oracle.run_bytes`'s timeout in place. M6 agenda 6.

*Original entry follows.*

## 14 (original). Still-open minors inherited from M2 and M3

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

---

# M6 agenda

**CLOSED OUT at the M6 wrap (task 13, 2026-08-14). What is still open lives in
the "M7 agenda" section at the end of this file** — this section keeps its
record, including the parts M6 did not touch, but it is no longer the place to
read for what is next. Per-item disposition, each linked to the heading below:

| # | item | disposition at the M6 wrap |
|---|---|---|
| 1 | reconstruction residual + `avg_score ≥ 0.997` | **partially closed** (tasks 11, 12): 48 non-`L3` shapes → **40**, `structure:` family 21 → 1. **The 0.997 half is WITHDRAWN, not deferred** — it stopped being a gate on 2026-08-13 (spec §2 decision log). Residual → M7 agenda 1 |
| 2 | corpus-wide L2, the four taint gaps, the truncation residue | **untouched by M6.** L2 reach is still 1 file → M7 agenda 2 |
| 3 | `next`/`pairs` iteration order | **untouched**, and it shrank with agenda 1: fallback-path occurrences 197 → **181** → M7 agenda 3 |
| 4 | probe hardening (4 re-deferred entries + the driver duplication) | **the fifth sub-item is CLOSED** — M6 task 7 extracted the shared driver into `scripts/probe_common.lua` (504 lines) instead of making a third copy, and `probe_behaviour.lua` / `probe_keyseq.lua` / `probe_enum.lua` all load it. The four wire-format entries are **untouched** → M7 agenda 4 |
| 5 | a `StructureError` does not name the proto that raised it | **untouched** (`structure/structured.py::_refused` still takes only the exception, re-checked 2026-08-14) → M7 agenda 5 |
| 6 | the engineering-debt set | **the suite-headroom entry was closed by a decision AND by work** (this cell said "not by work" until the M6 final review): M6 task 1 memoized `oracle.compile_source`, the lever the item itself named, and the 45s ceiling became a ~120s earmark for formal-verification instruments (human partner, 2026-08-13, with the 2026-08-14 tightening on what "too slow" has to be). The ordering question is **still unmeasured and still cheap to answer** — `find_spec("pytest_randomly")` is `None`, re-checked 2026-08-14. Everything else untouched → M7 agenda 6 |
| 7 | M1's Linux x86_64 verification | **still outstanding**, and still the only exit criterion in this project that has been half-satisfied since 2026-08-10 → M7 agenda 7 |

Written at the M5 wrap (task 12, 2026-08-13). Same conventions as the M4 and
M5 agendas above: **open unless the heading says otherwise**, numbered so items
can be cited, numbering is not a priority order, and **every figure quoted here
was measured at the M5 task 12 tree unless it says otherwise**. Where a figure
carried forward did not reproduce, the discrepancy is stated rather than
smoothed over.

M5's own closed items keep their record in place above (§§1–14), including the
retracted claims inside them; do not re-derive from those.

**Starting state, measured 2026-08-13.** 229/229 compile; **867 tests pass in
42.1–44.1s** on macOS 15.2 / Apple M4 (arm64), against a 45s ceiling (860 at
42.2–43.4s before the final fix round and the residual round, which added 5
and 2 tests); the
ledger holds 1478 unique shapes over 1944 occurrences, of which **1430 (96.8%)
/ 1896 (97.5%)** are `L3`; **216 files ship fully structured, 6 hybrid, 7 whole-
file fallback**; **1747/1944 (89.9%) occurrences ship structured text**; ported
quality metric **0.968833**; L2 reach **1 file**. `./scripts/ratchet_job.sh`
exits 0.

## 1. Close the reconstruction residual, and reach `avg_score ≥ 0.997` — PARTIALLY CLOSED (M6 tasks 11, 12); the `0.997` half WITHDRAWN

### Disposition at the M6 wrap (task 13, 2026-08-14)

**The `avg_score ≥ 0.997` clause is withdrawn, not carried.** It stopped being
a gate on 2026-08-13 by the human partner's decision, recorded in the spec's
§2 decision table (third row from the end). It is a dashboard observable and
measures **0.977328** at the M6 wrap, from 0.968833. Do not re-derive an M7
target from it: M6's own measurement is that this metric and defect detection
are not the same question — the fingerprint it coarsens scores `cfg_reachable`
**1.0** on `snr_common.lua:main_75`, a proto whose only loop the predecessor
had deleted.

**The residual half moved and is carried to M7 agenda 1.** Measured
2026-08-14 at the wrap: **40 non-`L3` ledger rows** (48 at M6 start), split
**29 own refusals + 11 inherited ancestors** by the leaf/ancestor join
`tests/test_m6_exit.py::coverage_gaps` performs. `L3` is **1438/1478 unique
(97.3%) / 1904/1944 occurrences (97.9%)**; **217 files ship fully structured,
8 hybrid, 4 whole-file fallback**.

**This section's two named defects are what tasks 11 and 12 worked on**, and
their outcomes are recorded inline below (the compound-`if` entry) and in
`docs/runbooks/structured-pipeline.md`'s "What is left, attributed rather than
narrated". Everything below this line is the M5-era diagnosis as written.

Everything below is the diagnosis M5 handed over; none of it is
hand-waving and each part has a committed artefact to start from.

The 48 non-`L3` unique protos / 48 non-`L3` occurrences split by
`refusal_reason` on the committed ledger: **`structure` 21, `mismatch` 22,
`reconstruct` 5, `compile` 0**. Two named defects account for most of it:

- **13 compound-`if` refusals — ONE defect. CLOSED by M6 task 11
  (2026-08-14).** `and`/`or` conditions with an else arm needed a condition
  tree in `sir/regions.py::If`; `regions.CondTest`/`CondOp` and
  `sir/build.py::_match_cond_chain` are it, and
  `tests/test_semantic_regressions.py::test_if_and_elseif_conjunctions_preserved`
  — the signal this entry named — moved `L1` -> `L3` by measurement.

  Measured outcome, stated as a partial rather than a clean sweep: the
  `structure:` family went **21 ledger shapes -> 1**, of which **7 reached
  `L3`** and **13 moved to `mismatch:`** (they print now and fail comparison,
  on a pre-existing `write_reg` `declared`-gate defect the structure refusal
  had been masking — see item 5). The survivor, `snr_common.lua:main_71`, is
  not a condition defect at all: its `break` at pc 295 targets the exit of a
  `while true` that `_match_loop` does not recognize. Corpus after:
  `L3` **1437/1478 unique, 1903/1944 occurrences**; **217 files fully
  structured, 5 hybrid, 7 whole-file fallback**; quality **0.971947**;
  `ratchet_diff.py` vs `0957364` = 7 upgrades, 0 downgrades.

  Still open, and named: `while <a and b> do` (`_match_while_header` requires
  the header to be one basic block), `while <a or b> do`, and
  `repeat ... until a or b` — **three** rows, all pinned
  by `tests/test_sir_condtree.py::WHILE_HEADER_GAP`. No corpus proto needs
  any of them.

  Two things from the task's fix round worth carrying forward. **The 13
  `mismatch:` arrivals are not one magnitude**: `snr_common.lua:main_76_2` is
  extra slots and extra `MOVE`s, while `snr_graphic.lua:main` **was**, at task
  11, `code` 385 -> 650 and *semantically wrong* output (**eight** table
  constructors aliased into one — four was a miscount; the `NEWTABLE`s into
  register 1 are at pcs 2, 19, 28, 39, 41, 43, 45, 47). Task 12 then closed
  the aliasing form: re-measured 2026-08-14, that root recompiles to `code`
  385 == 385 and `maxstacksize` 20 == 20, and the surviving mismatches are in
  its descendants (`root/2`, `root/3`, `root/4`).
  What they share, measured 13/13, is that the first opcode
  divergence lies outside every `cond_claimed(...)` set -- so they belong to
  item 5's reconstruction residual, not here. And **the predecessor
  structure-reference rate for these protos is 12/13 (92.3%)** after the fix,
  not the 6/13 measured before it; the pre-fix number was confounded by this
  very defect and should not be quoted.
- **4 root reconstruction defects that hybrid emission UNMASKED.** Their
  certification previously died on a descendant's refusal before any comparison
  ran, so their faithfulness had never been compared at all. One is
  adjudicated: `snr_music.lua`'s main collapses four distinct nested table
  constructors into **one aliased table** — `express/names.py::classify_registers`
  grading a temp as a local, the same family as `snr_common.lua`'s
  consumed-register read. Certification catches it, so nothing wrong ships;
  what it costs is the file.

**The leverage is still superlinear and still the same mechanism**: `print_chunk`
inlines the whole tree at each `CLOSURE` site, so one unstructurable inner
function forfeits its entire ancestor chain. Hybrid emission (M5 task 6)
softened that for descendants but cannot help a **root**, which is why the
remaining 7 whole-file fallbacks are exactly the 7 whose roots do not certify.

**The arithmetic to plan against** (re-derived 2026-08-13): 216 files score
exactly 1.000000, so the remaining 13 must average **≥ 0.947** for the corpus
to clear 0.997. Converting all 7 fallbacks to hybrids at the measured hybrid
quality of **0.816791** reaches only **0.9896**. So the target is not a better
assembly strategy; it is closing the two defects above so those files certify
outright.

## 2. Corpus-wide L2, and the taint analysis's four known gaps

L2's instrument is done (M5 task 9) and its two historical checkpoints are
green (task 10). What is **not** done is reach: **1 of 229 files** carries the
badge (`snr_lib.lua`, `L2@100%`, 2 ledger rows / 3 occurrences), 4 more are
refused `taint-static`, and **220 of 229 files contain no `pressButton` at
all** — for those there is no input loop to drive and no key sequence can
change that, which is a stronger statement than "not yet authored".

Two independent halves, and they should not be confused:

**(a) Authoring.** 9 files contain `pressButton` (re-derived 2026-08-13 by
scanning every proto's `GETGLOBAL` constants: 9 files, 220 without); 5 reach
the poll; **4 error before it** under the frozen stub policy (`snr_mainmenu`,
`snr_novel`, `snr_fragment_main`, `snr_story_main`). Those 4 are a live lead —
they *have* input loops. Of the 132 files that hit the behaviour probe's event
cap, the split is **101 `vms`-dominated, 26 `wait`-dominated (24 with
`doScriptScene`), 5 `pressButton`-dominated** — measured at M5 task 9 round 1
and independently reproduced by its scoped re-review over all 229 files; **not**
re-derived at task 12, which re-ran the probe only far enough to confirm its
headline. **That headline itself moved and this sentence had not been
updated** (M6 final review): task 12's own hybrid work converged
`snr_mainmenu.lua`, so the live figure is **229 files, 228 identical, 1 pinned
divergence, 398196 events** — the event total is the one thing that did not
move. The `vms`/`wait`/`pressButton` split above is still the M5 task 9
measurement and is still not re-derived.

**(b) Soundness.** The static may-analysis that gates the grant has four
documented gaps, each a committed test that GRANTS and should not, and the list
is labelled "what could be constructed", not "complete" — across four rounds,
thirty routes were found granting and every one of them was inside the previous
round's fix.

- a stub passed as a call **argument** (intra-proto: parameters are roots);
- a **script-built table** round trip (`t.x = stub` then `t.x == "a"`);
- **`VARARG`** — and note `snr_common.lua` has 26 `VARARG`s meeting 26 `select`
  calls, though M5 task 10 measured that neither checkpoint's subtree contains
  any of them;
- **harness state**, which is the different one: `waitf(n)` does
  `local m = tonumber(n)`, `nil` for a proxy, so the frame counter itself
  becomes stub-decided. **A register-level may-analysis is structurally blind
  to this** — it is the first limit found here that is not a propagation gap,
  and it was closed at the *boundary* (a `blind-harness` site kind fires when a
  stub-derived value reaches a `_CLEAN_CALLEES` argument window) rather than in
  the analysis. Any other harness state carried between calls is the same
  shape.

`snr_lib.lua`'s grant is safe by a profile that should be re-checked if it ever
changes: 0 `SETUPVAL`, 0 captured registers, 0 `TFORLOOP`, 0 `VARARG`, 0 `_G`
reads, and it calls no base global.

**(c) Truncation, which the M5 final fix round narrowed but did not close.**
That round found a grant that could rest *entirely* on a run cut off at
`MAX_EVENTS = 3000` — nothing read the trace status, so "byte-equal" silently
meant "equal over the first 3000 events". A grant now requires at least one
sequence to reach `OK`, and `cov` is measured over those alone. What remains,
constructed by review and committed as a known-open route
(`tests/test_l2_keyseq.py::test_a_branch_only_a_capped_sequence_enters_is_
granted_on_a_truncated_prefix`):

```lua
if pressButton("CIRCLE")==true then
  for i=1,5000 do engine.Go(i) end engine.OriginalTail()
else engine.Short() end
```

with the artifact differing only in the tail call. `tail=` finishes at `OK|5`
through the `else` arm; `k=1,CIRCLE;tail=` caps at `CAP|3001` before reaching
the divergent tail. Traces agree, taint is empty, both protos are `L3` —
**granted at `cov` 1.0**. So a capped run can no longer be the only evidence
for a *file*, but it can still be the only evidence for a *branch* no
completing sequence enters.

**Not cheaply closable, which is why it is here and not in M5.** `cov` cannot
see it: **both** specs enter 2 of 2 protos, so proto granularity is blind to a
branch. Two candidate instruments, neither small — **branch-level coverage**
(the badge was deliberately moved off basic blocks in M5 task 9 because block
attribution is by source line and therefore moves when the printer moves a
newline, which would make `cov` a presentation-layer value and break the
ledger's byte-stability rule — so this needs a line-free seam), or a
**post-cap divergence check** (continue both runs past the cap comparing a
digest rather than a full trace).

**Do not "fix" it by requiring every sequence to complete.** Measured twice:
`snr_lib.lua` under `tail=CIRCLE` reports `CAP|3000001` with the cap raised
1000×, i.e. the degenerate sequences do not halt at any budget, and every one
of the five authored files carries at least one (completions are 2/3, 2/3,
2/3, 1/2, 1/2). That rule fixes L2 reach at 0 permanently.

**The live grant is not resting on this**, measured rather than argued:
`snr_lib.lua`'s capped `tail=CIRCLE` re-run at 10× budget with every decimal
token normalised out yields **15 distinct event shapes at 3000 events and the
same 15 at 30000, none new** — the post-cap tail is pure repetition of the
menu's redraw/poll cycle. That is a property of that one sequence, measured
once; **the gate does not check it**, and any new sequence needs its own
measurement.

A related loose end: **truncation never reaches `corpus/ledger.jsonl`**. The
completed/total count lives only in `L2Result.detail`, which is CLI-facing;
the granted row is `{"cov": 1.0}`. Adding a key rewrites every driven row, so
it was left alone on a branch whose ledger is byte-frozen.

## 3. The `next`/`pairs` iteration-order gap (carried from M2 backlog item 5)

Unchanged and still the only place with **corpus-level runtime evidence** of a
real semantic gap rather than a theoretical one: `snr_novel.lua`'s single
`pairs` loop iterates a table the original builds with `NEWTABLE 1 0 23`
followed by 29 `SETTABLE`s, where the fallback emits a bare `{}` and luac gives
it `NEWTABLE ... 0 0` — different node array, different `next()` order, the
same multiset of 43 trace lines in a different order.

Scope carefully, because it is smaller than it was: presize fidelity is
guaranteed *indirectly* for anything that certifies `L3` (`NEWTABLE`'s `B`/`C`
are part of `code`), so the gap is confined to protos still on the fallback
path — which was **197 of 1944 occurrences** when this was written and is
**181** at the M6 wrap (re-measured 2026-08-14: 1944 − 1763 shipped
structured), and `snr_novel.lua` is one of the **4** remaining whole-file
fallbacks (7 when this was written). This item therefore shrinks as agenda 1
progresses and may vanish with it. Full text at "5. Table internal layout" in the M5 agenda above.

## 4. Probe hardening (the four re-deferred entries from M5 agenda 11)

All four are correctness traps for a *future* corpus or a future probe user,
all currently latent, and all blocked on the same thing: **the probes' wire
format is load-bearing** (four exact pinned divergence strings in
`scripts/probe_global_state.py`, two more in the behaviour probe), so the
obvious repairs are format changes that would move the pins. Doing them
together, with the pins re-derived once, is cheaper than doing them one at a
time. Full text and the per-entry reasoning are in §11 above:
value-side serialisation ambiguity; `strip_location` stripping only the first
location prefix; table/function-valued keys serialising to an unstable address;
and `pfields`/`envfields` making `pairs`/`next`/`rawget` on a stub report empty
(not fixable inside the metatable design at all — Lua 5.1 has no `__pairs`).

A fifth, from M5 task 9's own closing concern: `scripts/probe_keyseq.lua`
duplicates ~250 lines of `scripts/probe_behaviour.lua`. Deliberate, and pinned
by a drift test — but a **fourth** probe should extract the engine rather than
copy it a third time.

> **CLOSED — M6 task 7 (2026-08-14).** The fourth probe (`probe_enum.lua`) did
> not copy it. The shared driver moved into `scripts/probe_common.lua` (504
> lines at the wrap) and all three of `probe_behaviour.lua`,
> `probe_keyseq.lua` and `probe_enum.lua` load it. One consequence worth
> knowing, recorded in the task-7 report: the "no Lua patterns in the probe"
> rule had been asserted per probe against each probe's own file, so the ~460
> driver lines that moved were briefly covered by nothing;
> `test_no_lua_patterns_in_the_probe` is now parametrised over both files.
> **The four wire-format entries above are untouched** and carry to M7.

## 5. A `StructureError` does not say which proto raised it

Found while closing M5 agenda 8. `structure/structured.py::_refused` builds
`structure: <StructureError message>`, and the message's `pc` is relative to
**whichever proto in the subtree raised it** — an ancestor adopts a
descendant's refusal verbatim. `snr_lib.lua:main` has `n_insns: 5` and reports
`structure: pc 73: if targets out of range`. M5 task 6 hit the same thing from
the other side and had to retract an argument that read a descendant's pc as
the ancestor's own.

Agenda 8's fix does **not** cover this: it added `Mismatch.path` to the
`mismatch:` kind, and this is the `structure:`/`reconstruct:` kind, which has
no `Mismatch` to take a path from. The fix is to thread the refusing proto's
own path through `_refused` the way `_rejected` now threads `Mismatch.path` —
a proto path is index-derived and carries no corpus payload, so the red line is
not in the way. Small, and it makes `refusal_reason` usable for clustering the
residual in agenda 1.

## 6. Engineering debt, swept and re-deferred at M5 task 12

Each of these was individually decided at the M5 wrap rather than left silent;
the per-item reasoning is in §§10, 11 and 14 above. Grouped here because they
share one property — none changes behaviour, and several add test code to a
suite whose headroom is **host-dependent and, on the tightest host measured,
1.6 seconds**.

- **Suite headroom is the first of them.** 867 tests. Measured 2026-08-13 on
  macOS 15.2 / Apple M4 (arm64), five runs: **42.1–44.1s**, i.e. **0.9s** under
  the 45s ceiling at worst. The spread is this laptop's documented
  within-session upward drift, not the 7 tests M5's last two rounds added --
  those cost **0.16s** together, measured with `--durations`. A second host
  measures the same tree at 39.4-41.1s. **Quote the host and the position in
  the session with the number.** A reviewer's host measures the same tree at **39.4–41.1s
  over 10 runs**, i.e. ~4s. Quote the host with the number.

  **Test ordering is UNMEASURED — neither M5 claim about it was a measurement
  of ordering.** M5 task 11 reported 37.2–37.6s "fixed" against 39.5–40.4s
  "random" and that split propagated into `CLAUDE.md`, the `CHANGELOG` and
  this file; task 12 round 1 re-measured interleaved (5 pairs: 42.28 / 42.25 /
  42.26 / 42.99 / 43.39 against 42.57 / 42.69 / 42.97 / 43.09 / 42.78) and
  wrote "ordering is not a factor". **Neither arm ever varied the order.**
  Measured 2026-08-13: no randomiser is installed — `pytest --trace-config`
  registers exactly one third-party plugin (`pytest-timeout 2.4.0`) and
  `find_spec("pytest_randomly")` is `None` — so `-p no:randomly` deselects a
  plugin that does not exist and pytest accepts it as a **silent no-op**
  (`uv run pytest -p no:randomly --co -q` → 867 collected, exit 0). Both arms
  of every one of those A/Bs, including the reviewer's 10 on a second host,
  ran the same collection order.

  What survives is the variance, not the comparison: **1–2s of run-to-run
  spread**, which is why a single-run comparison across sessions has
  repeatedly "shown" an effect that nothing here could have produced.
  Answering the ordering question at all requires installing
  `pytest-randomly`; that is the M6 item, and it should be decided on whether
  order-independence is worth a dependency, not on these numbers.

  M5 task 2 recovered ~11.9s with a process-level certification
  memo and the milestone spent all of it. The two biggest single costs are
  `tests/test_behaviour_probe.py`'s corpus fixture (11.3s, and it is the *first
  payer* — the saving is a transfer, not a disappearance) and, new at task 12,
  `tests/test_m5_exit.py::test_m5_exit_quality_no_regression` (2.4s, 229
  `luac_sz4` runs). Raising the ceiling is not the answer. The concrete lever,
  and it is a real one: **`oracle.compile_source` has no cache and every call
  is a subprocess**, while `tests/test_corpus_compile.py` calls it on the
  *identical* 229 sources this new test does — memoizing it collapses one of
  the two passes outright. Failing that, split the corpus-wide arms behind a
  marker.
- Three hand-rolled region walks that should be one `_CHILDREN`-driven
  generator (§10).
- The one `mismatches[0].field` assertion that pins `_cmp`'s field *ordering*,
  and the fallback assertions coupled to the `__pld_` preamble — both need a
  per-site judgement, and M5 task 5 deliberately *added* one of the latter as a
  strengthening (§10).
- `Cfg.preds` sortedness untested, now that M3 structuring iterates
  predecessors; `cfg/blocks.py`'s proven-equivalent `leaders.add` mutant;
  `lift/lift.py`'s successor validation not checking `s in instrs` (§14).
- `LUA_KEYWORDS`' home, the empty `structure/`/`verify/` `__init__.py`s, the
  `emit` ↔ `structure` mutual dependency through `fallback.py`, and the
  `f"{path}_{i}"` proto-path convention at three sites — **one open question
  with four instances**: there is no shared codegen-side home, and nothing has
  needed one badly enough yet. The test that would close the last of them is
  named in §14 (§14).
- `express/reconstruct.py::_emit_multi`'s overstated shadowing comment and
  `tests/test_express_names.py::_temp_write_violations`' undocumented open-read
  ceiling (14369 corpus temp-writes with no explicit reader) — both are prose
  defects needing a measurement pass (§14).
- The three M2-era mutants no test can fail. Two involve `UNM`, which the
  corpus does not contain; the third manifests as a **hang**, so any mutation
  testing must keep `oracle.run_bytes`'s timeout in place (§14).
- Two pre-existing printer defects recorded but not fixed at M5 task 7, both
  verified at `923b41b`: a table constructor **mixing array and hash items**
  certifies `L1` because array items are emitted first (a real fidelity gap,
  and it is inside the `mismatch: code` cluster agenda 1 has to clear); and
  `_SIMPLE_PREC == _PREC["^"]` parenthesises any constant left of `^` (measured
  **unreachable** — 0 `^` in corpus output — so this one is cosmetic and may
  stay recorded forever).
- `verify/ledger.py::write_ledger` writes in place with no tmp+rename, so a
  kill that truncates at a **line** boundary leaves valid JSONL with rows
  missing, and `scripts/ratchet_diff.py` then returns 1 ("bad commit") from an
  I/O interruption. Mid-**line** truncation correctly yields 125. Recorded at
  M5 task 8 and deliberately not fixed there.

## 7. M1's Linux x86_64 verification is still outstanding

Not an M5 item and not an M6 item in the ordinary sense — it is an **M1 exit
criterion that has been half-satisfied since 2026-08-10**. `docs/runbooks/64bit-migration.md`
requires *both* 64-bit platforms green, not either; only macOS arm64 has been
proven (`ALL MIGRATION GATES PASSED on arm64 / Darwin`). Nothing since has
touched the ingest layer's width dispatch, so there is no reason to expect a
failure — which is exactly why it keeps not getting run.

M5 produced one concrete piece of evidence that this is not purely ceremonial:
`scripts/ratchet_job.sh`'s `mktemp -t` is **BSD-only** (GNU coreutils needs ≥3
trailing `X`s), so under `set -e` the job would die at that line on Linux, the
project's primary documented environment. That was found by reading upstream
`coreutils/src/mktemp.c`, **not by running it**, because no Linux host was
available — and it was fixed unverified. Both facts belong to whoever runs the
Linux gate first.

---

# M7 agenda

Written at the M6 wrap (task 13, 2026-08-14). Same conventions as the M4, M5
and M6 agendas above: **open unless the heading says otherwise**, numbered so
items can be cited, numbering is **not** a priority order, and **every figure
here was measured at the M6 wrap tree unless it says otherwise** — re-derive
before relying on any of them, and if one does not reproduce the measurement
wins and the discrepancy gets written down.

**Starting state, measured 2026-08-14.** `L3` **1438/1478 unique (97.3%) /
1904/1944 occurrences (97.9%)**; **217 files ship fully structured, 8 hybrid,
4 whole-file fallback**; **1763/1944 (90.7%)** occurrences ship structured
text; ported quality metric **0.977328** (an observable, not a gate — spec §2
decision table); L2 reach **1 file**. Suite **1077 tests**, 55.07-55.61s over three runs on
macOS 15.2 / Apple M4 (arm64) against the ~120s earmark.
`./scripts/ratchet_job.sh` exits 0 against baseline `0957364`
(**8 upgraded, 0 downgraded**).

Items 1–7 are the M6 agenda's items renumbered 1:1 with their M6 disposition
folded in (see the table at the head of that section); items 8–11 are new, and
8 and 9 exist because the 2026-08-14 plan amendments explicitly routed work
here rather than dropping it.

## 1. The reconstruction residual: 40 rows, five mechanisms, three open

Carried from M6 agenda 1, whose `avg_score ≥ 0.997` half is **withdrawn** and
must not be re-derived as an M7 target.

**The accounting, measured 2026-08-14, because two different denominators are
in circulation and both are right.** 40 non-`L3` ledger rows = **29 own
refusals + 11 inherited ancestors** (an ancestor adopts a descendant's refusal
verbatim; the join is `tests/test_m6_exit.py::coverage_gaps`). Attributed so
far: **9 rows** — 6 by M6 task 12's `_same_block` neuter experiment (5 own +
`snr_story_main:main`, which is inherited) and 3 by the clamp / conditional-
value shape (all own). **Unattributed: 21 own + 10 inherited = 31 rows.** A
document quoting "21" is counting own refusals; one quoting "31" is counting
rows. Say which.

`Reconstructor.write_reg`'s `reg not in self.declared` gate is the amplifier
behind all of it, and M6 task 12 measured it to be **at least five
mechanisms**: A constructor field stores (**closed**), B per-definition
closure capture (**closed**), C `_same_block` (**open**, 6 rows), D the clamp /
conditional-value shape (**open**, 3 rows — two arms of one conditional value
joining before a common consumer, which needs a statement-level conditional-
assignment region; `regions.CondValue` covers only the `TESTSET` `and`/`or`
idiom and there is no `TESTSET` here), E the `hazard`-set consequence of A
(**open**). Full diagnosis with the exemplars:
`docs/runbooks/structured-pipeline.md`, "What is left, attributed rather than
narrated".

One survivor is not in this family at all: `snr_common.lua:main_71`
(`structure: pc 286: else-join out of range`) is the last `structure:` row and
is a **loop** recognizer gap — its `break` at pc 295 targets the exit of a
`while true` that `_match_loop` does not recognize. **Three** more recognizer
gaps have no corpus consumer and are pinned synthetically by
`tests/test_sir_condtree.py::WHILE_HEADER_GAP`, which holds three rows:
`while <a and b> do` (the header must currently be one basic block),
`while <a or b> do`, and `repeat ... until a or b`. (`repeat ... until a and b`
is NOT in the gap and certifies — pinned separately, as a split rather than
smoothed over.)

## 2. Corpus-wide L2, the four taint gaps, and the truncation residue

**Untouched by M6.** The full text is M6 agenda 2 above and it is unamended:
reach is still **1 of 229 files**, 4 more refuse `taint-static`, **220 of 229
contain no `pressButton` at all** (a structural ceiling, not a backlog), the
static may-analysis has four documented granting gaps each committed as a
test, and the truncation residue is a committed known-open route
(`tests/test_l2_keyseq.py::test_a_branch_only_a_capped_sequence_enters_is_
granted_on_a_truncated_prefix`).

One thing M6 adds to it, and it cuts the other way: the two historical
key-sequence checkpoints live in `snr_common.lua`, and M6 confirmed **two real
defects in that file's predecessor text** (`main_76_2`, `main_75`) that the L2
harness's own stubs make invisible — `scripts/probe_keyseq.py` stubs the very
gates that select those arms, so its five authored sequences produce
byte-identical traces on original, predecessor **and** repaired text
(measured by the out-of-plan repair tasks; the claim is committed in
`tests/test_cross_corpus.py`'s module docstring, which is where to re-derive
it from). Raising
L2 reach and making L2 able to see this class are not the same project.

## 3. The `next`/`pairs` iteration-order gap

**Untouched**, and smaller than it was: presize fidelity is guaranteed
indirectly for anything that certifies `L3`, so the gap is confined to the
fallback path, which is **181 of 1944 occurrences** at the M6 wrap (197 at the
M5 wrap). Full text at M6 agenda 3.

## 4. Probe hardening — four wire-format entries

The fifth entry (a fourth probe copying the driver a third time) is **closed**
by M6 task 7's extraction into `scripts/probe_common.lua`. The four remaining
are unchanged and still share one blocker — the probes' wire format is
load-bearing, so the obvious repairs move pinned divergence strings. Full text
at M6 agenda 4 / M5 agenda 11.

## 5. A `StructureError` does not say which proto raised it

**Untouched**, re-checked 2026-08-14: `structure/structured.py::_refused`
still takes only the exception, so an ancestor adopts a descendant's message
with the descendant's pc. That is exactly the confusion item 1's accounting
had to work around by hand. Full text at M6 agenda 5.

## 6. Engineering debt

The suite-headroom entry was closed **both** by a decision and by work.
The decision: 45s → a ~120s earmark for formal-verification instruments, with
the 2026-08-14 tightening on what a "too slow" claim must contain. The work:
**M6 task 1 (`feba7c2`) memoized `oracle.compile_source`** — the exact lever
M6 agenda 6 named ("`oracle.compile_source` has no cache and every call is a
subprocess … memoizing it collapses one of the two passes outright"). This
paragraph said "resolved by a decision rather than by work" until the M6 final
review, which is half the story. The rest of M6 agenda 6's list is untouched,
plus three M6 additions:

- **The ordering question is still unmeasured and still cheap.**
  `find_spec("pytest_randomly")` is `None` (re-checked 2026-08-14), so every
  A/B this project has ever run compared two identical collection orders.
  Decide it on whether order-independence is worth a dependency.
- **`task-N-report.md` citations in tracked source (M6 final review, item 17,
  routed here).** `.superpowers/` is gitignored, so a claim whose only evidence
  is a task report is not reproducible from a clone. `src/pyluadec/oracle.py`'s
  two were fixed in that round (both measurements inlined with the command that
  produces them). **About 15 more remain**, in `express/reconstruct.py`,
  `emit/lua.py`, `structure/structured.py` and eight test modules — grep
  `task-.*-report\.md` outside `docs/superpowers/`. Each needs its own
  judgement (inline the measurement, re-derive it, or delete the claim), which
  is why it is an agenda item and not a line edit.
- **`corpus/pred_repairs/*.lua` are mode 644 where upstream is 755** (M6 final
  review, first-pass minor list). Deliberately left: in this repository they
  are committed data with a stated provenance, consumed by nothing, and run as
  `./build/lua_sz4 <file>`; the upstream bit is an artifact of the
  predecessor's environment and the README claims no mode parity. Recorded so
  the decision is visible rather than silently ignored.
- **`corpus/observation/classes.json`'s two consumer traps**, documented at
  the M6 wrap but not fixed, because fixing either moves a committed artifact:
  (a) `loop_polls_per_iteration` means "a poll site lies **somewhere** in a
  natural loop's body, directly or through an in-loop call to a poll-reaching
  callee" — under a dominance test (a poll site whose block dominates every
  latch of that loop) it is **116 of the 125** records that carry the flag,
  measured 2026-08-14, the nine exceptions being `snr_common:main_71`,
  `snr_common:main_75`, `snr_e1_10_s:main_29`, `snr_e2_10_f:main_35`,
  `snr_e2_10_s:main_13`, `snr_graphic:main_4`, `snr_mainmenu:main_7`,
  `snr_s4_10_fb:main_16` and `snr_s6_10_s:main_19`; (b) `mechanical.footprint`
  is a **7-key projection** of `footprints.json`'s 23 per-proto fields, and
  the two omitted honesty counters are the ones a consumer most needs —
  **142 of the 156 candidates have `unattributed_calls > 0` (908 in total)**
  and 127 have `unattributed_reads > 0` (1171), none of it visible in
  `classes.json`. Both fixes are field renames/additions, i.e. a regeneration,
  which is why they are here and not in M6.
- **`tests/conftest.py::pred_compiled` has no consumer** as of the M6 wrap
  (grep: one definition, zero uses). M6 task 13 removed its `strip` default
  rather than leave a trap; if M7 gives it consumers, keep the parameter
  required.

## 7. M1's Linux x86_64 verification

**Still outstanding**, unchanged since 2026-08-10 and still the only exit
criterion in this project that has been half-satisfied for a whole phase:
`docs/runbooks/64bit-migration.md` requires *both* 64-bit platforms green and
only macOS arm64 has been proven. M5's `mktemp -t` finding (BSD-only spelling,
fixed unverified) is the standing evidence that this is not ceremonial. Full
text at M6 agenda 7.

## 8. The Class-1 instrument's corpus-wide run

**Routed here by the 2026-08-14 plan amendment**, not dropped. `probe_enum` is
built, fault-injection-proven and pinned over the **13 compound-`if` leaves**;
what the amendment cut was the corpus-wide Class-1 run. Three things it needs
first, all measured:

- **Size it with `probe_enum.channels_of`, never with `classes.json`'s
  `input_space`.** The published figure collapses every string constant to
  `"str"`; corpus-wide the within-budget count is **1936 of 1944, not 1940**,
  and for `choice-branch` candidates it is **106 of 113, not 110** (re-derived
  2026-08-14 at the wrap tree). The candidate totals moved with the population
  and the corpus-wide ones did not: task 7 measured 162 candidates, 159 coarse
  → 155 fine; the wrap measures **156 candidates, 153 coarse → 149 fine**,
  because tasks 11 and 12 closed leaf refusals in between. Worst ratios: `snr_s7_10_f:main_53` 4 → 118 (29.5×),
  `snr_s2_10_s:main_60` 240 → 5280, `snr_s3_10_s:main_59` 3456 → 72576,
  `snr_s4_10_s:main_58` 1152 → 23616.
- **The predecessor-recompiled arm does not exist.** `probe_enum._payload`
  accepts `original` and `decompiled` only; the third side was dropped with
  the corpus-wide run (report §5.9). If M7 wants Track 1 driving, that arm is
  new work, and §3/§4's static adjudication is the yardstick it has to beat.
- **Two protos are never reached** (`snr_fragment_main:main_1`,
  `snr_story_main:main_1`): the chunk publishes them under no name the
  discovery walk finds.

## 9. The Class-2 (UI poll loop) instrument

**Design note delivered** (`docs/reports/m6-uiloop-design.md`), **prototype
routed here** by the same amendment. Read the note's own labelling of which
assumptions are measured and which are not before building anything. The two
measurements that matter most: the loop-body cut correspondence is **18 of
19** hand-cut protos, the sole failure being `snr_music:main_3` — which is
sole failure *because the predecessor's poll loop is missing altogether*,
i.e. the instrument's hardest case is a real defect; and the class overlap
(item 6's `loop_polls_per_iteration`, with the dominance refinement) means a
Class-2 instrument is not serving a disjoint population from Class 1.

## 10. What the cross-corpus adjudication left open

- **Four `snr_common.lua` paths were never walked end to end** (`main_55`,
  `main_28`, `main_76_7`, `main_77_24`). The loss sweeps walked **every site
  they flag** on all four, which bounds them for the swept fields only —
  global reads, global writes, call targets, call shapes, return arity, loop
  headers, reachable back edges and per-opcode test counts. That is a bound,
  not an end-to-end walk.
- **Two premises bytecode cannot settle**, both load-bearing for the twelve
  `equivalent-transform` verdicts: no side-effecting `__index`/`__newindex` on
  `_G` or on engine-owned tables, and `pairs()` order-insensitivity in the
  engine's own callees. Supporting but not conclusive: the eight metatable
  identifiers occur in **0 of 229** predecessor sources and, as a substring of
  any string constant, **0 of 229** original bytecode files — the metatables
  that would matter are installed by the PSP engine's C side, which neither
  corpus can see.
- **`corpus/pred_repairs/` repaired six defects and reconciled nothing else.**
  Its README lists what was deliberately left: the duplicated loop tail in
  `main_76_2` and the three-poll fall-through it causes, the `cursor row == 6`
  arm, and byte fidelity anywhere (two of the four instruction counts moved
  closer to the original, two moved further — the repairs buy behaviour, not
  bytes). Handing these upstream to the localization project is not a task in
  this repository, and nothing here reads that directory.

## 11. The provocations that have never been started

`M6+ 实验` in spec §7 — GPU proposer, `lparser`/`lcode` instrumented rule
mining, Lua 5.2 ingest — **none was started in M6**, and the pass-registry
decision (spec §2) named the GPU proposer as the plugin surface's only real
customer. If one of these starts, the registry question re-opens *with an
actual interface to design against*, which was the whole point of retiring it
rather than building it speculatively.

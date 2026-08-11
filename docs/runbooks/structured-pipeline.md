# Structured pipeline runbook (M3)

This is the operational and conceptual guide to the **structured** decompile
path: dominator-driven region identification, expression reconstruction, the
pure structural printer, and the per-proto `L3` certification gate that decides
whether any of it is allowed to ship.

It is the companion to `docs/runbooks/decompile-pipeline.md`, which documents
the M2 **fallback** path. The two coexist and neither replaces the other — see
"Relationship to the fallback runbook" at the end.

Every quantitative claim below was measured in this repository against the
229-file corpus (originally at commit `fb85f2f`; the capability-boundary
figures re-verified 2026-08-11 on the M3 merge candidate), or is cited to a
specific `file:line` / test name. If a number here stops matching reality,
that is a bug in the runbook; re-measure and fix it rather than routing
around it.

**How to re-derive — read this before trusting a number here.** Three tiers:

1. **Inlined and verified.** The capability-boundary table, its refusal
   breakdown, and the 58-residual histogram have complete runnable scripts
   under "Current capability boundary", each printed together with the output
   it produced when run on 2026-08-11.
2. **Read off a committed artifact or a standing test.** The L3 rates come
   from `corpus/ledger.jsonl` (`uv run python scripts/ledger_dashboard.py`).
   The 225/229 global-state figure comes from
   `tests/test_global_state_probe.py` / `scripts/probe_global_state.py`. The
   effects–emitter counts (207214/214192, 7284) live in
   `tests/test_effects_emitter_consistency.py`'s `corpus_scan` fixture, but
   the test asserts only floors — to see the exact numbers you have to print
   the fixture's `checked` / `protos` yourself.
3. **No saved command — you will have to write a script.** The fault-injection
   counts, the +17.3 / +63.6 / +0.0 percentage-point attributions, and the
   93/229 and 13.1% chunk-level figures were one-off measurements, several of
   them taken against intermediate code states that no longer exist. They are
   recorded as history, not as reproducible data. Do not assume a snippet
   exists for them somewhere; there is none.

## The pipeline, layer by layer

```
ingest -> lift -> cfg -> sir.build -> express.reconstruct -> emit.lua
                                   -> verify.certify (L3)
                                   -> structure.structured (ship structured OR fallback)
                                   -> pipeline -> ledger
```

`ingest`, `lift` and `cfg` are unchanged from M2 and are documented in
`decompile-pipeline.md`. Everything from `sir` onward is M3.

### `pyluadec.sir` — CFG + dominators to a region tree

- `sir/regions.py` (85 lines) — the frozen region node types:
  `Straight`, `Seq`, `If`, `NumericFor`, `GenericFor`, `Break`, `Return`,
  `Fallback`, and `all_claimed(region) -> frozenset[int]`, which folds a
  region tree into the set of pcs it claims and raises `RegionOverlap` if two
  siblings claim the same pc.
- `sir/build.py` (311 lines) — `build_sir(fn: LirFunction) -> Region`.
  Also exports `has_back_edge(fn)` as a cheap pre-check and `StructureError`
  as the refusal signal.

The design rule is stated at the top of `build.py` and is the thing to hold on
to: **recognize or raise `StructureError` — never emit a guessed structure.**
There is no "best effort" branch anywhere in this module.

Dominators are genuinely consumed, not built and ignored (the predecessor
project built a CFG and then wrote `_ = cfg`). `build_sir` computes
`immediate_dominators(cfg)` at `sir/build.py:79` and every branch/loop body
range goes through `_verify_single_entry` (`sir/build.py:43-68`), which refuses
unless every CFG block starting inside the claimed pc range is dominated by the
block containing the condition. The pc-interval arithmetic alone cannot see a
jump from unrelated code into the middle of a "then" body; the dominator check
can. Call sites: `sir/build.py:224`, `:226` (if/else arms), `:287` (numeric-for
body), `:306` (generic-for body).

**But do not read that as "dominance drives the structuring."** The recognizer
is pc-interval-driven; the dominator tree is a **post-hoc verifier** sitting on
top of it, and on today's corpus it is nearly inert. Measured 2026-08-11 over
all 1944 protos: `_verify_single_entry` is reached 1115 times; its
`dominates()` rejection branch — the multi-entry-branch case — fires **0**
times, and its "block unreachable from entry" branch fires 9 times but changes
the accept/refuse verdict for only **1** proto (`snr_common.lua:main_29_0`),
because the other 8 are refused for an unrelated reason anyway. Neutering
`_verify_single_entry` entirely therefore moves **1 of 1944** proto outcomes
(1775 accepted → 1776).

That is not an argument for deleting it. Both branches are covered by tests
(`tests/test_sir_build_acyclic.py`'s hand-built multi-entry CFG), the guard is
correct, and "never fires" here is a property of *this* corpus and of the
currently narrow recognizer: every region shape M3 accepts is one whose
single-entry property the interval arithmetic happens to get right. M4's
`while`/`repeat`/irreducible work is exactly where multi-entry bodies start to
be constructible, and that is when this check stops being free insurance and
starts being load-bearing. Keep it; just do not cite it as evidence that
dominators are doing the recognition.

**PC-claim audit.** `build_sir` asserts `all_claimed(region) == set(fn.instrs)`
at every exit (`sir/build.py:86-89`) and raises `StructureError` naming the
unclaimed pcs otherwise. A region tree that silently drops instructions is the
classic decompiler failure; this makes it impossible to return one. Corpus-wide
coverage: `tests/test_sir_build_acyclic.py::test_acyclic_corpus_claims_every_pc`
and `tests/test_sir_build_loops.py::test_for_corpus_claims_every_pc`.

`_structure_range` also refuses to loop forever: any recognizer path that fails
to advance `pc` raises rather than spinning (`sir/build.py:113-117`).

### `pyluadec.express` — LIR to statement/expression IR

- `express/expr.py` (73 lines) — the expression nodes, all frozen dataclasses:
  `ConstExpr`, `LocalExpr`, `GlobalExpr`, `UpvalExpr`, `IndexExpr`, `BinExpr`,
  `UnExpr`, `CallExpr`, `VarargExpr`, `ClosureExpr`, `TableExpr`.
- `express/names.py` (516 lines) — `classify_registers(fn) -> RegClass`
  (`locals` / `temps` / `loop_vars`) and `name_for(reg, depth) -> "l{depth}_{reg}"`.
- `express/reconstruct.py` (722 lines) — the `Reconstructor`: statement nodes
  (`LocalDecl`, `Assign`, `ExprStmt`, `ReturnStmt`) and targets (`LocalTarget`,
  `GlobalTarget`, `IndexTarget`, `UpvalTarget`), plus the API the printer
  drives: `stmts_for(instrs)`, `take_expr(reg)`, `cond_operand(x)`,
  `open_scope()` / `close_scope(snap)`.

One `Reconstructor` is shared across every region of one function, walked in
program order, because a `for` header's init/limit/step are staged as temps by
the `Straight` region immediately *before* the loop region that consumes them.
`open_scope`/`close_scope` are what keep a `local` declared in one `if` arm
from leaking into the other arm or past the `end`.

### `pyluadec.emit.lua` — region tree + expression tree to Lua text

`emit/lua.py` (561 lines). Public entry points:

- `print_chunk(proto) -> str | None` — prints a whole proto tree as a
  compilable chunk, nested closures inlined at their `CLOSURE` sites. Returns
  `None` (not a partial result) on `StructureError`/`ReconstructError`.
- `print_function(fn, region, rc, depth, upval_names) -> str`
- `_print_proto_body(proto, depth, upval_names) -> str` — lift + build_sir +
  classify + print, for one subtree.
- `print_expr(e, depth, parent_prec)` — context-free expression printing.
- `Printer` — the per-function context (proto, LIR, `RegClass`,
  `Reconstructor`, depth, upvalue names).

The discipline, stated in the module docstring: this is a **pure structural
fold**. It walks the typed trees once and emits strings on the way out. It
never reads back, re-scans, or post-processes any string it produced — no
peephole passes, no fixed-point loops, no counting `do`/`then`/`end` to find
block boundaries. `tests/test_engineering_practice.py::test_no_regex_in_analysis_or_emission_layers`
statically enforces the absence of `re` across
`src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}` (one
narrowly-scoped exception, `structure/fallback.py`'s compiled identifier
pattern, predates the rule).

Two invariants inside the printer that are easy to break and expensive to
debug:

- `_implicit_return_pc` (`emit/lua.py:458-486`) suppresses the `RETURN A 1`
  that `lparser.c`'s `close_func` unconditionally appends to every proto.
  Printing it makes the recompile emit *two*. This was worth +17.3 points of
  L3 rate on its own (see "How the L3 rate was actually won").
- `_terminates` (`emit/lua.py:489-517`) stops a `Seq` after an unconditional
  `return`/`break`, because in Lua 5.1 those are only legal as the last
  statement of a block — printing the sibling after them is a syntax error,
  not merely dead code.

### `pyluadec.verify.certify` + `pyluadec.structure.structured` — the landing gate

- `verify/certify.py` — `certify_l3(original, structured_src) -> CertResult`:
  compile the printed source with the real `luac_sz4` (`strip=True`), load the
  result back through `ingest`, and compare field-by-field against the original
  at each ladder rung in turn.
- `structure/structured.py` (230 lines) — `certify_proto(proto, *, is_chunk_root)`
  and `emit_certified_chunk(root) -> ChunkOutcome`.

## The certification gate is the only landing gate

This is the single most important property of the M3 design, so it is worth
stating precisely.

`emit_certified_chunk` (`structure/structured.py:198-251`) does exactly two
things:

1. Certifies **every** proto in the tree independently, recording a level per
   proto.
2. Chooses the shipped artifact: **iff the root certified `L3`**, the exact
   bytes certification compiled and compared (`ProtoCert.source`, produced by
   `print_chunk` inside `certify_proto`); otherwise
   `structure.fallback.emit_chunk(root)`.

So the invariant is:

> the shipped source is structured **⟺** the root proto certified `L3`,
> i.e. the structured print of the whole tree recompiled through the real
> `luac_sz4` into a proto that matches the original under the normalization
> ladder. No unverified structured code is ever returned.

`structured.py:249` asserts `certs["main"].source is not None` after the root
certifies, because a root that certified `L3` must by construction have printed
successfully. Note that the shipped bytes are *reused from* the certification,
not re-printed: an earlier revision called `print_chunk(root)` a second time
here, which made "shipped == certified" contingent on `print_chunk` being
deterministic (it is — 92/92 shipped artifacts re-print identically — but that
is a property of the printer, not of this gate, and no test would have noticed
losing it).

The consequence worth internalising: **a bug in region identification, in
register classification, or in inlining can only lower the L3 rate. It cannot
produce wrong output.** Whatever the recognizer gets wrong either raises
`StructureError`/`ReconstructError` (no print, fall back) or prints something
that recompiles to a different proto (certification fails, fall back). The
failure mode "plausible-looking Lua that means something else" — the
predecessor project's defining hazard — is closed off by construction, not by
review.

Pinned by `tests/test_structured_certify.py::test_printable_but_uncertified_chunk_falls_back_to_semantic_state_machine`
and `tests/test_pipeline_structured.py::test_uncertified_source_is_never_shipped`.

### Per-proto, not per-chunk

Certification is per proto subtree, so one unstructurable function cannot
poison its siblings' *levels*. The level (a proof record, per proto) and the
artifact (a conservative file-level choice, per chunk) are deliberately
decoupled — `pipeline.decompile_chunk` returns both.

A nested proto is certified in wrapper isolation (`certify_proto`,
`is_chunk_root=False`): its body is printed at `depth=1` with synthetic upvalue
names `u0..u{n-1}`, wrapped in

```lua
local u0, u1, ...
return function(l1_0, l1_1, ...)
<body>
end
```

and only `recompiled.subprotos[0]` is compared. The parameter names must match
what `name_for(reg, 1)` synthesizes — the same `l{depth}_{reg}` convention.

Certification results are memoized on `_memo_key = (structural_hash,
_debug_fingerprint)`. `structural_hash` alone is *not* sufficient: it is a
code-shape key that deliberately omits `source`, `linedefined`,
`lastlinedefined`, `lineinfo`, `locvars` and upvalue names, all of which
`compare_protos` checks. The two together cover every field the comparison
examines, so equal keys imply equal verdicts by construction
(`structure/structured.py:89-135`).

## The normalization ladder

`verify/normalize.py`. `LADDER_VERSION = "l3-ladder-v1"`.

| rung | name | what it neutralises |
| --- | --- | --- |
| `L3.0` | (none) | nothing — strict field-by-field equality |
| `L3.1` | `strip-lineinfo` | `source`, `linedefined`, `lastlinedefined`, `lineinfo`, `LocVar.name`, upvalue names |

`certify_l3` tries rungs in ascending order and records the first that passes as
`rung` / ledger `l3_level`. **Measured: 0 of the 1112 `L3` ledger entries
certify at rung 0; all 1112 are at rung 1.** That is not a slack ladder, it is
arithmetic: every corpus chunk carries `source = b"=?"` while a
`luac_sz4 -s` recompile produces `source = None`, and the 1715 non-main corpus
protos kept their original file's `linedefined`/`lastlinedefined`, which a
re-printed source with a different line layout cannot reproduce. Without rung 1
the L3 rate on this corpus would be exactly zero.

**The soundness argument for rung 1 lives next to the rung**, in
`_strip_lineinfo`'s own docstring (`verify/normalize.py`). It is argued from
what `compare_protos` still compares after the rung runs — `code` elementwise,
`constants` elementwise with bitwise `LuaNumber` payload equality, `nups` /
`numparams` / `is_vararg` / `maxstacksize`, `locvars` scope ranges, upvalue
count, and `subprotos` recursively — not from a hand-wave that "line info isn't
semantic". Read it there before adding rung 2; per spec §9 R3 each rung needs
its own argument, co-located, and a `LADDER_VERSION` bump.

What rung 1 does **not** prove: error-message text and `debug.getinfo` output.
`ldebug.c`'s `getobjname` consults `luaF_getlocalname`, so a local's *name* can
reach `attempt to index local 'x'`. `L3.1` says the two protos compute the same
thing, not that they emit byte-identical diagnostics.

Ladder tests: `tests/test_normalize_l31.py` (six cases, including
`test_l31_still_catches_real_difference` and
`test_l31_does_not_normalize_away_maxstacksize`).

### The candidate is always compiled `-s`, so unstripped input barely certifies

`verify/certify.py:54` and `structure/structured.py:183` (the wrapper path) both call
`oracle.compile_source(..., strip=True)`. That matches this corpus — all 229
files are `-s`-stripped (CLAUDE.md) — but it has a consequence that costs
people an afternoon if they meet it cold, because the symptom is a bare
`Mismatch(field="locvars")` and nothing in the modules used to mention it.

Rung 1 blanks locvar and upvalue *names* but **keeps** each locvar's count,
`startpc` and `endpc` (deliberately — a stronger check; see
`tests/test_normalize_l31.py::test_l31_strips_locvar_and_upvalue_names_but_keeps_counts`).
So an original that still carries debug info is compared, at every rung,
against a candidate whose `locvars` is empty. Measured 2026-08-11 with this
repo's `luac_sz4`:

| source | original compiled `-s` | original compiled without `-s` |
| --- | --- | --- |
| `x = 1` | `L3` rung 0 | `L3` rung 1 |
| `local a = 1  print(a)` | `L3` rung 0 | `L1`, field `locvars` |
| `for i = 1, 10 do print(i) end` | `L3` rung 0 | `L1`, field `locvars` |

Read off: a proto declaring **no** locals is unaffected; a proto declaring even
one can only certify if the original was stripped. Ordinary `luac` output
therefore falls back for essentially every real function — the most natural way
to point this decompiler at something that is not the target corpus. Compile
fixtures with `-s`, as `tests/test_certify.py` and
`tests/test_structured_certify.py` do (`tests/test_emit_lua.py` keeps an
unstripped `_proto` on purpose, to exercise the *printer*, and makes a separate
stripped copy when it wants to certify).

The stronger fix — matching the candidate's strip mode to the original's, which
would let rung 1 compare *real* locvar scope ranges instead of two empty tuples
— is **strictly stronger** than what the gate does today and is recorded as M4
work in `docs/runbooks/m3-backlog.md`. It is a behaviour change that can move
the committed ledger, so it was not made in the M3 merge-readiness round.

## Register classification: simulating `lparser.c`'s `freereg`

`express/names.py::_stack_discipline`. This is M3's central analytical idea and
the one worth understanding before touching anything in `express/`.

Every register is classified `local` (gets a real `local l0_7 = ...`
declaration) or `temp` (its defining expression is inlined into its single
consumer). Getting this wrong does not produce wrong code — certification
catches it — but it is what decides the L3 rate, because a `local` that luac
never allocated changes `maxstacksize` and the whole register numbering.

### What was there before, and why it was replaced

The M3-task-4 rule was `_adjacent_pure`: a register is a temp iff it has
exactly one tracked def and one tracked use, in that order, with no
`WRITE_HEAP` / `may_error` / open-region instruction in between. That is an
**effect-based inlining barrier**, and it was wrong in both directions:

- It is a *per-register-number, whole-function* question, but luac reuses each
  register slot for a fresh temporary in every statement, so a corpus register
  typically has a dozen defs and a dozen uses and the single-def rule rejected
  it outright. Everything rejected became a real `local`, needing more stack
  slots than luac used. `maxstacksize` was the single largest mismatch cluster.
- The pre-identified lever was to loosen the barrier: 584 of 614 blocked
  inlining pairs (95%) were blocked by `GETGLOBAL` being `ARBITRARY` under
  `STRICT`. Loosening it to `NO_METAMETHOD` changed **zero protos**. The reason
  is worth recording: the barrier was accidentally acting as a *statement-
  boundary detector*. In `local x = 1 print(x)`, the `GETGLOBAL print` sitting
  between `x`'s def and its use is exactly what correctly kept `x` a local.
  Re-grading `GETGLOBAL` freed genuine temps and genuine locals at the same
  rate, so the net was zero. **The effect model was never answering the
  question being asked.**

`_adjacent_pure` and the `EffectMode` knob it read no longer exist in
`express/names.py`.

### What is there now

`lparser.c`'s `statement()` ends with `fs->freereg = fs->nactvar`: at every
statement boundary the expression stack is empty and only declared locals
occupy registers. So

> a definition is a temp iff its value is consumed before the end of the
> statement that produced it, and a local iff it survives one.

That is simulable straight from the bytecode without knowing `nactvar`, because
`freereg` after any value-producing instruction is its target register plus one.
`_stack_discipline` keeps a `pending` stack of pushed-but-unconsumed values:

- a value producer targeting `a` pops every pending entry at or above `a`
  (exactly the operands it just consumed) and pushes its own results;
- a statement-ending instruction (`CALL` with `C==1`, `TAILCALL`, `RETURN`,
  `SETGLOBAL`, `SETUPVAL`, `FORPREP`, `CLOSE`, `FORLOOP`, `TFORLOOP`, or a
  write whose target is already a known local) pops its own operands and then
  **promotes everything still pending to local** — surviving a statement
  boundary is the definition of being one. (`CLOSE`/`FORLOOP`/`TFORLOOP` share
  one arm at `express/names.py:495-497`: a loop's back edge is a statement
  boundary too, and nothing may stay pending across it.)
- `SETTABLE`/`SETLIST` pop only *above* the table's own register, leaving the
  table pending (`local t = {} t.x = 1` and `local t = {x=1}` differ only in
  `NEWTABLE`'s size hints);
- conditions (`TEST`/`EQ`/`LT`/`LE`) and `JMP` only read, so `if f() then`
  correctly keeps `f()`'s result a temp while `local x = f() if x then`
  correctly promotes `x` at the boundary that follows.

A pending value must be read exactly **once** before it is popped or the
register is disqualified: zero reads would silently drop a statement, more than
one would inline — and re-evaluate — the same expression tree twice.

The verdict is aggregated per register number and any single disqualified
definition makes the whole register local, so the approximation is
one-directional: unsure ⇒ named local ⇒ always printable.

### The two `promote_all()` calls are not interchangeable

Documented at `express/names.py:427-465`; both were separately fault-injected
after a review found a comment that lumped them together and got the first one
wrong.

1. **The one at the `CALL`/`TAILCALL` statement boundary is load-bearing.** It
   protects a local whose slot is released by *scope exit* rather than by
   redefinition. In `do local a = f() g(a) end h()`, `end` drops `a` from
   `nactvar` and `GETGLOBAL h` reuses register 0, but nothing in the
   instruction stream marks the release: luac emits `CLOSE` only when the block
   captured an upvalue, so that boundary does not cover it and no other
   boundary sees it either. Without this line, `a` survives as a pop-once temp
   and gets inlined as `g(f())` — hoisting `GETGLOBAL g` in front of the call
   to `f`, an observable reordering under `STRICT`. **Measured: neutering it
   changes classification on 14 of 1944 corpus protos.** The committed ledger
   stays byte-identical only because all 14 are already `L1` for unrelated
   reasons — luck, not structure. Pinned by
   `tests/test_express_names.py::test_local_released_by_scope_exit_is_not_inlined_as_a_temp`.
2. **The one after a write to an already-known local is redundant on this
   corpus** — measured separately: **0 of 1944 protos** change classification
   when it alone is neutered, and for a structural reason: that branch runs
   `pop_ge(writes[0])` first, and a live named local sits below every pending
   temp, so the stack is already drained. It is kept because if it ever *does*
   fire it fires in the safe direction (promote to local).

### How the L3 rate was actually won

Each step measured against all 1944 protos:

| change | L3 protos | rate | delta |
| --- | --- | --- | --- |
| baseline (M3 task 7) | 3 | 0.15% | — |
| suppress luac's implicit trailing `RETURN` | 339 | 17.44% | +17.3 |
| inlining barrier under `NO_METAMETHOD` | 339 | 17.44% | **+0.0** |
| freereg simulation replaces the barrier | 1575 | 81.02% | **+63.6** |
| pre-declare parameters | 1577 | 81.12% | +0.1 |

The intermediate rows (3, 339, 339, 1575) are historical: each was measured
at the commit that landed that change during M3's development, not at this
runbook's `fb85f2f`, and are not independently re-derivable at `fb85f2f`
since the tree has moved past each intermediate state. Only the final row
(1577, 81.12%) is re-derivable here — it matches `corpus/ledger.jsonl` at
this commit (`tests/test_m3_exit.py`).

The pre-identified lever was a no-op; the fix nobody had planned was worth
+63.6 points. That is the milestone's main methodological lesson: the
hypothesis had a plausible mechanism and a 95% measurement behind it, and it
was still the wrong model of the problem.

## The effects–emitter consistency gate

`tests/test_effects_emitter_consistency.py` (M3 backlog item 2, landed in
task 10).

`lift/effects.py` and the emitters are two independent hand-transcriptions of
`vendor/lua-5.1/src/lvm.c`, and nothing else mechanically reconciles them. The
gate asserts, for every instruction, that the register indices an emitter
template must touch are a **subset** of `effects.reads | effects.writes`.

Four tests:

- corpus arm — walks all 229 files, lifts all 1944 protos. **Measured: 207214
  of 214192 instructions checked, 0 disagreements.** The other 6978 carry an
  open (`R[base..top)`) region and are skipped: 6949 `CALL`, 26 `VARARG`,
  3 `RETURN`.
- corpus opcode-reach pin — the corpus arm reaches only **32 of 38 opcodes**
  (`SELF`, `POW`, `UNM`, `NOT`, `CLOSE` never occur; all 26 `VARARG`s are
  `B == 0`, i.e. open). Pinned as a lower bound so the reach cannot silently
  shrink — `checked > 100_000` would not notice, since 81227 of the checked
  rows are `LOADK` alone.
- synthetic arm — the same invariant over an exhaustive operand grid built with
  `tests/synth.mk_instr` (7284 non-open rows), reaching **38 of 38 opcodes**.
- non-vacuity + fault injection — every opcode except `JMP`/`CLOSE` has a
  non-empty touched set, and dropping any one register from a real effects row
  makes the subset check fail.

Cost: ~0.9s, dominated by the single shared corpus walk (module-scoped fixture).

Two findings from writing it, both worth carrying:

- **The gate is containment, not equality.** The effects table is allowed to
  over-approximate and does so deliberately in at least two places
  (`lift.py` widens `CLOSURE`'s reads with the captured registers from the
  following `MOVE` pseudo-instructions; `FORLOOP`'s `may_error=True` is a
  documented conservative over-approximation).
- **`lift/effects.py` omits `writes_open` on `TAILCALL`.** This is a real gap:
  `lvm.c:630-632`, the `PCRC` (non-Lua callee) branch of `OP_TAILCALL`, leaves
  the callee's results at `R[a..top)` for the immediately following
  `RETURN A 0` to read. It does not make the gate fail — `OP_TAILCALL` always
  has `C == 0` (`lvm.c:611` asserts `GETARG_C(i) - 1 == LUA_MULTRET`), so the
  emitter side touches nothing beyond `R[a..a+b)` — but the row is
  under-approximate. Deliberately **not** fixed in task 10: per CLAUDE.md,
  changing the axiom layer needs an `lvm.c` citation *plus* a differential run,
  and adding `writes_open` would put every `TAILCALL` pc into
  `classify_registers`' `open_write_pcs`, which can move classifications and
  therefore the committed ledger. Carried to the M4 backlog.

## Common operations

### Decompile one file and see what certified

```bash
cd /Users/fotile96/pyluadec-refactor
PYLUADEC_CORPUS_DIR=<corpus> uv run python - <<'PY'
import os
from pathlib import Path
from pyluadec.ingest import load_file
from pyluadec.structure.structured import emit_certified_chunk
C = Path(os.environ["PYLUADEC_CORPUS_DIR"])
out = emit_certified_chunk(load_file(C / "snr_memory.lua"))
n3 = sum(1 for c in out.certs.values() if c.level == "L3")
print(f"{n3}/{len(out.certs)} protos L3; root={out.certs['main'].level}")
print("shipped:", "structured" if out.certs["main"].level == "L3" else "fallback")
PY
```

Observed for `snr_memory.lua`: `1/6 protos L3; root=L1` → the fallback chunk
ships, while one nested proto still records a genuine `L3` proof.

### Print the structured source for a file whose root certifies

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run python -c "
import os; from pathlib import Path
from pyluadec.ingest import load_file
from pyluadec.emit.lua import print_chunk
print(print_chunk(load_file(Path(os.environ['PYLUADEC_CORPUS_DIR'])/'snr_crd_0.lua')))"
```

92 of the 229 files have an `L3` root and therefore ship real structured source.

### Run the whole-corpus gate and regenerate the ledger

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run python scripts/run_corpus.py
```

A clean run prints `compiled 229/229` plus the structured/L3 breakdown. It
rewrites `corpus/ledger.jsonl` (committed) and `build/decompiled/*.lua` (not
committed). Never hand-edit the ledger; `tests/test_ledger_ratchet.py` requires
a fresh run to reproduce it byte for byte.

### Read the dashboard

```bash
uv run python scripts/ledger_dashboard.py            # or --markdown
```

Current output: 1478 unique protos / 1944 occurrences / 229 files,
`compile_ok 1478/1478`, `level L3 1112`, `level L1 366`, L3 share 75.2% unique
/ 81.1% occurrences, `L3 rung 1: 1112`, `ladder l3-ladder-v1`.

### Debug one function that refuses to certify

The recipe: certify it in isolation, look at the mismatch fields, then decode
the first differing instruction word on both sides.

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run python - <<'PY'
import os
from pathlib import Path
from pyluadec.ingest import load_file, load_bytes
from pyluadec import oracle
from pyluadec.emit.lua import _print_proto_body
from pyluadec.lift.opcodes import decode, luac_operand_str
from pyluadec.structure.structured import certify_proto

C = Path(os.environ["PYLUADEC_CORPUS_DIR"])
p = load_file(C / "snr_memory.lua").subprotos[0]        # the proto under test
cert = certify_proto(p, is_chunk_root=False)
print("level", cert.level, "fields", sorted({m.field for m in cert.mismatches}))

body = _print_proto_body(p, depth=1, upval_names=tuple(f"u{i}" for i in range(p.nups)))
wrapper = f"return function({', '.join(f'l1_{i}' for i in range(p.numparams))})\n{body}end\n"
mine = load_bytes(oracle.compile_source(wrapper.encode(), strip=True)).subprotos[0]
for i, (x, y) in enumerate(zip(p.code, mine.code)):
    if x != y:
        a, b = decode(x, pc=i + 1), decode(y, pc=i + 1)
        print(f"first divergence at pc {i+1}:")
        print(f"  original : {a.op.name:10s} {luac_operand_str(a)}")
        print(f"  ours     : {b.op.name:10s} {luac_operand_str(b)}")
        break
print("code len", len(p.code), "vs", len(mine.code),
      "| maxstacksize", p.maxstacksize, "vs", mine.maxstacksize)
PY
```

Observed output for that proto:

```
level L1 fields ['code']
first divergence at pc 7:
  original : FORPREP    4 30
  ours     : FORPREP    4 32
code len 39 vs 41 | maxstacksize 15 vs 15
```

Read that as: the loop body we printed is two instructions longer than the
original, so `FORPREP`'s jump offset shifted. The divergence is *downstream* of
pc 7 — a `FORPREP` offset mismatch is a symptom, not the cause. Cross-check
against the raw listing with

```bash
./build/luac_sz4 -l -l <corpus>/snr_memory.lua | less
```

and against the fallback output's `__pld_pc` state machine (see
`decompile-pipeline.md`, "Reading fallback output") when you need to know what
the original instruction stream actually did.

### Run the suite

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run pytest              # 285 tests, ~30s
PYLUADEC_CORPUS_DIR=<corpus> uv run pytest tests/test_effects_emitter_consistency.py -v
```

Without `PYLUADEC_CORPUS_DIR` the corpus-gated tests **skip**, including the M2
and M3 exit gates. `tests/conftest.py` prints a red banner in that case; heed
it (see CLAUDE.md).

## Ledger fields added in M3

`corpus/ledger.jsonl`, one row per unique `structural_hash`.

| field | meaning |
| --- | --- |
| `level` | `"L3"` (recompiled and matched under the ladder) or `"L1"` (compiles, unverified). `"L0"` means it did not even compile and must never appear. |
| `l3_level` | the ladder rung that passed, for `L3` rows; `null` otherwise. Currently always `1`. |
| `fallback` | `level != "L3"`. True means this proto's source came from the fallback state machine. |
| `confessions` | empty for `L3` rows; exactly one whole-range `fallback-state-machine` confession otherwise. |
| `ladder` | `LADDER_VERSION` at generation time (`l3-ladder-v1`). |
| `oracle` | `git log -1 -- vendor native` — the oracle build's provenance, **not** repo HEAD. See `decompile-pipeline.md` for why. |

**Ratchet discipline: levels only ever go up, confessions only ever come off.**
That is the *discipline*. Be precise about how much of it a machine checks —
re-read of the assertions, 2026-08-11:

**Asserted.** Within-row coupling between level and confession, both
directions: `tests/test_m3_exit.py::test_l3_entries_carry_a_rung_and_no_confessions`
(`L3` ⇒ non-null `l3_level`, empty `confessions`, `fallback is False`) and
`::test_non_l3_entries_confess` (non-`L3` ⇒ `fallback is True`, null
`l3_level`, exactly one whole-range `fallback-state-machine` confession). So a
level that rose without its confession coming off, or a confession dropped
without the level rising, does fail the suite. Also asserted: no `L0` and
`compile_ok` everywhere (`test_ledger_ratchet.py`, `test_m3_exit.py`), `shash`
sortedness and uniqueness, full-corpus coverage at exactly 1944 occurrences,
byte-identical regeneration from `run_corpus.py`
(`::test_ledger_is_a_reproducible_fixed_point`), and the `> 0.50` exit
fractions on both bases.

**Not asserted: cross-revision monotonicity.** Nothing in the suite compares
the ledger against any historical baseline. A ledger regenerated with *fewer*
`L3` rows and committed passes every test above, as long as the rate stays
over 50% and no `L0` appears — each row would still be internally consistent,
which is all the coupling tests look at. Full ratchet CI (baseline diff,
downgrade = fail, `git bisect` integration) is spec §5's complete form and is
an explicit **M4** item; M3 only guarantees the ledger fields can support it
(`docs/runbooks/m3-backlog.md` §7). Until then a shrinking L3 count is caught
by reading the ledger diff in review, not by the suite. `run_corpus.py:64-68`
takes the higher level when one structural hash occurs more than once.

## Current capability boundary — measured, not estimated

All figures over the 229-file corpus: 1478 unique proto shapes, 1944
occurrences.

| stage | unique | occurrences |
| --- | --- | --- |
| `build_sir` accepts the proto's own body | 1309 (88.6%) | 1775 (91.3%) |
| whole subtree prints (proto **and** every descendant) | 1170 (79.2%) | 1636 (84.2%) |
| certifies `L3` | **1112 (75.2%)** | **1577 (81.1%)** |

Three different numbers, three different causes, and the gap between each pair
is the honest M4 agenda:

1. **1478 → 1309: `build_sir` refuses 169 unique protos.** 162 of them carry a
   back edge the recognizer will not claim — `while`, `repeat`, and mixed or
   irreducible loops. (195 unique protos have a back edge at all; 33 of those
   are recognized as `for` loops.) The remaining 7 are acyclic refusals. All 16
   unique protos containing `TESTSET` — the `and`/`or` *value* idiom, which is
   deliberately not treated as an if-condition (`sir/build.py:16-19`) — are
   among the refusals.
2. **1309 → 1170: 139 more unique protos build a region tree but do not print,
   because a descendant closure does not.** `print_chunk` inlines the whole
   tree at each `CLOSURE` site, so one unstructurable inner function takes its
   entire ancestor chain with it. This is the "ancestor closure" effect; it is
   why the subtree-closed ceiling is well below the own-body one.
3. **1170 → 1112: 58 unique protos print but do not certify.** All 58 differ on
   `code`; 24 also on `maxstacksize`, 11 on `constants.len`, 11 on an
   individual constant. This is the residual approximation in the freereg
   simulation — statement grouping and register allocation that do not quite
   match luac's. (Round 1: dropped a basis-dependent "1 on `is_vararg`" entry
   here — certifying all 58 with `is_chunk_root` matched correctly to each
   proto's actual chunk-root status yields zero `is_vararg` mismatches; see
   `docs/runbooks/m3-backlog.md` §2 for the measurement.)

### Re-deriving the three rows

Rows 1 and 2, verbatim (re-run 2026-08-11, reproduces the table above):

```python
# PYLUADEC_CORPUS_DIR=... uv run python -
import os
from pathlib import Path
from pyluadec.emit.lua import _print_proto_body
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.ingest import load_file
from pyluadec.lift.lift import lift_proto
from pyluadec.pipeline import walk_proto_paths
from pyluadec.sir.build import StructureError, build_sir
from pyluadec.verify.ledger import structural_hash

uniq, occ = {}, {}
for f in sorted(Path(os.environ["PYLUADEC_CORPUS_DIR"]).glob("*.lua")):
    protos = {}
    walk_proto_paths("main", load_file(f), protos)
    for p in protos.values():
        h = structural_hash(p)
        occ[h] = occ.get(h, 0) + 1
        uniq.setdefault(h, p)

def accepts(p):
    try:
        build_sir(lift_proto(p)); return True
    except StructureError:
        return False

def prints(p):
    try:
        _print_proto_body(p, depth=1,
                          upval_names=tuple(f"u{i}" for i in range(p.nups)))
        return True
    except (StructureError, ReconstructError):
        return False

n_u, n_o = len(uniq), sum(occ.values())
for name, S in (("accepts own body", {h for h, p in uniq.items() if accepts(p)}),
                ("whole subtree prints", {h for h, p in uniq.items() if prints(p)})):
    u, o = len(S), sum(occ[h] for h in S)
    print(f"{name:24s} {u}/{n_u} ({u/n_u:.1%})  {o}/{n_o} ({o/n_o:.1%})")
```

```
accepts own body         1309/1478 (88.6%)  1775/1944 (91.3%)
whole subtree prints     1170/1478 (79.2%)  1636/1944 (84.2%)
```

Row 3 needs no script: it is the committed ledger. `uv run python
scripts/ledger_dashboard.py` prints both bases (`L3 share (unique)` and
`L3 share (occurrences)`).

The refusal breakdown in point 1 (169 / 162 / 7 / 195 / 33 / 16):

```python
# PYLUADEC_CORPUS_DIR=... uv run python -
import os
from pathlib import Path
from pyluadec.ingest import load_file
from pyluadec.lift.lift import lift_proto
from pyluadec.lift.opcodes import Op
from pyluadec.pipeline import walk_proto_paths
from pyluadec.sir.build import StructureError, build_sir, has_back_edge
from pyluadec.verify.ledger import structural_hash

uniq = {}
for f in sorted(Path(os.environ["PYLUADEC_CORPUS_DIR"]).glob("*.lua")):
    protos = {}
    walk_proto_paths("main", load_file(f), protos)
    for p in protos.values():
        uniq.setdefault(structural_hash(p), p)

refused, back, testset = set(), set(), set()
for h, p in uniq.items():
    fn = lift_proto(p)
    if has_back_edge(fn):
        back.add(h)
    if any(i.ri.op is Op.TESTSET for i in fn.instrs.values()):
        testset.add(h)
    try:
        build_sir(fn)
    except StructureError:
        refused.add(h)
print(f"unique protos                       {len(uniq)}")
print(f"build_sir refusals                  {len(refused)}")
print(f"  of which carry a back edge        {len(refused & back)}")
print(f"  acyclic refusals                  {len(refused - back)}")
print(f"protos with a back edge at all      {len(back)}")
print(f"  back edge but accepted (for loop) {len(back - refused)}")
print(f"protos containing TESTSET           {len(testset)}")
print(f"  of which are refused              {len(testset & refused)}")
```

```
unique protos                       1478
build_sir refusals                  169
  of which carry a back edge        162
  acyclic refusals                  7
protos with a back edge at all      195
  back edge but accepted (for loop) 33
protos containing TESTSET           16
  of which are refused              16
```

The 58-residual mismatch histogram in point 3. Prepend the `uniq` /
`is_root` construction below to the `prints` helper from the first script;
this is the only one that spends `luac_sz4` subprocesses (58 of them):

```python
# PYLUADEC_CORPUS_DIR=... uv run python -
import json, os
from collections import Counter
from pathlib import Path
from pyluadec.pipeline import walk_proto_paths
from pyluadec.ingest import load_file
from pyluadec.structure.structured import certify_proto
from pyluadec.verify.ledger import structural_hash
# ... plus the `prints` helper and its imports from the first script ...

LEDGER = Path("corpus/ledger.jsonl")
l3 = {json.loads(l)["shash"] for l in LEDGER.read_text().splitlines()
      if l.strip() and json.loads(l)["level"] == "L3"}

uniq, is_root = {}, {}
for f in sorted(Path(os.environ["PYLUADEC_CORPUS_DIR"]).glob("*.lua")):
    protos = {}
    walk_proto_paths("main", load_file(f), protos)
    for path, p in protos.items():
        h = structural_hash(p)
        uniq.setdefault(h, p)
        is_root[h] = is_root.get(h, False) or (path == "main")

resid = [h for h, p in uniq.items() if prints(p) and h not in l3]
print(f"print but do not certify: {len(resid)}")
hist = Counter()
for h in resid:
    c = certify_proto(uniq[h], is_chunk_root=is_root[h])
    assert c.level == "L1", h
    hist.update({"const[i]" if m.field.startswith("const[") else m.field
                 for m in c.mismatches})
for field, n in hist.most_common():
    print(f"  {field:16s} {n}")
```

```
print but do not certify: 58
  code             58
  maxstacksize     24
  const[i]         11
  constants.len    11
```

Note `is_chunk_root` is matched to each proto's *actual* chunk-root status
(true iff it occurs at `proto_path == "main"` in some file). Getting that
wrong is what produced the spurious "1 on `is_vararg`" entry an earlier
revision reported here.

### On the "~80.3%" ceiling

A planning-stage estimate of a "~80.3% subtree-closure ceiling" circulated
through this milestone and was quoted in `structure/structured.py`'s module
docstring and in the planning doc
(`docs/superpowers/plans/2026-08-10-phase3-m3-structured-backbone.md:69,72,1886,2221,2472`).
**It reproduces on neither basis.** The measured printability ceiling — the
real one, since only a proto that prints can certify — is 1170/1478 = 79.16%
unique and 1636/1944 = 84.16% occurrences; and the achieved occurrence rate,
1577/1944 = 81.12%, already exceeds 80.3%, which a ceiling cannot allow.
`structure/structured.py` now carries the measured figures. The planning doc
is a historical record and keeps its original text, with a correction note at
the top. `tests/test_m3_exit.py` never quoted the figure — its only thresholds
are the `> 0.50` exit-gate assertions at `:22` and `:40`.

The other standing limit is the **global-state probe** (L1.5), which reaches
225/229 files with the 4 pinned divergences documented in
`docs/runbooks/m3-backlog.md`. It is a genuine rung between "compiles" and
"differentially equivalent", but read its reach table before treating it as
strong evidence: for 222 of 229 files the entire compared payload is
`string:main=<function>`.

## Relationship to the fallback runbook

`docs/runbooks/decompile-pipeline.md` documents the M2 fallback path and stays
authoritative for it. The fallback is **not** deprecated and is not going away:
it is the floor. Every file whose root does not certify still ships fallback
source, and today that is 137 of 229 files.

Practical division of labour:

- Anything about `ingest` / `lift` / `cfg` / effect modes / `__pld_R`,
  `__pld_U`, `__pld_pc`, `__pld_top`, `__pld_F` / the ledger's non-M3 fields /
  known M2 semantic gaps → `decompile-pipeline.md`.
- Anything about `sir` / `express` / `emit` / certification / the normalization
  ladder / the L3 rate → this file.
- The M4 agenda, the global-state probe, and the deferred minors → 
  `docs/runbooks/m3-backlog.md`.

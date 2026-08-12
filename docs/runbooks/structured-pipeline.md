# Structured pipeline runbook (M3–M4)

This is the operational and conceptual guide to the **structured** decompile
path: dominator-driven region identification, expression reconstruction, the
pure structural printer, and the per-proto `L3` certification gate that decides
whether any of it is allowed to ship.

Written for M3 and extended through M4 (loop recognition, the `and`/`or` value
idiom, per-definition register classification, strip-mode matching, the effect
lattice). **This file is the authority for the capability boundary and for the
effect lattice.** Open work lives in `docs/runbooks/m3-backlog.md`'s "M5
agenda"; the readability comparison against the predecessor's shipped output
is `docs/reports/m4-readability.md`.

It is the companion to `docs/runbooks/decompile-pipeline.md`, which documents
the M2 **fallback** path. The two coexist and neither replaces the other — see
"Relationship to the fallback runbook" at the end.

Every quantitative claim below was measured in this repository against the
229-file corpus (originally at commit `fb85f2f`; the capability-boundary
figures re-measured through M4 and last verified 2026-08-12 at `3ae72c6`), or
is cited to a specific symbol / test name. If a number here stops matching
reality, that is a bug in the runbook; re-measure and fix it rather than
routing around it.

**Cite symbols, not line numbers.** Line citations in this project have a
measured failure rate: one sweep checked 19 of them and found **9 stale**, and
a later round introduced 6 more through its own docstring growth. Prefer
`module.py::symbol`. The `file:line` citations that remain here have each been
verified against the tree; convert any you touch.

**How to re-derive — read this before trusting a number here.** Three tiers:

1. **Inlined and verified.** The capability-boundary table, its refusal
   breakdown, and the print-but-do-not-certify histogram have complete
   runnable scripts under "Current capability boundary", each printed together
   with the output it produced when run on 2026-08-11.
2. **Read off a committed artifact or a standing test.** The L3 rates come
   from `corpus/ledger.jsonl` (`uv run python scripts/ledger_dashboard.py`).
   The 225/229 global-state figure comes from
   `tests/test_global_state_probe.py` / `scripts/probe_global_state.py`. The
   effects–emitter counts (214192/214192, 6981 open rows, 7448 grid rows) live in
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

(The per-module line counts below are `wc -l`, re-measured 2026-08-12 at the
M4 close. They are a sense of scale, not a citation — nothing depends on
them, and they will drift; re-run `wc -l` rather than trusting them.)

### `pyluadec.sir` — CFG + dominators to a region tree

- `sir/regions.py` (309 lines) — the frozen region node types:
  `Straight`, `Seq`, `If`, `NumericFor`, `GenericFor`, `Break`, `Return`,
  the M4 loop nodes `WhileTrue` / `While` / `Repeat` / `EndIter`,
  the M4 task-4 `CondValue` (plus its internal `VAlt` / `VTail` chain nodes and
  `value_claimed`), and `all_claimed(region) -> frozenset[int]`, which folds a
  region tree into the set of pcs it claims and raises `RegionOverlap` if two
  siblings claim the same pc.
- `sir/build.py` (1156 lines) — `build_sir(fn: LirFunction) -> Region`.
  Also exports `has_back_edge(fn)` as a cheap pre-check and `StructureError`
  as the refusal signal.

The design rule is stated at the top of `build.py` and is the thing to hold on
to: **recognize or raise `StructureError` — never emit a guessed structure.**
There is no "best effort" branch anywhere in this module.

Dominators are genuinely consumed, not built and ignored (the predecessor
project built a CFG and then wrote `_ = cfg`). `build_sir` computes
`immediate_dominators(cfg)` at `sir/build.py:119` and every branch/loop body
range goes through `_verify_single_entry` (`sir/build.py:68-108`), which refuses
unless every CFG block starting inside the claimed pc range is dominated by the
block containing the condition. The pc-interval arithmetic alone cannot see a
jump from unrelated code into the middle of a "then" body; the dominator check
can. Call sites: `_structure_if` (both branches), `_structure_numeric_for`
(body), `_structure_generic_for` (body), `_match_while` (`while <cond>` body),
`_match_repeat` (`repeat` body), `_match_while_true` (`while true` body), and
`_match_cond_value` (the M4 task-4 `CondValue` range).

The `_match_cond_value` call site is NOT covered by the M3-era inertness
measurement two paragraphs below (that one predates M4 task 3 and was never
re-derived for it). It has its own, separate proof: fix round 1 of task 4 found it pinned by
nothing (neutering it, together with `_match_cond_value`'s other guard below,
left 128/128 tests green and the corpus census unchanged) and added
`tests/test_express_testset.py::test_reachable_jump_into_the_middle_of_a_cond_value_chain_raises`,
which routes a self-consistent instruction stream through the real
`build_sir` with a hand-built, deliberately-impossible-for-luac CFG (the same
technique task 3's own fix round established for the analogous `_match_while`
guards) and shows: guard present -> refuses; guard neutered -> `build_sir`
wrongly succeeds, with the `CondValue` claiming a pc reachable via a path
that bypasses the chain's own anchor entirely. Load-bearing, with evidence,
not merely asserted.

`_match_cond_value` also carries a second check with no call-site entry above
because it isn't a `_verify_single_entry` call: an inline
`claimed != {p for p in fn.instrs if lo <= p < join}` equality inside
`_match_cond_value`, after `_parse_value` returns. Fix round 1 also found
this one pinned by nothing, but the two turned out to differ in kind on
investigation: `_parse_value`'s own recursive descent and
`sir/regions.py::value_claimed` are built from the same contiguous sub-ranges by
construction, so `_parse_value` succeeding provably implies the equality
holds -- no adversarial bytecode can separate them today. The check only has
teeth against a FUTURE bug that edits one of the two without the other; fault
injection (`tests/test_express_testset.py::test_cond_value_claim_check_is_unreachable_from_real_parse_value_but_the_pc_claim_audit_still_catches_a_broken_value_claimed`)
confirms even that case doesn't ship silently wrong output -- `build_sir`'s
own top-level pc-claim audit (`sir/build.py:126-129`) independently catches
it, just with a less specific message. Kept for the clearer, local diagnosis,
not because removing it would let anything wrong through.

Since M4, dominance is no longer only a post-hoc verifier: the three loop
recognizers **define a back edge by dominance, not by pc order** (a rotated
generic-for re-enters its body with a pc-retreating JMP whose target does not
dominate it), so `dominates` is load-bearing in `_match_while` /
`_match_repeat` / `_match_while_true` before any interval arithmetic runs.

**Do not read the acyclic part as "dominance drives the structuring."** For
`Straight`/`Seq`/`If`/`for` the recognizer is pc-interval-driven and the
dominator tree is a **post-hoc verifier** sitting on top of it. (The loop
recognizers added in M4 are the exception noted above -- there, dominance is
what defines a back edge in the first place.) The figures below are an M3-era
measurement of the verifier's inertness, taken BEFORE M4 task 3 changed which
shapes reach it; they have not been re-derived since and should be treated as
history rather than as a current claim. Measured 2026-08-11 over all 1944
protos, at commit 2a759a8: `_verify_single_entry` is reached 1115 times; its
`dominates()` rejection branch — the multi-entry-branch case — fires **0**
times, and its "block unreachable from entry" branch fires 8 times but changes
the accept/refuse verdict for only **1** proto (`snr_common.lua:main_29_0`),
because the other 7 are refused for an unrelated reason anyway. Neutering
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

#### The four loop recognizers (M4)

`_structure_range_impl` tries them in a fixed order at every dispatch
position, plus once more inside the straight-run accumulator (a loop header
can be an ordinary fall-through instruction, so nothing else would stop the
run at it). Each returns `(region, next pc)` or `None` — **never** raises: a
shape one cannot prove is simply not its loop, and the caller goes on to the
next and ultimately refuses.

| order | recognizer | closing edge | claims |
| --- | --- | --- | --- |
| 1 | `_match_while` | `JMP -> lo`, condition at the TOP | header instrs + cond + exit-JMP + closing JMP |
| 2 | `_match_while_true` | `JMP -> lo`, no condition | the closing JMP only |
| 3 | `_match_repeat` | `JMP -> lo` gated by a compare at `S-1` | cond + closing JMP |
| — | `_match_generic_for` / FORPREP | `TFORLOOP`+`JMP` / `FORLOOP` | the header instructions |

Three facts about that table are load-bearing and were each measured rather
than assumed:

- **`_match_while` goes first on purpose.** `while <cond>` can also be read as
  `while true do ... if c then <body> else break end ... end`, which is
  semantically identical and recompiles to *three* instructions where the
  original has two — it can never certify. Recognizing the real shape first is
  what keeps the desugaring from being what ships.
- **`_match_while`/`_match_repeat` try exactly ONE candidate closing JMP: the
  last one targeting `lo` in range.** Every jump back to `lo` is by definition
  inside `lo`'s loop, so the closing JMP — the loop's lexically last
  instruction — is the last of them. Trying candidates last-first the way
  `_match_while_true` does made `while true do if f() then g() else h() end
  end` match as a `While` that amputated the else block. (`while true` loops
  genuinely CAN share a header, which is why that one keeps the search.)
- **`_match_while`/`_match_repeat` refuse any body containing an `EndIter` of
  their own**, which is stricter than `_match_while_true`'s tail-position
  rule. An `EndIter` prints as nothing and always recompiles one JMP short
  (M4 task 2 measured 9 of 9 such shapes at L1), so accepting one here would
  preempt a reading that can certify. `_match_while_true` runs last and
  preempts nothing, so it keeps the weaker rule.

#### `_match_cond_value` — the `and`/`or` VALUE idiom (M4 task 4)

Tried at every dispatch position **before** `_structure_if`, and returns
`None` rather than raising, like the loop recognizers. It claims a whole
short-circuit value chain as one `CondValue` region whose target register
receives one assignment.

What luac emits (`lvm.c:577-585`, `lcode.c:condjump`/`patchtestreg`/`exp2reg`;
the no-frills VM-instruction PDF §TESTSET agrees and CLAUDE.md makes it
authoritative): `TESTSET A B C` followed by a `JMP` keeps `R[B]` (`R[A] :=
R[B]`) and takes that JMP when `bool(R[B]) == C`, otherwise falls through past
it. `C == 1` is `or` (`luaK_goiffalse` → `jumponcond(e, 1)`), `C == 0` is
`and`. Every alternative in one chain is patched to the same destination
register and the same join by `patchlistaux`.

**Erratum in that PDF, p. 37** (found and confirmed 2026-08-11 while
implementing this recognizer): its own pseudocode (`TESTSET A B C   if (R(B)
<=> C) then R(A) := R(B) else PC++`), its own `and`/`or` operator-mapping
line ("The `and` operator uses a C of 0 (false) while `or` uses a C value of
1 (true)"), and its own worked example (`local a,b,c; c = a and b` →
`testset 2 0 0` / `jmp -> [4]` / `move 2 1`, where a TRUTHY `a` falls through
to evaluate `b` and a FALSY one takes the jump with `c := a`) all agree with
`lvm.c` and with each other. Its PROSE sentence four lines below the
pseudocode does not: "If R(B) matches C, the next instruction is skipped,
otherwise R(B) is assigned to R(A) and the VM continues with the next
instruction" inverts the mapping on both halves (matching C should assign
and jump, not skip; not matching should fall through, not assign). Discard
that one sentence; trust the pseudocode, the operator-mapping line, the
worked example, and `lvm.c`'s `OP_TESTSET`, all four of which already agree
without it. Recorded here (CLAUDE.md cites this file for the PDF's authority)
so a reader who follows the PDF citation to p. 37 and reads the prose first
does not re-derive this.

The chain is parsed **right-nested**, which is the semantics rather than a
formatting preference: a taken TESTSET short-circuits the entire remainder.
Measured against `luac_sz4` — `b or c and d` (two ungated TESTSETs, C=1 then
C=0) and `(b or c) and d` are visibly different bytecode.

Two `patchtestreg` rewrites are handled explicitly, and one is deliberately
declined:

- **the gate.** `luaK_patchtohere` patches a pending jump list with `NO_REG`,
  which retargets it at the *next alternative* instead of the join. That is
  `(<gate> and X) or Y`, the only shape in this corpus. `_parse_value`
  requires the gate's target to equal `test_pc + 2` exactly — recognition, not
  a heuristic. The mirror shape `(<gate> or X) and Y` (gated alternative with
  `C == 0`) is refused: this project has not derived its source form.
- **the bare-`TEST` variant.** When the destination register IS the tested
  one, `patchtestreg` rewrites the TESTSET to `TEST B 0 C`. Accepted only once
  the chain is *committed* by a real TESTSET or a gate, because an
  uncommitted one is genuinely ambiguous: `x = x or 1` and
  `if not x then x = 1 end` compile to the same bytecode, and M3's `if`
  reading is the incumbent (the same tie-break `_match_repeat` documents).

**THE guard**, `Reconstructor._refuse_statements`: an alternative's operand
code must reconstruct to an *expression*. If it reconstructs to a statement,
printing only the and/or expression would drop that statement silently and the
pc-claim audit would not notice — the pcs are claimed either way. (The audit
proves nothing was left unclaimed, never that everything claimed was printed.)
Re-measured 2026-08-12: it fires on **1** corpus proto, because
`classify_registers` calls that staging register a local. The ledger shows the
same one row (`reconstruct: pc N: and/or alternative reconstructs to N
statement(s) ...`); an earlier "6" here predates M4 task 13. See "Current
capability boundary".

Threading (`luaK_jump`'s `jpc` concatenation, `vendor/lua-5.1/src/lcode.c`) is
the mechanism behind most of the special cases in this module: a jump still
pending when luac emits another JMP is concatenated onto that JMP's list and
patched wherever it ends up, so a nested loop's false-exit surfaces as a jump
to the ENCLOSING loop's header. `continue_target` is what lets
`_structure_if` and `_match_while_header` rewrite such a jump back to the end
of the range it actually belongs to. The same mechanism one level up — an
`if`'s false-exit threaded onto an enclosing `if`'s else-skip — is **not**
handled, and is the entire `if targets out of range` refusal cluster
(re-measured 2026-08-12: **10** unique protos, which is the figure "Current
capability boundary" point 1 and its verbatim script also give; 15 was the
pre-task-4 value).

**PC-claim audit.** `build_sir` asserts `all_claimed(region) == set(fn.instrs)`
at every exit (`sir/build.py:126-129`) and raises `StructureError` naming the
unclaimed pcs otherwise. A region tree that silently drops instructions is the
classic decompiler failure; this makes it impossible to return one. Corpus-wide
coverage: `tests/test_sir_build_acyclic.py::test_acyclic_corpus_claims_every_pc`
and `tests/test_sir_build_loops.py::test_for_corpus_claims_every_pc`.

`_structure_range` also refuses to loop forever: any recognizer path that fails
to advance `pc` raises rather than spinning (the `_last_pc` progress check
inside `_structure_range_impl`).

### `pyluadec.express` — LIR to statement/expression IR

- `express/expr.py` (73 lines) — the expression nodes, all frozen dataclasses:
  `ConstExpr`, `LocalExpr`, `GlobalExpr`, `UpvalExpr`, `IndexExpr`, `BinExpr`,
  `UnExpr`, `CallExpr`, `VarargExpr`, `ClosureExpr`, `TableExpr`.
- `express/names.py` (836 lines) — `classify_registers(fn) -> RegClass`
  (`locals` / `temps` / `loop_vars`) and `name_for(reg, depth) -> "l{depth}_{reg}"`.
- `express/reconstruct.py` (1143 lines) — the `Reconstructor`: statement nodes
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

`emit/lua.py` (707 lines). Public entry points:

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

- `_implicit_return_pc` suppresses the `RETURN A 1`
  that `lparser.c`'s `close_func` unconditionally appends to every proto.
  Printing it makes the recompile emit *two*. This was worth +17.3 points of
  L3 rate on its own (see "How the L3 rate was actually won").
- `_terminates` stops a `Seq` after an unconditional
  `return`/`break`, because in Lua 5.1 those are only legal as the last
  statement of a block — printing the sibling after them is a syntax error,
  not merely dead code.

### `pyluadec.verify.certify` + `pyluadec.structure.structured` — the landing gate

- `verify/certify.py` — `certify_l3(original, structured_src) -> CertResult`:
  compile the printed source with the real `luac_sz4` (stripped iff the
  original is — `carries_debug`; see "The candidate's strip mode follows the
  original's"), load the result back through `ingest`, and compare
  field-by-field against the original at each ladder rung in turn.
- `structure/structured.py` — `certify_proto(proto, *, is_chunk_root)`
  and `emit_certified_chunk(root) -> ChunkOutcome`.

## The certification gate is the only landing gate

This is the single most important property of the M3 design, so it is worth
stating precisely.

`structure/structured.py::emit_certified_chunk` does exactly two
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

`emit_certified_chunk` raises if `certs["main"].source is None` after the root
certifies, because a root that certified `L3` must by construction have printed
successfully. Note that the shipped bytes are *reused from* the certification,
not re-printed: an earlier revision called `print_chunk(root)` a second time
here, which made "shipped == certified" contingent on `print_chunk` being
deterministic (it is — re-measured 2026-08-12, **212/212** shipped artifacts
re-print identically; it was 92/92 at M3 close, before the loop work — but that
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

Certification results are memoized on `_oracle_identity() + (is_chunk_root,) +
_memo_key`, where `_memo_key = (structural_hash, _debug_fingerprint)`, in a
module-level dict that lives for the whole **process** (M5 task 2; it was
per-chunk, inside `emit_certified_chunk`, through M4).

`structural_hash` alone is *not* sufficient: it is a code-shape key that
deliberately omits `source`, `linedefined`, `lastlinedefined`, `lineinfo`,
`locvars` and upvalue names, all of which `compare_protos` checks. The two
together cover every field the comparison examines, so equal keys imply equal
verdicts by construction (`structure/structured.py::_debug_fingerprint`, over
`verify/certify.py::debug_view`). Measured over the corpus 2026-08-12: 16 of
the 1478 `structural_hash` groups carry more than one debug fingerprint, so
this is a live hazard rather than a theoretical one.

The other two key components exist because the scope is now process-wide:

- `is_chunk_root` selects a different procedure (whole-chunk compile vs.
  wrapper) and a different verdict shape (only the root form carries
  `source`). Within one chunk it could be omitted, because a proto cannot
  equal a strict descendant of itself; across chunks nothing constrains the
  two callers.
- `_oracle_identity()` — the `luac_sz4` binary's own `(path, mtime_ns, size)`,
  re-`stat`ed **on every lookup**. A `luac_sz4` rebuilt underneath a live
  process must not be certified against by proxy from the previous build's
  verdicts, and a byte-identical ledger would not catch that: the stale
  verdicts would be internally consistent and simply describe the wrong
  compiler. Two channels move that binary mid-process and this catches both —
  a rebuild in place, and a `PYLUADEC_BUILD_DIR` swap (`oracle.build_dir()`
  re-reads the variable per compile). The M5 task 2 original used
  `oracle_version()` (`git log -1 --format=%H -- vendor native`) memoized once
  per process, for symmetry with the ledger's `oracle` field; its round-1
  review demonstrated that serving a stale `L3` against a swapped compiler,
  because a once-per-process value cannot partition anything a real rebuild
  does. The git hash is not kept alongside — it is strictly weaker (a commit
  under `vendor/` without a rebuild leaves the same compiler in place, where
  the cached verdicts are still correct). Cost: two `stat`s per lookup,
  17.8 µs, i.e. ~45 ms on a warm 229-file pass that otherwise takes 0.62 s and
  nothing measurable on the suite.

All three components are pinned by neuter-proved tests in
`tests/test_structured_certify.py` (`test_process_cache_*`); the oracle
component has one test per channel. What the cache
buys is almost entirely *cross-pass*: intra-pass redundancy over the corpus is
only 20 of 1944 certifications (1.0%; there are 1924 distinct keys, not 1478),
but a second full corpus pass in one process costs 0.65s against ~9s cold.
`clear_certification_cache()` releases it — a full pass holds 4.08 MB of chunk
`source` bytes — and is itself pinned by
`test_clear_certification_cache_drops_every_entry`.

Because that dict now outlives the chunk, it is shared state between TESTS as
well: a fault-injection test that monkeypatches the printer or the
reconstructor and then certifies writes a wrong verdict under an ordinary key,
and `monkeypatch`'s teardown restores the attribute but not the cache. The
fence is `tests/conftest.py`'s autouse `_fence_certification_cache`, which
snapshots and restores the dict around every test; the poisoning pair in
`tests/test_structured_certify.py` fails without it. If you write a
fault-injection test, do not disable it.

## The normalization ladder

`verify/normalize.py`. `LADDER_VERSION = "l3-ladder-v1"`.

| rung | name | what it neutralises |
| --- | --- | --- |
| `L3.0` | (none) | nothing — strict field-by-field equality |
| `L3.1` | `strip-lineinfo` | `source`, `linedefined`, `lastlinedefined`, `lineinfo`, `LocVar.name`, upvalue names |

`certify_l3` tries rungs in ascending order and records the first that passes as
`rung` / ledger `l3_level`. **Measured: 0 of the `L3` ledger entries certify at
rung 0; all 1389 of them are at rung 1.** That is not a slack ladder, it is
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

### The candidate's strip mode follows the original's

`verify/certify.py::certify_l3` and `structure/structured.py::certify_proto`
(the wrapper path) both compile the candidate with
`strip=not carries_debug(original)`. Before M4 task 7 they compiled it `-s`
unconditionally — this section replaces the one titled "The candidate is always
compiled `-s`, so unstripped input barely certifies", which described that
older behaviour.

**Detection.** `verify/certify.py::carries_debug` walks
`verify/certify.py::debug_view` — the same per-proto field view
`structure/structured.py::_debug_fingerprint` hashes for the certification
memo, so there is exactly one enumeration of "the fields `compare_protos`
checks that `structural_hash` omits". Three of those fields are disjuncts:
`lineinfo`, `locvars`, `upvalues`, i.e. exactly `lundump.c` `LoadDebug`'s
three sized lists, i.e. exactly what `-s` zeroes out. The walk is over the
**subtree**, because `compare_protos` recurses.

`source` is deliberately **not** a disjunct, and this is not a detail.
Measured 2026-08-12 over the full corpus: all 1944 protos carry
`source = b"=?"` — a non-`None` placeholder — while all three debug lists are
empty in every one of them. Counting a non-`None` `source` as debug info would
classify all 229 files as unstripped and move the committed ledger.
`linedefined`/`lastlinedefined` are excluded for the plainer reason that they
survive `-s` (they are in `DumpFunction`'s body, not the debug segment), so
they carry no information about strippedness.
`tests/test_certify_stripmode.py::test_source_placeholder_alone_is_not_debug`
and `::test_every_corpus_proto_reads_as_stripped` pin both halves.

**What rung 1 now compares.** Rung 1 blanks locvar and upvalue *names* but
keeps each locvar's count, `startpc` and `endpc` (see
`tests/test_normalize_l31.py::test_l31_strips_locvar_and_upvalue_names_but_keeps_counts`).
Against a stripped original both sides' `locvars` are empty and that check is
`() == ()` — vacuous. Against an unstripped original the candidate now carries
real `locvars` too, so rung 1 checks that **every `local` was reconstructed
into the same lexical block over the same pc range**. Nothing else in the gate
makes a claim about lexical scope: `code` cannot see it, because `luac`
allocates the same register whether or not a value is bound to a name.

The negative control that makes this falsifiable is in
`tests/test_certify_stripmode.py`. Three sources compile to byte-identical
`code`, `constants` and `maxstacksize`, differing only in one `LocVar.endpc`:

| source | `a`'s scope | verdict, original `-s` | verdict, original unstripped |
| --- | --- | --- | --- |
| `do local a = f() g(a) end` `return` | endpc 5 | — (this is the original) | — |
| `do local l0_0 = f() g(l0_0) end` `return` | endpc 5 | `L3` | `L3` rung 1 |
| `local l0_0 = f() g(l0_0)` `return` | endpc 6 | `L3` | `L1`, field `locvars` |

The third row hoists the local out of the `do` block. A stripped original
cannot tell it from the second; an unstripped one refuses it on `locvars`,
with both sides non-empty and differing only in `endpc`. The trailing bare
`return` is load-bearing: `close_func` calls `removevars` before emitting the
implicit final RETURN, so a chunk-level local's `endpc` lands one pc later than
`leaveblock` would put it, while the explicit `return` allocates no register
and leaves the instruction stream identical. Put anything register-allocating
after the block instead (`h()`, `return 1`) and the hoist shifts every later
register, so the mismatch lands on `code` and proves nothing about scopes.

**What it changed, measured 2026-08-12.** The corpus does not move at all —
every corpus proto takes the `strip=True` branch, `corpus/ledger.jsonl` is
byte-identical after `scripts/run_corpus.py`, and so are all 229 files in
`build/decompiled/`. On unstripped input, over 30 hand-written sources
compiled both ways (the M4 task 7 report's own sample):

| | count of 60 rows | examples |
| --- | --- | --- |
| unstripped `L1` → `L3` | 12 | `local a = 1 print(a)`, `for i = 1, 10 do print(i) end`, `local function fact(n) ... end` |
| unstripped `L3` → `L1` | 2 | `repeat f() until g()`, `return a and b or c` |
| same level, rung 1 → rung 0 | 3 | `x = 1`, `print(1)`, `return 1` |
| identical verdict | 43 | all 30 stripped rows, plus 13 unstripped |

No stripped row changed level *or* rung. The three rung-1 → rung-0 rows are
originals with nothing in their subtree to reconstruct differently: the
unstripped candidate now reproduces `source`/`lineinfo` exactly, so they match
at the strict rung instead of needing the normalization.

**The 12:2 ratio is a property of that particular 30-source sample, not of the
change**, and reading it as "losses are rare" would be the wrong takeaway. The
general rule: **any statement whose reconstruction materialises a table-base,
index-target, or condition value as a `local` the original never declared now
refuses on unstripped input.** An ordinary example, not an exotic one —
`a.b = 1` (measured 2026-08-12):

```
local l0_0 = a
l0_0["b"] = 1
```

same `code` as the original, one locvar (`l0_0`, holding the table base) the
original doesn't have. `L3` rung 1 before this task, `L1` on `locvars` after.
`t[1] = t[2]` and `a[1] = c[2]` behave identically. `repeat`/`and`-`or` are the
same mechanism applied to a loop condition and a chain result, not a separate
phenomenon.

A second, independently-chosen sample of 30 ordinary one-liners — plain,
table-field and index assignments, calls, arithmetic, comparisons, method
calls, table constructors, `if`/`while`/`for`, `local function` — measured
2026-08-12 (29 of the 30 printed; one, a bare `a = b == c` chunk, hits an
unrelated `emit.lua` limitation and was excluded) gives:

| | count of 29 | examples |
| --- | --- | --- |
| unstripped `L1` → `L3` | 4 | `local a = 1`, `local a = f()`, `for i = 1, 10 do print(i) end`, `local function g() return 1 end` |
| unstripped `L3` → `L1` | 4 | `a.b = 1`, `a[1] = 1`, `a.b = c`, `a[1] = c[2]` |
| identical verdict | 21 | — |

Roughly **1:1**, not 12:1 — because this sample happens to contain four
ordinary table/index writes, the construct the mechanism above targets, while
the report's original sample contained none. Losses track how often
reconstruction invents a table-base or condition local, not how unusual the
Lua construct looks; a sample with more field/index assignments in it will
show more losses, not fewer.

The two losses in the report's original sample are worth reading in full
regardless — they are the same mechanism, just on less everyday syntax. In
both, the original declares no locals and our printer materialises one
(`local l0_0 = g()` for `repeat`'s condition; `local l0_0 = a and b or c` for
the chain's result). `code` is byte-identical, so under the old always-`-s`
candidate the invented local was invisible; the newly non-vacuous comparison
sees it and refuses. On the nested
path, single-use inlining *drops* a local the original had (`local y = x + 1
return y` prints as `return l1_0 + 1`) — but re-measured 2026-08-12, this is
**not** a new refusal: the wrapper candidate has always been compiled `-s`
before this task landed the rung-1 comparison it now uses, so it already
refused `L1` on `locvars` (the original's two locvars against the always-empty
candidate's `b='()'`). It still refuses `L1` on `locvars` after this task —
now against a candidate that carries one real locvar (the surviving
parameter) instead of none. The verdict is unchanged; only the mismatch is
better diagnosed. Both are pinned:
`::test_stricter_gate_refuses_reconstructions_that_invent_a_local` and
`::test_wrapper_path_refuses_when_reconstruction_drops_a_local`.

So the honest statement of the direction of change is **stricter**, not
"strictly stronger": a gate cannot begin examining a dimension and also promise
never to reject on it. What *is* strictly true is narrower and checkable, and
holds across both samples: the stripped branch is untouched code, and every
changed verdict — in either direction — is attributable to the debug-segment
lists ceasing to be vacuous. In all 14 level-changed rows of the report's
original sample the losing side's mismatches are confined to `locvars` (12
rows) or `locvars` + `upvalues` (2 rows, where the *count* differed because a
stripped candidate has no upvalue list at all); in all 8 level-changed rows of
the second, independent sample they are confined to `locvars` alone (that
sample has no upvalue-capturing closures to exercise the second case). None
mismatched on `code`, `constants`, `maxstacksize`, `nups`, `numparams`,
`is_vararg` or `subprotos.len` — the change moved exactly the dimension it was
aimed at, and the upvalue-count check on unstripped input became non-vacuous
along with the scope check.

Fixtures elsewhere in the suite are unaffected: they compile `-s`
(`tests/test_certify.py`, `tests/test_structured_certify.py`), and
`tests/test_emit_lua.py`'s deliberately-unstripped `_proto` exercises the
*printer* and makes a separate stripped copy when it wants to certify.

**Forward note for M4 Tasks 8-12 (loops, long-tail structuring).**
`repeat f() until g()` — a canonical loop shape those tasks will be printing
far more of — is one of this section's two measured losses: it refuses
certification when its original is compiled unstripped, for the mechanism
above (the condition value becomes a `local` the source never declared).
Every fixture in the suite compiles `-s` today, so this is currently covered
only by inheritance, not by design. New fixtures those tasks add should
compile `-s` **deliberately**, the way `test_certify.py` and
`test_structured_certify.py` already do — not merely because copying an
existing fixture happens to preserve it — so a later change to how loops are
authored in test sources doesn't silently reintroduce an unstripped `repeat`
or `while`/`for` fixture that certifies today only by luck of never having
been given debug info to compare.

## Register classification: simulating `lparser.c`'s `freereg`

`express/names.py::_stack_discipline`. This is M3's central analytical idea and
the one worth understanding before touching anything in `express/`.

Every register **definition** is classified `local` (gets a real
`local l0_7 = ...` declaration) or `temp` (its defining expression is inlined
into its single consumer). Getting this wrong does not produce wrong code —
certification catches it — but it is what decides the L3 rate, because a
`local` that luac never allocated changes `maxstacksize` and the whole
register numbering.

**Per definition, not per register (M4 task 13).** `RegClass.locals`/`temps`
remain a whole-function partition per register *number* and keep their strict
meaning (`temps` = *every* definition of this register is a temporary); the
field consumers should read is `RegClass.temp_defs`, a set of `(pc, reg)`
pairs, one entry per definition site. `reconstruct.write_reg` keys on it.
Why it has to: `lparser.c:1334` resets `fs->freereg = fs->nactvar` at the end
of every statement and `:1333` asserts `freereg >= nactvar` throughout, so one
slot is routinely a declared local in one statement and expression-stack
scratch in the next, and no single whole-function verdict fits it. The
conservative whole-function answer — `local` — materialized luac's expression
stack as named locals and emitted the `MOVE`s that copy into it: **253 of the
1478 corpus protos differed from the original by extra `MOVE`s and nothing
else** before this change, and 4 do after.

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
  one arm in `express/names.py::_stack_discipline`, the
  `op in (Op.CLOSE, Op.FORLOOP, Op.TFORLOOP)` branch: a loop's back edge is a statement
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

Every way of being unsure drives the answer toward "local", which is always
printable — the approximation is one-directional. Since M4 task 13 the
granularity is per definition, so an unsure definition no longer drags every
other definition of the same register number down with it.

### The four barriers on top of the pop-once rule

The pop-once accounting alone is not sufficient once verdicts are per
definition; four extra rules disqualify definitions the walk would otherwise
grade temporaries. Each was found by a *measured* regression, and each is
pinned by a fixture that fails when it is neutered (see
`tests/test_express_liverange.py`).

1. **`_same_block`** — a definition and its read must be in the same CFG basic
   block. Two properties depend on it. Execution counts: a definition read
   once per loop iteration but written once before the loop must not be
   popped on its first textual read. **`local i = 0 repeat i = i + 1 until
   i > 5` is not a live example of this** (fix round 1, F5(a), re-measured
   2026-08-11: neutering `_same_block` alone still certifies it `L3` — the
   ordinary pop-once accounting already disqualifies `i`'s definition on its
   own, since it is read twice textually, once by the `until` test and once
   by the body's own `i = i + 1`). The shape that DOES need `_same_block` for
   execution-count correctness: `local b, c = 1, 2  local a = b or c
   while a do a = b or c end print(a)` — neutering the guard silently turns
   the loop body's reassignment of `a` into a fresh unrelated local instead
   of a write to the outer `a`; certification refuses it (never ships), and
   it is pinned as `tests/test_express_liverange.py::
   LOCAL_CASES_CERT_ONLY[0]`. Block scoping:
   `emit.lua` wraps every `if` arm and loop body in `open_scope`/`close_scope`,
   which roll back the staging environment at `end`, so a value staged before
   a block and popped inside it has its pop undone and **whatever the block
   computed from it disappears from the output**. `snr_common.lua:main_77_20`
   motivated this rule during the task's development, but does **not**
   reproduce it at HEAD (fix round 1, F5(b), re-measured 2026-08-11: printing
   it with and without the guard is byte-identical) — historical, not a live
   pin. Stricter than either property needs (`f(a or b)` stages the
   callee in one block and calls it in another); the cost was measured, not
   assumed.
2. **The RK/literal barrier (`_bar_literal_operands`)** — a definition that
   would print as a Lua literal must not be inlined into an operand slot where
   `lcode.c` would have used a constant instead of a register. `luaK_exp2RK`
   encodes literals straight into B/C for the `ArgMode.K` slots (`OP_SPECS`,
   transcribed from `lopcodes.c`), so the original's use of a *register* there
   proves the slot held a local: `local a = 1  a = a + 1` inlines to
   `local a = 1 + 1`, which luac folds back into one `LOADK`. `luaK_prefix`'s
   `codearith(OP_UNM)`/`codenot` fold a literal operand the same way, so
   `UNM`/`NOT` get the rule too even though their B is `ArgArgR`.
   **`MAXINDEXRK` matters and the test differs by constant type**: a *string*
   literal is already `VK` when `exp2RK` sees it, so the check is on its index
   (`e->u.s.info <= 255`); a *number*, nil or boolean is `VKNUM`/`VNIL`/
   `VTRUE`/`VFALSE` and is interned only at `exp2RK` time, so the check is on
   the table's SIZE (`fs->nk <= 255`). Using the index for numbers cost
   `snr_crd_15.lua:main_1` and `snr_crd_20.lua:main_1` — both >400 constants —
   their certification; dropping the `MAXINDEXRK` refinement entirely cost 11
   more and 12 downgrades.
3. **`MOVE d, s` with `s < d` proves `s` held a named local.**
   `luaK_exp2nextreg` runs `freeexp` first, and `freeexp` only releases a
   `VNONRELOC` expression sitting at `freereg - 1` (it asserts exactly that),
   so discharging a temporary into the next free register finds
   `reg == e->u.s.info` and emits nothing at all. A copy from a lower slot
   upward is what luac emits instead: `luaK_dischargevars` rewrites `VLOCAL`
   to `VNONRELOC` carrying the local's own slot (`lcode.c:306-309`), and
   `discharge2reg`'s `VNONRELOC` arm then finds `reg != e->u.s.info` and codes
   the `MOVE` (`lcode.c:367-371`). `discharge2reg` has no `VLOCAL` case of its
   own. Without this rule,
   `local n = p  n = string.gsub(n, ...)` collapses the whole reassignment
   chain into one nested expression and every `MOVE` disappears from the
   recompile (`snr_common.lua:main_77_1`).
4. **Read-poisoning blames the last definition.** A read of a slot with
   nothing pending is a second read of an already-consumed temporary; it
   disqualifies *that* definition (`last_def`), which is what gives the second
   read a name to refer to. Loop control slots are exempt from the poisoning
   but not from being pushed: a `for` header's own `FORLOOP`/`TFORLOOP`
   re-reads its control triple every iteration, and blaming the staging for
   that turns `for i = 1, 10` into `local l0_0 = 1  for i = l0_0, 10, 1`.

Two seed sets that used to be one, for the same reason (M4 task 13): a
control slot that fails `_control_lifetime_ok` is by that verdict an ordinary
register a loop header merely reuses, so it is no longer seeded as a known
local — otherwise a `for k, v in pairs(x)` at the end of a function
retroactively materializes every temporary that ever used slots `a`/`a+1`/
`a+2` anywhere before it. And the "write to a named local is a statement
boundary" rule now consults `named_locals` (parameters, captured slots, `for`
variables) rather than the no-push seed, because a `for` header's staging
writes happen *mid*-statement.

### The two `promote_all()` calls are not interchangeable

Documented in `express/names.py::_stack_discipline`, under the comment
beginning "NOTE on the two intermediate `promote_all()` calls below"; both
were separately fault-injected
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

**This whole table is M3 history and none of it is re-derivable at HEAD.**
The intermediate rows (3, 339, 339, 1575) were each measured at the commit
that landed that change during M3's development, not at this runbook's
`fb85f2f`, and the tree has moved past every intermediate state. The final
row (1577, 81.12%) matched `corpus/ledger.jsonl` at `fb85f2f`; **it no longer
does** — M4 took the occurrence count to 1855 (95.4%), so re-deriving 1577
from today's ledger is impossible and an earlier revision of this paragraph
claiming otherwise was correct only until M4 task 1 landed. The table is kept
for the *lesson*, which does not depend on the absolute numbers.

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

- corpus arm — walks all 229 files, lifts all 1944 protos. **Measured
  (M4 task 8): all 214192 instructions checked, 0 disagreements.** 6981 of
  them carry an open (`R[base..top)`) region — 6949 `CALL`, 26 `VARARG`,
  3 `RETURN`, 3 `TAILCALL` — and are checked for their *static* part only;
  the `top`-relative part has no static register set to compare against and
  is outside what this gate reconciles. (Until M4 task 8 those rows were
  skipped outright. See below.)
- corpus opcode-reach pin — the corpus arm reaches **33 of 38 opcodes**
  (`SELF`, `POW`, `UNM`, `NOT`, `CLOSE` never occur). Pinned as a lower bound
  so the reach cannot silently shrink — `checked > 100_000` would not notice,
  since 81227 of the checked rows are `LOADK` alone.
- synthetic arm — the same invariant over an exhaustive operand grid built with
  `tests/synth.mk_instr` (7448 rows), reaching **38 of 38 opcodes**.
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
- **`lift/effects.py` omitted `writes_open` on `TAILCALL`** — found here in
  task 10, fixed in **M4 task 8**. `lvm.c:630-632`, the `PCRC` (non-Lua
  callee) branch of `OP_TAILCALL`, leaves the callee's results at `R[a..top)`
  for the immediately following `RETURN A 0` to read, and `lvm.c:611` asserts
  `GETARG_C(i) - 1 == LUA_MULTRET` so there is no fixed-result form to gate
  on: the row's `writes_open` is unconditional. The differential run CLAUDE.md
  requires for an axiom-layer change was done over all 1944 proto occurrences
  (`classify_registers`' four fields plus each proto's certification verdict,
  before and after): **nothing moved, and `corpus/ledger.jsonl` came back
  byte-identical.** The reason is `_block_floor`, not terminality —
  `successors(TAILCALL) == ()` makes every `TAILCALL` end its basic block, so
  it can never sit between a staging producer and the loop header consuming
  it. Details and the synthetic case that does reach the barrier:
  `tests/test_effects_tailcall.py`.

  The fix's one visible consequence was in this gate: with the blanket
  open-region skip in place, giving `TAILCALL` a `writes_open` silently
  dropped every `TAILCALL` row from both arms. Rather than accept the
  coverage loss, task 8 removed the skip — `_registers_touched` never names
  an open region's registers (every branch that could is guarded by
  `if b`/`if c` and degenerates to the empty set exactly when the region
  opens), so the subset assertion is well-posed for those rows and was simply
  discarding their static half. Measured with the skip removed: 0 violations,
  +6981 corpus rows, +1 corpus opcode (`VARARG`, whose 26 occurrences are all
  `B == 0`).

## The effect lattice: what the three modes mean, and why `STRICT` stays

M4 task 11. Evidence: `tests/test_effects_modes.py`. Per-row argument:
the comment block above `_row` in `src/pyluadec/lift/effects.py`, and the
`EffectMode` docstring.

### What the lattice is for

`lift/effects.py` grades every opcode into `PURE < READ_HEAP < WRITE_HEAP <
ARBITRARY` under three modes. CLAUDE.md's standing statement was that **only
`STRICT` has a justification** — the other two columns were asserted. This
section is the calibration.

Right-size it before reading further: **the lattice is not the inlining gate
and never moved the L3 rate.** M3 task 8 deleted `_adjacent_pure` and the
`EffectMode` knob from `express/names.py`; loosening the effect barrier
measured **+0.0 protos**, while simulating `lparser.c`'s `freereg = nactvar`
was worth +63.6 points (see "Register classification" above). The lattice is
calibrated because M5's pass registry and any reordering pass will consume it,
not because it is expected to move a number.

### The modes are a chain, and that does most of the work

The three modes are not three independent tables. They are nested assumption
sets:

| mode | assumes |
| --- | --- |
| `STRICT` | nothing beyond the Lua 5.1 VM |
| `NO_METAMETHOD` | …additionally, no value an instruction touches carries a metatable whose event that opcode could fire |
| `TRUSTING` | …additionally, a table *read* may be reordered freely — no intervening store or call changes what it returns |

A grading sound under a weaker assumption set is sound under a stronger one.
So **any row whose three columns are identical needs no argument beyond
`STRICT`'s** — the looser columns are entailed, for free.

Derived mechanically from `analyze()` by
`test_mode_columns_split_20_entailed_18_relaxed`:

- **20 of 38 rows are identical in all three modes** — `MOVE LOADK LOADBOOL
  LOADNIL NEWTABLE GETUPVAL SETUPVAL NOT JMP TEST TESTSET CALL TAILCALL RETURN
  FORPREP FORLOOP TFORLOOP CLOSE CLOSURE VARARG`. Entailed; nothing owed.
- **18 rows have at least one looser column strictly below `STRICT`** —
  `GETGLOBAL GETTABLE SELF SETGLOBAL SETTABLE SETLIST ADD SUB MUL DIV MOD POW
  UNM LEN CONCAT EQ LT LE`. Each of these carries a `# nm:` / `# tr:` line in
  `_row`.

And, from `test_trusting_moves_only_four_rows_below_no_metamethod`:
**`TRUSTING` moves exactly 4 rows below `NO_METAMETHOD` — `GETGLOBAL`,
`GETTABLE`, `SELF`, `LEN`, all `READ_HEAP → PURE`.** That is the entire value
`TRUSTING` adds over `NO_METAMETHOD`, and all four are `# UNARGUED`.

Standing tally (2026-08-12, after M5 task 1): **`NO_METAMETHOD` is argued on
all 38 rows and `# UNARGUED` on 0. `TRUSTING` is argued on 34 and `# UNARGUED`
on 4 (`GETGLOBAL`, `GETTABLE`, `SELF`, `LEN`).** `LEN` was the last
`NO_METAMETHOD` `# UNARGUED`, and M5 task 1 closed it by *regrading* rather
than arguing — the grading it carried was wrong (see "The `LEN` regrade"
below). The 20/18 entailment split above did **not** move with that regrade,
which is worth stating because the M5 plan predicted it would: `LEN` was
already one of the relaxed 18 (`STRICT` = `ARBITRARY`, looser columns below
it) and it still is. The split is derived from `analyze()`, so the test
settled it.

### The census, and its limit

Re-derived 2026-08-12 by
`test_corpus_never_names_metamethod_machinery` over the 229-file corpus:

| quantity | measured |
| --- | --- |
| files / proto occurrences | 229 / 1944 |
| constants | 71414 |
| string constants | 49063 (23586 distinct) |
| constants containing `__` (any metamethod event name) | **0** |
| constants containing `setmetatable`/`getmetatable`/`rawget`/`rawset`/`rawequal`/`newproxy`/`getfenv`/`setfenv`/`debug` | **0** |
| positive control (`vms`, the most-read global) | 993 |

The positive control is there because a census that answers "zero everywhere"
proves nothing if the scan is broken; the same loop that returns 0 for every
needle above returns 993 for `vms`. All comparisons are on `bytes`; the corpus
strings are Japanese game text and are never decoded.

A Lua 5.1 script cannot install a metatable without naming `setmetatable`, and
cannot name a metamethod event without a `__`-prefixed string. So **no table
this corpus builds itself carries a metatable.** That is the whole of
`NO_METAMETHOD`'s empirical support.

One loophole worth closing explicitly, since a static census over constants is
only as good as its claim to see all the code: the corpus never names
`loadstring`, `dofile` or `require` (0 constants each, measured the same
session), and `load` is never read as a global — so the scripts cannot compile
a chunk at runtime that the census would miss. The only unseen code is the
engine's own.

**The limit matters more than the result, and this project has been burned by
dropping exactly this kind of caveat.** The census sees only what the scripts
name. Measured the same session:

- of the **164** distinct global names the corpus reads (51497 `GETGLOBAL`
  sites), **56 are never written by any of the 229 files** — they arrive from
  outside the corpus. 52 are game-engine API (`layerLoad`, `playBGM`,
  `fontPrint`, `wait`, `switchScreen`, …) and 4 are Lua stdlib (`math`,
  `string`, `pairs`, `select`);
- **8379 of the 11910 `GETTABLE` sites** index a value whose nearest
  textually-preceding writer is a `GETGLOBAL`, against **188** that index a
  freshly `NEWTABLE`-d one. (That split comes from a straight-line backward
  scan that ignores control flow — an order of magnitude, not an exact
  attribution. The 164/56 global-name split is exact.)

Engine-supplied globals and userdata may carry `__index`, `__newindex` or
`__gc` that no constant table can reveal. **`NO_METAMETHOD` is therefore NOT
proven for `GETGLOBAL`/`GETTABLE`/`SELF`/`SETTABLE` on engine values** — and
those are the common case, not the exotic one.

`TRUSTING` is worse off: the corpus does not merely fail to support it, it
*falsifies* it. 892 `SETGLOBAL` sites over 108 global names that are also
read; **29 protos read and write the same global name**; 1667 `SETTABLE` + 92
`SETLIST` sites; 44809 `CALL` sites, any of which may store into any reachable
table.

### The decision: `STRICT` stays the default

1. **`STRICT` remains the pipeline-wide default.** `lift.lift_proto`'s `mode`
   parameter defaults to it, and nothing in `src/pyluadec/` selects anything
   else — pinned by
   `test_strict_is_the_default_and_the_only_mode_in_use`, which fails if a
   later change starts lifting under a looser mode without updating this
   section.
2. **`NO_METAMETHOD` is a permitted per-pass opt-in for M5**, scoped: sound
   for tables the script constructed, unproven for engine values. A pass that
   wants it must establish the value class it applies to, per region. It is
   not a safe global default precisely because the unproven case dominates.
3. **`TRUSTING` is not recommended for any pass.** Everything it buys over
   `NO_METAMETHOD` is treating four table-read opcodes as `PURE`, and the
   corpus supplies counterexamples to exactly that. It is kept in the enum
   (removing it is a behaviour change to the axiom layer, out of scope here)
   with all four of its distinguishing rows marked `# UNARGUED`.

Nothing downstream needs loosening today. That is why the M4 task 11
calibration was a documentation-and-tests task, with `lift/effects.py`'s
behaviour byte-for-byte unchanged (verified by replaying
`analyze`/`successors`/`extra_words` for all 38 opcodes over an operand grid
against the pre-change file: 82080 identical comparisons). **M5 task 1 then
changed exactly one cell** — see below.

### The `LEN` regrade (M5 task 1), and one finding still not fixed

An axiom-layer grading change needs the full protocol — an `lvm.c` citation
*plus* a differential run (M4 task 8 is the worked example). M4 task 11 found
two under-gradings and, having budget for the argument but not the protocol,
recorded both instead of touching either. M5 task 1 ran the protocol for the
first of them; the second still stands.

- **`LEN` at `NO_METAMETHOD` was wrong (`PURE`) and is now `READ_HEAP`** —
  M5 task 1, commit in `docs/runbooks/m3-backlog.md` §M5.1. `OP_LEN` is
  `lvm.c:514-533` and switches on the operand's *type* before any metamethod
  is consulted, so a table never reaches the `default:` arm at all: Lua 5.1
  has no table `__len`, and `NO_METAMETHOD`'s assumption removes nothing from
  this path. The `LUA_TTABLE` arm, `lvm.c:517-520`, is
  `setnvalue(ra, cast_num(luaH_getn(hvalue(rb))))`; `luaH_getn`
  (`ltable.c:560-576`) reads `t->sizearray` and `t->array[...]`, and for a
  boundary in the hash part delegates to `unbound_search`
  (`ltable.c:532-553`), which calls `luaH_getnum` (`ltable.c:435-449`)
  repeatedly. As graded before, a `SETTABLE` could legally be reordered across
  a `#t` and change its result. 22 `LEN` sites in the corpus, so not vacuous.
  (The `LUA_TSTRING` arm, `lvm.c:521-524`, really is `PURE` — it reads
  `tsvalue(rb)->len` off an immutable string, so `READ_HEAP` over-approximates
  that arm; the grading is per-opcode. The arm at `lvm.c:525-530` is the
  `default:` metamethod case and is emphatically not pure; an M4 draft of this
  bullet cited `lvm.c:523-526`, which straddles the two. All five ranges
  re-verified against `vendor/` at M5 task 1.)
  **The differential was null**, over all 1944 proto occurrences, and
  `corpus/ledger.jsonl` did not move — for two independently measured reasons:
  nothing in `src/` selects a looser mode, and, stronger, **no module under
  `src/pyluadec/` reads `InstrEffects.effect` at all** (the lattice stopped
  being the inlining gate at M3 task 8). Both legs are pinned by tests; the
  full record lives in `tests/test_effects_len.py`'s module docstring, which
  is where to look before making the next axiom-layer grading change.
- **`NEWTABLE` and `CLOSURE` are graded `PURE`/`may_error=False` at all three
  modes despite being able to run arbitrary Lua.** Both end in
  `Protect(luaC_checkGC(L))` (`lvm.c:461-467`, `lvm.c:723-742`);
  `luaC_checkGC` (`lgc.h:80`) can advance the collector into `GCSfinalize`
  (`lgc.c:592-595`), where `GCTM` (`lgc.c:445-473`) calls a userdata's `__gc`
  via `luaD_call`. Unobservable for this corpus — a Lua 5.1 script can only
  create userdata via `newproxy`, and the census finds 0 occurrences of it and
  0 of `__gc` — but an under-approximation in general, and it is the same
  engine-value blind spot as above wearing a different hat. `CONCAT`'s
  `NO_METAMETHOD = PURE` inherits the same caveat (string interning allocates
  too), which is why it is graded consistently with these two rather than
  singled out.

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

Observed for `snr_memory.lua` (re-run 2026-08-12): `2/6 protos L3; root=L1` →
the fallback chunk ships, while two nested protos (`main_0`, `main_1`) still
record genuine `L3` proofs.

### Print the structured source for a file whose root certifies

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run python -c "
import os; from pathlib import Path
from pyluadec.ingest import load_file
from pyluadec.emit.lua import print_chunk
print(print_chunk(load_file(Path(os.environ['PYLUADEC_CORPUS_DIR'])/'snr_crd_0.lua')))"
```

212 of the 229 files have an `L3` root and therefore ship real structured source
(92 at M3 close).

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

Current output (M4 task 13): 1478 unique protos / 1944 occurrences / 229
files, `compile_ok 1478/1478`, `level L3 1389`, `level L1 89`, L3 share 94.0%
unique / 95.4% occurrences, `L3 rung 1: 1389`, `ladder l3-ladder-v1`. (At M3
close it was `level L3 1112` / `level L1 366`, 75.2% / 81.1%.)

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
from pyluadec.verify.certify import carries_debug

C = Path(os.environ["PYLUADEC_CORPUS_DIR"])
p = load_file(C / "snr_novel.lua").subprotos[6]         # the proto under test
cert = certify_proto(p, is_chunk_root=False)
print("level", cert.level, "fields", sorted({m.field for m in cert.mismatches}))

# Rebuild EXACTLY certify_proto's wrapper. Every line below is load-bearing:
# `decls` because a body that names u0.. compiles those as GLOBALS without it,
# the `is_vararg & 2` arm because a vararg proto's frame differs, and the strip
# mode because otherwise the locvar/upvalue comparison you are debugging is not
# the one certify_proto made.
upn = tuple(f"u{i}" for i in range(p.nups))
body = _print_proto_body(p, depth=1, upval_names=upn)
params = ", ".join(f"l1_{i}" for i in range(p.numparams))
if p.is_vararg & 2:
    params += ", ..." if params else "..."
decls = ("local " + ", ".join(upn) + "\n") if upn else ""
mine = load_bytes(oracle.compile_source(
    f"{decls}return function({params})\n{body}end\n".encode(),
    strip=not carries_debug(p))).subprotos[0]
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

Observed output for that proto (run verbatim 2026-08-12):

```
level L1 fields ['code', 'constants.len']
first divergence at pc 13:
  original : LOADK      3 -7
  ours     : LOADK      3 -8
code len 15 vs 20 | maxstacksize 7 vs 7
```

`snr_novel.lua:main_6` is the runbook's own cluster-D exemplar (see "Current
capability boundary"), and the body it prints is:

```lua
for l1_3 = 0, 20, 1 do
  layerLoad(l1_3, "")
end
local l1_0 = switchScreen
local l1_1 = 0
local l1_2 = ""
l1_3 = 60
l1_0(l1_1, l1_2, l1_3)
```

Read that as: register 3 is the numeric `for`'s external index variable, and
after the loop the original reuses that register for something unrelated. We
print both as `l1_3` — but a Lua control variable's scope ends at its `end`, so
the trailing `l1_3 = 60` recompiles as a **`SETGLOBAL`**, which adds the
constant `"l1_3"` to the pool and five instructions to the body (15 → 20). The
first *reported* divergence is at pc 13, `LOADK 3 -7` against `LOADK 3 -8`:
that is only the constant indices shifting by one because of the added
constant. As with any `code` mismatch, the first differing word is a symptom;
here the cause is one instruction later — the `SETGLOBAL 3 -7` at pc 14, with
the three added `MOVE`s following at pcs 15-17 — and is a **scoping** defect
in the printer's naming, not an arithmetic one.

**If you change the exemplar, keep the wrapper intact.** Dropping the `decls`
line is the classic way to chase a phantom: `snr_memory.lua`'s `subprotos[0]`
has `nups == 1` and *certifies* (`level L3 fields []`, `code len 39 vs 39`),
but a wrapper without `local u0` compiles the body's `u0` as a global and
reports a divergence at pc 17, `GETUPVAL 11 0` against `GETGLOBAL 11 -6`, that
`certify_proto` never saw. Both readings measured 2026-08-12.

Cross-check against the raw listing with

```bash
# -o /dev/null: luac DUMPS unless told not to, so a bare -l run
# drops a luac.out into your cwd (see decompile-pipeline.md).
./build/luac_sz4 -o /dev/null -l -l <corpus>/snr_memory.lua | less
```

and against the fallback output's `__pld_pc` state machine (see
`decompile-pipeline.md`, "Reading fallback output") when you need to know what
the original instruction stream actually did.

### Run the suite

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run pytest              # 512 tests, ~40s (measured 2026-08-12)
PYLUADEC_CORPUS_DIR=<corpus> uv run pytest tests/test_effects_emitter_consistency.py -v
```

Without `PYLUADEC_CORPUS_DIR` the corpus-gated tests **skip**, including the M2
and M3 exit gates. `tests/conftest.py` prints a red banner in that case; heed
it (see CLAUDE.md).

`tests/test_generated_semantic_cases.py` (M4 task 5) only runs
`DEFAULT_LIMIT` (3) of its `CASE_COUNT` (24) deterministic differential-
execution cases by default, to keep the standing suite inside its speed
budget. The full sweep is a manual command, not part of the default run:

```bash
PYLUADEC_GENERATED_CASE_LIMIT=24 uv run pytest tests/test_generated_semantic_cases.py -v   # 24 tests, ~1.7s
```

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
by reading the ledger diff in review, not by the suite. `scripts/run_corpus.py`'s
`main()` takes the higher level (its `_RANK` comparison) when one structural
hash occurs more than once.

## Current capability boundary — measured, not estimated

All figures over the 229-file corpus: 1478 unique proto shapes, 1944
occurrences.

| stage | unique | occurrences |
| --- | --- | --- |
| `build_sir` accepts the proto's own body | 1447 (97.9%) | 1913 (98.4%) |
| whole subtree prints (proto **and** every descendant) | 1424 (96.3%) | 1890 (97.2%) |
| certifies `L3` | **1389 (94.0%)** | **1855 (95.4%)** |

Three different numbers, three different causes. M4 tasks 3 and 4 moved the
top two rows and did not move the third at all; **task 13 moved only the
third**, from 1139/1604 to the figures above, by making register
classification per definition rather than per register number. 212 of the 229
files now ship structured source (92 at M3 close). Structuring refusals are
again the largest single residual cluster.

1. **1478 → 1447: `build_sir` refuses 31 unique protos** (169 before M4 task
   3, 43 after it, 31 after task 4). 26 carry a back edge it will not claim,
   5 are acyclic refusals. By message: 11 `else-join out of range`, 10
   `if targets out of range` (in **every** case the if's false-exit was
   threaded onto an *enclosing if's* else-skip by the same `luaK_jump` jpc
   concat `_structure_if` already unwinds for loop headers — not one is
   `jt == break_target`), 10 `branch body block ... is unreachable`.
   `unrecognized transfer TESTSET` is gone: M4 task 4's `_match_cond_value`
   claims the `and`/`or` VALUE idiom as a `CondValue` region, which took the 8
   protos refused with that message plus 4 more that contain no TESTSET at all
   (`(<gate> and X) or Y` chains whose test `patchtestreg` rewrote to a bare
   `TEST`) and were refused as `if targets out of range`. All 16 protos that
   contain a TESTSET are still non-`L3`, but for reasons downstream of
   structuring — see point 3 and the note after it.
2. **1447 → 1424: 23 more unique protos build a region tree but do not print.**
   `print_chunk` inlines the whole tree at each `CLOSURE` site, so one
   unstructurable inner function takes its entire ancestor chain with it.
   Re-measured 2026-08-12 by asking, for each of the 23, whether every proto
   in its subtree prints on its own: **18 are descendant-driven and 5 are the
   proto's own body** — 3 `register N is read again after its staged value was
   consumed` (read-poisoning), 1 `_refuse_statements` (its own `CondValue`
   operand code reconstructs to a statement), 1 while-header code that
   reconstructs to a statement. (Was 139 protos before M4 task 3. An earlier
   draft said "6 of them" were `_refuse_statements`; that is the 1.)
3. **1424 → 1389: 35 unique protos print but do not certify.** This was the
   dominant gap until M4 task 13 (283 protos, of which 253 differed from the
   original by extra `MOVE` instructions and by nothing else at all). The
   cause was `RegClass`'s whole-function, per-register-*number* verdict, and
   the measured exemplar was `snr_crd_10.lua:main_2`: registers 0/1/2 are
   call-argument temps in its first six instructions and declared locals in
   the same slots before its `while` loop, `classify_registers` had to give
   one verdict, picked `local`, and the first six instructions came back with
   `MOVE`s. Task 13 made classification per definition and that cluster went
   from 253 to **4**.

   What is left, re-measured 2026-08-11 with the script below (89 unique
   protos below `L3` in total; the 54 in the first row belong to point 1's
   and point 2's causes rather than to this one):

   | cluster | unique |
   | --- | --- |
   | A. subtree refuses structuring | 54 |
   | D. extra `MOVE`s **plus** other additions | 16 |
   | B. same opcode histogram, operands differ | 14 |
   | C. extra `MOVE`s only | 4 |
   | E. other delta | 1 |

   The first differing instruction is a `GETGLOBAL` for 10 of the B cluster
   (constant-table ordering) and a `LOADK` for 10 of the D cluster. `NEWTABLE`
   size hints account for 3. These are three genuinely different problems and
   none of them is register classification. Re-run verbatim at M4 task 6 and
   reproduces byte-for-byte.

   Smallest exemplar per cluster (M4 task 6), with the ledger's own
   `refusal_reason`:

   | cluster | exemplar | insns | reason |
   | --- | --- | --- | --- |
   | A | `snr_lib.lua:main` | 5 | `structure: pc 73: if targets out of range` |
   | B | `snr_common.lua:main_77_0` | 5 | `mismatch: code` |
   | C | `snr_common.lua:main_24_1` | 19 | `mismatch: maxstacksize` |
   | D | `snr_novel.lua:main_6` | 15 | `mismatch: code` |
   | E | `snr_novel.lua:main_2` | 93 | `mismatch: maxstacksize` |

   (Cluster A's exemplar has 5 instructions in its OWN body: the refusal is a
   descendant's, since `print_chunk` inlines the whole tree. That is what
   makes the A cluster's size — 54 of the 89 — a count of *ancestor chains*,
   not of independent defects.)

   Two known-residual shapes are fixtured in
   `tests/test_express_liverange.py::KNOWN_RESIDUAL` with their causes:
   `_emit_multi`'s all-or-nothing materialization of a multi-result `CALL`
   (a generic `for` over `pairs(t)` prints `local l0_1, l0_2, l0_3 =
   pairs(l0_0)` where luac left the triple in the control slots), and
   `NEWTABLE`'s size hints (the constructor fold turns a following `t.k = s`
   statement into `{["k"] = s}`).

### The residual is standing data now: `refusal_reason` (M4 task 6)

Every non-`L3` ledger row carries a `refusal_reason` saying **why**; every
`L3` row carries `null`. Before this field a `build_sir` refusal and a
print-then-certify-rejection were indistinguishable in the ledger — both got
the same generic whole-range `fallback-state-machine` confession, which was
adequate only while nothing structured cleanly and then failed the comparison.
M4's loop work made that 35 of the 89 residual rows. `tests/test_m4_exit.py`
asserts the coupling in both directions and that the reason's kind is one of
the four in the committed vocabulary.

Four kinds; the full vocabulary and the payload rules live with the code, in
`structure.structured.ProtoCert.reason`:

| kind | meaning |
| --- | --- |
| `structure: <msg>` | `sir.build`/the printer refused to build a region tree |
| `reconstruct: <msg>` | a region printed but an expression under it could not be reconstructed |
| `compile: <phrase>` | the printed candidate (or its wrapper) did not recompile |
| `mismatch: <field>` | it printed and recompiled, and `compare_protos` differed on `<field>` |

Two deliberate exclusions, both about not putting corpus payload in a
checked-in file: the reason carries a `Mismatch`'s FIELD NAME and never its
`a`/`b` reprs (those are the actual code words and constants), and it never
carries `luac`'s error text (which echoes the offending source line). The one
raise site that used to interpolate a constant, `emit.lua._ident`, now reports
the constant's byte LENGTH instead — pinned by
`tests/test_emit_lua.py::test_ident_refusal_messages_do_not_quote_the_constant`.

`uv run python scripts/ledger_dashboard.py` prints the histogram (numbers in
the message collapsed to `N` for clustering). Measured 2026-08-11, 89 rows:

```
refusal: structure: pc N: else-join out of range                        18
refusal: mismatch: maxstacksize                                         18
refusal: mismatch: code                                                 17
refusal: structure: pc N: if targets out of range                       17
refusal: structure: pc N: branch body block at pc N is unreachable      13
refusal: reconstruct: register N is read again after its staged ...      4
refusal: reconstruct: pc N: and/or alternative reconstructs to N ...     1
refusal: structure: pc N: while-header code reconstructs to N ...        1
```

The two decompositions agree exactly: the six refusal rows sum to 54 (cluster
A) and the two `mismatch:` rows to 35 (clusters B–E). They are different cuts
of the same 89 — the A/B/C/D/E table classifies by *opcode-histogram delta at
the divergence point*, this one by *the first field `_cmp` reported*.

### The `L3.2 = canonical constant-pool order` rung: declined again, with the number

M3 measured 9 protos differing only by pool order and declined the rung. M4
task 6's brief set the bar at ≥20. **Re-measured 2026-08-11: 10.** The rung is
declined again; no `LADDER_VERSION` bump, `NORMALIZATIONS` unchanged.

The measurement is exact, not a proxy. For each of the 35 non-`L3` protos
whose candidate recompiled, walk the original/candidate pair recursively and
ask whether, at every proto, (a) all of rung 1's surviving scalar fields are
equal, (b) the constant pools are permutations of each other by payload-exact
key, and (c) the code arrays are equal once every constant-index operand is
replaced by the constant it names — the K modes come from `lift.opcodes`'
`OP_SPECS`, transcribed from `lopcodes.c`. Ten protos pass, all in
`snr_common.lua` (`main_9`, `main_12`, `main_14`, `main_28`, `main_36`–
`main_40`, `main_74_9`), one occurrence each: **10 unique / 10 occurrences,
0.68% / 0.51%.** A looser check (pools are a permutation at the divergence
point, ignoring the rest of the subtree) gives 11 — `config.lua:main` also
differs elsewhere, so a pool-order rung would not certify it.

Buying 10 rows costs a permanent widening of the gate: rung 2 would have to
argue that permuting a constant pool is meaning-preserving, and every future
certification would run under that admission. The trade was refused at 9 and
the population has barely moved. The script is
`scratchpad`-only by design (it is a one-off measurement, not a gate); its
logic is reproduced above in enough detail to rebuild in ten minutes.

### Census entries that are not corpus rows

Three known defects that the ledger cannot show, because they are either not
exercised by this corpus or not visible as a level. All three are pinned by
committed tests, so "known" here means recorded and fenced, not tolerated.

1. **The table-constructor fold reorders statements** (pre-existing, predates
   M4 task 13). `express.reconstruct` folds later field assignments back into
   the constructor and prints the constructor at the position of the LAST
   folded assignment, so any effectful statement standing between the first
   folded item and that position is printed *before* that item is evaluated.
   Reproduction, measured 2026-08-11:

   ```lua
   local function s(n) print(n) return n end
   local t = {}
   t.a = s(1)
   print("x")
   t.b = s(2)
   print(t.a, t.b)
   ```

   prints `1 x 2`; the structured print of it —
   `print("x")` then `local l0_1 = {["a"] = l0_0(1), ["b"] = l0_0(2)}` —
   prints `x 1 2`. **Unshippable**: the root does not certify, so the
   fallback chunk ships and its stdout matches the original exactly. Pinned
   by `tests/test_structured_certify.py::
   test_table_constructor_fold_reorders_statements_but_cannot_ship`, which
   asserts both the divergence and the fact that it cannot escape. Note the
   shorter repro that circulated for this (`local t = {} print(1)`) does
   reorder the statements but is NOT observable — the only statement that
   moves there is a pure `NEWTABLE`; two folded items straddling an effectful
   statement are needed to make it visible.

2. **Two of M4 task 5's five ported semantic-regression cases ship
   fallback**, and are pinned to `L1` so they fail loudly when fixed:
   `test_if_and_elseif_conjunctions_preserved` (refused,
   `structure: pc 4: if targets out of range` — the nested-AND-in-an-elseif
   -chain family, the same 17-proto corpus cluster) and
   `test_counter_closure_and_dispatch_mix` (prints, then differs on
   `maxstacksize` 18 vs 20 and 13 vs 15 constants — clusters B/D). Both
   docstrings in `tests/test_semantic_regressions.py` carry the full
   diagnosis. Both run their fallback artifact and check its stdout, so the
   *semantics* are regression-tested regardless of the level.

3. **`run_corpus.py`'s forced-`L0` path** used to keep whatever
   `confessions` the entry already had, which for an individually-`L3` proto
   in a chunk that failed to compile is `[]` — an `L0` row could ship
   unconfessed. Fixed in M4 task 6 (`_force_l0`); unreachable from the corpus
   (229/229 files compile), so it is pinned by unit tests instead:
   `tests/test_ledger.py::test_forced_l0_entry_is_confessed` and
   `::test_forced_l0_keeps_an_existing_confession`.

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
accepts own body         1447/1478 (97.9%)  1913/1944 (98.4%)
whole subtree prints     1424/1478 (96.3%)  1890/1944 (97.2%)
```

Row 3 needs no script: it is the committed ledger. `uv run python
scripts/ledger_dashboard.py` prints both bases (`L3 share (unique)` and
`L3 share (occurrences)`).

The refusal breakdown in point 1. Self-contained; re-run 2026-08-12, and the
eight lines it prints — 1478 / 31 / 26 / 5 / 195 / 169 / 16 / 8 — are the
output block below verbatim:

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
print(f"  back edge but accepted (loop)     {len(back - refused)}")
print(f"protos containing TESTSET           {len(testset)}")
print(f"  of which are refused              {len(testset & refused)}")
```

```
unique protos                       1478
build_sir refusals                  31
  of which carry a back edge        26
  acyclic refusals                  5
protos with a back edge at all      195
  back edge but accepted (loop)     169
protos containing TESTSET           16
  of which are refused              8
```

Point 3's opcode-histogram breakdown (re-run 2026-08-11 after M4 task 13; it
produced the 253/56/15/15 split quoted above as this task's baseline on
`dec379e`, and the 54/16/14/4/1 split below afterwards):

```python
# PYLUADEC_CORPUS_DIR=... uv run python -
# For every non-L3 unique proto, find the proto where compare_protos actually
# diverges (it RECURSES -- a root's own code often matches while a descendant's
# does not, so comparing only the top-level code arrays undercounts badly), and
# subtract the original's opcode histogram from the candidate's there. A delta
# of nothing but positive MOVE entries is the over-materialized-local
# signature.
import collections, os
from pathlib import Path
from pyluadec import oracle
from pyluadec.emit.lua import _print_proto_body, print_chunk
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.ingest import load_file, load_bytes
from pyluadec.lift.opcodes import decode
from pyluadec.pipeline import walk_proto_paths
from pyluadec.sir.build import StructureError
from pyluadec.structure.structured import certify_proto
from pyluadec.verify.certify import carries_debug
from pyluadec.verify.ledger import structural_hash

uniq, isroot = {}, {}
for f in sorted(Path(os.environ["PYLUADEC_CORPUS_DIR"]).glob("*.lua")):
    protos = {}
    walk_proto_paths("main", load_file(f), protos)
    for path, p in protos.items():
        h = structural_hash(p)
        if h not in uniq:
            uniq[h], isroot[h] = p, path == "main"

def ops(code):
    c = collections.Counter()
    for w in code:
        c[decode(w, 0).op.name] += 1
    return c

def candidate(p, root):
    """Exactly the proto certify_proto compares against, or None if it refuses."""
    strip = not carries_debug(p)                 # as certify_proto does
    if root:
        src = print_chunk(p)
        return None if src is None else load_bytes(
            oracle.compile_source(src.encode(), strip=strip))
    upn = tuple(f"u{i}" for i in range(p.nups))
    try:
        body = _print_proto_body(p, depth=1, upval_names=upn)
    except (StructureError, ReconstructError):
        return None
    params = ", ".join(f"l1_{i}" for i in range(p.numparams))
    if p.is_vararg & 2:
        params += ", ..." if params else "..."
    decls = ("local " + ", ".join(upn) + "\n") if upn else ""
    r = load_bytes(oracle.compile_source(
        f"{decls}return function({params})\n{body}end\n".encode(), strip=strip))
    return r.subprotos[0] if len(r.subprotos) == 1 else None

def nav(p, path):                      # paths are "root", "root/0", "root/0/1"
    for part in path.split("/")[1:]:
        if int(part) >= len(p.subprotos):
            return None
        p = p.subprotos[int(part)]
    return p

b, firstop = collections.Counter(), collections.Counter()
for h, p in uniq.items():
    cert = certify_proto(p, is_chunk_root=isroot[h])
    if cert.level == "L3":
        continue
    rec = candidate(p, isroot[h])
    if rec is None:
        b["A. subtree refuses structuring"] += 1
        continue
    path = cert.mismatches[0].path
    oa, ob = nav(p, path), nav(rec, path)
    if oa is None or ob is None:
        b["F. proto-tree shape differs"] += 1
        continue
    d = ops(ob.code)
    d.subtract(ops(oa.code))
    extra = {k: v for k, v in d.items() if v}
    if not extra:
        k = "B. same opcode histogram, operands differ"
    elif set(extra) == {"MOVE"}:
        k = "C. extra MOVEs only"
    elif extra.get("MOVE", 0) > 0 and all(v > 0 for v in extra.values()):
        k = "D. extra MOVEs + other additions"
    else:
        k = "E. other delta"
    b[k] += 1
    aa, bb = oa.code, ob.code
    j = 0
    while j < min(len(aa), len(bb)) and aa[j] == bb[j]:
        j += 1
    if j < min(len(aa), len(bb)):
        ra, rb = decode(aa[j], 0), decode(bb[j], 0)
        firstop[k[0] + " " + (ra.op.name if ra.op is rb.op
                              else ra.op.name + "->" + rb.op.name)] += 1
for k, v in b.most_common():
    print(f"{v:5d}  {k}")
print()
for k, v in firstop.most_common(6):
    print(f"{v:5d}  first differing instruction: {k}")
```

```
   54  A. subtree refuses structuring
   16  D. extra MOVEs + other additions
   14  B. same opcode histogram, operands differ
    4  C. extra MOVEs only
    1  E. other delta

   10  first differing instruction: B GETGLOBAL
   10  first differing instruction: D LOADK
    2  first differing instruction: B NEWTABLE
    2  first differing instruction: C JMP
    2  first differing instruction: D JMP
    1  first differing instruction: C NEWTABLE
```

The print-but-do-not-certify mismatch histogram in point 3. Self-contained —
run it verbatim like the two above. This is the only one that spends
`luac_sz4` subprocesses (35 of them):

```python
# PYLUADEC_CORPUS_DIR=... uv run python -
import json, os
from collections import Counter
from pathlib import Path
from pyluadec.pipeline import walk_proto_paths
from pyluadec.ingest import load_file
from pyluadec.structure.structured import certify_proto
from pyluadec.verify.ledger import structural_hash
from pyluadec.emit.lua import _print_proto_body
from pyluadec.sir.build import StructureError
from pyluadec.express.reconstruct import ReconstructError

def prints(p):
    try:
        _print_proto_body(p, depth=1,
                          upval_names=tuple(f"u{i}" for i in range(p.nups)))
        return True
    except (StructureError, ReconstructError):
        return False

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
print but do not certify: 35
  code             35
  maxstacksize     20
  constants.len    16
  const[i]         11
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
real one, since only a proto that prints can certify — was 1170/1478 = 79.16%
unique and 1636/1944 = 84.16% occurrences at M3 close; and the achieved
occurrence rate then, 1577/1944 = 81.12%, already exceeded 80.3%, which a
ceiling cannot allow. `structure/structured.py` now carries the measured
figures. The planning doc is a historical record and keeps its original text,
with a correction note at the top. `tests/test_m3_exit.py` never quoted the
figure — its only thresholds are its two `> 0.50` exit-gate assertions.

**M4 settled it beyond argument.** Printability is now 1424/1478 = 96.3%
unique and 1890/1944 = 97.2% occurrences, and the achieved `L3` rate is
1389/1478 = 94.0% / 1855/1944 = 95.4%. The "ceiling" is exceeded by more than
thirteen points on either basis. Kept here as a worked example of a
planning-stage number that survived into three documents and a module
docstring without ever being measured.

The other standing limits are the two probes. The **global-state probe**
(L1.5) reaches 225/229 files with 4 pinned divergences; read its reach table
before treating it as strong evidence, because for 222 of 229 files the entire
compared payload is `string:main=<function>`. The **behaviour probe** (L1.75,
M4 task 10) deepens that to 227/229 over 398196 recorded events — but its
reach is bimodal, not a uniform deepening: the 3000-event cap truncates 132 of
229 files, which contribute 99.5% of the events, while the other 97 contribute
a median of **10** events each. Both are documented in
`docs/runbooks/m3-backlog.md`; neither is L2.

## Relationship to the fallback runbook

`docs/runbooks/decompile-pipeline.md` documents the M2 fallback path and stays
authoritative for it. The fallback is **not** deprecated and is not going away:
it is the floor. Every file whose root does not certify still ships fallback
source, and today that is 17 of 229 files (137 at M3 close).

Practical division of labour:

- Anything about `ingest` / `lift` / `cfg` / effect modes / `__pld_R`,
  `__pld_U`, `__pld_pc`, `__pld_top`, `__pld_F` / the ledger's non-M3 fields /
  known M2 semantic gaps → `decompile-pipeline.md`.
- Anything about `sir` / `express` / `emit` / certification / the normalization
  ladder / the L3 rate → this file.
- The M5 agenda, the global-state and behaviour probes, and the deferred
  minors → `docs/runbooks/m3-backlog.md`.
- Readability against the predecessor's shipped output →
  `docs/reports/m4-readability.md`.

# Structured pipeline runbook (M3–M5)

This is the operational and conceptual guide to the **structured** decompile
path: dominator-driven region identification, expression reconstruction, the
pure structural printer, and the per-proto `L3` certification gate that decides
whether any of it is allowed to ship.

Written for M3, extended through M4 (loop recognition, the `and`/`or` value
idiom, per-definition register classification, strip-mode matching, the effect
lattice) and again through M5, which added roughly 900 lines here: output
surface v2, hybrid chunks, the L2 key-sequence gate and the ratchet tooling.
**This file is the authority for the capability boundary, for the effect
lattice and for the L2 grant rule.** Open work lives in
`docs/runbooks/m3-backlog.md`'s **"M6 agenda"** (the "M5 agenda" this line
used to route to is now a closed record above it); the readability comparison
against the predecessor's shipped output is `docs/reports/m4-readability.md`,
and M5's quality evaluation is `docs/reports/m5-quality.md`.

It is the companion to `docs/runbooks/decompile-pipeline.md`, which documents
the M2 **fallback** path. The two coexist and neither replaces the other — see
"Relationship to the fallback runbook" at the end.

Every quantitative claim below was measured in this repository against the
229-file corpus (originally at commit `fb85f2f`; the capability-boundary
figures re-measured through M4 and M5, and last verified 2026-08-13 at
`b73a513` plus the M5 final fix round), or
is cited to a specific symbol / test name. If a number here stops matching
reality, that is a bug in the runbook; re-measure and fix it rather than
routing around it.

**Cite symbols, not line numbers.** Line citations in this project have a
measured failure rate: one sweep checked 19 of them and found **9 stale**, and
a later round introduced 6 more through its own docstring growth. Prefer
`module.py::symbol`. The `file:line` citations that remain here have each been
verified against the tree; convert any you touch.

**How to re-derive — read this before trusting a number here.** Three tiers:

1. **Inlined and verified.** **Four** blocks under "Current capability
   boundary" — the capability-boundary table, its refusal breakdown, the
   opcode-histogram breakdown, and the print-but-do-not-certify histogram —
   each carry a complete runnable script printed together with the output it
   produced when run on **2026-08-13**. **All four of those pasted outputs
   were stale at the M5 wrap while the prose around them was right**, and the
   fourth was still stale after the first three were re-run, because "I
   re-ran the blocks" was itself written without counting them. Re-run the
   block; never trust the paste, including this sentence's claim about it.
2. **Read off a committed artifact or a standing test.** The L3 rates come
   from `corpus/ledger.jsonl` (`uv run python scripts/ledger_dashboard.py`).
   The 228/229 global-state figure comes from
   `tests/test_global_state_probe.py` / `scripts/probe_global_state.py`
   (it was 225/229 with 4 pins until M6 task 12 converged three of them;
   re-run 2026-08-14). The
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

(Line counts re-derived 2026-08-13, M5 task 11. The three this section used
to carry — 73 / 836 / 1143 — were all stale; only `names.py`'s changed in
that task.)

- `express/expr.py` (89 lines) — the expression nodes, all frozen dataclasses:
  `ConstExpr`, `LocalExpr`, `GlobalExpr`, `UpvalExpr`, `IndexExpr`, `BinExpr`,
  `UnExpr`, `CallExpr`, `VarargExpr`, `ClosureExpr`, `TableExpr`.
- `express/names.py` (494 lines) — `classify_registers(fn) -> RegClass`
  (`locals` / `temps` / `loop_vars`) and `name_for(reg, depth) -> "l{depth}_{reg}"`.
  It owns the half of the analysis that is about `for` headers: which slots a
  loop header genuinely owns, and over which pcs.
- `express/freereg.py` (558 lines) — `stack_discipline(...)`, the simulation of
  `lparser.c`'s `freereg = nactvar` allocation discipline, split out of
  `names.py` by M5 task 11. It knows nothing about `for` headers or `RegClass`;
  the four callbacks in its signature are its entire interface to `names.py`,
  and were already so before the split, which is what made the split textual.
  See "Register classification" below.
- `express/reconstruct.py` (1427 lines) — the `Reconstructor`: statement nodes
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

`emit/lua.py` (1128 lines as of M5 task 7; 707 at M3 close). Public entry
points:

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

#### Output surface v2 (M5 task 7)

The text this printer emits is a **versioned surface**, and M5 task 7 bumps
it to **v2**. CLAUDE.md's 下游耦合 section records that the predecessor's
`post_process/` chain matched the *old* emitter's exact style with
line-anchored regexes: `v\d+` naming, one statement per line, no top-level
indentation, `name = function(...)` form, double-quoted strings. That chain
is already incompatible with this project — our synthesized names are
`l<depth>_<reg>`, not `v\d+`, which broke the naming anchor two milestones
ago — and CLAUDE.md explicitly licenses a versioned replacement rather than a
byte-level replica ("不必字节级复刻旧输出…要么显式版本化"). v1 quirks are
therefore not preserved. What changed in v2, all of it presentation and all
of it proven certification-invariant by `corpus/ledger.jsonl` staying
byte-identical across each commit:

| | v1 (through M5 task 6) | v2 (M5 task 7) |
| --- | --- | --- |
| `else` + a single `if` | `else` / nested `if` / extra `end` | `elseif` |
| constant string key | `t["k"]`, `{["k"] = 1}` | `t.k`, `{k = 1}` (when the key is a Lua Name and not a reserved word) |
| negative numeral | `(-1)` everywhere | `-1`, parenthesised only where unary precedence demands (`(-1) ^ 2`, `(-1)[1]`) |
| unary `-` separator | always (`- x`) | only against a leading `-` (`- -x`), where `--` would start a comment |
| indentation | 2 spaces, **function bodies not indented at all** | 4 spaces uniformly, function bodies included |
| non-ASCII string constant | decimal escapes always (`"\227\128\144…"`) | raw UTF-8 when the bytes decode and re-encode identically, decimal escapes otherwise |
| same-operator `and`/`or` chain | `a and (b and c)` | `a and b and c` (`emit/lua.py::_ASSOCIATIVE`; **added M6 task 11 fix round 1**, not M5 task 7) |

The last row was missing from this table until the M6 final review found it —
it is a real seventh surface change and it had no entry here, in CLAUDE.md or
in `CHANGELOG.md`. Two things about it, both measured 2026-08-14:

- **On this corpus it is inert.** Neutering `_ASSOCIATIVE` to `frozenset()`
  and regenerating all 229 chunks changes **0 files**
  (`sha256(decompile_file(f).source)` identical for every one).
- **It is not unfalsifiable.** The same neuter fails
  `tests/test_emit_readability.py::test_associative_and_or_chains_are_flat` on
  synthetic input, and its byte-equivalence is proven against the real `luac`
  by `test_associative_and_or_chains_compile_identically` (6 pairs). So its
  evidence is *synthetic*, which is legitimate and is now labelled at the
  constant, exactly as this milestone labels its other narrow rules.

Two consequences worth knowing before reading a v2 file:

- A **hybrid** chunk's substituted subtree is emitted by
  `structure/fallback.py`, which is deliberately not beautified (CLAUDE.md:
  fallback 故意丑). Its lines keep their own column-0 baseline while the
  `end` that closes the substituted `function(...)` follows the enclosing
  indent. Measured after this task: every hybrid boundary in the corpus sits
  at indent 0, so the mismatch is currently invisible in the artifact.
- A v2 file can contain **raw multi-byte UTF-8** inside a double-quoted
  string. It is still a byte-exact representation of the original constant:
  `emit/lua.py::_str_lit` prints raw only when the bytes decode as strict
  UTF-8 **and** re-encode identically, and delegates to
  `structure/fallback.py::str_lit`'s decimal escapes otherwise. It is the one
  place that decodes a bytecode-derived string **whose result can reach the
  artifact as a value** — four other `decode(` calls exist
  (`emit/lua.py:157,190`, `structure/fallback.py:203,205`) and all four are
  ASCII identifier paths that only decide whether a name is spellable, never
  what the constant is. CLAUDE.md's scoped wording is the precise one; this
  bullet used to claim "the one place in this codebase that decodes", full
  stop, which a `grep -n "decode(" src/pyluadec/emit/lua.py
  src/pyluadec/structure/fallback.py` falsifies in one line. `_str_lit` is
  the whole of the scoped amendment recorded in CLAUDE.md's
  「工程红线」 section — `ingest`, `lift` and the comparison layer keep the
  absolute rule, and diagnostics still never carry corpus payload.

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
2. Chooses the shipped artifact, in three tiers (the third was added by M5
   task 6; see "Hybrid chunks" below):
   - **iff the root certified `L3`**, the exact bytes certification compiled
     and compared (`ProtoCert.source`, produced by `print_chunk` inside
     `certify_proto`);
   - else, iff `certify_hybrid` succeeds, the exact bytes *it* compiled and
     compared — structured code with the fallback state machine substituted at
     the CLOSURE sites that could not be certified;
   - else `structure.fallback.emit_chunk(root)`.

So the invariant is:

> Every proto in a shipped artifact is EITHER covered by the certification
> that compiled those exact bytes — its own fields compared to the original,
> field by field, through the real `luac_sz4` and the untouched normalization
> ladder — OR emitted by the semantically-exact fallback and confessed as
> such in the ledger. No unverified structured code is ever returned.

The M3/M4 form of that sentence ("the shipped source is structured **⟺** the
root proto certified `L3`") is the special case where the substitution set is
empty, and it is still what 216 of the 229 corpus files do.

`emit_certified_chunk` raises if `certs["main"].source is None` after the root
certifies, because a root that certified `L3` must by construction have printed
successfully. Note that the shipped bytes are *reused from* the certification,
not re-printed: an earlier revision called `print_chunk(root)` a second time
here, which made "shipped == certified" contingent on `print_chunk` being
deterministic (it is — re-measured 2026-08-12, **215/215** shipped artifacts
re-print identically; it was 92/92 at M3 close and 212/212 at M4 close — but that
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
Read the second one for what it is: both of its fixtures are roots with **no
subprotos**, so they have nothing to substitute and the whole-file fallback is
their only alternative. It pins "an uncertified print does not ship", not "the
whole file falls back" — those stopped being the same sentence when hybrid
emission landed, and the docstring saying otherwise survived until the M5
task-6 round-1 review. The hybrid form of the invariant is pinned by
`tests/test_hybrid_chunk.py::test_hybrid_shipping_invariant_holds` and the
`shipping_violations` fault-injection tests beside it.

### Hybrid chunks (M5 task 6)

`certify_hybrid(root, certs)` runs when the root misses `L3`. It is the same
gate, with the *scope of the claim* narrowed and nothing else touched.

**How the substitution set is chosen.** Two phases.

1. `_plan_substitutions` — printability, bottom-up. A proto that certified
   `L3` printed its whole subtree as part of that certification, so only the
   non-`L3` protos are probed, deepest-first, each with its already-substituted
   descendants in place. What refuses (`StructureError` / `ReconstructError` /
   `EmitError`) goes into the set, and a set member covers its whole subtree.
   The set is an **antichain**: when a refusing proto's ancestor also refuses,
   `_add_to_frontier` drops the descendant's entry. That is what makes
   `HybridCert.fallback_paths` readable as "the CLOSURE sites the printer left
   a hole at" — the printer never reaches a site inside an already substituted
   subtree, so a redundant entry names a hole that does not exist. Round 1 of
   this task did not prune; the artifact and the ledger closure were still
   right, and the invariant checker
   (`tests/test_hybrid_chunk.py::shipping_violations`, whose third check skips
   protos *below* the frontier) reported a false breach on the nested case.
   Nothing in the corpus nests today — all 8 substituted protos across the 6
   hybrids have zero subprotos — so the fixture is synthetic
   (`test_a_refusing_ancestor_replaces_its_refusing_descendant_in_the_frontier`).
2. `_hybrid_round` — print, compile with the real `luac_sz4`, and run the
   untouched `compare_protos` up the untouched ladder, discarding only the
   mismatches whose path falls **inside** a substituted subtree. A mismatch
   anywhere else grows the set and the round repeats (bounded by
   `_HYBRID_ROUNDS = 6`; the corpus needs at most 2). Three ways to give up,
   all of which ship the whole-file fallback instead: the root's own body does
   not print, the root's own fields are what differ, or a round would have to
   substitute a proto that certified `L3` on its own.

**What a successful `HybridCert` claims.** Every proto outside
`fallback_paths` compares equal to the original, field for field, at rung
`rung`. That includes the root's own `code` — and therefore the `CLOSURE`
instruction at each substituted site *and the `MOVE`/`GETUPVAL`
pseudo-instructions that follow it*. That is what makes the two obligations of
`structure.fallback.inline_function_parts` checkable rather than assumed:

- **one subproto slot** — the whole substituted subtree is emitted inside a
  single `function ... end` literal (its own nested functions become
  immediately-invoked `function(__pld_U) ... end` factories), so the parent's
  `Bx` operand and `subprotos` length are unchanged;
- **the same captures, in the same order** — the substituted function
  references the enclosing scope's *own* identifiers (no box protocol crosses
  the boundary, so Lua's upvalue mechanism supplies the aliasing), and a
  `local __pld_ord = {…}` prologue mentions them in upvalue-index order.
  `lparser.c` assigns upvalue indices at first mention and `pushclosure` emits
  the parent's pseudo-instruction sequence in that order, so without the
  prologue a pc-ordered state machine that touches upvalue 1 before upvalue 0
  would change the *parent's* `code`. `a = b` between two enclosing locals is
  the smallest case that does it (target parsed first, `GETUPVAL` emitted
  first); pinned by
  `tests/test_hybrid_chunk.py::test_dropping_the_upvalue_order_prologue_breaks_certification`.

**What it does not claim, and what covers that instead.** The substituted
subtrees. Certification structurally cannot bless them — they are not
byte-exact by construction — so the semantic evidence for the boundary comes
from running the code: the two standing probes
(`scripts/probe_global_state.py` L1.5, `scripts/probe_behaviour.py` L1.75) over
all 229 files, plus the differential-execution arm in
`tests/test_hybrid_chunk.py`. Both probes were unchanged by M5 task 6's hybrid
emission: 225/229 and 227/229 identical with the same 4 and 2 pinned
divergences (measured 2026-08-12, after that change — a dated snapshot, kept
because the claim it supports is about that change). **M6 task 12's
classification work then moved both**, in the direction the pins are supposed
to move: 228/229 and 228/229 with 1 pin each, four pins deleted as `gone`
(re-measured live 2026-08-14).

**How far the probes actually reach into the substituted code — measured, and
smaller than round 1 of this task claimed.** Injecting an unconditional
`error("PLD_SENTINEL")` at the entry of every substituted function (1, 1, 1, 1,
2, 2 sentinels across the six hybrids) and re-probing:

| probe | notices the sentinel | blind to it |
| --- | --- | --- |
| L1.5 global-state | **0 of 6** | all six |
| L1.75 behaviour | 4 of 6 | `snr_fragment_main.lua`, `snr_s5_10_s.lua` |

**`0 of 6` on L1.5 is not a corpus coincidence — it is close to structurally
unmovable, and this is not the same claim** (round 2 of this task's review;
the round-1 text above read like a measurement that could shift with a
different corpus or a different budget, and it cannot, for a reason internal
to the probe itself). `scripts/probe_global_state.lua` only `loadfile`s the
chunk and `pcall`s its top-level body once; it never enumerates or invokes the
globals that body *defines* (unlike `probe_behaviour.lua`'s invocation loop).
So L1.5 can only ever execute a hybrid's substituted code if that code runs
during the chunk's own top-level execution — never merely by being reachable
from a global the chunk leaves for its caller to invoke later, which is how
every one of the six hybrids' substituted functions is actually reached in
this corpus. Re-verified 2026-08-12 (round 2) by reading
`scripts/probe_global_state.lua` directly: no invocation loop is present.

`snr_fragment_main.lua`'s only global (`main`) errors after 12 recorded events,
and its substituted function is a chunk *local* called from another chunk
local; `snr_s5_10_s.lua` hits the 3000-event cap before the invocation loop
reaches the code that calls its two. **More budget does not fix the second
one, measured 2026-08-12 (round 2):** raising `MAX_EVENTS` from 3000 to
300000 in a scratch copy of `probe_behaviour.lua` and re-running it against
`snr_s5_10_s.lua`'s original bytecode produces `PROBE1|INSN|257070` — it now
stops on the 400M-instruction backstop (`INSN_BACKSTOP`) at 257070 recorded
events, short of even the raised 300000 cap, and still before the invocation
loop reaches the code that calls `main_42`/`main_43`. The earlier "hits the
3000-event cap" phrasing invites the inference that a bigger budget would
reach them; measured, it does not — the file's own top-level cost in VM
instructions outruns the backstop first. `snr_s5_10_s.lua` is also the single
file `test_corpus_hybrid_invariant_on_one_file` runs `shipping_violations`
over, so it is the least-covered of the six twice over. The committed fault
injection `test_a_broken_upvalue_write_at_the_boundary_diverges` is likewise a
**no-op on the corpus**: no substituted function performs a `SETUPVAL` through
a name slot, so all six artifacts stay byte-identical under that patch and
both probes stay green.

So: the probes gate the boundary on four files and say nothing about two. The
boundary's *mechanisms* — name-slot aliasing in both directions, the upvalue
order prologue, mixed box/name slots in a nested closure, per-iteration closures
and `OP_CLOSE` inside a substituted subtree — are covered by the synthetic
differential tests in `tests/test_hybrid_chunk.py`, which are the real evidence;
the corpus arm is a breadth check on top. The reach itself is pinned
two-directionally by `test_probe_reach_of_the_substituted_code`, so a future
hybrid landing in an unreached region fails rather than passing quietly.
Driving the two unreached files' substituted functions directly is not
available: both are chunk locals, and the original side is stripped bytecode
with no source to append a driver to.

**Measured rollout, 2026-08-12.** 216 files fully structured, **6 hybrid**,
**7 whole-file fallback** (was 216 / 0 / 13). Proto occurrences shipping
structured text: **1747/1944 (89.9%)**, was 1379/1944 (70.9%). Corpus
instruction volume shipping as a state machine: **14.2%** (30584/215218), was
34.4%. The 7 that remain are the files whose *root's own* reconstruction does
not certify, so there is no structured code to keep; see "Current capability
boundary".

### Per-proto, not per-chunk

Certification is per proto subtree, so one unstructurable function cannot
poison its siblings' *levels*. The level (a proof record, per proto) and the
artifact (per chunk, and since M5 task 6 per proto within a chunk) are
deliberately decoupled — `pipeline.decompile_chunk` returns both, as `levels`
and `shipped_fallback`.

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
rung 0; all 1430 of them are at rung 1.** That is not a slack ladder, it is
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

`express/freereg.py::stack_discipline`. This is M3's central analytical idea and
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

`_adjacent_pure` is gone, and nothing in `express/` reads `EffectMode` any
more — neither `names.py` nor the `freereg.py` it was split into so much as
imports it (checked 2026-08-13). `EffectMode` itself is alive in
`lift/effects.py`, where the lattice lives; it is simply no longer a knob on
register classification.

### What is there now

`lparser.c`'s `statement()` ends with `fs->freereg = fs->nactvar`: at every
statement boundary the expression stack is empty and only declared locals
occupy registers. So

> a definition is a temp iff its value is consumed before the end of the
> statement that produced it, and a local iff it survives one.

That is simulable straight from the bytecode without knowing `nactvar`, because
`freereg` after any value-producing instruction is its target register plus one.
`stack_discipline` keeps a `pending` stack of pushed-but-unconsumed values:

- a value producer targeting `a` pops every pending entry at or above `a`
  (exactly the operands it just consumed) and pushes its own results;
- a statement-ending instruction (`CALL` with `C==1`, `TAILCALL`, `RETURN`,
  `SETGLOBAL`, `SETUPVAL`, `FORPREP`, `CLOSE`, `FORLOOP`, `TFORLOOP`, or a
  write whose target is already a known local) pops its own operands and then
  **promotes everything still pending to local** — surviving a statement
  boundary is the definition of being one. (`CLOSE`/`FORLOOP`/`TFORLOOP` share
  one arm in `express/freereg.py::stack_discipline`, the
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
pinned by a fixture that fails when it is neutered. **What each one is worth
was measured barrier by barrier in M5 task 11 (2026-08-13, corrected in its
round 1)** — each neutered alone, in the real source, with the full suite run
and `corpus/ledger.jsonl` regenerated each time:

| barrier | corpus protos reclassified | ledger | full-suite failures |
| --- | --- | --- | --- |
| 1 `_same_block` | 28 / 1944 | **moves**, 9 lines (5 rows `L1`→`L3`, 1 `L3`→`L1`) | 7 |
| 2 RK/literal | **0 / 1944** | unchanged | 7 |
| 3 `MOVE d, s` | 3 / 1944 | **moves**, 2 lines (2 rows `L3`→`L1`) | 6 |
| 4 read-poison blame | 3 / 1944 | **moves**, 2 lines (no level change) | 2 |

Two things to take from it. **Barrier 2 is the one the corpus cannot see**:
neutering it — the whole literal test, and separately its RK C-slot arm alone
— reclassifies zero corpus protos and leaves the ledger byte-identical, so its
entire evidence is synthetic fixtures (`tests/test_express_liverange.py::
LOCAL_CASES[5]`, `[8]`, `[9]` and three in `test_express_reconstruct.py`). And
**barrier 4's pin is not where this section used to send a reader**: with it
neutered all 126 tests in the five `tests/test_express_*.py` modules still
pass, and the two failures are
`tests/test_sir_loops_longtail.py::test_repeat_fixture_claims_every_pc_and_certifies[6]`
and `tests/test_ledger_ratchet.py::test_ledger_is_a_reproducible_fixed_point`.
Barriers 1–3 are pinned in `tests/test_express_liverange.py` as this section
originally said of all four. Full failing-test-id sets are in that task's
report.

(An earlier revision of this paragraph, and of the code comment on barrier 4,
said barrier 4 was the *only* one whose absence moves the ledger. That was
never measured and the table above is its refutation — three of the four move
it. Recorded rather than silently deleted, per this file's own rule about
carried-forward claims.)

Since M5 task 11 the three state-independent barriers are module-level
functions in `express/freereg.py` under this same heading (`_same_block`,
and `_bar_literal_operands` carrying both 2 and 3). Barrier 4 stays as two
lines inside `stack_discipline`'s `do_read`, marked there — a judgement, not
an impossibility: it could be a function taking `last_def` and `mark_def`,
and two lines behind a call with two pieces of walk state threaded through to
reach them is indirection with no second reader.

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

Documented in `express/freereg.py::stack_discipline`, under the comment
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

216 of the 229 files have an `L3` root and therefore ship real structured source
(92 at M3 close, 212 at M4 close, 215 after M5 task 4).

### Run the whole-corpus gate and regenerate the ledger

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run python scripts/run_corpus.py
```

A clean run prints `compiled 229/229` plus the structured/L3 breakdown. It
rewrites `corpus/ledger.jsonl` (committed) and `build/decompiled/*.lua` (not
committed). Never hand-edit the ledger; `tests/test_ledger_ratchet.py` requires
a fresh run to reproduce it byte for byte.

Since M5 task 8 it also prints a `ledger key:` line **before** the rest, and
**refuses to write the ledger** if that check fails — see "The ledger's
grouping key" below. Current output on this corpus:

```
ledger key: 16/1478 shash group(s) carry >1 debug fingerprint (462 fingerprints between them); 0 disagree on (level, rung, reason)
compiled 229/229; ledger: 1478 unique protos (1944 occurrences)
structured 1904/1944 protos (97.9%); L3 1438/1478 unique (97.3%)
shipped: 1763/1944 protos structured (90.7%); 217 files fully structured, 8 hybrid, 4 whole-file fallback
L2: 1/5 authored file(s) granted; 2/1478 row(s) carry the badge (13 sequence(s) over 5/229 files)
```

(Re-measured 2026-08-14 after M6 task 12. The `L2:` line is newer than the
M5-close transcript this block used to show.)

### Read the dashboard

```bash
uv run python scripts/ledger_dashboard.py            # or --markdown
```

Current output (M6 task 12): 1478 unique protos / 1944 occurrences / 229
files, `compile_ok 1478/1478`, `level L3 1438`, `level L1 40`, L3 share 97.3%
unique / 97.9% occurrences, `L3 rung 1: 1438`, `ladder l3-ladder-v1`. (After
M6 task 11 it was `level L3 1437` / `level L1 41`; at M5 task 5
`level L3 1430` / `level L1 48`, 96.8% / 97.5%; after M5 task 4
`level L3 1403` / `level L1 75`, 94.9% / 96.1%; at M4 close
`level L3 1389` / `level L1 89`, 94.0% / 95.4%; at M3 close
`level L3 1112` / `level L1 366`, 75.2% / 81.1%.)

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
PYLUADEC_CORPUS_DIR=<corpus> PYLUADEC_PRED_CORPUS_DIR=<pred> uv run pytest   # 1087 tests; 52.73 / 56.18 / 56.83s over three runs on macOS 15.2 / Apple M4 (2026-08-14, M6 final-review fix round; the M6 wrap measured 1077 tests at 55.07-55.61s over three runs, and the same tree measured 57.90s just before this round -- the suite drifts upward within a session and has 1-2s of run-to-run spread, so do not compare single runs across sessions). Ceiling is a ~120s EARMARK for formal-verification instruments, not a general relaxation -- see CLAUDE.md. Without PYLUADEC_PRED_CORPUS_DIR 32 tests SKIP (test_cross_corpus.py 22, test_loss_sweep.py 8, test_predcorpus.py 2) and the run still exits 0 -- which is why scripts/ratchet_job.sh now requires the variable.
                                                        # Ordering is UNMEASURED, not "not a factor": no randomiser is installed, so `-p no:randomly` is a no-op and no M5 A/B ever varied the order. See m3-backlog.md, M6 agenda 6.
PYLUADEC_CORPUS_DIR=<corpus> uv run pytest tests/test_effects_emitter_consistency.py -v
```

Without `PYLUADEC_CORPUS_DIR` the corpus-gated tests **skip**, including the M2
and M3 exit gates. `tests/conftest.py` prints a red banner in that case; heed
it (see CLAUDE.md).

`tests/test_generated_semantic_cases.py` (M4 task 5) only runs
`DEFAULT_LIMIT` (3) of its `CASE_COUNT` (24) deterministic differential-
execution cases by default, to keep the standing suite inside its speed
budget. **The full sweep is a ratchet-job gate, not a manual command any
more** (M5 task 8) — `scripts/ratchet_job.sh` runs it, and the standalone form
stays available:

```bash
PYLUADEC_GENERATED_CASE_LIMIT=24 uv run pytest tests/test_generated_semantic_cases.py -v
```

Measured on macOS arm64: the full 24 cases run in **under 3 seconds**, against
**~0.3s** for the standing 3 — so the fold-in costs the ratchet ~2s and the
per-commit suite nothing. (The history of this one number is a small lesson.
It was "~1.7s" measured 2026-08-11, which did not reproduce; then a
single-figure "2.48s" quoted for two rounds; then "2.29–2.54s over 5 runs",
which the very next three runs fell below. Thirteen runs across this task span
**2.21–2.54s**. A range tight enough for a routine run to falsify is not more
honest than an order of magnitude, just wider, so the standing claim is the
ceiling. Why it grew was not investigated — five M5 tasks landed in between and
attributing it without measuring would be a guess.)

### Ratchet the ledger against a baseline (M5 task 8)

```bash
PYLUADEC_CORPUS_DIR=<corpus> ./scripts/ratchet_job.sh [BASELINE_REF]
```

Three gates: the full suite (which contains `tests/test_ledger_ratchet.py`,
i.e. the proof that `corpus/ledger.jsonl` is a byte-exact fixed point of
`scripts/run_corpus.py`), the baseline diff, and the full 24-case generated
sweep. `BASELINE_REF` defaults to `0957364`, the last merged milestone tip
(the M5 merge; the default was moved forward from `eb08890`, the M4 merge, at
the M6 wrap -- see that line's comment in `ratchet_job.sh`). Measured
end-to-end 2026-08-14 on the M6 wrap tree, 1077 tests: **57.9-58.2s** (37.9s on
2026-08-12 at 867 tests, before the ceiling was raised to a ~120s earmark).

The diff on its own:

```bash
git show 0957364:corpus/ledger.jsonl > /tmp/baseline.jsonl
uv run python scripts/ratchet_diff.py /tmp/baseline.jsonl corpus/ledger.jsonl
```

It exits **1** on any per-row `level` downgrade, `l3_level` rung downgrade
(remember a HIGHER rung is a WEAKER proof — rung k means `NORMALIZATIONS[:k]`
were applied before comparing), removed row, **occurrence that is no longer
walked** while its row survives, `L3` row carrying a `refusal_reason`,
per-occurrence `shipped` going `structured` → `fallback`, or row arriving at
`L0`; and **0** on upgrades, added rows and fields the *baseline* lacks.
Offending rows print grouped by `refusal_reason` cluster, which is what M4
added that field for: a regression that reads "12 rows, all `structure: … back
edge`" names the recognizer that broke.

**Exit codes are not free choices — see the next section for the contract.**
`125` means *this tree cannot be judged* (the ledger under test is missing,
unreadable, malformed, or carries duplicate `shash` rows) and makes `git bisect
run` **skip**; `128` means *the instrument is misconfigured* (wrong arguments,
or a baseline that is itself unusable) and makes `git bisect run` **abort**.
Round 1 of this task removed exit **2**, which the previous revision advertised
as "not a verdict": it is one, see below.

Two directions of schema tolerance, which are not symmetric. Fields the
**baseline** lacks are tolerated per-row and per-field, so an older ledger
stays diffable on what it does carry; fields the **new** ledger has dropped are
not. Measured 2026-08-12 by dropping one field from every row of the committed
ledger: `level` → 1478 `level-downgrade`s, `l3_level` → 1430 `rung-downgrade`s,
`refusal_reason` → 0, per-occurrence `shipped` → 0. The first two are
fail-safe; the last two fail open and are covered only by the printed schema
note.

Two real diffs, run 2026-08-12 at this commit:

| baseline | result |
| --- | --- |
| `eb08890` (M4 merged tip) | 1478 common, 0 removed/added, **41 upgraded, 0 downgraded**, L3 1389 → 1430; two schema notes (`shipped`, `hybrid` are newer than the baseline) |
| `bbe74f6` (M4 branch point / M3 tip) | 1478 common, 0 removed/added, **318 upgraded, 0 downgraded**, L3 1112 → 1430; three schema notes (plus `refusal_reason`) |

**Why this exists, and what it makes safe.** Before it, nothing compared the
committed ledger against a committed *historical* baseline: a regenerated
ledger with fewer `L3` rows passed the whole suite as long as the rate stayed
above the exit floor and no `L0` appeared. It also makes the deliberately
slack floors safe rather than merely defensible — `tests/test_sir_while.py`'s
census floor is measured-minus-10 and `tests/test_m4_exit.py`'s is points below
what is achieved, on the argument that a floor set at the measurement is a
tripwire. Both gaps are the same gap, and this closes it: floors catch
catastrophes without churning, the baseline diff catches the one-row
regression that stays inside them.

**Non-vacuity.** `tests/test_ratchet_diff.py` (43 tests: 37 at M5 task 8's close, plus 6 that
task 9 added for the `l2-lost` and `l2-coverage-downgrade` kinds) feeds hand-mutated
copies of the real committed ledger, one named case per failure mode, and
asserts a non-zero exit that names the offending row. Verified by mutation
three times, and **the mutation pass found something it had missed on each of
the last two rounds** — which is the honest summary, not "every check was
neutered":

- M5 task 8: each of the seven diff checks neutered in turn, exactly its own
  test(s) red.
- Round 1: repeating the pass over round 1's own additions found the exit-code
  tests were written against the *symbols* `EXIT_UNTESTABLE` / `EXIT_BROKEN`,
  so reverting both constants to the old, wrong value of 2 left all 24 tests
  green. Pinned by
  `test_the_exit_codes_are_literally_the_ones_git_treats_as_non_verdicts`.
- Round 2: the pass had **not** been run over round 1's `load_rows` guards.
  Two were unpinned, and one was load-bearing: deleting `isinstance(row, dict)`
  left the whole 664-test suite green while a ledger line of `5` raised
  `AttributeError` out of `load_rows`, past `main`'s `(OSError, ValueError)`
  handler, to a traceback and **exit 1 — a bad-commit verdict from an
  instrument fault**, i.e. round 1's own finding 2 reintroduced by round 1's
  fix for it. Now pinned by a parametrised case per guard.
- Round 3: the guards were pinned but the **prose about them was not
  measured**. Round 2's docstring argued `level` needed no check because an
  unknown one "ranks -1"; true of `3`, `None`, `"L9"` and `True`, false of
  `["L3"]` and `{"a": 1}` — `LEVEL_RANK.get` is a dict lookup, so those raise
  `TypeError` and exited **128 (abort)** where the contract says 125. Three of
  the eight committed "what happens if you delete this guard" strings also
  described the realistic hazard rather than the fixture they annotated. Both
  are corrected against measurement, and one provably dead conditional
  (`if os_ is None or ns is None`) was deleted rather than left as decoration.

The pattern across the three rounds is the same one every time: **the check
was real and the sentence about it was not**. Assume the next such sentence is
also unmeasured until someone runs it.

The standing claim is therefore the weaker, true one: neutering any one check
turns at least one named case red, and only cases belonging to that check.

### The `git bisect run` predicate

The predicate must survive checkouts of commits that predate `ratchet_diff.py`
itself, so **copy the script and the baseline out of the tree first**:

```bash
cp scripts/ratchet_diff.py /tmp/rd.py
cp corpus/ledger.jsonl     /tmp/baseline.jsonl      # or: git show <ref>:corpus/ledger.jsonl
export PYLUADEC_CORPUS_DIR=<corpus>

git bisect start <bad> <good>
git bisect run sh -c '
  rm -f corpus/ledger.jsonl
  uv run python scripts/run_corpus.py >/dev/null
  test -s corpus/ledger.jsonl || { git checkout -- corpus/ledger.jsonl; exit 125; }
  uv run python /tmp/rd.py /tmp/baseline.jsonl corpus/ledger.jsonl
  rc=$?
  git checkout -- corpus/ledger.jsonl
  exit $rc'
```

Each probe **regenerates** the ledger rather than reading the committed one:
at an arbitrary bisected commit the committed file is not known to be current,
and it is the code under test that must produce the verdict. The
`git checkout --` restores the ledger so the next checkout finds a clean tree.
Nothing else `run_corpus` writes is tracked (`build/decompiled/` is
gitignored). Only stdout is discarded, so any `COMPILE FAIL <file>` lines stay
in the bisect log.

**Why the skip test is "was a ledger produced", not "did `run_corpus` exit 0".**
`scripts/run_corpus.py` returns `0 if n_ok == len(files) else 1` — it returns
**1 when a file failed to compile, *after* writing a complete ledger whose rows
say `L0`.** The predicate this task originally documented was
`… run_corpus.py … || exit 125`, which mapped that to **skip**, so the loudest
regression class the ratchet exists for — a decompiler change whose output no
longer compiles, surfacing as `new-l0` and level downgrades to `L0` — was
silently unbisectable. (M5 task 8's original verification injected a
`StructureError`, which falls back and still compiles, so it never touched this
path.) `rm -f` plus `test -s` asks the question that actually matters: a
commit that could not produce a ledger at all cannot judge the ratchet, and one
that produced a ledger full of `L0` rows is exactly the commit being hunted.
`ratchet_diff.py`'s own 125/128 flow through the final `exit $rc`.

**Two things this shape does that are worth knowing before you run it.** First,
`run_corpus.py` has a *second* path that exits 1 without writing a ledger —
`key_disagreements` finding a `structural_hash` group with more than one
verdict, printing `LEDGER KEY UNSOUND` — and the predicate maps that to
**skip**, not bad. That is defensible (a run that refused to write a ledger
genuinely cannot judge the ratchet, and gate 1 of `scripts/ratchet_job.sh`
covers the invariant), but it is a real class of commit the bisect will step
over, so it is stated rather than left to be discovered. Second, `rm -f`
deletes a **tracked** file: a probe interrupted between the `rm -f` and the
`git checkout --` leaves your working tree missing `corpus/ledger.jsonl`. It is
one `git checkout -- corpus/ledger.jsonl` away from clean, but check for it
before blaming the next thing that reads the ledger.

**Exit codes: the measured contract.** `git-bisect(1)` (git 2.39.5 on this
host) says the script *"should exit with code 0 if the current source code is
good/old, and exit with a code between 1 and 127 (inclusive), except 125, if
the current source code is bad/new. Any other exit code will abort the bisect
process. The special exit code 125 should be used when the current source code
cannot be tested."* **Exit 2 is therefore BAD, identically to 1** — the claim
that it was "not a verdict" was wrong wherever it appeared, and is corrected in
`scripts/ratchet_diff.py`, its tests, the backlog and CLAUDE.md. Measured on a
six-commit scratch repo:

| predicate | `git bisect run` says |
| --- | --- |
| `exit 2` everywhere | "b07bfbd … is the first bad commit" — **an innocent commit blamed, silently** |
| `exit 125` everywhere | "There are only 'skip'ped commits left to test. … We cannot bisect more!" |
| `exit 128` everywhere | "error: bisect run failed: exit code 128 … is < 0 or >= 128" |

So `ratchet_diff.py` now returns **125** when the *tree's* ledger is unusable
and **128** when the *instrument* is (usage, unreadable baseline, or an
internal error in the diff itself — the last because an uncaught exception
would otherwise exit 1 and read as "bad").

**Verified 2026-08-12 (round 1) against a real COMPILE regression** — the case
the old predicate skipped. Scratch branch off the round-1 commit: two empty
commits, then one changing a single `end` to `edn` in the fallback emitter's
`OP_TEST` tail (`structure/fallback.py`), then one more empty commit. The
injection has to be in the **fallback** emitter, not the structured one: a
structured emitter that produces uncompilable Lua simply fails to certify and
falls back, so the chunk still compiles — measured, an equivalent typo in
`emit/lua.py`'s `if` header left `compiled 229/229` and only dropped L3 from
96.8% to 53.9%. The fallback emitter is the floor and has no certification gate
above it, which is exactly why an `L0` can only come from there.

| | result |
| --- | --- |
| `run_corpus.py` at the injected commit | **exit 1**, `compiled 222/229`, 7 `COMPILE FAIL` lines, and a **complete ledger containing 188 `L0` rows** |
| **old** predicate (`… \|\| exit 125`) at that same commit | **exit 125 = SKIP** — the regression was unbisectable |
| **new** predicate, full `git bisect run` over the 4 commits | found the injecting commit as *"the first bad commit"* in **22s / 2 probes**, reporting 191 regressions (188 `level-downgrade`, all `L3 -> L0` with `refusal_reason` `compile: shipped chunk did not compile`, plus 3 `shipping-regression`), with the `COMPILE FAIL <file>` lines visible in the bisect log |

Scratch branch deleted; `git diff 3a7528a..HEAD` touches no `src/` file.

### CI: there is none, and this task did not invent one

There is **no CI runner configuration in this repository** — no
`.github/workflows/`, no `.gitlab-ci.yml`, no CI YAML anywhere (checked
2026-08-12, M5 task 8). Every gate this project has is a command someone runs.
The ratchet is therefore `scripts/ratchet_job.sh`, documented above, and the
right time to run it is at a milestone wrap and before any merge that touches
`corpus/ledger.jsonl`. If a runner is ever added, that script is the job body;
adding one was deliberately out of scope rather than forgotten.

## Condition trees: `and`/`or` in an `if` (M6 task 11)

`regions.If.cond` used to be one compare instruction. That is enough for
`if a then`, and it is enough for `if a and b then f() end` -- which compiles
to the SAME bytecode as `if a then if b then f() end end`, so the nested
reading is a correct reading. It is not enough the moment the `if` has an
`else`: `luaK_patchtohere` sends both conjuncts' false-exits to the else
block, while the nested reading would send the inner one to the end of the
outer then-block, skipping the else entirely. `or` had no nested reading at
all -- `luaK_goiffalse` patches its truelist to the START of the then-block,
so the first compare's jump goes FORWARD over the second condition.

`If.cond` is now `LirInstr | CondNode`, where `CondNode` is `CondTest`
(a leaf: conditionally-evaluated `staging`, the test, its JMP pc, and the
polarity bit) or `CondOp` (`"and"`/`"or"` over two subtrees). Single-test
`if`s are untouched and still carry a bare `LirInstr` -- which is why this
change moved no existing row.

### How the tree is recovered

`lcode.c` compiles a boolean expression into a chain of test+JMP pairs with
two pending-jump lists (`luaK_infix`/`luaK_posfix`, lcode.c:684-736):

* `X and Y` -- `luaK_goiftrue(X)` puts X's own jump on the FALSElist and
  patches X's truelist to *here*, the start of Y's code;
* `X or Y` -- `luaK_goiffalse(X)` puts X's jump on the TRUElist and patches
  X's falselist to *here*.

`ifstat` then runs `luaK_goiftrue` over the whole expression, so the LAST
test's jump is always the false exit, the falselist is patched to the else
block (or the join), and the truelist to the start of the then-block.

Reading that backwards is `sir/build.py::_parse_cond`. The information the
instruction stream does NOT carry is which list each jump landed on -- `EQ A=1`
is `x == y` compiled for an `or` and `x ~= y` compiled for an `and`,
identically encoded -- and it is recovered from the jump's TARGET: a jump to
the true-target set is a truelist jump, one to the false target is a falselist
jump, and one landing on a later span's start is the "patched to here"
boundary between an `and`/`or`'s two operands, which is what makes grouping
(`(a or b) and c` vs `a or (b and c)`) recoverable. The polarity bit is then
folded into `Reconstructor.condition_expr`'s existing A/C-field reading via
its `jump_is_true_exit=` keyword, rather than wrapped in a second `not` --
`not (not (x == y))` compiles identically (two `invertjump`s cancel) but is
nobody's source.

The true-target set has two members, not one: the pc after the chain's last
JMP, and -- when a JMP sits at that pc -- that JMP's own target, because
`luaK_jump` concatenates the pending truelist onto it instead of flushing it.
`snr_common.lua:main_81` is the corpus instance: its then-block is a `break`,
so the `and`'s true-exit at pc 15 carries 26, the loop exit, while the chain
falls through to 19.

### Dispatch order, and why it is not a preference

`_structure_if` tries the incumbent ONE-compare reading FIRST and only
consults `_match_cond_chain` when that raises `StructureError`. The interval
arithmetic cannot distinguish `if a and b then` from
`if a then x = 1 if b then ... end end` -- same two tests, same two targets,
differing only in whether the instructions BETWEEN the tests are operand
staging or a statement, which `sir.build` has no register model to decide
(`Reconstructor._stage_run` decides it, one layer down, after the region tree
is fixed). Trying the chain first would therefore guess on exactly the shapes
where guessing is wrong. Re-measured 2026-08-14 at the M6 final review, on
this tree: inverting the order regenerates the ledger at `L3` **1433**/1478
unique / **1899**/1944 occurrences instead of **1438**/1478 / **1904**/1944 --
five protos downgraded. (The anchors here read 1432 vs 1437, task 11's totals;
the delta of five is the load-bearing part and it reproduces exactly.)

### The predecessor's structure reference, as a by-product

M6 Task 9's Step 1 asks how often `build_sir` accepts the PREDECESSOR
project's corresponding proto (its decompiled Lua source, recompiled with the
oracle and lifted). Loaded with
`predcorpus.load_pred_proto(pred_dir, name, strip=not carries_debug(original))`
-- the `strip=` argument is load-bearing; the default would manufacture an
`upvalues`-length mismatch on all 260 `nups > 0` protos.

Over the 13 compound-`if` leaves, measured 2026-08-14:

| tree | rate | failures |
| --- | --- | --- |
| `5961ea2` (before this task) | 6/13 (46.2%) | 6 × `if targets out of range`, 1 × `unrecognized transfer JMP` |
| `76a09e8` (after) | **12/13 (92.3%)** | 1 × `unrecognized transfer JMP` (`snr_common.lua:main_76_2` pc 63) |

The pre-task figure is **confounded**: six of its seven failures are the very
compound-`if` defect this section closes, so 46.2% measured the recognizer,
not the predecessor. **92.3% is the figure to reason from** — and the decision
it feeds (whether an LLM meta-reconstruction pass over the predecessor's
structure is worth commissioning) should also weigh that 8 of these 13 protos
are `ui-keyloop` shapes, five of which are among the six predecessor defects
this milestone confirmed. A high mechanical acceptance rate on the
predecessor's output is not the same thing as its structure being right.

### What it does not cover

`while <a and b> do` is a NAMED gap, pinned by
`tests/test_sir_condtree.py::WHILE_HEADER_GAP`. `_match_while_header` requires
the header to be ONE basic block ("nothing jumps into the middle of the
condition code"), which a two-test chain is not, and extending it means
reshaping `regions.While`'s `header`/`cond` split as well. No corpus proto
needs it. `repeat ... until a and b` certifies (the incumbent bottom-test
reading already describes it); `repeat ... until a or b` does not, and is
pinned in the same list -- the split is measured, not smoothed over.

## Constructor field stores and captured registers (M6 task 12)

Two independent defects in `classify_registers`, both reached through the same
downstream amplifier: `Reconstructor.write_reg`'s `reg not in self.declared`
gate. Once one definition of a register is materialized as a `local`, every
later definition of that register becomes a *reassignment* — so a single
misclassified definition does not merely cost one statement, it can silently
alias every later value written into the slot.

### 1. A field store is not a read of the table

`stack_discipline`'s pop-once rule grades a staged definition a temporary iff
its value is read exactly once before the statement ends. It already knew that
`SETTABLE`/`SETLIST` do not *free* the table (`pop_ge(a + 1)`, "the table
itself stays pending") but still counted their read of it, so a constructor
with N fields scored N + 1 reads and was graded a **local**.

The sources are unambiguous, and the two field forms restore `freereg` in two
different files — a reader given only the `lparser.c` pointer will not find the
`SETLIST` half at all:

| field form | emits | restores `freereg` |
| --- | --- | --- |
| hash (`{k = v}`, `{[e] = v}`) | `lparser.c::recfield`, `vendor/lua-5.1/src/lparser.c:443` | `fs->freereg = reg;` at `lparser.c:460` |
| array (`{a, b, c}`) | `lparser.c::closelistfield` `:464` / `lastlistfield` `:475`, which delegate to `luaK_setlist` (`lcode.c:819`) | `fs->freereg = base + 1;` at **`lcode.c:829`** |

Either way the table's own slot survives the store: the value stays on the
expression stack until whatever the literal is an operand of takes it.
`freereg._constructor_field_target` is the read half of that sentence.

(Round-1 correction: this section and `freereg.py` first cited
`lparser.c:596`/`:632`, which are inside `explist1` and `funcargs`. The
substance was right and the pointers were wrong, which at the axiom layer is
the difference between a fix and a coincidence.)

Two faces, both one-line reproductions (`tests/test_express_aliasing.py`):

* `f({x = 1})` printed `local l0_1 = {x = 1} f(l0_1)` — one stack slot more
  than luac used (`mismatch: maxstacksize`).
* `local t = {a = {..}, b = {..}}` printed `local l0_1 = {..}`,
  `l0_1 = {..}`, `local l0_0 = {a = l0_1, b = l0_1}` — **both fields aliased
  to the last table**. This is a different program, not an unfaithful
  rendering: `t.a.x` reads 3 where the original reads 1. `snr_graphic.lua:main`
  had eight tables collapsed into one (`code` 385 → 650); M5 adjudicated the
  same shape at `snr_music.lua:main`.

The discriminator is the pending definition's own opcode — only a slot whose
most recent push was `OP_NEWTABLE` gets the exemption — **plus a constant
key**, because `_dispatch` folds only `isk(ri.b)` and `_fold_settable` has no
register-key form. A dynamic-key constructor (`{[f()] = 1, [g()] = 2}`) is
materialized and emitted as one `t[k] = v` statement per field, each of which
reads the table for real; exempting those reads made `config.lua` raise
`register 0 is read again after its staged value was consumed` and stop
printing entirely. That was measured while the rule was being written, and it
is pinned by a neuter test rather than left as a comment.

### 2. `captured_regs` is a union, and was read as a whole-function fact

`lift.LirFunction.captured_regs` is the union over every `CLOSURE` in the
function of the slots its `MOVE` pseudo-instructions capture. `names.py` seeded
all of them as named locals for the whole function, which says "slot 7 holds a
live local everywhere" on the strength of one `function() ... end` near the
end of the chunk. A capture proves only that the slot held a live local **at
the `CLOSURE`'s pc**.

`snr_graphic.lua:main` is the measured worst case: **five** `CLOSURE`s at pcs
356, 358, 359, 366 and 372 capture registers 0–13, which made every definition
of registers 0–13
across the whole 385-instruction chunk a named local — including the eight
nested table constructors in slot 1 at pcs **2, 19, 28, 39, 41, 43, 45, 47**,
and hence defect 1's aliasing
on top. (Re-measured 2026-08-14: this said "four `CLOSURE`s" and "pcs 2–45";
there are five `CLOSURE`s, referencing five distinct subprotos, and the last
constructor is at 47.)

The refinement is per definition and is the weakest one that keeps the
capture's own guarantee: a definition is a captured local iff it is the **last
definition of that register at or before some capturing `CLOSURE`**, i.e. iff
the value it writes is the one that closure captures. Everything else in the
slot goes back to the freereg simulation. Population: **6 of 1944** protos
have a captured register with definitions no closure captures — but they
include `snr_graphic.lua:main`, `snr_memory.lua:main` and
`snr_mainmenu.lua:main`, so the shipping effect is out of all proportion to
the count (whole-file fallback 7 → 4, hybrid 5 → 8).

A register `captured_regs` names but `closure_pseudo` cannot attribute to a pc
stays whole-function seeded. That is empty for anything `lift_proto` produces
and non-empty for hand-built `LirFunction`s, which is exactly what
`tests/test_express_names.py::test_parameters_and_captured_registers_win_over_the_controls_override`
constructs — it failed without the fallback, so the fallback is load-bearing,
not decorative.

### What is left, attributed rather than narrated

**The M7 campaign census (2026-08-16, post task 10): 22 non-`L3` rows — 15 own
refusals + 7 inherited ancestors — every one attributed below.** The campaign
(Tasks 6–10) took the population from 40 (M6 close) to 22, measured row by row
from each task's committed ledger: task 6's dynamic-key constructor fold (−1),
task 7's skipped-kill clamp veto (−4: three own rows plus their inherited
root), task 8's staging-span exemption (−2), task 9's reaching-definition `>`
recogniser (−3) and hint-0 constructor budget gate (−2), task 10's
key-staged-below-table barrier (−4: two own rows plus two inherited roots,
flipping `snr_s3_10_s` and `snr_s4_10_s` whole-file structured) and
NEWTABLE-position lookahead (−1, `snr_common:main_29`). `L3` stands at
**1456/1478 unique (98.5%), 1922/1944 occurrences (98.9%)**; 222 of 229 files
ship fully structured, 5 hybrid, 2 whole-file fallback, and 1880/1944
occurrences (96.7%) ship structured text.

The clusters, each with its first-divergence evidence (all re-measured
2026-08-16 with the runbook's canonical wrapper recipe; `orig` is the corpus
bytecode, `cand` our recompiled print):

| cluster | rows (own) | + inherited | mechanism |
| --- | --- | --- | --- |
| K1 | 5 | — | constructor hint ≥ 1: the fold's deliberately ungated half |
| C | 1 | 1 | constant-pool interning order (`const[70..73]`) |
| J | 1 | — | jump-ladder spelling: candidate +13 instructions, first divergence a `JMP` target |
| M | 5 | 3 | materialization surplus: extra `local`s the original never had (`+code`, `+maxstacksize`) |
| R | 2 | 2 | `and`/`or` empty alternative re-reads a consumed temp |
| X | 1 | 1 | `while true` + `break` not recognized (`pc 286`) |

**Closed at task 10** (the spec §5 stop-loss re-scope, ruled with the human
partner 2026-08-16): cluster **O** — the register-key staging order — by the
`_bar_key_staged_below_table` barrier in `express/freereg.py`: a register-keyed
`GETTABLE`/`SETTABLE` whose key's pending definition PREDATES its table
operand's was never an inline `t[k]`, because stock 5.1.5 discharges the table
prefix before parsing the key on every parse route; the barrier grades the key
local, the reconstructor materializes it where the original declared it.
`snr_s3_10_s:main_59`/`snr_s4_10_s:main_58` + both roots certified. And
cluster **K2** — the hint-0 close position — by a NEWTABLE-side lookahead: a
hint-0 `NEWTABLE` whose first toucher is a `SETTABLE` into its register
materializes `local t = {}` at the `NEWTABLE` itself instead of at the first
store, restoring the declaration position the original wrote (the open-region
test in the scan is precise — `reg < base` means the open instruction does not
touch the register; `snr_common:main_29` needed exactly that, its first store
sits inside a `for` body past a `VARARG`/open `CALL` based above the table's
slot). One K2 row, `snr_common:main_77_25`, had certified already at task 9's
gate.

**K1 — the hint ≥ 1 half of the constructor budget (5 own rows).** The task-9
budget gate fires only on a decoded hash hint of 0, because every non-zero
hint is an `int2fb` bucketed lower bound that cannot be compared against a
field count exactly (see `_close_table_ctx`). The rows where that deliberate
gap is the whole story: `snr_common:main_24` (`NEWTABLE 0 0 1` vs `0 0 3` — a
one-field seed literal plus statement stores, folded into a three-field
literal), `main_25` (`0 0 2` vs `0 0 3`, same), `main_77` (pc 1: orig
`NEWTABLE 0 0 1` vs cand `LOADK 0 -1` — the literal placed after a constant
load), and the two whole-file fallback roots `snr_novel:main` (hint 7,
maxstacksize 17→18) and `snr_music:main` (hint 4, maxstacksize 24→28; the
M6 case study below documents this chunk's fold history). Closing these needs
an exact hint arithmetic under `int2fb` decoding, which the encoding does not
admit — the attribution *is* the disposition.

**C — constant-pool order (1 own + 1 inherited).** `snr_story_main:main_3`
and its root: `const[70]`–`const[73]` mismatch plus jump distances shifted by
the reinterning (`JMP 77` vs `JMP 85` at pc 290, 461 vs 469 instructions).
Same attribution as the task-8 census: the candidate interns two constants in
the opposite order from the original (`fileName`/`sysgim`), and every index
after the swap moves. The closed `L3.2` rung (below) is the standing decision
not to canonicalize pools.

**J — jump-ladder spelling (1 own).** `snr_graphic:main_4`: candidate is 13
instructions longer (769 vs 782), first divergence a `JMP` target at pc 355.
Task 9's `>` fix certified this row's clamp gate (its M6 twin
`snr_memory:main_4` went `L3`), and what remains is the ladder around it —
the shape pinned as `WHILE_HEADER_GAP` in `tests/test_sir_condtree.py`
(`while <a and b>` headers are not yet representable as compound conditions)
plus the elseif-vs-nested-if spelling each unrecognized rung of the ladder
pays for. No separate defect claim is made: this is the compound-condition
residual, measured as a length difference.

**M — materialization surplus (5 own + 3 inherited).**
`snr_mainmenu:main_7` (+4 instructions, maxstacksize 12→13),
`snr_common:main_25_4` (90 vs 104 instructions, maxstacksize 8→10, first
divergence `MOVE 4 0` vs `MOVE 4 2`), `main_76_2` (174 vs 180, 9→11),
`main_74_18` (first divergence `GETGLOBAL 1 -1` vs `GETGLOBAL 0 -1` — a
register-numbering shift from one extra live local, maxstacksize 9→8 the
other way), and `main_77_0` (pc 3: `SETUPVAL 1 1` vs `SETUPVAL 1 0`, a
register-index shift in the upvalue write). All five are the `declared`-gate
family the M6 census called mechanisms B/D/E: a definition the walk grades
local where the original had an expression-stack temp (or vice versa), so our
print carries one `local` too many and every register above it shifts. The
inherited companions are the roots `mainmenu:main` (`at root/7`),
`common:main_74` (`at root/18`) and `common:main_76` (`at root/2`).

**R — the `and`/`or` empty-alternative re-read (2 own + 2 inherited).**
`snr_memory:main_3` and `snr_graphic:main_3`, plus their roots, refuse at
`reconstruct: register 7 is read again after its staged value was consumed`.
Reproduced directly while re-deriving this census (the repro *is* the
diagnosis): `_print_proto_body` raises in `_value_run`'s empty-run arm —
`return self._read_reg(reg)` — i.e. one alternative of the short-circuit
chain contributes no instructions (`lcode.c:discharge2reg` emits nothing when
the operand already sits in the destination), so its value is the register's
*incoming* one, which an earlier alternative already popped. This is the
documented `x = <cond> and 9 or x` shape (`_value_run`'s own docstring cites
`snr_graphic.lua:main_3` pc 39 for exactly this) meeting the per-definition
`_consumed` guard: the pc-linear classifier has no control-flow model, so it
cannot see that two alternatives read *different* definitions of the slot.
The clamp-family veto (task 7) closed the `TESTSET`-based three rows of this
family; these two need the empty-alternative half, which is region work, not
classification work.

**X — the `while true` + `break` gap (1 own + 1 inherited).**
`snr_common:main_71` (`structure: pc 286: else-join out of range`) and its
root. Unchanged from the M6 census: the tests at pc 284/286 are a nested
`if`/`else`, and what actually refuses is the `break` at pc 295 targeting 410,
the exit of a `while true` (header 279) that `_match_loop` does not
recognize. Re-verified 2026-08-14: `_structure_if(284, break_target=410)`
succeeds, `_match_loop(279)` returns `None`.

**The campaign's closed mechanisms** (each with its own commit and tests, so
only the row arithmetic lives here): task 6's dynamic-key constructor fold
closed `config.lua`'s whole-file fallback (mechanism G's statement-store
half); task 7's `_merge_veto_skipped_kill` closed all three `reconstruct:`
clamp rows (the M6 census's "fourth mechanism" — `snr_common:main_69`,
`snr_s5_10_s:main_42/43` and their inherited roots, plus the two rows the
M6 text below still describes in its then-current state); task 8's
`_staging_span_ok` closed the `_same_block` rows for `snr_graphic:main_2`
and `snr_memory:main_2`; task 9's reaching-definition `_is_stack_temp`
disjunct closed the `>` recogniser's three rows (`snr_novel:main_2`,
`snr_novel:main_3`, `snr_memory:main_4` — the M6 clamp-twin of
`snr_graphic:main_4`) and the hint-0 budget gate closed
`snr_s1_10_s:main_48` and its root, flipping that file fully structured;
task 10 closed clusters O and K2 (above). The
M6-era
subsections below are kept as the measurement history of mechanisms three,
four and five — their row counts are as of their own dates, not current.

### History: the M6-era attribution that the campaign closed from

*Measured 2026-08-14; superseded by the census above on every row it
names. Kept because the neuter-experiment methodology and the per-mechanism
arguments are still the reference for re-deriving any of these clusters.*

40 non-`L3` shapes stood at the M6 close. The `declared` gate was shown to
be **at least three mechanisms**, of which M6 task 12 closed two. The
third, `_same_block`, refused to stage a value whose consumer sits in
another basic block — `g(a and 1 or 2)` printed
`local l0_0 = g  local l0_1 = a and 1 or 2  l0_0(l0_1)` and failed on
`maxstacksize`; `snr_common.lua:main_76_2` was the exemplar. Neutering
`_same_block` to a tautology and re-certifying the population moved **6 of
the 40** (`snr_graphic:main_2`, `snr_memory:main_2`, `snr_novel:main_2`,
`snr_novel:main_3`, `snr_story_main:main_3` and its root) — a real mechanism,
not the dominant one. The staging-span exemption (task 8) later closed the
first two of those six.

The `reconstruct: register N is read again` family was five rows then — two
inherited ancestors and three own refusals, all one clamp shape:

```
250 SUB      R7 = R7 - R2      <- graded TEMP (its one read is the LT below)
251 LT       0 R7 K            <- reads R7
252 JMP      -> 254
253 LOADK    R7 = K1           <- graded LOCAL (the RK/literal barrier)
...
257 SETTABLE R8[K] = R7        <- reads R7 AFTER THE JOIN
```

Two individually defensible verdicts over **two arms of one conditional
value**: the `SUB` really is read once before the branch, the `LOADK` really
is disqualified by the literal barrier, and at pc 257 the register holds
either. The reconstructor staged the `SUB`, the `LT` popped it, and the
post-join read hit `_read_reg`'s `_consumed` refusal. Task 7's
`_merge_veto_skipped_kill` — when the kill a staging veto skipped is itself
skipped by a later arm, the veto is withdrawn — closed all five rows. What
remains of this family today is the empty-alternative half (cluster R above),
a different arm of the same no-control-flow limitation.

### `snr_music.lua:main` — the M5 diagnosis was right, and is now closed

The task brief named it as a third instance of the constructor-aliasing
family, from M5's adjudication. That diagnosis **survives**, and M6 task 12
closed it. Measured 2026-08-14 by printing the chunk at BASE and at HEAD and
recompiling both:

| | BASE | HEAD | original |
| --- | --- | --- | --- |
| `code` length | 107 | **99** | 99 |
| `maxstacksize` | 29 | 27 | 24 |
| first differing pc | 2 | 1 | — |

At BASE the printed source opens `local l0_1 = {…}` / `l0_1 = {…}` /
`l0_1 = {…}` — four constructors collapsed into slot 1, exactly as M5 said. At
HEAD they fold into one literal (`local l0_0 = {layerName = {…},
musicTitle = {…}, …}`) and the instruction count is exactly right.

What was left then was a **fifth mechanism, and a consequence of closing the
first**: the outer constructor's context was held open longer, so the
`local` for the table was emitted after three later scalar `local`s and every
register shifted by three (24 → 27 is exactly those three slots).
Instrumented directly — the reg-0 context opens at pc 1 in both, and closes:

* at BASE while dispatching **pc 81** (`LOADBOOL` into register 1), because the
  inner tables had been materialized into register 1 and folding them left
  `LocalExpr(1)` items in the context's `hazard` set;
* at HEAD while dispatching **pc 84** (the `CLOSURE` that reads register 0),
  because the inner tables now fold as nested `TableExpr`s and `hazard` is
  **empty**.

So a fold that removes a hazard also removes the thing that used to close the
context at the right place. The row is still non-`L3` today — as cluster K1
(maxstacksize 24 → 28 with the hint-4 literal), the deliberately ungated
half of the constructor budget.

## Ledger fields added in M3

`corpus/ledger.jsonl`, one row per unique `structural_hash`.

| field | meaning |
| --- | --- |
| `level` | `"L3"` (recompiled and matched under the ladder) or `"L1"` (compiles, unverified). `"L0"` means it did not even compile and must never appear. |
| `l3_level` | the ladder rung that passed, for `L3` rows; `null` otherwise. Currently always `1`. |
| `fallback` | **Redefined in M5 task 6**: true iff at least one *occurrence* of this proto shape shipped as the fallback state machine. It used to be `level != "L3"`, which was the same predicate only while a chunk was all-structured or all-fallback. |
| `confessions` | exactly one whole-range `fallback-state-machine` confession iff `fallback`, empty otherwise — in both directions. |
| `occurrences[].shipped` | **New in M5 task 6.** `"structured"` or `"fallback"`: which emitter produced *this* occurrence's text in `build/decompiled/<file>.lua`. The exact, per-occurrence form of `fallback`. |
| `occurrences[].hybrid` | **New in M5 task 6.** Did the chunk this occurrence lives in ship as a hybrid? A per-chunk fact, recorded on the occurrence because that is where the chunk identity (`file`) lives. |
| `occurrences[].l2` | **New in M5 task 9.** `{"cov": 0.xx}` when this occurrence's FILE passed the L2 differential-execution gate, `{"refused": <kind>}` when it has an authored key sequence and did not, `null` when it has no sequence. |
| `l2` | **New in M5 task 9.** The row-level aggregate, `verify.ledger.row_l2`: `{"cov": min}` iff *every* occurrence is granted, `null` otherwise. Never measured independently. |

**`level` and `shipped` answer different questions and no longer agree.**
`level` is the proof record for the proto *in isolation* (its whole subtree,
via `certify_proto`), unchanged by how its neighbours ship. `shipped` is a fact
about the artifact. Since hybrid emission both disagreements occur on this
corpus: 6 rows are `L1` and ship structured (their own fields were compared
exactly by `certify_hybrid`; only their substituted descendants were not), and
150 rows are `L3` and ship fallback (they live in one of the 7 files that still
falls back whole). Read a row as: *this shape certifies at `level`; these
occurrences of it actually shipped as `shipped`.*
| `ladder` | `LADDER_VERSION` at generation time (`l3-ladder-v1`). |
| `oracle` | `git log -1 -- vendor native` — the oracle build's provenance, **not** repo HEAD. See `decompile-pipeline.md` for why. |

**Ratchet discipline: levels only ever go up, confessions only ever come off.**
That is the *discipline*. Be precise about how much of it a machine checks —
re-read of the assertions, 2026-08-11:

**Asserted** (restated for the M5 task 6 schema).
`tests/test_m3_exit.py::test_l3_entries_carry_a_rung_and_no_confessions`:
`L3` ⇒ non-null `l3_level` and null `refusal_reason`.
`::test_non_l3_entries_confess`: non-`L3` ⇒ null `l3_level` and a non-empty
`refusal_reason`; and, over **every** row, `fallback` ⇔ the whole-range
`fallback-state-machine` confession is present ⇔ some occurrence's `shipped` is
`"fallback"`. So a confession dropped without the shipping changing, shipping
changed without the confession being dropped, or a row-level aggregate drifting
from its per-occurrence record all fail the suite. What this pair *stopped*
asserting is `L3 ⇒ fallback is False`, which the redefinition of `fallback`
makes false in fact: 150 `L3` rows ship as state-machine text inside the 7
whole-file-fallback files, and demanding `confessions == []` for them would
have been the confession hole in the direction that matters. Also asserted: no `L0` and
`compile_ok` everywhere (`test_ledger_ratchet.py`, `test_m3_exit.py`), `shash`
sortedness and uniqueness, full-corpus coverage at exactly 1944 occurrences,
byte-identical regeneration from `run_corpus.py`
(`::test_ledger_is_a_reproducible_fixed_point`), and the `> 0.50` exit
fractions on both bases.

**Cross-revision monotonicity — asserted since M5 task 8, by an instrument
rather than by the suite.** It used to be the standing exception: nothing
compared the ledger against any historical baseline, so a ledger regenerated
with *fewer* `L3` rows and committed passed every test above as long as the
rate stayed over the floor and no `L0` appeared — each row would still be
internally consistent, which is all the coupling tests look at. That is now
`scripts/ratchet_diff.py` (spec §5's complete form: baseline diff, downgrade =
fail, `git bisect run` predicate), documented under "Ratchet the ledger against
a baseline" above.

Be precise about what changed and what did not. The **suite** still does not
diff against a baseline, and deliberately so: a baseline is a *ref*, not a
fixture, and pinning one inside `pytest` would either freeze it at one
milestone or re-derive it from `git` on every run. The check lives in
`scripts/ratchet_job.sh`, which is run at a wrap and before any merge that
touches the ledger. What the suite gained is the guarantee that the instrument
works: `tests/test_ratchet_diff.py` (43 tests, no corpus needed) is the
non-vacuity proof.

### The ledger's grouping key — pinned, not split (M5 task 8)

`corpus/ledger.jsonl` is keyed on `structural_hash` **alone**, and
`scripts/run_corpus.py::main()` takes the higher level (its `_RANK`
comparison) when one hash occurs more than once. That key is *not* sufficient
to imply an equal verdict, and the codebase says so elsewhere:
`structure.structured._memo_key` keys the certification memo on
`(structural_hash, _debug_fingerprint)` precisely because `structural_hash`
drops `source`, `linedefined`/`lastlinedefined`, `lineinfo`, `locvars` and
upvalue names — every one of which `verify.normalize.compare_protos` checks.
So "one hash, one verdict" was an assumption the ledger generator **made and
did not check**.

Measured 2026-08-12 (M5 task 8; the M4 figures reproduced exactly):

- **16 of the 1478 shash groups carry more than one debug fingerprint**,
  holding **462** fingerprints between them — 446 more than one each.
- **0 groups disagree on `(level, rung, refusal_reason)`.** The max-by-rank is
  vacuous on this corpus.
- Splitting the key to `(shash, dfp)` would take the ledger from **1478 rows
  to 1924**, all 446 additions being duplicate verdicts.

**The decision was to pin, not split, and the ledger did not move.**
`run_corpus.py::key_disagreements` evaluates the invariant over every
occurrence and `main()` **refuses to write a ledger that violates it**, so the
assumption is now checked once per regeneration instead of being trusted. The
figures above print on every run (`ledger key:` line). Splitting would have
landed 446 duplicate rows in the same commit as the instrument that diffs the
ledger *by row identity* — the first baseline diff would have read as 1478
removed + 1924 added, which is exactly the unreadable one-off movement the
agenda item wanted avoided.

What is pinned is the **certification** verdict from `decompile_chunk`, which
is what `_memo_key` claims is a function of `(shash, dfp)`. What is *not*
pinned is the compile-adjusted level the ledger stores (`level if compile_ok
else "L0"`): two occurrences of one shape can legitimately differ there,
because whether the whole *chunk* compiled is a property of the file, and that
case is already handled by `_force_l0` AND-ing `compile_ok` across the group.

**If `key_disagreements` ever returns non-empty, the fix is to split the
key** — a disagreement means two protos with equal code shape and unequal
debug fields certified differently, which is the case `_debug_fingerprint`
exists for. Non-vacuity:
`tests/test_ledger_ratchet.py::test_key_disagreement_check_actually_rejects_a_split_group`
covers a level, a rung and a reason disagreement separately.

## Current capability boundary — measured, not estimated

All figures over the 229-file corpus: 1478 unique proto shapes, 1944
occurrences.

| stage | unique | occurrences |
| --- | --- | --- |
| `build_sir` accepts the proto's own body | 1477 (99.9%) | 1943 (99.9%) |
| whole subtree prints (proto **and** every descendant) | 1472 (99.6%) | 1938 (99.7%) |
| certifies `L3` | **1456 (98.5%)** | **1922 (98.9%)** |

(Re-measured 2026-08-16 after M7 task 10. The M6-close figures were 1477 /
1472 / 1438 (97.3%, 1904 occurrences): the whole M7 campaign — tasks 6–10 —
moved the third row only, because none of its fixes changes what `build_sir`
accepts or what prints; the row's per-task path 1438 → 1439 → 1443 → 1445 →
1450 → 1456 is measured in each task's committed ledger.)

**The command, because rows 1 and 2 have never named one and row 2 is easy to
get wrong** (added in task 12 round 1, after a reviewer's reasonable predicate
produced 1240/1678 for row 2 and the figure could not be checked):

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run python - <<'PY'
import json, os
from pathlib import Path
from collections import defaultdict
from pyluadec.ingest import load_file
from pyluadec.lift import lift_proto
from pyluadec.pipeline import walk_proto_paths
from pyluadec.sir.build import build_sir, StructureError
from pyluadec.emit.lua import _print_proto_body
from pyluadec.express.reconstruct import ReconstructError
from pyluadec.verify.ledger import structural_hash

C = Path(os.environ["PYLUADEC_CORPUS_DIR"])
sir_ok, body_ok, occ = {}, {}, defaultdict(int)
for f in sorted(C.glob("*.lua")):
    tree = {}
    walk_proto_paths("main", load_file(f), tree)
    for path, p in tree.items():
        h = structural_hash(p)
        occ[h] += 1
        try:
            build_sir(lift_proto(p)); a = True
        except StructureError:
            a = False
        try:
            _print_proto_body(p, depth=1,
                              upval_names=tuple(f"u{i}" for i in range(p.nups)))
            b = True
        except (StructureError, ReconstructError):
            b = False
        sir_ok[h] = sir_ok.get(h, True) and a
        body_ok[h] = body_ok.get(h, True) and b
rows = [json.loads(l) for l in open("corpus/ledger.jsonl")]
l3 = {r["shash"] for r in rows if r["level"] == "L3"}
tot = lambda d: (sum(1 for h, v in d.items() if v),
                 sum(occ[h] for h, v in d.items() if v))
print("row 1", tot(sir_ok))
print("row 2", tot(body_ok))
print("row 3", (len(l3), sum(occ[h] for h in l3)))
PY
```

Two details are load-bearing and neither is guessable from the table:

1. **The unit is the unique `structural_hash`, folded with AND over every
   occurrence** — a shape counts only if *every* occurrence of it succeeds.
   Counting occurrences independently and de-duplicating afterwards gives a
   different, larger number.
2. **Row 2's predicate is `_print_proto_body` with synthetic upvalue names,
   not `print_chunk`.** `print_chunk` treats whatever it is handed as a chunk
   ROOT, and a chunk root has no upvalue names, so it refuses (returns
   `None`) for any proto that reads one. Substituting it gives **1240/1678**.
   Measured 2026-08-14: of the **260** occurrences where `_print_proto_body`
   succeeds and `print_chunk` does not, **all 260 have `nups >= 1`** and none
   has `nups == 0` — the whole gap is the upvalue-naming artifact, not a
   printing failure.

Three different numbers, three different causes. M4 tasks 3 and 4 moved the
top two rows and did not move the third at all; **task 13 moved only the
third**, from 1139/1604 to 1389/1855, by making register classification per
definition rather than per register number. **M5 task 4** moved all three, by
unwinding two more `jpc` absorbers and admitting the dead code luac emits
unconditionally (details in point 1), to 1465 / 1447 / 1403. **M5 task 5**
moved the bottom two rows to the figures above, in three clusters, none of
them a `build_sir` change (the top row is untouched): a `for` statement's
slots are now released at its `end` (cluster 1), a generic `for` over a call
prints one iterator expression instead of three materialized locals
(cluster 2), and `>`/`>=` are recovered instead of being normalised to
`<`/`<=` (cluster 3). All three are detailed in point 3 below. **M5 tasks 6–12
moved none of the three rows**, deliberately: task 6 changed how chunks are
assembled rather than what certifies, and tasks 7–12 were surface, gates and
documents. **M6 task 11** moved all three again, by giving `regions.If` a
condition TREE: the `structure:` refusal family went from 21 ledger shapes to
**1**, of which 7 reached `L3` outright and 13 moved down into row 3 (they
print now, and fail on `code`/`maxstacksize`). Net `+7` unique `L3`, `0`
downgrades against the M5 merge baseline `0957364`. **M6 task 12** moved it
once more, by `+1` unique / `+1` occurrence — a small number that badly
understates the change, because its real effect is on the *shipping* counts
below, not on the level census. See "Constructor field stores and captured
registers" below for both mechanisms.

**Artifact counts, re-measured 2026-08-14 (M6 task 12) — and note they are no
longer a single number.** **217** of the 229 files ship **fully** structured
source (92 at M3 close, 212 at M4 close, 215 after M5 task 4, 216 after task 5,
217 after M6 task 11, unchanged by task 12); a further **8 ship hybrid**
(structured with fallback holes at the `CLOSURE` sites that would not certify;
6 before task 11, 5 after it, 8 after task 12) and **4 ship the whole-file M2
fallback** (7 before task 12, 13 before M5 task 6, 17 at M4 close). Per
occurrence, **1763 of 1944 (90.7%) ship structured text** (1749 after task 11).
The corpus quality average is **0.977328** (0.935633 at M4 close, 0.946390
after M5 task 4, 0.950580 after task 5, 0.968833 after task 6, 0.971947 after
M6 task 11). Full evaluation, including the five volume bases that disagree
with each other by a factor of six, in `docs/reports/m5-quality.md` — whose
per-file numbers predate task 11.

Task 12 is the clearest case so far of the level census and the artifact
counts answering different questions: `+1` row at `L3`, but three of the
corpus's largest chunks moved from whole-file fallback to **hybrid**, so a
large fraction of each stopped going through the `__pld_R` state machine.
**Not all of it** — "reduced", not "stopped", and the difference is what
round 1 of this task's review had to correct in five places. Box-model lines,
measured 2026-08-14 across the change:

| file | `__pld_R` lines before | after |
| --- | --- | --- |
| `snr_graphic.lua` | 1862 / 2411 | **1324 / 1849** |
| `snr_memory.lua` | 1225 / 1673 | **1038 / 1469** |
| `snr_mainmenu.lua` | 3220 / 4782 | **1974 / 3325** |

None of the three `main`s certifies `L3` (`snr_mainmenu.lua:main` is `L1`,
`mismatch: code at root/7`), and `snr_mainmenu.lua:main_7` is `L1` with
`shipped: "fallback"` — 18 of that file's surviving box-model lines are the
very `["library"]` lines its probe pins were about. `quality_score.py` scores
the three at 0.51 / 0.45 / 0.57, which is the same story on a different base.

**The two fixes are jointly, not separately, responsible.** Measured by a
source-level four-way ablation over all 229 files (checking out BASE/HEAD
`names.py` and `freereg.py` independently and hashing
`decompile_file(...).source`): the constructor-read fix alone and the
closure-capture fix alone each produce output **byte-identical to BASE for
every one of the 229 files**; only both together change anything, and they
change exactly these three. On the *ledger* the split is different again —
the constructor fix alone accounts for the whole `+1` `L3`
(`snr_mainmenu.lua:main_2`) while shipping not one byte differently, and the
capture fix alone moves neither. Level and artifact really are two questions.

Three pinned probe divergences converged as a consequence. Deleting them was
forced by the instruments, not chosen: `probe_common.adjudicate_pins` reports
a converged pin as `gone`, each CLI returns 1 on it and each gate asserts it
empty. Deleted: `snr_graphic`/`snr_memory`/`snr_mainmenu` in
`probe_global_state.py`, `snr_mainmenu` in `probe_behaviour.py`, and
`snr_mainmenu.lua:main_7` in `probe_enum.py` — leaving one pin in each of the
first two and one in the third.

Task 11 moved exactly one file out of each of the first two buckets'
neighbours: `snr_fragment_main.lua` went hybrid -> fully structured, and
`snr_story_main.lua` stayed hybrid with its substituted frontier halved (2
functions -> 1).

1. **1478 → 1477: `build_sir` refuses 1 unique proto** (169 before M4 task
   3, 43 after it, 31 after task 4, 13 after M5 task 4, 1 after M6 task 11).

   The 13 that M5 close left here were all one defect — a compound `if`
   condition (`a and b`, `a or b`) on an `if` that HAS an else branch —
   and **M6 task 11 closed it** with the condition TREE this paragraph used
   to ask for; see "Condition trees" below for the recognizer.

   The survivor is `snr_common.lua:main_71`, `structure: pc 286: else-join
   out of range`, and it is **not** a condition defect. Measured 2026-08-14:
   the two tests at pc 284/286 target 297 and 298, which resolve to neither a
   true exit, a false exit, nor an internal split point, so
   `_match_cond_chain` declines them — correctly; they are a nested `if` with
   an `else`. What refuses is the `break` at pc 295 targeting 410, the exit
   of a `while true` (header 279, closing JMP 409) that `_match_loop` does
   not recognize. Structuring the same `if` WITH `break_target=410` succeeds;
   the refusal that escapes comes from a later attempt made without one.

   What M5 task 4 removed from this list, all of it one mechanism —
   `luaK_jump` concatenating `fs->jpc` onto whatever JMP is emitted next
   (lcode.c:59-66), which `_structure_if` already unwound for loop closings
   via `continue_target`:

   * the enclosing `if`'s **else-skip** absorbing a nested false-exit or
     else-skip (`if a then if b then f() end else h() end`) — the new
     `thread_target` parameter; this was the whole 11-proto `else-join` cluster
     and 3 of the 9 `if targets` leaves;
   * a `break` absorbing it (`if c then x() else break end`, `breakstat`,
     lparser.c:975-988) — `_match_else_break`, which cannot use a
     single-number rewrite because the join is `P+1` for a `P` that has to be
     recovered from the layout and validated by structuring;
   * `branch body block ... is unreachable` (10 protos) is gone entirely:
     `ifstat` emits the else-skip and `retstat` the RETURN-after-TAILCALL
     unconditionally, so both are dead whenever the arm ends in
     `break`/`return`, and `_is_dead_else_skip` now admits exactly those two
     shapes. The M4-era claim that "luac emits no dead code in if/for bodies"
     was false.

   `unrecognized transfer TESTSET` had already gone in M4 task 4, when
   `_match_cond_value` claimed the `and`/`or` VALUE idiom as a `CondValue`
   region.
2. **1477 → 1472: 5 more unique protos build a region tree but do not
   print.** `print_chunk` inlines the whole tree at each `CLOSURE` site, so
   one unstructurable inner function takes its entire ancestor chain with it.
   All 5 carry a `reconstruct:` reason (re-measured 2026-08-14; the paragraph
   below is the M5-close census of a list that was 26 protos then).

   The cleanest cut is over all **26** protos whose subtree does not print
   (1944 − 1918 occurrences, and 1478 − 1452 unique — every residual shape
   occurs exactly once on this corpus). Re-measured 2026-08-12 after M5
   task 5, by asking of each non-printing proto whether every DESCENDANT
   prints: **15 fail in their own body** (12 `structure: if targets out of
   range`/`else-join out of range`, 3 `reconstruct: register N is read again
   after its staged value was consumed`) and **11 fail only because a
   descendant does**. That is a different partition from point 1's 13, which
   counts `build_sir` refusals on the proto's own body regardless of what its
   descendants do; the two overlap in 12 protos. (Was 139 before M4 task 3,
   23 after task 13, 18 after M5 task 4.)

   M5 task 5 removed three kinds of entry from this list, all by fixing the
   reconstruction rather than the region builder: `while-header code
   reconstructs to N statement(s)` (2 protos), `and/or operand code
   reconstructs to N statement(s)` (2 protos) and `and/or alternative
   reconstructs to N statement(s)` (1 proto) no longer appear anywhere in the
   census.

   **That is a statement about this list only — not all five protos were
   released.** Re-measured 2026-08-12 (fix round 1, F5), proto by proto:
   `snr_lib.lua:main` and `:main_1` (the `and/or operand` pair) and
   `snr_novel.lua:main_13` (the `while-header` leaf) reached `L3`; the other
   two **migrated to point 3's list and are still `L1`** —
   `snr_story_main.lua:main_3` (`and/or alternative`) and `snr_novel.lua:main`
   (the ancestor that had been carrying `main_13`'s while-header confession)
   both now print and both now fail with `mismatch: code`. The ledger diff
   shows this: 27 rows moved `L1` → `L3`, and neither of those two is among
   them.

   The while-header one was `snr_novel.lua:main_13`, and M5 task 4 had
   already measured that it is **not a `While` defect**: its header is a
   single `GETUPVAL` whose definition `classify_registers` correctly grades a
   temp, and what materialised it was `Reconstructor.write_reg`'s
   `reg not in self.declared` gate firing on register 1, declared 35
   instructions earlier. Bisected across this task's three commits
   2026-08-12, the fix that released it is **cluster 2, not cluster 1**: what
   declared register 1 was the `CALL 0 2 4` at pc 26 staging the iterator
   triple for the `TFORLOOP` at pc 35, which `_emit_multi` used to
   materialize as `local l1_0, l1_1, l1_2 = ...`. Once that stages, register
   1 is never `declared` and the header's `GETUPVAL` stages cleanly. Pinned
   by `tests/test_sir_longtail2.py::test_while_header_refusal_is_a_
   reconstructor_scope_defect_not_a_while_defect`.
3. **1472 → 1438: 34 unique protos print but do not certify.** Was 22 at M5
   close; M6 task 11 moved 13 protos INTO this bucket out of point 1, which
   is an advance in diagnosis rather than a regression — they used to refuse
   before printing and now print and fail comparison. Re-derived straight off
   the committed ledger 2026-08-14 (M6 final review; this read "1472 → 1437:
   35" with a breakdown of 17/14/4, which was the post-task-11 state):
   **14 `mismatch: code`, 11 `mismatch: maxstacksize`, and 9
   `mismatch: <field> at root/<n>`** — 3 `maxstacksize at root/2`, 1 each of
   `maxstacksize at root/18`, `code at root/3`, `code at root/7`,
   `code at root/48`, `code at root/58`, `code at root/59` — the last group
   being ancestors whose own fields match and whose named descendant's do not.
   The whole non-`L3` set is 34 `mismatch` + 5 `reconstruct` + 1 `structure`
   = 40 rows.

   **None of the 13 fails inside a condition tree.** Measured 2026-08-14 for
   all thirteen: the first *opcode* divergence between the original and the
   recompile lies outside every `cond_claimed(...)` pc set, 13 times out of 13.
   So the arrivals are a pre-existing reconstruction defect that the structure
   refusal had been masking, not damage done by the new recognizer.

   `snr_common.lua:main_76_2` (174 instructions, the smallest **leaf** among
   them -- `snr_story_main.lua:main` at 10 instructions is the smallest of the
   13 outright, but its mismatch is a descendant's) is the exemplar for the
   *stack-inflation* form: the first opcode divergence is at pc 43, inside a
   plain `if/else`, where `Reconstructor.write_reg`'s
   `reg not in self.declared` gate materialises a staged temp as a `local`
   re-assignment (`local l1_3 = systemSave` ... `l1_3 = systemSave`) and the
   recompile grows extra slots and `MOVE`s.

   **That is one form of the family, not the whole of it, and the magnitude
   varies by an order of magnitude** (fix round 1 correction -- an earlier
   version of this paragraph said `maxstacksize` and `code` were "the two
   faces of the same thing", which is true of `main_76_2` and false of the
   worst case).

   **`snr_graphic.lua:main` was the other end, and task 12 CLOSED it. This
   paragraph described it in the present tense until the M6 final review;
   what follows is the historical description, then the measurement.** As of
   M5 close its root printed `code` **385 -> 650**, `maxstacksize` **20 ->
   24**, first opcode divergence at **pc 1** (`NEWTABLE 0 0 8` vs `NEWTABLE 0
   0 15`), and the printed source was **semantically wrong** rather than
   merely fat -- line 1 declared
   `local l0_1 = {...15 entries...}`, line 2 *reassigned* `l0_1 = {...7
   entries...}`, and line 17's `local l0_0 = {layerName = l0_1, layerNumber =
   l0_1, ...}` therefore pointed every field at the last table written. Eight
   distinct constructors collapsed into one alias (eight, not four -- the
   count agrees with this file's two other statements of it; measured
   2026-08-14, `NEWTABLE` into register 1 at pcs **2, 19, 28, 39, 41, 43, 45,
   47**).

   **Measured 2026-08-14 on this tree**: `certify_proto(main,
   is_chunk_root=True)` gives `L1` with `reason = "mismatch: maxstacksize at
   root/2"` -- the ROOT itself now matches (`code` 385, `maxstacksize` 20,
   both equal), and the surviving mismatches are all in descendants
   (`root/2` `maxstacksize` + `code`, `root/3` `maxstacksize` + `code`,
   `root/4` `code`). The aliasing form of the family is gone here; the stack-
   inflation form is what is left. Certification refuses it either way, which
   is the whole point of the gate.

   The paragraph below is the M5-close analysis of the same bucket. This was the
   dominant gap until M4 task 13 (283 protos, of which 253 differed from the
   original by extra `MOVE` instructions and by nothing else at all). The
   cause was `RegClass`'s whole-function, per-register-*number* verdict, and
   the measured exemplar was `snr_crd_10.lua:main_2`: registers 0/1/2 are
   call-argument temps in its first six instructions and declared locals in
   the same slots before its `while` loop, `classify_registers` had to give
   one verdict, picked `local`, and the first six instructions came back with
   `MOVE`s. Task 13 made classification per definition and that cluster went
   from 253 to **4**; M5 task 5 took the remainder from 44 to 22, in three
   clusters, all of them in `express`:

   * **A `for` statement owns its slots only for its own extent.**
     `lparser.c`'s `fornum`/`forlist` `new_localvar` the control triple and
     the visible variables and wrap the body in `enterblock`/`leaveblock`;
     `leaveblock` restores `fs->freereg = fs->nactvar`, so at the loop's `end`
     slots `a..a+3+n` go straight back to the expression stack. Two places
     modelled that as a whole-FUNCTION property. `classify_registers` now
     asks per pc, against a `[_window_floor(i), max(control_pcs)]` window per
     loop occurrence; and `Reconstructor` no longer seeds loop variables into
     `declared` for the whole function — `emit.lua`'s `NumericFor`/
     `GenericFor` arms call the new `declare_loop_vars` inside the
     `open_scope`/`close_scope` pair around the body. Before the fix, a write
     into a released slot printed as `l0_3 = 60`, a bare assignment to a name
     that is out of scope, which Lua compiles as a write to a GLOBAL. **+12
     unique.**
   * **A generic `for` over a call is one expression, not three.**
     `forlist` `adjust_assign`s the header's `explist1` to exactly 3 values,
     so `for k, v in pairs(t) do` is `CALL a b 4` into the control triple.
     `_emit_multi` had no `Expr` node meaning "the second value of `f()`" and
     materialized all three. The new `MultiSpill(base)` node fills the two
     spill slots and is deliberately unprintable, so a spill that escapes the
     `GenericFor` arm refuses rather than emitting something wrong. **+3
     unique.**
   * **`>`/`>=` are not `<`/`<=` with the operands swapped.** `codecomp`
     (lcode.c:673-686) compiles `a > b` by evaluating `a` then `b` and then
     exchanging the operands to emit `OP_LT`, so `x < y` and `y > x` are the
     same instruction and always printing `<` is a guess. Operands are
     evaluated left to right (`luaK_infix`'s default arm interns `e1` through
     `luaK_exp2RK` before `e2` is parsed), so the one evaluated first sits in
     the lower register and, if constant, carries the lower pool index —
     which is what `Reconstructor._reads_as_gt` reads. Two operand shapes are
     **deliberately undecidable** and stay in the `<` reading: a constant in
     field C (`x < 5` and `5 > x` are indistinguishable once `5` is already
     pooled), and a register operand that is a live **local** rather than an
     expression-stack temporary — `luaK_exp2RK` on a `VLOCAL` returns the
     declaration slot and pushes nothing, so its register number is not an
     evaluation-order witness at all (fix round 1, Important 2; the
     both-registers arm is gated on `rc.temps`/`rc.temp_defs` for exactly
     this reason). Both gaps are free: a bare local contributes no code and
     no constants, so both readings compile identically. Measured
     2026-08-12: 43 static `B > C` both-register sites, only 3 of them
     `(temp, temp)`; 20 firings while printing, 4 `(temp, temp)`; gating the
     arm moved the corpus `L3` count by **0** and left `corpus/ledger.jsonl`
     byte-identical. **+12 unique**, and it
     is what the `L3.2` rung had twice been proposed for; see the next
     section. **This is the class the M4-era "cluster B, constant-table
     ordering" label was pointing at, and it was a defect, not a
     normalization problem.**

   The **22 that remain**, re-measured 2026-08-12 after the three clusters
   (by `refusal_reason`; 11 `mismatch: maxstacksize`, 11 `mismatch: code`):

   * **17 are leaf defects and 5 are poisoned ancestors** (cut by asking of
     each non-`L3` proto whether every DESCENDANT certifies).
   * The dominant remaining shape, sampled at `snr_novel.lua:main_2`,
     `snr_graphic.lua:main_2` and `snr_common.lua:main_25_4`, is what is left
     of task 13's cluster: registers the classifier grades `local` where luac
     had temps, so the recompile stages them through fresh slots and grows a
     run of `MOVE`s (`CONCAT 4 4 5` becomes `MOVE 7,4; MOVE 8,5;
     CONCAT 4 7 8`). Each instance has its own local reason; no shared
     mechanism was found for them this session.
   * **`NEWTABLE` size hints**, pre-existing and fixtured in
     `tests/test_express_liverange.py::KNOWN_RESIDUAL`: the constructor fold
     turns a following `t.k = s` statement into `{["k"] = s}`, so the
     recompiled `NEWTABLE` carries a bigger hash-size hint.
     `snr_common.lua:main_24` (8 instructions) is the smallest instance.
   * **Multiple assignment**, exactly one proto: `snr_common.lua:main_77_0`,
     5 instructions, the smallest residual in the corpus. The M4 final review
     recorded it as "a genuine upvalue-index divergence"; that is the
     symptom. Measured 2026-08-12 by reverse-engineering the source, the
     original is `u0, u1 = 1, 0` and it recompiles to the proto exactly.
     `lparser.c`'s `assignment` (:931-962) resolves every left-hand
     variable before `explist1` runs and stores them in REVERSE order as its
     recursion unwinds, so printing the same bytecode as three statements
     makes `u1` the first upvalue referenced and the two `SETUPVAL` operands
     swap. Not fixed: recognising it needs lookahead over an emitted-statement
     run — a peephole over this layer's own output, the shape this project
     exists to avoid — and the whole corpus contains exactly one instance of
     the signature (measured: one descending `SETUPVAL`/`SETGLOBAL` run of
     length >= 2). Pinned with its diagnosis by
     `tests/test_express_residual.py::
     test_a_multiple_assignment_prints_as_separate_statements`.
   * The table-constructor fold's **statement reordering** is still live and
     still not a corpus row (see "Census entries that are not corpus rows"
     below); it is why the generic-`for` fixture in
     `tests/test_express_residual.py` is written as
     `local t = {7, 8, 9} for k, v in ipairs(t) do ... end` rather than with
     an intervening `local s = 0`.

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
the message collapsed to `N` for clustering). Re-measured 2026-08-12 after
M5 task 5, 48 rows:

```
refusal: structure: pc N: if targets out of range                       18
refusal: mismatch: maxstacksize                                         11
refusal: mismatch: code                                                 11
refusal: reconstruct: register N is read again after its staged ...      5
refusal: structure: pc N: else-join out of range                         3
```

(The 75-row histogram this replaced, measured 2026-08-12 after M5 task 4, led
with `mismatch: code` 23, `mismatch: maxstacksize` 21, `if targets` 18,
consumed-read 5, `else-join` 3, `and/or operand` 2, `while-header` 2,
`and/or alternative` 1. The last three rows are gone entirely; see point 2 of
the capability boundary for which fix took each.)

The two decompositions still agree: the `structure:`/`reconstruct:` rows sum
to 26 (protos whose subtree does not print, ancestor chains included) and the
two `mismatch:` rows to 22 (protos that print but do not certify). They are
different cuts of the same 48.

### The `L3.2 = canonical constant-pool order` rung: CLOSED, decided-not-doing

**Final number: 0. The item is closed permanently; do not re-measure it.**

The history is three measurements and two deferrals: M3 measured 9 protos
differing from the original only by constant-pool order and declined the
rung; M4 task 6 re-measured 10 against a bar of >= 20 and declined again; M5
task 5 re-measured 11 at its start. M5 task 5's brief set the rule in advance
-- >= 20 designs the rung, < 20 closes the item with the final number -- and
then the third cluster of that task removed the population's cause outright.
**Re-measured after it: 0 of the 48 remaining non-`L3` protos, and 0 of the
22 whose candidate recompiles, differ only by pool order.**

Every one of those 9/10/11 protos was the same defect, not a normalization
problem: `codecomp` (lcode.c:673-686) compiles `a > b` by evaluating `a` then
`b` and then EXCHANGING the operands so it can emit `OP_LT`, and
`luaK_infix`'s default arm (:710-733) interns `e1` through `luaK_exp2RK`
before the parser has seen `e2`. So `if select("#", ...) > 0 then` interns
`select, #, 0` while the `0 < select("#", ...)` this project used to print
interns `0, select, #` -- a pool permutation, produced by printing a
comparison the wrong way round. `Reconstructor._reads_as_gt` recovers the
`>`; see the capability boundary's point 3.

`NORMALIZATIONS` and `LADDER_VERSION` are unchanged and were never touched
for this. The rung would have bought rows by admitting that permuting a
constant pool is meaning-preserving, and every future certification would
have run under that admission; the defect it would have papered over is now
fixed instead.

The measurement method, kept because it is the right way to ask the question
if it ever comes up again for a different reason: for each non-`L3` proto
whose candidate recompiled, walk the original/candidate pair recursively and
ask whether, at every proto, (a) all of rung 1's surviving scalar fields are
equal, (b) the constant pools are permutations of each other by payload-exact
key, and (c) the code arrays are equal once every constant-index operand is
replaced by the constant it names -- the K modes come from `lift.opcodes`'
`OP_SPECS`, transcribed from `lopcodes.c`. It is exact, not a proxy. The
script is `scratchpad`-only by design (a one-off measurement, not a gate);
the logic above is enough to rebuild it in ten minutes.

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
   prints `x 1 2`. **Unshippable** — but not by the one-step rule this
   sentence used to give ("the root does not certify, so the fallback ships"),
   which M5 task 6 retired and task 12 corrected here. Measured on this
   fixture 2026-08-13: `main` is `L1` with `mismatch: code`, `main_0` is `L3`,
   and `emit_certified_chunk` returns `hybrid=False` with
   `fallback_paths == {"main", "main_0"}` — `certify_hybrid` was tried and
   returned `None`, because the defect is in the ROOT's own `code` and a hybrid
   can only substitute descendants. So the whole-chunk
   fallback ships and its stdout matches the original exactly. Pinned
   by `tests/test_structured_certify.py::
   test_table_constructor_fold_reorders_statements_but_cannot_ship`, which
   asserts both the divergence and the fact that it cannot escape. Note the
   shorter repro that circulated for this (`local t = {} print(1)`) does
   reorder the statements but is NOT observable — the only statement that
   moves there is a pure `NEWTABLE`; two folded items straddling an effectful
   statement are needed to make it visible.

2. **One of M4 task 5's five ported semantic-regression cases still ships
   fallback**, pinned to `L1` so it fails loudly when fixed:
   `test_counter_closure_and_dispatch_mix` (prints, then differs on
   `maxstacksize` 18 vs 20 and 13 vs 15 constants — clusters B/D). Its
   docstring in `tests/test_semantic_regressions.py` carries the full
   diagnosis, and it runs its fallback artifact and checks its stdout, so the
   *semantics* are regression-tested regardless of the level.

   **This item said TWO until the M6 final review.** The other was
   `test_if_and_elseif_conjunctions_preserved`, and **M6 task 11 moved it
   `L1` -> `L3`, structured** — the test itself, `m3-backlog.md`'s M6 agenda
   entry and `tests/test_m6_exit.py` all say so; only this paragraph still
   pinned it to `L1` with a `structure: pc 4: if targets out of range` that
   the condition-tree recognizer no longer produces.

3. **`run_corpus.py`'s forced-`L0` path** used to keep whatever
   `confessions` the entry already had, which for an individually-`L3` proto
   in a chunk that failed to compile is `[]` — an `L0` row could ship
   unconfessed. Fixed in M4 task 6 (`_force_l0`); unreachable from the corpus
   (229/229 files compile), so it is pinned by unit tests instead:
   `tests/test_ledger.py::test_forced_l0_entry_is_confessed` and
   `::test_forced_l0_keeps_an_existing_confession`.

### Re-deriving the three rows

Rows 1 and 2, verbatim (re-run 2026-08-13, reproduces the table above; the
`1447/1913` this block printed until then was an M5-task-4-era paste that
tasks 5's three clusters superseded — the *prose* table above was correct and
the pasted output was not, which is the whole hazard of pasting output):

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
accepts own body         1465/1478 (99.1%)  1931/1944 (99.3%)
whole subtree prints     1452/1478 (98.2%)  1918/1944 (98.7%)
```

Row 3 needs no script: it is the committed ledger. `uv run python
scripts/ledger_dashboard.py` prints both bases (`L3 share (unique)` and
`L3 share (occurrences)`).

The refusal breakdown in point 1. Self-contained; re-run 2026-08-13, and the
eight lines it prints — 1478 / 13 / 12 / 1 / 195 / 183 / 16 / 4 — are the
output block below verbatim. (It read `31 / 26 / 5 / … / 169 / … / 8` until
then, prefaced by that same verbatim claim: an M5-task-4-era paste that task
5 superseded, while point 1's prose three screens up already said 13.)

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
build_sir refusals                  13
  of which carry a back edge        12
  acyclic refusals                  1
protos with a back edge at all      195
  back edge but accepted (loop)     183
protos containing TESTSET           16
  of which are refused              4
```

Point 3's opcode-histogram breakdown, **re-run 2026-08-13**. The paste it
replaces (`31 A / 20 B / 19 D / 4 C / 1 E`, dated 2026-08-11) was the fourth
tier-1 block in this section and the most wrong of the four: it summed to
**75** where the non-`L3` unique population is **48** (1478 − 1430), which the
output below sums to exactly, and its introducing sentence quoted a *third*
split again (`54/16/14/4/1`). Category **D is now empty** — M5 tasks 4 and 5
removed it. Historical: the `253/56/15/15` split this block produced on
`dec379e` is M4 task 13's baseline and is quoted in point 3 above as history,
not as current state.

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
   26  A. subtree refuses structuring
   11  C. extra MOVEs only
   10  B. same opcode histogram, operands differ
    1  E. other delta

    5  first differing instruction: B NEWTABLE->LOADK
    4  first differing instruction: C CALL->MOVE
    3  first differing instruction: C JMP
    2  first differing instruction: C NEWTABLE
    2  first differing instruction: B NEWTABLE
    1  first differing instruction: C MOVE
```

The five category counts sum to **48 = 1478 − 1430**, and the split lines up
with the `refusal_reason` histogram three screens above by a different route:
**A = 26** is the `structure:`/`reconstruct:` population (subtree does not
print), and **B + C + E = 22** is the `mismatch:` population (prints, does not
certify). Two decompositions of the same 48.

The print-but-do-not-certify mismatch histogram in point 3. Self-contained —
run it verbatim like the two above (re-run 2026-08-13). This is the only one
that spends `luac_sz4` subprocesses (22 of them). Its output used to read
`35 / code 35 / maxstacksize 20 / constants.len 16 / const[i] 11`, from the
same superseded era as the two blocks above; the ledger's own census agrees
with the numbers below — 22 `mismatch:` rows, 11 `maxstacksize` and 11 `code`
(2 of those as `code at root/N`):

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
print but do not certify: 22
  code             22
  maxstacksize     14
  const[i]         8
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

**M4 settled it beyond argument, and M5 tasks 4 and 5 widened the margin.**
Printability is now 1452/1478 = 98.2% unique and 1918/1944 = 98.7%
occurrences, and the achieved `L3` rate is 1430/1478 = 96.8% / 1896/1944 =
97.5%. The "ceiling" is exceeded by more than fourteen points on either
basis. Kept here as a worked example of a
planning-stage number that survived into three documents and a module
docstring without ever being measured.

The other standing limits are the two probes. Both numbers below were
re-measured live at the M6 final review (2026-08-14) and both had moved: M6
task 12's hybrid emission converged three L1.5 pins and one L1.75 pin. The
**global-state probe** (L1.5) reaches **228/229** files with **1** pinned
divergence (was 225/4); read its reach table
before treating it as strong evidence, because for 222 of 229 files the entire
compared payload is `string:main=<function>`. The **behaviour probe** (L1.75,
M4 task 10) deepens that to **228/229** (was 227/229) over 398196 recorded events — the
event total did NOT move — but its
reach is bimodal, not a uniform deepening: the 3000-event cap truncates 132 of
229 files, which contribute 99.5% of the events, while the other 97 contribute
a median of **10** events each. Both are documented in
`docs/runbooks/m3-backlog.md`; neither is L2.

## The L2 gate — key-sequence differential execution (M5 task 9)

`scripts/probe_keyseq.lua` + `scripts/probe_keyseq.py`, gated by
`tests/test_l2_keyseq.py`. It is the third and deepest of the probe gates:
L1.5 compares the global-state delta a chunk leaves, L1.75 *calls* every
global function it defined and compares event traces, and L2 drives the
input-polling loops those calls get stuck in with a **scripted key sequence**.

### The grant rule

A file is granted `L2` when, under **every** one of its authored sequences:

1. both sides produce a recognisable trace (no probe-side failure),
2. the two traces are **byte-equal over everything the probe observed**,
3. the run actually consumed the sequence — at least one `K|` poll event,
4. neither side recorded any runtime **taint** mark, and

and, over the file as a whole:

5. the **static backstop** finds no place where a stub-derived value could
   decide a branch nothing observed,
6. **at least one authored sequence ran to completion** (`OK`, not `CAP`),
7. **every proto in the chunk is `L3`**.

Anything else refuses, with a reason from
`probe_keyseq.REFUSAL_KINDS` = `divergent | taint | taint-static |
no-key-poll | truncated | not-l3 | probe-error`. The badge is `cov`, the
fraction of the shipped artifact's **protos** the **completed** runs entered.

Condition 3 is what stops the gate being L1.75 with a better name: without it
any of the 229 files could be handed a sequence it never reads and granted on
trace equality alone. Condition 5 is what stops it being an *elaborate* L1.75
— see below; it was added in round 1 after review found twelve ways to launder
a stub value into a branch decision with the four other conditions all green.

Conditions 6 and 7 were added in the M5 final fix round, and both were **holes
that had shipped**:

* Condition 2 used to say "byte-equal" flatly, and `evaluate` never looked at
  `header`, so a run stopped at `MAX_EVENTS = 3000` compared equal *over its
  prefix* with nothing recorded anywhere. Demonstrated:
  `for i=1,5000 do engine.Go(i) end engine.OriginalTail()` against the same
  loop ending in `engine.COMPLETELY_DIFFERENT_TAIL()` — both `CAP|3001`,
  byte-equal, no taint, `granted=True, cov=1.0`. It is deliberately **"at
  least one"** and not "all": the degenerate sequences never halt (measured
  with the cap raised 1000x, `snr_lib.lua` under `tail=CIRCLE` reports
  `CAP|3000001`), and every one of the five authored files has one, so
  requiring all would put L2 reach at 0 permanently.

  **Condition 6 narrows the hole; it does not close it.** A capped run can no
  longer be the only evidence for a FILE, but it can still be the only
  evidence for a BRANCH no completing sequence enters — put `tail=` on the
  `else` arm and the divergent tail behind `k=1,CIRCLE`, and the gate grants
  at `cov` 1.0 because **both** specs enter 2 of 2 protos and proto
  granularity cannot see a branch. Committed as a known-open route
  (`tests/test_l2_keyseq.py::test_a_branch_only_a_capped_sequence_enters_is_
  granted_on_a_truncated_prefix`, which asserts the granting behaviour) and
  routed to M6 agenda 2 with the two candidate instruments. Reassurance for
  the one live grant, measured and not assumed: `snr_lib.lua`'s capped
  `tail=CIRCLE` re-run at 10× budget with decimal tokens normalised out gives
  **15 distinct event shapes at 3000 events and the same 15 at 30000, none
  new**. The gate does not check that; a new sequence would need its own
  measurement.
* The static backstop reads the **original** only, so it speaks for the
  artifact just while the two are field-identical. They otherwise diverge in
  shape: on `snr_music.lua` the original taints
  `{compare 36, length 1, launder 1, loop 3, truthiness 2}` and its shipped
  fallback text taints `{compare 3, loop 16}` — the `__pld_R` box model hides
  33 compare sites and invents 13. So **L2 today certifies only field-identical
  artifacts**; extending it to hybrids or fallback text is M6 work and needs
  the artifact analysed too, not this condition relaxed.

Measured cost of both: **none.** Reach is 1/5 authored files before and after
(`snr_lib.lua`, `cov` 1.0, 3/3 protos, block interval [0.3509, 0.9123] of 57 —
its two completing sequences alone give the same coverage as all three), and
`corpus/ledger.jsonl` is byte-unchanged. The four refused files fail condition
5 first and would also fail condition 7 (17 of 147, 4 of 6, 4 of 6, 2 of 5
protos not `L3`); the order of the last two checks is what decides which
reason they report, and it keeps the more informative taint finding.

### Taint: two instruments, because one is structurally blind

**Runtime marks** (`scripts/probe_keyseq.lua`) see what a metatable can see:
`cmp:lt` / `cmp:le` / `cmp:eq` when a stub proxy reaches a comparison
metamethod, and `intro:type` / `intro:rawequal` / `intro:getmetatable` when
one is introspected. Where the comparison marks apply they are not an
approximation — `lvm.c`'s `OP_LT`, `OP_LE` and `OP_EQ` produce no value, they
select the following `JMP` — but **where they apply is much narrower than it
looks**. `lvm.c`'s `equalobj` is

```c
ttype(o1) == ttype(o2) && luaV_equalval(L, o1, o2)
```

so `__eq` is consulted only for proxy-vs-proxy. `stub == "str"`, `stub == nil`
and `stub == 1` fire nothing at all, and `__lt`/`__le` are narrower still
(Lua 5.1 raises on mixed types before reaching a metamethod).

Measured 2026-08-12, twelve laundering routes, **every one granted with zero
runtime marks** before the backstop existed:

```
== "str"   == nil   ~= nil   == 1   == {}   #stub > 0   next(stub)
tostring(stub)   tonumber(stub)   stub .. ""   select("#", stub)   pcall(stub)
```

And it is not a corner. Counting on the **original bytecode** -- a
`GETGLOBAL "doScriptScene"` whose destination register is an operand of an
`EQ` within the next three instructions -- the idiom occurs **427 times across
23 of the 229 corpus files**, and 26 of the 132 capped files spin in exactly
that dispatch loop. (An earlier version of this line said "310 times across 20
corpus files". That figure is real but it counts `doScriptScene ==` in the
**decompiled artifact text**, where three of the 23 files ship fallback and so
do not spell the idiom; as a statement about the corpus it undercounts by
27%.)

**The static backstop** (`probe_keyseq.static_taint`) closes them. It is a
conservative may-analysis over registers, per proto, to a fixed point on the
existing `cfg.blocks.build_cfg`, run over the **original** lifted bytecode.
Seeds are `GETGLOBAL`s of **every** name the probe environment does not
resolve to a real, non-reflective library value: `_BASE_GLOBALS` (re-derived
from the vendored interpreter by a test) and `_DRIVER_GLOBALS` (compared
against the Lua `DRIVER` table by another), **minus `_REFLECTIVE_BASE` and
minus anything the chunk shadows**. It propagates through `MOVE`,
`GETTABLE`/`SELF` (table **or** key), `CALL` whose callee is not in
`_CLEAN_CALLEES`, arithmetic, `CONCAT`, `UNM`/`NOT` and `LEN`; every
`GETUPVAL` is stub; every register `lift_proto` reports as **captured** is
stub for the whole proto; block entry takes the union of predecessors.

**There is no "the chunk defines this global, so it is not a stub"
exemption**, and there was for one round. `read - written` over the whole
chunk, with no ordering, is unsound in exactly the way the runtime marks were:
`env.__index` consults `envfields`, which is empty until the chunk *executes*
the write, so a global read before its write — or whose write lives in a
function nobody calls — is a proxy at that read. Three fixtures granted with
byte-equal traces and zero marks, including laundering **through** the
exemption (`stash = sys.a` then `if stash == "x"`). A sound version would have
to prove the write dominates every read *and* that the written value is not
itself stub-derived; it was deleted instead, because it was measured to buy
nothing — with it gone the CLI is still 1/5 with the same file granted.
`snr_lib` has 0 globals that are both read and written; `snr_common` has 72.
**Six** flag kinds, all of which refuse (this line said "four" while the table
under it listed six):

| kind | site |
| --- | --- |
| `blind-compare` | `EQ`/`LT`/`LE` with a stub-derived operand |
| `blind-length` | `LEN` on a stub-derived register (`OP_LEN` never consults a metamethod for a table) |
| `blind-launder` | a call of `type`/`next`/`tostring`/`tonumber`/`select`/`pcall`/… with a stub-derived argument |
| `blind-truthiness` | `TEST`/`TESTSET` on a stub-derived register |
| `blind-loop` | `FORPREP`/`FORLOOP`/`TFORLOOP` whose control triple `R(A)..R(A+2)` is stub-derived — a loop's **trip count** is a branch, and the body can write a perfectly clean register |
| `blind-harness` | a stub-derived value in the argument window of a `_CLEAN_CALLEES` callee — the harness's own state is a channel a register analysis cannot follow (see below) |

`blind-truthiness` was very nearly left out, on the prediction that
`if someGlobal then` is common enough that refusing on it would take reach to
zero. **The prediction was wrong.** Re-measured 2026-08-13: `snr_common`
**20**, `snr_graphic` 9, `snr_memory` 9, `snr_music` 2, `snr_lib` **0** — so
including it costs nothing here and makes the condition the literal property
instead of an approximation of it. (The 17 this line carried for `snr_common`
predates the later rounds' widening of what counts as stub-derived.) The full
census, same run: `blind-compare` 236 / 58 / 48 / 36 / 0, `blind-loop` 50 /
19 / 10 / 3 / 0, `blind-launder` 3 / 1 / 2 / 1 / 0, `blind-length` 0 / 7 / 0 /
1 / 0, and **`blind-harness` 0 on all five** — so `blind-harness`'s evidence
is *entirely synthetic*, and a green corpus says nothing about whether it
works.

### The trusted-callee rule, and why it is an allowlist

Round 2 fixed "an accessor's return value is not stub-derived" by declaring
every `_BASE_GLOBALS` and `_DRIVER_GLOBALS` name a trusted callee — that is,
by trusting a list of callees **without checking what those callees do**. It
re-opened the same hole it closed. Measured, each with byte-equal traces, zero
runtime marks, and the proxy visible in the trace at the comparison:

```lua
local ok, v = pcall(f)                  -- pcall FORWARDS the callee's returns
local x = assert(sys.a)                 -- assert is the identity function
rawget(_G, "doScriptScene") == nil      -- reflects the environment
tostring = sys.conv; tostring(1)        -- a SHADOWED base name is a proxy
getfenv().doScriptScene                 -- getfenv() returns the target's env,
                                        -- whose __index BUILDS a proxy
local g = _G; g.doScriptScene == nil    -- decided by where the probe keeps
                                        -- the chunk's globals, not by the code
```

The rule is now an explicit **allowlist** of callees that provably cannot hand
back a value derived from their arguments or from the environment —
`pressButton`, `wait`, `type`, `rawequal`, `getmetatable`, `tostring`,
`tonumber`, `print` — minus anything the chunk shadows, and only when no
argument in the call window is stub-derived. Everything else, including every
other base global, returns a stub. `_G`, `getfenv`, `setfenv`, `load*`,
`dofile`, `require`, `module`, `package`, `arg` and `newproxy` are further
demoted to **seeds** (`_REFLECTIVE_BASE`): `env.__index` does resolve them for
real, but what they hand back is the stub environment's own shape.

Measured cost: none for the shipped grant — `snr_lib.lua` calls no base
global at all and the corpus reads `_G` and `getfenv` zero times. But the
allowlist is **not** decoration: emptying `_CLEAN_CALLEES` changes the taint
of 9 corpus files, `snr_lib.lua` among them.

Counted with the module's own `index_globals` rule, the corpus' **recognised
callees** are `wait` **4554**, `pressButton` **157**, `select` **26** and
`pairs` **7**. `string` and `math` are *never* recognised callees — the
intervening `GETTABLE` invalidates the holder, so `string.format(…)` already
returns a stub. An earlier version of this paragraph gave "`wait` (4556),
`pressButton` (157), `string` (95), `select` (26), `math` (10), `pairs` (7)":
those are `GETGLOBAL` **read** counts, which is a different question, and the
same mistake in kind as the `doScriptScene` figure two rounds earlier.

### Harness state is a channel, not a propagation gap

`waitf(n)` does `local m = tonumber(n)`, which is `nil` for a proxy, so
`wait(sys.delay)` advances **one** frame instead of N — and the frame counter
decides every later `pressButton`. Measured: both sides traced identically,
zero runtime marks (the probe's `waitf` calls its own local `tonumber`, so no
override sees it), `static_taint == {}`, GRANT; the control `wait(3)` takes
the other branch under the same key spec.

That is not a missing propagation rule — a register may-analysis is
*structurally* unable to follow taint into the harness's own state. The answer
is at the boundary instead: a stub-derived value reaching a callee the harness
depends on records a `blind-harness` site. Measured free (0 sites across the
corpus). The same rule covers `pressButton(sys.k)`, whose result is selected
by its argument's value.

**Anything else the harness carries between calls is the same class**, and
this is the first limit found here that is not a propagation gap.

### Four rounds of tightening, and what the reach did

The substantive result of this task, stated where the badge is:

* Round 0 shipped **5/5** authored files granted. Twelve laundering routes,
  four more, then eight more were found to grant with byte-equal traces and
  zero runtime marks — each time inside the code written to close the previous
  set.
* Rounds 1–4 took the analysis from nothing to a static backstop with six site
  kinds. **Reach never moved off 1/5.** Every round refused only fixtures, not
  corpus files.
* Four clean controls (a branch on a local, `pressButton(...) == true`,
  `tostring(7) == "7"`, a constant-trip `for`, and `wait(3)`) still grant
  after all of it, so the backstop did not become a blanket refusal.

So the badge is narrow *and* it survived four adversarial rounds without
narrowing further. The one shipped grant is `snr_lib.lua`, and it is
incidentally clean: 0 `SETUPVAL`, 0 captured registers, 0 `TFORLOOP`, 0
`VARARG`, 0 `_G` reads, no base-global call.

### What the pair still cannot see

Stated as gaps, not as a complete list — the previous version of this section
presented three blind spots as complete and was not, which is what let the
twelve routes ship. Each of these is a committed test
(`test_what_the_two_taint_instruments_still_cannot_see`) that *grants* and
should not:

**This is what I could construct, not a proof of what exists.** Three
consecutive review rounds each found the new hole inside the code written to
close the previous one — twelve routes in round 0, four in round 2, eight more
in round 3 — and each round's list of "what remains" claimed to be the whole
of it. Treat the four below as the residue I could not close, and assume
there are others. (This sentence said "three" while the list under it had
four; the harness-state bullet is the one that kept getting dropped, and
`scripts/probe_keyseq.py`'s own module docstring omitted it outright until the
M5 final fix round.)

* **A stub passed as an ARGUMENT.** `static_taint` is intra-proto and a
  parameter is a root, so `decide(sys.a)` with the comparison inside `decide`
  is not seen. (The RETURN direction is covered; so is the aliased launderer
  `local ts = tostring; ts(stub)`.)
* **A value stored into a script-built table and read back.**
  `local t = { x = stub }` then `if t.x == "a"`; `SETTABLE` is not tracked.
  Indexing off a stub-derived table, or at a stub-derived **key**
  (`t[sys.k]`), both are. The committed fixture uses the constructor rather
  than `local t = {} t.x = stub`, because the two-statement form is one this
  pipeline cannot certify (`mismatch: code`) and grant condition 7 would then
  refuse it as `not-l3` before taint got a word in.
* **Any other harness state carried between calls.** `blind-harness` closes
  the argument boundary for the callees currently in `_CLEAN_CALLEES`; a
  register may-analysis still cannot *follow* taint through the harness, so a
  future driver that keeps state a stub can perturb some other way would need
  the same treatment at its own boundary.
* **`VARARG`.** `local a = ...` compared against a literal is not flagged.
  `snr_common.lua` has 26 `VARARG`s and reads `select` 26 times (both counts
  re-measured in M5 task 10 and reproduced exactly), so this gap and the
  `select` idiom do meet in the file both historical checkpoints live in.
  **But not in the checkpoints themselves**: the 26/26 are spread over 11
  protos, and `OptionMain` (`main_74_13`) and `ConfigMain` (`main_76_2`) --
  together with the whole of the `main_74` and `main_76` subtrees -- contain
  **0** of each. Neither checkpoint property rests on the idiom, so task 10's
  regressions are not standing on this gap. It remains open for the L2 grant
  itself, which `snr_common.lua` does not have anyway (`taint-static`).

Two things tried this round that did not work, recorded so they are not
retried blind: widening the loop-variable register window does **not** catch a
stub-decided trip count (re-run at `a+40`, still granted — the body writes a
clean register and the decision is the loop's own, which is why `blind-loop`
had to be a site of its own); and pinning the derived `TFORLOOP` window on the
VERDICT does not work either, because `blind-loop` refuses the same file
anyway — it has to be pinned on the site counts.

The static analysis is also **path-insensitive**: a site in a function the key
sequence never enters still refuses the whole file. That is the conservative
direction, and it is why four of the five authored files refuse.

### Reach — measured, and not what the plan predicted

The M5 plan's premise was that "the 3000-event cap truncat[es] 132/229 files
mid-loop … the game loops block on input, and scripted input walks them". The
mechanism is right; the arithmetic is not.

Measured 2026-08-12, on the original side of all 229 files:

* 132 hit the cap, 97 finish. **That reproduces exactly.**
* Taking each capped file's most frequent recorded call over the whole trace:
  **101 are `vms`-dominated** (linear story scripts truncated by sheer
  volume — no key sequence changes them), **26 are `wait`-dominated** (24 of
  those contain `doScriptScene`, i.e. they spin in the dispatch loop above),
  and **5 are `pressButton`-dominated**.
* **9 files contain `pressButton` at all**; **5 reach the poll**. The other 4
  have an input loop and error before getting to it under the frozen stub
  policy — `snr_mainmenu` (arithmetic on a nil field), `snr_novel`
  (concatenate a nil field), `snr_fragment_main` and `snr_story_main` (compare
  table with number). They are a live M6 lead, not dead ground.
* The remaining **220 files contain no `pressButton` at all.**

An earlier version of this section said "for 224 of the 229 files there is no
input loop for a sequence to drive" and "the other 127 capped files are
truncated by sheer `vms()` volume". Both are wrong: 220, not 224; and 101, not
127.

### What the badge actually covers

| file | poll events / 3001 | verdict |
| --- | --- | --- |
| `snr_lib.lua` | 2243 | **L2@100%** — 3/3 protos; blocks in [0.3509, 0.9123] of 57 |
| `snr_music.lua` | 2502 | refused `taint-static` (compare 36, launder 1, length 1, loop 3, truthiness 2) |
| `snr_graphic.lua` | 2606 | refused `taint-static` (compare 58, launder 1, length 7, loop 19, truthiness 9) |
| `snr_memory.lua` | 2608 | refused `taint-static` (compare 48, launder 2, loop 10, truthiness 9) |
| `snr_common.lua` | 2557 | refused `taint-static` (compare 236, launder 3, loop 50, truthiness 20) |

**One of five authored files is granted.** In the ledger that is **2 rows and
3 proto occurrences of 1944**, and all three ship STRUCTURED text — `snr_lib`
is one of the 216 fully-structured files. So **L2 currently validates the
structured emitter on one file and says nothing about the fallback state
machine**: the four refused files are exactly the ones that ship fallback or
hybrid. 164 occurrences carry `{"refused": "taint-static"}`, which is data
rather than silence.

Before the round-1 backstop all five were granted. **How much of that is
"withdrawn because wrong" rather than conservative over-refusal is a
measurement, and it does not cover all four.** Per-proto site census, taking
each proto's own sites as its subtree total minus its children's:
`snr_graphic` and `snr_memory` each carry **one site in the main chunk
itself**, which every run executes, so their old grants really were wrong.
`snr_music` has **0** there (31 of its sites are in `main_3`) and
`snr_common` has **0** (its 234 sites are spread over 55 protos, none of them
the chunk body). For those two the refusal rests on the analysis being
path-insensitive — honest over-refusal, not a demonstrated wrong grant. An
earlier version of this paragraph said all four grants were wrong; that
claim is stronger than the evidence.

Five of the thirteen sequences still run to the cap (`snr_common`#3,
`snr_graphic`#3, `snr_lib`#3, `snr_memory`#2, `snr_music`#2 — re-measured
after the M5 task 10 re-timing below, and it is still exactly those five).
`snr_lib`#3 (`tail=CIRCLE`, the button held from frame 1) is the deliberate
control: it reproduces the L1.75 result, `CAP|3001` with 2243 polls, next to
the driven sequences that finish at `OK|68` (UP/four-DOWN/CIRCLE) and `OK|38`
(DOWN/DOWN/CIRCLE). The other four are not controls; they land every directive
they carry but their keys do not exit their loops, disclosed here rather than
presented as driven. The eight sequences that do finish land at 38, 68, 137,
174, 233, 238, 263 and 542 events.

**`snr_common.lua` and the divergence one key away.** Its third sequence is a
whole-chunk drive with `tail=CROSS`, and it does not diverge — but only
because it caps inside `autoSystemSave` before reaching `cBrStr`. Change that
tail key to `CIRCLE` and the same drive diverges at trace line 276
(`R|cBrStr|bad argument #1 to 'len'` vs `to '?'`). That is the `getobjname`
naming artifact of the fallback's `__pld_R` box model — the already-documented
class. **Corrected at the M6 final review (2026-08-14): this sentence used to
say the divergence was "already pinned as an exact byte pair by the L1.75
gate (`probe_behaviour.EXPECTED_DIVERGENCE`, for `snr_mainmenu`)", and that
entry was deleted two commits later** (`741bf1a`, M6 task 12) because
`snr_mainmenu.lua`'s pair CONVERGED — the same task removed three more of the
class from `probe_global_state.py`. A reader was being pointed at a table that
no longer contains it. What is live: the class is pinned two-directionally as
`probe_enum.EXPECTED_DIVERGENCE["snr_common.lua:main_81"]`, on a different
proto of this same file. *This* `cBrStr` pair is pinned nowhere, and saying so
is the point — L2 deliberately does not pin
divergences of its own: a pin is an exemption, and this gate refuses on
divergence rather than excusing it. `snr_common` refuses anyway, on
`taint-static`.

### The two historical checkpoints (M5 task 10)

`tests/test_keyseq_checkpoints.py` ports the predecessor's
`DEBUG_KEY_SEQUENCE_HARNESS.md` playbook — the two "已验证的高价值检查点" in
`snr_common.lua`, deferred through two milestones — onto this harness. Each
drives the original bytecode and our shipped artifact with one authored key
sequence, requires the traces to be **byte-equal**, and then asserts the
checkpoint's own property **on each trace separately**:

| checkpoint | property, as a statement about the trace |
| --- | --- |
| `systemOption.OptionMain`'s two mutually exclusive clamps (`1..5` / `0..1`) | Drive menu row 1 to both ends (4 LEFT, 6 RIGHT), move down one row, do the same (3 LEFT, 4 RIGHT). Row 1's display layer takes **5** distinct `layerClip` rectangles, row 2's takes **2**, both saturate under repeated pressing, 5 > 2 — two ranges of different size are in force under the same two keys — and the two keys move row 1's rectangle in **opposite** directions. |
| `systemConfig.ConfigMain`'s CIRCLE gate/wait | Press CIRCLE on a row the gates reject, then on the one row whose CIRCLE the `memoryFlag` gate decides. The run ends `OK` not `CAP`; the first CIRCLE-down is **not** the last poll; between it and the next iteration's poll the trace records exactly one call, `wait(1)`, and the frame advances by exactly 1; after the accepted press there is no further poll and the trace ends at the entry's return. |

**Which of the three named gates checkpoint 2 actually covers**, measured
rather than claimed — round 1 corrected a docstring that claimed all three:

| gate | covered? | evidence |
| --- | --- | --- |
| `firstFragment` | yes | forcing it open changes the trace and fires the call-window assertion |
| `memoryFlag` | one direction | forcing it **open** changes the trace and fires the tail assertion; forcing it **shut** leaves the trace byte-identical, because the probe environment fixes `memoryFlag` false and that is the arm the run already takes |
| `storyLineSkip` | **no** | it is written only inside the `firstFragment == 1` region, which this environment never enters; changing the value it toggles to leaves the trace byte-identical |

The first version of the sequence pressed CIRCLE only on rows the
`memoryFlag` gate does not guard, so **all three** of those mutations were
byte-identical. Three UPs onto the guarded row is what bought the second row
of that table.

The property is asserted on the **original's** trace as well as ours, which is
the whole point: trace equality is already the L2 gate's job and says nothing
if both sides regress together. That guarantee comes from the two property
tests applying their property function to each trace **separately**, after
requiring the traces equal — not from the injections, which mutate only the
artifact side in the committed parametrisation. As an out-of-tree exercise
(re-run each round, not committed), all ten injected bug shapes — three of
them the playbook's own — still fail the property when the *original* side is
replaced by `luac_sz4`-compiled mutated source so the two traces are
byte-equal. One of the ten is a **key-polarity swap**, found by
review: exchanging the two direction keys' names reaches the same five
rectangles in reverse order, which `set()` erases, so it passed every other
clamp assertion until an explicit "the two keys move the display in opposite
directions" check was added.

Both properties are expressed in **numbers and event structure only** —
distinct rectangle counts, poll frames, frame deltas, "was there a poll after
this one". No corpus string is matched: the red line holds without an
exception, and the one thing that could not be phrased structurally (*which*
menu row is which) is handled positionally, as "the first and last display
layer to be redrawn".

**What they do not prove.** `snr_common.lua` ships **whole-file fallback** and
its L2 verdict is `refused: taint-static`; this module does not change either,
and adds no sequence to `KEY_SEQUENCES` (so `corpus/ledger.jsonl` is
byte-unchanged). Round 1 *did* re-time the sequences already in
`KEY_SEQUENCES` — see below — but that moved no verdict and no `cov`, so the
ledger is unchanged by it too. These are behavioural regressions over the fallback state
machine along two input-driven paths — which is exactly the ground the L2
badge does not cover, since the badge is `snr_lib.lua` and structured text
only.

### The frame model, and the directives that were never read (M5 task 10 r1)

A `k=<frame>,<KEY>` directive is read only if the target polls on that exact
frame, and the frame counter moves on `wait` alone (`waitf`:
`frame += max(floor(n), 1)`). These menu loops answer an accepted press with
`wait(5)` and close the iteration with `wait(1)` — **six frames per press** —
so the 1-frame spacing the sequences shipped with delivered most directives
while the loop was inside a `wait`.

Measured on the original side of all five files: of the 13 sequences, 11 carry
`k=` directives and **all 11 dropped at least one**. Nine landed exactly their
first directive; `snr_common`#1 landed 2 of 5; and **both `snr_music`
sequences landed 0**, because that file's first poll is at frame 31 and every
directive was delivered before it. The gate was running on roughly one press
per sequence while its text described six. Nothing detected it, because a
dropped directive is silent — the trace is still comparable, still polls, and
still agrees.

Every frame is now derived by probing: directive *i* is placed at the first
frame after directive *i-1* at which the target actually polls that key.
Two trailing directives were **dropped** instead, because their key is not
polled on the path the rest of the sequence takes (`snr_common`#1's trailing
`CIRCLE`, which `OptionMain` polls only on the L/R page that key order never
enters, and `snr_graphic`#2's second `CROSS`, after the first has left the
loop). Re-measured: **11 of 11 land every directive.**

What it cost and did not cost, measured before landing:

* **No L2 verdict moved** — still 1 granted (`snr_lib.lua`) and 4
  `taint-static`, with the same site counts.
* **`cov` is 1.0 either way** (`snr_lib` already entered 3/3 protos), so
  `corpus/ledger.jsonl` is byte-unchanged and `ratchet_diff.py` sees nothing.
* The **block diagnostic** dropped: [0.386, 0.9474] → [0.3509, 0.9123] of 57
  blocks (upper bound 54 → 52). Two blocks were reached only by the old
  timing's accident of holding the tail key across a `wait`; three longer
  honest variants were measured without recovering them. It never enters the
  ledger.

`tests/test_l2_keyseq.py::test_the_sequences_actually_drive_the_corpus_loops`
now asserts every directive lands, so this cannot recur silently. Proven
load-bearing: restoring one old sequence makes it fail naming the five
directives that go unread.

### Why this has to be sound rather than best-effort

`l2` is a **committed ledger field**. `corpus/ledger.jsonl` currently carries
**2 row-level** grants and **3 occurrence-level** `{"cov": 1.0}` records, plus
164 occurrences at `{"refused": "taint-static"}`. The row/occurrence mismatch
is the aggregate design working, not a bug: the third granted occurrence lives
on shash `fbad0f8acb`, a shape with **292** occurrences in all — 291 of them
in files no key sequence drives — so `verify.ledger.row_l2` correctly
withholds the row-level badge. and `scripts/ratchet_diff.py` reads them for
`l2-lost` and `l2-coverage-downgrade`. So an unsound grant does not stay in a
console diagnostic: it is written into a checked-in artifact and becomes the
baseline a later run is measured against. That is the reason the analysis is
held to "no branch may be decided by a stub-derived value without a site being
recorded" rather than to best effort — and the reason three rounds of holes in
it were each treated as defects rather than as refinements.

### One deliberate exposure: `probe-error` details on the console

`L2Result.detail` for the `probe-error` reason is `str(ProbeError)[:400]`, and
`ProbeError` interpolates the probe's own stdout — trace lines that can carry
Japanese string constants. The CLI prints it.

**Accepted, explicitly.** The red line is about ingest/lift/verify/comparison
and about diagnostic text that lands in a committed artifact; this is neither.
`detail` never reaches `corpus/ledger.jsonl` — `as_ledger_field` emits only
`{"cov": <number>}` or `{"refused": <word from REFUSAL_KINDS>}` — and
`scripts/probe_behaviour.py::probe_raw` has embedded `stdout[:400]` the same
way since M4. The alternative is a probe that cannot say why it failed, which
is the L1.5 failure this whole family of gates was built to avoid.

### The spec grammar

Sequences are data, in `probe_keyseq.KEY_SEQUENCES` (file → tuple of specs).
A spec is `;`-joined directives, parsed by plain byte scanning:

| directive | meaning |
| --- | --- |
| `k=<frame>,<KEY>[+<KEY>]*` | the keys held on that frame (1-based) |
| `tail=<KEY>[+<KEY>]*` | the keys held on every frame past the last `k=`; `tail=` means none |
| `entry=<dotted.name>` | call exactly this instead of invoking every global function |
| `cov=1` | collect coverage |

Frame 1 is the first frame and `wait(n)` advances by `max(floor(n), 1)` —
the predecessor's rule (`DEBUG_KEY_SEQUENCE_HARNESS.md`:
`frame = frame + math.max(n, 1)`), which is also how the corpus' menu loops
pace themselves; every one of them ends its iteration with `wait(1)`.

`entry=` resolves a dotted path against the chunk's globals. The two
historical checkpoints are `systemOption.OptionMain` and
`systemConfig.ConfigMain` — the lower-case *instances*
(`systemOption = SystemOption.new()`), not the class tables; `entry=
SystemOption.OptionMain` is an `ENTRYFAIL`, and `ENTRYFAIL`/`SPECFAIL` are
deliberately **not** comparable values (a mistyped entry name is a property of
the spec, not of the program, and would produce the same string on both sides).

### Coverage: proto, not block, and why the badge had to change

The badge is **proto coverage**: distinct protos of the artifact entered
during the run (observed from `call` hook events, de-duplicated on
`(linedefined, lastlinedefined)` so two closures of one proto count once),
over the number of protos in the compiled artifact.

It started as **block** coverage and had to stop being that. Block attribution
has only one seam — the source line of each block's first instruction — so it
moves when the emitter moves a newline. Measured this session on one program,
one sequence, the same 10 blocks: the block interval reads **[0.30, 0.50]
spread over lines and [0.00, 0.90] compacted**, while the proto badge is
0.6667 either way. That breaks a project-level invariant, not
just a number: CLAUDE.md defines a presentation-layer change as one that
leaves `corpus/ledger.jsonl` byte-unchanged, and **M5 task 7 shipped five
printer changes on exactly that evidence** — one of them `elseif`, which
merges two lines into one. A layout-sensitive `cov` would have made those
commits read as reach regressions and would make `ratchet_diff`'s
`l2-coverage-downgrade` fire on cosmetics.

Proto coverage has no line in it. The one place a line number survives is the
de-duplication *key*, which is sound only while it is injective over the
artifact's protos — **checked per run**, not assumed. Measured over eight
artifacts (the five authored files plus `snr_novel`, `snr_crd_0`, `config`):
390 protos, 390 distinct keys. A hand-written one-liner does collide, which is
why it is a check; a non-injective artifact refuses with `probe-error` rather
than silently merging protos.

The original bytecode is **stripped** (`lineinfo` empty,
`debug.getinfo(...).currentline` is `-1`), so nothing can observe which of
*its* protos or blocks a run entered; coverage is a statement about the
artifact, which is also why it is per file rather than per proto (for the 13
files that ship fallback or hybrid the artifact's proto tree is not in
field-for-field correspondence with the original's).

**Block coverage survives as a diagnostic**, reported as an interval because
it is a bound, not a value: the upper bound credits any block sharing an
executed line, the lower counts only blocks whose entry line names exactly one
block. For `snr_lib` that is **[0.3509, 0.9123] of 57 blocks, 32 of them
sharing an entry line**. It never enters the ledger. (It was [0.386, 0.9474]
until M5 task 10 round 1 re-timed the sequences — see below; two blocks were
reached only by the old timing's accident of holding the tail key across a
`wait`, and three longer honest variants were measured without recovering
them.)

`LINE_SHIFT = 2000` blank lines are prepended for the coverage run so a probe
line number can never collide with a target one — the probe classifies each
distinct line once (a `getinfo` per line event costs 8×: 0.31s vs 2.39s on
6,000,004 events), and without the shift a line number first seen from the
probe's own source is filed as foreign for the rest of the run. Measured on a
602-line fixture where every line executes: **60 lines lost, 10.0%**, exactly
the probe's own executed ranges. This affects only the block diagnostic now,
but the diagnostic is quoted here, so it has to be right.

### The coverage run's backstop is a LINE budget, not an instruction budget

`INSN_BACKSTOP` is **structurally unreachable** under a line hook, and this
was found by review rather than by construction. With `LUA_MASKLINE` set,
`lvm.c::traceexec` fires the count hook only when `L->hookcount` is exactly 0
at its own entry — but the line hook's Lua body runs with
`L->allowhook == 0` (`ldo.c::luaD_callhook`), where `traceexec` still calls
`resethookcount` while `luaD_callhook` silently does nothing. With a hook body
executing on most instructions the zero-crossing almost always lands inside
it. Measured on this VM over 3,000,003 line events: mask `""` → **6** count
events, mask `"l"` → **0**, mask `"lc"` → **0**.

Before the fix, `function main() local x = 0 while true do x = x + 1 end end`
returned `INSN` under `tail=` and ran to the 120s subprocess timeout under
`tail=;cov=1`. The coverage hook now carries `LINE_BACKSTOP = 20000000` line
events instead — a genuine bound, since every line event costs at least one VM
instruction, and ~26× the heaviest measured coverage run (`snr_graphic`,
749,049). Both constants are pinned as unconditional literals, with a
test-only env shrink.

### Why it is a second Lua file

`scripts/probe_keyseq.lua` duplicates most of `probe_behaviour.lua`. That is
deliberate: the L1.75 gate's traces are frozen artefacts (two divergences
pinned as exact byte pairs, reach asserted as counts), and this probe changes
the trace format. Threading both formats through one file would put the L1.75
evidence at risk of every edit made for L2.

What is pinned, stated as a measurement rather than as "the two cannot drift":
`difflib` reports **297 identical lines** between them, 245 of those in runs of
five or more (re-measured this session; the review's 299/247 was taken before
round 1 edited both files). `test_the_semantically_shared_parts_of_the_two_probes_are_identical`
pins every region whose drift would make an L2 result incomparable with the
L1.75 evidence that justified it — the budget constants, the whole
stub-return policy, the proxy construction and metamethod blocks, and the
determinism overrides — comparing code only, so comments are free to differ.
It does **not** pin the serialisers or the recorder.

### Running it

```bash
PYLUADEC_CORPUS_DIR=<corpus> uv run python scripts/probe_keyseq.py
```

A clean run prints one line per authored file and
`L2: 1/5 authored file(s) granted, 4 refused as expected`, exiting **0** —
the expectation lives in `EXPECTED_VERDICT` so the CLI and the gate cannot
disagree on what "pass" means, the mistake the L1.5 CLI shipped with.

The badge lands in the ledger (see the field table above) and on the dashboard
(`L2 files driven`, `L2 share (rows)`, `L2 share (occurrences)`, `L2 badge per
file, min/median/max` — per FILE, because a row-basis median is dominated by
whichever driven file has the most protos — plus a refusal histogram).
`scripts/ratchet_diff.py` treats a lost grant (`l2-lost`) or a dropped
coverage (`l2-coverage-downgrade`) as regressions; a newly granted or improved
badge is not.

Cost, measured 2026-08-12 (three interleaved runs each way, the L2 block
short-circuited for the second arm): **0.19s** added to `scripts/run_corpus.py`
— 10.03/10.14/10.14s without, 10.29/10.31/10.37s with. It is cheaper than
before the backstop (0.66s) because four of the five files now refuse
statically, before any coverage subprocess runs. The whole
`tests/test_l2_keyseq.py` module — 103 tests including the corpus arm, the
twelve laundering routes and three fault injections — runs in **2.0s**.

## The quality score — the predecessor's metric, ported (M5 task 3)

`src/pyluadec/verify/semantic_score.py` is a mechanism-equivalent port of
`/root/pyluadec/pyluadec/semantic_eval.py`, the metric that produced the
predecessor's stated `avg_score 0.997` — the number spec §1 goal 4 and §7's
M5 row committed us not to regress against. It had never been run against our
output before this task, because it lives in the predecessor's 32-bit
in-process bridge pipeline.

**Since 2026-08-12 the 0.997 is M6's exit, not M5's** (spec §2 decision table;
the arithmetic is below and in `docs/reports/m5-quality.md`). M5 exits at
**0.968833** against a floor of 0.96 asserted by
`tests/test_m5_exit.py::test_m5_exit_quality_no_regression`, which is the one
test in that file that re-derives rather than reading the committed ledger.

**It is an evaluation instrument and gates nothing.** `verify/normalize.py`
and `verify/certify.py` decide what is `L3`; a high score cannot promote
anything, and no test in the tree lets it. What it adds is the one thing
certification structurally cannot give: certification is a *predicate*, so it
can say a proto does not match but not how far off it is. The score grades the
non-matching ones.

Definition, in one paragraph: per proto, nine component similarities —
`cfg_reachable` 0.10, `cfg_all` 0.05, `opcode_family` 0.20, `global_reads`
0.10, `global_writes` 0.10, `call_targets` 0.20, `call_shapes` 0.10,
`return_arity` 0.05, `const_fingerprint` 0.10 — where the counter components
are `1 - L1(a,b)/(|a|+|b|)` and the two CFG ones are 0/1 on an exact shape
triple. The file score is the `code_len`-weighted mean over protos. Every
weight, threshold and signature field is transcribed from the predecessor;
the module docstring lists the eight places the port had to choose between
reproducing their *comparison* and reproducing their bridge's *losses*
(`svalue()` NUL truncation, `py::str` on non-UTF-8, the `VARARG_HASARG`-only
vararg flag, the debug-section-derived upvalue count), with the corpus
measurement that shows each choice cannot move this corpus's number.

### Running it

```bash
PYLUADEC_CORPUS_DIR=... uv run python scripts/quality_score.py
PYLUADEC_CORPUS_DIR=... uv run python scripts/quality_score.py --all --strict
```

Read-only: it writes nothing, and in particular never touches
`corpus/ledger.jsonl`. A full sweep costs **11.4s** wall (2026-08-12), which
is why it is a CLI and not a suite member;
`tests/test_semantic_score.py::test_corpus_smoke_three_small_files` is the
committed arm (0.01s in-suite) and only pins that the path works.

### First measurement — 2026-08-12, at M5 task 3

```
files scored      : 229
avg_score         : 0.935579
below 0.997       : 17
on M2 fallback    : 17  (avg 0.132206)
structured        : 212  (avg 1.000000)
status            : pass=212  warn=0  fail=17
```

**Round-1 correction (2026-08-12):** the first version above had a real port
bug (D1 in the module docstring — a prefix-scheme choice, not a bridge-loss
choice, changed `_table_access_tag`'s prefix test's verdict on 60 GETTABLE
sites across 9 files). Fixed; re-measured:

```
files scored      : 229
avg_score         : 0.935633
below 0.997       : 17
on M2 fallback    : 17  (avg 0.132945)
structured        : 212  (avg 1.000000)
status            : pass=212  warn=0  fail=17
```

**0.935633 is the corrected headline** and supersedes 0.935579 everywhere
below; the two numbers above are kept side by side rather than silently
overwritten so the fix's effect is visible. It does not change any
conclusion in this section: still does not clear 0.997, still 17 files below
threshold, still the same 17 files.

**It does not clear 0.997.** This is the honest state of the milestone at M5
start, and it is the baseline every later re-measurement is compared against.

**M5 task 4 moved it to `avg_score 0.946390`**, with 14 files below threshold
(avg 0.123101) and 215 structured at exactly 1.000000 — three of the 17
fallback files (`snr_e1_10_s.lua`, `snr_s2_10_s.lua`, `snr_s6_10_s.lua`)
left fallback. **M5 task 5 moved it to `avg_score 0.950580`**, with 13 files
below threshold (avg 0.129456) and 216 structured at exactly 1.000000 — one
more file (`snr_lib.lua`) left fallback. **M5 task 6 (hybrid emission) moved it
to `avg_score 0.968833`**, still 13 files below threshold but split 6 hybrid
(avg 0.816791) / 7 whole-file fallback (avg 0.137429); tasks 7–12 did not move
it and were not supposed to, and the figure was re-measured at task 12 and
reproduces to six decimals. **That is where M5 exits, and it is where the
milestone's acceptance criterion was re-scoped** — 0.997 is M6's exit now, by
the human partner's decision of 2026-08-12, recorded in the spec's §2 decision
table. The arithmetic that closed the original gate off: 216 files at exactly
1.000000 means the other 13 must average ≥ 0.947, and converting all 7
remaining fallbacks to hybrids *at the measured hybrid quality* reaches only
0.9896. The current distribution, the per-file table for the 13, and the five
volume bases are in `docs/reports/m5-quality.md`.

The block below still describes the
M5-start state; the shape of the distribution is unchanged, only the counts.

The distribution is as clean as it could be: every one of the 212 files whose
root certifies `L3` scores **exactly 1.000000**, and every one of the 17 files
below the threshold is exactly a file that ships M2 fallback. So on today's
corpus the score is, at file granularity, a monotone function of the
certification verdict — it currently discovers no defect certification missed,
which is a real (if negative) result about the instrument, and the reason it
still earns its place is the grading it does *inside* the failing 17:

| file | score | file | score |
|---|---|---|---|
| `snr_lib.lua` | 0.040488 | `snr_s4_10_s.lua` | 0.146561 |
| `snr_fragment_main.lua` | 0.044070 | `snr_novel.lua` | 0.147137 |
| `snr_mainmenu.lua` | 0.075326 | `snr_s2_10_s.lua` | 0.151972 |
| `snr_memory.lua` | 0.104022 | `snr_s6_10_s.lua` | 0.153946 |
| `snr_story_main.lua` | 0.106464 | `snr_music.lua` | 0.154160 |
| `snr_graphic.lua` | 0.126425 | `snr_common.lua` | 0.174230 |
| `snr_s3_10_s.lua` | 0.139208 | `config.lua` | 0.180702 |
| `snr_s1_10_s.lua` | 0.142074 | `snr_e1_10_s.lua` | 0.230723 |
| `snr_s5_10_s.lua` | 0.142553 | | |

All 17 are `status=fail` with `drift_type=semantic_candidate`. Re-measured
2026-08-12 (round 1): every one of the 17 carries exactly three *kinds* of
hard issue — `function_shape_mismatch` and `proto_path_set_mismatch` (one
each, on all 17: the fallback lifts every nested function to a top-level
`__pld_F` factory, so the recompiled proto *tree* has a different shape, not
merely different code) plus a variable count of `signature_mismatch@<path>`
entries, one per proto whose `numparams`/`is_vararg`/`subproto_count` drifted.
That count ranges from 1 (`config.lua`) through 3 (`snr_lib.lua`) to 89
(`snr_common.lua`), giving hard-issue totals of 3, 5, and 91 respectively for
those three files. No file has a fourth kind.

### What the number implies for the exit gate — arithmetic, not opinion

229 × 0.997 = 228.313. The 212 structured files already contribute 212.000, so
the remaining 17 must contribute **≥ 16.313, i.e. average ≥ 0.9596**. They
average **0.1329** today (round-1 re-measurement; was 0.1322 before the D1
fix — this ratio is independent of the 212's contribution, so the fix moves
it slightly). There is no partial-credit path: a fallback file scores
around 0.13 whatever else is true of it, so **reaching 0.997 requires
essentially all 17 to start certifying** (or a comparable structural fix that
makes their artifact stop being a pc-dispatch state machine). Closing 16 of 17
leaves the average at (212 + 16 + 0.1329)/229 = **0.9962** — still short,
same as before the fix to four decimal places. This is the sharpest statement
of what Tasks 4–7 have to deliver.

**Re-derived at M5 task 12 (2026-08-13), on the post-hybrid population — and
this is the arithmetic the human partner's re-scope decision rests on.** 216
files now contribute 216.000, so the remaining 13 must average **≥ 0.947** for
the corpus to reach 0.997. They average **0.450980** (6 hybrids at 0.816791, 7
whole-file fallbacks at 0.137429). The partial-credit path that did not exist
at task 3 now does — a hybrid scores far above a fallback — but it does not
reach: converting all 7 remaining fallbacks to hybrids *at the measured hybrid
quality* gives (216 + 13 × 0.816791)/229 = **0.9896**. So 0.997 requires
essentially every file at ~1.0, i.e. the reconstruction residual closed, which
is M6 agenda 1. **Nothing here argues the gate should be weakened; it argues
which milestone owns it.**

### Calibration — why the number is believable

`tests/test_semantic_score.py` holds the two properties that make it
trustworthy, both proven by neutering (2026-08-12):

- **No false alarms.** A proto scored against itself is 1.0 on every
  component. Neuter: mistranscribe one weight (`cfg_all` 0.05 → 0.04) →
  `test_identical_protos_score_one_on_every_component` fails. This is what
  makes "212 files at exactly 1.000000" mean something.
- **Not blind.** The M2 fallback of a chunk that *does* certify scores
  **0.276364**, far under 1.0. Neuter: `_counter_similarity` returns a
  constant 1.0 → the score rises to **0.904545** (the two CFG components are
  not counters and keep firing, which is why blinding it does not reach 1.0)
  and `test_m2_fallback_of_an_l3_chunk_scores_below_one` fails against its
  `< 0.5` bound. That bound was set from both measurements rather than picked
  round; `< 0.9` would have let the neuter pass by 0.0045. Had the metric
  been unable to see the fallback, the corpus average would have been
  measuring almost nothing — the fallback files are **46.1%** of the corpus
  by instruction volume.

The first test additionally asserts its own non-vacuity: an all-empty Counter
pair scores 1.0 for free, so the sample must light up every counter and at
least one back edge.

### A brief number that did not reproduce

The M5 plan describes the 17 fallback files as "47.6% of the corpus by line
volume". Measured five ways on 2026-08-12, none lands on 47.6%: decompiled
output lines **80.1%** (120246/150144), bytecode instructions **46.1%**
(99289/215218), bytecode bytes **42.1%**, original source lines via
`lastlinedefined` **42.7%**, proto occurrences **40.2%** (781/1944). The
closest basis is instruction volume at 46.1%. Nothing in this task depends on
the figure; it is recorded so the next reader quotes a measured one. The other
two figures in that description — 17 fallback files and 212 structured — both
reproduce exactly.

**Re-measured after hybrid emission (M5 task 6, 2026-08-12)**, on the two
bases that are cheap to reproduce from the committed ledger and
`build/decompiled/`:

| basis | M4 close (17 files) | M5 task 5 (13 files) | M5 task 6 (7 files) |
| --- | --- | --- | --- |
| bytecode instructions shipping as a state machine | 46.1% | 34.4% | **14.2%** (30584/215218) |
| proto occurrences shipping as a state machine | 40.2% (781/1944) | 29.1% (565/1944) | **10.1%** (197/1944) |
| decompiled output lines in whole-file-fallback files | 80.1% | — | **37.0%** (31884/86228) |

The line-volume row is not comparable across columns the way the other two are
(the artifact's own text changes when a file stops shipping a state machine),
which is why the middle column is blank rather than guessed.

**Re-measured at M5 task 12 (2026-08-13), after output surface v2.** The first
two rows are unchanged to the digit (14.2% = 30584/215218, 10.1% = 197/1944 —
tasks 7–11 moved no proto). The third row is **37.3% (31884/85588)**: the
numerator is identical and the *denominator* fell by 640 lines, because task 7's
`elseif` folding removes one `end` per collapse from the structured files and
the whole-file-fallback files are untouched by it. A ratio whose denominator
moves under a presentation change is exactly why this row carries the caveat
above.

**Predecessor-line basis, added here because it is the one M4 quoted and the
one that kept getting disputed:** the 7 whole-file fallbacks are **8888/57998 =
15.3%** of the predecessor's shipped text, the 6 hybrids another 21.8%, so the
216 fully-structured files are **62.8%**. M4's "47.6%" for its 17-file set
reproduces exactly on this same basis (27623/57998). The five bases disagree by
a factor of six on the fallback column, so quote the denominator or quote the
per-occurrence figure instead. Full table: `docs/reports/m5-quality.md` §2.

## Relationship to the fallback runbook

`docs/runbooks/decompile-pipeline.md` documents the M2 fallback path and stays
authoritative for it. The fallback is **not** deprecated and is not going away:
it is the floor, and since M5 task 6 it is also what fills the holes in a
hybrid. Today **7** of 229 files ship it whole (137 at M3 close, 17 at M4
close, 13 before this task) and another 6 ship it for 197 individual protos
inside otherwise-structured files.

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

## The warranty corpus and the two-factor grade (M7)

`corpus/final/` (229 files, committed, generated) is the merged corpus the
localization project translates against; `corpus/warranty.jsonl` (one row per
file) records the per-occurrence two-factor grade and the selection verdict
that produced it. Both are **whole-cloth generated** by
`scripts/warranty_build.py --all` (a job: trigger = any ledger/panel/recert
movement and at close; refuses to write on a pin-table opcode violation or a
selection error) and regenerate byte-identically
(`tests/test_warranty.py`, corpus-gated on both env vars). **Authority for
every number and decision lives in `docs/reports/m7-warranty.md`** — this
section is a pointer, not a second record.

The grade vocabulary, in one breath each:

- **Factor T** (`predrecert.t_grade`, one place, both sides):
  `T3` = certified `L3` and ships structured text; `T2` = the hybrid
  contract compared this proto's own fields; `T-` = **ships fallback text**
  (shipped-first order, amended 2026-08-16 — a level never outranks a
  fallback shipment; see the report's §1 addendum for the 703 phantom
  grades the old order created).
- **Factor E**: `id` for ours (constructive identity — our text's source
  bytecode IS the original); for pred, the invariant panel
  (`corpus/observation/panel.json`) with `wm` (M6 walkthrough + driver
  validation) replacing the grade of exactly the six repaired protos.
  Order `id > wm > panel-pass > panel-pinned`; `panel-unpinned`
  disqualifies the pred side.

Selection (`warranty_build.select`, spec §6): lexicographic `(T, E)`, tie
→ ours. Two structural facts worth knowing before quoting outcomes:
**Factor E never decides a selection** (with ours at `id`, pred wins only
on a strict T advantage — 12 of 36 combinations, pinned as a test), and
**the merge is degenerate for a diagnosed reason** — 228/229 pred roots
fail re-certification, 163 of them (71%) on mechanism F (boilerplate dead
locals failing the root `maxstacksize` comparison), so all 229 files ship
ours and `corpus/final/` is byte-identical to our
own product. The warranty's value is the recorded per-occurrence evidence,
not the merging.

**Reading a `T-` row**: ours `T-` (64 occurrences) is the M2 floor —
semantically exact by construction, compileable, L1.5/L1.75-probe-covered
— while pred `T-` means no positive verification; the schema does not
distinguish the two (M8 schema candidate, recorded in the generator's
docstring). **Readability residual**: 52 lines of game dialogue ship as
`__pld_R[n] = "<Japanese>"` (49 `snr_common`, 2 `snr_story_main`, 1
`snr_novel`) — encoding-complete but without call context; pinned by
`tests/test_m7_exit.py`, fix routed to M8.

### The M8 campaign census (tasks 2–3 landed; tasks 4–5 Step-1 measured)

**State after M8 tasks 2+3 (2026-08-16, `927fbcd`): 19 non-`L3` rows — 13
own + 6 inherited — ALL `mismatch:`** (the `structure:` and `reconstruct:`
families are extinct: task 2's arm-trailing empty-then recognizer fix took
`main_71` + root past `build_sir`; task 3's empty-tail clamp fix certified
`snr_memory`'s whole file and `snr_graphic:main_3`). `L3` **1459/1478
unique (98.7%) / 1925/1944 occurrences (99.0%)** — shipped-structured
occurrences are a DIFFERENT quantity, **1882/1944** (do not conflate the
two; IMP-3/§4's word collision); products **223 fully structured / 4
hybrid / 2 whole-file fallback**; ratchet vs `72cb6a8`: 3 upgrades, 0
downgrades.

**The tasks 4+5 Step-1 census, measured 2026-08-16** (first divergence per
own row, exact-wrapper recompile; the reason field alone names only the
FIRST mismatch — the full field lists below come from
`ProtoCert.mismatches`):

| rows (own) | first divergence | mechanism family |
|---|---|---|
| `main_25` pc1, `main_24` pc1, `main_71` pc7 | `NEWTABLE` hash-hint C differs (2v3, 1v3, 10v0) | **K1 hint-position** — constructor literal vs statement-build choice |
| `main_77` pc1, `snr_novel:main` pc1 | `NEWTABLE` vs `LOADK` ordering (+ pool reorder) | **constructor layout** — ours builds statement-first, orig literal-first |
| `snr_story_main:main_3` pc290, `snr_graphic:main_4` pc355 | JMP offsets + 8/13 extra instrs (+ pool reorder) | **expression layout** — statement-order divergence cascading |
| `main_77_0` pc3 | `SETUPVAL` B=1 vs B=0 (5-instr proto) | the documented `u0, u1 = 1, 0` multiple-assignment residual (`tests/test_express_residual.py`) |
| `mainmenu:main_7`, `main_25_4`, `main_76_2` | extra `MOVE`s (+4/+14/+6), maxstack above orig | **materialization surplus (M)** — callee/arg reuse slots materialized where orig staged (`local l1_3 = layerClip; l1_3(l1_4, ...)` vs direct call) |
| `main_74_18`, `snr_music:main` | maxstack BELOW orig **plus** code/pool co-mismatches (58-item pool reorder on music) | slack + pool order — **no maxstacksize-only rung can certify either row** |

**A plan hypothesis corrected by measurement**: the M8 plan's table read the
8 maxstacksize rows as "K1 (5) + dead-slack"; the measured split is
M-family 3 + slack-with-co-mismatch 2, and the K1 rows live among the
`mismatch: code` population (hint is a code field). Consequence for Task 6:
**no single rung alone certifies any remaining row** — the L3.2 pool-order
rung would pair with music:main's maxstacksize clause, and K1 needs the
L3.3 hint rung; the M-family and layout rows are emitter-side work, not
rung work.

### The M-family diagnosis, deepened (M8 tasks-4/5 campaign, 2026-08-16)

`snr_mainmenu:main_7`'s +4 `MOVE`s (and, by signature, `main_25_4`'s +14
and `main_76_2`'s +6) decompose as: `local lD_R = <cond operand>` (the
condition-tree path materializes a register whose defs are ALL graded
temp — measured on main_7: (190,8), (194,8), (198,8), (207,8) every one
in `temp_defs`; the materialization is the RECONSTRUCTOR's doing, not the
classifier's), then the arm's later callee write to the same register
hits `write_reg`'s `declared`-wins rule and materializes as
`lD_R = layerMoveAlpha`, and calling through a local makes luac `MOVE`
the callee to the call base — one `MOVE` per site, four sites in main_7
(the identical menu-rebuild block × 4 gate sites). The original has no
local there: the condition reads `u1.library` via two SEPARATE defs
(190/194, each read once by its own compare), and the callee is a direct
global call. Scope release does not help (`local`, reassign and call sit
in the SAME if-arm). **Solved to the last link (same campaign, next round —
measurement-first, two hypotheses died on the way):** NOT the condition
tree (its `cond_operand` pops inline), NOT `_named_local` (all three
disjuncts false at the four sites, instrumented), NOT the plain
mention-list half of the skipped-kill veto (the JMP@197 successor's next
r8 mention is a WRITE at 468, read only at 469). The firing path is
`_merge_veto_skipped_kill`'s **open-read clause**: the inter-site region
[253, 468) holds four `CALL`-style `R[5..top)` open reads (pcs
385/405/425/445, base 5) and no r8 write, so the model cannot exclude
that the killed value survives to become an open-call argument -- the
veto fires, (195,8) grades local, the condition operand materializes,
and `write_reg`'s declared-wins then materializes the arm's callee
through the same slot (`l1_8 = layerMoveAlpha; l1_8(...)`) for the +1
MOVE per site. Whether the open call's runtime top ever reaches r8 is
statically undecidable in general -- this is the veto's documented
conservatism, not a bug in it. The design question for the fix: the
ORIGINAL's condition operand was dead at its compare and r8 FREED for
the callee (freereg reuse), while our `declared` is whole-function and
`close_scope` cannot see the release (same arm). Candidate directions:
(a) couple `declared` release to the freereg model's statement-boundary
drain (the discipline already knows the slot re-became stack), or
(b) prove the open reads' top < 9 from the callee-side emission and
narrow the clause. Both are design changes to load-bearing guards --
own review round each, not a campaign afternoon.

**Priority elevated to GATE-CRITICAL (controller review, 2026-08-16):**
`snr_mainmenu` is 3.5598x -- the corpus's worst footprint, on a
permanently loaded script (the original heap-risk case), and the ENTIRE
1.5x exit ceiling now rests on three single-own-row files:
`snr_mainmenu` (M-family, `main_7`), `snr_graphic` 1.9509 (`main_4`,
expression layout), `snr_story_main` 1.6956 (`main_3`, expression
layout). The direction decision should be made NOW, not at Task 6. Of
the two candidates: (a) freereg-coupled `declared` release is the
PRINCIPLED fix -- it addresses the actual gap (the model cannot see a
same-arm slot release that the original's freereg discipline performed),
generalizes to any future shape where a materialized local's slot is
re-staged, and can be neuter-tested against the discipline's own
statement-boundary drain; (b) open-read narrowing by top-provability is
a special-case argument (the callee-side emission proves top < 9) that
leaves the whole-function `declared` gap in place for the next shape.
Recommendation recorded: (a), with the review round it requires.

**Correction after the implementation-前 review (2026-08-16, measured):
neither (a) nor the reaching-def refinement saves THIS row.** The
earlier BFS targeted the plain-clause read (469) instead of the
open-read sites; re-run against pc 385: def@195 REACHES the open reads
on the loop-exit path ([253,468) contains no r8 write), so a
reaching-def refinement of the veto changes nothing here, and (a)'s
declared release only addresses the SECOND materialization (the
callee's), whose byte-exact alternative (calling the global directly)
compiles into a different register (the materialized local occupies r8
in our text's frame). The byte-exact spelling requires what the
original did: `u1.library` evaluated TWICE (two def pairs), i.e. a
duplicated GETTABLE read that STRICT effects forbids and the corpus
cannot license for an upvalue chain (the M4 NO_METAMETHOD opt-in
covers script-built tables only). This row therefore needs either a
partner decision (a corpus-informed double-eval opt-in) or stays with
recorded attribution -- flagged for the Task 6/stop-loss discussion,
NOT silently absorbed. The other two gate-critical rows
(`snr_graphic:main_4`, `snr_story_main:main_3`, expression layout) are
independent of this.

**Direction (a) was then measured and REJECTED (2026-08-16, controlled
experiment, reverted the same minute).** [The K1 count-cap experiment of
the same session met the same verdict: see below.] The proposed rule -- "a
temp-graded definition stages even over a `declared` slot, because a
staged value still enters `_pending` (reads pop it inline) and temp
means exactly one read, so no second name-read can exist" -- moved the
corpus to **35 shipping regressions** (`snr_common:main_27` structured
-> fallback among them; 1463 -> below, 8 hybrid files vs 4). The
soundness argument misses at least one path (most likely: reads the
discipline attributes to the NEW def are, in the reconstructor's text,
name-reads of the OLD local when the old value's expression was already
consumed by an inline pop in the OTHER order -- the per-def single-read
count and the env's pop order disagree across branches). `declared`
-wins is load-bearing for temp defs exactly as its docstring says; a
finer release needs the reaching-def review round it was already
assigned, not a one-line inversion. Experiment reverted; ledger
verified byte-identical to pre-experiment (`ratchet_diff` clean, suite
batch green).


### The K1 count-cap experiment: rejected 157-3 (same campaign)

The int2fb boundary was RE-MEASURED (2026-08-16, vendored luac): raw C
is EXACT for literal hash counts **1..16**, ambiguous at 17 ({17,18}),
collapsed from 18 on. This corrects the M7-task-9 note twice over: "past
7 is inexact" understates the exact range, and its worked example "a
15-field literal decodes to 14" does not reproduce (15 -> 15). Pinned as
`test_int2fb_exactness_boundary`.

The tempting fix -- cap the fold at the original's hint count, close the
ctx there, dispatch further SETTABLEs as statement stores -- was
implemented and **regressed 157 rows** (`snr_common:main_74` structured
-> fallback among them; whole-file fallback reappeared on 3 files). The
failure mode is the SAME one M7 task 9's first count gate hit and
documented: the early close reorders the value staging (the regressed
emission puts the outer literal's SETTABLEs ahead of a nested table's
own NEWTABLE staging -- the fold order and the statement stream no
longer compose). The cap was reverted the same session; ledger verified
byte-identical post-revert. The K1 cluster therefore stays with the L3.3
masking rung (a partner petition) or a fold-order-preserving split
(some signal for the constructor's END other than the count -- none is
known). Current refusals pinned red by
`test_literal_statement_split_is_a_recorded_gap`.

### The campaign's Step-1 census is COMPLETE (2026-08-16)

`snr_story_main:main_3` diagnosed last: first divergence pc307
`GETGLOBAL 12` vs `MOVE 12,11` -- our text assigns each callee to the
busy slot's local and calls through it (`l1_11 = keyPlaySE;
l1_11(seName.circle)`), where the original loads the callee fresh per
statement (`keyPlaySE(seName.circle)`, +8 instructions, const-pool
reorder). **All three gate-critical rows share this one root** with
`snr_mainmenu:main_7` and `snr_graphic:main_4`: the whole-function
`declared` merges a busy slot's per-statement lifetimes, and the
original re-evaluates (callees, upvalue chains) fresh per use. Rename
recorded: the "M-family" is really the **busy-slot family**.

**Every remaining own row is now attributed** (the spec §5 stop-loss
form, attribution-complete): busy-slot family ×5 (`main_7`, `main_4`,
`main_3`, `main_25_4`, `main_76_2`); K1 hint ×3 (`main_24`, `main_25`,
`main_71` -- L3.3 rung or fold-split, count-cap falsified); slack+code
×1 (`main_74_18`, maxstack BELOW original plus a code co-mismatch); +
6 inherited roots that dissolve with their descendants. Three fix
directions have been experimentally falsified with zero spillover
(declared-inversion 35 regressions; count-cap 157; reaching-def
refinement moot -- the value reaches the open reads). The paths that
remain are PARTNER DECISIONS at Task 6: the K1/L3.3 rung bundle, the
busy-slot ruling (reaching-def review round vs a corpus-informed
fresh-eval opt-in), and `main_74_18`'s disposition.

Also recorded from the same session: a NESTED-literal inversion gap
(inner literal's values read the outer's staged TableExpr; the outer's
materialization lands after the inner's statement -- the printed text
reads a GLOBAL). Certification refuses it, so it cannot ship wrong;
corpus census: no remaining row names it. Pinned by
`test_nested_literal_inversion_is_a_recorded_gap`.
## The propose-and-certify channel (M8 wiring, 2026-08-18)

A hand-written source **proposal** for a proto the reconstructor cannot
print, certified through the **unmodified** ladder and spliced into the
chunk at its CLOSURE site. Partner-approved 2026-08-18; the campaign
that produced the current nine proposals is
`docs/reports/m8-strategy-survey-fable5.md` §9, the wiring handoff is
`docs/reports/m8-handoff-proposal-channel.md`.

**The flow.** `structure/proposals.py` holds the pinned `MANIFEST`
(9 entries; adding/removing one is a deliberate edit held by
`tests/test_proposal_channel.py`'s enumeration pin) and the inliner: a
boundary-aware, string/comment-tracking scanner (no `re` -- the package
ban) that (1) rebinds the wrapper's `u<digits>` upvalue references to
the enclosing scope's own identifiers (`closure_parts`' pseudo-
instruction names), and (2) shifts `l<k>_` local prefixes by the site
depth -- the **shadow-capture fix**: the wrapper spells its locals
`l1_*`, and spliced at a depth-2 site an unshifted `l1_0` shadows the
very name `u0` was renamed to, silently turning a capture into a
self-reference (measured as `nups` mismatches on all three depth-2
sites in the first wiring round). `emit_certified_chunk`'s proposal
tier sits between root certification and hybrid: print the tree with
proposal bodies at the **refusing** sites only (the P4 filter lives in
`_proposal_round`'s dict narrowing -- the controller review's IMP-1
found the first wiring passed the dict through unfiltered, so a proposal
would have displaced a working reconstruction while the ledger said
`structured`; the filter is load-bearing and pinned by a
marker-comment test), compile with the real oracle, and compare with
the untouched ladder and **zero excluded paths**. Any error anywhere
refuses the chunk; the caller falls to hybrid/whole-fallback exactly as
before.

**Provenance (P2) and the ledger.** `shipped` gained the value
`"proposal"` (15 occurrences today, all in the four formerly-hybrid
files); a proposal-tier chunk records `L3` at the round's rung for
EVERY proto in the tree -- the whole-tree compare covered ancestors of
substituted sites too (the pre-hybrid "root certified implies every
descendant" convention, applied to the new tier). The reconstructor's
own per-proto verdicts are unchanged and internal; `ratchet_diff.py`
installs `structured > proposal > fallback` with `structured ->
proposal` the `proposal-mask` downgrade (the reconstructor used to
print this proto itself -- the P4 move the ratchet exists to see).

**What the channel is NOT.** It is not a comparator change --
`verify/` is untouched, `LADDER_VERSION` unchanged; certification went
through the same door it always had. It is not a return of the retired
pass registry (spec §2): no apply/rollback, only propose + the existing
certify. And it is not the fallback: proposal text is certified text,
so warranty `t_grade` grades it by level (the shipped-first `T-` arm is
for uncertified state machines). The census sections above are kept as
the history of the mechanisms the channel superseded; the residual
population as of this wiring is **empty** -- 1478/1478 `L3`, zero
fallback occurrences, `corpus/final/` carries no `__pld_` marker, every
footprint 1.0, and file-level byte identity (mod lineinfo) is 229/229.

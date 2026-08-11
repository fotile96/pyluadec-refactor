# Phase 4 (M4): Loops, Long-Tail Structuring, and Verification Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Structure the loop shapes that keep ~25% of unique protos in fallback (`while true` event loops, rotated generic-for, repeat, TESTSET and/or idiom), port the predecessor's semantic regressions as standing gates, and harden every verification instrument M3 left with a known gap — raising L3 certification from 75.2% to >85% of unique protos without weakening any gate.

**Architecture:** Extends the M3 pipeline (`ingest → lift → cfg → sir.build → express.reconstruct → emit.lua → certify_l3 → ledger`) in place. New SIR region nodes (`WhileTrue`, `Repeat`, `EndIter`) slot into the existing recognize-or-refuse discipline; the certification gate remains the sole arbiter of what ships. No new subsystem is introduced: the spec §4 pass registry is **deliberately deferred to M5** (decision confirmed by the human partner 2026-08-11 — it has zero client passes today, and the certification gate already provides per-function verify-commit/rollback discipline; M5's confession-ranking-driven idiom passes are its first real customer).

**Tech Stack:** Python 3.13 (uv), pytest (+pytest-timeout), vendored Lua 5.1.5 dual-width oracles (`luac_sz4`/`lua_sz4`), pybind11 ingest bridges. No new dependencies.

## Global Constraints

Copied from CLAUDE.md, the overall spec, and standing directives from the human partner. Every task's requirements implicitly include this section.

- **Certification must never be relaxed to raise the number.** `verify/normalize.py` (`NORMALIZATIONS`, `LADDER_VERSION`, `compare_protos`, `_cmp`), `verify/certify.py`'s comparison logic, and `certify_proto` may only be tightened. Any new ladder rung needs its own standalone soundness argument (argued from which fields `_cmp` still compares, checked against vendored source) and a `LADDER_VERSION` bump. Raising the L3 rate by weakening the gate is the one failure mode that would invalidate the milestone.
- **`corpus/golden/` is a read-only archive.** Never regenerated — a bug in the new code would silently become the baseline.
- **`vendor/` Lua sources stay pristine**; all modifications go through `native/patches/*.patch`. Reading `lparser.c`/`lcode.c`/`lvm.c`/`ldebug.c` to adjudicate semantics is expected; modifying them is forbidden.
- **All bytecode-derived strings are `bytes` on the Python side, never decoded**; number constants carry their original 8-byte payload. Corpus constants are Japanese game text and frequently non-UTF-8 — the predecessor crashed on exactly this.
- **`structural_hash` must not change** (`verify/ledger.py` — the ledger's primary key, 1478 committed entries).
- **`corpus/ledger.jsonl` may only be regenerated wholesale by `scripts/run_corpus.py`**, never hand-edited. Levels ratchet upward only; `L0` must never appear; the ledger must remain a byte-identical fixed point of its own generator (`tests/test_ledger_ratchet.py`). **M4 expects the ledger to change** — that is the milestone succeeding — but every change is an upgrade, reviewed on purpose, in a commit whose message says which task moved it.
- **Confess, don't guess.** Unrecognizable shapes raise `StructureError` rather than emit plausible output. Uncertified output must not ship as structured source (artifact is structured ⟺ root certified L3 — verified end-to-end at M3 final review, 92/92).
- **Corpus access only via `PYLUADEC_CORPUS_DIR`**, never hardcoded. Corpus-gated tests `pytest.skip` without it (do not change that behavior).
- **Engineering practice (standing directive from the human partner, verbatim):** "在实现过程中，你可看情况插入一些额外的review轮，用于检查是否有滥用regex匹配等不合适的编程风格与工程实践，这些东西最大的问题是可能把单元测试变得极慢，从而阻塞正常的开发流程。" `tests/test_engineering_practice.py` enforces no-`re` over `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}`. Suite is 285 tests / ~29.5s at M4 start; **budget ≤45s at M4 exit** — every task reports the suite time it adds and why.
- **Measurement provenance (M3's hardest-won lesson — five confidently-stated numbers were overturned by measurement in that one milestone, four of them the planner's).** Every number in this plan is marked with how it was measured. Implementers: **re-derive any number you depend on before relying on it; if your measurement contradicts this plan, the measurement wins and you say so in your report.** Every quantitative claim that lands in a document of record must be one you measured in your session or can cite to a file:line/test name.
- **Opcode semantics:** `others/a-no-frills-introduction-to-lua-5.1-vm-instructions.pdf` in the ORIGINAL project (`/Users/fotile96/pyluadec/others/`) takes precedence over official Lua docs. Ground truth for codegen is vendored `lparser.c`/`lcode.c`; for runtime, `lvm.c`.

## Measurement grounding (all taken 2026-08-11 on the M3 merge result, commit `2a759a8`)

Scripts for rows 1–3 are inlined in `docs/runbooks/structured-pipeline.md` § "Re-deriving the three rows". The loop-shape census scripts were session-scratch; Task 1 Step 1 recreates the census as a committed fixture, which is where these numbers get their permanent re-derivation path.

| fact | value |
|---|---|
| L3 certified | 1112/1478 unique (75.2%), 1577/1944 occurrences (81.1%) |
| `build_sir` refusals | 169 unique: **162 with back edges**, 7 acyclic |
| refusal messages | 139 "else-join out of range", 14 "if targets out of range", 8 "unrecognized transfer TESTSET", 8 "unreachable" |
| ~~back-edge kind mix (162 protos)~~ | ~~**144 pure unconditional-JMP-back** (`while true` family)~~ — **RETRACTED 2026-08-11 during Task 1; see the corrected row below** |
| ~~`while <cond>` headers~~ | ~~**0**~~ — **RETRACTED; it is the DOMINANT form** |
| **loop KIND mix (corrected, Task 1)** | Of the 169 refused unique protos: **134 contain only `while <cond>`** (214 loop occurrences), **15 only `while true`** (17 occurrences, and all 15 are blocked by unrelated causes — 7 TESTSET, 3 dead code in an if body, 3 threaded conditional break, 1 other), 3 compare-header-exiting-inside, 17 with no JMP dominance back edge. Corroborated by two independent re-derivations; `_match_while_true` measured to fire **0 times** corpus-wide (7888 calls, 0 matches) |

> **Retraction, and why it matters for how you read the rest of this plan.** The two struck rows were mine, and both were wrong the same way: I classified by the back-edge **opcode**, but a `while <cond>` also closes with a plain unconditional `JMP` — only `repeat` closes with a conditional one. The correct discriminator is the instruction at the back edge's **target**, and it must account for the lift layer's `consumed` pseudo-instructions: a compare instruction *swallows* its following `JMP`, so a naive "block ends with cond+JMP" test never matches. That single bug produced both the original census and my first attempt to re-check the implementer who caught it.
>
> **Consequence:** Tasks 1 and 2 buy **zero** corpus protos on their own. Nearly all of M4's loop value is in Task 3. The sub-rows 15/17 remain **unreconciled** against two later independent runs that got 23/9 by a different route (recorded honestly in `tests/test_sir_while.py`'s census note); the headline 134/214 and the zero-match result are what three parties agree on, and they are what the re-planning rests on.
| distinct back-edge targets per refused proto | 116×1, 24×2, 7×3, 5×4, 10 protos with ≥5 (max 16) |
| "non-natural" pc-retreating edges | ~~21 protos~~ — **RETRACTED 2026-08-12 at the M4 whole-branch review: it is 7**, on every basis (7 unique protos, 7 occurrences, 7 edges), and 7 is also the ceiling because only 7 protos in the corpus contain a `TFORLOOP` at all. The characterization is right — they *are* all rotated generic-for shapes (edge targets the body; the dominating block is the TFORLOOP test) — and so is the conclusion: Lua 5.1 has no `goto`, true irreducibility cannot occur in luac output, and back edges must be defined by **dominance**, not pc order. Only the count was wrong. Live figure: `sir/build.py::_match_while_true`'s docstring |
| TESTSET protos | 16 unique, **all 16 also carry back edges** — loops gate TESTSET work |
| blocked only by a descendant | 139 unique protos build a region tree but fail because a descendant closure doesn't — loop recognition pays super-linearly |
| printed-but-uncertified residual | 58 unique (all differ on `code`; 24 also `maxstacksize`, 11 `constants.len`, 11 a constant; 9 differ **only** in constant-pool order) |
| metamethod machinery in corpus | **zero** — no `setmetatable`/`getmetatable`/`rawget`/`rawset`/`rawequal`/`__*` name appears in any of the 1944 protos' constant tables |
| predecessor's readability baseline | `/Users/fotile96/pyluadec/post_process/input/*.lua` — 229 UTF-8 text outputs of the original decompiler, available on this machine |
| semantic regression sources | `/Users/fotile96/pyluadec/pyluadec/test_semantic_regressions.py` (5 cases), `test_generated_semantic_cases.py`, `test_ir_structure_roundtrip.py` — available on this machine |

Canonical compiled loop shapes (verified with `oracle.compile_source` this session; re-derive with the fixture in Task 1):

```
while true do print(1) end
  1 GETGLOBAL 0 print ; 2 LOADK ; 3 CALL ; 4 JMP sbx=-4 -> 1 ; 5 RETURN
while true do if f() then break end g() end
  1 GETGLOBAL f ; 2 CALL ; 3 TEST ; 4 JMP sbx=1 -> 6 ; 5 JMP sbx=3 -> 9   (break)
  6 GETGLOBAL g ; 7 CALL ; 8 JMP sbx=-8 -> 1  (closing) ; 9 RETURN
local i = 1 while i < 10 do i = i + 1 end          (absent from corpus refusals, still support it)
  1 LOADK ; 2 LT ; 3 JMP sbx=2 -> 6 ; 4 ADD ; 5 JMP sbx=-4 -> 2 ; 6 RETURN
local i = 0 repeat i = i + 1 until i > 5
  1 LOADK ; 2 ADD ; 3 LT ; 4 JMP sbx=-3 -> 2 ; 5 RETURN
```

## What M3 learned that binds every task here

1. **The corpus is a weak oracle.** It misses 6 of 38 opcodes, masked a Critical printer bug, and its denominators exclude the hard cases. Every recognizer task below therefore carries oracle-compiled synthetic fixtures *before* corpus measurements, and every new gate carries a fault-injection test proving it can fail.
2. **State the property, not the mechanism.** Where this plan sketches code, the sketch is a starting point; the binding requirement is the stated invariant (pc-claim exactness, dominance conditions, certification adjudicates). If the sketch conflicts with the invariant, the invariant governs — flag it, don't force it.
3. **Certification is the arbiter of byte fidelity.** luac's jump threading (e.g. an `if` whose join is the loop end gets its JMP threaded straight back to the header) does not need to be simulated — print natural source, recompile, and let `certify_l3` decide. M3's whole 81% was built this way.

## File structure

```
src/pyluadec/sir/regions.py        # +WhileTrue, +Repeat, +EndIter nodes (Task 1)
src/pyluadec/sir/build.py          # dominance-defined back edges; loop recognition (Tasks 1,3)
src/pyluadec/express/reconstruct.py# loop scoping; TESTSET and/or idiom (Tasks 2,4)
src/pyluadec/express/names.py      # freereg residual fixes as measured (Task 6)
src/pyluadec/emit/lua.py           # while/repeat printing (Task 2)
src/pyluadec/verify/certify.py     # strip-mode matching (Task 7)
src/pyluadec/structure/structured.py # strip-mode matching wrapper path (Task 7)
src/pyluadec/lift/effects.py       # TAILCALL writes_open (Task 8); mode-row docs (Task 11)
scripts/probe_behaviour.{py,lua}   # deepened probe (Task 10)
tests/test_sir_while.py            # Task 1
tests/test_emit_while.py           # Task 2
tests/test_sir_loops_longtail.py   # Task 3
tests/test_express_testset.py      # Task 4
tests/test_semantic_regressions.py # Task 5 (port)
tests/test_m4_exit.py              # Task 6, finalized Task 12
tests/test_certify_stripmode.py    # Task 7
tests/test_effects_tailcall.py     # Task 8
tests/test_effects_reconstructor_consistency.py  # Task 9
tests/test_behaviour_probe.py      # Task 10
tests/test_effects_modes.py        # Task 11
docs/runbooks/structured-pipeline.md, m3-backlog.md, CHANGELOG.md, CLAUDE.md  # Task 12
docs/reports/m4-readability.md     # Task 12
```

Task order: 1→2→3→4 (structuring, strictly ordered), 5 (semantic gates, needs while), 6 (re-census + residuals), 7–9 (gate hardening, independent of each other), 10 (probe, wants 7–9 landed), 11 (calibration, independent), 12 (wrap).

---

### Task 1: Dominance-defined back edges + `WhileTrue` recognition in `build_sir`

**Files:**
- Modify: `src/pyluadec/sir/regions.py` (add three nodes + `_CHILDREN` entries)
- Modify: `src/pyluadec/sir/build.py`
- Test: `tests/test_sir_while.py`

**Interfaces:**
- Consumes: `lift_proto(p) -> LirFunction` (`fn.instrs: dict[int, LirInstr]`, `li.ri.{op,a,b,c,sbx,pc}`, `li.successors`, `li.consumed`); `build_cfg`, `immediate_dominators` (CHK; `idom[entry] == entry`); existing `_structure_range(fn, cfg, idoms, pc2blk, lo, hi, break_target)`; `Break` node; `StructureError`; `all_claimed`.
- Produces (Tasks 2–4 rely on these exact names):
  - `regions.WhileTrue(body: Region, closing: LirInstr, claimed_pcs: frozenset[int])` — claims only the closing JMP's pc; body claims the rest.
  - `regions.Repeat(body: Region, cond: LirInstr, negated: bool, closing: LirInstr, claimed_pcs: frozenset[int])` — declared now (frozen dataclass + `_CHILDREN`), recognized in Task 3.
  - `regions.EndIter(claimed_pcs: frozenset[int])` — claims a threaded end-of-iteration JMP (a backward JMP to the current loop's header from inside its body). Prints as nothing (Task 2); certification adjudicates that luac re-threads identically on recompile.
  - `build_sir` recognizes single- and multi-back-edge `while true` loops; `_structure_range` gains a `continue_target: int | None` parameter threaded exactly like `break_target`.

**Binding invariants (govern over any code sketch below):**
1. A back edge is an edge `S → H` where `H` **dominates** `S` (CHK idoms; walk the idom chain, terminating at entry whose idom is itself). pc-retreating order is NOT the definition — the corpus's rotated generic-for shapes are pc-retreating edges that are *not* dominance back edges to their target (the true header is the TFORLOOP block). ~~21~~ **7 protos**, re-measured 2026-08-12; see the retraction in the grounding table above. The invariant is unchanged by the correction.
2. A `WhileTrue` loop is recognized at range position `L` only when: at least one `JMP` at some `S ∈ [L, hi)` has target `L`; `L`'s block dominates `S`'s block; the loop body `[L, S)` is single-entry (reusing `_verify_single_entry`); and every jump leaving `[L, S]` targets either `S+1` (break) or a `RETURN`/`TAILCALL` inside. `S` is the **last** such JMP; earlier JMP→L sites inside the body become `EndIter`.
3. pc-claim exactness is unchanged: `all_claimed(region) == set(fn.instrs)` at every `build_sir` exit. `WhileTrue` claims `{S}`, `EndIter` claims its own pc, the body claims everything else in `[L, S)`.
4. Anything that fails these conditions **raises `StructureError`** — no best-effort branch. The 7 acyclic refusals and TESTSET stay refused after this task.

- [ ] **Step 1: Write the failing tests (fixtures compiled through the real oracle)**

```python
# tests/test_sir_while.py
"""WhileTrue recognition. Fixtures are oracle-compiled; expected instruction
shapes were verified against luac_sz4 output on 2026-08-11 -- if luac emits
something different on your machine, the fixture comment is stale, not luac."""
import pytest
from pyluadec.oracle import compile_source
from pyluadec.ingest import load_bytes
from pyluadec.lift import lift_proto
from pyluadec.sir.build import build_sir, StructureError
from pyluadec.sir.regions import (WhileTrue, EndIter, Break, If, Seq, Straight,
                                  Return, all_claimed)


def _sir(src: bytes):
    fn = lift_proto(load_bytes(compile_source(src, strip=True)))
    r = build_sir(fn)
    assert all_claimed(r) == set(fn.instrs)   # pc-claim audit, every fixture
    return fn, r


def _find(r, ty):
    out = []
    stack = [r]
    while stack:
        n = stack.pop()
        if isinstance(n, ty):
            out.append(n)
        for attr in ("body", "then_body", "else_body"):
            c = getattr(n, attr, None)
            if c is not None:
                stack.extend(c if isinstance(c, tuple) else [c])
    return out


def test_minimal_while_true():
    # 1 GETGLOBAL 2 LOADK 3 CALL 4 JMP->1 5 RETURN
    fn, r = _sir(b"while true do print(1) end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 4 and w.claimed_pcs == frozenset({4})


def test_while_true_with_break_in_if():
    # break JMP@5 targets 9 == closing_pc+1
    fn, r = _sir(b"while true do if f() then break end g() end")
    (w,) = _find(r, WhileTrue)
    assert w.closing.ri.pc == 8
    assert len(_find(w.body, Break)) == 1


def test_threaded_continue_becomes_enditer():
    # `if c then x() end` as the WHOLE body: luac threads the if's join JMP
    # straight back to the header, producing a second backward JMP -> header.
    fn, r = _sir(b"while true do if f() then g() end end")
    (w,) = _find(r, WhileTrue)
    ends = _find(w.body, EndIter)
    assert len(ends) >= 1        # the threaded jump is claimed, not refused


def test_nested_while_true():
    src = b"while true do while true do if f() then break end end if g() then break end end"
    fn, r = _sir(src)
    assert len(_find(r, WhileTrue)) == 2


def test_while_cond_still_certifiable_shape():
    # while <cond>: cond at top, exit-JMP forward, closing JMP back to the
    # cond start. Recognizer may express this as WhileTrue(header=cond-block)
    # with the cond as a leading If whose then-arm is a Break -- or refuse.
    # It must NOT mis-claim. (Corpus has zero of these; support is for
    # generality and the semantic-regression port in Task 5.)
    fn = lift_proto(load_bytes(compile_source(
        b"local i = 1 while i < 10 do i = i + 1 end", strip=True)))
    try:
        r = build_sir(fn)
        assert all_claimed(r) == set(fn.instrs)
    except StructureError:
        pytest.xfail("while-<cond> deferred to Task 3 -- acceptable if Task 3 lifts this xfail")


def test_refusals_still_refuse():
    # repeat stays refused until Task 3; the acyclic TESTSET family until Task 4
    fn = lift_proto(load_bytes(compile_source(
        b"local i = 0 repeat i = i + 1 until i > 5", strip=True)))
    with pytest.raises(StructureError):
        build_sir(fn)


def test_corpus_while_acceptance_grows(corpus_dir):
    """Committed census: build_sir acceptance over unique protos must reach
    the measured floor. M3 baseline: 1309/1478. The 144 pure-while +
    (some of) 8 mixed protos become acceptable here; assert a conservative
    floor and print the real number for the ledger."""
    from pyluadec.pipeline import walk_proto_paths
    from pyluadec.ingest import load_file
    from pyluadec.verify.ledger import structural_hash
    uniq = {}
    for f in sorted(corpus_dir.glob("*.lua")):
        protos = {}
        walk_proto_paths("main", load_file(f), protos)
        for path, p in protos.items():
            uniq.setdefault(structural_hash(p), p)
    ok = 0
    for p in uniq.values():
        try:
            fn = lift_proto(p)
            r = build_sir(fn)
            assert all_claimed(r) == set(fn.instrs)
            ok += 1
        except StructureError:
            pass
    print(f"build_sir accepts {ok}/{len(uniq)} unique protos")
    # Floor deliberately modest: of the 144-strong while family, 16 protos
    # also contain TESTSET (still refused until Task 4), and loop BODIES may
    # hide refusal causes the acyclic corpus never exercised. Predicting the
    # exact number here would repeat M3's planner-asserts-unmeasured-number
    # failure. REQUIRED: after this test first passes, tighten the floor to
    # (measured - 10) in the same commit and put the measured value in this
    # comment; Task 3 tightens it again.
    assert ok >= 1350   # M3 baseline 1309; measured value: <fill in at implementation>
```

- [ ] **Step 2: Run and verify the right failures**

Run: `PYLUADEC_CORPUS_DIR=... uv run pytest tests/test_sir_while.py -v`
Expected: import error on `WhileTrue` (regions.py has no such node). Fix imports to get real per-test failures: the while fixtures raise `StructureError` (M3 refuses back edges outside for-shapes); `test_refusals_still_refuse` PASSES (guard test — confirm it passes for the right reason, `StructureError` not some crash).

- [ ] **Step 3: Add the region nodes**

```python
# regions.py — after Break
@dataclass(frozen=True)
class WhileTrue:
    body: "Region"
    closing: LirInstr                 # the backward JMP closing the loop
    claimed_pcs: frozenset[int]       # exactly {closing pc}


@dataclass(frozen=True)
class Repeat:
    body: "Region"
    cond: LirInstr                    # bottom comparison/TEST
    negated: bool
    closing: LirInstr                 # the conditional backward JMP
    claimed_pcs: frozenset[int]       # {cond pc, closing pc}


@dataclass(frozen=True)
class EndIter:
    claimed_pcs: frozenset[int]
```

Extend the `Region` union and `_CHILDREN` (`WhileTrue`/`Repeat`: `lambda r: (r.body,)`).

- [ ] **Step 4: Implement recognition in `build_sir`**

Sketch (the invariants above govern; adapt freely):

```python
# in _structure_range's dispatch, before the unrecognized-transfer raise:
w = _match_while_true(fn, cfg, idoms, pc2blk, pc, hi)
if w is not None:
    region, nxt = w
    parts.append(region)
    pc = nxt
    continue
# and in the JMP handling: a JMP whose sole successor == continue_target
# becomes EndIter (mirroring the existing break_target clause).
```

`_match_while_true(fn, cfg, idoms, pc2blk, lo, hi)`:
1. Collect `sites = [pc for pc in range(lo, hi) if JMP at pc targets lo]`, empty → `None`.
2. `S = max(sites)`; verify `lo`'s block dominates `S`'s block via the idom chain (walk up from `S`'s block; stop at entry). Not dominated → `None` (this is what keeps rotated for-shapes out).
3. `_verify_single_entry(cfg, idoms, pc2blk, S, lo, S)` for the body range.
4. Recurse: `body = _structure_range(fn, cfg, idoms, pc2blk, lo, S, break_target=S+1, continue_target=lo)`.
5. Return `(WhileTrue(body=body, closing=fn.instrs[S], claimed_pcs=frozenset({S})), S + 1)`.

Thread `continue_target` through `_structure_range` and `_structure_if` alongside `break_target` (nested loops: inner loop's targets shadow the outer's — plain parameter passing gives this for free).

- [ ] **Step 5: Run tests to green; run full suite**

Run: `PYLUADEC_CORPUS_DIR=... uv run pytest tests/test_sir_while.py -v && PYLUADEC_CORPUS_DIR=... uv run pytest`
Expected: new tests PASS (the `while_cond` one may xfail); full suite green. `tests/test_m3_exit.py` must still pass untouched. Note: `corpus/ledger.jsonl` does NOT move in this task — nothing prints loops yet, so certification outcomes are unchanged. If the ledger ratchet test fails, you changed behavior you shouldn't have.

- [ ] **Step 6: Commit**

```bash
git add tests/test_sir_while.py src/pyluadec/sir/regions.py src/pyluadec/sir/build.py
git commit -m "feat: M4 task 1 -- dominance-defined back edges, WhileTrue recognition"
```

---

### Task 2: Reconstruct + print + certify `while true` loops

**Files:**
- Modify: `src/pyluadec/express/reconstruct.py` (loop scope handling only, if any is needed beyond the printer driving `open_scope`/`close_scope`)
- Modify: `src/pyluadec/emit/lua.py` (region dispatch: `WhileTrue`, `EndIter`; also `Repeat`, printing `repeat ... until <cond>` — dead until Task 3 recognizes it, but the printer arm lands with its neighbors here)
- Test: `tests/test_emit_while.py`

**Interfaces:**
- Consumes: Task 1's nodes; `Reconstructor.stmts_for/take_expr/cond_operand/open_scope/close_scope`; printer's existing region dispatch (`emit/lua.py:377-436` at M4 start — line refs drift, match on `isinstance(r, ...)` chain); `certify_proto(proto, *, is_chunk_root) -> ProtoCert`; `emit_certified_chunk`.
- Produces: `print_chunk` renders `WhileTrue` as `while true do\n<body>\nend`, `EndIter` as nothing, `Break` (already printed) as `break`. End-to-end: oracle-compiled while fixtures certify **L3**.

**Binding invariants:**
1. The printed loop body opens a lexical scope exactly like an `if` arm (`open_scope` before, `close_scope` after) — a `local` declared inside the loop must not leak past `end`.
2. `EndIter` prints nothing. Its correctness is not argued — it is **adjudicated**: the fixture must certify L3, which proves luac re-threads the printed source identically. If a fixture fails certification on `code`, the recognizer/printer pair is wrong, not the gate.
3. Statement-boundary discipline: entering the loop region must flush pending staged expressions the same way `If` does (`take_expr` calls precede `open_scope` — see `emit/lua.py`'s `If` arm for the pattern that must be mirrored).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_emit_while.py
"""While-loop printing certifies L3 through the real gate. The gate is the
oracle: these tests assert certify_proto(...).level == 'L3', which means
recompiled bytecode equal to the original under the versioned ladder."""
from pyluadec.oracle import compile_source, run_bytes
from pyluadec.ingest import load_bytes
from pyluadec.structure.structured import certify_proto, emit_certified_chunk

CASES = [
    b"while true do print(1) end",                                  # unreachable RETURN after loop
    b"while true do if f() then break end g() end",
    b"while true do if f() then g() end end",                        # threaded EndIter
    b"local n = 0 while true do n = n + 1 if n > 3 then break end end print(n)",
    b"while true do while true do if f() then break end end if g() then break end end",
    b"while true do local x = h() if x then break end end",          # local scoped to body
]


def test_while_fixtures_certify_l3():
    for src in CASES:
        p = load_bytes(compile_source(src, strip=True))
        cert = certify_proto(p, is_chunk_root=True)
        assert cert.level == "L3", (src, cert.mismatches)


def test_while_output_runs_identically():
    src = b"local n = 0 while true do n = n + 1 if n > 3 then break end end print(n)"
    p = load_bytes(compile_source(src, strip=True))
    out = emit_certified_chunk(p)
    assert out.structured
    a = run_bytes(compile_source(src, strip=True), is_source=False)
    b = run_bytes(out.source, is_source=True)
    assert (a.stdout, a.returncode) == (b.stdout, b.returncode)


def test_loop_local_does_not_leak():
    # x declared in the body must not be visible after `end`; if the printer
    # leaked it, the recompile would allocate registers differently and the
    # cert would fail on code/maxstacksize -- but pin the textual property
    # too so the failure is legible.
    src = b"while true do local x = h() if x then break end end"
    p = load_bytes(compile_source(src, strip=True))
    out = emit_certified_chunk(p)
    assert out.structured
    text = out.source.decode("ascii")   # fixture is pure ASCII by construction
    assert text.index("local") > text.index("while true do")
```

Check `emit_certified_chunk`'s actual return type name/fields before writing (`ChunkOutcome` at M4 start — confirm its attribute for the source bytes and the structured flag by reading `structure/structured.py:205`).

- [ ] **Step 2: Run to verify failure** — expected: `certify_proto` returns L1 (printer raises/refuses on the new nodes → falls back), or `print_chunk` raises `StructureError` surfaced as level L1. Confirm the failure mode is refusal, never wrong output.

- [ ] **Step 3: Implement printer arms** — mirror the `NumericFor` arm's shape: emit header line, recurse body at `depth+1` with scope open/close, emit `end`. `Repeat`: emit `repeat`, body, `until <cond>` using the existing `condition()` helper's negation convention (read `_structure_if` for how `negated` maps comparisons — the `until` condition is the loop-EXIT condition).

- [ ] **Step 4: Green + full suite + corpus checkpoint**

Run: `PYLUADEC_CORPUS_DIR=... uv run pytest` then `PYLUADEC_CORPUS_DIR=... uv run python scripts/run_corpus.py`

**AMENDED 2026-08-11 (Task 1's measurement).** This task was originally written as "the first ledger movement". It is not: `_match_while_true` fires **zero times** corpus-wide (measured, 7888 calls / 0 matches — see the retraction note in the grounding section), so **the ledger is expected NOT to move here**, exactly as in Task 1. That is not a failure of this task — the printer arms are what Task 3's `While(cond, body)` work builds on, and the synthetic fixtures below are the only thing that can exercise them until Task 3 lands. Run `scripts/run_corpus.py` anyway and **verify** the ledger is byte-identical; if it moves, something reached the new nodes that shouldn't have, and that is a finding to report, not a win to bank. `uv run python scripts/ledger_dashboard.py` for the summary either way.

Also note: this task keeps `sir/build.py`'s `_is_generic_for_back_edge` exclusion in place. Task 1's review flagged that the exclusion's only accidental guard was ledger-invariance; since the ledger stays frozen here too, that guard still holds, and the direct fixture `tests/test_sir_while.py::test_generic_for_back_edge_inside_if_stays_refused` now pins it explicitly. Do not flip it in this task.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: M4 task 2 -- while/repeat/enditer printer arms, loop scoping (ledger unchanged by design)"
```

---

### Task 3: Long-tail loops — rotated generic-for, mixed nesting, `repeat`, `while <cond>`

**Files:**
- Modify: `src/pyluadec/sir/build.py`
- Test: `tests/test_sir_loops_longtail.py` (+ lift the Task 1 xfail if while-cond lands here)

**Interfaces:**
- Consumes: everything from Tasks 1–2. Produces: no new public names — this task closes recognition gaps inside `build_sir` (and, only if diagnosis demands, minimal printer touches).

**AMENDED 2026-08-11 — this task is now the milestone's main event, not its long tail.** Task 1's measurement showed `while <cond>` is the dominant corpus loop form (**134 of 169 refused unique protos, 214 loop occurrences**), not the zero my plan asserted. Tasks 1–2 buy nothing on the corpus; essentially all of M4's loop value is here. Two findings from Task 1's implementer, which the review corroborated, bind this task:

**(A) The blocker is ONE shape, and it is shared.** A `while <cond>` header and a mid-body `if <cond> then break end` compile to the *same two instructions*: `<compare>; JMP → loop-exit`. Lua's comparison opcodes carry an inversion flag in `A`, so luac needs no separate jump for the then-arm. Therefore **handling "the `if`'s own jump targets `break_target`" unlocks both at once**, and it is the single highest-value change left in M4. Start here.

**(B) Do NOT represent `while <cond>` as `WhileTrue` + a leading `if not c then break end`.** It is semantically correct and it will **not certify**: recompiling that source emits *three* instructions (`LT` inverted; `JMP` past the break; `JMP` to the exit) where the original has two. This task needs a real `While(cond, negated, body, closing, claimed_pcs)` region node in `sir/regions.py` plus its printer arm (`while <cond> do ... end`) — not a desugaring. Task 1's implementer deliberately declined to let `while <cond>` fall out opportunistically for exactly this reason; do not undo that judgment.

Add `While` beside Task 1's `WhileTrue`/`Repeat`/`EndIter` (same frozen-dataclass + `_CHILDREN` pattern), and give `emit/lua.py` its arm. Keep `WhileTrue` — it is the genuine `while true do ... end` shape and Task 5's semantic regression uses one.

**Scope, by measured population (ordered by value):**
0. **134 protos, `while <cond>` — finding (A) above. This is the task.** Expect the ledger to move substantially here for the first time in M4; regenerate, review the diff as upgrades-only, and put the measured L3 counts in the commit message.
1. **9 protos, pure FORLOOP/TFORLOOP back edges, still refused.** Diagnose-first: the plan does NOT assert the cause. Known exemplar: `snr_common.lua:main_24_1` — a generic-for whose entry `JMP@7→17`, body `8..16`, `TFORLOOP@17`, `JMP@18→8`, wrapped in an if whose else-join is the function end. First step is a diagnosis script printing each of the 9 protos' refusal message + instruction window; fix what the diagnosis actually shows (candidates: `_match_generic_for`'s shape window, `_structure_if`'s join handling at range end).
2. **8 mixed for+while protos** — should mostly fall out of Tasks 1+this task's fixes; verify by census.
3. **1 repeat proto** — recognize `Repeat`: at range position `L`, a conditional backward jump (comparison/TEST at `S-1`, `JMP@S → L`) with `L` dominating `S`. Body `[L, S-1)`, cond claims `{S-1, S}`. Printer arm already landed in Task 2.
4. **`while <cond>`** (0 in corpus; needed for Task 5's regression `while i < 10`-style loops — actually the regression uses `while true do ... break`, so this is generality work): recognize header-block cond+exit-JMP with closing JMP back to cond start. Express as the natural region for `while <cond> do body end` — either a dedicated shape or `WhileTrue` + leading negated-If-Break, whichever certifies; the fixture decides.

- [ ] **Step 1: Diagnosis script for the 9** (scratch, findings into the task report + as fixture comments)
- [ ] **Step 2: Failing tests** — oracle fixtures: `for k,v in pairs(t) do print(k) end` variants matching the rotated shape (compile `local t = {} for k in pairs(t) do f(k) end` inside an `if` to reproduce main_24_1's wrapper — verify the shape reproduces before pinning it); `repeat`; `while i < 10`; a for-inside-while-inside-for triple. Each asserts `all_claimed` exactness + `certify_proto(...).level == "L3"`.
- [ ] **Step 3: Implement per diagnosis; repeat recognition; while-cond.**
- [ ] **Step 4: Corpus census + ledger regeneration** — the committed census floor in `test_sir_while.py` rises; update its threshold to the measured value minus a small safety margin, with the measurement in the assert message. Run `scripts/run_corpus.py`, review the diff (upgrades only), commit.
- [ ] **Step 5: Commit** (`feat: M4 task 3 -- long-tail loops; build_sir acceptance <measured>/1478`)

---

### Task 4: TESTSET — the and/or value idiom (16 protos, all loop-gated until now)

**Files:**
- Modify: `src/pyluadec/sir/build.py` (TESTSET transfer handling) and/or `src/pyluadec/express/reconstruct.py` — mechanism is the implementer's choice; the invariants below bind.
- Test: `tests/test_express_testset.py`

**Interfaces:**
- Consumes: Tasks 1–3. Produces: `a = b or c` / `a = b and c` / chains reconstruct and certify; `sir/build.py:16-19`'s "TESTSET is not an if-condition" note updated to describe the new handling.

**Background (verify against the no-frills PDF §TESTSET before implementing):** `TESTSET A B C` = if `bool(R[B]) == C` then `R[A] := R[B]` else skip the following JMP. luac emits it for `a = b or c` (C=1: if b truthy, a=b, jump over c's evaluation) and `a = b and c` (C=0). `TEST A _ C` (same-register variant) appears when source and destination coincide. Chains (`a = b or c or d`) produce cascades.

**Binding invariants:**
1. The TESTSET/JMP pair and the alternative-value producer pcs are claimed exactly once (the pc-claim audit does not bend).
2. The reconstruction is adjudicated by certification: each fixture certifies L3. No fixture may pass by producing semantically-right-but-differently-compiled source (that IS a cert failure — fix the reconstruction).
3. Corpus TESTSET protos: measure how many of the 16 now certify; whatever remains refused stays refused loudly (report the count; do not special-case).

- [ ] **Step 1: Failing tests** — fixtures: `local a = b or c`, `local a = b and c`, `x = f() or {}`, `local a = b or c or d`, TESTSET inside a while body (the corpus reality), each asserting L3. Plus one guard: a TESTSET shape the recognizer does NOT claim must still raise `StructureError` (construct via `tests/synth.py` if luac can't be coaxed).
- [ ] **Step 2–4: red → implement → green + corpus census + ledger regen.**
- [ ] **Step 5: Commit** (`feat: M4 task 4 -- TESTSET and/or reconstruction; <n>/16 TESTSET protos certify`)

---

### Task 5: Port the predecessor's semantic regressions as standing gates

**Files:**
- Create: `tests/test_semantic_regressions.py`
- Test: itself

**Interfaces:**
- Consumes: `oracle.compile_source(src, strip=True)`, `oracle.run_bytes(payload, *, is_source, args=())` (returns object with `.stdout`/`.returncode` — confirm exact field names at `src/pyluadec/oracle.py:56`), `pyluadec.pipeline.decompile_chunk` / `emit_certified_chunk`.
- Produces: the spec-§7/§8 semantic-regression suite, decoupled from the predecessor's repo.

**Sources (spec §8: mechanism-equivalent rewrite, assertions' semantics unchanged):** the five cases in `/Users/fotile96/pyluadec/pyluadec/test_semantic_regressions.py` — closure-capture-const (`1020`), closure-capture-rw-upvalue (`250`), **while-true-break-guard (`1560`)** (this is why the task sits after loops), counter-closure-dispatch-mix (`1271004`), if-elseif-conjunctions (`1\t0\t2\t0`). Copy each Lua source verbatim from the original file (it is on this machine; read it, don't retype from this plan). Port shape per case:

```python
def _roundtrip(src: str, expected_stdout: str, expected_rc: int = 0):
    bc = compile_source(src.encode(), strip=True)
    out = emit_certified_chunk(load_bytes(bc))
    r = run_bytes(out.source, is_source=True)
    assert (r.returncode, r.stdout.decode()) == (expected_rc, expected_stdout)
    return out
```

**Also in this task:**
- Port `test_generated_semantic_cases.py`'s *intent*: read the original generator (252 lines, same directory); port the generation scheme with `PYLUADEC_GENERATED_CASE_LIMIT` honored (default a small N so the committed suite stays fast — measure and report; the full sweep is a manual command documented in the runbook).
- Port `test_ir_structure_roundtrip.py`'s intent: its 6 cases assert recompiled-proto shape equality — our `certify_proto(...).level == "L3"` is that assertion's strictly stronger form. Port the 6 sources, assert L3.
- **Explicit non-goal, recorded in the test module docstring:** the two key-sequence checkpoints (`OptionMain` double-clamp, `ConfigMain` CIRCLE gate) need the L2 stub harness — spec M5. Do not fake them with partial stubs.
- **Structured-path note:** assert `out.structured is True` for each of the 5 named cases. If one ships fallback, that is a *finding* (which structuring gap?), reported not papered over — the fallback output would still pass the stdout diff, which is exactly why the structured flag must be asserted separately.

- [ ] Steps: failing tests (cases assert both stdout equality AND `structured`) → implement the port → green → measure suite time added (budget: this task ≤3s; generated cases behind the env limit) → commit (`feat: M4 task 5 -- semantic regression port, 5+6 cases + generated harness`).

---

### Task 6: Corpus re-census, mismatch clustering, freereg residual fixes, M4 exit gate (draft)

**Files:**
- Modify: `src/pyluadec/express/names.py` and/or `src/pyluadec/express/reconstruct.py` (as the clusters dictate)
- Create: `tests/test_m4_exit.py` (draft thresholds; finalized Task 12)

**This is M3-Task-8's shape again: measure first, fix the top clusters, never touch the gate.** After Tasks 2–4 the printed-but-uncertified population has changed completely (new loop bodies bring new statement/register patterns). Do not assume the old 58-residual breakdown still holds.

**ADDED 2026-08-11 (Task 2's review).** The ledger cannot currently distinguish *why* a proto is `L1`: a `build_sir` refusal (`StructureError`, with a reason) and a print-then-reject (structured fine, failed certification on a named field) both land as the same generic `fallback-state-machine` confession. That was harmless while nothing structured-then-failed; Task 2 created the first such shapes (`EndIter`), and Task 3 will create many more. **Add a refusal/failure reason to the non-`L3` ledger rows** — the `StructureError` message for refusals, the first mismatch field for print-then-reject — and assert in `tests/test_m4_exit.py` that every non-`L3` row carries one. This is also what makes the M5 ratchet CI able to say *which* regression happened, and it turns Step 1's clustering from a scratch script into standing data.

- [ ] **Step 1: Re-cluster.** Sweep all unique protos: printable-but-L1, first-mismatch field histogram, per-cluster exemplars (smallest proto per cluster, with `luac_sz4 -o /dev/null -l` diff of original vs recompiled). Write the table into the task report.
- [ ] **Step 2: Fix the top clusters** in `names.py`/`reconstruct.py`, one commit per cluster, each with its own oracle fixture pinning the shape (TDD: fixture red → fix → green → corpus number moves).
- [ ] **Step 3: The constant-pool-order decision, settled by data.** If ≥20 unique protos now differ ONLY by pool order (M3 measured 9 — re-measure), design rung `L3.2 = canonical constant-pool order` with its standalone soundness argument (a pool permutation is meaning-preserving iff every RK/Bx reference is remapped by the same permutation and no instruction depends on an index's numeric value — argue from `lvm.c`'s RK/K access paths), bump `LADDER_VERSION`, add isolating positive/negative tests per the M3 rung pattern (`tests/test_normalize_l31.py` is the template). If the population stays small, record the number and skip the rung — adding gate surface to buy <20 protos is the wrong trade, and that decision has already been made once (M3) for 9.
- [ ] **Step 4: Draft `tests/test_m4_exit.py`:**

```python
def test_m4_exit_unique_l3_rate(ledger_rows):
    l3 = sum(1 for r in ledger_rows if r["level"] == "L3")
    frac = l3 / len(ledger_rows)
    assert frac > 0.85, f"unique L3 {l3}/{len(ledger_rows)} = {frac:.1%}"

def test_m4_exit_occurrence_l3_rate(ledger_rows):
    total = sum(len(r["occurrences"]) for r in ledger_rows)
    assert total == 1944
    l3 = sum(len(r["occurrences"]) for r in ledger_rows if r["level"] == "L3")
    assert l3 / total > 0.85
```

(Match `tests/test_m3_exit.py`'s actual fixture/field names — read it first; **do not modify it**.) The `0.85` floors are the milestone commitment (M3 start: 0.752/0.811 — measured, see grounding table). If after Steps 1–3 the measured rate is below 0.85, STOP and report to the controller with the cluster table — the threshold is not to be adjusted to fit; the remaining clusters are.
- [ ] **Step 5: Ledger regen + commit per cluster; final commit** (`feat: M4 task 6 -- residual clusters closed, L3 unique <measured>`).

---

### Task 7: Match the candidate's strip mode to the original's (strictly stronger gate)

**Files:**
- Modify: `src/pyluadec/verify/certify.py` (`certify_l3` — the `strip=True` at `:54`; line drifts, find the `compile_source` call), `src/pyluadec/structure/structured.py` (wrapper path, `:183`-ish)
- Test: `tests/test_certify_stripmode.py`

**This is a deliberate behavior change to the certification gate** (M4 backlog §9, deferred out of M3's merge round on purpose). Direction of change: **strictly stronger** — when the original proto carries debug info, compile the candidate unstripped so rung 1 compares *real locvar scope ranges* instead of two empty tuples.

**Binding invariants:**
1. Detection: the original's debug-completeness (has locvars / has source) decides the candidate's strip mode. The tree-uniformity fingerprint from M3 Task 7 (`_debug_fingerprint`) already encodes this per-proto — reuse, don't reinvent.
2. **The corpus result must not move at all** (all 229 files are stripped; both sides were already `-s`). `corpus/ledger.jsonl` byte-identical after this task is the acceptance test — if it moves, that is the finding; stop and report.
3. Unstripped fixtures gain: `local a = 1 print(a)` compiled WITHOUT `-s` must now certify (M3: L1 with `Mismatch(field='locvars')` — pinned in `structured-pipeline.md` § "The candidate is always compiled `-s`"; update that section, it documents the pre-change behavior).
4. Negative control (the "strictly stronger" claim, proven not asserted): a candidate that puts a local in the WRONG lexical block — e.g. original `do local a = f() g(a) end` vs a candidate hoisting `a` out of the `do` block — must FAIL certification unstripped on `locvars` (scope ranges differ) even though it certifies when both sides are stripped. This fixture is the task's reason to exist; if you cannot construct it, the change bought nothing measurable — report that.

- [ ] Steps: failing tests (positive: unstripped simple cases certify; negative: wrong-scope fixture refused; corpus: ledger byte-identity via existing ratchet test) → implement → `scripts/run_corpus.py` → `cmp` the ledger → docs update (`certify_l3` docstring + runbook section) → commit (`feat: M4 task 7 -- strip-mode matching, rung 1 compares real locvar scopes`).

---

### Task 8: `TAILCALL` `writes_open` — the differential run, then the axiom fix

**Files:**
- Modify: `src/pyluadec/lift/effects.py` (TAILCALL row), `tests/test_express_names.py` (the local `open_writes` shim in `_temp_write_violations` becomes redundant — remove the special case, cite this task)
- Test: `tests/test_effects_tailcall.py`

**Protocol (CLAUDE.md: axiom-layer changes need an lvm.c citation + a differential run; M4 backlog §4 has the full history — read it first):**
1. Citation (already established, verify): `lvm.c:630-632` `PCRC` branch leaves results at `R[a..top)`; `lvm.c:611` asserts `C == 0` always.
2. **Differential run BEFORE the change:** sweep all 1944 protos recording `classify_registers` output; apply the `writes_open` addition; re-sweep; diff. The M4 backlog documents why the effect is not provably nil (`_staging_slice`'s backward search can walk through a TAILCALL; a for-header downstream of a TAILCALL is NOT structurally excluded — a previous claim to the contrary was measured false). Corpus has exactly 3 TAILCALLs (all `snr_common.lua` — re-derive with the backlog's inlined script).
3. If classifications move: inspect each moved proto, confirm the new classification is the correct one (the barrier got stronger), regenerate the ledger, review.
4. If nothing moves: the fix still lands (the axiom layer must be right for synthetic input), with the differential result recorded in the test docstring.
- [ ] Steps: failing test (synthetic TAILCALL proto via `tests/synth.py` where `_staging_slice` currently walks through and post-fix refuses — construct with the effects-consistency grid as reference) → differential sweep (report numbers) → fix row with citation comment → green + ledger check → commit.

---

### Task 9: Extend the consistency gate to the structured reconstructor

**Files:**
- Create: `tests/test_effects_reconstructor_consistency.py`
- Test: itself

**M4 backlog §8, verbatim scope:** `reconstruct.py → emit/lua.py` is a **third** independent hand-transcription of `lvm.c` (9 direct `ri.a/b/c` decode sites in reconstruct, 16 in the printer, zero `effects` consumption as operand source), and `tests/test_effects_emitter_consistency.py` covers only the fallback transcription. The gate's own docstring (`:20-34`) documents this blind spot and points here.

**Binding invariants:**
1. For every pc the structured path processes, the registers `Reconstructor`/printer touch ⊆ that pc's `effects.reads | effects.writes` (skip open regions, as the existing gate does).
2. Mechanism: instrument via a recording shim around the reconstructor's register accessors (`take_expr`/`cond_operand`/env reads-writes) — NOT a re-transcription of the templates (a fourth transcription would be the disease as the cure). If the accessor surface turns out not to capture all touches, say so and propose; do not silently narrow "touch".
3. Same non-vacuity discipline as the sibling gate: a fault-injection test (drop an effects row entry → gate fires) and an opcode-reach pin over the synthetic grid (reuse `test_effects_emitter_consistency.py`'s grid — import, don't copy).
4. Runs over: all corpus protos that `build_sir` accepts (post-Task-4 this is the big set — measure cost; budget ≤3s, the sibling gate does 207k rows in 0.88s).
- [ ] Steps: red (gate exists, one seeded fault detected) → instrument → green over corpus, 0 disagreements expected — any real disagreement is a REAL BUG in reconstructor or effects table: adjudicate against lvm.c, fix the wrong side, never relax (the sibling gate found the brief's own helper wrong at M3 Task 10; expect the same class of surprise) → commit.

---

### Task 10: Deepened behavioural probe as a standing gate (L1.75)

**Files:**
- Create: `scripts/probe_behaviour.lua`, `scripts/probe_behaviour.py`
- Test: `tests/test_behaviour_probe.py`
- Modify: `scripts/probe_global_state.py` CLI (`main()` learns the pinned-divergence list — closes the M4-backlog minor "CLI prints 225/229 and returns 1 while the suite is green")

**Feasibility already done** (M3 Task 9 Deliverable B, recorded in M4 backlog §5 — read it first; numbers there are Task 9 measurements, re-derive what you rely on). Design findings that BIND this implementation:
1. **Budget = recorded-EVENT count (3000) with a generous instruction backstop (400M via `debug.sethook`).** An instruction budget alone was measured to destroy agreement (226/229 → 95/229) by truncating the two representations at different points. This is the load-bearing design constraint.
2. Determinism: neutralize `tostring(table)` addresses; stub-return policy is observably arbitrary but agreement-invariant (measured under guess/zero/nil) — pick `nil`-with-name-heuristic and freeze it in the script.
3. Payload: per-file SHA-256 committed as the comparison unit; full trace dumped to scratch only on mismatch.
4. **Re-measure agreement from scratch after Tasks 2–6:** the feasibility run predates loops. Files that flipped fallback→structured now recompile byte-identical, so their `getobjname` error-text noise and table-layout divergences VANISH — expect the pin list to shrink, possibly to empty (`snr_novel`'s pairs-order divergence was fallback-induced; certified-L3 output has identical NEWTABLE/SETLIST layout). Every remaining divergence gets the Task-9 treatment: instruction-level evidence, two-directional pin, or it's a real bug.
5. Fault injection non-vacuity: an arithmetic-swap and a FORLOOP-bound injection must each produce divergence (committed tests, not report prose).
6. Cost budget: ≤5s added to the suite (feasibility: 2.7s for 458 runs + the decompile cache already paid by conftest).
- [ ] Steps: probe scripts (no Lua string patterns — plain indexing, per the Task-9 precedent) → committed tests (determinism ×2 runs, non-vacuity ×2 injections, corpus agreement with pins) → wire `probe_global_state.py` CLI pin-awareness → docs → commit.

---

### Task 11: Effect-lattice calibration (spec M4 item)

**Files:**
- Modify: `src/pyluadec/lift/effects.py` (docstrings/comments per row — **zero behavior change**)
- Create: `tests/test_effects_modes.py`
- Modify: `docs/runbooks/structured-pipeline.md` (new section: the lattice's meaning, calibration evidence, default-mode decision)

**Context that right-sizes this task (M4 backlog §3):** the lattice is *no longer the inlining gate* (M3 deleted `EffectMode` from `names.py`; loosening was measured +0.0). Calibrate it because M5's pass registry and reordering passes will consume it — not to move L3. This is an **argumentation + evidence + tests** task, not a tuning task.

**Deliverables:**
1. **Corpus evidence, committed as a test:** the 2026-08-11 census (zero metamethod-related constants across all 1944 protos — no `setmetatable`/`getmetatable`/`raw*`/`__*` name in any constant table) becomes `test_corpus_never_names_metamethod_machinery`, with the census inline. This is the empirical basis for `NO_METAMETHOD` being *plausible for script-constructed tables* — and its limit: engine-injected globals/userdata can carry metatables the census cannot see, so `NO_METAMETHOD` is NOT proven for `GETGLOBAL`/`GETTABLE` on engine values. Write exactly that scoping into the mode's docstring.
2. **Per-row argument:** for each of the 38 rows, the `NO_METAMETHOD` and `TRUSTING` columns get a one-line justification or an explicit `# UNARGUED` marker — the current state (only STRICT argued, per CLAUDE.md) becomes visible row-by-row instead of a blanket caveat.
3. **Default-mode decision:** recommend and document. Expected outcome given the evidence: STRICT stays the default (nothing downstream needs loosening yet; the census justifies NO_METAMETHOD as a *permitted* per-pass opt-in for M5, engine-value caveat attached). If the implementer's analysis lands elsewhere, the argument governs — report it.
4. **Mode-difference tests:** for ≥3 representative opcodes (GETTABLE, ADD/arith, GETGLOBAL), a test pinning what each mode returns and, in the docstring, what would have to be TRUE of the runtime for that grading to be sound.
- [ ] Steps: census test red (no such test) → land census → per-row docs → mode-difference tests → runbook section → commit (`docs+test: M4 task 11 -- effect-lattice calibration, STRICT default upheld`).

---

### Task 12: Deferred minors, documents of record, readability evaluation, M4 exit

**Files:**
- Modify: `scripts/run_corpus.py` (forced-`L0` row records its own confession — 2-line fix, M4 backlog minors), `scripts/ledger_dashboard.py` (rung-sort `TypeError` guard), `tests/conftest.py` (shared corpus-proto cache for the census-style tests if the suite is over budget — measure first)
- Modify: `CHANGELOG.md`, `CLAUDE.md` (M4 section), `docs/runbooks/structured-pipeline.md` (capability boundary re-measured; while/repeat sections), `docs/runbooks/m3-backlog.md` (retitle: M4-completed items struck with commit refs; what remains becomes the M5 agenda seed — same "would otherwise be lost" rule as its predecessors)
- Create: `docs/reports/m4-readability.md`
- Finalize: `tests/test_m4_exit.py`

**Readability alignment evaluation (spec M4 exit, second half):** compare against the predecessor's shipped text output at `/Users/fotile96/pyluadec/post_process/input/*.lua` (229 UTF-8 files, verified present 2026-08-11). Deliverable is an honest *evaluation report*, not a gate:
1. Quantitative: files shipping structured (n/229, vs M3's 92); unique-proto L3 rate; per-file line-count ratio ours-vs-predecessor (a structured file should be the same order of magnitude; fallback files will be far larger — report the two populations separately); count of `__pld_*` artifacts remaining corpus-wide.
2. Qualitative: THREE representative files side-by-side (one clean scenario file, one heavy-logic file like `snr_common.lua`, one still-fallback file if any remain), each with a paragraph of honest assessment — where our output reads better (real block structure vs the predecessor's), where worse (synthesized `l0_0` names vs the predecessor's `v0`; anything else observed).
3. Every number measured in-session; the report states its commit hash.

**Deferred-minors sweep:** fix the two script items above; re-measure and either fix or explicitly re-defer (with one line of reasoning each, in the M5 agenda) the rest of M4 backlog §6 — probe value-side ambiguity, `strip_location` second prefix, `tostring(k)` table keys, `payload_of` split, `close_scope`/memo comments, process-level cert memo. Do not silently drop any.

**Exit checklist (all verified in-tree, evidence per item in the task report):**
- [ ] `tests/test_m4_exit.py` finalized and green: unique L3 > 0.85, occurrence L3 > 0.85, total == 1944.
- [ ] Semantic regressions: 5 named + 6 roundtrip + generated harness green, all 5 named shipping structured.
- [ ] All standing gates green: compile 229/229, golden parity, ledger fixed point, global-state probe (pin list re-measured), behavioural probe, both consistency gates, engineering-practice.
- [ ] Ledger: every change across M4 an upgrade; no `L0`; fixed point holds.
- [ ] Suite ≤45s with `--durations=15` recorded.
- [ ] `docs/runbooks/` current: no number in a document of record that wasn't measured this milestone or cited.
- [ ] Milestone wrap via superpowers flow (final whole-branch review + finishing-a-development-branch) — the controller's step, listed for completeness.

- [ ] Commit (`docs: M4 wrap -- readability evaluation, minors, exit gates`).

---

### Task 13: Live-range register classification — the bottleneck M4 actually has

> **ADDED 2026-08-11, after Task 3.** Executes **immediately after Task 4**, before Task 5. It is numbered 13 only so the earlier task numbers keep pointing at the same text; read the order as 1, 2, 3, 4, **13**, 5, 6, 7…

**Files:**
- Modify: `src/pyluadec/express/names.py` (`classify_registers` / `_stack_discipline`)
- Modify (only if the diagnosis demands): `src/pyluadec/express/reconstruct.py`
- Test: `tests/test_express_liverange.py`

**Interfaces:**
- Consumes: `classify_registers(fn: LirFunction) -> RegClass` (fields `locals`, `temps`, `loop_vars`); `certify_proto(proto, *, is_chunk_root) -> ProtoCert`.
- Produces: no new public names. `RegClass`'s contract is unchanged; what changes is which registers land in `locals` vs `temps`.

**Why this task exists.** Task 3 raised `build_sir` acceptance from 1309 to **1435/1478** but L3 only from 1112 to **1139** — the bottleneck moved. Measured after Task 3 (script committed in `docs/runbooks/structured-pipeline.md`, re-run and reproduced byte-for-byte by the task reviewer): of the **339** unique protos still below `L3`, **251 differ from the original by extra `MOVE` instructions and nothing else**, **13** by `MOVE` plus other traffic, 13 have the same histogram, and only **62** are structuring refusals. Of the 264, **226 first diverge at a `CALL` in the original where ours has a `MOVE`**.

Diagnosis, verified by the reviewer on the exemplar `snr_crd_10.lua:main_2`: pcs 1–6 stage a two-argument call in registers 0/1/2; `classify_registers(fn).locals` is `[0, 1, 2, 3]`; the printer therefore emits

```lua
local l1_0 = comSectionCardStart
local l1_1 = ...
local l1_2 = ...
l1_0(l1_1, l1_2)          -- luac: comSectionCardStart(<a>, <b>) with no MOVEs
```

**`classify_registers` decides per register *number*, whole-function.** A register that is a genuine `local` in one statement and a call-staging temp in another is classified once, for the whole function, and the conservative answer (`local`) wins — materializing luac's expression stack as named locals and emitting the `MOVE`s that copy into it.

**This is the same class of defect M3 Task 8 fixed once already** — and worth remembering how that went: I identified an effect-based inlining barrier as "the pre-identified lever", it moved **+0.0** protos, and simulating `lparser.c`'s own `freereg = nactvar` discipline moved **+63.6 points**. The rule was per-register-number and whole-function then, too. Task 8 fixed the *allocation* half; the *lifetime* half is still whole-function. Do not repeat my mistake of naming the lever before measuring it.

**The property to satisfy (not a mechanism — pick whatever achieves it):**

> A register is materialized as a named `local` **iff luac's parser would have had an active local variable in that slot at that pc.** Equivalently: classification must be a function of (register, pc-range), not of register alone. A slot that is a live local across statements *n..m* and a call-staging temp at statement *m+1* must be both, in its own ranges.

Wrong in either direction still breaks certification, so both directions need fixtures. Ground truth is `lparser.c`'s `nactvar`/`freereg` bookkeeping and `lcode.c`'s expression-stack discharge — read them; the certification gate adjudicates every answer.

- [ ] **Step 1: Measure before touching anything.** Re-run the committed residual script; produce the current split and a per-cluster exemplar list (smallest proto per cluster, with `luac_sz4 -o /dev/null -l` of original vs recompiled side by side). Put the table in the report — this is the task's baseline and the reviewer will check your final numbers against it.

- [ ] **Step 2: Write the failing fixtures first**, from the exemplars, smallest-first. Each is oracle-compiled and asserts `certify_proto(p, is_chunk_root=True).level == "L3"`. Include at minimum: a bare two-argument global call (`f(a, b)` with `a`/`b` locals); a call whose arguments are themselves calls; a call in a loop body where the same registers are reused across iterations; and a genuine local that must NOT be demoted to a temp (the opposite-direction guard — `local x = f() g(x) h(x)` reads `x` twice, so it must stay a local). Run them: expect `L1` with `code` mismatches, never wrong output.

- [ ] **Step 3: Implement**, guided by Step 1's clusters. Commit per cluster, each with its fixture going red→green and the corpus number re-measured.

- [ ] **Step 4: Corpus + ledger.** `scripts/run_corpus.py`; the diff must be **upgrades only** (no `L3`→`L1`, no `L0`). Put before/after counts on both bases in the commit message. **If a proto downgrades, stop** — a classification that improves the aggregate while breaking a previously-certifying shape is exactly the trade this project does not make.

- [ ] **Step 5: Report the residual honestly.** Whatever remains below `L3` gets the same cluster treatment, and the numbers go into Task 6's re-census rather than being quietly rolled forward.

**Constraints beyond the global ones:** do not touch the certification gate; do not widen `build_sir` (structuring refusals are the other 62 and belong to Task 6); the standing engineering-practice rule applies — the suite is at ~30s against a 45s ceiling, and any per-proto certification you add to the committed suite must be justified.

---

## Explicit non-goals (M5+, recorded so they are not re-litigated)

- **Pass registry + first beautify passes** (spec §4/§7 M4 item) — deferred to M5 by decision of the human partner, 2026-08-11 (this plan's header records the rationale). M5's confession-ranking-driven idiom passes are the registry's first client.
- **L2 differential-execution certification** (stub env + trace + coverage badge) and the two key-sequence checkpoints — spec M5. Task 10's probe is L1.75, not L2.
- **Full ratchet CI** (baseline diff, downgrade=fail, `git bisect` integration) — M3's ledger fields support it; building it is M5-adjacent tooling.
- **Variable-name semanticisation** — corpus is stripped; M5+ at best.
- **`test_ir_pipeline.py` (86 cases) translation** — spec §8 generates its list from per-function level data; M4's re-census (Task 6) produces that data, translation itself is M5.
- **GPU proposer, lparser/lcode instrumentation mining, Lua 5.2** — M6+.

## Self-review notes

- Spec coverage: spec-M4's four items map: proof-gated inlining = delivered M3 (recorded); effect calibration = Task 11; pass registry = explicitly deferred (user decision); first beautify passes = deferred with registry. Spec-M4 exit: semantic regressions = Task 5; readability alignment evaluation = Task 12. Loops absorbed from M3 non-goals per M3 backlog §1.
- Type consistency: `WhileTrue/Repeat/EndIter` fields consistent across Tasks 1–3; `certify_proto(proto, *, is_chunk_root)` and `emit_certified_chunk(root)` used as defined in M3 (`structured.py:145/:205`); `run_bytes(payload, *, is_source, args)` per `oracle.py:56`.
- Placeholder scan: no TBDs; diagnosis-first steps (Task 3 Step 1, Task 6 Step 1) are deliberate measure-before-fix steps with concrete outputs required, not deferrals.
- Numbers: every figure carries its measurement date/provenance; implementers instructed to re-derive.

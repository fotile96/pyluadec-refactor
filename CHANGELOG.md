# Changelog

## 2026-08-14 — M6: cross-corpus validation, and six defects in shipped software

- **The headline is not a rate. It is six defects found in software that
  shipped.** The predecessor project decompiled this same 229-script corpus;
  its output was recompiled, repacked into a PSP ISO and **played through to
  completion by a human** over a dozen fix rounds. M6 pointed this project's
  instruments at it and confirmed **six defects, four of them previously
  unknown**, every one walked at instruction level: `snr_music.lua:main_3` (the
  music gallery's poll loop is gone, so the gallery bounces straight back to
  the main menu); `snr_common.lua:main_76_2` (an unconditional `break` that
  opens the save screen from recollection mode, and an empty `else` that hangs
  the frame — **both verbatim the historical checkpoints in the predecessor's
  own debug playbook**); `snr_mainmenu.lua:main_7` (a
  `systemSave`/`novelFlag`/`musicFlag` gate deleted, so two mutually exclusive
  arms both run); `snr_graphic.lua:main_4` and `snr_memory.lua:main_4` (a
  `== 6` / `== 4` comparison dropped, twice each); and
  `snr_common.lua:main_75` (a retry `while` became an `if`). Evidence is
  pc/opcode-level throughout and carries no game text.
- **All six were found by the static arm; five of the six are invisible to
  both dynamic arms.** For `snr_mainmenu:main_7` the behaviour arm returns
  `agree` over an 18-event run, and `snr_common.lua`'s behaviour row is silent
  (`truncated:1/79` — its original-side run invoked 1 of the 79
  function-valued globals the file defines before the 3000-event cap). Two
  out-of-plan tasks repaired all six by hand under `corpus/pred_repairs/`,
  verified at instruction level and at runtime with bespoke drivers; the
  upstream predecessor corpus was not touched.
- **The cheapest instrument beat the designed one.** `scripts/loss_sweep.py` —
  four per-proto "the original has it, the predecessor does not" sweeps, one
  walk per proto, **3.31s over all 1944 pairs** — found everything the graded
  fingerprint found, **plus** a defect the fingerprint's `cfg_reachable` scores
  **1.0** on (`snr_common:main_75`, whose only loop had vanished), **plus** one
  that an aggregate five-opcode test count had hidden. 25 protos flag; every
  one is pinned with a verdict and an instruction walk.
- **`L3` is 1438/1478 unique (97.3%) and 1904/1944 occurrences (97.9%)**, from
  1430 (96.8%) / 1896 (97.5%) at M5 close; **217 of 229 files ship fully
  structured source, 8 hybrid, 4 whole-file fallback** (216/6/7); **1763/1944
  (90.7%) occurrences ship structured text**. Two defects closed it: compound
  `if` condition trees (`sir/regions.py::CondNode` +
  `build.py::_match_cond_chain`, which took the `structure:` refusal family
  from **21 ledger shapes to 1**) and two of the five mechanisms behind
  `Reconstructor.write_reg`'s `declared` gate. `scripts/ratchet_diff.py`
  against the M5 merge baseline `0957364`: **8 upgraded, 0 downgraded**.
- **`avg_score 0.997` is no longer a gate anywhere** (human partner,
  2026-08-13; recorded in the spec's own decision log, not only in a runbook).
  M5 handed it to M6 as M6's exit; M6 removed it and kept it as a dashboard
  observable. **The reason is not that it was out of reach** — it measures
  **0.977328** at this tree, from 0.968833, with 217 files at exactly
  1.000000. The reason is that M6 measured it to be uncorrelated with defect
  detection: the fingerprint it coarsens scores a perfect `cfg_reachable` on a
  proto whose only loop had been deleted. `tests/test_m5_exit.py`'s 0.96 floor
  stands, neither tightened nor relaxed.
- **Two more decision-log rows, both "premise falsified by measurement" rather
  than "unfinished".** Tasks 7 and 8 were re-scoped (corpus-wide enumerated
  differential → a feasibility demonstration on the 13 compound-`if` leaves;
  design-plus-prototype → a design note) on the evidence above, plus the
  measurement that killed Task 8's framing: **127 of the then-162 candidate
  protos poll the key every iteration, including 113/113 `choice-branch`**, so
  non-termination is not what distinguishes the UI-loop class. Tasks 9 and 10
  (structure reference + a ~1–2M-token LLM meta-reconstruction pass) were
  **dropped**: Task 9 Step 1 was the plan's own gate on Task 10, and measured
  after the compound-`if` fix, `build_sir` succeeds on **12 of the
  predecessor's 13 corresponding leaf protos (92.3%)**. The pre-fix 6/13 was
  confounded — six of its seven failures were the defect Task 11 closed — and
  should not be quoted.
- **New instruments, all with a non-vacuity proof.** `predcorpus.py` (compile
  + ingest the predecessor's source, with an explicit `strip` mode after a
  corpus-wide census caught 260 protos of manufactured `upvalues` mismatch);
  `lift/footprint.py` + `corpus/observation/footprints.json` (static
  interaction surface, with `dynamic_reads` as its own honesty counter);
  `observation_classes.py` + `corpus/observation/classes.json` (**156**
  candidate protos classified with committed evidence); `cross_corpus.py`
  (three arms, a **separate** `PRED_PINS` table — the spec forbids reusing our
  own pins for a different candidate population); `probe_enum.py` (enumerated
  differential driving over 13 leaves, with `budget-exceeded` rather than
  silent sampling); `loss_sweep.py`. Full-corpus scans stay **jobs**; the suite
  keeps gated smoke subsets and fixed-point gates.
- **Predecessor parity, measured corpus-wide for the first time: 229/229
  compile, 229/229 proto trees match 1:1, 0/229 byte-faithful** (3903
  substantive rung-1 mismatches over 1433 paths, 2989 coarser signals). The
  first version of that census was inflated by a strip-mode bug and is
  corrected in place — shipping the predecessor's text through our `L3` gate
  was already a measured non-goal (0/13) and stays one.
- **Exit gate `tests/test_m6_exit.py`** (13 tests, 0.15s, no corpus needed):
  unique `L3` ≥ **0.96** (achieved 97.3%), the ledger↔`classes.json`
  cross-artifact join covering every leaf refusal and every CAP-dominant
  proto, and every divergence adjudicated (no `suspect` verdicts). Every floor
  sits below its achieved value and states that value in its assert message;
  each is driven over mutated data and required to go red. Suite **1077 tests
  in 55.07-55.61s over three runs** (macOS 15.2 / Apple M4, arm64) against the ~120s
  earmark; `./scripts/ratchet_job.sh` runs its three gates end to end in 58.2s
  and exits 0, now against the M5 merge baseline `0957364` rather than the M4
  one it had been left pointing at.

## 2026-08-13 — M5: the long tail, the L2 gate, and a quality baseline

- **`L3` is 1430/1478 unique (96.8%) and 1896/1944 occurrences (97.5%)**, from
  1389 (94.0%) / 1855 (95.4%) at M4 close. Three routes, in order of what they
  bought: closing the `build_sir` refusal leaves (refusals 31 → 13), closing the
  mismatch/reconstruct leaves, and **hybrid chunk emission** — a chunk whose
  root does not certify now ships structured text with fallback holes at the
  `CLOSURE` sites that would not certify, instead of forfeiting the whole file.
  **216 of 229 files ship fully structured source, 6 ship hybrid, 7 still ship
  the whole-file M2 fallback** (17 at M4 close). Per occurrence, **1747/1944
  (89.9%) ship structured text**; by instruction volume, 85.8%.
- **The milestone's acceptance criterion was RE-SCOPED, by the human partner,
  and it is recorded in the spec's own decision log** rather than only in a
  runbook, because it modifies a §1 goal-4 criterion the user confirmed section
  by section. M5 task 3 ported the predecessor's `semantic_eval.py` metric and
  measured **0.935633** at milestone start against its stated `0.997`; tasks 4,
  5 and 6 moved it to **0.968833**. The arithmetic then closed the original
  gate off: with 216 files at *exactly* 1.000000 the remaining 13 must average
  ≥ 0.947, and converting all 7 remaining fallbacks to hybrids at the measured
  hybrid quality of 0.816791 reaches only 0.9896. **0.997 is M6's exit now**,
  with a diagnosed agenda rather than a hope — 13 compound-`if` refusals (one
  defect, with a committed 26-instruction repro) and 4 root reconstruction
  defects that hybrid emission *unmasked*, one of them adjudicated
  (`snr_music.lua`'s main collapses four nested table constructors into one
  aliased table). **The metric was not relaxed and the certification gate was
  not touched.**
- **Readability now beats the predecessor on the axis M4 called our worst.**
  Output surface v2: `elseif`, dot sugar for string keys, `-1` instead of
  `(-1)`, uniform 4-space indentation including function bodies, and readable
  UTF-8. Re-measured over the 216 structured files: max nesting depth **61 → 8**
  against the predecessor's **10**, and ours is deeper in **0 of 216** files;
  `["` 6085 → **0**; high-byte decimal escapes 991233 → **0**; `(-` 570 → **0**;
  line-leading `elseif` 0 → **282** (predecessor 278); `while` and `break` still
  match it **exactly** (196/196, 178/178); line ratio 0.972×. Every one of the
  five changes was verified by regenerating the whole ledger and requiring it
  **byte-identical** — which is what caught the one attempt that was not a
  presentation change. The UTF-8 item needed a scoped, human-approved amendment
  to the bytes red line, implemented in exactly one function
  (`emit/lua.py::_str_lit`); `ingest`, `lift` and `verify` still decode nothing.
- **A full ratchet, and a `git bisect` predicate that tells the truth.**
  `scripts/ratchet_diff.py` + `scripts/ratchet_job.sh` (suite → baseline diff →
  24-case differential sweep). It is a *command*: this repository has no CI
  runner configuration and none was invented. Four of the five review findings
  against it were about the bisect contract being wrong in ways the first
  report presented as verified — `git-bisect(1)` reads every exit code in
  1..127 except 125 as **bad**, so the intended "not a verdict" exit of 2 was
  silently naming innocent commits; and the documented predicate skipped
  exactly the loudest regression class it exists for. Both fixed and both
  demonstrated by running a real bisect against an injected **compile**
  regression. `tests/test_ratchet_diff.py` (**43** cases, no corpus needed —
  37 at task 8's close, plus 6 that task 9 added for the `l2-lost` and
  `l2-coverage-downgrade` kinds) exists
  solely to prove the tool can fail.
- **L2 differential certification is online, and its measured reach is one
  file.** Key-sequence driving under a stubbed environment, proto-level
  coverage, and a conservative static may-analysis that refuses a grant when a
  stub-derived value could decide a branch unobserved. New per-occurrence `l2`
  ledger field with a row-level pure aggregate. **`snr_lib.lua` at `L2@100%` —
  2 rows, 3 occurrences of 1944 — and 164 occurrences refused
  `taint-static`.** The reach is the result, not a shortfall to be explained
  away: across four review rounds **thirty granting routes were found, every
  one of them inside the previous round's fix**, and the reach never moved off
  1 of 5 — every fix refused a fixture, none refused a corpus file. The
  triggering finding is structural: Lua 5.1's `equalobj` compares types before
  consulting `__eq`, so a stub proxy compared against a string literal is
  *unobservable* to any runtime harness, and `doScriptScene == "<literal>"` is
  this corpus's central idiom (427 sites across 23 files). **220 of 229 files
  contain no `pressButton` at all**, so for most of the corpus there is no
  input loop to drive — a stronger statement than "not yet authored".

  **Two more granting routes were found in the final review round, making
  thirty-two, and both had shipped.** (1) `evaluate` never read the trace
  header, so when both sides stopped at `MAX_EVENTS = 3000` "byte-equal" meant
  "equal over the first 3000 events" with nothing recorded anywhere — a
  fixture whose two sides differ only in their final engine call certified
  identical at `cov=1.0`. A grant now requires at least one authored sequence
  to run to completion, and `cov` is measured over those only; it is *not*
  "every sequence", because the degenerate ones provably never halt (`snr_lib`
  under `tail=CIRCLE` reports `CAP|3000001` with the cap raised 1000×) and
  requiring it would put reach at 0 forever. **This narrows the hole rather
  than closing it, and the residual is committed as a known-open route**: a
  capped run can still be the only evidence for a BRANCH no completing
  sequence enters, which `cov` cannot see because both specs enter the same
  protos. M6 agenda 2 carries it, with the measurement that the one live grant
  is not standing on it (`snr_lib`'s capped sequence produces 15 distinct
  event shapes at 3000 events and the same 15 at 30000). (2) The static backstop reads the
  **original** only, so it spoke for the artifact only while the two were
  field-identical; on `snr_music.lua` the two shapes really do diverge
  (`__pld_R` hides 33 compare sites and invents 13). A grant now requires
  every proto in the chunk to be `L3`, which makes that precondition
  structural instead of accidental. **Reach unchanged at 1/5 and
  `corpus/ledger.jsonl` byte-unchanged**; extending L2 to hybrids or fallback
  text is M6 work and needs the artifact analysed, not this condition
  relaxed.
- **The two historical key-sequence checkpoints are regression tests.**
  `tests/test_keyseq_checkpoints.py` drives `snr_common.lua` and asserts the
  `OptionMain` double clamp and the `ConfigMain` CIRCLE gate/wait **on the
  original bytecode's trace as well as ours**, with **10** parametrised bug
  injections proving each assertion fires (re-counted 2026-08-13; task 10's
  own report says seven, which was its round-0 figure). Precisely: the two
  property tests apply their property function to each trace *separately*
  after requiring the traces equal, so a both-sides regression cannot pass —
  that is the guarantee. The committed parametrisation mutates **only the
  artifact side**; the both-sides form of the same demonstration is an
  out-of-tree exercise, disclosed as such in the file. Two things worth
  recording: a menu option's *value* is invisible to the probe, so the property
  is expressed through the `layerClip` rectangle the redraw produces and no
  menu row is ever named (the bytes red line, navigated rather than dodged);
  and re-timing exposed that **11 of 11 `k=`-bearing shipped sequences were
  dropping directives** — the frame model costs 6 frames per `wait` — which is
  now fixed, with 53/53 directives landing and no L2 verdict flipped.
- **The pass registry is retired, permanently, not deferred** (spec §2 decision
  table). Everything spec §4's Pass protocol specified — apply, verify,
  commit-or-rollback, confession — is already done, and done more strictly, by
  the per-proto certification gate. Nothing in M2–M5 needed a transform the
  protocol could express and the printer could not. `src/pyluadec/passes/` was
  never created, so no code was deleted. The plugin surface itself is not
  rejected; its client is M6+'s proposer.
- **Suite: 867 tests, 42.1–44.1s over five runs on macOS 15.2 / Apple M4
  (arm64)** — 0.9s under the ceiling at worst, and the spread is the documented
  within-session upward drift on this laptop, not the 7 tests M5's last two
  rounds added (those cost **0.16s** together, measured with `--durations`).
  **Test ordering was never varied, by either arm of the
  argument.** No randomiser is installed — measured 2026-08-13, the only
  third-party pytest plugin registered is `pytest-timeout 2.4.0`,
  `importlib.util.find_spec("pytest_randomly")` is `None`, and `-p
  no:randomly` names a plugin that does not exist, which pytest accepts as a
  **silent no-op** (`uv run pytest -p no:randomly --co -q` → 867 collected,
  exit 0). So M5 task 11's 5 pairs, task 12's 5 pairs and a reviewer's 10 on a
  second host all ran both arms in *identical collection order*: task 11
  asserted an ordering difference and task 12 "refuted" it, and neither
  checked that the knob was connected. What those runs do establish stands:
  this suite has 1–2s of run-to-run variance (fixed 42.25–43.39s, "random"
  42.57–43.09s — two samples of the same configuration), so a single-run
  comparison across sessions cannot separate anything from noise, which is the
  actual source of this milestone's disputed timings. M5 task 2 recovered
  ~11.9s with a process-level certification memo and the milestone spent all of
  it; **1.6s of headroom at worst on this host is the first item on the M6
  engineering agenda** (a reviewer's host measures the same tree at
  39.4–41.1s, i.e. ~4s — quote the host with the number).
- **Not done, and now the M6 agenda** (`docs/runbooks/m3-backlog.md`, numbered
  so items can be cited): reaching 0.997 by closing the reconstruction residual;
  corpus-wide L2 plus the taint analysis's four documented gaps (argument
  direction, script-built tables, `VARARG`, and harness state — the last being
  the first limit found that is *not* a propagation gap, since a register-level
  may-analysis structurally cannot follow taint into the probe's own frame
  counter); the `next`/`pairs` iteration-order gap; probe hardening; making a
  `StructureError` say which proto raised it; and the engineering debt swept at
  the wrap. **M1's Linux x86_64 verification is still outstanding** — the
  migration runbook requires *both* 64-bit platforms and only macOS arm64 has
  been proven, and M5 found one concrete Linux-only defect
  (`ratchet_job.sh`'s BSD-only `mktemp -t`) by reading upstream source rather
  than by running it.

## 2026-08-12 — M4: loops, and verification hardening

- **Loops recovered.** `while <cond>`, `while true`, `repeat`, threaded
  end-of-iteration jumps and the `and`/`or` *value* idiom are now region kinds
  (`sir/regions.py`: `While`, `WhileTrue`, `Repeat`, `EndIter`, `CondValue`;
  recognizers in `sir/build.py`). `build_sir` acceptance went **1309 -> 1447**
  of 1478 unique proto shapes. Measured against the predecessor's shipped
  output on the 212 files we structure, our line-leading `while` and `break`
  counts match it **exactly** (190/190 and 175/175) —
  `docs/reports/m4-readability.md`. **`repeat` is recognized but this corpus
  contains none** (0 `repeat`/`until` lines in all 229 decompiled files
  against 971 `while`), so its only evidence is synthetic; corpus green says
  nothing about it.
- **The real bottleneck was register classification, not loops.** `RegClass`
  gave one verdict per register *number* per function; task 13 made it per
  `(register, definition)`. That single change took the print-but-do-not-
  certify residual from 283 unique protos to **35**, and the "differs from the
  original only by extra `MOVE`s" cluster inside it from 253 to **4**. The
  three loop tasks before it moved the top two capability rows and the `L3`
  rate not at all.
- **`L3` is 1389/1478 unique (94.0%) and 1855/1944 occurrences (95.4%)**, from
  1112 (75.2%) / 1577 (81.1%) at M3 close, against an M4 exit floor of 85% on
  both bases (`tests/test_m4_exit.py`, which also pins the denominator at
  `== 1944`). **212 of 229 files ship structured source**, up from 92. The
  floors are milestone commitments and are deliberately ~9 points below the
  achievement: a floor set at the measurement is a tripwire, and the standard
  repair for a tripwire is to edit the threshold.
- **The ledger now says WHY a proto is not `L3`.** New `refusal_reason` field,
  four committed kinds (`structure:` / `reconstruct:` / `compile:` /
  `mismatch: <field>`), coupled to `level` in both directions and asserted as
  such. The residual census in `docs/runbooks/structured-pipeline.md` is
  derived from this field rather than from a scratch script, and
  `scripts/ledger_dashboard.py` prints its histogram. Two deliberate
  exclusions keep corpus payload out of a checked-in file: the reason carries a
  `Mismatch`'s field NAME and never its values, and never `luac`'s error text.
- **A behavioural probe (L1.75) is a standing gate.** `tests/test_behaviour_probe.py`
  loads each chunk under a stubbing environment, **invokes every global
  function it defined**, and compares a deterministic event trace between the
  original bytecode and our output: **229 files, 227 byte-identical, 2 pinned
  divergences, 0 probe failures, 398196 recorded events.** Read the reach split
  before over-crediting it — the 3000-event cap truncates 132 of 229 files, and
  those contribute 99.5% of the events while the other 97 contribute a median
  of **10** each. One feasibility claim carried into it was measured false: the
  stub-return policy is **not** agreement-invariant (227/227/226/226 across four
  policies).
- **Semantic-regression port.** The predecessor's 5 named semantic cases and 6
  roundtrip cases are ported, plus a generated differential harness; **3 of
  the 5 named cases ship structured, 2 ship the M2 fallback** —
  `test_counter_closure_and_dispatch_mix` and
  `test_if_and_elseif_conjunctions_preserved`, each pinned by an `== "L1"`
  assertion and a `b"__pld_pc" in out.source` check in
  `tests/test_semantic_regressions.py`, with the cause named in that case's
  own docstring (the "prints but does not certify" `mismatch` residual, and
  `build_sir`'s "if targets out of range" refusal, respectively — both in the
  M5 agenda's residual clusters).
- **Certification got stricter, not just wider.** `certify_l3` now compiles the
  candidate with `strip=not carries_debug(original)`, so rung 1 compares real
  locvar scope ranges on unstripped input. The corpus did not move (all 1944
  protos read as stripped). "Stricter" is the accurate word, not "strictly
  stronger": a gate that starts examining a dimension cannot also promise never
  to reject on it, and a reconstruction that materializes a `local` the
  original never declared is now refused.
- **`TAILCALL` gained `writes_open` in the axiom layer**, with the differential
  run CLAUDE.md requires: `classify_registers`' four fields plus every proto's
  level/rung/reason swept over all 1944 occurrences before and after —
  byte-identical, and `corpus/ledger.jsonl` reproduced byte-for-byte. The reason
  it moved nothing is structural (`effects.successors(TAILCALL) == ()`, so a
  `TAILCALL` always ends its basic block), now pinned by a test rather than
  left as prose. A knock-on: the effects–emitter consistency gate's blanket
  open-region skip was removed rather than accepted, taking it from 207214 to
  **all 214192** corpus instructions checked.
- **A second consistency gate**, `tests/test_effects_reconstructor_consistency.py`,
  reconciles `lift/effects.py` against the *structured* path
  (`express/reconstruct.py` -> `emit/lua.py`) — a third independent hand
  transcription of `lvm.c` that nothing had been checking. **0 violations**, by
  instrumentation rather than by a fourth transcription. Its own docstring
  records what it does NOT assert, including that `FORPREP`'s row backs no
  checked touch.
- **Effect-lattice calibration done.** `STRICT` stays the pipeline-wide default
  and is the only mode any `src/` code selects (enforced by a test).
  `NO_METAMETHOD` is a permitted per-pass opt-in **scoped to script-constructed
  tables** — the census finds 0 metamethod-related constants in 71414, but 56
  of the 164 global names the corpus reads are never written by it and come
  from the engine, where the census is blind. `TRUSTING` is recommended against
  for any pass: its whole delta is three rows and the corpus falsifies all
  three. `lift/effects.py`'s behaviour is unchanged (replayed identical over
  82080 comparisons). Two rows were found under-graded and left alone pending
  the full axiom protocol; the `LEN` one is a real defect and is M5 agenda
  item 1.
- **Readability evaluated honestly** against the predecessor's shipped
  localization input, in `docs/reports/m4-readability.md`. Structured output is
  0.98× the predecessor's line count in aggregate with all 212 files inside
  0.78×–1.03×, and carries **zero** `__pld_*` artifacts. It reads *worse* in
  five named printer-level places — non-ASCII strings as decimal escapes, no
  `elseif` (208 of them become nested `if`s, worst case 61 levels of nesting
  against 5), no dot sugar for string keys, un-indented function bodies, unary
  minus printing as `(-1)` — plus a sixth, structural one: the 17 files still
  on fallback are 47.6% of the corpus **by line volume**, so "212 of 229 files" is
  the flattering way to count.
- **Not done in M4, and now the M5 agenda** (`docs/runbooks/m3-backlog.md`):
  full ratchet CI (baseline diff, downgrade = fail) — M4 delivered the field
  that makes it cluster usefully but not the CI; the `LEN` regrade; the 89
  remaining uncertified proto occurrences, which are all inside those 17 files
  and hold 692 individually-certified siblings hostage; L2 differential
  certification and the key-sequence harness.

## 2026-08-11 — M3: structured backbone

- **Structural recovery online.** Three new packages replace the fallback path
  for the majority of the corpus: `pyluadec.sir` (dominator-driven region
  identification — `Straight`/`Seq`/`If`/`NumericFor`/`GenericFor`/`Break`/
  `Return`), `pyluadec.express` (register classification + statement/expression
  reconstruction), and `pyluadec.emit.lua` (a 561-line pure structural printer:
  one walk of the typed trees, no regex, no post-processing of its own output).
  The *absence of `re`* across
  `src/pyluadec/{ingest,lift,cfg,sir,express,emit,verify,structure}` is
  statically enforced by
  `tests/test_engineering_practice.py::test_no_regex_in_analysis_or_emission_layers`
  (one narrowly-scoped pre-existing exception in `structure/fallback.py`).
  "One walk, no post-processing" is a design discipline held by review and by
  the module docstring, not by a static check.
- **1112 of 1478 unique proto shapes (75.2%) and 1577 of 1944 proto
  occurrences (81.1%) now certify `L3`** — the printed source recompiled
  through the real `luac_sz4` and compared field-by-field against the original.
  92 of the 229 files ship genuinely structured source; the other 137 still
  ship the M2 fallback. Gated by `tests/test_m3_exit.py` (threshold >50%, a
  milestone commitment that must not be edited down).
- **Certification is the only landing gate.** `emit_certified_chunk` ships
  structured source **iff** the root proto certified `L3`, and the semantically
  exact fallback chunk otherwise. A bug in region identification or inlining
  can therefore only lower the L3 rate; it cannot produce wrong output.
  Certification is per proto subtree, so one unstructurable function does not
  poison its siblings' recorded levels.
- **Normalization ladder rung 1 (`L3.1`, `strip-lineinfo`)** added;
  `LADDER_VERSION` bumped to `l3-ladder-v1`. Its soundness argument is
  co-located with the rung in `verify/normalize.py` and is made from what
  `compare_protos` still compares afterwards (`code`, `constants` bitwise,
  frame sizes, locvar scope ranges, upvalue count, subprotos), not from a
  hand-wave. Measured: 0 of the 1112 `L3` entries certify at rung 0 — the
  corpus's `source = "=?"` and surviving `linedefined` make rung 0 unreachable
  here.
- **Two new standing gates.** `tests/test_global_state_probe.py` compares the
  observable global-table delta between original bytecode and decompiled output
  on real corpus content: **225 of 229 files byte-identical, 4 pinned
  divergences** that are error-message *text* only (an `ldebug.c` `getobjname`
  naming artifact of the fallback's register-box model — instruction-level
  evidence in `docs/runbooks/m3-backlog.md`). `tests/test_effects_emitter_consistency.py`
  mechanically reconciles `lift/effects.py` against the emitter templates:
  207214 of 214192 corpus instructions checked, 0 disagreements, plus a
  synthetic operand grid reaching all 38 opcodes.
- **Capability boundary, stated honestly.** `while`, `repeat`, and mixed or
  irreducible back edges are **not** structured: `build_sir` refuses 169 unique
  protos, 162 of them carrying such an edge, plus 7 acyclic refusals — all 16
  unique protos containing `TESTSET` (the `and`/`or` value idiom) are among
  these 169 refusals. A further 139 unique protos build a region tree but do
  not print because a descendant closure does not, and 58 print but do not
  certify. All of them stay at `L1` with a confession. This is the largest
  single M4 increment; see `docs/runbooks/m3-backlog.md`.
- **Ledger ratchet — what is machine-checked and what is not.** Asserted: no
  `L0`, `compile_ok` everywhere, `shash` sortedness/uniqueness, full-corpus
  coverage at 1944 occurrences, byte-identical regeneration from
  `run_corpus.py`, and *within-row* coupling between level and confession in
  both directions (`test_m3_exit.py`). **Not** asserted: cross-revision
  monotonicity — no test compares against a historical baseline, so a
  regenerated ledger with fewer `L3` rows passes the suite as long as the rate
  stays above 50%. "Levels only ever go up" is discipline plus review of the
  ledger diff; full ratchet CI is an explicit M4 item.
- See `docs/runbooks/structured-pipeline.md` for the full reference: layer
  layout, the certification invariant, the ladder, the `freereg` register model
  that was worth +63.6 points of L3 rate (and the pre-identified effect-mode
  lever that was worth exactly 0.0), and the day-to-day commands.

## 2026-08-10 — M1 (partial): macOS arm64 migration gate green

- `PYLUADEC_CORPUS_DIR=<corpus> ./scripts/verify_migration.sh` →
  `ALL MIGRATION GATES PASSED on arm64 / Darwin` (120 tests passed). First
  64-bit platform proven: the ingest layer's header-dispatched serialization
  width holds on a host where `sizeof(size_t) == 8`, both non-vacuously
  (`luac_sz8` correctly rejects this 32-bit corpus rather than silently
  misparsing it) and constructively (`luac_sz4` byte-for-byte roundtrips the
  whole corpus on this host).
- Linux x86_64 verification is still outstanding. Per
  `docs/runbooks/64bit-migration.md`, M1 requires both 64-bit platforms
  green, not either — this entry closes the macOS arm64 half only.

## 2026-08-10 — M2: fallback closed loop

- 229/229 corpus files produce compilable Lua source via the fallback
  state-machine emitter (`pyluadec.structure.fallback.emit_chunk`), verified
  by `tests/test_corpus_compile.py` and `scripts/run_corpus.py` (`compiled
  229/229`).
- Certification ledger v1 online: `corpus/ledger.jsonl` committed, 1478
  unique proto shapes / 1944 total proto occurrences across the corpus, all
  at level `L1` (fallback emission compiles clean against the in-repo
  oracle). Regeneration is a fixed point of `scripts/run_corpus.py`, guarded
  by `tests/test_ledger_ratchet.py`.
- All 38 Lua 5.1 opcodes covered end-to-end by differential-execution tests
  (`tests/test_fallback_*.py` via `tests/diffexec.assert_fallback_roundtrip`,
  `tests/test_fallback_closures.py::test_all_38_opcodes_reachable_in_emitter`):
  original bytecode and fallback-decompiled source run through the real
  `lua` interpreter and must agree on stdout and exit code.
- L3.0 strict proto comparator (`pyluadec.verify.normalize`) online with a
  versioned, currently-empty normalization ladder (`l3-ladder-v0`). Basic-
  block CFG (`pyluadec.cfg.blocks::build_cfg`) is built and actually consumed
  by the fallback emitter — one dispatch state per basic block (unlike the
  CFG in the original `pyluadec`, which was built but never read by its
  structuring pass). The irreducible-graph-safe dominator tree
  (`pyluadec.cfg.dom`, Cooper–Harvey–Kennedy) is implemented and tested
  (`tests/test_dom.py`) but has **no production consumer yet** — it is M3
  substrate, not something M2 reads. Likewise, `lift/effects.py`'s per-opcode
  `InstrEffects` (`effect`, `may_error`, `reads`, `writes`, `reads_open`,
  `writes_open`) are computed and attached to every `LirInstr` but not yet
  read by the emitter — also M3/M4 substrate (see "Effect modes" in
  `docs/runbooks/decompile-pipeline.md`).
- See `docs/runbooks/decompile-pipeline.md` for the full pipeline reference
  and a reading guide for fallback output.

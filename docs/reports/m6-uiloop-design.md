# M6 task 8 — the Class-2 (UI poll loop) design note

Everything in this note was measured on **2026-08-14** on macOS 15.2 / arm64
(Darwin 24.2.0), at `72a3704`, against
`PYLUADEC_CORPUS_DIR=/Users/fotile96/pyluadec/others/script_to_decompile`
(229 files, 1944 protos) and
`PYLUADEC_PRED_CORPUS_DIR=/Users/fotile96/Zndnovel/lua_scripts`.

**This task was re-scoped on 2026-08-14** (plan amendment, §"Tasks 7 and 8
re-scoped"). The brief asked for a design **and** a prototype
(`scripts/probe_uiloop.py`); the prototype is cut and this note is the whole
deliverable. Nothing under `scripts/` was added, and the suite is unmoved.

**What the re-scope was about, and what this note therefore has to answer.**
The plan's Class 2 was "arrow/action-key polling loops serving peripheral UI,
harder because a finite key sequence does not guarantee termination". Task 4
measured that premise and it did not survive: **127 of 162 candidates (78%)
poll the key inside a loop, including 113 of 113 `choice-branch`**. So
non-termination is not what distinguishes Class 2 — it is shared. §1 says what
does. §2 records the two pre-measurements. §3 gives the concrete design a
future prototype would need. §4 labels every assumption. §5 is the
recommendation, weighed against the alternative.

**Red line.** This note carries opcodes, pcs, block numbers, register numbers
and **ASCII identifiers only — no game text**. Identifiers such as
`pressButton`, `systemSave` and `comDlgSelectItem` are constant-pool strings
and they do appear here; what does not appear is any string constant that is
not an ASCII identifier. (An earlier revision said "no corpus string constant
appears in it", which contradicted its own contents.)

**pc convention.** Every pc in this note is **1-based**, matching
`pyluadec.lift` (`lift.py:42` decodes `p.code[pc - 1]` at `pc`) and
`luac_sz4 -l -l`. Verified against the listing this session; §6 records a
review finding that did not reproduce on exactly this point.

---

## 0. Which numbers here are new, and which are re-derivations

Every figure below was recomputed this session, independently of the report
that first published it wherever that was practical (the dominance test, the
poll-loop cut, the enumerated budget census and the `main_7` divergence census
were re-implemented from scratch against `pyluadec.cfg` rather than read out of
the committed JSON). §6 lists the **five** that did **not** reproduce — two of
them this note's own round-0 errors, corrected in place at §3.3 and §3.5.

**Round 1 rewrote §1.1 (three confound controls), §3.3 (the write-site
accounting), §3.5 (the behaviour-verdict attribution) and §6, and added §5.3.**
Where an earlier revision said something else, §6 says so rather than the
sentence quietly changing — the convention `docs/reports/m6-observation.md`
established.

---

## 1. What actually separates the two classes

**Not termination.** The mechanical rule that assigns the classes is
(`scripts/observation_classes.py::classify`):

- `ui-keyloop` — the proto's own body has a natural loop whose body contains a
  **direct** `pressButton` call;
- `choice-branch` — it does not, but it calls an option-reading function;
- `neither` — neither, in its own body.

Re-derived this session from `corpus/observation/classes.json`: census
**113 `choice-branch` / 11 `ui-keyloop` / 38 `neither`** over 162 candidates,
and `loop_polls_per_iteration` true on **127 of 162**, split
**113 / 11 / 3**. Both classes are loops. The plan's distinguishing difficulty
is shared by the whole of Class 1.

Three things do separate them, and all three are measured.

### 1.1 Defect density — 5 of 11 against 1 of 151

The milestone confirmed **six** defects in the predecessor's shipped output.
Their classes, joined against `classes.json` this session:

| defect | proto | class | our level | our shipped |
|---|---|---|---|---|
| 1 | `snr_music.lua:main_3` | `ui-keyloop` | `L1` | fallback |
| 2 | `snr_common.lua:main_76_2` | `ui-keyloop` | `L1` | fallback |
| 3 | `snr_mainmenu.lua:main_7` | `ui-keyloop` | `L1` | fallback |
| 4 | `snr_graphic.lua:main_4` | `ui-keyloop` | `L1` | fallback |
| 5 | `snr_memory.lua:main_4` | `ui-keyloop` | `L1` | fallback |
| 6 | `snr_common.lua:main_75` | `choice-branch` | `L3` | fallback |

**Five of the six are `ui-keyloop`, out of a population of eleven.** Class 2 is
**6.8%** of the candidate set and carries **83%** of the confirmed defects:
**5 of 11 (45%)** against **1 of the other 151 (0.7%)**.

**The obvious confound is controlled.** All 11 `ui-keyloop` candidates carry an
individually reviewed `observed` block while 98 of the 113 `choice-branch` do
not (Task 4 §4), so a hand-attention bias is a live objection. The control is
`scripts/loss_sweep.py`, which is **exhaustive over all 1944 proto pairs** and
mechanical. Re-run this session (**3.47 s wall**, 25 protos flagged over 1944
pairs, all six defects named in its own pin table), its flagged set splits by
class:

| class | flagged / population | rate |
|---|---|---|
| `ui-keyloop` | **9 / 11** | **82%** |
| `neither` | 6 / 38 | 16% |
| `choice-branch` | 2 / 113 | 1.8% |
| not a candidate | 8 | — |

An instrument that never heard of the classes and looked at every pair puts
**9 of the 11** Class-2 protos on its list and **2 of 113** Class-1 protos. The
concentration is not an artifact of where humans looked.

**The discovery-order objection is closed too.** `scripts/loss_sweep.py` never
reads `corpus/observation/classes.json` — it imports `cross_corpus.json_safe`,
`probe_common.adjudicate_pins` and `pyluadec` modules, and its per-proto counts
come from `verify/semantic_score.py::collect_proto_signatures`. **Five of its
eight `LOSS_KINDS` are `ProtoSignature` fields that already existed at
`b666a1c` ("M5 task 3"), before any M6 defect was known** — `global_reads`,
`global_writes`, `call_targets`, `call_shapes`, `return_arity` — and
`test_ops` is derived from `opcode_counts`, also present there. **Two are
not**: `n_natural_loops` and `n_back_edges` were added during M6, by which time
defect #1 was known. Measured this session, that does not affect the result:
**exactly one of the 25 flagged rows is flagged by the two loop kinds alone**,
and it is `snr_common:main_75`, a **`choice-branch`** proto. Dropping the two
M6-added kinds leaves `ui-keyloop` at **9/11** and takes `choice-branch` from
2/113 to **1/113** — the enrichment strengthens.

**And the size confound, which is the one this note was thinnest on.**
Class-2 protos are 4.5x larger (§1.2), and the sweep's flag rate rises with
size. Measured over all 1944 protos this session:

| instruction count | protos | flagged | rate |
|---|---|---|---|
| < 50 | 1089 | 0 | **0.0%** |
| 50–199 | 591 | 4 | 0.7% |
| 200–499 | 170 | 16 | **9.4%** |
| >= 500 | 94 | 5 | 5.3% |

**Nine of the eleven `ui-keyloop` protos are >= 200 instructions** (the two
below are `snr_common:main_81` at 26 and `main_76_2` at 174). Size-matched at
that threshold the enrichment survives intact:

```
>= 200 instructions: 264 protos, 21 flagged = 8.0% baseline
  ui-keyloop      8 / 9   = 88.9%
  neither         5 / 14  = 35.7%
  choice-branch   1 / 21  =  4.8%
```

**8 of 9 against 1 of 21, at equal size, against an 8.0% baseline.** Being big
is not what makes a Class-2 proto get flagged.

### 1.2 Structural difficulty, for both decompilers

Re-derived from `classes.json` this session:

| | n | our `L3` | ships structured | leaf refusal sites | median loop headers (max) | median instrs (max) |
|---|---|---|---|---|---|---|
| `choice-branch` | 113 | **108 (96%)** | 107 | 5 | 1 (14) | 102 (1372) |
| `neither` | 38 | 17 (45%) | 17 | 21 | 1 (4) | 127 (1009) |
| `ui-keyloop` | **11** | **1 (9%)** | **1** | **10** | 2 (16) | **461 (2182)** |

Class 2 protos are **4.5× larger by median instruction count**, **10 of 11 are
leaf refusal sites** in our own ledger (against 5 of 113), and **exactly one
certifies `L3`** (`snr_lib.lua:main_1`). The same population that broke the
predecessor's structurer is the population that still refuses ours. The class
predicate — "a direct key poll inside this proto's own loop" — is an accurate
proxy for *this proto is a screen*, and screens are large hand-written state
machines. It is not a proxy for *this loop may not terminate*.

### 1.3 The termination difference is real but carries 1 proto, not a class

Task 4 §3.6's residual answer is that the *shape* of the termination argument
differs: a card choice leaves its loop when a returned value matches an id in
the measured channel domain, while a UI screen's exit can depend on accumulated
table state, or on nothing at all. Quantified this session over the 11 Class-2
protos, by testing each poll loop's body for a CFG edge leaving the body:

```
14 poll loops over the 11 protos; 4 have NO exit edge, all 4 in ONE proto
  snr_mainmenu:main_7   4 poll loops, 4 with no exit edge
  the other 10 protos   1 poll loop each, all with an exit edge
```

So "no key sequence terminates this loop" is a **1-of-11** phenomenon
(`snr_mainmenu.lua:main_7`, whose four poll loops are left only through engine
calls that do not return). `snr_music.lua:main_3`'s exit depends on a
`TFORLOOP` scan rather than on the key — a second shape, one proto. Ten of the
eleven have an ordinary exit edge out of the poll-loop body.

**Answer.** The boundary is not where the plan put it. It is a **defect-density
and structural-difficulty boundary, not a termination boundary**: Class 2 is
the small, dense, screen-shaped population that both decompilers get wrong.
The split is worth keeping as a **triage prior** — 6.8% of the population, 83%
of the confirmed defects, 82% flagged by an unbiased static sweep — and is
worth nothing as a statement about which *instrument* each class needs.

---

## 2. The two pre-measurements

### 2.1 (a) Loop-body cut correspondence — re-derived

Task 4 ran this on **all 19 protos that call `pressButton` directly**, not the
2–3 the brief asked for. Re-implemented from scratch this session (own
dominance walk, own callee-provenance tracker; the predecessor side loaded
through `pyluadec.predcorpus.load_pred_proto(..., strip=True)` and recompiled
with the in-repo `luac_sz4`), the per-row numbers reproduce **cell for cell**:

```
proto                          orig hdr/be/poll/body/calls   pred hdr/be/poll/body/calls
snr_common:main_27                    1/ 1/1/ 55/ 12               1/ 1/1/ 53/ 12   match
snr_common:main_28                    1/ 1/1/ 57/ 13               1/ 1/1/ 55/ 13   match
snr_common:main_29                    6/ 8/1/ 79/ 18               6/ 8/1/ 79/ 18   match
snr_common:main_55                    1/ 1/1/ 52/ 13               1/ 1/1/ 50/ 13   match
snr_common:main_71                    6/ 8/1/ 38/ 10               6/ 8/1/ 36/ 10   match
snr_common:main_74_13                 1/ 1/1/266/ 24               1/ 1/1/252/ 24   match
snr_common:main_76_2                  1/ 1/1/ 62/ 13               1/ 4/1/ 78/ 21   body differs
snr_common:main_76_7                  4/ 4/1/ 55/ 12               4/ 4/1/ 53/ 12   match
snr_common:main_77_24                 1/ 1/1/ 91/ 26               1/ 1/1/ 90/ 26   match
snr_common:main_81                    1/ 1/1/ 11/  3               1/ 1/1/ 12/  3   match
snr_fragment_main:main_3              3/ 3/1/103/ 65               3/ 3/1/101/ 65   match
snr_graphic:main_4                    7/ 8/1/178/ 44               7/ 8/1/175/ 42   naming artifact
snr_lib:main_1                        2/ 2/1/ 46/ 14               2/ 2/1/ 44/ 14   match
snr_mainmenu:main_7                  16/32/4/612/235              16/28/4/616/235   match
snr_memory:main_4                     2/ 2/1/135/ 22               2/ 2/1/132/ 22   match
snr_music:main_3                      2/ 2/1/108/ 15               1/ 1/0/  0/  0   FAILS
snr_novel:main_7                      1/ 1/1/ 32/  6               1/ 1/1/ 33/  6   match
snr_novel:main_12                     2/ 2/1/ 69/ 21               2/ 2/1/ 71/ 21   match
snr_story_main:main_3                 3/ 3/1/ 92/ 50               3/ 3/1/ 91/ 51   body differs
```

(`snr_mainmenu:main_7`'s body/call columns are the **sum over all four** poll
loops here; the report's table gives a single loop's, which is why 612/235
appears against its 158/55. Both readings agree between the sides — the report
has 55 = 55 for one loop, this table has 235 = 235 for the union — so the row
is a `match` either way.)

**The published result is 18 of 19 with one structural failure, and that
number needs its criterion stated to be honest.** Task 4 §5.1 defines
correspondence as "the same number of poll loops **and** the same body
call-name sequence". Applied literally that is **15 of 19**: three rows differ
on the call column. The published **18 of 19** counts those three as
corresponding after adjudication, and the report says so in its own verdict
column:

- `snr_graphic:main_4` (44 vs 42) — a **naming artifact of the tracker**, not
  a divergence: two callees are reached through a temp register and cannot be
  named. Both calls still happen inside the same loop.
- `snr_story_main:main_3` (50 vs 51) — the predecessor **duplicated a shared
  `or`-tail** into the else arm. Semantically equivalent, structurally
  divergent.
- `snr_common:main_76_2` (13 vs 21, 1 latch vs 4) — **one loop with four
  latches**, the predecessor's `while` whose tail `luac` wrote out four times.
  The cut corresponds; the body carries 8 extra named calls.

Both readings are stated here because a later milestone will size work on this
number: **15 of 19 under the literal criterion, 18 of 19 after adjudicating
three explained rows, 1 structural failure either way.**

**The sole structural failure is a confirmed defect, not an instrument limit.**
`snr_music.lua:main_3`'s raw back edges re-derived this session as
`(src -> hdr)`: original **`[(325, 328), (365, 12)]`**, predecessor-recompiled
**`[(343, 346)]`**. Both sides agree on `nups=7`, `numparams=0` (377
instructions against 407). The predecessor's only back edge is the `pairs()`
`TFORLOOP`; **its poll loop is gone entirely**, and the L2 harness measures the
consequence — the original spins (`CAP`, 3001 events, 2502 polls), the
predecessor falls straight out (`OK`, 94 events, 6 polls on one frame). This is
the milestone's defect #1. The cut criterion was right and the program was
wrong.

### 2.2 (b) The 78% per-iteration overlap, and what the field actually means

Re-derived from `classes.json`: **127 of 162 (78%)**, split **113/113
`choice-branch`, 11/11 `ui-keyloop`, 3/38 `neither`**.

**`loop_polls_per_iteration` overstates its own name and a consumer must know
it.** The field means "a poll site lies **somewhere** in a natural-loop body",
not "on every iteration". Re-implemented independently this session — a poll
site counts only if **its block dominates every latch of the header** — the
predicate holds for **118 of 127**, and the 9 exceptions come out byte for byte
as published:

```
snr_common:main_71     snr_common:main_75     snr_e1_10_s:main_29
snr_e2_10_f:main_35    snr_e2_10_s:main_13    snr_graphic:main_4
snr_mainmenu:main_7    snr_s4_10_fb:main_16   snr_s6_10_s:main_19
```

**Three of the nine are Class-2 protos** (`snr_common:main_71`,
`snr_graphic:main_4`, `snr_mainmenu:main_7`), i.e. **3 of 11**. That is a
direct constraint on §3.4 below: a prototype cannot bound "one iteration" by
"one poll", because on 3 of its 11 targets a loop iteration can complete
without passing the poll.

### 2.3 Two more consumer caveats that a prototype inherits

- **`mechanical.footprint` is a 7-key projection.** It carries
  `global_reads`, `table_key_reads`, `calls`, `table_key_calls`,
  `dynamic_reads`, `read_sites`, `call_sites` — verified this session — and
  **not** `unattributed_calls` / `unattributed_reads`. Joining
  `corpus/observation/footprints.json` by `(file, proto_path)`:
  **146 of 162 candidates have unattributed calls, 946 in total** (and 133 have
  unattributed reads, 1566 in total). A prototype stubbing from
  `footprint.calls` alone silently misses them. §3.3 shows this is not a detail
  for Class 2 — it is the design's load-bearing failure.
- **`n_natural_loops` counts headers; `n_back_edges` is separate.** They differ
  on **14 of 162** records; `snr_mainmenu:main_7` is **16 headers against 32
  back edges**. A "loop count" that is really a latch count published a false
  structural claim once already in this milestone, and §6 records that it did
  so a second time.

---

## 3. What a per-iteration transition-comparison prototype would need

The brief's candidate design: treat the poll-loop body as
`(state, key) -> (state', effects)`, snapshot state at the poll site on both
sides, compare single-iteration effects over the enumerated
`(reachable-state x key)` frontier, and thereby sidestep whole-loop
termination. This section is what that costs, concretely, on the measured
corpus. §5 says whether to pay it.

### 3.1 Cutting the loop body — well-defined on one side, absent on the other

**Original side: well-defined for 19 of 19** (§2.1) — group back edges by
header, take the union of the backward closures, keep the loops whose body
contains a direct poll.

**Our side: well-defined for 1 of the 11 Class-2 protos.** Measured this
session by decompiling four files, recompiling our own text with `luac_sz4`,
and running the identical cut on the result:

| file | original hdr/be/poll/protos | ours hdr/be/poll/protos |
|---|---|---|
| `snr_lib.lua` (certifies, ships structured) | 2 / 2 / 1 / 3 | **2 / 2 / 1 / 3 — identical** |
| `snr_music.lua` (whole-file fallback) | 3 / 4 / 1 / 5 | 13 / 203 / **0** / 14 |
| `snr_memory.lua` (fallback) | 8 / 12 / 1 / 6 | 12 / 320 / **0** / 16 |
| `snr_mainmenu.lua` (fallback) | 20 / 40 / 4 / 9 | 57 / 1210 / **0** / 22 |

Where a proto certifies `L3` the correspondence is exact **by construction** —
the recompiled `code` array was compared field by field to get the certificate.
Where it ships the M2 fallback the poll-loop cut finds **nothing**, and the
203 / 320 / 1210 back edges are the pc-dispatch state machine's, not the
program's.

**The mechanism is recoverable, and the earlier report overstated the loss.**
Measured this session, the `GETGLOBAL pressButton` sites survive the fallback
**exactly**: 6→6 in `snr_music.lua`, 8→8 in `snr_memory.lua`, 36→36 in
`snr_mainmenu.lua`, 3→3 in `snr_lib.lua`. What breaks is register *adjacency* —
the fallback spills the loaded value into the numerically-keyed `__pld_R` box
and reloads it before the call:

```
ours, snr_music.lua fallback, one poll site
  36 GETGLOBAL  a=4 bx=9        ; the global name survives
  37 SETTABLE   a=0 b=K(0)  c=4 ; spilled into __pld_R[0]
  38 SETTABLE   a=0 b=K(1)  c=K ; the argument, into __pld_R[1]
  39 GETTABLE   a=4 b=0 c=K(0)  ; reloaded
  40 GETTABLE   a=5 b=0 c=K(1)
  41 CALL       a=4 b=2 c=2     ; the call, 5 instructions from its name
  42 SETTABLE   a=0 b=K(0) c=4  ; the result, back into __pld_R[0]
```

So a cut on our fallback side needs a tracker that follows values through
constant-numeric table keys, not one keyed on `GETGLOBAL`-to-`CALL` register
adjacency. That is buildable; it is simply a different tracker from the one
Task 4 used. What is **not** recoverable is loop *structure*: the fallback
dissolves control flow into pc dispatch, so there is no loop body to cut on our
side at all, only a call site to find.

### 3.2 Which side would a prototype compare, and does it have a mission?

Two candidate missions, and they want different sides:

1. **Audit the predecessor** (`original` vs `predecessor-recompiled`). This is
   where every confirmed defect came from, and the loop cut is well-defined on
   both sides for 19 of 19.
2. **Certify our own output** (`original` vs our reconstruction). Here the
   instrument has **no target**: of the 11 Class-2 protos, 1 certifies `L3` —
   where the certification gate already proves the strictly stronger property
   that the recompiled `code` array matches field by field — and 10 ship the
   M2 fallback, where the emitted text is semantically exact by construction
   and (§3.1) has no loop to cut.

Task 4 §5.7 pushed a prototype toward mission 2 with a purpose-built
reconstruction. Measured, mission 2's window is empty in both directions: above
the line the proof is already stronger, below it there is nothing to compare.

**A tension this note has to name rather than leave implicit.** `probe_enum` is
a **mission-2 instrument and only that** — `probe_enum._payload` accepts
`"original"` and `"decompiled"` and nothing else — and §5.2 item 3 nevertheless
recommends its targeted-entry half over the 11 if a dynamic arm is built at
all. The two are consistent only under the conditional §5.2 states: mission 2
has no window **today**, when 1 of 11 certifies and 10 ship a fallback that is
exact by construction. It acquires one the moment **Tasks 9–12 change
reconstruction** — a representation change that is wrong on one arm of one
branch is precisely what neither the certification gate (which would simply
refuse) nor a single stub policy would surface as a *behavioural* difference on
a proto that still certifies. So §5.2 item 3 is a recommendation about a future
state, not about the current one, and it is deliberately gated on that.
§5.3 records the same conditional for the predecessor arm, which
`probe_enum` does not have.

### 3.3 What "state" is — the design's load-bearing failure

The brief proposes "the footprint's read/write keys at the poll site". Measured
over the 11 Class-2 protos:

**`Footprint.write_sites` counts `SETTABLE` and nothing else.** `n_write += 1`
appears only in the `SETTABLE` arm, and the accounting identity
`write_sites == attributed + unattributed + dynamic + nonstring_key` holds
corpus-wide (**1667 = 256 + 945 + 66 + 400**, checked this session).
`SETGLOBAL` writes land in `global_writes`, a **fully named** channel;
`SETUPVAL` is excluded from the footprint entirely, and its module docstring
says so under "Deliberate exclusions" — all 1944 protos are debug-stripped, so
`Proto.upvalues` is empty and an upvalue write carries no name. So a
`write_sites` column is **not** "the write sites this proto makes", and §2.3's
own warning about the footprint's field names applies to it. Counted by opcode
this session, and cross-checked against `footprints.json`
(`SETTABLE == write_sites` and `SETLIST == setlist_sites` on all 11):

| proto | `SETTABLE` | of which attributed | `SETGLOBAL` | `SETUPVAL` | call sites | unattributed calls |
|---|---|---|---|---|---|---|
| `snr_common:main_29` | 1 | 0 | 0 | 0 | 63 | 4 |
| `snr_common:main_71` | 35 | 0 | 0 | 0 | 42 | 0 |
| `snr_common:main_74_13` | 24 | 0 | 0 | 0 | 42 | 16 |
| `snr_common:main_76_2` | 1 | 0 | 0 | 0 | 16 | 0 |
| `snr_common:main_81` | 0 | 0 | 0 | 0 | 3 | 0 |
| `snr_graphic:main_4` | 0 | 0 | 0 | **34** | 63 | 5 |
| `snr_lib:main_1` | 10 | 2 | 1 | 0 | 26 | 0 |
| `snr_mainmenu:main_7` | 0 | 0 | **2** | 0 | **271** | 32 |
| `snr_memory:main_4` | 0 | 0 | 3 | **27** | 42 | 5 |
| `snr_music:main_3` | 13 | 0 | 0 | **16** | 23 | 3 |
| `snr_story_main:main_3` | 1 | 1 | 9 | 0 | 78 | 2 |
| **total** | **85** | **3** | **15** | **77** | **669** | **67** |

`attributed` means a constant string key on a depth-1 global base — the only
form the `SETTABLE` census can name. So the honest figure is:

> **The eleven protos make 177 write sites — 85 `SETTABLE`, 15 `SETGLOBAL`,
> 77 `SETUPVAL`. Eighteen of them are nameable (3 attributed `SETTABLE` + all
> 15 `SETGLOBAL`): 10.2%.**

Three-and-a-half percent was the wrong figure, arrived at by reading a
`SETTABLE`-only counter as a write census. **Ten percent does not rescue the
design, and the corrected breakdown makes the objection sharper rather than
weaker**: the **77 invisible `SETUPVAL` sites are concentrated in exactly the
three protos whose loop exit depends on accumulated state** —
`snr_graphic:main_4` (34), `snr_memory:main_4` (27), `snr_music:main_3` (16),
the last being §1.3's `TFORLOOP`-over-a-flag-table exit. The part of the state
a Class-2 transition comparison most needs is the part the footprint is
structurally unable to name, because the corpus is stripped.

And `snr_mainmenu:main_7` — the proto with the four exit-less poll loops, the
four deleted progress gates and the worst Class-2 shape in the corpus — makes
**2** write sites (both `SETGLOBAL`, 1 distinct name) against **271** call
sites, 32 of them unattributed. Its state does not live in the script; it lives
in the engine, behind calls. (An earlier revision said "zero write sites",
which was the same `SETTABLE`-only reading.)

This is not a gap to be closed by more dataflow. It is the corpus telling us
that a UI screen's state is the engine's and its locals', and a stripped
bytecode cannot name either.

Three definitions of "state" are therefore on the table, and only one is
buildable today:

| definition | available? | what it costs |
|---|---|---|
| footprint read/write keys at the poll site | **no** — 18 of 177 write sites nameable, and the 77 unnameable `SETUPVAL` sites are where the loop-carried state is | — |
| the whole stub-environment shadow table | **yes** — `scripts/probe_common.lua` already serialises it | but this collapses "which keys matter" into "diff everything", which is what `probe_behaviour` already does per chunk; the per-iteration cut buys only the granularity, not a state abstraction |
| the channel assignment as input, the event trace as effects, no explicit `state'` | **yes** | this is `probe_enum` with a one-iteration budget, not a new instrument |

The third is the honest form of the proposal, and naming it honestly is most of
the design: **the "transition comparison" reduces to `probe_enum` restricted to
one iteration.** It does not need a new instrument; it needs an iteration bound
bolted onto an existing one.

### 3.4 Bounding an iteration instead of proving termination

The mechanism that would work: make the stub `pressButton` return the scripted
value on call 1 and raise a sentinel error on call 2, catching the sentinel at
the entry, so the recorded trace is exactly one loop body. That converts
"does this loop terminate" into "what did one body do", which is the design's
whole point.

**It is wrong on 3 of its 11 targets, and that is measured.** §2.2's dominance
test names `snr_common:main_71`, `snr_graphic:main_4` and `snr_mainmenu:main_7`
as protos whose poll site does **not** dominate every latch. On those, an
iteration can complete without reaching the poll, so "second poll = second
iteration" under-counts and the bound silently compares a body prefix against a
body prefix of a different length. A correct bound has to be keyed on the back
edge, which means instrumenting the *latch*, which means the instrument needs
the loop structure — which §3.1 measured is absent on our fallback side.

Cost is **not** an objection and should not be used as one. Re-derived this
session with `probe_enum.channels_of`, the enumerated product over the 11 is:

```
main_29 4   main_71 4   main_74_13 4   main_76_2 24  main_81 2   main_4(graphic) 8
main_1(lib) 2   main_7 128  main_4(memory) 4   main_3(music) 2   main_3(story) 512
total 694 assignments; both sides = 1388 drives
```

At the throughput measured this session on a warm decompile
(`snr_mainmenu.lua:main_7`, 256 drives in 0.67 s = **385 drives/s**), the whole
Class-2 population is about **3.6 s**. Everything in §5 is about yield, not
about cost.

### 3.5 The reach discipline, and what it implies here

Task 7's measured discipline transfers verbatim and is **more** load-bearing on
this population:

- **Resolve reach by NAME, never by line number.** Protos shipping fallback
  have their tree reshaped into `__pld_F` factories, so no line- or path-keyed
  correspondence survives — and **10 of the 11 Class-2 protos ship fallback**.
- **Measured this session: all 11 are name-reachable, with exactly one
  published name each.** `discover_entries` against the original resolves every
  one — **three** under a global name, **two** under a `<table>/<method>` path,
  and **six** under a global *named* `main` (none of these six is the chunk
  root; they are `main_4`, `main_1`, `main_7`, `main_4`, `main_3`, `main_3`,
  each bound to the global `main` by its chunk's own `CLOSURE`/`SETGLOBAL`
  pair). None is ambiguous. Unlike Task 7's 13 leaves, where 2 came back
  `never-reached`, reach is **not** a blocker for Class 2.
- **Key reach on the `R|<name>|` completion event, not the `I|` intent
  event.** The round-1 hole is live here rather than hypothetical: measured
  this session, **5 of the 7 files holding the 11 Class-2 protos truncate at
  the 3000-event cap** (`snr_common`, `snr_graphic`, `snr_lib`, `snr_memory`,
  `snr_music` all at 3001 events; `snr_mainmenu` terminates after **18** events
  and `snr_story_main` after **11**). Corpus-wide the probe reproduces
  **132 `CAP` / 97 `OK` / 398196 events**, with the `CAP` files carrying
  **99.48%** of all events and the 97 `OK` files a **median of 10**. An
  `I|`-keyed reach test on a file that is one event from the cap returns
  `identical` for a run in which the target executed nothing.

**And the sharpest single argument in §5 comes out of that same 18-event run —
on a named instrument, with the verdict that instrument actually gives.** Two
instruments have to be kept apart here, because an earlier revision of this
note conflated them:

- **The L1.75 gate** (`scripts/probe_behaviour.py` /
  `tests/test_behaviour_probe.py`, original vs **our artifact**) does **not**
  say `agree` on `snr_mainmenu.lua`. It is one of only **two pinned
  divergences in the whole corpus**
  (`probe_behaviour.EXPECTED_DIVERGENCE["snr_mainmenu.lua"]`), pinned on the
  `__pld_R` `getobjname` naming artifact.
- **The predecessor arm** (`scripts/cross_corpus.py --arm behaviour`, original
  vs **predecessor** — the arm the plan amendment quoted) is the one that
  agrees. Run this session:
  `cross_corpus.py --arm behaviour --file snr_mainmenu.lua` returns
  **`1/1 agree, 0 divergent (0 pinned); reach complete=1`**.

**What that agreeing run actually does, read off the trace rather than
inferred.** 18 events: `G|main`, `I|main`, **15** stub calls, then
`R|main|attempt to perform arithmetic on field 'library' (a nil value)`. The
chunk's `CLOSURE`/`SETGLOBAL` pair binds the global `main` to subproto index 7,
so the entry **is** `main_7` and the target **is** entered — its own first four
calls, at pcs 3, 6, 9 and 11, are the trace's first four `C|` events. At
pcs 12–13 it calls a helper through an **upvalue** (`GETUPVAL R0; CALL R0` —
precisely the call-graph gap Task 4 §3.4 named as the reason
`protos_reaching_poll` is a floor), that helper contributes the remaining 11
stub calls and then raises. **Execution never reaches the first of the four
poll sites, at pc 26** — it dies 13 pcs into a 2182-instruction screen.

A dynamic arm that reports `agree` on a run which errored out before entering
the screen's first poll loop is not evidence about that screen. That is the
argument, and it is stronger than the one the earlier revision made, because
the run does not merely stop early — it stops before the thing under test.

---

## 4. Assumptions, each labelled

The project's dominant defect is prose asserting behaviour nobody ran, and a
design note is pure prose. Every assumption this note or the design it
describes rests on is listed, with its status.

**Measured this session (15):**

1. The class census and the 78% per-iteration overlap. — 162 → 113/11/38;
   127/162 split 113/11/3.
2. The dominance refinement of that predicate, 118/127 with the 9 named
   exceptions. — re-implemented from scratch, exact agreement.
3. The poll-loop cut correspondence on all 19 protos, cell for cell, and
   `snr_music:main_3`'s inverted-tuple back edges. — re-implemented from
   scratch.
4. That 2 of the 19 ship structured text (`snr_lib:main_1`,
   `snr_fragment_main:main_3`) and 17 ship fallback; 9 `L3` / 10 `L1`.
5. The five-of-six defect concentration in `ui-keyloop`, and its **three
   controls**: the exhaustive loss sweep flags 9 of 11 `ui-keyloop` against
   2 of 113 `choice-branch`; the size-matched split at >= 200 instructions
   (8/9 vs 1/21 against an 8.0% baseline over 264 protos, with the full
   size-bucket table); and the `LOSS_KINDS` provenance (5 of 8 are
   `ProtoSignature` fields present at `b666a1c`, the two M6-added loop kinds
   flag exactly one row on their own and it is `choice-branch`).
6. The Class-2 structural profile (median 461 instructions, 10 of 11 leaf
   refusals, 1 of 11 `L3`).
7. That exit-less poll loops are 4 of 14, all in one proto.
8. That "state" as the footprint's keys is unavailable — **18 of 177 write
   sites nameable**, counted by opcode (`SETTABLE` 85 / 3 attributed,
   `SETGLOBAL` 15, `SETUPVAL` 77) and cross-checked against
   `footprints.json`'s own accounting identity; `main_7` at 2 writes / 271
   calls.
9. That our fallback side has no loop to cut but does keep the `GETGLOBAL`
   sites (6/6, 8/8, 36/36, 3/3), spilled through `__pld_R`. The disassembly
   window's pcs were confirmed against `luac_sz4 -l -l` on our own emitted
   source.
10. Reach: 11 of 11 name-resolvable, one entry each; 5 of 7 holding files
    truncate at the cap; corpus 132 `CAP` / 97 `OK` / 398196 events, `CAP`
    share 99.48%, `OK` median 10.
11. Cost: 385 drives/s warm, 694 assignments over the 11, so ~3.6 s.
12. **The L2 harness figures for `snr_music.lua`** under
    `probe_keyseq.probe_raw` with spec `entry=main;tail=` (no key ever
    pressed): original `CAP` / **3001 events / 2502 polls** over 417 distinct
    frames; predecessor source `OK` / **94 events / 6 polls** on **one** frame.
    Cited in §2.1 and previously absent from this accounting.
13. **`snr_common.lua`'s L1.75 truncation**: `PROBE1|CAP|3001`, **79**
    function-valued globals published, **1** invoked (`I|autoSystemSave` ->
    `R|autoSystemSave|CAP`), `keyWait` never invoked. Cited in §3.5 and §5.1
    and previously absent from this accounting.
14. **The two behaviour verdicts kept apart in §3.5**:
    `snr_mainmenu.lua` is one of `probe_behaviour.EXPECTED_DIVERGENCE`'s two
    pinned rows, while `cross_corpus.py --arm behaviour --file
    snr_mainmenu.lua` returns `1/1 agree, 0 divergent; reach complete=1`; and
    the 18-event trace's own composition (`G|`, `I|`, **15** `C|`, `R|` with an
    arithmetic-on-nil error), with the global `main` resolving to subproto
    index 7 and the first four `C|` events matching `main_7`'s own calls at
    pcs 3/6/9/11.
15. **The two historical checkpoint specs do not reach their gates** (§5.3):
    `OPTION_CLAMP_SPEC` gives `OK|376|0` / 129 polls and `CONFIG_GATE_SPEC`
    gives `OK|202|0` / 37 polls, **byte-identical between the original and the
    predecessor** on both.

**Unmeasured (8) — each of these is a claim this note makes or the design would
rest on, and none of them was run:**

1. **That a value-level tracker through `__pld_R`'s constant-numeric keys would
   in fact recover all the fallback-side poll call sites.** §3.1 measured that
   the `GETGLOBAL` survives and exhibits the spill pattern at one site. No
   tracker was written and no site census was run against one.
2. **That the sentinel-raising one-iteration bound is implementable at all.**
   §3.4 describes a mechanism. Nothing was built; the failure mode named there
   (3 of 11 do not re-enter through the poll) is measured, but the mechanism's
   *success* on the other 8 is not.
3. **That the M2 fallback's emitted text is semantically exact.** This is a
   design property of `structure/fallback.py` backed by the compile gate and
   the two standing probes, not a proof. §3.2's argument that mission 2 has no
   target below the certification line depends on it.
4. **That Task 11 / M7 will actually convert the 11 to `L3`.** §5's primary
   recommendation assumes work that has not been done. Its premise — that 10 of
   11 are leaf refusal sites, so the work is well-targeted — is measured; the
   outcome is not.
5. **That the defect concentration is causal ("screens are hard") rather than
   correlational.** §1.1 controls for hand-attention bias with an exhaustive
   instrument. It does not establish a mechanism, and n = 11.
6. **That any of this generalises past this corpus.** 229 files from one game.
   MEMORY.md's standing note that the corpus is a weaker oracle than it looks
   applies in full.
7. **That per-iteration transition equivalence would imply whole-loop
   equivalence.** It does under a bisimulation argument *if* the state
   abstraction is complete — and §3.3 measured that it is not (18 of 177 write
   sites nameable, with the loop-carried `SETUPVAL` half entirely unnameable).
   So the design's central claim to "sidestep termination" has no proof, and
   this note does not supply one.
8. **That the two `probe_enum` divergences on this population are exactly the
   `__pld_R` `getobjname` naming artifact and nothing else.** That
   adjudication is Task 7's and was not re-derived here; this note reproduced
   the verdict counts, not the adjudications behind them.

---

## 5. Recommendation: do not build the Class-2 dynamic prototype

**Recommendation: do not build `scripts/probe_uiloop.py` as designed.** Build
the three cheaper things in §5.2 instead. The prototype was already cut from this
task by the amendment; this section says it should stay cut in M7 as well, and
why, weighed against the evidence for the other side.

### 5.1 The evidence weighed

**For building it.** The population is right. Class 2 is where 5 of 6 confirmed
defects live and where 10 of 11 protos still refuse our structurer. The
enumeration is cheap (694 assignments, ~3.6 s). Reach is solved (11/11 named).
There is a real coverage argument that `probe_enum`'s enumerated product would
find things a single stub drive misses when Tasks 9–12 change reconstruction —
and `snr_mainmenu:main_7`'s **16 of 128** diverging assignments (re-derived
this session: 16 diverge, 112 agree byte-for-byte) shows a sampler had roughly
a 12% chance of seeing that one.

**Against, and it is heavier.**

1. **Mission 2 has no target** (§3.2). The one Class-2 proto that certifies
   already has a stronger proof; the ten that do not have no loop to cut and
   ship a state machine that is exact by construction.
2. **Mission 1's comparison is already done, statically, and better.**
   `scripts/loss_sweep.py` re-run this session: **3.47 s over 1944 pairs**, all
   six defects named with instruction-level walks, **9 of the 11 Class-2 protos
   flagged**, and **17 of the 19 poll protos** in its output. The two poll
   protos it misses (`snr_common:main_29`, `main_81`) were both driven by
   `probe_enum` this session and neither produced a semantic finding —
   `main_81`'s `divergent` is the known `__pld_R` naming pin. The milestone's
   own summary holds: **all six defects were found by the static arm and five
   were invisible to both dynamic arms.**
3. **Task 7's measured conclusion applies directly.** Its honest restatement is
   that the **targeted named entry** earned its keep and the **enumerated
   product bought nothing on that population**; both pinned divergences
   reproduce under a no-assignment drive, and **no row makes enumeration
   load-bearing**. A Class-2 transition prototype is enumeration *plus* a
   harder state model — it inherits the half that did not pay and adds cost to
   the half that did.
4. **The state model is measurably unavailable** (§3.3): **18 of 177 write
   sites nameable (10.2%)**, and the 77 unnameable `SETUPVAL` sites sit in
   exactly the three protos whose loop exit depends on accumulated state.
   Without a complete state abstraction the design's claim to sidestep
   termination does not go through (§4, unmeasured #7).
5. **The iteration bound is wrong on 3 of 11 targets** by the dominance
   measurement (§2.2, §3.4), and fixing it needs loop structure the fallback
   side does not have.
6. **The dynamic arms' blindness on this exact population is measured**, not
   inferred (§3.5): on the predecessor arm
   (`cross_corpus.py --arm behaviour --file snr_mainmenu.lua`) the verdict is
   **`1/1 agree`** for a run that raises after 18 events, **13 pcs into
   `main_7` and before its first poll site at pc 26** — while that proto
   carries four deleted progress gates. And `snr_common.lua` spends its whole
   3000-event budget inside **1 of 79** function-valued globals
   (`PROBE1|CAP|3001`, one `I|autoSystemSave`), so `keyWait` is never invoked
   at all.

Cost is deliberately **not** on this list. At 385 drives/s the whole thing runs
in seconds. The objection is yield.

### 5.2 What to do instead

1. **Convert the population rather than instrument it.** Ten of the eleven
   Class-2 protos are leaf refusal sites in our own ledger, and **eight of the
   eleven are among Task 7's 13 demonstrated leaves** (all but
   `snr_common:main_29`, `snr_lib:main_1` and `snr_story_main:main_3`, measured
   this session). Making them certify `L3` replaces
   every behavioural question about our own output with a byte-exact proof, and
   it is the milestone's existing highest-ranked item. This is the primary
   recommendation.
2. **Extend the static sweep, not the dynamic arm.** The sweep found everything
   at 3.47 s and its known gap is that it sweeps **losses only**: defect #2's
   `EQ +7 / LT +2` is a *gain* that nets out against its `TEST -1 / TESTSET -2`
   loss, which is exactly how the aggregate test-op count hid it, and
   `main_76_2`'s `n_back_edges 1 -> 4` is a gain and unswept. A gain sweep with
   a per-opcode reading is the cheapest remaining instrument in the tree.
3. **If a dynamic Class-2 arm is ever built, build only the separable cheap
   half**: `probe_enum`'s targeted named entry plus the `R|`-completion reach
   discipline, driven with a **single default stub assignment**, over the 11.
   That is ~22 drives, it reuses code that exists, and it is precisely where
   all the measured dynamic yield came from. No enumeration, no state snapshot,
   no iteration bound. Everything beyond it is prospective, and the case for it
   should be re-argued when Tasks 9–12 have actually changed reconstruction —
   because that is the only stated scenario in which enumeration becomes
   load-bearing.

### 5.3 The brief's Step 3, and where it went

The original brief's Step 3 asked for an **L2 lower bound on the predecessor
side**: run `probe_keyseq.evaluate` with the 5 driveable files' authored
sequences, predecessor text as the candidate, and land the result in the
divergence ledger either way. The 2026-08-14 amendment's "design note only"
governs and Step 3 is not delivered here. It is recorded rather than dropped
silently, with the one measurement this note has that bears on it:

**The module's own authored specs do not reach the arms the two historical
checkpoints select, and that reproduced this session.** Driving
`snr_common.lua`'s original bytecode and the predecessor's source through
`tests/test_keyseq_checkpoints.OPTION_CLAMP_SPEC` and `CONFIG_GATE_SPEC`
returns **byte-identical traces on both sides**:

```
OPTION_CLAMP_SPEC   original OK|376|0 polls=129   predecessor OK|376|0 polls=129   identical
CONFIG_GATE_SPEC    original OK|202|0 polls=37    predecessor OK|202|0 polls=37    identical
```

So Step 3 run with the existing sequences would return `agree` on the very file
that carries confirmed defect #2, and that `agree` would mean nothing. If M7
picks Step 3 up, **the sequences are the deliverable, not the harness run**:
the harness exists and the authored specs are the part measured not to reach.

This is also the predecessor-side conditional §3.2 refers to.
`probe_enum` cannot serve it — its `_payload` has two sides, `original` and
`decompiled`, and Task 7 recorded the predecessor arm as deliberately dropped.
A predecessor-side dynamic arm is `probe_keyseq`'s or `cross_corpus.py`'s, and
both already exist.

---

## 6. Numbers and claims that did not reproduce

Five: two of my own from round 0, two from Task 4 §5.6, and one from the round-1
review. None changes a conclusion; two of the five made a conclusion sharper.

**Mine, round 0 — both were real defects and both are corrected in place.**

0a. **"The footprint can name 3 of the 85 write sites these eleven protos make:
    3.5%", and "`main_7` … makes zero write sites"** (§3.3). `write_sites`
    counts `SETTABLE` only; `SETGLOBAL` lands in a **fully named** channel and
    `SETUPVAL` is excluded from the footprint entirely. Counted by opcode this
    session: **`SETTABLE` 85 (3 attributed) + `SETGLOBAL` 15 + `SETUPVAL` 77 =
    177 write sites, 18 nameable = 10.2%**, and `main_7` makes **2**
    `SETGLOBAL` writes. The table's cells were right; the label was wrong, and
    it was labelled *measured*, which is worse than a wrong number. The
    conclusion strengthens — the 77 invisible `SETUPVAL` sites are concentrated
    in the three protos whose loop exit depends on accumulated state.

0b. **"`snr_mainmenu.lua` completes the standing behaviour gate in 18 events
    and the gate says `agree`"** (§3.5, §5.1 item 6). Two instruments were
    conflated. On the **standing L1.75 gate** (`probe_behaviour.py`, original
    vs our artifact) `snr_mainmenu.lua` is one of only **two pinned divergences
    corpus-wide** — it does not say `agree`. The verdict I wanted is on the
    **predecessor arm**: `cross_corpus.py --arm behaviour --file
    snr_mainmenu.lua` returns `1/1 agree, 0 divergent; reach complete=1`. And
    "completes" was wrong too: the run **raises** after 18 events. §3.5 now
    names the right instrument and says what the trace does. The argument
    strengthens — the run dies at pc 13, before `main_7`'s first poll site at
    pc 26.

**Task 4 §5.6 — both now carry an inline correction in that report.**

1. **§5.6's table is labelled "headers" and its numbers are back edges.**
   Measured this session on the four files it names, computing both:

   | file | report "headers", orig / ours | my headers, orig / ours | my back edges, orig / ours |
   |---|---|---|---|
   | `snr_lib.lua` | 2 / 2 | 2 / 2 | 2 / 2 |
   | `snr_music.lua` | 4 / 203 | 3 / 13 | **4 / 203** |
   | `snr_memory.lua` | 12 / 320 | 8 / 12 | **12 / 320** |
   | `snr_mainmenu.lua` | 40 / 1210 | 20 / 57 | **40 / 1210** |

   The report's numbers are the back-edge column exactly. This is the same
   header/latch conflation that §3.1 and §5.4 of that report correct at length
   — it survived in §5.6's hand-built table. The poll and proto columns
   reproduce exactly (1/0/0/0 polls, 3/5/6/9 and 3/14/16/22 protos), and the
   conclusion the table supports is unaffected.

2. **"`pressButton` is never called through a `GETGLOBAL`-loaded register at
   all" (Task 4 §5.6) is false as stated.** The `GETGLOBAL pressButton` sites
   survive the fallback exactly (6→6, 8→8, 36→36, 3→3, measured this session).
   What breaks is the register adjacency between the load and the call, because
   the value round-trips through `__pld_R`. §3.1 gives the disassembly. The
   report's conclusion — that the poll-loop cut finds nothing on our fallback
   side — reproduces; its stated mechanism understates what is recoverable.

**From the round-1 review — a pc-convention finding, in the falsified
direction.**

3. **"The `GETGLOBAL` in `snr_music.lua`'s fallback is at pc 35 0-based; you
   print 36–42."** The site is the same one; the convention claim does not
   hold. **This project is 1-based**: `lift.py:42` decodes `p.code[pc - 1]` at
   `pc`, and `luac_sz4 -l -l` on our own emitted source numbers that exact
   instruction **36**, verified this session:

   ```
   35  [341]  JMP        14      ; to 50
   36  [342]  GETGLOBAL  4 -10   ; pressButton
   37  [342]  SETTABLE   0 -1 4
   ```

   The milestone's own standing warning is that `luac -l -l` and
   `pyluadec.lift` are 1-based and that a 0-based reading already cost one
   brief its pcs. §3.1's numbers stand; what they were missing is the explicit
   **label**, which the header now carries.

Two figures came out **different but not contradictory**, and are recorded so a
later reader does not mistake either for a regression:

- **`probe_enum` throughput 385 drives/s** here against Task 7's **338** and
  the round-1 review's **420**. Same measurement (256 warm drives on
  `snr_mainmenu:main_7`), host noise; nothing in §5 turns on it.
- **The loss sweep's size-bucket rates.** The review reported "5.6–9.0% above
  200"; measured here the two buckets above 200 are **9.4%** (200–499) and
  **5.3%** (>= 500), so the range is 5.3–9.4% under my boundaries. Bucket
  edges differ; **the size-matched result the buckets exist to support —
  `ui-keyloop` 8/9, `choice-branch` 1/21, baseline 8.0% over 264 protos —
  reproduced exactly.**
- **The CLI's `distinct=` column is over the ADJUDICATED prefix**, the report's
  table over the whole product. `main_7` prints `run=53 distinct=12` and the
  report's table says `14 / 128`. Both are right; the suite pins the latter
  (`test_what_an_identical_verdict_explored_on_each_corpus_row`).

Figures from earlier tasks that **did** reproduce exactly this session: the
class census 113/11/38; 127/162 and its class split; 118/127 with all 9 named
exceptions; 14 of 162 loops-vs-back-edges; 146/162 candidates with 946
unattributed calls; the whole 19-row cut table; `snr_music:main_3`'s back-edge
tuples; 2 of 19 shipping structured; `probe_enum`'s `identical 8, divergent 2,
budget-exceeded 1, never-reached 2` at 5.61 s; `snr_s4_10_s:main_58` at 23616
against the published 1152; the fine budget census **1936/1944**, **155/162**,
**106/113** with worst ratios 29.5x / 22.0x / 21.0x / 20.5x; `main_7`'s
**16 of 128**; the loss sweep's 25 protos over 1944 pairs at 3.47 s with all
six defects; the behaviour probe's 132 `CAP` / 97 `OK` / 398196 events.

---

## 7. Suite cost

**Zero.** This task adds one document under `docs/reports/` and edits one more
(`m6-observation.md` §5.6 and §10, the two corrections in §6) — no `scripts/`
file, no test, no fixture, no data. Verified by running the full suite with
both corpus variables set: **996 passed in 54.11 s** before round 0,
**996 passed in 52.97 s** after it, and **996 passed in 56.41 / 56.53 s** after
round 1, against the ~120 s earmark. `corpus/ledger.jsonl`,
`corpus/observation/*.json`, `corpus/golden/` and `vendor/` were not written
to; every measurement in this note was taken read-only or in a scratch
directory outside the tree.

---

## 8. What M7 inherits

1. **The class boundary is a triage prior, not an instrument selector** (§1).
   Class 2 is 6.8% of the candidates, 83% of the confirmed defects, and 82%
   flagged by an unbiased static sweep — and the enrichment survives all three
   controls: discovery order, `LOSS_KINDS` provenance, and **size** (8/9 vs
   1/21 at >= 200 instructions, against an 8.0% baseline). Use it to rank work;
   do not use it to justify a second instrument family.
2. **Termination is shared, and total non-termination is one proto** (§1.3,
   §2.2). `snr_mainmenu:main_7` is the only proto with exit-less poll loops.
3. **The recommendation is: convert the 11, extend the static sweep, and if a
   dynamic arm is built at all build only the targeted-entry half** (§5.2) —
   with the conditional §3.2 states, because `probe_enum` is a mission-2
   instrument and mission 2 has no window until Tasks 9–12 change
   reconstruction.
4. **Both pre-measurements, with their criteria stated** (§2): the cut is
   15/19 literally, 18/19 after adjudication, 1 structural failure that is a
   confirmed defect; and 127/162 which is 118/127 under dominance.
5. **Eight unmeasured assumptions are named** (§4). Any M7 task that builds on
   this note should close the ones it depends on before, not after.
6. **Four corrections applied, two of them to `m6-observation.md` §5.6** (§6):
   the headers/back-edges mislabel and the over-stated `__pld_R` mechanism
   sentence, both now carrying an inline correction in that report and a row
   in its §10; plus two of this note's own round-0 errors — a `SETTABLE`-only
   counter read as a write census, and a behaviour verdict attributed to the
   wrong instrument.
7. **The brief's Step 3 is undelivered and its blocker is measured** (§5.3):
   the two authored checkpoint specs give byte-identical traces on both sides,
   so an L2 lower bound run with them would agree vacuously. The sequences are
   the deliverable, not the harness run.

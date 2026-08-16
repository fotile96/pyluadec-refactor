# M8 handoff — from the controller session, 2026-08-16

Written after merging M7 to master (`0d39272`) and reviewing M8 tasks 1–3.
Audience: whoever drives M8 from here. Everything below was measured at
`b4d20eb` on branch `phase8-m8-zero-doubt-handoff` unless dated otherwise
— house rule stands, re-derive before relying on any of it.

## 1. Where the tree stands (verified, so you need not redo it)

```
master            0d39272  Merge phase7-m7-semantic-warranty-glm53
M8 branch tip     b4d20eb  (5 M8 commits + this record on top of the M7 tip)
suite             1183 passed / 66.65s   (M8 branch)
                  1174 passed / 67.05s   (merged master)
ratchet_job.sh    exit 0 on both
ratchet vs 72cb6a8   3 upgraded, 0 downgraded, 2 occ fallback -> structured
```

Ledger: **L3 1459/1478 unique (98.7%)**, **L3 1925/1944 occurrences
(99.0%)**, **shipped structured 1882/1944**, 19 non-`L3` rows **all
`mismatch:`**, products **223 fully structured / 4 hybrid / 2 whole-file
fallback**. Footprint non-1.0 files are now six: `snr_mainmenu` 3.5598,
`snr_music` 3.3440, `snr_novel` 2.8752, `snr_graphic` 1.9509,
`snr_story_main` 1.6956, `snr_common` 1.3994 — and `snr_memory` reached
1.0000 and left the set.

Tasks 1–3 are sound work. I re-ran every headline number in their reports
and they reproduce. Two things they did deserve to be copied, not just
noted: task 2's commit records that **the plan's own expectation did not
reproduce** (rows 22→22, not 22→20) with the real blocker stack measured;
task 4/5's census **corrected a hypothesis in the plan I wrote**. That is
the discipline this repo has spent three milestones trying to install.

## 2. Carried in from M7's final whole-branch review

The review ran late (after M8 tasks 1–3 landed) and returned **merge, no
Critical, nothing requiring a rewrite of M7 commits**. Its **seven
Important findings are M8's work**, enumerated with measurements in
`docs/reports/m7-warranty.md` §5 and routed in `docs/runbooks/m3-backlog.md`
"7. Carried in from M7's final whole-branch review".

Two of them I would not let slide to the end of the milestone:

- **IMP-2 — the mechanism-F attribution is wrong by ~4×.** Six committed
  sites say pred boilerplate dead locals "fail the root `maxstacksize`
  comparison in **228 of 229** files". Measured: **163** — the other 58
  roots fail on `code` with *equal* maxstacksize, so mechanism F is not
  what stops them. This is the sentence the merge deliverable's honesty
  argument rests on, and it is now on master in `CLAUDE.md`,
  `CHANGELOG.md`, `m7-warranty.md`, `m3-backlog.md`,
  `structured-pipeline.md` and the M7 spec. Correct all six together;
  correcting one is how a number ends up with two live spellings.
- **IMP-1 — `tests/test_m7_exit.py:78` is a tautology.** It skips any
  literal whose bracketed text decodes to pure ASCII, which is exactly
  what an escaped literal is, so the ratio is identically 1.0 for every
  possible input; rewriting all of `corpus/final/` to escaped form leaves
  it green. **M8's exit criterion 3 is a footprint ratio and its
  readability criterion is the same shape** — write M8's gates so that the
  mutation that should break them actually does, and prove it in the same
  commit. A gate that cannot fail is this repo's stated worst case.

## 3. Three changes I would make to the M8 plan itself

I wrote that plan; these are corrections to it, not requests.

### 3.1 Task 6's petition unit must be the **rung bundle a row needs**, not one rung

The tasks 4/5 census established: **no single rung alone certifies any
remaining row.** `snr_music:main` needs the pool-order rung *and* a
maxstacksize clause; the K1 rows need the hint rung and live in the `code`
family. The plan says "one petition, one decision", which would get an
`L3.2` approved that **certifies zero rows** — a comparator weakened for
no return, the worst possible trade. Restructure: one petition per *row or
row-family*, listing every rung that row needs, approved or refused as a
bundle. Rows whose bundle is refused go to the §1 stop-loss.

Amend the plan and commit the amendment with its reason (M6/M7 precedent),
rather than discovering this at Task 6.

### 3.2 The ≤1.5× exit gate has collapsed to two rows — say so in the risk section

Of the six over-budget files, only `snr_music` (3.34×) and `snr_novel`
(2.88×) are whole-file fallback, and **each is held by one root row**:
`snr_novel:main` is constructor layout (emitter-side, tractable),
`snr_music:main` is 58-item pool reorder + maxstack-below-original
(needs the bundle in 3.1, i.e. needs partner approval). So exit criterion
3's feasibility rests on those two rows.

There is a live tension worth surfacing to the partner **now**:
`snr_music` carries **no translatable text**, so if its bundle is refused
it lands cleanly in the spec §1 stop-loss — but that leaves **3.34× in the
shipped corpus**, contradicting the 1.5× ceiling the same partner set. One
of the two has to give, and it is better decided in the open than at Task
10.

### 3.3 Report rows and shipped-fallback occurrences as the primary metric

Task 2 closed the `structure:` family — a genuine capability milestone
(`build_sir` now accepts every corpus proto) — with **zero row movement,
zero product movement, zero footprint movement** (22→22; it converted two
`structure:` rows into two `mismatch: code` rows). All three of the rows
closed so far came from task 3. "Two refusal families extinct" is true and
reads like progress toward the goal; the goal is fallback → 0. Lead with
rows and fallback occurrences; keep the family census as secondary
diagnostics.

## 4. One committed error to fix in the same sweep as IMP-3

`docs/runbooks/structured-pipeline.md:4279` publishes
`**L3** 1459/1478 (98.7%) / **1882/1944 occurrences**`. **1882 is the
`shipped == "structured"` count; L3 occurrences is 1925.** This is the
same word collision CLAUDE.md already records from M6 (finding 14:
`sir/build.py` used "structured" for occurrence-`L3` while the ledger uses
it for shipped text), firing in the opposite direction. IMP-3 is the same
class (occurrence-`L3` published as 97.9% in four documents when it was
98.9% at M7 close). Fix them together and, if you touch the wording, make
the two quantities un-confusable at the point of use.

## 5. Process notes

- **M8 opened on an unreviewed, unmerged M7.** No harm resulted — all
  seven findings were fix-forward — but the review had to reason about
  five M8 commits sitting atop the range it was auditing. The plan's
  prerequisite section exists for this; it was not followed. Now closed:
  master carries M7 as of `0d39272`.
- The merge brought the M8 spec and plan into master too: those three
  docs commits were authored on the M7 branch before M8 branched from it.
  Harmless, documented here so nobody re-derives the surprise.
- `ratchet_job.sh`'s default baseline is `72cb6a8` (M7 branch tip), which
  is content-equivalent to the merge commit's ledger and reachable from
  master. Leaving it is fine; if you move it, move it to `0d39272` and say
  why in the commit.
- The M7 SDD ledger stops at task 10 — tasks 11/12 have no entries.
  `72cb6a8`'s commit message is a complete and spot-verified record of
  them, so nothing is lost, but **if M8 runs in-session again, write the
  ledger as you go**: a milestone whose only record is commit messages
  cannot be resumed after a context loss.

## 6. The thing to carry, which is not any individual number

M7's review found the milestone's own documented defect class — prose
asserting behaviour nobody ran — recurring **inside the round written to
correct it**: task 12 corrected two false sentences and shipped a gate
whose "measured 1.0000" is arithmetically forced. M8 is the milestone that
adds a footprint gate, a naming pass with a coverage figure, an inventory
with a reconciliation count, and a migration guide full of claims about
another repository's tools. Every one of those is a place this defect
lands. Measure each behavioural sentence before committing it, including
the ones no test asserts, and treat every superlative — only / always /
never / complete / all / exactly — as owing a measurement or a rewrite.

# 64-bit migration runbook

This is the operational playbook for standing up `pyluadec-refactor` on a
fresh 64-bit machine and declaring the Phase 1 migration (M1) complete. It is
meant to be followed literally, top to bottom, by someone who has never
touched this repo before.

## Why this exists

The project was bootstrapped (Phase 1 / M0) on a 32-bit i686 Gentoo userland,
because that is what the *original* `pyluadec` project required (it loads
32-bit Lua bytecode by mapping it directly onto host C structs, so it needed
a 32-bit host to match `sizeof(size_t)`). The whole point of this rewrite is
to stop depending on that: the ingest layer parses bytecode using a
serialization width read from the file header, independent of the host's
pointer size. `scripts/verify_migration.sh` exists to prove that claim by
running the same three correctness gates — build, roundtrip, and golden
parity — on any host and requiring identical PASS output.

M0 is "all gates green on the original 32-bit box" (already done). **M1 is
"all gates green on both a 64-bit Linux x86_64 host and a 64-bit macOS arm64
host."** Both, not either — see "Why two platforms" below.

## Prerequisites (fresh machine)

Install these before cloning:

- **git** — to clone the repo.
- **CMake ≥ 3.24** — builds the vendored Lua 5.1.5 (patched) and the two
  pybind11 bridges. The repo's `CMakeLists.txt` does not use anything newer
  than 3.24 features; that floor is a safety margin, not a hard requirement
  discovered by trial and error.
- **A C/C++ toolchain** — a C compiler for Lua itself, a C++ compiler
  (C++17-capable) for the pybind11 bridge modules.
- **uv** — manages the Python environment, dependency lock, and `pytest`
  invocation for this project. Version used during Phase 1 development:
  0.11.16; any reasonably current uv should work.
- **GNU patch** — applies `native/patches/0001-serial-sizet.patch` to the
  vendored Lua sources at configure time (invoked from `CMakeLists.txt`, not
  by hand).

### Linux x86_64

Use your distribution's package manager, e.g. on Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y git cmake build-essential patch curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Confirm versions:

```bash
git --version
cmake --version      # must report >= 3.24
gcc --version && g++ --version
patch --version
uv --version
```

### macOS arm64 (the primary future host)

```bash
xcode-select --install     # provides clang/clang++ and GNU patch
brew install cmake uv
```

Notes specific to macOS:

- The Xcode Command Line Tools provide both the C/C++ compiler (`clang`,
  `clang++`) and `patch` — you do not need a separate Homebrew package for
  either.
- The native build deliberately does **not** link `readline` and compiles
  Lua with `LUA_USE_POSIX` (see `native/CMakeLists.txt`), specifically so
  that no extra library (readline/editline) has to be located or installed
  on macOS. If a future change reintroduces a readline dependency, this
  runbook and that CMake logic need to be revisited together.
- APFS (the default macOS filesystem) is case-insensitive by default. This
  is a non-issue for this repo: every filename in the corpus and in
  `corpus/golden/` is already lowercase, so there is no case-collision risk.
  Worth knowing if the corpus or golden set ever grows filenames that differ
  only in case — they would collide on macOS but not on Linux.

Confirm versions the same way as Linux (`cmake --version` must still report
`>= 3.24`).

## Obtaining the corpus

The 229-file bytecode corpus is not part of this repo (see "Golden baseline
is read-only" below). On the current 32-bit reference machine it lives at
`/root/pyluadec/others/script_to_decompile/`. To migrate:

1. Copy that entire directory to any path on the new machine (USB drive,
   `scp`, `rsync`, tarball — the transport doesn't matter, only the file
   contents do). Do **not** cherry-pick files; the golden baseline in
   `corpus/golden/` was captured against the full 229-file set and gate ③
   expects all of them to be present.
2. Point the environment variable at wherever you put it:

   ```bash
   export PYLUADEC_CORPUS_DIR=/path/to/script_to_decompile
   ```

   Nothing in this repo's committed code hard-codes a corpus path — every
   script and test reads `PYLUADEC_CORPUS_DIR` at runtime, and corpus-gated
   pytest tests simply `pytest.skip(...)` if it's unset or points at a
   missing directory (see `tests/conftest.py`). Set it before running
   anything below.

## Clone, sync, verify

```bash
git clone <this-repo-url> pyluadec-refactor
cd pyluadec-refactor
uv sync
export PYLUADEC_CORPUS_DIR=/path/to/script_to_decompile   # if not already set
./scripts/verify_migration.sh
```

Expected final line on success:

```
ALL MIGRATION GATES PASSED on <arch> / <kernel>
```

e.g. `ALL MIGRATION GATES PASSED on arm64 / Darwin` on the Mac mini, or
`ALL MIGRATION GATES PASSED on x86_64 / Linux` on the Linux box. Anything
else — a non-zero exit, a stack trace, a gate printing failure output —
means the run did not pass; see Triage below. `verify_migration.sh` runs
with `set -euo pipefail`, so the first failing command aborts the whole
script immediately with a non-zero exit code; it will not silently continue
past a broken gate.

## The three gates, and how they map to spec §6 Step 2

`scripts/verify_migration.sh` is pure orchestration — it does not
reimplement any check itself, it just calls the three gate scripts (plus the
full test suite) in sequence and stops at the first failure:

| Gate | Script | What it proves | spec §6 Step 2 correspondence |
|---|---|---|---|
| ① Build | `./scripts/build_native.sh` | The vendored Lua 5.1.5 (with the serialization-width patch) and both pybind11 bridges (`_bridge_sz4`, `_bridge_sz8`) compile clean on this host/toolchain, producing `build/{lua,luac}_{sz4,sz8}` and the two `.so` bridge modules. | "构建产物在新环境可复现" — the artifact-reproducibility half of Step 2. |
| ② Roundtrip | `uv run python scripts/roundtrip_sz4.py build/luac_sz4` | `luac_sz4 -s` can load every one of the 229 corpus files and redump it byte-for-byte identical to the original. This is the strongest possible check that the sz4 (32-bit `size_t`) code path is unbroken on the new host: it is not just "parses without crashing," it is "produces the exact same bytes back out." | "sz4 读取/写回字节级一致" — the load↔dump fidelity half of Step 2. |
| ③ Golden parity | `uv run python scripts/compare_bridge_golden.py` | The new header-dispatched `pyluadec.ingest` layer, reading the same 229 files, produces proto structures (opcodes, constants, upvalues, param counts, vararg flags, sub-proto trees) that match the golden baseline captured from the *old* 32-bit-only project's bridge output and `luac -l -l` listings. This is what proves the new architecture is a faithful, host-independent replacement for the old in-process 32-bit-only bridge. | "新 ingest 层与旧实现（golden baseline）语义等价" — the third and final Step 2 check. |

`verify_migration.sh` runs `uv run pytest -v` after the three gates as a
final full-suite pass — this re-covers gates ②/③ (they also run as pytest
tests) plus everything else (vendor checks, patch application, build
artifact sanity, bridge unit tests), so a green full suite plus the three
explicit gate scripts is the complete Step 2 exit signal.

## Why two platforms (dual-platform requirement)

M1 is not satisfied by one green run on one 64-bit machine. **Both** a Linux
x86_64 host and a macOS arm64 host must independently run
`verify_migration.sh` to a clean `ALL MIGRATION GATES PASSED` before the
migration is considered done. The reason is that a single 64-bit host only
proves "not 32-bit"; it does not prove "not accidentally tied to one OS or
one CPU architecture's byte order, struct padding, toolchain quirks, or
filesystem case-sensitivity." Concretely:

- Linux x86_64 and macOS arm64 differ in endianness-adjacent toolchain
  defaults, default C++ standard library, struct packing/alignment
  behavior, and filesystem case-sensitivity (see the APFS note above) —
  exactly the kind of hidden assumption that a 32-bit-only codebase like the
  original project could quietly encode without anyone noticing for years.
- The Mac mini (arm64 macOS) is the intended primary day-to-day development
  host going forward; the Linux x86_64 box (with the RTX 5080) is kept
  around for CUDA-dependent future work. Both need to be first-class
  supported environments, not "works on my machine."

Only after both platforms report green should the switch-over be recorded
(changelog/ledger entry) and development stop returning to the 32-bit
environment.

## Triage when a gate fails

### Gate ② (roundtrip) fails

`scripts/roundtrip_sz4.py` prints `roundtrip: FAIL [<list of filenames>]`
and exits non-zero. For each failing file:

1. Re-run the load→redump by hand and byte-diff:

   `<file>` below is exactly what `roundtrip_sz4.py` printed (it already ends
   in `.lua`, e.g. `snr_crd_1.lua` -- do not append another `.lua`):

   ```bash
   build/luac_sz4 -s -o /tmp/rt.lua "$PYLUADEC_CORPUS_DIR/<file>"
   cmp -l "$PYLUADEC_CORPUS_DIR/<file>" /tmp/rt.lua | head
   ```

   `cmp -l` prints, for every differing byte, its 1-based offset and the old
   vs. new byte value (octal). The **first** line of that output is the
   offset to focus on — everything after it may just be cascading
   misalignment from that first divergence.

2. Take that byte offset and cross-reference it against the corresponding
   golden `luac -l -l` listing in `corpus/golden/listing/<file>.txt` (again,
   `<file>` already ends in `.lua`, so e.g. `snr_crd_1.lua.txt`; every file
   under `corpus/golden/listing/` is a plain `.txt`, and `manifest.json`
   holds only per-file `sha256`/`size`, no layout information) to
   identify which function/instruction lives at that offset in the dump
   format. The listing gives you `pc`, opcode, and (for the header/function
   boundary regions) sizes in bytes, which lets you map a raw offset back to
   "this is inside function N's constant table" or similar, even though the
   listing's addresses themselves are ASLR-tainted and can't be diffed
   directly.
3. Common root causes to check first: a toolchain that pads/aligns structs
   differently than the reference build (unlikely given the patch pins
   serialization width explicitly, but verify `native/patches/0001-serial-sizet.patch`
   applied cleanly — `uv run pytest tests/test_patch.py -v`), or a
   `luac_sz4` built against the wrong `LUA_INT32` /`size_t`-width macros.

### Gate ③ (golden parity) fails

`scripts/compare_bridge_golden.py` writes every discrepancy (not just
failures) to `corpus/discrepancies.json` (deliberately outside
`corpus/golden/`, which stays read-only -- see below) and prints a summary
line `N discrepancies (M unexpected)`. The gate only fails on `M > 0`. To
triage:

```bash
uv run python -c "
import json
d = json.load(open('corpus/discrepancies.json'))
unexpected = [x for x in d if x['verdict'] == 'unexpected']
for x in unexpected:
    print(x)
"
```

Each `unexpected` entry has `proto_path` (which file and, for nested
functions, which sub-proto index path within it), `field` (e.g. `code`,
`numparams`, `constants.len`, `const`, `upvalues`, `subprotos.len` — see
`scripts/compare_bridge_golden.py` for the full field list), and `old`/`new`
values. Read those fields directly — they tell you exactly which structural
element diverged and how, without needing to touch the golden archive
itself (which stays read-only; see below). Entries with `verdict ==
"expected"` are known, accepted differences (e.g. constant encoding
edge cases already reasoned about) and are not migration failures.

### Golden baseline is read-only

`corpus/golden/` (manifest, 229 proto dumps, 229 luac listings) was
captured once, from the *old* project's 32-bit tools, on the reference
32-bit machine, and is never regenerated. If you suspect the golden data
itself is wrong, that is a separate investigation from a migration gate
failure — do not "fix" gate ③ by editing files under `corpus/golden/`.

## The 32-bit environment after migration

Once M1 is declared (both platforms green), the original 32-bit i686
Gentoo box stops being a development environment. It is kept around
strictly as an **arbitration/reproduction site**: if a discrepancy ever
shows up on a 64-bit host and someone needs to reproduce the *original*
32-bit-native behavior to compare against, that box is where you do it. The
original project's checkout, `/root/pyluadec`, is left completely untouched
(no further commits, no experiments) — it is the historical reference this
whole rewrite was built against, and its golden output is what
`corpus/golden/` was captured from. All new development happens against
`pyluadec-refactor` on the 64-bit hosts from here on.

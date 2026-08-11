# Decompile pipeline runbook

This is the operational and conceptual guide to the M2 decompile pipeline:
what each layer does, the module/function to go read when you need the real
answer, the commands you actually run day to day, and — the part that will
save you the most time — how to read the fallback emitter's output when
something looks wrong.

Every command below was run against this repo (branch `phase2-m2-fallback`,
commit range ending at `beeccc1`) before being written down. If a command in
this file stops working, that is a bug in the runbook (or a regression);
file/fix it, don't route around it silently.

## Why this exists

M2's job (see `docs/superpowers/specs/2026-08-09-pyluadec-refactor-overall-design.md`
§7) was to close the loop from raw bytecode to *some* Lua source that is
provably semantically faithful, for all 229 corpus files, with a certification
record that survives re-runs. It deliberately does not attempt readability —
that is M3. This document is the map of what M2 actually built, so that
whoever builds M3 (possibly you, possibly someone with no memory of this
conversation) does not have to re-derive it by reading 1500 lines of source
first.

## The pipeline, layer by layer

```
ingest -> lift -> cfg -> structure.fallback -> oracle (compile-verify) -> ledger
```

### `pyluadec.ingest` — bytes to `Proto`

`pyluadec.ingest.load_file(path) -> Proto` (there is also `load_bytes(data)`
for in-memory bytecode, used heavily by tests and by the differential-exec
harness). Internally this reads the 12-byte Lua 5.1 header
(`pyluadec.ingest.header.parse_header`) and dispatches to one of two
pybind11 bridges built at `./scripts/build_native.sh` time — a 32-bit
(`sizeof(size_t)==4`) and a 64-bit variant — based on what the header says,
not on the size of `size_t` on the host running Python. That header-dispatch
is the whole point of Phase 1; see `docs/runbooks/64bit-migration.md` if you
need the history.

The result is a `pyluadec.ingest.proto.Proto`: a plain-data tree (`code`,
`constants`, `subprotos`, `numparams`, `is_vararg`, `nups`, `maxstacksize`,
`upvalues`, plus the debug fields `lineinfo`/`locvars`/`source` — empty for
this corpus, see CLAUDE.md). Everything downstream operates on `Proto`, never
on the bridge's raw dict.

### `pyluadec.lift` — `Proto` to LIR

Three modules:

- `opcodes.py` — the instruction decoder. `decode(word, pc=...) -> RawInstr`
  plus the `OP_SPECS` table (one row per Lua 5.1 opcode: name, arg format,
  arg modes). This is the layer that turns a 32-bit instruction word into a
  typed `(op, a, b, c, bx, sbx)` tuple. Golden-listing-checked against all
  229 corpus files (`tests/test_opcodes.py::test_decoder_matches_all_golden_listings`).
- `effects.py` — the **axiom layer** (its own docstring calls it that). One
  row per opcode (`_row()`, 38 opcodes) recording which registers it reads,
  which it writes, whether it reads/writes an *open* range
  (`R[base..top-1]`, for the varargs/multi-return opcodes), and its effect
  classification under three modes — see "Effect modes" below.
- `lift.py` — `lift_proto(p: Proto, mode=EffectMode.STRICT) -> LirFunction`.
  Walks `p.code` pc by pc, decodes each instruction, looks up its effects,
  computes successors (`effects.successors`), and — critically — accounts
  for opcodes that consume extra instruction words as operands rather than
  as instructions (`CLOSURE`'s trailing `MOVE`/`GETUPVAL` pseudo-instructions
  that name each upvalue to capture, and `SETLIST`'s extra word when `C==0`).
  Every pc in `p.code` ends up claimed exactly once, either as a real
  instruction or as a "consumed" operand word of the instruction before it —
  this is asserted corpus-wide by
  `tests/test_lift.py::test_corpus_full_pc_claim_audit` (1944 protos, ~210k
  instructions). `lift_proto` raises `LiftError` on anything that doesn't
  add up (out-of-range successor, `CLOSURE` `Bx` pointing outside
  `subprotos`, extra words running past the end of `code`, ...).

### `pyluadec.cfg` — LIR to basic blocks and dominators

- `blocks.py::build_cfg(fn: LirFunction) -> Cfg` — splits the linear
  instruction stream into basic blocks wherever a successor set isn't just
  "the next instruction" (branches, jumps, `CALL`/`RETURN` open-arg edges
  don't split blocks by themselves, but comparison/jump/loop opcodes do).
  `Cfg` is `{entry, blocks: {start_pc: BasicBlock}, preds: {pc: (pred_pcs)}}`.
- `dom.py::immediate_dominators(cfg) -> {pc: idom_pc}` — the
  Cooper–Harvey–Kennedy iterative algorithm, chosen specifically because it
  stays correct on irreducible control flow (arbitrary `goto`-shaped
  bytecode need not be reducible). `dom_tree()` and `dominates()` build on
  top of it. There is a regression test for exactly the case that made this
  choice necessary: `tests/test_dom.py` (see the "fixpoint-iteration
  regression case for irreducible-graph dominators" commit,
  `3907562`).

The CFG is not decorative in M2: `structure.fallback` builds one per
function and dispatches on its block boundaries (see next section) — unlike
the *original* pyluadec's CFG, which spec/CLAUDE.md records as built but
"structure 阶段完全没用" (`structure.py:1434`, `_ = cfg`). Not repeating that
mistake was a design goal.

### `pyluadec.structure.fallback` — LIR/CFG to Lua source (the M2 floor)

`emit_chunk(root: Proto) -> bytes`. This is the only structuring pass that
exists yet. It does not attempt to recover `if`/`while`/`for` — it emits
*every* function, regardless of shape, as a `pc`-dispatch state machine: a
`while true do ... end` loop with one `if __pld_pc == N then ... end` arm per
basic block, where each arm ends by setting `__pld_pc` to whatever the CFG
says that block's successor is. This is a mechanical, total, per-opcode
translation — all 38 opcodes have a translation rule in `_FnEmitter`
(`_emit_simple` for straight-line opcodes, `_emit_terminator` for
control-flow/call/return opcodes) — and it is exactly what "fallback" means
in this project's vocabulary: the pipeline's Plan Z when no smarter
structuring pass claims a region. In M2, it is the *only* pass, so it claims
100% of every function. See "Reading fallback output" below for the output
shape in detail; that section is the one worth bookmarking.

### `pyluadec.oracle` — compile-verify against the real toolchain

`oracle.compile_source(source: bytes, *, strip=False) -> bytes` shells out
to the repo's own vendored, width-patched `build/luac_sz4` to compile
emitted Lua source back to bytecode; raises `oracle.LuaCompileError` (with
`luac`'s stderr) if it doesn't compile. `oracle.run_bytes(payload, *,
is_source, args=()) -> subprocess.CompletedProcess` runs either source or
bytecode through `build/lua_sz4` and gives you back stdout/stderr/returncode.
Both binaries come from Phase 1's dual-width native build
(`./scripts/build_native.sh`); `oracle.build_dir()` resolves their location
(`PYLUADEC_BUILD_DIR` env var, default `<repo>/build`) and raises
`OracleError` with a build hint if they're missing.

Note the comment in `oracle.compile_source` about running `luac` with `cwd`
set to a tempdir and a *relative* input filename: `luac` embeds whatever
filename you pass it as `Proto.source` in the compiled chunk, so an absolute
tempdir path would make two compiles of byte-identical source produce
byte-*different* bytecode. That would have silently defeated any
byte/field-level comparison downstream (`verify.normalize`'s comparator, the
ledger's structural hash). This one bites you immediately if you "simplify"
it back to an absolute path — don't.

### `pyluadec.verify` — comparison and certification

- `normalize.py` — `compare_protos(a, b, level=0) -> list[Mismatch]`. Level 0
  ("L3.0") is a strict, field-by-field comparison of two `Proto` trees:
  `source`, `linedefined`, `lastlinedefined`, `nups`, `numparams`,
  `is_vararg`, `maxstacksize`, `code`, `constants` (bit-exact for numbers —
  `-0.0 != 0.0`), `lineinfo`, `locvars`, `upvalues`, and recursively over
  `subprotos`. `NORMALIZATIONS` is an empty tuple in M2 — the ladder exists
  (`normalize(p, level)` applies `NORMALIZATIONS[:level]`) but has no rungs
  yet; each future rung (e.g. register renumbering) must be added with its
  own soundness argument and must bump `LADDER_VERSION` (currently
  `"l3-ladder-v0"`). This is the "honest strictest baseline" the docstring
  describes.
- `ledger.py` — `structural_hash(p: Proto) -> str` (SHA-256 over a
  canonical JSON view of code/constants/arity/subproto shape — deliberately
  *not* over debug fields, since this corpus has none) and the
  `LedgerEntry` dataclass + `write_ledger`/`read_ledger`. See "Ledger field
  semantics" below.

### `pyluadec.pipeline` — the driver

`walk_proto_paths(path, p, out)` assigns every proto in a chunk a
dotted-suffix path (`main`, `main_0`, `main_0_3`, ...) by recursively
appending each subproto's index in its parent's `subprotos` list, and
collects them into a flat `{path: Proto}` dict — this naming scheme is what
both the fallback emitter's `__pld_F` table and the ledger's `occurrences`
records key on. `decompile_chunk(root: Proto) -> DecompileResult` walks the
chunk, calls `structure.fallback.emit_chunk`, and — since fallback claims
every pc of every proto — builds a trivial "confession" per proto (`pc_lo=1,
pc_hi=len(code), reason="fallback-state-machine", pass="structure.fallback"`)
recording that fact. `decompile_file(path)` is `decompile_chunk(load_file(path))`.

"Confessions" are how a future structuring pass would say "I only handled pc
12–47, the rest fell through to fallback" — the field exists now specifically
so M3 can start filling it in without changing the `DecompileResult` shape.

## Common operations

All commands assume you're at the repo root with `uv sync` already run, and
(where a command touches real corpus files) `PYLUADEC_CORPUS_DIR` pointed at
your local checkout of the 229-file corpus. None of these commands or their
output below embed an absolute path — copy them as-is; only the environment
variable is host-specific.

### Run the test suite

```bash
PYLUADEC_CORPUS_DIR=/path/to/script_to_decompile uv run pytest
```

This — **with the environment variable** — is the documented default way to
run the suite, not bare `uv run pytest`. Without `PYLUADEC_CORPUS_DIR`
pointing at a real corpus checkout, 13 corpus-gated tests silently
`pytest.skip` instead of running (`tests/conftest.py`'s `corpus_dir`
fixture) — and that list includes the M2 exit gate
(`tests/test_corpus_compile.py`), both migration gates
(`tests/test_golden.py`, `tests/test_parity.py`), and the ledger
fixed-point test (`tests/test_ledger_ratchet.py`). A bare `uv run pytest`
still prints a green "107 passed" in that case — it is not an error, by
design (see `tests/conftest.py`'s `corpus_dir` fixture docstring — corpus
availability is an environment fact, not a code defect) — but a green
result obtained that way says nothing about any of the gates above. A
`pytest_terminal_summary` hook in `tests/conftest.py` prints a loud warning
banner at the end of the run whenever `PYLUADEC_CORPUS_DIR` is unset or
missing, specifically so this isn't easy to miss by skimming a scrollback;
it does not change the exit code.

### Decompile a single file

```bash
uv run python -c "
from pyluadec.pipeline import decompile_file
res = decompile_file('$PYLUADEC_CORPUS_DIR/snr_crd_1.lua')
print(res.source.decode())
"
```

`res` is a `DecompileResult`: `res.source` is the full emitted Lua chunk
(bytes, ready to hand to `luac`), `res.confessions_by_proto` is the
`{proto_path: [confession, ...]}` map described above.

### Run the full-corpus compile gate

```bash
PYLUADEC_CORPUS_DIR=/path/to/script_to_decompile uv run python scripts/run_corpus.py
```

This decompiles all 229 files, writes each emitted source to
`build/decompiled/<name>.lua` (gitignored — scratch output, not a
deliverable), tries to `luac`-compile every one, and rewrites
`corpus/ledger.jsonl` (**not** gitignored — see "Ledger field semantics").
On a clean run it prints:

```
compiled 229/229; ledger: 1478 unique protos (1944 occurrences)
```

and exits 0. A file that fails to compile prints `COMPILE FAIL <name>: ...`
to stderr with the first 200 chars of `luac`'s error, and the script exits 1
(`n_ok != len(files)`). `tests/test_corpus_compile.py` is the same check as
a pytest test — run that in CI; run the script by hand when you need the
ledger regenerated or the compiled output on disk to poke at.

### View the ledger dashboard

```bash
uv run python scripts/ledger_dashboard.py
```

```
unique protos                       1478
occurrences                         1944
files                               229
compile_ok                          1478/1478
fallback                            1478/1478
level L1                            1478
confession: fallback-state-machine  1478
oracle                              321c2da9093790947e8797b8bddb06d2309846f7
ladder                              l3-ladder-v0
```

Add `--markdown` for a pipe-table rendering (same rows, suitable for pasting
into a PR description or status doc):

```bash
uv run python scripts/ledger_dashboard.py --markdown
```

The dashboard is read-only — it never writes `corpus/ledger.jsonl`. Only
`scripts/run_corpus.py` does that.

### Debug a single case with the differential-execution harness

`tests/diffexec.py::assert_fallback_roundtrip(lua_source: str, args=()) ->
bytes` is the building block nearly every fallback unit test uses
(`tests/test_fallback_*.py`). It compiles `lua_source` with the real `luac`,
decompiles the resulting bytecode through `structure.fallback.emit_chunk`,
runs *both* the original bytecode and the decompiled source through the real
`lua` interpreter, and asserts identical exit code and stdout. On mismatch
the `AssertionError` message includes both stdouts, both stderrs, and the
full decompiled source — that's usually enough to spot the bug without
reaching for a debugger.

You can drive it interactively from the repo root (this relies on the repo
root being on `sys.path`, which the root `conftest.py` exists specifically
to guarantee — see its docstring):

```bash
uv run python -c "
import tests.diffexec as d
dec = d.assert_fallback_roundtrip('''
local function outer()
  local function inner() return 1 end
  return inner()
end
print(outer())
''')
print(dec.decode())
"
```

If the assertion fails, read the "Reading fallback output" section below
before trying to fix it — the state-machine shape is unfamiliar the first
few times you look at it, and 90% of confusion is "which basic block is
this" rather than an actual bug.

## Reading fallback output

This is the section worth bookmarking. Fallback output is not meant to be
read casually — it's meant to be *decodable* by someone holding the original
bytecode listing. This section is that decoding key, plus a worked example.

### The prelude

Every emitted chunk starts with a fixed prelude (`structure.fallback.PRELUDE`):

```lua
local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_F = {}
```

- `__pld_select`/`__pld_unpack`/`__pld_tonumber`/`__pld_error` are aliases of
  the corresponding Lua globals, captured once so a decompiled script that
  happens to reassign `unpack` or `error` as a *global* (globals are just
  table accesses at the bytecode level, so this is legal Lua and the
  original bytecode may do it) can't shadow the helpers the emitter itself
  depends on.
- `__pld_pack(...)` builds an `{n=<count>, ...}` table — the standard
  Lua 5.1 idiom for capturing a variable-length result/argument list
  including trailing nils (`select('#', ...)` is the only correct way to get
  the true count; `#{...}` is not, because of nils).
- `__pld_get`/`__pld_set` are the accessors for *possibly-boxed* registers —
  see "the box model" below. Everything that isn't reasoning about capture
  goes through the direct `__pld_R[i]` / `__pld_R[i].v` forms inline instead
  of calling these (see `_FnEmitter.rd`/`wr` in `fallback.py`); `__pld_get`/
  `__pld_set` exist only for the two cases where a register index is *not*
  known statically at emit time (`VARARG` with `B==0`, `SETLIST` with
  `B==0`, open `CALL`/`RETURN` unpacking) and must be resolved against the
  boxed-set table `B` at runtime instead.
- `__pld_F` is the function factory table — see "`__pld_F` factories" below.

The `__pld_` prefix exists for exactly one reason: so the emitter can detect
(and refuse to emit, raising `EmitError`) a global name from the original
program that collides with it (`_FnEmitter.global_name`). It is not a style
choice — it is a correctness guard against exactly the kind of identifier
collision that would silently corrupt the state machine's own bookkeeping.

### `__pld_R` — the register file

Each Lua function's emitted body opens with:

```lua
local __pld_R, __pld_B, __pld_top = {}, {...}, 0
```

`__pld_R` is a Lua table standing in for the original bytecode's register
file (`R(0)..R(maxstacksize-1)`). Register `i` is read as `__pld_R[i]`
almost everywhere in the emitted code — `_FnEmitter.rd(i)` is the one place
that decides the exact spelling, and it branches on whether register `i` is
*boxed* (see next paragraph). `__pld_B` is a fixed table computed at
function-body-construction time (not touched at runtime after that): `{[i] =
true, ...}` for every register `i` that is boxed.

### The box model — why some registers are `{v = ...}`

A Lua closure created inside another function can capture (as an upvalue) a
register of its *enclosing* function that is still live after the enclosing
function keeps running or loops — the classic "closures share a mutable
upvalue" case. A plain Lua local can't be aliased like that, so the emitter
has to give any register that is ever captured this way its own heap-allocated
box: a one-field table `{v = <value>}`, so that both the enclosing function's
register access and the created closure's upvalue access go through the
*same* box object and observe each other's writes.

`_FnEmitter.boxed` (`= self.fn.captured_regs`, computed in `lift.py` from
`CLOSURE`'s trailing `MOVE` pseudo-instructions — see the lift section above)
is exactly that set of register indices. For a boxed register `i`:

- `rd(i)` emits `__pld_R[i].v` (unwrap).
- `wr(i, expr)` emits `__pld_R[i].v = expr`.
- it is initialized as `__pld_R[i] = {v = <initial value>}` (parameters:
  `{v = __pld_pN}`; non-parameter boxed registers not yet assigned: `{}`,
  i.e. box exists with `v == nil`).

For an *unboxed* register, `rd`/`wr` use the register slot directly
(`__pld_R[i]` / `__pld_R[i] = expr`) — no indirection, no box.

`CLOSE` (Lua 5.1's "this scope just ended, upvalues pointing above here must
stop sharing storage") is emitted as re-boxing every boxed register at or
above the `CLOSE` argument: `__pld_R[i] = {v = __pld_R[i].v}` — a fresh box
with a copy of the old value, so any closure that already captured the *old*
box keeps seeing the old value (correctly frozen), while the enclosing
function continues from a new, independent box. This is the exact runtime
behavior `CLOSE` has in the reference VM (`lvm.c`'s `luaF_close`), reproduced
at the source level instead of the C-struct level.

### `__pld_U` — the upvalue table

Every emitted function is actually two nested Lua functions:

```lua
__pld_F["<path>"] = function(__pld_U)
return function(<params>)
  ...
end
end
```

The outer function receives `__pld_U`, a plain array of box objects (`{v =
...}`, or a box shared with the parent's `__pld_R` slot — see `CLOSURE`
below) — one per upvalue, indexed the same way the original bytecode's
`GETUPVAL`/`SETUPVAL` index them (0-based, matching `RawInstr.b`). Reading
upvalue `b` is `__pld_U[b].v`; writing is `__pld_U[b].v = expr`. The *inner*
function (what `__pld_F[path]` actually returns and what gets called/closed
over) is the one holding `__pld_R`, the params, and the pc loop.

### `__pld_pc` — the dispatch state machine

```lua
local __pld_pc = 1
while true do
if __pld_pc == 1 then
  ...
elseif __pld_pc == 6 then
  ...
else __pld_error("pyluadec fallback: invalid pc") end
end
```

One `if`/`elseif` arm per CFG basic block (`build_cfg`'s `blocks` dict, keyed
by each block's *starting* original bytecode pc — 1-based, matching how
`lift_proto` numbers pcs). Each arm emits that block's instructions in order
(`_FnEmitter._emit_simple`) and ends with either a terminator
(`_emit_terminator` — branches, jumps, loop opcodes, `CALL`/`TAILCALL`,
`RETURN`) that sets `__pld_pc` to the appropriate successor block's start
pc, or, for a block that falls off the end into the next block, an explicit
`__pld_pc = <next block start>` appended by `_emit_block`. The `else` arm is
unreachable in correct output — it exists purely as a canary: if you ever
see `pyluadec fallback: invalid pc` at runtime, either the CFG built from
this proto is wrong, or something wrote a bogus jump target into
`__pld_pc`, and that is the bug to chase, not anything about the emitted
program logic.

Note the pc numbers in emitted `if __pld_pc == N` arms are *original
bytecode pcs, 1-based* — the same numbering a `luac -l -l` listing uses.
This is deliberate and is what makes cross-referencing possible (next
section).

### `__pld_top` — open call/vararg regions

Several opcodes have an "open" form where the number of values involved
isn't known until runtime — a call passing `f(...)` as its last argument
(`CALL` with `B==0`), a function returning "everything above register A"
(`RETURN`/`TAILCALL` with `B==0`), `VARARG` collecting "all the varargs"
(`B==0`), and `SETLIST` flushing "everything pushed since the last flush"
(`C==0`, more precisely: `B==0` meaning up to `top`). In all these cases,
the original VM tracks how many values are sitting in the "open" region of
the register stack above a known base in a single interpreter-wide `top`
variable; the emitter reproduces this with a single local, `__pld_top`, set
every time an open-result operation happens (see `_emit_call`'s `c == 0`
branch, `VARARG`'s `b < 1` branch) and consumed by whatever opcode reads the
open region next (open `RETURN`, `SETLIST` with `B==0`). If you see a bug
where "too many" or "too few" values reach a vararg call or table
constructor, `__pld_top` bookkeeping is the first place to look — grep for
every write to it in the function body and check each one is paired
correctly with the opcode that produced it.

### `__pld_F` — factories keyed by proto path

```lua
local __pld_F = {}
__pld_F["main_0"] = function(__pld_U) return function(...) ... end end
...
__pld_F["main"] = function(__pld_U) return function(...) ... end end
return __pld_F["main"]({})(...)
```

Every proto in the chunk (main chunk and every nested function, recursively)
gets an entry in `__pld_F`, keyed by the dotted path `pipeline.walk_proto_paths`
assigns it: the main chunk is `"main"`; its first subproto is `"main_0"`;
that subproto's fourth subproto is `"main_0_3"`; and so on — the suffix at
each level is that proto's index in its parent's `subprotos` list.
`structure.fallback.emit_chunk` walks the tree **children before parent**
(so a `CLOSURE` instruction can always find its target already registered
in `__pld_F` — Lua doesn't need forward declarations for this since `__pld_F`
is a table populated before any of it runs, but the emit walk order matches
CLOSURE's operand structure for readability regardless) and appends one
`__pld_F[path] = function(__pld_U) return function(...) ... end end` block
per proto. `CLOSURE a Bx` (create a closure of subproto `Bx` of the current
function, at register `a`) becomes a call `__pld_F["<path>_<Bx>"]({...})`
where `{...}` is the list of upvalue boxes to hand the child (each element
either `__pld_R[reg]` — a box shared with a captured local — or
`__pld_U[idx]` — passing an upvalue through unchanged; see the `CLOSURE`
case in `_emit_simple`). The whole chunk finishes with `return
__pld_F["main"]({})(...)` — calling the main chunk's factory with an empty
upvalue list (main chunks have none) and then immediately calling the
resulting function with the process's varargs.

### Worked example

Take this small Lua source (not from the corpus — corpus files have no
debug info to make a clean listing from; a hand-written example makes the
correspondence between listing and emitted code much easier to see):

```lua
local function add(a, b)
  if a > b then
    return a + b
  else
    return b - a
  end
end
print(add(3, 4))
```

Compile it and get the reference listing (`build/luac_sz4 -l -l` prints a
`luac`-style disassembly with per-instruction pc numbers, matching the
`__pld_pc` values you'll see in the emitted output):

```bash
$ ./build/luac_sz4 -l -l -o /dev/null example.lua
```
```
main <example.lua:0,0> (8 instructions, 32 bytes at ...)
0+ params, 5 slots, 0 upvalues, 1 local, 3 constants, 1 function
	1	[7]	CLOSURE  	0 0	; 0x...
	2	[8]	GETGLOBAL	1 -1	; print
	3	[8]	MOVE     	2 0
	4	[8]	LOADK    	3 -2	; 3
	5	[8]	LOADK    	4 -3	; 4
	6	[8]	CALL     	2 3 0
	7	[8]	CALL     	1 0 1
	8	[8]	RETURN   	0 1
...
function <example.lua:1,7> (8 instructions, 32 bytes at ...)
2 params, 3 slots, 0 upvalues, 2 locals, 0 constants, 0 functions
	1	[2]	LT       	0 1 0
	2	[2]	JMP      	3	; to 6
	3	[3]	ADD      	2 0 1
	4	[3]	RETURN   	2 2
	5	[3]	JMP      	2	; to 8
	6	[5]	SUB      	2 1 0
	7	[5]	RETURN   	2 2
	8	[7]	RETURN   	0 1
```

`emit_chunk` on this bytecode produces (elided prelude, this is the real
output):

```lua
__pld_F["main_0"] = function(__pld_U)
return function(__pld_p0, __pld_p1)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
local __pld_pc = 1
while true do
if __pld_pc == 1 then
if not (__pld_R[1] < __pld_R[0]) then __pld_pc = 2 else __pld_pc = 3 end
elseif __pld_pc == 2 then
__pld_pc = 6
elseif __pld_pc == 3 then
__pld_R[2] = __pld_R[0] + __pld_R[1]
return __pld_R[2]
elseif __pld_pc == 5 then
__pld_pc = 8
elseif __pld_pc == 6 then
__pld_R[2] = __pld_R[1] - __pld_R[0]
return __pld_R[2]
elseif __pld_pc == 8 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main"] = function(__pld_U)
return function(...)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = __pld_F["main_0"]({})
__pld_R[1] = print
__pld_R[2] = __pld_R[0]
__pld_R[3] = 3
__pld_R[4] = 4
do 
local __pld_rs = __pld_pack(__pld_R[2](__pld_R[3], __pld_R[4]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 2 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 2 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 2 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 2 + __pld_i - 1) end __pld_R[1](__pld_unpack(__pld_t, 1, __pld_n)) end
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
return __pld_F["main"]({})(...)
```

Walking it against the listing:

- `main_0` (the `add` function, proto path `"main_0"` — subproto 0 of
  `main`) has 3 basic blocks: pc 1 (the `LT`/`JMP`), pc 3 (the `ADD`/
  `RETURN` — note the listing's pc 4 `RETURN` doesn't get its own `__pld_pc`
  arm because it's the *last* instruction of the block starting at pc 3, not
  a jump target itself), and pc 6 (the `SUB`/`RETURN`). `build_cfg` also
  allocates block starts at pc 2 and pc 5 and pc 8 because those are
  fallthrough/jump targets from the branch — `elseif __pld_pc == 2 then
  __pld_pc = 6` is exactly `JMP 3 ; to 6` at listing pc 2. `elseif __pld_pc
  == 5 then __pld_pc = 8` is the second `JMP` (listing pc 5, `JMP 2 ; to 8`)
  landing on the *unreachable* final `RETURN 0 1` at listing pc 8 (unreachable
  because both branches of the `if` already `return`d in the source — the
  compiler still emits it, so the emitter still emits an arm for it, and it
  is simply dead code here — `return` with no values, matching `RETURN 0 1`
  i.e. "return zero values").
- `LT 0 1 0` (listing pc 1: `A=0, B=1, C=0`, meaning "compare `R(1) < R(0)`;
  if the boolean result `!= A` then skip the next instruction") becomes `if
  not (__pld_R[1] < __pld_R[0])`: `A==0` is exactly the "when false" sense,
  which the emitter renders as negating the comparison and taking the "skip"
  branch (`pc+2` = listing pc 3, `ADD`) when true, else falling to `pc+1`
  (pc 2, the `JMP`) — matching `_emit_terminator`'s `EQ/LT/LE` case exactly.
- `main` (the chunk itself, path `"main"`) has one block, pc 1–8 collapsed
  into a straight run because there's no branch — the `CLOSURE`, the two
  `GETGLOBAL`/`MOVE`/`LOADK`s, and the two `CALL`s all execute in sequence.
  `CALL 2 3 0` (listing pc 6: call `R(2)` with 2 args at `R(3),R(4)`,
  0 results requested = "open", i.e. all results) is why you see the
  `__pld_pack`/`__pld_set`/`__pld_top` dance — the outer `CALL 1 0 1` at
  listing pc 7 (call `R(1)` = `print` with "all args from `R(2)` up" = open,
  0 results wanted) is why the second `do ... end` unpacks via `__pld_get`
  against `__pld_top` instead of a fixed register range.
- `CLOSURE 0 0` becomes `__pld_R[0] = __pld_F["main_0"]({})` — the `{}`
  is the (empty) upvalue-box list, correct here because `add` captures no
  upvalues (`0 upvalues` in the listing for that function).

If two states in emitted output don't line up with the listing this way —
e.g. the state you'd expect at a given `__pld_pc` reads a different register
than the listing's operand for that pc, or the arm for a pc is simply
missing — that is where to start: dump the listing with `luac_sz4 -l -l`,
find the pc, read that opcode's row in `effects.py`/`fallback.py`'s
`_emit_simple`/`_emit_terminator`, and compare by hand. This is a slow
process by design in M2 — there's no debugger integration yet — but it is
mechanical, and the differential-exec harness (previous section) will tell
you *that* something's wrong long before you need to do it.

## Ledger field semantics and the ratchet discipline

`corpus/ledger.jsonl` is the certification record: one JSON line per unique
proto **shape** (not per occurrence — the same trivial function body appears
verbatim dozens of times across the 229 files and is recorded once). Fields
of a `LedgerEntry` (`pyluadec.verify.ledger.LedgerEntry`):

- `shash` — `structural_hash(proto)`: a SHA-256 over a canonical JSON view
  of `numparams`, `is_vararg`, `nups`, `maxstacksize`, `code`, `constants`,
  the *count* of upvalues, and recursively over `subprotos`. This is the
  primary key. It deliberately excludes debug fields (empty for this corpus
  anyway) and is stable across different source files that happen to
  compile to the same bytecode shape.
- `level` — `"L0"` through `"L3"`, the certification tier this entry has
  reached. M2 only ever produces `L1` ("fallback emission compiled clean
  against the oracle") or `L0` (compile failed — should never appear in a
  committed ledger; see the ratchet test below). `L2` (differential
  execution match) and `L3` (`normalize`-ladder proto-structure match) are
  wired as concepts (`l3_level` is a field on every entry, currently always
  `null`) but nothing in M2 populates them yet — that's later milestones
  (`L2` differential-exec certification is M5 per the plan's explicit
  non-goals; `L3.1+` normalization rungs are M3).
  **Plainly stated, `L1` means: this proto shape's fallback emission
  compiled, and — only for the synthetic cases the differential-exec suite
  happens to construct from source — matched stdout/exit code on those
  specific programs. It is NOT a claim that this proto shape's real corpus
  content was verified semantically equivalent to the original bytecode.**
  See "Known semantic gaps" below for the concrete, verified ways fallback
  output can diverge from the original program that `L1` says nothing about.
- `l3_level` — which rung of `verify.normalize.NORMALIZATIONS` this entry
  was compared at, when `level` includes an L3 result. Always `null` in M2
  (the ladder is empty).
- `compile_ok` — whether `oracle.compile_source` accepted the fallback
  emission for (every occurrence of) this proto shape without raising.
- `fallback` — whether this entry's translation came from the fallback pass
  specifically (as opposed to some future structural pass). Always `true` in
  M2.
- `n_insns` — `len(proto.code)`, for a quick sense of how big/small the
  shape is when scanning the file.
- `confessions` — the list from `DecompileResult.confessions_by_proto`,
  i.e. which passes claimed which pc ranges and why. In M2 always a single
  entry: the whole `[1, len(code)]` range, `reason="fallback-state-machine"`.
- `occurrences` — `[{"file": ..., "proto_path": ...}, ...]`, every
  `(corpus file, proto path)` pair whose proto hashed to `shash`. This is
  what lets the dashboard report "1478 unique protos, 1944 occurrences,
  229 files" — 1944 total protos across the corpus collapse to 1478 unique
  shapes.
- `oracle` — see below, its own subsection.
- `ladder` — `verify.normalize.LADDER_VERSION` at the time this entry was
  generated (`"l3-ladder-v0"` currently). Exists so that a future ladder
  version bump can be detected per-entry without re-diffing the whole file.

### The ratchet

Three rules, enforced by `tests/test_ledger_ratchet.py`:

1. **Levels only go up.** A committed ledger must never contain `L0`
   (`test_committed_ledger_exists_and_holds_the_line` asserts `level in
   ("L1", "L2", "L3")` for every entry, and `compile_ok` for all of them).
   There is not yet a full "did an entry regress from L2 to L1" check across
   commits — that needs git history diffing and is explicitly out of scope
   for M2 (see the plan's non-goals: "完整 Ratchet CI" is M3). What exists
   now is the floor: nothing you commit may contain a level below where M2
   left it.
2. **`corpus/ledger.jsonl` is produced only by `scripts/run_corpus.py`, and
   committed whole — never hand-edited.** There is no supported partial
   update. If you touch the fallback emitter, the effects table, or
   anything upstream of it, the correct workflow is: re-run
   `scripts/run_corpus.py` against the full corpus, look at the resulting
   diff, and commit the regenerated file if the diff makes sense. Hand
   editing a `.jsonl` line to "fix" a level or an occurrence list will drift
   the file out of the invariants the ratchet test checks (sorted-by-hash,
   deduplicated) and, more importantly, will stop being true — the ledger's
   entire value is that its claims are backed by an actual toolchain run.
3. **The ledger is a fixed point of its own generator.** Running
   `scripts/run_corpus.py` again against the same corpus and the same oracle
   build must reproduce `corpus/ledger.jsonl` byte-for-byte.
   `tests/test_ledger_ratchet.py::test_ledger_is_a_reproducible_fixed_point`
   enforces this directly — it runs `run_corpus.main()` against a scratch
   directory (via `monkeypatch`, so it never touches the real
   `corpus/ledger.jsonl` or `build/decompiled/`) and asserts the bytes match
   what's committed. This was verified by hand while writing this runbook
   too: running `scripts/run_corpus.py` against the real corpus leaves `git
   status` clean on `corpus/ledger.jsonl`. The reason this property matters
   as much as it does is the next subsection.

### Why `oracle` records the oracle build's provenance, not repo HEAD

`ledger.oracle_version()` returns `git log -1 --format=%H -- vendor native`
— the hash of the last commit that touched the *oracle's own build inputs*
(the vendored Lua sources and the native/pybind bridge, including the
serialization-width patch) — not `git rev-parse HEAD`.

This looks like an odd choice until you hit the failure mode it avoids: `git
rev-parse HEAD` changes the instant you commit the ledger itself (the commit
*containing* the ledger update becomes the new HEAD). If `oracle` had
recorded HEAD, then every doc-only, test-only, or ledger-only commit would
change what every single entry's `oracle` field "should" say the moment
you regenerate — even though the actual `luac`/`lua` binaries backing the
certification hadn't changed at all. That would make property 3 above
(fixed point) false in practice on every commit, burying any *real*
regression under thousands of lines of `oracle`-field-only diff noise, which
is precisely the failure the fixed-point test exists to prevent. This was
not a hypothetical — an earlier version of `oracle_version()` did use
`rev-parse HEAD`, and the fix (commit `beeccc1`, "oracle_version() tracks
the oracle build, not repo HEAD") was a dedicated round specifically because
this broke reproducibility. (A related but distinct reproducibility bug was
fixed earlier in commit `60a913f`: `oracle.compile_source` was embedding an
absolute tempdir path into the compiled chunk's `Proto.source`, making two
compiles of byte-identical source produce byte-different bytecode — see the
comment in `oracle.py` referenced above. Different mechanism, same family of
bug: something incidental to *when*/*where* you ran a command leaking into
output that's supposed to depend only on real inputs.) If you're ever
tempted to make `oracle_version()` track something that changes on
unrelated commits, don't — read commit `beeccc1`'s message first.

## Effect modes: STRICT / NO_METAMETHOD / TRUSTING

`pyluadec.lift.effects.EffectMode` has three values, and every opcode's row
in `effects._row()` carries a separate `Effect` classification
(`PURE`/`READ_HEAP`/`WRITE_HEAP`/`ARBITRARY`) for each:

- **`STRICT`** — the conservative default (`lift_proto`'s default argument,
  and the mode `structure.fallback` actually uses — it calls
  `lift_proto(proto)` with no mode argument). Assumes any table access
  (`GETTABLE`/`SETTABLE`/`GETGLOBAL`/`SETGLOBAL`/`SELF`/`SETLIST`) or
  arithmetic/comparison op (`ADD`..`POW`, `UNM`, `LEN`, `CONCAT`, `EQ`,
  `LT`, `LE`) can invoke an arbitrary metamethod — i.e. can have arbitrary
  side effects and can observe/mutate anything. This is the only mode that
  is *sound* to use without knowing anything about the target program's
  metatables, which is why it's the default for a corpus whose runtime
  behavior (custom `__index`/`__newindex`/`__add` etc. on engine-provided
  tables) is not something this project has characterized yet.
- **`NO_METAMETHOD`** — assumes the corpus never triggers a metamethod, so
  those same opcodes downgrade to `READ_HEAP`/`WRITE_HEAP`/`PURE` instead of
  `ARBITRARY`. This is a real assumption about the *target program*, not
  a property of Lua in general, and using it without justification would be
  unsound for any table this project hasn't confirmed has no relevant
  metatable.
- **`TRUSTING`** — a further relaxation on top of `NO_METAMETHOD`: table
  *reads* in particular are marked `PURE`, i.e. safe to freely reorder/
  duplicate/elide, which is only true if the target program never mutates
  the table being read between two reads a future optimization pass might
  reorder.

**Nothing in the M2 pipeline actually consumes the `effect` classification
yet.** `structure.fallback` doesn't branch on it at all — it emits the fully
general translation for every opcode regardless of mode (boxed registers,
full call-open-region tracking, the works), so `EffectMode` currently has no
observable effect on fallback output. The axiom layer exists now, calibrated
and tested (`tests/test_effects.py`), so that the passes which *will* need
it — inlining, dead-store elimination, any optimization that wants to prove
"this rewrite doesn't change observable behavior" — have a ready-made,
already-reasoned-about foundation instead of re-deriving per-opcode
semantics from scratch.

### Calibration: DONE in M4 task 11 — read that, not this

The three paragraphs above describe what the modes *mean*, and that is still
accurate. Everything this section used to say about calibration ("explicitly
deferred to M4", "treat any code selecting `NO_METAMETHOD`/`TRUSTING` as
suspect") is **superseded**. The calibration happened. The authority is
`docs/runbooks/structured-pipeline.md` → "The effect lattice: what the three
modes mean, and why `STRICT` stays", with the per-row argument in
`lift/effects.py`'s `_row` comment block and the pins in
`tests/test_effects_modes.py`. The outcome, restated here so an M5 pass
author who lands on this file first is not sent the wrong way:

- **`STRICT` stays the pipeline-wide default.** It is `lift_proto`'s default
  argument and the only mode any `src/` code selects — enforced by
  `tests/test_effects_modes.py::test_strict_is_the_default_and_the_only_mode_in_use`,
  which a change would have to delete and justify.
- **`NO_METAMETHOD` is a permitted per-pass opt-in, scoped to
  script-constructed tables.** The corpus census finds 0 metamethod-related
  constants in 71414 constants across all 1944 protos, which establishes it
  for tables the scripts build themselves — and *not* for engine values: 56 of
  the 164 distinct global names the corpus reads are never written by any of
  the 229 files, so they arrive from the PSP engine where the census is blind.
  A pass selecting it must establish the value class it applies to, per
  region. It is not a safe global default precisely because the unproven case
  dominates.
- **`TRUSTING` is recommended against for any pass.** Its entire delta over
  `NO_METAMETHOD` is three rows (`GETGLOBAL`/`GETTABLE`/`SELF` →`PURE`), and
  the corpus *falsifies* all three rather than merely failing to support them:
  892 `SETGLOBAL` sites, 29 protos that read and write the same global name,
  1667 `SETTABLE` + 92 `SETLIST` + 44809 `CALL` sites. It is kept in the enum
  (removing it would be an axiom-layer behaviour change) with all three
  distinguishing rows marked `# UNARGUED`.

Two rows were found under-graded during that calibration and deliberately
left alone pending the full axiom-change protocol (`lvm.c` citation plus a
differential run): `LEN` at `NO_METAMETHOD`, and `NEWTABLE`/`CLOSURE`'s GC
path. The `LEN` one is a real defect and is item 1 of the M5 agenda in
`docs/runbooks/m3-backlog.md`.

## Known semantic gaps

This is the single most important section for a future reader to find before
trusting what `L1` in the ledger implies about a piece of corpus content.
Fallback emission compiling clean against the oracle (`L1`) means exactly
that — it compiles — plus, for the synthetic cases the differential-exec
suite constructs from source (`tests/test_fallback_*.py`), that stdout and
exit code matched for *those specific programs*. It is **not** a claim that
any given corpus file's fallback output is semantically equivalent to the
original bytecode on real corpus content — the gaps below are known,
verified ways the two can diverge, and none of them would be caught by the
`L1` gate as it exists in M2.

- **Table internal layout is not reproduced.** `NEWTABLE A B C` calls
  `luaH_new(L, luaO_fb2int(B), luaO_fb2int(C))` in the reference VM
  (`lvm.c`'s `OP_NEWTABLE` case) — `B`/`C` are array/hash presize hints the
  compiler computed from the constructor's literal shape. The fallback
  emitter discards both: `NEWTABLE` becomes plain `{}` (`fallback.py`'s
  `_emit_simple`, the `Op.NEWTABLE` case), and `SETLIST` becomes individual
  `t[i] = v` assignments (`_emit_simple`'s `Op.SETLIST` case) rather than the
  batch array-part write `luaH_resizearray` performs during the original
  `OP_SETLIST`. Two verified consequences:
  - `local t = {1,nil,3} print(#t)` prints `3` from the original bytecode
    and `1` from fallback-decompiled source (`#` on a table with holes is
    only guaranteed to return *a* border, and which border depends on the
    array part's allocated size, which the two constructions disagree on).
  - `pairs` iteration order over constructor-built tables with a hash part
    diverges: an independent spot-check (40 randomly generated
    `{k1=v1, k2=v2, ...}`-style tables compiled, decompiled, and iterated
    with `pairs`, comparing the concatenated key order) found 3/40 pure-hash
    constructors and 16/40 mixed array+hash constructors where original and
    decompiled key order disagreed — because `hashnum`/table-resize bucket
    placement in `ltable.c` depends on the table's *capacity at insertion
    time*, and the fallback-decompiled table always starts at capacity 0
    and grows incrementally instead of being presized by `NEWTABLE`'s hint.
  - Corpus-reachable, not just a synthetic concern: across the 229-file
    corpus, 92 `NEWTABLE` instructions carry a non-zero array presize (`B`),
    62 carry a non-zero hash presize (`C`), and 154 carry at least one of the
    two; there are 92 `SETLIST` instructions and 7 `TFORLOOP`s (the opcode
    that drives `pairs`/`ipairs`-style iteration and would observe any order
    divergence).
  - Faithful layout needs real table-constructor reconstruction (recovering
    the constructor literal shape, not just replaying the opcode sequence
    into an empty table) — that is M3 structuring work, not a fallback
    patch; fallback's job was semantic exactness for *program behavior that
    doesn't depend on table internals*, and this is exactly the class of
    behavior that does.

- **Runtime error messages differ.** Error positions in the reference VM
  name the file/line of the *original* source that produced the error;
  fallback-decompiled source runs as a different file with different line
  numbers (the `__pld_pc`-dispatch state machine has no way to reproduce the
  original position from stripped bytecode — there is no `lineinfo` in this
  corpus to draw from in the first place, see `CLAUDE.md`). Verified: `local
  n = "x" for i = 1, n do end` raises `'for' limit must be a number` from
  both the original bytecode and the fallback-decompiled source (same
  message text, same nonzero exit code — this is what
  `tests/test_fallback_control.py::test_runtime_error_parity` checks), but
  the *position* differs — the original reports `errmsg.lua:2: ... in main
  chunk`, the decompiled version reports `errmsg_dec.lua:18: ... in function
  <errmsg_dec.lua:7>` via `__pld_error` (`FORPREP`'s error path,
  `fallback.py`'s `Op.FORPREP` case in `_emit_terminator`) with a completely
  different traceback shape (the state-machine's `while true do` loop is not
  present in the original control flow at all). Any script that `pcall`s an
  error and prints/parses the message text (not just checks `pcall`'s
  boolean) will observe this divergence.

- **Allocation and GC profile differ.** The emitted code allocates a fresh
  `__pld_R` register table per call, a `{v = ...}` box per captured register
  (see "The box model" above), and a `{n=..., ...}` pack table per open
  call/vararg/return, none of which exist in the reference VM's register-
  stack-based execution model. `collectgarbage("count")` readings, weak-
  table behavior keyed on any of these incidental tables, and `__gc`
  finalizer timing are consequently not preserved. Nothing in M2 attempts to
  verify or bound this; it is a structural consequence of the box-and-table
  translation strategy, not a bug to fix at the fallback layer.

- **What the differential harness does and does not compare.**
  `tests/diffexec.py::assert_fallback_roundtrip` — the workhorse behind
  nearly every fallback test — compares **stdout and exit code only**. It
  does not compare stderr text (see `test_runtime_error_parity` above, which
  deliberately only asserts both sides are nonzero, not that the messages
  match), does not compare table internal layout or `pairs`/`next` iteration
  order unless the test's own `print` output happens to expose it, and does
  not compare allocation counts, GC timing, or memory usage in any way. A
  green differential test is evidence about stdout/exit-code equivalence for
  the specific inputs exercised — nothing more.

## `corpus/discrepancies.json` is a gate artifact, not a record

`corpus/discrepancies.json` is listed in `.gitignore`
(`git check-ignore -v corpus/discrepancies.json` confirms it matches that
rule) and is never committed. It is produced by the golden-parity gate
(Phase 1; see `docs/runbooks/64bit-migration.md` and
`scripts/compare_bridge_golden.py`) as scratch output for a single gate run
— "here is what differed, if anything, this time" — not as a durable log of
verification history. This was a deliberate decision, not an oversight: a
gitignored gate artifact can't drift out of sync with the code that produced
it (there's nothing to go stale, because it's never read back except by the
gate run that just wrote it), whereas a committed one would raise the
question of whether it's still accurate after the next change and would
need its own upkeep discipline. If you need "when did we last confirm this
gate was clean" as a durable fact, that provenance belongs in CI history or
in `CHANGELOG.md` — not in a JSON file that exists purely as one gate run's
scratch output.

## Fallback output is intentionally ugly

Worth saying plainly, because it's easy to look at the worked example above
and read the `__pld_pc` dispatch loop as a bug or a first draft: it is not.
Fallback's job in M2 was semantic exactness for all 229 files, certified
against the real Lua toolchain, with nothing hand-waved — not readability.
Every function, however simple, gets the full state-machine treatment
because the fallback pass has no concept of "this region is simple, treat it
specially" — that concept (structured region recovery: turning a
comparison-and-two-blocks CFG shape back into `if a > b then ... else ...
end`, turning back-edges into `while`/`for`, synthesizing meaningful local
variable names in place of `__pld_R[n]`) is exactly what M3 is for, and
deliberately does not exist yet. Do not try to make fallback output prettier
in place — that's scope creep into M3's job, done without M3's design work
(structuring passes need a way to *coexist* with fallback so that a region a
smarter pass can't confidently claim still falls through, via the
`confessions` mechanism `pipeline.py` already has a stub for). If you're
looking at ugly fallback output and wondering whether that's expected: yes,
that's expected, and improving it is the next milestone's whole job.

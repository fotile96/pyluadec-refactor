-- L1.75 gate probe: load a chunk under a stubbing environment, run it, then
-- INVOKE every global function it defined, recording a deterministic trace of
-- the engine calls, stub writes, prints and errors that result. The original
-- corpus bytecode and our decompiled output can then be compared on real
-- behaviour, without the game engine.
--
-- WHY THIS EXISTS. The L1.5 probe (`probe_global_state.lua`) compares only the
-- delta a chunk makes to the global table. Measured over the corpus, that
-- payload has a median of 22 characters and for 222 of 229 files it is exactly
-- `OK|string:main=<function>`: it asserts that a global named `main` exists and
-- is a function, while every statement inside it -- the whole content of the
-- file -- is never executed. This probe calls it.
--
-- SCOPE (do not assume more than this):
--   * Only globals the chunk itself wrote are invoked, and only those whose
--     value is a function at the top level. Functions reachable only through a
--     table field are not called.
--   * Every function is called with NO arguments. A parameter therefore reads
--     as nil, not as a stub.
--   * Unknown globals resolve to a stub proxy that is indexable, callable and
--     arithmetic-tolerant, so execution runs far past the first missing engine
--     symbol. What it observes is therefore behaviour *under this stub
--     policy*, not behaviour under the real PSP engine.
--   * State accumulates across the invocations within one run (they share one
--     environment), deliberately: it is deterministic and it exercises code
--     that depends on what an earlier function set up.
--
-- THE BUDGET IS AN EVENT COUNT, NOT AN INSTRUCTION COUNT. This is the
-- load-bearing design constraint, measured at M3 task 9 feasibility: an
-- instruction budget alone drops original/decompiled agreement from 226/229 to
-- 95/229, purely because two representations of the same program execute a
-- different number of VM instructions and therefore get truncated at different
-- points. An *event* count truncates both sides at the same point in the
-- observable behaviour. `INSN_BACKSTOP` exists only to stop a loop that spins
-- without recording anything; reaching it is reported as its own status so it
-- can never be mistaken for a clean run.
--
-- OUTPUT. Line 1 is `PROBE1|<status>|<event count>` with status in
-- {OK, CAP, INSN}, or `LOADFAIL|<message>` if the chunk did not load. Then one
-- line per recorded event. Every field that can contain arbitrary bytes is
-- escaped so that one event is exactly one line (see `esc`).
--
-- No Lua string patterns anywhere in this file (plain `string.find(..., true)`
-- and byte indexing only), matching the repo-wide no-regex rule.

-- Everything the probe needs is bound to a local BEFORE the target chunk (or
-- the determinism overrides installed below) can touch it.
local G = _G
local pairs = pairs
local type = type
local rawget = rawget
local setfenv = setfenv
local tostring = tostring
local pcall = pcall
local error = error
local assert = assert
local loadfile = loadfile
local sethook = debug.sethook
local osexit = os.exit
local tsort = table.sort
local tconcat = table.concat
local sfind = string.find
local ssub = string.sub
local iowrite = io.write

-- ---------------------------------------------------------------- constants
-- FROZEN. Both sides of every comparison must use the same numbers, and the
-- numbers are part of what "the gate" means; they are not tuning knobs.
local MAX_EVENTS = 3000          -- the real budget
local HOOK_STEP = 1000000        -- debug hook granularity, VM instructions
local INSN_BACKSTOP = 400000000  -- backstop only; see the header

-- TEST-ONLY override, read once here (before the os.getenv determinism
-- override further down replaces the global -- this reads the REAL one).
-- `test_instruction_backstop_stops_a_loop_that_records_nothing` has to run
-- the VM for INSN_BACKSTOP real instructions to prove the backstop fires at
-- all; 400,000,000 of pure Lua is measurably slow (~0.5s, 27% of this task's
-- entire suite cost for one assertion, measured 2026-08-12) and the
-- production default has to stay exactly 400000000 unconditionally. A
-- synthetic test may set PYLUADEC_PROBE_INSN_BACKSTOP to shrink the run;
-- production runs (the corpus gate, the CLI) never set it, so nothing about
-- what ships is different. Guarded by
-- `test_production_insn_backstop_constant_is_unconditionally_400_million`,
-- which reads this file's text and fails if the literal above ever stops
-- being a bare, unconditional 400000000.
local backstop_override = os.getenv("PYLUADEC_PROBE_INSN_BACKSTOP")
if backstop_override then INSN_BACKSTOP = tonumber(backstop_override) end

local target = ...

-- Shared helpers live next to this script; find them from arg[0] rather than
-- through package.path, so the probe stays runnable as a bare
-- `lua scripts/probe_behaviour.lua <target>` from any cwd. assert() so a
-- missing helper file is a loud failure, not a nil-index further down.
local C
do
  local a = rawget(G, "arg")
  local argv0 = (a and a[0]) or ""
  local dir, i = "", 1
  while true do
    local s = sfind(argv0, "/", i, true)
    if not s then break end
    dir = ssub(argv0, 1, s)
    i = s + 1
  end
  local chunk = assert(loadfile(dir .. "probe_common.lua"),
                       "probe_common.lua not found next to " .. argv0)
  C = chunk()
end

-- --------------------------------------------------------------- serialising
-- `esc`, `to_s`, `keystr`, `cstr` and the first-sight identity ordinals live
-- in `probe_common.lua` (`M.serialiser`), shared with the L1.5, L2 and
-- enumeration probes; see that file for why a heap address may never enter a
-- trace and why corpus strings are passed through byte-for-byte.
local S = C.serialiser()
local esc, keystr = S.esc, S.keystr

-- ------------------------------------------------------------------ recording
-- The recorder (`append`, `record`, `flush_and_exit`) and the frozen
-- stub-return policy both live in `probe_common.lua`; see there for the reason
-- `record` raises and `append` does not, and for the measured stub-policy
-- comparison. `MAX_EVENTS` stays here because it is this gate's constant.
local R = C.recorder{
  max_events = MAX_EVENTS,
  osexit = osexit,
  render = function(r)
    local out = {"PROBE1|" .. (r.stopped or "OK") .. "|" .. r.nev}
    for i = 1, r.nev do out[i + 1] = r.ev[i] end
    return tconcat(out, "\n")
  end,
}
local append, record, flush_and_exit = R.append, R.record, R.flush_and_exit
local function errtext(e) return C.errtext(S, e) end

-- -------------------------------------------------------------- stub proxies
local P = C.proxies{S = S, record = record}
local get_proxy = P.get

-- ------------------------------------------------- determinism overrides on _G
-- os.exit/time/clock/date/getenv/tmpname, collectgarbage, math.random,
-- tostring, print and io.write; bodies and the reasoning in
-- `probe_common.lua::install_determinism`.
C.install_determinism(G, S, record)

-- ------------------------------------------------------------- environment
-- Shadow-table environment (`envfields`), from `probe_common.lua::stub_env`;
-- see there for why writes never land on `env` itself and what that costs.
local env, envfields = C.stub_env{G = G, S = S, record = record,
                                  get_proxy = get_proxy}

-- ------------------------------------------------------------------ run it
local f, loaderr = loadfile(target)
if not f then
  iowrite("LOADFAIL|" .. esc(C.strip_location(loaderr) or tostring(loaderr)) .. "\n")
  osexit(0)
end
setfenv(f, env)

local hook_calls = 0
sethook(function()
  -- See flush_and_exit's comment: a previous __PLD_INSN__ (or __PLD_CAP__)
  -- raise already happened and was swallowed by a pcall inside the target
  -- (the hook fires on a wall of VM instructions regardless of call-stack
  -- depth, so it re-enters even if the raise was caught deep inside a
  -- target-level pcall with no further stub calls to trip `record`).
  -- Re-raising would be swallowed again every HOOK_STEP instructions forever.
  if R.stopped then flush_and_exit() end
  hook_calls = hook_calls + 1
  if hook_calls * HOOK_STEP >= INSN_BACKSTOP then
    R.stopped = "INSN"
    error("__PLD_INSN__", 0)
  end
end, "", HOOK_STEP)

local ok, err = pcall(f)
if not ok then append("X|<chunk>|" .. errtext(err)) end

if not R.stopped then
  local names, n = {}, 0
  for k, v in pairs(envfields) do
    if type(v) == "function" then
      n = n + 1
      names[n] = k
    end
  end
  tsort(names, function(a, b) return keystr(a) < keystr(b) end)
  for i = 1, n do
    local k = names[i]
    append("I|" .. keystr(k))
    if R.stopped then break end
    local okf, errf = pcall(envfields[k])
    if okf then
      append("R|" .. keystr(k) .. "|ok")
    else
      append("R|" .. keystr(k) .. "|" .. errtext(errf))
    end
    if R.stopped then break end
  end
end

sethook()

-- Same output shape as flush_and_exit, reused rather than duplicated: the
-- only difference at a normal completion is that the process exits 0 by
-- falling off the end of the script anyway, which osexit(0) also does.
flush_and_exit()

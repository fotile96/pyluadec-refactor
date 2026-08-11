-- L1.75 gate probe: load a chunk under a stubbing environment, run it, then
-- INVOKE every global function it defined, recording a deterministic trace of
-- the engine calls, stub writes, prints and errors that result. The original
-- corpus bytecode and our decompiled output can then be compared on real
-- behaviour, without the game engine.
--
-- WHY THIS EXISTS. The L1.5 probe (`probe_global_state.lua`) compares only the
-- delta a chunk makes to the global table. Measured over the corpus, that
-- payload has a median of 15 characters and for 222 of 229 files it is exactly
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
local rawset = rawset
local rawget = rawget
local rawequal = rawequal
local select = select
local setmetatable = setmetatable
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
local sformat = string.format
local sfind = string.find
local ssub = string.sub
local sbyte = string.byte
local schar = string.char
local iowrite = io.write

-- ---------------------------------------------------------------- constants
-- FROZEN. Both sides of every comparison must use the same numbers, and the
-- numbers are part of what "the gate" means; they are not tuning knobs.
local MAX_EVENTS = 3000          -- the real budget
local HOOK_STEP = 1000000        -- debug hook granularity, VM instructions
local INSN_BACKSTOP = 400000000  -- backstop only; see the header

local target = ...

-- Shared helpers live next to this script; find them from arg[0] rather than
-- through package.path, so the probe stays runnable as a bare
-- `lua scripts/probe_behaviour.lua <target>` from any cwd. assert() so a
-- missing helper file is a loud failure, not a nil-index further down.
local strip_location
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
  strip_location = chunk().strip_location
end

-- --------------------------------------------------------------- serialising
-- Stable identities for tables and functions. `tostring(t)` leaks a heap
-- address, which differs between any two processes and would make the trace
-- non-deterministic; first-sight ordinals are a function of the observed
-- behaviour alone.
local ids, nid = {}, 0
local function idof(v)
  local n = ids[v]
  if not n then
    nid = nid + 1
    n = nid
    ids[v] = n
  end
  return n
end

-- One event is one line, so a byte that would break that (or the "|" field
-- separator) is escaped. Strings from this corpus are Japanese game text and
-- are frequently not UTF-8; they are passed through byte-for-byte otherwise,
-- never decoded or normalised.
local function esc(s)
  if not (sfind(s, "\\", 1, true) or sfind(s, "\n", 1, true)
          or sfind(s, "\r", 1, true) or sfind(s, "|", 1, true)) then
    return s
  end
  local out = {}
  for i = 1, #s do
    local b = sbyte(s, i)
    if b == 92 then out[i] = "\\\\"
    elseif b == 10 then out[i] = "\\n"
    elseif b == 13 then out[i] = "\\r"
    elseif b == 124 then out[i] = "\\p"
    else out[i] = schar(b) end
  end
  return tconcat(out)
end

local pname = {}   -- stub proxy -> its dotted name
local to_s

function to_s(v)
  local t = type(v)
  if t == "nil" then return "nil" end
  if t == "boolean" then return v and "true" or "false" end
  if t == "number" then return sformat("%.17g", v) end
  if t == "string" then return "\"" .. esc(v) .. "\"" end
  if t == "table" then
    local n = pname[v]
    if n then return "@" .. n end
    return "<table#" .. idof(v) .. ">"
  end
  if t == "function" then return "<function#" .. idof(v) .. ">" end
  return "<" .. t .. ">"
end

-- Table keys appear inside dotted names, where a quoted string would be noise.
local function keystr(k)
  if type(k) == "string" then return esc(k) end
  return to_s(k)
end

-- Concatenation result for the proxy's __concat: readable, address-free.
local function cstr(v)
  local t = type(v)
  if t == "string" then return v end
  if t == "number" then return sformat("%.17g", v) end
  return to_s(v)
end

-- ------------------------------------------------------------------ recording
local ev, nev = {}, 0
local stopped = nil   -- nil | "CAP" | "INSN"

-- `append` never raises: it is what the driver code below (outside any pcall
-- of target code) uses, so hitting the cap while bookkeeping cannot crash the
-- probe. `record` is what target-triggered metamethods use, and it DOES raise,
-- because a runaway loop that keeps calling stubs has to be stopped from the
-- inside.
local function append(s)
  nev = nev + 1
  ev[nev] = s
  if nev >= MAX_EVENTS and not stopped then stopped = "CAP" end
end

local function record(s)
  append(s)
  if stopped == "CAP" then error("__PLD_CAP__", 0) end
end

local function errtext(e)
  if type(e) == "string" then
    if sfind(e, "__PLD_CAP__", 1, true) then return "CAP" end
    if sfind(e, "__PLD_INSN__", 1, true) then return "INSN" end
    if sfind(e, "__PLD_OSEXIT__", 1, true) then return "OSEXIT" end
    return esc(strip_location(e) or e)
  end
  return to_s(e)
end

-- --------------------------------------------------------- stub-return policy
-- FROZEN: nil-with-name-heuristic -- this list, in this order, defaulting to
-- nil. Re-measured over the whole corpus 2026-08-12, original-vs-decompiled
-- agreement by policy:
--     nil-with-name-heuristic (this one)  227/229
--     always nil                          227/229
--     always zero                         226/229
--     predecessor's zero-defaulted guess  226/229
-- The M3 feasibility note claimed the policy was agreement-invariant; it is
-- not, by one file. The extra divergence under the two zero-defaulted policies
-- is snr_common.lua showing one more instance of the SAME pinned getobjname
-- class (`bad argument #1 to 'len'` vs `to '?'`), not a new defect -- so the
-- policy still decides mostly WHAT YOU OBSERVE rather than WHETHER THE TWO
-- SIDES AGREE, just not exactly. This one is both the best-agreeing and (by 9
-- events out of 398,196) the deepest-reaching, so it is picked once and
-- frozen: changing it invalidates nothing about the gate's soundness but does
-- invalidate every recorded trace.
--
-- The name tested is the full dotted path the stub was reached by
-- ("systemSave.memoryFlag"), and the tests are plain substring searches in
-- this fixed order. Returning nil by default (rather than 0) is deliberate:
-- nil is what a real missing engine call would give a caller that does not
-- check, so the trace shows the caller's real nil-handling.
local function stub_result(name)
  if sfind(name, "pressButton", 1, true) then return false end
  if sfind(name, "Is", 1, true) then return false end
  if sfind(name, "Count", 1, true) then return 0 end
  if sfind(name, "Index", 1, true) then return 0 end
  if sfind(name, "Num", 1, true) then return 0 end
  if sfind(name, "Time", 1, true) then return 0 end
  if sfind(name, "Name", 1, true) then return "stub" end
  if sfind(name, "Scene", 1, true) then return "stub" end
  return nil
end

-- -------------------------------------------------------------- stub proxies
local proxies = {}
local proxy_mt = {}

local function get_proxy(name)
  local p = proxies[name]
  if p == nil then
    p = setmetatable({}, proxy_mt)
    proxies[name] = p
    pname[p] = name
  end
  return p
end

local function zero() return 0 end

proxy_mt.__index = function(self, k)
  return get_proxy(pname[self] .. "." .. keystr(k))
end
proxy_mt.__newindex = function(self, k, v)
  record("S|" .. pname[self] .. "." .. keystr(k) .. "|" .. to_s(v))
  rawset(self, k, v)
end
proxy_mt.__call = function(self, ...)
  local n = select("#", ...)
  local parts = {}
  for i = 1, n do parts[i] = to_s((select(i, ...))) end
  local name = pname[self]
  record("C|" .. name .. "|" .. n .. "|" .. tconcat(parts, ","))
  return stub_result(name)
end
proxy_mt.__add = zero
proxy_mt.__sub = zero
proxy_mt.__mul = zero
proxy_mt.__div = zero
proxy_mt.__mod = zero
proxy_mt.__pow = zero
proxy_mt.__unm = zero
proxy_mt.__concat = function(a, b) return cstr(a) .. cstr(b) end
proxy_mt.__lt = function() return false end
proxy_mt.__le = function() return false end
-- Deliberately absent, each checked by neutering rather than assumed:
--   __len -- Lua 5.1's OP_LEN never consults a metamethod for a TABLE
--            (lvm.c: luaH_getn straight away), so it would be dead code.
--   __eq  -- only called after raw equality already failed, and returning
--            rawequal(a, b) there is exactly the default.
--   __tostring -- unreachable: the only route to it is the global `tostring`,
--            which is replaced below with a version that resolves a proxy by
--            name before any metamethod is considered.

-- ------------------------------------------------- determinism overrides on _G
-- Installed on the real library tables, because the environment below falls
-- through to _G for anything the chunk did not define. Every one of these is a
-- source of run-to-run or machine-to-machine variation, or (os.exit) a way for
-- the target to truncate the probe's own output while still exiting 0. The
-- corpus was measured not to call any of them, which is exactly why they are
-- covered by synthetic tests rather than by corpus green.
G.os.exit = function() error("__PLD_OSEXIT__", 0) end
G.os.time = function() return 0 end
G.os.clock = function() return 0 end
G.os.date = function() return "1970-01-01" end
G.os.getenv = function() return nil end
G.os.tmpname = function() return "/tmp/pld_probe_tmp" end
G.collectgarbage = function() return 0 end
-- `math.randomseed` is deliberately NOT overridden: it only calls C srand(),
-- and the replacement math.random below never consults the C RNG, so a no-op
-- override would be a guard nothing could falsify. Checked by neutering: with
-- os.time() pinned to 0, deleting a math.randomseed override changed no test.
do
  local seed = 0
  G.math.random = function(m, n)
    seed = (seed * 1103515245 + 12345) % 2147483648
    local r = seed / 2147483648
    if m == nil then return r end
    if n == nil then n = m m = 1 end
    return m + (r * (n - m + 1) - (r * (n - m + 1)) % 1)
  end
end
G.tostring = function(v)
  local t = type(v)
  if t == "table" then
    local n = pname[v]
    if n then return "@" .. n end
    return "table: #" .. idof(v)
  end
  if t == "function" or t == "userdata" or t == "thread" then
    return t .. ": #" .. idof(v)
  end
  return tostring(v)
end
G.print = function(...)
  local n = select("#", ...)
  local parts = {}
  for i = 1, n do parts[i] = cstr((select(i, ...))) end
  record("P|" .. esc(tconcat(parts, "\t")))
end
G.io.write = function(...)
  local n = select("#", ...)
  local parts = {}
  for i = 1, n do parts[i] = cstr((select(i, ...))) end
  record("W|" .. esc(tconcat(parts, "")))
end

-- ------------------------------------------------------------- environment
local env = {}
setmetatable(env, {
  __index = function(_, k)
    local base = G[k]
    if base ~= nil then return base end
    return get_proxy(keystr(k))
  end,
  __newindex = function(_, k, v)
    record("G|" .. keystr(k) .. "|" .. to_s(v))
    rawset(env, k, v)
  end,
})

-- ------------------------------------------------------------------ run it
local f, loaderr = loadfile(target)
if not f then
  iowrite("LOADFAIL|" .. esc(strip_location(loaderr) or tostring(loaderr)) .. "\n")
  osexit(0)
end
setfenv(f, env)

local hook_calls = 0
sethook(function()
  hook_calls = hook_calls + 1
  if hook_calls * HOOK_STEP >= INSN_BACKSTOP then
    stopped = "INSN"
    error("__PLD_INSN__", 0)
  end
end, "", HOOK_STEP)

local ok, err = pcall(f)
if not ok then append("X|<chunk>|" .. errtext(err)) end

if not stopped then
  local names, n = {}, 0
  for k, v in pairs(env) do
    if type(v) == "function" then
      n = n + 1
      names[n] = k
    end
  end
  tsort(names, function(a, b) return keystr(a) < keystr(b) end)
  for i = 1, n do
    local k = names[i]
    append("I|" .. keystr(k))
    if stopped then break end
    local okf, errf = pcall(rawget(env, k))
    if okf then
      append("R|" .. keystr(k) .. "|ok")
    else
      append("R|" .. keystr(k) .. "|" .. errtext(errf))
    end
    if stopped then break end
  end
end

sethook()

local out = {"PROBE1|" .. (stopped or "OK") .. "|" .. nev}
for i = 1, nev do out[i + 1] = ev[i] end
iowrite(tconcat(out, "\n"), "\n")

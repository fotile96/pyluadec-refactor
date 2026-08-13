-- L2 gate probe: load a chunk under a stubbing environment, drive it with a
-- SCRIPTED KEY SEQUENCE, and record a deterministic trace of the engine calls,
-- stub writes, prints, key polls and errors that result. The original corpus
-- bytecode and our decompiled output can then be compared on real behaviour
-- along an input-driven path, without the game engine.
--
-- WHY THIS EXISTS, MEASURED. The L1.75 probe (`probe_behaviour.lua`) answers
-- every `pressButton` with `false` (its frozen stub policy: any name containing
-- "Is" or "pressButton" is false). The corpus' menu loops therefore never exit.
-- Measured 2026-08-12 over all 229 files, on the original side: exactly five
-- files reach a `pressButton` poll at all, and each of them burns most of its
-- 3000-event budget on that one loop --
--     snr_common 2557, snr_graphic 2606, snr_lib 2243, snr_memory 2608,
--     snr_music 2502 pressButton call events out of 3001.
-- A scripted sequence walks the loop instead: `snr_lib.lua` goes from
-- `CAP|3001` (2243 of them polls) to `OK|38` under its DOWN/DOWN/CIRCLE
-- sequence and `OK|68` under its UP/four-DOWN/CIRCLE one -- i.e. it runs to
-- completion. (Two earlier versions of this comment said `OK|40` and then
-- `OK|28`/`OK|236`. 40 was never produced by any shipped sequence; 28/236 was
-- real but measured on the pre-M5-task-10 timings, under which those two
-- sequences landed only their FIRST directive -- see `KEY_SEQUENCES` in
-- `scripts/probe_keyseq.py`.)
--
-- WHAT IS INHERITED FROM `probe_behaviour.lua`, UNCHANGED AND ON PURPOSE:
-- the event-count budget with an instruction backstop (an instruction budget
-- alone drops agreement 226/229 -> 95/229, the M3 feasibility finding), the
-- shadow-table shape for `env` and stub proxies (Lua 5.1 fires `__newindex`
-- only while `rawget` is nil), the stub-return policy, the determinism
-- overrides, and the "a probe-side failure never becomes a comparable value"
-- rule. `tests/test_l2_keyseq.py::test_frozen_constants_agree_with_the_l1_75_
-- probe` pins the shared numbers and the stub policy against
-- `probe_behaviour.lua`'s text, so the two files cannot drift apart silently.
--
-- WHY IT IS A SEPARATE FILE RATHER THAN A FLAG ON THAT ONE: the L1.75 gate's
-- traces are frozen artefacts -- two pinned divergences are asserted as exact
-- byte pairs and the reach numbers are asserted as counts -- and this probe
-- changes the trace format (a fourth header field, `K|` poll events, a taint
-- section). Threading both formats through one file would put the L1.75 gate's
-- evidence at risk of every edit made for L2. The duplication is real and is
-- the price; the pinning test above is what keeps it honest.
--
-- OUTPUT. Line 1 is `KEYSEQ1|<status>|<event count>|<taint count>` with status
-- in {OK, CAP, INSN}, or one of the three refusals below. Then one line per
-- recorded event, then the taint section (sorted, deduplicated `T|` lines),
-- then -- only when `cov=1` was asked for -- one `COV|` line.
--
--   LOADFAIL|<msg>    the chunk did not load. A real observation: the driver
--                     compares it like any other trace.
--   SPECFAIL|<msg>    the key spec did not parse. NOT a comparable value; the
--                     Python side raises on it.
--   ENTRYFAIL|<msg>   `entry=` named something that is not a callable. Also
--                     not comparable -- a typo'd entry name would otherwise
--                     produce the same string on both sides and grant L2 for
--                     a run that never happened.
--
-- No Lua string patterns anywhere in this file (plain `string.find(..., true)`
-- and byte indexing only), matching the repo-wide no-regex rule.

-- Everything the probe needs is bound to a local BEFORE the target chunk (or
-- the determinism overrides installed below) can touch it.
local G = _G
local pairs = pairs
local type = type
local rawget = rawget
local rawequal = rawequal
local getmetatable = getmetatable
local select = select
local setmetatable = setmetatable
local setfenv = setfenv
local tostring = tostring
local tonumber = tonumber
local pcall = pcall
local error = error
local assert = assert
local loadfile = loadfile
local sethook = debug.sethook
local getinfo = debug.getinfo
local osexit = os.exit
local tsort = table.sort
local tconcat = table.concat
local sformat = string.format
local sfind = string.find
local ssub = string.sub
local sbyte = string.byte
local schar = string.char
local iowrite = io.write
local mfloor = math.floor

-- ---------------------------------------------------------------- constants
-- FROZEN, and identical to `probe_behaviour.lua`'s. Both sides of every
-- comparison must use the same numbers, and the numbers are part of what "the
-- gate" means; they are not tuning knobs.
local MAX_EVENTS = 3000          -- the real budget
local HOOK_STEP = 1000000        -- debug hook granularity, VM instructions
local INSN_BACKSTOP = 400000000  -- backstop only; see probe_behaviour.lua

-- The COVERAGE run's backstop, in LINE events rather than VM instructions.
-- `INSN_BACKSTOP` is structurally unreachable there and this replaces it; see
-- the `want_cov` hook below for the measurement and the lvm.c/ldo.c reason.
-- 20,000,000 line events is ~26x the heaviest measured coverage run
-- (snr_graphic, 749,049) and costs ~1s of hook if it is ever reached.
local LINE_BACKSTOP = 20000000

-- TEST-ONLY override, read once here (before the os.getenv determinism
-- override further down replaces the global -- this reads the REAL one). Same
-- contract as `probe_behaviour.lua`'s: production runs never set it, and
-- `tests/test_l2_keyseq.py::test_production_insn_backstop_constant_is_
-- unconditionally_400_million` fails if the literal above stops being a bare,
-- unconditional 400000000.
local backstop_override = os.getenv("PYLUADEC_PROBE_INSN_BACKSTOP")
if backstop_override then INSN_BACKSTOP = tonumber(backstop_override) end
local line_override = os.getenv("PYLUADEC_PROBE_LINE_BACKSTOP")
if line_override then LINE_BACKSTOP = tonumber(line_override) end

local target, spec = ...

-- Shared helpers live next to this script; found from arg[0] rather than
-- through package.path, so the probe stays runnable as a bare
-- `lua scripts/probe_keyseq.lua <target> <spec>` from any cwd.
local strip_location
local selfdir = ""
do
  local a = rawget(G, "arg")
  local argv0 = (a and a[0]) or ""
  local i = 1
  while true do
    local s = sfind(argv0, "/", i, true)
    if not s then break end
    selfdir = ssub(argv0, 1, s)
    i = s + 1
  end
  local chunk = assert(loadfile(selfdir .. "probe_common.lua"),
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
-- separator) is escaped. Strings from this corpus are Japanese game text; they
-- are passed through byte-for-byte, never decoded or normalised. (An earlier
-- version of this comment said they are "frequently not UTF-8". CLAUDE.md
-- records that as measured-FALSE: 49063 string constants, 17411 non-ASCII,
-- **0** non-UTF-8. The reason nothing here decodes is the red line itself, not
-- an encoding fact.)
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

local function die(kind, msg)
  iowrite(kind .. "|" .. esc(msg) .. "\n")
  osexit(0)
end

-- ------------------------------------------------------------ the key script
-- Spec grammar (ASCII, no spaces), directives joined by ";":
--
--   k=<frame>,<KEY>[+<KEY>]*   the keys held down on that frame (1-based)
--   tail=<KEY>[+<KEY>]*        the keys held on EVERY frame past the last
--                              `k=`; `tail=` with nothing after it means none
--   entry=<dotted.name>        call exactly this, instead of invoking every
--                              global function the chunk defined
--   cov=1                      collect executed source lines (see the hook)
--
-- Frame 1 is the first frame; `wait(n)` advances the frame by max(floor(n), 1),
-- which is the predecessor's harness rule (`DEBUG_KEY_SEQUENCE_HARNESS.md`:
-- `frame = frame + math.max(n, 1)`) and matches how the corpus' menu loops
-- pace themselves -- every one of them ends its iteration with `wait(1)`.
local keys_at = {}      -- frame -> {KEY -> true}
local tail_keys = nil   -- {KEY -> true} or nil when `tail=` was not given
local last_frame = 0
local entry = nil
local want_cov = false

local function split(s, sep)
  local out, n, i = {}, 0, 1
  while true do
    local j = sfind(s, sep, i, true)
    if not j then
      n = n + 1
      out[n] = ssub(s, i)
      return out, n
    end
    n = n + 1
    out[n] = ssub(s, i, j - 1)
    i = j + #sep
  end
end

local function keyset(s)
  local set = {}
  if s == "" then return set end
  local parts, n = split(s, "+")
  for i = 1, n do
    if parts[i] == "" then die("SPECFAIL", "empty key name in '" .. s .. "'") end
    set[parts[i]] = true
  end
  return set
end

do
  if spec == nil then spec = "" end
  local parts, n = split(spec, ";")
  for i = 1, n do
    local d = parts[i]
    if d ~= "" then
      local eq = sfind(d, "=", 1, true)
      if not eq then die("SPECFAIL", "directive without '=': " .. d) end
      local name = ssub(d, 1, eq - 1)
      local val = ssub(d, eq + 1)
      if name == "k" then
        local comma = sfind(val, ",", 1, true)
        if not comma then die("SPECFAIL", "k= needs <frame>,<KEY>: " .. d) end
        local fr = tonumber(ssub(val, 1, comma - 1))
        if not fr or fr < 1 or fr ~= mfloor(fr) then
          die("SPECFAIL", "k= frame must be a positive integer: " .. d)
        end
        keys_at[fr] = keyset(ssub(val, comma + 1))
        if fr > last_frame then last_frame = fr end
      elseif name == "tail" then
        tail_keys = keyset(val)
      elseif name == "entry" then
        if val == "" then die("SPECFAIL", "entry= needs a name") end
        entry = val
      elseif name == "cov" then
        if val ~= "1" then die("SPECFAIL", "cov= takes only 1: " .. d) end
        want_cov = true
      else
        die("SPECFAIL", "unknown directive: " .. name)
      end
    end
  end
end

-- ------------------------------------------------------------------ recording
local ev, nev = {}, 0
local stopped = nil   -- nil | "CAP" | "INSN"
-- Taint is a SET, not an event stream: it is a property of the run, and a
-- `type()` inside a hot loop would otherwise consume the whole event budget
-- and change what the gate compares. Deduplicated on "<kind>|<name>", emitted
-- sorted after the events so both sides' taint is compared too.
local taint, ntaint = {}, 0
local cov_ours, cov_seen = {}, {}
-- Proto-level coverage: keyed on (linedefined, lastlinedefined) so two
-- CLOSURES of the same proto count once. See the `want_cov` hook.
local cov_protos, n_cov_protos = {}, 0
local n_lines = 0
local tsource = nil

local function flush_and_exit()
  local out = {"KEYSEQ1|" .. (stopped or "OK") .. "|" .. nev .. "|" .. ntaint}
  local n = 1
  for i = 1, nev do n = n + 1 out[n] = ev[i] end
  local tk, ntk = {}, 0
  for k in pairs(taint) do ntk = ntk + 1 tk[ntk] = k end
  tsort(tk)
  for i = 1, ntk do n = n + 1 out[n] = "T|" .. tk[i] end
  if want_cov then
    local ls, nls = {}, 0
    for l in pairs(cov_ours) do nls = nls + 1 ls[nls] = l end
    tsort(ls)
    for i = 1, nls do ls[i] = "" .. ls[i] end
    n = n + 1
    out[n] = "COV|" .. tconcat(ls, ",")
    n = n + 1
    out[n] = "COVF|" .. n_cov_protos
  end
  iowrite(tconcat(out, "\n"), "\n")
  osexit(0)
end

local function append(s)
  nev = nev + 1
  ev[nev] = s
  if nev >= MAX_EVENTS and not stopped then stopped = "CAP" end
end

local function record(s)
  if stopped then flush_and_exit() end
  append(s)
  if stopped == "CAP" then error("__PLD_CAP__", 0) end
end

-- Never raises and never counts against the event budget: taint must not be
-- able to truncate a run, or a tainted run would be short in a way that could
-- look like agreement.
local function mark(kind, name)
  local k = kind .. "|" .. name
  if taint[k] == nil then
    taint[k] = true
    ntaint = ntaint + 1
  end
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
-- FROZEN, byte-identical to `probe_behaviour.lua`'s (pinned by
-- `test_frozen_constants_agree_with_the_l1_75_probe`). `pressButton` is still
-- listed even though the driver below intercepts the global before a proxy is
-- ever built for it: a target that reaches the name some other way (a field
-- called `pressButtonA`, say) must still get the L1.75 answer.
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

-- Writes land in a shadow table, never on the proxy itself: Lua 5.1 fires
-- __newindex only while rawget(t, k) is nil, so writing through would make
-- only the FIRST write to each field observable. Same shape, same known cost
-- (`pairs`/`next`/`rawget` report a stub proxy as empty) as
-- `probe_behaviour.lua`; documented there in full.
local pfields = setmetatable({}, {__mode = "k"})

proxy_mt.__index = function(self, k)
  local f = pfields[self]
  local v = f and f[k]
  if v ~= nil then return v end
  return get_proxy(pname[self] .. "." .. keystr(k))
end
proxy_mt.__newindex = function(self, k, v)
  record("S|" .. pname[self] .. "." .. keystr(k) .. "|" .. to_s(v))
  local f = pfields[self]
  if not f then f = {} pfields[self] = f end
  f[k] = v
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

-- The three comparison metamethods are the PROVABLE half of the taint
-- analysis. In Lua 5.1 `OP_LT`, `OP_LE` and `OP_EQ` do not produce a value:
-- each is followed by a `JMP` that the comparison's result selects (lvm.c's
-- `DOJUMP` arm; a `local b = x < y` compiles to LT, JMP, LOADBOOL, LOADBOOL).
-- So a comparison metamethod firing on a stub proxy IS a stub value deciding
-- a branch -- not an approximation of one.
--
-- `__lt`/`__le` keep `probe_behaviour.lua`'s `false`. `__eq` is NEW here and
-- semantically a no-op: lvm.c consults `__eq` only after `rawequal` has
-- already failed, and returning `false` there is exactly what happens with no
-- metamethod at all. It exists so the EQ case can be observed rather than
-- assumed absent.
proxy_mt.__lt = function(a, b)
  mark("cmp:lt", pname[a] or pname[b] or "?")
  return false
end
proxy_mt.__le = function(a, b)
  mark("cmp:le", pname[a] or pname[b] or "?")
  return false
end
proxy_mt.__eq = function(a, b)
  mark("cmp:eq", pname[a] or pname[b] or "?")
  return false
end

-- ------------------------------------------------- determinism overrides on _G
-- Identical to `probe_behaviour.lua`'s; see that file for why each one is a
-- source of run-to-run variation and why they are covered synthetically.
G.os.exit = function() error("__PLD_OSEXIT__", 0) end
G.os.time = function() return 0 end
G.os.clock = function() return 0 end
G.os.date = function() return "1970-01-01" end
G.os.getenv = function() return nil end
G.os.tmpname = function() return "/tmp/pld_probe_tmp" end
G.collectgarbage = function() return 0 end
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

-- ------------------------------------------------------------- the driver
-- Resolved by the environment BEFORE `_G`, so the target sees these rather
-- than a stub proxy (`pressButton`, `wait`) or the real library function
-- (`type`, `rawequal`, `getmetatable`).
local frame = 1

local function keys_now()
  local set = keys_at[frame]
  if set then return set end
  if frame > last_frame and tail_keys then return tail_keys end
  return nil
end

local function press(name)
  local set = keys_now()
  local down = false
  if set and type(name) == "string" then down = set[name] == true end
  record("K|" .. keystr(name) .. "|" .. frame .. "|" .. (down and "true" or "false"))
  return down
end

local function waitf(n)
  record("C|wait|1|" .. to_s(n))
  local m = tonumber(n)
  if m == nil or m ~= m then m = 1 end   -- nil or NaN
  m = mfloor(m)
  if m < 1 then m = 1 end
  frame = frame + m
  return nil
end

-- The conservative half of the taint analysis. Unlike the comparison
-- metamethods above, nothing here proves the result reached a branch -- Lua
-- gives no way to see that from inside the language, and `OP_TEST` on a table
-- consults no metamethod at all. So introspecting a stub is treated as if it
-- had decided a branch. Over-refusal, deliberately: see the "what this
-- provably cannot catch" list in `scripts/probe_keyseq.py`.
local function tainted_type(v)
  local n = pname[v]
  if n then mark("intro:type", n) end
  return type(v)
end

local function tainted_rawequal(a, b)
  local n = pname[a] or pname[b]
  if n then mark("intro:rawequal", n) end
  return rawequal(a, b)
end

local function tainted_getmetatable(v)
  local n = pname[v]
  if n then mark("intro:getmetatable", n) end
  return getmetatable(v)
end

local DRIVER = {
  pressButton = press,
  wait = waitf,
  type = tainted_type,
  rawequal = tainted_rawequal,
  getmetatable = tainted_getmetatable,
}

-- ------------------------------------------------------------- environment
-- Same shadow-table shape as `probe_behaviour.lua`'s `envfields`; see there.
local envfields = {}
local env = {}
setmetatable(env, {
  __index = function(_, k)
    local v = envfields[k]
    if v ~= nil then return v end
    local d = DRIVER[k]
    if d ~= nil then return d end
    local base = G[k]
    if base ~= nil then return base end
    return get_proxy(keystr(k))
  end,
  __newindex = function(_, k, v)
    record("G|" .. keystr(k) .. "|" .. to_s(v))
    envfields[k] = v
  end,
})

-- ------------------------------------------------------------------ run it
local f, loaderr = loadfile(target)
if not f then
  iowrite("LOADFAIL|" .. esc(strip_location(loaderr) or tostring(loaderr)) .. "\n")
  osexit(0)
end
setfenv(f, env)
tsource = getinfo(f, "S").source

local hook_calls = 0
local hook
if want_cov then
  -- Coverage collection, two measurements in one hook.
  --
  -- PROTO coverage ("call" events) is what the ledger badge is made of, and
  -- it is deliberately NOT line-based: `linedefined`/`lastlinedefined` are
  -- only a de-duplication key here (two CLOSUREs of one proto must count
  -- once), and the number reported is a COUNT of distinct protos entered.
  -- Nothing about it moves when the emitter changes where newlines go, which
  -- is the property `corpus/ledger.jsonl` needs -- see `coverage` in
  -- `scripts/probe_keyseq.py`.
  --
  -- LINE coverage ("line" events) drives the block-level DIAGNOSTIC only.
  -- `cov_seen[line]` is a first-sight classification: `true` when the line
  -- belongs to the target's chunk, `false` when it belongs to this probe (the
  -- recorder and the proxy metamethods run interleaved with the target).
  -- Classifying once per DISTINCT line rather than on every line event is what
  -- makes it affordable -- measured 2026-08-12 on 6,000,004 line events: 0.31s
  -- cached vs 2.39s with a `getinfo` every time. The caller prepends
  -- `LINE_SHIFT` blank lines so a probe line number can never collide with a
  -- target one.
  --
  -- `INSN_BACKSTOP` IS NOT REACHABLE HERE, and this is measured, not assumed.
  -- With `LUA_MASKLINE` set, `lvm.c::traceexec` fires the count hook only when
  -- `L->hookcount` is exactly 0 at its own entry -- but the line hook's own
  -- Lua body runs with `L->allowhook == 0` (ldo.c::luaD_callhook), where
  -- `traceexec` still calls `resethookcount` while `luaD_callhook` silently
  -- does nothing. With a hook body executing on most instructions the
  -- zero-crossing almost always lands inside it. Measured on this VM,
  -- 3,000,003 line events: mask "" -> 6 count events, mask "l" -> **0**, mask
  -- "lc" -> 0. So the backstop here is a LINE-event budget instead, which is
  -- a genuine bound (every line event is at least one VM instruction) and is
  -- pinned by `test_the_coverage_run_has_a_working_backstop`.
  hook = function(evt, ln)
    if evt == "call" then
      local info = getinfo(2, "S")
      if info ~= nil and info.source == tsource then
        local k = info.linedefined .. ":" .. info.lastlinedefined
        if cov_protos[k] == nil then
          cov_protos[k] = true
          n_cov_protos = n_cov_protos + 1
        end
      end
      return
    end
    if stopped then flush_and_exit() end
    n_lines = n_lines + 1
    if n_lines >= LINE_BACKSTOP then
      stopped = "INSN"
      error("__PLD_INSN__", 0)
    end
    local s = cov_seen[ln]
    if s == nil then
      local info = getinfo(2, "S")
      s = (info ~= nil and info.source == tsource)
      cov_seen[ln] = s
    end
    if s then cov_ours[ln] = true end
  end
  sethook(hook, "lc")
else
  hook = function()
    -- See probe_behaviour.lua's flush_and_exit comment: a previous raise was
    -- swallowed by a pcall inside the TARGET, and re-raising would be
    -- swallowed again every HOOK_STEP instructions forever.
    if stopped then flush_and_exit() end
    hook_calls = hook_calls + 1
    if hook_calls * HOOK_STEP >= INSN_BACKSTOP then
      stopped = "INSN"
      error("__PLD_INSN__", 0)
    end
  end
  sethook(hook, "", HOOK_STEP)
end

local ok, err = pcall(f)
if not ok then append("X|<chunk>|" .. errtext(err)) end

if not stopped then
  if entry then
    -- One named entry point, dotted: `SystemOption.OptionMain`. This is the
    -- predecessor's playbook shape (DEBUG_KEY_SEQUENCE_HARNESS.md drives one
    -- target function, not everything the file defines), and it is what keeps
    -- a checkpoint run from being derailed by an unrelated divergence
    -- elsewhere in the same file.
    local parts, n = split(entry, ".")
    local v = envfields[parts[1]]
    if v == nil then v = DRIVER[parts[1]] end
    if v == nil then v = G[parts[1]] end
    for i = 2, n do
      if type(v) ~= "table" then v = nil break end
      v = v[parts[i]]
    end
    if type(v) ~= "function" then
      -- DEFENSIVE: `die` writes and hard-exits through the real `os.exit`, so
      -- the hook cannot fire again in between. Tried: deleting this `sethook()`
      -- leaves every test green. It stays because a future edit that makes
      -- `die` return rather than exit would otherwise run the rest of this
      -- file under a live hook with `stopped` unset. (M3, round 2.)
      sethook()
      die("ENTRYFAIL", "entry '" .. entry .. "' is a " ..
          (v == nil and "nil" or type(v)) .. ", not a function")
    end
    append("I|" .. esc(entry))
    if not stopped then
      local okf, errf = pcall(v)
      if okf then
        append("R|" .. esc(entry) .. "|ok")
      else
        append("R|" .. esc(entry) .. "|" .. errtext(errf))
      end
    end
  else
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
      if stopped then break end
      local okf, errf = pcall(envfields[k])
      if okf then
        append("R|" .. keystr(k) .. "|ok")
      else
        append("R|" .. keystr(k) .. "|" .. errtext(errf))
      end
      if stopped then break end
    end
  end
end

sethook()
flush_and_exit()

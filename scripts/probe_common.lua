-- Helpers shared by the probe scripts (`probe_global_state.lua`, L1.5,
-- `probe_behaviour.lua`, L1.75, `probe_keyseq.lua`, L2, and `probe_enum.lua`,
-- M6 task 7). Loaded with `loadfile(<dir of arg[0]>)` by each probe rather
-- than `require`, so the probes stay runnable as bare
-- `lua scripts/probe_X.lua <target>` with no package.path setup.
--
-- No Lua string patterns anywhere in this file (plain `string.find(..., true)`
-- and byte indexing only), matching the repo-wide no-regex rule.
--
-- ## Why the driver factories below exist
--
-- `probe_keyseq.lua` was written by copying `probe_behaviour.lua`; measured
-- 2026-08-14 with `difflib.SequenceMatcher` over the two files, **257 lines
-- are identical** in blocks of 4 or more (the serialiser, the recorder, the
-- stub-return policy, the proxy metatable, the determinism overrides and the
-- environment shadow table). M5 recorded that as debt and M6 task 7's brief
-- forbids a fourth copy. The factories below are that debt being paid down:
-- `serialiser`, `recorder`, `stub_result`, `proxies`, `install_determinism`
-- and `stub_env`, each a closure factory so a probe can supply its own hooks
-- (taint marks, assignment injection) without the shared body being copied.
--
-- Every factory here is a MECHANICAL extraction: the bodies are the ones that
-- were in `probe_behaviour.lua`, unchanged. The evidence that the extraction
-- changed nothing is the L1.75 gate itself -- 229 files, both sides, byte
-- identical traces -- which is why `probe_behaviour.lua` was migrated onto
-- these factories in the same commit that added them.

local type = type
local sfind = string.find
local ssub = string.sub
local sbyte = string.byte
local schar = string.char
local sformat = string.format
local tconcat = table.concat
local setmetatable = setmetatable
local rawequal = rawequal
local select = select
local tostring = tostring
local iowrite = io.write
local error = error

local M = {}

-- Lua 5.1 formats both load and runtime errors as "<source>:<line>: <message>".
-- The source and line necessarily differ between a .luac input (stripped
-- bytecode: source "?", no line info) and a .lua input, so the prefix cannot be
-- compared -- but the residue is derived from string constants and opcode
-- semantics and is comparable. Strip the first "<anything>:<digits>: " prefix.
function M.strip_location(msg)
  if type(msg) ~= "string" then return nil end
  local i = 1
  while true do
    local c = sfind(msg, ":", i, true)
    if not c then return msg end
    local j = c + 1
    local digits = 0
    while true do
      local b = sbyte(msg, j)
      if b and b >= 48 and b <= 57 then
        digits = digits + 1
        j = j + 1
      else
        break
      end
    end
    if digits > 0 and ssub(msg, j, j + 1) == ": " then return ssub(msg, j + 2) end
    i = c + 1
  end
end

-- ------------------------------------------------------------- serialising
-- Stable identities for tables and functions. `tostring(t)` leaks a heap
-- address, which differs between any two processes and would make the trace
-- non-deterministic; first-sight ordinals are a function of the observed
-- behaviour alone.
--
-- One event is one line, so a byte that would break that (or the "|" field
-- separator) is escaped by `esc`. Strings from this corpus are Japanese game
-- text; they are passed through byte-for-byte, never decoded or normalised.
function M.serialiser()
  local ids, nid = {}, 0
  local S = {}
  -- stub proxy -> its dotted name. Populated by `M.proxies`; consulted by
  -- `to_s` and by the `tostring` override so a proxy never prints an address.
  S.pname = {}

  function S.idof(v)
    local n = ids[v]
    if not n then
      nid = nid + 1
      n = nid
      ids[v] = n
    end
    return n
  end

  function S.esc(s)
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

  function S.to_s(v)
    local t = type(v)
    if t == "nil" then return "nil" end
    if t == "boolean" then return v and "true" or "false" end
    if t == "number" then return sformat("%.17g", v) end
    if t == "string" then return "\"" .. S.esc(v) .. "\"" end
    if t == "table" then
      local n = S.pname[v]
      if n then return "@" .. n end
      return "<table#" .. S.idof(v) .. ">"
    end
    if t == "function" then return "<function#" .. S.idof(v) .. ">" end
    return "<" .. t .. ">"
  end

  -- Table keys appear inside dotted names, where a quoted string would be
  -- noise.
  function S.keystr(k)
    if type(k) == "string" then return S.esc(k) end
    return S.to_s(k)
  end

  -- Concatenation result for the proxy's __concat: readable, address-free.
  function S.cstr(v)
    local t = type(v)
    if t == "string" then return v end
    if t == "number" then return sformat("%.17g", v) end
    return S.to_s(v)
  end

  return S
end


-- ------------------------------------------------------------------ recording
-- `cfg.max_events`  -- the frozen event budget.
-- `cfg.osexit`      -- the REAL os.exit, captured by the caller before the
--                      determinism override replaces the global.
-- `cfg.render(R)`   -- returns the probe's whole stdout as a string (header
--                      line, events, whatever footers that probe defines).
--
-- `R.append` never raises: it is what driver code (outside any pcall of target
-- code) uses, so hitting the cap while bookkeeping cannot crash the probe.
-- `R.record` is what target-triggered metamethods use, and it DOES raise,
-- because a runaway loop that keeps calling stubs has to be stopped from the
-- inside.
--
-- `R.flush_and_exit` flushes the trace recorded so far and hard-exits. It is
-- only reached from `record`/a hook when `R.stopped` is ALREADY set -- i.e. a
-- previous raise (`__PLD_CAP__` / `__PLD_INSN__`) was swallowed by a pcall
-- inside the TARGET's own code rather than propagating out to the probe's own
-- pcall. `error()` only unwinds to the nearest pcall, which is not necessarily
-- ours, so re-raising would be swallowed again, forever. Measured before this
-- existed: `while true do pcall(function() tick() end) end` ran past the
-- 120s subprocess timeout with the event count growing unbounded, defeating
-- both the event cap and the instruction backstop from the inside.
function M.recorder(cfg)
  local R = {ev = {}, nev = 0, stopped = nil}
  local max_events, osexit, render = cfg.max_events, cfg.osexit, cfg.render

  function R.flush_and_exit()
    iowrite(render(R), "\n")
    osexit(0)
  end

  function R.append(s)
    R.nev = R.nev + 1
    R.ev[R.nev] = s
    if R.nev >= max_events and not R.stopped then R.stopped = "CAP" end
  end

  function R.record(s)
    if R.stopped then R.flush_and_exit() end
    R.append(s)
    if R.stopped == "CAP" then error("__PLD_CAP__", 0) end
  end

  return R
end


-- `(S, e)` -> the comparable residue of an error value. The internal control
-- raises are reported by their own names so a truncated run can never be
-- mistaken for a target-level error message.
function M.errtext(S, e)
  if type(e) == "string" then
    if sfind(e, "__PLD_CAP__", 1, true) then return "CAP" end
    if sfind(e, "__PLD_INSN__", 1, true) then return "INSN" end
    if sfind(e, "__PLD_OSEXIT__", 1, true) then return "OSEXIT" end
    return S.esc(M.strip_location(e) or e)
  end
  return S.to_s(e)
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
function M.stub_result(name)
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
-- `cfg.S`, `cfg.record`, and three optional hooks, each `nil` in the plain
-- (L1.75) configuration:
--   `cfg.stub_result(name, proxy)`  -- return value policy for a stub CALL.
--   `cfg.on_read(proxy, k, child, segs)` -- called after `__index` resolved to
--                                      a freshly minted CHILD proxy;
--                                      `true, v` replaces the result. Two
--                                      returns, not one, so that an injected
--                                      value of `nil` is expressible.
--   `cfg.on_call(proxy, name, ...)` -- called before the default return
--                                      policy; `true, v` overrides.
--   `cfg.taint(kind, name)`         -- L2's mark recorder.
--
-- Every write to a proxy field is recorded in `pfields` (proxy -> {key ->
-- value}), NEVER on the proxy table itself. Lua 5.1 fires __newindex only when
-- rawget(t, k) == nil, so if writes landed on the proxy via rawset (as they
-- did before this fix), only the FIRST write to a given field would ever be
-- observed -- measured: `sys.f = 1 sys.f = 2 sys.f = 3` recorded only
-- `S|sys.f|1`. Keeping the proxy's own raw table permanently empty means
-- rawget(self, k) is always nil, so __newindex (and __index, for reads that
-- have to see the last-written value) fires on every access.
--
-- KNOWN COST of the shadow-table shape, for both `pfields` here and the
-- environment's `envfields`: the raw tables stay permanently empty, so
-- `pairs`, `next` and `rawget` on a stub proxy or on `env` report them as
-- EMPTY no matter what has been written -- those three bypass metamethods in
-- Lua 5.1 and there is no __pairs in 5.1 to intercept. A target that iterates
-- a stub table it just populated would therefore see nothing and take a
-- different path than under the real engine. Verified unexercised by this
-- corpus (the 229 files' traces are byte-identical between the two sides, and
-- the only `pairs` loop in the corpus, `snr_novel.lua`'s, iterates a table the
-- SCRIPT built, not a proxy); recorded because the next probe user will not
-- rediscover it from the code.
--
-- `psegs` is the structural form of `pname`: the same access path as a list of
-- `{"k", key} / {"i", n} / {"d"}` segments. `probe_enum.lua` matches
-- assignments against it (a dotted STRING cannot distinguish the key `a.b`
-- from the path `a` then `b`, and a corpus key is not required to be an
-- identifier). Building it costs one table per proxy and is observable
-- nowhere else.
function M.proxies(cfg)
  local S, record = cfg.S, cfg.record
  local result = cfg.stub_result or M.stub_result
  local on_read, on_call, taint = cfg.on_read, cfg.on_call, cfg.taint
  local P = {}
  local proxies = {}
  local proxy_mt = {}
  local pfields = setmetatable({}, {__mode = "k"})
  local psegs = setmetatable({}, {__mode = "k"})
  P.mt = proxy_mt
  P.pfields = pfields
  P.psegs = psegs

  local function seg_of(k)
    if type(k) == "string" then return {"k", k} end
    if type(k) == "number" and k == (k - k % 1) then return {"i", k} end
    return {"d"}
  end

  function P.get(name, segs)
    local p = proxies[name]
    if p == nil then
      p = setmetatable({}, proxy_mt)
      proxies[name] = p
      S.pname[p] = name
      psegs[p] = segs or {}
    end
    return p
  end

  local function zero() return 0 end

  -- `track_segs` is off in the plain (L1.75/L2) configuration: building the
  -- child's segment list costs one table per proxy READ, and `probe_enum.lua`
  -- is the only consumer. Off, this body is exactly the one that was in
  -- `probe_behaviour.lua`.
  local track = cfg.track_segs
  proxy_mt.__index = function(self, k)
    local f = pfields[self]
    local v = f and f[k]
    if v ~= nil then return v end
    local nsegs = nil
    if track then
      local segs = psegs[self]
      nsegs = {}
      for i = 1, #segs do nsegs[i] = segs[i] end
      nsegs[#nsegs + 1] = seg_of(k)
    end
    local child = P.get(S.pname[self] .. "." .. S.keystr(k), nsegs)
    if on_read then
      local handled, r = on_read(self, k, child, nsegs)
      if handled then return r end
    end
    return child
  end
  proxy_mt.__newindex = function(self, k, v)
    record("S|" .. S.pname[self] .. "." .. S.keystr(k) .. "|" .. S.to_s(v))
    local f = pfields[self]
    if not f then f = {} pfields[self] = f end
    f[k] = v
  end
  proxy_mt.__call = function(self, ...)
    local n = select("#", ...)
    local parts = {}
    for i = 1, n do parts[i] = S.to_s((select(i, ...))) end
    local name = S.pname[self]
    record("C|" .. name .. "|" .. n .. "|" .. tconcat(parts, ","))
    if on_call then
      local handled, v = on_call(self, name, ...)
      if handled then return v end
    end
    return result(name, self)
  end
  proxy_mt.__add = zero
  proxy_mt.__sub = zero
  proxy_mt.__mul = zero
  proxy_mt.__div = zero
  proxy_mt.__mod = zero
  proxy_mt.__pow = zero
  proxy_mt.__unm = zero
  proxy_mt.__concat = function(a, b) return S.cstr(a) .. S.cstr(b) end
  if taint then
    -- The three comparison metamethods are the PROVABLE half of L2's taint
    -- analysis. In Lua 5.1 `OP_LT`, `OP_LE` and `OP_EQ` do not produce a
    -- value: each is followed by a `JMP` that the comparison's result selects
    -- (lvm.c's `DOJUMP` arm; a `local b = x < y` compiles to LT, JMP,
    -- LOADBOOL, LOADBOOL). So a comparison metamethod firing on a stub proxy
    -- IS a stub value deciding a branch -- not an approximation of one.
    --
    -- `__lt`/`__le` keep the plain configuration's `false`. `__eq` is extra
    -- here and semantically a no-op: lvm.c consults `__eq` only after
    -- `rawequal` has already failed, and returning `false` there is exactly
    -- what happens with no metamethod at all. It exists so the EQ case can be
    -- observed rather than assumed absent.
    proxy_mt.__lt = function(a, b)
      taint("cmp:lt", S.pname[a] or S.pname[b] or "?")
      return false
    end
    proxy_mt.__le = function(a, b)
      taint("cmp:le", S.pname[a] or S.pname[b] or "?")
      return false
    end
    proxy_mt.__eq = function(a, b)
      taint("cmp:eq", S.pname[a] or S.pname[b] or "?")
      return false
    end
  else
    proxy_mt.__lt = function() return false end
    proxy_mt.__le = function() return false end
  end
  -- Deliberately absent, each checked by neutering rather than assumed:
  --   __len -- Lua 5.1's OP_LEN never consults a metamethod for a TABLE
  --            (lvm.c: luaH_getn straight away), so it would be dead code.
  --   __eq  -- (plain configuration only) only called after raw equality
  --            already failed, and returning rawequal(a, b) there is exactly
  --            the default.
  --   __tostring -- unreachable: the only route to it is the global
  --            `tostring`, which `install_determinism` replaces with a version
  --            that resolves a proxy by name before any metamethod is
  --            considered.
  return P
end


-- ------------------------------------------------- determinism overrides on _G
-- Installed on the real library tables, because the stub environment falls
-- through to _G for anything the chunk did not define. Every one of these is a
-- source of run-to-run or machine-to-machine variation, or (os.exit) a way for
-- the target to truncate the probe's own output while still exiting 0. The
-- corpus was measured not to call any of them, which is exactly why they are
-- covered by synthetic tests rather than by corpus green.
--
-- `math.randomseed` is deliberately NOT overridden: it only calls C srand(),
-- and the replacement math.random never consults the C RNG, so a no-op
-- override would be a guard nothing could falsify. Checked by neutering: with
-- os.time() pinned to 0, deleting a math.randomseed override changed no test.
function M.install_determinism(G, S, record)
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
      local n = S.pname[v]
      if n then return "@" .. n end
      return "table: #" .. S.idof(v)
    end
    if t == "function" or t == "userdata" or t == "thread" then
      return t .. ": #" .. S.idof(v)
    end
    return tostring(v)
  end
  G.print = function(...)
    local n = select("#", ...)
    local parts = {}
    for i = 1, n do parts[i] = S.cstr((select(i, ...))) end
    record("P|" .. S.esc(tconcat(parts, "\t")))
  end
  G.io.write = function(...)
    local n = select("#", ...)
    local parts = {}
    for i = 1, n do parts[i] = S.cstr((select(i, ...))) end
    record("W|" .. S.esc(tconcat(parts, "")))
  end
end


-- ------------------------------------------------------------- environment
-- Every global the chunk writes is recorded in `envfields`, NEVER on `env`
-- itself, for the same reason as `pfields` above: rawset(env, k, v) would make
-- rawget(env, k) non-nil, so __newindex would fire only on the FIRST write to
-- each name -- measured: `X = 1 X = 2 X = 3` recorded only `G|X|1`, and
-- `A = 1; function main() A = A + 1 end` recorded no `G|A|...` event at all
-- for the reassignment. `envfields` is also what an invocation loop
-- enumerates and calls, since `env` itself is never populated.
--
-- `cfg.driver` is an optional table consulted between the chunk's own globals
-- and `_G` (L2's key-poll harness lives there). `cfg.get_proxy(name, segs)` is
-- `M.proxies(...).get`.
function M.stub_env(cfg)
  local G, S, record = cfg.G, cfg.S, cfg.record
  local get_proxy, driver = cfg.get_proxy, cfg.driver
  local envfields = {}
  local env = {}
  setmetatable(env, {
    __index = function(_, k)
      local v = envfields[k]
      if v ~= nil then return v end
      if driver then
        local d = driver[k]
        if d ~= nil then return d end
      end
      local base = G[k]
      if base ~= nil then return base end
      return get_proxy(S.keystr(k), {{"k", k}})
    end,
    __newindex = function(_, k, v)
      record("G|" .. S.keystr(k) .. "|" .. S.to_s(v))
      envfields[k] = v
    end,
  })
  return env, envfields
end


return M

-- M6 task 7: ENUMERATED differential driving of ONE proto.
--
-- The L1.75 probe (`probe_behaviour.lua`) runs a chunk once, under one fixed
-- stub-return policy, and compares the two sides' traces. That is a single
-- point of the input space. This probe drives the SAME stub environment with
-- an ASSIGNMENT: an explicit value for each of the access paths that a chosen
-- proto's branches actually read (its "channels", measured by
-- `scripts/observation_classes.py::channels`). Running every assignment in the
-- product and comparing both sides at each one turns "the two agree on the one
-- path the stubs happened to take" into "the two agree on every path the
-- proto's own branch conditions can select".
--
-- WHAT IT IS FOR. Not defect hunting -- M6 measured that the cheapest STATIC
-- instrument (`scripts/loss_sweep.py`) outperformed the designed dynamic ones
-- there. It is for the other half: PROVING SEMANTIC EQUIVALENCE WHERE BYTES
-- DIFFER, which is what Tasks 9-12 need when they change how a proto is
-- reconstructed.
--
-- SCOPE (do not assume more than this):
--   * One entry point per run, named by an ACCESS PATH (`E`), resolved on
--     BOTH sides by the same name -- so "the target was entered" is proven by
--     an event both sides record, not by a line number only one side has.
--   * Every function is called with NO arguments, as in L1.75. A parameter
--     reads as nil, not as a stub.
--   * An assignment holds a channel CONSTANT for the whole run. A poll loop
--     driven with `pressButton() == false` therefore never exits and is
--     truncated by the event cap; that is a bounded, identical truncation on
--     both sides, not a silent one (the status says CAP).
--   * `pfields` wins over an assignment: if the target WRITES the field an
--     assignment names, the written value is what later reads see. The
--     assignment models the ENGINE's value, and a script that overwrites it
--     has genuinely stopped reading the engine.
--
-- TWO MODES, selected by `M` in the spec file:
--   `discover` -- run the chunk, then walk the globals it defined looking for
--                 a function whose (linedefined, lastlinedefined) match `D`.
--                 Prints the ACCESS PATHS that reach it. This is how a nested
--                 proto ("main_76_2") is turned into a name both sides share;
--                 it is run against the ORIGINAL bytecode only, because only
--                 there do the line numbers belong to the proto tree the
--                 ledger names.
--   `drive`    -- run the chunk, install the assignments, call `E`, print the
--                 trace. Run identically on both sides.
--
-- OUTPUT. `ENUM1|<status>|<event count>` with status in {OK, CAP, INSN}, then
-- one line per event; or `LOADFAIL|<msg>`, `ENTRYFAIL|<msg>`, `SPECFAIL|<msg>`
-- -- three markers that are deliberately NOT comparable values (a typo'd
-- entry name produces the same string on both sides, and treating that as
-- agreement is the L1.5 probe's hardest-won lesson).
-- In `discover` mode: `ENUMD1|<n>` then `E|<access path>` lines, sorted.
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
local tonumber = tonumber
local pcall = pcall
local error = error
local assert = assert
local loadfile = loadfile
local getinfo = debug.getinfo
local sethook = debug.sethook
local osexit = os.exit
local tsort = table.sort
local tconcat = table.concat
local sfind = string.find
local ssub = string.sub
local schar = string.char
local sbyte = string.byte
local sformat = string.format
local iowrite = io.write

-- ---------------------------------------------------------------- constants
-- FROZEN, and the same numbers as the L1.75 gate: both sides of every
-- comparison must use them, and an enumeration whose truncation point moved
-- between assignments would compare two different amounts of behaviour.
-- Pinned against `probe_behaviour.lua` by
-- `test_frozen_constants_agree_with_the_l1_75_probe` in tests/test_probe_enum.py.
local MAX_EVENTS = 3000          -- the real budget
local HOOK_STEP = 1000000        -- debug hook granularity, VM instructions
local INSN_BACKSTOP = 400000000  -- backstop only; see probe_behaviour.lua
-- How deep the discovery walk descends through tables the chunk published.
-- 3 reaches `systemConfig.ConfigMain` (a method on a table a constructor
-- returned) and everything else this corpus needs; a bound is required
-- because a script-built table may be cyclic.
local DISCOVER_DEPTH = 4

local backstop_override = os.getenv("PYLUADEC_PROBE_INSN_BACKSTOP")
if backstop_override then INSN_BACKSTOP = tonumber(backstop_override) end

local target, specfile = ...

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

local S = C.serialiser()
local esc, keystr = S.esc, S.keystr

local function die(kind, msg)
  iowrite(kind .. "|" .. esc(msg) .. "\n")
  osexit(0)
end

-- ------------------------------------------------------------- the spec file
-- ASCII only, one directive per line, fields separated by a single space:
--
--   M <drive|discover>
--   D <linedefined> <lastlinedefined>     (discover)
--   E <access path>                       (drive; optional)
--   A <access path> <value>               (drive; repeatable)
--
-- An access path is `/`-joined tokens: `k<hex>` (string key), `i<int>`
-- (integer key), `d` (any other key), `c` (the result of CALLING the path so
-- far). A value is `s<hex>`, `n<number>`, `b0`, `b1` or `x` (nil).
--
-- Keys and string values are HEX, not literal text, for one reason: they can
-- be arbitrary bytes out of the constant pool. Hex keeps this file, its
-- command line and anything that logs them inside the project's ASCII rule
-- without a decoding policy having to exist.
local function unhex(h)
  local out, n = {}, 0
  if #h % 2 ~= 0 then die("SPECFAIL", "odd-length hex field") end
  for i = 1, #h, 2 do
    local b = tonumber(ssub(h, i, i + 1), 16)
    if b == nil then die("SPECFAIL", "bad hex field") end
    n = n + 1
    out[n] = schar(b)
  end
  return tconcat(out)
end

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

local function parse_path(text)
  local toks, n = split(text, "/")
  local segs = {}
  for i = 1, n do
    local t = toks[i]
    local kind = ssub(t, 1, 1)
    if kind == "k" then segs[i] = {"k", unhex(ssub(t, 2))}
    elseif kind == "i" then segs[i] = {"i", tonumber(ssub(t, 2))}
    elseif kind == "d" then segs[i] = {"d"}
    elseif kind == "c" then segs[i] = {"c"}
    else die("SPECFAIL", "bad path token") end
  end
  return segs, n
end

local function parse_value(text)
  local kind = ssub(text, 1, 1)
  if kind == "s" then return unhex(ssub(text, 2)) end
  if kind == "n" then return tonumber(ssub(text, 2)) end
  if kind == "b" then return ssub(text, 2) == "1" end
  if kind == "x" then return nil end
  die("SPECFAIL", "bad value code")
end

-- Human-readable rendering of an access path, for the `I|`/`R|`/`E|` events.
-- Bytes that are not printable ASCII are hex-escaped here rather than passed
-- through: these lines carry a NAME the report may quote, unlike the trace's
-- value fields, which stay raw.
--
-- `|` (0x7c) and `\\` (0x5c) are hex-escaped for a SECOND reason, and it is a
-- correctness one rather than a presentation one: the driver recognises its
-- own entry event by rebuilding this string in Python
-- (`probe_enum.py::path_text_of`) and matching it against the trace, while the
-- trace line itself goes through `esc`, which rewrites exactly those two bytes.
-- A key containing either would therefore never match, `entered` would be
-- permanently false and the verdict would be a spurious `never-reached`.
-- Escaping them here makes `esc` a no-op on the result, so the two renderings
-- agree by construction. Unreachable on this corpus -- `footprints.json`
-- measured `non_identifier_names == 0` over all 229 files -- so it is covered
-- by a synthetic test, not by corpus green.
local function tohex(v)
  local h = {}
  for j = 1, #v do h[j] = sformat("%02x", sbyte(v, j)) end
  return tconcat(h)
end

local function path_text(segs)
  local out = {}
  for i = 1, #segs do
    local s = segs[i]
    if s[1] == "k" then
      local v, ok = s[2], true
      for j = 1, #v do
        local b = sbyte(v, j)
        if b < 0x20 or b > 0x7e or b == 0x2e or b == 0x2f
            or b == 0x5c or b == 0x7c then ok = false end
      end
      out[#out + 1] = (i > 1 and "." or "") .. (ok and v or ("0x" .. tohex(v)))
    elseif s[1] == "i" then out[#out + 1] = "[" .. s[2] .. "]"
    elseif s[1] == "d" then out[#out + 1] = "[*]"
    else out[#out + 1] = "()" end
  end
  return tconcat(out)
end

-- The machine-readable form, i.e. what `parse_path` reads back. `discover`
-- emits both: the text is what a human and a report see, the spec is what the
-- driver feeds to the other side.
local function path_spec(segs)
  local out = {}
  for i = 1, #segs do
    local s = segs[i]
    if s[1] == "k" then out[i] = "k" .. tohex(s[2])
    elseif s[1] == "i" then out[i] = "i" .. s[2]
    elseif s[1] == "d" then out[i] = "d"
    else out[i] = "c" end
  end
  return tconcat(out, "/")
end

local mode, want_ld, want_lld, entry_segs = nil, nil, nil, nil
local assigns = {}   -- list of {segs, value, has_value}

do
  local fh = io.open(specfile, "rb")
  if fh == nil then die("SPECFAIL", "spec file not readable") end
  local text = fh:read("*a")
  fh:close()
  local lines, nl = split(text, "\n")
  for i = 1, nl do
    local line = lines[i]
    if line ~= "" then
      local fields, nf = split(line, " ")
      local d = fields[1]
      if d == "M" then
        mode = fields[2]
      elseif d == "D" then
        want_ld, want_lld = tonumber(fields[2]), tonumber(fields[3])
      elseif d == "E" then
        entry_segs = parse_path(fields[2])
      elseif d == "A" then
        if nf < 3 then die("SPECFAIL", "A needs a path and a value") end
        assigns[#assigns + 1] = {parse_path(fields[2]), parse_value(fields[3])}
      else
        die("SPECFAIL", "unknown directive")
      end
    end
  end
end
if mode ~= "drive" and mode ~= "discover" then
  die("SPECFAIL", "M must be drive or discover")
end
if mode == "discover" and (want_ld == nil or want_lld == nil) then
  die("SPECFAIL", "discover needs D")
end

-- ------------------------------------------------------- the assignment trie
-- Assignments are matched against a proxy's SEGMENT list, not against its
-- dotted name: a dotted string cannot distinguish the single key `a.b` from
-- the path `a` then `b`, and nothing guarantees a corpus key is an identifier.
-- At each step an exact key beats a wildcard, so `gameSave.myCard[140].hold`
-- and `gameSave.myCard[*].hold` can both be assigned in one run and the
-- specific one wins for index 140.
local root = {k = {}, i = {}}

local function trie_insert(segs, value)
  local node = root
  for j = 1, #segs do
    local s = segs[j]
    local nxt
    if s[1] == "k" then
      nxt = node.k[s[2]]
      if nxt == nil then nxt = {k = {}, i = {}} node.k[s[2]] = nxt end
    elseif s[1] == "i" then
      nxt = node.i[s[2]]
      if nxt == nil then nxt = {k = {}, i = {}} node.i[s[2]] = nxt end
    elseif s[1] == "d" then
      nxt = node.d
      if nxt == nil then nxt = {k = {}, i = {}} node.d = nxt end
    else
      nxt = node.c
      if nxt == nil then nxt = {k = {}, i = {}} node.c = nxt end
    end
    node = nxt
  end
  node.has = true
  node.value = value
end

for j = 1, #assigns do trie_insert(assigns[j][1], assigns[j][2]) end

-- `(has, value)`. Descends preferring an exact match and falling back to the
-- wildcard branch at each level, so the search is a small backtracking walk
-- rather than a single greedy descent.
local function trie_find(node, segs, j)
  if node == nil then return false end
  if j > #segs then
    if node.has then return true, node.value end
    return false
  end
  local s = segs[j]
  local exact
  if s[1] == "k" then exact = node.k[s[2]]
  elseif s[1] == "i" then exact = node.i[s[2]]
  elseif s[1] == "c" then exact = node.c end
  if exact ~= nil then
    local ok, v = trie_find(exact, segs, j + 1)
    if ok then return true, v end
  end
  if s[1] ~= "c" then
    local ok, v = trie_find(node.d, segs, j + 1)
    if ok then return true, v end
  end
  return false
end

-- ------------------------------------------------------------------ recording
local R = C.recorder{
  max_events = MAX_EVENTS,
  osexit = osexit,
  render = function(r)
    local out = {"ENUM1|" .. (r.stopped or "OK") .. "|" .. r.nev}
    for i = 1, r.nev do out[i + 1] = r.ev[i] end
    return tconcat(out, "\n")
  end,
}
local append, record, flush_and_exit = R.append, R.record, R.flush_and_exit
local function errtext(e) return C.errtext(S, e) end

-- -------------------------------------------------------------- stub proxies
-- The L1.75 stub environment, plus two injection hooks. With no assignments
-- at all the two probes' proxies behave identically (asserted by
-- `test_with_no_assignments_the_trace_matches_the_l1_75_probes` in
-- tests/test_probe_enum.py, which compares a whole trace body).
local P
P = C.proxies{
  S = S,
  record = function(s) record(s) end,
  track_segs = true,
  on_read = function(_self, _k, _child, segs)
    return trie_find(root, segs, 1)
  end,
  on_call = function(self, _name, ...)
    local segs = P.psegs[self]
    local q = {}
    for i = 1, #segs do q[i] = segs[i] end
    q[#q + 1] = {"c"}
    return trie_find(root, q, 1)
  end,
}
local get_proxy = P.get

C.install_determinism(G, S, record)

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
  -- See probe_common.lua's `recorder`: a previous raise was swallowed by a
  -- pcall inside the TARGET, and re-raising would be swallowed again forever.
  if R.stopped then flush_and_exit() end
  hook_calls = hook_calls + 1
  if hook_calls * HOOK_STEP >= INSN_BACKSTOP then
    R.stopped = "INSN"
    error("__PLD_INSN__", 0)
  end
end, "", HOOK_STEP)

local ok, err = pcall(f)
if not ok then append("X|<chunk>|" .. errtext(err)) end

-- ------------------------------------------------------------------ discover
if mode == "discover" then
  sethook()
  local hits = {}
  local seen = {}
  local function walk(tbl, prefix, depth)
    if depth > DISCOVER_DEPTH or seen[tbl] then return end
    seen[tbl] = true
    local keys, n = {}, 0
    for k in pairs(tbl) do
      if type(k) == "string" or type(k) == "number" then
        n = n + 1
        keys[n] = k
      end
    end
    tsort(keys, function(a, b) return keystr(a) < keystr(b) end)
    for idx = 1, n do
      local k = keys[idx]
      local v = tbl[k]
      local seg
      if type(k) == "string" then seg = {"k", k}
      elseif k == (k - k % 1) then seg = {"i", k}
      else seg = {"d"} end
      local path = {}
      for i = 1, #prefix do path[i] = prefix[i] end
      path[#path + 1] = seg
      if type(v) == "function" then
        local info = getinfo(v, "S")
        if info ~= nil and info.linedefined == want_ld
            and info.lastlinedefined == want_lld then
          hits[#hits + 1] = path_text(path) .. "|" .. path_spec(path)
        end
      elseif type(v) == "table" and S.pname[v] == nil then
        walk(v, path, depth + 1)
      end
    end
  end
  walk(envfields, {}, 1)
  tsort(hits)
  local out = {"ENUMD1|" .. #hits}
  for i = 1, #hits do out[i + 1] = "E|" .. hits[i] end
  iowrite(tconcat(out, "\n"), "\n")
  osexit(0)
end

-- --------------------------------------------------------------------- drive
if entry_segs ~= nil and not R.stopped then
  local v = envfields
  for i = 1, #entry_segs do
    if type(v) ~= "table" then v = nil break end
    local s = entry_segs[i]
    if s[1] ~= "k" and s[1] ~= "i" then v = nil break end
    v = rawget(v, s[2])
    if v == nil then break end
  end
  local name = path_text(entry_segs)
  if type(v) ~= "function" then
    -- DEFENSIVE, copied from probe_keyseq.lua with its reason: `die` writes
    -- and hard-exits through the real `os.exit`, so the hook cannot fire in
    -- between; it stays so a future edit that makes `die` return does not run
    -- the rest of this file under a live hook.
    sethook()
    die("ENTRYFAIL", "entry '" .. name .. "' is a " ..
        (v == nil and "nil" or type(v)) .. ", not a function")
  end
  append("I|" .. esc(name))
  if not R.stopped then
    local okf, errf = pcall(v)
    if okf then
      append("R|" .. esc(name) .. "|ok")
    else
      append("R|" .. esc(name) .. "|" .. errtext(errf))
    end
  end
end

sethook()
flush_and_exit()

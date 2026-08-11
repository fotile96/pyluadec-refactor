-- L1.5 gate probe: load a chunk, pcall it, and deterministically serialise the
-- delta it made to the global table, so the original corpus bytecode and our
-- decompiled output can be compared on real content without the game engine.
--
-- SCOPE (do not assume more than this): only globals that did NOT exist before
-- the chunk ran are compared (`if not base[k]`). Assignments to pre-existing
-- globals (including everything in the standard library) and in-place mutation
-- of an already-existing global table are INVISIBLE to this probe. That is a
-- deliberate simplification -- corpus chunks build their own top-level tables
-- -- but it means a green comparison is not evidence of full _G equivalence.
--
-- No Lua string patterns anywhere in this file (plain indexing / plain find
-- only), matching the repo-wide no-regex rule for analysis and emit layers.

-- Everything the probe itself needs is bound to a local BEFORE the target
-- chunk gets a chance to run. Otherwise a chunk that assigns `tostring = nil`
-- (or clobbers pairs/print/table/string) blinds the probe, which then produces
-- no output at all -- and two chunks that produce no output compare equal.
local G = _G
local pairs = pairs
local type = type
local tostring = tostring
local print = print
local loadfile = loadfile
local pcall = pcall
local osexit = os.exit
local tsort = table.sort
local tconcat = table.concat
local sformat = string.format
local sfind = string.find
local ssub = string.sub
local sbyte = string.byte

local target = ...

-- Lua 5.1 formats both load and runtime errors as "<source>:<line>: <message>".
-- The source and line necessarily differ between the .luac input (stripped
-- bytecode: source "?", no line info) and the .lua input, so the prefix cannot
-- be compared -- but the residue is derived from string constants and opcode
-- semantics and is comparable. Strip the first "<anything>:<digits>: " prefix.
local function strip_location(msg)
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

local function ser(v, depth, seen)
  local t = type(v)
  if t == "table" then
    if depth > 4 then return "<deep>" end
    if seen[v] then return "<cycle>" end
    seen[v] = true
    -- Key on type(k)..":"..tostring(k), and carry (key, value) together
    -- through the sort. Keying on tostring(k) alone collapses the number 1
    -- and the string "1" onto one entry, which loses one value and emits the
    -- other twice -- two genuinely different tables then serialise identically
    -- (a false pass). Carrying the value also removes the O(n^2) re-scan the
    -- previous version did to re-find each key.
    local items, n = {}, 0
    for k, vv in pairs(v) do
      n = n + 1
      items[n] = {k = type(k) .. ":" .. tostring(k), v = vv}
    end
    tsort(items, function(a, b) return a.k < b.k end)
    local parts = {}
    for i = 1, n do parts[i] = items[i].k .. "=" .. ser(items[i].v, depth + 1, seen) end
    seen[v] = nil
    return "{" .. tconcat(parts, ",") .. "}"
  elseif t == "number" then
    return sformat("%.17g", v)
  elseif t == "function" or t == "userdata" or t == "thread" then
    return "<" .. t .. ">"
  else
    return tostring(v)
  end
end

local basekey, baseval = {}, {}
for k, v in pairs(G) do basekey[k] = true baseval[k] = v end

local f, loaderr = loadfile(target)
if not f then
  local m = strip_location(loaderr)
  print("LOADFAIL|" .. (m or ser(loaderr, 0, {})))
  osexit(0)
end

local ok, err = pcall(f)

-- Restore every PRE-EXISTING global to the value it had before the chunk ran.
-- Local binding above is not sufficient on its own: Lua 5.1's C `print`
-- (luaB_print) re-resolves the global `tostring` on every call, so a chunk
-- doing `tostring = nil` makes the probe itself error out. Pre-existing
-- globals are never part of the compared delta, so restoring them cannot
-- mask a real difference -- it only stops the target chunk from blinding
-- the instrument.
for k in pairs(basekey) do G[k] = baseval[k] end

local items, n = {}, 0
for k, vv in pairs(G) do
  if not basekey[k] then
    n = n + 1
    items[n] = {k = type(k) .. ":" .. tostring(k), v = vv}
  end
end
tsort(items, function(a, b) return a.k < b.k end)
local out = {}
for i = 1, n do out[i] = items[i].k .. "=" .. ser(items[i].v, 0, {}) end

local head
if ok then
  head = "OK|"
else
  -- Print the error, not just the fact that there was one. Without this every
  -- distinct failure collapses to the constant "ERR|", and two sides that fail
  -- for entirely unrelated reasons at unrelated points compare equal.
  local m = strip_location(err)
  head = "ERR|" .. (m or ser(err, 0, {})) .. "|"
end
print(head .. tconcat(out, "\n"))

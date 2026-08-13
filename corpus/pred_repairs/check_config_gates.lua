-- Targeted driver for the two ConfigMain (`main_76_2`) checkpoints.
--
--   lua_sz4 check_defect2.lua <chunk> <firstFragment> <memoryFlag> <spec>
--
-- `<chunk>` is either the original stripped bytecode or a predecessor/repaired
-- .lua source; `<spec>` is `frame,KEY;frame,KEY;...;tail=KEY`.
--
-- Why this exists: `scripts/probe_keyseq.py` stubs `gameSave.tutorial.
-- firstFragment` and `memoryFlag`, which are exactly the two gates that select
-- the arms under test, so its traces are blind here. This driver gives those
-- two globals concrete values and drives the loop itself.
--
-- Nothing here decodes or prints a corpus string: `seName` is replaced with
-- ASCII names of this file's own making, every other recorded argument is a
-- number or a boolean.

local target, ff, mf, spec = ...

local G = _G
local ev, nev = {}, 0
local function rec(s) nev = nev + 1 ev[nev] = s end

local function fmt(v)
  local t = type(v)
  if t == "number" or t == "boolean" or t == "nil" then return tostring(v) end
  if t == "string" then return v end
  return t
end

-- ------------------------------------------------------------- stub globals
local proxy_mt = {}
local pname = setmetatable({}, {__mode = "k"})
local cache = {}
local function P(name)
  local p = cache[name]
  if p then return p end
  p = setmetatable({}, proxy_mt)
  pname[p] = name
  cache[name] = p
  return p
end
proxy_mt.__index = function(s, k) return P(pname[s] .. "." .. tostring(k)) end
proxy_mt.__newindex = function(s, k, v) rawset(s, k, v) end
proxy_mt.__call = function() return nil end
local function zero() return 0 end
proxy_mt.__add, proxy_mt.__sub, proxy_mt.__mul = zero, zero, zero
proxy_mt.__div, proxy_mt.__mod, proxy_mt.__pow, proxy_mt.__unm = zero, zero, zero, zero
proxy_mt.__concat = function(a, b) return fmt(a) .. fmt(b) end
proxy_mt.__lt = function() return false end
proxy_mt.__le = function() return false end

setmetatable(G, {__index = function(_, k) return P(tostring(k)) end})

-- --------------------------------------------------------------- the driver
local keys_at, tail_key, frame = {}, nil, 1
do
  local i = 1
  while i <= #spec do
    local j = string.find(spec, ";", i, true) or (#spec + 1)
    local d = string.sub(spec, i, j - 1)
    if d ~= "" then
      if string.sub(d, 1, 5) == "tail=" then
        tail_key = string.sub(d, 6)
      else
        local c = string.find(d, ",", 1, true)
        keys_at[tonumber(string.sub(d, 1, c - 1))] = string.sub(d, c + 1)
      end
    end
    i = j + 1
  end
end

local last_explicit = 0
for f in pairs(keys_at) do if f > last_explicit then last_explicit = f end end

function G.pressButton(name)
  local want = keys_at[frame]
  if want == nil and frame > last_explicit then want = tail_key end
  local down = (want == name)
  rec("K|" .. tostring(name) .. "|" .. frame .. "|" .. tostring(down))
  return down
end

function G.wait(n)
  n = tonumber(n) or 1
  if n < 1 then n = 1 end
  frame = frame + math.floor(n)
  rec("W|" .. math.floor(n) .. "|" .. frame)
end

function G.keyPlaySE(v) rec("SE|" .. fmt(v)) end
function G.layerClip(a, b, c, d, e)
  rec("CLIP|" .. fmt(a) .. "," .. fmt(b) .. "," .. fmt(c) .. "," .. fmt(d) .. "," .. fmt(e))
end
function G.layerMovePosition(a, b, c, d)
  rec("MOVE|" .. fmt(a) .. "," .. fmt(b) .. "," .. fmt(c) .. "," .. fmt(d))
end

-- ------------------------------------------------------------------- run it
local chunk = assert(loadfile(target))
local ok, err = pcall(chunk)
if not ok then
  io.write("LOADFAIL|" .. tostring(err) .. "\n")
  os.exit(0)
end

G.gameSave = {tutorial = {firstFragment = tonumber(ff)}}
G.memoryFlag = (mf == "true")
G.systemSave = {storyLineSkip = 0}
G.seName = {circle = "circle", cross = "cross", arrowKey = "arrowKey"}
G.retFlag = false

local budget = 400000
local stopped = nil
debug.sethook(function()
  stopped = "HANG"
  error("__PLD_BUDGET__", 0)
end, "", budget)

local ok2, res = pcall(function() return G.systemConfig.ConfigMain() end)
debug.sethook()

local status
if stopped == "HANG" then
  status = "HANG"
elseif not ok2 then
  status = "ERROR|" .. tostring(res)
else
  status = "OK|" .. fmt(res)
end
io.write(status .. "|events=" .. nev .. "|lastframe=" .. frame .. "\n")
for i = 1, nev do io.write(ev[i] .. "\n") end
os.exit(0)

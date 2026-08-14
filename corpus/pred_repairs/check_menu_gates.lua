-- Targeted driver for the four `snr_mainmenu.lua` menu-refresh gates
-- (`main_7`, the `library` arm of the CIRCLE handler).
--
--   lua_sz4 check_menu_gates.lua <chunk> <novelFlag> <musicFlag> <spec>
--
-- `<chunk>` is either the original stripped bytecode or a predecessor/repaired
-- .lua source; `<spec>` is `frame,KEY;frame,KEY;...;tail=KEY`.
--
-- Why this exists: `scripts/probe_keyseq.py` stubs `gameSave.startMenuState`,
-- so `gameSave.startMenuState == 0` is false against a proxy and the whole menu
-- loop is skipped -- its trace never reaches the gate under test. This driver
-- gives `gameSave`, `systemSave.libFlag` and the two flags concrete values so
-- the CIRCLE handler's `library` arm actually runs, and records the layer calls
-- the gate selects between.
--
-- Nothing here records a corpus string: string arguments are recorded as
-- `s<len>`, every other recorded argument is a number or a boolean.

local target, novelFlag, musicFlag, spec = ...

local G = _G
local ev, nev = {}, 0
local CAP = 4000
local capped = false

local function fmt(v)
  local t = type(v)
  if t == "number" or t == "boolean" or t == "nil" then return tostring(v) end
  if t == "string" then return "s" .. string.len(v) end
  return t
end

local function rec(s)
  if nev >= CAP then capped = true error("__PLD_CAP__", 0) end
  nev = nev + 1
  ev[nev] = s
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

function G.layerVisible(a, b) rec("VIS|" .. fmt(a) .. "," .. fmt(b)) end
function G.layerAlpha(a, b) rec("ALPHA|" .. fmt(a) .. "," .. fmt(b)) end
function G.layerMoveAlpha(a, b, c) rec("MOVA|" .. fmt(a) .. "," .. fmt(b) .. "," .. fmt(c)) end
function G.layerPosition(a, b, c) rec("POS|" .. fmt(a) .. "," .. fmt(b) .. "," .. fmt(c)) end
function G.keyPlaySE(v) rec("SE|" .. fmt(v)) end

-- Concrete save data. `startMenuState == 0` selects the eight-entry menu whose
-- `novel`/`music` rows the gate hides; `libFlag` is what lets the cursor rest on
-- `library`, which is the entry whose CIRCLE arm rebuilds the menu.
local card = {}
setmetatable(card, {__index = function(_, _) return {hold = 0} end})
G.gameSave = {startMenuState = 0, myCard = card}
G.systemSave = {
  libFlag = true,
  novelFlag = (novelFlag == "true"),
  musicFlag = (musicFlag == "true"),
  novelGetFlag = {}, memoryFlag = {}, cgFlag = {},
}
G.seName = {circle = "circle", cross = "cross", arrowKey = "arrowKey"}

-- ------------------------------------------------------------------- run it
local chunk = assert(loadfile(target))
local ok, err = pcall(chunk)
if not ok then
  io.write("LOADFAIL|" .. tostring(err) .. "\n")
  os.exit(0)
end

local budget = 4000000
local stopped = nil
debug.sethook(function()
  stopped = "HANG"
  error("__PLD_BUDGET__", 0)
end, "", budget)

local ok2, res = pcall(function() return G.main() end)
debug.sethook()

local status
if capped then status = "CAP"
elseif stopped == "HANG" then status = "HANG"
elseif not ok2 then status = "ERROR|" .. tostring(res)
else status = "OK|" .. fmt(res) end
io.write(status .. "|events=" .. nev .. "|lastframe=" .. frame .. "\n")
for i = 1, nev do io.write(ev[i] .. "\n") end
os.exit(0)

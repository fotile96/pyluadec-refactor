-- Targeted driver for `snr_common.lua`'s `autoSystemSave` (`main_75`) retry loop.
--
--   lua_sz4 check_autosave_retry.lua <chunk> <false_runs> <answers>
--
-- `<chunk>` is either the original stripped bytecode or a predecessor/repaired
-- .lua source. `<false_runs>` is how many leading calls to
-- `succeedLoadSystemdata()` return false before it starts returning true;
-- `<answers>` is a comma-separated list of what successive confirm dialogs
-- return ("true"/"false"), the last entry repeating -- e.g. `true,false`
-- answers the first dialog yes and every later one no, which is the only way
-- to reach the loop body's `break`.
--
-- Why this exists: `scripts/probe_keyseq.py` never calls `autoSystemSave` (it
-- drives `main` and the two `systemOption`/`systemConfig` methods), and every
-- global this function branches on is stubbed there, so its traces cannot see
-- whether the retry loops. This driver makes the load result a scripted
-- sequence and records the call order.
--
-- Nothing here records a corpus string: string arguments are recorded as
-- `s<len>`, every other recorded argument is a number or a boolean.

local target, false_runs, answers = ...
false_runs = tonumber(false_runs) or 0
local answer_list = {}
do
  local i = 1
  while i <= #answers do
    local j = string.find(answers, ",", i, true) or (#answers + 1)
    answer_list[#answer_list + 1] = (string.sub(answers, i, j - 1) == "true")
    i = j + 1
  end
  if #answer_list == 0 then answer_list[1] = false end
end
local dialogs = 0

local G = _G
local ev, nev = {}, 0
local CAP = 200
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

-- ------------------------------------------------------------------- run it
local chunk = assert(loadfile(target))
local ok, err = pcall(chunk)
if not ok then
  io.write("LOADFAIL|" .. tostring(err) .. "\n")
  os.exit(0)
end

local loads = 0
function G.succeedLoadSystemdata()
  loads = loads + 1
  local r = (loads > false_runs)
  rec("LOAD|" .. loads .. "|" .. tostring(r))
  return r
end
function G.existSystemdata() rec("EXIST|true") return true end
function G.comDlgYesNo(a, b, c)
  dialogs = dialogs + 1
  local answer = answer_list[dialogs] or answer_list[#answer_list]
  rec("DLG|" .. dialogs .. "," .. fmt(b) .. "," .. fmt(c) .. "|" .. tostring(answer))
  return answer
end
function G.cGetFileName(a, b) return "f" end
function G.runAutoSave() rec("SAVE") end
function G.applySystemdata() rec("APPLY") end
function G.wait(n) rec("W|" .. tostring(tonumber(n) or 1)) end

local budget = 2000000
local stopped = nil
debug.sethook(function()
  stopped = "HANG"
  error("__PLD_BUDGET__", 0)
end, "", budget)

local ok2, res = pcall(function() return G.autoSystemSave(0) end)
debug.sethook()

local status
if capped then status = "CAP"
elseif stopped == "HANG" then status = "HANG"
elseif not ok2 then status = "ERROR|" .. tostring(res)
else status = "OK|" .. fmt(res) end
io.write(status .. "|events=" .. nev .. "|loads=" .. loads .. "\n")
for i = 1, nev do io.write(ev[i] .. "\n") end
os.exit(0)

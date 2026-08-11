-- Helpers shared by the probe scripts (`probe_global_state.lua`, L1.5, and
-- `probe_behaviour.lua`, L1.75). Loaded with `loadfile(<dir of arg[0]>)` by
-- each probe rather than `require`, so the probes stay runnable as bare
-- `lua scripts/probe_X.lua <target>` with no package.path setup.
--
-- No Lua string patterns anywhere in this file (plain `string.find(..., true)`
-- and byte indexing only), matching the repo-wide no-regex rule.

local type = type
local sfind = string.find
local ssub = string.sub
local sbyte = string.byte

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

return M

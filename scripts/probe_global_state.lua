local target = ...
local base = {}
for k in pairs(_G) do base[k] = true end
local f = loadfile(target)
if not f then print("LOADFAIL") os.exit(0) end
local ok, err = pcall(f)
local out = {}
local function ser(v, depth, seen)
  local t = type(v)
  if t == "table" then
    if depth > 4 then return "<deep>" end
    if seen[v] then return "<cycle>" end
    seen[v] = true
    local keys = {}
    for k in pairs(v) do keys[#keys+1] = tostring(k) end
    table.sort(keys)
    local parts = {}
    for _, ks in ipairs(keys) do
      local val
      for k, vv in pairs(v) do if tostring(k) == ks then val = vv break end end
      parts[#parts+1] = ks .. "=" .. ser(val, depth + 1, seen)
    end
    seen[v] = nil
    return "{" .. table.concat(parts, ",") .. "}"
  elseif t == "number" then
    return string.format("%.17g", v)
  elseif t == "function" or t == "userdata" or t == "thread" then
    return "<" .. t .. ">"
  else
    return tostring(v)
  end
end
local names = {}
for k in pairs(_G) do if not base[k] then names[#names+1] = tostring(k) end end
table.sort(names)
for _, n in ipairs(names) do
  local val
  for k, vv in pairs(_G) do if tostring(k) == n then val = vv break end end
  out[#out+1] = n .. "=" .. ser(val, 0, {})
end
print((ok and "OK|" or "ERR|") .. table.concat(out, "\n"))

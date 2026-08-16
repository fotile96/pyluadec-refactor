local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_F = {}
__pld_F["main_0"] = function(__pld_U)
return function()
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = 0
__pld_R[1] = 1
__pld_R[2] = 1
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["musicTitle"]
__pld_R[3] = #(__pld_R[3])
__pld_R[4] = 1
do
local __pld_i = __pld_tonumber(__pld_R[2]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[3]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[4]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[2] = __pld_i - __pld_s __pld_R[3] = __pld_l __pld_R[4] = __pld_s
end
__pld_pc = 144
elseif __pld_pc == 9 then
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["selectFlag"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["musicTitle"]
__pld_R[7] = __pld_R[7][__pld_R[5]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
if not (__pld_R[6] == 0) then __pld_pc = 16 else __pld_pc = 17 end
elseif __pld_pc == 16 then
__pld_pc = 28
elseif __pld_pc == 17 then
__pld_R[6] = layerCopy
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["layerName"]
__pld_R[8] = __pld_R[8]["music_off"]
__pld_R[6](__pld_R[7], __pld_R[8])
__pld_pc = 65
elseif __pld_pc == 28 then
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["selectFlag"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["musicTitle"]
__pld_R[7] = __pld_R[7][__pld_R[5]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
if not (__pld_R[6] == 1) then __pld_pc = 35 else __pld_pc = 36 end
elseif __pld_pc == 35 then
__pld_pc = 47
elseif __pld_pc == 36 then
__pld_R[6] = layerCopy
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["layerName"]
__pld_R[8] = __pld_R[8]["music_select"]
__pld_R[6](__pld_R[7], __pld_R[8])
__pld_pc = 65
elseif __pld_pc == 47 then
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["selectFlag"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["musicTitle"]
__pld_R[7] = __pld_R[7][__pld_R[5]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
if not (__pld_R[6] == 2) then __pld_pc = 54 else __pld_pc = 55 end
elseif __pld_pc == 54 then
__pld_pc = 65
elseif __pld_pc == 55 then
__pld_R[6] = layerCopy
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["layerName"]
__pld_R[8] = __pld_R[8]["music_on"]
__pld_R[6](__pld_R[7], __pld_R[8])
__pld_pc = 65
elseif __pld_pc == 65 then
if not (__pld_R[5] <= 10) then __pld_pc = 66 else __pld_pc = 67 end
elseif __pld_pc == 66 then
__pld_pc = 90
elseif __pld_pc == 67 then
__pld_R[6] = layerClip
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = 0
__pld_R[9] = __pld_R[5] - 1
__pld_R[9] = __pld_R[9] * 20
__pld_R[10] = 120
__pld_R[11] = __pld_R[5] * 20
__pld_R[6](__pld_R[7], __pld_R[8], __pld_R[9], __pld_R[10], __pld_R[11])
__pld_R[6] = layerPosition
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = 5
__pld_R[9] = __pld_R[1] * 20
__pld_R[9] = __pld_R[9] + 25
__pld_R[6](__pld_R[7], __pld_R[8], __pld_R[9])
__pld_pc = 139
elseif __pld_pc == 90 then
if not (__pld_R[5] <= 20) then __pld_pc = 91 else __pld_pc = 92 end
elseif __pld_pc == 91 then
__pld_pc = 116
elseif __pld_pc == 92 then
__pld_R[6] = layerClip
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = 128
__pld_R[9] = __pld_R[5] - 11
__pld_R[9] = __pld_R[9] * 20
__pld_R[10] = 350
__pld_R[11] = __pld_R[5] - 10
__pld_R[11] = __pld_R[11] * 20
__pld_R[6](__pld_R[7], __pld_R[8], __pld_R[9], __pld_R[10], __pld_R[11])
__pld_R[6] = layerPosition
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = 128
__pld_R[9] = __pld_R[1] * 20
__pld_R[9] = __pld_R[9] + 25
__pld_R[6](__pld_R[7], __pld_R[8], __pld_R[9])
__pld_pc = 139
elseif __pld_pc == 116 then
__pld_R[6] = layerClip
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = 350
__pld_R[9] = __pld_R[5] - 21
__pld_R[9] = __pld_R[9] * 20
__pld_R[10] = 480
__pld_R[11] = __pld_R[5] - 20
__pld_R[11] = __pld_R[11] * 20
__pld_R[6](__pld_R[7], __pld_R[8], __pld_R[9], __pld_R[10], __pld_R[11])
__pld_R[6] = layerPosition
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[7] = __pld_R[7]["bg"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[7] = __pld_R[7] + __pld_R[5]
__pld_R[8] = 350
__pld_R[9] = __pld_R[1] * 20
__pld_R[9] = __pld_R[9] + 25
__pld_R[6](__pld_R[7], __pld_R[8], __pld_R[9])
__pld_pc = 139
elseif __pld_pc == 139 then
__pld_R[1] = __pld_R[1] + 1
if not (10 < __pld_R[1]) then __pld_pc = 141 else __pld_pc = 142 end
elseif __pld_pc == 141 then
__pld_pc = 144
elseif __pld_pc == 142 then
__pld_R[1] = 1
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 144
elseif __pld_pc == 144 then
do local __pld_s = __pld_R[4] local __pld_i = __pld_R[2] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[3]) or (__pld_s <= 0 and __pld_i >= __pld_R[3]) then
__pld_R[2] = __pld_i __pld_R[5] = __pld_i __pld_pc = 9
else __pld_pc = 145 end end
elseif __pld_pc == 145 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_1"] = function(__pld_U)
return function()
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = startLoading
__pld_R[0]()
__pld_R[0] = comLayerLoadFalse
__pld_R[1] = __pld_U[0].v
__pld_R[1] = __pld_R[1]["layerName"]
__pld_R[1] = __pld_R[1]["music_select"]
__pld_R[2] = "music/music_02_a.gim"
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = comLayerLoadFalse
__pld_R[1] = __pld_U[0].v
__pld_R[1] = __pld_R[1]["layerName"]
__pld_R[1] = __pld_R[1]["music_off"]
__pld_R[2] = "music/music_03_a.gim"
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = comLayerLoadFalse
__pld_R[1] = __pld_U[0].v
__pld_R[1] = __pld_R[1]["layerName"]
__pld_R[1] = __pld_R[1]["music_on"]
__pld_R[2] = "music/music_04_a.gim"
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = waitLoading
__pld_R[0]()
__pld_R[0] = wait
__pld_R[1] = 30
__pld_R[0](__pld_R[1])
__pld_R[0] = math
__pld_R[0] = __pld_R[0]["random"]
__pld_R[1] = 1
__pld_R[2] = 3
__pld_R[0] = __pld_R[0](__pld_R[1], __pld_R[2])
if not (__pld_R[0] == 1) then __pld_pc = 32 else __pld_pc = 33 end
elseif __pld_pc == 32 then
__pld_pc = 43
elseif __pld_pc == 33 then
__pld_R[1] = layerLoad
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["layerName"]
__pld_R[2] = __pld_R[2]["bg"]
__pld_R[3] = cGetFileName
__pld_R[4] = "bg"
__pld_R[5] = "bg_3_b_0"
do 
local __pld_rs = __pld_pack(__pld_R[3](__pld_R[4], __pld_R[5]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 3 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 3 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 2 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 2 + __pld_i - 1) end __pld_R[1](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_pc = 66
elseif __pld_pc == 43 then
if not (__pld_R[0] == 2) then __pld_pc = 44 else __pld_pc = 45 end
elseif __pld_pc == 44 then
__pld_pc = 55
elseif __pld_pc == 45 then
__pld_R[1] = layerLoad
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["layerName"]
__pld_R[2] = __pld_R[2]["bg"]
__pld_R[3] = cGetFileName
__pld_R[4] = "bg"
__pld_R[5] = "bg_7_b_0"
do 
local __pld_rs = __pld_pack(__pld_R[3](__pld_R[4], __pld_R[5]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 3 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 3 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 2 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 2 + __pld_i - 1) end __pld_R[1](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_pc = 66
elseif __pld_pc == 55 then
if not (__pld_R[0] == 3) then __pld_pc = 56 else __pld_pc = 57 end
elseif __pld_pc == 56 then
__pld_pc = 66
elseif __pld_pc == 57 then
__pld_R[1] = layerLoad
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["layerName"]
__pld_R[2] = __pld_R[2]["bg"]
__pld_R[3] = cGetFileName
__pld_R[4] = "bg"
__pld_R[5] = "bg_8_a_0"
do 
local __pld_rs = __pld_pack(__pld_R[3](__pld_R[4], __pld_R[5]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 3 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 3 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 2 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 2 + __pld_i - 1) end __pld_R[1](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_pc = 66
elseif __pld_pc == 66 then
__pld_R[1] = layerLoad
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["layerName"]
__pld_R[2] = __pld_R[2]["bg"]
__pld_R[2] = __pld_R[2] + 1
__pld_R[3] = "music/music_01_a.gim"
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = endLoading
__pld_R[1]()
__pld_R[1] = __pld_U[1].v
__pld_R[1]()
__pld_R[1] = switchScreen
__pld_R[2] = 0
__pld_R[3] = ""
__pld_R[4] = 60
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4])
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_2"] = function(__pld_U)
return function()
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = cInitGame
__pld_R[0]()
__pld_R[0] = switchScreen
__pld_R[1] = 0
__pld_R[2] = ""
__pld_R[3] = 60
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_3"] = function(__pld_U)
return function()
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = systemConfig
__pld_R[0] = __pld_R[0]["unsetConfigButton"]
__pld_R[0]()
__pld_R[0] = logEnable
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = advPart
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = __pld_U[0].v
__pld_R[0]()
__pld_pc = 12
elseif __pld_pc == 12 then
__pld_R[0] = pressButton
__pld_R[1] = "UP"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 16 else __pld_pc = 17 end
elseif __pld_pc == 16 then
__pld_pc = 64
elseif __pld_pc == 17 then
__pld_R[0] = __pld_U[1].v
if not (__pld_R[0] == false) then __pld_pc = 19 else __pld_pc = 20 end
elseif __pld_pc == 19 then
__pld_pc = 64
elseif __pld_pc == 20 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 28 else __pld_pc = 29 end
elseif __pld_pc == 28 then
__pld_pc = 36
elseif __pld_pc == 29 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 0
__pld_pc = 36
elseif __pld_pc == 36 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] - 1
if not (__pld_R[0] < 1) then __pld_pc = 39 else __pld_pc = 40 end
elseif __pld_pc == 39 then
__pld_pc = 43
elseif __pld_pc == 40 then
__pld_R[0] = 22
if __pld_R[0] then __pld_pc = 42 else __pld_pc = 43 end
elseif __pld_pc == 42 then
__pld_pc = 45
elseif __pld_pc == 43 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 45
elseif __pld_pc == 45 then
__pld_U[3].v = __pld_R[0]
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 54 else __pld_pc = 55 end
elseif __pld_pc == 54 then
__pld_pc = 62
elseif __pld_pc == 55 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 1
__pld_pc = 62
elseif __pld_pc == 62 then
__pld_R[0] = true
__pld_U[1].v = __pld_R[0]
__pld_pc = 64
elseif __pld_pc == 64 then
__pld_R[0] = pressButton
__pld_R[1] = "DOWN"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 68 else __pld_pc = 69 end
elseif __pld_pc == 68 then
__pld_pc = 116
elseif __pld_pc == 69 then
__pld_R[0] = __pld_U[1].v
if not (__pld_R[0] == false) then __pld_pc = 71 else __pld_pc = 72 end
elseif __pld_pc == 71 then
__pld_pc = 116
elseif __pld_pc == 72 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 80 else __pld_pc = 81 end
elseif __pld_pc == 80 then
__pld_pc = 88
elseif __pld_pc == 81 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 0
__pld_pc = 88
elseif __pld_pc == 88 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] + 1
if not (22 < __pld_R[0]) then __pld_pc = 91 else __pld_pc = 92 end
elseif __pld_pc == 91 then
__pld_pc = 95
elseif __pld_pc == 92 then
__pld_R[0] = 1
if __pld_R[0] then __pld_pc = 94 else __pld_pc = 95 end
elseif __pld_pc == 94 then
__pld_pc = 97
elseif __pld_pc == 95 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 97
elseif __pld_pc == 97 then
__pld_U[3].v = __pld_R[0]
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 106 else __pld_pc = 107 end
elseif __pld_pc == 106 then
__pld_pc = 114
elseif __pld_pc == 107 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 1
__pld_pc = 114
elseif __pld_pc == 114 then
__pld_R[0] = true
__pld_U[1].v = __pld_R[0]
__pld_pc = 116
elseif __pld_pc == 116 then
__pld_R[0] = pressButton
__pld_R[1] = "RIGHT"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 120 else __pld_pc = 121 end
elseif __pld_pc == 120 then
__pld_pc = 179
elseif __pld_pc == 121 then
__pld_R[0] = __pld_U[1].v
if not (__pld_R[0] == false) then __pld_pc = 123 else __pld_pc = 124 end
elseif __pld_pc == 123 then
__pld_pc = 179
elseif __pld_pc == 124 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 132 else __pld_pc = 133 end
elseif __pld_pc == 132 then
__pld_pc = 140
elseif __pld_pc == 133 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 0
__pld_pc = 140
elseif __pld_pc == 140 then
__pld_R[0] = __pld_U[3].v
if __pld_R[0] == 21 then __pld_pc = 142 else __pld_pc = 143 end
elseif __pld_pc == 142 then
__pld_pc = 146
elseif __pld_pc == 143 then
__pld_R[0] = __pld_U[3].v
if not (__pld_R[0] == 22) then __pld_pc = 145 else __pld_pc = 146 end
elseif __pld_pc == 145 then
__pld_pc = 150
elseif __pld_pc == 146 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] - 20
__pld_U[3].v = __pld_R[0]
__pld_pc = 161
elseif __pld_pc == 150 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] + 10
if not (22 < __pld_R[0]) then __pld_pc = 153 else __pld_pc = 154 end
elseif __pld_pc == 153 then
__pld_pc = 158
elseif __pld_pc == 154 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] - 10
if __pld_R[0] then __pld_pc = 157 else __pld_pc = 158 end
elseif __pld_pc == 157 then
__pld_pc = 160
elseif __pld_pc == 158 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] + 10
__pld_pc = 160
elseif __pld_pc == 160 then
__pld_U[3].v = __pld_R[0]
__pld_pc = 161
elseif __pld_pc == 161 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 169 else __pld_pc = 170 end
elseif __pld_pc == 169 then
__pld_pc = 177
elseif __pld_pc == 170 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 1
__pld_pc = 177
elseif __pld_pc == 177 then
__pld_R[0] = true
__pld_U[1].v = __pld_R[0]
__pld_pc = 179
elseif __pld_pc == 179 then
__pld_R[0] = pressButton
__pld_R[1] = "LEFT"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 183 else __pld_pc = 184 end
elseif __pld_pc == 183 then
__pld_pc = 242
elseif __pld_pc == 184 then
__pld_R[0] = __pld_U[1].v
if not (__pld_R[0] == false) then __pld_pc = 186 else __pld_pc = 187 end
elseif __pld_pc == 186 then
__pld_pc = 242
elseif __pld_pc == 187 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 195 else __pld_pc = 196 end
elseif __pld_pc == 195 then
__pld_pc = 203
elseif __pld_pc == 196 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 0
__pld_pc = 203
elseif __pld_pc == 203 then
__pld_R[0] = __pld_U[3].v
if __pld_R[0] == 1 then __pld_pc = 205 else __pld_pc = 206 end
elseif __pld_pc == 205 then
__pld_pc = 209
elseif __pld_pc == 206 then
__pld_R[0] = __pld_U[3].v
if not (__pld_R[0] == 2) then __pld_pc = 208 else __pld_pc = 209 end
elseif __pld_pc == 208 then
__pld_pc = 213
elseif __pld_pc == 209 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] + 20
__pld_U[3].v = __pld_R[0]
__pld_pc = 224
elseif __pld_pc == 213 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] - 10
if not (__pld_R[0] < 1) then __pld_pc = 216 else __pld_pc = 217 end
elseif __pld_pc == 216 then
__pld_pc = 221
elseif __pld_pc == 217 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] + 10
if __pld_R[0] then __pld_pc = 220 else __pld_pc = 221 end
elseif __pld_pc == 220 then
__pld_pc = 223
elseif __pld_pc == 221 then
__pld_R[0] = __pld_U[3].v
__pld_R[0] = __pld_R[0] - 10
__pld_pc = 223
elseif __pld_pc == 223 then
__pld_U[3].v = __pld_R[0]
__pld_pc = 224
elseif __pld_pc == 224 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if __pld_R[0] == 2 then __pld_pc = 232 else __pld_pc = 233 end
elseif __pld_pc == 232 then
__pld_pc = 240
elseif __pld_pc == 233 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 1
__pld_pc = 240
elseif __pld_pc == 240 then
__pld_R[0] = true
__pld_U[1].v = __pld_R[0]
__pld_pc = 242
elseif __pld_pc == 242 then
__pld_R[0] = pressButton
__pld_R[1] = "CIRCLE"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 246 else __pld_pc = 247 end
elseif __pld_pc == 246 then
__pld_pc = 310
elseif __pld_pc == 247 then
__pld_R[0] = __pld_U[1].v
if not (__pld_R[0] == false) then __pld_pc = 249 else __pld_pc = 250 end
elseif __pld_pc == 249 then
__pld_pc = 310
elseif __pld_pc == 250 then
__pld_R[0] = __pld_U[3].v
__pld_R[1] = __pld_U[4].v
if __pld_R[0] == __pld_R[1] then __pld_pc = 253 else __pld_pc = 254 end
elseif __pld_pc == 253 then
__pld_pc = 292
elseif __pld_pc == 254 then
__pld_R[0] = stopBGM
__pld_R[1] = 0
__pld_R[2] = 0
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = __pld_U[4].v
if __pld_R[0] == "" then __pld_pc = 260 else __pld_pc = 261 end
elseif __pld_pc == 260 then
__pld_pc = 268
elseif __pld_pc == 261 then
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[4].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 0
__pld_pc = 268
elseif __pld_pc == 268 then
__pld_R[0] = playBGM
__pld_R[1] = 0
__pld_R[2] = cGetFileName
__pld_R[3] = "bgm"
__pld_R[4] = __pld_U[2].v
__pld_R[4] = __pld_R[4]["musicName"]
__pld_R[5] = __pld_U[2].v
__pld_R[5] = __pld_R[5]["musicTitle"]
__pld_R[6] = __pld_U[3].v
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[2] = __pld_R[2](__pld_R[3], __pld_R[4])
__pld_R[3] = true
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
__pld_R[0] = __pld_U[3].v
__pld_U[4].v = __pld_R[0]
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 2
__pld_pc = 305
elseif __pld_pc == 292 then
__pld_R[0] = stopBGM
__pld_R[1] = 0
__pld_R[2] = 30
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = __pld_U[2].v
__pld_R[0] = __pld_R[0]["selectFlag"]
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[0][__pld_R[1]] = 1
__pld_R[0] = ""
__pld_U[4].v = __pld_R[0]
__pld_pc = 305
elseif __pld_pc == 305 then
__pld_R[0] = true
__pld_U[1].v = __pld_R[0]
__pld_R[0] = wait
__pld_R[1] = 3
__pld_R[0](__pld_R[1])
__pld_pc = 310
elseif __pld_pc == 310 then
__pld_R[0] = pressButton
__pld_R[1] = "CROSS"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 314 else __pld_pc = 315 end
elseif __pld_pc == 314 then
__pld_pc = 355
elseif __pld_pc == 315 then
__pld_R[0] = __pld_U[1].v
if not (__pld_R[0] == false) then __pld_pc = 317 else __pld_pc = 318 end
elseif __pld_pc == 317 then
__pld_pc = 355
elseif __pld_pc == 318 then
__pld_R[0] = ""
__pld_R[1] = pairs
__pld_R[2] = __pld_U[2].v
__pld_R[2] = __pld_R[2]["selectFlag"]
__pld_R[1], __pld_R[2], __pld_R[3] = __pld_R[1](__pld_R[2])
__pld_pc = 328
elseif __pld_pc == 324 then
if not (__pld_R[5] == 2) then __pld_pc = 325 else __pld_pc = 326 end
elseif __pld_pc == 325 then
__pld_pc = 328
elseif __pld_pc == 326 then
__pld_R[0] = __pld_R[4]
__pld_pc = 330
elseif __pld_pc == 328 then
__pld_R[4], __pld_R[5] = __pld_R[1](__pld_R[2], __pld_R[3])
if __pld_R[4] ~= nil then __pld_R[3] = __pld_R[4] __pld_pc = 329 else __pld_pc = 330 end
elseif __pld_pc == 329 then
__pld_pc = 324
elseif __pld_pc == 330 then
if __pld_R[0] == "" then __pld_pc = 331 else __pld_pc = 332 end
elseif __pld_pc == 331 then
__pld_pc = 369
elseif __pld_pc == 332 then
__pld_R[1] = stopBGM
__pld_R[2] = 0
__pld_R[3] = 30
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["musicTitle"]
__pld_R[2] = __pld_U[3].v
__pld_R[1] = __pld_R[1][__pld_R[2]]
if not (__pld_R[1] == __pld_R[0]) then __pld_pc = 341 else __pld_pc = 342 end
elseif __pld_pc == 341 then
__pld_pc = 346
elseif __pld_pc == 342 then
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["selectFlag"]
__pld_R[1][__pld_R[0]] = 1
__pld_pc = 349
elseif __pld_pc == 346 then
__pld_R[1] = __pld_U[2].v
__pld_R[1] = __pld_R[1]["selectFlag"]
__pld_R[1][__pld_R[0]] = 0
__pld_pc = 349
elseif __pld_pc == 349 then
__pld_R[1] = ""
__pld_U[4].v = __pld_R[1]
__pld_R[1] = true
__pld_U[1].v = __pld_R[1]
__pld_pc = 355
elseif __pld_pc == 354 then
__pld_pc = 369
elseif __pld_pc == 355 then
__pld_R[0] = __pld_U[1].v
if not (__pld_R[0] == true) then __pld_pc = 357 else __pld_pc = 358 end
elseif __pld_pc == 357 then
__pld_pc = 365
elseif __pld_pc == 358 then
__pld_R[0] = __pld_U[5].v
__pld_R[0]()
__pld_R[0] = false
__pld_U[1].v = __pld_R[0]
__pld_R[0] = wait
__pld_R[1] = 3
__pld_R[0](__pld_R[1])
__pld_pc = 365
elseif __pld_pc == 365 then
__pld_R[0] = wait
__pld_R[1] = 2
__pld_R[0](__pld_R[1])
__pld_pc = 12
elseif __pld_pc == 369 then
__pld_R[0] = __pld_U[6].v
__pld_R[0]()
__pld_R[0] = run
__pld_R[1] = cGetFileName
__pld_R[2] = "script"
__pld_R[3] = "snr_mainmenu"
do 
local __pld_rs = __pld_pack(__pld_R[1](__pld_R[2], __pld_R[3]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 1 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 1 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 1 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 1 + __pld_i - 1) end __pld_R[0](__pld_unpack(__pld_t, 1, __pld_n)) end
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main"] = function(__pld_U)
return function(...)
local __pld_R, __pld_B, __pld_top = {}, {[0]=true, [1]=true, [2]=true, [3]=true, [4]=true, [5]=true, [6]=true}, 0
__pld_R[0] = {}
__pld_R[1] = {}
__pld_R[2] = {}
__pld_R[3] = {}
__pld_R[4] = {}
__pld_R[5] = {}
__pld_R[6] = {}
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0].v = {}
__pld_R[1].v = {}
__pld_R[1].v["bg"] = 0
__pld_R[1].v["music_select"] = 50
__pld_R[1].v["music_off"] = 51
__pld_R[1].v["music_on"] = 52
__pld_R[0].v["layerName"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[2].v = "music_01_a"
__pld_R[3].v = "music_02_a"
__pld_R[4].v = "music_03_a"
__pld_R[5].v = "music_04_a"
__pld_R[6].v = "music_05_a"
__pld_R[7] = "music_06_a"
__pld_R[8] = "music_07_a"
__pld_R[9] = "music_08_a"
__pld_R[10] = "music_09_a"
__pld_R[11] = "music_10_a"
__pld_R[12] = "music_11_a"
__pld_R[13] = "music_12_a"
__pld_R[14] = "music_13_a"
__pld_R[15] = "music_14_a"
__pld_R[16] = "music_15_a"
__pld_R[17] = "music_16_a"
__pld_R[18] = "music_17_a"
__pld_R[19] = "music_18_a"
__pld_R[20] = "music_19_a"
__pld_R[21] = "music_20_a"
__pld_R[22] = "music_21_a"
__pld_R[23] = "music_22_a"
__pld_R[1].v[1] = __pld_R[2].v
__pld_R[1].v[2] = __pld_R[3].v
__pld_R[1].v[3] = __pld_R[4].v
__pld_R[1].v[4] = __pld_R[5].v
__pld_R[1].v[5] = __pld_R[6].v
__pld_R[1].v[6] = __pld_R[7]
__pld_R[1].v[7] = __pld_R[8]
__pld_R[1].v[8] = __pld_R[9]
__pld_R[1].v[9] = __pld_R[10]
__pld_R[1].v[10] = __pld_R[11]
__pld_R[1].v[11] = __pld_R[12]
__pld_R[1].v[12] = __pld_R[13]
__pld_R[1].v[13] = __pld_R[14]
__pld_R[1].v[14] = __pld_R[15]
__pld_R[1].v[15] = __pld_R[16]
__pld_R[1].v[16] = __pld_R[17]
__pld_R[1].v[17] = __pld_R[18]
__pld_R[1].v[18] = __pld_R[19]
__pld_R[1].v[19] = __pld_R[20]
__pld_R[1].v[20] = __pld_R[21]
__pld_R[1].v[21] = __pld_R[22]
__pld_R[1].v[22] = __pld_R[23]
__pld_R[0].v["musicTitle"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[1].v["music_01_a"] = 1
__pld_R[1].v["music_02_a"] = 0
__pld_R[1].v["music_03_a"] = 0
__pld_R[1].v["music_04_a"] = 0
__pld_R[1].v["music_05_a"] = 0
__pld_R[1].v["music_06_a"] = 0
__pld_R[1].v["music_07_a"] = 0
__pld_R[1].v["music_08_a"] = 0
__pld_R[1].v["music_09_a"] = 0
__pld_R[1].v["music_10_a"] = 0
__pld_R[1].v["music_11_a"] = 0
__pld_R[1].v["music_12_a"] = 0
__pld_R[1].v["music_13_a"] = 0
__pld_R[1].v["music_14_a"] = 0
__pld_R[1].v["music_15_a"] = 0
__pld_R[1].v["music_16_a"] = 0
__pld_R[1].v["music_17_a"] = 0
__pld_R[1].v["music_18_a"] = 0
__pld_R[1].v["music_19_a"] = 0
__pld_R[1].v["music_20_a"] = 0
__pld_R[1].v["music_21_a"] = 0
__pld_R[1].v["music_22_a"] = 0
__pld_R[0].v["selectFlag"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[1].v["music_01_a"] = "bgm_1_x"
__pld_R[1].v["music_02_a"] = "bgm_2_x"
__pld_R[1].v["music_03_a"] = "bgm_3_x"
__pld_R[1].v["music_04_a"] = "bgm_4_x"
__pld_R[1].v["music_05_a"] = "bgm_5_x"
__pld_R[1].v["music_06_a"] = "bgm_6_x"
__pld_R[1].v["music_07_a"] = "bgm_7_x"
__pld_R[1].v["music_08_a"] = "bgm_8_x"
__pld_R[1].v["music_09_a"] = "bgm_9_x"
__pld_R[1].v["music_10_a"] = "bgm_10_x"
__pld_R[1].v["music_11_a"] = "bgm_11_x"
__pld_R[1].v["music_12_a"] = "bgm_12_x"
__pld_R[1].v["music_13_a"] = "bgm_13_x"
__pld_R[1].v["music_14_a"] = "bgm_14_x"
__pld_R[1].v["music_15_a"] = "bgm_15_x"
__pld_R[1].v["music_16_a"] = "bgm_16_x"
__pld_R[1].v["music_17_a"] = "bgm_17_x"
__pld_R[1].v["music_18_a"] = "bgm_18_x"
__pld_R[1].v["music_19_a"] = "bgm_19_x"
__pld_R[1].v["music_20_a"] = "bgm_20_a"
__pld_R[1].v["music_21_a"] = "op_zansho_short"
__pld_R[1].v["music_22_a"] = "ed_bl_short"
__pld_R[0].v["musicName"] = __pld_R[1].v
__pld_R[1].v = false
__pld_R[2].v = 1
__pld_R[3].v = ""
__pld_R[4].v = __pld_F["main_0"]({[0]=__pld_R[0]})
__pld_R[5].v = __pld_F["main_1"]({[0]=__pld_R[0], [1]=__pld_R[4]})
__pld_R[6].v = __pld_F["main_2"]({})
__pld_R[7] = __pld_F["main_3"]({[0]=__pld_R[5], [1]=__pld_R[1], [2]=__pld_R[0], [3]=__pld_R[2], [4]=__pld_R[3], [5]=__pld_R[4], [6]=__pld_R[6]})
main = __pld_R[7]
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
return __pld_F["main"]({})(...)

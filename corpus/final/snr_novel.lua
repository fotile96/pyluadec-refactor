local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_F = {}
__pld_F["main_0"] = function(__pld_U)
return function(__pld_p0, __pld_p1, __pld_p2, __pld_p3)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
__pld_R[2] = __pld_p2
__pld_R[3] = __pld_p3
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[4] = 1
__pld_R[5] = string
__pld_R[5] = __pld_R[5]["len"]
__pld_R[6] = __pld_R[3]
__pld_R[5] = __pld_R[5](__pld_R[6])
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 38
elseif __pld_pc == 8 then
__pld_R[8] = string
__pld_R[8] = __pld_R[8]["sub"]
__pld_R[9] = __pld_R[3]
__pld_R[10] = __pld_R[7]
__pld_R[11] = __pld_R[7]
__pld_R[8] = __pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_R[9] = layerCopy
__pld_R[10] = __pld_R[0] + __pld_R[7]
__pld_R[10] = __pld_R[10] - 1
__pld_R[11] = __pld_U[0].v
__pld_R[11] = __pld_R[11]["layerNumber"]
__pld_R[11] = __pld_R[11]["novel_4_c"]
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerPosition
__pld_R[10] = __pld_R[0] + __pld_R[7]
__pld_R[10] = __pld_R[10] - 1
__pld_R[11] = __pld_R[1]
__pld_R[12] = __pld_R[7] - 1
__pld_R[12] = 7 * __pld_R[12]
__pld_R[12] = __pld_R[2] + __pld_R[12]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12])
__pld_R[9] = layerClip
__pld_R[10] = __pld_R[0] + __pld_R[7]
__pld_R[10] = __pld_R[10] - 1
__pld_R[11] = __pld_R[8] * 7
__pld_R[12] = 0
__pld_R[13] = __pld_R[8] + 1
__pld_R[13] = __pld_R[13] * 7
__pld_R[14] = 7
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12], __pld_R[13], __pld_R[14])
__pld_pc = 38
elseif __pld_pc == 38 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 8
else __pld_pc = 39 end end
elseif __pld_pc == 39 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_1"] = function(__pld_U)
return function(__pld_p0, __pld_p1, __pld_p2, __pld_p3)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
__pld_R[2] = __pld_p2
__pld_R[3] = __pld_p3
local __pld_pc = 1
while true do
if __pld_pc == 1 then
if not (__pld_R[3] < 10) then __pld_pc = 2 else __pld_pc = 3 end
elseif __pld_pc == 2 then
__pld_pc = 7
elseif __pld_pc == 3 then
__pld_R[4] = "00"
__pld_R[5] = __pld_R[3]
__pld_R[3] = __pld_R[4] .. __pld_R[5]
__pld_pc = 12
elseif __pld_pc == 7 then
if not (__pld_R[3] < 100) then __pld_pc = 8 else __pld_pc = 9 end
elseif __pld_pc == 8 then
__pld_pc = 12
elseif __pld_pc == 9 then
__pld_R[4] = "0"
__pld_R[5] = __pld_R[3]
__pld_R[3] = __pld_R[4] .. __pld_R[5]
__pld_pc = 12
elseif __pld_pc == 12 then
__pld_R[4] = 1
__pld_R[5] = string
__pld_R[5] = __pld_R[5]["len"]
__pld_R[6] = __pld_R[3]
__pld_R[5] = __pld_R[5](__pld_R[6])
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 49
elseif __pld_pc == 19 then
__pld_R[8] = string
__pld_R[8] = __pld_R[8]["sub"]
__pld_R[9] = __pld_R[3]
__pld_R[10] = __pld_R[7]
__pld_R[11] = __pld_R[7]
__pld_R[8] = __pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_R[9] = layerCopy
__pld_R[10] = __pld_R[0] + __pld_R[7]
__pld_R[10] = __pld_R[10] - 1
__pld_R[11] = __pld_U[0].v
__pld_R[11] = __pld_R[11]["layerNumber"]
__pld_R[11] = __pld_R[11]["novel_4_d"]
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerPosition
__pld_R[10] = __pld_R[0] + __pld_R[7]
__pld_R[10] = __pld_R[10] - 1
__pld_R[11] = __pld_R[1]
__pld_R[12] = __pld_R[7] - 1
__pld_R[12] = 7 * __pld_R[12]
__pld_R[12] = __pld_R[2] + __pld_R[12]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12])
__pld_R[9] = layerClip
__pld_R[10] = __pld_R[0] + __pld_R[7]
__pld_R[10] = __pld_R[10] - 1
__pld_R[11] = __pld_R[8] * 7
__pld_R[12] = 0
__pld_R[13] = __pld_R[8] + 1
__pld_R[13] = __pld_R[13] * 7
__pld_R[14] = 7
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12], __pld_R[13], __pld_R[14])
__pld_pc = 49
elseif __pld_pc == 49 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 19
else __pld_pc = 50 end end
elseif __pld_pc == 50 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_2"] = function(__pld_U)
return function(__pld_p0)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[1] = layerCopy
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["icon"]
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["layerNumber"]
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["layerName"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["t_novelFlag"]
__pld_R[5] = __pld_R[5][__pld_R[0]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[5] = "b"
__pld_R[4] = __pld_R[4] .. __pld_R[5]
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = layerPosition
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["icon"]
__pld_R[3] = 52
__pld_R[4] = 189
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[1] = layerCopy
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["icon"]
__pld_R[2] = __pld_R[2] + 2
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["layerNumber"]
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["layerName"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["t_novelFlag"]
__pld_R[6] = __pld_R[0] - 1
if not (__pld_R[6] < 1) then __pld_pc = 37 else __pld_pc = 38 end
elseif __pld_pc == 37 then
__pld_pc = 43
elseif __pld_pc == 38 then
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = #(__pld_R[6])
if __pld_R[6] then __pld_pc = 42 else __pld_pc = 43 end
elseif __pld_pc == 42 then
__pld_pc = 44
elseif __pld_pc == 43 then
__pld_R[6] = __pld_R[0] - 1
__pld_pc = 44
elseif __pld_pc == 44 then
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[5] = "b"
__pld_R[4] = __pld_R[4] .. __pld_R[5]
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = layerPosition
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["icon"]
__pld_R[2] = __pld_R[2] + 2
__pld_R[3] = 52
__pld_R[4] = 222
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[1] = layerCopy
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["icon"]
__pld_R[2] = __pld_R[2] + 1
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["layerNumber"]
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["layerName"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["t_novelFlag"]
__pld_R[6] = __pld_R[0] + 1
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["t_novelFlag"]
__pld_R[7] = #(__pld_R[7])
if not (__pld_R[7] < __pld_R[6]) then __pld_pc = 74 else __pld_pc = 75 end
elseif __pld_pc == 74 then
__pld_pc = 78
elseif __pld_pc == 75 then
__pld_R[6] = 1
if __pld_R[6] then __pld_pc = 77 else __pld_pc = 78 end
elseif __pld_pc == 77 then
__pld_pc = 79
elseif __pld_pc == 78 then
__pld_R[6] = __pld_R[0] + 1
__pld_pc = 79
elseif __pld_pc == 79 then
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[5] = "b"
__pld_R[4] = __pld_R[4] .. __pld_R[5]
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = layerPosition
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["icon"]
__pld_R[2] = __pld_R[2] + 1
__pld_R[3] = 52
__pld_R[4] = 158
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4])
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_3"] = function(__pld_U)
return function(__pld_p0, __pld_p1, __pld_p2)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
__pld_R[2] = __pld_p2
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["indexNumber"]
__pld_R[3] = __pld_R[3]["icon"]
__pld_R[3] = __pld_R[3] + 3
if not (__pld_R[2] == "down") then __pld_pc = 6 else __pld_pc = 7 end
elseif __pld_pc == 6 then
__pld_pc = 183
elseif __pld_pc == 7 then
__pld_R[4] = layerCopy
__pld_R[5] = __pld_R[3]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["indexNumber"]
__pld_R[6] = __pld_R[6]["icon"]
__pld_R[6] = __pld_R[6] + 1
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_R[3]
__pld_R[6] = 52
__pld_R[7] = 158
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerScale
__pld_R[5] = __pld_R[3]
__pld_R[6] = 100
__pld_R[7] = 100
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerMoveScale
__pld_R[5] = __pld_R[3]
__pld_R[6] = 100
__pld_R[7] = 0
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_R[3]
__pld_R[6] = 52
__pld_R[7] = 142
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerCopy
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerNumber"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[8] = __pld_R[8][__pld_R[0]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[8] = "b"
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[6] = 52
__pld_R[7] = 222
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[6] = 52
__pld_R[7] = 189
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerCopy
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerNumber"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[8] = __pld_R[8][__pld_R[1]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[8] = "b"
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = 52
__pld_R[7] = 189
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = 52
__pld_R[7] = 158
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerCopy
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerNumber"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[9] = __pld_R[0] - 1
if not (__pld_R[9] < 1) then __pld_pc = 114 else __pld_pc = 115 end
elseif __pld_pc == 114 then
__pld_pc = 120
elseif __pld_pc == 115 then
__pld_R[9] = __pld_U[0].v
__pld_R[9] = __pld_R[9]["t_novelFlag"]
__pld_R[9] = #(__pld_R[9])
if __pld_R[9] then __pld_pc = 119 else __pld_pc = 120 end
elseif __pld_pc == 119 then
__pld_pc = 121
elseif __pld_pc == 120 then
__pld_R[9] = __pld_R[0] - 1
__pld_pc = 121
elseif __pld_pc == 121 then
__pld_R[8] = __pld_R[8][__pld_R[9]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[8] = "b"
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 52
__pld_R[7] = 235
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerScale
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 100
__pld_R[7] = 0
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerClip
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 0
__pld_R[7] = 0
__pld_R[8] = 55
__pld_R[9] = 26
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8], __pld_R[9])
__pld_R[4] = layerMoveClip
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 0
__pld_R[7] = 0
__pld_R[8] = 55
__pld_R[9] = 33
__pld_R[10] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8], __pld_R[9], __pld_R[10])
__pld_R[4] = layerMoveScale
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 100
__pld_R[7] = 100
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 52
__pld_R[7] = 222
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_pc = 348
elseif __pld_pc == 183 then
if not (__pld_R[2] == "up") then __pld_pc = 184 else __pld_pc = 185 end
elseif __pld_pc == 184 then
__pld_pc = 348
elseif __pld_pc == 185 then
__pld_R[4] = layerCopy
__pld_R[5] = __pld_R[3]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["indexNumber"]
__pld_R[6] = __pld_R[6]["icon"]
__pld_R[6] = __pld_R[6] + 2
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_R[3]
__pld_R[6] = 52
__pld_R[7] = 222
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerScale
__pld_R[5] = __pld_R[3]
__pld_R[6] = 100
__pld_R[7] = 100
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerMoveClip
__pld_R[5] = __pld_R[3]
__pld_R[6] = 0
__pld_R[7] = 0
__pld_R[8] = 55
__pld_R[9] = 26
__pld_R[10] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8], __pld_R[9], __pld_R[10])
__pld_R[4] = layerMoveScale
__pld_R[5] = __pld_R[3]
__pld_R[6] = 100
__pld_R[7] = 0
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_R[3]
__pld_R[6] = 52
__pld_R[7] = 235
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerCopy
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerNumber"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[8] = __pld_R[8][__pld_R[0]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[8] = "b"
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[6] = 52
__pld_R[7] = 158
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[6] = 52
__pld_R[7] = 189
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerCopy
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerNumber"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[9] = __pld_R[0] + 1
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["t_novelFlag"]
__pld_R[10] = #(__pld_R[10])
if not (__pld_R[10] < __pld_R[9]) then __pld_pc = 269 else __pld_pc = 270 end
elseif __pld_pc == 269 then
__pld_pc = 273
elseif __pld_pc == 270 then
__pld_R[9] = 1
if __pld_R[9] then __pld_pc = 272 else __pld_pc = 273 end
elseif __pld_pc == 272 then
__pld_pc = 274
elseif __pld_pc == 273 then
__pld_R[9] = __pld_R[0] + 1
__pld_pc = 274
elseif __pld_pc == 274 then
__pld_R[8] = __pld_R[8][__pld_R[9]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[8] = "b"
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = 52
__pld_R[7] = 142
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerScale
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = 100
__pld_R[7] = 0
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerMoveScale
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = 100
__pld_R[7] = 100
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 1
__pld_R[6] = 52
__pld_R[7] = 158
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[4] = layerCopy
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerNumber"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["layerName"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[8] = __pld_R[8][__pld_R[1]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[8] = "b"
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = layerPosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 52
__pld_R[7] = 189
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = layerMovePosition
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["indexNumber"]
__pld_R[5] = __pld_R[5]["icon"]
__pld_R[5] = __pld_R[5] + 2
__pld_R[6] = 52
__pld_R[7] = 222
__pld_R[8] = 30
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_pc = 348
elseif __pld_pc == 348 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_4"] = function(__pld_U)
return function(__pld_p0, __pld_p1, __pld_p2)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
__pld_R[2] = __pld_p2
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[3] = layerCopy
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[4] = __pld_R[4] + 1
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerName"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["t_novelFlag"]
__pld_R[7] = __pld_R[7][__pld_R[1]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[7] = "a"
__pld_R[6] = __pld_R[6] .. __pld_R[7]
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerCopy
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerName"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["t_novelFlag"]
__pld_R[7] = __pld_R[7][__pld_R[0]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[7] = "a"
__pld_R[6] = __pld_R[6] .. __pld_R[7]
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[3](__pld_R[4], __pld_R[5])
if not (__pld_R[2] == "down") then __pld_pc = 35 else __pld_pc = 36 end
elseif __pld_pc == 35 then
__pld_pc = 53
elseif __pld_pc == 36 then
__pld_R[3] = layerPosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[5] = 0
__pld_R[6] = 270
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[3] = layerMovePosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[4] = __pld_R[4] + 1
__pld_R[5] = 0
__pld_R[6] = (-270)
__pld_R[7] = 30
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 71
elseif __pld_pc == 53 then
if not (__pld_R[2] == "up") then __pld_pc = 54 else __pld_pc = 55 end
elseif __pld_pc == 54 then
__pld_pc = 71
elseif __pld_pc == 55 then
__pld_R[3] = layerPosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[5] = 0
__pld_R[6] = (-270)
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[3] = layerMovePosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[4] = __pld_R[4] + 1
__pld_R[5] = 0
__pld_R[6] = 270
__pld_R[7] = 30
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 71
elseif __pld_pc == 71 then
__pld_R[3] = layerMovePosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[5] = 0
__pld_R[6] = 0
__pld_R[7] = 30
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[3] = __pld_U[1].v
__pld_R[4] = __pld_R[0]
__pld_R[5] = __pld_R[1]
__pld_R[6] = __pld_R[2]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[3] = layerCopy
__pld_R[4] = 10
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["novel_4_b"]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerClip
__pld_R[4] = 10
__pld_R[5] = 0
__pld_R[6] = 0
__pld_R[7] = 7
__pld_R[8] = 61
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[3] = layerPosition
__pld_R[4] = 10
__pld_R[5] = 115
__pld_R[6] = 205
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[3] = systemSave
__pld_R[3] = __pld_R[3]["bookMark"]
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["t_novelFlag"]
__pld_R[4] = __pld_R[4][__pld_R[0]]
__pld_R[3] = __pld_R[3][__pld_R[4]]
if __pld_R[3] == 0 then __pld_pc = 109 else __pld_pc = 110 end
elseif __pld_pc == 109 then
__pld_pc = 122
elseif __pld_pc == 110 then
__pld_R[3] = __pld_U[2].v
__pld_R[4] = 11
__pld_R[5] = 115
__pld_R[6] = 250
__pld_R[7] = systemSave
__pld_R[7] = __pld_R[7]["bookMark"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[8] = __pld_R[8][__pld_R[0]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 141
elseif __pld_pc == 122 then
__pld_R[3] = layerLoad
__pld_R[4] = 11
__pld_R[5] = ""
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerLoad
__pld_R[4] = 12
__pld_R[5] = ""
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerLoad
__pld_R[4] = 13
__pld_R[5] = ""
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerClip
__pld_R[4] = 10
__pld_R[5] = 7
__pld_R[6] = 0
__pld_R[7] = 14
__pld_R[8] = 61
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_pc = 141
elseif __pld_pc == 141 then
__pld_R[3] = wait
__pld_R[4] = 30
__pld_R[3](__pld_R[4])
__pld_R[3] = layerLoad
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["hardCover"]
__pld_R[4] = __pld_R[4] + 1
__pld_R[5] = ""
__pld_R[3](__pld_R[4], __pld_R[5])
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_5"] = function(__pld_U)
return function(__pld_p0)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[1] = layerCopy
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["hardCover"]
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["layerNumber"]
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["layerName"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["t_novelFlag"]
__pld_R[5] = __pld_R[5][__pld_R[0]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[5] = "a"
__pld_R[4] = __pld_R[4] .. __pld_R[5]
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = __pld_U[1].v
__pld_R[2] = __pld_R[0]
__pld_R[1](__pld_R[2])
__pld_R[1] = layerCopy
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["bar"]
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["layerNumber"]
__pld_R[3] = __pld_R[3]["novel_1_a"]
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = layerPosition
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["bar"]
__pld_R[3] = 15
__pld_R[4] = 0
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[1] = layerCopy
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["mask"]
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["layerNumber"]
__pld_R[3] = __pld_R[3]["novel_1_b"]
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = layerPosition
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["indexNumber"]
__pld_R[2] = __pld_R[2]["mask"]
__pld_R[3] = 59
__pld_R[4] = 158
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[1] = __pld_U[2].v
__pld_R[2] = 14
__pld_R[3] = 91
__pld_R[4] = 10
__pld_R[5] = "0"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = #(__pld_R[6])
__pld_R[5] = __pld_R[5] .. __pld_R[6]
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4], __pld_R[5])
__pld_R[1] = __pld_U[2].v
__pld_R[2] = 16
__pld_R[3] = 91
__pld_R[4] = 40
__pld_R[5] = "05"
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4], __pld_R[5])
__pld_R[1] = layerCopy
__pld_R[2] = 10
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["layerNumber"]
__pld_R[3] = __pld_R[3]["novel_4_b"]
__pld_R[1](__pld_R[2], __pld_R[3])
__pld_R[1] = layerClip
__pld_R[2] = 10
__pld_R[3] = 0
__pld_R[4] = 0
__pld_R[5] = 7
__pld_R[6] = 61
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[1] = layerPosition
__pld_R[2] = 10
__pld_R[3] = 115
__pld_R[4] = 205
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[1] = systemSave
__pld_R[1] = __pld_R[1]["bookMark"]
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["t_novelFlag"]
__pld_R[2] = __pld_R[2][__pld_R[0]]
__pld_R[1] = __pld_R[1][__pld_R[2]]
if __pld_R[1] == 0 then __pld_pc = 91 else __pld_pc = 92 end
elseif __pld_pc == 91 then
__pld_pc = 104
elseif __pld_pc == 92 then
__pld_R[1] = __pld_U[3].v
__pld_R[2] = 11
__pld_R[3] = 115
__pld_R[4] = 250
__pld_R[5] = systemSave
__pld_R[5] = __pld_R[5]["bookMark"]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4], __pld_R[5])
__pld_pc = 111
elseif __pld_pc == 104 then
__pld_R[1] = layerClip
__pld_R[2] = 10
__pld_R[3] = 7
__pld_R[4] = 0
__pld_R[5] = 14
__pld_R[6] = 61
__pld_R[1](__pld_R[2], __pld_R[3], __pld_R[4], __pld_R[5], __pld_R[6])
__pld_pc = 111
elseif __pld_pc == 111 then
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
__pld_F["main_6"] = function(__pld_U)
return function()
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = 0
__pld_R[1] = 20
__pld_R[2] = 1
do
local __pld_i = __pld_tonumber(__pld_R[0]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[1]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[2]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[0] = __pld_i - __pld_s __pld_R[1] = __pld_l __pld_R[2] = __pld_s
end
__pld_pc = 9
elseif __pld_pc == 5 then
__pld_R[4] = layerLoad
__pld_R[5] = __pld_R[3]
__pld_R[6] = ""
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 9
elseif __pld_pc == 9 then
do local __pld_s = __pld_R[2] local __pld_i = __pld_R[0] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[1]) or (__pld_s <= 0 and __pld_i >= __pld_R[1]) then
__pld_R[0] = __pld_i __pld_R[3] = __pld_i __pld_pc = 5
else __pld_pc = 10 end end
elseif __pld_pc == 10 then
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
__pld_F["main_7"] = function(__pld_U)
return function(__pld_p0)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
do local __pld_t = __pld_R[0] if __pld_t then __pld_R[1] = __pld_t __pld_pc = 2 else __pld_pc = 3 end end
elseif __pld_pc == 2 then
__pld_pc = 4
elseif __pld_pc == 3 then
__pld_R[1] = 1
__pld_pc = 4
elseif __pld_pc == 4 then
__pld_R[2] = __pld_U[0].v
__pld_R[3] = __pld_R[1]
__pld_R[2](__pld_R[3])
__pld_R[2] = 1
__pld_R[3] = false
__pld_R[4] = ""
__pld_pc = 10
elseif __pld_pc == 10 then
__pld_R[5] = pressButton
__pld_R[6] = "UP"
__pld_R[5] = __pld_R[5](__pld_R[6])
if not (__pld_R[5] == true) then __pld_pc = 14 else __pld_pc = 15 end
elseif __pld_pc == 14 then
__pld_pc = 30
elseif __pld_pc == 15 then
if not (__pld_R[3] == false) then __pld_pc = 16 else __pld_pc = 17 end
elseif __pld_pc == 16 then
__pld_pc = 30
elseif __pld_pc == 17 then
__pld_R[2] = __pld_R[1]
__pld_R[5] = __pld_R[1] + 1
__pld_R[6] = __pld_U[1].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = #(__pld_R[6])
if not (__pld_R[6] < __pld_R[5]) then __pld_pc = 23 else __pld_pc = 24 end
elseif __pld_pc == 23 then
__pld_pc = 27
elseif __pld_pc == 24 then
__pld_R[5] = 1
do local __pld_t = __pld_R[5] if __pld_t then __pld_R[1] = __pld_t __pld_pc = 26 else __pld_pc = 27 end end
elseif __pld_pc == 26 then
__pld_pc = 28
elseif __pld_pc == 27 then
__pld_R[1] = __pld_R[1] + 1
__pld_pc = 28
elseif __pld_pc == 28 then
__pld_R[3] = true
__pld_R[4] = "up"
__pld_pc = 30
elseif __pld_pc == 30 then
__pld_R[5] = pressButton
__pld_R[6] = "DOWN"
__pld_R[5] = __pld_R[5](__pld_R[6])
if not (__pld_R[5] == true) then __pld_pc = 34 else __pld_pc = 35 end
elseif __pld_pc == 34 then
__pld_pc = 49
elseif __pld_pc == 35 then
if not (__pld_R[3] == false) then __pld_pc = 36 else __pld_pc = 37 end
elseif __pld_pc == 36 then
__pld_pc = 49
elseif __pld_pc == 37 then
__pld_R[2] = __pld_R[1]
__pld_R[5] = __pld_R[1] - 1
if not (__pld_R[5] < 1) then __pld_pc = 40 else __pld_pc = 41 end
elseif __pld_pc == 40 then
__pld_pc = 46
elseif __pld_pc == 41 then
__pld_R[5] = __pld_U[1].v
__pld_R[5] = __pld_R[5]["t_novelFlag"]
__pld_R[5] = #(__pld_R[5])
do local __pld_t = __pld_R[5] if __pld_t then __pld_R[1] = __pld_t __pld_pc = 45 else __pld_pc = 46 end end
elseif __pld_pc == 45 then
__pld_pc = 47
elseif __pld_pc == 46 then
__pld_R[1] = __pld_R[1] - 1
__pld_pc = 47
elseif __pld_pc == 47 then
__pld_R[3] = true
__pld_R[4] = "down"
__pld_pc = 49
elseif __pld_pc == 49 then
__pld_R[5] = pressButton
__pld_R[6] = "RIGHT"
__pld_R[5] = __pld_R[5](__pld_R[6])
if not (__pld_R[5] == true) then __pld_pc = 53 else __pld_pc = 54 end
elseif __pld_pc == 53 then
__pld_pc = 63
elseif __pld_pc == 54 then
if not (__pld_R[3] == false) then __pld_pc = 55 else __pld_pc = 56 end
elseif __pld_pc == 55 then
__pld_pc = 63
elseif __pld_pc == 56 then
__pld_R[5] = 2
__pld_U[2].v = __pld_R[5]
__pld_R[5] = keyPlaySE
__pld_R[6] = seName
__pld_R[6] = __pld_R[6]["cross"]
__pld_R[5](__pld_R[6])
__pld_pc = 93
elseif __pld_pc == 63 then
__pld_R[5] = pressButton
__pld_R[6] = "LEFT"
__pld_R[5] = __pld_R[5](__pld_R[6])
if not (__pld_R[5] == true) then __pld_pc = 67 else __pld_pc = 68 end
elseif __pld_pc == 67 then
__pld_pc = 77
elseif __pld_pc == 68 then
if not (__pld_R[3] == false) then __pld_pc = 69 else __pld_pc = 70 end
elseif __pld_pc == 69 then
__pld_pc = 77
elseif __pld_pc == 70 then
__pld_R[5] = keyPlaySE
__pld_R[6] = seName
__pld_R[6] = __pld_R[6]["circle"]
__pld_R[5](__pld_R[6])
__pld_R[5] = 1
__pld_U[2].v = __pld_R[5]
__pld_pc = 93
elseif __pld_pc == 77 then
if not (__pld_R[3] == true) then __pld_pc = 78 else __pld_pc = 79 end
elseif __pld_pc == 78 then
__pld_pc = 89
elseif __pld_pc == 79 then
__pld_R[5] = keyPlaySE
__pld_R[6] = seName
__pld_R[6] = __pld_R[6]["arrowKey"]
__pld_R[5](__pld_R[6])
__pld_R[5] = __pld_U[3].v
__pld_R[6] = __pld_R[1]
__pld_R[7] = __pld_R[2]
__pld_R[8] = __pld_R[4]
__pld_R[5](__pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[3] = false
__pld_pc = 89
elseif __pld_pc == 89 then
__pld_R[5] = wait
__pld_R[6] = 2
__pld_R[5](__pld_R[6])
__pld_pc = 10
elseif __pld_pc == 93 then
__pld_R[5] = __pld_U[4].v
__pld_R[5]()
return __pld_R[1]
elseif __pld_pc == 96 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_8"] = function(__pld_U)
return function(__pld_p0, __pld_p1, __pld_p2)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
__pld_R[2] = __pld_p2
local __pld_pc = 1
while true do
if __pld_pc == 1 then
if not (__pld_R[2] == 1) then __pld_pc = 2 else __pld_pc = 3 end
elseif __pld_pc == 2 then
__pld_pc = 32
elseif __pld_pc == 3 then
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[4] = __pld_R[4] + 4
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] - 2
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[4] = __pld_R[4] + 5
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] + 2
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_pc = 92
elseif __pld_pc == 32 then
if not (__pld_R[2] == 2) then __pld_pc = 33 else __pld_pc = 34 end
elseif __pld_pc == 33 then
__pld_pc = 62
elseif __pld_pc == 34 then
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] - 2
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[4] = __pld_R[4] + 1
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] + 2
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_pc = 92
elseif __pld_pc == 62 then
if not (__pld_R[2] == 3) then __pld_pc = 63 else __pld_pc = 64 end
elseif __pld_pc == 63 then
__pld_pc = 92
elseif __pld_pc == 64 then
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[4] = __pld_R[4] + 2
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] - 2
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[4] = __pld_R[4] + 3
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] + 2
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_pc = 92
elseif __pld_pc == 92 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_9"] = function(__pld_U)
return function(__pld_p0, __pld_p1, __pld_p2)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
__pld_R[2] = __pld_p2
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[3] = layerCopy
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["novelBg"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerName"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["t_novelFlag"]
__pld_R[7] = __pld_R[7][__pld_R[0]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[7] = "d"
__pld_R[6] = __pld_R[6] .. __pld_R[7]
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerCopy
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["novelBar"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["novel_4_a"]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerCopy
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["title"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["layerName"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["t_novelFlag"]
__pld_R[7] = __pld_R[7][__pld_R[0]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[7] = "c"
__pld_R[6] = __pld_R[6] .. __pld_R[7]
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerPosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["title"]
__pld_R[5] = 462
__pld_R[6] = 5
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[3] = layerCopy
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["bookMark"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["novel_4_b"]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = systemSave
__pld_R[3] = __pld_R[3]["bookMark"]
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["novelTitle"]
__pld_R[4] = __pld_R[4][__pld_R[0]]
__pld_R[3] = __pld_R[3][__pld_R[4]]
if not (__pld_R[3] == 0) then __pld_pc = 63 else __pld_pc = 64 end
elseif __pld_pc == 63 then
__pld_pc = 74
elseif __pld_pc == 64 then
__pld_R[3] = layerClip
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["bookMark"]
__pld_R[5] = 7
__pld_R[6] = 0
__pld_R[7] = 14
__pld_R[8] = 61
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_pc = 94
elseif __pld_pc == 74 then
__pld_R[3] = layerClip
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["bookMark"]
__pld_R[5] = 0
__pld_R[6] = 0
__pld_R[7] = 7
__pld_R[8] = 61
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7], __pld_R[8])
__pld_R[3] = __pld_U[1].v
__pld_R[4] = 28
__pld_R[5] = 457
__pld_R[6] = 245
__pld_R[7] = systemSave
__pld_R[7] = __pld_R[7]["bookMark"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[8] = __pld_R[8][__pld_R[0]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 94
elseif __pld_pc == 94 then
__pld_R[3] = layerPosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["bookMark"]
__pld_R[5] = 457
__pld_R[6] = 200
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
if not (__pld_R[1] < 10) then __pld_pc = 102 else __pld_pc = 103 end
elseif __pld_pc == 102 then
__pld_pc = 112
elseif __pld_pc == 103 then
__pld_R[3] = __pld_U[2].v
__pld_R[4] = 14
__pld_R[5] = 470
__pld_R[6] = 205
__pld_R[7] = "00"
__pld_R[8] = __pld_R[1]
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 129
elseif __pld_pc == 112 then
if not (__pld_R[1] < 100) then __pld_pc = 113 else __pld_pc = 114 end
elseif __pld_pc == 113 then
__pld_pc = 123
elseif __pld_pc == 114 then
__pld_R[3] = __pld_U[2].v
__pld_R[4] = 14
__pld_R[5] = 470
__pld_R[6] = 205
__pld_R[7] = "0"
__pld_R[8] = __pld_R[1]
__pld_R[7] = __pld_R[7] .. __pld_R[8]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 129
elseif __pld_pc == 123 then
__pld_R[3] = __pld_U[2].v
__pld_R[4] = 14
__pld_R[5] = 470
__pld_R[6] = 205
__pld_R[7] = __pld_R[1]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 129
elseif __pld_pc == 129 then
__pld_R[3] = __pld_U[2].v
__pld_R[4] = 17
__pld_R[5] = 470
__pld_R[6] = 243
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["novelPageMax"]
__pld_R[8] = __pld_U[0].v
__pld_R[8] = __pld_R[8]["t_novelFlag"]
__pld_R[8] = __pld_R[8][__pld_R[0]]
__pld_R[7] = __pld_R[7][__pld_R[8]]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[3] = layerLoad
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1]
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[4] = __pld_R[4] + 2
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] - 1
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = comLayerLoadFalse
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[4] = __pld_R[4] + 3
__pld_R[5] = "novel/"
__pld_R[6] = __pld_U[0].v
__pld_R[6] = __pld_R[6]["t_novelFlag"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[7] = "_"
__pld_R[8] = __pld_R[1] + 1
__pld_R[9] = ".gim"
__pld_R[5] = __pld_R[5] .. __pld_R[6] .. __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[3](__pld_R[4], __pld_R[5])
__pld_R[3] = layerPosition
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["indexNumber"]
__pld_R[4] = __pld_R[4]["sentence"]
__pld_R[5] = 20
__pld_R[6] = 0
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[3] = __pld_U[3].v
__pld_R[4] = __pld_R[0]
__pld_R[5] = __pld_R[1]
__pld_R[6] = __pld_R[2]
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
__pld_R[3] = switchScreen
__pld_R[4] = 0
__pld_R[5] = ""
__pld_R[6] = 60
__pld_R[3](__pld_R[4], __pld_R[5], __pld_R[6])
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_10"] = function(__pld_U)
return function()
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = 0
__pld_R[1] = 40
__pld_R[2] = 1
do
local __pld_i = __pld_tonumber(__pld_R[0]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[1]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[2]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[0] = __pld_i - __pld_s __pld_R[1] = __pld_l __pld_R[2] = __pld_s
end
__pld_pc = 9
elseif __pld_pc == 5 then
__pld_R[4] = layerLoad
__pld_R[5] = __pld_R[3]
__pld_R[6] = ""
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 9
elseif __pld_pc == 9 then
do local __pld_s = __pld_R[2] local __pld_i = __pld_R[0] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[1]) or (__pld_s <= 0 and __pld_i >= __pld_R[1]) then
__pld_R[0] = __pld_i __pld_R[3] = __pld_i __pld_pc = 5
else __pld_pc = 10 end end
elseif __pld_pc == 10 then
__pld_R[0] = fontClear
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
__pld_F["main_11"] = function(__pld_U)
return function(__pld_p0, __pld_p1)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[2] = systemSave
__pld_R[2] = __pld_R[2]["bookMark"]
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["t_novelFlag"]
__pld_R[3] = __pld_R[3][__pld_R[0]]
__pld_R[2] = __pld_R[2][__pld_R[3]]
if not (__pld_R[2] == __pld_R[1]) then __pld_pc = 8 else __pld_pc = 9 end
elseif __pld_pc == 8 then
__pld_pc = 37
elseif __pld_pc == 9 then
__pld_R[2] = layerLoad
__pld_R[3] = 28
__pld_R[4] = ""
__pld_R[2](__pld_R[3], __pld_R[4])
__pld_R[2] = layerLoad
__pld_R[3] = 29
__pld_R[4] = ""
__pld_R[2](__pld_R[3], __pld_R[4])
__pld_R[2] = layerLoad
__pld_R[3] = 30
__pld_R[4] = ""
__pld_R[2](__pld_R[3], __pld_R[4])
__pld_R[2] = systemSave
__pld_R[2] = __pld_R[2]["bookMark"]
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["t_novelFlag"]
__pld_R[3] = __pld_R[3][__pld_R[0]]
__pld_R[2][__pld_R[3]] = 0
__pld_R[2] = layerClip
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["indexNumber"]
__pld_R[3] = __pld_R[3]["bookMark"]
__pld_R[4] = 7
__pld_R[5] = 0
__pld_R[6] = 14
__pld_R[7] = 61
__pld_R[2](__pld_R[3], __pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_pc = 63
elseif __pld_pc == 37 then
__pld_R[2] = systemSave
__pld_R[2] = __pld_R[2]["bookMark"]
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["t_novelFlag"]
__pld_R[3] = __pld_R[3][__pld_R[0]]
__pld_R[2][__pld_R[3]] = __pld_R[1]
__pld_R[2] = layerClip
__pld_R[3] = __pld_U[0].v
__pld_R[3] = __pld_R[3]["indexNumber"]
__pld_R[3] = __pld_R[3]["bookMark"]
__pld_R[4] = 0
__pld_R[5] = 0
__pld_R[6] = 7
__pld_R[7] = 61
__pld_R[2](__pld_R[3], __pld_R[4], __pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[2] = __pld_U[1].v
__pld_R[3] = 28
__pld_R[4] = 457
__pld_R[5] = 245
__pld_R[6] = systemSave
__pld_R[6] = __pld_R[6]["bookMark"]
__pld_R[7] = __pld_U[0].v
__pld_R[7] = __pld_R[7]["t_novelFlag"]
__pld_R[7] = __pld_R[7][__pld_R[0]]
__pld_R[6] = __pld_R[6][__pld_R[7]]
__pld_R[2](__pld_R[3], __pld_R[4], __pld_R[5], __pld_R[6])
__pld_pc = 63
elseif __pld_pc == 63 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_12"] = function(__pld_U)
return function(__pld_p0)
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[1] = systemSave
__pld_R[1] = __pld_R[1]["bookMark"]
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["t_novelFlag"]
__pld_R[2] = __pld_R[2][__pld_R[0]]
__pld_R[1] = __pld_R[1][__pld_R[2]]
if not (0 < __pld_R[1]) then __pld_pc = 8 else __pld_pc = 9 end
elseif __pld_pc == 8 then
__pld_pc = 17
elseif __pld_pc == 9 then
__pld_R[1] = systemSave
__pld_R[1] = __pld_R[1]["bookMark"]
__pld_R[2] = __pld_U[0].v
__pld_R[2] = __pld_R[2]["t_novelFlag"]
__pld_R[2] = __pld_R[2][__pld_R[0]]
__pld_R[1] = __pld_R[1][__pld_R[2]]
if __pld_R[1] then __pld_pc = 16 else __pld_pc = 17 end
elseif __pld_pc == 16 then
__pld_pc = 18
elseif __pld_pc == 17 then
__pld_R[1] = 1
__pld_pc = 18
elseif __pld_pc == 18 then
__pld_R[2] = 1
__pld_R[3] = false
__pld_R[4] = __pld_U[0].v
__pld_R[4] = __pld_R[4]["novelPageMax"]
__pld_R[5] = __pld_U[0].v
__pld_R[5] = __pld_R[5]["t_novelFlag"]
__pld_R[5] = __pld_R[5][__pld_R[0]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[5] = 1
__pld_R[6] = 1
__pld_R[7] = 1
__pld_R[8] = 1
__pld_R[9] = __pld_U[1].v
__pld_R[10] = __pld_R[0]
__pld_R[11] = __pld_R[1]
__pld_R[12] = __pld_R[8]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12])
__pld_pc = 35
elseif __pld_pc == 35 then
__pld_R[9] = pressButton
__pld_R[10] = "UP"
__pld_R[9] = __pld_R[9](__pld_R[10])
if not (__pld_R[9] == true) then __pld_pc = 39 else __pld_pc = 40 end
elseif __pld_pc == 39 then
__pld_pc = 50
elseif __pld_pc == 40 then
if not (__pld_R[3] == false) then __pld_pc = 41 else __pld_pc = 42 end
elseif __pld_pc == 41 then
__pld_pc = 50
elseif __pld_pc == 42 then
__pld_R[2] = __pld_R[1]
__pld_R[9] = __pld_R[1] + 1
if not (__pld_R[4] < __pld_R[9]) then __pld_pc = 45 else __pld_pc = 46 end
elseif __pld_pc == 45 then
__pld_pc = 48
elseif __pld_pc == 46 then
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[1] = __pld_t __pld_pc = 47 else __pld_pc = 48 end end
elseif __pld_pc == 47 then
__pld_pc = 49
elseif __pld_pc == 48 then
__pld_R[1] = __pld_R[1] + 1
__pld_pc = 49
elseif __pld_pc == 49 then
__pld_R[3] = true
__pld_pc = 50
elseif __pld_pc == 50 then
__pld_R[9] = pressButton
__pld_R[10] = "DOWN"
__pld_R[9] = __pld_R[9](__pld_R[10])
if not (__pld_R[9] == true) then __pld_pc = 54 else __pld_pc = 55 end
elseif __pld_pc == 54 then
__pld_pc = 66
elseif __pld_pc == 55 then
if not (__pld_R[3] == false) then __pld_pc = 56 else __pld_pc = 57 end
elseif __pld_pc == 56 then
__pld_pc = 66
elseif __pld_pc == 57 then
__pld_R[2] = __pld_R[1]
__pld_R[9] = __pld_R[1] - 1
if not (__pld_R[9] < 1) then __pld_pc = 60 else __pld_pc = 61 end
elseif __pld_pc == 60 then
__pld_pc = 64
elseif __pld_pc == 61 then
__pld_R[9] = 1
do local __pld_t = __pld_R[9] if __pld_t then __pld_R[1] = __pld_t __pld_pc = 63 else __pld_pc = 64 end end
elseif __pld_pc == 63 then
__pld_pc = 65
elseif __pld_pc == 64 then
__pld_R[1] = __pld_R[1] - 1
__pld_pc = 65
elseif __pld_pc == 65 then
__pld_R[3] = true
__pld_pc = 66
elseif __pld_pc == 66 then
__pld_R[9] = pressButton
__pld_R[10] = "RIGHT"
__pld_R[9] = __pld_R[9](__pld_R[10])
if not (__pld_R[9] == true) then __pld_pc = 70 else __pld_pc = 71 end
elseif __pld_pc == 70 then
__pld_pc = 80
elseif __pld_pc == 71 then
if not (__pld_R[3] == false) then __pld_pc = 72 else __pld_pc = 73 end
elseif __pld_pc == 72 then
__pld_pc = 80
elseif __pld_pc == 73 then
__pld_R[9] = keyPlaySE
__pld_R[10] = seName
__pld_R[10] = __pld_R[10]["cross"]
__pld_R[9](__pld_R[10])
__pld_R[9] = 0
__pld_U[2].v = __pld_R[9]
__pld_pc = 298
elseif __pld_pc == 80 then
__pld_R[9] = pressButton
__pld_R[10] = "LEFT"
__pld_R[9] = __pld_R[9](__pld_R[10])
if not (__pld_R[9] == true) then __pld_pc = 84 else __pld_pc = 85 end
elseif __pld_pc == 84 then
__pld_pc = 94
elseif __pld_pc == 85 then
if not (__pld_R[3] == false) then __pld_pc = 86 else __pld_pc = 87 end
elseif __pld_pc == 86 then
__pld_pc = 94
elseif __pld_pc == 87 then
__pld_R[9] = __pld_U[3].v
__pld_R[10] = __pld_R[0]
__pld_R[11] = __pld_R[1]
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = wait
__pld_R[10] = 10
__pld_R[9](__pld_R[10])
__pld_pc = 94
elseif __pld_pc == 94 then
if not (__pld_R[3] == true) then __pld_pc = 95 else __pld_pc = 96 end
elseif __pld_pc == 95 then
__pld_pc = 294
elseif __pld_pc == 96 then
__pld_R[9] = fontClear
__pld_R[9]()
if __pld_R[1] == __pld_R[2] then __pld_pc = 99 else __pld_pc = 100 end
elseif __pld_pc == 99 then
__pld_pc = 265
elseif __pld_pc == 100 then
__pld_R[7] = __pld_R[6]
__pld_R[9] = __pld_R[1] - __pld_R[2]
if not (0 < __pld_R[9]) then __pld_pc = 103 else __pld_pc = 104 end
elseif __pld_pc == 103 then
__pld_pc = 120
elseif __pld_pc == 104 then
__pld_R[6] = 1
if not (__pld_R[8] == 1) then __pld_pc = 106 else __pld_pc = 107 end
elseif __pld_pc == 106 then
__pld_pc = 110
elseif __pld_pc == 107 then
__pld_R[5] = 3
__pld_R[8] = 2
__pld_pc = 135
elseif __pld_pc == 110 then
if not (__pld_R[8] == 2) then __pld_pc = 111 else __pld_pc = 112 end
elseif __pld_pc == 111 then
__pld_pc = 115
elseif __pld_pc == 112 then
__pld_R[5] = 5
__pld_R[8] = 3
__pld_pc = 135
elseif __pld_pc == 115 then
if not (__pld_R[8] == 3) then __pld_pc = 116 else __pld_pc = 117 end
elseif __pld_pc == 116 then
__pld_pc = 135
elseif __pld_pc == 117 then
__pld_R[5] = 1
__pld_R[8] = 1
__pld_pc = 135
elseif __pld_pc == 120 then
__pld_R[6] = (-1)
if not (__pld_R[8] == 1) then __pld_pc = 122 else __pld_pc = 123 end
elseif __pld_pc == 122 then
__pld_pc = 126
elseif __pld_pc == 123 then
__pld_R[5] = 2
__pld_R[8] = 2
__pld_pc = 135
elseif __pld_pc == 126 then
if not (__pld_R[8] == 2) then __pld_pc = 127 else __pld_pc = 128 end
elseif __pld_pc == 127 then
__pld_pc = 131
elseif __pld_pc == 128 then
__pld_R[5] = 4
__pld_R[8] = 3
__pld_pc = 135
elseif __pld_pc == 131 then
if not (__pld_R[8] == 3) then __pld_pc = 132 else __pld_pc = 133 end
elseif __pld_pc == 132 then
__pld_pc = 135
elseif __pld_pc == 133 then
__pld_R[5] = 0
__pld_R[8] = 1
__pld_pc = 135
elseif __pld_pc == 135 then
__pld_R[9] = wait
__pld_R[10] = 5
__pld_R[9](__pld_R[10])
if __pld_R[6] == __pld_R[7] then __pld_pc = 139 else __pld_pc = 140 end
elseif __pld_pc == 139 then
__pld_pc = 232
elseif __pld_pc == 140 then
__pld_R[8] = 1
__pld_R[5] = 0
__pld_R[9] = layerLoad
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + 1
__pld_R[11] = ""
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerLoad
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + 2
__pld_R[11] = ""
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerLoad
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + 3
__pld_R[11] = ""
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerLoad
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + 4
__pld_R[11] = ""
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerLoad
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + 5
__pld_R[11] = ""
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerLoad
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[11] = "novel/"
__pld_R[12] = __pld_U[0].v
__pld_R[12] = __pld_R[12]["t_novelFlag"]
__pld_R[12] = __pld_R[12][__pld_R[0]]
__pld_R[13] = "_"
__pld_R[14] = __pld_R[1]
__pld_R[15] = ".gim"
__pld_R[11] = __pld_R[11] .. __pld_R[12] .. __pld_R[13] .. __pld_R[14] .. __pld_R[15]
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerPosition
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + __pld_R[5]
__pld_R[11] = 20
__pld_R[12] = 0
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12])
__pld_R[9] = comLayerLoadFalse
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + 2
__pld_R[11] = "novel/"
__pld_R[12] = __pld_U[0].v
__pld_R[12] = __pld_R[12]["t_novelFlag"]
__pld_R[12] = __pld_R[12][__pld_R[0]]
__pld_R[13] = "_"
__pld_R[14] = __pld_R[1] - 1
__pld_R[15] = ".gim"
__pld_R[11] = __pld_R[11] .. __pld_R[12] .. __pld_R[13] .. __pld_R[14] .. __pld_R[15]
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = comLayerLoadFalse
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + 3
__pld_R[11] = "novel/"
__pld_R[12] = __pld_U[0].v
__pld_R[12] = __pld_R[12]["t_novelFlag"]
__pld_R[12] = __pld_R[12][__pld_R[0]]
__pld_R[13] = "_"
__pld_R[14] = __pld_R[1] + 1
__pld_R[15] = ".gim"
__pld_R[11] = __pld_R[11] .. __pld_R[12] .. __pld_R[13] .. __pld_R[14] .. __pld_R[15]
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = __pld_U[4].v
__pld_R[10] = __pld_R[0]
__pld_R[11] = __pld_R[1]
__pld_R[12] = __pld_R[8]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12])
__pld_pc = 265
elseif __pld_pc == 232 then
__pld_R[9] = layerIsLoad
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + __pld_R[5]
__pld_R[9] = __pld_R[9](__pld_R[10])
if not (__pld_R[9] == true) then __pld_pc = 239 else __pld_pc = 240 end
elseif __pld_pc == 239 then
__pld_pc = 261
elseif __pld_pc == 240 then
__pld_R[9] = layerVisible
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + __pld_R[5]
__pld_R[11] = true
__pld_R[9](__pld_R[10], __pld_R[11])
__pld_R[9] = layerPosition
__pld_R[10] = __pld_U[0].v
__pld_R[10] = __pld_R[10]["indexNumber"]
__pld_R[10] = __pld_R[10]["sentence"]
__pld_R[10] = __pld_R[10] + __pld_R[5]
__pld_R[11] = 20
__pld_R[12] = 0
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12])
__pld_R[9] = __pld_U[4].v
__pld_R[10] = __pld_R[0]
__pld_R[11] = __pld_R[1]
__pld_R[12] = __pld_R[8]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12])
__pld_pc = 265
elseif __pld_pc == 261 then
__pld_R[9] = wait
__pld_R[10] = 1
__pld_R[9](__pld_R[10])
__pld_pc = 232
elseif __pld_pc == 265 then
if not (__pld_R[1] < 10) then __pld_pc = 266 else __pld_pc = 267 end
elseif __pld_pc == 266 then
__pld_pc = 276
elseif __pld_pc == 267 then
__pld_R[9] = __pld_U[5].v
__pld_R[10] = 14
__pld_R[11] = 470
__pld_R[12] = 205
__pld_R[13] = "00"
__pld_R[14] = __pld_R[1]
__pld_R[13] = __pld_R[13] .. __pld_R[14]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12], __pld_R[13])
__pld_pc = 293
elseif __pld_pc == 276 then
if not (__pld_R[1] < 100) then __pld_pc = 277 else __pld_pc = 278 end
elseif __pld_pc == 277 then
__pld_pc = 287
elseif __pld_pc == 278 then
__pld_R[9] = __pld_U[5].v
__pld_R[10] = 14
__pld_R[11] = 470
__pld_R[12] = 205
__pld_R[13] = "0"
__pld_R[14] = __pld_R[1]
__pld_R[13] = __pld_R[13] .. __pld_R[14]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12], __pld_R[13])
__pld_pc = 293
elseif __pld_pc == 287 then
__pld_R[9] = __pld_U[5].v
__pld_R[10] = 14
__pld_R[11] = 470
__pld_R[12] = 205
__pld_R[13] = __pld_R[1]
__pld_R[9](__pld_R[10], __pld_R[11], __pld_R[12], __pld_R[13])
__pld_pc = 293
elseif __pld_pc == 293 then
__pld_R[3] = false
__pld_pc = 294
elseif __pld_pc == 294 then
__pld_R[9] = wait
__pld_R[10] = 2
__pld_R[9](__pld_R[10])
__pld_pc = 35
elseif __pld_pc == 298 then
__pld_R[9] = __pld_U[6].v
__pld_R[9]()
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main_13"] = function(__pld_U)
return function()
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = __pld_U[0].v
if not (__pld_R[0] == 1) then __pld_pc = 3 else __pld_pc = 4 end
elseif __pld_pc == 3 then
__pld_pc = 13
elseif __pld_pc == 4 then
__pld_R[0] = msg
__pld_R[1] = "まだ一冊も取得していません。"
__pld_R[0](__pld_R[1])
__pld_R[0] = run
__pld_R[1] = cGetFileName
__pld_R[2] = "script"
__pld_R[3] = "snr_mainmenu"
do 
local __pld_rs = __pld_pack(__pld_R[1](__pld_R[2], __pld_R[3]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 1 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 1 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 1 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 1 + __pld_i - 1) end __pld_R[0](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_pc = 13
elseif __pld_pc == 13 then
__pld_R[0] = systemConfig
__pld_R[0] = __pld_R[0]["unsetConfigButton"]
__pld_R[0]()
__pld_R[0] = logEnable
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = advPart
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = startLoading
__pld_R[0]()
__pld_R[0] = pairs
__pld_R[1] = __pld_U[1].v
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[0], __pld_R[1], __pld_R[2] = __pld_R[0](__pld_R[1])
__pld_pc = 36
elseif __pld_pc == 29 then
__pld_R[5] = comLayerLoadFalse
__pld_R[6] = __pld_R[4]
__pld_R[7] = "novel/"
__pld_R[8] = __pld_R[3]
__pld_R[9] = ".gim"
__pld_R[7] = __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[5](__pld_R[6], __pld_R[7])
__pld_pc = 36
elseif __pld_pc == 36 then
__pld_R[3], __pld_R[4] = __pld_R[0](__pld_R[1], __pld_R[2])
if __pld_R[3] ~= nil then __pld_R[2] = __pld_R[3] __pld_pc = 37 else __pld_pc = 38 end
elseif __pld_pc == 37 then
__pld_pc = 29
elseif __pld_pc == 38 then
__pld_R[0] = waitLoading
__pld_R[0]()
__pld_R[0] = endLoading
__pld_R[0]()
__pld_R[0] = 1
__pld_pc = 43
elseif __pld_pc == 43 then
__pld_R[1] = __pld_U[2].v
if not (__pld_R[1] < 2) then __pld_pc = 45 else __pld_pc = 46 end
elseif __pld_pc == 45 then
__pld_pc = 64
elseif __pld_pc == 46 then
__pld_R[1] = __pld_U[2].v
if not (__pld_R[1] == 0) then __pld_pc = 48 else __pld_pc = 49 end
elseif __pld_pc == 48 then
__pld_pc = 54
elseif __pld_pc == 49 then
__pld_R[1] = __pld_U[3].v
__pld_R[2] = __pld_R[0]
__pld_R[1] = __pld_R[1](__pld_R[2])
__pld_R[0] = __pld_R[1]
__pld_pc = 60
elseif __pld_pc == 54 then
__pld_R[1] = __pld_U[2].v
if not (__pld_R[1] == 1) then __pld_pc = 56 else __pld_pc = 57 end
elseif __pld_pc == 56 then
__pld_pc = 60
elseif __pld_pc == 57 then
__pld_R[1] = __pld_U[4].v
__pld_R[2] = __pld_R[0]
__pld_R[1](__pld_R[2])
__pld_pc = 60
elseif __pld_pc == 60 then
__pld_R[1] = wait
__pld_R[2] = 2
__pld_R[1](__pld_R[2])
__pld_pc = 43
elseif __pld_pc == 64 then
__pld_R[1] = autoSystemSave
__pld_R[2] = 0
__pld_R[1](__pld_R[2])
__pld_R[1] = cInitGame
__pld_R[1]()
__pld_R[1] = run
__pld_R[2] = cGetFileName
__pld_R[3] = "script"
__pld_R[4] = "snr_mainmenu"
do 
local __pld_rs = __pld_pack(__pld_R[2](__pld_R[3], __pld_R[4]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 2 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 2 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 2 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 2 + __pld_i - 1) end __pld_R[1](__pld_unpack(__pld_t, 1, __pld_n)) end
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
__pld_F["main"] = function(__pld_U)
return function(...)
local __pld_R, __pld_B, __pld_top = {}, {[0]=true, [1]=true, [2]=true, [3]=true, [4]=true, [5]=true, [6]=true, [7]=true, [8]=true, [9]=true, [10]=true, [11]=true, [12]=true, [13]=true, [14]=true, [15]=true}, 0
__pld_R[0] = {}
__pld_R[1] = {}
__pld_R[2] = {}
__pld_R[3] = {}
__pld_R[4] = {}
__pld_R[5] = {}
__pld_R[6] = {}
__pld_R[7] = {}
__pld_R[8] = {}
__pld_R[9] = {}
__pld_R[10] = {}
__pld_R[11] = {}
__pld_R[12] = {}
__pld_R[13] = {}
__pld_R[14] = {}
__pld_R[15] = {}
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0].v = {}
__pld_R[1].v = {}
__pld_R[1].v["novel_1_a"] = 50
__pld_R[1].v["novel_1_b"] = 51
__pld_R[1].v["novel_2_a"] = 52
__pld_R[1].v["novel_2_b"] = 53
__pld_R[1].v["novel_2_c"] = 54
__pld_R[1].v["novel_3_aa"] = 55
__pld_R[1].v["novel_3_ab"] = 56
__pld_R[1].v["novel_3_ac"] = 57
__pld_R[1].v["novel_3_ad"] = 58
__pld_R[1].v["novel_3_ba"] = 59
__pld_R[1].v["novel_3_bb"] = 60
__pld_R[1].v["novel_3_bc"] = 61
__pld_R[1].v["novel_3_bd"] = 62
__pld_R[1].v["novel_3_ca"] = 63
__pld_R[1].v["novel_3_cb"] = 64
__pld_R[1].v["novel_3_cc"] = 65
__pld_R[1].v["novel_3_cd"] = 66
__pld_R[1].v["novel_3_da"] = 67
__pld_R[1].v["novel_3_db"] = 68
__pld_R[1].v["novel_3_dc"] = 69
__pld_R[1].v["novel_3_dd"] = 70
__pld_R[1].v["novel_3_ea"] = 71
__pld_R[1].v["novel_3_eb"] = 72
__pld_R[1].v["novel_3_ec"] = 73
__pld_R[1].v["novel_3_ed"] = 74
__pld_R[1].v["novel_4_a"] = 75
__pld_R[1].v["novel_4_b"] = 76
__pld_R[1].v["novel_4_c"] = 77
__pld_R[1].v["novel_4_d"] = 78
__pld_R[0].v["layerNumber"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[1].v["hardCover"] = 0
__pld_R[1].v["bar"] = 2
__pld_R[1].v["icon"] = 3
__pld_R[1].v["mask"] = 7
__pld_R[1].v["key"] = 8
__pld_R[1].v["novelBg"] = 0
__pld_R[1].v["sentence"] = 1
__pld_R[1].v["novelBar"] = 11
__pld_R[1].v["title"] = 12
__pld_R[1].v["bookMark"] = 13
__pld_R[0].v["indexNumber"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[2].v = "novel03"
__pld_R[3].v = "novel01"
__pld_R[4].v = "novel04"
__pld_R[5].v = "novel02"
__pld_R[6].v = "novel05"
__pld_R[1].v[1] = __pld_R[2].v
__pld_R[1].v[2] = __pld_R[3].v
__pld_R[1].v[3] = __pld_R[4].v
__pld_R[1].v[4] = __pld_R[5].v
__pld_R[1].v[5] = __pld_R[6].v
__pld_R[0].v["novelTitle"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[1].v["novel01"] = 1
__pld_R[1].v["novel02"] = 2
__pld_R[1].v["novel03"] = 3
__pld_R[1].v["novel04"] = 4
__pld_R[1].v["novel05"] = 5
__pld_R[0].v["novelKey"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[1].v["novel01"] = "novel_3_a"
__pld_R[1].v["novel02"] = "novel_3_b"
__pld_R[1].v["novel03"] = "novel_3_c"
__pld_R[1].v["novel04"] = "novel_3_d"
__pld_R[1].v["novel05"] = "novel_3_e"
__pld_R[0].v["layerName"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[1].v["novel01"] = 112
__pld_R[1].v["novel02"] = 159
__pld_R[1].v["novel03"] = 119
__pld_R[1].v["novel04"] = 119
__pld_R[1].v["novel05"] = 452
__pld_R[0].v["novelPageMax"] = __pld_R[1].v
__pld_R[1].v = {}
__pld_R[0].v["t_novelFlag"] = __pld_R[1].v
__pld_R[1].v = 0
__pld_R[2].v = 1
__pld_R[3].v = 1
__pld_R[4].v = 5
__pld_R[5].v = 1
do
local __pld_i = __pld_tonumber(__pld_R[3].v) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[4].v) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[5].v) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[3].v = __pld_i - __pld_s __pld_R[4].v = __pld_l __pld_R[5].v = __pld_s
end
__pld_pc = 94
elseif __pld_pc == 82 then
__pld_R[7].v = systemSave
__pld_R[7].v = __pld_R[7].v["novelGetFlag"]
__pld_R[8].v = __pld_R[0].v["novelTitle"]
__pld_R[8].v = __pld_R[8].v[__pld_R[6].v]
__pld_R[7].v = __pld_R[7].v[__pld_R[8].v]
if not (__pld_R[7].v == true) then __pld_pc = 88 else __pld_pc = 89 end
elseif __pld_pc == 88 then
__pld_pc = 94
elseif __pld_pc == 89 then
__pld_R[7].v = __pld_R[0].v["t_novelFlag"]
__pld_R[8].v = __pld_R[0].v["novelTitle"]
__pld_R[8].v = __pld_R[8].v[__pld_R[6].v]
__pld_R[7].v[__pld_R[2].v] = __pld_R[8].v
__pld_R[2].v = __pld_R[2].v + 1
__pld_pc = 94
elseif __pld_pc == 94 then
do local __pld_s = __pld_R[5].v local __pld_i = __pld_R[3].v + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[4].v) or (__pld_s <= 0 and __pld_i >= __pld_R[4].v) then
__pld_R[3].v = __pld_i __pld_R[6].v = __pld_i __pld_pc = 82
else __pld_pc = 95 end end
elseif __pld_pc == 95 then
__pld_R[3].v = __pld_F["main_0"]({[0]=__pld_R[0]})
__pld_R[4].v = __pld_F["main_1"]({[0]=__pld_R[0]})
__pld_R[5].v = __pld_F["main_2"]({[0]=__pld_R[0]})
__pld_R[6].v = __pld_F["main_3"]({[0]=__pld_R[0]})
__pld_R[7].v = __pld_F["main_4"]({[0]=__pld_R[0], [1]=__pld_R[6], [2]=__pld_R[4]})
__pld_R[8].v = __pld_F["main_5"]({[0]=__pld_R[0], [1]=__pld_R[5], [2]=__pld_R[3], [3]=__pld_R[4]})
__pld_R[9].v = __pld_F["main_6"]({})
__pld_R[10].v = __pld_F["main_7"]({[0]=__pld_R[8], [1]=__pld_R[0], [2]=__pld_R[1], [3]=__pld_R[7], [4]=__pld_R[9]})
__pld_R[11].v = __pld_F["main_8"]({[0]=__pld_R[0]})
__pld_R[12].v = __pld_F["main_9"]({[0]=__pld_R[0], [1]=__pld_R[4], [2]=__pld_R[3], [3]=__pld_R[11]})
__pld_R[13].v = __pld_F["main_10"]({})
__pld_R[14].v = __pld_F["main_11"]({[0]=__pld_R[0], [1]=__pld_R[4]})
__pld_R[15].v = __pld_F["main_12"]({[0]=__pld_R[0], [1]=__pld_R[12], [2]=__pld_R[1], [3]=__pld_R[14], [4]=__pld_R[11], [5]=__pld_R[3], [6]=__pld_R[13]})
__pld_R[16] = __pld_F["main_13"]({[0]=__pld_R[2], [1]=__pld_R[0], [2]=__pld_R[1], [3]=__pld_R[10], [4]=__pld_R[15]})
main = __pld_R[16]
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
end
return __pld_F["main"]({})(...)

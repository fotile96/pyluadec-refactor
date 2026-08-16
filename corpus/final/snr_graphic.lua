local l0_0 = {layerName = {graphic_01_a = 50, graphic_02_a = 51, graphic_03_a = 52, graphic_04_a = 53, graphic_05_a = 54, graphic_06_a = 55, graphic_07_a = 64, thumbnail_01_a = 56, thumbnail_02_a = 57, thumbnail_03_a = 58, thumbnail_04_a = 59, thumbnail_05_a = 60, thumbnail_06_a = 61, thumbnail_07_a = 62, thumbnail_08_a = 63}, layerNumber = {bg = 0, thumbnail = 2, mask = 11, complete = 31, key = 32, cursor = 34, view = 35}, thumbnailName = {"thumbnail_01_a", "thumbnail_02_a", "thumbnail_03_a", "thumbnail_04_a", "thumbnail_05_a", "thumbnail_06_a", "thumbnail_07_a", "thumbnail_08_a"}, viewX = {}, viewY = {}, cursorX = {}, cursorY = {}, cgNumber = {}}
l0_0.cgNumber[1] = {{"eve_1_x"}, {"eve_2_x"}, {"eve_3_x"}, {"eve_4_x"}, {"eve_5_x"}, {"eve_6_a", "eve_6_b", "eve_6_c"}, {"eve_7_x"}, {"eve_8_x"}, {"eve_9_x"}}
l0_0.cgNumber[2] = {{"eve_10_x"}, {"eve_11_x"}, {"eve_12_a", "eve_12_b"}, {"eve_13_x"}, {"eve_14_a", "eve_14_b"}, {"eve_15_a", "eve_15_b"}, {"eve_16_x"}, {"eve_17_x"}, {"eve_18_x"}}
l0_0.cgNumber[3] = {{"eve_19_x"}, {"eve_20_a", "eve_20_b", "eve_20_c", "eve_20_d"}, {"eve_21_x"}, {"eve_22_a", "eve_22_b"}, {"eve_23_x"}, {"eve_24_a", "eve_24_b"}, {"eve_25_a", "eve_25_b"}, {"eve_26_x"}, {"eve_27_a", "eve_27_b"}}
l0_0.cgNumber[4] = {{"eve_28_a", "eve_28_b", "eve_28_c"}, {"eve_29_x"}, {"eve_30_a", "eve_30_b"}, {"eve_31_a", "eve_31_b"}, {"eve_32_x", "eve_32_b"}, {"eve_33_a", "eve_33_b"}, {"eve_34_x"}, {"eve_35_a"}, {"eve_36_a", "eve_36_b", "eve_36_c"}}
l0_0.cgNumber[5] = {{"eve_37_x"}, {"eve_38_x"}, {"eve_39_x"}, {"eve_40_x"}, {"eve_41_x"}, {"eve_42_x"}, {"eve_43_x"}, {"eve_44_x"}, {"eve_45_x"}}
l0_0.cgNumber[6] = {{"eve_46_a", "eve_46_b", "eve_46_c", "eve_46_d"}, {"eve_47_x"}, {"eve_48_x"}, {"eve_49_x"}, {"eve_50_x"}, {"eve_51_a", "eve_51_b"}, {"eve_52_x"}, {"eve_53_x"}, {"eve_54_x"}}
l0_0.cgNumber[7] = {{"eve_55_x"}, {"eve_56_x"}, {"eve_57_a", "eve_57_b"}, {"eve_58_a", "eve_58_b"}, {"eve_59_x"}, {"eve_60_x"}, {"eve_61_x"}, {"eve_62_x"}, {"eve_63_x"}}
l0_0.cgNumber[8] = {{"eve_64_x"}, {"eve_69_x"}, {"eve_70_x"}, {"eve_71_x"}, {"eve_72_x"}, {"eve_73_a", "eve_73_b"}, {"eve_74_x"}}
local l0_1 = 1
local l0_2 = 0
local l0_3 = 1
local l0_4 = false
local l0_5 = 0
local l0_6 = 1
local l0_7 = 70
local l0_8 = math.ceil(l0_7 / 9)
local l0_9 = false
for l0_13 = 1, 8, 1 do
    for l0_17 = 1, 9, 1 do
        if l0_13 == 8 and 7 < l0_17 then
            break
        elseif systemSave.cgFlag[l0_0.cgNumber[l0_13][l0_17][1]] == true then
            l0_5 = l0_5 + 1
        end
    end
end
local l0_10 = function(l1_0, l1_1, l1_2, l1_3)
    for l1_7 = 1, string.len(l1_3), 1 do
        local l1_8 = string.sub(l1_3, l1_7, l1_7)
        layerCopy(l1_0 + l1_7 - 1, l0_0.layerName.graphic_03_a)
        layerPosition(l1_0 + l1_7 - 1, l1_1 + 7 * (l1_7 - 1), l1_2)
        layerClip(l1_0 + l1_7 - 1, 0, l1_8 * 7, 7, (l1_8 + 1) * 7)
    end
end
local l0_11 = function(l1_0, l1_1, l1_2)
    layerClip(l1_0, l1_1 * 120, l1_2 * 68, (l1_1 + 1) * 120, (l1_2 + 1) * 68)
end
local l0_12 = function()
    layerLoad(l0_0.layerNumber.bg, cGetFileName("bg", "bg_1_a_0"))
    layerCopy(l0_0.layerNumber.bg + 1, l0_0.layerName.graphic_01_a)
    local l1_0 = 0
    local l1_1 = 0
    for l1_5 = 1, 9, 1 do
        layerCopy(l0_0.layerNumber.mask + l1_5, l0_0.layerName.graphic_02_a)
        layerPosition(l0_0.layerNumber.mask + l1_5, 30 + l1_0 * 130, 50 + l1_1 * 73)
        if systemSave.cgFlag[l0_0.cgNumber[l0_3][l1_5][1]] == true then
            layerCopy(l0_0.layerNumber.thumbnail + l1_5, l0_0.layerName[l0_0.thumbnailName[l0_3]])
            l0_11(l0_0.layerNumber.thumbnail + l1_5, l1_0, l1_1)
            layerPosition(l0_0.layerNumber.thumbnail + l1_5, 30 + l1_0 * 130, 50 + l1_1 * 73)
        end
        l0_0.cursorX[l1_5] = 30 + l1_0 * 130
        l0_0.cursorY[l1_5] = 50 + l1_1 * 73
        l0_0.viewX[l1_5] = l1_0 * 130 - 150
        l0_0.viewY[l1_5] = l1_1 * 73 - 52
        l1_0 = l1_0 + 1
        if l1_0 >= 3 then
            l1_0 = 0
            l1_1 = l1_1 + 1
        end
    end
    l0_10(25, 460, 2, "01")
    l0_10(27, 387, 40, l0_7)
    l0_10(29, 357, 40, l0_5 < 10 and "0" .. l0_5 or l0_5)
    if l0_5 == l0_7 then
        layerCopy(l0_0.layerNumber.complete, l0_0.layerName.graphic_04_a)
    end
    layerPosition(l0_0.layerNumber.complete, 410, 40)
    layerCopy(l0_0.layerNumber.key, l0_0.layerName.graphic_05_a)
    layerClip(l0_0.layerNumber.key, 0, 0, 12, 18)
    layerPosition(l0_0.layerNumber.key, 463, 130)
    layerVisible(l0_0.layerNumber.mask + 1, false)
    layerCopy(l0_0.layerNumber.cursor, l0_0.layerName.graphic_07_a)
    layerPosition(l0_0.layerNumber.cursor, l0_0.cursorX[1], l0_0.cursorY[1])
end
local l0_13 = function(__pld_p0, __pld_p1, __pld_p2, __pld_p3)
local __pld_ord = {l0_0, l0_7, l0_10, l0_11, l0_8}
local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_R, __pld_B, __pld_top = {}, {}, 0
__pld_R[0] = __pld_p0
__pld_R[1] = __pld_p1
__pld_R[2] = __pld_p2
__pld_R[3] = __pld_p3
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[4] = 0
__pld_R[5] = 0
__pld_R[6] = layerLoad
__pld_R[7] = l0_0
__pld_R[7] = __pld_R[7]["layerNumber"]
__pld_R[7] = __pld_R[7]["key"]
__pld_R[8] = ""
__pld_R[6](__pld_R[7], __pld_R[8])
__pld_R[6] = layerLoad
__pld_R[7] = l0_0
__pld_R[7] = __pld_R[7]["layerNumber"]
__pld_R[7] = __pld_R[7]["key"]
__pld_R[7] = __pld_R[7] + 1
__pld_R[8] = ""
__pld_R[6](__pld_R[7], __pld_R[8])
__pld_R[6] = l0_7
__pld_R[7] = __pld_R[3] * 9
__pld_R[6] = __pld_R[6] - __pld_R[7]
if not (__pld_R[6] < 0) then __pld_pc = 20 else __pld_pc = 21 end
elseif __pld_pc == 20 then
__pld_pc = 27
elseif __pld_pc == 21 then
__pld_R[6] = l0_7
__pld_R[7] = __pld_R[3] - 1
__pld_R[7] = __pld_R[7] * 9
__pld_R[6] = __pld_R[6] - __pld_R[7]
if __pld_R[6] then __pld_pc = 26 else __pld_pc = 27 end
elseif __pld_pc == 26 then
__pld_pc = 28
elseif __pld_pc == 27 then
__pld_R[6] = 9
__pld_pc = 28
elseif __pld_pc == 28 then
if not (__pld_R[0] == 0) then __pld_pc = 29 else __pld_pc = 30 end
elseif __pld_pc == 29 then
__pld_pc = 33
elseif __pld_pc == 30 then
__pld_R[7] = 9
if __pld_R[7] then __pld_pc = 32 else __pld_pc = 33 end
elseif __pld_pc == 32 then
__pld_pc = 36
elseif __pld_pc == 33 then
__pld_R[7] = l0_7
__pld_R[8] = __pld_R[3] * 9
__pld_R[7] = __pld_R[7] - __pld_R[8]
__pld_pc = 36
elseif __pld_pc == 36 then
if not (9 < __pld_R[7]) then __pld_pc = 37 else __pld_pc = 38 end
elseif __pld_pc == 37 then
__pld_pc = 41
elseif __pld_pc == 38 then
__pld_R[8] = 9
do local __pld_t = __pld_R[8] if __pld_t then __pld_R[7] = __pld_t __pld_pc = 40 else __pld_pc = 41 end end
elseif __pld_pc == 40 then
__pld_pc = 41
elseif __pld_pc == 41 then
__pld_R[8] = 1
__pld_R[9] = __pld_R[7]
__pld_R[10] = 1
do
local __pld_i = __pld_tonumber(__pld_R[8]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[9]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[10]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[8] = __pld_i - __pld_s __pld_R[9] = __pld_l __pld_R[10] = __pld_s
end
__pld_pc = 97
elseif __pld_pc == 45 then
if not (__pld_R[0] == 0) then __pld_pc = 46 else __pld_pc = 47 end
elseif __pld_pc == 46 then
__pld_pc = 70
elseif __pld_pc == 47 then
__pld_R[12] = layerMovePosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["mask"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = __pld_R[14] - 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[16] = 20
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15], __pld_R[16])
__pld_R[12] = layerMovePosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = __pld_R[14] - 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[16] = 20
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15], __pld_R[16])
__pld_pc = 92
elseif __pld_pc == 70 then
__pld_R[12] = layerMovePosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["mask"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = __pld_R[14] + 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[16] = 20
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15], __pld_R[16])
__pld_R[12] = layerMovePosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = __pld_R[14] + 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[16] = 20
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15], __pld_R[16])
__pld_pc = 92
elseif __pld_pc == 92 then
__pld_R[4] = __pld_R[4] + 1
if not (3 <= __pld_R[4]) then __pld_pc = 94 else __pld_pc = 95 end
elseif __pld_pc == 94 then
__pld_pc = 97
elseif __pld_pc == 95 then
__pld_R[4] = 0
__pld_R[5] = __pld_R[5] + 1
__pld_pc = 97
elseif __pld_pc == 97 then
do local __pld_s = __pld_R[10] local __pld_i = __pld_R[8] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[9]) or (__pld_s <= 0 and __pld_i >= __pld_R[9]) then
__pld_R[8] = __pld_i __pld_R[11] = __pld_i __pld_pc = 45
else __pld_pc = 98 end end
elseif __pld_pc == 98 then
if not (__pld_R[0] == 0) then __pld_pc = 99 else __pld_pc = 100 end
elseif __pld_pc == 99 then
__pld_pc = 114
elseif __pld_pc == 100 then
__pld_R[8] = layerMovePosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["cursor"]
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["cursorX"]
__pld_R[10] = __pld_R[10][__pld_R[1]]
__pld_R[10] = __pld_R[10] - 480
__pld_R[11] = l0_0
__pld_R[11] = __pld_R[11]["cursorY"]
__pld_R[11] = __pld_R[11][__pld_R[1]]
__pld_R[12] = 20
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12])
__pld_pc = 127
elseif __pld_pc == 114 then
__pld_R[8] = layerMovePosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["cursor"]
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["cursorX"]
__pld_R[10] = __pld_R[10][__pld_R[1]]
__pld_R[10] = __pld_R[10] + 480
__pld_R[11] = l0_0
__pld_R[11] = __pld_R[11]["cursorY"]
__pld_R[11] = __pld_R[11][__pld_R[1]]
__pld_R[12] = 20
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12])
__pld_pc = 127
elseif __pld_pc == 127 then
__pld_R[8] = wait
__pld_R[9] = 20
__pld_R[8](__pld_R[9])
__pld_R[8] = l0_10
__pld_R[9] = 25
__pld_R[10] = 460
__pld_R[11] = 2
if not (__pld_R[3] < 10) then __pld_pc = 135 else __pld_pc = 136 end
elseif __pld_pc == 135 then
__pld_pc = 141
elseif __pld_pc == 136 then
__pld_R[12] = "0"
__pld_R[13] = __pld_R[3]
__pld_R[12] = __pld_R[12] .. __pld_R[13]
if __pld_R[12] then __pld_pc = 140 else __pld_pc = 141 end
elseif __pld_pc == 140 then
__pld_pc = 142
elseif __pld_pc == 141 then
__pld_R[12] = __pld_R[3]
__pld_pc = 142
elseif __pld_pc == 142 then
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12])
__pld_R[8] = 1
__pld_R[9] = __pld_R[7]
__pld_R[10] = 1
do
local __pld_i = __pld_tonumber(__pld_R[8]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[9]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[10]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[8] = __pld_i - __pld_s __pld_R[9] = __pld_l __pld_R[10] = __pld_s
end
__pld_pc = 161
elseif __pld_pc == 147 then
__pld_R[12] = layerLoad
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["mask"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = ""
__pld_R[12](__pld_R[13], __pld_R[14])
__pld_R[12] = layerLoad
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = ""
__pld_R[12](__pld_R[13], __pld_R[14])
__pld_pc = 161
elseif __pld_pc == 161 then
do local __pld_s = __pld_R[10] local __pld_i = __pld_R[8] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[9]) or (__pld_s <= 0 and __pld_i >= __pld_R[9]) then
__pld_R[8] = __pld_i __pld_R[11] = __pld_i __pld_pc = 147
else __pld_pc = 162 end end
elseif __pld_pc == 162 then
__pld_R[4] = 0
__pld_R[5] = 0
__pld_R[8] = 1
__pld_R[9] = __pld_R[6]
__pld_R[10] = 1
do
local __pld_i = __pld_tonumber(__pld_R[8]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[9]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[10]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[8] = __pld_i - __pld_s __pld_R[9] = __pld_l __pld_R[10] = __pld_s
end
__pld_pc = 281
elseif __pld_pc == 168 then
__pld_R[12] = layerCopy
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["mask"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = l0_0
__pld_R[14] = __pld_R[14]["layerName"]
__pld_R[14] = __pld_R[14]["graphic_02_a"]
__pld_R[12](__pld_R[13], __pld_R[14])
__pld_R[12] = systemSave
__pld_R[12] = __pld_R[12]["cgFlag"]
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["cgNumber"]
__pld_R[13] = __pld_R[13][__pld_R[3]]
__pld_R[13] = __pld_R[13][__pld_R[11]]
__pld_R[13] = __pld_R[13][1]
__pld_R[12] = __pld_R[12][__pld_R[13]]
if not (__pld_R[12] == true) then __pld_pc = 186 else __pld_pc = 187 end
elseif __pld_pc == 186 then
__pld_pc = 207
elseif __pld_pc == 187 then
__pld_R[12] = layerCopy
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = l0_0
__pld_R[14] = __pld_R[14]["layerName"]
__pld_R[15] = l0_0
__pld_R[15] = __pld_R[15]["thumbnailName"]
__pld_R[15] = __pld_R[15][__pld_R[3]]
__pld_R[14] = __pld_R[14][__pld_R[15]]
__pld_R[12](__pld_R[13], __pld_R[14])
__pld_R[12] = l0_11
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4]
__pld_R[15] = __pld_R[5]
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15])
__pld_pc = 207
elseif __pld_pc == 207 then
if not (__pld_R[0] == 0) then __pld_pc = 208 else __pld_pc = 209 end
elseif __pld_pc == 208 then
__pld_pc = 232
elseif __pld_pc == 209 then
__pld_R[12] = layerPosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["mask"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = 30 + __pld_R[14]
__pld_R[14] = __pld_R[14] + 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15])
__pld_R[12] = layerPosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = 30 + __pld_R[14]
__pld_R[14] = __pld_R[14] + 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15])
__pld_pc = 254
elseif __pld_pc == 232 then
__pld_R[12] = layerPosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["mask"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = 30 + __pld_R[14]
__pld_R[14] = __pld_R[14] - 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15])
__pld_R[12] = layerPosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = 30 + __pld_R[14]
__pld_R[14] = __pld_R[14] - 480
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15])
__pld_pc = 254
elseif __pld_pc == 254 then
__pld_R[12] = layerMovePosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["mask"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = 30 + __pld_R[14]
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[16] = 20
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15], __pld_R[16])
__pld_R[12] = layerMovePosition
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["layerNumber"]
__pld_R[13] = __pld_R[13]["thumbnail"]
__pld_R[13] = __pld_R[13] + __pld_R[11]
__pld_R[14] = __pld_R[4] * 130
__pld_R[14] = 30 + __pld_R[14]
__pld_R[15] = __pld_R[5] * 73
__pld_R[15] = 50 + __pld_R[15]
__pld_R[16] = 20
__pld_R[12](__pld_R[13], __pld_R[14], __pld_R[15], __pld_R[16])
__pld_R[4] = __pld_R[4] + 1
if not (3 <= __pld_R[4]) then __pld_pc = 278 else __pld_pc = 279 end
elseif __pld_pc == 278 then
__pld_pc = 281
elseif __pld_pc == 279 then
__pld_R[4] = 0
__pld_R[5] = __pld_R[5] + 1
__pld_pc = 281
elseif __pld_pc == 281 then
do local __pld_s = __pld_R[10] local __pld_i = __pld_R[8] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[9]) or (__pld_s <= 0 and __pld_i >= __pld_R[9]) then
__pld_R[8] = __pld_i __pld_R[11] = __pld_i __pld_pc = 168
else __pld_pc = 282 end end
elseif __pld_pc == 282 then
if not (__pld_R[0] == 0) then __pld_pc = 283 else __pld_pc = 284 end
elseif __pld_pc == 283 then
__pld_pc = 310
elseif __pld_pc == 284 then
__pld_R[8] = layerPosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["cursor"]
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["cursorX"]
__pld_R[10] = __pld_R[10][__pld_R[2]]
__pld_R[10] = __pld_R[10] + 480
__pld_R[11] = l0_0
__pld_R[11] = __pld_R[11]["cursorY"]
__pld_R[11] = __pld_R[11][__pld_R[2]]
__pld_R[12] = 20
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12])
__pld_R[8] = layerMovePosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["cursor"]
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["cursorX"]
__pld_R[10] = __pld_R[10][__pld_R[2]]
__pld_R[11] = l0_0
__pld_R[11] = __pld_R[11]["cursorY"]
__pld_R[11] = __pld_R[11][__pld_R[2]]
__pld_R[12] = 20
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12])
__pld_pc = 335
elseif __pld_pc == 310 then
__pld_R[8] = layerPosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["cursor"]
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["cursorX"]
__pld_R[10] = __pld_R[10][__pld_R[2]]
__pld_R[10] = __pld_R[10] - 480
__pld_R[11] = l0_0
__pld_R[11] = __pld_R[11]["cursorY"]
__pld_R[11] = __pld_R[11][__pld_R[2]]
__pld_R[12] = 20
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12])
__pld_R[8] = layerMovePosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["cursor"]
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["cursorX"]
__pld_R[10] = __pld_R[10][__pld_R[2]]
__pld_R[11] = l0_0
__pld_R[11] = __pld_R[11]["cursorY"]
__pld_R[11] = __pld_R[11][__pld_R[2]]
__pld_R[12] = 20
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12])
__pld_pc = 335
elseif __pld_pc == 335 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["mask"]
__pld_R[9] = __pld_R[9] + __pld_R[1]
__pld_R[10] = true
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["mask"]
__pld_R[9] = __pld_R[9] + __pld_R[2]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = wait
__pld_R[9] = 20
__pld_R[8](__pld_R[9])
if __pld_R[3] == 1 then __pld_pc = 353 else __pld_pc = 354 end
elseif __pld_pc == 353 then
__pld_pc = 378
elseif __pld_pc == 354 then
__pld_R[8] = layerCopy
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["key"]
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["layerName"]
__pld_R[10] = __pld_R[10]["graphic_06_a"]
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerClip
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["key"]
__pld_R[10] = 0
__pld_R[11] = 0
__pld_R[12] = 12
__pld_R[13] = 18
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12], __pld_R[13])
__pld_R[8] = layerPosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["key"]
__pld_R[10] = 5
__pld_R[11] = 130
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 378
elseif __pld_pc == 378 then
__pld_R[8] = l0_8
if not (__pld_R[3] < __pld_R[8]) then __pld_pc = 380 else __pld_pc = 381 end
elseif __pld_pc == 380 then
__pld_pc = 408
elseif __pld_pc == 381 then
__pld_R[8] = layerCopy
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["key"]
__pld_R[9] = __pld_R[9] + 1
__pld_R[10] = l0_0
__pld_R[10] = __pld_R[10]["layerName"]
__pld_R[10] = __pld_R[10]["graphic_05_a"]
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerClip
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["key"]
__pld_R[9] = __pld_R[9] + 1
__pld_R[10] = 0
__pld_R[11] = 0
__pld_R[12] = 12
__pld_R[13] = 18
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11], __pld_R[12], __pld_R[13])
__pld_R[8] = layerPosition
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["key"]
__pld_R[9] = __pld_R[9] + 1
__pld_R[10] = 463
__pld_R[11] = 130
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 408
elseif __pld_pc == 408 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
main = function()
local __pld_ord = {l0_0, l0_12, l0_9, l0_4, l0_2, l0_1, l0_7, l0_3, l0_8, l0_13, l0_6}
local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = advPart
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = logEnable
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = systemConfig
__pld_R[0] = __pld_R[0]["unsetConfigButton"]
__pld_R[0]()
__pld_R[0] = startLoading
__pld_R[0]()
__pld_R[0] = pairs
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerName"]
__pld_R[0], __pld_R[1], __pld_R[2] = __pld_R[0](__pld_R[1])
__pld_pc = 24
elseif __pld_pc == 17 then
__pld_R[5] = comLayerLoadFalse
__pld_R[6] = __pld_R[4]
__pld_R[7] = "graphic/"
__pld_R[8] = __pld_R[3]
__pld_R[9] = ".gim"
__pld_R[7] = __pld_R[7] .. __pld_R[8] .. __pld_R[9]
__pld_R[5](__pld_R[6], __pld_R[7])
__pld_pc = 24
elseif __pld_pc == 24 then
__pld_R[3], __pld_R[4] = __pld_R[0](__pld_R[1], __pld_R[2])
if __pld_R[3] ~= nil then __pld_R[2] = __pld_R[3] __pld_pc = 25 else __pld_pc = 26 end
elseif __pld_pc == 25 then
__pld_pc = 17
elseif __pld_pc == 26 then
__pld_R[0] = waitLoading
__pld_R[0]()
__pld_R[0] = endLoading
__pld_R[0]()
__pld_R[0] = l0_12
__pld_R[0]()
__pld_pc = 32
elseif __pld_pc == 32 then
__pld_R[0] = l0_9
if not (__pld_R[0] == false) then __pld_pc = 34 else __pld_pc = 35 end
elseif __pld_pc == 34 then
__pld_pc = 535
elseif __pld_pc == 35 then
__pld_R[0] = pressButton
__pld_R[1] = "UP"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 39 else __pld_pc = 40 end
elseif __pld_pc == 39 then
__pld_pc = 57
elseif __pld_pc == 40 then
__pld_R[0] = l0_4
if not (__pld_R[0] == false) then __pld_pc = 42 else __pld_pc = 43 end
elseif __pld_pc == 42 then
__pld_pc = 57
elseif __pld_pc == 43 then
__pld_R[0] = l0_1
l0_2 = __pld_R[0]
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] - 3
if not (__pld_R[0] < 1) then __pld_pc = 48 else __pld_pc = 49 end
elseif __pld_pc == 48 then
__pld_pc = 52
elseif __pld_pc == 49 then
__pld_R[0] = l0_1
if __pld_R[0] then __pld_pc = 51 else __pld_pc = 52 end
elseif __pld_pc == 51 then
__pld_pc = 54
elseif __pld_pc == 52 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] - 3
__pld_pc = 54
elseif __pld_pc == 54 then
l0_1 = __pld_R[0]
__pld_R[0] = true
l0_4 = __pld_R[0]
__pld_pc = 57
elseif __pld_pc == 57 then
__pld_R[0] = pressButton
__pld_R[1] = "DOWN"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 61 else __pld_pc = 62 end
elseif __pld_pc == 61 then
__pld_pc = 101
elseif __pld_pc == 62 then
__pld_R[0] = l0_4
if not (__pld_R[0] == false) then __pld_pc = 64 else __pld_pc = 65 end
elseif __pld_pc == 64 then
__pld_pc = 101
elseif __pld_pc == 65 then
__pld_R[0] = l0_1
l0_2 = __pld_R[0]
__pld_R[0] = l0_7
__pld_R[1] = l0_3
__pld_R[1] = __pld_R[1] * 9
__pld_R[0] = __pld_R[0] - __pld_R[1]
if not (__pld_R[0] < 0) then __pld_pc = 72 else __pld_pc = 73 end
elseif __pld_pc == 72 then
__pld_pc = 89
elseif __pld_pc == 73 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 3
__pld_R[1] = l0_7
__pld_R[2] = l0_3
__pld_R[2] = __pld_R[2] - 1
__pld_R[2] = __pld_R[2] * 9
__pld_R[1] = __pld_R[1] - __pld_R[2]
if not (__pld_R[1] < __pld_R[0]) then __pld_pc = 81 else __pld_pc = 82 end
elseif __pld_pc == 81 then
__pld_pc = 85
elseif __pld_pc == 82 then
__pld_R[0] = l0_1
if __pld_R[0] then __pld_pc = 84 else __pld_pc = 85 end
elseif __pld_pc == 84 then
__pld_pc = 87
elseif __pld_pc == 85 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 3
__pld_pc = 87
elseif __pld_pc == 87 then
l0_1 = __pld_R[0]
__pld_pc = 99
elseif __pld_pc == 89 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 3
if not (9 < __pld_R[0]) then __pld_pc = 92 else __pld_pc = 93 end
elseif __pld_pc == 92 then
__pld_pc = 96
elseif __pld_pc == 93 then
__pld_R[0] = l0_1
if __pld_R[0] then __pld_pc = 95 else __pld_pc = 96 end
elseif __pld_pc == 95 then
__pld_pc = 98
elseif __pld_pc == 96 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 3
__pld_pc = 98
elseif __pld_pc == 98 then
l0_1 = __pld_R[0]
__pld_pc = 99
elseif __pld_pc == 99 then
__pld_R[0] = true
l0_4 = __pld_R[0]
__pld_pc = 101
elseif __pld_pc == 101 then
__pld_R[0] = pressButton
__pld_R[1] = "RIGHT"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 105 else __pld_pc = 106 end
elseif __pld_pc == 105 then
__pld_pc = 213
elseif __pld_pc == 106 then
__pld_R[0] = l0_4
if not (__pld_R[0] == false) then __pld_pc = 108 else __pld_pc = 109 end
elseif __pld_pc == 108 then
__pld_pc = 213
elseif __pld_pc == 109 then
__pld_R[0] = l0_1
l0_2 = __pld_R[0]
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] + 1
__pld_R[1] = l0_8
if not (__pld_R[0] <= __pld_R[1]) then __pld_pc = 115 else __pld_pc = 116 end
elseif __pld_pc == 115 then
__pld_pc = 183
elseif __pld_pc == 116 then
__pld_R[0] = l0_1
if __pld_R[0] == 3 then __pld_pc = 118 else __pld_pc = 119 end
elseif __pld_pc == 118 then
__pld_pc = 125
elseif __pld_pc == 119 then
__pld_R[0] = l0_1
if __pld_R[0] == 6 then __pld_pc = 121 else __pld_pc = 122 end
elseif __pld_pc == 121 then
__pld_pc = 125
elseif __pld_pc == 122 then
__pld_R[0] = l0_1
if not (__pld_R[0] == 9) then __pld_pc = 124 else __pld_pc = 125 end
elseif __pld_pc == 124 then
__pld_pc = 161
elseif __pld_pc == 125 then
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] + 1
l0_3 = __pld_R[0]
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] - 2
l0_1 = __pld_R[0]
__pld_R[0] = l0_7
__pld_R[1] = l0_3
__pld_R[1] = __pld_R[1] * 9
__pld_R[0] = __pld_R[0] - __pld_R[1]
if not (__pld_R[0] < 0) then __pld_pc = 136 else __pld_pc = 137 end
elseif __pld_pc == 136 then
__pld_pc = 154
elseif __pld_pc == 137 then
__pld_R[0] = l0_1
__pld_R[1] = l0_7
__pld_R[2] = l0_3
__pld_R[2] = __pld_R[2] - 1
__pld_R[2] = __pld_R[2] * 9
__pld_R[1] = __pld_R[1] - __pld_R[2]
if not (__pld_R[1] < __pld_R[0]) then __pld_pc = 144 else __pld_pc = 145 end
elseif __pld_pc == 144 then
__pld_pc = 152
elseif __pld_pc == 145 then
__pld_R[0] = l0_7
__pld_R[1] = l0_3
__pld_R[1] = __pld_R[1] - 1
__pld_R[1] = __pld_R[1] * 9
__pld_R[0] = __pld_R[0] - __pld_R[1]
if __pld_R[0] then __pld_pc = 151 else __pld_pc = 152 end
elseif __pld_pc == 151 then
__pld_pc = 153
elseif __pld_pc == 152 then
__pld_R[0] = l0_1
__pld_pc = 153
elseif __pld_pc == 153 then
l0_1 = __pld_R[0]
__pld_pc = 154
elseif __pld_pc == 154 then
__pld_R[0] = l0_13
__pld_R[1] = 0
__pld_R[2] = l0_2
__pld_R[3] = l0_1
__pld_R[4] = l0_3
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_pc = 213
elseif __pld_pc == 161 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 1
__pld_R[1] = l0_7
__pld_R[2] = l0_3
__pld_R[2] = __pld_R[2] - 1
__pld_R[2] = __pld_R[2] * 9
__pld_R[1] = __pld_R[1] - __pld_R[2]
if not (__pld_R[1] < __pld_R[0]) then __pld_pc = 169 else __pld_pc = 170 end
elseif __pld_pc == 169 then
__pld_pc = 173
elseif __pld_pc == 170 then
__pld_R[0] = l0_1
if __pld_R[0] then __pld_pc = 172 else __pld_pc = 173 end
elseif __pld_pc == 172 then
__pld_pc = 175
elseif __pld_pc == 173 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 175
elseif __pld_pc == 175 then
l0_1 = __pld_R[0]
__pld_R[0] = l0_1
__pld_R[1] = l0_2
if not (__pld_R[0] == __pld_R[1]) then __pld_pc = 179 else __pld_pc = 180 end
elseif __pld_pc == 179 then
__pld_pc = 180
elseif __pld_pc == 180 then
__pld_R[0] = true
l0_4 = __pld_R[0]
__pld_pc = 213
elseif __pld_pc == 183 then
__pld_R[0] = l0_1
if __pld_R[0] == 3 then __pld_pc = 185 else __pld_pc = 186 end
elseif __pld_pc == 185 then
__pld_pc = 213
elseif __pld_pc == 186 then
__pld_R[0] = l0_1
if __pld_R[0] == 6 then __pld_pc = 188 else __pld_pc = 189 end
elseif __pld_pc == 188 then
__pld_pc = 213
elseif __pld_pc == 189 then
__pld_R[0] = l0_1
if __pld_R[0] == 9 then __pld_pc = 191 else __pld_pc = 192 end
elseif __pld_pc == 191 then
__pld_pc = 213
elseif __pld_pc == 192 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 1
__pld_R[1] = l0_7
__pld_R[2] = l0_3
__pld_R[2] = __pld_R[2] - 1
__pld_R[2] = __pld_R[2] * 9
__pld_R[1] = __pld_R[1] - __pld_R[2]
if not (__pld_R[1] < __pld_R[0]) then __pld_pc = 200 else __pld_pc = 201 end
elseif __pld_pc == 200 then
__pld_pc = 204
elseif __pld_pc == 201 then
__pld_R[0] = l0_1
if __pld_R[0] then __pld_pc = 203 else __pld_pc = 204 end
elseif __pld_pc == 203 then
__pld_pc = 206
elseif __pld_pc == 204 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 206
elseif __pld_pc == 206 then
l0_1 = __pld_R[0]
__pld_R[0] = l0_1
__pld_R[1] = l0_2
if not (__pld_R[0] == __pld_R[1]) then __pld_pc = 210 else __pld_pc = 211 end
elseif __pld_pc == 210 then
__pld_pc = 211
elseif __pld_pc == 211 then
__pld_R[0] = true
l0_4 = __pld_R[0]
__pld_pc = 213
elseif __pld_pc == 213 then
__pld_R[0] = pressButton
__pld_R[1] = "LEFT"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 217 else __pld_pc = 218 end
elseif __pld_pc == 217 then
__pld_pc = 277
elseif __pld_pc == 218 then
__pld_R[0] = l0_4
if not (__pld_R[0] == false) then __pld_pc = 220 else __pld_pc = 221 end
elseif __pld_pc == 220 then
__pld_pc = 277
elseif __pld_pc == 221 then
__pld_R[0] = l0_1
l0_2 = __pld_R[0]
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] - 1
if not (1 <= __pld_R[0]) then __pld_pc = 226 else __pld_pc = 227 end
elseif __pld_pc == 226 then
__pld_pc = 259
elseif __pld_pc == 227 then
__pld_R[0] = l0_1
if __pld_R[0] == 1 then __pld_pc = 229 else __pld_pc = 230 end
elseif __pld_pc == 229 then
__pld_pc = 236
elseif __pld_pc == 230 then
__pld_R[0] = l0_1
if __pld_R[0] == 4 then __pld_pc = 232 else __pld_pc = 233 end
elseif __pld_pc == 232 then
__pld_pc = 236
elseif __pld_pc == 233 then
__pld_R[0] = l0_1
if not (__pld_R[0] == 7) then __pld_pc = 235 else __pld_pc = 236 end
elseif __pld_pc == 235 then
__pld_pc = 249
elseif __pld_pc == 236 then
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] - 1
l0_3 = __pld_R[0]
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] + 2
l0_1 = __pld_R[0]
__pld_R[0] = l0_13
__pld_R[1] = 1
__pld_R[2] = l0_2
__pld_R[3] = l0_1
__pld_R[4] = l0_3
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_pc = 277
elseif __pld_pc == 249 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] - 1
l0_1 = __pld_R[0]
__pld_R[0] = l0_1
__pld_R[1] = l0_2
if not (__pld_R[0] == __pld_R[1]) then __pld_pc = 255 else __pld_pc = 256 end
elseif __pld_pc == 255 then
__pld_pc = 256
elseif __pld_pc == 256 then
__pld_R[0] = true
l0_4 = __pld_R[0]
__pld_pc = 277
elseif __pld_pc == 259 then
__pld_R[0] = l0_1
if __pld_R[0] == 1 then __pld_pc = 261 else __pld_pc = 262 end
elseif __pld_pc == 261 then
__pld_pc = 277
elseif __pld_pc == 262 then
__pld_R[0] = l0_1
if __pld_R[0] == 4 then __pld_pc = 264 else __pld_pc = 265 end
elseif __pld_pc == 264 then
__pld_pc = 277
elseif __pld_pc == 265 then
__pld_R[0] = l0_1
if __pld_R[0] == 7 then __pld_pc = 267 else __pld_pc = 268 end
elseif __pld_pc == 267 then
__pld_pc = 277
elseif __pld_pc == 268 then
__pld_R[0] = l0_1
__pld_R[0] = __pld_R[0] - 1
l0_1 = __pld_R[0]
__pld_R[0] = l0_1
__pld_R[1] = l0_2
if not (__pld_R[0] == __pld_R[1]) then __pld_pc = 274 else __pld_pc = 275 end
elseif __pld_pc == 274 then
__pld_pc = 275
elseif __pld_pc == 275 then
__pld_R[0] = true
l0_4 = __pld_R[0]
__pld_pc = 277
elseif __pld_pc == 277 then
__pld_R[0] = pressButton
__pld_R[1] = "L"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 281 else __pld_pc = 282 end
elseif __pld_pc == 281 then
__pld_pc = 298
elseif __pld_pc == 282 then
__pld_R[0] = l0_4
if not (__pld_R[0] == false) then __pld_pc = 284 else __pld_pc = 285 end
elseif __pld_pc == 284 then
__pld_pc = 298
elseif __pld_pc == 285 then
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] - 1
if not (1 <= __pld_R[0]) then __pld_pc = 288 else __pld_pc = 289 end
elseif __pld_pc == 288 then
__pld_pc = 298
elseif __pld_pc == 289 then
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] - 1
l0_3 = __pld_R[0]
__pld_R[0] = l0_13
__pld_R[1] = 1
__pld_R[2] = l0_1
__pld_R[3] = l0_1
__pld_R[4] = l0_3
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_pc = 298
elseif __pld_pc == 298 then
__pld_R[0] = pressButton
__pld_R[1] = "R"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 302 else __pld_pc = 303 end
elseif __pld_pc == 302 then
__pld_pc = 343
elseif __pld_pc == 303 then
__pld_R[0] = l0_4
if not (__pld_R[0] == false) then __pld_pc = 305 else __pld_pc = 306 end
elseif __pld_pc == 305 then
__pld_pc = 343
elseif __pld_pc == 306 then
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] + 1
__pld_R[1] = l0_8
if not (__pld_R[0] <= __pld_R[1]) then __pld_pc = 310 else __pld_pc = 311 end
elseif __pld_pc == 310 then
__pld_pc = 343
elseif __pld_pc == 311 then
__pld_R[0] = l0_3
__pld_R[0] = __pld_R[0] + 1
l0_3 = __pld_R[0]
__pld_R[0] = l0_7
__pld_R[1] = l0_3
__pld_R[1] = __pld_R[1] * 9
__pld_R[0] = __pld_R[0] - __pld_R[1]
if not (__pld_R[0] < 0) then __pld_pc = 319 else __pld_pc = 320 end
elseif __pld_pc == 319 then
__pld_pc = 337
elseif __pld_pc == 320 then
__pld_R[0] = l0_1
__pld_R[1] = l0_7
__pld_R[2] = l0_3
__pld_R[2] = __pld_R[2] - 1
__pld_R[2] = __pld_R[2] * 9
__pld_R[1] = __pld_R[1] - __pld_R[2]
if not (__pld_R[1] < __pld_R[0]) then __pld_pc = 327 else __pld_pc = 328 end
elseif __pld_pc == 327 then
__pld_pc = 335
elseif __pld_pc == 328 then
__pld_R[0] = l0_7
__pld_R[1] = l0_3
__pld_R[1] = __pld_R[1] - 1
__pld_R[1] = __pld_R[1] * 9
__pld_R[0] = __pld_R[0] - __pld_R[1]
if __pld_R[0] then __pld_pc = 334 else __pld_pc = 335 end
elseif __pld_pc == 334 then
__pld_pc = 336
elseif __pld_pc == 335 then
__pld_R[0] = l0_1
__pld_pc = 336
elseif __pld_pc == 336 then
l0_1 = __pld_R[0]
__pld_pc = 337
elseif __pld_pc == 337 then
__pld_R[0] = l0_13
__pld_R[1] = 0
__pld_R[2] = l0_1
__pld_R[3] = l0_1
__pld_R[4] = l0_3
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_pc = 343
elseif __pld_pc == 343 then
__pld_R[0] = pressButton
__pld_R[1] = "CROSS"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 347 else __pld_pc = 348 end
elseif __pld_pc == 347 then
__pld_pc = 356
elseif __pld_pc == 348 then
__pld_R[0] = keyPlaySE
__pld_R[1] = seName
__pld_R[1] = __pld_R[1]["cross"]
__pld_R[0](__pld_R[1])
__pld_R[0] = wait
__pld_R[1] = 10
__pld_R[0](__pld_R[1])
__pld_pc = 756
elseif __pld_pc == 356 then
__pld_R[0] = pressButton
__pld_R[1] = "CIRCLE"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 360 else __pld_pc = 361 end
elseif __pld_pc == 360 then
__pld_pc = 486
elseif __pld_pc == 361 then
__pld_R[0] = l0_4
if not (__pld_R[0] == false) then __pld_pc = 363 else __pld_pc = 364 end
elseif __pld_pc == 363 then
__pld_pc = 486
elseif __pld_pc == 364 then
__pld_R[0] = systemSave
__pld_R[0] = __pld_R[0]["cgFlag"]
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["cgNumber"]
__pld_R[2] = l0_3
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[2] = l0_1
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[1] = __pld_R[1][1]
__pld_R[0] = __pld_R[0][__pld_R[1]]
if not (__pld_R[0] == true) then __pld_pc = 375 else __pld_pc = 376 end
elseif __pld_pc == 375 then
__pld_pc = 486
elseif __pld_pc == 376 then
__pld_R[0] = keyPlaySE
__pld_R[1] = seName
__pld_R[1] = __pld_R[1]["circle"]
__pld_R[0](__pld_R[1])
__pld_R[0] = true
l0_9 = __pld_R[0]
__pld_R[0] = layerLoad
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = cGetFileName
__pld_R[3] = "event"
__pld_R[4] = l0_0
__pld_R[4] = __pld_R[4]["cgNumber"]
__pld_R[5] = l0_3
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[5] = l0_1
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[4] = __pld_R[4][1]
do 
local __pld_rs = __pld_pack(__pld_R[2](__pld_R[3], __pld_R[4]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 2 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 2 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 1 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 1 + __pld_i - 1) end __pld_R[0](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[0] = layerPosition
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = l0_0
__pld_R[2] = __pld_R[2]["viewX"]
__pld_R[3] = l0_1
__pld_R[2] = __pld_R[2][__pld_R[3]]
__pld_R[3] = l0_0
__pld_R[3] = __pld_R[3]["viewY"]
__pld_R[4] = l0_1
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
__pld_R[0] = layerMovePosition
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = 0
__pld_R[3] = 0
__pld_R[4] = 30
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[0] = layerScale
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = 25
__pld_R[3] = 25
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
__pld_R[0] = layerMoveScale
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = 100
__pld_R[3] = 100
__pld_R[4] = 30
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[0] = wait
__pld_R[1] = 30
__pld_R[0](__pld_R[1])
__pld_R[0] = l0_0
__pld_R[0] = __pld_R[0]["cgNumber"]
__pld_R[1] = l0_3
__pld_R[0] = __pld_R[0][__pld_R[1]]
__pld_R[1] = l0_1
__pld_R[0] = __pld_R[0][__pld_R[1]]
__pld_R[0] = #(__pld_R[0])
if not (1 < __pld_R[0]) then __pld_pc = 444 else __pld_pc = 445 end
elseif __pld_pc == 444 then
__pld_pc = 486
elseif __pld_pc == 445 then
__pld_R[0] = 2
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["cgNumber"]
__pld_R[2] = l0_3
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[2] = l0_1
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[1] = #(__pld_R[1])
__pld_R[2] = 1
do
local __pld_i = __pld_tonumber(__pld_R[0]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[1]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[2]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[0] = __pld_i - __pld_s __pld_R[1] = __pld_l __pld_R[2] = __pld_s
end
__pld_pc = 485
elseif __pld_pc == 455 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["cgFlag"]
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["cgNumber"]
__pld_R[6] = l0_3
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[6] = l0_1
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[5] = __pld_R[5][__pld_R[3]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
if not (__pld_R[4] == true) then __pld_pc = 466 else __pld_pc = 467 end
elseif __pld_pc == 466 then
__pld_pc = 485
elseif __pld_pc == 467 then
__pld_R[4] = layerLoadAsync
__pld_R[5] = 0
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerNumber"]
__pld_R[6] = __pld_R[6]["view"]
__pld_R[6] = __pld_R[6] + __pld_R[3]
__pld_R[6] = __pld_R[6] - 1
__pld_R[7] = cGetFileName
__pld_R[8] = "event"
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["cgNumber"]
__pld_R[10] = l0_3
__pld_R[9] = __pld_R[9][__pld_R[10]]
__pld_R[10] = l0_1
__pld_R[9] = __pld_R[9][__pld_R[10]]
__pld_R[9] = __pld_R[9][__pld_R[3]]
do 
local __pld_rs = __pld_pack(__pld_R[7](__pld_R[8], __pld_R[9]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 7 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 7 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_pc = 485
elseif __pld_pc == 485 then
do local __pld_s = __pld_R[2] local __pld_i = __pld_R[0] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[1]) or (__pld_s <= 0 and __pld_i >= __pld_R[1]) then
__pld_R[0] = __pld_i __pld_R[3] = __pld_i __pld_pc = 455
else __pld_pc = 486 end end
elseif __pld_pc == 486 then
__pld_R[0] = l0_4
if not (__pld_R[0] == true) then __pld_pc = 488 else __pld_pc = 489 end
elseif __pld_pc == 488 then
__pld_pc = 752
elseif __pld_pc == 489 then
__pld_R[0] = l0_2
__pld_R[1] = l0_1
if __pld_R[0] == __pld_R[1] then __pld_pc = 492 else __pld_pc = 493 end
elseif __pld_pc == 492 then
__pld_pc = 497
elseif __pld_pc == 493 then
__pld_R[0] = keyPlaySE
__pld_R[1] = seName
__pld_R[1] = __pld_R[1]["arrowKey"]
__pld_R[0](__pld_R[1])
__pld_pc = 497
elseif __pld_pc == 497 then
__pld_R[0] = layerVisible
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["mask"]
__pld_R[2] = l0_2
__pld_R[1] = __pld_R[1] + __pld_R[2]
__pld_R[2] = true
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = layerVisible
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["mask"]
__pld_R[2] = l0_1
__pld_R[1] = __pld_R[1] + __pld_R[2]
__pld_R[2] = false
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = layerMovePosition
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["cursor"]
__pld_R[2] = l0_0
__pld_R[2] = __pld_R[2]["cursorX"]
__pld_R[3] = l0_1
__pld_R[2] = __pld_R[2][__pld_R[3]]
__pld_R[3] = l0_0
__pld_R[3] = __pld_R[3]["cursorY"]
__pld_R[4] = l0_1
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[4] = 5
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[0] = fontClear
__pld_R[0]()
__pld_R[0] = false
l0_4 = __pld_R[0]
__pld_R[0] = wait
__pld_R[1] = 5
__pld_R[0](__pld_R[1])
__pld_pc = 752
elseif __pld_pc == 535 then
__pld_R[0] = pressButton
__pld_R[1] = "CIRCLE"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 539 else __pld_pc = 540 end
elseif __pld_pc == 539 then
__pld_pc = 692
elseif __pld_pc == 540 then
__pld_R[0] = l0_6
__pld_R[0] = __pld_R[0] + 1
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["cgNumber"]
__pld_R[2] = l0_3
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[2] = l0_1
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[1] = #(__pld_R[1])
if not (__pld_R[1] < __pld_R[0]) then __pld_pc = 550 else __pld_pc = 551 end
elseif __pld_pc == 550 then
__pld_pc = 554
elseif __pld_pc == 551 then
__pld_R[0] = (-1)
if __pld_R[0] then __pld_pc = 553 else __pld_pc = 554 end
elseif __pld_pc == 553 then
__pld_pc = 556
elseif __pld_pc == 554 then
__pld_R[0] = l0_6
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 556
elseif __pld_pc == 556 then
l0_6 = __pld_R[0]
__pld_R[0] = l0_6
if not (1 < __pld_R[0]) then __pld_pc = 559 else __pld_pc = 560 end
elseif __pld_pc == 559 then
__pld_pc = 598
elseif __pld_pc == 560 then
__pld_R[0] = l0_6
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["cgNumber"]
__pld_R[2] = l0_3
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[2] = l0_1
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[1] = #(__pld_R[1])
__pld_R[2] = 1
do
local __pld_i = __pld_tonumber(__pld_R[0]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[1]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[2]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[0] = __pld_i - __pld_s __pld_R[1] = __pld_l __pld_R[2] = __pld_s
end
__pld_pc = 597
elseif __pld_pc == 570 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["cgFlag"]
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["cgNumber"]
__pld_R[6] = l0_3
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[6] = l0_1
__pld_R[5] = __pld_R[5][__pld_R[6]]
__pld_R[5] = __pld_R[5][__pld_R[3]]
__pld_R[4] = __pld_R[4][__pld_R[5]]
if not (__pld_R[4] == true) then __pld_pc = 581 else __pld_pc = 582 end
elseif __pld_pc == 581 then
__pld_pc = 585
elseif __pld_pc == 582 then
l0_6 = __pld_R[3]
__pld_pc = 598
elseif __pld_pc == 584 then
__pld_pc = 597
elseif __pld_pc == 585 then
__pld_R[4] = l0_0
__pld_R[4] = __pld_R[4]["cgNumber"]
__pld_R[5] = l0_3
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[5] = l0_1
__pld_R[4] = __pld_R[4][__pld_R[5]]
__pld_R[4] = #(__pld_R[4])
if not (__pld_R[3] == __pld_R[4]) then __pld_pc = 593 else __pld_pc = 594 end
elseif __pld_pc == 593 then
__pld_pc = 597
elseif __pld_pc == 594 then
__pld_R[4] = (-1)
l0_6 = __pld_R[4]
__pld_pc = 598
elseif __pld_pc == 597 then
do local __pld_s = __pld_R[2] local __pld_i = __pld_R[0] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[1]) or (__pld_s <= 0 and __pld_i >= __pld_R[1]) then
__pld_R[0] = __pld_i __pld_R[3] = __pld_i __pld_pc = 570
else __pld_pc = 598 end end
elseif __pld_pc == 598 then
__pld_R[0] = l0_6
if not (__pld_R[0] == (-1)) then __pld_pc = 600 else __pld_pc = 601 end
elseif __pld_pc == 600 then
__pld_pc = 657
elseif __pld_pc == 601 then
__pld_R[0] = keyPlaySE
__pld_R[1] = seName
__pld_R[1] = __pld_R[1]["cross"]
__pld_R[0](__pld_R[1])
__pld_R[0] = layerMoveScale
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = 25
__pld_R[3] = 25
__pld_R[4] = 30
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[0] = layerMovePosition
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = l0_0
__pld_R[2] = __pld_R[2]["viewX"]
__pld_R[3] = l0_1
__pld_R[2] = __pld_R[2][__pld_R[3]]
__pld_R[3] = l0_0
__pld_R[3] = __pld_R[3]["viewY"]
__pld_R[4] = l0_1
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[4] = 30
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[0] = wait
__pld_R[1] = 30
__pld_R[0](__pld_R[1])
__pld_R[0] = 1
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["cgNumber"]
__pld_R[2] = l0_3
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[2] = l0_1
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[1] = #(__pld_R[1])
__pld_R[2] = 1
do
local __pld_i = __pld_tonumber(__pld_R[0]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[1]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[2]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[0] = __pld_i - __pld_s __pld_R[1] = __pld_l __pld_R[2] = __pld_s
end
__pld_pc = 648
elseif __pld_pc == 640 then
__pld_R[4] = layerLoad
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["view"]
__pld_R[5] = __pld_R[5] + __pld_R[3]
__pld_R[5] = __pld_R[5] - 1
__pld_R[6] = ""
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 648
elseif __pld_pc == 648 then
do local __pld_s = __pld_R[2] local __pld_i = __pld_R[0] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[1]) or (__pld_s <= 0 and __pld_i >= __pld_R[1]) then
__pld_R[0] = __pld_i __pld_R[3] = __pld_i __pld_pc = 640
else __pld_pc = 649 end end
elseif __pld_pc == 649 then
__pld_R[0] = wait
__pld_R[1] = 10
__pld_R[0](__pld_R[1])
__pld_R[0] = 1
l0_6 = __pld_R[0]
__pld_R[0] = false
l0_9 = __pld_R[0]
__pld_pc = 692
elseif __pld_pc == 657 then
__pld_R[0] = layerIsLoad
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = l0_6
__pld_R[1] = __pld_R[1] + __pld_R[2]
__pld_R[1] = __pld_R[1] - 1
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 666 else __pld_pc = 667 end
elseif __pld_pc == 666 then
__pld_pc = 668
elseif __pld_pc == 667 then
__pld_pc = 672
elseif __pld_pc == 668 then
__pld_R[0] = wait
__pld_R[1] = 1
__pld_R[0](__pld_R[1])
__pld_pc = 657
elseif __pld_pc == 672 then
__pld_R[0] = keyPlaySE
__pld_R[1] = seName
__pld_R[1] = __pld_R[1]["circle"]
__pld_R[0](__pld_R[1])
__pld_R[0] = layerCopy
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = l0_0
__pld_R[2] = __pld_R[2]["layerNumber"]
__pld_R[2] = __pld_R[2]["view"]
__pld_R[3] = l0_6
__pld_R[2] = __pld_R[2] + __pld_R[3]
__pld_R[2] = __pld_R[2] - 1
__pld_R[0](__pld_R[1], __pld_R[2])
__pld_R[0] = switchScreen
__pld_R[1] = 0
__pld_R[2] = ""
__pld_R[3] = 30
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
__pld_pc = 692
elseif __pld_pc == 692 then
__pld_R[0] = pressButton
__pld_R[1] = "CROSS"
__pld_R[0] = __pld_R[0](__pld_R[1])
if not (__pld_R[0] == true) then __pld_pc = 696 else __pld_pc = 697 end
elseif __pld_pc == 696 then
__pld_pc = 752
elseif __pld_pc == 697 then
__pld_R[0] = keyPlaySE
__pld_R[1] = seName
__pld_R[1] = __pld_R[1]["cross"]
__pld_R[0](__pld_R[1])
__pld_R[0] = layerMoveScale
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = 25
__pld_R[3] = 25
__pld_R[4] = 30
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[0] = layerMovePosition
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["layerNumber"]
__pld_R[1] = __pld_R[1]["view"]
__pld_R[2] = l0_0
__pld_R[2] = __pld_R[2]["viewX"]
__pld_R[3] = l0_1
__pld_R[2] = __pld_R[2][__pld_R[3]]
__pld_R[3] = l0_0
__pld_R[3] = __pld_R[3]["viewY"]
__pld_R[4] = l0_1
__pld_R[3] = __pld_R[3][__pld_R[4]]
__pld_R[4] = 30
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3], __pld_R[4])
__pld_R[0] = wait
__pld_R[1] = 30
__pld_R[0](__pld_R[1])
__pld_R[0] = 1
__pld_R[1] = l0_0
__pld_R[1] = __pld_R[1]["cgNumber"]
__pld_R[2] = l0_3
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[2] = l0_1
__pld_R[1] = __pld_R[1][__pld_R[2]]
__pld_R[1] = #(__pld_R[1])
__pld_R[2] = 1
do
local __pld_i = __pld_tonumber(__pld_R[0]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[1]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[2]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[0] = __pld_i - __pld_s __pld_R[1] = __pld_l __pld_R[2] = __pld_s
end
__pld_pc = 744
elseif __pld_pc == 736 then
__pld_R[4] = layerLoad
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["view"]
__pld_R[5] = __pld_R[5] + __pld_R[3]
__pld_R[5] = __pld_R[5] - 1
__pld_R[6] = ""
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 744
elseif __pld_pc == 744 then
do local __pld_s = __pld_R[2] local __pld_i = __pld_R[0] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[1]) or (__pld_s <= 0 and __pld_i >= __pld_R[1]) then
__pld_R[0] = __pld_i __pld_R[3] = __pld_i __pld_pc = 736
else __pld_pc = 745 end end
elseif __pld_pc == 745 then
__pld_R[0] = wait
__pld_R[1] = 10
__pld_R[0](__pld_R[1])
__pld_R[0] = 1
l0_6 = __pld_R[0]
__pld_R[0] = false
l0_9 = __pld_R[0]
__pld_pc = 752
elseif __pld_pc == 752 then
__pld_R[0] = wait
__pld_R[1] = 2
__pld_R[0](__pld_R[1])
__pld_pc = 32
elseif __pld_pc == 756 then
__pld_R[0] = cInitGame
__pld_R[0]()
__pld_R[0] = switchScreen
__pld_R[1] = 0
__pld_R[2] = ""
__pld_R[3] = 60
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
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

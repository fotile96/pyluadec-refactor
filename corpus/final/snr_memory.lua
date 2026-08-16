local l0_0 = {layerName = {memory_01_a = 50, graphic_02_a = 51, graphic_03_a = 52, graphic_04_a = 53, graphic_05_a = 54, graphic_06_a = 55, graphic_07_a = 64, memoryThumbnail_1_a = 56, memoryThumbnail_2_a = 57}, layerNumber = {bg = 0, thumbnail = 2, mask = 11, complete = 31, key = 32, cursor = 34, view = 35}, thumbnailName = {"memoryThumbnail_1_a", "memoryThumbnail_2_a"}, viewX = {}, viewY = {}, cursorX = {}, cursorY = {}, memoryNumber = {}, doScriptScene = {snr_s0_10_f = "sof_10", snr_s1_10_f = "s1f-10", snr_s2_10_f = "s2f-10", snr_s3_10_fa = "s3fa-10", snr_s3_10_fb = "s3fb-10", snr_s3_10_fc = "s3fc-10", snr_s4_10_fa = "s4fa-10", snr_s4_10_fb = "s4fb-10", snr_s5_10_f = "s5f-10", snr_s6_10_f = "s6f-10", snr_s7_10_f = "s7f-10", snr_s8_10_f = "s8f-10", snr_e1_10_f = "e1f-10", snr_e2_10_f = "e2f-10"}}
l0_0.memoryNumber[1] = {"snr_s0_10_f", "snr_s1_10_f", "snr_s2_10_f", "snr_s3_10_fa", "snr_s3_10_fb", "snr_s3_10_fc", "snr_s4_10_fa", "snr_s4_10_fb", "snr_s5_10_f"}
l0_0.memoryNumber[2] = {"snr_s6_10_f", "snr_s7_10_f", "snr_s8_10_f", "snr_e1_10_f", "snr_e2_10_f"}
local l0_1 = 1
local l0_2 = 0
local l0_3 = 1
local l0_4 = false
local l0_5 = 0
for l0_9, l0_10 in pairs(systemSave.memoryFlag) do
    if l0_10 == true then
        l0_5 = l0_5 + 1
    end
end
local l0_6 = 1
local l0_7 = 14
local l0_8 = math.ceil(l0_7 / 9)
local l0_9 = false
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
    layerCopy(l0_0.layerNumber.bg + 1, l0_0.layerName.memory_01_a)
    local l1_0 = 0
    local l1_1 = 0
    for l1_5 = 1, 9, 1 do
        layerCopy(l0_0.layerNumber.mask + l1_5, l0_0.layerName.graphic_02_a)
        layerPosition(l0_0.layerNumber.mask + l1_5, 30 + l1_0 * 130, 50 + l1_1 * 73)
        if systemSave.memoryFlag[l0_0.memoryNumber[l0_3][l1_5]] == true then
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
    switchScreen(0, "", 60)
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
__pld_pc = 280
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
__pld_R[12] = __pld_R[12]["memoryFlag"]
__pld_R[13] = l0_0
__pld_R[13] = __pld_R[13]["memoryNumber"]
__pld_R[13] = __pld_R[13][__pld_R[3]]
__pld_R[13] = __pld_R[13][__pld_R[11]]
__pld_R[12] = __pld_R[12][__pld_R[13]]
if not (__pld_R[12] == true) then __pld_pc = 185 else __pld_pc = 186 end
elseif __pld_pc == 185 then
__pld_pc = 206
elseif __pld_pc == 186 then
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
__pld_pc = 206
elseif __pld_pc == 206 then
if not (__pld_R[0] == 0) then __pld_pc = 207 else __pld_pc = 208 end
elseif __pld_pc == 207 then
__pld_pc = 231
elseif __pld_pc == 208 then
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
__pld_pc = 253
elseif __pld_pc == 231 then
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
__pld_pc = 253
elseif __pld_pc == 253 then
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
if not (3 <= __pld_R[4]) then __pld_pc = 277 else __pld_pc = 278 end
elseif __pld_pc == 277 then
__pld_pc = 280
elseif __pld_pc == 278 then
__pld_R[4] = 0
__pld_R[5] = __pld_R[5] + 1
__pld_pc = 280
elseif __pld_pc == 280 then
do local __pld_s = __pld_R[10] local __pld_i = __pld_R[8] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[9]) or (__pld_s <= 0 and __pld_i >= __pld_R[9]) then
__pld_R[8] = __pld_i __pld_R[11] = __pld_i __pld_pc = 168
else __pld_pc = 281 end end
elseif __pld_pc == 281 then
if not (__pld_R[0] == 0) then __pld_pc = 282 else __pld_pc = 283 end
elseif __pld_pc == 282 then
__pld_pc = 309
elseif __pld_pc == 283 then
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
__pld_pc = 334
elseif __pld_pc == 309 then
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
__pld_pc = 334
elseif __pld_pc == 334 then
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
if __pld_R[3] == 1 then __pld_pc = 352 else __pld_pc = 353 end
elseif __pld_pc == 352 then
__pld_pc = 377
elseif __pld_pc == 353 then
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
__pld_pc = 377
elseif __pld_pc == 377 then
__pld_R[8] = l0_8
if not (__pld_R[3] < __pld_R[8]) then __pld_pc = 379 else __pld_pc = 380 end
elseif __pld_pc == 379 then
__pld_pc = 407
elseif __pld_pc == 380 then
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
__pld_pc = 407
elseif __pld_pc == 407 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end
main = function()
    memoryFlag = true
    systemConfig.unsetConfigButton()
    logEnable(false)
    advPart(false)
    cInitGame()
    startLoading()
    for l1_3, l1_4 in pairs(l0_0.layerName) do
        comLayerLoadFalse(l1_4, "graphic/" .. l1_3 .. ".gim")
    end
    waitLoading()
    endLoading()
    l0_12()
    while true do
        if pressButton("UP") == true then
            if l0_4 == false then
                l0_2 = l0_1
                local l1_0 = l0_1 - 3 < 1 and l0_1 or l0_1 - 3
                l0_1 = l1_0
                l1_0 = true
                l0_4 = l1_0
            end
        end
        if pressButton("DOWN") == true then
            if l0_4 == false then
                l0_2 = l0_1
                if l0_7 - l0_3 * 9 < 0 then
                    local l1_0 = l0_1 + 3 > l0_7 - (l0_3 - 1) * 9 and l0_1 or l0_1 + 3
                    l0_1 = l1_0
                else
                    local l1_0 = 9 < l0_1 + 3 and l0_1 or l0_1 + 3
                    l0_1 = l1_0
                end
                l0_4 = true
            end
        end
        if pressButton("RIGHT") == true then
            if l0_4 == false then
                l0_2 = l0_1
                if l0_3 + 1 <= l0_8 then
                    if l0_1 == 3 or l0_1 == 6 or l0_1 == 9 then
                        l0_3 = l0_3 + 1
                        l0_1 = l0_1 - 2
                        if l0_7 - l0_3 * 9 < 0 then
                            local l1_0 = l0_1 > l0_7 - (l0_3 - 1) * 9 and l0_7 - (l0_3 - 1) * 9 or l0_1
                            l0_1 = l1_0
                        end
                        l0_13(0, l0_2, l0_1, l0_3)
                    else
                        local l1_0 = l0_1 + 1 > l0_7 - (l0_3 - 1) * 9 and l0_1 or l0_1 + 1
                        l0_1 = l1_0
                        l1_0 = l0_1
                        if l1_0 == l0_2 then
                        end
                        l1_0 = true
                        l0_4 = l1_0
                    end
                elseif not (l0_1 == 3) then
                    if not (l0_1 == 6) then
                        if not (l0_1 == 9) then
                            local l1_0 = l0_1 + 1 > l0_7 - (l0_3 - 1) * 9 and l0_1 or l0_1 + 1
                            l0_1 = l1_0
                            l1_0 = l0_1
                            if l1_0 == l0_2 then
                            end
                            l1_0 = true
                            l0_4 = l1_0
                        end
                    end
                end
            end
        end
        if pressButton("LEFT") == true then
            if l0_4 == false then
                l0_2 = l0_1
                if 1 <= l0_3 - 1 then
                    if l0_1 == 1 or l0_1 == 4 or l0_1 == 7 then
                        l0_3 = l0_3 - 1
                        l0_1 = l0_1 + 2
                        l0_13(1, l0_2, l0_1, l0_3)
                        l0_4 = true
                    else
                        l0_1 = l0_1 - 1
                        if l0_1 == l0_2 then
                        end
                        l0_4 = true
                    end
                elseif not (l0_1 == 1) then
                    if not (l0_1 == 4) then
                        if not (l0_1 == 7) then
                            l0_1 = l0_1 - 1
                            if l0_1 == l0_2 then
                            end
                            l0_4 = true
                        end
                    end
                end
            end
        end
        if pressButton("L") == true then
            if l0_4 == false then
                if 1 <= l0_3 - 1 then
                    l0_3 = l0_3 - 1
                    l0_13(1, l0_1, l0_1, l0_3)
                end
            end
        end
        if pressButton("R") == true then
            if l0_4 == false then
                if l0_3 + 1 <= l0_8 then
                    l0_3 = l0_3 + 1
                    if l0_7 - l0_3 * 9 < 0 then
                        local l1_0 = l0_1 > l0_7 - (l0_3 - 1) * 9 and l0_7 - (l0_3 - 1) * 9 or l0_1
                        l0_1 = l1_0
                    end
                    l0_13(0, l0_1, l0_1, l0_3)
                end
            end
        end
        if pressButton("CROSS") == true then
            keyPlaySE(seName.cross)
            wait(5)
            break
        end
        if pressButton("CIRCLE") == true then
            if l0_4 == false then
                if systemSave.memoryFlag[l0_0.memoryNumber[l0_3][l0_1]] == true then
                    keyPlaySE(seName.circle)
                    wait(10)
                    cInitGame()
                    switchScreen(0, "", 60)
                    doScriptScene = l0_0.doScriptScene[l0_0.memoryNumber[l0_3][l0_1]]
                    run(cGetFileName("script", l0_0.memoryNumber[l0_3][l0_1]))
                    quit()
                end
            end
        end
        if l0_4 == true then
            if not (l0_2 == l0_1) then
                keyPlaySE(seName.arrowKey)
            end
            layerVisible(l0_0.layerNumber.mask + l0_2, true)
            layerVisible(l0_0.layerNumber.mask + l0_1, false)
            layerMovePosition(l0_0.layerNumber.cursor, l0_0.cursorX[l0_1], l0_0.cursorY[l0_1], 5)
            fontClear()
            l0_4 = false
            wait(5)
        end
        wait(2)
    end
    memoryFlag = false
    cInitGame()
    switchScreen(0, "", 60)
    run(cGetFileName("script", "snr_mainmenu"))
end

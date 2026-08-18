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
local l0_13 = function(l1_0, l1_1, l1_2, l1_3)
    local l1_4 = 0
    local l1_5 = 0
    layerLoad(l0_0.layerNumber.key, "")
    layerLoad(l0_0.layerNumber.key + 1, "")
    local l1_6 = l0_7 - l1_3 * 9 < 0 and l0_7 - (l1_3 - 1) * 9 or 9
    local l1_7 = l1_0 == 0 and 9 or l0_7 - l1_3 * 9
    l1_7 = 9 < l1_7 and 9 or l1_7
    for l1_11 = 1, l1_7, 1 do
        if l1_0 == 0 then
            layerMovePosition(l0_0.layerNumber.mask + l1_11, l1_4 * 130 - 480, 50 + l1_5 * 73, 20)
            layerMovePosition(l0_0.layerNumber.thumbnail + l1_11, l1_4 * 130 - 480, 50 + l1_5 * 73, 20)
        else
            layerMovePosition(l0_0.layerNumber.mask + l1_11, l1_4 * 130 + 480, 50 + l1_5 * 73, 20)
            layerMovePosition(l0_0.layerNumber.thumbnail + l1_11, l1_4 * 130 + 480, 50 + l1_5 * 73, 20)
        end
        l1_4 = l1_4 + 1
        if l1_4 >= 3 then
            l1_4 = 0
            l1_5 = l1_5 + 1
        end
    end
    if l1_0 == 0 then
        layerMovePosition(l0_0.layerNumber.cursor, l0_0.cursorX[l1_1] - 480, l0_0.cursorY[l1_1], 20)
    else
        layerMovePosition(l0_0.layerNumber.cursor, l0_0.cursorX[l1_1] + 480, l0_0.cursorY[l1_1], 20)
    end
    wait(20)
    l0_10(25, 460, 2, l1_3 < 10 and "0" .. l1_3 or l1_3)
    for l1_11 = 1, l1_7, 1 do
        layerLoad(l0_0.layerNumber.mask + l1_11, "")
        layerLoad(l0_0.layerNumber.thumbnail + l1_11, "")
    end
    l1_4 = 0
    l1_5 = 0
    for l1_11 = 1, l1_6, 1 do
        layerCopy(l0_0.layerNumber.mask + l1_11, l0_0.layerName.graphic_02_a)
        if systemSave.cgFlag[l0_0.cgNumber[l1_3][l1_11][1]] == true then
            layerCopy(l0_0.layerNumber.thumbnail + l1_11, l0_0.layerName[l0_0.thumbnailName[l1_3]])
            l0_11(l0_0.layerNumber.thumbnail + l1_11, l1_4, l1_5)
        end
        if l1_0 == 0 then
            layerPosition(l0_0.layerNumber.mask + l1_11, 30 + l1_4 * 130 + 480, 50 + l1_5 * 73)
            layerPosition(l0_0.layerNumber.thumbnail + l1_11, 30 + l1_4 * 130 + 480, 50 + l1_5 * 73)
        else
            layerPosition(l0_0.layerNumber.mask + l1_11, 30 + l1_4 * 130 - 480, 50 + l1_5 * 73)
            layerPosition(l0_0.layerNumber.thumbnail + l1_11, 30 + l1_4 * 130 - 480, 50 + l1_5 * 73)
        end
        layerMovePosition(l0_0.layerNumber.mask + l1_11, 30 + l1_4 * 130, 50 + l1_5 * 73, 20)
        layerMovePosition(l0_0.layerNumber.thumbnail + l1_11, 30 + l1_4 * 130, 50 + l1_5 * 73, 20)
        l1_4 = l1_4 + 1
        if 3 <= l1_4 then
            l1_4 = 0
            l1_5 = l1_5 + 1
        end
    end
    if l1_0 == 0 then
        layerPosition(l0_0.layerNumber.cursor, l0_0.cursorX[l1_2] + 480, l0_0.cursorY[l1_2], 20)
        layerMovePosition(l0_0.layerNumber.cursor, l0_0.cursorX[l1_2], l0_0.cursorY[l1_2], 20)
    else
        layerPosition(l0_0.layerNumber.cursor, l0_0.cursorX[l1_2] - 480, l0_0.cursorY[l1_2], 20)
        layerMovePosition(l0_0.layerNumber.cursor, l0_0.cursorX[l1_2], l0_0.cursorY[l1_2], 20)
    end
    layerVisible(l0_0.layerNumber.mask + l1_1, true)
    layerVisible(l0_0.layerNumber.mask + l1_2, false)
    wait(20)
    if not (l1_3 == 1) then
        layerCopy(l0_0.layerNumber.key, l0_0.layerName.graphic_06_a)
        layerClip(l0_0.layerNumber.key, 0, 0, 12, 18)
        layerPosition(l0_0.layerNumber.key, 5, 130)
    end
    if l1_3 < l0_8 then
        layerCopy(l0_0.layerNumber.key + 1, l0_0.layerName.graphic_05_a)
        layerClip(l0_0.layerNumber.key + 1, 0, 0, 12, 18)
        layerPosition(l0_0.layerNumber.key + 1, 463, 130)
    end
end
main = function()
advPart(false)
logEnable(false)
systemConfig.unsetConfigButton()
startLoading()
for l1_3, l1_4 in pairs(l0_0.layerName) do
    comLayerLoadFalse(l1_4, "graphic/" .. l1_3 .. ".gim")
end
waitLoading()
endLoading()
l0_12()
while true do
    if l0_9 == false then
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
            wait(10)
            break
        end
        if pressButton("CIRCLE") == true then
            if l0_4 == false then
                if systemSave.cgFlag[l0_0.cgNumber[l0_3][l0_1][1]] == true then
                    keyPlaySE(seName.circle)
                    l0_9 = true
                    layerLoad(l0_0.layerNumber.view, cGetFileName("event", l0_0.cgNumber[l0_3][l0_1][1]))
                    layerPosition(l0_0.layerNumber.view, l0_0.viewX[l0_1], l0_0.viewY[l0_1])
                    layerMovePosition(l0_0.layerNumber.view, 0, 0, 30)
                    layerScale(l0_0.layerNumber.view, 25, 25)
                    layerMoveScale(l0_0.layerNumber.view, 100, 100, 30)
                    wait(30)
                    if 1 < #l0_0.cgNumber[l0_3][l0_1] then
                        for l1_3 = 2, #l0_0.cgNumber[l0_3][l0_1], 1 do
                            if systemSave.cgFlag[l0_0.cgNumber[l0_3][l0_1][l1_3]] == true then
                                layerLoadAsync(0, l0_0.layerNumber.view + l1_3 - 1, cGetFileName("event", l0_0.cgNumber[l0_3][l0_1][l1_3]))
                            end
                        end
                    end
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
    else
        if pressButton("CIRCLE") == true then
            l0_6 = l0_6 + 1 > #l0_0.cgNumber[l0_3][l0_1] and -1 or l0_6 + 1
            if 1 < l0_6 then
                for l1_3 = l0_6, #l0_0.cgNumber[l0_3][l0_1], 1 do
                    if systemSave.cgFlag[l0_0.cgNumber[l0_3][l0_1][l1_3]] == true then
                        l0_6 = l1_3
                        break
                    elseif l1_3 == #l0_0.cgNumber[l0_3][l0_1] then
                        l0_6 = -1
                        break
                    end
                end
            end
            if l0_6 == -1 then
                keyPlaySE(seName.cross)
                layerMoveScale(l0_0.layerNumber.view, 25, 25, 30)
                layerMovePosition(l0_0.layerNumber.view, l0_0.viewX[l0_1], l0_0.viewY[l0_1], 30)
                wait(30)
                for l1_3 = 1, #l0_0.cgNumber[l0_3][l0_1], 1 do
                    layerLoad(l0_0.layerNumber.view + l1_3 - 1, "")
                end
                wait(10)
                l0_6 = 1
                l0_9 = false
            else
                while true do
                    if layerIsLoad(l0_0.layerNumber.view + l0_6 - 1) == true then
                        break
                    end
                    wait(1)
                end
                keyPlaySE(seName.circle)
                layerCopy(l0_0.layerNumber.view, l0_0.layerNumber.view + l0_6 - 1)
                switchScreen(0, "", 30)
            end
        end
        if pressButton("CROSS") == true then
            keyPlaySE(seName.cross)
            layerMoveScale(l0_0.layerNumber.view, 25, 25, 30)
            layerMovePosition(l0_0.layerNumber.view, l0_0.viewX[l0_1], l0_0.viewY[l0_1], 30)
            wait(30)
            for l1_3 = 1, #l0_0.cgNumber[l0_3][l0_1], 1 do
                layerLoad(l0_0.layerNumber.view + l1_3 - 1, "")
            end
            wait(10)
            l0_6 = 1
            l0_9 = false
        end
    end
    wait(2)
end
cInitGame()
switchScreen(0, "", 60)
run(cGetFileName("script", "snr_mainmenu"))
end

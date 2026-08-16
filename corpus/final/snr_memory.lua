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
        if systemSave.memoryFlag[l0_0.memoryNumber[l1_3][l1_11]] == true then
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

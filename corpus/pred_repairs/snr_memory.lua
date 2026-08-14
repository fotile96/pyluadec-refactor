local v0 = {}
local v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15
v0.layerName = {}
v0.layerName.memory_01_a = 50
v0.layerName.graphic_02_a = 51
v0.layerName.graphic_03_a = 52
v0.layerName.graphic_04_a = 53
v0.layerName.graphic_05_a = 54
v0.layerName.graphic_06_a = 55
v0.layerName.graphic_07_a = 64
v0.layerName.memoryThumbnail_1_a = 56
v0.layerName.memoryThumbnail_2_a = 57
v0.layerNumber = {}
v0.layerNumber.bg = 0
v0.layerNumber.thumbnail = 2
v0.layerNumber.mask = 11
v0.layerNumber.complete = 31
v0.layerNumber.key = 32
v0.layerNumber.cursor = 34
v0.layerNumber.view = 35
v0.thumbnailName = {}
v2 = "memoryThumbnail_1_a"
v3 = "memoryThumbnail_2_a"
v0.thumbnailName[1] = v2
v0.thumbnailName[2] = v3
v0.viewX = {}
v0.viewY = {}
v0.cursorX = {}
v0.cursorY = {}
v0.memoryNumber = {}
v0.doScriptScene = {}
v0.doScriptScene.snr_s0_10_f = "sof_10"
v0.doScriptScene.snr_s1_10_f = "s1f-10"
v0.doScriptScene.snr_s2_10_f = "s2f-10"
v0.doScriptScene.snr_s3_10_fa = "s3fa-10"
v0.doScriptScene.snr_s3_10_fb = "s3fb-10"
v0.doScriptScene.snr_s3_10_fc = "s3fc-10"
v0.doScriptScene.snr_s4_10_fa = "s4fa-10"
v0.doScriptScene.snr_s4_10_fb = "s4fb-10"
v0.doScriptScene.snr_s5_10_f = "s5f-10"
v0.doScriptScene.snr_s6_10_f = "s6f-10"
v0.doScriptScene.snr_s7_10_f = "s7f-10"
v0.doScriptScene.snr_s8_10_f = "s8f-10"
v0.doScriptScene.snr_e1_10_f = "e1f-10"
v0.doScriptScene.snr_e2_10_f = "e2f-10"
v0.memoryNumber[1] = {}
v3 = "snr_s0_10_f"
v4 = "snr_s1_10_f"
v5 = "snr_s2_10_f"
v6 = "snr_s3_10_fa"
v7 = "snr_s3_10_fb"
v8 = "snr_s3_10_fc"
v9 = "snr_s4_10_fa"
v10 = "snr_s4_10_fb"
v11 = "snr_s5_10_f"
v0.memoryNumber[1][1] = v3
v0.memoryNumber[1][2] = v4
v0.memoryNumber[1][3] = v5
v0.memoryNumber[1][4] = v6
v0.memoryNumber[1][5] = v7
v0.memoryNumber[1][6] = v8
v0.memoryNumber[1][7] = v9
v0.memoryNumber[1][8] = v10
v0.memoryNumber[1][9] = v11
v0.memoryNumber[2] = {}
v3 = "snr_s6_10_f"
v4 = "snr_s7_10_f"
v5 = "snr_s8_10_f"
v6 = "snr_e1_10_f"
v7 = "snr_e2_10_f"
v0.memoryNumber[2][1] = v3
v0.memoryNumber[2][2] = v4
v0.memoryNumber[2][3] = v5
v0.memoryNumber[2][4] = v6
v0.memoryNumber[2][5] = v7
v1 = 1
v2 = 0
v3 = 1
v4 = false
v5 = 0
v7 = systemSave.memoryFlag
v6, v7, v8 = pairs(v7)
for v9, v10 in v6, v7, v8 do
    if v10 == true then
        v5 = v5 + 1
    end
end
v6 = 1
v7 = 14
v8 = math.ceil((v7 / 9))
v9 = false
v10 = function(p0, p1, p2, p3)
    local v1 = 1
    local v2, v3, i4, v4, v5, v6, v7, v8
    v2 = string.len(p3)
    v3 = 1
    for i4 = v1, v2, v3 do
        v4 = string.sub(p3, i4, i4)
        v5 = (p0 + i4) - 1
        layerCopy(v5, v0.layerName.graphic_03_a)
        v5 = (p0 + i4) - 1
        v6 = 7 * (i4 - 1)
        layerPosition(v5, (p1 + v6), p2)
        v5 = (p0 + i4) - 1
        v7 = v4 * 7
        v8 = (v4 + 1) * 7
        layerClip(v5, 0, v7, 7, v8)
    end
end
v11 = function(p0, p1, p2)
    local v0, v1, v2, v3
    v0 = p1 * 120
    v1 = p2 * 68
    v2 = (p1 + 1) * 120
    v3 = (p2 + 1) * 68
    layerClip(p0, v0, v1, v2, v3)
end
v12 = function()
    local v1 = layerLoad
    local v2, v4, v6, v8, i2, v9, v12, v13, v14
    v1(v0.layerNumber.bg, cGetFileName("bg", "bg_1_a_0"))
    layerCopy((v0.layerNumber.bg + 1), v0.layerName.memory_01_a)
    v1 = 0
    v2 = 0
    v4 = 1
    v6 = 9
    v8 = 1
    for i2 = v4, v6, v8 do
        layerCopy((v0.layerNumber.mask + i2), v0.layerName.graphic_02_a)
        v9 = v0.layerNumber.mask + i2
        v12 = 30 + (v1 * 130)
        layerPosition(v9, v12, (50 + (v2 * 73)))
        if systemSave.memoryFlag[v0.memoryNumber[v3][i2]] == true then
            layerCopy((v0.layerNumber.thumbnail + i2), v0.layerName[v0.thumbnailName[v3]])
            v11((v0.layerNumber.thumbnail + i2), v1, v2)
            v9 = v0.layerNumber.thumbnail + i2
            v12 = 30 + (v1 * 130)
            layerPosition(v9, v12, (50 + (v2 * 73)))
        end
        v9 = 30 + (v1 * 130)
        v0.cursorX[i2] = v9
        v9 = 50 + (v2 * 73)
        v0.cursorY[i2] = v9
        v9 = (v1 * 130) - 150
        v0.viewX[i2] = v9
        v9 = (v2 * 73) - 52
        v0.viewY[i2] = v9
        v1 = v1 + 1
        if 3 <= v1 then
            v1 = 0
            v2 = v2 + 1
        end
    end
    v10(25, 460, 2, "01")
    v10(27, 387, 40, v7)
    v4 = v10
    v6 = 29
    v8 = 357
    i2 = 40
    if v5 < 10 then
        v14 = "0"
        v9 = v5
        v14 = v14 .. v9
    else
        v14 = v5
    end
    v4(v6, v8, i2, v14)
    v4 = v5
    if v4 == v7 then
        layerCopy(v0.layerNumber.complete, v0.layerName.graphic_04_a)
    end
    layerPosition(v0.layerNumber.complete, 410, 40)
    layerCopy(v0.layerNumber.key, v0.layerName.graphic_05_a)
    layerClip(v0.layerNumber.key, 0, 0, 12, 18)
    layerPosition(v0.layerNumber.key, 463, 130)
    layerVisible((v0.layerNumber.mask + 1), false)
    layerCopy(v0.layerNumber.cursor, v0.layerName.graphic_07_a)
    layerPosition(v0.layerNumber.cursor, v0.cursorX[1], v0.cursorY[1])
    switchScreen(0, "", 60)
end
v13 = function(p0, p1, p2, p3)
    local v1 = 0
    local v2 = 0
    local v3, v4, v5, v6, v9, i8, v12, v13, v14, v15
    layerLoad(v0.layerNumber.key, "")
    layerLoad((v0.layerNumber.key + 1), "")
    v4 = v7
    v3 = p3 * 9
    v4 = v4 - v3
    if v4 < 0 then
        v4 = v7
        v3 = (p3 - 1) * 9
        v4 = v4 - v3
    else
        v4 = 9
    end
    if p0 == 0 then
        v3 = 9
    else
        v3 = v7
        v5 = p3 * 9
        v3 = v3 - v5
    end
    if 9 < v3 then
        v5 = 9
        v3 = v5 or v3
    end
    v5 = 1
    v6 = v3
    v9 = 1
    for i8 = v5, v6, v9 do
        if p0 == 0 then
            v12 = v0.layerNumber.mask + i8
            v13 = (v1 * 130) - 480
            layerMovePosition(v12, v13, (50 + (v2 * 73)), 20)
            v12 = v0.layerNumber.thumbnail + i8
            v13 = (v1 * 130) - 480
            layerMovePosition(v12, v13, (50 + (v2 * 73)), 20)
        else
            v12 = v0.layerNumber.mask + i8
            v13 = (v1 * 130) + 480
            layerMovePosition(v12, v13, (50 + (v2 * 73)), 20)
            v12 = v0.layerNumber.thumbnail + i8
            v13 = (v1 * 130) + 480
            layerMovePosition(v12, v13, (50 + (v2 * 73)), 20)
        end
        v1 = v1 + 1
        if 3 <= v1 then
            v1 = 0
            v2 = v2 + 1
        end
    end
    if p0 == 0 then
        layerMovePosition(v0.layerNumber.cursor, (v0.cursorX[p1] - 480), v0.cursorY[p1], 20)
    else
        layerMovePosition(v0.layerNumber.cursor, (v0.cursorX[p1] + 480), v0.cursorY[p1], 20)
    end
    wait(20)
    v5 = v10
    v6 = 25
    v9 = 460
    i8 = 2
    if p3 < 10 then
        v15 = "0"
        v12 = p3
        v15 = v15 .. v12
    else
        v15 = p3
    end
    v5(v6, v9, i8, v15)
    v5 = 1
    v6 = v3
    v9 = 1
    for i8 = v5, v6, v9 do
        layerLoad((v0.layerNumber.mask + i8), "")
        layerLoad((v0.layerNumber.thumbnail + i8), "")
    end
    v1 = 0
    v2 = 0
    v5 = 1
    v6 = v4
    v9 = 1
    for i8 = v5, v6, v9 do
        layerCopy((v0.layerNumber.mask + i8), v0.layerName.graphic_02_a)
        if systemSave.memoryFlag[v0.memoryNumber[p3][i8]] == true then
            layerCopy((v0.layerNumber.thumbnail + i8), v0.layerName[v0.thumbnailName[p3]])
            v11((v0.layerNumber.thumbnail + i8), v1, v2)
        end
        if p0 == 0 then
            v12 = v0.layerNumber.mask + i8
            v13 = (30 + (v1 * 130)) + 480
            layerPosition(v12, v13, (50 + (v2 * 73)))
            v12 = v0.layerNumber.thumbnail + i8
            v13 = (30 + (v1 * 130)) + 480
            layerPosition(v12, v13, (50 + (v2 * 73)))
        else
            v12 = v0.layerNumber.mask + i8
            v13 = (30 + (v1 * 130)) - 480
            layerPosition(v12, v13, (50 + (v2 * 73)))
            v12 = v0.layerNumber.thumbnail + i8
            v13 = (30 + (v1 * 130)) - 480
            layerPosition(v12, v13, (50 + (v2 * 73)))
        end
        v12 = v0.layerNumber.mask + i8
        v13 = 30 + (v1 * 130)
        layerMovePosition(v12, v13, (50 + (v2 * 73)), 20)
        v12 = v0.layerNumber.thumbnail + i8
        v13 = 30 + (v1 * 130)
        layerMovePosition(v12, v13, (50 + (v2 * 73)), 20)
        v1 = v1 + 1
        if 3 <= v1 then
            v1 = 0
            v2 = v2 + 1
        end
    end
    if p0 == 0 then
        layerPosition(v0.layerNumber.cursor, (v0.cursorX[p2] + 480), v0.cursorY[p2], 20)
        layerMovePosition(v0.layerNumber.cursor, v0.cursorX[p2], v0.cursorY[p2], 20)
    else
        layerPosition(v0.layerNumber.cursor, (v0.cursorX[p2] - 480), v0.cursorY[p2], 20)
        layerMovePosition(v0.layerNumber.cursor, v0.cursorX[p2], v0.cursorY[p2], 20)
    end
    layerVisible((v0.layerNumber.mask + p1), true)
    layerVisible((v0.layerNumber.mask + p2), false)
    wait(20)
    if not (p3 == 1) then
        layerCopy(v0.layerNumber.key, v0.layerName.graphic_06_a)
        layerClip(v0.layerNumber.key, 0, 0, 12, 18)
        layerPosition(v0.layerNumber.key, 5, 130)
    end
    if p3 < v8 then
        layerCopy((v0.layerNumber.key + 1), v0.layerName.graphic_05_a)
        layerClip((v0.layerNumber.key + 1), 0, 0, 12, 18)
        layerPosition((v0.layerNumber.key + 1), 463, 130)
    end
end
main = function()
    local v5, v6, v9, g3, g4, v10, v11, v14
    memoryFlag = true
    systemConfig.unsetConfigButton()
    logEnable(false)
    advPart(false)
    cInitGame()
    startLoading()
    v5 = v0.layerName
    v6, v5, v9 = pairs(v5)
    for g3, g4 in v6, v5, v9 do
        comLayerLoadFalse(g4, "graphic/" .. g3 .. ".gim")
    end
    waitLoading()
    endLoading()
    v12()
    while true do
        v6 = pressButton("UP")
        if v6 == true then
            if v4 == false then
                v2 = v1
                v6 = v1 - 3
                if v6 < 1 then
                    v6 = v1
                    if not (v6) then
                        v6 = v1 - 3
                    end
                else
                    v6 = v1 - 3
                end
                v1 = v6
                v4 = true
            end
        end
        v6 = pressButton("DOWN")
        if v6 == true then
            if v4 == false then
                v2 = v1
                v6 = v7
                v5 = v3 * 9
                v6 = v6 - v5
                if v6 < 0 then
                    v6 = v1 + 3
                    v5 = v7
                    v9 = (v3 - 1) * 9
                    v5 = v5 - v9
                    if v5 < v6 then
                        v6 = v1
                        if not (v6) then
                            v6 = v1 + 3
                        end
                    else
                        v6 = v1 + 3
                    end
                    v1 = v6
                else
                    v6 = v1 + 3
                    if 9 < v6 then
                        v6 = v1
                        if not (v6) then
                            v6 = v1 + 3
                        end
                    else
                        v6 = v1 + 3
                    end
                    v1 = v6
                end
                v4 = true
            end
        end
        v6 = pressButton("RIGHT")
        if v6 == true then
            if v4 == false then
                v2 = v1
                v6 = v3 + 1
                if v6 <= v8 then
                    if v1 == 3 or v1 == 6 or v1 == 9 then
                        v6 = v3 + 1
                        v3 = v6
                        v6 = v1 - 2
                        v1 = v6
                        v6 = v7
                        v5 = v3 * 9
                        v6 = v6 - v5
                        if v6 < 0 then
                            v6 = v1
                            v5 = v7
                            v9 = (v3 - 1) * 9
                            v5 = v5 - v9
                            if v5 < v6 then
                                v6 = v7
                                v5 = (v3 - 1) * 9
                                v6 = v6 - v5
                            end
                            v1 = v6
                        end
                        v13(0, v2, v1, v3)
                    else
                        v6 = v1 + 1
                        v5 = v7
                        v9 = (v3 - 1) * 9
                        v5 = v5 - v9
                        if v5 < v6 then
                            v6 = v1
                            if not (v6) then
                                v6 = v1 + 1
                            end
                        else
                            v6 = v1 + 1
                        end
                        v1 = v6
                        v6 = v1
                        v4 = true
                    end
                elseif not (v1 == 3) then
                    if not (v1 == 6) then
                        if not (v1 == 9) then
                            v6 = v1 + 1
                            v5 = v7
                            v9 = (v3 - 1) * 9
                            v5 = v5 - v9
                            if v5 < v6 then
                                v6 = v1
                                if not (v6) then
                                    v6 = v1 + 1
                                end
                            else
                                v6 = v1 + 1
                            end
                            v1 = v6
                            v6 = v1
                            v4 = true
                        end
                    end
                end
            end
        end
        v6 = pressButton("LEFT")
        if v6 == true then
            if v4 == false then
                v2 = v1
                v6 = v3 - 1
                if 1 <= v6 then
                    if v1 == 1 or v1 == 4 or v1 == 7 then
                        v6 = v3 - 1
                        v3 = v6
                        v6 = v1 + 2
                        v1 = v6
                        v13(1, v2, v1, v3)
                        v4 = true
                    else
                        v6 = v1 - 1
                        v1 = v6
                        v6 = v1
                        v4 = true
                    end
                elseif not (v1 == 1) then
                    if not (v1 == 4) then
                        if not (v1 == 7) then
                            v6 = v1 - 1
                            v1 = v6
                            v6 = v1
                            v4 = true
                        end
                    end
                end
            end
        end
        v6 = pressButton("L")
        if v6 == true then
            if v4 == false then
                v6 = v3 - 1
                if 1 <= v6 then
                    v6 = v3 - 1
                    v3 = v6
                    v13(1, v1, v1, v3)
                end
            end
        end
        v6 = pressButton("R")
        if v6 == true then
            if v4 == false then
                v6 = v3 + 1
                if v6 <= v8 then
                    v6 = v3 + 1
                    v3 = v6
                    v6 = v7
                    v5 = v3 * 9
                    v6 = v6 - v5
                    if v6 < 0 then
                        v6 = v1
                        v5 = v7
                        v9 = (v3 - 1) * 9
                        v5 = v5 - v9
                        if v5 < v6 then
                            v6 = v7
                            v5 = (v3 - 1) * 9
                            v6 = v6 - v5
                        end
                        v1 = v6
                    end
                    v13(0, v1, v1, v3)
                end
            end
        end
        if pressButton("CROSS") == true then
            keyPlaySE(seName.cross)
            wait(5)
            break
        else
            if pressButton("CIRCLE") == true then
                if v4 == false then
                    if systemSave.memoryFlag[v0.memoryNumber[v3][v1]] == true then
                        keyPlaySE(seName.circle)
                        wait(10)
                        cInitGame()
                        switchScreen(0, "", 60)
                        doScriptScene = v0.doScriptScene[v0.memoryNumber[v3][v1]]
                        run(cGetFileName("script", v0.memoryNumber[v3][v1]))
                        quit()
                    end
                end
            end
            if v4 == true then
                if not (v2 == v1) then
                    keyPlaySE(seName.arrowKey)
                end
                layerVisible((v0.layerNumber.mask + v2), true)
                layerVisible((v0.layerNumber.mask + v1), false)
                layerMovePosition(v0.layerNumber.cursor, v0.cursorX[v1], v0.cursorY[v1], 5)
                fontClear()
                v4 = false
                wait(5)
            end
            wait(2)
        end
    end
    memoryFlag = false
    cInitGame()
    switchScreen(0, "", 60)
    run(cGetFileName("script", "snr_mainmenu"))
end
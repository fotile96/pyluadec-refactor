local v0 = {}
local v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14
v0.layerNumber = {}
v0.layerNumber.bg = 0
v0.layerNumber.logo = 1
v0.layerNumber.menu = 2
v0.layerKey0 = {}
v2 = "title_02_a"
v3 = "title_05_a"
v4 = "title_06_a"
v5 = "title_08_a"
v6 = "title_09_a"
v7 = "title_10_a"
v8 = "title_11_a"
v9 = "title_12_a"
v0.layerKey0[1] = v2
v0.layerKey0[2] = v3
v0.layerKey0[3] = v4
v0.layerKey0[4] = v5
v0.layerKey0[5] = v6
v0.layerKey0[6] = v7
v0.layerKey0[7] = v8
v0.layerKey0[8] = v9
v0.layerKey1 = {}
v2 = "title_03_a"
v3 = "title_05_a"
v4 = "title_06_a"
v5 = "title_07_a"
v6 = "title_08_a"
v7 = "title_09_a"
v8 = "title_10_a"
v9 = "title_11_a"
v10 = "title_12_a"
v0.layerKey1[1] = v2
v0.layerKey1[2] = v3
v0.layerKey1[3] = v4
v0.layerKey1[4] = v5
v0.layerKey1[5] = v6
v0.layerKey1[6] = v7
v0.layerKey1[7] = v8
v0.layerKey1[8] = v9
v0.layerKey1[9] = v10
v0.layerKey2 = {}
v2 = "title_03_a"
v3 = "title_04_a"
v4 = "title_05_a"
v5 = "title_06_a"
v6 = "title_07_a"
v7 = "title_08_a"
v8 = "title_09_a"
v9 = "title_10_a"
v10 = "title_11_a"
v11 = "title_12_a"
v0.layerKey2[1] = v2
v0.layerKey2[2] = v3
v0.layerKey2[3] = v4
v0.layerKey2[4] = v5
v0.layerKey2[5] = v6
v0.layerKey2[6] = v7
v0.layerKey2[7] = v8
v0.layerKey2[8] = v9
v0.layerKey2[9] = v10
v0.layerKey2[10] = v11
v0.layerKey3 = {}
v2 = "title_03_a"
v3 = "title_04_a"
v4 = "title_13_a"
v5 = "title_05_a"
v6 = "title_06_a"
v7 = "title_07_a"
v8 = "title_08_a"
v9 = "title_09_a"
v10 = "title_10_a"
v11 = "title_11_a"
v12 = "title_12_a"
v0.layerKey3[1] = v2
v0.layerKey3[2] = v3
v0.layerKey3[3] = v4
v0.layerKey3[4] = v5
v0.layerKey3[5] = v6
v0.layerKey3[6] = v7
v0.layerKey3[7] = v8
v0.layerKey3[8] = v9
v0.layerKey3[9] = v10
v0.layerKey3[10] = v11
v0.layerKey3[11] = v12
v0.layerWidth = {}
v0.layerWidth.title_02_a = 102
v0.layerWidth.title_03_a = 88
v0.layerWidth.title_04_a = 119
v0.layerWidth.title_05_a = 67
v0.layerWidth.title_06_a = 75
v0.layerWidth.title_07_a = 102
v0.layerWidth.title_08_a = 101
v0.layerWidth.title_09_a = 116
v0.layerWidth.title_10_a = 132
v0.layerWidth.title_11_a = 127
v0.layerWidth.title_12_a = 116
v0.layerWidth.title_13_a = 117
v0.layerHeight = {}
v0.layerHeight.title_02_a = 72
v0.layerHeight.title_03_a = 70
v0.layerHeight.title_04_a = 68
v0.layerHeight.title_05_a = 62
v0.layerHeight.title_06_a = 59
v0.layerHeight.title_07_a = 32
v0.layerHeight.title_08_a = 40
v0.layerHeight.title_09_a = 34
v0.layerHeight.title_10_a = 36
v0.layerHeight.title_11_a = 40
v0.layerHeight.title_12_a = 34
v0.layerHeight.title_13_a = 67
if gameSave.startMenuState == 2 then
    systemSave.libFlag = true
end
if gameSave.myCard[133].hold == 1 then
    systemSave.novelFlag = true
end
if gameSave.myCard[141].hold == 1 then
    systemSave.musicFlag = true
end
v1 = {}
if gameSave.myCard[133].hold == 1 then
    systemSave.novelGetFlag.novel03 = true
end
if gameSave.myCard[134].hold == 1 then
    systemSave.novelGetFlag.novel01 = true
end
if gameSave.myCard[135].hold == 1 then
    systemSave.novelGetFlag.novel04 = true
end
if gameSave.myCard[137].hold == 1 then
    systemSave.novelGetFlag.novel02 = true
end
if gameSave.myCard[138].hold == 1 then
    systemSave.novelGetFlag.novel05 = true
end
if gameSave.myCard[1].hold == 1 then
    systemSave.memoryFlag.snr_s0_10_f = true
end
if gameSave.myCard[133].hold == 1 then
    systemSave.memoryFlag.snr_s1_10_f = true
end
if gameSave.myCard[134].hold == 1 then
    systemSave.memoryFlag.snr_s2_10_f = true
end
if gameSave.myCard[135].hold == 1 then
    systemSave.memoryFlag.snr_s3_10_fa = true
end
if gameSave.myCard[136].hold == 1 then
    systemSave.memoryFlag.snr_s3_10_fb = true
end
if gameSave.myCard[145].hold == 1 then
    systemSave.memoryFlag.snr_s3_10_fc = true
end
if gameSave.myCard[137].hold == 1 then
    systemSave.memoryFlag.snr_s4_10_fa = true
end
if gameSave.myCard[138].hold == 1 then
    systemSave.memoryFlag.snr_s4_10_fb = true
end
if gameSave.myCard[139].hold == 1 then
    systemSave.memoryFlag.snr_s5_10_f = true
end
if gameSave.myCard[140].hold == 1 then
    systemSave.memoryFlag.snr_s6_10_f = true
end
if gameSave.myCard[141].hold == 1 then
    systemSave.memoryFlag.snr_s7_10_f = true
end
if gameSave.myCard[142].hold == 1 then
    systemSave.memoryFlag.snr_s8_10_f = true
end
if gameSave.myCard[143].hold == 1 then
    systemSave.memoryFlag.snr_e1_10_f = true
end
if gameSave.myCard[144].hold == 1 then
    systemSave.memoryFlag.snr_e2_10_f = true
end
v2 = function(p0, p1)
    local v1
    layerClip(p0, 0, 0, v0.layerWidth[p1], (v0.layerHeight[p1] / 2))
end
v3 = function(p0, p1)
    local v1
    layerClip(p0, 0, (v0.layerHeight[p1] / 2), v0.layerWidth[p1], v0.layerHeight[p1])
end
v4 = function()
    local v4, v5, v6, i0, v7, v8
    savedataTitle("タイトル", "")
    cPlayLoopSeWrap(cGetFileName("loop", "loop_10"))
    layerCopy(v0.layerNumber.bg, layerName.titleBG)
    layerCopy(v0.layerNumber.logo, layerName.title_01_a)
    layerPosition(v0.layerNumber.logo, 38, 10)
    layerCopy(20, layerName.effectWhite)
    layerBlend(20, "ADD")
    layerMoveAlpha(20, 0, 180)
    wait(180)
    layerLoad(20, "")
    if gameSave.startMenuState == 0 then
        v4 = {}
        v4.prologue = 1
        v4.library = 2
        v4.option = 3
        v4.load = 4
        v4.novel = 5
        v4.scene = 6
        v4.cg = 7
        v4.music = 8
        v1 = v4
        v4 = 1
        v5 = #v0.layerKey0
        v6 = 1
        for i0 = v4, v5, v6 do
            layerCopy((v0.layerNumber.menu + i0), layerName[v0.layerKey0[i0]])
            v2((v0.layerNumber.menu + i0), v0.layerKey0[i0])
            if i0 == v1.prologue then
                layerPosition((v0.layerNumber.menu + v1.prologue), 193, 139)
            elseif i0 == v1.library then
                layerPosition((v0.layerNumber.menu + v1.library), 205, 208)
            elseif i0 == v1.option then
                layerPosition((v0.layerNumber.menu + v1.option), 215, 241)
            elseif i0 == v1.load then
                layerPosition((v0.layerNumber.menu + v1.load), 330, 142)
            elseif i0 == v1.novel then
                layerPosition((v0.layerNumber.menu + v1.novel), 353, 185)
            elseif i0 == v1.scene then
                layerPosition((v0.layerNumber.menu + v1.scene), 335, 207)
            elseif i0 == v1.cg then
                layerPosition((v0.layerNumber.menu + v1.cg), 340, 223)
            elseif i0 == v1.music then
                layerPosition((v0.layerNumber.menu + v1.music), 352, 243)
            end
            if v1.novel <= i0 then
                layerVisible((v0.layerNumber.menu + i0), false)
            end
        end
        v3((v0.layerNumber.menu + 1), v0.layerKey0[1])
    else
        if gameSave.startMenuState == 1 then
            v4 = {}
            v4.story = 1
            v4.library = 2
            v4.option = 3
            v4.save = 4
            v4.load = 5
            v4.novel = 6
            v4.scene = 7
            v4.cg = 8
            v4.music = 9
            v1 = v4
            v4 = 1
            v5 = #v0.layerKey1
            v6 = 1
            for i0 = v4, v5, v6 do
                layerCopy((v0.layerNumber.menu + i0), layerName[v0.layerKey1[i0]])
                v2((v0.layerNumber.menu + i0), v0.layerKey1[i0])
                if i0 == v1.story then
                    layerPosition((v0.layerNumber.menu + v1.story), 210, 120)
                elseif i0 == v1.library then
                    layerPosition((v0.layerNumber.menu + v1.library), 205, 208)
                elseif i0 == v1.option then
                    layerPosition((v0.layerNumber.menu + v1.option), 215, 241)
                elseif i0 == v1.save then
                    layerPosition((v0.layerNumber.menu + v1.save), 48, 145)
                elseif i0 == v1.load then
                    layerPosition((v0.layerNumber.menu + v1.load), 330, 142)
                elseif i0 == v1.novel then
                    layerPosition((v0.layerNumber.menu + v1.novel), 353, 185)
                elseif i0 == v1.scene then
                    layerPosition((v0.layerNumber.menu + v1.scene), 335, 207)
                elseif i0 == v1.cg then
                    layerPosition((v0.layerNumber.menu + v1.cg), 340, 223)
                elseif i0 == v1.music then
                    layerPosition((v0.layerNumber.menu + v1.music), 352, 243)
                end
                if v1.novel <= i0 then
                    layerVisible((v0.layerNumber.menu + i0), false)
                end
            end
            v3((v0.layerNumber.menu + 1), v0.layerKey1[1])
        else
            if gameSave.startMenuState == 2 then
                v4 = {}
                v4.story = 1
                v4.fragment = 2
                v4.library = 3
                v4.option = 4
                v4.save = 5
                v4.load = 6
                v4.novel = 7
                v4.scene = 8
                v4.cg = 9
                v4.music = 10
                v1 = v4
                if gameSave.myCard[140].hold == -1 then
                    v4 = 1
                    v5 = #v0.layerKey2
                    v6 = 1
                    for i0 = v4, v5, v6 do
                        layerCopy((v0.layerNumber.menu + i0), layerName[v0.layerKey2[i0]])
                        v2((v0.layerNumber.menu + i0), v0.layerKey2[i0])
                        if i0 == v1.story then
                            layerPosition((v0.layerNumber.menu + v1.story), 210, 120)
                        elseif i0 == v1.fragment then
                            layerPosition((v0.layerNumber.menu + v1.fragment), 190, 160)
                        elseif i0 == v1.library then
                            layerPosition((v0.layerNumber.menu + v1.library), 205, 208)
                        elseif i0 == v1.option then
                            layerPosition((v0.layerNumber.menu + v1.option), 215, 241)
                        elseif i0 == v1.save then
                            layerPosition((v0.layerNumber.menu + v1.save), 48, 145)
                        elseif i0 == v1.load then
                            layerPosition((v0.layerNumber.menu + v1.load), 330, 142)
                        elseif i0 == v1.novel then
                            layerPosition((v0.layerNumber.menu + v1.novel), 353, 185)
                        elseif i0 == v1.scene then
                            layerPosition((v0.layerNumber.menu + v1.scene), 335, 207)
                        elseif i0 == v1.cg then
                            layerPosition((v0.layerNumber.menu + v1.cg), 340, 223)
                        elseif i0 == v1.music then
                            layerPosition((v0.layerNumber.menu + v1.music), 352, 243)
                        end
                        if v1.novel <= i0 then
                            layerVisible((v0.layerNumber.menu + i0), false)
                        end
                    end
                    v3((v0.layerNumber.menu + 1), v0.layerKey2[1])
                else
                    v4 = {}
                    v4.story = 1
                    v4.fragment = 2
                    v4.section7 = 3
                    v4.library = 4
                    v4.option = 5
                    v4.save = 6
                    v4.load = 7
                    v4.novel = 8
                    v4.scene = 9
                    v4.cg = 10
                    v4.music = 11
                    v1 = v4
                    v4 = 1
                    v5 = #v0.layerKey3
                    v6 = 1
                    for i0 = v4, v5, v6 do
                        layerCopy((v0.layerNumber.menu + i0), layerName[v0.layerKey3[i0]])
                        v2((v0.layerNumber.menu + i0), v0.layerKey3[i0])
                        if i0 == v1.story then
                            layerPosition((v0.layerNumber.menu + v1.story), 210, 110)
                        elseif i0 == v1.fragment then
                            layerPosition((v0.layerNumber.menu + v1.fragment), 190, 145)
                        elseif i0 == v1.section7 then
                            layerPosition((v0.layerNumber.menu + v1.section7), 194, 180)
                        elseif i0 == v1.library then
                            layerPosition((v0.layerNumber.menu + v1.library), 205, 208)
                        elseif i0 == v1.option then
                            layerPosition((v0.layerNumber.menu + v1.option), 215, 241)
                        elseif i0 == v1.save then
                            layerPosition((v0.layerNumber.menu + v1.save), 48, 145)
                        elseif i0 == v1.load then
                            layerPosition((v0.layerNumber.menu + v1.load), 330, 142)
                        elseif i0 == v1.novel then
                            layerPosition((v0.layerNumber.menu + v1.novel), 353, 185)
                        elseif i0 == v1.scene then
                            layerPosition((v0.layerNumber.menu + v1.scene), 335, 207)
                        elseif i0 == v1.cg then
                            layerPosition((v0.layerNumber.menu + v1.cg), 340, 223)
                        elseif i0 == v1.music then
                            layerPosition((v0.layerNumber.menu + v1.music), 352, 243)
                        end
                        if v1.novel <= i0 then
                            layerVisible((v0.layerNumber.menu + i0), false)
                        end
                    end
                    v3((v0.layerNumber.menu + 1), v0.layerKey3[1])
                end
            end
        end
    end
    if not (systemSave.libFlag == true) then
        layerVisible((v0.layerNumber.menu + v1.library), false)
    end
    switchScreen(0, "", 30)
end
v5 = function()
    layerCopy(0, backLayerName.black)
    layerAlpha(0, 0)
    layerMoveAlpha(0, 60, 20)
    wait(20)
end
v6 = function()
    layerMoveAlpha(0, 0, 20)
    wait(20)
    layerLoad(0, "")
end
v7 = function()
    local v0
    pageScreen(1)
    fontClear()
    v5()
    runListLoad()
    pageScreen(0)
    v0 = succeedLoadGamedata()
    if v0 then
        runAutoLoad()
        cInitGame()
        switchScreen(0, "", 60)
        applyGamedata()
    end
end
v8 = function()
    pageScreen(1)
    fontClear()
    v5()
    runListSave()
    autoSystemSave(1)
    pageScreen(0)
end
main = function()
    local v5, v6, v9, v10, v11, v12, v13, i4, v14
    advPart(false)
    logEnable(false)
    systemConfig.unsetConfigButton()
    cInitGame()
    v4()
    v5 = 1
    v6 = 0
    v9 = false
    v10 = false
    if gameSave.startMenuState == 0 then
        while true do
            if v10 == false then
                v11 = pressButton("UP")
                if (v11 == true) and (v9 == false) then
                    v6 = v5
                    if v1.option < v5 then
                        v5 = v1.prologue
                    else
                        v11 = v5 - 1
                        if v11 < v1.prologue then
                            v11 = v1.prologue
                            if not (v11) then
                                v5 = v5 - 1
                            else
                                v5 = v11
                            end
                        else
                            v5 = v5 - 1
                        end
                    end
                    if v5 == v1.library then
                        if not (systemSave.libFlag == true) then
                            v11 = v5 - 1
                            if v11 < v1.prologue then
                                v11 = v1.prologue
                                if not (v11) then
                                    v5 = v5 - 1
                                else
                                    v5 = v11
                                end
                            else
                                v5 = v5 - 1
                            end
                        end
                    end
                    v9 = true
                end
                v11 = pressButton("DOWN")
                if (v11 == true) and (v9 == false) then
                    v6 = v5
                    if v1.option < v5 then
                        v5 = v1.library
                    else
                        v11 = v5 + 1
                        if v1.option < v11 then
                            v11 = v1.option
                            if not (v11) then
                                v5 = v5 + 1
                            else
                                v5 = v11
                            end
                        else
                            v5 = v5 + 1
                        end
                    end
                    if v5 == v1.library then
                        if not (systemSave.libFlag == true) then
                            v11 = v5 + 1
                            if v1.option < v11 then
                                v11 = v1.option
                                if not (v11) then
                                    v5 = v5 + 1
                                else
                                    v5 = v11
                                end
                            else
                                v5 = v5 + 1
                            end
                        end
                    end
                    v9 = true
                end
                v11 = pressButton("RIGHT")
                if (v11 == true) and (v9 == false) then
                    v6 = v5
                    v5 = v1.load
                    v9 = true
                end
                v11 = pressButton("LEFT")
                if (v11 == true) and (v9 == false) then
                    v6 = v5
                    v5 = v1.prologue
                    v9 = true
                end
                v11 = pressButton("CIRCLE")
                if (v11 == true) and (v9 == false) then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if v5 == v1.prologue then
                        cInitGame()
                        switchScreen(0, "", 60)
                        doScriptScene = "sof_10"
                        run(cGetFileName("script", "snr_s0_10_f"))
                        quit()
                    else
                        if v5 == v1.library then
                            v10 = true
                            if not (systemSave.novelFlag == true) then
                                v5 = v1.scene
                            else
                                v5 = v1.novel
                            end
                            v11 = 1
                            v12 = #v0.layerKey0
                            v13 = 1
                            for i4 = v11, v12, v13 do
                                if i4 < v1.novel then
                                    if not (i4 == v1.library) then
                                        layerMoveAlpha((v0.layerNumber.menu + i4), 50, 30)
                                    end
                                elseif (i4 == v1.novel and not (systemSave.novelFlag == true)) or (i4 == v1.music and not (systemSave.musicFlag == true)) then
                                    layerVisible((v0.layerNumber.menu + i4), false)
                                else
                                    layerAlpha((v0.layerNumber.menu + i4), 0)
                                    layerVisible((v0.layerNumber.menu + i4), true)
                                    layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                                end
                            end
                            wait(30)
                        else
                            if v5 == v1.option then
                                systemOption.Option()
                            elseif v5 == v1.load then
                                v7()
                            end
                        end
                    end
                    v2((v0.layerNumber.menu + v6), v0.layerKey0[v6])
                    v3((v0.layerNumber.menu + v5), v0.layerKey0[v5])
                end
            else
                v11 = pressButton("UP")
                if (v11 == true) and (v9 == false) then
                    keyPlaySE(seName.arrowKey)
                    v6 = v5
                    v11 = v5 - 1
                    if v11 < v1.novel then
                        v11 = v1.novel
                        if not (v11) then
                            v5 = v5 - 1
                        else
                            v5 = v11
                        end
                    else
                        v5 = v5 - 1
                    end
                    if v5 == v1.novel then
                        if not (systemSave.novelFlag == true) then
                            v5 = v5 + 1
                        end
                    end
                    v9 = true
                end
                v11 = pressButton("DOWN")
                if (v11 == true) and (v9 == false) then
                    keyPlaySE(seName.arrowKey)
                    v6 = v5
                    v11 = v5 + 1
                    if v1.music < v11 then
                        v11 = v1.music
                        if not (v11) then
                            v5 = v5 + 1
                        else
                            v5 = v11
                        end
                    else
                        v5 = v5 + 1
                    end
                    if v5 == v1.music then
                        if not (systemSave.musicFlag == true) then
                            v5 = v5 - 1
                        end
                    end
                    v9 = true
                end
                v11 = pressButton("CIRCLE")
                if (v11 == true) and (v9 == false) then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if v5 == v1.novel then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_novel"))
                        quit()
                    elseif v5 == v1.scene then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_memory"))
                        quit()
                    elseif v5 == v1.cg then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_graphic"))
                        quit()
                    elseif v5 == v1.music then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_music"))
                        quit()
                    end
                end
                v11 = pressButton("CROSS")
                if (v11 == true) and (v9 == false) then
                    keyPlaySE(seName.cross)
                    v10 = false
                    v6 = v5
                    v5 = v1.library
                    v11 = 1
                    v12 = v1.music
                    v13 = 1
                    for i4 = v11, v12, v13 do
                        if i4 < v1.novel then
                            layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                        else
                            layerMoveAlpha((v0.layerNumber.menu + i4), 0, 30)
                        end
                    end
                    wait(30)
                    v11 = v1.novel
                    v12 = v1.music
                    v13 = 1
                    for i4 = v11, v12, v13 do
                        layerVisible((v0.layerNumber.menu + i4), false)
                    end
                    v2((v0.layerNumber.menu + v6), v0.layerKey0[v6])
                    v3((v0.layerNumber.menu + v5), v0.layerKey0[v5])
                end
            end
            if v9 == true then
                v2((v0.layerNumber.menu + v6), v0.layerKey0[v6])
                v3((v0.layerNumber.menu + v5), v0.layerKey0[v5])
                keyPlaySE(seName.arrowKey)
                wait(3)
                v9 = false
            end
            wait(2)
        end
    else
        if gameSave.startMenuState == 1 then
            while true do
                if v10 == false then
                    v11 = pressButton("UP")
                    if (v11 == true) and (v9 == false) then
                        v6 = v5
                        if v1.option < v5 then
                            v5 = v1.story
                        else
                            v11 = v5 - 1
                            if v11 < v1.story then
                                v11 = v1.story
                                if not (v11) then
                                    v5 = v5 - 1
                                else
                                    v5 = v11
                                end
                            else
                                v5 = v5 - 1
                            end
                        end
                        if v5 == v1.library then
                            if not (systemSave.libFlag == true) then
                                v11 = v5 - 1
                                if v11 < v1.story then
                                    v11 = v1.story
                                    if not (v11) then
                                        v5 = v5 - 1
                                    else
                                        v5 = v11
                                    end
                                else
                                    v5 = v5 - 1
                                end
                            end
                        end
                        v9 = true
                    end
                    v11 = pressButton("DOWN")
                    if (v11 == true) and (v9 == false) then
                        v6 = v5
                        if v1.option < v5 then
                            v5 = v1.library
                        else
                            v11 = v5 + 1
                            if v1.option < v11 then
                                v11 = v1.option
                                if not (v11) then
                                    v5 = v5 + 1
                                else
                                    v5 = v11
                                end
                            else
                                v5 = v5 + 1
                            end
                        end
                        if v5 == v1.library then
                            if not (systemSave.libFlag == true) then
                                v11 = v5 + 1
                                if v1.option < v11 then
                                    v11 = v1.option
                                    if not (v11) then
                                        v5 = v5 + 1
                                    else
                                        v5 = v11
                                    end
                                else
                                    v5 = v5 + 1
                                end
                            end
                        end
                        v9 = true
                    end
                    v11 = pressButton("RIGHT")
                    if (v11 == true) and (v9 == false) then
                        v6 = v5
                        v5 = v1.load
                        v9 = true
                    end
                    v11 = pressButton("LEFT")
                    if (v11 == true) and (v9 == false) then
                        v6 = v5
                        v5 = v1.save
                        v9 = true
                    end
                    v11 = pressButton("CIRCLE")
                    if (v11 == true) and (v9 == false) then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if v5 == v1.story then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_story_main"))
                            quit()
                        else
                            if v5 == v1.library then
                                v10 = true
                                if not (systemSave.novelFlag == true) then
                                    v5 = v1.scene
                                else
                                    v5 = v1.novel
                                end
                                v11 = 1
                                v12 = #v0.layerKey1
                                v13 = 1
                                for i4 = v11, v12, v13 do
                                    if i4 < v1.novel then
                                        if not (i4 == v1.library) then
                                            layerMoveAlpha((v0.layerNumber.menu + i4), 50, 30)
                                        end
                                    elseif (i4 == v1.novel and not (systemSave.novelFlag == true)) or (i4 == v1.music and not (systemSave.musicFlag == true)) then
                                        layerVisible((v0.layerNumber.menu + i4), false)
                                    else
                                        layerAlpha((v0.layerNumber.menu + i4), 0)
                                        layerVisible((v0.layerNumber.menu + i4), true)
                                        layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                                    end
                                end
                                wait(30)
                                v2((v0.layerNumber.menu + v6), v0.layerKey1[v6])
                                v3((v0.layerNumber.menu + v5), v0.layerKey1[v5])
                            else
                                if v5 == v1.option then
                                    systemOption.Option()
                                elseif v5 == v1.save then
                                    v8()
                                elseif v5 == v1.load then
                                    v7()
                                end
                            end
                        end
                    end
                else
                    v11 = pressButton("UP")
                    if (v11 == true) and (v9 == false) then
                        keyPlaySE(seName.arrowKey)
                        v6 = v5
                        v11 = v5 - 1
                        if v11 < v1.novel then
                            v11 = v1.novel
                            if not (v11) then
                                v5 = v5 - 1
                            else
                                v5 = v11
                            end
                        else
                            v5 = v5 - 1
                        end
                        if v5 == v1.novel then
                            if not (systemSave.novelFlag == true) then
                                v5 = v5 + 1
                            end
                        end
                        v9 = true
                    end
                    v11 = pressButton("DOWN")
                    if (v11 == true) and (v9 == false) then
                        keyPlaySE(seName.arrowKey)
                        v6 = v5
                        v11 = v5 + 1
                        if v1.music < v11 then
                            v11 = v1.music
                            if not (v11) then
                                v5 = v5 + 1
                            else
                                v5 = v11
                            end
                        else
                            v5 = v5 + 1
                        end
                        if v5 == v1.music then
                            if not (systemSave.musicFlag == true) then
                                v5 = v5 - 1
                            end
                        end
                        v9 = true
                    end
                    v11 = pressButton("CIRCLE")
                    if (v11 == true) and (v9 == false) then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if v5 == v1.novel then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_novel"))
                            quit()
                        elseif v5 == v1.scene then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_memory"))
                            quit()
                        elseif v5 == v1.cg then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_graphic"))
                            quit()
                        elseif v5 == v1.music then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_music"))
                            quit()
                        end
                    end
                    v11 = pressButton("CROSS")
                    if (v11 == true) and (v9 == false) then
                        keyPlaySE(seName.cross)
                        v10 = false
                        v6 = v5
                        v5 = v1.library
                        v11 = 1
                        v12 = v1.music
                        v13 = 1
                        for i4 = v11, v12, v13 do
                            if i4 < v1.novel then
                                layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                            else
                                layerMoveAlpha((v0.layerNumber.menu + i4), 0, 30)
                            end
                        end
                        wait(30)
                        v11 = v1.novel
                        v12 = v1.music
                        v13 = 1
                        for i4 = v11, v12, v13 do
                            layerVisible((v0.layerNumber.menu + i4), false)
                        end
                        v2((v0.layerNumber.menu + v6), v0.layerKey1[v6])
                        v3((v0.layerNumber.menu + v5), v0.layerKey1[v5])
                    end
                end
                if v9 == true then
                    v2((v0.layerNumber.menu + v6), v0.layerKey1[v6])
                    v3((v0.layerNumber.menu + v5), v0.layerKey1[v5])
                    keyPlaySE(seName.arrowKey)
                    wait(3)
                    v9 = false
                end
                wait(2)
            end
        else
            if gameSave.startMenuState == 2 then
                if gameSave.myCard[140].hold == -1 then
                    while true do
                        if v10 == false then
                            v11 = pressButton("UP")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                if v1.option < v5 then
                                    v5 = v1.story
                                else
                                    v11 = v5 - 1
                                    if v11 < v1.story then
                                        v11 = v1.story
                                        if not (v11) then
                                            v5 = v5 - 1
                                        else
                                            v5 = v11
                                        end
                                    else
                                        v5 = v5 - 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("DOWN")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                if v1.option < v5 then
                                    v5 = v1.fragment
                                else
                                    v11 = v5 + 1
                                    if v1.option < v11 then
                                        v11 = v1.option
                                        if not (v11) then
                                            v5 = v5 + 1
                                        else
                                            v5 = v11
                                        end
                                    else
                                        v5 = v5 + 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("RIGHT")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                v5 = v1.load
                                v9 = true
                            end
                            v11 = pressButton("LEFT")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                v5 = v1.save
                                v9 = true
                            end
                            v11 = pressButton("CIRCLE")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.circle)
                                wait(10)
                                if v5 == v1.story then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_story_main"))
                                    quit()
                                elseif v5 == v1.fragment then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_fragment_main"))
                                    quit()
                                else
                                    if v5 == v1.library then
                                        v10 = true
                                        if not (systemSave.novelFlag == true) then
                                            v5 = v1.scene
                                        else
                                            v5 = v1.novel
                                        end
                                        v11 = 1
                                        v12 = #v0.layerKey2
                                        v13 = 1
                                        for i4 = v11, v12, v13 do
                                            if i4 < v1.novel then
                                                if not (i4 == v1.library) then
                                                    layerMoveAlpha((v0.layerNumber.menu + i4), 50, 30)
                                                end
                                            elseif (i4 == v1.novel and not (systemSave.novelFlag == true)) or (i4 == v1.music and not (systemSave.musicFlag == true)) then
                                                layerVisible((v0.layerNumber.menu + i4), false)
                                            else
                                                layerAlpha((v0.layerNumber.menu + i4), 0)
                                                layerVisible((v0.layerNumber.menu + i4), true)
                                                layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                                            end
                                        end
                                        wait(30)
                                        v2((v0.layerNumber.menu + v6), v0.layerKey2[v6])
                                        v3((v0.layerNumber.menu + v5), v0.layerKey2[v5])
                                    else
                                        if v5 == v1.option then
                                            systemOption.Option()
                                        elseif v5 == v1.save then
                                            v8()
                                        elseif v5 == v1.load then
                                            v7()
                                        end
                                    end
                                end
                            end
                        else
                            v11 = pressButton("UP")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.arrowKey)
                                v6 = v5
                                v11 = v5 - 1
                                if v11 < v1.novel then
                                    v11 = v1.novel
                                    if not (v11) then
                                        v5 = v5 - 1
                                    else
                                        v5 = v11
                                    end
                                else
                                    v5 = v5 - 1
                                end
                                if v5 == v1.novel then
                                    if not (systemSave.novelFlag == true) then
                                        v5 = v5 + 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("DOWN")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.arrowKey)
                                v6 = v5
                                v11 = v5 + 1
                                if v1.music < v11 then
                                    v11 = v1.music
                                    if not (v11) then
                                        v5 = v5 + 1
                                    else
                                        v5 = v11
                                    end
                                else
                                    v5 = v5 + 1
                                end
                                if v5 == v1.music then
                                    if not (systemSave.musicFlag == true) then
                                        v5 = v5 - 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("CIRCLE")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.circle)
                                wait(10)
                                if v5 == v1.novel then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_novel"))
                                    quit()
                                elseif v5 == v1.scene then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_memory"))
                                    quit()
                                elseif v5 == v1.cg then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_graphic"))
                                    quit()
                                elseif v5 == v1.music then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_music"))
                                    quit()
                                end
                            end
                            v11 = pressButton("CROSS")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.cross)
                                v10 = false
                                v6 = v5
                                v5 = v1.library
                                v11 = 1
                                v12 = v1.music
                                v13 = 1
                                for i4 = v11, v12, v13 do
                                    if i4 < v1.novel then
                                        layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                                    else
                                        layerMoveAlpha((v0.layerNumber.menu + i4), 0, 30)
                                    end
                                end
                                wait(30)
                                v11 = v1.novel
                                v12 = v1.music
                                v13 = 1
                                for i4 = v11, v12, v13 do
                                    layerVisible((v0.layerNumber.menu + i4), false)
                                end
                                v2((v0.layerNumber.menu + v6), v0.layerKey2[v6])
                                v3((v0.layerNumber.menu + v5), v0.layerKey2[v5])
                            end
                        end
                        if v9 == true then
                            v2((v0.layerNumber.menu + v6), v0.layerKey2[v6])
                            v3((v0.layerNumber.menu + v5), v0.layerKey2[v5])
                            keyPlaySE(seName.arrowKey)
                            wait(3)
                            v9 = false
                        end
                        wait(2)
                    end
                else
                    while true do
                        if v10 == false then
                            v11 = pressButton("UP")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                if v1.option < v5 then
                                    v5 = v1.story
                                else
                                    v11 = v5 - 1
                                    if v11 < v1.story then
                                        v11 = v1.story
                                        if not (v11) then
                                            v5 = v5 - 1
                                        else
                                            v5 = v11
                                        end
                                    else
                                        v5 = v5 - 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("DOWN")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                if v1.option < v5 then
                                    v5 = v1.fragment
                                else
                                    v11 = v5 + 1
                                    if v1.option < v11 then
                                        v11 = v1.option
                                        if not (v11) then
                                            v5 = v5 + 1
                                        else
                                            v5 = v11
                                        end
                                    else
                                        v5 = v5 + 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("RIGHT")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                v5 = v1.load
                                v9 = true
                            end
                            v11 = pressButton("LEFT")
                            if (v11 == true) and (v9 == false) then
                                v6 = v5
                                v5 = v1.save
                                v9 = true
                            end
                            v11 = pressButton("CIRCLE")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.circle)
                                wait(10)
                                if v5 == v1.story then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_story_main"))
                                    quit()
                                elseif v5 == v1.fragment then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_fragment_main"))
                                    quit()
                                elseif v5 == v1.section7 then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    doScriptScene = "s7f-10"
                                    run(cGetFileName("script", "snr_s7_10_f"))
                                    quit()
                                else
                                    if v5 == v1.library then
                                        v10 = true
                                        if not (systemSave.novelFlag == true) then
                                            v5 = v1.scene
                                        else
                                            v5 = v1.novel
                                        end
                                        v11 = 1
                                        v12 = 11
                                        v13 = 1
                                        for i4 = v11, v12, v13 do
                                            if i4 < v1.novel then
                                                if not (i4 == v1.library) then
                                                    layerMoveAlpha((v0.layerNumber.menu + i4), 50, 30)
                                                end
                                            elseif (i4 == v1.novel and not (systemSave.novelFlag == true)) or (i4 == v1.music and not (systemSave.musicFlag == true)) then
                                                layerVisible((v0.layerNumber.menu + i4), false)
                                            else
                                                layerAlpha((v0.layerNumber.menu + i4), 0)
                                                layerVisible((v0.layerNumber.menu + i4), true)
                                                layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                                            end
                                        end
                                        wait(30)
                                    else
                                        if v5 == v1.option then
                                            systemOption.Option()
                                        elseif v5 == v1.save then
                                            v8()
                                        elseif v5 == v1.load then
                                            v7()
                                        end
                                    end
                                end
                                v2((v0.layerNumber.menu + v6), v0.layerKey3[v6])
                                v3((v0.layerNumber.menu + v5), v0.layerKey3[v5])
                            end
                        else
                            v11 = pressButton("UP")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.arrowKey)
                                v6 = v5
                                v11 = v5 - 1
                                if v11 < v1.novel then
                                    v11 = v1.novel
                                    if not (v11) then
                                        v5 = v5 - 1
                                    else
                                        v5 = v11
                                    end
                                else
                                    v5 = v5 - 1
                                end
                                if v5 == v1.novel then
                                    if not (systemSave.novelFlag == true) then
                                        v5 = v5 + 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("DOWN")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.arrowKey)
                                v6 = v5
                                v11 = v5 + 1
                                if v1.music < v11 then
                                    v11 = v1.music
                                    if not (v11) then
                                        v5 = v5 + 1
                                    else
                                        v5 = v11
                                    end
                                else
                                    v5 = v5 + 1
                                end
                                if v5 == v1.music then
                                    if not (systemSave.musicFlag == true) then
                                        v5 = v5 - 1
                                    end
                                end
                                v9 = true
                            end
                            v11 = pressButton("CIRCLE")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.circle)
                                wait(10)
                                if v5 == v1.novel then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_novel"))
                                    quit()
                                elseif v5 == v1.scene then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_memory"))
                                    quit()
                                elseif v5 == v1.cg then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_graphic"))
                                    quit()
                                elseif v5 == v1.music then
                                    cInitGame()
                                    switchScreen(0, "", 60)
                                    run(cGetFileName("script", "snr_music"))
                                    quit()
                                end
                            end
                            v11 = pressButton("CROSS")
                            if (v11 == true) and (v9 == false) then
                                keyPlaySE(seName.cross)
                                v10 = false
                                v6 = v5
                                v5 = v1.library
                                v11 = 1
                                v12 = v1.music
                                v13 = 1
                                for i4 = v11, v12, v13 do
                                    if i4 < v1.novel then
                                        layerMoveAlpha((v0.layerNumber.menu + i4), 100, 30)
                                    else
                                        layerMoveAlpha((v0.layerNumber.menu + i4), 0, 30)
                                    end
                                end
                                wait(30)
                                v11 = v1.novel
                                v12 = v1.music
                                v13 = 1
                                for i4 = v11, v12, v13 do
                                    layerVisible((v0.layerNumber.menu + i4), false)
                                end
                                v2((v0.layerNumber.menu + v6), v0.layerKey3[v6])
                                v3((v0.layerNumber.menu + v5), v0.layerKey3[v5])
                            end
                        end
                        if v9 == true then
                            v2((v0.layerNumber.menu + v6), v0.layerKey3[v6])
                            v3((v0.layerNumber.menu + v5), v0.layerKey3[v5])
                            keyPlaySE(seName.arrowKey)
                            wait(3)
                            v9 = false
                        end
                        wait(2)
                    end
                end
            end
        end
    end
end
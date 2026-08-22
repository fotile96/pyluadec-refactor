local l0_0 = {layerNumber = {bg = 0, logo = 1, menu = 2}, layerKey0 = {"title_02_a", "title_05_a", "title_06_a", "title_08_a", "title_09_a", "title_10_a", "title_11_a", "title_12_a"}, layerKey1 = {"title_03_a", "title_05_a", "title_06_a", "title_07_a", "title_08_a", "title_09_a", "title_10_a", "title_11_a", "title_12_a"}, layerKey2 = {"title_03_a", "title_04_a", "title_05_a", "title_06_a", "title_07_a", "title_08_a", "title_09_a", "title_10_a", "title_11_a", "title_12_a"}, layerKey3 = {"title_03_a", "title_04_a", "title_13_a", "title_05_a", "title_06_a", "title_07_a", "title_08_a", "title_09_a", "title_10_a", "title_11_a", "title_12_a"}, layerWidth = {title_02_a = 102, title_03_a = 88, title_04_a = 119, title_05_a = 67, title_06_a = 75, title_07_a = 102, title_08_a = 101, title_09_a = 116, title_10_a = 132, title_11_a = 127, title_12_a = 116, title_13_a = 117}, layerHeight = {title_02_a = 72, title_03_a = 70, title_04_a = 68, title_05_a = 62, title_06_a = 59, title_07_a = 32, title_08_a = 40, title_09_a = 34, title_10_a = 36, title_11_a = 40, title_12_a = 34, title_13_a = 67}}
if gameSave.startMenuState == 2 then
    systemSave.libFlag = true
end
if gameSave.myCard[133].hold == 1 then
    systemSave.novelFlag = true
end
if gameSave.myCard[141].hold == 1 then
    systemSave.musicFlag = true
end
local l0_1 = {}
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
local l0_2 = function(l1_0, l1_1)
    local l1_2 = l0_0.layerHeight[l1_1] / 2
    layerClip(l1_0, 0, 0, l0_0.layerWidth[l1_1], l1_2)
end
local l0_3 = function(l1_0, l1_1)
    local l1_2 = l0_0.layerHeight[l1_1] / 2
    local l1_3 = l0_0.layerHeight[l1_1]
    layerClip(l1_0, 0, l1_2, l0_0.layerWidth[l1_1], l1_3)
end
local l0_4 = function()
    savedataTitle("タイトル", "")
    cPlayLoopSeWrap(cGetFileName("loop", "loop_10"))
    layerCopy(l0_0.layerNumber.bg, layerName.titleBG)
    layerCopy(l0_0.layerNumber.logo, layerName.title_01_a)
    layerPosition(l0_0.layerNumber.logo, 38, 10)
    layerCopy(20, layerName.effectWhite)
    layerBlend(20, "ADD")
    layerMoveAlpha(20, 0, 180)
    wait(180)
    layerLoad(20, "")
    if gameSave.startMenuState == 0 then
        l0_1 = {prologue = 1, library = 2, option = 3, load = 4, novel = 5, scene = 6, cg = 7, music = 8}
        for l1_3 = 1, #l0_0.layerKey0, 1 do
            layerCopy(l0_0.layerNumber.menu + l1_3, layerName[l0_0.layerKey0[l1_3]])
            l0_2(l0_0.layerNumber.menu + l1_3, l0_0.layerKey0[l1_3])
            if l1_3 == l0_1.prologue then
                layerPosition(l0_0.layerNumber.menu + l0_1.prologue, 193, 139)
            elseif l1_3 == l0_1.library then
                layerPosition(l0_0.layerNumber.menu + l0_1.library, 205, 208)
            elseif l1_3 == l0_1.option then
                layerPosition(l0_0.layerNumber.menu + l0_1.option, 215, 241)
            elseif l1_3 == l0_1.load then
                layerPosition(l0_0.layerNumber.menu + l0_1.load, 330, 142)
            elseif l1_3 == l0_1.novel then
                layerPosition(l0_0.layerNumber.menu + l0_1.novel, 353, 185)
            elseif l1_3 == l0_1.scene then
                layerPosition(l0_0.layerNumber.menu + l0_1.scene, 335, 207)
            elseif l1_3 == l0_1.cg then
                layerPosition(l0_0.layerNumber.menu + l0_1.cg, 340, 223)
            elseif l1_3 == l0_1.music then
                layerPosition(l0_0.layerNumber.menu + l0_1.music, 352, 243)
            end
            if l1_3 >= l0_1.novel then
                layerVisible(l0_0.layerNumber.menu + l1_3, false)
            end
        end
        l0_3(l0_0.layerNumber.menu + 1, l0_0.layerKey0[1])
    elseif gameSave.startMenuState == 1 then
        l0_1 = {story = 1, library = 2, option = 3, save = 4, load = 5, novel = 6, scene = 7, cg = 8, music = 9}
        for l1_3 = 1, #l0_0.layerKey1, 1 do
            layerCopy(l0_0.layerNumber.menu + l1_3, layerName[l0_0.layerKey1[l1_3]])
            l0_2(l0_0.layerNumber.menu + l1_3, l0_0.layerKey1[l1_3])
            if l1_3 == l0_1.story then
                layerPosition(l0_0.layerNumber.menu + l0_1.story, 210, 120)
            elseif l1_3 == l0_1.library then
                layerPosition(l0_0.layerNumber.menu + l0_1.library, 205, 208)
            elseif l1_3 == l0_1.option then
                layerPosition(l0_0.layerNumber.menu + l0_1.option, 215, 241)
            elseif l1_3 == l0_1.save then
                layerPosition(l0_0.layerNumber.menu + l0_1.save, 48, 145)
            elseif l1_3 == l0_1.load then
                layerPosition(l0_0.layerNumber.menu + l0_1.load, 330, 142)
            elseif l1_3 == l0_1.novel then
                layerPosition(l0_0.layerNumber.menu + l0_1.novel, 353, 185)
            elseif l1_3 == l0_1.scene then
                layerPosition(l0_0.layerNumber.menu + l0_1.scene, 335, 207)
            elseif l1_3 == l0_1.cg then
                layerPosition(l0_0.layerNumber.menu + l0_1.cg, 340, 223)
            elseif l1_3 == l0_1.music then
                layerPosition(l0_0.layerNumber.menu + l0_1.music, 352, 243)
            end
            if l0_1.novel <= l1_3 then
                layerVisible(l0_0.layerNumber.menu + l1_3, false)
            end
        end
        l0_3(l0_0.layerNumber.menu + 1, l0_0.layerKey1[1])
    elseif gameSave.startMenuState == 2 then
        l0_1 = {story = 1, fragment = 2, library = 3, option = 4, save = 5, load = 6, novel = 7, scene = 8, cg = 9, music = 10}
        if gameSave.myCard[140].hold == -1 then
            for l1_3 = 1, #l0_0.layerKey2, 1 do
                layerCopy(l0_0.layerNumber.menu + l1_3, layerName[l0_0.layerKey2[l1_3]])
                l0_2(l0_0.layerNumber.menu + l1_3, l0_0.layerKey2[l1_3])
                if l1_3 == l0_1.story then
                    layerPosition(l0_0.layerNumber.menu + l0_1.story, 210, 120)
                elseif l1_3 == l0_1.fragment then
                    layerPosition(l0_0.layerNumber.menu + l0_1.fragment, 190, 160)
                elseif l1_3 == l0_1.library then
                    layerPosition(l0_0.layerNumber.menu + l0_1.library, 205, 208)
                elseif l1_3 == l0_1.option then
                    layerPosition(l0_0.layerNumber.menu + l0_1.option, 215, 241)
                elseif l1_3 == l0_1.save then
                    layerPosition(l0_0.layerNumber.menu + l0_1.save, 48, 145)
                elseif l1_3 == l0_1.load then
                    layerPosition(l0_0.layerNumber.menu + l0_1.load, 330, 142)
                elseif l1_3 == l0_1.novel then
                    layerPosition(l0_0.layerNumber.menu + l0_1.novel, 353, 185)
                elseif l1_3 == l0_1.scene then
                    layerPosition(l0_0.layerNumber.menu + l0_1.scene, 335, 207)
                elseif l1_3 == l0_1.cg then
                    layerPosition(l0_0.layerNumber.menu + l0_1.cg, 340, 223)
                elseif l1_3 == l0_1.music then
                    layerPosition(l0_0.layerNumber.menu + l0_1.music, 352, 243)
                end
                if l0_1.novel <= l1_3 then
                    layerVisible(l0_0.layerNumber.menu + l1_3, false)
                end
            end
            l0_3(l0_0.layerNumber.menu + 1, l0_0.layerKey2[1])
        else
            l0_1 = {story = 1, fragment = 2, section7 = 3, library = 4, option = 5, save = 6, load = 7, novel = 8, scene = 9, cg = 10, music = 11}
            for l1_3 = 1, #l0_0.layerKey3, 1 do
                layerCopy(l0_0.layerNumber.menu + l1_3, layerName[l0_0.layerKey3[l1_3]])
                l0_2(l0_0.layerNumber.menu + l1_3, l0_0.layerKey3[l1_3])
                if l1_3 == l0_1.story then
                    layerPosition(l0_0.layerNumber.menu + l0_1.story, 210, 110)
                elseif l1_3 == l0_1.fragment then
                    layerPosition(l0_0.layerNumber.menu + l0_1.fragment, 190, 145)
                elseif l1_3 == l0_1.section7 then
                    layerPosition(l0_0.layerNumber.menu + l0_1.section7, 194, 180)
                elseif l1_3 == l0_1.library then
                    layerPosition(l0_0.layerNumber.menu + l0_1.library, 205, 208)
                elseif l1_3 == l0_1.option then
                    layerPosition(l0_0.layerNumber.menu + l0_1.option, 215, 241)
                elseif l1_3 == l0_1.save then
                    layerPosition(l0_0.layerNumber.menu + l0_1.save, 48, 145)
                elseif l1_3 == l0_1.load then
                    layerPosition(l0_0.layerNumber.menu + l0_1.load, 330, 142)
                elseif l1_3 == l0_1.novel then
                    layerPosition(l0_0.layerNumber.menu + l0_1.novel, 353, 185)
                elseif l1_3 == l0_1.scene then
                    layerPosition(l0_0.layerNumber.menu + l0_1.scene, 335, 207)
                elseif l1_3 == l0_1.cg then
                    layerPosition(l0_0.layerNumber.menu + l0_1.cg, 340, 223)
                elseif l1_3 == l0_1.music then
                    layerPosition(l0_0.layerNumber.menu + l0_1.music, 352, 243)
                end
                if l0_1.novel <= l1_3 then
                    layerVisible(l0_0.layerNumber.menu + l1_3, false)
                end
            end
            l0_3(l0_0.layerNumber.menu + 1, l0_0.layerKey3[1])
        end
    end
    if not (systemSave.libFlag == true) then
        layerVisible(l0_0.layerNumber.menu + l0_1.library, false)
    end
    switchScreen(0, "", 30)
end
local l0_5 = function()
    layerCopy(0, backLayerName.black)
    layerAlpha(0, 0)
    layerMoveAlpha(0, 60, 20)
    wait(20)
end
local l0_6 = function()
    layerMoveAlpha(0, 0, 20)
    wait(20)
    layerLoad(0, "")
end
local l0_7 = function()
    pageScreen(1)
    fontClear()
    l0_5()
    runListLoad()
    pageScreen(0)
    if succeedLoadGamedata() then
        runAutoLoad()
        cInitGame()
        switchScreen(0, "", 60)
        applyGamedata()
    end
end
local l0_8 = function()
    pageScreen(1)
    fontClear()
    l0_5()
    runListSave()
    autoSystemSave(1)
    pageScreen(0)
end
main = function()
advPart(false)
logEnable(false)
systemConfig.unsetConfigButton()
cInitGame()
l0_4()
local l1_0 = 1
local l1_1 = 0
local l1_2 = false
local l1_3 = false
if gameSave.startMenuState == 0 then
    while true do
        if l1_3 == false then
            if pressButton("UP") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    if l0_1.option < l1_0 then
                        l1_0 = l0_1.prologue
                    else
                        l1_0 = l1_0 - 1 < l0_1.prologue and l0_1.prologue or l1_0 - 1
                    end
                    if l1_0 == l0_1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 - 1 < l0_1.prologue and l0_1.prologue or l1_0 - 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("DOWN") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    if l0_1.option < l1_0 then
                        l1_0 = l0_1.library
                    else
                        l1_0 = l1_0 + 1 > l0_1.option and l0_1.option or l1_0 + 1
                    end
                    if l1_0 == l0_1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 + 1 > l0_1.option and l0_1.option or l1_0 + 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("RIGHT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = l0_1.load
                    l1_2 = true
                end
            end
            if pressButton("LEFT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = l0_1.prologue
                    l1_2 = true
                end
            end
            if pressButton("CIRCLE") == true then
                if l1_2 == false then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if l1_0 == l0_1.prologue then
                        cInitGame()
                        switchScreen(0, "", 60)
                        doScriptScene = "sof_10"
                        run(cGetFileName("script", "snr_s0_10_f"))
                        quit()
                    elseif l1_0 == l0_1.library then
                        l1_3 = true
                        if not (systemSave.novelFlag == true) then
                            l1_0 = l0_1.scene
                        else
                            l1_0 = l0_1.novel
                        end
                        for l1_7 = 1, #l0_0.layerKey0, 1 do
                            if l1_7 < l0_1.novel then
                                if not (l1_7 == l0_1.library) then
                                    layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 50, 30)
                                end
                            elseif l1_7 == l0_1.novel and not (systemSave.novelFlag == true) or l1_7 == l0_1.music and not (systemSave.musicFlag == true) then
                                layerVisible(l0_0.layerNumber.menu + l1_7, false)
                            else
                                layerAlpha(l0_0.layerNumber.menu + l1_7, 0)
                                layerVisible(l0_0.layerNumber.menu + l1_7, true)
                                layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                            end
                        end
                        wait(30)
                    elseif l1_0 == l0_1.option then
                        systemOption.Option()
                    elseif l1_0 == l0_1.load then
                        l0_7()
                    end
                    l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey0[l1_1])
                    l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey0[l1_0])
                end
            end
        else
            if pressButton("UP") == true then
                if l1_2 == false then
                    keyPlaySE(seName.arrowKey)
                    l1_1 = l1_0
                    l1_0 = l1_0 - 1 < l0_1.novel and l0_1.novel or l1_0 - 1
                    if l1_0 == l0_1.novel then
                        if not (systemSave.novelFlag == true) then
                            l1_0 = l1_0 + 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("DOWN") == true then
                if l1_2 == false then
                    keyPlaySE(seName.arrowKey)
                    l1_1 = l1_0
                    l1_0 = l1_0 + 1 > l0_1.music and l0_1.music or l1_0 + 1
                    if l1_0 == l0_1.music then
                        if not (systemSave.musicFlag == true) then
                            l1_0 = l1_0 - 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("CIRCLE") == true then
                if l1_2 == false then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if l1_0 == l0_1.novel then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_novel"))
                        quit()
                    elseif l1_0 == l0_1.scene then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_memory"))
                        quit()
                    elseif l1_0 == l0_1.cg then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_graphic"))
                        quit()
                    elseif l1_0 == l0_1.music then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_music"))
                        quit()
                    end
                end
            end
            if pressButton("CROSS") == true then
                if l1_2 == false then
                    keyPlaySE(seName.cross)
                    l1_3 = false
                    l1_1 = l1_0
                    l1_0 = l0_1.library
                    for l1_7 = 1, l0_1.music, 1 do
                        if l1_7 < l0_1.novel then
                            layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                        else
                            layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 0, 30)
                        end
                    end
                    wait(30)
                    for l1_7 = l0_1.novel, l0_1.music, 1 do
                        layerVisible(l0_0.layerNumber.menu + l1_7, false)
                    end
                    l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey0[l1_1])
                    l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey0[l1_0])
                end
            end
        end
        if l1_2 == true then
            l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey0[l1_1])
            l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey0[l1_0])
            keyPlaySE(seName.arrowKey)
            wait(3)
            l1_2 = false
        end
        wait(2)
    end
elseif gameSave.startMenuState == 1 then
    while true do
        if l1_3 == false then
            if pressButton("UP") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    if l0_1.option < l1_0 then
                        l1_0 = l0_1.story
                    else
                        l1_0 = l1_0 - 1 < l0_1.story and l0_1.story or l1_0 - 1
                    end
                    if l1_0 == l0_1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 - 1 < l0_1.story and l0_1.story or l1_0 - 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("DOWN") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    if l0_1.option < l1_0 then
                        l1_0 = l0_1.library
                    else
                        l1_0 = l1_0 + 1 > l0_1.option and l0_1.option or l1_0 + 1
                    end
                    if l1_0 == l0_1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 + 1 > l0_1.option and l0_1.option or l1_0 + 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("RIGHT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = l0_1.load
                    l1_2 = true
                end
            end
            if pressButton("LEFT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = l0_1.save
                    l1_2 = true
                end
            end
            if pressButton("CIRCLE") == true then
                if l1_2 == false then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if l1_0 == l0_1.story then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_story_main"))
                        quit()
                    elseif l1_0 == l0_1.library then
                        l1_3 = true
                        if not (systemSave.novelFlag == true) then
                            l1_0 = l0_1.scene
                        else
                            l1_0 = l0_1.novel
                        end
                        for l1_7 = 1, #l0_0.layerKey1, 1 do
                            if l1_7 < l0_1.novel then
                                if not (l1_7 == l0_1.library) then
                                    layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 50, 30)
                                end
                            elseif l1_7 == l0_1.novel and not (systemSave.novelFlag == true) or l1_7 == l0_1.music and not (systemSave.musicFlag == true) then
                                layerVisible(l0_0.layerNumber.menu + l1_7, false)
                            else
                                layerAlpha(l0_0.layerNumber.menu + l1_7, 0)
                                layerVisible(l0_0.layerNumber.menu + l1_7, true)
                                layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                            end
                        end
                        wait(30)
                        l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey1[l1_1])
                        l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey1[l1_0])
                    elseif l1_0 == l0_1.option then
                        systemOption.Option()
                    elseif l1_0 == l0_1.save then
                        l0_8()
                    elseif l1_0 == l0_1.load then
                        l0_7()
                    end
                end
            end
        else
            if pressButton("UP") == true then
                if l1_2 == false then
                    keyPlaySE(seName.arrowKey)
                    l1_1 = l1_0
                    l1_0 = l1_0 - 1 < l0_1.novel and l0_1.novel or l1_0 - 1
                    if l1_0 == l0_1.novel then
                        if not (systemSave.novelFlag == true) then
                            l1_0 = l1_0 + 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("DOWN") == true then
                if l1_2 == false then
                    keyPlaySE(seName.arrowKey)
                    l1_1 = l1_0
                    l1_0 = l1_0 + 1 > l0_1.music and l0_1.music or l1_0 + 1
                    if l1_0 == l0_1.music then
                        if not (systemSave.musicFlag == true) then
                            l1_0 = l1_0 - 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("CIRCLE") == true then
                if l1_2 == false then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if l1_0 == l0_1.novel then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_novel"))
                        quit()
                    elseif l1_0 == l0_1.scene then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_memory"))
                        quit()
                    elseif l1_0 == l0_1.cg then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_graphic"))
                        quit()
                    elseif l1_0 == l0_1.music then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_music"))
                        quit()
                    end
                end
            end
            if pressButton("CROSS") == true then
                if l1_2 == false then
                    keyPlaySE(seName.cross)
                    l1_3 = false
                    l1_1 = l1_0
                    l1_0 = l0_1.library
                    for l1_7 = 1, l0_1.music, 1 do
                        if l1_7 < l0_1.novel then
                            layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                        else
                            layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 0, 30)
                        end
                    end
                    wait(30)
                    for l1_7 = l0_1.novel, l0_1.music, 1 do
                        layerVisible(l0_0.layerNumber.menu + l1_7, false)
                    end
                    l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey1[l1_1])
                    l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey1[l1_0])
                end
            end
        end
        if l1_2 == true then
            l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey1[l1_1])
            l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey1[l1_0])
            keyPlaySE(seName.arrowKey)
            wait(3)
            l1_2 = false
        end
        wait(2)
    end
elseif gameSave.startMenuState == 2 then
    if gameSave.myCard[140].hold == -1 then
        while true do
            if l1_3 == false then
                if pressButton("UP") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        if l0_1.option < l1_0 then
                            l1_0 = l0_1.story
                        else
                            l1_0 = l1_0 - 1 < l0_1.story and l0_1.story or l1_0 - 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("DOWN") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        if l0_1.option < l1_0 then
                            l1_0 = l0_1.fragment
                        else
                            l1_0 = l1_0 + 1 > l0_1.option and l0_1.option or l1_0 + 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("RIGHT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = l0_1.load
                        l1_2 = true
                    end
                end
                if pressButton("LEFT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = l0_1.save
                        l1_2 = true
                    end
                end
                if pressButton("CIRCLE") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if l1_0 == l0_1.story then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_story_main"))
                            quit()
                        elseif l1_0 == l0_1.fragment then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_fragment_main"))
                            quit()
                        elseif l1_0 == l0_1.library then
                            l1_3 = true
                            if not (systemSave.novelFlag == true) then
                                l1_0 = l0_1.scene
                            else
                                l1_0 = l0_1.novel
                            end
                            for l1_7 = 1, #l0_0.layerKey2, 1 do
                                if l1_7 < l0_1.novel then
                                    if not (l1_7 == l0_1.library) then
                                        layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 50, 30)
                                    end
                                elseif l1_7 == l0_1.novel and not (systemSave.novelFlag == true) or l1_7 == l0_1.music and not (systemSave.musicFlag == true) then
                                    layerVisible(l0_0.layerNumber.menu + l1_7, false)
                                else
                                    layerAlpha(l0_0.layerNumber.menu + l1_7, 0)
                                    layerVisible(l0_0.layerNumber.menu + l1_7, true)
                                    layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                                end
                            end
                            wait(30)
                            l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey2[l1_1])
                            l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey2[l1_0])
                        elseif l1_0 == l0_1.option then
                            systemOption.Option()
                        elseif l1_0 == l0_1.save then
                            l0_8()
                        elseif l1_0 == l0_1.load then
                            l0_7()
                        end
                    end
                end
            else
                if pressButton("UP") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.arrowKey)
                        l1_1 = l1_0
                        l1_0 = l1_0 - 1 < l0_1.novel and l0_1.novel or l1_0 - 1
                        if l1_0 == l0_1.novel then
                            if not (systemSave.novelFlag == true) then
                                l1_0 = l1_0 + 1
                            end
                        end
                        l1_2 = true
                    end
                end
                if pressButton("DOWN") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.arrowKey)
                        l1_1 = l1_0
                        l1_0 = l1_0 + 1 > l0_1.music and l0_1.music or l1_0 + 1
                        if l1_0 == l0_1.music then
                            if not (systemSave.musicFlag == true) then
                                l1_0 = l1_0 - 1
                            end
                        end
                        l1_2 = true
                    end
                end
                if pressButton("CIRCLE") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if l1_0 == l0_1.novel then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_novel"))
                            quit()
                        elseif l1_0 == l0_1.scene then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_memory"))
                            quit()
                        elseif l1_0 == l0_1.cg then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_graphic"))
                            quit()
                        elseif l1_0 == l0_1.music then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_music"))
                            quit()
                        end
                    end
                end
                if pressButton("CROSS") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.cross)
                        l1_3 = false
                        l1_1 = l1_0
                        l1_0 = l0_1.library
                        for l1_7 = 1, l0_1.music, 1 do
                            if l1_7 < l0_1.novel then
                                layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                            else
                                layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 0, 30)
                            end
                        end
                        wait(30)
                        for l1_7 = l0_1.novel, l0_1.music, 1 do
                            layerVisible(l0_0.layerNumber.menu + l1_7, false)
                        end
                        l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey2[l1_1])
                        l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey2[l1_0])
                    end
                end
            end
            if l1_2 == true then
                l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey2[l1_1])
                l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey2[l1_0])
                keyPlaySE(seName.arrowKey)
                wait(3)
                l1_2 = false
            end
            wait(2)
        end
    else
        while true do
            if l1_3 == false then
                if pressButton("UP") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        if l0_1.option < l1_0 then
                            l1_0 = l0_1.story
                        else
                            l1_0 = l1_0 - 1 < l0_1.story and l0_1.story or l1_0 - 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("DOWN") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        if l0_1.option < l1_0 then
                            l1_0 = l0_1.fragment
                        else
                            l1_0 = l1_0 + 1 > l0_1.option and l0_1.option or l1_0 + 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("RIGHT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = l0_1.load
                        l1_2 = true
                    end
                end
                if pressButton("LEFT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = l0_1.save
                        l1_2 = true
                    end
                end
                if pressButton("CIRCLE") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if l1_0 == l0_1.story then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_story_main"))
                            quit()
                        elseif l1_0 == l0_1.fragment then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_fragment_main"))
                            quit()
                        elseif l1_0 == l0_1.section7 then
                            cInitGame()
                            switchScreen(0, "", 60)
                            doScriptScene = "s7f-10"
                            run(cGetFileName("script", "snr_s7_10_f"))
                            quit()
                        elseif l1_0 == l0_1.library then
                            l1_3 = true
                            if not (systemSave.novelFlag == true) then
                                l1_0 = l0_1.scene
                            else
                                l1_0 = l0_1.novel
                            end
                            for l1_7 = 1, 11, 1 do
                                if l1_7 < l0_1.novel then
                                    if not (l1_7 == l0_1.library) then
                                        layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 50, 30)
                                    end
                                elseif l1_7 == l0_1.novel and not (systemSave.novelFlag == true) or l1_7 == l0_1.music and not (systemSave.musicFlag == true) then
                                    layerVisible(l0_0.layerNumber.menu + l1_7, false)
                                else
                                    layerAlpha(l0_0.layerNumber.menu + l1_7, 0)
                                    layerVisible(l0_0.layerNumber.menu + l1_7, true)
                                    layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                                end
                            end
                            wait(30)
                        elseif l1_0 == l0_1.option then
                            systemOption.Option()
                        elseif l1_0 == l0_1.save then
                            l0_8()
                        elseif l1_0 == l0_1.load then
                            l0_7()
                        end
                        l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey3[l1_1])
                        l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey3[l1_0])
                    end
                end
            else
                if pressButton("UP") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.arrowKey)
                        l1_1 = l1_0
                        l1_0 = l1_0 - 1 < l0_1.novel and l0_1.novel or l1_0 - 1
                        if l1_0 == l0_1.novel then
                            if not (systemSave.novelFlag == true) then
                                l1_0 = l1_0 + 1
                            end
                        end
                        l1_2 = true
                    end
                end
                if pressButton("DOWN") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.arrowKey)
                        l1_1 = l1_0
                        l1_0 = l1_0 + 1 > l0_1.music and l0_1.music or l1_0 + 1
                        if l1_0 == l0_1.music then
                            if not (systemSave.musicFlag == true) then
                                l1_0 = l1_0 - 1
                            end
                        end
                        l1_2 = true
                    end
                end
                if pressButton("CIRCLE") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if l1_0 == l0_1.novel then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_novel"))
                            quit()
                        elseif l1_0 == l0_1.scene then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_memory"))
                            quit()
                        elseif l1_0 == l0_1.cg then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_graphic"))
                            quit()
                        elseif l1_0 == l0_1.music then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_music"))
                            quit()
                        end
                    end
                end
                if pressButton("CROSS") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.cross)
                        l1_3 = false
                        l1_1 = l1_0
                        l1_0 = l0_1.library
                        for l1_7 = 1, l0_1.music, 1 do
                            if l1_7 < l0_1.novel then
                                layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 100, 30)
                            else
                                layerMoveAlpha(l0_0.layerNumber.menu + l1_7, 0, 30)
                            end
                        end
                        wait(30)
                        for l1_7 = l0_1.novel, l0_1.music, 1 do
                            layerVisible(l0_0.layerNumber.menu + l1_7, false)
                        end
                        l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey3[l1_1])
                        l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey3[l1_0])
                    end
                end
            end
            if l1_2 == true then
                l0_2(l0_0.layerNumber.menu + l1_1, l0_0.layerKey3[l1_1])
                l0_3(l0_0.layerNumber.menu + l1_0, l0_0.layerKey3[l1_0])
                keyPlaySE(seName.arrowKey)
                wait(3)
                l1_2 = false
            end
            wait(2)
        end
    end
end
end

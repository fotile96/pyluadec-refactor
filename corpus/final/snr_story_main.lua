local l0_0 = function(l1_0, l1_1)
    if l1_1 >= 90 then
        layerClip(l1_0, 0, 180, 75, 200)
    elseif l1_1 >= 80 then
        layerClip(l1_0, 0, 160, 75, 180)
    elseif l1_1 >= 70 then
        layerClip(l1_0, 0, 140, 75, 160)
    elseif l1_1 >= 60 then
        layerClip(l1_0, 0, 120, 75, 140)
    elseif l1_1 >= 50 then
        layerClip(l1_0, 0, 100, 75, 120)
    elseif l1_1 >= 40 then
        layerClip(l1_0, 0, 80, 75, 100)
    elseif l1_1 >= 30 then
        layerClip(l1_0, 0, 60, 75, 80)
    elseif l1_1 >= 20 then
        layerClip(l1_0, 0, 40, 75, 60)
    elseif l1_1 >= 10 then
        layerClip(l1_0, 0, 20, 75, 40)
    else
        layerClip(l1_0, 0, 0, 75, 20)
    end
end
local l0_1 = function(l1_0, l1_1)
    local l1_2 = 0
    local l1_3 = 0
    local l1_4 = 2
    local l1_5 = 0
    local l1_6 = l1_0 - l1_1
    if not (l1_0 == l1_1) then
        if l1_6 < 2 then
            if l1_6 > -2 then
                l1_5 = 10
            end
        end
    end
    local l1_7 = 0
    local l1_8 = 0
    local l1_9 = 0
    local l1_10 = 0
    local l1_11 = 0
    local l1_12 = 0
    local l1_13 = 0
    local l1_14 = 0
    local l1_15 = 0
    local l1_16 = 0
    local l1_17 = 0
    for l1_21 = layerName.plot - 4, layerName.plot + 50, 1 do
        layerLoad(l1_21, "")
    end
    if not (l1_0 == 1) then
        layerCopy(layerName.plot + 40, layerName.sys_2_d)
        layerClip(layerName.plot + 40, 0, 0, 30, 15)
        layerPosition(layerName.plot + 40, 5, 80)
    end
    if not (l1_0 == comSectionStoryGetCount()) then
        layerCopy(layerName.plot + 41, layerName.sys_2_d)
        layerClip(layerName.plot + 41, 30, 0, 60, 15)
        layerPosition(layerName.plot + 41, 449, 80)
    end
    local l1_18 = sceneId2aCard[gameSave.storyRoute[l1_0].sceneId]
    layerCopy(layerName.cardLabel1, sceneState[l1_18].layerName)
    layerClip(layerName.cardLabel1, sceneState[l1_18].clipX, sceneState[l1_18].clipY, sceneState[l1_18].clipX + 145, sceneState[l1_18].clipY + 15)
    layerPosition(layerName.cardLabel1, 330, 5)
    if l1_0 < comSectionStoryGetCount() - 2 and l1_6 == -1 then
        l1_7 = 80
        l1_9 = 372
        l1_11 = 409
        l1_13 = 103
        l1_15 = 100
        l1_8 = 70
        l1_10 = 386
        l1_12 = 419
        l1_14 = 100
        l1_16 = 0
        l1_17 = l1_0 + 3
    elseif 3 < l1_0 then
        if l1_6 == 1 then
            l1_7 = 80
            l1_9 = 29
            l1_11 = 65
            l1_13 = 103
            l1_15 = 100
            l1_8 = 70
            l1_10 = 19
            l1_12 = 50
            l1_14 = 100
            l1_16 = 0
            l1_17 = l1_0 - 3
        end
    end
    if not (l1_17 == 0) then
        local l1_19 = sceneId2aCard[gameSave.storyRoute[l1_17].sceneId]
        layerCopy(layerName.plot - 4, plotState[l1_19].layerName)
        layerClip(layerName.plot - 4, plotState[l1_19].clipX, plotState[l1_19].clipY, plotState[l1_19].clipX + 82, plotState[l1_19].clipY + 48)
        layerCopy(layerName.plot - 3, layerName.sys_4_b)
        l0_0(layerName.plot - 3, gameSave.storyRoute[l1_17].ayanoTime)
        if string.sub(gameSave.storyRoute[l1_17].sceneId, -4) == "_sel" then
            layerCopy(layerName.plot - 2, layerName.sys_2_c)
            if gameSave.myCard[l1_19].hold == -1 then
                if l1_4 == 2 then
                    layerClip(layerName.plot - 2, 0, 95, 83, 114)
                else
                    layerClip(layerName.plot - 2, 0, 76, 83, 95)
                end
            elseif l1_4 == 2 then
                layerClip(layerName.plot - 2, 0, 19, 83, 38)
            else
                layerClip(layerName.plot - 2, 0, 0, 83, 19)
            end
        else
            layerCopy(layerName.plot - 2, layerName.sys_2_b)
            if gameSave.myCard[l1_19].hold == -1 then
                if l1_4 == 2 then
                    layerClip(layerName.plot - 2, 0, 95, 83, 114)
                else
                    layerClip(layerName.plot - 2, 0, 76, 83, 95)
                end
            elseif l1_4 == 2 then
                layerClip(layerName.plot - 2, 0, 19, 83, 38)
            else
                layerClip(layerName.plot - 2, 0, 0, 83, 19)
            end
        end
        layerScale(layerName.plot - 4, l1_7, l1_7)
        layerScale(layerName.plot - 2, l1_7, l1_7)
        layerScale(layerName.plot - 3, l1_7, l1_7)
        layerMoveScale(layerName.plot - 4, l1_8, l1_8, l1_5)
        layerMoveScale(layerName.plot - 2, l1_8, l1_8, l1_5)
        layerMoveScale(layerName.plot - 3, l1_8, l1_8, l1_5)
        layerPosition(layerName.plot - 4, l1_9, 60)
        layerPosition(layerName.plot - 2, l1_9, l1_13)
        layerPosition(layerName.plot - 3, l1_9 + 4, 85)
        layerMovePosition(layerName.plot - 4, l1_10, 60, l1_5)
        layerMovePosition(layerName.plot - 2, l1_10, l1_14, l1_5)
        layerMovePosition(layerName.plot - 3, l1_10 + 4, 85, l1_5)
        layerAlpha(layerName.plot - 4, l1_15)
        layerAlpha(layerName.plot - 2, l1_15)
        layerAlpha(layerName.plot - 3, l1_15)
        layerMoveAlpha(layerName.plot - 4, l1_16, l1_5)
        layerMoveAlpha(layerName.plot - 2, l1_16, l1_5)
        layerMoveAlpha(layerName.plot - 3, l1_16, l1_5)
    end
    if 2 < l1_0 then
        l1_0 = l1_0 - 2
        l1_4 = 0
    elseif 1 < l1_0 then
        l1_0 = l1_0 - 1
        l1_4 = 1
    end
    for l1_22 = 0, 4, 1 do
        if not (gameSave.storyRoute[l1_0 + l1_22].sceneId == -1) then
            local l1_23 = sceneId2aCard[gameSave.storyRoute[l1_0 + l1_22].sceneId]
            layerCopy(layerName.plot + l1_22 * 4, plotState[l1_23].layerName)
            layerClip(layerName.plot + l1_22 * 4, plotState[l1_23].clipX, plotState[l1_23].clipY, plotState[l1_23].clipX + 82, plotState[l1_23].clipY + 48)
            layerCopy(layerName.plot + l1_22 * 4 + 1, layerName.sys_4_b)
            l0_0(layerName.plot + l1_22 * 4 + 1, gameSave.storyRoute[l1_0 + l1_22].ayanoTime)
            if string.sub(gameSave.storyRoute[l1_0 + l1_22].sceneId, -4) == "_sel" then
                layerCopy(layerName.plot + l1_22 * 4 + 2, layerName.sys_2_c)
                if gameSave.myCard[l1_23].hold == -1 then
                    if l1_4 == 2 then
                        layerClip(layerName.plot + l1_22 * 4 + 2, 0, 95, 83, 114)
                    else
                        layerClip(layerName.plot + l1_22 * 4 + 2, 0, 76, 83, 95)
                    end
                elseif l1_4 == 2 then
                    layerClip(layerName.plot + l1_22 * 4 + 2, 0, 19, 83, 38)
                else
                    layerClip(layerName.plot + l1_22 * 4 + 2, 0, 0, 83, 19)
                end
            else
                layerCopy(layerName.plot + l1_22 * 4 + 2, layerName.sys_2_b)
                if gameSave.myCard[l1_23].hold == -1 then
                    if l1_4 == 2 then
                        layerClip(layerName.plot + l1_22 * 4 + 2, 0, 95, 83, 114)
                    else
                        layerClip(layerName.plot + l1_22 * 4 + 2, 0, 76, 83, 95)
                    end
                elseif l1_4 == 2 then
                    layerClip(layerName.plot + l1_22 * 4 + 2, 0, 19, 83, 38)
                else
                    layerClip(layerName.plot + l1_22 * 4 + 2, 0, 0, 83, 19)
                end
            end
            if l1_4 == 0 then
                if 0 < l1_6 then
                    l1_7 = 90
                    l1_9 = (l1_4 + 1) * 95 + 19
                    l1_11 = (l1_4 + 1) * 95 + 55
                    l1_13 = 106
                    l1_15 = 100
                elseif l1_6 < 0 then
                    l1_7 = 70
                    l1_9 = l1_4 * 95 + 19
                    l1_11 = l1_4 * 95 + 50
                    l1_13 = 100
                    l1_15 = 0
                end
                l1_8 = 80
                l1_10 = l1_4 * 95 + 29
                l1_12 = l1_4 * 95 + 65
                l1_14 = 103
                l1_16 = 100
            elseif l1_4 == 1 then
                if 0 < l1_6 then
                    l1_7 = 100
                    l1_9 = (l1_4 + 1) * 95 + 9
                    l1_11 = (l1_4 + 1) * 95 + 50
                    l1_13 = 109
                    l1_15 = 100
                elseif l1_6 < 0 then
                    l1_7 = 80
                    l1_9 = (l1_4 - 1) * 95 + 29
                    l1_11 = (l1_4 - 1) * 95 + 65
                    l1_13 = 103
                    l1_15 = 100
                end
                l1_8 = 90
                l1_10 = l1_4 * 95 + 14
                l1_12 = l1_4 * 95 + 55
                l1_14 = 106
                l1_16 = 100
            elseif l1_4 == 2 then
                if 0 < l1_6 then
                    l1_9 = (l1_4 + l1_6) * 95 + 4
                    l1_11 = (l1_4 + l1_6) * 95 + 45
                elseif l1_6 < 0 then
                    l1_9 = (l1_4 + l1_6) * 95 + 14
                    l1_11 = (l1_4 + l1_6) * 95 + 55
                end
                l1_13 = 106
                l1_7 = 90
                l1_15 = 100
                l1_8 = 100
                l1_10 = l1_4 * 95 + 9
                l1_12 = l1_4 * 95 + 50
                l1_14 = 109
                l1_16 = 100
            elseif l1_4 == 3 then
                if 0 < l1_6 then
                    l1_7 = 80
                    l1_9 = (l1_4 + 1) * 95 - 8
                    l1_11 = (l1_4 + 1) * 95 + 29
                    l1_13 = 103
                    l1_15 = 100
                elseif l1_6 < 0 then
                    l1_7 = 100
                    l1_9 = (l1_4 - 1) * 95 + 9
                    l1_11 = (l1_4 - 1) * 95 + 50
                    l1_13 = 109
                    l1_15 = 100
                end
                l1_8 = 90
                l1_10 = l1_4 * 95 + 4
                l1_12 = l1_4 * 95 + 45
                l1_14 = 106
                l1_16 = 100
            elseif l1_4 == 4 then
                if 0 < l1_6 then
                    l1_7 = 70
                    l1_9 = l1_4 * 95
                    l1_11 = l1_4 * 95 + 33
                    l1_13 = 100
                    l1_15 = 0
                elseif l1_6 < 0 then
                    l1_7 = 90
                    l1_9 = (l1_4 - 1) * 95 + 4
                    l1_11 = (l1_4 - 1) * 95 + 45
                    l1_13 = 106
                    l1_15 = 100
                end
                l1_8 = 80
                l1_10 = l1_4 * 95 - 8
                l1_12 = l1_4 * 95 + 29
                l1_14 = 103
                l1_16 = 100
            end
            layerScale(layerName.plot + l1_22 * 4, l1_7, l1_7)
            layerScale(layerName.plot + l1_22 * 4 + 2, l1_7, l1_7)
            layerScale(layerName.plot + l1_22 * 4 + 1, l1_7, l1_7)
            layerMoveScale(layerName.plot + l1_22 * 4, l1_8, l1_8, l1_5)
            layerMoveScale(layerName.plot + l1_22 * 4 + 2, l1_8, l1_8, l1_5)
            layerMoveScale(layerName.plot + l1_22 * 4 + 1, l1_8, l1_8, l1_5)
            layerPosition(layerName.plot + l1_22 * 4, l1_9, 60)
            layerPosition(layerName.plot + l1_22 * 4 + 2, l1_9, l1_13)
            layerPosition(layerName.plot + l1_22 * 4 + 1, l1_9 + 4, 85)
            layerMovePosition(layerName.plot + l1_22 * 4, l1_10, 60, l1_5)
            layerMovePosition(layerName.plot + l1_22 * 4 + 2, l1_10, l1_14, l1_5)
            layerMovePosition(layerName.plot + l1_22 * 4 + 1, l1_10 + 4, 85, l1_5)
            layerAlpha(layerName.plot + l1_22 * 4, l1_15)
            layerAlpha(layerName.plot + l1_22 * 4 + 2, l1_15)
            layerAlpha(layerName.plot + l1_22 * 4 + 1, l1_15)
            layerMoveAlpha(layerName.plot + l1_22 * 4, l1_16, l1_5)
            layerMoveAlpha(layerName.plot + l1_22 * 4 + 2, l1_16, l1_5)
            layerMoveAlpha(layerName.plot + l1_22 * 4 + 1, l1_16, l1_5)
            l1_3 = l1_3 + 1
            l1_4 = l1_4 + 1
            if 5 <= l1_3 or l1_4 == 5 then
                break
            end
        else
            break
        end
    end
end
local l0_2 = function()
    savedataTitle("ストーリーモード", "")
    wait(1)
    cInitGame()
    layerCopy(100, layerName.effectBlack)
    layerCopy(layerName.bg1, layerName.bg_1_a_0)
    layerCopy(layerName.bg1 + 1, layerName.sys_2_a)
    layerClip(layerName.bg1 + 1, 0, 0, 139, 37)
    layerPosition(layerName.bg1 + 1, 5, 5)
    layerCopy(layerName.bg1 + 2, layerName.sys_2_a)
    layerClip(layerName.bg1 + 2, 0, 40, 139, 120)
    layerPosition(layerName.bg1 + 2, 195, 56)
    layerCopy(layerName.bg1 + 3, layerName.sys_2_a)
    layerClip(layerName.bg1 + 3, 0, 120, 139, 195)
    layerPosition(layerName.bg1 + 3, 338, 190)
    l0_1(selectItemNo, selectItemNo)
    layerLoadAsync(0, layerName.card1, cGetFileName("card", "crd_1_a"))
    layerMoveAlpha(100, 0, 60)
    wait(60)
    layerLoad(100, "")
end
main = function()
advPart(false)
logEnable(false)
systemConfig.unsetConfigButton()
if gameSave.tutorial.firstFragment == 0 then
    if gameSave.startMenuState == 1 then
        doScriptScene = "s1s_10"
        run(cGetFileName("script", "snr_s1_10_s"))
        quit()
    else
        vms(16817, "NONVOICE", "【■おしらせ】ゲームメニューに、『Ｆｒａｇｍｅｎｔ』モードが追加されました。")
        vms(16818, "NONVOICE", "【■おしらせ】物語の続きはＦｒａｇｍｅｎｔモードより参照することができます。")
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
end
local l1_0 = comSectionStoryGetCount()
if l1_0 == 0 then
    doScriptScene = "s1s_20"
    run(cGetFileName("script", "snr_s1_10_s"))
    quit()
end
if selectItemNo < 1 then
    selectItemNo = l1_0
end
if l1_0 < selectItemNo then
    selectItemNo = l1_0
end
l0_2()
local l1_1 = false
local l1_2 = false
local l1_3 = 0
local l1_4 = selectItemNo
local l1_5 = l1_4
local l1_6 = false
local l1_7 = 1
local l1_8 = 1
local l1_9 = 1
systemConfig.setConfigButton()
while true do
    if pressButton("RIGHT") == true then
        if l1_6 == false then
            if l1_4 < l1_0 then
                l1_5 = l1_4
                l1_4 = l1_0 < l1_4 + 1 and l1_0 or l1_4 + 1
                l1_6 = true
            end
        end
    end
    if pressButton("LEFT") == true then
        if l1_6 == false then
            if 1 < l1_4 then
                l1_5 = l1_4
                l1_4 = l1_4 - 1
                l1_6 = true
            end
        end
    end
    if pressButton("R") == true then
        if l1_6 == false then
            l1_5 = l1_4
            for l1_13 = l1_4 + 1, l1_0, 1 do
                local l1_14 = sceneId2aCard[gameSave.storyRoute[l1_13].sceneId]
                l1_4 = l1_13
                if gameSave.myCard[l1_14].hold == -1 then
                    l1_4 = l1_13
                    break
                end
            end
            wait(5)
            l1_6 = true
        end
    end
    if pressButton("L") == true then
        if l1_6 == false then
            l1_5 = l1_4
            for l1_13 = l1_4 - 1, 1, -1 do
                local l1_14 = sceneId2aCard[gameSave.storyRoute[l1_13].sceneId]
                l1_4 = l1_13
                if gameSave.myCard[l1_14].hold == -1 then
                    l1_4 = l1_13
                    break
                end
            end
            wait(5)
            l1_6 = true
        end
    end
    if l1_6 == true then
        keyPlaySE(seName.arrowKey)
        fontClear()
        l0_1(l1_4, l1_5)
        l1_3 = 0
        l1_6 = false
        layerLoad(layerName.card1, "")
        layerLoad(layerName.card3, "")
        wait(3)
    end
    local l1_10 = sceneId2aCard[gameSave.storyRoute[l1_4].sceneId]
    if not (gameSave.myCard[l1_10].hold == -1) then
        if l1_3 <= 3 then
            if 3 <= l1_3 then
                layerLoadAsync(0, layerName.card1, cGetFileName("card", "crd_" .. l1_10 .. "_a"))
                l1_2 = true
            end
            l1_3 = l1_3 + 1 > 4 and 4 or l1_3 + 1
        end
    end
    if l1_2 == true then
        if layerIsLoad(layerName.card1) == true then
            layerVisible(layerName.card1, true)
            layerAlpha(layerName.card1, 0)
            layerPosition(layerName.card1, 130, 110)
            layerMovePosition(layerName.card1, 130, 130, 10)
            layerMoveAlpha(layerName.card1, 100, 10)
            l1_2 = false
        end
    end
    if not (pressButton("CIRCLE") == true) then
        l1_7 = 0
    end
    if pressButton("CIRCLE") == true then
        if l1_7 == 0 then
            fileName = l1_4 == 1 and cGetFileName("sysgim", "sys_5_b") or cGetFileName("sysgim", "sys_5_a")
            keyPlaySE(seName.circle)
            if comDlgYesNo(fileName, 100, 80) == true then
                local l1_11 = comSectionUID2ScriptFileName(gameSave.storyRoute[l1_4].sceneId)
                doScriptScene = gameSave.storyRoute[l1_4].sceneId
                selectItemNo = -1
                gameSave.ayanoTime = gameSave.storyRoute[l1_4].ayanoTime
                cClearNumStoryRoute(l1_4)
                cInitGame()
                fontClear()
                run(cGetFileName("script", l1_11))
                quit()
            else
                l1_7 = 1
                l1_8 = 1
                l1_9 = 1
            end
            layerLoad(layerName.card3, "")
            switchScreen(0, "", 5)
            wait(5)
        end
    end
    if not (pressButton("CROSS") == true) then
        l1_8 = 0
    end
    if pressButton("CROSS") == true then
        if l1_8 == 0 then
            systemConfig.unsetConfigButton()
            keyPlaySE(seName.cross)
            selectItemNo = l1_4
            break
        end
    end
    if not (pressButton("TRIANGLE") == true) then
        l1_9 = 0
    end
    if pressButton("TRIANGLE") == true then
        if l1_9 == 0 then
            systemConfig.unsetConfigButton()
            keyPlaySE(seName.cross)
            layerCopy(199, layerName.effectBlack)
            fontClear()
            switchScreen(0, "", 60)
            selectItemNo = l1_4
            comSectionFragmentItemInit()
            cInitGame()
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
    end
    wait(2)
end
layerCopy(199, layerName.effectBlack)
fontClear()
switchScreen(0, "", 60)
cInitGame()
run(cGetFileName("script", "snr_mainmenu"))
quit()
end

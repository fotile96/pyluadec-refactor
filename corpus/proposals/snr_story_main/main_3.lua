local u0, u1
return function()
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
u0()
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
        u1(l1_4, l1_5)
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

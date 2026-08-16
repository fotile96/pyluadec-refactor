local l0_0 = function(l1_0)
    local l1_1 = true
    for l1_5 = 1, l1_0 - 1, 1 do
        local l1_6 = sceneId2aCard[gameSave.storyRoute[l1_5].sceneId]
        if not (string.sub(gameSave.storyRoute[l1_5].sceneId, -4) == "_sel") then
            if gameSave.myCard[l1_6].hold == -1 then
                l1_1 = false
            end
        end
    end
    return l1_1
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
    for l1_19 = layerName.plot - 2, layerName.plot + 50, 1 do
        layerLoad(l1_19, "")
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
    local l1_16 = sceneId2aCard[gameSave.storyRoute[l1_0].sceneId]
    layerCopy(layerName.cardLabel1, sceneState[l1_16].layerName)
    layerClip(layerName.cardLabel1, sceneState[l1_16].clipX, sceneState[l1_16].clipY, sceneState[l1_16].clipX + 145, sceneState[l1_16].clipY + 15)
    layerPosition(layerName.cardLabel1, 330, 5)
    if l1_0 < comSectionStoryGetCount() - 2 and l1_6 == -1 then
        l1_7 = 80
        l1_9 = 372
        plotLayerPositionX2 = 409
        l1_11 = 103
        l1_13 = 100
        l1_8 = 70
        l1_10 = 386
        plotLayerMovePositionX2 = 419
        l1_12 = 100
        l1_14 = 0
        l1_15 = l1_0 + 3
    elseif 3 < l1_0 then
        if l1_6 == 1 then
            l1_7 = 80
            l1_9 = 29
            plotLayerPositionX2 = 65
            l1_11 = 103
            l1_13 = 100
            l1_8 = 70
            l1_10 = 9
            plotLayerMovePositionX2 = 50
            l1_12 = 100
            l1_14 = 0
            l1_15 = l1_0 - 3
        end
    end
    if not (l1_15 == 0) then
        local l1_17 = sceneId2aCard[gameSave.storyRoute[l1_15].sceneId]
        layerCopy(layerName.plot - 1, plotState[l1_17].layerName)
        layerClip(layerName.plot - 1, plotState[l1_17].clipX, plotState[l1_17].clipY, plotState[l1_17].clipX + 82, plotState[l1_17].clipY + 48)
        if string.sub(gameSave.storyRoute[l1_15].sceneId, -4) == "_sel" then
            layerCopy(layerName.plot - 2, layerName.sys_2_c)
            if gameSave.myCard[l1_17].hold == -1 then
                if l1_4 == 2 then
                    layerClip(layerName.plot - 2, 0, 133, 83, 152)
                else
                    layerClip(layerName.plot - 2, 0, 114, 83, 133)
                end
            elseif l1_4 == 2 then
                layerClip(layerName.plot - 2, 0, 57, 83, 76)
            else
                layerClip(layerName.plot - 2, 0, 38, 83, 57)
            end
        else
            layerCopy(layerName.plot - 2, layerName.sys_2_b)
            if gameSave.myCard[l1_17].hold == -1 then
                if l1_4 == 2 then
                    layerClip(layerName.plot - 2, 0, 133, 83, 152)
                else
                    layerClip(layerName.plot - 2, 0, 114, 83, 133)
                end
            elseif l1_4 == 2 then
                layerClip(layerName.plot - 2, 0, 57, 83, 76)
            else
                layerClip(layerName.plot - 2, 0, 38, 83, 57)
            end
        end
        layerScale(layerName.plot - 1, l1_7, l1_7)
        layerScale(layerName.plot - 2, l1_7, l1_7)
        layerMoveScale(layerName.plot - 1, l1_8, l1_8, l1_5)
        layerMoveScale(layerName.plot - 2, l1_8, l1_8, l1_5)
        layerPosition(layerName.plot - 1, l1_9, 60)
        layerPosition(layerName.plot - 2, l1_9, l1_11)
        layerMovePosition(layerName.plot - 1, l1_10, 60, l1_5)
        layerMovePosition(layerName.plot - 2, l1_10, l1_12, l1_5)
        layerAlpha(layerName.plot - 1, l1_13)
        layerAlpha(layerName.plot - 2, l1_13)
        layerMoveAlpha(layerName.plot - 1, l1_14, l1_5)
        layerMoveAlpha(layerName.plot - 2, l1_14, l1_5)
    end
    if 2 < l1_0 then
        l1_0 = l1_0 - 2
        l1_4 = 0
    elseif 1 < l1_0 then
        l1_0 = l1_0 - 1
        l1_4 = 1
    end
    for l1_20 = 0, 4, 1 do
        if not (gameSave.storyRoute[l1_0 + l1_20].sceneId == -1) then
            local l1_21 = sceneId2aCard[gameSave.storyRoute[l1_0 + l1_20].sceneId]
            layerCopy(layerName.plot + l1_20 * 3, plotState[l1_21].layerName)
            layerClip(layerName.plot + l1_20 * 3, plotState[l1_21].clipX, plotState[l1_21].clipY, plotState[l1_21].clipX + 82, plotState[l1_21].clipY + 48)
            if string.sub(gameSave.storyRoute[l1_0 + l1_20].sceneId, -4) == "_sel" then
                layerCopy(layerName.plot + l1_20 * 3 + 1, layerName.sys_2_c)
                if gameSave.myCard[l1_21].hold == -1 then
                    if l1_4 == 2 then
                        layerClip(layerName.plot + l1_20 * 3 + 1, 0, 133, 83, 152)
                    else
                        layerClip(layerName.plot + l1_20 * 3 + 1, 0, 114, 83, 133)
                    end
                elseif l1_4 == 2 then
                    layerClip(layerName.plot + l1_20 * 3 + 1, 0, 57, 83, 76)
                else
                    layerClip(layerName.plot + l1_20 * 3 + 1, 0, 38, 83, 57)
                end
            else
                layerCopy(layerName.plot + l1_20 * 3 + 1, layerName.sys_2_b)
                if gameSave.myCard[l1_21].hold == -1 then
                    if l1_4 == 2 then
                        layerClip(layerName.plot + l1_20 * 3 + 1, 0, 133, 83, 152)
                    else
                        layerClip(layerName.plot + l1_20 * 3 + 1, 0, 114, 83, 133)
                    end
                elseif l1_4 == 2 then
                    layerClip(layerName.plot + l1_20 * 3 + 1, 0, 57, 83, 76)
                else
                    layerClip(layerName.plot + l1_20 * 3 + 1, 0, 38, 83, 57)
                end
            end
            if l1_4 == 0 then
                if 0 < l1_6 then
                    l1_7 = 90
                    l1_9 = (l1_4 + 1) * 95 + 14
                    plotLayerPositionX2 = (l1_4 + 1) * 95 + 55
                    l1_11 = 106
                    l1_13 = 100
                elseif l1_6 < 0 then
                    l1_7 = 70
                    l1_9 = l1_4 * 95 + 9
                    plotLayerPositionX2 = l1_4 * 95 + 50
                    l1_11 = 100
                    l1_13 = 0
                end
                l1_8 = 80
                l1_10 = l1_4 * 95 + 29
                plotLayerMovePositionX2 = l1_4 * 95 + 65
                l1_12 = 103
                l1_14 = 100
            elseif l1_4 == 1 then
                if 0 < l1_6 then
                    l1_7 = 100
                    l1_9 = (l1_4 + 1) * 95 + 9
                    plotLayerPositionX2 = (l1_4 + 1) * 95 + 50
                    l1_11 = 109
                    l1_13 = 100
                elseif l1_6 < 0 then
                    l1_7 = 80
                    l1_9 = (l1_4 - 1) * 95 + 29
                    plotLayerPositionX2 = (l1_4 - 1) * 95 + 65
                    l1_11 = 103
                    l1_13 = 100
                end
                l1_8 = 90
                l1_10 = l1_4 * 95 + 14
                plotLayerMovePositionX2 = l1_4 * 95 + 55
                l1_12 = 106
                l1_14 = 100
            elseif l1_4 == 2 then
                if 0 < l1_6 then
                    l1_9 = (l1_4 + 1) * 95 + 4
                    plotLayerPositionX2 = (l1_4 + 1) * 95 + 45
                elseif l1_6 < 0 then
                    l1_9 = (l1_4 - 1) * 95 + 14
                    plotLayerPositionX2 = (l1_4 - 1) * 95 + 55
                end
                l1_11 = 106
                l1_7 = 90
                l1_13 = 100
                l1_8 = 100
                l1_10 = l1_4 * 95 + 9
                plotLayerMovePositionX2 = l1_4 * 95 + 50
                l1_12 = 109
                l1_14 = 100
            elseif l1_4 == 3 then
                if 0 < l1_6 then
                    l1_7 = 80
                    l1_9 = (l1_4 + 1) * 95 - 8
                    plotLayerPositionX2 = (l1_4 + 1) * 95 + 29
                    l1_11 = 103
                    l1_13 = 100
                elseif l1_6 < 0 then
                    l1_7 = 100
                    l1_9 = (l1_4 - 1) * 95 + 9
                    plotLayerPositionX2 = (l1_4 - 1) * 95 + 50
                    l1_11 = 109
                    l1_13 = 100
                end
                l1_8 = 90
                l1_10 = l1_4 * 95 + 4
                plotLayerMovePositionX2 = l1_4 * 95 + 45
                l1_12 = 106
                l1_14 = 100
            elseif l1_4 == 4 then
                if 0 < l1_6 then
                    l1_7 = 70
                    l1_9 = l1_4 * 95
                    plotLayerPositionX2 = l1_4 * 95 + 33
                    l1_11 = 100
                    l1_13 = 0
                elseif l1_6 < 0 then
                    l1_7 = 90
                    l1_9 = (l1_4 - 1) * 95 + 4
                    plotLayerPositionX2 = (l1_4 - 1) * 95 + 45
                    l1_11 = 106
                    l1_13 = 100
                end
                l1_8 = 80
                l1_10 = l1_4 * 95 - 8
                plotLayerMovePositionX2 = l1_4 * 95 + 29
                l1_12 = 103
                l1_14 = 100
            end
            layerScale(layerName.plot + l1_20 * 3, l1_7, l1_7)
            layerScale(layerName.plot + l1_20 * 3 + 1, l1_7, l1_7)
            layerMoveScale(layerName.plot + l1_20 * 3, l1_8, l1_8, l1_5)
            layerMoveScale(layerName.plot + l1_20 * 3 + 1, l1_8, l1_8, l1_5)
            layerPosition(layerName.plot + l1_20 * 3, l1_9, 60)
            layerPosition(layerName.plot + l1_20 * 3 + 1, l1_9, l1_11)
            layerMovePosition(layerName.plot + l1_20 * 3, l1_10, 60, l1_5)
            layerMovePosition(layerName.plot + l1_20 * 3 + 1, l1_10, l1_12, l1_5)
            layerAlpha(layerName.plot + l1_20 * 3, l1_13)
            layerAlpha(layerName.plot + l1_20 * 3 + 1, l1_13)
            layerMoveAlpha(layerName.plot + l1_20 * 3, l1_14, l1_5)
            layerMoveAlpha(layerName.plot + l1_20 * 3 + 1, l1_14, l1_5)
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
    savedataTitle("フラグメントモード", "")
    wait(1)
    cInitGame()
    layerCopy(layerName.bg1, layerName.bg_1_a_0)
    layerCopy(layerName.bg1 + 1, layerName.sys_3_a)
    layerClip(layerName.bg1 + 1, 0, 0, 160, 37)
    layerPosition(layerName.bg1 + 1, 5, 5)
    layerCopy(layerName.bg1 + 2, layerName.sys_3_a)
    layerClip(layerName.bg1 + 2, 0, 40, 160, 120)
    layerPosition(layerName.bg1 + 2, 195, 56)
    layerCopy(layerName.bg1 + 3, layerName.sys_3_a)
    layerClip(layerName.bg1 + 3, 0, 120, 160, 191)
    layerPosition(layerName.bg1 + 3, 338, 191)
    l0_1(selectItemNo, selectItemNo)
    layerLoadAsync(0, layerName.card1, cGetFileName("card", "crd_1_a"))
    wait(1)
end
main = function()
    advPart(false)
    logEnable(false)
    systemConfig.unsetConfigButton()
    local l1_0 = comSectionStoryGetCount()
    if l1_0 == 0 then
        vms(6056, "NONVOICE", "【■おしらせ】あらすじを作成する物語がありません。_rストーリーモードをプレイしてください。")
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
    if gameSave.myCard[136].hold == 1 then
        if gameSave.myCard[145].hold == -1 then
            cInitGame()
            doScriptScene = "s3fc-10"
            run(cGetFileName("script", "snr_s3_10_fc"))
            quit()
        end
    end
    if gameSave.tutorial.firstFragment == 0 then
        if gameSave.tutorial.firstFragmentBegin == 0 then
            systemConfig.setConfigButton()
            run(cGetFileName("script", "snr_crd_0"))
            quit()
        else
            gameSave.storyRoute[1].sceneId = "s1s_20"
            gameSave.storyRoute[1].ayanoTime = 0
        end
    end
    if selectItemNo < 1 then
        selectItemNo = l1_0
    end
    if l1_0 < selectItemNo then
        selectItemNo = l1_0
    end
    l0_2()
    local l1_1 = false
    local l1_2 = 0
    local l1_3 = false
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
            l1_2 = 0
            l1_6 = false
            layerLoad(layerName.card1, "")
            wait(3)
        end
        local l1_10 = sceneId2aCard[gameSave.storyRoute[l1_4].sceneId]
        if not (gameSave.myCard[l1_10].hold == -1) then
            if l1_2 <= 3 then
                if 3 <= l1_2 then
                    layerLoadAsync(0, layerName.card1, cGetFileName("card", "crd_" .. l1_10 .. "_a"))
                    l1_3 = true
                end
                l1_2 = l1_2 + 1 > 4 and 4 or l1_2 + 1
            end
        end
        if l1_3 == true then
            if layerIsLoad(layerName.card1) == true then
                layerVisible(layerName.card1, true)
                layerAlpha(layerName.card1, 0)
                layerPosition(layerName.card1, 130, 110)
                layerMovePosition(layerName.card1, 130, 130, 10)
                layerMoveAlpha(layerName.card1, 100, 10)
                l1_3 = false
            end
        end
        if not (pressButton("CIRCLE") == true) then
            l1_7 = 0
        end
        if pressButton("CIRCLE") == true then
            if l1_6 == false then
                if l1_7 == 0 then
                    if not (string.sub(gameSave.storyRoute[l1_4].sceneId, -4) == "_sel") then
                        local l1_11 = sceneId2aCard[gameSave.storyRoute[l1_4].sceneId]
                        if gameSave.myCard[l1_11].hold == -1 then
                            if l0_0(l1_4) == false then
                                oCard.mesNotStoryLine()
                            else
                                keyPlaySE(seName.circle)
                                wait(10)
                                selectItemNo = l1_4
                                gameSave.fragmentDoSceneId = gameSave.storyRoute[l1_4].sceneId
                                gameSave.fragmentDoCardId = l1_11
                                fontClear()
                                run(cGetFileName("scriptc", "snr_crd_" .. l1_11))
                                quit()
                            end
                        else
                            local l1_12 = cGetFileName("sysgim", "sys_5_f")
                            keyPlaySE(seName.circle)
                            if comDlgYesNoSel(l1_12, 0, 50, 1) == true then
                                wait(10)
                                selectItemNo = l1_4
                                gameSave.fragmentDoSceneId = gameSave.storyRoute[l1_4].sceneId
                                gameSave.fragmentDoCardId = l1_11
                                fontClear()
                                run(cGetFileName("scriptc", "snr_crd_" .. l1_11))
                                quit()
                            else
                                l1_7 = 1
                                l1_8 = 1
                                l1_9 = 1
                            end
                        end
                    else
                        local l1_11 = sceneId2aCard[gameSave.storyRoute[l1_4].sceneId]
                        if gameSave.myCard[l1_11].hold == -1 then
                            keyPlaySE(seName.circle)
                            wait(10)
                            selectItemNo = l1_4
                            gameSave.fragmentDoSceneId = gameSave.storyRoute[l1_4].sceneId
                            gameSave.fragmentDoCardId = l1_11
                            fontClear()
                            run(cGetFileName("scriptc", "snr_crd_" .. l1_11))
                            quit()
                        else
                            local l1_12 = cGetFileName("sysgim", "sys_5_f")
                            keyPlaySE(seName.circle)
                            if comDlgYesNoSel(l1_12, 0, 0, 1) == true then
                                wait(10)
                                selectItemNo = l1_4
                                gameSave.fragmentDoSceneId = gameSave.storyRoute[l1_4].sceneId
                                gameSave.fragmentDoCardId = l1_11
                                fontClear()
                                run(cGetFileName("scriptc", "snr_crd_" .. l1_11))
                                quit()
                            else
                                l1_7 = 1
                                l1_8 = 1
                                l1_9 = 1
                            end
                        end
                    end
                end
            end
        end
        if not (pressButton("CROSS") == true) then
            l1_8 = 0
        end
        if pressButton("CROSS") == true then
            if l1_8 == 0 then
                systemConfig.unsetConfigButton()
                keyPlaySE(seName.cross)
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
                run(cGetFileName("script", "snr_story_main"))
                quit()
            end
        end
        wait(2)
    end
    wait(1)
    layerCopy(199, layerName.effectBlack)
    fontClear()
    switchScreen(0, "", 30)
    cInitGame()
    run(cGetFileName("script", "snr_mainmenu"))
    quit()
end

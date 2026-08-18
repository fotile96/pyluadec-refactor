local u0, u1, u2, u3, u4, u5, u6
return function()
advPart(false)
logEnable(false)
systemConfig.unsetConfigButton()
cInitGame()
u0()
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
                    if u1.option < l1_0 then
                        l1_0 = u1.prologue
                    else
                        l1_0 = l1_0 - 1 < u1.prologue and u1.prologue or l1_0 - 1
                    end
                    if l1_0 == u1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 - 1 < u1.prologue and u1.prologue or l1_0 - 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("DOWN") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    if u1.option < l1_0 then
                        l1_0 = u1.library
                    else
                        l1_0 = l1_0 + 1 > u1.option and u1.option or l1_0 + 1
                    end
                    if l1_0 == u1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 + 1 > u1.option and u1.option or l1_0 + 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("RIGHT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = u1.load
                    l1_2 = true
                end
            end
            if pressButton("LEFT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = u1.prologue
                    l1_2 = true
                end
            end
            if pressButton("CIRCLE") == true then
                if l1_2 == false then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if l1_0 == u1.prologue then
                        cInitGame()
                        switchScreen(0, "", 60)
                        doScriptScene = "sof_10"
                        run(cGetFileName("script", "snr_s0_10_f"))
                        quit()
                    elseif l1_0 == u1.library then
                        l1_3 = true
                        if not (systemSave.novelFlag == true) then
                            l1_0 = u1.scene
                        else
                            l1_0 = u1.novel
                        end
                        for l1_7 = 1, #u2.layerKey0, 1 do
                            if l1_7 < u1.novel then
                                if not (l1_7 == u1.library) then
                                    layerMoveAlpha(u2.layerNumber.menu + l1_7, 50, 30)
                                end
                            elseif l1_7 == u1.novel and not (systemSave.novelFlag == true) or l1_7 == u1.music and not (systemSave.musicFlag == true) then
                                layerVisible(u2.layerNumber.menu + l1_7, false)
                            else
                                layerAlpha(u2.layerNumber.menu + l1_7, 0)
                                layerVisible(u2.layerNumber.menu + l1_7, true)
                                layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                            end
                        end
                        wait(30)
                    elseif l1_0 == u1.option then
                        systemOption.Option()
                    elseif l1_0 == u1.load then
                        u3()
                    end
                    u4(u2.layerNumber.menu + l1_1, u2.layerKey0[l1_1])
                    u5(u2.layerNumber.menu + l1_0, u2.layerKey0[l1_0])
                end
            end
        else
            if pressButton("UP") == true then
                if l1_2 == false then
                    keyPlaySE(seName.arrowKey)
                    l1_1 = l1_0
                    l1_0 = l1_0 - 1 < u1.novel and u1.novel or l1_0 - 1
                    if l1_0 == u1.novel then
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
                    l1_0 = l1_0 + 1 > u1.music and u1.music or l1_0 + 1
                    if l1_0 == u1.music then
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
                    if l1_0 == u1.novel then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_novel"))
                        quit()
                    elseif l1_0 == u1.scene then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_memory"))
                        quit()
                    elseif l1_0 == u1.cg then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_graphic"))
                        quit()
                    elseif l1_0 == u1.music then
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
                    l1_0 = u1.library
                    for l1_7 = 1, u1.music, 1 do
                        if l1_7 < u1.novel then
                            layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                        else
                            layerMoveAlpha(u2.layerNumber.menu + l1_7, 0, 30)
                        end
                    end
                    wait(30)
                    for l1_7 = u1.novel, u1.music, 1 do
                        layerVisible(u2.layerNumber.menu + l1_7, false)
                    end
                    u4(u2.layerNumber.menu + l1_1, u2.layerKey0[l1_1])
                    u5(u2.layerNumber.menu + l1_0, u2.layerKey0[l1_0])
                end
            end
        end
        if l1_2 == true then
            u4(u2.layerNumber.menu + l1_1, u2.layerKey0[l1_1])
            u5(u2.layerNumber.menu + l1_0, u2.layerKey0[l1_0])
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
                    if u1.option < l1_0 then
                        l1_0 = u1.story
                    else
                        l1_0 = l1_0 - 1 < u1.story and u1.story or l1_0 - 1
                    end
                    if l1_0 == u1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 - 1 < u1.story and u1.story or l1_0 - 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("DOWN") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    if u1.option < l1_0 then
                        l1_0 = u1.library
                    else
                        l1_0 = l1_0 + 1 > u1.option and u1.option or l1_0 + 1
                    end
                    if l1_0 == u1.library then
                        if not (systemSave.libFlag == true) then
                            l1_0 = l1_0 + 1 > u1.option and u1.option or l1_0 + 1
                        end
                    end
                    l1_2 = true
                end
            end
            if pressButton("RIGHT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = u1.load
                    l1_2 = true
                end
            end
            if pressButton("LEFT") == true then
                if l1_2 == false then
                    l1_1 = l1_0
                    l1_0 = u1.save
                    l1_2 = true
                end
            end
            if pressButton("CIRCLE") == true then
                if l1_2 == false then
                    keyPlaySE(seName.circle)
                    wait(10)
                    if l1_0 == u1.story then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_story_main"))
                        quit()
                    elseif l1_0 == u1.library then
                        l1_3 = true
                        if not (systemSave.novelFlag == true) then
                            l1_0 = u1.scene
                        else
                            l1_0 = u1.novel
                        end
                        for l1_7 = 1, #u2.layerKey1, 1 do
                            if l1_7 < u1.novel then
                                if not (l1_7 == u1.library) then
                                    layerMoveAlpha(u2.layerNumber.menu + l1_7, 50, 30)
                                end
                            elseif l1_7 == u1.novel and not (systemSave.novelFlag == true) or l1_7 == u1.music and not (systemSave.musicFlag == true) then
                                layerVisible(u2.layerNumber.menu + l1_7, false)
                            else
                                layerAlpha(u2.layerNumber.menu + l1_7, 0)
                                layerVisible(u2.layerNumber.menu + l1_7, true)
                                layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                            end
                        end
                        wait(30)
                        u4(u2.layerNumber.menu + l1_1, u2.layerKey1[l1_1])
                        u5(u2.layerNumber.menu + l1_0, u2.layerKey1[l1_0])
                    elseif l1_0 == u1.option then
                        systemOption.Option()
                    elseif l1_0 == u1.save then
                        u6()
                    elseif l1_0 == u1.load then
                        u3()
                    end
                end
            end
        else
            if pressButton("UP") == true then
                if l1_2 == false then
                    keyPlaySE(seName.arrowKey)
                    l1_1 = l1_0
                    l1_0 = l1_0 - 1 < u1.novel and u1.novel or l1_0 - 1
                    if l1_0 == u1.novel then
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
                    l1_0 = l1_0 + 1 > u1.music and u1.music or l1_0 + 1
                    if l1_0 == u1.music then
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
                    if l1_0 == u1.novel then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_novel"))
                        quit()
                    elseif l1_0 == u1.scene then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_memory"))
                        quit()
                    elseif l1_0 == u1.cg then
                        cInitGame()
                        switchScreen(0, "", 60)
                        run(cGetFileName("script", "snr_graphic"))
                        quit()
                    elseif l1_0 == u1.music then
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
                    l1_0 = u1.library
                    for l1_7 = 1, u1.music, 1 do
                        if l1_7 < u1.novel then
                            layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                        else
                            layerMoveAlpha(u2.layerNumber.menu + l1_7, 0, 30)
                        end
                    end
                    wait(30)
                    for l1_7 = u1.novel, u1.music, 1 do
                        layerVisible(u2.layerNumber.menu + l1_7, false)
                    end
                    u4(u2.layerNumber.menu + l1_1, u2.layerKey1[l1_1])
                    u5(u2.layerNumber.menu + l1_0, u2.layerKey1[l1_0])
                end
            end
        end
        if l1_2 == true then
            u4(u2.layerNumber.menu + l1_1, u2.layerKey1[l1_1])
            u5(u2.layerNumber.menu + l1_0, u2.layerKey1[l1_0])
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
                        if u1.option < l1_0 then
                            l1_0 = u1.story
                        else
                            l1_0 = l1_0 - 1 < u1.story and u1.story or l1_0 - 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("DOWN") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        if u1.option < l1_0 then
                            l1_0 = u1.fragment
                        else
                            l1_0 = l1_0 + 1 > u1.option and u1.option or l1_0 + 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("RIGHT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = u1.load
                        l1_2 = true
                    end
                end
                if pressButton("LEFT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = u1.save
                        l1_2 = true
                    end
                end
                if pressButton("CIRCLE") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if l1_0 == u1.story then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_story_main"))
                            quit()
                        elseif l1_0 == u1.fragment then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_fragment_main"))
                            quit()
                        elseif l1_0 == u1.library then
                            l1_3 = true
                            if not (systemSave.novelFlag == true) then
                                l1_0 = u1.scene
                            else
                                l1_0 = u1.novel
                            end
                            for l1_7 = 1, #u2.layerKey2, 1 do
                                if l1_7 < u1.novel then
                                    if not (l1_7 == u1.library) then
                                        layerMoveAlpha(u2.layerNumber.menu + l1_7, 50, 30)
                                    end
                                elseif l1_7 == u1.novel and not (systemSave.novelFlag == true) or l1_7 == u1.music and not (systemSave.musicFlag == true) then
                                    layerVisible(u2.layerNumber.menu + l1_7, false)
                                else
                                    layerAlpha(u2.layerNumber.menu + l1_7, 0)
                                    layerVisible(u2.layerNumber.menu + l1_7, true)
                                    layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                                end
                            end
                            wait(30)
                            u4(u2.layerNumber.menu + l1_1, u2.layerKey2[l1_1])
                            u5(u2.layerNumber.menu + l1_0, u2.layerKey2[l1_0])
                        elseif l1_0 == u1.option then
                            systemOption.Option()
                        elseif l1_0 == u1.save then
                            u6()
                        elseif l1_0 == u1.load then
                            u3()
                        end
                    end
                end
            else
                if pressButton("UP") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.arrowKey)
                        l1_1 = l1_0
                        l1_0 = l1_0 - 1 < u1.novel and u1.novel or l1_0 - 1
                        if l1_0 == u1.novel then
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
                        l1_0 = l1_0 + 1 > u1.music and u1.music or l1_0 + 1
                        if l1_0 == u1.music then
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
                        if l1_0 == u1.novel then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_novel"))
                            quit()
                        elseif l1_0 == u1.scene then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_memory"))
                            quit()
                        elseif l1_0 == u1.cg then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_graphic"))
                            quit()
                        elseif l1_0 == u1.music then
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
                        l1_0 = u1.library
                        for l1_7 = 1, u1.music, 1 do
                            if l1_7 < u1.novel then
                                layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                            else
                                layerMoveAlpha(u2.layerNumber.menu + l1_7, 0, 30)
                            end
                        end
                        wait(30)
                        for l1_7 = u1.novel, u1.music, 1 do
                            layerVisible(u2.layerNumber.menu + l1_7, false)
                        end
                        u4(u2.layerNumber.menu + l1_1, u2.layerKey2[l1_1])
                        u5(u2.layerNumber.menu + l1_0, u2.layerKey2[l1_0])
                    end
                end
            end
            if l1_2 == true then
                u4(u2.layerNumber.menu + l1_1, u2.layerKey2[l1_1])
                u5(u2.layerNumber.menu + l1_0, u2.layerKey2[l1_0])
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
                        if u1.option < l1_0 then
                            l1_0 = u1.story
                        else
                            l1_0 = l1_0 - 1 < u1.story and u1.story or l1_0 - 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("DOWN") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        if u1.option < l1_0 then
                            l1_0 = u1.fragment
                        else
                            l1_0 = l1_0 + 1 > u1.option and u1.option or l1_0 + 1
                        end
                        l1_2 = true
                    end
                end
                if pressButton("RIGHT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = u1.load
                        l1_2 = true
                    end
                end
                if pressButton("LEFT") == true then
                    if l1_2 == false then
                        l1_1 = l1_0
                        l1_0 = u1.save
                        l1_2 = true
                    end
                end
                if pressButton("CIRCLE") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.circle)
                        wait(10)
                        if l1_0 == u1.story then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_story_main"))
                            quit()
                        elseif l1_0 == u1.fragment then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_fragment_main"))
                            quit()
                        elseif l1_0 == u1.section7 then
                            cInitGame()
                            switchScreen(0, "", 60)
                            doScriptScene = "s7f-10"
                            run(cGetFileName("script", "snr_s7_10_f"))
                            quit()
                        elseif l1_0 == u1.library then
                            l1_3 = true
                            if not (systemSave.novelFlag == true) then
                                l1_0 = u1.scene
                            else
                                l1_0 = u1.novel
                            end
                            for l1_7 = 1, 11, 1 do
                                if l1_7 < u1.novel then
                                    if not (l1_7 == u1.library) then
                                        layerMoveAlpha(u2.layerNumber.menu + l1_7, 50, 30)
                                    end
                                elseif l1_7 == u1.novel and not (systemSave.novelFlag == true) or l1_7 == u1.music and not (systemSave.musicFlag == true) then
                                    layerVisible(u2.layerNumber.menu + l1_7, false)
                                else
                                    layerAlpha(u2.layerNumber.menu + l1_7, 0)
                                    layerVisible(u2.layerNumber.menu + l1_7, true)
                                    layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                                end
                            end
                            wait(30)
                        elseif l1_0 == u1.option then
                            systemOption.Option()
                        elseif l1_0 == u1.save then
                            u6()
                        elseif l1_0 == u1.load then
                            u3()
                        end
                        u4(u2.layerNumber.menu + l1_1, u2.layerKey3[l1_1])
                        u5(u2.layerNumber.menu + l1_0, u2.layerKey3[l1_0])
                    end
                end
            else
                if pressButton("UP") == true then
                    if l1_2 == false then
                        keyPlaySE(seName.arrowKey)
                        l1_1 = l1_0
                        l1_0 = l1_0 - 1 < u1.novel and u1.novel or l1_0 - 1
                        if l1_0 == u1.novel then
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
                        l1_0 = l1_0 + 1 > u1.music and u1.music or l1_0 + 1
                        if l1_0 == u1.music then
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
                        if l1_0 == u1.novel then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_novel"))
                            quit()
                        elseif l1_0 == u1.scene then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_memory"))
                            quit()
                        elseif l1_0 == u1.cg then
                            cInitGame()
                            switchScreen(0, "", 60)
                            run(cGetFileName("script", "snr_graphic"))
                            quit()
                        elseif l1_0 == u1.music then
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
                        l1_0 = u1.library
                        for l1_7 = 1, u1.music, 1 do
                            if l1_7 < u1.novel then
                                layerMoveAlpha(u2.layerNumber.menu + l1_7, 100, 30)
                            else
                                layerMoveAlpha(u2.layerNumber.menu + l1_7, 0, 30)
                            end
                        end
                        wait(30)
                        for l1_7 = u1.novel, u1.music, 1 do
                            layerVisible(u2.layerNumber.menu + l1_7, false)
                        end
                        u4(u2.layerNumber.menu + l1_1, u2.layerKey3[l1_1])
                        u5(u2.layerNumber.menu + l1_0, u2.layerKey3[l1_0])
                    end
                end
            end
            if l1_2 == true then
                u4(u2.layerNumber.menu + l1_1, u2.layerKey3[l1_1])
                u5(u2.layerNumber.menu + l1_0, u2.layerKey3[l1_0])
                keyPlaySE(seName.arrowKey)
                wait(3)
                l1_2 = false
            end
            wait(2)
        end
    end
end
end

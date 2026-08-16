libGomRin = function()
end
main = function()
    cInitGame()
    local l1_0 = 1
    local l1_1 = false
    cfontPrint(0, 200, 100, 16777215, 255, "SEC7F")
    cfontPrint(0, 200, 150, 16777215, 16711680, "PROLOGUE")
    cfontPrint(0, 200, 200, 16777215, 16711680, "STORY")
    cfontPrint(0, 200, 250, 16777215, 16711680, "DEBUG")
    local l1_2 = 1
    while true do
        if pressButton("UP") == true then
            if l1_1 == false then
                l1_0 = l1_0 - 1 < 1 and 1 or l1_0 - 1
                l1_1 = true
            end
        end
        if pressButton("DOWN") == true then
            if l1_1 == false then
                l1_0 = l1_0 + 1 > 4 and 4 or l1_0 + 1
                l1_1 = true
            end
        end
        if pressButton("CIRCLE") == true then
            if l1_2 == 0 then
                break
            end
        else
            l1_2 = 0
        end
        if l1_1 == true then
            fontClear()
            if l1_0 == 1 then
                cfontPrint(0, 200, 100, 16777215, 255, "SEC7F")
            else
                cfontPrint(0, 200, 100, 16777215, 16711680, "SEC7F")
            end
            if l1_0 == 2 then
                cfontPrint(0, 200, 150, 16777215, 255, "PROLOGUE")
            else
                cfontPrint(0, 200, 150, 16777215, 16711680, "PROLOGUE")
            end
            if l1_0 == 3 then
                cfontPrint(0, 200, 200, 16777215, 255, "STORY")
            else
                cfontPrint(0, 200, 200, 16777215, 16711680, "STORY")
            end
            if l1_0 == 4 then
                cfontPrint(0, 200, 250, 16777215, 255, "DEBUG")
            else
                cfontPrint(0, 200, 250, 16777215, 16711680, "DEBUG")
            end
            l1_1 = false
            wait(5)
        end
        wait(1)
    end
    fontClear()
    if l1_0 == 1 then
        cardIDFlag = true
        for l1_6 = 1, 195, 1 do
            local l1_7 = gameSave.myCard[l1_6]
            l1_7.hold = 1
        end
        gameSave.startMenuState = 2
        gameSave.myCard[1].hold = 1
        gameSave.myCard[2].hold = 1
        gameSave.tutorial.firstStory = 1
        gameSave.tutorial.firstFragmentBegin = 1
        gameSave.tutorial.firstFragment = 1
        gameSave.ayanoTime = 0
        gameSave.storyRoute[1].sceneId = "e1s_10"
        gameSave.storyRoute[1].ayanoTime = 0
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    run(cGetFileName("script", "snr_mainmenu"))
    quit()
end

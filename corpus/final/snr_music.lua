local l0_0 = {layerName = {bg = 0, music_select = 50, music_off = 51, music_on = 52}, musicTitle = {"music_01_a", "music_02_a", "music_03_a", "music_04_a", "music_05_a", "music_06_a", "music_07_a", "music_08_a", "music_09_a", "music_10_a", "music_11_a", "music_12_a", "music_13_a", "music_14_a", "music_15_a", "music_16_a", "music_17_a", "music_18_a", "music_19_a", "music_20_a", "music_21_a", "music_22_a"}, selectFlag = {music_01_a = 1, music_02_a = 0, music_03_a = 0, music_04_a = 0, music_05_a = 0, music_06_a = 0, music_07_a = 0, music_08_a = 0, music_09_a = 0, music_10_a = 0, music_11_a = 0, music_12_a = 0, music_13_a = 0, music_14_a = 0, music_15_a = 0, music_16_a = 0, music_17_a = 0, music_18_a = 0, music_19_a = 0, music_20_a = 0, music_21_a = 0, music_22_a = 0}, musicName = {music_01_a = "bgm_1_x", music_02_a = "bgm_2_x", music_03_a = "bgm_3_x", music_04_a = "bgm_4_x", music_05_a = "bgm_5_x", music_06_a = "bgm_6_x", music_07_a = "bgm_7_x", music_08_a = "bgm_8_x", music_09_a = "bgm_9_x", music_10_a = "bgm_10_x", music_11_a = "bgm_11_x", music_12_a = "bgm_12_x", music_13_a = "bgm_13_x", music_14_a = "bgm_14_x", music_15_a = "bgm_15_x", music_16_a = "bgm_16_x", music_17_a = "bgm_17_x", music_18_a = "bgm_18_x", music_19_a = "bgm_19_x", music_20_a = "bgm_20_a", music_21_a = "op_zansho_short", music_22_a = "ed_bl_short"}}
local l0_1 = false
local l0_2 = 1
local l0_3 = ""
local l0_4 = function()
    local l1_0 = 0
    local l1_1 = 1
    for l1_5 = 1, #l0_0.musicTitle, 1 do
        if l0_0.selectFlag[l0_0.musicTitle[l1_5]] == 0 then
            layerCopy(l0_0.layerName.bg + 1 + l1_5, l0_0.layerName.music_off)
        elseif l0_0.selectFlag[l0_0.musicTitle[l1_5]] == 1 then
            layerCopy(l0_0.layerName.bg + 1 + l1_5, l0_0.layerName.music_select)
        elseif l0_0.selectFlag[l0_0.musicTitle[l1_5]] == 2 then
            layerCopy(l0_0.layerName.bg + 1 + l1_5, l0_0.layerName.music_on)
        end
        if l1_5 <= 10 then
            layerClip(l0_0.layerName.bg + 1 + l1_5, 0, (l1_5 - 1) * 20, 120, l1_5 * 20)
            layerPosition(l0_0.layerName.bg + 1 + l1_5, 5, l1_1 * 20 + 25)
        elseif l1_5 <= 20 then
            layerClip(l0_0.layerName.bg + 1 + l1_5, 128, (l1_5 - 11) * 20, 350, (l1_5 - 10) * 20)
            layerPosition(l0_0.layerName.bg + 1 + l1_5, 128, l1_1 * 20 + 25)
        else
            layerClip(l0_0.layerName.bg + 1 + l1_5, 350, (l1_5 - 21) * 20, 480, (l1_5 - 20) * 20)
            layerPosition(l0_0.layerName.bg + 1 + l1_5, 350, l1_1 * 20 + 25)
        end
        l1_1 = l1_1 + 1
        if 10 < l1_1 then
            l1_1 = 1
            l1_0 = l1_0 + 1
        end
    end
end
local l0_5 = function()
    startLoading()
    comLayerLoadFalse(l0_0.layerName.music_select, "music/music_02_a.gim")
    comLayerLoadFalse(l0_0.layerName.music_off, "music/music_03_a.gim")
    comLayerLoadFalse(l0_0.layerName.music_on, "music/music_04_a.gim")
    waitLoading()
    wait(30)
    local l1_0 = math.random(1, 3)
    if l1_0 == 1 then
        layerLoad(l0_0.layerName.bg, cGetFileName("bg", "bg_3_b_0"))
    elseif l1_0 == 2 then
        layerLoad(l0_0.layerName.bg, cGetFileName("bg", "bg_7_b_0"))
    elseif l1_0 == 3 then
        layerLoad(l0_0.layerName.bg, cGetFileName("bg", "bg_8_a_0"))
    end
    layerLoad(l0_0.layerName.bg + 1, "music/music_01_a.gim")
    endLoading()
    l0_4()
    switchScreen(0, "", 60)
end
local l0_6 = function()
    cInitGame()
    switchScreen(0, "", 60)
end
main = function()
    systemConfig.unsetConfigButton()
    logEnable(false)
    advPart(false)
    l0_5()
    while true do
        if pressButton("UP") == true then
            if l0_1 == false then
                if not (l0_0.selectFlag[l0_0.musicTitle[l0_2]] == 2) then
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 0
                end
                local l1_0 = l0_2 - 1 < 1 and 22 or l0_2 - 1
                l0_2 = l1_0
                l1_0 = l0_0
                l1_0 = l1_0.selectFlag
                l1_0 = l1_0[l0_0.musicTitle[l0_2]]
                if not (l1_0 == 2) then
                    l1_0 = l0_0
                    l1_0 = l1_0.selectFlag
                    l1_0[l0_0.musicTitle[l0_2]] = 1
                end
                l1_0 = true
                l0_1 = l1_0
            end
        end
        if pressButton("DOWN") == true then
            if l0_1 == false then
                if not (l0_0.selectFlag[l0_0.musicTitle[l0_2]] == 2) then
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 0
                end
                local l1_0 = 22 < l0_2 + 1 and 1 or l0_2 + 1
                l0_2 = l1_0
                l1_0 = l0_0
                l1_0 = l1_0.selectFlag
                l1_0 = l1_0[l0_0.musicTitle[l0_2]]
                if not (l1_0 == 2) then
                    l1_0 = l0_0
                    l1_0 = l1_0.selectFlag
                    l1_0[l0_0.musicTitle[l0_2]] = 1
                end
                l1_0 = true
                l0_1 = l1_0
            end
        end
        if pressButton("RIGHT") == true then
            if l0_1 == false then
                if not (l0_0.selectFlag[l0_0.musicTitle[l0_2]] == 2) then
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 0
                end
                if l0_2 == 21 or l0_2 == 22 then
                    l0_2 = l0_2 - 20
                else
                    local l1_0 = 22 < l0_2 + 10 and l0_2 - 10 or l0_2 + 10
                    l0_2 = l1_0
                end
                if not (l0_0.selectFlag[l0_0.musicTitle[l0_2]] == 2) then
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 1
                end
                l0_1 = true
            end
        end
        if pressButton("LEFT") == true then
            if l0_1 == false then
                if not (l0_0.selectFlag[l0_0.musicTitle[l0_2]] == 2) then
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 0
                end
                if l0_2 == 1 or l0_2 == 2 then
                    l0_2 = l0_2 + 20
                else
                    local l1_0 = l0_2 - 10 < 1 and l0_2 + 10 or l0_2 - 10
                    l0_2 = l1_0
                end
                if not (l0_0.selectFlag[l0_0.musicTitle[l0_2]] == 2) then
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 1
                end
                l0_1 = true
            end
        end
        if pressButton("CIRCLE") == true then
            if l0_1 == false then
                if not (l0_2 == l0_3) then
                    stopBGM(0, 0)
                    if not (l0_3 == "") then
                        l0_0.selectFlag[l0_0.musicTitle[l0_3]] = 0
                    end
                    playBGM(0, cGetFileName("bgm", l0_0.musicName[l0_0.musicTitle[l0_2]]), true)
                    l0_3 = l0_2
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 2
                else
                    stopBGM(0, 30)
                    l0_0.selectFlag[l0_0.musicTitle[l0_2]] = 1
                    l0_3 = ""
                end
                l0_1 = true
                wait(3)
            end
        end
        if pressButton("CROSS") == true then
            if l0_1 == false then
                local l1_0 = ""
                for l1_4, l1_5 in pairs(l0_0.selectFlag) do
                    if l1_5 == 2 then
                        l1_0 = l1_4
                        break
                    end
                end
                if not (l1_0 == "") then
                    stopBGM(0, 30)
                    if l0_0.musicTitle[l0_2] == l1_0 then
                        l0_0.selectFlag[l1_0] = 1
                    else
                        l0_0.selectFlag[l1_0] = 0
                    end
                    l0_3 = ""
                    l0_1 = true
                else
                    break
                end
            end
        end
        if l0_1 == true then
            l0_4()
            l0_1 = false
            wait(3)
        end
        wait(2)
    end
    l0_6()
    run(cGetFileName("script", "snr_mainmenu"))
end

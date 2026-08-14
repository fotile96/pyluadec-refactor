local v0 = {}
local v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21, v22, v23
v0.layerName = {}
v0.layerName.bg = 0
v0.layerName.music_select = 50
v0.layerName.music_off = 51
v0.layerName.music_on = 52
v0.musicTitle = {}
v2 = "music_01_a"
v3 = "music_02_a"
v4 = "music_03_a"
v5 = "music_04_a"
v6 = "music_05_a"
v7 = "music_06_a"
v8 = "music_07_a"
v9 = "music_08_a"
v10 = "music_09_a"
v11 = "music_10_a"
v12 = "music_11_a"
v13 = "music_12_a"
v14 = "music_13_a"
v15 = "music_14_a"
v16 = "music_15_a"
v17 = "music_16_a"
v18 = "music_17_a"
v19 = "music_18_a"
v20 = "music_19_a"
v21 = "music_20_a"
v22 = "music_21_a"
v23 = "music_22_a"
v0.musicTitle[1] = v2
v0.musicTitle[2] = v3
v0.musicTitle[3] = v4
v0.musicTitle[4] = v5
v0.musicTitle[5] = v6
v0.musicTitle[6] = v7
v0.musicTitle[7] = v8
v0.musicTitle[8] = v9
v0.musicTitle[9] = v10
v0.musicTitle[10] = v11
v0.musicTitle[11] = v12
v0.musicTitle[12] = v13
v0.musicTitle[13] = v14
v0.musicTitle[14] = v15
v0.musicTitle[15] = v16
v0.musicTitle[16] = v17
v0.musicTitle[17] = v18
v0.musicTitle[18] = v19
v0.musicTitle[19] = v20
v0.musicTitle[20] = v21
v0.musicTitle[21] = v22
v0.musicTitle[22] = v23
v0.selectFlag = {}
v0.selectFlag.music_01_a = 1
v0.selectFlag.music_02_a = 0
v0.selectFlag.music_03_a = 0
v0.selectFlag.music_04_a = 0
v0.selectFlag.music_05_a = 0
v0.selectFlag.music_06_a = 0
v0.selectFlag.music_07_a = 0
v0.selectFlag.music_08_a = 0
v0.selectFlag.music_09_a = 0
v0.selectFlag.music_10_a = 0
v0.selectFlag.music_11_a = 0
v0.selectFlag.music_12_a = 0
v0.selectFlag.music_13_a = 0
v0.selectFlag.music_14_a = 0
v0.selectFlag.music_15_a = 0
v0.selectFlag.music_16_a = 0
v0.selectFlag.music_17_a = 0
v0.selectFlag.music_18_a = 0
v0.selectFlag.music_19_a = 0
v0.selectFlag.music_20_a = 0
v0.selectFlag.music_21_a = 0
v0.selectFlag.music_22_a = 0
v0.musicName = {}
v0.musicName.music_01_a = "bgm_1_x"
v0.musicName.music_02_a = "bgm_2_x"
v0.musicName.music_03_a = "bgm_3_x"
v0.musicName.music_04_a = "bgm_4_x"
v0.musicName.music_05_a = "bgm_5_x"
v0.musicName.music_06_a = "bgm_6_x"
v0.musicName.music_07_a = "bgm_7_x"
v0.musicName.music_08_a = "bgm_8_x"
v0.musicName.music_09_a = "bgm_9_x"
v0.musicName.music_10_a = "bgm_10_x"
v0.musicName.music_11_a = "bgm_11_x"
v0.musicName.music_12_a = "bgm_12_x"
v0.musicName.music_13_a = "bgm_13_x"
v0.musicName.music_14_a = "bgm_14_x"
v0.musicName.music_15_a = "bgm_15_x"
v0.musicName.music_16_a = "bgm_16_x"
v0.musicName.music_17_a = "bgm_17_x"
v0.musicName.music_18_a = "bgm_18_x"
v0.musicName.music_19_a = "bgm_19_x"
v0.musicName.music_20_a = "bgm_20_a"
v0.musicName.music_21_a = "op_zansho_short"
v0.musicName.music_22_a = "ed_bl_short"
v1 = false
v2 = 1
v3 = ""
v4 = function()
    local v1 = 0
    local v2 = 1
    local v3 = 1
    local v4, v5, i2, v6, v7, v8
    v4 = #v0.musicTitle
    v5 = 1
    for i2 = v3, v4, v5 do
        if v0.selectFlag[v0.musicTitle[i2]] == 0 then
            v6 = (v0.layerName.bg + 1) + i2
            layerCopy(v6, v0.layerName.music_off)
        elseif v0.selectFlag[v0.musicTitle[i2]] == 1 then
            v6 = (v0.layerName.bg + 1) + i2
            layerCopy(v6, v0.layerName.music_select)
        elseif v0.selectFlag[v0.musicTitle[i2]] == 2 then
            v6 = (v0.layerName.bg + 1) + i2
            layerCopy(v6, v0.layerName.music_on)
        end
        if i2 <= 10 then
            v6 = (v0.layerName.bg + 1) + i2
            v7 = (i2 - 1) * 20
            layerClip(v6, 0, v7, 120, (i2 * 20))
            v6 = (v0.layerName.bg + 1) + i2
            v7 = (v2 * 20) + 25
            layerPosition(v6, 5, v7)
        elseif i2 <= 20 then
            v6 = (v0.layerName.bg + 1) + i2
            v7 = (i2 - 11) * 20
            v8 = (i2 - 10) * 20
            layerClip(v6, 128, v7, 350, v8)
            v6 = (v0.layerName.bg + 1) + i2
            v7 = (v2 * 20) + 25
            layerPosition(v6, 128, v7)
        else
            v6 = (v0.layerName.bg + 1) + i2
            v7 = (i2 - 21) * 20
            v8 = (i2 - 20) * 20
            layerClip(v6, 350, v7, 480, v8)
            v6 = (v0.layerName.bg + 1) + i2
            v7 = (v2 * 20) + 25
            layerPosition(v6, 350, v7)
        end
        v2 = v2 + 1
        if 10 < v2 then
            v2 = 1
            v1 = v1 + 1
        end
    end
end
v5 = function()
    local v1, v2, v3
    startLoading()
    comLayerLoadFalse(v0.layerName.music_select, "music/music_02_a.gim")
    comLayerLoadFalse(v0.layerName.music_off, "music/music_03_a.gim")
    comLayerLoadFalse(v0.layerName.music_on, "music/music_04_a.gim")
    waitLoading()
    wait(30)
    v1 = math.random(1, 3)
    if v1 == 1 then
        layerLoad(v0.layerName.bg, cGetFileName("bg", "bg_3_b_0"))
    elseif v1 == 2 then
        layerLoad(v0.layerName.bg, cGetFileName("bg", "bg_7_b_0"))
    elseif v1 == 3 then
        layerLoad(v0.layerName.bg, cGetFileName("bg", "bg_8_a_0"))
    end
    layerLoad((v0.layerName.bg + 1), "music/music_01_a.gim")
    endLoading()
    v4()
    switchScreen(0, "", 60)
end
v6 = function()
    cInitGame()
    switchScreen(0, "", 60)
end
main = function()
    local v7, v8, v9, v10, v11, v12
    systemConfig.unsetConfigButton()
    logEnable(false)
    advPart(false)
    v5()
    while true do
    v7 = pressButton("UP")
    if v7 == true then
        if v1 == false then
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 0
            end
            v7 = v2 - 1
            if v7 < 1 then
                v7 = 22
            else
                v7 = v2 - 1
            end
            v2 = v7
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 1
            end
            v1 = true
        end
    end
    v7 = pressButton("DOWN")
    if v7 == true then
        if v1 == false then
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 0
            end
            v7 = v2 + 1
            if 22 < v7 then
                v7 = 1
            else
                v7 = v2 + 1
            end
            v2 = v7
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 1
            end
            v1 = true
        end
    end
    v7 = pressButton("RIGHT")
    if v7 == true then
        if v1 == false then
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 0
            end
            if not (v2 == 21) then
                if v2 == 22 then
                    v7 = v2 - 20
                    v2 = v7
                else
                    v7 = v2 + 10
                    if 22 < v7 then
                        v7 = v2 - 10
                    else
                        v7 = v2 + 10
                    end
                    v2 = v7
                end
            else
                v7 = v2 - 20
                v2 = v7
            end
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 1
            end
            v1 = true
        end
    end
    v7 = pressButton("LEFT")
    if v7 == true then
        if v1 == false then
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 0
            end
            if not (v2 == 1) then
                if v2 == 2 then
                    v7 = v2 + 20
                    v2 = v7
                else
                    v7 = v2 - 10
                    if v7 < 1 then
                        v7 = v2 + 10
                    else
                        v7 = v2 - 10
                    end
                    v2 = v7
                end
            else
                v7 = v2 + 20
                v2 = v7
            end
            if not (v0.selectFlag[v0.musicTitle[v2]] == 2) then
                v0.selectFlag[v0.musicTitle[v2]] = 1
            end
            v1 = true
        end
    end
    v7 = pressButton("CIRCLE")
    if v7 == true then
        if v1 == false then
            v7 = v2
            if not (v7 == v3) then
                stopBGM(0, 0)
                if not (v3 == "") then
                    v0.selectFlag[v0.musicTitle[v3]] = 0
                end
                v8 = v0.musicTitle[v2]
                v9 = v0.musicName[v8]
                playBGM(0, cGetFileName("bgm", v9), true)
                v3 = v2
                v0.selectFlag[v0.musicTitle[v2]] = 2
            else
                stopBGM(0, 30)
                v0.selectFlag[v0.musicTitle[v2]] = 1
                v3 = ""
            end
            v1 = true
            wait(3)
        end
    end
    v7 = pressButton("CROSS")
    if v7 == true then
        if v1 == false then
            v7 = ""
            v10 = v0.selectFlag
            v11, v10, v12 = pairs(v10)
            for v9, v8 in v11, v10, v12 do
                if v8 == 2 then
                    v7 = v9
                    break
                end
            end
            if not (v7 == "") then
                stopBGM(0, 30)
                if v0.musicTitle[v2] == v7 then
                    v0.selectFlag[v7] = 1
                else
                    v0.selectFlag[v7] = 0
                end
                v3 = ""
                v1 = true
            else
                break
            end
        end
    end
    if v1 == true then
        v4()
        v1 = false
        wait(3)
    end
    wait(2)
    end
    v6()
    run(cGetFileName("script", "snr_mainmenu"))
end
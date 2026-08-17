local l0_0 = {layerNumber = {novel_1_a = 50, novel_1_b = 51, novel_2_a = 52, novel_2_b = 53, novel_2_c = 54, novel_3_aa = 55, novel_3_ab = 56, novel_3_ac = 57, novel_3_ad = 58, novel_3_ba = 59, novel_3_bb = 60, novel_3_bc = 61, novel_3_bd = 62, novel_3_ca = 63, novel_3_cb = 64, novel_3_cc = 65, novel_3_cd = 66, novel_3_da = 67, novel_3_db = 68, novel_3_dc = 69, novel_3_dd = 70, novel_3_ea = 71, novel_3_eb = 72, novel_3_ec = 73, novel_3_ed = 74, novel_4_a = 75, novel_4_b = 76, novel_4_c = 77, novel_4_d = 78}, indexNumber = {hardCover = 0, bar = 2, icon = 3, mask = 7, key = 8, novelBg = 0, sentence = 1, novelBar = 11, title = 12, bookMark = 13}, novelTitle = {"novel03", "novel01", "novel04", "novel02", "novel05"}, novelKey = {novel01 = 1, novel02 = 2, novel03 = 3, novel04 = 4, novel05 = 5}, layerName = {novel01 = "novel_3_a", novel02 = "novel_3_b", novel03 = "novel_3_c", novel04 = "novel_3_d", novel05 = "novel_3_e"}, novelPageMax = {novel01 = 112, novel02 = 159, novel03 = 119, novel04 = 119, novel05 = 452}, t_novelFlag = {}}
local l0_1 = 0
local l0_2 = 1
for l0_6 = 1, 5, 1 do
    if systemSave.novelGetFlag[l0_0.novelTitle[l0_6]] == true then
        l0_0.t_novelFlag[l0_2] = l0_0.novelTitle[l0_6]
        l0_2 = l0_2 + 1
    end
end
local l0_3 = function(l1_0, l1_1, l1_2, l1_3)
    for l1_7 = 1, string.len(l1_3), 1 do
        local l1_8 = string.sub(l1_3, l1_7, l1_7)
        layerCopy(l1_0 + l1_7 - 1, l0_0.layerNumber.novel_4_c)
        layerPosition(l1_0 + l1_7 - 1, l1_1, l1_2 + 7 * (l1_7 - 1))
        layerClip(l1_0 + l1_7 - 1, l1_8 * 7, 0, (l1_8 + 1) * 7, 7)
    end
end
local l0_4 = function(l1_0, l1_1, l1_2, l1_3)
    if l1_3 < 10 then
        l1_3 = "00" .. l1_3
    elseif l1_3 < 100 then
        l1_3 = "0" .. l1_3
    end
    for l1_7 = 1, string.len(l1_3), 1 do
        local l1_8 = string.sub(l1_3, l1_7, l1_7)
        layerCopy(l1_0 + l1_7 - 1, l0_0.layerNumber.novel_4_d)
        layerPosition(l1_0 + l1_7 - 1, l1_1, l1_2 + 7 * (l1_7 - 1))
        layerClip(l1_0 + l1_7 - 1, l1_8 * 7, 0, (l1_8 + 1) * 7, 7)
    end
end
local l0_5 = function(l1_0)
    layerCopy(l0_0.indexNumber.icon, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0]] .. "b"])
    layerPosition(l0_0.indexNumber.icon, 52, 189)
    layerCopy(l0_0.indexNumber.icon + 2, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0 - 1 < 1 and #l0_0.t_novelFlag or l1_0 - 1]] .. "b"])
    layerPosition(l0_0.indexNumber.icon + 2, 52, 222)
    layerCopy(l0_0.indexNumber.icon + 1, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0 + 1 > #l0_0.t_novelFlag and 1 or l1_0 + 1]] .. "b"])
    layerPosition(l0_0.indexNumber.icon + 1, 52, 158)
end
local l0_6 = function(l1_0, l1_1, l1_2)
    local l1_3 = l0_0.indexNumber.icon + 3
    if l1_2 == "down" then
        layerCopy(l1_3, l0_0.indexNumber.icon + 1)
        layerPosition(l1_3, 52, 158)
        layerScale(l1_3, 100, 100)
        layerMoveScale(l1_3, 100, 0, 30)
        layerMovePosition(l1_3, 52, 142, 30)
        layerCopy(l0_0.indexNumber.icon, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0]] .. "b"])
        layerPosition(l0_0.indexNumber.icon, 52, 222)
        layerMovePosition(l0_0.indexNumber.icon, 52, 189, 30)
        layerCopy(l0_0.indexNumber.icon + 1, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_1]] .. "b"])
        layerPosition(l0_0.indexNumber.icon + 1, 52, 189)
        layerMovePosition(l0_0.indexNumber.icon + 1, 52, 158, 30)
        layerCopy(l0_0.indexNumber.icon + 2, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0 - 1 < 1 and #l0_0.t_novelFlag or l1_0 - 1]] .. "b"])
        layerPosition(l0_0.indexNumber.icon + 2, 52, 235)
        layerScale(l0_0.indexNumber.icon + 2, 100, 0)
        layerClip(l0_0.indexNumber.icon + 2, 0, 0, 55, 26)
        layerMoveClip(l0_0.indexNumber.icon + 2, 0, 0, 55, 33, 30)
        layerMoveScale(l0_0.indexNumber.icon + 2, 100, 100, 30)
        layerMovePosition(l0_0.indexNumber.icon + 2, 52, 222, 30)
    elseif l1_2 == "up" then
        layerCopy(l1_3, l0_0.indexNumber.icon + 2)
        layerPosition(l1_3, 52, 222)
        layerScale(l1_3, 100, 100)
        layerMoveClip(l1_3, 0, 0, 55, 26, 30)
        layerMoveScale(l1_3, 100, 0, 30)
        layerMovePosition(l1_3, 52, 235, 30)
        layerCopy(l0_0.indexNumber.icon, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0]] .. "b"])
        layerPosition(l0_0.indexNumber.icon, 52, 158)
        layerMovePosition(l0_0.indexNumber.icon, 52, 189, 30)
        layerCopy(l0_0.indexNumber.icon + 1, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0 + 1 > #l0_0.t_novelFlag and 1 or l1_0 + 1]] .. "b"])
        layerPosition(l0_0.indexNumber.icon + 1, 52, 142)
        layerScale(l0_0.indexNumber.icon + 1, 100, 0)
        layerMoveScale(l0_0.indexNumber.icon + 1, 100, 100, 30)
        layerMovePosition(l0_0.indexNumber.icon + 1, 52, 158, 30)
        layerCopy(l0_0.indexNumber.icon + 2, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_1]] .. "b"])
        layerPosition(l0_0.indexNumber.icon + 2, 52, 189)
        layerMovePosition(l0_0.indexNumber.icon + 2, 52, 222, 30)
    end
end
local l0_7 = function(l1_0, l1_1, l1_2)
    layerCopy(l0_0.indexNumber.hardCover + 1, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_1]] .. "a"])
    layerCopy(l0_0.indexNumber.hardCover, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0]] .. "a"])
    if l1_2 == "down" then
        layerPosition(l0_0.indexNumber.hardCover, 0, 270)
        layerMovePosition(l0_0.indexNumber.hardCover + 1, 0, -270, 30)
    elseif l1_2 == "up" then
        layerPosition(l0_0.indexNumber.hardCover, 0, -270)
        layerMovePosition(l0_0.indexNumber.hardCover + 1, 0, 270, 30)
    end
    layerMovePosition(l0_0.indexNumber.hardCover, 0, 0, 30)
    l0_6(l1_0, l1_1, l1_2)
    layerCopy(10, l0_0.layerNumber.novel_4_b)
    layerClip(10, 0, 0, 7, 61)
    layerPosition(10, 115, 205)
    if not (systemSave.bookMark[l0_0.t_novelFlag[l1_0]] == 0) then
        l0_4(11, 115, 250, systemSave.bookMark[l0_0.t_novelFlag[l1_0]])
    else
        layerLoad(11, "")
        layerLoad(12, "")
        layerLoad(13, "")
        layerClip(10, 7, 0, 14, 61)
    end
    wait(30)
    layerLoad(l0_0.indexNumber.hardCover + 1, "")
end
local l0_8 = function(l1_0)
    layerCopy(l0_0.indexNumber.hardCover, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0]] .. "a"])
    l0_5(l1_0)
    layerCopy(l0_0.indexNumber.bar, l0_0.layerNumber.novel_1_a)
    layerPosition(l0_0.indexNumber.bar, 15, 0)
    layerCopy(l0_0.indexNumber.mask, l0_0.layerNumber.novel_1_b)
    layerPosition(l0_0.indexNumber.mask, 59, 158)
    l0_3(14, 91, 10, "0" .. #l0_0.t_novelFlag)
    l0_3(16, 91, 40, "05")
    layerCopy(10, l0_0.layerNumber.novel_4_b)
    layerClip(10, 0, 0, 7, 61)
    layerPosition(10, 115, 205)
    if not (systemSave.bookMark[l0_0.t_novelFlag[l1_0]] == 0) then
        l0_4(11, 115, 250, systemSave.bookMark[l0_0.t_novelFlag[l1_0]])
    else
        layerClip(10, 7, 0, 14, 61)
    end
    switchScreen(0, "", 60)
end
local l0_9 = function()
    for l1_3 = 0, 20, 1 do
        layerLoad(l1_3, "")
    end
    switchScreen(0, "", 60)
end
local l0_10 = function(l1_0)
    local l1_1 = l1_0 or 1
    l0_8(l1_1)
    local l1_2 = 1
    local l1_3 = false
    local l1_4 = ""
    while true do
        if pressButton("UP") == true then
            if l1_3 == false then
                l1_2 = l1_1
                l1_1 = l1_1 + 1 > #l0_0.t_novelFlag and 1 or l1_1 + 1
                l1_3 = true
                l1_4 = "up"
            end
        end
        if pressButton("DOWN") == true then
            if l1_3 == false then
                l1_2 = l1_1
                l1_1 = l1_1 - 1 < 1 and #l0_0.t_novelFlag or l1_1 - 1
                l1_3 = true
                l1_4 = "down"
            end
        end
        if pressButton("RIGHT") == true then
            if l1_3 == false then
                l0_1 = 2
                keyPlaySE(seName.cross)
                break
            end
        end
        if pressButton("LEFT") == true then
            if l1_3 == false then
                keyPlaySE(seName.circle)
                l0_1 = 1
                break
            end
        end
        if l1_3 == true then
            keyPlaySE(seName.arrowKey)
            l0_7(l1_1, l1_2, l1_4)
            l1_3 = false
        end
        wait(2)
    end
    l0_9()
    return l1_1
end
local l0_11 = function(l1_0, l1_1, l1_2)
    if l1_2 == 1 then
        comLayerLoadFalse(l0_0.indexNumber.sentence + 4, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 - 2 .. ".gim")
        comLayerLoadFalse(l0_0.indexNumber.sentence + 5, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 + 2 .. ".gim")
    elseif l1_2 == 2 then
        comLayerLoadFalse(l0_0.indexNumber.sentence, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 - 2 .. ".gim")
        comLayerLoadFalse(l0_0.indexNumber.sentence + 1, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 + 2 .. ".gim")
    elseif l1_2 == 3 then
        comLayerLoadFalse(l0_0.indexNumber.sentence + 2, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 - 2 .. ".gim")
        comLayerLoadFalse(l0_0.indexNumber.sentence + 3, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 + 2 .. ".gim")
    end
end
local l0_12 = function(l1_0, l1_1, l1_2)
    layerCopy(l0_0.indexNumber.novelBg, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0]] .. "d"])
    layerCopy(l0_0.indexNumber.novelBar, l0_0.layerNumber.novel_4_a)
    layerCopy(l0_0.indexNumber.title, l0_0.layerNumber[l0_0.layerName[l0_0.t_novelFlag[l1_0]] .. "c"])
    layerPosition(l0_0.indexNumber.title, 462, 5)
    layerCopy(l0_0.indexNumber.bookMark, l0_0.layerNumber.novel_4_b)
    if systemSave.bookMark[l0_0.novelTitle[l1_0]] == 0 then
        layerClip(l0_0.indexNumber.bookMark, 7, 0, 14, 61)
    else
        layerClip(l0_0.indexNumber.bookMark, 0, 0, 7, 61)
        l0_4(28, 457, 245, systemSave.bookMark[l0_0.t_novelFlag[l1_0]])
    end
    layerPosition(l0_0.indexNumber.bookMark, 457, 200)
    if l1_1 < 10 then
        l0_3(14, 470, 205, "00" .. l1_1)
    elseif l1_1 < 100 then
        l0_3(14, 470, 205, "0" .. l1_1)
    else
        l0_3(14, 470, 205, l1_1)
    end
    l0_3(17, 470, 243, l0_0.novelPageMax[l0_0.t_novelFlag[l1_0]])
    layerLoad(l0_0.indexNumber.sentence, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 .. ".gim")
    comLayerLoadFalse(l0_0.indexNumber.sentence + 2, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 - 1 .. ".gim")
    comLayerLoadFalse(l0_0.indexNumber.sentence + 3, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 + 1 .. ".gim")
    layerPosition(l0_0.indexNumber.sentence, 20, 0)
    l0_11(l1_0, l1_1, l1_2)
    switchScreen(0, "", 60)
end
local l0_13 = function()
    for l1_3 = 0, 40, 1 do
        layerLoad(l1_3, "")
    end
    fontClear()
    switchScreen(0, "", 60)
end
local l0_14 = function(l1_0, l1_1)
    if systemSave.bookMark[l0_0.t_novelFlag[l1_0]] == l1_1 then
        layerLoad(28, "")
        layerLoad(29, "")
        layerLoad(30, "")
        systemSave.bookMark[l0_0.t_novelFlag[l1_0]] = 0
        layerClip(l0_0.indexNumber.bookMark, 7, 0, 14, 61)
    else
        systemSave.bookMark[l0_0.t_novelFlag[l1_0]] = l1_1
        layerClip(l0_0.indexNumber.bookMark, 0, 0, 7, 61)
        l0_4(28, 457, 245, systemSave.bookMark[l0_0.t_novelFlag[l1_0]])
    end
end
local l0_15 = function(l1_0)
    local l1_1 = systemSave.bookMark[l0_0.t_novelFlag[l1_0]] > 0 and systemSave.bookMark[l0_0.t_novelFlag[l1_0]] or 1
    local l1_2 = 1
    local l1_3 = false
    local l1_4 = l0_0.novelPageMax[l0_0.t_novelFlag[l1_0]]
    local l1_5 = 1
    local l1_6 = 1
    local l1_7 = 1
    local l1_8 = 1
    l0_12(l1_0, l1_1, l1_8)
    while true do
        if pressButton("UP") == true then
            if l1_3 == false then
                l1_2 = l1_1
                l1_1 = l1_4 < l1_1 + 1 and l1_4 or l1_1 + 1
                l1_3 = true
            end
        end
        if pressButton("DOWN") == true then
            if l1_3 == false then
                l1_2 = l1_1
                l1_1 = l1_1 - 1 < 1 and 1 or l1_1 - 1
                l1_3 = true
            end
        end
        if pressButton("RIGHT") == true then
            if l1_3 == false then
                keyPlaySE(seName.cross)
                l0_1 = 0
                break
            end
        end
        if pressButton("LEFT") == true then
            if l1_3 == false then
                l0_14(l1_0, l1_1)
                wait(10)
            end
        end
        if l1_3 == true then
            fontClear()
            if not (l1_1 == l1_2) then
                l1_7 = l1_6
                if 0 < l1_1 - l1_2 then
                    l1_6 = 1
                    if l1_8 == 1 then
                        l1_5 = 3
                        l1_8 = 2
                    elseif l1_8 == 2 then
                        l1_5 = 5
                        l1_8 = 3
                    elseif l1_8 == 3 then
                        l1_5 = 1
                        l1_8 = 1
                    end
                else
                    l1_6 = -1
                    if l1_8 == 1 then
                        l1_5 = 2
                        l1_8 = 2
                    elseif l1_8 == 2 then
                        l1_5 = 4
                        l1_8 = 3
                    elseif l1_8 == 3 then
                        l1_5 = 0
                        l1_8 = 1
                    end
                end
                wait(5)
                if not (l1_6 == l1_7) then
                    l1_8 = 1
                    l1_5 = 0
                    layerLoad(l0_0.indexNumber.sentence + 1, "")
                    layerLoad(l0_0.indexNumber.sentence + 2, "")
                    layerLoad(l0_0.indexNumber.sentence + 3, "")
                    layerLoad(l0_0.indexNumber.sentence + 4, "")
                    layerLoad(l0_0.indexNumber.sentence + 5, "")
                    layerLoad(l0_0.indexNumber.sentence, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 .. ".gim")
                    layerPosition(l0_0.indexNumber.sentence + l1_5, 20, 0)
                    comLayerLoadFalse(l0_0.indexNumber.sentence + 2, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 - 1 .. ".gim")
                    comLayerLoadFalse(l0_0.indexNumber.sentence + 3, "novel/" .. l0_0.t_novelFlag[l1_0] .. "_" .. l1_1 + 1 .. ".gim")
                    l0_11(l1_0, l1_1, l1_8)
                else
                    while true do
                        if layerIsLoad(l0_0.indexNumber.sentence + l1_5) == true then
                            layerVisible(l0_0.indexNumber.sentence + l1_5, true)
                            layerPosition(l0_0.indexNumber.sentence + l1_5, 20, 0)
                            l0_11(l1_0, l1_1, l1_8)
                            break
                        end
                        wait(1)
                    end
                end
            end
            if l1_1 < 10 then
                l0_3(14, 470, 205, "00" .. l1_1)
            elseif l1_1 < 100 then
                l0_3(14, 470, 205, "0" .. l1_1)
            else
                l0_3(14, 470, 205, l1_1)
            end
            l1_3 = false
        end
        wait(2)
    end
    l0_13()
end
main = function()
    if l0_2 == 1 then
        msg("まだ一冊も取得していません。")
        run(cGetFileName("script", "snr_mainmenu"))
    end
    systemConfig.unsetConfigButton()
    logEnable(false)
    advPart(false)
    startLoading()
    for l1_3, l1_4 in pairs(l0_0.layerNumber) do
        comLayerLoadFalse(l1_4, "novel/" .. l1_3 .. ".gim")
    end
    waitLoading()
    endLoading()
    local l1_0 = 1
    while l0_1 < 2 do
        if l0_1 == 0 then
            l1_0 = l0_10(l1_0)
        elseif l0_1 == 1 then
            l0_15(l1_0)
        end
        wait(2)
    end
    autoSystemSave(0)
    cInitGame()
    run(cGetFileName("script", "snr_mainmenu"))
end

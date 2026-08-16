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
local __pld_ord = {l0_2, l0_1}
local __pld_select, __pld_unpack, __pld_tonumber, __pld_error = select, unpack, tonumber, error
local __pld_pack = function(...) return {n = __pld_select('#', ...), ...} end
local __pld_get = function(R, B, i) local x = R[i] if B[i] then return x.v end return x end
local __pld_set = function(R, B, i, v) if B[i] then R[i].v = v else R[i] = v end end
local __pld_R, __pld_B, __pld_top = {}, {}, 0
local __pld_pc = 1
while true do
if __pld_pc == 1 then
__pld_R[0] = advPart
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = logEnable
__pld_R[1] = false
__pld_R[0](__pld_R[1])
__pld_R[0] = systemConfig
__pld_R[0] = __pld_R[0]["unsetConfigButton"]
__pld_R[0]()
__pld_R[0] = gameSave
__pld_R[0] = __pld_R[0]["tutorial"]
__pld_R[0] = __pld_R[0]["firstFragment"]
if not (__pld_R[0] == 0) then __pld_pc = 14 else __pld_pc = 15 end
elseif __pld_pc == 14 then
__pld_pc = 50
elseif __pld_pc == 15 then
__pld_R[0] = gameSave
__pld_R[0] = __pld_R[0]["startMenuState"]
if not (__pld_R[0] == 1) then __pld_pc = 18 else __pld_pc = 19 end
elseif __pld_pc == 18 then
__pld_pc = 30
elseif __pld_pc == 19 then
__pld_R[0] = "s1s_10"
doScriptScene = __pld_R[0]
__pld_R[0] = run
__pld_R[1] = cGetFileName
__pld_R[2] = "script"
__pld_R[3] = "snr_s1_10_s"
do 
local __pld_rs = __pld_pack(__pld_R[1](__pld_R[2], __pld_R[3]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 1 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 1 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 1 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 1 + __pld_i - 1) end __pld_R[0](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[0] = quit
__pld_R[0]()
__pld_pc = 50
elseif __pld_pc == 30 then
__pld_R[0] = vms
__pld_R[1] = 16817
__pld_R[2] = "NONVOICE"
__pld_R[3] = "【■おしらせ】ゲームメニューに、『Ｆｒａｇｍｅｎｔ』モードが追加されました。"
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
__pld_R[0] = vms
__pld_R[1] = 16818
__pld_R[2] = "NONVOICE"
__pld_R[3] = "【■おしらせ】物語の続きはＦｒａｇｍｅｎｔモードより参照することができます。"
__pld_R[0](__pld_R[1], __pld_R[2], __pld_R[3])
__pld_R[0] = cInitGame
__pld_R[0]()
__pld_R[0] = run
__pld_R[1] = cGetFileName
__pld_R[2] = "script"
__pld_R[3] = "snr_mainmenu"
do 
local __pld_rs = __pld_pack(__pld_R[1](__pld_R[2], __pld_R[3]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 1 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 1 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 1 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 1 + __pld_i - 1) end __pld_R[0](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[0] = quit
__pld_R[0]()
__pld_pc = 50
elseif __pld_pc == 50 then
__pld_R[0] = comSectionStoryGetCount
__pld_R[0] = __pld_R[0]()
if not (__pld_R[0] == 0) then __pld_pc = 53 else __pld_pc = 54 end
elseif __pld_pc == 53 then
__pld_pc = 64
elseif __pld_pc == 54 then
__pld_R[1] = "s1s_20"
doScriptScene = __pld_R[1]
__pld_R[1] = run
__pld_R[2] = cGetFileName
__pld_R[3] = "script"
__pld_R[4] = "snr_s1_10_s"
do 
local __pld_rs = __pld_pack(__pld_R[2](__pld_R[3], __pld_R[4]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 2 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 2 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 2 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 2 + __pld_i - 1) end __pld_R[1](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[1] = quit
__pld_R[1]()
__pld_pc = 64
elseif __pld_pc == 64 then
__pld_R[1] = selectItemNo
if not (__pld_R[1] < 1) then __pld_pc = 66 else __pld_pc = 67 end
elseif __pld_pc == 66 then
__pld_pc = 68
elseif __pld_pc == 67 then
selectItemNo = __pld_R[0]
__pld_pc = 68
elseif __pld_pc == 68 then
__pld_R[1] = selectItemNo
if not (__pld_R[0] < __pld_R[1]) then __pld_pc = 70 else __pld_pc = 71 end
elseif __pld_pc == 70 then
__pld_pc = 72
elseif __pld_pc == 71 then
selectItemNo = __pld_R[0]
__pld_pc = 72
elseif __pld_pc == 72 then
__pld_R[1] = l0_2
__pld_R[1]()
__pld_R[1] = false
__pld_R[2] = false
__pld_R[3] = 0
__pld_R[4] = selectItemNo
__pld_R[5] = __pld_R[4]
__pld_R[6] = false
__pld_R[7] = 1
__pld_R[8] = 1
__pld_R[9] = 1
__pld_R[10] = systemConfig
__pld_R[10] = __pld_R[10]["setConfigButton"]
__pld_R[10]()
__pld_pc = 86
elseif __pld_pc == 86 then
__pld_R[10] = pressButton
__pld_R[11] = "RIGHT"
__pld_R[10] = __pld_R[10](__pld_R[11])
if not (__pld_R[10] == true) then __pld_pc = 90 else __pld_pc = 91 end
elseif __pld_pc == 90 then
__pld_pc = 103
elseif __pld_pc == 91 then
if not (__pld_R[6] == false) then __pld_pc = 92 else __pld_pc = 93 end
elseif __pld_pc == 92 then
__pld_pc = 103
elseif __pld_pc == 93 then
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 94 else __pld_pc = 95 end
elseif __pld_pc == 94 then
__pld_pc = 103
elseif __pld_pc == 95 then
__pld_R[5] = __pld_R[4]
__pld_R[10] = __pld_R[4] + 1
if not (__pld_R[0] < __pld_R[10]) then __pld_pc = 98 else __pld_pc = 99 end
elseif __pld_pc == 98 then
__pld_pc = 101
elseif __pld_pc == 99 then
do local __pld_t = __pld_R[0] if __pld_t then __pld_R[4] = __pld_t __pld_pc = 100 else __pld_pc = 101 end end
elseif __pld_pc == 100 then
__pld_pc = 102
elseif __pld_pc == 101 then
__pld_R[4] = __pld_R[4] + 1
__pld_pc = 102
elseif __pld_pc == 102 then
__pld_R[6] = true
__pld_pc = 103
elseif __pld_pc == 103 then
__pld_R[10] = pressButton
__pld_R[11] = "LEFT"
__pld_R[10] = __pld_R[10](__pld_R[11])
if not (__pld_R[10] == true) then __pld_pc = 107 else __pld_pc = 108 end
elseif __pld_pc == 107 then
__pld_pc = 115
elseif __pld_pc == 108 then
if not (__pld_R[6] == false) then __pld_pc = 109 else __pld_pc = 110 end
elseif __pld_pc == 109 then
__pld_pc = 115
elseif __pld_pc == 110 then
if not (1 < __pld_R[4]) then __pld_pc = 111 else __pld_pc = 112 end
elseif __pld_pc == 111 then
__pld_pc = 115
elseif __pld_pc == 112 then
__pld_R[5] = __pld_R[4]
__pld_R[4] = __pld_R[4] - 1
__pld_R[6] = true
__pld_pc = 115
elseif __pld_pc == 115 then
__pld_R[10] = pressButton
__pld_R[11] = "R"
__pld_R[10] = __pld_R[10](__pld_R[11])
if not (__pld_R[10] == true) then __pld_pc = 119 else __pld_pc = 120 end
elseif __pld_pc == 119 then
__pld_pc = 147
elseif __pld_pc == 120 then
if not (__pld_R[6] == false) then __pld_pc = 121 else __pld_pc = 122 end
elseif __pld_pc == 121 then
__pld_pc = 147
elseif __pld_pc == 122 then
__pld_R[5] = __pld_R[4]
__pld_R[10] = __pld_R[4] + 1
__pld_R[11] = __pld_R[0]
__pld_R[12] = 1
do
local __pld_i = __pld_tonumber(__pld_R[10]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[11]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[12]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[10] = __pld_i - __pld_s __pld_R[11] = __pld_l __pld_R[12] = __pld_s
end
__pld_pc = 142
elseif __pld_pc == 127 then
__pld_R[14] = sceneId2aCard
__pld_R[15] = gameSave
__pld_R[15] = __pld_R[15]["storyRoute"]
__pld_R[15] = __pld_R[15][__pld_R[13]]
__pld_R[15] = __pld_R[15]["sceneId"]
__pld_R[14] = __pld_R[14][__pld_R[15]]
__pld_R[4] = __pld_R[13]
__pld_R[15] = gameSave
__pld_R[15] = __pld_R[15]["myCard"]
__pld_R[15] = __pld_R[15][__pld_R[14]]
__pld_R[15] = __pld_R[15]["hold"]
if not (__pld_R[15] == (-1)) then __pld_pc = 139 else __pld_pc = 140 end
elseif __pld_pc == 139 then
__pld_pc = 142
elseif __pld_pc == 140 then
__pld_R[4] = __pld_R[13]
__pld_pc = 143
elseif __pld_pc == 142 then
do local __pld_s = __pld_R[12] local __pld_i = __pld_R[10] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[11]) or (__pld_s <= 0 and __pld_i >= __pld_R[11]) then
__pld_R[10] = __pld_i __pld_R[13] = __pld_i __pld_pc = 127
else __pld_pc = 143 end end
elseif __pld_pc == 143 then
__pld_R[10] = wait
__pld_R[11] = 5
__pld_R[10](__pld_R[11])
__pld_R[6] = true
__pld_pc = 147
elseif __pld_pc == 147 then
__pld_R[10] = pressButton
__pld_R[11] = "L"
__pld_R[10] = __pld_R[10](__pld_R[11])
if not (__pld_R[10] == true) then __pld_pc = 151 else __pld_pc = 152 end
elseif __pld_pc == 151 then
__pld_pc = 179
elseif __pld_pc == 152 then
if not (__pld_R[6] == false) then __pld_pc = 153 else __pld_pc = 154 end
elseif __pld_pc == 153 then
__pld_pc = 179
elseif __pld_pc == 154 then
__pld_R[5] = __pld_R[4]
__pld_R[10] = __pld_R[4] - 1
__pld_R[11] = 1
__pld_R[12] = (-1)
do
local __pld_i = __pld_tonumber(__pld_R[10]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[11]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[12]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[10] = __pld_i - __pld_s __pld_R[11] = __pld_l __pld_R[12] = __pld_s
end
__pld_pc = 174
elseif __pld_pc == 159 then
__pld_R[14] = sceneId2aCard
__pld_R[15] = gameSave
__pld_R[15] = __pld_R[15]["storyRoute"]
__pld_R[15] = __pld_R[15][__pld_R[13]]
__pld_R[15] = __pld_R[15]["sceneId"]
__pld_R[14] = __pld_R[14][__pld_R[15]]
__pld_R[4] = __pld_R[13]
__pld_R[15] = gameSave
__pld_R[15] = __pld_R[15]["myCard"]
__pld_R[15] = __pld_R[15][__pld_R[14]]
__pld_R[15] = __pld_R[15]["hold"]
if not (__pld_R[15] == (-1)) then __pld_pc = 171 else __pld_pc = 172 end
elseif __pld_pc == 171 then
__pld_pc = 174
elseif __pld_pc == 172 then
__pld_R[4] = __pld_R[13]
__pld_pc = 175
elseif __pld_pc == 174 then
do local __pld_s = __pld_R[12] local __pld_i = __pld_R[10] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[11]) or (__pld_s <= 0 and __pld_i >= __pld_R[11]) then
__pld_R[10] = __pld_i __pld_R[13] = __pld_i __pld_pc = 159
else __pld_pc = 175 end end
elseif __pld_pc == 175 then
__pld_R[10] = wait
__pld_R[11] = 5
__pld_R[10](__pld_R[11])
__pld_R[6] = true
__pld_pc = 179
elseif __pld_pc == 179 then
if not (__pld_R[6] == true) then __pld_pc = 180 else __pld_pc = 181 end
elseif __pld_pc == 180 then
__pld_pc = 206
elseif __pld_pc == 181 then
__pld_R[10] = keyPlaySE
__pld_R[11] = seName
__pld_R[11] = __pld_R[11]["arrowKey"]
__pld_R[10](__pld_R[11])
__pld_R[10] = fontClear
__pld_R[10]()
__pld_R[10] = l0_1
__pld_R[11] = __pld_R[4]
__pld_R[12] = __pld_R[5]
__pld_R[10](__pld_R[11], __pld_R[12])
__pld_R[3] = 0
__pld_R[6] = false
__pld_R[10] = layerLoad
__pld_R[11] = layerName
__pld_R[11] = __pld_R[11]["card1"]
__pld_R[12] = ""
__pld_R[10](__pld_R[11], __pld_R[12])
__pld_R[10] = layerLoad
__pld_R[11] = layerName
__pld_R[11] = __pld_R[11]["card3"]
__pld_R[12] = ""
__pld_R[10](__pld_R[11], __pld_R[12])
__pld_R[10] = wait
__pld_R[11] = 3
__pld_R[10](__pld_R[11])
__pld_pc = 206
elseif __pld_pc == 206 then
__pld_R[10] = sceneId2aCard
__pld_R[11] = gameSave
__pld_R[11] = __pld_R[11]["storyRoute"]
__pld_R[11] = __pld_R[11][__pld_R[4]]
__pld_R[11] = __pld_R[11]["sceneId"]
__pld_R[10] = __pld_R[10][__pld_R[11]]
__pld_R[11] = gameSave
__pld_R[11] = __pld_R[11]["myCard"]
__pld_R[11] = __pld_R[11][__pld_R[10]]
__pld_R[11] = __pld_R[11]["hold"]
if __pld_R[11] == (-1) then __pld_pc = 217 else __pld_pc = 218 end
elseif __pld_pc == 217 then
__pld_pc = 242
elseif __pld_pc == 218 then
if not (__pld_R[3] <= 3) then __pld_pc = 219 else __pld_pc = 220 end
elseif __pld_pc == 219 then
__pld_pc = 242
elseif __pld_pc == 220 then
if not (3 <= __pld_R[3]) then __pld_pc = 221 else __pld_pc = 222 end
elseif __pld_pc == 221 then
__pld_pc = 235
elseif __pld_pc == 222 then
__pld_R[11] = layerLoadAsync
__pld_R[12] = 0
__pld_R[13] = layerName
__pld_R[13] = __pld_R[13]["card1"]
__pld_R[14] = cGetFileName
__pld_R[15] = "card"
__pld_R[16] = "crd_"
__pld_R[17] = __pld_R[10]
__pld_R[18] = "_a"
__pld_R[16] = __pld_R[16] .. __pld_R[17] .. __pld_R[18]
do 
local __pld_rs = __pld_pack(__pld_R[14](__pld_R[15], __pld_R[16]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 14 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 14 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 12 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 12 + __pld_i - 1) end __pld_R[11](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[2] = true
__pld_pc = 235
elseif __pld_pc == 235 then
__pld_R[11] = __pld_R[3] + 1
if not (4 < __pld_R[11]) then __pld_pc = 237 else __pld_pc = 238 end
elseif __pld_pc == 237 then
__pld_pc = 241
elseif __pld_pc == 238 then
__pld_R[11] = 4
do local __pld_t = __pld_R[11] if __pld_t then __pld_R[3] = __pld_t __pld_pc = 240 else __pld_pc = 241 end end
elseif __pld_pc == 240 then
__pld_pc = 242
elseif __pld_pc == 241 then
__pld_R[3] = __pld_R[3] + 1
__pld_pc = 242
elseif __pld_pc == 242 then
if not (__pld_R[2] == true) then __pld_pc = 243 else __pld_pc = 244 end
elseif __pld_pc == 243 then
__pld_pc = 280
elseif __pld_pc == 244 then
__pld_R[11] = layerIsLoad
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["card1"]
__pld_R[11] = __pld_R[11](__pld_R[12])
if not (__pld_R[11] == true) then __pld_pc = 249 else __pld_pc = 250 end
elseif __pld_pc == 249 then
__pld_pc = 280
elseif __pld_pc == 250 then
__pld_R[11] = layerVisible
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["card1"]
__pld_R[13] = true
__pld_R[11](__pld_R[12], __pld_R[13])
__pld_R[11] = layerAlpha
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["card1"]
__pld_R[13] = 0
__pld_R[11](__pld_R[12], __pld_R[13])
__pld_R[11] = layerPosition
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["card1"]
__pld_R[13] = 130
__pld_R[14] = 110
__pld_R[11](__pld_R[12], __pld_R[13], __pld_R[14])
__pld_R[11] = layerMovePosition
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["card1"]
__pld_R[13] = 130
__pld_R[14] = 130
__pld_R[15] = 10
__pld_R[11](__pld_R[12], __pld_R[13], __pld_R[14], __pld_R[15])
__pld_R[11] = layerMoveAlpha
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["card1"]
__pld_R[13] = 100
__pld_R[14] = 10
__pld_R[11](__pld_R[12], __pld_R[13], __pld_R[14])
__pld_R[2] = false
__pld_pc = 280
elseif __pld_pc == 280 then
__pld_R[11] = pressButton
__pld_R[12] = "CIRCLE"
__pld_R[11] = __pld_R[11](__pld_R[12])
if __pld_R[11] == true then __pld_pc = 284 else __pld_pc = 285 end
elseif __pld_pc == 284 then
__pld_pc = 286
elseif __pld_pc == 285 then
__pld_R[7] = 0
__pld_pc = 286
elseif __pld_pc == 286 then
__pld_R[11] = pressButton
__pld_R[12] = "CIRCLE"
__pld_R[11] = __pld_R[11](__pld_R[12])
if not (__pld_R[11] == true) then __pld_pc = 290 else __pld_pc = 291 end
elseif __pld_pc == 290 then
__pld_pc = 368
elseif __pld_pc == 291 then
if not (__pld_R[7] == 0) then __pld_pc = 292 else __pld_pc = 293 end
elseif __pld_pc == 292 then
__pld_pc = 368
elseif __pld_pc == 293 then
if not (__pld_R[4] == 1) then __pld_pc = 294 else __pld_pc = 295 end
elseif __pld_pc == 294 then
__pld_pc = 301
elseif __pld_pc == 295 then
__pld_R[11] = cGetFileName
__pld_R[12] = "sysgim"
__pld_R[13] = "sys_5_b"
__pld_R[11] = __pld_R[11](__pld_R[12], __pld_R[13])
if __pld_R[11] then __pld_pc = 300 else __pld_pc = 301 end
elseif __pld_pc == 300 then
__pld_pc = 305
elseif __pld_pc == 301 then
__pld_R[11] = cGetFileName
__pld_R[12] = "sysgim"
__pld_R[13] = "sys_5_a"
__pld_R[11] = __pld_R[11](__pld_R[12], __pld_R[13])
__pld_pc = 305
elseif __pld_pc == 305 then
fileName = __pld_R[11]
__pld_R[11] = keyPlaySE
__pld_R[12] = seName
__pld_R[12] = __pld_R[12]["circle"]
__pld_R[11](__pld_R[12])
__pld_R[11] = comDlgYesNo
__pld_R[12] = fileName
__pld_R[13] = 100
__pld_R[14] = 80
__pld_R[11] = __pld_R[11](__pld_R[12], __pld_R[13], __pld_R[14])
if not (__pld_R[11] == true) then __pld_pc = 316 else __pld_pc = 317 end
elseif __pld_pc == 316 then
__pld_pc = 352
elseif __pld_pc == 317 then
__pld_R[11] = comSectionUID2ScriptFileName
__pld_R[12] = gameSave
__pld_R[12] = __pld_R[12]["storyRoute"]
__pld_R[12] = __pld_R[12][__pld_R[4]]
__pld_R[12] = __pld_R[12]["sceneId"]
__pld_R[11] = __pld_R[11](__pld_R[12])
__pld_R[12] = gameSave
__pld_R[12] = __pld_R[12]["storyRoute"]
__pld_R[12] = __pld_R[12][__pld_R[4]]
__pld_R[12] = __pld_R[12]["sceneId"]
doScriptScene = __pld_R[12]
__pld_R[12] = (-1)
selectItemNo = __pld_R[12]
__pld_R[12] = gameSave
__pld_R[13] = gameSave
__pld_R[13] = __pld_R[13]["storyRoute"]
__pld_R[13] = __pld_R[13][__pld_R[4]]
__pld_R[13] = __pld_R[13]["ayanoTime"]
__pld_R[12]["ayanoTime"] = __pld_R[13]
__pld_R[12] = cClearNumStoryRoute
__pld_R[13] = __pld_R[4]
__pld_R[12](__pld_R[13])
__pld_R[12] = cInitGame
__pld_R[12]()
__pld_R[12] = fontClear
__pld_R[12]()
__pld_R[12] = run
__pld_R[13] = cGetFileName
__pld_R[14] = "script"
__pld_R[15] = __pld_R[11]
do 
local __pld_rs = __pld_pack(__pld_R[13](__pld_R[14], __pld_R[15]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 13 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 13 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 13 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 13 + __pld_i - 1) end __pld_R[12](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[12] = quit
__pld_R[12]()
__pld_pc = 355
elseif __pld_pc == 352 then
__pld_R[7] = 1
__pld_R[8] = 1
__pld_R[9] = 1
__pld_pc = 355
elseif __pld_pc == 355 then
__pld_R[11] = layerLoad
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["card3"]
__pld_R[13] = ""
__pld_R[11](__pld_R[12], __pld_R[13])
__pld_R[11] = switchScreen
__pld_R[12] = 0
__pld_R[13] = ""
__pld_R[14] = 5
__pld_R[11](__pld_R[12], __pld_R[13], __pld_R[14])
__pld_R[11] = wait
__pld_R[12] = 5
__pld_R[11](__pld_R[12])
__pld_pc = 368
elseif __pld_pc == 368 then
__pld_R[11] = pressButton
__pld_R[12] = "CROSS"
__pld_R[11] = __pld_R[11](__pld_R[12])
if __pld_R[11] == true then __pld_pc = 372 else __pld_pc = 373 end
elseif __pld_pc == 372 then
__pld_pc = 374
elseif __pld_pc == 373 then
__pld_R[8] = 0
__pld_pc = 374
elseif __pld_pc == 374 then
__pld_R[11] = pressButton
__pld_R[12] = "CROSS"
__pld_R[11] = __pld_R[11](__pld_R[12])
if not (__pld_R[11] == true) then __pld_pc = 378 else __pld_pc = 379 end
elseif __pld_pc == 378 then
__pld_pc = 390
elseif __pld_pc == 379 then
if not (__pld_R[8] == 0) then __pld_pc = 380 else __pld_pc = 381 end
elseif __pld_pc == 380 then
__pld_pc = 390
elseif __pld_pc == 381 then
__pld_R[11] = systemConfig
__pld_R[11] = __pld_R[11]["unsetConfigButton"]
__pld_R[11]()
__pld_R[11] = keyPlaySE
__pld_R[12] = seName
__pld_R[12] = __pld_R[12]["cross"]
__pld_R[11](__pld_R[12])
selectItemNo = __pld_R[4]
__pld_pc = 439
elseif __pld_pc == 390 then
__pld_R[11] = pressButton
__pld_R[12] = "TRIANGLE"
__pld_R[11] = __pld_R[11](__pld_R[12])
if __pld_R[11] == true then __pld_pc = 394 else __pld_pc = 395 end
elseif __pld_pc == 394 then
__pld_pc = 396
elseif __pld_pc == 395 then
__pld_R[9] = 0
__pld_pc = 396
elseif __pld_pc == 396 then
__pld_R[11] = pressButton
__pld_R[12] = "TRIANGLE"
__pld_R[11] = __pld_R[11](__pld_R[12])
if not (__pld_R[11] == true) then __pld_pc = 400 else __pld_pc = 401 end
elseif __pld_pc == 400 then
__pld_pc = 435
elseif __pld_pc == 401 then
if not (__pld_R[9] == 0) then __pld_pc = 402 else __pld_pc = 403 end
elseif __pld_pc == 402 then
__pld_pc = 435
elseif __pld_pc == 403 then
__pld_R[11] = systemConfig
__pld_R[11] = __pld_R[11]["unsetConfigButton"]
__pld_R[11]()
__pld_R[11] = keyPlaySE
__pld_R[12] = seName
__pld_R[12] = __pld_R[12]["cross"]
__pld_R[11](__pld_R[12])
__pld_R[11] = layerCopy
__pld_R[12] = 199
__pld_R[13] = layerName
__pld_R[13] = __pld_R[13]["effectBlack"]
__pld_R[11](__pld_R[12], __pld_R[13])
__pld_R[11] = fontClear
__pld_R[11]()
__pld_R[11] = switchScreen
__pld_R[12] = 0
__pld_R[13] = ""
__pld_R[14] = 60
__pld_R[11](__pld_R[12], __pld_R[13], __pld_R[14])
selectItemNo = __pld_R[4]
__pld_R[11] = comSectionFragmentItemInit
__pld_R[11]()
__pld_R[11] = cInitGame
__pld_R[11]()
__pld_R[11] = run
__pld_R[12] = cGetFileName
__pld_R[13] = "script"
__pld_R[14] = "snr_fragment_main"
do 
local __pld_rs = __pld_pack(__pld_R[12](__pld_R[13], __pld_R[14]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 12 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 12 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 12 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 12 + __pld_i - 1) end __pld_R[11](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[11] = quit
__pld_R[11]()
__pld_pc = 435
elseif __pld_pc == 435 then
__pld_R[11] = wait
__pld_R[12] = 2
__pld_R[11](__pld_R[12])
__pld_pc = 86
elseif __pld_pc == 439 then
__pld_R[10] = layerCopy
__pld_R[11] = 199
__pld_R[12] = layerName
__pld_R[12] = __pld_R[12]["effectBlack"]
__pld_R[10](__pld_R[11], __pld_R[12])
__pld_R[10] = fontClear
__pld_R[10]()
__pld_R[10] = switchScreen
__pld_R[11] = 0
__pld_R[12] = ""
__pld_R[13] = 60
__pld_R[10](__pld_R[11], __pld_R[12], __pld_R[13])
__pld_R[10] = cInitGame
__pld_R[10]()
__pld_R[10] = run
__pld_R[11] = cGetFileName
__pld_R[12] = "script"
__pld_R[13] = "snr_mainmenu"
do 
local __pld_rs = __pld_pack(__pld_R[11](__pld_R[12], __pld_R[13]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 11 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 11 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 11 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 11 + __pld_i - 1) end __pld_R[10](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[10] = quit
__pld_R[10]()
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end

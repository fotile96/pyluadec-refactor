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
local __pld_ord = {l0_4, l0_1, l0_0, l0_7, l0_2, l0_3, l0_8}
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
__pld_R[0] = cInitGame
__pld_R[0]()
__pld_R[0] = l0_4
__pld_R[0]()
__pld_R[0] = 1
__pld_R[1] = 0
__pld_R[2] = false
__pld_R[3] = false
__pld_R[4] = gameSave
__pld_R[4] = __pld_R[4]["startMenuState"]
if not (__pld_R[4] == 0) then __pld_pc = 21 else __pld_pc = 22 end
elseif __pld_pc == 21 then
__pld_pc = 558
elseif __pld_pc == 22 then
if not (__pld_R[3] == false) then __pld_pc = 23 else __pld_pc = 24 end
elseif __pld_pc == 23 then
__pld_pc = 291
elseif __pld_pc == 24 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 28 else __pld_pc = 29 end
elseif __pld_pc == 28 then
__pld_pc = 68
elseif __pld_pc == 29 then
if not (__pld_R[2] == false) then __pld_pc = 30 else __pld_pc = 31 end
elseif __pld_pc == 30 then
__pld_pc = 68
elseif __pld_pc == 31 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 35 else __pld_pc = 36 end
elseif __pld_pc == 35 then
__pld_pc = 39
elseif __pld_pc == 36 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["prologue"]
__pld_pc = 49
elseif __pld_pc == 39 then
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["prologue"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 43 else __pld_pc = 44 end
elseif __pld_pc == 43 then
__pld_pc = 48
elseif __pld_pc == 44 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["prologue"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 47 else __pld_pc = 48 end end
elseif __pld_pc == 47 then
__pld_pc = 49
elseif __pld_pc == 48 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 49
elseif __pld_pc == 49 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 52 else __pld_pc = 53 end
elseif __pld_pc == 52 then
__pld_pc = 67
elseif __pld_pc == 53 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["libFlag"]
if __pld_R[4] == true then __pld_pc = 56 else __pld_pc = 57 end
elseif __pld_pc == 56 then
__pld_pc = 67
elseif __pld_pc == 57 then
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["prologue"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 61 else __pld_pc = 62 end
elseif __pld_pc == 61 then
__pld_pc = 66
elseif __pld_pc == 62 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["prologue"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 65 else __pld_pc = 66 end end
elseif __pld_pc == 65 then
__pld_pc = 67
elseif __pld_pc == 66 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 67
elseif __pld_pc == 67 then
__pld_R[2] = true
__pld_pc = 68
elseif __pld_pc == 68 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 72 else __pld_pc = 73 end
elseif __pld_pc == 72 then
__pld_pc = 112
elseif __pld_pc == 73 then
if not (__pld_R[2] == false) then __pld_pc = 74 else __pld_pc = 75 end
elseif __pld_pc == 74 then
__pld_pc = 112
elseif __pld_pc == 75 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 79 else __pld_pc = 80 end
elseif __pld_pc == 79 then
__pld_pc = 83
elseif __pld_pc == 80 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["library"]
__pld_pc = 93
elseif __pld_pc == 83 then
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["option"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 87 else __pld_pc = 88 end
elseif __pld_pc == 87 then
__pld_pc = 92
elseif __pld_pc == 88 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 91 else __pld_pc = 92 end end
elseif __pld_pc == 91 then
__pld_pc = 93
elseif __pld_pc == 92 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 93
elseif __pld_pc == 93 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 96 else __pld_pc = 97 end
elseif __pld_pc == 96 then
__pld_pc = 111
elseif __pld_pc == 97 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["libFlag"]
if __pld_R[4] == true then __pld_pc = 100 else __pld_pc = 101 end
elseif __pld_pc == 100 then
__pld_pc = 111
elseif __pld_pc == 101 then
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["option"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 105 else __pld_pc = 106 end
elseif __pld_pc == 105 then
__pld_pc = 110
elseif __pld_pc == 106 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 109 else __pld_pc = 110 end end
elseif __pld_pc == 109 then
__pld_pc = 111
elseif __pld_pc == 110 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 111
elseif __pld_pc == 111 then
__pld_R[2] = true
__pld_pc = 112
elseif __pld_pc == 112 then
__pld_R[4] = pressButton
__pld_R[5] = "RIGHT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 116 else __pld_pc = 117 end
elseif __pld_pc == 116 then
__pld_pc = 123
elseif __pld_pc == 117 then
if not (__pld_R[2] == false) then __pld_pc = 118 else __pld_pc = 119 end
elseif __pld_pc == 118 then
__pld_pc = 123
elseif __pld_pc == 119 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["load"]
__pld_R[2] = true
__pld_pc = 123
elseif __pld_pc == 123 then
__pld_R[4] = pressButton
__pld_R[5] = "LEFT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 127 else __pld_pc = 128 end
elseif __pld_pc == 127 then
__pld_pc = 134
elseif __pld_pc == 128 then
if not (__pld_R[2] == false) then __pld_pc = 129 else __pld_pc = 130 end
elseif __pld_pc == 129 then
__pld_pc = 134
elseif __pld_pc == 130 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["prologue"]
__pld_R[2] = true
__pld_pc = 134
elseif __pld_pc == 134 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 138 else __pld_pc = 139 end
elseif __pld_pc == 138 then
__pld_pc = 525
elseif __pld_pc == 139 then
if not (__pld_R[2] == false) then __pld_pc = 140 else __pld_pc = 141 end
elseif __pld_pc == 140 then
__pld_pc = 525
elseif __pld_pc == 141 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["prologue"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 151 else __pld_pc = 152 end
elseif __pld_pc == 151 then
__pld_pc = 170
elseif __pld_pc == 152 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = "sof_10"
doScriptScene = __pld_R[4]
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_s0_10_f"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 272
elseif __pld_pc == 170 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 173 else __pld_pc = 174 end
elseif __pld_pc == 173 then
__pld_pc = 258
elseif __pld_pc == 174 then
__pld_R[3] = true
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 178 else __pld_pc = 179 end
elseif __pld_pc == 178 then
__pld_pc = 182
elseif __pld_pc == 179 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["scene"]
__pld_pc = 184
elseif __pld_pc == 182 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["novel"]
__pld_pc = 184
elseif __pld_pc == 184 then
__pld_R[4] = 1
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerKey0"]
__pld_R[5] = #(__pld_R[5])
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 253
elseif __pld_pc == 190 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 193 else __pld_pc = 194 end
elseif __pld_pc == 193 then
__pld_pc = 207
elseif __pld_pc == 194 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["library"]
if __pld_R[7] == __pld_R[8] then __pld_pc = 197 else __pld_pc = 198 end
elseif __pld_pc == 197 then
__pld_pc = 253
elseif __pld_pc == 198 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 50
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 253
elseif __pld_pc == 207 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 210 else __pld_pc = 211 end
elseif __pld_pc == 210 then
__pld_pc = 215
elseif __pld_pc == 211 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["novelFlag"]
if not (__pld_R[8] == true) then __pld_pc = 214 else __pld_pc = 215 end
elseif __pld_pc == 214 then
__pld_pc = 223
elseif __pld_pc == 215 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["music"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 218 else __pld_pc = 219 end
elseif __pld_pc == 218 then
__pld_pc = 231
elseif __pld_pc == 219 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["musicFlag"]
if __pld_R[8] == true then __pld_pc = 222 else __pld_pc = 223 end
elseif __pld_pc == 222 then
__pld_pc = 231
elseif __pld_pc == 223 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 253
elseif __pld_pc == 231 then
__pld_R[8] = layerAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = true
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 253
elseif __pld_pc == 253 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 190
else __pld_pc = 254 end end
elseif __pld_pc == 254 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_pc = 272
elseif __pld_pc == 258 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 261 else __pld_pc = 262 end
elseif __pld_pc == 261 then
__pld_pc = 266
elseif __pld_pc == 262 then
__pld_R[4] = systemOption
__pld_R[4] = __pld_R[4]["Option"]
__pld_R[4]()
__pld_pc = 272
elseif __pld_pc == 266 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["load"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 269 else __pld_pc = 270 end
elseif __pld_pc == 269 then
__pld_pc = 272
elseif __pld_pc == 270 then
__pld_R[4] = l0_7
__pld_R[4]()
__pld_pc = 272
elseif __pld_pc == 272 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey0"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey0"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 525
elseif __pld_pc == 291 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 295 else __pld_pc = 296 end
elseif __pld_pc == 295 then
__pld_pc = 323
elseif __pld_pc == 296 then
if not (__pld_R[2] == false) then __pld_pc = 297 else __pld_pc = 298 end
elseif __pld_pc == 297 then
__pld_pc = 323
elseif __pld_pc == 298 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["novel"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 307 else __pld_pc = 308 end
elseif __pld_pc == 307 then
__pld_pc = 312
elseif __pld_pc == 308 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 311 else __pld_pc = 312 end end
elseif __pld_pc == 311 then
__pld_pc = 313
elseif __pld_pc == 312 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 313
elseif __pld_pc == 313 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 316 else __pld_pc = 317 end
elseif __pld_pc == 316 then
__pld_pc = 322
elseif __pld_pc == 317 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 320 else __pld_pc = 321 end
elseif __pld_pc == 320 then
__pld_pc = 322
elseif __pld_pc == 321 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 322
elseif __pld_pc == 322 then
__pld_R[2] = true
__pld_pc = 323
elseif __pld_pc == 323 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 327 else __pld_pc = 328 end
elseif __pld_pc == 327 then
__pld_pc = 355
elseif __pld_pc == 328 then
if not (__pld_R[2] == false) then __pld_pc = 329 else __pld_pc = 330 end
elseif __pld_pc == 329 then
__pld_pc = 355
elseif __pld_pc == 330 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 339 else __pld_pc = 340 end
elseif __pld_pc == 339 then
__pld_pc = 344
elseif __pld_pc == 340 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 343 else __pld_pc = 344 end end
elseif __pld_pc == 343 then
__pld_pc = 345
elseif __pld_pc == 344 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 345
elseif __pld_pc == 345 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 348 else __pld_pc = 349 end
elseif __pld_pc == 348 then
__pld_pc = 354
elseif __pld_pc == 349 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["musicFlag"]
if __pld_R[4] == true then __pld_pc = 352 else __pld_pc = 353 end
elseif __pld_pc == 352 then
__pld_pc = 354
elseif __pld_pc == 353 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 354
elseif __pld_pc == 354 then
__pld_R[2] = true
__pld_pc = 355
elseif __pld_pc == 355 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 359 else __pld_pc = 360 end
elseif __pld_pc == 359 then
__pld_pc = 448
elseif __pld_pc == 360 then
if not (__pld_R[2] == false) then __pld_pc = 361 else __pld_pc = 362 end
elseif __pld_pc == 361 then
__pld_pc = 448
elseif __pld_pc == 362 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 372 else __pld_pc = 373 end
elseif __pld_pc == 372 then
__pld_pc = 389
elseif __pld_pc == 373 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_novel"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 448
elseif __pld_pc == 389 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["scene"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 392 else __pld_pc = 393 end
elseif __pld_pc == 392 then
__pld_pc = 409
elseif __pld_pc == 393 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_memory"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 448
elseif __pld_pc == 409 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["cg"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 412 else __pld_pc = 413 end
elseif __pld_pc == 412 then
__pld_pc = 429
elseif __pld_pc == 413 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_graphic"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 448
elseif __pld_pc == 429 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 432 else __pld_pc = 433 end
elseif __pld_pc == 432 then
__pld_pc = 448
elseif __pld_pc == 433 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_music"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 448
elseif __pld_pc == 448 then
__pld_R[4] = pressButton
__pld_R[5] = "CROSS"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 452 else __pld_pc = 453 end
elseif __pld_pc == 452 then
__pld_pc = 525
elseif __pld_pc == 453 then
if not (__pld_R[2] == false) then __pld_pc = 454 else __pld_pc = 455 end
elseif __pld_pc == 454 then
__pld_pc = 525
elseif __pld_pc == 455 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["cross"]
__pld_R[4](__pld_R[5])
__pld_R[3] = false
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["library"]
__pld_R[4] = 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 489
elseif __pld_pc == 468 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 471 else __pld_pc = 472 end
elseif __pld_pc == 471 then
__pld_pc = 481
elseif __pld_pc == 472 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 489
elseif __pld_pc == 481 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 489
elseif __pld_pc == 489 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 468
else __pld_pc = 490 end end
elseif __pld_pc == 490 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 506
elseif __pld_pc == 499 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 506
elseif __pld_pc == 506 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 499
else __pld_pc = 507 end end
elseif __pld_pc == 507 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey0"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey0"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 525
elseif __pld_pc == 525 then
if not (__pld_R[2] == true) then __pld_pc = 526 else __pld_pc = 527 end
elseif __pld_pc == 526 then
__pld_pc = 553
elseif __pld_pc == 527 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey0"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey0"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 3
__pld_R[4](__pld_R[5])
__pld_R[2] = false
__pld_pc = 553
elseif __pld_pc == 553 then
__pld_R[4] = wait
__pld_R[5] = 2
__pld_R[4](__pld_R[5])
__pld_pc = 22
elseif __pld_pc == 557 then
__pld_pc = 2182
elseif __pld_pc == 558 then
__pld_R[4] = gameSave
__pld_R[4] = __pld_R[4]["startMenuState"]
if not (__pld_R[4] == 1) then __pld_pc = 561 else __pld_pc = 562 end
elseif __pld_pc == 561 then
__pld_pc = 1103
elseif __pld_pc == 562 then
if not (__pld_R[3] == false) then __pld_pc = 563 else __pld_pc = 564 end
elseif __pld_pc == 563 then
__pld_pc = 836
elseif __pld_pc == 564 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 568 else __pld_pc = 569 end
elseif __pld_pc == 568 then
__pld_pc = 608
elseif __pld_pc == 569 then
if not (__pld_R[2] == false) then __pld_pc = 570 else __pld_pc = 571 end
elseif __pld_pc == 570 then
__pld_pc = 608
elseif __pld_pc == 571 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 575 else __pld_pc = 576 end
elseif __pld_pc == 575 then
__pld_pc = 579
elseif __pld_pc == 576 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["story"]
__pld_pc = 589
elseif __pld_pc == 579 then
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["story"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 583 else __pld_pc = 584 end
elseif __pld_pc == 583 then
__pld_pc = 588
elseif __pld_pc == 584 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["story"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 587 else __pld_pc = 588 end end
elseif __pld_pc == 587 then
__pld_pc = 589
elseif __pld_pc == 588 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 589
elseif __pld_pc == 589 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 592 else __pld_pc = 593 end
elseif __pld_pc == 592 then
__pld_pc = 607
elseif __pld_pc == 593 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["libFlag"]
if __pld_R[4] == true then __pld_pc = 596 else __pld_pc = 597 end
elseif __pld_pc == 596 then
__pld_pc = 607
elseif __pld_pc == 597 then
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["story"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 601 else __pld_pc = 602 end
elseif __pld_pc == 601 then
__pld_pc = 606
elseif __pld_pc == 602 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["story"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 605 else __pld_pc = 606 end end
elseif __pld_pc == 605 then
__pld_pc = 607
elseif __pld_pc == 606 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 607
elseif __pld_pc == 607 then
__pld_R[2] = true
__pld_pc = 608
elseif __pld_pc == 608 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 612 else __pld_pc = 613 end
elseif __pld_pc == 612 then
__pld_pc = 652
elseif __pld_pc == 613 then
if not (__pld_R[2] == false) then __pld_pc = 614 else __pld_pc = 615 end
elseif __pld_pc == 614 then
__pld_pc = 652
elseif __pld_pc == 615 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 619 else __pld_pc = 620 end
elseif __pld_pc == 619 then
__pld_pc = 623
elseif __pld_pc == 620 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["library"]
__pld_pc = 633
elseif __pld_pc == 623 then
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["option"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 627 else __pld_pc = 628 end
elseif __pld_pc == 627 then
__pld_pc = 632
elseif __pld_pc == 628 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 631 else __pld_pc = 632 end end
elseif __pld_pc == 631 then
__pld_pc = 633
elseif __pld_pc == 632 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 633
elseif __pld_pc == 633 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 636 else __pld_pc = 637 end
elseif __pld_pc == 636 then
__pld_pc = 651
elseif __pld_pc == 637 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["libFlag"]
if __pld_R[4] == true then __pld_pc = 640 else __pld_pc = 641 end
elseif __pld_pc == 640 then
__pld_pc = 651
elseif __pld_pc == 641 then
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["option"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 645 else __pld_pc = 646 end
elseif __pld_pc == 645 then
__pld_pc = 650
elseif __pld_pc == 646 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 649 else __pld_pc = 650 end end
elseif __pld_pc == 649 then
__pld_pc = 651
elseif __pld_pc == 650 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 651
elseif __pld_pc == 651 then
__pld_R[2] = true
__pld_pc = 652
elseif __pld_pc == 652 then
__pld_R[4] = pressButton
__pld_R[5] = "RIGHT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 656 else __pld_pc = 657 end
elseif __pld_pc == 656 then
__pld_pc = 663
elseif __pld_pc == 657 then
if not (__pld_R[2] == false) then __pld_pc = 658 else __pld_pc = 659 end
elseif __pld_pc == 658 then
__pld_pc = 663
elseif __pld_pc == 659 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["load"]
__pld_R[2] = true
__pld_pc = 663
elseif __pld_pc == 663 then
__pld_R[4] = pressButton
__pld_R[5] = "LEFT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 667 else __pld_pc = 668 end
elseif __pld_pc == 667 then
__pld_pc = 674
elseif __pld_pc == 668 then
if not (__pld_R[2] == false) then __pld_pc = 669 else __pld_pc = 670 end
elseif __pld_pc == 669 then
__pld_pc = 674
elseif __pld_pc == 670 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["save"]
__pld_R[2] = true
__pld_pc = 674
elseif __pld_pc == 674 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 678 else __pld_pc = 679 end
elseif __pld_pc == 678 then
__pld_pc = 1070
elseif __pld_pc == 679 then
if not (__pld_R[2] == false) then __pld_pc = 680 else __pld_pc = 681 end
elseif __pld_pc == 680 then
__pld_pc = 1070
elseif __pld_pc == 681 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["story"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 691 else __pld_pc = 692 end
elseif __pld_pc == 691 then
__pld_pc = 708
elseif __pld_pc == 692 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_story_main"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1070
elseif __pld_pc == 708 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 711 else __pld_pc = 712 end
elseif __pld_pc == 711 then
__pld_pc = 814
elseif __pld_pc == 712 then
__pld_R[3] = true
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 716 else __pld_pc = 717 end
elseif __pld_pc == 716 then
__pld_pc = 720
elseif __pld_pc == 717 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["scene"]
__pld_pc = 722
elseif __pld_pc == 720 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["novel"]
__pld_pc = 722
elseif __pld_pc == 722 then
__pld_R[4] = 1
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerKey1"]
__pld_R[5] = #(__pld_R[5])
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 791
elseif __pld_pc == 728 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 731 else __pld_pc = 732 end
elseif __pld_pc == 731 then
__pld_pc = 745
elseif __pld_pc == 732 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["library"]
if __pld_R[7] == __pld_R[8] then __pld_pc = 735 else __pld_pc = 736 end
elseif __pld_pc == 735 then
__pld_pc = 791
elseif __pld_pc == 736 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 50
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 791
elseif __pld_pc == 745 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 748 else __pld_pc = 749 end
elseif __pld_pc == 748 then
__pld_pc = 753
elseif __pld_pc == 749 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["novelFlag"]
if not (__pld_R[8] == true) then __pld_pc = 752 else __pld_pc = 753 end
elseif __pld_pc == 752 then
__pld_pc = 761
elseif __pld_pc == 753 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["music"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 756 else __pld_pc = 757 end
elseif __pld_pc == 756 then
__pld_pc = 769
elseif __pld_pc == 757 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["musicFlag"]
if __pld_R[8] == true then __pld_pc = 760 else __pld_pc = 761 end
elseif __pld_pc == 760 then
__pld_pc = 769
elseif __pld_pc == 761 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 791
elseif __pld_pc == 769 then
__pld_R[8] = layerAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = true
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 791
elseif __pld_pc == 791 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 728
else __pld_pc = 792 end end
elseif __pld_pc == 792 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey1"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey1"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 1070
elseif __pld_pc == 814 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 817 else __pld_pc = 818 end
elseif __pld_pc == 817 then
__pld_pc = 822
elseif __pld_pc == 818 then
__pld_R[4] = systemOption
__pld_R[4] = __pld_R[4]["Option"]
__pld_R[4]()
__pld_pc = 1070
elseif __pld_pc == 822 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["save"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 825 else __pld_pc = 826 end
elseif __pld_pc == 825 then
__pld_pc = 829
elseif __pld_pc == 826 then
__pld_R[4] = l0_8
__pld_R[4]()
__pld_pc = 1070
elseif __pld_pc == 829 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["load"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 832 else __pld_pc = 833 end
elseif __pld_pc == 832 then
__pld_pc = 1070
elseif __pld_pc == 833 then
__pld_R[4] = l0_7
__pld_R[4]()
__pld_pc = 1070
elseif __pld_pc == 836 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 840 else __pld_pc = 841 end
elseif __pld_pc == 840 then
__pld_pc = 868
elseif __pld_pc == 841 then
if not (__pld_R[2] == false) then __pld_pc = 842 else __pld_pc = 843 end
elseif __pld_pc == 842 then
__pld_pc = 868
elseif __pld_pc == 843 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["novel"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 852 else __pld_pc = 853 end
elseif __pld_pc == 852 then
__pld_pc = 857
elseif __pld_pc == 853 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 856 else __pld_pc = 857 end end
elseif __pld_pc == 856 then
__pld_pc = 858
elseif __pld_pc == 857 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 858
elseif __pld_pc == 858 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 861 else __pld_pc = 862 end
elseif __pld_pc == 861 then
__pld_pc = 867
elseif __pld_pc == 862 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 865 else __pld_pc = 866 end
elseif __pld_pc == 865 then
__pld_pc = 867
elseif __pld_pc == 866 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 867
elseif __pld_pc == 867 then
__pld_R[2] = true
__pld_pc = 868
elseif __pld_pc == 868 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 872 else __pld_pc = 873 end
elseif __pld_pc == 872 then
__pld_pc = 900
elseif __pld_pc == 873 then
if not (__pld_R[2] == false) then __pld_pc = 874 else __pld_pc = 875 end
elseif __pld_pc == 874 then
__pld_pc = 900
elseif __pld_pc == 875 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 884 else __pld_pc = 885 end
elseif __pld_pc == 884 then
__pld_pc = 889
elseif __pld_pc == 885 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 888 else __pld_pc = 889 end end
elseif __pld_pc == 888 then
__pld_pc = 890
elseif __pld_pc == 889 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 890
elseif __pld_pc == 890 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 893 else __pld_pc = 894 end
elseif __pld_pc == 893 then
__pld_pc = 899
elseif __pld_pc == 894 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["musicFlag"]
if __pld_R[4] == true then __pld_pc = 897 else __pld_pc = 898 end
elseif __pld_pc == 897 then
__pld_pc = 899
elseif __pld_pc == 898 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 899
elseif __pld_pc == 899 then
__pld_R[2] = true
__pld_pc = 900
elseif __pld_pc == 900 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 904 else __pld_pc = 905 end
elseif __pld_pc == 904 then
__pld_pc = 993
elseif __pld_pc == 905 then
if not (__pld_R[2] == false) then __pld_pc = 906 else __pld_pc = 907 end
elseif __pld_pc == 906 then
__pld_pc = 993
elseif __pld_pc == 907 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 917 else __pld_pc = 918 end
elseif __pld_pc == 917 then
__pld_pc = 934
elseif __pld_pc == 918 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_novel"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 993
elseif __pld_pc == 934 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["scene"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 937 else __pld_pc = 938 end
elseif __pld_pc == 937 then
__pld_pc = 954
elseif __pld_pc == 938 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_memory"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 993
elseif __pld_pc == 954 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["cg"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 957 else __pld_pc = 958 end
elseif __pld_pc == 957 then
__pld_pc = 974
elseif __pld_pc == 958 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_graphic"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 993
elseif __pld_pc == 974 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 977 else __pld_pc = 978 end
elseif __pld_pc == 977 then
__pld_pc = 993
elseif __pld_pc == 978 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_music"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 993
elseif __pld_pc == 993 then
__pld_R[4] = pressButton
__pld_R[5] = "CROSS"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 997 else __pld_pc = 998 end
elseif __pld_pc == 997 then
__pld_pc = 1070
elseif __pld_pc == 998 then
if not (__pld_R[2] == false) then __pld_pc = 999 else __pld_pc = 1000 end
elseif __pld_pc == 999 then
__pld_pc = 1070
elseif __pld_pc == 1000 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["cross"]
__pld_R[4](__pld_R[5])
__pld_R[3] = false
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["library"]
__pld_R[4] = 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 1034
elseif __pld_pc == 1013 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 1016 else __pld_pc = 1017 end
elseif __pld_pc == 1016 then
__pld_pc = 1026
elseif __pld_pc == 1017 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1034
elseif __pld_pc == 1026 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1034
elseif __pld_pc == 1034 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 1013
else __pld_pc = 1035 end end
elseif __pld_pc == 1035 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 1051
elseif __pld_pc == 1044 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 1051
elseif __pld_pc == 1051 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 1044
else __pld_pc = 1052 end end
elseif __pld_pc == 1052 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey1"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey1"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 1070
elseif __pld_pc == 1070 then
if not (__pld_R[2] == true) then __pld_pc = 1071 else __pld_pc = 1072 end
elseif __pld_pc == 1071 then
__pld_pc = 1098
elseif __pld_pc == 1072 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey1"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey1"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 3
__pld_R[4](__pld_R[5])
__pld_R[2] = false
__pld_pc = 1098
elseif __pld_pc == 1098 then
__pld_R[4] = wait
__pld_R[5] = 2
__pld_R[4](__pld_R[5])
__pld_pc = 562
elseif __pld_pc == 1102 then
__pld_pc = 2182
elseif __pld_pc == 1103 then
__pld_R[4] = gameSave
__pld_R[4] = __pld_R[4]["startMenuState"]
if not (__pld_R[4] == 2) then __pld_pc = 1106 else __pld_pc = 1107 end
elseif __pld_pc == 1106 then
__pld_pc = 2182
elseif __pld_pc == 1107 then
__pld_R[4] = gameSave
__pld_R[4] = __pld_R[4]["myCard"]
__pld_R[4] = __pld_R[4][140]
__pld_R[4] = __pld_R[4]["hold"]
if not (__pld_R[4] == (-1)) then __pld_pc = 1112 else __pld_pc = 1113 end
elseif __pld_pc == 1112 then
__pld_pc = 1638
elseif __pld_pc == 1113 then
if not (__pld_R[3] == false) then __pld_pc = 1114 else __pld_pc = 1115 end
elseif __pld_pc == 1114 then
__pld_pc = 1371
elseif __pld_pc == 1115 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1119 else __pld_pc = 1120 end
elseif __pld_pc == 1119 then
__pld_pc = 1141
elseif __pld_pc == 1120 then
if not (__pld_R[2] == false) then __pld_pc = 1121 else __pld_pc = 1122 end
elseif __pld_pc == 1121 then
__pld_pc = 1141
elseif __pld_pc == 1122 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 1126 else __pld_pc = 1127 end
elseif __pld_pc == 1126 then
__pld_pc = 1130
elseif __pld_pc == 1127 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["story"]
__pld_pc = 1140
elseif __pld_pc == 1130 then
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["story"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 1134 else __pld_pc = 1135 end
elseif __pld_pc == 1134 then
__pld_pc = 1139
elseif __pld_pc == 1135 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["story"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1138 else __pld_pc = 1139 end end
elseif __pld_pc == 1138 then
__pld_pc = 1140
elseif __pld_pc == 1139 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 1140
elseif __pld_pc == 1140 then
__pld_R[2] = true
__pld_pc = 1141
elseif __pld_pc == 1141 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1145 else __pld_pc = 1146 end
elseif __pld_pc == 1145 then
__pld_pc = 1167
elseif __pld_pc == 1146 then
if not (__pld_R[2] == false) then __pld_pc = 1147 else __pld_pc = 1148 end
elseif __pld_pc == 1147 then
__pld_pc = 1167
elseif __pld_pc == 1148 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 1152 else __pld_pc = 1153 end
elseif __pld_pc == 1152 then
__pld_pc = 1156
elseif __pld_pc == 1153 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["fragment"]
__pld_pc = 1166
elseif __pld_pc == 1156 then
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["option"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 1160 else __pld_pc = 1161 end
elseif __pld_pc == 1160 then
__pld_pc = 1165
elseif __pld_pc == 1161 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1164 else __pld_pc = 1165 end end
elseif __pld_pc == 1164 then
__pld_pc = 1166
elseif __pld_pc == 1165 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 1166
elseif __pld_pc == 1166 then
__pld_R[2] = true
__pld_pc = 1167
elseif __pld_pc == 1167 then
__pld_R[4] = pressButton
__pld_R[5] = "RIGHT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1171 else __pld_pc = 1172 end
elseif __pld_pc == 1171 then
__pld_pc = 1178
elseif __pld_pc == 1172 then
if not (__pld_R[2] == false) then __pld_pc = 1173 else __pld_pc = 1174 end
elseif __pld_pc == 1173 then
__pld_pc = 1178
elseif __pld_pc == 1174 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["load"]
__pld_R[2] = true
__pld_pc = 1178
elseif __pld_pc == 1178 then
__pld_R[4] = pressButton
__pld_R[5] = "LEFT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1182 else __pld_pc = 1183 end
elseif __pld_pc == 1182 then
__pld_pc = 1189
elseif __pld_pc == 1183 then
if not (__pld_R[2] == false) then __pld_pc = 1184 else __pld_pc = 1185 end
elseif __pld_pc == 1184 then
__pld_pc = 1189
elseif __pld_pc == 1185 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["save"]
__pld_R[2] = true
__pld_pc = 1189
elseif __pld_pc == 1189 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1193 else __pld_pc = 1194 end
elseif __pld_pc == 1193 then
__pld_pc = 1605
elseif __pld_pc == 1194 then
if not (__pld_R[2] == false) then __pld_pc = 1195 else __pld_pc = 1196 end
elseif __pld_pc == 1195 then
__pld_pc = 1605
elseif __pld_pc == 1196 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["story"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1206 else __pld_pc = 1207 end
elseif __pld_pc == 1206 then
__pld_pc = 1223
elseif __pld_pc == 1207 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_story_main"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1605
elseif __pld_pc == 1223 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["fragment"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1226 else __pld_pc = 1227 end
elseif __pld_pc == 1226 then
__pld_pc = 1243
elseif __pld_pc == 1227 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_fragment_main"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1605
elseif __pld_pc == 1243 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1246 else __pld_pc = 1247 end
elseif __pld_pc == 1246 then
__pld_pc = 1349
elseif __pld_pc == 1247 then
__pld_R[3] = true
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 1251 else __pld_pc = 1252 end
elseif __pld_pc == 1251 then
__pld_pc = 1255
elseif __pld_pc == 1252 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["scene"]
__pld_pc = 1257
elseif __pld_pc == 1255 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["novel"]
__pld_pc = 1257
elseif __pld_pc == 1257 then
__pld_R[4] = 1
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerKey2"]
__pld_R[5] = #(__pld_R[5])
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 1326
elseif __pld_pc == 1263 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 1266 else __pld_pc = 1267 end
elseif __pld_pc == 1266 then
__pld_pc = 1280
elseif __pld_pc == 1267 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["library"]
if __pld_R[7] == __pld_R[8] then __pld_pc = 1270 else __pld_pc = 1271 end
elseif __pld_pc == 1270 then
__pld_pc = 1326
elseif __pld_pc == 1271 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 50
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1326
elseif __pld_pc == 1280 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 1283 else __pld_pc = 1284 end
elseif __pld_pc == 1283 then
__pld_pc = 1288
elseif __pld_pc == 1284 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["novelFlag"]
if not (__pld_R[8] == true) then __pld_pc = 1287 else __pld_pc = 1288 end
elseif __pld_pc == 1287 then
__pld_pc = 1296
elseif __pld_pc == 1288 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["music"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 1291 else __pld_pc = 1292 end
elseif __pld_pc == 1291 then
__pld_pc = 1304
elseif __pld_pc == 1292 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["musicFlag"]
if __pld_R[8] == true then __pld_pc = 1295 else __pld_pc = 1296 end
elseif __pld_pc == 1295 then
__pld_pc = 1304
elseif __pld_pc == 1296 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 1326
elseif __pld_pc == 1304 then
__pld_R[8] = layerAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = true
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1326
elseif __pld_pc == 1326 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 1263
else __pld_pc = 1327 end end
elseif __pld_pc == 1327 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey2"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey2"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 1605
elseif __pld_pc == 1349 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1352 else __pld_pc = 1353 end
elseif __pld_pc == 1352 then
__pld_pc = 1357
elseif __pld_pc == 1353 then
__pld_R[4] = systemOption
__pld_R[4] = __pld_R[4]["Option"]
__pld_R[4]()
__pld_pc = 1605
elseif __pld_pc == 1357 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["save"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1360 else __pld_pc = 1361 end
elseif __pld_pc == 1360 then
__pld_pc = 1364
elseif __pld_pc == 1361 then
__pld_R[4] = l0_8
__pld_R[4]()
__pld_pc = 1605
elseif __pld_pc == 1364 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["load"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1367 else __pld_pc = 1368 end
elseif __pld_pc == 1367 then
__pld_pc = 1605
elseif __pld_pc == 1368 then
__pld_R[4] = l0_7
__pld_R[4]()
__pld_pc = 1605
elseif __pld_pc == 1371 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1375 else __pld_pc = 1376 end
elseif __pld_pc == 1375 then
__pld_pc = 1403
elseif __pld_pc == 1376 then
if not (__pld_R[2] == false) then __pld_pc = 1377 else __pld_pc = 1378 end
elseif __pld_pc == 1377 then
__pld_pc = 1403
elseif __pld_pc == 1378 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["novel"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 1387 else __pld_pc = 1388 end
elseif __pld_pc == 1387 then
__pld_pc = 1392
elseif __pld_pc == 1388 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1391 else __pld_pc = 1392 end end
elseif __pld_pc == 1391 then
__pld_pc = 1393
elseif __pld_pc == 1392 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 1393
elseif __pld_pc == 1393 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1396 else __pld_pc = 1397 end
elseif __pld_pc == 1396 then
__pld_pc = 1402
elseif __pld_pc == 1397 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 1400 else __pld_pc = 1401 end
elseif __pld_pc == 1400 then
__pld_pc = 1402
elseif __pld_pc == 1401 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 1402
elseif __pld_pc == 1402 then
__pld_R[2] = true
__pld_pc = 1403
elseif __pld_pc == 1403 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1407 else __pld_pc = 1408 end
elseif __pld_pc == 1407 then
__pld_pc = 1435
elseif __pld_pc == 1408 then
if not (__pld_R[2] == false) then __pld_pc = 1409 else __pld_pc = 1410 end
elseif __pld_pc == 1409 then
__pld_pc = 1435
elseif __pld_pc == 1410 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 1419 else __pld_pc = 1420 end
elseif __pld_pc == 1419 then
__pld_pc = 1424
elseif __pld_pc == 1420 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1423 else __pld_pc = 1424 end end
elseif __pld_pc == 1423 then
__pld_pc = 1425
elseif __pld_pc == 1424 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 1425
elseif __pld_pc == 1425 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1428 else __pld_pc = 1429 end
elseif __pld_pc == 1428 then
__pld_pc = 1434
elseif __pld_pc == 1429 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["musicFlag"]
if __pld_R[4] == true then __pld_pc = 1432 else __pld_pc = 1433 end
elseif __pld_pc == 1432 then
__pld_pc = 1434
elseif __pld_pc == 1433 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 1434
elseif __pld_pc == 1434 then
__pld_R[2] = true
__pld_pc = 1435
elseif __pld_pc == 1435 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1439 else __pld_pc = 1440 end
elseif __pld_pc == 1439 then
__pld_pc = 1528
elseif __pld_pc == 1440 then
if not (__pld_R[2] == false) then __pld_pc = 1441 else __pld_pc = 1442 end
elseif __pld_pc == 1441 then
__pld_pc = 1528
elseif __pld_pc == 1442 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1452 else __pld_pc = 1453 end
elseif __pld_pc == 1452 then
__pld_pc = 1469
elseif __pld_pc == 1453 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_novel"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1528
elseif __pld_pc == 1469 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["scene"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1472 else __pld_pc = 1473 end
elseif __pld_pc == 1472 then
__pld_pc = 1489
elseif __pld_pc == 1473 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_memory"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1528
elseif __pld_pc == 1489 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["cg"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1492 else __pld_pc = 1493 end
elseif __pld_pc == 1492 then
__pld_pc = 1509
elseif __pld_pc == 1493 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_graphic"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1528
elseif __pld_pc == 1509 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1512 else __pld_pc = 1513 end
elseif __pld_pc == 1512 then
__pld_pc = 1528
elseif __pld_pc == 1513 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_music"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1528
elseif __pld_pc == 1528 then
__pld_R[4] = pressButton
__pld_R[5] = "CROSS"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1532 else __pld_pc = 1533 end
elseif __pld_pc == 1532 then
__pld_pc = 1605
elseif __pld_pc == 1533 then
if not (__pld_R[2] == false) then __pld_pc = 1534 else __pld_pc = 1535 end
elseif __pld_pc == 1534 then
__pld_pc = 1605
elseif __pld_pc == 1535 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["cross"]
__pld_R[4](__pld_R[5])
__pld_R[3] = false
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["library"]
__pld_R[4] = 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 1569
elseif __pld_pc == 1548 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 1551 else __pld_pc = 1552 end
elseif __pld_pc == 1551 then
__pld_pc = 1561
elseif __pld_pc == 1552 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1569
elseif __pld_pc == 1561 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1569
elseif __pld_pc == 1569 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 1548
else __pld_pc = 1570 end end
elseif __pld_pc == 1570 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 1586
elseif __pld_pc == 1579 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 1586
elseif __pld_pc == 1586 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 1579
else __pld_pc = 1587 end end
elseif __pld_pc == 1587 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey2"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey2"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 1605
elseif __pld_pc == 1605 then
if not (__pld_R[2] == true) then __pld_pc = 1606 else __pld_pc = 1607 end
elseif __pld_pc == 1606 then
__pld_pc = 1633
elseif __pld_pc == 1607 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey2"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey2"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 3
__pld_R[4](__pld_R[5])
__pld_R[2] = false
__pld_pc = 1633
elseif __pld_pc == 1633 then
__pld_R[4] = wait
__pld_R[5] = 2
__pld_R[4](__pld_R[5])
__pld_pc = 1113
elseif __pld_pc == 1637 then
__pld_pc = 2182
elseif __pld_pc == 1638 then
if not (__pld_R[3] == false) then __pld_pc = 1639 else __pld_pc = 1640 end
elseif __pld_pc == 1639 then
__pld_pc = 1916
elseif __pld_pc == 1640 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1644 else __pld_pc = 1645 end
elseif __pld_pc == 1644 then
__pld_pc = 1666
elseif __pld_pc == 1645 then
if not (__pld_R[2] == false) then __pld_pc = 1646 else __pld_pc = 1647 end
elseif __pld_pc == 1646 then
__pld_pc = 1666
elseif __pld_pc == 1647 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 1651 else __pld_pc = 1652 end
elseif __pld_pc == 1651 then
__pld_pc = 1655
elseif __pld_pc == 1652 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["story"]
__pld_pc = 1665
elseif __pld_pc == 1655 then
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["story"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 1659 else __pld_pc = 1660 end
elseif __pld_pc == 1659 then
__pld_pc = 1664
elseif __pld_pc == 1660 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["story"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1663 else __pld_pc = 1664 end end
elseif __pld_pc == 1663 then
__pld_pc = 1665
elseif __pld_pc == 1664 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 1665
elseif __pld_pc == 1665 then
__pld_R[2] = true
__pld_pc = 1666
elseif __pld_pc == 1666 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1670 else __pld_pc = 1671 end
elseif __pld_pc == 1670 then
__pld_pc = 1692
elseif __pld_pc == 1671 then
if not (__pld_R[2] == false) then __pld_pc = 1672 else __pld_pc = 1673 end
elseif __pld_pc == 1672 then
__pld_pc = 1692
elseif __pld_pc == 1673 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[4] < __pld_R[0]) then __pld_pc = 1677 else __pld_pc = 1678 end
elseif __pld_pc == 1677 then
__pld_pc = 1681
elseif __pld_pc == 1678 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["fragment"]
__pld_pc = 1691
elseif __pld_pc == 1681 then
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["option"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 1685 else __pld_pc = 1686 end
elseif __pld_pc == 1685 then
__pld_pc = 1690
elseif __pld_pc == 1686 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1689 else __pld_pc = 1690 end end
elseif __pld_pc == 1689 then
__pld_pc = 1691
elseif __pld_pc == 1690 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 1691
elseif __pld_pc == 1691 then
__pld_R[2] = true
__pld_pc = 1692
elseif __pld_pc == 1692 then
__pld_R[4] = pressButton
__pld_R[5] = "RIGHT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1696 else __pld_pc = 1697 end
elseif __pld_pc == 1696 then
__pld_pc = 1703
elseif __pld_pc == 1697 then
if not (__pld_R[2] == false) then __pld_pc = 1698 else __pld_pc = 1699 end
elseif __pld_pc == 1698 then
__pld_pc = 1703
elseif __pld_pc == 1699 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["load"]
__pld_R[2] = true
__pld_pc = 1703
elseif __pld_pc == 1703 then
__pld_R[4] = pressButton
__pld_R[5] = "LEFT"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1707 else __pld_pc = 1708 end
elseif __pld_pc == 1707 then
__pld_pc = 1714
elseif __pld_pc == 1708 then
if not (__pld_R[2] == false) then __pld_pc = 1709 else __pld_pc = 1710 end
elseif __pld_pc == 1709 then
__pld_pc = 1714
elseif __pld_pc == 1710 then
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["save"]
__pld_R[2] = true
__pld_pc = 1714
elseif __pld_pc == 1714 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1718 else __pld_pc = 1719 end
elseif __pld_pc == 1718 then
__pld_pc = 2150
elseif __pld_pc == 1719 then
if not (__pld_R[2] == false) then __pld_pc = 1720 else __pld_pc = 1721 end
elseif __pld_pc == 1720 then
__pld_pc = 2150
elseif __pld_pc == 1721 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["story"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1731 else __pld_pc = 1732 end
elseif __pld_pc == 1731 then
__pld_pc = 1748
elseif __pld_pc == 1732 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_story_main"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1897
elseif __pld_pc == 1748 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["fragment"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1751 else __pld_pc = 1752 end
elseif __pld_pc == 1751 then
__pld_pc = 1768
elseif __pld_pc == 1752 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_fragment_main"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1897
elseif __pld_pc == 1768 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["section7"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1771 else __pld_pc = 1772 end
elseif __pld_pc == 1771 then
__pld_pc = 1790
elseif __pld_pc == 1772 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = "s7f-10"
doScriptScene = __pld_R[4]
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_s7_10_f"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 1897
elseif __pld_pc == 1790 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["library"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1793 else __pld_pc = 1794 end
elseif __pld_pc == 1793 then
__pld_pc = 1876
elseif __pld_pc == 1794 then
__pld_R[3] = true
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 1798 else __pld_pc = 1799 end
elseif __pld_pc == 1798 then
__pld_pc = 1802
elseif __pld_pc == 1799 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["scene"]
__pld_pc = 1804
elseif __pld_pc == 1802 then
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["novel"]
__pld_pc = 1804
elseif __pld_pc == 1804 then
__pld_R[4] = 1
__pld_R[5] = 11
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 1871
elseif __pld_pc == 1808 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 1811 else __pld_pc = 1812 end
elseif __pld_pc == 1811 then
__pld_pc = 1825
elseif __pld_pc == 1812 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["library"]
if __pld_R[7] == __pld_R[8] then __pld_pc = 1815 else __pld_pc = 1816 end
elseif __pld_pc == 1815 then
__pld_pc = 1871
elseif __pld_pc == 1816 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 50
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1871
elseif __pld_pc == 1825 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 1828 else __pld_pc = 1829 end
elseif __pld_pc == 1828 then
__pld_pc = 1833
elseif __pld_pc == 1829 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["novelFlag"]
if not (__pld_R[8] == true) then __pld_pc = 1832 else __pld_pc = 1833 end
elseif __pld_pc == 1832 then
__pld_pc = 1841
elseif __pld_pc == 1833 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["music"]
if not (__pld_R[7] == __pld_R[8]) then __pld_pc = 1836 else __pld_pc = 1837 end
elseif __pld_pc == 1836 then
__pld_pc = 1849
elseif __pld_pc == 1837 then
__pld_R[8] = systemSave
__pld_R[8] = __pld_R[8]["musicFlag"]
if __pld_R[8] == true then __pld_pc = 1840 else __pld_pc = 1841 end
elseif __pld_pc == 1840 then
__pld_pc = 1849
elseif __pld_pc == 1841 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 1871
elseif __pld_pc == 1849 then
__pld_R[8] = layerAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = true
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 1871
elseif __pld_pc == 1871 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 1808
else __pld_pc = 1872 end end
elseif __pld_pc == 1872 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_pc = 1897
elseif __pld_pc == 1876 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["option"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1879 else __pld_pc = 1880 end
elseif __pld_pc == 1879 then
__pld_pc = 1884
elseif __pld_pc == 1880 then
__pld_R[4] = systemOption
__pld_R[4] = __pld_R[4]["Option"]
__pld_R[4]()
__pld_pc = 1897
elseif __pld_pc == 1884 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["save"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1887 else __pld_pc = 1888 end
elseif __pld_pc == 1887 then
__pld_pc = 1891
elseif __pld_pc == 1888 then
__pld_R[4] = l0_8
__pld_R[4]()
__pld_pc = 1897
elseif __pld_pc == 1891 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["load"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1894 else __pld_pc = 1895 end
elseif __pld_pc == 1894 then
__pld_pc = 1897
elseif __pld_pc == 1895 then
__pld_R[4] = l0_7
__pld_R[4]()
__pld_pc = 1897
elseif __pld_pc == 1897 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey3"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey3"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 2150
elseif __pld_pc == 1916 then
__pld_R[4] = pressButton
__pld_R[5] = "UP"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1920 else __pld_pc = 1921 end
elseif __pld_pc == 1920 then
__pld_pc = 1948
elseif __pld_pc == 1921 then
if not (__pld_R[2] == false) then __pld_pc = 1922 else __pld_pc = 1923 end
elseif __pld_pc == 1922 then
__pld_pc = 1948
elseif __pld_pc == 1923 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] - 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["novel"]
if not (__pld_R[4] < __pld_R[5]) then __pld_pc = 1932 else __pld_pc = 1933 end
elseif __pld_pc == 1932 then
__pld_pc = 1937
elseif __pld_pc == 1933 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1936 else __pld_pc = 1937 end end
elseif __pld_pc == 1936 then
__pld_pc = 1938
elseif __pld_pc == 1937 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 1938
elseif __pld_pc == 1938 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1941 else __pld_pc = 1942 end
elseif __pld_pc == 1941 then
__pld_pc = 1947
elseif __pld_pc == 1942 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["novelFlag"]
if __pld_R[4] == true then __pld_pc = 1945 else __pld_pc = 1946 end
elseif __pld_pc == 1945 then
__pld_pc = 1947
elseif __pld_pc == 1946 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 1947
elseif __pld_pc == 1947 then
__pld_R[2] = true
__pld_pc = 1948
elseif __pld_pc == 1948 then
__pld_R[4] = pressButton
__pld_R[5] = "DOWN"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1952 else __pld_pc = 1953 end
elseif __pld_pc == 1952 then
__pld_pc = 1980
elseif __pld_pc == 1953 then
if not (__pld_R[2] == false) then __pld_pc = 1954 else __pld_pc = 1955 end
elseif __pld_pc == 1954 then
__pld_pc = 1980
elseif __pld_pc == 1955 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[1] = __pld_R[0]
__pld_R[4] = __pld_R[0] + 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
if not (__pld_R[5] < __pld_R[4]) then __pld_pc = 1964 else __pld_pc = 1965 end
elseif __pld_pc == 1964 then
__pld_pc = 1969
elseif __pld_pc == 1965 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
do local __pld_t = __pld_R[4] if __pld_t then __pld_R[0] = __pld_t __pld_pc = 1968 else __pld_pc = 1969 end end
elseif __pld_pc == 1968 then
__pld_pc = 1970
elseif __pld_pc == 1969 then
__pld_R[0] = __pld_R[0] + 1
__pld_pc = 1970
elseif __pld_pc == 1970 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1973 else __pld_pc = 1974 end
elseif __pld_pc == 1973 then
__pld_pc = 1979
elseif __pld_pc == 1974 then
__pld_R[4] = systemSave
__pld_R[4] = __pld_R[4]["musicFlag"]
if __pld_R[4] == true then __pld_pc = 1977 else __pld_pc = 1978 end
elseif __pld_pc == 1977 then
__pld_pc = 1979
elseif __pld_pc == 1978 then
__pld_R[0] = __pld_R[0] - 1
__pld_pc = 1979
elseif __pld_pc == 1979 then
__pld_R[2] = true
__pld_pc = 1980
elseif __pld_pc == 1980 then
__pld_R[4] = pressButton
__pld_R[5] = "CIRCLE"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 1984 else __pld_pc = 1985 end
elseif __pld_pc == 1984 then
__pld_pc = 2073
elseif __pld_pc == 1985 then
if not (__pld_R[2] == false) then __pld_pc = 1986 else __pld_pc = 1987 end
elseif __pld_pc == 1986 then
__pld_pc = 2073
elseif __pld_pc == 1987 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["circle"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 10
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 1997 else __pld_pc = 1998 end
elseif __pld_pc == 1997 then
__pld_pc = 2014
elseif __pld_pc == 1998 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_novel"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 2073
elseif __pld_pc == 2014 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["scene"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 2017 else __pld_pc = 2018 end
elseif __pld_pc == 2017 then
__pld_pc = 2034
elseif __pld_pc == 2018 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_memory"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 2073
elseif __pld_pc == 2034 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["cg"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 2037 else __pld_pc = 2038 end
elseif __pld_pc == 2037 then
__pld_pc = 2054
elseif __pld_pc == 2038 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_graphic"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 2073
elseif __pld_pc == 2054 then
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["music"]
if not (__pld_R[0] == __pld_R[4]) then __pld_pc = 2057 else __pld_pc = 2058 end
elseif __pld_pc == 2057 then
__pld_pc = 2073
elseif __pld_pc == 2058 then
__pld_R[4] = cInitGame
__pld_R[4]()
__pld_R[4] = switchScreen
__pld_R[5] = 0
__pld_R[6] = ""
__pld_R[7] = 60
__pld_R[4](__pld_R[5], __pld_R[6], __pld_R[7])
__pld_R[4] = run
__pld_R[5] = cGetFileName
__pld_R[6] = "script"
__pld_R[7] = "snr_music"
do 
local __pld_rs = __pld_pack(__pld_R[5](__pld_R[6], __pld_R[7]))
for __pld_i = 1, __pld_rs.n do __pld_set(__pld_R, __pld_B, 5 + __pld_i - 1, __pld_rs[__pld_i]) end
__pld_top = 5 + __pld_rs.n end
do local __pld_t, __pld_n = {}, __pld_top - 5 for __pld_i = 1, __pld_n do __pld_t[__pld_i] = __pld_get(__pld_R, __pld_B, 5 + __pld_i - 1) end __pld_R[4](__pld_unpack(__pld_t, 1, __pld_n)) end
__pld_R[4] = quit
__pld_R[4]()
__pld_pc = 2073
elseif __pld_pc == 2073 then
__pld_R[4] = pressButton
__pld_R[5] = "CROSS"
__pld_R[4] = __pld_R[4](__pld_R[5])
if not (__pld_R[4] == true) then __pld_pc = 2077 else __pld_pc = 2078 end
elseif __pld_pc == 2077 then
__pld_pc = 2150
elseif __pld_pc == 2078 then
if not (__pld_R[2] == false) then __pld_pc = 2079 else __pld_pc = 2080 end
elseif __pld_pc == 2079 then
__pld_pc = 2150
elseif __pld_pc == 2080 then
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["cross"]
__pld_R[4](__pld_R[5])
__pld_R[3] = false
__pld_R[1] = __pld_R[0]
__pld_R[4] = l0_1
__pld_R[0] = __pld_R[4]["library"]
__pld_R[4] = 1
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 2114
elseif __pld_pc == 2093 then
__pld_R[8] = l0_1
__pld_R[8] = __pld_R[8]["novel"]
if not (__pld_R[7] < __pld_R[8]) then __pld_pc = 2096 else __pld_pc = 2097 end
elseif __pld_pc == 2096 then
__pld_pc = 2106
elseif __pld_pc == 2097 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 100
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 2114
elseif __pld_pc == 2106 then
__pld_R[8] = layerMoveAlpha
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = 0
__pld_R[11] = 30
__pld_R[8](__pld_R[9], __pld_R[10], __pld_R[11])
__pld_pc = 2114
elseif __pld_pc == 2114 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 2093
else __pld_pc = 2115 end end
elseif __pld_pc == 2115 then
__pld_R[4] = wait
__pld_R[5] = 30
__pld_R[4](__pld_R[5])
__pld_R[4] = l0_1
__pld_R[4] = __pld_R[4]["novel"]
__pld_R[5] = l0_1
__pld_R[5] = __pld_R[5]["music"]
__pld_R[6] = 1
do
local __pld_i = __pld_tonumber(__pld_R[4]) if __pld_i == nil then __pld_error("'for' initial value must be a number") end
local __pld_l = __pld_tonumber(__pld_R[5]) if __pld_l == nil then __pld_error("'for' limit must be a number") end
local __pld_s = __pld_tonumber(__pld_R[6]) if __pld_s == nil then __pld_error("'for' step must be a number") end
__pld_R[4] = __pld_i - __pld_s __pld_R[5] = __pld_l __pld_R[6] = __pld_s
end
__pld_pc = 2131
elseif __pld_pc == 2124 then
__pld_R[8] = layerVisible
__pld_R[9] = l0_0
__pld_R[9] = __pld_R[9]["layerNumber"]
__pld_R[9] = __pld_R[9]["menu"]
__pld_R[9] = __pld_R[9] + __pld_R[7]
__pld_R[10] = false
__pld_R[8](__pld_R[9], __pld_R[10])
__pld_pc = 2131
elseif __pld_pc == 2131 then
do local __pld_s = __pld_R[6] local __pld_i = __pld_R[4] + __pld_s
if (__pld_s > 0 and __pld_i <= __pld_R[5]) or (__pld_s <= 0 and __pld_i >= __pld_R[5]) then
__pld_R[4] = __pld_i __pld_R[7] = __pld_i __pld_pc = 2124
else __pld_pc = 2132 end end
elseif __pld_pc == 2132 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey3"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey3"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_pc = 2150
elseif __pld_pc == 2150 then
if not (__pld_R[2] == true) then __pld_pc = 2151 else __pld_pc = 2152 end
elseif __pld_pc == 2151 then
__pld_pc = 2178
elseif __pld_pc == 2152 then
__pld_R[4] = l0_2
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[1]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey3"]
__pld_R[6] = __pld_R[6][__pld_R[1]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = l0_3
__pld_R[5] = l0_0
__pld_R[5] = __pld_R[5]["layerNumber"]
__pld_R[5] = __pld_R[5]["menu"]
__pld_R[5] = __pld_R[5] + __pld_R[0]
__pld_R[6] = l0_0
__pld_R[6] = __pld_R[6]["layerKey3"]
__pld_R[6] = __pld_R[6][__pld_R[0]]
__pld_R[4](__pld_R[5], __pld_R[6])
__pld_R[4] = keyPlaySE
__pld_R[5] = seName
__pld_R[5] = __pld_R[5]["arrowKey"]
__pld_R[4](__pld_R[5])
__pld_R[4] = wait
__pld_R[5] = 3
__pld_R[4](__pld_R[5])
__pld_R[2] = false
__pld_pc = 2178
elseif __pld_pc == 2178 then
__pld_R[4] = wait
__pld_R[5] = 2
__pld_R[4](__pld_R[5])
__pld_pc = 1638
elseif __pld_pc == 2182 then
return
else __pld_error("pyluadec fallback: invalid pc") end
end
end

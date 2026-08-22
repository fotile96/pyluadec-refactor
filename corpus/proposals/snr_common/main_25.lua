return function()
local l1_0 = {layerNo = layerName.hour1, layerNo2 = layerName.hour2}
l1_0.setHourGlassCount2FileName = function(l2_0)
    local l2_1 = 0
    local l2_2 = 0
    if l2_0 >= 100 then
        l2_1 = 240
        l2_2 = 60
    elseif l2_0 >= 90 then
        l2_1 = 180
        l2_2 = 60
    elseif l2_0 >= 80 then
        l2_1 = 120
        l2_2 = 60
    elseif l2_0 >= 70 then
        l2_1 = 60
        l2_2 = 60
    elseif 60 <= l2_0 then
        l2_1 = 0
        l2_2 = 60
    elseif l2_0 >= 50 then
        l2_1 = 240
        l2_2 = 0
    elseif l2_0 >= 40 then
        l2_1 = 180
        l2_2 = 0
    elseif l2_0 >= 30 then
        l2_1 = 120
        l2_2 = 0
    elseif l2_0 >= 20 then
        l2_1 = 60
        l2_2 = 0
    elseif l2_0 >= 10 then
        l2_1 = 0
        l2_2 = 0
    end
    return l2_1, l2_2
end
l1_0.hourGlassStageIn = function(l2_0)
    local l2_1, l2_2 = l1_0.setHourGlassCount2FileName(l2_0)
    layerCopy(l1_0.layerNo, layerName.sys_4_a)
    layerClip(l1_0.layerNo, l2_1, l2_2, l2_1 + 60, l2_2 + 60)
    layerAnime(l1_0.layerNo, 4, true)
    layerAlpha(l1_0.layerNo, 0)
    layerPosition(l1_0.layerNo, 520, -30)
    layerMovePosition(l1_0.layerNo, 400, 10, 30)
    layerMoveAlpha(l1_0.layerNo, 100, 30)
    wait(30)
end
l1_0.hourGlassStageOut = function(l2_0)
    layerMovePosition(l1_0.layerNo, -50, -50, 30)
    layerMoveAlpha(l1_0.layerNo, 0, 30)
    wait(30)
    layerLoad(l1_0.layerNo, "")
    switchScreen(0, "", 30)
    wait(10)
end
l1_0.hourGlassStageCngTo = function(l2_0, l2_1)
    local l2_2, l2_3 = l1_0.setHourGlassCount2FileName(l2_1)
    local l2_4, l2_5 = l1_0.setHourGlassCount2FileName(l2_0)
    layerCopy(l1_0.layerNo2, layerName.sys_4_a)
    layerClip(l1_0.layerNo2, l2_4, l2_5, l2_4 + 60, l2_5 + 60)
    layerAlpha(l1_0.layerNo2, 100)
    layerPosition(l1_0.layerNo2, 5, 5)
    layerMoveAlpha(l1_0.layerNo2, 0, 30)
    layerCopy(l1_0.layerNo, layerName.sys_4_a)
    layerClip(l1_0.layerNo, l2_2, l2_3, l2_2 + 60, l2_3 + 60)
    layerAlpha(l1_0.layerNo, 0)
    layerPosition(l1_0.layerNo, 5, 5)
    layerMoveAlpha(l1_0.layerNo, 100, 30)
    layerAnime(l1_0.layerNo, 4, true)
    wait(30)
    layerLoad(l1_0.layerNo2, "")
    switchScreen(0, "", 30)
    wait(10)
end
l1_0.hourGlassStageStart = function()
advPart(false)
layerAlpha(l1_0.layerNo, 100)
local l2_0, l2_1 = l1_0.setHourGlassCount2FileName(100)
layerClip(l1_0.layerNo, l2_0, l2_1, l2_0 + 60, l2_1 + 60)
layerPosition(l1_0.layerNo, 5, 5)
layerMovePosition(l1_0.layerNo, 5, -10, 40)
layerMoveRotate(l1_0.layerNo, 0, 0, 180, 40)
wait(40)
l2_0, l2_1 = l1_0.setHourGlassCount2FileName(0)
layerClip(l1_0.layerNo, l2_0, l2_1, l2_0 + 60, l2_1 + 60)
layerPosition(l1_0.layerNo, 5, -10)
layerRotate(l1_0.layerNo, 0, 0, 0)
switchScreen(0, "", 15)
layerMovePosition(l1_0.layerNo, 5, 5, 30)
wait(30)
advPart(true)
end
return l1_0
end

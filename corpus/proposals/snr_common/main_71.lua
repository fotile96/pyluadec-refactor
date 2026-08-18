return function(l1_0, l1_1, l1_2, l1_3, ...)
if not l1_3 then
    l1_3 = ""
end
advPart(false)
local l1_5 = {art = 1, music = 2, health = 3, staffRoom = 4, court = 5, ground = 6, class = 7, roof = 8, corridor = 9, library = 10}
local l1_6 = {art = 0, music = 52, health = 104, staffRoom = 156, court = 208, ground = 0, class = 52, roof = 104, corridor = 156, library = 208}
local l1_7 = {art = 0, music = 0, health = 0, staffRoom = 0, court = 0, ground = 120, class = 120, roof = 120, corridor = 120, library = 120}
local l1_8 = {}
local l1_9 = {}
local l1_10 = {bg = 0, chara = 1, info = 3, map = 4}
local l1_11 = {}
local l1_12 = 0
if 0 < select("#", ...) then
    l1_12 = select("#", ...) / 4
end
for l1_16 = 1, select("#", ...), 1 do
    l1_11[l1_16] = select(l1_16, ...)
end
for l1_16 = 0, 15, 1 do
    layerLoad(l1_16, "")
end
layerLoad(l1_10.bg, l1_0)
layerCopy(l1_10.info, layerName.sel_map_0_a)
layerPosition(l1_10.info, 0, 230)
if l1_1 == "YUI" then
    layerCopy(l1_10.chara, layerName.sel_map_2_a)
    if l1_2 == 1 then
        layerClip(l1_10.chara, 0, 0, 90, 92)
    else
        layerClip(l1_10.chara, 90, 0, 180, 92)
    end
elseif l1_1 == "AYA" then
    layerCopy(l1_10.chara, layerName.sel_map_2_b)
    if l1_2 == 1 then
        layerClip(l1_10.chara, 0, 0, 80, 84)
    elseif l1_2 == 2 then
        layerClip(l1_10.chara, 80, 0, 160, 84)
    else
        layerClip(l1_10.chara, 160, 0, 240, 84)
    end
end
layerPosition(l1_10.chara, 180, 188)
if not (l1_3 == "") then
    layerCopy(l1_10.map, layerName.sel_map_1_a)
    layerPosition(l1_10.map, 356, 246)
    layerClip(l1_10.map, l1_7[l1_3], l1_6[l1_3] + 26, l1_7[l1_3] + 120, l1_6[l1_3] + 52)
else
    l1_3 = l1_11[1]
end
local l1_13 = 1
local l1_14 = 1
for l1_18 = 1, l1_12, 1 do
    layerCopy(l1_10.map + l1_18, layerName.sel_map_1_a)
    layerPosition(l1_10.map + l1_18, l1_11[(l1_18 - 1) * 4 + 2], l1_11[(l1_18 - 1) * 4 + 3])
    if l1_11[(l1_18 - 1) * 4 + 1] == l1_3 then
        layerClip(l1_10.map + l1_18, l1_7[l1_11[(l1_18 - 1) * 4 + 1]], l1_6[l1_11[(l1_18 - 1) * 4 + 1]], l1_7[l1_11[(l1_18 - 1) * 4 + 1]] + 120, l1_6[l1_11[(l1_18 - 1) * 4 + 1]] + 26)
        l1_13 = l1_18
    else
        layerClip(l1_10.map + l1_18, l1_7[l1_11[(l1_18 - 1) * 4 + 1]], l1_6[l1_11[(l1_18 - 1) * 4 + 1]] + 26, l1_7[l1_11[(l1_18 - 1) * 4 + 1]] + 120, l1_6[l1_11[(l1_18 - 1) * 4 + 1]] + 52)
    end
end
switchScreen(0, "", 60)
local l1_15 = false
local l1_16 = 1
local l1_17 = 1
local l1_18 = 1
while true do
    if l1_15 == false then
        if pressButton("CIRCLE") == true then
            if l1_18 == 0 then
                keyPlaySE(seName.circle)
                wait(5)
                break
            end
        else
            l1_18 = 0
        end
        if pressButton("UP") == true then
            if l1_16 == 0 then
                l1_14 = l1_13
                l1_13 = l1_13 - 1 < 1 and l1_12 or l1_13 - 1
                l1_15 = true
            end
        else
            l1_16 = 0
        end
        if pressButton("DOWN") == true then
            if l1_17 == 0 then
                l1_14 = l1_13
                l1_13 = l1_12 < l1_13 + 1 and 1 or l1_13 + 1
                l1_15 = true
            end
        else
            l1_17 = 0
        end
        if pressButton("LEFT") == true then
        end
        if pressButton("RIGHT") == true then
        end
    end
    if l1_15 == true then
        keyPlaySE(seName.arrowKey)
        layerClip(l1_10.map + l1_13, l1_7[l1_11[(l1_13 - 1) * 4 + 1]], l1_6[l1_11[(l1_13 - 1) * 4 + 1]], l1_7[l1_11[(l1_13 - 1) * 4 + 1]] + 120, l1_6[l1_11[(l1_13 - 1) * 4 + 1]] + 26)
        layerClip(l1_10.map + l1_14, l1_7[l1_11[(l1_14 - 1) * 4 + 1]], l1_6[l1_11[(l1_14 - 1) * 4 + 1]] + 26, l1_7[l1_11[(l1_14 - 1) * 4 + 1]] + 120, l1_6[l1_11[(l1_14 - 1) * 4 + 1]] + 52)
        l1_15 = false
        wait(5)
    end
    wait(2)
end
for l1_22 = 1, l1_12, 1 do
    if not (l1_13 == l1_22) then
        layerMoveAlpha(l1_10.map + l1_22, 0, 30)
        layerMoveScale(l1_10.map + l1_22, 100, 0, 30)
    end
end
wait(30)
for l1_22 = 0, 15, 1 do
    layerLoad(l1_22, "")
end
advPart(true)
return l1_11[(l1_13 - 1) * 4 + 4]
end

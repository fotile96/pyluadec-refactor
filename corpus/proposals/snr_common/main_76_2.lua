local u0
return function()
local l1_0 = 0
local l1_1 = 1
local l1_2 = false
while l1_0 < 1 do
    if pressButton("CIRCLE") == true then
        if l1_2 == false then
            if gameSave.tutorial.firstFragment == 1 then
                if l1_1 == 6 then
                    keyPlaySE(seName.circle)
                    systemSave.storyLineSkip = systemSave.storyLineSkip == 2 and 0 or 2
                    if not (systemSave.storyLineSkip == 0) then
                        layerClip(u0.layerNumber.info + 4, 0, 0, 11, 11)
                    else
                        layerClip(u0.layerNumber.info + 4, 0, 11, 11, 22)
                    end
                    wait(5)
                elseif l1_1 == 3 and memoryFlag == true then
                else
                    keyPlaySE(seName.circle)
                    break
                end
            elseif not (l1_1 == 3) and not (l1_1 == 4) and not (l1_1 == 7) and not (l1_1 == 8) or l1_1 == 3 and memoryFlag == true then
            else
                keyPlaySE(seName.circle)
                break
            end
        end
    end
    if pressButton("CROSS") == true then
        if l1_2 == false then
            keyPlaySE(seName.cross)
            l1_1 = -1
            break
        end
    end
    if pressButton("UP") == true then
        if l1_2 == false then
            l1_1 = l1_1 - 1 < 1 and 8 or l1_1 - 1
            l1_2 = true
        end
    end
    if pressButton("DOWN") == true then
        if l1_2 == false then
            l1_1 = 8 < l1_1 + 1 and 1 or l1_1 + 1
            l1_2 = true
        end
    end
    if l1_2 == true then
        keyPlaySE(seName.arrowKey)
        layerMovePosition(u0.layerNumber.configBG + 2, 175, (l1_1 - 1) * 24 + 35, 5)
        layerClip(u0.layerNumber.info + 3, 0, (l1_1 - 1) * 18, 376, l1_1 * 18)
        wait(5)
        l1_2 = false
    end
    wait(1)
end
return l1_1
end

local u0, u1, u2, u3, u4, u5, u6, u7, u8, u9, u10
return function()
advPart(false)
logEnable(false)
systemConfig.unsetConfigButton()
startLoading()
for l1_3, l1_4 in pairs(u0.layerName) do
    comLayerLoadFalse(l1_4, "graphic/" .. l1_3 .. ".gim")
end
waitLoading()
endLoading()
u1()
while true do
    if u2 == false then
        if pressButton("UP") == true then
            if u3 == false then
                u4 = u5
                local l1_0 = u5 - 3 < 1 and u5 or u5 - 3
                u5 = l1_0
                l1_0 = true
                u3 = l1_0
            end
        end
        if pressButton("DOWN") == true then
            if u3 == false then
                u4 = u5
                if u6 - u7 * 9 < 0 then
                    local l1_0 = u5 + 3 > u6 - (u7 - 1) * 9 and u5 or u5 + 3
                    u5 = l1_0
                else
                    local l1_0 = 9 < u5 + 3 and u5 or u5 + 3
                    u5 = l1_0
                end
                u3 = true
            end
        end
        if pressButton("RIGHT") == true then
            if u3 == false then
                u4 = u5
                if u7 + 1 <= u8 then
                    if u5 == 3 or u5 == 6 or u5 == 9 then
                        u7 = u7 + 1
                        u5 = u5 - 2
                        if u6 - u7 * 9 < 0 then
                            local l1_0 = u5 > u6 - (u7 - 1) * 9 and u6 - (u7 - 1) * 9 or u5
                            u5 = l1_0
                        end
                        u9(0, u4, u5, u7)
                    else
                        local l1_0 = u5 + 1 > u6 - (u7 - 1) * 9 and u5 or u5 + 1
                        u5 = l1_0
                        l1_0 = u5
                        if l1_0 == u4 then
                        end
                        l1_0 = true
                        u3 = l1_0
                    end
                elseif not (u5 == 3) then
                    if not (u5 == 6) then
                        if not (u5 == 9) then
                            local l1_0 = u5 + 1 > u6 - (u7 - 1) * 9 and u5 or u5 + 1
                            u5 = l1_0
                            l1_0 = u5
                            if l1_0 == u4 then
                            end
                            l1_0 = true
                            u3 = l1_0
                        end
                    end
                end
            end
        end
        if pressButton("LEFT") == true then
            if u3 == false then
                u4 = u5
                if 1 <= u7 - 1 then
                    if u5 == 1 or u5 == 4 or u5 == 7 then
                        u7 = u7 - 1
                        u5 = u5 + 2
                        u9(1, u4, u5, u7)
                    else
                        u5 = u5 - 1
                        if u5 == u4 then
                        end
                        u3 = true
                    end
                elseif not (u5 == 1) then
                    if not (u5 == 4) then
                        if not (u5 == 7) then
                            u5 = u5 - 1
                            if u5 == u4 then
                            end
                            u3 = true
                        end
                    end
                end
            end
        end
        if pressButton("L") == true then
            if u3 == false then
                if 1 <= u7 - 1 then
                    u7 = u7 - 1
                    u9(1, u5, u5, u7)
                end
            end
        end
        if pressButton("R") == true then
            if u3 == false then
                if u7 + 1 <= u8 then
                    u7 = u7 + 1
                    if u6 - u7 * 9 < 0 then
                        local l1_0 = u5 > u6 - (u7 - 1) * 9 and u6 - (u7 - 1) * 9 or u5
                        u5 = l1_0
                    end
                    u9(0, u5, u5, u7)
                end
            end
        end
        if pressButton("CROSS") == true then
            keyPlaySE(seName.cross)
            wait(10)
            break
        end
        if pressButton("CIRCLE") == true then
            if u3 == false then
                if systemSave.cgFlag[u0.cgNumber[u7][u5][1]] == true then
                    keyPlaySE(seName.circle)
                    u2 = true
                    layerLoad(u0.layerNumber.view, cGetFileName("event", u0.cgNumber[u7][u5][1]))
                    layerPosition(u0.layerNumber.view, u0.viewX[u5], u0.viewY[u5])
                    layerMovePosition(u0.layerNumber.view, 0, 0, 30)
                    layerScale(u0.layerNumber.view, 25, 25)
                    layerMoveScale(u0.layerNumber.view, 100, 100, 30)
                    wait(30)
                    if 1 < #u0.cgNumber[u7][u5] then
                        for l1_3 = 2, #u0.cgNumber[u7][u5], 1 do
                            if systemSave.cgFlag[u0.cgNumber[u7][u5][l1_3]] == true then
                                layerLoadAsync(0, u0.layerNumber.view + l1_3 - 1, cGetFileName("event", u0.cgNumber[u7][u5][l1_3]))
                            end
                        end
                    end
                end
            end
        end
        if u3 == true then
            if not (u4 == u5) then
                keyPlaySE(seName.arrowKey)
            end
            layerVisible(u0.layerNumber.mask + u4, true)
            layerVisible(u0.layerNumber.mask + u5, false)
            layerMovePosition(u0.layerNumber.cursor, u0.cursorX[u5], u0.cursorY[u5], 5)
            fontClear()
            u3 = false
            wait(5)
        end
    else
        if pressButton("CIRCLE") == true then
            u10 = u10 + 1 > #u0.cgNumber[u7][u5] and -1 or u10 + 1
            if 1 < u10 then
                for l1_3 = u10, #u0.cgNumber[u7][u5], 1 do
                    if systemSave.cgFlag[u0.cgNumber[u7][u5][l1_3]] == true then
                        u10 = l1_3
                        break
                    elseif l1_3 == #u0.cgNumber[u7][u5] then
                        u10 = -1
                        break
                    end
                end
            end
            if u10 == -1 then
                keyPlaySE(seName.cross)
                layerMoveScale(u0.layerNumber.view, 25, 25, 30)
                layerMovePosition(u0.layerNumber.view, u0.viewX[u5], u0.viewY[u5], 30)
                wait(30)
                for l1_3 = 1, #u0.cgNumber[u7][u5], 1 do
                    layerLoad(u0.layerNumber.view + l1_3 - 1, "")
                end
                wait(10)
                u10 = 1
                u2 = false
            else
                while true do
                    if layerIsLoad(u0.layerNumber.view + u10 - 1) == true then
                        break
                    end
                    wait(1)
                end
                keyPlaySE(seName.circle)
                layerCopy(u0.layerNumber.view, u0.layerNumber.view + u10 - 1)
                switchScreen(0, "", 30)
            end
        end
        if pressButton("CROSS") == true then
            keyPlaySE(seName.cross)
            layerMoveScale(u0.layerNumber.view, 25, 25, 30)
            layerMovePosition(u0.layerNumber.view, u0.viewX[u5], u0.viewY[u5], 30)
            wait(30)
            for l1_3 = 1, #u0.cgNumber[u7][u5], 1 do
                layerLoad(u0.layerNumber.view + l1_3 - 1, "")
            end
            wait(10)
            u10 = 1
            u2 = false
        end
    end
    wait(2)
end
cInitGame()
switchScreen(0, "", 60)
run(cGetFileName("script", "snr_mainmenu"))
end

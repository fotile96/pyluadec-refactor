return function()
    local t = { startMenuState = 0 }
    t.debagMsg = function(msg)
        if debagFlag then
            vms(1, "NONVOICE", "■デバッグ：" .. msg)
        end
    end
    t.debagPairs = function(t2)
        if debagFlag then
            for k, v in pairs(t2) do
                vms(2, "NONVOICE", "Ｋｅｙ＿" .. k .. "：Ｖａｌｕｅ＿" .. v)
            end
        end
    end
    return t
end

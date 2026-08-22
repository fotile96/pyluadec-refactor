local u0
return function()
local l1_0
pageScreen(1)
u0.blackIn()
u0.OptionInit()
for l1_4 = 3, 100, 1 do
    layerAlpha(l1_4, 0)
end
layerScale(u0.layerNumber.optionBg, 0, 100)
layerMoveScale(u0.layerNumber.optionBg, 100, 100, 20)
layerScale(u0.layerNumber.info, 0, 100)
layerMoveScale(u0.layerNumber.info, 100, 100, 20)
wait(20)
for l1_4 = 3, 100, 1 do
    layerMoveAlpha(l1_4, 100, 10)
end
wait(10)
u0.OptionMain()
u0.OptionEnd()
autoSystemSave(1)
u0.blackOut()
wait(5)
pageScreen(0)
wait(1)
end

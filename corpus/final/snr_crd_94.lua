local card_94_s8s_50_intro = function()
    vms(3868, "NONVOICE", "○セクション７のあらすじを選択してください。")
end
local card_94_s8s_50_resolve = function()
    wait(60)
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(200)
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『誰も見たことのない夕焼け』のあらすじを作成しました。")
    comSectionCardEndSection()
    doScriptScene = "s8f-10"
    run(cGetFileName("script", "snr_s8_10_f"))
    quit()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[141].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_94_s8s_50_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 141 then
            break
        end
        if l1_3 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        vms(3869, "NONVOICE", "○セクション７のあらすじを選択してください。")
        wait(30)
    end
    card_94_s8s_50_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

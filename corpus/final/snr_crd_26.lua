local card_26_e2s_10_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    vms(2169, "NONVOICE", "○セクションＥＸ１のあらすじを選択してください。")
end
local card_26_e2s_10_resolve = function()
    wait(60)
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(120)
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『誰も来ない』のあらすじを作成しました。")
    local l1_0 = gameSave.myCard[gameSave.fragmentDoCardId]
    l1_0.hold = 1
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[143].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_26_e2s_10_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 143 then
            break
        end
        if l1_3 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        vms(2170, "NONVOICE", "○セクションＥＸ１のあらすじを選択してください。")
        wait(30)
    end
    card_26_e2s_10_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

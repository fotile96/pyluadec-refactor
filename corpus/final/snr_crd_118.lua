local card_118_e1s_10_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_20_b"))
    wait(1)
    layerLoad(layerName.pose1, cGetFileName("bg", "bg_26_b_0"))
    switchScreen(0, "", 60)
    wait(60)
    vms(635, "NONVOICE", "セクション４に存在した分岐、『選択：ユカリ先生』のカードを選択してください。")
end
local card_118_e1s_10_resolve = function()
    wait(120)
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『春』のあらすじを作成しました。")
    comPoseDelete()
    comSectionCardEndSection()
    doScriptScene = "e1f-10"
    run(cGetFileName("script", "snr_e1_10_f"))
    quit()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[152].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_118_e1s_10_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 152 then
            break
        end
        if l1_3 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        vms(636, "NONVOICE", "セクション４に存在した分岐、『選択：ユカリ先生』のカードを選択してください。")
        wait(30)
    end
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(60)
    card_118_e1s_10_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

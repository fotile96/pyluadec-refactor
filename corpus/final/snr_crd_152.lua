local card_152_s4s_100_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_19_x"))
    cLoadPlaySE(cGetFileName("se", "se_106"), false)
    wait(1)
    layerLoad(layerName.pose1, cGetFileName("event", "eve_49_x"))
    switchScreen(0, "", 60)
    wait(60)
    vms(966, "NONVOICE", "セクション８のあらすじカードを選択してください。")
end
local card_152_s4s_100_sel_resolve = function()
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(200)
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ユカリ先生』の選択肢（受け入れる）を作成しました。")
    gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
    comPoseDelete()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[142].hold == -1 then
        vms(967, "NONVOICE", "【＊＊＊】この場面を作成するためのカードが足りません。")
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_152_s4s_100_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 142 then
            break
        end
        if l1_3 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_1 == 1 then
            vms(968, "NONVOICE", "セクション８のあらすじカードを選択してください。")
        end
        if l1_1 == 0 then
            vms(969, "NONVOICE", "セクション８のあらすじカードを選択してください。")
        end
        wait(30)
    end
    card_152_s4s_100_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

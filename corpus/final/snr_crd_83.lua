local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3593, "NONVOICE", "【直哉】「アヤノさんが階段にいると、男の人の声が聞こえたんだ」")
    vms(3594, "NONVOICE", "【彩野】「えっと、この声の主って――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3595, "NONVOICE", "【彩野】「ユウイチの声……」")
    vms(3596, "NONVOICE", "【直哉】「ユウイチとアヤノさんは、階段で再会したんだ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『階段へ』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_2_e")
    vms(3597, "NONVOICE", "【彩野】「ユウイチの声が階段から聞こえたんだ」")
    vms(3598, "NONVOICE", "【彩野】「ユウイチ……」")
    vms(3599, "NONVOICE", "【直哉】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[123].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    l0_0()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 123 then
            break
        end
        if l1_3 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_1 == 1 then
            oCard.mesNG2()
            vms(3600, "NONVOICE", "物語の登場人物として、『アイツ』の名前のカードを作ってある。")
            vms(3601, "NONVOICE", "そのカードを見て貰えばいいかな。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_1()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

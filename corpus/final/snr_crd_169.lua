local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1302, "NONVOICE", "【直哉】「ここはアヤノさんを捜しに、ユウイチが校内を探索する場面――」")
    vms(1303, "NONVOICE", "【直哉】「それでね。この後の、屋上でアヤノさんを見つける場面のあらすじもつくってあるんだ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1304, "NONVOICE", "【彩野】「あ、そうなんだ。……それ、教えてもらっていい？」")
    vms(1305, "NONVOICE", "【直哉】「うん。『選択』の場面だね……」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1306, "NONVOICE", "【彩野】「ふむ……」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1307, "NONVOICE", "【彩野】「そっか、ここの場面は『学校内を探索して、屋上でアヤノを見つけた』でひとまとめにしていいみたいだね」")
    vms(1308, "NONVOICE", "【直哉】「了解。カードをつくるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『探索：アヤノの居場所』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[170].hold == -1 then
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
        if l1_3 == 170 then
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
            vms(1309, "NONVOICE", "屋上の選択――『選択：アヤノを――』のあらすじを見せてみよう。")
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

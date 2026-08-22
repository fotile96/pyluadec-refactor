local card_18_s1s_170_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1609, "NONVOICE", "【彩野】「直哉くん……」")
    vms(1610, "NONVOICE", "【直哉】「……どうかした？」")
    vms(1611, "NONVOICE", "彩野さんは声を落としていった。")
    comPoseLoad("po2_aya_f_2_e")
    vms(1612, "NONVOICE", "【彩野】「ここ、なんだけど、なにかすごく嫌な予感がする」")
    vms(1613, "NONVOICE", "【彩野】「学校に戻ると、嫌なことが起きるような気がする」")
    vms(1614, "NONVOICE", "【彩野】「すごく、嫌なこと」")
    vms(1615, "NONVOICE", "【彩野】「なんなんだろう、これ……」")
    comPoseDelete()
end
local card_18_s1s_170_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1616, "NONVOICE", "【彩野】「でも……」")
    vms(1617, "NONVOICE", "【彩野】「屋上から、転落……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1618, "NONVOICE", "【彩野】「これって、私の『現実』の事と、関係あるのかな？」")
    vms(1619, "NONVOICE", "【直哉】「あ……」")
    vms(1620, "NONVOICE", "【直哉】「……」")
    vms(1621, "NONVOICE", "僕は固まった。なんと答えてよいのか、言葉が見つからない。")
    comPoseLoad("po2_aya_f_1_c")
    vms(1622, "NONVOICE", "【彩野】「屋上から、私が、落ちた。『現実』はこの『物語』と関係あるのかな？」")
    vms(1623, "NONVOICE", "【直哉】「それは……わからない」")
    vms(1624, "NONVOICE", "【直哉】「進めてみないと、今の段階だと、情報が少なすぎて」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1625, "NONVOICE", "【彩野】「そっか……。ごめんね……」")
    comPoseLoad("po2_aya_f_2_c")
    vms(1626, "NONVOICE", "【彩野】「でも……」")
    vms(1627, "NONVOICE", "【直哉】「ん？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1628, "NONVOICE", "【彩野】「ここで、私が学校に戻らない、そういう方法もあるんじゃないかな？」")
    vms(1629, "NONVOICE", "【直哉】「えっと……分岐がある、っていうこと？」")
    vms(1630, "NONVOICE", "【彩野】「うん。そんな感じ」")
    comPoseLoad("po2_aya_f_1_e")
    vms(1631, "NONVOICE", "【彩野】「家に帰るの。そうしたら、あんな嫌な思い、しなくてすんだのかもしれない」")
    vms(1632, "NONVOICE", "【直哉】「家に帰る……。わかった。カードを書いてみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：学校に戻る』の選択肢（家に帰る）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[116].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_18_s1s_170_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 116 then
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
            vms(1633, "NONVOICE", "【彩野】「すごく、嫌なことが屋上で起きたような気がする」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_18_s1s_170_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

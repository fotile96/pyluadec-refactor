local card_19_s1s_180_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1654, "NONVOICE", "【彩野】「いつもの生活、日常、か」")
    vms(1655, "NONVOICE", "【彩野】「いつもは『アヤノ』、放課後はどうしてたのかな？」")
    comPoseDelete()
end
local card_19_s1s_180_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_d")
    vms(1656, "NONVOICE", "【彩野】「ふむ、すぐに家に帰っちゃったんだ。仕方ない子だなあ」")
    vms(1657, "NONVOICE", "【直哉】「彩野さん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1658, "NONVOICE", "【彩野】「ん？ どうかした？」")
    vms(1659, "NONVOICE", "【直哉】「ここで『物語』は終わってるんだけど……これって、どういうことなんだろう」")
    vms(1660, "NONVOICE", "【直哉】「一応、これで完結しちゃったのかな」")
    comPoseLoad("po2_aya_f_2_a")
    vms(1661, "NONVOICE", "【彩野】「うーん、これ以上の展開は、思いつかないって感じ、かも」")
    vms(1662, "NONVOICE", "【直哉】「バッドエンド、みたいなもの？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1663, "NONVOICE", "【彩野】「たぶん……そうかも」")
    comPoseLoad("po2_aya_f_2_d")
    vms(1664, "NONVOICE", "【彩野】「なんだろう、原稿用紙に物語を書いてる途中で上手く進まなくて、紙をクシャクシャにまるめて、ポイ、みたいな」")
    vms(1665, "NONVOICE", "【直哉】「たしかに、この前のシーンから物語は分岐してるから、そういうのもあるかもしれないね」")
    vms(1666, "NONVOICE", "【直哉】「でも、こういう終わり方も好きだけどね、僕は」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1667, "NONVOICE", "【彩野】「ふふ。ちょっと不思議なお話でした、みたいな感じ？」")
    vms(1668, "NONVOICE", "【直哉】「そうそう。じゃ、ここの場面のあらすじをまとめてみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『いつもの生活』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[121].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_19_s1s_180_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 121 then
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
            vms(1669, "NONVOICE", "【彩野】「アヤノは学校が終わったら普段ならどうしていたんだろう……」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_19_s1s_180_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

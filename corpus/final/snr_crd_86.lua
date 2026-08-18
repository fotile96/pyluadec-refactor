local card_86_s3s_550_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3644, "NONVOICE", "【彩野】「階段でバランスを崩したアヤノが、ユウイチに助けられる場面、だね」")
    vms(3645, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3646, "NONVOICE", "【彩野】「あ――直哉くん？ どうしてアヤノは階段に来ているんだっけ？」")
    vms(3647, "NONVOICE", "【直哉】「あ、それはね。『階段のウワサ話』の調査のためだね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3648, "NONVOICE", "【彩野】「階段のウワサ話――」")
    vms(3649, "NONVOICE", "【彩野】「えっと、そのことを詳しく解説した場面って、ある？」")
    vms(3650, "NONVOICE", "階段のウワサ話は、陸上部のきくちゃんに聞きに行ったから……。")
    vms(3651, "NONVOICE", "その場面のあらすじを確認して貰うのがいいかな。")
    comPoseDelete()
end
local card_86_s3s_550_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3652, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3653, "NONVOICE", "【彩野】「そっか、こんな『ウワサ』だったんだ」")
    vms(3654, "NONVOICE", "【彩野】「あ、それと、直哉くん。この『階段』の場面で一つ、気になることがあって」")
    vms(3655, "NONVOICE", "【直哉】「気になること？」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3656, "NONVOICE", "【彩野】「うん。ちょっとね、いつだったのかは忘れちゃったんだけど……」")
    vms(3657, "NONVOICE", "【彩野】「私、『現実』でも、ユウイチとこんな風に階段で呼び止められて話したような気がする」")
    vms(3658, "NONVOICE", "【直哉】「え、それは――」")
    comPoseLoad("po2_aya_f_2_d")
    vms(3659, "NONVOICE", "【彩野】「あ、もちろんアイツと抱き合ったなんて覚えは無いんだけどね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3660, "NONVOICE", "【彩野】「でも、アイツと話したような気はするの」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3661, "NONVOICE", "【彩野】「……ごめんね、はっきりしなくて」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ユウイチと階段へ』のあらすじを作成しました。")
    comPoseDelete()
    vms(3662, "NONVOICE", "ユウイチと階段で話した、か。")
    vms(3663, "NONVOICE", "……。")
    vms(3664, "NONVOICE", "何かそれが物語の下地になっているのだろうか？")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[77].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_86_s3s_550_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 77 then
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
            vms(3665, "NONVOICE", "陸上部のきくちゃんに聞きに行った時のあらすじを見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_86_s3s_550_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

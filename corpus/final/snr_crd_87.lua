local card_87_s3s_580_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3666, "NONVOICE", "【彩野】「直哉くん、ここの場面なんだけど……」")
    vms(3667, "NONVOICE", "【彩野】「『いつかは別れが』を選んだ後のあらすじってどうなるのかな……？」")
    vms(3668, "NONVOICE", "【直哉】「えっと、それは……」")
    vms(3669, "NONVOICE", "【直哉】「あまり良くない、展開になるね」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3670, "NONVOICE", "【彩野】「良くない展開……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3671, "NONVOICE", "【彩野】「あらすじのカードとか、ある？」")
    vms(3672, "NONVOICE", "【直哉】「えっとね……」")
    vms(3673, "NONVOICE", "この後のシーンのあらすじを説明すると言うことは、必然的に『図書室』に繋がることになる。")
    vms(3674, "NONVOICE", "正直、『あの場面』を彩野さんに余り見せたくはなかった。")
    vms(3675, "NONVOICE", "……")
    vms(3676, "NONVOICE", "でも、彩野さんが見たいというなら……説明はするべきだ。")
    vms(3677, "NONVOICE", "【直哉】「……。うん。カードを作ってあるよ」")
    comPoseDelete()
end
local card_87_s3s_580_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(3678, "NONVOICE", "【彩野】「あ――」")
    vms(3679, "NONVOICE", "彩野さんはカードの内容に目を通すと、視線を落とした。")
    vms(3680, "NONVOICE", "【直哉】「それでね。このカードを作ったとき、この後の展開は良くない『予感』がするから、ここで分岐を作った方が良いかもしれないって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3681, "NONVOICE", "【彩野】「うん。そうだね……」")
    vms(3682, "NONVOICE", "【彩野】「『でも、いつかは別れが』の展開が良くないのなら……」")
    vms(3683, "NONVOICE", "【直哉】「分岐、を？」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3684, "NONVOICE", "【彩野】「うん……『ずっと一緒にいたい』、そう思ったのかもしれない」")
    vms(3685, "NONVOICE", "【彩野】「で、でも、直哉くん、私は――！」")
    vms(3686, "NONVOICE", "【直哉】「――わかった。カードを作るね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ユウイチと……』の選択肢（ずっと一緒にいたい）を作成しました。")
    comPoseLoad("po2_aya_f_1_a")
    vms(3687, "NONVOICE", "【彩野】「……直哉くん……」")
    vms(3688, "NONVOICE", "【直哉】「……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3689, "NONVOICE", "【彩野】「ごめんなさい」")
    vms(3690, "NONVOICE", "【直哉】「謝らないで、彩野さん」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3691, "NONVOICE", "【彩野】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[92].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_87_s3s_580_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 92 then
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
            vms(3692, "NONVOICE", "『でも、いつかは別れが』のあらすじを彩野さんに説明しよう……。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_87_s3s_580_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

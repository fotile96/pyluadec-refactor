local card_173_s4s_670_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1404, "NONVOICE", "【直哉】「屋上でユウイチがアヤノさんを助けた後の場面、だね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1405, "NONVOICE", "【彩野】「それでね、直哉くん、ここの部分なんだけど……」")
    vms(1406, "NONVOICE", "【直哉】「ん、どうかした？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1407, "NONVOICE", "【彩野】「家に帰る、なんだよね……」")
    vms(1408, "NONVOICE", "【直哉】「あ、うん。この後はセクションの終わりだね」")
    vms(1409, "NONVOICE", "【直哉】「『消えたサクラ』の場面でセクションは完了。物語は終わるんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1410, "NONVOICE", "【彩野】「うん……」")
    vms(1411, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1412, "NONVOICE", "【彩野】「……ね、直哉くん」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1413, "NONVOICE", "【彩野】「じゃあ……。このセクションはもう、終わってるんだよね？」")
    vms(1414, "NONVOICE", "【直哉】「うん。そういう事になるね」")
    vms(1415, "NONVOICE", "【彩野】「……直哉くん。セクション４の物語全体の『あらすじ』、教えてもらっていいかな？」")
    comPoseDelete()
end
local card_173_s4s_670_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1416, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1417, "NONVOICE", "【彩野】「そっか……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1418, "NONVOICE", "【彩野】「直哉くん、ここ、新しい『物語』が追加できるかもしれない」")
    vms(1419, "NONVOICE", "【直哉】「物語の展開が、変わるかもしれない、ということ？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1420, "NONVOICE", "【彩野】「うん、なんとなく。結末を聞いてそう思ったの」")
    vms(1421, "NONVOICE", "彩野さんは教室の端に座っている千秋ちゃんを、まるで眩しいものでも見るかのように目を細めて眺めた。")
    vms(1422, "NONVOICE", "【彩野】「もしかしたらサクラさんを探すことで、もう少し『物語が続くかもしれない』って」")
    vms(1423, "NONVOICE", "サクラさんを、探す――")
    vms(1424, "NONVOICE", "【直哉】「……わかった。カードを作ってみるよ」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1425, "NONVOICE", "コクリと、彩野さんは頷いた。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：放課後の学校』の選択肢（サクラを待つ）を作成しました。")
    vms(1426, "NONVOICE", "カードをつくった――")
    vms(1427, "NONVOICE", "でも……。")
    vms(1428, "NONVOICE", "彩野さんの表情は、浮かばない……。")
    vms(1429, "NONVOICE", "どうしてだろう……？")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[137].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_173_s4s_670_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 137 then
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
            vms(1430, "NONVOICE", "セクション４のあらすじを、アヤノさんに渡そう……。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_173_s4s_670_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

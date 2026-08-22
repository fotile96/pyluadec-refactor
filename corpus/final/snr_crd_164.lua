local card_164_s4s_360_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1146, "NONVOICE", "【直哉】「アヤノさんの机を調べるかどうかの選択、だね」")
    vms(1147, "NONVOICE", "【直哉】「でね、彩野さん。この場面の『展開』について、気になる部分があるんだけど……」")
    comPoseLoad("po2_aya_f_2_a")
    vms(1148, "NONVOICE", "【彩野】「展開？」")
    vms(1149, "NONVOICE", "【直哉】「うん。ここのシーンに辿り着くには、『屋上のサクラさん』の質問が関係あるのかもしれないなって思ったんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1150, "NONVOICE", "【彩野】「ん、どういうこと？」")
    vms(1151, "NONVOICE", "【直哉】「えっとね、この前の場面でサクラさんから質問があったんだけど、その答えにこう答える必要があったのかなって」")
    comPoseDelete()
end
local card_164_s4s_360_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1152, "NONVOICE", "【彩野】「『信じてみてもいい』――」")
    vms(1153, "NONVOICE", "【彩野】「サクラさんを信じること――」")
    vms(1154, "NONVOICE", "【直哉】「うん。そうすると、この展開になるんだと思う。それで――」")
    vms(1155, "NONVOICE", "【直哉】「サクラさんは、ユウイチにこう言葉を返したんだ」")
    vms(1156, "NONVOICE", "【直哉】「『たぶん、アヤノさんも夕日のこと、信じてるよ』って」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1157, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1158, "NONVOICE", "【彩野】「……ね、直哉くん」")
    vms(1159, "NONVOICE", "【彩野】「ここ、展開を追加していいかな？」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1160, "NONVOICE", "【彩野】「私の――アヤノの机を調べるって」")
    vms(1161, "NONVOICE", "【直哉】「アヤノさんの机を？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1162, "NONVOICE", "【彩野】「うん。……そうすれば、次の物語に進めると思う」")
    vms(1163, "NONVOICE", "【直哉】「……わかった。作ってみるよ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：アヤノの机』の選択肢（机を調べる）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[161].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[159].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_164_s4s_360_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 161 then
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
            vms(1164, "NONVOICE", "この場面に辿り着くには、屋上のサクラさんの質問にどう答える必要があったのだろうか……。")
            vms(1165, "NONVOICE", "「信じてみてもいい」、「下らない」……どちらだったろうか？")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_164_s4s_360_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

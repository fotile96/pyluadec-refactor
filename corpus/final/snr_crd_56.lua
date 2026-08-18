local card_56_s2s_420_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2912, "NONVOICE", "【彩野】「屋上から転落した、男子生徒を目撃する場面」")
    vms(2913, "NONVOICE", "【彩野】「……なんだろう、すごく嫌な感じがする」")
    vms(2914, "NONVOICE", "【彩野】「この男子生徒って……」")
    cStopBGMWrap()
    vms(2915, "NONVOICE", "【直哉】「……実は、もう一場面あるんだ、彩野さん」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2916, "NONVOICE", "【彩野】「え？」")
    vms(2917, "NONVOICE", "僕は、彩野さんに『ユウイチの後ろ姿』のあらすじを見せることにした。")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_8_x"))
    comPoseDelete()
end
local card_56_s2s_420_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(2918, "NONVOICE", "【彩野】「え、これ……じゃあ……」")
    vms(2919, "NONVOICE", "【直哉】「うん。このあらすじと組み合わせると、屋上から落ちたのはユウイチだと思う」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2920, "NONVOICE", "【彩野】「……」")
    vms(2921, "NONVOICE", "【彩野】「ユウイチ……」")
    vms(2922, "NONVOICE", "【彩野】「直哉くん、これ、オマジナイが失敗しちゃったから、なのかな」")
    vms(2923, "NONVOICE", "【直哉】「……たぶん。話の流れを考えると、その可能性は高いと思う」")
    vms(2924, "NONVOICE", "【彩野】「たぶん効くオマジナイ、と、やってソンはないオマジナイ……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2925, "NONVOICE", "【彩野】「ね、直哉くん」")
    vms(2926, "NONVOICE", "彩野さんは何かを思い詰めたように、僕の名前を呼んだ。")
    vms(2927, "NONVOICE", "【彩野】「やっぱりここ、アヤノの意識が弱いからだと思う」")
    vms(2928, "NONVOICE", "【直哉】「……意識」")
    vms(2929, "NONVOICE", "【彩野】「そう、意識……オマジナイへの願いのようなもの」")
    vms(2930, "NONVOICE", "【彩野】「カード、つくってもらっていいかな」")
    vms(2931, "NONVOICE", "【直哉】「オマジナイの『願い』のカード？」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2932, "NONVOICE", "【彩野】「うん。そういうこと。『絶対に効くオマジナイ』で、お願い」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2933, "NONVOICE", "【直哉】「……わかった。つくってみるよ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『廊下に響く声』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_97_a"), "『絶対に効くオマジナイ』のカードを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        gameSave.myCard[97].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[57].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_56_s2s_420_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 57 then
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
            vms(2934, "NONVOICE", "彩野さんに『ユウイチの後ろ姿』のあらすじを見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_56_s2s_420_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

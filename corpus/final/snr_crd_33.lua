local card_33_s2s_80_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2447, "NONVOICE", "【彩野】「夏の予定……」")
    vms(2448, "NONVOICE", "【彩野】「直哉くん。この誘いを断って、予定に行かなかったときの『あらすじ』って、もしかして知ってる？」")
    vms(2449, "NONVOICE", "【直哉】「あ、うん。この後の話だね。『また、いつもの生活』と同じみたいだ」")
    vms(2450, "NONVOICE", "【彩野】「そのあらすじカード、見せてもらっていい？」")
    comPoseDelete()
end
local card_33_s2s_80_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2451, "NONVOICE", "【彩野】「ふむ。予定に行かないと、なにも起こらないんだ……」")
    vms(2452, "NONVOICE", "【直哉】「……彩野さん」")
    vms(2453, "NONVOICE", "【彩野】「どうしたの？ 直哉くん」")
    vms(2454, "NONVOICE", "【直哉】「ここの『また、いつもの生活』のカードをつくったときに、考えた事があるんだ」")
    vms(2455, "NONVOICE", "【彩野】「考えた事？ 教えて、直哉くん」")
    vms(2456, "NONVOICE", "【直哉】「えっとね、確か、『何も起こらない日常』だと物語は終わっちゃうから――」")
    vms(2457, "NONVOICE", "【直哉】「物語を進めるためには、自分で行動を起こさなきゃって」")
    vms(2458, "NONVOICE", "【彩野】「自分で行動……なるほど。そういう事、言ってたんだ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(2459, "NONVOICE", "【彩野】「……ふむ。だったら、直哉くん」")
    vms(2460, "NONVOICE", "【直哉】「うん」")
    vms(2461, "NONVOICE", "【彩野】「ここはやっぱり、ユウイチと『行く』べきじゃないかな」")
    vms(2462, "NONVOICE", "【直哉】「選択肢をつくる、ということだね」")
    vms(2463, "NONVOICE", "【彩野】「うん、そう思う」")
    vms(2464, "NONVOICE", "【直哉】「了解。カードに書いてみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：週末の予定』の選択肢（行く）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[31].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[32].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_33_s2s_80_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 31 then
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
            vms(2465, "NONVOICE", "【彩野】「どこにも行かなかった場合、いつもの生活に戻っていったような……」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_33_s2s_80_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

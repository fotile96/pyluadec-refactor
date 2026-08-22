local card_24_s1s_230_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2118, "NONVOICE", "【彩野】「屋上、の場面……」")
    vms(2119, "NONVOICE", "【彩野】「風の『におい』」")
    vms(2120, "NONVOICE", "【彩野】「お日さまの匂い」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2121, "NONVOICE", "【彩野】「私は、どうして屋上にいたんだろう……」")
    comPoseDelete()
end
local card_24_s1s_230_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2122, "NONVOICE", "【彩野】「そっか……私、気がつくと屋上に、いたんだ」")
    vms(2123, "NONVOICE", "【直哉】「えっと、物語の『アヤノ』さんは、だよね。現実の『彩野』さん、ではなく」")
    comPoseLoad("po2_aya_f_2_c")
    vms(2124, "NONVOICE", "【彩野】「あっ、うん。そうだよね」")
    vms(2125, "NONVOICE", "【直哉】「教室でコックリさんをやっていて、アヤノさんは気がついたら屋上にいた」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2126, "NONVOICE", "【彩野】「うん。まとめるとそんな感じ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『気がつくといる場所』のあらすじを作成しました。")
    vms(2127, "NONVOICE", "でも。この展開。")
    vms(2128, "NONVOICE", "なぜ、屋上なんだ？")
    vms(2129, "NONVOICE", "なぜ、彩野さんは気がついたら屋上にいる、そんな物語を書く必要があるんだ？")
    vms(2130, "NONVOICE", "まさか、現実に起きたことと、この物語はリンクしている？")
    vms(2131, "NONVOICE", "しかし、そんな事があり得るのだろうか？")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[117].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_24_s1s_230_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 117 then
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
            vms(2132, "NONVOICE", "【彩野】「屋上……どうして屋上にいたんだろう……」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_24_s1s_230_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

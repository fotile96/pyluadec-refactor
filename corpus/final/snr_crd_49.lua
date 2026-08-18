local card_49_s2s_293_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2810, "NONVOICE", "【彩野】「オマジナイが成功したかな？ 失敗したかな？ って思う場面だね」")
    vms(2811, "NONVOICE", "【直哉】「そうだね……」")
    vms(2812, "NONVOICE", "【彩野】「どうしたの？ なにかあった、直哉くん」")
    vms(2813, "NONVOICE", "【直哉】「うん。実はこの後の展開なんだけど、こんな感じなんだ」")
    vms(2814, "NONVOICE", "【直哉】「一つは、中庭に転落した男子生徒を目撃する『廊下に響く声』の場面」")
    comPoseDelete()
end
local card_49_s2s_293_resolve = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_c")
    vms(2815, "NONVOICE", "【彩野】「……」")
    vms(2816, "NONVOICE", "【直哉】「そしてもう一つが、屋上から『ユウイチの後ろ姿』を目撃する場面」")
    comPoseDelete()
end
local card_49_s2s_293_step3 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(2817, "NONVOICE", "【彩野】「……ユウイチ……」")
    vms(17182, "NONVOICE", "【直哉】「『良くない結末』、だね」")
    vms(17183, "NONVOICE", "【彩野】「うん……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2821, "NONVOICE", "【彩野】「この結末と、オマジナイの結果は関係あるのかな？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(17184, "NONVOICE", "【彩野】「オマジナイに失敗しちゃってるって感じで……」")
    vms(2822, "NONVOICE", "【直哉】「……断言できないけど。ただ、物語の中で『ハズしてるような気もする』って書いてあるし、可能性は高いと思う」")
    vms(2825, "NONVOICE", "【彩野】「うん……そうだよね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『オマジナイ、成功……？』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[56].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[57].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_49_s2s_293_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 56 then
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
            vms(2826, "NONVOICE", "『廊下に響く声』のカードを見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_49_s2s_293_resolve()
    local l1_3 = 0
    local l1_4 = 0
    local l1_5 = -1
    while l1_3 < 1 do
        local l1_6 = oCard.selectCardObj()
        if l1_6 == 57 then
            break
        end
        if l1_6 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_4 == 1 then
            oCard.mesNG2()
            vms(2827, "NONVOICE", "『ユウイチの後ろ姿』のカードを見せてみよう。")
            comPoseDelete()
        end
        if l1_4 == 0 then
            oCard.mesNG()
            l1_4 = l1_4 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_49_s2s_293_step3()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

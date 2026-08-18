local card_147_s4s_30_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(746, "NONVOICE", "【直哉】「ここは、ユウイチと、ポケットに入れられた手紙について話す場面――」")
    vms(747, "NONVOICE", "【直哉】「それでね、彩野さん。ここの『私じゃない』の展開については、既にあらすじが作ってあるんだ」")
    comPoseLoad("po2_aya_f_2_a")
    vms(748, "NONVOICE", "【彩野】「あ、そうなんだ。カードを見せてもらっていい？」")
    comPoseDelete()
end
local card_147_s4s_30_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(749, "NONVOICE", "【彩野】「ふむ。『私じゃない』から先の展開は、セクション３に戻っちゃうんだ」")
    vms(750, "NONVOICE", "【直哉】「そうだね。セクション４から３に戻る。≪ちょっと特殊な展開≫だと思う」")
    vms(751, "NONVOICE", "【直哉】「でも。４から３に戻ると言うことは、結局展開は進んでないことになるわけで――」")
    vms(752, "NONVOICE", "【彩野】「他の展開、だね」")
    comPoseLoad("po2_aya_f_2_e")
    vms(753, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(754, "NONVOICE", "【彩野】「……直哉くん」")
    vms(755, "NONVOICE", "【直哉】「うん」")
    comPoseLoad("po2_aya_f_1_b")
    vms(756, "NONVOICE", "【彩野】「やっぱり、ここはこの手紙の事について、調べてみるべきだと思う」")
    vms(757, "NONVOICE", "【直哉】「という事は――」")
    comPoseLoad("po2_aya_f_1_a")
    vms(758, "NONVOICE", "【彩野】「えっとね。手紙に興味を持つような感じで――『気になる』展開も追加してもらっていい？」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：屋上のウワサ』の選択肢（気になるね）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[148].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_147_s4s_30_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 148 then
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
            vms(759, "NONVOICE", "『私じゃない』のあらすじを見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_147_s4s_30_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local card_12_s1s_100_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(638, "NONVOICE", "【彩野】「ユウイチの答案を、受け流す、か」")
    vms(639, "NONVOICE", "彩野さんは少し首を傾けた。")
    comPoseLoad("po2_aya_f_2_d")
    vms(640, "NONVOICE", "【彩野】「もうちょっと、ほかに反応って、ないかな」")
    vms(641, "NONVOICE", "【彩野】「ちょっとこれ、アヤノの反応としてもひどいような気がする」")
    comPoseLoad("po2_aya_f_2_a")
    vms(642, "NONVOICE", "【彩野】「って、私が言うのも変なんだけどね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(643, "NONVOICE", "【直哉】「はは。でももうちょっと、反応、ということは、ここももしかして、物語が分岐するかもしれないって事？」")
    vms(644, "NONVOICE", "【彩野】「そうかもしれない。直哉くん、さっきの『受け流す』場面のあらすじって、どうだったっけ？」")
    comPoseDelete()
end
local card_12_s1s_100_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(645, "NONVOICE", "【彩野】「そっか。こんなお話なんだ」")
    comPoseLoad("po2_aya_f_2_d")
    vms(646, "NONVOICE", "【彩野】「うーん。やっぱりちょっとひどいかな」")
    vms(647, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(648, "NONVOICE", "【彩野】「えっと。それじゃあ……」")
    vms(649, "NONVOICE", "【直哉】「なにか、お話、浮かんだ？」")
    vms(650, "NONVOICE", "【彩野】「うん。『受け流す』だとひどいから、その受け流すの正反対」")
    vms(651, "NONVOICE", "【直哉】「ということは……」")
    vms(652, "NONVOICE", "【彩野】「アヤノがユウイチを羨ましがる――という感じになるかな」")
    vms(653, "NONVOICE", "【直哉】「『羨ましがる』ね。わかった。じゃ、カードを作ってみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ユウイチの答案』の選択肢（羨ましがる）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[14].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_12_s1s_100_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 14 then
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
            vms(654, "NONVOICE", "【彩野】「うーん、なんで答案にあんな反応をしたんだろう……」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_12_s1s_100_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

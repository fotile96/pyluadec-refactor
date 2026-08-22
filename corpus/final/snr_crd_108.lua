local card_108_s6s_280_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_2_e")
    vms(515, "NONVOICE", "【直哉】「屋上で、アヤノさんは気が付くと屋上にいて……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(516, "NONVOICE", "【彩野】「直哉くん……」")
    vms(517, "NONVOICE", "【彩野】「もう一度、一番初めに直哉くんにつくってもらったカード、見せてもらっていい？」")
    vms(518, "NONVOICE", "【直哉】「一番初め……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(519, "NONVOICE", "【彩野】「うん。『ある子が学校にくる物語』だと思うんだ」")
    vms(520, "NONVOICE", "【直哉】「あ、うん……」")
    comPoseDelete()
end
local card_108_s6s_280_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(521, "NONVOICE", "【彩野】「でも……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(522, "NONVOICE", "【彩野】「……」")
    vms(523, "NONVOICE", "【直哉】「……彩野さん？」")
    vms(524, "NONVOICE", "【彩野】「…………」")
    comPoseLoad("po2_aya_f_1_a")
    vms(525, "NONVOICE", "【彩野】「直哉くん。ここは、『中庭に行く』展開も、あります」")
    vms(526, "NONVOICE", "【直哉】「あ、うん……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：屋上の帰り道』のあらすじを作成しました。")
    vms(527, "NONVOICE", "【彩野】「それで――」")
    vms(528, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(529, "NONVOICE", "【彩野】「それで、ごめんなさい、直哉くん」")
    vms(530, "NONVOICE", "【彩野】「この先が、最後の場面だから」")
    vms(531, "NONVOICE", "【彩野】「物語の終わり、だから」")
    vms(532, "NONVOICE", "【直哉】「彩野さん……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(533, "NONVOICE", "彩野さんは静かに首を横に振った。")
    vms(534, "NONVOICE", "【直哉】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[1].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[104].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_108_s6s_280_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 1 then
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
            vms(535, "NONVOICE", "『ある子が学校にくる物語』を、彩野さんに渡そう……。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_108_s6s_280_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2014, "NONVOICE", "【彩野】「『彼女』としていたこと……」")
    vms(2015, "NONVOICE", "【彩野】「約束……」")
    vms(2016, "NONVOICE", "【彩野】「直哉くん、もう一度、『約束』について、カードを見せて貰っていい？」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2017, "NONVOICE", "【彩野】「放課後の、約束」")
    vms(2018, "NONVOICE", "【直哉】「入院中……もしかしたら、この子は本当にいて、病弱な子なのかな」")
    vms(2019, "NONVOICE", "【直哉】「それだったら、僕は会わなかったのかもしれない」")
    vms(2020, "NONVOICE", "【彩野】「うん。滅多に学校に来なかった子、なのかも」")
    vms(2021, "NONVOICE", "【直哉】「彩野さんは、どう思った？」")
    vms(2022, "NONVOICE", "【彩野】「私は……」")
    vms(2023, "NONVOICE", "【直哉】「……」")
    vms(2024, "NONVOICE", "【彩野】「ごめんね。やっぱりよくわからない。でも……」")
    vms(2025, "NONVOICE", "【彩野】「ひとつ、感じる事はあるの」")
    vms(2026, "NONVOICE", "【直哉】「ん、なんだろう」")
    vms(2027, "NONVOICE", "【彩野】「彼女は、この物語にとって、重要なキャラクターだと思う。やっぱり」")
    vms(2028, "NONVOICE", "【直哉】「ふむ」")
    vms(2029, "NONVOICE", "【彩野】「ちょっと、特別な感じ、するもの」")
    vms(2030, "NONVOICE", "【直哉】「コックリさんの、彼女」")
    vms(2031, "NONVOICE", "【彩野】「うん」")
    vms(2032, "NONVOICE", "【直哉】「現実にいるかどうかはわからない」")
    vms(2033, "NONVOICE", "【直哉】「でも、似たような子がモチーフとなったのかもしれない。調べてみる価値はあるかもしれないね」")
    vms(2034, "NONVOICE", "彩野さんは、ゆっくりと頷いた。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『彼女との出会い』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[131].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    l0_0()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 131 then
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
            vms(2035, "NONVOICE", "【彩野】「二人はどうして出会ったんだろう……。『約束』。それを示すものって、あるかな」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_1()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

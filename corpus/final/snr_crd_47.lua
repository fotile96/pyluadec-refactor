local card_47_s2s_250_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2779, "NONVOICE", "【彩野】「教室の中で話した後、サクラさんにオマジナイを聞きに行く場面」")
    vms(2780, "NONVOICE", "【直哉】「ここの教室の場面、セクション１も似たような感じに、茶化されたところがあったかな」")
    vms(2781, "NONVOICE", "【彩野】「え？ そうなの？」")
    vms(2782, "NONVOICE", "【直哉】「えっとね、確か『朝の教室』の場面に……」")
    comPoseDelete()
end
local card_47_s2s_250_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2783, "NONVOICE", "【彩野】「朝の教室……夫婦喧嘩……」")
    vms(2784, "NONVOICE", "【彩野】「でも、私たち、実際にはクラスでこんな事は言われてなかったよね？」")
    vms(2785, "NONVOICE", "【直哉】「……そうだったと思う」")
    vms(2786, "NONVOICE", "【彩野】「私、思うんだけど、この物語の『アヤノ』は、物語として誇張してる部分はあるよ」")
    vms(2787, "NONVOICE", "【直哉】「うん……」")
    vms(2788, "NONVOICE", "【彩野】「オマジナイ、とか。やっぱり違うなって、思うもん」")
    vms(2789, "NONVOICE", "【彩野】「どうしてこんな風になってるんだろう……」")
    comPoseLoad("po2_aya_f_1_d")
    vms(2790, "NONVOICE", "【彩野】「……直哉くん、聞いてる？」")
    vms(2791, "NONVOICE", "【直哉】「あ……う、うん。ごめん。あらすじカードをつくるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『図書室』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_1_c")
    vms(2792, "NONVOICE", "【彩野】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[9].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_47_s2s_250_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 9 then
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
            vms(2793, "NONVOICE", "『朝の教室』のあらすじを彩野さんに見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_47_s2s_250_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

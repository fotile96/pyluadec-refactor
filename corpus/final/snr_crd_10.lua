local card_10_s1s_80_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(283, "NONVOICE", "【直哉】「セクション１，というのが、どうやらこの物語の区切りを意味するみたいだね」")
    vms(284, "NONVOICE", "【彩野】「たぶん、そうだと思う。第一章とか、第一幕とか、そういう区切り」")
    vms(285, "NONVOICE", "【直哉】「セクション『１』。ということは、セクション２も３もあるかもしれない」")
    vms(286, "NONVOICE", "【彩野】「……うん」")
    vms(287, "NONVOICE", "【直哉】「あとは、これまでの展開を見ていると、舞台となるのはやっぱりこの場所。――学校だと思う」")
    vms(288, "NONVOICE", "【彩野】「うん――」")
    comPoseDelete()
end
local card_10_s1s_80_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(289, "NONVOICE", "【彩野】「教室が舞台、なのかな」")
    vms(290, "NONVOICE", "【直哉】「その可能性は、やっぱり高いと思う。典型的……と言ってしまうとちょっと失礼だね。ごめんなさい」")
    vms(291, "NONVOICE", "【彩野】「ううん。私もそう思う。なんというか、典型的なお決まりのフォーマット。学園もの、みたいな」")
    vms(292, "NONVOICE", "【直哉】「うん、言ってしまえばそんな感じのお話だった」")
    comSectionCardFlagIn(126, false)
    vms(293, "NONVOICE", "【直哉】「あと、もう一つ」")
    vms(294, "NONVOICE", "【直哉】「もしかしたら、この物語の主人公は、彩野さん……『アヤノ』さんなのかもしれない」")
    vms(295, "NONVOICE", "彩野さんはコクリと頷いた。")
    vms(296, "NONVOICE", "【彩野】「そんな気がする。アヤノの主観の方が、つくりやすいかも」")
    comSectionCardFlagOut(126, false)
    comPoseLoad("po2_aya_f_2_a")
    vms(297, "NONVOICE", "【彩野】「って、自分で言うのも変な話なんだけど」")
    vms(298, "NONVOICE", "【直哉】「主観。あ、そっか。これまでは三人称だったもんね」")
    vms(299, "NONVOICE", "【直哉】「次からはアヤノさんの視点で、物語を進めてみようか」")
    comPoseLoad("po2_aya_f_1_a")
    vms(300, "NONVOICE", "【彩野】「うん。ちょっと、なんか、へんな感じだね。自分の事って」")
    vms(301, "NONVOICE", "【直哉】「ふふ。僕もなんだか、楽しいよ、懐かしくて。ちょっとした、舞台みたいな」")
    comPoseLoad("po2_aya_f_1_e")
    vms(302, "NONVOICE", "【彩野】「演劇っぽいかもね、確かに」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『セクション１：アヤノ』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[126].hold = 1
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
    card_10_s1s_80_intro()
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
            vms(303, "NONVOICE", "【彩野】「今、私たちのいる場所……」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_10_s1s_80_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(537, "NONVOICE", "【彩野】「お昼休みに話していたこと、コックリさん……」")
    vms(538, "NONVOICE", "【直哉】「彩野さんは、やったことがあるの？」")
    vms(539, "NONVOICE", "【彩野】「それが、よくわからないの」")
    vms(540, "NONVOICE", "【彩野】「でもこんな風にお話を書いたって事は、昔やったことがあったのかもしれないけど……」")
    vms(541, "NONVOICE", "【直哉】「はっきりしない、感じ」")
    vms(542, "NONVOICE", "【彩野】「そう、なの。ごめんなさい」")
    vms(543, "NONVOICE", "【直哉】「いや、そんな。あやまることなんて」")
    vms(544, "NONVOICE", "【彩野】「でも、確か――『約束』だったかな？」")
    vms(545, "NONVOICE", "【直哉】「約束？」")
    vms(546, "NONVOICE", "【彩野】「そう、放課後に……、えっと、誰かとしていた約束」")
    vms(547, "NONVOICE", "【直哉】「うん。そうだね。そういう部分が最初にあった」")
    vms(548, "NONVOICE", "【彩野】「あの『約束』についてって、最初に感じていたこと――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(549, "NONVOICE", "【彩野】「そう……。『思い出せない』」")
    vms(550, "NONVOICE", "【彩野】「その感覚と、似ているのかも。コックリさんをしていたのかどうか、わからない感覚って」")
    vms(551, "NONVOICE", "【直哉】「なんだろう。思い出せそうで思い出せない、そんな感じなのかな」")
    vms(552, "NONVOICE", "彩野さんはコクリと頷いた。")
    vms(553, "NONVOICE", "【彩野】「そう。言葉にすると、そんな感じ」")
    comPoseLoad("po2_aya_f_2_e")
    vms(554, "NONVOICE", "【彩野】「それで、このシーンでアヤノは、ユウイチをコックリさんに誘っているんだよね……うーん……」")
    vms(555, "NONVOICE", "【直哉】「まあ、このことはとりあえず、おいておこう」")
    comPoseLoad("po2_aya_f_1_c")
    vms(556, "NONVOICE", "【彩野】「うん……コックリさんか……なんなんだろう」")
    vms(557, "NONVOICE", "彩野さんはそういうと、小さくため息をついた。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『昼休みの教室』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[6].hold == -1 then
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
        if l1_3 == 6 then
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
            vms(558, "NONVOICE", "【彩野】「一番初め『約束』についてはどう感じていたっけ？」")
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

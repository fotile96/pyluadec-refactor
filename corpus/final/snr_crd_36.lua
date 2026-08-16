local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2547, "NONVOICE", "【直哉】「ここから、セクション２の物語が始まる、ということかな」")
    vms(2548, "NONVOICE", "【彩野】「うん。そうだと思う。セクション２……。第二章という感じ」")
    vms(2549, "NONVOICE", "【直哉】「あ、それじゃあ――」")
    vms(2550, "NONVOICE", "セクション２ということは、この物語もやっぱりアヤノさんが学校の中を巡る感じの物語になるのだろうか？")
    vms(2551, "NONVOICE", "一応、念のため確認しておこう。僕は彩野さんに、『物語の主人公』のカードを見せることにした。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2552, "NONVOICE", "【直哉】「この物語の主人公も、やっぱり？」")
    vms(2553, "NONVOICE", "【彩野】「うん。アヤノだと思う。このセクションでは」")
    vms(2554, "NONVOICE", "【直哉】「『このセクションでは』？ それじゃあ、もしかしてアヤノさん以外の人物も主人公になるかもしれない、ということ？」")
    vms(2555, "NONVOICE", "【彩野】「たぶん……だけど。その可能性は高いって思うの」")
    vms(2556, "NONVOICE", "【彩野】「私、『この部分の主人公はアヤノだな』って。そんな風に書いていたような気がする」")
    vms(2557, "NONVOICE", "【直哉】「となると、ユウイチやサクラさんにも可能性があるということかな……。物語の主要な人物から考えると」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2558, "NONVOICE", "【彩野】「そうかも……でも、今は……。他の展開まではちょっと思い浮かばないの。ごめんなさい」")
    vms(2559, "NONVOICE", "【直哉】「あ、ううん。もちろん了解。ゆっくり考えよう。とりあえず、このセクションを最後まで進んでみてから、だね」")
    vms(2560, "NONVOICE", "【直哉】「そしたら、また、セクション１の時みたいに新しい展開が浮かぶかもしれないから」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2561, "NONVOICE", "【彩野】「……うん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『セクション２：アヤノ』のカードを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[126].hold == -1 then
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
        if l1_3 == 126 then
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
            vms(2562, "NONVOICE", "彩野さんに、『物語の主人公』のカードを見せてみよう。")
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

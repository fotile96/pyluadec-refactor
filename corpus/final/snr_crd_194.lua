local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_2_e")
    vms(1763, "NONVOICE", "【彩野】「直哉くん、ここなんだけど――」")
    vms(1764, "NONVOICE", "【彩野】「ちょっと、他とは違う感じがするの」")
    vms(1765, "NONVOICE", "【直哉】「違う感じ？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1766, "NONVOICE", "【彩野】「うん。なんて言えばいいのかな……」")
    vms(1767, "NONVOICE", "【彩野】「物語でもあるけど、物語でもない感じ……かな」")
    vms(1768, "NONVOICE", "【直哉】「うーん……それは……」")
    comPoseLoad("po2_aya_f_2_d")
    vms(1769, "NONVOICE", "【彩野】「あ……説明が下手で、ごめんね」")
    vms(1770, "NONVOICE", "【直哉】「そんな事は……。僕の方こそ、上手く汲み取れなくて……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1771, "NONVOICE", "【彩野】「うーん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1772, "NONVOICE", "【彩野】「直哉くん、ごめんね。ちょっと、サクラさんの日記を、見せてもらっていい？」")
    vms(1773, "NONVOICE", "【直哉】「どの日記にする？」")
    vms(1774, "NONVOICE", "【彩野】「えっと、セクション５に入って、物語として辿ってきた日記でいいと思う」")
    vms(1775, "NONVOICE", "【直哉】「となると、『サクラの日記：９月１３日』と――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerNonvoiceTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1776, "NONVOICE", "【直哉】「『サクラの日記：７月（書きかけ）』だね――」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(1777, "NONVOICE", "【彩野】「……うん」")
    vms(1778, "NONVOICE", "【彩野】「……そうだ……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1779, "NONVOICE", "【彩野】「えっとね、直哉くん。ここの部分、『現実』に、私とサクラさんが病院で会話した内容だよ」")
    vms(1780, "NONVOICE", "【直哉】「サクラさんと、彩野さんの……現実の会話」")
    vms(1781, "NONVOICE", "【彩野】「うん。この日記を読んではっきりしたんだ」")
    vms(1782, "NONVOICE", "【彩野】「『物語』では、サクラさんは私と同じ高校だけど――」")
    vms(1783, "NONVOICE", "【彩野】「『現実』では、サクラさんは１３歳で――」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1784, "NONVOICE", "【彩野】「こんな風に話してたの。私たち」")
    vms(1785, "NONVOICE", "【彩野】「それじゃあ……ここの部分のあらすじ、つくるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『中庭のアヤノさん』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_1_c")
    vms(1786, "NONVOICE", "【彩野】「どうしてこの部分、私も『浮かばなかった』のか、わからないけど……」")
    vms(1787, "NONVOICE", "【直哉】「……サクラさんの日記と、屋上の『いつかきみがみるお話。』が関係しているのかな？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1788, "NONVOICE", "【彩野】「たぶん、そうなんだと思う」")
    vms(1789, "NONVOICE", "【彩野】「……でも、とにかく今は、あれこれ考えるより、サクラさんの『物語』をつくりたいなって思うんだ」")
    comPoseLoad("po2_aya_f_1_e")
    vms(1790, "NONVOICE", "【彩野】「せっかくお話のタネがあるんだから、ね」")
    vms(1791, "NONVOICE", "【直哉】「うん。僕からもお願いするよ」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[179].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[180].hold == -1 then
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
        if l1_3 == 179 then
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
            vms(1792, "NONVOICE", "サクラの日記：９月１３日を渡そう。")
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
    local l1_3 = 0
    local l1_4 = 0
    local l1_5 = -1
    while l1_3 < 1 do
        local l1_6 = oCard.selectCardObj()
        if l1_6 == 180 then
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
            vms(1793, "NONVOICE", "サクラの日記：７月（書きかけ）を渡そう。")
            comPoseDelete()
        end
        if l1_4 == 0 then
            oCard.mesNG()
            l1_4 = l1_4 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_2()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

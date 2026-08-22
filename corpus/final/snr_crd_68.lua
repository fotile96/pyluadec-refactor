local card_68_s3s_100_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3244, "NONVOICE", "【直哉】「ここの部分の展開は、またまた『いつもの生活』だね」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3245, "NONVOICE", "【彩野】「『またまた』？」")
    vms(3246, "NONVOICE", "【彩野】「えっとじゃあ、この展開は他にも出てきた、と言うこと？」")
    vms(3247, "NONVOICE", "【直哉】「うん。そうなんだ」")
    vms(3248, "NONVOICE", "【直哉】「まずはセクション１の『いつもの生活』」")
    comPoseDelete()
end
local card_68_s3s_100_resolve = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3249, "NONVOICE", "【彩野】「ふむ、なるほど……」")
    vms(3250, "NONVOICE", "【直哉】「そして……これがセクション２の『また、いつもの生活』」")
    comPoseDelete()
end
local card_68_s3s_100_step3 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3251, "NONVOICE", "【彩野】「そうなんだ……いろんな物語で出てきているんだね、この場面」")
    vms(3252, "NONVOICE", "【直哉】「それでね。この場面が出てきたときは、中途半端な所で物語が終わっちゃう……」")
    vms(3253, "NONVOICE", "【直哉】「要するに、バッドエンド、になるのかな」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3254, "NONVOICE", "【彩野】「ふむふむ……」")
    vms(3255, "NONVOICE", "【直哉】「逆に考えるとね、この場面が展開されるときは、その前の部分の選択肢が重要になる――」")
    vms(3256, "NONVOICE", "【直哉】「つまり、『新しい物語を展開する』ための目印みたいなものかなって、僕は考えてる」")
    comPoseLoad("po2_aya_f_2_b")
    vms(3257, "NONVOICE", "【彩野】「日常を脱する、ということ？」")
    vms(3258, "NONVOICE", "【直哉】「うん。僕はそう思ってる……って、勝手に解釈しちゃってるけど」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3259, "NONVOICE", "【彩野】「ううん。ありがとう。そっか。なるほどね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3260, "NONVOICE", "【彩野】「じゃあ、やっぱり、この場面でも……」")
    vms(3261, "NONVOICE", "【直哉】「うん。前の場面の『選択』が重要なんじゃないかなって、思ってる」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ウワサに興味がない』のあらすじを作成しました。")
    vms(3262, "NONVOICE", "【彩野】「日常を脱すること……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3263, "NONVOICE", "【彩野】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[19].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[31].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_68_s3s_100_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 19 then
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
            vms(3264, "NONVOICE", "セクション１の『いつもの生活』のあらすじを彩野さんに見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_68_s3s_100_resolve()
    local l1_3 = 0
    local l1_4 = 0
    local l1_5 = -1
    while l1_3 < 1 do
        local l1_6 = oCard.selectCardObj()
        if l1_6 == 31 then
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
            vms(3265, "NONVOICE", "セクション２の『また、いつもの生活』のあらすじを彩野さんに見せてみよう。")
            comPoseDelete()
        end
        if l1_4 == 0 then
            oCard.mesNG()
            l1_4 = l1_4 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_68_s3s_100_step3()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

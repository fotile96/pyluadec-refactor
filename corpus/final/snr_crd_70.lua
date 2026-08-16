local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3319, "NONVOICE", "【直哉】「サクラさんから聞いた階段のウワサについて、クラスのみんなに聞いてみる場面なんだけど……」")
    vms(3320, "NONVOICE", "【直哉】「実はね、彩野さん」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3321, "NONVOICE", "【彩野】「え、どうかした？」")
    vms(3322, "NONVOICE", "【直哉】「ここの場面なんだけど、『適当に聞く』『とりあえず聞いてみる』どちらを考えても、似たような展開になっちゃうんだ」")
    vms(3323, "NONVOICE", "【彩野】「ふむ……そうなんだ」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3324, "NONVOICE", "【彩野】「似たような、展開……」")
    vms(3325, "NONVOICE", "【直哉】「あ、ごめんね。まずはあらすじのカードを見てもらった方が早いと思う」")
    vms(3326, "NONVOICE", "【直哉】「まずは、『適当に聞く』方の展開――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_2_d")
    vms(3327, "NONVOICE", "【彩野】「はは、適当に、ね……」")
    vms(3328, "NONVOICE", "【直哉】「次に『とりあえず聞いてみる』のはこんなあらすじ」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3329, "NONVOICE", "【彩野】「ふむ……」")
    comPoseLoad("po2_aya_f_2_d")
    vms(3330, "NONVOICE", "【彩野】「うーん、どちらも相手にしてもらえない感じだね」")
    vms(3331, "NONVOICE", "【直哉】「それで、ちょっと思ったんだけど、他の『物語』でもやっぱり同じような事があったんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3332, "NONVOICE", "【彩野】「同じような事って、展開が？」")
    vms(3333, "NONVOICE", "【直哉】「えっとね。つまり、お話を聞く態度の問題として」")
    vms(3334, "NONVOICE", "【直哉】「相手から話題を振られて、その反応――」")
    vms(3335, "NONVOICE", "【彩野】「話をされたら、ふざけてないで、真剣に聞く、という感じ？」")
    vms(3336, "NONVOICE", "【直哉】「そうそう、そんな感じ。結局これは、お話に対しての取り組みを示しているのかなって」")
    vms(3337, "NONVOICE", "【彩野】「そっか……ふむ。ありがとう、直哉くん」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3338, "NONVOICE", "【彩野】「となると、ここは展開を追加した方がいいみたいだね」")
    vms(3339, "NONVOICE", "【彩野】「えっと、『選択肢』だっけ？ カードを作ってもらっていい？」")
    vms(3340, "NONVOICE", "【直哉】「うん。どんなカード？」")
    vms(3341, "NONVOICE", "【彩野】「やっぱり、『真剣に聞く』が、いいと思う」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ウワサ話を……』の選択肢（真剣に聞く）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[71].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[72].hold == -1 then
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
        if l1_3 == 71 then
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
            vms(3342, "NONVOICE", "『適当に聞く』のカードを見せてみよう。")
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
        if l1_6 == 72 then
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
            vms(3343, "NONVOICE", "『とりあえず聞いてみる』のカードを見せてみよう。")
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

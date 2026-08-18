local card_67_s3s_90_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3212, "NONVOICE", "階段のウワサ、か。")
    vms(3213, "NONVOICE", "【直哉】「そういえば――」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3214, "NONVOICE", "【彩野】「うん？ どうかしたの、直哉くん」")
    vms(3215, "NONVOICE", "【直哉】「あっ、ごめんね。ここの階段の話なんだけど、セクション１にも少し出てきたなって思ったんだ」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3216, "NONVOICE", "【彩野】「セクション１……」")
    vms(3217, "NONVOICE", "【直哉】「あ、えっとね。この物語じゃない、他の物語で」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3218, "NONVOICE", "【彩野】「他の物語……そうなんだ」")
    vms(3219, "NONVOICE", "【直哉】「うん。ちょっと待って、その部分を解説したカードは――」")
    vms(3220, "NONVOICE", "確か、放課後学校を探索するときに……。")
    comPoseDelete()
end
local card_67_s3s_90_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3221, "NONVOICE", "【彩野】「そっか、ホコリっぽくて、『いわく』つきの階段……」")
    vms(3222, "NONVOICE", "【直哉】「それで、この階段の部分の描写は、『現実』の学校と似ているなって」")
    comPoseLoad("po2_aya_f_1_e")
    vms(3223, "NONVOICE", "【彩野】「うん。確かにそんな感じ。お化け階段だね」")
    vms(3224, "NONVOICE", "うん。")
    vms(3225, "NONVOICE", "屋上に出るために通る必要がある階段――")
    vms(3226, "NONVOICE", "通称『お化け階段』。校舎の隅に位置し、太陽の光もあまり差さないその階段は、以前より生徒達からウワサ話が立ち上がる格好の標的となっていた。")
    vms(3227, "NONVOICE", "いわく、この階段の方から人のうめき声が聞こえる、登る度に階段の数が合わない、怪しい人影が見えた、等々……。")
    comPoseLoad("po2_aya_f_1_a")
    vms(3228, "NONVOICE", "【直哉】「でも、あの場所っていつからそんなウワサが立つようになったんだろう」")
    vms(3229, "NONVOICE", "【彩野】「……うーん。わからないなあ。でも、相当昔からだと思うよ。小さい頃も聞いた記憶があるんだ」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3230, "NONVOICE", "【彩野】「ちょっとね、私もあそこは、嫌な感じ、するんだ」")
    vms(3231, "NONVOICE", "【直哉】「あ、そうなんだ……」")
    vms(3232, "NONVOICE", "【彩野】「うん、なんかね、背筋がゾクッとするって言うか――」")
    vms(3233, "NONVOICE", "【直哉】「ふむ……」")
    comPoseLoad("po2_aya_f_2_c")
    vms(3234, "NONVOICE", "【彩野】「あ、そっか！」")
    vms(3235, "NONVOICE", "【直哉】「ん？ なにかあった？」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3236, "NONVOICE", "【彩野】「えっとね。分岐、させようかなと思って。今の、この――お化け階段」")
    vms(3237, "NONVOICE", "【直哉】「階段を……」")
    vms(3238, "NONVOICE", "【彩野】「うん。なんかね。私も階段から何かお話が浮かびそうな気がする。だから、それを展開させてみようかなって」")
    vms(3239, "NONVOICE", "【直哉】「ふむ。ここの部分って、現実とリンクしてるみたいだからね……」")
    vms(3240, "NONVOICE", "【直哉】「階段。何か、彩野さんに思うところはあったのかもしれないね」")
    vms(3241, "NONVOICE", "【直哉】「それじゃ、カードをつくるね」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3242, "NONVOICE", "【彩野】「うん。お願い」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ウワサとは』の選択肢（お化け階段）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[20].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[65].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_67_s3s_90_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 20 then
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
            vms(3243, "NONVOICE", "セクション1で、放課後、学校を探索したときの場面のあらすじを彩野さんに説明してみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_67_s3s_90_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

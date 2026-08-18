local card_89_s3s_650_step8 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(3702, "NONVOICE", "【彩野】「うーん……」")
    vms(3703, "NONVOICE", "【彩野】「直哉くん……」")
    vms(3704, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(3705, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(3706, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3707, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3708, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(3709, "NONVOICE", "ということは、この『まとめ』では続いて正解のカードを選ぶ必要がある――つまり、途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(3710, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local card_89_s3s_650_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3711, "NONVOICE", "【直哉】「セクション３、アヤノさんとユウイチが屋上で過ごすシーン」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3712, "NONVOICE", "【彩野】「……」")
    vms(3713, "NONVOICE", "【直哉】「ここで、セクション３は終わりだね」")
    vms(3714, "NONVOICE", "【直哉】「……」")
    vms(3715, "NONVOICE", "【直哉】「ここまでの物語を、まとめてもいいかな？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3716, "NONVOICE", "【彩野】「あ、うん……」")
    vms(3717, "NONVOICE", "【直哉】「この物語は、お昼休みにサクラさんから学校のある場所の『ウワサ』を聞いたところから始まったんだ」")
    comPoseDelete()
end
local card_89_s3s_650_resolve = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3718, "NONVOICE", "【彩野】「階段の、ウワサ……」")
    vms(3719, "NONVOICE", "【直哉】「そう、階段のウワサ話を聞いたアヤノさんは、クラスメイトからも詳しい話を聞くことにした」")
    vms(3720, "NONVOICE", "【直哉】「階段は、通称『――階段』と呼ばれていた」")
    comPoseDelete()
end
local card_89_s3s_650_step3 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3721, "NONVOICE", "【彩野】「お化け階段……階段のウワサ……」")
    vms(3722, "NONVOICE", "【直哉】「アヤノさんはクラスメイトから聞いた情報を元に、学校内を探索して先生達からも話を聞くことにした」")
    vms(3723, "NONVOICE", "【直哉】「この事を示す場面が――」")
    comPoseDelete()
end
local card_89_s3s_650_step4 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3724, "NONVOICE", "【彩野】「保健室の先生……直哉くん、この先生って……」")
    vms(3725, "NONVOICE", "【直哉】「そう。『現実には存在していない』先生。恐らく、彩野さんの創作ということになるね」")
    vms(3726, "NONVOICE", "【彩野】「創作……」")
    vms(3727, "NONVOICE", "【直哉】「それで、ウワサについて調べている途中、アヤノさんはユウイチを見かけたんだ」")
    vms(3728, "NONVOICE", "【直哉】「ここで『物語を進行させるための展開』は、ユウイチを――」")
    comPoseDelete()
end
local card_89_s3s_650_step5 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_2_d")
    vms(3729, "NONVOICE", "【彩野】「はは、ほうっておいちゃうんだね……」")
    vms(3730, "NONVOICE", "【直哉】「うん。校庭にいる『きくちゃん』にウワサを聞く方が優先って」")
    vms(3731, "NONVOICE", "【直哉】「ウワサをきくちゃんに聞く。そのことを示す場面が――」")
    comPoseDelete()
end
local card_89_s3s_650_step6 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(3732, "NONVOICE", "【彩野】「きくちゃん……」")
    vms(3733, "NONVOICE", "【直哉】「きくちゃんからウワサを聞き終わり、アヤノさんはウワサの出所の階段へと向かった」")
    vms(3734, "NONVOICE", "【直哉】「途中、アヤノさんはユウイチと合流して、階段の調査を始めた。その場面が――」")
    comPoseDelete()
end
local card_89_s3s_650_step7 = function()
    oCard.cardAnswerNonvoiceTrue()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_1_a")
    vms(3735, "NONVOICE", "【彩野】「……」")
    vms(3736, "NONVOICE", "【直哉】「階段を調べている途中、ふざけたユウイチに怒ったアヤノさんだったけれど、身体を動かした時にバランスを崩し――」")
    vms(3737, "NONVOICE", "【直哉】「ユウイチと抱き合う形になってしまう」")
    vms(3738, "NONVOICE", "【直哉】「その時、アヤノさんは思ったんだ。ユウイチと――」")
    comPoseDelete()
end
local card_89_s3s_650_step9 = function()
    oCard.cardAnswerNonvoiceTrue()
    vms(3739, "NONVOICE", "【直哉】「そして、アヤノさんはユウイチと一緒に屋上に行った」")
    vms(3740, "NONVOICE", "【直哉】「屋上からは花火が上がっているのが見えた」")
    vms(3741, "NONVOICE", "【直哉】「二人は『手を握り合った』」")
    vms(3742, "NONVOICE", "【直哉】「……ここまでが、セクション３だね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3743, "NONVOICE", "【彩野】「でも直哉くん、これは物語で――」")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_14_x"))
    vms(3744, "NONVOICE", "【直哉】「『本当にユウイチと屋上に行ったわけじゃない』でしょ。わかってる。既に聞いたよ。彩野さんは覚えてないかもしれないけれど」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3745, "NONVOICE", "【彩野】「う……あ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3746, "NONVOICE", "【彩野】「……直哉くん……」")
    vms(3747, "NONVOICE", "【直哉】「あ……」")
    vms(3748, "NONVOICE", "【彩野】「……」")
    vms(3749, "NONVOICE", "【直哉】「ご、ごめん、何言ってるんだ僕は……」")
    vms(3750, "NONVOICE", "彩野さんは黙って首を横に振る。")
    vms(3751, "NONVOICE", "【直哉】「……ごめんなさい」")
    vms(3752, "NONVOICE", "【彩野】「……」")
    vms(3753, "NONVOICE", "【直哉】「……彩野さん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3754, "NONVOICE", "【彩野】「な……おやくんは……」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3755, "NONVOICE", "【彩野】「謝らなくていいよ。私の記憶、無くなるから」")
    vms(3756, "NONVOICE", "【直哉】「……彩野さん……」")
    comPoseLoad("po2_aya_f_1_e")
    vms(3757, "NONVOICE", "【彩野】「気にしなくて、大丈夫だから」")
    vms(3758, "NONVOICE", "そう言って、彩野さんは力なく笑う。")
    vms(3759, "NONVOICE", "【彩野】「あらすじ、お願いします。もうこれで、この物語は終わりだから」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ユウイチとキス』のあらすじを作成しました。")
    comPoseDelete()
    vms(3760, "NONVOICE", "【直哉】「……」")
    vms(3761, "NONVOICE", "……。")
    vms(3762, "NONVOICE", "……僕は……")
    vms(3763, "NONVOICE", "何を、言ってるんだ……。")
    vms(3764, "NONVOICE", "彩野さんに……。")
    vms(3765, "NONVOICE", "……。")
    comSectionCardEndSection()
    doScriptScene = "s3fa-10"
    run(cGetFileName("script", "snr_s3_10_fa"))
    quit()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[64].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[69].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[74].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[76].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[77].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[86].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[88].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[68].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[84].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    local l1_0 = false
    card_89_s3s_650_intro()
    local l1_1 = 0
    local l1_2 = 0
    local l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 64 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3766, "NONVOICE", "この物語は、『お昼休みの廊下』にサクラさんから学校のある場所の『ウワサ』を聞いたところから始まった。")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_89_s3s_650_resolve()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 69 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3767, "NONVOICE", "階段は、通称、『お化け――』")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_89_s3s_650_step3()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 74 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3768, "NONVOICE", "階段のウワサについて、『学校内を探索』して、『先生達に話を聞いた』場面は――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_89_s3s_650_step4()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 76 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3769, "NONVOICE", "ここで『物語を進行させるための展開』は、ユウイチを放って――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_89_s3s_650_step5()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 77 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3770, "NONVOICE", "ウワサをきくちゃんに聞く。きくちゃんは陸上部に入っていたから――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_89_s3s_650_step6()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 86 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3771, "NONVOICE", "アヤノさんは、『ユウイチと階段に行って』調査を始めた。")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_89_s3s_650_step7()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 88 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3772, "NONVOICE", "ユウイチと抱き合う形になってしまったアヤノさんは思ったんだ。ユウイチと、『ずっと――』")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    if l1_0 == true then
        card_89_s3s_650_step8()
    end
    card_89_s3s_650_step9()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

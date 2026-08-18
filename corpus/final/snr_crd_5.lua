local card_5_s1s_36_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2828, "NONVOICE", "【直哉】「消しゴムを落として、拾った時に『放課後の約束』を思い出す、か」")
    vms(2829, "NONVOICE", "【直哉】「消しゴムを落とす前にアヤノさんが考えていた『クラスの子』って、『約束を思い出せない』で出てきたクラスメイトの事かな？」")
    vms(2830, "NONVOICE", "【彩野】「クラスメイト？ 女の子？」")
    vms(2831, "NONVOICE", "【直哉】「あ、うん。そうだよ」")
    vms(2832, "NONVOICE", "【彩野】「えっと……直哉くん。その子の名前って、わかる？」")
    vms(2833, "NONVOICE", "クラスメイトの、名前――")
    comPoseDelete()
end
local card_5_s1s_36_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2834, "NONVOICE", "【直哉】「『きくちゃん』さんについて、なにかわかる？」")
    vms(2835, "NONVOICE", "彩野さんは首を横に振った。")
    vms(2836, "NONVOICE", "【彩野】「……ごめんなさい。考えてみたけど、全然わからないの」")
    vms(2837, "NONVOICE", "【直哉】「そう、わからないんだ……」")
    vms(2838, "NONVOICE", "【直哉】「……うん。僕も昔の記憶だから、あまりはっきりはしないけど……」")
    vms(2839, "NONVOICE", "【直哉】「うちのクラスに、こういうニックネームで呼ばれてた子は……ちょっと思い浮かばないな」")
    vms(2840, "NONVOICE", "【彩野】「……」")
    vms(2841, "NONVOICE", "【直哉】「でも、愛称で呼んでるんだから結構親しい事になるよね」")
    vms(2842, "NONVOICE", "【直哉】「僕が知らなくて彩野さんが知っている子だとしても、人物は限られてくると思うんだ。『きく』がつく子」")
    vms(2843, "NONVOICE", "【直哉】「名字が菊川、菊池、菊田……名前が菊子……菊三……うーん……」")
    vms(2844, "NONVOICE", "【彩野】「ごめんね、全然浮かばなくて」")
    vms(2845, "NONVOICE", "【直哉】「そんな、気にしなくてもいいよ」")
    vms(2846, "NONVOICE", "【直哉】「もしかしたら、この子は物語に出てくる『群衆』扱いなのかもしれない」")
    vms(2847, "NONVOICE", "【直哉】「だから、もしまた後で『物語』にこの子の名前が出てきたら……」")
    vms(2848, "NONVOICE", "【直哉】「それはその時に考えればいいんじゃないかな。何度も出てきたら、この子が物語にとって意味があるという事になる。その時に考えればいいよ」")
    vms(2849, "NONVOICE", "【彩野】「自分が考えてた事なのに……」")
    vms(2850, "NONVOICE", "【直哉】「彩野さんが気にする必要はないよ。今は『そういう状態』なんだ。物語も、彩野さんも」")
    vms(2851, "NONVOICE", "【直哉】「だから今は今で僕たちでできる事をやろう。流れに身を任せよう」")
    vms(2852, "NONVOICE", "彩野さんは小さく頷く。")
    vms(2853, "NONVOICE", "僕はカードに『あらすじ』を書いた。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『約束をしている』のあらすじを作成しました。")
    vms(2854, "NONVOICE", "【直哉】「この場面のあらすじができたよ」")
    vms(2855, "NONVOICE", "【彩野】「……直哉くん」")
    vms(2856, "NONVOICE", "【直哉】「さ、次の場面について、考えてみよう。まだまだ、物語は続きそうだから」")
    vms(2857, "NONVOICE", "【彩野】「……うん」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[129].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_5_s1s_36_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 129 then
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
            vms(2858, "NONVOICE", "【彩野】「……この場面以外のところで、誰かの名前を呼んでいたと思う」")
            vms(2859, "NONVOICE", "【彩野】「その子の『愛称』って――」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_5_s1s_36_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

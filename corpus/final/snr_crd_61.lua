local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3083, "NONVOICE", "【彩野】「セクション２は、これで終わりなんだね」")
    vms(3084, "NONVOICE", "【直哉】「このセクションの物語も、まとめてみた方がいいかな」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3085, "NONVOICE", "【彩野】「まとめる？」")
    vms(3086, "NONVOICE", "【直哉】「うん。ここまで聞いた物語を、まとめてみるって感じ」")
    vms(3087, "NONVOICE", "【直哉】「セクション１……ほかの『物語』でも最後に、それまでの出来事を『まとめ』てみたんだ」")
    comPoseLoad("po2_aya_f_1_e")
    vms(3088, "NONVOICE", "【彩野】「そうなんだ。うん。いいアイデアだね」")
    vms(3089, "NONVOICE", "【直哉】「それで、このセクション２なんだけど……」")
    vms(3090, "NONVOICE", "【直哉】「実は物語の途中でもいったん『まとめて』いるから、まずはこのカードを見てもらった方がいいと思う」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3091, "NONVOICE", "【彩野】「うん。どんなカード？」")
    vms(3092, "NONVOICE", "『夜の廊下』のあらすじをまとめるときに、場面にたどり着くまでの分岐点をメモしてある。")
    vms(3093, "NONVOICE", "途中の分岐も複雑だったし、まずはこのカードに目を通してもらうのが一番わかりやすいだろう。")
    vms(3094, "NONVOICE", "僕は彩野さんにカードを渡すことにした。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3095, "NONVOICE", "【彩野】「ふむ……。なるほど、いろんな分岐があったんだね」")
    vms(3096, "NONVOICE", "【直哉】「それと、もう一つ。この場面をまとめた後にわかったこと」")
    vms(3097, "NONVOICE", "【直哉】「物語の開始の時に、アヤノさんはユウイチに対してプールに行くことを提案していたんだけど、もう一ヵ所、行きたい場所があったんだ」")
    vms(3098, "NONVOICE", "【直哉】「その場面に行ったときのあらすじがこれだよ」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_e")
    comPoseLoad("po2_aya_f_2_e")
    vms(3099, "NONVOICE", "【彩野】「でも、プラネタリウムって……どうしてだろう？」")
    vms(3100, "NONVOICE", "【直哉】「それは、まだわからない。でも、プラネタリウムという言葉は、セクション１にも出てきたんだ」")
    vms(3101, "NONVOICE", "【直哉】「この『プラネタリウム』は、そのセクション１のあらすじをみて、彩野さんが思い浮かべた場所だったんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3102, "NONVOICE", "【彩野】「セクション１……他の物語にも？」")
    vms(3103, "NONVOICE", "【直哉】「うん。これは単語が『繋がっている』ということになるね」")
    vms(3104, "NONVOICE", "【彩野】「何か……『意味』があるかもしれない、ということ？」")
    vms(3105, "NONVOICE", "【直哉】「うん……。少なくとも、無意味であるとは思えない。それと、もう一つ、知っておいて欲しいこと」")
    vms(3106, "NONVOICE", "【直哉】「このセクションを始めるときに、彩野さんは『物語』に対してこんな風に言っていたんだ」")
    vms(3107, "NONVOICE", "【直哉】「『物語自体はすごくシンプルで、あらすじもすぐにまとめられそうなんだけど、枝葉が多いかもしれない』って」")
    comPoseLoad("po2_aya_f_2_d")
    vms(3108, "NONVOICE", "【彩野】「確かに……振り返ってみても、そんな感じがするね」")
    vms(3109, "NONVOICE", "【直哉】「うん。これはどうしてなのかなって、思うんだけど」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3110, "NONVOICE", "【彩野】「そうだね……」")
    vms(3111, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3112, "NONVOICE", "【彩野】「たぶん、だけど」")
    vms(3113, "NONVOICE", "【直哉】「うん」")
    vms(3114, "NONVOICE", "【彩野】「枝葉が多い、お話が短いって事は、……この場面をつくるときに、すごく大変だったのかもしれないなって」")
    vms(3115, "NONVOICE", "【直哉】「大変？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3116, "NONVOICE", "【彩野】「うん。つまりね、書きにくかったかもしれないって思ったんだ」")
    vms(3117, "NONVOICE", "【彩野】「だから途中で何度も物語をやり直したり、お話が進んだとしても短くなったりしたんじゃないかな？」")
    vms(3118, "NONVOICE", "【直哉】「ふむ……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3119, "NONVOICE", "【彩野】「どうして、やり直したのか、進めなかったのか――そこまでは解らないけど。……ごめんね、私の事なのに」")
    vms(3120, "NONVOICE", "【直哉】「あ、そんなことは。でも、書きにくかった、か……。うん」")
    vms(3121, "NONVOICE", "確かに、そう考えてみると、この物語の流れは合点がいく。")
    vms(3122, "NONVOICE", "途中まで書いては消し、書いては消し……そうして生まれたのが、このセクション２なのかもしれない。")
    comPoseDelete()
    wait(1)
    layerLoad(layerName.event, cGetFileName("event", "eve_47_x"))
    switchScreen(0, "", 120)
    vms(3123, "NONVOICE", "なんとなく、僕の頭に机に向かっている彩野さんの姿が浮かんだ。")
    vms(3124, "NONVOICE", "消しゴムで『物語』を何度も何度も修正しながらノートに書いている、彩野さんの姿が。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『オマジナイの効果』のあらすじを作成しました。")
    cStopBGMWrap()
    wait(1)
    comEffectFadeOut(120)
    comSectionCardEndSection()
    doScriptScene = "s2f-10"
    run(cGetFileName("script", "snr_s2_10_f"))
    quit()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[58].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[60].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[49].hold == -1 then
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
        if l1_3 == 58 then
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
            vms(3125, "NONVOICE", "『夜の廊下』のあらすじを見せてみよう。")
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
        if l1_6 == 60 then
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
            vms(3126, "NONVOICE", "プールとは別の場所。")
            vms(3127, "NONVOICE", "その場所に『行ったときのあらすじ』を見せてみよう。")
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

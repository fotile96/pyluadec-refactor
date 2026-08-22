local card_30_s1s_330_step8 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(2333, "NONVOICE", "【彩野】「うーん……」")
    vms(2334, "NONVOICE", "【彩野】「直哉くん……」")
    vms(2335, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(2336, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(2337, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2338, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2339, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(2340, "NONVOICE", "ということは、この『まとめ』では続いて正解のカードを選ぶ必要がある――つまり、途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(2341, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local card_30_s1s_330_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2342, "NONVOICE", "【彩野】「これで、物語は終わりなんだね」")
    vms(2343, "NONVOICE", "【彩野】「うん」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2344, "NONVOICE", "彩野さんは何かを考え込むように視線を落とし、教室の机の上の落書きを見つめている。")
    vms(2345, "NONVOICE", "【彩野】「……」")
    vms(2346, "NONVOICE", "【彩野】「ね、直哉くん」")
    vms(2347, "NONVOICE", "【直哉】「どうかした？」")
    vms(2348, "NONVOICE", "【彩野】「ちょっと、これまでのお話をここでいったん、まとめてみようかと思うの」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2349, "NONVOICE", "【直哉】「うん。それはいいかもしれないね。ずいぶん長くなったし、ちょうどお話も一区切りみたいだから」")
    vms(2350, "NONVOICE", "【直哉】「つまり、この『セクション１』のあらすじをつくろう、ということだね」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2351, "NONVOICE", "【彩野】「うん、そういうこと」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2352, "NONVOICE", "【彩野】「じゃあ、これまで聞いた『物語』について、まとめて質問していい？」")
    vms(2353, "NONVOICE", "【直哉】「うん。了解」")
    vms(2354, "NONVOICE", "僕は机の上にカードを広げた。")
    vms(2355, "NONVOICE", "【彩野】「じゃあね、まず最初に――」")
    vms(2356, "NONVOICE", "【彩野】「私が一番初めに直哉くんに書いて貰ったカードは…………」")
    comPoseDelete()
end
local card_30_s1s_330_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2357, "NONVOICE", "【彩野】「この『物語』、一番最初はどんな感じで書き始められているのかな……」")
    comPoseDelete()
end
local card_30_s1s_330_step3 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(2358, "NONVOICE", "【彩野】「いくつかの章や節でこの物語は分かれているみたい。この物語で言う、『第一章』はなんと言うんだろう？」")
    comPoseDelete()
end
local card_30_s1s_330_step4 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(2359, "NONVOICE", "【彩野】「放課後、私とあの子でコックリさんをやることになって。封筒とか、準備が念入りだったよね……」")
    comPoseDelete()
end
local card_30_s1s_330_step5 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2360, "NONVOICE", "【彩野】「ふむ。なるほど……」")
    vms(2361, "NONVOICE", "【彩野】「あ。でももし、何の事件も起きずに私が『平和な日常生活』を送っていたとしたら、それはどんな感じになるのかな？」")
    comPoseDelete()
end
local card_30_s1s_330_step6 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(2362, "NONVOICE", "【彩野】「ちょっと私が言うのも嫌なんだけど……彼女に私が屋上から落とされた時の場面は、どんな感じだったかな……」")
    comPoseDelete()
end
local card_30_s1s_330_step7 = function()
    oCard.cardAnswerTrue()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_1_a")
    vms(2363, "NONVOICE", "【彩野】「そして最後に、私を助けに来てくれたアイツ。その場面のあらすじは――」")
    comPoseDelete()
end
local card_30_s1s_330_step9 = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2364, "NONVOICE", "【直哉】「よし、まとめたよ。これでこの物語は全部終わり、完結したのかな？」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『誰かが呼んでた』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_2_a")
    vms(2365, "NONVOICE", "【彩野】「えっとね。『完結』とは、ちょっとちがうかも」")
    vms(2366, "NONVOICE", "【直哉】「やっぱり、セクション『その１』だから？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2367, "NONVOICE", "【彩野】「うん。きっと、どこかで物語の『分岐』が発生すると思うの」")
    vms(2368, "NONVOICE", "【直哉】「そっか。まだ先は、長いかな」")
    vms(2369, "NONVOICE", "【直哉】「……でもまあ、今日はこれぐらいにしない？ また明日、調べてみようよ」")
    vms(2370, "NONVOICE", "【彩野】「これぐらい？」")
    vms(2371, "NONVOICE", "そう言うと、彩野さんは黒板の時計を確認した。")
    vms(2372, "NONVOICE", "【彩野】「え、こんな時間なんだ。もしかして、今日はずっと私といたの？」")
    vms(2373, "NONVOICE", "【直哉】「まあ、そんな感じだね」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2374, "NONVOICE", "【彩野】「それは……ありがとう、直哉くん」")
    comSectionCardEndSection()
    doScriptScene = "s1f-10"
    run(cGetFileName("script", "snr_s1_10_f"))
    quit()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[1].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[2].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[10].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[21].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[19].hold == -1 then
        comPoseLoad("po2_aya_f_1_c")
        vms(17198, "NONVOICE", "【彩野】「直哉くん、ここの部分なんだけど……なかなか考えが整理できなくて」")
        comPoseLoad("po2_aya_f_2_e")
        vms(17199, "NONVOICE", "【彩野】「カード、足りないかも……」")
        vms(17200, "NONVOICE", "【直哉】「カード……。どんなカードか、わかるかな……？」")
        vms(17201, "NONVOICE", "【彩野】「えっと……。積極的に行動するとは反対の事……『日常』が、どうであったのかも、知りたかったかな」")
        vms(17202, "NONVOICE", "【直哉】「日常……？」")
        vms(17203, "NONVOICE", "【彩野】「ほら、私たちって、現実には学校が終わったら、すぐに『家に帰ったり』したほうが多かったから……」")
        vms(17204, "NONVOICE", "【彩野】「もし、『そういうお話』があればって」")
        vms(17205, "NONVOICE", "【直哉】「ふむ……」")
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[28].hold == -1 then
        comPoseLoad("po2_aya_f_1_c")
        vms(17206, "NONVOICE", "【彩野】「直哉くん、ここの部分なんだけど……なかなか考えが整理できなくて」")
        comPoseLoad("po2_aya_f_2_e")
        vms(17207, "NONVOICE", "【彩野】「カード、足りないかも……」")
        vms(17208, "NONVOICE", "【直哉】「カード……。どんなカードか、わかるかな……？」")
        vms(17209, "NONVOICE", "【彩野】「えっと……。現実のユウイチ、あんな風に格好良かったかなって、ちょっと気になってるんだ」")
        vms(17210, "NONVOICE", "【直哉】「屋上のピンチを最後に助けに来る、みたいな？」")
        comPoseLoad("po2_aya_f_1_b")
        vms(17211, "NONVOICE", "【彩野】「そうそう」")
        comPoseLoad("po2_aya_f_1_a")
        vms(17212, "NONVOICE", "【彩野】「テストの答案も、少し、気になるかな。私たちって、私たちそんな賭けしてなかったから」")
        comPoseLoad("po2_aya_f_1_c")
        vms(17213, "NONVOICE", "【彩野】「ユウイチが助けに来ないと言うことは、ちょっと嫌な感じだけど……少し、展開が気になるの」")
        vms(17214, "NONVOICE", "【直哉】「ふむ……」")
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[29].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    local l1_0 = false
    card_30_s1s_330_intro()
    local l1_1 = 0
    local l1_2 = 0
    local l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 1 then
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
            vms(2375, "NONVOICE", "【彩野】「一番最初に、書いて貰ったカードって……」")
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
    card_30_s1s_330_resolve()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 2 then
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
            vms(2376, "NONVOICE", "【彩野】「一番最初に『あらすじ』をつくったカードは……」")
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
    card_30_s1s_330_step3()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 10 then
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
            vms(2377, "NONVOICE", "【彩野】「たしか、『なんとか１』って言ってたっけ……」")
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
    card_30_s1s_330_step4()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 21 then
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
            vms(2378, "NONVOICE", "【彩野】「放課後にコックリさんをやることになって……１０円玉とか封筒とか、いろいろ準備してくれてた……」")
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
    card_30_s1s_330_step5()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 19 then
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
            vms(2379, "NONVOICE", "【彩野】「いつもの光景、いつもの日常。それを示すあらすじは……」")
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
    card_30_s1s_330_step6()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 28 then
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
            vms(2380, "NONVOICE", "【彩野】「私が屋上から落とされた時の場面って、どんな描写だったんだろう……」")
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
    card_30_s1s_330_step7()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 29 then
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
            vms(2381, "NONVOICE", "【彩野】「物語の最後。私を助けに来てくれたアイツの名前――」")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    if l1_0 == true then
        card_30_s1s_330_step8()
    end
    card_30_s1s_330_step9()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

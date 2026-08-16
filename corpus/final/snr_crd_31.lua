local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2382, "NONVOICE", "【直哉】「あれ？」")
    vms(2383, "NONVOICE", "【彩野】「どうかした、直哉くん」")
    vms(2384, "NONVOICE", "【直哉】「あ――うん。この部分なんだけど、昨日とはちょっと展開が違うような気がして……どうしてかな？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2385, "NONVOICE", "【彩野】「ふむ。そうなんだ……」")
    vms(2386, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_a")
    vms(2387, "NONVOICE", "【彩野】「あ、もしかしたら」")
    vms(2388, "NONVOICE", "【直哉】「ん？」")
    vms(2389, "NONVOICE", "【彩野】「私、記憶はできなくても『思い出す』事はできるんだよね？」")
    vms(2390, "NONVOICE", "【直哉】「うん。そういう事だよ」")
    vms(2391, "NONVOICE", "【彩野】「それで私、昨日も『物語』を言ったんだよね？」")
    vms(2392, "NONVOICE", "【直哉】「そうだね。沢山話してくれたよ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(2393, "NONVOICE", "【彩野】「うん。それで思ったんだ。もしかしたら――何かを思い出しているのかなって」")
    vms(2394, "NONVOICE", "【直哉】「彩野さんが、事故に遭う前に、この『物語』を書いていたかもしれないってこと？」")
    vms(2395, "NONVOICE", "【彩野】「たぶん……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2396, "NONVOICE", "【彩野】「ごめんね……なにか、自分でも上手く説明できないんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2397, "NONVOICE", "【彩野】「でも、たぶん、そうじゃないかなって思う」")
    vms(2398, "NONVOICE", "物語を、『思い出している』――")
    vms(2399, "NONVOICE", "そんな事が、可能なんだろうか？")
    vms(2400, "NONVOICE", "わからない。_nわからないけれど、今、彩野さんに何らかの『変化』が起きているのは確かだ。")
    comPoseLoad("po2_aya_f_1_e")
    vms(2401, "NONVOICE", "【彩野】「それでね、直哉くん。お話を話しながら思ったんだけど、もしかしてこの場面と同じようなシーンを、私、言ってなかったかな？」")
    vms(2402, "NONVOICE", "【直哉】「同じ、場面……？」")
    vms(2403, "NONVOICE", "【彩野】「デジャブ――って言うほど大げさじゃないんだけど、そんな感じがしたんだ」")
    vms(2404, "NONVOICE", "【彩野】「なにか、この場面、懐かしいなって」")
    vms(2405, "NONVOICE", "この場面は、『何も起こらなかった日常』を描いている場面だ。")
    vms(2406, "NONVOICE", "……。")
    vms(2407, "NONVOICE", "確かに、昨日彩野さんから聞いた『セクション１』の中に、この場面と同じようなシーンの場面があった。")
    vms(2408, "NONVOICE", "『何も起こらなかった日常』を描いた場面――")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    comPoseLoad("po2_aya_f_1_b")
    vms(2409, "NONVOICE", "【彩野】「あ、やっぱり他のお話――セクション１でもこういう場面があったんだね。ありがとう、直哉くん」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2410, "NONVOICE", "【彩野】「でも、ここでも……」")
    vms(2411, "NONVOICE", "【彩野】「何も起こらない日常だと、そこで物語が終わっちゃうんだね」")
    vms(2412, "NONVOICE", "【直哉】「『何も起こらない』と終わっちゃう――」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2413, "NONVOICE", "【彩野】「なにか、浮かんだ？」")
    vms(2414, "NONVOICE", "【直哉】「うん。『物語』を進めるためには、『日常』ではだめなような気がしたんだ」")
    vms(2415, "NONVOICE", "【彩野】「日常では、駄目？」")
    vms(2416, "NONVOICE", "【直哉】「つまりね、『自分で行動を起こさないといけない』っていう事かもしれないって」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2417, "NONVOICE", "【彩野】「自分で行動……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『また、いつもの生活』のあらすじを作成しました。")
    vms(2418, "NONVOICE", "彩野さんは口に手を当てたまま、じっと考え込んでいる。")
    vms(2419, "NONVOICE", "……。")
    vms(2420, "NONVOICE", "この場面について何か思うところがあるみたいだ。")
    vms(2421, "NONVOICE", "これまでの事を踏まえて『もう一度この場面を見てみて』もよいかもしれない。")
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
    l0_0()
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
            vms(2422, "NONVOICE", "【彩野】「いつもの日常。『いつもの生活』――」")
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

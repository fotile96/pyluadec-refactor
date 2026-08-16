local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2489, "NONVOICE", "【直哉】「この場面、オマジナイに興味があるか聞いてくる所だけど――」")
    vms(2490, "NONVOICE", "【直哉】「少し前に出てきたユウイチの誘いの部分と、少し似ているね」")
    vms(2491, "NONVOICE", "【彩野】「似ているって？」")
    vms(2492, "NONVOICE", "【直哉】「えっとね。どちらも興味がなさそうな答えをすると、いつもの生活に行くことになるんだ」")
    vms(2493, "NONVOICE", "【彩野】「興味がない……」")
    vms(2494, "NONVOICE", "【直哉】「この場面では、『サクラさんのため息』が目安になるのかな」")
    vms(2495, "NONVOICE", "【彩野】「……。直哉くん、そのサクラさんの場面、教えて貰っていい？」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    comPoseLoad("po2_aya_f_2_e")
    vms(2496, "NONVOICE", "【彩野】「サクラさんのため息……か」")
    vms(2497, "NONVOICE", "【彩野】「ね、直哉くん、ごめんなさい、もう一つ聞いていい？」")
    vms(2498, "NONVOICE", "【直哉】「うん。なんだろう」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2499, "NONVOICE", "【彩野】「えっとね、サクラさんと私、もしかしたら他のお話でも、放課後に会ってたのかもしれないって、思ったの」")
    vms(2500, "NONVOICE", "他のお話……セクション１、の事だろうか？")
    vms(2501, "NONVOICE", "【直哉】「……コックリさんとか？」")
    comPoseLoad("po2_aya_f_2_a")
    vms(2502, "NONVOICE", "【彩野】「あ……！ うん、そうかもしれない！」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2503, "NONVOICE", "【彩野】「でも……」")
    vms(2504, "NONVOICE", "【彩野】「……コックリさんか……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2505, "NONVOICE", "【彩野】「直哉くん、その時、アヤノはコックリさんになにか質問しなかったかな？」")
    vms(2506, "NONVOICE", "【直哉】「質問……」")
    vms(2507, "NONVOICE", "【彩野】「うん。コックリさんに対して、何かを聞いたと思うの……」")
    vms(2508, "NONVOICE", "【彩野】「その時のあらすじ、あったら見せて欲しいなって」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(2509, "NONVOICE", "【彩野】「……」")
    vms(2510, "NONVOICE", "彩野さんはカードを手にしたまま、何かをじっと考えているようだ。")
    comPoseLoad("po2_aya_f_1_a")
    vms(2511, "NONVOICE", "【彩野】「……うん」")
    vms(2512, "NONVOICE", "自分自身に言い聞かせるように、小さく、頷いた。")
    vms(2513, "NONVOICE", "【直哉】「何か、浮かんだ？」")
    vms(2514, "NONVOICE", "【彩野】「直哉くん、オマジナイの願い事、なんだけど……」")
    vms(2515, "NONVOICE", "【彩野】「たぶん、このコックリさんの場面とも関連があると思う」")
    vms(2516, "NONVOICE", "【直哉】「え、どういうこと？」")
    vms(2517, "NONVOICE", "【彩野】「コックリさんの場面で、『彼』……のこと、聞いたんだよね？」")
    vms(2518, "NONVOICE", "【直哉】「……うん」")
    vms(2519, "NONVOICE", "彼……つまり、ユウイチのことだ……。")
    vms(2520, "NONVOICE", "【彩野】「でも、その質問に対するコックリさんの答えは、『いいえ』だった」")
    vms(2521, "NONVOICE", "【彩野】「その願いを、ここで晴らしたいって考えたような気がする」")
    vms(2522, "NONVOICE", "【直哉】「……あれ？ でも、この場面とさっきのコックリさんの場面は、続いてないよね？」")
    vms(2523, "NONVOICE", "【直哉】「だったら、コックリさんの時にうまくいかなかったから、ここで代わりになんとかする……というのは少しおかしいんじゃないかな？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2524, "NONVOICE", "【彩野】「うーん、確かにそうなんだけど……でも」")
    vms(2525, "NONVOICE", "【直哉】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2526, "NONVOICE", "【彩野】「でも、どこかでこの物語は、全体として『繋がっている』感じがするの」")
    vms(2527, "NONVOICE", "【直哉】「……ふむ……。つまり、ある選択肢を選んだ『物語』で満たされなかった想いを――」")
    vms(2528, "NONVOICE", "【直哉】「――別の『物語』で満たしているって感じかな」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2529, "NONVOICE", "【彩野】「……うん。たぶん……」")
    vms(2530, "NONVOICE", "ある物語を考えた先がバッドエンドだから、別の新しい『分岐』の物語を考えてみる、ということはあった。")
    vms(2531, "NONVOICE", "その流れで考えてみると、ある物語で選んだ想いが満たされないから、別の物語をつくった、ともいえるのかもしれない。")
    comPoseLoad("po2_aya_f_1_a")
    vms(2532, "NONVOICE", "……。")
    vms(2533, "NONVOICE", "……それにしても。")
    vms(2534, "NONVOICE", "曖昧な記憶を元にしているから仕方が無いとはいえ、限りなく手探りに近い行為を僕たちはしているな、と思う。")
    vms(2535, "NONVOICE", "この物語に、終わりはあるのだろうか？")
    vms(2536, "NONVOICE", "【彩野】「……それで、直哉くん？」")
    vms(2537, "NONVOICE", "【直哉】「……あ！ うん、ごめん。ぼーっとしちゃってた」")
    vms(2538, "NONVOICE", "【彩野】「この場面の選択肢なんだけどね。『両思いになる』オマジナイ」")
    vms(2539, "NONVOICE", "【直哉】「……え？」")
    vms(2540, "NONVOICE", "【彩野】「そのオマジナイを、アヤノは望んだと思うの」")
    vms(2541, "NONVOICE", "【直哉】「あ……うん……」")
    vms(2542, "NONVOICE", "両思いになる、オマジナイ……。")
    vms(2543, "NONVOICE", "ユウイチと両思いになる――")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：オマジナイへの興味』の選択肢（両思いになるオマジナイ）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[63].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[23].hold == -1 then
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
        if l1_3 == 63 then
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
            vms(2544, "NONVOICE", "【彩野】「サクラさんがため息をつく所って、どんな場面なのかな……」")
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
    l1_0 = 0
    l1_1 = 0
    l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 23 then
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
            vms(2545, "NONVOICE", "コックリさんの時の場面……。")
            vms(2546, "NONVOICE", "でも、結果は『良くない結果』だったんだよね……。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_2()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

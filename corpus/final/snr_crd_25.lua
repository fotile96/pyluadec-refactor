local card_25_s1s_260_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_2_e")
    vms(2133, "NONVOICE", "【彩野】「屋上……女の子。コックリさん……」")
    vms(2134, "NONVOICE", "【彩野】「直哉くん、もしかしたら……」")
    vms(2135, "NONVOICE", "【直哉】「彩野さん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2136, "NONVOICE", "【彩野】「あ、うん。えっとね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2137, "NONVOICE", "【彩野】「私、屋上で何か……何か、屋上に関連する『お話』に関わっていたのかもしれない」")
    vms(2138, "NONVOICE", "屋上に関係する『お話』……。")
    vms(2139, "NONVOICE", "もしかしたら、屋上で見つけた、あの不思議な絵本……物語の事を言っているのだろうか？")
    vms(2140, "NONVOICE", "【直哉】「彩野さん、もしかして、この『お話』の事？」")
    comPoseDelete()
end
local card_25_s1s_260_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(2141, "NONVOICE", "【彩野】「屋上……」")
    vms(2142, "NONVOICE", "【彩野】「サクラさん……屋上」")
    vms(2143, "NONVOICE", "彩野さんは、屋上で見つけた「物語」を見ながら、何か小さく言葉を呟いている。")
    vms(2144, "NONVOICE", "【直哉】「彩野さん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2145, "NONVOICE", "【彩野】「あ、ごめん、直哉くん」")
    vms(2146, "NONVOICE", "【彩野】「えっとね、ここの部分、『サクラさん』と呼びかける展開をつくってもらって、いい？」")
    vms(2147, "NONVOICE", "サクラさん……。")
    vms(2148, "NONVOICE", "【直哉】「あ……うん……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：声の主』の選択肢（サクラさん）を作成しました。")
    comPoseLoad("po2_aya_f_1_c")
    vms(2149, "NONVOICE", "……。")
    vms(2150, "NONVOICE", "どうしてだろう……。これまでの物語の流れを考えれば、なんてことのない展開の筈なのに……。")
    vms(2151, "NONVOICE", "……すごく重みがあるような気がする。これは……。")
    comPoseLoad("po2_aya_f_2_e")
    vms(2152, "NONVOICE", "【彩野】「……」")
    vms(2153, "NONVOICE", "【彩野】「直哉くん……胸騒ぎがするの」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2154, "NONVOICE", "【彩野】「もう少し……このまま、この物語を読み進めていっていい？」")
    vms(2155, "NONVOICE", "【直哉】「あ、うん。それはもちろん」")
    vms(2156, "NONVOICE", "胸騒ぎ……。")
    vms(2157, "NONVOICE", "屋上で見つけた『あの日記』も、ここから先の展開と関係しているのは間違いないだろう。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[145].hold == -1 then
        comPoseLoad("po2_aya_f_2_e")
        vms(2159, "NONVOICE", "【彩野】「直哉くん、ここの部分なんだけど……」")
        cPlayOneshotMusic(cGetFileName("mus", "mus_12"))
        comEffectYellowIn(60)
        wait(60)
        vms(2160, "NONVOICE", "【彩野】「たぶん、彼女の事を≪もっとずっと深く知らない≫と、進めないような気がする」")
        vms(2161, "NONVOICE", "【直哉】「手持ちのカードが足りない、という事？」")
        vms(2162, "NONVOICE", "【彩野】「カードなのかな……。うん、たぶんそうだと思うけど……」")
        vms(2163, "NONVOICE", "うーん……。")
        vms(2164, "NONVOICE", "今の手持ちのカード……もしくは≪カード以外の何か？≫を知らないと、この先はわからない、という事なのかもしれない。")
        vms(2165, "NONVOICE", "もっとずっと深く……か。")
        vms(2166, "NONVOICE", "気になるけど、とりあえずこの場面は置いておいて、次に進んでみよう。")
        vms(2167, "NONVOICE", "≪ずっと後≫になって、彩野さんが言っている『何か』が解るかもしれない。")
        comPoseDelete()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_25_s1s_260_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 145 then
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
            vms(2168, "NONVOICE", "屋上で見つけた、あの不思議な絵本……物語……")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_25_s1s_260_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

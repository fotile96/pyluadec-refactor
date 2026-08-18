local card_58_s2s_500_step5 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(2959, "NONVOICE", "【彩野】「うーん……」")
    vms(2960, "NONVOICE", "【彩野】「直哉くん……」")
    vms(2961, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(2962, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(2963, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2964, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2965, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(2966, "NONVOICE", "ということは、この『まとめ』では続いて正解のカードを選ぶ必要がある――つまり、途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(2967, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local card_58_s2s_500_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2968, "NONVOICE", "【直哉】「この場面は、途中までは『ユウイチの後ろ姿』と同じ展開。でも――」")
    vms(2969, "NONVOICE", "【直哉】「最後にユウイチが正気を取り戻す部分が違うんだ」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2970, "NONVOICE", "【彩野】「『オマジナイ』が効いたんだね」")
    vms(2971, "NONVOICE", "【直哉】「うん、そうだと思う。他のエンドは……よくない結末だったから」")
    comPoseLoad("po2_aya_f_1_a")
    cStopBGMWrap()
    vms(2972, "NONVOICE", "【彩野】「他の結末。良くない結末……。そういうのが、あるんだね」")
    vms(2973, "NONVOICE", "【彩野】「えっと、それじゃあこの『夜の廊下』場面に辿り着くには、どういう展開になればよかったんだっけ？」")
    vms(2974, "NONVOICE", "【直哉】「うーん――ここは結構入り組んでるね。ここに辿り着くまでに、いろいろな経緯や選択が重なってる感じなんだ」")
    vms(2975, "NONVOICE", "【彩野】「ふむ……」")
    vms(2976, "NONVOICE", "彩野さんは考え込んでいる。")
    vms(2977, "NONVOICE", "確かに、この場面に来るまでに様々な分岐や経緯があったけど、それを『色々あった』で済ましてしまうのは説明としてかなり不足している。")
    vms(2978, "NONVOICE", "ここは、セクション１の時と同じように……ちょっとお話を、『まとめ』てみたほうが良さそうだ。")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    vms(2979, "NONVOICE", "【直哉】「そっか。じゃあちょっと、この場面までの経緯をまとめてみるね」")
    vms(2980, "NONVOICE", "【彩野】「……うん、お願い。直哉くん」")
    vms(2981, "NONVOICE", "【直哉】「まず最初に。放課後の約束を『していない』、ユウイチと週末の約束を『する』」")
    vms(2982, "NONVOICE", "【直哉】「これで、セクション１から物語が『分岐』して、セクション２の物語になるんだ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(2983, "NONVOICE", "【彩野】「……セクション２」")
    vms(2984, "NONVOICE", "【直哉】「『物語』に入ると、サクラさんがオマジナイの事について聞いてくる」")
    vms(2985, "NONVOICE", "【直哉】「だけど……この時、オマジナイに興味がないそぶりをすると――」")
    vms(2986, "NONVOICE", "【直哉】「アヤノさんが帰った後、サクラさんはそっとある行動をとるんだ。その行動は――」")
    comPoseDelete()
end
local card_58_s2s_500_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_d")
    vms(2987, "NONVOICE", "【彩野】「ため息をついちゃうみたいな、落胆させるようなことは駄目ってことね」")
    vms(2988, "NONVOICE", "【直哉】「うん。オマジナイに興味があることを伝えないと」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2989, "NONVOICE", "【彩野】「興味……うん。なるほどね」")
    vms(2990, "NONVOICE", "【直哉】「次に、アヤノさんがオマジナイに興味があると聞いたサクラさんは、アヤノさんに対してナゾトキを出題する」")
    vms(2991, "NONVOICE", "【直哉】「この時の答えが、後ほどの展開に影響するんだ」")
    vms(2992, "NONVOICE", "【直哉】「サクラさんのナゾトキで正解した時のあらすじは――」")
    comPoseDelete()
end
local card_58_s2s_500_step3 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_a")
    vms(2993, "NONVOICE", "【彩野】「あ、なるほど。正解の時と不正解があった時で、展開が違うんだね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2994, "NONVOICE", "【彩野】「直哉くん。ここのナゾトキの内容も、どこかの場面と『繋がっている』のかな？」")
    vms(2995, "NONVOICE", "【直哉】「うーん、それはまだ、わからない。でも、たぶんそうなんじゃないかなって思う」")
    vms(2996, "NONVOICE", "【直哉】「サクラさんの言葉には、何となく『意味』があるような気がするんだ。何かを示唆するような」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2997, "NONVOICE", "【彩野】「……しさ？」")
    vms(2998, "NONVOICE", "【直哉】「そう。示唆。何かをほのめかしているんじゃないかなって思う。今はまだ、それが何かは解らないけどね」")
    vms(2999, "NONVOICE", "【直哉】「さて、ナゾトキの後だけど、ナゾトキの結果を受けて、サクラさんはアヤノさんにオマジナイを教えた」")
    vms(3000, "NONVOICE", "【直哉】「このオマジナイは、ナゾトキが正解だったときと間違っていた時とで、内容が違っていたんだ」")
    vms(3001, "NONVOICE", "【直哉】「ナゾトキに正解することで得られたオマジナイは……」")
    comPoseDelete()
end
local card_58_s2s_500_step4 = function()
    oCard.cardAnswerTrue()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_1_a")
    vms(3002, "NONVOICE", "【直哉】「消しゴムに名前を書く、これが正解の『オマジナイ』だね」")
    comPoseLoad("po2_aya_f_2_d")
    vms(3003, "NONVOICE", "【彩野】「消しゴムに名前？ ……懐かしい感じだね」")
    vms(3004, "NONVOICE", "【直哉】「実は、この消しゴムは、セクション１にも出てきたよ」")
    vms(3005, "NONVOICE", "【彩野】「セクション１。他の『お話』で？」")
    vms(3006, "NONVOICE", "【直哉】「うん。忘れていた約束を思い出すキッカケの道具として、ね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3007, "NONVOICE", "【彩野】「……」")
    vms(3008, "NONVOICE", "【直哉】「この消しゴムがなんの意味を持つのかはまだ解らない。でも、消しゴムはこの物語にとっての何かのキーになっている事は確実だと思う」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3009, "NONVOICE", "【彩野】「どうして？」")
    vms(3010, "NONVOICE", "【直哉】「二回も、アヤノさんに対しての何らかの『行動』に関わっているんだ。思い出す、オマジナイ……願掛け。なにかまだ、あるんじゃないかなって僕は思う」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3011, "NONVOICE", "【彩野】「うん……」")
    vms(3012, "NONVOICE", "【直哉】「そして、オマジナイをした後。アヤノさんは、オマジナイが本当に効くのか、再度自分自身に問いかけた」")
    vms(3013, "NONVOICE", "【直哉】「二回のバッドエンドを得てわかったこと。それが、オマジナイに対して『どう思うのか』だった」")
    vms(3014, "NONVOICE", "【直哉】「『その行動』の場面は――」")
    comPoseDelete()
end
local card_58_s2s_500_step6 = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3015, "NONVOICE", "【彩野】「そのオマジナイは絶対に効くと思うこと……」")
    vms(3016, "NONVOICE", "【直哉】「うん。これが最後のポイント。まとめるとこんな感じだね」")
    vms(3017, "NONVOICE", "【直哉】「『放課後の約束をしていない』、『ユウイチと週末の約束をする』」")
    vms(3018, "NONVOICE", "【直哉】「『オマジナイに興味がある』、 『ナゾトキに正解する』」")
    vms(3019, "NONVOICE", "【直哉】「『消しゴムに名前を書く』、『そのオマジナイは絶対に効く』」")
    vms(3020, "NONVOICE", "【直哉】「これによって、ユウイチは意識を取り戻す。『オマジナイは成功した』と考えていいかもしれない」")
    comPoseLoad("po2_aya_f_2_d")
    vms(3021, "NONVOICE", "【彩野】「この分岐は……なんというか、やっぱり、複雑な感じがするね」")
    vms(3022, "NONVOICE", "【直哉】「そうだね。どうしてこんな風に、沢山の分岐がある物語になったんだろう」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3023, "NONVOICE", "【彩野】「うん……」")
    vms(3024, "NONVOICE", "【直哉】「まあ、まだこのセクションは終わりじゃない。終わったら、落ち着いて少し考えてみるのもいいかもしれない」")
    vms(3025, "NONVOICE", "【彩野】「うん、そうだね」")
    comPoseLoad("po2_aya_f_1_e")
    vms(3026, "NONVOICE", "【彩野】「……いろいろありがとう、直哉くん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『夜の廊下』のあらすじを作成しました。")
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
    if gameSave.myCard[62].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[50].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[52].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    local l1_0 = false
    card_58_s2s_500_intro()
    local l1_1 = 0
    local l1_2 = 0
    local l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 63 then
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
            vms(3027, "NONVOICE", "息をつく……ため息が出ちゃったり……。")
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
    card_58_s2s_500_resolve()
    local l1_4 = 0
    local l1_5 = 0
    local l1_6 = -1
    while l1_4 < 1 do
        local l1_7 = oCard.selectCardObj()
        if l1_7 == 62 then
            break
        end
        if l1_7 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_5 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3028, "NONVOICE", "『ナゾトキの正解』を、彩野さんに見せてみよう。")
            comPoseDelete()
        end
        if l1_5 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_5 = l1_5 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_58_s2s_500_step3()
    local l1_7 = 0
    local l1_8 = 0
    local l1_9 = -1
    while l1_7 < 1 do
        local l1_10 = oCard.selectCardObj()
        if l1_10 == 50 then
            break
        end
        if l1_10 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_8 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3029, "NONVOICE", "サクラさんは三つのオマジナイを教えてくれた。")
            vms(3030, "NONVOICE", "正解となるのは文房具に関係している――")
            comPoseDelete()
        end
        if l1_8 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_8 = l1_8 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_58_s2s_500_step4()
    local l1_10 = 0
    local l1_11 = 0
    local l1_12 = -1
    while l1_10 < 1 do
        local l1_13 = oCard.selectCardObj()
        if l1_13 == 52 then
            break
        end
        if l1_13 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_11 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(3031, "NONVOICE", "「絶対に」「たぶん」「やってソンはない」この中で、正解はどれだっただろうか？")
            comPoseDelete()
        end
        if l1_11 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_11 = l1_11 + 1
            comPoseDelete()
        end
        wait(30)
    end
    if l1_0 == true then
        card_58_s2s_500_step5()
    end
    card_58_s2s_500_step6()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

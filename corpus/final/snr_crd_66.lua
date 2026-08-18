local card_66_s3s_50_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3168, "NONVOICE", "【彩野】「直哉くん、ここの場面なんだけど」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3169, "NONVOICE", "【彩野】「……」")
    vms(3170, "NONVOICE", "【直哉】「どうかした？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3171, "NONVOICE", "【彩野】「うん……。ここ、『聞く』のに、ちょっと違和感がある気がして」")
    vms(3172, "NONVOICE", "【直哉】「違和感？ どういうことだろう」")
    vms(3173, "NONVOICE", "【彩野】「……うん。なんかね、アヤノは、ちょっとサクラさんに『答えを合わせてる』のかなって」")
    vms(3174, "NONVOICE", "【直哉】「ふむ……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3175, "NONVOICE", "【彩野】「本当は、ちょっと違った事を思ってるのかなって、思ったの」")
    vms(3176, "NONVOICE", "【直哉】「違う感情……。彩野さんの心の中で思っていたこと――本意とは別の答えを返している、と言うこと？」")
    vms(3177, "NONVOICE", "【彩野】「うん。そんな感じがしたの。なんとなく」")
    vms(3178, "NONVOICE", "【彩野】「なんとなく、なんだけど。……でも……」")
    vms(3179, "NONVOICE", "アヤノさんと、サクラさん……。")
    comPoseLoad("po2_aya_f_2_e")
    vms(3180, "NONVOICE", "【彩野】「物語では、アヤノとサクラさんって、どんな関係なんだろう？」")
    vms(3181, "NONVOICE", "彩野さんは僕に聞くでもなく、そっと言葉を呟く。")
    vms(3182, "NONVOICE", "彩野さんとサクラさんの『関係』。")
    vms(3183, "NONVOICE", "これまで彩野さんから聞いた『物語』で、『サクラさんとアヤノさんの関係』を一言で説明するとしたら。")
    vms(3184, "NONVOICE", "昨日、彩野さんから聞いた、『あのセクションのあらすじ』を見せれば、説明できるだろうか……")
    comPoseDelete()
end
local card_66_s3s_50_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(3185, "NONVOICE", "【彩野】「セクション５。私とサクラさんの物語……」")
    vms(3186, "NONVOICE", "【直哉】「アヤノさん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3187, "NONVOICE", "【彩野】「――直哉くん」")
    vms(3188, "NONVOICE", "【直哉】「うん」")
    vms(3189, "NONVOICE", "【彩野】「ここの分岐に、「聞かない」を入れてもらっていい？」")
    vms(3190, "NONVOICE", "【直哉】「え？ 聞かない？ サクラさんの話を聞かないの？」")
    vms(3191, "NONVOICE", "【直哉】「今まで――その、物語が『良くない方向』……」")
    vms(3192, "NONVOICE", "【直哉】「つまり、バッドエンドに進む時って、大抵アヤノさんがその物事に『あまり興味を持っていない』事を示す分岐の先じゃなかったっけ？」")
    vms(3193, "NONVOICE", "【直哉】「ほら、オマジナイを信じないとか、階段のウワサに興味がないとか……」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3194, "NONVOICE", "【彩野】「うーん、言われてみれば確かにそうなんだけど……」")
    vms(3195, "NONVOICE", "【彩野】「でもね……ここでは、ちょっと特別な感じがする」")
    vms(3196, "NONVOICE", "【直哉】「特別な感じ……？」")
    vms(3197, "NONVOICE", "【彩野】「うん……なんだろう。現実にこういうやりとりをしていたかもしれない、って言うのかな」")
    vms(3198, "NONVOICE", "【彩野】「それでね。アヤノとサクラさんの関係って、もうちょっと素直にやりとりする感じだったのかもしれないって」")
    vms(3199, "NONVOICE", "【彩野】「だから、そうすれば『お話』が広がるのかなって」")
    vms(3200, "NONVOICE", "【直哉】「ふむ……」")
    vms(3201, "NONVOICE", "【彩野】「サクラさんから『聞いた』お話を受け止めて――私が答えを返す。その流れが『自然』であるのかの違いって言うのかな」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3202, "NONVOICE", "【彩野】「それでね、ここはアヤノが素直に――サクラさんと『いつものように』会話をしてるって想像したら、ちょっと違うのかなって」")
    vms(3203, "NONVOICE", "【直哉】「いつものように……か。うん。わかった。カードを作ってみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：興味深いウワサ』の選択肢（聞かない）を作成しました。")
    comPoseDelete()
    vms(3204, "NONVOICE", "『いつもの』『自然な』サクラさんとアヤノさんのやりとり。")
    vms(3205, "NONVOICE", "……。")
    vms(3206, "NONVOICE", "……それを再現するとしたら。")
    vms(3207, "NONVOICE", "……サクラさんの行き先は――")
    vms(3208, "NONVOICE", "……。")
    vms(3209, "NONVOICE", "この先の物語はどうなるのだろう……。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[139].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_66_s3s_50_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 139 then
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
            vms(3210, "NONVOICE", "二人の関係を描いたセクションのあらすじ。")
            vms(3211, "NONVOICE", "あのセクションのあらすじカード、見せるべきだろうか……。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_66_s3s_50_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

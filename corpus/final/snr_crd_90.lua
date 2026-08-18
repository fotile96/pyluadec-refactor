local card_90_s3s_641_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3791, "NONVOICE", "【直哉】「彩野さん、ここの部分なんだけど……」")
    vms(3792, "NONVOICE", "【彩野】「……うん？ どうかした？」")
    vms(3793, "NONVOICE", "【直哉】「実は昨日の夜に彩野さんから連絡があって――」")
    vms(3794, "NONVOICE", "【直哉】「『キスはしない』選択肢を追加してみてはどうかって、提案があったんだ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3795, "NONVOICE", "【彩野】「……そうなんだ」")
    vms(3796, "NONVOICE", "【直哉】「この箇所に分岐が発生するって、これまで彩野さんは言っていなかったんだけど……」")
    vms(3797, "NONVOICE", "【直哉】「電話口で、『これまでに作った物語のカードを見ながら、思い浮かんだ』って」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3798, "NONVOICE", "【彩野】「ふむふむ……」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3799, "NONVOICE", "【彩野】「あ、私、直哉くんの家に電話掛けたんだね」")
    comPoseLoad("po2_aya_f_2_b")
    vms(3800, "NONVOICE", "【彩野】「……もしかして、電話するの、初めてじゃない？」")
    vms(3801, "NONVOICE", "【直哉】「あ、う、うん」")
    vms(3802, "NONVOICE", "【彩野】「……そっか。うん。なるほど」")
    vms(3803, "NONVOICE", "【彩野】「そしたら、直哉くん、今読んでる『物語』。セクション３Ａのあらすじカードが、あるんだよね？」")
    vms(3804, "NONVOICE", "【直哉】「あ……うん。あるよ」")
    comPoseDelete()
end
local card_90_s3s_641_sel_resolve = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3805, "NONVOICE", "【彩野】「それと、セクション――４だっけ。その物語のあらすじって、何になる？」")
    vms(3806, "NONVOICE", "【直哉】「えっと、セクション４は結末が二つあって、４Ａと４Ｂになるね」")
    vms(3807, "NONVOICE", "【彩野】「４Ｂの方が最新、でいいのかな？」")
    vms(3808, "NONVOICE", "【直哉】「うん。でもこのあらすじは、どちらかというとバッドエンドっぽくて、何か――」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3809, "NONVOICE", "【彩野】「……大丈夫。見せて」")
    vms(3810, "NONVOICE", "【直哉】「……うん」")
    comPoseDelete()
end
local card_90_s3s_641_sel_step3 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3811, "NONVOICE", "カードを受け取ると彩野さんは小さく頷いた。")
    vms(3812, "NONVOICE", "【彩野】「そっか。セクション３で『大声でユウイチを呼んだ』展開でセクション４に入るんだけど――」")
    vms(3813, "NONVOICE", "【彩野】「セクション４で、ユウイチの見せたカードに『私じゃないって』言えば……」")
    vms(3814, "NONVOICE", "【直哉】「……もう一度セクション３に戻ることができる」")
    vms(3815, "NONVOICE", "【彩野】「うん。これが『本来のお話の流れ』だったのかもしれない」")
    vms(3816, "NONVOICE", "【彩野】「直哉くん。こんな感じにお話を辿った場合、『キスしない』展開を作ってもらっていい？」")
    vms(3817, "NONVOICE", "【直哉】「でも、こんな風に――思いつきみたいに物語を増やしちゃってよいのかな？」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3818, "NONVOICE", "【彩野】「思いつき……でも昨日、私は、直哉くんに『展開があるかもしれない』って伝えたんだよね？」")
    vms(3819, "NONVOICE", "【直哉】「うん。夜に――電話で」")
    comPoseLoad("po2_aya_f_1_e")
    vms(3820, "NONVOICE", "【彩野】「じゃあ、大丈夫」")
    vms(3821, "NONVOICE", "【直哉】「……」")
    vms(3822, "NONVOICE", "【直哉】「……わかった」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3823, "NONVOICE", "【彩野】「うん。……お願い」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：花火の中、ユウイチと』の選択肢（ユウイチとキスしない）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[135].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[138].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_90_s3s_641_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 135 then
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
            vms(3824, "NONVOICE", "セクション３Ａのあらすじカードを彩野さんに見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_90_s3s_641_sel_resolve()
    local l1_3 = 0
    local l1_4 = 0
    local l1_5 = -1
    while l1_3 < 1 do
        local l1_6 = oCard.selectCardObj()
        if l1_6 == 138 then
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
            vms(3825, "NONVOICE", "セクション４Ｂのあらすじカードを彩野さんに見せてみよう。")
            vms(3826, "NONVOICE", "でも、この物語は……。")
            comPoseDelete()
        end
        if l1_4 == 0 then
            oCard.mesNG()
            l1_4 = l1_4 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_90_s3s_641_sel_step3()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

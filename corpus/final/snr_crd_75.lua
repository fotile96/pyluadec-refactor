local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_2_e")
    vms(3391, "NONVOICE", "【彩野】「直哉くん……」")
    vms(3392, "NONVOICE", "彩野さんは声を落として言った。")
    vms(3393, "NONVOICE", "【彩野】「どうしてだろう、ここの場面、『後をつける』だとすごく嫌な感じがするの」")
    vms(3394, "NONVOICE", "【直哉】「嫌な感じ……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3395, "NONVOICE", "【彩野】「うん。なんだろう。嫌な予感がするって言うのかな……」")
    vms(3396, "NONVOICE", "この場面の後――")
    vms(3397, "NONVOICE", "アヤノさんはユウイチの後をつけて、図書室でユカリ先生と抱き合っているユウイチを目撃する……。")
    comPoseLoad("po2_aya_f_1_a")
    vms(3398, "NONVOICE", "【彩野】「ね、直哉くん……。この後の場面のあらすじって、わかる？」")
    vms(3399, "NONVOICE", "【直哉】「あ、う、うん……」")
    vms(3400, "NONVOICE", "とりあえず、彩野さんに見せるのは『後をつける』の場面のあらすじだけにしておこう。")
    vms(3401, "NONVOICE", "その後の場面は……。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3402, "NONVOICE", "【彩野】「えっと、この後の場面のあらすじは、ある？」")
    vms(3403, "NONVOICE", "【直哉】「え、あ、えっと……どこにしまったかな……」")
    comPoseLoad("po2_aya_f_1_d")
    vms(3404, "NONVOICE", "【彩野】「……」")
    vms(3405, "NONVOICE", "【直哉】「……あれ、見つからないな、はは……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3406, "NONVOICE", "【彩野】「あ、探すぐらいならいいよ。大丈夫」")
    vms(3407, "NONVOICE", "【彩野】「――それでね、直哉くん」")
    vms(3408, "NONVOICE", "【直哉】「……うん」")
    vms(3409, "NONVOICE", "【彩野】「ここの部分、新しい展開を追加してもらっていい？」")
    vms(3410, "NONVOICE", "【直哉】「……展開？」")
    vms(3411, "NONVOICE", "【彩野】「えっとね」")
    vms(3412, "NONVOICE", "【彩野】「この場面のユウイチは『ほうっておく』で、お願い」")
    vms(3413, "NONVOICE", "【直哉】「話し掛けないんだ」")
    vms(3414, "NONVOICE", "【彩野】「うん。もともとは陸上部の子に、階段のウワサを確認しようかなっていう所だから、そっちの方を優先って感じ」")
    comPoseLoad("po2_aya_f_1_e")
    vms(3415, "NONVOICE", "【彩野】「まあ、ユウイチなら放っておいても大丈夫だよ」")
    vms(3416, "NONVOICE", "【直哉】「はは、まあね」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3417, "NONVOICE", "【彩野】「それじゃあ、お願いできるかな？」")
    vms(3418, "NONVOICE", "【直哉】「うん。カードを作るね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ユウイチの影』の選択肢（ほうっておく）を作成しました。")
    comPoseLoad("po2_aya_f_2_e")
    vms(3419, "NONVOICE", "【彩野】「……」")
    vms(3420, "NONVOICE", "【直哉】「どうかした？ 彩野さん」")
    vms(3421, "NONVOICE", "【彩野】「……うん。それでね」")
    vms(3422, "NONVOICE", "【彩野】「実はここって、何か、展開が浮かびそうなんだけど……」")
    vms(3423, "NONVOICE", "【直哉】「展開？ それじゃあ、この『ほうっておく』の他にも、新しい展開があるかもしれないと言うこと？」")
    vms(3424, "NONVOICE", "【彩野】「うん。そうかもしれない……」")
    vms(3425, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3426, "NONVOICE", "【彩野】「……ごめんなさい、はっきりしなくて」")
    vms(3427, "NONVOICE", "新しい展開……か。")
    vms(3428, "NONVOICE", "でも、彩野さんにはどうすれば新しい展開が発生するのか、明確ではないみたいだ。")
    vms(3429, "NONVOICE", "もうちょっと――カードがたまってから、もう一度この場面について考えたほうがいいかもしれない。")
    vms(3430, "NONVOICE", "今は他の場面の物語を読み進めてみよう。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[79].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[80].hold == -1 then
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
        if l1_3 == 79 then
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
            vms(3431, "NONVOICE", "彩野さんに見せるのは『後をつける』のあらすじだけにしておこう……。")
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

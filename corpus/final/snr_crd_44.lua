local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2714, "NONVOICE", "【彩野】「直哉くん、この場所を決める場面なんだけど……」")
    vms(2715, "NONVOICE", "【直哉】「うん」")
    comPoseLoad("po2_aya_f_2_a")
    vms(2716, "NONVOICE", "【彩野】「プール以外にも、アヤノが行きたい場所があるような気がするんだ」")
    vms(2717, "NONVOICE", "【直哉】「プール以外の場所ね。どこだろう。行きたい箇所としてアヤノさんは色々リストアップしていたけど……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2718, "NONVOICE", "【彩野】「そうだね……。あ、プールって、結局アヤノはユウイチと行ったんだよね？」")
    vms(2719, "NONVOICE", "【直哉】「あ、うん。カードがつくってあるよ」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2721, "NONVOICE", "彩野さんは、カードの内容に目を通した。")
    comPoseLoad("po2_aya_f_2_a")
    vms(2722, "NONVOICE", "【彩野】「はは……うーん、いかにも夏って感じだね」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2723, "NONVOICE", "【彩野】「……」")
    vms(2724, "NONVOICE", "【直哉】「何か浮かんだ？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2725, "NONVOICE", "【彩野】「あ、うん。ね、直哉くん？ ちょっと聞いていい？」")
    vms(2726, "NONVOICE", "【直哉】「うん。なんだろう」")
    comPoseLoad("po2_aya_f_2_a")
    vms(2727, "NONVOICE", "【彩野】「えっとね……。ここの部分のお話って、セクション１とはまた別の展開なんだよね」")
    vms(2728, "NONVOICE", "【直哉】「セクション２だからね。物語としては分かれているよ」")
    vms(2729, "NONVOICE", "【彩野】「じゃあ――そのセクション１の、終わりの部分ってあらすじってあるかな」")
    vms(2730, "NONVOICE", "【直哉】「セクション１の最後の場面。『誰かが呼んでた』だったかな。つくってあるよ」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    comPoseLoad("po2_aya_f_2_e")
    vms(2731, "NONVOICE", "【彩野】「……」")
    vms(2732, "NONVOICE", "【直哉】「セクション１の最後の部分がどうかした？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2733, "NONVOICE", "【彩野】「あ、ここのね。星が見えるって所。ここでプラネタリウムって、アヤノが言ってるんだよね」")
    vms(2734, "NONVOICE", "【直哉】「……プラネタリウム。そっか。ユウイチと場所を決めるときも、言っていたね」")
    vms(2735, "NONVOICE", "【彩野】「ね、そうだよね。……うん」")
    vms(2736, "NONVOICE", "【直哉】「もしかして、プラネタリウムかな？ 展開、追加してみる？」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2737, "NONVOICE", "【彩野】「うん。『プラネタリウムに行く場面』、追加、お願いしていいかな？ 」")
    vms(2738, "NONVOICE", "【直哉】「了解。カードを書いてみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：出かける場所』の選択肢（プラネタリウム）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[30].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[59].hold == -1 then
        comPoseLoad("po2_aya_f_2_e")
        vms(2739, "NONVOICE", "【彩野】「直哉くん、ここの部分なんだけど……」")
        cPlayOneshotMusic(cGetFileName("mus", "mus_12"))
        comEffectYellowIn(60)
        wait(60)
        vms(2740, "NONVOICE", "【彩野】「≪もうちょっと後になってから、もう一度≫考えさせてもらっていい？」")
        vms(2741, "NONVOICE", "【直哉】「手持ちのカードが足りない、という事？」")
        vms(2742, "NONVOICE", "【彩野】「うん、そうかもしれない……プールの他に、場所があるような気がするんだけど……」")
        vms(2743, "NONVOICE", "【彩野】「でも……ちょっと浮かばなくて」")
        vms(2744, "NONVOICE", "場所……か。とりあえずこの場面は保留にして、次に進んでみよう。")
        vms(2745, "NONVOICE", "≪後≫になって、彩野さんが言っている『プールの他の場所』が解るかもしれない。")
        comPoseDelete()
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
        if l1_3 == 59 then
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
            vms(2746, "NONVOICE", "ユウイチとアヤノさんが、プールに行ったときのあらすじカードを見せてみよう。")
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
        if l1_6 == 30 then
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
            vms(2747, "NONVOICE", "セクション１の最後のシーン。『誰かが呼んでた』だったかな。")
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

local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2584, "NONVOICE", "【直哉】「このシーンで一瞬見えた、屋上からの場面だけど……」")
    vms(2585, "NONVOICE", "【彩野】「もしかして、私、前にそういう『お話』を言った？」")
    vms(2586, "NONVOICE", "【直哉】「彩野さん、わかる？」")
    wait(1)
    layerLoad(layerName.event, cGetFileName("event", "eve_46_a"))
    layerLoad(layerName.pose1, "")
    switchScreen(0, "", 10)
    wait(10)
    wait(1)
    layerLoad(layerName.bg1, cGetFileName("bg", "bg_1_a_0"))
    layerLoad(layerName.pose1, cGetFileName("pose", "po2_aya_f_1_a"))
    switchScreen(0, "", 10)
    vms(2587, "NONVOICE", "【彩野】「うん……何となくだけど……」")
    vms(2588, "NONVOICE", "【彩野】「そうだね、この場面のフラッシュバックと同じような感じで」")
    vms(2589, "NONVOICE", "【彩野】「もしかしたら、前、どこかでこれ言ったのかなって」")
    vms(2590, "NONVOICE", "【彩野】「『その場面』のカードって、あるかな？」")
    vms(2591, "NONVOICE", "【直哉】「あ、うん。持ってるよ。そのカードはね……」")
    vms(2592, "NONVOICE", "僕はカードを机の上に並べた。")
    vms(2593, "NONVOICE", "セクション１でユウイチが助けに来た場面のカードを見せた方がいいだろうな。")
    vms(2594, "NONVOICE", "……もう一方のバッドエンドの方は……止めておこう。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2595, "NONVOICE", "【彩野】「ああ、やっぱり。こういうお話もあったんだ」")
    vms(2596, "NONVOICE", "【直哉】「……と言うことは、この部分はセクション１の部分が混じっている、という事になるのかな」")
    vms(2597, "NONVOICE", "【彩野】「うん。そう思うよ」")
    vms(2598, "NONVOICE", "この場面でも物語は『繋がっている』。彩野さんの物語では、パーツ同士が繋がりあっている、と考えていいみたいだ。")
    vms(2599, "NONVOICE", "……。")
    vms(2600, "NONVOICE", "現実のユウイチ、彩野さんもやはり、屋上から飛び降りている。")
    vms(2601, "NONVOICE", "……この物語と現実の一部も繋がっている、そんな事はあるだろうか？")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ユウイチのことが好き』のあらすじを作成しました。")
    vms(2602, "NONVOICE", "ユウイチの事が好き、か。")
    vms(2603, "NONVOICE", "……。")
    vms(2604, "NONVOICE", "……次。")
    vms(2605, "NONVOICE", "……次。次のあらすじを考えないと……。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[29].hold == -1 then
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
        if l1_3 == 29 then
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
            vms(2606, "NONVOICE", "セクション１でユウイチが助けに来た場面のカードを見せた方がいいだろうな。")
            vms(2607, "NONVOICE", "たしかあのカードは……『ユウイチはアヤノを助ける』だったっけ……。")
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

local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(665, "NONVOICE", "【彩野】「……お店……ユウイチとの賭け……」")
    vms(666, "NONVOICE", "【彩野】「えっと……ね。直哉くん」")
    vms(667, "NONVOICE", "【彩野】「『物語』じゃなくて、現実のことなんだけど……」")
    vms(668, "NONVOICE", "【直哉】「ん、なんだろう」")
    vms(669, "NONVOICE", "【彩野】「あれを出すお店って、今もまだある？」")
    vms(670, "NONVOICE", "彩野さんはおずおずと聞いた。")
    vms(671, "NONVOICE", "【彩野】「私たちもよく食べていた――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(672, "NONVOICE", "【彩野】「そうそう、ハンバーガーのお店」")
    vms(673, "NONVOICE", "ハンバーガー。現実のファストフードのお店。")
    vms(674, "NONVOICE", "……そうか。")
    vms(675, "NONVOICE", "僕らが高校生だったとき、ファストフードのお店にはよく行ったものだった。")
    vms(676, "NONVOICE", "僕と、彩野さんと……_nユウイチの三人で。")
    vms(677, "NONVOICE", "あの店は、駅からちょっと横に入ったところにある。")
    vms(678, "NONVOICE", "見つけづらいのが原因なのか、お客さんは少なく余り流行っているとはいえなかった。")
    vms(679, "NONVOICE", "僕的にはそこらへんの理由も含めて落ち着けて好きだったのだけれど、彩野さんが心配するのも無理はない。")
    vms(680, "NONVOICE", "【直哉】「大丈夫。まだちゃんとやってるよ。オーナーのおじさんも元気」")
    vms(681, "NONVOICE", "【彩野】「……よかった」")
    comPoseLoad("po2_aya_f_1_e")
    vms(682, "NONVOICE", "【彩野】「直哉くんハンバーガー好きだったもんね」")
    vms(683, "NONVOICE", "【直哉】「この前久しぶりに行ったら、僕らのことちゃんと覚えててくれたよ。お嬢ちゃんにもよろしく、だって」")
    vms(684, "NONVOICE", "【彩野】「ふふ、どういたしまして」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『答案を羨ましがる』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[132].hold == -1 then
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
        if l1_3 == 132 then
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
            vms(685, "NONVOICE", "【彩野】「ユウイチに何をおごろうとしてたんだっけ……」")
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

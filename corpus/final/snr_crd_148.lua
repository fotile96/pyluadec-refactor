local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(760, "NONVOICE", "【直哉】「廊下でユウイチを見かけて、声を掛けるんだけど――」")
    vms(761, "NONVOICE", "【直哉】「アヤノさんは『私じゃない』って、結局分かれちゃうんだね」")
    vms(762, "NONVOICE", "【彩野】「うん……」")
    vms(763, "NONVOICE", "【彩野】「あ、それで直哉くん。物語の中で、アヤノは『きくちゃんの所、行ってみよう』ってあったけど……」")
    comPoseLoad("po2_aya_f_2_a")
    vms(764, "NONVOICE", "【彩野】「この後の展開って、どんな展開になるのかな？」")
    vms(765, "NONVOICE", "【直哉】「あ、うん。えっとね、きくちゃんの居るところ――校庭に行くんだ」")
    vms(766, "NONVOICE", "【直哉】「場面は、セクション３になるね。あらすじが作ってあるよ」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_e")
    vms(767, "NONVOICE", "【彩野】「あ、なるほど。きくちゃんに階段のウワサを聞きに戻るんだね」")
    vms(768, "NONVOICE", "【直哉】「うん。物語の展開的には、セクション３から４に行って、やっぱり３に戻るって感じ」")
    vms(769, "NONVOICE", "【直哉】「でも……改めてこうやって物語の流れをまとめてみると、ちょっと面白いね」")
    vms(770, "NONVOICE", "【直哉】「どうしてこんな展開にしたんだろう？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(771, "NONVOICE", "【彩野】「うーん……そうだね……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『私じゃない』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[77].hold == -1 then
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
        if l1_3 == 77 then
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
            vms(772, "NONVOICE", "『陸上部のウワサ』を聞きに行く場面だったかな……")
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

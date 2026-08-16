local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2874, "NONVOICE", "【直哉】「彩野さん、ここの部分なんだけど」")
    vms(2875, "NONVOICE", "【彩野】「どうかしたの？ 直哉くん」")
    vms(2876, "NONVOICE", "【直哉】「うん、実はこの選択肢の部分を指して、こんな風に彩野さんが言っていたことがあるんだ」")
    vms(2877, "NONVOICE", "彩野さんが言っていた、『絶対に効くオマジナイ』……。")
    vms(2878, "NONVOICE", "そのカードを見せてみよう。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2879, "NONVOICE", "【彩野】「絶対に効くオマジナイ……」")
    vms(2880, "NONVOICE", "【直哉】「実は、このカード、この先の場面のあらすじを読んで彩野さんが提案したんだ」")
    vms(2881, "NONVOICE", "【彩野】「この先の、場面……」")
    vms(2882, "NONVOICE", "【直哉】「そう。ここのオマジナイの箇所、二つとも……結末は良くなくて」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2883, "NONVOICE", "【彩野】「あ、そうなんだ」")
    vms(2884, "NONVOICE", "【直哉】「それで、彩野さんが『だったら、絶対に効くオマジナイ』をつくってって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2885, "NONVOICE", "【彩野】「そっか……。うん。ありがとう、直哉くん」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2886, "NONVOICE", "【彩野】「じゃあ、ここの展開に『絶対に効くオマジナイ』も追加してもらっていい？」")
    vms(2887, "NONVOICE", "【直哉】「うん、もちろん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：オマジナイの効果』の選択肢（絶対に効く）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        gameSave.myCard[115].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[97].hold == -1 then
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
        if l1_3 == 97 then
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
            vms(2888, "NONVOICE", "『絶対に効くオマジナイ』のカードを見せてみよう。")
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

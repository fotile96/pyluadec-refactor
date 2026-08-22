local card_43_s2s_210_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2707, "NONVOICE", "【直哉】「ユウイチの誘いに対してアヤノさんが思い出す場面、だね」")
    vms(2708, "NONVOICE", "【彩野】「直哉くん、えっと、ユウイチが誘ってきた所のあらすじ、もう一度見せてもらっていい？」")
    vms(2709, "NONVOICE", "【直哉】「『夏の予定』だね」")
    comPoseDelete()
end
local card_43_s2s_210_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2710, "NONVOICE", "【彩野】「そっか。その場面ではまだ予定を決め切れていなかったから、もう一度聞いてきたんだ」")
    vms(2711, "NONVOICE", "【直哉】「あらすじはこんな感じで問題ないかな？」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『出かける場所』のあらすじを作成しました。")
    vms(2712, "NONVOICE", "【彩野】「うん、大丈夫。ありがとう、直哉くん」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[32].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_43_s2s_210_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 32 then
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
            vms(2713, "NONVOICE", "『夏の予定』のカードを彩野さんに見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_43_s2s_210_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

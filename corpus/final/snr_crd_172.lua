local card_172_s4s_620_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1387, "NONVOICE", "【直哉】「ここは、屋上でユウイチがアヤノさんを助け出す場面だね」")
    comPoseLoad("po2_aya_f_2_d")
    vms(1388, "NONVOICE", "【彩野】「うん。ユウイチもなんだかカッコいい感じだね」")
    vms(1389, "NONVOICE", "【直哉】「そうだよね。でも……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1390, "NONVOICE", "【彩野】「ん？ 何か気になるところがあった？」")
    vms(1391, "NONVOICE", "【直哉】「うん――『ユウイチがアヤノさんを助ける』シーンなんだけど――」")
    vms(1392, "NONVOICE", "【直哉】「他の物語……セクション１でも、同じ展開があったんだ」")
    vms(1393, "NONVOICE", "【彩野】「セクション１……」")
    vms(1394, "NONVOICE", "【直哉】「そう。セクション１で、ユウイチがアヤノさんを助ける場面なんだけど……」")
    comPoseDelete()
end
local card_172_s4s_620_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1395, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1396, "NONVOICE", "【彩野】「……うん、確かに……同じかも」")
    vms(1397, "NONVOICE", "【直哉】「セクション１の方はアヤノさんが主人公で、こちらはユウイチが主人公」")
    vms(1398, "NONVOICE", "【直哉】「視点は違うけど、描いている要素は同じ、だと思う」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1399, "NONVOICE", "【彩野】「でも、どうしてなんだろう？ なんでセクション４とセクション１は同じなんだろう？」")
    vms(1400, "NONVOICE", "【直哉】「わからない、わからないけど――」")
    vms(1401, "NONVOICE", "【直哉】「これだけ『重なる要素』が多いと言うことは、やっぱり何かの意味があるのは確かだと思う」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1402, "NONVOICE", "【彩野】「うん……そうだよね……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『アヤノは意識を取り戻す』のあらすじを作成しました。")
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
    card_172_s4s_620_intro()
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
            vms(1403, "NONVOICE", "セクション１で、『ユウイチがアヤノさんを助ける』場面……")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_172_s4s_620_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3852, "NONVOICE", "【直哉】「階段でバランスを崩したアヤノさんが、ユウイチに助けられて――慌てて身体を離す所、だね」")
    vms(3853, "NONVOICE", "【直哉】「でも、『いつかは別れが』の後にこのシーンに繋がるのは、どういうことなんだろう」")
    vms(3854, "NONVOICE", "【彩野】「うーん……。直哉くん、この後に展開される場面って、わかる？」")
    vms(3855, "NONVOICE", "この後の展開は、図書室で先生とユウイチが居るところをアヤノさんが目撃する場面だ。")
    vms(3856, "NONVOICE", "……。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3857, "NONVOICE", "【彩野】「あ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3858, "NONVOICE", "【彩野】「図書室と……先生……」")
    vms(3859, "NONVOICE", "【直哉】「物語の流れとしては、『いつかは別れが』って、思った後、図書室でユウイチとユカリ先生を目撃する……」")
    vms(3860, "NONVOICE", "【直哉】「そして、その先は――バッドエンド。良くない結末、だね」")
    vms(3861, "NONVOICE", "【直哉】「……」")
    vms(3862, "NONVOICE", "【彩野】「……良くない、結末……」")
    vms(3863, "NONVOICE", "【直哉】「……ここも、分岐を作った方がいいのかな？」")
    vms(3864, "NONVOICE", "【彩野】「あ……うん……そう……かも」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『でも、いつかは別れが』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
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
        if l1_3 == 80 then
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
            vms(3865, "NONVOICE", "この場面のあと、アヤノさんが目撃した、図書室の場面は――")
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

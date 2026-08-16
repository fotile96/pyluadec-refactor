local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2681, "NONVOICE", "【彩野】「ここは、ユウイチに対してアヤノが『好きでも嫌いでもない』と答える場面」")
    vms(2682, "NONVOICE", "【彩野】「だから、あらすじもシンプルだよ」")
    vms(2683, "NONVOICE", "【直哉】「でも……」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2684, "NONVOICE", "【彩野】「どうしたの？ 直哉くん」")
    vms(2685, "NONVOICE", "【直哉】「あ、いや……なんでもない。カードをつくるね」")
    vms(2686, "NONVOICE", "【彩野】「うん。お願い。すぐつくれちゃうね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ユウイチのことは……』のあらすじを作成しました。")
    vms(2687, "NONVOICE", "【直哉】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    l0_0()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

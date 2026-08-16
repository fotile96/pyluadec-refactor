local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3353, "NONVOICE", "【直哉】「階段のウワサについて『とりあえず聞く』場面なんだけど……」")
    vms(3354, "NONVOICE", "【直哉】「この返答をしても、物語が進まないみたいだね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3355, "NONVOICE", "【彩野】「『この返答をしても』？」")
    vms(3356, "NONVOICE", "【直哉】「実はね、もう一つの選択肢、『適当に聞く』の場面も同じような展開だったんだ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『とりあえず聞いてみる』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_2_e")
    vms(3357, "NONVOICE", "【彩野】「うーん……と言う事は……」")
    vms(3358, "NONVOICE", "【彩野】「この展開じゃ、だめって事なのかな……」")
    vms(3359, "NONVOICE", "【彩野】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[71].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    l0_0()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

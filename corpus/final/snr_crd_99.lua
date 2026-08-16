local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3879, "NONVOICE", "【直哉】「今度の『物語』は――セクション６、だね」")
    vms(3880, "NONVOICE", "【彩野】「うん……アヤノの物語」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『セクション６：アヤノ』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_1_c")
    vms(3881, "NONVOICE", "【彩野】「でも、直哉くん、このセクションは――」")
    vms(3882, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3883, "NONVOICE", "【彩野】「このセクションの、結末は……」")
    vms(3884, "NONVOICE", "【直哉】「僕は、彩野さんの物語を読みたいと思うよ」")
    vms(3885, "NONVOICE", "【直哉】「どんな結末になっても」")
    vms(3886, "NONVOICE", "【直哉】「これまでずっと、彩野さんの物語を、聞いてきたんだから」")
    vms(3887, "NONVOICE", "【彩野】「直哉くん……」")
    vms(3888, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3889, "NONVOICE", "【彩野】「……ありがとう」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[98].hold == -1 then
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

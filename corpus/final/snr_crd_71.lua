local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3344, "NONVOICE", "【直哉】「階段のウワサについて聞く場面だけど……」")
    vms(3345, "NONVOICE", "【直哉】「『例によって』って、言っちゃっていいのかな」")
    vms(3346, "NONVOICE", "【直哉】「適当に聞いていたらダメみたいだね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3347, "NONVOICE", "【彩野】「駄目みたい……って？ お話が進まない感じなの？」")
    vms(3348, "NONVOICE", "【直哉】「うん。一言で言うとそんな感じ」")
    vms(3349, "NONVOICE", "【直哉】「あらすじも……こうかな」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『適当に聞く』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_2_e")
    vms(3350, "NONVOICE", "【彩野】「ふむ……」")
    vms(3351, "NONVOICE", "【直哉】「もうちょっと――受け答えも、真剣に取り組む必要があるのかもしれないね」")
    vms(3352, "NONVOICE", "【彩野】「うーん……そっか……」")
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

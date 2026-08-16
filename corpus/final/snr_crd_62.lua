local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3128, "NONVOICE", "【彩野】「ここは、ナゾトキに間違いなく答えられたときの場面」")
    vms(3129, "NONVOICE", "【直哉】「わざわざ正解の場面が用意されてるって事は、ナゾトキは単なる通過点じゃなくて、後の展開に影響を及ぼす可能性があるってことかな」")
    vms(3130, "NONVOICE", "【彩野】「たぶん、そうだと思う」")
    vms(3131, "NONVOICE", "【直哉】「間違いが良い結果を生むとは思えないし……。ナゾトキにはちゃんと正解したほうがいいみたいだね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ナゾトキの正解』のあらすじを作成しました。")
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

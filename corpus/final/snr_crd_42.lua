local card_42_s2s_209_main = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2700, "NONVOICE", "【彩野】「ここは、ナゾトキの中に間違いがあったときの場面」")
    vms(2701, "NONVOICE", "【直哉】「あらすじとしてはシンプルだから、すぐまとめちゃえるね」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2702, "NONVOICE", "【彩野】「うん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ナゾトキの間違い』のあらすじを作成しました。")
    vms(2703, "NONVOICE", "【直哉】「そういえば、この前の千秋ちゃん――サクラさんの妹さんのお話だと、サクラさんはたくさん本を読んでいるということだったよ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2704, "NONVOICE", "【彩野】「サクラさん……」")
    vms(2705, "NONVOICE", "【直哉】「もしかしたら、現実の彩野さんとサクラさんも、どこかでこんなやりとりをしていたのかもしれないね」")
    vms(2706, "NONVOICE", "【彩野】「あ……うん。そうだね」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    card_42_s2s_209_main()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

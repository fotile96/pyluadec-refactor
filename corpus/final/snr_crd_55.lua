local card_55_s2s_380_main = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2909, "NONVOICE", "【彩野】「アヤノがオマジナイを終えたときの場面」")
    vms(2910, "NONVOICE", "【直哉】「この場面自体は特にこれと言って注意するところはないね。『終わった』ってしているだけで」")
    vms(2911, "NONVOICE", "【彩野】「うん。きっと、オマジナイの影響が出てくるのはもっと後の場面になってからだと思う」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『オマジナイ完了』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    card_55_s2s_380_main()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

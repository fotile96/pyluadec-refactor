local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2896, "NONVOICE", "【彩野】「『オマジナイ』はたぶん効くんじゃないかなあって思った後の場面だね」")
    vms(2897, "NONVOICE", "【直哉】「この場面自体はなんてことないんだけど、何というか……」")
    vms(2898, "NONVOICE", "【彩野】「ん？ どうしたの」")
    vms(2899, "NONVOICE", "【直哉】「ちょっとあまり良い流れではないよね。本気で取り組んでない感じが」")
    comPoseLoad("po2_aya_f_1_c")
    vms(2900, "NONVOICE", "【彩野】「あ、うん。……嫌なことが起こらなければいいけど」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『たぶん効くと思う』のあらすじを作成しました。")
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

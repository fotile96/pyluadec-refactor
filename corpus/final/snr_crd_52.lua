local card_52_s2s_350_main = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2889, "NONVOICE", "【彩野】「『絶対に効くオマジナイ』を選んだときの場面だね」")
    vms(2890, "NONVOICE", "【直哉】「うん。これだけ強く言ってるって事は、自分自身にも『これは効くね』って言い聞かせてる感じかな」")
    vms(2891, "NONVOICE", "【彩野】「絶対に効く……」")
    vms(2892, "NONVOICE", "【直哉】「だいたいオマジナイって、そういうものかもしれない」")
    comPoseLoad("po2_aya_f_2_a")
    vms(2893, "NONVOICE", "【彩野】「ん、どういうこと？」")
    vms(2894, "NONVOICE", "【直哉】「自分自身の意識を確認するって感じかな。オマジナイを通じて、意識を確認している感じ」")
    comPoseLoad("po2_aya_f_2_d")
    vms(2895, "NONVOICE", "【彩野】「あ……そうかもしれないね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『絶対に効くと思う』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    card_52_s2s_350_main()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

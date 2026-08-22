local card_54_s2s_370_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2901, "NONVOICE", "【彩野】「アヤノが、『まあやってもソンは無いんだし』って、オマジナイに取り掛かる場面」")
    vms(2902, "NONVOICE", "【直哉】「そうだね。どちらかというと、あまり積極的には取り組んでない感じ」")
    vms(2903, "NONVOICE", "【彩野】「うん」")
    vms(2904, "NONVOICE", "【直哉】「となると、この『やってソンはないオマジナイ』はこの場面と同じような感じなのかな」")
    comPoseDelete()
end
local card_54_s2s_370_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2905, "NONVOICE", "【彩野】「そっか。オマジナイに対して、『たぶん効く』と『やってソンはない』って思うと、どちらも同じような感じになるんだ」")
    vms(2906, "NONVOICE", "【直哉】「うん。これまでの流れを考えると、あまり物語的にはいい流れとは言えないかも」")
    vms(2907, "NONVOICE", "【彩野】「そうだね……ちょっといやな感じ、するね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『やってソンはないと思う』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[53].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_54_s2s_370_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 53 then
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
            vms(2908, "NONVOICE", "たぶん効くかなって、オマジナイに対して思った場面があったな……。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_54_s2s_370_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

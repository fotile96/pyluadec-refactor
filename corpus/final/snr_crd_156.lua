local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1027, "NONVOICE", "【直哉】「ここは、アヤノさんを捜しにユウイチが学校を探索するシーンだけど……」")
    vms(1028, "NONVOICE", "【彩野】「結局、この場面では見つからなかったんだね」")
    vms(1029, "NONVOICE", "【直哉】「うん。それでね、この後、『廊下のユウイチ』の場面に繋がるんだ」")
    comPoseLoad("po2_aya_f_2_a")
    vms(1030, "NONVOICE", "【彩野】「廊下のユウイチ？」")
    vms(1031, "NONVOICE", "【直哉】「あらすじカードをつくってあるから、それを見て貰った方が早いと思う」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1032, "NONVOICE", "【彩野】「廊下のユウイチ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1033, "NONVOICE", "【彩野】「でも、この結末は……」")
    vms(1034, "NONVOICE", "【直哉】「……どうしてもこの結末になっちゃうみたいだ」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1035, "NONVOICE", "【彩野】「バッドエンド……」")
    vms(1036, "NONVOICE", "【直哉】「うん。もしかしたら、展開を変えてあげる必要があるかもしれない」")
    vms(1037, "NONVOICE", "【彩野】「そうだね……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『探索：アヤノに何が？』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[157].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    l0_0()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 157 then
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
            vms(1038, "NONVOICE", "『廊下のユウイチ』のカードを彩野さんに見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_1()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

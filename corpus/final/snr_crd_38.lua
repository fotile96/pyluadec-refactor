local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2572, "NONVOICE", "【彩野】「直哉くん、ここのシーンだけど……」")
    vms(2573, "NONVOICE", "【彩野】「「好きと言い切った」後の分岐した先の場面のあらすじって、ある？」")
    vms(2574, "NONVOICE", "分岐した先。『ユウイチのことが好き』の場面の事だろうな……。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2575, "NONVOICE", "【彩野】「じゃあ直哉くん、ここに分岐を加えてもらっていい？」")
    vms(2576, "NONVOICE", "【直哉】「分岐？ ここで物語が分かれるの？」")
    vms(2577, "NONVOICE", "【彩野】「うん。『適当に濁す』。これが分岐」")
    vms(2578, "NONVOICE", "【直哉】「……でも、この場面って、サクラさんのオマジナイが絡んでくるから、ここを適当に濁しても、先は――」")
    comPoseLoad("po2_aya_f_1_d")
    vms(2579, "NONVOICE", "【彩野】「……いいの。私がつくりたいんだから」")
    vms(2580, "NONVOICE", "【直哉】「あ……う、うん」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2581, "NONVOICE", "【彩野】「ごめんね。でも、……お願い」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ユウイチへの想い』の選択肢（適当に濁す）を作成しました。")
    vms(2582, "NONVOICE", "【直哉】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[39].hold == -1 then
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
        if l1_3 == 39 then
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
            vms(2583, "NONVOICE", "『ユウイチのことが好き』の場面のあらすじを見せてみよう。")
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

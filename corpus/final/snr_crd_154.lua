local card_154_s4s_160_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(982, "NONVOICE", "【直哉】「サクラさんからメモを見せてもらった時の行動だね」")
    vms(983, "NONVOICE", "【直哉】「それで、『廊下のユウイチ』の展開のあらすじもつくってあるんだ」")
    comPoseLoad("po2_aya_f_2_a")
    vms(984, "NONVOICE", "【彩野】「あ、見せてもらっていい？」")
    vms(985, "NONVOICE", "【直哉】「うん……」")
    vms(986, "NONVOICE", "【直哉】「でも、ちょっと注意してね。展開は良くない……バッドエンドなんだ」")
    comPoseDelete()
end
local card_154_s4s_160_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(987, "NONVOICE", "【彩野】「あ……」")
    vms(988, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(989, "NONVOICE", "【彩野】「うん……確かに、これは良くない結末だね」")
    vms(990, "NONVOICE", "【直哉】「でね。ちょっと考えてみたんだけど――」")
    vms(991, "NONVOICE", "【直哉】「これまで彩野さんが話してくれた『物語』って、こんな感じでサクラさんから質問を受けて答える部分が結構たくさんあって――」")
    comPoseLoad("po2_aya_f_1_a")
    vms(992, "NONVOICE", "【彩野】「質問？」")
    vms(993, "NONVOICE", "【直哉】「うん。『コックリさんに興味がある？』とか、『オマジナイは？』、『階段のウワサは？』とか……」")
    comPoseLoad("po2_aya_f_2_d")
    vms(994, "NONVOICE", "【彩野】「……七不思議だ」")
    vms(995, "NONVOICE", "【直哉】「そうそう。でね。質問に対して、『興味を抱いてない』って答えた場合、やっぱりどれも結末はよくなかったんだ」")
    comPoseLoad("po2_aya_f_1_c")
    vms(996, "NONVOICE", "【彩野】「……よくない結末……バッドエンド」")
    vms(997, "NONVOICE", "【直哉】「うん。そういう事」")
    comPoseLoad("po2_aya_f_1_a")
    vms(998, "NONVOICE", "【彩野】「……そっか。それじゃあ、ここも」")
    vms(999, "NONVOICE", "僕は頷いた。")
    vms(1000, "NONVOICE", "【彩野】「直哉くん、『興味を惹かれた』展開、つくってもらっていい？」")
    vms(1001, "NONVOICE", "【直哉】「うん、了解」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：メモを見たとき』の選択肢（興味を惹かれた）を作成しました。")
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
    card_154_s4s_160_sel_intro()
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
            vms(1002, "NONVOICE", "『廊下のユウイチ』のあらすじを見せてみよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_154_s4s_160_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

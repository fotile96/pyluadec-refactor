local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1063, "NONVOICE", "【直哉】「この場面は、サクラさんのメモを見た時、ユウイチがどう思ったのか、なんだけど……」")
    vms(1064, "NONVOICE", "【直哉】「『下らない』と思った先は――やっぱり良くない結末だったよ」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1065, "NONVOICE", "【彩野】「そうなんだ……」")
    vms(1066, "NONVOICE", "【直哉】「この先の展開は、『屋上の人影』なんだけど――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1067, "NONVOICE", "【彩野】「……あ……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1068, "NONVOICE", "【彩野】「……良くない結末、だね……」")
    vms(1069, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1070, "NONVOICE", "【彩野】「でも、さっき直哉くん『やっぱり良くない結末だった』って言ったけど――」")
    vms(1071, "NONVOICE", "【彩野】「今までもこういう展開、あったの？」")
    vms(1072, "NONVOICE", "【直哉】「うん。そうなんだ。基本的に、この女の子――サクラさんから何か話題を振られたときは――」")
    vms(1073, "NONVOICE", "【直哉】「『下らない』とか、興味が無いようなそぶりを見せると、良くない結果になるみたいだね、『他の物語』でも」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1074, "NONVOICE", "【彩野】「……そっか……」")
    vms(1075, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1076, "NONVOICE", "【彩野】「それじゃあ……展開は『信じてみてもいい』かな」")
    vms(1077, "NONVOICE", "【直哉】「新しい展開の追加、だね」")
    vms(1078, "NONVOICE", "【彩野】「うん。カードをつくってもらっていい？」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：メモの内容』の選択肢（信じてみてもいい）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[165].hold == -1 then
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
        if l1_3 == 165 then
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
            vms(1079, "NONVOICE", "『屋上の人影』のカードを彩野さんに見せてみよう。")
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

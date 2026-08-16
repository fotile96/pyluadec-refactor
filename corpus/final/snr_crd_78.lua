local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_2_e")
    vms(3475, "NONVOICE", "【彩野】「直哉くん、ここの場面なんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(3476, "NONVOICE", "【彩野】「嫌な感じ……図書室に行くと、何か、良くないことが起きるような気がするの」")
    vms(3477, "NONVOICE", "彩野さんは眉間に皺を寄せながら言った。")
    vms(3478, "NONVOICE", "【彩野】「なんだろう、先生に関わるような……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3479, "NONVOICE", "【彩野】「先生に、なにか感情を抱いたと思うの。それが、なんだったのかなって……」")
    vms(3480, "NONVOICE", "アヤノさんが『先生』に抱いた感情。それは――")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(3481, "NONVOICE", "【彩野】「先生は信用できない……。こういう風にアヤノが思った……」")
    vms(3482, "NONVOICE", "【直哉】「うん。この後に展開する物語を見て、ね」")
    vms(3483, "NONVOICE", "ユカリ先生とユウイチが図書室で抱き合っている場面は――必要があったら見せることにしよう。")
    vms(3484, "NONVOICE", "僕から進んで、彩野さんには――見せたくなかった。")
    comPoseLoad("po2_aya_f_1_a")
    vms(3485, "NONVOICE", "【彩野】「直哉くん、ここは……やっぱり図書室に行くことが、『良くない事』を引き起こしてるような気がする」")
    vms(3486, "NONVOICE", "【直哉】「それじゃあ他の場所に？」")
    vms(3487, "NONVOICE", "【彩野】「うん。ここでは階段のウワサを聞いてるんだから、やっぱりウワサされてる場所に行って、調べてみてもいいと思う」")
    vms(3488, "NONVOICE", "【直哉】「直接、階段に行ってみるって事かな？」")
    vms(3489, "NONVOICE", "【彩野】「うん。カードをつくってもらっていい？」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：向かう場所』の選択肢（階段へ）を作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[107].hold == -1 then
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
        if l1_3 == 107 then
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
            vms(3490, "NONVOICE", "【彩野】「『先生は――』なんて思ったんだろう」")
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

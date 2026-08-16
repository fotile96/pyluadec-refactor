local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1273, "NONVOICE", "【直哉】「彩野さん、このアヤノさんのノートを調べる場面なんだけど……」")
    comPoseLoad("po2_aya_f_2_a")
    vms(1274, "NONVOICE", "【彩野】「どうかした？」")
    vms(1275, "NONVOICE", "【直哉】「うん、……実は、ここの場面の描写って――」")
    vms(1276, "NONVOICE", "【直哉】「これまでに聞いてきた『物語』が繋がっているように感じるんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1277, "NONVOICE", "【彩野】「繋がってる？ 同じって事？」")
    vms(1278, "NONVOICE", "【直哉】「えっとね……同じ……というか、要素……一部分が同じ、と言うか……」")
    vms(1279, "NONVOICE", "【彩野】「ふむ……」")
    vms(1280, "NONVOICE", "【直哉】「たとえば……『ノート』に書いてあったコックリさんの文字」")
    vms(1281, "NONVOICE", "【直哉】「コックリさんは、セクション１に出てきた『良くない結果』の場面と繋がってる」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1282, "NONVOICE", "【彩野】「あ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1283, "NONVOICE", "【彩野】「うん……コックリさん……してるね……」")
    vms(1284, "NONVOICE", "【直哉】「それでね、ノートに挟まっていた『名前の書いてある消しゴム』――」")
    vms(1285, "NONVOICE", "【直哉】「これはそのまま、セクション２に『消しゴムに名前を書いていた』場面があるんだ」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1286, "NONVOICE", "【彩野】「うん……」")
    vms(1287, "NONVOICE", "【彩野】「これは……直哉くん、どういう事なんだろう？」")
    vms(1288, "NONVOICE", "【直哉】「僕にも解らない。わからないけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1289, "NONVOICE", "【彩野】「……」")
    vms(1290, "NONVOICE", "【直哉】「この、物語――セクション４になって、繋がりの『密度』が高くなってきてる感じがする」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1291, "NONVOICE", "【彩野】「繋がりの、密度……」")
    vms(1292, "NONVOICE", "【直哉】「そう。これまでも部分部分で、物語が繋がってる部分はあったんだけど――」")
    vms(1293, "NONVOICE", "【直哉】「セクション４では、他と繋がってる箇所が、他のセクションより多いように思ったんだ」")
    vms(1294, "NONVOICE", "【彩野】「……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ノートに書かれた名前』のあらすじを作成しました。")
    comPoseDelete()
    vms(1295, "NONVOICE", "そして――")
    vms(1296, "NONVOICE", "ノートに書かれた、『さよなら』の文字。")
    vms(1297, "NONVOICE", "そこにも、意味はあるのだろうか……")
    vms(1298, "NONVOICE", "この物語の一部が、現実と繋がっているとしたら……")
    vms(1299, "NONVOICE", "……。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[23].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[50].hold == -1 then
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
        if l1_3 == 23 then
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
            vms(1300, "NONVOICE", "セクション１、サクラさんとアヤノさんがコックリさんをした場面の描写――『良くない結果』と、繋がっている……。")
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
    local l1_3 = 0
    local l1_4 = 0
    local l1_5 = -1
    while l1_3 < 1 do
        local l1_6 = oCard.selectCardObj()
        if l1_6 == 50 then
            break
        end
        if l1_6 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_4 == 1 then
            oCard.mesNG2()
            vms(1301, "NONVOICE", "セクション２では『消しゴムに名前』を書いた場面があった……。")
            comPoseDelete()
        end
        if l1_4 == 0 then
            oCard.mesNG()
            l1_4 = l1_4 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_2()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

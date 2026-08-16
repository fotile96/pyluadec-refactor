local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1364, "NONVOICE", "【直哉】「ここは、屋上でアヤノさんが腕を広げている所、だね……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1365, "NONVOICE", "【彩野】「その後は――バッドエンド……」")
    vms(1366, "NONVOICE", "【直哉】「うん。そうなんだけど……でも、このシーン……」")
    vms(1367, "NONVOICE", "【彩野】「どうかした？」")
    vms(1368, "NONVOICE", "【直哉】「うん。ここ、アヤノさんが手を広げている部分なんだけど――」")
    vms(1369, "NONVOICE", "【直哉】「他の物語――セクション２では、ユウイチが同じような行動をしていたんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1370, "NONVOICE", "【彩野】「え？ ユウイチが？」")
    vms(1371, "NONVOICE", "【直哉】「うん。あらすじを見て貰った方がいいと思う」")
    vms(1372, "NONVOICE", "【直哉】「セクション２のバッドエンドで――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1373, "NONVOICE", "【彩野】「あ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1374, "NONVOICE", "【彩野】「……」")
    vms(1375, "NONVOICE", "【彩野】「……うん……」")
    vms(1376, "NONVOICE", "【彩野】「確かに、ここの行動は似ているね……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1377, "NONVOICE", "【彩野】「直哉くん。もう一つ質問していい？」")
    vms(1378, "NONVOICE", "【直哉】「うん、なんだろう」")
    vms(1379, "NONVOICE", "【彩野】「ここのシーンでアヤノが言ってる、『約束守らないと』って、何の事だろう？」")
    vms(1380, "NONVOICE", "約束――")
    vms(1381, "NONVOICE", "【直哉】「うん……。これまで聞いてきた中で、『放課後の約束』とかはあったんだけど――」")
    vms(1382, "NONVOICE", "【直哉】「ただ、屋上の縁に立つ――それほど深刻な『約束』をした場面は……ちょっと浮かばないね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1383, "NONVOICE", "【彩野】「そっか……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1384, "NONVOICE", "【彩野】「教えてくれて、ありがとう、直哉くん」")
    vms(1385, "NONVOICE", "【直哉】「……こちらこそ、力になれずに、ごめんね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『腕をつかむ』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[57].hold == -1 then
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
        if l1_3 == 57 then
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
            vms(1386, "NONVOICE", "セクション２。屋上で、アヤノさんが『ユウイチの後ろ姿』を目撃する場面だ。")
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

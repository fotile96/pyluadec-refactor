local card_170_s4s_490_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1334, "NONVOICE", "【直哉】「屋上でアヤノさんを見つけたユウイチが、アヤノさんを呼び止めるシーンだね」")
    vms(1335, "NONVOICE", "【直哉】「ここの、『腕を掴む』展開のあらすじは既につくってあるよ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1336, "NONVOICE", "【彩野】「あ、見せてもらっていい？」")
    vms(1337, "NONVOICE", "【直哉】「うん。これも結果はあまり良くないけど……」")
    comPoseDelete()
end
local card_170_s4s_490_sel_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1338, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_d")
    vms(1339, "NONVOICE", "【彩野】「……確かに、良くない感じだね」")
    comPoseLoad("po2_aya_f_2_c")
    vms(1340, "NONVOICE", "【彩野】「あ、でも――」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1341, "NONVOICE", "【彩野】「さっき、直哉くん『これも結果はあまり良くない』と言ったけど――他にもそういう物語があったの？」")
    vms(1342, "NONVOICE", "【直哉】「うん。物語の展開は分岐しているけれど――初めに考えるような行動はどれも……良くない結果を生んでいて」")
    vms(1343, "NONVOICE", "【彩野】「そうなんだ。じゃあ、ここも変えた方がよいよね……」")
    vms(1344, "NONVOICE", "【直哉】「うん、たぶん……そうだと思う」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1345, "NONVOICE", "【彩野】「そっか……じゃ、直哉くん、ここ、分岐をつくってもらっていい？」")
    vms(1346, "NONVOICE", "【直哉】「どんな感じにしようか？」")
    comPoseLoad("po2_aya_f_1_e")
    vms(1347, "NONVOICE", "【彩野】「えっとね。『腕を掴む』ぐらいじゃ駄目だったから、グイッと『引き戻す』ような感じで、お願い」")
    vms(1348, "NONVOICE", "【直哉】「うん、了解。カードを作っておくね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：アヤノを――』の選択肢（腕を掴む）を作成しました。")
    comPoseLoad("po2_aya_f_1_a")
    cPlayOneshotMusic(cGetFileName("mus", "mus_12"))
    comEffectYellowIn(60)
    wait(60)
    vms(1349, "NONVOICE", "【彩野】「あ……」")
    vms(1350, "NONVOICE", "【直哉】「……ん？」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1351, "NONVOICE", "【彩野】「……えっと」")
    vms(1352, "NONVOICE", "【直哉】「どうかした？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1353, "NONVOICE", "【彩野】「ここの場面なんだけど……」")
    vms(1354, "NONVOICE", "【彩野】「……」")
    vms(1355, "NONVOICE", "【彩野】「…………」")
    vms(1356, "NONVOICE", "【彩野】「あ、う、ううん」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1357, "NONVOICE", "【彩野】「ごめんなさい。何でもない」")
    vms(1358, "NONVOICE", "【直哉】「でも……」")
    vms(1359, "NONVOICE", "【彩野】「ごめんなさい。本当になんでもないの」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1360, "NONVOICE", "【彩野】「気にしないで……。ごめんなさい」")
    vms(1361, "NONVOICE", "【直哉】「彩野さん……」")
    vms(1362, "NONVOICE", "……。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[171].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_170_s4s_490_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 171 then
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
            vms(1363, "NONVOICE", "【直哉】「『腕を掴む』時のあらすじを見せてみよう」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_170_s4s_490_sel_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

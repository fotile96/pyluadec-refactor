local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    comPoseLoad("po2_aya_f_2_e")
    vms(696, "NONVOICE", "【彩野】「うーん、直哉くん……」")
    vms(697, "NONVOICE", "【直哉】「どうしたの、彩野さん」")
    comPoseLoad("po2_aya_f_1_a")
    vms(698, "NONVOICE", "【彩野】「この物語って、学校の物語なんだよね？」")
    vms(699, "NONVOICE", "【直哉】「……そうだと思うよ。今までの展開からすると」")
    vms(700, "NONVOICE", "……。_n彩野さんの物語なのに、僕が答えてしまっていいのだろうか……。")
    vms(701, "NONVOICE", "【彩野】「だよね。『学校の物語』」")
    vms(702, "NONVOICE", "【彩野】「そして、この『物語』で主人公とされている人物は――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(703, "NONVOICE", "【彩野】「でも……そう……うん」")
    vms(704, "NONVOICE", "【彩野】「……私……なんだよね……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(705, "NONVOICE", "彩野さんは声を落としていった。")
    vms(706, "NONVOICE", "【直哉】「なんか、納得いかない、という感じ？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(707, "NONVOICE", "【彩野】「うん……。正直に言うとね。私、こんな感じの性格なのかなあ？」")
    vms(708, "NONVOICE", "【直哉】「いやそれは……うーん……」")
    vms(709, "NONVOICE", "【直哉】「そういう風に言われてみると、確かに現実の彩野さんよりは……少し活動的な感じがする」")
    vms(710, "NONVOICE", "【直哉】「僕も正直にいうと、これが『彩野さんだ』とされると、ちょっと違和感みたいなものはあるかもしれない」")
    vms(711, "NONVOICE", "【彩野】「そうだよね……」")
    vms(712, "NONVOICE", "【直哉】「物語だから……ある程度オーバーに書いた方が動かしやすいっていうのはあるのかもしれないけど」")
    vms(713, "NONVOICE", "【彩野】「なんで、私、『アヤノ』にしたんだろう……」")
    vms(714, "NONVOICE", "【彩野】「他の人じゃ、だめだったのかな」")
    vms(715, "NONVOICE", "【彩野】「カタカナ、なんだよね、『アヤノ』」")
    vms(716, "NONVOICE", "【直哉】「アヤノさんであり、彩野さんでない」")
    vms(717, "NONVOICE", "【彩野】「そういう事、なのかな」")
    comPoseLoad("po2_aya_f_2_d")
    vms(718, "NONVOICE", "【彩野】「ごめんね、へんな事聞いちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(719, "NONVOICE", "【直哉】「ううん。気になったことはどんどん聞いてくれていいから」")
    vms(720, "NONVOICE", "【直哉】「……手伝いたいんだ」")
    comPoseLoad("po2_aya_f_1_e")
    vms(721, "NONVOICE", "【彩野】「ありがとう。直哉くん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『答案を受け流す』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[10].hold == -1 then
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
        if l1_3 == 10 then
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
            vms(722, "NONVOICE", "【彩野】「この『物語』の主人公って……」")
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

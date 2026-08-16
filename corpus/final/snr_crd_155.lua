local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1003, "NONVOICE", "【直哉】「渡されたメモに対して、『興味が無い』と答えると、『彼女』は消えちゃうんだけど……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1004, "NONVOICE", "【彩野】「でも、『救えたのかもしれない』とか、『落ちた音』とか『消える』とか――なんなんだろう……」")
    vms(1005, "NONVOICE", "【直哉】「……彩野さん」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1006, "NONVOICE", "【彩野】「なにか、気がついた？」")
    vms(1007, "NONVOICE", "【直哉】「あ……うん。ちょっとね、思ったんだけど……」")
    vms(1008, "NONVOICE", "【直哉】「『消えた少女』や、『下の方から聞こえた音』……この場面は今まで読んできた物語の要素が複合的に組み合わさっているような気がするんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1009, "NONVOICE", "【彩野】「組み合わさってる……？」")
    vms(1010, "NONVOICE", "【直哉】「他の物語……セクション１でもこの少女――『サクラさん』がアヤノさんに話しかけたあと――」")
    vms(1011, "NONVOICE", "【直哉】「やはり、『消えて』しまった」")
    vms(1012, "NONVOICE", "【直哉】「直接的な『物語』の繋がりではないけれど、物語を構成する『要素』が似ているような気がしたんだ」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1013, "NONVOICE", "【彩野】「ふむ……」")
    vms(1014, "NONVOICE", "【彩野】「じゃあ、ここで聞こえた『音』も？」")
    vms(1015, "NONVOICE", "【直哉】「うん。恐らくこれは、『中庭』で起きたある出来事のキーワード――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1016, "NONVOICE", "【彩野】「あ……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1017, "NONVOICE", "【彩野】「中庭の、人だかり……」")
    vms(1018, "NONVOICE", "【直哉】「そう。そのカードの要素が含まれているような気がした」")
    vms(1019, "NONVOICE", "【彩野】「うん……直哉くんの言ってること、わかったような気がする」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1020, "NONVOICE", "【彩野】「でも、この『物語』の場面には、中庭には何も痕跡がなかったし、サクラさんは消えてしまったんだよね？」")
    vms(1021, "NONVOICE", "【直哉】「そう……そういう事になるね」")
    vms(1022, "NONVOICE", "【直哉】「だから、直接的な『繋がり』はないかもしれないけど、要素が繋がってるかもって、思ったんだ……」")
    vms(1023, "NONVOICE", "【彩野】「そっか……教えてくれてありがとう」")
    comPoseLoad("po2_aya_f_2_d")
    vms(1024, "NONVOICE", "【彩野】「『消えた』という点では共通してるんだけどねー……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『興味はない』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[95].hold == -1 then
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
        if l1_3 == 95 then
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
            vms(1025, "NONVOICE", "中庭の出来事を描写したカードは、『キーワード』として既につくっている。")
            vms(1026, "NONVOICE", "あのカードを彩野さんに見せてみよう。")
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

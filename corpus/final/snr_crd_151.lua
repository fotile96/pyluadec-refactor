local card_151_s4s_70_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(945, "NONVOICE", "【直哉】「ユウイチがメモの事をユカリ先生に聞く場面、だね」")
    vms(946, "NONVOICE", "【彩野】「メモの事はユカリ先生は知らなかったみたいなんだけど、このシーンの終わりで――」")
    comPoseLoad("po2_aya_f_2_d")
    vms(947, "NONVOICE", "【彩野】「どうしてユカリ先生が手なんか回す必要があったんだろう？」")
    vms(948, "NONVOICE", "【直哉】「それは――」")
    vms(949, "NONVOICE", "……この場面は、セクション３で、ユウイチとユカリ先生が抱き合っていた場面と、『繋がっている』ことは間違いない。")
    vms(950, "NONVOICE", "でも、その場面を『あらすじ』として彩野さんに教えてしまっていいものだろうか？")
    vms(951, "NONVOICE", "……。")
    vms(952, "NONVOICE", "……ここは……。")
    vms(953, "NONVOICE", "……隠しても、仕方ない。そう思う。")
    vms(954, "NONVOICE", "この場面を理解するには、図書室のシーンを知る必要があるのは明らかだから。")
    comPoseDelete()
end
local card_151_s4s_70_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_c")
    vms(955, "NONVOICE", "【彩野】「……え……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(956, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(957, "NONVOICE", "【彩野】「あ、そうなんだ……」")
    vms(958, "NONVOICE", "【直哉】「そう。このカードに書かれているみたいに――」")
    vms(959, "NONVOICE", "【直哉】「セクション３で、アヤノさんは『ユカリ先生とユウイチが抱き合っている』場面を目撃しているんだ」")
    vms(960, "NONVOICE", "【彩野】「だから、ユカリ先生はこんな風に、ユウイチに……」")
    vms(961, "NONVOICE", "【彩野】「……う、うん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(962, "NONVOICE", "【彩野】「……わかった」")
    vms(963, "NONVOICE", "【彩野】「……あらすじ、まとめる……ね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『図書室の先生』のあらすじを作成しました。")
    comPoseDelete()
    vms(964, "NONVOICE", "【直哉】「……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[80].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_151_s4s_70_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 80 then
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
            vms(965, "NONVOICE", "彩野さんにセクション３、『図書室で目撃』した場面を教えよう……。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_151_s4s_70_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

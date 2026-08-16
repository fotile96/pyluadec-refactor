local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2935, "NONVOICE", "【彩野】「ユウイチが、屋上から落ちた場面」")
    vms(2936, "NONVOICE", "【直哉】「……そうだね」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2937, "NONVOICE", "【彩野】「直哉くん、これ……」")
    vms(2938, "NONVOICE", "【直哉】「たぶん、オマジナイに失敗したときの場面だと思う」")
    vms(2939, "NONVOICE", "【彩野】「そう……なんだ……」")
    vms(2940, "NONVOICE", "オマジナイに失敗したときの場面は、もう一場面ある。")
    vms(2941, "NONVOICE", "……『中庭の人だかり』だ。")
    vms(2942, "NONVOICE", "僕はカードを彩野さんに見せることにした。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2943, "NONVOICE", "【直哉】「オマジナイに失敗したときの場面の、もう一つがこのカード」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2944, "NONVOICE", "【彩野】「……ユウイチ」")
    vms(2945, "NONVOICE", "彩野さんは僕からカードを受け取ると、眉間に僅かに皺を寄せ、そっとアイツの名前を口に出した。")
    vms(2946, "NONVOICE", "……そう、ユウイチだ。")
    vms(2947, "NONVOICE", "この場面で、ユウイチは屋上から転落している。『現実』と同じように。")
    vms(2948, "NONVOICE", "もし、この場面が『繋がっている』のだとしたら、中庭でウワサされている男子生徒は、ユウイチとみて良いだろう。")
    vms(2949, "NONVOICE", "でも……だとしても、なぜ？")
    vms(2950, "NONVOICE", "なぜ、彩野さんはこのシーンを物語に入れる必要があったんだ？")
    vms(2951, "NONVOICE", "ただ単にオマジナイに失敗するのなら、何も起こらなければいい。")
    vms(2952, "NONVOICE", "なぜ、ユウイチを『転落』させなきゃいけないんだ？")
    comPoseLoad("po2_aya_f_1_c")
    vms(2953, "NONVOICE", "【彩野】「オマジナイに失敗したから、ユウイチは屋上から落ちたんだね」")
    vms(2954, "NONVOICE", "【直哉】「え？」")
    vms(2955, "NONVOICE", "【彩野】「……この場面のあらすじ」")
    vms(2956, "NONVOICE", "【直哉】「あ、う、うん……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ユウイチの後ろ姿』のあらすじを作成しました。")
    vms(2957, "NONVOICE", "……。")
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
            vms(2958, "NONVOICE", "『中庭の人だかり』のカードを彩野さんに見せてみよう。")
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

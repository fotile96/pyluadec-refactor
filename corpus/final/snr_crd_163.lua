local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1129, "NONVOICE", "【直哉】「ユウイチが教室に戻ると、室内が荒れていた、という場面だけど――」")
    comPoseLoad("po2_aya_f_2_a")
    vms(1130, "NONVOICE", "【彩野】「『だけど？』」")
    vms(1131, "NONVOICE", "【直哉】「うん、それで、この場面なんだけど――既にあらすじを作成した場面の後半と、展開が同じような感じなんだ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1132, "NONVOICE", "【彩野】「そうなんだ。その場面のあらすじ、みせてもらっていい？」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1133, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1134, "NONVOICE", "【彩野】「ふむ……確かに同じみたいだね」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1135, "NONVOICE", "【彩野】「ちょっと、ここのシーン……気になるかな」")
    vms(1136, "NONVOICE", "【直哉】「気になる？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1137, "NONVOICE", "【彩野】「うん、なんか……生々しいっていうのかな。頭の中にパッと、映像が浮かぶの」")
    vms(1138, "NONVOICE", "【彩野】「椅子や机や、鞄が倒れてたりするところ」")
    vms(1139, "NONVOICE", "【直哉】「以前、彩野さんが見たかもしれない、ということ？」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1140, "NONVOICE", "【彩野】「うん……似たような事、現実に見たのかな……」")
    comPoseLoad("po2_aya_f_2_d")
    vms(1141, "NONVOICE", "【彩野】「って、さすがに私たちのクラス、誰かが突然暴れ出すなんて事、なかったよね？」")
    vms(1142, "NONVOICE", "【直哉】「はは……うん。悪戯でもこういうのはなかったと思うよ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1143, "NONVOICE", "【彩野】「だよね……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1144, "NONVOICE", "【彩野】「でも……それじゃあ、私、どこで見たんだろう……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『ひっくり返った机』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[155].hold == -1 then
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
        if l1_3 == 155 then
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
            vms(1145, "NONVOICE", "ここの展開は、メモを見たときに『興味はない』と伝えた後と同じかな……。")
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

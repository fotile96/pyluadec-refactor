local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3454, "NONVOICE", "【直哉】「陸上部のウワサを『きくちゃん』に聞く場面――」")
    vms(3455, "NONVOICE", "【直哉】「『きくちゃん』に、話を聞くんだね」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3456, "NONVOICE", "【彩野】「きくちゃん……」")
    vms(3458, "NONVOICE", "【直哉】「うん。前に彩野さんが話してくれた『物語』にも登場したんだ」")
    vms(3457, "NONVOICE", "【直哉】「これで『きくちゃん』が物語に関わってくるのは二回目になるかな」")
    vms(3459, "NONVOICE", "【直哉】「きくちゃんについては個別にカードをつくってるよ。これを見てもらった方が早いと思う」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3460, "NONVOICE", "【彩野】「……そっか。あ、それで二回目って事は、初めに登場した部分もあるって事だよね？」")
    vms(3461, "NONVOICE", "【直哉】「うん。カードを作ってあるよ」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3462, "NONVOICE", "【彩野】「そのカードも見せてもらっていい？」")
    vms(3463, "NONVOICE", "きくちゃんが最初に登場したシーン……。")
    vms(3464, "NONVOICE", "セクション１の、放課後の約束について聞いた所だったかな。")
    vms(3465, "NONVOICE", "「してる」「していない」「思い出せない」……一番初めにきくちゃんの描写が出てきたのは、どのシーンだっただろう？")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3466, "NONVOICE", "【彩野】「ふむ……なるほど」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3467, "NONVOICE", "【彩野】「きくちゃん……」")
    vms(3468, "NONVOICE", "【直哉】「うちのクラスに、こういうニックネームで呼ばれてた子は……ちょっと思い浮かばない」")
    vms(3469, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3470, "NONVOICE", "【彩野】「でも、ここでも、きくちゃんが出てきたって言うことは、やっぱりなにかしら、物語にとって意味があるキャラクタみたいだね」")
    vms(3471, "NONVOICE", "【直哉】「うん……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『陸上部のウワサ』のあらすじを作成しました。")
    vms(3472, "NONVOICE", "きくちゃん、か……")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[129].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[6].hold == -1 then
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
        if l1_3 == 129 then
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
            vms(3473, "NONVOICE", "きくちゃんについてのカードを見せてみよう。")
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
        if l1_6 == 6 then
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
            vms(3474, "NONVOICE", "セクション１の、放課後の約束について聞いた所だったかな……。")
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

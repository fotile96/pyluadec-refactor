local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3141, "NONVOICE", "【直哉】「休み時間、サクラさんとお話する場面、だね」")
    vms(3142, "NONVOICE", "【直哉】「あ、サクラさんと廊下で話す場面は――他の『物語』でも出てきたと思う」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3143, "NONVOICE", "【彩野】「他の物語？」")
    vms(3144, "NONVOICE", "【彩野】「えっと、どの場面か教えてくれる？」")
    vms(3145, "NONVOICE", "【直哉】「うん。セクション２の初めのほうだったんだけど……」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    vms(3146, "NONVOICE", "【彩野】「そっか、ここでは図書室でオマジナイを聞いたんだ」")
    vms(3147, "NONVOICE", "【直哉】「うん、そうみたいだね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『昼休みの廊下』のあらすじを作成しました。")
    comPoseDelete()
    vms(3148, "NONVOICE", "『コックリさん』、『オマジナイ』の次は『階段のウワサ』……か。")
    vms(3149, "NONVOICE", "まさにお約束的な展開と言えなくもないけど……。")
    vms(3150, "NONVOICE", "よくわからないのが――")
    vms(3151, "NONVOICE", "なぜ、彩野さんはこの『お約束』の物語をつくろうと思ったのか、という事だ……。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[34].hold == -1 then
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
        if l1_3 == 34 then
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
            vms(3152, "NONVOICE", "サクラさんとアヤノさんが話したのはいつの時間かな……。")
            vms(3153, "NONVOICE", "確か、休憩時間だったような。")
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

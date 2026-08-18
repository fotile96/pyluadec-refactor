local card_85_s3s_470_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3616, "NONVOICE", "【彩野】「直哉くん、ここの場面なんだけど――」")
    vms(3617, "NONVOICE", "【直哉】「バッドエンド……良くない結末……だね」")
    vms(3618, "NONVOICE", "【彩野】「うん……」")
    vms(3619, "NONVOICE", "【直哉】「でも、少し気になる事があるんだ」")
    comPoseLoad("po2_aya_f_1_b")
    vms(3620, "NONVOICE", "【彩野】「気になる事？」")
    vms(3621, "NONVOICE", "【直哉】「うん。結末は……その、残念な感じだったんだけど」")
    vms(3622, "NONVOICE", "【直哉】「なんというかね、要所が、これまでに彩野さんから聞いた物語要素と重なっていて」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3623, "NONVOICE", "【彩野】「そうなんだ……」")
    vms(3624, "NONVOICE", "【直哉】「うん。まず、屋上のサクラさん。これはセクション１で聞いた物語――」")
    comPoseDelete()
end
local card_85_s3s_470_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3625, "NONVOICE", "【彩野】「ふむ……確かにそうみたいだね」")
    vms(3626, "NONVOICE", "【直哉】「そして、『中庭』の場面」")
    vms(3627, "NONVOICE", "【直哉】「これはセクション２で出てきたバッドエンドにも、同じような場面があったんだ」")
    comPoseDelete()
end
local card_85_s3s_470_step3 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3628, "NONVOICE", "【彩野】「あ……なるほど」")
    vms(3629, "NONVOICE", "【彩野】「でも、この『重なり』は、どういう事なんだろう……」")
    vms(3630, "NONVOICE", "【直哉】「そうだね……。ここまでセクション１，２，３と物語を聞いてきて、思ったんだけど――」")
    vms(3631, "NONVOICE", "【彩野】「うん」")
    vms(3632, "NONVOICE", "【直哉】「少しずつ、物語が重なる部分が多くなってきたような気がするんだ」")
    vms(3633, "NONVOICE", "【彩野】「でも、同じ学校が舞台だったら……。色んなお話を聞くほど重複する部分は、やっぱり出てくる感じじゃないかな？」")
    vms(3634, "NONVOICE", "【直哉】「うーん、それもそっか……」")
    vms(3635, "NONVOICE", "【直哉】「……」")
    vms(3636, "NONVOICE", "【直哉】「でも、ちょっと違う感じもする」")
    comPoseLoad("po2_aya_f_2_a")
    vms(3637, "NONVOICE", "【彩野】「違う感じ？」")
    vms(3638, "NONVOICE", "【直哉】「たとえばセクション１と３は作中でも同じ日の出来事じゃないんだけど、同じような描写がでてきたり」")
    vms(3639, "NONVOICE", "【直哉】「何か、この場面に『伝えたかったこと』が含まれてるような気がする」")
    vms(3640, "NONVOICE", "【直哉】「……って、ごめんね。勝手になんか色々考えちゃって」")
    comPoseLoad("po2_aya_f_1_e")
    vms(3641, "NONVOICE", "【彩野】「ううん……。ありがとう。すごく、参考になるよ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『屋上』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[27].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[56].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_85_s3s_470_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 27 then
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
            vms(3642, "NONVOICE", "セクション１、屋上でサクラさんと対峙した場面――")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_85_s3s_470_resolve()
    local l1_3 = 0
    local l1_4 = 0
    local l1_5 = -1
    while l1_3 < 1 do
        local l1_6 = oCard.selectCardObj()
        if l1_6 == 56 then
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
            vms(3643, "NONVOICE", "セクション２、バッドエンドの場面の描写――")
            comPoseDelete()
        end
        if l1_4 == 0 then
            oCard.mesNG()
            l1_4 = l1_4 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_85_s3s_470_step3()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

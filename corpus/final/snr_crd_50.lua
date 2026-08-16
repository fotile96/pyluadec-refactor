local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2860, "NONVOICE", "【直哉】「消しゴムに名前を書くオマジナイ……。よくある事ではあるんだけど」")
    vms(2861, "NONVOICE", "【彩野】「ん、なにか気になるの？」")
    vms(2862, "NONVOICE", "【直哉】「うん。確か、セクション１でも出てきたんだ。消しゴム」")
    vms(2863, "NONVOICE", "【直哉】「えっとね、放課後の約束について考えるところで――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2864, "NONVOICE", "【直哉】「あれ？」")
    vms(2865, "NONVOICE", "【彩野】「どうかしたの、直哉くん」")
    vms(2866, "NONVOICE", "【直哉】「うん。ここで消しゴムを見て約束を思い出すと言うことは、このセクション２のお話って、セクション１の前になるのかな？」")
    vms(2867, "NONVOICE", "【彩野】「うーん、そうとも言い切れない感じがする。はっきり前、って言い切ってる部分があるわけでもないし……」")
    vms(2868, "NONVOICE", "【直哉】「ふむ……」")
    vms(2869, "NONVOICE", "【直哉】「と、言うことは、この箇所も物語が『繋がっている』事を示している描写になるのかな」")
    vms(2870, "NONVOICE", "【彩野】「うん。そうかもしれない」")
    vms(2871, "NONVOICE", "消しゴム。セクション１に続いてまた出てきたと言うことは、この道具が物語の何かのキーになっているということなのだろうか？")
    vms(2872, "NONVOICE", "もしかしたらまたどこかの『物語』で、消しゴムが出てくるのかもしれない。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『消しゴムに名前』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[5].hold == -1 then
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
        if l1_3 == 5 then
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
            vms(2873, "NONVOICE", "確か、約束をしている場面だったかな……。")
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

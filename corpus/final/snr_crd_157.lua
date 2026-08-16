local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1039, "NONVOICE", "【直哉】「この場面、屋上から飛び降りる、バッドエンドなんだけど――」")
    vms(1040, "NONVOICE", "【直哉】「彩野さん、ちょっと気がついた事があるんだ」")
    comPoseLoad("po2_aya_f_2_a")
    vms(1041, "NONVOICE", "【彩野】「気付いたこと……？」")
    vms(1042, "NONVOICE", "【直哉】「実はね、これと同じような場面が他の物語……セクション１にもあったんだ」")
    vms(1043, "NONVOICE", "【直哉】「それはアヤノさんが主観の――アヤノさんが物語の主人公だったんだけど」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1044, "NONVOICE", "【彩野】「セクション１、そんな物語が、あるんだね」")
    vms(1045, "NONVOICE", "【直哉】「うん。それで、この場面では『ユウイチ』が『屋上のアヤノさん』を見つけて、走り出すんだけど――」")
    vms(1046, "NONVOICE", "【直哉】「セクション１では、『気が付いたら屋上に居たアヤノさん』の場面が出てくるんだ」")
    vms(1047, "NONVOICE", "【直哉】「それも、行き着いた先はバッドエンドだったんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1048, "NONVOICE", "【彩野】「バッドエンド……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1049, "NONVOICE", "【彩野】「直哉くん、その物語を見せてもらっていい？」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1050, "NONVOICE", "【彩野】「あ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1051, "NONVOICE", "【彩野】「うん……。屋上にいた、アヤノ……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1052, "NONVOICE", "【彩野】「この、サクラさんって？」")
    vms(1053, "NONVOICE", "【直哉】「えっとね、屋上でユウイチが出会った『謎の少女』」")
    vms(1054, "NONVOICE", "【直哉】「他の物語と合わせて考えると、この子の名前は『サクラさん』だと思う」")
    vms(1055, "NONVOICE", "【彩野】「ふむ……」")
    vms(1056, "NONVOICE", "【直哉】「それで――このセクション１と呼んでいる物語。二つの物語は時間軸も違うけど、含んでる『要素』は似ているような感じがする」")
    vms(1057, "NONVOICE", "【彩野】「たしかに……そうだね」")
    vms(1058, "NONVOICE", "【彩野】「……どうしてだろう……」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『廊下のユウイチ』のあらすじを作成しました。")
    comPoseDelete()
    vms(1059, "NONVOICE", "付け加えるのなら――")
    vms(1060, "NONVOICE", "『現実』では、ユウイチがまず屋上から飛び降り、その後を追うようにして彩野さんは飛び降りた。")
    vms(1061, "NONVOICE", "なぜ、物語では『彩野さんが先に屋上から落ちる』事になっているのだろう……。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[28].hold == -1 then
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
        if l1_3 == 28 then
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
            vms(1062, "NONVOICE", "セクション１、『約束はまもらないと』では、屋上でサクラさんがアヤノさんににじり寄った……。")
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

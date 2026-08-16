local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1534, "NONVOICE", "【彩野】「屋上のサクラさん……」")
    vms(1535, "NONVOICE", "彩野さんは、ぽつりと呟いた。")
    vms(1536, "NONVOICE", "【彩野】「……この場面のあらすじは、こんな感じだね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『サクラさん』のあらすじを作成しました。")
    cStopBGMWrap()
    vms(1537, "NONVOICE", "【直哉】「あ、うん……」")
    vms(1538, "NONVOICE", "【直哉】「それでね、彩野さん、これを見てほしいんだ」")
    vms(1539, "NONVOICE", "僕は、彩野さんに屋上で見つけた『日記』と『いつかきみがみるお話。』を渡した。")
    cLoadPlaySE(cGetFileName("se", "se_101"), false)
    vms(1540, "NONVOICE", "彩野さんは日記に目を通すと、小さく頷いた。")
    comPoseLoad("po2_aya_f_1_b")
    vms(1541, "NONVOICE", "【彩野】「サクラさんの日記と、私の日記……」")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    vms(1542, "NONVOICE", "【直哉】「え、彩野さんのも？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1543, "NONVOICE", "【彩野】「うん。そう。私たち、交換日記……してたの」")
    vms(1544, "NONVOICE", "【彩野】「直哉くん、これ、どこに？」")
    vms(1545, "NONVOICE", "【直哉】「えっと、屋上にあったんだ。誰が置いたのかは、わからないんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1546, "NONVOICE", "【彩野】「そう……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1547, "NONVOICE", "【彩野】「私たちが病院に入院した時からの、日記……」")
    vms(1548, "NONVOICE", "【彩野】「……」")
    vms(1549, "NONVOICE", "【彩野】「……私、サクラさんと……」")
    vms(1550, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1551, "NONVOICE", "【彩野】「……直哉くん」")
    vms(1552, "NONVOICE", "【彩野】「もしかしたら、物語が――浮かぶかもしれない」")
    vms(1553, "NONVOICE", "【彩野】「この、サクラさんの日記と、物語と――直哉くんのおかげで」")
    vms(1554, "NONVOICE", "【直哉】「え？」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1555, "NONVOICE", "【彩野】「……ね、直哉くん。これまでの『物語』を、もう一度見せてもらっていい？」")
    vms(1556, "NONVOICE", "【直哉】「物語……セクション１から４の物語で、いいんだよ_rね？」")
    vms(1557, "NONVOICE", "【彩野】「うん。ごめんね、面倒なこと頼んじゃって」")
    vms(1558, "NONVOICE", "【直哉】「あ、ううん。全然」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1559, "NONVOICE", "すべての物語と言うことは……セクション３Ｂや、４Ｂも入る……か。")
    vms(1560, "NONVOICE", "【直哉】「えっとね、セクション１のあらすじは――」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1561, "NONVOICE", "【彩野】「コックリさん……」")
    vms(1562, "NONVOICE", "【直哉】「セクション２のあらすじは――」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1563, "NONVOICE", "【彩野】「オマジナイ……」")
    vms(1564, "NONVOICE", "【直哉】「セクション３Ａのあらすじは――」")
    comPoseDelete()
end
local l0_3 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(1565, "NONVOICE", "【彩野】「階段……ユウイチ……」")
    vms(1566, "NONVOICE", "【直哉】「セクション３Ｂのあらすじは――」")
    comPoseDelete()
end
local l0_4 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_b")
    vms(1567, "NONVOICE", "【彩野】「キス、しないんだ……」")
    vms(1568, "NONVOICE", "【直哉】「セクション４Ａのあらすじは――」")
    comPoseDelete()
end
local l0_5 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1569, "NONVOICE", "【彩野】「ユウイチ……」")
    vms(1570, "NONVOICE", "【直哉】「セクション４Ｂのあらすじは――」")
    comPoseDelete()
end
local l0_6 = function()
    oCard.cardAnswerNonvoiceTrue()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_1_c")
    vms(1571, "NONVOICE", "【彩野】「サクラさん……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1572, "NONVOICE", "【彩野】「……」")
    vms(1573, "NONVOICE", "【彩野】「……直哉くん」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1574, "NONVOICE", "【彩野】「それとね、『いつかきみがみるお話。』のあらすじも教えて貰って、いい？」")
    vms(1575, "NONVOICE", "【直哉】「……うん。『いつかきみがみるお話。』の、あらすじは――」")
    comPoseDelete()
end
local l0_7 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(1576, "NONVOICE", "【彩野】「うん……」")
    comPoseLoad("po2_aya_f_1_a")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_1_x"))
    vms(1577, "NONVOICE", "【彩野】「でね、直哉くん。これを元に『あらすじ』をつくることができると思う」")
    vms(1578, "NONVOICE", "【直哉】「あらすじ？ サクラさんの日記から物語のあらすじをつくる、という事？」")
    vms(1579, "NONVOICE", "【彩野】「ちょっと待って。書くもの、かりていいかな？」")
    vms(1580, "NONVOICE", "【直哉】「あ、うん……はい」")
    vms(1581, "NONVOICE", "僕はペンを彩野さんに渡す。")
    vms(1582, "NONVOICE", "【彩野】「ありがとう！」")
    vms(1583, "NONVOICE", "彩野さんは椅子を引くと、机に向かった。")
    comPoseDelete()
    cLoadPlaySE(cGetFileName("se", "se_51"), false)
    wait(120)
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 179 .. "_a"), "『サクラの日記：９月１３日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 180 .. "_a"), "『サクラの日記：７月（書きかけ）』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 181 .. "_a"), "『サクラの日記：９月１６日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 182 .. "_a"), "『サクラの日記：９月１６日（夜）』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 183 .. "_a"), "『サクラの日記：９月２０日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 184 .. "_a"), "『サクラの日記：９月２２日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 185 .. "_a"), "『サクラの日記：９月２３日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 186 .. "_a"), "『サクラの日記：９月２９日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 187 .. "_a"), "『サクラの日記：断片』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 188 .. "_a"), "『サクラの日記：１０月３日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 189 .. "_a"), "『サクラの日記：１１月１２日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 190 .. "_a"), "『サクラの日記：２月１３日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 93 .. "_a"), "『アヤノの返信：９月２５日』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 191 .. "_a"), "『アヤノの返信：１０月３０日』のあらすじを作成しました。")
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_1_a")
    comPoseLoad("po2_aya_f_1_b")
    vms(1584, "NONVOICE", "【彩野】「このあらすじを元に、物語を作ってみるね」")
    vms(1585, "NONVOICE", "【直哉】「物語を……今の彩野さんが……？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1586, "NONVOICE", "彩野さんはコクリと頷く。")
    vms(17043, "NONVOICE", "【彩野】「直哉くんに、サクラさんと私の事、教えてあげられると思う」")
    vms(1587, "NONVOICE", "【彩野】「≪昔、書いた物語を辿る≫じゃなくて、≪今、つくりながら≫になるから……」")
    vms(1588, "NONVOICE", "【彩野】「≪物語の途中で≫直哉くんに質問しちゃうかもしれないけど……」")
    vms(1589, "NONVOICE", "【直哉】「あ、うん。そこはもちろん！ なにかあったら、どんどん聞いてくれれば」")
    vms(1590, "NONVOICE", "……。")
    vms(1591, "NONVOICE", "あ、でも、彩野さんが先にあらすじをつくったと言うことは……。")
    cPlayOneshotMusic(cGetFileName("mus", "mus_13"))
    comEffectYellowIn(60)
    wait(60)
    vms(1592, "NONVOICE", "≪あらすじのスキップはできるけど、スキップしていたら物語が追えなくなる≫事もありそうだ……。")
    cPlayOneshotMusic(cGetFileName("mus", "mus_12"))
    comEffectYellowIn(60)
    wait(60)
    vms(1593, "NONVOICE", "≪この物語……セクション５では、あらすじスキップしないで物語を聞く≫事が必要になると思う。注意しないといけないな……。")
    comPoseLoad("po2_aya_f_1_e")
    vms(1594, "NONVOICE", "【彩野】「ありがとう。……二人で協力して、物語をつくろうね」")
    vms(1595, "NONVOICE", "【直哉】「う、うん……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1596, "NONVOICE", "【彩野】「じゃあ、始めるね」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1597, "NONVOICE", "【彩野】「セクション５、サクラさんとアヤノの物語を」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 178 .. "_a"), "『セクション５：サクラ』のあらすじを作成しました。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. 195 .. "_a"), "『セクション５：アヤノ』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        gameSave.myCard[178].hold = 1
        gameSave.myCard[179].hold = 1
        gameSave.myCard[180].hold = 1
        gameSave.myCard[181].hold = 1
        gameSave.myCard[182].hold = 1
        gameSave.myCard[183].hold = 1
        gameSave.myCard[184].hold = 1
        gameSave.myCard[185].hold = 1
        gameSave.myCard[186].hold = 1
        gameSave.myCard[187].hold = 1
        gameSave.myCard[188].hold = 1
        gameSave.myCard[189].hold = 1
        gameSave.myCard[190].hold = 1
        gameSave.myCard[93].hold = 1
        gameSave.myCard[191].hold = 1
        gameSave.myCard[195].hold = 1
        comAyanoTimeRefresh()
    end
    comPoseDelete()
    cStopBGMWrap()
    wait(1)
    comEffectFadeOut(120)
    cPlayBGMWrap(cGetFileName("bgm", "bgm_1_x"))
    wait(1)
    layerLoad(layerName.pose1, cGetFileName("cutin", "tut_0_a"))
    layerLoad(layerName.scene, "")
    switchScreen(0, "", 60)
    wait(60)
    vms(17044, "NONVOICE", "【セクション５について】セクション５では、これまでのように「彩野がカードを見ながら物語を辿る」のではなく、「彩野がカードを見ながら物語を作成する」セクションです。")
    cLoadPlaySE(cGetFileName("se", "se_101"), false)
    wait(1)
    layerLoad(layerName.pose2, cGetFileName("event", "eve_56_x"))
    switchScreen(0, "", 120)
    layerMoveScale(layerName.pose2, 45, 45, 120)
    layerMovePosition(layerName.pose2, 100, -40, 120)
    wait(120)
    vms(17045, "NONVOICE", "【セクション５について】ストーリーモード中、何度か彩野から質問される場面があります。")
    vms(17046, "NONVOICE", "【セクション５について】彩野の言葉に耳をかたむけ、正解のカードを選んでいくことで物語が進行します。")
    wait(120)
    vms(17047, "NONVOICE", "【スキップ……】先ほど、彩野はサクラと彩野の日記の内容をみて、『物語より先にあらすじカード』を作成しました。")
    vms(17048, "NONVOICE", "【スキップ……】つまり、物語が未完成なまま、先に「あらすじ」という物語の枠を決めてしまったことになります。")
    vms(17049, "NONVOICE", "【スキップ……】このため、セクション５ではあらすじスキップを多用すると「物語で語るべき事」を見落としてしまう……かもしれません。")
    cStopBGMWrap()
    wait(1)
    comEffectFadeOut(120)
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[133].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[134].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[135].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[136].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[137].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[138].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[145].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[25].hold == -1 then
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
        if l1_3 == 133 then
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
            vms(1598, "NONVOICE", "セクション１のあらすじは――")
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
        if l1_6 == 134 then
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
            vms(1599, "NONVOICE", "セクション２のあらすじは――")
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
    local l1_6 = 0
    local l1_7 = 0
    local l1_8 = -1
    while l1_6 < 1 do
        local l1_9 = oCard.selectCardObj()
        if l1_9 == 135 then
            break
        end
        if l1_9 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_7 == 1 then
            oCard.mesNG2()
            vms(1600, "NONVOICE", "Ｓｅｃｔｉｏｎ３Ａのあらすじ――")
            comPoseDelete()
        end
        if l1_7 == 0 then
            oCard.mesNG()
            l1_7 = l1_7 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_3()
    local l1_9 = 0
    local l1_10 = 0
    local l1_11 = -1
    while l1_9 < 1 do
        local l1_12 = oCard.selectCardObj()
        if l1_12 == 136 then
            break
        end
        if l1_12 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_10 == 1 then
            oCard.mesNG2()
            vms(1601, "NONVOICE", "セクション３Ｂのあらすじは――")
            comPoseDelete()
        end
        if l1_10 == 0 then
            oCard.mesNG()
            l1_10 = l1_10 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_4()
    local l1_12 = 0
    local l1_13 = 0
    local l1_14 = -1
    while l1_12 < 1 do
        local l1_15 = oCard.selectCardObj()
        if l1_15 == 137 then
            break
        end
        if l1_15 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_13 == 1 then
            oCard.mesNG2()
            vms(1602, "NONVOICE", "セクション４Ａのあらすじは――")
            comPoseDelete()
        end
        if l1_13 == 0 then
            oCard.mesNG()
            l1_13 = l1_13 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_5()
    local l1_15 = 0
    local l1_16 = 0
    local l1_17 = -1
    while l1_15 < 1 do
        local l1_18 = oCard.selectCardObj()
        if l1_18 == 138 then
            break
        end
        if l1_18 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_16 == 1 then
            oCard.mesNG2()
            vms(1603, "NONVOICE", "セクション４Ｂのあらすじは――")
            comPoseDelete()
        end
        if l1_16 == 0 then
            oCard.mesNG()
            l1_16 = l1_16 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_6()
    local l1_18 = 0
    local l1_19 = 0
    local l1_20 = -1
    while l1_18 < 1 do
        local l1_21 = oCard.selectCardObj()
        if l1_21 == 145 then
            break
        end
        if l1_21 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_19 == 1 then
            oCard.mesNG2()
            vms(1604, "NONVOICE", "『いつかきみがみるお話。』の、あらすじは――")
            comPoseDelete()
        end
        if l1_19 == 0 then
            oCard.mesNG()
            l1_19 = l1_19 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_7()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

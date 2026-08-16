local l0_0 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(445, "NONVOICE", "【彩野】「うーん……」")
    vms(446, "NONVOICE", "【彩野】「直哉くん……」")
    vms(447, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(448, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(449, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(450, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(451, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(452, "NONVOICE", "途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(453, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local l0_1 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(454, "NONVOICE", "【直哉】「屋上でサクラさんと話す場面、だね……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(455, "NONVOICE", "【彩野】「……サクラさん……」")
    vms(456, "NONVOICE", "【直哉】「サクラさんの日記で言うと、時期的に考えて ９月、１０月ぐらいになるのかな……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(457, "NONVOICE", "【彩野】「サクラさんの日記……？」")
    vms(458, "NONVOICE", "【直哉】「うん。……あ、他の物語――セクション５では、サクラさんと彩野さんの日記を元に、物語を作成したんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(459, "NONVOICE", "【彩野】「セクション５……」")
    vms(460, "NONVOICE", "【彩野】「えっと、直哉くん。その、セクション５の『物語』を見せてもらっていい？」")
    vms(461, "NONVOICE", "【直哉】「『セクション５のあらすじ』でいいかな」")
    vms(462, "NONVOICE", "【彩野】「あ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(463, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(464, "NONVOICE", "【彩野】「ごめんね、詳しく知りたいから、ひととおり見せてもらっていいかな？」")
    vms(465, "NONVOICE", "【直哉】「うん、了解。まずは、『サクラの日記：９月１３日』だね――」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_b")
    vms(466, "NONVOICE", "【彩野】「……サクラさんと、私、出会って……」")
    vms(467, "NONVOICE", "【直哉】「サクラの日記：７月（書きかけ）――」")
    comPoseDelete()
end
local l0_3 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_b")
    vms(468, "NONVOICE", "【彩野】「うん。サクラさんと、こんな風に、会ってた……」")
    vms(469, "NONVOICE", "【直哉】「サクラの日記：９月１６日――」")
    comPoseDelete()
end
local l0_4 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(470, "NONVOICE", "【彩野】「ユウイチ……」")
    vms(471, "NONVOICE", "【直哉】「サクラの日記：９月１６日（夜）――」")
    comPoseDelete()
end
local l0_5 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(472, "NONVOICE", "【彩野】「サクラさん……」")
    vms(473, "NONVOICE", "【直哉】「サクラの日記：９月２０日――」")
    comPoseDelete()
end
local l0_6 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(474, "NONVOICE", "【彩野】「ユウイチ……ドーナツ……」")
    vms(475, "NONVOICE", "【直哉】「サクラの日記：９月２２日――」")
    comPoseDelete()
end
local l0_7 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(476, "NONVOICE", "【彩野】「電話……してた……」")
    vms(477, "NONVOICE", "【直哉】「サクラの日記：９月２３日――」")
    comPoseDelete()
end
local l0_8 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(478, "NONVOICE", "【彩野】「サクラさん、苦しそうで……」")
    vms(479, "NONVOICE", "【直哉】「サクラの日記：９月２９日――」")
    comPoseDelete()
end
local l0_9 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_b")
    vms(480, "NONVOICE", "【彩野】「歌……」")
    vms(481, "NONVOICE", "【直哉】「サクラの日記：断片――」")
    comPoseDelete()
end
local l0_10 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(482, "NONVOICE", "【彩野】「オマジナイ……」")
    vms(483, "NONVOICE", "【直哉】「サクラの日記：１０月３日――」")
    comPoseDelete()
end
local l0_11 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(484, "NONVOICE", "【彩野】「身体が……」")
    vms(485, "NONVOICE", "【直哉】「サクラの日記：１１月１２日――」")
    comPoseDelete()
end
local l0_12 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(486, "NONVOICE", "【彩野】「中庭……」")
    vms(487, "NONVOICE", "【直哉】「サクラの日記：２月１３日――」")
    comPoseDelete()
end
local l0_13 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(488, "NONVOICE", "【彩野】「サクラさん……」")
    vms(489, "NONVOICE", "【直哉】「アヤノの返信：９月２５日――」")
    comPoseDelete()
end
local l0_14 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_2_e")
    cStopBGMWrap()
    vms(490, "NONVOICE", "【彩野】「そう、病室で……ユウイチ」")
    vms(491, "NONVOICE", "【直哉】「これで最後だね。アヤノの返信：１０月３０日――」")
    comPoseDelete()
end
local l0_15 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(492, "NONVOICE", "【彩野】「……」")
    vms(493, "NONVOICE", "【彩野】「…………」")
    vms(494, "NONVOICE", "【彩野】「でも……」")
    vms(495, "NONVOICE", "【直哉】「どうかした？」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『Ｔｒｕｅ Ｃｏｌｏｒ』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_2_e")
    vms(496, "NONVOICE", "【彩野】「物語の、続きを聞いてもらえば、わかるから」")
    vms(497, "NONVOICE", "【直哉】「彩野……さん……」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[179].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[180].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[181].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[182].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[183].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[184].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[185].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[186].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[187].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[188].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[189].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[190].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[93].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[191].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    local l1_0 = false
    l0_1()
    local l1_1 = 0
    local l1_2 = 0
    local l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 179 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(498, "NONVOICE", "サクラの日記：９月１３日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_2()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 180 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(499, "NONVOICE", "サクラの日記：７月（書きかけ）――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_3()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 181 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(500, "NONVOICE", "サクラの日記：９月１６日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_4()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 182 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(501, "NONVOICE", "サクラの日記：９月１６日（夜）――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_5()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 183 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(502, "NONVOICE", "サクラの日記：９月２０日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_6()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 184 then
            break
        end
        if l1_4 == -1 then
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(503, "NONVOICE", "サクラの日記：９月２２日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            l1_0 = true
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_7()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 185 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(504, "NONVOICE", "サクラの日記：９月２３日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_8()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 186 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(505, "NONVOICE", "サクラの日記：９月２９日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_9()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 187 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(506, "NONVOICE", "サクラの日記：断片――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_10()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 188 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(507, "NONVOICE", "サクラの日記：１０月３日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_11()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 189 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(508, "NONVOICE", "サクラの日記：１１月１２日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_12()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 190 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(509, "NONVOICE", "サクラの日記：２月１３日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_13()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 93 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(510, "NONVOICE", "アヤノの返信：９月２５日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    l0_14()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 191 then
            break
        end
        if l1_4 == -1 then
            l1_0 = true
            oCard.cancelCard()
            comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
            run(cGetFileName("script", "snr_fragment_main"))
            quit()
        end
        if l1_2 == 1 then
            l1_0 = true
            oCard.mesNG2()
            vms(511, "NONVOICE", "アヤノの返信：１０月３０日――")
            comPoseDelete()
        end
        if l1_2 == 0 then
            oCard.mesNG()
            l1_2 = l1_2 + 1
            comPoseDelete()
        end
        wait(30)
    end
    if l1_0 == true then
        l0_0()
    end
    l0_15()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local l0_0 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(371, "NONVOICE", "【彩野】「うーん……」")
    vms(372, "NONVOICE", "【彩野】「直哉くん……」")
    vms(373, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(374, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(375, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(376, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(377, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(378, "NONVOICE", "途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(379, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local l0_1 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(380, "NONVOICE", "【直哉】「アヤノさんがノートにつけていたタイトル、だね」")
    vms(381, "NONVOICE", "【彩野】「物語の、タイトル……」")
    vms(382, "NONVOICE", "【直哉】「えっとね。『失われた夢の物語』の展開は、カードをつくってあるよ」")
    comPoseLoad("po2_aya_f_2_a")
    vms(383, "NONVOICE", "【彩野】「そうなんだ……。見せてもらっていい？」")
    vms(384, "NONVOICE", "【直哉】「うん。えっとね、これになるよ」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(385, "NONVOICE", "【彩野】「そっか……」")
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(386, "NONVOICE", "【彩野】「……」")
    vms(387, "NONVOICE", "【彩野】「……物語の、タイトル……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(388, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(389, "NONVOICE", "【彩野】「ごめんなさい、直哉くん、ちょっと手間を掛けさせてしまうんだけど……」")
    vms(390, "NONVOICE", "【直哉】「ん、なんだろう？」")
    vms(391, "NONVOICE", "【彩野】「これまで私たちが作ってきた物語のあらすじを、もう一度、一通り最初から見せてもらっていいかな？」")
    vms(392, "NONVOICE", "【直哉】「物語――各セクションのあらすじカードだね」")
    vms(393, "NONVOICE", "【彩野】「うん……そうだと思う……」")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    vms(394, "NONVOICE", "【直哉】「まず、セクション１の物語のあらすじは――」")
    comPoseDelete()
end
local l0_3 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(395, "NONVOICE", "【彩野】「コックリさんをして……」")
    vms(396, "NONVOICE", "【直哉】「セクション２のあらすじは――」")
    comPoseDelete()
end
local l0_4 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(397, "NONVOICE", "【彩野】「オマジナイをして……」")
    vms(398, "NONVOICE", "【直哉】「セクション３Ａのあらすじは――」")
    comPoseDelete()
end
local l0_5 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(399, "NONVOICE", "【彩野】「階段のウワサ……」")
    vms(400, "NONVOICE", "【直哉】「セクション３Ｂのあらすじは――」")
    comPoseDelete()
end
local l0_6 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(401, "NONVOICE", "【彩野】「花火を見て……」")
    vms(402, "NONVOICE", "【直哉】「セクション４Ａのあらすじは――」")
    comPoseDelete()
end
local l0_7 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(403, "NONVOICE", "【彩野】「メモを見て……」")
    vms(404, "NONVOICE", "【直哉】「セクション４Ｂのあらすじは――」")
    comPoseDelete()
end
local l0_8 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(405, "NONVOICE", "【彩野】「屋上……」")
    vms(406, "NONVOICE", "【直哉】「セクション５のあらすじは――」")
    comPoseDelete()
end
local l0_9 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(407, "NONVOICE", "【彩野】「……サクラさん……」")
    vms(408, "NONVOICE", "【直哉】「それとね、彩野さん」")
    vms(409, "NONVOICE", "【彩野】「……うん」")
    vms(410, "NONVOICE", "【直哉】「実はこの間、誰かからのメモが彩野さんの手帳に挟まれてたんだ」")
    vms(411, "NONVOICE", "【彩野】「メモ？」")
    vms(412, "NONVOICE", "【直哉】「うん。メモの内容は『お話のありかは、屋上にある』だった」")
    vms(413, "NONVOICE", "【直哉】「それで実際に屋上に行ったら、本当に『物語』の冊子を発見したんだ」")
    comPoseLoad("po2_aya_f_2_e")
    vms(414, "NONVOICE", "【彩野】「物語……」")
    vms(415, "NONVOICE", "【直哉】「うん。その物語のタイトルは――」")
    comPoseDelete()
end
local l0_10 = function()
    oCard.cardAnswerNonvoiceTrue()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(416, "NONVOICE", "【彩野】「いつか、君が、見る、お話……」")
    vms(417, "NONVOICE", "【彩野】「屋上……メモ……」")
    vms(418, "NONVOICE", "【彩野】「……夕焼け……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(419, "NONVOICE", "【彩野】「直哉くん……」")
    vms(420, "NONVOICE", "【直哉】「うん」")
    vms(421, "NONVOICE", "【彩野】「さっき、セクション４の物語を教えて貰ったんだけど――」")
    vms(422, "NONVOICE", "【彩野】「ここで、ユウイチのポケットに入っていたメモの内容って、どういう内容かわかる？」")
    vms(423, "NONVOICE", "【直哉】「えっとね、確か、『ポケットの中のメモ』の場面に書いてあったはず――」")
    comPoseDelete()
end
local l0_11 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(424, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(425, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(426, "NONVOICE", "【彩野】「……タイトル……」")
    vms(427, "NONVOICE", "【彩野】「……わかった」")
    vms(428, "NONVOICE", "【直哉】「……え？」")
    vms(429, "NONVOICE", "【彩野】「思い出したの。サクラさんと作った、『物語』のタイトル」")
    vms(430, "NONVOICE", "【直哉】「物語の、タイトル」")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    vms(431, "NONVOICE", "【彩野】「うん。――『<Ｔｒｕｅ Ｃｏｌｏｒ,トゥルー カラー>』」")
    vms(432, "NONVOICE", "【彩野】「これが、物語のタイトルだよ、直哉くん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ノート』の選択肢（Ｔｒｕｅ Ｃｏｌｏｒ）を作成しました。")
    comPoseDelete()
    vms(433, "NONVOICE", "『Ｔｒｕｅ Ｃｏｌｏｒ』……。")
    vms(434, "NONVOICE", "……。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[192].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
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
    if gameSave.myCard[139].hold == -1 then
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
    if gameSave.myCard[146].hold == -1 then
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
        if l1_4 == 192 then
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
            vms(435, "NONVOICE", "『失われた夢の物語』のあらすじを見せてみよう。")
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
        if l1_4 == 133 then
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
            vms(436, "NONVOICE", "セクション１のあらすじは――")
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
        if l1_4 == 134 then
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
            vms(437, "NONVOICE", "セクション２のあらすじは――")
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
        if l1_4 == 135 then
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
            vms(438, "NONVOICE", "セクション３Ａのあらすじは――")
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
        if l1_4 == 136 then
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
            vms(439, "NONVOICE", "セクション３Ｂのあらすじは――")
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
        if l1_4 == 137 then
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
            vms(440, "NONVOICE", "セクション４Ａのあらすじは――")
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
        if l1_4 == 138 then
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
            vms(441, "NONVOICE", "セクション４Ｂのあらすじは――")
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
        if l1_4 == 139 then
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
            vms(442, "NONVOICE", "セクション５のあらすじは――")
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
        if l1_4 == 145 then
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
            vms(443, "NONVOICE", "屋上で見つけた『物語』のタイトルは――")
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
        if l1_4 == 146 then
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
            vms(444, "NONVOICE", "セクション４、『ポケットの中のメモ』の場面――")
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
    l0_11()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

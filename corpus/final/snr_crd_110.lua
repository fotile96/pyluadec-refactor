local l0_0 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(559, "NONVOICE", "【彩野】「うーん……」")
    vms(560, "NONVOICE", "【彩野】「直哉くん……」")
    vms(561, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(562, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(563, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(564, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(565, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(566, "NONVOICE", "途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(567, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local l0_1 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    comPoseLoad("po2_aya_f_1_c")
    vms(568, "NONVOICE", "【直哉】「……彩野さん……」")
    vms(569, "NONVOICE", "【彩野】「これで、この物語は、終わりなの」")
    comPoseLoad("po2_aya_f_2_e")
    vms(570, "NONVOICE", "【彩野】「……ごめんなさい。直哉くん」")
    vms(571, "NONVOICE", "【彩野】「……」")
    vms(572, "NONVOICE", "【直哉】「……彩野さん……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(573, "NONVOICE", "【彩野】「……」")
    vms(574, "NONVOICE", "【直哉】「…………」")
    vms(575, "NONVOICE", "【直哉】「…………わかった」")
    comPoseLoad("po2_aya_f_1_a")
    vms(576, "NONVOICE", "【彩野】「直哉くん……」")
    vms(577, "NONVOICE", "【直哉】「彩野さんがそう言うのなら。ここで物語が終わりなら、これまでのあらすじをまとめる」")
    comPoseLoad("po2_aya_f_1_c")
    vms(578, "NONVOICE", "【彩野】「直哉くん……」")
    vms(579, "NONVOICE", "【直哉】「それが僕の役目だった」")
    vms(580, "NONVOICE", "【直哉】「僕はこれまで、物語の終わりの時にはその話のあらすじを『まとめ』ていた」")
    vms(581, "NONVOICE", "【直哉】「だからここで物語が終わりと彩野さんが言うなら、やっぱりまとめてみたいと思う」")
    comPoseLoad("po2_aya_f_2_e")
    vms(582, "NONVOICE", "【彩野】「でも……」")
    vms(583, "NONVOICE", "【直哉】「うん。わかってる。でも、たとえ≪途中で物語が書けなくなっても≫そこまでの物語をまとめてみたいんだ」")
    vms(584, "NONVOICE", "【彩野】「……」")
    vms(585, "NONVOICE", "【直哉】「……始めて、いい？」")
    comPoseLoad("po2_aya_f_1_c")
    vms(586, "NONVOICE", "【彩野】「うん……お願い……します」")
    vms(587, "NONVOICE", "【直哉】「――このセクションは、セクション３、サクラさんとの会話で『階段のウワサ』に興味がないと答えたところから展開した」")
    vms(588, "NONVOICE", "【直哉】「アヤノさんは、本当はこんなウワサを望んでいた」")
    comPoseDelete()
end
local l0_2 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(589, "NONVOICE", "【彩野】「……」")
    vms(590, "NONVOICE", "【直哉】「サクラさんはアヤノさんと手紙をやりとりする中で、簡単なクイズを出題することがあった」")
    vms(591, "NONVOICE", "【直哉】「アヤノさんは、クイズの問題を解くときに役立つからと、ある場所で手紙を読むことが多かった」")
    comPoseDelete()
end
local l0_3 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    vms(592, "NONVOICE", "【彩野】「……」")
    vms(593, "NONVOICE", "【直哉】「病院を抜け出したサクラさんは、学校の屋上でアヤノさんにノートを託した」")
    vms(594, "NONVOICE", "【直哉】「その場面のあらすじは――」")
    comPoseDelete()
end
local l0_4 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_c")
    cStopBGMWrap()
    vms(595, "NONVOICE", "【彩野】「……」")
    vms(596, "NONVOICE", "【直哉】「最後に。彩野さんが一番初めに語った物語。『ある子が学校にくる物語』」")
    vms(597, "NONVOICE", "【直哉】「この『ある子』に含ませていた≪物語の登場人物≫は、彩野さんと――」")
    comPoseDelete()
end
local l0_5 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(598, "NONVOICE", "【彩野】「でも……」")
    vms(599, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(600, "NONVOICE", "【彩野】「……ごめんなさい」")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_15_x"))
    vms(601, "NONVOICE", "【直哉】「これで、物語は……終わりなんだね」")
    comPoseLoad("po2_aya_f_2_e")
    vms(602, "NONVOICE", "【彩野】「そう。明るい結末も、暗い結末も、≪なにもない≫の」")
    vms(603, "NONVOICE", "【彩野】「先が書けない。……思いつかなかった」")
    comPoseLoad("po2_aya_f_1_c")
    vms(604, "NONVOICE", "【彩野】「私に物語をつくる事なんて、できなかったの」")
    vms(605, "NONVOICE", "【直哉】「……彩野さん……」")
    vms(606, "NONVOICE", "【彩野】「ごめんなさい……」")
    vms(607, "NONVOICE", "【彩野】「……」")
    vms(608, "NONVOICE", "【彩野】「ここまで……ずっと」")
    comPoseLoad("po2_aya_f_2_e")
    vms(609, "NONVOICE", "【彩野】「ずっとずっと、直哉くんが隣にいてくれて――」")
    vms(610, "NONVOICE", "【彩野】「『物語』を辿ることを、手伝ってくれたんだよね？」")
    vms(611, "NONVOICE", "【彩野】「……」")
    vms(612, "NONVOICE", "【彩野】「……ごめんなさい」")
    vms(613, "NONVOICE", "【直哉】「……僕のした事なんて、大したことじゃないよ」")
    vms(614, "NONVOICE", "【彩野】「そんな……」")
    vms(615, "NONVOICE", "【直哉】「セクション６、『中庭の雪』の場面……つくるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『中庭の雪』のあらすじを作成しました。")
    comPoseLoad("po2_aya_f_1_c")
    vms(616, "NONVOICE", "【彩野】「……本当に、ごめんなさい」")
    comPoseLoad("po2_aya_f_1_e")
    vms(617, "NONVOICE", "【彩野】「今までありがとう、直哉くん」")
    vms(618, "NONVOICE", "【彩野】「……学校には……」")
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(619, "NONVOICE", "【彩野】「もう、来なくていいと思うから」")
    comEffectWhiteOut(200)
    wait(200)
    comSectionCardEndSection()
    doScriptScene = "s6f-10"
    run(cGetFileName("script", "snr_s6_10_f"))
    quit()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[98].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[102].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[104].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[124].hold == -1 then
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
        if l1_4 == 98 then
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
            vms(620, "NONVOICE", "【直哉】「――このセクションは、セクション３、サクラさんとの会話で『階段のウワサ』に興味がないと答えたところから展開した」")
            vms(621, "NONVOICE", "【直哉】「アヤノさんは、本当はこんなウワサを望んでいた」")
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
        if l1_4 == 102 then
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
            vms(622, "NONVOICE", "【直哉】「サクラさんはアヤノさんと手紙をやりとりする中で、簡単なクイズを出題することがあった」")
            vms(623, "NONVOICE", "【直哉】「アヤノさんは、クイズの問題を解くときに役立つからと、ある場所で手紙を読むことが多かった」")
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
        if l1_4 == 104 then
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
            vms(624, "NONVOICE", "【直哉】「病院を抜け出したサクラさんは、学校の屋上でアヤノさんにノートを託した」")
            vms(625, "NONVOICE", "【直哉】「その場面のあらすじは――」")
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
        if l1_4 == 124 then
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
            vms(626, "NONVOICE", "【直哉】「最後に。彩野さんが一番初めに語った物語。『ある子が学校にくる物語』」")
            vms(627, "NONVOICE", "【直哉】「この『ある子』に含ませていた人物は、彩野さんと――」")
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
    if l1_0 == true then
        l0_0()
    end
    l0_5()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local l0_0 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(1683, "NONVOICE", "【彩野】「うーん……」")
    vms(1684, "NONVOICE", "【彩野】「直哉くん……」")
    vms(1685, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(1686, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(1687, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1688, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1689, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(1690, "NONVOICE", "ということは、この『まとめ』では続いて正解のカードを選ぶ必要がある――つまり、途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(1691, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local l0_1 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1692, "NONVOICE", "【直哉】「２月の、中庭……」")
    vms(1693, "NONVOICE", "【直哉】「彩野さん、この結末は……」")
    vms(1694, "NONVOICE", "彩野さんはゆっくり頷いた。")
    vms(1695, "NONVOICE", "【彩野】「私とサクラさんの日記から考えた物語、だから」")
    vms(1696, "NONVOICE", "【彩野】「……」")
    vms(1697, "NONVOICE", "この物語――セクション５のあらすじは、その大半が――")
    vms(1698, "NONVOICE", "『サクラさんと彩野さんの交換日記を見ながら、彩野さんが作成したあらすじ』だ。")
    vms(1699, "NONVOICE", "千秋ちゃん――は、サクラさんについてこう言っていた。")
    wait(1)
    comEffectFadeOut(60)
    wait(1)
    layerLoad(layerName.bg1, cGetFileName("bg", "bg_11_a_0"))
    switchScreen(0, "", 60)
    wait(60)
    vms(1700, "NONVOICE", "【千秋】「死にました」")
    vms(1701, "NONVOICE", "【直哉】「……え」")
    vms(1702, "NONVOICE", "僕は言葉に詰まった。")
    vms(1703, "NONVOICE", "千秋ちゃんはよどみなく喋り続けた。")
    vms(1704, "NONVOICE", "【千秋】「６年前。病気でした。死にました。今はいません」")
    wait(1)
    comEffectFadeOut(60)
    wait(1)
    layerLoad(layerName.bg1, cGetFileName("bg", "bg_1_a_0"))
    switchScreen(0, "", 60)
    wait(60)
    vms(1705, "NONVOICE", "……。")
    vms(1706, "NONVOICE", "セクション５の内容は、『現実に残された日記のやりとり』をベースに作成されている……内容は、ほぼ事実という事だろう。")
    comPoseLoad("po2_aya_f_1_a")
    vms(1707, "NONVOICE", "【彩野】「……直哉くん、ちょっとお願いしていい？」")
    vms(1708, "NONVOICE", "【直哉】「あ……どうかした？」")
    vms(1709, "NONVOICE", "【彩野】「えっとね。屋上に行きたいの。扉、開いてるかな？」")
    vms(1710, "NONVOICE", "【直哉】「鍵……うん。大丈夫。鍵を持ってるよ。由加里先生から預かってるから」")
    vms(1711, "NONVOICE", "【彩野】「そっか……鍵、掛かってるんだ」")
    vms(1712, "NONVOICE", "【彩野】「……由加里先生……」")
    wait(1)
    comEffectFadeOut(60)
    vms(1713, "NONVOICE", "【直哉】「千秋ちゃんも来る？」")
    vms(1714, "NONVOICE", "僕が聞くと、千秋ちゃんは首を横に振った。")
    vms(1715, "NONVOICE", "……たぶん、彼女なりに気を遣ってくれているのだろう。")
    vms(1716, "NONVOICE", "遅くなるようなら先に帰っていてと伝え、僕たちは屋上に向かった。")
    cLoadPlaySE(cGetFileName("se", "se_46"), false)
    wait(1)
    comEffectFadeOut(60)
    wait(1)
    layerLoad(layerName.bg1, cGetFileName("bg", "bg_4_b_0"))
    switchScreen(0, "", 60)
    wait(60)
    wait(1)
    comEffectFadeOut(60)
    wait(1)
    layerLoad(layerName.bg1, cGetFileName("bg", "bg_14_b_0"))
    switchScreen(0, "", 60)
    wait(60)
    vms(1717, "NONVOICE", "階段をのぼる途中、僕はもう一度これまでの『セクション５』のあらすじを彩野さんに説明した。")
    vms(1718, "NONVOICE", "【彩野】「……サクラさん」")
    vms(1719, "NONVOICE", "ぽつりとそう言うと、彩野さんは深いため息をついた。")
    cLoadPlaySE(cGetFileName("se", "se_44"), false)
    wait(1)
    comEffectFadeOut(60)
    wait(1)
    layerLoad(layerName.bg1, cGetFileName("bg", "bg_7_b_0"))
    switchScreen(0, "", 60)
    wait(60)
    cPlayOneshotMusic(cGetFileName("mus", "mus_43"))
    vms(1720, "NONVOICE", "夕日が目に眩しかった。")
    vms(1721, "NONVOICE", "【直哉】「彩野さん……大丈夫？」")
    vms(1722, "NONVOICE", "彩野さんは屋上の入り口に立ったまま、こめかみに人差し指をあて、眉間に皺を寄せ、目を強く閉じている。")
    vms(1723, "NONVOICE", "何かを深く考え込むように。")
    vms(1724, "NONVOICE", "【彩野】「……直哉くん、もう一度サクラさんの日記――。私たちが出会った部分の『９月の物語』を見せてもらっていい？」")
    comPoseDelete()
end
local l0_2 = function()
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(60)
    comPoseLoad("po2_aya_f_1_a")
    vms(1725, "NONVOICE", "【彩野】「ありがとう……それじゃあ、物語の私たちが、『中庭でお話した場面』のあらすじも、お願いしていい？」")
    comPoseDelete()
end
local l0_3 = function()
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(60)
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_1_a")
    vms(1726, "NONVOICE", "【彩野】「最後に、『私が書いた日記』を見せてもらっていいかな。９月の日記になると思う」")
    comPoseDelete()
end
local l0_4 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1727, "NONVOICE", "【彩野】「……ありがとう。直哉くん」")
    vms(1728, "NONVOICE", "彩野さんはフェンスの側に寄るとじっと外を見つめている。")
    vms(1729, "NONVOICE", "そろそろ日が暮れかけていた。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『２月、中庭』のあらすじを作成しました。")
    vms(1730, "NONVOICE", "【彩野】「私たちの日記。交換日記」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1731, "NONVOICE", "【彩野】「私たちは日記をやりとりしていた」")
    vms(1732, "NONVOICE", "【彩野】「病院で聞いたウワサ話や、学校のウワサや、学校の出来事を日記に書いてた」")
    vms(1733, "NONVOICE", "【直哉】「――現実の彩野さんと、サクラさんの日記」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1734, "NONVOICE", "【彩野】「うん……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1735, "NONVOICE", "【彩野】「……」")
    cStopBGMWrap()
    vms(1736, "NONVOICE", "その時、彩野さんは『あ』と小さく声を上げた。")
    comPoseLoad("po2_aya_f_1_a")
    vms(1737, "NONVOICE", "【彩野】「……もしかしたら、直哉くん、私、サクラさんから『物語』で『学校の階段のウワサ』を聞いたこと、なかった？」")
    vms(1738, "NONVOICE", "【直哉】「階段のウワサ……うん。セクション３と４の『物語』にそういうのがあったよ」")
    vms(1739, "NONVOICE", "【彩野】「と言うことは、サクラさんから聞かれたんだよね。『階段のウワサに興味があるか、無いか』って」")
    vms(1740, "NONVOICE", "【直哉】「あ――えっと――うん。聞かれたと思う」")
    cPlayOneshotMusic(cGetFileName("mus", "mus_12"))
    comEffectYellowIn(60)
    wait(60)
    vms(1741, "NONVOICE", "たしか、『放課後の約束をしていない』、ユウイチとの予定に『行かない』で辿り着く場面だ。")
    comPoseLoad("po2_aya_f_1_c")
    vms(1742, "NONVOICE", "【彩野】「そこからまた、≪次の物語が展開される≫と思う」")
    vms(1743, "NONVOICE", "【直哉】「……アヤノさんと、サクラさんの物語が？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1744, "NONVOICE", "【彩野】「うん。でも、もしかしたら……」")
    vms(1745, "NONVOICE", "【直哉】「……ん、どうかした？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1746, "NONVOICE", "【彩野】「あ、ううん。ごめんなさい。なんでもない」")
    vms(1747, "NONVOICE", "【彩野】「どうしよっか？ 今から考えてみる……？ それとも、明日にする？」")
    vms(1748, "NONVOICE", "【直哉】「そうだね……もう夕方だし、明日にした方がいいかもしれない」")
    vms(1749, "NONVOICE", "【彩野】「そう――だよね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1750, "NONVOICE", "【彩野】「……」")
    vms(1751, "NONVOICE", "【彩野】「…………えっとね」")
    vms(1752, "NONVOICE", "【彩野】「……」")
    vms(1753, "NONVOICE", "【彩野】「直哉くん……」")
    vms(1754, "NONVOICE", "【直哉】「うん」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1755, "NONVOICE", "【彩野】「たぶん、もうじきこの『物語』も結末が近いような気がするの」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1756, "NONVOICE", "【彩野】「だから、もしかしたら明日で物語は――」")
    vms(1757, "NONVOICE", "【直哉】「あ……」")
    vms(1758, "NONVOICE", "物語の結末が、近づいている――？")
    vms(1759, "NONVOICE", "【直哉】「……うん」")
    comSectionCardEndSection()
    doScriptScene = "s5f-10"
    run(cGetFileName("script", "snr_s5_10_f"))
    quit()
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[179].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[194].hold == -1 then
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
            vms(1760, "NONVOICE", "【彩野】「……直哉くん、もう一度サクラさんの日記――。私たちが出会った部分の『９月の物語』を見せてもらっていい？」")
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
        if l1_4 == 194 then
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
            vms(1761, "NONVOICE", "【彩野】「……物語の私たちが、『中庭でお話した場面』のあらすじも、お願いしていい？」")
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
        if l1_4 == 93 then
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
            vms(1762, "NONVOICE", "【彩野】「最後に、『私が書いた日記』を見せてもらっていいかな。９月の日記になると思う」")
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
    wait(60)
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(120)
    l0_4()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

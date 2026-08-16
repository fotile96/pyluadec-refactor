local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2297, "NONVOICE", "【直哉】「彩野さん、この場面なんだけど……」")
    vms(2298, "NONVOICE", "【彩野】「えっと、あらすじを考えるんだよね」")
    vms(2299, "NONVOICE", "【直哉】「うん。なにかうまい言い方はないかな」")
    vms(2300, "NONVOICE", "【彩野】「……うーん……。廊下を走って……それで……」")
    vms(2301, "NONVOICE", "【彩野】「ユウイチとテストの点数を競って……負けた方が何かをおごるんだよね……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2302, "NONVOICE", "…………。")
    vms(2303, "NONVOICE", "彩野さんは考え込んでいる。ここは何か、あらすじを考える上で助けになるカードを渡した方がいいだろう。")
    vms(2304, "NONVOICE", "…………。")
    vms(2305, "NONVOICE", "カード、だ。")
    vms(2306, "NONVOICE", "ひとつ、気になる事があった。")
    oCard.showMiniIn(cGetFileName("card", "crd_132_a"))
    vms(2307, "NONVOICE", "彩野さんがこの場面の物語を語る中で、《ハンバーガー》という言葉を口に出した時だけ、僅かに眉間に皺を寄せたのだ。")
    vms(2308, "NONVOICE", "これはどういう事だろうか？")
    vms(2309, "NONVOICE", "【直哉】「彩野さん、もしかしてお腹空いてたりする？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2310, "NONVOICE", "【彩野】「ううん。大丈夫。まだ時間も……」")
    vms(2311, "NONVOICE", "そう言うと、彩野さんは黒板の上の時計を確認した。")
    vms(2312, "NONVOICE", "【彩野】「お昼には早いし。もしかして、直哉くん、お昼にしたい？」")
    vms(2313, "NONVOICE", "【直哉】「ううん。大丈夫」")
    oCard.showMiniOut()
    comPoseLoad("po2_aya_f_1_b")
    vms(2314, "NONVOICE", "【彩野】「朝ご飯、ちゃんと食べた？」")
    vms(2315, "NONVOICE", "【直哉】「えーと、まあ……ほどほどに」")
    comPoseLoad("po2_aya_f_1_e")
    vms(2316, "NONVOICE", "【彩野】「ちゃんと食べないと、だめだよ」")
    vms(2317, "NONVOICE", "【直哉】「あ……はい……気をつけます」")
    vms(2318, "NONVOICE", "朝ご飯……。")
    oCard.showMiniIn(cGetFileName("card", "crd_132_a"))
    vms(2319, "NONVOICE", "い、いや、違う。朝ご飯の話じゃない。ハンバーガーの事だった。")
    vms(2320, "NONVOICE", "もしかしたらこれは、彩野さんにとって『意味のある』言葉なのかもしれない。")
    oCard.showMiniOut()
    comPoseLoad("po2_aya_f_1_a")
    vms(2321, "NONVOICE", "さて、もう一度考えてみよう。")
    vms(2322, "NONVOICE", "この場面の『あらすじ』に対して、彩野さんがつぶやいていた事。")
    vms(2323, "NONVOICE", "『負けた方が何かをおごる』か。うん。そうなると、見せるカードは……。")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2324, "NONVOICE", "【彩野】「そっか。負けた方がハンバーガーをおごるんだったね」")
    vms(2325, "NONVOICE", "【彩野】「ユウイチとテストの点数を競争する賭けをしていて、負けた方がおごらなくちゃいけない」")
    vms(2326, "NONVOICE", "【彩野】「テストの事をアヤノは忘れてたから、急いで教室に行って、勉強しようとしてたんだ」")
    vms(2327, "NONVOICE", "【彩野】「――こういう『あらすじ』だね。直哉くん、手伝ってくれてありがとう」")
    oCard.showMiniIn(cGetFileName("card", "crd_132_a"))
    vms(2328, "NONVOICE", "やっぱり、彩野さんはこのカードで『あらすじ』を考える事ができた。")
    vms(2329, "NONVOICE", "という事は、このカード――彩野さんの口調が変わったときにメモしたこのカード――には『意味』があったということになる。")
    vms(2330, "NONVOICE", "つまり、『あらすじ』をつくる上でのヒント、何かのきっかけになる『言葉』だった、ということだ。")
    vms(2331, "NONVOICE", "彩野さんが物語を語る中で、口調に変化が見られた言葉は、気になる言葉としてメモしておいたほうがいいだろう。")
    oCard.showMiniOut()
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『放課後の約束』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[132].hold == -1 then
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
        if l1_3 == 132 then
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
            vms(2332, "NONVOICE", "【彩野】「……たぶん、食べるものだったと思う」")
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

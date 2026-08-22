local card_167_s4s_420_sel_step6 = function()
    cStopBGMWrap()
    comPoseLoad("po2_aya_f_2_e")
    vms(1192, "NONVOICE", "【彩野】「うーん……」")
    vms(1193, "NONVOICE", "【彩野】「直哉くん……」")
    vms(1194, "NONVOICE", "【彩野】「ごめんなさい、考えが上手くまとまらないの」")
    vms(1195, "NONVOICE", "【直哉】「出したカードが間違っていると言うこと？」")
    vms(1196, "NONVOICE", "【彩野】「ううん、渡してくれたカードはあっていると思うんだけど……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1197, "NONVOICE", "【彩野】「途中でちょっと、集中ができなくなっちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1198, "NONVOICE", "そういえば、間違ったカード渡してしまった時があった。")
    vms(1199, "NONVOICE", "ということは、この『まとめ』では続いて正解のカードを選ぶ必要がある――つまり、途中一度でもカードの選択を間違えるとだめみたいだ。")
    vms(1200, "NONVOICE", "なかなか厳しいな。もう一度、カードを選び直してみよう……。")
    comPoseDelete()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
local card_167_s4s_420_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1201, "NONVOICE", "【直哉】「ここで、アヤノさんのノートを調べるんだけど……」")
    vms(1202, "NONVOICE", "【彩野】「この場面は、どの場面から繋がるのかな？」")
    vms(1203, "NONVOICE", "【直哉】「えっとね――うーん……」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1204, "NONVOICE", "【彩野】「どうしたの？」")
    vms(1205, "NONVOICE", "【直哉】「いや、実はね、ここに辿り着くまでに色々と物語が分岐していて――」")
    vms(1206, "NONVOICE", "【直哉】「ちょっと一言では説明しづらくなってきたかなって……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1207, "NONVOICE", "【彩野】「そうなんだ。どうすればいいかな……」")
    cStopBGMWrap()
    vms(1208, "NONVOICE", "【直哉】「あ、そうだ。ちょっと、お話をまとめてみた方がいいかも」")
    vms(1209, "NONVOICE", "【彩野】「お話をまとめる？」")
    vms(1210, "NONVOICE", "【直哉】「ここまでの物語の流れを、整理しようかなって」")
    comPoseLoad("po2_aya_f_1_e")
    vms(1211, "NONVOICE", "【彩野】「あ、そうだね。そうして貰えると、助かるかも」")
    vms(1212, "NONVOICE", "【直哉】「うん。それじゃあね……」")
    cPlayBGMWrap(cGetFileName("bgm", "bgm_7_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1213, "NONVOICE", "【直哉】「まず最初に、この物語――セクション４は廊下を歩くユウイチをアヤノさんが見掛けたところから始まるんだけど――」")
    vms(1214, "NONVOICE", "【直哉】「アヤノさんから呼び止められたユウイチは、ポケットにメモが入っていた事を伝えるんだ」")
    wait(1)
    layerLoad(layerName.pose3, cGetFileName("cutin", "cut_61"))
    layerPosition(layerName.pose3, 320, 30)
    switchScreen(0, "", 30)
    wait(30)
    vms(1215, "NONVOICE", "【直哉】「メモには『誰も見た事のない夕焼けの秘密は、屋上に行けばわかる』と書いてあった」")
    vms(1216, "NONVOICE", "【彩野】「ふむ……」")
    wait(1)
    layerLoad(layerName.pose3, "")
    switchScreen(0, "", 30)
    wait(30)
    vms(1217, "NONVOICE", "【直哉】「アヤノさんはそのメモを見て、どう思ったのかというと――」")
    comPoseDelete()
end
local card_167_s4s_420_sel_resolve = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1218, "NONVOICE", "【彩野】「確かに、ちょっと気になるね」")
    vms(1219, "NONVOICE", "【直哉】「でね。その後、アヤノさんとユウイチは別れて――物語は、ユウイチ視点に変わる」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1220, "NONVOICE", "【彩野】「ユウイチ……」")
    vms(1221, "NONVOICE", "【直哉】「そう、ユウイチが『物語の主人公』になるんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1222, "NONVOICE", "【彩野】「……」")
    vms(1223, "NONVOICE", "【直哉】「そして、ユウイチはメモの差出人がユカリ先生じゃないかと思って図書室に行く」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1224, "NONVOICE", "【彩野】「うん……」")
    vms(1225, "NONVOICE", "【直哉】「でも、メモの差出人はユカリ先生じゃなかった」")
    vms(1226, "NONVOICE", "【直哉】「とりあえずユウイチは、メモの指示通り、屋上に行ってみる事にした」")
    vms(1227, "NONVOICE", "【直哉】「そこでユウイチは、メモの差出人という『少女』に出会った」")
    vms(1228, "NONVOICE", "【彩野】「少女……」")
    vms(1229, "NONVOICE", "【直哉】「うん。髪の長い女の子。これまでの物語の展開から、彼女の名前は恐らく、この名前だと思う――」")
    comPoseDelete()
end
local card_167_s4s_420_sel_step3 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_2_e")
    vms(1230, "NONVOICE", "【彩野】「サクラさん……」")
    vms(1231, "NONVOICE", "【直哉】「少女――サクラさんは、ユウイチがメモを見たとき、その内容について『興味がある』のか質問した」")
    vms(1232, "NONVOICE", "【直哉】「その『質問』の場面が――」")
    comPoseDelete()
end
local card_167_s4s_420_sel_step4 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1233, "NONVOICE", "【彩野】「……」")
    vms(1234, "NONVOICE", "【直哉】「ユウイチは『興味がある』と答えた。例によって、と言ってもいいかもしれないね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1235, "NONVOICE", "【彩野】「え？……」")
    vms(1236, "NONVOICE", "【直哉】「例によって、というのは――これまでサクラさんがアヤノさんやユウイチに何か『話題』を持ちかけたとき――」")
    vms(1237, "NONVOICE", "【直哉】「その話題に『興味がない』ようなそぶり……『下らない』や『興味が無い』や茶化したりすると、物語はバッドエンドを迎えているんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1238, "NONVOICE", "【彩野】「ふむ……」")
    vms(1239, "NONVOICE", "【直哉】「だから、物語を進めるには『興味がある』事が必要条件と言えるかもしれない」")
    vms(1240, "NONVOICE", "【彩野】「あ……なるほど……」")
    comPoseLoad("po2_aya_f_2_d")
    vms(1241, "NONVOICE", "【彩野】「……って、ごめんね、話の途中で、質問しちゃって」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1242, "NONVOICE", "【彩野】「……えっと、それでどうしたんだっけ？」")
    vms(1243, "NONVOICE", "【直哉】「うん。興味がある、と答えたユウイチに対して――」")
    vms(1244, "NONVOICE", "【直哉】「次に、少女はメモの内容について、どんな感想を抱いたのか聞いてきた」")
    vms(1245, "NONVOICE", "【直哉】「ユウイチの『答え』は――」")
    comPoseDelete()
end
local card_167_s4s_420_sel_step5 = function()
    oCard.cardAnswerNonvoiceTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1246, "NONVOICE", "【彩野】「信じてみてもいい……サクラさんを、信じる事……」")
    vms(1247, "NONVOICE", "【直哉】「ユウイチが『信じてみてもいい』と答えると、ユウイチの後ろから物音が聞こえた」")
    vms(1248, "NONVOICE", "【直哉】「ユウイチは辺りを調べてみるけれど、なにもみつからなかった」")
    vms(1249, "NONVOICE", "【直哉】「そして、気がつくとサクラさんの姿も見つからなかった」")
    vms(1250, "NONVOICE", "【直哉】「サクラさんは『消えてしまった』んだ」")
    comPoseLoad("po2_aya_f_1_c")
    vms(1251, "NONVOICE", "【彩野】「……」")
    vms(1252, "NONVOICE", "【直哉】「訳のわからないまま、ユウイチは教室に戻るんだけど――」")
    vms(1253, "NONVOICE", "【直哉】「ユウイチの目に入ったのはひっくり返っていたアヤノさんの机だった」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1254, "NONVOICE", "【彩野】「机……」")
    vms(1255, "NONVOICE", "【直哉】「ユウイチは、アヤノさんの机を――」")
    comPoseDelete()
end
local card_167_s4s_420_sel_step7 = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1256, "NONVOICE", "【彩野】「私の机を、調べた……」")
    comPoseLoad("po2_aya_f_1_b")
    vms(1257, "NONVOICE", "【彩野】「……なるほど。うん、これまでの流れが、わかったと思う」")
    vms(1258, "NONVOICE", "【直哉】「よかった。あとね、この机を調べる所なんだけれど――」")
    vms(1259, "NONVOICE", "【直哉】「この場面のあらすじをつくったときに、彩野さんが『ノート』の事を気に掛けていたんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1260, "NONVOICE", "【彩野】「ノート……」")
    vms(1261, "NONVOICE", "【直哉】「うん。……理由ははっきりしないけれど、何か、気になるって」")
    vms(1262, "NONVOICE", "【彩野】「ふむ……。そうなると……ここに、新しい展開を追加した方がいいのかも」")
    vms(1263, "NONVOICE", "【直哉】「展開――カードを作った方がいい？」")
    vms(1264, "NONVOICE", "【彩野】「うん。『ノートを調べる』、が、いいかな」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：アヤノのノート』の選択肢（ノートを調べる）を作成しました。")
    comPoseLoad("po2_aya_f_1_e")
    vms(1265, "NONVOICE", "【彩野】「これで、お話が整理できたよ。ありがとう、直哉くん」")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[149].hold == -1 then
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
    if gameSave.myCard[153].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[154].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[161].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[166].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    local l1_0 = false
    card_167_s4s_420_sel_intro()
    local l1_1 = 0
    local l1_2 = 0
    local l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 149 then
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
            vms(1266, "NONVOICE", "ユウイチからメモを見せられて、アヤノさんはどう思ったのかというと――")
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
    card_167_s4s_420_sel_resolve()
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
            vms(1267, "NONVOICE", "【直哉】「髪の長い女の子。これまでの物語の展開から、少女の名前は恐らく、この名前だと思う――」")
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
    card_167_s4s_420_sel_step3()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 154 then
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
            vms(1268, "NONVOICE", "少女――サクラさんは、ユウイチがメモを見たとき、その内容について『興味がある』のか質問した。")
            vms(1269, "NONVOICE", "その『質問』、選択の場面が――")
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
    card_167_s4s_420_sel_step4()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 161 then
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
            vms(1270, "NONVOICE", "少女はメモの内容について、どんな感想を抱いたのか聞いてきた。")
            vms(1271, "NONVOICE", "ユウイチの『答え』は、「下らない」、「信じてみてもいい」、どちらだっただろう――")
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
    card_167_s4s_420_sel_step5()
    l1_1 = 0
    l1_2 = 0
    l1_3 = -1
    while l1_1 < 1 do
        local l1_4 = oCard.selectCardObj()
        if l1_4 == 166 then
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
            vms(1272, "NONVOICE", "ユウイチは、アヤノさんの机をどうしたんだっけ……。")
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
        card_167_s4s_420_sel_step6()
    end
    card_167_s4s_420_sel_step7()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local card_21_s1s_210_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(1990, "NONVOICE", "【彩野】「コックリさん……彼女……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1991, "NONVOICE", "彩野さんは、なにかを深く考えているようだ。")
    vms(1992, "NONVOICE", "【彩野】「ここの描写って、なんかちょっと、リアルな感じがする。やっぱりわたしって、やったことあるのかな」")
    vms(1993, "NONVOICE", "【彩野】「……」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1994, "NONVOICE", "【彩野】「ね、直哉くん。ここの彼女と『したこと』についての、カードってある？」")
    comPoseDelete()
end
local card_21_s1s_210_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(1995, "NONVOICE", "【彩野】「コックリさん……だよね……うん……」")
    vms(1996, "NONVOICE", "【直哉】「放課後、『彼女』としていた約束」")
    vms(1997, "NONVOICE", "【直哉】「彩野さん、この彼女って、なんなんだろう。彩野さんの知り合い？」")
    comPoseLoad("po2_aya_f_2_e")
    vms(1998, "NONVOICE", "【彩野】「それも……わからないの。コックリさんを『現実』にしたことも」")
    comPoseLoad("po2_aya_f_1_a")
    vms(1999, "NONVOICE", "【彩野】「うーん……どうなんだろう。直哉くんは、どう？」")
    vms(2000, "NONVOICE", "【直哉】「え、僕？」")
    vms(2001, "NONVOICE", "【直哉】「……」")
    vms(2002, "NONVOICE", "【直哉】「やっぱり同級生にこういう子はいなかったと思うよ」")
    vms(2003, "NONVOICE", "【直哉】「何というかね。居たらちょっと目立つタイプの子かも、と思うし」")
    vms(2004, "NONVOICE", "【彩野】「……そっか」")
    vms(2005, "NONVOICE", "【直哉】「でも、何かあるんだよね」")
    vms(2006, "NONVOICE", "【彩野】「現実に……会ったのかな……やっぱり……」")
    vms(2007, "NONVOICE", "【直哉】「どうだろう。特徴的な、『物語』的なキャラクターとも言えるけど」")
    comPoseLoad("po2_aya_f_2_e")
    vms(2008, "NONVOICE", "【彩野】「そうだよね。そうとも言える……」")
    vms(2009, "NONVOICE", "彩野さんは眉間に皺を寄せた。")
    vms(2010, "NONVOICE", "【直哉】「ま、まあ……あんまり考え込んでも、仕方ないし。もうちょっと、物語を進めてみればいいんじゃないかな？」")
    vms(2011, "NONVOICE", "【直哉】「ここの場面のあらすじが、何かのヒントになるかもしれないよ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(2012, "NONVOICE", "【彩野】「ありがとう。そうしてみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『放課後のコックリさん』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[122].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_21_s1s_210_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 122 then
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
            vms(2013, "NONVOICE", "【彩野】「あの子とした事……いけないこと……」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_21_s1s_210_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

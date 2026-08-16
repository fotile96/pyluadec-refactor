local l0_0 = function(l1_0, l1_1)
    local l1_2 = function()
    end
    comSectionNonLabelBegin(l1_0, l1_1)
    cPlayOneshotMusic(cGetFileName("mus", "mus_26"))
    wait(1)
    layerLoad(layerName.bg1, cGetFileName("bg", "bg_26_a_0"))
    switchScreen(0, "", 60)
    wait(60)
    cPlayLoopSeWrap(cGetFileName("loop", "loop_6"))
    vms(3890, "NONVOICE", "狭い室内には女性が足を組んで椅子に座っている。_n『先生』だ。")
    vms(3891, "NONVOICE", "先生の机の上には本やファイルが並べられている。")
    vms(3892, "NONVOICE", "整然という言葉とはおよそかけ離れているが、だいたい左、だいたい右、だいたい中央でそれなりにカテゴライズはされているようだった。")
    vms(3893, "NONVOICE", "研究室内を眺めてみると、百科事典や国語辞典に混じって、童話や絵本も並べられていた。")
    vms(3894, "NONVOICE", "高校生に対して行う授業の資料にして絵本というのはいささか対象年齢が低すぎるように思われた。")
    vms(3895, "NONVOICE", "が、児童を対象とした本の中にこそ教育の原石があるのかもしれない。")
    vms(3896, "NONVOICE", "少なくともこれらの本が、教師にとってある種のポリシーを持って揃えられているのは確かだ。")
    vms(3897, "NONVOICE", "視点を『先生』に戻そう。")
    vms(3898, "NONVOICE", "手には安い油性のボールペンが握られている。")
    vms(3899, "NONVOICE", "『先生』はクルクルと器用にそれを回している。学生の頃からの癖が抜けていないのだ。")
    vms(3900, "NONVOICE", "彼女は机の上に広がっているプリンタ用紙を眺めては小さくため息を漏らし、時折それに赤ペンで何かを書き込んでいく。")
    cLoadPlaySE(cGetFileName("se", "se_48"), false)
    vms(3901, "NONVOICE", "扉が開く音が聞こえた。")
    vms(3902, "NONVOICE", "ペンを机の上に置く。")
    cLoadPlaySE(cGetFileName("se", "se_68"), false)
    vms(3903, "NONVOICE", "椅子を回転させ、身体を『彼女』の方に向けた。")
    vms(3904, "NONVOICE", "先生は、「どうぞ。……早かったね、道、空いてた？」と、彼女に聞く。")
    vms(3905, "NONVOICE", "彼女は、はい、と返事をすると、先生の元に行き、教師の肩の向こうを覗き込んだ。")
    vms(3906, "NONVOICE", "教師は女子生徒の方に紙を見せながら、「今、最後の確認、赤入れしてるところ。明日か明後日には渡せると思う」と、答えた。")
    vms(3907, "NONVOICE", "女生徒は『ここまで書いていいんですか？』と訊いた。")
    vms(3908, "NONVOICE", "もちろん、と先生は答え、「ここまで書かないと意味がないの」と、言葉を続けた。")
    vms(3909, "NONVOICE", "先生は「……そっちの方は順調？」と訊く。")
    vms(3910, "NONVOICE", "女生徒は『まあまあ、と言ったところです』、と答えた。")
    cStopLoopSeWrap()
    wait(1)
    comEffectFadeOut(120)
    vms(3911, "YUK01930", "【由加里】「楽しみにしてるわね。千秋さんの物語」")
    vms(3912, "NONVOICE", "教師は微笑んで言う。")
    vms(3913, "NONVOICE", "『≪セクション５、冬の始まり――彼を待つところから始めたいと思います≫』")
    vms(3914, "NONVOICE", "女生徒は窓から校庭を眺めながら答えた。")
    l1_2()
end
local l0_1 = function(l1_0, l1_1)
    local l1_2 = function()
    end
    cPlayOneshotMusic(cGetFileName("mus", "mus_8"))
    layerLoad(layerName.pose1, cGetFileName("cutin", "cut_e_ex1"))
    layerLoad(layerName.scene, "")
    layerLoad(layerName.hour1, "")
    layerAlpha(layerName.pose1, 0)
    layerPosition(layerName.pose1, 240, 10, 60)
    layerRotate(layerName.pose1, 10, 10, 10)
    layerMoveAlpha(layerName.pose1, 100, 120)
    layerMoveRotate(layerName.pose1, 0, 0, 0, 30)
    wait(120)
    wait(120)
    oCard.show(cGetFileName("card", "crd_143_a"), "『セクションＥＸ１』のあらすじを作成しました。")
    vms(17000, "NONVOICE", "フラグメントモード：セクションＥＸ１が終了しました。")
    cLoadPlaySE(cGetFileName("se", "se_28"), false)
    layerMoveScale(layerName.pose1, 100, 0, 60)
    layerMoveAlpha(layerName.pose1, 4278190335, 60)
    layerMoveRotate(layerName.pose1, 0, 0, 100, 60)
    wait(60)
    comEffectFadeOut(60)
    l1_2()
end
main = function()
    local l1_0 = 0
    while l1_0 == 0 do
        if doScriptScene == "end" then
            l1_0 = 1
        elseif doScriptScene == "e1f-10" then
            l0_0(doScriptScene, "由加里先生")
            doScriptScene = "e1f-complete"
        elseif doScriptScene == "e1f-complete" then
            if memoryFlag == true then
                run(cGetFileName("script", "snr_memory"))
                quit()
            end
            l0_1(doScriptScene, "セクションＥＸ１読了")
            gameSave.myCard[118].hold = 1
            gameSave.myCard[143].hold = 1
            doScriptScene = "end"
        end
        wait(5)
    end
    cInitGame()
    run(cGetFileName("script", "snr_mainmenu"))
    quit()
end

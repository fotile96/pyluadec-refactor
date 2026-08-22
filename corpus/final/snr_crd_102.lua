local l0_0 = function()
    vms(331, "NONVOICE", "＜推理クイズ＞")
    vms(332, "NONVOICE", "さてアヤノさん、問題です。")
    vms(333, "NONVOICE", "この前はアヤノさん、ギブアップしちゃったから（泣）今度はちゃんと答えを送ってくださいね！")
    vms(334, "NONVOICE", "では（コホン）、出題します。")
    vms(335, "NONVOICE", "３つの椅子、Ａ、Ｂ、Ｃがあるとします。")
    vms(336, "NONVOICE", "そして、それぞれの椅子に、アヤノさん、サクラ、ユウイチさんが座っているとします。")
    vms(337, "NONVOICE", "三人には、それぞれ次の特徴があります。")
    vms(338, "NONVOICE", "○アヤノ：嘘をつかない_n_r○サクラ：嘘をつく_n_r○ユウイチ：真実も嘘もつく。")
    vms(339, "NONVOICE", "Ｂの椅子に座っている人物が言いました。")
    vms(340, "NONVOICE", "【Ｂの椅子】「Ｃはアヤノです」")
    vms(341, "NONVOICE", "Ｃの椅子に座っている人物が言いました。")
    vms(342, "NONVOICE", "【Ｃの椅子】「Ａはアヤノです」")
    vms(343, "NONVOICE", "さて、それではＡ、Ｂ、Ｃの椅子に座っている人物はそれぞれ誰になるでしょうか？")
end
local l0_1 = function()
    comPoseLoad("po2_aya_f_1_c")
    vms(344, "NONVOICE", "【彩野】「うーん、何か違うような……」")
    vms(345, "NONVOICE", "……。")
    vms(346, "NONVOICE", "一度整理してみよう。")
    vms(347, "NONVOICE", "Ｂの椅子に座っている人物がアヤノさんの場合、アヤノさんは本当のことを言っている事になるのだろうか？")
    vms(348, "NONVOICE", "Ｃの椅子に座っている人物がアヤノさんの場合、アヤノさんは本当のことを言っている事になるのだろうか？")
end
local l0_2 = function()
    comPoseLoad("po2_aya_f_2_e")
    vms(349, "NONVOICE", "【彩野】「うーん、これも違うような……」")
    vms(350, "NONVOICE", "……。")
    vms(351, "NONVOICE", "落ち着いて考えてみよう。")
    vms(352, "NONVOICE", "Ｂの椅子に座っている人物がアヤノさんの場合、アヤノさんは本当のことを言っている事になるのだろうか？")
    vms(353, "NONVOICE", "Ｃの椅子に座っている人物がアヤノさんの場合、アヤノさんは本当のことを言っている事になるのだろうか？")
    vms(354, "NONVOICE", "Ｃの椅子に座っている人物がサクラさんの場合、サクラさんは本当のことを言っている事になるのだろうか？")
end
local card_102_s6s_110_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_c")
    vms(355, "NONVOICE", "【直哉】「サクラさんからの手紙だけど……これは……推理クイズ……？」")
    vms(356, "NONVOICE", "【彩野】「直哉くん……」")
    vms(357, "NONVOICE", "【直哉】「あ、うん」")
    vms(358, "NONVOICE", "【彩野】「……この箇所の問題なんだけど……私も答えがわからなくて……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(359, "NONVOICE", "【彩野】「……ちょっと、気になっちゃって……お話もうまく先が浮かばないの」")
    vms(360, "NONVOICE", "【彩野】「それでね、直哉くん。相談なんだけど――」")
    comPoseLoad("po2_aya_f_1_a")
    vms(361, "NONVOICE", "【彩野】「直哉くんと協力して考えてみれば、解けるかもって思ったんだ」")
    vms(362, "NONVOICE", "そうか……ただでさえメモがいるような、面倒くさい問題なのに……。")
    vms(363, "NONVOICE", "彩野さんの記憶の状態だと、よりいっそう、この問題を解くのが大変にちがいなかった。")
    vms(364, "NONVOICE", "【直哉】「ふむ……推理クイズか。僕が力になれるのかはわからないけど、やってみようか」")
    comPoseLoad("po2_aya_f_1_e")
    vms(365, "NONVOICE", "【彩野】「ありがとう！」")
    comPoseLoad("po2_aya_f_1_b")
    vms(366, "NONVOICE", "【彩野】「えっと、それじゃあ問題をもう一度聞かせてもらっていい？」")
    vms(367, "NONVOICE", "【直哉】「確か――」")
    l0_0()
    local l1_0 = 0
    local l1_1 = 0
    while l1_0 == 0 do
        local l1_2 = 0
        l1_2 = comDlgSelectItem(false, true, false, true, 1, "none", 0, 0, "sel_s6s_110_sel_a", 115, 80, 1, "sel_s6s_110_sel_b", 115, 100, 2, "sel_s6s_110_sel_c", 115, 120, 3, "sel_s6s_110_sel_d", 115, 140, 4, "sel_s6s_110_sel_e", 115, 160, 5, "sel_s6s_110_sel_f", 115, 180, 6)
        if l1_2 == 5 then
            l1_0 = 1
            break
        end
        if l1_1 == 1 then
            l0_0()
            l0_2()
        end
        if l1_1 == 0 then
            l0_0()
            l0_1()
            l1_1 = 1
        end
        wait(5)
    end
end
local card_102_s6s_110_resolve = function()
    comPoseLoad("po2_aya_f_1_a")
    keyPlaySE(seName.getCard)
    comEffectYellowIn(60)
    wait(60)
    comPoseLoad("po2_aya_f_1_b")
    vms(368, "NONVOICE", "【彩野】「そっか！ ５番が正解なんだね」")
    vms(369, "NONVOICE", "【彩野】「これで続きも展開できそう」")
    comPoseLoad("po2_aya_f_1_e")
    vms(370, "NONVOICE", "【彩野】「ありがとう、直哉くんのおかげだよ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『図書室で読む』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    card_102_s6s_110_intro()
    card_102_s6s_110_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

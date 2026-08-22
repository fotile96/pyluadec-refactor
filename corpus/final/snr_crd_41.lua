local card_41_s2s_190_sel_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2688, "NONVOICE", "【直哉】「彩野さん、ここのナゾトキだけど、間違えた部分と正解の部分、両方のあらすじがあるみたいだね」")
    vms(2689, "NONVOICE", "【彩野】「あ、そうなんだ……」")
    vms(2690, "NONVOICE", "【彩野】「じゃあ、えっと、直哉くん。最初に正解の場面のあらすじを見せてもらっていい？」")
    comPoseDelete()
end
local card_41_s2s_190_sel_resolve = function()
    oCard.cardAnswerTrue()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(2691, "NONVOICE", "【彩野】「なるほど……ありがとう」")
    vms(2692, "NONVOICE", "【彩野】「それじゃあ……ナゾトキに間違えたときの場面、教えてくれるかな……」")
    comPoseDelete()
end
local card_41_s2s_190_sel_step3 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(2693, "NONVOICE", "【彩野】「ふむふむ……」")
    vms(2694, "NONVOICE", "【彩野】「ここの場面、正解と間違いの両方があるってことは、やっぱり後ろの展開に影響があるみたいだね」")
    vms(2695, "NONVOICE", "【直哉】「そうだね……。意味がなかったら、わざわざ二つに分ける必要はないかもしれない」")
    vms(2696, "NONVOICE", "【直哉】「後で見返したときのために、ナゾトキの正解もカードに書いておくね」")
    vms(2697, "NONVOICE", "【彩野】「あ、そうしてもらえると便利かも。ありがとう、直哉くん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『選択：ナゾトキ』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[62].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if gameSave.myCard[42].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_41_s2s_190_sel_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 62 then
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
            vms(2698, "NONVOICE", "【彩野】「ナゾトキに正解したときのあらすじを見せてもらっていい？」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_41_s2s_190_sel_resolve()
    local l1_3 = 0
    local l1_4 = 0
    local l1_5 = -1
    while l1_3 < 1 do
        local l1_6 = oCard.selectCardObj()
        if l1_6 == 42 then
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
            vms(2699, "NONVOICE", "【彩野】「ナゾトキを間違えちゃったときのあらすじを見せてもらっていい？」")
            comPoseDelete()
        end
        if l1_4 == 0 then
            oCard.mesNG()
            l1_4 = l1_4 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_41_s2s_190_sel_step3()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3132, "NONVOICE", "【直哉】「この場面のあと、『また、いつもの生活』に戻っちゃうみたいだね」")
    vms(3133, "NONVOICE", "【彩野】「いつもの生活。えっと、直哉くん、そのカード見せて貰っていい？」")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3134, "NONVOICE", "【彩野】「なるほど……」")
    vms(3135, "NONVOICE", "【直哉】「アヤノさんのここの答えは、ちょっと茶化したような感じだったね」")
    comPoseLoad("po2_aya_f_2_d")
    vms(3136, "NONVOICE", "【彩野】「それで、この終わりなんだよね……」")
    vms(3137, "NONVOICE", "【彩野】「うーん、となるとサクラさんの質問を真面目に受け取らないと、『何事も起こらず終了』って感じかな」")
    vms(3138, "NONVOICE", "【直哉】「うん……」")
    vms(3139, "NONVOICE", "真剣に向き合う……か。この結果を踏まえて、新しい選択肢を彩野さんに提案してもいいかもしれない。")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『サクラのため息』のあらすじを作成しました。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[31].hold == -1 then
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
        if l1_3 == 31 then
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
            vms(3140, "NONVOICE", "『また、いつもの生活』のカードを彩野さんに見せてみよう。")
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

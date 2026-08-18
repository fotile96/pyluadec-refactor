local card_8_s1s_60_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3506, "NONVOICE", "【彩野】「きくちゃんと『噂』について話してた」")
    vms(3507, "NONVOICE", "【直哉】「うん。それでユウイチの話になって……アヤノさんは約束を思い出したんだ」")
    vms(3508, "NONVOICE", "【彩野】「ユウイチ……。ちょっと変な感じがする。なにか」")
    vms(3509, "NONVOICE", "【直哉】「変な感じ……」")
    vms(3510, "NONVOICE", "【彩野】「うん。やっぱり現実とは。あんな風に、ユウイチとの仲について、冷やかしみたいに言われた事、無かったから」")
    vms(3511, "NONVOICE", "ユウイチとの仲で言われた事、か。確か、このカードが関連するかもしれない。")
    comPoseDelete()
end
local card_8_s1s_60_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3512, "NONVOICE", "【直哉】「でも、彩野さんは現実でもユウイチとは幼なじみだから、それぐらいは……」")
    vms(3513, "NONVOICE", "【彩野】「確かに、仲は悪くなかったよ。でも、こんな風に言われた事無かったし」")
    vms(3514, "NONVOICE", "彩野さんは語尾を強めていった。")
    vms(3515, "NONVOICE", "【直哉】「とはいえ、この物語は彩野さんの物語なんだよね、だったら――」")
    vms(3516, "NONVOICE", "【彩野】「そうだけど、でも……」")
    vms(3517, "NONVOICE", "【直哉】「それに彩野さんは聞いてなくても、やっぱり現実でも他のみんなはそんな風に言って――」")
    vms(3518, "NONVOICE", "【彩野】「……」")
    vms(3519, "NONVOICE", "【直哉】「あ……」")
    vms(3520, "NONVOICE", "【彩野】「…………直哉くん」")
    vms(3521, "NONVOICE", "【直哉】「……ごめん」")
    vms(3522, "NONVOICE", "【彩野】「……いえ、ごめんなさい。私の方こそ」")
    vms(3523, "NONVOICE", "……どうかしていた。今、彩野さんにそんな事を言っても、何もならないのに。")
    vms(3524, "NONVOICE", "本当に、どうかしている。")
    vms(3525, "NONVOICE", "【直哉】「ごめん、なんか余計な事――」")
    vms(3526, "NONVOICE", "【彩野】「もう、謝らないで、直哉くん」")
    vms(3527, "NONVOICE", "僕は頷いた。確かに、今はこのことを気にしてもどうにもならないのだ。")
    vms(3528, "NONVOICE", "【直哉】「……じゃあ、えっと……」")
    vms(3529, "NONVOICE", "【彩野】「あらすじで言うなら、この場面はこんな感じ」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『約束を思い出す』のあらすじを作成しました。")
    vms(3530, "NONVOICE", "【直哉】「噂について話して、アヤノさんは『約束』を思い出したんだ」")
    vms(3531, "NONVOICE", "【彩野】「うん。これがこの場面の『あらすじ』」")
    vms(3532, "NONVOICE", "【直哉】「次の『あらすじ』作ってもいい？」")
    vms(3533, "NONVOICE", "【彩野】「もちろんどうぞ、だよ。直哉くん」")
    vms(3534, "NONVOICE", "彩野さんはにっこりと微笑んだ。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[127].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_8_s1s_60_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 127 then
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
            vms(3535, "NONVOICE", "【彩野】「えっと。喧嘩している、的な……。でも、どうして……」")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_8_s1s_60_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

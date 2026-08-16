local l0_0 = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(3288, "NONVOICE", "【彩野】「『放課後の約束をしていない』。とりあえずアヤノはそう思ったんだけど――」")
    vms(3289, "NONVOICE", "【彩野】「今度は『何かもっと他の大切な約束』をしてたかもって感じたんだよね」")
    vms(3290, "NONVOICE", "【直哉】「うん、そういう展開だった」")
    vms(3291, "NONVOICE", "【彩野】「あ！」")
    vms(3292, "NONVOICE", "【直哉】「どうかした？」")
    vms(3293, "NONVOICE", "【彩野】「えっとね、考え事をしてたとき、私、何か手に触っていなかった？」")
    vms(3294, "NONVOICE", "【彩野】「文房具だと思うんだけど……えっと……なんだろう？」")
    vms(3295, "NONVOICE", "考え事をしていたとき、彩野さんが掌の中で転がしていた文房具といえば――")
    comPoseDelete()
end
local l0_1 = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(3296, "NONVOICE", "【彩野】「そうそう、消しゴムだね」")
    vms(3297, "NONVOICE", "【彩野】「消しゴムを触りながら、アヤノは、放課後の約束をしていないと考えたんだけど――」")
    vms(3298, "NONVOICE", "【彩野】「今度は『放課後の約束』よりもっと大切な『他の約束』をしていたような気がしてきた、ということだね」")
    vms(3299, "NONVOICE", "【直哉】「そう。アヤノさんの言葉としてはそういう事になるね。カードを作ってみるね」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『約束をしていない』のあらすじを作成しました。")
    vms(3300, "NONVOICE", "【直哉】「この部分の言葉を入れ替えてやれば、次の展開が少し見える気がするよ」")
    vms(3301, "NONVOICE", "【彩野】「ん。どういうこと？」")
    vms(3302, "NONVOICE", "【直哉】「『何かもっと他の大切な約束』を見るためには、どうすればいいと思う？」")
    vms(3303, "NONVOICE", "【彩野】「そっか。『放課後の約束をしない』展開。そうすれば、ほかの約束の事がわかるんだね。なるほど」")
    vms(3304, "NONVOICE", "【直哉】「うん」")
    vms(3305, "NONVOICE", "……。")
    vms(3306, "NONVOICE", "加えて、僕にはもう一つ気になる事があった。")
    vms(3307, "NONVOICE", "それは『消しゴム』だった。これまでの彩野さんの物語を聞く限り、この文房具がなにかキーのような扱われかたをしていることが多い。")
    vms(3308, "NONVOICE", "もしかしたら今後、消しゴムは『物語』に関わってくるのかもしれない。")
    vms(3309, "NONVOICE", "今はまだわからない。けれど彩野さんが何か考え込んだ時のために、気に留めておく必要はあるだろう。")
    comPoseLoad("po2_aya_f_2_e")
    vms(3310, "NONVOICE", "【彩野】「あっ！ それとね、直哉くん……」")
    vms(3311, "NONVOICE", "【直哉】「ん……どうかした？」")
    cPlayOneshotMusic(cGetFileName("mus", "mus_12"))
    comEffectYellowIn(60)
    wait(60)
    vms(3312, "NONVOICE", "【彩野】「ここの部分の展開、≪もうちょっと後になってから、もう一度見せてもらっていい？≫」")
    vms(3313, "NONVOICE", "【直哉】「え？ どうして？」")
    comPoseLoad("po2_aya_f_1_a")
    vms(3314, "NONVOICE", "【彩野】「うん……なにか、少し引っかかるの。この≪物語の進み方であっているのかな≫って」")
    comPoseLoad("po2_aya_f_2_e")
    vms(3315, "NONVOICE", "【彩野】「でも、それが……浮かばなくて……」")
    vms(3316, "NONVOICE", "今の手持ちのカードだと浮かばない、という事なのだろうか。")
    cPlayOneshotMusic(cGetFileName("mus", "mus_12"))
    vms(3317, "NONVOICE", "≪物語が進んだら、もう一度この場面を≫振り返ってみても良いかもしれない。")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[130].hold == -1 then
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
        if l1_3 == 130 then
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
            vms(3318, "NONVOICE", "【彩野】「……文房具。よく転がる物だったかな……」")
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

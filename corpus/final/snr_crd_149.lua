local card_149_s4s_51_intro = function()
    cPlayBGMWrap(cGetFileName("bgm", "bgm_5_x"))
    comPoseLoad("po2_aya_f_1_a")
    vms(773, "NONVOICE", "【直哉】「ユウイチの渡したメモについての場面、だね」")
    comPoseLoad("po2_aya_f_2_d")
    vms(774, "NONVOICE", "【彩野】「アヤノは『気になるね』って言うんだけど、結局『用事がある』って別行動になっちゃうんだね」")
    vms(775, "NONVOICE", "【直哉】「うん。たぶん、この部分は他の物語――『セクション３』と、繋がっていると思う」")
    comPoseLoad("po2_aya_f_2_e")
    vms(776, "NONVOICE", "【彩野】「セクション３……」")
    vms(777, "NONVOICE", "【彩野】「ね、直哉くん。その、アヤノが別行動した部分の物語――」")
    vms(778, "NONVOICE", "【彩野】「『セクション３の物語』のあらすじって、わかる？」")
    vms(779, "NONVOICE", "【直哉】「うん、カードを作ってるよ」")
    comPoseDelete()
end
local card_149_s4s_51_resolve = function()
    oCard.cardAnswerTrue()
    comPoseLoad("po2_aya_f_1_a")
    vms(780, "NONVOICE", "【彩野】「あ……」")
    comPoseLoad("po2_aya_f_2_e")
    vms(781, "NONVOICE", "【彩野】「……」")
    vms(782, "NONVOICE", "【直哉】「セクション３は、アヤノさんとユウイチが結ばれる物語、だね」")
    comPoseLoad("po2_aya_f_1_c")
    vms(783, "NONVOICE", "【彩野】「直哉くん……」")
    vms(784, "NONVOICE", "【直哉】「これも一つの物語、なんだと思う。僕はそう思ってる」")
    vms(785, "NONVOICE", "【彩野】「……」")
    vms(786, "NONVOICE", "【直哉】「今は、『この物語』。セクション４の物語を、読み進めたいんだ」")
    comPoseLoad("po2_aya_f_1_a")
    vms(787, "NONVOICE", "【彩野】「……うん……」")
    comPoseLoad("po2_aya_f_1_b")
    vms(788, "NONVOICE", "【彩野】「……ありがとう、直哉くん」")
    cLoadPlaySE(cGetFileName("se", "se_30"), false)
    oCard.show(cGetFileName("card", "crd_" .. gameSave.fragmentDoCardId .. "_a"), "『気になるね』のあらすじを作成しました。")
    comPoseDelete()
    vms(789, "NONVOICE", "でも、このシーンで、アヤノさんとユウイチは別れてしまうとなると――")
    vms(790, "NONVOICE", "残された人物はユウイチになる。")
    vms(791, "NONVOICE", "ユウイチの、『物語』――？")
    comPoseDelete()
    if not (gameSave.myCard[gameSave.fragmentDoCardId].hold == 1) then
        gameSave.myCard[gameSave.fragmentDoCardId].hold = 1
        comAyanoTimeRefresh()
    end
end
main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    if gameSave.myCard[135].hold == -1 then
        oCard.mesNot()
        comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    card_149_s4s_51_intro()
    local l1_0 = 0
    local l1_1 = 0
    local l1_2 = -1
    while l1_0 < 1 do
        local l1_3 = oCard.selectCardObj()
        if l1_3 == 135 then
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
            vms(792, "NONVOICE", "セクション３のあらすじを彩野さんに教えよう。")
            comPoseDelete()
        end
        if l1_1 == 0 then
            oCard.mesNG()
            l1_1 = l1_1 + 1
            comPoseDelete()
        end
        wait(30)
    end
    card_149_s4s_51_resolve()
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

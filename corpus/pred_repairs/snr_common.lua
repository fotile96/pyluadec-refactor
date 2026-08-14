local v0, v1, v2, i0, v3, v4, v5, i4, v6, v7, v8, i8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19
debagFlag = false
ceroFlag = false
voiceFlag = true
cardIDFlag = false
selectItemNo = 1
memoryFlag = false
gameSave = {}
gameSave.startMenuState = 0
gameSave.ayanoTime = 0
gameSave.sceneid = ""
gameSave.sceneName = ""
gameSave.sectionName = ""
gameSave.storyRoute = {}
gameSave.fragmentDoSceneId = ""
gameSave.fragmentDoCardId = ""
gameSave.myCard = {}
gameSave.tutorial = {}
gameSave.tutorial.firstStory = 0
gameSave.tutorial.count1StoryRoute = 0
gameSave.tutorial.count2StoryRoute = 0
gameSave.tutorial.firstFragmentBegin = 0
gameSave.tutorial.firstFragment = 0
gameSave.tutorial.firstCard = 0
systemSave = {}
systemSave.messageSpeed = 3
systemSave.messageSkip = 0
systemSave.messageReadColor = 0
systemSave.voiceCut = 0
systemSave.messageSpeedAutoFigure = 3
systemSave.messageSpeedAutoLine = 3
systemSave.autoVoice = 0
systemSave.volumeMaster = 5
systemSave.volumeBGM = 5
systemSave.volumeSE = 5
systemSave.volumeVoice = 5
systemSave.voiceNaoya = 1
systemSave.voiceAyano = 1
systemSave.voiceYuichi = 1
systemSave.voiceYukari = 1
systemSave.voiceChiaki = 1
systemSave.voiceSakura = 1
systemSave.voiceOther = 1
systemSave.libFlag = false
systemSave.novelFlag = false
systemSave.musicFlag = false
systemSave.novelGetFlag = {}
systemSave.novelGetFlag.novel01 = false
systemSave.novelGetFlag.novel02 = false
systemSave.novelGetFlag.novel03 = false
systemSave.novelGetFlag.novel04 = false
systemSave.novelGetFlag.novel05 = false
systemSave.bookMark = {}
systemSave.bookMark.novel01 = 0
systemSave.bookMark.novel02 = 0
systemSave.bookMark.novel03 = 0
systemSave.bookMark.novel04 = 0
systemSave.bookMark.novel05 = 0
systemSave.memoryFlag = {}
systemSave.cgFlag = {}
systemSave.storyLineSkip = 0
sceneId2aCard = {}
sceneId2aCard.sof_10 = 1
sceneId2aCard.s1s_20 = 2
sceneId2aCard.s1s_30 = 3
sceneId2aCard.s1s_35_sel = 4
sceneId2aCard.s1s_36 = 5
sceneId2aCard.s1s_37 = 6
sceneId2aCard.s1s_38 = 7
sceneId2aCard.s1s_60 = 8
sceneId2aCard.s1s_70 = 9
sceneId2aCard.s1s_80 = 10
sceneId2aCard.s1s_90 = 11
sceneId2aCard.s1s_100_sel = 12
sceneId2aCard.s1s_110 = 13
sceneId2aCard.s1s_120 = 14
sceneId2aCard.s1s_130 = 15
sceneId2aCard.s1s_140 = 16
sceneId2aCard.s1s_160 = 17
sceneId2aCard.s1s_170_sel = 18
sceneId2aCard.s1s_180 = 19
sceneId2aCard.s1s_200_sel = 20
sceneId2aCard.s1s_210 = 21
sceneId2aCard.s1s_215 = 22
sceneId2aCard.s1s_220 = 23
sceneId2aCard.s1s_230 = 24
sceneId2aCard.s1s_260_sel = 25
sceneId2aCard.e2s_10 = 26
sceneId2aCard.s1s_280 = 27
sceneId2aCard.s1s_300 = 28
sceneId2aCard.s1s_320 = 29
sceneId2aCard.s1s_330 = 30
sceneId2aCard.s2s_40 = 31
sceneId2aCard.s2s_60 = 32
sceneId2aCard.s2s_80_sel = 33
sceneId2aCard.s2s_90 = 34
sceneId2aCard.s2s_120_sel = 35
sceneId2aCard.s2s_140 = 36
sceneId2aCard.s2s_150 = 37
sceneId2aCard.s2s_160_sel = 38
sceneId2aCard.s2s_170 = 39
sceneId2aCard.s2s_180 = 40
sceneId2aCard.s2s_190_sel = 41
sceneId2aCard.s2s_209 = 42
sceneId2aCard.s2s_210 = 43
sceneId2aCard.s2s_220_sel = 44
sceneId2aCard.s2s_230 = 45
sceneId2aCard.s2s_240 = 46
sceneId2aCard.s2s_250 = 47
sceneId2aCard.s2s_260_sel = 48
sceneId2aCard.s2s_293 = 49
sceneId2aCard.s2s_300 = 50
sceneId2aCard.s2s_340_sel = 51
sceneId2aCard.s2s_350 = 52
sceneId2aCard.s2s_360 = 53
sceneId2aCard.s2s_370 = 54
sceneId2aCard.s2s_380 = 55
sceneId2aCard.s2s_420 = 56
sceneId2aCard.s2s_450 = 57
sceneId2aCard.s2s_500 = 58
sceneId2aCard.s2s_570 = 59
sceneId2aCard.s2s_590 = 60
sceneId2aCard.s2s_610 = 61
sceneId2aCard.s2s_208 = 62
sceneId2aCard.s2s_124 = 63
sceneId2aCard.s3s_10 = 64
sceneId2aCard.s3s_20_sel = 65
sceneId2aCard.s3s_50_sel = 66
sceneId2aCard.s3s_90_sel = 67
sceneId2aCard.s3s_100 = 68
sceneId2aCard.s3s_120 = 69
sceneId2aCard.s3s_170_sel = 70
sceneId2aCard.s3s_171 = 71
sceneId2aCard.s3s_172 = 72
sceneId2aCard.s3s_190 = 73
sceneId2aCard.s3s_230_sel = 74
sceneId2aCard.s3s_300_sel = 75
sceneId2aCard.s3s_301 = 76
sceneId2aCard.s3s_340 = 77
sceneId2aCard.s3s_350_sel = 78
sceneId2aCard.s3s_360 = 79
sceneId2aCard.s3s_370 = 80
sceneId2aCard.s3s_375 = 81
sceneId2aCard.s3s_380 = 82
sceneId2aCard.s3s_410 = 83
sceneId2aCard.s3s_460 = 84
sceneId2aCard.s3s_470 = 85
sceneId2aCard.s3s_550 = 86
sceneId2aCard.s3s_580_sel = 87
sceneId2aCard.s3s_600 = 88
sceneId2aCard.s3s_650 = 89
sceneId2aCard.s3s_641_sel = 90
sceneId2aCard.s3s_670 = 91
sceneId2aCard.s3s_590 = 92
sceneId2aCard.s5s_806 = 93
sceneId2aCard.s8s_50 = 94
sceneId2aCard.keyword = 95
sceneId2aCard.keyword = 96
sceneId2aCard.keyword = 97
sceneId2aCard.s6s_10 = 98
sceneId2aCard.s6s_20 = 99
sceneId2aCard.s6s_60_sel = 100
sceneId2aCard.s6s_70 = 101
sceneId2aCard.s6s_110 = 102
sceneId2aCard.s6s_150_sel = 103
sceneId2aCard.s6s_160 = 104
sceneId2aCard.keyword = 105
sceneId2aCard.keyword = 106
sceneId2aCard.keyword = 107
sceneId2aCard.s6s_280_sel = 108
sceneId2aCard.keyword = 109
sceneId2aCard.s6s_290 = 110
sceneId2aCard.s8s_10 = 111
sceneId2aCard.s8s_30 = 112
sceneId2aCard.s8s_40 = 113
sceneId2aCard.keyword = 114
sceneId2aCard.keyword = 115
sceneId2aCard.keyword = 116
sceneId2aCard.keyword = 117
sceneId2aCard.e1s_10 = 118
sceneId2aCard.keyword = 119
sceneId2aCard.keyword = 120
sceneId2aCard.keyword = 121
sceneId2aCard.keyword = 122
sceneId2aCard.keyword = 123
sceneId2aCard.keyword = 124
sceneId2aCard.keyword = 125
sceneId2aCard.keyword = 126
sceneId2aCard.keyword = 127
sceneId2aCard.keyword = 128
sceneId2aCard.keyword = 129
sceneId2aCard.keyword = 130
sceneId2aCard.keyword = 131
sceneId2aCard.keyword = 132
sceneId2aCard.keyword = 133
sceneId2aCard.keyword = 134
sceneId2aCard.keyword = 135
sceneId2aCard.keyword = 136
sceneId2aCard.keyword = 137
sceneId2aCard.keyword = 138
sceneId2aCard.keyword = 139
sceneId2aCard.keyword = 140
sceneId2aCard.keyword = 141
sceneId2aCard.keyword = 142
sceneId2aCard.keyword = 143
sceneId2aCard.keyword = 144
sceneId2aCard.keyword = 145
sceneId2aCard.s4s_10 = 146
sceneId2aCard.s4s_30_sel = 147
sceneId2aCard.s4s_40 = 148
sceneId2aCard.s4s_51 = 149
sceneId2aCard.s4s_60 = 150
sceneId2aCard.s4s_70 = 151
sceneId2aCard.s4s_100_sel = 152
sceneId2aCard.s4s_130 = 153
sceneId2aCard.s4s_160_sel = 154
sceneId2aCard.s4s_180 = 155
sceneId2aCard.s4s_210_sel = 156
sceneId2aCard.s4s_215 = 157
sceneId2aCard.e2s_20 = 158
sceneId2aCard.s4s_290_sel = 159
sceneId2aCard.s4s_300 = 160
sceneId2aCard.s4s_310 = 161
sceneId2aCard.e2s_155 = 162
sceneId2aCard.s4s_330 = 163
sceneId2aCard.s4s_360_sel = 164
sceneId2aCard.s4s_370 = 165
sceneId2aCard.s4s_390 = 166
sceneId2aCard.s4s_420_sel = 167
sceneId2aCard.s4s_430 = 168
sceneId2aCard.s4s_450_sel = 169
sceneId2aCard.s4s_490_sel = 170
sceneId2aCard.s4s_560 = 171
sceneId2aCard.s4s_620 = 172
sceneId2aCard.s4s_670_sel = 173
sceneId2aCard.s4s_710 = 174
sceneId2aCard.s4s_720 = 175
sceneId2aCard.s4s_680 = 176
sceneId2aCard.s5s_20 = 177
sceneId2aCard.s5s_30 = 178
sceneId2aCard.s5s_40 = 179
sceneId2aCard.s5s_140 = 180
sceneId2aCard.s5s_260 = 181
sceneId2aCard.s5s_320 = 182
sceneId2aCard.s5s_410 = 183
sceneId2aCard.s5s_430 = 184
sceneId2aCard.s5s_520 = 185
sceneId2aCard.s5s_550 = 186
sceneId2aCard.s5s_580 = 187
sceneId2aCard.s5s_660 = 188
sceneId2aCard.s5s_680 = 189
sceneId2aCard.s5s_740 = 190
sceneId2aCard.s5s_820 = 191
sceneId2aCard.s6s_151 = 192
sceneId2aCard.s5s_870 = 193
sceneId2aCard.s5s_200 = 194
sceneId2aCard.s5s_805 = 195
cHan2Zen = function(p0)
    local v0
    p0 = string.gsub(p0, "0", "０")
    p0 = string.gsub(p0, "1", "１")
    p0 = string.gsub(p0, "2", "２")
    p0 = string.gsub(p0, "3", "３")
    p0 = string.gsub(p0, "4", "４")
    p0 = string.gsub(p0, "5", "５")
    p0 = string.gsub(p0, "6", "６")
    p0 = string.gsub(p0, "7", "７")
    p0 = string.gsub(p0, "8", "８")
    p0 = string.gsub(p0, "9", "９")
    p0 = string.gsub(p0, "a", "ａ")
    p0 = string.gsub(p0, "b", "ｂ")
    p0 = string.gsub(p0, "c", "ｃ")
    p0 = string.gsub(p0, "d", "ｄ")
    p0 = string.gsub(p0, "e", "ｅ")
    p0 = string.gsub(p0, "f", "ｆ")
    p0 = string.gsub(p0, "g", "ｇ")
    p0 = string.gsub(p0, "h", "ｈ")
    p0 = string.gsub(p0, "i", "ｉ")
    p0 = string.gsub(p0, "j", "ｊ")
    p0 = string.gsub(p0, "k", "ｋ")
    p0 = string.gsub(p0, "l", "ｌ")
    p0 = string.gsub(p0, "m", "ｍ")
    p0 = string.gsub(p0, "n", "ｎ")
    p0 = string.gsub(p0, "o", "ｏ")
    p0 = string.gsub(p0, "p", "ｐ")
    p0 = string.gsub(p0, "q", "ｑ")
    p0 = string.gsub(p0, "r", "ｒ")
    p0 = string.gsub(p0, "s", "ｓ")
    p0 = string.gsub(p0, "t", "ｔ")
    p0 = string.gsub(p0, "u", "ｕ")
    p0 = string.gsub(p0, "v", "ｖ")
    p0 = string.gsub(p0, "w", "ｗ")
    p0 = string.gsub(p0, "x", "ｘ")
    p0 = string.gsub(p0, "y", "ｙ")
    p0 = string.gsub(p0, "z", "ｚ")
    p0 = string.gsub(p0, "A", "Ａ")
    p0 = string.gsub(p0, "B", "Ｂ")
    p0 = string.gsub(p0, "C", "Ｃ")
    p0 = string.gsub(p0, "D", "Ｄ")
    p0 = string.gsub(p0, "E", "Ｅ")
    p0 = string.gsub(p0, "F", "Ｆ")
    p0 = string.gsub(p0, "G", "Ｇ")
    p0 = string.gsub(p0, "H", "Ｈ")
    p0 = string.gsub(p0, "I", "Ｉ")
    p0 = string.gsub(p0, "J", "Ｊ")
    p0 = string.gsub(p0, "K", "Ｋ")
    p0 = string.gsub(p0, "L", "Ｌ")
    p0 = string.gsub(p0, "M", "Ｍ")
    p0 = string.gsub(p0, "N", "Ｎ")
    p0 = string.gsub(p0, "O", "Ｏ")
    p0 = string.gsub(p0, "P", "Ｐ")
    p0 = string.gsub(p0, "Q", "Ｑ")
    p0 = string.gsub(p0, "R", "Ｒ")
    p0 = string.gsub(p0, "S", "Ｓ")
    p0 = string.gsub(p0, "T", "Ｔ")
    p0 = string.gsub(p0, "U", "Ｕ")
    p0 = string.gsub(p0, "V", "Ｖ")
    p0 = string.gsub(p0, "W", "Ｗ")
    p0 = string.gsub(p0, "X", "Ｘ")
    p0 = string.gsub(p0, "Y", "Ｙ")
    p0 = string.gsub(p0, "Z", "Ｚ")
    p0 = string.gsub(p0, "!", "！")
    p0 = string.gsub(p0, "%?", "？")
    p0 = string.gsub(p0, "%:", "：")
    p0 = string.gsub(p0, "%(", "（")
    p0 = string.gsub(p0, "%)", "）")
    p0 = string.gsub(p0, "%-", "－")
    return p0
end
cfontPrint = function(p0, p1, p2, p3, p4, p5)
    fontPrint(p0, p1, p2, p3, p4, cHan2Zen(p5))
end
storyRouteMax = 99
cMakeStoryRoute = function()
    local v0 = 1
    local v1 = storyRouteMax
    local v2 = 1
    local i0, v3
    for i0 = v0, v1, v2 do
        gameSave.storyRoute[i0] = {}
        gameSave.storyRoute[i0].sceneId = -1
        gameSave.storyRoute[i0].ayanoTime = -1
    end
end
cInitStoryRoute = function()
    local v0 = 1
    local v1 = storyRouteMax
    local v2 = 1
    local i0
    for i0 = v0, v1, v2 do
        gameSave.storyRoute[i0].sceneId = -1
        gameSave.storyRoute[i0].ayanoTime = -1
    end
end
cClearNumStoryRoute = function(p0)
    local v0 = p0
    local v1 = storyRouteMax
    local v2 = 1
    local i1
    for i1 = v0, v1, v2 do
        gameSave.storyRoute[i1].sceneId = -1
        gameSave.storyRoute[i1].ayanoTime = -1
    end
end
cBrStr = function(p0)
    local v0 = ""
    local v1 = 1
    local v2, v3, i2, v4, v5
    v2 = string.len(p0)
    v3 = 1
    for i2 = v1, v2, v3 do
        v4 = v0
        v5 = string.sub(p0, i2, i2)
        v0 = v4 .. v5
        v4 = i2 % 24
        if v4 == 0 then
            v4 = v0
            v5 = "\n"
            v0 = v4 .. v5
        end
    end
    return v0
end
myCardMax = 195
cMakeMyCard = function()
    local v0 = 1
    local v1 = myCardMax
    local v2 = 1
    local i0, v3
    for i0 = v0, v1, v2 do
        gameSave.myCard[i0] = {}
        gameSave.myCard[i0].hold = -1
    end
end
cardSort = {}
v0 = 1
v1 = myCardMax
v2 = 1
for i0 = v0, v1, v2 do
    cardSort[i0] = {}
end
cardSort[1][1] = 1
cardSort[44][1] = 2
cardSort[45][1] = 3
cardSort[46][1] = 4
cardSort[47][1] = 5
cardSort[48][1] = 6
cardSort[49][1] = 7
cardSort[50][1] = 8
cardSort[51][1] = 9
cardSort[52][1] = 10
cardSort[53][1] = 11
cardSort[54][1] = 12
cardSort[55][1] = 13
cardSort[56][1] = 14
cardSort[57][1] = 15
cardSort[58][1] = 16
cardSort[59][1] = 17
cardSort[60][1] = 18
cardSort[61][1] = 19
cardSort[62][1] = 20
cardSort[63][1] = 21
cardSort[64][1] = 22
cardSort[65][1] = 23
cardSort[66][1] = 24
cardSort[67][1] = 25
cardSort[3][1] = 26
cardSort[68][1] = 27
cardSort[69][1] = 28
cardSort[70][1] = 29
cardSort[71][1] = 30
cardSort[72][1] = 31
cardSort[73][1] = 32
cardSort[74][1] = 33
cardSort[75][1] = 34
cardSort[76][1] = 35
cardSort[78][1] = 36
cardSort[79][1] = 37
cardSort[80][1] = 38
cardSort[81][1] = 39
cardSort[82][1] = 40
cardSort[83][1] = 41
cardSort[85][1] = 42
cardSort[86][1] = 43
cardSort[87][1] = 44
cardSort[88][1] = 45
cardSort[89][1] = 46
cardSort[90][1] = 47
cardSort[91][1] = 48
cardSort[92][1] = 49
cardSort[93][1] = 50
cardSort[94][1] = 51
cardSort[95][1] = 52
cardSort[96][1] = 53
cardSort[97][1] = 54
cardSort[98][1] = 55
cardSort[99][1] = 56
cardSort[100][1] = 57
cardSort[101][1] = 58
cardSort[102][1] = 59
cardSort[103][1] = 60
cardSort[104][1] = 61
cardSort[84][1] = 62
cardSort[77][1] = 63
cardSort[105][1] = 64
cardSort[106][1] = 65
cardSort[107][1] = 66
cardSort[108][1] = 67
cardSort[109][1] = 68
cardSort[110][1] = 69
cardSort[111][1] = 70
cardSort[112][1] = 71
cardSort[113][1] = 72
cardSort[114][1] = 73
cardSort[115][1] = 74
cardSort[116][1] = 75
cardSort[117][1] = 76
cardSort[118][1] = 77
cardSort[119][1] = 78
cardSort[120][1] = 79
cardSort[121][1] = 80
cardSort[122][1] = 81
cardSort[123][1] = 82
cardSort[124][1] = 83
cardSort[125][1] = 84
cardSort[126][1] = 85
cardSort[127][1] = 86
cardSort[128][1] = 87
cardSort[130][1] = 88
cardSort[132][1] = 89
cardSort[131][1] = 90
cardSort[133][1] = 91
cardSort[129][1] = 92
cardSort[179][1] = 93
cardSort[195][1] = 94
cardSort[6][1] = 95
cardSort[7][1] = 96
cardSort[8][1] = 97
cardSort[182][1] = 98
cardSort[183][1] = 99
cardSort[184][1] = 100
cardSort[185][1] = 101
cardSort[186][1] = 102
cardSort[187][1] = 103
cardSort[189][1] = 104
cardSort[9][1] = 105
cardSort[10][1] = 106
cardSort[11][1] = 107
cardSort[190][1] = 108
cardSort[12][1] = 109
cardSort[191][1] = 110
cardSort[192][1] = 111
cardSort[193][1] = 112
cardSort[194][1] = 113
cardSort[13][1] = 114
cardSort[14][1] = 115
cardSort[15][1] = 116
cardSort[16][1] = 117
cardSort[2][1] = 118
cardSort[17][1] = 119
cardSort[18][1] = 120
cardSort[19][1] = 121
cardSort[20][1] = 122
cardSort[21][1] = 123
cardSort[22][1] = 124
cardSort[23][1] = 125
cardSort[24][1] = 126
cardSort[25][1] = 127
cardSort[26][1] = 128
cardSort[27][1] = 129
cardSort[28][1] = 130
cardSort[29][1] = 131
cardSort[30][1] = 132
cardSort[31][1] = 133
cardSort[32][1] = 134
cardSort[33][1] = 135
cardSort[34][1] = 136
cardSort[35][1] = 137
cardSort[36][1] = 138
cardSort[37][1] = 139
cardSort[38][1] = 140
cardSort[39][1] = 141
cardSort[40][1] = 142
cardSort[41][1] = 143
cardSort[42][1] = 144
cardSort[43][1] = 145
cardSort[134][1] = 146
cardSort[135][1] = 147
cardSort[136][1] = 148
cardSort[137][1] = 149
cardSort[138][1] = 150
cardSort[139][1] = 151
cardSort[140][1] = 152
cardSort[141][1] = 153
cardSort[142][1] = 154
cardSort[143][1] = 155
cardSort[144][1] = 156
cardSort[145][1] = 157
cardSort[4][1] = 158
cardSort[146][1] = 159
cardSort[147][1] = 160
cardSort[148][1] = 161
cardSort[5][1] = 162
cardSort[149][1] = 163
cardSort[150][1] = 164
cardSort[151][1] = 165
cardSort[152][1] = 166
cardSort[153][1] = 167
cardSort[154][1] = 168
cardSort[155][1] = 169
cardSort[156][1] = 170
cardSort[157][1] = 171
cardSort[158][1] = 172
cardSort[159][1] = 173
cardSort[161][1] = 174
cardSort[162][1] = 175
cardSort[160][1] = 176
cardSort[163][1] = 177
cardSort[164][1] = 178
cardSort[165][1] = 179
cardSort[166][1] = 180
cardSort[168][1] = 181
cardSort[169][1] = 182
cardSort[170][1] = 183
cardSort[171][1] = 184
cardSort[172][1] = 185
cardSort[173][1] = 186
cardSort[174][1] = 187
cardSort[175][1] = 188
cardSort[176][1] = 189
cardSort[177][1] = 190
cardSort[180][1] = 191
cardSort[188][1] = 192
cardSort[181][1] = 193
cardSort[167][1] = 194
cardSort[178][1] = 195
plotTitle = {}
plotTitle[1] = "ある子が学校にくる物語"
plotTitle[2] = "夏の朝、高校までの通学路"
plotTitle[3] = "放課後の約束"
plotTitle[4] = "選択：放課後の約束"
plotTitle[5] = "約束をしている"
plotTitle[6] = "約束を思い出せない"
plotTitle[7] = "約束をしていない"
plotTitle[8] = "約束を思い出す"
plotTitle[9] = "朝の教室"
plotTitle[10] = "セクション１：アヤノ"
plotTitle[11] = "昼休みの教室"
plotTitle[12] = "選択：ユウイチの答案"
plotTitle[13] = "答案を羨ましがる"
plotTitle[14] = "答案を受け流す"
plotTitle[15] = "授業が始まる"
plotTitle[16] = "放課後"
plotTitle[17] = "ユウイチとファストフード"
plotTitle[18] = "選択：学校に戻る"
plotTitle[19] = "いつもの生活"
plotTitle[20] = "探索：放課後の学校"
plotTitle[21] = "放課後のコックリさん"
plotTitle[22] = "彼女との出会い"
plotTitle[23] = "良くない結果"
plotTitle[24] = "気がつくといる場所"
plotTitle[25] = "選択：声の主"
plotTitle[26] = "誰も来ない"
plotTitle[27] = "彼女の名前"
plotTitle[28] = "約束はまもらないと"
plotTitle[29] = "ユウイチはアヤノを助ける"
plotTitle[30] = "誰かが呼んでた"
plotTitle[31] = "また、いつもの生活"
plotTitle[32] = "夏の予定"
plotTitle[33] = "選択：週末の予定"
plotTitle[34] = "休み時間"
plotTitle[35] = "選択：オマジナイへの興味"
plotTitle[36] = "セクション２：アヤノ"
plotTitle[37] = "ユウイチとの仲"
plotTitle[38] = "選択：ユウイチへの想い"
plotTitle[39] = "ユウイチのことが好き"
plotTitle[40] = "ユウイチのことは……"
plotTitle[41] = "選択：ナゾトキ"
plotTitle[42] = "ナゾトキの間違い"
plotTitle[43] = "出かける場所"
plotTitle[44] = "選択：出かける場所"
plotTitle[45] = "プールの約束"
plotTitle[46] = "プラネタリウムの約束"
plotTitle[47] = "図書室"
plotTitle[48] = "選択：放課後のオマジナイ"
plotTitle[49] = "オマジナイ、成功……？"
plotTitle[50] = "消しゴムに名前"
plotTitle[51] = "選択：オマジナイの効果"
plotTitle[52] = "絶対に効くと思う"
plotTitle[53] = "たぶん効くと思う"
plotTitle[54] = "やってソンはないと思う"
plotTitle[55] = "オマジナイ完了"
plotTitle[56] = "廊下に響く声"
plotTitle[57] = "ユウイチの後ろ姿"
plotTitle[58] = "夜の廊下"
plotTitle[59] = "プール"
plotTitle[60] = "プラネタリウム"
plotTitle[61] = "オマジナイの効果"
plotTitle[62] = "ナゾトキの正解"
plotTitle[63] = "サクラのため息"
plotTitle[64] = "昼休みの廊下"
plotTitle[65] = "選択：階段のウワサ"
plotTitle[66] = "選択：興味深いウワサ"
plotTitle[67] = "選択：ウワサとは"
plotTitle[68] = "ウワサに興味がない"
plotTitle[69] = "お化け階段"
plotTitle[70] = "選択：ウワサ話を……"
plotTitle[71] = "適当に聞く"
plotTitle[72] = "とりあえず聞いてみる"
plotTitle[73] = "真剣に聞く"
plotTitle[74] = "探索：放課後の学校"
plotTitle[75] = "選択：ユウイチの影"
plotTitle[76] = "ほうっておく"
plotTitle[77] = "陸上部のウワサ"
plotTitle[78] = "選択：向かう場所"
plotTitle[79] = "後をつける"
plotTitle[80] = "口づけ"
plotTitle[81] = "セクション３：アヤノ"
plotTitle[82] = "走り去るアヤノ"
plotTitle[83] = "階段へ"
plotTitle[84] = "ユウイチの腕"
plotTitle[85] = "屋上"
plotTitle[86] = "ユウイチと階段へ"
plotTitle[87] = "選択：ユウイチと……"
plotTitle[88] = "ずっと一緒にいたい"
plotTitle[89] = "ユウイチとキス"
plotTitle[90] = "選択：花火の中、ユウイチと"
plotTitle[91] = "ユウイチとキスしない"
plotTitle[92] = "でも、いつかは別れが"
plotTitle[93] = "アヤノの返信：９月２５日"
plotTitle[94] = "誰も見たことのない夕焼け"
plotTitle[95] = "中庭の人だかり"
plotTitle[96] = "サクラさんのナゾトキ"
plotTitle[97] = "絶対に効くオマジナイ"
plotTitle[98] = "インパクトのあるウワサ"
plotTitle[99] = "セクション６：アヤノ"
plotTitle[100] = "選択：どこで読む"
plotTitle[101] = "サクラからの手紙"
plotTitle[102] = "図書室で読む"
plotTitle[103] = "選択：ノート"
plotTitle[104] = "Ｔｒｕｅ Ｃｏｌｏｒ"
plotTitle[105] = "自己暗示"
plotTitle[106] = "強迫観念"
plotTitle[107] = "先生は信用できない"
plotTitle[108] = "選択：屋上の帰り道"
plotTitle[109] = "冬の告白は失敗する"
plotTitle[110] = "中庭の雪"
plotTitle[111] = "僕の言葉"
plotTitle[112] = "セクション８：ユウイチ、直哉"
plotTitle[113] = "フェンスの向こう側"
plotTitle[114] = "ナオヤ"
plotTitle[115] = "アヤノ"
plotTitle[116] = "屋上から転落"
plotTitle[117] = "気がつくと屋上"
plotTitle[118] = "春"
plotTitle[119] = "屋上"
plotTitle[120] = "将来の職業"
plotTitle[121] = "すぐに家に帰ってた"
plotTitle[122] = "コックリさん"
plotTitle[123] = "ユウイチ"
plotTitle[124] = "サクラ"
plotTitle[125] = "ユカリ先生"
plotTitle[126] = "物語の主人公"
plotTitle[127] = "夫婦喧嘩"
plotTitle[128] = "黒板の上の時計"
plotTitle[129] = "きくちゃん"
plotTitle[130] = "消しゴム"
plotTitle[131] = "あの子と会う約束"
plotTitle[132] = "ハンバーガー"
plotTitle[133] = "Ｓｅｃｔｉｏｎ１あらすじ"
plotTitle[134] = "Ｓｅｃｔｉｏｎ２あらすじ"
plotTitle[135] = "Ｓｅｃｔｉｏｎ３Ａあらすじ"
plotTitle[136] = "Ｓｅｃｔｉｏｎ３Ｂあらすじ"
plotTitle[137] = "Ｓｅｃｔｉｏｎ４Ａあらすじ"
plotTitle[138] = "Ｓｅｃｔｉｏｎ４Ｂあらすじ"
plotTitle[139] = "Ｓｅｃｔｉｏｎ５あらすじ"
plotTitle[140] = "Ｓｅｃｔｉｏｎ６あらすじ"
plotTitle[141] = "Ｓｅｃｔｉｏｎ７あらすじ"
plotTitle[142] = "Ｓｅｃｔｉｏｎ８あらすじ"
plotTitle[143] = "ＳｅｃｔｉｏｎＥｘ１"
plotTitle[144] = "ＳｅｃｔｉｏｎＥｘ２"
plotTitle[145] = "いつかきみがみるお話。"
plotTitle[146] = "ポケットの中のメモ"
plotTitle[147] = "選択：屋上のウワサ"
plotTitle[148] = "私じゃない"
plotTitle[149] = "気になるね"
plotTitle[150] = "セクション４：ユウイチ"
plotTitle[151] = "図書室の先生"
plotTitle[152] = "選択：ユカリ先生"
plotTitle[153] = "どこかで見たことのある少女"
plotTitle[154] = "選択：メモを見たとき"
plotTitle[155] = "興味はない"
plotTitle[156] = "探索：アヤノに何が？"
plotTitle[157] = "廊下のユウイチ"
plotTitle[158] = "セクションＥＸ２：女子生徒"
plotTitle[159] = "選択：メモの内容"
plotTitle[160] = "下らない、と思った"
plotTitle[161] = "信じてみてもいい"
plotTitle[162] = "セカンドノベル"
plotTitle[163] = "ひっくり返った机"
plotTitle[164] = "選択：アヤノの机"
plotTitle[165] = "屋上の人影"
plotTitle[166] = "アヤノの机を調べる"
plotTitle[167] = "選択：アヤノのノート"
plotTitle[168] = "ノートに書かれた名前"
plotTitle[169] = "探索：アヤノの居場所"
plotTitle[170] = "選択：アヤノを――"
plotTitle[171] = "腕をつかむ"
plotTitle[172] = "アヤノは意識を取り戻す"
plotTitle[173] = "選択：放課後の学校"
plotTitle[174] = "セクション４：アヤノ"
plotTitle[175] = "サクラを待つ"
plotTitle[176] = "消えたサクラ"
plotTitle[177] = "サクラさん"
plotTitle[178] = "セクション５：サクラ"
plotTitle[179] = "サクラの日記：９月１３日"
plotTitle[180] = "サクラの日記：７月（書きかけ）"
plotTitle[181] = "サクラの日記：９月１６日"
plotTitle[182] = "サクラの日記：９月１６日（夜）"
plotTitle[183] = "サクラの日記：９月２０日"
plotTitle[184] = "サクラの日記：９月２２日"
plotTitle[185] = "サクラの日記：９月２３日"
plotTitle[186] = "サクラの日記：９月２９日"
plotTitle[187] = "サクラの日記：断片"
plotTitle[188] = "サクラの日記：１０月３日"
plotTitle[189] = "サクラの日記：１１月１２日"
plotTitle[190] = "サクラの日記：２月１３日"
plotTitle[191] = "アヤノの返信：１０月３０日"
plotTitle[192] = "失われた夢の物語"
plotTitle[193] = "２月、中庭"
plotTitle[194] = "中庭のアヤノさん"
plotTitle[195] = "セクション５：アヤノ"
v0 = 1
v1 = 195
v2 = 1
for i0 = v0, v1, v2 do
    v4 = cBrStr(plotTitle[i0])
    plotTitle[i0] = v4
end
layerName = {}
layerName.event = 0
layerName.bg1 = 0
layerName.bg2 = 1
layerName.bg3 = 2
layerName.bg4 = 3
layerName.bg5 = 4
layerName.pose1 = 5
layerName.pose2 = 6
layerName.pose3 = 7
layerName.pose4 = 8
layerName.pose5 = 9
layerName.swap = 10
layerName.pose6 = 11
layerName.plot = 20
layerName.card1 = 40
layerName.card2 = 41
layerName.card3 = 80
layerName.hour1 = 42
layerName.hour2 = 43
layerName.scene = 44
layerName.sceneType = 45
layerName.reading = 46
layerName.dlg = 70
layerName.dlgCursor = 85
layerName.cardLabel1 = 50
layerName.cardLabel2 = 51
layerName.effectBlack = 204
layerName.effectWhite = 205
layerName.effectYellow = 206
layerName.sys_4_a = 207
layerName.sys_4_b = 208
layerName.bg_1_a_0 = 209
layerName.po1_aya_f_1_a = 210
layerName.sys_5_e = 211
layerName.title_01_a = 212
layerName.title_02_a = 213
layerName.title_03_a = 214
layerName.title_04_a = 215
layerName.title_05_a = 216
layerName.title_06_a = 217
layerName.title_07_a = 218
layerName.title_08_a = 219
layerName.title_09_a = 220
layerName.title_10_a = 221
layerName.title_11_a = 222
layerName.title_12_a = 223
layerName.title_13_a = 224
layerName.sys_7_a = 225
layerName.sys_8_a = 226
layerName.sys_2_a = 227
layerName.sys_2_b = 228
layerName.sys_2_c = 229
layerName.sys_3_a = 230
layerName.sys_12_a = 231
layerName.sys_12_b = 232
layerName.sys_12_c = 233
layerName.sys_12_d = 234
layerName.sys_12_e = 235
layerName.sys_12_f = 236
layerName.sys_12_g = 237
layerName.sys_13_a = 238
layerName.sys_13_b = 239
layerName.sys_13_c = 240
layerName.sys_13_d = 241
layerName.sys_9_a = 242
layerName.sel_map_0_a = 243
layerName.sel_map_1_a = 244
layerName.sel_map_2_a = 245
layerName.sel_map_2_b = 246
layerName.sys_2_d = 247
layerName.plot_1_a = 248
layerName.plot_2_a = 249
layerName.plot_3_a = 250
layerName.plot_4_a = 251
layerName.scene_1_a = 252
layerName.scene_2_a = 253
layerName.sys_1_j = 254
layerName.titleBG = 255
seName = {}
seName.getCard = 4
seName.arrowKey = 5
seName.circle = 6
seName.cross = 7
seName.viewCard = 8
backLayerName = {}
backLayerName.sys_20_a = 299
backLayerName.sys_20_b = 298
backLayerName.sys_20_c = 297
backLayerName.sys_20_d = 296
backLayerName.sys_20_e = 295
backLayerName.sys_20_f = 294
backLayerName.sys_21_a = 293
backLayerName.sys_21_b = 292
backLayerName.sys_21_c = 291
backLayerName.sys_21_d = 290
backLayerName.sys_21_e = 289
backLayerName.sys_21_f = 288
backLayerName.sys_22_a = 287
backLayerName.sys_22_ba = 286
backLayerName.sys_22_bb = 285
backLayerName.sys_22_c = 284
backLayerName.sys_22_d = 283
backLayerName.sys_22_e = 282
backLayerName.sys_23_a = 281
backLayerName.sys_23_b = 280
backLayerName.sys_23_c = 279
backLayerName.sys_23_d = 278
backLayerName.sys_23_e = 277
backLayerName.sys_23_f = 276
backLayerName.sys_24_b = 275
backLayerName.sys_24_c = 274
backLayerName.sys_11_a = 273
backLayerName.sys_11_b = 272
backLayerName.sys_11_c = 271
backLayerName.sys_11_d = 270
backLayerName.black = 269
backLayerName.sys_11_e = 268
backLayerName.sys_5_e = 267
backLayerName.sys_5_g = 266
backLayerName.sys_13_b = 265
backLayerName.sys_13_c = 264
backLayerName.sys_5_h = 263
backLayerName.sys_5_i = 262
backLayerName.sys_5_j = 261
plotState = {}
v0 = 0
v1 = 0
v2 = layerName.plot_1_a
i0 = 1
v3 = 1
v4 = 195
v5 = 1
for i4 = v3, v4, v5 do
    plotState[i4] = {}
    v7 = v0 * 82
    plotState[i4].clipX = v7
    v7 = v1 * 48
    plotState[i4].clipY = v7
    plotState[i4].layerName = v2
    v6 = v0 + 1
    if 5 < v6 then
        v0 = 0
        v1 = v1 + 1
    else
        v0 = v0 + 1
    end
    v6 = i0 * 60
    if v6 <= i4 then
        v0 = 0
        v1 = 0
        i0 = i0 + 1
        v2 = v2 + 1
    end
end
sceneState = {}
v3 = 0
v4 = 0
v5 = layerName.scene_1_a
i4 = 1
v6 = 1
v8 = 195
v7 = 1
for i8 = v6, v8, v7 do
    sceneState[i8] = {}
    v10 = v3 * 145
    sceneState[i8].clipX = v10
    v10 = v4 * 15
    sceneState[i8].clipY = v10
    sceneState[i8].layerName = v5
    v9 = v3 + 1
    if 2 < v9 then
        v3 = 0
        v4 = v4 + 1
    else
        v3 = v3 + 1
    end
    v9 = i4 * 102
    if v9 <= i8 then
        v3 = 0
        v4 = 0
        i4 = i4 + 1
        v5 = v5 + 1
    end
end
cMakeStoryRoute()
cMakeMyCard()
nowPlayBgmFileName = ""
cPlayBGMWrap = function(p0)
    if not (p0 == nowPlayBgmFileName) then
        playBGM(0, p0, true)
        nowPlayBgmFileName = p0
    end
end
cPlayBGMNotLoop = function(p0)
    playBGM(0, p0, false)
    nowPlayBgmFileName = ""
end
cStopBGMWrap = function(...)
    local v0 = 30
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    stopBGM(0, v0)
    nowPlayBgmFileName = ""
end
cLoadPlaySE = function(p0, p1)
    loadSE(0, p0)
    waitLoading()
    playSE(0, p1)
end
nowPlayLoopSeFileName = ""
cPlayLoopSeWrap = function(p0)
    if not (p0 == nowPlayLoopSeFileName) then
        playBGM(1, p0, true)
        nowPlayLoopSeFileName = p0
    end
end
cStopLoopSeWrap = function(...)
    local v0 = 30
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    stopBGM(1, v0)
    nowPlayLoopSeFileName = ""
end
cPlayOneshotMusic = function(p0)
    playBGM(1, p0, false)
    nowPlayLoopSeFileName = ""
end
cStopOneshotMusic = function(...)
    local v0 = 30
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    stopBGM(1, v0)
end
cGetFileName = function(p0, p1)
    local v0 = ""
    local v1, v2, v3
    if p0 == "bg" then
        v0 = "bg/" .. p1 .. ".gim"
    end
    if p0 == "bgm" then
        v0 = "bgm/" .. p1 .. ".at3"
    end
    if p0 == "card" then
        v0 = "card/" .. p1 .. ".gim"
    end
    if p0 == "cutin" then
        v0 = "cutin/" .. p1 .. ".gim"
    end
    if p0 == "effect" then
        v0 = "effect/" .. p1 .. ".gim"
    end
    if p0 == "event" then
        v0 = "event/" .. p1 .. ".gim"
        if not (systemSave.cgFlag[p1] == true) then
            systemSave.cgFlag[p1] = true
        end
    end
    if p0 == "plot" then
        v0 = "plot/" .. p1 .. ".gim"
    end
    if p0 == "pose" then
        v0 = "pose/" .. p1 .. ".gim"
    end
    if p0 == "script" then
        v0 = "script/" .. p1 .. ".lua"
    end
    if p0 == "scriptc" then
        v0 = "script/" .. p1 .. ".lua"
    end
    if p0 == "se" then
        v0 = "se/" .. p1 .. ".vag"
    end
    if p0 == "loop" then
        v0 = "se/" .. p1 .. ".at3"
    end
    if p0 == "mus" then
        v0 = "se/" .. p1 .. ".at3"
    end
    if p0 == "sysgim" then
        v0 = "sysgim/" .. p1 .. ".gim"
    end
    if p0 == "scene" then
        v0 = "scene/" .. p1 .. ".gim"
    end
    if p0 == "select" then
        v0 = "select/" .. p1 .. ".gim"
    end
    return v0
end
cInitBgm = function()
    cStopBGMWrap()
end
cInitSe = function()
    local v0 = 0
    local v1 = 7
    local v2 = 1
    local i0
    for i0 = v0, v1, v2 do
        stopSE(i0)
    end
end
cInitLoopSe = function()
    cStopLoopSeWrap()
end
cInitOneshotMusic = function()
    cStopOneshotMusic()
end
cInitLayer = function()
    local v0 = 0
    local v1 = 199
    local v2 = 1
    local i0
    for i0 = v0, v1, v2 do
        layerLoad(i0, "")
    end
end
cInitGame = function()
    msgQuit()
    fontClear()
    cInitBgm()
    cInitSe()
    cInitLoopSe()
    cInitOneshotMusic()
    cInitLayer()
end
cInitScene = function()
    cInitSe()
    cInitOneshotMusic()
    cInitLayer()
end
fragmentItemCount = 1
fragmentCursorCount = 0
fragmentCursorPage = 1
vms = function(p0, p1, p2)
    local v0, v1, v2
    if not (p1 == "NONVOICE") then
        if not (p1 == "NORECORD") then
            if voiceFlag == true then
                playVoice("voice/" .. p1 .. ".at3")
            end
        else
        end
    else
    end
    msg(p0, p2)
end
ObjectCommon = {}
ObjectCommon.new = function()
    local v0 = {}
    local v1, v3
    v0.startMenuState = 0
    v0.debagMsg = function(p0)
        local v0 = debagFlag
        local v1
        if v0 then
            v1 = ("■デバッグ：") .. p0
            vms(1, "NONVOICE", v1)
        end
    end
    v0.debagPairs = function(p0)
        local v0 = debagFlag
        local v1, v2, g4, g5, v3, v4
        if v0 then
            v1 = p0
            v0, v1, v2 = pairs(v1)
            for g4, g5 in v0, v1, v2 do
                vms(2, "NONVOICE", "Ｋｅｙ＿" .. g4 .. "：Ｖａｌｕｅ＿" .. g5)
            end
        end
    end
    return v0
end
oCom = ObjectCommon.new()
ObjectHourGlass = {}
ObjectHourGlass.new = function()
    local v0 = {}
    local v1, v3, v4, v5, v6, v2
    v0.layerNo = layerName.hour1
    v0.layerNo2 = layerName.hour2
    v0.setHourGlassCount2FileName = function(p0)
        local v0 = 0
        local v1 = 0
        if 100 <= p0 then
            v0 = 240
            v1 = 60
        elseif 90 <= p0 then
            v0 = 180
            v1 = 60
        elseif 80 <= p0 then
            v0 = 120
            v1 = 60
        elseif 70 <= p0 then
            v0 = 60
            v1 = 60
        elseif 60 <= p0 then
            v0 = 0
            v1 = 60
        elseif 50 <= p0 then
            v0 = 240
            v1 = 0
        elseif 40 <= p0 then
            v0 = 180
            v1 = 0
        elseif 30 <= p0 then
            v0 = 120
            v1 = 0
        elseif 20 <= p0 then
            v0 = 60
            v1 = 0
        elseif 10 <= p0 then
            v0 = 0
            v1 = 0
        end
        return v0, v1
    end
    v0.hourGlassStageIn = function(p0)
        local v1, v2, v3, v4
        v1, v2 = v0.setHourGlassCount2FileName(p0)
        layerCopy(v0.layerNo, layerName.sys_4_a)
        v3 = v1 + 60
        v4 = v2 + 60
        layerClip(v0.layerNo, v1, v2, v3, v4)
        layerAnime(v0.layerNo, 4, true)
        layerAlpha(v0.layerNo, 0)
        layerPosition(v0.layerNo, 520, -30)
        layerMovePosition(v0.layerNo, 400, 10, 30)
        layerMoveAlpha(v0.layerNo, 100, 30)
        wait(30)
    end
    v0.hourGlassStageOut = function(p0)
        layerMovePosition(v0.layerNo, -50, -50, 30)
        layerMoveAlpha(v0.layerNo, 0, 30)
        wait(30)
        layerLoad(v0.layerNo, "")
        switchScreen(0, "", 30)
        wait(10)
    end
    v0.hourGlassStageCngTo = function(p0, p1)
        local v1, v2, v3, v4, v5, v6
        v1, v2 = v0.setHourGlassCount2FileName(p1)
        v3, v4 = v0.setHourGlassCount2FileName(p0)
        layerCopy(v0.layerNo2, layerName.sys_4_a)
        layerClip(v0.layerNo2, v3, v4, (v3 + 60), (v4 + 60))
        layerAlpha(v0.layerNo2, 100)
        layerPosition(v0.layerNo2, 5, 5)
        layerMoveAlpha(v0.layerNo2, 0, 30)
        layerCopy(v0.layerNo, layerName.sys_4_a)
        v5 = v1 + 60
        v6 = v2 + 60
        layerClip(v0.layerNo, v1, v2, v5, v6)
        layerAlpha(v0.layerNo, 0)
        layerPosition(v0.layerNo, 5, 5)
        layerMoveAlpha(v0.layerNo, 100, 30)
        layerAnime(v0.layerNo, 4, true)
        wait(30)
        layerLoad(v0.layerNo2, "")
        switchScreen(0, "", 30)
        wait(10)
    end
    v0.hourGlassStageStart = function()
        local v1, v2, v3, v4, v5, v6
        advPart(false)
        layerAlpha(v0.layerNo, 100)
        v1, v2 = v0.setHourGlassCount2FileName(100)
        layerClip(v0.layerNo, v1, v2, (v1 + 60), (v2 + 60))
        layerPosition(v0.layerNo, 5, 5)
        layerMovePosition(v0.layerNo, 5, -10, 40)
        layerMoveRotate(v0.layerNo, 0, 0, 180, 40)
        wait(40)
        v5, v6 = v0.setHourGlassCount2FileName(0)
        v2 = v6
        v1 = v5
        layerClip(v0.layerNo, v1, v2, (v1 + 60), (v2 + 60))
        layerPosition(v0.layerNo, 5, -10)
        layerRotate(v0.layerNo, 0, 0, 0)
        switchScreen(0, "", 15)
        layerMovePosition(v0.layerNo, 5, 5, 30)
        wait(30)
        advPart(true)
    end
    return v0
end
oHour = ObjectHourGlass.new()
comDlgYesNo = function(p0, p1, p2)
    return comDlgYesNoSel(p0, p1, p2, 0)
end
comDlgYesNoSel = function(p0, p1, p2, p3)
    local v0 = 0
    local v1 = false
    local v2, v3, v4, v5, v6, v7, v8, v9
    if p3 == 1 then
        v0 = 1
    end
    layerCopy(layerName.dlg, layerName.sys_5_e)
    layerLoad((layerName.dlg + 1), p0)
    layerPosition((layerName.dlg + 1), p1, p2)
    layerCopy((layerName.dlg + 2), layerName.sys_13_b)
    layerPosition((layerName.dlg + 2), 184, (139 + (23 * v0)))
    layerCopy((layerName.dlg + 3), layerName.sys_13_c)
    layerPosition((layerName.dlg + 3), 217, 142)
    switchScreen(0, "", 10)
    wait(10)
    v4 = 1
    v2 = 1
    v5 = 1
    v3 = 1
    v6 = 0
    while true do
        v7 = pressButton("UP")
        if (v7 == true) and (v1 == false) and (v4 == 0) then
            v7 = v0 - 1
            if v7 < 0 then
                v0 = 1
            else
                v0 = v0 - 1
            end
            v1 = true
        end
        v7 = pressButton("UP")
        if v7 == false then
            v4 = 0
        end
        v7 = pressButton("DOWN")
        if (v7 == true) and (v1 == false) and (v2 == 0) then
            v7 = v0 + 1
            if 1 < v7 then
                v0 = 0
            else
                v0 = v0 + 1
            end
            v1 = true
        end
        v7 = pressButton("DOWN")
        if v7 == false then
            v2 = 0
        end
        v7 = pressButton("CIRCLE")
        if (v7 == true) and (v1 == false) and (v5 == 0) then
            keyPlaySE(seName.circle)
            break
        else
            v7 = pressButton("CIRCLE")
            if v7 == false then
                v5 = 0
            end
            v7 = pressButton("CROSS")
            if (v7 == true) and (v1 == false) and (v3 == 0) then
                keyPlaySE(seName.cross)
                v0 = 1
                break
            else
                v7 = pressButton("CROSS")
                if v7 == false then
                    v3 = 0
                end
                if v1 == true then
                    keyPlaySE(seName.arrowKey)
                    layerMovePosition((layerName.dlg + 2), 184, (139 + (23 * v0)), 5)
                    wait(5)
                    v1 = false
                end
                v6 = v6 + 1
                if 12 < v6 then
                    v5 = 0
                end
                wait(2)
            end
        end
    end
    layerPosition((layerName.dlg + 2), 184, (139 + (23 * v0)), 5)
    switchScreen(0, "", 0)
    wait(1)
    layerAlpha((layerName.dlg + 2), 0)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 100)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 0)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 100)
    switchScreen(0, "", 0)
    wait(5)
    layerLoad(layerName.dlg, "")
    layerLoad((layerName.dlg + 1), "")
    layerLoad((layerName.dlg + 2), "")
    layerLoad((layerName.dlg + 3), "")
    switchScreen(0, "", 10)
    v7 = false
    if v0 == 0 then
        v7 = true
    end
    return v7
end
comDlgStorylineSkip = function(p0, ...)
    local v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15
    if gameSave.myCard[sceneId2aCard[p0]].hold == -1 then
        advPart(true)
        logEnable(true)
        v0 = false
        return v0
    end
    if systemSave.storyLineSkip == 2 then
        advPart(true)
        logEnable(true)
        v1 = false
        return v1
    end
    logEnable(false)
    advPart(false)
    v5 = cGetFileName("card", "crd_" .. sceneId2aCard[p0] .. "_a")
    v6 = true
    v2 = select("#", ...)
    if 0 < v2 then
        v6 = false
        cLoadPlaySE(cGetFileName("se", "se_101"), false)
        wait(1)
        layerLoad(layerName.dlg, select(1, ...))
        layerAlpha(layerName.dlg, 80)
        switchScreen(0, "", 60)
        wait(60)
    else
        layerCopy(layerName.dlg, layerName.effectBlack)
        layerAlpha(layerName.dlg, 40)
    end
    layerCopy((layerName.dlg + 1), layerName.sys_13_a)
    layerCopy((layerName.dlg + 2), layerName.sys_13_b)
    layerPosition((layerName.dlg + 2), 296, 142)
    layerCopy((layerName.dlg + 3), layerName.sys_13_c)
    layerPosition((layerName.dlg + 3), 327, 145)
    layerCopy((layerName.dlg + 4), layerName.sys_13_d)
    layerPosition((layerName.dlg + 4), 51, 246)
    layerClip((layerName.dlg + 4), 0, 0, 377, 18)
    layerLoad((layerName.dlg + 5), v5)
    layerPosition((layerName.dlg + 5), 15, 40)
    layerAlpha((layerName.dlg + 5), 0)
    layerMovePosition((layerName.dlg + 5), 15, 70, 10)
    layerMoveAlpha((layerName.dlg + 5), 100, 10)
    wait(10)
    v2 = 0
    v3 = false
    v4 = 1
    v7 = 1
    v8 = 1
    v9 = 1
    v10 = 1
    v11 = 0
    while true do
        v12 = pressButton("UP")
        if (v12 == true) and (v3 == false) and (v4 == 0) then
            v12 = v2 - 1
            if v12 < 0 then
                v2 = 1
            else
                v2 = v2 - 1
            end
            v3 = true
        end
        v12 = pressButton("UP")
        if v12 == false then
            v4 = 0
        end
        v12 = pressButton("DOWN")
        if (v12 == true) and (v3 == false) and (v7 == 0) then
            v12 = v2 + 1
            if 1 < v12 then
                v2 = 0
            else
                v2 = v2 + 1
            end
            v3 = true
        end
        v12 = pressButton("DOWN")
        if v12 == false then
            v7 = 0
        end
        v12 = pressButton("CIRCLE")
        if (v12 == true) and (v3 == false) and (v8 == 0) then
            keyPlaySE(seName.circle)
            break
        else
            v12 = pressButton("CIRCLE")
            if v12 == false then
                v8 = 0
            end
            if systemSave.storyLineSkip == 1 then
                keyPlaySE(seName.circle)
                break
            else
                v12 = pressButton("CROSS")
                if (v12 == true) and (v3 == false) and (v9 == 0) then
                    keyPlaySE(seName.cross)
                    v2 = 1
                    break
                else
                    v12 = pressButton("CROSS")
                    if v12 == false then
                        v9 = 0
                    end
                    if v3 == true then
                        keyPlaySE(seName.arrowKey)
                        layerMovePosition((layerName.dlg + 2), 296, (142 + (23 * v2)), 5)
                        layerClip((layerName.dlg + 4), 0, (18 * v2), 377, (18 + (18 * v2)))
                        wait(5)
                        v3 = false
                    end
                    v11 = v11 + 1
                    if 12 < v11 then
                        v8 = 0
                        v9 = 0
                        v10 = 0
                    end
                    wait(2)
                end
            end
        end
    end
    layerPosition((layerName.dlg + 2), 296, (142 + (23 * v2)), 5)
    switchScreen(0, "", 0)
    wait(1)
    layerAlpha((layerName.dlg + 2), 0)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 100)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 0)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 100)
    switchScreen(0, "", 0)
    wait(5)
    layerLoad(layerName.dlg, "")
    layerLoad((layerName.dlg + 1), "")
    layerLoad((layerName.dlg + 2), "")
    layerLoad((layerName.dlg + 3), "")
    layerLoad((layerName.dlg + 4), "")
    layerLoad((layerName.dlg + 5), "")
    if v6 == false then
        switchScreen(0, "", 60)
        wait(60)
    else
        switchScreen(0, "", 10)
        wait(10)
    end
    advPart(true)
    logEnable(true)
    v12 = false
    if v2 == 0 then
        v12 = true
    end
    return v12
end
comDlgSelectItem = function(p0, p1, p2, p3, p4, p5, p6, p7, ...)
    local v0, v1, v2, v3, v4, v5, i12, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17
    advPart(false)
    v0 = function(p0, p1)
        local v0, v1, v2, v3
        if p1 == true then
            return cGetFileName("select", p0 .. "_on")
        else
            v0 = "select"
            return cGetFileName(v0, p0 .. "_off")
        end
    end
    v1 = {}
    v2 = 0
    v3 = select("#", ...)
    if 0 < v3 then
        v3 = select("#", ...)
        v2 = v3 / 4
    end
    v3 = 1
    v4 = select("#", ...)
    v5 = 1
    for i12 = v3, v4, v5 do
        v6 = select(i12, ...)
        v1[i12] = v6
    end
    wait(5)
    if p1 == true then
        layerCopy(layerName.dlg, layerName.effectBlack)
        layerAlpha(layerName.dlg, 40)
    end
    if not (p5 == "none") then
        layerLoad((layerName.dlg + 1), p5)
        layerPosition((layerName.dlg + 1), p6, p7)
    end
    if 0 < v2 then
        v3 = v0(v1[1], true)
        v4 = v0(v1[1], false)
        layerLoad((layerName.dlg + 2), v3)
        layerPosition((layerName.dlg + 2), v1[2], v1[3])
        layerVisible((layerName.dlg + 2), true)
        i12 = layerName.dlg + 3
        v6 = v4
        layerLoad(i12, v6)
        layerPosition((layerName.dlg + 3), v1[2], v1[3])
        layerVisible((layerName.dlg + 3), false)
    end
    v3 = 4
    v4 = 2
    v5 = v2
    i12 = 1
    for v6 = v4, v5, i12 do
        v8 = ((v6 - 1) * 4) + 1
        v7 = v0(v1[v8], true)
        v9 = ((v6 - 1) * 4) + 1
        v8 = v0(v1[v9], false)
        layerLoad((layerName.dlg + v3), v7)
        v10 = layerName.dlg + v3
        v11 = ((v6 - 1) * 4) + 2
        v12 = ((v6 - 1) * 4) + 3
        layerPosition(v10, v1[v11], v1[v12])
        layerVisible((layerName.dlg + v3), false)
        v3 = v3 + 1
        layerLoad((layerName.dlg + v3), v8)
        v10 = layerName.dlg + v3
        v11 = ((v6 - 1) * 4) + 2
        v12 = ((v6 - 1) * 4) + 3
        layerPosition(v10, v1[v11], v1[v12])
        layerVisible((layerName.dlg + v3), true)
        v3 = v3 + 1
    end
    if (p2 == true) and (0 < v2) then
        layerLoad(layerName.dlgCursor, cGetFileName("sysgim", "sys_9_a"))
        layerPosition(layerName.dlgCursor, (v1[2] - 16), v1[3])
    end
    v4 = 1
    v5 = 1
    i12 = 1
    v6 = 1
    v7 = 0
    v8 = 1
    v9 = 1
    v10 = 1
    v11 = 1
    while v7 < 1 do
        if -1 < p4 then
            v8 = p4
            if v8 < 1 then
                v8 = 1
            end
            if v2 < v8 then
                v8 = v2
            end
            p4 = -1
        end
        v12 = pressButton("UP")
        if v12 == true then
            if v4 == 0 then
                v8 = v8 - 1
                if p3 == true then
                    stopSE(seName.arrowKey)
                end
                if v8 < 1 then
                    v8 = v2
                    if p3 == true then
                        playSE(seName.arrowKey, false)
                    end
                elseif p3 == true then
                    playSE(seName.arrowKey, false)
                end
                if p2 == true then
                    v13 = v1[(((v8 - 1) * 4) + 2)] - 16
                    v14 = ((v8 - 1) * 4) + 3
                    layerMovePosition(layerName.dlgCursor, v13, v1[v14], 12)
                end
                v4 = 1
                v9 = 1
            end
        else
            v4 = 0
        end
        v12 = pressButton("DOWN")
        if v12 == true then
            if v5 == 0 then
                v8 = v8 + 1
                if p3 == true then
                    stopSE(seName.arrowKey)
                end
                if v2 < v8 then
                    v8 = 1
                    if p3 == true then
                        playSE(seName.arrowKey, false)
                    end
                elseif p3 == true then
                    playSE(seName.arrowKey, false)
                end
                if p2 == true then
                    v13 = v1[(((v8 - 1) * 4) + 2)] - 16
                    v14 = ((v8 - 1) * 4) + 3
                    layerMovePosition(layerName.dlgCursor, v13, v1[v14], 12)
                end
                v5 = 1
                v9 = 1
            end
        else
            v5 = 0
        end
        if v9 == 1 then
            v12 = 1
            v15 = v2
            v13 = 1
            for v14 = v12, v15, v13 do
                if v8 == v14 then
                    v16 = layerName.dlg + 2
                    v17 = (v14 - 1) * 2
                    layerVisible((v16 + v17), true)
                    v16 = layerName.dlg + 3
                    v17 = (v14 - 1) * 2
                    layerVisible((v16 + v17), false)
                else
                    v16 = layerName.dlg + 2
                    v17 = (v14 - 1) * 2
                    layerVisible((v16 + v17), false)
                    v16 = layerName.dlg + 3
                    v17 = (v14 - 1) * 2
                    layerVisible((v16 + v17), true)
                end
            end
            v9 = 0
        end
        v12 = pressButton("CIRCLE")
        if v12 == true then
            if (i12 == 0) and (0 < v2) then
                if p3 == true then
                    playSE(seName.circle, false)
                end
                v7 = 1
            end
        else
            i12 = 0
        end
        if p0 == true then
            v12 = pressButton("CROSS")
            if v12 == true then
                if v6 == 0 then
                    v7 = 1
                    v8 = -1
                end
            else
                v6 = 0
            end
        end
        wait(2)
    end
    if p2 == true then
        layerMoveAlpha(layerName.dlgCursor, 0, 30)
    end
    v12 = 1
    v15 = v2
    v13 = 1
    for v14 = v12, v15, v13 do
        if not (v8 == v14) then
            v16 = layerName.dlg + 2
            v17 = (v14 - 1) * 2
            layerMoveAlpha((v16 + v17), 0, 30)
            v16 = layerName.dlg + 3
            v17 = (v14 - 1) * 2
            layerMoveAlpha((v16 + v17), 0, 30)
            v16 = layerName.dlg + 2
            v17 = (v14 - 1) * 2
            layerMoveScale((v16 + v17), 100, 0, 20)
            v16 = layerName.dlg + 3
            v17 = (v14 - 1) * 2
            layerMoveScale((v16 + v17), 100, 0, 20)
        end
    end
    wait(30)
    layerLoad(layerName.dlg, "")
    layerLoad((layerName.dlg + 1), "")
    v12 = 1
    v15 = v2
    v13 = 1
    for v14 = v12, v15, v13 do
        v16 = layerName.dlg + 2
        v17 = (v14 - 1) * 2
        layerLoad((v16 + v17), "")
        v16 = layerName.dlg + 3
        v17 = (v14 - 1) * 2
        layerLoad((v16 + v17), "")
    end
    if p2 == true then
        layerLoad(layerName.dlgCursor, "")
    end
    switchScreen(0, "", 10)
    wait(30)
    if p3 == true then
        stopSE(3)
        stopSE(4)
    end
    advPart(true)
    v12 = 0
    if v8 == -1 then
        v12 = -1
    else
        v15 = ((v8 - 1) * 4) + 4
        v12 = v1[v15]
    end
    return v12
end
comClearLayer = function()
    layerLoad(layerName.bg1, "")
    layerLoad(layerName.bg2, "")
    layerLoad(layerName.bg3, "")
    layerLoad(layerName.bg4, "")
    layerLoad(layerName.bg5, "")
    layerLoad(layerName.pose1, "")
    layerLoad(layerName.pose2, "")
    layerLoad(layerName.pose3, "")
    layerLoad(layerName.pose4, "")
    layerLoad(layerName.pose5, "")
end
comEffectWhiteIn = function(p0)
    layerCopy(layerName.swap, layerName.effectWhite)
    layerBlend(layerName.swap, "ADD")
    layerMoveAlpha(layerName.swap, 0, p0)
end
comEffectWhiteOut = function(p0)
    wait(1)
    comClearLayer()
    layerCopy(layerName.event, layerName.effectWhite)
    switchScreen(0, "", p0)
end
comEffectFadeIn = function(p0)
    layerCopy(layerName.swap, layerName.effectBlack)
    layerMoveAlpha(layerName.swap, 0, p0)
end
comEffectFadeOut = function(p0)
    wait(1)
    comClearLayer()
    layerCopy(0, layerName.effectBlack)
    switchScreen(0, "", p0)
    wait(p0)
end
comEffectYellowIn = function(p0)
    layerCopy(layerName.swap, layerName.effectYellow)
    layerBlend(layerName.swap, "ADD")
    layerMoveAlpha(layerName.swap, 0, p0)
end
comEffectBlackoutAndIn = function(p0, ...)
    local v0 = 120
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    wait(1)
    layerCopy(layerName.swap, layerName.effectBlack)
    switchScreen(0, "", v0)
    wait(p0)
    layerLoad(layerName.swap, "")
    switchScreen(0, "", v0)
end
comPoseLoad = function(p0, ...)
    local v0 = 30
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    wait(1)
    layerLoad(layerName.pose1, cGetFileName("pose", p0))
    switchScreen(0, "", v0)
    wait(15)
end
comPoseLoadSec3 = function(p0, ...)
    local v0 = 30
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    wait(1)
    layerLoad(layerName.pose1, cGetFileName("pose", p0))
    layerPosition(layerName.pose1, 0, 20)
    switchScreen(0, "", v0)
    wait(15)
end
comPoseDoubleLoad = function(p0, p1, ...)
    local v0 = 30
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    wait(1)
    layerLoad(p0, cGetFileName("pose", p1))
    comPoseInitPosition(2)
    switchScreen(0, "", v0)
    wait(15)
end
comPoseDelete = function(...)
    local v0 = 30
    local v1, v2
    v1 = select("#", ...)
    if 0 < v1 then
        v0 = select(1, ...)
    end
    wait(1)
    layerLoad(layerName.pose1, "")
    layerLoad(layerName.pose2, "")
    switchScreen(0, "", v0)
end
comPoseInitPosition = function(p0)
    if p0 == 2 then
        layerPosition(layerName.pose1, 80, 0)
        layerPosition(layerName.pose2, -100, 0)
    end
end
comPoseMoveResetPosition = function(p0, p1)
    local v0
    if p0 == 2 then
        layerMovePosition(layerName.pose1, 80, 0, p1)
        layerMovePosition(layerName.pose2, -100, 0, p1)
        wait(p1)
    end
end
comPoseMoveLeave = function(p0, p1, p2)
    local v0, v1
    if p0 == 2 then
        if p1 == layerName.pose1 then
            layerMovePosition(layerName.pose1, 100, 10, p2)
            wait(p2)
            layerMovePosition(layerName.pose1, 100, 0, p2)
            wait(p2)
        end
        if p1 == layerName.pose2 then
            layerMovePosition(layerName.pose2, -40, 10, p2)
            wait(p2)
            layerMovePosition(layerName.pose2, -40, 0, p2)
            wait(p2)
        end
    end
end
comPoseMoveApproach = function(p0, p1, p2)
    local v0, v1
    if p0 == 2 then
        if p1 == layerName.pose1 then
            layerMovePosition(layerName.pose1, 60, 10, p2)
            wait(p2)
            layerMovePosition(layerName.pose1, 60, 0, p2)
            wait(p2)
        end
        if p1 == layerName.pose2 then
            layerMovePosition(layerName.pose2, -80, 10, p2)
            wait(p2)
            layerMovePosition(layerName.pose2, -80, 0, p2)
            wait(p2)
        end
    end
end
comPoseMoveApproach2 = function(p0, p1, p2, p3)
    local v0, v1
    if p0 == 2 then
        if p1 == layerName.pose1 then
            layerMovePosition(layerName.pose1, 30, 0, p2)
            layerMovePosition(layerName.pose2, -110, 0, p2)
            wait(p2)
            layerMovePosition(layerName.pose1, 40, 0, p3)
            layerMovePosition(layerName.pose2, -100, 0, p3)
            wait(p3)
        end
        if p1 == layerName.pose2 then
            layerMovePosition(layerName.pose1, 90, 0, p2)
            layerMovePosition(layerName.pose2, -50, 0, p2)
            wait(p2)
            layerMovePosition(layerName.pose1, 80, 0, p3)
            layerMovePosition(layerName.pose2, -60, 0, p3)
            wait(p3)
        end
    end
end
comPoseMoveLeftRight = function(p0, p1, p2)
    local v0, v1, v2, i3, v3, v4
    if p0 == 2 then
        if p1 == layerName.pose1 then
            v0 = 0
            v1 = 2
            v2 = 1
            for i3 = v0, v1, v2 do
                layerMovePosition(layerName.pose1, 70, 0, p2)
                wait(p2)
                layerMovePosition(layerName.pose1, 80, 0, p2)
                wait(p2)
            end
        end
        if p1 == layerName.pose2 then
            v0 = 0
            v1 = 2
            v2 = 1
            for i3 = v0, v1, v2 do
                layerMovePosition(layerName.pose2, -110, 0, p2)
                wait(p2)
                layerMovePosition(layerName.pose2, -100, 0, p2)
                wait(p2)
            end
        end
    end
end
comSectionStoryStart = function(p0, p1, p2)
    local v0, v1, v2, v3, v4, v5
    layerCopy(layerName.scene, sceneState[sceneId2aCard[p0]].layerName)
    v0 = (sceneState[sceneId2aCard[p0]].clipX) + 145
    v1 = (sceneState[sceneId2aCard[p0]].clipY) + 15
    layerClip(layerName.scene, sceneState[sceneId2aCard[p0]].clipX, sceneState[sceneId2aCard[p0]].clipY, v0, v1)
    layerPosition(layerName.scene, 330, 5)
    v2, v3 = oHour.setHourGlassCount2FileName(p2)
    layerCopy(layerName.hour1, layerName.sys_4_a)
    layerClip(layerName.hour1, v2, v3, (v2 + 60), (v3 + 60))
    layerPosition(layerName.hour1, 5, 5)
    layerAnime(layerName.hour1, 4, true)
    switchScreen(0, "", 5)
    wait(5)
    systemConfig.setConfigButton()
end
comSectionStoryEnd = function(p0, p1, p2)
    comSectionStoryAddRoute(p0)
    comSectionStoryChkAyanoTime(p0, p2)
end
comSectionStoryEndForce = function(p0, p1, p2)
    comSectionStoryAddRoute(p0)
    comSectionStoryChkAyanoTimeForce(p0, p2)
end
comSectionStoryAddRoute = function(p0)
    local v0 = 1
    local v1 = storyRouteMax
    local v2 = 1
    local i1
    for i1 = v0, v1, v2 do
        if gameSave.storyRoute[i1].sceneId == -1 then
            gameSave.storyRoute[i1].sceneId = p0
            gameSave.storyRoute[i1].ayanoTime = gameSave.ayanoTime
            break
        elseif i1 == 90 then
            oCom.debagvms(3, "NONVOICE", "★エラーです。記憶ルートが９０を超えました。Story配列を増加させることを検討してください。")
        end
    end
end
comSectionStoryCheckRoute = function(p0)
    local v0 = false
    local v1 = 1
    local v2 = storyRouteMax
    local v3 = 1
    local i2
    for i2 = v1, v2, v3 do
        if gameSave.storyRoute[i2].sceneId == p0 then
            v0 = true
            break
        end
    end
    return v0
end
comSectionStoryShowRoute = function()
    local v0 = 1
    local v1 = storyRouteMax
    local v2 = 1
    local i0, v3, v4, v5
    for i0 = v0, v1, v2 do
        if not (gameSave.storyRoute[i0].sceneId == -1) then
            oCom.debagvms(4, "NONVOICE", i0 .. "_rsceneId：" .. gameSave.storyRoute[i0].sceneId)
            oCom.debagvms(5, "NONVOICE", i0 .. "_rayanoTime：" .. gameSave.storyRoute[i0].ayanoTime)
        end
    end
end
comSectionStoryChkAyanoTime = function(p0, p1)
    local v0
    if gameSave.myCard[sceneId2aCard[p0]].hold == -1 then
        v0 = gameSave.ayanoTime + p1
        gameSave.ayanoTime = v0
        if 100 <= gameSave.ayanoTime then
            comSectionStoryEndAyanoTime("normal")
        end
    end
end
comSectionStoryChkAyanoTimeForce = function(p0, p1)
    local v0
    v0 = gameSave.ayanoTime + p1
    gameSave.ayanoTime = v0
    if 100 <= gameSave.ayanoTime then
        comSectionStoryEndAyanoTime("force")
    end
end
comStorySceneEnd = function(p0)
    local v0, v1, v2, v3, v4, v5, v6, v7, v8, v9
    advPart(false)
    if p0 == 0 then
        layerCopy(layerName.dlg, layerName.sys_12_a)
    elseif p0 == 1 then
        layerCopy(layerName.dlg, layerName.sys_12_b)
    else
        layerCopy(layerName.dlg, layerName.sys_12_c)
    end
    layerCopy((layerName.dlg + 1), layerName.sys_12_d)
    layerCopy((layerName.dlg + 2), layerName.sys_12_e)
    layerPosition((layerName.dlg + 2), 161, 87)
    layerCopy((layerName.dlg + 3), layerName.sys_12_f)
    layerPosition((layerName.dlg + 3), 180, 90)
    layerCopy((layerName.dlg + 4), layerName.sys_12_g)
    layerPosition((layerName.dlg + 4), 140, 246)
    layerClip((layerName.dlg + 4), 0, 0, 201, 18)
    switchScreen(0, "", 30)
    v1 = 1
    v0 = false
    v2 = 1
    v3 = 1
    v4 = 1
    v5 = 1
    while true do
        v6 = pressButton("UP")
        if (v6 == true) and (v0 == false) and (v2 == 0) then
            v6 = v1 - 1
            if v6 < 1 then
                v1 = 3
            else
                v1 = v1 - 1
            end
            v0 = true
        end
        v6 = pressButton("UP")
        if v6 == false then
            v2 = 0
        end
        v6 = pressButton("DOWN")
        if (v6 == true) and (v0 == false) and (v3 == 0) then
            v6 = v1 + 1
            if 3 < v6 then
                v1 = 1
            else
                v1 = v1 + 1
            end
            v0 = true
        end
        v6 = pressButton("DOWN")
        if v6 == false then
            v3 = 0
        end
        v6 = pressButton("CIRCLE")
        if (v6 == true) and (v0 == false) and (v4 == 0) then
            keyPlaySE(seName.circle)
            wait(5)
            break
        else
            v6 = pressButton("CIRCLE")
            if v6 == false then
                v4 = 0
            end
            v6 = pressButton("CROSS")
            if (v6 == true) and (v0 == false) and (v5 == 0) then
                keyPlaySE(seName.cross)
                wait(5)
                v1 = 1
                break
            else
                v6 = pressButton("CROSS")
                if v6 == false then
                    v5 = 0
                end
                if v0 == true then
                    keyPlaySE(seName.arrowKey)
                    v7 = layerName.dlg + 2
                    v8 = (v1 - 1) * 25
                    layerMovePosition(v7, 161, (87 + v8), 5)
                    v7 = layerName.dlg + 4
                    v8 = 18 * (v1 - 1)
                    v9 = 18 * (v1 - 1)
                    layerClip(v7, 0, v8, 201, (18 + v9))
                    wait(5)
                    v0 = false
                end
                wait(2)
            end
        end
    end
    v7 = layerName.dlg + 2
    v8 = (v1 - 1) * 25
    layerPosition(v7, 161, (87 + v8), 5)
    switchScreen(0, "", 0)
    wait(1)
    layerAlpha((layerName.dlg + 2), 0)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 100)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 0)
    switchScreen(0, "", 0)
    wait(5)
    layerAlpha((layerName.dlg + 2), 100)
    switchScreen(0, "", 0)
    wait(5)
    cInitGame()
    switchScreen(0, "", 30)
    wait(30)
    return v1
end
comSectionStoryEndAyanoTime = function(p0)
    local v0, v1, v2, v3, v4, v5
    cStopBGMWrap()
    v0, v1 = oHour.setHourGlassCount2FileName(100)
    layerClip(layerName.hour1, v0, v1, (v0 + 60), (v1 + 60))
    layerPosition(layerName.hour1, 5, 5)
    layerAnime(layerName.hour1, 4, true)
    switchScreen(0, "", 10)
    if p0 == "normal" then
        cPlayOneshotMusic(cGetFileName("mus", "mus_16"))
        comEffectWhiteOut(120)
        layerCopy(layerName.bg1, layerName.bg_1_a_0)
        layerCopy(layerName.pose1, layerName.po1_aya_f_1_a)
        comEffectWhiteIn(180)
        wait(180)
        cPlayBGMWrap(cGetFileName("bgm", "bgm_8_x"))
        vms(6, "NONVOICE", "そこまで彩野さんが『物語』を話した時だった。")
        vms(7, "NONVOICE", "彩野さんは小さくため息をつくと、そっと目をつむった。")
        vms(8, "NONVOICE", "胸に手を当て、息を吸い込む。")
        vms(9, "NONVOICE", "やがて目を開いた彼女は、まるでなにかとても眩しいものでも眺めるように、あたりを見渡していた。")
        cStopBGMWrap()
        comEffectFadeOut(100)
        vms(10, "NONVOICE", "彩野さんから「記憶」が途絶えてしまったようだ。")
        fontClear()
        layerLoad(layerName.hour1, "")
        layerLoad(layerName.scene, "")
        layerLoad(layerName.sceneType, "")
        layerLoad(layerName.reading, "")
        switchScreen(0, "", 30)
        vms(11, "NONVOICE", "物語の続きを聞くには、新しい『あらすじ』を作成する必要があるかもしれない。")
        vms(12, "NONVOICE", "■Ｔｉｍｅ ｏｖｅｒ")
    end
    if p0 == "force" then
        cPlayOneshotMusic(cGetFileName("mus", "mus_16"))
        comEffectWhiteOut(120)
        layerCopy(layerName.bg1, layerName.bg_1_a_0)
        layerLoad(layerName.pose1, cGetFileName("pose", "po1_aya_f_2_e"))
        comEffectWhiteIn(180)
        wait(180)
        cPlayBGMWrap(cGetFileName("bgm", "bgm_8_x"))
        vms(13, "NONVOICE", "彩野さんは小さくため息をつくと、そっと目をつむった。")
        vms(14, "NONVOICE", "胸に手を当て、息を吸い込む。")
        vms(15, "NONVOICE", "やがて目を開いた彼女は、まるでなにかとても眩しいものでも眺めるように、あたりを見渡していた。")
        cStopBGMWrap()
        comEffectFadeOut(100)
        vms(16, "NONVOICE", "彩野さんから「記憶」が途絶えてしまったようだ。")
        fontClear()
        layerLoad(layerName.hour1, "")
        layerLoad(layerName.scene, "")
        layerLoad(layerName.sceneType, "")
        layerLoad(layerName.reading, "")
        switchScreen(0, "", 30)
        vms(17, "NONVOICE", "物語の続きを聞くには、正しい『日記』を選択する必要がある。")
        vms(18, "NONVOICE", "■Ｔｉｍｅ ｏｖｅｒ")
    end
    v4 = comStorySceneEnd(1)
    if v4 == 1 then
        cInitGame()
        run(cGetFileName("script", "snr_story_main"))
        quit()
    end
    if v4 == 2 then
        comSectionFragmentItemInit()
        cInitGame()
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if v4 == 3 then
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
    if v4 == -1 then
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
end
comSectionGameOver = function()
    local v0, v1
    cStopBGMWrap()
    comEffectWhiteOut(120)
    fontClear()
    layerLoad(layerName.hour1, "")
    layerLoad(layerName.scene, "")
    layerLoad(layerName.sceneType, "")
    layerLoad(layerName.reading, "")
    switchScreen(0, "", 30)
    v0 = comStorySceneEnd(0)
    if v0 == 1 then
        cInitGame()
        run(cGetFileName("script", "snr_story_main"))
        quit()
    end
    if v0 == 2 then
        comSectionFragmentItemInit()
        cInitGame()
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if v0 == 3 then
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
    if v0 == -1 then
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
end
comSectionComplete = function()
    local v0, v1
    cStopBGMWrap()
    comEffectWhiteOut(120)
    fontClear()
    layerLoad(layerName.hour1, "")
    layerLoad(layerName.scene, "")
    layerLoad(layerName.sceneType, "")
    layerLoad(layerName.reading, "")
    switchScreen(0, "", 30)
    v0 = comStorySceneEnd(2)
    if v0 == 1 then
        cInitGame()
        run(cGetFileName("script", "snr_story_main"))
        quit()
    end
    if v0 == 2 then
        comSectionFragmentItemInit()
        cInitGame()
        run(cGetFileName("script", "snr_fragment_main"))
        quit()
    end
    if v0 == 3 then
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
    if v0 == -1 then
        cInitGame()
        run(cGetFileName("script", "snr_mainmenu"))
        quit()
    end
end
comSectionStoryGetCount = function()
    local v0 = 0
    local v1 = 1
    local v2 = storyRouteMax
    local v3 = 1
    local i1
    for i1 = v1, v2, v3 do
        if gameSave.storyRoute[i1].sceneId == -1 then
            break
        end
        v0 = v0 + 1
    end
    return v0
end
comSectionUID2ScriptFileName = function(p0)
    local v0, v1, v2, v3
    v0 = string.sub(p0, 1, 2)
    v1 = string.sub(p0, 3, 3)
    v2 = "snr_" .. v0 .. "_10_" .. v1
    return v2
end
comSectionStoryBegin = function(p0, p1)
    local v0, v1, v2
    gameSave.sceneName = p1
    gameSave.sceneId = p0
    v0 = string.sub(p0, 1, 2)
    v1 = ""
    if v0 == "s1" then
        v1 = "セクション１／ストーリー"
    elseif v0 == "s2" then
        v1 = "セクション２／ストーリー"
    elseif v0 == "s3" then
        v1 = "セクション３／ストーリー"
    elseif v0 == "s4" then
        v1 = "セクション４／ストーリー"
    elseif v0 == "s5" then
        v1 = "セクション５／ストーリー"
    elseif v0 == "s6" then
        v1 = "セクション６／ストーリー"
    elseif v0 == "s7" then
        v1 = "セクション７／ストーリー"
    elseif v0 == "s8" then
        v1 = "セクション８／ストーリー"
    elseif v0 == "e1" then
        v1 = "セクションEX１／ストーリー"
    elseif v0 == "e2" then
        v1 = "セクションEX２／ストーリー"
    end
    savedataTitle(p1, v1)
    comSectionStoryStart(gameSave.sceneId, gameSave.sceneName, gameSave.ayanoTime)
    v2 = advIsPart()
    if v2 == false then
        advPart(true)
    end
    logEnable(true)
    systemConfig.setConfigButton()
end
comSectionNonLabelBegin = function(p0, p1)
    local v0, v1, v2
    gameSave.sceneName = p1
    gameSave.sceneId = p0
    v0 = string.sub(p0, 1, 4)
    v1 = ""
    if v0 == "sof_" then
        v1 = "プロローグ"
    elseif v0 == "s1f-" then
        v1 = "セクション１／フラグメント"
    elseif v0 == "s2f-" then
        v1 = "セクション２／フラグメント"
    elseif v0 == "s3fa" then
        v1 = "セクション３A／フラグメント"
    elseif v0 == "s3fb" then
        v1 = "セクション３B／フラグメント"
    elseif v0 == "s3fc" then
        v1 = "セクション３C／フラグメント"
    elseif v0 == "s4fa" then
        v1 = "セクション４A／フラグメント"
    elseif v0 == "s4fb" then
        v1 = "セクション４B／フラグメント"
    elseif v0 == "s5f-" then
        v1 = "セクション５／フラグメント"
    elseif v0 == "s6f-" then
        v1 = "セクション６／フラグメント"
    elseif v0 == "s7f-" then
        v1 = "セクション７／フラグメント"
    elseif v0 == "s8f-" then
        v1 = "セクション８／フラグメント"
    elseif v0 == "e1f-" then
        v1 = "セクションEX１／フラグメント"
    elseif v0 == "e2f-" then
        v1 = "セクションEX２／フラグメント"
    end
    savedataTitle(p1, v1)
    v2 = advIsPart()
    if v2 == false then
        advPart(true)
    end
    logEnable(true)
    systemConfig.setConfigButton()
end
comSectionCardStart = function(p0, p1)
    local v0, v1, v2, v3, v4, i4, v5, v6
    v0 = string.sub(p0, 1, 2)
    v1 = ""
    if v0 == "s1" then
        v1 = "セクション１／フラグメント"
    elseif v0 == "s2" then
        v1 = "セクション２／フラグメント"
    elseif v0 == "s3" then
        v1 = "セクション３／フラグメント"
    elseif v0 == "s4" then
        v1 = "セクション４／フラグメント"
    elseif v0 == "s5" then
        v1 = "セクション５／フラグメント"
    elseif v0 == "s6" then
        v1 = "セクション６／フラグメント"
    elseif v0 == "s7" then
        v1 = "セクション７／フラグメント"
    elseif v0 == "s8" then
        v1 = "セクション８／フラグメント"
    elseif v0 == "e1" then
        v1 = "セクションEX１／フラグメント"
    elseif v0 == "e2" then
        v1 = "セクションEX２／フラグメント"
    end
    savedataTitle(string.gsub(plotTitle[p1], "\n", ""), v1)
    v3 = 1
    v2 = 199
    v4 = 1
    for i4 = v3, v2, v4 do
        layerLoad(i4, "")
    end
    cInitBgm()
    cInitSe()
    oCard.cursorPositionInit()
    wait(1)
    layerCopy(layerName.bg1, layerName.bg_1_a_0)
    layerCopy(layerName.scene, sceneState[p1].layerName)
    layerCopy(layerName.scene, sceneState[p1].layerName)
    layerClip(layerName.scene, sceneState[p1].clipX, sceneState[p1].clipY, (sceneState[p1].clipX + 145), (sceneState[p1].clipY + 15))
    layerPosition(layerName.scene, 330, 5)
    switchScreen(0, "", 30)
    systemConfig.setConfigButton()
    v3 = advIsPart()
    if v3 == false then
        advPart(true)
    end
    logEnable(true)
end
comSectionCardEnd = function(p0, p1)
    local v0, v1, v2, i2
    advPart(false)
    wait(1)
    v0 = 1
    v1 = 199
    v2 = 1
    for i2 = v0, v1, v2 do
        layerLoad(i2, "")
    end
    fontClear()
    cInitBgm()
    cInitSe()
    layerCopy(layerName.bg1, layerName.bg_1_a_0)
    switchScreen(0, "", 30)
    wait(30)
end
comSectionCardEndEvent = function()
    local v0
    advPart(false)
    cInitGame()
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end
comSectionCardEndSection = function()
    advPart(false)
    wait(1)
    comEffectFadeOut(120)
    wait(30)
    cInitGame()
end
comSectionCardFlagIn = function(p0, p1)
    local v0, v1, v2, v3
    if p1 == true then
        if not (gameSave.myCard[p0].hold == -1) then
            playSE(seName.cross, false)
            oCard.showMiniIn(cGetFileName("card", "crd_" .. p0 .. "_a"))
        end
    elseif gameSave.myCard[p0].hold == -1 then
        playSE(seName.cross, false)
        oCard.showMiniIn(cGetFileName("card", "crd_" .. p0 .. "_a"))
    end
end
comSectionCardFlagOut = function(p0, p1)
    if p1 == true then
        if not (gameSave.myCard[p0].hold == -1) then
            oCard.showMiniOut()
        end
    elseif gameSave.myCard[p0].hold == -1 then
        oCard.showMiniOut()
    end
end
comAyanoTimeRefresh = function()
    local v0, v1, v2, v3, v4, v5, i3, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15
    v0 = comSectionStoryGetCount()
    v1 = 0
    v2 = 0
    v3 = 1
    v4 = v0
    v5 = 1
    for i3 = v3, v4, v5 do
        if v1 == 1 then
            v6 = string.gsub((plotTitle[sceneId2aCard[gameSave.storyRoute[i3].sceneId]]), "\n", "")
            v7 = string.gsub((plotTitle[sceneId2aCard[gameSave.storyRoute[(i3 - 1)].sceneId]]), "\n", "")
            cStopBGMWrap()
            keyPlaySE(seName.viewCard)
            comEffectYellowIn(120)
            wait(120)
            v8 = gameSave.storyRoute[i3].sceneId
            layerCopy(layerName.pose1, sceneState[sceneId2aCard[v8]].layerName)
            v11 = (sceneState[sceneId2aCard[v8]].clipX) + 145
            v12 = (sceneState[sceneId2aCard[v8]].clipY) + 15
            layerClip(layerName.pose1, sceneState[sceneId2aCard[v8]].clipX, sceneState[sceneId2aCard[v8]].clipY, v11, v12)
            layerPosition(layerName.pose1, 168, 80)
            v9 = i3 - 1
            v10 = gameSave.storyRoute[v9].sceneId
            layerCopy(layerName.pose2, sceneState[sceneId2aCard[v10]].layerName)
            v12 = (sceneState[sceneId2aCard[v10]].clipX) + 145
            v13 = (sceneState[sceneId2aCard[v10]].clipY) + 15
            layerClip(layerName.pose2, sceneState[sceneId2aCard[v10]].clipX, sceneState[sceneId2aCard[v10]].clipY, v12, v13)
            layerPosition(layerName.pose2, 168, 80)
            vms(21, "NONVOICE", "彩野に対して『あらすじ』で物語を説明できるようになりました。")
            wait(1)
            layerMovePosition(layerName.pose1, 168, 130, 60)
            layerMovePosition(layerName.pose2, 168, 30, 60)
            switchScreen(0, "", 60)
            wait(60)
            layerLoad(layerName.pose3, cGetFileName("sysgim", "sys_1_i"))
            layerPosition(layerName.pose3, 143, 50)
            switchScreen(0, "", 60)
            wait(60)
            vms(22, "NONVOICE", "これにより、ストーリーモードで『" .. v7 .. "』を読むときに経過していた時間を短縮できるようになりました。")
            wait(1)
            keyPlaySE(seName.viewCard)
            layerLoad(layerName.pose1, "")
            layerLoad(layerName.pose2, "")
            layerLoad(layerName.pose3, "")
            comEffectYellowIn(60)
            wait(60)
            v9 = gameSave.storyRoute[i3].ayanoTime
            v15 = i3 - 1
            v14 = gameSave.storyRoute[v15].ayanoTime
            v2 = v9 - v14
            v1 = 2
        end
        if v1 == 2 then
            v6 = gameSave.storyRoute[i3].ayanoTime - v2
            if v6 < 0 then
                v6 = 0
            end
            gameSave.storyRoute[i3].ayanoTime = v6
        end
        v6 = gameSave.storyRoute[i3].sceneId
        if v6 == gameSave.fragmentDoSceneId then
            v1 = 1
        end
    end
end
comSectionFragmentItemInit = function()
    fragmentItemCount = 1
    fragmentCursorCount = 0
    fragmentCursorPage = 1
end
comSelectMap = function(p0, p1, p2, p3, ...)
    local v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, i13, v11, v12, v13, v14, v15, v16, v17, v18
    if not (p3) then
        p3 = ""
    end
    advPart(false)
    v0 = {}
    v0.art = 1
    v0.music = 2
    v0.health = 3
    v0.staffRoom = 4
    v0.court = 5
    v0.ground = 6
    v0.class = 7
    v0.roof = 8
    v0.corridor = 9
    v0.library = 10
    v1 = {}
    v1.art = 0
    v1.music = 52
    v1.health = 104
    v1.staffRoom = 156
    v1.court = 208
    v1.ground = 0
    v1.class = 52
    v1.roof = 104
    v1.corridor = 156
    v1.library = 208
    v2 = {}
    v2.art = 0
    v2.music = 0
    v2.health = 0
    v2.staffRoom = 0
    v2.court = 0
    v2.ground = 120
    v2.class = 120
    v2.roof = 120
    v2.corridor = 120
    v2.library = 120
    v3 = {}
    v4 = {}
    v5 = {}
    v5.bg = 0
    v5.chara = 1
    v5.info = 3
    v5.map = 4
    v6 = {}
    v7 = 0
    v8 = select("#", ...)
    if 0 < v8 then
        v8 = select("#", ...)
        v7 = v8 / 4
    end
    v8 = 1
    v9 = select("#", ...)
    v10 = 1
    for i13 = v8, v9, v10 do
        v11 = select(i13, ...)
        v6[i13] = v11
    end
    v8 = 0
    v9 = 15
    v10 = 1
    for i13 = v8, v9, v10 do
        layerLoad(i13, "")
    end
    layerLoad(v5.bg, p0)
    layerCopy(v5.info, layerName.sel_map_0_a)
    layerPosition(v5.info, 0, 230)
    if p1 == "YUI" then
        layerCopy(v5.chara, layerName.sel_map_2_a)
        if p2 == 1 then
            layerClip(v5.chara, 0, 0, 90, 92)
        else
            layerClip(v5.chara, 90, 0, 180, 92)
        end
    elseif p1 == "AYA" then
        layerCopy(v5.chara, layerName.sel_map_2_b)
        if p2 == 1 then
            layerClip(v5.chara, 0, 0, 80, 84)
        elseif p2 == 2 then
            layerClip(v5.chara, 80, 0, 160, 84)
        else
            layerClip(v5.chara, 160, 0, 240, 84)
        end
    end
    layerPosition(v5.chara, 180, 188)
    if not (p3 == "") then
        layerCopy(v5.map, layerName.sel_map_1_a)
        layerPosition(v5.map, 356, 246)
        i13 = v1[p3] + 26
        v11 = v2[p3] + 120
        v12 = v1[p3] + 52
        layerClip(v5.map, v2[p3], i13, v11, v12)
    else
        p3 = v6[1]
    end
    v8 = 1
    v9 = 1
    v10 = 1
    i13 = v7
    v11 = 1
    for v12 = v10, i13, v11 do
        layerCopy((v5.map + v12), layerName.sel_map_1_a)
        v13 = v5.map + v12
        v14 = ((v12 - 1) * 4) + 2
        v15 = ((v12 - 1) * 4) + 3
        layerPosition(v13, v6[v14], v6[v15])
        v16 = ((v12 - 1) * 4) + 1
        if v6[v16] == p3 then
            v13 = v5.map + v12
            v14 = ((v12 - 1) * 4) + 1
            v15 = ((v12 - 1) * 4) + 1
            v17 = (v2[v6[(((v12 - 1) * 4) + 1)]]) + 120
            v18 = (v1[v6[(((v12 - 1) * 4) + 1)]]) + 26
            layerClip(v13, v2[v6[v14]], v1[v6[v15]], v17, v18)
            v8 = v12
        else
            v13 = v5.map + v12
            v14 = ((v12 - 1) * 4) + 1
            v15 = (v1[v6[(((v12 - 1) * 4) + 1)]]) + 26
            v17 = (v2[v6[(((v12 - 1) * 4) + 1)]]) + 120
            v18 = (v1[v6[(((v12 - 1) * 4) + 1)]]) + 52
            layerClip(v13, v2[v6[v14]], v15, v17, v18)
        end
    end
    switchScreen(0, "", 60)
    v10 = false
    i13 = 1
    v11 = 1
    v12 = 1
    while true do
        if v10 == false then
            v16 = pressButton("CIRCLE")
            if v16 == true then
                if v12 == 0 then
                    keyPlaySE(seName.circle)
                    wait(5)
                    break
                end
            else
                v12 = 0
            end
            v16 = pressButton("UP")
            if v16 == true then
                if i13 == 0 then
                    v9 = v8
                    v16 = v8 - 1
                    if v16 < 1 then
                        if not (v7) then
                            v8 = v8 - 1
                        else
                            v8 = v7
                        end
                    else
                        v8 = v8 - 1
                    end
                    v10 = true
                end
            else
                i13 = 0
            end
            v16 = pressButton("DOWN")
            if v16 == true then
                if v11 == 0 then
                    v9 = v8
                    v16 = v8 + 1
                    if v7 < v16 then
                        v8 = 1
                    else
                        v8 = v8 + 1
                    end
                    v10 = true
                end
            else
                v11 = 0
            end
            v16 = pressButton("LEFT")
            v16 = pressButton("RIGHT")
        end
        if v10 == true then
            keyPlaySE(seName.arrowKey)
            v13 = v5.map + v8
            v14 = ((v8 - 1) * 4) + 1
            v15 = ((v8 - 1) * 4) + 1
            v17 = (v2[v6[(((v8 - 1) * 4) + 1)]]) + 120
            v18 = (v1[v6[(((v8 - 1) * 4) + 1)]]) + 26
            layerClip(v13, v2[v6[v14]], v1[v6[v15]], v17, v18)
            v13 = v5.map + v9
            v14 = ((v9 - 1) * 4) + 1
            v15 = (v1[v6[(((v9 - 1) * 4) + 1)]]) + 26
            v17 = (v2[v6[(((v9 - 1) * 4) + 1)]]) + 120
            v18 = (v1[v6[(((v9 - 1) * 4) + 1)]]) + 52
            layerClip(v13, v2[v6[v14]], v15, v17, v18)
            v10 = false
            wait(5)
        end
        wait(2)
    end
    v16 = 1
    v13 = v7
    v14 = 1
    for v15 = v16, v13, v14 do
        if not (v8 == v15) then
            layerMoveAlpha((v5.map + v15), 0, 30)
            layerMoveScale((v5.map + v15), 100, 0, 30)
        end
    end
    wait(30)
    v16 = 0
    v13 = 15
    v14 = 1
    for v15 = v16, v13, v14 do
        layerLoad(v15, "")
    end
    advPart(true)
    v16 = v6[(((v8 - 1) * 4) + 4)]
    return v16
end
comSectionMapmoveAyanoIn = function(p0)
    local v0
    v0 = math.random(1, 3)
    if p0 == "class" then
        if v0 == 1 then
            vms(27, "AYA00180", "【アヤノ】「教室に来たよ」")
        end
        if v0 == 2 then
            vms(28, "AYA00190", "【アヤノ】「私たちの教室だね」")
        end
        if v0 == 3 then
            vms(29, "AYA00200", "【アヤノ】「教室に戻ってきたよ」")
        end
    end
    if p0 == "corridor" then
        if v0 == 1 then
            vms(30, "AYA00210", "【アヤノ】「廊下に出たよ」")
        end
        if v0 == 2 then
            vms(31, "AYA00220", "【アヤノ】「放課後の廊下は静かだね」")
        end
        if v0 == 3 then
            vms(32, "AYA00230", "【アヤノ】「廊下。ここの窓からは中庭と屋上を見ることができるよ」")
        end
    end
    if p0 == "roof" then
        if v0 == 1 then
            vms(33, "AYA00240", "【アヤノ】「屋上。風が気持ちいいな」")
        end
        if v0 == 2 then
            vms(34, "AYA00250", "【アヤノ】「屋上に出たけど……だれもいないね」")
        end
        if v0 == 3 then
            vms(35, "AYA00260", "【アヤノ】「屋上についたよ。長くいると日焼けしちゃいそう」")
        end
    end
    if p0 == "court" then
        if v0 == 1 then
            vms(36, "AYA00270", "【アヤノ】「靴を履き替えて、中庭に出たよ」")
        end
        if v0 == 2 then
            vms(37, "AYA00280", "【アヤノ】「中庭。今日も暑いなあ」")
        end
        if v0 == 3 then
            vms(38, "AYA00290", "【アヤノ】「中庭だね。あっちの木の下の影に入れば涼しいかな？」")
        end
    end
    if p0 == "ground" then
        if v0 == 1 then
            vms(39, "AYA00300", "【アヤノ】「校庭に来たよ。北校舎と体育館、テニスコートとプールが見えるね」")
        end
        if v0 == 2 then
            vms(40, "AYA00310", "【アヤノ】「校庭に出たけど……やっぱりこの季節はあっついなあ」")
        end
        if v0 == 3 then
            vms(41, "AYA00320", "【アヤノ】「校庭に出たよ」")
        end
    end
    if p0 == "health" then
        if v0 == 1 then
            vms(42, "AYA00330", "【アヤノ】「保健室に来たよ」")
        end
        if v0 == 2 then
            vms(43, "AYA00340", "【アヤノ】「保健室……薬のにおいがする」")
        end
        if v0 == 3 then
            vms(44, "AYA00350", "【アヤノ】「保健室だね。他の教室と比べると、ちょっと気温が低いような気がする」")
        end
    end
    if p0 == "art" then
        if v0 == 1 then
            vms(45, "AYA00360", "【アヤノ】「美術室。他の教室と比べると、やっぱり雰囲気がちがう感じがするなあ」")
        end
        if v0 == 2 then
            vms(46, "AYA00370", "【アヤノ】「美術室だよ」")
        end
        if v0 == 3 then
            vms(47, "AYA00380", "【アヤノ】「美術室についたよ。制作途中の作品が見えるね」")
        end
    end
    if p0 == "music" then
        if v0 == 1 then
            vms(48, "AYA00390", "【アヤノ】「音楽室に来たよ」")
        end
        if v0 == 2 then
            vms(49, "AYA00400", "【アヤノ】「音楽室。中は防音になってるから、廊下の声も聞こえないね」")
        end
        if v0 == 3 then
            vms(50, "AYA00410", "【アヤノ】「音楽室。何か演奏してみようかあ……」")
        end
    end
    if p0 == "library" then
        if v0 == 1 then
            vms(51, "AYA00420", "【アヤノ】「図書室に来たよ」")
        end
        if v0 == 2 then
            vms(52, "AYA00430", "【アヤノ】「図書室だね。さすがにここは、静かにしないと……」")
        end
        if v0 == 3 then
            vms(53, "AYA00440", "【アヤノ】「図書室。なにか借りていこうかなあ……」")
        end
    end
    if p0 == "timeout" then
        if v0 == 1 then
            vms(54, "AYA00450", "【アヤノ】「そろそろ、時間かな」")
        end
        if v0 == 2 then
            vms(55, "AYA00460", "【アヤノ】「あっ、そろそろ待ち合わせの時間かも」")
        end
        if v0 == 3 then
            vms(56, "AYA00470", "【アヤノ】「うん。そろそろ時間みたい」")
        end
    end
end
comSectionMapmoveAyanoOut = function()
    local v0
    v0 = math.random(1, 3)
    vms(57, "AYA00480", "【アヤノ】「さて、次はどこに行こう」")
    vms(58, "NONVOICE", v0)
end
SystemOption = {}
SystemOption.new = function()
    local v0 = {}
    local v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13
    v0.optionKey0 = {}
    v2 = "messageSpeed"
    v3 = "messageSkip"
    v4 = "messageReadColor"
    v5 = "voiceCut"
    v6 = "messageSpeedAutoFigure"
    v7 = "messageSpeedAutoLine"
    v8 = "autoVoice"
    v0.optionKey0[1] = v2
    v0.optionKey0[2] = v3
    v0.optionKey0[3] = v4
    v0.optionKey0[4] = v5
    v0.optionKey0[5] = v6
    v0.optionKey0[6] = v7
    v0.optionKey0[7] = v8
    v0.optionKey1 = {}
    v2 = "volumeMaster"
    v3 = "volumeBGM"
    v4 = "volumeSE"
    v5 = "volumeVoice"
    v6 = "voiceFlag1"
    v7 = "voiceFlag2"
    v0.optionKey1[1] = v2
    v0.optionKey1[2] = v3
    v0.optionKey1[3] = v4
    v0.optionKey1[4] = v5
    v0.optionKey1[5] = v6
    v0.optionKey1[6] = v7
    v0.optionFlag = {}
    v0.optionFlag.messageSpeed = false
    v0.optionFlag.messageSkip = false
    v0.optionFlag.messageReadColor = false
    v0.optionFlag.voiceCut = false
    v0.optionFlag.messageSpeedAutoFigure = false
    v0.optionFlag.messageSpeedAutoLine = false
    v0.optionFlag.autoVoice = false
    v0.optionFlag.volumeMaster = false
    v0.optionFlag.volumeBGM = false
    v0.optionFlag.volumeSE = false
    v0.optionFlag.volumeVoice = false
    v0.cursorY = {}
    v0.cursorY.messageSpeed = 48
    v0.cursorY.messageSkip = 72
    v0.cursorY.messageReadColor = 96
    v0.cursorY.voiceCut = 120
    v0.cursorY.messageSpeedAutoFigure = 150
    v0.cursorY.messageSpeedAutoLine = 174
    v0.cursorY.autoVoice = 198
    v0.cursorY.volumeMaster = 48
    v0.cursorY.volumeBGM = 72
    v0.cursorY.volumeSE = 96
    v0.cursorY.volumeVoice = 120
    v0.cursorY.voiceFlag1 = 173
    v0.cursorY.voiceFlag2 = 197
    v0.layerNumber = {}
    v0.layerNumber.optionBg = 1
    v0.layerNumber.info = 2
    v0.layerNumber.cursor = 3
    v0.layerNumber.lr = 6
    v0.layerNumber.messageSpeed = 8
    v0.layerNumber.messageSkip = 11
    v0.layerNumber.messageReadColor = 14
    v0.layerNumber.voiceCut = 17
    v0.layerNumber.messageSpeedAutoFigure = 20
    v0.layerNumber.messageSpeedAutoLine = 23
    v0.layerNumber.autoVoice = 26
    v0.layerNumber.volumeMaster = 8
    v0.layerNumber.volumeBGM = 12
    v0.layerNumber.volumeSE = 16
    v0.layerNumber.volumeVoice = 20
    v0.layerNumber.voiceFlagBG = 24
    v0.layerNumber.voiceFlag1 = 26
    v0.layerNumber.voiceFlag2 = 29
    v0.KeyX = {}
    v0.KeyX.messageSpeed = 373
    v0.KeyX.messageSkip = 320
    v0.KeyX.messageReadColor = 320
    v0.KeyX.voiceCut = 355
    v0.KeyX.messageSpeedAutoFigure = 373
    v0.KeyX.messageSpeedAutoLine = 373
    v0.KeyX.autoVoice = 355
    v0.KeyX.volumeMaster = 195
    v0.KeyX.volumeBGM = 195
    v0.KeyX.volumeSE = 195
    v0.KeyX.volumeVoice = 195
    v0.KeyX.voiceNaoya = 45
    v0.KeyX.voiceAyano = 105
    v0.KeyX.voiceYuichi = 165
    v0.KeyX.voiceYukari = 45
    v0.KeyX.voiceChiaki = 120
    v0.KeyX.voiceSakura = 180
    v0.KeyX.voiceOther = 255
    v0.voiceClip = {}
    v0.voiceClip.voiceNaoya = {}
    v0.voiceClip.voiceNaoya.clipX1 = 0
    v0.voiceClip.voiceNaoya.clipX2 = 35
    v0.voiceClip.voiceAyano = {}
    v0.voiceClip.voiceAyano.clipX1 = 60
    v0.voiceClip.voiceAyano.clipX2 = 95
    v0.voiceClip.voiceYuichi = {}
    v0.voiceClip.voiceYuichi.clipX1 = 120
    v0.voiceClip.voiceYuichi.clipX2 = 185
    v0.voiceClip.voiceYukari = {}
    v0.voiceClip.voiceYukari.clipX1 = 0
    v0.voiceClip.voiceYukari.clipX2 = 50
    v0.voiceClip.voiceChiaki = {}
    v0.voiceClip.voiceChiaki.clipX1 = 75
    v0.voiceClip.voiceChiaki.clipX2 = 110
    v0.voiceClip.voiceSakura = {}
    v0.voiceClip.voiceSakura.clipX1 = 135
    v0.voiceClip.voiceSakura.clipX2 = 185
    v0.voiceClip.voiceOther = {}
    v0.voiceClip.voiceOther.clipX1 = 210
    v0.voiceClip.voiceOther.clipX2 = 260
    v0.voiceKey1 = {}
    v2 = "voiceNaoya"
    v3 = "voiceAyano"
    v4 = "voiceYuichi"
    v0.voiceKey1[1] = v2
    v0.voiceKey1[2] = v3
    v0.voiceKey1[3] = v4
    v0.voiceKey2 = {}
    v2 = "voiceYukari"
    v3 = "voiceChiaki"
    v4 = "voiceSakura"
    v5 = "voiceOther"
    v0.voiceKey2[1] = v2
    v0.voiceKey2[2] = v3
    v0.voiceKey2[3] = v4
    v0.voiceKey2[4] = v5
    v0.OptionInit = function(p0)
        local v1, v2, v3, v4, v5
        if not (p0) then
            p0 = 0
        end
        layerCopy(v0.layerNumber.optionBg, backLayerName.sys_23_a)
        layerPosition(v0.layerNumber.optionBg, 25, 30)
        layerCopy(v0.layerNumber.cursor, backLayerName.sys_21_b)
        layerCopy(v0.layerNumber.info, backLayerName.sys_20_e)
        layerPosition(v0.layerNumber.info, 25, 244)
        if p0 == 0 then
            layerPosition(v0.layerNumber.cursor, 29, v0.cursorY[v0.optionKey0[1]])
            layerCopy((v0.layerNumber.info + 3), backLayerName.sys_24_b)
            layerPosition((v0.layerNumber.info + 3), 37, 248)
            layerClip((v0.layerNumber.info + 3), 0, 0, 406, 18)
            layerCopy((v0.layerNumber.optionBg + 3), backLayerName.sys_21_a)
            layerPosition((v0.layerNumber.optionBg + 3), 45, 51)
            layerCopy(v0.layerNumber.lr, backLayerName.sys_23_d)
            layerPosition(v0.layerNumber.lr, 386, 36)
            layerClip(v0.layerNumber.lr, 20, 0, 84, 10)
            layerCopy((v0.layerNumber.lr + 1), backLayerName.sys_23_e)
            layerPosition((v0.layerNumber.lr + 1), 463, 130)
            layerClip((v0.layerNumber.lr + 1), 0, 0, 12, 18)
            v0.loadKey(v0.layerNumber.messageSpeed, "messageSpeed")
            layerCopy(v0.layerNumber.messageSpeed, backLayerName.sys_21_c)
            v0.messageSpeed()
            v0.loadKey(v0.layerNumber.messageSkip, "messageSkip")
            layerCopy(v0.layerNumber.messageSkip, backLayerName.sys_21_d)
            v0.messageSkip()
            v0.loadKey(v0.layerNumber.messageReadColor, "messageReadColor")
            layerCopy(v0.layerNumber.messageReadColor, backLayerName.sys_21_e)
            v0.messageReadColor()
            v0.loadKey(v0.layerNumber.voiceCut, "voiceCut")
            layerCopy(v0.layerNumber.voiceCut, backLayerName.sys_22_d)
            v0.voiceCut()
            v0.loadKey(v0.layerNumber.messageSpeedAutoFigure, "messageSpeedAutoFigure")
            layerCopy(v0.layerNumber.messageSpeedAutoFigure, backLayerName.sys_21_c)
            v0.messageSpeedAutoFigure()
            v0.loadKey(v0.layerNumber.messageSpeedAutoLine, "messageSpeedAutoLine")
            layerCopy(v0.layerNumber.messageSpeedAutoLine, backLayerName.sys_21_c)
            v0.messageSpeedAutoLine()
            v0.loadKey(v0.layerNumber.autoVoice, "autoVoice")
            layerCopy(v0.layerNumber.autoVoice, backLayerName.sys_21_f)
            v0.autoVoice()
        else
            layerPosition(v0.layerNumber.cursor, 29, v0.cursorY[v0.optionKey1[1]])
            layerCopy((v0.layerNumber.info + 3), backLayerName.sys_24_c)
            layerPosition((v0.layerNumber.info + 3), 45, 248)
            layerClip((v0.layerNumber.info + 3), 0, 0, 391, 18)
            layerCopy((v0.layerNumber.optionBg + 3), backLayerName.sys_22_a)
            layerPosition((v0.layerNumber.optionBg + 3), 45, 51)
            layerCopy(v0.layerNumber.lr, backLayerName.sys_23_d)
            layerPosition(v0.layerNumber.lr, 366, 36)
            layerClip(v0.layerNumber.lr, 0, 0, 60, 10)
            layerCopy((v0.layerNumber.lr + 1), backLayerName.sys_23_f)
            layerPosition((v0.layerNumber.lr + 1), 5, 130)
            layerClip((v0.layerNumber.lr + 1), 0, 0, 12, 18)
            v0.loadKey((v0.layerNumber.volumeMaster + 1), "volumeMaster")
            v0.volume(v0.layerNumber.volumeMaster, "volumeMaster")
            v0.loadKey((v0.layerNumber.volumeBGM + 1), "volumeBGM")
            v0.volume(v0.layerNumber.volumeBGM, "volumeBGM")
            v0.loadKey((v0.layerNumber.volumeSE + 1), "volumeSE")
            v0.volume(v0.layerNumber.volumeSE, "volumeSE")
            v0.loadKey((v0.layerNumber.volumeVoice + 1), "volumeVoice")
            v0.volume(v0.layerNumber.volumeVoice, "volumeVoice")
            layerCopy(v0.layerNumber.voiceFlagBG, backLayerName.sys_22_e)
            v2 = v0.cursorY.voiceFlag1 + 3
            layerPosition(v0.layerNumber.voiceFlagBG, 60, v2)
            layerClip(v0.layerNumber.voiceFlagBG, 0, 41, 260, 82)
            v3 = 1
            v1 = 3
            v4 = 1
            for v2 = v3, v1, v4 do
                v0.voiceFlag1(v2, v0.voiceKey1[v2])
            end
            v3 = 1
            v1 = 4
            v4 = 1
            for v2 = v3, v1, v4 do
                v0.voiceFlag2(v2, v0.voiceKey2[v2])
            end
        end
    end
    v0.loadKey = function(p0, p1)
        local v1, v2
        layerCopy((p0 + 1), backLayerName.sys_23_b)
        layerPosition((p0 + 1), v0.KeyX[p1], (v0.cursorY[p1] + 2))
        layerClip((p0 + 1), 0, 0, 16, 18)
        layerCopy((p0 + 2), backLayerName.sys_23_c)
        v1 = p0 + 2
        v2 = v0.cursorY[p1] + 2
        layerPosition(v1, 421, v2)
        v1 = p0 + 2
        layerClip(v1, 0, 0, 16, 18)
    end
    v0.messageSpeed = function()
        local v1, v2, v3
        v1 = (systemSave.messageSpeed - 1) * 16
        v2 = systemSave.messageSpeed * 16
        layerClip(v0.layerNumber.messageSpeed, 0, v1, 22, v2)
        v1 = v0.cursorY.messageSpeed + 3
        layerPosition(v0.layerNumber.messageSpeed, 393, v1)
        if systemSave.messageSpeed == 1 then
            layerVisible((v0.layerNumber.messageSpeed + 1), false)
        end
        if systemSave.messageSpeed == 2 then
            layerVisible((v0.layerNumber.messageSpeed + 1), true)
        end
        if systemSave.messageSpeed == 4 then
            layerVisible((v0.layerNumber.messageSpeed + 2), true)
        end
        if systemSave.messageSpeed == 5 then
            v3 = v0.layerNumber.messageSpeed + 2
            layerVisible(v3, false)
        end
    end
    v0.messageSkip = function()
        local v1, v2, v3
        v1 = systemSave.messageSkip * 17
        v2 = (systemSave.messageSkip + 1) * 17
        layerClip(v0.layerNumber.messageSkip, 0, v1, 78, v2)
        v1 = v0.cursorY.messageSkip + 3
        layerPosition(v0.layerNumber.messageSkip, 340, v1)
        if systemSave.messageSkip == 0 then
            layerVisible((v0.layerNumber.messageSkip + 1), false)
            layerVisible((v0.layerNumber.messageSkip + 2), true)
        else
            layerVisible((v0.layerNumber.messageSkip + 1), true)
            v3 = v0.layerNumber.messageSkip + 2
            layerVisible(v3, false)
        end
    end
    v0.messageReadColor = function()
        local v1, v2, v3
        v1 = systemSave.messageReadColor * 17
        v2 = (systemSave.messageReadColor + 1) * 17
        layerClip(v0.layerNumber.messageReadColor, 0, v1, 79, v2)
        v1 = v0.cursorY.messageReadColor + 3
        layerPosition(v0.layerNumber.messageReadColor, 340, v1)
        if systemSave.messageReadColor == 0 then
            layerVisible((v0.layerNumber.messageReadColor + 1), false)
            layerVisible((v0.layerNumber.messageReadColor + 2), true)
        else
            layerVisible((v0.layerNumber.messageReadColor + 1), true)
            v3 = v0.layerNumber.messageReadColor + 2
            layerVisible(v3, false)
        end
    end
    v0.voiceCut = function()
        local v1, v2, v3
        v1 = systemSave.voiceCut * 17
        v2 = (systemSave.voiceCut + 1) * 17
        layerClip(v0.layerNumber.voiceCut, 0, v1, 46, v2)
        v1 = v0.cursorY.voiceCut + 3
        layerPosition(v0.layerNumber.voiceCut, 374, v1)
        if systemSave.voiceCut == 0 then
            layerVisible((v0.layerNumber.voiceCut + 1), false)
            layerVisible((v0.layerNumber.voiceCut + 2), true)
        else
            layerVisible((v0.layerNumber.voiceCut + 1), true)
            v3 = v0.layerNumber.voiceCut + 2
            layerVisible(v3, false)
        end
    end
    v0.messageSpeedAutoFigure = function()
        local v1, v2, v3
        v1 = (systemSave.messageSpeedAutoFigure - 1) * 16
        v2 = systemSave.messageSpeedAutoFigure * 16
        layerClip(v0.layerNumber.messageSpeedAutoFigure, 0, v1, 22, v2)
        v1 = v0.cursorY.messageSpeedAutoFigure + 3
        layerPosition(v0.layerNumber.messageSpeedAutoFigure, 393, v1)
        if systemSave.messageSpeedAutoFigure == 1 then
            layerVisible((v0.layerNumber.messageSpeedAutoFigure + 1), false)
        end
        if systemSave.messageSpeedAutoFigure == 2 then
            layerVisible((v0.layerNumber.messageSpeedAutoFigure + 1), true)
        end
        if systemSave.messageSpeedAutoFigure == 4 then
            layerVisible((v0.layerNumber.messageSpeedAutoFigure + 2), true)
        end
        if systemSave.messageSpeedAutoFigure == 5 then
            v3 = v0.layerNumber.messageSpeedAutoFigure + 2
            layerVisible(v3, false)
        end
    end
    v0.messageSpeedAutoLine = function()
        local v1, v2, v3
        v1 = (systemSave.messageSpeedAutoLine - 1) * 16
        v2 = systemSave.messageSpeedAutoLine * 16
        layerClip(v0.layerNumber.messageSpeedAutoLine, 0, v1, 22, v2)
        v1 = v0.cursorY.messageSpeedAutoLine + 3
        layerPosition(v0.layerNumber.messageSpeedAutoLine, 393, v1)
        if systemSave.messageSpeedAutoLine == 1 then
            layerVisible((v0.layerNumber.messageSpeedAutoLine + 1), false)
        end
        if systemSave.messageSpeedAutoLine == 2 then
            layerVisible((v0.layerNumber.messageSpeedAutoLine + 1), true)
        end
        if systemSave.messageSpeedAutoLine == 4 then
            layerVisible((v0.layerNumber.messageSpeedAutoLine + 2), true)
        end
        if systemSave.messageSpeedAutoLine == 5 then
            v3 = v0.layerNumber.messageSpeedAutoLine + 2
            layerVisible(v3, false)
        end
    end
    v0.autoVoice = function()
        local v1, v2, v3
        v1 = systemSave.autoVoice * 16
        v2 = (systemSave.autoVoice + 1) * 16
        layerClip(v0.layerNumber.autoVoice, 0, v1, 47, v2)
        layerPosition(v0.layerNumber.autoVoice, 375, (v0.cursorY.autoVoice + 3))
        if systemSave.autoVoice == 0 then
            layerVisible((v0.layerNumber.autoVoice + 1), false)
            layerVisible((v0.layerNumber.autoVoice + 2), true)
        else
            layerVisible((v0.layerNumber.autoVoice + 1), true)
            v3 = v0.layerNumber.autoVoice + 2
            layerVisible(v3, false)
        end
    end
    v0.volume = function(p0, p1)
        local v1 = 1
        local v2, v3, v4
        layerCopy(p0, backLayerName.sys_22_ba)
        layerPosition(p0, 211, (v0.cursorY[p1] + 5))
        layerCopy((p0 + 1), backLayerName.sys_22_bb)
        if 0 < systemSave[p1] then
            v3 = p0 + 1
            v4 = 67 + (14 * systemSave[p1])
            layerClip(v3, 67, 0, v4, 16)
            layerPosition((p0 + 1), 278, (v0.cursorY[p1] + 5))
        else
            layerClip((p0 + 1), 0, 0, 67, 16)
            v3 = p0 + 1
            v2 = v0.cursorY[p1] + 5
            layerPosition(v3, 211, v2)
        end
        if systemSave[p1] < 1 then
            layerVisible((p0 + 2), false)
            layerVisible((p0 + 3), true)
        elseif 9 < systemSave[p1] then
            layerVisible((p0 + 2), true)
            layerVisible((p0 + 3), false)
        else
            layerVisible((p0 + 2), true)
            v3 = p0 + 3
            layerVisible(v3, true)
        end
    end
    v0.voiceFlag1 = function(p0, p1)
        local v1, v2
        v1 = (v0.layerNumber.voiceFlag1 + p0) - 1
        layerCopy(v1, backLayerName.sys_20_f)
        if systemSave[p1] == 1 then
            v1 = (v0.layerNumber.voiceFlag1 + p0) - 1
            layerClip(v1, 0, 0, 11, 11)
        else
            v1 = (v0.layerNumber.voiceFlag1 + p0) - 1
            layerClip(v1, 0, 11, 11, 22)
        end
        v1 = (v0.layerNumber.voiceFlag1 + p0) - 1
        v2 = v0.cursorY.voiceFlag1 + 6
        layerPosition(v1, v0.KeyX[p1], v2)
    end
    v0.voiceFlag2 = function(p0, p1)
        local v1, v2
        v1 = (v0.layerNumber.voiceFlag2 + p0) - 1
        layerCopy(v1, backLayerName.sys_20_f)
        if systemSave[p1] == 1 then
            v1 = (v0.layerNumber.voiceFlag2 + p0) - 1
            layerClip(v1, 0, 0, 11, 11)
        else
            v1 = (v0.layerNumber.voiceFlag2 + p0) - 1
            layerClip(v1, 0, 11, 11, 22)
        end
        v1 = (v0.layerNumber.voiceFlag2 + p0) - 1
        v2 = v0.cursorY.voiceFlag2 + 6
        layerPosition(v1, v0.KeyX[p1], v2)
    end
    v0.voiceCursor = function(p0, p1)
        local v1, v2, v3
        if 4 < p0 then
            layerCopy((v0.layerNumber.voiceFlagBG + 1), backLayerName.sys_22_e)
            if p0 == 5 then
                v1 = v0.layerNumber.voiceFlagBG + 1
                v2 = (v0.KeyX[v0.voiceKey1[p1]]) + 15
                layerPosition(v1, v2, (v0.cursorY.voiceFlag1 + 3))
                layerClip((v0.layerNumber.voiceFlagBG + 1), v0.voiceClip[v0.voiceKey1[p1]].clipX1, 0, v0.voiceClip[v0.voiceKey1[p1]].clipX2, 20)
            elseif p0 == 6 then
                v1 = v0.layerNumber.voiceFlagBG + 1
                v2 = (v0.KeyX[v0.voiceKey2[p1]]) + 15
                layerPosition(v1, v2, (v0.cursorY.voiceFlag2 + 3))
                layerClip((v0.layerNumber.voiceFlagBG + 1), v0.voiceClip[v0.voiceKey2[p1]].clipX1, 24, v0.voiceClip[v0.voiceKey2[p1]].clipX2, 41)
            end
        else
            layerLoad((v0.layerNumber.voiceFlagBG + 1), "")
        end
    end
    v0.OptionMain = function()
        local v1 = 0
        local v2 = 1
        local v3 = false
        local v4 = 0
        local v5 = false
        local v6 = false
        local v7 = 1
        local v8 = {}
        local v9, v10, v11, v12, v13
        v8.volumeMaster = 0
        v8.volumeBGM = 0
        v8.volumeSE = 0
        v8.volumeVoice = 0
        while v1 < 1 do
            v9 = pressButton("R")
            if (v9 == true) and (v4 == 0) then
                v4 = 1
                v5 = true
            end
            v9 = pressButton("L")
            if (v9 == true) and (v4 == 1) then
                v4 = 0
                v5 = true
            end
            if v5 == false then
                if v4 == 0 then
                    v9 = pressButton("CROSS")
                    if (v9 == true) and (v3 == false) then
                        keyPlaySE(seName.cross)
                        break
                    else
                        v9 = pressButton("UP")
                        if (v9 == true) and (v3 == false) then
                            v9 = v2 - 1
                            if v9 < 1 then
                                v2 = 7
                            else
                                v2 = v2 - 1
                            end
                            v3 = true
                            v6 = true
                        end
                        v9 = pressButton("DOWN")
                        if (v9 == true) and (v3 == false) then
                            v9 = v2 + 1
                            if 7 < v9 then
                                v2 = 1
                            else
                                v2 = v2 + 1
                            end
                            v3 = true
                            v6 = true
                        end
                        v9 = pressButton("RIGHT")
                        if (v9 == true) and (v3 == false) then
                            if (v2 == 1) or (v2 == 5) or (v2 == 6) then
                                v10 = v0.optionKey0[v2]
                                v11 = (systemSave[v0.optionKey0[v2]]) + 1
                                if 5 < v11 then
                                    v11 = 5
                                else
                                    v11 = (systemSave[v0.optionKey0[v2]]) + 1
                                end
                                systemSave[v10] = v11
                            else
                                v10 = v0.optionKey0[v2]
                                v11 = (systemSave[v0.optionKey0[v2]]) + 1
                                if 1 < v11 then
                                    v11 = 1
                                else
                                    v11 = (systemSave[v0.optionKey0[v2]]) + 1
                                end
                                systemSave[v10] = v11
                            end
                            v0.optionFlag[v0.optionKey0[v2]] = true
                            v3 = true
                        end
                        v9 = pressButton("LEFT")
                        if (v9 == true) and (v3 == false) then
                            if (v2 == 1) or (v2 == 5) or (v2 == 6) then
                                v10 = v0.optionKey0[v2]
                                v11 = (systemSave[v0.optionKey0[v2]]) - 1
                                if v11 < 1 then
                                    v11 = 1
                                else
                                    v11 = (systemSave[v0.optionKey0[v2]]) - 1
                                end
                                systemSave[v10] = v11
                            else
                                v10 = v0.optionKey0[v2]
                                v11 = (systemSave[v0.optionKey0[v2]]) - 1
                                if v11 < 0 then
                                    v11 = 0
                                else
                                    v11 = (systemSave[v0.optionKey0[v2]]) - 1
                                end
                                systemSave[v10] = v11
                            end
                            v0.optionFlag[v0.optionKey0[v2]] = true
                            v3 = true
                        end
                        if v3 == true then
                            keyPlaySE(seName.arrowKey)
                            v9 = v0.optionFlag.messageSpeed
                            if v9 then
                                v0.messageSpeed()
                            end
                            v9 = v0.optionFlag.messageSkip
                            if v9 then
                                v0.messageSkip()
                            end
                            v9 = v0.optionFlag.messageReadColor
                            if v9 then
                                v0.messageReadColor()
                            end
                            v9 = v0.optionFlag.voiceCut
                            if v9 then
                                v0.voiceCut()
                            end
                            v9 = v0.optionFlag.messageSpeedAutoFigure
                            if v9 then
                                v0.messageSpeedAutoFigure()
                            end
                            v9 = v0.optionFlag.messageSpeedAutoLine
                            if v9 then
                                v0.messageSpeedAutoLine()
                            end
                            v9 = v0.optionFlag.autoVoice
                            if v9 then
                                v0.autoVoice()
                            end
                            if v6 then
                                v12 = v0.cursorY[v0.optionKey0[v2]]
                                layerMovePosition(v0.layerNumber.cursor, 29, v12, 5)
                                v10 = v0.layerNumber.info + 3
                                v12 = (v2 - 1) * 18
                                layerClip(v10, 0, v12, 406, (v2 * 18))
                                v6 = false
                            end
                            wait(5)
                            v0.optionFlag[v0.optionKey0[v2]] = false
                            v3 = false
                        end
                    end
                else
                    v9 = pressButton("CROSS")
                    if (v9 == true) and (v3 == false) then
                        keyPlaySE(seName.cross)
                        break
                    else
                        v9 = pressButton("CIRCLE")
                        if (v9 == true) and (v3 == false) then
                            if (v2 == 1) or (v2 == 2) or (v2 == 3) or (v2 == 4) then
                                if v8[v0.optionKey1[v2]] == 0 then
                                    v8[v0.optionKey1[v2]] = systemSave[v0.optionKey1[v2]]
                                    systemSave[v0.optionKey1[v2]] = 0
                                else
                                    systemSave[v0.optionKey1[v2]] = v8[v0.optionKey1[v2]]
                                    v8[v0.optionKey1[v2]] = 0
                                end
                            elseif v2 == 5 then
                                v10 = v0.voiceKey1[v7]
                                if systemSave[v0.voiceKey1[v7]] == 0 then
                                    v11 = 1
                                else
                                    v11 = 0
                                end
                                systemSave[v10] = v11
                            elseif v2 == 6 then
                                v10 = v0.voiceKey2[v7]
                                if systemSave[v0.voiceKey2[v7]] == 0 then
                                    v11 = 1
                                else
                                    v11 = 0
                                end
                                systemSave[v10] = v11
                            end
                            wait(3)
                            keyPlaySE(seName.circle)
                            v0.optionFlag[v0.optionKey1[v2]] = true
                            v3 = true
                        end
                        v9 = pressButton("UP")
                        if (v9 == true) and (v3 == false) then
                            v9 = v2 - 1
                            if v9 < 1 then
                                v2 = 6
                            else
                                v2 = v2 - 1
                            end
                            if (v2 == 5) and (3 < v7) then
                                v7 = 3
                            end
                            v3 = true
                            v6 = true
                        end
                        v9 = pressButton("DOWN")
                        if (v9 == true) and (v3 == false) then
                            v9 = v2 + 1
                            if 6 < v9 then
                                v2 = 1
                            else
                                v2 = v2 + 1
                            end
                            if (v2 == 5) and (3 < v7) then
                                v7 = 3
                            end
                            v3 = true
                            v6 = true
                        end
                        v9 = pressButton("RIGHT")
                        if (v9 == true) and (v3 == false) then
                            if (v2 == 1) or (v2 == 2) or (v2 == 3) or (v2 == 4) then
                                v8[v0.optionKey1[v2]] = 0
                                v10 = v0.optionKey1[v2]
                                v11 = (systemSave[v0.optionKey1[v2]]) + 1
                                if 10 < v11 then
                                    v11 = 10
                                else
                                    v11 = (systemSave[v0.optionKey1[v2]]) + 1
                                end
                                systemSave[v10] = v11
                                v0.optionFlag[v0.optionKey1[v2]] = true
                            elseif v2 == 5 then
                                v9 = v7 + 1
                                if 3 < v9 then
                                    v7 = 3
                                else
                                    v7 = v7 + 1
                                end
                            elseif v2 == 6 then
                                v9 = v7 + 1
                                if 4 < v9 then
                                    v7 = 4
                                else
                                    v7 = v7 + 1
                                end
                            end
                            v3 = true
                        end
                        v9 = pressButton("LEFT")
                        if (v9 == true) and (v3 == false) then
                            if (v2 == 1) or (v2 == 2) or (v2 == 3) or (v2 == 4) then
                                v10 = v0.optionKey1[v2]
                                v11 = (systemSave[v0.optionKey1[v2]]) - 1
                                if v11 < 0 then
                                    v11 = 0
                                else
                                    v11 = (systemSave[v0.optionKey1[v2]]) - 1
                                end
                                systemSave[v10] = v11
                                v0.optionFlag[v0.optionKey1[v2]] = true
                            else
                                v9 = v7 - 1
                                if v9 < 1 then
                                    v7 = 1
                                else
                                    v7 = v7 - 1
                                end
                            end
                            v3 = true
                        end
                        if v3 == true then
                            keyPlaySE(seName.arrowKey)
                            v9 = v0.optionFlag.volumeMaster
                            if v9 then
                                v0.volume(v0.layerNumber.volumeMaster, "volumeMaster")
                            end
                            v9 = v0.optionFlag.volumeBGM
                            if v9 then
                                v0.volume(v0.layerNumber.volumeBGM, "volumeBGM")
                            end
                            v9 = v0.optionFlag.volumeSE
                            if v9 then
                                v0.volume(v0.layerNumber.volumeSE, "volumeSE")
                            end
                            v9 = v0.optionFlag.volumeVoice
                            if v9 then
                                v0.volume(v0.layerNumber.volumeVoice, "volumeVoice")
                            end
                            v9 = v0.optionFlag.voiceFlag1
                            if v9 then
                                v0.voiceFlag1(v7, v0.voiceKey1[v7])
                            end
                            v9 = v0.optionFlag.voiceFlag2
                            if v9 then
                                v0.voiceFlag2(v7, v0.voiceKey2[v7])
                            end
                            v0.voiceCursor(v2, v7)
                            if v6 then
                                v12 = v0.cursorY[v0.optionKey1[v2]]
                                layerMovePosition(v0.layerNumber.cursor, 29, v12, 5)
                                if not (v2 == 6) then
                                    v10 = v0.layerNumber.info + 3
                                    v12 = (v2 - 1) * 18
                                    layerClip(v10, 0, v12, 391, (v2 * 18))
                                end
                                v6 = false
                            end
                            wait(5)
                            v0.optionFlag[v0.optionKey1[v2]] = false
                            v3 = false
                        end
                    end
                end
            else
                v5 = false
                v0.pageChange()
                v0.OptionInit(v4)
                v2 = 1
            end
            wait(1)
        end
    end
    v0.blackIn = function()
        layerLoad(0, "")
        wait(1)
        layerCopy(0, backLayerName.black)
        layerAlpha(0, 0)
        layerMoveAlpha(0, 60, 20)
        wait(20)
    end
    v0.blackOut = function()
        layerMoveAlpha(0, 0, 20)
        wait(20)
        layerLoad(0, "")
    end
    v0.pageChange = function()
        local v0 = 1
        local v1 = 100
        local v2 = 1
        local i0
        for i0 = v0, v1, v2 do
            layerLoad(i0, "")
        end
    end
    v0.OptionEnd = function()
        local v1 = 3
        local v2 = 100
        local v3 = 1
        local i0
        for i0 = v1, v2, v3 do
            layerMoveAlpha(i0, 0, 10)
        end
        wait(10)
        layerMoveScale(v0.layerNumber.optionBg, 0, 100, 20)
        layerMoveScale(v0.layerNumber.info, 0, 100, 20)
        wait(20)
        v1 = 1
        v2 = 100
        v3 = 1
        for i0 = v1, v2, v3 do
            layerLoad(i0, "")
        end
    end
    v0.Option = function()
        local v1, v2, v3, i1
        pageScreen(1)
        v0.blackIn()
        v0.OptionInit()
        v1 = 3
        v2 = 100
        v3 = 1
        for i1 = v1, v2, v3 do
            layerAlpha(i1, 0)
        end
        layerScale(v0.layerNumber.optionBg, 0, 100)
        layerMoveScale(v0.layerNumber.optionBg, 100, 100, 20)
        layerScale(v0.layerNumber.info, 0, 100)
        layerMoveScale(v0.layerNumber.info, 100, 100, 20)
        wait(20)
        v1 = 3
        v2 = 100
        v3 = 1
        for i1 = v1, v2, v3 do
            layerMoveAlpha(i1, 100, 10)
        end
        wait(10)
        v0.OptionMain()
        v0.OptionEnd()
        autoSystemSave(1)
        v0.blackOut()
        wait(5)
        pageScreen(0)
        wait(1)
    end
    return v0
end
systemOption = SystemOption.new()
autoSystemSave = function(p0)
    local v0, v1
    if not (p0) then
        p0 = 0
    end
    v0 = 0
    v1 = succeedLoadSystemdata()
    if v1 then
        runAutoSave()
    else
        v1 = existSystemdata()
        if v1 then
            if p0 == 1 then
                v1 = systemConfig.confirm(backLayerName.sys_5_i, 100, 80)
                if v1 == true then
                    runAutoSave()
                else
                    v0 = 1
                end
            else
                v1 = comDlgYesNo(cGetFileName("sysgim", "sys_5_i"), 100, 80)
                if v1 == true then
                    runAutoSave()
                else
                    v0 = 1
                    return
                end
            end
        elseif p0 == 1 then
            v1 = systemConfig.confirm(backLayerName.sys_5_j, 100, 80)
            if v1 == true then
                runAutoSave()
            else
                v0 = 1
            end
        else
            v1 = comDlgYesNo(cGetFileName("sysgim", "sys_5_j"), 100, 80)
            if v1 == true then
                runAutoSave()
            else
                v0 = 1
                return
            end
        end
    end
    if v0 == 1 then
        applySystemdata()
        return
    end
    wait(1)
    while succeedLoadSystemdata() == false do
        v1 = existSystemdata()
        if v1 then
            if p0 == 1 then
                v1 = systemConfig.confirm(backLayerName.sys_5_i, 100, 80)
                if v1 == true then
                    runAutoSave()
                else
                    break
                end
            else
                v1 = comDlgYesNo(cGetFileName("sysgim", "sys_5_i"), 100, 80)
                if v1 == true then
                    runAutoSave()
                else
                    break
                end
            end
        elseif p0 == 1 then
            v1 = systemConfig.confirm(backLayerName.sys_5_j, 100, 80)
            if v1 == true then
                runAutoSave()
            else
                break
            end
        else
            v1 = comDlgYesNo(cGetFileName("sysgim", "sys_5_j"), 100, 80)
            if v1 == true then
                runAutoSave()
            else
                break
            end
        end
        wait(1)
    end
    applySystemdata()
end
SystemConfig = {}
SystemConfig.new = function()
    local v0 = {}
    local v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12
    v0.layerNumber = {}
    v0.layerNumber.configBG = 1
    v0.layerNumber.info = 2
    v0.ConfigInit = function()
        local v1, v2, v3, i0
        if systemSave.storyLineSkip == 1 then
            systemSave.storyLineSkip = 0
        end
        fontClear()
        v0.blackIn()
        layerCopy(v0.layerNumber.configBG, backLayerName.sys_20_a)
        layerPosition(v0.layerNumber.configBG, 170, 30)
        layerCopy(v0.layerNumber.info, backLayerName.sys_20_e)
        layerPosition(v0.layerNumber.info, 25, 244)
        layerCopy((v0.layerNumber.configBG + 2), backLayerName.sys_20_b)
        layerPosition((v0.layerNumber.configBG + 2), 175, 35)
        if gameSave.tutorial.firstFragment == 1 then
            if memoryFlag == true then
                layerLoad((v0.layerNumber.configBG + 3), cGetFileName("sysgim", "sys_20_cd"))
            else
                layerCopy((v0.layerNumber.configBG + 3), backLayerName.sys_20_c)
            end
        elseif memoryFlag == true then
            systemSave.storyLineSkip = 0
            layerLoad((v0.layerNumber.configBG + 3), cGetFileName("sysgim", "sys_20_cc"))
        else
            systemSave.storyLineSkip = 0
            layerLoad((v0.layerNumber.configBG + 3), cGetFileName("sysgim", "sys_20_cb"))
        end
        layerPosition((v0.layerNumber.configBG + 3), 193, 38)
        layerCopy((v0.layerNumber.info + 3), backLayerName.sys_20_d)
        layerPosition((v0.layerNumber.info + 3), 53, 248)
        layerClip((v0.layerNumber.info + 3), 0, 0, 361, 18)
        layerCopy((v0.layerNumber.info + 4), backLayerName.sys_20_f)
        layerPosition((v0.layerNumber.info + 4), 180, 163)
        if not (systemSave.storyLineSkip == 0) then
            layerClip((v0.layerNumber.info + 4), 0, 0, 11, 11)
        else
            layerClip((v0.layerNumber.info + 4), 0, 11, 11, 22)
        end
        v2 = v0.layerNumber.info + 1
        v1 = v0.layerNumber.info + 4
        v3 = 1
        for i0 = v2, v1, v3 do
            layerAlpha(i0, 0)
        end
        layerScale(v0.layerNumber.configBG, 0, 100)
        layerScale(v0.layerNumber.info, 0, 100)
        layerMoveScale(v0.layerNumber.configBG, 100, 100, 20)
        layerMoveScale(v0.layerNumber.info, 100, 100, 20)
        wait(20)
        v2 = v0.layerNumber.info + 1
        v1 = v0.layerNumber.info + 4
        v3 = 1
        for i0 = v2, v1, v3 do
            layerMoveAlpha(i0, 100, 10)
        end
        wait(10)
    end
    v0.ConfigEnd = function()
        local v1, v2, v3, i0
        v1 = v0.layerNumber.info + 1
        v2 = v0.layerNumber.info + 4
        v3 = 1
        for i0 = v1, v2, v3 do
            layerMoveAlpha(i0, 0, 10)
        end
        wait(10)
        layerMoveScale(v0.layerNumber.configBG, 0, 100, 20)
        layerMoveScale(v0.layerNumber.info, 0, 100, 20)
        wait(20)
        v1 = 1
        v2 = 5
        v3 = 1
        for i0 = v1, v2, v3 do
            layerLoad(i0, "")
        end
    end
    v0.ConfigMain = function()
        local v1 = 0
        local v2 = 1
        local v3 = false
        local v4, v5, v6, v7
        while v1 < 1 do
            v4 = pressButton("CIRCLE")
            if (v4 == true) and (v3 == false) then
                if gameSave.tutorial.firstFragment == 1 then
                    if v2 == 6 then
                        keyPlaySE(seName.circle)
                        if systemSave.storyLineSkip == 2 then
                            v5 = 0
                        else
                            v5 = 2
                        end
                        systemSave.storyLineSkip = v5
                        if not (systemSave.storyLineSkip == 0) then
                            layerClip((v0.layerNumber.info + 4), 0, 0, 11, 11)
                        else
                            layerClip((v0.layerNumber.info + 4), 0, 11, 11, 22)
                        end
                        wait(5)
                    elseif v2 == 3 then
                        if not (memoryFlag == true) then
                            keyPlaySE(seName.circle)
                            break
                        else
                            wait(1)
                        end
                    else
                        keyPlaySE(seName.circle)
                        break
                    end
                elseif (v2 == 3) or (v2 == 4) or (v2 == 7) or (v2 == 8) then
                    if v2 == 3 then
                        if not (memoryFlag == true) then
                            keyPlaySE(seName.circle)
                            break
                        else
                            wait(1)
                        end
                    else
                        keyPlaySE(seName.circle)
                        break
                    end
                else
                    v4 = pressButton("CROSS")
                    if (v4 == true) and (v3 == false) then
                        keyPlaySE(seName.cross)
                        v2 = -1
                        break
                    else
                        v4 = pressButton("UP")
                        if (v4 == true) and (v3 == false) then
                            v4 = v2 - 1
                            if v4 < 1 then
                                v2 = 8
                            else
                                v2 = v2 - 1
                            end
                            v3 = true
                        end
                        v4 = pressButton("DOWN")
                        if (v4 == true) and (v3 == false) then
                            v4 = v2 + 1
                            if 8 < v4 then
                                v2 = 1
                            else
                                v2 = v2 + 1
                            end
                            v3 = true
                        end
                        if v3 == true then
                            keyPlaySE(seName.arrowKey)
                            v5 = v0.layerNumber.configBG + 2
                            v6 = ((v2 - 1) * 24) + 35
                            layerMovePosition(v5, 175, v6, 5)
                            v5 = v0.layerNumber.info + 3
                            v6 = (v2 - 1) * 18
                            layerClip(v5, 0, v6, 376, (v2 * 18))
                            wait(5)
                            v3 = false
                        end
                        wait(1)
                    end
                end
            else
                v4 = pressButton("CROSS")
                if (v4 == true) and (v3 == false) then
                    keyPlaySE(seName.cross)
                    v2 = -1
                    break
                else
                    v4 = pressButton("UP")
                    if (v4 == true) and (v3 == false) then
                        v4 = v2 - 1
                        if v4 < 1 then
                            v2 = 8
                        else
                            v2 = v2 - 1
                        end
                        v3 = true
                    end
                    v4 = pressButton("DOWN")
                    if (v4 == true) and (v3 == false) then
                        v4 = v2 + 1
                        if 8 < v4 then
                            v2 = 1
                        else
                            v2 = v2 + 1
                        end
                        v3 = true
                    end
                    if v3 == true then
                        keyPlaySE(seName.arrowKey)
                        v5 = v0.layerNumber.configBG + 2
                        v6 = ((v2 - 1) * 24) + 35
                        layerMovePosition(v5, 175, v6, 5)
                        v5 = v0.layerNumber.info + 3
                        v6 = (v2 - 1) * 18
                        v7 = v2 * 18
                        layerClip(v5, 0, v6, 376, v7)
                        wait(5)
                        v3 = false
                    end
                    wait(1)
                end
            end
        end
        return v2
    end
    v0.blackIn = function()
        layerLoad(0, "")
        wait(1)
        layerCopy(0, backLayerName.black)
        layerAlpha(0, 0)
        layerMoveAlpha(0, 60, 20)
        wait(20)
    end
    v0.blackOut = function()
        layerMoveAlpha(0, 0, 20)
        wait(20)
        layerLoad(0, "")
    end
    v0.unsetConfigButton = function()
        functionButton("SQUARE", "")
    end
    v0.setConfigButton = function()
        functionButton("SQUARE", "systemConfig.Config")
    end
    v0.confirm = function(p0, p1, p2)
        local v1 = 0
        local v2 = false
        local v3, v4, v5, v6, v7, v8, v9, v10, v11, v12
        layerCopy(v0.layerNumber.configBG, backLayerName.sys_5_e)
        layerCopy((v0.layerNumber.configBG + 1), p0)
        layerPosition((v0.layerNumber.configBG + 1), p1, p2)
        layerCopy((v0.layerNumber.configBG + 2), backLayerName.sys_13_b)
        v3 = v0.layerNumber.configBG + 2
        v4 = 139 + (23 * v1)
        layerPosition(v3, 184, v4)
        layerCopy((v0.layerNumber.configBG + 3), backLayerName.sys_13_c)
        layerPosition((v0.layerNumber.configBG + 3), 217, 142)
        v5 = 0
        v3 = 3
        v6 = 1
        for v4 = v5, v3, v6 do
            layerAlpha((v0.layerNumber.configBG + v4), 0)
            layerMoveAlpha((v0.layerNumber.configBG + v4), 100, 30)
        end
        wait(30)
        v5 = 1
        v3 = 1
        v6 = 1
        v4 = 1
        v8 = 0
        while true do
            v7 = pressButton("UP")
            if (v7 == true) and (v2 == false) and (v5 == 0) then
                v7 = v1 - 1
                if v7 < 0 then
                    v1 = 1
                else
                    v1 = v1 - 1
                end
                v2 = true
            end
            v7 = pressButton("UP")
            if v7 == false then
                v5 = 0
            end
            v7 = pressButton("DOWN")
            if (v7 == true) and (v2 == false) and (v3 == 0) then
                v7 = v1 + 1
                if 1 < v7 then
                    v1 = 0
                else
                    v1 = v1 + 1
                end
                v2 = true
            end
            v7 = pressButton("DOWN")
            if v7 == false then
                v3 = 0
            end
            v7 = pressButton("CIRCLE")
            if (v7 == true) and (v2 == false) and (v6 == 0) then
                keyPlaySE(seName.circle)
                break
            else
                v7 = pressButton("CIRCLE")
                if v7 == false then
                    v6 = 0
                end
                v7 = pressButton("CROSS")
                if (v7 == true) and (v2 == false) and (v4 == 0) then
                    keyPlaySE(seName.cross)
                    v1 = 1
                    break
                else
                    v7 = pressButton("CROSS")
                    if v7 == false then
                        v4 = 0
                    end
                    if v2 == true then
                        keyPlaySE(seName.arrowKey)
                        v9 = v0.layerNumber.configBG + 2
                        v10 = 139 + (23 * v1)
                        layerMovePosition(v9, 184, v10, 5)
                        wait(5)
                        v2 = false
                    end
                    v8 = v8 + 1
                    if 12 < v8 then
                        v6 = 0
                    end
                    wait(2)
                end
            end
        end
        v7 = 0
        v9 = 3
        v11 = 1
        for v10 = v7, v9, v11 do
            layerMoveAlpha((v0.layerNumber.configBG + v10), 0, 30)
        end
        wait(30)
        v7 = 0
        v9 = 3
        v11 = 1
        for v10 = v7, v9, v11 do
            layerLoad((v0.layerNumber.configBG + v10), "")
        end
        retFlag = false
        if v1 == 0 then
            retFlag = true
        end
        v7 = retFlag
        return v7
    end
    v0.Config = function()
        local v1, v2, v3
        playVoice("")
        v1 = advIsPart()
        v2 = nil
        advPart(false)
        pageScreen(1)
        fontClear()
        v0.ConfigInit()
        v2 = v0.ConfigMain()
        v0.ConfigEnd()
        if v2 == 8 then
            v3 = v0.confirm(backLayerName.sys_5_g, 130, 80)
            if v3 == false then
                v2 = -1
            end
        elseif (v2 == 1) or (v2 == 2) then
            v3 = v0.confirm(backLayerName.sys_5_h, 150, 80)
            if v3 == false then
                v2 = -1
            end
        end
        v0.blackOut()
        if v2 == 1 then
            pageScreen(0)
            wait(10)
            msgQuit()
            cInitGame()
            fontClear()
            switchScreen(0, "", 60)
            memoryFlag = false
            run(cGetFileName("script", "snr_story_main"))
        elseif v2 == 2 then
            pageScreen(0)
            wait(10)
            msgQuit()
            cInitGame()
            fontClear()
            switchScreen(0, "", 60)
            memoryFlag = false
            run(cGetFileName("script", "snr_fragment_main"))
        elseif v2 == 3 then
            v0.blackIn()
            if v1 == true then
                advPart(true)
            end
            runListSave()
            autoSystemSave(1)
            pageScreen(0)
            wait(10)
            v0.Config()
        elseif v2 == 4 then
            v0.blackIn()
            runListLoad()
            pageScreen(0)
            v3 = succeedLoadGamedata()
            if v3 then
                runAutoLoad()
                cInitGame()
                switchScreen(0, "", 60)
                applyGamedata()
            else
                wait(10)
                v0.Config()
            end
        elseif v2 == 5 then
            pageScreen(0)
            wait(10)
            oCard.checkCard(logFlag)
            v0.Config()
        elseif not (v2 == 6) then
            if v2 == 7 then
                pageScreen(0)
                wait(10)
                systemOption.Option()
                v0.Config()
            elseif v2 == 8 then
                pageScreen(0)
                msgQuit()
                wait(10)
                cInitGame()
                fontClear()
                switchScreen(0, "", 60)
                memoryFlag = false
                run(cGetFileName("script", "snr_mainmenu"))
            end
        else
        end
        pageScreen(0)
        wait(10)
        if v1 == true then
            advPart(true)
        end
    end
    return v0
end
systemConfig = SystemConfig.new()
ObjectCard = {}
ObjectCard.new = function()
    local v0 = {}
    local v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19
    v0.layerNo = layerName.card1
    v1 = 1
    v2 = 0
    v0.cursorPositionInit = function()
        local v0 = 1
        v2 = 0
        v1 = v0
    end
    v0.show = function(p0, p1)
        local v1 = p0
        local v2
        v1 = string.gsub(v1, "card/crd_", "")
        v1 = 18000 + (string.gsub(v1, "_a.gim", ""))
        layerLoad(v0.layerNo, p0)
        layerAlpha(v0.layerNo, 0)
        layerPosition(v0.layerNo, -400, 40)
        layerMovePosition(v0.layerNo, 130, 40, 30)
        layerMoveAlpha(v0.layerNo, 100, 30)
        wait(30)
        vms(v1, "NONVOICE", p1)
        layerMovePosition(v0.layerNo, 480, 40, 30)
        layerMoveAlpha(v0.layerNo, 0, 30)
        wait(30)
        layerLoad(v0.layerNo, "")
        switchScreen(0, "", 30)
    end
    v0.showMiniIn = function(p0)
        layerLoad(v0.layerNo, p0)
        layerAlpha(v0.layerNo, 0)
        layerPosition(v0.layerNo, 270, 10)
        layerMovePosition(v0.layerNo, 270, 30, 20)
        layerMoveAlpha(v0.layerNo, 100, 20)
        wait(20)
    end
    v0.showMiniOut = function()
        layerMovePosition(v0.layerNo, 270, 40, 20)
        layerMoveAlpha(v0.layerNo, 0, 20)
        wait(20)
        layerLoad(v0.layerNo, "")
        switchScreen(0, "", 30)
    end
    v0.showRouteDetailIn = function(p0)
        layerLoad(v0.layerNo, p0)
        layerAlpha(v0.layerNo, 0)
        layerPosition(v0.layerNo, 130, 110)
        layerMovePosition(v0.layerNo, 130, 130, 10)
        layerMoveAlpha(v0.layerNo, 100, 10)
        wait(10)
    end
    v0.showRouteDetailOut = function()
        layerMovePosition(v0.layerNo, 130, 130, 5)
        layerMoveAlpha(v0.layerNo, 0, 5)
        wait(5)
        layerLoad(v0.layerNo, "")
    end
    v0.cardNgAnim = function()
        layerCopy(layerName.pose5, layerName.effectWhite)
        layerVisible(layerName.pose5, false)
        wait(1)
        keyPlaySE(seName.viewCard)
        layerVisible(layerName.pose5, true)
        layerBlend(layerName.pose5, "ADD")
        layerAlpha(layerName.pose5, 0)
        layerScale(layerName.pose5, 100, 100)
        layerRotate(layerName.pose5, 0, 0, 0)
        layerMoveAlpha(layerName.pose5, 80, 30)
        layerMoveScale(layerName.pose5, 0, 0, 30)
        layerMovePosition(layerName.pose5, 0, 80, 30)
        layerMoveRotate(layerName.pose5, 0, 0, 150, 30)
        wait(90)
        keyPlaySE(seName.arrowKey)
        layerScale(layerName.pose5, 100, 100)
        layerAlpha(layerName.pose5, 5)
        layerRotate(layerName.pose5, 0, 0, 0)
        layerPosition(layerName.pose5, 0, 0)
        layerMoveAlpha(layerName.pose5, 0, 60)
        wait(60)
        keyPlaySE(seName.arrowKey)
        layerAlpha(layerName.pose5, 10)
        layerMoveAlpha(layerName.pose5, 0, 60)
        wait(60)
        keyPlaySE(seName.arrowKey)
        layerAlpha(layerName.pose5, 5)
        layerMoveAlpha(layerName.pose5, 0, 60)
        wait(60)
        wait(1)
        layerLoad(layerName.pose5, "")
        switchScreen(0, "", 1)
        wait(1)
    end
    v0.mesNot = function()
        local v0
        comPoseLoad("po2_aya_f_2_e")
        v0 = math.random(1, 3)
        if v0 == 1 then
            vms(60, "AYA00000", "【彩野】「ごめんなさい……直哉くん……」")
            vms(61, "AYA00010", "【彩野】「今私たちが持っているカードでは、この場面をつくること、難しそう……」")
            vms(62, "NAO00000", "【直哉】「そうなんだ……」")
            vms(63, "NONVOICE", "……。")
        end
        if v0 == 2 then
            vms(64, "AYA00020", "【彩野】「あ……直哉くん……」")
            vms(65, "NAO00010", "【直哉】「ん、どうかした？」")
            vms(66, "AYA00030", "【彩野】「カードの種類、もしかしたら足りないかも」")
            vms(67, "NAO00020", "【直哉】「僕たちの今持っているカードだと、『あらすじ』がつくれない、ということかな？」")
            vms(68, "NONVOICE", "彩野さんはこくんと頷く。")
        end
        if v0 == 3 then
            vms(69, "AYA00040", "【彩野】「うーん……」")
            vms(70, "NONVOICE", "彩野さんは眉間に皺を寄せている。")
            vms(71, "NAO00030", "【直哉】「なにかあった？」")
            vms(72, "AYA00050", "【彩野】「この場面のあらすじを考えているんだけど、浮かばなくて」")
            vms(73, "NAO00040", "【直哉】「そっか。もうちょっとカードを集めてみた方がいいかも」")
            vms(74, "AYA00060", "【彩野】「うん……ごめんね」")
        end
        vms(75, "NONVOICE", "この場面をまとめるには、手持ちのカードが足りないみたいだ。")
        vms(76, "NONVOICE", "新しいカードを集めてみよう。")
        comPoseDelete()
    end
    v0.mesNot2 = function()
        comPoseLoad("po2_aya_f_2_e")
        vms(77, "AYA00040", "【彩野】「うーん……」")
        vms(78, "NONVOICE", "アヤノさんは眉間に皺を寄せている。")
        vms(79, "NONVOICE", "……。")
        vms(80, "NONVOICE", "……。彩野さんはカードをじっと目にしたまま動かない。")
        vms(81, "NONVOICE", "この場面を進行させるには、手持ちのカードが足りないようだ。")
        vms(82, "NONVOICE", "他の場面を展開させて、新しいカードを手に入れる必要があるかもしれない。")
        comPoseDelete()
    end
    v0.mesNG = function()
        local v1
        systemConfig.unsetConfigButton()
        comPoseLoad("po2_aya_f_1_a")
        v0.cardNgAnim()
        comPoseLoad("po2_aya_f_1_c")
        v1 = math.random(1, 3)
        if v1 == 1 then
            vms(83, "AYA00070", "【彩野】「ごめんなさい、直哉くん……。何も浮かばないの」")
            vms(84, "NONVOICE", "彩野さんはカードを見ると、残念そうに首を横に振った。")
        end
        if v1 == 2 then
            vms(85, "AYA00080", "【彩野】「…………」")
            vms(86, "NONVOICE", "彩野さんは僕からカードを受け取ると、じっとそれを見ている。")
            vms(87, "AYA00090", "【彩野】「……ごめんなさい。ちょっと、違うかも」")
        end
        if v1 == 3 then
            vms(88, "AYA00100", "【彩野】「このカードは……うーん」")
            vms(89, "NONVOICE", "彩野さんはしばらく考え込んだあと、僕の目を見ていった。")
            vms(90, "AYA00110", "【彩野】「直哉くん……他のカードを見せて貰っていい？」")
        end
        vms(91, "NONVOICE", "どうやら渡すべきカードはこれでは無いようだ。")
        systemConfig.setConfigButton()
    end
    v0.mesNG2 = function()
        local v1
        systemConfig.unsetConfigButton()
        comPoseLoad("po2_aya_f_1_a")
        v0.cardNgAnim()
        comPoseLoad("po2_aya_f_2_e")
        v1 = math.random(1, 3)
        if v1 == 1 then
            vms(92, "AYA00120", "【彩野】「やっぱり……。浮かばないみたい。ごめんなさい」")
            vms(93, "NONVOICE", "彩野さんはうつむきがちに言った。")
        end
        if v1 == 2 then
            vms(94, "AYA00130", "【彩野】「ごめんなさい……考えがまとまらなくて」")
            vms(95, "NONVOICE", "彩野さんは目を伏せていった。")
        end
        if v1 == 3 then
            vms(96, "AYA00140", "【彩野】「ごめんなさい……このカードはイメージしてたのとは違う感じがする」")
            vms(97, "NONVOICE", "彩野さんはカードをそっと元の場所に戻した。")
        end
        vms(98, "NONVOICE", "……違うカードを渡してみよう。")
        systemConfig.setConfigButton()
    end
    v0.mesAnswer = function()
        local v0
        v0 = math.random(1, 3)
        if v0 == 1 then
            vms(99, "AYA00150", "【彩野】「ありがとう」")
        end
        if v0 == 2 then
            vms(100, "AYA00160", "【彩野】「ありがとう、直哉くん」")
        end
        if v0 == 3 then
            vms(101, "AYA00170", "【彩野】「ありがとう」")
        end
    end
    v0.mesNotStoryLine = function()
        vms(102, "NONVOICE", "○このあらすじより『前の場面のあらすじ』が作成されていません。_rあらすじは物語の先頭から順番に作成する必要があります。")
        wait(5)
    end
    v0.cancelCard = function()
        vms(103, "NONVOICE", "カード選択を中止しました。")
        wait(5)
    end
    v0.cardAnswerTrue = function()
        systemConfig.unsetConfigButton()
        comPoseLoad("po2_aya_f_1_a")
        wait(1)
        layerCopy(layerName.pose4, layerName.bg_1_a_0)
        layerCopy(layerName.pose5, layerName.effectWhite)
        layerVisible(layerName.pose4, false)
        layerVisible(layerName.pose5, false)
        wait(1)
        keyPlaySE(seName.viewCard)
        layerVisible(layerName.pose5, true)
        layerBlend(layerName.pose5, "ADD")
        layerAlpha(layerName.pose5, 0)
        layerScale(layerName.pose5, 100, 100)
        layerRotate(layerName.pose5, 0, 0, 0)
        layerMoveAlpha(layerName.pose5, 80, 30)
        layerMoveScale(layerName.pose5, 0, 0, 30)
        layerMoveRotate(layerName.pose5, 0, 0, 100, 30)
        wait(90)
        keyPlaySE(seName.arrowKey)
        layerScale(layerName.pose5, 100, 100)
        layerRotate(layerName.pose5, 0, 0, 0)
        layerAlpha(layerName.pose5, 5)
        layerMoveAlpha(layerName.pose5, 0, 60)
        wait(60)
        keyPlaySE(seName.arrowKey)
        layerAlpha(layerName.pose5, 10)
        layerMoveAlpha(layerName.pose5, 0, 60)
        wait(60)
        keyPlaySE(seName.getCard)
        layerVisible(layerName.pose4, true)
        layerVisible(layerName.pose5, true)
        layerScale(layerName.pose4, 100, 100)
        layerAlpha(layerName.pose4, 100)
        layerAlpha(layerName.pose5, 80)
        layerMoveScale(layerName.pose4, 110, 110, 50)
        layerMoveAlpha(layerName.pose4, 0, 50)
        layerMoveAlpha(layerName.pose5, 0, 30)
        wait(60)
        layerLoad(layerName.pose4, "")
        layerLoad(layerName.pose5, "")
        switchScreen(0, "", 1)
        wait(1)
        systemConfig.setConfigButton()
        comPoseLoad("po2_aya_f_1_b")
        v0.mesAnswer()
    end
    v0.cardAnswerNonvoiceTrue = function()
        systemConfig.unsetConfigButton()
        comPoseLoad("po2_aya_f_1_a")
        wait(1)
        layerCopy(layerName.pose4, layerName.bg_1_a_0)
        layerCopy(layerName.pose5, layerName.effectWhite)
        layerVisible(layerName.pose4, false)
        layerVisible(layerName.pose5, false)
        wait(1)
        keyPlaySE(seName.viewCard)
        layerVisible(layerName.pose5, true)
        layerBlend(layerName.pose5, "ADD")
        layerAlpha(layerName.pose5, 0)
        layerScale(layerName.pose5, 100, 100)
        layerRotate(layerName.pose5, 0, 0, 0)
        layerMoveAlpha(layerName.pose5, 80, 30)
        layerMoveScale(layerName.pose5, 0, 0, 30)
        layerMoveRotate(layerName.pose5, 0, 0, 100, 30)
        wait(90)
        keyPlaySE(seName.arrowKey)
        layerScale(layerName.pose5, 100, 100)
        layerRotate(layerName.pose5, 0, 0, 0)
        layerAlpha(layerName.pose5, 5)
        layerMoveAlpha(layerName.pose5, 0, 60)
        wait(60)
        keyPlaySE(seName.arrowKey)
        layerAlpha(layerName.pose5, 10)
        layerMoveAlpha(layerName.pose5, 0, 60)
        wait(60)
        keyPlaySE(seName.getCard)
        layerVisible(layerName.pose4, true)
        layerVisible(layerName.pose5, true)
        layerScale(layerName.pose4, 100, 100)
        layerAlpha(layerName.pose4, 100)
        layerAlpha(layerName.pose5, 80)
        layerMoveScale(layerName.pose4, 110, 110, 50)
        layerMoveAlpha(layerName.pose4, 0, 50)
        layerMoveAlpha(layerName.pose5, 0, 30)
        wait(60)
        layerLoad(layerName.pose4, "")
        layerLoad(layerName.pose5, "")
        switchScreen(0, "", 1)
        wait(1)
        systemConfig.setConfigButton()
    end
    v0.viewAnswer = function()
        local v0 = ""
        local v1
        if not (nowPlayBgmFileName == "") then
            v0 = nowPlayBgmFileName
        end
        cStopBGMWrap(0)
        wait(60)
        cPlayOneshotMusic(cGetFileName("mus", "mus_1"))
        comEffectYellowIn(120)
        wait(260)
        if not (v0 == "") then
            cPlayBGMWrap(v0)
        end
    end
    v0.selectCardObj = function()
        local v1, v2, v3, v4
        advPart(false)
        wait(1)
        pageScreen(1)
        v0.cardModeInit()
        v1 = myCardMax + 1
        v2 = myCardMax + 2
        v3 = v0.cardModeSet(v1, v2)
        v4 = v0.cardModeSelect(v3, v1, v2, 0)
        v0.cardModeExit()
        pageScreen(0)
        wait(1)
        advPart(true)
        if v4 == -1 then
            return v4
        else
            return v3[v4].cid
        end
    end
    v0.selectCardNotCancelObj = function()
        local v1, v2, v3, v4
        advPart(false)
        wait(1)
        pageScreen(1)
        v0.cardModeNotCancelInit()
        v1 = myCardMax + 1
        v2 = myCardMax + 2
        v3 = v0.cardModeSet(v1, v2)
        v4 = v0.cardModeSelect(v3, v1, v2, 2)
        v0.cardModeExit()
        pageScreen(0)
        wait(1)
        advPart(true)
        if v4 == -1 then
            return v4
        else
            return v3[v4].cid
        end
    end
    v0.checkCard = function()
        local v1, v2, v3
        pageScreen(1)
        v0.cardModeInit()
        v1 = myCardMax + 1
        v2 = myCardMax + 2
        v3 = v0.cardModeSet
        v0.cardModeSelect(v3(v1, v2), v1, v2, 1)
        v0.cardModeExit()
        pageScreen(0)
        wait(1)
    end
    v0.drawSceneName = function(p0, p1, p2)
        local v0 = plotTitle[p0]
        local v1, v2, v3, v4
        if cardIDFlag == true then
            v1 = "（"
            v2 = p0
            v3 = "）"
            v4 = v0
            v0 = v1 .. v2 .. v3 .. v4
        end
        v0 = string.gsub(v0, "\n", "")
        cfontPrint(0, p1, p2, 16777215, 6684672, v0)
    end
    v0.cardModeInit = function()
        local v0
        wait(1)
        fontClear()
        layerCopy(0, backLayerName.sys_11_a)
        layerAlpha(0, 0)
        v0 = myCardMax + 3
        layerCopy(v0, backLayerName.sys_11_e)
        layerPosition(v0, 412, 253)
        layerAlpha(v0, 0)
        layerMoveAlpha(0, 100, 20)
        layerMoveAlpha(v0, 100, 20)
        wait(20)
    end
    v0.cardModeNotCancelInit = function()
        wait(1)
        fontClear()
        layerCopy(0, backLayerName.sys_11_a)
        layerAlpha(0, 0)
        layerMoveAlpha(0, 100, 20)
        wait(20)
    end
    v0.cardModeExit = function()
        local v0 = 0
        local v1 = 200
        local v2 = 1
        local i0
        for i0 = v0, v1, v2 do
            layerMoveAlpha(i0, 0, 60)
        end
        wait(60)
        fontClear()
        v0 = 0
        v1 = 200
        v2 = 1
        for i0 = v0, v1, v2 do
            layerLoad(i0, "")
        end
    end
    v0.cardModeSelect = function(p0, p1, p2, p3)
        local v3 = v1
        local v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19
        v4 = v2 * 15
        v3 = v3 + v4
        v4 = v1
        v5 = v2
        v6 = v3
        v7 = false
        v8 = false
        v9 = 0
        v10 = 260
        v11 = 1
        v12 = 1
        while true do
            if v7 == false then
                if not (p3 == 2) then
                    v13 = pressButton("CROSS")
                    if v13 == true then
                        if v12 == 0 then
                            keyPlaySE(seName.cross)
                            v3 = -1
                            break
                        end
                    else
                        v12 = 0
                    end
                end
                if not (v4 == v1) then
                    v4 = v1
                end
                if not (v5 == v2) then
                    v5 = v2
                end
                v13 = pressButton("RIGHT")
                if v13 == true then
                    v13 = v1 + 1
                    v1 = v13
                    v7 = true
                end
                v13 = pressButton("LEFT")
                if v13 == true then
                    v13 = v1 - 1
                    v1 = v13
                    v7 = true
                end
                v13 = pressButton("DOWN")
                if v13 == true then
                    v13 = v2 + 1
                    v2 = v13
                    v7 = true
                end
                v13 = pressButton("UP")
                if v13 == true then
                    v13 = v2 - 1
                    v2 = v13
                    v7 = true
                end
                if 15 < v1 then
                    v1 = 1
                    v13 = v2 + 1
                    v2 = v13
                    if 12 < v2 then
                        v2 = 0
                    end
                end
                if v1 < 1 then
                    v1 = 15
                    v13 = v2 - 1
                    v2 = v13
                    if v2 < 0 then
                        v2 = 12
                    end
                end
                if 12 < v2 then
                    v2 = 0
                    v13 = v1 + 1
                    v1 = v13
                    if 15 < v1 then
                        v1 = 1
                    end
                end
                if v2 < 0 then
                    v2 = 12
                    v13 = v1 - 1
                    v1 = v13
                    if v1 < 1 then
                        v1 = 15
                    end
                end
            end
            if (v7 == false) and (not (p3 == 1)) then
                v13 = pressButton("CIRCLE")
                if v13 == true then
                    if v11 == 0 then
                        if p0[v3].visible == true then
                            keyPlaySE(seName.circle)
                            layerVisible(p1, false)
                            layerMovePosition(v3, 260, -100, 50)
                            layerMoveRotate(v3, 0, -100, 360, 50)
                            v14 = v3
                            layerMoveScale(v14, 200, 200, 50)
                            wait(60)
                            break
                        end
                    end
                else
                    v11 = 0
                end
            end
            if v7 == true then
                fontClear()
                v13 = v1
                v15 = v2 * 15
                v3 = v13 + v15
                keyPlaySE(seName.arrowKey)
                layerLoad(p2, "")
                v9 = 0
                if p0[v3].visible == true then
                    v0.drawSceneName(p0[v3].cid, 10, 253)
                    layerCopy(v3, backLayerName.sys_11_c)
                    layerClip(v3, p0[v3].x, p0[v3].y, (p0[v3].x + 26), (p0[v3].y + 15))
                end
                v13 = v5 * 15
                v6 = v4 + v13
                layerCopy(v6, backLayerName.sys_11_b)
                layerClip(v6, p0[v6].x, p0[v6].y, (p0[v6].x + 26), (p0[v6].y + 15))
                if not (p0[v6].visible == true) then
                    layerVisible(v6, false)
                end
                layerPosition(p1, p0[v3].x, (p0[v3].y - 2))
                wait(2)
                v7 = false
            end
            if (p0[v3].visible == true) and (v9 <= 5) then
                if 5 <= v9 then
                    v19 = p2
                    v18 = "card/crd_"
                    v16 = p0[v3].cid
                    layerLoadAsync(1, v19, v18 .. v16 .. "_a.gim")
                    v8 = true
                end
                v13 = v9 + 1
                if 6 < v13 then
                    v9 = 6
                else
                    v9 = v9 + 1
                end
            end
            if v8 == true then
                v13 = layerIsLoad(p2)
                if v13 == true then
                    layerVisible(p2, true)
                    if 220 < p0[v3].x then
                        layerPosition(p2, 10, 90)
                        layerMovePosition(p2, 10, 100, 5)
                    else
                        layerPosition(p2, 260, 90)
                        layerMovePosition(p2, 260, 100, 5)
                    end
                    layerAlpha(p2, 0)
                    v15 = p2
                    layerMoveAlpha(v15, 100, 5)
                    v8 = false
                end
            end
            wait(2)
        end
        return v3
    end
    v0.cardModeSet = function(p0, p1)
        local v3 = v1
        local v4, v5, v6, v7, v8, v9, i6, v10, v11, v12, v13, v14, v15, v16
        v4 = v2 * 15
        v3 = v3 + v4
        v4 = {}
        v5 = 1
        v6 = 1
        v7 = 1
        v8 = myCardMax
        v9 = 1
        for i6 = v7, v8, v9 do
            v10 = 0
            if v5 <= 5 then
                v11 = (v5 - 1) * 30
                v10 = v11 + 13
            elseif v5 <= 10 then
                v11 = (v5 - 1) * 30
                v10 = v11 + 17
            else
                v11 = (v5 - 1) * 30
                v10 = v11 + 21
            end
            v11 = true
            v12 = cardSort[i6][1]
            if gameSave.myCard[v12].hold == -1 then
                v11 = false
            end
            v4[i6] = {}
            v4[i6].x = v10
            v14 = (v6 * 16) + 30
            v4[i6].y = v14
            v4[i6].cid = v12
            v4[i6].visible = v11
            if i6 == v3 then
                layerCopy(i6, backLayerName.sys_11_c)
            else
                layerCopy(i6, backLayerName.sys_11_b)
            end
            layerPosition(i6, 240, 272)
            layerAlpha(i6, 0)
            layerClip(i6, v4[i6].x, v4[i6].y, (v4[i6].x + 26), (v4[i6].y + 15))
            layerVisible(i6, v4[i6].visible)
            v5 = v5 + 1
            if 15 < v5 then
                v5 = 1
                v6 = v6 + 1
            end
        end
        v7 = 1
        v8 = myCardMax
        v9 = 1
        for i6 = v7, v8, v9 do
            v13 = v4[i6].y - 2
            v14 = (math.random(6, 12)) * 5
            layerMovePosition(i6, v4[i6].x, v13, v14)
            layerMoveAlpha(i6, 100, 60)
        end
        wait(60)
        layerCopy(p0, backLayerName.sys_11_d)
        layerPosition(p0, v4[v3].x, (v4[v3].y - 2))
        if v4[v3].visible == true then
            v0.drawSceneName(v4[v3].cid, 10, 253)
        end
        return v4
    end
    return v0
end
oCard = ObjectCard.new()
keyPlaySE = function(p0)
    stopSE(p0)
    playSE(p0, false)
end
startLoading = function()
    layerVisible(layerName.sys_1_j, true)
    layerPosition(layerName.sys_1_j, 300, 230)
    layerAnime(layerName.sys_1_j, 10, true)
end
endLoading = function()
    layerVisible(layerName.sys_1_j, false)
    wait(1)
end
keyWait = function(p0)
    local v0 = 0
    local v1 = 1
    local v2
    while true do
        v2 = pressButton("CIRCLE")
        if not (v2 == true) then
            v1 = 0
        end
        v2 = pressButton("CIRCLE")
        if v2 == true then
            if v1 == 0 then
                break
            end
        end
        v2 = p0 / 3
        if v2 <= v0 then
            break
        else
            wait(1)
        end
        v0 = v0 + 1
    end
end
comLayerLoadFalse = function(p0, p1, p2)
    if not (p2) then
        p2 = 0
    end
    layerLoadAsync(p2, p0, p1)
end
main = function()
    local v0 = layerLoad
    local v1, v2, v3, g3, v4
    v0(0, cGetFileName("sysgim", "IPL01"))
    layerAlpha(0, 0)
    layerLoad(1, cGetFileName("sysgim", "IPL02"))
    layerAlpha(1, 0)
    layerLoad(2, cGetFileName("sysgim", "sys_1_a"))
    layerAlpha(2, 0)
    layerLoad(3, cGetFileName("sysgim", "autosave"))
    layerAlpha(3, 0)
    fontLoad(0, "pgf/LXGWWenKai-Regular.pgf")
    -- fontLoad(1, "pgf/tsukuminpro_e_17.pgf")
    fontLoad(1, "pgf/tsukuminpro_e_09.pgf")
    comLayerLoadFalse(layerName.sys_1_j, cGetFileName("sysgim", "sys_1_j"))
    comLayerLoadFalse(layerName.titleBG, cGetFileName("bg", "bg_4_a_0"))
    comLayerLoadFalse(layerName.title_01_a, cGetFileName("sysgim", "title_01_a"))
    comLayerLoadFalse(layerName.title_02_a, cGetFileName("sysgim", "title_02_a"))
    comLayerLoadFalse(layerName.title_03_a, cGetFileName("sysgim", "title_03_a"))
    comLayerLoadFalse(layerName.title_04_a, cGetFileName("sysgim", "title_04_a"))
    comLayerLoadFalse(layerName.title_05_a, cGetFileName("sysgim", "title_05_a"))
    comLayerLoadFalse(layerName.title_06_a, cGetFileName("sysgim", "title_06_a"))
    comLayerLoadFalse(layerName.title_07_a, cGetFileName("sysgim", "title_07_a"))
    comLayerLoadFalse(layerName.title_08_a, cGetFileName("sysgim", "title_08_a"))
    comLayerLoadFalse(layerName.title_09_a, cGetFileName("sysgim", "title_09_a"))
    comLayerLoadFalse(layerName.title_10_a, cGetFileName("sysgim", "title_10_a"))
    comLayerLoadFalse(layerName.title_11_a, cGetFileName("sysgim", "title_11_a"))
    comLayerLoadFalse(layerName.title_12_a, cGetFileName("sysgim", "title_12_a"))
    comLayerLoadFalse(layerName.title_13_a, cGetFileName("sysgim", "title_13_a"))
    loadSE(seName.arrowKey, cGetFileName("se", "se_154"))
    loadSE(seName.circle, cGetFileName("se", "se_37"))
    loadSE(seName.cross, cGetFileName("se", "se_40"))
    loadSE(seName.getCard, cGetFileName("se", "se_152"))
    loadSE(seName.viewCard, cGetFileName("se", "se_28"))
    comLayerLoadFalse(201, "sysgim/prg_story_message.gim")
    layerPosition(201, 0, 162)
    comLayerLoadFalse(231, "sysgim/prg_story_message.gim", 1)
    comLayerLoadFalse(202, "sysgim/prg_cursor_1.gim")
    comLayerLoadFalse(203, "sysgim/prg_auto_1.gim")
    layerPosition(203, 449, 261)
    comLayerLoadFalse(layerName.effectBlack, cGetFileName("event", "eve_0_b"))
    comLayerLoadFalse(layerName.effectWhite, cGetFileName("event", "eve_0_a"))
    comLayerLoadFalse(layerName.effectYellow, cGetFileName("event", "eve_0_c"))
    comLayerLoadFalse(layerName.sys_4_a, cGetFileName("sysgim", "sys_4_a"))
    comLayerLoadFalse(layerName.sys_4_b, cGetFileName("sysgim", "sys_4_b"))
    comLayerLoadFalse(layerName.bg_1_a_0, cGetFileName("bg", "bg_1_a_0"))
    comLayerLoadFalse(layerName.po1_aya_f_1_a, cGetFileName("pose", "po1_aya_f_1_a"))
    comLayerLoadFalse(layerName.sys_12_a, cGetFileName("sysgim", "sys_12_a"))
    comLayerLoadFalse(layerName.sys_12_b, cGetFileName("sysgim", "sys_12_b"))
    comLayerLoadFalse(layerName.sys_12_c, cGetFileName("sysgim", "sys_12_c"))
    comLayerLoadFalse(layerName.sys_12_d, cGetFileName("sysgim", "sys_12_d"))
    comLayerLoadFalse(layerName.sys_12_e, cGetFileName("sysgim", "sys_12_e"))
    comLayerLoadFalse(layerName.sys_12_f, cGetFileName("sysgim", "sys_12_f"))
    comLayerLoadFalse(layerName.sys_12_g, cGetFileName("sysgim", "sys_12_g"))
    comLayerLoadFalse(layerName.sys_13_a, cGetFileName("sysgim", "sys_13_a"))
    comLayerLoadFalse(layerName.sys_13_b, cGetFileName("sysgim", "sys_13_b"))
    comLayerLoadFalse(layerName.sys_13_c, cGetFileName("sysgim", "sys_13_c"))
    comLayerLoadFalse(layerName.sys_13_d, cGetFileName("sysgim", "sys_13_d"))
    comLayerLoadFalse(layerName.sys_5_e, cGetFileName("sysgim", "sys_5_e"))
    comLayerLoadFalse(layerName.plot_1_a, cGetFileName("plot", "plot_1_a"))
    comLayerLoadFalse(layerName.plot_2_a, cGetFileName("plot", "plot_2_a"))
    comLayerLoadFalse(layerName.plot_3_a, cGetFileName("plot", "plot_3_a"))
    comLayerLoadFalse(layerName.plot_4_a, cGetFileName("plot", "plot_4_a"))
    comLayerLoadFalse(layerName.scene_1_a, cGetFileName("scene", "scene_1_a"))
    comLayerLoadFalse(layerName.scene_2_a, cGetFileName("scene", "scene_2_a"))
    comLayerLoadFalse(layerName.sys_7_a, cGetFileName("sysgim", "sys_7_a"))
    comLayerLoadFalse(layerName.sys_8_a, cGetFileName("sysgim", "sys_8_a"))
    comLayerLoadFalse(layerName.sys_9_a, cGetFileName("sysgim", "sys_9_a"))
    comLayerLoadFalse(layerName.sys_2_a, cGetFileName("sysgim", "sys_2_a"))
    comLayerLoadFalse(layerName.sys_2_b, cGetFileName("sysgim", "sys_2_b"))
    comLayerLoadFalse(layerName.sys_2_c, cGetFileName("sysgim", "sys_2_c"))
    comLayerLoadFalse(layerName.sys_3_a, cGetFileName("sysgim", "sys_3_a"))
    comLayerLoadFalse(layerName.sys_2_d, cGetFileName("sysgim", "sys_2_d"))
    comLayerLoadFalse(layerName.sel_map_0_a, cGetFileName("select", "sel_map_0_a"))
    comLayerLoadFalse(layerName.sel_map_1_a, cGetFileName("select", "sel_map_1_a"))
    comLayerLoadFalse(layerName.sel_map_2_a, cGetFileName("select", "sel_map_2_a"))
    v0 = comLayerLoadFalse
    v1 = layerName.sel_map_2_b
    v2 = "sel_map_2_b"
    v0(v1, cGetFileName("select", v2))
    v0, v1, v3 = pairs(backLayerName)
    for g3, v2 in v0, v1, v3 do
        if (not (v2 == 237)) and (not (v2 == 236)) then
            comLayerLoadFalse(backLayerName[g3], cGetFileName("sysgim", g3), 1)
        end
    end
    comLayerLoadFalse(backLayerName.black, cGetFileName("event", "eve_0_b"), 1)
    layerMoveAlpha(0, 100, 120)
    wait(120)
    keyWait(180)
    layerMoveAlpha(0, 0, 120)
    layerMoveAlpha(1, 100, 120)
    wait(120)
    keyWait(180)
    layerMoveAlpha(1, 0, 120)
    wait(120)
    layerMoveAlpha(2, 100, 120)
    wait(120)
    keyWait(180)
    layerMoveAlpha(2, 0, 120)
    wait(120)
    layerMoveAlpha(3, 100, 120)
    wait(120)
    keyWait(180)
    layerMoveAlpha(3, 0, 120)
    wait(120)
    startLoading()
    waitLoading()
    wait(60)
    endLoading()
    runAutoLoad()
    cInitGame()
    initComplete = 1
    if debagFlag == true then
        run(cGetFileName("script", "snr_lib"))
    end
    run(cGetFileName("script", "snr_mainmenu"))
    quit()
end
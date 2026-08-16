main = function()
    comSectionCardStart(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    vms(1670, "NONVOICE", "≪この場面のカードは、サクラの日記を見て彩野が作成しました。そのため、直哉と彩野によるカード選択シーンはありません≫")
    vms(1671, "NONVOICE", "【（ヒント）】セクション５を読み進めるには、彩野の言葉に耳をかたむけ、ストーリーモードでカードを選択してください。正解カードを選んでいくことで、先に進むことができます。")
    comSectionCardEnd(gameSave.fragmentDoSceneId, gameSave.fragmentDoCardId)
    run(cGetFileName("script", "snr_fragment_main"))
    quit()
end

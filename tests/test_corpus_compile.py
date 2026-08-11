def test_all_229_corpus_files_produce_compilable_output(corpus_dir, decompiled):
    from pyluadec import oracle
    failures = []
    files = sorted(corpus_dir.glob("*.lua"))
    for f in files:
        try:
            oracle.compile_source(decompiled(f).source)
        except Exception as e:                                    # noqa: BLE001
            failures.append((f.name, str(e)[:200]))
    assert len(files) == 229
    assert failures == [], f"{len(failures)} files failed: {failures[:5]}"

def test_all_229_corpus_files_produce_compilable_output(corpus_dir):
    from pyluadec import oracle
    from pyluadec.pipeline import decompile_file
    failures = []
    files = sorted(corpus_dir.glob("*.lua"))
    for f in files:
        try:
            oracle.compile_source(decompile_file(f).source)
        except Exception as e:                                    # noqa: BLE001
            failures.append((f.name, str(e)[:200]))
    assert len(files) == 229
    assert failures == [], f"{len(failures)} files failed: {failures[:5]}"

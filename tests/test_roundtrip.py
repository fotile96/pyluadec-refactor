from pathlib import Path

BUILD = Path(__file__).resolve().parents[1] / "build"

def test_corpus_roundtrip_byte_identical(corpus_dir, tmp_path):
    from scripts.roundtrip_sz4 import roundtrip_file
    bad = [f.name for f in sorted(corpus_dir.glob("*.lua"))
           if not roundtrip_file(BUILD / "luac_sz4", f, tmp_path)]
    assert bad == []

import json
from pathlib import Path

GOLDEN = Path(__file__).resolve().parents[1] / "corpus" / "golden"

def test_golden_complete():
    manifest = json.loads((GOLDEN / "manifest.json").read_text())
    assert len(manifest) == 229
    for name in manifest:
        assert (GOLDEN / "proto_dump" / (name + ".json.gz")).exists()
        assert (GOLDEN / "listing" / (name + ".txt")).exists()

def test_golden_matches_corpus_hashes(corpus_dir):
    import hashlib
    manifest = json.loads((GOLDEN / "manifest.json").read_text())
    for name, meta in manifest.items():
        blob = (corpus_dir / name).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == meta["sha256"], name

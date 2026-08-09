import gzip
import json
from pathlib import Path

GOLDEN = Path(__file__).resolve().parents[1] / "corpus" / "golden"

# Top-level keys the old bridge's proto dict always exposes (verified uniform
# across all 229 captured files at capture time).
PROTO_KEYS = {"code", "constants", "is_vararg", "numparams", "subprotos", "upvalues"}

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

def test_golden_artifacts_valid():
    """Guard against silent corruption of the read-only golden archive: every
    proto_dump/*.json.gz must be valid gzip+JSON with the expected top-level
    proto keys, and every listing/*.txt must be non-empty and start with the
    luac listing header ("main <..."). Existence checks alone (see
    test_golden_complete) would not catch a zero-byte or truncated file.
    """
    manifest = json.loads((GOLDEN / "manifest.json").read_text())
    for name in manifest:
        with gzip.open(GOLDEN / "proto_dump" / (name + ".json.gz"), "rt", encoding="utf-8") as fh:
            dump = json.load(fh)
        assert set(dump.keys()) == PROTO_KEYS, name

        listing = (GOLDEN / "listing" / (name + ".txt")).read_text(encoding="utf-8")
        assert listing, name
        assert listing.startswith("\nmain <") or listing.startswith("main <"), name

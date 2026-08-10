import json
from pathlib import Path

def test_single_file_parity(corpus_dir):
    from scripts.compare_bridge_golden import compare_file
    assert compare_file("snr_crd_1.lua", corpus_dir) == []

def test_full_corpus_parity(corpus_dir):
    from scripts.compare_bridge_golden import compare_corpus
    report = compare_corpus(corpus_dir)
    unexpected = [d for d in report if d["verdict"] == "unexpected"]
    assert unexpected == [], f"{len(unexpected)} unexpected discrepancies"

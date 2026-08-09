import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def corpus_dir() -> Path:
    p = os.environ.get("PYLUADEC_CORPUS_DIR")
    if not p or not Path(p).is_dir():
        pytest.skip("PYLUADEC_CORPUS_DIR not set or missing (corpus tests skipped)")
    return Path(p)

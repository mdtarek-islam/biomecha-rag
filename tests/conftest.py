from pathlib import Path

import pytest

SAMPLE_CORPUS = Path(__file__).resolve().parents[1] / "data" / "sample_corpus"


@pytest.fixture
def sample_corpus() -> Path:
    return SAMPLE_CORPUS

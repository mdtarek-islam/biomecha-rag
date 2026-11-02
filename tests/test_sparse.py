import pytest

from biomecha_rag.sparse import BM25Encoder, token_index

DOCS = [
    "badminton smash racket speed forearm pronation",
    "swimming drag streamlined body position",
    "sprint start horizontal force ground contact",
]


def _dot(q, d):
    dv = dict(zip(d.indices, d.values))
    return sum(v * dv.get(i, 0.0) for i, v in zip(q.indices, q.values))


def test_token_index_is_stable_32_bit():
    assert token_index("smash") == token_index("smash")
    assert 0 <= token_index("smash") < 2**32


def test_query_weights_sum_to_one_and_skip_unknown_terms():
    enc = BM25Encoder().fit(DOCS)
    q = enc.encode_query("smash drag unknownterm")
    assert len(q.indices) == 2
    assert sum(q.values) == pytest.approx(1.0)


def test_sparse_dot_ranks_matching_document_first():
    enc = BM25Encoder().fit(DOCS)
    q = enc.encode_query("forearm pronation in the smash")
    scores = [_dot(q, enc.encode_document(d)) for d in DOCS]
    assert scores.index(max(scores)) == 0
    assert scores[1] == 0.0


def test_rank_bm25_scores_agree_on_top_document():
    enc = BM25Encoder().fit(DOCS)
    scores = enc.scores("streamlined drag")
    assert scores.index(max(scores)) == 1


def test_dump_and_load_round_trip(tmp_path):
    enc = BM25Encoder().fit(DOCS)
    path = tmp_path / "bm25.json"
    enc.dump(path)
    loaded = BM25Encoder.load(path)
    assert loaded.encode_query("smash drag") == enc.encode_query("smash drag")
    assert loaded.encode_document(DOCS[0]) == enc.encode_document(DOCS[0])


def test_unfitted_encoder_raises():
    with pytest.raises(RuntimeError):
        BM25Encoder().encode_query("smash")


def test_empty_corpus_rejected():
    with pytest.raises(ValueError):
        BM25Encoder().fit(["", "the and"])

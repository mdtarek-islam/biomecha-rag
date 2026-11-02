import math

import pytest

from biomecha_rag.embeddings import BGE_QUERY_INSTRUCTION, HashingEmbedder, HFInferenceEmbedder
from biomecha_rag.reranker import HFCrossEncoderReranker, LexicalReranker
from biomecha_rag.types import Chunk, ScoredChunk


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return FakeResponse(self.payload(json) if callable(self.payload) else self.payload)


def _cand(cid, text, score=0.0):
    return ScoredChunk(Chunk(cid, cid.split("::")[0], text), score)


def test_lexical_reranker_orders_by_query_coverage():
    cands = [
        _cand("a::0", "swimming drag"),
        _cand("b::0", "smash racket forearm pronation"),
        _cand("c::0", "smash speed"),
    ]
    out = LexicalReranker().rerank("smash forearm pronation", cands, top_n=2)
    assert [c.chunk.chunk_id for c in out] == ["b::0", "c::0"]
    assert out[0].score == pytest.approx(1.0)


def test_lexical_reranker_ties_keep_retrieval_order():
    cands = [_cand("z::0", "smash"), _cand("a::0", "smash")]
    out = LexicalReranker().rerank("smash", cands, top_n=2)
    assert [c.chunk.chunk_id for c in out] == ["z::0", "a::0"]


def test_hf_reranker_maps_indices_and_sorts():
    session = FakeSession([{"index": 0, "score": 0.1}, {"index": 1, "score": 0.9}])
    reranker = HFCrossEncoderReranker("https://rerank.example", "tok", session=session)
    out = reranker.rerank("q", [_cand("a::0", "x"), _cand("b::0", "y")], top_n=1)
    assert [c.chunk.chunk_id for c in out] == ["b::0"]
    call = session.calls[0]
    assert call["url"] == "https://rerank.example/rerank"
    assert call["json"]["texts"] == ["x", "y"]
    assert call["headers"]["Authorization"] == "Bearer tok"


def test_hf_reranker_skips_call_on_empty_candidates():
    session = FakeSession([])
    assert HFCrossEncoderReranker("https://r", "", session=session).rerank("q", [], 3) == []
    assert session.calls == []


def test_hashing_embedder_is_deterministic_and_normalised():
    emb = HashingEmbedder(dimension=64)
    a = emb.embed_query("badminton smash")
    assert a == HashingEmbedder(dimension=64).embed_query("badminton smash")
    assert math.isclose(sum(v * v for v in a), 1.0)
    assert len(emb.embed_documents(["x", "y"])) == 2


def test_hf_embedder_prefixes_query_and_batches_documents():
    session = FakeSession(lambda body: [[0.0, 1.0] for _ in body["inputs"]])
    emb = HFInferenceEmbedder("https://embed.example/", "", batch_size=2, session=session)
    assert emb.embed_documents(["a", "b", "c"]) == [[0.0, 1.0]] * 3
    assert len(session.calls) == 2
    emb.embed_query("smash")
    assert session.calls[-1]["json"]["inputs"] == [BGE_QUERY_INSTRUCTION + "smash"]
    assert "Authorization" not in session.calls[-1]["headers"]


def test_hf_embedder_requires_url():
    with pytest.raises(ValueError):
        HFInferenceEmbedder("", "tok")

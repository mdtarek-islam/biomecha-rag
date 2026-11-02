from types import SimpleNamespace

import pytest

from biomecha_rag.corpus import chunk_documents, load_documents
from biomecha_rag.embeddings import HashingEmbedder
from biomecha_rag.retriever import (
    HybridRetriever,
    InMemoryHybridStore,
    PineconeHybridStore,
    hybrid_scale,
)
from biomecha_rag.sparse import BM25Encoder
from biomecha_rag.types import Chunk, SparseVector

DENSE_WIN = Chunk("dense::0", "dense", "dense winner")
SPARSE_WIN = Chunk("sparse::0", "sparse", "sparse winner")


def _store():
    store = InMemoryHybridStore()
    store.upsert(
        [DENSE_WIN, SPARSE_WIN],
        [[1.0, 0.0], [0.2, 0.0]],
        [SparseVector([7], [0.1]), SparseVector([7], [1.0])],
    )
    return store


@pytest.mark.parametrize(
    "alpha,expected",
    [(1.0, "dense::0"), (0.0, "sparse::0"), (0.8, "dense::0"), (0.2, "sparse::0")],
)
def test_alpha_controls_fusion_order(alpha, expected):
    dense, sparse = hybrid_scale([1.0, 0.0], SparseVector([7], [1.0]), alpha)
    results = _store().query(dense, sparse, top_k=2)
    assert results[0].chunk.chunk_id == expected
    assert results[0].score >= results[1].score


def test_hybrid_scale_is_convex_combination():
    dense, sparse = hybrid_scale([2.0], SparseVector([1], [4.0]), 0.25)
    assert dense == [0.5]
    assert sparse.values == [3.0]


def test_hybrid_scale_rejects_bad_alpha():
    with pytest.raises(ValueError):
        hybrid_scale([1.0], SparseVector([], []), 1.5)


def test_ties_break_by_chunk_id():
    store = InMemoryHybridStore()
    a, b = Chunk("b::0", "b", "x"), Chunk("a::0", "a", "x")
    store.upsert([a, b], [[1.0], [1.0]], [SparseVector([], []), SparseVector([], [])])
    ids = [r.chunk.chunk_id for r in store.query([1.0], SparseVector([], []), 2)]
    assert ids == ["a::0", "b::0"]


def test_in_memory_retriever_finds_topic_in_sample_corpus(sample_corpus):
    chunks = chunk_documents(load_documents(sample_corpus))
    encoder = BM25Encoder().fit([c.text for c in chunks])
    retriever = HybridRetriever(HashingEmbedder(), encoder, InMemoryHybridStore(), alpha=0.5)
    assert retriever.index(chunks) == len(chunks)
    top = retriever.retrieve("form drag and streamlined body position", top_k=3)
    assert top[0].chunk.doc_id == "swimming-hydrodynamics"


class FakeIndex:
    def __init__(self):
        self.upserts = []
        self.queries = []

    def upsert(self, vectors, namespace):
        self.upserts.append((vectors, namespace))

    def query(self, **kwargs):
        self.queries.append(kwargs)
        match = SimpleNamespace(
            id="n::0", score=0.9, metadata={"doc_id": "n", "text": "hello", "title": "N"}
        )
        return SimpleNamespace(matches=[match])


def test_pinecone_store_payload_and_mapping():
    index = FakeIndex()
    store = PineconeHybridStore("", "unused", namespace="ns", index=index)
    store.upsert(
        [Chunk("n::0", "n", "hello", {"title": "N"})], [[0.1, 0.2]], [SparseVector([3], [0.5])]
    )
    vectors, namespace = index.upserts[0]
    assert namespace == "ns"
    assert vectors[0]["sparse_values"] == {"indices": [3], "values": [0.5]}
    assert vectors[0]["metadata"]["text"] == "hello"

    results = store.query([0.1, 0.2], SparseVector([3], [0.5]), top_k=1)
    assert index.queries[0]["sparse_vector"] == {"indices": [3], "values": [0.5]}
    assert results[0].chunk == Chunk("n::0", "n", "hello", {"title": "N"})


def test_pinecone_store_omits_empty_sparse_vector():
    index = FakeIndex()
    PineconeHybridStore("", "unused", index=index).query([0.1], SparseVector([], []), 1)
    assert "sparse_vector" not in index.queries[0]


def test_pinecone_sdk_importable_when_installed():
    pinecone = pytest.importorskip("pinecone")
    assert hasattr(pinecone, "Pinecone")

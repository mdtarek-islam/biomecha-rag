"""Hybrid dense plus sparse retrieval.

Both stores score a record as ``alpha * dense_dot + (1 - alpha) * sparse_dot``.
``hybrid_scale`` applies the weights to the query vectors, so a Pinecone index
with the ``dotproduct`` metric returns the same convex combination.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from biomecha_rag.embeddings import Embedder
from biomecha_rag.sparse import BM25Encoder
from biomecha_rag.types import Chunk, ScoredChunk, SparseVector


def hybrid_scale(dense: Sequence[float], sparse: SparseVector,
                 alpha: float) -> tuple[list[float], SparseVector]:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be between 0 and 1")
    return (
        [v * alpha for v in dense],
        SparseVector(indices=list(sparse.indices),
                     values=[v * (1 - alpha) for v in sparse.values]),
    )


class HybridStore(Protocol):
    def upsert(self, chunks: Sequence[Chunk], dense: Sequence[Sequence[float]],
               sparse: Sequence[SparseVector]) -> int: ...

    def query(self, dense: Sequence[float], sparse: SparseVector,
              top_k: int) -> list[ScoredChunk]: ...


class InMemoryHybridStore:
    """Exact dot-product store with the same contract as the Pinecone store."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[Chunk, list[float], dict[int, float]]] = {}

    def upsert(self, chunks, dense, sparse) -> int:
        if not len(chunks) == len(dense) == len(sparse):
            raise ValueError("chunks, dense and sparse must have equal length")
        for chunk, d, s in zip(chunks, dense, sparse):
            self._records[chunk.chunk_id] = (chunk, list(d), dict(zip(s.indices, s.values)))
        return len(chunks)

    def query(self, dense, sparse, top_k) -> list[ScoredChunk]:
        q_sparse = dict(zip(sparse.indices, sparse.values))
        scored = []
        for chunk, d, s in self._records.values():
            dense_score = sum(a * b for a, b in zip(dense, d))
            sparse_score = sum(v * s.get(i, 0.0) for i, v in q_sparse.items())
            scored.append(ScoredChunk(chunk=chunk, score=dense_score + sparse_score))
        scored.sort(key=lambda sc: (-sc.score, sc.chunk.chunk_id))
        return scored[:top_k]


class PineconeHybridStore:
    """Pinecone serverless index. The index must use the ``dotproduct`` metric."""

    def __init__(self, api_key: str, index_name: str, namespace: str = "",
                 index=None) -> None:
        if index is None:
            from pinecone import Pinecone

            client = Pinecone(api_key=api_key)
            # SDK v10 exposes ``index(name=...)``; earlier releases expose ``Index(name)``.
            opener = getattr(client, "index", None) or client.Index
            index = opener(name=index_name)
        self._index = index
        self.namespace = namespace

    def upsert(self, chunks, dense, sparse, batch_size: int = 100) -> int:
        vectors = [
            {
                "id": c.chunk_id,
                "values": list(d),
                "sparse_values": s.as_dict(),
                "metadata": {"doc_id": c.doc_id, "text": c.text, **c.metadata},
            }
            for c, d, s in zip(chunks, dense, sparse)
        ]
        for start in range(0, len(vectors), batch_size):
            self._index.upsert(vectors=vectors[start:start + batch_size],
                               namespace=self.namespace)
        return len(vectors)

    def query(self, dense, sparse, top_k) -> list[ScoredChunk]:
        kwargs = {"vector": list(dense), "top_k": top_k, "include_metadata": True,
                  "namespace": self.namespace}
        if sparse.indices:
            kwargs["sparse_vector"] = sparse.as_dict()
        response = self._index.query(**kwargs)
        out = []
        for match in response.matches:
            meta = dict(match.metadata or {})
            text = meta.pop("text", "")
            doc_id = meta.pop("doc_id", "")
            out.append(ScoredChunk(chunk=Chunk(match.id, doc_id, text, meta),
                                   score=float(match.score)))
        return out


class HybridRetriever:
    def __init__(self, embedder: Embedder, encoder: BM25Encoder, store: HybridStore,
                 alpha: float = 0.5) -> None:
        self.embedder = embedder
        self.encoder = encoder
        self.store = store
        self.alpha = alpha

    def index(self, chunks: Sequence[Chunk]) -> int:
        texts = [c.text for c in chunks]
        dense = self.embedder.embed_documents(texts)
        sparse = [self.encoder.encode_document(t) for t in texts]
        return self.store.upsert(chunks, dense, sparse)

    def retrieve(self, query: str, top_k: int = 20) -> list[ScoredChunk]:
        dense, sparse = hybrid_scale(self.embedder.embed_query(query),
                                     self.encoder.encode_query(query), self.alpha)
        return self.store.query(dense, sparse, top_k)

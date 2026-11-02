"""Cross-encoder reranking.

``HFCrossEncoderReranker`` calls a BGE reranker served by Text Embeddings
Inference (``/rerank`` route). ``LexicalReranker`` is a deterministic offline
fallback based on query term coverage.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

import requests

from biomecha_rag.text import tokenize
from biomecha_rag.types import ScoredChunk


class Reranker(Protocol):
    def rerank(self, query: str, candidates: Sequence[ScoredChunk],
               top_n: int) -> list[ScoredChunk]: ...


class HFCrossEncoderReranker:
    def __init__(self, endpoint_url: str, token: str, timeout: float = 20.0,
                 session: requests.Session | None = None) -> None:
        if not endpoint_url:
            raise ValueError("endpoint_url is required")
        self.endpoint_url = endpoint_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._headers = {"Content-Type": "application/json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def rerank(self, query, candidates, top_n) -> list[ScoredChunk]:
        if not candidates:
            return []
        response = self._session.post(
            f"{self.endpoint_url}/rerank",
            json={"query": query, "texts": [c.chunk.text for c in candidates],
                  "truncate": True},
            headers=self._headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        ranked = sorted(response.json(), key=lambda r: -float(r["score"]))
        return [ScoredChunk(candidates[r["index"]].chunk, float(r["score"]))
                for r in ranked[:top_n]]


class LexicalReranker:
    """Score = share of distinct query terms found in the chunk.

    Ties keep the retrieval order, then fall back to chunk id.
    """

    def rerank(self, query, candidates, top_n) -> list[ScoredChunk]:
        terms = set(tokenize(query))
        rows = []
        for rank, cand in enumerate(candidates):
            words = set(tokenize(cand.chunk.text))
            coverage = len(terms & words) / len(terms) if terms else 0.0
            rows.append((-coverage, rank, cand.chunk.chunk_id, cand, coverage))
        rows.sort(key=lambda r: r[:3])
        return [ScoredChunk(r[3].chunk, r[4]) for r in rows[:top_n]]

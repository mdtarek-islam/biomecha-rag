"""Dense embedders.

``HFInferenceEmbedder`` calls a BGE model served by Text Embeddings Inference on a
Hugging Face Inference Endpoint. ``HashingEmbedder`` is a deterministic offline
fallback for tests and local runs. It captures lexical overlap only.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from typing import Protocol

import requests

# BGE v1.5 English models expect this prefix on short queries, not on passages.
BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class Embedder(Protocol):
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class HFInferenceEmbedder:
    """Client for a Text Embeddings Inference ``/embed`` route."""

    def __init__(self, endpoint_url: str, token: str, dimension: int = 1024,
                 batch_size: int = 32, timeout: float = 20.0,
                 session: requests.Session | None = None) -> None:
        if not endpoint_url:
            raise ValueError("endpoint_url is required")
        self.endpoint_url = endpoint_url.rstrip("/")
        self.dimension = dimension
        self.batch_size = batch_size
        self.timeout = timeout
        self._session = session or requests.Session()
        self._headers = {"Content-Type": "application/json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def _post(self, texts: Sequence[str]) -> list[list[float]]:
        response = self._session.post(
            f"{self.endpoint_url}/embed",
            json={"inputs": list(texts), "normalize": True, "truncate": True},
            headers=self._headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        vectors = response.json()
        if len(vectors) != len(texts):
            raise ValueError("embedding endpoint returned the wrong number of vectors")
        return vectors

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            out.extend(self._post(texts[start:start + self.batch_size]))
        return out

    def embed_query(self, text: str) -> list[float]:
        return self._post([BGE_QUERY_INSTRUCTION + text])[0]


class HashingEmbedder:
    """Feature-hashing bag of words, L2 normalised. Deterministic across processes."""

    def __init__(self, dimension: int = 256) -> None:
        self.dimension = dimension

    def _bucket(self, token: str) -> tuple[int, float]:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        return value % self.dimension, 1.0 if (value >> 63) & 1 else -1.0

    def _embed(self, text: str) -> list[float]:
        from biomecha_rag.text import tokenize

        vec = [0.0] * self.dimension
        for token in tokenize(text):
            index, sign = self._bucket(token)
            vec[index] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

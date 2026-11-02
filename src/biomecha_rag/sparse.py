"""BM25 sparse encoding.

``rank_bm25`` supplies the IDF table and average document length. The encoder
turns these into Pinecone sparse vectors: documents carry the BM25 term-frequency
component, queries carry normalised IDF weights. Their dot product approximates
the BM25 score, which is what a ``dotproduct`` Pinecone index computes.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from rank_bm25 import BM25Okapi

from biomecha_rag.text import tokenize
from biomecha_rag.types import SparseVector


def token_index(token: str) -> int:
    """Stable 32-bit index for a token."""
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big")


def _merge(pairs: dict[int, float]) -> SparseVector:
    indices = sorted(pairs)
    return SparseVector(indices=indices, values=[pairs[i] for i in indices])


class BM25Encoder:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.idf: dict[str, float] = {}
        self.avgdl: float = 0.0
        self._bm25: BM25Okapi | None = None

    def fit(self, texts: Sequence[str]) -> BM25Encoder:
        corpus = [tokenize(t) for t in texts]
        if not any(corpus):
            raise ValueError("cannot fit BM25 on an empty corpus")
        self._bm25 = BM25Okapi(corpus, k1=self.k1, b=self.b)
        self.idf = {t: float(v) for t, v in self._bm25.idf.items()}
        self.avgdl = float(self._bm25.avgdl)
        return self

    def _require_fit(self) -> None:
        if not self.idf:
            raise RuntimeError("BM25Encoder is not fitted")

    def scores(self, query: str) -> list[float]:
        """Plain BM25 scores of ``query`` against the fitted corpus, in corpus order."""
        if self._bm25 is None:
            raise RuntimeError("BM25Encoder has no in-memory corpus; call fit()")
        return [float(s) for s in self._bm25.get_scores(tokenize(query))]

    def encode_document(self, text: str) -> SparseVector:
        self._require_fit()
        tokens = tokenize(text)
        norm = self.k1 * (1 - self.b + self.b * len(tokens) / self.avgdl)
        pairs: dict[int, float] = {}
        for token, tf in Counter(tokens).items():
            index = token_index(token)
            pairs[index] = pairs.get(index, 0.0) + tf * (self.k1 + 1) / (tf + norm)
        return _merge(pairs)

    def encode_query(self, text: str) -> SparseVector:
        self._require_fit()
        pairs: dict[int, float] = {}
        for token in set(tokenize(text)):
            weight = self.idf.get(token, 0.0)
            if weight > 0:
                index = token_index(token)
                pairs[index] = pairs.get(index, 0.0) + weight
        total = sum(pairs.values())
        if total:
            pairs = {i: v / total for i, v in pairs.items()}
        return _merge(pairs)

    def dump(self, path: str | Path) -> None:
        self._require_fit()
        payload = {"k1": self.k1, "b": self.b, "avgdl": self.avgdl, "idf": self.idf}
        Path(path).write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> BM25Encoder:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        encoder = cls(k1=payload["k1"], b=payload["b"])
        encoder.idf = {k: float(v) for k, v in payload["idf"].items()}
        encoder.avgdl = float(payload["avgdl"])
        return encoder

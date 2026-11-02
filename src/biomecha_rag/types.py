"""Shared data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class SparseVector:
    indices: list[int]
    values: list[float]

    def as_dict(self) -> dict:
        return {"indices": list(self.indices), "values": list(self.values)}

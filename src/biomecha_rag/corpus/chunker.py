"""Split documents into overlapping word windows that respect paragraph breaks."""

from __future__ import annotations

import re
from collections.abc import Iterable

from biomecha_rag.corpus.loader import Document
from biomecha_rag.types import Chunk

_FRONT_MATTER = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


def _paragraphs(text: str) -> list[str]:
    """Body paragraphs only. Headings live in metadata; blockquotes hold editorial notes."""
    text = _FRONT_MATTER.sub("", text)
    parts = [p.strip() for p in re.split(r"\n\s*\n", text)]
    return [p for p in parts if p and not p.startswith(("#", ">"))]


def chunk_document(doc: Document, max_words: int = 120, overlap: int = 20) -> list[Chunk]:
    """Pack paragraphs into chunks of at most ``max_words`` words.

    A paragraph longer than ``max_words`` is split into windows that share
    ``overlap`` words with the previous window.
    """
    if max_words < 1 or not 0 <= overlap < max_words:
        raise ValueError("require max_words >= 1 and 0 <= overlap < max_words")

    pieces: list[list[str]] = []
    current: list[str] = []
    for para in _paragraphs(doc.text):
        words = para.split()
        if len(words) > max_words:
            if current:
                pieces.append(current)
                current = []
            step = max_words - overlap
            for start in range(0, len(words), step):
                pieces.append(words[start:start + max_words])
                if start + max_words >= len(words):
                    break
            continue
        if current and len(current) + len(words) > max_words:
            pieces.append(current)
            current = []
        current = current + words
    if current:
        pieces.append(current)

    return [
        Chunk(
            chunk_id=f"{doc.doc_id}::{i}",
            doc_id=doc.doc_id,
            text=" ".join(words),
            metadata={"title": doc.title, "source": doc.source, "position": i},
        )
        for i, words in enumerate(pieces)
    ]


def chunk_documents(docs: Iterable[Document], max_words: int = 120,
                    overlap: int = 20) -> list[Chunk]:
    return [c for d in docs for c in chunk_document(d, max_words, overlap)]

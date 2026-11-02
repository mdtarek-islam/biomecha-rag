"""Tokenisation shared by the sparse encoder and the lexical reranker."""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    "a an and are as at be by for from how in is it of on or that the this to was what "
    "when where which while who why with does do during".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]

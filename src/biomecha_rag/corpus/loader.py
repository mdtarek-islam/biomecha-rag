"""Load markdown and plain-text sports science notes from a folder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = (".md", ".txt")


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    text: str
    source: str


def _title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def load_documents(folder: str | Path) -> list[Document]:
    """Read every supported file in ``folder``, sorted by name for stable ids."""
    root = Path(folder)
    if not root.is_dir():
        raise FileNotFoundError(f"corpus folder not found: {root}")
    docs = []
    for path in sorted(root.iterdir()):
        if path.suffix.lower() not in SUPPORTED_SUFFIXES or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        docs.append(Document(doc_id=path.stem, title=_title(text, path.stem), text=text,
                             source=path.name))
    return docs

"""Answer generation.

``MistralGenerator`` builds a LangChain chain (prompt, Hugging Face endpoint,
string parser) that calls Mistral-7B-Instruct on a Hugging Face Inference
Endpoint. LangChain imports are lazy so the Lambda handler and the tests load
without it. ``ExtractiveGenerator`` is an offline fallback that quotes the top
chunks verbatim.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from biomecha_rag.types import ScoredChunk

SYSTEM_INSTRUCTIONS = (
    "You are a sports biomechanics assistant. Answer only from the context. "
    "Cite every claim with the chunk id in square brackets, for example [doc::0]. "
    "If the context does not contain the answer, say that you do not know."
)

# Mistral-7B-Instruct chat format. The serving tokenizer adds the BOS token.
PROMPT_TEMPLATE = (
    "[INST] " + SYSTEM_INSTRUCTIONS + "\n\nContext:\n{context}\n\n"
    "Question: {question} [/INST]"
)


def format_context(chunks: Sequence[ScoredChunk]) -> str:
    return "\n\n".join(f"[{c.chunk.chunk_id}] {c.chunk.text}" for c in chunks)


class Generator(Protocol):
    def generate(self, question: str, chunks: Sequence[ScoredChunk]) -> str: ...


def build_prompt():
    from langchain_core.prompts import PromptTemplate

    return PromptTemplate.from_template(PROMPT_TEMPLATE)


def build_chain(llm):
    """Compose prompt, model and parser. ``llm`` is any LangChain runnable LLM."""
    from langchain_core.output_parsers import StrOutputParser

    return build_prompt() | llm | StrOutputParser()


class MistralGenerator:
    def __init__(self, endpoint_url: str, token: str, max_new_tokens: int = 512,
                 temperature: float = 0.1, llm=None) -> None:
        if llm is None:
            from langchain_huggingface import HuggingFaceEndpoint

            llm = HuggingFaceEndpoint(
                endpoint_url=endpoint_url,
                huggingfacehub_api_token=token or None,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                repetition_penalty=1.05,
                return_full_text=False,
            )
        self._chain = build_chain(llm)

    def generate(self, question, chunks) -> str:
        return self._chain.invoke(
            {"context": format_context(chunks), "question": question}
        ).strip()


class ExtractiveGenerator:
    """Offline fallback: return the first sentence of each chunk with its citation."""

    def __init__(self, max_chunks: int = 3) -> None:
        self.max_chunks = max_chunks

    def generate(self, question, chunks) -> str:
        if not chunks:
            return "No relevant context was found for this question."
        lines = []
        for c in chunks[: self.max_chunks]:
            sentence = c.chunk.text.split(". ")[0].rstrip(".")
            lines.append(f"{sentence}. [{c.chunk.chunk_id}]")
        return " ".join(lines)

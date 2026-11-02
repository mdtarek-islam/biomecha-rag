"""Retrieve, rerank, generate."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from biomecha_rag.generator import Generator
from biomecha_rag.reranker import Reranker
from biomecha_rag.retriever import HybridRetriever

_CITATION = re.compile(r"\[([^\[\]\s]+::\d+)\]")


@dataclass(frozen=True)
class Answer:
    answer: str
    citations: list[str]
    context_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"answer": self.answer, "citations": self.citations,
                "context_ids": self.context_ids}


class RagPipeline:
    def __init__(self, retriever: HybridRetriever, reranker: Reranker,
                 generator: Generator, top_k: int = 20, top_n: int = 5) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.generator = generator
        self.top_k = top_k
        self.top_n = top_n

    def ask(self, question: str, top_n: int | None = None) -> Answer:
        candidates = self.retriever.retrieve(question, top_k=self.top_k)
        context = self.reranker.rerank(question, candidates, top_n or self.top_n)
        text = self.generator.generate(question, context)
        context_ids = [c.chunk.chunk_id for c in context]
        allowed = set(context_ids)
        cited = []
        for cid in _CITATION.findall(text):
            if cid in allowed and cid not in cited:
                cited.append(cid)
        return Answer(answer=text, citations=cited, context_ids=context_ids)


def build_pipeline(settings=None) -> RagPipeline:
    """Wire the deployed components: HF endpoints, Pinecone and a stored BM25 table."""
    from biomecha_rag.config import Settings
    from biomecha_rag.embeddings import HFInferenceEmbedder
    from biomecha_rag.generator import MistralGenerator
    from biomecha_rag.reranker import HFCrossEncoderReranker
    from biomecha_rag.retriever import PineconeHybridStore
    from biomecha_rag.sparse import BM25Encoder

    s = settings or Settings.from_env()
    retriever = HybridRetriever(
        embedder=HFInferenceEmbedder(s.embed_endpoint_url, s.hf_token),
        encoder=BM25Encoder.load(s.bm25_params_path),
        store=PineconeHybridStore(s.pinecone_api_key, s.pinecone_index, s.pinecone_namespace),
        alpha=s.alpha,
    )
    return RagPipeline(
        retriever=retriever,
        reranker=HFCrossEncoderReranker(s.rerank_endpoint_url, s.hf_token),
        generator=MistralGenerator(s.llm_endpoint_url, s.hf_token, s.max_new_tokens,
                                   s.temperature),
        top_k=s.top_k,
        top_n=s.rerank_top_n,
    )


def build_local_pipeline(corpus_dir, alpha: float = 0.5) -> RagPipeline:
    """Offline pipeline over a folder of notes: no network, no credentials."""
    from biomecha_rag.corpus import chunk_documents, load_documents
    from biomecha_rag.embeddings import HashingEmbedder
    from biomecha_rag.generator import ExtractiveGenerator
    from biomecha_rag.reranker import LexicalReranker
    from biomecha_rag.retriever import InMemoryHybridStore
    from biomecha_rag.sparse import BM25Encoder

    chunks = chunk_documents(load_documents(corpus_dir))
    retriever = HybridRetriever(HashingEmbedder(), BM25Encoder().fit([c.text for c in chunks]),
                                InMemoryHybridStore(), alpha=alpha)
    retriever.index(chunks)
    return RagPipeline(retriever, LexicalReranker(), ExtractiveGenerator())

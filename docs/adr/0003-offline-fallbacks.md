# ADR 0003: Deterministic offline fallbacks behind each interface

Date: 2026-11-02. Base commit: 39ceb36.

Context: CI has no endpoint credentials. Tests must not call paid services.

Decision: Define one protocol per stage: embedder, store, reranker, generator. Ship a deterministic local implementation of each: hashing embedder, in-memory store, lexical reranker, extractive generator. Import LangChain and Pinecone lazily.

Trade-offs: The fallbacks show wiring, not answer quality. Their scores say nothing about BGE or Mistral-7B accuracy.

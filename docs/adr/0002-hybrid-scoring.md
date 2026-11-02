# ADR 0002: Hybrid scoring by scaled dot product

Date: 2026-11-02. Base commit: 39ceb36.

Context: Dense BGE vectors catch paraphrase. BM25 catches exact terms such as "pronation" or "valgus".

Decision: Store both vectors in one Pinecone index with the dotproduct metric. Scale the query: dense by alpha, sparse by 1 minus alpha. The in-memory store applies the same formula, so tests check the fusion order offline.

Trade-offs: The BM25 IDF table is fitted at ingest time and shipped as bm25_params.json. Adding documents means refitting and re-upserting.

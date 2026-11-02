"""Command line interface.

  biomecha-rag ingest --corpus data/sample_corpus --bm25-out bm25_params.json
  biomecha-rag ask "How does trunk rotation affect smash speed?" --local
"""

from __future__ import annotations

import argparse
import json
import sys

DEFAULT_CORPUS = "data/sample_corpus"


def _ingest(args) -> int:
    from biomecha_rag.config import Settings
    from biomecha_rag.corpus import chunk_documents, load_documents
    from biomecha_rag.embeddings import HFInferenceEmbedder
    from biomecha_rag.retriever import HybridRetriever, PineconeHybridStore
    from biomecha_rag.sparse import BM25Encoder

    chunks = chunk_documents(load_documents(args.corpus), args.max_words, args.overlap)
    encoder = BM25Encoder().fit([c.text for c in chunks])
    encoder.dump(args.bm25_out)
    if args.dry_run:
        print(json.dumps({"chunks": len(chunks), "bm25_params": args.bm25_out}))
        return 0
    s = Settings.from_env()
    retriever = HybridRetriever(
        HFInferenceEmbedder(s.embed_endpoint_url, s.hf_token), encoder,
        PineconeHybridStore(s.pinecone_api_key, s.pinecone_index, s.pinecone_namespace),
        alpha=s.alpha,
    )
    count = retriever.index(chunks)
    print(json.dumps({"upserted": count, "bm25_params": args.bm25_out}))
    return 0


def _ask(args) -> int:
    from biomecha_rag.pipeline import build_local_pipeline, build_pipeline

    pipeline = build_local_pipeline(args.corpus) if args.local else build_pipeline()
    print(json.dumps(pipeline.ask(args.question, top_n=args.top_n).as_dict(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="biomecha-rag")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="chunk notes, fit BM25, upsert to Pinecone")
    ingest.add_argument("--corpus", default=DEFAULT_CORPUS)
    ingest.add_argument("--bm25-out", default="bm25_params.json")
    ingest.add_argument("--max-words", type=int, default=120)
    ingest.add_argument("--overlap", type=int, default=20)
    ingest.add_argument("--dry-run", action="store_true",
                        help="fit BM25 and count chunks without calling any endpoint")
    ingest.set_defaults(func=_ingest)

    ask = sub.add_parser("ask", help="answer a question")
    ask.add_argument("question")
    ask.add_argument("--top-n", type=int, default=None)
    ask.add_argument("--local", action="store_true",
                     help="use the offline pipeline over --corpus")
    ask.add_argument("--corpus", default=DEFAULT_CORPUS)
    ask.set_defaults(func=_ask)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

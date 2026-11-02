import pytest

from biomecha_rag.config import Settings
from biomecha_rag.embeddings import HashingEmbedder
from biomecha_rag.generator import ExtractiveGenerator, format_context
from biomecha_rag.pipeline import RagPipeline, build_local_pipeline
from biomecha_rag.reranker import LexicalReranker
from biomecha_rag.retriever import HybridRetriever, InMemoryHybridStore
from biomecha_rag.sparse import BM25Encoder
from biomecha_rag.types import Chunk, ScoredChunk

CHUNKS = [
    Chunk("smash::0", "smash", "Trunk rotation adds racket speed in the badminton smash."),
    Chunk("swim::0", "swim", "A streamlined position reduces form drag in swimming."),
    Chunk("sprint::0", "sprint", "Horizontal force drives sprint acceleration."),
]


class CitingGenerator:
    """Fake model that cites the first context chunk plus an id it was not given."""

    def __init__(self):
        self.seen = None

    def generate(self, question, chunks):
        self.seen = [c.chunk.chunk_id for c in chunks]
        return f"Answer [{self.seen[0]}] and [{self.seen[0]}] and [ghost::9]."


def _pipeline(generator):
    retriever = HybridRetriever(
        HashingEmbedder(), BM25Encoder().fit([c.text for c in CHUNKS]), InMemoryHybridStore()
    )
    retriever.index(CHUNKS)
    return RagPipeline(retriever, LexicalReranker(), generator, top_k=3, top_n=2)


def test_pipeline_end_to_end_with_fakes():
    gen = CitingGenerator()
    answer = _pipeline(gen).ask("How does trunk rotation change smash racket speed?")
    assert gen.seen[0] == "smash::0"
    assert len(gen.seen) == 2
    assert answer.citations == ["smash::0"]
    assert answer.context_ids == gen.seen


def test_pipeline_top_n_override():
    gen = CitingGenerator()
    _pipeline(gen).ask("drag", top_n=1)
    assert len(gen.seen) == 1


def test_local_pipeline_over_sample_corpus(sample_corpus):
    answer = build_local_pipeline(sample_corpus).ask("How do swimmers reduce form drag?")
    assert answer.citations
    assert answer.citations[0].startswith("swimming-hydrodynamics::")


def test_format_context_and_extractive_generator():
    chunks = [ScoredChunk(CHUNKS[0], 1.0)]
    assert format_context(chunks).startswith("[smash::0] Trunk rotation")
    assert ExtractiveGenerator().generate("q", chunks).endswith("[smash::0]")
    assert "No relevant context" in ExtractiveGenerator().generate("q", [])


def test_langchain_chain_with_fake_llm():
    pytest.importorskip("langchain_core")
    from langchain_core.language_models.fake import FakeListLLM

    from biomecha_rag.generator import MistralGenerator

    gen = MistralGenerator("unused", "", llm=FakeListLLM(responses=["  Fine [smash::0]  "]))
    assert gen.generate("q", [ScoredChunk(CHUNKS[0], 1.0)]) == "Fine [smash::0]"


def test_settings_from_env_and_validation():
    s = Settings.from_env({"HYBRID_ALPHA": "0.3", "RERANK_TOP_N": "4", "HF_TOKEN": "x"})
    assert (s.alpha, s.rerank_top_n, s.hf_token) == (0.3, 4, "x")
    assert Settings.from_env({}).pinecone_index == "biomecha-rag"
    with pytest.raises(ValueError):
        Settings.from_env({"HYBRID_ALPHA": "2"})

import json

from biomecha_rag.cli import main
from biomecha_rag.sparse import BM25Encoder


def test_ingest_dry_run_writes_bm25_params(tmp_path, sample_corpus, capsys):
    out = tmp_path / "bm25.json"
    assert main(["ingest", "--corpus", str(sample_corpus), "--bm25-out", str(out),
                 "--dry-run"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["chunks"] >= 4
    assert BM25Encoder.load(out).encode_query("smash").indices


def test_ask_local_prints_cited_answer(sample_corpus, capsys):
    assert main(["ask", "What causes knee valgus on landing?", "--local",
                 "--corpus", str(sample_corpus)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["citations"][0].startswith("jump-landing::")

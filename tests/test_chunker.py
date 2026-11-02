import pytest

from biomecha_rag.corpus import Document, chunk_document, chunk_documents, load_documents


def _doc(text):
    return Document(doc_id="note", title="Note", text=text, source="note.md")


def test_loader_reads_sample_corpus_with_titles(sample_corpus):
    docs = load_documents(sample_corpus)
    assert [d.doc_id for d in docs] == sorted(d.doc_id for d in docs)
    assert len(docs) == 4
    titles = {d.doc_id: d.title for d in docs}
    assert titles["badminton-smash"] == "Badminton smash mechanics"


def test_loader_rejects_missing_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_documents(tmp_path / "absent")


def test_short_paragraphs_pack_into_one_chunk():
    chunks = chunk_document(_doc("alpha beta\n\ngamma delta"), max_words=10, overlap=2)
    assert len(chunks) == 1
    assert chunks[0].text == "alpha beta gamma delta"
    assert chunks[0].chunk_id == "note::0"


def test_headings_and_blockquote_notes_are_not_chunked():
    text = "# Title\n\n> Editorial note.\n\nBody text."
    chunks = chunk_document(_doc(text), max_words=10, overlap=2)
    assert [c.text for c in chunks] == ["Body text."]


def test_paragraph_boundary_starts_new_chunk_when_full():
    text = "a1 a2 a3 a4\n\nb1 b2 b3 b4"
    chunks = chunk_document(_doc(text), max_words=5, overlap=1)
    assert [c.text for c in chunks] == ["a1 a2 a3 a4", "b1 b2 b3 b4"]


def test_long_paragraph_splits_with_overlap():
    words = [f"w{i}" for i in range(10)]
    chunks = chunk_document(_doc(" ".join(words)), max_words=4, overlap=1)
    texts = [c.text.split() for c in chunks]
    assert all(len(t) <= 4 for t in texts)
    assert texts[0][-1] == texts[1][0]
    assert texts[-1][-1] == "w9"


def test_chunk_metadata_and_ids_are_stable(sample_corpus):
    first = chunk_documents(load_documents(sample_corpus))
    second = chunk_documents(load_documents(sample_corpus))
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert all(c.metadata["source"].endswith(".md") for c in first)


@pytest.mark.parametrize("max_words,overlap", [(0, 0), (5, 5), (5, -1)])
def test_invalid_window_rejected(max_words, overlap):
    with pytest.raises(ValueError):
        chunk_document(_doc("x"), max_words=max_words, overlap=overlap)

from app.services.pdf import PageText, chunk_pages
from app.services.retrieval import retrieve


def test_chunking_preserves_page_numbers():
    chunks = chunk_pages([PageText(2, "contract " * 600)], chunk_size=100, overlap=20)
    assert chunks
    assert {chunk["page"] for chunk in chunks} == {2}


def test_retrieval_prioritizes_matching_terms():
    chunks = [
        {"page": 1, "text": "A general introduction to contracts."},
        {"page": 4, "text": "The termination clause requires thirty days notice."},
    ]
    results = retrieve(chunks, "termination notice")
    assert results[0]["page"] == 4


from askify.ingester.chunker import chunk_code, chunk_document


def test_code_chunks_include_source_hash():
    file = {
        "source": "app.py",
        "content": "def calculate_total(price, tax):\n    return price + tax\n",
        "type": "code",
        "hash": "file-hash-123",
    }

    chunks = chunk_code(file)

    assert chunks
    assert all(
        chunk["source_hash"] == "file-hash-123"
        for chunk in chunks
    )


def test_document_chunks_include_source_hash():
    file = {
        "source": "README.md",
        "content": "First paragraph with useful content.\n\nSecond paragraph with more content.",
        "type": "document",
        "hash": "document-hash-456",
    }

    chunks = chunk_document(file)

    assert chunks
    assert all(
        chunk["source_hash"] == "document-hash-456"
        for chunk in chunks
    )

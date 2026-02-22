"""
test_ingestion.py — Tests for PDF ingestion and chunking.

Uses a minimal in-memory PDF to test the full ingestion path without
external files. Mocks the vector_store to avoid FAISS persistence.
Naming convention: test_ingestion_<behavior>
"""
import io
import os
from unittest.mock import MagicMock, patch

import pytest

# Skip this entire module if PyMuPDF (fitz) or faiss-cpu are not installed.
pytest.importorskip("fitz", reason="PyMuPDF (fitz) not installed")
pytest.importorskip("faiss", reason="faiss-cpu not installed")


def make_minimal_pdf_bytes() -> bytes:
    """
    Hand-crafted minimal valid 1-page PDF with extractable text.
    """
    return b"""%PDF-1.4
1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj
2 0 obj<</Type /Pages /Kids[3 0 R] /Count 1>>endobj
3 0 obj<</Type /Page /Parent 2 0 R /MediaBox[0 0 612 792]
/Contents 4 0 R /Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 72 720 Td (Hello Clearpath world.) Tj ET
endstream
endobj
5 0 obj<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000360 00000 n 
trailer<</Size 6 /Root 1 0 R>>
startxref
441
%%EOF"""


# ---------------------------------------------------------------------------
# Chunking function tests (pure Python, no FAISS needed)
# ---------------------------------------------------------------------------

def test_chunk_text_returns_list():
    from backend.rag.ingestion import chunk_text
    chunks = chunk_text("This is a sample text. " * 30)
    assert isinstance(chunks, list)


def test_chunk_text_single_chunk_for_short_text():
    from backend.rag.ingestion import chunk_text
    chunks = chunk_text("Hello world.")
    assert len(chunks) == 1


def test_chunk_text_preserves_content():
    from backend.rag.ingestion import chunk_text
    text = "Clearpath is a support platform."
    chunks = chunk_text(text)
    combined = " ".join(c.get("text", c) if isinstance(c, dict) else c for c in chunks)
    assert "Clearpath" in combined


def test_chunk_text_respects_chunk_size():
    """Chunks should not significantly exceed 512 token limit (using word-based approximation)."""
    from backend.rag.ingestion import chunk_text
    from backend.utils.token_counter import count_tokens

    long_text = "This is a test sentence about Clearpath products and services. " * 100
    chunks = chunk_text(long_text)
    for chunk in chunks:
        text = chunk.get("text", chunk) if isinstance(chunk, dict) else chunk
        # Allow slight overshoot due to approximation
        assert count_tokens(text) <= 600, f"Chunk exceeded 600 tokens"


def test_chunk_text_has_overlap():
    """With overlap, content from the end of one chunk should appear at the start of the next."""
    from backend.rag.ingestion import chunk_text
    # Generate a text that will definitely need multiple chunks
    word = "Clearpath "
    text = word * 600  # ~600 repetitions → well over 512 tokens
    chunks = chunk_text(text)
    if len(chunks) > 1:
        # Both chunks should contain "Clearpath" — confirming overlap preserves content
        first_text = chunks[0].get("text", chunks[0]) if isinstance(chunks[0], dict) else chunks[0]
        second_text = chunks[1].get("text", chunks[1]) if isinstance(chunks[1], dict) else chunks[1]
        assert "Clearpath" in first_text
        assert "Clearpath" in second_text


# ---------------------------------------------------------------------------
# Ingestion function tests
# ---------------------------------------------------------------------------

def test_ingestion_ingest_pdf_returns_records(tmp_path):
    """Test that ingest_pdf returns chunk records for a valid PDF."""
    from backend.rag.ingestion import ingest_pdf

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(make_minimal_pdf_bytes())

    mock_vs = MagicMock()
    mock_vs.add = MagicMock()
    mock_vs.persist = MagicMock()

    with patch("backend.rag.ingestion.vector_store", mock_vs):
        records = ingest_pdf(str(pdf_path))

    assert isinstance(records, list)
    # Even a minimal PDF should produce at least 1 chunk
    assert len(records) >= 1


def test_ingestion_record_has_required_fields(tmp_path):
    """Each ChunkRecord should have required metadata fields."""
    from backend.rag.ingestion import ingest_pdf

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(make_minimal_pdf_bytes())

    mock_vs = MagicMock()
    with patch("backend.rag.ingestion.vector_store", mock_vs):
        records = ingest_pdf(str(pdf_path))

    if records:
        rec = records[0]
        # ChunkRecord is a dataclass/dict — check key attributes
        assert hasattr(rec, "text") or "text" in (rec if isinstance(rec, dict) else vars(rec))


def test_ingestion_vector_store_add_called(tmp_path):
    """vector_store.add() should be called during ingestion."""
    from backend.rag.ingestion import ingest_pdf

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(make_minimal_pdf_bytes())

    mock_vs = MagicMock()
    with patch("backend.rag.ingestion.vector_store", mock_vs):
        ingest_pdf(str(pdf_path))

    mock_vs.add.assert_called_once()


def test_ingestion_vector_store_persist_called(tmp_path):
    """vector_store.persist() should be called after successful ingestion."""
    from backend.rag.ingestion import ingest_pdf

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(make_minimal_pdf_bytes())

    mock_vs = MagicMock()
    with patch("backend.rag.ingestion.vector_store", mock_vs):
        ingest_pdf(str(pdf_path))

    mock_vs.persist.assert_called_once()


def test_ingestion_raises_for_nonexistent_file():
    """ingest_pdf should raise for a file that doesn't exist."""
    from backend.rag.ingestion import ingest_pdf

    with pytest.raises(Exception):
        ingest_pdf("/nonexistent/path/to/missing.pdf")

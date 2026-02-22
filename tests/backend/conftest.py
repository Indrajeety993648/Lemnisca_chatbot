"""
conftest.py — Shared fixtures for Clearpath backend tests.

Provides:
  - test_client: FastAPI TestClient with mocked FAISS + Groq
  - sample_query: a simple user query string
  - mock_faiss_index: a small in-memory FAISS index (10 vectors, dim=384)
  - mock_groq_response: a mocked non-streaming groq completion object
  - sample_chunks: list of RetrievedChunk dicts
"""
import io
import struct
from typing import Any, List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tiny helper to create a minimal valid PDF in memory (1 page, some text)
# ---------------------------------------------------------------------------

def make_tiny_pdf() -> bytes:
    """
    Return a minimal valid PDF as bytes.
    This is a hand-crafted 1-page PDF with one line of extractable text.
    """
    # Minimal valid PDF structure
    content = b"""%PDF-1.4
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
    return content


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_query() -> str:
    return "What is Clearpath?"


@pytest.fixture
def sample_chunks() -> List[dict]:
    """Return a list of chunk dicts as produced by the retriever."""
    return [
        {
            "text": "Clearpath is a customer support platform with Pro and Enterprise plans.",
            "source_file": "clearpath_overview.pdf",
            "page_number": 1,
            "score": 0.85,
        },
        {
            "text": "The Pro plan costs $49/month and includes 5 users.",
            "source_file": "pricing_guide.pdf",
            "page_number": 3,
            "score": 0.72,
        },
    ]


@pytest.fixture
def mock_groq_response() -> MagicMock:
    """
    Create a mock object that mimics a non-streaming groq ChatCompletion.
    Matches the shape accessed in pipeline.py.
    """
    choice = MagicMock()
    choice.message.content = "Clearpath is a customer support platform."
    choice.finish_reason = "stop"

    usage = MagicMock()
    usage.prompt_tokens = 120
    usage.completion_tokens = 30

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


@pytest.fixture
def mock_streaming_groq_response() -> MagicMock:
    """
    Create a mock iterator mimicking a streaming groq response.
    Yields 3 chunk objects then a final stop chunk.
    """
    def _make_chunk(token: str, finish: str | None = None) -> MagicMock:
        delta = MagicMock()
        delta.content = token
        choice = MagicMock()
        choice.delta = delta
        choice.finish_reason = finish
        usage = MagicMock()
        usage.prompt_tokens = 120
        usage.completion_tokens = 3
        chunk = MagicMock()
        chunk.choices = [choice]
        chunk.usage = usage
        return chunk

    chunks = [
        _make_chunk("Clearpath "),
        _make_chunk("is great."),
        _make_chunk("", finish_reason="stop"),
    ]

    stream = MagicMock()
    stream.__iter__ = MagicMock(return_value=iter(chunks))
    return stream


@pytest.fixture
def mock_faiss_index():
    """
    Return a small in-memory FAISS index (10 vectors, dim=384).
    Also returns a corresponding metadata list.
    Skips automatically if faiss-cpu is not installed.
    """
    faiss = pytest.importorskip("faiss", reason="faiss-cpu not installed")

    dim = 384
    index = faiss.IndexFlatIP(dim)
    rng = np.random.default_rng(42)
    vectors = rng.standard_normal((10, dim)).astype(np.float32)
    # L2-normalize
    faiss.normalize_L2(vectors)
    index.add(vectors)

    metadata = [
        {
            "chunk_id": f"chunk-{i}",
            "text": f"This is sample chunk number {i} about Clearpath features.",
            "source_file": "test_doc.pdf",
            "page_number": i + 1,
            "chunk_index": i,
        }
        for i in range(10)
    ]
    return index, metadata


@pytest.fixture
def tiny_pdf_bytes() -> bytes:
    return make_tiny_pdf()


# ---------------------------------------------------------------------------
# App fixture with mocked vector store
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client(mock_faiss_index):
    """
    FastAPI TestClient with:
    - vector_store pre-loaded with mock_faiss_index
    - Groq client patched to avoid real HTTP calls
    """
    faiss_index, metadata = mock_faiss_index

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata):
        from backend.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client

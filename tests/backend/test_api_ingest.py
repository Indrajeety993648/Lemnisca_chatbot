"""
test_api_ingest.py — HTTP tests for POST /api/ingest endpoint.

Tests file upload via multipart/form-data with valid and invalid inputs.
Naming convention: test_api_ingest_<behavior>
"""
import io
from unittest.mock import MagicMock, patch

import pytest


def make_minimal_pdf_bytes() -> bytes:
    """Minimal valid 1-page PDF with extractable text."""
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
# Valid PDF upload
# ---------------------------------------------------------------------------

def test_api_ingest_returns_200_for_valid_pdf(test_client, tmp_path):
    mock_records = [
        MagicMock(chunk_id="c1", text="Hello Clearpath world.", source_file="test.pdf",
                  page_number=1, chunk_index=0)
    ]

    with patch("backend.api.routes_ingest.ingest_pdf", return_value=mock_records), \
         patch("backend.api.routes_ingest.settings") as mock_settings:
        mock_settings.PDF_DIR = str(tmp_path)
        mock_settings.MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

        pdf_bytes = make_minimal_pdf_bytes()
        response = test_client.post(
            "/api/ingest",
            files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )

    assert response.status_code == 200


def test_api_ingest_response_has_required_fields(test_client, tmp_path):
    mock_records = [
        MagicMock(chunk_id="c1", text="Hello.", source_file="test.pdf",
                  page_number=1, chunk_index=0)
    ]

    with patch("backend.api.routes_ingest.ingest_pdf", return_value=mock_records), \
         patch("backend.api.routes_ingest.settings") as mock_settings:
        mock_settings.PDF_DIR = str(tmp_path)
        mock_settings.MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

        pdf_bytes = make_minimal_pdf_bytes()
        response = test_client.post(
            "/api/ingest",
            files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )

    body = response.json()
    assert "status" in body
    assert "filename" in body
    assert "chunks_created" in body


def test_api_ingest_returns_400_for_non_pdf(test_client):
    """Uploading a text file should return 400."""
    txt_bytes = b"This is a plain text file, not a PDF."
    response = test_client.post(
        "/api/ingest",
        files={"file": ("document.txt", io.BytesIO(txt_bytes), "text/plain")},
    )
    assert response.status_code == 400


def test_api_ingest_returns_422_for_missing_file(test_client):
    """Request with no file field should return 422."""
    response = test_client.post("/api/ingest")
    assert response.status_code == 422


def test_api_ingest_chunks_created_matches_records(test_client, tmp_path):
    n_chunks = 3
    mock_records = [
        MagicMock(chunk_id=f"c{i}", text=f"Chunk {i}.", source_file="test.pdf",
                  page_number=1, chunk_index=i)
        for i in range(n_chunks)
    ]

    with patch("backend.api.routes_ingest.ingest_pdf", return_value=mock_records), \
         patch("backend.api.routes_ingest.settings") as mock_settings:
        mock_settings.PDF_DIR = str(tmp_path)
        mock_settings.MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

        pdf_bytes = make_minimal_pdf_bytes()
        response = test_client.post(
            "/api/ingest",
            files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )

    body = response.json()
    assert body["chunks_created"] == n_chunks


def test_api_ingest_status_is_success_for_valid(test_client, tmp_path):
    mock_records = [
        MagicMock(chunk_id="c1", text="Hello.", source_file="test.pdf",
                  page_number=1, chunk_index=0)
    ]

    with patch("backend.api.routes_ingest.ingest_pdf", return_value=mock_records), \
         patch("backend.api.routes_ingest.settings") as mock_settings:
        mock_settings.PDF_DIR = str(tmp_path)
        mock_settings.MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

        pdf_bytes = make_minimal_pdf_bytes()
        response = test_client.post(
            "/api/ingest",
            files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )

    assert response.json()["status"] == "success"

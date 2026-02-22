"""
routes_ingest.py — POST /api/ingest endpoint.

Accepts a PDF file upload (multipart/form-data), validates it, saves it to
the configured PDF directory, and runs the full ingestion pipeline.

Per Section 6.2 of ARCHITECTURE.md:
  - 200: success
  - 400: invalid file (not PDF, too large, no extractable text)
  - 500: processing error
"""
import logging
import os
import re
import time

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.api.schemas import IngestResponse
from backend.config import settings
from backend.rag.ingestion import ingest_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

# Allowed PDF MIME types
_ALLOWED_MIME_TYPES = {"application/pdf", "binary/octet-stream"}

# Filename sanitization: allow only alphanumeric, hyphens, underscores, and .pdf extension
_SAFE_FILENAME_RE = re.compile(r"^[\w\-]+\.pdf$", re.ASCII | re.IGNORECASE)


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename to alphanumeric + hyphens + underscores only.
    Preserves the .pdf extension.
    Returns the sanitized name or raises ValueError if it cannot be made safe.
    """
    if not filename:
        raise ValueError("Empty filename")
    # Strip path components
    basename = os.path.basename(filename)
    # Replace spaces with underscores
    sanitized = basename.replace(" ", "_")
    # Remove any character that isn't alphanumeric, hyphen, underscore, or dot
    sanitized = re.sub(r"[^\w\-.]", "", sanitized)
    # Ensure it ends with .pdf (case-insensitive)
    if not sanitized.lower().endswith(".pdf"):
        raise ValueError(f"File '{filename}' does not have a .pdf extension after sanitization")
    if not _SAFE_FILENAME_RE.match(sanitized):
        raise ValueError(f"Filename '{sanitized}' contains disallowed characters")
    return sanitized


@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={
        400: {"description": "Invalid file"},
        500: {"description": "Processing error"},
    },
)
async def ingest_endpoint(file: UploadFile = File(...)):
    """
    Upload and process a PDF file for RAG indexing.

    Validation (per Section 8 — Security):
    - Must be a .pdf file (MIME type or extension check).
    - Max size: 50 MB.
    - Must contain extractable text (not scanned image-only).

    After validation, the PDF is saved to CLEARPATH_PDF_DIR and ingested
    into the FAISS index.
    """
    start_time = time.time()

    # --- Filename validation ---
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        safe_filename = _sanitize_filename(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # --- Read file content and size check ---
    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size {file_size / (1024 * 1024):.1f} MB exceeds maximum allowed 50 MB.",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- Basic PDF header check ---
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="File does not appear to be a valid PDF (missing PDF header).",
        )

    # --- Save file to PDF directory ---
    os.makedirs(settings.PDF_DIR, exist_ok=True)
    file_path = os.path.join(settings.PDF_DIR, safe_filename)

    try:
        with open(file_path, "wb") as fh:
            fh.write(content)
    except OSError as exc:
        logger.exception("Failed to save uploaded PDF '%s'", safe_filename)
        raise HTTPException(
            status_code=500, detail=f"Could not save uploaded file: {exc}"
        )

    # --- Run ingestion pipeline ---
    try:
        records = ingest_pdf(file_path)
    except ValueError as exc:
        # Raised by ingestion.py when PDF has no extractable text
        logger.warning("Ingestion validation failed for '%s': %s", safe_filename, exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Ingestion pipeline error for '%s'", safe_filename)
        raise HTTPException(
            status_code=500, detail=f"Processing error: {exc}"
        )

    processing_time_ms = (time.time() - start_time) * 1000
    total_pages = max((r.page_number for r in records), default=0)

    logger.info(
        "Ingested '%s': %d chunks, %d pages, %.1f ms",
        safe_filename,
        len(records),
        total_pages,
        processing_time_ms,
    )

    return IngestResponse(
        status="success",
        filename=safe_filename,
        chunks_created=len(records),
        total_pages=total_pages,
        processing_time_ms=round(processing_time_ms, 2),
    )

"""
ingestion.py — PDF parsing and recursive chunking pipeline.

Implements the ingestion flow described in Sections 3.1 and 3.2 of
ARCHITECTURE.md:

1. Open PDF with PyMuPDF (fitz).
2. Extract text page-by-page, append [PAGE_BREAK:N] markers.
3. Recursively split text into chunks of 512 tokens with 64-token overlap,
   using separator hierarchy: ["\n\n", "\n", ". ", " "].
4. Assign page numbers to each chunk by looking up the nearest PAGE_BREAK
   marker before the chunk's position in the original text.
5. Embed chunks in batches of 32.
6. Create ChunkRecord objects and add them to the FAISS vector store.
7. Persist the updated index to disk.
"""
import logging
import os
import re
import uuid
from typing import List, Tuple

import fitz  # PyMuPDF

from backend.rag.embedder import embedder
from backend.rag.vector_store import ChunkRecord, vector_store
from backend.utils.text_sanitizer import sanitize_pdf_text
from backend.utils.token_counter import count_tokens, get_last_n_tokens

logger = logging.getLogger(__name__)

# Separator hierarchy for recursive splitting (Section 3.2)
_SEPARATORS = ["\n\n", "\n", ". ", " "]

# Chunk parameters (Section 3.2 — immutable)
_CHUNK_SIZE = 512      # tokens
_CHUNK_OVERLAP = 64    # tokens

# PAGE_BREAK marker pattern used during ingestion
_PAGE_BREAK_PATTERN = re.compile(r"\[PAGE_BREAK:(\d+)\]")


# ---------------------------------------------------------------------------
# Step 1 — PDF text extraction
# ---------------------------------------------------------------------------


def extract_text_from_pdf(file_path: str) -> Tuple[str, int]:
    """
    Open a PDF and extract all page text, inserting [PAGE_BREAK:N] markers.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Tuple of (full_text, total_pages).
        full_text contains sanitized page text with [PAGE_BREAK:N] separators.

    Raises:
        ValueError: If the PDF has no extractable text (scanned image-only).
        RuntimeError: If PyMuPDF cannot open the file.
    """
    doc = fitz.open(file_path)
    total_pages = len(doc)
    full_text = ""

    for page_num in range(total_pages):
        page_text = doc[page_num].get_text("text")
        page_text = sanitize_pdf_text(page_text)
        full_text += page_text + f"\n[PAGE_BREAK:{page_num + 1}]\n"

    doc.close()

    # Check that at least some text was extracted
    stripped = _PAGE_BREAK_PATTERN.sub("", full_text).strip()
    if not stripped:
        raise ValueError(
            f"PDF '{os.path.basename(file_path)}' contains no extractable text. "
            "Scanned image-only PDFs are not supported."
        )

    return full_text, total_pages


# ---------------------------------------------------------------------------
# Step 2 — Recursive chunking
# ---------------------------------------------------------------------------


def _recursive_split(text: str, separators: List[str]) -> List[str]:
    """
    Recursively split `text` into chunks that each fit within _CHUNK_SIZE tokens.

    This implements the pseudocode from Section 3.2 exactly:
    - If the entire text fits within CHUNK_SIZE, return it as a single chunk.
    - Otherwise, split on the first viable separator, accumulate segments into
      a running buffer, and flush to a chunk (with overlap) when the buffer
      would overflow.
    - If no separator produces sub-chunks (pathological case), fall back to
      halving the text.

    Args:
        text: The text to split.
        separators: Ordered list of separator strings to try.

    Returns:
        List of text strings, each <= CHUNK_SIZE tokens.
    """
    if count_tokens(text) <= _CHUNK_SIZE:
        return [text]

    if not separators:
        # Pathological fallback: no separator left — split at midpoint by words.
        words = text.split()
        mid = max(1, len(words) // 2)
        return [" ".join(words[:mid]), " ".join(words[mid:])]

    sep = separators[0]
    remaining_seps = separators[1:]

    if sep not in text:
        # This separator is not present; try the next one.
        return _recursive_split(text, remaining_seps)

    segments = text.split(sep)
    chunks: List[str] = []
    current = ""

    for segment in segments:
        if not current:
            candidate = segment
        else:
            candidate = current + sep + segment

        if count_tokens(candidate) > _CHUNK_SIZE:
            if current:
                chunks.append(current)
                # Build overlap: take last CHUNK_OVERLAP tokens of `current`
                overlap_text = get_last_n_tokens(current, _CHUNK_OVERLAP)
                if overlap_text:
                    current = overlap_text + sep + segment
                else:
                    current = segment
            else:
                # Single segment already exceeds chunk size — recurse
                sub_chunks = _recursive_split(segment, remaining_seps)
                # The last sub-chunk becomes the new buffer (with overlap preserved)
                chunks.extend(sub_chunks[:-1])
                current = sub_chunks[-1] if sub_chunks else ""
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


def _build_page_map(full_text: str) -> List[Tuple[int, int]]:
    """
    Build a sorted list of (char_offset, page_number) from PAGE_BREAK markers.

    Used to map a character position in the cleaned text back to its source
    page number.
    """
    page_map: List[Tuple[int, int]] = []
    for match in _PAGE_BREAK_PATTERN.finditer(full_text):
        page_num = int(match.group(1))
        page_map.append((match.start(), page_num))
    return sorted(page_map, key=lambda x: x[0])


def _lookup_page(char_offset: int, page_map: List[Tuple[int, int]]) -> int:
    """
    Return the page number for a given character offset in the original text.

    Returns the page of the nearest PAGE_BREAK marker that appears at or
    before `char_offset`. Defaults to page 1 if no markers precede the offset.
    """
    page = 1
    for marker_offset, marker_page in page_map:
        if marker_offset <= char_offset:
            page = marker_page
        else:
            break
    return page


def chunk_text(full_text: str) -> List[dict]:
    """
    Split PDF text (with PAGE_BREAK markers) into overlap chunks.

    Args:
        full_text: Output of extract_text_from_pdf() — includes [PAGE_BREAK:N] markers.

    Returns:
        List of dicts with keys: text (clean), page_number.
    """
    # Build page map before stripping markers
    page_map = _build_page_map(full_text)

    # Strip PAGE_BREAK markers to get clean text for splitting
    clean_text = _PAGE_BREAK_PATTERN.sub("", full_text)

    # Recursively split
    raw_chunks = _recursive_split(clean_text, _SEPARATORS)

    # Assign page numbers by locating each chunk's position in clean_text
    result = []
    search_start = 0
    for chunk_text_content in raw_chunks:
        if not chunk_text_content.strip():
            continue

        # Find where this chunk appears in clean_text (from search_start forward)
        idx = clean_text.find(chunk_text_content, search_start)
        if idx == -1:
            # If exact match fails (can happen due to overlap), search from 0
            idx = clean_text.find(chunk_text_content)

        # Determine page by mapping clean_text offset back to original text position.
        # Because markers are stripped, we approximate: the ratio of characters
        # consumed gives us a position in the full_text.
        if idx >= 0:
            # Scale clean_text position to full_text position (approximate)
            ratio = idx / max(len(clean_text), 1)
            approx_full_offset = int(ratio * len(full_text))
            page_num = _lookup_page(approx_full_offset, page_map)
            search_start = idx + len(chunk_text_content)
        else:
            page_num = 1

        result.append({"text": chunk_text_content.strip(), "page_number": page_num})

    return result


# ---------------------------------------------------------------------------
# Step 3 — Full ingestion pipeline
# ---------------------------------------------------------------------------


def ingest_pdf(file_path: str) -> List[ChunkRecord]:
    """
    Full ingestion pipeline for a single PDF file.

    Steps:
    1. Extract text from PDF using PyMuPDF.
    2. Split into recursive chunks (512 tokens, 64-token overlap).
    3. Embed chunks in batches of 32.
    4. Create ChunkRecord objects.
    5. Add records to the FAISS vector store.
    6. Persist the updated index to disk.

    Args:
        file_path: Absolute path to a validated .pdf file.

    Returns:
        List of ChunkRecord objects that were added to the index.

    Raises:
        ValueError: If PDF has no extractable text.
        RuntimeError: If PyMuPDF fails to open the file.
    """
    filename = os.path.basename(file_path)
    logger.info("Starting ingestion of '%s'", filename)

    # Step 1: Extract text
    full_text, total_pages = extract_text_from_pdf(file_path)
    logger.info("'%s': extracted %d pages", filename, total_pages)

    # Step 2: Chunk text
    chunks_meta = chunk_text(full_text)
    logger.info("'%s': produced %d chunks", filename, len(chunks_meta))

    if not chunks_meta:
        raise ValueError(f"PDF '{filename}' produced no chunks after splitting.")

    # Step 3: Embed in batches of 32
    texts = [c["text"] for c in chunks_meta]
    embeddings = embedder.encode(texts, batch_size=32)  # shape (n, 384)

    # Step 4: Build ChunkRecord list
    records: List[ChunkRecord] = []
    for i, (meta, emb) in enumerate(zip(chunks_meta, embeddings)):
        record = ChunkRecord(
            chunk_id=str(uuid.uuid4()),
            text=meta["text"],
            source_file=filename,
            page_number=meta["page_number"],
            chunk_index=i,
            embedding=emb,
        )
        records.append(record)

    # Step 5: Add to vector store
    vector_store.add(records)

    # Step 6: Persist
    vector_store.persist()

    logger.info(
        "Ingestion complete for '%s': %d chunks added to FAISS index.",
        filename,
        len(records),
    )
    return records

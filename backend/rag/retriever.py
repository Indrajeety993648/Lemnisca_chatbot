"""
retriever.py — Top-k chunk retrieval with threshold filtering, re-ranking,
and deduplication.

Implements Sections 3.5 and 3.6 of ARCHITECTURE.md:

Retrieval (Section 3.5):
  - top-k = 5
  - similarity threshold = 0.35 (inner product after L2 normalization,
    equivalent to cosine similarity 0.35)
  - Chunks below the threshold are discarded even if in top-k
  - Invalid FAISS indices (-1) are skipped

Deduplication (Section 3.5):
  - If two chunks have > 80% text overlap (character-level Jaccard similarity),
    drop the lower-scored one.

Re-ranking (Section 3.6):
  - Sort by FAISS score descending (already guaranteed by FAISS).
  - Apply +0.05 score boost to chunks whose source_file contains a keyword
    from the query (e.g., "pricing" query → boost chunks from pricing_guide.pdf).
  - Re-sort after boost.
  - Return final ordered list.
"""
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from backend.config import settings
from backend.rag.embedder import embedder
from backend.rag.vector_store import vector_store

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A single chunk retrieved from the FAISS index with its metadata."""

    text: str
    source_file: str
    page_number: int
    score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "score": self.score,
        }


# ---------------------------------------------------------------------------
# Deduplication (Section 3.5)
# ---------------------------------------------------------------------------


def _jaccard_similarity(a: str, b: str) -> float:
    """
    Compute character-level Jaccard similarity between two strings.

    Jaccard(A, B) = |A ∩ B| / |A ∪ B| where A and B are sets of characters.
    Returns 0.0 if both strings are empty.
    """
    set_a = set(a)
    set_b = set(b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def deduplicate(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    """
    Remove duplicate chunks using character-level Jaccard similarity.

    If two chunks have > 80% character overlap, keep the one with the higher
    similarity score. The comparison is done against all already-accepted
    chunks so that the result set has no pair with > 80% overlap.
    """
    if not chunks:
        return []

    accepted: List[RetrievedChunk] = []

    for candidate in chunks:
        is_duplicate = False
        for existing in accepted:
            sim = _jaccard_similarity(candidate.text, existing.text)
            if sim > 0.80:
                # Keep the higher-scored chunk
                if candidate.score > existing.score:
                    existing.text = candidate.text
                    existing.score = candidate.score
                    existing.source_file = candidate.source_file
                    existing.page_number = candidate.page_number
                is_duplicate = True
                break
        if not is_duplicate:
            accepted.append(candidate)

    return accepted


# ---------------------------------------------------------------------------
# Re-ranking (Section 3.6)
# ---------------------------------------------------------------------------


def _extract_filename_keywords(source_file: str) -> List[str]:
    """
    Derive keywords from a PDF filename for re-ranking purposes.

    Splits on underscores, hyphens, and dots, removes the .pdf extension,
    and filters out tokens shorter than 3 characters.

    Example: "pricing_guide_v2.pdf" → ["pricing", "guide"]
    """
    stem = re.sub(r"\.pdf$", "", source_file, flags=re.IGNORECASE)
    tokens = re.split(r"[_\-.\s]+", stem)
    return [t.lower() for t in tokens if len(t) >= 3]


def _apply_reranking_boost(
    chunks: List[RetrievedChunk], query_lower: str
) -> List[RetrievedChunk]:
    """
    Apply a +0.05 score boost to chunks whose source_file contains a keyword
    that also appears in the query.

    Per Section 3.6: re-sort after boost.
    """
    for chunk in chunks:
        keywords = _extract_filename_keywords(chunk.source_file)
        for kw in keywords:
            if kw in query_lower:
                chunk.score += 0.05
                break  # Only one boost per chunk

    chunks.sort(key=lambda c: c.score, reverse=True)
    return chunks


# ---------------------------------------------------------------------------
# Main retrieval function
# ---------------------------------------------------------------------------


def retrieve(
    query: str,
    k: int = settings.TOP_K,
    threshold: float = settings.SIMILARITY_THRESHOLD,
) -> List[RetrievedChunk]:
    """
    Retrieve the top-k relevant chunks for a query from the FAISS index.

    Pipeline:
    1. Embed the query (L2-normalized float32 vector, shape (384,)).
    2. FAISS inner-product search for k nearest neighbours.
    3. Filter out invalid indices (-1) and chunks below the score threshold.
    4. Apply re-ranking boost (+0.05 for source-filename keyword match).
    5. Deduplicate (character-level Jaccard > 0.80 → keep higher score).
    6. Return final ordered list.

    Args:
        query: Raw user query string (not yet embedded).
        k: Number of nearest neighbours to retrieve. Default: 5.
        threshold: Minimum similarity score to include a chunk. Default: 0.35.

    Returns:
        List of RetrievedChunk objects, ordered by score descending,
        de-duplicated, and re-ranked.
    """
    query_embedding = embedder.encode(query)
    raw_results = vector_store.search(query_embedding, k=k)

    retrieved: List[RetrievedChunk] = []
    for res in raw_results:
        score = res["score"]
        if score < threshold:
            continue  # Below similarity threshold — discard
        retrieved.append(
            RetrievedChunk(
                text=res["text"],
                source_file=res["source_file"],
                page_number=res["page_number"],
                score=score,
            )
        )

    logger.debug(
        "Retrieval: %d/%d chunks passed threshold %.2f for query '%s...'",
        len(retrieved),
        len(raw_results),
        threshold,
        query[:60],
    )

    # Re-ranking
    query_lower = query.lower()
    retrieved = _apply_reranking_boost(retrieved, query_lower)

    # Deduplication
    retrieved = deduplicate(retrieved)

    return retrieved

"""
vector_store.py — FAISS IndexFlatIP management.

Implements the VectorStore class responsible for:
- Holding a FAISS IndexFlatIP (flat inner product) index in memory.
- Persisting the index to disk as index.faiss and chunk metadata to index.pkl.
- Loading the index from disk on startup.
- Validating embedding dimensionality on load (must be 384).
- Adding new ChunkRecord objects to the index.
- Performing similarity search against the index.

Per Section 3.4 of ARCHITECTURE.md:
  Index type: IndexFlatIP
  Persistence: index.faiss (FAISS binary) + index.pkl (Python pickle of metadata list)
  ID mapping: FAISS internal IDs are sequential integers == metadata list indices.
"""
import logging
import os
import pickle
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from backend.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ChunkRecord:
    """
    Represents a single text chunk with its embedding and metadata.

    The embedding field is excluded from dict serialization (it is stored
    directly in the FAISS index, not in the pickle sidecar).
    """

    chunk_id: str
    text: str
    source_file: str
    page_number: int
    chunk_index: int
    embedding: Optional[np.ndarray] = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable metadata (no embedding)."""
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
        }


class VectorStore:
    """
    FAISS IndexFlatIP vector store with pickle metadata sidecar.

    Usage:
        vector_store.load()          # On startup — idempotent if no file exists
        vector_store.add(records)    # After ingestion
        vector_store.persist()       # Save index + metadata to disk
        results = vector_store.search(query_embedding, k=5)
    """

    def __init__(
        self,
        index_dir: str = settings.FAISS_INDEX_PATH,
        dimension: int = settings.EMBEDDING_DIM,
    ) -> None:
        self.index_dir = index_dir
        self.faiss_path = os.path.join(index_dir, "index.faiss")
        self.pkl_path = os.path.join(index_dir, "index.pkl")
        self.dimension = dimension

        # In-memory state — populated by load() or add()
        self._index: Optional[faiss.IndexFlatIP] = None
        self._metadata: List[Dict[str, Any]] = []
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Startup / Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """
        Load the FAISS index and metadata from disk.

        If no index file exists, initialises an empty IndexFlatIP.
        If the file exists but has a dimensionality mismatch, raises RuntimeError
        so main.py can refuse to start (per Section 8 — Fault Tolerance).
        This method is idempotent.
        """
        if os.path.exists(self.faiss_path) and os.path.exists(self.pkl_path):
            logger.info("Loading FAISS index from %s", self.faiss_path)
            index = faiss.read_index(self.faiss_path)

            # Validate dimensionality
            loaded_dim = index.d
            if loaded_dim != self.dimension:
                raise RuntimeError(
                    f"FAISS index dimension mismatch: expected {self.dimension}, got {loaded_dim}"
                )

            with open(self.pkl_path, "rb") as fh:
                metadata = pickle.load(fh)

            self._index = index
            self._metadata = metadata
            logger.info(
                "FAISS index loaded — %d chunks, dimension %d",
                self._index.ntotal,
                loaded_dim,
            )
        else:
            logger.info(
                "No FAISS index found at %s — initialising empty index (dim=%d).",
                self.faiss_path,
                self.dimension,
            )
            self._index = faiss.IndexFlatIP(self.dimension)
            self._metadata = []

        self._loaded = True

    def _ensure_loaded(self) -> None:
        """Ensure the index is initialised. Called before any read/write operation."""
        if not self._loaded:
            self.load()

    def persist(self) -> None:
        """
        Save the FAISS index and metadata to disk.

        Creates the index directory if it does not exist.
        """
        self._ensure_loaded()
        os.makedirs(self.index_dir, exist_ok=True)
        faiss.write_index(self._index, self.faiss_path)
        with open(self.pkl_path, "wb") as fh:
            pickle.dump(self._metadata, fh)
        logger.info(
            "FAISS index persisted — %d chunks at %s",
            self._index.ntotal,
            self.faiss_path,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add(self, records: List[ChunkRecord]) -> None:
        """
        Add a list of ChunkRecord objects to the index.

        Each record must have a non-None embedding of shape (384,).
        Embeddings must already be L2-normalized (done by Embedder).
        FAISS assigns sequential integer IDs that correspond 1:1 to
        the positions in self._metadata (ID == metadata list index).
        """
        self._ensure_loaded()
        if not records:
            return

        embeddings = np.array(
            [r.embedding for r in records], dtype=np.float32
        )

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {embeddings.shape[1]}"
            )

        self._index.add(embeddings)
        for r in records:
            self._metadata.append(r.to_dict())

        logger.debug("Added %d chunks to FAISS index (total: %d)", len(records), self._index.ntotal)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def search(
        self, query_embedding: np.ndarray, k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform inner-product nearest-neighbour search.

        Args:
            query_embedding: L2-normalized float32 vector of shape (384,).
            k: Number of neighbours to retrieve.

        Returns:
            List of dicts with keys: chunk_id, text, source_file,
            page_number, chunk_index, score. Ordered by score descending.
            Invalid FAISS indices (-1) are filtered out automatically.
        """
        self._ensure_loaded()

        if self._index.ntotal == 0:
            return []

        query = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = dict(self._metadata[idx])
            meta["score"] = float(score)
            results.append(meta)

        return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_total_chunks(self) -> int:
        """Return the number of vectors currently stored in the FAISS index."""
        self._ensure_loaded()
        return self._index.ntotal

    def get_dimension(self) -> int:
        """Return the dimensionality of the FAISS index."""
        self._ensure_loaded()
        return self._index.d

    def is_loaded(self) -> bool:
        """Return True if the index has been initialised (load() was called)."""
        return self._loaded


# Module-level singleton used throughout the backend.
vector_store = VectorStore()

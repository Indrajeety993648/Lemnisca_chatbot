"""
embedder.py — Embedding model wrapper.

Wraps sentence-transformers/all-MiniLM-L6-v2 for:
- Single-text and batch embedding.
- L2 normalization of all embeddings before they are inserted into FAISS.
  After L2 normalization, inner-product search (IndexFlatIP) is equivalent
  to cosine similarity, as specified in Section 3.3 of ARCHITECTURE.md.

Model specification (Section 3.3):
  - Model: sentence-transformers/all-MiniLM-L6-v2
  - Embedding dimensionality: 384
  - Max sequence length: 256 tokens (model hard limit; chunks that exceed
    this are truncated to the first 256 model tokens)
  - L2 normalization: applied to every output vector
  - Batch size for ingestion: 32
"""
import logging
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_EMBEDDING_DIM = 384
_INGESTION_BATCH_SIZE = 32


class Embedder:
    """Thin wrapper around SentenceTransformer for embedding and L2 normalization."""

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        logger.info("Loading embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)
        self.dimension: int = self.model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded — dimension: %d", self.dimension)

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = _INGESTION_BATCH_SIZE,
    ) -> np.ndarray:
        """
        Embed one or more texts and return L2-normalized float32 embeddings.

        Args:
            texts: A single string or a list of strings to embed.
            batch_size: Mini-batch size for the SentenceTransformer forward pass.
                        Defaults to 32 as specified in Section 3.3.

        Returns:
            np.ndarray of shape (n, 384) for a list of texts, or (384,) for a
            single string. All vectors are L2-normalized (unit length).
        """
        single = isinstance(texts, str)
        if single:
            texts = [texts]

        embeddings: np.ndarray = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,  # We apply our own L2 normalization below.
        ).astype(np.float32)

        # L2 normalization: divide each vector by its L2 norm.
        # Using np.divide with `where` guard prevents NaN from zero-norm vectors.
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = np.divide(
            embeddings, norms, out=np.zeros_like(embeddings), where=norms != 0
        )

        if single:
            return embeddings[0]  # shape (384,)
        return embeddings  # shape (n, 384)


# Module-level singleton used throughout the backend.
embedder = Embedder()

"""
token_counter.py — Token counting utilities for the RAG pipeline.

Uses the WordPiece tokenizer from sentence-transformers/all-MiniLM-L6-v2
to measure token counts for chunking. Falls back to a word-based
approximation (1 token per 0.75 words) if the tokenizer cannot be loaded.

Per Section 3.2 of ARCHITECTURE.md:
  chunk_size = 512 tokens
  chunk_overlap = 64 tokens
  Measured by the tokenizer of all-MiniLM-L6-v2.
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Module-level tokenizer instance (lazy-loaded on first use).
_tokenizer = None
_tokenizer_load_failed = False


def _get_tokenizer():
    """
    Lazy-load the all-MiniLM-L6-v2 tokenizer. Results are cached module-globally.
    If loading fails, _tokenizer_load_failed is set so subsequent calls use
    the word-based fallback without retrying.
    """
    global _tokenizer, _tokenizer_load_failed
    if _tokenizer is not None:
        return _tokenizer
    if _tokenizer_load_failed:
        return None
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        _tokenizer = model.tokenizer
        logger.info("Token counter: loaded tokenizer from all-MiniLM-L6-v2")
        return _tokenizer
    except Exception as exc:
        logger.warning(
            "Token counter: failed to load tokenizer (%s). "
            "Falling back to word-based approximation.",
            exc,
        )
        _tokenizer_load_failed = True
        return None


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in `text` using the all-MiniLM-L6-v2 tokenizer.

    Falls back to the word-based approximation (words / 0.75) if the
    tokenizer is unavailable.
    """
    if not text:
        return 0

    tokenizer = _get_tokenizer()
    if tokenizer is not None:
        try:
            # encode() returns a list of token IDs without special tokens by default.
            # add_special_tokens=False mirrors the effective content token count.
            token_ids = tokenizer.encode(text, add_special_tokens=False)
            return len(token_ids)
        except Exception:
            pass

    # Fallback: approximate via whitespace splitting
    # 1 token ≈ 0.75 words → tokens ≈ words / 0.75 ≈ words * 1.333
    words = text.split()
    return int(len(words) / 0.75)


def get_last_n_tokens(text: str, n: int) -> str:
    """
    Return the last `n` tokens of `text` as a decoded string.

    Used to construct the overlap region when splitting a chunk that
    exceeded the target chunk size. The returned text is then prepended
    to the next chunk.
    """
    if not text or n <= 0:
        return ""

    tokenizer = _get_tokenizer()
    if tokenizer is not None:
        try:
            token_ids = tokenizer.encode(text, add_special_tokens=False)
            last_ids = token_ids[-n:]
            return tokenizer.decode(last_ids)
        except Exception:
            pass

    # Fallback: word-based approximation
    # n tokens ≈ n * 0.75 words
    words = text.split()
    word_count = max(1, int(n * 0.75))
    return " ".join(words[-word_count:])

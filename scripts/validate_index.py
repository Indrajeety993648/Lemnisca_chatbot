#!/usr/bin/env python3
"""
validate_index.py — Verify FAISS index integrity.

Loads the FAISS index from the configured path, checks:
  1. Index file and metadata sidecar exist.
  2. Index dimensionality matches EMBEDDING_DIM (384).
  3. Total chunk count.
  4. Prints a sample of metadata entries (first 3).

Exit codes:
  0 — Index is valid.
  1 — Index is missing or invalid.
"""
import os
import pickle
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

EXPECTED_DIM = 384
DEFAULT_INDEX_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "data", "faiss_index"
)


def validate_index(index_dir: str = DEFAULT_INDEX_PATH) -> bool:
    """
    Validate the FAISS index at index_dir.

    Returns True if valid, False otherwise.
    """
    index_file = os.path.join(index_dir, "index.faiss")
    metadata_file = os.path.join(index_dir, "index.pkl")

    print(f"Validating FAISS index at: {os.path.abspath(index_dir)}")
    print("-" * 60)

    # Check files exist
    if not os.path.exists(index_file):
        print(f"[FAIL] index.faiss not found at: {index_file}")
        print("       Run the ingestion pipeline first to create the index.")
        return False

    if not os.path.exists(metadata_file):
        print(f"[FAIL] index.pkl not found at: {metadata_file}")
        print("       Metadata sidecar is missing — re-ingest all documents.")
        return False

    print(f"[OK]   index.faiss exists ({os.path.getsize(index_file):,} bytes)")
    print(f"[OK]   index.pkl exists    ({os.path.getsize(metadata_file):,} bytes)")

    # Load and validate FAISS index
    try:
        import faiss  # type: ignore

        index = faiss.read_index(index_file)
        actual_dim = index.d
        total_vectors = index.ntotal

        if actual_dim != EXPECTED_DIM:
            print(
                f"[FAIL] Dimension mismatch: expected {EXPECTED_DIM}, got {actual_dim}."
            )
            print("       Re-ingest all documents to rebuild with correct embeddings.")
            return False

        print(f"[OK]   Dimensionality: {actual_dim} (matches expected {EXPECTED_DIM})")
        print(f"[OK]   Total vectors in index: {total_vectors:,}")

    except ImportError:
        print("[WARN] faiss-cpu not installed — skipping index dimension check.")
    except Exception as exc:
        print(f"[FAIL] Failed to load FAISS index: {exc}")
        return False

    # Load and validate metadata
    try:
        with open(metadata_file, "rb") as fh:
            metadata = pickle.load(fh)

        if not isinstance(metadata, list):
            print(f"[FAIL] Metadata is not a list (got {type(metadata).__name__}).")
            return False

        print(f"[OK]   Chunk metadata entries: {len(metadata):,}")

        if metadata:
            print("\nSample metadata (first 3 entries):")
            for i, entry in enumerate(metadata[:3]):
                print(f"  [{i}] chunk_id={entry.get('chunk_id', 'N/A')!r}"
                      f"  source={entry.get('source_file', 'N/A')!r}"
                      f"  page={entry.get('page_number', 'N/A')}")

    except Exception as exc:
        print(f"[FAIL] Failed to load metadata: {exc}")
        return False

    print("\n[PASS] FAISS index is valid and ready.")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate the Clearpath FAISS index.")
    parser.add_argument(
        "--index-dir",
        default=DEFAULT_INDEX_PATH,
        help="Path to the faiss_index directory (default: backend/data/faiss_index)",
    )
    args = parser.parse_args()

    success = validate_index(args.index_dir)
    sys.exit(0 if success else 1)

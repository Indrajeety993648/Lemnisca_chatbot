"""
config.py — Application configuration loaded from environment variables.

All variables use the CLEARPATH_ prefix as specified in Section 9.1 of ARCHITECTURE.md.
"""
import os
import json
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with CLEARPATH_ prefix.
    Values can be overridden via a .env file at the project root.
    """

    # --- Application ---
    PROJECT_NAME: str = "Clearpath RAG Chatbot"
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = Field(default="INFO", description="Python logging level: DEBUG, INFO, WARNING, ERROR")

    # --- Groq API ---
    GROQ_API_KEY: str = Field(..., description="Groq API key — required")

    # --- CORS ---
    # Use str type so pydantic-settings v2 does NOT attempt JSON pre-parsing.
    # The allowed_origins property converts it to List[str] at access time.
    ALLOWED_ORIGINS_RAW: str = Field(
        default="http://localhost:5173",
        alias="CLEARPATH_ALLOWED_ORIGINS",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Return ALLOWED_ORIGINS_RAW parsed as a list."""
        v = self.ALLOWED_ORIGINS_RAW
        # Try JSON array first: ["http://...", "http://..."]
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(o).strip() for o in parsed if str(o).strip()]
        except (json.JSONDecodeError, TypeError):
            pass
        # Fall back to comma-separated string
        return [o.strip() for o in v.split(",") if o.strip()]

    # --- File Paths ---
    FAISS_INDEX_PATH: str = Field(
        default="backend/data/faiss_index",
        description="Directory containing index.faiss and index.pkl",
    )
    PDF_DIR: str = Field(
        default="backend/data/pdfs",
        description="Directory where uploaded PDFs are stored",
    )
    LOG_FILE_PATH: str = Field(
        default="backend/data/logs/queries.jsonl",
        description="Append-only JSONL query log file",
    )

    # --- RAG Parameters (immutable per Section 3) ---
    CHUNK_SIZE: int = Field(default=512, description="Target chunk size in tokens")
    CHUNK_OVERLAP: int = Field(default=64, description="Token overlap between consecutive chunks")
    TOP_K: int = Field(default=5, description="Number of chunks to retrieve per query")
    SIMILARITY_THRESHOLD: float = Field(
        default=0.35, description="Minimum inner-product score to accept a retrieved chunk"
    )
    EMBEDDING_DIM: int = Field(default=384, description="Embedding dimension for all-MiniLM-L6-v2")

    # --- Groq Model IDs (immutable per Section 4.1) ---
    SIMPLE_MODEL: str = Field(default="llama-3.1-8b-instant", description="Model for simple queries")
    COMPLEX_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Model for complex queries")

    # --- Rate Limiting ---
    RATE_LIMIT_QUERY_PER_MINUTE: int = Field(default=30, description="Per-IP rate limit for /api/query")
    RATE_LIMIT_INGEST_PER_MINUTE: int = Field(default=5, description="Per-IP rate limit for /api/ingest")

    # --- Upload Limits ---
    MAX_FILE_SIZE_BYTES: int = Field(default=50 * 1024 * 1024, description="50 MB max PDF upload size")

    model_config = SettingsConfigDict(
        env_prefix="CLEARPATH_",
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )


settings = Settings()

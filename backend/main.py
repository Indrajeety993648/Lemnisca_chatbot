"""
main.py — FastAPI application entrypoint for the Clearpath RAG Chatbot.

Responsibilities:
- Create the FastAPI app with metadata.
- Configure CORS middleware using CLEARPATH_ALLOWED_ORIGINS.
- Register the lifespan context manager:
    - Startup: load FAISS index, validate embedding dimensionality.
    - Shutdown: log graceful stop.
- Include all API routers under the /api prefix.
- Expose a root diagnostic route.
"""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

# Configure application-level logger (stdout, suitable for container environments).
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager executed on startup and shutdown.

    Startup:
      1. Load FAISS index from disk into the global VectorStore instance.
      2. Validate that the loaded index dimensionality matches EMBEDDING_DIM (384).
         If there is a mismatch, log a critical error and raise RuntimeError
         so the server refuses to start (per Section 8 — Fault Tolerance).

    Shutdown:
      - Log graceful stop message.
    """
    # Import here to avoid circular import at module load time.
    from backend.rag.vector_store import vector_store

    logger.info("Startup: loading FAISS index from '%s'", settings.FAISS_INDEX_PATH)
    try:
        vector_store.load()
        loaded_dim = vector_store.get_dimension()
        if loaded_dim != settings.EMBEDDING_DIM:
            logger.critical(
                "FAISS index dimension mismatch: expected %d, got %d. "
                "Refusing to start — re-ingest all documents.",
                settings.EMBEDDING_DIM,
                loaded_dim,
            )
            raise RuntimeError(
                f"FAISS index dimension mismatch: expected {settings.EMBEDDING_DIM}, "
                f"got {loaded_dim}"
            )
        logger.info(
            "FAISS index loaded: %d chunks, dimension %d",
            vector_store.get_total_chunks(),
            loaded_dim,
        )
    except FileNotFoundError:
        logger.info(
            "No FAISS index at '%s' — starting with empty index.",
            settings.FAISS_INDEX_PATH,
        )

    yield

    logger.info("Shutdown: Clearpath backend stopping.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Clearpath RAG-based customer support chatbot API",
    lifespan=lifespan,
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)

# --- API Routers ---
# Imported after app creation to avoid circular imports.
from backend.api import routes_debug, routes_health, routes_ingest, routes_logs, routes_query  # noqa: E402

app.include_router(routes_query.router, prefix="/api", tags=["Query"])
app.include_router(routes_ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(routes_debug.router, prefix="/api", tags=["Debug"])
app.include_router(routes_logs.router, prefix="/api", tags=["Logs"])
app.include_router(routes_health.router, prefix="/api", tags=["Health"])


@app.get("/", include_in_schema=False)
async def root():
    """Root route — confirms the API is running."""
    return {"message": "Clearpath RAG Chatbot API is running", "version": settings.VERSION}


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )

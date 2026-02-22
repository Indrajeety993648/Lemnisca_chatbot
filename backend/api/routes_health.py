"""
routes_health.py — GET /api/health endpoint.

Returns system health status including FAISS index state, Groq API
reachability, and server uptime.

Per Section 6.5 of ARCHITECTURE.md:
  - 200: always returned (even when status='degraded')

The server start time is stored as a module-level variable in this module
rather than in main.py to avoid circular imports.
"""
import logging
import time

import httpx
from fastapi import APIRouter

from backend.api.schemas import HealthResponse
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Server start time — set once when this module is first imported.
# Since FastAPI loads all routers at startup, this approximates the
# process start time accurately.
_SERVER_START_TIME: float = time.time()


async def _check_groq_reachable() -> bool:
    """
    Lightweight reachability check against the Groq API.

    Sends a GET request to the Groq models listing endpoint. Any HTTP
    response (including 401 Unauthorized) means the API is reachable.
    Returns False on connection errors, timeouts, or 5xx responses.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            )
            # 200/401/403 all mean the endpoint is reachable
            return response.status_code < 500
    except Exception:
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health_endpoint():
    """
    Health check endpoint.

    Checks:
    1. Whether the FAISS index is loaded in memory.
    2. Whether the Groq API is network-reachable.
    3. Server uptime in seconds.

    Always returns HTTP 200. The 'status' field is 'healthy' if all
    subsystems are operational, 'degraded' if any check fails.
    """
    from backend.rag.vector_store import vector_store

    faiss_loaded = vector_store.is_loaded()
    total_chunks = vector_store.get_total_chunks()
    groq_reachable = await _check_groq_reachable()
    uptime = time.time() - _SERVER_START_TIME

    overall_status = "healthy" if faiss_loaded and groq_reachable else "degraded"

    return HealthResponse(
        status=overall_status,
        faiss_index_loaded=faiss_loaded,
        total_chunks=total_chunks,
        groq_api_reachable=groq_reachable,
        uptime_seconds=round(uptime, 2),
    )

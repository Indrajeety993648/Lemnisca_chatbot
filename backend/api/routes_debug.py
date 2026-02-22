"""
routes_debug.py — GET /api/debug endpoint.

Returns structured debug information for the last N queries from the
queries.jsonl log file.

Per Section 6.3 of ARCHITECTURE.md:
  - 200: success
  - 400: invalid `n` parameter (handled by FastAPI query param validation)
"""
import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.api.schemas import DebugResponse
from backend.logging_.structured_logger import get_recent_logs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/debug",
    response_model=DebugResponse,
    responses={400: {"description": "Invalid n parameter"}},
)
async def debug_endpoint(
    n: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of recent query log entries to return (1–100)",
    )
):
    """
    Retrieve debug information for the last N queries.

    Reads from the append-only queries.jsonl log file and returns the
    most recent `n` entries in reverse-chronological order.
    """
    try:
        entries = get_recent_logs(n=n)
    except Exception as exc:
        logger.exception("Failed to read debug logs")
        raise HTTPException(status_code=500, detail=f"Could not read logs: {exc}")

    return DebugResponse(entries=entries, total_count=len(entries))

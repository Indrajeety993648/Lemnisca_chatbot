"""
routes_logs.py — GET /api/logs endpoint.

Returns raw structured log entries from queries.jsonl with offset/limit
pagination support.

Per Section 6.4 of ARCHITECTURE.md:
  - 200: success
  - 400: invalid parameters (handled by FastAPI query param validation)
"""
import logging

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import LogEntry, LogsResponse
from backend.logging_.structured_logger import get_all_logs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/logs",
    response_model=LogsResponse,
    responses={400: {"description": "Invalid offset or limit parameter"}},
)
async def logs_endpoint(
    offset: int = Query(
        default=0,
        ge=0,
        description="Starting position in the log file (0-indexed)",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of log entries to return (1–500)",
    ),
):
    """
    Retrieve raw structured logs with offset/limit pagination.

    Reads all entries from queries.jsonl, applies pagination, and returns
    the requested slice together with the total entry count.
    """
    try:
        all_logs = get_all_logs()
    except Exception as exc:
        logger.exception("Failed to read logs for /api/logs")
        raise HTTPException(status_code=500, detail=f"Could not read logs: {exc}")

    total = len(all_logs)
    paged = all_logs[offset: offset + limit]

    return LogsResponse(
        logs=paged,
        total=total,
        offset=offset,
        limit=limit,
    )

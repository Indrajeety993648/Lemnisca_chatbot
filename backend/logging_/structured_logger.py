"""
structured_logger.py — JSON structured logging for all query events.

Writes one JSON object per line (JSONL format) to the configured log file
(CLEARPATH_LOG_FILE_PATH, default: backend/data/logs/queries.jsonl).

Log entry format (Section 4.3 of ARCHITECTURE.md — immutable):
{
    "request_id": "uuid4-string",
    "timestamp": "ISO-8601 datetime with timezone (UTC)",
    "query": "the raw user query text",
    "classification": "simple | complex",
    "model_used": "llama-3.1-8b-instant | llama-3.3-70b-versatile",
    "tokens_input": 0,
    "tokens_output": 0,
    "latency_ms": 0.0,
    "retrieval_count": 0,
    "retrieval_scores": [],
    "evaluator_flags": [],
    "error": null
}

Log rotation (Section 8 — Logging):
  Rotate when file exceeds 100 MB.
  Rotated files named: queries_YYYYMMDD_HHMMSS.jsonl
  Retention: 30 days.
"""
import glob
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import List, Optional

from backend.api.schemas import LogEntry
from backend.config import settings

logger = logging.getLogger(__name__)

# Rotation threshold: 100 MB
_ROTATION_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100 MB

# Retention period for rotated files: 30 days
_RETENTION_SECONDS = 30 * 24 * 60 * 60


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_log_dir() -> None:
    """Create the log directory if it does not exist."""
    log_dir = os.path.dirname(settings.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)


def _rotate_if_needed() -> None:
    """
    Rotate the log file if it exceeds the 100 MB threshold.

    The current file is renamed to queries_YYYYMMDD_HHMMSS.jsonl and a
    fresh file is started. Old rotated files older than 30 days are deleted.
    """
    try:
        if not os.path.exists(settings.LOG_FILE_PATH):
            return

        size = os.path.getsize(settings.LOG_FILE_PATH)
        if size < _ROTATION_THRESHOLD_BYTES:
            return

        # Build rotated filename
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.dirname(settings.LOG_FILE_PATH)
        rotated_name = f"queries_{timestamp_str}.jsonl"
        rotated_path = os.path.join(log_dir, rotated_name)

        os.rename(settings.LOG_FILE_PATH, rotated_path)
        logger.info("Log rotated: %s → %s", settings.LOG_FILE_PATH, rotated_path)

        # Delete rotated files older than 30 days
        pattern = os.path.join(log_dir, "queries_*.jsonl")
        now = time.time()
        for old_file in glob.glob(pattern):
            if os.path.getmtime(old_file) < now - _RETENTION_SECONDS:
                os.remove(old_file)
                logger.info("Deleted old log file: %s", old_file)

    except OSError as exc:
        logger.warning("Log rotation failed: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def log_query(
    request_id: str,
    query: str,
    classification: str,
    model_used: str,
    tokens_input: int,
    tokens_output: int,
    latency_ms: float,
    retrieval_count: int,
    retrieval_scores: List[float],
    evaluator_flags: List[str],
    error: Optional[str] = None,
) -> None:
    """
    Append a single structured JSON log entry to queries.jsonl.

    Fields match the exact schema defined in Section 4.3 of ARCHITECTURE.md.
    The timestamp is always in UTC ISO-8601 format with timezone offset.
    """
    entry = {
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "classification": classification,
        "model_used": model_used,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "latency_ms": latency_ms,
        "retrieval_count": retrieval_count,
        "retrieval_scores": retrieval_scores,
        "evaluator_flags": evaluator_flags,
        "error": error,
    }

    try:
        _ensure_log_dir()
        _rotate_if_needed()

        with open(settings.LOG_FILE_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    except OSError as exc:
        logger.error("Failed to write log entry for request_id=%s: %s", request_id, exc)


def _parse_log_line(line: str) -> Optional[LogEntry]:
    """
    Parse a single JSONL line into a LogEntry Pydantic model.

    Returns None if the line is malformed or cannot be validated.
    """
    try:
        data = json.loads(line.strip())
        return LogEntry(**data)
    except (json.JSONDecodeError, Exception):
        return None


def get_all_logs() -> List[LogEntry]:
    """
    Read and parse all entries from the queries.jsonl log file.

    Returns:
        List of LogEntry objects in the order they appear in the file
        (i.e., chronological order). Malformed lines are silently skipped.
    """
    if not os.path.exists(settings.LOG_FILE_PATH):
        return []

    entries: List[LogEntry] = []
    try:
        with open(settings.LOG_FILE_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    entry = _parse_log_line(line)
                    if entry is not None:
                        entries.append(entry)
    except OSError as exc:
        logger.error("Failed to read log file: %s", exc)

    return entries


def get_recent_logs(n: int = 10) -> List[LogEntry]:
    """
    Return the last `n` log entries from queries.jsonl.

    Reads the entire file and returns the tail. For large log files the
    rotation mechanism ensures the active file stays under 100 MB.

    Args:
        n: Number of entries to return (most recent first).

    Returns:
        List of up to `n` LogEntry objects in reverse-chronological order.
    """
    all_entries = get_all_logs()
    return list(reversed(all_entries[-n:]))

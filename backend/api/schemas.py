"""
schemas.py — Pydantic v2 request/response models for all API endpoints.

Defined per Section 6 of ARCHITECTURE.md. All models use Field() for
validation constraints. No additional fields beyond the specification.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------


class Source(BaseModel):
    """A single retrieved source chunk referenced in a query response."""

    source_file: str = Field(..., description="Original PDF filename")
    page_number: int = Field(..., description="1-indexed page number the chunk came from")
    score: float = Field(..., description="Similarity score (inner product after L2 norm)")


class DebugInfo(BaseModel):
    """Debug metadata attached to every query response."""

    classification: Literal["simple", "complex"] = Field(
        ..., description="Router classification result"
    )
    model_used: str = Field(..., description="Groq model ID used for generation")
    tokens_input: int = Field(default=0, description="Prompt token count")
    tokens_output: int = Field(default=0, description="Completion token count")
    latency_ms: float = Field(..., description="End-to-end latency in milliseconds")
    retrieval_count: int = Field(..., description="Number of chunks that passed the threshold")
    evaluator_flags: List[str] = Field(
        default_factory=list,
        description="Flags from the output evaluator: no_context_warning, refusal_detected, potential_hallucination",
    )


# ---------------------------------------------------------------------------
# /api/query
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    """Request body for POST /api/query."""

    query: str = Field(
        ...,
        max_length=2000,
        description="The user's natural language question",
    )
    stream: bool = Field(
        default=False,
        description="If true, response is streamed via SSE (text/event-stream)",
    )


class QueryResponse(BaseModel):
    """Non-streaming response body for POST /api/query."""

    request_id: str = Field(..., description="UUID4 identifier for this request")
    answer: str = Field(..., description="Generated answer from the LLM")
    sources: List[Source] = Field(
        default_factory=list, description="Retrieved source chunks used for context"
    )
    debug: DebugInfo = Field(..., description="Debug and routing metadata")


# ---------------------------------------------------------------------------
# /api/ingest
# ---------------------------------------------------------------------------


class IngestResponse(BaseModel):
    """Response body for POST /api/ingest."""

    status: Literal["success", "error"] = Field(..., description="Processing status")
    filename: str = Field(..., description="Sanitized filename of the uploaded PDF")
    chunks_created: int = Field(..., description="Number of chunks added to the FAISS index")
    total_pages: int = Field(..., description="Total page count of the ingested PDF")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")


# ---------------------------------------------------------------------------
# /api/debug and /api/logs — shared log entry model
# ---------------------------------------------------------------------------


class LogEntry(BaseModel):
    """A single structured log entry as defined in Section 4.3 of ARCHITECTURE.md."""

    request_id: str = Field(..., description="UUID4 request identifier")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    query: str = Field(..., description="Raw user query text")
    classification: str = Field(..., description="Router classification: simple | complex")
    model_used: str = Field(..., description="Groq model ID used")
    tokens_input: int = Field(default=0, description="Prompt token count")
    tokens_output: int = Field(default=0, description="Completion token count")
    latency_ms: float = Field(default=0.0, description="End-to-end latency in milliseconds")
    retrieval_count: int = Field(default=0, description="Chunks that passed threshold")
    retrieval_scores: List[float] = Field(
        default_factory=list, description="Similarity scores of retrieved chunks"
    )
    evaluator_flags: List[str] = Field(
        default_factory=list, description="Output evaluator flags"
    )
    error: Optional[str] = Field(default=None, description="Error message if request failed")


class DebugResponse(BaseModel):
    """Response body for GET /api/debug."""

    entries: List[LogEntry] = Field(..., description="Recent log entries")
    total_count: int = Field(..., description="Number of entries returned")


class LogsResponse(BaseModel):
    """Response body for GET /api/logs."""

    logs: List[LogEntry] = Field(..., description="Paginated log entries")
    total: int = Field(..., description="Total number of log entries in the file")
    offset: int = Field(..., description="Pagination offset used")
    limit: int = Field(..., description="Pagination limit used")


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Response body for GET /api/health."""

    status: Literal["healthy", "degraded"] = Field(..., description="Overall system health")
    faiss_index_loaded: bool = Field(..., description="True if FAISS index is in memory")
    total_chunks: int = Field(..., description="Number of chunks currently in the FAISS index")
    groq_api_reachable: bool = Field(..., description="True if Groq API responded successfully")
    uptime_seconds: float = Field(..., description="Seconds since backend startup")


# ---------------------------------------------------------------------------
# Shared error response
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Structured error response returned on all error status codes."""

    error: str = Field(..., description="Human-readable error description")
    request_id: Optional[str] = Field(default=None, description="Request UUID if available")
    status_code: int = Field(..., description="HTTP status code")

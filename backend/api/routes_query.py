"""
routes_query.py — POST /api/query endpoint.

Handles both JSON (non-streaming) and SSE streaming query responses.
The full RAG pipeline is invoked from rag/pipeline.py.

Per Section 6.1 of ARCHITECTURE.md:
  - 200: success
  - 400: invalid request (query empty / too long — caught by Pydantic validation)
  - 500: internal error (FAISS error, unexpected exception)
  - 503: service unavailable (Groq unreachable after retries)

SSE format (stream=true):
  event: token  data: {"token": "..."}
  event: done   data: {"request_id": "...", "sources": [...], "debug": {...}}
  event: error  data: {"error": "...", "request_id": "...", "status_code": N}

The X-Request-Id header is set on all responses.
"""
import json
import logging
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from backend.api.schemas import QueryRequest, QueryResponse
from backend.rag.pipeline import run_query_pipeline, run_sse_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"description": "Invalid request — query too short or too long"},
        500: {"description": "Internal server error"},
        503: {"description": "Groq API unavailable"},
    },
)
async def query_endpoint(request_data: QueryRequest, request: Request):
    """
    Main chat endpoint.

    Accepts a natural language query, runs the full RAG pipeline
    (deterministic router → FAISS retrieval → prompt assembly → Groq LLM →
    output evaluator → structured log), and returns the answer with debug
    metadata.

    If stream=true, the response is delivered as an SSE stream.
    Each token is sent as 'event: token'. On completion, 'event: done'
    carries the full source and debug metadata.
    """
    request_id = str(uuid.uuid4())

    # Explicit validation: empty or whitespace-only queries return 400 (not 422)
    if not request_data.query.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Query cannot be empty or whitespace only.", "status_code": 400},
            headers={"X-Request-Id": request_id},
        )

    if request_data.stream:
        # --- SSE streaming path ---
        async def event_generator():
            try:
                async for event in run_sse_pipeline(
                    query=request_data.query,
                    request_id=request_id,
                ):
                    yield event
            except Exception as exc:
                logger.exception(
                    "Unhandled streaming error for request_id=%s", request_id
                )
                yield {
                    "event": "error",
                    "data": json.dumps(
                        {
                            "error": "An internal error occurred during streaming.",
                            "request_id": request_id,
                            "status_code": 500,
                        }
                    ),
                }

        return EventSourceResponse(event_generator())

    # --- Non-streaming path ---
    try:
        result = await run_query_pipeline(
            query=request_data.query,
            request_id=request_id,
        )
        response = JSONResponse(content=result, status_code=200)
        response.headers["X-Request-Id"] = request_id
        return response

    except ConnectionError as exc:
        # Groq API unreachable after retries
        logger.error(
            "Groq API unreachable for request_id=%s: %s", request_id, exc
        )
        return JSONResponse(
            status_code=503,
            content={
                "error": "The AI service is temporarily unavailable. Please try again in a few moments.",
                "request_id": request_id,
                "status_code": 503,
            },
            headers={"X-Request-Id": request_id},
        )

    except Exception as exc:
        logger.exception("Pipeline error for request_id=%s", request_id)
        return JSONResponse(
            status_code=500,
            content={
                "error": "An internal server error occurred.",
                "request_id": request_id,
                "status_code": 500,
            },
            headers={"X-Request-Id": request_id},
        )

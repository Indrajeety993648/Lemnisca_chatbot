# Clearpath RAG Chatbot — API Reference

**Base URL**: `http://localhost:8000`
**Version**: 1.0.0

All responses include `Content-Type: application/json` and `X-Request-Id: <uuid>`.

---

## POST /api/query

Submit a user query through the full RAG pipeline.

**Request Body**:
```json
{
  "query": "What are your pricing plans?",
  "stream": false
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | User question (1–2000 chars) |
| `stream` | boolean | No | If true, return SSE stream (default false) |

**Response (non-streaming)**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Clearpath offers Pro and Enterprise plans...",
  "sources": [
    { "source_file": "pricing_guide.pdf", "page_number": 3, "score": 0.87 }
  ],
  "debug": {
    "classification": "simple",
    "model_used": "llama-3.1-8b-instant",
    "tokens_input": 145,
    "tokens_output": 52,
    "latency_ms": 820.4,
    "retrieval_count": 3,
    "evaluator_flags": []
  }
}
```

**SSE Response (stream: true)**:
```
event: token
data: {"token": "Clearpath "}

event: token
data: {"token": "offers..."}

event: done
data: {"request_id": "...", "sources": [...], "debug": {...}}
```

**curl example**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Clearpath?", "stream": false}'
```

**Status Codes**:
| Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Empty or too-long query |
| 422 | Validation error (missing required field) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Groq API unavailable after retries |

---

## POST /api/ingest

Upload a PDF file for RAG indexing.

**Request**: `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | file | PDF file, max 50 MB |

**Response**:
```json
{
  "status": "success",
  "filename": "pricing_guide.pdf",
  "chunks_created": 42,
  "total_pages": 8,
  "processing_time_ms": 2350.6
}
```

**curl example**:
```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@/path/to/document.pdf"
```

**Status Codes**:
| Code | Meaning |
|---|---|
| 200 | Success |
| 400 | Invalid file (not PDF, too large, no extractable text) |
| 500 | Processing error |

---

## GET /api/debug

Retrieve debug information for the most recent queries.

**Query Parameters**:
| Param | Type | Default | Description |
|---|---|---|---|
| `n` | integer | 10 | Number of recent entries (1–100) |

**Response**:
```json
{
  "entries": [
    {
      "request_id": "uuid",
      "timestamp": "2026-02-21T13:45:00Z",
      "query": "What is Clearpath?",
      "classification": "simple",
      "model_used": "llama-3.1-8b-instant",
      "tokens_input": 120,
      "tokens_output": 35,
      "latency_ms": 640.2,
      "retrieval_count": 3,
      "evaluator_flags": [],
      "error": null
    }
  ],
  "total_count": 1
}
```

**curl example**:
```bash
curl "http://localhost:8000/api/debug?n=5"
```

---

## GET /api/logs

Retrieve paginated raw structured logs.

**Query Parameters**:
| Param | Type | Default | Description |
|---|---|---|---|
| `offset` | integer | 0 | Start position |
| `limit` | integer | 50 | Entries per page (1–500) |

**Response**:
```json
{
  "logs": [ /* full log entries with retrieval_scores */ ],
  "total": 150,
  "offset": 0,
  "limit": 50
}
```

**curl example**:
```bash
curl "http://localhost:8000/api/logs?offset=0&limit=25"
```

---

## GET /api/health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "faiss_index_loaded": true,
  "total_chunks": 1248,
  "groq_api_reachable": true,
  "uptime_seconds": 3621.4
}
```

`status` is `"degraded"` if FAISS index is empty or Groq is unreachable.

**curl example**:
```bash
curl http://localhost:8000/api/health
```

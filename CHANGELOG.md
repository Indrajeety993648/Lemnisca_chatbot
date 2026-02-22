# Changelog

All notable changes to Clearpath RAG Chatbot are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] — 2026-02-22

### Added

**Backend**
- FastAPI application with lifespan-based FAISS index loading and startup validation
- `POST /api/query` — full RAG pipeline, non-streaming and SSE streaming responses
- `POST /api/ingest` — PDF upload, text extraction, chunking, embedding, FAISS indexing
- `GET /api/debug` — recent query debug metadata
- `GET /api/logs` — paginated structured JSONL logs
- `GET /api/health` — health check with FAISS status and uptime
- `DeterministicRouter` — 6-node rule-based query classifier (simple/complex)
- `OutputEvaluator` — 3-check post-generation evaluation (no_context, refusal, hallucination)
- `GroqClient` — Groq API wrapper with 2-retry exponential backoff (1s, 3s)
- `VectorStore` — FAISS IndexFlatIP with L2-normalized embeddings
- `StructuredLogger` — JSONL append-only logging with 100 MB rotation and 30-day retention
- Text sanitization (input + chunk-level prompt injection prevention)
- Token counting with all-MiniLM-L6-v2 tokenizer and word-based fallback
- Rate limiting: 30 req/min per IP for `/api/query`, 5 req/min for `/api/ingest`
- CORS configuration via `CLEARPATH_ALLOWED_ORIGINS` environment variable

**Frontend**
- React 18 + TypeScript (strict mode) with Vite 5
- `App` — full-viewport layout with header, chat area, debug panel
- `ChatBox` — scrollable message list with auto-scroll and typing indicator
- `MessageBubble` — user/assistant rendering with Markdown, source citations, evaluator banners
- `InputBar` — textarea with Enter-to-send, Shift+Enter for newline, 2000-char limit
- `DebugPanel` — collapsible sidebar (desktop) / bottom sheet (mobile) with classification badge and flag chips
- `useChat` hook — SSE stream handling, token accumulation, debug state
- `apiClient` — typed fetch wrapper for all 5 API endpoints with 30s/120s timeouts
- React Error Boundary with retry button
- Accessibility: `role="log"`, `aria-live="polite"`, `aria-label` on all icon buttons
- Responsive design: mobile, tablet, desktop breakpoints

**Testing**
- 8 backend test modules using pytest + pytest-asyncio
- 5 frontend test modules using Vitest + React Testing Library

**Infrastructure**
- `docker-compose.yml` — backend + frontend local dev orchestration
- `backend/Dockerfile`, `frontend/Dockerfile`
- `scripts/run_dev.sh` — starts both servers with PID cleanup
- `scripts/validate_index.py` — FAISS index integrity checker
- `scripts/ingest_all_pdfs.py` — batch PDF ingestion

**Documentation**
- `ARCHITECTURE.md` — master blueprint (immutable)
- `docs/api_reference.md` — per-endpoint documentation
- `docs/router_rules.md` — decision tree and keyword lists
- `docs/rag_pipeline.md` — pipeline deep-dive
- `docs/evaluator_rules.md` — evaluator checks and flag definitions

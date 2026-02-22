# CLEARPATH RAG CHATBOT — MASTER ARCHITECTURE BLUEPRINT

**Version**: 1.0.0
**Date**: 2026-02-22
**Status**: Final
**Author**: Lead Developer

---

# 1. High-Level Architecture

## System Overview

Clearpath is a RAG-based customer support chatbot. Users submit natural-language queries through a React frontend. The backend receives the query, classifies it via a deterministic (rule-based) router, retrieves relevant context from a FAISS vector store built from 30 PDF documents, assembles a prompt, sends it to the appropriate Groq LLM model, evaluates the output, and returns the response with debug metadata.

There is NO deployment architecture. The system runs locally or in a single-server configuration.

## ASCII Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React + TS)                       │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ InputBar  │  │  ChatBox     │  │DebugPanel  │  │ MessageBubble│  │
│  └─────┬────┘  │  (messages)  │  │(collapsible)│  │  (per msg)   │  │
│        │       └──────────────┘  └────────────┘  └──────────────┘  │
│        │                                                             │
│  ┌─────▼────────────────────────────────────────────────────────┐   │
│  │                    useChat Hook + apiClient                   │   │
│  └─────┬────────────────────────────────────────────────────────┘   │
└────────┼────────────────────────────────────────────────────────────┘
         │ HTTP POST (JSON) / SSE stream
         ▼
┌────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Python)                      │
│                                                                     │
│  ┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  API Router  │───▶│ Deterministic    │───▶│  RAG Pipeline    │   │
│  │  /api/*      │    │ Query Router     │    │                  │   │
│  └─────────────┘    │ (rule-based)     │    │ ┌──────────────┐ │   │
│                      │                  │    │ │ Embedder     │ │   │
│                      │ Output:          │    │ │ (MiniLM-L6)  │ │   │
│                      │  simple → 8B     │    │ └──────┬───────┘ │   │
│                      │  complex → 70B   │    │        │         │   │
│                      └──────────────────┘    │ ┌──────▼───────┐ │   │
│                                              │ │ FAISS Store  │ │   │
│  ┌──────────────────┐                        │ │ (IndexFlatIP)│ │   │
│  │  Output Evaluator │◀───────────────────── │ └──────────────┘ │   │
│  │  (3 checks)       │                        │                  │   │
│  └────────┬─────────┘                        │ ┌──────────────┐ │   │
│           │                                   │ │ Prompt       │ │   │
│           │                                   │ │ Assembler    │ │   │
│           ▼                                   │ └──────────────┘ │   │
│  ┌──────────────────┐    ┌────────────────┐  └──────────────────┘   │
│  │  Response Builder │───▶│  Groq LLM API  │                        │
│  │  (+ debug meta)   │    │  (HTTP POST)   │                        │
│  └────────┬─────────┘    └────────────────┘                        │
│           │                                                         │
│  ┌────────▼─────────┐                                              │
│  │  Structured Logger│                                              │
│  │  (JSON logs)      │                                              │
│  └──────────────────┘                                              │
└────────────────────────────────────────────────────────────────────┘
```

## Data Flow (Query Path)

1. User types query in `InputBar` and clicks send.
2. `useChat` hook calls `apiClient.postQuery(query)` via HTTP POST to `/api/query`.
3. FastAPI receives the request, generates a `request_id` (UUID4), starts a timer.
4. **Deterministic Router** classifies the query as `simple` or `complex` using rule-based logic (Section 4).
5. **Embedder** encodes the query using `sentence-transformers/all-MiniLM-L6-v2` (384-dim vector).
6. **FAISS Store** performs inner-product similarity search, returns top-5 chunks.
7. **Prompt Assembler** builds the final prompt by inserting retrieved chunks into the prompt template.
8. **Groq API** is called with the assembled prompt using the model selected by the router.
9. **Output Evaluator** runs 3 checks on the generated response (Section 5).
10. **Response Builder** packages the answer, debug metadata, and evaluator flags.
11. **Structured Logger** writes a JSON log entry.
12. Response is returned to the frontend via SSE stream or JSON.
13. `useChat` hook updates state; `ChatBox` renders the new `MessageBubble`; `DebugPanel` shows metadata.

## Data Flow (Ingestion Path)

1. Admin uploads a PDF file via POST `/api/ingest`.
2. Backend extracts text from PDF using `PyMuPDF` (fitz).
3. Text is split into chunks (512 tokens, 64-token overlap).
4. Each chunk is embedded using `sentence-transformers/all-MiniLM-L6-v2`.
5. Embeddings are added to the FAISS index.
6. FAISS index is persisted to disk.
7. Chunk metadata (source filename, page number, chunk index) is stored in a JSON sidecar file.

---

# 2. Folder Structure

```
/home/indra/Lemnisca_chatbot/
├── ARCHITECTURE.md                  # THIS FILE — master blueprint
├── README.md                        # Project overview and setup instructions
├── CHANGELOG.md                     # Version history
├── .env.example                     # Template for environment variables
├── .env                             # Local environment variables (gitignored)
├── .gitignore
├── docker-compose.yml               # Local dev orchestration
├── Makefile                         # Common dev commands
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt             # Pinned Python dependencies
│   ├── pyproject.toml               # Project metadata
│   ├── main.py                      # FastAPI app entrypoint
│   ├── config.py                    # Environment and app configuration
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_query.py          # POST /api/query
│   │   ├── routes_ingest.py         # POST /api/ingest
│   │   ├── routes_debug.py          # GET /api/debug
│   │   ├── routes_logs.py           # GET /api/logs
│   │   ├── routes_health.py         # GET /api/health
│   │   └── schemas.py               # Pydantic request/response models
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestion.py             # PDF parsing + chunking
│   │   ├── embedder.py              # Embedding model wrapper
│   │   ├── vector_store.py          # FAISS index management
│   │   ├── retriever.py             # Query → top-k chunk retrieval
│   │   ├── prompt_assembler.py      # Prompt template + chunk insertion
│   │   └── pipeline.py              # Orchestrates full RAG query flow
│   │
│   ├── router/
│   │   ├── __init__.py
│   │   └── deterministic_router.py  # Rule-based query classifier
│   │
│   ├── evaluator/
│   │   ├── __init__.py
│   │   └── output_evaluator.py      # 3-check post-generation evaluator
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   └── groq_client.py           # Groq API wrapper with retry logic
│   │
│   ├── logging_/
│   │   ├── __init__.py
│   │   └── structured_logger.py     # JSON structured logging
│   │
│   ├── data/
│   │   ├── pdfs/                    # Uploaded PDF files
│   │   ├── faiss_index/             # Persisted FAISS index files
│   │   │   ├── index.faiss
│   │   │   └── index.pkl            # Chunk metadata sidecar
│   │   └── logs/                    # JSON log files
│   │       └── queries.jsonl        # Append-only query log
│   │
│   └── utils/
│       ├── __init__.py
│       ├── text_sanitizer.py        # Input/output sanitization
│       └── token_counter.py         # Token counting utility
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   │
│   ├── public/
│   │   └── favicon.ico
│   │
│   └── src/
│       ├── main.tsx                  # React entrypoint
│       ├── App.tsx                   # Root component
│       │
│       ├── components/
│       │   ├── ChatBox.tsx           # Message list container
│       │   ├── MessageBubble.tsx     # Individual message display
│       │   ├── InputBar.tsx          # Text input + send button
│       │   └── DebugPanel.tsx        # Collapsible debug metadata
│       │
│       ├── hooks/
│       │   └── useChat.ts           # Chat state + API integration
│       │
│       ├── services/
│       │   └── apiClient.ts         # HTTP/SSE client wrapper
│       │
│       ├── types/
│       │   └── index.ts             # TypeScript type definitions
│       │
│       └── styles/
│           └── globals.css           # Tailwind base + custom styles
│
├── tests/
│   ├── backend/
│   │   ├── conftest.py              # Shared fixtures
│   │   ├── test_router.py           # Router classification tests
│   │   ├── test_evaluator.py        # Output evaluator tests
│   │   ├── test_rag_pipeline.py     # RAG pipeline integration tests
│   │   ├── test_ingestion.py        # PDF ingestion tests
│   │   ├── test_api_query.py        # /api/query endpoint tests
│   │   ├── test_api_ingest.py       # /api/ingest endpoint tests
│   │   └── test_api_health.py       # Health check tests
│   │
│   └── frontend/
│       ├── setup.ts                 # Test setup
│       ├── ChatBox.test.tsx
│       ├── InputBar.test.tsx
│       ├── DebugPanel.test.tsx
│       ├── useChat.test.ts
│       └── apiClient.test.ts
│
├── scripts/
│   ├── ingest_all_pdfs.py           # Batch ingest all PDFs in data/pdfs/
│   ├── validate_index.py            # Verify FAISS index integrity
│   └── run_dev.sh                   # Start backend + frontend for dev
│
└── docs/
    ├── api_reference.md             # Detailed API documentation
    ├── router_rules.md              # Router decision tree documentation
    ├── rag_pipeline.md              # RAG pipeline deep-dive
    └── evaluator_rules.md           # Evaluator check documentation
```

---

# 3. RAG Pipeline Specification

## 3.1 PDF Ingestion

**Library**: PyMuPDF (fitz) version 1.24.x

**Process**:
1. Accept PDF file via `/api/ingest`.
2. Validate file: must be `.pdf`, max file size 50 MB, must have extractable text (not scanned image-only).
3. Extract text page-by-page using `fitz.open()`. Preserve page numbers.
4. Concatenate all pages into a single text string with page boundary markers: `\n[PAGE_BREAK:N]\n`.
5. Pass to chunking stage.

**Pseudocode — Ingestion**:
```python
FUNCTION ingest_pdf(file_path: str) -> List[ChunkRecord]:
    doc = fitz.open(file_path)
    full_text = ""
    FOR page_num IN range(len(doc)):
        page_text = doc[page_num].get_text("text")
        page_text = sanitize_text(page_text)
        full_text += page_text + "\n[PAGE_BREAK:" + str(page_num + 1) + "]\n"

    chunks = chunk_text(full_text, chunk_size=512, chunk_overlap=64)

    records = []
    FOR i, chunk IN enumerate(chunks):
        page_num = extract_page_number(chunk)  // from nearest PAGE_BREAK marker
        embedding = embedder.encode(chunk.clean_text)
        record = ChunkRecord(
            chunk_id = generate_uuid(),
            text = chunk.clean_text,
            source_file = basename(file_path),
            page_number = page_num,
            chunk_index = i,
            embedding = embedding
        )
        records.append(record)

    vector_store.add(records)
    vector_store.persist()
    RETURN records
```

## 3.2 Chunking Strategy

**Method**: Recursive character text splitting with token-based sizing.

**Parameters**:
- `chunk_size`: 512 tokens (measured by the tokenizer of `sentence-transformers/all-MiniLM-L6-v2`, which uses a WordPiece tokenizer; approximate via whitespace splitting at a ratio of 1 token per 0.75 words, yielding roughly 384 words per chunk)
- `chunk_overlap`: 64 tokens (12.5% overlap)
- `separator_hierarchy`: `["\n\n", "\n", ". ", " "]` — split on double newline first, then single newline, then sentence boundary, then whitespace.

**Justification**:
- 512 tokens balances granularity with context. Smaller chunks (256) fragment meaning; larger chunks (1024) dilute relevance scores.
- 64-token overlap prevents information loss at boundaries. 12.5% is the industry standard for support documentation.
- Recursive splitting preserves paragraph and sentence structure, which is critical for customer support content that often has step-by-step instructions.

**Pseudocode — Chunking**:
```python
FUNCTION chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[Chunk]:
    separators = ["\n\n", "\n", ". ", " "]
    // Remove PAGE_BREAK markers from text but record their positions
    clean_text, page_map = strip_and_map_page_breaks(text)
    chunks = recursive_split(clean_text, separators, chunk_size, chunk_overlap)
    FOR chunk IN chunks:
        chunk.page_number = lookup_page(chunk.start_offset, page_map)
    RETURN chunks

FUNCTION recursive_split(text, separators, size, overlap) -> List[Chunk]:
    IF token_count(text) <= size:
        RETURN [Chunk(text)]
    sep = find_best_separator(text, separators)
    segments = text.split(sep)
    chunks = []
    current = ""
    FOR segment IN segments:
        IF token_count(current + sep + segment) > size:
            chunks.append(Chunk(current))
            // Keep overlap from end of current
            overlap_text = get_last_n_tokens(current, overlap)
            current = overlap_text + sep + segment
        ELSE:
            current = current + sep + segment IF current ELSE segment
    IF current:
        chunks.append(Chunk(current))
    RETURN chunks
```

## 3.3 Embedding Model

- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensionality**: 384
- **Max sequence length**: 256 tokens (chunks exceeding this are truncated; this is acceptable because our 512-token chunks are measured differently than the model's tokenizer — effective content after WordPiece is within range for most chunks; for chunks that exceed, the first 256 model tokens are used, which captures the opening context)
- **Normalization**: L2-normalize all embeddings before insertion into FAISS. This enables inner-product search to behave as cosine similarity.
- **Batch size**: Embed in batches of 32 during ingestion for throughput.

## 3.4 FAISS Vector Store

- **Index type**: `IndexFlatIP` (flat inner product). With 30 PDFs, the total chunk count is estimated at 2,000-5,000 chunks. Flat index is optimal for this scale (exact search, no training required, search time < 10ms).
- **Persistence**: Save index to `backend/data/faiss_index/index.faiss` using `faiss.write_index()`. Save chunk metadata (list of ChunkRecord dicts) to `backend/data/faiss_index/index.pkl` using pickle.
- **Loading**: Load index into memory on backend startup. Reload after each ingestion.
- **ID mapping**: FAISS internal IDs are sequential integers. The metadata list is ordered identically, so `faiss_id == metadata_list_index`.

## 3.5 Retrieval

- **Top-k**: `k = 5`
- **Similarity threshold**: `0.35` (inner product after L2 normalization; this is equivalent to cosine similarity 0.35). Chunks below this threshold are discarded even if in top-k.
- **Deduplication**: If two chunks from the same source file and adjacent pages are retrieved, keep both (they likely contain continuation of relevant content). If two chunks have > 80% text overlap (measured by character-level Jaccard), drop the lower-scored one.

**Pseudocode — Retrieval**:
```python
FUNCTION retrieve(query: str, k: int = 5, threshold: float = 0.35) -> List[RetrievedChunk]:
    query_embedding = embedder.encode(query)
    query_embedding = l2_normalize(query_embedding)
    scores, indices = faiss_index.search(query_embedding.reshape(1, -1), k)

    results = []
    FOR i IN range(k):
        score = scores[0][i]
        idx = indices[0][i]
        IF idx == -1 OR score < threshold:
            CONTINUE
        chunk_meta = metadata_list[idx]
        results.append(RetrievedChunk(
            text = chunk_meta.text,
            source_file = chunk_meta.source_file,
            page_number = chunk_meta.page_number,
            score = float(score)
        ))

    results = deduplicate(results)
    RETURN results
```

## 3.6 Re-ranking

**Method**: Score-based heuristic (no cross-encoder). This keeps latency low and avoids additional model dependencies.

**Rules**:
1. Sort retrieved chunks by FAISS similarity score descending (already done by FAISS).
2. Apply a +0.05 boost to chunks whose `source_file` matches a keyword in the query (e.g., if query contains "pricing" and chunk is from "pricing_guide.pdf").
3. Re-sort after boost.
4. Return final ordered list.

**Justification**: Cross-encoders add 200-500ms latency. For 5 chunks, heuristic re-ranking is sufficient and keeps total retrieval under 50ms.

## 3.7 Text Sanitization

Before inserting retrieved chunks into the prompt:
1. Strip excessive whitespace (collapse multiple spaces/newlines to single).
2. Remove any remaining `[PAGE_BREAK:N]` markers.
3. Truncate any single chunk to 600 tokens max (safety limit).
4. Escape any string that looks like a prompt injection attempt: remove lines starting with "SYSTEM:", "INSTRUCTION:", "IGNORE PREVIOUS", or "YOU ARE".

## 3.8 Prompt Assembly

**Prompt Template**:
```
SYSTEM_PROMPT = """You are Clearpath Assistant, a helpful customer support agent for Clearpath.
You answer questions based ONLY on the provided context. If the context does not contain
enough information to answer the question, say "I don't have enough information in our
documentation to answer that question."

Do not make up information. Do not reference external sources. Be concise and helpful."""

USER_PROMPT_TEMPLATE = """Context:
---
{context_chunks}
---

Question: {user_query}

Answer:"""
```

**Context Assembly**:
```python
FUNCTION assemble_prompt(query: str, chunks: List[RetrievedChunk]) -> List[Message]:
    context_text = ""
    FOR i, chunk IN enumerate(chunks):
        context_text += f"[Source: {chunk.source_file}, Page {chunk.page_number}]\n"
        context_text += chunk.text + "\n\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
            context_chunks=context_text.strip(),
            user_query=query
        )}
    ]
    RETURN messages
```

---

# 4. Router Rules

## 4.1 Classification Logic

The deterministic router classifies every query as either `simple` or `complex`. Classification uses ONLY the following measurable features — no LLM calls.

### Feature Extraction

| Feature | How to Compute |
|---|---|
| `word_count` | Split query on whitespace, count elements |
| `char_count` | `len(query)` |
| `question_count` | Count occurrences of `?` in query |
| `has_complexity_keywords` | Check if query contains any word from COMPLEXITY_KEYWORDS list |
| `has_ambiguity_markers` | Check if query contains any phrase from AMBIGUITY_MARKERS list |
| `has_complaint_markers` | Check if query contains any phrase from COMPLAINT_MARKERS list |
| `has_comparison_pattern` | Check if query matches any COMPARISON_PATTERNS regex |
| `sentence_count` | Count occurrences of `.` `?` `!` that end a sentence (followed by space or end-of-string) |

### Keyword / Phrase Lists

**COMPLEXITY_KEYWORDS** (case-insensitive match, whole word boundary):
```python
["compare", "comparison", "difference", "differences", "versus", "vs",
 "integrate", "integration", "configure", "configuration", "migrate",
 "migration", "troubleshoot", "troubleshooting", "architecture",
 "workflow", "optimize", "optimization", "analyze", "analysis",
 "strategy", "strategies", "compliance", "security", "audit",
 "enterprise", "scalability", "performance", "benchmark", "custom",
 "advanced", "multiple", "several", "complex", "detailed", "comprehensive",
 "explain how", "walk me through", "step by step", "in depth"]
```

**AMBIGUITY_MARKERS** (case-insensitive substring match):
```python
["it depends", "what if", "hypothetically", "in general",
 "is it possible", "can you explain", "could you elaborate",
 "what are the pros and cons", "trade-off", "tradeoff",
 "best practice", "best practices", "recommend", "recommendation",
 "should i", "which one", "what would"]
```

**COMPLAINT_MARKERS** (case-insensitive substring match):
```python
["not working", "broken", "bug", "issue", "problem", "error",
 "frustrated", "disappointed", "unacceptable", "terrible",
 "worst", "angry", "complaint", "escalate", "refund",
 "cancel", "cancellation", "speak to manager", "supervisor"]
```

**COMPARISON_PATTERNS** (regex):
```python
[r"\bvs\.?\b", r"\bversus\b", r"\bcompared?\s+to\b",
 r"\bdifference\s+between\b", r"\bbetter\s+than\b",
 r"\bworse\s+than\b", r"\bor\b.*\bor\b"]
```

### Decision Tree

```
NODE 1: Is word_count <= 3 AND question_count <= 1 AND NOT has_complexity_keywords?
  ├── YES → CLASSIFY: simple (greeting or trivial query)
  └── NO → Go to NODE 2

NODE 2: Does the query have has_complaint_markers?
  ├── YES → CLASSIFY: complex (complaints need nuanced handling)
  └── NO → Go to NODE 3

NODE 3: Is question_count >= 3?
  ├── YES → CLASSIFY: complex (multi-part question)
  └── NO → Go to NODE 4

NODE 4: Does the query have has_comparison_pattern?
  ├── YES → CLASSIFY: complex (comparative analysis)
  └── NO → Go to NODE 5

NODE 5: Count complexity indicators:
         complexity_score = 0
         IF has_complexity_keywords: complexity_score += 2
         IF has_ambiguity_markers: complexity_score += 2
         IF word_count > 40: complexity_score += 1
         IF sentence_count >= 3: complexity_score += 1
         Is complexity_score >= 2?
  ├── YES → CLASSIFY: complex
  └── NO → Go to NODE 6

NODE 6: Is word_count > 25 AND has_ambiguity_markers?
  ├── YES → CLASSIFY: complex
  └── NO → CLASSIFY: simple
```

### Model Mapping

| Classification | Groq Model ID | Max Tokens (response) |
|---|---|---|
| `simple` | `llama-3.1-8b-instant` | 512 |
| `complex` | `llama-3.3-70b-versatile` | 1024 |

## 4.2 Example Classifications

**Example 1**: "What is Clearpath?"
- word_count=3, question_count=1, no complexity/ambiguity/complaint keywords
- NODE 1: word_count <= 3 AND question_count <= 1 AND NOT has_complexity → YES
- **Result: simple** → llama-3.1-8b-instant

**Example 2**: "How do I reset my password?"
- word_count=7, question_count=1, no complexity/ambiguity/complaint keywords
- NODE 1: word_count > 3 → NO
- NODE 2: no complaint markers → NO
- NODE 3: question_count < 3 → NO
- NODE 4: no comparison pattern → NO
- NODE 5: complexity_score = 0 → NO
- NODE 6: word_count <= 25 → NO
- **Result: simple** → llama-3.1-8b-instant

**Example 3**: "The billing system is not working and I want a refund immediately. This is unacceptable."
- word_count=15, question_count=0, has_complaint_markers=["not working", "refund", "unacceptable"]
- NODE 1: word_count > 3 → NO
- NODE 2: has_complaint_markers → YES
- **Result: complex** → llama-3.3-70b-versatile

**Example 4**: "What is the difference between the Pro plan and the Enterprise plan? Which one should I choose? Are there any hidden fees?"
- word_count=23, question_count=3, has_comparison_pattern=["difference between"], has_ambiguity_markers=["which one"], has_complexity_keywords=["difference", "enterprise"]
- NODE 1: word_count > 3 → NO
- NODE 2: no complaint markers → NO
- NODE 3: question_count >= 3 → YES
- **Result: complex** → llama-3.3-70b-versatile

**Example 5**: "Can you explain how the integration with Slack works step by step?"
- word_count=12, question_count=1, has_complexity_keywords=["explain how", "integration", "step by step"]
- NODE 1: word_count > 3 → NO
- NODE 2: no complaint markers → NO
- NODE 3: question_count < 3 → NO
- NODE 4: no comparison pattern → NO
- NODE 5: complexity_score = has_complexity_keywords(+2) = 2 → YES
- **Result: complex** → llama-3.3-70b-versatile

**Example 6**: "What are your business hours?"
- word_count=5, question_count=1, no complexity/ambiguity/complaint keywords
- NODE 1: word_count > 3 → NO
- NODE 2: no complaint markers → NO
- NODE 3: question_count < 3 → NO
- NODE 4: no comparison pattern → NO
- NODE 5: complexity_score = 0 → NO
- NODE 6: word_count <= 25 → NO
- **Result: simple** → llama-3.1-8b-instant

## 4.3 Logging Format

Every query processed by the router MUST produce a log entry in the following format:

```json
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
```

Fields `tokens_input`, `tokens_output`, and `latency_ms` are populated after the LLM call completes. The log is written as a single line to `backend/data/logs/queries.jsonl` (append mode).

---

# 5. Evaluator Rules

The Output Evaluator runs 3 sequential checks on every LLM response BEFORE returning it to the user. Each check produces zero or one flag. Flags are attached to the response metadata but do NOT block the response unless specified.

## Check 1: No-Context Check

- **Trigger condition**: `retrieval_count == 0` (zero chunks passed the similarity threshold during retrieval).
- **Flag name**: `no_context_warning`
- **Severity**: `warning`
- **Action**: ANNOTATE the response (do not block). Append to response metadata: `"flags": ["no_context_warning"]`. The frontend displays a subtle warning: "This response was generated without supporting documentation."
- **Logic**:
```python
IF retrieval_count == 0:
    flags.append("no_context_warning")
```

## Check 2: Refusal / Non-Answer Detection

- **Trigger condition**: The LLM response text contains any of the following phrases (case-insensitive substring match):
```python
REFUSAL_PHRASES = [
    "i cannot",
    "i can't",
    "i don't have information",
    "i don't have enough information",
    "i do not have",
    "i'm not sure",
    "i am not sure",
    "i'm unable to",
    "i am unable to",
    "outside my knowledge",
    "beyond my scope",
    "not able to help",
    "cannot assist with",
    "no information available",
    "unfortunately, i don't",
    "i apologize, but i",
    "i'm sorry, but i don't"
]
```
- **Minimum match threshold**: 1 (any single phrase match triggers the flag).
- **Flag name**: `refusal_detected`
- **Severity**: `info`
- **Action**: ANNOTATE the response. Do not block. This is expected behavior when the query is out of domain.
- **Logic**:
```python
response_lower = response_text.lower()
FOR phrase IN REFUSAL_PHRASES:
    IF phrase IN response_lower:
        flags.append("refusal_detected")
        BREAK
```

## Check 3: Domain-Specific Hallucination Check

- **Rule**: If the LLM response mentions a specific product plan name or pricing figure that does NOT appear in any of the retrieved chunks, flag as potential hallucination.
- **Detection heuristic**:
  1. Extract all currency amounts from the response using regex: `r'\$\d+(?:\.\d{2})?(?:\s*/\s*(?:month|year|mo|yr))?'`
  2. Extract all currency amounts from the concatenated retrieved chunk texts using the same regex.
  3. If ANY currency amount in the response is NOT present in the retrieved chunks, flag.
  4. Additionally, extract capitalized multi-word proper nouns from the response (regex: `r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'`) that look like product/plan names. If any such name appears in the response but NOT in the retrieved chunks AND NOT in a predefined allowlist, flag.
- **Allowlist** (known safe terms that may appear without chunk support):
```python
ALLOWED_TERMS = ["Clearpath", "Clearpath Assistant"]
```
- **Flag name**: `potential_hallucination`
- **Severity**: `warning`
- **Action**: ANNOTATE the response. Do not block. The frontend displays: "Some details in this response could not be verified against our documentation."
- **Logic**:
```python
FUNCTION check_hallucination(response_text, retrieved_chunks):
    chunk_text = " ".join([c.text for c in retrieved_chunks])

    response_prices = extract_prices(response_text)
    chunk_prices = extract_prices(chunk_text)

    FOR price IN response_prices:
        IF price NOT IN chunk_prices:
            RETURN "potential_hallucination"

    response_names = extract_proper_nouns(response_text)
    chunk_names = extract_proper_nouns(chunk_text)

    FOR name IN response_names:
        IF name NOT IN chunk_names AND name NOT IN ALLOWED_TERMS:
            RETURN "potential_hallucination"

    RETURN None
```

---

# 6. Backend API Specification

## Technology

- **Language**: Python 3.11+
- **Framework**: FastAPI 0.115+
- **ASGI server**: Uvicorn
- **Streaming**: Server-Sent Events (SSE) via `sse-starlette`

## Common Headers

All responses include:
- `Content-Type: application/json` (or `text/event-stream` for SSE)
- `X-Request-Id: <uuid4>` — echoed from request or generated server-side

## 6.1 POST /api/query

**Description**: Main chat endpoint. Accepts a user query, runs the full RAG pipeline, returns the response.

**Request Schema**:
```json
{
    "type": "object",
    "required": ["query"],
    "properties": {
        "query": {
            "type": "string",
            "minLength": 1,
            "maxLength": 2000,
            "description": "The user's natural language question"
        },
        "stream": {
            "type": "boolean",
            "default": false,
            "description": "If true, response is streamed via SSE"
        }
    }
}
```

**Response Schema (non-streaming)**:
```json
{
    "type": "object",
    "properties": {
        "request_id": { "type": "string", "format": "uuid" },
        "answer": { "type": "string" },
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_file": { "type": "string" },
                    "page_number": { "type": "integer" },
                    "score": { "type": "number" }
                }
            }
        },
        "debug": {
            "type": "object",
            "properties": {
                "classification": { "type": "string", "enum": ["simple", "complex"] },
                "model_used": { "type": "string" },
                "tokens_input": { "type": "integer" },
                "tokens_output": { "type": "integer" },
                "latency_ms": { "type": "number" },
                "retrieval_count": { "type": "integer" },
                "evaluator_flags": {
                    "type": "array",
                    "items": { "type": "string" }
                }
            }
        }
    }
}
```

**SSE Response Format** (when `stream: true`):
```
event: token
data: {"token": "partial text"}

event: token
data: {"token": "more text"}

event: done
data: {"request_id": "...", "sources": [...], "debug": {...}}
```

**Error Response Schema**:
```json
{
    "type": "object",
    "properties": {
        "error": { "type": "string" },
        "request_id": { "type": "string", "format": "uuid" },
        "status_code": { "type": "integer" }
    }
}
```

**Status Codes**:
- `200` — Success
- `400` — Invalid request (empty query, too long)
- `429` — Rate limit exceeded
- `500` — Internal server error (Groq API failure, FAISS error)
- `503` — Service unavailable (model timeout after retries)

## 6.2 POST /api/ingest

**Description**: Upload and process a PDF file for RAG indexing.

**Request**: `multipart/form-data` with a single file field.

```
Field: "file" — PDF file, max 50 MB
```

**Response Schema**:
```json
{
    "type": "object",
    "properties": {
        "status": { "type": "string", "enum": ["success", "error"] },
        "filename": { "type": "string" },
        "chunks_created": { "type": "integer" },
        "total_pages": { "type": "integer" },
        "processing_time_ms": { "type": "number" }
    }
}
```

**Error Response Schema**:
```json
{
    "type": "object",
    "properties": {
        "error": { "type": "string" },
        "detail": { "type": "string" }
    }
}
```

**Status Codes**:
- `200` — Success
- `400` — Invalid file (not PDF, too large, no extractable text)
- `500` — Processing error

## 6.3 GET /api/debug

**Description**: Retrieve debug information for the last N queries.

**Query Parameters**:
```
n: integer, default=10, min=1, max=100 — number of recent queries to return
```

**Response Schema**:
```json
{
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "request_id": { "type": "string" },
                    "timestamp": { "type": "string", "format": "date-time" },
                    "query": { "type": "string" },
                    "classification": { "type": "string" },
                    "model_used": { "type": "string" },
                    "tokens_input": { "type": "integer" },
                    "tokens_output": { "type": "integer" },
                    "latency_ms": { "type": "number" },
                    "retrieval_count": { "type": "integer" },
                    "evaluator_flags": { "type": "array", "items": { "type": "string" } },
                    "error": { "type": ["string", "null"] }
                }
            }
        },
        "total_count": { "type": "integer" }
    }
}
```

**Status Codes**:
- `200` — Success
- `400` — Invalid `n` parameter

## 6.4 GET /api/logs

**Description**: Retrieve raw structured logs. Supports pagination.

**Query Parameters**:
```
offset: integer, default=0, min=0 — starting position
limit: integer, default=50, min=1, max=500 — number of entries
```

**Response Schema**:
```json
{
    "type": "object",
    "properties": {
        "logs": {
            "type": "array",
            "items": {
                "type": "object",
                "description": "Full log entry as defined in Section 4.3"
            }
        },
        "total": { "type": "integer" },
        "offset": { "type": "integer" },
        "limit": { "type": "integer" }
    }
}
```

**Status Codes**:
- `200` — Success
- `400` — Invalid parameters

## 6.5 GET /api/health

**Description**: Health check endpoint.

**Response Schema**:
```json
{
    "type": "object",
    "properties": {
        "status": { "type": "string", "enum": ["healthy", "degraded"] },
        "faiss_index_loaded": { "type": "boolean" },
        "total_chunks": { "type": "integer" },
        "groq_api_reachable": { "type": "boolean" },
        "uptime_seconds": { "type": "number" }
    }
}
```

**Status Codes**:
- `200` — Healthy or degraded (still responds)

---

# 7. Frontend Architecture

## Technology Stack

- **Framework**: React 18+ with TypeScript (strict mode)
- **Build tool**: Vite 5+
- **Styling**: Tailwind CSS 3+
- **HTTP client**: Native `fetch` API (no axios — reduces bundle size)
- **Markdown rendering**: `react-markdown` with `remark-gfm`
- **Testing**: Vitest + React Testing Library

## Component Hierarchy

```
App
├── ChatBox
│   ├── MessageBubble (user)
│   │   └── timestamp
│   ├── MessageBubble (assistant)
│   │   ├── markdown content
│   │   ├── source citations
│   │   ├── evaluator flag warnings
│   │   └── timestamp
│   └── ... (list of messages, auto-scroll)
├── InputBar
│   ├── text input
│   ├── send button
│   └── loading indicator
└── DebugPanel (collapsible)
    ├── classification badge
    ├── model used
    ├── token counts
    ├── latency
    ├── retrieval count
    └── evaluator flags
```

## Component Specifications

### App.tsx
- Root component. Renders `ChatBox`, `InputBar`, `DebugPanel`.
- Uses `useChat` hook for all state and API interaction.
- Layout: full viewport height, flex column. ChatBox takes remaining space, InputBar fixed at bottom.

### ChatBox
**Props**:
```typescript
interface ChatBoxProps {
    messages: Message[];
    isLoading: boolean;
}
```
- Renders a scrollable list of `MessageBubble` components.
- Auto-scrolls to bottom when new messages arrive (using `useEffect` + `scrollIntoView`).
- Shows a typing indicator when `isLoading` is true.

### MessageBubble
**Props**:
```typescript
interface MessageBubbleProps {
    message: Message;
}

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: string;
    sources?: Source[];
    debug?: DebugInfo;
    flags?: string[];
}
```
- User messages: right-aligned, blue background (`bg-blue-600 text-white`).
- Assistant messages: left-aligned, gray background (`bg-gray-100 text-gray-900`).
- Assistant content rendered as Markdown.
- If `flags` includes `no_context_warning`, show yellow warning banner below message.
- If `flags` includes `potential_hallucination`, show orange warning banner below message.
- If `sources` is non-empty, show a "Sources" expandable section listing filenames and page numbers.

### InputBar
**Props**:
```typescript
interface InputBarProps {
    onSend: (query: string) => void;
    isLoading: boolean;
}
```
- Text input field with placeholder "Ask Clearpath a question...".
- Send button (arrow icon). Disabled when input is empty or `isLoading` is true.
- Enter key submits (Shift+Enter for newline).
- Input is cleared after send.
- Max input length: 2000 characters (enforced client-side with visual counter).

### DebugPanel
**Props**:
```typescript
interface DebugPanelProps {
    debugInfo: DebugInfo | null;
    isOpen: boolean;
    onToggle: () => void;
}

interface DebugInfo {
    classification: "simple" | "complex";
    model_used: string;
    tokens_input: number;
    tokens_output: number;
    latency_ms: number;
    retrieval_count: number;
    evaluator_flags: string[];
}
```
- Collapsible panel on the right side (desktop) or bottom sheet (mobile).
- Toggle button with bug icon. Default state: collapsed.
- Shows data for the most recent assistant message.
- Classification badge: green for "simple", orange for "complex".
- Flags displayed as colored chips: yellow for warnings, red for errors.

### useChat Hook
**State**:
```typescript
interface ChatState {
    messages: Message[];
    isLoading: boolean;
    error: string | null;
    debugInfo: DebugInfo | null;
    isDebugOpen: boolean;
}
```
**Methods**:
- `sendMessage(query: string)`: POSTs to `/api/query` with `stream: true`. Handles SSE events, builds up assistant message token by token. On `done` event, extracts debug info.
- `toggleDebug()`: Toggles `isDebugOpen`.
- `clearError()`: Clears error state.

### apiClient
- Base URL from environment variable `VITE_API_BASE_URL` (default: `http://localhost:8000`).
- `postQuery(query, stream)`: POST to `/api/query`. If stream, returns `EventSource`-compatible reader. If not stream, returns parsed JSON.
- `postIngest(file)`: POST multipart to `/api/ingest`.
- `getDebug(n)`: GET `/api/debug?n=N`.
- `getLogs(offset, limit)`: GET `/api/logs?offset=O&limit=L`.
- `getHealth()`: GET `/api/health`.
- All methods throw typed errors. Timeout: 30 seconds for query, 120 seconds for ingest.

## Responsive Design

| Breakpoint | Width | Layout |
|---|---|---|
| Mobile | < 640px | Single column, debug panel as bottom sheet, full-width messages |
| Tablet | 640px - 1024px | Single column, debug panel as side drawer (280px) |
| Desktop | > 1024px | Main chat area with debug panel as persistent sidebar (320px) |

---

# 8. Non-Functional Requirements

## Performance

| Metric | Target |
|---|---|
| Simple query end-to-end latency | < 2 seconds |
| Complex query end-to-end latency | < 5 seconds |
| FAISS similarity search time | < 50 ms |
| PDF ingestion (per page) | < 500 ms |
| Embedding generation (per chunk) | < 20 ms |
| Frontend time-to-interactive | < 1.5 seconds |

## Security

- **Input sanitization**: All user queries are stripped of HTML tags, null bytes, and control characters before processing.
- **Prompt injection prevention**: Retrieved chunks are sanitized per Section 3.7. User queries are wrapped in the template — never raw-concatenated with system prompts.
- **Rate limiting**:
  - Per-IP: 30 requests per minute for `/api/query`
  - Per-IP: 5 requests per minute for `/api/ingest`
  - Global: 500 requests per minute for `/api/query`
- **No PII logging**: Queries are logged but responses are NOT logged in full (only first 100 characters for debug). No user identification data is stored.
- **CORS**: Allowed origins configured via environment variable `ALLOWED_ORIGINS`. Default: `http://localhost:5173`.
- **File upload validation**: Only `.pdf` MIME type accepted. Max size 50 MB. Filename sanitized (alphanumeric, hyphens, underscores only).

## Scalability

- Backend is stateless (FAISS index loaded from disk into memory; no session state).
- Horizontal scaling: multiple backend instances can share the same FAISS index directory via a shared filesystem.
- FAISS index size limit: 50,000 chunks maximum. Beyond this, migrate to `IndexIVFFlat` with `nlist=100`.

## Fault Tolerance

- **Groq API timeout**: 30 seconds per request.
- **Retry policy**: Max 2 retries with exponential backoff (1s, 3s). Only retry on 5xx errors or timeouts. Do NOT retry on 4xx.
- **Fallback behavior**: If Groq API is unreachable after retries, return error response with `status_code: 503` and message "The AI service is temporarily unavailable. Please try again in a few moments."
- **FAISS index corruption**: On startup, validate index dimensionality matches 384. If mismatch, log error and refuse to start.

## Token Cost Optimization

- Router ensures the 8B model (`llama-3.1-8b-instant`) handles at least 70% of queries.
- Max response tokens are capped per classification: 512 for simple, 1024 for complex.
- System prompt is kept under 100 tokens.
- Retrieved context is limited to 5 chunks of max 600 tokens each (3,000 tokens max context).

## Logging

- **Format**: JSON Lines (`.jsonl`), one entry per line.
- **File**: `backend/data/logs/queries.jsonl`
- **Rotation**: Rotate when file exceeds 100 MB. Rotated files named `queries_YYYYMMDD_HHMMSS.jsonl`.
- **Retention**: Keep rotated files for 30 days, then delete.
- **Application logs**: Standard Python `logging` module, JSON formatter, written to stdout for container compatibility.

## Memory Constraints

- FAISS index for 5,000 chunks at 384 dimensions (float32): approximately 7.5 MB. Well within memory constraints.
- Chunk metadata (text + metadata per chunk, ~2KB avg): approximately 10 MB for 5,000 chunks.
- Embedding model (`all-MiniLM-L6-v2`): approximately 80 MB in memory.
- Total baseline memory: approximately 100 MB. Target: keep under 512 MB including Python runtime overhead.

---

# 9. Conclusion

The Clearpath RAG Chatbot is designed for high reliability, cost-efficiency, and user satisfaction. By leveraging a deterministic router and a multi-stage evaluation pipeline, it provides accurate, context-aware support for project management teams.

---
# End of Master Architecture Blueprint

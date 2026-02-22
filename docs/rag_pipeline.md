# Clearpath — RAG Pipeline Deep-Dive

## Overview

The RAG (Retrieval-Augmented Generation) pipeline processes every user query in 6 stages: ingestion (one-time), embedding, retrieval, re-ranking, prompt assembly, and generation.

---

## Stage 1: PDF Ingestion

**Library**: PyMuPDF (fitz) 1.24.x  
**Triggered by**: `POST /api/ingest`

1. Validate file: `.pdf` extension, ≤ 50 MB, has extractable text.
2. Extract text page-by-page using `fitz.open()`. Preserve page numbers via `[PAGE_BREAK:N]` markers.
3. Pass concatenated text to chunking.
4. Embed each chunk, add to FAISS, persist to disk.

---

## Stage 2: Chunking

**Method**: Recursive character splitting with token-based sizing.

| Parameter | Value | Rationale |
|---|---|---|
| `chunk_size` | 512 tokens | Balances context vs. specificity |
| `chunk_overlap` | 64 tokens (12.5%) | Prevents information loss at boundaries |
| Separators | `["\n\n", "\n", ". ", " "]` | Preserves paragraph/sentence structure |

Separator hierarchy tries `\n\n` (paragraph break) first, then `\n`, then sentence boundary, then whitespace. This preserves step-by-step instructions common in support documentation.

---

## Stage 3: Embedding

**Model**: `sentence-transformers/all-MiniLM-L6-v2`  
**Dimensionality**: 384  
**Max sequence length**: 256 model tokens  
**Normalization**: L2-normalize before indexing (enables cosine similarity via inner product)  
**Batch size**: 32 during ingestion

```python
embedding = model.encode(chunk_text, normalize_embeddings=True)
```

---

## Stage 4: FAISS Vector Store

**Index type**: `IndexFlatIP` (flat inner product — exact search)  
**Why flat?** With 2,000–5,000 chunks, flat search completes in < 10 ms. No training required.  
**Persistence**: `backend/data/faiss_index/index.faiss` + `index.pkl` (metadata sidecar)  
**ID mapping**: FAISS internal ID = metadata list index (sequential integers)

---

## Stage 5: Retrieval

| Parameter | Value |
|---|---|
| `k` (top-k) | 5 |
| Similarity threshold | 0.35 (cosine similarity after L2 normalization) |
| Deduplication | Drop chunks with > 80% Jaccard overlap (keep higher-scored) |

**Re-ranking heuristic**: Apply +0.05 score boost to chunks whose `source_file` contains a keyword present in the query (e.g., query mentions "pricing" → boost chunks from `pricing_guide.pdf`). Re-sort after boosting.

---

## Stage 6: Prompt Assembly

**System prompt** (< 100 tokens):
```
You are Clearpath Assistant, a helpful customer support agent for Clearpath.
You answer questions based ONLY on the provided context. If the context does not contain
enough information to answer the question, say "I don't have enough information in our
documentation to answer that question."
Do not make up information. Do not reference external sources. Be concise and helpful.
```

**User prompt template**:
```
Context:
---
[Source: pricing_guide.pdf, Page 3]
<chunk text>

[Source: overview.pdf, Page 1]
<chunk text>
---

Question: <user query>

Answer:
```

**Context Safety**:
- Each chunk sanitized: whitespace collapsed, `[PAGE_BREAK:N]` removed, truncated to 600 tokens max
- Prompt injection removed: lines starting with `SYSTEM:`, `INSTRUCTION:`, `IGNORE PREVIOUS`, `YOU ARE`

---

## Groq LLM Call

| Classification | Model | Max Tokens |
|---|---|---|
| simple | `llama-3.1-8b-instant` | 512 |
| complex | `llama-3.3-70b-versatile` | 1024 |

**Retry policy**: Max 2 retries with exponential backoff (1s, 3s). Retry on 5xx/timeout only.  
**Fallback**: If all retries fail → HTTP 503 response.

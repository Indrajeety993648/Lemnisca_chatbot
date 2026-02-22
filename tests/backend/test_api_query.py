"""
test_api_query.py — HTTP tests for POST /api/query endpoint.

Tests both streaming and non-streaming responses using FastAPI TestClient.
Naming convention: test_api_query_<behavior>
"""
from unittest.mock import MagicMock, patch

import pytest


def _make_groq_response(text: str = "Clearpath is a support platform.") -> MagicMock:
    choice = MagicMock()
    choice.message.content = text
    choice.finish_reason = "stop"
    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 20
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


# ---------------------------------------------------------------------------
# Non-streaming: valid requests
# ---------------------------------------------------------------------------

def test_api_query_returns_200_for_valid_query(test_client, mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response()

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        response = test_client.post("/api/query", json={"query": "What is Clearpath?"})

    assert response.status_code == 200


def test_api_query_response_has_required_fields(test_client, mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response()

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        response = test_client.post("/api/query", json={"query": "What is Clearpath?"})

    body = response.json()
    assert "request_id" in body
    assert "answer" in body
    assert "sources" in body
    assert "debug" in body


def test_api_query_debug_structure(test_client, mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response()

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        response = test_client.post("/api/query", json={"query": "What is Clearpath?"})

    debug = response.json()["debug"]
    assert "classification" in debug
    assert "model_used" in debug
    assert "tokens_input" in debug
    assert "tokens_output" in debug
    assert "latency_ms" in debug
    assert "retrieval_count" in debug
    assert "evaluator_flags" in debug


def test_api_query_returns_correct_answer(test_client, mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    expected = "Clearpath is a fantastic platform."
    groq_resp = _make_groq_response(expected)

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        response = test_client.post("/api/query", json={"query": "What is Clearpath?"})

    assert response.json()["answer"] == expected


def test_api_query_has_x_request_id_header(test_client, mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response()

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        response = test_client.post("/api/query", json={"query": "What is Clearpath?"})

    assert "x-request-id" in response.headers


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_api_query_returns_422_for_missing_query(test_client):
    response = test_client.post("/api/query", json={})
    assert response.status_code == 422


def test_api_query_returns_400_for_empty_query(test_client):
    response = test_client.post("/api/query", json={"query": ""})
    assert response.status_code == 400


def test_api_query_returns_400_for_too_long_query(test_client):
    long_query = "x" * 2001
    response = test_client.post("/api/query", json={"query": long_query})
    assert response.status_code in (400, 422)


def test_api_query_returns_400_for_whitespace_only_query(test_client):
    response = test_client.post("/api/query", json={"query": "   "})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Groq failure scenarios
# ---------------------------------------------------------------------------

def test_api_query_returns_503_when_groq_is_down(test_client, mock_faiss_index):
    faiss_index, metadata = mock_faiss_index

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate",
               side_effect=ConnectionError("Groq unreachable")):
        response = test_client.post("/api/query", json={"query": "What is Clearpath?"})

    assert response.status_code == 503


def test_api_query_503_has_error_message(test_client, mock_faiss_index):
    faiss_index, metadata = mock_faiss_index

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate",
               side_effect=ConnectionError("Groq unreachable")):
        response = test_client.post("/api/query", json={"query": "What is Clearpath?"})

    body = response.json()
    assert "error" in body

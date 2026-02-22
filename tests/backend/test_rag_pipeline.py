"""
test_rag_pipeline.py — Integration tests for the RAG pipeline.

Uses a real small in-memory FAISS index and mocked Groq to test
the full pipeline.py orchestration without network calls.
Naming convention: test_pipeline_<behavior>
"""
import re
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture
def pipeline_with_mocks(mock_faiss_index):
    """
    Set up the pipeline with a mocked vector store and Groq client.
    Returns a callable: run_pipeline(query, stream=False) -> result
    """
    faiss_index, metadata = mock_faiss_index

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata):
        import importlib
        import backend.rag.pipeline as pipeline_mod
        importlib.reload(pipeline_mod)
        yield pipeline_mod


def _make_groq_response(text: str) -> MagicMock:
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
# Non-streaming pipeline tests
# ---------------------------------------------------------------------------

def test_pipeline_returns_answer_for_valid_query(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index

    groq_resp = _make_groq_response("Clearpath is a platform.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        from backend.rag.pipeline import run_query
        result = run_query("What is Clearpath?", request_id="test-001", stream=False)

    assert result["answer"] == "Clearpath is a platform."
    assert "request_id" in result
    assert "sources" in result
    assert "debug" in result


def test_pipeline_debug_contains_classification(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response("Simple answer.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        from backend.rag.pipeline import run_query
        result = run_query("What is Clearpath?", request_id="test-002", stream=False)

    debug = result["debug"]
    assert debug["classification"] in ("simple", "complex")
    assert "model_used" in debug
    assert "latency_ms" in debug
    assert "retrieval_count" in debug
    assert "evaluator_flags" in debug


def test_pipeline_debug_tokens_are_integers(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response("An answer.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        from backend.rag.pipeline import run_query
        result = run_query("What is Clearpath?", request_id="test-003", stream=False)

    debug = result["debug"]
    assert isinstance(debug["tokens_input"], int)
    assert isinstance(debug["tokens_output"], int)
    assert debug["tokens_input"] >= 0
    assert debug["tokens_output"] >= 0


def test_pipeline_sources_list_is_returned(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response("Answer from sources.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        from backend.rag.pipeline import run_query
        result = run_query("What is Clearpath?", request_id="test-004", stream=False)

    assert isinstance(result["sources"], list)


def test_pipeline_simple_query_uses_8b_model(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response("Short answer.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp) as mock_gen:
        from backend.rag.pipeline import run_query
        # "What is Clearpath?" → simple → 8b model
        result = run_query("What is Clearpath?", request_id="test-005", stream=False)

    assert result["debug"]["model_used"] == "llama-3.1-8b-instant"


def test_pipeline_complex_query_uses_70b_model(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response("Complex detailed answer.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        from backend.rag.pipeline import run_query
        # "The billing system is not working" → complex (complaint marker)
        result = run_query(
            "The billing system is not working and I want a refund. This is unacceptable.",
            request_id="test-006",
            stream=False,
        )

    assert result["debug"]["model_used"] == "llama-3.3-70b-versatile"


def test_pipeline_latency_ms_is_positive(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response("Answer.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        from backend.rag.pipeline import run_query
        result = run_query("What is Clearpath?", request_id="test-007", stream=False)

    assert result["debug"]["latency_ms"] >= 0


def test_pipeline_evaluator_flags_is_list(mock_faiss_index):
    faiss_index, metadata = mock_faiss_index
    groq_resp = _make_groq_response("Here is the answer.")

    with patch("backend.rag.vector_store.vector_store._index", faiss_index), \
         patch("backend.rag.vector_store.vector_store._metadata", metadata), \
         patch("backend.llm.groq_client.groq_client.generate", return_value=groq_resp):
        from backend.rag.pipeline import run_query
        result = run_query("What is Clearpath?", request_id="test-008", stream=False)

    assert isinstance(result["debug"]["evaluator_flags"], list)

"""
test_api_health.py — Tests for GET /api/health endpoint.

Naming convention: test_api_health_<behavior>
"""
from unittest.mock import patch

import pytest


def test_api_health_returns_200(test_client):
    response = test_client.get("/api/health")
    assert response.status_code == 200


def test_api_health_response_has_required_fields(test_client):
    response = test_client.get("/api/health")
    body = response.json()
    assert "status" in body
    assert "faiss_index_loaded" in body
    assert "total_chunks" in body
    assert "groq_api_reachable" in body
    assert "uptime_seconds" in body


def test_api_health_status_is_valid_enum(test_client):
    response = test_client.get("/api/health")
    status = response.json()["status"]
    assert status in ("healthy", "degraded")


def test_api_health_faiss_index_loaded_is_boolean(test_client):
    response = test_client.get("/api/health")
    assert isinstance(response.json()["faiss_index_loaded"], bool)


def test_api_health_total_chunks_is_integer(test_client):
    response = test_client.get("/api/health")
    assert isinstance(response.json()["total_chunks"], int)
    assert response.json()["total_chunks"] >= 0


def test_api_health_uptime_is_non_negative(test_client):
    response = test_client.get("/api/health")
    assert response.json()["uptime_seconds"] >= 0


def test_api_health_groq_api_reachable_is_boolean(test_client):
    response = test_client.get("/api/health")
    assert isinstance(response.json()["groq_api_reachable"], bool)

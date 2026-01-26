"""
Contract tests for Graphiti API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime


class _FakeGraphitiService:
    async def ingest_message(self, content, source_description, group_id, valid_at):
        return {
            "episode_uuid": "ep-123",
            "nodes": [{"uuid": "n-1", "name": "TestNode"}],
            "edges": []
        }

    async def search(self, query, group_ids, limit, use_cross_encoder):
        return {
            "edges": [{"uuid": "e-1", "fact": "Something happened"}],
            "count": 1
        }

    async def health_check(self):
        return {"healthy": True, "neo4j_uri": "bolt://mock:7687", "group_id": "dionysus"}

    async def get_entity(self, name, group_id):
        if name == "TestNode":
            return {"uuid": "n-1", "name": "TestNode"}
        return None


@pytest.fixture
def app():
    import api.routers.graphiti as graphiti_router

    test_app = FastAPI()
    test_app.include_router(graphiti_router.router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_ingest_returns_schema(client):
    """POST /api/graphiti/ingest returns ingestion result."""
    import api.routers.graphiti as graphiti_router

    client.app.dependency_overrides[graphiti_router.get_graphiti_dependency] = lambda: _FakeGraphitiService()
    try:
        response = client.post(
            "/api/graphiti/ingest",
            json={"content": "Hello world", "source_description": "test"}
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["episode_uuid"] == "ep-123"
    assert len(data["nodes"]) == 1


def test_search_returns_schema(client):
    """POST /api/graphiti/search returns search results."""
    import api.routers.graphiti as graphiti_router

    client.app.dependency_overrides[graphiti_router.get_graphiti_dependency] = lambda: _FakeGraphitiService()
    try:
        response = client.post(
            "/api/graphiti/search",
            json={"query": "test query", "limit": 5}
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["edges"]) == 1


def test_health_returns_schema(client):
    """GET /api/graphiti/health returns health status."""
    import api.routers.graphiti as graphiti_router

    client.app.dependency_overrides[graphiti_router.get_graphiti_dependency] = lambda: _FakeGraphitiService()
    try:
        response = client.get("/api/graphiti/health")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True


def test_get_entity_returns_schema(client):
    """GET /api/graphiti/entity/{name} returns entity data."""
    import api.routers.graphiti as graphiti_router

    client.app.dependency_overrides[graphiti_router.get_graphiti_dependency] = lambda: _FakeGraphitiService()
    try:
        response = client.get("/api/graphiti/entity/TestNode")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TestNode"


def test_get_entity_not_found(client):
    """GET /api/graphiti/entity/{name} returns 404 if missing."""
    import api.routers.graphiti as graphiti_router

    client.app.dependency_overrides[graphiti_router.get_graphiti_dependency] = lambda: _FakeGraphitiService()
    try:
        response = client.get("/api/graphiti/entity/Unknown")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 404

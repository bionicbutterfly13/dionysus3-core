"""
Contract tests for Subconscious API endpoints (Feature 102).
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class _FakeSubconsciousService:
    def session_start(self, session_id: str, project_id=None, cwd=None) -> None:
        pass

    async def sync(self, session_id: str):
        from api.models.subconscious import SyncResponse
        return SyncResponse(guidance="", memory_blocks={"guidance": "", "user_preferences": "", "project_context": "", "pending_items": ""})

    async def ingest(self, payload):
        return {"ingested": True, "memories_created": 0}

    async def run_subconscious_decider(self, agent_id=None):
        return {"applied": {"narrative": 0, "relationships": 0, "contradictions": 0, "emotional": 0, "consolidation": 0}}


@pytest.fixture
def app():
    import api.routers.subconscious as subconscious_router
    test_app = FastAPI()
    test_app.include_router(subconscious_router.router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def _override_service(client, service=None):
    import api.routers.subconscious as subconscious_router
    client.app.dependency_overrides[subconscious_router._service] = lambda: service or _FakeSubconsciousService()
    return subconscious_router


def test_session_start_returns_ok(client):
    """POST /subconscious/session-start returns status ok."""
    _override_service(client)
    try:
        response = client.post(
            "/subconscious/session-start",
            json={"session_id": "s1", "project_id": "p1"},
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["session_id"] == "s1"


def test_sync_returns_guidance_and_blocks(client):
    """GET /subconscious/sync returns SyncResponse shape."""
    _override_service(client)
    try:
        response = client.get("/subconscious/sync", params={"session_id": "s1"})
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert "guidance" in data
    assert "memory_blocks" in data
    assert isinstance(data["memory_blocks"], dict)


def test_sync_post_returns_same_shape(client):
    """POST /subconscious/sync returns SyncResponse shape."""
    _override_service(client)
    try:
        response = client.post("/subconscious/sync", params={"session_id": "s1"})
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert "guidance" in data
    assert "memory_blocks" in data


def test_ingest_returns_ingested(client):
    """POST /subconscious/ingest returns ingested result."""
    _override_service(client)
    try:
        response = client.post(
            "/subconscious/ingest",
            json={"session_id": "s1", "transcript": "User said X. Assistant said Y."},
        )
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["ingested"] is True
    assert "memories_created" in data


def test_run_decider_returns_applied(client):
    """POST /subconscious/run-decider returns applied counts or skipped."""
    _override_service(client)
    try:
        response = client.post("/subconscious/run-decider")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert "applied" in data or "skipped" in data


def test_session_start_missing_session_id_returns_422(client):
    """POST /subconscious/session-start with missing session_id returns 422."""
    response = client.post("/subconscious/session-start", json={})
    assert response.status_code == 422


def test_ingest_missing_session_id_returns_422(client):
    """POST /subconscious/ingest with missing session_id returns 422."""
    response = client.post("/subconscious/ingest", json={"transcript": "x"})
    assert response.status_code == 422

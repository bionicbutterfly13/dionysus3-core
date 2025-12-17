"""
Contract Tests: Skills API (Webhook-backed)
Feature: 006-procedural-skills

Tests:
- POST /api/skills/upsert
- POST /api/skills/practice

These are contract tests: they do not require n8n/Neo4j. We stub the
RemoteSyncService used by the router.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class _StubSyncService:
    def __init__(self, *, upsert_result=None, practice_result=None):
        self._upsert_result = upsert_result or {"success": True, "records": []}
        self._practice_result = practice_result or {"success": True, "records": []}

    async def skill_upsert(self, payload: dict):
        return self._upsert_result

    async def skill_practice(self, payload: dict):
        return self._practice_result


@pytest.fixture
def app():
    import api.routers.skills as skills

    test_app = FastAPI()
    test_app.include_router(skills.router)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_skill_upsert_success(client, monkeypatch):
    import api.routers.skills as skills

    stub = _StubSyncService(
        upsert_result={"success": True, "skill_id": "skill-1", "created": True}
    )
    monkeypatch.setattr(skills, "get_sync_service", lambda: stub)

    resp = client.post(
        "/api/skills/upsert",
        json={
            "skill_id": "skill-1",
            "name": "Debugging",
            "description": "Find and fix bugs",
            "proficiency": 0.2,
            "decay_rate": 0.01,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["skill_id"] == "skill-1"


def test_skill_upsert_rejects_invalid_proficiency(client):
    resp = client.post(
        "/api/skills/upsert",
        json={"skill_id": "skill-1", "name": "Debugging", "proficiency": 1.5},
    )
    assert resp.status_code == 422


def test_skill_practice_success(client, monkeypatch):
    import api.routers.skills as skills

    stub = _StubSyncService(
        practice_result={"success": True, "skill_id": "skill-1", "practice_count": 2}
    )
    monkeypatch.setattr(skills, "get_sync_service", lambda: stub)

    resp = client.post(
        "/api/skills/practice",
        json={"skill_id": "skill-1", "success": True, "delta": 0.05},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["skill_id"] == "skill-1"


def test_skill_practice_requires_skill_id(client):
    resp = client.post("/api/skills/practice", json={"success": True})
    assert resp.status_code == 422

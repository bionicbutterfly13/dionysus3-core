"""
Contract Tests: Memory Traverse API
Feature: 006-procedural-skills

Tests the POST /api/memory/traverse endpoint contract.

NOTE: This is a contract test, so it does not require n8n/Neo4j. We stub the
RemoteSyncService used by the router.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class _StubSyncService:
    def __init__(self, result):
        self._result = result

    async def traverse(self, *, query_type: str, params: dict):
        return self._result


@pytest.fixture
def app(monkeypatch):
    from api.routers import memory

    test_app = FastAPI()
    test_app.include_router(memory.router)

    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_traverse_skill_graph_success(client, monkeypatch):
    from api.routers import memory

    stub = _StubSyncService(
        {
            "success": True,
            "records": [
                {
                    "skill": {"skill_id": "skill-1", "name": "Debugging"},
                    "outgoing": [],
                    "incoming": [],
                }
            ],
        }
    )
    monkeypatch.setattr(memory, "get_sync_service", lambda: stub)

    resp = client.post(
        "/api/memory/traverse",
        json={"query_type": "skill_graph", "params": {"skill_id": "skill-1"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["query_type"] == "skill_graph"
    assert body["data"]["success"] is True


def test_traverse_failure_returns_502(client, monkeypatch):
    from api.routers import memory

    stub = _StubSyncService({"success": False, "error": "n8n unavailable"})
    monkeypatch.setattr(memory, "get_sync_service", lambda: stub)

    resp = client.post(
        "/api/memory/traverse",
        json={"query_type": "skill_graph", "params": {"skill_id": "skill-1"}},
    )
    assert resp.status_code == 502


def test_traverse_invalid_query_type_rejected(client):
    resp = client.post(
        "/api/memory/traverse",
        json={"query_type": "not-a-real-query", "params": {}},
    )
    assert resp.status_code == 422

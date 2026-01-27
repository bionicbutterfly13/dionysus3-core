"""
Contract tests for Memory API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

class _FakeSyncService:
    async def query_by_session(self, session_id, query=None, include_session_metadata=False):
        return []
    
    async def search_memories(self, query, include_session_attribution=True, limit=20):
        return []

@pytest.fixture
def app():
    import api.routers.memory as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_search_memories_contract(client):
    """GET /api/memory/search returns search results."""
    import api.routers.memory as router
    
    with patch("api.routers.memory.get_sync_service", return_value=_FakeSyncService()):
        response = client.get("/api/memory/search?query=test")
        
    assert response.status_code == 200
    data = response.json()
    assert "memories" in data
    assert "total" in data

def test_get_session_memories_contract(client):
    """GET /api/memory/sessions/{id} returns session memories."""
    import api.routers.memory as router
    
    with patch("api.routers.memory.get_sync_service", return_value=_FakeSyncService()):
        response = client.get("/api/memory/sessions/sess-123")
        
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess-123"
    assert "memories" in data

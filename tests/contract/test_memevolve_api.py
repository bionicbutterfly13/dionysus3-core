"""
Contract tests for MemEvolve API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

class _FakeMemEvolveAdapter:
    async def health_check(self):
        return {"status": "ok", "service": "memevolve"}
    
    async def recall_memories(self, request):
        return {
            "memories": [],
            "query": request.query,
            "result_count": 0,
            "search_time_ms": 10.0
        }

@pytest.fixture
def app():
    import api.routers.memevolve as router
    from api.services.hmac_utils import verify_memevolve_signature

    test_app = FastAPI()
    # Bypass HMAC validation for contract tests
    test_app.include_router(router.router)
    test_app.dependency_overrides[verify_memevolve_signature] = lambda: True
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_health_contract(client):
    """POST /webhook/memevolve/v1/health returns status."""
    import api.routers.memevolve as router
    
    client.app.dependency_overrides[router.get_memevolve_adapter] = lambda: _FakeMemEvolveAdapter()
    try:
        response = client.post("/webhook/memevolve/v1/health")
    finally:
        client.app.dependency_overrides.clear()
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_recall_contract(client):
    """POST /webhook/memevolve/v1/recall returns memories."""
    import api.routers.memevolve as router
    
    client.app.dependency_overrides[router.get_memevolve_adapter] = lambda: _FakeMemEvolveAdapter()
    try:
        response = client.post(
            "/webhook/memevolve/v1/recall",
            json={"query": "test"}
        )
    finally:
        client.app.dependency_overrides.clear()
        
    assert response.status_code == 200
    data = response.json()
    assert "memories" in data
    assert data["query"] == "test"

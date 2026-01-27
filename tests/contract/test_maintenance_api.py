"""
Contract tests for Maintenance API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

class _FakeMaintenanceService:
    async def get_human_review_queue(self, limit=20):
        return []
    
    async def resolve_review_item(self, item_id):
        return True

@pytest.fixture
def app():
    import api.routers.maintenance as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_get_review_queue_contract(client):
    """GET /api/maintenance/review-queue returns list."""
    import api.routers.maintenance as router
    
    with patch("api.services.maintenance_service.get_maintenance_service", return_value=_FakeMaintenanceService()):
        response = client.get("/api/maintenance/review-queue")
        
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_integrity_check_contract(client):
    """GET /api/maintenance/integrity-check returns health info."""
    response = client.get("/api/maintenance/integrity-check")
    assert response.status_code == 200
    data = response.json()
    assert "graphiti_health" in data

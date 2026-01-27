"""
Contract tests for Mental Models API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime
from api.models.mental_model import ModelDomain, ModelStatus

class _FakeModelService:
    async def create_model(self, request):
        mock_model = MagicMock()
        mock_model.id = uuid4()
        return mock_model

    async def list_models(self, domain=None, status=None, limit=20, offset=0):
        mock_response = MagicMock()
        mock_response.models = []
        mock_response.total = 0
        return mock_response

@pytest.fixture
def app():
    import api.routers.models as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_create_model_contract(client):
    """POST /api/models/ returns model id."""
    import api.routers.models as router
    
    with patch("api.services.model_service.get_model_service", return_value=_FakeModelService()):
        response = client.post(
            "/api/models/",
            json={
                "name": "Test Model",
                "domain": "user",
                "basin_ids": [str(uuid4())],
                "description": "test"
            }
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "model_id" in data

def test_list_models_contract(client):
    """GET /api/models/ returns list."""
    import api.routers.models as router
    
    with patch("api.services.model_service.get_model_service", return_value=_FakeModelService()):
        response = client.get("/api/models/")
        
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "total" in data

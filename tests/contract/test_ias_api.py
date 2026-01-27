"""
Contract tests for IAS API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime

class _FakeSessionManager:
    async def get_or_create_journey(self, device_id):
        mock_journey = MagicMock()
        mock_journey.id = uuid.uuid4()
        mock_journey.is_new = True
        return mock_journey

    async def create_session(self, journey_id):
        mock_session = MagicMock()
        mock_session.id = uuid.uuid4()
        mock_session.created_at = datetime.utcnow()
        return mock_session

    async def get_session(self, session_id):
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.journey_id = uuid.uuid4()
        mock_session.messages = []
        mock_session.confidence_score = 0
        mock_session.diagnosis = None
        return mock_session

@pytest.fixture
def app():
    import api.routers.ias as ias_router

    test_app = FastAPI()
    test_app.include_router(ias_router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_create_session_contract(client):
    """POST /ias/session returns session data."""
    import api.routers.ias as ias_router
    
    client.app.dependency_overrides[ias_router.get_session_manager] = lambda: _FakeSessionManager()
    try:
        response = client.post("/ias/session", headers={"X-Device-Id": str(uuid.uuid4())})
    finally:
        client.app.dependency_overrides.clear()
        
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "created_at" in data

def test_get_framework_contract(client):
    """GET /ias/framework returns the framework."""
    response = client.get("/ias/framework")
    assert response.status_code == 200
    data = response.json()
    assert "framework" in data
    assert "steps" in data["framework"]

"""
Contract tests for Metacognition API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from api.models.metacognitive_particle import ParticleType

class _FakeMetacognitionService:
    async def classify(self, agent_id, blanket):
        return ParticleType.COGNITIVE, 0.9, 1, False
    
    async def get_agent_agency(self, agent_id):
        return 0.5, True, ParticleType.ACTIVE_METACOGNITIVE

@pytest.fixture
def app():
    import api.routers.metacognition as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_classify_contract(client):
    """POST /api/v1/metacognition/classify returns classification result."""
    with patch("api.services.particle_classifier.ParticleClassifier", return_value=_FakeMetacognitionService()):
        response = client.post(
            "/api/v1/metacognition/classify",
            json={
                "agent_id": "test-agent",
                "blanket": {
                    "sensory_states": [0.1, 0.2],
                    "active_states": [0.3, 0.4],
                    "internal_states": [0.5, 0.6]
                }
            }
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["particle_type"] == "COGNITIVE"
    assert data["confidence"] == 0.9

def test_get_agency_contract(client):
    """GET /api/v1/metacognition/agency/{id} returns agency strength."""
    with patch("api.services.agency_service.AgencyService", return_value=_FakeMetacognitionService()):
        response = client.get("/api/v1/metacognition/agency/test-agent")
        
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "test-agent"
    assert data["agency_strength"] == 0.5

"""
Contract tests for Beautiful Loop API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.models.beautiful_loop import UnifiedRealityModel, ResonanceSignal, ResonanceMode

class _FakeURMService:
    def __init__(self):
        self._model = UnifiedRealityModel(
            cycle_id="test-cycle",
            current_context={"task": "test"},
            resonance=ResonanceSignal(
                mode=ResonanceMode.STABLE,
                resonance_score=0.9,
                discovery_urgency=0.1
            )
        )
    
    def get_model(self):
        return self._model

@pytest.fixture
def app():
    import api.routers.beautiful_loop as beautiful_loop_router

    test_app = FastAPI()
    test_app.include_router(beautiful_loop_router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_get_reality_model_returns_schema(client):
    """GET /api/v1/beautiful-loop/reality-model returns populated model."""
    import api.routers.beautiful_loop as router
    
    client.app.dependency_overrides[router.get_unified_reality_model] = lambda: _FakeURMService()
    try:
        response = client.get("/api/v1/beautiful-loop/reality-model")
    finally:
        client.app.dependency_overrides.clear()
        
    assert response.status_code == 200
    data = response.json()
    assert data["cycle_id"] == "test-cycle"
    assert data["current_context"]["task"] == "test"
    assert data["resonance"]["mode"] == "stable"
"""
Contract tests for Domain Specialization API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

class _FakeDomainService:
    def __init__(self):
        self.neuro_db = MagicMock()
        self.neuro_db.concepts = {"test": {}}
        self.ai_db = MagicMock()
        self.ai_db.concepts = {"test": {}}
        self.cross_mapper = MagicMock()
        self.cross_mapper.mappings = {"test": {}}

    async def analyze_domain_content(self, content, context):
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.primary_domain = "neuroscience"
        mock_result.neuroscience_concepts = []
        mock_result.ai_concepts = []
        mock_result.cross_domain_mappings = []
        mock_result.terminology_density = 0.5
        mock_result.complexity_score = 0.5
        mock_result.processing_time = 0.1
        mock_result.specialized_prompts = {}
        return mock_result

@pytest.fixture
def app():
    import api.routers.domain_specialization as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_analyze_simple_contract(client):
    """POST /api/domain/analyze/simple returns summary."""
    import api.routers.domain_specialization as router
    
    with patch("api.routers.domain_specialization.get_domain_specialization_service", return_value=_FakeDomainService()):
        response = client.post(
            "/api/domain/analyze/simple",
            json={"content": "Neural networks are models of brains"}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["primary_domain"] == "neuroscience"

def test_health_contract(client):
    """GET /api/domain/health returns status."""
    import api.routers.domain_specialization as router
    
    with patch("api.routers.domain_specialization.get_domain_specialization_service", return_value=_FakeDomainService()):
        response = client.get("/api/domain/health")
        
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True

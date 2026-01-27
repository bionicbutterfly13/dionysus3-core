"""
Contract tests for Meta-ToT API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from api.models.meta_tot import MetaToTDecision, MetaToTResult

class _FakeMetaToTService:
    def decide(self, task, context):
        return MetaToTDecision(use_meta_tot=False, rationale="Testing", complexity_score=0.1, uncertainty_score=0.1)
    
    async def run(self, task, context, config_overrides=None, decision=None):
        return MetaToTResult(
            session_id="test",
            best_path=[],
            confidence=0.9,
            metrics={},
            decision=decision,
            trace_id="trace-1"
        ), None

@pytest.fixture
def app():
    import api.routers.meta_tot as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_run_meta_tot_contract(client):
    """POST /api/meta-tot/run returns response."""
    with patch("api.routers.meta_tot.get_meta_tot_decision_service", return_value=_FakeMetaToTService()):
        response = client.post(
            "/api/meta-tot/run",
            json={"task": "Solve mystery", "context": {}}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "result" in data

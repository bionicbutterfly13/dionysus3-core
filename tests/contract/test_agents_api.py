"""
Contract tests for Agents API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

class _FakeExecutionTraceService:
    async def list_traces(self, agent_name=None, limit=20, success_only=False):
        return [{
            "id": str(uuid4()),
            "agent_name": "perception",
            "run_id": "run-1",
            "started_at": "2026-01-26T12:00:00",
            "step_count": 5,
            "planning_count": 2,
            "success": True
        }]

    async def get_trace(self, trace_id):
        mock_trace = MagicMock()
        mock_trace.id = trace_id
        mock_trace.agent_name = "perception"
        mock_trace.started_at = "2026-01-26T12:00:00"
        mock_trace.completed_at = "2026-01-26T12:01:00"
        mock_trace.success = True
        mock_trace.steps = []
        mock_trace.activated_basins = []
        mock_trace.error_message = None
        return mock_trace

@pytest.fixture
def app():
    import api.routers.agents as router

    test_app = FastAPI()
    test_app.include_router(router.router)
    return test_app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_list_traces_contract(client):
    """GET /api/agents/traces returns traces list."""
    import api.routers.agents as router
    
    with patch("api.routers.agents.get_execution_trace_service", return_value=_FakeExecutionTraceService()):
        response = client.get("/api/agents/traces")
        
    assert response.status_code == 200
    data = response.json()
    assert "traces" in data
    assert len(data["traces"]) > 0

def test_get_token_usage_contract(client):
    """GET /api/agents/token-usage returns statistics."""
    import api.routers.agents as router

    with patch("api.routers.agents.get_all_token_summaries", return_value=[{"agent": "test"}]), \
         patch("api.routers.agents.get_aggregate_token_stats", return_value={"total": 100}):
        response = client.get("/api/agents/token-usage")

    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "aggregate" in data


# --- Error Response Tests ---


def test_get_trace_invalid_uuid_returns_400(client):
    """GET /api/agents/traces/{trace_id} with invalid UUID returns 400."""
    response = client.get("/api/agents/traces/not-a-valid-uuid")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_get_trace_not_found_returns_404(client):
    """GET /api/agents/traces/{trace_id} returns 404 for non-existent trace."""
    class _FakeServiceNotFound:
        async def get_trace(self, trace_id):
            return None

    with patch("api.routers.agents.get_execution_trace_service", return_value=_FakeServiceNotFound()):
        response = client.get(f"/api/agents/traces/{uuid4()}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_trace_mermaid_not_found_returns_404(client):
    """GET /api/agents/traces/{trace_id}/mermaid returns 404 for non-existent trace."""
    class _FakeServiceNotFound:
        async def get_trace(self, trace_id):
            return None

    with patch("api.routers.agents.get_execution_trace_service", return_value=_FakeServiceNotFound()):
        response = client.get(f"/api/agents/traces/{uuid4()}/mermaid")

    assert response.status_code == 404


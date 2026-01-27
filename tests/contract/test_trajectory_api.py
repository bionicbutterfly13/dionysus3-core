"""
Contract tests for Trajectory API endpoints.

Tests API contracts for execution trace viewing and export.
Focus on error responses per T041-020.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestTrajectoryErrorResponses:
    """Error response tests for trajectory endpoints."""

    @pytest.fixture(autouse=True)
    def mock_not_found(self):
        """Mock service to return None (trace not found)."""
        mock_service = MagicMock()
        mock_service.get_trace_from_execution = AsyncMock(return_value=None)

        with patch('api.routers.trajectory.get_trajectory_viz_service', return_value=mock_service):
            yield

    def test_get_trace_returns_404_for_missing(self):
        """GET /api/trajectory/{trace_id} returns 404 for non-existent trace."""
        response = client.get("/api/trajectory/nonexistent-trace")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_get_trace_json_returns_404_for_missing(self):
        """GET /api/trajectory/{trace_id}/json returns 404 for non-existent trace."""
        response = client.get("/api/trajectory/nonexistent-trace/json")
        assert response.status_code == 404

    def test_get_trace_mermaid_returns_404_for_missing(self):
        """GET /api/trajectory/{trace_id}/mermaid returns 404 for non-existent trace."""
        response = client.get("/api/trajectory/nonexistent-trace/mermaid")
        assert response.status_code == 404

    def test_get_trace_html_returns_404_for_missing(self):
        """GET /api/trajectory/{trace_id}/html returns 404 for non-existent trace."""
        response = client.get("/api/trajectory/nonexistent-trace/html")
        assert response.status_code == 404


class TestDemoTraceEndpoint:
    """Contract tests for GET /api/trajectory/demo/sample."""

    def test_demo_returns_200_with_html(self):
        """GET /api/trajectory/demo/sample returns 200 with HTML."""
        response = client.get("/api/trajectory/demo/sample")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

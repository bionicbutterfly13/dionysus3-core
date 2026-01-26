"""
Contract tests for Trajectory API endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_demo_trace_returns_html(client):
    """GET /api/trajectory/demo/sample returns HTML response."""
    response = await client.get("/api/trajectory/demo/sample")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

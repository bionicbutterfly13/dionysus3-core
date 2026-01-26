"""
Contract tests for Monitoring Pulse API endpoints.
"""

import pytest


class _FakeGraphiti:
    async def search(self, query, limit=5):
        return {"edges": [{"name": "System", "fact": "Operational"}]}


@pytest.mark.asyncio
async def test_daily_pulse_returns_200_with_schema(client, monkeypatch):
    """GET /monitoring/pulse/daily returns PulseResponse schema."""
    from api.main import app
    from api.routers import monitoring_pulse as pulse_router
    from api.services.graphiti_service import get_graphiti_dependency

    monkeypatch.setattr(
        pulse_router,
        "get_git_commits",
        lambda limit=5: [
            pulse_router.CommitInfo(
                hash="abc123",
                author="Test",
                date="2026-01-25T00:00:00Z",
                message="Test commit",
                files_changed=["api/routers/monitoring_pulse.py"],
            )
        ],
    )

    app.dependency_overrides[get_graphiti_dependency] = lambda: _FakeGraphiti()
    try:
        response = await client.get("/monitoring/pulse/daily")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "git_commits" in data
    assert "recent_entities" in data
    assert "system_status" in data
    assert isinstance(data["git_commits"], list)
    assert isinstance(data["recent_entities"], list)

"""
Contract tests for Session API endpoints.

Covers /api/session/reconstruct and /api/session/context.
"""

from types import SimpleNamespace

import pytest


class _FakeReconstructionResult(SimpleNamespace):
    def to_compact_context(self) -> str:
        return "## Compact Context\n- Example"


class _FakeReconstructionService:
    async def reconstruct(self, context, prefetched_tasks=None):
        return _FakeReconstructionResult(
            project_summary="Test summary",
            recent_sessions=[],
            active_tasks=[],
            key_entities=[],
            recent_decisions=[],
            episodic_memories=[],
            coherence_score=0.8,
            fragment_count=3,
            reconstruction_time_ms=12.5,
            gap_fills=[],
            warnings=[],
        )


@pytest.mark.asyncio
async def test_reconstruct_returns_200_with_schema(client, monkeypatch):
    """POST /api/session/reconstruct returns ReconstructResponse schema."""
    from api.routers import session as session_router

    monkeypatch.setattr(
        session_router,
        "get_reconstruction_service",
        lambda: _FakeReconstructionService(),
    )

    payload = {"project_path": "/Volumes/Asylum/dev/dionysus3-core"}
    response = await client.post("/api/session/reconstruct", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "project_summary" in data
    assert "recent_sessions" in data
    assert "active_tasks" in data
    assert "key_entities" in data
    assert "recent_decisions" in data
    assert "episodic_memories" in data
    assert "coherence_score" in data
    assert "fragment_count" in data
    assert "reconstruction_time_ms" in data
    assert "gap_fills" in data
    assert "warnings" in data
    assert "compact_context" in data


@pytest.mark.asyncio
async def test_quick_context_returns_200_with_schema(client, monkeypatch):
    """GET /api/session/context returns QuickContextResponse schema."""
    from api.routers import session as session_router

    monkeypatch.setattr(
        session_router,
        "get_reconstruction_service",
        lambda: _FakeReconstructionService(),
    )

    response = await client.get(
        "/api/session/context",
        params={"project_path": "/Volumes/Asylum/dev/dionysus3-core", "cues": "heartbeat,precision"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "project_name" in data
    assert "active_task_count" in data
    assert "recent_session_count" in data
    assert "compact_context" in data
    assert "reconstruction_time_ms" in data

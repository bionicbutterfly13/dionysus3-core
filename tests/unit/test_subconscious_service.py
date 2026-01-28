"""
Unit tests for SubconsciousService (Feature 102).

Tests Hexis-style observation flow and Letta-style session API with mocked dependencies.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.models.subconscious import (
    ConsolidationObservation,
    ContradictionObservation,
    EmotionalObservation,
    IngestRequest,
    NarrativeObservation,
    RelationshipObservation,
    SubconsciousObservations,
    SyncResponse,
)
from api.services.subconscious_service import SubconsciousService


@pytest.fixture
def mock_graphiti():
    graphiti = AsyncMock()
    graphiti.search = AsyncMock(return_value={"edges": [{"fact": "test fact", "uuid": "u1"}]})
    return graphiti


@pytest.fixture
def mock_memevolve():
    memevolve = AsyncMock()
    memevolve.recall_memories = AsyncMock(
        return_value={"memories": [{"content": "memory 1", "memory_id": "m1"}]}
    )
    memevolve.ingest_message = AsyncMock(return_value={"memories_created": 1})
    return memevolve


@pytest.fixture
def mock_router():
    router = AsyncMock()
    router.route_memory = AsyncMock(return_value={"memory_type": "STRATEGIC", "basin_name": "strategic-basin"})
    return router


@pytest.fixture
def service(mock_graphiti, mock_memevolve, mock_router):
    return SubconsciousService(graphiti=mock_graphiti, memevolve=mock_memevolve, router=mock_router)


@pytest.mark.asyncio
async def test_get_subconscious_context(service, mock_graphiti, mock_memevolve):
    """get_subconscious_context builds context from Graphiti + MemEvolve."""
    ctx = await service.get_subconscious_context(agent_id="test-agent")
    assert "recent_memories" in ctx
    assert "goals" in ctx
    assert "emotional_state" in ctx
    mock_graphiti.search.assert_called_once()
    mock_memevolve.recall_memories.assert_called_once()


@pytest.mark.asyncio
async def test_get_subconscious_context_handles_errors(service, mock_graphiti):
    """get_subconscious_context handles partial failures gracefully."""
    mock_graphiti.search.side_effect = Exception("search failed")
    ctx = await service.get_subconscious_context()
    assert isinstance(ctx, dict)
    assert "recent_memories" in ctx


@pytest.mark.asyncio
@patch("api.services.llm_service.chat_completion")
async def test_run_subconscious_decider_success(mock_chat, service, mock_router):
    """run_subconscious_decider calls LLM, parses observations, applies them."""
    mock_chat.return_value = json.dumps({
        "narrative_observations": [{"type": "turning_point", "summary": "Turning point", "confidence": 0.8}],
        "relationship_observations": [],
        "contradiction_observations": [],
        "emotional_observations": [],
        "consolidation_observations": [],
    })
    result = await service.run_subconscious_decider(agent_id="test-agent")
    assert "applied" in result
    assert result["applied"]["narrative"] == 1
    mock_chat.assert_called_once()
    assert mock_router.route_memory.called


@pytest.mark.asyncio
@patch("api.services.llm_service.chat_completion")
async def test_run_subconscious_decider_skips_on_error(mock_chat, service):
    """run_subconscious_decider returns skipped=True on LLM error."""
    mock_chat.side_effect = Exception("LLM failed")
    result = await service.run_subconscious_decider()
    assert result.get("skipped") is True
    assert "reason" in result


@pytest.mark.asyncio
async def test_apply_subconscious_observations_narrative(service, mock_router):
    """apply_subconscious_observations routes narrative observations to STRATEGIC basin."""
    obs = SubconsciousObservations(
        narrative_observations=[
            NarrativeObservation(type="turning_point", summary="Turning point", confidence=0.8)
        ]
    )
    counts = await service.apply_subconscious_observations(obs)
    assert counts["narrative"] == 1
    mock_router.route_memory.assert_called_once()
    call_kwargs = mock_router.route_memory.call_args[1]
    assert call_kwargs["memory_type"].value == "strategic"
    assert "subconscious:narrative" in call_kwargs["source_id"]


@pytest.mark.asyncio
async def test_apply_subconscious_observations_filters_low_confidence(service, mock_router):
    """apply_subconscious_observations filters observations below confidence threshold."""
    obs = SubconsciousObservations(
        narrative_observations=[
            NarrativeObservation(type="turning_point", summary="Low conf", confidence=0.5)
        ]
    )
    counts = await service.apply_subconscious_observations(obs)
    assert counts["narrative"] == 0
    mock_router.route_memory.assert_not_called()


@pytest.mark.asyncio
async def test_apply_subconscious_observations_all_types(service, mock_router):
    """apply_subconscious_observations handles all observation types."""
    obs = SubconsciousObservations(
        narrative_observations=[NarrativeObservation(summary="N", confidence=0.7)],
        relationship_observations=[RelationshipObservation(entity="E", confidence=0.7)],
        contradiction_observations=[ContradictionObservation(tension="T", confidence=0.7)],
        emotional_observations=[EmotionalObservation(pattern="P", confidence=0.7)],
        consolidation_observations=[ConsolidationObservation(rationale="R", confidence=0.7)],
    )
    counts = await service.apply_subconscious_observations(obs)
    assert counts["narrative"] == 1
    assert counts["relationships"] == 1
    assert counts["contradictions"] == 1
    assert counts["emotional"] == 1
    assert counts["consolidation"] == 1
    assert mock_router.route_memory.call_count == 5


def test_session_start_registers_session(service):
    """session_start stores session in registry."""
    service.session_start(session_id="s1", project_id="p1", cwd="/path")
    from api.services.subconscious_service import _session_registry
    assert "s1" in _session_registry
    assert _session_registry["s1"]["project_id"] == "p1"


@pytest.mark.asyncio
async def test_sync_returns_guidance_and_blocks(service, mock_graphiti, mock_memevolve):
    """sync builds SyncResponse from Graphiti + MemEvolve recall."""
    result = await service.sync(session_id="s1")
    assert isinstance(result, SyncResponse)
    assert "guidance" in result.model_dump()
    assert "memory_blocks" in result.model_dump()
    mock_memevolve.recall_memories.assert_called_once()
    mock_graphiti.search.assert_called_once()


@pytest.mark.asyncio
async def test_sync_handles_errors(service, mock_graphiti, mock_memevolve):
    """sync handles failures gracefully."""
    mock_graphiti.search.side_effect = Exception("search failed")
    mock_memevolve.recall_memories.side_effect = Exception("recall failed")
    result = await service.sync(session_id="s1")
    assert isinstance(result, SyncResponse)
    assert result.guidance == ""


@pytest.mark.asyncio
async def test_ingest_calls_memevolve(service, mock_memevolve):
    """ingest calls MemEvolveAdapter.ingest_message with correct params."""
    payload = IngestRequest(session_id="s1", transcript="User said X")
    result = await service.ingest(payload)
    assert result["ingested"] is True
    mock_memevolve.ingest_message.assert_called_once()
    call_kwargs = mock_memevolve.ingest_message.call_args[1]
    assert call_kwargs["content"] == "User said X"
    assert call_kwargs["source_id"] == "subconscious:s1"
    assert call_kwargs["session_id"] == "s1"


@pytest.mark.asyncio
async def test_ingest_rejects_empty_content(service, mock_memevolve):
    """ingest returns ingested=False for empty content."""
    payload = IngestRequest(session_id="s1", transcript="")
    result = await service.ingest(payload)
    assert result["ingested"] is False
    assert "reason" in result
    mock_memevolve.ingest_message.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_prefers_transcript_over_summary(service, mock_memevolve):
    """ingest uses transcript if both transcript and summary provided."""
    payload = IngestRequest(session_id="s1", transcript="transcript", summary="summary")
    await service.ingest(payload)
    call_kwargs = mock_memevolve.ingest_message.call_args[1]
    assert call_kwargs["content"] == "transcript"

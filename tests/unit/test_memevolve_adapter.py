import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.memevolve import (
    MemoryIngestRequest,
    MemoryRecallRequest,
    TrajectoryData,
    TrajectoryMetadata,
    TrajectoryStep,
)
from api.services.memevolve_adapter import MemEvolveAdapter


def _build_sync_service():
    service = AsyncMock()
    service.config = SimpleNamespace(
        recall_webhook_url="http://test/recall",
        memevolve_evolve_webhook_url="http://test/evolve",
        webhook_url="http://test/ingest",
    )
    service._send_to_webhook = AsyncMock(return_value={"success": True})
    return service


@pytest.mark.asyncio
async def test_health_check():
    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    health = await adapter.health_check()
    assert health["status"] == "ok"
    assert health["service"] == "dionysus-memevolve-adapter"
    assert "timestamp" in health


def test_resolve_valid_at_uses_metadata_timestamp():
    now = datetime.utcnow()
    result = MemEvolveAdapter._resolve_valid_at({})
    assert now <= result <= now + timedelta(seconds=2)

    stamp = datetime(2026, 1, 17, 0, 0, 0)
    assert MemEvolveAdapter._resolve_valid_at({"timestamp": stamp}) == stamp

    assert MemEvolveAdapter._resolve_valid_at({"timestamp": "2026-01-17T00:00:00"}) == stamp
    assert MemEvolveAdapter._resolve_valid_at({"timestamp": "invalid"}) is None
    numeric = MemEvolveAdapter._resolve_valid_at({"timestamp": 1700000000})
    assert isinstance(numeric, datetime)


@pytest.mark.asyncio
async def test_ingest_trajectory_records_relationships(monkeypatch):
    graphiti = AsyncMock()
    graphiti._format_trajectory_text = MagicMock(return_value="formatted")
    graphiti._summarize_trajectory = AsyncMock(return_value="summary")
    graphiti.extract_with_context = AsyncMock(
        return_value={
            "entities": [{"name": "A"}],
            "relationships": [
                {"source": "A", "target": "B", "type": "REL", "confidence": 0.8},
                {"source": "A", "target": "C", "type": "REL", "confidence": 0.4},
            ],
        }
    )
    graphiti.execute_cypher = AsyncMock(return_value=[])
    graphiti.ingest_extracted_relationships = AsyncMock(return_value={"ingested": 1})

    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    request = MemoryIngestRequest(
        trajectory=TrajectoryData(
            query="q",
            steps=[TrajectoryStep(observation="obs")],
            metadata=TrajectoryMetadata(
                session_id="sess-1",
                project_id="proj-1",
                timestamp=datetime(2026, 1, 17, 12, 0, 0),
            ),
        ),
    )

    with patch.object(adapter, "_get_graphiti_service", AsyncMock(return_value=graphiti)):
        result = await adapter.ingest_trajectory(request)

    assert result["entities_extracted"] == 1
    assert result["memories_created"] == 2
    assert graphiti.ingest_extracted_relationships.await_count == 1
    assert graphiti.execute_cypher.await_count >= 2
    assert any(
        "RelationshipProposal" in call.args[0]
        for call in graphiti.execute_cypher.call_args_list
    )


@pytest.mark.asyncio
async def test_ingest_trajectory_calls_webhook(monkeypatch):
    monkeypatch.setenv("MEMEVOLVE_WEBHOOK_INGEST_ENABLED", "true")
    graphiti = AsyncMock()
    graphiti._format_trajectory_text = MagicMock(return_value="formatted")
    graphiti._summarize_trajectory = AsyncMock(return_value="summary")
    graphiti.extract_with_context = AsyncMock(return_value={"entities": [], "relationships": []})
    graphiti.execute_cypher = AsyncMock(return_value=[])
    graphiti.ingest_extracted_relationships = AsyncMock(return_value={"ingested": 0})

    sync_service = _build_sync_service()
    adapter = MemEvolveAdapter(sync_service=sync_service)
    request = MemoryIngestRequest(
        trajectory=TrajectoryData(
            query="q",
            steps=[TrajectoryStep(observation="obs")],
            metadata=TrajectoryMetadata(),
        )
    )

    with patch.object(adapter, "_get_graphiti_service", AsyncMock(return_value=graphiti)):
        await adapter.ingest_trajectory(request)

    sync_service._send_to_webhook.assert_awaited_once()


@pytest.mark.asyncio
async def test_recall_memories_graphiti_default():
    graphiti = AsyncMock()
    graphiti.search = AsyncMock(
        return_value={
            "edges": [
                {"uuid": "1", "fact": "hello", "valid_at": "2026-01-01T00:00:00"}
            ]
        }
    )

    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    request = MemoryRecallRequest(query="hello", limit=5, project_id="proj-1", include_temporal_metadata=True)

    with patch.object(adapter, "_get_graphiti_service", AsyncMock(return_value=graphiti)):
        result = await adapter.recall_memories(request)

    assert result["result_count"] == 1
    assert result["memories"][0]["content"] == "hello"
    assert result["memories"][0]["valid_at"] == "2026-01-01T00:00:00"


@pytest.mark.asyncio
async def test_recall_memories_webhook_path(monkeypatch):
    monkeypatch.setenv("MEMEVOLVE_RECALL_BACKEND", "n8n")
    sync_service = _build_sync_service()
    sync_service._send_to_webhook = AsyncMock(
        return_value={
            "results": [
                {
                    "id": "mem-1",
                    "content": "alpha",
                    "type": "semantic",
                    "importance": 0.9,
                    "similarity": 0.88,
                }
            ]
        }
    )
    adapter = MemEvolveAdapter(sync_service=sync_service)
    request = MemoryRecallRequest(query="alpha", limit=3)

    result = await adapter.recall_memories(request)
    assert result["result_count"] == 1
    assert result["memories"][0]["similarity"] == 0.88


@pytest.mark.asyncio
async def test_trigger_evolution_graphiti_backend(monkeypatch):
    monkeypatch.setenv("MEMEVOLVE_EVOLVE_BACKEND", "graphiti")
    graphiti = AsyncMock()
    graphiti.execute_cypher = AsyncMock(
        side_effect=[
            [{"t": {"id": str(i)}} for i in range(25)],
            [{"s": {"id": "strategy-1"}}],
        ]
    )

    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    with patch.object(adapter, "_get_graphiti_service", AsyncMock(return_value=graphiti)):
        result = await adapter.trigger_evolution()

    assert result["success"] is True
    assert "Analyzed 25 recent trajectories" in result["basis"]


@pytest.mark.asyncio
async def test_wrapper_calls_graphiti():
    graphiti = AsyncMock()
    graphiti.execute_cypher = AsyncMock(return_value=[{"ok": True}])
    graphiti.extract_with_context = AsyncMock(return_value={"entities": []})
    graphiti.ingest_extracted_relationships = AsyncMock(return_value={"ingested": 1})

    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    with patch.object(adapter, "_get_graphiti_service", AsyncMock(return_value=graphiti)):
        await adapter.execute_cypher("RETURN 1", {"x": 1})
        await adapter.extract_with_context(content="hello")
        await adapter.ingest_relationships(relationships=[], source_id="src-1")

    graphiti.execute_cypher.assert_awaited()
    graphiti.extract_with_context.assert_awaited()
    graphiti.ingest_extracted_relationships.assert_awaited()


@pytest.mark.asyncio
async def test_get_graphiti_service_proxy():
    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    graphiti = AsyncMock()
    with patch("api.services.graphiti_service.get_graphiti_service", AsyncMock(return_value=graphiti)):
        result = await adapter._get_graphiti_service()
    assert result is graphiti


@pytest.mark.asyncio
async def test_ingest_trajectory_uses_provided_entities_edges():
    graphiti = AsyncMock()
    graphiti._format_trajectory_text = MagicMock(return_value="formatted")
    graphiti._summarize_trajectory = AsyncMock(return_value="summary")
    graphiti.extract_with_context = AsyncMock()
    graphiti.execute_cypher = AsyncMock(return_value=[])
    graphiti.ingest_extracted_relationships = AsyncMock(return_value={"ingested": 0})

    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    request = MemoryIngestRequest(
        trajectory=TrajectoryData(
            query="q",
            steps=[TrajectoryStep(observation="obs")],
            metadata=TrajectoryMetadata(),
        ),
        entities=[{"name": "Provided"}],
        edges=[{"source": "Provided", "target": "Target", "type": "REL", "confidence": 0.7}],
    )

    with patch.object(adapter, "_get_graphiti_service", AsyncMock(return_value=graphiti)):
        result = await adapter.ingest_trajectory(request)

    assert result["entities_extracted"] == 1
    assert graphiti.extract_with_context.await_count == 0


@pytest.mark.asyncio
async def test_ingest_trajectory_graphiti_error_fallback():
    graphiti = AsyncMock()
    graphiti._format_trajectory_text = MagicMock(return_value="formatted")
    graphiti._summarize_trajectory = AsyncMock(side_effect=RuntimeError("boom"))
    graphiti.execute_cypher = AsyncMock(return_value=[])
    graphiti.ingest_extracted_relationships = AsyncMock(return_value={"ingested": 0})

    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    request = MemoryIngestRequest(
        trajectory=TrajectoryData(
            query="q",
            steps=[TrajectoryStep(observation="obs")],
            metadata=TrajectoryMetadata(),
        )
    )

    with patch.object(adapter, "_get_graphiti_service", AsyncMock(return_value=graphiti)):
        result = await adapter.ingest_trajectory(request)

    assert result["entities_extracted"] == 0
    assert result["memories_created"] == 1


@pytest.mark.asyncio
async def test_ingest_message_delegates_to_ingest_trajectory():
    adapter = MemEvolveAdapter(sync_service=_build_sync_service())
    with patch.object(adapter, "ingest_trajectory", AsyncMock(return_value={"ok": True})) as ingest:
        await adapter.ingest_message("hello", "src-1", session_id="sess-1", project_id="proj-1")
    ingest.assert_awaited_once()


@pytest.mark.asyncio
async def test_recall_memories_webhook_filters(monkeypatch):
    monkeypatch.setenv("MEMEVOLVE_RECALL_BACKEND", "n8n")
    sync_service = _build_sync_service()
    sync_service._send_to_webhook = AsyncMock(return_value={"results": []})
    adapter = MemEvolveAdapter(sync_service=sync_service)
    request = MemoryRecallRequest(
        query="alpha",
        limit=3,
        memory_types=["semantic"],
        project_id="proj-1",
        session_id="sess-1",
        include_temporal_metadata=True,
        context={"extra": "x"},
    )

    await adapter.recall_memories(request)
    payload = sync_service._send_to_webhook.call_args[0][0]
    assert payload["filters"]["project_id"] == "proj-1"
    assert payload["filters"]["session_id"] == "sess-1"
    assert payload["filters"]["include_temporal"] is True
    assert payload["filters"]["extra"] == "x"


@pytest.mark.asyncio
async def test_recall_memories_fallback_on_error(monkeypatch):
    monkeypatch.setenv("MEMEVOLVE_RECALL_BACKEND", "n8n")
    monkeypatch.setenv("MEMEVOLVE_RECALL_FALLBACK", "true")
    sync_service = _build_sync_service()
    sync_service._send_to_webhook = AsyncMock(side_effect=RuntimeError("down"))
    adapter = MemEvolveAdapter(sync_service=sync_service)
    request = MemoryRecallRequest(query="alpha", limit=3)

    with patch.object(
        adapter,
        "_recall_from_graphiti",
        AsyncMock(return_value={"memories": [], "error": "down"}),
    ) as fallback:
        result = await adapter.recall_memories(request)

    assert result["error"] == "down"
    fallback.assert_awaited_once()


@pytest.mark.asyncio
async def test_trigger_evolution_webhook_backend(monkeypatch):
    monkeypatch.setenv("MEMEVOLVE_EVOLVE_BACKEND", "n8n")
    sync_service = _build_sync_service()
    sync_service._send_to_webhook = AsyncMock(return_value={"success": True})
    adapter = MemEvolveAdapter(sync_service=sync_service)
    result = await adapter.trigger_evolution()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_record_pending_relationships_noop():
    graphiti = AsyncMock()
    await MemEvolveAdapter._record_pending_relationships(
        graphiti=graphiti,
        relationships=[],
        source_id="memevolve:test",
        session_id=None,
        project_id=None,
    )
    graphiti.execute_cypher.assert_not_called()

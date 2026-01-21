import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from fastapi import HTTPException

from api.models.memevolve import MemoryIngestRequest, TrajectoryData
from api.routers import memevolve


def _build_request(**kwargs) -> MemoryIngestRequest:
    trajectory = TrajectoryData(
        query="test",
        summary="test summary",
        steps=[],
    )
    return MemoryIngestRequest(trajectory=trajectory, **kwargs)


@pytest.mark.asyncio
async def test_health_check_post_returns_status():
    adapter = MagicMock()
    adapter.health_check = AsyncMock(
        return_value={"status": "ok", "service": "dionysus-memevolve-adapter"}
    )

    response = await memevolve.health_check(adapter=adapter)

    assert response.status == "ok"
    assert response.service == "dionysus-memevolve-adapter"


@pytest.mark.asyncio
async def test_health_check_get_returns_status():
    adapter = MagicMock()
    adapter.health_check = AsyncMock(
        return_value={"status": "ok", "service": "dionysus-memevolve-adapter"}
    )

    response = await memevolve.health_check_get(adapter=adapter)

    assert response.status == "ok"
    assert response.service == "dionysus-memevolve-adapter"


@pytest.mark.asyncio
async def test_recall_memories_maps_items():
    adapter = MagicMock()
    adapter.recall_memories = AsyncMock(
        return_value={
            "memories": [
                {
                    "id": "mem-1",
                    "content": "sample",
                    "type": "semantic",
                    "importance": 0.7,
                    "similarity": 0.9,
                }
            ],
            "query": "hello",
            "result_count": 1,
            "search_time_ms": 12.5,
        }
    )

    request = memevolve.MemoryRecallRequest(query="hello")
    response = await memevolve.recall_memories(request, adapter=adapter)

    assert response.query == "hello"
    assert response.result_count == 1
    assert response.memories[0].id == "mem-1"


@pytest.mark.asyncio
async def test_trigger_evolution_success():
    adapter = MagicMock()
    adapter.trigger_evolution = AsyncMock(
        return_value={
            "success": True,
            "records": [{"basis": "recent", "id": "strategy-1"}],
        }
    )

    response = await memevolve.trigger_evolution(adapter=adapter)

    assert response.success is True
    assert response.optimization_basis == "recent"
    assert response.new_strategy_id == "strategy-1"


@pytest.mark.asyncio
async def test_trigger_evolution_failure():
    adapter = MagicMock()
    adapter.trigger_evolution = AsyncMock(
        return_value={"success": False, "error": "boom"}
    )

    response = await memevolve.trigger_evolution(adapter=adapter)

    assert response.success is False
    assert "boom" in response.message


@pytest.mark.asyncio
async def test_ingest_rejects_pre_extracted_entities():
    request = _build_request(entities=[{"name": "Entity", "type": "Test"}])
    adapter = MagicMock()
    adapter.ingest_trajectory = AsyncMock(
        return_value={
            "ingest_id": "123e4567-e89b-12d3-a456-426614174000",
            "entities_extracted": 0,
            "memories_created": 0,
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await memevolve.ingest_trajectory(request, adapter=adapter)

    assert exc_info.value.status_code == 400
    assert "pre-extracted" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_ingest_rejects_pre_extracted_edges():
    request = _build_request(edges=[{"source": "A", "target": "B", "relation": "RELATES"}])
    adapter = MagicMock()
    adapter.ingest_trajectory = AsyncMock(
        return_value={
            "ingest_id": "123e4567-e89b-12d3-a456-426614174000",
            "entities_extracted": 0,
            "memories_created": 0,
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        await memevolve.ingest_trajectory(request, adapter=adapter)

    assert exc_info.value.status_code == 400
    assert "pre-extracted" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_ingest_allows_raw_payload():
    request = _build_request(entities=[], edges=[])

    mock_adapter = MagicMock()
    mock_adapter.ingest_trajectory = AsyncMock(
        return_value={
            "ingest_id": "123e4567-e89b-12d3-a456-426614174000",
            "entities_extracted": 0,
            "memories_created": 0,
        }
    )

    response = await memevolve.ingest_trajectory(request, adapter=mock_adapter)

    assert response.ingest_id == UUID("123e4567-e89b-12d3-a456-426614174000")

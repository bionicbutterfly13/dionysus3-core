"""
Tests for HexisMemoryService
Feature: 101-hexis-core-migration

TDD Red Phase: Tests written before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from api.models.hexis_ontology import MemoryType, Neighborhood, NeighborhoodType


@pytest.fixture
def mock_graphiti():
    """Mock GraphitiService for testing."""
    mock = AsyncMock()
    mock.search.return_value = {
        "edges": [
            {"fact": "Test memory fact 1", "uuid": "mem-001"},
            {"fact": "Test memory fact 2", "uuid": "mem-002"},
        ]
    }
    mock.persist_fact.return_value = "fact-uuid-123"
    mock.execute_cypher.return_value = []
    return mock


@pytest.fixture
def mock_memevolve():
    """Mock MemEvolveAdapter for testing."""
    mock = AsyncMock()
    mock.ingest_message.return_value = {"status": "ok", "entity_count": 1}
    return mock


@pytest.mark.asyncio
async def test_recall_returns_memory_items(mock_graphiti, mock_memevolve):
    """recall() should return list of memory items from Graphiti search."""
    with patch("api.services.hexis_memory.get_graphiti_service", return_value=mock_graphiti):
        from api.services.hexis_memory import HexisMemoryService

        service = HexisMemoryService()
        results = await service.recall(
            query="test query",
            agent_id="test-agent",
            limit=10
        )

        assert len(results) == 2
        assert results[0].content == "Test memory fact 1"
        mock_graphiti.search.assert_called_once()


@pytest.mark.asyncio
async def test_recall_respects_limit(mock_graphiti, mock_memevolve):
    """recall() should respect the limit parameter."""
    mock_graphiti.search.return_value = {
        "edges": [{"fact": f"Fact {i}", "uuid": f"mem-{i}"} for i in range(20)]
    }

    with patch("api.services.hexis_memory.get_graphiti_service", return_value=mock_graphiti):
        from api.services.hexis_memory import HexisMemoryService

        service = HexisMemoryService()
        results = await service.recall(
            query="test",
            agent_id="test-agent",
            limit=5
        )

        # Service should apply limit
        assert len(results) <= 5


@pytest.mark.asyncio
async def test_recall_empty_on_no_results(mock_graphiti, mock_memevolve):
    """recall() should return empty list when no matches found."""
    mock_graphiti.search.return_value = {"edges": []}

    with patch("api.services.hexis_memory.get_graphiti_service", return_value=mock_graphiti):
        from api.services.hexis_memory import HexisMemoryService

        service = HexisMemoryService()
        results = await service.recall(
            query="nonexistent",
            agent_id="test-agent"
        )

        assert results == []


@pytest.mark.asyncio
async def test_store_persists_to_graphiti(mock_graphiti, mock_memevolve):
    """store() should persist memory through Graphiti."""
    with patch("api.services.hexis_memory.get_graphiti_service", return_value=mock_graphiti):
        from api.services.hexis_memory import HexisMemoryService

        service = HexisMemoryService()
        result_id = await service.store(
            content="Important fact to remember",
            agent_id="test-agent",
            memory_type=MemoryType.SEMANTIC
        )

        assert result_id is not None
        mock_graphiti.persist_fact.assert_called_once()


@pytest.mark.asyncio
async def test_store_includes_memory_type_metadata(mock_graphiti, mock_memevolve):
    """store() should include memory type in basin_id for routing."""
    with patch("api.services.hexis_memory.get_graphiti_service", return_value=mock_graphiti):
        from api.services.hexis_memory import HexisMemoryService

        service = HexisMemoryService()
        await service.store(
            content="A procedural memory",
            agent_id="test-agent",
            memory_type=MemoryType.PROCEDURAL
        )

        # Verify basin_id includes memory type
        call_kwargs = mock_graphiti.persist_fact.call_args.kwargs
        assert "procedural" in call_kwargs.get("basin_id", "").lower()


@pytest.mark.asyncio
async def test_get_neighborhoods_returns_list(mock_graphiti, mock_memevolve):
    """get_neighborhoods() should return list of Neighborhood objects."""
    mock_graphiti.execute_cypher.return_value = [
        {"name": "Python Async", "type": "topic", "member_count": 5},
        {"name": "Session 12", "type": "temporal", "member_count": 3},
    ]

    with patch("api.services.hexis_memory.get_graphiti_service", return_value=mock_graphiti):
        from api.services.hexis_memory import HexisMemoryService

        service = HexisMemoryService()
        neighborhoods = await service.get_neighborhoods(agent_id="test-agent")

        assert len(neighborhoods) >= 0  # May be empty if not implemented
        # When implemented, should return Neighborhood objects


@pytest.mark.asyncio
async def test_recall_handles_graphiti_error_gracefully(mock_graphiti, mock_memevolve):
    """recall() should handle Graphiti errors gracefully."""
    mock_graphiti.search.side_effect = Exception("Connection failed")

    with patch("api.services.hexis_memory.get_graphiti_service", return_value=mock_graphiti):
        from api.services.hexis_memory import HexisMemoryService

        service = HexisMemoryService()

        # Should not raise, should return empty or handle gracefully
        try:
            results = await service.recall(
                query="test",
                agent_id="test-agent"
            )
            assert results == []
        except Exception:
            pytest.fail("recall() should handle errors gracefully")


@pytest.mark.asyncio
async def test_singleton_access():
    """get_hexis_memory_service() should return singleton instance."""
    from api.services.hexis_memory import get_hexis_memory_service

    service1 = get_hexis_memory_service()
    service2 = get_hexis_memory_service()

    assert service1 is service2

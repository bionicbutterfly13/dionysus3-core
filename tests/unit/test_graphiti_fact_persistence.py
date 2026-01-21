"""
Unit tests for Graphiti fact persistence.
Track: 041-resonance-gating
Task: T041-028 - Connect Nemori Facts to Graphiti

Tests verify:
1. persist_fact creates Fact node with correct properties
2. persist_fact links to Episode via DISTILLED_FROM relationship
3. Bi-temporal tracking (valid_at and created_at)
4. Basin ID cross-reference is stored
5. Graceful failure handling (returns None, logs warning)
6. Idempotent fact ID generation (no duplicates)

MEMORY CLUSTER SYNERGY:
- persist_fact() supplements route_memory() → extract_with_context() flow
- route_memory() extracts entities/relationships for graph traversal
- persist_fact() creates Fact nodes for temporal queries
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
import hashlib

from api.services.graphiti_service import GraphitiService, GraphitiConfig


class TestPersistFact:
    """Tests for GraphitiService.persist_fact method."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock GraphitiConfig."""
        return GraphitiConfig(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="test",
            group_id="dionysus",
        )

    @pytest.fixture
    def graphiti_service(self, mock_config):
        """Create GraphitiService with mocked config (no actual Neo4j connection)."""
        service = GraphitiService(mock_config)
        service._initialized = True  # Skip actual initialization
        return service

    @pytest.mark.asyncio
    async def test_persist_fact_creates_node(self, graphiti_service):
        """Verify persist_fact creates Fact node with correct properties."""
        fact_text = "The user prefers dark mode for late-night coding sessions"
        episode_id = "ep_abc123"
        valid_at = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_test123"}])

        result = await graphiti_service.persist_fact(
            fact_text=fact_text,
            source_episode_id=episode_id,
            valid_at=valid_at,
            basin_id="experiential-basin",
            confidence=0.85,
        )

        content_hash = hashlib.sha256(fact_text.encode()).hexdigest()[:16]
        expected_fact_id = f"fact_{content_hash}"
        assert result == expected_fact_id

        graphiti_service.execute_cypher.assert_called_once()
        call_args = graphiti_service.execute_cypher.call_args
        params = call_args[0][1]

        assert params["fact_id"] == expected_fact_id
        assert params["fact_text"] == fact_text
        assert params["source_episode_id"] == episode_id
        assert params["basin_id"] == "experiential-basin"
        assert params["confidence"] == 0.85
        assert params["valid_at"] == valid_at.isoformat()
        assert params["group_id"] == "dionysus"

    @pytest.mark.asyncio
    async def test_persist_fact_links_to_episode(self, graphiti_service):
        """Verify DISTILLED_FROM relationship is created in the Cypher query."""
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_xyz"}])

        await graphiti_service.persist_fact(
            fact_text="Test fact content",
            source_episode_id="ep_source123",
            valid_at=datetime.now(timezone.utc),
        )

        call_args = graphiti_service.execute_cypher.call_args
        cypher_query = call_args[0][0]

        assert "DISTILLED_FROM" in cypher_query
        assert "MERGE (f)-[:DISTILLED_FROM]->(ep)" in cypher_query

    @pytest.mark.asyncio
    async def test_persist_fact_bitemporal_tracking(self, graphiti_service):
        """Verify valid_at and created_at timestamps are set correctly."""
        valid_time = datetime(2025, 6, 1, 12, 30, 0, tzinfo=timezone.utc)
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_temporal"}])

        await graphiti_service.persist_fact(
            fact_text="Temporal test fact",
            source_episode_id="ep_time",
            valid_at=valid_time,
        )

        call_args = graphiti_service.execute_cypher.call_args
        cypher_query = call_args[0][0]
        params = call_args[0][1]

        assert params["valid_at"] == valid_time.isoformat()
        assert "f.valid_at = datetime($valid_at)" in cypher_query
        assert "f.created_at = datetime()" in cypher_query

    @pytest.mark.asyncio
    async def test_persist_fact_with_basin_id(self, graphiti_service):
        """Verify basin_id cross-reference is stored."""
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_basin"}])

        await graphiti_service.persist_fact(
            fact_text="Basin cross-reference test",
            source_episode_id="ep_basin",
            valid_at=datetime.now(timezone.utc),
            basin_id="semantic-basin",
        )

        call_args = graphiti_service.execute_cypher.call_args
        params = call_args[0][1]

        assert params["basin_id"] == "semantic-basin"

    @pytest.mark.asyncio
    async def test_persist_fact_without_basin_id(self, graphiti_service):
        """Verify persist_fact works without basin_id (optional parameter)."""
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_no_basin"}])

        result = await graphiti_service.persist_fact(
            fact_text="No basin fact",
            source_episode_id="ep_no_basin",
            valid_at=datetime.now(timezone.utc),
        )

        assert result is not None
        call_args = graphiti_service.execute_cypher.call_args
        params = call_args[0][1]

        assert params["basin_id"] is None

    @pytest.mark.asyncio
    async def test_persist_fact_failure_handling(self, graphiti_service):
        """Verify graceful degradation on failure (returns None, logs warning)."""
        graphiti_service.execute_cypher = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        with patch("api.services.graphiti_service.logger") as mock_logger:
            result = await graphiti_service.persist_fact(
                fact_text="Failing fact",
                source_episode_id="ep_fail",
                valid_at=datetime.now(timezone.utc),
            )

            assert result is None
            mock_logger.error.assert_called_once()
            error_msg = mock_logger.error.call_args[0][0]
            assert "Failed to persist fact to Graphiti" in error_msg

    @pytest.mark.asyncio
    async def test_persist_fact_idempotent(self, graphiti_service):
        """Verify same fact text produces same ID (no duplicates)."""
        fact_text = "Identical fact content for idempotency test"
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_idem"}])

        result1 = await graphiti_service.persist_fact(
            fact_text=fact_text,
            source_episode_id="ep_first",
            valid_at=datetime.now(timezone.utc),
        )

        result2 = await graphiti_service.persist_fact(
            fact_text=fact_text,
            source_episode_id="ep_second",
            valid_at=datetime.now(timezone.utc),
        )

        assert result1 == result2

        content_hash = hashlib.sha256(fact_text.encode()).hexdigest()[:16]
        expected_id = f"fact_{content_hash}"
        assert result1 == expected_id

    @pytest.mark.asyncio
    async def test_persist_fact_different_content_different_id(self, graphiti_service):
        """Verify different fact text produces different IDs."""
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_diff"}])

        result1 = await graphiti_service.persist_fact(
            fact_text="First unique fact",
            source_episode_id="ep_1",
            valid_at=datetime.now(timezone.utc),
        )

        result2 = await graphiti_service.persist_fact(
            fact_text="Second unique fact",
            source_episode_id="ep_2",
            valid_at=datetime.now(timezone.utc),
        )

        assert result1 != result2

    @pytest.mark.asyncio
    async def test_persist_fact_uses_default_group_id(self, graphiti_service):
        """Verify default group_id from config is used when not specified."""
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_group"}])

        await graphiti_service.persist_fact(
            fact_text="Group test fact",
            source_episode_id="ep_group",
            valid_at=datetime.now(timezone.utc),
        )

        call_args = graphiti_service.execute_cypher.call_args
        params = call_args[0][1]

        assert params["group_id"] == "dionysus"

    @pytest.mark.asyncio
    async def test_persist_fact_with_custom_group_id(self, graphiti_service):
        """Verify custom group_id overrides default."""
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_custom"}])

        await graphiti_service.persist_fact(
            fact_text="Custom group fact",
            source_episode_id="ep_custom",
            valid_at=datetime.now(timezone.utc),
            group_id="custom-project",
        )

        call_args = graphiti_service.execute_cypher.call_args
        params = call_args[0][1]

        assert params["group_id"] == "custom-project"

    @pytest.mark.asyncio
    async def test_persist_fact_confidence_update_on_match(self, graphiti_service):
        """Verify confidence is updated on match only if higher."""
        graphiti_service.execute_cypher = AsyncMock(return_value=[{"fact_id": "fact_conf"}])

        await graphiti_service.persist_fact(
            fact_text="Confidence test fact",
            source_episode_id="ep_conf",
            valid_at=datetime.now(timezone.utc),
            confidence=0.9,
        )

        call_args = graphiti_service.execute_cypher.call_args
        cypher_query = call_args[0][0]

        assert "ON MATCH SET" in cypher_query
        assert "CASE WHEN $confidence > f.confidence" in cypher_query

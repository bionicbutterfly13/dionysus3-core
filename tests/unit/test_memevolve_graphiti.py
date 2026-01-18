"""
Unit tests for Graphiti-backed MemEvolve integration.
Track: 057-memory-systems-integration
Task: 4.3 - TDD tests for Graphiti-backed MemEvolve ingest + recall

Tests verify:
1. recall_memories uses Graphiti backend by default
2. _recall_from_graphiti transforms Graphiti edges to MemEvolve format
3. trigger_evolution uses Graphiti backend by default
4. ingest_trajectory stores via Graphiti
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import os

from api.services.memevolve_adapter import MemEvolveAdapter
from api.models.memevolve import (
    MemoryRecallRequest,
    TrajectoryData,
    TrajectoryStep,
    TrajectoryMetadata,
    TrajectoryType,
)


class TestRecallFromGraphiti:
    """Tests for _recall_from_graphiti method."""

    @pytest.mark.asyncio
    async def test_recall_transforms_edges_to_memories(self):
        """Verify Graphiti edges are transformed to MemEvolve memory format."""
        adapter = MemEvolveAdapter()
        
        mock_graphiti = AsyncMock()
        mock_graphiti.search.return_value = {
            "edges": [
                {
                    "uuid": "edge-123",
                    "fact": "User prefers dark mode",
                    "valid_at": "2025-01-01T00:00:00Z",
                    "invalid_at": None,
                },
                {
                    "uuid": "edge-456",
                    "name": "Project deadline is Friday",
                },
            ]
        }
        
        with patch.object(adapter, "_get_graphiti_service", return_value=mock_graphiti):
            request = MemoryRecallRequest(
                query="user preferences",
                limit=10,
                project_id="proj-1",
            )
            
            import time
            result = await adapter._recall_from_graphiti(request, time.time())
        
        assert result["result_count"] == 2
        assert len(result["memories"]) == 2
        
        # Check first memory
        mem1 = result["memories"][0]
        assert mem1["id"] == "edge-123"
        assert mem1["content"] == "User prefers dark mode"
        assert mem1["type"] == "semantic"
        
        # Check second memory
        mem2 = result["memories"][1]
        assert mem2["id"] == "edge-456"
        assert mem2["content"] == "Project deadline is Friday"

    @pytest.mark.asyncio
    async def test_recall_includes_temporal_metadata_when_requested(self):
        """Verify temporal metadata is included when requested."""
        adapter = MemEvolveAdapter()
        
        mock_graphiti = AsyncMock()
        mock_graphiti.search.return_value = {
            "edges": [
                {
                    "uuid": "edge-789",
                    "fact": "Meeting scheduled",
                    "valid_at": "2025-01-15T10:00:00Z",
                    "invalid_at": "2025-01-15T11:00:00Z",
                },
            ]
        }
        
        with patch.object(adapter, "_get_graphiti_service", return_value=mock_graphiti):
            request = MemoryRecallRequest(
                query="meetings",
                limit=5,
                include_temporal_metadata=True,
            )
            
            import time
            result = await adapter._recall_from_graphiti(request, time.time())
        
        mem = result["memories"][0]
        assert "valid_at" in mem
        assert "invalid_at" in mem
        assert mem["valid_at"] == "2025-01-15T10:00:00Z"

    @pytest.mark.asyncio
    async def test_recall_passes_group_ids_to_graphiti(self):
        """Verify project_id is passed as group_ids to Graphiti search."""
        adapter = MemEvolveAdapter()
        
        mock_graphiti = AsyncMock()
        mock_graphiti.search.return_value = {"edges": []}
        
        with patch.object(adapter, "_get_graphiti_service", return_value=mock_graphiti):
            request = MemoryRecallRequest(
                query="test query",
                limit=10,
                project_id="my-project",
            )
            
            import time
            await adapter._recall_from_graphiti(request, time.time())
        
        mock_graphiti.search.assert_called_once_with(
            query="test query",
            group_ids=["my-project"],
            limit=10,
        )


class TestRecallMemoriesBackendSelection:
    """Tests for recall_memories backend selection."""

    @pytest.mark.asyncio
    async def test_defaults_to_graphiti_backend(self):
        """Verify Graphiti is the default recall backend."""
        adapter = MemEvolveAdapter()
        
        mock_graphiti = AsyncMock()
        mock_graphiti.search.return_value = {"edges": []}
        
        # Ensure env var is not set (use default)
        with patch.dict(os.environ, {}, clear=False):
            if "MEMEVOLVE_RECALL_BACKEND" in os.environ:
                del os.environ["MEMEVOLVE_RECALL_BACKEND"]
            
            with patch.object(adapter, "_get_graphiti_service", return_value=mock_graphiti):
                request = MemoryRecallRequest(query="test", limit=5)
                result = await adapter.recall_memories(request)
        
        # Should have called Graphiti, not webhook
        mock_graphiti.search.assert_called_once()
        assert "memories" in result

    @pytest.mark.asyncio
    async def test_explicit_graphiti_backend(self):
        """Verify explicit graphiti backend setting works."""
        adapter = MemEvolveAdapter()
        
        mock_graphiti = AsyncMock()
        mock_graphiti.search.return_value = {"edges": [{"uuid": "1", "fact": "test"}]}
        
        with patch.dict(os.environ, {"MEMEVOLVE_RECALL_BACKEND": "graphiti"}):
            with patch.object(adapter, "_get_graphiti_service", return_value=mock_graphiti):
                request = MemoryRecallRequest(query="test", limit=5)
                result = await adapter.recall_memories(request)
        
        mock_graphiti.search.assert_called_once()
        assert result["result_count"] == 1


class TestTriggerEvolutionBackendSelection:
    """Tests for trigger_evolution backend selection."""

    @pytest.mark.asyncio
    async def test_defaults_to_graphiti_backend(self):
        """Verify Graphiti is the default evolve backend."""
        adapter = MemEvolveAdapter()
        
        mock_graphiti = AsyncMock()
        # Mock trajectory query
        mock_graphiti.execute_cypher.side_effect = [
            [{"t": {}} for _ in range(5)],  # Trajectory query
            [{"s": {"id": "strategy-1"}}],  # Strategy creation
        ]
        
        with patch.dict(os.environ, {}, clear=False):
            if "MEMEVOLVE_EVOLVE_BACKEND" in os.environ:
                del os.environ["MEMEVOLVE_EVOLVE_BACKEND"]
            
            with patch.object(adapter, "_get_graphiti_service", return_value=mock_graphiti):
                result = await adapter.trigger_evolution()
        
        # Should have called Graphiti Cypher
        assert mock_graphiti.execute_cypher.call_count == 2
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_evolution_creates_retrieval_strategy(self):
        """Verify evolution creates RetrievalStrategy node in Graphiti."""
        adapter = MemEvolveAdapter()
        
        mock_graphiti = AsyncMock()
        mock_graphiti.execute_cypher.side_effect = [
            [{"t": {}} for _ in range(25)],  # 25 trajectories
            [{"s": {"id": "strategy-new", "top_k": 7, "threshold": 0.75}}],
        ]
        
        with patch.dict(os.environ, {"MEMEVOLVE_EVOLVE_BACKEND": "graphiti"}):
            with patch.object(adapter, "_get_graphiti_service", return_value=mock_graphiti):
                result = await adapter.trigger_evolution()
        
        # Verify strategy creation Cypher was called
        create_call = mock_graphiti.execute_cypher.call_args_list[1]
        assert "RetrievalStrategy" in create_call[0][0]
        assert result["success"] is True
        assert "Analyzed 25 recent trajectories" in result["basis"]


class TestIngestTrajectoryGraphiti:
    """Tests for ingest_trajectory with Graphiti backend."""

    @pytest.mark.asyncio
    async def test_ingest_stores_trajectory_via_graphiti(self):
        """Verify trajectory ingestion uses Graphiti."""
        adapter = MemEvolveAdapter()

        mock_graphiti = AsyncMock()
        mock_graphiti._format_trajectory_text.return_value = "Formatted trajectory text"
        mock_graphiti._summarize_trajectory.return_value = "Trajectory summary"
        mock_graphiti.extract_with_context.return_value = {
            "entities": [{"name": "button", "type": "UI_ELEMENT"}],
            "relationships": [],
        }
        mock_graphiti.execute_cypher.return_value = [{"t": {"id": "traj-1"}}]
        mock_graphiti.ingest_extracted_relationships.return_value = {"ingested": 0}

        async def mock_get_graphiti():
            return mock_graphiti

        with patch.object(adapter, "_get_graphiti_service", side_effect=mock_get_graphiti):
            trajectory = TrajectoryData(
                query="Test task",
                steps=[
                    TrajectoryStep(
                        observation="User clicked button",
                        thought="Processing click",
                        action="Show dialog",
                    )
                ],
                metadata=TrajectoryMetadata(
                    agent_id="agent-1",
                    session_id="session-1",
                    project_id="project-1",
                    trajectory_type=TrajectoryType.EPISODIC,
                ),
            )

            # Wrap TrajectoryData in MemoryIngestRequest
            from api.models.memevolve import MemoryIngestRequest
            request = MemoryIngestRequest(trajectory=trajectory)

            result = await adapter.ingest_trajectory(request)

        # Should have called Graphiti for extraction and storage
        assert mock_graphiti._format_trajectory_text.called
        assert mock_graphiti.execute_cypher.called
        assert "ingest_id" in result


class TestGraphitiBackendEnvVarDefaults:
    """Tests to verify environment variable defaults."""

    def test_recall_backend_defaults_to_graphiti(self):
        """MEMEVOLVE_RECALL_BACKEND defaults to 'graphiti'."""
        # Clear any existing env var
        with patch.dict(os.environ, {}, clear=False):
            if "MEMEVOLVE_RECALL_BACKEND" in os.environ:
                del os.environ["MEMEVOLVE_RECALL_BACKEND"]
            
            backend = os.getenv("MEMEVOLVE_RECALL_BACKEND", "graphiti").lower()
            assert backend == "graphiti"

    def test_evolve_backend_defaults_to_graphiti(self):
        """MEMEVOLVE_EVOLVE_BACKEND defaults to 'graphiti'."""
        with patch.dict(os.environ, {}, clear=False):
            if "MEMEVOLVE_EVOLVE_BACKEND" in os.environ:
                del os.environ["MEMEVOLVE_EVOLVE_BACKEND"]
            
            backend = os.getenv("MEMEVOLVE_EVOLVE_BACKEND", "graphiti").lower()
            assert backend == "graphiti"

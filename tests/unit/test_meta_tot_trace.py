"""
Unit tests for Meta-ToT Trace Service.
Feature: 041-meta-tot-engine
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from api.services.meta_tot_trace_service import (
    MetaToTTraceService,
    get_meta_tot_trace_service,
)
from api.models.meta_tot import MetaToTTracePayload, MetaToTNodeTrace, MetaToTDecision


class TestMetaToTTraceService:
    @pytest.mark.asyncio
    async def test_store_trace_success(self):
        mock_graphiti = AsyncMock()
        mock_graphiti.execute_cypher = AsyncMock(return_value=[{"id": "trace-123"}])
        service = MetaToTTraceService(graphiti_service=mock_graphiti)

        payload = MetaToTTracePayload(
            trace_id="trace-123",
            session_id="session-456",
            best_path=["node1", "node2"],
            confidence=0.8,
        )
        result = await service.store_trace(payload)
        assert result == "trace-123"
        mock_graphiti.execute_cypher.assert_called_once()
        call_args = mock_graphiti.execute_cypher.call_args
        assert "MERGE (t:MetaToTTrace" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_store_trace_with_fallback_graphiti(self):
        """Test that service properly gets graphiti if not provided."""
        mock_graphiti = AsyncMock()
        mock_graphiti.execute_cypher = AsyncMock(return_value=[{"id": "trace-fallback"}])

        with patch('api.services.meta_tot_trace_service.get_graphiti_service', return_value=mock_graphiti):
            service = MetaToTTraceService()  # No graphiti_service provided
            payload = MetaToTTracePayload(
                trace_id="trace-fallback",
                session_id="session-789",
            )
            result = await service.store_trace(payload)
            assert result == "trace-fallback"

    @pytest.mark.asyncio
    async def test_get_trace_found(self):
        payload = MetaToTTracePayload(
            trace_id="neo4j-trace",
            session_id="session-neo4j",
            confidence=0.9,
        )
        mock_graphiti = AsyncMock()
        mock_graphiti.execute_cypher = AsyncMock(
            return_value=[{"payload": json.dumps(payload.model_dump())}]
        )
        service = MetaToTTraceService(graphiti_service=mock_graphiti)

        result = await service.get_trace("neo4j-trace")
        assert result is not None
        assert result.trace_id == "neo4j-trace"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_get_trace_not_found(self):
        mock_graphiti = AsyncMock()
        mock_graphiti.execute_cypher = AsyncMock(return_value=[])
        service = MetaToTTraceService(graphiti_service=mock_graphiti)

        result = await service.get_trace("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_trace_empty_payload(self):
        mock_graphiti = AsyncMock()
        mock_graphiti.execute_cypher = AsyncMock(return_value=[{"payload": None}])
        service = MetaToTTraceService(graphiti_service=mock_graphiti)

        result = await service.get_trace("empty-payload")
        assert result is None


class TestTracePayloadSerialization:
    def test_payload_with_nodes(self):
        node_trace = MetaToTNodeTrace(
            node_id="n1",
            depth=1,
            node_type="exploration",
            cpa_domain="explore",
            thought="test thought",
            score=0.8,
            visit_count=5,
            value_estimate=0.7,
            prediction_error=0.1,
            free_energy=0.2,
        )
        payload = MetaToTTracePayload(
            trace_id="t1",
            session_id="s1",
            nodes=[node_trace],
        )
        dumped = payload.model_dump()
        assert len(dumped["nodes"]) == 1
        assert dumped["nodes"][0]["node_id"] == "n1"

    def test_payload_with_decision(self):
        decision = MetaToTDecision(
            use_meta_tot=True,
            complexity_score=0.8,
            uncertainty_score=0.5,
            rationale="test decision",
        )
        payload = MetaToTTracePayload(
            trace_id="t2",
            session_id="s2",
            decision=decision,
        )
        dumped = payload.model_dump()
        assert dumped["decision"]["use_meta_tot"] is True


class TestGetMetaToTTraceService:
    def test_singleton(self):
        import api.services.meta_tot_trace_service as module
        module._meta_tot_trace_service = None
        svc1 = get_meta_tot_trace_service()
        svc2 = get_meta_tot_trace_service()
        assert svc1 is svc2
        module._meta_tot_trace_service = None

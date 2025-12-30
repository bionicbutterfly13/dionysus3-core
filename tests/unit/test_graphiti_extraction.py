"""
Unit Tests for GraphitiService Consolidated Extraction

Tests the extract_with_context method that consolidates extraction logic
previously duplicated between GraphitiService and KGLearningService.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

pytestmark = pytest.mark.asyncio


class TestExtractWithContext:
    """Tests for the consolidated extract_with_context method."""

    @pytest.fixture
    def mock_graphiti_service(self):
        """Create a mock GraphitiService."""
        from api.services.graphiti_service import GraphitiService
        
        with patch.object(GraphitiService, '__init__', lambda x: None):
            service = GraphitiService()
            service.config = MagicMock()
            service.config.group_id = "test_group"
            service._initialized = True
            service._parse_json_response = GraphitiService._parse_json_response
            return service

    async def test_extract_with_context_returns_entities_and_relationships(self, mock_graphiti_service):
        """Verify extraction returns properly structured output."""
        mock_response = '''
        {
            "entities": ["Concept A", "Concept B"],
            "relationships": [
                {"source": "A", "target": "B", "type": "EXTENDS", "confidence": 0.9, "evidence": "test"}
            ]
        }
        '''
        
        with patch('api.services.graphiti_service.chat_completion', return_value=mock_response):
            result = await mock_graphiti_service.extract_with_context(
                content="Test content about A and B"
            )
            
            assert "entities" in result
            assert "relationships" in result
            assert "approved_count" in result
            assert "pending_count" in result
            assert len(result["entities"]) == 2
            assert len(result["relationships"]) == 1

    async def test_extract_with_basin_context(self, mock_graphiti_service):
        """Verify basin context is included in prompt."""
        mock_response = '{"entities": [], "relationships": []}'
        
        with patch('api.services.graphiti_service.chat_completion', return_value=mock_response) as mock_chat:
            await mock_graphiti_service.extract_with_context(
                content="Test content",
                basin_context="Attractor Basin: Consciousness studies"
            )
            
            # Verify the prompt includes basin context
            call_args = mock_chat.call_args
            prompt = call_args.kwargs.get("messages", [{}])[0].get("content", "")
            assert "ATTRACTOR BASINS" in prompt
            assert "Consciousness studies" in prompt

    async def test_extract_with_strategy_context(self, mock_graphiti_service):
        """Verify strategy context is included in prompt."""
        mock_response = '{"entities": [], "relationships": []}'
        
        with patch('api.services.graphiti_service.chat_completion', return_value=mock_response) as mock_chat:
            await mock_graphiti_service.extract_with_context(
                content="Test content",
                strategy_context="Prioritized Relations: THEORETICALLY_EXTENDS, VALIDATES"
            )
            
            call_args = mock_chat.call_args
            prompt = call_args.kwargs.get("messages", [{}])[0].get("content", "")
            assert "THEORETICALLY_EXTENDS" in prompt

    async def test_confidence_threshold_gates_approval(self, mock_graphiti_service):
        """Verify relationships below threshold are marked pending."""
        mock_response = '''
        {
            "entities": [],
            "relationships": [
                {"source": "A", "target": "B", "type": "EXTENDS", "confidence": 0.9, "evidence": "high"},
                {"source": "C", "target": "D", "type": "RELATES", "confidence": 0.4, "evidence": "low"}
            ]
        }
        '''
        
        with patch('api.services.graphiti_service.chat_completion', return_value=mock_response):
            result = await mock_graphiti_service.extract_with_context(
                content="Test",
                confidence_threshold=0.6
            )
            
            assert result["approved_count"] == 1
            assert result["pending_count"] == 1
            
            approved = [r for r in result["relationships"] if r["status"] == "approved"]
            pending = [r for r in result["relationships"] if r["status"] == "pending_review"]
            
            assert len(approved) == 1
            assert approved[0]["source"] == "A"
            assert len(pending) == 1
            assert pending[0]["source"] == "C"

    async def test_custom_confidence_threshold(self, mock_graphiti_service):
        """Verify custom confidence threshold is respected."""
        mock_response = '''
        {
            "entities": [],
            "relationships": [
                {"source": "A", "target": "B", "type": "EXTENDS", "confidence": 0.7, "evidence": "test"}
            ]
        }
        '''
        
        with patch('api.services.graphiti_service.chat_completion', return_value=mock_response):
            # With threshold 0.6, should be approved
            result1 = await mock_graphiti_service.extract_with_context(
                content="Test",
                confidence_threshold=0.6
            )
            assert result1["approved_count"] == 1
            
            # With threshold 0.8, should be pending
            result2 = await mock_graphiti_service.extract_with_context(
                content="Test",
                confidence_threshold=0.8
            )
            assert result2["pending_count"] == 1

    async def test_extraction_error_returns_empty_result(self, mock_graphiti_service):
        """Verify extraction errors return empty result with error."""
        with patch('api.services.graphiti_service.chat_completion', side_effect=Exception("LLM error")):
            result = await mock_graphiti_service.extract_with_context(content="Test")
            
            assert result["entities"] == []
            assert result["relationships"] == []
            assert "error" in result


class TestIngestExtractedRelationships:
    """Tests for ingesting pre-extracted relationships."""

    @pytest.fixture
    def mock_graphiti_service(self):
        from api.services.graphiti_service import GraphitiService
        
        with patch.object(GraphitiService, '__init__', lambda x: None):
            service = GraphitiService()
            service.config = MagicMock()
            service.config.group_id = "test_group"
            service._initialized = True
            
            mock_graphiti = MagicMock()
            mock_graphiti.add_episode = AsyncMock(return_value=MagicMock())
            service._get_graphiti = MagicMock(return_value=mock_graphiti)
            service._graphiti = mock_graphiti
            
            return service

    async def test_only_approved_relationships_ingested(self, mock_graphiti_service):
        """Verify only approved relationships are ingested."""
        relationships = [
            {"source": "A", "target": "B", "relation_type": "EXTENDS", "status": "approved", "evidence": "test"},
            {"source": "C", "target": "D", "relation_type": "RELATES", "status": "pending_review", "evidence": "test"},
        ]
        
        result = await mock_graphiti_service.ingest_extracted_relationships(
            relationships=relationships,
            source_id="test_source"
        )
        
        assert result["ingested"] == 1
        assert result["skipped"] == 1

    async def test_ingestion_tracks_errors(self, mock_graphiti_service):
        """Verify ingestion errors are tracked."""
        mock_graphiti_service._get_graphiti().add_episode = AsyncMock(
            side_effect=Exception("Neo4j error")
        )
        
        relationships = [
            {"source": "A", "target": "B", "relation_type": "EXTENDS", "status": "approved", "evidence": "test"},
        ]
        
        result = await mock_graphiti_service.ingest_extracted_relationships(
            relationships=relationships,
            source_id="test_source"
        )
        
        assert result["ingested"] == 0
        assert len(result["errors"]) == 1


class TestKGLearningServiceIntegration:
    """Tests verifying KGLearningService uses consolidated extractor."""

    async def test_kg_learning_uses_graphiti_extract_with_context(self):
        """Verify KGLearningService calls GraphitiService.extract_with_context."""
        from api.services.kg_learning_service import KGLearningService
        
        mock_graphiti = AsyncMock()
        mock_graphiti.extract_with_context = AsyncMock(return_value={
            "entities": ["Entity1"],
            "relationships": [
                {"source": "A", "target": "B", "relation_type": "EXTENDS", 
                 "confidence": 0.9, "status": "approved", "evidence": "test"}
            ],
            "approved_count": 1,
            "pending_count": 0,
            "model_used": "test_model"
        })
        mock_graphiti.ingest_extracted_relationships = AsyncMock(return_value={
            "ingested": 1, "skipped": 0, "errors": []
        })
        
        service = KGLearningService()
        
        # Mock dependencies
        with patch('api.services.kg_learning_service.get_graphiti_service', return_value=mock_graphiti):
            with patch.object(service, '_get_relevant_basins', return_value="basin context"):
                with patch.object(service, '_get_active_strategies', return_value="strategy context"):
                    with patch.object(service, '_persist_proposal', return_value=None):
                        with patch.object(service, '_strengthen_basins', return_value=None):
                            with patch.object(service, 'evaluate_extraction', return_value={"precision_score": 0.5}):
                                result = await service.extract_and_learn(
                                    content="Test content",
                                    source_id="test_source"
                                )
        
        # Verify GraphitiService.extract_with_context was called
        mock_graphiti.extract_with_context.assert_called_once()
        call_kwargs = mock_graphiti.extract_with_context.call_args.kwargs
        assert call_kwargs["basin_context"] == "basin context"
        assert call_kwargs["strategy_context"] == "strategy context"
        
        # Verify relationships were ingested via GraphitiService
        mock_graphiti.ingest_extracted_relationships.assert_called_once()
        
        # Verify result
        assert len(result.entities) == 1
        assert len(result.relationships) == 1

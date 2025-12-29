import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.kg_learning_service import KGLearningService
from api.models.kg_learning import ExtractionResult, RelationshipProposal

@pytest.fixture
def mock_sonnet():
    with patch("api.services.kg_learning_service.SONNET", "mock-model"):
        yield

@pytest.mark.asyncio
async def test_extract_and_learn_gating(mock_sonnet):
    """Verify that low-confidence extractions are gated and high-confidence are persisted."""
    service = KGLearningService()
    service._driver = AsyncMock() # Mock the Neo4j driver
    
    # 1. Mock LLM Response with one high and one low confidence relation
    mock_data = {
        "entities": ["ConceptA", "ConceptB", "ConceptC"],
        "relationships": [
            {"source": "ConceptA", "target": "ConceptB", "type": "EXTENDS", "confidence": 0.9, "evidence": "Direct quote"},
            {"source": "ConceptB", "target": "ConceptC", "type": "RELATES_TO", "confidence": 0.3, "evidence": "Vague hint"}
        ]
    }
    
    with patch("api.services.kg_learning_service.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = json.dumps(mock_data)
        
        with patch("api.services.kg_learning_service.get_graphiti_service", new_callable=AsyncMock) as mock_get_graphiti:
            mock_graphiti = AsyncMock()
            mock_get_graphiti.return_value = mock_graphiti
            
            result = await service.extract_and_learn("Sample content", "source-1")
            
            # Verify high confidence (0.9) was sent to Graphiti
            # Only 1 ingest_message call for ConceptA -> ConceptB
            assert mock_graphiti.ingest_message.call_count == 1
            
            # Verify both were persisted as proposals via _persist_proposal
            # We check the call to execute_query in _persist_proposal (plus strengthening and strategies)
            # Actually, let's check the result object statuses
            assert result.relationships[0].status == "approved"
            assert result.relationships[1].status == "pending_review"
            
            # Verify provenance
            assert result.relationships[0].run_id is not None
            assert result.relationships[0].model_id == "mock-model"

@pytest.mark.asyncio
async def test_basin_strengthening():
    """Verify that basins are strengthened based on extracted entities."""
    service = KGLearningService()
    service._driver = AsyncMock()
    
    await service._strengthen_basins(["Alpha", "Beta"])
    
    # Verify MERGE query was called
    service._driver.execute_query.assert_called_once()
    args = service._driver.execute_query.call_args
    assert "MERGE (b:AttractorBasin" in args[0][0]
    assert args[0][1]["main"] == "Alpha"

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.kg_learning_service import KGLearningService


@pytest.fixture
def mock_model():
    with patch("api.services.kg_learning_service.GPT5_NANO", "mock-model"):
        yield


@pytest.mark.asyncio
async def test_extract_and_learn_gating(mock_model):
    """Verify that low-confidence extractions are gated and high-confidence are persisted."""
    service = KGLearningService()
    service._driver = AsyncMock()  # Mock the Neo4j driver

    # Mock GraphitiService with extract_with_context response
    mock_graphiti = AsyncMock()
    mock_graphiti.extract_with_context = AsyncMock(return_value={
        "entities": ["ConceptA", "ConceptB", "ConceptC"],
        "relationships": [
            {"source": "ConceptA", "target": "ConceptB", "relation_type": "EXTENDS",
             "confidence": 0.9, "evidence": "Direct quote", "status": "approved"},
            {"source": "ConceptB", "target": "ConceptC", "relation_type": "RELATES_TO",
             "confidence": 0.3, "evidence": "Vague hint", "status": "pending_review"}
        ],
        "approved_count": 1,
        "pending_count": 1,
        "model_used": "mock-model"
    })
    mock_graphiti.ingest_extracted_relationships = AsyncMock(return_value={
        "ingested": 1, "skipped": 1, "errors": []
    })

    with patch("api.services.kg_learning_service.get_graphiti_service", return_value=mock_graphiti):
        with patch.object(service, '_get_relevant_basins', return_value="basin context"):
            with patch.object(service, '_get_active_strategies', return_value="strategy context"):
                with patch.object(service, '_persist_proposal', return_value=None):
                    with patch.object(service, '_strengthen_basins', return_value=None):
                        with patch.object(service, 'evaluate_extraction', return_value={"precision_score": 0.5}):
                            result = await service.extract_and_learn("Sample content", "source-1")

    # Verify extract_with_context was called with context
    mock_graphiti.extract_with_context.assert_called_once()
    call_kwargs = mock_graphiti.extract_with_context.call_args.kwargs
    assert call_kwargs["basin_context"] == "basin context"
    assert call_kwargs["strategy_context"] == "strategy context"

    # Verify only approved relationships were ingested
    mock_graphiti.ingest_extracted_relationships.assert_called_once()

    # Verify result contains relationships with correct statuses
    assert len(result.relationships) == 2
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

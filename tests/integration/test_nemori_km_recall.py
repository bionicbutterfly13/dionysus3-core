import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.nemori_recall_service import NemoriRecallService
from api.models.autobiographical import DevelopmentEpisode, DevelopmentArchetype
from datetime import datetime

@pytest.mark.asyncio
async def test_nemori_km_recall_ratio():
    """Verify the k/m retrieval ratio logic."""
    # 1. Setup mocks
    mock_episodes = [
        DevelopmentEpisode(
            episode_id="ep-1", journey_id="j-1", title="Ep 1", 
            summary="Sum 1", narrative="Long narrative 1", 
            start_time=datetime.utcnow(), end_time=datetime.utcnow(),
            dominant_archetype=DevelopmentArchetype.SAGE
        ),
        DevelopmentEpisode(
            episode_id="ep-2", journey_id="j-1", title="Ep 2", 
            summary="Sum 2", narrative="Long narrative 2", 
            start_time=datetime.utcnow(), end_time=datetime.utcnow()
        ),
        DevelopmentEpisode(
            episode_id="ep-3", journey_id="j-1", title="Ep 3", 
            summary="Sum 3", narrative="Long narrative 3", 
            start_time=datetime.utcnow(), end_time=datetime.utcnow()
        )
    ]
    
    mock_store = AsyncMock()
    mock_store.search_episodes = AsyncMock(return_value=mock_episodes)
    
    mock_semantic_result = MagicMock()
    mock_semantic_result.content = "Semantic fact 1"
    
    mock_search_response = MagicMock()
    mock_search_response.results = [mock_semantic_result]
    
    mock_vector_search = AsyncMock()
    mock_vector_search.semantic_search = AsyncMock(return_value=mock_search_response)
    
    # 2. Execute recall
    with patch("api.services.nemori_recall_service.get_consolidated_memory_store", return_value=mock_store), \
         patch("api.services.nemori_recall_service.get_vector_search_service", return_value=mock_vector_search):
         
        svc = NemoriRecallService(k=3, m=5)
        result = await svc.recall_with_nemori_ratio("test query")
        
        # 3. Verify
        assert result["episodes_count"] == 3
        assert result["semantic_count"] == 1
        
        context = result["formatted_context"]
        assert "[FULL] Ep 1" in context
        assert "[FULL] Ep 2" in context
        assert "Ep 3:" in context # Abbreviated
        assert "Semantic fact 1" in context

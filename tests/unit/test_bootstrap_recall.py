import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from api.services.bootstrap_recall_service import BootstrapRecallService
from api.models.bootstrap import BootstrapConfig

@pytest.fixture
def bootstrap_service():
    return BootstrapRecallService()

@pytest.mark.asyncio
async def test_recall_context_success(bootstrap_service):
    """Verify successful hybrid recall and formatting."""
    config = BootstrapConfig(project_id="test-project")
    
    with patch("api.services.bootstrap_recall_service.get_vector_search_service") as mock_vector, \
         patch("api.services.bootstrap_recall_service.get_graphiti_service") as mock_graphiti:
        
        # Mock Vector Search
        mock_vec_svc = AsyncMock()
        mock_vec_svc.semantic_search.return_value = MagicMock(results=[
            MagicMock(content="semantic memory 1", similarity_score=0.9, memory_type="semantic")
        ])
        mock_vector.return_value = mock_vec_svc
        
        # Mock Graphiti
        mock_graph_svc = AsyncMock()
        mock_graph_svc.search.return_value = [{"content": "temporal trajectory 1"}]
        mock_graphiti.return_value = mock_graph_svc
        
        result = await bootstrap_service.recall_context(query="test query", project_id="test-project", config=config)
        
        assert "## Past Context" in result.formatted_context
        assert "test-project" in result.formatted_context
        assert "semantic memory 1" in result.formatted_context
        assert "temporal trajectory 1" in result.formatted_context
        assert result.source_count == 2
        assert result.summarized is False

@pytest.mark.asyncio
async def test_timeout_logic(bootstrap_service):
    """T010a: Unit test for bootstrap timeout and graceful fallback"""
    config = BootstrapConfig(project_id="test-project")
    
    async def slow_recall(*args, **kwargs):
        await asyncio.sleep(3.0) # Longer than 2s timeout
        return []

    with patch.object(bootstrap_service, "_execute_recall", side_effect=slow_recall):
        result = await bootstrap_service.recall_context(query="query", project_id="test", config=config)
        
        assert result.source_count == 0
        assert "timed out" in result.formatted_context

@pytest.mark.asyncio
async def test_summarization_trigger(bootstrap_service):
    """T008: Verify LLM summarization triggers on large payloads."""
    config = BootstrapConfig(project_id="test-project", max_tokens=10) # Tiny limit
    
    # Large context that exceeds 10 tokens heuristic
    large_context = "word " * 100 
    
    with patch("api.services.bootstrap_recall_service.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Summary text"
        
        # We need to bypass the actual retrieval to test summarization logic
        with patch.object(bootstrap_service, "_fetch_semantic_memories", return_value=[{"content": large_context, "score": 0.9, "type": "s"}]), \
             patch.object(bootstrap_service, "_fetch_temporal_trajectories", return_value=[]):
            
            result = await bootstrap_service.recall_context(query="q", project_id="p", config=config)
            
            assert result.summarized is True
            assert "Summarized" in result.formatted_context
            mock_chat.assert_called_once()

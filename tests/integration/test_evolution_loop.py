"""
Integration tests for Consciousness Self-Evolution (Feature 049).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.meta_evolution_service import MetaEvolutionService
from api.models.evolution import SystemMoment, EvolutionUpdate

@pytest.mark.asyncio
async def test_capture_system_moment():
    mock_driver = AsyncMock()
    # Mock node count results
    mock_driver.execute_query.return_value = [{"l": ["Memory"], "c": 100}]
    
    with patch("api.services.meta_evolution_service.get_neo4j_driver", return_value=mock_driver):
        service = MetaEvolutionService()
        moment = await service.capture_system_moment()
        
        assert isinstance(moment, SystemMoment)
        assert moment.total_memories_count == 100
        assert mock_driver.execute_query.call_count == 2 # One for count, one for create

@pytest.mark.asyncio
async def test_run_evolution_cycle():
    mock_driver = AsyncMock()
    # Mock high-surprise episodes
    mock_driver.execute_query.return_value = [
        {"e": {"task_query": "failed task", "surprise_score": 0.9, "timestamp": "..."}}
    ]
    
    service = MetaEvolutionService()
    
    with patch("api.services.meta_evolution_service.get_neo4j_driver", return_value=mock_driver), \
         patch("api.services.meta_evolution_service.chat_completion", new_callable=AsyncMock) as mock_chat, \
         patch("api.services.meta_evolution_service.get_consciousness_pipeline") as mock_pipe_getter:
        
        mock_chat.return_value = '{"new_strategy_description": "Be more careful", "rationale": "High surprise detected", "expected_improvement": 0.5}'
        mock_pipeline = AsyncMock()
        mock_pipe_getter.return_value = mock_pipeline
        
        update = await service.run_evolution_cycle()
        
        assert isinstance(update, EvolutionUpdate)
        assert update.new_strategy_description == "Be more careful"
        mock_pipeline.process_cognitive_event.assert_called_once()

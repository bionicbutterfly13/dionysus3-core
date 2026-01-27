import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.nemori_river_flow import NemoriRiverFlow
from api.models.autobiographical import DevelopmentEpisode
from datetime import datetime

@pytest.mark.asyncio
async def test_meta_evolution_trigger_on_high_surprisal():
    """Verify that high surprisal in predict_and_calibrate triggers Meta-Evolution."""
    # 1. Setup mocks
    mock_episode = DevelopmentEpisode(
        episode_id="ep-123", journey_id="j-1", title="Test", 
        summary="Test", narrative="Test",
        start_time=datetime.utcnow(), end_time=datetime.utcnow()
    )
    
    # Mock LLM response with HIGH surprisal
    mock_calibration_response = """
    {
      "new_facts": ["Dionysus is self-aware"],
      "symbolic_residue": {"active_goals": [], "active_entities": [], "stable_context": ""},
      "surprisal": 0.85
    }
    """
    
    mock_adapter = AsyncMock()
    mock_adapter.trigger_evolution = AsyncMock(return_value={"status": "evolved"})
    
    with patch("api.services.nemori_river_flow.chat_completion", return_value=mock_calibration_response), \
         patch("api.services.nemori_river_flow.get_memevolve_adapter", return_value=mock_adapter), \
         patch("api.services.nemori_river_flow.get_memory_basin_router", return_value=AsyncMock()), \
         patch("api.services.nemori_river_flow.get_graphiti_service", return_value=AsyncMock()):
         
        river = NemoriRiverFlow()
        await river.predict_and_calibrate(mock_episode, [], {"name": "test", "description": "test context"})
        
        # 3. Verify evolution was triggered
        mock_adapter.trigger_evolution.assert_called_once()

@pytest.mark.asyncio
async def test_meta_evolution_not_triggered_on_low_surprisal():
    """Verify that low surprisal does NOT trigger Meta-Evolution."""
    # 1. Setup mocks
    mock_episode = DevelopmentEpisode(
        episode_id="ep-123", journey_id="j-1", title="Test", 
        summary="Test", narrative="Test",
        start_time=datetime.utcnow(), end_time=datetime.utcnow()
    )
    
    # Mock LLM response with LOW surprisal
    mock_calibration_response = """
    {
      "new_facts": [],
      "symbolic_residue": {"active_goals": [], "active_entities": [], "stable_context": ""},
      "surprisal": 0.1
    }
    """
    
    mock_adapter = AsyncMock()
    mock_adapter.trigger_evolution = AsyncMock()
    
    with patch("api.services.nemori_river_flow.chat_completion", return_value=mock_calibration_response), \
         patch("api.services.nemori_river_flow.get_memevolve_adapter", return_value=mock_adapter), \
         patch("api.services.nemori_river_flow.get_memory_basin_router", return_value=AsyncMock()), \
         patch("api.services.nemori_river_flow.get_graphiti_service", return_value=AsyncMock()):
         
        river = NemoriRiverFlow()
        await river.predict_and_calibrate(mock_episode, [], {"name": "test", "description": "test context"})
        
        # 3. Verify evolution was NOT triggered
        mock_adapter.trigger_evolution.assert_not_called()

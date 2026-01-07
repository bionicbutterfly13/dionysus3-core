
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import json

from api.services.consciousness_integration_pipeline import ConsciousnessIntegrationPipeline
from api.models.beautiful_loop import ResonanceSignal, ResonanceMode

@pytest.mark.asyncio
async def test_pipeline_propagates_resonance_signal():
    # Setup mocks
    mock_memory_core = AsyncMock()
    mock_tier_svc = AsyncMock()
    mock_graphiti = AsyncMock()
    mock_learner = AsyncMock()
    
    # Setup pipeline with mocks
    with patch("api.services.consciousness_integration_pipeline.get_consciousness_memory_core", return_value=mock_memory_core), \
         patch("api.services.consciousness_integration_pipeline.get_multi_tier_service", return_value=mock_tier_svc), \
         patch("api.services.consciousness_integration_pipeline.get_graphiti_service", new_callable=AsyncMock) as mock_get_graphiti, \
         patch("api.services.consciousness_integration_pipeline.get_meta_learner", return_value=mock_learner):
         
        mock_get_graphiti.return_value = mock_graphiti
        
        pipeline = ConsciousnessIntegrationPipeline()
        
        # specific resonance signal
        resonance = ResonanceSignal(
            mode=ResonanceMode.DISSONANT,
            resonance_score=0.1,
            surprisal=0.9,
            coherence=0.2,
            discovery_urgency=0.8
        )
        
        context = {
            "project_id": "test_project",
            "resonance_signal": resonance
        }
        
        # Execute
        await pipeline.process_cognitive_event(
            problem="Test dissonance",
            reasoning_trace="Reasoning...",
            context=context
        )
        
        # Verify memory core interaction
        assert mock_memory_core.record_interaction.called
        call_args = mock_memory_core.record_interaction.call_args
        assert call_args is not None
        
        # Check arguments
        _, kwargs = call_args
        assert kwargs.get("resonance_signal") == resonance
        assert kwargs["resonance_signal"].mode == ResonanceMode.DISSONANT

    

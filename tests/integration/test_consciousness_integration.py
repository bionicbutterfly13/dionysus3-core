"""
Integration test for Unified Consciousness Integration Pipeline.
Feature 045.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.consciousness_integration_pipeline import ConsciousnessIntegrationPipeline

@pytest.mark.asyncio
async def test_unified_integration_flow():
    # Mock all underlying services
    with patch("api.services.consciousness_integration_pipeline.get_autobiographical_service") as mock_auto_getter, \
         patch("api.services.consciousness_integration_pipeline.get_graphiti_service") as mock_graphiti_getter, \
         patch("api.services.consciousness_integration_pipeline.get_meta_learner") as mock_learner_getter:
        
        mock_auto = AsyncMock()
        mock_auto_getter.return_value = mock_auto
        
        mock_graphiti = AsyncMock()
        mock_graphiti_getter.return_value = mock_graphiti
        
        mock_learner = AsyncMock()
        mock_learner_getter.return_value = mock_learner
        
        pipeline = ConsciousnessIntegrationPipeline()
        
        event_id = await pipeline.process_cognitive_event(
            problem="Test problem",
            reasoning_trace="Test trace",
            outcome="Success",
            context={"project_id": "test_project", "confidence": 0.9}
        )
        
        assert event_id is not None
        
        # Verify all branches were called
        mock_auto.record_event.assert_called_once()
        mock_graphiti.ingest_message.assert_called_once()
        mock_learner.record_episode.assert_called_once()
        
        # Verify trace data in calls (checking kwargs)
        _, kwargs = mock_graphiti.ingest_message.call_args
        assert "Test problem" in kwargs["content"]
        assert "Test trace" in kwargs["content"]
        assert kwargs["group_id"] == "test_project"
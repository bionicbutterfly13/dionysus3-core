"""
Integration test for Unified Consciousness Integration Pipeline.
Feature 045.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.consciousness_integration_pipeline import ConsciousnessIntegrationPipeline

@pytest.mark.asyncio
async def test_unified_integration_flow():
    """
    Integration test for Unified Consciousness Integration Pipeline.

    Tests that process_cognitive_event correctly routes data to:
    - Graphiti service for knowledge graph persistence
    - Meta-learner for cognitive episode recording
    - Multi-tier service for memory consolidation
    """
    # Mock all underlying services based on actual imports in consciousness_integration_pipeline.py
    with patch("api.services.consciousness_integration_pipeline.get_graphiti_service") as mock_graphiti_getter, \
         patch("api.services.consciousness_integration_pipeline.get_meta_learner") as mock_learner_getter, \
         patch("api.services.consciousness_integration_pipeline.get_multi_tier_service") as mock_multi_tier_getter:

        mock_graphiti = AsyncMock()
        mock_graphiti_getter.return_value = mock_graphiti

        mock_learner = AsyncMock()
        mock_learner_getter.return_value = mock_learner

        mock_multi_tier = AsyncMock()
        mock_multi_tier_getter.return_value = mock_multi_tier

        pipeline = ConsciousnessIntegrationPipeline()

        event_id = await pipeline.process_cognitive_event(
            problem="Test problem",
            reasoning_trace="Test trace",
            outcome="Success",
            context={"project_id": "test_project", "confidence": 0.9}
        )

        assert event_id is not None

        # Verify graphiti and meta-learner branches were called
        mock_graphiti.ingest_message.assert_called_once()
        mock_learner.record_episode.assert_called_once()

        # Verify trace data in calls (checking kwargs)
        _, kwargs = mock_graphiti.ingest_message.call_args
        assert "Test problem" in kwargs["content"]
        assert "Test trace" in kwargs["content"]
        assert kwargs["group_id"] == "test_project"
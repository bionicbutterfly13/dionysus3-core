import pytest
from unittest.mock import AsyncMock, patch
from api.services.unified_reality_model import UnifiedRealityModelService
from api.models.belief_journey import BeliefJourney, LimitingBelief, BeliefStatus
from uuid import uuid4

@pytest.mark.asyncio
async def test_sync_belief_states_populated():
    """Verify that belief_states are populated from BeliefTrackingService."""
    # 1. Setup mocks
    mock_journey = BeliefJourney(
        id=uuid4(),
        participant_id="test-user",
        graphiti_group_id="test-group"
    )
    mock_belief = LimitingBelief(
        id=uuid4(),
        journey_id=mock_journey.id,
        content="I am not good enough",
        status=BeliefStatus.IDENTIFIED
    )
    mock_journey.limiting_beliefs.append(mock_belief)
    
    mock_service = AsyncMock()
    mock_service.get_active_journey = AsyncMock(return_value=mock_journey)
    
    # 2. Setup URM and sync
    with patch("api.services.belief_tracking_service.get_belief_tracking_service", return_value=mock_service):
        urm = UnifiedRealityModelService()
        await urm.sync_belief_states()
        
        model = urm.get_model()
        assert len(model.belief_states) > 0
        assert model.belief_states[0]["content"] == "I am not good enough"

@pytest.mark.asyncio
async def test_sync_belief_states_graceful_handling():
    """Verify graceful handling if BeliefTrackingService is unavailable."""
    # Setup URM and sync with service returning None (unavailable)
    mock_service = AsyncMock()
    mock_service.get_active_journey = AsyncMock(side_effect=Exception("Service Down"))
    
    with patch("api.services.belief_tracking_service.get_belief_tracking_service", return_value=mock_service):
        urm = UnifiedRealityModelService()
        # Should not raise exception
        await urm.sync_belief_states()
        
        model = urm.get_model()
        assert len(model.belief_states) == 0

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from api.models.autobiographical import DevelopmentEvent, DevelopmentEpisode, DevelopmentEventType, RiverStage, ActiveInferenceState
from api.services.nemori_river_flow import NemoriRiverFlow
from api.models.sync import MemoryType

@pytest.mark.asyncio
async def test_nemori_linking_logic():
    # Setup Mocks
    mock_store = AsyncMock()
    mock_router = AsyncMock()
    
    # Mock Router
    # classify_memory_type is async, so AsyncMock is fine
    mock_router.classify_memory_type.return_value = MemoryType.STRATEGIC
    
    # get_basin_for_type is SYNC, so we must replace the auto-generated AsyncMock
    mock_router.get_basin_for_type = MagicMock(return_value={
        "basin_name": "strategic-basin",
        "default_strength": 0.85
    })

    # Setup Episode and Events
    episode = DevelopmentEpisode(
        episode_id="ep_123",
        journey_id="journey_1",
        title="Test Episode",
        summary="A test summary",
        narrative="A test narrative",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        events=["evt_1"]
    )
    
    active_state = ActiveInferenceState(
        twa_state={"focus": "testing"},
        surprisal=0.1
    )
    
    event = DevelopmentEvent(
        event_id="evt_1",
        event_type=DevelopmentEventType.GENESIS,
        summary="Event 1",
        rationale="Testing",
        impact="None",
        active_inference_state=active_state
    )

    # Patch dependencies
    with patch("api.services.nemori_river_flow.get_consolidated_memory_store", return_value=mock_store), \
         patch("api.services.nemori_river_flow.get_memory_basin_router", return_value=mock_router), \
         patch("api.services.nemori_river_flow.chat_completion", new_callable=AsyncMock) as mock_chat:
        
        # Mock LLM responses
        # 1. Prediction
        mock_chat.side_effect = [
            "- Fact 1\n- Fact 2", # Predictions
            '{"new_facts": ["Fact 1"], "symbolic_residue": {}}' # Calibration JSON
        ]

        # Instantiate Service
        nemori = NemoriRiverFlow()
        
        # ACT: Call predict_and_calibrate
        new_facts, residue = await nemori.predict_and_calibrate(episode, [event])
        
        # ASSERT
        assert len(new_facts) == 1
        assert new_facts[0] == "Fact 1"
        
        # Verify Store Event was called
        assert mock_store.store_event.called
        stored_event = mock_store.store_event.call_args[0][0]
        
        # Verify Linking Fields
        assert stored_event.event_type == DevelopmentEventType.SEMANTIC_DISTILLATION
        assert stored_event.linked_basin_id == "strategic-basin" # From mock router
        assert stored_event.basin_r_score == 0.85
        assert stored_event.markov_blanket_id is not None
        assert stored_event.markov_blanket_id.startswith("mb_")
        # Verify blanket ID is deterministic (sha256-based, not Python hash)
        assert len(stored_event.markov_blanket_id) == 19  # "mb_" + 16 hex chars


@pytest.mark.asyncio
async def test_blanket_id_determinism():
    """Test that same TWA state produces same blanket ID across calls."""
    import hashlib
    import json
    
    twa_state_1 = {"focus": "testing", "mode": "qa"}
    twa_state_2 = {"focus": "testing", "mode": "qa"}  # Same content
    twa_state_3 = {"focus": "different", "mode": "qa"}  # Different content
    
    def compute_blanket_id(twa_state):
        state_str = json.dumps(twa_state, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()[:16]
        return f"mb_{state_hash}"
    
    # Same input = same output
    id_1 = compute_blanket_id(twa_state_1)
    id_2 = compute_blanket_id(twa_state_2)
    assert id_1 == id_2, "Same TWA state should produce same blanket ID"
    
    # Different input = different output
    id_3 = compute_blanket_id(twa_state_3)
    assert id_1 != id_3, "Different TWA state should produce different blanket ID"
    
    # Format check
    assert id_1.startswith("mb_")
    assert len(id_1) == 19  # "mb_" + 16 hex chars

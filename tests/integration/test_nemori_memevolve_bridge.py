import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from api.services.nemori_river_flow import NemoriRiverFlow
from api.models.autobiographical import (
    DevelopmentEpisode, 
    DevelopmentEvent, 
    DevelopmentArchetype, 
    RiverStage, 
    DevelopmentEventType
)

@pytest.mark.asyncio
async def test_predict_and_calibrate_persists_facts():
    """Verify T041-028: Nemori facts go to Graphiti."""
    
    # Setup
    flow = NemoriRiverFlow()
    episode = DevelopmentEpisode(
        episode_id="ep_test_1",
        journey_id="j_1",
        title="Test Episode",
        summary="A test summary",
        narrative="A test narrative",
        events=["ev1"],
        river_stage=RiverStage.MAIN_RIVER,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc)
    )
    events = [DevelopmentEvent(
        event_id="ev1", 
        timestamp=datetime.now(timezone.utc), 
        event_type=DevelopmentEventType.SYSTEM_REFLECTION,
        summary="Event 1",
        rationale="Rational for event 1",
        river_stage=RiverStage.SOURCE,
        impact="None"
    )]
    
    # Mocks
    mock_graphiti = AsyncMock()
    # Router must handle both sync and async methods
    mock_router = MagicMock(spec=NemoriRiverFlow) # utilizing duck typing or spec 
    mock_router.classify_memory_type = AsyncMock(return_value="episodic")
    mock_router.get_basin_for_type = MagicMock(return_value={"basin_name": "hexis_consent", "default_strength": 0.5})
    
    # Mock LLM calls to return predictable JSON
    mock_chat_response = """
    ```json
    {
        "new_facts": ["Fact 1", "Fact 2"],
        "symbolic_residue": {"active_goals": ["Goal A"]}
    }
    ```
    """
    # First call is predictions (list), second is calibration (JSON)
    # We'll just mock the responses carefully or use side_effect
    
    with patch("api.services.nemori_river_flow.get_graphiti_service", new=AsyncMock(return_value=mock_graphiti)), \
         patch("api.services.nemori_river_flow.get_memory_basin_router", return_value=mock_router), \
         patch("api.services.nemori_river_flow.chat_completion", side_effect=["- Prediction 1", mock_chat_response]), \
         patch("api.services.nemori_river_flow.get_token_budget_manager"), \
         patch("api.services.nemori_river_flow.get_residue_tracker"):
         
         # Mock router behavior (already set above, but ensuring)
         # mock_router.classify_memory_type.return_value = "episodic" 
         # mock_router.get_basin_for_type.return_value = ...
         
         # Execute
         new_facts, residue = await flow.predict_and_calibrate(episode, events)
         
         # Verify
         assert len(new_facts) == 2
         assert "Fact 1" in new_facts
         
         # Check Graphiti Persistence
         assert mock_graphiti.persist_fact.call_count == 2
         mock_graphiti.persist_fact.assert_any_call(
             fact_text="Fact 1",
             source_episode_id="ep_test_1",
             valid_at=pytest.any(datetime), # checking types roughly
             basin_id="hexis_consent",
             confidence=0.8
         )

@pytest.mark.asyncio
async def test_construct_episode_bridges_to_trajectory():
    """Verify T041-029: Episodes are bridged to Trajectories."""
    
    flow = NemoriRiverFlow()
    events = [DevelopmentEvent(
        event_id="ev1", 
        timestamp=datetime.now(timezone.utc), 
        event_type=DevelopmentEventType.SYSTEM_REFLECTION,
        summary="Event 1",
        rationale="Rationale for event 1",
        river_stage=RiverStage.SOURCE,
        impact="Low"
    )]
    
    mock_adapter = AsyncMock()
    mock_episode_llm = """
    ```json
    {
        "title": "Bridged Episode",
        "summary": "Summary of bridged episode",
        "narrative": "Detailed narrative",
        "archetype": "sage",
        "strand_id": "testing"
    }
    ```
    """
    mock_sharpen_llm = "Sharpened Narrative"
    
    with patch("api.services.nemori_river_flow.get_memevolve_adapter", return_value=mock_adapter), \
         patch("api.services.nemori_river_flow.chat_completion", side_effect=[mock_episode_llm, mock_sharpen_llm]), \
         patch.object(flow.store, "create_episode", new=AsyncMock()):
         
         result = await flow.construct_episode(events, "journey_1")
         
         assert result is not None
         assert result.title == "Bridged Episode"
         
         # Verify Bridge Call
         assert mock_adapter.ingest_trajectory.called
         call_args = mock_adapter.ingest_trajectory.call_args[0][0]
         
         assert call_args.project_id == "dionysus_core"
         assert call_args.memory_type == "episodic"
         # Check trajectory content
         steps = call_args.trajectory.steps
         assert "Summary: Summary of bridged episode" in steps[0].observation
         assert "Narrative: Sharpened Narrative" in steps[0].thought

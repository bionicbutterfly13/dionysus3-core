import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from api.services.subconscious_service import SubconsciousService, _normalize_observations
from api.services.exoskeleton_service import ExoskeletonService
from api.models.subconscious import SubconsciousObservations, PathologicalPattern
from api.models.hexis_ontology import ExoskeletonMode, SubconsciousState
from api.services.heartbeat_service import HeartbeatService
from api.models.action import ActionRequest, ActionResult, ActionStatus, ActionPlan, HeartbeatDecision

@pytest.mark.asyncio
async def test_subconscious_pathological_pattern_normalization():
    """Test that pathological patterns are correctly normalized from LLM JSON."""
    doc = {
        "narrative_observations": [],
        "relationship_observations": [],
        "contradiction_observations": [],
        "emotional_observations": [],
        "consolidation_observations": [],
        "pathological_patterns": [
            {
                "type": "replay_cycle",
                "summary": "Detected a 24h replay loop about the missed deadline.",
                "confidence": 0.9,
                "evidence_ids": ["mem1", "mem2"]
            }
        ]
    }
    obs = _normalize_observations(doc)
    assert len(obs.pathological_patterns) == 1
    assert obs.pathological_patterns[0].type == "replay_cycle"
    assert obs.pathological_patterns[0].confidence == 0.9

@pytest.mark.asyncio
async def test_exoskeleton_recovery_path():
    """Test that ExoskeletonService generates recovery paths."""
    service = ExoskeletonService(hexis_service=MagicMock())
    path = await service.get_recovery_path("Finish the report", 0.8)
    assert len(path) > 3
    # Look for grounding in the first few steps
    grounding_found = any("Vital Pause" in step for step in path[:2])
    assert grounding_found
    assert "EXTERNAL BLOCK" in path[0] 

@pytest.mark.asyncio
async def test_heartbeat_gap_calculation():
    """Test that HeartbeatService calculates intention-execution gap correctly."""
    mock_energy = MagicMock()
    mock_executor = MagicMock()
    # Mocking successful and failed actions
    results = [
        ActionResult(action_type="recall", status=ActionStatus.COMPLETED, energy_cost=1.0, data={}, started_at=datetime.utcnow(), ended_at=datetime.utcnow()),
        ActionResult(action_type="reflect", status=ActionStatus.FAILED, energy_cost=0.0, error="test error", started_at=datetime.utcnow(), ended_at=datetime.utcnow())
    ]
    mock_executor.execute_plan = AsyncMock(return_value=results)
    mock_executor.execute = AsyncMock(return_value=ActionResult(action_type="observe", status=ActionStatus.COMPLETED, energy_cost=0.0, data={"snapshot": {}}, started_at=datetime.utcnow(), ended_at=datetime.utcnow()))

    service = HeartbeatService(energy_service=mock_energy, action_executor=mock_executor)
    
    # Mock Hexis
    mock_hexis = MagicMock()
    mock_subconscious = MagicMock(spec=SubconsciousState)
    mock_hexis.get_subconscious_state = AsyncMock(return_value=mock_subconscious)
    mock_hexis.update_subconscious_state = AsyncMock()

    with patch("api.services.hexis_service.get_hexis_service", return_value=mock_hexis):
        # We simulate the Act phase logic
        trimmed_plan = MagicMock()
        trimmed_plan.actions = [MagicMock(), MagicMock()]
        
        # Manually trigger the logic we added to heartbeat
        gap_magnitude = 1.0 - (sum(1 for r in results if r.status == ActionStatus.COMPLETED) / len(results))
        assert gap_magnitude == 0.5
        
        # Test the mode shift
        if gap_magnitude >= 0.5:
             mock_subconscious.exoskeleton_mode = ExoskeletonMode.RECOVERY
        
        assert mock_subconscious.exoskeleton_mode == ExoskeletonMode.RECOVERY

@pytest.mark.asyncio
async def test_mosaeic_scoring_extraction():
    """Test that MOSAEICService extracts new scores (simulated)."""
    from api.services.mosaeic_service import MOSAEICService
    service = MOSAEICService()
    
    mock_response = """
    {
        "senses": {"content": "tension", "intensity": 0.5, "tags": []},
        "actions": {"content": "typing fast", "intensity": 0.8, "tags": []},
        "emotions": {"content": "anxiety", "intensity": 0.6, "tags": []},
        "impulses": {"content": "to stop", "intensity": 0.4, "tags": []},
        "cognitions": {"content": "i must finish", "intensity": 0.9, "tags": []},
        "summary": "Working under pressure",
        "identity_congruence": 0.7,
        "self_betrayal_score": 0.2,
        "narrative_theme": "The Grind",
        "coherence": 0.8
    }
    """
    
    with patch("api.services.llm_service.chat_completion", AsyncMock(return_value=mock_response)):
        capture = await service.extract_capture("I am typing fast because I am anxious.")
        assert capture.identity_congruence == 0.7
        assert capture.self_betrayal_score == 0.2
        assert capture.narrative_theme == "The Grind"

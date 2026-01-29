import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from api.services.exoskeleton_service import ExoskeletonService
from api.models.exoskeleton import RecoveryPathway, SurrogateFilter, MismatchExperiment
from api.models.hexis_ontology import ExoskeletonMode, SubconsciousState
from api.services.heartbeat_service import HeartbeatService, ContextBuilder, HeartbeatContext
from api.models.action import EnvironmentSnapshot, GoalsSnapshot
from api.models.goal import GoalAssessment

@pytest.mark.asyncio
async def test_exoskeleton_advanced_features():
    """Test Surrogate Filter and Mismatch Experiment logic."""
    mock_hexis = MagicMock()
    # Mock hexis service to avoid real Neo4j/Graphiti initialization
    with patch("api.services.exoskeleton_service.get_hexis_service", return_value=mock_hexis):
        service = ExoskeletonService(hexis_service=mock_hexis)
        
        # 1. Test Surrogate Filter generation
        sf = await service.generate_surrogate_filter()
        assert "Prioritize grounding" in sf.directives[0]
        assert "abandon_task" in sf.forbidden_actions
        assert sf.obedience_tier == 3
        
        # 2. Test Mismatch Experiment
        mock_subconscious = MagicMock()
        mock_subconscious.temporal_priors = {}
        mock_hexis.get_subconscious_state = AsyncMock(return_value=mock_subconscious)
        mock_hexis.update_subconscious_state = AsyncMock()
        
        exp = await service.record_mismatch_experiment(
            prediction="System will crash",
            catastrophe_level=0.9,
            result="Success"
        )
        
        assert exp.outcome_delta == 0.9

@pytest.mark.asyncio
async def test_heartbeat_scaffolding_injection():
    """Test that HeartbeatContext correctly includes exoskeleton scaffolding in RECOVERY mode."""
    mock_subconscious = MagicMock()
    mock_subconscious.exoskeleton_mode = ExoskeletonMode.RECOVERY
    mock_subconscious.modality = "siege_locked"
    mock_subconscious.intention_execution_gap = 0.8
    mock_subconscious.active_loops = []
    mock_subconscious.is_finality_predicted = False
    
    # Mocking external services
    with patch("api.services.hexis_service.get_hexis_service") as mock_get_hexis:
        mock_get_hexis.return_value.get_subconscious_state = AsyncMock(return_value=mock_subconscious)
        
        builder = ContextBuilder(driver=MagicMock())
        builder._get_driver = MagicMock()
        
        env = EnvironmentSnapshot(heartbeat_number=1, current_energy=10.0)
        goal_snapshot = GoalsSnapshot(active=[], queued=[], blocked=[], stale=[])
        goal_assessment = GoalAssessment(
            active_goals=[], 
            queued_goals=[], 
            blocked_goals=[], 
            stale_goals=[], 
            issues=[], 
            snapshot=goal_snapshot
        )
        
        with patch("api.services.exoskeleton_service.get_exoskeleton_service") as mock_get_exoskeleton:
            mock_exo = MagicMock()
            mock_exo.get_recovery_path = AsyncMock(return_value=MagicMock())
            mock_exo.generate_surrogate_filter = AsyncMock(return_value=MagicMock())
            mock_get_exoskeleton.return_value = mock_exo
            
            context = await builder.build_context(env, goal_assessment)
            
            assert context.recovery_pathway is not None
            assert context.surrogate_filter is not None

@pytest.mark.asyncio
async def test_mosaeic_signal_loss_prompt():
    """Test that MOSAEIC prompt includes signal loss identification instructions."""
    from api.services.mosaeic_service import MOSAEICService
    service = MOSAEICService()
    
    # Correct the patching path to the service's local import
    with patch("api.services.mosaeic_service.chat_completion") as mock_chat:
        # Provide a valid JSON response to avoid validation errors
        mock_chat.return_value = """{
            "senses": {"content": "tension", "intensity": 0.5, "precision": 1.0, "surprisal": 0.0, "narrative_theme": "signal loss", "tags": []},
            "actions": {"content": "none", "intensity": 0.0, "precision": 1.0, "surprisal": 0.0, "narrative_theme": "...", "tags": []},
            "emotions": {"content": "none", "intensity": 0.0, "precision": 1.0, "surprisal": 0.0, "narrative_theme": "...", "tags": []},
            "impulses": {"content": "none", "intensity": 0.0, "precision": 1.0, "surprisal": 0.0, "narrative_theme": "...", "tags": []},
            "cognitions": {"content": "none", "intensity": 0.0, "precision": 1.0, "surprisal": 0.0, "narrative_theme": "...", "tags": []},
            "summary": "drift detected",
            "identity_congruence": 0.5,
            "self_betrayal_score": 0.8,
            "narrative_theme": "drift",
            "coherence": 0.5
        }"""
        await service.extract_capture("drift")
        
        assert mock_chat.called
        prompt = mock_chat.call_args[1]["messages"][0]["content"]
        assert "SIGNAL LOSS IDENTIFICATION" in prompt
        assert "narrative_theme" in prompt

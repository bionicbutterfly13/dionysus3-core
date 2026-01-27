
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json
from api.agents.consciousness_manager import ConsciousnessManager
from api.models.belief_state import BeliefState as CanonicalBeliefState

@pytest.mark.asyncio
async def test_criticality_trigger_high_entropy():
    # Mock dependencies
    with patch("api.agents.consciousness_manager.get_active_inference_service") as mock_get_ai_svc, \
         patch("api.agents.consciousness_manager.get_metaplasticity_controller") as mock_get_meta_ctrl, \
         patch("api.agents.consciousness_manager.get_meta_learner"), \
         patch("api.agents.consciousness_manager.get_particle_store"), \
         patch("api.agents.consciousness_manager.BootstrapRecallService"), \
         patch("api.agents.consciousness_manager.ManagedPerceptionAgent"), \
         patch("api.agents.consciousness_manager.ManagedReasoningAgent"), \
         patch("api.agents.consciousness_manager.ManagedMetacognitionAgent"), \
         patch("api.agents.consciousness_manager.ManagedMarketingStrategist"), \
         patch("api.agents.consciousness_manager.CodeAgent") as MockCodeAgent, \
         patch("api.agents.consciousness_manager.run_agent_with_timeout") as mock_run_agent, \
         patch("api.agents.consciousness_manager.get_worldview_integration_service") as mock_get_worldview, \
         patch("api.agents.consciousness_manager.get_hyper_model_service"), \
         patch("api.agents.consciousness_manager.get_unified_reality_model"), \
         patch("api.agents.consciousness_manager.get_fractal_tracer"):

        # Setup AI Service Mock
        mock_ai_svc = MagicMock()
        mock_get_ai_svc.return_value = mock_ai_svc
        # Force high entropy (criticality breach)
        mock_ai_svc.calculate_uncertainty.return_value = 6.0 # Threshold is 5.0
        
        # Setup Metaplasticity Mock
        mock_get_meta_ctrl.return_value.get_precision.return_value = 1.0
        mock_get_meta_ctrl.return_value.update_belief_dynamic = AsyncMock()
        mock_get_meta_ctrl.return_value.update_precision_from_surprise.return_value = 0.5
        mock_get_meta_ctrl.return_value.calculate_learning_rate.return_value = 0.1
        mock_get_meta_ctrl.return_value.calculate_max_steps.return_value = 10

        # Setup Worldview Service Mock
        mock_worldview = MagicMock()
        mock_get_worldview.return_value = mock_worldview
        mock_worldview.filter_prediction_by_worldview = AsyncMock(return_value={
            "flagged_for_review": False,
            "final_confidence": 0.1,
            "alignment_score": 1.0
        })
        mock_worldview.record_prediction_error = AsyncMock()

        # Setup Orchestrator Result
        mock_run_agent.return_value = json.dumps({
            "reasoning": "Test reasoning",
            "actions": [],
            "confidence": 0.1 # Low confidence -> High Entropy
        })

        # Initialize Manager
        manager = ConsciousnessManager()
        manager._entered = True 
        manager.orchestrator = MockCodeAgent()
        
        # Manually mock the _reasoning_managed toolset to avoid attribute errors
        mock_reasoning = MagicMock()
        mock_reasoning.tools = {}
        manager._reasoning_managed = mock_reasoning
        
        # Run OODA Cycle
        initial_context = {
            "task": "Test Task", 
            "bootstrap_recall": False,
            "meta_learning_enabled": False
        }
        
        # We need to bypass some complex init logic in _run_ooda_cycle
        # But we want to hit the Criticality Check block.
        # We'll mock the internal methods that might fail.
        manager._check_prior_constraints = AsyncMock()
        manager._check_prior_constraints.return_value = {"permitted": True}
        manager._fetch_biographical_context = AsyncMock()
        manager._fetch_biographical_context.return_value = None
        
        with patch("api.services.cognitive_meta_coordinator.get_meta_coordinator") as mock_coord_getter:
             mock_coord = MagicMock()
             mock_coord_getter.return_value = mock_coord
             mock_plan = MagicMock()
             mock_plan.mode.value = "fast"
             mock_plan.afforded_tools = []
             mock_plan.enforce_checklist = False
             
             mock_coord.coordinate = AsyncMock(return_value=mock_plan)
             
             await manager._run_ooda_cycle(initial_context)

        # Verification
        # 1. Check if calculate_uncertainty was called
        mock_ai_svc.calculate_uncertainty.assert_called_once()
        
        # 2. Check if System State was set to CRITICAL
        assert initial_context.get("system_state") == "CRITICAL"

@pytest.mark.asyncio
async def test_criticality_trigger_low_entropy():
    # Same setup but low entropy
     with patch("api.agents.consciousness_manager.get_active_inference_service") as mock_get_ai_svc, \
         patch("api.agents.consciousness_manager.get_metaplasticity_controller") as mock_get_meta_ctrl, \
         patch("api.agents.consciousness_manager.get_meta_learner"), \
         patch("api.agents.consciousness_manager.get_particle_store"), \
         patch("api.agents.consciousness_manager.BootstrapRecallService"), \
         patch("api.agents.consciousness_manager.ManagedPerceptionAgent"), \
         patch("api.agents.consciousness_manager.ManagedReasoningAgent"), \
         patch("api.agents.consciousness_manager.ManagedMetacognitionAgent"), \
         patch("api.agents.consciousness_manager.ManagedMarketingStrategist"), \
         patch("api.agents.consciousness_manager.CodeAgent") as MockCodeAgent, \
         patch("api.agents.consciousness_manager.run_agent_with_timeout") as mock_run_agent, \
         patch("api.agents.consciousness_manager.get_worldview_integration_service") as mock_get_worldview, \
         patch("api.agents.consciousness_manager.get_hyper_model_service"), \
         patch("api.agents.consciousness_manager.get_unified_reality_model"), \
         patch("api.agents.consciousness_manager.get_fractal_tracer"):

        # Setup AI Service Mock
        mock_ai_svc = MagicMock()
        mock_get_ai_svc.return_value = mock_ai_svc
        # Force low entropy (safe state)
        mock_ai_svc.calculate_uncertainty.return_value = 2.0 
        
        # Setup Metaplasticity Mock
        mock_get_meta_ctrl.return_value.get_precision.return_value = 1.0 
        mock_get_meta_ctrl.return_value.update_belief_dynamic = AsyncMock() 
        mock_get_meta_ctrl.return_value.update_precision_from_surprise.return_value = 0.5
        mock_get_meta_ctrl.return_value.calculate_learning_rate.return_value = 0.1
        mock_get_meta_ctrl.return_value.calculate_max_steps.return_value = 10

        # Setup Worldview Service Mock
        mock_worldview = MagicMock()
        mock_get_worldview.return_value = mock_worldview
        mock_worldview.filter_prediction_by_worldview = AsyncMock(return_value={
            "flagged_for_review": False,
            "final_confidence": 0.9,
            "alignment_score": 1.0
        })
        mock_worldview.record_prediction_error = AsyncMock()

        # Setup Orchestrator Result
        mock_run_agent.return_value = json.dumps({
            "reasoning": "Test reasoning",
            "actions": [],
            "confidence": 0.9 
        })

        manager = ConsciousnessManager()
        manager._entered = True 
        manager.orchestrator = MockCodeAgent()
        mock_reasoning = MagicMock()
        mock_reasoning.tools = {}
        manager._reasoning_managed = mock_reasoning

        initial_context = {
            "task": "Test Task", 
            "bootstrap_recall": False,
            "meta_learning_enabled": False
        }
        
        manager._check_prior_constraints = AsyncMock()
        manager._check_prior_constraints.return_value = {"permitted": True}
        manager._fetch_biographical_context = AsyncMock()
        manager._fetch_biographical_context.return_value = None
        
        with patch("api.services.cognitive_meta_coordinator.get_meta_coordinator") as mock_coord_getter:
             mock_coord = MagicMock()
             mock_coord_getter.return_value = mock_coord
             mock_plan = MagicMock()
             mock_plan.mode.value = "fast"
             mock_plan.afforded_tools = []
             mock_plan.enforce_checklist = False
             
             mock_coord.coordinate = AsyncMock(return_value=mock_plan)
             
             await manager._run_ooda_cycle(initial_context)

        # Verification
        mock_ai_svc.calculate_uncertainty.assert_called_once()
        assert initial_context.get("system_state") != "CRITICAL"

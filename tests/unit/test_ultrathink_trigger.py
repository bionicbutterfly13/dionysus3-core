
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from api.agents.consciousness_manager import ConsciousnessManager
from api.models.beautiful_loop import ResonanceSignal, ResonanceMode

@pytest.mark.asyncio
async def test_ultrathink_protocol_injection():
    # Mock dependencies
    with patch("api.services.llm_service.get_router_model"), \
         patch("api.services.bootstrap_recall_service.BootstrapRecallService"), \
         patch("api.agents.consciousness_manager.get_metaplasticity_controller") as mock_get_meta_ctrl, \
         patch("api.agents.consciousness_manager.get_meta_learner") as mock_get_meta_learner, \
         patch("api.agents.consciousness_manager.ManagedPerceptionAgent"), \
         patch("api.agents.consciousness_manager.ManagedReasoningAgent"), \
         patch("api.agents.consciousness_manager.ManagedMetacognitionAgent"), \
         patch("api.agents.consciousness_manager.ManagedMarketingStrategist"), \
         patch("api.agents.consciousness_manager.get_hyper_model_service") as mock_hyper, \
         patch("api.agents.consciousness_manager.get_unified_reality_model"), \
         patch("api.agents.consciousness_manager.get_resonance_detector"), \
         patch("api.agents.resource_gate.run_agent_with_timeout") as mock_run_agent:

        # Setup HyperModel mock
        mock_hyper.return_value.forecast_precision_profile.return_value.layer_precisions = {}

        # Setup Metaplasticity mock
        mock_meta_svc = mock_get_meta_ctrl.return_value
        mock_meta_svc.update_precision_from_surprise.return_value = 0.8
        mock_meta_svc.calculate_learning_rate.return_value = 0.1
        mock_meta_svc.calculate_max_steps.return_value = 10
        
        # Setup Meta Learner mock
        mock_learner = mock_get_meta_learner.return_value
        mock_learner.retrieve_relevant_episodes = AsyncMock(return_value=[])
        mock_learner.synthesize_lessons = AsyncMock(return_value="Test lessons")

        # Setup Manager
        manager = ConsciousnessManager()
        manager._entered = True # Bypass context manager
        
        # Setup Reasoning Agent Mock
        manager._reasoning_managed = MagicMock()
        manager._reasoning_managed.tools = {} # Needs to be iterable dict
        
        manager.orchestrator = AsyncMock() # Mock orchestrator to prevent heavy init
        
        # Setup Context with Dissonance
        dissonant_signal = ResonanceSignal(
            mode=ResonanceMode.DISSONANT,
            resonance_score=0.1,
            surprisal=0.9,
            coherence=0.2,
            discovery_urgency=0.9
        )
        
        initial_context = {
            "task": "Test Ultrathink",
            "resonance_signal": dissonant_signal.model_dump(),
            "coordination_plan": {"mode": "standard", "afforded_tools": []} # Mock coord plan
        }
        
        # Mock Meta Coordinator
        with patch("api.services.cognitive_meta_coordinator.get_meta_coordinator") as mock_coord:
             mock_plan = MagicMock()
             mock_plan.mode.value = "standard"
             mock_plan.afforded_tools = []
             mock_plan.enforce_checklist = False
             mock_plan.rationale = "Test"
             
             mock_coord.return_value.coordinate = AsyncMock(return_value=mock_plan)
             
             # Execute
             await manager._run_ooda_cycle(initial_context)
             
        # Verify Prompt Injection
        assert mock_run_agent.called
        args, _ = mock_run_agent.call_args
        prompt = args[1]
        
        assert "PROTOCOL OVERRIDE: ULTRATHINK ACTIVATED" in prompt
        assert "CRITICAL DISSONANCE DETECTED" in prompt
        assert "OVERRIDE BREVITY" in prompt
        assert "MULTI-DIMENSIONAL ANALYSIS" in prompt


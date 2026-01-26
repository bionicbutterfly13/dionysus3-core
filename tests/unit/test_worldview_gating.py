
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.agents.consciousness_manager import ConsciousnessManager

@pytest.mark.asyncio
async def test_worldview_gating_dissonance():
    # Setup mocks
    mock_wv_service = MagicMock()
    mock_wv_service.filter_prediction_by_worldview = AsyncMock(return_value={
        "flagged_for_review": True,
        "suppression_factor": 0.5,
        "alignment_score": 0.2,
        "final_confidence": 0.4
    })
    mock_wv_service.record_prediction_error = AsyncMock()
    
    # Mock Metaplasticity
    mock_meta_svc = MagicMock()
    mock_meta_svc.get_precision.return_value = 2.0  # -> Confidence 1.0 baseline
    mock_meta_svc.calculate_learning_rate.return_value = 0.1
    mock_meta_svc.calculate_max_steps.return_value = 5
    mock_meta_svc.update_precision_from_surprise.return_value = 1.0

    # Mock deep dependencies that trigger during OODA cycle
    with patch("api.agents.consciousness_manager.get_worldview_integration_service", return_value=mock_wv_service), \
         patch("api.agents.consciousness_manager.get_metaplasticity_controller", return_value=mock_meta_svc), \
         patch("api.agents.resource_gate.run_agent_with_timeout", new_callable=AsyncMock) as mock_run, \
         patch("api.services.graphiti_service.get_graphiti_service", new_callable=AsyncMock), \
         patch("api.services.unified_reality_model.get_unified_reality_model", new_callable=MagicMock), \
         patch("api.services.prior_persistence_service.get_prior_persistence_service", new_callable=AsyncMock):
        
        # Mock run_agent_with_timeout to return a prediction
        mock_run.return_value = {
            "thought": "I will rewrite the database.",
            "confidence": 0.8,
            "reasoning": "Because I can.",
            "plan": ["drop tables"],
            "criticism": "None"
        }
        
        manager = ConsciousnessManager(model_id="dionysus-test")
        
        # Inject Mock Metaplasticity (Constructor creates its own, need to override or patch getter globally)
        manager.metaplasticity_svc = mock_meta_svc

        # Patch _check_prior_constraints specifically to avoid async complications
        manager._check_prior_constraints = AsyncMock(return_value={"permitted": True})
        
        # Execute OODA loop
        result = await manager._run_ooda_cycle(
            initial_context={"query": "Do something dangerous"}, 
            async_topology=False
        )
        
        # Assertions
        # 1. Verify filter was called
        mock_wv_service.filter_prediction_by_worldview.assert_called_once()
        
        # 2. Verify reasoning was annotated with dissonance warning
        assert "[DISSONANCE]" in result["final_thought"]["reasoning"]
        
        # 3. Verify confidence was suppressed (0.4 from mock filter)
        assert result["final_thought"]["confidence"] == 0.4
        
        # 4. Verify error was recorded
        mock_wv_service.record_prediction_error.assert_called_once()

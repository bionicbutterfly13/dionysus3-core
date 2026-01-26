import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from api.agents.consciousness_manager import ConsciousnessManager
from api.services.particle_store import get_particle_store, ParticleStore

@pytest.mark.asyncio
async def test_particle_flow_integration():
    """
    Verify Feature 040:
    1. OODA Loop generates a thought.
    2. Thought is converted to MetacognitiveParticle.
    3. Particle is stored in Working Memory.
    4. IF resonant, Particle is persisted to Graphiti.
    """
    
    # 1. Setup Mocks
    mock_graphiti = AsyncMock()
    mock_meta_svc = MagicMock()
    mock_meta_svc.get_precision.return_value = 4.0 # High precision
    
    # Mock Worldview (since we enabled it)
    mock_wv_svc = AsyncMock()
    mock_wv_svc.filter_prediction_by_worldview.return_value = {
        "flagged_for_review": False, 
        "final_confidence": 0.9, # High confidence -> High resonance -> Persistence
        "alignment_score": 1.0
    }
    
    # Mock Agent Execution
    mock_run = AsyncMock(return_value={
        "thought": "Integration Test",
        "reasoning": "I am testing the particle flow.",
        "confidence": 0.9,
        "plan": []
    })
    
    # 2. Patch dependencies
    with patch("api.agents.consciousness_manager.get_graphiti_service", new_callable=AsyncMock) as get_graphiti, \
         patch("api.services.particle_store.get_graphiti_service", return_value=mock_graphiti), \
         patch("api.agents.consciousness_manager.get_metaplasticity_controller", return_value=mock_meta_svc), \
         patch("api.agents.consciousness_manager.get_worldview_integration_service", return_value=mock_wv_svc), \
         patch("api.agents.resource_gate.run_agent_with_timeout", mock_run), \
         patch("api.services.unified_reality_model.get_unified_reality_model", new_callable=MagicMock), \
         patch("api.services.prior_persistence_service.get_prior_persistence_service", new_callable=AsyncMock):
        
        # Reset Particle Store singleton for clean test
        store = get_particle_store()
        store._particles = []
        store._graphiti = mock_graphiti
        
        manager = ConsciousnessManager(model_id="test")
        manager.metaplasticity_svc = mock_meta_svc
        manager.particle_store = store # Inject store
        
        # Bypass lengthy prior checks
        manager._check_prior_constraints = AsyncMock(return_value={"permitted": True})
        
        # 3. Execute
        await manager._run_ooda_cycle(
            initial_context={"query": "Test Flow", "session_id": "integration-test-session"}, 
            async_topology=False
        )
        
        # 4. Verify Memory (Working Memory)
        active_particles = store.get_active_particles()
        assert len(active_particles) == 1
        p = active_particles[0]
        assert p.content == "I am testing the particle flow."
        assert p.precision == 4.0
        assert p.resonance_score == 0.9
        assert p.context_id == "integration-test-session"
        
        # 5. Verify Persistence (Graphiti)
        # Since resonance 0.9 > 0.8 threshold, it should have persisted
        mock_graphiti.add_node.assert_called_once()
        call_args = mock_graphiti.add_node.call_args[0][0]
        assert call_args["type"] == "MetacognitiveParticle"
        assert call_args["res_score"] == 0.9

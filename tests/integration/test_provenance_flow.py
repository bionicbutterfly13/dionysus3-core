import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.agents.consciousness_manager import ConsciousnessManager
from api.services.particle_store import get_particle_store

@pytest.mark.asyncio
async def test_provenance_flow():
    """
    Verify Feature 041:
    Provenance IDs passed from Reasoning -> Particle -> Graphiti Payload.
    """
    # 1. Setup Mocks
    mock_graphiti = AsyncMock()
    
    import json
    # Reasoning Result WITH provenance (Must be a JSON string as per OODA expectation)
    mock_run = AsyncMock(return_value=json.dumps({
        "thought": "Provenance Test",
        "reasoning": "Derived from Node A and Node B",
        "confidence": 0.95,
        "provenance_ids": ["node-a-uuid", "node-b-uuid"] # <--- The Inlet
    }))
    
    mock_meta_svc = MagicMock()
    mock_meta_svc.get_precision.return_value = 4.5
    
    mock_wv_svc = AsyncMock()
    mock_wv_svc.filter_prediction_by_worldview.return_value = {
        "flagged_for_review": False, 
        "final_confidence": 0.95,
        "alignment_score": 1.0
    }
    
    # Mock Bootstrap to avoid ENV checks
    mock_bootstrap = MagicMock()
    # recall_context must be awaitable and return object with attributes
    recall_result = MagicMock()
    recall_result.formatted_context = "Mock Context"
    mock_bootstrap.recall_context = AsyncMock(return_value=recall_result)

    # Mock MetaLearner
    mock_meta_learner = MagicMock()
    mock_meta_learner.retrieve_relevant_episodes = AsyncMock(return_value=[])

    # 2. Patch
    with patch("api.services.particle_store.get_graphiti_service", return_value=mock_graphiti), \
         patch("api.agents.consciousness_manager.get_metaplasticity_controller", return_value=mock_meta_svc), \
         patch("api.agents.consciousness_manager.get_meta_learner", return_value=mock_meta_learner), \
         patch("api.agents.consciousness_manager.get_worldview_integration_service", return_value=mock_wv_svc), \
         patch("api.agents.resource_gate.run_agent_with_timeout", mock_run), \
         patch("api.agents.consciousness_manager.BootstrapRecallService", return_value=mock_bootstrap), \
         patch("api.agents.consciousness_manager.get_worldview_integration_service", return_value=mock_wv_svc), \
         patch("api.agents.resource_gate.run_agent_with_timeout", mock_run), \
         patch("api.services.unified_reality_model.get_unified_reality_model", new_callable=MagicMock), \
         patch("api.services.prior_persistence_service.get_prior_persistence_service", new_callable=AsyncMock):

        store = get_particle_store()
        store._particles = []
        store._graphiti = mock_graphiti
        
        manager = ConsciousnessManager(model_id="test")
        manager.metaplasticity_svc = mock_meta_svc
        manager.particle_store = store
        manager._check_prior_constraints = AsyncMock(return_value={"permitted": True})
        
        # 3. Execute
        await manager._run_ooda_cycle(
            initial_context={"query": "Provenance?"}, 
            async_topology=False
        )
        
        # 4. Verify Outlet (Graphiti Payload)
        # Check call args to add_node
        mock_graphiti.add_node.assert_called_once()
        node_payload = mock_graphiti.add_node.call_args[0][0]
        
        assert node_payload["type"] == "MetacognitiveParticle"
        assert node_payload["provenance"] == ["node-a-uuid", "node-b-uuid"]
        assert node_payload["res_score"] == 0.95

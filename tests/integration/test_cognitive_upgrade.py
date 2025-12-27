import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.agents.consciousness_manager import ConsciousnessManager
from api.models.bootstrap import BootstrapResult

@pytest.mark.asyncio
async def test_efe_driven_exploration_pivot():
    """T021: Verify that high uncertainty (EFE) triggers epistemic (research) behavior."""
    
    # Setup high uncertainty scenario
    with patch("api.services.efe_engine.EFEEngine.calculate_efe") as mock_efe, \
         patch("api.agents.consciousness_manager.BootstrapRecallService.recall_context", new_callable=AsyncMock) as mock_recall, \
         patch("smolagents.CodeAgent.run") as mock_run:
        
        # 1. Mock high EFE (uncertainty=0.9)
        mock_efe.return_value = MagicMock(dominant_seed_id="research_task")
        
        # 2. Mock recall result
        mock_recall.return_value = BootstrapResult(
            formatted_context="## Past Context\n- Found relevant info",
            source_count=1,
            summarized=False,
            latency_ms=5.0
        )
        
        mock_run.return_value = '{"reasoning": "Uncertainty high, pivoting to research", "actions": [{"action": "recall", "params": {"query": "context"}}] }'
        
        manager = ConsciousnessManager()
        initial_context = {
            "project_id": "dionysus-core",
            "task": "Perform complex unknown operation",
            "bootstrap_recall": True
        }
        
        result = await manager.run_ooda_cycle(initial_context)
        
        # Verify result contains the research action
        assert "actions" in result
        assert any(a["action"] == "recall" for a in result["actions"])
        assert "final_plan" in result

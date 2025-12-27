import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.agents.consciousness_manager import ConsciousnessManager
from api.models.bootstrap import BootstrapResult

@pytest.mark.asyncio
async def test_bootstrap_ooda_flow_injection():
    """T014: Integration test verifying bootstrap context injection into OODA loop."""
    
    # Mock result
    mock_result = BootstrapResult(
        formatted_context="## Past Context\n- Mocked memory",
        source_count=1,
        summarized=False,
        latency_ms=10.0
    )
    
    # We need to mock the internal orchestrator.run to avoid actual LLM calls
    with patch("api.agents.consciousness_manager.BootstrapRecallService.recall_context", new_callable=AsyncMock) as mock_recall, \
         patch("smolagents.CodeAgent.run") as mock_run:
        
        mock_recall.return_value = mock_result
        mock_run.return_value = "OODA result"
        
        manager = ConsciousnessManager()
        initial_context = {
            "project_id": "test-integration",
            "task": "test task"
        }
        
        await manager.run_ooda_cycle(initial_context)
        
        # Verify recall was called
        mock_recall.assert_called_once()
        args, kwargs = mock_recall.call_args
        assert kwargs["project_id"] == "test-integration"
        assert kwargs["query"] == "test task"
        
        # Verify it was injected into initial_context (which was passed to orchestrator prompt builder)
        assert initial_context["bootstrap_past_context"] == "## Past Context\n- Mocked memory"
        
        # Verify orchestrator was called with a prompt containing our injection marker
        prompt_arg = mock_run.call_args[0][0]
        assert "bootstrap_past_context" in prompt_arg

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from api.agents.audit import AgentAuditCallback, get_audit_callback
from smolagents.memory import ActionStep

@pytest.mark.asyncio
async def test_audit_callback_on_step():
    """Verify that the audit callback correctly forwards steps to the webhook."""
    audit = AgentAuditCallback(webhook_url="http://mock-n8n/step", project_id="test-proj")
    
    # Mock the internal _send_payload method
    with patch.object(audit, "_send_payload", new_callable=AsyncMock) as mock_send:
        # Create a mock step
        mock_step = MagicMock(spec=ActionStep)
        mock_step.step_number = 1
        mock_step.tool_calls = []
        mock_step.observation = "Tool finished"
        mock_step.error = None
        
        await audit.on_step(mock_step, agent_name="test_agent", trace_id="trace-123")
        
        # Verify background task was created
        # In a real run, create_task is called. We need to wait or mock it.
        # Since I patched _send_payload, I can check if it was called if I use await or similar.
        
        # Give it a tiny bit of time for the background task to run
        await asyncio.sleep(0.1)
        
        mock_send.assert_called_once()
        payload = mock_send.call_args[0][0]
        assert payload["agent_name"] == "test_agent"
        assert payload["trace_id"] == "trace-123"
        assert payload["step_number"] == 1

def test_audit_registry_generation():
    """Verify that the callback registry is correctly generated for an agent."""
    audit = get_audit_callback()
    registry = audit.get_registry("test_orchestrator", trace_id="trace-456")
    
    assert registry is not None
    # CallbackRegistry should have entries for ActionStep and PlanningStep
    assert ActionStep in registry._callbacks
    assert len(registry._callbacks[ActionStep]) >= 1

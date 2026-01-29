import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.agents.heartbeat_agent import HeartbeatAgent

@pytest.mark.asyncio
async def test_heartbeat_requires_consent():
    """Verify HeartbeatAgent halts if check_consent fails."""
    
    # Mock deps - Patch the SOURCE since it is imported inside the function
    with patch("api.services.hexis_service.get_hexis_service") as mock_get_hexis:
        mock_hexis = AsyncMock()
        mock_get_hexis.return_value = mock_hexis
        
        # Scenario 1: No Consent
        mock_hexis.check_consent.return_value = False
        
        # HeartbeatAgent.__init__ imports get_router_model -> mock it or mock agent entirely
        with patch("api.services.llm_service.get_router_model"), \
             patch("smolagents.MCPClient"), \
             patch("smolagents.ToolCallingAgent"):
             
            agent = HeartbeatAgent()
            # Force agent.agent to present to skip context manager path if desired, 
            # OR just run _run_decide directly if possible. 
            # Since check is in _run_decide, we can test that directly if we mock the agent.
            agent.agent = AsyncMock() 
            
            result = await agent._run_decide({"agent_id": "test_agent"})
            
            assert "HEXIS_CONSENT_REQUIRED" in result
            mock_hexis.check_consent.assert_called_with("test_agent")

@pytest.mark.asyncio
async def test_heartbeat_proceeds_with_consent():
    """Verify HeartbeatAgent proceeds if consent exists."""
    with patch("api.services.hexis_service.get_hexis_service") as mock_get_hexis:
        mock_hexis = AsyncMock()
        mock_get_hexis.return_value = mock_hexis
        mock_hexis.check_consent.return_value = True
        
        with patch("api.services.llm_service.get_router_model"), \
             patch("smolagents.MCPClient"), \
             patch("smolagents.ToolCallingAgent"), \
             patch("api.agents.resource_gate.run_agent_with_timeout", new=AsyncMock(return_value="Action Planned")) as mock_run:
             
             agent = HeartbeatAgent()
             agent.agent = AsyncMock()
             
             # Also mock ManagedMetacognitionAgent context manager
             # We need it to return an object that HAS arbitrate_decision and IS awaitable
             mock_managed_instance = MagicMock()
             mock_managed_instance.arbitrate_decision = AsyncMock(return_value={"use_s2": False, "reason": "Simple task"})
             mock_managed_instance.__enter__.return_value = mock_managed_instance
             mock_managed_instance.__exit__.return_value = None
             
             with patch("api.agents.managed.metacognition.ManagedMetacognitionAgent", return_value=mock_managed_instance):
                 result = await agent._run_decide({"agent_id": "test_agent"})
                 
                 assert "Action Planned" in result
                 assert "SYSTEM 1 ACCEPTED" in result

@pytest.mark.asyncio
async def test_heartbeat_blocks_on_boundary_violation():
    """Verify HeartbeatAgent blocks actions that violate Hexis boundaries."""
    with patch("api.services.hexis_service.get_hexis_service") as mock_get_hexis:
        mock_hexis = AsyncMock()
        mock_get_hexis.return_value = mock_hexis
        mock_hexis.check_consent.return_value = True
        mock_hexis.get_boundaries.return_value = ["regex:delete\\s+.*data"]
        mock_hexis.check_action_against_boundaries.return_value = MagicMock(
            permitted=False,
            reason="Boundary violation: delete data"
        )

        with patch("api.services.llm_service.get_router_model"), \
             patch("smolagents.MCPClient"), \
             patch("smolagents.ToolCallingAgent"), \
             patch("api.agents.resource_gate.run_agent_with_timeout", new=AsyncMock(return_value="Delete all data now.")):

            agent = HeartbeatAgent()
            agent.agent = AsyncMock()

            result = await agent._run_decide({"agent_id": "test_agent"})

            assert "HEXIS_BOUNDARY_VIOLATION" in result
            mock_hexis.check_action_against_boundaries.assert_called()

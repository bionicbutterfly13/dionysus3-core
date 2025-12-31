import pytest
from smolagents import CodeAgent, ToolCallingAgent
from api.agents.perception_agent import PerceptionAgent
from api.agents.reasoning_agent import ReasoningAgent
from api.agents.metacognition_agent import MetacognitionAgent
from api.agents.heartbeat_agent import HeartbeatAgent
from api.agents.consciousness_manager import ConsciousnessManager
from api.agents.managed import (
    ManagedPerceptionAgent,
    ManagedReasoningAgent,
    ManagedMetacognitionAgent,
)


# Mark tests that require MCP server connection
mcp_required = pytest.mark.skipif(
    True,  # Always skip in unit tests - these are integration tests
    reason="Requires MCP server running (move to integration tests)"
)


@mcp_required
def test_agents_are_properly_configured():
    """Verify that all core agents use proper smolagents classes."""
    # All agents are now ToolCallingAgents to support hierarchy/managed_agents securely
    p_agent = PerceptionAgent().__enter__()
    r_agent = ReasoningAgent().__enter__()
    m_agent = MetacognitionAgent().__enter__()
    h_agent = HeartbeatAgent().__enter__()
    cm = ConsciousnessManager().__enter__()

    assert isinstance(p_agent.agent, ToolCallingAgent)
    assert isinstance(r_agent.agent, ToolCallingAgent)
    assert isinstance(m_agent.agent, ToolCallingAgent)
    assert isinstance(h_agent.agent, ToolCallingAgent)
    # Feature 039: Orchestrator is now CodeAgent for native multi-agent orchestration
    assert isinstance(cm.orchestrator, CodeAgent)

    # Clean up
    p_agent.close()
    r_agent.close()
    m_agent.close()
    h_agent.close()
    cm.close()


@mcp_required
def test_managed_agent_wrappers():
    """Verify ManagedAgent wrappers produce valid ToolCallingAgent instances.

    Note: smolagents 1.23+ removed ManagedAgent class. Wrappers now return
    ToolCallingAgent directly with name/description set.
    """
    perception = ManagedPerceptionAgent()
    reasoning = ManagedReasoningAgent()
    metacognition = ManagedMetacognitionAgent()

    with perception, reasoning, metacognition:
        p_agent = perception.get_managed()
        r_agent = reasoning.get_managed()
        m_agent = metacognition.get_managed()

        # Verify ToolCallingAgent type (smolagents 1.23+)
        assert isinstance(p_agent, ToolCallingAgent)
        assert isinstance(r_agent, ToolCallingAgent)
        assert isinstance(m_agent, ToolCallingAgent)

        # Verify names match OODA phases
        assert p_agent.name == "perception"
        assert r_agent.name == "reasoning"
        assert m_agent.name == "metacognition"

        # Verify descriptions are populated (from inner agents)
        assert p_agent.description is not None and len(p_agent.description) > 10
        assert r_agent.description is not None and len(r_agent.description) > 10
        assert m_agent.description is not None and len(m_agent.description) > 10


@mcp_required
def test_consciousness_manager_uses_managed_agents():
    """Verify ConsciousnessManager properly integrates managed agent wrappers.

    Note: smolagents 1.23+ stores managed_agents as dict keyed by name.
    """
    cm = ConsciousnessManager()

    with cm:
        # Verify orchestrator has managed_agents configured
        assert cm.orchestrator is not None
        assert hasattr(cm.orchestrator, 'managed_agents')
        # smolagents 1.23+: managed_agents is a dict
        assert isinstance(cm.orchestrator.managed_agents, dict)
        assert len(cm.orchestrator.managed_agents) == 3

        # Verify managed agent names (keys in dict)
        agent_names = set(cm.orchestrator.managed_agents.keys())
        assert agent_names == {"perception", "reasoning", "metacognition"}

        # Verify all are ToolCallingAgent instances
        for name, agent in cm.orchestrator.managed_agents.items():
            assert isinstance(agent, ToolCallingAgent), f"{name} should be ToolCallingAgent"

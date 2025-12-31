import pytest
from smolagents import CodeAgent, ToolCallingAgent, ManagedAgent
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


def test_managed_agent_wrappers():
    """Verify ManagedAgent wrappers produce valid ManagedAgent instances."""
    perception = ManagedPerceptionAgent()
    reasoning = ManagedReasoningAgent()
    metacognition = ManagedMetacognitionAgent()

    with perception, reasoning, metacognition:
        p_managed = perception.get_managed()
        r_managed = reasoning.get_managed()
        m_managed = metacognition.get_managed()

        # Verify ManagedAgent type
        assert isinstance(p_managed, ManagedAgent)
        assert isinstance(r_managed, ManagedAgent)
        assert isinstance(m_managed, ManagedAgent)

        # Verify names match OODA phases
        assert p_managed.name == "perception"
        assert r_managed.name == "reasoning"
        assert m_managed.name == "metacognition"

        # Verify descriptions are populated
        assert "OBSERVE" in p_managed.description
        assert "ORIENT" in r_managed.description
        assert "DECIDE" in m_managed.description

        # Verify underlying agents are ToolCallingAgent
        assert isinstance(p_managed.agent, ToolCallingAgent)
        assert isinstance(r_managed.agent, ToolCallingAgent)
        assert isinstance(m_managed.agent, ToolCallingAgent)


def test_consciousness_manager_uses_managed_agents():
    """Verify ConsciousnessManager properly integrates ManagedAgent wrappers."""
    cm = ConsciousnessManager()

    with cm:
        # Verify orchestrator has managed_agents configured
        assert cm.orchestrator is not None
        assert hasattr(cm.orchestrator, 'managed_agents')
        assert len(cm.orchestrator.managed_agents) == 3

        # Verify managed agent names
        agent_names = {ma.name for ma in cm.orchestrator.managed_agents}
        assert agent_names == {"perception", "reasoning", "metacognition"}

        # Verify all are ManagedAgent instances
        for ma in cm.orchestrator.managed_agents:
            assert isinstance(ma, ManagedAgent)

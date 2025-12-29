import pytest
from smolagents import CodeAgent, ToolCallingAgent
from api.agents.perception_agent import PerceptionAgent
from api.agents.reasoning_agent import ReasoningAgent
from api.agents.metacognition_agent import MetacognitionAgent
from api.agents.heartbeat_agent import HeartbeatAgent
from api.agents.consciousness_manager import ConsciousnessManager

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
    assert isinstance(cm.orchestrator, ToolCallingAgent)
    
    # Clean up
    p_agent.close()
    r_agent.close()
    m_agent.close()
    h_agent.close()
    cm.close()

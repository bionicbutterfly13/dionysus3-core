"""
Dionysus Agents Module

Smolagents-based cognitive agents for the heartbeat decision system.
"""

from api.agents.heartbeat_agent import HeartbeatAgent
from api.agents.perception_agent import PerceptionAgent
from api.agents.reasoning_agent import ReasoningAgent
from api.agents.metacognition_agent import MetacognitionAgent
from api.agents.consciousness_manager import ConsciousnessManager
from api.agents.decision_adapter import (
    AgentDecisionAdapter,
    AgentDecisionConfig,
    get_agent_decision_adapter,
)
# Feature 039: ManagedAgent wrappers for multi-agent orchestration
from api.agents.managed import (
    ManagedPerceptionAgent,
    ManagedReasoningAgent,
    ManagedMetacognitionAgent,
)

__all__ = [
    "HeartbeatAgent",
    "PerceptionAgent",
    "ReasoningAgent",
    "MetacognitionAgent",
    "ConsciousnessManager",
    "AgentDecisionAdapter",
    "AgentDecisionConfig",
    "get_agent_decision_adapter",
    # Feature 039: ManagedAgent wrappers
    "ManagedPerceptionAgent",
    "ManagedReasoningAgent",
    "ManagedMetacognitionAgent",
]

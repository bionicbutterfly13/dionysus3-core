# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Managed Perception Agent (Feature 039, T008)

ManagedAgent wrapper for the OBSERVE phase of the OODA loop.
Gathers environmental context, recalls relevant memories, and
captures experiential state via MOSAEIC.

The manager agent delegates to this agent when it needs to:
- Observe the current environment state
- Recall memories relevant to the current context
- Capture the user's experiential state (MOSAEIC)
- Query the wisdom graph for strategic principles
"""

import logging
from typing import Optional

from smolagents import ToolCallingAgent

from api.agents.perception_agent import PerceptionAgent

logger = logging.getLogger("dionysus.agents.managed.perception")


class ManagedPerceptionAgent:
    """
    ManagedAgent wrapper for PerceptionAgent.

    Provides a ToolCallingAgent instance that the ConsciousnessManager
    can use for native smolagents multi-agent orchestration during the OBSERVE phase.
    
    Note: smolagents 1.23+ removed ManagedAgent class. Agents with name/description
    are passed directly to managed_agents parameter.
    """

    # Description used by the manager to decide when to delegate
    DESCRIPTION = """OBSERVE phase specialist for the OODA cognitive loop.

Capabilities:
- observe_environment: Gather current environmental context and state
- semantic_recall: Retrieve memories relevant to the current situation
- mosaeic_capture: Capture experiential state (Senses, Actions, Emotions, Impulses, Cognitions)
- query_wisdom: Access strategic principles from the wisdom graph

Use this agent when you need to:
1. Understand the current situation before reasoning
2. Recall past experiences or knowledge relevant to the task
3. Capture the user's current mental/emotional state
4. Ground decisions in stored wisdom and principles

This agent should be called FIRST in most cognitive cycles to establish
situational awareness before reasoning or decision-making."""

    def __init__(self, model_id: str = "dionysus-agents"):
        """
        Initialize the managed perception agent.

        Args:
            model_id: Model identifier for LiteLLM routing
        """
        self.model_id = model_id
        self._inner: Optional[PerceptionAgent] = None
        self._agent: Optional[ToolCallingAgent] = None

    def _ensure_initialized(self) -> PerceptionAgent:
        """Lazily initialize the inner agent."""
        if self._inner is None:
            self._inner = PerceptionAgent(self.model_id)
        return self._inner

    def get_managed(self) -> ToolCallingAgent:
        """
        Get the ToolCallingAgent for use in multi-agent orchestration.

        Returns:
            ToolCallingAgent instance with name and description set
        """
        if self._agent is not None:
            return self._agent

        inner = self._ensure_initialized()

        # Enter context to get the configured agent
        with inner as configured:
            # smolagents 1.23+: agents have name/description directly
            self._agent = configured.agent
            logger.debug("Retrieved ToolCallingAgent for perception")
            return self._agent

    @property
    def agent(self) -> Optional[ToolCallingAgent]:
        """Direct access to underlying agent for callback configuration."""
        return self._agent

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._inner is not None:
            self._inner.__exit__(exc_type, exc_val, exc_tb)
        return False

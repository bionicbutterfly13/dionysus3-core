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

from smolagents import ManagedAgent

from api.agents.perception_agent import PerceptionAgent

logger = logging.getLogger("dionysus.agents.managed.perception")


class ManagedPerceptionAgent:
    """
    ManagedAgent wrapper for PerceptionAgent.

    Provides a ManagedAgent instance that the ConsciousnessManager
    can use for natural language delegation during the OBSERVE phase.
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
        self._managed: Optional[ManagedAgent] = None

    def _ensure_initialized(self) -> PerceptionAgent:
        """Lazily initialize the inner agent."""
        if self._inner is None:
            self._inner = PerceptionAgent(self.model_id)
        return self._inner

    def get_managed(self) -> ManagedAgent:
        """
        Get the ManagedAgent wrapper for use in multi-agent orchestration.

        Returns:
            ManagedAgent instance wrapping the PerceptionAgent
        """
        if self._managed is not None:
            return self._managed

        inner = self._ensure_initialized()

        # Enter context to get the configured agent
        with inner as configured:
            self._managed = ManagedAgent(
                agent=configured.agent,
                name="perception",
                description=self.DESCRIPTION,
            )
            logger.debug("Created ManagedAgent wrapper for perception")
            return self._managed

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._inner is not None:
            self._inner.__exit__(exc_type, exc_val, exc_tb)
        return False

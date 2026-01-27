# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Managed Metacognition Agent (Feature 039, T008)

ManagedAgent wrapper for the DECIDE phase of the OODA loop.
Reviews goal states, assesses model accuracy, and makes
decisions about next actions and mental model revisions.

The manager agent delegates to this agent when it needs to:
- Review and prioritize goals
- Assess mental model accuracy
- Decide on next actions
- Revise beliefs and models based on evidence
"""

import logging
from typing import Optional

from smolagents import ToolCallingAgent

from api.agents.metacognition_agent import MetacognitionAgent

logger = logging.getLogger("dionysus.agents.managed.metacognition")


class ManagedMetacognitionAgent:
    """
    ManagedAgent wrapper for MetacognitionAgent.

    Provides a ToolCallingAgent instance that the ConsciousnessManager
    can use for native smolagents multi-agent orchestration during the DECIDE phase.
    
    ABM Alignment (Chapter 22, Anderson 2014):
    - Specialization: DECIDE phase expert for goal prioritizing and model evaluation.
    - Local Rules: Implements arbitration rules to decide between System 1 and System 2 reasoning.
    - Adaptation: Revises mental models based on evidence from the environment.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        """
        Initialize the managed metacognition agent.

        Args:
            model_id: Model identifier for LiteLLM routing
        """
        self.model_id = model_id
        self._inner: Optional[MetacognitionAgent] = None
        self._agent: Optional[ToolCallingAgent] = None

    def _ensure_initialized(self) -> MetacognitionAgent:
        """Lazily initialize the inner agent."""
        if self._inner is None:
            self._inner = MetacognitionAgent(self.model_id)
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
            logger.debug("Retrieved ToolCallingAgent for metacognition")
            return self._agent

    @property
    def agent(self) -> Optional[ToolCallingAgent]:
        """Direct access to underlying agent for callback configuration."""
        return self._agent

    async def arbitrate_decision(self, proposal: dict, context: dict) -> dict:
        """
        Proxy call to inner MetacognitionAgent for decision arbitration.
        """
        inner = self._ensure_initialized()
        return await inner.arbitrate_decision(proposal, context)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._inner is not None:
            self._inner.__exit__(exc_type, exc_val, exc_tb)
        return False

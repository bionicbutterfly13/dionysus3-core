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
    
    Note: smolagents 1.23+ removed ManagedAgent class. Agents with name/description
    are passed directly to managed_agents parameter.
    """

    # Description used by the manager to decide when to delegate
    DESCRIPTION = """DECIDE phase specialist for the OODA cognitive loop.

Capabilities:
- list_goals: Review current goals and their priority/status
- update_goal: Modify goal priority, status, or details
- revise_mental_model: Update beliefs based on new evidence
- assess_model_accuracy: Evaluate how well mental models predict reality
- select_action: Choose the best action given current understanding

Use this agent when you need to:
1. Review what goals are active and their priorities
2. Decide what action to take next
3. Update mental models based on prediction errors
4. Reconcile conflicting information or goals

This agent should be called AFTER reasoning to translate understanding
into decisions. It closes the cognitive loop by selecting actions
and updating internal models."""

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

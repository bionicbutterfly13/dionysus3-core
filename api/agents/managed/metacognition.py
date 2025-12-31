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

from smolagents import ManagedAgent

from api.agents.metacognition_agent import MetacognitionAgent

logger = logging.getLogger("dionysus.agents.managed.metacognition")


class ManagedMetacognitionAgent:
    """
    ManagedAgent wrapper for MetacognitionAgent.

    Provides a ManagedAgent instance that the ConsciousnessManager
    can use for natural language delegation during the DECIDE phase.
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
        self._managed: Optional[ManagedAgent] = None

    def _ensure_initialized(self) -> MetacognitionAgent:
        """Lazily initialize the inner agent."""
        if self._inner is None:
            self._inner = MetacognitionAgent(self.model_id)
        return self._inner

    def get_managed(self) -> ManagedAgent:
        """
        Get the ManagedAgent wrapper for use in multi-agent orchestration.

        Returns:
            ManagedAgent instance wrapping the MetacognitionAgent
        """
        if self._managed is not None:
            return self._managed

        inner = self._ensure_initialized()

        # Enter context to get the configured agent
        with inner as configured:
            self._managed = ManagedAgent(
                agent=configured.agent,
                name="metacognition",
                description=self.DESCRIPTION,
            )
            logger.debug("Created ManagedAgent wrapper for metacognition")
            return self._managed

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._inner is not None:
            self._inner.__exit__(exc_type, exc_val, exc_tb)
        return False

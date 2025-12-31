# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Managed Reasoning Agent (Feature 039, T008)

ManagedAgent wrapper for the ORIENT phase of the OODA loop.
Analyzes observations, reflects on patterns, and synthesizes
information to build situational understanding.

The manager agent delegates to this agent when it needs to:
- Analyze observations from the perception phase
- Identify patterns and relationships
- Synthesize information from multiple sources
- Build mental models of the current situation
"""

import logging
from typing import Optional

from smolagents import ManagedAgent

from api.agents.reasoning_agent import ReasoningAgent

logger = logging.getLogger("dionysus.agents.managed.reasoning")


class ManagedReasoningAgent:
    """
    ManagedAgent wrapper for ReasoningAgent.

    Provides a ManagedAgent instance that the ConsciousnessManager
    can use for natural language delegation during the ORIENT phase.
    """

    # Description used by the manager to decide when to delegate
    DESCRIPTION = """ORIENT phase specialist for the OODA cognitive loop.

Capabilities:
- reflect_on_topic: Deep analysis of a topic with multiple perspectives
- synthesize_information: Combine observations into coherent understanding
- identify_patterns: Recognize recurring themes and relationships
- build_mental_model: Create predictive models from observations

Use this agent when you need to:
1. Make sense of observations gathered by the perception agent
2. Identify what the observations mean in context
3. Recognize patterns that inform decision-making
4. Build or update mental models of the situation

This agent should be called AFTER perception to transform raw observations
into actionable understanding. It bridges observation and decision."""

    def __init__(self, model_id: str = "dionysus-agents"):
        """
        Initialize the managed reasoning agent.

        Args:
            model_id: Model identifier for LiteLLM routing
        """
        self.model_id = model_id
        self._inner: Optional[ReasoningAgent] = None
        self._managed: Optional[ManagedAgent] = None

    def _ensure_initialized(self) -> ReasoningAgent:
        """Lazily initialize the inner agent."""
        if self._inner is None:
            self._inner = ReasoningAgent(self.model_id)
        return self._inner

    def get_managed(self) -> ManagedAgent:
        """
        Get the ManagedAgent wrapper for use in multi-agent orchestration.

        Returns:
            ManagedAgent instance wrapping the ReasoningAgent
        """
        if self._managed is not None:
            return self._managed

        inner = self._ensure_initialized()

        # Enter context to get the configured agent
        with inner as configured:
            self._managed = ManagedAgent(
                agent=configured.agent,
                name="reasoning",
                description=self.DESCRIPTION,
            )
            logger.debug("Created ManagedAgent wrapper for reasoning")
            return self._managed

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._inner is not None:
            self._inner.__exit__(exc_type, exc_val, exc_tb)
        return False

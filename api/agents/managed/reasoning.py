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

from smolagents import ToolCallingAgent

from api.agents.reasoning_agent import ReasoningAgent

logger = logging.getLogger("dionysus.agents.managed.reasoning")


class ManagedReasoningAgent:
    """
    ManagedAgent wrapper for ReasoningAgent.

    Provides a ToolCallingAgent instance that the ConsciousnessManager
    can use for native smolagents multi-agent orchestration during the ORIENT phase.
    
    ABM Alignment (Chapter 22, Anderson 2014):
    - Heterogeneity: Specialized reasoning agent with distinct cognitive protocols.
    - Local Rules: Employs 'Checklist-Driven Surgeon' rules for pattern identification.
    - Interaction: Bridges observation data to stable mental models.
    """

    # Description used by the manager to decide when to delegate
    DESCRIPTION = """ORIENT phase specialist for the OODA cognitive loop.
    
    Implements the 'Checklist-Driven Surgeon' protocol for high-accuracy reasoning.

    Capabilities:
    - understand_question: Deconstruct complex problems before solving
    - recall_related: Verify and ground reasoning in analogous solved examples
    - examine_answer: Self-critique and verification of reasoning traces
    - backtracking: Recover from errors by revising approach
    - meta_tot_run: Execute non-linear probabilistic planning (Meta-Tree-of-Thought)
    - reflect_on_topic: Deep analysis of a topic with multiple perspectives
    - identify_patterns: Recognize recurring themes and relationships

    Use this agent when accuracy is critical, when the task is complex/uncertain, 
    or when you need a rigorous verification of a proposed solution.
    It bridges observation and decision by transforming raw data into verified wisdom."""

    def __init__(self, model_id: str = "dionysus-agents"):
        """
        Initialize the managed reasoning agent.

        Args:
            model_id: Model identifier for LiteLLM routing
        """
        self.model_id = model_id
        self._inner: Optional[ReasoningAgent] = None
        self._agent: Optional[ToolCallingAgent] = None

    def _ensure_initialized(self) -> ReasoningAgent:
        """Lazily initialize the inner agent."""
        if self._inner is None:
            self._inner = ReasoningAgent(self.model_id)
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
            logger.debug("Retrieved ToolCallingAgent for reasoning")
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

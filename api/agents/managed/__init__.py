# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Managed Agents Module (Feature 039, T008)

ManagedAgent wrappers for OODA phase agents, enabling native
smolagents multi-agent orchestration via ConsciousnessManager.

Each wrapper:
1. Initializes the underlying ToolCallingAgent
2. Wraps it in a ManagedAgent with descriptive metadata
3. Provides the ManagedAgent to the orchestrating CodeAgent

Usage:
    from api.agents.managed import (
        ManagedPerceptionAgent,
        ManagedReasoningAgent,
        ManagedMetacognitionAgent,
    )

    perception = ManagedPerceptionAgent().get_managed()
    reasoning = ManagedReasoningAgent().get_managed()
    metacognition = ManagedMetacognitionAgent().get_managed()

    manager = CodeAgent(
        tools=[],
        model=model,
        managed_agents=[perception, reasoning, metacognition],
    )
"""

from api.agents.managed.perception import ManagedPerceptionAgent
from api.agents.managed.reasoning import ManagedReasoningAgent
from api.agents.managed.metacognition import ManagedMetacognitionAgent

__all__ = [
    "ManagedPerceptionAgent",
    "ManagedReasoningAgent",
    "ManagedMetacognitionAgent",
]

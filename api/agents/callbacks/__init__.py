# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Agent Callbacks Module (Feature 039)

Type-specific callbacks for smolagents integration with Dionysus consciousness.
Callbacks are registered per step type (PlanningStep, ActionStep) and execute
during agent runs to integrate with IWMT, attractor basins, and memory systems.
"""

from api.agents.callbacks.iwmt_callback import (
    iwmt_coherence_callback,
    get_iwmt_callback,
)
from api.agents.callbacks.basin_callback import (
    basin_activation_callback,
    get_basin_callback,
)
from api.agents.callbacks.memory_callback import (
    memory_pruning_callback,
    get_memory_callback,
)

__all__ = [
    "iwmt_coherence_callback",
    "get_iwmt_callback",
    "basin_activation_callback",
    "get_basin_callback",
    "memory_pruning_callback",
    "get_memory_callback",
]

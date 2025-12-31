# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Memory Pruning Callback (Feature 039, T006)

Dynamically prunes old observations from agent memory to reduce token usage.
Follows the smolagents pattern for memory optimization during long-running
agent cycles (like heartbeats with 10+ steps).

When an ActionStep is processed, this callback:
1. Checks the step number against the memory window
2. Summarizes observations from steps older than the window
3. Preserves tool call metadata while reducing verbose output

This enables efficient multi-step agent runs without context overflow.
"""

import logging
import os
from typing import Any, Callable

from smolagents.memory import ActionStep

logger = logging.getLogger("dionysus.callbacks.memory")

# Number of recent steps to keep full observations for
MEMORY_WINDOW = int(os.getenv("AGENT_MEMORY_WINDOW", "3"))

# Maximum length for summarized observations
SUMMARY_MAX_LENGTH = int(os.getenv("AGENT_SUMMARY_MAX_LENGTH", "150"))


def _summarize_observation(observation: str, step_number: int) -> str:
    """
    Create a summarized version of an observation.
    
    Args:
        observation: The full observation text
        step_number: The step number for reference
        
    Returns:
        Summarized observation string
    """
    if not observation:
        return ""
    
    # Extract first meaningful line and truncate
    lines = observation.strip().split("\n")
    first_line = lines[0][:100] if lines else ""
    
    # Count tool results if present
    result_count = observation.count("Result:")
    
    summary_parts = [f"[STEP {step_number} PRUNED]"]
    
    if result_count > 0:
        summary_parts.append(f"{result_count} tool results")
    
    if first_line:
        summary_parts.append(f'"{first_line}..."')
    
    return " ".join(summary_parts)


def memory_pruning_callback(memory_step: ActionStep, agent: Any) -> None:
    """
    Callback that prunes old observations to save tokens.

    This is the main callback function registered with smolagents.
    It runs during ActionStep execution and summarizes observations
    from steps older than the memory window.

    Feature 039, T007: Integrated with TokenUsageTracker for metrics.

    Args:
        memory_step: The ActionStep being processed
        agent: The smolagents agent instance
    """
    # Feature 039, T007: Get token tracker for this agent
    from api.agents.audit import get_token_tracker

    agent_name = getattr(agent, "name", None) or "unknown"
    tracker = get_token_tracker(agent_name)

    try:
        latest_step = getattr(memory_step, "step_number", 0)

        # Record pre-pruning state for current step
        tracker.record_pre_prune(memory_step)

        if latest_step < MEMORY_WINDOW:
            tracker.record_post_prune(memory_step)
            return  # Not enough steps to prune yet

        # Access agent memory
        memory = getattr(agent, "memory", None)
        if not memory:
            tracker.record_post_prune(memory_step)
            return

        steps = getattr(memory, "steps", [])
        if not steps:
            tracker.record_post_prune(memory_step)
            return

        pruned_count = 0
        original_tokens = 0
        pruned_tokens = 0

        for prev_step in steps:
            if not isinstance(prev_step, ActionStep):
                continue

            prev_number = getattr(prev_step, "step_number", 0)

            # Only prune steps older than window
            if prev_number > latest_step - MEMORY_WINDOW:
                continue

            # Get current observation
            observation = getattr(prev_step, "observations", None)
            if observation is None:
                observation = getattr(prev_step, "observation", None)

            if not observation or len(str(observation)) <= SUMMARY_MAX_LENGTH:
                continue  # Already short enough

            # Track token reduction (rough estimate: 4 chars per token)
            original_tokens += len(str(observation)) // 4

            # Summarize the observation
            summary = _summarize_observation(str(observation), prev_number)
            pruned_tokens += len(summary) // 4

            # Update the step's observation
            if hasattr(prev_step, "observations"):
                prev_step.observations = summary
            elif hasattr(prev_step, "observation"):
                prev_step.observation = summary

            # Also prune observation images if present (for multimodal agents)
            if hasattr(prev_step, "observations_images"):
                prev_step.observations_images = None

            pruned_count += 1

        # Record post-pruning state
        tracker.record_post_prune(memory_step)

        # Log pruning for observability
        if pruned_count > 0:
            reduction = original_tokens - pruned_tokens
            reduction_pct = (reduction / original_tokens * 100) if original_tokens > 0 else 0
            logger.info(
                f"Memory pruned: {pruned_count} steps, "
                f"~{reduction} tokens saved ({reduction_pct:.0f}% reduction) "
                f"(current step {latest_step})"
            )

    except Exception as e:
        # Callback failure should not break agent
        logger.warning(f"Memory pruning callback failed (non-fatal): {e}")


def get_memory_callback() -> Callable:
    """
    Factory function to get the memory pruning callback.
    
    Returns the callback function configured for the current environment.
    """
    return memory_pruning_callback

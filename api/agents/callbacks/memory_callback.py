# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Memory Pruning Callback (Feature 039, T006; Track 099)

Dynamically prunes old observations from agent memory to reduce token usage.
Follows the smolagents pattern for memory optimization during long-running
agent cycles (like heartbeats with 10+ steps).

When an ActionStep is processed, this callback:
1. Checks the step number against the memory window
2. (Track 099) Flushes content we're about to prune to long-term memory via
   MemoryBasinRouter.route_memory, then
3. Summarizes observations from steps older than the window
4. Preserves tool call metadata while reducing verbose output

This enables efficient multi-step agent runs without context overflow.
"""

import asyncio
import logging
import os
from typing import Any, Callable, List, Tuple

from smolagents.memory import ActionStep

logger = logging.getLogger("dionysus.callbacks.memory")

# Number of recent steps to keep full observations for
MEMORY_WINDOW = int(os.getenv("AGENT_MEMORY_WINDOW", "3"))

# Maximum length for summarized observations
SUMMARY_MAX_LENGTH = int(os.getenv("AGENT_SUMMARY_MAX_LENGTH", "150"))

# Track 099: cap size of flush payload to avoid huge route_memory calls
FLUSH_MAX_CHARS = int(os.getenv("AGENT_PRUNE_FLUSH_MAX_CHARS", "15000"))


async def _flush_pruned_steps_to_memory(content: str, agent_name: str) -> None:
    """Route pruned-step content through MemoryBasinRouter (Track 099). Log on failure."""
    try:
        from api.services.memory_basin_router import get_memory_basin_router

        router = get_memory_basin_router()
        await router.route_memory(
            content=content,
            source_id=f"prune_flush:{agent_name}",
        )
        logger.info("Pre-prune memory flush completed for agent %s", agent_name)
    except Exception as e:
        logger.warning("Pre-prune memory flush failed (non-fatal): %s", e)


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

        # Track 099: collect (step, full_observation) for steps we're about to prune
        to_prune: List[Tuple[Any, int, str]] = []
        for prev_step in steps:
            if not isinstance(prev_step, ActionStep):
                continue
            prev_number = getattr(prev_step, "step_number", 0)
            if prev_number > latest_step - MEMORY_WINDOW:
                continue
            ob = getattr(prev_step, "observations", None) or getattr(prev_step, "observation", None)
            if not ob or len(str(ob)) <= SUMMARY_MAX_LENGTH:
                continue
            to_prune.append((prev_step, prev_number, str(ob)))

        # Flush to long-term memory before pruning (fire-and-forget)
        if to_prune:
            parts = [f"[Step {n}]\n{t}" for _, n, t in to_prune]
            flush_content = "\n\n".join(parts)
            if len(flush_content) > FLUSH_MAX_CHARS:
                flush_content = flush_content[:FLUSH_MAX_CHARS] + "\n\n...[truncated]"
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            try:
                asyncio.run_coroutine_threadsafe(
                    _flush_pruned_steps_to_memory(flush_content, agent_name),
                    loop,
                )
            except Exception as e:
                logger.warning("Could not schedule pre-prune flush (non-fatal): %s", e)

        pruned_count = 0
        original_tokens = 0
        pruned_tokens = 0

        for prev_step, prev_number, observation in to_prune:
            original_tokens += len(observation) // 4
            summary = _summarize_observation(observation, prev_number)
            pruned_tokens += len(summary) // 4
            if hasattr(prev_step, "observations"):
                prev_step.observations = summary
            elif hasattr(prev_step, "observation"):
                prev_step.observation = summary
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

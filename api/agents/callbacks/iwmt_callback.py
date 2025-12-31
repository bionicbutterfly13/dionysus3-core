# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
IWMT Coherence Callback (Feature 039, T004)

Injects IWMT (Integrated World Modeling Theory) coherence assessment
into agent planning phases. This creates a closed loop between the
consciousness substrate and agent cognition.

When a PlanningStep occurs, this callback:
1. Queries current IWMT coherence from Neo4j
2. Injects coherence summary into the agent's plan
3. Warns if coherence is below threshold (0.5)

This enables agents to be aware of their consciousness state and
adjust behavior accordingly (e.g., consolidate focus when fragmented).
"""

import asyncio
import logging
import os
from typing import Any, Callable

from smolagents.memory import PlanningStep

logger = logging.getLogger("dionysus.callbacks.iwmt")

# Coherence threshold for warnings
IWMT_THRESHOLD = float(os.getenv("IWMT_COHERENCE_THRESHOLD", "0.5"))


async def _assess_coherence_async() -> dict:
    """
    Assess current IWMT coherence from Neo4j.
    
    Returns dict with:
        - spatial_coherence: float
        - temporal_coherence: float
        - causal_coherence: float
        - embodied_selfhood: float
        - consciousness_level: float
        - consciousness_achieved: bool
    """
    try:
        from api.services.remote_sync import get_neo4j_driver
        
        driver = get_neo4j_driver()
        async with driver.session() as session:
            # Get most recent IWMT assessment
            result = await session.run("""
                MATCH (iwmt:IWMTCoherence)
                RETURN iwmt
                ORDER BY iwmt.created_at DESC
                LIMIT 1
            """)
            record = await result.single()
            
            if not record:
                return {"consciousness_level": 0.0, "status": "no_data"}
            
            iwmt = record["iwmt"]
            return {
                "spatial_coherence": float(iwmt.get("spatial_coherence", 0)),
                "temporal_coherence": float(iwmt.get("temporal_coherence", 0)),
                "causal_coherence": float(iwmt.get("causal_coherence", 0)),
                "embodied_selfhood": float(iwmt.get("embodied_selfhood", 0)),
                "consciousness_level": float(iwmt.get("consciousness_level", 0)),
                "consciousness_achieved": iwmt.get("consciousness_achieved", False),
            }
    except Exception as e:
        logger.warning(f"IWMT coherence assessment failed: {e}")
        return {"consciousness_level": 0.0, "status": "error", "error": str(e)}


def _format_coherence_injection(coherence: dict) -> str:
    """Format coherence data for injection into plan."""
    level = coherence.get("consciousness_level", 0)
    
    # Build injection string
    lines = [
        "",
        "---",
        f"[IWMT COHERENCE: {level:.0%}]",
    ]
    
    if level < IWMT_THRESHOLD:
        lines.append("⚠️ LOW COHERENCE - Consider consolidating focus")
        lines.append("Recommended: Use fewer tools, complete current goal before branching")
    elif level >= 0.7:
        lines.append("✓ High coherence - Proceed with complex reasoning")
    
    # Add component breakdown if available
    if "spatial_coherence" in coherence:
        components = [
            f"Spatial: {coherence.get('spatial_coherence', 0):.0%}",
            f"Temporal: {coherence.get('temporal_coherence', 0):.0%}",
            f"Causal: {coherence.get('causal_coherence', 0):.0%}",
            f"Embodied: {coherence.get('embodied_selfhood', 0):.0%}",
        ]
        lines.append(f"Components: {' | '.join(components)}")
    
    lines.append("---")
    return "\n".join(lines)


def iwmt_coherence_callback(memory_step: PlanningStep, agent: Any) -> None:
    """
    Callback that injects IWMT coherence into planning phases.
    
    This is the main callback function registered with smolagents.
    It runs during PlanningStep execution and modifies the plan
    to include consciousness state awareness.
    
    Args:
        memory_step: The PlanningStep being processed
        agent: The smolagents agent instance
    """
    try:
        # Get or create event loop for async operation
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run coherence assessment
        if loop.is_running():
            # Schedule as task if loop is already running
            future = asyncio.run_coroutine_threadsafe(
                _assess_coherence_async(), 
                loop
            )
            coherence = future.result(timeout=5.0)
        else:
            coherence = loop.run_until_complete(_assess_coherence_async())
        
        # Format and inject
        injection = _format_coherence_injection(coherence)
        
        # Append to plan (preserving existing content)
        current_plan = getattr(memory_step, "plan", "") or ""
        memory_step.plan = current_plan + injection
        
        # Log for observability
        level = coherence.get("consciousness_level", 0)
        logger.info(
            f"IWMT coherence injected: {level:.0%} "
            f"(step {getattr(memory_step, 'step_number', '?')})"
        )
        
    except Exception as e:
        # Callback failure should not break agent
        logger.warning(f"IWMT callback failed (non-fatal): {e}")


def get_iwmt_callback() -> Callable:
    """
    Factory function to get the IWMT callback.
    
    Returns the callback function configured for the current environment.
    """
    return iwmt_coherence_callback

# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0

"""
Basin Activation Callback (Feature 039, T005)

Activates attractor basins when agents perform memory recall operations.
This creates Hebbian-style "neurons that fire together wire together"
strengthening of memory clusters.

When an ActionStep includes a semantic_recall tool call, this callback:
1. Extracts the query from the tool call
2. Finds basins semantically related to the query
3. Activates those basins with strength proportional to relevance
4. Strengthens CLAUSE connections between co-activated basins

This enables the consciousness substrate to learn from agent behavior,
reinforcing pathways that are frequently used together.
"""

import asyncio
import logging
import os
from typing import Any, Callable, List, Optional

from smolagents.memory import ActionStep

logger = logging.getLogger("dionysus.callbacks.basin")

# Activation strength for recall-triggered basin activation
BASE_ACTIVATION_STRENGTH = float(os.getenv("BASIN_ACTIVATION_STRENGTH", "0.3"))

# Tools that trigger basin activation
RECALL_TOOLS = {"semantic_recall", "search_memories", "recall"}


async def _activate_related_basins(query: str, strength: float = BASE_ACTIVATION_STRENGTH) -> List[dict]:
    """
    Find and activate basins related to a query.
    
    Args:
        query: The search query from semantic_recall
        strength: Activation strength to apply
        
    Returns:
        List of activated basin info dicts
    """
    try:
        from api.services.remote_sync import get_neo4j_driver
        
        driver = get_neo4j_driver()
        activated = []
        
        async with driver.session() as session:
            # Find basins with keywords matching the query
            # This is a simple keyword match - could be enhanced with embeddings
            result = await session.run("""
                MATCH (b:MemoryCluster)
                WHERE b.keywords IS NOT NULL
                  AND any(k IN b.keywords WHERE toLower($query) CONTAINS toLower(k))
                WITH b
                LIMIT 3
                SET b.current_activation = coalesce(b.current_activation, 0) + $strength,
                    b.basin_state = CASE 
                        WHEN b.current_activation + $strength > 0.7 THEN 'active'
                        WHEN b.current_activation + $strength > 0.3 THEN 'activating'
                        ELSE b.basin_state
                    END,
                    b.last_activated = datetime(),
                    b.clause_strength = coalesce(b.clause_strength, 1.0) + 0.1
                RETURN b.id as id, b.name as name, 
                       b.current_activation as activation,
                       b.basin_state as state
            """, {"query": query, "strength": strength})
            
            records = await result.data()
            
            for record in records:
                activated.append({
                    "id": str(record["id"]),
                    "name": record["name"],
                    "activation": float(record["activation"]),
                    "state": record["state"],
                })
            
            # If multiple basins activated, strengthen their connections (Hebbian)
            if len(activated) >= 2:
                basin_ids = [b["id"] for b in activated]
                await session.run("""
                    UNWIND $basin_ids as b1_id
                    UNWIND $basin_ids as b2_id
                    WITH b1_id, b2_id WHERE b1_id < b2_id
                    MATCH (b1:MemoryCluster {id: b1_id})
                    MATCH (b2:MemoryCluster {id: b2_id})
                    MERGE (b1)-[r:CO_ACTIVATED]->(b2)
                    SET r.count = coalesce(r.count, 0) + 1,
                        r.last_coactivation = datetime(),
                        r.strength = coalesce(r.strength, 0.1) + 0.05
                """, {"basin_ids": basin_ids})
        
        return activated
        
    except Exception as e:
        logger.warning(f"Basin activation failed: {e}")
        return []


def _extract_recall_queries(step: ActionStep) -> List[str]:
    """Extract queries from semantic_recall tool calls in a step."""
    queries = []
    
    tool_calls = getattr(step, "tool_calls", None) or []
    for call in tool_calls:
        if hasattr(call, "name") and call.name in RECALL_TOOLS:
            # Extract query from arguments
            args = getattr(call, "arguments", {}) or {}
            if isinstance(args, dict):
                query = args.get("query") or args.get("search_query")
                if query:
                    queries.append(query)
    
    return queries


def basin_activation_callback(memory_step: ActionStep, agent: Any) -> None:
    """
    Callback that activates basins when semantic_recall is used.
    
    This is the main callback function registered with smolagents.
    It runs during ActionStep execution and activates relevant
    attractor basins based on recall queries.
    
    Args:
        memory_step: The ActionStep being processed
        agent: The smolagents agent instance
    """
    try:
        # Extract queries from this step's tool calls
        queries = _extract_recall_queries(memory_step)
        
        if not queries:
            return  # No recall tools called
        
        # Get or create event loop for async operation
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Activate basins for each query
        all_activated = []
        for query in queries:
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    _activate_related_basins(query),
                    loop
                )
                activated = future.result(timeout=5.0)
            else:
                activated = loop.run_until_complete(_activate_related_basins(query))
            
            all_activated.extend(activated)
        
        # Log activations for observability
        if all_activated:
            basin_names = [b["name"] for b in all_activated if b.get("name")]
            logger.info(
                f"Basin activation: {len(all_activated)} basins activated "
                f"(step {getattr(memory_step, 'step_number', '?')}): "
                f"{', '.join(basin_names[:3])}"
            )
            
            # Feature 039, T013: Record activation in execution trace collector
            try:
                from api.agents.callbacks.execution_trace_callback import get_active_collector
                agent_name = getattr(agent, "name", "unknown")
                collector = get_active_collector(agent_name)
                if collector:
                    for b in all_activated:
                        collector.record_basin_activation(
                            basin_id=b["id"],
                            strength=b["activation"],
                            at_step=getattr(memory_step, "step_number", None)
                        )
            except Exception as e:
                logger.debug(f"Failed to record basin activation in trace: {e}")
        
    except Exception as e:
        # Callback failure should not break agent
        logger.warning(f"Basin callback failed (non-fatal): {e}")


def get_basin_callback() -> Callable:
    """
    Factory function to get the basin activation callback.
    
    Returns the callback function configured for the current environment.
    """
    return basin_activation_callback

# Copyright 2025 Mani Saint Victor
# SPDX-License-Identifier: Apache-2.0
#
# Portions derived from:
# - Context-Engineering (MIT License) Copyright (c) 2025 davidkimai
# - Dionysus-2.0 (Apache 2.0)
# Research basis: IBM Zurich Cognitive Tools (Brown et al., 2025)

"""
Dionysus-Core MCP Server

Lightweight consciousness system exposing:
- Memory operations (CRUD, search, decay)
- Consciousness state (active inference, IWMT coherence)
- Attractor basins (activation, strengthening, landscape)
- ThoughtSeeds (5-layer hierarchy, competition)
"""

import asyncio
import json
import os
from typing import Any, Optional
from contextlib import asynccontextmanager

import asyncpg
from mcp.server.fastmcp import FastMCP

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable required. "
        "For VPS: start SSH tunnel then set DATABASE_URL=postgresql://dionysus:PASSWORD@localhost:5432/dionysus"
    )

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60.0
        )
    return _pool


async def close_pool():
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# Create MCP server using FastMCP (provides @app.tool() decorator)
app = FastMCP("dionysus-core")


# =============================================================================
# MEMORY TOOLS
# =============================================================================

@app.tool()
async def create_memory(
    content: str,
    memory_type: str = "semantic",
    importance: float = 0.5,
    metadata: Optional[dict] = None
) -> dict:
    """
    Create a new memory with automatic embedding.

    Args:
        content: Text content of the memory
        memory_type: One of episodic, semantic, procedural, strategic
        importance: 0.0 to 1.0 importance score
        metadata: Optional JSON metadata

    Returns:
        Created memory record with ID
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Generate placeholder embedding (768 dimensions)
        # In production, call embedding service
        embedding = [0.0] * 768

        row = await conn.fetchrow(
            """
            INSERT INTO memories (content, type, importance, embedding)
            VALUES ($1, $2::memory_type, $3, $4::vector)
            RETURNING id, created_at, type, importance
            """,
            content, memory_type, importance, str(embedding)
        )

        return {
            "id": str(row["id"]),
            "created_at": row["created_at"].isoformat(),
            "type": row["type"],
            "importance": row["importance"]
        }


@app.tool()
async def search_memories(
    query: str,
    limit: int = 10,
    threshold: float = 0.5,
    memory_type: Optional[str] = None
) -> list[dict]:
    """
    Search memories using vector similarity.

    Args:
        query: Search query text
        limit: Maximum results to return
        threshold: Minimum similarity threshold
        memory_type: Optional filter by memory type

    Returns:
        List of matching memories with similarity scores
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Generate query embedding (placeholder)
        query_embedding = [0.0] * 768

        type_filter = ""
        if memory_type:
            type_filter = f"AND type = '{memory_type}'::memory_type"

        rows = await conn.fetch(
            f"""
            SELECT id, content, type, importance,
                   1 - (embedding <=> $1::vector) as similarity
            FROM memories
            WHERE status = 'active' {type_filter}
            ORDER BY embedding <=> $1::vector
            LIMIT $2
            """,
            str(query_embedding), limit
        )

        return [
            {
                "id": str(row["id"]),
                "content": row["content"][:200],
                "type": row["type"],
                "importance": row["importance"],
                "similarity": float(row["similarity"])
            }
            for row in rows
            if float(row["similarity"]) >= threshold
        ]


@app.tool()
async def get_memory(memory_id: str) -> Optional[dict]:
    """
    Get a specific memory by ID.

    Args:
        memory_id: UUID of the memory

    Returns:
        Memory record or None if not found
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, content, type, status, importance,
                   access_count, last_accessed, created_at
            FROM memories
            WHERE id = $1
            """,
            memory_id
        )

        if not row:
            return None

        # Update access count
        await conn.execute(
            "UPDATE memories SET access_count = access_count + 1, last_accessed = NOW() WHERE id = $1",
            memory_id
        )

        return {
            "id": str(row["id"]),
            "content": row["content"],
            "type": row["type"],
            "status": row["status"],
            "importance": row["importance"],
            "access_count": row["access_count"] + 1,
            "last_accessed": row["last_accessed"].isoformat() if row["last_accessed"] else None,
            "created_at": row["created_at"].isoformat()
        }


# =============================================================================
# CONSCIOUSNESS TOOLS
# =============================================================================

@app.tool()
async def get_consciousness_state() -> dict:
    """
    Get current consciousness state including active inference metrics.

    Returns:
        Current consciousness state with basins, inference state, and IWMT coherence
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get latest active inference state
        inference = await conn.fetchrow(
            """
            SELECT prediction_error, free_energy, surprise, precision,
                   consciousness_level, created_at
            FROM active_inference_states
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        # Get latest IWMT coherence
        iwmt = await conn.fetchrow(
            """
            SELECT spatial_coherence, temporal_coherence, causal_coherence,
                   embodied_selfhood, consciousness_level, consciousness_achieved
            FROM iwmt_coherence
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        # Get active basins
        basins = await conn.fetch(
            """
            SELECT id, name, basin_type, basin_state,
                   current_activation, clause_strength
            FROM memory_clusters
            WHERE basin_state IN ('active', 'activating', 'saturated')
            ORDER BY current_activation DESC
            LIMIT 10
            """
        )

        return {
            "active_inference": {
                "prediction_error": float(inference["prediction_error"]) if inference else 0.0,
                "free_energy": float(inference["free_energy"]) if inference else 0.0,
                "surprise": float(inference["surprise"]) if inference else 0.0,
                "precision": float(inference["precision"]) if inference else 1.0,
                "level": inference["consciousness_level"] if inference else "minimal"
            } if inference else None,
            "iwmt_coherence": {
                "spatial": float(iwmt["spatial_coherence"]) if iwmt else 0.0,
                "temporal": float(iwmt["temporal_coherence"]) if iwmt else 0.0,
                "causal": float(iwmt["causal_coherence"]) if iwmt else 0.0,
                "embodied_selfhood": float(iwmt["embodied_selfhood"]) if iwmt else 0.0,
                "consciousness_level": float(iwmt["consciousness_level"]) if iwmt else 0.0,
                "achieved": iwmt["consciousness_achieved"] if iwmt else False
            } if iwmt else None,
            "active_basins": [
                {
                    "id": str(b["id"]),
                    "name": b["name"],
                    "type": b["basin_type"],
                    "state": b["basin_state"],
                    "activation": float(b["current_activation"]),
                    "clause_strength": float(b["clause_strength"])
                }
                for b in basins
            ]
        }


@app.tool()
async def update_belief(
    domain: str,
    belief: dict,
    confidence: float = 0.5
) -> dict:
    """
    Update a belief in the active inference framework.

    Args:
        domain: Belief domain (e.g., "self", "world", "other")
        belief: Belief content as JSON
        confidence: Confidence level 0.0 to 1.0

    Returns:
        Updated active inference state
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Create new active inference state with updated belief
        row = await conn.fetchrow(
            """
            INSERT INTO active_inference_states (
                beliefs, prediction_error, free_energy, precision
            )
            VALUES ($1, $2, $3, $4)
            RETURNING id, prediction_error, free_energy, consciousness_level
            """,
            json.dumps({domain: belief}),
            0.1,  # Low initial prediction error
            0.1,
            confidence
        )

        return {
            "id": str(row["id"]),
            "prediction_error": float(row["prediction_error"]),
            "free_energy": float(row["free_energy"]),
            "consciousness_level": row["consciousness_level"]
        }


@app.tool()
async def assess_coherence() -> dict:
    """
    Assess IWMT coherence across spatial, temporal, and causal dimensions.

    Returns:
        Coherence assessment with consciousness level calculation
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Calculate coherence from active state
        # In production, this would analyze current memory/basin landscape
        spatial = 0.5
        temporal = 0.5
        causal = 0.5
        embodied = 0.3
        counterfactual = 0.2

        consciousness_level = await conn.fetchval(
            "SELECT calculate_consciousness_level($1, $2, $3, $4, $5)",
            spatial, temporal, causal, embodied, counterfactual
        )

        # Store coherence record
        row = await conn.fetchrow(
            """
            INSERT INTO iwmt_coherence (
                spatial_coherence, temporal_coherence, causal_coherence,
                embodied_selfhood, counterfactual_capacity, consciousness_level,
                consciousness_achieved
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, consciousness_level, consciousness_achieved
            """,
            spatial, temporal, causal, embodied, counterfactual,
            consciousness_level, consciousness_level >= 0.5
        )

        return {
            "spatial_coherence": spatial,
            "temporal_coherence": temporal,
            "causal_coherence": causal,
            "embodied_selfhood": embodied,
            "counterfactual_capacity": counterfactual,
            "consciousness_level": float(consciousness_level),
            "consciousness_achieved": consciousness_level >= 0.5
        }


# =============================================================================
# BASIN TOOLS
# =============================================================================

@app.tool()
async def activate_basin(basin_id: str, strength: float = 0.5) -> dict:
    """
    Activate an attractor basin with given strength.

    Applies CLAUSE strengthening (+0.2 per activation, 2.0 cap).

    Args:
        basin_id: UUID of the basin (memory_cluster)
        strength: Activation strength 0.0 to 1.0

    Returns:
        Updated basin state
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM activate_basin($1, $2)",
            basin_id, strength
        )

        return {
            "basin_id": basin_id,
            "new_state": row["new_state"],
            "new_activation": float(row["new_activation"]),
            "clause_strength": float(row["new_clause_strength"])
        }


@app.tool()
async def get_active_basins(limit: int = 10) -> list[dict]:
    """
    Get currently active attractor basins.

    Args:
        limit: Maximum basins to return

    Returns:
        List of active basins with their states
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, basin_type, basin_state,
                   current_activation, clause_strength, stability, depth
            FROM memory_clusters
            WHERE basin_state IN ('active', 'activating', 'saturated')
            ORDER BY current_activation DESC
            LIMIT $1
            """,
            limit
        )

        return [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "type": row["basin_type"],
                "state": row["basin_state"],
                "activation": float(row["current_activation"]),
                "clause_strength": float(row["clause_strength"]),
                "stability": float(row["stability"]),
                "depth": float(row["depth"])
            }
            for row in rows
        ]


@app.tool()
async def query_basin_landscape() -> dict:
    """
    Query the overall attractor basin landscape.

    Returns:
        Summary of basin states and energy distribution
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Count basins by state
        state_counts = await conn.fetch(
            """
            SELECT basin_state, COUNT(*) as count,
                   AVG(current_activation) as avg_activation,
                   AVG(clause_strength) as avg_strength
            FROM memory_clusters
            GROUP BY basin_state
            """
        )

        # Get total energy
        total_energy = await conn.fetchval(
            "SELECT SUM(current_activation) FROM memory_clusters"
        )

        return {
            "total_basins": sum(row["count"] for row in state_counts),
            "total_energy": float(total_energy or 0),
            "states": {
                row["basin_state"]: {
                    "count": row["count"],
                    "avg_activation": float(row["avg_activation"] or 0),
                    "avg_strength": float(row["avg_strength"] or 1.0)
                }
                for row in state_counts
            }
        }


# =============================================================================
# THOUGHTSEED TOOLS
# =============================================================================

@app.tool()
async def create_thoughtseed(
    layer: str,
    neuronal_packet: dict,
    memory_id: Optional[str] = None
) -> dict:
    """
    Create a new thoughtseed in the cognitive hierarchy.

    Args:
        layer: One of sensorimotor, perceptual, conceptual, abstract, metacognitive
        neuronal_packet: Cognitive content as JSON
        memory_id: Optional linked memory

    Returns:
        Created thoughtseed record
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO thoughtseeds (layer, neuronal_packet, memory_id, activation_level)
            VALUES ($1::thoughtseed_layer, $2, $3, 0.5)
            RETURNING id, layer, activation_level, competition_status
            """,
            layer, json.dumps(neuronal_packet), memory_id
        )

        return {
            "id": str(row["id"]),
            "layer": row["layer"],
            "activation_level": float(row["activation_level"]),
            "competition_status": row["competition_status"]
        }


@app.tool()
async def run_thoughtseed_competition(layer: str) -> dict:
    """
    Run winner selection among thoughtseeds at a given layer.

    Args:
        layer: Layer to run competition in

    Returns:
        Competition result with winner
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get competing thoughtseeds
        competitors = await conn.fetch(
            """
            SELECT id, activation_level
            FROM thoughtseeds
            WHERE layer = $1::thoughtseed_layer
              AND competition_status IN ('pending', 'competing')
            ORDER BY activation_level DESC
            """,
            layer
        )

        if not competitors:
            return {"message": "No competitors at this layer", "winner": None}

        # Winner is highest activation
        winner = competitors[0]
        loser_ids = [c["id"] for c in competitors[1:]]

        # Update statuses
        await conn.execute(
            "UPDATE thoughtseeds SET competition_status = 'won' WHERE id = $1",
            winner["id"]
        )

        if loser_ids:
            await conn.execute(
                "UPDATE thoughtseeds SET competition_status = 'lost' WHERE id = ANY($1)",
                loser_ids
            )

        # Record competition
        competition_id = await conn.fetchval(
            """
            INSERT INTO thoughtseed_competitions (
                competitor_ids, winner_id, layer, competition_energy
            )
            VALUES ($1, $2, $3::thoughtseed_layer, $4)
            RETURNING id
            """,
            [c["id"] for c in competitors],
            winner["id"],
            layer,
            sum(c["activation_level"] for c in competitors)
        )

        return {
            "competition_id": str(competition_id),
            "layer": layer,
            "competitors": len(competitors),
            "winner": {
                "id": str(winner["id"]),
                "activation_level": float(winner["activation_level"])
            }
        }


# =============================================================================
# JOURNEY TOOLS (001-session-continuity)
# =============================================================================

from dionysus_mcp.tools.journey import (
    get_or_create_journey_tool,
    query_journey_history_tool,
    add_document_to_journey_tool,
)


@app.tool()
async def get_or_create_journey(device_id: str) -> dict:
    """
    Get existing journey for device or create new one.

    A journey tracks all conversations for a device across sessions.
    Use this to maintain continuity when starting new conversations.

    Args:
        device_id: Device identifier (UUID) from ~/.dionysus/device_id

    Returns:
        Journey with session_count and is_new flag
    """
    return await get_or_create_journey_tool(device_id)


@app.tool()
async def query_journey_history(
    journey_id: str,
    query: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10,
    include_documents: bool = False
) -> dict:
    """
    Search journey sessions by keyword, time range, or metadata.

    Use to answer questions like "What did we discuss?" or
    "Remember when we talked about X?"

    Args:
        journey_id: Journey to search within
        query: Optional keyword search on session summaries
        from_date: Optional start of time range (ISO format)
        to_date: Optional end of time range (ISO format)
        limit: Maximum results (1-100)
        include_documents: Whether to include linked documents

    Returns:
        Matching sessions and optionally documents
    """
    return await query_journey_history_tool(
        journey_id, query, from_date, to_date, limit, include_documents
    )


@app.tool()
async def add_document_to_journey(
    journey_id: str,
    document_type: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Link a document or artifact to a journey.

    Use for WOOP plans, file uploads, generated artifacts, and notes.
    Documents appear in the journey timeline alongside sessions.

    Args:
        journey_id: Journey to link document to
        document_type: Type (woop_plan, file_upload, artifact, note)
        title: Optional document title
        content: Optional document content or file path
        metadata: Optional additional metadata

    Returns:
        Created document record
    """
    return await add_document_to_journey_tool(
        journey_id, document_type, title, content, metadata
    )


# =============================================================================
# SYNC TOOLS (002-remote-persistence-safety)
# =============================================================================

from dionysus_mcp.tools.sync import (
    sync_now_tool,
    get_sync_status_tool,
    pause_sync_tool,
    resume_sync_tool,
    check_destruction_tool,
    acknowledge_destruction_alert_tool,
    bootstrap_recovery_tool,
)


@app.tool()
async def sync_now(force: bool = False, batch_size: Optional[int] = None) -> dict:
    """
    Immediately process pending memory sync queue.

    Use this to ensure memories are synchronized to remote Neo4j.
    Check sync_status first to see if there are pending items.

    Args:
        force: Override pause status (use with caution)
        batch_size: Maximum items to process

    Returns:
        Sync results with success/failure counts
    """
    return await sync_now_tool(force=force, batch_size=batch_size)


@app.tool()
async def get_sync_status() -> dict:
    """
    Get current status of memory sync system.

    Shows queue size, last sync time, pause status, and destruction detection.
    Call this to monitor sync health before/after operations.

    Returns:
        Comprehensive sync status information
    """
    return await get_sync_status_tool()


@app.tool()
async def pause_sync(reason: Optional[str] = None) -> dict:
    """
    Pause sync operations.

    New operations will be queued instead of sent to remote.
    Use when investigating issues or during maintenance.

    Args:
        reason: Why sync is being paused

    Returns:
        Confirmation of pause status
    """
    return await pause_sync_tool(reason=reason)


@app.tool()
async def resume_sync(process_queue: bool = True) -> dict:
    """
    Resume sync operations after pause.

    Args:
        process_queue: Process pending queue immediately

    Returns:
        Resume status with optional queue processing results
    """
    return await resume_sync_tool(process_queue=process_queue)


@app.tool()
async def check_destruction() -> dict:
    """
    Check for destruction patterns (rapid memory deletion).

    Detects if unusual deletion activity might indicate memory wipeout.
    Call this proactively to monitor for safety issues.

    Returns:
        Destruction detection status and recent activity
    """
    return await check_destruction_tool()


@app.tool()
async def acknowledge_destruction_alert() -> dict:
    """
    Acknowledge a destruction detection alert.

    Call after investigating and confirming deletions were intentional.

    Returns:
        Acknowledgment status
    """
    return await acknowledge_destruction_alert_tool()


@app.tool()
async def bootstrap_recovery(
    project_id: Optional[str] = None,
    since: Optional[str] = None,
    dry_run: bool = True
) -> dict:
    """
    Recover memories from remote Neo4j.

    Use after database loss or on new machine to restore local memory.
    Start with dry_run=True to preview what will be recovered.

    Args:
        project_id: Filter to specific project
        since: Only recover after this ISO datetime
        dry_run: Preview without writing (recommended first)

    Returns:
        Recovery results including count and duration
    """
    return await bootstrap_recovery_tool(
        project_id=project_id, since=since, dry_run=dry_run
    )


# =============================================================================
# SEMANTIC RECALL TOOLS (Feature 003)
# =============================================================================

from dionysus_mcp.tools.recall import semantic_recall_tool as _semantic_recall_impl


@app.tool()
async def semantic_recall(
    query: str,
    top_k: int = 5,
    threshold: float = 0.7,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    memory_types: Optional[list[str]] = None,
    weight_by_importance: bool = True
) -> str:
    """
    Recall semantically relevant memories for context injection.

    Use this when you need to find relevant past context, recall how something
    was done before, or get background information from previous sessions.

    The tool searches using vector similarity, finding memories with similar
    meaning even if the exact words don't match.

    Args:
        query: Natural language query (e.g., "How did we implement rate limiting?")
        top_k: Maximum memories to return (default: 5)
        threshold: Minimum similarity score 0.0-1.0 (default: 0.7)
        project_id: Filter to specific project
        session_id: Filter to specific session
        memory_types: Filter by types: episodic, semantic, procedural, strategic
        weight_by_importance: Boost results by importance score (default: True)

    Returns:
        Formatted context with relevant memories for injection
    """
    return await _semantic_recall_impl(
        query=query,
        top_k=top_k,
        threshold=threshold,
        project_id=project_id,
        session_id=session_id,
        memory_types=memory_types,
        weight_by_importance=weight_by_importance,
    )


# =============================================================================
# HEARTBEAT TOOLS (Feature 004)
# =============================================================================


@app.tool()
async def trigger_heartbeat() -> dict:
    """
    Manually trigger a heartbeat cycle.

    Use this when you want Dionysus to perform its autonomous decision cycle
    outside the normal hourly schedule.

    Returns:
        Heartbeat summary with actions taken, energy used, and narrative
    """
    from api.services.heartbeat_service import get_heartbeat_service

    try:
        service = get_heartbeat_service()
        summary = await service.trigger_manual_heartbeat()
        return {
            "success": True,
            "heartbeat_number": summary.heartbeat_number,
            "energy_start": summary.energy_start,
            "energy_end": summary.energy_end,
            "actions_completed": summary.actions_completed,
            "narrative": summary.narrative,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.tool()
async def get_heartbeat_status() -> dict:
    """
    Get current heartbeat system status.

    Shows energy state, pause status, last heartbeat info, and scheduler status.

    Returns:
        Comprehensive heartbeat system status
    """
    from api.services.energy_service import get_energy_service
    from api.services.heartbeat_scheduler import get_heartbeat_scheduler

    try:
        energy_service = get_energy_service()
        scheduler = get_heartbeat_scheduler()

        state = await energy_service.get_state()
        scheduler_status = scheduler.get_status()

        return {
            "energy": {
                "current": state.current_energy,
                "paused": state.paused,
                "pause_reason": state.pause_reason,
            },
            "heartbeat_count": state.heartbeat_count,
            "last_heartbeat_at": state.last_heartbeat_at.isoformat() if state.last_heartbeat_at else None,
            "scheduler": scheduler_status,
        }
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_energy_status() -> dict:
    """
    Get current energy budget status.

    Shows available energy and action costs.

    Returns:
        Energy state and available actions with costs
    """
    from api.services.energy_service import get_energy_service

    try:
        service = get_energy_service()
        state = await service.get_state()
        costs = service.get_all_costs()

        return {
            "current_energy": state.current_energy,
            "max_energy": service.get_config().max_energy,
            "base_regeneration": service.get_config().base_regeneration,
            "action_costs": costs,
            "affordable_actions": [
                action for action, cost in costs.items()
                if cost <= state.current_energy
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def create_goal(
    title: str,
    description: Optional[str] = None,
    priority: str = "queued",
    source: str = "user_request"
) -> dict:
    """
    Create a new goal for Dionysus.

    Goals guide what Dionysus works on during heartbeat cycles.

    Args:
        title: Short goal title
        description: What does 'done' look like?
        priority: active, queued, or backburner
        source: curiosity, user_request, identity, derived, external

    Returns:
        Created goal with ID
    """
    from api.models.goal import GoalCreate, GoalPriority, GoalSource
    from api.services.goal_service import get_goal_service

    try:
        service = get_goal_service()
        goal_data = GoalCreate(
            title=title,
            description=description,
            priority=GoalPriority(priority),
            source=GoalSource(source),
        )
        goal = await service.create_goal(goal_data)

        return {
            "success": True,
            "goal": {
                "id": str(goal.id),
                "title": goal.title,
                "priority": goal.priority.value,
                "source": goal.source.value,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.tool()
async def list_goals(
    priority: Optional[str] = None,
    include_completed: bool = False,
    limit: int = 20
) -> dict:
    """
    List goals, optionally filtered by priority.

    Args:
        priority: Filter to specific priority (active, queued, backburner)
        include_completed: Include completed/abandoned goals
        limit: Maximum goals to return

    Returns:
        List of goals with their status
    """
    from api.models.goal import GoalPriority
    from api.services.goal_service import get_goal_service

    try:
        service = get_goal_service()
        priority_filter = GoalPriority(priority) if priority else None
        goals = await service.list_goals(
            priority=priority_filter,
            include_completed=include_completed,
            limit=limit,
        )

        return {
            "count": len(goals),
            "goals": [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "priority": g.priority.value,
                    "source": g.source.value,
                    "blocked": g.blocked_by is not None,
                    "last_touched": g.last_touched.isoformat() if g.last_touched else None,
                }
                for g in goals
            ],
        }
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def update_goal(
    goal_id: str,
    action: str,
    note: Optional[str] = None
) -> dict:
    """
    Update a goal's status.

    Args:
        goal_id: UUID of the goal
        action: promote, demote, complete, abandon, add_progress
        note: Optional note (required for add_progress and abandon)

    Returns:
        Updated goal status
    """
    from uuid import UUID
    from api.services.goal_service import get_goal_service

    try:
        service = get_goal_service()
        goal_uuid = UUID(goal_id)

        if action == "promote":
            goal = await service.promote_goal(goal_uuid)
        elif action == "demote":
            goal = await service.demote_goal(goal_uuid, "backburner")
        elif action == "complete":
            goal = await service.complete_goal(goal_uuid)
        elif action == "abandon":
            goal = await service.abandon_goal(goal_uuid, note or "No reason given")
        elif action == "add_progress":
            goal = await service.add_progress(goal_uuid, note or "Progress update")
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

        return {
            "success": True,
            "goal": {
                "id": str(goal.id),
                "title": goal.title,
                "priority": goal.priority.value,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.tool()
async def pause_heartbeat(reason: str) -> dict:
    """
    Pause the heartbeat system.

    Args:
        reason: Why heartbeat is being paused

    Returns:
        Confirmation of pause status
    """
    from api.services.energy_service import get_energy_service

    try:
        service = get_energy_service()
        await service.pause(reason)
        return {"success": True, "paused": True, "reason": reason}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.tool()
async def resume_heartbeat() -> dict:
    """
    Resume the heartbeat system after pause.

    Returns:
        Confirmation of resume status
    """
    from api.services.energy_service import get_energy_service

    try:
        service = get_energy_service()
        await service.resume()
        return {"success": True, "paused": False}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# MENTAL MODEL TOOLS (Feature 005)
# =============================================================================

from dionysus_mcp.tools.models import (
    create_mental_model_tool,
    list_mental_models_tool,
    get_mental_model_tool,
    revise_mental_model_tool,
    generate_prediction_tool,
    run_prediction_competition_tool,
    get_models_by_winners_tool,
)


@app.tool()
async def create_mental_model(
    name: str,
    domain: str,
    basin_ids: list[str],
    description: Optional[str] = None,
    prediction_templates: Optional[list[dict]] = None
) -> dict:
    """
    Create a new mental model from constituent basins.

    Mental models combine memory clusters (basins) to generate predictions
    about users, self, world, or specific tasks.

    Args:
        name: Unique model name
        domain: One of user, self, world, task_specific
        basin_ids: List of memory cluster UUIDs to combine
        description: Optional description of what the model predicts
        prediction_templates: Optional list of prediction templates with:
            - trigger: What triggers this prediction
            - predict: What the model predicts
            - suggest: Suggested action

    Returns:
        Success status with model_id or error message
    """
    return await create_mental_model_tool(
        name=name,
        domain=domain,
        basin_ids=basin_ids,
        description=description,
        prediction_templates=prediction_templates,
    )


@app.tool()
async def list_mental_models(
    domain: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> dict:
    """
    List mental models with optional filtering.

    Args:
        domain: Filter by domain (user, self, world, task_specific)
        status: Filter by status (draft, active, deprecated)
        limit: Maximum results (default: 20)
        offset: Pagination offset

    Returns:
        List of models with summary info and total count
    """
    return await list_mental_models_tool(
        domain=domain,
        status=status,
        limit=limit,
        offset=offset,
    )


@app.tool()
async def get_mental_model(
    model_id: str,
    include_predictions: bool = False,
    include_revisions: bool = False
) -> dict:
    """
    Get details for a specific mental model.

    Args:
        model_id: UUID of the model
        include_predictions: Include recent predictions
        include_revisions: Include revision history

    Returns:
        Full model details including basins and templates
    """
    return await get_mental_model_tool(
        model_id=model_id,
        include_predictions=include_predictions,
        include_revisions=include_revisions,
    )


@app.tool()
async def revise_mental_model(
    model_id: str,
    trigger_description: str,
    add_basins: Optional[list[str]] = None,
    remove_basins: Optional[list[str]] = None
) -> dict:
    """
    Revise a mental model's structure by adding or removing basins.

    Args:
        model_id: UUID of the model
        trigger_description: Why this revision is being made
        add_basins: Basin UUIDs to add
        remove_basins: Basin UUIDs to remove

    Returns:
        Success status with revision_id and updated accuracy
    """
    return await revise_mental_model_tool(
        model_id=model_id,
        trigger_description=trigger_description,
        add_basins=add_basins,
        remove_basins=remove_basins,
    )


@app.tool()
async def generate_prediction(
    model_id: str,
    context: dict,
    inference_state_id: Optional[str] = None
) -> dict:
    """
    Generate a prediction from a mental model.

    Creates a ThoughtSeed in the cognitive hierarchy for competition.
    Domain mapping: user→conceptual, self→metacognitive, world→abstract.

    Args:
        model_id: UUID of the mental model
        context: Context dict with keys like user_message, domain_hint, etc.
        inference_state_id: Optional link to active inference state

    Returns:
        Prediction with thoughtseed reference and confidence score
    """
    return await generate_prediction_tool(
        model_id=model_id,
        context=context,
        inference_state_id=inference_state_id,
    )


@app.tool()
async def run_prediction_competition(
    layer: str
) -> dict:
    """
    Run ThoughtSeed competition for predictions at a given cognitive layer.

    Layer mapping from ModelDomain:
    - user → conceptual (abstract concepts)
    - self → metacognitive (self-monitoring)
    - world → abstract (reasoning)
    - task_specific → perceptual (pattern recognition)

    Winner's constituent basins are activated via CLAUSE strengthening.

    Args:
        layer: ThoughtSeed layer (sensorimotor, perceptual, conceptual, abstract, metacognitive)

    Returns:
        Competition result with winner and activated basins
    """
    return await run_prediction_competition_tool(layer=layer)


@app.tool()
async def get_models_by_winners(
    layer: Optional[str] = None,
    limit: int = 5
) -> dict:
    """
    Get Mental Models associated with winning ThoughtSeeds.

    Models whose predictions have won in ThoughtSeed competition are
    cognitively relevant and should be prioritized.

    Args:
        layer: Optional filter by ThoughtSeed layer
        limit: Maximum models to return (default: 5)

    Returns:
        List of models with their ThoughtSeed context
    """
    return await get_models_by_winners_tool(layer=layer, limit=limit)


# =============================================================================
# SERVER LIFECYCLE
# =============================================================================

def main():
    """Run the MCP server using FastMCP's built-in stdio transport."""
    import atexit

    # Register cleanup for connection pool
    def cleanup():
        if _pool:
            asyncio.get_event_loop().run_until_complete(close_pool())

    atexit.register(cleanup)

    # FastMCP handles stdio transport internally
    app.run()


if __name__ == "__main__":
    main()

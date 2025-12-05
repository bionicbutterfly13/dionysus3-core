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
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5433/agi_memory"
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


# Create MCP server
app = Server("dionysus-core")


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
# SERVER LIFECYCLE
# =============================================================================

async def main():
    """Run the MCP server."""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())

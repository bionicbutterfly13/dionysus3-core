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
import hashlib
import hmac
import json
import os
from typing import Any, List, Optional
from contextlib import asynccontextmanager

import httpx
from mcp.server.fastmcp import FastMCP
from api.services.remote_sync import get_neo4j_driver, close_neo4j_driver


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
    Create a new memory via n8n webhook.

    All memory operations are proxied through n8n workflows which handle
    Neo4j persistence. No direct database connections.

    Args:
        content: Text content of the memory
        memory_type: One of episodic, semantic, procedural, strategic
        importance: 0.0 to 1.0 importance score
        metadata: Optional JSON metadata

    Returns:
        Created memory record with ID
    """
    import uuid
    from datetime import datetime

    memory_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    payload = {
        "memory_id": memory_id,
        "content": content,
        "memory_type": memory_type,
        "importance": importance,
        "metadata": metadata or {},
        "created_at": created_at,
        "operation": "create",
    }

    payload_bytes = json.dumps(payload, default=str).encode("utf-8")
    signature = _generate_webhook_signature(payload_bytes)

    async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
        response = await client.post(
            N8N_WEBHOOK_URL,
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        if response.status_code == 200:
            result = response.json() if response.text else {}
            return {
                "id": result.get("memory_id", memory_id),
                "created_at": result.get("created_at", created_at),
                "type": memory_type,
                "importance": importance,
            }
        else:
            raise Exception(
                f"Webhook returned {response.status_code}: {response.text}"
            )


@app.tool()
async def search_memories(
    query: str,
    limit: int = 10,
    threshold: float = 0.5,
    memory_type: Optional[str] = None
) -> list[dict]:
    """
    Search memories using vector similarity via n8n webhook.

    The n8n workflow handles embedding generation and Neo4j vector search.
    No direct database connections.

    Args:
        query: Search query text
        limit: Maximum results to return
        threshold: Minimum similarity threshold
        memory_type: Optional filter by memory type

    Returns:
        List of matching memories with similarity scores
    """
    payload: dict[str, Any] = {
        "operation": "vector_search",
        "query": query,
        "k": limit,
        "threshold": threshold,
    }

    if memory_type:
        payload["filters"] = {"memory_types": [memory_type]}

    payload_bytes = json.dumps(payload, default=str).encode("utf-8")
    signature = _generate_webhook_signature(payload_bytes)

    async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
        response = await client.post(
            N8N_RECALL_URL,
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
            },
        )

        if response.status_code == 200:
            result = response.json() if response.text else {}
            items = result.get("results") or result.get("memories") or []

            return [
                {
                    "id": str(item.get("id") or item.get("memory_id") or ""),
                    "content": str(item.get("content", ""))[:200],
                    "type": item.get("memory_type") or item.get("type") or "unknown",
                    "importance": float(item.get("importance", 0.5)),
                    "similarity": float(
                        item.get("similarity_score") or item.get("score") or item.get("similarity") or 0.0
                    ),
                }
                for item in items
                if isinstance(item, dict)
            ]
        else:
            raise Exception(
                f"Webhook returned {response.status_code}: {response.text}"
            )


@app.tool()
async def observe_environment() -> dict:
    """
    Gather a snapshot of the current environment (energy, goals, memories).
    """
    from api.services.action_executor import get_action_executor
    from api.models.action import ActionRequest
    from api.services.energy_service import ActionType
    
    executor = get_action_executor()
    result = await executor.execute(ActionRequest(action_type=ActionType.OBSERVE))
    return result.data.get("snapshot", {}) if result.success else {"error": result.error}


@app.tool()
async def reflect_on_topic(topic: str, context: Optional[str] = None) -> str:
    """
    Deep reflection on a specific topic to gain new insights.
    """
    from api.services.llm_service import chat_completion, GPT5_NANO
    
    system_prompt = "You are Dionysus's reflective faculty. Analyze for root causes and systemic connections."
    user_content = f"Topic: {topic}\n\nContext: {context or 'None'}"
    
    return await chat_completion(
        messages=[{"role": "user", "content": user_content}],
        system_prompt=system_prompt,
        model=GPT5_NANO,
        max_tokens=1000
    )


@app.tool()
async def synthesize_information(objective: str, data_points: str) -> str:
    """
    Synthesize multiple data points into a coherent analysis or plan.
    """
    from api.services.llm_service import chat_completion, GPT5_NANO
    
    system_prompt = "You are Dionysus's synthesis faculty. Weave disparate data into a high-level actionable plan."
    user_content = f"Objective: {objective}\n\nData Points: {data_points}"
    
    return await chat_completion(
        messages=[{"role": "user", "content": user_content}],
        system_prompt=system_prompt,
        model=GPT5_NANO,
        max_tokens=1000
    )


@app.tool()
async def manage_energy(operation: str, amount: float = 0.0) -> dict:
    """
    Check energy status or spend energy. Operations: 'get_status', 'spend_energy'.
    """
    from api.services.energy_service import get_energy_service
    service = get_energy_service()
    
    if operation == "get_status":
        state = await service.get_state()
        return {"current_energy": state.current_energy, "heartbeat_count": state.heartbeat_count}
    elif operation == "spend_energy":
        success, remaining = await service.spend_energy(amount)
        return {"success": success, "remaining_energy": remaining}
    return {"error": f"Unknown operation: {operation}"}


# =============================================================================
# CONSCIOUSNESS TOOLS
# =============================================================================

@app.tool()
async def get_consciousness_state() -> dict:
    """
    Get current consciousness state via n8n webhook.
    """
    driver = get_neo4j_driver()
    async with driver.session() as session:
        # This one statement can fetch all required data in parallel.
        result = await session.run("""
            OPTIONAL MATCH (inf:ActiveInferenceState)
            WITH inf ORDER BY inf.created_at DESC LIMIT 1
            OPTIONAL MATCH (iwmt:IWMTCoherence)
            WITH inf, iwmt ORDER BY iwmt.created_at DESC LIMIT 1
            OPTIONAL MATCH (b:MemoryCluster)
            WHERE b.basin_state IN ['active', 'activating', 'saturated']
            WITH inf, iwmt, collect(b) as basins
            RETURN inf, iwmt, basins
        """)
        data = await result.single() or {}

        inf = data.get('inf')
        iwmt = data.get('iwmt')
        basins_raw = data.get('basins', [])

        return {
            "active_inference": {
                "prediction_error": float(inf.get("prediction_error", 0.0)),
                "free_energy": float(inf.get("free_energy", 0.0)),
                "surprise": float(inf.get("surprise", 0.0)),
                "precision": float(inf.get("precision", 1.0)),
                "level": inf.get("consciousness_level", "minimal")
            } if inf else None,
            "iwmt_coherence": {
                "spatial": float(iwmt.get("spatial_coherence", 0.0)),
                "temporal": float(iwmt.get("temporal_coherence", 0.0)),
                "causal": float(iwmt.get("causal_coherence", 0.0)),
                "embodied_selfhood": float(iwmt.get("embodied_selfhood", 0.0)),
                "consciousness_level": float(iwmt.get("consciousness_level", 0.0)),
                "achieved": iwmt.get("consciousness_achieved", False)
            } if iwmt else None,
            "active_basins": [
                {
                    "id": str(b.get("id")),
                    "name": b.get("name"),
                    "type": b.get("basin_type"),
                    "state": b.get("basin_state"),
                    "activation": float(b.get("current_activation", 0.0)),
                    "clause_strength": float(b.get("clause_strength", 1.0))
                }
                for b in basins_raw
            ]
        }



@app.tool()
async def get_context_flow(project_id: str = "default") -> dict:
    """
    Get current neural field metrics (compression, resonance, flow state).
    """
    from api.services.context_stream import get_context_stream_service
    service = get_context_stream_service()
    flow = await service.analyze_current_flow(project_id=project_id)
    
    return {
        "state": flow.state.value,
        "density": flow.density,
        "turbulence": flow.turbulence,
        "compression": flow.compression,
        "resonance": flow.resonance,
        "summary": flow.summary
    }


@app.tool()
async def update_belief(
    domain: str,
    belief: dict,
    confidence: float = 0.5
) -> dict:
    """
    Update a belief in the active inference framework via n8n webhook.
    """
    driver = get_neo4j_driver()
    cypher = """
        CREATE (ais:ActiveInferenceState {
            id: randomUUID(),
            beliefs: $beliefs,
            prediction_error: 0.1,
            free_energy: 0.1,
            precision: $confidence,
            created_at: datetime()
        })
        RETURN ais.id as id, ais.prediction_error as prediction_error,
               ais.free_energy as free_energy, ais.precision as consciousness_level
    """
    params = {
        "beliefs": json.dumps({domain: belief}),
        "confidence": confidence
    }
    async with driver.session() as session:
        result = await session.run(cypher, params)
        row = await result.single()

    return {
        "id": str(row["id"]),
        "prediction_error": float(row["prediction_error"]),
        "free_energy": float(row["free_energy"]),
        "consciousness_level": row["consciousness_level"]
    }



@app.tool()
async def assess_coherence() -> dict:
    """
    Assess IWMT coherence based on current attractor basin landscape.
    """
    driver = get_neo4j_driver()
    
    # Fetch data for calculation
    async with driver.session() as session:
        # Get active basins and their relationships
        result = await session.run("""
            MATCH (b:MemoryCluster)
            WHERE b.basin_state IN ['active', 'activating', 'saturated']
            OPTIONAL MATCH (b)-[r:LINKED_TO]->(other:MemoryCluster)
            WHERE other.basin_state IN ['active', 'activating', 'saturated']
            RETURN b, collect(type(r)) as rels
        """)
        rows = await result.data()

    if not rows:
        return {"status": "insufficient_data", "consciousness_level": 0.0}

    # Real IWMT Coherence Calculations
    # 1. Spatial: Density of active basin connections
    total_basins = len(rows)
    total_rels = sum(len(r["rels"]) for r in rows)
    spatial = min(1.0, total_rels / (total_basins * 2.0)) if total_basins > 0 else 0.0
    
    # 2. Temporal: Stability/Recency of active basins
    avg_stability = sum(float(r["b"].get("stability", 0.5)) for r in rows) / total_basins
    temporal = avg_stability
    
    # 3. Causal: Presence of directed informational links (CLAUSE strength)
    avg_strength = sum(float(r["b"].get("clause_strength", 1.0)) for r in rows) / total_basins
    causal = min(1.0, avg_strength / 2.0)
    
    # 4. Embodied Selfhood: Presence of 'self' domain basins
    self_basins = [r for r in rows if r["b"].get("domain") == "self"]
    embodied = min(1.0, len(self_basins) / 2.0)
    
    # 5. Counterfactual: Depth of basins
    avg_depth = sum(float(r["b"].get("depth", 0.3)) for r in rows) / total_basins
    counterfactual = avg_depth

    consciousness_level = (spatial + temporal + causal + embodied + counterfactual) / 5.0
    
    # Persist the assessment
    cypher = """
        CREATE (iwmt:IWMTCoherence {
            id: randomUUID(),
            spatial_coherence: $s,
            temporal_coherence: $t,
            causal_coherence: $c,
            embodied_selfhood: $e,
            counterfactual_capacity: $cf,
            consciousness_level: $level,
            consciousness_achieved: $achieved,
            created_at: datetime()
        })
        RETURN iwmt.id as id
    """
    params = {
        "s": spatial, "t": temporal, "c": causal, "e": embodied, "cf": counterfactual,
        "level": consciousness_level, "achieved": consciousness_level >= 0.5
    }
    
    async with driver.session() as session:
        await session.run(cypher, params)

    return {
        "spatial_coherence": round(spatial, 3),
        "temporal_coherence": round(temporal, 3),
        "causal_coherence": round(causal, 3),
        "embodied_selfhood": round(embodied, 3),
        "counterfactual_capacity": round(counterfactual, 3),
        "consciousness_level": round(consciousness_level, 3),
        "consciousness_achieved": consciousness_level >= 0.5
    }



# =============================================================================
# BASIN TOOLS
# =============================================================================

@app.tool()
async def activate_basin(basin_id: str, strength: float = 0.5) -> dict:
    """
    Activate an attractor basin with given strength via n8n webhook.
    """
    driver = get_neo4j_driver()
    cypher = """
        MATCH (c:MemoryCluster {id: $basin_id})
        SET c.current_activation = c.current_activation + $strength,
            c.basin_state = 'activating',
            c.clause_strength = coalesce(c.clause_strength, 1.0) + 0.2
        // Cap clause_strength at 2.0
        SET c.clause_strength = CASE WHEN c.clause_strength > 2.0 THEN 2.0 ELSE c.clause_strength END
        RETURN c.basin_state as new_state,
               c.current_activation as new_activation,
               c.clause_strength as new_clause_strength
    """
    params = {"basin_id": basin_id, "strength": strength}
    
    async with driver.session() as session:
        result = await session.run(cypher, params)
        row = await result.single()

    if not row:
        raise ValueError(f"Basin with id {basin_id} not found.")

    return {
        "basin_id": basin_id,
        "new_state": row["new_state"],
        "new_activation": float(row["new_activation"]),
        "clause_strength": float(row["new_clause_strength"])
    }



@app.tool()
async def get_active_basins(limit: int = 10) -> list[dict]:
    """
    Get currently active attractor basins via n8n webhook.
    """
    driver = get_neo4j_driver()
    cypher = """
        MATCH (c:MemoryCluster)
        WHERE c.basin_state IN ['active', 'activating', 'saturated']
        RETURN c.id as id, c.name as name, c.basin_type as basin_type,
               c.basin_state as basin_state, c.current_activation as current_activation,
               c.clause_strength as clause_strength, c.stability as stability, c.depth as depth
        ORDER BY c.current_activation DESC
        LIMIT $limit
    """
    params = {"limit": limit}
    
    async with driver.session() as session:
        result = await session.run(cypher, params)
        rows = await result.data()

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
    Query the overall attractor basin landscape via n8n webhook.
    """
    driver = get_neo4j_driver()
    cypher_counts = """
        MATCH (c:MemoryCluster)
        RETURN c.basin_state as basin_state, COUNT(c) as count,
               avg(c.current_activation) as avg_activation,
               avg(c.clause_strength) as avg_strength
    """
    cypher_total_energy = "MATCH (c:MemoryCluster) RETURN sum(c.current_activation) as total_energy"
    
    async with driver.session() as session:
        result_counts = await session.run(cypher_counts)
        state_counts = await result_counts.data()
        
        result_energy = await session.run(cypher_total_energy)
        total_energy_record = await result_energy.single()
        total_energy = total_energy_record["total_energy"] if total_energy_record else 0

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
    content: str,
    memory_id: Optional[str] = None,
    child_thought_ids: Optional[List[str]] = None,
    parent_thought_id: Optional[str] = None,
    neuronal_packet: Optional[dict] = None
) -> dict:
    """
    Create a new thoughtseed in the cognitive hierarchy via n8n webhook.
    Supports fractal structures via child/parent links.
    """
    driver = get_neo4j_driver()
    cypher = """
        CREATE (t:ThoughtSeed {
            id: randomUUID(),
            layer: $layer,
            content: $content,
            neuronal_packet: $neuronal_packet,
            memory_id: $memory_id,
            child_thought_ids: $child_thought_ids,
            parent_thought_id: $parent_thought_id,
            activation_level: 0.5,
            competition_status: 'pending',
            created_at: datetime()
        })
        WITH t
        // Optional link to parent if provided
        FOREACH (_ IN CASE WHEN $parent_thought_id IS NOT NULL THEN [1] ELSE [] END |
            MERGE (p:ThoughtSeed {id: $parent_thought_id})
            MERGE (p)-[:HAS_CHILD]->(t)
        )
        RETURN t.id as id, t.layer as layer,
               t.activation_level as activation_level,
               t.competition_status as competition_status
    """
    params = {
        "layer": layer,
        "content": content,
        "neuronal_packet": json.dumps(neuronal_packet or {}),
        "memory_id": memory_id,
        "child_thought_ids": child_thought_ids or [],
        "parent_thought_id": parent_thought_id
    }
    
    async with driver.session() as session:
        result = await session.run(cypher, params)
        row = await result.single()

    return {
        "id": str(row["id"]),
        "layer": row["layer"],
        "activation_level": float(row["activation_level"]),
        "competition_status": row["competition_status"]
    }



@app.tool()
async def run_thoughtseed_competition(layer: str) -> dict:
    """
    Run winner selection among thoughtseeds at a given layer via n8n webhook.
    """
    driver = get_neo4j_driver()
    # This logic is complex and better handled by a single n8n workflow/Cypher query
    # if it were more than just selection. Here, we can do it in parts.
    
    get_competitors_cypher = """
        MATCH (t:ThoughtSeed)
        WHERE t.layer = $layer
          AND t.competition_status IN ['pending', 'competing']
        RETURN t.id as id, t.activation_level as activation_level
        ORDER BY t.activation_level DESC
    """
    
    async with driver.session() as session:
        result = await session.run(get_competitors_cypher, {"layer": layer})
        competitors = await result.data()

        if not competitors:
            return {"message": "No competitors at this layer", "winner": None}

        winner = competitors[0]
        loser_ids = [c["id"] for c in competitors[1:]]

        # Update winner
        await session.run(
            "MATCH (t:ThoughtSeed {id: $id}) SET t.competition_status = 'won'",
            {"id": winner["id"]}
        )

        # Update losers
        if loser_ids:
            await session.run(
                "MATCH (t:ThoughtSeed) WHERE t.id IN $ids SET t.competition_status = 'lost'",
                {"ids": loser_ids}
            )

        # Record competition
        competition_result = await session.run(
            """
            CREATE (c:ThoughtSeedCompetition {
                id: randomUUID(),
                competitor_ids: $competitor_ids,
                winner_id: $winner_id,
                layer: $layer,
                competition_energy: $energy,
                created_at: datetime()
            })
            RETURN c.id as id
            """,
            {
                "competitor_ids": [c["id"] for c in competitors],
                "winner_id": winner["id"],
                "layer": layer,
                "energy": sum(c["activation_level"] for c in competitors)
            }
        )
        competition_record = await competition_result.single()

    return {
        "competition_id": str(competition_record["id"]),
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
# ARCHON TOOLS (Feature 012)
# =============================================================================

@app.tool()
async def fetch_archon_tasks() -> list[dict]:
    """
    Fetch historical tasks from the local Archon environment.
    Used for historical reconstruction and longitudinal memory.
    """
    # This tool acts as a proxy to the local filesystem/Archon state.
    # In this environment, we can read from the specs/ directory to simulate task history.
    import glob
    import os
    
    tasks = []
    specs_path = "specs/*"
    for spec_dir in glob.glob(specs_path):
        tasks_file = os.path.join(spec_dir, "tasks.md")
        if os.path.exists(tasks_file):
            with open(tasks_file, "r") as f:
                content = f.read()
                # Simple parser for [X] or [ ] tasks
                for line in content.split("\n"):
                    if "[" in line and "]" in line and "-" in line:
                        status = "completed" if "[X]" in line or "[x]" in line else "pending"
                        tasks.append({
                            "project": os.path.basename(spec_dir),
                            "description": line.split("]", 1)[1].strip(),
                            "status": status,
                            "source": "markdown_spec"
                        })
    return tasks


# =============================================================
# MOSAEIC TOOLS (Feature 024)
# =============================================================

@app.tool()
async def mosaeic_capture(text: str, source_id: str = "agent_observation") -> str:
    """
    Capture a deep experiential state using the MOSAEIC protocol.
    Extracts Senses, Actions, Emotions, Impulses, and Cognitions from text.
    
    Args:
        text: The raw narrative or observed experience.
        source_id: Identifier for the source of this experience.
    """
    from api.services.mosaeic_service import get_mosaeic_service
    service = get_mosaeic_service()
    
    capture = await service.extract_capture(text, source_id)
    await service.persist_capture(capture)
    
    summary = f"MOSAEIC Capture Successful: {capture.summary}\n"
    summary += f"- Senses: {capture.senses.content} (Intensity: {capture.senses.intensity})\n"
    summary += f"- Actions: {capture.actions.content} (Intensity: {capture.actions.intensity})\n"
    summary += f"- Emotions: {capture.emotions.content} (Intensity: {capture.emotions.intensity})\n"
    summary += f"- Impulses: {capture.impulses.content} (Intensity: {capture.impulses.intensity})\n"
    summary += f"- Cognitions: {capture.cognitions.content} (Intensity: {capture.cognitions.intensity})\n"
    
    return summary


# =============================================================================
# SERVER LIFECYCLE
# =============================================================================

def main():
    """Run the MCP server using FastMCP's built-in stdio transport."""
    import atexit

    # Register cleanup for the webhook driver
    def cleanup():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError: # No running loop, create a new one for cleanup
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running(): # If loop is already running, schedule as a task
            loop.create_task(close_neo4j_driver())
        else: # Otherwise, run until complete
            loop.run_until_complete(close_neo4j_driver())

    atexit.register(cleanup)

    # FastMCP handles stdio transport internally
    app.run()



if __name__ == "__main__":
    main()

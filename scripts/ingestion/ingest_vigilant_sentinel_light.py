"""
Vigilant Sentinel avatar profile ingestion (gateway-only).

Uses n8n Cypher webhook via RemoteSyncService. No direct Neo4j access.
Requires: MEMORY_WEBHOOK_TOKEN, N8N_CYPHER_URL.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# Project root for imports
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

load_dotenv(_root / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_light")

CYPHER_URL = os.getenv("N8N_CYPHER_URL", "http://localhost:5678/webhook/neo4j/v1/cypher")
WEBHOOK_TOKEN = os.getenv("MEMORY_WEBHOOK_TOKEN", "")

if not WEBHOOK_TOKEN:
    raise ValueError("MEMORY_WEBHOOK_TOKEN is required for n8n Cypher webhook")

logger.info("Using n8n Cypher webhook for ingestion (no direct Neo4j).")


def _sync():
    from api.services.remote_sync import RemoteSyncService, SyncConfig

    return RemoteSyncService(
        config=SyncConfig(webhook_token=WEBHOOK_TOKEN, cypher_webhook_url=CYPHER_URL)
    )


async def create_trajectory(
    sync: Any, summary: str, trajectory_json: str, metadata: Dict[str, Any]
) -> str:
    """Create Trajectory node via gateway. Returns trajectory id."""
    ingest_id = str(uuid.uuid4())
    query = """
    CREATE (t:Trajectory {
        id: $id,
        summary: $summary,
        trajectory_type: 'structural',
        created_at: datetime(),
        metadata: $metadata,
        trajectory_json: $trajectory_json,
        project_id: $project_id,
        session_id: $session_id,
        source: 'manual_ingest'
    })
    RETURN t.id as id
    """
    params = {
        "id": ingest_id,
        "summary": summary,
        "metadata": json.dumps(metadata),
        "trajectory_json": trajectory_json,
        "project_id": metadata.get("project_id"),
        "session_id": metadata.get("session_id"),
    }
    res = await run_cypher(query, params, mode="write")
    records = res.get("records") or res.get("results") or []
    if not records:
        raise RuntimeError("create_trajectory: no RETURN id from Cypher")
    row = records[0] if isinstance(records[0], dict) else {}
    return row.get("id") or ingest_id


async def ingest_relationships(source_id: str, relationships: List[Dict[str, Any]]) -> None:
    """Ingest entities and relationships via gateway."""
    cypher = """
    MATCH (source {id: $source_id})
    MERGE (s:Entity {name: $source_name})
    ON CREATE SET s.id = randomUUID(), s.created_at = datetime(), s.type = $source_type, s.description = $source_desc
    ON MATCH SET s.type = $source_type, s.description = $source_desc
    MERGE (t:Entity {name: $target_name})
    ON CREATE SET t.id = randomUUID(), t.created_at = datetime(), t.type = $target_type, t.description = $target_desc
    ON MATCH SET t.type = $target_type, t.description = $target_desc
    MERGE (s)-[r:RELATED_TO {type: $rel_type}]->(t)
    SET r.evidence = $evidence, r.confidence = $confidence, r.updated_at = datetime()
    MERGE (s)-[:MENTIONED_IN]->(source)
    MERGE (t)-[:MENTIONED_IN]->(source)
    """
    count = 0
    for rel in relationships:
        params = {
            "source_id": source_id,
            "source_name": rel["source_name"],
            "source_type": rel["source_type"],
            "source_desc": rel["source_desc"],
            "target_name": rel["target_name"],
            "target_type": rel["target_type"],
            "target_desc": rel["target_desc"],
            "rel_type": rel["relation"],
            "evidence": rel["evidence"],
            "confidence": rel["confidence"],
        }
        await run_cypher(cypher, params, mode="write")
        count += 1
        if count % 5 == 0:
            logger.info("Ingested %d relationships...", count)
    logger.info("Total relationships ingested: %d", count)


async def main_async() -> int:
    profile_name = "The Vigilant Sentinel"
    profile_desc = "High-functioning adults with ADHD, gifted/twice-exceptional minds. Hyper-analytical, emotionally hypersensitive."

    relationships: List[Dict[str, Any]] = [
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Pain: RSD (Rejection Sensitive Dysphoria)",
            "target_type": "PainPoint",
            "target_desc": "Emotional volatility and rejection sensitivity. 'It hurts in my nervous system.'",
            "relation": "EXPERIENCES_PAIN",
            "evidence": "Not just sensitive — it hurts in my nervous system.",
            "confidence": 0.9,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Pain: Executive Paralysis",
            "target_type": "PainPoint",
            "target_desc": "I know exactly what to do... I just can't make myself do it.",
            "relation": "EXPERIENCES_PAIN",
            "evidence": "It isn't willpower. My brain literally won't turn on.",
            "confidence": 0.9,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Pain: Hollow Success Paradox",
            "target_type": "PainPoint",
            "target_desc": "External wins coupled with internal exhaustion.",
            "relation": "EXPERIENCES_PAIN",
            "evidence": "Why can I solve complex systems but can't reply to an email?",
            "confidence": 0.8,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Pain: Masking and Burnout",
            "target_type": "PainPoint",
            "target_desc": "Exhausting effort to appear normal.",
            "relation": "EXPERIENCES_PAIN",
            "evidence": "I'm a Hunter in a Farmer's world.",
            "confidence": 0.85,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Belief: Hunter in Farmer's World",
            "target_type": "Belief",
            "target_desc": "Genius processing but incompatible with bureaucratic norms.",
            "relation": "HOLDS_BELIEF",
            "evidence": "Identity reflection",
            "confidence": 0.9,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Belief: Productivity Systems Fail",
            "target_type": "Belief",
            "target_desc": "Conventional systems crumble under executive dysfunction.",
            "relation": "HOLDS_BELIEF",
            "evidence": "Lists and planners feel like punishment.",
            "confidence": 0.95,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Desire: Psychological Traction",
            "target_type": "Desire",
            "target_desc": "Collapse inner-critic loops within minutes.",
            "relation": "DESIRES",
            "evidence": "Regain psychological traction immediately",
            "confidence": 1.0,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Desire: Stop Paralysis",
            "target_type": "Desire",
            "target_desc": "Escape neuro-emotional paralysis reliably.",
            "relation": "DESIRES",
            "evidence": "Stop the freeze response",
            "confidence": 0.9,
        },
        {
            "source_name": profile_name,
            "source_type": "AvatarArchetype",
            "source_desc": profile_desc,
            "target_name": "Failed: Standard Planners/CBT",
            "target_type": "FailedSolution",
            "target_desc": "Frames struggle as ignorance/laziness vs neurological.",
            "relation": "REJECTS_SOLUTION",
            "evidence": "Lists and planners feel like punishment.",
            "confidence": 0.9,
        },
    ]

    logger.info("Creating Trajectory...")
    trajectory_id = await create_trajectory(
        summary="Manually ingested Vigilant Sentinel Avatar Profile via gateway (n8n Cypher)",
        trajectory_json=json.dumps({"operation": "ingest_profile", "status": "manual"}),
        metadata={
            "project_id": "dionysus_core",
            "session_id": "avatar_ingest_light",
            "tags": ["avatar", "manual_ingest"],
        },
    )
    logger.info("Trajectory created: %s", trajectory_id)

    logger.info("Ingesting relationships...")
    await ingest_relationships(trajectory_id, relationships)

    logger.info("Done!")
    return 0


def main() -> None:
    code = asyncio.run(main_async())
    sys.exit(code)


if __name__ == "__main__":
    main()

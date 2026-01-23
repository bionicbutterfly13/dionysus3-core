#!/usr/bin/env python3
"""
Neo4j Schema for Metacognitive Particles

Feature: 040-metacognitive-particles
Task: T076

Applies indexes and constraints for metacognitive particle persistence.
Uses n8n webhook (no direct Neo4j access per CLAUDE.md).

Usage:
    python scripts/init_metacognitive_schema.py

AUTHOR: Mani Saint-Victor, MD
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


# Schema statements from data-model.md
METACOGNITIVE_SCHEMA = [
    # Unique constraints
    """CREATE CONSTRAINT particle_id IF NOT EXISTS
FOR (p:MetacognitiveParticle) REQUIRE p.id IS UNIQUE""",

    """CREATE CONSTRAINT belief_id IF NOT EXISTS
FOR (b:BeliefState) REQUIRE b.id IS UNIQUE""",

    """CREATE CONSTRAINT gain_event_id IF NOT EXISTS
FOR (g:EpistemicGainEvent) REQUIRE g.id IS UNIQUE""",

    # Performance indexes
    """CREATE INDEX particle_agent IF NOT EXISTS
FOR (p:MetacognitiveParticle) ON (p.agent_id)""",

    """CREATE INDEX particle_type IF NOT EXISTS
FOR (p:MetacognitiveParticle) ON (p.type)""",

    """CREATE INDEX particle_level IF NOT EXISTS
FOR (p:MetacognitiveParticle) ON (p.level)""",

    """CREATE INDEX gain_magnitude IF NOT EXISTS
FOR (g:EpistemicGainEvent) ON (g.magnitude)""",

    """CREATE INDEX gain_detected_at IF NOT EXISTS
FOR (g:EpistemicGainEvent) ON (g.detected_at)""",

    """CREATE INDEX belief_entropy IF NOT EXISTS
FOR (b:BeliefState) ON (b.entropy)""",
]


async def apply_schema():
    """Apply metacognitive schema via n8n cypher webhook."""
    try:
        from api.services.remote_sync import RemoteSyncService, SyncConfig
    except ImportError as e:
        print(f"✗ Failed to import RemoteSyncService: {e}")
        return False

    token = os.getenv("MEMORY_WEBHOOK_TOKEN", "")
    if not token:
        print("✗ MEMORY_WEBHOOK_TOKEN not set")
        return False

    cypher_url = os.getenv("N8N_CYPHER_URL", "http://localhost:5678/webhook/neo4j/v1/cypher")
    sync = RemoteSyncService(config=SyncConfig(webhook_token=token, cypher_webhook_url=cypher_url))

    print(f"Using n8n cypher webhook: {cypher_url}")
    print(f"\nApplying {len(METACOGNITIVE_SCHEMA)} schema statements...")

    success_count = 0
    for i, statement in enumerate(METACOGNITIVE_SCHEMA, 1):
        first_line = statement.strip().split("\n")[0][:50]
        print(f"  [{i}/{len(METACOGNITIVE_SCHEMA)}] {first_line}...")
        try:
            res = await sync.run_cypher(statement, mode="write")
            if res.get("success", True) is False:
                raise RuntimeError(res.get("error", "Webhook returned failure"))
            print("       ✓ Success")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                print("       ⚠ Already exists (OK)")
                success_count += 1
            else:
                print(f"       ✗ Error: {error_msg}")

    # Verification
    print("\nVerifying indexes...")
    try:
        indexes = await sync.run_cypher("SHOW INDEXES YIELD name WHERE name STARTS WITH 'particle' OR name STARTS WITH 'belief' OR name STARTS WITH 'gain' RETURN name", mode="read")
        records = indexes.get("records") or indexes.get("results") or []
        print(f"  Found {len(records)} metacognitive indexes")
    except Exception as e:
        print(f"  ⚠ Verification query failed: {e}")

    print(f"\n{'✓' if success_count == len(METACOGNITIVE_SCHEMA) else '⚠'} Applied {success_count}/{len(METACOGNITIVE_SCHEMA)} statements")
    return success_count == len(METACOGNITIVE_SCHEMA)


async def main():
    """Run schema initialization."""
    print("=" * 60)
    print("Metacognitive Particles Neo4j Schema")
    print("Feature: 040-metacognitive-particles | Task: T076")
    print("=" * 60)
    print()
    print("This script creates indexes for:")
    print("  - MetacognitiveParticle nodes")
    print("  - BeliefState nodes")
    print("  - EpistemicGainEvent nodes")
    print()

    success = await apply_schema()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

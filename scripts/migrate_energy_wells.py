#!/usr/bin/env python3
"""
Neo4j Migration Script: Energy Wells
Feature: 030-neuronal-packet-mental-models

Augments existing MemoryCluster nodes with Energy-Well properties:
- boundary_energy
- stability
- cohesion_ratio

Usage:
    python scripts/migrate_energy_wells.py
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

async def run_migration():
    """Apply Neo4j migration via n8n cypher webhook."""
    try:
        from api.services.remote_sync import RemoteSyncService, SyncConfig
    except Exception as e:
        print(f"✗ Failed to import webhook client: {e}")
        return False

    token = os.getenv("MEMORY_WEBHOOK_TOKEN", "")
    cypher_url = os.getenv("N8N_CYPHER_URL", "http://localhost:5678/webhook/neo4j/v1/cypher")
    sync = RemoteSyncService(config=SyncConfig(webhook_token=token, cypher_webhook_url=cypher_url))

    print(f"Using n8n cypher webhook: {cypher_url}")

    # 1. Add Energy-Well properties to existing MemoryCluster nodes if missing
    migration_query = """
    MATCH (c:MemoryCluster)
    SET c.boundary_energy = coalesce(c.boundary_energy, 0.5),
        c.stability = coalesce(c.stability, 0.5),
        c.cohesion_ratio = coalesce(c.cohesion_ratio, 1.0),
        c.updated_at = datetime()
    RETURN count(c) as count
    """

    print("\nMigrating MemoryCluster nodes...")
    try:
        res = await sync.run_cypher(migration_query, mode="write")
        records = res.get("records") or res.get("results") or []
        count = records[0].get("count") if records else 0
        print(f"  ✓ Successfully updated {count} nodes.")
    except Exception as e:
        print(f"  ✗ Migration failed: {e}")
        return False

    # 2. Also ensure MentalModel nodes have these properties
    model_migration = """
    MATCH (m:MentalModel)
    SET m.boundary_energy = coalesce(m.boundary_energy, 0.5),
        m.stability = coalesce(m.stability, 0.5),
        m.cohesion_ratio = coalesce(m.cohesion_ratio, 1.0),
        m.updated_at = datetime()
    RETURN count(m) as count
    """

    print("\nMigrating MentalModel nodes...")
    try:
        res = await sync.run_cypher(model_migration, mode="write")
        records = res.get("records") or res.get("results") or []
        count = records[0].get("count") if records else 0
        print(f"  ✓ Successfully updated {count} nodes.")
    except Exception as e:
        print(f"  ✗ MentalModel migration failed: {e}")

    print("\n✓ Energy Well migration complete!")
    return True

if __name__ == "__main__":
    exit_code = asyncio.run(run_migration())
    sys.exit(0 if exit_code else 1)

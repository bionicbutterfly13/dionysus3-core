#!/usr/bin/env python3
"""
Neo4j Migration Script: Avatar Basins
Feature: 030-neuronal-packet-mental-models

Maps the Avatar Mental Model (Analytical Empath) to Energy Wells.
Specifically targets basins identified in Feature 018.
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
    """Apply Avatar-specific energy settings."""
    try:
        from api.services.remote_sync import RemoteSyncService, SyncConfig
    except Exception as e:
        print(f"✗ Failed to import webhook client: {e}")
        return False

    token = os.getenv("MEMORY_WEBHOOK_TOKEN", "")
    cypher_url = os.getenv("N8N_CYPHER_URL", "http://localhost:5678/webhook/neo4j/v1/cypher")
    sync = RemoteSyncService(config=SyncConfig(webhook_token=token, cypher_webhook_url=cypher_url))

    # High-stability basins for the Analytical Empath
    avatar_basins = [
        {"name": "Resistance to Change", "energy": 0.8, "stability": 0.9, "cohesion": 1.2},
        {"name": "Breakthrough Readiness", "energy": 0.4, "stability": 0.3, "cohesion": 0.8},
        {"name": "Analytical Professional", "energy": 0.9, "stability": 0.95, "cohesion": 1.5},
    ]

    print("\nMapping Avatar Attractor Basins...")
    for basin in avatar_basins:
        query = """
        MATCH (c:MemoryCluster {name: $name})
        SET c.boundary_energy = $energy,
            c.stability = $stability,
            c.cohesion_ratio = $cohesion,
            c.updated_at = datetime()
        RETURN count(c) as count
        """
        try:
            res = await sync.run_cypher(query, basin)
            print(f"  ✓ Processed '{basin['name']}'")
        except Exception as e:
            print(f"  ✗ Failed to map '{basin['name']}': {e}")

    print("\n✓ Avatar Basin Mapping complete!")
    return True

if __name__ == "__main__":
    exit_code = asyncio.run(run_migration())
    sys.exit(0 if exit_code else 1)

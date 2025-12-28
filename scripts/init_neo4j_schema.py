#!/usr/bin/env python3
"""
Neo4j Schema Initialization Script
Feature: 002-remote-persistence-safety

Applies the Neo4j schema from contracts/neo4j-schema.cypher to the VPS Neo4j instance.

Usage:
    # Requires n8n to be running and configured to reach Neo4j:
    python scripts/init_neo4j_schema.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Schema statements (extracted from neo4j-schema.cypher)
# Comments are stripped since Cypher Shell handles them differently than driver
SCHEMA_STATEMENTS = [
    # Constraints
    """CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE""",
    """CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.id IS UNIQUE""",
    """CREATE CONSTRAINT project_id_unique IF NOT EXISTS
FOR (p:Project) REQUIRE p.id IS UNIQUE""",
    # Vector index for semantic similarity search
    """CREATE VECTOR INDEX memory_embedding IF NOT EXISTS
FOR (m:Memory) ON (m.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}}""",
    # Full-text search on memory content
    """CREATE FULLTEXT INDEX memory_content_fulltext IF NOT EXISTS
FOR (n:Memory) ON EACH [n.content]""",
    # Composite index for project + type filtered queries
    """CREATE INDEX memory_project_type IF NOT EXISTS
FOR (m:Memory) ON (m.source_project, m.memory_type)""",
    # Date range queries on memories
    """CREATE INDEX memory_created_at IF NOT EXISTS
FOR (m:Memory) ON (m.created_at)""",
    # Session date range queries
    """CREATE INDEX session_dates IF NOT EXISTS
FOR (s:Session) ON (s.started_at, s.ended_at)""",
    # Project lookup by name
    """CREATE INDEX project_name IF NOT EXISTS
FOR (p:Project) ON (p.name)""",
    # Sync version for conflict detection
    """CREATE INDEX memory_sync_version IF NOT EXISTS
FOR (m:Memory) ON (m.sync_version)""",
    # Initial Projects
    """MERGE (p:Project {id: 'dionysus-core'})
SET p.name = 'Dionysus Core',
    p.description = 'AGI memory system core',
    p.created_at = datetime()""",
    """MERGE (p:Project {id: 'inner-architect-companion'})
SET p.name = 'Inner Architect Companion',
    p.description = 'IAS coaching application',
    p.created_at = datetime()""",
    """MERGE (p:Project {id: 'dionysus-memory'})
SET p.name = 'Dionysus Memory',
    p.description = 'Memory persistence and consolidation',
    p.created_at = datetime()""",
]


async def apply_schema():
    """Apply Neo4j schema via n8n cypher webhook (no direct Neo4j access)."""
    try:
        from api.services.remote_sync import RemoteSyncService, SyncConfig
    except Exception as e:
        print(f"✗ Failed to import webhook client: {e}")
        return False

    token = os.getenv("MEMORY_WEBHOOK_TOKEN", "")
    if not token:
        print("✗ MEMORY_WEBHOOK_TOKEN not set in environment")
        return False

    cypher_url = os.getenv("N8N_CYPHER_URL", "http://localhost:5678/webhook/neo4j/v1/cypher")
    sync = RemoteSyncService(config=SyncConfig(webhook_token=token, cypher_webhook_url=cypher_url))

    print(f"Using n8n cypher webhook: {cypher_url}")

    # Apply each schema statement
    print("\nApplying schema statements...")
    for i, statement in enumerate(SCHEMA_STATEMENTS, 1):
        first_line = statement.strip().split("\n")[0][:60]
        print(f"  [{i}/{len(SCHEMA_STATEMENTS)}] {first_line}...")
        try:
            res = await sync.run_cypher(statement, mode="write")
            if res.get("success", True) is False:
                raise RuntimeError(res.get("error", "Webhook returned failure"))
            print("       ✓ Success")
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                print("       ⚠ Already exists (skipped)")
            else:
                print(f"       ✗ Error: {error_msg}")

    # Basic verification
    print("\nVerifying schema...")
    try:
        projects = await sync.run_cypher("MATCH (p:Project) RETURN count(p) as count", mode="read")
        records = projects.get("records") or projects.get("results") or []
        count = records[0].get("count") if records and isinstance(records[0], dict) else None
        print(f"  Projects: {count}")
    except Exception as e:
        print(f"  ⚠ Verification failed: {e}")

    print("\n✓ Schema initialization complete (via n8n)!")
    return True

    except Exception as e:
        print(f"\n✗ Schema initialization failed: {e}")
        return False


async def main():
    """Run schema initialization."""
    print("=" * 60)
    print("Neo4j Schema Initialization")
    print("Feature: 002-remote-persistence-safety")
    print("=" * 60)
    print()

    print("Prerequisites:")
    print("  Ensure n8n is running and configured with Neo4j credentials.")
    print("  Ensure MEMORY_WEBHOOK_TOKEN matches both API and n8n.")
    print()

    success = await apply_schema()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Neo4j Schema Initialization Script
Feature: 002-remote-persistence-safety

Applies the Neo4j schema from contracts/neo4j-schema.cypher to the VPS Neo4j instance.

Usage:
    # Start SSH tunnel first:
    ssh -L 7687:127.0.0.1:7687 -N root@72.61.78.89

    # Then run this script:
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
    `vector.dimensions`: 768,
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
    """Apply Neo4j schema to the database."""
    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        print("✗ neo4j package not installed. Run: pip install neo4j")
        return False

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    if not password:
        print("✗ NEO4J_PASSWORD not set in environment")
        return False

    print(f"Connecting to Neo4j at {uri}...")

    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

        # Test connection
        async with driver.session() as session:
            result = await session.run("RETURN 1")
            await result.single()
            print("✓ Connected to Neo4j")

        # Apply each schema statement
        print("\nApplying schema statements...")
        async with driver.session() as session:
            for i, statement in enumerate(SCHEMA_STATEMENTS, 1):
                try:
                    # Get a brief description from the statement
                    first_line = statement.strip().split("\n")[0][:60]
                    print(f"  [{i}/{len(SCHEMA_STATEMENTS)}] {first_line}...")

                    await session.run(statement)
                    print(f"       ✓ Success")
                except Exception as e:
                    error_msg = str(e)
                    # Some errors are expected (e.g., index already exists)
                    if "already exists" in error_msg.lower():
                        print(f"       ⚠ Already exists (skipped)")
                    else:
                        print(f"       ✗ Error: {error_msg}")

        # Verify schema
        print("\nVerifying schema...")
        async with driver.session() as session:
            # Check constraints
            result = await session.run("SHOW CONSTRAINTS")
            constraints = await result.values()
            print(f"  Constraints: {len(constraints)}")

            # Check indexes
            result = await session.run("SHOW INDEXES")
            indexes = await result.values()
            print(f"  Indexes: {len(indexes)}")

            # Check projects
            result = await session.run("MATCH (p:Project) RETURN count(p) as count")
            record = await result.single()
            print(f"  Projects: {record['count']}")

        await driver.close()
        print("\n✓ Schema initialization complete!")
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
    print("  Ensure SSH tunnel is running:")
    print("    ssh -L 7687:127.0.0.1:7687 -N root@72.61.78.89")
    print()

    success = await apply_schema()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

import asyncio
import os
from datetime import datetime
from api.services.graphiti_service import get_graphiti_service

# Configuration
SOURCE_OF_TRUTH_PATH = "/Volumes/Asylum/dev/dionysus3-core/reference/email-sequence/research/EMAIL-SEQUENCE-PLAN.md"
CURRICULUM_ID = "ias-core-v1"
CURRICULUM_TITLE = "The Inner Architect System"

async def seed_ias_graph():
    """
    Seeds the IAS Curriculum Root Object and links it to the Source of Truth file.
    Uses GraphitiService to ensure strict adherence to "No Direct Password" rule.
    """
    print(f"Initializing Graphiti Service...")
    graphiti = await get_graphiti_service()
    
    # 1. Create Curriculum Root
    print(f"Creating Curriculum Root: {CURRICULUM_TITLE}...")
    cypher_root = """
    MERGE (c:Curriculum {id: $id})
    SET c.title = $title,
        c.description = "Neuroscience-backed guided breakthrough program for high-performing analytical empaths.",
        c.updated_at = datetime()
    RETURN c.id as id
    """
    await graphiti.execute_cypher(cypher_root, {
        "id": CURRICULUM_ID, 
        "title": CURRICULUM_TITLE
    })
    
    # 2. Link Source of Truth Asset
    print(f"Linking Source of Truth: {SOURCE_OF_TRUTH_PATH}...")
    cypher_asset = """
    MATCH (c:Curriculum {id: $curriculum_id})
    MERGE (a:Asset {id: $asset_id})
    MERGE (c)-[:HAS_SOURCE_OF_TRUTH]->(a)
    SET a.type = "markdown_file",
        a.path = $path,
        a.description = "Primary architectural source of truth for the email sequence and curriculum structure.",
        a.updated_at = datetime()
    RETURN a.id as id
    """
    asset_id = f"asset-{CURRICULUM_ID}-sot"
    await graphiti.execute_cypher(cypher_asset, {
        "curriculum_id": CURRICULUM_ID,
        "asset_id": asset_id,
        "path": SOURCE_OF_TRUTH_PATH
    })

    # 3. Create Launch Event (Business Logic)
    print(f"Creating Launch Event (Jan 8 Deadline)...")
    cypher_launch = """
    MATCH (c:Curriculum {id: $curriculum_id})
    MERGE (l:LaunchEvent {id: $launch_id})
    MERGE (c)-[:HAS_LAUNCH]->(l)
    SET l.deadline = datetime($deadline),
        l.price_charter = 3975,
        l.price_regular = 5475,
        l.framework = "Todd Brown Bullet Campaign",
        l.updated_at = datetime()
    RETURN l.id as id
    """
    await graphiti.execute_cypher(cypher_launch, {
        "curriculum_id": CURRICULUM_ID,
        "launch_id": f"launch-{CURRICULUM_ID}-jan8",
        # ISO8601 for Jan 8, 2026 (Assuming 2026 based on context, or user intent?)
        # User said "Jan 8", current time is Jan 1, 2026. So Jan 8, 2026.
        "deadline": "2026-01-08T23:59:59-05:00" 
    })
    
    print("✅ IAS Data Object seeded successfully.")
    print(f"   - Root: {CURRICULUM_ID}")
    print(f"   - Source: {asset_id} -> {SOURCE_OF_TRUTH_PATH}")
    print(f"   - Launch: Jan 8 Deadline | $3975 -> $5475")

if __name__ == "__main__":
    # Ensure env vars are loaded for GraphitiService
    if not os.getenv("NEO4J_PASSWORD"):
        print("❌ Error: NEO4J_PASSWORD env var is missing. Cannot proceed safely.")
        exit(1)
        
    asyncio.run(seed_ias_graph())

import asyncio
import os
import json
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.graphiti_service import get_graphiti_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dionysus.sync_wisdom")

async def main():
    input_file = "wisdom_extraction_raw.json"
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found.")
        return

    try:
        with open(input_file, "r") as f:
            insights = json.load(f)
    except Exception as e:
        logger.error(f"Error reading {input_file}: {e}")
        return

    logger.info(f"Loaded {len(insights)} insights for Graphiti sync.")
    
    # Initialize Graphiti service (uses env vars)
    from api.services.graphiti_service import GraphitiConfig
    config = GraphitiConfig(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    graphiti_svc = await get_graphiti_service(config)

    # Get existing episodes to skip
    # We'll use a raw cypher query via the driver if possible, or just trust the count
    # Better: Query for all source_descriptions in the group
    driver = graphiti_svc._graphiti.driver
    existing_sessions_query = "MATCH (n:Episodic {group_id: 'distilled-wisdom'}) RETURN n.source_description as source"
    records, _, _ = await driver.execute_query(existing_sessions_query)
    processed_sources = {record["source"] for record in records}
    logger.info(f"Found {len(processed_sources)} sessions already in Graphiti.")

    for i, item in enumerate(insights):
        # Determine source/session_id
        session_id = item.get("session_id", "unknown")
        source_desc = f"distilled_wisdom_{session_id}"
        
        if source_desc in processed_sources:
            continue
            
        logger.info(f"[{i+1}/{len(insights)}] Syncing session: {session_id}")
        
        # Format the insight as content for Graphiti
        # We'll convert the whole item back to JSON string so Graphiti can extract from it
        content = json.dumps(item, indent=2)
        
        try:
            result = await graphiti_svc.ingest_message(
                content=content,
                source_description=f"distilled_wisdom_{session_id}",
                group_id="distilled-wisdom"
            )
            logger.info(f"  ✓ Success: Created episode {result.get('episode_uuid')}")
            logger.info(f"  Nodes: {len(result.get('nodes', []))}, Edges: {len(result.get('edges', []))}")
        except Exception as e:
            logger.error(f"  ✗ Failed to sync {session_id}: {e}")
            
    await graphiti_svc.close()
    logger.info("Wisdom sync session complete.")

if __name__ == "__main__":
    asyncio.run(main())

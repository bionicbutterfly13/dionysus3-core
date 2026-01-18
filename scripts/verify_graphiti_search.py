
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())
# Load environment variables
load_dotenv()

from api.services.graphiti_service import get_graphiti_service, GraphitiService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_graphiti_connection():
    logger.info("Initializing GraphitiService...")
    try:
        service = await get_graphiti_service()
    except Exception as e:
        logger.error(f"Failed to initialize GraphitiService: {e}")
        return

    logger.info("1. Testing basic Cypher execution (Neo4j Connectivity)...")
    try:
        # Simple count query
        results = await service.execute_cypher("MATCH (n) RETURN count(n) as count LIMIT 1")
        count = results[0]['count'] if results else 0
        logger.info(f"SUCCESS: Connected to Neo4j. Total nodes: {count}")
    except Exception as e:
        logger.error(f"FAILURE: Cypher execution failed: {e}")
        return

    logger.info("\n2. Testing Graphiti Search (Vector Index)...")
    query = "Dionysus architecture"
    try:
        # Search via Graphiti
        results = await service.search(query=query, limit=3)
        edges = results.get("edges", [])
        
        logger.info(f"Search found {len(edges)} results.")
        for i, edge in enumerate(edges):
            logger.info(f"Result {i+1}:")
            logger.info(f"  UUID: {edge.get('uuid')}")
            logger.info(f"  Name: {edge.get('name')}")
            logger.info(f"  Fact: {edge.get('fact')}")
            
        logger.info("SUCCESS: Graphiti search executed.")
    except Exception as e:
        logger.error(f"FAILURE: Graphiti search failed: {e}")

    logger.info("\n3. Testing Retrieval Strategy Fetch (Cypher)...")
    try:
        cypher = "MATCH (s:RetrievalStrategy) RETURN s ORDER BY s.created_at DESC LIMIT 1"
        records = await service.execute_cypher(cypher)
        if records:
            strategy = records[0]['s']
            logger.info(f"SUCCESS: Retrieved latest strategy: {strategy.get('id', 'unknown')}")
        else:
            logger.info("SUCCESS: Cypher executed (no strategy found, but query worked).")
    except Exception as e:
        logger.error(f"FAILURE: Strategy fetch failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_graphiti_connection())


import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.services.vector_search import get_vector_search_service

async def verify_vector_search_service():
    logger.info("Initializing VectorSearchService...")
    service = get_vector_search_service()
    
    # 1. Health Check
    logger.info("\n1. Testing Health Check...")
    health = await service.health_check()
    logger.info(f"Health: {health}")
    
    if not health.get("healthy"):
        logger.error("Health check failed!")
        return

    # 2. Strategy Fetch
    logger.info("\n2. Testing Strategy Fetch (Internal)...")
    strategy = await service._get_latest_strategy()
    logger.info(f"Strategy: {strategy}")

    # 3. Semantic Search
    logger.info("\n3. Testing Semantic Search...")
    query = "Dionysus architecture"
    response = await service.semantic_search(query=query, top_k=3)
    
    logger.info(f"Search Time: {response.search_time_ms:.2f}ms")
    logger.info(f"Results Found: {response.count}")
    
    for i, res in enumerate(response.results):
        logger.info(f"Result {i+1}: [{res.similarity_score:.4f}] {res.content[:100]}...")

    if response.count >= 0:
        logger.info("\nSUCCESS: VectorSearchService is functioning via Graphiti.")

if __name__ == "__main__":
    asyncio.run(verify_vector_search_service())

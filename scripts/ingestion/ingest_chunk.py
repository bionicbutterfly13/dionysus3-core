import asyncio
import sys
import os
import logging

# Add parent directory to path to allow imports from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.kg_learning_service import KGLearningService
from api.services.memevolve_adapter import MemEvolveAdapter
from api.services.graphiti_service import GraphitiService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ingest_chunk(filename: str):
    file_path = os.path.join("scripts/chunks", filename)
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return

    with open(file_path, "r") as f:
        content = f.read()

    logger.info(f"Ingesting chunk: {filename} ({len(content)} chars)")

    # Initialize Services
    # GraphitiService will auto-detect config from env via GraphitiConfig
    graphiti_service = await GraphitiService.get_instance()
    
    # Initialize Adapter
    # MemEvolveAdapter does not take graphiti_service in init
    # It accesses it internally via singleton    # Initialize Adapter
    # MemEvolveAdapter does not take graphiti_service in init
    # It accesses it internally via singleton or import
    adapter = MemEvolveAdapter()
    
    # Initialize Learning Service
    # Note: KGLearningService expects `adapter` in its __init__
    kg_service = KGLearningService(adapter=adapter)` in its __init__
    kg_service = KGLearningService(adapter=adapter)

    try:
        # Use SEMANTIC memory type (standard for papers/theory)
        from api.models.memevolve import MemoryType
        
        result = await kg_service.extract_and_learn_typed(
            content=content,
            source_id=f"paper:narrative_active_inference:{filename}",
            memory_type=MemoryType.SEMANTIC
        )
        
        logger.info(f"Ingestion Complete for {filename}")
        logger.info(f"Entities: {len(result.entities)}")
        logger.info(f"Relationships: {len(result.relationships)}")
        logger.info(f"Basin Updates: {result.basin_updates}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ingest_chunk.py <filename>")
        sys.exit(1)
        
    chunk_filename = sys.argv[1]
    asyncio.run(ingest_chunk(chunk_filename))

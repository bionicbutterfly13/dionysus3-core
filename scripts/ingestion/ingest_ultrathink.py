
import asyncio
import os
import sys
import logging
from api.services.kg_learning_service import get_kg_learning_service
from api.models.sync import MemoryType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_ultrathink_ingestion():
    """
    Manually run KGLearningService extraction on the target document.
    This bypasses the standard API and invokes the 'River' logic directly.
    """
    
    # 1. Define Source Path
    # The file is in the artifacts directory. We'll simply read it directly if possible, 
    # or assume the content is passed here. For this script, we'll embed the content 
    # or read from a mapped path.
    # Since we are running inside the container, we need to access the file where it resides.
    # The user volume mapping shows /Volumes/Asylum:/Volumes/Asylum.
    # The artifact path is /Users/manisaintvictor/... which is effectively on the host.
    # WE MUST HAVE THE CONTENT ACCESSIBLE.
    # For safety, I will write the content to a temp file in /app/scripts/temp_content.md first 
    # (which I will do in the tool calling sequence), then read it here.
    
    # Manually override NEO4J_URI for container-to-service communication
    os.environ["NEO4J_URI"] = "bolt://neo4j:7687"
    
    target_file = "/app/scripts/narrative_active_inference_paper.md"
    
    if not os.path.exists(target_file):
        logger.error(f"Target file not found: {target_file}")
        return

    logger.info(f"Reading content from {target_file}...")
    with open(target_file, "r") as f:
        content = f.read()

    # 2. Initialize Service
    logger.info("Initializing KGLearningService...")
    kg_service = get_kg_learning_service()

    # 3. Execute "Ultrathink" Extraction
    # We use 'extract_and_learn_typed' to force it through the full pipeline:
    # - Basin classification
    # - Strategy boosting
    # - Graphiti storage
    source_id = "ultrathink:narrative_as_active_inference_paper"
    
    logger.info(f"Starting extraction for source: {source_id}")
    logger.info(f"Content length: {len(content)} chars")
    
    # Force SEMANTIC memory type for deep theory
    result = await kg_service.extract_and_learn_typed(
        content=content,
        source_id=source_id,
        memory_type=MemoryType.SEMANTIC 
    )

    # 4. Report Results
    logger.info("--- ULTRATHINK INGESTION COMPLETE ---")
    logger.info(f"Run ID: {result.run_id}")
    logger.info(f"Entities Extracted: {len(result.entities)}")
    logger.info(f"Relationships Proposed: {len(result.relationships)}")
    
    for rel in result.relationships:
        logger.info(f"  [REL] {rel.source} --({rel.relation_type})--> {rel.target} (Conf: {rel.confidence})")

    # 5. Check if AutoSchemaKG integration is triggered (via relationship ingestion implicitly or explicitly)
    # The current code doesn't explicitly call AutoSchemaKG from KGLearningService, 
    # but the data is now in Graphiti, which is the "Structure" layer.

if __name__ == "__main__":
    asyncio.run(run_ultrathink_ingestion())

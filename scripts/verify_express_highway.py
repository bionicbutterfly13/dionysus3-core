
import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_highway")

async def verify_express_highway():
    """
    Verify the unified ingestion pipeline (Express Highway).
    """
    logger.info("Initializing Express Highway Verification...")
    
    try:
        from api.services.kg_learning_service import get_kg_learning_service
        from api.models.sync import MemoryType
        
        service = get_kg_learning_service()
        
        test_content = (
            "The MemEvolve architecture consolidates Nemori and Graphiti into a unified pipeline. "
            "AutoSchema acts as the structural encoder, transforming raw text into conceptual graphs. "
            "Active Inference provides top-down priors to guide this extraction."
        )
        source_id = "verification_script_run_001"
        
        logger.info(f"Ingesting test content: {test_content[:50]}...")
        
        result = await service.ingest_unified(
            content=test_content,
            source_id=source_id,
            # Let it infer memory type, or force one
            memory_type=None 
        )
        
        logger.info("Ingestion completed successfully.")
        logger.info(f"Result Run ID: {result.get('run_id')}")
        logger.info(f"Consciousness Level: {result.get('consciousness_level')}")
        logger.info(f"Concept Count: {result.get('concept_count')}")
        
        ingest_stats = result.get("ingestion_stats", {})
        logger.info(f"Ingested Entities: {ingest_stats.get('entities_extracted')}")
        logger.info(f"Memories Created: {ingest_stats.get('memories_created')}")
        
        if result.get("consciousness_level") > 0:
            logger.info("✅ Verification PASSED: Unified Pipeline is operational.")
        else:
            logger.warning("⚠️ Verification WARNING: Consciousness level is 0, something might be off with extraction.")
            
    except Exception as e:
        logger.error(f"❌ Verification FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_express_highway())


import asyncio
import logging
from api.models.memevolve import MemoryRecallRequest
from api.services.memevolve_adapter import get_memevolve_adapter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_retrieval")

async def verify_retrieval_strategy():
    """
    Verify Active Inference Retrieval Strategy.
    """
    logger.info("Initializing Active Retrieval Verification...")
    
    try:
        adapter = get_memevolve_adapter()
        
        # Test Query: Something that benefits from "Expansion"
        # "Marketing Strategy" -> should expand to [Avatar, Mechanism, Offer]
        query = "What is the core marketing mechanism?"
        project_id = "dionysus_core"
        
        logger.info(f"Executing Recall for query: '{query}'")
        
        result = await adapter.recall_memories(
            MemoryRecallRequest(
                query=query,
                project_id=project_id,
                limit=5,
                context="Direct Response Marketing"
            )
        )
        
        logger.info("Recall completed.")
        logger.info(f"Original Query: {result.get('query')}")
        logger.info(f"Expanded Query: {result.get('expanded_query')}")
        logger.info(f"Strategy Used: {result.get('strategy')}")
        logger.info(f"Concepts Expanded: {result.get('expansion_concepts')}")
        logger.info(f"Results Found: {result.get('result_count')}")
        
        if result.get('expansion_concepts'):
            logger.info("✅ Verification PASSED: Query Expansion Active.")
        else:
            logger.warning("⚠️ Verification WARNING: No concepts expanded. Check LLM or Prompt.")

    except Exception as e:
        logger.error(f"❌ Verification FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_retrieval_strategy())

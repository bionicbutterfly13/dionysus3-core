
import asyncio
import logging
import json
import time
from uuid import uuid4
from datetime import datetime
from api.services.memevolve_adapter import get_memevolve_adapter
from api.services.graphiti_service import get_graphiti_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_meta_evolution")

async def main():
    logger.info("Initializing Meta-Evolution Verification...")
    
    adapter = get_memevolve_adapter()
    graphiti = await get_graphiti_service()
    
    # 1. Seed "High Surprisal" Trajectories
    # We want low similarity scores to drive VFE up (VFE = 1 - Resonance)
    # If we create trajectories with similarity 0.1, VFE will be 0.9 (High)
    
    logger.info("Seeding High-Surprisal Trajectories...")
    
    dummy_results = [
        {"id": str(uuid4()), "content": "Irrelevant info A", "similarity": 0.1},
        {"id": str(uuid4()), "content": "Irrelevant info B", "similarity": 0.05}
    ]
    
    seed_query = """
    CREATE (t:Trajectory {
        id: $id,
        trajectory_type: 'search',
        query: $query,
        result: $result,
        created_at: datetime(),
        summary: 'Synthetic high surprisal trajectory for verification'
    })
    """
    
    # Insert 5 bad searches
    for i in range(5):
        await graphiti.execute_cypher(
            seed_query,
            {
                "id": str(uuid4()),
                "query": f"Impossible query {i}",
                "result": json.dumps(dummy_results)
            }
        )
        
    logger.info("Seeded 5 trajectories with ~0.9 VFE.")
    
    # 2. Trigger Evolution
    logger.info("Triggering Evolution...")
    start_time = time.time()
    
    result = await adapter.trigger_evolution()
    
    duration = time.time() - start_time
    logger.info(f"Evolution process took {duration:.2f}s")
    
    # 3. Assertions
    if not result.get("success"):
        logger.error(f"❌ Evolution Failed: {result.get('error')}")
        return

    action = result.get("action")
    avg_vfe = result.get("avg_vfe", 0.0)
    
    logger.info(f"Action Taken: {action}")
    logger.info(f"Average VFE: {avg_vfe:.4f}")
    
    if action == "evolved" and avg_vfe > 0.3:
        new_strategy = result.get("new_strategy")
        logger.info(f"✅ SUCCESS: Evolution Triggered correctly.")
        logger.info(f"New Strategy Created: {new_strategy.get('strategy_name', 'Unknown')}")
        logger.info(f"New Top K: {new_strategy.get('top_k')}")
        logger.info(f"Basis: {new_strategy.get('basis')}")
    else:
        logger.warning(f"⚠️ WARNING: Evolution not triggered as expected. Action: {action}")

    # Cleanup (Optional, but good for hygiene)
    # We won't delete, to keep audit trail, but in real test env we might.

if __name__ == "__main__":
    asyncio.run(main())


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
logger = logging.getLogger("verify_structure_learning")

async def main():
    logger.info("Initializing Structure Learning Verification...")
    
    adapter = get_memevolve_adapter()
    graphiti = await get_graphiti_service()
    
    # 1. Seed "High Surprisal" Trajectories (Structure Failure)
    # We want near-zero similarity to drive VFE > 0.7
    # If sim = 0.05, VFE = 0.95 (High Surprisal)
    
    logger.info("Seeding Radical Surprisal Trajectories...")
    
    dummy_results = [
        {"id": str(uuid4()), "content": "Noise", "similarity": 0.05}
    ]
    
    seed_query = """
    CREATE (t:Trajectory {
        id: $id,
        trajectory_type: 'search',
        query: $query,
        result: $result,
        created_at: datetime(),
        summary: 'Synthetic structural failure for verification'
    })
    """
    
    # Insert 5 bad searches about "Unknown Topic"
    # We use a query about something likely missing, e.g. "Quantum Gravity in Marketing"
    for i in range(5):
        await graphiti.execute_cypher(
            seed_query,
            {
                "id": str(uuid4()),
                "query": "How to apply Quantum Entanglement to Direct Response Marketing", 
                "result": json.dumps(dummy_results)
            }
        )
        
    logger.info("Seeded 5 trajectories with ~0.95 VFE.")
    
    # 2. Trigger Evolution
    logger.info("Triggering Meta-Evolution...")
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
    
    if action == "structure_expanded" and avg_vfe > 0.7:
        new_concept = result.get("new_concept")
        # Ensure we handle dict or list properly
        if isinstance(new_concept, list) and new_concept:
            concept_name = new_concept[0].get('name')
        elif isinstance(new_concept, dict):
            concept_name = new_concept.get('name')
        else:
            concept_name = "Unknown"
            
        logger.info(f"✅ SUCCESS: Structure Expansion Triggered.")
        logger.info(f"New Concept Created: {concept_name}")
        logger.info(f"Rationale: {result.get('msg')}")
    else:
        logger.warning(f"⚠️ WARNING: Structure Learning not triggered. Action: {action}")

if __name__ == "__main__":
    asyncio.run(main())

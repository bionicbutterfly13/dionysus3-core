
import asyncio
import uuid
import sys
import os
import logging

# Add /app to path for VPS imports
sys.path.append("/app")

from api.services.session_manager import get_session_manager
from api.services.remote_sync import get_neo4j_driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reproduce")

async def reproduce():
    logger.info("Starting identity awareness surgical diagnostic")
    
    driver = get_neo4j_driver() # This is the WebhookNeo4jDriver shim
    
    logger.info("Checking constraints...")
    res_cons = await driver.execute_query("SHOW CONSTRAINTS")
    logger.info(f"Constraints: {res_cons}")
    
    logger.info("Auditing Journey relationships:")
    q_rel = "MATCH (j:Journey)-[r]->(n) RETURN type(r) as type, labels(n) as labels LIMIT 10"
    res_rel = await driver.execute_query(q_rel)
    logger.info(f"Relationships: {res_rel}")
    
    logger.info("Listing existing nodes with device_id:")
    q_peek = "MATCH (n) WHERE n.device_id IS NOT NULL RETURN labels(n) as labels, n.device_id as did, n.id as id LIMIT 10"
    res_p = await driver.execute_query(q_peek)
    logger.info(f"Peek results: {res_p}")
    
    did = uuid.uuid4()
    logger.info(f"Test DID: {did}")
    
    # 1. MATCH (Should return empty)
    logger.info("Step 1: MATCH")
    q_match = "MATCH (j:Journey {device_id: $did}) RETURN j"
    res_m = await driver.execute_query(q_match, {"did": str(did)})
    logger.info(f"MATCH result: {res_m}")
    
    # 2. CREATE (Should return data)
    logger.info("Step 2: CREATE")
    q_create = """
    CREATE (j:Journey {
        device_id: $did,
        id: $id,
        created_at: datetime()
    })
    RETURN j {.*} as data
    """
    try:
        res_c = await driver.execute_query(q_create, {"did": str(did), "id": str(uuid.uuid4())})
        logger.info(f"CREATE result: {res_c}")
        
        if not res_c:
            logger.error("CRITICAL: CREATE returned EMPTY list []")
        else:
            logger.info("SUCCESS: CREATE returned data")
            
    except Exception as e:
        logger.error(f"CREATE failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())

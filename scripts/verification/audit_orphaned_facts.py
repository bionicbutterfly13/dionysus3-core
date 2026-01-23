import asyncio
import os
import sys
import logging

# Add project root to path
sys.path.append(os.getcwd())

from api.services.graphiti_service import get_graphiti_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audit_orphans")

async def audit_orphans():
    logger.info("Initializing Audit for Orphaned 'Fact' Episodes...")
    
    graphiti = await get_graphiti_service()
    
    # Query to count episodes that look like the redundant ones we managed to stop
    # Criteria: name starts with 'fact_', usually singular facts derived from relationships
    
    count_cypher = """
    MATCH (e:Episode)
    WHERE e.name STARTS WITH 'fact_'
    RETURN count(e) as orphan_count, collect(e.id)[0..5] as samples
    """
    
    try:
        results = await graphiti.execute_cypher(count_cypher)
        if results:
            count = results[0]['orphan_count']
            samples = results[0]['samples']
            logger.info(f" फाउंड {count} potential orphaned 'fact' episodes.")
            if count > 0:
                logger.info(f"Sample IDs: {samples}")
                
                # Check what they are linked to (if anything)
                link_check_cypher = """
                MATCH (e:Episode)
                WHERE e.name STARTS WITH 'fact_'
                OPTIONAL MATCH (e)-[r]-()
                RETURN count(r) as rel_count
                """
                link_res = await graphiti.execute_cypher(link_check_cypher)
                avg_rels = 0
                if link_res:
                    total_rels = sum(r['rel_count'] for r in link_res)
                    avg_rels = total_rels / count
                logger.info(f"Average relationships per node: {avg_rels:.2f}")
                
        else:
            logger.info("No orphaned 'fact' episodes found.")
            
    except Exception as e:
        logger.error(f"Audit failed: {e}")

if __name__ == "__main__":
    asyncio.run(audit_orphans())

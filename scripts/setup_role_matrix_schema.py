"""
Setup Neo4j constraints and indexes for RoleMatrix via Graphiti.
Feature: 034-network-self-modeling
Task: T062
"""

import asyncio
import logging
from api.services.webhook_neo4j_driver import get_neo4j_driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup_role_matrix")

async def setup_schema():
    driver = get_neo4j_driver()
    
    constraints = [
        "CREATE CONSTRAINT role_matrix_id IF NOT EXISTS FOR (rm:RoleMatrix) REQUIRE rm.id IS UNIQUE",
        "CREATE CONSTRAINT role_node_id IF NOT EXISTS FOR (rn:RoleNode) REQUIRE rn.id IS UNIQUE",
        "CREATE INDEX role_matrix_name IF NOT EXISTS FOR (rm:RoleMatrix) ON (rm.name)"
    ]
    
    async with driver.session() as session:
        for cypher in constraints:
            logger.info(f"Executing: {cypher}")
            await session.run(cypher)
            
    logger.info("RoleMatrix schema setup complete.")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(setup_schema())

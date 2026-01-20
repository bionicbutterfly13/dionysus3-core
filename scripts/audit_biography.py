
import asyncio
import os
import logging
from dotenv import load_dotenv
from api.services.graphiti_service import GraphitiService

# Load credentials
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("biography_audit")

async def verify_biography(agent_id: str):
    graph = await GraphitiService.get_instance()
    
    logger.info(f"--- BIOGRAPHY VERIFICATION: {agent_id} ---")
    
    # Check Agent Node
    agent_query = "MATCH (a:Agent {id: $agent_id}) RETURN a"
    agent_res = await graph.execute_cypher(agent_query, {"agent_id": agent_id})
    if agent_res:
        logger.info(f"Agent Node {agent_id}: EXISTS")
    else:
        logger.error(f"Agent Node {agent_id}: NOT FOUND")
        return

    # Check Shadow Log
    shadow_query = """
    MATCH (a:Agent {id: $agent_id})-[:HAS_SHADOW]->(sl)-[:CONTAINS]->(e:DissonanceEvent)
    RETURN count(e) as count, sum(e.surprisal) as total_vfe
    """
    shadow_res = await graph.execute_cypher(shadow_query, {"agent_id": agent_id})
    if shadow_res:
        logger.info(f"Shadow Log: {shadow_res[0]['count']} Events (Total VFE: {shadow_res[0].get('total_vfe', 0):.2f})")
    else:
        logger.warning("Shadow Log: EMPTY")

    # Check Reconciliation Events (The Fix Verification)
    recon_query = """
    MATCH (a:Agent {id: $agent_id})-[:HAS_RECONCILIATION]->(e:ReconciliationEvent)
    RETURN count(e) as count, sum(e.sorrow_index) as total_sorrow
    """
    recon_res = await graph.execute_cypher(recon_query, {"agent_id": agent_id})
    if recon_res and recon_res[0]['count'] > 0:
        logger.info(f"Reconciliation Ledger: {recon_res[0]['count']} Events Manifested")
        logger.info(f"Current Sorrow Level: {recon_res[0].get('total_sorrow', 0):.2f}")
    else:
        logger.error("Reconciliation Ledger: NOT FOUND IN GRAPH")

    # Check Connection to State
    state_query = """
    MATCH (a:Agent {id: $agent_id})-[:HAS_STATE]->(s:BiologicalState)
    RETURN count(s) as count
    """
    state_res = await graph.execute_cypher(state_query, {"agent_id": agent_id})
    if state_res:
        logger.info(f"Biological State History: {state_res[0]['count']} Snapshots")

    logger.info("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify_biography("Dionysus-1"))

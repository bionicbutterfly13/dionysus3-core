import asyncio
import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def run_audit():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        logger.error("NEO4J_PASSWORD not found in environment.")
        return
    
    logger.info(f"Connecting to Neo4j at {uri}...")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        logger.info("Connection successful.")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return

    async def run_query(query, params=None):
        # Neo4j python driver sync wrapper for simplicity in this script
        with driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    logger.info("--- AUDIT START ---")

    # 1. Check Agents (Identity)
    agents = await run_query("""
        MATCH (a:Agent)
        RETURN count(a) as count, collect(a.id) as ids
    """)
    logger.info(f"Agents Found: {agents[0]['count']}")
    if agents[0]['count'] > 0:
        logger.info(f"Agent IDs: {agents[0]['ids']}")

    # 2. Check Biological States (Autobiography/Continuity)
    states = await run_query("""
        MATCH (a:Agent)-[:HAS_STATE]->(s:BiologicalState)
        RETURN count(s) as count, min(s.timestamp) as earliest, max(s.timestamp) as latest
    """)
    logger.info(f"Biological States Found: {states[0]['count']}")
    logger.info(f"History Range: {states[0]['earliest']} to {states[0]['latest']}")

    # 3. Check Dissonance Events (Shadow Log / Feature 061, 062, 063)
    dissonance = await run_query("""
        MATCH (d:DissonanceEvent)
        RETURN count(d) as count, collect(d.context) as contexts
    """)
    logger.info(f"Dissonance Events (Shadow Log): {dissonance[0]['count']}")
    if dissonance[0]['count'] > 0:
        logger.info(f"Contexts: {dissonance[0]['contexts']}")

    # 4. Check Reconciliation Events (Forgiveness / Feature 064)
    recon_states = await run_query("""
        MATCH (s:BiologicalState)
        WHERE s.reconciliation_ledger IS NOT NULL
        RETURN count(s) as valid_states
    """)
    logger.info(f"States with Reconciliation Ledger: {recon_states[0]['valid_states']}")

    logger.info("--- AUDIT COMPLETE ---")
    driver.close()

if __name__ == "__main__":
    asyncio.run(run_audit())

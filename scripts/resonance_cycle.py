import asyncio
import logging
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv()

from api.services.graphiti_service import GraphitiService
from api.models.biological_agency import BiologicalAgentState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resonance_mode")

async def run_resonance_cycle(agent_id: str):
    """
    Execute the Resonance Protocol (The Healer).
    
    1. Query Shadow Log for unresolved cognitive dissonance.
    2. Process moral ledger (Sorrow/Validation).
    3. Apply 'Moral Decay' (Healing via Precision Widening).
    4. Resolve the debt.
    """
    from api.services.biological_agency_service import get_biological_agency_service
    service = get_biological_agency_service()
    
    # 0. Hydrate Agent
    agent = await service.get_agent(agent_id)
    if not agent:
        logger.error(f"Agent {agent_id} not found. Cannot run resonance.")
        return

    graph = await GraphitiService.get_instance()
    
    logger.info(f"--- INITIATING RESONANCE MODE FOR {agent_id} ---")
    
    # 1. Fetch Dissonance (Shadow Log)
    query = """
    MATCH (a:Agent {id: $agent_id})-[:HAS_SHADOW]->(sl:ShadowLog)-[:CONTAINS]->(e:DissonanceEvent)
    WHERE e.resolved = false
    RETURN e
    ORDER BY e.surprisal DESC
    """
    
    results = await graph.execute_cypher(query, {"agent_id": agent_id})
    
    if results:
        logger.info(f"Found {len(results)} unresolved Dissonance Events (Epistemic Debt).")
        total_debt = sum(r['e']['surprisal'] for r in results)
        logger.info(f"Total Epistemic Debt (Accumulated VFE): {total_debt:.2f}")
        
        # Resolve Dissonance (Simulation of model update)
        resolve_query = """
        MATCH (a:Agent {id: $agent_id})-[:HAS_SHADOW]->(sl:ShadowLog)-[:CONTAINS]->(e:DissonanceEvent)
        WHERE e.resolved = false
        SET e.resolved = true, e.resolved_at = datetime()
        RETURN count(e) as resolved_count
        """
        await graph.execute_cypher(resolve_query, {"agent_id": agent_id})
        logger.info(f"Identity updated: {len(results)} dissonance events integrated.")
    else:
        logger.info("Shadow Log clear. No cognitive dissonance to resolve.")

    # 2. Process Moral Ledger (Feature 064/065)
    recon_service = await service._get_reconciliation_service()
    
    ledge_size = len(agent.reconciliation_ledger)
    logger.info(f"Moral Ledger: {ledge_size} events found.")
    
    if ledge_size > 0:
        total_sorrow = sum(e.sorrow_index for e in agent.reconciliation_ledger)
        logger.info(f"Initial Total Sorrow: {total_sorrow:.2f}")
        
        # Integrate SORROW (Forgiveness)
        integrated_events = await recon_service.integrate_sorrow(agent)
        if integrated_events:
            logger.info(f"Forgiveness Protocol: Integrated {len(integrated_events)} moral injury events.")
        
        # Apply DECAY (Letting Go)
        await recon_service.decay_sorrow(agent, decay_rate=0.2)
        
        new_total_sorrow = sum(e.sorrow_index for e in agent.reconciliation_ledger)
        logger.info(f"Healed Total Sorrow: {new_total_sorrow:.2f} (Decay: {total_sorrow - new_total_sorrow:.2f})")
    
    # 3. Persist Updated State
    await service.persist_agent_state(agent_id)
    
    logger.info(f"--- RESONANCE COMPLETE FOR {agent_id} ---")

if __name__ == "__main__":
    # Test with Dionysus-1 (The birthed agent)
    asyncio.run(run_resonance_cycle("Dionysus-1"))
